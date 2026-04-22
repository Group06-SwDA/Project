# C4 Container Diagram — Methodology and Code

This document describes the full extraction and analysis pipeline that
produces the C4 diagram of Backstage's knowledge dependencies, from
git history to the final `.puml` file.

## Files produced in this folder

- `04_c4_container.puml` — PlantUML source (output of the `07_c4_diagram.py` script)
- `c4_knowledge_dependencies.svg` — SVG rendering of the diagram
- `codice_c4.md` — this file

---

## 1. Overall Pipeline

The C4 is the last link in a six-stage pipeline. Each script produces
intermediate artifacts in `data/` that are consumed by the next:

```
           repo/ (blobless clone of backstage/backstage, branch master)
                         |
                         v
  [01] 01_extract_commits.py     -> data/commits_raw.csv
                         |
                         v
  [02] 02_filter_commits.py      -> data/commits_filtered.csv
                                    data/filter_stats.md
                         |
            +------------+------------+
            v                         v
  [03] 03_cochange_analysis.py   [04] 04_author_coupling.py
       -> data/cochange.csv           -> data/author_coupling.csv
            |                         |
            +------------+------------+
                         v
  [05] 05_build_graph.py         -> output/graph.gexf
                                    data/graph_nodes.csv
                                    data/graph_edges.csv
                                    data/package_edges.csv
                         |
                         v
  [07] 07_c4_diagram.py          -> output/diagrams/04_c4_container.puml
                                    -> (PlantUML) .svg
```

**Note on cloning:** the repository is cloned in *blobless* mode
(`git clone --filter=blob:none --no-checkout --single-branch -b master`)
to avoid downloading the ~4.9 GB of blobs. `git log --name-only` reads
only commit and tree objects, so it does not trigger promisor fetches.

---

## 2. Step 01 — Commit Extraction

**Goal:** transform `git log` into a long CSV (one row per
`(commit, file)` pair).

**Methodological choices:**

- `git log --name-only` (not PyDriller): throughput ~500–2000 commits/s
  vs ~2 commits/s with PyDriller on a blobless clone.
- Without the `-m` flag: merge commits do not produce a diff against a single
  parent, so they are skipped. This is the canonical MSR choice to avoid
  double-counting changes originating from feature branches.
- Writing to a temporary file instead of streaming via pipe: avoids silent
  data-loss bugs on Windows when `git log`'s stdout exceeds the pipe buffer.

**Output schema (`commits_raw.csv`):**

| Column | Type | Description |
|---|---|---|
| `commit_hash` | str | SHA-1 |
| `author_email`, `author_name` | str | |
| `date_iso` | str | ISO 8601 |
| `is_merge`, `num_parents` | bool, int | |
| `num_files_in_commit` | int | commit size |
| `new_path` | str | path of the modified file |

```python
#!/usr/bin/env python3
"""01_extract_commits.py - Commit extraction via `git log` (subprocess)."""
import argparse, csv, subprocess, sys, tempfile, time, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO_PATH = ROOT / "repo"
OUTPUT = ROOT / "data" / "commits_raw.csv"
SENTINEL = "__COMMIT__"
FS = "\x01"  # SOH: field separator, never present in path/email/name


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--since", default=None)
    ap.add_argument("--branch", default="master")
    args = ap.parse_args()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fmt = f"{SENTINEL}%H{FS}%aE{FS}%aN{FS}%aI{FS}%P"
    cmd = ["git", "-C", str(REPO_PATH), "log", "--name-only",
           f"--pretty=format:{fmt}", args.branch]
    if args.since:
        cmd.append(f"--since={args.since}")

    fd, tmp_name = tempfile.mkstemp(prefix="gitlog_", suffix=".txt",
                                    dir=OUTPUT.parent)
    os.close(fd)
    tmp_path = Path(tmp_name)
    with tmp_path.open("wb") as out_fh:
        ret = subprocess.run(cmd, stdout=out_fh, stderr=subprocess.PIPE,
                             check=False)
    if ret.returncode != 0:
        sys.exit(f"git log failed: {ret.stderr.decode(errors='replace')}")

    count_commits = count_rows = 0
    cur = None
    try:
        with tmp_path.open("r", encoding="utf-8", errors="replace") as fin, \
             OUTPUT.open("w", newline="", encoding="utf-8") as fout:
            writer = csv.writer(fout)
            writer.writerow([
                "commit_hash", "author_email", "author_name", "date_iso",
                "is_merge", "num_parents", "num_files_in_commit", "new_path",
            ])
            for line in fin:
                line = line.rstrip("\r\n")
                if line.startswith(SENTINEL):
                    if cur is not None:
                        count_rows += _flush(writer, cur)
                        count_commits += 1
                        if args.limit and count_commits >= args.limit:
                            cur = None; break
                    parts = line[len(SENTINEL):].split(FS)
                    if len(parts) != 5:
                        cur = None; continue
                    h, email, name, iso_date, parents_str = parts
                    parents = parents_str.split() if parents_str else []
                    cur = {"h": h, "email": email, "name": name,
                           "date": iso_date, "parents": parents,
                           "is_merge": len(parents) >= 2,
                           "files": [], "_seen": set()}
                elif line and cur is not None:
                    if line not in cur["_seen"]:
                        cur["_seen"].add(line); cur["files"].append(line)
            if cur is not None:
                count_rows += _flush(writer, cur); count_commits += 1
    finally:
        try: tmp_path.unlink()
        except OSError: pass


def _flush(writer, cur) -> int:
    n = len(cur["files"])
    if n == 0:
        writer.writerow([cur["h"], cur["email"], cur["name"], cur["date"],
                         cur["is_merge"], len(cur["parents"]), 0, ""])
        return 1
    for p in cur["files"]:
        writer.writerow([cur["h"], cur["email"], cur["name"], cur["date"],
                         cur["is_merge"], len(cur["parents"]), n, p])
    return n


if __name__ == "__main__":
    main()
```

---

## 3. Step 02 — Methodological Filtering

**Goal:** remove structural noise before analysis. Each
filter is a *threat to validity* documented in `data/filter_stats.md`
with pre/post counts.

| # | Filter | Rationale |
|---|---|---|
| 1 | Merge commits (`num_parents >= 2`) | Merge artifacts, not original work |
| 2 | Bots (`dependabot`, `renovate`, `[bot]`, `github-actions`, …) | Do not represent human knowledge |
| 3 | Commits with `> 30` files | Massive refactors distort co-change (standard MSR threshold; Tornhill uses ~50) |
| 4 | Non-code files (`.md`, `.lock`, `.svg`, `.json`, `.yaml`, binaries, …) | Not "source code" in the strict sense |
| 5 | `.changeset/*` | Backstage uses Changesets — touched in almost every PR, would generate false coupling |

```python
#!/usr/bin/env python3
"""02_filter_commits.py - Apply methodological filters to commits."""
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "commits_raw.csv"
OUT = ROOT / "data" / "commits_filtered.csv"
STATS = ROOT / "data" / "filter_stats.md"

MAX_FILES_PER_COMMIT = 30

BOT_PATTERN = re.compile(
    r"(?:dependabot|renovate|\[bot\]|goalie|imgbot|github-actions)", re.I)

EXCLUDE_EXTS = {
    ".md", ".lock", ".txt", ".svg", ".png", ".jpg", ".jpeg", ".gif", ".ico",
    ".webp", ".yaml", ".yml", ".json", ".snap", ".log", ".csv", ".tsv",
    ".pdf", ".zip", ".gz", ".tgz", ".ttf", ".woff", ".woff2",
}
EXCLUDE_NAMES = {
    "yarn.lock", "package-lock.json", "pnpm-lock.yaml",
    "CHANGELOG.md", "CHANGELOG", "LICENSE", "README.md",
    ".gitignore", ".npmignore", ".dockerignore",
}
EXCLUDE_PREFIXES = (".changeset/", "node_modules/", "dist/", "build/",
                    "coverage/", ".yarn/")


def is_excluded(path: str) -> bool:
    if not path: return True
    p = path.replace("\\", "/").lower()
    if any(p.startswith(pref) for pref in EXCLUDE_PREFIXES): return True
    basename = p.rsplit("/", 1)[-1]
    if basename in EXCLUDE_NAMES: return True
    if "." in basename:
        ext = "." + basename.rsplit(".", 1)[-1]
        if ext in EXCLUDE_EXTS: return True
    return False


def main():
    df = pd.read_csv(RAW, low_memory=False)
    # Filter 1: merge commits
    df["is_merge_bool"] = df["is_merge"].astype(str).str.lower().isin(
        ["true", "1", "yes"])
    df = df[~df["is_merge_bool"] & (df["num_parents"].fillna(0) < 2)]
    df = df.drop(columns=["is_merge_bool"])
    # Filter 2: bot authors
    bot_mask = df["author_email"].fillna("").str.contains(BOT_PATTERN, regex=True)
    df = df[~bot_mask]
    # Filter 3: oversized commits
    df = df[df["num_files_in_commit"].fillna(0) <= MAX_FILES_PER_COMMIT]
    # Filter 4+5: non-code paths
    df["_ex"] = df["new_path"].fillna("").apply(is_excluded)
    df = df[~df["_ex"]].drop(columns=["_ex"])
    df.to_csv(OUT, index=False)


if __name__ == "__main__":
    main()
```

---

## 4. Step 03 — Co-change Analysis (Logical Coupling)

**Goal:** measure the *logical coupling* between pairs of files, i.e.
the tendency to be modified together in the same commit.

**Metrics computed** (for each pair `(f₁, f₂)`):

- `support(f₁,f₂)` = number of commits touching both
- `freq(f)` = number of commits touching `f`
- `confidence(f₁→f₂) = support / freq(f₁)` (asymmetric, association-rule style)
- **`jaccard(f₁,f₂) = support / (freq(f₁) + freq(f₂) − support)`**
  reference symmetric metric (Gall 1998; Zimmermann et al. 2005)

**Filter:** only pairs with `support ≥ 5` (below this threshold, the signal is
statistical noise).

```python
#!/usr/bin/env python3
"""03_cochange_analysis.py - Logical coupling between files (co-change analysis)."""
from collections import Counter
from itertools import combinations
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
INP = ROOT / "data" / "commits_filtered.csv"
OUT = ROOT / "data" / "cochange.csv"

MIN_SUPPORT = 5  # standard MSR (pairs cochanged once = statistical noise)


def main():
    df = pd.read_csv(INP, usecols=["commit_hash", "new_path"], low_memory=False)
    df = df[df["new_path"].notna() & (df["new_path"].astype(str) != "")]

    freq = df.groupby("new_path")["commit_hash"].nunique().to_dict()
    commits = df.groupby("commit_hash")["new_path"].apply(set)

    co_counts: Counter = Counter()
    for files in commits.values:
        if len(files) < 2:
            continue
        for a, b in combinations(sorted(files), 2):
            co_counts[(a, b)] += 1

    rows = []
    for (a, b), support in co_counts.items():
        if support < MIN_SUPPORT:
            continue
        fa, fb = freq[a], freq[b]
        rows.append({
            "file_a": a, "file_b": b, "support": support,
            "freq_a": fa, "freq_b": fb,
            "confidence_ab": support / fa,
            "confidence_ba": support / fb,
            "jaccard": support / (fa + fb - support),
        })

    result = pd.DataFrame(rows).sort_values("jaccard", ascending=False)
    result.to_csv(OUT, index=False)


if __name__ == "__main__":
    main()
```

---

## 5. Step 04 — Author Coupling (Socio-technical Coupling)

**Goal:** measure *socio-technical coupling* — two files are
related if the same authors work on them (shared knowledge
among people, not necessarily co-modification).

**Metrics** (two in parallel, on a sparse file × authors matrix):

- **Jaccard on author sets:**
  `jaccard_authors(f₁,f₂) = |A(f₁) ∩ A(f₂)| / |A(f₁) ∪ A(f₂)|`
- **Cosine similarity** on weighted vectors `(file × author → # commits)`:
  `cosine(f₁,f₂) = (v₁ · v₂) / (‖v₁‖ · ‖v₂‖)`
  Cosine weights the *frequency* with which each author works on the file,
  not just binary presence.

**Filters:**
- `MIN_COMMITS_PER_FILE = 5`: files with too short a history → weak signal
- `MIN_COSINE = 0.05` OR `jaccard >= 0.1` (at least one above threshold)
- `TOP_K = 200000`: hard cap for memory safety

`scipy.sparse` is used because the `(files × authors)` matrix is large but
very sparse, and the product `M @ M.T` computes all similarities in a
single operation.

```python
#!/usr/bin/env python3
"""04_author_coupling.py - Socio-technical coupling between files."""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, diags

ROOT = Path(__file__).resolve().parent.parent
INP = ROOT / "data" / "commits_filtered.csv"
OUT = ROOT / "data" / "author_coupling.csv"

MIN_COMMITS_PER_FILE = 5
MIN_COSINE = 0.05
TOP_K = 200000


def main():
    df = pd.read_csv(INP,
                     usecols=["commit_hash", "author_email", "new_path"],
                     low_memory=False)
    df = df[df["new_path"].notna() & (df["new_path"].astype(str) != "")]
    df = df[df["author_email"].notna() & (df["author_email"].astype(str) != "")]

    file_commits = df.groupby("new_path")["commit_hash"].nunique()
    active = file_commits[file_commits >= MIN_COMMITS_PER_FILE].index
    df = df[df["new_path"].isin(active)]

    agg = (df.groupby(["new_path", "author_email"])["commit_hash"]
             .nunique().reset_index())
    agg.columns = ["file", "author", "n"]

    files = sorted(agg["file"].unique())
    authors = sorted(agg["author"].unique())
    fi = {f: i for i, f in enumerate(files)}
    ai = {a: i for i, a in enumerate(authors)}

    rows_idx = agg["file"].map(fi).values
    cols_idx = agg["author"].map(ai).values
    data = agg["n"].values.astype(np.float32)
    M = csr_matrix((data, (rows_idx, cols_idx)),
                   shape=(len(files), len(authors)))
    M_bin = (M > 0).astype(np.float32)

    # Jaccard on author sets
    intersect = (M_bin @ M_bin.T).tocoo()
    degrees = np.asarray(M_bin.sum(axis=1)).flatten()

    # Weighted cosine similarity
    norms = np.asarray(np.sqrt(M.multiply(M).sum(axis=1))).flatten()
    norms[norms == 0] = 1.0
    Mn = diags(1.0 / norms) @ M
    cosine = (Mn @ Mn.T).tocoo()

    cos_dict = {}
    for i, j, v in zip(cosine.row, cosine.col, cosine.data):
        if i < j and v >= MIN_COSINE:
            cos_dict[(i, j)] = float(v)

    rows_out = []
    for i, j, inter_val in zip(intersect.row, intersect.col, intersect.data):
        if i >= j: continue
        inter = int(inter_val)
        if inter < 1: continue
        union = degrees[i] + degrees[j] - inter
        jacc = (inter / union) if union > 0 else 0.0
        cos_v = cos_dict.get((i, j), 0.0)
        if cos_v < MIN_COSINE and jacc < 0.1:
            continue
        rows_out.append({
            "file_a": files[i], "file_b": files[j],
            "shared_authors": inter,
            "jaccard_authors": jacc,
            "cosine_authors": cos_v,
        })

    result = (pd.DataFrame(rows_out)
              .sort_values("cosine_authors", ascending=False))
    if len(result) > TOP_K:
        result = result.head(TOP_K)
    result.to_csv(OUT, index=False)


if __name__ == "__main__":
    main()
```

---

## 6. Step 05 — Graph Construction + Louvain

**Goal:** merge the two signals into a single weighted graph,
detect communities, and aggregate at the package level.

**Linear combination of weights:**

`w(f₁,f₂) = α · jaccard_cochange + β · cosine_authors`  with `α = 0.7, β = 0.3`

The 70/30 weighting favours co-change (primary technical signal) but
keeps the socio-technical component as a meaningful contribution. Threshold:
`w >= 0.10` to keep only edges with a non-marginal signal.

**Community detection:** **Louvain** algorithm (Blondel et al. 2008)
with `random_state=42` for reproducibility. Louvain maximises
*modularity* and scales to large graphs.

**Package-level aggregation:** files are grouped into packages
according to the rule `packages/<n>`, `plugins/<n>`, or the first
segment of the path. For each package pair, the weights of the
file-level edges between them are summed (`weight_sum`).

**Key outputs for the C4:**
- `data/graph_nodes.csv` — (file, package, community, weighted_degree)
- `data/package_edges.csv` — (pkg_a, pkg_b, weight_sum, edge_count)

```python
#!/usr/bin/env python3
"""05_build_graph.py - Knowledge-dependency graph construction."""
from pathlib import Path
import community as community_louvain  # python-louvain
import networkx as nx
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
COCHANGE = ROOT / "data" / "cochange.csv"
AUTHOR = ROOT / "data" / "author_coupling.csv"
GEXF_OUT = ROOT / "output" / "graph.gexf"
NODES_OUT = ROOT / "data" / "graph_nodes.csv"
EDGES_OUT = ROOT / "data" / "graph_edges.csv"
PKG_OUT = ROOT / "data" / "package_edges.csv"

ALPHA = 0.7   # weight of co-change signal
BETA = 0.3    # weight of author-coupling signal
EDGE_THRESHOLD = 0.10


def package_of(path: str) -> str:
    p = (path or "").replace("\\", "/")
    parts = p.split("/")
    if len(parts) >= 2 and parts[0] in ("packages", "plugins"):
        return f"{parts[0]}/{parts[1]}"
    if len(parts) >= 1 and parts[0]:
        return parts[0]
    return "<root>"


def main():
    cc = pd.read_csv(COCHANGE) if COCHANGE.exists() else pd.DataFrame()
    au = pd.read_csv(AUTHOR) if AUTHOR.exists() else pd.DataFrame()

    if not cc.empty:
        cc = cc[["file_a", "file_b", "jaccard", "support"]].rename(
            columns={"jaccard": "jaccard_cc"})
    else:
        cc = pd.DataFrame(columns=["file_a","file_b","jaccard_cc","support"])
    if not au.empty:
        au = au[["file_a", "file_b", "cosine_authors", "shared_authors"]]
    else:
        au = pd.DataFrame(columns=["file_a","file_b","cosine_authors",
                                   "shared_authors"])

    merged = pd.merge(cc, au, on=["file_a", "file_b"], how="outer").fillna(0)
    merged["weight"] = (ALPHA * merged["jaccard_cc"]
                        + BETA * merged["cosine_authors"])
    edges = merged[merged["weight"] >= EDGE_THRESHOLD].copy()
    if edges.empty:
        return

    G = nx.Graph()
    for _, r in edges.iterrows():
        G.add_edge(r["file_a"], r["file_b"],
                   weight=float(r["weight"]),
                   jaccard_cc=float(r["jaccard_cc"]),
                   cosine_auth=float(r["cosine_authors"]),
                   support=int(r["support"]) if r["support"] else 0,
                   shared_authors=int(r["shared_authors"]) if r["shared_authors"] else 0)

    # Louvain community detection
    partition = community_louvain.best_partition(G, weight="weight",
                                                  random_state=42)
    nx.set_node_attributes(G, partition, "community")
    for node in G.nodes():
        G.nodes[node]["package"] = package_of(node)
    degree = dict(G.degree(weight="weight"))
    nx.set_node_attributes(G, degree, "weighted_degree")

    GEXF_OUT.parent.mkdir(parents=True, exist_ok=True)
    nx.write_gexf(G, GEXF_OUT)

    nodes_df = pd.DataFrame([
        {"file": n, "package": G.nodes[n]["package"],
         "community": G.nodes[n]["community"],
         "weighted_degree": G.nodes[n]["weighted_degree"],
         "degree": G.degree[n]}
        for n in G.nodes()
    ]).sort_values("weighted_degree", ascending=False)
    nodes_df.to_csv(NODES_OUT, index=False)

    edges_df = pd.DataFrame([
        {"file_a": u, "file_b": v,
         "weight": d["weight"], "jaccard_cc": d["jaccard_cc"],
         "cosine_auth": d["cosine_auth"], "support": d["support"],
         "shared_authors": d["shared_authors"],
         "community_a": G.nodes[u]["community"],
         "community_b": G.nodes[v]["community"]}
        for u, v, d in G.edges(data=True)
    ]).sort_values("weight", ascending=False)
    edges_df.to_csv(EDGES_OUT, index=False)

    # Package-level aggregation
    edges_df["pkg_a"] = edges_df["file_a"].apply(package_of)
    edges_df["pkg_b"] = edges_df["file_b"].apply(package_of)
    swap = edges_df["pkg_a"] > edges_df["pkg_b"]
    edges_df.loc[swap, ["pkg_a", "pkg_b"]] = \
        edges_df.loc[swap, ["pkg_b", "pkg_a"]].values
    inter = edges_df[edges_df["pkg_a"] != edges_df["pkg_b"]]

    pkg_agg = (inter.groupby(["pkg_a", "pkg_b"])
               .agg(weight_sum=("weight", "sum"),
                    weight_mean=("weight", "mean"),
                    edge_count=("weight", "size"))
               .reset_index()
               .sort_values("weight_sum", ascending=False))
    pkg_agg.to_csv(PKG_OUT, index=False)


if __name__ == "__main__":
    main()
```

---

## 7. Step 07 — C4 Container Diagram Generation

**Conceptual mapping** — C4 (Simon Brown) is reinterpreted
through an MSR lens:

| C4 Concept          | Mapping in the project                                        |
|---------------------|---------------------------------------------------------------|
| `Container`         | Monorepo package (top-N by `weighted_degree`)                 |
| `System_Boundary`   | Louvain community (knowledge-dependency cluster)              |
| `Rel_Neighbor`      | Aggregated inter-package coupling (`weight_sum`)              |

**Readability parameters** (a C4 diagram with all ~200 packages
would be unreadable):
- `TOP_PACKAGES = 25` — most central packages by `total_wd`
- `TOP_EDGES = 35` — strongest edges among the selected packages
- `MAX_CLUSTERS_TO_SHOW = 5` — most represented communities

The filters are not arbitrary: they are *presentation* choices that can be
documented as readability/completeness trade-offs in the report.

**Rendering:**
```
java -jar tools/plantuml.jar -tsvg output/diagrams/04_c4_container.puml
```

```python
#!/usr/bin/env python3
"""07_c4_diagram.py - C4 Container diagram from coupling data."""
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
NODES = ROOT / "data" / "graph_nodes.csv"
PKG_EDGES = ROOT / "data" / "package_edges.csv"
OUT = ROOT / "output" / "diagrams" / "04_c4_container.puml"

TOP_PACKAGES = 25
TOP_EDGES = 35
MAX_CLUSTERS_TO_SHOW = 5


def safe_id(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]", "_", s)
    if s and s[0].isdigit():
        s = "n_" + s
    return s or "n_empty"


def short_label(pkg: str) -> str:
    return pkg.rsplit("/", 1)[-1] if "/" in pkg else pkg


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    nodes = pd.read_csv(NODES)
    pkg_edges = pd.read_csv(PKG_EDGES)

    pkg_files = nodes.groupby("package").size().rename("num_files")
    pkg_wd = nodes.groupby("package")["weighted_degree"].sum().rename("total_wd")
    pkg_comm = (nodes.groupby("package")["community"]
                .agg(lambda x: int(x.mode().iloc[0]) if len(x) else 0)
                .rename("dominant_community"))
    pkg_stats = pd.concat([pkg_files, pkg_wd, pkg_comm], axis=1)
    pkg_stats = pkg_stats.sort_values("total_wd", ascending=False)

    top_pkgs = pkg_stats.head(TOP_PACKAGES).index.tolist()
    comm_counts = (pkg_stats.loc[top_pkgs].groupby("dominant_community").size()
                   .sort_values(ascending=False))
    keep_comms = set(comm_counts.head(MAX_CLUSTERS_TO_SHOW).index)
    top_pkgs = [p for p in top_pkgs
                if pkg_stats.loc[p, "dominant_community"] in keep_comms]

    sub = pkg_edges[pkg_edges["pkg_a"].isin(top_pkgs)
                    & pkg_edges["pkg_b"].isin(top_pkgs)]
    sub = sub.nlargest(TOP_EDGES, "weight_sum")

    lines = [
        "@startuml c4_knowledge_dependencies",
        "!include <C4/C4_Container>",
        "",
        "LAYOUT_WITH_LEGEND()",
        "",
        "title Backstage Knowledge Dependencies - C4 Container View",
        "",
    ]

    by_comm = {}
    for pkg in top_pkgs:
        by_comm.setdefault(int(pkg_stats.loc[pkg, "dominant_community"]),
                           []).append(pkg)

    for comm, pkgs in sorted(by_comm.items(), key=lambda x: -len(x[1])):
        total_files = sum(int(pkg_stats.loc[p, "num_files"]) for p in pkgs)
        lines.append(f'System_Boundary(cluster_{comm}, '
                     f'"Louvain Cluster #{comm} ({total_files} files)") {{')
        for pkg in pkgs:
            pid = safe_id(pkg)
            n_files = int(pkg_stats.loc[pkg, "num_files"])
            label = short_label(pkg)
            descr = f"TypeScript / monorepo"
            tooltip = f"{pkg} - {n_files} modified files"
            lines.append(f'    Container({pid}, "{label}", '
                         f'"{descr}", "{tooltip}")')
        lines.append("}")
        lines.append("")

    lines.append("' --- inter-package couplings ---")
    for _, r in sub.iterrows():
        a, b = safe_id(r["pkg_a"]), safe_id(r["pkg_b"])
        lines.append(f'Rel_Neighbor({a}, {b}, '
                     f'"coupling={r["weight_sum"]:.0f}", '
                     f'"{int(r["edge_count"])} file edges")')

    lines.append("")
    lines.append("@enduml")
    OUT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
```

---

## 8. Parameter Summary (for the report)

Single table of all numerical parameters in the pipeline, for the
*Threats to Validity / Reproducibility* section of the report:

| Step | Parameter | Value | Justification |
|------|-----------|-------|---------------|
| 02 | `MAX_FILES_PER_COMMIT` | 30 | MSR standard; Tornhill suggests ~50 |
| 03 | `MIN_SUPPORT` | 5 | Avoids pairs with a single co-change (noise) |
| 04 | `MIN_COMMITS_PER_FILE` | 5 | Files with short history = unreliable signal |
| 04 | `MIN_COSINE` | 0.05 | Cuts marginal similarities |
| 04 | `TOP_K` | 200 000 | Hard cap for memory safety |
| 05 | `ALPHA` (co-change) | 0.7 | Primary technical signal |
| 05 | `BETA` (author) | 0.3 | Socio-technical as complement |
| 05 | `EDGE_THRESHOLD` | 0.10 | Cuts edges with marginal signal |
| 05 | `random_state` (Louvain) | 42 | Reproducibility |
| 07 | `TOP_PACKAGES` | 25 | C4 readability |
| 07 | `TOP_EDGES` | 35 | C4 readability |
| 07 | `MAX_CLUSTERS_TO_SHOW` | 5 | C4 readability |

## 9. References

- **Gall, Hajek, Jazayeri (1998)** — *Detection of logical coupling based on product release history*. First work on logical coupling.
- **Zimmermann, Weißgerber, Diehl, Zeller (2005)** — *Mining version histories to guide software changes*. Jaccard as the standard metric.
- **Blondel, Guillaume, Lambiotte, Lefebvre (2008)** — *Fast unfolding of communities in large networks*. Louvain algorithm.
- **Brown, Simon** — *The C4 model for software architecture*. `c4model.com`.
- **Tornhill, Adam** — *Your Code as a Crime Scene*. Practical thresholds for MSR.

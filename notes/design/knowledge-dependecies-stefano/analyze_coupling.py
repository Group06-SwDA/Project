import csv
import json
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from pathlib import Path
from collections import defaultdict, Counter

matplotlib.rcParams['figure.dpi'] = 150

BASE = Path(__file__).parent
CSV_FILE = BASE / "coupling.csv"
OUT_DIR = BASE

# Load coupling data (each row = one unique pair, code-maat doesn't duplicate)
seen_pairs = set()
file_couplings = defaultdict(list)  # file -> [(partner, degree)]

with open(CSV_FILE) as f:
    reader = csv.DictReader(f)
    for row in reader:
        entity = row["entity"]
        coupled = row["coupled"]
        degree = int(row["degree"])
        pair = frozenset([entity, coupled])
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        file_couplings[entity].append((coupled, degree))
        file_couplings[coupled].append((entity, degree))

# Build entries: one per file, metric = number of unique coupling partners
entries = []
for f, partners in file_couplings.items():
    entries.append({
        "file": f,
        "couplings": len(partners),
        "avg_degree": round(float(np.mean([d for _, d in partners])), 1),
    })

entries_sorted = sorted(entries, key=lambda x: x["couplings"], reverse=True)
most15 = entries_sorted[:15]
least15 = sorted(entries_sorted, key=lambda x: x["couplings"])[:15]

with open(OUT_DIR / "most15.json", "w") as f:
    json.dump(most15, f, indent=2)
with open(OUT_DIR / "least15.json", "w") as f:
    json.dump(least15, f, indent=2)

print(f"most15.json and least15.json saved in {OUT_DIR}")

coupling_counts = [e["couplings"] for e in entries]

def short_label(path, segments=2):
    parts = path.split("/")
    return "/".join(parts[-segments:]) if len(parts) >= segments else path

# --- 1. Coupling count distribution histogram ---
max_count = max(coupling_counts)
bin_edges = [1, 2, 3, 5, 10, 20, 50]
bins = [b for b in bin_edges if b <= max_count] + [max_count + 1]

fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(coupling_counts, bins=bins, edgecolor="black", color="steelblue")
ax.set_title("Knowledge coupling count distribution")
ax.set_xlabel("Number of coupled files")
ax.set_ylabel("Number of files")
ax.set_xticks(bins)
plt.tight_layout()
plt.savefig(OUT_DIR / "histogram.png")
plt.close()
print("histogram.png saved")

# --- 2. Top 15 files by coupling count ---
fig, ax = plt.subplots(figsize=(13, 7))
names = [short_label(e["file"]) for e in most15]
values = [e["couplings"] for e in most15]
colors = plt.cm.Reds_r(np.linspace(0.2, 0.8, len(names)))
bars = ax.barh(names[::-1], values[::-1], color=colors[::-1])
ax.bar_label(bars, padding=3)
ax.set_title("Top 15 files by number of knowledge couplings")
ax.set_xlabel("Number of coupled files")
plt.tight_layout()
plt.savefig(OUT_DIR / "top15.png")
plt.close()
print("top15.png saved")

# --- 3. Low-coupling files (1 partner) per package —— analog of "leaf files" ---
low_files = [e["file"] for e in entries if e["couplings"] == 1]
package_counts = Counter()
for f in low_files:
    parts = f.split("/")
    package = parts[1] if len(parts) > 2 else parts[0]
    package_counts[package] += 1

top_packages = package_counts.most_common(15)
pkg_names = [p for p, _ in top_packages]
pkg_values = [c for _, c in top_packages]
colors_l = plt.cm.Blues(np.linspace(0.3, 0.8, len(pkg_names)))

fig, ax = plt.subplots(figsize=(12, 7))
bars_l = ax.barh(pkg_names[::-1], pkg_values[::-1], color=colors_l)
ax.bar_label(bars_l, padding=3)
ax.set_title(f"Low-coupling files (1 partner) by package — total: {len(low_files)}")
ax.set_xlabel("Number of files")
plt.tight_layout()
plt.savefig(OUT_DIR / "least15.png")
plt.close()
print("least15.png saved")

# --- 4. Coupling distribution donut (mirrors code deps buckets, shifted: starts at 1) ---
buckets = {"1": 0, "2–5": 0, "6–15": 0, "16+": 0}
for e in entries:
    c = e["couplings"]
    if c == 1:
        buckets["1"] += 1
    elif c <= 5:
        buckets["2–5"] += 1
    elif c <= 15:
        buckets["6–15"] += 1
    else:
        buckets["16+"] += 1

fig, ax = plt.subplots(figsize=(7, 7))
ax.pie(
    buckets.values(),
    labels=buckets.keys(),
    autopct="%1.1f%%",
    startangle=90,
    pctdistance=0.75,
    wedgeprops=dict(width=0.5),
    colors=plt.cm.Set2.colors[:4],
)
ax.set_title("Files by knowledge coupling count range")
plt.tight_layout()
plt.savefig(OUT_DIR / "distribution_donut.png")
plt.close()
print("distribution_donut.png saved")

# --- 5. Text table ---
print(f"\nTotal files with at least one coupling: {len(entries)}")
print(f"Total coupling pairs: {len(seen_pairs)}")

print("\n=== TOP 15 FILES BY KNOWLEDGE COUPLING COUNT ===")
for i, e in enumerate(most15, 1):
    print(f"{i:>2}. {e['couplings']:>3} couplings  avg degree: {e['avg_degree']:>5}  {e['file']}")

print("\n=== 15 FILES WITH FEWEST KNOWLEDGE COUPLINGS ===")
for i, e in enumerate(least15, 1):
    print(f"{i:>2}. {e['couplings']:>3} couplings  avg degree: {e['avg_degree']:>5}  {e['file']}")

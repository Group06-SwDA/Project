"""
Quadrant scatter plot — overview, no labels.

All file pairs plotted by code coupling (X) vs knowledge coupling (Y).
Points coloured by quadrant.

Output: scatter_quadrants.png
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

SCRIPT_DIR    = Path(__file__).parent
DEPS_PATH     = SCRIPT_DIR.parent / "code-dependencies-stefano" / "deps.json"
COUPLING_PATH = SCRIPT_DIR.parent / "knowledge-dependecies-stefano" / "coupling.csv"
OUTPUT_PATH   = SCRIPT_DIR / "scatter_quadrants.png"

CODE_THRESHOLD      = 25
KNOWLEDGE_THRESHOLD = 50

QUAD_COLORS = {
    "aligned":      "#27ae60",
    "stale_import": "#8e44ad",
    "hidden_dep":   "#e67e22",
    "independent":  "#bdc3c7",
}


def load_code_pairs(path: Path) -> dict[tuple, int]:
    with open(path) as f:
        deps = json.load(f)
    pair_count: dict[tuple, int] = {}
    for file, imports in deps.items():
        for imp in imports:
            key = tuple(sorted([file, imp]))
            pair_count[key] = pair_count.get(key, 0) + 1
    return pair_count


def build_df(pair_count, coupling_df) -> pd.DataFrame:
    coupling_df = coupling_df.copy()
    coupling_df["pair"] = coupling_df.apply(
        lambda r: tuple(sorted([r["entity"], r["coupled"]])), axis=1
    )
    all_pairs: dict = {}
    for _, row in coupling_df.iterrows():
        p = row["pair"]
        all_pairs[p] = {
            "file_a": row["entity"],
            "file_b": row["coupled"],
            "knowledge": float(row["degree"]),
            "code": min(pair_count.get(p, 0) * 50.0, 100.0),
        }
    for pair, count in pair_count.items():
        if pair not in all_pairs:
            all_pairs[pair] = {
                "file_a": pair[0],
                "file_b": pair[1],
                "knowledge": 0.0,
                "code": min(count * 50.0, 100.0),
            }
    return pd.DataFrame(all_pairs.values())


def quadrant(code, knowledge) -> str:
    if code > CODE_THRESHOLD and knowledge > KNOWLEDGE_THRESHOLD:
        return "aligned"
    if code > CODE_THRESHOLD:
        return "stale_import"
    if knowledge > KNOWLEDGE_THRESHOLD:
        return "hidden_dep"
    return "independent"


def main():
    pair_count  = load_code_pairs(DEPS_PATH)
    coupling_df = pd.read_csv(COUPLING_PATH)
    df = build_df(pair_count, coupling_df)

    print(f"Total pairs: {len(df)}  "
          f"(from coupling.csv: {len(coupling_df)}, "
          f"code-only: {len(df) - len(coupling_df)})")

    df["quadrant"] = df.apply(lambda r: quadrant(r["code"], r["knowledge"]), axis=1)

    rng = np.random.default_rng(42)
    # Jitter on X to spread the 3 discrete code values (0, 50, 100)
    df["code_jitter"] = df["code"] + rng.uniform(-4, 4, size=len(df))
    # Jitter on Y only for points at knowledge=0 so they don't all stack on the axis
    y_jitter = np.where(df["knowledge"] == 0, rng.uniform(-1.5, 1.5, size=len(df)), 0)
    df["knowledge_jitter"] = df["knowledge"] + y_jitter

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_facecolor("#f9f9f9")
    fig.patch.set_facecolor("#f9f9f9")

    for quad, group in df.groupby("quadrant"):
        ax.scatter(
            group["code_jitter"], group["knowledge_jitter"],
            c=QUAD_COLORS[quad], s=22, alpha=0.5, linewidths=0, zorder=3,
        )

    ax.axvline(CODE_THRESHOLD,      color="#555", lw=1.0, ls="--", alpha=0.6)
    ax.axhline(KNOWLEDGE_THRESHOLD, color="#555", lw=1.0, ls="--", alpha=0.6)

    ax.text(2,  104, "Hidden dependency  (smell)", fontsize=9, color="#e67e22", alpha=0.75, va="top")
    ax.text(60, 104, "Aligned coupling",           fontsize=9, color="#27ae60", alpha=0.75, va="top")
    ax.text(60,   2, "Stale / mysterious import",  fontsize=9, color="#8e44ad", alpha=0.75, va="bottom")
    ax.text(2,    2, "Independent files",          fontsize=9, color="#888",    alpha=0.75, va="bottom")

    counts = df["quadrant"].value_counts()
    legend_handles = [
        mpatches.Patch(color=QUAD_COLORS["hidden_dep"],   label=f"Hidden dependency  ({counts.get('hidden_dep', 0)})"),
        mpatches.Patch(color=QUAD_COLORS["stale_import"], label=f"Stale import         ({counts.get('stale_import', 0)})"),
        mpatches.Patch(color=QUAD_COLORS["aligned"],      label=f"Aligned              ({counts.get('aligned', 0)})"),
        mpatches.Patch(color=QUAD_COLORS["independent"],  label=f"Independent          ({counts.get('independent', 0)})"),
    ]
    ax.legend(handles=legend_handles, loc="center right", fontsize=9,
              framealpha=0.9, title="Quadrant  (n pairs)", title_fontsize=9)

    ax.set_xlabel("Code Coupling  (0 = no import · 50 = one-directional · 100 = bidirectional)", fontsize=10)
    ax.set_ylabel("Knowledge Coupling  (co-commit degree %)", fontsize=10)
    ax.set_xlim(-10, 115)
    ax.set_ylim(-5, 110)
    ax.set_xticks([0, 50, 100])
    ax.yaxis.grid(True, alpha=0.3)
    ax.set_axisbelow(True)
    ax.set_title("Code Coupling vs Knowledge Coupling — Quadrant Overview",
                 fontsize=13, fontweight="bold", pad=12)

    plt.tight_layout()
    plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
    print(f"Saved → {OUTPUT_PATH}")
    print("\n=== Quadrant counts ===")
    print(counts.to_string())


if __name__ == "__main__":
    main()

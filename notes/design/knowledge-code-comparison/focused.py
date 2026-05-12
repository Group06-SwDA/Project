"""
Focused dot charts for the two interesting quadrants.

For each quadrant, shows the top N most significant pairs
with full readable file names.

  focused_hidden_dep.png   — high knowledge, no code import  (hidden dependencies)
  focused_stale_import.png — has code import, low knowledge  (stale / mysterious imports)
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import numpy as np
from pathlib import Path

SCRIPT_DIR    = Path(__file__).parent
DEPS_PATH     = SCRIPT_DIR.parent / "code-dependencies-stefano" / "deps.json"
COUPLING_PATH = SCRIPT_DIR.parent / "knowledge-dependecies-stefano" / "coupling.csv"

CODE_THRESHOLD      = 25
KNOWLEDGE_THRESHOLD = 50
TOP_N               = 15


# ── Data ─────────────────────────────────────────────────────────────────────

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
            "avg_revs": float(row.get("average-revs", 0)),
        }
    for pair, count in pair_count.items():
        if pair not in all_pairs:
            all_pairs[pair] = {
                "file_a": pair[0],
                "file_b": pair[1],
                "knowledge": 0.0,
                "code": min(count * 50.0, 100.0),
                "avg_revs": 0.0,
            }
    return pd.DataFrame(all_pairs.values())


def pair_label(file_a: str, file_b: str) -> str:
    def trim(p: str, n: int = 3) -> str:
        parts = p.split("/")
        return "/".join(parts[-n:]) if len(parts) >= n else p
    return f"{trim(file_a)}   ↔   {trim(file_b)}"


# ── Dot / lollipop chart ──────────────────────────────────────────────────────

def lollipop(ax, values, labels, color, xlabel, title, subtitle):
    y = np.arange(len(labels))
    ax.hlines(y, 0, values, color=color, linewidth=1.8, alpha=0.6)
    ax.scatter(values, y, color=color, s=60, zorder=5)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel(xlabel, fontsize=9)
    ax.set_xlim(0, max(values) * 1.15 + 5)
    ax.xaxis.grid(True, alpha=0.3)
    ax.set_axisbelow(True)
    ax.invert_yaxis()
    ax.set_title(f"{title}\n{subtitle}", fontsize=11, fontweight="bold", pad=10)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    pair_count  = load_code_pairs(DEPS_PATH)
    coupling_df = pd.read_csv(COUPLING_PATH)
    df = build_df(pair_count, coupling_df)

    # ── Chart 1: Hidden dependency (high knowledge, no code import) ──────────
    hidden = (
        df[(df["knowledge"] > KNOWLEDGE_THRESHOLD) & (df["code"] <= CODE_THRESHOLD)]
        .sort_values(["knowledge", "avg_revs"], ascending=[False, False])
        .head(TOP_N)
        .reset_index(drop=True)
    )
    hidden["label"] = hidden.apply(lambda r: pair_label(r["file_a"], r["file_b"]), axis=1)

    fig1, ax1 = plt.subplots(figsize=(14, 0.55 * len(hidden) + 2.5))
    fig1.patch.set_facecolor("#fef9f4")
    ax1.set_facecolor("#fef9f4")
    lollipop(
        ax1,
        hidden["knowledge"].tolist(),
        hidden["label"].tolist(),
        color="#e67e22",
        xlabel="Knowledge coupling  (co-commit degree %)",
        title=f"Hidden Dependencies  — top {len(hidden)} pairs",
        subtitle="High knowledge coupling · No direct code import\n"
                 "These files are always committed together but share no import — potential architectural smell",
    )
    plt.tight_layout()
    out1 = SCRIPT_DIR / "focused_hidden_dep.png"
    plt.savefig(out1, dpi=150, bbox_inches="tight")
    print(f"Saved → {out1}")
    plt.close()

    # ── Chart 2: Stale / mysterious import (code dep, low knowledge) ─────────
    stale = (
        df[(df["code"] > CODE_THRESHOLD) & (df["knowledge"] <= KNOWLEDGE_THRESHOLD)]
        .sort_values(["code", "knowledge"], ascending=[False, True])
        .head(TOP_N)
        .reset_index(drop=True)
    )
    stale["label"] = stale.apply(lambda r: pair_label(r["file_a"], r["file_b"]), axis=1)

    # Two metrics side by side: code score + knowledge score
    fig2, axes = plt.subplots(1, 2, figsize=(18, 0.55 * len(stale) + 2.5), sharey=True)
    fig2.patch.set_facecolor("#faf4fe")
    for ax in axes:
        ax.set_facecolor("#faf4fe")

    fig2.suptitle(
        f"Stale / Mysterious Imports  — top {len(stale)} pairs\n"
        "Direct code import exists · Files rarely or never committed together",
        fontsize=11, fontweight="bold",
    )

    y = np.arange(len(stale))

    # Left: code coupling
    axes[0].hlines(y, 0, stale["code"], color="#8e44ad", lw=1.8, alpha=0.6)
    axes[0].scatter(stale["code"], y, color="#8e44ad", s=60, zorder=5)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(stale["label"], fontsize=8)
    axes[0].set_xlabel("Code coupling  (50 = one-dir · 100 = bidirectional)", fontsize=9)
    axes[0].set_xlim(0, 120)
    axes[0].xaxis.grid(True, alpha=0.3)
    axes[0].set_axisbelow(True)
    axes[0].invert_yaxis()
    axes[0].set_title("Code coupling score", fontsize=10)

    # Right: knowledge coupling
    axes[1].hlines(y, 0, stale["knowledge"], color="#3498db", lw=1.8, alpha=0.6)
    axes[1].scatter(stale["knowledge"], y, color="#3498db", s=60, zorder=5)
    axes[1].set_xlabel("Knowledge coupling  (co-commit degree %)", fontsize=9)
    axes[1].set_xlim(0, 120)
    axes[1].xaxis.grid(True, alpha=0.3)
    axes[1].set_axisbelow(True)
    axes[1].set_title("Knowledge coupling score", fontsize=10)

    plt.tight_layout()
    out2 = SCRIPT_DIR / "focused_stale_import.png"
    plt.savefig(out2, dpi=150, bbox_inches="tight")
    print(f"Saved → {out2}")
    plt.close()


if __name__ == "__main__":
    main()

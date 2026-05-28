import json
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from pathlib import Path

matplotlib.rcParams['figure.dpi'] = 150

BASE = Path(__file__).parent
DEPS_FILE = BASE / "deps.json"
OUT_DIR = BASE

# Load
with open(DEPS_FILE) as f:
    data = json.load(f)

entries = [{"file": k, "deps": len(v)} for k, v in data.items()]
entries_sorted = sorted(entries, key=lambda x: x["deps"], reverse=True)

most15 = entries_sorted[:15]
least15 = sorted(entries_sorted, key=lambda x: x["deps"])[:15]

# Save JSON
with open(OUT_DIR / "most15.json", "w") as f:
    json.dump(most15, f, indent=2)

with open(OUT_DIR / "least15.json", "w") as f:
    json.dump(least15, f, indent=2)

print(f"most15.json and least15.json saved in {OUT_DIR}")

dep_counts = [e["deps"] for e in entries]

def short_label(path, segments=2):
    parts = path.split("/")
    return "/".join(parts[-segments:]) if len(parts) >= segments else path

# --- 1. Dependency distribution histogram ---
fig, ax = plt.subplots(figsize=(10, 5))
bins = [0, 1, 2, 3, 5, 10, 20, 50, max(dep_counts) + 1]
ax.hist(dep_counts, bins=bins, edgecolor="black", color="steelblue")
ax.set_title("Dependency count distribution")
ax.set_xlabel("Number of dependencies")
ax.set_ylabel("Number of files")
ax.set_xticks(bins)
plt.tight_layout()
plt.savefig(OUT_DIR / "histogram.png")
plt.close()
print("histogram.png saved")

# --- 2. Top 15 files by dependency count ---
fig, ax = plt.subplots(figsize=(13, 7))
names = [short_label(e["file"]) for e in most15]
values = [e["deps"] for e in most15]
colors = plt.cm.Reds_r(np.linspace(0.2, 0.8, len(names)))
bars = ax.barh(names[::-1], values[::-1], color=colors[::-1])
ax.bar_label(bars, padding=3)
ax.set_title("Top 15 files by number of dependencies")
ax.set_xlabel("Number of dependencies")
plt.tight_layout()
plt.savefig(OUT_DIR / "top15.png")
plt.close()
print("top15.png saved")

# --- 3. Leaf files (0 deps) per package ---
from collections import Counter
leaf_files = [e["file"] for e in entries if e["deps"] == 0]
package_counts = Counter()
for f in leaf_files:
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
ax.set_title(f"Leaf files (0 dependencies) by package — total: {len(leaf_files)}")
ax.set_xlabel("Number of leaf files")
plt.tight_layout()
plt.savefig(OUT_DIR / "least15.png")
plt.close()
print("least15.png saved")

# --- 4. Dependency distribution donut ---
buckets = {"0": 0, "1–5": 0, "6–15": 0, "16+": 0}
for e in entries:
    d = e["deps"]
    if d == 0:
        buckets["0"] += 1
    elif d <= 5:
        buckets["1–5"] += 1
    elif d <= 15:
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
ax.set_title("Files by dependency count range")
plt.tight_layout()
plt.savefig(OUT_DIR / "distribution_donut.png")
plt.close()
print("distribution_donut.png saved")

# --- 5. Text table ---
print("\n=== TOP 15 FILES BY DEPENDENCY COUNT ===")
for i, e in enumerate(most15, 1):
    print(f"{i:>2}. {e['deps']:>3} deps  {e['file']}")

print("\n=== 15 FILES WITH FEWEST DEPENDENCIES ===")
for i, e in enumerate(least15, 1):
    print(f"{i:>2}. {e['deps']:>3} deps  {e['file']}")

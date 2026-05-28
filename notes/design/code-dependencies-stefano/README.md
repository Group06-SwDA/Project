# Backstage Dependency Analysis

## 1. Generate `deps.json` with madge

```bash
madge --json \
  --extensions ts,tsx \
  --ts-config /Backstage/Backstage_snapshot/tsconfig.json \
  --exclude '\.test\.(ts|tsx)$|\.spec\.(ts|tsx)$|\.stories\.(ts|tsx)$|__mocks__|__fixtures__|__tests__|\.d\.ts$|^\.storybook/' \
  /Backstage/Backstage_snapshot/packages/ \
  /Backstage/Backstage_snapshot/plugins/ \
  > deps.json
```

## 2. Set up Python environment

```bash
cd /home/stealve/madge
python3 -m venv .venv
source .venv/bin/activate
pip install matplotlib
```

## 3. Run the analysis

```bash
python3 analyze_deps.py
```

## Output

| File                       | Description                                              |
| -------------------------- | -------------------------------------------------------- |
| `deps.json`              | Raw dependency graph from madge                          |
| `most15.json`            | Top 15 files by dependency count                         |
| `least15.json`           | 15 files with fewest dependencies                        |
| `histogram.png`          | Dependency count distribution histogram                  |
| `top15.png`              | Top 15 files by number of dependencies                   |
| `least15.png`            | Leaf files (0 deps) grouped by package                   |
| `distribution_donut.png` | Files by dependency count range (0 / 1–5 / 6–15 / 16+) |

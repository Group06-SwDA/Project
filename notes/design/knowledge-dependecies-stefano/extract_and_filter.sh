#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="./Backstage_snapshot"
RAW_LOG="./git_log.log"
FILTERED_LOG="./git_log_filtered.log"

echo "==> Extracting git log from $REPO_DIR ..."
git -C "$REPO_DIR" log --all --numstat --date=short \
    --pretty=format:'--%h--%ad--%aN' \
    --no-renames --no-merges \
    > "$RAW_LOG"
echo "    $(grep -c '^--' "$RAW_LOG") commits extracted -> $RAW_LOG"

echo "==> Applying filters ..."
awk '
BEGIN { RS=""; ORS="\n\n"; FS="\n" }
{
    header = $1
    if (tolower(header) ~ /dependabot|renovate|\[bot\]|goalie|imgbot|github-actions/) next

    out = header; count = 0
    for (i = 2; i <= NF; i++) {
        if ($i == "") continue
        split($i, f, "\t")
        if (length(f) < 3) continue
        p = tolower(f[3])
        if (p ~ /^(\.changeset|node_modules|dist|build|coverage|\.yarn|\.storybook)\//) continue
        if (p ~ /\/__mocks__\/|\/__fixtures__\/|\/__tests__\//) continue
        if (p ~ /\.(test|spec|stories)\.(ts|tsx)$/) continue
        if (p ~ /\.d\.ts$/) continue
        if (p !~ /\.(ts|tsx)$/) continue
        if (p !~ /^(packages|plugins)\//) continue
        out = out "\n" $i; count++
    }
    if (count == 0 || count > 30) next
    print out
}
' "$RAW_LOG" > "$FILTERED_LOG"
echo "    $(grep -c '^--' "$FILTERED_LOG") commits after filtering -> $FILTERED_LOG"

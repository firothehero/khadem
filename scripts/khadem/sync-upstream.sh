#!/usr/bin/env bash
# Merge the latest NousResearch/hermes-agent into this Khadem fork and verify the Arabic layer.
#
#   scripts/khadem/sync-upstream.sh            # merge upstream/main into the current branch + checks
#   SKIP_CHECKS=1 scripts/khadem/sync-upstream.sh
#
# Khadem keeps every change inside plugins/khadem/ (+ its tests and scripts), so upstream merges are
# conflict-free by construction; if a conflict ever appears, KHADEM.md → "Patch ledger" says why.
set -euo pipefail
UPSTREAM_URL="${UPSTREAM_URL:-https://github.com/NousResearch/hermes-agent.git}"
UPSTREAM_BRANCH="${UPSTREAM_BRANCH:-main}"
cd "$(git rev-parse --show-toplevel)"

if ! git remote get-url upstream >/dev/null 2>&1; then
  git remote add upstream "$UPSTREAM_URL"
fi
git fetch --no-tags upstream "$UPSTREAM_BRANCH"

before=$(git rev-parse HEAD)
if ! git merge --no-edit "upstream/$UPSTREAM_BRANCH"; then
  echo "✗ merge conflict — files:" >&2
  git diff --name-only --diff-filter=U >&2
  echo "Resolve per KHADEM.md (Khadem files: keep ours; upstream files: take theirs, then re-apply ledger patches)." >&2
  exit 1
fi
echo "merged $(git rev-list --count "$before"..HEAD) commit(s) from upstream/$UPSTREAM_BRANCH"

if [ "${SKIP_CHECKS:-0}" != "1" ]; then
  scripts/khadem/check.sh
fi

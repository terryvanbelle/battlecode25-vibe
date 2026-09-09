#!/usr/bin/env bash
# Commit one agent's paths without ever writing the SHARED .git/index.
#
#   tools/agent-commit.sh alice -m "message" agents/alice/TRAINING_LOG.md ...
#
# WHY. All three lineages share one working tree and one .git/index. The project
# rule is `git commit --only <paths>`, which is correct but cannot introduce a
# NEW file ("did not match any files known to git") -- and every accepted
# snapshot is a new file. The obvious fix, `git add`, publishes into the shared
# index, where a sibling's commit in the window before yours takes your files
# with it. That has happened, for 1,716 lines of one lineage's work committed
# under another's message.
#
# This builds a PRIVATE index seeded from HEAD, adds there, and commits from it.
# The resulting tree is HEAD + exactly the named paths, so no sibling's
# working-tree state can be swept in, new files included, and .git/index is
# never opened for writing.
#
# Generalised from a helper one lineage wrote for itself, because the hazard is
# identical for all three and a rule that has to be remembered is not a control
# (TRAINING_ALGORITHM doctrine 19). Two subtleties it gets right, both of which
# cost that lineage something before they were understood:
#
#   * after the commit HEAD has moved, but the shared index still holds the OLD
#     blobs for those paths, so `git status` shows them STAGED IN REVERSE and a
#     sibling committing from the index would revert this commit. The last step
#     re-syncs the shared index for the named paths only, leaving a sibling's
#     genuinely staged work untouched.
#   * a sibling's commit landing between read-tree and commit makes git refuse
#     with "cannot lock ref 'HEAD'". Retrying is correct here precisely because
#     the private index is rebuilt from HEAD on each attempt, so the retry
#     carries the sibling's commit forward instead of clobbering it.
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

AGENT="${1:-}"; shift || true
case "$AGENT" in
  alice|bob|carol) ;;
  *) echo "usage: $0 <alice|bob|carol> -m <message> <path>..." >&2; exit 1;;
esac
[ "${1:-}" = "-m" ] || { echo "usage: $0 $AGENT -m <message> <path>..." >&2; exit 1; }
MSG="$2"; shift 2
[ "$#" -gt 0 ] || { echo "no paths given" >&2; exit 1; }

# Paths are relative to the repo root and must be inside this agent's workspace.
# The refusal is the point: it is the same guard as the commit rule, applied
# where the commit happens rather than where the rule is written.
for p in "$@"; do
  case "$p" in
    "agents/$AGENT"/*) ;;
    *) echo "refusing path outside agents/$AGENT/: $p" >&2; exit 1;;
  esac
done

IDX="$(mktemp -t bc25-idx.XXXXXX)"; trap 'rm -f "$IDX"' EXIT
cd "$REPO"
for attempt in 1 2 3 4 5; do
    GIT_INDEX_FILE="$IDX" git read-tree HEAD
    GIT_INDEX_FILE="$IDX" git add -- "$@"
    if GIT_INDEX_FILE="$IDX" git commit -q -m "$MSG"; then break; fi
    [ "$attempt" = 5 ] && { echo "commit failed after 5 attempts" >&2; exit 1; }
    echo "  ref-lock race with a sibling; re-reading HEAD and retrying ($attempt)" >&2
    sleep 2
done
git reset -q HEAD -- "$@"
git log --oneline -1

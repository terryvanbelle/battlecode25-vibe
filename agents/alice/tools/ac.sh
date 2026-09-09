#!/usr/bin/env bash
# Commit alice's paths from ANY working directory.
#
#   tools/ac.sh -m "message" agents/alice/<path> [more...]
#   tools/ac.sh -m "message" TRAINING_LOG.md            # also accepts bare names
#
# WHY THIS EXISTS (doctrine 19 -- install the check where the mistake happens):
# tools/agent-commit.sh takes repo-relative paths, and I habitually `cd` into
# agents/alice to do the work. `git add agents/alice/foo` then resolves to
# agents/alice/agents/alice/foo and dies with "pathspec did not match any files".
# That cost me three failed commits in one session, each time after a long
# heredoc had already run -- so the failure lands *after* the irreplaceable part,
# which is the worst place for it. Remembering to cd back is not a fix; this is.
#
# It cds to the repo root itself and normalises every path argument to
# agents/alice/..., so the same command works from the repo root, from
# agents/alice, or from anywhere else.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

args=()
for a in "$@"; do
  case "$a" in
    -m|--*|-*)            args+=("$a") ;;                       # flags pass through
    agents/alice/*)       args+=("$a") ;;                       # already correct
    */*|*.md|*.sh|*.py|*.java|*.txt)
      # a workspace-relative path: prefix it, but only if that file exists
      if [ -e "agents/alice/$a" ]; then args+=("agents/alice/$a"); else args+=("$a"); fi ;;
    *)                    args+=("$a") ;;                       # message text etc.
  esac
done

exec "$ROOT/tools/agent-commit.sh" alice "${args[@]}"

#!/usr/bin/env bash
# One-shot independent replication of a candidate, on a FRESH random 25-map
# sample rather than the pinned pair it was screened on.
#
# WHY: a matched pair on the pinned samples controls map difficulty, which is
# what makes a -11 or -26 trustworthy. It does NOT make a +2 trustworthy --
# +2 at n=144 is 0.33 sd, inside the noise floor, and the pinned maps are the
# ground the candidate was selected on. The baseline's own fresh-sample score
# is already measured (97/150 on run 20260911-041301), so this is a like-for-
# like comparison on ground neither build was chosen against.
#
# Usage: tools/replicate.sh <package>
set -uo pipefail
ARM="${1:?usage: replicate.sh <package>}"
cd /home/terryvanbelle/projects/vibe/2025/agents/darla

# Wait for the arm queue to drain AND for any gauntlet to finish, so this never
# competes with the screening runs. Matches the RE-EXEC name: gauntlet.sh runs
# from a private copy and the original path never appears in a process listing.
while [ "$(grep -cvE '^\s*(#|$)' progress/pending-arms.txt 2>/dev/null || true)" -gt 0 ] \
   || pgrep -f '\.reexec-gauntlet\.sh' > /dev/null; do sleep 60; done

echo "$(date -uIs) REPLICATE START $ARM -- fresh random 25-map sample"
NMAPS=25 BOT="$ARM" OPPONENTS="carol bob alice" MAXJOBS=2 ../../tools/gauntlet.sh \
  || { echo "$(date -uIs) REPLICATE ERROR $ARM"; exit 1; }
run=$(ls -1t gauntlet | head -1)
echo "$(date -uIs) REPLICATE COMPLETE $ARM $run -- $(grep -E '^overall' gauntlet/$run/summary.txt)"

#!/usr/bin/env bash
# A candidate against ALL THREE lineages on ALL 75 maps, both sides: 450 games.
#
# WHY THIS EXISTS. Two instruments were in use and neither can decide a small
# effect:
#
#   head-to-head (150 games, arm vs baseline)  -- pairs perfectly on (map, side),
#     but its resolution is set by the number of DISCORDANT maps, and a change
#     that only fires on a rare code path diverges on 4 of 75 maps. darla75
#     swept all four 2-0, which is p ~ 0.06 one-sided and cannot be pushed
#     further: the engine is deterministic, so re-running returns the same games.
#
#   replicate.sh (150 games, fresh random 25-map sample vs the roster) -- has
#     genuine run-to-run variance, but the shipped build's own 37 samples have
#     mean 102.5/150 and sd 7.34, so its 2-sd floor is ~15 games. It returned
#     +0.07 sd for darla75. That is not evidence of no effect; it is an
#     instrument that cannot see a 4-game effect.
#
# This run pairs on (opponent, map, side) instead of (map, side), which triples
# the keys -- 450 paired comparisons rather than 150 -- without weakening the
# pairing. The baseline's own 450-game run is the shared reference and is worth
# computing once: every future small-effect arm can be compared against it.
#
# Usage: tools/paired-roster.sh <package>
set -uo pipefail
ARM="${1:?usage: paired-roster.sh <package>}"
cd /home/terryvanbelle/projects/vibe/2025/agents/darla
while [ "$(grep -cvE '^\s*(#|$)' progress/pending-arms.txt 2>/dev/null || true)" -gt 0 ] \
   || pgrep -f '\.reexec-gauntlet\.sh' > /dev/null; do sleep 60; done
echo "$(date -uIs) PAIRED START $ARM -- 75 maps x 3 lineages x 2 sides = 450 games"
MAPS="$(tr '\n' ' ' < ../../tools/bc25-maps.txt)" BOT="$ARM" OPPONENTS="carol bob alice" \
  MAXJOBS=2 ../../tools/gauntlet.sh || { echo "$(date -uIs) PAIRED ERROR $ARM"; exit 1; }
run=$(ls -1t gauntlet | head -1)
echo "$(date -uIs) PAIRED COMPLETE $ARM $run -- $(grep -E '^overall' gauntlet/$run/summary.txt)"

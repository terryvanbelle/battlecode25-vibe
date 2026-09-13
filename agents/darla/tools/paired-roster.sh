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

# Serialize evaluation drivers. The wait-loop below is check-then-act: two drivers
# can both observe "no gauntlet running" in the same second, and on 2026-09-12 that
# put a 450-game paired run and a 150-game head-to-head into ONE output directory --
# the paired run collated the other's games as its own and lost all 450 of its own.
# They also share one VM workspace, so concurrency risks more than directory names.
# Hold a lock for the whole run; 201>&- keeps the gauntlet child from inheriting it.
exec 201>/tmp/darla-eval-driver.lock
flock 201
while [ "$(grep -cvE '^\s*(#|$)' progress/pending-arms.txt 2>/dev/null || true)" -gt 0 ] \
   || pgrep -f '\.reexec-gauntlet\.sh' > /dev/null; do sleep 60; done
echo "$(date -uIs) PAIRED START $ARM -- 75 maps x 3 lineages x 2 sides = 450 games"
MAPS="$(tr '\n' ' ' < ../../tools/bc25-maps.txt)" BOT="$ARM" OPPONENTS="carol bob alice" \
  MAXJOBS=2 ../../tools/gauntlet.sh 201>&- | tee /tmp/darla-run-$$.out || { echo "$(date -uIs) PAIRED ERROR $ARM"; exit 1; }
# Identify the run from the GAUNTLET'S OWN output, never from `ls -1t`. Collation
# rewrites mtimes, so the newest directory is whichever run finished last -- not
# ours. On 2026-09-13 this made paired-roster.sh report "123/150" for darla86 by
# reading an idle-filler run that collated while ours was still playing; the real
# result, 352/450, sat in the directory the gauntlet had already named on stdout.
run=$(sed -n 's/^gauntlet \([0-9-]*\) .*/\1/p' /tmp/darla-run-$$.out | head -1)
rm -f /tmp/darla-run-$$.out
echo "$(date -uIs) PAIRED COMPLETE $ARM $run -- $(grep -E '^overall' gauntlet/$run/summary.txt)"

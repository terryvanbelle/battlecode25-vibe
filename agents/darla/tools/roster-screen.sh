#!/usr/bin/env bash
# ROSTER-SAMPLE SCREEN: a candidate against all three frozen lineages on a PINNED
# 25-map sample, both sides -- 150 games, paired on (opponent, map, side).
#
# WHY, 2026-09-14. The first gate was self-play against the shipped build. Twice
# in one day it disagreed in sign with the frozen roster: darla124/darla129 swept
# 17-20 maps in the mirror and lost on the roster; darla133 scored 88/150 in the
# mirror -- 13 over the bar -- and came in 9 games BELOW the incumbent on the
# 450-game paired roster (McNemar z = -1.08). A bot playing its own predecessor
# measures how it exploits that predecessor's specific habits, which is worth
# nothing against three strangers. Self-play stays as a catastrophe check; this
# is the gate.
#
# The map sample is PINNED (tools/roster-screen-maps.txt, drawn once with a fixed
# seed) so that an arm and the shipped build are paired on identical keys and
# McNemar applies -- replicate.sh's fresh samples cannot be paired. The shipped
# build's own run on this sample is the shared reference; compute it once per
# accepted iteration.
#
# Usage: tools/roster-screen.sh <package>
set -uo pipefail
ARM="${1:?usage: roster-screen.sh <package>}"
cd /home/terryvanbelle/projects/vibe/2025/agents/darla
exec 201>/tmp/darla-eval-driver.lock
flock 201
while [ "$(grep -cvE '^\s*(#|$)' progress/pending-arms.txt 2>/dev/null || true)" -gt 0 ] \
   || pgrep -f '\.reexec-gauntlet\.sh' > /dev/null; do sleep 60; done
echo "$(date -uIs) RSCREEN START $ARM -- 25 pinned maps x 3 lineages x 2 sides"
MAPS="$(tr '\n' ' ' < tools/roster-screen-maps.txt)" BOT="$ARM" OPPONENTS="carol bob alice" \
  MAXJOBS=2 ../../tools/gauntlet.sh 201>&- | tee /tmp/darla-run-$$.out || { echo "$(date -uIs) RSCREEN ERROR $ARM"; exit 1; }
run=$(sed -n 's/^gauntlet \([0-9-]*\) .*/\1/p' /tmp/darla-run-$$.out | head -1)
rm -f /tmp/darla-run-$$.out
echo "$(date -uIs) RSCREEN COMPLETE $ARM $run -- $(grep -E '^overall' gauntlet/$run/summary.txt)"

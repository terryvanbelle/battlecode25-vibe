#!/usr/bin/env bash
# A candidate against THREE MID-LINEAGE SNAPSHOTS, all 75 maps, both sides: 450 games.
#
# WHY: the v3 benchmark said the standing roster does not generalise -- two
# accepted iterations worth +19 and +15 games against alice/bob/carol moved v3 by
# 15-13 of 28 discordant, z=+0.38. And darla86 then split the two existing
# instruments in SIGN. Both point at the same shortage: three opponents, all
# final builds of this project's own family, is a narrow world to be measured in.
#
# These three are accepted snapshots from the middle-late part of each lineage, so
# they are behaviourally different bots rather than weaker copies of the finals.
# They only ever play darla -- the rule that alice, bob and carol never play each
# other is untouched, and no benchmark bot is involved.
set -uo pipefail
ARM="${1:?usage: widen.sh <package>}"
cd /home/terryvanbelle/projects/vibe/2025/agents/darla
exec 201>/tmp/darla-eval-driver.lock
flock 201
while [ "$(grep -cvE '^\s*(#|$)' progress/pending-arms.txt 2>/dev/null || true)" -gt 0 ] \
   || pgrep -f '\.reexec-gauntlet\.sh' > /dev/null; do sleep 60; done
echo "$(date -uIs) WIDEN START $ARM -- 75 maps x 3 mid-lineage snapshots x 2 sides"
MAPS="$(tr '\n' ' ' < ../../tools/bc25-maps.txt)" BOT="$ARM" \
  OPPONENTS="alice_iter39 bob_iter18 carol_iter44" MAXJOBS=2 \
  ../../tools/gauntlet.sh 201>&- | tee /tmp/darla-run-$$.out || { echo "$(date -uIs) WIDEN ERROR $ARM"; exit 1; }
run=$(sed -n 's/^gauntlet \([0-9-]*\) .*/\1/p' /tmp/darla-run-$$.out | head -1)
rm -f /tmp/darla-run-$$.out
echo "$(date -uIs) WIDEN COMPLETE $ARM $run -- $(grep -E '^overall' gauntlet/$run/summary.txt)"

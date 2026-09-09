#!/usr/bin/env bash
# Re-fork src/bob_rush from the CURRENT accepted bot, re-applying only the
# economy-first spawn policy.
#
# WHY THIS ARCHETYPE EXISTS -- it is a REGIME instrument, not a strength one.
# Census over ~4,900 self-play games and 68 opponents (TRAINING_LOG 2026-09-09):
# essentially ZERO ended before round 200, bob_denier's MEDIAN is 949 rounds, and
# the only short-game opponent (examplefuncsplayer) is beaten 100/100 and so can
# show bob failing at nothing. Meanwhile 6.0% of carol's wins land under round 200
# and that is where bob's losses concentrate. So every opening mechanism this
# lineage has evaluated was evaluated in a pool that cannot produce the opening
# failure it targeted -- which is the best account available of the nulls at
# iterations 31, 32 and 33.
#
# Its ACCEPTANCE CRITERION IS THE REGIME, NOT THE WIN RATE: it must produce
# sub-200-round games on small ruin-poor maps. A version of it that bob beats 95%
# of the time is still a good instrument if the games are short; a version that
# goes 50% over 900-round games is useless for the purpose.
#
# THE POLE. bob is units-first: it pumps soldiers and hoards 1200 chips against a
# future tower completion. bob_rush is economy-first -- it keeps unit count low so
# tower paint survives to complete ruin patterns (a pattern is ~120-150 paint and
# buys +5-10 paint/turn FOREVER, while a soldier is 200 paint spent once), holds no
# chip reserve at all, and converts to splashers immediately rather than at round 60.
#
# A CIRCULARITY WARNING, recorded so a later session cannot forget it: this
# archetype's policy overlaps mechanisms this lineage has considered adopting
# (a spawn paint reserve; un-gating splashers). "bob loses to an opponent that does
# X" is therefore NOT evidence that bob should do X -- the archetype was built to
# create a regime, and an opponent built around a mechanism will of course display
# that mechanism. Use it to generate short games; keep the accept gate elsewhere.
#
# Usage: bob-tools/refork-rush.sh          # re-fork
#        bob-tools/refork-rush.sh --check  # report drift, change nothing
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [ "${1:-}" = "--check" ]; then
  drift=0
  [ -d src/bob_rush ] || { echo "src/bob_rush does not exist"; exit 1; }
  for f in src/bob/*.java; do
    b=$(basename "$f"); [ "$b" = Tower.java ] && continue
    diff -q <(sed 's/^package bob;/package X;/' "$f") \
            <(sed 's/^package bob_rush;/package X;/' "src/bob_rush/$b") >/dev/null \
      || { echo "STALE: $b differs from the live bot"; drift=1; }
  done
  [ $drift = 0 ] && echo "bob_rush is in sync with the live bot (Tower.java policy aside)"
  exit $drift
fi

rm -rf src/bob_rush.new && cp -r src/bob src/bob_rush.new
sed -i 's/^package bob;/package bob_rush;/' src/bob_rush.new/*.java
python3 - <<'PY'
import re,sys
p="src/bob_rush.new/Tower.java"
s=open(p).read()

old_res = "        int reserve = rc.getRoundNum() <= 30 ? 0 : 1200;"
new_res = ("        // ARCHETYPE POLICY: economy-first holds NO chip reserve. bob hoards 1200\n"
           "        // against a future tower completion; traced on CastleDefense T1 that left it\n"
           "        // unable to reach the 1600 chips a splasher needs for the whole game.\n"
           "        int reserve = 0;\n"
           "        /** Paint kept back so a soldier can still complete a ruin pattern (~120-150\n"
           "         *  paint) after this spawn. This is the pole: a pattern buys +5-10 paint/turn\n"
           "         *  forever, a soldier spends 200 paint once. */\n"
           "        final int PATTERN_PAINT_RESERVE = 250;")
assert old_res in s, "reserve line not found -- live bot changed shape"
s = s.replace(old_res, new_res)

old_want = """        int slot = spawned % 5;
        UnitType want = (slot == 4) ? UnitType.MOPPER
                       : (((SPLASHER_SLOTS >> slot) & 1) != 0 && rc.getRoundNum() > 60)
                         ? UnitType.SPLASHER
                       : UnitType.SOLDIER;
        if (chips >= want.moneyCost + reserve) {
            int start = G.rng.nextInt(8);"""
new_want = """        int slot = spawned % 5;
        // ARCHETYPE POLICY: splashers from round 1, not round 60. Splashers are the
        // only unit that can OVERWRITE enemy paint, which is what converts a map fast.
        UnitType want = (slot == 4) ? UnitType.MOPPER
                       : (((SPLASHER_SLOTS >> slot) & 1) != 0)
                         ? UnitType.SPLASHER
                       : UnitType.SOLDIER;
        // Draw the direction FIRST, unconditionally, so this policy perturbs the PRNG
        // stream identically regardless of whether the paint guard refuses the spawn
        // (TRAINING_LOG: iteration 33 was VOIDED by exactly this ordering bug).
        if (chips >= want.moneyCost + reserve) {
            int start = G.rng.nextInt(8);
            if (rc.getPaint() - want.paintCost < PATTERN_PAINT_RESERVE) return;"""
assert old_want in s, "spawn block not found -- live bot changed shape"
s = s.replace(old_want, new_want)
open(p,"w").write(s)
print("bob_rush Tower.java policy applied")
PY
rm -rf src/bob_rush && mv src/bob_rush.new src/bob_rush
echo "re-forked src/bob_rush"

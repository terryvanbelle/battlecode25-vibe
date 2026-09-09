#!/usr/bin/env bash
# ITERATION 43. Give the SOLDIER the frontier-seeking its own SPLASHER has had
# since iteration 0.
#
# THE MEASUREMENT THAT MOTIVATES IT (iteration 42, decision-level, 1563 soldier-turns,
# accounting closed exactly with zero anomalies):
#
#   stratum  turns |   A busy  B lowP   C own  D paint  E marked  F noEmpty  UNREACH
#     small    843 |    50.4%    0.9%    1.5%    11.9%      3.9%      25.5%     5.8%
#     large    720 |    26.1%    0.7%   15.8%    43.9%      0.0%       9.6%     3.9%
#
# F = the soldier had NO empty tile within its action radius (r^2 <= 9). It is
# standing inside its own paint. 25.5% of small-map soldier-turns, against 9.6% on
# large -- 2.7x more common in the regime where bob wins 14% than in the one where
# it wins 60%.
#
# And on those turns Soldier.run() calls Nav.wander(): a persistent-direction RANDOM
# WALK that never seeks unpainted ground. Splasher.run() has navigated to the nearest
# empty/enemy tile since iteration 0. The capability is already in this codebase.
#
# THE DOSE is how many turns a soldier commits to walking toward chosen empty ground
# before re-deciding, mirroring the wander-persistence the navigator already uses.
#   SEEK = 0  never seek. EXACT ZERO ARM: `SEEK == 0 ||` short-circuits, so
#             seekEmpty() never runs -- no sensing, no RNG draw, no state touched,
#             and Nav.wander() is reached by the identical path. Byte-identical.
#   SEEK = 3  short commitment, re-targets often
#   SEEK = 8  long commitment, comparable to wander's own 6-15 step persistence
#
# TARGETING is deliberately restricted to tiles with `d > actionRadiusSquared` --
# ground the soldier cannot already paint from where it stands. That is exactly the
# F condition, so the mechanism can only fire on the turns the probe counted, and
# cannot quietly become a general movement rewrite.
#
# THE PRICE, stated before the run (a reallocation is priced against what it
# displaces, not against zero): the displaced use is wandering, which by F's own
# definition produced no paint action that turn -- so the direct cost is near zero.
# The real cost is indirect: a wandering soldier can stumble onto a new ruin, and a
# seeking one is steered by paint instead. If ruin capture falls, that is where it
# will show, and tower count is a registered secondary for that reason.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOB="$(cd "$HERE/.." && pwd)"
cd "$BOB"

for d in 0 3 8; do
    arm="bob_fs$d"
    rm -rf "src/$arm"
    cp -r src/bob "src/$arm"
    for f in "src/$arm"/*.java; do sed -i "s/^package bob;/package $arm;/" "$f"; done

    python3 - "src/$arm/Soldier.java" "$d" <<'PY'
import sys
p, dose = sys.argv[1], sys.argv[2]
s = open(p).read()

old_move = '''        // 3. Movement: toward ruin if working one, else wander.
        if (workRuin != null) {
            Nav.navTo(workRuin);
        } else {
            Nav.wander();
        }'''
assert old_move in s, "movement block changed -- reread Soldier.run() and update this splice"
new_move = '''        // 3. Movement: toward ruin if working one, else seek unpainted ground, else wander.
        if (workRuin != null) {
            Nav.navTo(workRuin);
        } else if (SEEK == 0 || !seekEmpty()) {
            Nav.wander();
        }'''
s = s.replace(old_move, new_move)

helper = '''
    /** ITERATION 43 dose: turns committed to walking toward chosen empty ground
     *  before re-deciding. 0 = never seek = EXACT zero arm (the `SEEK == 0 ||`
     *  short-circuits, so nothing below ever runs and no RNG is drawn). */
    static final int SEEK = %s;
    static MapLocation seekTgt = null;
    static int seekTurns = 0;

    /** Walk toward the nearest visible empty tile that is OUT of action range --
     *  i.e. exactly the situation iteration 42 counted as F. Returns false if there
     *  is nothing to seek, so the caller falls back to the incumbent wander. */
    static boolean seekEmpty() throws GameActionException {
        RobotController rc = G.rc;
        MapLocation me = rc.getLocation();
        if (seekTgt != null) {
            if (--seekTurns <= 0) seekTgt = null;
            else if (rc.canSenseLocation(seekTgt)
                    && rc.senseMapInfo(seekTgt).getPaint() != PaintType.EMPTY) seekTgt = null;
        }
        if (seekTgt == null) {
            int best = Integer.MAX_VALUE;
            for (MapInfo t : rc.senseNearbyMapInfos()) {
                if (t.getPaint() == PaintType.EMPTY && t.isPassable()) {
                    int d = me.distanceSquaredTo(t.getMapLocation());
                    if (d > UnitType.SOLDIER.actionRadiusSquared && d < best) {
                        best = d; seekTgt = t.getMapLocation();
                    }
                }
            }
            if (seekTgt == null) return false;
            seekTurns = SEEK;
        }
        Nav.navTo(seekTgt);
        return true;
    }
''' % dose

k = s.rstrip().rfind('}')
open(p, 'w').write(s[:k] + helper + s[k:])
PY

    grep -q "static final int SEEK = $d;" "src/$arm/Soldier.java" || { echo "!! $arm: dose did not land" >&2; exit 1; }
    grep -q 'SEEK == 0 || !seekEmpty()' "src/$arm/Soldier.java" || { echo "!! $arm: call site did not land" >&2; exit 1; }
    bob-tools/compile-check.sh "$arm" >/dev/null
    echo "$arm  SEEK=$d"
done
echo "bob_fs0 is the EXACT zero arm (short-circuits before any sensing or RNG)"

#!/usr/bin/env bash
# ITERATION 42 SIZING PROBE -- why does a soldier's idle-paint action decline?
#
# WHAT PUTS THIS ON THE TABLE. Iteration 41's census (150 bob-vs-carol tournament
# games, exact unit-rounds at stride 1) put bob's soldiers at 0.665 tiles per
# soldier-round on small maps and 0.778 on large, against a hard ceiling of 1.0.
# Closing that to 1.0 would take bob from 100 to 151 tiles by round 30 -- past
# carol's 146. It is the first mechanism this lineage has found that is the right
# ORDER OF MAGNITUDE for the 75-per-mille small-map coverage gap, rather than the
# ~10x-too-small mechanisms of iterations 37, 40 and 41.
#
# TWO CANDIDATE MECHANISMS, and they call for different fixes:
#
#   E  there ARE empty tiles in the soldier's action radius, but every one of them
#      carries a mark, and paintSomething() refuses any marked tile outright.
#      Fix: paint a marked tile in the MARK'S colour (which is what workOnRuin
#      already does, and cannot break the pattern -- it is what the pattern wants).
#   F  there are no empty tiles in the action radius at all. The soldier is
#      standing inside its own painted territory.
#      Fix: navigation. A soldier with no ruin currently does Nav.wander(), a
#      persistent-direction RANDOM WALK that never seeks unpainted ground -- while
#      Splasher.run() already navigates to the nearest empty/enemy tile.
#
# WHY THIS NEEDS AN IN-BOT PROBE rather than more replay reading. Measured off the
# round-25 grid of one game, 16% of the map's empty tiles are mark-blocked but 69%
# of the empty tiles WITHIN A SOLDIER'S ACTION RADIUS are (9.6 in range, 2.9
# unmarked). Those two numbers are the same quantity against different referents,
# and the global one is the wrong referent for a decision taken at r^2 <= 9
# (measurement doctrine 5). Only the decision point settles E vs F, and only
# in-bot instrumentation sees the decision point (doctrine: instrument the
# DECISION, not the outcome).
#
# The classification is exhaustive over paintSomething's exits, so the codes must
# sum to the soldier-turn count -- an accounting that closes is what licenses
# reading a share off it:
#   A  action already used this turn (ruin work, SRP work, tower attack) -- NOT idle
#   B  paint at or below PAINT_FLOOR
#   C  painted its own tile
#   D  painted an unmarked empty tile in range
#   E  empty tiles in range, ALL marked      <- mechanism E
#   F  no empty tile in range at all         <- mechanism F
#
# INERTNESS. The rewrite of paintSomething splits one compound `if` into two and
# hoists a counter into the existing loop; the same tiles are visited in the same
# order and the same `best` is chosen, so the same action is taken. No RNG is
# drawn (LEARNING 35 / 52). bob_sr0 is a byte-identical baseline, so the
# arm-to-arm identity check validates the instrumented build itself.
#
# The tag is written to G.probeTag and APPENDED by RobotPlayer, never straight to
# setIndicatorString: that is ONE slot per robot per turn and the last writer
# wins silently. Iteration 41's tower probe wrote the slot directly, RobotPlayer's
# bytecode monitor overwrote it, and 24 games recorded not one probe line.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOB="$(cd "$HERE/.." && pwd)"
cd "$BOB"

for arm in bob_sr0 bob_sr1; do
    rm -rf "src/$arm"
    cp -r src/bob "src/$arm"
    for f in "src/$arm"/*.java; do sed -i "s/^package bob;/package $arm;/" "$f"; done
done

python3 - src/bob_sr1 <<'PY'
import sys, os
d = sys.argv[1]

# ---- G: a tag slot any unit can write -------------------------------------
p = os.path.join(d, 'G.java')
s = open(p).read()
k = s.rstrip().rfind('}')
assert k > 0, "G.java has no closing brace"
s = s[:k] + '    /** PROBE ONLY: appended to the indicator string by RobotPlayer. */\n' \
            '    static String probeTag = "";\n' + s[k:]
open(p, 'w').write(s)

# ---- Soldier.paintSomething: classify every exit --------------------------
p = os.path.join(d, 'Soldier.java')
s = open(p).read()
old = '''    static void paintSomething() throws GameActionException {
        RobotController rc = G.rc;
        if (!rc.isActionReady() || rc.getPaint() <= PAINT_FLOOR) return;
        MapLocation me = rc.getLocation();
        if (!rc.senseMapInfo(me).getPaint().isAlly() && rc.canAttack(me)) {
            rc.attack(me);
            return;
        }
        MapLocation best = null;
        int bestD = Integer.MAX_VALUE;
        for (MapInfo t : rc.senseNearbyMapInfos(UnitType.SOLDIER.actionRadiusSquared)) {
            if (t.getPaint() == PaintType.EMPTY && t.isPassable()
                    && t.getMark() == PaintType.EMPTY) {
                MapLocation l = t.getMapLocation();
                int d = me.distanceSquaredTo(l);
                if (d < bestD) { bestD = d; best = l; }
            }
        }
        if (best != null && rc.canAttack(best)) rc.attack(best);
    }'''
assert old in s, "paintSomething body changed -- reread it and update this splice"
new = '''    static int pA, pB, pC, pD, pE, pF;

    static void paintSomething() throws GameActionException {
        RobotController rc = G.rc;
        if (!rc.isActionReady()) { pA++; tag('A'); return; }
        if (rc.getPaint() <= PAINT_FLOOR) { pB++; tag('B'); return; }
        MapLocation me = rc.getLocation();
        if (!rc.senseMapInfo(me).getPaint().isAlly() && rc.canAttack(me)) {
            rc.attack(me);
            pC++; tag('C');
            return;
        }
        MapLocation best = null;
        int bestD = Integer.MAX_VALUE;
        int emptyInRange = 0;
        for (MapInfo t : rc.senseNearbyMapInfos(UnitType.SOLDIER.actionRadiusSquared)) {
            if (t.getPaint() == PaintType.EMPTY && t.isPassable()) {
                emptyInRange++;
                if (t.getMark() == PaintType.EMPTY) {
                    MapLocation l = t.getMapLocation();
                    int d = me.distanceSquaredTo(l);
                    if (d < bestD) { bestD = d; best = l; }
                }
            }
        }
        if (best != null && rc.canAttack(best)) {
            rc.attack(best);
            pD++; tag('D');
            return;
        }
        if (emptyInRange > 0) { pE++; tag('E'); } else { pF++; tag('F'); }
    }

    /** PROBE ONLY. Exhaustive over paintSomething's exits, so A+B+C+D+E+F is the
     *  soldier-turn count and the shares are readable. */
    static void tag(char code) {
        G.probeTag = "IDL " + code + " A" + pA + " B" + pB + " C" + pC
                   + " D" + pD + " E" + pE + " F" + pF;
    }'''
open(p, 'w').write(s.replace(old, new))

# ---- RobotPlayer: APPEND the tag, never overwrite the slot ----------------
p = os.path.join(d, 'RobotPlayer.java')
s = open(p).read()
old = '''                    + " mx=" + maxBc + " p=" + rc.getPaint());'''
assert old in s, "RobotPlayer indicator line changed -- reread it"
open(p, 'w').write(s.replace(old,
    '''                    + " mx=" + maxBc + " p=" + rc.getPaint()
                    + " " + G.probeTag);'''))
PY

for pat in 'pA++' 'emptyInRange++' 'static void tag(char code)'; do
    grep -q "$pat" src/bob_sr1/Soldier.java || { echo "!! bob_sr1: missing $pat" >&2; exit 1; }
done
grep -q 'G.probeTag' src/bob_sr1/RobotPlayer.java || { echo "!! bob_sr1: RobotPlayer append did not land" >&2; exit 1; }
if grep -q 'probeTag' src/bob_sr0/Soldier.java src/bob_sr0/RobotPlayer.java; then
    echo "!! bob_sr0 is not a clean baseline" >&2; exit 1
fi

bob-tools/compile-check.sh bob_sr0 >/dev/null
bob-tools/compile-check.sh bob_sr1 >/dev/null
echo "bob_sr0  baseline (byte-identical to src/bob)"
echo "bob_sr1  + soldier idle-reason probe (A-F), behaviour-inert, compiles"

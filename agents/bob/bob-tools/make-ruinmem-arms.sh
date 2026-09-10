#!/usr/bin/env bash
# ITERATION 58. Give soldiers a MEMORY of ruins.
#
# THE MEASUREMENT (iteration 57, zero games, 75 tournament replays):
#   own-side ruin mark rate   bob 81.6%   alice 91.6%   (bob -10.0 points)
#   contested ruins: alice claims 62.8% first, median lead 361 ROUNDS
#   only 1% of ruins go unmarked by both teams -- every ruin is reachable
#
# THE DEFECT, in bob's own code: chooseRuin() calls ONLY senseNearbyRuins(-1),
# i.e. ruins inside vision r^2<=20. With none visible, workRuin stays null and the
# soldier falls through to Nav.wander() -- a persistent-direction RANDOM WALK.
# Bob has no memory of ruins; it finds them by wandering into them.
#
# NOT CLOSED #6. That entry closed ruin SELECTION/RANKING on the finding that
# bob's mean choice set is 0.83 -- a soldier usually has zero or one visible
# candidate. That number is the motivation here: the set is EMPTY, not badly
# ordered. This changes what is IN the candidate set and leaves ranking alone.
#
# THE DOSE:
#   k0 = 0  EXACT ZERO ARM. RUINMEM is tested before any memory is read or
#           written, so control flow, sensing and RNG consumption are identical
#           to bob_iter20.
#   k1 = 1  remember every ruin sensed; when none is visible, target the nearest
#           remembered ruin not known to be occupied.
#   k2 = 2  also target a remembered ruin when the only visible ones are occupied.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOB="$(cd "$HERE/.." && pwd)"
cd "$BOB"

emit() {
    arm="bob_$1"; d="$2"
    rm -rf "src/$arm"
    cp -r src/bob "src/$arm"
    for f in "src/$arm"/*.java; do sed -i "s/^package bob;/package $arm;/" "$f"; done
    python3 - "src/$arm/Soldier.java" "$d" <<'PY'
import sys
p, d = sys.argv[1], sys.argv[2]
s = open(p).read()

old_f = "    static MapLocation workRuin = null;"
new_f = ("""    /** ITERATION 58 dose. 0 = exact zero arm (tested before any memory is read
     *  or written). 1 = fall back to the nearest remembered unoccupied ruin when
     *  none is visible. 2 = also fall back when every visible ruin is occupied. */
    static final int RUINMEM = %s;

    /** Ruins this soldier has ever sensed, and the ones it has seen occupied.
     *  Per-robot state: a fresh soldier starts blank and fills this in as it
     *  walks, which is why the dose can only help a soldier that has moved. */
    static MapLocation[] seen = new MapLocation[64];
    static boolean[] seenTaken = new boolean[64];
    static int nSeen = 0;

    static void rememberRuins(MapLocation[] ruins) throws GameActionException {
        RobotController rc = G.rc;
        for (int i = ruins.length; --i >= 0; ) {
            MapLocation r = ruins[i];
            boolean taken = rc.senseRobotAtLocation(r) != null;
            int at = -1;
            for (int j = nSeen; --j >= 0; ) if (seen[j].equals(r)) { at = j; break; }
            if (at >= 0) { seenTaken[at] = taken; continue; }
            if (nSeen < seen.length) { seen[nSeen] = r; seenTaken[nSeen] = taken; nSeen++; }
        }
    }

    /** Nearest remembered ruin not known to be occupied, or null. */
    static MapLocation recallRuin(MapLocation me) {
        MapLocation best = null; int bd = Integer.MAX_VALUE;
        for (int j = nSeen; --j >= 0; ) {
            if (seenTaken[j]) continue;
            int dd = me.distanceSquaredTo(seen[j]);
            if (dd < bd) { bd = dd; best = seen[j]; }
        }
        return best;
    }

    static MapLocation workRuin = null;""" % d)
assert old_f in s, "field anchor"
s = s.replace(old_f, new_f, 1)

old_c = """        if (workRuin == null) {
            MapLocation me = rc.getLocation();
            MapLocation[] ruins = rc.senseNearbyRuins(-1);
            int best = Integer.MAX_VALUE;
            for (MapLocation r : ruins) {
                if (rc.senseRobotAtLocation(r) != null) continue; // tower already there
                int d = me.distanceSquaredTo(r);
                if (d < best) { best = d; workRuin = r; }
            }
        }"""
new_c = """        if (workRuin == null) {
            MapLocation me = rc.getLocation();
            MapLocation[] ruins = rc.senseNearbyRuins(-1);
            if (RUINMEM != 0) rememberRuins(ruins);
            int best = Integer.MAX_VALUE;
            boolean sawAny = false;
            for (MapLocation r : ruins) {
                sawAny = true;
                if (rc.senseRobotAtLocation(r) != null) continue; // tower already there
                int d = me.distanceSquaredTo(r);
                if (d < best) { best = d; workRuin = r; }
            }
            // ITERATION 58: nothing visible to work -> fall back to memory rather
            // than to Nav.wander()'s random walk. At dose 2 this also fires when
            // ruins WERE visible but every one of them was already occupied.
            if (workRuin == null && RUINMEM != 0 && (RUINMEM >= 2 || !sawAny)) {
                workRuin = recallRuin(me);
            }
        }"""
assert old_c in s, "chooseRuin anchor"
s = s.replace(old_c, new_c, 1)
open(p, 'w').write(s)
PY
    got=$(grep -oP 'RUINMEM = \K[0-9]+' "src/$arm/Soldier.java")
    [ "$got" = "$d" ] || { echo "!! $arm has RUINMEM=$got, wanted $d" >&2; exit 1; }
    echo "  $arm  RUINMEM=$d"
}

emit k0 0
emit k1 1
emit k2 2
echo "arms written."

#!/usr/bin/env bash
# ITERATION 50. Same mechanism as 49, past the knob's saturation point, and with
# the CANDIDATE SET as the isolated variable.
#
# WHY. Iteration 49 scored d1 = 0 (crowd -3.9%) and d3 = +6 (crowd -35.6%): the
# dose that moved the mechanism moved the score, and the ladder stopped at +6,
# one game under the replicate band. The WEIGHT has almost no headroom left --
# navTo's candidate ranks run 0..4, so at DECLUMP >= 5 crowd strictly dominates
# directness and every larger weight is the identical ordering. The headroom is
# in the CANDIDATE SET: navTo considers 5 of 8 directions (straight, +-45, +-90),
# so a unit boxed in by allies CANNOT step backwards to escape them.
#
# ARMS. Weight is held at full domination in both treated arms (9 > any rank
# used), so the ONLY thing that differs between e9 and e9w is the candidate set.
#   e0  = W 0, narrow  EXACT ZERO ARM (constant tested before anything is sensed)
#   e9  = W 9, narrow  the 49 knob at saturation -- tells me its remaining headroom
#   e9w = W 9, WIDE    all 8 directions ranked by directness (ranks 0..7)
#
# The FALLBACK pass ("take anything") deliberately keeps the original 5
# directions in every arm. Widening it too would let a boxed-in unit walk
# backwards for reasons unrelated to crowding, which is a second mechanism.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOB="$(cd "$HERE/.." && pwd)"
cd "$BOB"

emit() {
    arm="bob_$1"; w="$2"; wide="$3"
    rm -rf "src/$arm"
    cp -r src/bob "src/$arm"
    for f in "src/$arm"/*.java; do sed -i "s/^package bob;/package $arm;/" "$f"; done
    python3 - "src/$arm/Nav.java" "$w" "$wide" <<'PY'
import sys
p, w, wide = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(p).read()

old_field = "public class Nav {\n    static Direction wanderDir = null;"
new_field = ("public class Nav {\n"
"    /** ITERATION 49/50 dose. Steps of directness one adjacent ally is worth.\n"
"     *  0 = the exact zero arm. navTo ranks run 0..4 narrow / 0..7 wide, so any\n"
"     *  weight above the max rank is the same strict ordering. */\n"
"    static final int DECLUMP = %s;\n"
"    /** ITERATION 50: 1 = rank all 8 directions in navTo's crowd-aware pass\n"
"     *  instead of 5, so a unit boxed in by allies can step backwards to escape.\n"
"     *  The FALLBACK pass keeps the original 5 in every arm. */\n"
"    static final int WIDE = %s;\n\n"
"    static int crowdAt(RobotInfo[] allies, MapLocation nl) {\n"
"        int c = 0;\n"
"        for (int j = allies.length; --j >= 0; )\n"
"            if (allies[j].getLocation().distanceSquaredTo(nl) <= 2) c++;\n"
"        return c;\n"
"    }\n\n"
"    static Direction wanderDir = null;") % (w, wide)
assert old_field in s, "field anchor"
s = s.replace(old_field, new_field, 1)

old_nav = """        // first pass: avoid enemy paint
        for (Direction c : cands) {
            if (rc.canMove(c)) {
                MapLocation nl = me.add(c);
                PaintType p = rc.senseMapInfo(nl).getPaint();
                if (!p.isEnemy()) { rc.move(c); return; }
            }
        }"""
new_nav = """        // first pass: avoid enemy paint
        if (DECLUMP == 0) {
            for (Direction c : cands) {
                if (rc.canMove(c)) {
                    MapLocation nl = me.add(c);
                    PaintType p = rc.senseMapInfo(nl).getPaint();
                    if (!p.isEnemy()) { rc.move(c); return; }
                }
            }
        } else {
            Direction[] pick = cands;
            if (WIDE != 0) {
                pick = new Direction[]{
                    d, d.rotateLeft(), d.rotateRight(),
                    d.rotateLeft().rotateLeft(), d.rotateRight().rotateRight(),
                    d.rotateLeft().rotateLeft().rotateLeft(),
                    d.rotateRight().rotateRight().rotateRight(),
                    d.opposite(),
                };
            }
            RobotInfo[] allies = rc.senseNearbyRobots(-1, G.us);
            Direction best = null;
            int bestScore = Integer.MAX_VALUE;
            for (int i = 0; i < pick.length; i++) {
                Direction c = pick[i];
                if (!rc.canMove(c)) continue;
                MapLocation nl = me.add(c);
                if (rc.senseMapInfo(nl).getPaint().isEnemy()) continue;
                int score = crowdAt(allies, nl) * DECLUMP + i;
                if (score < bestScore) { bestScore = score; best = c; }
            }
            if (best != null) { rc.move(best); return; }
        }"""
assert old_nav in s, "navTo anchor"
s = s.replace(old_nav, new_nav, 1)

old_w = """            int start = G.rng.nextInt(8);
            wanderDir = null;
            for (int i = 0; i < 8; i++) {
                Direction c = G.DIRS[(start + i) & 7];
                if (rc.canMove(c)) { wanderDir = c; break; }
            }"""
new_w = """            int start = G.rng.nextInt(8);   // SAME draw, same order -- LEARNINGS 35
            wanderDir = null;
            if (DECLUMP == 0) {
                for (int i = 0; i < 8; i++) {
                    Direction c = G.DIRS[(start + i) & 7];
                    if (rc.canMove(c)) { wanderDir = c; break; }
                }
            } else {
                RobotInfo[] allies = rc.senseNearbyRobots(-1, G.us);
                MapLocation me2 = rc.getLocation();
                int bestScore = Integer.MAX_VALUE;
                for (int i = 0; i < 8; i++) {
                    Direction c = G.DIRS[(start + i) & 7];
                    if (!rc.canMove(c)) continue;
                    int score = crowdAt(allies, me2.add(c)) * DECLUMP + i;
                    if (score < bestScore) { bestScore = score; wanderDir = c; }
                }
            }"""
assert old_w in s, "wander anchor"
s = s.replace(old_w, new_w, 1)
open(p, 'w').write(s)
PY
    gw=$(grep -oP 'DECLUMP = \K[0-9]+' "src/$arm/Nav.java")
    gd=$(grep -oP 'WIDE = \K[0-9]+' "src/$arm/Nav.java")
    [ "$gw" = "$w" ] && [ "$gd" = "$wide" ] || { echo "!! $arm dose mismatch: W=$gw WIDE=$gd" >&2; exit 1; }
    echo "  $arm  DECLUMP=$w WIDE=$wide"
}

emit e0  0 0
emit e9  9 0
emit e9w 9 1
echo "arms written."

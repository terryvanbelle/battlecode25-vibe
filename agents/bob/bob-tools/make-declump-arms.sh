#!/usr/bin/env bash
# ITERATION 49. Prefer LESS-CROWDED tiles when moving.
#
# THE MEASUREMENT (iteration 48, zero games, 18,057 mobile-unit observations over
# 50 games + 75 tournament games as the control):
#
#     crowd per mobile-unit-round   bob 0.687   alice 0.475      (bob +31%)
#     of which mobile-mobile        87.4%   <- avoidable by a movement preference
#     of which tower-adjacency      12.6%   <- not avoidable
#     paint burned on crowding     ~24,900 per game   [LOWER BOUND]
#     paint issued to units         65,022 per game
#
# ENGINE TARGET (InternalRobot.processEndOfTurn, bytecode-verified):
#     crowd = |allied robots within r^2<=2, excluding self|
#     own/neutral paint: -crowd    enemy paint: -2*crowd    EVERY TURN
# Charged on YOUR OWN paint too, and TOWERS COUNT as allies.
#
# WHY THIS IS NOT A TRANSFER, which is the thing that killed iterations 43/45/47.
# Movement and action cooldowns are separate, so a unit that was going to move
# anyway pays nothing to move somewhere less crowded. No displaced unit, no
# shrunken army, no tower pool touched. The registered risk is different and is
# about POSITION, not paint: units cluster because they are going to the same
# place, so spreading them may trade paint for ground that matters.
#
# THE DOSE is a weight. Candidate directions are ranked by directness (index i,
# 0 = straight at the target), and the move chosen minimises
#
#       score = crowd(candidate tile) * DECLUMP + i
#
# so DECLUMP is "how many steps of directness one adjacent ally is worth".
#   d0 = 0  EXACT ZERO ARM. The constant is tested before anything is sensed, so
#           control flow, sensing and RNG consumption are byte-identical to today.
#   d1 = 1  one ally is worth one step of directness.
#   d3 = 3  crowding dominates directness (max rank is 4).
#
# Applied to BOTH navTo and wander's new-direction pick, because the mechanism is
# one thing -- "prefer less-crowded tiles when moving" -- and splitting it would
# under-dose. wander's RNG draws are UNCHANGED in number and order (G.rng.nextInt(8)
# still picks the scan start, G.rng.nextInt(10) still sets the step count), so the
# zero arm stays exact (LEARNINGS 35).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOB="$(cd "$HERE/.." && pwd)"
cd "$BOB"

emit() {
    arm="bob_$1"; w="$2"
    rm -rf "src/$arm"
    cp -r src/bob "src/$arm"
    for f in "src/$arm"/*.java; do sed -i "s/^package bob;/package $arm;/" "$f"; done
    python3 - "src/$arm/Nav.java" "$w" <<'PY'
import sys
p, w = sys.argv[1], sys.argv[2]
s = open(p).read()

old_field = "public class Nav {\n    static Direction wanderDir = null;"
new_field = ("public class Nav {\n"
"    /** ITERATION 49 dose (SHIPPING CODE, not a probe). How many steps of\n"
"     *  directness one adjacent ally is worth when choosing a move. 0 = the\n"
"     *  exact zero arm: tested before anything is sensed, so control flow,\n"
"     *  sensing and RNG consumption are byte-identical to bob_iter20. */\n"
"    static final int DECLUMP = %s;\n\n"
"    /** Allied robots (towers included -- the engine counts them) within r^2<=2\n"
"     *  of `nl`. `allies` is one senseNearbyRobots call hoisted by the caller. */\n"
"    static int crowdAt(RobotInfo[] allies, MapLocation nl) {\n"
"        int c = 0;\n"
"        for (int j = allies.length; --j >= 0; )\n"
"            if (allies[j].getLocation().distanceSquaredTo(nl) <= 2) c++;\n"
"        return c;\n"
"    }\n\n"
"    static Direction wanderDir = null;") % w
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
            // ...and among the legal, non-enemy candidates take the one that
            // minimises crowd*DECLUMP + directness rank. Strict `<` keeps the
            // MORE DIRECT candidate on a tie, so this only ever deviates when it
            // actually buys a paint point.
            RobotInfo[] allies = rc.senseNearbyRobots(-1, G.us);
            Direction best = null;
            int bestScore = Integer.MAX_VALUE;
            for (int i = 0; i < cands.length; i++) {
                Direction c = cands[i];
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
new_w = """            int start = G.rng.nextInt(8);   // SAME draw, same order -- see LEARNINGS 35
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

# wander() has no local for the robot's own location; add one next to its rc.
open(p, 'w').write(s)
PY
    got=$(grep -oP 'DECLUMP = \K[0-9]+' "src/$arm/Nav.java")
    [ "$got" = "$w" ] || { echo "!! $arm has DECLUMP=$got, wanted $w" >&2; exit 1; }
    echo "  $arm  DECLUMP=$w"
}

emit d0 0
emit d1 1
emit d3 3
echo "arms written."

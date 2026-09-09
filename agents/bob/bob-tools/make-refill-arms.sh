#!/usr/bin/env bash
# ITERATION 47. Raise bob's soldier REFILL threshold, to buy SOLDIER-ROUNDS.
#
# THE TERM THIS TARGETS. tiles = acts x conv. CLOSED.md #19/#20/#21 close `conv`
# from both ends and close composition in both directions, leaving `acts` --
# total paint actions per game -- as the only live term (LEARNINGS 82/84). `acts`
# can only rise three ways: more units, units acting more often, or units living
# LONGER. This is the third, and it is the one never touched.
#
# THE DEFECT. Soldier paint capacity is 200 and `REFILL_BELOW = 50`, so a soldier
# runs its stash down to 25% full before it will even consider topping up, and
# `tryRefill()` only fires when an allied tower with >=100 paint is already inside
# vision (r^2<=20). 89% of bob's deaths are starvation (iteration 44: 8.2 starved
# of 9.2 dead per game). A soldier at 150 paint is far likelier to still be near
# the tower it spawned from than one at 40, so triggering EARLIER is what catches
# it while a tower is still in vision. That is the causal claim.
#
# WHAT THIS IS NOT, recorded so the iteration cannot later be re-narrated.
# It is NOT motivated by the low-paint cooldown tax. I checked that first, at the
# bytecode of the pinned 3.1.0 jar (InternalRobot.addActionCooldownTurns):
#
#     X = Math.round(paintAmount * 100.0 / paintCapacity)
#     if (X < 50 && type.isRobotType()) num += Math.round(num * (100 - 2*X) / 100.0)
#     actionCooldownTurns += num          // -10 per round, ready when < 10
#
# For a SOLDIER base num is 10, so the taxed value tops out at 19 at X=1 -- still
# below 20 -- and one decrement always brings it under 10. **The low-paint
# cooldown tax costs a soldier exactly zero rounds at every paint level where it
# can still attack (cost 5).** It is real only for MOPPER (3->5 turns/action) and
# SPLASHER (5->9), and both of those run far below their untaxed action ceiling
# already (0.057 splashes/splasher-round against a 0.20 ceiling; 0.150
# unpaints/mopper-round against 0.333), so cooldown does not bind for them either.
# That whole direction is closed by arithmetic for ZERO games -- see CLOSED.md #22.
#
# THE DOSE is the constant itself. Soldier paint capacity is 200.
#   g0 =  50  EXACT ZERO ARM -- the value bob ships today, so the source is
#             identical to src/bob apart from the package line and this comment.
#   g1 = 100  top up below half full.
#   g2 = 150  top up below three-quarters full.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOB="$(cd "$HERE/.." && pwd)"
cd "$BOB"

emit() {
    arm="bob_$1"; val="$2"
    rm -rf "src/$arm"
    cp -r src/bob "src/$arm"
    for f in "src/$arm"/*.java; do sed -i "s/^package bob;/package $arm;/" "$f"; done
    python3 - "src/$arm/Soldier.java" "$val" <<'PY'
import sys
p, val = sys.argv[1], sys.argv[2]
s = open(p).read()
old = "    static final int REFILL_BELOW = 50;      // start seeking refill when paint below this"
new = ("    // ITERATION 47 dose (SHIPPING CODE, not a probe). Soldier paint capacity is\n"
       "    // 200; this is the stash level below which a soldier will top up at an allied\n"
       "    // tower already in vision. 50 = the value bob ships today = the exact zero arm.\n"
       "    static final int REFILL_BELOW = %s;" % val)
assert old in s, "anchor not found in " + p
s = s.replace(old, new, 1)
open(p, 'w').write(s)
PY
    grep -q "ITERATION 47 dose" "src/$arm/Soldier.java" || { echo "!! dose did not land in $arm" >&2; exit 1; }
    got=$(grep -oP 'REFILL_BELOW = \K[0-9]+' "src/$arm/Soldier.java")
    [ "$got" = "$val" ] || { echo "!! $arm has REFILL_BELOW=$got, wanted $val" >&2; exit 1; }
    echo "  $arm  REFILL_BELOW=$val"
}

emit g0 50
emit g1 100
emit g2 150
echo "arms written."

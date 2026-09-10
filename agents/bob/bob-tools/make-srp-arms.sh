#!/usr/bin/env bash
# ITERATION 61. ABLATE iteration 12's accepted SRP mechanism.
#
# WHY ABLATE AN ACCEPTED MECHANISM. Iteration 12 accepted SRPs long ago against a
# different opponent, and an accepted mechanism becomes a premise. Measured now:
#
#   mark provenance (iter56, 75 tournament games)   bob 34.4% SRP (135/game)
#                                                 alice  1.4% SRP  (4/game)
#
# Bob pours soldier effort into Special Resource Patterns that the lineage beating
# it 60-40 essentially does not build. And iterations 56-60 closed EVERY other
# mechanism for bob's own-side ruin gap -- ranking, abandonment, memory, symmetry
# inference, dispersal -- while the defect stands: bob misses 2.2x alice's
# own-side ruins AT THE SAME DISTANCES, with the SAME army, from the SAME start.
# The soldiers are present and doing something else. This is the something else.
#
# THE DOSE is the chip gate on starting an SRP. workOnSrp() tests it BEFORE any
# sensing and before any RNG draw, so a raised gate is a clean ablation:
#   s0 =        500  EXACT ZERO ARM (the shipping value).
#   s1 =       3000  partial -- SRPs only when chips are plentiful.
#   s2 =  999999999  FULL ABLATION -- no SRP is ever started.
#
# THE PAYER, named before building (doctrine 46): an active SRP gives +3 resource
# per turn to EVERY allied mining tower (engine-verified, RULES.md), and bob
# completes ~3.67 SRPs a game. Ablating them costs PAINT INCOME. If ruin marks
# rise and paint income falls in proportion, this is a transfer and I will say so.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOB="$(cd "$HERE/.." && pwd)"
cd "$BOB"

emit() {
    arm="bob_$1"; v="$2"
    rm -rf "src/$arm"
    cp -r src/bob "src/$arm"
    for f in "src/$arm"/*.java; do sed -i "s/^package bob;/package $arm;/" "$f"; done
    python3 - "src/$arm/Soldier.java" "$v" <<'PY'
import sys
p, v = sys.argv[1], sys.argv[2]
s = open(p).read()
old = "    static final int SRP_MIN_CHIPS = 500;"
new = ("    /** ITERATION 61 ablation. Chips required before STARTING an SRP.\n"
       "     *  500 = the shipping value = the exact zero arm. A raised gate is a\n"
       "     *  clean ablation because workOnSrp() tests it before any sensing and\n"
       "     *  before any RNG draw, so control flow above it is unchanged. */\n"
       "    static final int SRP_MIN_CHIPS = %s;" % v)
assert old in s, "anchor not found in " + p
s = s.replace(old, new, 1)
open(p, 'w').write(s)
PY
    got=$(grep -oP 'SRP_MIN_CHIPS = \K[0-9]+' "src/$arm/Soldier.java")
    [ "$got" = "$v" ] || { echo "!! $arm has SRP_MIN_CHIPS=$got, wanted $v" >&2; exit 1; }
    echo "  $arm  SRP_MIN_CHIPS=$v"
}

emit s0 500
emit s1 3000
emit s2 999999999
echo "arms written."

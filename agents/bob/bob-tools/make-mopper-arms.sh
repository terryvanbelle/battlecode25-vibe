#!/usr/bin/env bash
# ITERATION 45. Raise bob's MOPPER share, and price what it displaces.
#
# THE MEASUREMENT (iteration 44, all 300 bob games of tournament 20260909-1300,
# engine-derived counters, r<=200):
#
#   team   | spawn sold% spl% mop% | alive sold% spl% mop% | unpaint/game | dTiles(small)
#   alice  |  70.6  0.9  28.5      |  74.9  0.5  24.6      |     47.0     |    309.5
#   bob    |  74.2 15.2  10.6      |  83.5  9.3   7.1      |     15.5     |    218.4
#   carol  |  37.4 62.5   0.0      |  42.5 57.4   0.0      |      0.1     |    332.1
#
# A SOLDIER CANNOT PAINT OVER ENEMY PAINT (engine 3.1.0, and already noted in
# Tower.java's iteration-20 comment). Only moppers and splashers can clear it.
# Alice unpaints 47 tiles a game; bob 15.5. On small maps alice gains 309 tiles
# of coverage to bob's 218.
#
# NOT the closed direction. Iteration 41 CLOSED "add a cheaper-unit fallback to
# the spawn rotation" (priced at ~0.8 units per 120 rounds). This is a different
# knob: WHICH SLOTS build moppers. Mopper paint cost is 100, the cheapest unit,
# and bob's towers live at 185-210 paint, so mopper slots never stall.
#
# THE DOSE is a bitmask over (spawned % 5), evaluated BEFORE the splasher test.
# Slots today: 0,1 SOLDIER  2,3 SPLASHER  4 MOPPER.
#   m0 = 0b10000  slot 4 only. EXACT ZERO ARM: the expression reduces to the
#                 original `slot == 4`, so no behaviour, no RNG, no state changes.
#   mS = 0b10010  slots 1,4 -- the extra mopper is paid for by a SOLDIER.
#   mL = 0b11000  slots 3,4 -- the extra mopper is paid for by a SPLASHER.
#   mX = 0b11010  slots 1,3,4 -- one of each, the extended dose.
#
# mS and mL are the SAME mopper share bought from DIFFERENT units. That is
# deliberate: LEARNING 76 says a mechanism that pays for itself out of the army
# scores well on a per-unit ratio and nothing on the objective, so the
# displacement is the thing to measure, not a nuisance to average over.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOB="$(cd "$HERE/.." && pwd)"
cd "$BOB"

emit() {
    arm="bob_$1"; mask="$2"
    rm -rf "src/$arm"
    cp -r src/bob "src/$arm"
    for f in "src/$arm"/*.java; do sed -i "s/^package bob;/package $arm;/" "$f"; done
    python3 - "src/$arm/Tower.java" "$mask" <<'PY'
import sys
p, mask = sys.argv[1], sys.argv[2]
s = open(p).read()
old = """        UnitType want = (slot == 4) ? UnitType.MOPPER"""
new = """        // ITERATION 45 dose (SHIPPING CODE, not a probe). Which of the 5 spawn
        // slots build a MOPPER, as a bitmask over (spawned %% 5). 0b10000 = slot 4
        // only = the exact zero arm, reducing to the original `slot == 4`.
        final int MOPPER_SLOTS = %s;
        UnitType want = (((MOPPER_SLOTS >> slot) & 1) != 0) ? UnitType.MOPPER""" % mask
assert old in s, "anchor not found in " + p
s = s.replace(old, new, 1)
open(p, 'w').write(s)
PY
    grep -q "MOPPER_SLOTS" "src/$arm/Tower.java" || { echo "!! dose did not land in $arm" >&2; exit 1; }
    echo "  $arm  MOPPER_SLOTS=$mask"
}

emit m0 0b10000
emit mS 0b10010
emit mL 0b11000
emit mX 0b11010
echo "arms written."

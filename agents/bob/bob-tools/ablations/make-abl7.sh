#!/usr/bin/env bash
# Ablation A7: bob_iter9 with iteration 7's avalanche hash REMOVED, i.e. tower type
# chosen by iteration 1's team-symmetric parity rule ((x+y)&1). Everything else is
# iteration 9 verbatim. Builds src/bob_abl7 (package bob_abl7).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
rm -rf src/bob_abl7
cp -r src/bob_iter9 src/bob_abl7
sed -i 's/^package bob_iter9;/package bob_abl7;/' src/bob_abl7/*.java
python3 - <<'PY'
import re, pathlib
p = pathlib.Path('src/bob_abl7/Soldier.java')
s = p.read_text()
# replace the whole avalanche-hash body with iteration 1's parity rule
old_start = s.index('        int h = ruin.x * 0x27D4EB2D')
old_end = s.index('LEVEL_ONE_MONEY_TOWER : UnitType.LEVEL_ONE_PAINT_TOWER;', old_start) + len('LEVEL_ONE_MONEY_TOWER : UnitType.LEVEL_ONE_PAINT_TOWER;')
new = """        // ABLATION A7: iteration 7's avalanche hash removed; back to iteration 1's
        // team-symmetric parity rule. Under rotation (x+y) and (W-1-x + H-1-y) share
        // parity whenever W+H is even, so mirrored ruins agree on those maps and the
        // two halves get the same mix -- which is the property iteration 7 gave up.
        return ((ruin.x + ruin.y) & 1) == 0
            ? UnitType.LEVEL_ONE_MONEY_TOWER : UnitType.LEVEL_ONE_PAINT_TOWER;"""
p.write_text(s[:old_start] + new + s[old_end:])
print("A7: avalanche hash -> parity rule")
PY
bob-tools/compile-check.sh bob_abl7

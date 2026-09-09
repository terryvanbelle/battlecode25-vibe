#!/usr/bin/env bash
# Iteration 40 arms: the SMALL_AREA dose ladder, forked from the working-tree src/bob.
#   bob_sa0  SMALL_AREA    0  gate never relaxed        <- EXACT zero arm
#   bob_sa1  SMALL_AREA 1000  relax below 1000 tiles (~22 of 75 maps)
#   bob_sa2  SMALL_AREA 1500  relax below 1500 tiles (~35 of 75 maps)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOB="$(cd "$HERE/.." && pwd)"
cd "$BOB"
grep -q 'static final int SMALL_AREA' src/bob/Tower.java || {
    echo "!! src/bob/Tower.java carries no SMALL_AREA constant" >&2; exit 1; }
i=0
for d in 0 1000 1500; do
    arm="bob_sa$i"
    rm -rf "src/$arm"; cp -r src/bob "src/$arm"
    for f in "src/$arm"/*.java; do sed -i "s/^package bob;/package $arm;/" "$f"; done
    sed -i "s/static final int SMALL_AREA = 0;/static final int SMALL_AREA = $d;/" "src/$arm/Tower.java"
    [ "$(grep -c "static final int SMALL_AREA = $d;" "src/$arm/Tower.java")" = 1 ] || {
        echo "!! $arm: SMALL_AREA not set to $d" >&2; exit 1; }
    echo "$arm  SMALL_AREA=$d"; i=$((i+1))
done

#!/usr/bin/env bash
# Iteration 38 arms: the MARKCLEAN dose ladder, forked from the working-tree src/bob.
#
#   bob_mk0  MARKCLEAN 0  unchanged                          <- EXACT zero arm
#   bob_mk1  MARKCLEAN 1  clear marks around finished towers
#   bob_mk2  MARKCLEAN 2  ... and around finished SRP centres
#
# bob_mk0 is exact by construction: cleanStaleMarks() returns on the constant before
# any sensing call, so control flow and RNG consumption match bob_iter20 exactly. It
# must come out 25/50 with all 25 maps split, as iteration 27b's and 37's zero arms
# did -- that check validates this generator, not just the hypothesis.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOB="$(cd "$HERE/.." && pwd)"
cd "$BOB"
grep -q 'static final int MARKCLEAN' src/bob/Soldier.java || {
    echo "!! src/bob/Soldier.java carries no MARKCLEAN constant" >&2; exit 1; }
for d in 0 1 2; do
    arm="bob_mk$d"
    rm -rf "src/$arm"
    cp -r src/bob "src/$arm"
    for f in "src/$arm"/*.java; do
        sed -i "s/^package bob;/package $arm;/" "$f"
    done
    sed -i "s/static final int MARKCLEAN = 0;/static final int MARKCLEAN = $d;/" "src/$arm/Soldier.java"
    got=$(grep -c "static final int MARKCLEAN = $d;" "src/$arm/Soldier.java")
    [ "$got" = 1 ] || { echo "!! $arm: MARKCLEAN not set to $d" >&2; exit 1; }
    echo "$arm  MARKCLEAN=$d"
done

#!/usr/bin/env bash
# Iteration 38 FOLLOW-UP PROBE. The mark-cleaning arms completed FEWER SRPs, not more.
#
# THE SUSPICION: my safety argument was that a mark is removed only when "the pattern it
# belongs to" is finished. But cleanStaleMarks does not test what pattern a mark belongs
# to -- it tests whether the TILE is within Chebyshev 2 of a ruin carrying a tower. A tile
# can satisfy that AND be part of an in-progress SRP, because cleaning is exactly what
# opens the rings around towers for SRP siting in the first place. If so, a second
# soldier's janitor pass erases a first soldier's in-progress SRP marks, the pattern can
# never complete, and the builder burns its 25 paint and 120 turns of patience.
#
# THE DISCRIMINATOR: that story predicts MORE SRP starts and FEWER completions in the
# cleaning arm. A bare "fewer completions" is also consistent with the arm simply losing
# more, so starts are what separate the hypotheses. Emit a marker on markResourcePattern
# (start) and on patience expiry (drop), alongside the existing completion marker.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOB="$(cd "$HERE/.." && pwd)"
cd "$BOB"
for d in 0 1; do
    arm="bob_mkp$d"
    rm -rf "src/$arm"
    cp -r src/bob "src/$arm"
    for f in "src/$arm"/*.java; do sed -i "s/^package bob;/package $arm;/" "$f"; done
    sed -i "s/static final int MARKCLEAN = 0;/static final int MARKCLEAN = $d;/" "src/$arm/Soldier.java"
    # start marker, immediately after the pattern is marked
    perl -0pi -e 's/(\s+)rc\.markResourcePattern\(me\);/$1rc.markResourcePattern(me);$1rc.setTimelineMarker("SRPmark", 200, 200, 0);/' "src/$arm/Soldier.java"
    # drop marker, when patience expires
    perl -0pi -e 's/if \(srp != null \&\& \+\+srpTurns > SRP_PATIENCE\) srp = null;/if (srp != null \&\& ++srpTurns > SRP_PATIENCE) { rc.setTimelineMarker("SRPdrop", 255, 0, 0); srp = null; }/' "src/$arm/Soldier.java"
    for pat in 'MARKCLEAN = '"$d"';' 'SRPmark' 'SRPdrop'; do
        grep -q "$pat" "src/$arm/Soldier.java" || { echo "!! $arm: missing $pat" >&2; exit 1; }
    done
    echo "$arm  MARKCLEAN=$d  + SRPmark/SRPdrop instrumentation"
done

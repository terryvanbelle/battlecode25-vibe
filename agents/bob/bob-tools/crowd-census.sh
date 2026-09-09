#!/usr/bin/env bash
# ITERATION 48: how much paint does bob burn on the CROWDING penalty?
#
#   bob-tools/crowd-census.sh <run-id> <name-filter> [every]
#
# Renders the arena every <every> rounds with ReplayDump's existing --map mode and
# prints the raw frames, prefixed by file. bob-tools/crowd_agg.py does the counting.
#
# ENGINE TARGET (InternalRobot.processEndOfTurn, bytecode-verified 2026-09-09):
#     crowd = |getAllRobotsWithinRadiusSquared(myLoc, 2, myTeam)| excluding self
# and the robot pays -crowd paint on its own/neutral paint, -2*crowd on enemy paint,
# EVERY TURN. r^2 <= 2 is exactly the 8 surrounding cells, so grid row order does not
# matter. `crowd` counts TOWERS as well as mobile units.
#
# WHY SAMPLING IS LEGITIMATE HERE, given LEARNINGS 85 says it is not elsewhere:
# crowd is an INSTANTANEOUS quantity, so sampling rounds estimates its mean without
# bias. LEARNINGS 85's stride bug bit a CUMULATIVE counter, where skipped rounds are
# dropped rather than averaged. Different estimator, different failure mode -- and
# --map samples proportionally to game length, so long games contribute more frames,
# which is what a per-unit-round mean wants.
#
# Reuses tools/replaydump/ReplayDump.java verbatim -- not a fork.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
source "$REPO/tools/lib.sh"
RUN="$1"; FILT="${2:-}"; EVERY="${3:-100}"
WANT_VER="$(cat "$REPO/arena/engine_version.txt")"
case "$RUN" in
  /*|~*|\$*) RDIR="$RUN" ;;
  *)     RDIR="\$HOME/battlecode25-vibe/agents/bob/gauntlet/$RUN" ;;
esac
ensure_vm
W="bobcrowd-$$"
gssh "mkdir -p ~/$W" >/dev/null
trap 'gssh "rm -rf ~/'"$W"'" >/dev/null 2>&1 || true' EXIT
gscp "$REPO/tools/replaydump/ReplayDump.java" "$USER_NAME@$IP:$W/" >/dev/null
gssh "
  export PATH=\$HOME/jdk21/bin:\$PATH
  BC_JAR=\$(find ~/.gradle -name 'battlecode25-java-$WANT_VER.jar' | grep -v source | head -1)
  [ -n \"\$BC_JAR\" ] || { echo '!! no pinned engine jar' >&2; exit 1; }
  cd ~/$W
  javac -d . -classpath \"\$BC_JAR\" ReplayDump.java 2>&1 | head -3
  for f in $RDIR/*$FILT*.bc25; do
    b=\$(basename \"\$f\")
    # ISOLATION: drop every IND line at the source (RULES.md 2026-09-09), unconditionally,
    # so this script can never be the one that leaks a tournament replay's debug output.
    java -classpath \".:\$BC_JAR\" com.google.flatbuffers.ReplayDump \"\$f\" --map $EVERY 2>/dev/null |
      grep -v ' IND ' |
      awk -v F=\"\$b\" '
        /^=== GameHeader/ { if (match(\$0,/team1=[^ ]+/)) t1=substr(\$0,RSTART+6,RLENGTH-6);
                            if (match(\$0,/team2=[^ ]+/)) t2=substr(\$0,RSTART+6,RLENGTH-6);
                            printf \"HDR\t%s\t%s\t%s\n\", F, t1, t2; next }
        /^=== ARENA round/ { printf \"ARENA\t%s\t%s\n\", F, \$4; ingrid=1; next }
        /^=== / && !/^=== ARENA/ { ingrid=0 }
        ingrid==1 && /^ *[0-9]+ [.#oabABtndsmpTNDSMP*]+$/ {
            y=\$1; row=\$2; printf \"G\t%s\t%s\t%s\n\", F, y, row }'
  done
"

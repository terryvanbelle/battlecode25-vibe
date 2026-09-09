#!/usr/bin/env bash
# Per-replay census of PATTERN COMPLETIONS and BYTECODE HEALTH, over a gauntlet run's
# replays ON battlecode-dev. Compiles ReplayDump once on the VM and loops there.
#
# WHY THIS EXISTS (iteration 38). Two quantities, both already in the replays, neither
# costing a single new game:
#
#  1. MECHANISM CHECK. Soldier.workOnSrp() calls setTimelineMarker("SRP") on every
#     completed resource pattern and workOnRuin() calls setTimelineMarker("tower built"),
#     so counting markers counts completions. MatchMaker.addTimelineMarker is uncapped
#     (a plain ArrayList) but IS gated on showIndicators -- verified live 2026-09-09 that
#     gauntlet replays do carry markers, so a zero here means zero completions and not a
#     switched-off instrument. Re-verify that if the runner's flags ever change.
#
#  2. BYTECODE CONFOUND. RobotPlayer's monitor writes "ov=<overruns> bc=<used>/<limit>
#     mx=<max>" into the indicator string every turn. A candidate that adds sensing can
#     lose games by overrunning the limit rather than by its policy, and an EXACT zero arm
#     cannot detect that -- the zero arm short-circuits before the new code. So read the
#     overrun count on the ARMS, not just on the null.
#
# ReplayDump labels robots "idN(T1,SOLDIER)", so team attribution comes from the label.
# TimelineMarker.team() is 0-based in the schema and ReplayDump already prints team()+1;
# do not re-correct it here.
#
#   bob-tools/srp-census.sh <remote-replay-dir> [name-filter]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
source "$REPO/tools/lib.sh"
RDIR="$1"; FILT="${2:-bob}"
WANT_VER="$(cat "$REPO/arena/engine_version.txt")"
ensure_vm
RUN="bobsrp-$$"
gssh "mkdir -p ~/$RUN" >/dev/null
trap 'gssh "rm -rf ~/'"$RUN"'" >/dev/null 2>&1 || true' EXIT
gscp "$REPO/tools/replaydump/ReplayDump.java" "$USER_NAME@$IP:$RUN/" >/dev/null
echo "file,srp1,srp2,tower1,tower2,ov1,ov2,mx1,mx2,rounds"
gssh "
  export PATH=\$HOME/jdk21/bin:\$PATH
  BC_JAR=\$(find ~/.gradle -name 'battlecode25-java-$WANT_VER.jar' | grep -v source | head -1)
  [ -n \"\$BC_JAR\" ] || { echo '!! no pinned engine jar' >&2; exit 1; }
  cd ~/$RUN
  javac -d . -classpath \"\$BC_JAR\" ReplayDump.java 2>&1 | head -3
  for f in $RDIR/*$FILT*.bc25; do
    b=\$(basename \"\$f\")
    java -classpath \".:\$BC_JAR\" com.google.flatbuffers.ReplayDump \"\$f\" 2>/dev/null |
      awk -v F=\"\$b\" '
        /marker r[0-9]+ team1 SRP/          { s1++ }
        /marker r[0-9]+ team2 SRP/          { s2++ }
        /marker r[0-9]+ team1 tower built/  { t1++ }
        /marker r[0-9]+ team2 tower built/  { t2++ }
        /IND / {
          team = (\$0 ~ /\\(T1,/) ? 1 : 2
          if (match(\$0, /ov=[0-9]+/))  { v = substr(\$0, RSTART+3, RLENGTH-3) + 0; if (team==1 && v>o1) o1=v; if (team==2 && v>o2) o2=v }
          if (match(\$0, /mx=[0-9]+/))  { v = substr(\$0, RSTART+3, RLENGTH-3) + 0; if (team==1 && v>m1) m1=v; if (team==2 && v>m2) m2=v }
        }
        /^round / { rn=\$2 }
        END { printf \"%s,%d,%d,%d,%d,%d,%d,%d,%d,%d\n\", F, s1,s2,t1,t2,o1,o2,m1,m2,rn }'
  done
"

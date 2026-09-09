#!/usr/bin/env bash
# Batch early-game census over a directory of replays ON battlecode-dev.
#
# WHY: tools/replay-dump.sh copies+compiles per replay, which is right for one
# game and far too slow for 150. This compiles ReplayDump ONCE on the VM and
# loops there, printing one CSV row per replay:
#   file,map,team1,team2,rounds,winner,winType, and per-team coverage/units at
#   the sampled early rounds.
#
# It reuses tools/replaydump/ReplayDump.java verbatim -- it is NOT a fork, so a
# fix to that file is picked up here automatically.
#
#   bob-tools/early-census.sh <remote-replay-dir> <name-filter> [--at N]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
source "$REPO/tools/lib.sh"
RDIR="$1"; FILT="${2:-bob}"; AT="${3:-30}"
WANT_VER="$(cat "$REPO/arena/engine_version.txt")"
ensure_vm
RUN="bobcensus-$$"
gssh "mkdir -p ~/$RUN" >/dev/null
trap 'gssh "rm -rf ~/'"$RUN"'" >/dev/null 2>&1 || true' EXIT
gscp "$REPO/tools/replaydump/ReplayDump.java" "$USER_NAME@$IP:$RUN/" >/dev/null
gssh "
  export PATH=\$HOME/jdk21/bin:\$PATH
  BC_JAR=\$(find ~/.gradle -name 'battlecode25-java-$WANT_VER.jar' | grep -v source | head -1)
  [ -n \"\$BC_JAR\" ] || { echo '!! no pinned engine jar' >&2; exit 1; }
  cd ~/$RUN
  javac -d . -classpath \"\$BC_JAR\" ReplayDump.java 2>&1 | head -3
  for f in $RDIR/*$FILT*.bc25; do
    b=\$(basename \"\$f\")
    java -classpath \".:\$BC_JAR\" com.google.flatbuffers.ReplayDump \"\$f\" --every $AT 2>/dev/null |
      awk -v F=\"\$b\" '
        /^=== MatchHeader/ { hdr=\$0 }
        /^round .* \\| T1 / { rn=\$2; if (rn % $AT == 0 || rn==$AT) { last[rn]=\$0 } }
        /^=== MatchFooter/ { foot=\$0 }
        END {
          w=\"?\"; ty=\"?\"; rr=\"?\";
          if (match(foot,/winner=team[12]/)) w=substr(foot,RSTART+7,RLENGTH-7);
          if (match(foot,/winType=[A-Z_]+/)) ty=substr(foot,RSTART+8,RLENGTH-8);
          if (match(foot,/rounds=[0-9]+/)) rr=substr(foot,RSTART+7,RLENGTH-7);
          line = last[$AT];
          printf \"%s|%s|%s|%s|%s\\n\", F, w, ty, rr, line;
        }'
  done
"

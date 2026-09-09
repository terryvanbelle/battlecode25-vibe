#!/usr/bin/env bash
# ITERATION 52: reconstruct every tower's LEVEL over its whole life.
#
#   bob-tools/tower-level-census.sh <run-id|abs-dir> <name-filter>
#
# ReplayDump prints `UPGRADE <label> hp->N` UNCONDITIONALLY, and tower max HP by
# level is 1000/1500/2000 (money/paint) and 2000/2500/3000 (defense), so hp->
# names the new level. Tower SPAWN lines need the detailed window, hence
# --from 1 --to 2000; everything except SPAWN/UPGRADE/DIED is dropped ON THE VM
# so only a few hundred lines per game cross the wire.
#
# ISOLATION: IND lines are dropped at the source, unconditionally (RULES.md).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
source "$REPO/tools/lib.sh"
RUN="$1"; FILT="${2:-}"
WANT_VER="$(cat "$REPO/arena/engine_version.txt")"
case "$RUN" in
  /*|~*|\$*) RDIR="$RUN" ;;
  *)         RDIR="\$HOME/battlecode25-vibe/agents/bob/gauntlet/$RUN" ;;
esac
ensure_vm
W="bobtl-$$"
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
    java -classpath \".:\$BC_JAR\" com.google.flatbuffers.ReplayDump \"\$f\" --from 1 --to 2000 --quiet 2>/dev/null |
      grep -v ' IND ' |
      awk -v F=\"\$b\" '
        /^=== GameHeader/ { if (match(\$0,/team1=[^ ]+/)) t1=substr(\$0,RSTART+6,RLENGTH-6);
                            if (match(\$0,/team2=[^ ]+/)) t2=substr(\$0,RSTART+6,RLENGTH-6);
                            printf \"HDR\t%s\t%s\t%s\n\", F, t1, t2; next }
        /^=== MatchFooter/ { printf \"FTR\t%s\t%s\n\", F, \$0; next }
        / SPAWN | UPGRADE | DIED / { printf \"E\t%s\t%s\n\", F, \$0 }'
  done
"

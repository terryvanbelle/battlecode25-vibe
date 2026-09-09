#!/usr/bin/env bash
# Pull only the PAINT / UNPAINT action lines out of TOURNAMENT replays, filtering
# on the VM.
#
#   tools/paint-trace.sh <run> <a> <b> <maplist-file>
#
# Same reasoning as tools/ind-dump.sh: printing the action log needs a
# --from/--to window, and that window prints every action of both teams for every
# round in it. Grepping locally would ship millions of lines so that ~1% survives.
# This greps on the VM and returns only what is needed.
#
# Output, one line per action, prefixed so games can be told apart:
#   <map> <TAB> <aliceSide> <TAB> round <N> id<ID>(T<t>,<TYPE>) PAINT|UNPAINT (x,y)
# plus a `# GAME <map> <side>` header carrying which team is the arm.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$HERE/../../.."
source "$ROOT/tools/lib.sh"

RUN="${1:?usage: paint-trace.sh <run> <a> <b> <maplist>}"
A="${2:?}"; B="${3:?}"; MAPLIST="${4:?}"
[ -f "$MAPLIST" ] || { echo "no such map list: $MAPLIST" >&2; exit 1; }

WANT_VER="$(cat "$ROOT/arena/engine_version.txt")"
[ -n "$WANT_VER" ] || { echo "!! cannot read arena/engine_version.txt" >&2; exit 1; }

ensure_vm
REM="battlecode25-vibe/agents/alice/ptrace-$$-$(date +%s)"
gssh "mkdir -p ~/$REM" >/dev/null
trap 'gssh "rm -rf ~/$REM" >/dev/null 2>&1 || true' EXIT
gscp "$ROOT/tools/replaydump/ReplayDump.java" "$USER_NAME@$IP:$REM/" >/dev/null
gscp "$MAPLIST" "$USER_NAME@$IP:$REM/maps.txt" >/dev/null

cat > /tmp/pt-$$.sh <<REMOTE
#!/usr/bin/env bash
set -uo pipefail
export JAVA_HOME=\$HOME/jdk21 PATH=\$HOME/jdk21/bin:\$PATH
BC_JAR=\$(find ~/.gradle -name 'battlecode25-java-$WANT_VER.jar' | grep -v source | head -1)
[ -n "\$BC_JAR" ] || { echo "!! no jar" >&2; exit 1; }
cd ~/$REM
javac -d . -classpath "\$BC_JAR" ReplayDump.java 2>/dev/null || { echo "!! javac failed" >&2; exit 1; }
TDIR=~/battlecode25-vibe/arena/tournaments/$RUN/replays
while read -r MAP; do
  [ -n "\$MAP" ] || continue
  for ORD in "$A-vs-$B" "$B-vs-$A"; do
    F="\$TDIR/\$ORD-on-\$MAP.bc25"
    [ -f "\$F" ] || continue
    OUT=\$(java -classpath ".:\$BC_JAR" com.google.flatbuffers.ReplayDump "\$F" \
            --quiet --from 1 --to 100000 2>/dev/null)
    HDR=\$(printf '%s\n' "\$OUT" | sed -n 's/^=== GameHeader  team1=\([^ ]*\)  team2=\([^ ]*\).*/\1/p')
    if [ "\$HDR" = "$A" ]; then SIDE=T1; else SIDE=T2; fi
    echo "# GAME \$MAP \$SIDE"
    printf '%s\n' "\$OUT" | grep -E ' (PAINT|UNPAINT) |^round [0-9]* DIED ' || true
  done
done < maps.txt
REMOTE
gscp /tmp/pt-$$.sh "$USER_NAME@$IP:$REM/run.sh" >/dev/null
rm -f /tmp/pt-$$.sh
gssh "bash ~/$REM/run.sh"

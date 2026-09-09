#!/usr/bin/env bash
# Batched round-R census over TOURNAMENT replays, run entirely on battlecode-dev.
#
#   tools/tournament-census.sh <run> <a> <b> <round> <maplist-file>
#
# e.g. tools/tournament-census.sh 20260909-1300 alice carol 300 small19.txt
#
# Prints one TSV row per replay:
#   map  side  <full round-R summary line, both teams>
# with alice's fields resolved to the ARM columns by reading the GameHeader,
# never by assuming the filename order matches team order.
#
# WHY THIS EXISTS, and why it is not a workaround for a tools/ bug:
# tools/replay-dump.sh is correct but pays a full ssh + scp + javac per replay
# (measured 71s wall for one game). A 76-game census would be ~90 minutes of
# almost pure setup cost. This uploads ReplayDump.java ONCE, compiles it ONCE,
# and loops over replays that are ALREADY on the VM, so nothing is copied at all.
# It reuses tools/lib.sh and the same engine-jar pin, so the engine it reads is
# the same one tools/replay-dump.sh reads -- the pin is the part that must not be
# reimplemented, and it is not: WANT_VER comes from arena/engine_version.txt.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$HERE/../../.."
source "$ROOT/tools/lib.sh"

RUN="${1:?usage: tournament-census.sh <run> <a> <b> <round> <maplist> [event-regex]}"
A="${2:?}"; B="${3:?}"; ROUND="${4:?}"; MAPLIST="${5:?}"
# Optional 6th arg: an egrep pattern. Every dump line matching it is emitted as
# an extra row tagged EV, prefixed with the same map/side, so a caller can
# reconstruct per-game state (e.g. tower type mix) from the raw event stream.
EVENTS="${6:-}"
[ -f "$MAPLIST" ] || { echo "no such map list: $MAPLIST" >&2; exit 1; }

WANT_VER="$(cat "$ROOT/arena/engine_version.txt")"
[ -n "$WANT_VER" ] || { echo "!! cannot read arena/engine_version.txt" >&2; exit 1; }

ensure_vm
REM="battlecode25-vibe/agents/alice/census-$$-$(date +%s)"
gssh "mkdir -p ~/$REM" >/dev/null
trap 'gssh "rm -rf ~/$REM" >/dev/null 2>&1 || true' EXIT

gscp "$ROOT/tools/replaydump/ReplayDump.java" "$USER_NAME@$IP:$REM/" >/dev/null
gscp "$MAPLIST" "$USER_NAME@$IP:$REM/maps.txt" >/dev/null

# The loop runs remotely from a scp'd script rather than an inline gssh string:
# an inline heredoc inside a double-quoted ssh argument has already broken one
# tool in this repo with an unexplained 'unexpected end of file'.
cat > /tmp/tc-$$.sh <<REMOTE
#!/usr/bin/env bash
set -uo pipefail
export JAVA_HOME=\$HOME/jdk21 PATH=\$HOME/jdk21/bin:\$PATH
BC_JAR=\$(find ~/.gradle -name 'battlecode25-java-$WANT_VER.jar' | grep -v source | head -1)
if [ -z "\$BC_JAR" ]; then echo "!! no battlecode25-java-$WANT_VER.jar" >&2; exit 1; fi
cd ~/$REM
javac -d . -classpath "\$BC_JAR" ReplayDump.java 2>/dev/null || { echo "!! javac failed" >&2; exit 1; }
TDIR=~/battlecode25-vibe/arena/tournaments/$RUN/replays
while read -r MAP; do
  [ -n "\$MAP" ] || continue
  for ORD in "$A-vs-$B" "$B-vs-$A"; do
    F="\$TDIR/\$ORD-on-\$MAP.bc25"
    [ -f "\$F" ] || continue
    OUT=\$(java -classpath ".:\$BC_JAR" com.google.flatbuffers.ReplayDump "\$F" --every $ROUND 2>/dev/null)
    HDR=\$(printf '%s\n' "\$OUT" | sed -n 's/^=== GameHeader  team1=\([^ ]*\)  team2=\([^ ]*\).*/\1 \2/p')
    T1=\${HDR%% *}
    if [ "\$T1" = "$A" ]; then SIDE=T1; else SIDE=T2; fi
    FOOT=\$(printf '%s\n' "\$OUT" | sed -n 's/^=== MatchFooter //p')
    LINE=\$(printf '%s\n' "\$OUT" | grep "^round $ROUND | " || true)
    # A game that ENDED before round $ROUND is a real result (a fast win or
    # loss), not missing data. It is tagged SHORT and carries its last summary
    # line, so it can never be silently dropped from a mean -- dropping the fast
    # games would bias exactly the quantity this census is about.
    if [ -z "\$LINE" ]; then
      LAST=\$(printf '%s\n' "\$OUT" | grep "^round [0-9]* | " | tail -1)
      printf '%s\t%s\tSHORT\t%s\t%s\n' "\$MAP" "\$SIDE" "\$FOOT" "\$LAST"
    else
      printf '%s\t%s\tOK\t%s\t%s\n' "\$MAP" "\$SIDE" "\$FOOT" "\$LINE"
    fi
    if [ -n '$EVENTS' ]; then
      printf '%s\n' "\$OUT" | grep -E '$EVENTS' | while read -r EL; do
        printf '%s\t%s\tEV\t%s\n' "\$MAP" "\$SIDE" "\$EL"
      done
    fi
  done
done < maps.txt
REMOTE
gscp /tmp/tc-$$.sh "$USER_NAME@$IP:$REM/run.sh" >/dev/null
rm -f /tmp/tc-$$.sh
gssh "bash ~/$REM/run.sh"

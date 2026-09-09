#!/usr/bin/env bash
# Pull ONLY this bot's indicator strings out of a local replay, filtering on the VM.
#
#   tools/ind-dump.sh <pkg> <replay.bc25> [<replay.bc25> ...]
#
# WHY NOT tools/replay-dump.sh: to print indicator strings ReplayDump needs an
# action-log window (`--from/--to`), and that window also prints every paint,
# move and attack of BOTH teams for every round in it. On a 2000-round game that
# is millions of lines shipped over ssh so that a local `grep ' IND '` can throw
# ~99.9% of them away. This runs the identical dump with the identical engine pin
# and greps on the VM, so only the IND lines cross the wire.
#
# It is NOT a fork of the dumper: it uploads and runs tools/replaydump/ReplayDump.java
# unchanged, and takes WANT_VER from arena/engine_version.txt exactly as
# replay-dump.sh does. Only the location of the grep differs.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$HERE/../../.."
source "$ROOT/tools/lib.sh"

PKG="${1:?usage: ind-dump.sh <pkg> <replay.bc25> ...}"; shift
# DUMP_GREP overrides what is pulled back. Default is this bot's indicator
# strings, which NEED the action-log window. UPGRADE / tower-SPAWN / DIED lines
# print unconditionally, so DUMP_WINDOW=0 skips the window and the dump is far
# cheaper -- no action log is generated at all.
GREP_PAT="${DUMP_GREP:- IND }"
WINDOW="${DUMP_WINDOW:-1}"
# DUMP_EVERY: when set, keep the per-round aggregate lines (drop --quiet) at that
# stride. Needed for twPaint/cov comparisons, which live on the summary line.
EVERY="${DUMP_EVERY:-}"
[ "$#" -ge 1 ] || { echo "no replays given" >&2; exit 1; }

WANT_VER="$(cat "$ROOT/arena/engine_version.txt")"
[ -n "$WANT_VER" ] || { echo "!! cannot read arena/engine_version.txt" >&2; exit 1; }

ensure_vm
REM="battlecode25-vibe/agents/alice/inddump-$$-$(date +%s)"
gssh "mkdir -p ~/$REM" >/dev/null
trap 'gssh "rm -rf ~/$REM" >/dev/null 2>&1 || true' EXIT
gscp "$ROOT/tools/replaydump/ReplayDump.java" "$USER_NAME@$IP:$REM/" >/dev/null

i=0
for f in "$@"; do
  i=$((i+1))
  gscp "$f" "$USER_NAME@$IP:$REM/in$i.bc25" >/dev/null
done

gssh "
  export JAVA_HOME=\$HOME/jdk21 PATH=\$HOME/jdk21/bin:\$PATH
  BC_JAR=\$(find ~/.gradle -name 'battlecode25-java-$WANT_VER.jar' | grep -v source | head -1)
  if [ -z \"\$BC_JAR\" ]; then echo '!! no battlecode25-java-$WANT_VER.jar' >&2; exit 1; fi
  cd ~/$REM
  javac -d . -classpath \"\$BC_JAR\" ReplayDump.java 2>/dev/null || { echo '!! javac failed' >&2; exit 1; }
  for k in \$(seq 1 $i); do
    echo \"=== FILE \$k\"
    if [ "$WINDOW" = "1" ]; then
      java -classpath \".:\$BC_JAR\" com.google.flatbuffers.ReplayDump in\$k.bc25 \
           --quiet --from 1 --to 100000 --ind $PKG 2>/dev/null | grep '$GREP_PAT' || true
    else
      if [ -n "$EVERY" ]; then
        java -classpath \".:\$BC_JAR\" com.google.flatbuffers.ReplayDump in\$k.bc25 \
             --every $EVERY 2>/dev/null | grep -E '$GREP_PAT|GameHeader' || true
      else
        java -classpath \".:\$BC_JAR\" com.google.flatbuffers.ReplayDump in\$k.bc25 \
             --quiet 2>/dev/null | grep -E '$GREP_PAT|GameHeader' || true
      fi
    fi
  done
"

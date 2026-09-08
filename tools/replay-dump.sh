#!/usr/bin/env bash
# Shared BC25 replay-to-text tool. Compiles and runs tools/replaydump/ReplayDump.java
# on battlecode-dev against the engine jar's own schema classes.
#
#   tools/replay-dump.sh <replay.bc25> [flags]
#
# Flags (passed through):
#   --from R --to R   detailed action log window
#   --robot ID        per-turn track of one robot
#   --every N         aggregate sampling stride (default 25)
#   --map N           ASCII arena every N rounds
#   --map-at R        ASCII arena once at round R (repeatable)
#   --views           also print separate paint and mark grids
#   --quiet           suppress per-round aggregates
#
# Examples:
#   tools/replay-dump.sh r.bc25 --quiet --map-at 400 --views
#   tools/replay-dump.sh r.bc25 --from 90 --to 110 --robot 12345
#
# Each invocation gets a unique remote dir, so parallel dumps cannot clobber
# each other. The dir is removed on exit.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib.sh"

[ "$#" -ge 1 ] || { echo "usage: $0 <replay.bc25> [flags]" >&2; exit 1; }
REPLAY="$1"; shift
[ -f "$REPLAY" ] || { echo "no such file: $REPLAY" >&2; exit 1; }

# BC25_ENGINE_VERSION overrides the pin for TESTING ONLY -- see engine-jar.sh.
# Never test a failure path by editing arena/engine_version.txt: it is tracked,
# and three agents read it live from this same working tree.
WANT_VER="${BC25_ENGINE_VERSION:-$(cat "$HERE/../arena/engine_version.txt" 2>/dev/null)}"
[ -n "$WANT_VER" ] || { echo "!! cannot read arena/engine_version.txt" >&2; exit 1; }

ensure_vm
RUN_DIR="replaydump/run-$$-$(date +%s%N)"
gssh "mkdir -p ~/$RUN_DIR" >/dev/null
trap 'gssh "rm -rf ~/$RUN_DIR" >/dev/null 2>&1 || true' EXIT
gscp "$HERE/replaydump/ReplayDump.java" "$USER_NAME@$IP:$RUN_DIR/" >/dev/null
gscp "$REPLAY" "$USER_NAME@$IP:$RUN_DIR/in.bc25" >/dev/null

gssh "
  export JAVA_HOME=\$HOME/jdk21 PATH=\$HOME/jdk21/bin:\$PATH
  # Pinned to arena/engine_version.txt, NOT 'highest version wins'. The gradle
  # cache holds a stale battlecode25-java-1.0.0.jar beside the real one, so
  # sorting by version and taking the last gives the right answer only while the
  # newest jar present happens to be the wanted one -- right by luck of a flag,
  # not by a check. This tool produces the census and arena data all three
  # lineages reason from, so a silently wrong engine here contaminates their
  # verdicts, not merely its own output.
  # NOTE every inner quote below must stay escaped: this whole block is inside a
  # double-quoted gssh argument, and a bare quote ends it (that broke the tool
  # once, with 'syntax error: unexpected end of file' and no other clue).
  BC_JAR=\$(find ~/.gradle -name 'battlecode25-java-$WANT_VER.jar' | grep -v source | head -1)
  if [ -z \"\$BC_JAR\" ]; then echo \"!! no battlecode25-java-$WANT_VER.jar on the VM\" >&2; exit 1; fi
  cd ~/$RUN_DIR
  javac -d . -classpath \"\$BC_JAR\" ReplayDump.java
  java -classpath \".:\$BC_JAR\" com.google.flatbuffers.ReplayDump in.bc25 $*
"

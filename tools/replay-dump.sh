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

ensure_vm
RUN_DIR="replaydump/run-$$-$(date +%s%N)"
gssh "mkdir -p ~/$RUN_DIR" >/dev/null
trap 'gssh "rm -rf ~/$RUN_DIR" >/dev/null 2>&1 || true' EXIT
gscp "$HERE/replaydump/ReplayDump.java" "$USER_NAME@$IP:$RUN_DIR/" >/dev/null
gscp "$REPLAY" "$USER_NAME@$IP:$RUN_DIR/in.bc25" >/dev/null

gssh "
  export JAVA_HOME=\$HOME/jdk21 PATH=\$HOME/jdk21/bin:\$PATH
  BC_JAR=\$(find ~/.gradle -name 'battlecode25-java-*.jar' | grep -v source | sort -V | tail -1)
  cd ~/$RUN_DIR
  javac -d . -classpath \"\$BC_JAR\" ReplayDump.java
  java -classpath \".:\$BC_JAR\" com.google.flatbuffers.ReplayDump in.bc25 $*
"

#!/usr/bin/env bash
# Alice's BC25 replay-to-text tool. Compiles/runs ReplayDump.java on
# battlecode-dev against the engine jar's vendored schema classes.
#
#   tools/replay-dump.sh replays/some.bc25 [--from R --to R] [--robot ID] [--every N]
#
# Unique remote dir per run (parallel dumps must not clobber each other).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/../../../tools/lib.sh"

[ "$#" -ge 1 ] || { echo "usage: $0 <replay.bc25> [flags]" >&2; exit 1; }
REPLAY="$1"; shift
[ -f "$REPLAY" ] || { echo "no such file: $REPLAY" >&2; exit 1; }

ensure_vm
RUN_DIR="alice-replaydump/run-$$-$(date +%s%N)"
gssh "mkdir -p ~/$RUN_DIR" >/dev/null
trap 'gssh "rm -rf ~/$RUN_DIR" >/dev/null 2>&1 || true' EXIT
gscp "$HERE/replaydump/ReplayDump.java" "$USER_NAME@$IP:$RUN_DIR/" >/dev/null
gscp "$REPLAY" "$USER_NAME@$IP:$RUN_DIR/in.bc25" >/dev/null

gssh "
  export JAVA_HOME=\$HOME/jdk21 PATH=\$HOME/jdk21/bin:\$PATH
  BC_JAR=\$(find ~/.gradle -name 'battlecode25-java-3*.jar' | sort -V | tail -1)
  cd ~/$RUN_DIR
  javac -d . -classpath \"\$BC_JAR\" ReplayDump.java
  java -classpath \".:\$BC_JAR\" com.google.flatbuffers.ReplayDump in.bc25 $*
"

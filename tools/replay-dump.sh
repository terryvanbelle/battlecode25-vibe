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
# Replays already ON the VM are dumped in place, with no copying at all:
#
#   tools/replay-dump.sh --vm 'arena/tournaments/<run>/replays/*.bc25' --quiet ...
#
# --vm takes a path or a glob relative to the VM home, is repeatable, and can be
# mixed with local files. With more than one replay, each dump is preceded by
# `=== FILE <name>`.
#
# The compiled dumper is CACHED on the VM, keyed by the hash of ReplayDump.java
# and the pinned engine version, so an unchanged tool compiles once and every
# later call reuses it.
#
# Both of those come from a lineage that measured the cost and prototyped the
# fix rather than only reporting it: a full ssh + scp + javac per replay is 71s
# of wall time per game, which made a 76-replay census ~90 minutes of almost
# pure setup. Its prototype uploaded and compiled once and looped over replays
# already on the VM; that is what is upstreamed here, so all three lineages get
# it and nobody has to reimplement the engine pin to do so.
#
# Each invocation still gets a unique remote dir for anything it uploads, so
# parallel dumps cannot clobber each other. The dir is removed on exit.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib.sh"

[ "$#" -ge 1 ] || { echo "usage: $0 <replay.bc25 | --vm <path|glob>>... [flags]" >&2; exit 1; }
LOCAL=(); VMPATHS=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --vm) [ "$#" -ge 2 ] || { echo "--vm needs a path" >&2; exit 1; }
          VMPATHS+=("$2"); shift 2 ;;
    -*)   break ;;                      # first javap-style flag: the rest are dump flags
    *)    [ -f "$1" ] || { echo "no such file: $1" >&2; exit 1; }
          LOCAL+=("$1"); shift ;;
  esac
done
[ "${#LOCAL[@]}" -gt 0 ] || [ "${#VMPATHS[@]}" -gt 0 ] || { echo "no replay given" >&2; exit 1; }

# BC25_ENGINE_VERSION overrides the pin for TESTING ONLY -- see engine-jar.sh.
# Never test a failure path by editing arena/engine_version.txt: it is tracked,
# and three agents read it live from this same working tree.
WANT_VER="${BC25_ENGINE_VERSION:-$(cat "$HERE/../arena/engine_version.txt" 2>/dev/null)}"
[ -n "$WANT_VER" ] || { echo "!! cannot read arena/engine_version.txt" >&2; exit 1; }

ensure_vm
RUN_DIR="replaydump/run-$$-$(date +%s%N)"
gssh "mkdir -p ~/$RUN_DIR" >/dev/null
trap 'gssh "rm -rf ~/$RUN_DIR" >/dev/null 2>&1 || true' EXIT

# The cache key is the tool's own hash plus the pinned engine version, so an
# edit to ReplayDump.java or a version bump misses the cache and recompiles,
# while an unchanged tool never compiles twice. Stale classes are the one
# failure this must not have -- a fixed dumper that keeps printing the old
# output would be worse than the 71s it saves.
SHA="$(sha1sum "$HERE/replaydump/ReplayDump.java" | cut -c1-12)"
CACHE="replaydump/cache-$WANT_VER-$SHA"
if ! gssh "test -f ~/$CACHE/com/google/flatbuffers/ReplayDump.class" 2>/dev/null; then
  gssh "mkdir -p ~/$CACHE" >/dev/null
  gscp "$HERE/replaydump/ReplayDump.java" "$USER_NAME@$IP:$CACHE/" >/dev/null
  NEED_COMPILE=1
else
  NEED_COMPILE=0
fi

# Only local files are uploaded; --vm paths are read where they already are.
i=0
for f in ${LOCAL[@]+"${LOCAL[@]}"}; do
  gscp "$f" "$USER_NAME@$IP:$RUN_DIR/in$i.bc25" >/dev/null
  i=$((i+1))
done
INPUTS=""
i=0
for f in ${LOCAL[@]+"${LOCAL[@]}"}; do INPUTS="$INPUTS ~/$RUN_DIR/in$i.bc25"; i=$((i+1)); done
for p in ${VMPATHS[@]+"${VMPATHS[@]}"}; do INPUTS="$INPUTS ~/$p"; done

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
  if [ $NEED_COMPILE = 1 ]; then
    cd ~/$CACHE && javac -d . -classpath \"\$BC_JAR\" ReplayDump.java || exit 1
  fi
  n=0; for f in $INPUTS; do n=\$((n+1)); done
  for f in $INPUTS; do
    if [ \$n -gt 1 ]; then echo \"=== FILE \$(basename \$f)\"; fi
    java -classpath \"\$HOME/$CACHE:\$BC_JAR\" com.google.flatbuffers.ReplayDump \"\$f\" $*
  done
"

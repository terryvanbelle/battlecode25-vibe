#!/usr/bin/env bash
# Disassemble an engine class from the PINNED battlecode25 jar, wherever a jar
# and a JDK actually exist.
#
#   tools/engine-javap.sh battlecode.common.UnitType
#   tools/engine-javap.sh -c battlecode.world.GameWorld
#   tools/engine-javap.sh -c -p battlecode.world.RobotControllerImpl | grep -A20 attack
#
# Flags before the class name are passed to javap; with none, -p is used.
#
# WHY THIS EXISTS. `tools/engine-jar.sh` resolves the right jar and refuses the
# wrong one, which is the part that matters -- battlecode-dev's gradle cache
# holds a stale 1.0.0 beside the real 3.1.0, and decompiling the wrong one
# yields confident, false engine facts. But resolving a path is not running a
# command, and the documented usage
#
#     javap -p -c -cp "$(tools/engine-jar.sh)" <class>
#
# could not work on the driver at all: there is no local jar AND no local JDK
# there. The --remote form returns a path that is only meaningful on the VM,
# where `javap` is not on PATH in a non-interactive ssh (it lives in ~/jdk21).
# A lineage paid two failed calls to discover the working incantation and then
# reported it rather than keeping the workaround to itself. This is the fix:
# one command that resolves the pinned jar, puts the JDK on PATH, and runs.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib.sh"

[ "$#" -ge 1 ] || { echo "usage: $0 [javap flags] <fully.qualified.Class>" >&2; exit 1; }
CLASS="${@: -1}"
FLAGS=("${@:1:$#-1}")
[ "${#FLAGS[@]}" -gt 0 ] || FLAGS=(-p)

# Local first when it can actually work -- no VM round trip, no shared load.
LOCAL_JAR="$("$HERE/engine-jar.sh" 2>/dev/null || true)"
if [ -n "$LOCAL_JAR" ] && [ -f "$LOCAL_JAR" ] && command -v javap >/dev/null 2>&1; then
  exec javap "${FLAGS[@]}" -cp "$LOCAL_JAR" "$CLASS"
fi

JAR="$("$HERE/engine-jar.sh" --remote)"
[ -n "$JAR" ] || { echo "!! could not resolve the pinned engine jar on $VM" >&2; exit 1; }
ensure_vm
gssh "export JAVA_HOME=\$HOME/jdk21 PATH=\$HOME/jdk21/bin:\$PATH
      javap $(printf '%q ' "${FLAGS[@]}") -cp '$JAR' '$CLASS'"

#!/usr/bin/env bash
# Print the path of the CORRECT engine jar, or fail loudly.
#
#   javap -p -c -cp "$(tools/engine-jar.sh)" battlecode.common.RobotController
#   tools/engine-jar.sh --remote     # the jar as resolved on battlecode-dev
#
# WHY THIS EXISTS. battlecode-dev's gradle cache holds BOTH
# battlecode25-java-1.0.0.jar and battlecode25-java-3.1.0.jar, so a probe that
# locates the engine with `find ... -name 'battlecode25*.jar' | head -1` can
# decompile the wrong engine and derive confident, false facts about the game.
# A lineage did exactly that, and caught it only because a method it expected
# was missing outright -- a subtler difference between versions would have
# passed silently into tools/engine-facts.md, which every lineage trusts.
#
# So this resolves the version from engine_version.txt rather than from whatever
# the filesystem happens to offer first, and REFUSES to print a path whose
# version does not match. A wrong jar becomes an error instead of a wrong fact.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"

WANT="$(cat "$REPO/arena/engine_version.txt" 2>/dev/null || true)"
[ -n "$WANT" ] || { echo "!! cannot read arena/engine_version.txt" >&2; exit 1; }

find_jar () {   # $1 = search root; empty output if absent, never fatal
    # `|| true` and the -d guard are load-bearing under `set -euo pipefail`:
    # a missing search root makes find exit non-zero, pipefail propagates it,
    # and set -e then kills this script BEFORE it can print its own error. The
    # first version did exactly that -- no path, no message, exit 1 -- which is
    # the silent failure this tool exists to prevent, committed inside the tool
    # itself.
    [ -d "$1" ] || return 0
    find "$1" -name "battlecode25-java-${WANT}.jar" 2>/dev/null | head -1 || true
}

if [ "${1:-}" = --remote ]; then
    source "$HERE/lib.sh"
    ensure_vm
    path="$(gssh "find ~/.gradle ~/battlecode25-vibe -name 'battlecode25-java-${WANT}.jar' 2>/dev/null | head -1")"
    [ -n "$path" ] || { echo "!! no battlecode25-java-${WANT}.jar on $VM" >&2; exit 1; }
    echo "$path"
    exit 0
fi

jar="$(find_jar "$HOME/.gradle")"
[ -n "$jar" ] || jar="$(find_jar "$REPO")"
[ -n "$jar" ] || jar="$(find_jar "${TMPDIR:-/tmp}")"

if [ -z "$jar" ]; then
    echo "!! no battlecode25-java-${WANT}.jar found locally." >&2
    echo "   Do NOT fall back to whatever jar you can find: the cache holds" >&2
    echo "   older versions, and decompiling one yields false engine facts." >&2
    echo "   Use --remote, or fetch ${WANT} first." >&2
    exit 1
fi
echo "$jar"

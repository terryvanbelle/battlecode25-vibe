#!/usr/bin/env bash
# Like tools/vm-match.sh but with robot stdout enabled (for tracing probe builds
# that print counters with System.out.println; the shared runner hardcodes
# -PoutputVerbose=false, which drops them).
#
# Usage (from agents/bob): TEAM_A=bob TEAM_B=bob_iter0 bob-tools/vm-verbose-match.sh MapName
#
# FIXED 2026-09-08. This script previously did two unsafe things that the shared
# tools/vm-match.sh documents and avoids. Both were found by reading that script
# while a 160-game gauntlet of mine was in flight:
#
#  1. It built and ran inside $WS_REL -- the SAME directory the gauntlets use.
#     `./gradlew run` rewrites build/classes, and in-flight gauntlet games load
#     their robot classes from exactly that path, so a trace run started during a
#     gauntlet can swap the code out from under games already in progress and
#     silently corrupt their results. Now uses a sibling dir, as vm-match.sh does.
#  2. It took no slot from the shared semaphore. battlecode-dev also serves a live
#     BC26 project and two sibling lineages, and every other runner's HARD_CAP
#     check counts running games -- a runner that does not TAKE a slot makes the
#     cap a fiction. Now acquires one, released when the remote shell exits.
#
# CAVEAT for anything traced before this date: the verbose logs in logs/ dated
# 2026-09-07 were produced by the unsafe version. They are fine as traces of
# THEIR OWN games, but if one of them overlapped a gauntlet, that gauntlet's
# results are suspect rather than these logs.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../../../tools/lib.sh"

TEAM_A="${TEAM_A:-bob}"
TEAM_B="${TEAM_B:-examplefuncsplayer}"
[ "$#" -ge 1 ] || { echo "need at least one map name"; exit 1; }

find_workspace
mkdir -p "$WS_DIR/matches" "$WS_DIR/logs"
ensure_vm

# Build and play in a SIBLING directory, never the workspace the gauntlets use.
MATCH_REL="$WS_REL-vmatch"
gssh "
  cd ~/$REMOTE_REPO
  mkdir -p '$MATCH_REL/src'
  for f in build.gradle gradle gradlew gradlew.bat gradle.properties engine_version.txt client_version.txt; do
    [ -e '$MATCH_REL'/\$f ] || cp -r '$WS_REL'/\$f '$MATCH_REL'/ 2>/dev/null || true
  done
" >/dev/null
gscp -r "$WS_DIR/src/." "$USER_NAME@$IP:$REMOTE_REPO/$MATCH_REL/src/" >/dev/null

for MAP in "$@"; do
  echo "=== verbose match: $TEAM_A vs $TEAM_B on $MAP ==="
  gssh "
    export JAVA_HOME=\$HOME/jdk21 PATH=\$HOME/jdk21/bin:\$PATH
    cd ~/$REMOTE_REPO/$MATCH_REL
    GLOBAL_CAP=${GLOBAL_CAP:-5} HARD_CAP=${HARD_CAP:-7}
$(cat "$REPO_ROOT/tools/remote-slot.sh")
    acquire_slot
    ./gradlew --no-daemon run -PteamA=$TEAM_A -PteamB=$TEAM_B -Pmaps=$MAP \
      -PoutputVerbose=true > \$HOME/bob-verbose-$MAP.log 2>&1
    grep -E '\[server\]' \$HOME/bob-verbose-$MAP.log | tail -5
  "
  gscp "$USER_NAME@$IP:$REMOTE_REPO/$MATCH_REL/matches/$TEAM_A-vs-$TEAM_B-on-$MAP.bc25" "$WS_DIR/matches/" >/dev/null || echo "  (no replay pulled)"
  gscp "$USER_NAME@$IP:bob-verbose-$MAP.log" "$WS_DIR/logs/" >/dev/null || true
done
echo "logs in $WS_DIR/logs/bob-verbose-<map>.log"

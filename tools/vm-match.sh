#!/usr/bin/env bash
# Run one or more BC25 matches on battlecode-dev from inside a workspace.
#
#   cd agents/alice
#   ../../tools/vm-match.sh DefaultSmall                       # examplefuncsplayer vs itself
#   TEAM_A=alice TEAM_B=examplefuncsplayer ../../tools/vm-match.sh DefaultSmall
#
# Pulls the replay (.bc25) and log back into the workspace's matches/ and logs/.
# NOTE: battlecode-dev is SHARED with a live BC26 project -- this script never
# kills processes or stops the VM.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

TEAM_A="${TEAM_A:-examplefuncsplayer}"
TEAM_B="${TEAM_B:-examplefuncsplayer}"
[ "$#" -ge 1 ] || { echo "need at least one map name"; exit 1; }

find_workspace
mkdir -p "$WS_DIR/matches" "$WS_DIR/logs"
ensure_vm

gssh "mkdir -p ~/$REMOTE_REPO/$WS_REL/src" >/dev/null
gscp -r "$WS_DIR/src/." "$USER_NAME@$IP:$REMOTE_REPO/$WS_REL/src/" >/dev/null

for MAP in "$@"; do
  echo "=== match: $TEAM_A vs $TEAM_B on $MAP ($WS_REL) ==="
  # A single debug match is still a game on a shared box: it is counted by every
  # other runner's HARD_CAP check, so if it does not TAKE a slot the cap is a
  # fiction and three agents tracing replays can push the machine over. Same
  # semaphore as gauntlet.sh and tournament.sh; the slot is released when this
  # shell exits.
  gssh "
    export JAVA_HOME=\$HOME/jdk21 PATH=\$HOME/jdk21/bin:\$PATH
    cd ~/$REMOTE_REPO/$WS_REL
    GLOBAL_CAP=${GLOBAL_CAP:-5} HARD_CAP=${HARD_CAP:-7}
$(cat "$REPO_ROOT/tools/remote-slot.sh")
    acquire_slot
    ./gradlew --no-daemon run -PteamA=$TEAM_A -PteamB=$TEAM_B -Pmaps=$MAP \
      -PoutputVerbose=false 2>&1 | tee \$HOME/bc25-match-$MAP.log | grep -E '\[server\]' || true
  "
  gscp "$USER_NAME@$IP:$REMOTE_REPO/$WS_REL/matches/$TEAM_A-vs-$TEAM_B-on-$MAP.bc25" "$WS_DIR/matches/" >/dev/null || echo "  (no replay pulled)"
  gscp "$USER_NAME@$IP:bc25-match-$MAP.log" "$WS_DIR/logs/" >/dev/null || true
done
echo "artifacts in $WS_DIR/matches and $WS_DIR/logs"

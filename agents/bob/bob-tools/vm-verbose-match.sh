#!/usr/bin/env bash
# Like tools/vm-match.sh but with robot stdout enabled (for tracing).
# Usage (from agents/bob): TEAM_A=bob TEAM_B=bob_iter0 bob-tools/vm-verbose-match.sh MapName
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../../../tools/lib.sh"

TEAM_A="${TEAM_A:-bob}"
TEAM_B="${TEAM_B:-examplefuncsplayer}"
[ "$#" -ge 1 ] || { echo "need at least one map name"; exit 1; }

find_workspace
mkdir -p "$WS_DIR/matches" "$WS_DIR/logs"
ensure_vm

gssh "mkdir -p ~/$REMOTE_REPO/$WS_REL/src" >/dev/null
gscp -r "$WS_DIR/src/." "$USER_NAME@$IP:$REMOTE_REPO/$WS_REL/src/" >/dev/null

for MAP in "$@"; do
  echo "=== verbose match: $TEAM_A vs $TEAM_B on $MAP ==="
  gssh "
    export JAVA_HOME=\$HOME/jdk21 PATH=\$HOME/jdk21/bin:\$PATH
    cd ~/$REMOTE_REPO/$WS_REL
    ./gradlew --no-daemon run -PteamA=$TEAM_A -PteamB=$TEAM_B -Pmaps=$MAP \
      -PoutputVerbose=true > \$HOME/bob-verbose-$MAP.log 2>&1
    grep -E '\[server\]' \$HOME/bob-verbose-$MAP.log | tail -5
  "
  gscp "$USER_NAME@$IP:$REMOTE_REPO/$WS_REL/matches/$TEAM_A-vs-$TEAM_B-on-$MAP.bc25" "$WS_DIR/matches/" >/dev/null || echo "  (no replay pulled)"
  gscp "$USER_NAME@$IP:bob-verbose-$MAP.log" "$WS_DIR/logs/" >/dev/null || true
done
echo "logs in $WS_DIR/logs/bob-verbose-<map>.log"

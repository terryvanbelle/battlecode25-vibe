#!/usr/bin/env bash
# Round-robin tournament between the agents' current bots (alice, bob, carol),
# every pair x every map x both sides, run headlessly on battlecode-dev.
#
#   tools/tournament.sh                 # all maps in tools/bc25-maps.txt
#   MAPS="DefaultSmall" tools/tournament.sh
#
# Each bot is exported from the repo's HEAD (the agent's last commit), never
# from the working tree, so a mid-experiment broken tree can't poison the
# tournament. Each bot is compiled in isolation first; one that fails to build
# forfeits all its games (recorded as such) instead of blocking the others.
#
# Output: tournaments/<run-id>/ (results.csv, reasons.txt, summary.txt) --
# committed to git by cron-tournament.sh. Replays stay on battlecode-dev under
# ~/battlecode25-vibe/arena/tournaments/<run-id>/ (driver disk is tight).
#
# SHARED VM: battlecode-dev also serves a live BC26 project. Never kill
# processes, never stop the VM; the runner yields at GLOBAL_CAP like gauntlet.sh.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

BOTS="${BOTS:-alice bob carol}"
MAXJOBS="${MAXJOBS:-4}"
GLOBAL_CAP="${GLOBAL_CAP:-6}"
if [ -z "${MAPS:-}" ]; then
  if [ -f "$REPO_ROOT/tools/bc25-maps.txt" ]; then MAPS="$(tr '\n' ' ' < "$REPO_ROOT/tools/bc25-maps.txt")"
  else MAPS="DefaultSmall"; fi
fi

exec 9>/tmp/bc25-tournament.lock
flock -n 9 || { echo "another tournament is already running; exiting"; exit 0; }

RUN_ID="$(date -u +%Y%m%d-%H%M)"
OUT="$REPO_ROOT/tournaments/$RUN_ID"
mkdir -p "$OUT"

# ---- stage: export each bot's last committed source into a clean src tree ----
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
cp -r "$REPO_ROOT/arena/src/examplefuncsplayer" "$STAGE/" 2>/dev/null || true
for B in $BOTS; do
  if git -C "$REPO_ROOT" cat-file -e "HEAD:agents/$B/src/$B/RobotPlayer.java" 2>/dev/null; then
    mkdir -p "$STAGE/$B"
    git -C "$REPO_ROOT" archive HEAD "agents/$B/src/$B" | tar -x -C "$STAGE" --strip-components=3
  else
    echo "!! $B has no committed bot at agents/$B/src/$B -- it forfeits" | tee -a "$OUT/summary.txt"
  fi
done

# pairs
PAIRS=""
set -- $BOTS
while [ "$#" -gt 1 ]; do
  first=$1; shift
  for other in "$@"; do PAIRS="$PAIRS $first:$other"; done
done

NMAPS=$(echo "$MAPS" | wc -w)
echo "tournament $RUN_ID  bots=[$BOTS]  maps=$NMAPS  pairs=[$PAIRS]"

ensure_vm
gssh "mkdir -p ~/$REMOTE_REPO/arena/src ~/$REMOTE_REPO/arena/tournaments" >/dev/null
gscp -r "$STAGE/." "$USER_NAME@$IP:$REMOTE_REPO/arena/stage-$RUN_ID/" >/dev/null

RTAG="tournament-$RUN_ID"
remote=$(mktemp)
cat > "$remote" <<REMOTE
set -uo pipefail
export JAVA_HOME=\$HOME/jdk21 PATH=\$HOME/jdk21/bin:\$PATH
cd ~/$REMOTE_REPO/arena
RUNDIR=tournaments/$RUN_ID
mkdir -p "\$RUNDIR/replays"; : > "\$RUNDIR/results.txt"

# -- isolated compile check per bot: broken bots forfeit, others still play --
OK_BOTS=""
for B in $BOTS; do
  rm -rf src; mkdir -p src
  cp -r stage-$RUN_ID/examplefuncsplayer src/ 2>/dev/null || true
  [ -d stage-$RUN_ID/\$B ] || { echo "FORFEIT \$B missing" >> "\$RUNDIR/results.txt"; continue; }
  cp -r stage-$RUN_ID/\$B src/
  if ./gradlew --no-daemon -q build >/dev/null 2>&1; then OK_BOTS="\$OK_BOTS \$B"
  else echo "FORFEIT \$B build-failed" >> "\$RUNDIR/results.txt"; fi
done

# -- combined build of all surviving bots --
rm -rf src; mkdir -p src
cp -r stage-$RUN_ID/examplefuncsplayer src/ 2>/dev/null || true
for B in \$OK_BOTS; do cp -r stage-$RUN_ID/\$B src/; done
./gradlew --no-daemon -q build >/dev/null 2>&1 || { echo "BUILD-FAILED" >> "\$RUNDIR/results.txt"; echo TOURNAMENT-COMPLETE >> "\$RUNDIR/results.txt"; exit 1; }
CP=\$(./gradlew --no-daemon -q printClasspath | tail -1)

yield_load () {
  while [ "\$(pgrep -fc battlecode.server.Main || true)" -ge $GLOBAL_CAP ]; do sleep 10; done
}

game () {  # <botA> <botB> <map>   (botA plays side A)
  local TA=\$1 TB=\$2 MAP=\$3 LOG W R RE
  local REPLAY="\$RUNDIR/replays/\${TA}-vs-\${TB}-on-\${MAP}.bc25"
  LOG=\$(java -Xmx2g \\
    --add-opens=java.base/jdk.internal.misc=ALL-UNNAMED \\
    --add-opens=java.base/jdk.internal.math=ALL-UNNAMED \\
    --add-opens=java.base/jdk.internal.util=ALL-UNNAMED \\
    --add-opens=java.base/jdk.internal.access=ALL-UNNAMED \\
    --add-opens=java.base/sun.security.action=ALL-UNNAMED \\
    -Dbc.server.wait-for-client=false -Dbc.server.mode=headless -Dbc.server.map-path=maps \\
    -Dbc.server.robot-player-to-system-out=false -Dbc.server.debug=false \\
    -Dbc.engine.debug-methods=false -Dbc.engine.enable-profiler=false -Dbc.engine.show-indicators=true \\
    -Dbc.game.team-a="\$TA" -Dbc.game.team-b="\$TB" \\
    -Dbc.game.team-a.url=build/classes -Dbc.game.team-b.url=build/classes \\
    -Dbc.game.team-a.package="\$TA" -Dbc.game.team-b.package="\$TB" \\
    -Dbc.game.maps="\$MAP" -Dbc.server.validate-maps=true -Dbc.server.alternate-order=false \\
    -Dbc.server.save-file="\$REPLAY" \\
    -cp "\$CP" battlecode.server.Main -c=- 2>&1 || true)
  W=\$(printf '%s\n' "\$LOG"  | sed -n 's/.*(\([AB]\)) wins.*/\1/p' | tail -1)
  R=\$(printf '%s\n' "\$LOG"  | sed -n 's/.*wins (round \([0-9]*\)).*/\1/p' | tail -1)
  RE=\$(printf '%s\n' "\$LOG" | sed -n 's/.*Reason: //p' | tail -1)
  {
    printf 'RESULT %s %s %s %s %s\n' "\$TA" "\$TB" "\$MAP" "\${W:-?}" "\${R:-?}"
    printf 'REASON %s %s %s %s\n'    "\$TA" "\$TB" "\$MAP" "\${RE:-?}"
  } >> "\$RUNDIR/results.txt"
}

for PAIR in $PAIRS; do
  X=\${PAIR%%:*}; Y=\${PAIR##*:}
  case " \$OK_BOTS " in *" \$X "*) ;; *) continue;; esac
  case " \$OK_BOTS " in *" \$Y "*) ;; *) continue;; esac
  for MAP in $MAPS; do
    for ORDER in "\$X \$Y" "\$Y \$X"; do
      while [ "\$(jobs -rp | wc -l)" -ge $MAXJOBS ]; do wait -n; done
      yield_load
      game \$ORDER "\$MAP" &
    done
  done
done
wait
rm -rf stage-$RUN_ID
echo TOURNAMENT-COMPLETE >> "\$RUNDIR/results.txt"
REMOTE
gscp "$remote" "$USER_NAME@$IP:$RTAG.sh" >/dev/null
gssh "setsid bash -c 'bash ~/$RTAG.sh > ~/$RTAG.log 2>&1' </dev/null >/dev/null 2>&1 &" >/dev/null || true
rm -f "$remote"

RES="$REMOTE_REPO/arena/tournaments/$RUN_ID/results.txt"
echo "  polling every 60s ..."
deadline=$(( $(date +%s) + 240*60 ))
while true; do
  sleep 60
  snap=$(gssh "cat $RES 2>/dev/null; echo '@@@'; pgrep -f '$RTAG.sh' >/dev/null && echo ALIVE") || { echo "  (ssh retry)"; continue; }
  body=${snap%@@@*}; ctl=${snap#*@@@}
  printf '%s\n' "$body" > "$OUT/results.txt"
  n=$(printf '%s\n' "$body" | grep -c '^RESULT ' || true)
  echo "  $n games done"
  grep -q '^TOURNAMENT-COMPLETE' "$OUT/results.txt" && break
  printf '%s\n' "$ctl" | grep -q ALIVE || { echo "!! runner died" >&2; break; }
  [ "$(date +%s)" -gt "$deadline" ] && { echo "!! poll deadline" >&2; break; }
done

# ---- collate ----
{ echo "team_a,team_b,map,winner_side,winner_bot,rounds"
  grep '^RESULT ' "$OUT/results.txt" | while read -r _ TA TB MAP WIN RND; do
    if [ "$WIN" = A ]; then WB=$TA; elif [ "$WIN" = B ]; then WB=$TB; else WB=unknown; fi
    echo "$TA,$TB,$MAP,$WIN,$WB,$RND"
  done; } > "$OUT/results.csv"
grep '^REASON ' "$OUT/results.txt" | sed 's/^REASON //' > "$OUT/reasons.txt" || true

{
  echo "tournament $RUN_ID (UTC)  bots=[$BOTS]  maps=$NMAPS"
  grep '^FORFEIT' "$OUT/results.txt" | sed 's/^/  !! /' || true
  echo
  echo "standings (total games won):"
  for B in $BOTS; do
    w=$(awk -F, -v b="$B" 'NR>1 && $5==b' "$OUT/results.csv" | wc -l)
    t=$(awk -F, -v b="$B" 'NR>1 && ($1==b || $2==b)' "$OUT/results.csv" | wc -l)
    awk -v b="$B" -v w="$w" -v t="$t" 'BEGIN{printf "  %-8s %3d/%d (%.0f%%)\n", b, w, t, (t>0)?100*w/t:0}'
  done
  echo
  echo "head-to-head (wins for row bot vs column bot):"
  for X in $BOTS; do for Y in $BOTS; do
    [ "$X" = "$Y" ] && continue
    w=$(awk -F, -v x="$X" -v y="$Y" 'NR>1 && (($1==x&&$2==y)||($1==y&&$2==x)) && $5==x' "$OUT/results.csv" | wc -l)
    t=$(awk -F, -v x="$X" -v y="$Y" 'NR>1 && (($1==x&&$2==y)||($1==y&&$2==x))' "$OUT/results.csv" | wc -l)
    awk -v x="$X" -v y="$Y" -v w="$w" -v t="$t" 'BEGIN{if(t>0)printf "  %-8s vs %-8s %3d/%d\n", x, y, w, t}'
  done; done
  echo
  echo "swept maps per pair (won from both sides):"
  for X in $BOTS; do for Y in $BOTS; do
    [ "$X" \< "$Y" ] || continue
    awk -F, -v x="$X" -v y="$Y" 'NR>1 && (($1==x&&$2==y)||($1==y&&$2==x)) {r[$3]=r[$3] $5 ";"} END {
      for (m in r) { if (r[m] == x";"x";") sx++; else if (r[m] == y";"y";") sy++; else sp++ }
      printf "  %s-%s: %s sweeps %d, %s sweeps %d, split %d\n", x, y, x, sx+0, y, sy+0, sp+0 }' "$OUT/results.csv"
  done; done
  echo
  echo "replays: battlecode-dev:~/$REMOTE_REPO/arena/tournaments/$RUN_ID/replays/"
} | tee "$OUT/summary.txt"

echo "wrote $OUT/"

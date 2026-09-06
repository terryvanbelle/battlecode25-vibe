#!/usr/bin/env bash
# Run a Gauntlet for the current workspace's bot (TRAINING_ALGORITHM.md).
# For every opponent and map, play both sides headlessly on battlecode-dev.
#
#   cd agents/alice
#   BOT=alice OPPONENTS="examplefuncsplayer alice_iter1" ../../tools/gauntlet.sh
#   MAPS="DefaultSmall DefaultMedium" MAXJOBS=2 ../../tools/gauntlet.sh
#
# Output (workspace-local, gauntlet/<run-id>/):
#   results.csv  opponent,map,bot_side,winner_side,rounds,bot_result
#   reasons.txt  win-type text per game
#   summary.txt  overall + per-opponent win rate, swept-map score, exception count
#   losses/*.bc25  replays of lost games
#
# SHARED VM RULES: battlecode-dev also serves a live BC26 project. This script
# never kills processes and never stops the VM, and its remote runner yields
# while the machine-wide battlecode.server count is at/above GLOBAL_CAP, so
# both projects' runs interleave instead of trampling each other.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

find_workspace
default_bot="$(basename "$WS_REL")"; [ "$default_bot" = arena ] && default_bot=examplefuncsplayer
BOT="${BOT:-$default_bot}"
OPPONENTS="${OPPONENTS:-examplefuncsplayer}"
MAXJOBS="${MAXJOBS:-3}"          # this run's concurrent games
GLOBAL_CAP="${GLOBAL_CAP:-6}"    # machine-wide battlecode.server ceiling (BC26 included)

if [ -z "${MAPS:-}" ]; then
  if [ -f "$REPO_ROOT/tools/bc25-maps.txt" ]; then MAPS="$(tr '\n' ' ' < "$REPO_ROOT/tools/bc25-maps.txt")"
  else MAPS="DefaultSmall"; fi
fi

RUN_ID="$(date +%Y%m%d-%H%M%S)"
OUT="$WS_DIR/gauntlet/$RUN_ID"
mkdir -p "$OUT/losses"
NGAMES=$(( $(echo "$OPPONENTS" | wc -w) * $(echo "$MAPS" | wc -w) * 2 ))
echo "gauntlet $RUN_ID  ws=$WS_REL bot=$BOT  opponents=[$OPPONENTS]  maps=$(echo "$MAPS" | wc -w)  games=$NGAMES  jobs=$MAXJOBS"

ensure_vm
gssh "mkdir -p ~/$REMOTE_REPO/$WS_REL/src" >/dev/null
gscp -r "$WS_DIR/src/." "$USER_NAME@$IP:$REMOTE_REPO/$WS_REL/src/" >/dev/null

RTAG="gauntlet-$RUN_ID"
remote=$(mktemp)
cat > "$remote" <<REMOTE
set -uo pipefail
export JAVA_HOME=\$HOME/jdk21 PATH=\$HOME/jdk21/bin:\$PATH
cd ~/$REMOTE_REPO/$WS_REL
./gradlew --no-daemon -q build >/dev/null 2>&1 || { mkdir -p gauntlet/$RUN_ID; echo "BUILD-FAILED" > gauntlet/$RUN_ID/results.txt; exit 1; }
CP=\$(./gradlew --no-daemon -q printClasspath | tail -1)
mkdir -p gauntlet/$RUN_ID; : > gauntlet/$RUN_ID/results.txt

yield_load () {  # wait while the whole machine is at the game cap (BC26 runs too)
  while [ "\$(pgrep -fc battlecode.server.Main || true)" -ge $GLOBAL_CAP ]; do sleep 10; done
}

game () {  # <opp> <map> <side>
  local OPP=\$1 MAP=\$2 SIDE=\$3 TA TB
  if [ "\$SIDE" = A ]; then TA=$BOT; TB=\$OPP; else TA=\$OPP; TB=$BOT; fi
  local REPLAY=gauntlet/$RUN_ID/\${OPP}__\${MAP}__bot\${SIDE}.bc25 LOG W R RE
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
  EX=\$(printf '%s\n' "\$LOG" | grep -c "^\[\$SIDE:.*Exception" || true)
  {
    printf 'RESULT %s %s %s %s %s\n' "\$OPP" "\$MAP" "\$SIDE" "\${W:-?}" "\${R:-?}"
    printf 'REASON %s %s %s %s\n'    "\$OPP" "\$MAP" "\$SIDE" "\${RE:-?}"
    printf 'EXC %s %s %s %s\n'       "\$OPP" "\$MAP" "\$SIDE" "\${EX:-0}"
  } >> gauntlet/$RUN_ID/results.txt
}

for OPP in $OPPONENTS; do
  for MAP in $MAPS; do
    for SIDE in A B; do
      while [ "\$(jobs -rp | wc -l)" -ge $MAXJOBS ]; do wait -n; done
      yield_load
      game "\$OPP" "\$MAP" "\$SIDE" &
    done
  done
done
wait
echo GAUNTLET-COMPLETE >> gauntlet/$RUN_ID/results.txt
REMOTE
gscp "$remote" "$USER_NAME@$IP:$RTAG.sh" >/dev/null
gssh "setsid bash -c 'bash ~/$RTAG.sh > ~/$RTAG.log 2>&1' </dev/null >/dev/null 2>&1 &" >/dev/null || true

RES="$REMOTE_REPO/$WS_REL/gauntlet/$RUN_ID/results.txt"
echo "  polling every 45s ..."
seen=0; deadline=$(( $(date +%s) + 180*60 ))
while true; do
  sleep 45
  snap=$(gssh "cat $RES 2>/dev/null; echo '@@@'; pgrep -f '$RTAG.sh' >/dev/null && echo ALIVE") || { echo "  (ssh retry)"; continue; }
  body=${snap%@@@*}; ctl=${snap#*@@@}
  printf '%s\n' "$body" > "$OUT/results.txt"
  n=$(printf '%s\n' "$body" | grep -c '^RESULT ' || true)
  if [ "$n" -gt "$seen" ]; then
    printf '%s\n' "$body" | grep '^RESULT ' | tail -n +"$((seen+1))" | while read -r _ OPP MAP SIDE WIN RND; do
      [ "$WIN" = "$SIDE" ] && r="win " || { [ "$WIN" = "?" ] && r="????" || r="LOSS"; }
      printf '  [%3d/%d] %s %-24s %-16s r%s\n' "$n" "$NGAMES" "$r" "$MAP" "$OPP" "$RND"
    done
    seen=$n
  fi
  grep -q '^BUILD-FAILED' "$OUT/results.txt" && { echo "!! remote build failed (see $RTAG.log on VM)" >&2; exit 1; }
  grep -q '^GAUNTLET-COMPLETE' "$OUT/results.txt" && { echo "  complete ($n games)"; break; }
  printf '%s\n' "$ctl" | grep -q ALIVE || { echo "!! runner died at $n/$NGAMES games" >&2; break; }
  [ "$(date +%s)" -gt "$deadline" ] && { echo "!! poll deadline" >&2; break; }
done

# ---- collate ----
{ echo "opponent,map,bot_side,winner_side,rounds,bot_result"
  grep '^RESULT ' "$OUT/results.txt" | while read -r _ OPP MAP SIDE WIN RND; do
    [ "$WIN" = "$SIDE" ] && R=win || { [ "$WIN" = "?" ] && R=unknown || R=loss; }
    echo "$OPP,$MAP,$SIDE,$WIN,$RND,$R"
  done; } > "$OUT/results.csv"
grep '^REASON ' "$OUT/results.txt" | sed 's/^REASON //' > "$OUT/reasons.txt" || true

awk -F, 'NR>1 && $6=="loss"{print $1"__"$2"__bot"$3".bc25"}' "$OUT/results.csv" | while read -r k; do
  [ -n "$k" ] && gscp "$USER_NAME@$IP:$REMOTE_REPO/$WS_REL/gauntlet/$RUN_ID/$k" "$OUT/losses/" >/dev/null 2>&1 || true
done

{
  total=$(($(wc -l < "$OUT/results.csv") - 1))
  wins=$(grep -c ',win$' "$OUT/results.csv" || true)
  echo "run $RUN_ID  ws=$WS_REL bot=$BOT"
  awk -v w="$wins" -v t="$total" 'BEGIN{printf "overall: %d/%d wins (%.1f%%)\n", w, t, (t>0)?100*w/t:0}'
  echo
  echo "  swept maps (won from BOTH sides) -- immune to spawn advantage:"
  for OPP in $OPPONENTS; do
    awk -F, -v o="$OPP" 'NR>1 && $1==o {r[$2]=r[$2] $6 ";"} END {
      sw=0; sl=0; sp=0; n=0
      for (m in r) { n++
        if (r[m] ~ /win;.*win;/) sw++
        else if (r[m] ~ /loss;.*loss;/) sl++
        else sp++ }
      printf "    vs %-24s swept-win %2d/%d   swept-loss %2d   split-by-side %2d\n", o, sw, n, sl, sp
    }' "$OUT/results.csv"
  done
  echo
  for OPP in $OPPONENTS; do
    t=$(grep -c "^$OPP," "$OUT/results.csv" || true)
    w=$(grep -c "^$OPP,.*,win$" "$OUT/results.csv" || true)
    awk -v o="$OPP" -v w="$w" -v t="$t" 'BEGIN{printf "  vs %-24s %d/%d (%.0f%%)\n", o, w, t, (t>0)?100*w/t:0}'
  done
  grep '^EXC ' "$OUT/results.txt" | awk '{s+=$5; if($5>0) n++} END{
      if (s>0) printf "\n  !! %d thrown exceptions across %d games -- a throw abandons the rest\n  !! of that robot turn; fix before trusting this win rate. Worst:\n", s, n }'
  grep '^EXC ' "$OUT/results.txt" | awk '$5>0{printf "  !!   %-16s %-24s bot=%s  %s exceptions\n",$2,$3,$4,$5}' | sort -k5 -rn | head -5
  echo
  echo "losses:"
  awk -F, 'NR>1 && $6=="loss"{printf "  %-24s %-16s bot=%s  r%s\n",$2,$1,$3,$5}' "$OUT/results.csv"
} | tee "$OUT/summary.txt"

echo
echo "wrote $OUT/"
rm -f "$remote"

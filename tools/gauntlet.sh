#!/usr/bin/env bash
# Run a Gauntlet for the current workspace's bot (TRAINING_ALGORITHM.md).
# For every opponent and map, play both sides headlessly on battlecode-dev.
#
#   cd agents/alice
#   BOT=alice OPPONENTS="examplefuncsplayer alice_iter1" ../../tools/gauntlet.sh
#   NMAPS=40 ../../tools/gauntlet.sh                      # wider sample
#   MAPS="DefaultSmall DefaultMedium" MAXJOBS=2 ../../tools/gauntlet.sh
#
# MAP SAMPLING: with no MAPS set, the run plays a fresh RANDOM sample of NMAPS
# (default 25) maps drawn from tools/bc25-maps.txt -- not all 75, and not the
# same 25 every time. Both sides of every map are still played, so the run stays
# balanced; the sample is drawn once and shared by every opponent in the run, so
# within-run comparisons between opponents are exact. The sample is written to
# gauntlet/<run-id>/maps.txt, and passing MAPS="$(cat .../maps.txt)" replays a
# run on exactly the same maps.
#
# WHY RANDOM RATHER THAN A FIXED SET: a fixed map list is an overfitting
# surface -- accepted iterations drift toward the handful of maps in the list.
# Resampling each run tests each iteration on ground its predecessors were not
# tuned against. The cost is that win rates from two different runs are measured
# on different maps, so cross-run deltas are noisier; the accept gate is a
# within-run head-to-head, which is unaffected. Pin MAPS explicitly when you
# specifically need run-to-run comparability (regression checks, ablations,
# tracing a single map).
#
# Output (workspace-local, gauntlet/<run-id>/):
#   results.csv  opponent,map,bot_side,winner_side,rounds,bot_result
#   reasons.txt  win-type text per game
#   summary.txt  overall + per-opponent win rate, swept-map score, exception count
#   losses/*.bc25  replays of lost games
#
# SHARED VM RULES: battlecode-dev also serves a live BC26 project. This script
# never kills processes and never stops the VM. Games are gated by a flock
# semaphore shared by every BC25 runner (GLOBAL_CAP), plus a machine-wide
# ceiling (HARD_CAP) that counts the BC26 project's games too.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
source "$(dirname "${BASH_SOURCE[0]}")/collate.sh"

find_workspace
default_bot="$(basename "$WS_REL")"; [ "$default_bot" = arena ] && default_bot=examplefuncsplayer
BOT="${BOT:-$default_bot}"
OPPONENTS="${OPPONENTS:-examplefuncsplayer}"
MAXJOBS="${MAXJOBS:-3}"          # this run's concurrent games
NMAPS="${NMAPS:-25}"            # size of the random map sample when MAPS is unset
GLOBAL_CAP="${GLOBAL_CAP:-5}"   # BC25 games in flight across ALL agents+tournament
HARD_CAP="${HARD_CAP:-7}"       # machine-wide ceiling, counts the BC26 project too

SAMPLED=0
if [ -z "${MAPS:-}" ]; then
  if [ -f "$REPO_ROOT/tools/bc25-maps.txt" ]; then
    MAPS="$(shuf -n "$NMAPS" "$REPO_ROOT/tools/bc25-maps.txt" | tr '\n' ' ')"
    SAMPLED=1
  else MAPS="DefaultSmall"; fi
fi

RUN_ID="$(date +%Y%m%d-%H%M%S)"
OUT="$WS_DIR/gauntlet/$RUN_ID"
mkdir -p "$OUT/losses"
NGAMES=$(( $(echo "$OPPONENTS" | wc -w) * $(echo "$MAPS" | wc -w) * 2 ))
printf '%s\n' $MAPS > "$OUT/maps.txt"
# Record WHICH BUILD is playing, now, while it is still knowable: src/<agent> is
# a moving target and reconstructing it later from snapshot dates gives an answer
# that changes the moment the candidate is accepted. Never fatal to a run.
python3 "$REPO_ROOT/tools/bot_identity.py" --workspace "$WS_DIR" > "$OUT/bot.txt" 2>/dev/null || true
[ "$SAMPLED" = 1 ] && MAPTAG="$(echo "$MAPS" | wc -w) sampled of $(wc -l < "$REPO_ROOT/tools/bc25-maps.txt")" \
                   || MAPTAG="$(echo "$MAPS" | wc -w) pinned"
echo "gauntlet $RUN_ID  ws=$WS_REL bot=$BOT  opponents=[$OPPONENTS]  maps=$MAPTAG  games=$NGAMES  jobs=$MAXJOBS"

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

# Cross-runner counting semaphore. Three agents plus the tournament all run
# gauntlets on this VM, and a pre-launch "is the machine busy" check races:
# each runner can observe the count below the cap and then all launch at once
# (observed: 7 games against a cap of 6, load 10.3 on 8 vCPUs). Slot files held
# under flock for the LIFETIME of each game make the cap actually binding
# across every BC25 runner. The lock releases automatically when the game's
# subshell exits, so a crashed game cannot leak a slot.
SLOTDIR=\$HOME/.bc25-slots; mkdir -p "\$SLOTDIR"
acquire_slot () {   # sets SFD; held until the game's subshell exits
  # Stand in ONE line, so that the HARD_CAP check below and the slot-taking
  # that follows it cannot be interleaved by another runner. GLOBAL_CAP is
  # enforced by the slot flocks and was never the leak; HARD_CAP is a `pgrep`
  # count, so under the old code two runners could both read "6 < 7" before
  # either started a game and the machine ended up at 8. That is not
  # hypothetical -- 8 concurrent games against a cap of 7 were observed on
  # battlecode-dev on 2026-09-06, and the shape reproduces in a harness
  # (tools/semaphore-test.sh) that returns peak 8 ungated and 7 gated.
  # The kernel drops the gate on fd close, so a runner that dies holding it
  # cannot wedge the box, and a gate holder only ever waits for something no
  # other runner could have proceeded past anyway.
  exec {GFD}>"\$SLOTDIR/gate"
  flock \$GFD
  # Politeness toward the BC26 project, which runs its own games outside this
  # semaphore: never push the machine-wide game count past HARD_CAP.
  while [ "\$(pgrep -fc battlecode.server.Main || true)" -ge $HARD_CAP ]; do sleep 10; done
  while true; do
    for i in \$(seq 1 $GLOBAL_CAP); do
      exec {SFD}>"\$SLOTDIR/slot.\$i"
      flock -n \$SFD && { exec {GFD}>&-; return 0; }   # hold slot, leave the line
      exec {SFD}>&-
    done
    sleep 5
  done
}

game () {  # <opp> <map> <side>
  local OPP=\$1 MAP=\$2 SIDE=\$3 TA TB
  if [ "\$SIDE" = A ]; then TA=$BOT; TB=\$OPP; else TA=\$OPP; TB=$BOT; fi
  local REPLAY=gauntlet/$RUN_ID/\${OPP}__\${MAP}__bot\${SIDE}.bc25 LOG W R RE
  acquire_slot
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
collate_run

echo "wrote $OUT/"
rm -f "$remote"

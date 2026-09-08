#!/usr/bin/env bash
# Measure each agent's committed bot against downloaded BC25 finalist bots.
#
#   tools/benchmark.sh                 # all maps, both sides, every pairing
#   MAPS="DefaultSmall" tools/benchmark.sh
#
# COORDINATOR ONLY. Agents must never run this, never read the benchmark source,
# and never examine a game played against a benchmark bot. Those are hard rules
# from the project owner, and this script is built so they hold by construction
# rather than by anyone's discipline:
#
#   * the benchmark source lives ONLY on battlecode-dev, under ~/bc25-benchmarks,
#     and never enters this repository -- so it is not in any agent's checkout;
#   * NO REPLAY IS EVER WRITTEN. The per-game java invocation deliberately omits
#     -Dbc.server.save-file, so there is no game record to examine and none to
#     discard afterwards. That is the point: nothing to delete beats remembering
#     to delete it;
#   * only the score of each game is kept -- winner and round count, nothing
#     about how it was won.
#
# The benchmark is a YARDSTICK, not an opponent to study or tune against. It
# answers one question: how far is each lineage from a bot that won its division.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib.sh"
source "$HERE/benchmark-collate.sh"

BOTS="${BOTS:-alice bob carol}"
BENCH="${BENCH:-TSPAARKHS v3}"      # staged on the VM under ~/bc25-benchmarks/bench/src
MAXJOBS="${MAXJOBS:-3}"
GLOBAL_CAP="${GLOBAL_CAP:-5}"
HARD_CAP="${HARD_CAP:-7}"
if [ -z "${MAPS:-}" ]; then
  MAPS="$(tr '\n' ' ' < "$REPO_ROOT/tools/bc25-maps.txt")"
fi
MAPS="$(printf '%s ' $MAPS)"

exec 9>/tmp/bc25-benchmark.lock
flock -n 9 || { echo "another benchmark run is already going; exiting"; exit 0; }

RUN_ID="$(date -u +%Y%m%d-%H%M)"
OUT="$REPO_ROOT/benchmarks/$RUN_ID"
mkdir -p "$OUT"
trap 'rm -rf "$STAGE"; [ -s "$OUT/scores.csv" ] || rm -rf "$OUT"' EXIT

STAGE=$(mktemp -d)
for B in $BOTS; do
  git -C "$REPO_ROOT" archive HEAD "agents/$B/src/$B" | tar -x -C "$STAGE" --strip-components=3
  git -C "$REPO_ROOT" log -1 --format="$B %h %s" -- "agents/$B/src/$B"
done > "$OUT/bots.txt"

NMAPS=$(echo "$MAPS" | wc -w)
echo "benchmark $RUN_ID  agents=[$BOTS]  benchmarks=[$BENCH]  maps=$NMAPS  games=$(( $(echo "$BOTS" | wc -w) * $(echo "$BENCH" | wc -w) * NMAPS * 2 ))"

ensure_vm
gssh "mkdir -p ~/bc25-benchmarks/bench/src ~/bc25-benchmarks/stage-$RUN_ID" >/dev/null
gscp -r "$STAGE/." "$USER_NAME@$IP:bc25-benchmarks/stage-$RUN_ID/" >/dev/null

RTAG="benchmark-$RUN_ID"
remote=$(mktemp)
cat > "$remote" <<REMOTE
set -uo pipefail
export JAVA_HOME=\$HOME/jdk21 PATH=\$HOME/jdk21/bin:\$PATH
cd ~/bc25-benchmarks/bench
RES=\$HOME/bc25-benchmarks/$RUN_ID.txt; : > \$RES
# agent bots join the benchmark build; benchmark packages are already there
for B in $BOTS; do rm -rf src/\$B; cp -r ../stage-$RUN_ID/\$B src/; done
./gradlew --no-daemon -q build >/dev/null 2>&1 || { echo BUILD-FAILED >> \$RES; exit 1; }
CP=\$(./gradlew --no-daemon -q printClasspath | tail -1)

GLOBAL_CAP=$GLOBAL_CAP HARD_CAP=$HARD_CAP
$(cat "$REPO_ROOT/tools/remote-slot.sh")

game () {  # <agent> <bench> <map> <side>
  local A=\$1 K=\$2 MAP=\$3 SIDE=\$4 TA TB LOG W R
  if [ "\$SIDE" = A ]; then TA=\$A; TB=\$K; else TA=\$K; TB=\$A; fi
  acquire_slot
  # NO -Dbc.server.save-file: no replay is written, so there is no game record.
  LOG=\$(java -Xmx2g \\
    --add-opens=java.base/jdk.internal.misc=ALL-UNNAMED \\
    --add-opens=java.base/jdk.internal.math=ALL-UNNAMED \\
    --add-opens=java.base/jdk.internal.util=ALL-UNNAMED \\
    --add-opens=java.base/jdk.internal.access=ALL-UNNAMED \\
    --add-opens=java.base/sun.security.action=ALL-UNNAMED \\
    -Dbc.server.wait-for-client=false -Dbc.server.mode=headless -Dbc.server.map-path=maps \\
    -Dbc.server.robot-player-to-system-out=false -Dbc.server.debug=false \\
    -Dbc.engine.debug-methods=false -Dbc.engine.enable-profiler=false \\
    -Dbc.game.team-a="\$TA" -Dbc.game.team-b="\$TB" \\
    -Dbc.game.team-a.url=build/classes -Dbc.game.team-b.url=build/classes \\
    -Dbc.game.team-a.package="\$TA" -Dbc.game.team-b.package="\$TB" \\
    -Dbc.game.maps="\$MAP" -Dbc.server.validate-maps=true -Dbc.server.alternate-order=false \\
    -cp "\$CP" battlecode.server.Main -c=- 2>&1 || true)
  W=\$(printf '%s\n' "\$LOG" | sed -n 's/.*(\([AB]\)) wins.*/\1/p' | tail -1)
  R=\$(printf '%s\n' "\$LOG" | sed -n 's/.*wins (round \([0-9]*\)).*/\1/p' | tail -1)
  # score only: who won and how long. Nothing about how.
  printf 'RESULT %s %s %s %s %s %s\n' "\$A" "\$K" "\$MAP" "\$SIDE" "\${W:-?}" "\${R:-?}" >> \$RES
}

for A in $BOTS; do for K in $BENCH; do for MAP in $MAPS; do for SIDE in A B; do
  while [ "\$(jobs -rp | wc -l)" -ge $MAXJOBS ]; do wait -n; done
  game "\$A" "\$K" "\$MAP" "\$SIDE" &
done; done; done; done
wait
rm -rf ~/bc25-benchmarks/stage-$RUN_ID
echo BENCHMARK-COMPLETE >> \$RES
REMOTE
gscp "$remote" "$USER_NAME@$IP:$RTAG.sh" >/dev/null
gssh "setsid bash -c 'bash ~/$RTAG.sh > /dev/null 2>&1' </dev/null >/dev/null 2>&1 &" >/dev/null || true
rm -f "$remote"

RES="bc25-benchmarks/$RUN_ID.txt"
echo "  polling every 60s ..."
deadline=$(( $(date +%s) + 600*60 ))
while true; do
  sleep 60
  snap=$(gssh "cat $RES 2>/dev/null; echo '@@@'; pgrep -f '$RTAG.sh' >/dev/null && echo ALIVE") || continue
  body=${snap%@@@*}; ctl=${snap#*@@@}
  printf '%s\n' "$body" > "$OUT/raw.txt"
  n=$(printf '%s\n' "$body" | grep -c '^RESULT ' || true)
  echo "  $n games"
  grep -q '^BUILD-FAILED' "$OUT/raw.txt" && { echo "!! remote build failed" >&2; exit 1; }
  grep -q '^BENCHMARK-COMPLETE' "$OUT/raw.txt" && break
  printf '%s\n' "$ctl" | grep -q ALIVE || { echo "!! runner died at $n games" >&2; break; }
  [ "$(date +%s)" -gt "$deadline" ] && { echo "!! poll deadline" >&2; break; }
done

# Collation lives in benchmark-collate.sh so that this path and
# benchmark-collect.sh (recovery) cannot drift apart -- a recovered run has to be
# comparable with a live one or it is not worth recovering.
RAW="$OUT/raw.txt"
collate_benchmark
rm -f "$RAW"
gssh "rm -f ~/$RES ~/$RTAG.sh" >/dev/null 2>&1 || true

cat "$OUT/summary.md"
echo "wrote $OUT/"

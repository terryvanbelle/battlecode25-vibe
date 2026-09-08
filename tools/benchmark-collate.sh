#!/usr/bin/env bash
# Shared collation for the finalist-bot benchmark, sourced by both
# tools/benchmark.sh (live run) and tools/benchmark-collect.sh (recovery).
#
# Extracted rather than duplicated for the reason the tournament collation was:
# two copies of a scoring rule drift, and the drift is invisible because both
# outputs still look like plausible tables. A recovered run must be byte-for-byte
# comparable with a live one or it cannot be compared to the previous week's.
#
# Expects: OUT (local run dir), RAW (file of raw remote output), RUN_ID.
# Derives the agent and benchmark lists FROM THE DATA rather than from the
# caller's environment, so a recovery works without knowing how the run was
# launched.

collate_benchmark () {
  local complete=1
  grep -q '^BENCHMARK-COMPLETE' "$RAW" || complete=0

  # RESULT <agent> <benchmark> <map> <agent_side> <winner_side> <rounds>
  { echo "agent,benchmark,map,agent_side,winner_side,rounds,agent_result"
    grep '^RESULT ' "$RAW" | while read -r _ A K MAP SIDE W R; do
      [ "$W" = "$SIDE" ] && r=win || { [ "$W" = "?" ] && r=unknown || r=loss; }
      echo "$A,$K,$MAP,$SIDE,$W,$R,$r"
    done; } > "$OUT/scores.csv"

  local agents benches
  agents=$(awk -F, 'NR>1{if(!($1 in s)){s[$1]=1; printf "%s ", $1}}' "$OUT/scores.csv")
  benches=$(awk -F, 'NR>1{if(!($2 in s)){s[$2]=1; printf "%s ", $2}}' "$OUT/scores.csv")

  { echo "# Benchmark $RUN_ID"
    echo
    if [ "$complete" = 0 ]; then
      echo "> **!! INCOMPLETE** — this run has no \`BENCHMARK-COMPLETE\` marker."
      echo "> It was collated from a runner that stopped early (session death,"
      echo "> poll deadline, or a killed process). The games below really were"
      echo "> played, but the map coverage is PARTIAL and agents may have"
      echo "> unequal sample sizes — compare win% across agents only after"
      echo "> checking the \`played\` column."
      echo
    fi
    echo "Each agent's committed bot against downloaded BC25 finalist bots, all maps, both sides."
    echo "Scores only — no replays were written and none exist."
    echo
    echo "| agent | benchmark | won | played | win% | swept | swept against |"
    echo "|---|---|---|---|---|---|---|"
    for A in $agents; do for K in $benches; do
      awk -F, -v a="$A" -v k="$K" 'NR>1 && $1==a && $2==k {
          t++; if ($7=="win") w++; r[$3]=r[$3] $7 ";" }
        END { if (!t) exit
          for (m in r) { if (r[m] ~ /win;.*win;/) sw++; else if (r[m] ~ /loss;.*loss;/) sl++ }
          printf "| %s | %s | %d | %d | %.1f%% | %d | %d |\n", a, k, w+0, t+0, (t?100*w/t:0), sw+0, sl+0 }' "$OUT/scores.csv"
    done; done

    # Unequal samples make the win% column non-comparable across rows, and that
    # is invisible in a table of percentages. Say it explicitly when it happens.
    awk -F, 'NR>1{n[$1"/"$2]++} END{
        for (k in n) { if (min=="" || n[k]<min) min=n[k]; if (n[k]>max) max=n[k] }
        if (max != min) printf "\n> **!! UNEQUAL SAMPLES** — pairings range from %d to %d games, so win%% is not comparable across rows.\n", min, max }' "$OUT/scores.csv"

    echo
    echo "## What played"; echo
    if [ -s "$OUT/bots.txt" ]; then
      sed 's/^/- /' "$OUT/bots.txt"
    else
      echo "- (bots.txt not recovered — it is written driver-side at launch and"
      echo "  does not exist on the VM, so a run recovered on a fresh checkout"
      echo "  cannot say which commits played.)"
    fi
  } > "$OUT/summary.md"

  [ "$complete" = 0 ] && echo "!! run $RUN_ID is INCOMPLETE — collated anyway" >&2
  return 0
}

#!/usr/bin/env bash
# Collate a gauntlet run's raw results.txt into results.csv / reasons.txt /
# summary.txt, and pull the losing replays back. Shared by gauntlet.sh (which
# calls it at the end of its poll loop) and gauntlet-collect.sh (which calls it
# for a run whose poll loop died). Source this; not executable on its own.
#
# collate_run expects these to be set by the caller, exactly as gauntlet.sh
# names them: OUT RUN_ID BOT WS_REL OPPONENTS MAPTAG SAMPLED IP USER_NAME.
# $OUT/results.txt must already exist locally.

collate_run () {
  local complete=0
  grep -q '^GAUNTLET-COMPLETE' "$OUT/results.txt" && complete=1

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
    # A run that stopped early (poll deadline, dead runner, a session that died
    # under it) is still readable, but its per-opponent totals are a PREFIX of
    # the plan -- opponents are the outer loop, so the last ones may have no
    # games at all. Say so at the top, the way tournament summaries do, rather
    # than letting a short run read as a finished one.
    [ "$complete" = 1 ] || echo "!! INCOMPLETE -- no GAUNTLET-COMPLETE marker; games below are a prefix of the plan"
    echo "run $RUN_ID  ws=$WS_REL bot=$BOT  maps=$MAPTAG"
    if [ "$SAMPLED" = 1 ]; then
      echo "  map sample (random this run; replay with MAPS=\"\$(cat $OUT/maps.txt)\"):"
      tr '\n' ' ' < "$OUT/maps.txt" | fold -s -w 76 | sed 's/^/    /'
      echo
    fi
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
}

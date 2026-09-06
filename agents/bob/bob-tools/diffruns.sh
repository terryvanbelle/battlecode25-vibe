#!/usr/bin/env bash
# Game-by-game diff of two gauntlet runs' results.csv (opponent,map,side keyed).
# Usage: bob-tools/diffruns.sh gauntlet/<runA> gauntlet/<runB>
set -euo pipefail
A="$1/results.csv"; B="$2/results.csv"
join -t, -j1 \
  <(awk -F, 'NR>1{print $1"__"$2"__"$3","$6","$5}' "$A" | sort) \
  <(awk -F, 'NR>1{print $1"__"$2"__"$3","$6","$5}' "$B" | sort) \
| awk -F, '
  $2!=$4 { printf "FLIP  %-50s %s(r%s) -> %s(r%s)\n", $1, $2, $3, $4, $5; f++ ; next}
  $3!=$5 { printf "drift %-50s rounds %s -> %s (%s)\n", $1, $3, $5, $2; d++ }
  END { printf "\n%d flips, %d round-drifts (same result)\n", f, d }'

#!/usr/bin/env bash
# Iteration 38 link-1 manipulation check: did the return-to-refill DECISION actually fire?
#
# homeAsk/homeGo are cumulative per-robot counters stamped into the indicator string as
# ha=/hg=. ReplayDump only prints indicator strings inside a --from/--to window, so take a
# narrow window late in the game and read the last value each surviving robot reached.
#
#   homecheck.sh <replay.bc25> [round]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
R="${2:-1900}"
DUMP=$("$HERE/dumpcache.sh" "$1" --quiet --from "$R" --to $((R+2)))
grep -o 'ha=[0-9]* hg=[0-9]*' "$DUMP" | awk -F'[= ]' '
  {ask+=$2; go+=$4; n++}
  END {if(n) printf "robots=%d  homeAsk=%d  homeGo=%d  hit-rate=%.1f%%\n", n, ask, go, 100*go/ask;
       else print "no ha=/hg= counters found -- is this an i38 build?"}'

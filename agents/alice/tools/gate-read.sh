#!/usr/bin/env bash
# Read a gauntlet run against the accept gate, in the form my ledger requires:
# wins/losses, swept-win, swept-loss, split, and the margin identity check.
#
#   tools/gate-read.sh gauntlet/<run-id> [opponent ...]
#
# RESULT format (tools/gauntlet.sh:148): RESULT <OPP> <MAP> <MY-SIDE> <WINNING-SIDE> <ROUNDS>
# so I win a game iff field 4 == field 5. Field 2 is the OPPONENT, never the winner --
# that confusion cost me a phantom "tournament is broken" report once already.
set -euo pipefail
RUN="${1:?usage: gate-read.sh <run-dir> [opponent ...]}"; shift || true
R="$RUN/results.txt"
[ -f "$R" ] || { echo "no results.txt in $RUN" >&2; exit 1; }
OPPS=("$@")
if [ "${#OPPS[@]}" -eq 0 ]; then
  mapfile -t OPPS < <(awk '/^RESULT/{print $2}' "$R" | sort -u)
fi
printf '%-18s %7s %5s %5s %5s %7s %s\n' opponent record SW SL split margin identity
for O in "${OPPS[@]}"; do
  awk -v opp="$O" '
    $1=="RESULT" && $2==opp {
      m=$3; n[m]=1
      if ($4==$5) { w++; wm[m]++ } else { l++; lm[m]++ }
    }
    END {
      for (k in wm) if (wm[k]==2) sw++
      for (k in lm) if (lm[k]==2) sl++
      nmaps = length(n); split_ = nmaps - sw - sl
      margin = w - nmaps            # margin over 50%, per MAP (= SW - SL)
      ok = (margin == sw - sl) ? "OK" : "MISMATCH"
      printf "%-18s %3d-%-3d %5d %5d %5d %+7d  %s (wins-N=%d, SW-SL=%d)\n",
             opp, w, l, sw, sl, split_, margin, ok, margin, sw-sl
    }' "$R"
done
echo
printf 'exceptions: %s\n' "$(awk '/^EXC/{s+=$5} END{print s+0}' "$R")"

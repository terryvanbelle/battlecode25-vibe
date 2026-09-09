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
# --- STANDING PRE-CHECKS, printed on EVERY verdict read -------------------------
# Doctrine 16: a lesson you wrote is not a control; install the check where the
# mistake happens. Each line below has already cost this lineage a candidate, and
# the first one has cost it THREE (iterations 20, 26 and 39a). Printing them here
# is deliberate -- this runs whether or not I think I need it.
cat >&2 <<'PRECHECK'
  -- before reading these numbers as a verdict ---------------------------------
  1. SCARCITY. Name the resource you claim was wasted, and the resource that is
     actually binding. If they differ, the freed resource buys nothing.
     (i20: freed soldier TURNS, paint was binding -> null. i26: spent chips,
      paint was binding -> -21. i39a: freed build SLOTS, tower paint was
      binding, and the "idling" WAS the accumulation -> splashers went to 0.)
  2. UNIT. net_swept = SW-SL = wins-N. sd(net_swept) = sqrt(decisive) = sd(wins).
     wins-losses is 2x net_swept and its sd is 2x. Gate and floor must be in the
     SAME unit; the identity column below fails loudly if they are not.
  3. BITE. Was the mechanism check run on a map where the mechanism is KNOWN to
     act? A near-inert map says nothing either way (the iteration 38 error).
  4. DIVERSION. If this candidate redirects a unit's turn, state what those turns
     were DOING BEFORE -- measured, not assumed. A branch that is "inert on 96.2%
     of turns" is a fact about the BRANCH; those turns may be the bot working.
     (i44: diverted hungry soldiers to remembered towers, -58 net swept. The
      96.2% of hungry turns with no tower in vision were the turns the soldier
      spent painting and capturing ruins. Paint was not binding; ruin-capture
      TEMPO was, and the diversion spent it. Towers 4 v 8 by round 200.)
  ------------------------------------------------------------------------------
PRECHECK

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

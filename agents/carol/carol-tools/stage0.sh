#!/usr/bin/env bash
# Stage 0: the MANDATORY pre-gauntlet check (TRAINING_ALGORITHM 5.0).
#
# WHY THIS TOOL REFUSES TO PRINT WHO WON.
#
# LEARNINGS carries "Replay inspection is for MECHANISM, never for VERDICT (iteration 41/42,
# the costly one)". Iteration 47 then read a one-map, one-SIDE stage-0 result as a "complete
# reversal" -- 25 towers to 5 on Leaf -- and the 100-game screen came back at -0.93 sd. That
# same run reported 60% of its maps splitting by spawn side, so a single-side game carries
# almost no information about the pair. The lesson was already written down and did not fire.
#
# Doctrine 19: a lesson you wrote is not a control; install the check where the mistake
# happens. So this tool answers only the two questions stage 0 is FOR --
#
#     1. IDENTITY   : do the arms actually differ? (if not, the whole run is wasted)
#     2. MECHANISM  : did the intended behaviour change, in the direction intended?
#
# -- and deliberately does not print, and does not collect, the winner. If you want to know
# whether the candidate is better, run the gauntlet; that is the only thing that can tell you.
# Both sides are played because a one-side result is not a sample of anything.
#
#   stage0.sh <candidate> <baseline> <map>
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS="$(cd "$HERE/.." && pwd)"
REPO="$(cd "$WS/../.." && pwd)"
[ "$#" -eq 3 ] || { echo "usage: stage0.sh <candidate> <baseline> <map>" >&2; exit 1; }
CAND="$1"; BASE="$2"; MAP="$3"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

run () { # $1=teamA $2=teamB -> echoes replay path
  ( cd "$WS" && TEAM_A="$1" TEAM_B="$2" "$REPO/tools/vm-match.sh" "$MAP" >/dev/null 2>&1 )
  echo "$WS/matches/$1-vs-$2-on-$MAP.bc25"
}

echo "=== stage 0: $CAND vs $BASE on $MAP (both sides) ==="
echo "    identity + mechanism only -- this tool does not report the winner, by design."
echo

R1="$(run "$CAND" "$BASE")"
R2="$(run "$BASE" "$CAND")"
R3="$(run "$BASE" "$BASE")"

for tag in "A:$R1" "B:$R2" "ref:$R3"; do
  side="${tag%%:*}"; rp="${tag#*:}"
  "$REPO/tools/replay-dump.sh" "$rp" --every 1 > "$TMP/$side.txt" 2>/dev/null
done

# IDENTITY: a live mechanism must change the game away from the baseline-vs-baseline reference.
r1=$(grep -c '^round' "$TMP/A.txt" || true)
r3=$(grep -c '^round' "$TMP/ref.txt" || true)
echo "IDENTITY"
if [ "$r1" = "$r3" ] && diff -q <(grep '| T1' "$TMP/A.txt") <(grep '| T1' "$TMP/ref.txt") >/dev/null 2>&1; then
  echo "  !! candidate arm is IDENTICAL to the $BASE-vs-$BASE reference."
  echo "  !! The mechanism is DEAD on this map. Do not spend a gauntlet."
else
  echo "  arms differ from the $BASE-vs-$BASE reference (rounds $r1 vs $r3) -- mechanism is live."
fi

echo
echo "MECHANISM (build events, --every 1, both sides; doctrine 18 safe -- these are events)"
"$REPO/tools/.venv/bin/python3" "$HERE/mixcheck/channels.py" "$TMP/A.txt" "$TMP/B.txt"
echo
echo "Reminder: a difference above is evidence the mechanism FIRED, never that it PAID."
echo "Doctrine: a manipulation check proves the mechanism fired, never that firing it helped."

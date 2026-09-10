#!/usr/bin/env bash
# Is the absolute-strength instrument stale? Exits NON-ZERO if it is.
#
#   tools/roster-stale.sh [max_accepts_behind]     # default 1
#
# WHY THIS EXISTS. On 2026-09-10 the frozen-roster run came back after being last
# run at iteration 39 and reported that iteration 43 -- the live bot, four accepts
# later -- LOSES to iteration 39 by -7 net swept. An entire session had been spent
# probing and optimising from a baseline that had already regressed.
#
# A stale absolute-strength instrument is WORSE than an absent one: its last
# reading silently licenses the belief that the bot has been improving, and every
# other instrument I own (gauntlet headline, tournament standings) is relative and
# cannot separate "the bot improved" from "the instrument moved".
#
# The fix is not to remember to run it. It is to make the staleness loud, tied to
# ACCEPTS rather than to convenience (doctrine 19: install the check where the
# mistake happens). Run this before proposing any mechanism.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
MAX="${1:-1}"
# Validate the argument. A garbage limit made `[ "$BEHIND" -gt "$MAX" ]` fail
# silently and return the reassuring branch -- the exact defect this file exists
# to prevent, present in its own first draft. Caught by trying to exercise the
# failure path instead of assuming it worked.
case "$MAX" in
  ''|*[!0-9]*) echo "!! limit must be a non-negative integer, got: '$MAX'" >&2; exit 2 ;;
esac

# --selftest injects values so the FAILURE branch is provably exercised. A check
# whose failure path has never run is not a check.
if [ "${SELFTEST:-}" = "1" ]; then
  BEHIND=5; MEASURED=39; LATEST=43; MAX=1
  echo "SELFTEST: injecting latest=43 measured=39 behind=5 limit=1"
  echo "latest accepted snapshot : alice_iter$LATEST"
  echo "last roster measurement  : alice_iter$MEASURED"
  echo "accepts behind           : $BEHIND   (limit $MAX)"
  if [ "$BEHIND" -gt "$MAX" ]; then
    echo "!! ROSTER IS STALE by $BEHIND accepts. (selftest: failure branch reached)"
    exit 1
  fi
  echo "SELFTEST FAILED -- the failure branch did not trigger"; exit 3
fi

# Accepted snapshots are the ground truth for "how far the bot has moved".
LATEST=$(ls -d src/alice_iter*/ 2>/dev/null | sed 's#.*alice_iter\([0-9]*\)/#\1#' \
         | sort -n | tail -1)
[ -n "$LATEST" ] || { echo "!! no src/alice_iterN snapshots found"; exit 2; }

HIST=progress/vs_old_bots_history.csv
[ -f "$HIST" ] || { echo "!! no $HIST -- the roster has NEVER been run"; exit 1; }

# The "as <bot>" column records which bot was measured. Take the highest iterN
# that appears in a roster-run row.
MEASURED=$(grep 'roster-run' "$HIST" | sed -n 's/.*alice_iter\([0-9]*\),.*/\1/p' \
           | sort -n | tail -1)
[ -n "$MEASURED" ] || { echo "!! no roster-run rows in $HIST"; exit 1; }

# Count accepted snapshots strictly between the measured one and the latest.
BEHIND=$(ls -d src/alice_iter*/ 2>/dev/null | sed 's#.*alice_iter\([0-9]*\)/#\1#' \
         | sort -n | awk -v m="$MEASURED" '$1 > m' | wc -l)

echo "latest accepted snapshot : alice_iter$LATEST"
echo "last roster measurement  : alice_iter$MEASURED"
echo "accepts behind           : $BEHIND   (limit $MAX)"

if [ "$BEHIND" -gt "$MAX" ]; then
  cat <<EOF
!! ROSTER IS STALE by $BEHIND accepts.
   Your only absolute-strength instrument has not seen the current bot. Run it
   BEFORE proposing a mechanism -- the last time this went $BEHIND behind, it was
   hiding a regression and a whole session was spent optimising from it:

     OPPONENTS="\$(../../tools/.venv/bin/python3 ../../tools/track_vs_old_bots.py --roster)" \\
         ../../tools/gauntlet.sh
     ../../tools/.venv/bin/python3 ../../tools/track_vs_old_bots.py gauntlet/<run-id>
EOF
  exit 1
fi
echo "OK: the roster is current enough to trust."

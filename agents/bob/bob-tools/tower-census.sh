#!/usr/bin/env bash
# bob-tools/tower-census.sh -- how many towers does bob ever hold, per replay?
#
# Built for iteration 33's PRE-REGISTERED tournament prediction (1): "bob's tower
# count stops being pinned at 2 on ruin-poor maps." That is a MECHANISM reading
# checkable in a replay, and it does not depend on the win column -- which matters
# because doctrine 9061b80 says a cross-lineage claim can only be tested in the
# tournament, and the tournament's win column is a noisy way to read one mechanism.
#
#   bob-tools/tower-census.sh <replay.bc25> [more.bc25 ...]
#
# Prints one line per replay: map, which side bob was, bob's STARTING and MAX tower
# count, and the same for the opponent. Baseline to beat, from 20260908-1300:
#   CastleDefense max 2, Filter max 2   (pinned; carol reached 4 and 5)
#   Money         max 15                (ruin-rich, bob is fine there)
#
# WHY MAX AND NOT FINAL: towers get destroyed, so a final count of 2 is ambiguous
# between "never built" and "built and lost". Max separates them, and "never built"
# is the claim under test.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"

printf '%-22s %-4s %-14s %-14s %s\n' map side "bob tw start/max" "opp tw start/max" rounds
for R in "$@"; do
  [ -f "$R" ] || { echo "no such replay: $R" >&2; continue; }
  OUT="$("$REPO/tools/replay-dump.sh" "$R" --every 10 2>/dev/null)" || { echo "dump failed: $R" >&2; continue; }

  # Which side is bob? Read it from the replay, never from the filename -- the
  # filename says who was team_a in the SCHEDULE, and a mis-join here would print a
  # plausible-looking wrong answer (doctrine 9061b80's mis-joined column).
  HDR="$(printf '%s\n' "$OUT" | grep -m1 '^=== GameHeader')"
  T1="$(sed -n 's/.*team1=\([^ ]*\).*/\1/p' <<<"$HDR")"
  T2="$(sed -n 's/.*team2=\([^ ]*\).*/\1/p' <<<"$HDR")"
  if   [ "$T1" = bob ]; then BOBT=1; OPP="$T2"
  elif [ "$T2" = bob ]; then BOBT=2; OPP="$T1"
  else echo "bob is not in $R (team1=$T1 team2=$T2)" >&2; continue; fi

  MAP="$(printf '%s\n' "$OUT" | sed -n 's/.*MatchHeader map=\([^ ]*\).*/\1/p' | head -1)"
  RND="$(printf '%s\n' "$OUT" | sed -n 's/.*MatchFooter.*rounds=\([0-9]*\).*/\1/p' | head -1)"

  tw () {  # $1 = team number -> newline-separated tw values in round order
    printf '%s\n' "$OUT" | grep '^round [0-9]* |' \
      | awk -v t="$1" '{ n=split($0,seg,/\| T/); if (n>t) { split(seg[t+1],f," ");
          for(i=1;i<=length(f);i++) if (f[i] ~ /^tw[0-9]+$/) { print substr(f[i],3); break } } }'
  }
  # Capture ONCE into a variable, then slice it. Piping tw() straight into `head -1`
  # closes the pipe early, which under `set -o pipefail` turns SIGPIPE into a fatal
  # exit 141 partway through a multi-replay run -- it killed the third replay of the
  # first test while the first two printed correct answers, which is exactly the kind
  # of partial success that reads as "done".
  BOBTW="$(tw $BOBT)"; OPPTW="$(tw $((3-BOBT)))"
  BS="$(head -1 <<<"$BOBTW")"; BM="$(sort -n <<<"$BOBTW" | tail -1)"
  OS="$(head -1 <<<"$OPPTW")"; OM="$(sort -n <<<"$OPPTW" | tail -1)"
  printf '%-22s T%-3s %-14s %-14s %s\n' "$MAP" "$BOBT vs $OPP" "$BS/$BM" "$OS/$OM" "${RND:-?}"
done

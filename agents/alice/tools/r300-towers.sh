#!/usr/bin/env bash
# Iteration 47 falsifier: tower count at a given round, per team, for a set of
# replays, labelled by which team is the ARM.
#
#   tools/r300-towers.sh <arm-package> [--round R] <replay.bc25> ...
#
# Prints one TSV row per replay:  map  side  round  armTowers  ctlTowers  diff
# and a summary mean. Reads the replay-dump per-round summary line, whose `tw<N>`
# field is the team's tower count; `--every R` is honoured (verified 2026-09-09:
# 34 summary lines at --every 50 on a 1556-round game = 3 always-printed opening
# rounds + 1556/50).
#
# WHY BY REPLAY AND NOT BY WIN RATE: the gate already measures who wins. This
# measures whether the win came through the mechanism I claimed -- more towers at
# r300 -- which a win rate cannot distinguish from an unexplained gain.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARM="${1:?usage: r300-towers.sh <arm-package> [--round R] <replay.bc25> ...}"; shift
ROUND=300
if [ "${1:-}" = "--round" ]; then ROUND="$2"; shift 2; fi
printf 'map\tside\tround\tarm_tw\tctl_tw\tdiff\n'
sum=0; n=0
for f in "$@"; do
  out=$("$HERE/../../../tools/replay-dump.sh" "$f" --every "$ROUND" 2>/dev/null) || continue
  hdr=$(printf '%s\n' "$out" | sed -n 's/^=== GameHeader  team1=\([^ ]*\)  team2=\([^ ]*\).*/\1 \2/p')
  t1=${hdr%% *}; t2=${hdr##* }
  if   [ "$t1" = "$ARM" ]; then armIdx=1; ctlIdx=2
  elif [ "$t2" = "$ARM" ]; then armIdx=2; ctlIdx=1
  else echo "!! $f: neither team is $ARM ($t1/$t2)" >&2; continue; fi
  map=$(printf '%s\n' "$out" | sed -n 's/^=== MatchHeader map=\([^ ]*\).*/\1/p')
  line=$(printf '%s\n' "$out" | grep "^round $ROUND | " || true)
  [ -n "$line" ] || { echo "!! $f: no summary at round $ROUND" >&2; continue; }
  # Split on '|' first. A single greedy regex over the whole line reaches the
  # OTHER team's tw field and silently reports the wrong team -- caught before
  # this script was ever used, by the case where the two teams differ.
  a=$(printf '%s\n' "$line" | awk -F'|' -v i="$armIdx" '{split($(i+1),f," "); for(k in f) if(f[k]~/^tw[0-9]+$/) print substr(f[k],3)}')
  c=$(printf '%s\n' "$line" | awk -F'|' -v i="$ctlIdx" '{split($(i+1),f," "); for(k in f) if(f[k]~/^tw[0-9]+$/) print substr(f[k],3)}')
  [ -n "$a" ] && [ -n "$c" ] || { echo "!! $f: could not read tw" >&2; continue; }
  printf '%s\tT%s\t%s\t%s\t%s\t%+d\n' "$map" "$armIdx" "$ROUND" "$a" "$c" "$((a-c))"
  sum=$((sum + a - c)); n=$((n+1))
done
[ "$n" -gt 0 ] && awk -v s="$sum" -v n="$n" -v r="$ROUND" 'BEGIN{printf "\nmean arm-minus-control towers at round %s: %+.2f over %d games\n", r, s/n, n}' || true

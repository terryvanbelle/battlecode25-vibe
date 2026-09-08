#!/usr/bin/env bash
# Iteration 40's link-1 check: did money towers actually buy UPGRADES?
#
# UPGRADE events appear in the dump's event log at any stride, so an --every 200 dump is
# enough and no detailed window is needed. Split by team, and split PAINT upgrades out --
# only a paint tower's upgrade converts chips into paint income (5/turn -> 10/turn), which
# is the whole causal chain. Money-tower upgrades raise chip income, which is a means, not
# the end.
#
# Round-1 upgrades are excluded: all four starting towers upgrade on round 1 for free and
# counting them adds a constant 2 per team that hides small real differences.
#
#   upgrades.sh <replay.bc25> [...]
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
printf '%-24s %-16s %8s %8s %8s\n' map team upgrades paintUpg moneyUpg
for R in "$@"; do
  D=$("$HERE/dumpcache.sh" "$R" --every 200)
  MAP=$(sed -n '2p' "$D" | grep -o 'map=[^ ]*' | cut -d= -f2)
  T1=$(head -1 "$D" | grep -o 'team1=[^ ]*' | cut -d= -f2)
  T2=$(head -1 "$D" | grep -o 'team2=[^ ]*' | cut -d= -f2)
  for T in T1 T2; do
    NAME=$([ "$T" = T1 ] && echo "$T1" || echo "$T2")
    L=$(grep 'UPGRADE' "$D" | grep -v '^round 1 ' | grep "($T,")
    printf '%-24s %-16s %8d %8d %8d\n' "$MAP" "$NAME" \
      "$(echo "$L" | grep -c .)" "$(echo "$L" | grep -c PAINT)" "$(echo "$L" | grep -c MONEY)"
  done
done

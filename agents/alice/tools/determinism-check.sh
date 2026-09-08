#!/usr/bin/env bash
# Compare two gauntlet runs on the maps they share, for the same opponent.
# Under a deterministic engine every shared (map, side) cell must match exactly.
# Only compares maps where BOTH runs have played BOTH games -- a partially played
# map looks like a mismatch and is not one. (I made exactly that error once.)
set -euo pipefail
R1="${1:?usage: determinism-check.sh <run1> <run2> [opponent]}"
R2="${2:?}"; OPP="${3:-alice_iter24}"
match=0; differ=0; skipped=0
while read -r M; do
  A=$(grep "^RESULT $OPP $M " "$R1/results.txt" | awk '{print $4$5}' | sort | tr '\n' ',')
  B=$(grep "^RESULT $OPP $M " "$R2/results.txt" | awk '{print $4$5}' | sort | tr '\n' ',')
  na=$(grep -c "^RESULT $OPP $M " "$R1/results.txt" || true)
  nb=$(grep -c "^RESULT $OPP $M " "$R2/results.txt" || true)
  if [ "$na" -lt 2 ] || [ "$nb" -lt 2 ]; then
    printf '  %-16s SKIP (incomplete: %d and %d games)\n' "$M" "$na" "$nb"; skipped=$((skipped+1)); continue
  fi
  if [ "$A" = "$B" ]; then printf '  %-16s MATCH  %s\n' "$M" "$A"; match=$((match+1))
  else printf '  %-16s ***DIFFER***  run1=%s run2=%s\n' "$M" "$A" "$B"; differ=$((differ+1)); fi
done < <(comm -12 <(sort "$R1/maps.txt") <(sort "$R2/maps.txt"))
echo
echo "shared maps fully played: $((match+differ))   match: $match   differ: $differ   skipped: $skipped"
[ "$differ" -eq 0 ] || echo "!! NON-DETERMINISM: the zero-variance-null reasoning does not hold. Report this."

#!/usr/bin/env bash
# Re-fork src/bob_denier from the CURRENT accepted bot, re-applying only the
# paint-denial spawn policy. The archetype exists to answer "can I handle an
# opponent that erases paint"; every other difference from the live bot is
# staleness, and staleness silently inflates our win rate against it
# (TRAINING_ALGORITHM.md: a stale fork once masked a 62.5% as 95.0%).
#
# Usage: bob-tools/refork-denier.sh          # re-fork
#        bob-tools/refork-denier.sh --check  # report drift, change nothing
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

OLD_POLICY='        UnitType want = (spawned % 5 == 4) ? UnitType.MOPPER
                       : (spawned % 5 == 2 && rc.getRoundNum() > 60) ? UnitType.SPLASHER
                       : UnitType.SOLDIER;'

if [ "${1:-}" = "--check" ]; then
  drift=0
  for f in src/bob/*.java; do
    b=$(basename "$f"); [ "$b" = Tower.java ] && continue
    diff -q <(sed 's/^package bob;/package X;/' "$f") \
            <(sed 's/^package bob_denier;/package X;/' "src/bob_denier/$b") >/dev/null \
      || { echo "STALE: $b differs from the live bot"; drift=1; }
  done
  [ $drift = 0 ] && echo "bob_denier is in sync with the live bot (Tower.java policy aside)"
  exit $drift
fi

rm -rf src/bob_denier.new && cp -r src/bob src/bob_denier.new
sed -i 's/^package bob;/package bob_denier;/' src/bob_denier.new/*.java
python3 - "$OLD_POLICY" <<'PY'
import sys, pathlib
old = sys.argv[1]
p = pathlib.Path('src/bob_denier.new/Tower.java')
s = p.read_text()
new = """        // ARCHETYPE (paint denial). See src/bob_denier/README for what this is for.
        // The lineage's own bots are all painting races that spawn 3 soldiers per
        // splasher per mopper. Soldiers CANNOT overwrite enemy paint (engine fact),
        // so once the map saturates they cannot move the score at all. This pole
        // inverts that: a short economy phase, then splashers and moppers only, to
        // attack our territory rather than race us for neutral ground.
        UnitType want;
        if (rc.getRoundNum() <= 60) {
            want = UnitType.SOLDIER;                       // must capture some ruins first
        } else {
            want = (spawned % 2 == 0) ? UnitType.SPLASHER : UnitType.MOPPER;
        }"""
assert old in s, "live bot's spawn-mix line changed shape -- update refork-denier.sh"
p.write_text(s.replace(old, new))
print("denial spawn policy re-applied")
PY
cp src/bob_denier/README src/bob_denier.new/README
rm -rf src/bob_denier && mv src/bob_denier.new src/bob_denier
bob-tools/compile-check.sh bob_denier

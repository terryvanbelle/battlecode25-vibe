#!/usr/bin/env bash
# Regenerate src/carol_mirror as a byte-identical copy of src/carol (package renamed only).
# Run this before EVERY mirror match: a stale mirror silently stops being a mirror, which
# is the archetype-staleness failure the training algorithm warns about.
set -euo pipefail
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$WS/src/carol"
DST="$WS/src/carol_mirror"
rm -rf "$DST"; mkdir -p "$DST"
for f in "$SRC"/*.java; do
  sed 's/^package carol;/package carol_mirror;/' "$f" > "$DST/$(basename "$f")"
done
# Verify the only difference is the package line.
if diff <(sed '/^package /d' "$SRC"/*.java) <(sed '/^package /d' "$DST"/*.java) >/dev/null; then
  echo "carol_mirror synced (identical apart from package declaration)"
else
  echo "!! mirror differs beyond the package line -- refusing to claim it is a mirror" >&2
  exit 1
fi

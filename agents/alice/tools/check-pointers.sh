#!/usr/bin/env bash
# Verify every LEARNINGS.md index pointer actually resolves.
#
# Exits NON-ZERO if any pointer is dead. This matters: my first two attempts at
# this check printed a reassuring message unconditionally --
#   `diff a b | head -20 && echo IDENTICAL`   reads head's status, not diff's
#   `... | while read; do ...; done; echo OK`  reads the loop's last iteration
# A check that cannot fail is not a check (doctrine 19).
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
bad=0
while read -r p; do
  [ -n "$p" ] || continue
  grep -qF "$p" LEARNINGS_ARCHIVE.md && continue
  grep -qF "$p" TRAINING_LOG.md && continue
  echo "!! BROKEN POINTER: $p"; bad=$((bad+1))
done < <(grep -o -- '-> `"[^"]*"`\|-> log, `"[^"]*"`' LEARNINGS.md | sed 's/.*`"//; s/"`//' | sort -u)
if [ "$bad" -gt 0 ]; then echo "FAIL: $bad dead pointer(s)"; exit 1; fi
echo "OK: every pointer in LEARNINGS.md resolves"

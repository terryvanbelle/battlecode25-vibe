#!/usr/bin/env bash
# Fire iteration 12 (paint-tower upgrades) in one command, taking the correct branch.
#
# carol_i12 was forked from i7. Per the pre-registration in TRAINING_LOG.md:
#   - iteration 11 REJECTED -> i7 is still the baseline, carol_i12 is correct as-is.
#   - iteration 11 ACCEPTED -> baseline is i11; running carol_i12 as-is would measure
#     "add upgrades AND remove splashers" at once, the iteration-4 bundling error.
#     In that case carol_i12 must be REBUILT from src/carol (= i11) first.
# This script refuses to run the wrong one rather than letting a compiled candidate and a
# free slot make the shortcut tempting.
set -euo pipefail
cd "$(dirname "$0")/.."
VERDICT="${1:-}"; BASE="${2:-carol_iter7}"
case "$VERDICT" in
  reject) : ;;
  accept)
    echo "== iteration 11 accepted: rebuilding carol_i12 from src/carol (i11) =="
    python3 tools/rebuild-i12-from-current.py || { echo "!! rebuild failed"; exit 1; } ;;
  *) echo "usage: $0 {accept|reject} [baseline-snapshot]"; exit 2 ;;
esac
MAPS="$(tr '\n' ' ' < gauntlet/20260906-230220/maps.txt)" \
  BOT=carol_i12 OPPONENTS="$BASE carol_rush" MAXJOBS=3 ../../tools/gauntlet.sh

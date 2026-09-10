#!/usr/bin/env bash
# The RATCHET on the keep-biased census-fail rule.
#
#   tools/unconfirmed.sh            # check; exit 3 if a cumulative census is due
#   SELFTEST=1 tools/unconfirmed.sh # prove the failure branch runs
#
# WHY. "Keep if the census point estimate is >= 0 and no falsifier fired" says KEEP
# for nearly every unconfirmed positive result, and most results are that. Twenty
# applications give a HEAD that is an accumulation of individually-unconfirmed
# changes with no point at which the accumulation is tested -- a mechanism for
# manufacturing a plateau and hiding it. This makes the accumulation visible.
#
# N=3 is derived, not chosen: an unconfirmed change failed a +12 census, K3's came
# in at +5, so three of them reach ~+15 if additive -- the smallest count the
# existing instrument can detect.
#
# Invoked by tools/ac.sh whenever src/alice/ is in the commit, with NO pipe, so the
# gate reads this script's own exit status.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LEDGER="$HERE/../UNCONFIRMED.md"
N=3

[ -f "$LEDGER" ] || { echo "!! unconfirmed.sh: no UNCONFIRMED.md at $LEDGER" >&2; exit 2; }

PENDING="$(grep -c '^- \[ \]' "$LEDGER" || true)"
if [ "${SELFTEST:-0}" = "1" ]; then
  echo "unconfirmed.sh SELFTEST: forcing the ratchet to trip" >&2
  PENDING=$((N + 1))
fi

echo "unconfirmed changes standing in HEAD : $PENDING   (ratchet at $N)"
if [ "$PENDING" -ge "$N" ]; then
  cat >&2 <<MSG
!! RATCHET TRIPPED: $PENDING unconfirmed changes stand in HEAD (limit $N).
!! Each one is positive on its own evidence and NONE is established. Their
!! CUMULATIVE effect has never been measured, which is exactly how a plateau
!! hides. Before promoting anything further, run the accumulation against the
!! last confirmed snapshot: 75 maps / 150 games at the +12 bar.
!!   PASS -> mark the pending entries confirmed-in-aggregate and reset.
!!   FAIL -> revert newest-first until it passes.
!! Override with UNCONFIRMED_OK=1 only with a stated reason in TRAINING_LOG.md.
MSG
  [ "${UNCONFIRMED_OK:-0}" = "1" ] || exit 3
  echo "!! overridden by UNCONFIRMED_OK=1" >&2
fi
echo "OK: the unconfirmed accumulation is inside the ratchet."

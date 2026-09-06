#!/usr/bin/env bash
# Collate a gauntlet run that finished on battlecode-dev but whose driver-side
# poll loop did not survive to collate it (a killed session, a dropped SSH, a
# poll deadline hit while the detached runner kept going).
#
#   cd agents/alice
#   ../../tools/gauntlet-collect.sh                 # newest remote run for this workspace
#   ../../tools/gauntlet-collect.sh 20260906-203042 # a specific run
#   ../../tools/gauntlet-collect.sh --list          # what is on the VM, and whether it finished
#
# The remote runner is launched with setsid and is NOT tied to the driver
# session: when the driver dies mid-poll the games keep playing to completion.
# Re-running the gauntlet in that situation throws away finished matches and
# burns shared VM time, so recover the run instead. Output is the usual
# gauntlet/<run-id>/{results.csv,reasons.txt,summary.txt,losses/}; a run with no
# GAUNTLET-COMPLETE marker is still collated but labelled !! INCOMPLETE.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
source "$(dirname "${BASH_SOURCE[0]}")/collate.sh"

find_workspace
default_bot="$(basename "$WS_REL")"; [ "$default_bot" = arena ] && default_bot=examplefuncsplayer
BOT="${BOT:-$default_bot}"
ensure_vm
RDIR="$REMOTE_REPO/$WS_REL/gauntlet"

if [ "${1:-}" = --list ]; then
  gssh "for d in \$(ls -dt ~/$RDIR/*/ 2>/dev/null); do
          r=\$d/results.txt
          printf '%-18s %4s games  %s\n' \"\$(basename \$d)\" \
            \"\$(grep -c '^RESULT ' \$r 2>/dev/null || echo 0)\" \
            \"\$(grep -q GAUNTLET-COMPLETE \$r 2>/dev/null && echo complete || echo INCOMPLETE)\"
        done"
  exit 0
fi

RUN_ID="${1:-$(gssh "ls -t ~/$RDIR 2>/dev/null | head -1")}"
[ -n "$RUN_ID" ] || { echo "!! no runs under ~/$RDIR on $VM" >&2; exit 1; }
OUT="$WS_DIR/gauntlet/$RUN_ID"
mkdir -p "$OUT/losses"

gscp "$USER_NAME@$IP:$RDIR/$RUN_ID/results.txt" "$OUT/results.txt" >/dev/null \
  || { echo "!! no results.txt for run $RUN_ID on $VM" >&2; exit 1; }
# maps.txt is written driver-side at launch, so it is normally already here.
[ -f "$OUT/maps.txt" ] || gscp "$USER_NAME@$IP:$RDIR/$RUN_ID/maps.txt" "$OUT/maps.txt" >/dev/null 2>&1 || true

# Opponents in the order the runner played them (the outer loop), so a
# truncated run's summary lists the accept-gate opponent first, as launched.
OPPONENTS="$(awk '/^RESULT /{if(!($2 in s)){s[$2]=1; printf "%s ", $2}}' "$OUT/results.txt")"
[ -n "$OPPONENTS" ] || { echo "!! run $RUN_ID has no RESULT lines" >&2; exit 1; }
if [ -s "$OUT/maps.txt" ]; then SAMPLED=1; MAPTAG="$(wc -w < "$OUT/maps.txt" | tr -d ' ') sampled"
else SAMPLED=0; MAPTAG="$(awk '/^RESULT /{m[$3]=1} END{print length(m)}' "$OUT/results.txt") played"; fi

echo "collecting $RUN_ID  ws=$WS_REL bot=$BOT  opponents=[$OPPONENTS]"
collate_run
echo
echo "wrote $OUT/"

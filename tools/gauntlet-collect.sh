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
# maps.txt and maps.src are written driver-side at launch, so for a run launched
# from this checkout they are already here. (The remote never had them -- the map
# list is baked into the generated runner script -- so a fetch would fail; a run
# recovered in a fresh clone simply has no map list, which is reported as such
# rather than guessed at.)

# Opponents in the order the runner played them (the outer loop), so a
# truncated run's summary lists the accept-gate opponent first, as launched.
OPPONENTS="$(awk '/^RESULT /{if(!($2 in s)){s[$2]=1; printf "%s ", $2}}' "$OUT/results.txt")"
[ -n "$OPPONENTS" ] || { echo "!! run $RUN_ID has no RESULT lines" >&2; exit 1; }
# Provenance comes from maps.src, never from the presence of maps.txt. Inferring
# it was a real defect: a pinned run recovered after a session death was labelled
# "sampled ... random this run", which in the recovery path is the worst place for
# it -- that summary is read by someone deciding whether an exact repeat is still
# available, and it says the comparison cannot be repeated when it can. Reported
# by a lineage that hit it on its own pinned run. Runs launched before maps.src
# existed report the provenance as unrecorded instead of asserting either way.
# NOT $(wc -w < "$OUT/maps.txt" 2>/dev/null): the redirection failure is the
# SHELL's, not wc's, so 2>/dev/null cannot silence it and under `set -e` the
# failed assignment kills the script -- on the no-map-list path, which is the
# recovery case this whole script exists for.
NMAP=0
if [ -f "$OUT/maps.txt" ]; then NMAP="$(wc -w < "$OUT/maps.txt" | tr -d ' ')"; fi
case "$(cat "$OUT/maps.src" 2>/dev/null)" in
  sampled) SAMPLED=1; MAPTAG="$NMAP sampled" ;;
  pinned)  SAMPLED=0; MAPTAG="$NMAP pinned" ;;
  *) if [ -s "$OUT/maps.txt" ]; then SAMPLED=2; MAPTAG="$NMAP, provenance unrecorded"
     else SAMPLED=3; MAPTAG="$(awk '/^RESULT /{m[$3]=1} END{print length(m)}' "$OUT/results.txt") played"; fi ;;
esac

# Prefer what the run RECORDED about the build that played. $BOT defaulted to
# the WORKSPACE name (alice/bob/carol), which is never what played: a roster run
# tests a snapshot or a candidate, and bot.txt has held the right value all
# along. This is not merely a console cosmetic -- $BOT is also printed by
# collate_run into summary.txt, so a recovered run PERSISTED the workspace name
# as the build under test, misleading exactly the session-death recovery this
# script exists for. No number changes; the label does.
if [ -f "$OUT/bot.txt" ]; then
  lbl="$(sed -n 's/^label=//p' "$OUT/bot.txt" | head -1)"
  [ -n "$lbl" ] && BOT="$lbl"
fi
echo "collecting $RUN_ID  ws=$WS_REL bot=$BOT  opponents=[$OPPONENTS]"
collate_run
echo
echo "wrote $OUT/"

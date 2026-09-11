#!/usr/bin/env bash
# One line saying what the VM is doing right now, for the owner's benefit.
#
# The owner's point (2026-09-11): waiting on a run is fine, but from their side
# "waiting" and "doing nothing" look identical. This makes the difference visible
# without them having to ask.
set -uo pipefail
cd /home/terryvanbelle/projects/vibe/2025/agents/darla

# The LIVE run is the newest one with no summary.txt: a summary is written at
# collation, so its absence means still playing. `ls -t | head -1` was wrong --
# collation rewrites mtimes, so a just-finished run looks newest and the line
# named darla33 (long finished) while darla35 was actually playing.
run=$(for d in $(ls -1t gauntlet 2>/dev/null); do
        [ -f "gauntlet/$d/summary.txt" ] || { echo "$d"; break; }
      done)
prog=""
if [ -n "$run" ] && [ -f "gauntlet/$run/results.txt" ]; then
  # results.txt holds TWO lines per game (RESULT + REASON), so a raw line count
  # reads ~2.7x high -- it showed "414 games" for a 150-game run. Count RESULT
  # lines only. results.csv does not exist until collation, so it cannot be used
  # for a run that is still playing.
  done_n=$(grep -c '^RESULT ' "gauntlet/$run/results.txt" 2>/dev/null || true)
  # Total = maps x 2 sides x opponents. runner.sh is not kept in the run
  # directory, and summary.txt does not exist until collation, so derive it from
  # maps.txt (the only file present while a run is live).
  nmaps=$(grep -c . "gauntlet/$run/maps.txt" 2>/dev/null || true)
  nopp=$(awk '{print $2}' "gauntlet/$run/results.txt" 2>/dev/null | sort -u | grep -c . || true)
  [ "${nmaps:-0}" -gt 0 ] && [ "${nopp:-0}" -gt 0 ] && tot=$(( nmaps * 2 * nopp )) || tot=""
  bot=$(sed -n 's/^bot=//p' "gauntlet/$run/bot.txt" 2>/dev/null)
  if [ -n "$tot" ]; then prog="$bot ${done_n:-0}/$tot games"; else prog="$bot ${done_n:-0} games"; fi
fi

g=$(pgrep -fc '\.reexec-gauntlet\.sh' 2>/dev/null || true)
waiting=$(ps -eo args | grep -c '[t]ools/head-to-head.sh darla' || true)
q=$(grep -cvE '^\s*(#|$)' progress/pending-arms.txt 2>/dev/null || true)

if [ "${g:-0}" -gt 0 ]; then
  echo "RUNNING: ${prog:-$run} | ${g:-0} gauntlet(s) live, ${waiting:-0} head-to-head(s) queued behind, ${q:-0} arms pending"
else
  echo "IDLE: nothing running. ${waiting:-0} head-to-head(s) waiting, ${q:-0} arms pending"
fi

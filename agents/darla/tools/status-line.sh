#!/usr/bin/env bash
# One line saying what the VM is doing right now, for the owner's benefit.
#
# The owner's point (2026-09-11): waiting on a run is fine, but from their side
# "waiting" and "doing nothing" look identical. This makes the difference visible
# without them having to ask.
set -uo pipefail
cd /home/terryvanbelle/projects/vibe/2025/agents/darla

run=$(ls -1t gauntlet 2>/dev/null | head -1)
prog=""
if [ -n "$run" ] && [ -f "gauntlet/$run/results.txt" ]; then
  done_n=$(grep -c . "gauntlet/$run/results.txt" 2>/dev/null || true)
  tot=$(sed -n 's/.*games=\([0-9]*\).*/\1/p' "gauntlet/$run/summary.txt" 2>/dev/null | head -1)
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

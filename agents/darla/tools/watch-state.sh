#!/usr/bin/env bash
# State-based watcher. Emits one line per NEW completed run, whatever produced it.
#
# WHY THIS REPLACES TAILING LOG FILES. Every previous watcher named the logs it
# watched, and every one went blind the moment the system grew a new producer:
# the monitor tailed arm-runner + idle-filler and missed head-to-heads entirely
# (two results sat unread for 73 minutes on 2026-09-11); the obvious patch --
# adding /tmp/darla-h2h-*.log -- is the SAME bug, because `tail -F` expands a
# glob once at startup and never sees a log created afterwards.
#
# So this does not watch logs at all. It scans the actual artefact -- a run
# directory with a summary.txt -- and reports anything it has not reported
# before. A new kind of producer is covered automatically, because every producer
# ends by writing a summary.
set -uo pipefail
cd /home/terryvanbelle/projects/vibe/2025/agents/darla
SEEN=/tmp/darla-seen-runs.txt
touch "$SEEN"

# Do not replay history on first start.
if [ ! -s "$SEEN" ]; then
  for d in gauntlet/*/; do [ -f "$d/summary.txt" ] && basename "$d" >> "$SEEN"; done
fi

while true; do
  for d in gauntlet/*/; do
    [ -f "$d/summary.txt" ] || continue
    # Wait for the overall line. summary.txt appears before collation finishes
    # writing it, so reporting on the file's existence alone announces a result
    # with no score -- which happened for 20260911-214415.
    grep -q '^overall' "$d/summary.txt" || continue
    run=$(basename "$d")
    grep -qx "$run" "$SEEN" && continue
    bot=$(sed -n 's/^bot=//p' "$d/bot.txt" 2>/dev/null)
    opp=$(sed -n 's/^  opponents=\[\(.*\)\].*/\1/p' "$d/summary.txt" 2>/dev/null | head -1)
    res=$(grep -m1 -E '^overall' "$d/summary.txt")
    echo "RESULT $run  bot=${bot:-?}  $res"
    echo "$run" >> "$SEEN"
  done

  q=$(grep -cvE '^\s*(#|$)' progress/pending-arms.txt 2>/dev/null || true)
  g=$(pgrep -fc '\.reexec-gauntlet\.sh' 2>/dev/null || true)
  h=$(pgrep -fc 'head-to-head\.sh|replicate\.sh' 2>/dev/null || true)
  if [ "${q:-0}" -eq 0 ] && [ "${g:-0}" -eq 0 ] && [ "${h:-0}" -eq 0 ]; then
    echo "IDLE  nothing queued, nothing running, nothing waiting -- the VM has no work"
    sleep 300
  fi
  sleep 60
done

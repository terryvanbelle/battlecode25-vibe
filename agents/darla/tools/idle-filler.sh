#!/usr/bin/env bash
# Darla's idle filler. The guarantee: the VM is never idle overnight.
#
# tools/arm-runner.sh drains progress/pending-arms.txt and then WAITS for a
# human to add another arm. That wait is the failure mode -- if the session is
# asleep when the last arm lands, the machine sits doing nothing until someone
# notices. This daemon removes that dependency.
#
# When the pending queue is empty and no gauntlet is in flight, it runs the
# standing fallback job: a FRESH RANDOM 25-map sample of the shipped baseline
# against the three frozen lineages, recorded into progress/vs_old_bots_history.csv.
#
# That job is never wasted work, which is what makes it safe to run unattended:
#   * fresh random maps each time, so it is not an overfitting surface (the
#     pinned samples are for matched pairs; this is for absolute strength);
#   * the opponents are frozen, so a moving line is real change, not a moving
#     instrument -- which is exactly what vs_old_bots.png is for;
#   * it extends a time series that currently has ONE date on it.
# It never touches src/, never commits, and cannot change what plays anywhere.
set -uo pipefail
WS=/home/terryvanbelle/projects/vibe/2025/agents/darla
VENV=/home/terryvanbelle/projects/vibe/2025/tools/.venv/bin/python3
cd "$WS"

exec 9>/tmp/darla-idle-filler.lock
flock -n 9 || { echo "$(date -uIs) filler already running; exiting"; exit 0; }

while true; do
  pending=$(grep -cvE '^\s*(#|$)' progress/pending-arms.txt 2>/dev/null || echo 0)
  # See the note in arm-runner.sh: match the re-exec name, never the original.
  inflight=$(pgrep -fc '\.reexec-gauntlet\.sh' 2>/dev/null || echo 0)

  if [ "$pending" -gt 0 ] || [ "$inflight" -gt 0 ]; then
    sleep 120                      # real work is happening; stay out of the way
    continue
  fi

  echo "$(date -uIs) FILLER START -- queue empty, running a fresh-sample baseline gauntlet"
  NMAPS=25 BOT=darla OPPONENTS="carol bob alice" MAXJOBS=2 \
    ../../tools/gauntlet.sh || { echo "$(date -uIs) FILLER ERROR -- gauntlet failed"; sleep 300; continue; }

  run=$(ls -1t gauntlet | head -1)
  "$VENV" ../../tools/track_vs_old_bots.py "gauntlet/$run" >/dev/null 2>&1 \
    && "$VENV" ../../tools/plot_vs_old_bots.py >/dev/null 2>&1 \
    && echo "$(date -uIs) FILLER COMPLETE $run -- vs_old_bots chart extended" \
    || echo "$(date -uIs) FILLER WARN $run -- games kept, charting failed"
done

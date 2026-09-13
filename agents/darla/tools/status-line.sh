#!/usr/bin/env bash
# One line saying what the VM is doing right now, for the owner's benefit.
#
# The owner's point (2026-09-11): waiting on a run is fine, but from their side
# "waiting" and "doing nothing" look identical. This makes the difference visible
# without them having to ask.
set -uo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/jobs.sh"
cd /home/terryvanbelle/projects/vibe/2025/agents/darla

# The LIVE run is the newest one with no summary.txt: a summary is written at
# collation, so its absence means still playing. `ls -t | head -1` was wrong --
# collation rewrites mtimes, so a just-finished run looks newest and the line
# named darla33 (long finished) while darla35 was actually playing.
# 2026-09-12: mtime order was still wrong in the other direction. Five run dirs
# from the 09-11 outage have no summary.txt and no results.txt -- they are 0-game
# orphans -- and whenever the genuinely live run had not yet written results.txt,
# this loop fell through to one of them and reported "darla25 0 games (2111m in)",
# a 35-hour-old ghost. Directory names ARE timestamps, so sort by NAME, which no
# amount of collation can rewrite, and skip a dir that has neither summary nor
# results and is older than 15 minutes: that combination is only ever an orphan.
run=$(now=$(date +%s); for d in $(ls -1 gauntlet 2>/dev/null | sort -r); do
        [ -f "gauntlet/$d/summary.txt" ] && continue
        # Skip orphans by WRITE FRESHNESS, not by whether results.txt exists. The
        # first version of this check skipped a dir only when results.txt was
        # absent, and gauntlet/20260910-200447 -- an abandoned run with an EMPTY
        # results.txt -- sailed through it and was reported as "darla 0 games
        # (3230m in)", a 54-hour-old ghost, whenever the genuinely live run had
        # not yet created its directory. A live run touches results.txt
        # continuously, including a 450-game one that will not write summary.txt
        # for 40 minutes, so the newest write in the directory is the signal that
        # separates "still playing" from "abandoned".
        m=$(stat -c %Y "gauntlet/$d" 2>/dev/null || echo 0)
        r=$(stat -c %Y "gauntlet/$d/results.txt" 2>/dev/null || echo 0)
        [ "$r" -gt "$m" ] && m="$r"
        [ $(( now - m )) -gt 900 ] && continue
        echo "$d"; break
      done)
prog=""
# Show elapsed time always, and 0 games explicitly. A blank count on a run that
# has not yet written results.txt looks identical to a stalled reader, and cost
# two false investigations.
age=""
[ -n "$run" ] && age=" ($(( ($(date +%s) - $(stat -c %Y "gauntlet/$run" 2>/dev/null || date +%s)) / 60 ))m in)"
if [ -n "$run" ]; then
  # results.txt holds TWO lines per game (RESULT + REASON), so a raw line count
  # reads ~2.7x high -- it showed "414 games" for a 150-game run. Count RESULT
  # lines only. results.csv does not exist until collation, so it cannot be used
  # for a run that is still playing.
  done_n=$(grep -c '^RESULT ' "gauntlet/$run/results.txt" 2>/dev/null || true); done_n=${done_n:-0}
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
# Count EVERY evaluation job, not a hardcoded list of one. New job types have
# been added twice (replicate.sh, then darla-largemap.sh) and each time this
# line under-reported the queue until it was noticed by hand -- the same
# 'watcher does not know about a new producer' shape as the monitor and
# vm-prune bugs. Match the shared suffix instead.
waiting=$(ps -eo args | grep -cE "$EVAL_JOB_RE" || true)
q=$(grep -cvE '^\s*(#|$)' progress/pending-arms.txt 2>/dev/null || true)

if [ "${g:-0}" -gt 0 ]; then
  echo "RUNNING: ${prog:-$run}${age} | ${g:-0} gauntlet(s) live, ${waiting:-0} head-to-head(s) in queue (incl. live), ${q:-0} arms pending"
else
  # A queued head-to-head polls every 60s, so a handover between runs shows as a
  # brief no-gauntlet window. That is WAITING, not IDLE -- work exists and will
  # start on its own. Only report IDLE when there is genuinely nothing to run,
  # because the heartbeat treats IDLE as a failure to fix.
  if [ "${waiting:-0}" -gt 0 ] || [ "${q:-0}" -gt 0 ]; then
    echo "WAITING: between runs. ${waiting:-0} head-to-head(s) queued, ${q:-0} arms pending -- starts within 60s"
  else
    echo "IDLE: nothing running, nothing queued -- the VM has no work"
  fi
fi

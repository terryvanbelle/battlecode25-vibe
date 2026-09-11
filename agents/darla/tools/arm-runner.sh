#!/usr/bin/env bash
# Darla's standing arm runner. Drains progress/pending-arms.txt forever.
#
# THE POINT: adding a line to pending-arms.txt starts a gauntlet with no session
# involved. The VM never idles while an arm is pending, and nothing is lost if
# the Claude session dies -- this is setsid-detached and holds a flock, so a
# second launch is a no-op rather than a double-run.
#
# Each arm is run on BOTH pinned 12-map samples, so every result is a matched
# pair against the darla1 baseline of 89/144 on exactly the same ground.
# An arm is skipped if it already has 144 collated games: re-running a finished
# arm discards real games and pays for shared VM time twice.
set -uo pipefail
WS=/home/terryvanbelle/projects/vibe/2025/agents/darla
cd "$WS"
PENDING=progress/pending-arms.txt
SAMPLES="20260910-213703 20260910-213919"

exec 9>/tmp/darla-arm-runner.lock
flock -n 9 || { echo "$(date -uIs) runner already holds the lock; exiting"; exit 0; }

played () {   # total collated games for an arm, across all runs
  local arm=$1 tot=0 n
  for d in gauntlet/*/; do
    [ -f "$d/bot.txt" ] && [ -f "$d/summary.txt" ] || continue
    grep -qx "bot=$arm" "$d/bot.txt" || continue
    n=$(sed -n 's/^overall: [0-9]*\/\([0-9]*\) wins.*/\1/p' "$d/summary.txt")
    tot=$(( tot + ${n:-0} ))
  done
  echo "$tot"
}

idle_announced=0
while true; do
  arm=$(grep -vE '^\s*(#|$)' "$PENDING" 2>/dev/null | head -1)

  if [ -z "$arm" ]; then
    [ "$idle_announced" -eq 0 ] && {
      echo "$(date -uIs) QUEUE IDLE -- pending-arms.txt is empty, nothing to run"
      idle_announced=1
    }
    sleep 180
    continue
  fi
  idle_announced=0

  if [ ! -d "src/$arm" ]; then
    echo "$(date -uIs) ARM ERROR $arm -- no src/$arm, dropping it from the queue"
    sed -i "0,/^\s*$arm\s*$/{/^\s*$arm\s*$/d}" "$PENDING"
    continue
  fi

  have=$(played "$arm")
  if [ "$have" -ge 144 ]; then
    echo "$(date -uIs) ARM SKIP $arm -- already has $have collated games"
    sed -i "0,/^\s*$arm\s*$/{/^\s*$arm\s*$/d}" "$PENDING"
    continue
  fi

  # Wait out any gauntlet launched OUTSIDE this runner for the same workspace.
  # gauntlet.sh warns about a concurrent run per workspace and then proceeds;
  # the warning exists to catch a second session forking the ledger, and a
  # standing runner should never be the thing that trips it. Checked here,
  # before ARM START, so the runner's own child can never match.
  # Detect an in-flight gauntlet by its RE-EXEC name, not by 'tools/gauntlet.sh'.
  # gauntlet.sh copies itself to tools/.reexec-gauntlet.sh.<pid> and exec's that
  # (so editing the original cannot corrupt a run in flight), which means the
  # original path never appears in any running process's cmdline and a pgrep for
  # it silently matches NOTHING. This checker was written that way first and was
  # blind: the runner and the filler both launched into a gauntlet that was
  # already going, and the workspace-concurrency warning fired.
  while pgrep -f '\.reexec-gauntlet\.sh' > /dev/null; do sleep 60; done

  echo "$(date -uIs) ARM START $arm ($have/144 games so far)"
  for r in $SAMPLES; do
    BOT="$arm" OPPONENTS="carol bob alice" MAXJOBS=2 \
      MAPS="$(cat gauntlet/$r/maps.txt)" ../../tools/gauntlet.sh \
      || echo "$(date -uIs) ARM ERROR $arm -- gauntlet failed on sample $r"
  done
  # Only retire an arm that actually PRODUCED games. The first version removed it
  # from the queue unconditionally, so when the VM filled up and every gauntlet
  # died on ENOSPC in under a second, the runner spun through the entire queue in
  # four seconds marking each arm "COMPLETE -- 0/144 games collated". A failure
  # must not look like a result, and must not consume the work item.
  have_now=$(played "$arm")
  if [ "$have_now" -ge 144 ]; then
    echo "$(date -uIs) ARM COMPLETE $arm -- $have_now/144 games collated"
    sed -i "0,/^\s*$arm\s*$/{/^\s*$arm\s*$/d}" "$PENDING"
  else
    echo "$(date -uIs) ARM INCOMPLETE $arm -- only $have_now/144; LEAVING IT QUEUED and backing off 5m"
    sleep 300
  fi
done

#!/usr/bin/env bash
# Keep the driver's root filesystem from filling while the arm queue runs.
#
# WHY THIS EXISTS: the "never idle" arrangement (arm-runner + idle-filler) turns
# gauntlet runs over far faster than the project used to, and each run writes its
# lost games to gauntlet/<run>/losses/*.bc25 -- roughly 40-70MB a run. The hourly
# bc25-driver-prune timer keeps the newest 2 runs per workspace and never touches
# a file under an hour old, which was sized for a slower loop. At the current rate
# the disk reached 100% and a git commit failed with ENOSPC mid-session.
#
# This runs the SAME sanctioned tool, just more often and with tighter knobs, and
# only when space is actually short. It never deletes anything the tool would not:
# gauntlet and matches replay blobs only, never agents/*/replays/ (which is
# curated and git-TRACKED -- 34 replays live there as committed evidence).
#
# It does NOT touch /Users/terryvanbelle/projects/vibe_bc26, which holds 18G of
# the archived BC26 project's replays and is the actual reason the disk is full.
# That is another project's recorded results; deleting it is the owner's call and
# has been put to them.
set -uo pipefail
REPO=/home/terryvanbelle/projects/vibe/2025
cd "$REPO"

exec 9>/tmp/darla-disk-guard.lock
flock -n 9 || exit 0

LOW_MB="${LOW_MB:-1200}"      # act below this much free
while true; do
  free_mb=$(df -Pm / | awk 'NR==2 {print $4}')
  if [ "${free_mb:-0}" -lt "$LOW_MB" ]; then
    echo "$(date -uIs) DISK LOW ${free_mb}MB free -- pruning"
    # TWO STAGE. The first version pruned at KEEP_RUNS=1 MIN_AGE_MIN=20 on every
    # pass, and since free space is permanently under LOW_MB (the 18G of archived
    # BC26 replays sees to that) it ran every 10 minutes and destroyed replays
    # almost as fast as they were written. It deleted the darla15 control replay
    # six minutes before that control was needed to interpret darla17, and the
    # comparison had to be regenerated. Replays are the only mechanism evidence
    # this project has; prune them as a last resort, not as a routine.
    KEEP_RUNS=2 MIN_AGE_MIN=45 timeout 300 tools/driver-prune.sh 2>&1 | tail -2
    if [ "$(df -Pm / | awk 'NR==2 {print $4}')" -lt 500 ]; then
      echo "$(date -uIs) DISK still tight after gentle prune -- escalating"
      KEEP_RUNS=1 MIN_AGE_MIN=20 timeout 300 tools/driver-prune.sh 2>&1 | tail -2
    fi
    echo "$(date -uIs) DISK after prune: $(df -Pm / | awk 'NR==2 {print $4}')MB free"
    # THE VM HAS ITS OWN, SMALLER DISK (20G against the driver's 30G) and it fills
    # FIRST: every gauntlet writes ALL of its replays there while only the losses
    # are pulled down. On 2026-09-11 it hit 100% and three arms died on ENOSPC
    # inside four seconds. A driver-side prune does nothing for that, so prune both.
    KEEP=3 GRACE_H=2 timeout 300 "$REPO/tools/vm-prune.sh" >/dev/null 2>&1 || true

    # Still short after pruning everything we own: say so loudly rather than
    # silently letting the next gauntlet die on ENOSPC.
    now=$(df -Pm / | awk 'NR==2 {print $4}')
    [ "$now" -lt 400 ] && echo "$(date -uIs) DISK CRITICAL ${now}MB free after pruning our own replays -- the 18G under projects/vibe_bc26 is the remaining cause and needs the owner's decision"
  fi
  sleep 600
done

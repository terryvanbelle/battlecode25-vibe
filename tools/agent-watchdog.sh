#!/usr/bin/env bash
# Outside-the-session watchdog for the BC25 agents.
#
# WHY THIS EXISTS, AND WHY IT IS NOT A SECOND COORDINATOR
# ------------------------------------------------------
# The coordinator session restarts dead agents itself, on a self-scheduled loop.
# That is enough for every failure EXCEPT the one that matters most: an account
# usage limit pauses the coordinator too. Its scheduled wake-up then fires into
# a 429, the turn dies before it can re-arm, and the loop that was supposed to
# recover from the limit is itself killed by it. The recovery therefore has to
# live outside the session -- in systemd, which retries forever and needs no
# quota.
#
# It does NOT start a rival Claude session. Two coordinators would each spawn
# three agents into one working tree, which is exactly the race MULTI_AGENT.md's
# git rules forbid. Instead it types a message into the coordinator's existing
# tmux session. That works in every case that matters:
#
#   * coordinator paused by the limit -> the keystrokes QUEUE, and are processed
#     the instant the window clears. Nothing is lost and nothing races.
#   * coordinator alive and healthy   -> its heartbeat is fresh, so no nudge is
#     sent at all.
#   * tmux session gone entirely      -> recreated here, exactly as ~/bc25 does,
#     and then nudged.
#
# Liveness signal is a heartbeat file the coordinator touches each loop tick.
# A heartbeat is used rather than "are there agent commits recently?" because an
# agent can legitimately spend half an hour tracing a replay without committing,
# and a false positive here costs duplicate agents.
set -uo pipefail

SESSION=bc25
REPO=/home/terryvanbelle/projects/vibe/2025
HEARTBEAT="$HOME/.bc25-coordinator-heartbeat"
NUDGED="$HOME/.bc25-watchdog-last-nudge"
LOCKFILE="$HOME/.bc25-watchdog.lock"
STALE_MIN="${STALE_MIN:-30}"        # heartbeat older than this = coordinator not working
COOLDOWN_MIN="${COOLDOWN_MIN:-15}"  # never nudge more often than this
DRY_RUN="${DRY_RUN:-0}"

log () { echo "$(date -u +%FT%TZ) watchdog: $*"; }

# One watchdog at a time; a slow nudge must not overlap the next timer firing.
exec 9>"$LOCKFILE"
flock -n 9 || { log "another run holds the lock; exiting"; exit 0; }

age_min () {  # <file> -> age in whole minutes, or a huge number if absent
  [ -f "$1" ] || { echo 999999; return; }
  echo $(( ( $(date +%s) - $(stat -c %Y "$1") ) / 60 ))
}

# Close the sibling-transcript leak before anything else. This runs on EVERY
# tick, above the healthy-coordinator early exit below, because the leak is
# widest exactly when the coordinator IS healthy and relaunching agents -- each
# launch recreates the symlink this removes. See tools/isolation-sweep.sh.
"$REPO/tools/isolation-sweep.sh" || log "isolation sweep failed (continuing)"

hb_age=$(age_min "$HEARTBEAT")
if [ "$hb_age" -lt "$STALE_MIN" ]; then
  log "coordinator heartbeat ${hb_age}m old (< ${STALE_MIN}m) -- healthy, nothing to do"
  exit 0
fi
log "coordinator heartbeat ${hb_age}m old (>= ${STALE_MIN}m) -- not working"

nudge_age=$(age_min "$NUDGED")
if [ "$nudge_age" -lt "$COOLDOWN_MIN" ]; then
  log "already nudged ${nudge_age}m ago (< ${COOLDOWN_MIN}m cooldown); waiting"
  exit 0
fi

# The message the coordinator will act on. Kept short and unambiguous: it lands
# as ordinary input, possibly hours later, so it must make sense with no memory
# of why it arrived.
MSG="Watchdog: your heartbeat is ${hb_age} minutes stale, so the agents are probably not running. Check ListAgents and restart any of alice/bob/carol that is missing, using tools/agent-prompts/<name>.md as the prompt. Do not launch one that is already running. Then touch ~/.bc25-coordinator-heartbeat and re-arm your watchdog loop."

if [ "$DRY_RUN" = 1 ]; then
  log "DRY_RUN: would ensure session '$SESSION' and send:"
  log "  $MSG"
  exit 0
fi

if ! tmux has-session -t "$SESSION" 2>/dev/null; then
  log "tmux session '$SESSION' is gone -- recreating it"
  cd "$REPO" || exit 1
  tmux new-session -d -s "$SESSION" "claude --dangerously-skip-permissions"
  sleep 20        # let the CLI reach its prompt before typing at it
fi

# -l sends the text literally (no key-name interpretation), then Enter submits.
tmux send-keys -t "$SESSION" -l "$MSG"
tmux send-keys -t "$SESSION" Enter
date +%s > "$NUDGED"
log "nudged session '$SESSION'"

# Cross-runner counting semaphore for battlecode-dev. Injected verbatim into the
# remote scripts of gauntlet.sh, tournament.sh and vm-match.sh -- every path that
# starts a game must take a slot, or the cap it enforces is a fiction.
#
# NOT sourced locally: the callers inline it with $(cat) inside their remote
# heredoc, so the $VARs below stay literal and are resolved on the VM. Keep it
# free of backticks and $(...) that the driver should not run -- an unquoted
# heredoc executes those at generation time (that bug printed "pgrep: no
# matching criteria specified" on every launch for a day).
#
# Expects GLOBAL_CAP and HARD_CAP to be set by the caller.
SLOTDIR=$HOME/.bc25-slots; mkdir -p "$SLOTDIR"

acquire_slot () {   # sets SFD; the slot is held until the caller's subshell exits
  # Stand in ONE line, so the HARD_CAP check below and the slot-taking that
  # follows it cannot be interleaved by another runner. GLOBAL_CAP is enforced
  # by the slot flocks and was never the leak; HARD_CAP is a pgrep count, so
  # under the old code two runners could both read "6 < 7" before either
  # started a game and the machine ended up at 8 -- observed on 2026-09-06, and
  # reproduced by tools/semaphore-test.sh (peak 8 ungated, 7 gated).
  # The kernel drops the gate on fd close, so a runner that dies holding it
  # cannot wedge the box, and a gate holder only ever waits on a condition no
  # other runner could have passed either.
  exec {GFD}>"$SLOTDIR/gate"
  flock $GFD
  # Politeness toward the BC26 project, which runs its own games outside this
  # semaphore: never push the machine-wide game count past HARD_CAP.
  while [ "$(pgrep -fc battlecode.server.Main || true)" -ge $HARD_CAP ]; do sleep 10; done
  while true; do
    for i in $(seq 1 $GLOBAL_CAP); do
      exec {SFD}>"$SLOTDIR/slot.$i"
      flock -n $SFD && { exec {GFD}>&-; return 0; }   # hold slot, leave the line
      exec {SFD}>&-
    done
    sleep 5
  done
}

# ONE definition of "an evaluation job", sourced by every script that needs it.
#
# This pattern was hardcoded separately in idle-filler.sh (yield), watch-state.sh
# (idle detection) and status-line.sh (queue count). Each copy named the job types
# that existed when it was written, and each went stale the moment a new type was
# added -- darla-largemap.sh was starved by the filler and then reported as "not
# waiting" by the watcher, producing a false IDLE while a job sat in its poll loop.
# Five instances of the same shape tonight across these scripts, vm-prune's agent
# roster and the monitor's log list.
#
# The contract: any script under agents/darla/tools (or /tmp) that runs games and
# should hold off the idle filler. Add new job types HERE and nowhere else.
EVAL_JOB_RE='head-to-head\.sh|replicate\.sh|darla-largemap\.sh'

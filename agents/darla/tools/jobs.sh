# ONE definition of "an evaluation job", sourced by every script that needs it.
# Add new job types HERE and nowhere else -- five separate hardcoded copies of
# this pattern went stale on 2026-09-11/12 as new job types were added.
#
# 2026-09-12: paired-roster.sh was added and NOT registered here, which is the
# same failure a seventh time. status-line reported "0 head-to-head(s) in queue"
# while two paired runs were waiting, and the idle-filler would not have yielded
# to them. The pattern now matches any script in tools/ whose name is one of the
# known evaluation drivers, and the assertion below fails loudly if a driver
# exists on disk that the pattern does not match -- so the next unregistered job
# type is caught by the next script that sources this file, not by a wrong status
# line hours later.
EVAL_JOB_RE='widen\.sh|head-to-head\.sh|replicate\.sh|paired-roster\.sh|darla-largemap\.sh|darla-band\.sh|darla-vs\.sh|darla-fresh\.sh'

# Self-check: every executable driver in tools/ that launches a gauntlet must be
# matched. Prints to stderr and does not exit, so a stale pattern degrades to a
# warning rather than breaking a running daemon.
_jobs_self_check() {
    local d="$(dirname "${BASH_SOURCE[0]}")" f b
    for f in "$d"/*.sh; do
        b="$(basename "$f")"
        case "$b" in jobs.sh|make-arm.sh|status-line.sh|watch-state.sh|disk-guard.sh|arm-runner.sh|idle-filler.sh) continue;; esac
        grep -q 'gauntlet\.sh' "$f" 2>/dev/null || continue
        printf '%s\n' "$b" | grep -qE "^($EVAL_JOB_RE)$" \
            || echo "jobs.sh WARNING: $b launches a gauntlet but is not in EVAL_JOB_RE" >&2
    done
}
_jobs_self_check

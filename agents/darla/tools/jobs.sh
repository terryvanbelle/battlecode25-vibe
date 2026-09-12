# ONE definition of "an evaluation job", sourced by every script that needs it.
# Add new job types HERE and nowhere else -- five separate hardcoded copies of
# this pattern went stale on 2026-09-11/12 as new job types were added.
EVAL_JOB_RE='head-to-head\.sh|replicate\.sh|darla-largemap\.sh|darla-band\.sh|darla-vs\.sh|darla-fresh\.sh'

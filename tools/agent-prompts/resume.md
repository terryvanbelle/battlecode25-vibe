Continue your development loop.

You are being resumed, not restarted: your own context is intact, so do **not**
re-read your charter, TRAINING_ALGORITHM.md, MULTI_AGENT.md, METHODS.md,
LEARNINGS.md or RULES.md. You already have them. Re-reading them is the single
largest avoidable cost in this project — measured at ~77k tokens per cold start,
20–50% of a session's entire budget — and it buys nothing when you have not lost
context.

Re-establish only what can have CHANGED while you were writing your report:

- any run you left in flight (`../../tools/gauntlet-collect.sh --list` from your
  workspace, or a scoped `pgrep -f "<your-run-id>"`), and collate anything that
  finished — never re-run a completed run;
- `git status --short agents/<you>` if you were mid-commit;
- `ls -t tournaments/` only if a tournament was due to land.

Then carry on from the plan you already have: the next iteration, the pending
verdict, the analysis you had queued. If your last report named a resume point,
that is where you start.

Two standing reminders, because they are cheap and a lapse is expensive:
your accept/reject is whatever you pre-registered, and a rejected iteration is a
delivered result. Report what you did, what you measured, and what you concluded.

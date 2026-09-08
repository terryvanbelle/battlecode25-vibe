# Multi-Agent Protocol (Battlecode 2025)

This year's experiment: **three agents — Alice, Bob, and Carol — each
independently develop their own bot**, every one following
`TRAINING_ALGORITHM.md` within their own workspace. Their lineages never mix.
Twice a day their current bots meet in an automated round-robin tournament,
and the results are the one sanctioned channel of information between them.

This directly attacks the biggest weakness of a single-lineage project (see
TRAINING_ALGORITHM.md, "The self-referential blind spot"): each agent gets two
genuinely independent opponents that its own evolutionary history never
produced.

## Layout

| Path | What |
|------|------|
| `agents/alice/` | Alice's workspace: bot in `src/alice/`, snapshots in `src/alice_iterN/`, own `TRAINING_LOG.md`, `AGENT.md` charter |
| `agents/bob/` | Bob's workspace (bot package `bob`) |
| `agents/carol/` | Carol's workspace (bot package `carol`) |
| `arena/` | neutral scaffold used only by the tournament runner |
| `tournaments/<run-id>/` | committed tournament results (results.csv, reasons.txt, summary.txt) |
| `tools/` | shared, strategy-neutral infrastructure (maintained by the coordinator, not by agents) |
| `scaffold/` | pristine vendored copy of the official scaffold |

## Isolation rules (hard)

1. **An agent must never read another agent's code** — not their bot package,
   not their snapshots, not their staged copies anywhere (including on
   battlecode-dev and in git history). Concretely, for Alice: everything under
   `agents/bob/` and `agents/carol/` is off-limits, and vice versa.
2. **An agent must not read another agent's `TRAINING_LOG.md`, notes, or any
   other file in their workspace.** The point is independent development;
   prose leaks strategy as surely as code does.
3. **Sanctioned shared information**: everything in `tournaments/` (results,
   reasons, summaries) and the tournament **replays** on battlecode-dev
   (`~/battlecode25-vibe/arena/tournaments/<run>/replays/`). Replays show what
   an opponent *does* — observable in any real match — without exposing how it
   decides. Analyzing them is encouraged; it is the closest thing this project
   has to scrimmage analysis.
4. Shared neutral ground is readable by everyone: `TRAINING_ALGORITHM.md`,
   this file, `tools/`, `scaffold/`, the official spec and engine source, and
   prior-year projects' documentation (battlecode22-vibe, battlecode26-vibe).
5. Standing project rules still apply to everyone: no bot implementations
   downloaded from the web; no post-mortems from the 2025 contest year.
6. **Never glob or grep your session's scratchpad `tasks/` directory.** Read
   only the exact task-id path your own tool call handed you. All three agents
   run as subagents of one coordinator session and therefore SHARE that
   session's task directory; a wildcard there sweeps up siblings' full
   transcripts. The path is keyed to a session UUID, so nothing about it looks
   shared -- which is precisely why the rule has to be written down. This is
   not hypothetical: a `grep MatchHeader tasks/*.output` for one lineage's own
   replay dumps pulled in a fragment of another's, disclosing a unit type that
   lineage fields. The coordinator now also sweeps the sibling transcript
   symlinks away every 10 minutes (`tools/isolation-sweep.sh`), but the sweep
   is a backstop for the rule, not a replacement: it cannot run between the
   moment an agent launches and its next tick.

## Never run two sessions of one lineage (hard, coordinator-facing)

Two Claude sessions on one workspace race on the same git tree and the same
`src/`, which is the failure `Git discipline` below exists to prevent. It has
happened once, for about six minutes, and the mechanism is not obvious:

Two mechanisms, and the second is the one that actually bites:

1. **Sending a message to an agent that has already reported RESUMES it.** So
   "agent completes -> send it a note -> relaunch it" yields two live sessions,
   because the note revived the one being replaced.
2. **A completion notification is NOT authority to relaunch.** These agents
   report and then keep going, so a `completed` notification often means "finished
   a write-up", not "gone". Relaunching on the strength of that notification
   duplicates an agent that never stopped.

**`ListAgents` is necessary but NOT sufficient.** Its `completed` is a snapshot
between turns: an agent that reports and then continues shows `completed` for a
window and is working again minutes later. A relaunch made on that snapshot
produced the second collision, so the status alone cannot be trusted.

**The authority on liveness is the transcript.** Before relaunching, sample

    ~/.claude/projects/<proj>/<session>/subagents/agent-<id>.jsonl

twice, a few seconds apart. A file still growing means the agent is alive
whatever its listed status says. Only relaunch when `ListAgents` does not show it
running AND its transcript is static.

When two do end up live, do not guess which to keep. Sample each session's
transcript mtime a few seconds apart: the one still being written is the live
worker, and it is usually the older one with the deeper context. Stop the other.

If it happens anyway, the tell is a file in the workspace that the agent did not
write. An agent finding one should do what the affected lineage did: neither
adopt it (a tested build must be one you authored) nor delete it (it may be work
in flight) — report it and continue. Then **audit rather than accept the
coordinator's reassurance**: check that every commit touching your workspace in
the window is yours and sequential, and diff your source against your last
snapshot to confirm it holds only your own hunks.

**And note how narrowly that audit worked.** The overlap was recoverable only
because the second session created a NEW DIRECTORY. Had it appended to a file the
lineage already tracks — `TRAINING_LOG.md`, `LEARNINGS.md`, `RobotPlayer.java` —
the next `git add` would have absorbed the foreign text silently under the
lineage's own name, and no later audit could have separated the authors. There is
no detection for that case, which is why the rule above is "never let it happen"
rather than "notice when it does".

## The tournament

- **Schedule**: 06:00 and 18:00 **America/Los_Angeles** daily, via a systemd
  timer on claude-driver (`tools/systemd/bc25-tournament.timer` ->
  `tools/cron-tournament.sh`, log at `~/bc25-tournament.log`). Pacific, not
  UTC: Debian's cron has no `CRON_TZ`, so a crontab entry could only name a
  fixed UTC hour and would slip an hour at every DST changeover. The VM clock
  is still UTC, so run IDs and log timestamps stay UTC —
  `systemctl list-timers bc25-tournament.timer` is the authority on when the
  next one fires.
- **Format**: every pair (alice-bob, alice-carol, bob-carol) x every map in
  `tools/bc25-maps.txt` x both sides -- 450 games. Maps are played in random
  order, so a run that hits its time limit yields an unbiased random subset
  rather than the alphabetically-first slice; such a run is labelled
  `!! INCOMPLETE` at the top of its `summary.txt`. Read that line before
  drawing conclusions from a run's standings.
- **Which bot plays**: the agent's **last committed** `src/<name>/` at the
  repo's HEAD when the tournament starts — never the working tree. Commit
  when your bot is in a state you want measured; keep `HEAD` compiling.
- **A bot that fails to compile in isolation forfeits** that tournament (the
  other pair still plays). Forfeits are recorded in the summary.
- Results are committed to `tournaments/` and pushed automatically.

**Using tournament results** (per TRAINING_ALGORITHM.md's measurement
doctrine): the sibling bots are true peers — independent lineages at a
comparable stage — so tournament games are the highest-value loss source in
Step 1 and legitimate evidence everywhere the algorithm calls for an even
instrument. But the accept gate stays *within* your own workspace
(head-to-head vs. your last snapshot); the tournament happens only twice a
day and its timing shouldn't gate your loop.

## Progress reporting

Each agent keeps two charts in `agents/<name>/progress/`, regenerated after
every accept and shown when reporting progress:

| Chart | What it answers |
|-------|-----------------|
| `cumulative_iterations.png` | how fast is this lineage actually accepting work? Read the slope; a flat stretch is time spent on rejected candidates. |
| `vs_old_bots.png` | is the bot stronger in absolute terms? Win% against a frozen roster (iter0, then every 5th snapshot), which a moving gauntlet pool cannot tell you. |

Tools are shared and strategy-neutral (`tools/plot_progress.py`,
`tools/track_vs_old_bots.py`, `tools/plot_vs_old_bots.py`, run with
`tools/.venv/bin/python3`); each auto-detects the workspace it is run from and
reads only that agent's data. Ported from battlecode26-vibe, which took them
from battlecode22-vibe. `progress/vs_old_bots_history.csv` is committed --
`gauntlet/` is git-ignored, so it is the only durable record of these
measurements.

Each gauntlet run records which build actually played in
`gauntlet/<run-id>/bot.txt` (`tools/bot_identity.py`, by content, normalising
the package line), and that is what labels a row in
`progress/vs_old_bots_history.csv`. A label ending `+cand` means the run
measured a candidate ahead of every snapshot — normal for a roster run played
before the accept decision — so read `carol_iter7+cand` as "after iter7, not
yet accepted", never as iteration 7 itself.

These are per-agent and stay inside the agent's own workspace; they are not a
cross-agent comparison. Cross-agent standing is what `tournaments/` is for.

## Calibrate your null: run a mirror

Before trusting any head-to-head threshold, measure what **identical code**
scores against itself. Copy your current bot to a second package differing only
in its `package` line and play it against the original over your usual sample.

This is not a formality. On 2026-09-07 one agent measured it and found identical
code split **all 20 maps, exactly 20/40, with zero swept maps** — the null has
**no variance at all**, not binomial spread. That invalidates the reasoning
"n/40 is only 1.6 SD from 50%, so it is inside the noise floor": under a
deterministic engine and deterministic bots there is no noise floor, and a
5-game margin is a real 5-game effect. A candidate had been rejected on that
mistaken basis and had to be accepted on review.

Whether *your* mirror is deterministic depends on how your bot uses randomness,
which is why each lineage must measure its own rather than assuming either way.
Once measured, keep the mirror package as a permanent control and read every
head-to-head against it instead of against an assumed 50%.

**Regenerate the mirror from your CURRENT build every time you use it.** A
mirror package created once and left alone silently becomes a fork of an old
build, and then it is not a null at all — it is an ordinary head-to-head against
a stale opponent, which is exactly the measurement you were trying to avoid. One
agent's `alice_mirror` had drifted this way before it was ever run. Verify
byte-identity apart from the package line, as you would for a snapshot.

The subtler version bites *after an accept*: your mirror must be built from the
**baseline the candidate is being measured against**, and that baseline moves
every time you accept something. Attributing a candidate's deviations against a
mirror of the previous accepted build **credits the candidate with games the
already-accepted mechanism flipped**. Two nulls one accept apart disagreed on
6 of 40 games — same net margin, different games. The tell is cheap to check:
if maps appear in *both* the previous iteration's deviation list and this one's,
you are reading a stale null.

**Quote margins in games against the mirror null, not in standard deviations.**
"+2 games against a null that never sweeps a map" imports no random-sampling
model; "+0.8 sd" imports one this engine does not have. Both mirrors measured so
far sit *exactly* at the even split (12/24 and 20/40), so a margin is simply the
number of games the code flipped.

**Your error bar is over MAPS, not over games.** Ask what would have to be
re-rolled to get a different number. Re-running the same games cannot change
anything — every (map, side) cell is a fixed function of the two programs — so
per-game randomness is not your error bar and a binomial sd is the wrong model.
The only thing that varies between one estimate and the next is *which maps were
drawn*, which makes the map the unit of resampling. Use
`tools/map-resample.py <run-dir>`: bootstrap and jackknife over maps, a 95%
interval, and the distance from the mirror null.

This matters in **both** directions, and quoting a formula instead of the data
got it wrong both ways in one session. Binomial overstated the spread ~2x on an
interaction estimate (deterministic per-map outcomes are concentrated, not
coin-flip-like: eight of twelve maps contributed exactly zero). The same floor
then **under-sold an accept** — hedged as "inside the noise band" when
resampling put it at +2.0 sd — and **badly under-reported a rejection**, which
was not "indistinguishable from the null" but *identical to it on every map and
both sides, se = 0*. That is a far harder rejection than a win rate near 50%.

**Corollary, measured twice independently: a swept map is a near noise-free
instrument.** Identical code swept nothing — 0 of 12 maps for one lineage, 0 of
20 for another; every map split 1-1. So a swept win is a real effect rather than
spawn luck, and swept-map counts deserve more weight than headline win rates.
This also turns out to be the *right unit*: a swept map is exactly the map-level
observation that resampling treats as the datum, so leaning on sweeps was
correct before anyone here understood why.

The mirror also gives you exact causal attribution: games where the candidate
deviates from the mirror's outcome are precisely the games the mechanism
changed, so you can count how many it won and lost rather than inferring from
an aggregate. Pair it with a firing count — a mechanism can be **rare and
high-value**, and a low firing rate on its own is not evidence that it did not
cause the result.

## Never stop to wait (hard)

Nothing resumes an agent automatically. When you stop, you go idle and your
session ends until a human notices — while your remote run continues on
battlecode-dev regardless of whether you are watching it. So stopping to wait
buys nothing and costs every minute until someone intervenes.

Two of the three agents ended their first session this way ("waiting on the
gauntlet", "the watchers will notify me"). Per TRAINING_ALGORITHM.md's "Never
idle": waiting on a run you already started is normal execution, not a
stopping point. Poll it to completion yourself, and use the gaps for
non-blocking work — writing up the iteration, engine probes, replay tracing,
preparing the next hypothesis, ablation planning.

Stop only when genuinely blocked by something outside your control, and say
precisely what is blocking you and what you would do next.

## If your session dies mid-run

The gauntlet's remote runner is launched with `setsid` on battlecode-dev and is
**not** tied to your session: when the driver-side poll loop dies (a dropped
SSH, a killed session, the 180-minute poll deadline), the games keep playing to
completion. What is lost is only the collation.

So never re-run a gauntlet you were already running — that discards finished
matches and burns shared VM time twice. Recover it:

```bash
cd agents/<you>
../../tools/gauntlet-collect.sh --list          # runs on the VM + whether each finished
../../tools/gauntlet-collect.sh <run-id>        # collate it here (default: newest)
```

It writes the usual `results.csv` / `reasons.txt` / `summary.txt` / `losses/`.
A run with no `GAUNTLET-COMPLETE` marker is still collated, with `!! INCOMPLETE`
at the top of its summary — read that line first, as with tournament summaries:
opponents are the outer loop, so a truncated run's later opponents may have no
games at all.

Anything you chained *on the driver* to fire when a run finished (a watcher
loop, a queued follow-up gauntlet) does die with the session. After a recovery,
check whether the thing you queued behind the run actually launched.

## Shared-resource rules (hard)

`battlecode-dev` also serves a **live BC26 project**, plus your two sibling
agents. Therefore:

- Never `pkill`/`kill` anything on battlecode-dev; never stop either VM.
- Run gauntlets with `MAXJOBS` <= 3 (the tools' default). Games are gated by a
  flock semaphore shared across all BC25 runners (`GLOBAL_CAP`, 5) under a
  machine-wide ceiling that counts BC26's games too (`HARD_CAP`, 7), so your
  run will queue behind your siblings' rather than oversubscribing the box.
  Expect runs to be slower when all three of you are evaluating at once —
  that is the system working, not a failure.
- Driver disk is tight: your workspace's `gauntlet/` output is git-ignored —
  prune old runs you no longer need. Keep bulky artifacts on battlecode-dev.
- **If you write your own tool that touches battlecode-dev, it must obey the
  same two rules the shared runners do.** Both have already been violated in
  practice, once in `tools/` and once in a lineage's own tool, and neither
  failure is visible in its own output:
  1. **Take a semaphore slot before starting any game.** Every other runner's
     `HARD_CAP` check counts running games, so a runner that starts one without
     a slot does not merely exceed the cap — it makes the cap a fiction for
     everyone, including the BC26 project.
  2. **Never build into a directory a gauntlet runs from.** `gauntlet.sh`
     compiles ONCE and then every game loads its robot classes from
     `build/classes`; a `./gradlew run` in that same workspace rewrites those
     classes underneath games already in flight. The damage lands on the
     GAUNTLET, not on the tool, so the tool looks fine and the run it corrupted
     never announces itself. Build in a sibling directory or under `/tmp`.
     (Syncing `src/` is harmless — nothing recompiles mid-run — but only
     because of that build-once behaviour, so do not rely on it loosely.)

  A lineage found both of these in its own tool by reading `tools/vm-match.sh`,
  which documents them. That is luck, not a process, which is why they are here.

## Git discipline

- Commit **only your own paths** (`agents/<you>/...`), staging them
  explicitly — never `git add -A` (this nearly baselined broken code twice in
  the BC26 project).
- `git pull --rebase` before every push; on push rejection, pull-rebase and
  retry. Three agents plus cron share this repo; races are normal, conflicts
  are not (paths are disjoint — a conflict means someone broke rule 1 of this
  section).
- Never delete anything from the GitHub repository without the user's
  permission.

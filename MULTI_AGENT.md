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

## The tournament

- **Schedule**: 06:00 and 18:00 UTC daily, via cron on claude-driver
  (`tools/cron-tournament.sh`, log at `~/bc25-tournament-cron.log`).
- **Format**: every pair (alice-bob, alice-carol, bob-carol) x every map in
  `tools/bc25-maps.txt` x both sides.
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

## Shared-resource rules (hard)

`battlecode-dev` also serves a **live BC26 project**, plus your two sibling
agents. Therefore:

- Never `pkill`/`kill` anything on battlecode-dev; never stop either VM.
- Run gauntlets with `MAXJOBS` <= 3 (the tools' default). The runners already
  yield while the machine-wide game count is at `GLOBAL_CAP` (6).
- Driver disk is tight: your workspace's `gauntlet/` output is git-ignored —
  prune old runs you no longer need. Keep bulky artifacts on battlecode-dev.

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

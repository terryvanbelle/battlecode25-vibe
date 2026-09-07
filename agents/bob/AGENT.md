# Bob's workspace

You are **Bob**, one of three independent Battlecode 2025 bot developers
(the others are alice carol - you must never read anything in their workspaces).

## Your charter

- Your bot lives in `src/bob/` (Java package `bob`). Frozen accepted
  snapshots go in `src/bob_iterN/` (package `bob_iterN`).
- Follow `../../TRAINING_ALGORITHM.md` (the loop) and `../../MULTI_AGENT.md`
  (isolation, tournament, shared-resource, and git rules). Both are binding.
- Keep your own `TRAINING_LOG.md` here, per the algorithm's Logging section,
  plus any private notes/tools you want in this directory.
- Commit only paths under `agents/bob/`, staged explicitly; pull --rebase
  before pushing. Your last committed `src/bob/` is what plays in the
  twice-daily tournament - keep it compiling.

## Running matches (from this directory)

```bash
TEAM_A=bob TEAM_B=examplefuncsplayer ../../tools/vm-match.sh DefaultSmall
BOT=bob OPPONENTS="examplefuncsplayer bob_iter1" ../../tools/gauntlet.sh
```

Both run headlessly on the battlecode-dev VM and pull results back here.
`gauntlet/` output is git-ignored; prune old runs.

**Maps: leave `MAPS` unset.** A gauntlet with no `MAPS` plays a fresh random
sample of 25 maps drawn from the 75 in `../../tools/bc25-maps.txt` (both sides
of each, so 25 maps x 1 opponent = 50 games). `NMAPS=40` widens the sample.
Do not hand-pick a standing map list: a fixed list is an overfitting surface,
and accepted iterations drift toward the maps on it. Resampling every run tests
each iteration on ground its predecessors were never tuned against.

The sample is drawn once per run and shared by every opponent in it, so
opponent-vs-opponent comparisons *within* a run are exact. Across runs the maps
differ, so a raw win-rate delta between two runs is noisier than it looks --
your accept gate is a within-run head-to-head, which is unaffected. Pin
`MAPS="$(cat gauntlet/<run-id>/maps.txt)"` to replay a run's exact maps, which
is what you want for a regression check, an ablation, or chasing one map.

## Reporting progress (two charts, kept current)

Regenerate both after every accept, and show them when you report:

```bash
../../tools/.venv/bin/python3 ../../tools/plot_progress.py        # progress/cumulative_iterations.png
../../tools/.venv/bin/python3 ../../tools/plot_vs_old_bots.py     # progress/vs_old_bots.png
```

**Cumulative accepted iterations** counts your `src/bob_iterN/` snapshots by the
date each first appeared. Read the *slope*, not the height: a flat stretch means
the loop spent that time on rejected candidates, which is information about your
loop rather than about your bot. Record process changes -- changes to *how* you
evaluate, not individual accepts -- in `progress/milestones.txt` as
`<commit>|<label>`, in the same commit as the change itself.

**Win % vs. old bots** tracks a frozen roster: iteration 0, then every 5th
accepted snapshot, derived automatically, never hand-edited. This is your only
absolute-strength instrument. Your gauntlet headline win% is measured against a
pool that changes and a map sample that is redrawn each run, so it cannot tell
"the bot improved" from "the instrument moved"; a frozen opponent can.

```bash
# extend it: play the roster, record the run, redraw
OPPONENTS="$(../../tools/.venv/bin/python3 ../../tools/track_vs_old_bots.py --roster)" \
    ../../tools/gauntlet.sh
../../tools/.venv/bin/python3 ../../tools/track_vs_old_bots.py gauntlet/<run-id>
```

Points from a deliberate roster run are drawn solid; points backfilled from a
pre-accept head-to-head are hollow, because the bot measured there was a
candidate that may have been rejected. A dip in a hollow point is not a
regression. History lives in `progress/vs_old_bots_history.csv` and IS committed
-- `gauntlet/` is git-ignored, so that file is the only durable record.

`progress/roster_extra.txt` adds fixed non-snapshot yardsticks (a synthetic
archetype, a pinned benchmark), one name per line. They qualify for the same
reason old snapshots do: they never change.

## Ground truth

- Official spec: https://play.battlecode.org/bc25/specs (Battlecode 2025).
- Engine source (official, allowed): https://github.com/battlecode/battlecode25
  and the engine jar in ~/.gradle on battlecode-dev (javap it as needed).
- Prior-year methodology: battlecode22-vibe and battlecode26-vibe repos
  (LEARNINGS.md, RESEARCH.md). Their post-mortem syntheses cover 2019-2024;
  2025 post-mortems are forbidden.

## BC25 finals benchmark bots — a yardstick, never an opponent (HARD)

Bots from the BC25 finals have been downloaded by the coordinator, on the
project owner's authority, for **one purpose**: measuring how far this lineage
is from a tournament-winning bot. The rules are absolute.

- **Never read their code.** It lives only on battlecode-dev, outside this repo.
- **Never examine any game played against them.** No replay is written for those
  games at all, so no artefact exists — do not seek, request, or reason from
  one. If you ever find yourself holding one, stop and tell the coordinator.
- **Never run those matches.** The coordinator runs them; you never do.
- **Never add one as an opponent.** Not to your gauntlet, not to
  `progress/roster_extra.txt`, not to a synthetic archetype, not anywhere. This
  is the failure mode to watch for, because it looks *reasonable*: a
  never-changing external bot is exactly what a frozen yardstick is made of, and
  a future session could propose it in complete good faith. `tools/progress_lib`
  refuses these names outright, but the rule binds regardless of the guard.
- **You may read a benchmark score** if one appears in a committed results file.
  That is the whole of your permitted access.

Treat a score as *distance*, not as a target. Tuning toward a fixed external
opponent is overfitting with extra steps — the same error as hand-picking a
standing map list, which this charter already forbids for that exact reason.

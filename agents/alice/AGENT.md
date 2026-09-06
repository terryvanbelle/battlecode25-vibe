# Alice's workspace

You are **Alice**, one of three independent Battlecode 2025 bot developers
(the others are bob carol - you must never read anything in their workspaces).

## Your charter

- Your bot lives in `src/alice/` (Java package `alice`). Frozen accepted
  snapshots go in `src/alice_iterN/` (package `alice_iterN`).
- Follow `../../TRAINING_ALGORITHM.md` (the loop) and `../../MULTI_AGENT.md`
  (isolation, tournament, shared-resource, and git rules). Both are binding.
- Keep your own `TRAINING_LOG.md` here, per the algorithm's Logging section,
  plus any private notes/tools you want in this directory.
- Commit only paths under `agents/alice/`, staged explicitly; pull --rebase
  before pushing. Your last committed `src/alice/` is what plays in the
  twice-daily tournament - keep it compiling.

## Running matches (from this directory)

```bash
TEAM_A=alice TEAM_B=examplefuncsplayer ../../tools/vm-match.sh DefaultSmall
BOT=alice OPPONENTS="examplefuncsplayer alice_iter1" ../../tools/gauntlet.sh
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

## Ground truth

- Official spec: https://play.battlecode.org/bc25/specs (Battlecode 2025).
- Engine source (official, allowed): https://github.com/battlecode/battlecode25
  and the engine jar in ~/.gradle on battlecode-dev (javap it as needed).
- Prior-year methodology: battlecode22-vibe and battlecode26-vibe repos
  (LEARNINGS.md, RESEARCH.md). Their post-mortem syntheses cover 2019-2024;
  2025 post-mortems are forbidden, as are downloaded bot implementations.

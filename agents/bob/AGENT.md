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
BOT=bob OPPONENTS="examplefuncsplayer bob_iter1" MAPS="DefaultSmall DefaultMedium" ../../tools/gauntlet.sh
```

Both run headlessly on the battlecode-dev VM and pull results back here.
`gauntlet/` output is git-ignored; prune old runs. The full map list is
`../../tools/bc25-maps.txt` (75 maps; use subsets for day-to-day loops).

## Ground truth

- Official spec: https://play.battlecode.org/bc25/specs (Battlecode 2025).
- Engine source (official, allowed): https://github.com/battlecode/battlecode25
  and the engine jar in ~/.gradle on battlecode-dev (javap it as needed).
- Prior-year methodology: battlecode22-vibe and battlecode26-vibe repos
  (LEARNINGS.md, RESEARCH.md). Their post-mortem syntheses cover 2019-2024;
  2025 post-mortems are forbidden, as are downloaded bot implementations.

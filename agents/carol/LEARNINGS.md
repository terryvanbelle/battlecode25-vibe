# Carol — durable lessons (BC25)

Distilled from `TRAINING_LOG.md`. Organised by theme, not chronology.

## The game's real shape

- **BC25 is a coverage race, not a fight.** In carol's first 32-game self-lineage
  evaluation, 30 of 32 games ran the full 2000 rounds and were decided by the "painted
  more of the map" tiebreak; only 2 ended via the 70% rule. Optimise tiles-painted-per-
  round before optimising anything combat-shaped.
- **No unit can damage an enemy robot's HP.** Only towers deal robot damage; everything
  else is paint denial (moppers steal 10, swing 5) and paint starvation (0 paint = -20
  HP/turn and frozen). "Killing" enemy units means cutting them off from paint.
- **Patterns are exact.** All 24 non-centre tiles of a tower pattern (25 for an SRP) must
  hold precisely the right colour; EMPTY fails a 0-bit just as enemy paint does. So one
  enemy soldier attack denies a whole ruin, and mopping a contested tile is not enough —
  it must be repainted.

## Measurement

- **Determinism holds** (verified: 3 identical runs, byte-identical decompressed
  replays). Re-running a marginal result yields nothing; vary the dose or widen the
  sample. `tools/replay-strings.py --hash` is the arm-to-arm identity check.
- **Indicator strings are the cheapest instrument by a wide margin.** Putting round,
  chips, tower count and tower paint into the tower's indicator string cost one match and
  immediately produced the single largest finding of the project so far (below). Do this
  before theorising, every time.
- **An opponent pinned at 100% has no resolving power.** examplefuncsplayer went 24/24
  at iteration 0 and was demoted to benchmark immediately; the real instruments are the
  frozen self-lineage, the synthetic archetypes, and the sibling bots in the tournament.

## Economy

- **Look for the unspent resource.** iter1's trace: **213,260 chips idle at round 2000**
  while towers sat paint-dry at ~0/1000 and unit production was throttled to a trickle.
  The cause was a one-token bug of omission — every ruin was built as a money tower, and
  money towers generate no paint, so team paint income was the single starting lv2 paint
  tower (10/turn) for the entire game. This is the algorithm's "capability preserved at
  zero marginal cost" shape: a whole resource stream doing nothing.
- **Fixing one binding constraint exposes the next.** Switching to all-paint towers made
  chips bind instead: unreserved robot spawning drained the treasury to ~150 and tower
  count *fell* from 8 to 3, because completing a ruin needs 1000 chips it no longer had.
  A 1200-chip reserve restored it to 10 towers. Always re-trace after relieving a
  bottleneck — the trace that motivated the change is stale the moment it lands.
- **Check reachability before splitting a change into two iterations.** The chip reserve
  is provably dead code on the pre-change bot (a 1200-chip gate against a treasury that
  never drops below 2230 and climbs to 213k), so reserve-and-paint-towers is one
  indivisible change, not two. Splitting it would have produced a meaningless null result.

## Idleness is the enemy

- **Instrument for "did nothing" states, not just for outcomes.** Adding a `NOTGT` marker
  for "soldier had no empty tile in action radius" revealed that ~57% of all soldier turns
  painted nothing. Absolute degeneracy signals like this need no opponent to be wrong, and
  the algorithm is right that they beat opponent-relative comparisons as targets.
- A local random walk cannot find the frontier on a 40x40+ map once home is painted.

## Process

- `git pull --rebase --autostash` before every push; three agents plus cron share the
  repo and a plain rebase aborts on their unstaged work.
- Commit `src/carol` itself, not only the snapshots — the twice-daily tournament plays
  the last committed `src/carol`, and it silently stayed at iteration 0 for two accepted
  iterations because only the `carol_iterN/` copies were being staged.

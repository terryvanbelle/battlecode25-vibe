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

## Soldiers cannot contest ground (the coverage endgame)

A soldier's attack paints a tile **only if it is EMPTY or already ally-painted** — enemy
paint is untouchable to it (engine: `soldierAttack` paints only when
`getPaint(loc)==0 || sameTeam`). So once the two colours meet along a frontier, soldiers
on the wrong side of it have literally nothing to do. This is the mechanism behind the
`NOTGT` idle rate staying near 60% even after exploration was fixed: the soldiers *are*
reaching new ground, but much of it is enemy-painted and therefore inert to them.

Only two things convert enemy territory:
- **Splashers**, in bulk, within r2<=2 of the splash centre (and they paint empty/ally
  tiles out to r2<=4 in the same action);
- **Moppers**, one tile at a time, and only back to EMPTY — a soldier must then follow up
  to actually claim it.

So the coverage race is won by conversion capacity, not by painting speed on virgin
ground, and a bot with no splashers has almost none. Elevates splashers from "a nice
throughput gain" to the central missing capability.

## Measurement (addendum, 2026-09-06)

- **Never score a gauntlet from a prefix.** Iteration 2's accept note was written from a
  partially-written `results.txt` and concluded "carol_rush is running near even against
  carol", which became the leading structural target. Over the completed 32 games rush was
  at 84.4%. The h2h that gated the accept happened to be complete (the runner iterates
  opponents in order), so the decision survived, but the strategic conclusion filed with it
  was wrong for hours. Wait for `GAUNTLET-COMPLETE`.
- **Map sampling changed on 2026-09-06**: `tools/gauntlet.sh` now draws a fresh RANDOM
  25-map sample per run instead of using a hand-picked list, because a standing map list is
  an overfitting surface. Consequences for reading this log: (a) win rates from runs BEFORE
  and AFTER that change are not measured on the same instrument and must not be compared as
  raw deltas — iterations 0-3 ran on a fixed 16-map list; (b) within a run the sample is
  shared by every opponent, so the accept gate (a within-run head-to-head) is unaffected;
  (c) pin `MAPS="$(cat gauntlet/<run-id>/maps.txt)"` whenever run-to-run comparability is
  the point — regression checks against an older snapshot, ablations, re-running a single
  map to trace it, and especially the mirror-match play-symmetry audit, which cannot tell a
  real side bias from a resampling artifact unless the maps are pinned.

## Fixed constants rot into dead bands

A flat threshold on a resource creates a band the resource can get stuck in. `CHIP_RESERVE`
= 1200 meant a tower spawned only at `chips >= 1200 + unitCost`; on a map where no further
ruin was ever completed the treasury settled at ~1350 — above the reserve, below the gate —
and unit production stopped **completely and permanently** at round 25, with a full paint
stash and 1350 chips unspent, ending in annihilation at round 69. The reserve had been
accepted on good evidence (it fixed a tower collapse) and was still right in the regime it
was measured in; it was armed in a regime that was never measured. Two rules that follow:
arm a reserve only once the thing it protects is demonstrably happening, and instrument the
gate value itself (`rsv=` in the indicator string), not just the resource it gates.

## The two ceilings (why the tower mix is the whole economy)

Every painted tile costs 5 paint and **all** team paint originates from paint-tower mining
(5/10/15 per turn at lv1/2/3, plus 3 per active SRP per paint tower). Every unit costs
chips, and all chips originate from money-tower mining (20/30/40, plus 3 per SRP per money
tower). So a game plan is pinned between two hard ceilings:

- **painting rate <= team paint income / 5 tiles per round** — set by paint-tower count;
- **unit count growth <= team chip income / unit cost** — set by money-tower count.

Both numerators come from the same scarce thing: completed ruins. So *the paint/money build
mix is not a detail, it is the strategy*, and the failure mode is always the same shape —
one resource pinned at zero while the other accumulates unspent:

| trace | regime | symptom |
|---|---|---|
| iteration 1, DefaultMedium | all money towers | 213k chips idle, tower paint ~0 |
| iteration 3, galaxy | all paint towers | 30 chips/turn forever, one soldier per 8.3 rounds, tower paint +5/turn unspent |
| iteration 3-4, DefaultSmall | 1 paint tower, no ruins claimed | tower paint 0 from round 11, chips idle, annihilated |

Read both numbers in every economic trace, not one. A trace that shows only the resource
you suspected will confirm whatever you already believed.

## Reading a running gauntlet is free information

Two of this session's most useful findings were read out of replays pulled from a gauntlet
that was still running, hours before its summary existed: the iteration-5 mechanism check
(chip income 30 -> 150/round, towers 12 -> 25) and the IDLE-ALLY/IDLE-ENEMY split that chose
the next two iterations. Three things make this work and are worth reusing:

- **Both teams are in one replay.** A candidate-vs-snapshot game contains both arms, so a
  single replay is an exact A/B on identical map and seed. Separate them by a field only one
  build emits (`rsv=`, `IDLE-*` vs `NOTGT`) — which is a reason to always give a new
  instrument a *new name* rather than changing an existing one's format.
- **`scp` one finished replay off the VM mid-run.** Read-only, no contention, no waiting.
- **But never rebuild mid-run.** Games load classes from the shared `build/classes`, so
  `vm-compile.sh`, `vm-match.sh` or a second gauntlet launched from the same workspace would
  poison every game that has not yet started. Reading is safe; building is not.

Corollary for instrumentation design: stamp something team-identifying into every indicator
string. Both of carol's builds emit `pnt`/`slf` identically, so idle *counts* were separable
but idle *rates* were not — a per-team denominator was unavailable for want of one character.

## Accepting on an incomplete run is sometimes correct — state why

"Never score from a prefix" is about conclusions the remaining games could reverse. When the
outstanding games *cannot* change the verdict — 23 of 24 head-to-head games played, gate at
>50%, worst case 16/24 — waiting buys nothing and costs the tournament an iteration. The
discipline is not "always wait", it is "compute what the missing games could do first, and
write that computation down".

# Alice — LEARNINGS.md

Durable lessons distilled from `TRAINING_LOG.md`, organised by theme rather
than chronology. The log is the evidence; this is the index of what I would
tell a fresh session before it touched anything.

---

## 1. The economy of Battlecode 2025 (as my lineage has measured it)

**Paint is the binding resource; chips are not, and have not been since
iteration 2.** Every game up to iteration 3 ended with an unspendable chip
mountain — $113k (iter1), $120,840 (iter2), $204,780 (iter3). Any mechanism that
converts chips into paint or into paint *income* is close to free.

**Iteration 4 proved that and drained the mountain** — towers upgrading
themselves took end-of-game chips from $87,100 to $1,740 on Racetrack and held
coverage flat (495→555‰) where the baseline decayed (436→283‰); 39/50 vs the
previous snapshot. **But the sink is finite**: once every tower reaches L3,
`getNextLevel()` returns null and chips pile straight back up ($180,890 by
r2000 in a later trace). SRPs are the obvious way to reopen it, and they remain
unbuilt.

**A robot's entire output is bounded by the paint it was born with** — because
there is no refill anywhere in the bot, and `transferPaint` is never called (see
§3b; this is the largest single unused mechanic I have found). A soldier spawns with 200, spends 5 per painted
tile and 25 per pattern mark, bleeds upkeep every turn, and dies at ~41 rounds
having painted ~35 tiles (traced: id12472, DefaultLarge). Therefore **cumulative
team coverage is bounded by cumulative paint production**, not by chips and not
by unit count.

**Paint is also a throughput multiplier, not just a budget.** Below 50% stash,
cooldowns scale by (100 − 2·paint%). Every soldier spends its last third of life
acting at roughly half rate. Keeping a unit above 50% is worth about double its
action rate.

**Ranked chips→paint conversions** (all engine-verified, see `RULES.md`):
1. **SRP** — 200 chips buys +3/turn to *every* producing tower, both kinds. At
   16 towers that is +24 paint and +24 chips per turn. Best per chip by an
   order of magnitude; needs a 5×5 pattern held 50 rounds.
2. **Tower self-upgrade** — paint income 5→10→15/turn for 2500 then 5000 chips,
   and it costs *nothing else*: `assertCanUpgradeTower` never checks action
   readiness and `upgradeTower` adds no cooldown.
3. **New tower** — 1000 chips for +500 instant tower paint; capped by ruins and
   the 25-tower limit.

**Money towers are spawn-dead after ~2 units.** They produce 0 paint and start
with 500; once spent they can never spawn again. Tower *paint*, not chips, is
what gates spawning.

## 2. Coverage is a stock under attack, not a running total

The single most expensive misconception I have held. Painted area can and does
*decline*: iteration 3's coverage peaked at 562‰ on round 500 and decayed to
467‰ by round 2000 while its own soldier count quadrupled. Enemy moppers erase
tiles faster than a starving army repaints them. Any reasoning of the form
"we paint X tiles per round, so coverage grows" is wrong.

Corollary: **soldiers cannot overwrite enemy paint** (engine: paints only if the
tile is empty or already ally). A soldier-only bot has no answer to erasure at
all. Only splashers convert enemy paint, and moppers clear it to empty.

## 3. RETRACTED — "unit population has an interior optimum set by the clumping tax"

**This section previously argued that my bot's armies grow until the adjacency
tax strangles them. It was an artifact of a broken instrument and is withdrawn.**

My replay dumper tracked live robots but never removed the dead: BC25 reports
robot deaths as `Action.DieAction` inside a `Turn`, not via `Round.diedIds`,
which carries none. So every "units alive" figure I ever logged was **cumulative
spawns**. It had me believing the bot fielded 690 units on a 625-tile map.

Corrected on the same replays: the real army is **~34 units**, and the accepted
baseline routinely ends a game with **zero soldiers alive**. Iteration 3's
famous "314 soldiers" was cumulative too — its *reject* stands, its *explanation*
does not.

**What is actually true of the engine** (unchanged, still verified): the
adjacency tax is −1 paint per adjacent ally robot, −2 on enemy paint, and it is
charged on ally tiles too. What is *not* established is that my bot has ever been
dense enough for it to bind. Do not plan against clumping without first measuring
adjacency on a corrected trace.

## 3b. The real degeneracy: a starvation treadmill

With deaths counted properly, the shape of every game is this:

- **65-100% of all unit deaths are paint starvation**, not combat. A unit at 0
  paint takes −20 HP/turn and cannot act until refilled.
- **`transferPaint` is called zero times per game**, by either team. Nothing in
  the lineage has ever refilled a unit. A unit's lifetime output *is* the paint
  it was born with.
- So the bot spawns ~102 units and loses ~104 per 250 rounds to hold ~34 alive.
  Its only way to deliver fresh paint to the field is to **respawn**: 200 tower
  paint **plus 250 chips**, discarding a positioned veteran, to restart the same
  ~85-round clock. A refill would cost the same paint and **no chips**.

**The spawn mix is a price artifact, not a policy.** The tower's spawn line reads
25% moppers. The *realized* mix is ~90% moppers, because a mopper costs 100 tower
paint and a soldier 200 against an income of 5-15/turn — the tower funds the cheap
unit twice as often and never saves up for the expensive one. Worse, when the RNG
picks SOLDIER and paint is short the build simply fails and the turn is wasted.
Moppers cannot paint; painted area is the win condition.

**Corollary that cost a run**: driving moppers to zero does not fix this. At
`MOPPER_PAINT_RESERVE=200` the bot painted ~10x more and still lost, because it
did zero mopping while the opponent erased its paint all game (see §2 — coverage
is a contested stock). The useful range is an interior one.

## 3c. The absorbing state — the most expensive bug this lineage has had

Tower paint funds spawning. A soldier costs 200 of it, a mopper 100, and tower
paint income is 5-15/turn. So the tower funds the cheap unit twice as often and
never saves for the expensive one — and **the drain is self-reinforcing**:

> tower paint → 0 ⇒ only the 100-paint mopper is affordable ⇒ moppers complete no
> tower patterns ⇒ no new towers ⇒ paint income never recovers ⇒ tower paint stays 0

This is not a skewed ratio, it is an **absorbing state**. On Mirage the accepted
iteration-4 build entered it at **round 200** and played the remaining 1,369
rounds with 2 towers, 0 soldiers and coverage falling 132 → 15‰ before being
eliminated. The same signature appears in every loss examined (box; HungerGames
spawning 97% moppers at r2000).

It also re-explains **split-by-side maps**, which I had filed as positional noise:
when both sides run the same rule, the map is a race into the same absorbing
state, and small positional differences decide who falls in first. One mechanism,
not fifteen coin flips. **Whenever many maps split by side, look for a shared
runaway before concluding "positional".**

The fix (iteration 5) is one line and carries no tuned constant: build a mopper
only if the tower could have afforded a soldier instead —
`rc.getPaint() < UnitType.SOLDIER.paintCost`.

## 4. Methodology lessons paid for in this project

**A replay counter means nothing until you have found its call site.** I built a
hypothesis on "MopAction == 0 across a whole game". `MopAction` is emitted only
by `mopSwing`, which my bot never calls, so that zero was guaranteed a priori
and measured nothing. The real counter was `UnpaintAction`. Check the emitter
before quoting the number.

**Read the engine, not your own digest of the engine.** My `RULES.md` line on
the clumping tax was literally true and still left me with the wrong model,
because it did not say that the tax survives onto ally tiles. Opening
`processEndOfTurn` settled in one minute what I would otherwise have guessed.

**A representativeness argument can be wrong in the direction that flatters
you.** Before iteration 3 I argued the pool never contests enemy paint, so
cutting the bot's only anti-paint unit was untested-but-safe. The pool contests
it constantly — with the very unit I was cutting. Check what the *opponents*
do in a replay before claiming a threat is absent.

**The mechanism can engage exactly as designed and still invert the result.**
Iteration 3 hit every mechanistic prediction (moppers → 0, soldiers → 314) and
lost 7/24. "Mechanism verified" is a licence to evaluate, never a prediction of
the sign.

**A concentrated regression inside a broad win is a target, not a veto.**
Iteration 1 (DefaultSmall) and iteration 2 (maze) both accepted with one
one-directional swept-loss carried forward; both times the trace of that
regression was where the next real finding came from.

**Don't pick the arm that won by less than the noise floor.** Iteration 5's dose
50 scored two games above dose 100 (23/30 vs 21/30), but on the 27 (map,side)
cells both arms played they disagreed on *three*. I took dose 100, because its
threshold equals a game constant (`SOLDIER.paintCost`) while dose 50's is
arbitrary. Choosing the arbitrary constant *because* it won one extra cell on the
sample it was measured on is fitting the instrument, and the algorithm's stated
preference for self-calibrating thresholds is the tie-breaker that avoids it.

**Instrument any pool the change draws on, in the first run.** Iteration 6's
refill and the tower's spawn draw on the same tower paint. Printing `twPaint`
showed refilling *substitutes* for spawning rather than adding to it (pool drained
to 40% of baseline, 17% fewer soldiers) — which inverted my dose prediction before
the sweep rather than after it.

**Rejections are the cheapest evidence available.** Iteration 3 cost one run and
overturned two beliefs, opened a functional area, and explained why the current
accepted bot works. That is a better return than most accepts.

## 5. Instrument hygiene

- **Never redirect run output into the shared `/tmp` tree.** A sibling agent's
  gauntlet wrote its progress into the same absolute path as mine; the file
  interleaved. Use `agents/alice/logs/` and poll
  `gauntlet/<run>/results.txt`, which is workspace-scoped.
- **Map samples are now random per run** (25 of 75). Within a run every opponent
  plays the same maps, so the head-to-head accept gate is exact; *across* runs
  win rates are no longer measured on the same instrument. Pin with
  `MAPS="$(cat gauntlet/<run-id>/maps.txt)"` whenever comparability matters
  (regression checks, ablations, dose sweeps, re-tracing one game).
- **A hand-picked standing map list is an overfitting surface.** Mine (EVAL12)
  is retired.
- **Noise bands**: 24-game H2H — treat 13-15/24 as inside noise of 50%; 16/24 is
  ~92% one-sided, 17/24 ~97%. 50-game H2H — 24-29/50 inside noise, ≥30/50 ~92%,
  ≥32/50 ~98%.
- **A monotone counter is a bug report.** The tell for the death-accounting bug
  was a unit count that only ever rose, and a 2000-round dump containing zero
  `DIED` lines. Any "alive"/"in flight" figure that never decreases across a
  whole game is measuring arrivals, not stock — check the removal path before
  believing it. Cross-check a derived stock against the map's own bounds: more
  units than the map has tiles is impossible, and I logged it anyway.
- **Bytecode is not a constraint** for this bot: 0 overruns and 0 near-misses
  over a full 2000-round game, peak 1638/17500 (9%) for soldiers, 534/20000 (3%)
  for towers. Expensive logic — BFS navigation, symmetry inference, per-tile
  scoring — is affordable and should not be avoided on cost grounds.

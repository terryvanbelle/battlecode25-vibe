# Alice — LEARNINGS.md

Durable lessons distilled from `TRAINING_LOG.md`, organised by theme rather
than chronology. The log is the evidence; this is the index of what I would
tell a fresh session before it touched anything.

---

## 1. The economy of Battlecode 2025 (as my lineage has measured it)

**Paint is the binding resource; chips are not, and have not been since
iteration 2.** Every game so far ends with an unspendable chip mountain —
$113k (iter1), $120,840 (iter2), $204,780 (iter3). Any mechanism that converts
chips into paint or into paint *income* is close to free.

**A robot's entire output is bounded by the paint it was born with.** There is
no refill anywhere in the bot. A soldier spawns with 200, spends 5 per painted
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

## 3. Unit population has an interior optimum, set by the clumping tax

`processEndOfTurn` charges −1 paint per adjacent ally robot (−2 on enemy paint),
**and the ally-tile branch charges it too** — standing on your own paint waives
only the terrain penalty, never the crowding one. A surrounded robot pays −8 per
turn against a 200-paint stash.

So spawning is not free even when the resources exist: at 314 soldiers on a
1500-tile map (iteration 3) the entire army sat at ~0 paint and the team's paint
*actions* fell to ~80 per 250 rounds — one fifth of what a quarter as many
soldiers had managed. **More units produced strictly less work.**

The accepted iteration 2 wins partly by accident here: its mopper branch burns
tower paint on units that then consume almost nothing, which caps the soldier
population near a survivable density. A deliberate regulator should beat an
accidental one — but it must be measured, not assumed (that is the open
iteration 5 thread).

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
- **Bytecode is not a constraint** for this bot: 0 overruns and 0 near-misses
  over a full 2000-round game, peak 1638/17500 (9%) for soldiers, 534/20000 (3%)
  for towers. Expensive logic — BFS navigation, symmetry inference, per-tile
  scoring — is affordable and should not be avoided on cost grounds.

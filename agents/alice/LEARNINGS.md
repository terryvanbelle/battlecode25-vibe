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

**Extended 2026-09-07 by two measurements this section was missing** — see the
theme *"the engine debits before it checks"* below, which this entry should have
cited from the day it was written and did not:

1. **The map SATURATES.** Money at round 1200: T1 432‰ + T2 545‰ = **977‰
   painted**. The instant-win bar is 700‰. After ~round 500 there is no empty
   ground left to claim, so the remaining ~270‰ can only be **taken off the
   opponent** — and by the corollary above, the unit I mass-produce cannot take
   a single tile. That is the whole explanation for my coverage curve flattening
   at 450–530‰ for the last 1,400 rounds, in the **mirror** as well as against bob.
2. **The refused attack is not free.** The corollary said a soldier "cannot"
   overwrite enemy paint. It can *try*, and the engine charges it 5 paint for
   trying. That is a cost, not a no-op, and it went unnoticed for 22 iterations.

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

**[CORRECTED 2026-09-08 — the ~90% figure below is STALE. Iteration 5's reserve
rule fixed it: measured on the iteration-24 replay the realized mix is 572 soldiers
to 156 moppers, i.e. 78.6% SOLDIERS. The paragraph is kept because iterations 5-18
were designed while it stood, but it must not be quoted as current. A session of my
own lineage cited a stale ledger row on 2026-09-08 for exactly this reason.]**

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

### 3b-i. SHARPENED for moppers — "lifetime output IS the paint it was born with" is FALSE for a mopper

§3b above says *"a unit's lifetime output is the paint it was born with."* That is
true of a **soldier**, whose paint converts into painted tiles, and it is **exactly
wrong for a mopper**. From `UnitType`: a **mopper's attack costs 0 paint.** A
mopper with 8 paint mops precisely as well as one with 100.

So for a mopper, paint buys **duration and nothing else** — and since a mopper has
no income, upkeep is its *only* sink. Two levers exist and they are not equally
priced: adding income (refill) or **reducing upkeep**. The first is the closed
`transferPaint` direction; the second had never been looked at.

Measured 2026-09-07 over 25,825 mopper-turns on three maps
(`alice_mopstand`, verified inert: read-only calls, **0 bytecode overruns**):

| map | moppers | **died at exactly p=0** | died with >60 paint | median lifespan |
|---|---|---|---|---|
| UnderTheSea | 194 | **69.8%** | 18.5% | 80 rounds |
| catface | 84 | **71.8%** | 21.8% | 61 rounds |
| CastleDefense | 43 | **28.6%** | 50.0% | 38 rounds |
| **pooled** | **321** | **64.7%** | 23.6% | — |

CastleDefense is the honest exception and it is the combat map of the three — on a
map where the enemy kills moppers, the paint clock stops mattering. **A degeneracy
whose rate depends this strongly on the map is a regime, not a constant.**

**The accounting closes**, which is what licenses reading a mechanism off it. Per-turn
Δpaint on consecutive rounds against the engine's terrain table:

| tile under mopper | engine term | observed | unexplained |
|---|---|---|---|
| ally | 0 | **-0.54** | -0.54 (crowding tax) |
| empty | -2 | **-2.04** | -0.04 |
| enemy | -4 | **-3.50** | +0.50 |

Terrain is the whole sink. **This refuted my own follow-up hypothesis for free**: I
had nominated the crowding tax as the real drain and had already written the
instrument for it, and the reconciliation priced crowding at -0.54 against
terrain's -2 to -4. A decomposition that closes does not only license the
conclusion you wanted — it kills the one you were about to spend a run on.

### 3b-ii. A hypothesis dies of absent FREQUENCY or absent SUPPLY, and they look identical from the outside

Two of my hypotheses died within a day of each other, both by a count I nearly
did not take, and **the two counts are different**:

| hypothesis | frequency of the situation | supply of alternatives | died of |
|---|---|---|---|
| ruin-collision dispatch | fine — groups of 3+ were common | **0 unclaimed ruins left** | **supply** |
| mopper stands on enemy paint | **9.0%**, under its own gate | fine — 76% had an alternative | **frequency** |

The ruin case taught me to count supply, so on the mopper case I pre-registered a
supply check — and supply was *not* the problem. Had I checked only supply, having
"learned the lesson", the mopper hypothesis would have passed. **The transferable
rule is to take both counts, because the previous failure tells you which question
you asked last time, not which one matters this time.**

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

## 3d. PARTLY RETRACTED — towers are the master variable, but ruin supply does NOT cap them

> **Retracted 2026-09-07 by the first round-robin tournament.** The
> master-variable half stands and is stronger than ever. The "supply, not
> discovery" half is **wrong**, and it was wrong in the specific way this
> three-agent project exists to catch: it was inferred entirely from self-play,
> where both sides shared the defect, so ruins ran out late and evenly and the
> ceiling *looked* like supply.
>
> The independent lineage `bob` beat alice **143-7 (4.7%)**. On gridworld —
> 25 ruins — bob claims **14 towers by round 160** while alice stalls at **5**
> holding $3,240 it never spends. Same map, same ruin supply. Changing **one
> constant** in alice's wander (iteration 12) took it from **4 towers / 233‰** to
> **15 towers / 620‰** against `alice_iter7` on that map.
>
> So the corrected law is: **ruin supply saturates eventually, but the RATE of
> claiming decides the split, and the split decides the game.** Everything the
> paragraph below retires — remembering ruins, sharing them over comms,
> exploration heuristics — is **re-opened**.

*Original text, kept for the record:*


Across every trace, the tower column decides the game (16 v 2 on Mirage;
8 v 6 twice). Towers produce the binding resource, so everything else is
downstream. Both accepted iterations work by protecting or raising tower count,
and the two rejects lost by suppressing it.

But tower count is capped by the **map's ruins, not by finding them**: healthy
bots build out to saturation (Mirage 22 ruins → 10 + 11 towers; Racetrack 14 →
8 + 6). So an entire family of ideas — remembering ruins, sharing ruin locations
over comms, exploration heuristics — is dead, and iteration 9 proved it for the
cost of one match. **Tower-count *differences* come from failing to build on
available ruins**, i.e. from the absorbing state (§3c) or from immobile soldiers,
never from failing to find them.

Corollary for ranking any economic idea: **a tower is worth 5-15 paint/turn plus a
spawn point plus 500 starting paint. An SRP is +3/turn per tower.** Anything that
trades tower-building time for something else needs to clear that bar, and
iteration 10 only worked once it was gated behind tower saturation.

## 3e. PARTLY RETRACTED — movement is still exploration, but the paint
## decomposition below is WRONG (see the paint-budget census)

> **RETRACTION (iteration 22 census, `alice_pbudget`, box + UnderTheSea, exact
> accounting to 200/soldier).** The claim "a soldier converts only ~8 of its 200
> paint into painted tiles (~1.6 paint actions per lifetime); ~192 goes to
> upkeep" is **false by an order of magnitude**. Measured: a soldier performs a
> **median of 20 paint actions** of the 40 its tank allows, and upkeep is
> **40–42%** of the budget, not 96%. The prediction that this would be retracted
> was recorded before the run. The *conclusion* of 3e — that standing still to
> save upkeep loses because it stops finding ruins (iteration 8, towers 6 v 8) —
> **stands**; only the arithmetic under it was wrong.



Measured: a soldier converts only ~8 of its 200 paint into painted tiles (~1.6
paint actions per lifetime); ~192 goes to upkeep. Upkeep looks self-inflicted,
because the engine charges **0 on an ally tile** and −1/−2 otherwise, so a soldier
standing on its own paint could live indefinitely.

Iteration 8 acted on that and lost by 145‰ while cutting deaths 52% and starvation
deaths 70%. The cause was one column: **towers 6 v 8**. A soldier that stands still
never finds a ruin. So the −1/turn is the *price of exploration*, and exploration
buys tower income, which is worth more than the tiles the paint would have bought.

This is the algorithm's "survival bought with inactivity" written in this year's
units, and I walked into it having read the warning. **Halving a death rate is not
evidence of anything until the tower/economy column is checked.**

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

**Reject on a trace when the mechanism is unambiguous — it costs a match, not a
run.** Three candidates died this way (mopper reserve dose 200, iteration 8's
standstill, iteration 9's ruin memory) and one was *refined* three times the same
way (iteration 10a→b→c, thrash → displacement → win). Each step was chosen from a
specific trace column, never from a parameter search. The rule that makes it safe:
only reject on a trace when the mechanism demonstrably engaged and the outcome is
clearly negative — otherwise run the sweep.

**Run your own pre-registered reachability check before writing the code, not
after.** I pre-registered "count how often a soldier has no ruin in vision but a
remembered one — if rare, this is dead code", then built iteration 9 first. The
answer (21 of 22 ruins already built) was sitting in replays I already had.

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
- **Noise bands — SUPERSEDED, these were binomial.** The old table ("13-15/24
  inside noise, 16/24 ~92%, 17/24 ~97%", and the 50-game equivalents) assumed
  per-game randomness this engine does not have, and got readings wrong in
  *both* directions (see the deterministic-uncertainty theme below). **Use
  `../../tools/map-resample.py <run-dir>`** — bootstrap and jackknife over the
  run's own per-map results — and quote its interval, never a formula.
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

---

## 6. The self-referential blind spot, caught in the act

This is the most important thing this lineage has learned, and it cost eleven
iterations and a 95.8% self-measured win rate to learn.

**What happened.** Iteration 9 tested "remember unbuilt ruins", saw tower count
fail to rise (10 v 11 on Mirage), and closed *the entire family* of
find-more-ruins ideas — memory, comms-shared ruin locations, exploration
heuristics — with the conclusion "ruin supply, not discovery, caps tower count".
The evidence was real. The measurement was correct. The conclusion was wrong.

**Why it was wrong.** Every opponent in that measurement descended from alice, so
every opponent shared alice's defect: soldiers that only react to ruins inside
vision (r²=20) and random-walk otherwise. Both sides were equally bad at
*arriving*, so ruins were consumed slowly and evenly, and the map saturating late
looked exactly like a supply ceiling. **A defect the whole pool shares is
invisible to the whole pool.** It does not show up as a loss, or a bad metric, or
a suspicious trace. It shows up as nothing at all.

**What broke it open.** One tournament against two independently-developed bots.
`bob` beat alice 143-7 while alice beat `carol` 55-26 — alice was not weak, it was
missing one capability. Two of the three lineages had converged on the same trap,
which is itself the lesson: the trap is what a bot *naturally grows into* from a
reactive `senseNearbyRuins` soldier, so a lineage cannot be expected to find its
way out by looking at itself.

### The transferable rules

1. **A conclusion of the form "X does not matter" is only as strong as the
   *diversity* of the pool that produced it.** "Our opponents don't punish X" and
   "X doesn't matter" are different claims, and a self-descended pool cannot tell
   them apart. Write down which one you actually measured.
2. **Retiring a whole family of ideas is a much bigger claim than rejecting one
   implementation.** Iteration 9 tested *one* mechanism (memory) and retired
   *four* (memory, comms, exploration, sharing). One mechanism failing its gate is
   evidence about that mechanism.
3. **A ledger entry needs a re-open condition, and the condition must be checkable
   by someone who does not already believe the entry is wrong.** Iteration 9's
   was: "a map class exists where ruins are not saturated by mid-game — check the
   ruin count against final tower totals before believing it." That condition is
   exactly what the tournament satisfied, and it is the reason re-opening was
   disciplined rather than a hunch. **Write the re-open condition when you close
   the direction, not when you want to re-open it.**
4. **When an external instrument finally arrives, spend it on your oldest
   confident beliefs, not your newest uncertain ones.** The 4.7% did not point at
   the iteration I was working on (SRPs); it pointed at a conclusion I had been
   treating as settled fact for three iterations.
5. **A rising win rate against your own history is not evidence of strength.**
   alice's frozen-roster instrument read 95.8% the same week alice went 7-143.
   Both numbers are correct. Only one is about strength.

---

## 7. A pinned resource is only pathological if capacity sits idle behind it

The algorithm names "resource pinned in a dead band" as a degeneracy signal to
prefer over opponent-relative comparisons. It is a good signal, and I misread it
in a way that is easy to repeat, so here is the discriminator.

**What I saw.** On a mirror game (identical code both sides, so the curve is a
property of the policy) the treasury oscillated in **$650-1410 for 600 rounds and
never once reached the `CHIP_RESERVE = 1450` spend gate**. Textbook dead band.
I lowered the gate to its principled tight bound. It scored **11/24 against a
measured mirror null of exactly 12/24** — one game *worse*.

**Why it was not a defect.** A stock pinned *just beneath a spend threshold* is the
**equilibrium signature of a converter that is already spending everything above
that threshold**. Income arrives, the stock crosses the gate, a purchase fires,
the stock falls back. On a trace this is **indistinguishable from starvation** and
it means the opposite: the gate is not blocking spending, it is *defining* the
buffer, and lowering it only shrinks the guarantee the buffer exists to provide.

### The discriminator, in general form

> A threshold on a resource is pathological **only if capacity that the resource
> would buy is sitting idle behind it.** Check the *complementary* input, not the
> pinned one.

- Pinned stock **+ idle complementary capacity** → the gate may really be blocking
  conversion. Worth a dose.
- Pinned stock **+ everything downstream busy** → the pin is a working converter
  at equilibrium. Leave it alone.

**Applied to my own case, this would have redirected me before I spent the run.**
Capacity *was* idle — **4,885 tower paint**. But a spawn costs **250 chips *and*
200 paint**, so paint piling up while chips stay pinned proves **chips are the
binding input and paint is the abundant one**. The idle paint was evidence about
the *production mix* (a fixed ~50/50 money/paint tower split chosen by ruin
parity), not about the chip gate. I attributed idle capacity to the wrong input.

### Two smaller lessons that came with it

1. **Name the complementary input before proposing the fix.** "X is pinned"
   is half a diagnosis. "X is pinned *and* Y bought with X is idle" is a whole one.
2. **This is why the mirror null matters.** Under binomial reasoning 11/24 reads
   "slightly below even, within noise" and the result is ambiguous. Against a null
   with **no variance** it reads "this change cost exactly one game" — a small,
   *unambiguous* negative. A deterministic null turns a shrug into a measurement.

## Theme: a policy keyed on map geometry needs a map that exercises both branches

I spent an iteration on a "latent bug" that did not exist. The whole thing
collapses to one sentence:

> **`gridworld` has no odd-parity ruins, and my tower-type rule keys on
> `(x+y)&1`.** So on the only map I traced, the paint branch was dead code —
> and I read "the paint branch produces nothing" off it.

The generalisation is not about parity or about ruins.

> **Before tracing a branch on a map, confirm that map actually produces the
> input that takes the branch.** A conditional keyed on map geometry —
> coordinates, symmetry, ruin/wall placement, distances, counts — has a
> *reachability* precondition that varies **per map**, not just per game state.
> §3's reachability pre-check asks "is this branch ever taken"; the sharper
> question is "**is it taken on the map I am about to measure it on**".

Three concrete tells I now check:

1. **Census the branch, not the outcome.** My census counted tower *completions*
   by type and found zero paint towers. Had it counted `wantTower` *decisions*
   it would have shown 22,092 MONEY / 0 PAINT and the answer would have been
   immediate. **Instrument the decision upstream of the effect** — a zero at the
   output cannot distinguish "the mechanism failed" from "the mechanism never
   ran". This is the same distinction as §4's classification 2 vs 3, applied to
   diagnosis rather than to a candidate.
2. **A corpus statistic hides per-map degeneracy.** Across the 75 maps the ruin
   parity split is 732/642 — near-perfectly balanced, which is exactly why I
   never thought to check it. Three individual maps are 100% even. **The mean of
   a map property tells you nothing about the map in front of you.**
3. **Two arms on two *sides* of one map is not a comparison.** I read 12-v-6
   tower counts as a code effect. Re-running with byte-identical code on both
   sides reproduced 12-v-6 exactly: it was positional. Phase 0 §7 says a
   persistent lopsided split in a mirror is a real bug; the corollary I missed is
   that **any cross-team count on a single map must be quoted against the mirror
   before it can be read as an effect of the code.** I had the mirror null
   already computed and did not consult it.

### The retraction was worth more than the iteration would have been

Refuting my own claim produced a firmer result than the claim would have: forcing
all-MONEY loses **5/20 (25%)** on the maps where the branch is live. I nearly
deleted a feature worth 75-25 because the map I chose could not see it. The
ledger entry that says "this direction is closed, and here is the number" is the
asset — not the iteration I thought I was running.

## Theme: a contested quantity sits at an equilibrium — measure throughput, not level

Iteration 19 made moppers clear the enemy paint that blocks tower patterns. The
metric I pre-registered as the mechanism gate barely moved:

| | gridworld | UnderTheSea |
|---|---|---|
| % of ruin-targeted soldier turns with enemy paint in the pattern | 35.8% → **36.1%** | 81.2% → **81.4%** |
| near-stall samples (≥20/24 done, soldier at the ruin) | 724 → **358** | 1,714 → **465** |
| ruin-targeted soldier turns in total | 22,092 → **18,604** | 6,477 → **3,130** |

Both readings are correct and they are not in conflict.

> **A quantity both sides act on settles at an equilibrium level, and clearing it
> faster raises the flow through it without moving the level.** The opponent
> repaints as fast as I clear, so the *fraction of ruins blocked* is pinned. What
> changes is how long each individual blockage lasts — visible as fewer soldier
> turns spent stalled, not as fewer blockages.

This generalises past this iteration. Coverage is contested (LEARNINGS §2 already
says so). So is map control, so is any stock the opponent can subtract from. For
all of them:

1. **Pre-registering a *level* as the mechanism gate is a mistake when the
   quantity is contested.** I nearly failed a working mechanism on its own gate.
   The right pre-registration is a rate, a duration, or a count of the *state
   being exited* — "how many turns are spent blocked", not "how often is
   something blocked".
2. **The tell is that the level is flat while a downstream count moves a lot.**
   Flat level + halved stall count + fewer total turns is not a contradiction and
   not noise; it is the signature of a throughput change under a pinned level.
3. **It is also the reason a mechanism can be real and still small.** Raising
   throughput through an equilibrium buys the difference in flow, not the whole
   stock. Iteration 19 gained exactly +1 tower per map over the mirror null —
   consistent with a genuine but bounded effect, and I recorded that prediction
   before the evaluation returned rather than after.

The corollary for design: **if you want the level to move, you must change who
supplies the quantity, not how fast you consume it.** That is why iteration 20 —
soldiers refusing to commit to blocked ruins — is a different mechanism and not
a refinement of 19: it does not fight the equilibrium at all, it stops paying
for it.

## Theme: removing waste pays only when the freed resource is the scarce one

> **THIRD OCCURRENCE, 2026-09-08 (iteration 39a).** This entry did not fire, again. See
> "a lesson written THREE times is not a lesson, it is a missing control" below; the check
> now prints from `tools/gate-read.sh` on every verdict read.

Iterations 19 and 20 attacked the *same* measured waste from opposite sides,
against the same baseline, on the same map sampler. One accepted, one landed on
the null to the game.

| | mechanism | measured engagement | result |
|---|---|---|---|
| iteration 19 | moppers **clear** the enemy paint blocking a pattern | near-stall samples halved | **ACCEPT** 15/24, swept 3–0 |
| iteration 20 | soldiers **avoid** ruins they cannot finish | blocked-ruin turns −10 to −19 pts, total ruin turns −27% / −57% | **REJECT** 12, 12, 13 of 24 |

Iteration 20 engaged *harder* than 19 and bought nothing. The rule that explains
the pair:

> **Removing a waste frees a resource. It pays only if that resource was the
> binding constraint.** Unblocking a pattern *adds a tower*, because the blocked
> tile was what stopped the tower existing. Avoiding a blocked ruin merely
> *relocates a soldier whose paint is already spent* — it frees turns, and turns
> were never scarce.

Engine arithmetic makes the constraint explicit: `SOLDIER.attackCost = 5` against
a 200 tank (verified — `soldierAttack` calls `addPaint(-attackCost)`), so a
soldier has **exactly 40 paint actions in its entire life** against a 24-tile,
120-paint pattern. Handing it more *turns* to spend an exhausted *budget* is a
no-op by construction.

### How to tell the two cases apart BEFORE spending the run

1. **Name the freed resource, then ask what else it is short of.** "Soldier
   turns" freed by iteration 20 were immediately re-spent painting ground with
   paint the soldier did not have. The freed resource has to be convertible into
   the thing you are short of, or the conversion is where it dies.
2. **A flat level on the master variable is the tell, and it is visible in the
   mechanism run.** Tower count did not move in either of iteration 20's
   mechanism games. I recorded that as a damning caveat before the evaluation
   returned; it predicted the null exactly. **A mechanism check that moves its
   own metric but not the master variable has already told you the answer.**
3. **This is the "metrics that improve without converting" pattern with a
   mechanism attached.** The 2026 project logged five mechanism-verified damage
   increases converting to nothing. The addition here is *why*: damage, like
   turns, was not the binding input.

### The rejection was worth more than a marginal accept

Iteration 20 cost 72 games and converted a plausible belief — "wasted soldier
turns cap tower count" — into a measured falsehood, while promoting its
pre-registered falsifier into the next target. **Soldier paint is the binding
constraint, and I now know that rather than suspect it.** A 13/24 accepted on
enthusiasm would have bought a marginal feature and left the belief intact.

### Consistency pass, 2026-09-07 — this theme had only its negative case

Found by comparing entries rather than re-reading them: **this section states the
rule and gives one example of it failing (iteration 20) and one of it succeeding
in a different resource (iteration 19), but never records the case that proves it
in the resource the section itself names as binding.** Iteration 22 is that case,
and the two entries had no reference to each other until now — the exact "two
rules that ought to cite each other and never do" tell this document extracted
from its previous pass.

| | freed resource | was it the binding one? | result |
|---|---|---|---|
| iteration 19 | a blocked pattern tile | yes — it was what stopped the tower existing | ACCEPT 15/24 |
| iteration 20 | soldier **turns** | **no** — turns were never scarce | REJECT, 12/24 at zero variance |
| **iteration 22** | soldier **paint** — 24–36% of the 200 tank | **yes — the constraint this very section names** | **ACCEPT 19/24, then 33/50 on fresh maps** |

The rule predicted this correctly and in advance, which is worth more than the
accept: *"removing a waste pays only if the freed resource was the binding
constraint"* plus *"soldier paint is the binding constraint"* entails that
removing a **paint** waste should pay. It did, at +7 and +8 games on two disjoint
map samples. **Both halves were already written down; nobody had put them side by
side.** The follow-through is the discipline this pass is for: when a section
records a rule and a failure, go looking for the success it predicts, because if
you cannot find one the rule is not yet load-bearing.

Cross-reference added: the mechanism by which iteration 22's paint was being
wasted is in the theme **"the engine DEBITS before it CHECKS"** below.

## Theme: in a deterministic game, the MAP is the unit of uncertainty — never the game

I quoted an interaction's noise as `sqrt(4 × 24 × 0.25) = 4.9` games. That is a
binomial sd, and **binomial assumes per-game randomness that this project
established does not exist.** The engine is deterministic and so are both
builds, so every `(map, side)` cell is a fixed function of the two programs.
Re-running is worthless (Measurement doctrine #1 already says so) precisely
*because* nothing is random per game.

> **The only thing that varies between two estimates is which maps were drawn.
> So the map is the observation, and uncertainty comes from resampling maps —
> bootstrap or jackknife over the run's own per-map results.**

Doctrine #1 and the binomial noise floor were quietly contradicting each other,
and I had been using both for a whole session without noticing.

### It is not a conservative approximation — it is wrong in both directions

| quantity | binomial sd | map-resample sd | effect |
|---|---|---|---|
| iteration 21 interaction (−2 games) | 4.9 → 0.41 sd | **2.4** → **0.84 sd** | binomial **overstated** spread ~2×, so I called a result "comfortably" inside noise when it is 0.84 sd |
| iteration 19 arm A (15/24) | "p = 0.154, inside the 13–15 noise band" | **1.5** → **+2.00 sd**, CI [12, 18] | binomial **under-sold a real accept**; I hedged a 2-sd result |
| iteration 20 `p5`, `p10` (12/24) | "≈ 50%, indistinguishable" | **se = 0.00**, CI [12, 12] | every map split 1–1: **identical to the null on every map, both sides** |

Deterministic per-map outcomes are *concentrated*, not coin-flip-like — eight of
twelve maps contributed exactly 0 to the interaction. Structure has lower
variance than independence, which is why binomial ran wide here. But it can also
run narrow: a change that flips whole maps one-directionally has *more*
map-level variance than binomial would predict.

### Three consequences I am adopting

1. **Swept maps were accidentally the right statistic all along.** A swept map is
   the map-level unit that resampling treats as the observation, which is why
   "swept 3–0 against a zero-variance null" carried iteration 19 correctly even
   while my stated reasoning about it was wrong. Prefer map-level statistics.
2. **`se = 0` is a real and very strong reading.** When every map splits 1–1 the
   candidate is not "statistically indistinguishable" from the baseline — it is
   *identical in outcome on every cell measured*. That is a far harder rejection
   than a win rate near 50%, and it deserves to be reported as such.
3. **Automate it so the wrong model cannot come back.**
   **`../../tools/map-resample.py` — shared ground** (promoted in `eb99f33`;
   the rule is in MULTI_AGENT.md for all three lineages). Computes bootstrap +
   jackknife over maps from any run's `results.csv`. Quote it instead of a
   formula, and do not keep a copy here — a duplicated tool goes stale exactly
   the way a forked archetype does.

**The general form**: *before* attaching an uncertainty to a number, ask what
would have to be re-rolled to get a different one. If re-running the same games
cannot change the answer, per-game randomness is not the source of your error
bars, and any formula that assumes it is describing a different experiment.

## Theme: two rules in one document can disagree, and neither looks wrong alone

Prompted by the coordinator after the binomial correction: a periodic
**consistency pass** over this file, rather than only appending to it. The first
pass found three, and the first one is the sharpest.

### 1. The right method and the wrong one, side by side, in the same section

§4 says *"Don't pick the arm that won by less than the noise floor"* — and the
reasoning it actually uses is **cell disagreement**: iteration 5's two doses
"disagreed on *three* of the 27 (map,side) cells they both played". **That is the
deterministic method.** It counts cells that actually differ, which is exactly
what map resampling formalises.

Eight lines later, §5 stated the binomial noise band ("13–15/24 is inside
noise") as live guidance. **I had the correct model and the incorrect model in
the same document, in adjacent sections, for the entire session** — and quoted
the wrong one all the way through iterations 19, 20 and 21.

> **Neither entry looks wrong in isolation.** That is the whole failure mode. A
> per-entry review passes both; only *comparing* them fails. Append-only notes
> accumulate contradictions silently, because every check is local.

The binomial band is now marked superseded in place, pointing at
`../../tools/map-resample.py`. Superseding beats deleting: the wrong rule was
load-bearing for months of reasoning, and a reader of the old entries needs to
know it was withdrawn and why.

### 2. Measurement doctrine #1 versus the noise floor

The governing document says re-running is worthless *because the engine is
deterministic*. My own noise floor assumed per-game randomness. **A rule that
says "there is no per-game randomness" and a rule that says "here is your
per-game randomness" cannot both be right**, and I used both without noticing.
The tell I now watch for: *a rule about determinism and a rule about noise, in
the same project, that never cite each other.*

### 3. §3e "movement is exploration" versus iteration 20 "turns are not scarce"

These read as contradictory and are not — but only for a reason worth writing
down. §3e's movement buys **reaching ruins that were never reached**; iteration
20's freed turns were re-spent *locally*, on ruins already in vision, by soldiers
whose paint was already gone. **Movement that expands the reachable set buys
towers; turns handed back inside the set already explored buy nothing.** The
resource freed has to be convertible into the thing that is scarce — the same
rule as the waste-removal theme, arriving from a different direction.

**Flagged as an open inconsistency rather than resolved**: §3e also claims a
soldier converts "~8 of its 200 paint into painted tiles (~1.6 paint actions per
lifetime); ~192 goes to upkeep". That is hard to reconcile with a median of 18
paint remaining *at a ruin* after a soldier has been painting a pattern. One of
the two numbers is wrong, and `alice_pbudget` — which decomposes the 200 by
action class with upkeep as the exact residual — is built precisely to settle
it. **Recorded as a pre-registered prediction: I expect §3e's decomposition to
be retracted.**


## Theme: the engine DEBITS before it CHECKS — verify the predicate, not the proxy

The most valuable thing this lineage found in a day, and it was found by
decompiling rather than by reasoning.

`javap -c battlecode/world/InternalRobot.class`, `soldierAttack`:

```
 58: invokevirtual addPaint:(I)V      <-- -5 paint, UNCONDITIONAL
170: isPaintable(loc) ... ifeq 231    <-- bail out, after the debit
207: teamFromPaint(mine) != there -> return   <-- ENEMY PAINT: bail, after the debit
210: setPaint(...)                    <-- only reached for empty-or-ally
```

**A soldier attack aimed at an enemy-painted tile costs the full 5 paint and does
nothing.** `canAttack` does not protect you: it checks range and action-readiness,
never the tile's paint. Combined with §2's saturation finding — 97.7% of the map
painted, so a non-ally tile is overwhelmingly an *enemy* tile — this was the
largest paint leak in the lineage.

### The generalisable rule

> **When a guard is a proxy for what the engine actually tests, it is a bug
> waiting for the distribution to shift.** `!paint.isAlly()` and
> `paint == EMPTY` agree while the map is mostly unpainted, and diverge
> completely once it saturates. The first is a proxy; the second is the
> engine's own predicate. Write the engine's predicate.

Iteration 22 is the demonstration, and it is unusually clean because both
branches drew on the **same** budget in the **same** turn:

| branch | guard | 2x2 price |
|---|---|---|
| paint the tile underfoot | `!here.getPaint().isAlly()` — a **proxy** | **−7 games** |
| paint the nearest empty tile in range | `t.getPaint() == PaintType.EMPTY` — the **engine's predicate** | **+6 games** |

Removing both scored **0/24** at zero variance: they are the only paint that ever
reaches ground outside a tower pattern, so they are complements. **A 13-game swing
between two branches of the same method, decided by one predicate.**

### It recurred in a PRE-REGISTRATION, which is the worst place for it (2026-09-07)

The rule above is written in my own words in `tools/engine-facts.md`. I then wrote
an iteration-24 accept gate on the proxy **"enemy paint"** when the engine's charge
is on **every non-ally tile** — a mopper pays -4 on enemy and **-2 on EMPTY**. Empty
tiles sit under my moppers four times more often than enemy ones, so the gate
measured 9.0% where the engine's own predicate measures **33.3%**.

Two things make this worth its own entry rather than a footnote:

- **A proxy in a gate is more dangerous than a proxy in a guard.** A bad guard
  loses paint and shows up in a trace. A bad gate **silently mis-scores the
  hypothesis** and the loss is invisible — I would have recorded "measured, dead"
  and moved on, with a number that was correctly computed against the wrong thing.
  That is the wrong-referent error (doctrine 5) reaching the measuring instrument.
- **The fix is only legitimate because the rule pre-dates the data.** Rescoping a
  gate after seeing the number is normally fishing. It is defensible here *only*
  because the predicate was written down before the gate was, and the original
  hypothesis stays rejected on its own terms rather than being rescued.

**Practical form: when pre-registering a threshold on an engine-charged quantity,
quote the engine's charge table into the pre-registration.** Had the three-row
table (ally 0 / empty -2 / enemy -4) been sitting in my gate, the omission of
"empty" would have been unmissable.

### Two corrections this forces on my own reasoning

- **I priced the wrong thing and got the right answer.** I costed the underfoot
  branch as a bad *upkeep rebate* (`saved/spent` = 0.039–0.052) and that number is
  real, but the dominant channel was the refused attack. The replay says so:
  starvation deaths fell from 30–42 to 8–11 per 250 rounds. **Being right about
  the sign is not being right about the mechanism**, and only the mechanism
  transfers to the next iteration.
- **"Cannot do X" in a spec digest must be paired with "and here is what trying
  costs".** `RULES.md` had "Cannot overwrite enemy paint" from early on. It was
  true and it was useless, because the expensive half was the price of the attempt.
  I have added the debit as a TRAP beside the `transferPaint` clamping one.

## Theme: an instrument that samples positions your current policy chooses cannot price a policy that chooses different positions

`alice_splashcensus` counted, every soldier turn, the best 13-tile splash blast
reachable from where the soldier stood — a proper *decision* instrument, sampled
2,402 soldier-turns across two windows, and stable to two decimals (mean 1.37
tiles of 13, both windows). Break-even for a splasher is 10 of 13. Read at face
value it kills the unit by a factor of seven.

**It does not, and the tell was in the column I nearly did not print**: 94–98% of
the non-ally tiles in those blasts were **enemy** paint. The blast was empty of
*legal soldier targets* because soldiers stand inside their own finished paint.
The census priced "a splasher standing where a soldier chose to stand", and the
entire case for a splasher is that it would stand somewhere else — at the border,
where it can convert 9 enemy tiles in one action.

> **Before trusting a decision census, ask who chose the sample points.** If the
> current policy chose them, the census measures the marginal value of the new
> capability *inside the old policy's habitat*, which is the one place a
> capability-adding change is least likely to pay. The fix is to sample positions
> the new policy would visit, or to state the bound honestly and leave the
> question open.

Recorded as **open, not closed**: the splasher is neither justified nor refuted.
Putting it in the closed-directions ledger on this evidence would be exactly the
error above.

## Theme: never dichotomise a continuous covariate — the split invents the effect

Paid for on 2026-09-07, within two hours of building the instrument that did it.

I wrote `tools/density-split.py` to partition a run's 25 maps at the corpus median
ruin density, because several of my mechanisms are ruin-related and the corpus
spans a 4.8x density range. It reported iteration 22 at **+6 games over the null
on the sparse half and +2 on the dense half**, I called that "suggestive, not
decisive", and I wrote several hundred words about being unable to explain its
direction. At full resolution — Spearman's rho against density, permutation-tested
— the accept-gate opponent gives **rho = −0.093, p = 0.673**, and the other four
opponents give 0.15 to 0.99. **There was no effect to explain.**

> **A median split discards the ordering within each bin, so the difference
> between the bins rides on which side of an arbitrary cut a handful of
> observations happened to fall.** With 14 maps against 11, moving two across the
> line moves the headline by several points. Use the rank correlation, which uses
> every observation's position and cannot be moved by the cut.

### The part that is about me, not about statistics

I **flagged** the result as under-powered and then reasoned about it anyway, at
length, including constructing a mechanistic story for why it contradicted my own
model. The correct next step was five lines of code.

> **Flagging uncertainty is not a substitute for resolving it when resolving it is
> cheap.** A hedge in the prose does not make an artifact less of an artifact; it
> only makes the retraction politer. If a caveat is worth writing, first ask what
> it would cost to delete the caveat by measuring.

This is the same failure the project already records in another register —
*"prefer a measurement to an argument when two entries disagree"* — and it should
have cited that entry. Cross-referenced now, in both directions.

### The fix went into the instrument, not into my memory

`density-split.py` computes rho **first**, labels it PRIMARY, prints the split
underneath marked DESCRIPTIVE ONLY, and carries the whole story in a source
comment. A lesson that lives only in a log entry has to be remembered by whoever
next runs the tool; a lesson compiled into the tool's output does not.

## Theme: when a covariate analysis fails twice, stop correlating and go price the code path

Iteration 23 changed one clause that does two things at once: it stops paying 5
paint for an engine-refused attack, **and** it `continue`s, so the soldier scans
onward and lands on a paintable tile further along the same pattern. I tried
twice to separate them with map-level covariates, and both attempts failed:

| attempt | variable | rho | p |
|---|---|---|---|
| pre-registered | ruin **density** | +0.318 | 0.127 |
| post-hoc rescue | absolute ruin **count** | +0.104 | 0.640 |
| (control) | map **area** | −0.116 | 0.606 |

The pre-registered prediction had the **wrong sign**. The post-hoc replacement,
built specifically to fix that, performed **worse than the thing it replaced**.

### Three rules, in the order they cost me something

**1. A post-hoc explanation earns exactly one thing: the next test.**
When the density prediction failed I constructed a tower-conversion story that fit
the data, and it was a *good* story — the replay backs it (18 towers vs 9). But I
named its sharper prediction and ran it within minutes, and it died. Had I written
the story down without testing it, it would have sat in this file beside a null it
"agreed with", survived because nobody re-checked it, and been quoted three
iterations later as established. **That is exactly how this project once ended up
with the wrong and right models eight lines apart.**

**2. A null with a point estimate is not a trend, and "agrees with my story" is
not evidence.** rho = +0.318 at p = 0.127 is a null. I caught myself writing that
"two independent readings now agree" when one was that null and the other was a
single game. Superseded in place.

**3. When the correlational route fails, the answer is a game experiment, not a
better covariate.** §5b already says it: **an ablation prices a CODE PATH, not a
concept.** The separating arm is `src/alice_i23abl`, which differs from the
candidate by **one keyword** — `break` instead of `continue`. That is a cleaner
instrument than any regression over 25 maps, because there is no question about
what was gated.

### The generalisable shape

> **Cross-map variation can only separate two mechanisms if they scale with
> different map properties.** When two co-occurring effects both scale with
> "how much of the game this branch runs", no covariate will split them, and
> hunting for a better one is a way of avoiding the experiment that would.

And the corollary, which is the useful part: **a change with no detectable
covariate structure is not a weak result — it is a uniform one.** Across a 4.8x
ruin-density range and a 6x area range, iteration 23 swept 9 maps and lost none
from both sides. "Works everywhere" is the strongest shape a change can have for a
bot that must play an unknown map, and it is the same fact the swept-map count was
already reporting in a different language.

## Theme: enumerate the cases, then COUNT them — a case analysis has no frequencies in it

Two things happened within an hour of each other, and together they make the rule.

**The win.** Iteration 22's mechanism attribution was marked OPEN under the loop's
step 3b. Rather than spend a run separating it, I enumerated the four possible
states of the tile the deleted branch acted on, and found that **two of them are
byte-identical between the two builds** — because the surviving area branch scans
`r²<=9`, which includes distance 0, and picks the nearest empty tile with a strict
`d < paintD`, so a d = 0 empty tile always wins. That left exactly one gaining row
(the engine trap) and one losing row. **The attribution closed for zero games**,
and it closed *falsifiably*: I named the case that would break it (show the area
branch can miss a distance-0 empty tile) and checked the three ways it could occur.

**The miss, in the same table.** I labelled the losing row *"a real loss that
iteration 22 accepted without noticing"* and built a candidate to recover it. The
decision census then found the state occurs **zero times in 4,331 action-ready
soldier turns** — because the map is ~90% painted by round 300, so a soldier is
essentially never standing on empty ground.

> **A case analysis tells you which behaviours DIFFER. It contains no information
> about which of them ever HAPPEN.** Those are different questions and the second
> one is empirical. Enumerating four rows and then reasoning about a non-identical
> row's size is smuggling a frequency claim into a logical argument.

### The rule, and the two halves it joins

1. **Enumerate** — it is cheaper than any run, it closes attributions that an
   experiment would cost 100 games to settle, and the rows that come out *not*
   identical are exactly the behaviours nobody deliberately chose.
2. **Then count each surviving row** with a decision census, before believing any
   of them matters. This is the existing reachability pre-check, and I did not
   think to apply it to my own enumeration — I only ran it because one row had
   become a candidate in its own right.

Note the payoff runs both ways: the census **killed the candidate** and
**strengthened the closure**. With the losing row measured at zero, iteration 22's
deletion is not a large gain traded against a small loss — it is a pure removal,
with three of four rows contributing exactly nothing.

### And the correction ran in my favour, which is the dangerous direction

"The loss I identified is actually zero" makes my accepted iteration look better.
That is precisely the kind of correction that never gets made, because nothing
prompts it. It got made here only because the row had been promoted to a candidate
and candidates get pre-checked. **Findings that flatter you need the same
pre-checks as findings that do not** — and they will not ask for them.

## CONSISTENCY PASS — three of today's themes are one theme, and none cited the others

Run as the algorithm's Logging section requires: *compare* entries rather than
re-read them, and treat **two rules that ought to cite each other and never do**
as the tell. Four themes were added to this file today. **None of them referenced
any of the others.** Comparing them, three are the same failure wearing different
clothes:

| theme | the analysis was | what it never asked |
|---|---|---|
| *"an instrument that samples positions your current policy chooses…"* | a correct decision census, 2,402 turns, stable to two decimals | **from which positions?** — the old policy's, which is where a new capability is least likely to pay |
| *"enumerate the cases, then COUNT them"* | a correct, exhaustive, falsifiable four-row case analysis | **how often is each row taken?** — one row turned out to occur **0 times in 4,331 turns** |
| *"when a covariate analysis fails twice…"* | a correct rank correlation with permutation p-values | **do the two mechanisms occur at different rates across maps?** — they do not, so no covariate could ever separate them |

### The unifying rule

> **Every one of these was a valid analysis that was silent about FREQUENCY.**
> Logic tells you which cases differ; statistics tells you whether a difference is
> real; **neither tells you how often the case arises**, and that is a separate,
> empirical, usually cheap measurement. When an argument turns on "this situation
> matters", the sentence after it must be a count.

Which is the project's existing **reachability pre-check**, generalised. That rule
was written for dead code branches — *"is the branch this reasoning lives in ever
taken?"* — and I applied it faithfully to branches all day. **What I did not do is
apply it to my own analyses**, which are just as capable of describing situations
that never arise. A census, an enumeration and a correlation are all reasoning
that lives in a branch.

### And it explains the fourth theme rather than sitting beside it

*"Never dichotomise a continuous covariate"* looks like a separate statistical
point, and it is — but its damage came the same way. A median split reports a
difference between two bins **without reporting how the observations are
distributed within them**, so it hides the frequency information that would have
shown there was no trend. Same failure: a summary that suppresses the count.

### Cross-references added, in both directions

- *"samples positions"*, *"enumerate then count"*, and *"covariate analysis fails
  twice"* now name each other as the same failure class, and all three name the
  **reachability pre-check** as their parent rule.
- *"never dichotomise"* names *"covariate analysis fails twice"*, which is the
  entry that produced its evidence.
- *"the engine DEBITS before it CHECKS"* is the odd one out and stays separate: it
  is a fact about the engine, not a failure of my reasoning about frequency, and
  conflating the two would blur the one entry that is verified by decompilation.

**Process note on the pass itself.** All four entries were written today, each
was checked when written, and each was individually correct. A per-entry review
passes all four. **Only comparing them fails** — which is precisely what this
document's earlier pass predicted would happen, and it happened within hours of
that prediction being recorded.

## Theme: head-to-head margins DO NOT CHAIN — measured, at cell level, in one line of code

The cleanest measurement this lineage has made, and the one with the widest reach.
Three builds differing by **one keyword**, all played on **one pinned 25-map
sample**, so the numbers below are an identity rather than an estimate:

```
  i23abl  beats  iter22   by +8      (33/50, swept 9/1)
  iter23  beats  i23abl   by +6      (31/50, swept 7/1)
  iter23  beats  iter22   by +8      (33/50, swept 9/1)   -- NOT +14
```

Parts sum to **+14** against a whole of **+8**. And the whole is not merely
*close* to the first leg — it is **indistinguishable** from it. Aggregates can
coincide by luck, so the deterministic cell check settles it: of the 50
`(map, side)` cells, **6 disagree, split exactly 3–3 across six different maps**.
That is the churn signature, not a causal effect. Against `iter22`, the second
keyword is worth **zero**, with the diff shape proving it rather than an aggregate
merely failing to detect it. Against `i23abl` the *same* keyword sweeps 7 maps
to 1.

> **"A beat B by 8" and "C beat A by 6" does not license "C beats B by 14".**
> A feature's value is a property of the **matchup**, not of the feature. The only
> way to know what C is worth against B is to play C against B, on the same maps.

### Why it happens here, and why the shape is general

Effect (2) — scanning past an engine-refused tile to a paintable one — only pays
against an opponent that has *already* stopped bleeding paint on refused actions.
Against one that is still bleeding, the race is not close enough for the
refinement to flip an outcome. **A refinement is worth something only when the
game is tight enough for refinements to matter**, and how tight the game is
depends on who you are playing.

### This is §5b's "partial derivative" measured rather than argued

§5b warns that the accept gate measures *"marginal value conditional on everything
the baseline already carries"*, and that a chain of individually-positive accepts
can walk downhill. That has been an argument in this project. **It is now a
measurement**: a feature worth +6 against my immediate predecessor is worth
exactly 0 against the generation before it, established at cell level in one line
of code.

Two consequences I am adopting:

1. **The frozen roster is not a nice-to-have; the arithmetic above is why it
   exists.** No chain of head-to-heads can reconstruct a level, because the links
   are not additive. Only a fixed opponent measures a level.
2. **When an ablation's parts do not sum, do not average them and move on.** The
   gap *is* the finding. Run the cell-disagreement check on the two arms that look
   equal — if they agree on ~90% of cells with the remainder split evenly, they
   are the same bot in that matchup, whatever the aggregate suggests.

### And a note on carrying a feature that measures zero

`iter23` keeps the clause even though it contributes nothing to today's margin,
because it wins the head-to-head that *is* the accept gate and costs nothing in
bytecode. That is a defensible call, but it is **an unpriced liability under §5b's
own warning** — a feature carried on a matchup-specific benefit is exactly the
half of a future destructive pair nobody thinks to suspect. Recorded here so that
if a frozen-roster reading ever drops, this clause is on the list of things to
ablate first.

## Theme: "supersede in place" must ANNOTATE the old entry, not merely append a new one

My logging convention is *supersede in place; do not delete*, so that decisions made
while a rule stood stay readable. That is right, and on 2026-09-08 it failed anyway,
in a way worth naming.

A session of my own lineage grepped my closed-directions ledger for `CHIP_RESERVE`,
found the **iteration 16** row, and quoted its re-open condition (*"the tower mix is
fixed first and chips shown to bind with soldiers idle"*) as met. But that row had
been **superseded two iterations later** by a stricter one (*"a change first raises
chip income"*) after three further measurements. Nothing at the old row said so. It
proposed a whole iteration on a rule that had been replaced.

> **An un-annotated superseded entry is indistinguishable from live guidance at
> exactly the moment someone is relying on it.** Preserving history is not the same
> as marking which version is current, and only the second protects a reader.

The rule I am adopting, and have applied retroactively:

- When superseding, **edit the old entry to carry an inline
  `[SUPERSEDED <date> — see <where>; that condition, not this one, is binding]`**,
  then append the new one. The old text stays intact; only a marker is added.
- Same for stale *figures*, not just rules — a number quoted in a themed lesson is
  guidance too. §3b's "realized mix is ~90% moppers" was true when written and is
  now 78.6% *soldiers*; it now carries a correction banner rather than being
  silently right-for-its-era.
- **The tell that you need this**: append-only history plus a grep-shaped reader.
  Anyone searching by keyword lands on whichever entry matches first, not on the
  newest, so recency cannot be conveyed by position in the file.

This is the same family as the caveat lesson elsewhere in this document: there, a
caveat protected only the dimension it named; here, a supersession protected only
the reader who arrives in chronological order. Both fail the reader who arrives
some other way, and that is the normal way people arrive.


## Theme: a REPLAY's per-robot state is post-decision by construction, so it cannot price affordability

Doctrine already says *instrument the decision, not the outcome*, and I had read
that as being about where to put an in-bot counter. On 2026-09-08 it bit me from a
direction I had not considered: a statistic derived entirely from the **replay**,
with no in-bot instrument at all, was post-decision by construction.

I traced a tower's paint with `replay-dump --robot <id>` and crossed it with team
money to ask "how often could this tower afford each unit":

| unit | cost | ends turn with paint >= cost | AND money >= reserve |
|---|---|---|---|
| MOPPER | 100 | 59.6% | 32.50% |
| SOLDIER | 200 | 10.3% | **0.10%** |
| SPLASHER | 300 | 5.3% | **0.05%** |

That reads as a spectacular result — a soldier affordable on one turn in a
thousand, the absorbing state finally measured. **It is an artefact.** The replay
records each robot's state *after* its turn, so the paint is **post-spend**: every
turn on which the unit *was* affordable and *was* bought appears in the data as a
low-paint turn. The statistic is conditioned on the very outcome it purports to
predict, and it under-counts affordability by exactly the cases of interest.

**What caught it was a reconciliation, not suspicion.** 0.10% of 2000 turns is ~2
opportunities for one tower and ~24 across the team, while **572 soldiers were
actually built in that same game**. Two artefacts that had to agree, didn't.

### The rules this sharpens

> **A replay tells you what a unit ENDED UP with. It can never tell you what the
> unit COULD HAVE AFFORDED**, because the affording and the spending happen inside
> the same turn and only the residue is recorded.

- **Any "how often was X possible" question needs a decision-point instrument.**
  Post-hoc state answers "how often did X remain unused", which is a different and
  usually much smaller number.
- **Suspect any statistic whose denominator is a state the mechanism itself
  changes.** Paint is spent by the decision being measured; so is a treasury, a
  cooldown, a build slot. Anything the decision consumes is disqualified as a
  conditioning variable.
- **The cheap check is a reconciliation, and it is available almost always.** If a
  rate implies N opportunities, find the count of realised events and compare. Here
  24 versus 572 settled it in one line, with no new games.

Note what survived the correction, because discarding the whole analysis would have
been the lazy response: the *separate* finding that high-paint turns are turns when
money blocked the spawn is a claim **about post-turn state**, which is exactly what
post-turn state supports. Only the step from there to affordability was invalid.
**When part of an analysis fails, find the boundary rather than binning all of it.**


## Theme: swept maps and the head-to-head margin are THE SAME NUMBER, not two signals

Discovered 2026-09-08 while accepting iteration 24, in the act of citing both as
independent corroboration. They are arithmetically identical.

In a gauntlet that plays **both sides of every map**, let `SW` = maps won from both
sides, `SL` = maps lost from both sides, `SP` = maps that split by side, over
`N = SW + SL + SP` maps and `2N` games. A split map contributes exactly one win by
construction, so:

```
wins            = 2·SW + SP
margin over 50% = wins − N = 2·SW + SP − (SW + SL + SP) = SW − SL
```

> **The margin over 50% equals the net swept-map count, exactly. Split maps
> contribute precisely nothing to it.**

**State BOTH forms, always, because "margin" names two different quantities** and
the identity has a different coefficient for each:

```
margin over 50%   =  wins − N          =      (SW − SL)      <- per MAP
win−loss margin   =  wins − losses     =  2 × (SW − SL)      <- per GAME
```

Both are exact. They differ only in whether the unit is a map or a game, and a
quoted "margin" is ambiguous between them. This is not hypothetical: on
2026-09-08 the coordinator read my entry as the second form, computed a factor of
2 against my figure, and told me my coefficient was wrong — then re-derived it and
found we were each right about our own definition. Two correct parties, one
argument, caused entirely by a missing definition. Doctrine 14 now carries both
forms and requires a quoted margin to say which it means.

**What made that resolvable in minutes was the verification table, not the
argument.** The entry recorded the identity checked on all three opponents with
**zero residual**; that is what turned "whose formula is right" into "which
quantity does the word name". *Write the check into the log, not just the
conclusion* — a claim with its verification attached can survive being
contradicted by someone senior, and a claim without one cannot.

Verified on all three opponents of run `20260907-234431`, with no residual:

| opponent | SW | SL | SP | wins | margin over 50% | SW − SL |
|---|---|---|---|---|---|---|
| alice_iter23 | 8 | 0 | 17 | 33/50 | **+8** | **+8** |
| alice_flood | 21 | 1 | 3 | 45/50 | **+20** | **+20** |
| alice_iter7 | 4 | 0 | 2 | 10/12 | **+4** | **+4** |

### What this invalidates, including something I said an hour ago

I wrote that iteration 24 was supported by "two independent signals — head-to-head
66% (p≈0.02) and swept 8–0 (p≈0.008)" and treated that convergence as satisfying
doctrine 13's *"a real effect usually shows up in more than one place."* **It is one
place, cited twice.** Worse, the two p-values I quoted differ only because I applied
two different null models to the same eight maps, so the smaller one was not extra
confidence — it was a second opinion from the same witness.

This is not a small bookkeeping point: **the summary file prints both numbers side
by side on every run**, and I have been reading them as mutually corroborating for
many iterations.

### What each one is still good for

They are the same *magnitude*, but not the same *statement*, and the difference is
worth keeping:

- **`SW − SL` is the estimator.** It is the margin, computed on maps rather than
  games, and it is immune to spawn advantage by construction.
- **`SP` is the noise gauge, and it is free.** 17 of 25 maps splitting by side says
  most of this matchup is decided by which side you spawn on. That is information
  about the *instrument's resolution* which the win rate alone hides, and it says
  the effective sample here is nearer 8 maps than 50 games.

So the honest reading of iteration 24 is: **+8 net swept maps out of 25, with 17
maps carrying no signal at all.** That is still a clear accept — SW − SL = 8 with
SL = 0 is a one-directional result, and doctrine 10 says one-directional beats
scattered — but it is one result, and the genuinely independent corroboration is the
**mechanism** (starvation 48.8% → 31.1%), which is a different measurement of a
different quantity.

**The general rule: before calling two numbers independent corroboration, check
whether one is a deterministic function of the other.** Two statistics computed from
the same games usually are.


## CONSISTENCY PASS 2026-09-08 — tonight's four entries are all ONE error wearing different clothes

Written after adding them, by comparing them rather than re-reading each. Every one
passed inspection when written; only the comparison shows the pattern.

| entry | what I did | the number was... |
|---|---|---|
| **3b-ii** ruin-collision death | counted *collisions*, never counted *targets* | correct, about the wrong quantity |
| **proxy in a pre-registration** | gated on "enemy paint" where the engine charges "non-ally" | correct, about the wrong predicate |
| **swept maps vs win margin** | cited two statistics as independent corroboration | correct **twice**, about the *same* quantity |
| **the caveat's dimension** | flagged "how many maps" when the error was "how much of the game" | correct, about the wrong axis |

The unifying statement, and it is stronger than the four separately:

> **Every one of these was a correct computation. None was an arithmetic mistake.
> The failure is always in the mapping between the number and the claim** — and that
> mapping is never checked by re-doing the calculation, which is the only check that
> feels like checking.

This is the wrong-referent theme (doctrine 5) generalised. What tonight adds is that
the wrong referent has at least **four distinct shapes**, and I had a name for only
the first:

1. **Wrong quantity** — counted something real that does not bear on the claim.
2. **Wrong predicate** — used a paraphrase of the engine's test instead of the test.
3. **Wrong independence** — treated a deterministic function of X as evidence
   alongside X. *(New tonight, and the sneakiest, because both numbers are right and
   both are about the right thing.)*
4. **Wrong axis** — audited one dimension of a claim and inherited the others.

### The one operational check that would have caught all four

Each failed the same cheap test, which I am adopting as standing practice:

> **Before a number decides anything, write one sentence: "this number is the
> ___ of ___, measured over ___." Then check that each blank matches the claim.**

- collisions *of soldiers*, over *soldiers that had a target* — the claim was about soldiers **without** one.
- share *of hold-turns on enemy paint* — the engine charges on **non-ally** tiles.
- swept margin *of the same 25 maps* — already counted in the win rate.
- mopper share *of 22 rounds* — the claim was about a **646-round game**.

Four blanks, four mismatches, all visible without new data. **The check costs one
sentence and it is the sentence I skip when the number agrees with me.**

### Cross-references added, in both directions

Marked at each of the four entries: they are instances of this pass, not
independent lessons, and a future session that re-derives any one of them should
find the other three rather than treat it as novel.


## Theme: a retraction is a claim too, and shares the assumption that produced the error

The subtlest thing this session found, and it is about the *shape* of corrections
rather than about any measurement.

I made a claim, retracted it, and **both were wrong in the same way**:

| version | claim about effect (2), the `continue` clause |
|---|---|
| original | *"worth about +1 game — essentially nothing"* |
| retraction | *"+6 games; 'essentially nothing' was wrong by six games"* |
| **measured truth** | **+6 against a trap-fixed opponent, and exactly 0 against `iter22`** |

Neither version was right. The retraction corrected the *number* while inheriting
the error that generated it: **both assumed a feature has one value.** I argued
about whether that value was 1 or 6 and never asked whether it was a single
quantity at all. It is not — it is a function of the opponent, and against the
build the accept was measured on it is zero.

> **A correction is written by the same person, in the same frame, minutes after
> the mistake.** It fixes the thing that was noticed, and inherits everything that
> was not — and the unexamined assumption is precisely what was not noticed,
> because if it had been noticed it would have been the correction.

### The practical form

When retracting, do not only ask *"what number was wrong?"* Ask **"what did both
versions take for granted?"** In this case: that "the value of effect (2)" names
one thing. Once asked, the answer took one cell-level check to find.

This compounds with the trap this file already records — **a correction that runs
in your favour is the one least likely to get made** (the row-3 loss I measured at
zero, which made my accepted iteration look better). Put the two together and the
dangerous corrections are the ones that are *comfortable*: a retraction feels like
rigour, so it is the least likely piece of writing to get audited. **A retraction
is the most self-satisfied thing you will write all day, and it deserves more
scrutiny than the claim it replaces, not less.**

### 2026-09-08 — the caveat I wrote was about the wrong DIMENSION

I read 22 rounds of two tournament openings, saw bob field no moppers on every
line, and wrote "bob builds zero moppers" as a claim about his strategy. Over the
full 646 and 509 rounds he is **17.9% and 16.2% moppers** against my 26.2% and
21.1%. He *defers* them; he does not forgo them.

What makes this worth recording is not the error but the caveat I *did* write. I
flagged the observation as **"one observation of a policy seen twice, not two
independent samples"** — a correct and thoughtful note about **how many maps**. The
error was about **how much of the game**. Having audited one dimension carefully, I
felt audited; the dimension I never named was the one that was wrong.

> **A caveat protects only the dimension it names, and writing a good one creates
> the feeling of having checked all of them.** Before trusting a flagged claim, ask
> what dimension the flag is *about*, and name the ones it is silent on: sample
> size, duration, opponent, map, and regime are five different axes and a note on
> one is not a note on any other.

This compounds with the entry above rather than repeating it. That one says a
retraction inherits the assumption that produced the error. This one says a
**caveat** does the same thing *before* any error is noticed — the mechanism is
identical and it fires earlier. Both are cases of partial scrutiny feeling like
complete scrutiny.

And the practical tell was cheap: the claim was about a *game* and the evidence
was from an *opening*, and those two nouns are visibly different. **When the
evidence and the claim are about different-sized objects, that mismatch is
findable by reading the sentence, without any new data.**

### Cross-references

- The measurement that exposed it is *"head-to-head margins DO NOT CHAIN"* above,
  which is where the matchup-dependence was established at cell level.
- The favour-running-correction trap is in *"enumerate the cases, then COUNT
  them"*.
- The parent failure — using a number you have already labelled unreliable — is
  measurement doctrine 6, which came from the same evening.

---

## Theme: an instrument can produce NOTHING and no-finding, and the two are indistinguishable downstream

### 2026-09-08 — the census that emitted nothing, with no error anywhere

I built an in-bot tower census, ran a full game, dumped **188,514 indicator lines**
from the replay, and **not one was the census's.** No exception. No bytecode
overrun. No warning. The dump was clean and empty.

The cause: my `run()` loop's `finally` block writes a standing bytecode diagnostic
with `setIndicatorString` **after** `runTower` returns, and the engine keeps only
the **last** indicator string of a turn. The census was writing into a single-slot
channel that my own code overwrote microseconds later, every turn, forever.

> **An instrument that writes into a shared single-slot channel is silently erased
> by whoever writes last, and the failure mode is an empty result, not an error.**

The reason this is dangerous rather than merely annoying: I was measuring
*"do towers ever reach the splasher's price?"* and I already half-believed the
answer was **no**. An empty result reads exactly like "the thing never happened".
I was one step from writing up "towers never reach 300 paint" as a finding —
supported by an instrument that had never run.

### The check, and why it must be a POSITIVE control

**Before drawing any inference from what an instrument did not show, verify that it
showed something.** Not "the pipeline ran" — that it emitted a value you can point
at. And the check has to be on a quantity you know to be non-zero, because a
counter that reads 0 is as consistent with "never fired" as with "never ran".

I applied this to the very next census and it earned its keep immediately: I
pre-registered that *"max ally-tower `paintAmount` seen must be > 0, or
`RobotInfo.paintAmount` is not populated for allied towers, every gain figure is
garbage, and the correct response is to fix the instrument, not to report a small
number as a finding."* It came back 1000, so the numbers were readable — but had it
come back 0 I would have had a pre-committed reading of it, instead of a tempting
small number.

### How this compounds with the rest of the ledger

It is the same family as *"a REPLAY's per-robot state is post-decision by
construction"* — both are cases where the instrument answers a **different question
than the one asked** and the output still looks like an answer. But the failure is
strictly worse here: a post-decision statistic at least produces numbers you can
reconcile against something else, and reconciliation is what caught it. **An
instrument that emits nothing produces no number to reconcile.** There is no
internal contradiction to find. Only a positive control catches it.

---

## Theme: a maximum-per-observation is not a total, however many observations you add up

### 2026-09-08 — "494 soldiers of paint", and why it failed a plausibility check

My refill census summed, over every robot-turn where a paint withdrawal was legal,
the amount that robot *could* have withdrawn — `min(capacity - paint, towerPaint)`.
The total came to **98,773 paint**, which reads as **494 soldiers' worth** in a game.

It is nonsense, and the arithmetic that kills it is trivial: transfers have a
**cooldown of 10**, so a robot loitering beside a tower for ten hungry turns
contributes ten full tank-fills to that sum while it could actually have taken
**one**. The same tower's paint is then counted again for every other robot standing
next to it. The sum double-counts by roughly (dwell time x adjacent robots).

> **A per-observation maximum summed over observations is an upper bound repeated,
> not a total.** It is only a total when the observations draw on disjoint supply
> AND each can be realised independently — which a cooldown and a shared pool both
> break.

What actually caught it was **not** noticing the cooldown. It was a plausibility
check against a number from a different measurement entirely: **572 soldiers are
actually built in a whole game**, so "494 soldiers of paint sitting recoverable"
would mean I had been leaving nearly a second army on the table every game while
starving. Two figures that cannot both be true is the cheapest error detector I
have, and it works even when I cannot yet see *which* one is wrong.

This is the same detector that caught the post-spend affordability artefact earlier
the same night (0.10% of turns affordable vs 572 soldiers actually built). **Twice
in one session, an artefact was killed by reconciling against an unrelated count,
and neither time did I spot the defect by re-reading the code.** Worth promoting to
routine: *every derived aggregate gets reconciled against one independently-measured
quantity before it is quoted.*

---

## Theme: an exactly symmetric statistic is a hypothesis about the FILE FORMAT

### 2026-09-08 — my "tournament runner is broken" that was my own awk

I tallied a live tournament's `results.txt` and got: alice 75-75 vs bob, alice 75-75
vs carol, winning side A=180 / B=180, and **zero swept maps out of 75 in all three
pairs.** Zero sweeps is precisely the signature my mirror null produces for
*identical code*, so this looked like a real and serious fault: three different bots,
at three different commits, behaving like copies of one another.

It was my parse. `tools/tournament.sh:163` writes
`RESULT <teamA> <teamB> <map> <winnerSide> <rounds>` — **field 2 is team A, not the
winner**, and the winner is the `A`/`B` in field 5. Every map is played twice with
the assignment swapped, so field 2 is `alice` in exactly half the games **by
construction**. My "perfect 1-1 on every map" was an identity of the file format.
Corrected, the run reads alice 39-111 vs bob (26.0%) and 103-47 vs carol (68.7%) —
a real and rather good result that my bug had erased.

> **Three independent-looking quantities all landing on exact symmetry is not a
> finding about the world. Real systems are lopsided; file formats are symmetric.**
> Treat exact symmetry as evidence about the parser first, the data second.

### And the discriminating case for "what does this field mean" is the WRITER

I spent a while building theories about side bias and map-forced splits — that is,
looking for the answer in *more of the same data*. The question "what is field 2"
is not answerable from the data at all, at any sample size. One `grep` in
`tools/tournament.sh`, which I am explicitly allowed to read, settled it outright.

This is the project's standing rule — *run the discriminating case before you name
the fault* — with a sharper form for one common sub-case: **when the uncertainty is
about the SEMANTICS of a field rather than its values, the discriminating case is
the code that writes it.** More data cannot resolve a definition.

It also came within one step of costing something real. The charter tells me to
report tooling bugs rather than work around them, and reporting is *correct* — but a
report of a phantom bug spends a coordinator's attention and, worse, teaches the
other two lineages to distrust an instrument that was fine.

---

## Theme: SW+SL and SW−SL are different measurements, and a zero-variance null makes the first look like evidence

### 2026-09-08 — seven swept maps that proved the mechanism worked and said nothing about whether it helped

Iteration 25 came back **26-24 vs the baseline, 4 swept wins, 3 swept losses**. My
mirror null sweeps **nothing** — identical code splits every map, measured twice in
this project — so every one of those seven swept maps is proof that the mechanism
genuinely changed that game's outcome. Seven decisive, noise-free observations.

And they carry **no information about whether the change was good.** Four went one way,
three the other.

> **`SW + SL` measures how much a mechanism PERTURBS outcomes. `SW − SL` measures
> whether the perturbation HELPS.** Under a deterministic engine the null has zero
> variance, which makes `SW + SL` large and unambiguous while `SW − SL` remains a coin
> flip. Quoting the first in support of the second is precisely the error the swept-map
> doctrine exists to prevent.

The trap is that my own ledger already says *"a swept map is a near noise-free
instrument"* and *"swept-map counts deserve more weight than headline win rates"*. Both
are true and both are statements about `SW − SL`. Read quickly, they license "seven
maps swept, that is a strong signal" — which inverts them.

### The criterion, and the contrast that calibrates it

> **When `|SW − SL|` is small relative to `SW + SL`, the run measured sensitivity, not
> benefit. Take a second fresh map sample before accepting.**

- Iteration 25: `SW + SL = 7`, `|SW − SL| = 1`. Sensitivity.
- Iteration 24: `SW + SL = 8`, `|SW − SL| = 8` — eight swept wins, **zero** swept
  losses. That is what a directed effect looks like in this instrument.

The two runs have almost the same number of decisive maps. Only the *split* tells them
apart, and a net-margin-only report renders them nearly identical (+1 vs +8 on a scale
where 25 maps are available). **Always report `SW` and `SL` separately, never only
their difference.**

### On adding a hurdle after seeing the data

I introduced this rule *after* the run it condemns, which is normally the cardinal sin.
It is legitimate here for two specific reasons, and I record them so the exemption
cannot be stretched:

1. **It demands more evidence, not a different reading of the same evidence.** A
   goalpost that moves toward "measure again" is different in kind from one that moves
   toward "and therefore I was right". The candidate can still win.
2. **It is stated in a form that binds every future run**, including ones that would
   otherwise pass more easily, and it is written into the ledger rather than applied
   once and forgotten.

A rule that fails either test is rationalisation. This one is also, uncomfortably, a
rule that would have made *iteration 24* pass faster rather than slower — which is a
decent check that it is not shaped around the result I wanted here.

---

## Theme: the arm that improves your metric most can be the arm that loses

### 2026-09-08 — starvation deaths, anti-correlated with winning across three arms

Since iteration 24 I have treated **paint-starvation deaths** as the thing to minimise.
It is a good diagnostic: it is 31% of all my deaths, it is measurable, and it has an
obvious causal story. Three arms of the same mechanism at different doses, one map, same
opponent:

| arm | starvation deaths (final window) | tower paint at r2000 | outcome |
|---|---|---|---|
| baseline | 66 | 850 | LOST |
| **R = 200** | **85 (worst)** | 2,253 | **WON** |
| R = 0 | **29 (best)** | 728 | LOST |

**The arm with the fewest starvation deaths lost. The arm with the most won.**

The mechanism of the inversion is worth stating exactly, because it is not "the metric
was noisy":

> R = 0 buys unit lifetime by spending the **tower paint that creates units in the first
> place.** The starvation count sees only the first half of that trade — **the metric
> improves partly *because* the units that would have starved were never built.**

So the count is not measuring "units I saved". It is measuring "units that existed and
died in a particular way", and a change that suppresses the *denominator* improves it for
free. A metric that a mechanism can improve by shrinking the population it counts over is
not an objective; it is a diagnostic that has to be read next to the population size.

### Where this sits relative to the rest of the ledger

This is the same structure as *"a REPLAY's per-robot state is post-decision by
construction"* and as the "494 soldiers of paint" summation error — a statistic
conditioned on, or divided by, a population the intervention itself changes. That makes
it the **third distinct disguise in one session**, which is the real lesson: the family
recurs far faster than any individual instance would suggest, and I have now caught it
in a replay statistic, a summed bound, a ratio's denominator, and an optimisation target.

### The operational check

> **Before treating any count as an objective, ask what happens to it if the population
> being counted shrinks to zero.** If the metric reaches its best value there, it is a
> diagnostic and must be reported beside the population size, never alone.

"Zero starvation deaths" is achieved perfectly by building no units. That test takes five
seconds and would have demoted this metric before I built an iteration around it.

---

## Theme: my gauntlet's resolution collapses exactly where I need it most

### 2026-09-08 — the effective sample is decisive MAPS, and it shrinks as the candidate approaches its baseline

Three head-to-heads from one run, same 25 maps, same 50 games each:

| opponent | split maps (no signal) | decisive maps | resolution |
|---|---|---|---|
| `alice_iter7` (18 iterations back) | 1 | **24** | +24.41 sd |
| `alice_flood` (synthetic) | 6 | **19** | +8.93 sd |
| **`alice_iter24` (the accept gate)** | **18** | **7** | **+0.38 sd** |

Every row cost the same 50 games. The gate row bought **7 usable observations**; the
others bought 24 and 19.

> **A head-to-head's effective sample size is the number of maps that do NOT split by
> side, and that number falls as the two bots become more similar.** Games are not the
> unit and never were; a split map is two games that cancel exactly.

### Why this is adverse selection rather than bad luck

The comparison I am *required* to make — candidate against its immediate predecessor —
is by construction the comparison between the two most similar bots I have. So the
instrument has its **worst resolution precisely on the measurement the accept gate
depends on**, and its best resolution on comparisons that decide nothing. Iteration 24
saw the same shape (17 of 25 split); this is structural, not a bad draw.

This also explains something that used to read as a paradox: a run can post an
impressive-looking headline (81.3% across three opponents) while the only row that
matters is a coin flip. The strong rows are strong *because* they are irrelevant.

### What to do about it

- **Report split counts beside every head-to-head**, so "50 games" is never mistaken for
  50 observations. `tools/gate-read.sh` now prints them by default.
- **For a candidate that lands inside the noise, widen the sample rather than re-reading
  it** — `NMAPS=40` draws 40 maps instead of 25, and the extra resolution lands in the
  decisive maps because the split fraction is a property of the *pair*, not the sample
  size. A second fresh 25-map sample does the same job by pooling, which is the route
  the iteration-25 confirmation took.
- **Do not chain**: the tempting shortcut is to infer the gate from the wide-open
  `alice_iter7` row, which has plenty of resolution. That is exactly the chaining this
  ledger already forbids — *head-to-head margins do not chain* — and the resolution
  argument makes the temptation stronger, not weaker.

## Theme: an UNSPENT SURPLUS is not evidence of waste — and my first correction was ALSO wrong

> **SEE ALSO the third occurrence (iteration 39a, 2026-09-08)** and the control installed for
> it. This entry and the one at "removing waste pays only when the freed resource is the
> scarce one" are the same rule reached from two directions, and until today neither cited
> the other — the exact tell this document's own consistency-pass rule names.

> **SUPERSEDED, SAME DAY, BY ITS OWN PRESCRIBED TEST.** This entry originally concluded that
> the surplus was "a symptom of losing" and prescribed the contrast case as the missing
> check. I ran the check. **The winner's surplus was 4x the loser's** ($154,040 vs $1,510),
> so the entry's own conclusion is false in the opposite direction. The corrected mechanism
> is in the section "The resolution: chips COMPOUND, paint does not" at the end. The
> original text is kept because the prescribed test was right even though the conclusion
> drawn without it was not — the failure was asserting the conclusion *before* running it.

## (original, retained) an unspent surplus measured in a losing game

### 2026-09-08 — $36,830 of unspent chips, and the mechanism I built to spend them lost by 21 swept maps

Iteration 26 shifted the tower mix from ~50/50 money/paint to 25/75, on this reasoning:
at rounds 1200-1600 of a tournament game against `bob` I held **$36,830 unspent chips**
while my ten towers held 680 paint between them. Half my tower slots were producing the
resource I demonstrably could not spend, so I moved them to the one I could.

Census over all 75 maps: **54-96, net swept −21.** Not a near miss — the largest margin in
either direction I have ever measured against my own predecessor.

The paired replay trace says why, and it is the mirror image of the premise. At round 200
the candidate holds **3-160x the baseline's tower paint** while trailing it on **map
coverage**, which is the win condition. The pile did not go away. **It changed currency.**

> **The game I measured the surplus in was a game I was losing badly.** A bot that is
> losing has few units, few ruins and few tiles to act on, so whatever it produces
> accumulates. The surplus was a *consequence* of losing. I read it as a cause.

### The check, which costs nothing and which I did not run

**Would the surplus still be there in a game I was WINNING?**

A resource that accumulates only when you are behind is not a resource you are failing to
exploit — it is the accounting shadow of having nothing to spend it on. One dump of a won
game would have settled it before I wrote a line of code. I had won games available in the
same run and never looked, because the losing game was the one I was investigating for
*other* reasons and the surplus was simply the most striking number in it.

Generalised: **any "we have too much X" claim needs the same statistic from a game with the
opposite outcome before it becomes a hypothesis.** Otherwise it is conditioned on losing,
and the mechanism you build from it will be aimed at a state you only reach when it is
already too late.

### The trap has a positive-control shape, which is how it connects to the rest of the ledger

This is the same defect as "an instrument can produce NOTHING and no-finding, and the two
are indistinguishable downstream": a measurement taken in exactly one condition cannot tell
you whether it is describing the mechanism or describing the condition. There the fix was a
positive control; here it is a **contrast case** — the same number under the opposite
outcome. Same remedy, different axis.

---

## Theme: a rate pooled over HETEROGENEOUS producers measures specialisation, not shortage

### 2026-09-08 — "paint affordability 6-11%" was a fact about money towers

The second pillar under iteration 26 was my own tower census, over 80,752 tower-turns:

> the chip gate is open on **80-94%** of tower-turns, while paint-affordability sits at
> **6-11%**

Both figures are correctly computed. Neither is a **team-level** constraint, because the
population they average over is **half money towers, which by construction almost never
hold paint**. Pooling an affordability rate across producers that specialise in different
resources measures how specialised they are. It cannot measure which resource the *team* is
short of, and I used it as though it could.

### The tell was in the same census, and I quoted both halves in the same argument

The census also reported towers holding **>= 300 paint on 3.0-6.8% of tower-turns**.

**Stock and shortage cannot both be true of the same resource.** If paint were the binding
team constraint at 6-11% affordability, stocks would sit near zero — instead they were
large enough that iteration 25 was built specifically to *withdraw* from them, and iteration
25 worked. I had two artefacts that should have reconciled, they didn't, and rather than
reconcile them I cited both as support for the same conclusion.

That is `CONSISTENCY PASS 2026-09-08`'s operational check — "when two figures ought to
reconcile, reconcile them exactly and account for the residual" — failing on numbers I had
myself collected, in a document where I had already written the rule down.

### The operational form

- **Before quoting a pooled rate as a constraint, ask what the denominator is made of.**
  If the population is heterogeneous *in the thing being measured*, the pool measures the
  heterogeneity. Split by producer type first and see whether the split rates say the same
  thing; if they don't, there is no pooled number to quote.
- **A constraint claim and a stock claim about the same resource must be reconciled**, and
  if they cannot be, at most one of them is about the quantity you think it is.

### Cross-references

- Doctrine rule 5 (wrong-referent) — this is a new member of that family: not a number
  computed against the wrong object, but a rate averaged over a population it is not
  homogeneous across.
- "an exactly symmetric statistic is a hypothesis about the FILE FORMAT" — same instinct
  applied to a different artefact: interrogate what the measurement is *of*, not just
  whether the arithmetic is right.

### The resolution: chips COMPOUND, paint does not

Both the original premise and its first correction reached for a *behavioural* story about
the bots. The answer was an accounting property of the two currencies, sitting in `RULES.md`
the whole time:

- `assertCanCompleteTowerPattern` gates on **`getMoney() >= 1000`**; upgrades cost
  **2,500 / 5,000 chips**; a spawn costs **250 chips + 200 paint**.
- So **chips buy towers, and towers produce both chips and paint.** A chip spent early
  returns more of *both* currencies forever. Paint buys nothing that produces — it pays
  spawns and paints tiles, and is purely consumptive.

Everything the iteration 26 census showed follows from that with no reference to who was
ahead: tower count diverges monotonically (4 vs 8 at r200, 7 vs 15 at r1200) because
compounding rates diverge; **cash stocks looked similar early** because a stock cannot show
a rate; the paint pile is residue, since paint cannot be reinvested; and the winner's
six-figure end-state surplus is what a *finished* compounding race looks like once every
ruin is taken and there is nothing left to buy.

> **A stock is not a rate, and for a compounding resource the stock is at its most
> misleading exactly when the compounding has succeeded.**

### The operational rule, which would have prevented all three errors

**When the explanation of a result is a claim about a resource, check that resource's own
production identity in `RULES.md` before reaching for a story about the bots.** One grep
beats any number of coherent narratives, and I ran two narratives past a census and a
retraction before running the grep.

And the sharper form of the process failure: I wrote the sentence naming the test I had not
run, and committed the conclusion in the same breath. **Naming a missing check is not
performing it** — if the check is cheap enough to name, it is cheap enough to run before the
claim ships.

## Theme: with a deterministic engine, the SPLIT/SWEEP structure reads a mechanism's firing rate directly

### 2026-09-08 — a classifier-free regime test, entailed by the diff rather than assumed

Iteration 28 is a **regime-dependent** mechanism: towers build splashers only once chips run
past a threshold, which happens only in games that get that far. Doctrine rule 4 says such a
mechanism needs a regime-matched sample and a map-level prediction, so I pre-registered one
— and built the classifier badly. The replacement needs no classifier at all.

The candidate differed from its baseline by **exactly one executable line** (verified by
diffing with comments stripped, not by intention). Therefore:

> **On any map where the gate does not fire, the two bots are byte-identical.** Under a
> deterministic engine the A-side and B-side games are then the same game with the labels
> swapped, so the map **must split**. A non-firing map *cannot* be a swept win or a swept
> loss.

Which makes the sweep counts a direct readout of the mechanism:

| quantity | what it means |
|---|---|
| **swept wins** | maps where the mechanism fired **and decided the map in my favour** |
| **swept losses** | maps where it fired and **cost** me the map |
| **splits** | maps where it did not fire, or fired without changing the outcome |

Iteration 28 read 44 / 0 / 31 over the full 75-map census, and the reading was confirmed on
the ground: the split maps `memstore` and `rain` show `spl0` and flat chips in the replay,
exactly as the structure says they must.

**This is the first genuinely new use I have found for swept maps.** The ledger already
records that swept counts and the head-to-head margin are the *same number* — `wins − N =
SW − SL` identically — so citing both is citing one number twice. But that identity is about
`SW − SL`. **`SW + SL` versus the split count is independent of it**, and under a one-line
diff it measures *reach*: how many maps the mechanism acted on at all. Two numbers after
all, but not the two I had been reaching for.

### Preconditions, because this does not hold in general

1. **A deterministic engine** — verified, 12/12, earlier the same day.
2. **A genuinely single-mechanism diff.** Verify it by diffing stripped source. With two
   changed behaviours a split can mean "both fired and cancelled", and the inference dies.
3. **Both sides of every map played.** A one-sided sample has no sweeps to count.

### And the falsifier I pre-registered was MIS-SPECIFIED, which is its own lesson

I had written: *"if the wins are spread evenly across short and long games, the mechanism is
not what won"*. The wins came out spread evenly. By the letter of the pre-registration that
is a reject, and I accepted anyway — so the reasoning has to be better than a preference.

It is: **the falsifier's inference was logically impossible.** With a one-line diff there is
no other mechanism available for "what else won" to be. A pre-registration earns its
authority by naming a test the mechanism could actually fail; mine tested a **proxy that
does not track the thing it stands for**.

Concretely, the classifier called maps LONG or SHORT by whether the *previous iteration's*
games reached round 2000 — but the new bot **ends games earlier**, by painting enough of the
map instead of grinding to a tiebreak. So I had built a regime classifier out of a property
of a *different matchup* and then used it as a property of the map. Doctrine rule 5's
wrong-referent error, and the first time I have caught one before it moved a verdict.

> **Overriding a pre-registered gate is legitimate only when you can show the gate's
> INFERENCE is invalid, not when you can show its conclusion is inconvenient.** The
> distinction is whether the replacement test was available before the data and is strictly
> stronger. Here it was and is — it follows from the diff, which was fixed before the run.

**Operational**: when pre-registering a regime prediction, prefer a classifier the *mechanism
itself* determines (did it fire?) over a proxy for the conditions under which it should fire.
Under a deterministic engine and a single-mechanism diff, the split/sweep structure is that
classifier, and it is free.

## Theme: ROUND-COUNT IDENTITY is not byte-identity — the tiebreak forges the evidence

The split/sweep entry above gave me a free firing-rate instrument: under a deterministic
engine and a one-line diff, a map where the mechanism never fires is played identically from
both sides, so **equal round counts on the two sides means the builds never diverged.**

That inference has a hole, and it is not a small one.

> **Every game that reaches the round cap has round count 2000 on both sides — whether or
> not the two games were the same game.** The tiebreak *forces* the equality that I was
> reading as evidence of identity.

Caught by a subset test that could not fail honestly. Iteration 29 lowered a threshold, so
its never-fired set must be a **subset** of iteration 28's. Raw counts: 23 and 16. A subset
cannot be larger than its superset, so the instrument was wrong, not the result. Excluding
r2000/r2000 games: 6 and 8, subset holds, zero violations.

The correction is one line: **exclude games at the round cap before comparing round counts.**
What it cost was an overclaim I had already written down and reasoned from the same day —
"of 31 splits, 16 are byte-identical" — where the honest number is 8. The contamination is
worst exactly where this lineage's games cluster: 23.8% of tournament games end at the cap.

> **A necessary condition read as a sufficient one is invisible when it agrees with you.**
> Identical games ⇒ equal round counts. The converse needed the cap ruled out, and I never
> checked because every case I looked at was one I already believed.

**Operational**: the check that found this was run on a result I *expected to pass*. Nothing
else would have caught it — a check run only when the answer is feared is a formality whose
verdict is already decided.

## Theme: measure WHICH guard binds before fixing a mechanism that never fires

Replay forensics showed an accepted mechanism — iteration 25's paint refill — making
**zero** `transferPaint` calls across three entire games, while the opponent made 62, 74 and
36. It has three guards: below half paint, action unused, and a tower with spare paint
**adjacent**.

I formed a hypothesis from reading the code: `runSoldier` spends the action painting, so the
action guard must be what blocks the refill. The fix followed immediately and was a genuine
one-liner — move the call before the role dispatch. It was **completely wrong**.

Instrumented build, counters read off replay indicator strings, three self-play games:

| | hungry turns | action FREE | tower ADJACENT |
|---|---|---|---|
| DefaultMedium | 499 | 50% | **0.0%** |
| TheBest | 9,808 | 86% | **1.0%** |
| UnderTheSea | 1,708 | 93% | **0.0%** |

The action guard passes on 50-93% of the turns where it matters — obvious in hindsight, since
a soldier low on paint cannot paint and therefore never spends its action. **Adjacency binds
by two orders of magnitude.** The one-line fix targeted the one guard that was never the
problem.

> **When a mechanism never fires and it has N guards, the cost of measuring which one binds
> is a handful of games. The cost of guessing is an entire iteration that changes nothing —
> and a census that "rejects" a fix which was never applied.**

Two riders worth as much as the finding:

1. **A plausible causal story read off the source is not a measurement.** Mine was coherent,
   specific, and referred to real lines of code. It was still false.
2. **The same trap sat one step further on.** The replacement mechanism has to spend
   *movement*, and `wander()` already spends movement every turn — so appending a walk after
   the role would have been inert **for exactly the reason the refill is inert**. Having just
   been burned, I checked instead of assuming, and put the walk before the role dispatch.
   A failure mode you have just diagnosed is most dangerous in its next disguise.

## Theme: a pre-registered criterion may only cite quantities from the run it judges

Third wrong-referent error in one day, and the first one I had written *into a
pre-registration*, which is the place it does the most damage.

I pre-registered: *"a lower threshold that reaches further must produce fewer splits than
iteration 28's 31."* The run returned 60. But **31 was measured in `i28` vs `iter25` and 60 in
`i29` vs `i28` — different baselines.** A pair's split count measures how often *that pair*
differs; it is not a property of either member, so the two numbers are not comparable. The
criterion was not failed. It was **inapplicable**, and it was inapplicable the moment I wrote
it.

> **Rule: every quantity in a pre-registered gate must be measurable inside the run the gate
> judges.** A cross-run constant smuggles in a second matchup, and the gate then tests a
> comparison nobody ran.

Note what makes this insidious: I had written up the identical error that morning, in detail,
as the reason my iteration 28 classifier failed — and then reproduced it before lunch. The
write-up did not inoculate me. What would have caught it is a mechanical check at
pre-registration time: *for each number in this gate, which run produces it?* If the answer
is "a different one", the gate is broken.

## Theme: the CONSERVATIVE dose is not automatically the safe one

Iteration 30 diverts a soldier to walk to a tower for paint. I ran two doses:

- **A** — divert only when `paint < attackCost`, i.e. once it cannot paint a single tile, so
  the painting given up is *provably zero*;
- **B** — divert at the hunger line already in the code, `paint*2 < capacity`, which pulls
  away a soldier that could still be painting.

I expected **A** to win. The lineage's best mechanisms all have the shape "consume only what
was going spare", and this lineage's worst result (−21 net swept) came from a change that
starved a resource by being too aggressive. A was the arm with a zero-opportunity-cost
argument attached to it.

**B beat A** — +10 net swept against +3, 62% against 54%.

> **CORRECTED the same day by replication on a disjoint 35-map sample** (the 35 maps the
> dose run did not use). The arms came back **+2** and **0**: the *ordering* holds and A never
> beat B in either sample, but the gap fell from +13 to +4 on a common 75-map scale. **The
> "three to one" was a sample-specific ratio read as a property of the mechanism**, and I had
> already written it here as a general lesson. Two paired samples of the same quantity
> disagreed by ~9 net swept on a 75-map scale, so **a 35-40 map dose comparison here cannot
> resolve below roughly 5 net swept.** What follows below survives as an ORDERING claim; the
> magnitude does not.

The argument for A was sound and irrelevant. It priced the *painting given up* and ignored
the *unit lost*: 72-88% of my deaths are starvation, so a soldier that keeps painting until
it is provably empty is a soldier that dies before it reaches the tower. I had even written
that risk down for A, and then did not weight it, because the zero-cost framing was more
vivid than the race it was losing.

> **"Provably no opportunity cost" prices only the thing you chose to measure.** When the
> failure mode is a race against a deadline, acting late has a cost that a
> spare-capacity argument cannot see — the resource you were protecting is destroyed with
> the unit.

**Operational**: run the doses. Both arms cost one shared 160-game run, they shared a map
sample so the comparison was exact, and the result inverted a prior I would otherwise have
shipped as a single-arm iteration. When a dose argument feels obviously right, that is a
reason to include the other arm, not to skip it.

## Theme: pick the run convention that makes the reading unambiguous

A two-arm run must put the **baseline** in `BOT` so both arms share one map sample against
one opponent — which inverts the summary: `swept-win` then counts maps the *baseline* swept,
and an arm is good when the baseline **loses**.

I wrote that direction into the pre-registration before seeing a number, which is the right
guard. But the better move came after: **the decisive census went back to candidate-as-`BOT`**,
my usual direction, instead of carrying the inversion into the run that actually accepts
something.

> A convention you have to remember is a defect you have chosen to keep. Documenting an
> inversion protects one reading; removing it protects every future one, including the
> reading done by a session that never saw the note.

This is the same principle as the scratchpad fix landing in the restart prompt rather than in
a log entry, and the same reason a hand-transformation applied because you spotted a mismatch
is not a repair. **Where a risk can be designed out instead of documented, design it out.**

## Theme: a constant's NAME is not its semantics — read the method body

I found an unused engine call, `mopSwing`, and costed it from the constants around it:

```
MOPPER_ATTACK_PAINT_DEPLETION = 10        MOPPER_SWING_PAINT_DEPLETION = 5
```

and concluded the swing removes 5 paint from each of 3 tiles — a **3-tile enemy-paint
remover**, which happened to be precisely the weapon my measured weakness (coverage falling as
enemy paint replaces mine) called for. I wrote a cost table, declared it "strictly better on
every axis", reordered my iteration queue around it, told myself it invalidated the premise
behind three earlier iterations, and recorded all of that in `RULES.md`.

Then I disassembled the method:

```
onTheMap(loc) -> GameWorld.getRobot(loc) -> isRobotType/getTeam
              -> addPaint(-MOPPER_SWING_PAINT_DEPLETION)
```

**No tile-paint write exists in the method.** The constant is *robot* paint. `mopSwing` drains
enemy units; it does not convert ground. Every downstream conclusion was void, including the
one that "corrected" three earlier iterations which had been right all along.

> **A constant tells you a magnitude. Only the code tells you what the magnitude is
> subtracted from.** Read the method body before costing anything on a named constant.

Three things make this worse than an ordinary mistake, and they are the reusable part:

1. **The name was *nearly* right.** Five *is* deducted, and it *is* paint. Had the name been
   plainly wrong I would have checked it. A name that is 80% accurate defeats suspicion in a
   way that a wrong one does not.
2. **The error arrived wearing the shape of the answer I wanted.** I had spent the day
   measuring a coverage collapse; a "3-tile enemy-paint remover" fit that hole exactly. A
   finding that resolves your open problem on first contact deserves *more* scrutiny than one
   that complicates it, and it reliably gets less.
3. **The check cost one command.** `javap -c` was the same tool I had already used twice that
   day and explicitly praised for settling questions in seconds. Having a cheap verification
   habit does not help if you skip it exactly when the claim is exciting.

**And it is a different failure from the two earlier the same day.** Those were "source cannot
tell you how often a code path executes" — a runtime property needing measurement. This one is
static semantics, fully answerable from source, that I simply did not read. The corrective is
therefore not "trust source less"; it is **read the right level of source**: the call site for
what happens, the method body for what it means, and a run for how often.

**Operational**: when a claim from source reordering your priorities, propagate it into
`RULES.md` only *after* reading the implementation. A wrong reference outlives the log entry
that retracts it — mine sat in `RULES.md` for twenty minutes and would have been read by every
future session as established fact.

### Addendum, same day: I repeated this error within the hour

I made the identical mistake on `COMPLETE_RESOURCE_PATTERN_COST` — assumed paint, it is
**chips** — **less than an hour after writing the entry above**, and after having disassembled
a method body to catch the first instance. The tell was the same: constants printed beside it
were paint constants, so the currency looked settled.

It voided the headline rationale of my strongest-looking lead. I had called resource patterns
"a mechanic that converts the resource I hoard into the resource throttling me"; they spend
the throttling resource.

> **Writing a lesson down does not install it.** Two lessons written up today recurred within
> hours, each in a context that did not resemble the original. The write-up buys *recognition
> after the fact* — real value, but diagnosis, not immunity.

The corrective must be a step, not a resolution: **before a constant enters a cost table, grep
its use site and read the assert.** Put it beside the constants, not in a document you demonstrably
read and fail to apply.

And note the shared direction of both errors: **each made a mechanic look better than it was,
along the exact axis of the problem I was trying to solve.** Motivated reading does not feel
like motivated reading; it feels like a lead. Run the check hardest on the finding you like most.

---

## Theme: a CENSUS is exact — separate sampling noise from run-to-run noise before you call something unresolvable

### 2026-09-08 — 150 of 150 games identical across two independently launched runs

A session death launched the same 75-map census twice, 87 seconds apart: same candidate,
same baseline, same map set. `tools/determinism-check.sh` on all 75 maps and both sides:

```
shared maps fully played: 75   match: 75   differ: 0   skipped: 0
```

Both runs returned `SW=13 SL=13 split=49`, net swept 0, 75/150, 0 exceptions — the same
digits, not merely the same verdict.

**Yesterday I measured two 35-40 map samples of one quantity disagreeing by ~9 net swept on
a 75-map scale and wrote down a resolution limit.** The limit is real, but I had not
established *where the variance came from*, and the natural reading — the one I left on the
page — lumps sampling and engine/harness noise together. This separates them:

> **All of that spread was WHICH MAPS were drawn. None of it was run-to-run noise.** The
> engine's only nondeterminism is the 6th tiebreak (`Math.random`), and in 150 games it
> decided none — it sits behind five deterministic tiebreaks and is almost never reached.

### The operational consequences, which point in opposite directions

- **A sampled run (25-40 maps) cannot resolve below ~5 net swept.** Unchanged, and it is a
  *sampling* limit, so the fix is more maps or a disjoint replication — never a re-run.
- **A census is exact.** A census result near zero is not "noise around zero", it *is* zero.
  Iteration 32's −1 and iteration 33's 0 are the numbers.
- **Never re-run a census.** It is guaranteed to return the same answer and costs shared VM
  time to learn nothing. (I did not choose this duplicate, but I would have been wrong to
  treat the second run as confirmation *of the result*; it only confirms the *pipeline*.)

### The null I already had and had not been using as one

`tools/mirror_null.txt` records alice vs a byte-identical copy: **0 swept wins, 0 swept
losses, every map split 1-1.** That is the measured signature of an inert change under a
deterministic engine, and it turns the sweep counts into a **mechanism-firing test that
needs no instrumentation at all**:

> **Non-split maps under a deterministic engine = maps whose outcome the change altered.**
> The null is 0. So iteration 33's 26 decisive maps out of 75 prove the mechanism fired
> broadly, from the same numbers that judge it.

This is why "net swept 0" was worth more than "no effect": a change that decides 26 maps and
nets zero is a *measurement that the resource it spends is not the binding one*, not a
failure to act. Pair it with the pre-registered mechanism check every time — the sweep
structure is free and I had been asking for separate instrumentation to learn it.

### Cross-references

- Extends *"with a deterministic engine, the SPLIT/SWEEP structure reads a mechanism's
  firing rate directly"* — that entry read the firing rate; this one gives it a **calibrated
  zero** from the mirror null, so the reading is absolute rather than comparative.
- Scopes *"my gauntlet's resolution collapses exactly where I need it most"* to **sampled**
  runs only.
- Caveat retained: this is a census of a *fixed* map population. It is exact about those 75
  maps and says nothing about maps outside them.

---

## Theme: you cannot compare a COMPOUNDING resource to a CONSUMPTIVE one with a per-turn rate

### 2026-09-08 — "a money tower funds soldiers 3.2x faster", and it was the wrong question

Iteration 34 rebalanced tower construction from ~50% money towers to ~24%, on an arithmetic
I checked carefully and verified from bytecode:

| tower | per turn | soldiers funded per turn |
|---|---|---|
| money | `moneyPerTurn` 20 | 20 / `SOLDIER.moneyCost` 250 = **0.080** |
| paint | `paintPerTurn` 5 | 5 / `SOLDIER.paintCost` 200 = **0.025** |

Every constant is right. The **units** are not. That table prices a money tower as a
*supplier of soldiers*, and it is not one:

> **Chips buy TOWERS. A money tower's 20 chips/turn is not 0.08 soldiers/turn — it is
> 0.02 towers/turn, and a tower produces soldiers forever, plus more chips, plus more
> paint.** Paint is terminal: it pays a spawn and paints a tile and is gone.

Dividing both by `SOLDIER.*Cost` makes them look commensurable by erasing exactly the
property that distinguishes them. **A ratio between an investment yield and a consumption
rate is not a number that means anything**, however carefully each side is verified.

### What the engine actually did with the extra paint

`Barcode`, T1 = `alice_i34`, T2 = `alice_iter30`. The mechanism worked perfectly and the
bot still collapsed:

| round | T1 towers | T1 tower paint | T1 soldiers | T1 chips | T1 cov | | T2 towers | T2 soldiers | T2 cov |
|---|---|---|---|---|---|---|---|---|---|
| 200 | 7 | **2,156** | 9 | $1,330 | 420 | | 9 | 10 | 451 |
| 300 | **7** | **2,201** | 10 | $1,430 | 437 | | 11 | 14 | 537 |
| 500 | **7** | 811 | 11 | $1,330 | 370 | | 15 | 27 | 601 |
| 1100 | **7** | 511 | 9 | $3,380 | 306 | | 15 | 26 + 18 splashers | 667 |

**T1's tower count froze at 7 for 900 rounds.** Its tower paint at r200 was nearly *double*
the baseline's — the change did exactly what it was designed to do — and the paint then
**stranded**, draining away while the army stayed at ~10 soldiers and coverage decayed
420 -> 306. The baseline compounded to 15 towers and 44 units.

> **I raised production of the consumptive resource by cutting production of the compounding
> one. The consumptive resource piled up unspent and everything else stalled.**

### The trap fired for the THIRD time, and this time I had the rule written down

My evidence that chips were spare was *"chips idle at $1,000-3,700"*. LEARNINGS already says,
in these words:

> *"A stock is not a rate, and for a compounding resource the stock is at its most misleading
> exactly when the compounding has succeeded."*

and

> *"When the explanation of a result is a claim about a resource, check that resource's own
> production identity in RULES.md before reaching for a story about the bots."*

**The idle balance I cited as proof of surplus was produced BY the money towers I then
deleted.** I read a stock, inferred the rate was redundant, and cut the rate. The previous
two firings of this trap cost iteration 26 (−21) and a retraction; this one is worse, because
the earlier entries were on the page and I wrote a fresh engine-verified table instead of
re-reading them.

### The operational check, which is one sentence and would have stopped this

> **Before changing the MIX of two resources, ask of each: does spending it produce more of
> anything? If exactly one of them does, they are not exchangeable at any ratio, and a
> per-turn comparison between them is a category error rather than a dose to be tuned.**

In BC25 the answer is in `RULES.md`: `completeTowerPattern` gates on `getMoney() >= 1000` and
upgrades cost 2,500/5,000 chips, so **chips are the only currency that buys production**.
There is no corresponding paint purchase. That asymmetry is the whole game and it is not
visible anywhere in a soldiers-per-turn table.

### What the iteration got right, and is worth keeping

- **The named risk was the real one.** I pre-registered iteration 26's chip-starvation cliff
  and a two-branch diagnostic: *towers fall* vs *soldiers rise*. Towers froze and soldiers did
  not rise — branch (a), cleanly, with the rival branch refuted rather than merely unchosen.
  **Pre-registration converted a rout into a precise answer.**
- **The parity defect is real and survives the rejection.** Four of the 75 maps are
  single-parity (`gridworld`, `Filter`, `Snowman` all-even; `CastleDefense` all-odd), so the
  old rule builds zero paint towers on three maps and zero money towers on one. That is still
  a bug; it is just not one worth fixing by moving the ratio the wrong way.
- **Validating a geometric key against all 1,374 real ruin coordinates before running games
  was cheap and correct**, and it is reusable. The key had zero single-branch maps. The key
  was never the problem.

### Same-day correction: the Barcode collapse is NOT the universal mechanism

I wrote the table above from `Barcode` and let "tower count froze at 7 for 900 rounds" stand
as *the* explanation. I then dumped a second map, and it does not hold:

| `DefaultMedium`, T1 = `alice_i34` | r200 | r300 | r500 | r1000 | outcome |
|---|---|---|---|---|---|
| T1 towers | 10 | 10 | 11 | 11 | **T1 WON** |
| T2 towers | 11 | 12 | 12 | 12 | |

**No freeze, a one-tower gap, and the candidate won the map.** The tower-starvation story is
real on `Barcode` and is not what happens everywhere; iteration 34 wins some maps.

> **A replay chosen because I already had it verifies that a mechanism CAN operate. It never
> establishes how often it does.** I have this rule written down twice already — for
> iteration 25's `UnderTheSea` arm and for the R=0 ablation — and I still let a single map's
> table carry the word "why" in a headline.

The honest division of labour, and it is the same every time:

- **The census says whether it HARMED.** That is the evidence, and it is overwhelming.
- **A replay offers a mechanism that could produce that.** `Barcode` offers one; a second map
  shows the mechanism is not uniform, so the aggregate harm is a *mixture* — some maps
  collapse, some are unaffected, some improve.

The pre-registered diagnostic survives this intact, because I registered it as a **comparison
of two named branches**, not as a claim about every map: towers fell rather than soldiers
rising, on the map where it failed. What does not survive is my generalising one map's
magnitude into the mechanism's headline.

---

## Theme: a counter that goes to ZERO late in a game may be a PHASE CHANGE, not a failure

### 2026-09-08 — "one soldier alive and $72,980 idle" is what the winner looks like

I found this in the shipping bot's own replays and wrote it up as a pathology:

> `DefaultMedium` r1000, `alice_iter30`: $72,980 chips, 12 towers frozen since r500, 86 paint
> per tower, **1 soldier alive**, 12 splashers, and zero soldiers spawned in that window.

Three alarming-looking facts at once — an enormous idle stock, a unit count collapsed to ~zero,
and a growth curve gone flat — so I built two repair arms for the line that causes it. Then I
ran **one game** to size a risk I had named, and the same pattern appeared **on the side that
won**, while my repaired arm showed the healthy-looking numbers and lost:

| r1000 | soldiers | splashers | towers | coverage | result |
|---|---|---|---|---|---|
| `alice_i36a` (the "fix") | **19** | 0 | 12 | **312**, falling | lost |
| `alice_iter30` (baseline) | **0** | 12 | 11 | **662**, rising | **won** |

### Why every one of the three signals was misread

Each was a *phase* signature that I read as a *health* signature:

- **Tower count flat** — expansion FINISHED, not starved. Every reachable ruin was taken by
  r500. A flat curve at the cap looks identical to a stalled one.
- **Soldiers -> 0** — a soldier claims ruins and paints ground it cannot hold. With no ruins
  left it has no job. The splasher is the only unit I field that takes *enemy* paint, so after
  expansion it is the only unit whose output still converts.
- **Chips piling up** — the terminal state of a finished compounding race, exactly as my own
  earlier entry says: *"the winner's six-figure end-state surplus is what a finished
  compounding race looks like once every ruin is taken and there is nothing left to buy."*

**I had written that sentence, about this exact number, and still read the surplus as waste.**
Fourth firing of *"an unspent surplus is not evidence of waste"*, second in one day.

### The check that separates the two readings, and it is one question

> **Before calling a late-game counter collapse a pathology, look at the SAME counter on the
> side that WON that game.** If the winner does it too, it is the phase, not the bug. This
> costs one replay and needs no new instrumentation, because a candidate-vs-baseline replay
> already contains both teams.

The general form, which is what makes it worth an entry:

> **A metric's healthy value is a function of the game PHASE.** Any threshold or alarm read
> off a mid-game aggregate — "soldiers should be rising", "towers should be growing", "chips
> should be spent" — is implicitly a claim that the phase never changes. In BC25 it always
> changes, at the round the last ruin is claimed.

### And the process point, which is the reusable half

The one-game control existed **only because the pre-registration named a specific quantity to
measure** — *"does arm A build any splashers at all?"* — rather than a direction to hope for.
That named quantity cost **one game, 0.7% of the screen it replaced**, and it killed the
direction before the expensive run.

> **Pre-register a QUANTITY, not just a gate. A named quantity can often be measured far more
> cheaply than the gate can be evaluated, and when it can, measure it first.**

Cross-reference: this is the cheap-positive-control shape from *"an instrument can produce
NOTHING and no-finding"*, pointed at a candidate instead of at an instrument.

---

## Theme: a SCREEN ranks arms; only a CENSUS sizes an effect — and small effects are where skipping it tempts most

### 2026-09-08 — +4 on 25 maps became −1 on 75

Iteration 35's two arms were screened on a shared 25-map sample and then the survivor was
censused:

| arm | money share | 25-map screen | **75-map census** |
|---|---|---|---|
| `alice_i35a` | 49.1% | +0 | *(not run)* |
| `alice_i35b` | 69.6% | **+4** | **−1** |

The +4 came with everything that normally makes a result feel solid: it was the best number of
the day, it sat on a **monotone dose curve** (24.3% -> −52, 49.1% -> 0, 69.6% -> +4), and the
arm's record was 58%. All of that was compatible with the true value being −1.

**What saved it was a number written down before the run**, not judgment applied after:
*"my measured limit for a sampled run is ~5 net swept, and +4 is below it; a 25-map screen
cannot tell +4 from 0."* That sentence cost nothing and prevented shipping a regression —
and, worse than the regression, **believing the curve**.

### Why the temptation is strongest exactly where the risk is

- A **large** effect is resolved by the screen, so the census is a formality and nobody is
  tempted to skip it.
- A **small** effect is the one the screen cannot resolve — and it is also the one where the
  census feels least worth 150 games, because "it's only a couple of maps either way".

> **The cases where a confirmation run feels least necessary are exactly the cases it exists
> for.** Effect size and the strength of the argument for skipping the check move together.

### The division of labour, stated so it is reusable

| instrument | what it can do | what it CANNOT do |
|---|---|---|
| 25-map screen, shared sample | rank arms against each other; kill an arm that is clearly bad | size an effect smaller than ~5 net swept |
| 75-map census | give **the** number, exactly (150/150 reproducible) | say anything about maps outside the 75 |

A monotone-looking curve built from screen points is a curve of *unresolved* points. Here, once
both extremes were censused, the real shape was **flat from ~49% to ~70% with a cliff below** —
not monotone at all. **The apparent trend was noise arranged in a suggestive order**, and the
ordering was doing the persuading.

### Cross-reference

This sharpens the earlier entry that scoped the ~5 net swept limit to *sampled* runs after the
150/150 determinism control. That entry established the limit; this one is what it costs to
forget it, and the answer is: an accepted regression plus a false model of the mechanism.

### 2026-09-08, same day — NARROWING the entry above: "exact" is about BYTE-IDENTICAL builds only

The 150/150 result is real and the conclusion I drew from it was too broad. Both runs were the
**same build**. A census re-run of one build is exact; **a census MARGIN between two different
builds is not**, because any code change perturbs the PRNG stream, and that is a different
regime from re-running the same bytes.

Calibrated by a third lineage on **policy-identical arms differing only in PRNG phase**, full
corpus, both sides:

| | |
|---|---|
| sd of the head-to-head | **4.80 games per 150** (78% of binomial) |
| maps whose result survives a phase change | **38 of 75** |

So half the corpus is a coin flip that **more of the same maps cannot fix** — the residue is
**engine chaos on a fixed corpus, not sampling error**. Census buys about **2.2x** resolution
over a 25-map screen, not the ~4.7x that "zero variance" implies. Working band for a 150-game
full-corpus head-to-head, until I calibrate my own: **>= +10 accept, +7..+9 replicate,
<= +6 reject.**

**This bit immediately.** Iteration 37a censused at **+7**, cleared my pre-registered gate, and
I promoted it — then reverted, because +7 is the replicate band. Four hours earlier I had
refused iteration 35b on +4 for a resolution reason; the same discipline applies at +7 and I
nearly missed it because the gate I had written said only "net swept > 0".

> **A resolution finding narrows what your GATE may say, not just what you may conclude.**
> A gate of "> 0" silently assumes the floor is 0. Mine never was.

**And the corollary needs narrowing too, in the same direction.** I wrote that byte-identical
code splits every map, making sweep counts a free mechanism test. True **between byte-identical
arms**. Between arms that differ, ~half the corpus flips on phase alone, so:

- a **handful** of decisive maps is now **weak** mechanism evidence (iteration 37a's 15 of 75);
- a **large** decisive set still is strong (iteration 34's 26 of 75, or an empty identical-set).

### How to measure your own floor, which is cheap and which I should not have borrowed

Two numbers cannot estimate a standard deviation, but **a fixed corpus hands you 75 paired maps
for free**, and over the per-map records `E[(Sa − Sb)²] = 2·Var(S)`. The arms must be
**policy-identical and phase-different** — for me that is one character: the PRNG seed offset,
`rc.getID() * 31 + 17` -> `+ 18`. Same distribution for every decision, different realisation.
Run it against the baseline over the full corpus and whatever net swept comes back is **pure
chaos**, measured on your own bot.

That same arm also gives the only honest **replication** in this regime: re-running an
identical pair returns the identical number by construction and confirms the *pipeline*, not
the *effect*. To replicate an effect you must change the phase and keep the policy.

---

## Theme: a change with NO policy content moved my census by +12 — measure your own floor, and check its MEAN

### 2026-09-08 — the "null" that wasn't, and what it cost

To calibrate my own accept threshold I built `alice_phase`: `alice_iter30` with **one**
substantive change, the PRNG seed offset `rc.getID() * 31 + 17` -> `+ 18`. Same distribution
for every decision. Zero policy content. Full 75-map census against the baseline:

| | SW | SL | split | record | net swept |
|---|---|---|---|---|---|
| `alice_phase` vs `alice_iter30` | 20 | 8 | 47 | 87/150 (58.0%) | **+12** |

**Iteration 37a, a real mechanism change, had censused at +7 the same day.** A policy-free
change beat it. Iteration 37a was rejected on this, having already been promoted once and
reverted once.

### Two diagnostics, and the one that fired is not the one I expected

- **`Var(S)` against the Bernoulli ceiling** (S = per-map win proportion; max 0.25): mine came
  back **0.093**, comfortably under. **Passed.**
- **The MEAN**: a policy-identical pair must be **mean-zero**. Mine sat at **S = 0.580, 2.3 sd
  from zero.** **Failed.**

> **A variance check cannot detect a shifted null.** I would have accepted the floor as
> well-behaved on the ceiling test alone. The mean is the cheaper and stricter check, and it is
> the one that says *this pair is not a null at all* — which makes the sd an understatement
> rather than an estimate.

### Why "policy-identical" was false, and the defect it uncovered

`rngState` is seeded from `rc.getID()`, and **starting-tower IDs are fixed for a given map**
(`Gears` id1-id4, `DefaultMedium` id4-id7). The engine is deterministic, so those towers draw
**the same sequence in every game on that map**. So

```java
UnitType want = (rnd(4) == 0) ? UnitType.MOPPER : UnitType.SOLDIER;
```

is **not 25% for the towers that matter most** — it is a fixed draw per map, set by one
constant. Offset 17 gives one starting tower **5 moppers in its first 12 spawns**; offset 18
gives the same tower **0 of 12**. Iteration 5 measured early moppers crowding out soldiers as
an *absorbing state*, so that constant silently sets an opening the bot's author never chose.

> **An ID-seeded PRNG in a deterministic engine is not randomness — it is a hard-coded opening
> with a random-looking name.** Wherever entity IDs are stable across games, "random" tie-breaks
> are fixed sequences, and the seed constant becomes a tuned parameter nobody knows they own.

This is the same family as *"a constant's NAME is not its semantics"*: `rnd(4) == 0` reads as a
frequency and is a *literal fixed sequence* for the units whose decisions matter most.

### The operational rules

1. **Measure your OWN floor.** Three lineages, same engine and same corpus, measured 4.80 (78%
   of binomial), 5.29 (86%, mine), and 6.48 (106%). **The floor is a property of the bot.**
   Inheriting another's would have set my gate ~10% too loose and would have hidden the mean
   shift entirely.
2. **Check the null's mean, not only its variance.**
3. **A gate of "net swept > 0" silently asserts the floor is zero.** Mine is +12. Every such
   gate I had written was too weak.
4. **Do not fix this by tuning the seed.** That is overfitting to a fixed opening and fragile
   under any change to spawn order. Fix it by making the opening mix *explicit* — a per-tower
   counter giving exactly 1 in 4 — which deletes the hidden parameter instead of choosing a
   lucky value for it.


## Theme: a lesson written THREE times is not a lesson, it is a missing control

**2026-09-08, iteration 39a.** I measured that the splasher gate fires on 76% of tower
build-turns on DefaultHuge and that the tower cannot afford the paint on 96% of those, called
1,315 idle build-turns "pure waste", and built a candidate to reclaim them. The candidate
removed splasher production **entirely** (gate firings 1374 -> 0 on two maps) because the
idling *was* the accumulation mechanism: the tower was saving toward a 300-paint splasher, and
letting it buy a 200-paint soldier meant it never reached 300 again.

**Build slots were never scarce. Tower paint was.** That is verbatim the rule already in this
document under "removing waste pays only when the freed resource is the scarce one" (iteration
20, freed soldier turns) and again under "an UNSPENT SURPLUS is not evidence of waste"
(iteration 26, spent chips, −21 net swept). Three iterations, one error, and **two prior
write-ups that did not stop the third.**

> **The tell was available before the run and I did not use it: a 96% "unaffordable" rate is
> not a failure rate if the other 4% is what the 96% was saving up for.** Any denominator that
> includes the accumulation phase of a savings behaviour will read as waste.

### The control, since the note demonstrably is not one

`tools/gate-read.sh` — the tool I invoke to read *every* verdict — now prints three standing
pre-checks to stderr before any numbers, unconditionally:

1. **SCARCITY**: name the wasted resource and the binding one; if they differ, the freed
   resource buys nothing. Carries all three failures as worked examples.
2. **UNIT**: `net_swept = SW−SL = wins−N`, `sd = sqrt(decisive)`; `wins−losses` is 2x both.
3. **BITE**: was the mechanism check run on a map where the mechanism is known to act?

It fires whether or not I think I need it, which is the whole point. Its honest weakness:
it fires when I *read* a result, not when I *design* a candidate — so it can still cost a
screen, but not an accept. That is a strictly smaller blast radius, not a cure.

## Theme: my gate and my floor are in the same unit — the audit, with the derivation

**Coordinator flag, 2026-09-08.** Another lineage's gate tool computed the sd of the **win
count** while quoting its threshold on the **margin**; since `sd(margin) = 2 × sd(wins)`, every
gate it produced was **1.0 sd wearing a 2.0 sd label** — a one-tail false-accept rate near 16%
where it believed it had 2%. I was asked to audit mine before my next verdict.

**Mine is sound, and here is the derivation rather than the assurance.** With every map played
both sides, writing `split` for the maps that go one apiece:

```
wins          = 2*SW + split          N  = SW + SL + split
wins - N      = SW - SL               = net_swept        <- EXACT, so the sds are EQUAL
wins - losses = 2*(SW - SL)           = 2 * net_swept    <- the sd is DOUBLED
Var(net_swept) = Var(2*SW - decisive) = 4 * decisive/4   = decisive
```

So `sd(net_swept) = sqrt(decisive) = sd(wins)`, and **there is no factor of 2 between my floor
and my gate** — the factor of 2 lives in `wins − losses`, a statistic I do not gate on. My
census null: `sd_net_swept = 5.29`, gate `+12`, giving **2.27 sd**.

> **The structural protection is that my gate and my floor are expressed in the SAME unit, so
> the sd-multiple is invariant to which of the two margins I quote.** +12 against sd 5.29 and
> +24 against sd 10.58 are the same statement. A tool is only exposed to this bug when the
> threshold and the sd come from different places — which is exactly how the other lineage's
> did.

And the answer to the question the coordinator asked of my `alice_phase` result: **the +12 is
`wins − N`** (87 − 75 = 12, matching SW − SL = 20 − 8), so my **win-count sd is 5.29**, not
2.65 — squarely between the other two lineages' 4.80 and 6.48, against a binomial reference of
6.12 (86%). My floor is not anomalous under either reading.

**Two controls, installed rather than resolved.** `tools/noise-floor.py` now carries
unit-bearing names (`sd_net_swept`, `sd_wins`, `sd_win_minus_loss`) and **asserts
`SW − SL == wins − N` on every run**, refusing to report if it ever fails. `tools/gate-read.sh`
already computed the same identity independently and prints `OK (wins-N=…, SW-SL=…)` per
opponent — so two tools written days apart agree, which is the reconciliation doctrine 5 asks
for rather than a single tool trusted twice.

One thing worth keeping: I declined to ship `alice_phase` on the grounds that **a margin needs
a mechanism**, and that decision is correct under *either* unit reading. The arithmetic sharpens
the report; it was never what made the call.

## Theme: a tournament run is not an independent sample — dedupe on the COMMIT PAIR, not the run id

**2026-09-09.** To get more per-map resolution than one tournament gives, I pooled the last four
runs: 8 games per map instead of 2. The pooled set said I was 0/8 on 23 maps against `bob` —
which reads as overwhelming.

**`alice`–`bob` was byte-identical across `20260908-1300` and `20260909-0100`: 150/150 games,
same winner *and* same round count.** Both lineages had shipped unchanged commits, and the
engine is deterministic. The second tournament re-ran the identical 150 games. `alice`–`carol`
did differ (carol shipped a new commit): 19/150 identical, 127/150 same winner.

> **Pooling N tournaments multiplies the apparent `n` by N, adds zero information for any pair
> whose two commits have not moved, and shrinks every standard error by `sqrt(N)`.** "0/8 on 23
> maps" was 0/2 against bob, printed four times.

### The rule

**Deduplicate on `(commit_a, commit_b, map, side)`, never on the run id.** `bots.txt` in each
tournament directory carries the commit each lineage played, which is exactly what makes this
checkable. After dedup my four runs held **450 unique games, 6 per map** — 2 vs bob, 4 vs carol.

**And cluster at the map level.** The remaining games on one map are 2–4 games of the same
pairing on the same terrain; they are not independent either. My finding survived both
corrections (18.7 points, 2.39 sd) but it was 2x overstated before them.

**The tell, available for free**: identical `rounds` values across runs. A round count is a
near-continuous quantity — two genuinely independent games agreeing on it to the round is
essentially impossible, so a single mismatch-free column is proof of replay, not of consistency.

**Cross-reference.** The tournament report already warns that citing a margin *and* its sweep
counts is citing one number twice. This is the same error along the time axis instead of the
statistic axis, and neither warning would have caught the other.


## Theme: one map cannot size a corpus quantity — and I made this error inside the session I read the warning

**2026-09-09.** Tracing `alice-vs-bob-on-MoneyTower`, I found alice's money pinned at
$1,200–1,400 — below `CHIP_RESERVE = 1450` — with 1,700–2,200 tower paint idle and **zero
splashers built in 1,044 rounds**. The story was clean and mechanistic: a ruin-sparse map yields
few money towers, so chip income never crosses the splasher gate.

It even passed the SCARCITY pre-check **affirmatively** — freed resource and binding resource
would both have been chips — which is the first time that check has ever endorsed a candidate
of mine rather than vetoing one. That is precisely what made it persuasive.

**It was false.** `BatSignal`, equally sparse at 10 ruins, has a **$13,400** median chip pile,
spends 0% of turns below the reserve, and builds 9 splashers. Chip starvation is a property of
`MoneyTower` — the corpus's second-sparsest map *by density*, 5.7 ruins/1k — and not of sparse
maps at all.

`tools/mapdata/README.md` makes this exact argument, in these words, about `gridworld`: it is "a
poor choice for sizing any ruin-related quantity, and a bad default just because it is small and
quick to trace." **I read that file earlier in the same session and then did the same thing with
a different map.**

> **Pick the sample before the trace, not the trace before the sample.** A single replay can
> show that a mechanism *exists*; it can never show how common it is. The moment a finding is
> phrased as a property of a *class* of maps ("on sparse maps alice ..."), it needs a sample
> spanning that class — and, just as importantly, a check against the class's *other* extreme.

**What made the difference here was cost asymmetry, and it is worth stating as the operating
rule.** Four replay dumps off games already on disk cost no VM game time. An iteration built on
the refuted mechanism would have cost a screen and possibly a census. **When the check is
cheaper than the experiment by an order of magnitude, run the check even when the story is
convincing — especially then**, because a story that survives one trace is exactly the kind that
gets built on without a second.

**A first affirmative SCARCITY reading is not a licence.** The pre-check tests whether the
freed and binding resources coincide; it does not test whether the *measurement* of what binds
generalises. Passing it moved my confidence far more than it should have.

## Theme: a stronger dose of the same mechanism producing LESS of the predicted effect is how you catch a noise reading

**2026-09-09, iterations 41a/41b.** I measured an opponent-independent weakness — 44.0% on the
25 ruin-sparsest maps against 62.7% elsewhere, 2.39 sd — and proposed the obvious cause: alice
builds zero splashers on those maps while both siblings spawn them from round 2. Screen 41a's
`k4` arm came back `+2` on the sparse half and `−2` on the rich half. Cancellation in the
predicted direction, exactly as pre-registered.

Then I found a defect in my own arm (an unaffordable splasher made the tower build *nothing*,
so the arm suppressed total production as well as reallocating it) and rebuilt it faithfully.
The corrected arm has **more** splashers and **no** lost spawns — a strictly stronger dose of
the same mechanism. Its sparse half came back **`+0`**, and its total went from `0` to `−2`.

> **The predicted effect got smaller as the mechanism got stronger.** That is not a weak result,
> it is a *contradiction*, and it is the cheapest available proof that the original `+2` was
> noise rather than signal.

### Why this is worth a rule

A dose ladder is normally read for *monotonicity across doses within one run*. This is the same
logic across **implementations of the same dose**: a faithful implementation is a higher
effective dose than a confounded one, so the effect must not shrink. Had 41b merely come back
`+1`, I would have called it "consistent, needs a census". It came back with the *sign of the
relationship inverted*, which no amount of extra sampling rescues.

**The operational rule**: when a first arm gives a small effect in the predicted direction and
you then improve the implementation, **pre-commit to reading the improved arm as a dose
increase**. If the predicted effect does not grow, the first reading was noise — regardless of
whether the new total still looks "close".

### And the substantive lesson, which is about copying opponents

Both siblings run early splashers and both beat me on sparse maps. I inferred the arrow from
that co-occurrence.

> **Adopting an opponent's visible policy is not adopting what makes it work.** A splasher share
> is one line of a composition inside a bot built around it. Transplanted into mine it competes
> with a soldier economy tuned for ruin capture — so what I measured was the *transplant*, never
> the policy. This is the tournament's self-referential blind spot working in reverse: the
> channel is genuinely informative about *where* I am weak, and near-worthless about *what to do
> about it*, because it shows me outcomes and one line of a commit message, never mechanisms.

**Keep the two apart in the ledger.** The weakness (44% vs 62.7%) is a measurement and survives.
The explanation (no early splashers) is dead. A future session that remembers only "sparse maps
are bad, siblings splash early" will rebuild iteration 41 — so the closed-axis entry names the
re-open condition as *a reason the rest of my bot now supports the share*, not fresh evidence
that the siblings still have one.

## Theme: a distribution measured UNDER a gate is shaped BY that gate — to size a threshold you must move it

Censusing tower turns on `MoneyTower` I found the spawn gate (`CHIP_RESERVE = 1450`) skipping
**97%** of them, and asked the reachability question: where below the gate does the treasury
actually sit? The histogram was emphatic and closed exactly against the bucket total:

| money at the decision point | share of skipped turns |
|---|---|
| < 250 | **0.7%** |
| 250–999 | ~6% |
| 1000–1249 | ~20% |
| **1250–1449** | **72–78%** |

Three-quarters of blocked turns sat within 200 chips of the gate. The reserve exists so a
1000-chip tower completion can always fund, and a soldier costs 250, so the *derived* threshold
is `1000 + 250 = 1250`; the extra 450 was a searched constant protecting nothing. One line,
engine-derived, self-calibrating, and it would preserve iteration 2's guarantee by construction.

**Every part of that is true and the conclusion is still wrong.** Iteration 16 ran the dose at
*exactly* 1250 and measured 11/24 — identical to baseline, with soldier count falling. Two
artefacts that ought to agree and don't, which is doctrine 5's tell. The reconciliation:

> **The treasury equilibrates just below whatever the gate is.** Money climbs until it crosses
> the threshold, a tower spends 250, it drops under, it climbs again. The band [1250, 1450) is
> not an opportunity the gate is narrowly missing — it is **the sawtooth the gate creates**. Move
> the gate to 1250 and the treasury parks under *that*, at the same firing rate.

So a pile-up just below a threshold means **the gate is binding and working as designed**, which
is the opposite of what it looks like. The identical number supports both readings and the
histogram cannot separate them; only *moving* the gate can.

**The general form.** Any quantity a bot spends down against a threshold will pile up just below
that threshold, at every threshold, whatever its value. Reading the pile-up as "nearly
affordable" is mistaking a control system's set-point for an opportunity. **Never size a
threshold from the distribution it produced.**

This is the mirror of the entry at "measure WHICH guard binds before fixing a mechanism that
never fires" — that one warns about a gate sitting *above* the operating band (dead code); this
one warns about reading the operating band that a *live* gate carved out. **A reachability
measurement can fail in both directions, and they look nothing alike.**

### The control, because a lesson is not one (doctrine 19)

What stopped this was not insight. It was grepping my own closed-directions ledger before
building, which cost under a minute and returned the hypothesis **stated by name**:

> | "The treasury sitting under the gate is why my army is small" | the spender fields no more army | — |

So the check is now a named pre-check, to be discharged in writing in the pre-registration
alongside reachability, trigger frequency, generality and history:

> **LEDGER pre-check — grep `TRAINING_LOG.md` for the constant, branch or mechanism this change
> touches, before building.** Not "recall whether it is closed": grep it. Three sessions running,
> the ledger has answered a persuasive candidate for free — iteration 40 unbuilt, the tower-mix
> corollary twice, and now this. The entries that pay are the ones carrying a falsifiable
> **re-open condition** rather than a verdict, because then the check is one grep and a
> comparison instead of a judgement call.

### Consistency pass: this entry and the post-spend replay entry are the SAME failure

Comparing entries rather than checking each one on its own (which is the only way this kind of
error surfaces), the gate entry above and the earlier entry on **replay state being written
post-turn** are two instances of one rule, and neither cited the other:

| entry | the statistic | what it is conditioned on |
|---|---|---|
| replay post-spend | "how often could this tower afford a soldier" = 0.10% | **the purchase** — turns where it *could* afford one are exactly the turns it spent down |
| gate-shaped distribution | "money is within 200 chips of the gate on 72% of turns" | **the gate** — the spend that follows crossing it is what creates the band |

> **A measurement taken downstream of the mechanism it is meant to evaluate reports the
> mechanism's own footprint back to you.** Both statistics are correctly computed, both look like
> discoveries, and both are answers to a question about what *would* happen, taken from data
> generated by what *did*.

The tells are the same too, and both are cheap: **reconcile the rate into a count you can observe
directly** (0.10% implied ~24 opportunities against 572 soldiers actually built), or **check
whether the quantity would look identical under the benign hypothesis** (money piles below every
gate, at every value of the gate).

Add a third instance from 2026-09-09, which is what prompted this pass: the `DEAD` bucket —
tower-turns holding 200–299 paint while wanting a 300-paint splasher — read as idle waste. It is
conditioned on the *build*: a tower must pass through [200,300) on its way to 300 before every
splasher, so the bucket is produced by the very builds it appeared to be preventing. The
reconciliation is the same move: `DEAD/built` measured 4.9–5.9 against the 6.67 that accumulation
alone predicts at 15 paint/turn. **No residue, no waste, no iteration.**

Three instances, one shape. The unifying pre-check, which is now the thing to actually run:

> **Before reading a statistic as an opportunity, ask what generated the data. If the mechanism
> under study is upstream of the measurement, the number describes the mechanism working, not the
> mechanism failing.**

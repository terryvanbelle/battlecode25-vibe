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

## 3e. Movement is not waste — it is the exploration that buys towers

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
3. **Automate it so the wrong model cannot come back.** `tools/map-resample.py`
   computes bootstrap + jackknife over maps from any run's `results.csv`. Quote
   it instead of a formula.

**The general form**: *before* attaching an uncertainty to a number, ask what
would have to be re-rolled to get a different one. If re-running the same games
cannot change the answer, per-game randomness is not the source of your error
bars, and any formula that assumes it is describing a different experiment.

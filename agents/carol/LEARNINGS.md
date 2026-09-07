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

## Price a sink in the resource that actually binds, not the one it is denominated in

Ranking the three unused mechanics (SRPs, tower upgrades, comms) I dismissed tower upgrades
on arithmetic that was correct and irrelevant: 2500 chips for +10 chips/turn is a 250-round
payback, versus 1000 chips for +20/turn from a new tower. Both numbers are in **chips**.

The MoneyTower trace then showed both teams finishing with 100,190 and 158,950 idle chips
while every tower sat at `tp<=150`. Chips there are not scarce, they are *garbage*; paint
generation is the hard cap, and a lv1 paint tower mining 5/turn funds one 200-paint soldier
every 40 rounds regardless of the treasury. Repriced in paint, a lv2 upgrade **doubles** a
tower's output for chips that were being thrown away, and 158,950 idle chips is 794 SRPs.

The general form: an option's cost and its benefit are often denominated in different
resources, and the ROI you compute by dividing them is meaningless unless both are scarce.
Ask which resource is binding *first*, price everything in that, and treat an abundant
resource's cost as zero. The winner's profile this project keeps rediscovering — "capability
preserved at zero marginal cost" — is mostly this observation wearing a different hat.

## A rules digest is not an instrument; only a call-site diff is

`RULES.md` documented special resource patterns, tower upgrades and communications in
engine-verified detail, and even concluded in as many words that "chips accumulate uselessly
unless spent on towers/upgrades/SRPs". The bot implemented **none of the three**. Six
iterations of reading my own notes never surfaced it; one `javap RobotController` diffed
against `grep -o 'rc\.[a-zA-Z]*'` surfaced all three in a minute.

Knowing a mechanic exists and *calling* it are independent facts, and only the second is
checkable mechanically. The sweep is now a standing per-evaluation item next to the bytecode
check — cheap, and it is the only thing that can catch a whole mechanic sitting idle.

## Verify a threshold against the operating band before, not after, the run

Iteration 6's `PAINT_PLENTIFUL = 500` was not dead code — the gate genuinely flipped on
Mirage, where tower paint spans 0-1000. It was worse than dead: it sat just *above* the
mid-game band (Mirage r1000 average 414), so it fired early and then effectively never again,
silently reverting the previous iteration's accepted result while looking like it worked.

A gate above the operating band is obvious in a trace and invisible in a win rate. Before
committing a threshold, read the actual distribution of the quantity it tests out of a replay
and check the threshold falls *inside* it — and for a map-adaptive threshold, check it
separates the map classes you meant it to separate. That check costs one replay and would
have set this constant correctly the first time.

## Writing the lesson is not fixing the bug

"Fixed constants rot into dead bands" was written after `CHIP_RESERVE` froze the treasury at
1350 and got carol annihilated on DefaultSmall at round 69. Four iterations later the same
map produced the same annihilation at the same round, because the entry ended with two rules
("arm a reserve only once the thing it protects is happening"; "instrument the gate value
itself") and **neither was ever implemented**. The identical shape had just appeared in the
API sweep: `RULES.md` concluded chips are wasted without SRPs/upgrades, and the bot called
none of them.

A third instance turned up the moment I actually ran the audit: the longest entry in this
file concludes that splashers are "the central missing capability", and the spawn line rolls
only `MOPPER` or `SOLDIER`. `runSplasher()` is compiled and unreachable.

Three distinct failure modes, one root: a conclusion recorded in prose has no mechanical
consequence. LEARNINGS.md entries that prescribe a code change now carry an explicit status,
and an entry that prescribes one without a commit behind it is an open bug, not a lesson.
The general check is cheap — for each entry, name the line of code it changed; if there
isn't one, it is still an open bug wearing a lesson's clothes.

## Check the gate can see the effect before you build the fix

The frozen-treasury bug freezes the treasury only when the last money tower dies. Killing
towers is something `carol_rush` does and my own lineage does not — so the accept gate
(head-to-head against my last snapshot) showed the degeneracy in 1 of 22 loss replays, while
the three rusher losses showed it for 1887, 1881 and 44 consecutive rounds each.

Had I run the standard gate, it would have come back ~50%, I would have read that as a
rejection, and I would have closed a direction that is worth three games and a fatal
degeneracy. The measurement would have been perfectly executed and completely uninformative.

So the pre-check is not just "is the branch reachable in my bot" but **"does the instrument I
am about to gate on ever produce the situation the branch handles?"** — one query against
existing replays, before writing the fix. When the answer is no, the mechanism becomes the
primary gate and the head-to-head is demoted to a regression check. This is the specific shape
the self-referential blind spot takes: a lineage cannot regression-test a defence against a
behaviour it never performs, and every instrument descended from that lineage inherits the
hole.

## Sizing an opportunity needs the wins as well as the losses

Measuring frozen-treasury runs only in losses would have shown three big numbers and proved
nothing — plenty of things are common in games we lose. Running the same query over won games
gave 0, 0, 0 across 2,955 rounds, and it is that pair that makes the signal: the condition
fires in all three losses and none of the wins, so disarming the reserve cannot misfire while
a game is going well. The algorithm's "don't sample only losses" is usually framed as avoiding
tautological conclusions; it is just as valuable for establishing that a trigger is *safe*.

## A mechanism can rewrite the whole game and move nothing

Iteration 6's self-calibrating tower mix was verified to work in every sense that is not the
scoreboard. The gate genuinely flipped (tower paint spans 0-1000 on Mirage), the tower count
on the motivating map went 4-5 to 8, and diffing indicator trajectories between the two doses
showed **31,274 differing lines on Mirage and 59,798 on Leaf** — essentially every robot-turn
of those games changed. The winner did not.

Across 40 paired games on identical maps, 37 outcomes were unchanged, and a direct
head-to-head between the two doses came out 20/40. Three instruments, one answer.

The trap is that the mechanistic story was *true*, and a true mechanistic story is the most
convincing thing available short of a head-to-head. "The threshold sits above the operating
band, so it builds the wrong tower type" was correct, checkable, and checked — and the thing
it predicted about winning was still false. This is why the accept gate is a head-to-head and
not a mechanism check, and it is worth re-reading whenever a mechanism verification comes back
beautiful.

The practical tell: if a change rewrites tens of thousands of robot-turns and the outcome does
not move, the quantity it controls is not on the path to winning. Do not spend a refinement on
a better value of it — the lever is the wrong lever, not the wrong setting. Two near-miss
refinements were available under the rules here and taking them would have been a mistake.

## Ask what the run already in flight answers before queueing another

The play-symmetry mirror audit sat "owed" for four iterations because it looked like it needed
its own 40-game run against a byte-identical copy. It did not. Iteration 7's head-to-head block
was already a mirror match — the new mechanism provably never fired against the baseline, so
the two builds made identical decisions over 20 maps and both sides — and it answered the
question outright (every map split by side; the favoured side was 9 maps to 10, so no
team-identity bias).

Shared VM time is the scarcest resource in this project, and a queued run costs hours of
wall-clock that a query against an existing replay costs seconds. Before queueing anything,
ask which pending question the *current* run's replays already contain the answer to. Several
of this session's findings — the frozen-treasury trigger frequency, the arm-to-arm identity
check, this audit — came out of runs launched for a different purpose entirely.

## Carol's tower mass stops every archetype -- but not her own lineage

**Corrected the same session it was written.** The original claim ("a defence nobody has
beaten") was drawn from `carol_decap` and `carol_rush` alone. Measuring carol's own tower count
across 27 traced h2h replays shows it **falling after passing three in 15 of them**, sometimes
8->4 or 10->5. Carol's soldiers already attack enemy towers, and `carol_iter5` is a full
economy that masses them -- so her own lineage is the only opponent in the pool that reliably
takes her towers. What follows still holds against the archetypes, and the reason they fail is
still the arithmetic below; what does not hold is the word "nobody".

Built `carol_decap` specifically to kill carol's money towers, and it went **39/40 = 97.5%**
against her while **never taking a single tower**: across three traced games carol's tower
count only ever rose (2->11, 2->15, flat at 4) and never once fell.

The arithmetic says it cannot work. A soldier does 50 damage to a tower, so a lv1 tower at
1,000 HP needs **20 uninterrupted attacks** — while every carol tower in range returns 20
single-target *plus* 10 AoE per turn, **for free**, because tower attacks bypass the action
cooldown entirely (engine note: `assertCanAttackTower` checks only the per-turn flags). Any
soldier that closes on a defended tower dies well before its twentieth swing. `carol_rush`
scores its occasional win only by swarming *small* maps in the opening, before carol's second
and third towers exist.

Three consequences worth carrying:
- **Tower count is defensive depth, not just economy.** Every accepted econ iteration that
  raised tower count also bought survivability, and none of them were credited for it.
- **It explains why the frozen-treasury degeneracy is rare** on the accepted baseline: that bug
  needs the last money tower to die, and killing *any* tower is already hard.
- **Adding an economy to an aggressive archetype made it worse at aggression.** carol_decap's
  ruin-building slowed it to the frontier, so it arrived later and in smaller numbers. An
  archetype exists to pose one threat cleanly; making it a better *bot* made it a worse
  *instrument*.

## Judge an instrument by whether it poses the threat, not by its win rate

`carol_decap`'s 97.5% would have supported the summary "it is too weak, tune it up". The trace
said something entirely different and far more useful: it never kills a tower, so no amount of
tuning its *targeting* would help — the defect is arrival timing, not target selection. A win
rate can only tell you an opponent lost; it cannot tell you whether it ever performed the
behaviour you built it to perform. For any purpose-built archetype, verify the behaviour
directly in a replay before drawing a single conclusion from its record.

## Losing the last paint tower is an instant, silent, unrecoverable loss

Read out of the disassembly, not inferred from the symptom.
`InternalRobot.processBeginningOfRound` gates paint income on the tower's own type —
`if (type.paintPerTurn != 0) addPaint(paintPerTurn + 3*numSRPs)` — and a money tower's
`paintPerTurn` is 0, so it gains paint from **nothing**, SRPs included, because the SRP bonus
sits inside that same guard. A robot's paint cost is drawn from the *building tower's* stash,
so once every surviving tower is dry, `buildRobot` fails at any chip total; with no robot no
ruin can be painted; with no ruin no tower can ever be rebuilt.

Observed on Dominoes: the starting paint tower died around round 200 and carol then held one
dry money tower for **1,800 rounds while chips climbed to 60,000**, taking 29 soldier actions
in the whole game. It costs the accepted baseline **2 of 40** games against `carol_rush`, and
the control arm proved it belongs to the baseline rather than to any candidate.

Three things follow:
- **Paint-tower count is a survival variable, not an economic one.** Every tower-mix decision
  is also a bet on not reaching zero paint towers.
- `NUMBER_INITIAL_PAINT_TOWERS = 1`, so **every game begins one death away from this state**,
  and a tower-type rule that never asks what the team already holds is gambling every game.
- **Chips are worthless the instant it happens**, so no "spend the surplus" mechanism — SRPs,
  upgrades, a disarmed reserve — can be the escape route. Only prevention works.

The general lesson underneath: look for states the rules make *absorbing*. A disadvantage you
can trade out of is a tuning problem; a state with no legal path out is a correctness problem,
and it deserves a guard rather than a better heuristic.

## Condition a reachability check on the guard the gate sits behind

The standing pre-check "is this branch ever taken?" has a failure mode that passes review:
checking the **marginal** distribution of the gated quantity instead of its **conditional**
distribution given the guard.

Iteration 12 gated a paint-tower upgrade on `chips >= 3,700`. The pre-check measured 146,350
tower-turns and found **21.7% clear 3,700** — a comfortable PASS. In the run the mechanism
fired **once in 11,016 tower-turns**, because the gate sits inside a guard (`is this an
upgradable paint tower?`) and the two are anti-correlated:

| | chips >= 3,700 | guard matches | both |
|---|---|---|---|
| gridworld | 92.5% | 2.1% | **0.59%** |
| DefaultMedium | 0.0% | 68.4% | **0.00%** |

Neither marginal is alarming; the conjunction is ~0 everywhere. The anti-correlation had a
mechanical cause that was visible in the code all along: the treasury is drained to ~1,450 by
spawning, so chips accumulate **only** when spawning is already blocked by zero tower paint —
and on the maps where that happens, carol builds no towers, so almost none of hers are
upgradable paint towers.

**The rule**: measure the gated quantity **among the turns that actually reach that line**, not
across all turns. And when you do a joint analysis, do it on the pair the mechanism will
**execute** under, not the pair that **motivated** it. I had run a joint check — chip-rich AND
paint-destitute, 11.1% — and it was the right *shape* of analysis on the wrong *pair*; it
described the problem the feature was aimed at, never the conditions the feature needed to run.

Two corollaries earned the same day:

- **Read the mechanism gate from live replays a few games in, not from the final win rate.** A
  mechanism firing once in 11,000 opportunities returns a clean ~50% that reads as "this
  doesn't help", when the truth is it never ran. Those are opposite conclusions and the
  scoreboard cannot distinguish them. Cost: one replay pull, 15 games in.
- **A guard is a mechanism and needs its own reachability check.** The fix for the inert
  upgrade added a deadlock guard reusing `stagnantTurns >= 10`. Measured before shipping:
  `stag == 0` on **all 27,356** tower-turns sampled, max 0 — the counter resets whenever chips
  change, which is nearly every turn. The guard would never have tripped, leaving the deadlock
  it existed to prevent completely unmitigated, inside the fix for an inert mechanism. Replaced
  with one whose tripping is observable in the trace (`upgSave` vs `upgGiveUp`), and its firing
  is now a **registered gate**, not an assumption.

## "More X doesn't help" does not license "less X is free"

Three iterations (5, 8, 10) raised carol's unit production by three different routes; iteration
10 fielded **4.1x the soldier-turns** and the head-to-head moved from 50.0% to 47.5%. I
summarised that, correctly, as "unit production is not the binding constraint" — and then used
it to justify iteration 12b, which **withheld** spawning to fund tower upgrades. It lost 32
points (62.5% -> 30.0%), with 12 swept-losses to 4 swept-wins.

Those three iterations measured the **upward** direction only. A plateau in one direction says
nothing about the gradient in the other, and a bot sitting at the *edge* of a plateau looks
identical, in that data, to one sitting in the middle of a flat region. The two differ entirely
in what a *reduction* costs.

**The rule**: before spending a resource on the grounds that more of it was worthless, check
that *less* of it is also cheap — that is a separate measurement, and the zero arm of the new
mechanism is not the same experiment as the old one's upper arm.

This rejection was worth its run precisely because both pre-registered gates passed: `UPG` fired
22 times on 10/10 maps and the guard tripped 152 times on 10/10, so the mechanism demonstrably
did what it was designed to do and the result is about the *trade*, not the implementation. The
strongest rejections are the ones where the mechanism worked.

## An early conditional-gate read samples game PHASES, not turns

Reading a conditional reachability counter 8 games into a run — instead of waiting 40
minutes for the full one — is the single best process change I made, and it has a failure
mode I walked straight into.

On iteration 14 I read the counter early and wrote *"the hypothesis is wrong: of the idle
turns this targets, 93.5% have no empty tile anywhere in vision."* Over **complete** games
the same counter reads:

| map/side | hit-rate among targeted turns |
|---|---|
| Parking_lot B | **76.9%** |
| Bunny B | 58.9% |
| walalilongla B | 49.9% |
| DefaultMedium B | **20.5%** (I quoted 6.5% for this map) |
| Castle B | 4.0% |

The rate is not a constant. It varies by map from 4% to 77%, and it varies **within** a game:
early rounds are exactly when territory is least saturated and the frontier is nearest, so a
prefix of the replay over-samples the phase where the counter reads highest — or, as here,
lowest, once you realise which way the bias runs for *this* counter. A partial replay is a
biased sample of game phases, not a small random sample of turns.

The fix is not to stop reading gates early — 5 minutes versus 40 is still the right trade.
It is:

- **Treat an early read as directional only.** Never write "the hypothesis is wrong" on one.
- **Ask which way the phase bias runs before quoting the number.** Any counter whose rate
  depends on board saturation, unit count, or resource level is phase-dependent by
  construction, and that is most counters worth measuring.
- **Let the decision rule, not the diagnosis, make the call.** I kept the run alive because I
  had pre-registered that the verdict came from mirror deviation rather than firing count.
  That is what saved a +6-game one-directional accept from being thrown away on a bad number.

This is the same lesson as iteration 12's from the other side. There, a *low* firing count
nearly killed a real effect; here, a *misread* firing count nearly did. Both times the
protection was the same: **frequency counters diagnose, they never decide.**

## Measure whether a memory can LEARN before you build one

Iteration 15's first design remembered where EMPTY ground had been *seen*, and steered idle
soldiers at the nearest remembered cell. It compiles, it is cheap, and it is nearly useless:
on Castle it fired `memHit` 1,250 times against `memNone` **8,084**.

The reason is structural and I should have seen it on paper. The memory could only be written
inside the vision scan that runs on idle turns, and that scan returns a target on just 4% of
those turns on Castle. **A memory that can only learn on the turns it already has an answer
starves exactly when it is needed.** Its density is highest where it adds least.

Inverting it fixed the density problem completely. Remembering *where this robot has been* is
written once per turn, unconditionally, with no sensing at all — and at spawn every cell is
unknown, so "somewhere I have never been" is dense from turn one and is precisely where
unpainted ground can still be. Measured over a full game, **every** exploration target the
inverted version picked was a never-visited cell (`expOld = 0` across 27,822 indicator
samples), so the memory never saturates either.

The general rule: for any proposed memory, state its **write condition** and check it against
the **read condition** before implementing. If the two are correlated, the memory is a
no-op dressed as a mechanism. Two minutes of measurement caught this one; it would have cost a
40-minute run and probably a rejected iteration.

## The History pre-check must name the iteration that wrote the LINE, not the previous one

TRAINING_ALGORITHM §3 asks: "If a prior iteration deliberately established the behavior this
would change, the fix must supersede that reasoning with new evidence, not silently revert
it." I recorded that pre-check as **passing** for iteration 15 — "strictly extends iteration
14, reverts nothing" — and it was true, and it was the wrong question.

The line I rewrote was `newExploreTarget()`. That was established by **iteration 3**, eleven
iterations earlier, with an explicit argument: a soldier must commit to a *far* target rather
than re-roll a local step every turn, because "a local random walk cannot find the frontier on
a 40x40+ map once home is painted" (`NOTGT` on ~57% of soldier turns). Iteration 15b returned
the **nearest** unvisited cell — a few turns away, so `moveExploring` re-rolled it constantly
and the persistent target collapsed straight back into the random walk iteration 3 deleted.
11/40, swept 3-14.

The rationale was in a comment **directly above the function I was editing**. I had read that
comment. I had quoted its 57% figure in my own notes one iteration earlier. I still missed it,
because I asked the pre-check about the wrong iteration.

- **Ask "which iteration established this line, and what was its argument?"** — not "does this
  revert my previous iteration?". Recency is not the relevant relation; authorship is.
- **`git log -L` or a grep of the log for the function name answers it in seconds.** The cost
  of the check is far below the cost of one rejected run.
- **A code comment explaining why something is the way it is IS the History pre-check**, and
  the moment to read it is when you delete it. I replaced that comment with my own, which
  confidently asserted the opposite ("Nearest rather than farthest is deliberate"), and wrote
  no evidence for the assertion.

## Pre-register a MAP-LEVEL prediction, not just a threshold

Iteration 15b's headline was 27.5%, so it was never going to be accepted. But the genuinely
useful output was a prediction I had written down before the run: the gain should concentrate
on the maps with most to gain — Castle (frontier hit-rate 4.0%, 18,040 idle turns) — and not
on Parking_lot (76.9%).

**Castle was a swept loss; Parking_lot was a swept win. Exactly inverted.**

A threshold ("h2h > 50%") can only tell me whether to accept. A map-level prediction tells me
whether the *mechanism I described* is the mechanism doing the work — and it is checkable even
on a run that lands near 50%, which is exactly where the threshold is least informative and
the temptation to accept on a story is highest. Under a deterministic engine with a
zero-variance mirror null, per-map outcomes are real signal, not noise, so this costs nothing
to register and can reverse a decision the headline would have gotten wrong.

Register one on every iteration from here: *which maps should move, and why*.

## Price the features you already carry — a rejected candidate is a free ablation

Iteration 15c was rejected at 52.5%, deviating from the zero-variance null on exactly one map
in forty. Read as an accept/reject decision that is a null result. Read as a *measurement* it
is the most valuable run of the session, because splitting iteration 15b's bundle produced a
two-point dose curve on a feature accepted twelve iterations earlier and never measured since:

```
null (identical code)                   20/40
memory + FARTHEST target (15c)          21/40      (+1)
memory + NEAREST target  (15b)          11/40      (-9)
```

Iteration 3's "commit to a far exploration target rather than re-roll a local step" is worth
**about ten games in forty**. Nothing in twelve iterations had priced it; it was accepted as
one half of a coupled pair and quietly carried ever since. TRAINING_ALGORITHM's stall list puts
ablating carried features first precisely because of this pattern, and a 2026 audit found the
most valuable features were ones accepted almost incidentally.

Two things follow that I did not appreciate before:

- **A bundled candidate, split into its parts, ablates the baseline for free.** I did not set
  out to measure iteration 3. I set out to work out why 15b lost, and isolating the variable
  priced an eleven-iteration-old feature as a side effect. Whenever a candidate loses badly and
  it touched more than one thing, splitting it buys a number about the baseline, not just about
  the candidate.
- **Now that it is priced, it is protected.** "Iteration 3's commitment is worth ~10 games/40"
  is a fact any future navigation change has to beat, and it converts a vague "don't break the
  explorer" instinct into a threshold. Unpriced features cannot be defended, only feared.

## Know which idleness you are looking at before you fix it

Two units, two very different diagnoses, measured the same way from the same eight replays:

| unit | dominant idle state | share |
|---|---|---|
| **splasher** | `noPaint` — below its 50-paint attack cost | up to **79%** of its turns; 1,987 turns on Parking_lot against 10 splashes |
| **soldier** | has paint (median 96–141), idle for lack of a *target* | cannot paint at all on only 8.6–17.6% of turns |

Same word — "idle" — two unrelated causes. The splasher needs logistics (it is nowhere near a
tower and nothing brings it back). The soldier needs somewhere to go, which is what iteration
14 gave it and why iteration 14 worked.

Had I generalized from the splasher measurement to "carol's units are paint-starved" I would
have built refill logistics for soldiers and addressed 8–17% of turns while believing I was
addressing 79%. **Measure the state distribution per unit type, never pooled** — a pooled
"idle" counter would have averaged these two into a number describing neither.

## Cost the price, not just the benefit — twice in one session, two different disguises

Two rejected iterations, one shared error, and I did not recognize it the second time even
though I had just written up the first.

**Iteration 17 (send dry splashers home to refill).** I measured the benefit precisely: 1,987
turns per game in which a splasher could not act. I never measured the **price** — the walk.
Result: `rw` shows a splasher spending 10–49 turns walking to gain at most **2** refuels, while
walking away from the frontier it must then walk back to. Final: 20/40, exactly the null, +0
games.

**Iteration 19a (stop building moppers).** I measured the benefit precisely: moppers idle on
95.1% of 78,480 turns, at 5 of every 20 spawns. I never measured the **price** — a mopper costs
**100 paint against a soldier's 200**, and `buildRobot` draws that from the tower's own stash,
which is under 200 paint on 57–99% of tower turns. Cutting the cheap unit in a paint-starved
economy *removes* production. Running at 32%.

The disguise differs — one price is measured in turns, the other in the scarce resource — but
the shape is identical: **I counted what the change would gain and never counted what it would
spend.** An idle unit is not free to redirect, and a cheap unit is not cheap to delete.

The habit that fixes it is small and mechanical:

- **For every mechanism, write the benefit and the price as two numbers before running it.**
  Iteration 17's "10–49 turns walking for 2 refuels" was computable from a single verification
  match; I ran that match and only read the firing counter off it.
- **Name the units.** "1,987 idle turns" and "a 40-turn walk" are the same currency and can be
  compared; "95% idle" and "300 chips" cannot, which is exactly how the second one slipped past.
- **Ask what the thing costs on the axis that binds.** Carol's binding resource is tower paint.
  Both mistakes evaluated a change on a non-binding axis (turns, spawn slots) while the price
  fell on the binding one.

Contrast with the two that worked. Iteration 14 (frontier-seeking): benefit = redirect an idle
soldier, price = **zero**, it only changes the destination of a move already happening; +6
games. Iteration 18 (release the pinned reserve): benefit = unblock production, price = **zero
towers**, verified by a paired within-game count; +7 games. Both are the "capability preserved
at zero marginal cost" profile — and the reason that profile keeps winning is precisely that
its price term is *zero*, so getting the price wrong cannot hurt you.

## A counter that reads zero and a counter that is ABSENT are different facts

I nearly rejected a working mechanism because my extraction helper was

```python
def mx(k):
    v = [ ... regex over the replay ... ]
    return max(v) if v else 0          # <-- "no samples" and "genuinely zero" both render as 0
```

After rebasing iteration 20 onto a new baseline I had left its counters out of
`setIndicatorString`, so the regex matched nothing and the helper reported `fl=fd=fs=0`. I
wrote it up as "the mechanism is completely inert over a full 2,000-round game" and reasoned my
way to a tidy mechanistic explanation for why. Re-run with the counters actually emitted: **134
deliveries per mopper.**

This is the exact inverse of the failure this whole project guards against. Doctrine says never
*accept* a mechanism whose firing count is zero, because it cannot have caused the result. It
follows just as strongly that you must never *reject* one on a zero you have not proved is real.
An absent counter looks identical to a dead mechanism, and the wrong conclusion is available in
one line of plausible Python.

- **Assert the sample count before reporting the value.** `assert v, f"no samples for {k}"` —
  or print `n=` alongside every statistic. I now print the sample count for every counter I
  read, and a counter with `n=0` is a **tooling bug until proven otherwise**, never a finding.
- **Whenever a mechanism reads zero, first confirm the instrument is present.** The cheapest
  check is a sibling counter that must be non-zero — here `tw2` (ally tower in vision) was
  reading 275, which would have exposed the artifact instantly had I emitted and read it.
- **Rebasing a candidate onto a new baseline is exactly when instrumentation goes missing**,
  because the string-surgery that ports the change has to re-find its anchor points and will
  silently drop what it cannot place.

## Two of my own mechanistic stories, both tidy, both wrong, both killed by one game

Within an hour I reasoned my way into two confident explanations and measured both:

- *"Moppers idle 95% of the time because they bleed 2–4 paint/turn, freeze at zero and die."*
  RULES.md genuinely says a robot at 0 paint cannot move or act and takes −20 HP/turn against
  the mopper's 50 HP. It is a clean, rules-grounded story. **Median mopper paint: 94 of 100.
  Turns at zero: 1.0%.** Refuted.
- *"The ferry cannot fire because moppers are broke."* Refuted by the same numbers, and by 134
  deliveries per mopper.

Neither story was careless — both were derived from the spec and both would have survived a
review. What killed them was one instrumented game each, costing about two minutes. That ratio
is the whole argument for TRAINING_ALGORITHM §2: **trace, don't theorize.** The danger is not
holding a wrong theory, it is that a *well-founded* wrong theory reads exactly like a finding
and will be written into the log as one if nothing is measured.

## Reachability has three levels, and I have now been caught at each

A mechanism can fail to fire for three different reasons, and I have shipped a candidate
blocked at each level in a single session. They need different checks and only the third is the
one the algorithm's "reachability" pre-check actually names.

1. **The condition never exists.** Iteration 16's tower-AoE guard: `runTower` attacks before it
   spawns, so "enemy in sight AND action not ready" is empty. `aoeFreed = 0`.
   *Check*: read the guard you are nesting inside, and the statement order around it.
2. **The condition exists in the world but not in the robot's view.** Iteration 20's ferry: a
   donor tower and a dry tower coexist on 49% of rounds on DefaultLarge — I measured that and
   called the pre-check passed — but the *mopper* saw a donor on only 19 turns and had to be
   within r²=2 to act. **Seeing a donor is not standing next to one.** `fd` max 1 per game.
   *Check*: measure the condition **from the acting unit's indicator**, never from a global
   count over the map.
3. **The condition is visible and actionable but rare.** Iteration 12's tower upgrade: 3 firings
   in 144,823 tower-turns — and it was worth +5 games anyway.
   *Check*: none needed. Rarity is not a verdict; measure the outcome, not the frequency.

The trap is that level 2 *looks* like a completed reachability check. I wrote a table, counted
rounds, split the maps into "should move" and "should not", and registered a prediction — all
of it methodologically clean, all of it about the wrong subject. The unit of analysis for a
reachability check is **the robot that must act**, because the gate lives in its vision, its
action radius and its position, not in the map's global state.

The distinction sharpens for any mechanism that requires *adjacency* rather than *sight*.
Battlecode's transfer and build actions run at r²=2 to r²=9 while vision is r²=20 — so for
those, the world can be full of opportunity that no unit is ever positioned to take. Two
iterations died on exactly that geometry this session (17's splasher refill, 20's ferry), and
in both cases the fix is navigation, not a better threshold. **When the mechanism needs
adjacency, ask who drives the unit there before asking whether the opportunity exists.**

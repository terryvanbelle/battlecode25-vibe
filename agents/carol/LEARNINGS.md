# Carol — durable lessons (BC25)

## STANDING CONSTRAINTS — read these before proposing any evaluation

1. **No bot implementations may be downloaded from the web.** (Project rule, from the start.)
2. **No post-mortems from the 2025 contest year.** Other years are fair game.
3. **BC25 finals bots are a YARDSTICK ONLY** (project owner, 2026-09-07). They live on
   battlecode-dev outside this repo. Forbidden absolutely: reading their source, and examining
   **any game played against them** — no replay, log, trace, dump or arena view. Permitted: reading
   a benchmark **score** from a committed results file, nothing else. **The coordinator runs those
   matches, not me** — I must never add a finals bot to a gauntlet, an `OPPONENTS` list or
   `roster_extra.txt`. If I ever hold such an artefact: **stop and tell the coordinator.**

   The enforcement is structural — no replay is written for those games, so the artefact does not
   exist — which is stronger than a rule because it survives a session that never read one. The
   part a rule still has to cover is *requesting*: a benchmark bot in the frozen roster would look
   like a perfectly sensible proposal, since a never-changing opponent is exactly what that roster
   wants. It is excluded anyway.

   **Use the number as distance, never as a target.** Tuning toward a fixed external opponent is
   overfitting with extra steps — the same error as hand-picking a standing map list, which the
   charter forbids for that reason. The accept gate stays the within-run head-to-head; the frozen
   roster stays the absolute instrument; the tournament stays the independent-opponent instrument.
   Expect a bad score: carol sits last in the inter-agent standings while her own instruments read
   92–100%, and that gap is the self-referential blind spot itself. A third-party number is the
   only thing that can size it, which is worth more than a flattering one.


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
points (62.5% -> 30.0%), with 12 swept-losses to 4 swept-wins. **[SUPERSEDED 2026-09-08: the
sweep clause is NOT independent support — margin = 2*(swept - swept-against) identically. The
32-point drop stands, measured once. See the audit at the end of this file.]**

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
11/40, swept 3-14. **[SUPERSEDED 2026-09-08: the swept-loss count is a miscount; the identity
margin = 2*(swept - swept-against) determines SL = 12, not 14. See the audit at the end of this
file. The rejection itself is unaffected.]**

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

## Cost the price, not just the benefit — THREE times, three different disguises

(Was "twice in one session, two different disguises". Extended in place; both original cases
stand as written, and the third one below is a different shape worth separating from them.)

Three iterations, one family of error, and I did not recognize it the second time even though I
had just written up the first — nor the third, several hours after writing up both.

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

> **SUPERSEDED IN PLACE (iteration 31).** The "moppers idle on 95.1% of 78,480 turns" figure above
> is left as written because it was load-bearing for iteration 19a's decision, but it **no longer
> describes this bot**. Iteration 31 throttled mopper production with a paint floor, verified the
> realized share moved 44% -> 9.5% exactly as designed, and scored **25/50 — the null.** In the same
> game the un-throttled arm's moppers performed **112 unpaint actions and 28 mop swings** in one
> 250-round window against the throttled arm's 19 and 0. Moppers on the current build are active,
> and mopping enemy paint is part of how coverage is won. Two iterations (19a, 31) have now attacked
> mopper production on the strength of the 95.1% figure and both failed. Do not price a change
> against a utilisation number measured on an older build; re-measure it first.

**Iteration 26 (build SRPs) — and this one is a different shape.** Here I *did* cost the price.
I costed it repeatedly and correctly: 200 chips, ~90–150 paint, payback ~13 rounds, all written
down before building. Then I set the entry gate to
`rc.getPaint() >= MARK_PATTERN_PAINT_COST` — **25**, the cost of the *first step alone*. Placing
an SRP is a multi-turn transaction (mark → recolour 13 tiles → complete), and a soldier admitted
with 25 paint can perform step one and nothing else. 59–88% of marks were abandoned, burning
1,200 paint on DefaultMedium and 2,300 on Bunny — on a build whose soldiers I had *just* measured
as chronically paint-starved.

The first two omitted a price term entirely. **This one priced every step and then gated on the
cheapest of them**, which is why writing up the first two did not inoculate me against it.

**The rule that covers all three: gate on the total cost of the transaction, not on the cost of
entering it.** Any commitment with a non-refundable deposit has this shape — a marked pattern, a
reserved slot, a unit sent somewhere it must then return from. And the two failure modes look
nothing alike in the counters: an omitted price term shows up as a *disappointing benefit*, while
a mis-placed gate shows up as a **high abandonment rate with the mechanism visibly working**.
When a mechanism engages and still loses, check the abandonment rate before you doubt the
mechanism.

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

## Reachability has FOUR levels, and I have now been caught at each

(Was "three levels". Extended, not replaced: level 4 and the level-2 inversion below were both
measured after this entry was first written, and the original three still stand as written.)

A mechanism can fail to fire for four different reasons. They need different checks and only the
third is the one the algorithm's "reachability" pre-check actually names.

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

4. **The condition is guaranteed by the RULES' initial state, so a lifetime memory of it is a
   constant.** Iteration 24b latched "has this robot ever sensed an ally paint tower" and fired
   **0 of 185** asks — including 0 of 144 on the one map it was built for. `RULES.md`:
   `NUMBER_INITIAL_PAINT_TOWERS = 1`, and a robot spawns adjacent to the tower that builds it,
   so the flag is true on turn 1 for every robot that will ever exist. It faithfully recorded a
   fact the rules guarantee.
   *Check*: before building any "have I ever seen X" memory, ask what the **starting
   configuration** guarantees. A latch over a condition true at t=0 is not a rare condition.

**Level 2 has an inversion, and it is the same error with the sign flipped.** Iteration 20
assumed a condition existed in the robot's view because it existed on the map. Iteration 24a
assumed a condition would be *rare* in the robot's view because it is rare on the map — and its
guard fired **41 of 41** asks on healthy ground, because vision is r²=20 on a 50×30 map and
being out of sight of every ally paint tower is the *common* case. Both are now measured, in
both directions, so the rule can be stated without hedging: **a predicate's firing rate is a
property of the robot's information, not of the map.** Map-level statistics predict neither
that a condition will be available nor that it will be rare.

**The cheap way to settle it: bracket the predicate from both extremes.** 24a (fires always) and
24b (fires never) between them cost 4 games of VM time and no evaluation at all, and the pair
localised the useful condition far better than guessing a middle one would have. This is the
same move as a dose bracket around a parameter, applied to a *predicate*. When a guard's firing
rate is what is in doubt, build the two extremes first and read the bracket.

The distinction sharpens for any mechanism that requires *adjacency* rather than *sight*.
Battlecode's transfer and build actions run at r²=2 to r²=9 while vision is r²=20 — so for
those, the world can be full of opportunity that no unit is ever positioned to take. Two
iterations died on exactly that geometry this session (17's splasher refill, 20's ferry), and
in both cases the fix is navigation, not a better threshold. **When the mechanism needs
adjacency, ask who drives the unit there before asking whether the opportunity exists.**

## The zero arm is where the information is — two sweeps, two surprises, neither guessable

I swept two unit-share constants this session with the same design (zero arm, one interior arm,
the incumbent), and both results contradicted the hypothesis that motivated the run.

| knob | zero arm | shape found | outcome |
|---|---|---|---|
| `MOPPER_IN_20` (was 5) | 0 scores **35%** | concave, **incumbent far past the peak** | 2 accepted, **+6 games** |
| `SPLASHER_IN_20` (was 3) | 0 scores **12.5%** | concave, **incumbent at the peak** | both arms rejected |

**Neither shape was predictable from the other**, and the plausible unifying story — "carol
over-provisions cheap support units" — would have been half right and half expensively wrong.
The knobs look symmetric, sit three lines apart in the same function, and behave oppositely.

What the zero arm actually buys, concretely:

- **It makes the shape legible.** With only "2 vs 5" I would have had one number and no way to
  tell a slope from a peak. With 0 in the run, dose 2 and dose 5 could each be scored against a
  *common* opponent on identical maps, which is what exposed the concavity.
- **It prices the feature.** Deleting splashers costs ~50 points; that number did not exist
  before and it retroactively priced iteration 11, accepted ten iterations earlier on a 62.5%
  head-to-head and never re-measured.
- **It refutes the motivating hypothesis cheaply.** Both sweeps began as "this unit is wasteful,
  cut it". Both were wrong, and the arm that proved it was one I was running anyway.

The general rule I am taking from it: **when you propose removing or reducing something, the
zero arm is not a control, it is the experiment.** The interior doses tell you where to go; the
zero arm tells you whether the thing is worth having at all — and three times this session that
was the answer I had confidently assumed and got backwards.

A corollary on ordering: run the zero arm in the *same* run as the interior dose, never as a
follow-up. Cross-run comparisons are confounded by the map sample; within one run, opponents
share the sample exactly, and it is that exactness that let a 72.5%-vs-65.0% gap be read as a
real ordering rather than noise.

## Instrument the decision — but check the counter is as WIDE as the decision

The standing pre-check says to count the decision rather than the outcome, because a zero at the
output cannot separate "ran and failed" from "never ran". True, and it has paid for itself
repeatedly. But a decision counter has its own failure mode, and I built one this session:

Iteration 26a's `srpOk` counted `canMarkResourcePattern(rc.getLocation())` — the soldier's own
tile as the pattern centre. `RESOURCE_PATTERN_RADIUS_SQUARED = 8` means the soldier may centre a
pattern anywhere within r²=8, roughly **25 candidate centres**. So the counter asked about one
of twenty-five options and every number it produced was a lower bound.

It happened not to matter — a lower bound above zero already cleared the gate. But had it come
back near zero I would have written "the mechanism is unreachable" on the strength of it, and a
narrow proxy can only ever produce **false negatives**, which read exactly like refutations.

**Rule: when you instrument a decision, verify the counter's condition is the same width as the
decision the bot would actually get to make.** Ask what the API permits, not what the simplest
expression tests. A decision counter narrower than its decision is a refutation generator.

## Two consumers of one budget must partition it by an explicit decision

§5b warns that where two branches buy the same good from one budget, *the order they fire in
sets the allocation, by accident rather than by measurement*. Iteration 26 is the first time I
had that warning in hand **before** writing the second consumer, and the fix was nearly free.

carol's idle-soldier branch already splits itself for a different reason — iteration 14's
`frontFound` (an empty tile is visible; go to it) versus `frontNone` (nothing paintable anywhere
in vision). Measuring that existing counter cost **no VM time at all**, because it was already
being emitted into replays I had on disk:

```
              IDLE-ALLY   frontFound   frontNone
DefaultLarge      1032          292      740  (72%)
DefaultMedium     3443          809     2634  (77%)
Fossil            2947          340     2607  (88%)
gridworld         6647         1621     5026  (76%)
```

So iteration 26's SRP work was scoped to `frontNone` *only*. The two mechanisms now partition
the idle budget by a stated decision, and if that split is wrong it is wrong visibly and can be
re-measured. Had I simply written "if idle, build an SRP", the allocation between frontier-
seeking and SRP-building would have been decided by which `if` I happened to put first.

**The reusable move: before adding a second consumer to a budget, look for a counter the first
consumer already emits.** A bot instrumented per the algorithm usually already knows how its
budget divides, and the question can be answered from replays rather than from a run.

## Write a closed direction's re-opening condition as a testable predicate

The closed-directions ledger says re-opening needs "a specific reason the recorded cause no
longer applies". That is much easier to honour when the original entry stated its cause as
something checkable. Iteration 4/5 deferred SRPs with:

> it is a chip *sink*, and a sink is worth little until the chip *source* is fixed

which is effectively the predicate *"chips are still scarce"*. Twenty iterations later the
traces showed chips pinned at $1200–1700 for entire games while the binding resource ran dry —
the predicate had flipped, plainly and without argument, and the direction re-opened in one
paragraph instead of a debate about whether it "felt" under-explored.

The neighbouring entry shows the same discipline holding a door **shut**: tower upgrades were
closed with the condition "chips idle after both the money mix *and* SRPs are in". SRPs are not
in yet, so that one stays closed — same session, same evidence, opposite answer, no judgement
call required.

**Rule: when closing a direction, write the cause as a condition that could later be observed to
be false.** "Not worth it" cannot be re-opened honestly. "Worth little while X holds" can.

## `canAttack` is a legality check, not an efficacy check — and a bug class is never local

The largest single waste ever found in this lineage: **71–85% of all soldier attacks were
discarded by the engine**, burning 42–55% of the entire soldier paint budget, every game, on every
map measured. `workOnRuin` attacked tower-pattern tiles holding **enemy** paint. A soldier paints a
tile only if it is EMPTY or already own-team; `rc.canAttack()` returns true anyway, the engine
charges the full 5 paint, and nothing happens.

Three things generalise, and the third is the expensive one.

**1. Separate "may I do this" from "will this accomplish anything".** Every `can*` predicate in
this API answers the first question only. Cooldown, range, and cost are checked; whether the
action's *effect* is legal on that target is not. Any call site that picks a target must apply the
effect rule itself. Grep for `rc.attack(` and read every site against the effect rule, not the
guard.

**2. The symptom looked like six unrelated problems.** Before the cause was found I had, in one
session, separately measured: soldiers dying dry at ~50 rounds (77–94% at paint < 5); the ruin
branch consuming 56–71% of soldier turns; a realized build mix of 50% moppers against an intended
10%; the paint tower pinned in the [100,200) dead band on 27–49% of turns; splashers at 0.7% of
builds against an intended 15%; and a paint accounting that would not close by 41–53%. **All six
are the same bug.** When several independent-looking degeneracies appear at once, look for one
upstream cause before designing six fixes — and note that the accounting failing to close was the
only one of the six that pointed *at* the cause rather than away from it. That is what the
"close the accounting before you read anything off it" rule buys.

**3. I had already found this exact bug class, in another unit, and did not sweep.** An earlier
iteration fixed the splasher's targeting for precisely this reason — it "scored enemy tiles
anywhere in r²=4, so it preferred centres ringed by enemy paint it could not actually convert" —
and the same iteration never checked the soldier, the mopper, or the tower. The soldier's version
then survived for many more iterations while I chased its downstream symptoms.
**A bug class found at one call site is a hypothesis about every other call site of the same kind,
and testing it costs one grep.** When a fix is written, the commit should sweep the siblings.

## Two artefacts that agree are only evidence when they are actually independent

I measured soldier paint drain two ways offline and got 3.40 and 3.46 per turn — agreement to 2%,
which I read as corroboration. The true figure was **1.20–1.58**. Both routes differenced the same
per-turn paint series and both assumed paint leaves a robot only via drain or via an action the
replay logs; discarded attacks are logged nowhere, so the shared assumption was false and the two
"independent" checks were one method computed twice.

The tell was available and I missed it: the two agreed with each other but neither closed against
the *lifetime budget*, which is a third artefact of a genuinely different kind. **Reconcile against
an artefact that does not share your method's assumptions** — a total, a conservation law, a
number produced by the engine rather than by your parser. Agreement among same-family estimates
measures consistency, not truth.

This is the counterpart to the existing rule that the tell for a wrong referent is "two artefacts
that should agree and didn't". The complement is just as real: **two artefacts that agree may
simply share a blind spot**, and the cure for both is the same — pick the reconciling artefact for
its independence, not for its convenience.

## AUDIT (2026-09-08): swept counts and the win margin are the same number — three entries re-checked

Doctrine 14 now states the identity: every map is played from both sides, so wins = 2·SW + D and
losses = 2·SL + D with D the split maps; **D cancels and `margin = 2 × (swept − swept-against)`
identically.** An identity always agrees with itself, so a margin and its sweep counts can never
corroborate each other. This is placed deliberately against doctrine 13 ("a real effect shows up in
more than one place"), which is exactly what makes the second statistic *feel* like confirmation.

Superseding in place rather than deleting, because the affected conclusions were load-bearing.

**1. "Iteration 12b lost 32 points (62.5% → 30.0%), with 12 swept-losses to 4 swept-wins."**
Reconciled exactly: 30.0% of 40 games = 12 wins, so 2·4 + D = 12 gives D = 4, losses = 2·12 + 4 =
28, and 4 + 12 + 4 = 20 maps. Everything closes — **and that is the problem**: margin −16 =
2 × (4 − 12) is the same number written twice. **The conclusion is unaffected** (a 32-point drop is
a 32-point drop, measured once), but the sweep clause added no independent support and should not
be read as a second witness. What it *does* add is D = 4: only 4 of 20 maps were coin-flips, so
that loss was decisive rather than noisy — which is a genuinely new fact and the one worth keeping.

**2. "Iteration 15b: 11/40, swept 3–14." — DOES NOT RECONCILE, flagged unresolved.**
SW + SL = 17, so D = 20 − 17 = 3, which predicts wins = 2·3 + 3 = 9, not 11. The residual is 2
games and I cannot account for it: either the win count and the sweep counts come from different
slices of that run, or one is a transcription error. **I am not repairing it by picking whichever
number I prefer** — that is the wrong-referent trap in its most tempting form. The entry's
conclusion does not depend on the discrepancy (27.5%/11-of-40 is a clear rejection either way), but
the numbers are marked as unreconciled until the run directory is re-read.

**3. "Castle was a swept loss; Parking_lot was a swept win. Exactly inverted."** — **Correct as
written, no change.** This is not the aggregate identity: it names *which* maps swept which way to
check a pre-registered map-level prediction. Per-map sweep facts are a real projection of the data
that the aggregate margin cannot express. The identity only forbids treating the *totals* as a
second witness for the *margin*.

**The general rule to carry:** when a second metric is computed from the same games as the first,
ask whether it is a new projection of the data or an algebraic restatement. Aggregate sweeps vs.
margin: restatement. Split-map count D: new. Which map swept: new. Firing counts, per-turn
counters, and anything read from a replay rather than from the win/loss table: new.

### Entry 2's discrepancy is now RESOLVED — and the identity is what resolved it

The run directory (`20260907-133422`) has been pruned, so I could not re-read it. But the identity
does not need it: with 40 games over 20 maps, 11 wins, and SW = 3 (the log names all three swept
wins individually — DefaultMedium, Parking_lot, defensetower),

```
wins = 2·SW + D   ->   11 = 6 + D   ->   D = 5
SL   = 20 − SW − D = 20 − 3 − 5     ->   SL = 12
```

and every figure then closes: losses = 2·12 + 5 = 29, total 40, maps 3 + 12 + 5 = 20.
**SL is fully determined, and the recorded "swept 3–14" is a miscount of the swept losses; the
true value is 12.** The log's own wording gives it away — "14 maps *including* Castle, Bunny,
DefaultLarge, gridworld, PlumberGame" names five and asserts a total, which is where the slip
happened.

Two things worth keeping from this. First, the thing that made the discrepancy *solvable* was the
same identity that makes sweeps useless as corroboration — **an identity is worthless as evidence
and invaluable as a constraint**, and those are not in tension. Second, I resolved it without
picking the number I liked: SW was independently attested by an enumeration of named maps, the
game count was fixed, and SL followed. Had SW been the uncertain one, the honest answer would have
stayed "unresolved". The conclusion of the entry (iteration 15b rejected at 27.5%, prediction
inverted) is untouched.


## Independence of the DERIVATION is not independence of the REFERENT

Doctrine 14's extension, and I met it from both sides in one day. I had two offline estimates of
soldier paint drain agree to within 2% and read that as corroboration; both were wrong by a factor
of two, because both assumed paint leaves a robot only via drain or via a logged action. Different
arithmetic, same false referent. Separately, a second session elsewhere re-derived a statistic
without having seen the first derivation, and that too was worth nothing, because both routes read
the same post-spend quantity.

**Ask what a derivation measured, not what path it took there.** Agreement between two routes
bounds arithmetic error only; it says nothing about whether the quantity was the right one.

The sharp version, because the same data can be valid or invalid depending on the question:

| question asked of post-spend replay state | verdict |
|---|---|
| "how often *could* this tower have afforded a soldier?" | **invalid** — the turns it did build are exactly the turns recorded low; conditioned on the outcome |
| "how much of its life does this tower *persist* at 100–199 paint?" | **sound** — persistence is exactly what post-turn state records |

Same table of numbers, opposite verdicts. So the label to attach to a measurement is not
"valid/invalid" but "valid *for which question*". I had headed my own two columns "INVALID" and
"corrected", implying one repaired the other; in fact each is correct for a different question and
neither supersedes the other.

## Superseding in place must LOOK superseded

"Supersede in place, do not delete" is right — a withdrawn rule was load-bearing for whatever was
decided while it stood, so deleting it makes the older entries unreadable rather than merely wrong.
But it has a failure mode: a reader who greps lands on whichever row matches first, not the newest,
so **stale text keeps reading as live**. Nearly cited a superseded figure as current for exactly
this reason.

The fix is cheap and mechanical: every superseded figure or rule carries an inline
`**[SUPERSEDED <date>: what replaced it, and where]**` marker *at the point of the stale text*, not
only in a correction appended elsewhere. Applied retroactively here and in `TRAINING_LOG.md`.
Preserving the old text is right; leaving it indistinguishable from live text is the defect.

## A measured constant is only valid for the build it was measured on

Three consecutive iterations died on this, and the third one made it a pattern rather than bad luck:

| iteration | constant relied on | measured on | what it was on the current build | outcome |
|---|---|---|---|---|
| 31 | moppers idle on **95.1%** of turns | an older build | moppers **active**: 112 unpaints, 28 swings in one window | REJECT at exactly the null |
| 32 | idle budget is **72–88% `frontNone`** (deep ally ground) | iteration 25 | IDLE-ALLY is 77% / 33% / **1.4%** on three maps | REFUTED, 0 completions |

Both figures were sound when taken. Both were quoted, in good faith, about a bot that no longer
existed — and in both cases *the accepted iterations in between had specifically changed the thing
the constant described* (iteration 30 raised splasher production; 29 and 30 pushed soldiers to the
frontier). That is the tell: **the more relevant an old measurement is to a direction, the more
likely the accepts since then have invalidated it**, because relevance is what made it a target.

**Standing pre-condition, not an anecdote: before a constant from an earlier iteration is allowed
to carry a design argument, re-measure it on the current build, or state in the pre-registration
that it was not re-measured and treat that as the term most likely to fail.** Iteration 31 did
write that caveat down and it was precisely the term that failed — so writing it down is necessary
but is *not* a substitute for the re-measurement. The re-measurement is cheap: both figures above
were recoverable from a single 8-game probe already being run for another purpose.

## A probe must be the SAME WIDTH as the shipping decision — both mismatches are fatal

Iteration 26a recorded half of this: *"a narrower proxy can only produce false negatives."*
Iteration 32 produced **both** halves within one hour, which is what makes the rule general.

- **Probe wider than the mechanism → FALSE NEGATIVE.** Probe p demanded a fully-sensable, wholly
  clean cell and a blanket ruin guard, and returned `srpOk = 0` on all four maps. Its
  pre-registered kill condition fired and I was one decision away from closing a live direction on
  my own instrument's artefact. Two guards were provably too wide: full-cell sensing is impossible
  from 12 of the 25 standing positions in a cell at vision r²=20, and a ruin that already has a
  tower is not a conflict at all ("tower survives even if its pattern is later painted over").
- **Probe wider than the code you then SHIP → FALSE POSITIVE.** Probe q measured the tile-local
  decision across the whole action radius and returned 52–100% firing. The build I wrote from it
  considered only the soldier's own cell — a narrowing I made for bytecode economy, without
  measuring — and engaged on **0.26%** of turns.

So: **any width mismatch invalidates a probe; the direction of the mismatch only decides which way
you are fooled.** The practical guard is to write the probe's condition and the shipping condition
as the *same expression* wherever possible, and when they must differ, to say in the
pre-registration exactly how and why. A narrowing introduced after the probe — even one that looks
like pure optimisation — is a new, unmeasured hypothesis.

## Zero completions with a non-zero win rate is a trap, not a hint

Iteration 32's three arms all scored 5/8 while taking 0, 10 and 14 mechanism actions per game.
It was tempting to read the identical 5/8 as "the direction is worth a full run". It is the
opposite: a change touching ~10 of ~30,000 robot-turns *cannot* have moved three games, so the
5/8 is measuring something else — and had I bought the 100-game run on it, whatever that something
else was would have been attributed to the mechanism. **When the engagement counter says the
mechanism barely ran, the win rate is evidence about the baseline, not about the change.** Check
engagement *before* looking at the score, and check bytecode overruns before believing either.

## A variable's blast radius is where its VALUE ENDS UP, not where it is read

I reported `gauntlet-collect.sh` printing the workspace name instead of the bot that played, and
characterised it as **cosmetic** on this evidence: `grep -n '\$BOT' tools/gauntlet-collect.sh`
returned exactly one hit, the `echo` on line 54. That grep was correct. The conclusion was not.

The coordinator's fix (`0fd72ab`) records what I missed: `$BOT` is also handed to **`collate.sh`**,
which prints `bot=$BOT` at line 35 — inside the block piped to `tee "$OUT/summary.txt"`. So the
wrong label was **written into the run's summary file**, not scrolled past in a terminal. I
verified both sides afterwards: `gauntlet/20260908-063927/summary.txt` said `bot=carol` while its
`bot.txt` said `carol_i33`, and the post-fix run wrote `bot=carol_i34_4` correctly.

**The error was one of scope, not of method.** I did the right procedure — read what the code
computes rather than describing the symptom — and applied it to a single file, while the variable
crossed a file boundary (`collate.sh`'s own header even lists `BOT` among the names it is handed).
A single-file grep cannot see a cross-file hand-off, so it can only ever under-report reach.

Two things to carry:

- **When tracing a variable to size a defect, trace it across every file it is exported into, and
  ask specifically whether any use is inside a `tee`, a redirect, or a file write.** "Read once"
  and "stored once" are different facts, and only the second determines who is misled later.
- **"Cosmetic" and "written into an artifact a later session will trust" are different sizes of
  problem.** No number moved either way — that part was right — but a persisted wrong label
  misleads exactly the session-death recovery `gauntlet-collect.sh` exists for. A future session
  reading a recovered `summary.txt` would see the baseline's name where the build under test should
  be, and could reasonably discard a finished 100-game run or pay for it twice.

**This is the same error as the width mismatch recorded above, in a different medium.** There, my
probe's condition covered a different domain than the shipping decision. Here, my grep's scope
covered a different domain than the variable's actual reach. Both times I measured a narrower
domain than the one that mattered and reported the result as though it covered the whole. The
general guard is the same in both: **state the domain your check actually covered, and check that
it is the domain the claim is about.**

## A statistic that never lands in a file is a recollection, not a measurement

Iteration 34 was accepted and its commit message headlined `rho=+0.624 on the pre-registered
ruin-density prediction`. Recomputing it from the run's own `results.csv` one session later gives
**+0.244, t=1.21** — not significant. Every *other* number in that entry reproduced exactly (28/50,
swept 7/4/14, and both half-splits to the tenth of a percent), which is what makes the failure
instructive: the entry looked verified because most of it was.

The rho was computed inline, in conversation, and never written to a file. So nothing in the repo
could contradict it, and it propagated into a commit message where it now reads as an established
result. The half-splits survived precisely *because* they had been written down as a table.

**Rule adopted: any statistic that appears in a verdict must be produced by a committed script
that regenerates it from `gauntlet/<run>/results.csv`.** Not "was computed correctly" — *is
recomputable*. `carol-tools/covar/mapcovar.py` now does this for map covariates.

Two second-order lessons, both of which cost more than the first:

- **Sanity-check a new tool against a published number you expect it to match.** I found this only
  because I ran the new covariate tool on an old run to validate the tool. The tool was fine; the
  history was wrong. Validation runs discover errors in whichever of the two is actually broken,
  and you do not get to choose which.
- **Separate the gate from the argument, in advance, so a bad statistic cannot silently move a
  verdict.** Iteration 34's accept survived this intact — the pre-registered gate was
  win-rate-plus-sweeps and rho was never in it. Had I written "accept if the covariate confirms",
  a number I could not reproduce would have decided the iteration. Pre-registering the gate as a
  *specific arithmetic condition on the raw record* is what contained the blast radius.

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

## An aggregate gate cannot see a trade, and a roster of your own snapshots cannot either

Carol's tournament win rate rose 19.0% → 32.3% over two days. Stratified by map area, tiny maps
went **+40.8 points** and huge maps went **−5.8**; rho(win%, area) moved from +0.029 (flat) to
**−0.546, t = −5.57**. The lineage bought small-map strength and partly paid for it in large-map
strength, over a chain of individually-passing accepts. Both of my instruments were blind:

- **A single aggregate win rate over a random map sample hides a trade.** +20 on small and −5 on
  large clears `> 25/50` every time. The gate was not too loose; it was **unstratified**. Fix: the
  accept gate now reports and constrains the small-half and large-half win rates separately.
- **A frozen roster built from your own snapshots shares your blind spots, so they cancel.** My
  roster read 94–100% on every member and I logged that as "saturated". It was not saturation from
  strength — every opponent on it failed on large maps in the same way I did, so the deficit
  subtracted out of every head-to-head. **A yardstick made of your own past selves can only measure
  the axes you were already varying.** Building another synthetic archetype myself would not have
  helped: I would have built it out of the same assumptions that produced the blind spot.

The general form: **an instrument you constructed cannot find an error in the assumptions you used
to construct it.** The only reason this was findable is that the tournament supplies opponents
another lineage produced. It cost zero VM time — the data had been sitting in `tournaments/` for
hours while I ran gauntlets that could not answer the question.

Corollary worth its own line: **when a covariate turns up significant at t = −5.57 and your last
three accepts were argued at |t| < 2.2, stop and re-plan.** The strong signal is not a footnote to
the iteration in flight; it is the agenda.

## My accept gate had one fewer condition than it looked like (iteration 36)

The tournament report proves, for an N-map both-sides sample, `wins - N = SW - SL`. Checked on
iteration 36's own run: N=25, wins=28, SW=6, SL=3, split D=16; `2*6+16 = 28` and `2*3+16 = 22`.
Exact.

So the gate condition **"swept wins >= swept losses" is algebraically implied by "wins > 25/50"**.
For eleven iterations I have been writing a two-condition gate as three, and reporting a margin
and its sweep counts as two agreeing pieces of evidence when they are one number written twice.
The report warns about this in as many words and I encoded the error into my gate anyway. *Reading
a warning is not the same as auditing your own instrument against it.*

**What the sweep counts add that the margin cannot is D, the split count** — decisiveness, not
direction. On iteration 36, D=16 of 25: **64% of maps were coin-flips decided by spawn side**,
which is the honest explanation for why a real mechanism produced only a 28/50 headline.

> **SUPERSEDED (2026-09-08, see "My gates were set against se = 0" below).** The floor adopted
> here is *algebraically* independent of the margin, which is what this paragraph checked, and
> that is not the same as being *statistically* resolvable. Measured on my own 59 arms, a
> dead-even arm reached SW=9; five of the nine arms at 24-26/50 clear SW >= 5. The floor is
> passed by a majority of bots that are exactly as good as their opponent, so it excludes
> nothing. It is retired as a gate and kept as a descriptive statistic. The reasoning below is
> left intact because the algebraic half of it is correct and still worth having.

**Replacement, and the check that it is not post-hoc rationalisation.** New condition 2 is an
absolute floor, **swept wins >= 5 of 25**, which is genuinely independent: `wins=28` is compatible
with `(SW,SL)` of `(3,0)`, `(4,1)`, `(5,2)`, `(6,3)`..., so the floor constrains D and is not
implied by the margin. **I checked what it does to the verdict I had just reached before adopting
it: iteration 36 has SW=6, so it still passes, and the change alters no past decision.** Adopting
a stricter gate that happens to spare the result in hand is exactly the move that needs stating
out loud, so I am stating it.

## A milestone hash that exists but is not mine is plotted, not skipped

`progress/milestones.txt` carried `d28ec3f` for the area-stratification milestone. That hash
resolves — to a commit outside this lineage. `tools/plot_progress.py` calls
`pl.commit_date(repo_root, commit)`, which resolves against the whole repo and only prints
"not found; skipped" when the hash resolves to nothing at all. **A mistyped hash that happens to
exist is therefore placed silently at the wrong date.**

Honest sizing: here the wrong commit was 3 minutes from the right one (`0ef9308`), so the chart was
visually correct and the defect was invisible. The failure mode is real, the instance was harmless,
and I am not going to inflate it. Corrected the line; reported the tooling gap rather than
patching around it, since `tools/` is coordinator-owned and the same trap sits in front of all
three lineages.

## The git INDEX is shared between the three agents, and it swallowed my commit

Iteration 37's pre-registration — the training-log entry, both candidate source trees and
`trajectory.py` — was staged with `git add <carol paths>` and, before my `git commit` ran, another
agent committed. Their commit took **my staged files** with it: `118270b`, whose message is about
their own work, contains all four of my files and none of my message.

Nothing was lost and HEAD still compiles, but the attribution is wrong and the pre-registration
is recorded under a commit that does not mention it. Noting the hash here so a future session
looking for "where was iteration 37 pre-registered" can find it: **`118270b`**.

**Diagnosis, stated as what actually happened rather than the symptom.** `MULTI_AGENT.md` warns
that the *working tree* is shared. The sharper fact is that **`.git/index` is shared too**, so
`git add` publishes my changes into a staging area any of the three of us can commit from. It is
not a race I can win by being quick; `add`-then-`commit` is two operations against shared mutable
state with an arbitrary gap between them. The same window explains the earlier oddity in this
session where a `--rebase --autostash` left my staged files unstaged.

**Fix, adopted from here on: never stage as a separate step.** `git commit --only <paths> -F -`
commits exactly the named paths regardless of what is in the index, in one operation. It cannot
sweep another agent's files in and cannot leave mine sitting where another agent will sweep them.
The window is not zero — nothing here can make it zero — but it removes the step where my work
sits exposed.

Reported to the coordinator rather than only worked around: the same trap sits in front of all
three lineages, and `git add -A` (already forbidden) is the loud version of a hazard whose quiet
version is plain `git add` of one's own paths.

## The frozen roster un-saturates itself, and my "the roster is blind" note is now out of date

I recorded earlier this project that the frozen roster had saturated at 94-100% and could no
longer discriminate, and I built `carol_racer` to try to fix it (which failed, for the separate
and better reason that a yardstick I construct inherits my blind spots). The roster is now:

```
carol_iter0 carol_iter1 carol_iter7 carol_iter21 carol_iter35 carol_rush carol_turtle examplefuncsplayer
```

**`carol_iter35` is in it.** The roster is derived automatically as "iteration 0, then every 5th
accepted snapshot", so it picks up recent strong snapshots on its own as the lineage advances. Its
top member is no longer a bot from the distant past that everything beats — it is the immediate
predecessor, against which iteration 36 measured 28/50. That is the opposite of saturated.

**So the instrument repaired itself by the mechanism it was designed with, and the fix I went
looking for was unnecessary.** The correct move when a frozen instrument saturates is to check
whether its own refresh rule will fix it before building a replacement — I built the replacement
first and only checked the roster's composition afterwards, in a lull, by accident.

Deferring the roster run itself for now with the reason stated rather than silently skipping it:
it is 8 opponents x 50 = 400 games, a gauntlet is in flight, and the twice-daily tournament is
about two hours out. It should be run once iteration 37 resolves, and it will now produce a
point that means something.

## "Realized != intended" says one of them is wrong, and I assumed four times it was the realized one

Iterations 30, 35 and 36 were all found by one recipe: compare the *realized* behaviour against
the *intended* behaviour, find the gate causing the divergence, make the gate reachable. All three
were real and all three were accepted. Iteration 37 ran the same recipe on `SPLASH_FLOOR = 2000`
and lost **3/50, 0 of 26 on the large-area half**, with the covariate reversing sign
(rho = -0.491, t = -2.70 against a pre-registered rho > 0).

**The recipe has an unstated premise: that the *intended* side is correct.** The intended mix here
is `SPLASHER_IN_20 = 3`, a constant from iteration 3, never validated against anything. The gate
was not corrupting a good policy — the gate *was* the policy, silently correcting a stale constant
that the roll had been getting wrong for thirty iterations.

So the general form: **a divergence between realized and intended is evidence that one of them is
wrong, and which one is an open question every time.** Ask it explicitly. The cheap version of the
question is "is the gate doing work?", answerable by removing it — which is what this run did, at
the cost of learning it the expensive way.

**Three confirmations of a heuristic is exactly when it stops being checked.** The fourth case fit
the template so well that I wrote "the fourth gate-as-off-switch in this lineage, and the first one
I built myself" into the pre-registration as though the pattern-match were the finding.

**What it bought, which is real.** Forcing splashers past the cheaper units is worth roughly 44
points of win rate against the same opponent family, and my instrument had never measured it,
because every gauntlet I run is carol against carol and both sides carried the same gate. An
accepted iteration's *size* is invisible to a within-lineage instrument; only removing it measures
it. Iteration 30 accepted at 28/50 and is worth ~44 points.

## Pre-registering the weak link is worth more than pre-registering the gate

The pre-registration named the causal chain (gate -> soldiers -> ruins claimed -> towers -> income)
and, in an addendum written before any game was played, identified **link 2 as the weak one**, on
rho(soldiers built, ruins claimed) = +0.199, t=+0.86, ns — with the consequence stated in advance:
"if soldier share rises and towers do not, the fault is ruin *conversion*, not affordability."

That is exactly what happened. Soldier share 62.2% -> 93.7%; tower count +0.30, higher in 2 of 6
games. **1,078 soldiers bought 0.3 of a tower.** Because the consequence was written down first,
the rejection came with its diagnosis attached instead of needing a second run to find one.

Also worth keeping: the registered **price** came due at twice the size of the benefit. Coverage
289 against 612 — 53% less ground painted, in 0 of 6 games more. 41 splashers produced 289
coverage; 338 produced 612. Registering a price turns "it lost" into a number that explains why.

## My gates were set against `se = 0`, and the tool that says so was already in the repo

Flagged by the coordinator after another lineage hit it; I checked the magnitude on my own runs
rather than take the number on trust, because the honest value is empirical and lineage-specific.

**The error, stated precisely.** The engine is deterministic, so a rerun on the same maps
reproduces byte-for-byte. That is true, and it makes `se = 0` for the question *"what happened on
these 25 maps"*. An accept asks a different question — *"does this change help over the map
population"* — and generalising from a 25-of-75 draw carries real sampling variance. Same numbers,
two referents; I had been quoting the precision of the first as if it licensed the second. This is
the wrong-referent error applied to the project's foundational assumption, which is why it survived
37 iterations: the premise it rests on is *correct*.

**The estimator.** Each map is played both sides, so per-map wins `w in {0,1,2}` is the natural
unit and it is *paired by construction* — map difficulty and spawn advantage live inside `w` and
cancel, which is why the sd of the difference is smaller than the sd of either arm's raw count.
A 50-game head-to-head is `sum(w)` over `n=25` maps drawn without replacement from `N=75`:

    Var(count) = n * s^2 * (N - n)/(N - 1)

The `(N-n)/(N-1) = 50/74` finite-population term cuts the sd by 18% and is not a nicety: a third
of the corpus is in every sample. `carol-tools/gatepower.py` computes this over every arm I have
ever run.

**The measurement (59 arms, all my own runs).** Pooled median sd = 1.79 wins, but that pools
lopsided arms where `w` is pinned at 0 or 2 and the variance is structurally small. **The accept
question is only ever asked of a near-even arm**, and restricted to the 18 arms at 20-30/50 the
median sd is **2.21 with fpc, 3.00 without** — and the without-fpc figure reproduces
`tools/map-resample.py`'s jackknife to two decimals, which cross-validates both estimators.

    a one-sided 95% accept needs >= 28.6/50, against the >25/50 I had been using.

**What that does to my own history.** `tools/map-resample.py` prints the distance from the mirror
null in sd *directly on the run I accepted from*, and I had not been reading that line:

| iteration | h2h | distance | resolved by the margin? |
|---|---|---|---|
| 35 | 33/50 | **+2.91 sd** | yes, comfortably |
| 36 | 28/50 | **+1.03 sd** | **no** — one-sided p ~ 0.15 |
| 34 | 28/50 | ~+1 sd | **no** |

Iterations 34 and 36 sit inside the band where a 50-game arm cannot separate an effect from a map
draw. In both I declined to let the margin carry the accept and rested it on independent evidence
instead — a pre-registered covariate, and a manipulation check showing 5 moppers against 367.
**That instinct was right, and this is the reason it was right rather than merely cautious.** Both
accepts stand, but they stand on the mechanism evidence alone; the headline never supported them.

**The floor I adopted eleven iterations too late was also inside the band.** I replaced
"SW >= SL" (algebraically implied by the margin) with "SW >= 5 of 25", checking only that it was
*algebraically* independent. It is. It is not *statistically* resolvable: among my nine arms at
24-26/50 — bots dead even with their opponent — SW ran 1, 2, 3, 4, 4, 4, 6, 7, **9**, and five of
the nine clear 5. A floor a majority of null arms passes excludes nothing. **Algebraic
independence is not evidential independence, and I checked only the half that was easy to check.**

### The gate I am adopting, and the one number that makes it cheap

The corpus is finite and small, and the fpc has a consequence worth stating plainly:

| maps played | games | sd(count) | margin needed |
|---|---|---|---|
| 25 | 50 | 2.4 | 28.6/50 (57.8%) |
| 40 | 80 | 2.5 | 44.2/80 (55.3%) |
| 50 | 100 | 2.4 | 53.9/100 (53.9%) |
| **75** | **150** | **0** | **any margin > 0** |

**At `n = N` the map-sampling error is exactly zero** — not small, zero — because there is no
longer a sample: you hold the population, and the engine's determinism then leaves no other noise
source at all. 150 games buys an *exact* answer to "does this beat the incumbent over the corpus".

The over-claim to avoid, stated before I am tempted by it: that is exact **for the corpus**, not
for maps in general. The 75 maps are themselves a sample of the space of maps, and no within-
corpus design can measure that residual — the tournament is the only instrument that touches it.
Playing all 75 is not the hand-picked map list my charter forbids: a complete population has no
selection to bias. The real cost is that repeated full-corpus tuning makes the corpus a training
set, which resampling at least dilutes.

**Standing gate from iteration 38 on:**

1. **Screen at 25 maps / 50 games.** `>= 29/50` accepts (clears +1.645 sd with the fpc,
   +1.34 sd without — I take the conservative form and require 29). `<= 25/50` rejects.
2. **26-28/50 is UNRESOLVED, not accepted.** Confirm on a *disjoint* map sample by pinning the
   complement of the screening run's `maps.txt`, and pool. A replication on disjoint maps is the
   coordinator's test and it is the only one that estimates the true se rather than assuming one.
3. **Report `D`, the split count, always; gate on it never.** It is the one thing the sweep
   counts carry that the margin does not, and it is descriptive.
4. **Quote the sd distance from `tools/map-resample.py` in every verdict.** The line was always
   printed. Not reading it is what this entry is about.

## `p` in the replay dump counts painted TILES, not painting units — caught by an impossible ratio

Building the splasher-utilisation counter I printed a "soldier paint rate" of **3163%** of one
paint per soldier-turn. An impossible number is a gift: it cannot be argued with, only explained.

The dump line reads `sold0 spl9 ... acts[p707 u0 a33 s73 m0]` — 707 paints on a round where the
team fielded **zero soldiers**. `p` counts `PaintAction`, and the engine emits one per *tile*, so
a splasher's ~10-tile disc registers as ~10 paints (707/73 = 9.7, which is the splasher disc).
`p` is a tile counter that no unit owns.

Two things worth keeping:

- **The denominator was mine, the numerator was the engine's.** I divided a tile count by a unit
  count and called it a per-unit rate. Every number in that column was meaningless, and the ones
  that were *not* obviously impossible — 19.4%, 17.4% — looked entirely plausible and would have
  been quoted. Only the rows where the population went to zero exposed it.
- **The splasher column next to it was fine**, because `s` counts splash *actions* and `spl`
  counts splashers, and both are per-unit. Same table, same shape, one column valid and one not.
  A ceiling is what told them apart: splash utilisation has an exact engine ceiling (0.2/round
  from the +50 cooldown) and sat sensibly under it, while the soldier column had no ceiling I had
  bothered to write down, so nothing flagged 3163% except my reading it.

**Rule: give every rate an explicit ceiling before you print it.** A rate with no stated maximum
cannot be sanity-checked, and the one in this table was wrong by a factor of 30.

## The late game is all splashers and no soldiers, and I had never looked

Same dumps, incidentally: on Castle at round 1800 both teams field `sold0 spl9`. Carol converges
to an **all-splasher late game with zero soldiers alive** — and only soldiers call `workOnRuin`,
so from that point on the bot cannot claim another ruin at all. Not acted on this iteration
(iteration 38 is already committed to one mechanism), recorded so it is not re-discovered.

## I measured a property of the GAME and diagnosed it as a property of my BOT

Iteration 38's motivating statistic was that **88% of carol's unit deaths are paint starvation,
not combat** — 3,905 of 4,450 across 16 replays. Correct, and I read it as a carol defect.

Four tournament games later: bob starves at 91-94%, alice at 57-81%. Everybody starves. RULES had
already written down the reason and I had quoted it in the same pre-registration without hearing
it — *no unit damages enemy robots' HP directly*, so attrition in BC25 is tower fire plus paint
starvation, and starvation must dominate for every bot that ever existed. **A statistic with no
comparison group cannot distinguish "my bot does this" from "this game does this",** and 88% of
anything feels like a finding.

What makes this specific rather than a platitude: **every instrument I own is made of my own
code.** Gauntlet arms are carol against carol; the frozen roster is carol against older carol.
None of them has a comparison group in the sense that matters, so none could have caught it. The
tournament could, and did, in four games and about ten minutes of VM time. The training algorithm
names this as the self-referential blind spot; this is what it looks like from the inside, which
is *not* like an error — the number was real, reproducible, and pointed at a genuine mechanism.

**The same table also contained the actual deficit**, which I would not have gone looking for:
carol paints roughly half what its opponents paint on large maps (281/377/300 against 592-683)
while fielding a third to a half of their standing army. Same death rate, half the units alive.
So the trip was worth it — but what it bought was a *correction*, not a confirmation.

**Rule adopted: before a statistic about my bot motivates an iteration, get one number for the
same statistic from an opponent my lineage did not produce.** Four tournament dumps cost minutes
and are already on disk. I have run 38 iterations without once doing this.

## Check WHICH BUILD the tournament played before reading anything into it

The same four dumps showed carol building two moppers per soldier — 887 against 425 — a 60-70%
mopper share against an intended 10%. I began writing it up as a live deficit.

The tournament exports HEAD at tournament time, and its report says so plainly:
`carol @ 6c55fc4`, which is **iteration 29**. Iterations 30-36 have never played an external
opponent. The mopper flood is the exact fault iteration 36's `PAINT_FLOOR` was built to fix, so
the table is not a current deficit at all — it is **external retro-validation of a fix I have
already shipped**, which is close to the opposite conclusion.

That distinction carries real weight here, because iteration 36 was accepted at 28/50, +1.03 sd —
*statistically unresolved* under the gate I re-set today — and rested entirely on a within-lineage
manipulation check. The same fault, at the same magnitude, measured against opponents my lineage
did not produce, is the strongest support that accept has ever had. It still does not show the fix
*worked*: only the next tournament, the first to play a post-29 build, can show that.

**Rule: read the "What played" section of the tournament report before reading its numbers.** A
lineage that commits several accepts between tournaments is always looking at a stale bot, and the
staler it is the more confidently it reads as a live finding.

## A gate that FIRES is not a gate that MATTERS — 50x the mechanism, 7% of the outcome

My reachability doctrine says: before building a mechanism, check the gate can actually fire.
Iteration 38 passed that check twice over — the decision fired 5,007 times at a 93% hit rate, and
paint transfers rose **fiftyfold**, from 94 to 4,758.

It reduced starvation deaths by **7%**.

Fifty times the refilling, and the units starved anyway. The doctrine answered "can this run?"
and I heard it as "is this the constraint?" Those are different questions and only the first is
cheap. **Reachability is necessary and nowhere near sufficient**, and the gap between them is
where a 100-game run goes.

The tell was available in advance and I did not compute it: the mechanism's *ceiling*. A refill
moves paint from a tower to a unit. It creates no paint. So the most it could ever do is
re-allocate a fixed budget — and re-allocating a budget cannot increase the total work done
unless the old allocation was wasting some. I never asked what the ceiling was, only whether the
gate would open.

**Rule: alongside "can this gate fire?", compute "if this gate fired on every eligible turn, how
much could the outcome move?" If that number is small, the reachability check is irrelevant.**

## Ask how the bot ALREADY solves the problem before adding a second mechanism for it

Iteration 38 added return-to-refill because 88% of carol's deaths are starvation. What I never
asked is how carol's units get paint *today*. The answer was two lines of a replay trace:

```
round 39  soldier id10270  (9,35)  paint=7    SPAWN id12046(T1,PAINT_TOWER) at (9,34)
round 41  soldier id10270  (10,35) paint=199
```

The soldier spends itself down to 7 paint converting a ruin into a paint tower, then refills from
the tower it just built. **Carol's soldiers do not travel to refill points; they manufacture
them.** The loop is local, the walk is zero, and the trip leaves a tower behind. That is why the
incumbent needs 94 transfers where my version needed 4,758 to do worse.

My mechanism did not fill a gap. It **competed with a better mechanism already in place**, pulling
low-paint soldiers off the ruins they were converting — soldiers built doubled (64 -> 128) while
towers alive fell 24%, which is that displacement written in numbers.

**The generalisation is uncomfortable, because I have a routine for the opposite error.** The
Phase 0 API sweep is a disciplined search for capabilities the bot *never uses* — and it found
messaging, correctly. There is no matching routine for capabilities the bot *already uses well*,
and that asymmetry biases every iteration toward addition. An unused API method is visible in a
grep; a working loop is invisible unless you trace a single robot for forty rounds, which costs
one cached dump and which I had never once done before this iteration.

**Rule adopted: before adding a mechanism for problem X, trace one robot end-to-end and write
down how the bot solves X today — even if the answer is "it doesn't".** If there is an existing
loop, the new mechanism must be argued against *it*, not against nothing.

**Corollary that sizes it:** the incumbent's loop is a *pump* (a soldier trip produces a tower)
and mine was a *drain* (a soldier trip consumes tower paint). When a bot has a mechanism that
creates the scarce resource, a mechanism that merely moves it around is competing for the same
unit-turns at strictly worse value.

## Three times in one session: a column whose NAME implied a normalisation it did not have

1. **`p` counts painted tiles, not painting units.** I divided it by a unit count and printed a
   "soldier paint rate" of 3163%.
2. **`twPaint~` and `tw~` in my pooled table were sums of per-map means, not means.** I quoted
   "towers alive 20.1" and "9,748 tower paint" and reasoned from both.
3. **`sd(win count)` pooled over all arms was not the sd of the arms that gate an accept** —
   lopsided arms have structurally tiny variance, so pooling understated it exactly where the
   gate lives (1.79 pooled against 2.21 for near-even arms).

Same defect three times: **a label that reads as normalised over something it was never divided
by.** All three produced numbers that were plausible enough to quote, and in two of the three the
plausible rows were as wrong as the absurd one — it was only the absurd row (3163%, an arena that
disagreed with a table) that made me look.

**What actually caught them was never re-reading the code.** It was an external check each time:
an impossible ratio, a rendered arena that contradicted a table, and splitting a population that
should have been split from the start. Re-reading a script that computes what you told it to
compute cannot surface an error in what you told it.

**Two habits adopted, both cheap:**
- **State the denominator in the header, not the quantity.** `tiles/soldier-turn`, not `paints`;
  `sum of per-map means`, not `twPaint~`. A header that names the normalisation cannot silently
  imply the wrong one.
- **Render the thing once before trusting a table of it.** One ASCII arena at one round cost a
  cached dump and caught an error I had already committed to the training log.

**And the ratios were fine all three times.** In the pooled-sums case both arms were summed
identically, so every ratio — tower paint −71%, towers −24%, coverage −51% — was exactly right
and the verdict never depended on the broken absolutes. Worth stating because the instinct on
finding an error like this is to distrust the whole table, and the disciplined move is to work out
which claims actually rested on the broken quantity. Here it was one inference (that tower paint
is abundant late), and the per-map spread — 7,813 against 423, an 18-fold range — refuted it
outright.

## Carol's units are TETHERED to towers by paint, and two iterations attacked the tether from opposite ends

Iterations 38 and 39 were the two halves of one mistake, and neither was visible as such from
inside itself.

| | change | link 1 | result |
|---|---|---|---|
| **38** | low-paint unit walks **toward** the nearest remembered tower | fired 5,007x, 93% hit, refills **50x** | 17/50, −3.10 sd |
| **39** | non-firing splasher walks **toward the frontier** (away from towers) | fired, 89.8% found a frontier | 17/50, −3.50 sd |

Both mechanisms ran exactly as designed. Both lost by roughly the same margin. Both dose ladders
were **monotone toward zero** — less of the mechanism was better at every setting tested.

**The single fact that explains both:** `transferPaint` requires r2<=2 — adjacency — for every
unit type, hardcoded in the engine. A unit's paint is therefore a *tether* to the tower that
filled it. It can spend that paint anywhere, but it can only get more by physically touching a
tower.

- **38 pulled the units in.** Refills rose fiftyfold and drained the tower stashes by 71%, and
  tower paint is what *builds* units: splashers −29%, towers −24%, coverage −51%.
- **39 pushed the units out.** Splashers reached the frontier and ran dry there permanently —
  `noPaint` 27.8% -> 47.0% — and *fired fewer shots than the incumbent*, 629 against 663.

**So the tether length bounds carol's territory, and neither shortening nor lengthening the leash
helps.** The arena picture is the same fact: carol boxed into a corner while bob spans the map.

**What follows, and it is not another movement change.** The tether is anchored at towers, so the
only way to reach further is to *move the anchors* — put more towers further out. That is the
soldier -> ruin -> tower pump, which is also what iteration 38's replay trace found the incumbent
already doing well (a soldier spends to 7 paint building a tower, then refills from it two rounds
later). **Two consecutive iterations tried to out-think a loop that was already the right one.**

**The generalisable form:** when two opposite changes to the same variable both lose by the same
margin, the variable is not the lever — something *else* is holding the outcome fixed, and the
next iteration must name what. I spent two runs establishing this and could have spent one, had I
asked after iteration 38 what the *opposite* change would predict.

## Price the SECOND-ORDER cost of a resource trade, not just the ledger entry (iteration 40)

Iteration 40 raised the money-tower share to buy chips, and I pre-registered the trade honestly as
an income ledger: each money tower forgoes 5 paint/turn, each upgrade it funds adds 5 paint/turn,
so the trade is roughly break-even and wins only if the chips buy more than one upgrade per
forgone paint tower. That arithmetic was correct and it was less than half the cost.

**What it missed: the chips do not sit in the treasury. They buy units, and a unit's build cost is
200 PAINT drawn from the building tower's own stash.** So the trade is charged twice — once for
the paint income forgone, and again when the chips it bought are spent back against the paint
account. On `TheBest` the candidate built 153 soldiers to the incumbent's 25: ~30,600 tower paint
against ~5,000, and its median tower paint ran at 993 against 3,082.

The generalisation, and it is not specific to money towers:

> **When you trade supply of a binding resource for supply of a non-binding one, ask what the
> non-binding resource is spent ON. If spending it creates demand on the binding resource, the
> trade is charged twice and your income ledger prices one of them.**

The galling part is that I had the fact written down. `RULES.md` said money towers generate no
paint and that "chips accumulate uselessly unless spent on towers/upgrades/SRPs". I read that
sentence as *chips are useless* and never read the subordinate clause as *here is what happens
when they stop being useless*. **A note that states a fact conditionally is only as good as the
condition you remember to check** — I have now rewritten that passage to state the second-order
cost as its own paragraph rather than as a dependent clause.

## A pre-registered discriminator that CLEARS its suspect has done its job (iteration 40)

Before the run I registered: *if iteration 40 fails the way iteration 37 did, splasher builds will
fall.* They did not fall — they held on the losing maps and rose on the winning one. The tidy
story ("cheap units crowd out splashers, same as 37") was available, plausible, and false, and I
would have filed it, because iteration 40 also failed and a ready-made mechanism for a failure is
very hard to decline.

**The check's whole value was in coming back negative.** It removed the explanation I was going to
reach for and left me with no account at all, which is the only state in which I actually go and
measure. I have been writing weak links as *predictions of how the candidate might fail*; the more
useful framing is *predictions that will stop me reusing last iteration's explanation*. Register
the discriminator against your own most likely misdiagnosis, not only against the mechanism.

## Reproduce one WIN before reading a loss sample as a mechanism (iteration 40)

The gauntlet pulls back only the candidate's losses. I analysed four of them and found a 2-6x
soldier surge in the candidate, which looked exactly like a mechanism firing. The engine is
deterministic, so reproducing a swept-WIN map costs one match; I ran it, and the sign flipped —
on the map it won, the candidate built the *fewest* soldiers and the *most* splashers.

So the surge was not the mechanism operating; it was a marker of the games it lost. **A quantity
measured only on losses cannot distinguish "the cause of losing" from "what losing looks like",
and the losses/ directory quietly guarantees that sample.** One deterministic re-run of a won map
is the cheapest bias check available in this project and I should run it every time a loss-sample
number is about to become a mechanism claim.

## A one-match PRE-FLIGHT before every gauntlet, gated on link 1 only (iteration 41)

Iteration 41's first build completed 5 resource patterns and activated none. Had I gone straight
to the gauntlet I would have spent 100 games measuring the win-rate of a mechanism that was not
running, and the verdict would have been a true number about a false thing — "SRPs don't help"
rather than "my SRPs never activate".

One match costs ~1% of a gauntlet and answers a strictly prior question: **does the mechanism fire
at all?** It ran four times on iteration 41 and rejected three builds. The rule I am adopting:

> **Never spend a gauntlet until one match has shown link 1 firing.** The pre-flight is not a
> weak evaluation — it is a different question, and it is the one that must be answered first.

This works only because link 1 was chosen to be a *directly readable* quantity rather than an
inference. The active-SRP counter had read 0 in every game this lineage ever played, so any
non-zero value was proof. Pick link-1 instruments with that property on purpose.

## "The counter says zero" is consistent with several faults that have DIFFERENT remedies (it 41)

`completed 5, active 0` was equally consistent with: a hand-decoded pattern in the wrong
orientation; a chip shortage at the completion gate; an enemy raid; and friendly fire. Four faults,
four different fixes. I picked the one my pre-registration had already named ("place them deeper"),
built it, and it was a **no-op** — every tag count came back identical to the byte.

Rendering the arena settled it in one look. At round 650 the pattern read exactly
`AAaAA/AaaaA/aaAaa/AaaaA/AAaAA`; at 680 two tiles had gone from ally SECONDARY to ally PRIMARY.
Still our paint. **Our own splashers were bulldozing our own patterns.**

> **When a counter reads zero, enumerate the faults consistent with that zero before choosing one.
> If more than one has a different remedy, the counter cannot pick between them and you must go
> and LOOK.** A pre-registered remedy is a hypothesis, not a diagnosis, and mine had 1-in-4 odds.

Third time a rendered picture has beaten a table for me. The pattern is not that pictures are
better; it is that a *tabulated* quantity answers the question you thought to ask, while a rendered
one shows the quantity you did not.

## Ask what your OWN units do to your own state (iteration 41)

Every failure mode I had catalogued was about the opponent or about scarcity. The actual killer was
endogenous: a splasher paints ally-primary across its whole footprint and scores centres by enemy
and empty tiles, so a *perfectly correct* splash at a legitimate target beside a resource pattern
converts its secondary tiles to primary and resets the 50-round activation clock. No bug, no enemy,
no shortage — two of my own subsystems with incompatible ideas about what a tile is for.

Worth generalising, because carol now has several kinds of tile with meaning beyond "painted":
tower-pattern tiles, resource-pattern tiles, and plain territory. **Any unit that writes to a
shared surface must know which regions carry meaning it can destroy.** I expect more of these as
the bot gains structure, and the tell is a feature that works in isolation and dies in situ.

## A cache keyed on a MUTABLE path serves stale answers silently (iteration 41)

`carol-tools/mixcheck/dumpcache.sh` keyed its cache on the replay's path plus flags. But
`vm-match.sh` writes every rerun of the same pairing+map to the *same filename*, so re-running a
rebuilt bot and re-dumping returned the previous build's analysis — the cached file was three
minutes **older** than the replay it claimed to describe.

It cost me a wrong inference for several minutes, and it was nearly worse: two different builds
produced byte-identical numbers, which I read as "the cache is stale" when in that instance the
build genuinely had not changed behaviour. **Two failure modes producing the same symptom, again.**
Fixed by keying on the content hash. The general rule: **a cache key must name the CONTENT, not a
location that content can be replaced at** — and a filename that a tool deliberately overwrites is
the worst possible key.

## Replay inspection is for MECHANISM, never for VERDICT (iteration 41/42, the costly one)

The gauntlet had already answered: `carol_i41_a` 27/50, large maps 9/18. I then opened one loss
replay from `losses/`, saw a collapse on `DefaultHuge`, and built **four** fixes for it across
**six** VM matches. Every diagnosis was wrong, and the map was never broken — the candidate went
**1/2** there, not 0/2. I had substituted one draw for the distribution.

The structural trap, because it is built into the tooling:

> **A gauntlet gives you a distribution. The `losses/` directory gives you its LEFT TAIL, by
> construction.** Opening a tail replay and asking "why does the candidate lose?" presupposes a
> pattern in a sample selected for its absence. The verdict was already computed and no amount of
> looking at one game can revise it.

So: use replays to ask *did link 1 fire* (a mechanism question, answerable from one game because
mechanisms are deterministic), never to ask *why did it lose* (a distributional question, not
answerable from one game at all). I already had the milder version of this lesson — "reproduce one
WIN before reading a loss sample as a mechanism" — and it was not strong enough, because it still
licensed reading a *verdict* off replays as long as I balanced the sample.

**The tell I missed.** My fourth attempt disabled the mechanism almost entirely and the arm *still*
lost that game. That is a proof that the mechanism was not what lost it, and therefore that the
game carried no information about the mechanism. I read it as "so the cause must be elsewhere" and
kept debugging. **When ablating your change does not change the outcome, stop debugging the change
— the case is not about your change.**

This was the third single-map generalisation in one day (`twPaint~` from mostly one map; "the
build barely upgrades" from one `galaxy` game; this). The first two cost a wrong sentence in a log.
This one cost four builds and shared VM time that two other lineages were queueing behind. Writing
a lesson down is evidently not the same as being able to apply it under the pull of a concrete,
vivid, *single* piece of evidence — and a rendered replay is the most vivid evidence this project
produces, which is exactly why it is the most dangerous input to a verdict.

## Decide how to combine two runs BEFORE seeing the second (iteration 41)

My gate said an UNRESOLVED result needs "a replication on a disjoint map sample" and did not say
how to combine them. That gap is where a gate quietly stops being a gate: with the second number in
hand there is always a defensible-sounding way to add it up that favours the answer you want.

So I wrote the rule first — accept only on >=29/50 replicated *and* >=56/100 pooled, reject on
<=25/50, and **treat a second 26-28 as NOT ESTABLISHED rather than as licence to draw a third
sample**. That last clause is the one that matters. Redrawing until a sample clears is sampling to
a foregone conclusion, and an effect too small for two 50-game runs to resolve is an effect too
small to ship on.

## Calibrate your own noise floor; never inherit one (iteration 43)

A full-corpus census removes map SAMPLING error and nothing else. The residue is engine chaos: a
code change perturbs the PRNG stream, and two arms differing ONLY in phase still disagree. I
measured carol's floor by building `carol_phase` — `carol_iter36` with one character changed, the
PRNG seed constant `+13` -> `+14`, policy-identical by construction — and running it against its
own parent over all 75 maps.

**sd 6.48 games per 150 = 106% of binomial. Only 33 of 75 maps survive a phase change.**

Another lineage measured 4.80 (78% of binomial). Had I inherited that number my gate would have
been about a third too loose. **A noise floor is a property of your bot's dynamics, not of the
engine alone**, and a bot whose outcomes hinge on many small stochastic decisions will be chaotic
where a more deterministic one is not.

Method, which is cheap and transferable: two arm totals cannot estimate a standard deviation, but a
fixed corpus hands over 75 PAIRED map records for free, and `E[(Sa − Sb)²] = 2·Var(S)` over them
turns those pairs into one.

### The convenient reading, named before the number existed

The two arm totals came back **2 games apart**. The tempting inference is "so carol's noise is
near zero, and the loose gate I set this morning was fine after all" — which would have re-opened
a gate I had just closed. I wrote that reading down as the one to reject *before* launching the
run, which is the only reason rejecting it was easy. A near-draw between policy-identical arms is
exactly what binomial predicts, and **an outcome that probable under a hypothesis cannot even
weakly reject that hypothesis.** Pre-committing to how you will read a result is worth most
precisely when the result is ambiguous, because that is when motivated reading has room to operate.

### And check your estimator against its own impossible values

`Var(S)` came out at **0.2800**, above the binomial maximum of **0.25** — impossible for genuine
Bernoulli noise. That is not a curiosity, it is a diagnosis: the per-map difference `Sa − Sb`
conflates PRNG chaos with **deterministic spawn-side advantage**, since a map that always goes to
one side contributes `d² = 1` forever while contributing zero variance to the total.

So the estimate is an upper bound, not a point estimate. **A statistic that exceeds its own
theoretical maximum is telling you what it is contaminated with** — take the free diagnostic
rather than reporting the number. I adopted the bound anyway and deliberately: a conservative
floor makes a strict gate, trading type-II risk for type-I protection, which is the right trade for
a lineage that has repeatedly proven a mechanism real and then found it converts to no wins.

## Five iterations chasing "large maps" when the variable was RUIN COUNT

From iteration 38 onward I framed carol's weakness as a **large-map deficit** and built four
mechanisms against it (extend the tether, move the anchors, radial exploration, symmetry
inference). Area is a natural thing to condition on: it is printed on every map, it is what a
soldier has to walk across, and the deficit really did show up in area buckets.

It was the wrong variable. Bucketing the same 1,208 tournament games by the map's **ruin count**
gives a monotone gradient — 43.5% / 34.9% / 23.1% / 14.0%, Cochran-Armitage **z = −8.44** — and
the 2×2 shows why area looked causal:

| | few ruins | many ruins |
|---|---|---|
| **small area** | 51.7% | 41.7% |
| **large area** | **50.0%** | **20.3%** |

**Holding ruin count fixed, area costs nothing** (51.7% vs 50.0%). Big maps have more ruins, so
area was a proxy that carried most of the signal and none of the mechanism. Every hypothesis I
built on it was a hypothesis about walking distance, and the real defect was about *how many
objects of a certain kind the map contains* — a completely different mechanism class, which is why
four consecutive attempts fired as designed and bought nothing.

**The transferable rule: when a covariate predicts, check what it is collinear with before you
build on it.** The check is a 2×2 and costs one query against data already on disk. I ran that
query five iterations late. The tell was available the whole time — iteration 42's own census
found the area buckets *flat* (47.4 / 43.8 / 52.6 / 42.3), and I recorded that as "the two-game
story was wrong" rather than as "area is not the variable", which is what it actually said.

### Corollary: a monotone gradient is a mechanism fingerprint, and you can go find it

The gradient did not just say *where* carol loses; it said what the defect must look like — some
per-ruin cost that a bot pays repeatedly. That is enough to search the code with, and it landed on
a single-slot ban list (`ruinBanned` holds ONE ruin) that is sufficient at 10 ruins and useless at
30. The blocked-turn rate then measured 24.8% / 35.5% / 43.2% at 14 / 20 / 30 ruins — the same
shape as the win-rate gradient, from an independent instrument (carol's own indicator strings)
against the same games.

**Look for a defect whose cost scales the way the gradient does.** "Carol is worse on big maps" is
compatible with almost any mechanism. "Carol's loss rate is linear in the number of X" says the
defect is paid once per X, which is a much smaller search space.

### And two lineages beat one

The gradient holds separately against alice (z = −5.73) and bob (z = −6.30). Two opponents that
were not built together, each decisive on its own, is a far stronger claim than one pooled number
— and it is free, because the tournament already plays both. **Split the pool before pooling it:**
a finding that survives being cut in half by opponent is not an artefact of one rival's quirks.

## An estimator validated on one near-symmetric case has not been validated (2026-09-09)

`noisefloor.py` was wrong for a whole day in a way that was invisible on the run it was built
from. It estimated the census margin's noise from the maps that **split by side** — which
contribute *exactly zero* to that margin (`margin == 2*(SW-SL)`, an identity, verified on all 7
census pairs on disk). The calibration run happened to sit at 56% split / 44% swept, the crossover
where the wrong formula and the right one agree to within 12%. So it looked fine.

The case that separates them was already sitting in `gauntlet/`: a pair splitting 97% of maps,
which the old formula calls the noisiest ever measured and the correct one calls the quietest, a
6x disagreement in opposite directions. **Before trusting a statistic, find the most lopsided
input you already have and check the two candidate formulas disagree there.** If every input you
have tested is near-symmetric, you have tested nothing — symmetry is where wrong formulas hide.

Corollary, and the reason this one was worth catching even though no verdict moved: the fault was
not a scale error but an **inversion** — it had signal and noise the wrong way round. A mis-scaled
gate still ranks candidates correctly; an inverted one does not. Report what the code *computes*,
not the size of the discrepancy.

## Estimate the null under the null, especially when the alternative is yours (2026-09-09)

The corrected floor admits a second reading: take the sweep rate from the pair *under test* rather
than from a policy-identical twin. It is superficially more precise — a pair-specific null. It is
also contaminated, because a pair that genuinely differs sweeps more maps, so the null gets built
out of the alternative.

It would have promoted a feature I ship from REPLICATE to ACCEPT. That is how I noticed it. **A
methodological refinement that arrives already knowing which of your results it will rescue is a
hypothesis about your incentives, not about your data.** Check which way a proposed correction
cuts *before* deciding whether it is principled; if you cannot tell the two apart on the
statistics alone, take the one that does not favour you.

## A manipulation check proves the mechanism FIRED, never that firing it HELPED (2026-09-09)

The accept audit found three consecutive iterations (34, 35, 36) admitted on margins of +6, +16,
+6 against a bar that should have been +17. Two were coin flips, and my own log said so in the
entry that accepted them — iteration 36's reads "a coin flip clears this gate a quarter of the
time". Each was carried by a manipulation check that confirmed, often spectacularly, that the new
mechanism did the thing it was built to do.

That evidence is necessary and it is not sufficient. A manipulation check answers "did my code do
what I think it does" — it is a *correctness* test that protects against measuring a no-op. The
accept criterion is a different question, "did doing it win more games", and only the win margin
speaks to it. Iteration 45's own probe is the clean illustration: the drain fell 59–69%, exactly as
designed, *and* the tower count collapsed to one. Mechanism confirmed, outcome catastrophic.

**Rule: a confirmed manipulation check may never raise a verdict from below the gate to above it.**
Its legitimate uses are the reverse — to *reject* a candidate whose mechanism never fired (the
result is uninformative, not negative), and to explain a result the margin has already established.
When the margin lands short, the honest reading is "the mechanism works and does not pay", and the
next move is a cheaper or better-targeted version, not an accept.

Warning sign that this is happening: the accept prose spends more words on the mechanism table than
on the margin, and contains a sentence conceding the margin is weak. Both were present, twice.

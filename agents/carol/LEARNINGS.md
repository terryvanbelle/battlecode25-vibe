# Carol — durable lessons (BC25), LIVE DIGEST

**This is the index. The evidence lives in `LEARNINGS_ARCHIVE.md`, which is GREP-ONLY** — never
read it whole. Every line below is greppable there by its quoted heading:
`grep -n -A25 "<heading>" LEARNINGS_ARCHIVE.md`. Nothing was deleted in the split.

Restructured 2026-09-09 from a 2,426-line file that was read in full at every cold start (~33k
tokens a time, for entries that were mostly settled). Add new lessons HERE as one line plus a
pointer, with the evidence in the log; promote to the archive when the entry grows past two lines.

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



---

## The five that have cost me the most (re-read these; the rest are reference)

1. **Replay inspection is for MECHANISM, never for VERDICT.** A one-map, one-side result is close
   to information-free — 44-56% of maps split by spawn side alone. Has now fired three times,
   most recently at iteration 57's stage 0. → *"Replay inspection is for MECHANISM"*, *"A one-map,
   one-side result is close to information-free"*
2. **Reachability has FOUR levels and I have been caught at each**: does the branch fire, is the
   choice set bigger than one, does the option set carry the signal, and is the gate inside the
   band the quantity actually occupies. → *"Reachability has FOUR levels"*, *"Verify a threshold
   against the operating band"*, *"Condition a reachability check on the guard the gate sits behind"*
3. **Cost the price, not just the benefit** — three times in three disguises, plus the
   second-order cost of a resource trade. Price a REALLOCATION against what it displaces. →
   *"Cost the price, not just the benefit"*, *"Price the SECOND-ORDER cost of a resource trade"*
4. **A lesson written is not a control.** Install the check where the mistake happens. Recorded
   three times as "the THIRD instance". → *"A doctrine applied only where it was learned is not a
   control"*, *"Writing the lesson is not fixing the bug"*
5. **My accept gate was blind for ten iterations and three entries had already said so.** A
   self-play gate cannot price a capability whose value only shows against another lineage. →
   *"My accept gate was blind for ten iterations"*, *"An aggregate gate cannot see a trade"*

## The budget question — ask it before pricing ANY throughput mechanism

**"What is the budget, and is it already spent?"** A rate limit is not slack when the budget
beneath it is fully spent. I made this error three times in one day (2026-09-09), each time with
a correct local measurement and a wrong referent:

| candidate | the "surplus" I saw | why it was not surplus |
|---|---|---|
| iter 56 pin-escape | treasury idle in a band on 77.2% of tower-turns | dwell-time, not slack; ~100% of chip income is spent |
| iter 57 `MONEY_MOD` | 3 towers at the 1000 paint cap, overflowing | the cap is per-tower; that tower's *build capacity* is load-bearing |
| build-fallback | builds on 0.9% of tower-turns vs a 7.04% gate — a "6.6x loss" | chips already fully spent; buys timing and mix, not volume |

Two of the three were killed before spending a game, by closing the accounting first. The control:
**decompose the budget and check the parts sum to income BEFORE reading any rate off it.** If spend
≈ income, the mechanism can only reallocate, and it must be priced against what it displaces — not
against zero. See TRAINING_LOG iterations 56–57. A resource at its cap is not free; ask where it
*is*, not how much of it there is.

## A re-open condition must be checked for FEASIBILITY when written, not when invoked

A closed direction's re-open condition is a rule, and rules get power-checked as rarely as
experiments do. C1b's condition ("must beat the unconditional version, not the baseline") is the
methodologically correct comparison AND unsatisfiable: the comparison it demands is a +6 difference
against sd 18.3 — **0.33 sd**, unresolvable at 300 games. On the page it looked identical to an
actionable condition.

**The check is one line: expected effect size of the comparison the condition demands, divided by
the sd of that comparison. Under ~2 sd, the condition is decorative** — it will send a future
session to spend games learning that nothing can be learned. Same shape as killing an experiment on
power, applied one level up: to the rule rather than to the run. See TRAINING_LOG, "C1b's re-open
condition, EVALUATED".

## A failing self-play census does not refute a cross-lineage claim, any more than a passing one confirms it

Doctrine 17 is usually quoted in one direction — a census cannot show a mechanism closes the
tournament gap. The converse is equally true and easier to forget when the number is bad: iteration
58's census rejected the mechanism as a *self-play improvement* (+14/150, +1.08 sd), and that is a
correct verdict about the referent it measured. It is **not** evidence about "carol converts ruins
worse than alice and bob", because both arms were carol. Match the instrument to the referent in
both directions, and do not let a reject you agree with quietly answer a question it never asked.

## Measurement and gates

- Gates were set against `se = 0`; the standing sampled gate is **>=34/50 accept, <=30/50 reject,
  31-33 unresolved**, sd(margin) = 8.59. State the UNIT of a gate. → *"My gates were set against"*
- Calibrate your own noise floor; never inherit one. Check an estimator against its impossible
  values. → *"Calibrate your own noise floor"*, *"An estimator validated on one near-symmetric case"*
- Swept counts and the win margin are the SAME number (`wins − N == SW − SL`). Two agreeing
  numbers are only evidence if independent — and independence of the DERIVATION is not
  independence of the REFERENT. → *"swept counts and the win margin are the same number"*,
  *"Independence of the DERIVATION"*
- Unresolved is not rejected — buy power instead. → *"SUPERSEDES the entry above"*
- A manipulation check proves the mechanism FIRED, never that firing it HELPED; and it must assert
  the DOSE. → *"A manipulation check proves the mechanism FIRED"*, *"must assert the DOSE"*
- Pre-register a MAP-LEVEL prediction, and pre-register the WEAK LINK rather than the gate. →
  *"Pre-register a MAP-LEVEL prediction"*, *"Pre-registering the weak link"*
- The zero arm is where the information is. A dose curve is evidence about the bot it was measured
  on. → *"The zero arm is where the information is"*, *"A dose curve is evidence about the bot"*
- A dose denominator must not be ENDOGENOUS to the treatment. → *"must not be ENDOGENOUS"*
- Decide how to combine two runs BEFORE seeing the second. → *"Decide how to combine two runs"*
- A statistic that never lands in a file is a recollection. → *"never lands in a file"*

## Instruments and tools

- **Run the discriminating case before naming a fault**: a mislabel and an inversion look identical
  in the output. `gateverdict.py` was INVERTING (counting the baseline's wins under the candidate's
  name and gating on it) and would have reported a −28 regression as ACCEPT. Fixed 2026-09-09; see
  TRAINING_LOG "TOOL BUG".
- Check the gate can SEE the effect before building the fix; register an instrument's MEASUREMENT
  CONDITIONS, not just its formula. → *"Check the gate can see the effect"*, *"Register an
  instrument's MEASUREMENT CONDITIONS"*
- A probe must be the SAME WIDTH as the shipping decision. A counter that reads zero and one that
  is ABSENT are different facts. → *"A probe must be the SAME WIDTH"*, *"A counter that reads zero"*
- A column whose NAME implies a normalisation it does not have — three times in one session. →
  *"a column whose NAME implied a normalisation"*, *"`p` in the replay dump counts painted TILES"*
- Check WHICH BUILD the tournament played. A measured constant is only valid for the build, and the
  subsystem, it was measured on. → *"Check WHICH BUILD"*, *"A measured constant is only valid"*

## Economy and the game's shape (carol-specific)

- **The two ceilings**: the tower mix decides which resource binds, and the realized unit mix is set
  by the ORDERING of affordability gates, not by the intended shares. → *"The two ceilings"*,
  *"The realized unit mix is set by the ORDERING"*
- **A resource that looks surplus is load-bearing**, and "it is at its cap" is not evidence it is
  free. Iteration 56 read treasury dwell-time as slack; iteration 57 read a per-tower paint cap as
  spare capacity. Both were wrong, same session. → TRAINING_LOG iterations 56–57
- Carol's units are TETHERED to towers by paint. Losing the last paint tower is an instant, silent,
  unrecoverable loss. → *"Carol's units are TETHERED"*, *"Losing the last paint tower"*
- Soldiers cannot contest ground; the late game is all splashers and no soldiers. → *"Soldiers
  cannot contest ground"*, *"The late game is all splashers"*
- Fixed constants rot into dead bands; a gate above where the treasury sits is an off switch. →
  *"Fixed constants rot into dead bands"*
- Two consumers of one budget must partition it by an explicit decision. → *"Two consumers of one budget"*
- The variable is RUIN COUNT, not map size — and map AREA was a confound I described wrong for nine
  iterations. → *"Five iterations chasing"*, *"Map area was a confound"*
- Carol's tower mass stops every archetype but not her own lineage. → *"Carol's tower mass"*

## Hypotheses and process

- Ask how the bot ALREADY solves the problem before adding a second mechanism. → *"Ask how the bot
  ALREADY solves"*
- The History pre-check must name the iteration that wrote the LINE. Write a closed direction's
  re-opening condition as a testable predicate. → *"The History pre-check must name"*, *"Write a
  closed direction's re-opening condition"*
- Price the features you already carry — a rejected candidate is a free ablation. → *"Price the
  features you already carry"*
- "More X doesn't help" does not license "less X is free". → *"More X doesn't help"*
- "Realized != intended" says one of them is wrong; I assumed four times it was the realized one. →
  *"Realized != intended"*
- Separate the MECHANISM from the POLICY wrapped around it when rejecting. → *"separate the
  MECHANISM from the POLICY"*
- Copying a rival's observable RATIO is not a strategy. → *"Copying a rival's observable RATIO"*
- A DEFERRED iteration needs a written re-entry condition. → *"A DEFERRED iteration"*
- Ask what the run already in flight answers before queueing another. → *"Ask what the run already"*
- Reproduce one WIN before reading a loss sample as a mechanism; size an opportunity with the wins
  too. → *"Reproduce one WIN"*, *"Sizing an opportunity needs the wins"*
- A guard belongs on the branch that STARTS work; a state's EXIT PATH must not sit inside a guard
  the state closes. → *"A guard belongs on the branch"*, *"A state's own EXIT PATH"*
- A variable's blast radius is where its VALUE ENDS UP. `canAttack` is legality, not efficacy. →
  *"A variable's blast radius"*, *"`canAttack` is a legality check"*
- A UNIT'S LEGAL ACTION SET, not its cost, decides what an architecture can do. A soldier paints
  only EMPTY or own-team tiles, so its conversion rate against contested ground is exactly zero:
  soldier-primary can take ground and structurally cannot recapture it. Measured iteration 59,
  Leaf: coverage 611 at r500 decaying to 400, with **paint acts = 0** at r1500 while towers held
  4,039 paint and $9,340 chips sat idle. Nothing was scarce; the army was disqualified. So a unit
  mix must be a function of MAP STATE, not of the treasury. → TRAINING_LOG, *"Correction 3 (D1c)"*
- A THRESHOLD BAND on a quantity the treatment itself consumes is fed by the treatment — doctrine
  10 one level down, and I wrote doctrine 10 and still shipped it. Gating moppers on tower paint in
  [100,200) looked like "spend an idle stash"; with 25 towers spawning continuously it is just the
  band every paint tower's stash passes through on each refill cycle, so it took +113 builds per
  250 rounds against soldiers' +35. The fix names the state instead of a band: a MONEY tower has
  `paintPerTurn == 0` [E], so its stash really is finite and idle. → TRAINING_LOG, *"Correction 1 (D1b)"*
- CHECK A PRE-REGISTERED BAND FOR FEASIBILITY WHEN YOU WRITE IT — the C1b lesson applies to
  manipulation checks, not just to re-open conditions. I registered "HOME must be 5-25% of splasher
  turns" and measured 58.8%/63.8%; the band was unreachable at ANY dose, because a splasher carries
  6 splashes, acts once per 5 turns (30 working turns) and needs 20-40 moves for a round trip, so
  travel is inherently 40-60% of the duty cycle. One line of arithmetic, not done. Worse, the band
  could not DISCRIMINATE (doctrine 15): 64% HOME is predicted equally by "logistics uselessly took
  over" and "logistics work and the trip is long". → TRAINING_LOG, *"The overshoot band was infeasible"*
- A PER-UNIT RATE IS BLIND TO A POPULATION EFFECT. I registered D3 as "each stranded splasher fires
  more often"; the fire rate was FLAT (23.7% -> 22.6%/25.2%) while standing splashers went 4 -> 22-32
  and towers 7 -> 17-22. The mechanism was survival, not throughput. When a treatment can change how
  many units exist, register ABSOLUTE counts alongside every share. → TRAINING_LOG, *"So the mechanism is NOT the one I registered"*
- YOUR STAGE-0 PROBE MAP IS AN INSTRUMENT — CHECK WHERE IT SITS IN THE CORPUS. Every stage 0 in
  this lineage used **Leaf**, which is 3,600 area (the MAXIMUM, 89th pct) with **52 ruins — 99th
  pct, the only map in 75 with >=52**, against corpus medians of 1,500 and 17. Iteration 60's census
  put +24 of its +26 margin on ruin-dense maps, so Leaf is the corpus BEST CASE by construction for
  every economy/flywheel mechanism here. It over-stated three in one session: carol_r1 won Leaf then
  lost 38/150; iteration 60's doses looked decisive and the census landed exactly on the bar;
  iteration 61's doses looked decisive and the 25-map screen was flat. Stage 0 now runs on
  **Mirage** (1,600 / 18, closest to the joint median); Leaf only as a labelled best-case probe.
  → TRAINING_LOG, *"LEAF IS THE CORPUS OUTLIER"*
- A MECHANISM STATISTIC THAT MOVES WITHOUT THE OUTCOME MOVING IS A CORRELATE, NOT THE CHANNEL.
  `noPaint` went 0.0% -> 49.0% across the REFILL_LOW ladder — worse than the pre-D3 41.2% — and the
  25-map outcome did not move at all (+0/-4/+2). It was iteration 60's headline stage-0 clause.
  Test a mechanism claim by DOSING the statistic and watching the gate, not by showing the statistic
  moved. → TRAINING_LOG, *"the mechanism statistic is not the causal channel"*
- A MEDIAN PROBE MAP IS UNBIASED, NOT PRECISE — one game is n=1 whichever map it is. Iteration 61
  moved stage 0 off outlier Leaf to median Mirage; iteration 64 then passed ALL THREE registered
  clauses on Mirage (coverage 296->705, splashers built 26->54 breaking a two-iteration invariant,
  standing splashers 0->17, starved 309->20) and the 25-map screen measured NOTHING (28/50, closed).
  The failure was never Leaf specifically, it was treating one game as predictive of a population.
  **Stage 0 answers "does the mechanism FIRE", never "does firing PAY".** → TRAINING_LOG,
  *"it sharpens iteration 61 rather than repeating it"*
- BEFORE DOSING A TRIGGER, CHECK IT FIRES ON A MAJORITY OF THE CORPUS — free, from replays. The
  iteration-64 phase switch keyed on `getNumberTowers()`, which carol rarely reaches: arms
  TOWER_TARGET 6 and 8 played games identical in winner AND round count on **72% of 50**, so the
  upper ladder was one measurement wearing three labels. A dormant trigger makes a dose ladder
  unable to resolve anything, and doctrine 3's identity count is what exposes it.
  → TRAINING_LOG, *"Doctrine 3's identity count, on the screen"*
- AN UNREGISTERED SUBGROUP MAY KILL A HYPOTHESIS, NEVER RESCUE ONE. Dormancy invited the rescue
  "measure it where it can act"; the ruin-density split came back +2 dense / +4 sparse — flat where
  the mechanism fires — so it closed the direction. Run such a split, and let it point only one way.
  → TRAINING_LOG, *"The dilution excuse, tested and REFUSED"*
- A VERDICT DOES NOT TRANSFER, BUT ITS ARITHMETIC OFTEN DOES — and the ratio that decides it is
  usually nameable. bob CLOSED "keep units alive by feeding them" at -6 wins BOTH doses
  (agents/bob/CLOSED.md #23); I ACCEPTED the same mechanism as iteration 60 at +26/150 and it
  validated on three external instruments. Reconciled: benefit scales with **attackCost/capacity** —
  soldier 5/200 = 2.5% (acts at almost any stash), splasher 50/300 = 16.7% (completely inert below
  50). Same mechanism, same cost, benefit 6.7x larger on my architecture. When a foreign verdict
  disagrees with yours, find the ratio that differs before believing either. → TRAINING_LOG,
  *"bob CLOSED the mechanism I just accepted"*
- DE-CLUMPING AND TARGET-SEEKING CONFLICT FOR AN AoE UNIT. Crowd -89..-100% bought +7% splash score
  and cost **-17..-28% firing rate**, net -11..-22% (iteration 65, killed for 4 games). A soldier
  paints the tile it stands on, so moving it is cheap; a splasher must be within r²<=4 of a dense
  target cluster, and dense clusters are where other splashers also want to be. bob measured the
  same payer at -6.0% paint actions; on an AoE architecture it is 3-5x larger.
  → TRAINING_LOG, *"Iteration 65 -- KILLED AT STAGE 0"*
- MY OWN DECISION PROXIES ARE VALID MANIPULATION CHECKS AND WORTHLESS AS EVIDENCE OF VALUE. Twice
  now a quantity the bot computes to make its OWN decisions moved enormously while the outcome did
  not follow: iter61 `noPaint` 0.0%->49.0% with a flat screen (+0/-4/+2); iter66 splash score +52%
  on the bot's own "total value" with the screen at -8/-4. Such quantities are chosen for being
  cheap in bytecode, not for correlating with winning, and they are free and pre-instrumented, which
  is exactly why I keep reaching for them. Use them to prove the knob MOVED; never to argue the
  movement was worth having. → TRAINING_LOG, *"The pattern this makes"*
- PRICE A MECHANISM AGAINST THE ALTERNATIVE THAT ACTUALLY EXISTS. I killed low-score splashes as
  "14 paint/tile, 3x worse than a soldier's 5" — but this build fields THREE soldiers a game and a
  soldier cannot paint an enemy tile at all [E]. No soldier was ever going to do it cheaper; the
  real alternative was NO conversion, worth zero, against which 14 paint/tile is worth taking. A
  correct number against a counterfactual that does not exist (doctrine 5, wrong referent).
  → TRAINING_LOG, *"Wrong referent (doctrine 5)"*
- A CONDITIONAL PROBABILITY MEASURED UNDER YOUR CURRENT POLICY IS NOT A FACT ABOUT THE GAME.
  I measured, correctly and on two disjoint maps, that enemy-converted tiles are lost 2.7-6.4x more
  often than empty-converted ones — then built a policy on it and lost -22/-14/-46 out of 50. They
  are lost more often BECAUSE they sit where the enemy is active; stop contesting that ground and
  the enemy keeps it and expands, so the front moves and the estimate collapses. Retention was an
  equilibrium of both policies, not a property of a tile's origin. Before acting on a measured
  conditional, ask whether the action moves the conditioning event. → TRAINING_LOG, *"Error 2 -- the deeper one"*
- NAMING SOMETHING "UNPRICED" AND THEN DOSING IT TO ZERO IS ASSUMING, NOT BRACKETING. I wrote that
  enemy conversion "carries unpriced defensive value" and shipped an arm (W_ENEMY=0) that set it to
  nothing; that arm was PAINTED OUT at round 474 and scored 2/50. >70% of paintable squares is an
  instant win for EITHER side, so enemy conversion is the only brake on the opponent's win
  condition. If a term is unpriced, the dose that zeroes it is the one you must justify hardest.
  → TRAINING_LOG, *"Error 1"*
- "MY INSTRUMENT IS BLIND" IS A HYPOTHESIS, NOT AN EXPLANATION. I argued carefully that iteration
  64's self-play null was instrument-limited (five counters moved hard; doctrine 17; bob's #15 had
  four nulls with the same diagnosis), built a cross-architecture opponent to prove it — and the
  instrument REFUTED it. Self-play said +6/50, bobf said -2/150; they agree. The excuse is seductive
  precisely because it explains a disappointing result without the mechanism being wrong. Build the
  instrument doctrine 17 implies and let it rule EITHER way. → TRAINING_LOG, *"I was wrong, and I am recording the shape"*
- CALIBRATE A NEW INSTRUMENT BEFORE REGISTERING A BAR AGAINST IT — agreement is not resolution.
  bobf reproduced the tournament EXACTLY in every bucket, and I then registered a >=+8 gate without
  knowing what 8 was worth. Measured after: sd 4.18 per 150 games, so +8 was 1.9 sd (adequate, by
  luck). The same measurement corrected an overclaim of mine within the hour: a -4 bucket delta I
  had called a "refutation" is 1.46 sd, i.e. nothing. One placebo run, the same method that gave
  sd 6.48 on my own gate. → TRAINING_LOG, *"bobf's NOISE FLOOR"*
- CROSS-ARCHITECTURE GAMES ARE FAR MORE CHAOS-SENSITIVE THAN SELF-PLAY. Only **2%** of bobf games
  survive a PRNG-seed change, against **44%** in my self-play placebo. Two different designs meet in
  far more contingent positions than two builds of one design, so an external instrument needs MORE
  games to resolve the same effect, not fewer — despite feeling like the better instrument.
- TWO QUANTITIES SCALING TOGETHER IS NOT A MECHANISM. Splasher HOME share scales with map area
  (35.5% at 1,600 -> 58.8% at 3,600) exactly as my largest deficit does, I had a smoking-gun trace
  and a real defect in my own accepted code — and bounding it left the share FLAT and RISING at the
  tightest dose, because bounding a trip does not create the resource the trip fetches. HOME is a
  symptom of tower paint scarcity, not a travel cost. Co-scaling is the cheapest coincidence in a
  system with one binding constraint; the test that separates symptom from cause cost 3 games.
  → TRAINING_LOG, *"Iteration 70 -- KILLED AT STAGE 0"*
- A LOW COST CAN BE A SYMPTOM OF PASSIVITY, NOT EFFICIENCY. Measured across two large maps: carol's
  units stand on their OWN paint 58.5-89.7% of the time and pay 0.21-0.82 paint/unit-round of drain;
  alice stands on CAROL's paint 85-88% of the time, pays 1.71-1.77, and wins both. bob's #26 recorded
  the same relationship from his side (alice 0.360 vs bob 0.192, 88% more, wins 60-40). Carol's drain
  is the LOWEST of three bots measured and carol is losing — standing on enemy paint is the price of
  being in enemy territory. Before optimising a cost DOWN, check which side of it the winner is on.
  → TRAINING_LOG, *"Where units stand"*
- A BOUNDARY DRAWN TO SUMMARISE RESULTS IS NOT A NATURAL KIND. I nearly built an area-gated mechanism
  keyed on 1,600 tiles — a bucket edge I invented for a report table. Priced at +7 against a +9 bar
  and declined on arithmetic; the better objection is that a mechanism keyed to your own presentation
  is fitted to it. → TRAINING_LOG, *"PRICED AND DECLINED"*
- DOCTRINE 7 GOVERNS THE MECHANISM CHECK, NOT ONLY THE GATE. I checked that my GATE opponent posed
  the threat before building iteration 71 and wrote it up proudly — then ran the stage-0 manipulation
  check against carol_iter44, which mops 17 times a game against bobf's 828. Stage 0 reported total
  paint actions **+16%**; against an opponent that actually applies the pressure the same metric is
  **-33%**. A manipulation check measures the mechanism in the regime you run it in: against an
  opponent that never creates the conditions the mechanism trades against, it reports the benefit
  without the cost. Stage 0 is what licenses the build, so it needs the check MORE than the gate does.
  → TRAINING_LOG, *"The lesson, and it is one level up"*
- A FOREIGN RE-OPEN CONDITION CAN BE RIGHT WHILE YOUR TEST OF IT IS WRONG. bob's #17 asks for a
  mechanism raising mopper share "without reducing total paint actions". I measured that clause as
  MET and built on it; measured properly it fails, and the iteration died at -3.83 sd — the largest
  negative this lineage has recorded. His closure transferred and his condition was well specified;
  only my measurement of it was not. When you take a foreign closure as "the prior to beat", the
  clause you test is only as good as the regime you test it in.
- I HAVE NOW ARGUED "MY SELF-PLAY GATE IS BLIND" TWICE AND BEEN REFUTED BOTH TIMES. Iteration 68:
  self-play +6/50, bobf -2/150 — they agreed. Iteration 71: self-play +4/50, bobf **-16/150** — the
  self-play gate was OPTIMISTIC, not blind, and understated the harm in the safe direction. Both
  times I had a quantitative argument (a 100x threat-exposure ratio the second time). The story
  explains a disappointing number without requiring the mechanism to be wrong, which is why it keeps
  appealing. Run the external instrument as the TEST of the claim, never as a way around the screen.
- **DEFAULT GATE RULE (adopted 2026-09-10):** if a mechanism's cost is paid against an OPPONENT'S
  BEHAVIOUR rather than against the map, `bobf` is the default opponent for BOTH the stage-0
  mechanism check and the gate. The external instrument has now caught two things the self-play gate
  would have passed (iteration 68 agreed with it; iteration 71 it passed at +4 while bobf said -16).
  Self-play remains the right instrument for map-coupled mechanisms and for dose selection among my
  own arms. → progress/milestones.txt
- A FULLY VALIDATED CAUSAL CHAIN CAN MOVE AT EVERY LINK AND THE OUTCOME STILL NOT FOLLOW, BECAUSE
  THE CHAIN IS REGIME-LIMITED. Iteration 76 moved coverage 37%->65%, ruins marked 9->13, towers
  10->14, tower paint 1,024->1,666 and painted area 459->700 per-mille — winning that game 700 to
  219 — and the 25-map screen returned +0/-10/-4. These are outcome-side quantities, not decision
  proxies, so this is stronger than the iter61/iter66 failures. The decomposition explains it: all
  three arms are POSITIVE on large maps and negative on small/mid, because on a small map coverage
  is not scarce. **Validate a chain end-to-end on the CORPUS, not on the map where it works** — and
  when you price a chain, price the regime share too. → TRAINING_LOG, *"the chain is real but REGIME-LIMITED"*
- PRICING A CHAIN END-TO-END CAN DISCOUNT A DIFFERENT ITERATION THAT SHARES IT. Iteration 75's
  symmetry sizing (+61%) runs through this same coverage chain; measuring the chain end-to-end
  showed it converts only on large maps, so that +61% is a large-map figure and the two unbuilt
  memory links would buy the minority regime. A chain measured for one candidate re-prices every
  candidate that shares it — check what else you sized through it.
- A COST METRIC ON WHICH I LEAD THE FIELD IS NOT A DEFECT — THIRD INSTANCE, NOW A STANDING CHECK.
  paint drain 0.21-0.82 vs the winner's 1.71-1.77; tower attacks 859 vs bobf's 1,265 on the map I
  lose worst; soldiers 1-11 vs 12-39 (and measured optimal). All three looked like waste, none was.
  **Before pricing any cost as a defect, measure the winner's value of it FIRST** — it is one dump
  and it has killed three candidates for zero games. → TRAINING_LOG, *"THIRD time I have been at the efficient end"*
- CLAIM A TOURNAMENT SWING ONLY WHEN THE OPPONENT IS FIXED, AND APPLY IT BOTH WAYS. carol went
  +2.3 in standings and +7 head-to-head against alice while carol's HEAD was BYTE-IDENTICAL and
  alice had accepted a change — so none of it was mine. The previous tournament was the mirror image
  (alice fixed, my +9 was mine) and I claimed it. The discipline only means something if it also
  makes you give back the favourable one. → TRAINING_LOG, *"The tournament moved my way and it is NOT mine"*
- YOUR QUALITATIVE INSTRUMENT NEEDS A SAMPLING RULE TOO. My screens and censuses sampled the corpus
  correctly for 16 iterations; every REPLAY I ever opened was Gears or galaxy — both large. So every
  mechanism targeted "cannot acquire", because that is the failure mode of the only games I had read.
  The mid band is 64 of 150 games and I had never opened one; its failure mode is the INVERSE (carol
  leads by 200+ per-mille at r1400 and collapses). **Sample the regime you trace, not just the regime
  you score.** → TRAINING_LOG, *"Every trace I have run in this project was on Gears or galaxy"*
- A CORPUS-POOLED CLOSURE DOES NOT SETTLE A REGIME-SPECIFIC QUESTION, and re-opening on that ground
  is legitimate rather than motivated. It is the same shape as an aggregate gate hiding a -6/+20
  trade: a pooled null can conceal a regime where the effect is real and opposite. Write the re-open
  as "the closure's basis does not cover the question I am now asking" — that stands on its own and
  is a different act from re-opening because you like the hypothesis.

## Housekeeping

- The git INDEX is shared between all three agents; use `carol-tools/commit.sh` (or
  `tools/agent-commit.sh`). → *"The git INDEX is shared"*
- Superseding in place must LOOK superseded. → *"Superseding in place must LOOK superseded"*
- The frozen roster un-saturates itself. → *"The frozen roster un-saturates itself"*
- Reading a running gauntlet is free information. → *"Reading a running gauntlet"*
- A cache keyed on a MUTABLE path serves stale answers silently. → *"A cache keyed on a MUTABLE path"*

- **A regime gate is worth minus the side you switch OFF, never the side you keep.** I priced the
  i69 area gate at +7 by counting its good (small-map) side. But the ungated bot already has that
  side; the gate's only product is the loss it avoids on the other side — and i69's other side was
  neutral, so the gate was worth zero. Price a gate as (null action) - (what the disabled regime
  was costing you). Same null-action error as pricing against zero instead of against no-op, in a
  new hiding place.
- **A boundary chosen to maximise separation will always find one — permutation-test the choice,
  not just the split.** Shuffle the covariate labels across units and re-run the whole max-over-
  thresholds search; the p-value must be for the search, not for the winning cut.
- **Two mechanisms can share a ceiling *and* be anti-aligned in regime.** i69 helps on small maps
  and is neutral on large; i76 hurts on small and helps on large. A single "regime gate" for both
  is incoherent. When a correlation between candidates is negative, look for the covariate that
  signs it before concluding they merely compete for one resource.
- **An oracle can survive the data and still die.** The i76 +12 was not a fantasy — re-derived at a
  data-chosen boundary it measures ~+11. It closes because +11 is 42% of the bar, not because it
  was unbuildable. "Confirmed" and "sufficient" are different verdicts; report both.

- **Normalise whole-game totals by game length BEFORE reading a dose ladder.** My iteration-69 build
  table sat in the log for two sessions as raw per-game counts; the arms' games ran 657-991 rounds,
  and normalising inverted which arm looked most productive. Recover the round count from the replay
  (`T r=`) rather than trusting a total.
- **A one-knob ladder cannot attribute value between two quantities the knob moves together.**
  `SPLASHER_EVERY` raises splasher rate and cuts soldier rate monotonically and in lockstep; no
  contrast in that design separates "more splashers" from "fewer soldiers". I drafted the attribution
  and withdrew it. To separate collinear arms you need a knob that moves one and not the other.
- **Extrapolate a headroom at the MARGINAL rate, not the average.** Returns inside my production
  ladder fell 8x from the first step to the last (0.82 -> 0.10 margin per unit). Averaging over the
  whole ladder inflated the remaining headroom's value 3x. When you extrapolate from the top of a
  measured range, the last step is the estimator.
- **A pooled budget is not a per-agent budget.** My splasher ceiling divided *pooled* paint income by
  300, but the engine requires one tower to pay 300 from its own stock. Pooled income says the rate
  is affordable; the replays say a single tower holds 300 paint in only 27-54% of rounds. Check
  whether the resource your ceiling divides is actually fungible across the payers.
- **"Unreachable" and "not worth reaching" are different closures, and the second is stronger.**
  Premise 3's production half is refuted on value: even granting the full 3.5x, it extrapolates to
  12-35% of the accept bar. Prefer to close a premise on value when the data allows it, because an
  unreachability closure invites a better implementation and a value closure does not.

- **A backwards completion argument still has to measure its hinge.** "Production is worthless, so
  the pair that needs production cannot work" is valid only if the production measurement transfers
  across the posture change — and it was taken under the posture the pair replaces. That is the
  iteration-67 error wearing a different hat. I closed the premise by measuring the coupling (the
  posture change relieves the binding resource by 1.09x against a required 2.02x), not by running
  the logic backwards alone.
- **When the measured gap is an order of magnitude, a weak estimate is good enough.** The r2 relief
  figure comes from one game with three coupled changes — normally too weak to close anything. It
  closes this, because it would have to be wrong by 10x in the favourable direction to matter.
  Match the precision you demand to the size of the gap you are testing.
- **Paired halves can each relieve the resource the other exhausts.** Dropping the tether freed tower
  paint (71.5% -> 78.2%) while splasher-first spending drove chips down (38.3% -> 10.3%), so joint
  affordability of the 400-chips-AND-300-paint build fell 21.1% -> 0.2%. Before pairing two
  mechanisms, check the JOINT condition they must satisfy together, not each one's own resource.

- **A winner-side check is only as good as the winner.** "The bot beating me is on the other side of
  this metric, so it is not my defect" killed three of my candidates for zero games. It was my most
  productive instrument of the session and its authority was always conditional on the reference
  being a good bot. When the reference turns out to lose 75-100% of its own games to an external
  standard, every closure of that form re-opens — by the change of objective, not by preference.
  Two of my three survived because they had an independent absolute closure underneath; record which
  closures have one, because that is what decides whether a comparative kill survives a re-framing.
- **A regime decomposition of a head-to-head margin is a fact about the matchup, not about you.**
  "The deficit is 100% large-map" organised several iterations of targeting. It says where I lose to
  one specific co-evolved rival, and says nothing about where I am absolutely weak.
- **Self-play dose ladders are mirror optima.** They tune against an opponent carrying my own
  weaknesses, which should overstate mechanisms exploiting my architecture's failings and understate
  those that only matter against dissimilar opponents. That is the shape of a joint local optimum.
  Declare it as a caveat; the remedy is cross-architecture rungs, not a re-run.
- **Re-examining a closure can move the sign AWAY from the candidate.** Re-opening the tower-attack
  gate cost the "for gating" argument its authority (it was rival-specific) while the "against
  gating" arithmetic survived. A re-examination is not a licence to revive; report it when it points
  the other way.

- **Validate the measurement instrument BEFORE spending the games it is meant to read.** My
  registered stage 0 cost zero because checking that the attack counter reproduced my recorded
  numbers showed the recorded numbers were wrong by 2.3-21x. The instrument check is not overhead
  before an experiment; it is sometimes the experiment.
- **A recorded number with no method attached is its own error class.** Inverted referent, wrong
  referent and un-normalised total are all reasoning errors over real measurements. This was a figure
  that entered the log, survived into a closure map, and justified a registered iteration, with no
  reproducible derivation anywhere. When quoting a number from your own record to justify a build,
  check that something can still produce it.
- **When two of your own numbers disagree, run the checks that could indict the INSTRUMENT before
  concluding the record is wrong** — and say which you checked. Complete round coverage in the replay
  and no reassignment of the state string were what licensed "my record is the fault, not the tool".
- **A test can be structurally incapable of answering its question.** I checked whether attacking
  turns also showed 'nothing paintable' and got a clean 0 of 606 — which proved nothing, because the
  attack path breaks before that flag is appended. A 100%-clean result from a test that cannot
  produce the other answer is not evidence; report it as inconclusive.

- **Re-frame a finding, then re-measure it before trusting the re-frame.** I argued that "the deficit
  is 100% large-map" was an artefact of one co-evolved matchup. Rebuilt on four frozen
  cross-architecture rungs, the regime effect reproduced on all four — so the re-framing was wrong
  and the finding was carol's own. A re-framing is a hypothesis too.
- **"Where am I least dominant" and "where do I lose" are different questions, and an instrument
  answers only one.** carol beats every roster rung in every bucket (lowest cell 51.6%), so the
  roster locates a gradient and can never locate a failure. The instrument that knows the failures
  reports counts without identities. Say which question your instrument can answer before reading an
  answer off it.
- **A gate's variable can be under-determined by the corpus that motivated it.** Ruin count predicts
  my results at least as well as map area, ruin density not at all, and a 2x2 control leaves both
  standing at similar magnitude on n=26-30 cells. The area boundary I re-derived would select nearly
  the same maps as a ruin boundary. Record which variable a gate would have to READ, separately from
  the magnitude it would deliver.

- **A failed instrument means UNTESTED, not REJECTED — and it is more expensive than a failed arm.**
  `carol_decap` read 97.5% and would naturally have been filed as "tower siege does not threaten
  carol". It was a statement about the instrument: decap attacked towers with soldiers, which the
  engine makes nearly impossible. A failed opponent closes a whole line of questioning rather than
  one lever. Re-read every saturated rung as a question about the rung.
- **Coupling is a defect in an arm and a virtue in an opponent.** An experimental arm needs one
  change so the result can be attributed; a stress opponent needs difficulty and no attribution at
  all. Fork your strongest bot and couple freely when building a rung -- a weak hand-built archetype
  cannot beat you, which is exactly how the previous one failed.
- **Build a stress opponent against a degeneracy measured in your own trace**, never against a guess
  at what some other bot does. The target here was carol's own recorded absorbing state -- production
  frozen for 1,887 / 1,881 / 44 consecutive rounds once the last money tower dies.
- **A rung that beats you localises the capability it was built to stress and nothing else.** Its win
  rate is not a general strength reading. Keep it a diagnostic; do not let it become a benchmark.

- **Sweep a new detector across every replay you already hold before trusting a null of n=3.** Mine
  held at n=117 (median 1 round) -- but the same sweep showed the signature in only 17% of the games
  it was supposed to explain, and in winners too. A prevalence baseline costs zero games and can
  pre-empt the whole causal design.
- **A confirmed mechanism can be an irrelevant one.** The absorbing state was exactly as recorded --
  treasury pinned near zero for up to 1,602 rounds while towers stood with paint at capacity -- and
  it still was not what decided the matchup. "The mechanism is real" and "the mechanism explains this
  result" are separate claims needing separate evidence.
- **Both teams live in the same replay, so a retained loss also retains a controlled winner.** Map,
  terrain and round count are held constant by construction. That turned a loss-biased corpus into a
  within-game comparison (carol peak 4.7 towers losing 39%, the archetype 7.5 losing 2%) with no
  confound at all -- far stronger than comparing against healthy games on other maps.
- **When the registered alternative fires, change the measured quantity, not the design.** The
  matched-pair set was built for the freeze; the freeze is not the mechanism; the pairs are still the
  right control, now applied to tower trajectory instead.

- **A matched-pair control can change WHICH half of a decomposition to aim at, not just its
  confidence.** Measured on my loss corpus alone, acquisition and retention priced at 1.22:1 --
  "comparable, choose on cost". Measured on matched pairs they price at 2.3:1. The uncontrolled
  version used the OPPONENT's peak as the acquisition target (a different bot); the pair uses my own
  peak on the winning side of the same map, which is a target I demonstrably reach. Pick the
  counterfactual target your own bot has been observed to achieve.
- **Verify determinism with a two-part fingerprint before trusting a re-run as a matched pair.**
  Winner alone is weak -- same winner with a different round count is a different game. All 36 of
  mine reproduced on winner AND round count AND result, which is what licensed the pairing.
- **Check WHEN a loss happens before pricing it as a cause.** My structure losses cluster at a median
  72% through the game, so part of the retention gap is the losing process rather than its cause --
  which makes the acquisition share an understatement, and that direction is worth declaring.
- **A weak rung is not a useless rung.** At 88% and 94% they adjudicate nothing close, but they
  extend the ladder's range and are what registers a LARGE regression first. Say what a rung is for
  when you add it.

- **A decomposition can invert between regimes, and the regime that carries the margin is the one
  that counts.** My matched pairs said acquisition beats retention 2.3:1; the both-sides losses --
  which ARE the entire margin -- say retention beats acquisition 2.4:1. Near mirror images. Two
  proximate mechanisms in two regimes, not two rival explanations of one. Check the decomposition
  separately in the subset that carries the margin before choosing what to build.
- **Register a magnitude check alongside a presence check; the presence answer may be right and
  uninformative.** "Does the gap appear?" answered PRESENT exactly as predicted. The magnitude check
  I registered as a selection control fired NEITHER of its two branches -- the gap was smaller, not
  larger or similar -- and that anomaly was the actual finding.
- **A design that varies only X can never identify X's own effect.** My matched pairs varied only the
  side, so they could see mechanisms downstream of the side and were structurally blind to the side
  itself. The set I had discarded for carrying no margin information was the only one that could
  break that confound.
- **Two sets can support different contrasts, and must not be reported as one.** Win-half versus
  loss-half is a different comparison from carol versus opponent; the both-sides losses cannot supply
  the first at all. Compare like for like across sets before claiming a pattern holds.

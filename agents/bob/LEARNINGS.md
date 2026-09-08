# Bob — LEARNINGS.md

Durable lessons, organised by theme. The chronological record is `TRAINING_LOG.md`;
this file is what I would want to read first if I lost all context. Every entry
names the measurement that produced it, because a lesson without one is a belief.

---

## 1. Instruments

**Dump raw per-round counters before theorising.** The single highest-value thing
I built was `bob-tools/dump-replay.sh` + `BobDump.java`, and the highest-value way
to read it was for *absolute degeneracy*, not opponent-relative deficit. "327,000
chips unspent at round 2000" and "coverage peaks at round 150 and then declines"
need no opponent to be obviously wrong, and both had been sitting in every replay
since iteration 0 while I reasoned about matchups. Iterations 3, 5 and 7 all came
out of counter dumps; iteration 2, which came out of reasoning, was rejected.

**The instrument can share a cause with the disease.** Iteration 3 scored 87.5%
partly *because* `towerTypeFor` was broken: on an all-money map, upgrading the one
starting paint tower is nearly the only paint lever there is. A metric measured on
a defective bot measures the defect too. When an accept looks unusually large, ask
what else in the bot had to be wrong for it to be that large.

**Read a counter you did not think to print.** Extending the dumper to report
tower types built — a column I added almost as an afterthought — immediately
exposed the root cause of two separate multi-iteration threads. Cheap instruments
beat clever hypotheses.

**Verify enum/index mappings by running them, never by reading the order.** I
confirmed `PAINT_TOWER=1, MONEY_TOWER=2` by printing `RobotType.names` before
building an argument on top of it. The whole root-cause finding would have been
backwards if that mapping were wrong.

## 2. Engine ground truth beats inference

Every substantive win this session came from `javap -c` on the engine jar, not
from the spec prose:

- `assertCanUpgradeTower` requires only r²≤2 + ally tower + level + chips. **No
  action consumed, no cooldown added** — so a tower can upgrade *itself*, for
  free, on any turn, alongside attacking and spawning. That is iteration 3.
- `InternalRobot.<init>` sets `paintAmount = 0`: a newly completed tower has **no
  paint**, and a money tower (`paintPerTurn == 0`) can therefore never accumulate
  the 200 paint a soldier costs. Money towers are permanently sterile spawn points.
- `processBeginningOfRound` adds `extraResourcesFromPatterns(team)` to **paint**
  towers as well as money towers, and it equals `3 × numResourcePatterns`. So an
  SRP is +3 paint/turn on *every* allied paint tower — the spec's phrase "mining
  towers" hides this completely.
- The tower type must be a pure function of the ruin: `workOnRuin` marks the 5×5
  and then refuses to re-mark, so a type that can change between marking and
  completion produces a ruin no later soldier can ever finish.

## 3. Symmetry and fixed-order decisions (the recurring bug class)

**`((ruin.x + ruin.y) & 1)` does not mix anything.** Ruin centres are ≥5 apart on
regular lattices, so on a given map they nearly all share one parity of `x+y`.
Measured: gridworld 0 paint/9 money, starburst 4/0, Snowglobe 4/0, Thirds 1/0 — a
per-map coin flip landing on 100% of one type. Simulated offline, the rule returns
**100% one type on every even ruin spacing** and 50% on odd, because `(x+y)&1` is
invariant along an even-stepped lattice.

The general lesson is stronger than the fix: **a coordinate expression is not a
mixing function.** Any rule of the form `f(x, y) mod k` will resonate with a map's
lattice. If a decision needs to be spread, hash with avalanche, or derive it from
a count rather than a coordinate.

I walked straight past this while auditing the *same function* for a different
hazard (time dependence) one iteration earlier. Auditing one failure mode in a
line of code does not audit the line.

Still open and unmeasured: `Nav.navTo` tries `rotateLeft` before `rotateRight` —
a fixed handedness, the same bug class, never tested. Mirror-match is the
instrument.

> **AMENDED 2026-09-08 by the corpus scan — see §29. The counts above are not
> corpus facts and they overstate the degeneracy.** `bob-tools/foldscan` read all
> 75 official `.map25` files and found the parity rule is all-one-type on **4
> maps, not "every even ruin spacing"**, with a corpus money share of 53.3%. The
> numbers quoted above (`gridworld 0/9`) cannot be ruin-set counts at all —
> gridworld has **21** ruins, all even — so they are towers actually built in one
> game, presented here as a property of the map. The synthetic lattice simulation
> beside them was over *hypothetical* spacings, never the real corpus. Left in
> place because iteration 7 replaced parity with an avalanche hash partly on the
> strength of this paragraph, and that cost 20 points (§13); a reader arriving at
> that decision needs to see what it was resting on. The *general* lesson — a
> coordinate expression is not a mixing function — survives; the sizing does not.
> And note what this paragraph never mentions, which turned out to be the larger
> defect by an order of magnitude: **mirror symmetry**, 46.4% of all ruins.

## 4. Measurement discipline

**A strict-majority gate means strict.** Iteration 2 came back at exactly 12/24 =
50.0% and was rejected. Accepting it would have cost nothing visible that day and
poisoned the baseline for every later comparison.

**Attribute a rejection to the condition actually evaluated.** I closed iteration
4 with a tidy arithmetic story about chips buying paint income. The story may be
true, but the run never tested it, because no arm on either side ever ran a mixed
economy. A ledger entry that names an experiment which did not happen is worse
than no entry — it forecloses a real question.

**Free pre-checks first.** The iteration 7 hash was validated in seconds against
simulated ruin lattices with no engine, VM or game involved. If a hypothesis is
about a pure function, test it as one before spending an hour of shared VM time.

**Swept maps over raw win rate.** In near-mirror matchups most maps split by side.
Swept-win/swept-loss counts, and the *fall* in split-by-side (10 → 3 at iteration
3), were the signals that separated real capability gains from churn.

## 5. Strategy facts about this game (2025)

- **Paint income is the binding constraint**, not chips. Chips ran to 327k–551k
  unspent while coverage sat at 45%.
- **The endgame is zero-sum.** Long games end with the whole map painted (966 of
  1000 per-mil claimed by someone). Soldiers *cannot overwrite enemy paint at
  all* — only splashers (within r²≤2 of the splash centre) and moppers can. So
  once the map saturates, the 3-in-5 of production that is soldiers stops being
  able to affect the score. The 3:1:1 spawn ratio is an unmeasured iteration-0
  default.
- **Territory penalties are a real paint sink**: ~1–2 paint/turn per robot, so a
  50-robot army burns more paint standing still than several un-upgraded paint
  towers generate.
- The winner's profile from the algorithm — *capability preserved at zero marginal
  cost: standing defenses, spending idle resources, removing pure waste* — paid
  out first try (iteration 3) after two clever-mechanism attempts failed.
- **Coverage decides the game, not combat — see §18 for the 300-game census.**
  298 of 300 tournament games ended on a paint condition and only 2 on
  elimination. Read the two bullets above through that: "the endgame is zero-sum"
  is not merely a late-game fact, it is the *entire* win condition, and the
  territory-penalty paint sink is a direct debit against the only scored quantity.
  Any hypothesis about killing, surviving, or defending owes an explicit account
  of how it converts into painted tiles.

## 6. Process

- **Never run two gauntlets from one workspace**: they share `build/classes` on
  the VM and the second one's rebuild poisons the first one's results mid-run.
- **Never stop while a run is in flight.** Nothing resumes an agent automatically;
  a monitor does not outlive the session. The run keeps going on the VM either
  way, so stopping buys nothing and costs every minute until a human notices. I
  did this once and it cost real time.
- Compile-check candidate code in an isolated directory on the VM
  (`~/bob-tools/<name>/`) rather than the workspace `src/`, so a syntax check
  cannot disturb a gauntlet that is running.
- Keep `HEAD`'s `src/bob` at the best *verified* bot at all times — it is what
  plays in the twice-daily tournament. Uncommitted candidates stay uncommitted.

---

## 7. Lessons from the iteration 5-7 block (2026-09-06)

**A rate is a claim about a denominator.** I reported that our splashers and moppers
ran at "~1% of action capacity". The denominator was cumulative *spawn* counts,
because that is what the dumper's unit columns actually are. Read against live
population (from `Turn` records: 2 moppers alive where 52 had been built), the real
figure is ~37%. The finding reversed completely. Before publishing any per-unit
rate, confirm the denominator is the population you mean, not a total the engine
happens to expose.

**Simulate against the real distribution, not an idealised model of it.** I
validated the tower-mix hash offline against synthetic ruin lattices at spacings
5-8 and concluded the old parity rule "returns 100% one type on every even
spacing". True of a perfect lattice. Measured against all 75 actual map files, the
old rule degenerates on **4 maps out of 75**, and the hash's mean deviation from a
50/50 mix is very slightly *worse* (9.9 vs 9.3 points) because it scatters moderate
skew across maps the old rule had at exactly 50/50. Offline pre-checks are still
right and still cheap — but run them against the real population when the real
population is sitting on disk. It was, and I did not look until after the run.

**When an h2h lands near 50%, count byte-identical games before calling it
marginal.** Determinism makes a re-run worthless, so the useful question is whether
the two arms were ever different. Iteration 5's 15/30 turned out to be 13 of 15
maps byte-identical, i.e. a no-op measured as a coin flip. `results.csv` alone
answers this: identical round counts and the same winning *side* from both sides.

**Check that the map sample can even see the change.** Iteration 7's 20-map sample
contained none of the 4 maps where its mechanism is live. A random sample is the
right default against overfitting, but for a change whose effect is concentrated in
a known subset, the sample size that matters is the number of *affected* maps drawn,
which can easily be zero. Compute the affected subset from the mechanism before the
run, and check the drawn sample against it.

**Selecting maps by mechanism is legitimate; selecting them by outcome is not.**
Re-running on the maps where a change is live is a valid instrument as long as the
subset is defined by the mechanism *before* results are seen, and as long as the
broad random sample is still reported as the no-regression check. Both halves get
stated, or it is cherry-picking.

**Deaths are in `DieAction`, not `Round.diedIds`.** `diedIds` is empty for the whole
game in this engine. Anything counting deaths off it silently counts zero — which
is what my first death-forensics pass did, and it looked like a clean result.

## 8. Instrument bugs produce plausible output (2026-09-06)

Three in one session, all in tooling I wrote, none caught by reading the code:

- **A masked compile failure ran a stale class.** `mop-trace.sh` piped `javac`
  through `head`, so a compile error scrolled past and the previous `.class` ran,
  printing believable metrics from the *previous* version of the tool. Make the
  compile fatal in every wrapper script.
- **Assumed enum ordering.** `RobotType` is NONE=0, PAINT_TOWER=1, MONEY_TOWER=2,
  DEFENSE_TOWER=3, SOLDIER=4, SPLASHER=5, MOPPER=6 — MOPPER is the *highest*. A
  filter of `type > MOPPER` meant to drop towers dropped nothing, and the census
  reported a believable 63/26/9 split that was really 84/3/12. It reversed a
  queued iteration.
- **Assumed a schema field carried data.** Deaths are `DieAction` inside a turn;
  `Round.diedIds` is empty all game, so the first death-forensics pass counted
  zero and looked like a clean result.

The common shape: every one of them printed something plausible. What caught them
was a single value whose correct magnitude was predictable in advance — nothing
printed at all, a 0% that could not be 0%. **Put at least one such value in every
report and check it first.** Probing the enum with `javap -constants` takes ten
seconds and would have prevented two of the three.

Corollary, learned the same day: a denominator is part of the claim. "1% of action
capacity" (cumulative spawns) became ~37% (live population), and "32% of unit-turns
waste a free step" became 10% once towers stopped being counted as units. Both
reversed the resulting decision.

## 9. A waste can be the efficient behaviour (2026-09-06)

The single most instructive result so far. I measured that **78% of our unit deaths
happen at ≤10 paint** — starvation, not combat — across four games, three maps,
three opponents, both sides. Independently confirmed from a tournament replay, where
an unrelated lineage lost 6x fewer moppers than mine on the same map. A real,
general, large, correctly-measured fact.

I read it as the bot's largest leak. It is closer to the bot's most efficient
behaviour.

**Why.** Spawning converts 200 paint into *200 paint plus a body*. Refilling
converts 200 paint into *200 paint*. Bodies were the scarce resource (~15 alive
against ~290 built) and chips were abundant (55,630 unspent in the losing game,
327,000 in an earlier trace), so chips never bound. While paint is the binding
constraint and chips are free, spawning strictly dominates refilling, and a unit
that paints until it starves has already converted its whole stash into tiles and
then freed the economy to build a replacement that arrives with a fresh body.

Fixing the "leak" cut deaths 283 → 31 and lost the head-to-head 16/40, because the
paint went to keeping units alive instead of to building them: 29 soldiers against
the opponent's 45, coverage 267 against 703, dead by round 889.

**The transferable rules:**

1. **Before calling an observed loss "waste", price its alternative.** A resource
   that ends at zero has been *spent*, not lost. The question is never "how much did
   we lose" but "what would the same resource have bought instead".
2. **Identify the binding constraint first, and re-check it after every economy
   change.** Every conclusion about paint here is conditional on chips being free.
   That condition is measurable in one column of the replay dump and I did not look
   at it until after the run.
3. **A dying unit is not a failed unit.** Attrition is the price of doing the thing
   that wins; TRAINING_ALGORITHM.md says exactly this and I still had to pay for it.
4. **Turn a rejection into a test.** The rejection produced a *quantitative*
   condition for its own reversal — "re-open when team chips stop accumulating
   below ~5,000" — which is now a pre-registered readout on the next run rather
   than a note that might get revisited. A closed direction with a numeric trigger
   is worth far more than one closed with a paragraph.

---

## 10. A pre-registered trigger is only as good as its proxy (2026-09-07)

Section 9 ended by praising itself for closing a direction with a *numeric* re-open
trigger: "re-open refilling when team chips stop accumulating — sustained below
~5,000 while towers still want to spawn." Iteration 9 ran that readout. Chips came in
at 360–4,343, sustained for 1,380 rounds, with unit counts climbing the whole time.
The trigger fired.

**And it was wrong.** The mechanism it stood for is *paint stranded in a tower that
chips prevent from being spawned*. Team chips at ~1,300 do not show that: a soldier
costs 250 chips, so that is five soldiers already affordable at that instant. Worse,
the threshold silently collapsed two different stocks — chips are **team-global**,
paint is **per-tower**, and only the per-tower one gates any individual spawn. A
genuinely chip-limited economy pins the treasury below one unit's cost and holds it
there; mine was oscillating at 5–16x that, which is the signature of income being
spent as fast as it arrives.

So iteration 9 did not move chips from "dead" to "binding". It moved them from
**dead** (73,750 unspent on the baseline in the same game) to **in balance**. Paint
still binds. Iteration 8 stays closed, and the trigger is restated as the quantity
that actually gates the decision: *team chips pinned under ~250 while any allied
tower holds ≥200 paint.*

**The transferable rules:**

1. **Register the mechanism's own quantity, not a correlate of it.** "Chips stopped
   accumulating" is a symptom of several different worlds; "a tower has paint it
   cannot spawn" is the one world that matters.
2. **When you must use a proxy, write down in advance what would make it lie.** Had
   I written "this proxy fails if the treasury is merely turning over rather than
   empty", I would have read the column correctly on sight.
3. **Beware thresholds that span two stocks with different scopes.** A team-global
   total and a per-entity stock do not share a threshold; the aggregate can look
   comfortable while every individual is starved, and vice versa.
4. **A trigger that fires and is then correctly refused is still a win.** It cost one
   column of one replay to learn this, against the full gauntlet I would have spent
   re-opening a closed direction on a symptom.

## 11. Relaxing the binding constraint pays where optimising around it does not

Iterations 5–8 all tried to spend the *existing* paint better — waste less to
adjacency, keep units alive longer, stop wandering. Every one was rejected or closed,
and section 9 explains why: the paint was already being spent about as well as it
could be.

Iteration 9 did not improve paint *use* at all. It raised paint *income* — +3
paint/turn on every allied paint tower per Special Resource Pattern, for 200 chips
out of a treasury that was sitting on 73,750 unspent. h2h 62.5%, swept 5–0.

The measured chain: more paint income → more units spawnable → the idle chip pile
converts into bodies (+82 soldiers, +28 splashers, +28 moppers on one map) → more
tiles painted → coverage 703 vs 271. Every step is in the replay dump, and the
arithmetic closes to the right order of magnitude on both the paint and the chip side.

**The rule: when several careful efficiency plays in a row all fail, stop optimising
the constraint and go widen it.** The efficiency ceiling was real; the constraint was
movable. And the tell was visible for many iterations before I acted on it — a second
resource accumulating unspent into the tens of thousands is the loudest possible
signal that the *other* resource is what binds.

---

## 12. A candidate can WIN a game with its mechanism completely inert (2026-09-07)

Iteration 10 added a 20-line neighbourhood search for SRP sites. Its first verification
lost both maps. After one fix it *won* one and took the other to a tiebreaker — a
tempting moment to go spend a gauntlet. The replay counters said `srpA = 0` in both
games: the mechanism had fired **once in 2000 rounds** and completed nothing. The wins
and losses were both about something else entirely.

Had the gauntlet run then, whatever came back — accept or reject — would have been a
number attached to the wrong cause, and it would have entered the log as evidence about
SRP site search forever.

**The rules:**

1. **Read the mechanistic criterion BEFORE the win rate, every time, including — and
   especially — when the win rate looks good.** A favourable number suppresses the
   urge to check, which is exactly backwards.
2. **"Did it engage?" needs a counter, not a result.** Game outcomes are a
   many-to-one function of everything the bot does; only an instrument on the specific
   mechanism can answer whether that mechanism did anything.
3. **Instrument the refusal reasons, not just the successes.** A counter that only
   counts successes cannot distinguish "never tried" from "tried and was refused", and
   the refusal breakdown is what named all three defects here.

Corollary that paid immediately: three separate defects hid inside one small change
(a silently-truncating sense call, painting outside action radius, and a rotation that
defeated its own visibility bound). None was visible in a win rate; all three were
obvious in a refusal histogram.

## 13. Local wins do not compose into global progress (2026-09-07)

Six accepted iterations, every single one of which cleared a head-to-head against its
immediate predecessor. Measured against the frozen `bob_iter1`, which never changes:

```
at iteration 3   34/40  85.0%
at iteration 9   28/50  56.0%
```

The lineage went **backwards by 29 points against an old opponent while winning every
step against itself.** The gauntlet headline over the same span looked healthy, because
it is measured against a pool that moves with the bot.

**The rules:**

1. **A chain of locally-winning steps is not a globally improving path.** Beating your
   own immediate predecessor is a *necessary* condition for progress, not a sufficient
   one, and nothing about repeating it accumulates.
2. **The only instrument that can catch this is one that cannot move.** This is why
   TRAINING_ALGORITHM.md's fixed roster is never retired and never updated. Run it more
   often than every five accepts — it costs one gauntlet and it is the only number in
   the whole system that is not self-referential.

   **I wrote this rule on the morning of 2026-09-07 and broke it that evening**, letting
   the roster go 15 hours and two accepts stale until the coordinator asked. §21 turns it
   into the only form I can't wriggle out of: run it **before** accepting, every time, with
   no margin-size trigger at all.
3. **Marginal accepts are where the drift enters.** `[SUPERSEDED 2026-09-07 -- see the
   note below and §21: true of marginal accepts, FALSE as a restriction to them.]` The prime suspect here is the one
   feature accepted at 52.5% whose own audit recorded that it *hurts 37 maps and helps
   18*, with a documented doubling of side asymmetry — and the roster's failure is
   specifically side-dependent. A 52.5% h2h and a −0.59-point pool effect is not a
   contradiction; it is what a coin-flip accept looks like from two directions.

   **PARTIALLY SUPERSEDED, same day, by iteration 18 — see §21.** This rule is true of
   marginal accepts but **false as a restriction to them**, and believing the restriction
   is what cost me iteration 18. That accept was **+6 games with 6 swept maps and 0 swept
   losses** `[STALE FIGURE 2026-09-08 -- see §25: those are ONE number, not three;
   +6 above the null IS 6-0 net sweeps]` against a null with zero variance — about as unmarginal as this lineage
   produces — and it *still* came out 6 games behind its own predecessor against an
   ancestor. Drift does not enter only through coin-flips. It enters through any accept
   whose gain is conditional on something the baseline happens to carry, and confidence in
   the margin says nothing about whether the gain is conditional. Read rule 3 as
   "marginal accepts are **one** place drift enters", not as a filter that tells you when
   you are safe.
4. **Prefer the ablation to the invention when this fires.** The question "is the
   feature I added five iterations ago still worth anything?" is answerable with one
   pinned run per feature, and TRAINING_ALGORITHM.md records that this historically
   finds more real corrections than new ideas do.

## 14. Check whether your second metric is a function of your first (2026-09-07)

I built a confident story — "four independent opponents all beat us from side B" —
supported by a second statistic, `split-by-side` map counts: 10 of 25 against
`bob_iter1` versus 2 of 25 against `bob_iter0`. Two metrics, same conclusion, different
opponents. It felt like doctrine #10's "a real effect shows up in more than one place".

Both halves were wrong, in different ways:

- The side pattern came from **looking only at losses**. At a 95-98% win rate nearly
  every game is a win, so the handful of losses lands wherever chance puts it. Measured
  over all 271 tournament games the side gap is 2.2 points, **1.01 sd**, and the sign
  flips across my own gauntlets.
- `split-by-side` is **`2p(1-p)` by construction**. Out of 25 maps: p=0.56 predicts
  12.3±2.5 (observed 10), p=0.96 predicts 1.9±1.3 (observed 2), p=1.00 predicts 0
  (observed 0). Every value sat on its expectation. The "second metric" was the first
  metric wearing a hat.

**The rules:**

1. **Before treating two metrics as corroborating, ask whether one is a deterministic
   function of the other.** Derived counts — sweeps, splits, streaks, per-map tallies —
   usually are. Write down the null formula (`2p(1-p)`, `p²`, `(1-p)²`) and compare the
   observation to *it*, not to zero or to another opponent.
2. **A rate needs its denominator.** "Most of our losses are side B" and "we are worse
   on side B" are different claims, and only the second one needs measuring. The first
   is nearly content-free when the win rate is high.
3. **Genuinely independent confirmation comes from a different KIND of instrument** —
   a mechanism counter or a replay-derived quantity like towers built or paint delivered
   — not from another arithmetic view of the same win/loss vector. This is why the
   mechanistic criterion is the one that earns its place in a pre-registration, and why
   "swept-win > swept-loss" is nearly implied by "h2h > 50%" `[SUPERSEDED 2026-09-08 --
   EXACTLY implied, see §25]` and should not be counted
   as a second source.
   **SUPERSEDED 2026-09-08: not "nearly implied" — EXACTLY implied. It is an algebraic
   identity, `margin = 2 x (swept - swept against)`. See §25. Writing "nearly" left room
   to believe the two numbers could disagree informatively, and I went on to quote both as
   agreeing evidence three sections later. The word "nearly" was doing the damage.**
4. **Deviation from the null formula is where the real information lives.** The same
   arithmetic that killed `split-by-side` produced a genuine finding: observed sweeps
   were *fewer* than `25p²` predicts (5 and 0 against 7.8 and 2.8), so the two sides of
   a map are anti-correlated — maps have side-specific character. The metric was not
   useless; comparing it to the wrong baseline was.

## 15. An accept gate against your predecessor is blind to interactions with what the predecessor already carries (2026-09-07)

This is a property of the **method**, not of this bot, and it applies to any lineage
that gates accepts on a head-to-head against its most recent snapshot.

Measured, on 25 pinned maps against a frozen opponent:

```
                        no SRP     with SRP
tower-type hash          76%         56%
parity tower rule        (—)         82%
```

Neither feature is bad alone. The hash without SRPs is 76%; SRPs without the hash are
82% — the best build the lineage ever produced. **Together they are 56%.** An SRP
returns `+3 paint/turn per allied paint tower`, so its payoff is *multiplicative* in
the tower mix, while the hash raised the variance of that mix. Variance that is
survivable when income is linear becomes punishing when it is multiplicative.

**Why the gate could not possibly have caught it.** Iteration 9 (SRPs) was evaluated
head-to-head against `bob_iter7`, and `bob_iter7` **already carried the hash**. So the
hash was present in *both arms* of the comparison. A head-to-head can only see effects
that differ between the arms; anything the two builds share cancels out by
construction. The gate reported 62.5% and was not wrong — the SRPs really are worth
+62.5% *given the hash*. It simply cannot express "and this pair is worth −20 against
everything else".

**The general rules:**

1. **`accept(candidate vs predecessor)` measures the candidate's marginal value
   conditional on every feature the predecessor already has.** It is a partial
   derivative, not a level. A chain of positive partial derivatives can walk downhill
   in absolute terms, and in this lineage it did — six accepts, every one winning its
   gate, and the bot ended 29 points worse against a frozen opponent.
2. **Only an instrument that does not move can see the level.** The frozen roster is
   not a nice-to-have chart; it is the only thing in a self-referential loop that can
   detect this failure at all. Run it *often*, not every five accepts.
3. **When the roster shows a drop, ablate features PAIRWISE, not one at a time.**
   Single-feature ablation would have exonerated both the hash (fine alone) and the
   SRPs (excellent alone) and found nothing. The interaction only appears when you gate
   one off *in the presence of* the other — which is exactly what `bob_abl7`
   (iteration 9 minus the hash) did.
4. **Suspect interaction whenever a new mechanism's payoff is multiplicative in some
   existing quantity.** "+X per existing thing Y" is the signature: it converts
   whatever controls Y's distribution from a linear concern into a variance concern,
   and features that were harmless under linearity become harmful.
5. **A marginal accept is where this enters.** Iteration 7 went in at 52.5% with its
   own audit recording −0.59 points across the map pool. It sat harmlessly for two
   iterations and then cost 20 points the moment a multiplicative mechanism arrived.
   A coin-flip accept is not "free to keep" — it is an unpriced liability against every
   future feature.

## 16. A heuristic that nominates a candidate is not evidence about it (2026-09-07)

LEARNINGS 15 rule 4 says to suspect an interaction wherever a new mechanism's payoff is
multiplicative in an existing quantity. Applied to my own lineage it immediately
nominated a second pair: iteration 3's tower self-upgrade (2,500 chips for +5 paint/turn
on one tower) versus SRPs (200 chips for +3/turn on *every* paint tower). The
arithmetic looked overwhelming — an order of magnitude better per chip — and iteration 3
had been accepted back when chips were a dead resource piling to 70,000 unspent, a
condition SRPs had since removed. Textbook shape.

I ran it anyway. **Removing the upgrade cost 9 games and 8 net sweeps.** The prediction
was backwards.

The arithmetic was wrong because it treated the two as competing for one job.
They are **additive on the same tower**: a level-1 paint tower mines 5/turn and each
SRP adds 3, so three SRPs give 14; upgrading doubles the *base* and the same tower gives
19. The upgrade is what makes each tower a *bigger platform* for the SRPs — and it also
buys 1000 → 1500 HP, which an income-only comparison cannot see.

**The rules:**

1. **A structural heuristic selects what to measure; it never substitutes for the
   measurement.** I was one paragraph from writing "SRPs obsolete upgrades" into the
   closed-directions ledger on arithmetic alone. One 50-game run stopped it.
2. **The sign of an interaction is not predictable from its shape.** Both pairs I found
   have the identical signature "payoff multiplicative in an existing quantity". The
   hash/SRP pair was **destructive**, because the hash controlled the *variance* of the
   multiplier. The upgrade/SRP pair is **constructive**, because the upgrade raises the
   *level* of the base. Structure tells you a pair is coupled; only a run tells you
   which way.
3. **When comparing two mechanisms, first ask whether they are substitutes or
   complements.** "Cost per unit of X" comparisons silently assume substitutes. If both
   effects land on the same object and add, the cheaper one does not retire the dearer
   one — it makes it *more* valuable, and cost-efficiency ratios actively mislead.
4. **A refuted prediction from a good heuristic is a success, not a waste.** It cost one
   run, corrected my model of the economy, and left the rule stronger by bounding what
   it can and cannot tell me.
5. **This section bans nomination by PLAUSIBILITY. It does not ban nomination by
   ANCESTRY — see §21 rule 3.** The distinction matters because the two look alike and a
   future reader could quote this section to refuse an ablation §21 requires. Plausibility
   nomination asks *"which of my features look like they should interact?"* and is a
   prediction, which is why 2 of 3 were refuted. Ancestry nomination asks *"which features
   entered or left between the two generations the roster is comparing?"* and is a
   **lookup** — the roster has already supplied the evidence that something is wrong, and
   ancestry only says where to look. Run the 2x2 when the roster drops; do not run it
   because a pair looks coupled.


---

## 17. A verified mechanism is not a verified benefit — and "idle" has two meanings

Three iterations in one day (13, 14, 15) failed, and two of them failed the *same* way:
the mechanism did exactly what it was designed to do, at the designed magnitude, and
changed nothing.

```
iteration 13  SRP prospecting   produced active SRPs on maps that had none for 2000 rounds   -35 games
iteration 15  bug navigation    built 19 towers on maze where the baseline builds 4           -4 games
```

Iteration 15's verification game was as clean as evidence gets: `maze` was a **swept
loss to an independent lineage**, the diagnosis was "they build ~20 towers, I build 4",
and the candidate built 19. Played from both sides, `maze` splits. TRAINING_ALGORITHM.md
already records this as a regularity ("metrics that improve without converting to
wins"); what this pair adds is that the metric can be the *exact quantity the loss was
diagnosed on* and still not convert.

**The rules:**

1. **Register the mechanism's own subset before running it, and let it be able to say
   no.** Iteration 15's pre-registered subset — the 8 most wall-blocked maps — came back
   1 swept win to 1 swept loss. Without it, one spectacular verification game would have
   carried an accept.
2. **Distinguish a RESOURCE from a CAPABILITY before spending anything you call idle.**
   A resource accumulates when unused and can be *shown* idle by watching it pile up
   (20,720 chips; 461,480 chips) — spending it is nearly free. A capability produces
   value continuously and only *looks* idle because its output is on no counter you
   print. Soldier wandering looked like spare capacity because the soldier's action was
   already spent painting; it was in fact the bot's ruin-discovery system, and
   redirecting it cost three of every four games.
3. **Ask what the fix's own arithmetic says before running it.** The denial probe found
   `SPLASH_MIN_VALUE = 5` refusing 85% of splasher turns with the mean best score at
   4.0 — a constant sitting precisely on the centre of the distribution it gates, which
   looks like a free win. But a splash costs 50 paint and score ~ tiles, so score 4 is
   12.5 paint/tile against a soldier's 5. Lowering it would have been the same failure a
   third time, visible in advance for the price of one division.
4. **A cheap independent instrument you already have beats a careful plan.** Iteration 14
   was built, compiled and pre-registered before the tournament report — already on disk
   — showed that bob loses on money-heavy maps *less* often than chance (9% against a
   15% base rate) and sweeps `gridworld`, the map the whole hypothesis rested on. It was
   never run. That is now the fifth time this project answered a gauntlet-shaped question
   from a file it already had.
5. **A refinement that makes things worse is a finding about the original.** Restricting
   bug-nav's latch to terrain (removing what I had diagnosed as a defect — latching onto
   allies) scored *worse* than leaving the defect in. The "bug" was supplying real
   formation cohesion, which is Phase 0.7's caution seen from the other side.

## 18. Every game is decided by paint coverage; elimination essentially never happens (2026-09-07)

Census of all 300 of my games in tournament `20260907-1300`, joining `results.csv`
against `reasons.txt` — three independent lineages, 75 maps, both sides:

```
BOB_WIN   painted enough of the map                259
BOB_WIN   tiebreak, painted more                    16
bob_loss  painted enough of the map                 16
bob_loss  tiebreak, painted more                     7
BOB_WIN   destroyed all of the enemy team's units     2
                                                   ---
                                                    300
```

**298 of 300 games were decided by paint coverage. Two by elimination, both wins.
Not one of my 23 losses was a loss by being killed.** Every single one was
out-painted, whether at round 308 or on the round-2000 tiebreak.

Three things follow, and they retro-fit several of my own iterations:

1. **The victory condition is a coverage race, not a fight.** Tower HP, unit
   survival and army strength are only instrumental, and only to the extent they
   convert into painted tiles. This is the sharpest form of the algorithm's
   recorded regularity *"metrics that improve without converting to wins"* — I met
   it three times in one day (iterations 13, 15, and the splasher-threshold
   arithmetic), and this census says why: almost any military metric I could
   improve is two steps removed from the only quantity that is ever scored.

2. **It reframes my `catface` and `maze` swept losses.** I had read `catface` as
   "a sibling destroys both my starting towers by round 250, so I have a defensive
   hole". The tower kills are real, but the *game* was lost on paint at round 1431
   and on the tiebreak at 2000. The towers are a mechanism, not the verdict, and I
   was about to build a defensive iteration against a verdict that never occurred.

3. **It sets the exchange rate for iteration 16.** If coverage decides everything,
   then a production slot's worth is exactly the net painted tiles per chip it
   returns — soldier paint gained, plus enemy paint removed (which moves the
   differential twice), minus the paint the unit burns standing on hostile ground.
   That is a computable price, and §3 of the algorithm requires me to compute it
   before building. It is what iteration 16's ablation is measuring.

**The tell for reuse:** I had this file on disk for hours and read only the
standings and the swept-map table off it. The *reason* column was one `awk` away
and is a stronger fact than either. When a report has a column you have never
aggregated, aggregate it before spending a run.

## 19. Reachability means the CHOICE SET, not just the guard (2026-09-07)

Iteration 17 scored candidate ruins by a new term. Three doses — 0, 1, 3 — produced
**byte-identical counters for every soldier in the game**. The change never executed.

The cause: `chooseRuin` iterates `rc.senseNearbyRuins(-1)`, which is *ruins currently in
vision* (r² = 20). A soldier essentially never sees two unoccupied ruins at once, so the
candidate set is a **singleton**, and every scoring function whatsoever selects the same
element of a one-element set.

> **EXTENDED 2026-09-08 — there is a THIRD way, and it cost me a second candidate in the
> same functional area.** Reachability has now failed for this lineage in three distinct
> places, and checking the first two does not cover the third:
>
> 1. **The guard never fires** — a dead branch. (The failure this check was invented for.)
> 2. **The choice set is a singleton** — the guard fires, there is nothing to choose between.
>    (This entry.)
> 3. **The decision is sampled at a degenerate TIME.** Iteration 23's first candidate keyed
>    the tower type on `getNumberTowers()`, expecting the realized share to be a controlled
>    sequence converging on 1/K. The guard fired, the choice set had two live members, the
>    implementation was verified correct on every ruin in play — and the realized money share
>    still swung **14% to 89%** across three maps, because *marking is bursty*: soldiers latch
>    the first ruin they see and hold it for 170-250 turns (measured, iteration 17), so every
>    ruin on the map is stamped with whatever the counter read during one early window.
>
> The unifying question is **"how many distinct values does the deciding quantity actually
> take, at the moments the decision is made?"** A guard check answers it for the branch, a
> choice-set check answers it for the options, and neither answers it for the *sampling
> distribution*. All three are the same failure — a decision with one effective input — and
> the third is the one that survives the first two checks.
>
> Note this is the same underlying fact about soldier behaviour, reaching a third mechanism:
> **ruin claims are latched early and never revisited.** That fact has now voided two
> candidates and constrained a third. It is a property of the bot I keep designing *around*
> instead of changing, and it belongs on the candidate list in its own right.

I did run §3's reachability pre-check. I applied it to the **guard** — "is this branch
ever taken?", and it is, on 85% of soldier turns — and never to the **set the branch
ranks**. A ranking change inside a reachable branch is still dead code if the thing being
ranked has one element.

**The general form:** for any change to a comparison, tie-break, priority or score, the
reachability question is not *"does this code run?"* but *"does it ever run with two or
more candidates?"* Instrument the size of the choice set, not the frequency of the branch.

Cost of catching it here: three single-map games. Cost of not catching it: a 100-game
gauntlet reporting a difference that could only have been churn.

## 20. A floor constant on a threshold good manufactures zombies (2026-09-07)

`PAINT_FLOOR = 15` stops a soldier painting when its stash drops below 15. Traced with
`tools/replay-dump.sh --robot`, one soldier:

```
round  42  (23,17)  paint=14  aCD= 2  hp=250
round 225  (24,18)  paint=13  aCD= 0  hp=250      <- ~200 rounds
```

Its action was **available and unused for roughly two hundred consecutive rounds**, and its
HP never moved. `NO_PAINT_DAMAGE` applies only at *zero* paint, so the floor parks the unit
one point above the band that would kill it. The bot manufactures immortal do-nothing
soldiers — TRAINING_ALGORITHM.md's *"survival bought with inactivity"*, produced by a
constant rather than by a policy.

Two compounding reasons the constant is wrong here, and the second is the general lesson:

1. My own iteration-8 economics concluded that **dying at zero is the efficient terminal
   state** — a unit that paints until it starves has converted its whole stash into tiles
   and freed the economy to build a replacement with a fresh body and a full stash. The
   floor prevents precisely that.
2. **A floor is a linear-value heuristic, and it was sitting on top of a threshold good.**
   Reserving the last 15 paint is sensible if paint converts to value smoothly. A tower
   pattern does not: 119 of 120 paint buys **zero** towers, 120 buys +5 paint/turn forever.
   Under a threshold, the marginal value of the last unit spent is the *highest*, not the
   lowest — which inverts the reasoning a floor is built on.

**Reusable tell:** whenever a reserve, floor, minimum or "keep some back" constant guards
a spend, ask whether the thing being bought is linear or a threshold. If it is a threshold,
the constant is backwards near the threshold, and the size of the reserve is exactly the
size of the loss.

## 21. Head-to-head margins do not chain (2026-09-07)

Measured on my own lineage, on identical maps, both comparisons exact:

```
bob_iter18 vs bob_iter12 (its predecessor)              +6 games, 6 sweeps, 0 swept losses
bob_iter18 vs bob_iter11, minus bob_iter12 vs bob_iter11   -6 games, and 1 sweep against 4
```

**CORRECTION 2026-09-08 (§25): the two halves of each line above are ONE number, not two.**
`+6 games above the null` and `6 sweeps, 0 swept losses` are the same fact — 6-0 = 6 — and
quoting them side by side made a single measurement look like a corroborated one. The
finding of §21 is unaffected (both lines are still exact, and they still disagree in
direction, which is the whole point), but the *weight* I put on iteration 18 was inflated.

Beating the thing you replace by six games is **compatible with being six games worse than
it** against something three generations back. Both numbers are exact — same 25-map sample,
both sides, a null with zero variance — so this is not a measurement problem. It is a fact
about the ordering: **strength here is not transitive, and a chain of positive head-to-heads
does not integrate into a level.**

The coordinator relays that another lineage measured the same phenomenon independently the
same night, with the sign in its favour: a feature worth +6 against its immediate
predecessor and **exactly 0** against the generation before it, established at cell level.
Two lineages, opposite signs, same structure. That makes it a property of the game and the
method, not of my bot.

**Consequences I have to actually change my behaviour for:**

1. **The frozen roster is not an audit, it is the only instrument that reports a level.**
   The head-to-head reports a *difference against one specific opponent* and nothing more.
   I had been treating the roster as periodic housekeeping — doctrine #9's "every ~5
   accepts" — and the roster is what caught this.
2. **Run the roster BEFORE accepting, and "thin margin" is the wrong trigger.** Doctrine #9
   says to do this on thin margins. My margin was +6 with 6 sweeps and 0 swept losses,
   which did not feel thin at all — and that is precisely why I skipped the check that
   would have caught it. **The rule failed at the exact moment it felt unnecessary, which
   is the only moment it ever matters.** So the trigger is not the margin's size; it is
   simply "before accepting".
3. **When the roster drops, ancestry names the pair — not plausibility.** Now §5b in the
   loop document. The candidates are the features that entered or left *between the
   generations the roster compares*, which is a lookup rather than an act of imagination.
   Mine: `bob_iter11` had ruin memory, `bob_iter12` deleted it, `bob_iter18` bet on
   spending a soldier's last paint into work that only pays if a replacement returns. A gate
   whose **both arms lack** the feature that would make the bet pay cannot see the problem.

**The reusable shape:** any mechanism that spends a unit's last resource on work that only
pays out *later, via somebody else* is a bet on the machinery that brings somebody else
back. Check that machinery exists before pricing the bet.

**Second instance, next day (2026-09-08), and it is the OTHER face of the same fact.**
§21 above is "direct margins do not chain into a level". Iteration 19 produced the converse:
a gap measured against a *common reference* did not predict the *direct* head-to-head.

```
against bob_iter11 (draw 1):   bob_mC 26/50  vs  bob_iter18 19/50     -> mC ahead by +7
directly (draw 2):             bob_mC 22/50 against bob_iter18        -> mC behind by -3
```

Both exact, both against a zero-variance null. So neither direction of the inference works:
you cannot chain direct margins into a level, **and you cannot read a direct margin off two
comparisons with a shared third party.** The only measurement of "does A beat B" is A
against B. Anything else is a different quantity that happens to be denominated in games.

**Where this sits in this file** (added by the consistency pass, because these four
sections are one thread and none of them cited the others):

- **§13 is this same finding, measured on a different generation and written the same
  morning.** It already said "run the roster more often than every five accepts". I broke
  my own rule that evening. §13's rule 3 — *marginal accepts are where drift enters* — is
  **partially superseded here**: iteration 18 was the opposite of marginal and drifted
  anyway, so margin size is not a safety signal.
- **§15 is the mechanism**, in the abstract: an accept gate is a partial derivative,
  blind to any interaction with what the baseline already carries. §21 is the first time I
  measured it happening to me rather than reasoning about it.
- **§16 bans nomination by plausibility; §21 rule 3 permits nomination by ancestry.**
  These are not in conflict and §16 rule 5 now says so explicitly — one is a prediction,
  the other is a lookup performed only after the roster has already found something wrong.

## 22. The map that suggested the hypothesis is the worst map to size it on (2026-09-08)

TRAINING_ALGORITHM.md warns "check your sizing map is not degenerate". This is the sharper
version, and it is a *selection effect*, not bad luck.

I nearly built a soldier-repulsion mechanism on the strength of `mit`, where my soldiers sat
**6.5x** more clustered than a uniform-placement null. Sizing it on three more maps:

```
map              r200    r400    r600    r800
mit   60x60      3.2x    6.5x    4.2x    1.4x     <- the map that suggested it
Gears 55x55      0.0x    1.0x    1.6x    1.6x     <- the LARGEST map: no effect at all
rain  30x30      2.2x    2.5x    1.6x    2.2x
quack 30x35      2.6x    1.0x    1.0x     -
```

**The reason `mit` suggested the hypothesis is the same reason it is atypical**: I noticed
clustering there *because* clustering was extreme there. Any map that makes an effect
visible enough to hypothesise about has been selected for having an unusually large value of
it. So the motivating map is not merely a poor estimate of the population — it is a
*biased* one, biased upward, every time.

**Rule:** the motivating map may establish that an effect *exists*; it may never be used to
size it. Size on maps chosen before you looked. Cost of obeying this: zero games. Cost of
not obeying it here would have been a full 200-game evaluation of a mechanism worth nothing.

Cross-links: §10 (a pre-registered trigger is only as good as its proxy) is the same error
one level up — there the proxy was wrong, here the *sample the proxy was calibrated on* is
wrong. §18's 300-game census is the counter-example that shows the fix: a claim sized on the
whole corpus needed no such caveat.

## 23. Check that a number lies in its own logical range (2026-09-08)

My first coverage table read **`DefaultSmall 134.4%`**. A percentage over 100 cannot be a
close call — it is a proof of error, available before any interpretation and requiring no
domain knowledge at all. Cause: `Round.teamCoverageAmounts` is **per-mille of TOTAL map
tiles** (`tools/engine-facts.md` says so explicitly) and I had divided it by *passable*
tiles. Exactly doctrine #5's wrong-referent error, and exactly the failure this file's §8
records for instrument bugs.

What made it safe to proceed afterwards was closing the accounting, not just fixing the
divisor:

```
census 3025 tiles = 2002 painted (T1 1106) ...  coverage per-mille  T1 recon=366 engine=382
```

recon 366 against engine 382, gap **−16**, and T1 had **17 units** on the board occluding
paint in the reconstructed grid. The residual is explained to within one tile, which is what
licences reading anything off the corrected figures.

**Rule:** before interpreting any derived quantity, ask what range it is *allowed* to take
and check it is inside. Shares in [0,1], counts ≤ their population, per-mille ≤ 1000. This
catches the wrong-referent class of error at zero cost, and it caught one the same day I
was congratulating myself for catching two others.

## 24. "Idle" has a THIRD meaning: structurally incapable (2026-09-08)

§17 distinguishes an idle **resource** (accumulates unused; spending it is nearly free) from
an idle **capability** (produces value continuously, looks idle only because its output is
on no counter). Iteration 20's trace found a case that is neither:

```
Gears, rounds 900-920, map 99.9% painted
  2441 soldier-turns  ->  10 painted tiles   (0.4% of turns)
   534 splasher-turns ->   3 splashes = 33 converted tiles
  and 89.6% of those soldiers held paint ABOVE the floor -- they were not starved
```

The soldiers were able to act, had paint, had no cooldown problem, and had **no legal
scoring move**: soldiers cannot overwrite enemy paint at all, and the map was full. That is
not inefficiency and not a hidden capability — it is a unit type that has become
*structurally incapable* of affecting the score, while still costing 200 tower paint every
time one is re-bought.

**The diagnostic that separates the three:** ask what the unit *could* do if it played
perfectly from here. A resource would be spent; a capability would keep producing something
you were not counting; a structurally incapable unit would do **exactly the same nothing**.
Only the third case licences removing the unit rather than improving it.

This is also why §17's warning did not protect me and should not have: §17 says do not
redirect something that looks idle. Here the finding is stronger than "looks idle" — the
rules of the game say it cannot act. Cross-links: §18 (coverage decides every game) is what
makes "cannot affect the score" equivalent to "cannot affect the outcome"; §5 already
recorded that soldiers cannot overwrite enemy paint and that the 3:1:1 spawn ratio is an
unmeasured iteration-0 default, and those two facts sat in the same section, eight lines
apart, for a day without being put together. **Two facts in one section that imply a
candidate and never cite each other is the same tell as two rules that never cite each
other.**

### 24a. Amendment, written BEFORE the run returned: "incapable" was too strong — they are DEMAND-LIMITED

Checked §24's claim one more time before results could bias me, and it does not survive as
written. Soldiers cannot overwrite *enemy* paint, but **moppers remove enemy paint and leave
the tile NEUTRAL** — and a soldier can paint neutral. So there is a two-step conversion path,
mopper then soldier, and the soldier is a real part of it. Counted over the same windows:

```
map            T1 soldier PAINT   T1 mopper UNPAINT   T2 mopper UNPAINT
Gears                10                  2                  19
DefaultLarge         14                 22                  18
Money                24                 10                   2
Parking_lot          23                  6                   1
```

Soldier paints sit in the same order of magnitude as total mopper activity on both sides
(plus, on the two maps that never fully saturate, some residual virgin ground). That is the
signature of soldiers servicing neutral tiles as they are *created*.

**So the correct statement is not "soldiers cannot score" but "soldier work arrives at a rate
set by mopper activity, and I field 100+ soldiers to service 7-40 tiles per 21 rounds."**
Demand-limited, not incapable. The distinction matters for the candidate:

- It **strengthens** the case for cutting the soldier share, because the required number of
  soldiers is set by the neutral-tile arrival rate, not by how much paint the team holds.
- It **predicts an interior peak rather than a monotone curve** — cut soldiers far enough and
  the mopper→soldier chain starves, so 1:3:1 may well be worse than 2:2:1. That is now a
  mechanistic reason for the interior-peak branch I pre-registered, rather than mere hedging.

The general lesson, which is the one worth keeping: **before calling a unit useless, enumerate
who else changes the state it consumes.** I had checked what a soldier can do to enemy paint
and stopped there; the answer changed once I asked what makes a tile neutral in the first
place. §17's "does this ever engage" question applied to the *supply* of work rather than to
the mechanism.

## 25. The margin and the swept-map count are the SAME NUMBER (2026-09-08)

Relayed by the coordinator from another lineage, now doctrine #14 in
TRAINING_ALGORITHM.md, and **verified independently on all 8 arms of my own last two runs
before I accepted it**:

```
run 20260907-212222      wins   margin    2*(SW-SL)          split maps D
  bob_iter12            28/50     +6     2*(6-3) =  +6            16
  bob_iter18            31/50    +12     2*(9-3) = +12            13
  bob_mC                24/50     -2     2*(4-5) =  -2            16
  bob_mD                28/50     +6     2*(7-4) =  +6            14
run 20260907-232155
  bob_iter11            23/50     -4     2*(3-5) =  -4            17
  bob_iter12            22/50     -6     2*(1-4) =  -6            20
  bob_iter18            22/50     -6     2*(1-4) =  -6            20
  bob_mirror            25/50     +0     2*(0-0) =  +0            25
```

**Why it is an identity, not a correlation.** Every map is played from both sides, so
`wins = 2·SW + D` and `losses = 2·SL + D` where D is the maps that split. D cancels:

```
margin = wins - losses = 2·(SW - SL)          exactly, always, whatever the bots do
```

Equivalently, in the units I actually quote: **wins above the 25/50 null = (SW − SL)**. An
identity always agrees with itself, so it can never corroborate anything.

**This is pointed at me.** I accepted iteration 18 on *"+6 games, 6 swept maps, 0 swept
losses"* and called it "about as unmarginal as this lineage produces". Under the identity
that is **one** piece of evidence wearing three hats — 6 − 0 = 6 — and it is the accept that
a later same-sample run found to be 6 games *worse* than its predecessor against their
common ancestor. §21 concluded the frozen roster is the only instrument reporting a level;
this makes that conclusion stronger, because the thing that made 18 look safe was a single
margin quoted three ways.

**What sweeps DO add, and it is real: D, the decisiveness.** The margin fixes `SW − SL`;
the sweeps also give you `SW + SL`, hence D. That is genuinely independent of who is ahead.
The mirror row above is the clean example — margin 0 *and* D = 25 — and "identical code
splits every single map" is a much stronger statement than "identical code scores 50%".
This is also exactly §14 rule 4, which survives intact: the information is in the deviation
of the sweep *count* from its null (`25p²`), never in the sweep *difference*.

**The consistency-pass lesson, which is the expensive half.** §14 rule 3 already said
swept-win > swept-loss is *"nearly implied"* by h2h > 50% and should not be counted as a
second source. I wrote that on 2026-09-07 and then quoted margin-and-sweeps as agreeing
evidence in §21 the same night, and again in the iteration 19 log the next day. **The word
"nearly" was load-bearing damage**: it left room for the two numbers to disagree
informatively, so the rule read as a caution rather than a prohibition, and a caution is
exactly what momentum overrides. When something is an identity, say identity — and derive
it in the entry, because a derivation cannot be softened by a later reader in a hurry.

### 25a. Say WHICH margin (2026-09-08)

The coordinator's follow-up: there are two forms and **both are exact**, differing only in
what the word "margin" names.

```
margin over 50%   wins - N        =      (SW - SL)        over N maps, both sides
margin as spread  wins - losses   =  2 x (SW - SL)
```

An identity quoted without its definition produced a false disagreement between two parties
who were both right. My §25 above happens to state both forms and label them, and my
iteration-18 arithmetic used the first (`31/50` = +6 over the null = 6 − 0 net sweeps), so
the reading stands. But the general rule is worth more than the check: **when quoting a
margin, name the quantity.** "+6" is not a number in this project until you say whether it
is games above the null or games of spread — they differ by a factor of two, and every
comparison between two entries in this log silently assumes they used the same one.

I have used "games above the null" throughout, including in §21 and in every iteration
entry. Recording that here so a future reader does not have to infer it.

## 26. Independence of the DERIVATION is not independence of the REFERENT (2026-09-08)

Relayed by the coordinator, who made the error himself: a second session independently
re-derived another lineage's statistic without seeing the first, and that was called strong
corroboration. It was not. The statistic had already been retracted as a post-spend artefact
under doctrine 15, and **re-deriving a number does not repair its referent** — both routes
read the same invalid quantity out of the same replay.

The clean pair, from the *same* post-spend data:

```
"how often could the tower afford X"           INVALID -- post-spend state is conditioned
                                                on the spending it is meant to predict
"high tower paint is a symptom of a shut gate"  SOUND -- a claim about what state PERSISTS,
                                                and persistence is what post-turn state records
```

**Ask what a derivation measured, not what path it took to get there.** Two derivations of
the same wrong referent are one error counted twice — which is §14's identity problem with a
longer lever.

**Applied to my own cross-check from an hour earlier, because I came close to this.** I
wrote that the replay census (68% of splashers could afford a splash) and the in-bot denial
probe (5.2% blocked by paint at the decision point) were "two instruments agreeing". Stated
that way it is the error above. The honest version:

- They are **not** two measurements of one quantity. The in-bot probe measures affordability
  **at the decision point** — the referent I actually care about. The replay census measures
  **post-action paint**, a systematically lower shadow of it.
- So the probe **carries the claim on its own**. The replay number corroborates only in the
  weak sense that it sits on the correct side of the predicted bias — which is a
  *consistency check on my understanding of the bias*, not a second vote for the conclusion.
- What makes this legitimate rather than circular is that the two referents genuinely differ
  and one of them is valid. Had both been post-action, agreement would have meant nothing at
  all.

**The reusable test:** before calling two numbers corroborating, write down the *quantity*
each one is an estimate of. If it is the same quantity reached two ways, you have one
measurement. If the quantities differ and at least one is valid for the claim, you have
evidence — and you should be able to say which one is doing the work. In my case the in-bot
probe is doing the work; the replay census is decoration, and I have relabelled it as such.

**Documentation hygiene, adopted the same day.** "Supersede in place, do not delete" is
correct — a withdrawn rule was load-bearing for whatever was decided while it stood — but it
leaves a stale rule *looking live* to anyone who greps and lands on the first match rather
than the newest. Superseded rules and stale figures now carry an inline
`[SUPERSEDED <date> -- see §N]` / `[STALE FIGURE <date> -- see §N]` marker on the line a
grep would hit, applied retroactively (§13 rule 3, §14 rule 3, and the "+6 games / 6 sweeps"
figure). Preservation and a warning are not in tension; leaving the warning off the matched
line is what made them look so.

## 27. I reported a real bug with a false symptom — and the symptom I named was untestable (2026-09-08)

I reported the `+cand` roster-label bug this way:

> an accepted candidate's roster point stays permanently "hollow" on the only absolute
> chart I have — it reads as "may have been rejected" when it was accepted.

The bug was real and the coordinator fixed it. **The symptom I attributed to it was wrong.**

`plot_vs_old_bots.py` reads three fields per CSV row: it groups series by `opponent`,
positions by `date`/`win_pct`, and decides marker fill from `source` alone —

```
solid  = [p for p in pts if p[4] != "backfill"]     # p[4] is the SOURCE column
hollow = [p for p in pts if p[4] == "backfill"]
```

The `bot` column — the field `+cand` corrupts — **is never read by the plot**. My row's
source was `roster-run`, so my iteration 20 point was drawn *solid before the fix and solid
after it*. Confirmed: re-deriving with the fixed tool rewrote 4 rows in the CSV and left
`vs_old_bots.png` byte-identical.

**Why this is worth an entry rather than an erratum.** Had I "verified" the fix the obvious
way — look at the chart, see a solid point, declare it fixed — I would have been right by
accident. The two hypotheses (fixed / not fixed) render **the same image**, so the chart has
*zero* discriminating power on this question. That is the coordinator's own finding about
bug #1 in a second instance: a verification performed where the hypotheses do not differ is
not a verification. Here they do not differ *at all*, which is the degenerate worst case.

The discriminating instrument was the CSV's `bot` column, and it is the one I checked:
`bob_iter18+cand` → `bob_iter20`. Fixed.

**What the bug actually cost**, stated as what the code computes: not appearance, but
**provenance** — the durable record of *which snapshot* achieved 35/50 vs `bob_iter11` was
filed under the wrong name. `gauntlet/` is git-ignored, so that CSV is the only lasting
record of it; a wrong name there is a wrong answer to "when did this lineage turn around",
which is exactly the question iterations 12–20 existed to settle.

**The transferable rule, and it generalises past tooling.** When reporting a fault, name the
observable that *distinguishes* faulty from fixed, and check that it distinguishes before
naming it. "It looks wrong on the chart" was a symptom I never confirmed the chart could
show. My own report was the un-run discriminating case — the same failure I have twice now
caught in someone else's instrument, committed in my own bug report.

## 28. Every map in the corpus is symmetric — but only 27 of 75 are symmetric the way you'd guess (2026-09-08)

Read straight from the 75 `.map25` flatbuffers inside the engine jar (a Python re-parse I
wrote for this; nothing here comes from any agent's workspace, so it is shared ground on the
same footing as `tools/mapdata`). Testing the wall grid for invariance under vertical
reflection `(W-1-x, y)`, horizontal reflection `(x, H-1-y)`, and 180° rotation `(W-1-x, H-1-y)`:

```
symmetric under at least one of the three     75 / 75      no exceptions
  vertical reflection only                    30
  horizontal reflection only                  18
  180 rotation only                           23
  all three (fully bilateral)                  4
```

**So 48 of 75 maps — 64% — are NOT rotationally symmetric.** Anything that assumes "the
enemy's copy of my spawn is my position rotated 180° about the centre" is simply wrong on
two maps in three. That is a large, quiet trap: the assumption is the most natural one to
make, it is right often enough to look fine in a trace, and no error is ever raised.

**Why iteration 21's beacon is safe anyway, which is the point worth keeping.** The beacon
does not need to be the true mirror. It only needs to land in the *enemy half*, and that is
implied by whichever symmetry holds:

```
vertical reflection   enemy half is x > W/2   beacon x' = W-1-x > W/2   in enemy half
horizontal reflection enemy half is y > H/2   beacon y' = H-1-y > H/2   in enemy half
180 rotation          both coordinates flip   both hold                 in enemy half
```

**The general lesson: weaken the claim until it is symmetry-agnostic, instead of detecting
the symmetry.** Detecting it needs observations, comms and a fallback for "not yet known" —
three new ways to be wrong, and iteration 17 was voided by exactly that class of failure (a
mechanism that never executed). Asking only for the *half* costs nothing and cannot be wrong
on any map in the corpus.

### Two methodological notes, because both nearly bit

**The indexing convention was an assumption, so I ran the discriminating case.** Reading the
wall vector as `y*W+x` versus `x*H+y` swaps the "vertical" and "horizontal" labels. Square
maps cannot tell them apart — a transpose preserves rotational symmetry — so the
discriminating set is the **non-square** maps:

```
row-major  y*W+x    symmetric 75/75    non-square 25/25
col-major  x*H+y    symmetric 54/75    non-square  4/25
```

Row-major, decisively. Had I checked only the corpus-wide 75 vs 54 I would have had a weak
argument; the non-square subset is where the two hypotheses actually differ. Same rule as
§27 and as the coordinator's finding on the coverage denominator, now three times over:
**test where the hypotheses differ, not where the data is convenient.**

**The parse is externally corroborated.** My scan gives `DefaultMedium` 35x35 with **32 walls
= 2.6%**. The coordinator, by a different route (Java, engine source), independently
described the map that defeated the coverage-denominator verification as having "32 walls in
1225 tiles — 2.6%". Two independent implementations agreeing on a specific count is a real
check on the parser, and it is the kind of check §26 says to look for: independent
*derivation*, not just an independent-looking number.

**Prior art in my own toolbox, stated so this does not read as a fresh discovery.**
`bob-tools/BobSym.java`, written for the iteration-14 tower-type audit, already says "maps
are guaranteed symmetric" and already *infers* which of the three transforms is in force per
map. What §28 adds is the corpus **distribution** — which that tool computes per map and
never tabulated — and the consequence: because rotational symmetry is the *minority* case
(27 of 75), inferring the transform is unavoidable for anything that needs the true mirror,
while anything that needs only the enemy half can skip inference entirely. The first tool
needed the mirror (a ruin and its counterpart), so it had to infer. The beacon does not, so
it must not.



## 29. Closing the FIX is not closing the DEFECT (2026-09-08)

Iteration 12 replaced iteration 7's avalanche hash with `((x+y)&1)` and is the largest
effect this lineage has measured, **+26 points**, justified by team symmetry: "under
rotation `(x+y)` and `(W-1-x + H-1-y)` share parity **whenever `W+H` is even**." Every clause
is true, and the conditional is not the corpus — `x` and `W-1-x` share parity iff `W` is odd,
and **48 of the 75 maps have an even dimension**, where the rule assigns opposite types to
*every* mirrored ruin.

**I did not discover that today. I measured it at iteration 14 and wrote it in my own log:**
`bob-tools/BobSym.java`, 30 maps (40%) with a mismatched mirrored pair, team gap 11.0 points.
Then I built the obvious fix — fold the coordinates into the canonical quadrant — measured it
offline in three minutes, found it doubled whole-map mix variance, and **closed it**. The
entry reads, correctly, "no rule dominates."

Eight iterations later I re-derived the entire thing from scratch: same defect, same fix,
same corpus, a scanner that reproduces the old numbers exactly. I found the old entry only
after the replacement run was already in flight, by grepping for the *tool's* name.

**The lesson is about the shape of the ledger, not about symmetry.** A closed-directions
ledger records the *fix* that was killed. But closing a fix quietly retires the *defect* too,
because the defect now lives only inside an entry whose headline is a rejection — and nobody
re-reads a rejection looking for an open problem. The 40%-of-maps asymmetry had been measured,
priced, and abandoned, and no artefact anywhere said "this is still broken".

Three things that follow:

- **Grep the ledger by MECHANISM, not by functional area.** I searched for the iteration
  number and the area ("tower type") and found nothing; searching for what the change *does*
  ("fold", "symmetr", "mirror") found it instantly. Closed entries are named after their
  mechanism.
- **When you close a fix, state separately whether the DEFECT is closed.** "No rule
  dominates" closes a fix and leaves a defect standing; those need different words, and one
  of them should end up in a standing list of known-open problems.
- **An audit tool is a regression test, not a one-time verdict.** `BobSym` exists precisely
  to audit `towerTypeFor`. It was run on the hash, and never re-run when iteration 12 put a
  different rule in the same function. The moment to re-run an audit is when the audited code
  changes.

**What legitimately re-opens it** (recorded because "I forgot" is not a re-open reason): the
iteration-14 closure weighed an *unpriced* team gap against an *unpriced* mix deviation.
Iteration 12 then priced one side and not the other — its +26 was attributed to mix
mismatch. So the trade the closure adjudicated has since acquired a number on one arm. That
is new information about the closure's own reasoning, which is the only thing that ever
justifies re-opening.

**And read this with §3, which it amends.** §3 condemned this same function for a *different*
defect (mixing), sized that defect from a synthetic lattice simulation plus four per-game
tower counts rather than the corpus, and never mentioned symmetry. §3 and §28 are about the
same function and the same corpus and had never cited each other before today — the "two
rules that ought to cite each other and never do" tell from TRAINING_ALGORITHM.md.

## 30. A missing capability is invisible to every instrument except a scheduled sweep (2026-09-08)

22 iterations in, a four-minute diff of `javap battlecode.common.RobotController` against my
own call sites found **27 of 68 methods never called** — including the *entire* communication
subsystem (`sendMessage`, `readMessages`, `broadcastMessage`), free-standing `mark`, and
`getNumberTowers`.

**Why it survived 22 iterations of an evidence-driven loop.** Every instrument this lineage
owns is triggered by something going wrong: a losing replay to trace, a metric out of range, a
rejected candidate to explain. An API method that is never called produces **no error, no bad
number, and no losing game that points at it**. The loop is a search over *fixes to observed
faults*, and a capability you never had cannot generate a fault — it generates a ceiling, and
ceilings are silent.

That is why TRAINING_ALGORITHM.md makes this a *scheduled* sweep rather than a response to a
symptom, and it is the same structural blindness as §15 (an accept gate cannot see an
interaction with a feature both arms carry) and the "self-referential blind spot": in all
three cases the thing you cannot see is the thing that is absent from *both* sides of every
comparison you run.

**The sharpest instance.** Iteration 17 was voided on the finding that `chooseRuin` ranks a
one-element set, and I concluded soldiers "would need memory of ruins seen earlier — a much
larger change than the one I priced". That conclusion was reached without knowing `mark`
existed: an ally-visible annotation, r²<=2, **1 paint**, no action cooldown, needing no radio
and no protocol. I priced a design space that was missing one of its cheapest members, and
nothing in the void analysis could have revealed that, because the analysis was correct about
everything it did consider.

**The transferable rule: when you write "X would require x", check that the platform does not
already provide x.** The sentence "that would need memory / comms / coordination" is a claim
about the API, not about the design, and it is the exact sentence to stop on.

Corollary worth keeping: a documented constraint can be an artefact of your own code rather
than the engine. `towerTypeFor`'s comment says the tower type "must stay a pure function of the
ruin and never of time" — true only because `workOnRuin` *recomputes* the type before calling
`canCompleteTowerPattern`. `getTowerPattern` lets the type be read back off the marks already
on the ground, which is where the decision was recorded in the first place. **Before treating a
constraint as binding, find the line that imposes it.**

## 31. The binding resource is a property of the MAP, and it inverts (2026-09-08)

Measured at the spawn decision point, in-bot (`src/bob_sprobe`), share of tower-turns on which
the spawn was refused for want of chips:

```
map          r200    later             paintBlock (later)
memstore     90.0%   78.5% (r600)         17.5%
Justice      51.3%   23.5% (r400)         74.5%
Flower       38.8%    8.7% (r600)         88.7%
DonkeyKong     --     7.5% (r2000)        88.6%
Dominoes      0.0%    0.0%                97.5%
```

On Dominoes the bot is **never** chip-limited and almost always paint-limited. On memstore it is
the reverse for the whole game. This is not a fact about the bot; it is a fact about the map,
and any global constant that assumes one regime is wrong on the other.

**Three consequences, in increasing order of how much they cost me.**

**1. A strategy fact.** A single global tower-mix or reserve constant cannot be right, because
the resource it trades against is not the same resource on every map. This is the strongest
case this lineage has yet produced for the design preference both predecessor projects reached
independently: *self-calibrating thresholds beat fixed constants for opponent- and map-variable
behaviour*. Deriving the threshold from what a tower can observe about its own refusals is
strictly better than searching over more constants, and the refusal counter is already written.

**2. Three agreeing maps are not a corpus.** I sized "chips are slack" on DonkeyKong, Flower and
Dominoes. All three agreed. All three were right. **memstore is the exact opposite** and the
premise died on a 150-game run. TRAINING_ALGORITHM.md §3 says *"a quantity measured on one map is
a statement about that map until you check it elsewhere"* — I read that as "use more than one
map" and satisfied it. The real content is **span**, not count: three maps that agree tell you
less than two that disagree, because agreement among a small sample is exactly what a
regime-dependent quantity produces when the sample lands inside one regime.

**3. Post-decision measurement: doctrine 15 in a different coordinate.** My premise rested on
$132,014 of chips unspent at r2000. That number is correct. It is also taken **after the game is
decided** — the map is full by ~25% of game length, coverage peaks near r150 (§18: every game is
settled on coverage), and the probe shows chip-blocking is an early phenomenon that decays as
the game goes on. So chips bind exactly when it matters and release exactly when it stops
mattering, and measuring the endgame captures only the half where the answer is "slack".

Doctrine 15 warns about reading robot state recorded *after the action*. This is the same error
one level up: reading team state *after the decision that state was supposed to explain*. The
tell is identical — a quantity that looks abundant precisely because the thing that consumes it
has already finished. **When a resource looks free, ask when it looked free, and compare that to
when the game was decided.**

**And the finding that came out of it is worth more than the iteration was.** The spawn gate is
`chips >= cost + reserve` with `reserve = 1200` (1450 for a soldier), and memstore's treasury
sat at a mean of 1000-1350 for the entire game — **pinned just below my own gate**. On
chip-limited maps it is not the economy refusing to spawn, it is a constant I wrote in iteration
0 and never measured. A resource pinned in a dead band is one of the two absolute degeneracy
signals the algorithm names, and it took a decision-point probe to see it, because from outside
the bot "treasury sits at 1200" and "treasury cannot afford anything" look the same.

---

## 32. A 2-game margin bought a mechanism story; replication cost nothing and refuted it (2026-09-08)

Iteration 25 measured `+2` for one dose arm and I wrote several paragraphs explaining *why* — a
genuinely nice argument about utilisation counting towers eventually built while saying nothing
about when. Iteration 26 put the same arm on a fresh map sample: `−1`. Pooled over 200 games: `+0`.
The mechanism I explained does not exist.

The damning part is that **I had already written the correct caveat** in the same entry — *"the
peak's location is far better supported than its height — location rests on a sign pattern across
five doses, height on two games"* — and then wrote the mechanism section as though the height were
real. That is doctrine 6 exactly: the caveat was flagged, and then reasoned past. A flagged caveat
has to **constrain what you write next**, and the concrete test is: *would this paragraph survive if
the number it explains were zero?* If not, do not write it until the number replicates.

**Doctrine 2 is about shape, not height.** "A curve that peaks in the middle is stronger evidence
than any single point" licenses reading a *sign pattern across doses*. It does not license
explaining the magnitude at one dose. I read a shape claim as a height claim because the shape
happened to be real (the tails do fall away) and that lent unearned credibility to the peak.

**And the replication was free.** A duplicate run — the dying session double-submitted the same four
arms 31 seconds apart — sat finished and uncollated on the VM. Doctrine 1 says re-running a
deterministic engine is worthless, and that is true of re-running *the same games*; it is emphatically
not true of **the same arms on a redrawn map sample**, which is the only cheap replication this
project has. Collecting an orphaned duplicate cost one command and overturned a published conclusion.
**Check `gauntlet-collect.sh --list` for uncollated runs before trusting any thin margin in the log.**

Corollary for the resume checklist: an unplanned duplicate run is not waste to be discarded, it is a
free independent sample. Collate it and pool it.

## 33. Distinguish a plateau from a peak before you claim an optimum (2026-09-08)

Seven reserve levels, ~700 games:

```
reserve      0    600   1200   1800   2400   3000   3600
vs null     -7     -3     +0     -1     +0     -3     -7
```

Iterations 24 and 25 each saw three points of this and each named a **peak** — iteration 24 put it
above 1200, iteration 25 put it at 2400. Both were fitting a maximum to a **flat middle**, where the
argmax is whichever arm caught the friendlier sample. With the tails measured on both sides, the
honest reading is a **plateau from ~1200 to ~2400 with symmetric falloff**, and inside a plateau
there is no optimum to locate — only a range that does not matter.

Two operational rules from this:

1. **A three-point ladder cannot tell a peak from a plateau.** It has one interior point, and one
   interior point above two lower ones is what *both* shapes look like. Do not name an optimum until
   the interior is sampled at more than one dose, on one shared sample.
2. **A flat middle with falling tails is itself the finding**, and a good one. It converts an
   unexamined constant into a validated one and closes the thread — which is worth more than the
   marginal accept I was chasing. Iteration 0 set `reserve = 1200` as "the 1000 a tower costs, plus
   a little"; it survives 25 iterations later not because it won but because it is bracketed.

**Why the plateau is flat, which is the transferable part:** a reserve is a knob on *how a budget is
split*. The iteration-24 spawn probe measured production as **chip-gated on 38–90% of early
tower-turns** — the budget itself is the binding constraint on most turns. Splitting a binding budget
differently moves nothing until the split gets extreme enough to break something, which is precisely
a flat middle with falling tails. **Before tuning an allocation parameter, check whether allocation
is the binding constraint; if the resource is gated, the whole allocation family will read zero** and
you can skip the ladder. This retires the reserve thread and points the next one at income.

## 34. No tournament-derived quantity measures MY bot — I learned this twice in ninety minutes (2026-09-08)

The tournament is the only measurement in this project taken against opponents my lineage did not
produce, which makes it feel like the authoritative instrument. It is not an instrument for
**attribution** at all, because the other two lineages accept iterations between every pair of
runs. Between two tournaments I compared, one sibling advanced **seventeen** accepted iterations.

I made the error twice in one session:

1. **The standings delta.** I read bob 92.3% -> 70.3% as "bob regressed 22 points". The report
   prints a commit per bot under *"What played"* and I read only my own line. The head-to-head
   deltas said it outright — one sibling +18.7 against me, the other −25.3 — and I had quoted those
   numbers without registering what they meant.
2. **The loss-shape.** Having just written the correction for (1), I reached for a *different*
   tournament statistic — the share of losses ending inside 500 rounds, 0.0% -> 17.4% -> 25.8% —
   and argued it was immune because *"a shape is more robust to opponent drift than a level."* Then
   I checked: 78% of my wins over `examplefuncsplayer` end inside 500 rounds versus 2.2% at r2000
   against `bob_iter0`. Round length is one of the **most** opponent-dependent quantities there is.

The second is the instructive one. The first was carelessness; the second was **motivated
reasoning wearing methodology's clothes**. I produced a general-sounding principle ("shapes are
robust") that I had never tested, applied it to exactly one case, and stopped. The tell was that
the principle appeared *at the moment it was needed* and was never checked against data I already
had on disk.

**The frozen rung settled it in one query and refuted my own hypothesis before the tournament ran.**
Against `bob_iter11`, which cannot change, the fast-loss share is flat at 16-23% across six builds —
and the regressed iteration 18 has the **lowest** at 7%. No early-collapse mode exists. I had a
mechanism ready to blame (`RUIN_FLOOR = 0` letting a soldier paint to exactly zero, where
`NO_PAINT_DAMAGE` applies and it cannot move) and it was going to be iteration 28.

**Operational rules:**

- **No tournament-derived quantity attributes anything to my bot.** Not standings, not
  head-to-head, not any distribution derived from them. Its role is **target selection** — a map I
  am swept on is a real weakness whoever caused it — and never attribution. That is narrower than
  the role I had been giving it.
- **When a comparison spans time, list everything that changed, not just my part.** The confound
  was printed in the report I was reading.
- **A methodological principle invented mid-argument is a red flag, not a defence.** If it is
  general, it was testable before I needed it; test it then, on data already held. Both times here
  the refuting data was already on disk and cost one query.
- **Reach for the frozen instrument first, not as a cross-check.** I own five frozen opponents
  precisely so that "did my change help?" has a clean answer, and I twice went to the confounded
  number first because it was the one in front of me.

## 35. A PRNG draw inside a conditional makes that conditional part of the behaviour (2026-09-08)

I added a conjunct to a spawn gate and called the zero-dose arm *exact*, having javap-confirmed that
the engine already asserts the condition I was adding. The reasoning was right about the engine and
wrong about the bot:

```java
if (chips >= want.moneyCost + reserve) {
    int start = G.rng.nextInt(8);      // consumed INSIDE the gate
    for (...) { if (rc.canBuildRobot(want, l)) { ... } }
}
```

`G.rng` is a per-robot `Random(rc.getID())`. A tower with chips but too little paint still entered
this block, still drew, and ran a loop that could spawn nothing. Narrowing the `if` skipped the draw
on exactly those turns and offset that tower's PRNG for the rest of the game. **The change was
neutral in outcome and catastrophic in sequence** — every later random direction differed.

**The rule: a PRNG is shared mutable state, so the set of turns on which you draw is itself
behaviour.** Adding, removing, or *re-scoping* a draw is never a no-op, however inert the guarded
code is. When adding a guard around code that draws, put the guard **after** the draw unless you
intend the desynchronisation. This generalises past PRNGs to anything with call-order-dependent
state.

**Corollary for reading old results:** any past iteration that narrowed or widened a condition
wrapping a draw carries the same contamination, and its measured effect is its mechanism *plus* a
PRNG reshuffle. Do not re-litigate old verdicts on this basis alone — but do not cite their margins
as precise either.

## 36. A mirror null's zero variance is STRUCTURAL — it is not evidence the instrument is quiet (2026-09-08)

Seven consecutive runs put my control arm at *exactly* 25/50 with all 25 maps split. I wrote, at
iteration 18, *"a zero arm measured at EXACTLY the null (25/50, **se = 0**, all 25 maps split)"* and
proceeded to treat 2- and 3-game deltas as signal.

**That zero variance was forced, not observed.** The control was byte-identical to the bot, so a
deterministic engine on a symmetric matchup *cannot* return anything but 25/50-all-split. It is a
wiring check on the harness. It is not a measurement of how much a **changed** arm's score moves for
reasons unrelated to its mechanism, and those are different quantities.

The distinction became measurable by accident. A voided arm differed from the bot **only** by PRNG
phase — no rule changed, no reachable outcome altered — and scored **19/50**, with swept maps going
from 0-against to 8-against. A behaviourally neutral change moved the instrument by 6 games.

Set against that band, my recent "results" — `-3`, `+2`, `-1`, `+0`, `-3` — are all inside it. That
is consistent with what the 400-game pooled replication already said (the effects were zero), and it
explains *why* the `+2` never replicated: it was never a +2 of anything.

**Rules:**
- **Never quote a mirror null as the instrument's standard error.** It bounds harness error, not
  measurement noise. Two different quantities were wearing the same number.
- **The noise floor for a CHANGED arm must be measured with changed arms**, not derived from a
  binomial formula that assumes coin-flips are the only source of variation. A deterministic engine
  is not a low-noise engine; it is a chaotic one with reproducible chaos.
- **Calibrate it directly**: run several behaviourally neutral, PRNG-desynchronised arms in one
  gauntlet and read the spread. Doctrine 9 has asked for this noise floor since day one and I have
  been supplying a formula where a measurement was wanted.
- Hold the finding to standard: the 19/50 is **one** draw. The logical half — zero variance under
  byte-identity is forced — needs no sample and is the part I assert.

### 36a. Refinement, same day: the binomial floor was right; the `se = 0` was the intruder

Looking at the voided PRNG-phase-only arm map by map:

```
arm swept  2 / 25      bot swept  8 / 25      split 15 / 25
```

A byte-identical mirror splits **25 of 25**. With only the PRNG phase changed, **10 of 25 maps stop
splitting** — which side wins is decided by seed phase, consistently across both sides. If each game
were an independent coin flip, 50% of maps would be swept by one side or the other; the observed 40%
is close to that, slightly under, as expected when the map itself favours neither side.

So the per-game outcome between policy-identical bots is **near a coin flip**, and the right noise
model is the ordinary binomial one: `n = 50`, `se = sqrt(50 x 0.25) ≈ 3.5 games`, so a **±7 band at
2 se**. That reframes 36 more precisely and slightly against my first reading of it:

- **The binomial noise floor doctrine 9 asks for was never the wrong tool.** I had it available and
  it gives the right answer.
- **What went wrong is that a second, incompatible number was in circulation** — the mirror null's
  `se = 0` — and I quoted whichever was nearer to hand. Two quantities wore the same name
  ("the null"), one forced by symmetry and one statistical, and the forced one silently won because
  it appeared in every run's output.
- **The 19/50 is a −1.7 se draw**, not an anomaly. I should not have implied it was surprising; it
  is exactly what a ±3.5 se instrument does one time in ten.

Against `se ≈ 3.5`, my logged results read: iteration 25's `+2` is **0.6 se**, iteration 24's `−3`
is **0.85 se**, iteration 26's spread is **0.3-0.85 se**. None was ever distinguishable from zero,
and the 400-game pooled replication that found exactly `+0` is what an honest reading predicts.

**The rule this leaves:** when two numbers in your workflow can both be called "the null", name them
apart and write down which one gates decisions. The failure was not a missing formula; it was a
collision of vocabulary that let a structural constant impersonate a statistical one. The queued
calibration is still worth running — its job is now the sharper question of whether the real spread
**exceeds** binomial, which would mean cross-map chaos is correlated and even ±7 is too tight.

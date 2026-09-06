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

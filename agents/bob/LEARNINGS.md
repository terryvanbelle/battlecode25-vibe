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

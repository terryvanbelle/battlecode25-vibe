# Battlecode Training Algorithm

A year-agnostic method for developing a world-class Battlecode bot through an
automated, evidence-driven iteration loop. It is a fresh synthesis of what two
predecessor projects (`battlecode22-vibe`, 128 iterations; `battlecode26-vibe`,
~195 iterations) proved out, discarded, or learned the hard way — not a copy of
either project's algorithm document. Where a rule below exists because
something specific went wrong before, the rule states the failure it prevents.

**Standing constraints for this project:** no bot implementations may be
downloaded from the web, and no post-mortems from the current contest year may
be read. Post-mortems from *other* years are fair game and should be read
early. This removes the external-benchmark instrument the 2026 project relied
on; the opponent pool below is designed to work without it.

---

## Phase 0 — Ground truth before strategy

Do these before writing any strategy code. Every one of them was either done
late in a prior project and regretted, or done early and repeatedly paid off.

1. **Digest the spec into `RULES.md`** — units, costs, cooldowns, vision/action
   radii, win conditions, tiebreakers, the communication mechanism, bytecode
   limits. Keep it updated as balance patches land.
2. **Probe the engine directly; never trust inference from behavior.** Decompile
   the game jar (`javap -c`), read vendored engine source where available, and
   write one-off probe bots for anything ambiguous. Prior projects resolved
   multi-iteration guessing threads in minutes this way. Periodically sweep the
   full `RobotController` API for methods the bot never calls — a whole game
   mechanic sat unused for 81 iterations once because the obvious methods were
   assumed to be the whole interface.
3. **Look for radius asymmetries** (one unit's action radius exceeding another's
   vision radius, and similar). These recur every year and are reliably
   exploitable.
4. **Build the match/replay infrastructure first**: a headless match runner that
   bypasses the Gradle daemon (raw `java` invocation cut per-game time from
   ~10–30s to ~2s in 2026), parallel execution, and a replay-to-text tool that
   can extract per-round metrics, per-unit indicator strings, and action/move
   traces. Cross-year post-mortems agree: infrastructure outranks early
   strategy work, and it rarely needs rewriting when the strategy does.
5. **Verify determinism.** Run identical code twice and diff game-by-game. Both
   prior engines were deterministic; this fact drives the entire measurement
   methodology below. If this year's engine is *not* deterministic, the
   dose-response rules below change — establish which world you are in first.
6. **Wire bytecode-budget monitoring into Iteration 0.** The limiter pauses a
   robot's turn mid-instruction silently — no exception. Compare the round
   number before/after each robot's own logic (confirmed overrun) and
   `Clock.getBytecodeNum()` against the type's limit (near-miss), and surface
   both in indicator strings. Check it on every full evaluation forever; a
   one-off "we have headroom" check goes stale as logic accumulates.
7. **Audit for play-symmetry from day one.** The single largest bug class either
   project found: any fixed absolute-order decision (iterating a `Direction[]`
   array in compass order, taking the first satisfying result from a sensing
   call whose scan order is fixed, hardcoded direction fallbacks, anything
   correlated with team identity) interacts with map geometry to give one side
   a compounding tempo edge. Audit new tie-break/default-direction code as it
   is written, and mirror-match periodically (bot vs. byte-identical copy on
   every map, both sides): a persistent lopsided split on a map is a real bug.
   Two cautions from experience: a *consistent* arbitrary preference can be
   supplying real formation cohesion that pure randomization destroys, so a
   "fair" fix can still be a net regression — measure it; and in a mirror,
   any inter-team stat difference is positional, not policy.
8. **Know the map contract.** Maps are guaranteed one of a small set of
   symmetries. Inferring which one holds (track observed terrain, eliminate
   hypotheses) and extrapolating the unseen half is standard practice among
   strong teams every year — plan for it rather than discovering its absence
   late.

## Iteration 0

Deliberately minimal: the smallest legal bot that moves a unit and writes
instrumentation into the replay, with bytecode monitoring already wired in.
Snapshot it, run it through the full evaluation, and let everything else grow
from the loop.

---

## The opponent pool ("the Gauntlet")

A set of opponents the current bot is evaluated against: every opponent × every
map in the pool × both sides (`2·B·N` games). With external bots off-limits,
the pool has three sources:

- **Frozen self-lineage.** Every accepted iteration is snapshotted
  (`src/g_iterN/`) and joins the pool. This is the regression suite.
- **Synthetic archetypes.** Bots we build ourselves to span the year's key
  strategic policy space (e.g. a pure rusher, a pure economy/turtle, whatever
  discrete strategic commitments this year's rules create). Build the simple
  poles early; they exist to answer "does our bot handle an opponent that does
  X" for X our own lineage never does. **Keep them synced**: archetypes forked
  from the bot's own code go silently stale and inflate win rates (this masked
  a 62.5% as 95.0% once). Automate the resync and make staleness loud.
- **Handicapped self-play** (optional): the current bot with a deliberate
  handicap (resource tax, unit cap) can serve as a tunable-strength sparring
  partner when the lineage is too young to provide peers.

**Classification.** Each opponent is a **peer** (current win rate ~30–90%) or a
**benchmark** (<30% — a target to close on, not noise). Benchmarks never gate
acceptance and are played less often; peers gate acceptance. Reclassify from
results: benchmark→peer at ≥30%; peer→benchmark after two consecutive
evaluations below 20%. Retire any opponent beaten ≥80% in two consecutive
evaluations; never retire an opponent we lose to.

**The self-referential blind spot.** Every instrument above descends from our
own code, so none can detect a weakness the whole lineage shares. The 2026
project only discovered several such weaknesses when independent bots arrived.
Without external bots, the mitigations are: archetypes deliberately built to
attack us in ways we don't attack ourselves; adversarial map selection (build
or select maps that stress untested situations); and epistemic humility —
absolute strength claims are unverifiable here, only relative progress is.

---

## Measurement doctrine

The accept/reject machinery lives or dies on these rules. Each one is paid for.

1. **Determinism means re-running is worthless.** Identical code produces
   byte-identical results, so a marginal result re-run yields zero new
   information. To probe a marginal effect, vary the *dose* (the mechanism's
   size/threshold) or widen the sample (more maps, more opponents).
2. **Dose-response, with a zero arm.** A parameter is only a dose if it changes
   the condition actually evaluated (verify — a "dose sweep" once produced
   byte-identical games because the parameter fed a check that never ran).
   Always measure the zero arm: a negative slope between two nonzero doses
   once wrongly condemned a low dose that beat zero handily; the curve was
   concave with an interior optimum. A curve that peaks in the middle is
   stronger evidence than any single point.
3. **Arm-to-arm identity check.** Before interpreting any comparison, count how
   many `(opponent, map, side)` games are byte-identical between the two arms.
   All-identical means the change never executed — this caught three "results"
   in one project that were the same bot measured twice.
4. **Rank instruments by matchup evenness, and check representativeness.**
   An instrument pinned near 0% or 100% cannot resolve a few games; an even
   matchup can. But resolution is not representativeness: an even instrument
   cannot measure a defense against a behavior its opponents never perform
   (a mirror proved a defensive feature "worthless" that was in fact worth
   several games against rushers, because the lineage never rushes). For any
   defensive feature, first check whether the evaluating opponents pose the
   threat at all.
5. **Primary accept test: head-to-head against the most recent accepted
   snapshot**, all maps, both sides. >50% means the candidate genuinely beats
   what it replaces — immune to archetype staleness and to mirror collapse.
   ~50% is a near miss, not an accept, absent a separate mechanistic argument.
6. **Peers are the regression check; lopsided instruments give direction
   only.** Never accept or reject on a lopsided instrument alone — both
   mistakes were made and both had to be walked back. A 1–2 game move on a
   lopsided instrument is noise; compute the binomial noise floor for each
   instrument's sample size and distrust any delta under it regardless of how
   good the story is.
7. **Diff game-by-game and read the diff's shape.** Scattered, mixed-direction
   flips (especially on maps known to be chaos-sensitive) are churn. Flips
   that are one-directional, or concentrated on one map/side across many
   opponents, are a real causal effect — reproduce and trace before deciding.
8. **Normalize per round before comparing counters.** Every replay counter
   scales with game length; a change that makes games longer reads as "worse"
   on raw counts.
9. **Track a fixed old-bot roster for long-run progress.** Peer retirement
   makes the peer rate a poor absolute yardstick (stable rate = no progress,
   or progress against a hardening roster). Every ~5 accepted iterations,
   run against a fixed, never-retired roster composed of every 5th accepted
   snapshot (iter1, iter5, iter10, ...) and chart it. Add each new
   multiple-of-5 snapshot to the roster as it appears rather than replacing
   older entries — the value is in each line's long-run trend. On thin accept
   margins, run this *before* accepting, not after — it once caught a bad
   accept by ten games when the two pre-registered metrics had each moved by
   one.
10. **Don't let pre-registered metrics decide when a cheap unrun instrument
    could reverse them.** A real effect big enough to accept on usually shows
    up in more than one place.

---

## The iteration loop

Hyperparameters (starting values; revisit only with evidence):

| name | value | meaning |
|---|---|---|
| `WinPct` | 60% | peer win rate required to accept |
| `NearMissMargin` | 5 pts | below `WinPct` that still permits refinement |
| `MaxNearMissRefinements` | 3 | extra refinements for a near-miss solution |
| `MaxHypothesisIterations` | 10 | hypothesis attempts per losing game |
| `MaxSolutionsIterations` | 10 | solution attempts per verified hypothesis |
| `MaxConsecutiveRejects` | 3 | rejects before the next attempt must change area |
| `BenchmarkEvery` | 3 | evaluations between benchmark runs |
| `ReproSampleSize` | 8 | peers in the cheap pre-Gauntlet sample |

### 1. Select a target

Pick a losing game from the last evaluation — or invoke the structural track
(below). Two selection disciplines:

- **Don't sample only losses.** "We're behind on metric X in our losses" is
  near-tautological when X is a scoring term. Trace wins too, and prefer
  absolute degeneracy signals ("our bot stalls at round N", "resource pinned
  in a dead band") over opponent-relative comparisons — a stall needs no
  opponent to be wrong.
- **Track functional areas, not just games** (visibly, in `TRAINING_LOG.md`).
  A string of rejects concentrated in one area must be recognized as a closed
  thread, not diffuse bad luck. After `MaxConsecutiveRejects` in one area, the
  next attempt must leave it.

### 2. Trace, don't theorize

Read the actual replay (metrics, indicators, action traces) before forming a
hypothesis. Nearly every serious root cause in ~320 combined iterations was
found in a trace, not by reasoning about what a good bot would do — and traces
routinely killed plausible hypotheses before they cost an iteration.

### 3. Hypothesis, with three cheap pre-checks

State the hypothesis with pre-registered variables and thresholds that would
verify it, instrument if needed, and re-run the motivating game. Then, before
building a solution:

- **Reachability.** Is the branch this reasoning lives in ever taken? Check
  gate values against the actual observed ranges of the quantities they test
  (a resource gate above the treasury's equilibrium band is dead code). A
  correct chain of reasoning about a dormant branch predicts nothing — this
  burned three iterations in one day once. Also read the *guard you are
  nesting inside*: a new clause added under an outer condition that already
  excludes the targeted case can never fire.
- **Trigger frequency.** Check how often the triggering condition fires across
  *other* recent games, not just the diagnosed one. "Helps the diagnosed case,
  hurts broadly" is a recognizable failure shape: conditions that look narrow
  on one replay are often common everywhere.
- **Generality.** Verify the hypothesis on at least one other losing game
  (different opponent/map preferred). Shared symptom ≠ shared root cause.
- **History.** If a prior iteration deliberately established the behavior this
  would change, the fix must supersede that reasoning with new evidence, not
  silently revert it.

### 4. Implement and mechanistically verify

Small, isolated changes; never bundle (a bundled result is uninterpretable).
Re-run the motivating game and classify:

1. **Won** — proceed.
2. **Still lost, but the mechanism demonstrably engaged as designed, with a
   specific evidenced account of why this game couldn't flip anyway** (e.g.
   opponent's scale advantage exceeds the fix's marginal effect) — a valid
   basis to proceed; many of the best accepted iterations took this path. Log
   both halves.
3. **No evidence of engagement** — discard or fix; don't evaluate further.

Two verification caveats: a mechanistically-correct feature can be a no-op
because upstream state never produces the situation it handles (check "does
this ever engage" before concluding it doesn't work — and note it may become
valuable later when upstream changes); and if the change alters who draws on
any shared/capped team resource (a build cap, a shared treasury, comm slots),
instrument the pool itself in the first run — three iterations once failed
identically because a global cap, visible in the data the whole time, was
never printed.

### 5. Staged evaluation

1. **Cheap reproduction sample**: `ReproSampleSize` peers, all maps, both
   sides, diffed by shape against the baseline. An unambiguous real regression
   here kills the change without spending a full run. A *clean* sample does
   not skip the full run — real regressions in production-priority and
   resource-threshold changes have been invisible at small scale repeatedly.
2. **Full Gauntlet** + head-to-head vs. the last accepted snapshot.
3. **Accept** if the head-to-head clears 50%, peer `WinPct` is met, and the
   diff shows no unresolved one-directional regression. Snapshot; this run
   becomes the new baseline.
4. **Near miss** (within `NearMissMargin`, no real regression): refine the same
   solution, up to `MaxNearMissRefinements` — several good ideas cleared the
   bar only after a parameter refinement of a directionally-correct mechanism.
5. **Reject**: trace the flipped games. A specific, well-understood failure
   mode earns one targeted refinement; otherwise revert fully and select a new
   target. A rejected attempt that converts a weakly-founded belief into a
   firmly-founded one paid for its run.

Design preference discovered independently in both projects: **self-calibrating
thresholds beat fixed constants** for opponent-variable behavior. When a fixed
threshold repeatedly trades one opponent's gain for another's loss, derive the
threshold from in-game observation instead of searching over more constants.

### 6. Post-accept routine (atomic, every time)

Update progress charts and the fixed-roster history, archive one representative
replay into `replays/` (named `iterNN_<opponent>_<map>_<side>`, prefer the most
informative win), and commit everything in the same commit as the accept
decision — staging explicit paths, never `git add -A` (which twice nearly
baselined unverified code). Every one of these lapsed for 10+ iterations at
some point when treated as "later"; the routine exists because later never
comes. Label any history CSV rows with the build that actually played, not the
latest snapshot directory name.

---

## When the loop stalls

**Never idle.** There is no valid state where nothing is being attempted.
Waiting on a running evaluation is execution, not idling; finishing a search
and stopping is not an acceptable outcome. In order of preference when stuck:

1. **Ablate accepted features.** Gate each carried feature off, run the
   head-to-head/mirror, and measure its true current value. A 2026 audit found
   the two most valuable features were failure-mode preventers accepted almost
   incidentally, the headline-accepted features were worth ~0, and one was
   negative. One cheap run per feature; historically it found more real
   corrections than invention did. (Respect representativeness: an ablation on
   opponents that never pose the relevant threat proves nothing — see
   Measurement doctrine #4.)
2. **High-risk structural exploration** — a first-class track, not a fallback.
   Name a capability gap or strategic difference versus a strong opponent (not
   necessarily traced to one game), implement at whatever scope it needs, and
   verify with full rigor. The highest-value accepts in both prior projects
   came from this track. A rejected structural attempt is a normal outcome.
3. **Re-read the cross-year research** (prior-year post-mortems, the perennial
   mechanics: symmetry inference, comms schema design, hybrid bug-nav,
   micro-over-macro, rush/turtle map-adaptivity).
4. **Consider a from-scratch rewrite** of the bot on the same infrastructure —
   the 2020 champion's advice when a strategy has stopped moving, and cheaper
   than it looks.

**Maintain a closed-directions ledger** in `TRAINING_LOG.md`: each closed
avenue with the measurement that killed it. Re-opening is legitimate only with
a specific reason the recorded cause no longer applies (this correctly
re-opened two directions in 2026 — one became an accept; the other converted a
weak rejection into a firm one). "Feels under-explored" is not a reason.

Watch for the deep regularities the ledger tends to fill with: metrics that
improve without converting to wins (five mechanism-verified damage increases
converted to nothing in 2026); survival bought with inactivity (halving the
death rate cost 18 peer games — units die doing the thing that wins); and the
recurring winner's profile: **capability preserved at zero marginal cost**
(standing defenses, spending idle resources, removing pure waste).

---

## Logging

`TRAINING_LOG.md` is the append-only chronological record: every iteration
(accepted, rejected, or void) with its hypothesis, pre-registered variables,
measurements, decision, and what was learned. Rejections are data. A fresh
session must be able to resume mid-iteration from the log alone. Keep the
functional-area map and closed-directions ledger current inside it, and
periodically distill durable lessons into a `LEARNINGS.md` organized by theme.

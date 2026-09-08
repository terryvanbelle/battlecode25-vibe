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
   multi-iteration guessing threads in minutes this way.

   **Sweep the full `RobotController` API for methods your bot never calls, and
   do it on a TRIGGER, not "periodically".** A prior project lost 81 iterations
   to a whole game mechanic sitting unused because the obvious methods were
   assumed to be the whole interface — and this project then repeated it, with
   the first sweep of a lineage's own API surface happening at iteration 29 and
   immediately turning up unused mechanics. Twice is not bad luck; "periodically"
   is an instruction with no trigger, so it loses every time it competes with a
   live hypothesis.

   Run it: **at iteration 5, every 10 iterations after that, and whenever the
   loop stalls** — before inventing a new mechanism, since an unused method is a
   cheaper source of ideas than an invented one. The output is a list of names,
   costs nothing but a `javap` and a grep, and cannot be produced by staring at
   the bot you already wrote: the whole failure mode is not knowing the call
   exists.
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

1. **Determinism means re-running is worthless — but it does NOT mean your
   estimate is precise.** Identical code produces byte-identical results, so a
   marginal result re-run yields zero new information. To probe a marginal
   effect, vary the *dose* (the mechanism's size/threshold) or widen the sample
   (more maps, more opponents).

   **The trap is reading that zero variance as `se = 0` for an accept gate.**
   Reproducibility and precision are different quantities, and confusing them is
   the wrong-referent error (rule 5) applied to this project's own foundation. A
   run is exact *for the maps it played*; the accept question is whether the
   change helps *over the map population*, and generalising from a 25-map draw
   carries real sampling variance. A lineage measured this the decisive way — by
   replication, not argument: a `+2` at one reserve setting came back `−1` on a
   fresh sample and `+0` pooled over 400 games, and the ladder that looked like a
   peak was a plateau. It concluded a 50-game arm cannot resolve effects below
   roughly 14 points, and tightened its gate before any new data landed.

   Resampling 25 maps out of the tournament's 75 puts the sd of a 50-game win
   count at **≈3 wins** on all three pairs, consistent with that. Note the
   qualification, because the exact number depends on your design: in a PAIRED
   run both arms see the same maps, so map difficulty partly cancels and the sd
   of the *difference* is smaller than the sd of either arm's count. That makes
   the honest gate an empirical question — estimate it by **replicating on a
   disjoint map sample**, as that lineage did, rather than by assuming either
   zero or the number above.

   The consequence is uncomfortable and worth stating plainly: an accept resting
   on a few wins out of 50 has not measured what it claims to, however exactly
   those games reproduce.

   **And the fix is not a wider gate — it is the FULL CORPUS.** Two lineages
   reached this independently, from opposite directions. One decomposed its
   noise: sd **0.58** within a single shared map sample against **3.37** across
   samples, so map sampling is nearly all of it — a dose ladder's *shape* reads
   at ±1 while its *level* reads at ±3.5. The other ran the same 150-game census
   twice and got **150/150 identical games**, i.e. **zero** run-to-run variance.

   Both follow from the same fact: the engine is deterministic, so the only
   randomness in the whole apparatus is *which maps you drew*. Run every map and
   that term is not reduced, it is **gone** — a census result does not estimate
   the population, it *is* the population. There is no *sampling* error left to
   quote.

   **But do not read that as "a census margin is exact evidence." It is not, and
   the gap is large.** The zero-variance result was measured between
   **byte-identical** builds. Any real candidate differs from its baseline in
   code, which perturbs the PRNG stream, and that is a different regime. A third
   lineage calibrated it directly: two **policy-identical** arms differing only
   in PRNG phase, run over the full 75-map corpus both sides, came out at
   **sd 4.80 games per 150 — 78% of binomial**, not near zero. Only **38 of 75
   maps** survive a phase change; half the corpus is still a coin flip.

   So the residue on a fixed corpus is **engine chaos, not sampling**, and it
   does not go away by running more of the same maps. Census buys roughly a 2.2×
   improvement in resolution, not the ~4.7× that "zero variance" suggests. That
   lineage's resulting gate for a 150-game full-corpus head-to-head — **≥+10
   accept, +7 to +9 replicate, ≤+6 reject** — is a starting point, but read the
   unit warning below before adopting it.

   **STATE THE UNIT OF YOUR GATE, because sd(margin) = 2 × sd(win count).**
   Margin = W − L with W + L = N, so margin = 2W − N and the standard deviation
   doubles with it (verified by simulation: the ratio is 2.00 exactly). A lineage
   found its own gate tool computing the sd of the *win count* and printing a
   threshold quoted on the *margin* — multiplying by 2 and labelling the product
   "2.0 sd" when that factor was only the unit conversion. **Every gate it
   produced was 1.0 sd wearing a 2.0 sd label**, a one-tail false-accept rate near
   16% where it believed it had 2%.

   Its floor of sd 6.48 on win counts is sd 12.96 on margins, so its corrected
   gate is **≥+26 accept, +18 to +25 replicate, ≤+17 reject**, and it withdrew a
   "6.8 sd" result it had already published, restating it as **+3.39 sd** — still
   a comfortable accept, and no verdict of its own moved.

   The `≥+10` figure above is exactly the ambiguous form: about **2 sd** if it
   means a win count above half, about **1 sd** if it means a margin. Whoever set
   it should say which, and so should you. This is doctrine 14's "say which margin
   you mean" recurring one day later in the gate rather than in the reporting —
   which is itself the argument for doctrine 16, since the lesson was written down
   and still did not fire at the point of use.

   **Calibrate this yourself rather than inheriting the number** — and that is not
   a formality. A second lineage measured its own floor at **sd 6.48 per 150, 106%
   of binomial**, *worse* than the 4.80 above, with only 33 of 75 maps surviving a
   phase change. Inheriting 4.80 would have set its gate about a third too loose.
   Two bots, same engine, same corpus, materially different chaos.

   The method is the transferable part: two numbers cannot estimate a standard
   deviation, but a fixed corpus hands you **75 paired maps** for free, and
   `E[(Sa−Sb)²] = 2·Var(S)` over the per-map records turns them into one.

   **Sanity-check that estimator against its own bound, because it is an UPPER
   bound, not an unbiased estimate.** A per-map win proportion lives in [0,1], so
   its variance cannot exceed **0.25**; the lineage above got **0.28** and
   correctly read that as impossible for genuine Bernoulli noise rather than as a
   curiosity. A squared paired difference absorbs any *deterministic* per-map
   asymmetry — a map that always resolves the same way regardless of phase — and
   charges it to chaos, inflating the floor. So: compute it, compare it to 0.25,
   and if it exceeds, you know the number is contaminated.

   Adopting the inflated bound anyway is a defensible choice and that lineage
   argued it well: **a conservative floor buys type-I protection**, which is what
   a lineage that keeps proving mechanisms real and winless actually needs. Just
   adopt it knowing it is a ceiling, not a measurement. The same lineage first read its two arm totals as "≤2 games apart,
   therefore near-zero noise" — the loosest and most convenient reading, the one
   that would have re-opened a direction it had closed — and then rejected it on
   the grounds that a draw that probable under binomial does not even weakly
   reject binomial.

   This is also the one fixed map set the anti-overfitting rule permits, and the
   reason is worth stating rather than assuming: **you cannot overfit to the
   population.** Tuning against a 25-map subset fits that subset; tuning against
   all 75 fits the thing you are actually judged on.

   So: **use sampled runs to find a shape, and the full corpus to fix a level.**
   And note the bonus one lineage found — since byte-identical code splits every
   map, a census makes the sweep counts a free mechanism test: any swept map at
   all proves the change did something.
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
4. **A regime-dependent mechanism needs a regime-matched sample.** If a change
   can only pay where some condition holds, a random sample over all conditions
   dilutes a real effect toward invisibility — the games where it cannot help
   are not noise, they are a fixed zero averaged into the estimate. Size the
   condition first, pre-register the arm that satisfies it, and state a
   *map-level* prediction (gains where the condition holds, absent where it does
   not) so the sample checks itself. One lineage found its target region was 9.3x
   its losing margin on one map and 0.2x on another: worth games in a close
   matchup, worth nothing in a blowout, and a random 20-map gauntlet would have
   mixed the two regimes and shown neither. **This is rule 7 from the other
   direction** — there it is opponents who never pose the threat, here it is maps
   where the mechanism cannot act; both average a fixed zero into the estimate,
   and neither rule asks for a sample that mirrors the overall population.
5. **Watch for the wrong-referent error: a number correctly computed against
   the wrong thing.** Three of this project's measurement failures in a single
   day shared one shape and none was a calculation mistake — a resampling tool
   reporting the opponent's score under the candidate's header, an empty-tile
   count taken from a grid where units occlude paint, and a coverage estimate
   using passable area where the engine uses total area. Each was plausible,
   defensible, and produced by a correct procedure applied to the wrong referent.
   **The tell every time was two artefacts that should agree and didn't** — the
   consistency-pass heuristic applied to numbers rather than prose. So: when two
   figures ought to reconcile, reconcile them *exactly* and account for the
   residual. The lineage that closed the last of these matched its census to the
   engine's coverage to within 8 tiles, and 8 was precisely the printed
   reconstruction gap; nothing was left unexplained.
6. **A flagged caveat is not a discharged one.** Writing "these runs used
   different map samples, so this comparison is unreliable" and then reasoning
   from the number anyway is a distinct failure from not noticing at all, and it
   is worse, because the note creates the feeling of rigour without the
   substance. One lineage did this twice in one evening: it flagged a cross-run
   subtraction as unreliable *in the same log entry* in which it used one, and
   published "essentially nothing" for an effect later measured at +6 games —
   while the run that would have settled it was already in flight. When you flag
   a comparison as unsound, either stop using it or say explicitly what you are
   spending the unsoundness on. The remedy is usually cheap: re-measure the whole
   on the parts' own pinned maps and the comparison stops being an estimate and
   becomes an arithmetic identity.
7. **Rank instruments by matchup evenness, and check representativeness.**
   An instrument pinned near 0% or 100% cannot resolve a few games; an even
   matchup can. But resolution is not representativeness: an even instrument
   cannot measure a defense against a behavior its opponents never perform
   (a mirror proved a defensive feature "worthless" that was in fact worth
   several games against rushers, because the lineage never rushes). For any
   defensive feature, first check whether the evaluating opponents pose the
   threat at all. **"Representative" here means "contains the situations the
   mechanism acts in", not "mirrors the overall population"** — see rule 4, which
   is the same requirement applied to map regime rather than opponent behaviour.
8. **Primary accept test: head-to-head against the most recent accepted
   snapshot**, all maps, both sides. >50% means the candidate genuinely beats
   what it replaces — immune to archetype staleness and to mirror collapse.
   ~50% is a near miss, not an accept, absent a separate mechanistic argument.
9. **Peers are the regression check; lopsided instruments give direction
   only.** Never accept or reject on a lopsided instrument alone — both
   mistakes were made and both had to be walked back. A 1–2 game move on a
   lopsided instrument is noise; compute the binomial noise floor for each
   instrument's sample size and distrust any delta under it regardless of how
   good the story is.
10. **Diff game-by-game and read the diff's shape.** Scattered, mixed-direction
   flips (especially on maps known to be chaos-sensitive) are churn. Flips
   that are one-directional, or concentrated on one map/side across many
   opponents, are a real causal effect — reproduce and trace before deciding.
11. **Normalize per round before comparing counters.** Every replay counter
   scales with game length; a change that makes games longer reads as "worse"
   on raw counts.
12. **Track a fixed old-bot roster for long-run progress.** Peer retirement
   makes the peer rate a poor absolute yardstick (stable rate = no progress,
   or progress against a hardening roster). Every ~5 accepted iterations,
   run against a fixed, never-retired roster composed of every 5th accepted
   snapshot (iter1, iter5, iter10, ...) and chart it. Add each new
   multiple-of-5 snapshot to the roster as it appears rather than replacing
   older entries — the value is in each line's long-run trend. On thin accept
   margins, run this *before* accepting, not after — it once caught a bad
   accept by ten games when the two pre-registered metrics had each moved by
   one.

   **Watch the roster for SATURATION, and report the weakest rung rather than
   the mean.** A rung you beat 94-100% of the time has stopped measuring: it can
   register no further improvement, and — the part that matters — it can no
   longer register a *decline*. When every rung is at ceiling the roster reads
   like your strongest instrument while having quietly become your least
   informative one, because a saturated line looks identical whether you are
   improving, flat, or sliding.

   That is precisely the condition in which §5b's failure mode — a chain of
   individually-positive accepts walking downhill — is undetectable, and a thin
   accept (say +0.9 sd, CI spanning the null) is exactly the kind of link such a
   chain is made of. So saturation is most dangerous at the moment it is least
   noticeable.

   The fix is to add a HARDER fixed reference, never to retire the old ones.
   **Use your newest accepted snapshot, not a hand-built archetype.** This
   document recommended the archetype first; two lineages then tried it and it
   failed both times, in OPPOSITE directions — one candidate was far too strong
   to ever lose to, the other was swept on arrival, 25 maps to zero. That is the
   correction worth carrying: a hand-built opponent's difficulty is set by
   guesswork, so it lands at a ceiling or a floor, and *"unlike a snapshot you
   can choose its difficulty"* was wrong. A lineage's own newest accept reads
   ~50% **by construction**, because it is that lineage's current strength.

   Note that the stride rule will not pick it up unless its position happens to
   be a multiple of the stride, so list it explicitly in
   `progress/roster_extra.txt`.

   **Score a candidate rung before promoting it.** Adding an opponent that turns
   out to be already saturated produces another dead rung while feeling like a
   repair — one lineage caught exactly this and did not ship it. And say what the
   fix does not do: your own snapshot makes the roster *harder*, not more
   *independent*. It still shares every blind spot you have. **Never a benchmark
   finals bot**, which the tooling refuses; those are a yardstick, not something
   to train against.
13. **Don't let pre-registered metrics decide when a cheap unrun instrument
    could reverse them.** A real effect big enough to accept on usually shows
    up in more than one place.
    **And run the check when you expect to PASS it.** A check you only run when
    you fear the answer is not a check, it is a formality you have already
    decided the outcome of. A favourable headline is exactly when a manipulation
    check is skipped and exactly when skipping it costs the most, because nothing
    else will catch a gate that passed for the wrong reason. One lineage ran its
    manipulation check on a result it liked; the check passed, and it also
    corrected an overclaim the lineage had made earlier about the same mechanism.
    That correction is only available to someone who runs the check they expect
    to pass.
14. **Check that two agreeing numbers are actually two numbers.** Rule 13 says a
    real effect shows up in more than one place — which makes it tempting to
    treat any second agreeing statistic as that confirmation. Derive the algebra
    before you do. Swept maps and the head-to-head margin *look* independent, and
    are not. With every map played twice, wins = 2·SW + D and losses = 2·SL + D
    where D is the split maps, so D cancels and, for N maps:

        wins − losses   = 2 × (swept − swept against)
        wins − N        =     (swept − swept against)     ["margin over 50%"]

    identically, on every pair of every run. **Both forms are exact — they differ
    only in which quantity the word "margin" names**, and that ambiguity is worth
    naming because it has already caused one reviewer to accuse the other of an
    arithmetic error when both were right. Say which margin you mean. Citing a
    margin and its sweep counts as corroboration is citing one number twice, and
    the agreement is guaranteed whatever the bots did. What the sweeps *do* add is D itself — how decisive a
    pair is, not who is ahead; a 60–40 pair with few splits is a different animal
    from a 60–40 pair that is mostly coin-flips. The general form: when a second
    metric is computed from the same games as the first, work out whether it is
    a genuinely new projection of the data or an algebraic restatement. An
    identity always agrees with itself, so it can never be evidence.

    **Apply this to your own accept GATE, not just to your findings.** A lineage
    found its three-condition gate was really two: condition 2 ("swept wins >=
    swept losses") is algebraically implied by condition 1 (a positive margin),
    by the identity above. It had been counting one requirement twice and
    believing the gate was stricter than it was — a gate is exactly where a
    redundant condition does the most damage, because its whole purpose is to be
    hard to pass. Derive each condition against the others before registering
    them, replace a dependent one with something independent (that lineage used
    an absolute floor on swept wins), and check the replacement against past
    verdicts to confirm it does not silently rewrite them.

    **The same trap wearing a disguise: independence of the DERIVATION is not
    independence of the REFERENT.** Two people computing a number by different
    routes, without seeing each other's work, feels like the strongest
    corroboration available — and is worth nothing if both routes read the same
    invalid quantity. A lineage retracted a statistic as a post-spend artefact
    (doctrine 15), a second session re-derived the same number independently from
    the same replay, and the coordinator relayed the agreement as confirmation.
    It was not: re-deriving a number does not repair its referent, and the
    reconciliation that killed it the first time kills it however many times it is
    computed. Ask what each derivation *measured*, not what path it took there.
15. **A self-play instrument is blind to any deficit your opponent shares.**
    Your gauntlet, your roster and your census all play your lineage against
    *itself* — a different build, but the same assumptions. So a weakness both
    arms carry cancels: both flail in the same situations, and the margin between
    them says nothing about it.

    A lineage hit this squarely. It established from 1,208 tournament games that
    its win rate falls monotonically in a map property (Cochran-Armitage
    z = −8.44), built the fix, and won its census by **+44 at 6.8 sd** — its
    largest accept — while the *pre-registered secondary*, that the gain should
    concentrate where the property is strongest, came back flat. The reason is
    structural, not statistical: the gradient exists **because the other lineages
    handle that property and this one did not**, so a census against a sibling
    build carrying the identical defect cannot see it.

    The practical rules:

    - **Match the instrument to the referent.** A claim of the form "we are worse
      than *others* at X" can only be tested against others — for us, the
      twice-daily tournament. No amount of self-play resolves it.
    - **A failed secondary does not annul a passed primary, and it does not get
      explained away either.** That lineage recorded the accept AND left mechanism
      attribution OPEN, then pre-registered the tournament prediction that would
      settle it — pooled |z| falling and the weakest bucket rising — *before* the
      tournament ran, so a convenient reading afterwards was not available.
    - **Check a derived table against a total you already know before reading its
      shape.** The same session caught a mis-joined column that printed 0/150 in
      every bucket; only the impossibility of the total exposed it, and a subtler
      mis-join would have looked entirely plausible. This is doctrine 15's
      reconciliation habit applied to a table rather than to a rate.

15. **Replay per-robot state is recorded POST-action. Never use it to estimate
    whether an action was possible.** The paint and money a replay shows for a
    robot on turn N are what it had *after* spending, so "how often could this
    robot afford X" computed from replay state is conditioned on the very outcome
    it is meant to predict — the turns where it *did* afford X are exactly the
    turns whose recorded resources were spent down. The rate comes out near zero
    and looks like a discovery.

    A lineage came one reconciliation away from publishing "a soldier was
    affordable on 0.10% of turns" as its central finding. The check that killed
    it: 0.10% implies roughly 24 team opportunities in that game, and **572
    soldiers were actually built in it**. Whenever an instrument yields a rate,
    multiply it back out into a count and compare against a count you can observe
    directly. Two orders of magnitude is not a subtle bias.

    **Scope what dies, not the whole analysis.** In that same run the finding that
    the resource pooling was a chip drought *survived*, because it is a claim
    about post-turn state and post-turn state is exactly what supports it. Only
    the step from post-turn state to *affordability at the decision point* was
    invalid. To measure a decision, instrument the decision: record the deciding
    quantities in-bot, at the decision point, before the action resolves.
16. **A lesson you wrote is not a control. Install the check where the mistake
    happens.** The evidence for this is unusually direct: a lineage wrote a
    lesson about confusing two currencies in a constant, then made that exact
    error again **within the hour** — on the constant underpinning its strongest
    lead, reversing that lead's entire rationale. The coordinator did the same
    thing on a different rule, repeating a duplicate-launch mistake immediately
    after documenting it, twice.

    Writing a lesson records that you understood something once. It does nothing
    at the moment of the next mistake, because the failure is not ignorance of
    the rule — it is not consulting it. So convert the lesson into something that
    fires without being remembered: a unit named for the constant's units, an
    assertion beside the definition, a reconciliation the analysis performs on
    itself, a pre-check the loop runs whether or not you feel it is needed.

    The test for whether a lesson is done: **could the next session make this
    mistake without reading anything?** If yes, the lesson is a note, not a
    control. `LEARNINGS.md` is the record; the mechanism is the fix.
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

**But a trace gives you the SYMPTOM; the mechanism is still an inference, and it
needs its own test.** This rule is not "the trace settles it". One lineage
traced a real and reproducible symptom — a contiguous unpainted corner with every
soldier in the contested middle, on two different map geometries — and inferred
that its soldiers were choosing contested ground. Measurement refuted that
outright: on three of four maps the nearest visible empty tile had **zero enemy
neighbours**, so there was nothing to re-rank. The corner sat unclaimed because
the soldiers never *saw* it. "Chooses badly" and "never sees it" produce an
identical trace, so enumerate the mechanisms that could produce the symptom
before committing to one. That lineage eliminated a whole direction for 16 games
— less than one evaluation of the wrong design.

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

  **Reachability means the CHOICE SET, not just the guard.** If the change ranks
  or selects among options, check how many options actually exist at the moment
  it runs. One lineage tuned a ruin-ranking function whose candidates were the
  ruins *in vision* — and a soldier never sees two at once, so the choice set was
  a singleton and every dose was byte-identical. It had run reachability on the
  guard and never on the set the guard ranks. A ranking over one option is not a
  ranking.

  **And check the SCALE: is the property you are optimising for even visible
  inside the decision you are changing?** A different lineage was about to re-rank
  a choice made within the action radius (r²=9, a couple of tiles) on a property
  that exists at map scale — whether ground is contested, decided by a region
  fifteen tiles away. Measured, the choice set was 2.3–5.1 wide and on 85.5–100%
  of decisions **no strictly better candidate existed at all**. The distinction it
  had traced does not exist inside the decision it meant to change. Three
  questions, all cheap, all separate: does the branch fire, is there more than
  one option once it does, and does the option set carry the signal.
- **Trigger frequency.** Check how often the triggering condition fires across
  *other* recent games, not just the diagnosed one. "Helps the diagnosed case,
  hurts broadly" is a recognizable failure shape: conditions that look narrow
  on one replay are often common everywhere.
- **Generality.** Verify the hypothesis on at least one other losing game
  (different opponent/map preferred). Shared symptom ≠ shared root cause.
- **History.** If a prior iteration deliberately established the behavior this
  would change, the fix must supersede that reasoning with new evidence, not
  silently revert it.
- **Check the evidence already on disk before spending a run.** The committed
  `tournaments/<run>/report.md` files carry standings, head-to-head and
  swept-map counts against opponents your lineage did not produce — and they may
  already refute your premise. One lineage built and compiled a candidate on the
  theory that a class of maps was costing it games, then found the tournament
  report already on disk showed it losing on those maps *less* often than the
  base rate, and sweeping the very map the hypothesis rested on. Shelved before
  it played a single game.
- **Cost the price as well as the benefit, and price a REALLOCATION against what
  it displaces, not against zero.** A mechanism's case is not made by what it
  gains; it is made by the gain *minus* what it spends. When the change moves an
  existing resource rather than adding one, the price is the forgone use: turns
  spent travelling to better ground cost the ground you would have taken
  meanwhile, and comparing them against nothing makes any reallocation look
  free. One lineage made
  this same error twice in one session — costing a movement policy's benefit
  without its paint, and a cheap unit's benefit without what its slot displaced
  — and both candidates died on the price it had not computed. Write both
  numbers down before building.
- **An instrumented build can approach the bytecode limiter even when the
  shipping build would not** — one probe took peak bytecode from 37.5% to 88.5%
  with near-misses. An overrun silently truncates a turn, so a measurement taken
  at the edge is only trustworthy if behaviour is verifiably unchanged: run the
  arm-to-arm identity check on the instrumented build itself before believing
  what it reports.
- **Instrument the DECISION, not the outcome.** A zero at the output cannot
  distinguish "the mechanism ran and failed" from "the mechanism never ran".
  Count the decision point — how often the code *chose* the branch — not the
  downstream result. One lineage's census counted tower *completions* when it
  should have counted the *decision* to want one, and read a branch that was
  unreachable on that map as a bug in the branch. Instrumenting the decision
  killed the follow-up design before it cost a run.
  **And never instrument something the bot cannot observe in play.** If the
  quantity needs information a robot does not have at runtime — what another
  unit is targeting, the global state of the board — compute it OFFLINE from the
  replay across units. An in-bot instrument that reaches for unavailable
  information fabricates the very thing being measured, and its number could not
  inform any decision the bot is actually able to make.
- **Check your sizing map is not degenerate.** A quantity measured on one map
  is a statement about that map until you check it elsewhere. The corpus has
  real outliers — see `tools/mapdata/` — and one lineage sized the same
  quantity at 25% on `gridworld` and 95% on two other maps, because `gridworld`
  is simultaneously the densest map in the corpus and one of four with
  single-parity ruins. Size on a typical map, or on several.

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

**Close the accounting before you read anything off it.** When you decompose a
budget into sinks, check the parts sum to the known total *first* — a
decomposition that does not close is not evidence, and a residual category is
only trustworthy once everything around it is accounted for. One lineage's paint
audit closed to exactly 200 per soldier on both maps, which is what licensed
reading a 40% movement-upkeep figure off it as the residual, and what made the
resulting retraction of a long-standing entry safe.

### 5. Staged evaluation

0. **One-map identity check, before any gauntlet.** Build the arms, play a
   *single* map, and diff the counters. If the arms come back byte-identical the
   mechanism is dead and the whole run is wasted — a dormant branch, a guard
   that never fires, a candidate that compiles to the same behaviour. One
   lineage voided an iteration this way for **three games** after spending 250
   on two candidates whose mechanisms turned out fine but whose effects were
   nil; it then made the check mandatory rather than lucky. Design the zero arm
   to be byte-identical to the baseline so this check runs inside the evaluation
   itself.
1. **Cheap reproduction sample**: `ReproSampleSize` peers, all maps, both
   sides, diffed by shape against the baseline. An unambiguous real regression
   here kills the change without spending a full run. A *clean* sample does
   not skip the full run — real regressions in production-priority and
   resource-threshold changes have been invisible at small scale repeatedly.
2. **Full Gauntlet** + head-to-head vs. the last accepted snapshot.
3. **Accept** if the head-to-head clears 50%, peer `WinPct` is met, and the
   diff shows no unresolved one-directional regression. Snapshot; this run
   becomes the new baseline.
3b. **If the result holds but your explanation of it fails, accept the result and
   record the attribution as OPEN.** Do not back-fill a mechanism story because
   the number came out well — a plausible account that survives only because
   nobody tested it is worse than an admitted gap, since every later iteration
   will be built on it. One lineage accepted a change on 34/50 with nine swept
   wins and zero swept losses while its pre-registered map-level prediction came
   out the wrong sign (rho +0.318, p = 0.127) and its post-hoc replacement did
   worse (p = 0.640); it logged "no covariate structure, attribution open" and
   built a one-keyword separating experiment as the next candidate. Note that no
   covariate structure and "swept everywhere" are often the *same* fact: a change
   that works on every map has nothing left for a map property to explain.

   **"Open" means unresolved, not unexamined.** This rule forbids fitting a story
   to a good number; it does not license leaving open a question that *reading the
   code* answers. Before spending a run, try to close it by enumeration: the same
   lineage then closed the attribution above at **zero game cost** by exhausting
   the four states of one tile and showing two were byte-identical, one a small
   loss, and one the engine trap — so the gain could only have come from the trap.
   That is a decomposition over code plus a verified engine fact, and it is
   falsifiable (name the case that would break the identity, and check it).
   Prefer it to an experiment; reach for the experiment when no such
   decomposition exists. An enumeration that closes the question also tends to
   hand you the next candidate, since the cases that are *not* identical are
   exactly the behaviour nobody chose.
4. **Near miss** (within `NearMissMargin`, no real regression): refine the same
   solution, up to `MaxNearMissRefinements` — several good ideas cleared the
   bar only after a parameter refinement of a directionally-correct mechanism.
8. **Reject**: trace the flipped games. A specific, well-understood failure
   mode earns one targeted refinement; otherwise revert fully and select a new
   target. A rejected attempt that converts a weakly-founded belief into a
   firmly-founded one paid for its run.

Design preference discovered independently in both projects: **self-calibrating
thresholds beat fixed constants** for opponent-variable behavior. When a fixed
threshold repeatedly trades one opponent's gain for another's loss, derive the
threshold from in-game observation instead of searching over more constants.

### 5b. What the accept gate cannot see

The head-to-head in step 5 is a **partial derivative, not a level**. It measures
a candidate's marginal value *conditional on everything the baseline already
carries* — so it is structurally blind to any interaction between the candidate
and a feature the baseline also has, because that interaction sits in both arms
of the comparison and cancels.

The consequence is that **a chain of individually-positive accepts can walk
downhill**. This is not hypothetical. One lineage found a snapshot scoring 56%
against a frozen opponent it had beaten 85% earlier, with every accept along the
way having beaten its immediate predecessor. The cause was a pair of features
that are fine alone and destructive together — 76% and 82% separately, 56%
combined — and the accept gate could not have caught it, because the candidate
was measured against a baseline that already carried the other half.

**This has now been measured directly, not just argued.** One lineage ran all
three comparisons of a two-part change on a single pinned 25-map sample, making
the arithmetic exact rather than estimated:

```
part 1 beats generation N-1 by +8
part 2 beats (N-1 + part 1) by +6
whole beats generation N-1 by +8    <- not +14
```

Sub-additive by 6 — and the whole is not merely *close* to the first leg but
**indistinguishable from it**: of 50 (map, side) cells, 6 disagreed, split
exactly 3–3 across six different maps, which is the churn signature rather than
an effect. So **a feature worth +6 against the immediate predecessor is worth
exactly 0 against the generation before it.** Head-to-head margins do not chain.

That is the whole case for the frozen roster in one line: no sequence of
head-to-heads can reconstruct a level when the links are not additive, so a
lineage that only ever measures adjacent generations cannot know where it stands.

Three practical rules follow:

- **The frozen roster is the only instrument that sees this.** Run it on a
  schedule, not only when something feels wrong. A head-to-head against your
  predecessor cannot tell a rising lineage from a drifting one.
- **When the roster drops, ablate PAIRWISE.** Single-feature ablation would have
  exonerated both halves of that pair individually. Test features in
  combination, not one at a time.
- **A marginal accept is an unpriced liability** against every feature you have
  not written yet. Something that barely clears the bar today is the half of a
  future destructive pair you will not think to suspect.
- **An ablation prices a CODE PATH, not a concept.** Record exactly which branch
  was gated. One lineage priced its "opportunistic area paint" at +6 games and
  then found a separate branch — painting the tile underfoot — spending 2.5-3.8x
  more of the same resource, never ablated, and easy to assume was covered by
  the earlier price because both are "painting". Two branches that consume the
  same budget are two prices. And where two such branches buy the *same good*,
  they are substitutes competing for one budget — in which case **the order they
  fire in sets the allocation, by accident rather than by measurement**, which is
  a policy nobody chose. Price them separately, then choose the split.

**When the roster drops, let ANCESTRY name the pair, not plausibility.** The
candidates are the features that entered or left between the generations the
roster is comparing — read the lineage, not your intuition about what ought to
interact. One lineage did exactly this: its ancestor carried a memory feature,
the next accept deleted it, and a later accept spent a unit's last resource into
work that only pays if a replacement returns to finish it. That is a bet which
only pays out under a feature an earlier accept had already removed — and it is
structurally invisible to a gate whose *both* arms lack that feature. The pair
was named by the ancestry in three lines of log, not by imagination.

**Nominations are usually wrong — the base rate says so.** Three candidate pairs
have been nominated by reasoning in this project and ablated properly; **two
were refuted**, one of them with the interaction coming out the *opposite sign*
to the argument for it. The one real destructive pair was found by ablating
after a frozen-roster drop, not by predicting it. So run the 2x2 when the roster
says something is wrong; do not run it because a pair *looks* like it should
interact.

A caution on chasing these: a heuristic **nominates** a candidate pair, it is
never evidence about one. The *sign* of an interaction is not predictable from
its shape — the same lineage found two pairs sharing the signature "payoff
multiplicative in an existing quantity", one destructive and one constructive,
and its prediction about the second was refuted by the ablation that saved a
feature worth 8 net swept maps.

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

## Most of what you try will fail. That is the design, not a verdict on you.

A loop whose changes mostly worked would have a gate that was too loose. The
rejection rate is the price of a gate strict enough to be worth trusting, so a
run of negative results is evidence the method is working, not evidence the
lineage is stuck. Read this section when a string of rejections starts to feel
like a plateau.

**An accept is not the only thing that moves the project.** These all did, in a
single day across three lineages:

- **A closed direction.** A constant bracketed on both sides is settled forever;
  nobody spends games there again. "Reserve is a plateau, not a peak" cost 400
  games once and saves them every time it is not re-litigated.
- **A falsified premise.** One lineage found the paint-tether story that **four**
  of its iterations rested on was simply false. That is worth more than any one
  of those iterations, because it invalidates a class of future proposals too.
- **A cheap kill.** Two games refuted an iteration's premise; one `javap` killed
  another; four probe matches killed a treatment before it cost 150 games. The
  cheapest possible way to be wrong is the most valuable habit here.
- **A better instrument.** In one day: the noise floor measured three ways, the
  full-corpus census, the API sweep, the engine-jar pin. Every future verdict is
  more trustworthy because of work that produced no accept at all.
- **A caught error.** A phase-only arm — a change that does *nothing* — scored
  **+12** and would have cleared an inherited accept gate. Declining to ship it
  is not a null result; it is a regression prevented.

**And the needle IS moving.** Over four full tournaments:

```
            20260907-0100   20260908-1300
alice           35.3%    ->     56.3%      (+21)
carol           19.0%    ->     45.3%      (+26)
bob             95.7%    ->     48.3%      (-47)
```

Two lineages climbed more than twenty points in two days. **And bob's fall is
not a decline** — the standings are zero-sum, so his number fell because the
other two rose. His own frozen roster, the only instrument that reports a level,
has him going 40 -> 70 against a fixed ancestor over the same period: his
strongest build ever, while his relative standing halved. Never read the
tournament as absolute strength in either direction.

**What this asks of you:** keep proposing things, and keep killing them cheaply.
A lineage that stops trying because most attempts fail has guaranteed the
outcome it feared; a lineage that keeps generating candidates and rejecting them
in two games apiece is spending almost nothing per attempt and will eventually
buy an accept that holds. The bounds are the rules — isolation, the shared VM,
the benchmark-as-yardstick — and inside them, being wrong quickly and in public
is exactly the job.

## When the loop stalls

**Out of ideas? Do these two things before inventing a new mechanism.** Both are
cheap, both draw on material you already own, and both have a better hit rate
than staring at the current bot.

1. **Re-examine the old tournament games.** Every round-robin's replays are kept
   on battlecode-dev under `arena/tournaments/<run>/replays/`, and they are the
   only games in this project played against opponents your lineage did not
   produce. You have almost certainly not exhausted them: a loss you traced once
   for one hypothesis still contains everything you were not looking for at the
   time. Read them for what the *other* lineages do that you never attempt —
   that is the self-referential blind spot in its most directly observable form.
2. **Re-read the prior-year reference docs** in `reference/`. Year-specific
   mechanics rarely transfer; the shape of past mistakes does, and so does the
   catalogue of ideas a lineage forgot to try. Start with `reference/RESEARCH.md`
   -- cross-year post-mortem findings from 2019-2024, whose §11 "The short list,
   when stuck" exists for exactly this moment. Its most load-bearing entries for
   a stalled lineage: symmetry inference (standard everywhere else, needs no
   communication, and is exact rather than heuristic); *emergent* coordination
   rather than commanded coordination, where one team won two-thirds of self-play
   games from a spawn-ORDERING change with no messages sent; and the repeated
   finding that the elaborate coordinated plan flops while basics done well win.
   (`RESEARCH.md` is a rebuild, not either predecessor's copy: both of those are
   built on 2025 post-mortems, which stay forbidden second-hand as much as
   first-hand, so the sources were filtered block-by-block BEFORE being read and
   only the 2019-2024 material survives. See `reference/README.md`.)

Neither is a substitute for a trace of your own bot losing. They are for the
state where you have run out of hypotheses, not the state where you have one.



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

**Run a consistency pass over LEARNINGS, not only an append.** Entries are
written months apart and each is checked when written, so a per-entry review
passes everything; only *comparing* entries fails. This is not hypothetical —
one lineage found the correct deterministic method (counting the (map,side)
cells on which two builds disagree) recorded in section 4, and a binomial noise
band contradicting it in section 5, **eight lines apart**, and quoted the wrong
one through three consecutive iterations.

The tell it extracted is worth reusing: **two rules that ought to cite each
other and never do.** A determinism rule and a noise rule in the same document
that have never referred to one another have probably never been compared.

**When you stop mid-hypothesis, record which pre-checks you have NOT done.**
Name them explicitly rather than leaving the log to imply the work was complete
— momentum is exactly when a pre-check gets skipped, and the next session
inherits the momentum without the doubt. One lineage registered three unfinished
checks by name and wrote down why each was the trap that had already caught it
three times that session; that is a stopping point another session can resume
from safely.

**A retraction is a claim too, and audit it harder than the claim it replaces.**
A correction is written by the same person, in the same frame, minutes after the
mistake — so it fixes what was noticed and inherits everything that was not, and
the unexamined assumption is precisely what was not noticed, because had it been
noticed it would have *been* the correction. One lineage called an effect "+1,
essentially nothing", retracted it as "+6", and both were wrong the same way:
the true answer was +6 against one opponent and exactly 0 against another. It
had argued about whether the number was 1 or 6 and never asked whether the
feature had a single value at all. So when retracting, do not only ask what was
wrong — ask **what both versions took for granted**.

This compounds with the rule that a correction running in your favour is the one
least likely to get made: **the dangerous corrections are the comfortable ones.**
A retraction feels like rigour, which makes it the least-audited thing in a log.

**Supersede in place; do not delete.** A withdrawn rule was load-bearing for
whatever was decided while it stood, so a reader arriving at those older entries
needs to find that it was withdrawn and why. Deleting it makes the old
conclusions unreadable rather than merely wrong.

**And prefer a measurement to an argument when two entries disagree.** The same
pass found a paint-budget decomposition that could not be reconciled with an
observed median; rather than settle it by reasoning, that lineage registered a
prediction about which entry would fall and ran the instrumentation to decide
it.

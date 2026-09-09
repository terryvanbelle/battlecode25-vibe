# Doctrine case studies

The evidence behind `TRAINING_ALGORITHM.md`'s measurement doctrine: what
actually happened, to whom, and with which numbers. It was split out of that
file on 2026-09-09 because the doctrine is read in full at every cold start by
every lineage, and at 1,109 lines it had become the largest mandatory read in
the project — while these passages are what you consult when a rule surprises
you, not what you need in front of you to follow it.

**Nothing was deleted, and no rule moved.** Every doctrine entry keeps its rule,
its decisive numbers and its actionable checklist inline; what came here is the
narrative that earned them. Read the entry for a rule you are about to lean on,
or when a rule seems wrong to you — that is usually the moment a case study is
worth its tokens.

## Doctrine 1 — Determinism means re-running is worthless — but it does NOT mean your

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

## Doctrine 12 — Track a fixed old-bot roster for long-run progress. Peer retirement

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

## Doctrine 14 — Check that two agreeing numbers are actually two numbers. Rule 13 says

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

## Doctrine 15 — Before you build an instrument, check its statistic can separate the

A lineage proposed "distinct tiles occupied per 30 turns" to detect soldiers
livelocked between two tiles. Then it noticed that a soldier standing at a
ruin painting a 5×5 pattern *also* occupies few tiles — that is the bot
working correctly. Every robot it probed was low-mobility on both the map it
loses and the map it sweeps. Had it built the census as specified, the tool
would have returned **a large, confident, meaningless number**.

**What worked instead was a conjunction, where each clause rules out a benign
reading the others allow**: few tiles, *alternating* between them, paint
falling every turn, nothing ever completed, death by exhaustion in place.
Productive parking fails the alternation and the nothing-completed clauses;
a slow walk fails the few-tiles clause. When a single statistic cannot
discriminate, the fix is usually a conjunction rather than a better
single number.

The same probe then pointed at the variable that *does* separate — unit
lifetime — which the lineage promoted to lead the census while demoting
mobility to secondary. **Revising a spec before the tool exists is nearly
free; revising it after is a rebuild plus every conclusion drawn in between.**

**And state the DENOMINATOR of every rate as carefully as the numerator.**
Two lineages have now published a rate that was wrong only in its
denominator, and neither error is visible in the number itself:

Both are the same shape — a count that looks like exposure but is not. So
before reading any rate, say out loud what one unit of the denominator is
(a robot-round? a decided game? an independent game?), and check that the
thing you divided by counts exactly those.

## Doctrine 16 — Check your evaluation covers the REGIME where you actually lose. The

A lineage found that across **~4,900 self-play games and 68 opponents,
essentially none ended before round 200** — while its losses to a sibling
concentrate exactly there, and that sibling ends 6% of its games in that
range. Even the synthetic archetype it had built to attack itself differently
had a median length of 949. **Four consecutive iterations were each evaluated
in a regime none was designed for**, which explains four nulls without any
hypothesis about the mechanisms themselves.

Before reading another null: plot what your gauntlet actually samples — game
length, map size, whatever your losses condition on — against the
distribution of your *tournament losses*. A gauntlet that never enters the
regime will report a confident, well-powered nothing.

**Take the free controls the tournament hands you**, too. When two lineages
play byte-identical builds across consecutive runs, that pair is a frozen
control nobody paid for: one such pair reproduced 150/150 including exact
round counts, and corrected two headline statistics that had been pooled over
opponents whose strength was changing underneath them.

**And tightening a gate is not free.** A lineage corrected its threshold
upward, audited its past accepts against the new bar, found three that failed
it, and predicted in writing that the stretch had destroyed value. A
full-corpus census then returned **+38 (+3.31 sd)** — they were three small
*true* effects. **Raising a threshold without adding power only trades false
accepts for false rejects.** If the honest gate is beyond your current
resolution, the answer is more games or a better instrument, not a stricter
number.

## Doctrine 17 — A self-play instrument is blind to any deficit your opponent shares

A lineage hit this squarely. It established from 1,208 tournament games that
its win rate falls monotonically in a map property (Cochran-Armitage
z = −8.44), built the fix, and won its census by **+44 at 6.8 sd** — its
largest accept — while the *pre-registered secondary*, that the gain should
concentrate where the property is strongest, came back flat. The reason is
structural, not statistical: the gradient exists **because the other lineages
handle that property and this one did not**, so a census against a sibling
build carrying the identical defect cannot see it.

The practical rules:

## Doctrine 18 — Replay per-robot state is recorded POST-action. Never use it to estima

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

## Doctrine 19 — A lesson you wrote is not a control. Install the check where the mista

Writing a lesson records that you understood something once. It does nothing
at the moment of the next mistake, because the failure is not ignorance of
the rule — it is not consulting it. So convert the lesson into something that
fires without being remembered: a unit named for the constant's units, an
assertion beside the definition, a reconciliation the analysis performs on
itself, a pre-check the loop runs whether or not you feel it is needed.

The test for whether a lesson is done: **could the next session make this
mistake without reading anything?** If yes, the lesson is a note, not a
control. `LEARNINGS.md` is the record; the mechanism is the fix.

## Doctrine 20 — A pooled tournament rate is a statement about a THREE-body system, nev

A lineage found a map subset where its pooled rate was 25.0% against an
expected 49.9%, z = 4.15, and it looked like a private, specific defect. The
pair decomposition inverted the reading: against one opponent the subset was
flat (−2.9 points, z = −0.32), and the whole effect sat in the two pairs
involving the third lineage (−41.4 and −35.8). So the correct claim was not
"I am broken on these maps" but "**two of the three lack a capability the
third has**" — and the flat pair is the control that proves it, because two
builds carrying the same deficit cancel exactly as doctrine 17 describes.

The rules that follow:

---

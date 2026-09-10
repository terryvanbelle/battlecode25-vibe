# Cross-lineage methods

Practices that demonstrably worked for one lineage, written down so the other
two can adopt them. Maintained by the coordinator, who is the only party that
reads all three workspaces. Attribution is deliberate: knowing *who* a practice
worked for tells you what kind of situation it was forged in.

**What crosses this line and what does not.** Methodology crosses: how you
measure, how you decide, how you record, how you keep yourself honest. Strategy
does not: no mechanism, no unit mix, no build order, no map-specific finding, and
no number that encodes one. That firewall is not squeamishness — the twice-daily
tournament is only a measurement because the three of you arrived at your bots
independently, and it stops being one the moment a mechanism crosses. You may
adopt anything in this file freely; you may not ask for, and will not be given,
anything outside it.

Every item names the evidence. A practice without one is a preference.

---

## Spending

**1. Build a ladder that kills hypotheses for free before it kills them for
games.** (alice) Her order is: engine probe against the pinned jar, then a census
over replays already on disk, then a 2–3 game probe, then a screen, then a
census. Recent kills at each rung: a leading hypothesis refuted by reading the
engine (`attack()` adds cooldown only `if (type.isRobotType())`, and a tower is
not one) for zero games; a build-radius finding killed for three; an iteration
voided for two when its motivating bucket reconciled to accumulation alone. The
rung matters more than the cleverness: a hypothesis killed at rung one costs
nothing and returns the whole session.

    **Two refinements, both from a session where four pre-checks in a row
    demoted the direction that motivated them:** design the pre-check so that it
    *can* disqualify the mechanism you want to build — one that can only confirm
    it is a formality, and the cheapest decision in the loop is the one that
    kills your own favourite. And before choosing a mechanism at all, run the
    test that decides which CLASS of fix is eligible: "the unit died" is an
    endurance limit no targeting rule can repair, "the unit was alive and
    elsewhere" is a decision one can. Every mechanism in that session which
    skipped the class test failed.

**2. Price the mechanism in the units of the gap before you screen it.** (bob)
Not "did it help" but "how much of the deficit can it possibly close". He
measured a mechanism's effect at +1.7 per-mille against a +16 per-mille
requirement and closed the direction **on magnitude rather than on power** — a
null that cannot be dismissed as an underpowered run, and which no larger sample
would have overturned. He also declined an 88-game census he had registered, on
the grounds that it would resolve a ±2-win effect whose mechanism was 10× too
small, and recorded the decision as a change rather than dropping it silently.

    **Get the exchange rate from your own spent gates, never from theory.**
    (bob) Two rejected iterations had each paid a gate for a *measured* quantity
    of an intermediate resource, which turns them into calibration data: he
    derived 1.0 unit of that resource ≈ 25 wins out of 50, saturating above ~0.25
    of it. That priced an entire family for free — his bar needs ≥0.40 saved, the
    largest saving anywhere in his budget is 0.600, and half of it already
    saturates — so the family closed at once instead of one idea per screen. The
    theoretical rate he had been sizing against for 50 iterations was **8×
    optimistic**. A conversion factor you reasoned out is a guess wearing a
    number's clothes; your own rejects are where a real one comes from.

**3. Read your own instruments for absolute degeneracy, not opponent-relative
deficit.** (bob) "327,000 chips unspent at round 2000" and "coverage peaks at
round 150 then declines" need no opponent to be obviously wrong, and both had
been sitting in every replay since iteration 0 while he reasoned about matchups.
Three accepted iterations came out of counter dumps; the one that came out of
reasoning was rejected.

## Gates

**4. Know what your gate is worth in standard deviations, measured from your own
runs.** (carol) The engine is deterministic, so a rerun on the same maps
reproduces exactly — which tempts you into treating the screen's standard error
as zero. But an accept asks about the map *population*, and a 25-of-75 draw
carries real sampling variance. Measuring 59 of her own arms showed a gate she
had labelled 2.0 sd was worth about 1.0 sd. Do this to your own gate before you
trust another verdict from it.

**5. The finite-population correction is not a nicety, and pairing per map is
free.** (carol) With n=25 drawn from N=75 the (N−n)/(N−1) factor is a real 18%
reduction in sd. Each map contributes both sides, so the natural unit is per-map
wins in {0,1,2}; map difficulty and spawn advantage live inside that unit and
cancel when both arms draw the same map.

**6. A dose comparison advances only after replication on a *disjoint* map
sample.** (alice) A run is exact for the maps it played, which is not the same as
precise about the map population. `comm -23 <(sort tools/bc25-maps.txt) <(sort
gauntlet/<run>/maps.txt)` gives you the maps a run did not use. One of her dose
comparisons inverted a prior on a 7-point gap whose resolution she had never
measured.

**7. Put the unit in every name.** (bob) His `gate.py` exists because two units
in play differ by exactly a factor of two — `wins_above_half = W − N/2` versus
`win_minus_loss = W − L`, which is twice it. A gate and a noise floor quoted
without units are one careless comparison away from a factor-of-two error, and
this project has published one (a 6.8 sd that was 3.39 sd). Name the variable
after its unit and the mistake becomes unspeakable rather than merely unlikely.

**8. Ask whether your gate can see the thing at all — and answer it with a
number.** (carol, and bob independently) She correlated her target property with
winning in both instruments: +0.009 over 5,768 self-play games versus −0.346 over
300 tournament games. Nineteen times the data, and the flat instrument was the
one she was accepting on. He reached the same conclusion from the other side,
finding that four consecutive mechanisms aimed at one deficit had all been graded
on a self-play gauntlet that structurally cannot price them (doctrine 17). Before
building against a deficit you found in the tournament, check that your gauntlet
can register it. If it cannot, the accept/reject you are about to spend 50 games
on carries no information.

## Pre-registration

**9. Specify the manipulation check as a SHARE, not a count.** (carol) "Did the
knob move the behaviour, and by how much of what was available" catches a dose
overshoot that a raw count hides. Hers caught a 4× overshoot for the cost of one
game, where the same error class had previously cost a full 50-game screen.

**10. Then check the share's denominator is not caused by the treatment.**
(carol) Her corrected check swept the knob 8× and the metric moved only 67%→89%,
because blocking a build left resources unspent, which generated more
opportunities to divide by — the denominator grew 11× across arms. **A ratio fed
by the thing it measures compresses toward a constant no matter what you do to
it.** The fix is a counterfactual denominator computed from a quantity the
treatment does not move.

**11. Register the *selection rule* before the numbers exist, not just the
gate.** (carol) "Screen the largest setting whose corrected dose is ≤50%, and if
none qualifies, report that the mechanism cannot be dosed into band" — committed
before the doses were measured, which made applying it mechanical rather than a
judgement call made while looking at outcomes. Her rule explicitly ignored the
calibration-map results, which is the part that stops it being overfitting.

**12. Name, in advance, the observation that would make you drop the
hypothesis.** (alice) Her strongest accept this week was one whose pre-registered
falsifier pointed *away* from the session's headline and did not fire; the gain
decomposed exactly as predicted (+3 on the four target maps, −1 across the other
71) rather than as a diffuse drift. A falsifier you would actually accept is what
separates a confirmed prediction from a plausible story.

## Memory

**13. Keep a closed-directions ledger, and grep it by hypothesis name before
opening anything.** (alice) Hers returned a hypothesis by name that had been
closed three times, catching a re-open in progress. Each entry needs a **checkable
re-open condition** — the number that would have to change — or it silently
becomes a permanent ban rather than a closed question.

**14. Every durable lesson names the measurement that produced it.** (bob) "A
lesson without one is a belief" is the header of his LEARNINGS, and it is what
lets him distinguish a lesson that has been superseded from one that has merely
become inconvenient. Two of his entries have been corrected on this basis rather
than argued about.

**15. Tag engine facts with their provenance.** (carol) Every `[E]` in her rules
digest is verified from the pinned jar, with a provenance section naming how and
when. When the jar resolver was fixed, she re-verified the tagged set in one pass
instead of wondering which facts were inferred.

**16. Run a standing unused-API sweep on a schedule, not when you feel stuck.**
(alice, adopted independently by bob and carol) All three of the sweeps run so far
found something material — one of them a mechanic that had never appeared in any
accepted snapshot across 48 iterations, not because it was rejected but because
it was selected once, deferred for something else, and never picked back up in
~13,000 log lines. A stall is the *late* signal; the calendar is the early one.

## Doing it at all

**17. A lesson you wrote is not a control — install the check where the mistake
happens.** All three converged on this independently, which is why it is doctrine
19 in TRAINING_ALGORITHM.md, and each built the same shape of fix: a tool that
refuses to let you make the error rather than a note asking you not to.
- (carol) a stage-0 check that **refuses to print or even collect who won**, so a
  one-map result cannot be read as a verdict; it answers only "do the arms
  differ" and "did the intended behaviour change".
- (carol) `tools/agent-commit.sh`, which commits through a private git index so
  the shared one is never written — now shared, and the reason the commit rule no
  longer has to be remembered.
- (bob) a gate script that will not print a number without its unit.
- (alice) a ledger she greps by name, rather than a memory she consults.

**19. An aggregate gate cannot see a trade — pre-register the subgroup that
would expose one.** (carol) Her census rejected at +14 overall, and the
pre-registered subgroup split it into **−6 and +20** across a map property fixed
before the first turn: the mechanism paid where the lineage loses and cost it
where the lineage already wins, and the two nearly cancelled into a number that
looked like nothing happening. Three things made that readable rather than
post-hoc: the subgroup was registered before both the screen and the census, it
was keyed to a property that exists before the game starts rather than to
anything the game produces, and its three previous failures to fire were named
in the registration. A split you choose after seeing the aggregate can always be
found; this one could have failed and had.

    **Cut by TIME as well, and before you trust either.** (bob) His whole-game
    comparative said a stock differed by −4%; windowed by round it reads −9%,
    −16%, −18% across exactly the interval where the coverage gap opens, averaged
    away by his ending 15% ahead. "The deficit is not a stock but a window" is a
    different kind of conclusion from anything a whole-game number can yield —
    and his army arriving at 1.94× five hundred rounds too late is invisible to
    every aggregate he had.

    **Cross the cut with the opponent — the 2×2 is the standard form.** (alice)
    A map-property cut pooled over opponents cannot say whether the property or
    the opponent drives it. She had what looked like a map-size deficit; the 2×2
    showed −28.7 against one lineage and a flat +0.85 against the other, so it
    was never a size problem but a size-and-that-opponent problem, and the six
    iterations aimed at the pooled reading were aimed at nothing. This is
    doctrine 20's pooled-versus-pair error arriving on a map cut instead of a
    standings cut. `tools/map-subset.py` does the win-rate version for you and
    refuses to print a pooled rate without its three pair rates; a metric of your
    own you must cross yourself.

**20. Cost an experiment's resolution against its expected signal, and kill it
before it spends games if it cannot separate its own hypotheses.** (carol) A
planned 50-game screen resolved 21.2 margin points against an expected effect of
+14 — 1.32 sd. She cancelled it, left the arm built and unrun, and recorded
attribution as permanently open for that design. Three hundred games saved, and
unlike a null this decision cannot be argued with afterwards: it is arithmetic
done in advance. The reciprocal is doctrine's own warning — an experiment that
*can* separate its hypotheses is worth running even when you expect it to pass,
which is how her free in-run placebo came to confirm a mirror at exactly 50.0%.

**24. A defect implies a decision — attribute a rate to its actor before calling
it waste.** (alice) A pre-specified secondary fired hard: 23.4% of her
post-saturation paint actions repainted ground her own team already held,
apparently buying nothing. Splitting by the unit that produced them gave 100% to
one type and zero to the other, and that type has no alternative — it is the
unavoidable footprint of an area weapon, not a targeting choice any code makes.
Published without the split it would have been a 23% "waste" headline about the
shape of a splash. So before a rate becomes a defect, ask which actor produced
it and whether that actor could have done otherwise; if one actor is all of it
and had no choice, you have measured a constraint. The same split is what
confirmed a separate engine trap at corpus scale in the same pass — 12,409
over-enemy paints, one actor 12,409, the other exactly 0.

**25. Prove your check can fail before you trust it passing — and make a
completeness test count the unit the writer writes.** (alice) Two of her
verifications printed reassurance unconditionally: `diff | head && echo
IDENTICAL` reads `head`'s exit status, not `diff`'s, and a `while` loop's status
is its last iteration's, so both said IDENTICAL whatever they found. She rebuilt
the checker so that it can fail. Separately, a waiter counting *lines* to decide
a run had finished read 58 lines as 50 games when each game writes three — the
run was at 19 — and the partial file showed the textbook signature of an inert
mechanism for an arm that was actually engaging at 74%. **A check that cannot
fail is not a check, and a partial file can show exactly the pattern you fear.**
The two tests: make your verifier fail on purpose once, and count the unit the
producer emits, not the lines it happens to produce.

**27. When independent levers all price below your gate's resolution, the next
decision is about the EVALUATION DESIGN, not the mechanism.** (alice, and bob
from the other direction) She measured four mechanisms from four unrelated
instruments and all four landed at 7–17% of the same gap; he ran three arms that
scored +6, +5, +6 against a bar of +7. Neither of those is four disappointments
or three near-misses — together they say the deficit is structural and the
individual levers sit at or below what a 50-game screen can see. Her iteration 53
proves the instrument half with evidence rather than assumption: the intermediate
variable moved **+639, over 50% above control**, and the screen returned net
swept −2. So the choice is stack-and-screen (test the sum, accept the loss of
attribution) or census-per-mechanism (keep attribution, pay 150 games each) —
and it is made and written down **before** building any of them, because deciding
afterwards is choosing the design that flatters the result you got.

**28. A two-way rule always finds a winner unless you name the residual in
advance.** (alice) Her discriminator returned 43% / 41% / 16% against a
pre-registered rule needing ≥60% either way, so the verdict was MIXED and she
picked no mechanism on it. The third bucket was named before the run: folding it
into one side gives 57%, into the other 59%, and either would have licensed a
claim that the class was settled. Register the category that means *neither*.

**29. Score your registered predictions as a series — the pattern in your own
errors is free calibration.** (bob) Five consecutive predictions of his got the
structural call wrong and the magnitude call roughly right, and he logged that as
a fact about himself rather than about the game. It costs nothing, because every
one of those predictions was already registered before its run; all that is added
is reading them together afterwards. What it buys is knowing which half of your
own claims to discount — and a lineage that knows its structural intuitions are
unreliable will spend its probes differently from one that does not.

    **Split the tally three ways, because the middle case is the informative
    one**: right, *nominally right but substantively wrong* (correct area, wrong
    quantity), and plainly wrong. At 1 / 2 / 6 he concluded his instincts find
    the right area reliably and the right quantity rarely — so the efficient move
    is to probe several quantities inside a nominated area rather than hunt for
    better areas. A tally is only worth keeping if it changes what you do next.

**30. A frozen rung at 100% cannot register a regression — read the roster
weakest-first, and repair saturation by ADDING a harder rung, never by retiring
one.** (bob, then carol independently) He found his roster reading 92%, 88% and
100% with one rung still discriminating, and made it a standing rule for his
workspace: when the weakest rung passes ~90%, pin the newest accepted snapshot as
a new rung. She met the same thing from the other side while doing the honest
version of a pre-accept roster check — 7 of 11 rungs at 100%, which she noted
*could not have shown a regression* even if her candidate had caused one. A mean
over saturated rungs hides that nothing in the set can move. Retiring a rung is
the one repair that is never available, because it takes its whole history with
it and the value of a rung is its long-run trend.

**31. Register the PRECEDENCE between a primary and its control — and never set
a threshold on a ceiling.** (bob) He registered a build threshold and a
comparative control, and they fired in opposite directions: the primary cleared
its bar by 1.4% while the control showed the lineage already doing the thing
*better* than the opponent beating it. Nothing in the registration said which
governed, so the precedence had to be settled after the fact — on the merits, but
that is a decision you never want to be making with the numbers in front of you.
Register it in the same breath as the conditions.

    The second half is the sharper rule. His primary measured a **ceiling** —
    what the direction is worth if everything goes perfectly and costs nothing —
    and a threshold on a ceiling inverts the meaning of a pass: clearing 16,000
    by 1.4% *reads* as support and is evidence the direction cannot pay, because
    the real mechanism only ever recovers a fraction of a ceiling. His own
    registered confound then showed the ceiling was unpurchasable at all. If your
    primary is a ceiling, the bar belongs several multiples above what you need,
    or the quantity is the wrong primary.

**32. Check that you are BEHIND on a metric before you optimise it — and never
ask an outcome-conditioned question of a corpus whose outcomes are structural.**
(bob) Both halves come from one closure, and the first has now paid three times
running.

    **The comparative.** Three consecutive directions of his closed because the
    tournament corpus showed him *ahead* of the lineage beating him 60–40 on the
    very quantity he was about to improve — territory discipline, upgrade rate,
    chip liquidity. Each time the check was free, off replays already on disk,
    and each time it replaced a screen. "Am I actually worse at this than the bot
    that beats me?" is the cheapest question in the loop and almost nobody asks
    it first. This is doctrine 17 turned into a positive procedure instead of a
    warning.

    **The corpus.** He registered a split conditioned on *outcome* — "higher in
    the games I lose" — against a mirror gauntlet in which both sides run
    identical policy and the win/loss split is 50/50 **by construction**. That
    corpus can measure a level; it can never condition on winning. He caught it
    before reading the number as an answer, redid it against real opponents, and
    it inverted outright, turning a would-be re-open into a confirmed closure.
    Before conditioning on any outcome, ask what generates that outcome in the
    corpus you are using.

**33. Check where your probe map sits in the corpus distribution — a cheap rung
on an outlier over-promises systematically.** (carol) Every stage-0 check her
lineage had ever run used one map. Measured against the corpus it is 3,600 area
against a median of 1,500, 52 ruins against a median of 17, and **the only map of
75 with ≥52** — for a lineage whose gains concentrate on ruin-dense maps, the
best case by construction. It over-stated three mechanisms in a single session,
including one that won there and then lost 38/150. No verdict was invalidated,
because every verdict was decided on a 25-map screen or a 75-map census, but it
explains why the cheap rung kept promising more than the screen delivered. The
repair is to default the rung to a median map and keep the outlier as a
**labelled best-case probe** — an outlier is useful precisely when you know it is
one.

    **And a statistic that moves hugely while the outcome does not is a
    correlate, not the channel.** Hers moved 0% → 49% across a dose ladder with
    a dead-flat result, and it had been the headline clause of an earlier
    accept's stage 0. She found it by running a check she expected to pass, which
    is the only way that kind of error surfaces.

**34. A pre-gate needs a null arm — its noise floor is not your accept gate's,
and measuring it is free.** (alice) Her 6-game manipulation pre-gate rejected a
bundle at −125.7. In the same batch sat an arm that provably did nothing (its
lever fired at 1%), and it moved the same comparison by **−69** — so the
pre-gate's floor is about ±70 and the rejection is 1.8 noise units, directionally
clear but nothing like as crisp as the raw number reads. She had measured her
accept gate's floor long ago and never this one. The null arm costs nothing
because it ships in the same batch as the arms you were already building.

    Two more from the same run, both worth copying. **Check your inventory
    before you make a design decision, not after** — hers went from three
    surviving levers to two, and from ~48% of the gap to ~33%, which changed the
    decision she was about to register. And **a lever that fires at 1% is
    UNTESTED, not rejected**; miscounting it as a null is how a direction gets
    closed on evidence that never existed.

**35. When a mechanism does not fire, build a FUNNEL of its preconditions
before you re-dose anything.** (alice) Her lever fired on ~1% of opportunities
and her registered next step was to re-dose the threshold she blamed. Instead she
decomposed firing into a chain of conditional shares — action free after the
attempt 45.4%, then spare resource above the threshold 60.0%, then a recipient in
range **20.0%**, then that recipient actually needing it 21.4% — which located
the collapse at adjacency, not at the dose she was about to change. The re-dose
would have spent a build and six games moving a mechanism from dead to slightly
less dead.

    Three properties make it a rule rather than a story. It **validates itself**:
    the funnel predicted 1.2% firing against ~1% observed in an ablation, so the
    instrument is checkable against something already measured. The
    **counterfactual bounds the knob**: removing the threshold entirely lifts
    firing only 1.2% → 1.9%, which settles that the knob cannot matter, without
    building anything. And it separates **cannot act** from **did not help** —
    different closures with different re-open conditions, and only the first can
    be stated as "the dose cannot make it act, and what would make it act removes
    the reason it was safe".

    **An EXACT invariant across a manipulation that should have moved it is a
    stronger result than any change.** (carol) She drove the supposed competitor
    from 331 to **0** and the contested quantity did not move at all — 26 before,
    26 after, unchanged to the unit. That is not a weak effect; it says the
    competition was never the constraint, and it pointed at the real ceiling,
    which two very different configurations were hitting by different routes.
    When a manipulation removes something entirely and the target is unchanged to
    the last digit, stop looking for a dose and start looking for what else is
    binding.

    The same run carries the harder half of §22: she had *published* a cause for
    the non-firing, then did the arithmetic on her own explanation — a starting
    stock of 100, ~0.96 spent per turn, a ~64-turn life, therefore above the
    threshold for ~80% of its life — and retracted it before acting on it. That
    retraction is what exposed the real gap: she had priced the mechanism's
    supply and never measured its delivery.

**21. Simulate the null before you trust a bar — especially for any statistic
built from a max, a best-of, or an argmax.** (alice) Her pre-registered bar of
100 sat *below* what best-of-8 noisy sectors produce with no structure at all:
about 200 per mille of pure upward bias. The bar could not have rejected
anything, and the first screenful duly reported "emphatically passes". She voided
it rather than substituting a new one mid-flight. Selection statistics are biased
upward by construction, so the bar has to clear the bias, not zero — and the
cheapest way to find the bias is to run the same statistic against data you know
has no structure.

**22. A re-open condition that fires must be written back to the entry that
carried it.** (alice) Her ledger held a condition already discharged by a census
sitting on disk, unannotated, so a later iteration partly re-ran work she already
had — and the lesson that failed was her own "supersede in place must ANNOTATE
the old entry", on the very entry it was written for. A closed-directions ledger
(§13) and this are two halves of one mechanism: without the write-back, the
ledger degrades into a record of what you once believed rather than what is
currently true.

**26. A settled fact must carry its provenance, and a word that spans two
quantities will eventually be read as the wrong one.** (alice) She carried a
premise as settled for 44 iterations and killed three iterations with it. It had
been established **off one map, late, in self-play** — provenance that could
never have borne that weight, and which nothing in the entry recorded. The error
underneath was a conflation: one word named two different measurable quantities,
one of which remained true while the other was false, and the true one was read
as evidence for the false one. Record how a fact was measured beside the fact
itself — how many maps, at what round, against whom — so a later session can see
what it can bear. And when a premise rests on a word rather than a number, ask
which quantity the word denotes *here*, because it will not always denote the
same one.

    **Gross is not net, and an opponent-specific finding must carry its
    opponent in the sentence.** (bob) A count he was about to act on differed by
    59% and was **90% churn**: standing stock differed by 4%. "Built" and
    "standing" are two quantities under one word, which is this entry's failure
    in its cleanest form. Separately, he had been carrying a figure measured
    against ONE opponent as his general opening; against the other lineage that
    opening is fine. Write the opponent into the sentence, or the finding will be
    generalised by whoever reads it next — including you.

    **Sweep your own re-open conditions periodically.** Hers was written at
    iteration 9, was satisfiable long before it was checked, and fired the moment
    someone looked. §13 keeps the ledger, §22 writes back a discharge, §23 makes
    sure a condition can be met at all — this is the part that makes a condition
    get *tested*: put it on the same schedule as the unused-API sweep (§16),
    because a stall is the late signal and the calendar is the early one.

**23. Power-check a re-open condition when you WRITE it, not when you invoke
it.** (carol) She audited a condition her own ledger carried and found it
unsatisfiable: the proxy clause passed comfortably, but the clause that mattered
required a conditional variant to beat the unconditional one, and the gap between
them was 0.33 sd — unresolvable at 300 games. So the condition could never be
met, and had sat there for days looking actionable. **A re-open condition that is
correct and unsatisfiable reads identically on the page to one that is correct
and actionable**, which makes this the one property of a ledger entry you cannot
check by re-reading it. Cost it against your own noise floor at the moment you
write it, and if it cannot resolve, say so and close the direction properly
instead of leaving a door that does not open.

**18. When a session ends mid-question, leave the resume point machine-checkable.**
All three now do a version of this, and the sessions that recover cleanly are the
ones whose in-flight work was described by run-id and gate rather than by
intention.

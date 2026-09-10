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

    **A sweep catches an unused METHOD, never an unused TARGET.** (alice) Her
    sweep ran four times and each time correctly reported the attack call as
    *used* — it is, constantly, for a different purpose. The verb was in
    permanent use and only the object was missing: no soldier of hers had ever
    targeted an enemy tower, in a lineage whose own master variable is towers. No
    amount of re-running the sweep could surface that, because the sweep asks
    which methods are called and not which arguments they are called with. Ask
    the symmetric question instead — *what does this bot never do TO the thing it
    cares most about?* — and check the call sites, not the call list.

    **And when a sample is selected, say which half of the finding survives it —
    then check that claim too.** She chose four games as her worst collapses, so
    the 25:1 ratio was inflated by selection, and she wrote "the rate is selected;
    the absence is structural". **Her own pre-check refuted the second half one
    iteration later**: run against a matched sample of her *wins*, the bot
    destroyed 7 enemy towers, so the zero was a property of those games after all.

    The repair is the distinction the line was reaching for. **An aggregate zero
    in a selected sample is still selected. Only a zero you can trace to a
    missing code path is structural — and you must attribute it by actor before
    you can say which you have** (§24). Attributing every kill and all 20,000 HP
    of tower damage gave SPLASHER 100%, SOLDIER 0%: the structural claim is that
    her *soldiers* never attack towers, which the source confirms and no sample
    can overturn, and it is sharper than the aggregate claim she lost.

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

**24b. When you EXTEND an instrument, prove the extension is additive by
reproducing the old numbers exactly.** (alice and carol, independently, the same
night) She added counters to a probe whose funnel figures she had already
published, then verified 558/558 units, 93,727/93,727 turns, 2,094/2,094 events
and identical game-end rounds before trusting a single new number. He — on a
different lineage — patched counters into five arms and required every game to
reproduce its earlier round number, since only counters had changed. The engine
is deterministic, so an extension that alters behaviour announces itself
immediately and one that does not is free to trust. Two lineages arriving at this
in one night is the usual sign that a practice belongs in the shared file.

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

    **Better than once: ship a `SELFTEST=1` mode that injects a failing value.**
    (alice) She built a control to catch a stale instrument, and its first draft
    reproduced this exact defect — a malformed argument made a `-gt` fail
    silently and the script printed *"OK: the roster is current enough to
    trust."* Third member of this family in a day. Her fix was not to test it
    once but to build the test in: an env var forces the failure branch, and all
    three exit paths are verified on demand. A check whose failure path has never
    executed is a check you are guessing about, and a self-test mode retires the
    guess permanently instead of at the moment you happened to look.

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

    **And when every lever lands in the same narrow band, the band is naming the
    CLASS of what you lack.** (alice) Her four-then-seven mechanisms all priced
    at 7–17% of one gap, which §27 reads as "structural". Measuring two unrelated
    fronts then showed both short by the same kind of quantity — completing a
    pattern needs a ~4.5-unit relay and gets 2.41; killing a tower needs ~1.6
    unit-budgets on one target and gets 1.01 — so they are one defect, not two,
    and the defect is **coordination**. Every mechanism she had priced was a
    *local* rule (a heading, a threshold, a key, a spare action), and no local
    rule supplies coordination. That is why they all landed in the same band. Ask
    what the near-miss mechanisms have in common; the answer names the capability.

    **When every candidate mechanism closes and the defect stands, that
    exhaustion is a finding — ask what the units are doing INSTEAD.** (bob) Five
    mechanisms closed against one live defect, and his units turned out to be
    present, at the right distances, in the right numbers, and simply not doing
    the thing. That converts the question from policy to accounting: their turns
    went somewhere, so measure where. His own earlier census already held the
    answer — a third of the relevant effort going to work the opponent beating
    him essentially never does, under an accept made long ago against a different
    opponent.

    **Then ask whether it is a DECISION gap or an INPUT gap, because only one of
    them a local rule can close.** (alice) Before reaching for the expensive
    capability she drafted the cheap alternative — re-key a per-unit choice to a
    shared observable so units converge with no communication — and her own
    ledger killed it for zero games: the choice set is 1.00 candidates per turn
    and was **never 2** across 15,229 turns, so a shared tie-break has no tie to
    break. What that revealed is the criterion: her units fail to concentrate not
    because they *choose* differently but because they *see* different things, and
    **no function of each agent's own inputs can coordinate agents whose inputs do
    not overlap.** That is a property of the information, not of the policy — so
    when the inputs are disjoint, a local rule cannot close the gap at any dose,
    and the requirement is a channel that crosses the input boundary. Ask it in
    that order: would these two agents even have the same options in front of
    them?

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

**40. Run the absolute-strength instrument on a schedule tied to ACCEPTS — a
stale roster is worse than none.** (alice) Hers was four accepts behind when it
finally ran, and it appeared to show her live bot losing to its own earlier
snapshot by −7 net swept, ~−2.3 sd. **That alarm turned out to be false** — the
150-game census returned +2 — and the correction is recorded in §41, because the
staleness itself was real and is the lesson here: for four accepts she had no
absolute reading at all, and a session of work rested on a baseline nobody had
checked. **The last
reading of a stale instrument silently licenses the belief that the line has been
going up.** Tie the run to accepts, not to convenience: after every accept, or
every second at the outside, and treat "my absolute instrument is N accepts
stale" as a defect to fix before the next build rather than a note.

    The corollary from the same run, and it is why nothing was lost: she
    registered the rule *before* the confirmation census returned — revert at one
    threshold, do nothing in a middle band, treat a third case as an unlucky
    draw — plus a diagnostic cut. The census landed in the third branch and she
    applied it as written. **Reverting on the screen alone would have destroyed a
    correct accept on noise**, and the diagnostic cut then reproduced that
    accept's original map-level prediction exactly, at 150 games instead of the 8
    it was accepted on. Register the ACTION, not just the metric.

**41. A multi-cell instrument needs a multiplicity correction, and sibling cells
from the same run are not corroboration.** (alice) Her roster prints twelve cells
per run. She read the most alarming one as a single comparison: P(a given cell
≤ −2.29 sd) = 0.011, but **P(at least one of twelve) = 0.121** — about one run in
eight, and she had no multiplicity correction anywhere in her roster reading.
Worse, she then cited the two largest movers among those same twelve as
independent support, across runs on different random map samples — *selecting the
movers and calling them corroboration*, in an entry that quoted the charter line
forbidding it.

    The instrument's own limit, measured afterwards: a 25-map cell has
    sd ≈ 3.05 net swept, so it cannot resolve anything below about ±6. **The
    roster detects large regressions and cannot adjudicate close ones.** So the
    standing rule is escalation: an alarming cell is a **trigger for a census,
    never a finding**, and no sibling cell from the same run may be quoted as
    support for it.

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

**44. A pre-registered branch fixes the DECISION, not the validity of the action
it prescribes — check the prescription before you spend on it.** (alice) Her
registered rule said a measured share in one band meant "re-site the mechanism
here". The band fired, and executing it would have been wrong: the proposed site
offers 79 opportunities a game against 1,884 at the site that had *already*
failed — 24× smaller than the thing it was meant to rescue. Pre-registration
binds you against rationalising a result after seeing it; it does not oblige you
to spend games on a prescription that evidence you already hold refutes. Fire the
branch, check the prescription, and **record why you are not executing it** —
otherwise a registration becomes a licence to do the wrong thing on schedule.

    **And when two of your own numbers disagree by orders of magnitude, trace
    them instead of picking one.** Hers disagreed 900-fold — a logged "fires 4
    times a game" against a probe's 3,774 — and they reconciled *exactly*: the old
    figure was the tail of a funnel (691 runs → 79 with both candidates legal → 4
    where they differ). She nearly filed a correction against a number that was
    right, and the reconciliation turned out to be the refutation of her own next
    step. The disagreement is usually more informative than either figure.

**43. A relationship measured under your current policy is an equilibrium of
that policy, not a property of the game.** (carol) She measured, correctly and
with replication, that tiles converted from enemy ground are lost 2.7–6.4× more
often than others — then built a policy to stop converting them. The measurement
did not survive its own intervention: those tiles are lost more often *because*
they sit where the opponent is active, so a policy that stops contesting that
ground lets the front advance and drags down the retention of everything else
too. The number was a joint product of both policies, and she had read it as a
fact about a tile's origin.

    Her own framing is the one to keep: this is the denominator confound one
    level up. **There the treatment moved the divisor; here it moved the
    conditional.** Before you act on a rate measured from your own replays, ask
    what in that rate is downstream of the behaviour you are about to change —
    and if the answer is "most of it", the measurement can motivate a hypothesis
    but cannot price it.

    **And a zero dose tests REMOVAL, not reduction.** (same iteration) She dosed
    a term she had called "unpriced" to zero, and the zero arm was not outscored
    but *ended early* — the term was the only brake her bot had on the opponent's
    win condition. Before zeroing a term, ask what it was doing that you never
    measured; the question is free and the answer here cost one arm.

**42. The bot's own DECISION statistics are the most tempting and least
trustworthy secondaries.** (carol) Twice in her own log a quantity the bot
computes in order to choose its next action moved enormously while the outcome
went the other way: one proxy ran 0.0% → 49.0% across a dose ladder with a flat
screen, and the bot's internal "value" of an action rose 52% against a screen of
−8/−4. Her diagnosis of why she keeps reaching for them is what makes this a rule
— **they are free, already instrumented, and cheap in bytecode, and they were
selected for being cheap to compute, never for correlating with winning.** They
are excellent manipulation checks: they prove a knob moved. They are not evidence
the movement was worth having, and a dose response in one is not a dose response
in the outcome.

    **And re-derive a CLOSED constant when your architecture moves, not just a
    live one.** (carol) Her own accept invalidated a closure's stated basis: a
    floor she had closed as "the bot is nowhere near it" went from blocking 1.2
    turns per fire to 6.7, because the accept tripled the population the floor
    applies to. A closed direction's *reason* can expire while nobody touches the
    direction — and the thing most likely to expire it is your own last accept.

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

    **Used deliberately the next time, it paid twice in one run.** Her treatment
    moved a quantity +6.4% where the bar wanted a 15% fall; the null arm — two
    byte-identical bots — moved it ±7.7%, so the effect was inside the noise, and
    without that number "+6.4%, the mechanism runs backwards" was the confident,
    publishable, wrong reading. The second payment came free: **the treatment arm
    went 4–2 and the null arm also went 4–2**, which turns "a 6-game score is
    worth nothing" from an intuition into a measurement.

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

    **Run the funnel BEFORE the build when the mechanism has that shape, and
    price the RESOURCE rather than the opportunity.** She later recognised a new
    direction as the same animal — a unit with a capability that must be *next
    to* something on a turn it has nothing else to do — and reordered her own
    registered plan to put the funnel first, which is the order that would have
    saved the earlier lever. The funnel then passed narrowly (2.23% against a
    2.00% bar set beforehand) and she recorded the margin, not just the verdict.

    Pricing caught the deeper error, in her own registration one screen old: she
    had written the mechanism was "non-diverting by construction" because it
    fires only on turns whose action went unused. **The turn is free; the paint
    is not.** At 5 paint per attempt and 698 opportunities a game, the naive
    version consumes 70% of the unit-spawn budget for the binding resource — not
    a mechanism but a rewrite of the economy, and the family that had already
    lost her four iterations. An opportunity being free does not make the action
    free: price every resource it consumes against the binding budget, not only
    the one it obviously spends.

    **Measure the denominator the mechanism will actually see — at the exact
    call site the code will live at, not a superset of it.** (alice, stating it
    as a rule after the third instance.) She measured a choice set over *all*
    movement-ready turns, then installed the mechanism inside a single movement
    path, and never measured that path's share of movement. Her two earlier
    versions of the same miss: one priced a unit's *surplus* and not its
    *adjacency*; another priced an *opportunity* and not the *resource* it
    spends. Each time the pre-check was honest about a population the code would
    never meet. Run the funnel where the branch lives.

    **One level deeper: the site must be one where a DECISION exists**, not
    merely where the code runs. Her follow-up counter found 64% of entries into
    the movement path follow an already-open heading, with no choice at all — so
    the 44.8% "a real choice exists" she had passed her bar on was measured over
    *hypothetical* moves rather than over decisions the bot actually makes.

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

**37. Enumerate the CANDIDATE SET before building anything that selects, ranks
or remembers within it.** (bob and alice, same day, different lineages) He built
a memory mechanism to recover targets his units were missing, and the registered
secondary showed the arm identical to the exact zero arm **to three decimals**:
recall can only return a target already sensed, and the ones he misses are the
ones no unit ever came within sensing range of. Memory cannot reach what was
never seen. She had killed a *ranking* version of her own mechanism before
writing a line, because on all 6,424 relevant turns the choice set contained
**exactly one** item — every dose would have been byte-identical to zero.

    **Close on a BOUND, not a point estimate, when the measurement is a proxy.**
    (bob, applying this entry to his own next idea before writing a line of it)
    His proxy — "the mirror target was already marked" — is a *lower* bound on
    "the information was available", so the true reach lies somewhere in
    [31.5%, 100%], far too wide to close on directly. He doubled the measured
    value and found the direction still worth under 4 wins out of 50, below even
    his replicate band, so the closure does not depend on the proxy being tight.

    **And keep "too small" separate from "inert".** His previous iteration was
    structurally impossible; this one works and is merely undersized. Conflating
    them either retires a working mechanism or keeps re-attempting an impossible
    one — and their re-open conditions differ completely: a changed bar or a
    cheaper delivery for the first, nothing at all for the second.

    Same failure, opposite directions, and both were knowable from the source in
    minutes: ask what the set contains in the cases you care about. If it is
    empty or a singleton there, no policy over it can help, however good the
    policy is. The corollary is the useful half — an empty candidate set means the
    defect is **acquisition** (exploration, reach, arrival), not **policy**
    (choice, order, memory), and those are different iterations with different
    gates.

**39. Registering WHAT TO MEASURE is not registering WHAT WOULD KILL IT.**
(alice) She registered a pre-check's measurement and no threshold, and noticed
only once the number was on screen. Every pre-check of hers that produced a clean
verdict that day had a bar written first — one failed at 1.2%, one passed 2.00%
at 2.23%, one closed at a registered 50% — and this one could produce no verdict
at all. Her handling is the rule: **claim no pre-registered pass, invent no bar
with the number visible**, offer the value for comparison only ("roughly 4× the
threshold I last accepted as sufficient"), and register the bar for the next
stage before that stage exists. The two halves feel identical while you are
writing them, which is exactly why the omission survives a careful session.

**38. Every registered band needs a QUANTIFIER, and the branches must partition
the space.** (bob) He wrote a primary as "at r100 / r200 / r400" — all of them?
any? at least two? — measured 15.1 / 14.6 / 10.2 against a 15% band, and the
observed case fell between his own branches for the **third time**. He recorded
it as a habit rather than an accident, which is the right diagnosis: an
unquantified band reads as complete and is not. Write "all three", "any one",
"at least two"; then check that every possible outcome lands in exactly one
branch. Each of his three misses cost nothing only because something else
happened to agree, which is luck rather than design.

**36. When you establish that X at round R predicts the outcome, PLOT X PAST R
before you build anything.** (alice) She established early that the tower leader
at round 300 wins, and then for dozens of iterations measured towers only *at*
round 300 — while the curve that actually decides those games happens afterwards.
Asking a question she had never asked (*when I lose, was I ever ahead?*) showed
**48% of her losses are games she led at r300**, and tracing them showed her tower
count peaking and declining in six of six while the opponent's rose monotonically.
The "coverage collapse" her log had carried as unexplained for twenty iterations
is downstream of tower loss, not a paint problem — so every mechanism she had
ever aimed at it was aimed at the wrong variable, because the collapse was only
ever visible to her as a paint curve.

    The trap is subtle because the predictor is *correct*: the leader at R really
    does win. What the snapshot cannot show is what happens to the leader
    afterwards, and "we were ahead and lost" is a completely different failure
    from "we were never ahead". Plot the master variable across the whole game,
    and register the fork — a decline in the quantity itself versus a decline in
    what it produces — before you trace, because they are different defects with
    different fixes.

**21. Simulate the null before you trust a bar — especially for any statistic
built from a max, a best-of, or an argmax.** (alice) Her pre-registered bar of
100 sat *below* what best-of-8 noisy sectors produce with no structure at all:
about 200 per mille of pure upward bias. The bar could not have rejected
anything, and the first screenful duly reported "emphatically passes". She voided
it rather than substituting a new one mid-flight. Selection statistics are biased
upward by construction, so the bar has to clear the bias, not zero — and the
cheapest way to find the bias is to run the same statistic against data you know
has no structure.

    **But ask what the null is a null OF before you reuse it — the same
    simulation can invert its meaning when the estimand changes.** (alice, one
    day later, correcting her own entry.) She reran that null on a
    similar-looking statistic and the observed value sat *below* it; her first
    instinct was "selection artefact, discount it", and that was wrong here. The
    earlier statistic was a **prediction** about future turns, where the estimate
    need not persist and the winner's curse bites fully. The new one is a choice
    among tiles the unit **occupies on the next turn**, where the value is
    *realised* rather than predicted — so selecting the minimum of N is a
    mechanical gain, not a bias, and a null matching the observed says only that
    the field is spatially random at that scale. Same statistic, same simulation,
    opposite meaning. **Selection over realised values is real; selection over
    predicted values is curse.**

    Better still, she chose a statistic that needs no null at all — a spread test
    (`max − min ≥ 1`) is unbiased where a best-of is not — and noted that passing
    44.8% against a 25% bar is a different kind of pass from squeaking 2.23% past
    2.00%, rather than recording both as "passed".

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

    **A figure in your log carries the population it was measured on.** (alice)
    She justified a direction with a delivery rate from her own log — and the
    figure was measured over *all* unit types at two sampled rounds, while the
    population she was about to build for reads 34.0% rather than 53–65%. Not a
    contradiction and not fatal, but she quoted it because it was already written
    down rather than because it answered her question. A number and its
    population have to travel together, or the number outlives the conditions
    that produced it.

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

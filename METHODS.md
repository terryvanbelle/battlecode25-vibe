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

**2. Price the mechanism in the units of the gap before you screen it.** (bob)
Not "did it help" but "how much of the deficit can it possibly close". He
measured a mechanism's effect at +1.7 per-mille against a +16 per-mille
requirement and closed the direction **on magnitude rather than on power** — a
null that cannot be dismissed as an underpowered run, and which no larger sample
would have overturned. He also declined an 88-game census he had registered, on
the grounds that it would resolve a ±2-win effect whose mechanism was 10× too
small, and recorded the decision as a change rather than dropping it silently.

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

**18. When a session ends mid-question, leave the resume point machine-checkable.**
All three now do a version of this, and the sessions that recover cleanly are the
ones whose in-flight work was described by run-id and gate rather than by
intention.

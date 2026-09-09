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

## Housekeeping

- The git INDEX is shared between all three agents; use `carol-tools/commit.sh` (or
  `tools/agent-commit.sh`). → *"The git INDEX is shared"*
- Superseding in place must LOOK superseded. → *"Superseding in place must LOOK superseded"*
- The frozen roster un-saturates itself. → *"The frozen roster un-saturates itself"*
- Reading a running gauntlet is free information. → *"Reading a running gauntlet"*
- A cache keyed on a MUTABLE path serves stale answers silently. → *"A cache keyed on a MUTABLE path"*

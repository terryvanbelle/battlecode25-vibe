# Alice — LEARNINGS.md (index)

What I would tell a fresh session before it touched anything. **One or two lines
per lesson**; the full entry and its evidence live in `LEARNINGS_ARCHIVE.md`,
which is grep-only and must never be read whole:

    grep -n "<pointer text>" LEARNINGS_ARCHIVE.md
    sed -n '<line>,<line+60>p' LEARNINGS_ARCHIVE.md

Pointers are heading fragments, not line numbers, so they survive edits to the
archive. `TRAINING_LOG.md` remains the evidence of record and the home of the
**closed-directions ledger** — grep that ledger by hypothesis name before
opening any direction (it has caught a re-open in progress three sessions
running).

Split 2026-09-09: this file was 2,971 lines and was read in full at every cold
start, ~40k tokens of the ~77k that mandatory re-reading cost per session.

---

## A. Game facts my lineage has measured (BC25)

- **Paint is the binding resource; chips are not, and have not been since iteration 2.** Chip mountains of $113k–$205k in every early game. -> `"The economy of Battlecode 2025"`
- **Coverage is a stock under attack, not a running total.** It peaks and *decays* (562‰@r500 -> 467‰@r2000) while the army grows. Never reason "we paint X/round so coverage grows". -> `"Coverage is a stock under attack"`
- **65–100% of unit deaths are paint starvation, not combat.** A unit at 0 paint takes −20 HP/turn and cannot act. -> `"The real degeneracy: a starvation treadmill"`
- **The absorbing state — the most expensive bug this lineage has had.** Tower paint funds spawning; a soldier costs 200, a mopper 100, income is 5–15/turn. So a drained tower can only ever afford the cheap unit and never saves back up. **Confirmed size-conditional 2026-09-09**: alice's towers average 145 paint each on small maps (below the soldier price) and 221 on large. -> `"The absorbing state"`
- **Towers are the master variable.** The r300 tower leader wins 13/14 in self-play and 79–81% cross-lineage. -> `"towers are the master variable"`
- **Bytecode is not a constraint for this bot.** Measured, not assumed. -> `"Instrument hygiene"`
- **A pinned resource is only pathological if capacity sits idle behind it.** The discriminator, because I misread a pinned curve once. -> `"A pinned resource is only pathological"`
- **The board SATURATES by r200–400** — 0–4% of paintable tiles unpainted, literally 0 on some maps. There is no frontier to walk to, and every remaining per-mille must be taken from enemy paint. -> log, `"THE FRONTIER DOES NOT EXIST"`
- **The conversion channel is the mopper, not the splasher** (691 unpaints vs 62 splashes on one map), and 26–38% of mops are handed back within **1 round** by an adjacent enemy. -> log, `"The conversion census"`

## B. Retractions — do not re-adopt these

- **RETRACTED: "unit population has an interior optimum set by a clumping tax."** -> `"unit population has an interior optimum"`
- **PARTLY RETRACTED: ruin supply does NOT cap towers.** The master-variable half stands; the "supply not discovery" half was inferred purely from self-play, where both sides shared the defect. Killed by the first round-robin. -> `"ruin supply does NOT cap them"`
- **PARTLY RETRACTED: the soldier paint decomposition was wrong by an order of magnitude.** Movement is still exploration; the "~8 of 200 paint becomes tiles" claim is false. -> `"the paint"` + `"decomposition below is WRONG"`
- **SUPERSEDED: the old binomial noise bands.** They overstated spread ~2x and made me hedge a real 2-sd accept. -> `"Instrument hygiene"`
- **RETRACTED: "b0 = 0, iteration 19's branch never fires."** It fires on 10.9% of mops; the zero was a 128-mop small-sample artefact. -> log, `"RETRACTS my own"`
- **RETRACTED: `mopSwing` is a 3-tile ground converter.** The method body has **no tile-paint write** — it drains *robot* paint. I costed it from the constant name and reordered a queue around it. -> `"a constant's NAME is not its semantics"`
- **RETRACTED: "my gauntlet cannot see the size axis."** One claim too wide: it cannot see whether the *gap to carol* closed, since both arms are mine. -> log, `"I overclaimed"`

## C. What decides whether a measurement means anything

- **The self-referential blind spot — the most important thing this lineage learned**, and it cost eleven iterations behind a 95.8% self-measured win rate. -> `"The self-referential blind spot"`
- **A replay counter means nothing until you have found its call site.** `MopAction == 0` was guaranteed a priori. -> `"Methodology lessons paid for"`
- **Read the engine, not your own digest of the engine.** -> `"Methodology lessons paid for"`
- **The engine DEBITS before it CHECKS — verify the predicate, not the proxy.** -> `"the engine DEBITS before it CHECKS"`
- **A REPLAY's per-robot state is post-decision by construction**, so it cannot price affordability. -> `"post-decision by construction"`
- **A correlate you measured in a replay is not a predicate a robot can evaluate.** -> `"not a predicate a robot can evaluate"`
- **An instrument that samples positions your current policy chooses cannot price a policy that chooses different positions.** -> `"cannot price a policy that chooses different positions"`
- **An instrument can produce NOTHING and no-finding, and the two are indistinguishable downstream.** -> `"an instrument can produce NOTHING"`
- **A distribution measured UNDER a gate is shaped BY that gate.** To size a threshold you must MOVE it, never read the pile-up it produced. This nearly re-opened a three-times-closed direction. -> `"shaped BY that gate"`
- **An UNSPENT SURPLUS is not evidence of waste** — and my first correction of this was also wrong. -> `"an UNSPENT SURPLUS is not evidence of waste"`
- **A rate pooled over HETEROGENEOUS producers measures specialisation, not shortage.** -> `"HETEROGENEOUS producers"`
- **A counter that goes to ZERO late in a game may be a PHASE CHANGE, not a failure.** -> `"may be a PHASE CHANGE"`
- **A monotone counter is a bug report.** -> `"Instrument hygiene"`
- **An INERT BRANCH is a fact about the BRANCH.** Measure what the turns it fails to serve are actually *doing* — this is the iteration 44 lesson and it cost −58. -> `"an INERT BRANCH is a fact about the BRANCH"`
- **Measure whether the THING the mechanism points at EXISTS, before building the mechanism.** -> `"before building the mechanism"`
- **Three arms failed on one root: the bot had no representation of the thing they all guessed at.** -> `"the bot had no representation"`
- **Measure WHICH guard binds before fixing a mechanism that never fires.** -> `"measure WHICH guard binds"`
- **Enumerate the cases, then COUNT them** — a case analysis has no frequencies in it. -> `"a case analysis has no frequencies"`
- **When a covariate analysis fails twice, stop correlating and go price the code path.** -> `"stop correlating and go price the code path"`
- **Never dichotomise a continuous covariate** — the split invents the effect. -> `"never dichotomise a continuous covariate"`
- **A maximum-per-observation is not a total**, however many observations you add up. -> `"is not a total"`
- **You cannot compare a COMPOUNDING resource to a CONSUMPTIVE one with a per-turn rate.** -> `"COMPOUNDING resource"`
- **An exactly symmetric statistic is a hypothesis about the FILE FORMAT.** -> `"a hypothesis about the FILE FORMAT"`
- **One map cannot size a corpus quantity** — and I made this error inside the session I wrote the warning. -> `"one map cannot size a corpus quantity"`
- **Do not read a dump until its writer has exited.** Partial output is a biased sample of the *early game*: I computed 41% off a partial file whose finished value was 4.1%. -> log, `"caught within minutes"`

## D. Gates, doses and verdicts

- **In a deterministic game the MAP is the unit of uncertainty — never the game.** -> `"the MAP is the unit of uncertainty"`
- **A SCREEN ranks arms; only a CENSUS sizes an effect**, and small effects are where skipping the census tempts most. -> `"only a CENSUS sizes an effect"`
- **A CENSUS is exact** — separate sampling noise from run-to-run noise before calling something unresolvable. -> `"a CENSUS is exact"`
- **Measure your own noise floor, and check its MEAN.** A change with **zero policy content** (a PRNG seed offset) moved my census by **+12 net swept**. Any census bar at +4 would have accepted it. -> `"NO policy content moved my census by +12"`
- **My gate and my floor must be in the same unit** — the audit and derivation. Standing bars: screen (25 maps/50 games) net swept >= +4; census (75 maps/150 games) net swept >= **+12** (2.27 sd on `sd_net_swept = 5.29`). -> `"my gate and my floor are in the same unit"`
- **Swept maps and the head-to-head margin are THE SAME NUMBER**, not two agreeing signals. What sweeps add is D, the count of split maps. -> `"THE SAME NUMBER, not two signals"`
- **SW+SL and SW−SL are different measurements**, and a zero-variance null makes the first look like evidence. -> `"different measurements"`
- **Head-to-head margins DO NOT CHAIN.** Measured at cell level. -> `"DO NOT CHAIN"`
- **A tournament run is not an independent sample** — dedupe on the COMMIT PAIR, not the run id. -> `"dedupe on the COMMIT PAIR"`
- **With a deterministic engine, the SPLIT/SWEEP structure reads a mechanism's firing rate directly.** -> `"reads a mechanism's firing rate directly"`
- **The mechanism can engage exactly as designed and still invert the result.** -> `"Methodology lessons paid for"`
- **A BITE check proves a mechanism ACTS** — it can still invert the sign on the mechanism's own metric. -> `"a BITE check proves a mechanism ACTS"`
- **The arm that improves your metric most can be the arm that loses.** -> `"can be the arm that loses"`
- **A ratio is not a quantity.** Maximising "share of mops that stick" halved the ground held. -> log, `"A ratio is not a quantity"`
- **The CONSERVATIVE dose is not automatically the safe one.** -> `"the CONSERVATIVE dose is not automatically"`
- **A stronger dose producing LESS of the predicted effect is how you catch a noise reading.** -> `"producing LESS of the predicted effect"`
- **A pre-registered criterion may only cite quantities from the run it judges.** -> `"may only cite quantities from the run it judges"`
- **A dose comparison advances only after replication on a DISJOINT map sample.** -> `"Instrument hygiene"`
- **A hand-picked standing map list is an overfitting surface.** Leave `MAPS` unset; resample every run. -> `"Instrument hygiene"`
- **Don't pick the arm that won by less than the noise floor.** -> `"Methodology lessons paid for"`
- **A concentrated regression inside a broad win is a target, not a veto.** -> `"Methodology lessons paid for"`
- **Instrument any pool the change draws on, in the first run.** -> `"Methodology lessons paid for"`
- **Rejections are the cheapest evidence available.** -> `"Methodology lessons paid for"`
- **My gauntlet's resolution collapses exactly where I need it most.** -> `"resolution collapses exactly where I need it"`
- **ROUND-COUNT IDENTITY is not byte-identity** — the tiebreak forges the evidence. -> `"ROUND-COUNT IDENTITY is not byte-identity"`
- **A policy keyed on map geometry needs a map that exercises both branches.** -> `"needs a map that exercises both branches"`
- **A contested quantity sits at an equilibrium — measure throughput, not level.** -> `"measure throughput, not level"`
- **Removing waste pays only when the freed resource is the scarce one.** Iterations 20, 26, 39a each freed a non-binding resource; 44 spent the binding one to buy the non-binding one. -> `"removing waste pays only when"`
- **Pick the run convention that makes the reading unambiguous.** -> `"makes the reading unambiguous"`

## E. Keeping myself honest

- **A bar registered against ZERO is not a bar when the statistic has a noise floor.** "Best of 8 sectors" is a maximum of eight noisy ~9-tile estimates, so it is upward-biased even with no structure at all: the winner's-curse floor was ~200 per mille and I had pre-registered 100. Simulate the null *before* registering the threshold, and void the gate rather than quietly replacing it. -> log, `"my registered bar was void"`
- **An internal consistency check catches instrument bugs that a plausible number hides.** `worst > chosen` is arithmetically impossible; it exposed a probe that recorded 0 for headings pointing off-map and inflated the headroom by ~140 per mille. Build one impossibility test into every counter. -> log, `"an internal consistency check caught a probe bug"`
- **Ask how much there is to COLLECT before asking whether it helps.** Eight games closed iteration 50 on a ceiling (17% of the gap under perfect assumptions); iterations 44–47 each spent a 50–150 game screen to learn the same class of thing. The bound comes from what is available, so no larger sample overturns it. -> log, `"The pre-check paid for itself"`
- **A gate blind to an effect carries no information about it — and section 8 is a pre-check whose trigger is BEFORE BUILDING.** I built a 6-game probe on self-play to explain a gap my own log had already measured as null inside my lineage (rho +0.014, p=0.903). Every pre-registered criterion passed; the probe reproduced the effect's ordering *backwards*, because the effect is opponent-driven and self-play cannot contain it. -> log, `"the direction DEAD, and the reason is my instrument"`
- **Say whether your claim needs the PER-TURN or the PER-LIFETIME number.** Soldier upkeep per turn is 1.7x higher on small maps; upkeep per lifetime is *lower*, because lifetime is 87.8 turns there against 220.0 on large. The two move oppositely and nearly cancel, so one framing looks like a finding and the other is flat. -> log, `"the hidden variable"`
- **A digest is a proxy for the engine, and mine was wrong.** `RULES.md` said the clumping tax ignored adjacent towers; the engine counts them (no `isRobotType()` filter, self excluded by ID only). Now also SIZED: 3.8–17.8% of soldier upkeep — real, and a minor term. -> log, `"adjacent ally TOWERS are taxed"`
- **A lesson written THREE times is not a lesson, it is a missing control.** Install the check where the mistake happens. -> `"a lesson written THREE times"`
- **A retraction is a claim too**, and it shares the assumption that produced the error. -> `"a retraction is a claim too"`
- **"Supersede in place" must ANNOTATE the old entry**, not merely append a new one. -> `"must ANNOTATE the old entry"`
- **Two rules in one document can disagree, and neither looks wrong alone.** -> `"two rules in one document can disagree"`
- **Consistency passes**: two separate sessions found that several of that day's entries were one error wearing different clothes. Run one before trusting a cluster of new lessons. -> `"CONSISTENCY PASS"`
- **Never redirect run output into the shared `/tmp` tree** — a sibling's run interleaved with mine. Use `agents/alice/logs/`. -> `"Instrument hygiene"`
- **The recurring error of this lineage, named:** a real number attributed to a referent wider than it supports. It has appeared at least five times (sparseness-for-size, skipM, the mopSwing constant, the gauntlet-blindness overclaim, b0=0). When a number resolves an open problem on first contact, that is when to check the referent, not when to celebrate.
- **This lineage's failure mode is generating mechanisms faster than it locates defects.** Iterations 44–47 were four mechanisms proposed without a located defect, and all four were rejected. Census before mechanism.

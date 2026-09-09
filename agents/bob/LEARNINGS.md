# Bob — LEARNINGS.md (index)

**This file is an INDEX, and it is the whole of what a fresh session should read.** Every entry is one
line: the operative rule, and the number that finds the evidence. The evidence itself — measurements,
arithmetic, the reasoning that produced each lesson — lives verbatim in **`LEARNINGS_ARCHIVE.md`**, which
is **grep-only and never read whole**:

```bash
grep -n "^## 47\." LEARNINGS_ARCHIVE.md      # find lesson 47, then sed -n '<a>,<b>p'
grep -in "denominator" LEARNINGS_ARCHIVE.md  # search by topic
```

Companion files, and what each is for:

| file | read it | what it holds |
|---|---|---|
| `LEARNINGS.md` | **whole, first** | this index — the live lessons |
| `LEARNINGS_ARCHIVE.md` | **grep only** | the full evidence for every lesson, nothing deleted |
| `CLOSED.md` | **grep, before proposing any mechanism** | the 22 closed/blocked directions + re-open conditions |
| `RULES.md` | whole, first | engine ground truth + standing prohibitions |
| `TRAINING_LOG.md` | **tail only** | the chronological record; where I left off |

> **The single highest-value habit in this file**: before proposing a mechanism, `grep CLOSED.md` for its
> words, then check the arithmetic of its ceiling against the gap it is aimed at. Both are cheap. This
> lineage spent 24 games re-deriving a defect its own ledger already held (#74), and has closed four
> directions for **zero games** on sizing alone.

---

## A. Denominators, rates and referents — the error class that has cost me most

- **1.** A rate is a fraction; get the denominator wrong and everything downstream is wrong. Wrong for 41 iterations. → #71
- **2.** Check a rate against its own **hard ceiling** before believing it: a per-turn action rate above 1.0 is a broken denominator, not a finding. → #81
- **3.** A rate whose numerator and denominator count **different populations** is not a rate. → #79
- **4.** A suspicious denominator is not automatically a bad one — ask whether the excluded events *could* have been positives. If they could not, excluding them is the right partition and sharpens the estimate. → #83
- **5.** Do not optimise a ratio whose denominator **the mechanism itself controls**. → #76
- **6.** Check whether your second metric is a **function of** your first before citing them as two pieces of evidence. → #14
- **7.** Independence of the *derivation* is not independence of the *referent*. → #26
- **8.** The wrong referent is easy to pick twice in one session on the same quantity. Name what a number is *about*, out loud. → #73, #34
- **9.** "Denial units run at ~1% of capacity" — **RETRACTED**, a dead-unit denominator. Do not reuse the figure. → #47
- **10.** No tournament-derived quantity measures **my** bot; the three win counts are conserved and sum to 450. → #34
- **11.** A statistic that flags the whole population is not a detector. → #53
- **12.** Two headline statistics were pooled over opponents whose strength was **changing**. → #54

## B. Gates, sampling, noise and what a margin can carry

- **12b. NEW.** **A measurement's window is part of the measurement.** I carried iteration 44's r≤200 composition (83.5% soldiers) as if it were whole-game (it is 48%), inflating a denominator 1.7x until two instruments were made to disagree. → #89
- **12c. NEW — the sizing rule that replaces the theoretical one.** **1.0 paint/unit-round saved ≈ 25 wins/50, and it SATURATES** (iter49 saved 0.240 → +6; iter50 saved 0.285 → +6). So +10 needs ≥0.40 saved, and the largest saving in bob's whole budget (crowding's avoidable 0.600) already saturates at +6 — **no paint-saving movement mechanism can reach +10**. The old "1 paint ≈ 0.15 tiles" theoretical rate was ~8x optimistic. Check the next idea against this before building. → #90
- **13.** My 50-game arm cannot resolve anything smaller than a **~14-point** effect — which is most of what I test. Size the effect against the instrument first. → #37
- **14.** The noise floor is binomial, and it is nearly **all map sampling**. → #43
- **15.** Swept-map counts are **not** noise-immune: 5–6 each way is what pure noise looks like. → #44
- **16.** The margin and the swept-map count are the **same number** (`wins − N = swept − swept-against`, exactly). Citing both is citing one number twice; what the sweep adds is **D**, the split count. → #25 (supersedes the "nearly implied" form in #15)
- **17.** Head-to-head margins **do not chain**. → #21
- **18.** Two numbers cannot estimate a standard deviation — 75 paired maps can. → #48
- **19.** An accept gate against your predecessor is **blind to interactions** with what the predecessor already carries. → #15
- **20.** A 2-game margin will buy you a mechanism story; replication costs nothing and refutes it. → #32
- **21.** Distinguish a **plateau** from a **peak** before claiming an optimum. → #33
- **22.** A dose sweep is only informative if the knob actually controls the damage. → #40
- **23.** The gate's unit belongs in its **name** (`wins_above_half`, not "margin"). → #51
- **24.** A void condition must be registered against an instrument **the arms actually carry**. → #77
- **25.** Pre-register readings for PASS, NULL *and* NEGATIVE — I once registered only the first two and got the third. → #59
- **25b. NEW.** **Register the PRECEDENCE between a primary and its control, not just both** — iteration 52's primary cleared by 1.4% while its comparative fired the other way, leaving me free to choose. And **say whether a primary measures a CEILING or an achievable quantity**: a ceiling threshold that clears narrowly is evidence *against* the direction, since the achievable part is strictly smaller. → #92
- **26.** Set the trigger from **the decision it forces**, not from the outcome expected. → #80 (I called three branches exhaustive and the observed case fell between them)
- **27.** Pooling across tournaments is invalid here (the engine is deterministic; games reproduce exactly). → #62
- **28.** A behaviour-preserving commit defeats a commit-hash duplicate detector — deduplicate on **games**. → #75
- **29.** An ID-seeded RNG means this lineage has never run a true mirror test; a mirror null's zero variance is **structural**, not evidence the instrument is quiet. → #42, #36
- **30.** A PRNG draw inside a conditional makes that conditional part of the behaviour — an "exact zero arm" must not consume RNG differently. → #35, #52

## C. Instruments lie plausibly — how mine have failed

- **30b. NEW.** **The DIRECTION of an instrument's error matters more than its magnitude, and you must establish it BEFORE you look.** An error running against your hypothesis turns a two-sided error bar into a one-sided bound: 2,484 team-frames, zero with the paint reconstruction under-counting, so every territory figure was a lower bound and the bias could not be why anything cleared. → #91
- **31.** Instrument bugs produce **plausible** output. A number that looks reasonable is not a passing test. → #8
- **32.** My own instrument reported a silent **zero** and only a sanity read caught it. → #70
- **33.** A greedy regex made every row of a probe table report the **wrong team**. → #45
- **34.** An identity check can fail silently by being **stricter** than the property it tests. → #41
- **35.** `javap` with stderr suppressed reported "no such method" when the real cause was **no JDK on PATH**. Never suppress stderr on a probe. → #57
- **36.** `setIndicatorString` is **one slot per robot per turn**; the last writer wins silently. → #72
- **37.** A pre-registered trigger is only as good as its **proxy**. → #10
- **38.** The map that suggested the hypothesis is the **worst** map to size it on. → #22
- **39.** Check that a number lies in its own **logical range**. → #23
- **40.** Date-check a resume context's git snapshot before believing it. → #61
- **41.** **Run the discriminating case** even when the source reads like a confession — I reported a real bug with a false symptom, and the symptom I named was untestable. → #63, #27
- **42.** The refuting column was already in the trace I published as confirmation. → #50
- **43.** Measure the quantity that decides the regime, not a proxy opponent for it. → #64
- **44.** A missing capability is invisible to every instrument except a **scheduled sweep** (an API sweep found 24 never-called methods). → #30, #38
- **45.** The stall trigger works, and it works *because* it is a trigger. → #66
- **44b. NEW.** A secondary accumulated over a **whole game** is a post-outcome quantity whenever the treatment changes the win rate: iteration 47's "conversion −16%, dose-monotone" was **entirely** the arms losing more, and vanished (+0.9%/−1.2%) when windowed to r≤200. Large, monotone, mechanistically plausible, sign-agreeing — and an artefact. **Read secondaries in a window that closes before the games do.** → #87
- **45b. NEW.** A sampling stride is not free just because the counters are cumulative: `ReplayDump --every N` silently drops up to `N-1` rounds off each game's **end**, and the loss scales with game length — the one bias that would have faked iteration 47's result. **Use stride 1.** Test the invariant your own script claims. → #85

## D. Mechanisms: what they cost, and what pays for them

- **46. THE CENTRAL ONE.** State, **before building**, which term of the objective's decomposition the mechanism moves and **which term pays**. If the payer is the term you are already worst at, it is a transfer, not a gain — and a transfer priced in the wrong units looks like progress right up to the gate. → #82, #76
- **47.** A **verified mechanism is not a verified benefit**. Iterations 43 and 45 both engaged perfectly and lost. → #17
- **48.** A candidate can *win* a game with its mechanism completely **inert**. → #12
- **49.** Local wins do not compose into global progress. → #13
- **50.** Relaxing the **binding constraint** pays where optimising around it does not. → #11
- **51.** The binding resource is a property of the **map**, and it inverts. → #31
- **52.** A waste can be the **efficient** behaviour; "idle" has three meanings, the third being *structurally incapable*. → #9, #17, #24
- **53.** Measured per-unit waste in a **cohesive formation** is not recoverable by making units individually less wasteful. → #49
- **54.** Reachability means the **choice set**, not just the guard. → #19
- **55.** A floor constant on a **threshold good** manufactures zombies (`PAINT_FLOOR` parked soldiers one point above the band that kills them). → #20
- **56.** A gate that **converts** instead of delaying inverts the feature it guards. → #56
- **57.** Closing the **fix** is not closing the **defect**. → #29
- **58.** A heuristic that *nominates* a candidate is not evidence about it. → #16
- **59.** My entire opponent pool cannot produce the games I lose. → #55

## E. Engine ground truth (BC25 3.1.0) — verified, not inferred

Numbers live in `RULES.md`; these are the ones that changed a decision.

- **60.** Engine ground truth beats inference — `javap` the pinned 3.1.0 jar via `tools/engine-jar.sh`. → #2
- **61.** Every game is decided by **paint coverage**; elimination essentially never happens. → #18
- **62.** A **soldier cannot paint over enemy paint**, and the wasted attack is invisible to every counter. → #78
- **63.** The engine **never cleans up marks**, and neither did my bot. → #65
- **64.** `disintegrate()` is a pure suicide with no refund. → #67
- **65.** Every map in the corpus is symmetric — but only **27 of 75** the way you would guess. → #28
- **66.** Symmetry and fixed-order decisions are this lineage's recurring bug class. → #3
- **66b. NEW.** **A condensed rule is a cache, and mine went 47 iterations without invalidation.** `RULES.md`'s paint-penalty digest hid that crowding is charged on your **own** paint and that `crowd` counts **towers** — i.e. it hid the largest single paint sink in the game (~24,900/game). **Re-derive a digested number from the bytecode as the FIRST step of any mechanism that depends on it.** → #88
- **67. NEW (iteration 47).** The **low-paint cooldown tax is exactly zero for soldiers**. `num` tops out at 19 (< 20) at X=1, so one decrement always clears it. Real only for MOPPER (3→5 turns/action) and SPLASHER (5→9) — both of which already run far below their untaxed ceilings. → `CLOSED.md` #22

## F. Where bob actually stands (the strategic state, and it is nearly closed)

- **68.** Bob's entire deficit is **small maps**, and the tournament said so all along. → #68
- **69.** The round-30 cliff and the small-map deficit are the **same phenomenon**. → #69
- **70.** `tiles = acts × conv`. **`conv` is closed from both ends**: bob's redundant repainting is exactly 0 of 2,377 classified repaints, and answering alice's 47 unpaints/game with moppers costs more than it returns. → #84, #83, `CLOSED.md` #19/#21
- **71.** **Composition is a local optimum in both directions** — iteration 20's splasher peak is interior at 2 of 5 slots, iteration 45's mopper harm is monotone. → #82, `CLOSED.md` #20
- **72.** So **`acts` — total paint actions per game — is the only live term**, and it has exactly three sources: more units, units acting more often, or units **living longer**. Acting-more-often is now closed too (#67), so **living longer is the remaining route**. 89% of bob's deaths are starvation (8.2 of 9.2 per game). → #82, iteration 47
- **72b. NEW — the model correction.** **`acts` was never the binding constraint; PAINT is.** All three sources of `acts` are now closed (composition #20, acting-more-often #22, living-longer #23) and each bottomed out in a fixed paint budget. Feeding a unit costs the paint that builds one: `tower.getPaint() >= 200` gates every SOLDIER. → #86, `CLOSED.md` #23/#24
- **72c. NEW — where to look next.** Bob issues ~59,460 paint to units per game and converts only ~**38%** into paint actions; the residual is ≈2 paint per unit-round, the size of the engine's per-turn penalties (−1 neutral, −2 enemy, +1 per adjacent ally, doubled in enemy territory). Spending less draws on **no** tower pool — the one re-open condition on #23. **This 38% is an accounting estimate, not a measurement.** → #86
- **72d. NEW — bob is CHIP-POOR, and the trace everyone cites is superseded.** Median chip balance reaches the L2 upgrade trigger (6,500) only ~r800 and the L3 trigger (9,000) never before r1100 — past most games' end. Iteration 3's "327k chips unspent at r2000" predates the upgrade path it motivated; **re-measure before any "bob has spare chips" argument.** → `CLOSED.md` #28
- **73.** Sizing anchor, for any future mechanism: the small-map deficit is **91 tiles**; an extra soldier-round is worth **≤0.265 tiles**; so closing it needs **≈+343 soldier-rounds/game (+28%)**. Every mechanism tried before iteration 47 sized at **2–5%** of that.

## G. Process and hygiene

- **74. Grep your own ledger before proposing.** I spent 24 games rediscovering a defect my own log already held. → #74
- **75.** **Supersede in place, do not delete** — a withdrawn rule was load-bearing for whatever was decided while it stood. Mark it `[SUPERSEDED <date> -- see §N]` on the line, so the reader meets the correction before the claim. → #26
- **76.** Marginal accepts are where drift enters. → #13 (partially superseded by #21: iteration 18 was the opposite of marginal and drifted anyway)
- **77.** Three closures in one day is a reason to write down **what would make me distrust them**. → #60
- **78.** A consistency pass on my own doctrine caught a rule doing work it cannot do. Re-read the index for load-bearing claims periodically. → #58
- **79.** Write the mid-flight revision **before** the verdict, with the gate frozen beside it — that is what stopped iteration 45's motivated re-sizing from absorbing the result. → TRAINING_LOG, iteration 45
- **80.** A rejected iteration is a delivered result. The highest-value outputs here include a hypothesis killed for three games, a mechanism shown an order of magnitude too small, and a control that inverted a headline finding. → #59, #32, #60
- **81.** Instruments and measurement discipline, the originals. → #1, #4, #6
- **82.** Strategy facts about this game, and the iteration 5–7 block. → #5, #7
- **83.** I designed a protocol around **who owns the radio** rather than who holds the information. → #39
- **84.** Churn and causality have different **flip signatures**, and both are now measured. → #46

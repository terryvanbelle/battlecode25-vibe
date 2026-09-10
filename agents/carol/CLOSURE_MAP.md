# carol — CLOSURE MAP

**State at time of writing:** `src/carol` = `BUILD "i45a"`, unchanged since the iteration-60 accept
(commit `3610230`). Snapshot copy: `src/carol_iter45`. Every axis and design premise below is
closed or blocked. **This document, not the 22,000-line training log, is where a successor starts.**

Iteration 59's rewrite cost a full session; iteration 77's cost **8 probe games** — the difference
was that 77 began from a committed survey. This is that survey, generalised.

---

## 0. How to read a closure

A closure is not "I tried it and it didn't work". Each entry below records a **kind**, because the
kinds carry different licences:

| kind | meaning | what re-opens it |
|---|---|---|
| **measured-and-small** | built, measured, effect real but below the bar | a larger bar-relative effect, or a changed bar |
| **oracle-ceilinged** | *no* implementation can clear the bar — the perfect version was priced | only a change to the bar or the regime mix |
| **refuted-on-value** | reachable, and not worth reaching even if free | a change to what the mechanism is worth, not to how well it is built |
| **structurally-impossible** | the engine or the architecture forbids it | a new primitive |
| **feasibility** | the API does not exist | a new API or a comms channel |
| **gate-unimplementable** | the mechanism only pays under a conditional that cannot be built | a buildable conditional |
| **excluded-by-measurement** | not the deficit; the quantity was already healthy | a regime where it is not healthy |
| **blocked** | *not closed* — a prerequisite is unmet and named | the prerequisite |

> **A closure says an implementation failed. A ceiling says no implementation can succeed.**
> Two of the axes below carry ceilings at or below the accept bar. That is the difference between
> "I am stuck" and "this design cannot get there", and it is the load-bearing result of the project.

---

## 1. The design premises — 6 of 6 closed

Enumerated *as architectures*, after twenty mechanism axes had been enumerated one level down. Each
was checked against the free upper bound first: is it already refuted by a rival's behaviour or by
my own past experiment?

| # | premise | cost | closure kind | the number |
|---|---|---|---|---|
| 1 | drop the dedicated refill trip, keep opportunistic top-up | one constant (`REFILL_LOW=0`) | **refuted** | that *is* the iteration-60 zero arm; D3 beat it by **+26** |
| 2 | raise allocation toward the 125/1,000r ceiling | one constant | **oracle-ceilinged** | **+7 = 27% of the bar** (iteration 69) |
| 3 | **high-production forward attrition** — 1 and 2 *together* | rewrite | **refuted-on-value** (production half) + rescue route measured | see below |
| 4 | soldier-primary | rewrite | **refuted** | iteration 59, **−5.71 sd** |
| 5 | mopper ferry logistics | rewrite | **structurally-impossible** (dominated) | mopper carries **1/3** a splasher tank; killed at rung one, 0 games |
| 6 | comms-coordinated posture | rewrite + unbuilt primitive | **blocked → closed** | no traced deficit, and the memory prerequisite is unmet (see axis 20) |

### Premise 3 in full — it was the only survivor and it is now closed

Its shape was the reason a rewrite track existed: **both halves are individually refuted, but each
refutation was conditional on the other half.** Dropping the tether alone loses 26 games *only if you
cannot replace the units it strands*; producing at the ceiling is worth little *only if the units are
recalled anyway*. That is destructive-pair logic and it is legitimate.

**Production half — refuted ON VALUE, not on reachability.**
- Allocation driven to a **32× dose** (mix 12.7:1 → 0.4:1, the largest dose this project has applied
  to anything) reaches **62 splashers/1,000r against a 125 ceiling — half the headroom, at maximum dose.**
- Returns diminish **8× inside the ladder**: K=8→K=4 bought +7 units for +6 margin (0.82/unit);
  K=4→K=2 bought **+19 units for +2 margin (0.10/unit, 0.28 sd)**.
- Extrapolating the remaining 63 units at the **marginal** rate — the right estimator when you start
  from the top of a measured range — gives **+3 census margin**; at the average rate, **+9**.
  Against a **+26** bar. The arm's own directly measured census value is **+6 at 0.7 sd**.

**Posture half — its refutation stands unrescued, and the rescue route is MEASURED.**
The two halves are coupled through one tower needing **400 chips AND 300 paint at the same moment**.
Forward posture removes refill trips, which drain tower paint — that is the pair's funding source and
it had never been measured. Matched window (rounds 1–522, leavemealone, same opponent):

| | chips ≥ 1600 | a tower ≥ 300 paint | **both at once** |
|---|---|---|---|
| incumbent, tether ON | 38.3% | 71.5% | **21.1%** |
| `carol_r2`, tether OFF | 10.3% | **78.2%** | **0.2%** |

- The funding source is **real and small**: **1.09× relief**, against the **2.02×** the pair requires.
  Granting it in full closes **9% of the headroom**. Required 100%, measured 9%.
- **The halves actively fight**: joint affordability collapses **21.1% → 0.2%**, because splasher-first
  spending drives chips down while the tether change frees paint. **Each half exhausts the resource
  the other relieves.** This is a stronger negative than mere non-composition, and it is the measured
  mechanism behind iteration 77's stage A producing 12 splashers against a control's 43.

> **Premise 3 closes entirely.** Note the discipline that got there: the production numbers were all
> measured *under the tethered posture*, and the pair claims production is worth more *when posture is
> forward*. Carrying them across that policy change unchecked would have been the iteration-67 error
> (cost −22/−14/−46). The hinge was measured, not assumed.

---

## 2. The mechanism axes — 21 entries

The log calls this "twenty axes"; it counts the six-member coverage family as one. Listed here as
they fall.

### Economy and production

| axis | kind | the number | re-open condition |
|---|---|---|---|
| **allocation / unit mix** (`SPLASHER_EVERY`) | oracle-ceilinged, then refuted-on-value | oracle **+7 = 27% of bar**; census **+6 at 0.72 sd** against a +9 bar; large bucket −4 | only if the binder changes — see misreadable fact 7 |
| `MONEY_MOD` (tower type mix) | structurally-impossible | integer optimum: a `min()` ceiling cannot be raised by a knob that trades its two terms. **0 games** | closure was corpus-pooled; a *regime-specific* question is a legitimate re-open, and that is a different act from liking the hypothesis |
| `CHIP_RESERVE` / the spawn gate | measured-and-small | not the fixed point; equilibrium sits **3.5× above** realised behaviour. The gate reads its own fuel | as above |
| soldier ceiling (standing-count cap) | **feasibility** | no robot-count API on `RobotController`, and carol has no comms. **0 games** | a comms channel |
| `REFILL_LOW` (D3 latch) | measured-and-small, bracketed both sides | flat over [10,50]; degrades above (100 → 19, 150 → 12 of 50) | none |

### Targeting and firing

| axis | kind | the number | re-open |
|---|---|---|---|
| splash scoring weights (`W_EMPTY`:`W_ENEMY`) | **closed for good** | 2:3 incumbent beats 3:1 (**−22**), 5:1 (**−14**), 3:0 (**−46**) | none — enemy-targeting is the only brake on the opponent's 70% win |
| splash targeting as a family | closed, re-open **spent** | the iteration-66 re-open condition was *satisfied* (retention differs 2.7–6.4×) and the mechanism built on it failed at every dose — the retention gap is **policy-dependent, not exogenous** | none; the re-open is used up |
| `SPLASH_MIN_SCORE` | measured-and-small, bracketed both sides | flat at 4 (+0), harmful at 14 (−8) and 20 (−4); incumbent 8 sits at the plateau edge | none |

### Denial

| axis | kind | the number | re-open |
|---|---|---|---|
| mopper supply / paint denial (`MOPPER_EVERY`) | closed decisively | **−16/150 vs bobf (−3.83 sd)**, −9 in the target bucket, total paint actions −33% | bob's `CLOSED.md` #17 confirmed cross-architecture; his re-open holds **only against opponents that do not apply the pressure** |

### Movement and logistics

| axis | kind | the number | re-open |
|---|---|---|---|
| obstacle tracing / bug navigation | closed at stage 0 | `HOME` share **rose** at all three doses (35.5% → 42.8–49.3%); splasher population fell. 3 games | none |
| navigation / pathfinding **family** | closed by an answered re-open | units are blocked by **robots, not terrain** — my own units are the dominant obstacle and re-targeting the dominant escape | a design where allies are not the obstacle |
| de-clumping / crowd-penalised movement | closed at stage 0 | manipulation −89…−100%, score +7%, firing rate unmoved. 4 games. Matches bob #25/#27 | none |
| travel cost (`HOME` share) | **refuted as a cause** | bounded, and the share does not move; it is **downstream of paint**, not a driver | none |

### Coverage and exploration

| axis | kind | the number | re-open |
|---|---|---|---|
| **the coverage AXIS** (6 ranked members) | **oracle-ceilinged AT the bar** | a *perfect* 100%-coverage mechanism prices at **exactly +26** — and only if it costs nothing on small/mid, where all three real arms measured **−2, −14, −8** | only a change to the bar or the corpus regime mix |
| explore-target sampling rank (`EXPLORE_RANK`, i76) | closed; area-gated form **gate-derived and still small** | ungated **+0 / −10 / −4**; area-gated form re-derived from the data measures **~+11 = 42% of bar at 1.2 sd** | needs a mechanism worth ≥ the bar, not a better gate — the gate is buildable (see §3) |
| forward / anchor-relative targeting (`carol_i78`) | declined at oracle | built and verified (+7 coverage points, 57%→64%), **oracle ~+4** | shares the coverage ceiling; not additive |
| ranks 2 (refresh period) and 5 (distance-aware refill) | **never built, and will not be** | different implementations of a premise already priced at or below the bar. **0 games** | as the axis |

### Expansion and territory

| axis | kind | the number | re-open |
|---|---|---|---|
| ruin **selection** and **completion** | excluded-by-measurement | **85%** of sensed ruins are marked, **73%** of marked are claimed | a regime where these fall |
| "selected but abandoned" | excluded at rung zero | `pb` (patience bans) is **0** in counters I already had. 0 games | none |
| claim **rate** | excluded-by-measurement | median gap **57** vs the rival's 37 — slower, but not the deficit | none |
| denial of **lost** sites | real, measured, **not the deficit** | confirmed where it occurs, but vs the rival carol loses **zero** towers | a regime where carol loses towers |

### Information and composition

| axis | kind | the number | re-open |
|---|---|---|---|
| symmetry inference | **BLOCKED — not closed** | refutation is correct and **3–13× faster** with a ruin memory, but pins on only **37–41%** of turns because a robot accumulates just **4.7–5.6 witnesses before dying**. Independently closed by bob #32 at 31.5%/0.53 ruins | a robot that lives longer, or comms — i.e. the same prerequisite as premise 6 |
| unit-mix phase switch on `getNumberTowers()` | closed **on external evidence**; re-open **spent** | self-play −20 at target 2, flat at 4/6/8; **94/150 vs bobf against a 96 baseline, −4 in the large bucket it targeted** | **none. The "instrument-limited" re-opening is spent and must not be re-used** |

---

## 3. The two ceilings, and the gate that is buildable but insufficient

These are the strongest results in the project and the easiest to misquote.

1. **Coverage oracle = +26 = exactly the accept bar.** A perfect coverage mechanism ties the bar and
   only if it is free elsewhere, which no real arm was.
2. **Allocation oracle = +7 = 27% of the bar.**
3. **The area gate is buildable and it does not save either.** My threshold of 1,600 was invented for
   a report table; re-derived by max-separation sweep with a **label-permutation null over the search
   itself**, every data-chosen boundary lands in **1320–1600** (i76 pooled 1500, p=0.060; i69 pooled
   1600, p=0.646; paired bobf corpus 1500, separation +11, p=0.032). **The invented boundary was
   right and the threshold was never the defect.** But:
   - **i69 and i76 want OPPOSITE gates.** i69 is small-positive/large-neutral; i76 is
     small-negative/large-positive, held out across all three i76 doses (−4/−18/−16). There is no
     single "regime gate"; there are two anti-aligned ones.
   - **A gate is worth minus the side you switch OFF, never the side you keep.** i69's gate prices at
     **~0** because its bad side is already neutral — you cannot gain by disabling something that is
     not costing you. My +7 oracle had counted the *good* side, which the ungated bot already has.
   - i76's gate delivers a measured **~+11**, i.e. **42% of the bar at 1.2 sd**.

---

## 4. Facts a context-free reader WILL misread

Every one of these has already cost me, or was caught only by an implausible magnitude.

1. **`bot_result` is the run BOT's perspective, not the candidate's.** I inverted this twice; once it
   produced −11.24 sd and only the absurdity caught it. **Use `tools/margin.py`**, which refuses to
   compute a signed margin without an explicit `--candidate` and resolves it against the run's own
   `bot.txt`.
2. **In the dose screens the candidate is the OPPONENT.** Runs `20260910-100324` and `20260910-123040`
   both carry `bot=carol_iter45`; candidate margin = −(bot margin). Check `bot.txt` and the opponent
   column *before* pairing anything.
3. **Screen margins inflate roughly 2× against the census.** The same arm scored **+12 screen / +6
   census**. Never quote a screen margin against the census bar.
4. **The +26 accept bar is a self-play census MARGIN (W−L) over 150 games**, not a win count. Screen
   gate is ≥31/50. Census: ≥+26 ACCEPT, +18..+25 REPLICATE, ≤+17 REJECT.
5. **Noise floors differ by instrument.** Self-play 150-game census: sd 6.48 on wins → **12.96 on
   margin**. `bobf`: **4.18 per 150**. A +3/150 effect needs ~1,800 games at 2 sd — which is why
   several things here are closed rather than under-powered.
6. **"36 splashers per 1,000 rounds" comes from leavemealone against a different opponent.** Do not
   mix it with Mirage-derived rates. Mixing referents is the error logged three times in this file.
7. **The 125/1,000r ceiling POOLS paint income across six towers, and its stated binder is wrong.**
   The engine requires **one tower to pay 300 from its own stock**. Measured: a tower holds ≥300 paint
   in only **27–54%** of rounds, while chips clear the $1,600 gate in **58–75%**. The ceiling table
   says "binding: chips (barely)"; **chips are not binding.** Ask of any aggregate ceiling: *can the
   payer actually reach the pooled quantity?*
8. **Stage-0 tables are whole-game totals and are NOT normalised.** Mirage games ran **474–2,000**
   rounds across the probe corpus. Recover the round count from the replay (`T r=` in the tower
   indicator) before reading any dose ladder. I misread my own iteration-69 table for two sessions.
9. **A one-knob dose ladder cannot attribute between two quantities the knob co-moves.**
   `SPLASHER_EVERY` raises splasher rate and cuts soldier rate monotonically and in lockstep. The
   un-normalised table reads beautifully as "the value came from cutting soldiers" — that story is an
   artefact of the knob, and no sample size fixes it.
10. **Oracle values are hypotheticals under a perfect conditional.** i76's +12 and i69's +7 assume a
    perfect area gate. Their **measured ungated** values are **−4 to 0** and **+3**.
11. **`bobf` prices bob's STYLE only.** It cannot certify "closes the gap to alice". Only the
    twice-daily tournament can, and only when the opponent is fixed — apply any such swing **both
    ways**.
12. **`roster_extra.txt` bots are frozen synthetic archetypes and another lineage's committed
    snapshots** (`carol_rush, carol_turtle, examplefuncsplayer, carol_iter44, carol_racer, carol_r1,
    bobf, bobf20, bobf18, bobf12`). They are yardsticks, not live rivals. Nothing is ever retired.
13. **BC25 finals benchmark bots are a yardstick, NEVER an opponent (HARD).** Never read their code,
    never examine or run a game against them, never add one to a gauntlet or roster. A committed
    *score* may be read; nothing else.
14. **`agents/alice/` is hard-isolated in both directions** — no code, snapshots, logs, git history,
    or VM paths, ever. `agents/bob/` became readable on 2026-09-10 under MULTI_AGENT rule 0.
15. **`src/carol` and `src/carol_iter45` are the same bot** apart from package. HEAD has not moved
    since the iteration-60 accept.
16. **The refill-path defect is logged and UNFIXED in HEAD.** `walkHomeIfDry` has no fallback when the
    home tower is unreachable. Iteration 73's minimal fix **did not pass** (29/50, +8, 1.13 sd against
    a ≥31 bar). It is a known defect that did not pay to fix, not an oversight.
17. **Probe the engine only via `tools/engine-javap.sh`.** The gradle cache holds a stale **1.0.0**
    jar beside the real **3.1.0**; a direct javap will silently read the wrong one.
18. **carol has no comms and no robot-count API.** Several axes close on feasibility for that reason
    alone, at zero games. Do not re-derive them as design failures.
19. **Engine facts that constrain the architecture** [verified via javap]: `transferPaint` is r²≤2 for
    **every** unit type — the tether is a consequence of this plus "a unit's only paint source is a
    tower". Soldier attack paints only EMPTY or own-team tiles (**never** overwrites enemy paint).
    Splasher r²≤4 AoE, overwrites enemy paint only within r²≤2 of centre. Mopper attack costs **0
    paint**. Money towers have `paintPerTurn == 0`. `SOLDIER` = 250 chips + 200 paint;
    `SPLASHER` = 400 chips + 300 paint. `BUILD_ROBOT_RADIUS_SQUARED = 4`. SRPs stack linearly.
20. **The tether is not forced by r²≤2.** I claimed it was; the existence proof refuted it — a rival
    operates at p90 distance **17.0** against carol's **6.3** under the identical constraint.
21. **The bar is not the binding constraint.** Checked independently: at a conventional 2 sd the bar
    would be ~**+18.5** rather than +26, and **nothing priced clears either** — best measured
    candidate +11 at 1.2 sd, production extrapolation +3 to +9. The impasse is not an artefact of a
    conservative gate.

---

## 5. What is NOT closed

- **The posture half of premise 3 as a standalone question.** Its *pair* rescue is closed. p90 unit
  distance from own nearest tower is **6.3** against a rival's **17.0** under the identical engine
  constraint, so the capability gap is real and demonstrated reachable by an existence proof. What is
  closed is *funding it via production*. Nothing here says a different funding mechanism is refuted —
  it says none has been named, and premises 5 and 6 were the two candidates, both closed.
- **Symmetry inference** is **blocked, not closed**, on a named prerequisite (witness accumulation).
- **The mid-map collapse**, traced but never converted: carol leads at r1400 in 3/3 traced losses,
  then loses **40% of held tiles, 92–100% to overpaint rather than mopping**. The deficit decomposes
  **small +10 / mid 0 / large −30** — a 100% large-map deficit. This is described, not closed, and
  no mechanism priced against it has cleared the bar.

---

## 6. Where a successor starts

1. **Read §4 first.** Most of the cost in this project was referent and normalisation errors, not
   bad hypotheses.
2. **Do not re-run anything in §2 without meeting its stated re-open condition.** Two re-opens are
   explicitly *spent* (phase switch, splash targeting family) and must not be re-used.
3. **The bar does not move.** Sub-bar pursuit was refused on instruction and the refusal held up.
4. **Do not manufacture an axis.** The enumeration is complete at both levels — 21 mechanism entries
   and 6 of 6 design premises. A twenty-second axis invented to have something to run is the failure
   mode this document exists to prevent.
5. If a successor design is attempted, **begin from a committed survey and register the ABORT
   condition before writing a line.** That is what took a rewrite from one session to 8 probe games.

# carol — CLOSURE MAP

**State at time of writing:** `src/carol` = `BUILD "i45a"`, unchanged since the iteration-60 accept
(commit `3610230`). Snapshot copy: `src/carol_iter45`. Every axis and design premise below is
closed or blocked. §7.9 — iteration 80's ruin memory, the last margin-carrying mechanism with nothing
shut against it — was built and **rejected at the screen**, with its gated form oracle-ceilinged.
**This document, not the 23,000-line training log, is where a successor starts.**

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
22. **`p90 distance 6.3` is a POSITION statistic, not a CAPABILITY limit — and it has been used as
    one.** It is the p90 of where carol's units *are*, dominated by units parked beside a tower
    refilling. The distance at which carol **demonstrably completes towers**, measured at the single
    `completeTowerPattern` site with `REFILL_LOW=50` fully active, is **median 8.89, p75 11.70,
    p90 15.00, max 25.24** (iteration 80 stage 0, 18 completions over 3 games). **Only 27.8% of the
    towers carol actually built lie inside the 6.3 figure.** Anywhere this lineage has argued "carol
    cannot operate beyond ~6", that inference is unsupported. The tether (a refill latch) and the
    build envelope are **different constraints**, and iteration 60's **−26** prices the former only.
23. **A distance threshold in this game sits on a QUANTISED, BIMODAL distribution — never read one
    off a single cut.** Ruins and towers occupy fixed map coordinates, so ruin→tower distance is a
    set of mass points: a near cluster over d ∈ [5.0, 6.4] and a far cluster over d ∈ [8, 11], with
    an almost empty gap between. Iteration 80's registered threshold landed **exactly on the top mass
    point**; the same data read at d ≤ 6.24 gave 24.5% and at d ≤ 6.32 gave 37.3%, flipping a
    registered verdict on 0.08 of a distance unit. **Always print the sensitivity across the
    plateau before quoting a share.**

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

---

## 7. RE-EXAMINATION under the absolute-strength objective (2026-09-10)

`OBJECTIVE.md` is binding: the objective is now **absolute strength**, not the head-to-head gap. The
test applied to every entry above: **was its closing number computed relative to a co-evolving
lineage, or absolutely?** Re-examined, not re-run. Zero games.

### 7.1 The absolute baseline, from `benchmarks/HISTORY.md` (score only — the whole of my access)

| run | carol vs `v3` | maps swept | maps **swept against** | carol vs `TSPAARKHS` |
|---|---|---|---|---|
| 20260908 | 5.3% | 1 | 68 of 75 | **0/150** |
| 20260909 | 20.7% | 8 | 52 | **0/150** |
| 20260910 (`3610230`) | **24.7%** | **10** | **48** | **0/150, swept on 75 of 75 maps** |

Read in one direction only, as the file itself instructs: near the floor it has little room to show a
*regression*, so it measures distance to a tournament-winning bot and nothing else.

**This changes the reading of my own plateau finding.** I recorded "the loop has plateaued" on 16
iterations with 0 accepts. That is still true and stands. But the same span shows carol going
**5.3% → 24.7%** against `v3` — the strongest of the three lineages — and **maps where carol loses
every single game falling 68 → 48 of 75.** What plateaued was *accepts*; the accepts that did land
moved the absolute number a long way. The 09-10 run played `3610230`, the iteration-60 accept, and
HEAD has not moved since, so there is **no benchmark evidence at all** about the 16 barren
iterations — correctly, since they changed no build.

**And the honest floor: 0 wins in 450 games against `TSPAARKHS`, swept on every map, every run.**

### 7.2 Transfers UNCHANGED — the bulk of the map

Everything measured on my own bot, against my own bar, or from the engine:

- **All engine facts** (§4 item 19) and every closure resting on them.
- **Both oracle ceilings** — coverage = +26, allocation = +7 — computed from my own coverage→margin
  conversion against my own census bar.
- **`MONEY_MOD`'s integer optimum** — a `min()` ceiling cannot be raised by a knob that trades its
  two terms. Arithmetic.
- **`CHIP_RESERVE` / the gate at equilibrium** — a fixed point on my own economy.
- **Soldier ceiling on feasibility** — no robot-count API, no comms.
- **The fungibility correction** — pooled paint income vs one tower paying 300 from its own stock.
- **"A gate is worth minus the side you switch off"** and the whole area-gate re-derivation.
- **Premise 3's arithmetic** — the 1.09× vs 2.02× relief, and the mutual-destruction table
  (21.1% → 0.2%). Measured on my own bot against a matched control of my own.
- **Bracketed dose ladders**: `REFILL_LOW`, `SPLASH_MIN_SCORE`, splash weights, de-clumping,
  obstacle tracing, navigation-family.
- **The expansion exclusions** (85% marked / 73% claimed / `pb`=0 / claim-rate 57).
- **Symmetry inference BLOCKED** on witness accumulation (4.7–5.6 before death).

### 7.3 Transfers on a NARROWER basis — the comparative half loses authority, an absolute half survives

| entry | what weakens | what survives |
|---|---|---|
| **drain-reduction family** | "alice pays 2–8× carol's drain and wins both games", replicated by bob #26 — both references are lineages that lose ~75–100% to the external standard | **the mechanism argument, which is absolute**: lowering drain means standing *more* on my own paint, where a soldier **cannot paint at all** [engine fact] and a splasher gains nothing. Carol's 0.21–0.82 is the lowest ever measured in this project. Stays closed on the engine fact, not on the comparison |
| **soldier count** | "carol is at the efficient end of the metric, 1–11 vs 12–39" | **iteration 59 tested soldier-primary absolutely and it lost at −5.71 sd** on a self-play census against my own bar. Stays closed on that |

### 7.4 RE-OPENS — the winner-side check loses its authority

> **My winner-side check killed three candidates for zero games this session. Its authority was
> always conditional on the reference being a good bot.** Two of the three have an independent
> absolute closure (§7.3) and stay shut. **One does not, and it re-opens.**

**Soldier tower-attack gating — RE-OPENED.** Killed on this table and nothing else:

| map | area | carol attacks/1,000r | `bobf` attacks/1,000r | ratio |
|---|---|---|---|---|
| Mirage | 1,600 | 98 | 253 | 2.58× |
| galaxy | 2,025 | 208 | 182 | 0.88× |
| Gears | 3,025 | 859 | **1,265** | **1.47×** |

The whole inference was *"`bobf` attacks more than carol on the map carol loses worst, and wins —
so carol is not over-attacking."* `bobf` is another co-evolved lineage; bob's own benchmark line is
**4.7% vs `v3` and 0.0% vs `TSPAARKHS`, unchanged across all three runs.** Being ahead of it is not
evidence of being near optimal. **No dose ladder was ever run — the candidate was registered and
killed before a build.** It re-opens by the change of objective, not by preference.

### 7.5 RE-FRAMED, not re-opened

- **"The deficit is 100% large-map (small +10 / mid 0 / large −30)"** — **CORRECTED the same day,
  see the decomposition rebuild in `TRAINING_LOG.md`.** I claimed this was an artefact of the
  carol–alice matchup. Rebuilt on the four frozen cross-architecture rungs (300 games), the regime
  effect **reproduces on all four**: small 77.6% / mid 77.1% / **large 57.3%**. It is carol's own
  property, not an artefact. What *does* change is its character — against alice large maps are a net
  **loss** (−30); against the roster they are a net **win** (+18). It is a dominance gradient, not a
  deficit. The variable is under-determined between area and **ruin count** (r −0.306 vs −0.395,
  density flat at +0.015), so an "area gate" may really be a ruin gate.
  **Original claim, now superseded:** that it said nothing about absolute weakness. It has organised the targeting of several
  iterations. Under the new objective it no longer identifies where I am weak, and I have no
  regime decomposition of the absolute instrument: `HISTORY.md` gives me *how many* maps I am swept
  on (48 of 75 vs `v3`), never *which*. **That decomposition must be rebuilt on the roster.**
- **"coverage 49% vs 90%"** — the 49% is mine and absolute; the **90% target is alice's** and loses
  its authority as a target. The coverage oracle survives because it was priced against my own bar.
- **"Two lineages, the same 38% conversion — a property of the game"** — still the strongest form of
  cross-architecture evidence I have, but both architectures are near the same floor. It is evidence
  about *these* designs, not necessarily about the game.

### 7.6 A caveat class that is now larger — declared, not used to re-open anything

**Every dose ladder in §2 was run in self-play against my own predecessor.** Under a head-to-head
objective that was a known limitation. Under absolute strength it is a **mirror optimum**: tuned
against an opponent with my own weaknesses. **Direction declared:** a mirror optimum should
*overstate* mechanisms that exploit my own architecture's failings and *understate* mechanisms that
only matter against dissimilar opponents — which is the exact shape of a joint local optimum.

I am **not** re-opening on this. It is a caveat, and the remedy is already built and named by the
objective: the frozen roster's **8 discriminating cross-architecture rungs** are the outcome
instrument precisely because they are not a mirror.

### 7.7 Pricing the re-opened set

One entry re-opened, so the set is one. Priced the way everything else today was priced:

**Cost, measured absolutely on my own bot** (vs `bobf`, per 1,000 rounds):

| map | area | attacks | **paint spent attacking** | paint ACTIONS | attack share of action-paint |
|---|---|---|---|---|---|
| Mirage | 1,600 | 98 | 490 | 4,297 | **2.3%** |
| galaxy | 2,025 | 208 | 1,040 | 3,844 | — |
| **Gears** | **3,025** | **859** | **4,296** | 3,392 | **20%** |

The attack is **completely ungated in code** — every soldier attacks any enemy tower in range, every
turn it can, at 5 paint. Spending scales **8.8× with map area while painting falls.** On the largest
maps carol spends **more paint attacking towers than it has paint actions**, and paint is the
binding resource on the only axis with a ceiling at the bar.

**Benefit, and why the sign is genuinely uncertain.** I priced it both ways when I found it:
- *against gating*: ~43 tower kills on Gears each cost the opponent 1,000 chips and ~25 rounds of
  that tower's income — crudely a **1.56:1 trade in carol's favour on the tiebreak quantity**;
- *for gating*: the opponent **rebuilt all 43**, and runs 2.6× carol's income, so paint denied to
  her is worth less per unit than paint spent by carol.

**The "for gating" half is alice-specific and loses authority with the objective; the "against
gating" half is arithmetic on the tiebreak quantity and survives.** So the re-examination moves the
sign *toward* leaving the attack ungated — which is the opposite of what re-opening a candidate
usually does, and worth saying plainly.

> **Verdict: the sign is uncertain, the cost is large and absolute, and it is settleable by a
> zero-armed dose ladder — the exact instrument for an uncertain sign.** It does not route through
> the coverage chain, so it does not inherit that closure. It is the only priced candidate the new
> objective produces from the existing map, and it was found by re-examination, not manufactured.

### 7.8 RESOLVED — iteration 79 CLOSED the re-opened tower-attack gate, at ZERO games

The registration below was executed and **closed before stage 0 spent a game**, because validating the
counter refuted the premise's magnitude. The recorded cost table was wrong: 98/208/859 attacks per
1,000r were actually **5/10/379** (two of them **21× over**), and the "paint ACTIONS" column was
equally unreproducible — **a number a registered iteration was built on had no method attached to it.**
Re-priced on engine facts (a soldier's paint *is* `rc.attack`, so an attack displaces at most one paint
action, and only if there was one to displace): attacks are **2.43% of soldier-turns on the worst map,
0.24–0.29% elsewhere**, and a *perfect* gate recovers ~252 tiles = **~13% of the bar, ~+3 census** before
subtracting tower denial. **Closed: refuted-on-value.** Re-open only on a mechanism that raises the
attack's cost by an order of magnitude.

> **The transferable lesson, now standing practice: validate the instrument before spending the games.**
> It cost zero here and it caught a knife-edge in iteration 80 the same day.

### 7.9 CLOSED — iteration 80, the RUIN MEMORY. Rejected at the screen; the gated form is oracle-ceilinged.

The first margin-carrying mechanism with **nothing closed against it** (ledger-checked against five
near neighbours, all of which rest on "against alice carol loses zero towers", which is false in the
regime carrying the margin).

- **Traced:** on Set A — the six maps carol loses from **both sides** against `carol_siege`, i.e. the
  entire margin — the failure is **replacement, not defence and not the opening** (2.7:1 whole-game,
  ~10:1 over r300–800). Split three ways it is **availability 77.5%** vs affordability 13.1% and
  choice 9.4%; **77.7% of blind rounds still have unclaimed ruins left, median 7.** Positioning, not
  exhaustion.
- **Root, from the code:** `nearestEmptyRuin()` is sense-range only. carol keeps a 12-slot `towerMem`
  and **no memory of unclaimed ruins at all**, while sighting **67%** of them per game and finishing
  with a mean of **2.75** structures. Acquired and discarded.
- **Stage 0 (6 games, two no-op probe builds, both reproducing the control's exact end rounds):**
  M0 `ov=0`. M1 **71.2%** of 16,064 blind soldier-turns hold a remembered unclaimed ruin (bar 50%).
  M2 registered **37.3%** (bar 33%) — **passed, but knife-edge and not banked**; re-read against the
  threshold-free demonstrated envelope it is **46.3%** within carol's median claim distance and
  **84.6%** within her p75. **The falsifier does not fire.**
- **Known before the build, from stage 0:** a naive memory **goes stale** — ≥3.7% of remembered
  "unclaimed" ruins already carry a tower. The built arms forget on sense and on ban.
- **RESULT — 200 games over two independent 25-map samples, gate ≥ 31/50, mirror null 25/50:**

| arm | design | candidate | vs null |
|---|---|---|---|
| `carol_i80_10 / _20 / _inf` | forget a banned ruin at RECORD time | **21/50 each** | **−4** |
| `carol_i80_lazy` | filter bans at NAVIGATION time (the fix) | **27/50** | **+2** |

  The doses genuinely diverge (25 of 50 cells differ in end round), so this is a real measurement.
  **A PERFECT, buildable area gate prices at 26.0/50 — one game above the null against a ≥31 gate**,
  and the regime effect it would key on **reverses sign between the two samples** (small maps 30.8%
  then 61.5%), so it is noise and the gate is dead twice over.
- **Kind: measured-and-small** for the corrected design; **oracle-ceilinged at ~+1 game** for the
  gated form. **Re-open only on a mechanism that raises the PER-FIRING VALUE of a memory redirect,
  never its volume** — volume is measured and is not the binder, and the two designs land on opposite
  sides of the null. **An area/ruin gate must not be re-proposed** without a regime effect that
  replicates across two independent map samples.
- **Most likely account, named as a hypothesis and NOT established:** the redirect displaces
  frontier-seeking (iteration 14, accepted), so it spends a decision that was already producing
  value rather than a resource. The ablation that would establish it was not run.
- **Stage 0's M1 was overstated 3.5×** and I caught it from the built arm, not from the probe:
  **77% of the remembered ruins were BANNED** — ruins carol had already proved uncompletable because
  an enemy-painted pattern tile can never be overwritten [E]. Corrected, M1 fails its own ≥50% bar.
  The stage-0 **demonstrated-envelope** result is unaffected; it never touched `ruinMem`.

### 7.8 (original registration, kept for the record) — the tower-attack gate

**Mechanism:** gate the soldier tower attack. **Doses:** over the gate's strictness (never attack /
attack only when the tower is below a health threshold / attack only when carrying surplus paint),
with a **zero arm** that is byte-identical to HEAD.

| # | check | must move |
|---|---|---|
| **0** | manipulation: attack paint per 1,000r on a large map | must **fall** monotonically in dose; if it does not, the knob is not the knob and I stop for 3 games |
| **A** | paint actions per 1,000r | must **rise** — otherwise the freed paint is not being spent, and the mechanism is a no-op with a cost |
| **B** | dose screen | **≥ 31/50** to proceed |
| **C** | **primary outcome instrument, per `OBJECTIVE.md`: the 15-rung frozen roster**, reported on the 8 discriminating rungs | a placement run, read for regression as well as gain |
| **D** | self-play census | **≥ +26 ACCEPT / +18..+25 REPLICATE / ≤ +17 REJECT** — the bar does not change |

**Falsifier, registered:** if check 0 passes and check A fails, the paint is freed and not converted,
and the whole "attack spending is a sink" premise is refuted rather than the implementation — that
closes the direction on value, at 3 games, exactly as premise 3's production half closed.

**Pre-registered caveat:** the cost table above was measured against `bobf` on three maps. It is a
cost measured on **my own bot** (my attacks, my paint), so it does not inherit the mirror-optimum
caveat of §7.6 — but the three maps are a convenience sample and the 8.8× area scaling is the load-
bearing claim, not the level on any one map.

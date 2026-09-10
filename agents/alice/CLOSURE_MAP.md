# Alice — CLOSURE MAP

What is closed, **by what kind of closure**, with the number that closed it and its re-open
condition. Written after the mechanism enumeration finished and the redesign aborted, so a successor
starts here rather than re-deriving it. Everything about `carol` comes from **replays of games alice
played**; no other lineage's source was read.

**Closure kinds** — the kind matters more than the verdict, because it determines what could reopen it:
`measured-and-small` · `oracle-ceilinged` · `phase-mismatched` · `gate-unimplementable` ·
`refuted-on-value` · `structurally-unavailable`

---

## 1. Mechanism axes

| # | axis | kind | the number | re-open condition |
|---|---|---|---|---|
| 1 | **memory / persistent state** | refuted-on-precondition | on mit, 8–20 sites unclaimed for 700 rounds, **seen at zero samples** | memory cannot remember what was never seen — needs a discovery change first |
| 2 | **spacing / vision overlap** | oracle-ceilinged | passed its gate (0.483 v 0.92) but perfect spread moves empty-visibility **6.4% → ~10.4%** against a **93.6%** deficit | none written; the ceiling is arithmetic |
| 3 | **local gradient (targeting)** | measured-and-small | **0.95x random** for blind soldiers; the empty-tile control scored 2.4x on sighted, so the instrument works | — |
| 4 | **local gradient (exploration)** | refuted-on-sign | **−64.5%** registered, **−14.6%** team-relative — wrong sign both ways | — |
| 5 | **messaging** | structurally-unavailable | reporters see **2.48x fewer** empty tiles than non-reporters; delivery 49.9%/34.7% | connected sighted soldiers > 60%, **or** zero-reporter tower-frames < 50% |
| 6 | **tower mix (count)** — E2 | refuted-on-value | screen **−8** | — |
| 7 | **upgrade priority (rate)** — i53 | refuted-on-value | **−2**, having moved tower paint **+639 (+50%)** | — |
| 8 | **refill reserve** — K3 | measured-and-small · **SHIPPED, UNCONFIRMED** | screen +4, **census FAIL +5** | see `UNCONFIRMED.md` |
| 9 | **refill widening** — K7 | oracle-ceilinged | gate opened **8.61x**, paint moved **1.39x** — ≤7.7% of output | raise paint moved *per refill* toward 100 while keeping the rate |
| 10 | **splasher chip gate** — K8 | phase-mismatched | **2.22x** against ≥5x; fixed point **3.2x** | tower paint ≥300 on >50% of decisive-window frames (now 29%) |
| 11 | **pair i53+K8** | phase-mismatched | joint **1.94x**; the resources are anti-correlated in time | make the two co-occur |
| 12 | **SRP / resource patterns** | gate-unimplementable | the only global proxy correlates **+0.01** with what it would proxy; the per-soldier gate fires **87%** | an observable correlating with expansion-exhaustion at \|r\| ≥ 0.6 |
| 13 | **mopper share (dose)** | structurally-blocked | claim rate 58.1% (neither branch); **refusing a mopper yields a SOLDIER by construction** | a destination for the freed paint that is not soldiers |
| 14 | **mopper runaway** | refuted-on-value | tail share **26.0%** v a 25% design constant; the tail is **volume (8.00x)**, not pathology | — |
| 15 | **CLASS: chip-gated + paint-costly** | phase-mismatched | above 3,950 chips, paint ≥300 co-occurs on **0.0% of 244 frames**; rank corr **−0.496** | — |
| 16 | **coordinated unit economy** — R1 | **structurally-unavailable** | aborted 1/4 then 2/4; **its funding half is refuted** — see §3 | — |

## 2. Design premises

| premise | status |
|---|---|
| **D1 expansion-first** | **VALIDATED** — r300 tower leader wins **81%**; alice wins the race **12–4** |
| D2 spawn-and-forget | refuted by the upper bound (0.383 v 2.044 refills/unit) — but its fix is gated on adjacency (2.61%) |
| D3 mix by dice | refuted by the upper bound (21% moppers / 11.3% splashers v 0% / 30.6%) |
| D4 disperse to find work | **collapsed into D1** — a consequence, not a policy (unassigned units sit at 3.5 v assigned 7.0) |
| D5 local-only decisions | engine-fixed; not separable |
| D6 chip reserve | not binding (42,712 surplus) |

## 3. The prize, which today's refutation does NOT touch

> **alice wins the r300 race 12–4 and converts its leads at 75%; carol converts at 100% and takes all
> 3 ties.** Converting alice's *existing* leads at that rate is **+3 games in 19 → +23.7 net swept**,
> against a **+12** census bar; two-thirds capture is **+15.8** and still clears.
> **What died today is one route to the prize, not the prize.** It is counted, not modelled.

## 4. Facts a context-free reader WILL misread

A rewrite discards the context that made these safe. Each is **true**, and each invites the wrong inference.

1. **"The soldier is correctly idle."** True — an empty tile is in action range on 1.8% of idle turns.
   **It is an information ceiling, not a finished job**: 93.6% of paintable tiles are invisible to the
   whole team at once. **The 81% idle rate is NOT headroom.**
2. **"Unspent resource accumulates."** **False here.** Tower paint income is per-tower and spawning is
   what builds towers, so **the spending IS the investment**. Cutting spawns 78% banked nothing —
   the arm simply held **half the towers** and the same paint per tower.
3. **"Alice has more towers than carol and loses."** True, and the tower lead still predicts the winner
   **81%** of the time. Alice **wins the race and under-converts it** — do not discard expansion-first.
4. **"Chips are in 42x surplus."** True and unusable: the chip gate opens **exactly when the paint is
   gone** (rank corr −0.496; 0.0% co-occurrence above 3,950).
5. **"Alice runs 11.3% splashers."** **Only against carol.** It is 35.0% v bob and 42.6% v iter43 —
   the gate is on chips, so the share is *jointly produced with the opponent*. **Any composition figure
   must carry its opponent in the sentence.**
6. **"Towers are starved."** They hold ~154 paint and pay **no upkeep** (verified: the `processEndOfTurn`
   block is gated on `isRobotType`). The only outflows are **spawning and transfers.**

---

# 5. RE-EXAMINATION under the absolute-strength objective (2026-09-10)

`OBJECTIVE.md` is binding. One question per entry: **was the closing number computed relative to the
rival, or absolutely?** Re-examined, not re-run.

## Transfers unchanged — 13 of 16 mechanism axes

Axes **1–12, 14, 15, 16** all close on numbers measured **on alice alone or on the engine**: the
engine enumerations, the permutation nulls, the oracle ceilings against *my own* bar, the phase
relationship, gate un-implementability, and the structural result that spending is the investment.
**None of them says "the rival is on the other side of this metric."** They stand.

**Note the screens and censuses transfer too** (E2 −8, i53 −2, K3 +4/+5, K7, K8, the pair): every one
was **arm versus its own byte-identical control**, never against carol. That was worth the discipline.

## RE-OPENED by the change of objective — not by preference

| | entry | why it does not transfer |
|---|---|---|
| **13** | **mopper share (dose)** | It closed because *"refusing a mopper yields a SOLDIER, and soldiers are the term alice already leads carol 1.35x on."* **That is a pure relative argument.** Being ahead of a bot that loses ~75% of its games to the external standard is not evidence that more soldiers are worthless. **The substitution is still real — the freed paint does become soldiers — but "soldiers are not worth having" is now unevidenced.** |
| **D2** | **spawn-and-forget** | Closed on *"carol resupplies 2.044/unit against my 0.383."* **Purely relative.** Neither refuted nor supported now — an **open question**, not a closed premise. |
| **D3** | **mix by dice** | Closed on *"carol runs 0% moppers and 30.6% splashers against my 21% / 11.3%."* **Purely relative.** Same status. |

## And the survey's premise set was derived the same way — this is the larger correction

**The four premises the redesign was built on (A fewer units, B no moppers, C ~30% splashers, D
resupply first-class) were every one of them "carol does X."** Under the new objective **that is not
evidence.** They are not refuted — they are **unevidenced**, which is a different and worse state,
because I priced and built on them.

> **One survives on absolute grounds and should be kept: premise B.** *Moppers emit `UnpaintAction`
> and never `PaintAction`* is an engine fact about alice alone — a mopper contributes exactly zero to
> paint output whatever any rival does. **B's justification is independent of the objective; A, C and
> D's is not.**

## D1 needs splitting, because half of it is relative

- **"The r300 tower lead predicts the winner ~81%"** — a property of the *game dynamic*, corroborated
  cross-lineage. **Transfers.** Expansion-first remains the validated objective.
- **"...and alice wins that race 12–4"** — **relative, and it was functioning as reassurance.** Winning
  a race against a bot that loses three quarters of its games says nothing about whether alice expands
  *well*. **Retired as evidence.**

## The counted prize survives, and its justification gets STRONGER

I had stated it as *"alice converts leads at 75%, carol at 100%."* **The 100% target does not need
carol at all**: **12 of 12 is the ceiling.** So the absolute statement is

> **alice loses 3 of its own 12 winnable games — 3 games in 19 it had already earned by r300.**

That is an **absolute** loss, unchanged by who the opponent is, still **+23.7 net swept** at full
capture against a **+12** bar. **It was the strongest thing I held this morning and it is the
strongest thing I hold now.**

## One entry the new objective PROMOTES rather than re-opens

> **The shipped bot loses to its own `alice_iter39` at 18/50.** I flagged it as inside 12-rung
> multiplicity noise and deprioritised it — **correctly, under the old objective, where the roster was
> a side check.** The roster is now the **primary outcome instrument**, and "my current head is beaten
> by my own earlier snapshot" is a direct absolute-strength question. **Promoted from a rung to watch
> to a diagnostic worth resolving.**

## Tally

**13 of 16 mechanism axes transfer. 3 re-open** (mopper dose, D2, D3). **4 survey premises lose their
evidence, 1 of which (B) survives on independent absolute grounds.** **1 entry is promoted.** The
prize is untouched and better justified.

---

## 17. Production efficiency per spawn paint — `refuted-on-value` (2026-09-10)

**The axis:** rank unit types by tiles painted ÷ paint spent spawning that type, then build more of
the top-ranked type. Splashers rank first; M2 built one whenever the tower could afford it.

**Closing number, absolute (no rival in the sentence):** splasher count **1.69x**, output per round
**1.01x**. Then, at the action site: in **r1–300** the arm does **0.71x** the paint actions of its
control while hard paint-starvation runs **3.95x** higher; after r300 **80–91%** of action-capable
unit-turns are idle **for want of a target**, in both arms, with units acting on **~4%** of turns.

**Why it closes, and it is not "small":** the ranking is denominated in **spawn paint** — a *build*
budget. Total output is bounded by **action paint**. The ranking is *correct about which unit to
build* and *cannot raise total output*, because the quantity it optimises is not the quantity that
binds. Worse, splashers are the priciest unit on *both* budgets (300/50 vs a soldier's 200/5), so
buying them in the opening spends the action budget before the army exists.

**Re-open condition:** *only* if action paint becomes the binding constraint outside the opening —
i.e. the "idle for want of PAINT" share after r300 exceeds the "idle for want of TARGET" share. It is
currently 10.3% against 83.7%. **Naming supply as the re-open, not mix.**

**What this closure hands forward — larger than the axis it closes:** ~96% of my army's action
capacity is unused after r300, and **not for want of paint**. "No target" means the unit is not
standing next to unpainted ground: a **placement and travel** problem. Every mix question is arguing
over a budget that is not the one running out.

> **A ranking's denominator names the budget it optimises. Before acting on one, check that the
> quantity you want to move is bounded by that same budget.**

---

## 18. Army utilisation — `oracle-ceilinged` (folds into axis 2), 2026-09-10

**The axis:** my units act on **4.40%** of their action-capable turns (1.1% after r1000). The obvious
reading is 96% headroom. It is not.

**Operationalisation check that opened it:** no prior closure measured this. Requirement I counted
**soldiers** and distance to *unexplored* ground; B0/axis 2 counted **tiles** and the team's vision
union; axis 3 counted *choices given targets exist*. This counts **action-capable turns** at the
**action** radius. *A closure covers a question only if its denominator is the question's denominator.*

**Closing number:** of "no target in action range" turns after r300, only **17.2%** have workable
ground anywhere in vision — registered gate **≥60% travel-bound / ≤30% sight-bound**. **SIGHT-BOUND.**
**71.98%** of all action-capable turns have no workable tile in vision at all.

**Why it closes:** the units are not failing to reach visible work; there is no visible work. That is
B0's **93.6% information deficit** seen from the unit's side, and B0's spacing remedy is already
oracle-ceilinged (6.4% → 10.4%). **The army is larger than the work the map presents to it** — which
is why M2's extra units produced no extra output, and it strengthens §17 rather than opening a lever.

**Re-open condition:** the share of no-target turns with work in vision rises above **60%** — which
happens only if the map stops saturating, e.g. a genuinely larger reachable frontier. Phase drift
measured at 44.8% → 28.2% → 23.5% → **13.3%**, so it is moving *away* from re-opening.

**Sub-thread, now CLOSED for zero games — moppers travel-bound (56.88% of mopper idle turns have
enemy paint in vision, outside its r²≤2 radius):** **dead on arrival against the redundancy closure.**
Only a splasher takes enemy-painted ground [E]; it reaches further (centre to r²≤4), converts
enemy → ALLY in one step where the mopper yields only enemy → EMPTY, and does up to 13 tiles per
action against the mopper's one. The pattern-shade exclusivity that could have saved it fails: the
soldier's ruin branch already repaints ally wrong-shade tiles to the correct shade. **The idle
capacity is idle for work another unit owns.**

> *Before pricing a unit's idle capacity, check whether the work it is idle for is work only it can
> do.* Utilisation is a ratio whose numerator can be worth zero.

---

## 19. Accumulate-by-spending-less — `refuted-on-mechanism` (2026-09-10)

**The axis:** the composition premise under R1 — spawn fewer units so towers stop draining
themselves, keeping tower paint high, which was to fund splashers (capped at 29% early, 0% after
r1200) and refills (unreachable at 2.61% adjacency). Premise A funding premises C and D.

**Closing number:** cutting spawns **78%** left tower paint **identical — 147.0 arm v 147.4 control**.
The arm simply held **half the towers (3.25 v 6.89)**, with total paint in the same **2:1** ratio.

**Why it closes:** paint income is **per-tower**, and spawning is what builds towers. **The spending
IS the investment.** A does not pay for C or D; the banked resource never exists. This is a fact
about the game's economy, not about that design — *"accumulate by spending less" was never available
to anyone*, which is why it takes the whole composition down rather than one arm of it.

**Re-open condition:** a paint income route that is **not** proportional to tower count. Closed by
enumeration, not by sampling — paint enters via exactly three engine routes and all three are
accounted for. **No re-open is expected.**

---

# 6. TODAY'S FOUR CLOSURES (2026-09-10) — all four found without a screen

| # | axis | kind | the number | re-open condition |
|---|---|---|---|---|
| **17** | production efficiency per **spawn paint** | `refuted-on-value` | splashers **1.69x**, output/round **1.01x**; r1–300 actions **0.71x** with paint-starvation **3.95x** | action paint binds after r300 — i.e. paint-idle > target-idle. Now **10.3% v 83.7%** |
| **18** | **army utilisation** (the 96%) | `oracle-ceilinged` | acts on **4.40%** of action-capable turns (1.1% after r1000); **71.98%** see no workable tile at all; travel share **17.2%** v a ≤30% bar | no-target turns with work in vision rise above **60%**. Drift is **44.8 → 13.3%**, moving away |
| **18a** | mopper travel-bound sub-thread | `superseded` | **56.88%** of mopper idle turns see out-of-range enemy paint | a job the splasher cannot do. Pattern-shade, the only candidate, **fails** |
| **19** | accumulate-by-spending-less | `refuted-on-mechanism` | spawns **−78%** → tower paint **147.0 v 147.4**, towers **3.25 v 6.89** | a paint route not proportional to tower count. **None exists** |

**Cost of the four: one 300-game census (which refuted a suspected regression) and 12 debug matches.
No screen was spent on any of them.** Three were decided by within-game measurement at the decision
site and one by reading the engine.

## What these four say together

They are one finding seen from four sides: **every axis I have left is denominated in a budget that
is not the one that binds.** M2 optimised the build budget; the composition premise tried to bank a
resource that only exists while being spent; the mopper thread priced idle capacity whose work
another unit owns; and the 96% is not headroom because **the army already exceeds the work the map
presents to it.**

> **The two keepers, and they are halves of one rule:**
> **A closure covers a question only if its denominator is the question's denominator.**
> **Utilisation is a ratio whose numerator can be worth zero.**

## Standing position

**The counted prize is untouched and no mechanism reaches it:** alice wins the r300 race **12–4** and
converts leads at **75%** against carol's 100%; capturing those is **+3 games in 19 = +23.7 net
swept** against a **+12** bar. It survives every closure above because it is **counted, not
modelled** — and today's work removed four candidate routes to it without touching the prize itself.

**This is a finished position, not a gap.** The space is closed on far stronger evidence than it was
this morning, and the honest report is the closure map rather than a manufactured direction.

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

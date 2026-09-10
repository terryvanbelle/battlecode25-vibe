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

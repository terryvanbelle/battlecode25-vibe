# Closed-directions ledger (bob)

**GREP THIS FILE BY HYPOTHESIS NAME BEFORE OPENING ANYTHING.** Not "read it when stuck" — grep it as the
first act of proposing a mechanism. This lineage spent 24 games in one week re-deriving a defect its own
log already held (LEARNING 74), and a second near-miss the same week was caught only because a session
happened to search for `SPLASHER_SLOTS`. Prose scattered across 16,000 log lines is not a ledger.

Adopted from `METHODS.md` §13. Every entry carries a **RE-OPEN** condition — the number that would have
to change. Without one a closed direction silently becomes a permanent ban rather than a closed question,
and this lineage has already had to *un-close* one direction (the conditional splasher gate, which was
blocked rather than closed — a different state, recorded as such).

`CLOSED` = measured and rejected. `BLOCKED` = not refuted, but cannot be evaluated until something else
exists. Keep them distinct.

| # | direction (grep by these words) | state | killed by | RE-OPEN when |
|---|---|---|---|---|
| 1 | tower spawns a **mopper** when its paint stash is below soldier cost | CLOSED | iter2: "stash < 200" is the steady state at paint towers; fallback preempted soldiers 2:1 | a tower's stash distribution is measured and is *not* concentrated below 200 |
| 2 | same, restricted to `paintPerTurn == 0` towers with chips ≥ 1500 | CLOSED | iter2: h2h exactly 12/24, swept 1–1. Mechanism engaged, effect nil | — |
| 3 | **RUIN_FLOOR** | CLOSED | iter18, 150-game screen | — |
| 4 | candidates that reshape bob's own **opening spend**, motivated by the ruin-poor deficit | CLOSED | the deficit is opponent-inflicted; the same code reaches 4–7 towers against a different opponent | evidence that bob's *own* spend binds in a game it loses |
| 5 | **bob_rush** / production-policy archetypes as a route to the short-game regime | CLOSED | opposite-pole policy moved median game length 668 → 760, i.e. away from the regime | a production change is shown to *shorten* games |
| 6 | **ruin selection/ranking** changes as a fix for the ruin-poor deficit | CLOSED | mean choice set 0.83 on the motivating map, structurally smallest exactly where the fix aims | a measurement showing a plural choice set on ruin-poor maps |
| 7 | un-gate the round-60 **splasher slot unconditionally** | CLOSED | −7 wins_above_half on the full corpus, harm localised to games > 1,000 rounds | — |
| 7b | the **conditional** form of the same gate | **BLOCKED**, not closed | no measurable benefit until a regime instrument exists | a regime instrument exists |
| 8 | recover idle soldier turns by **seeking visible unpainted ground** | CLOSED | +1/+3 wins; mechanism active at +3.7 per-mille, +5.4 at perfection, against a cliff at −49 | the requirement drops below ~6 per-mille |
| 9 | remove **stale pattern marks** to free SRP sites | CLOSED | −3/−6 wins; mechanism confirmed active and *inverted* (starts +110%, completions −34%) | the targeted-clean repair (recompute the tower pattern's mark and clean only those) is built — a real, unbuilt repair |
| 10 | lift the round-60 splasher gate **on small maps** | CLOSED | +2/+3 wins; priced at +1.7 per-mille against a 16 per-mille requirement | the requirement drops below ~2 per-mille |
| 11 | add a **cheaper-unit fallback** to the spawn rotation | CLOSED | measured 0.26–0.81 units per 120 rounds | the rotation stall is measured above ~3 units/120 rounds |
| 12 | **reorder the splasher slots** so they are not adjacent (`0b01100` → `0b01010`) | CLOSED by arithmetic, no run | a 5-slot cycle's cost is unchanged by ordering | — |
| 13 | let `paintSomething` paint **marked tiles in the mark's colour** | CLOSED | decision rate 3.9% of soldier-turns small, 0.0% large — the rescued branch is rarely taken | the marked-and-blocked decision rate exceeds ~15% |
| 14 | **soldier frontier-seeking** navigation (both the general and the F-turn form) | CLOSED | iters 43: +2/+3 wins out of 50; mechanism confirmed (+6.5% tiles/soldier-round, correct regime sign) and priced at −11% towers | a version exists that does not spend tower count |
| 15 | evaluate an early-coverage mechanism on a **self-play gauntlet** *(method, not mechanism)* | **BLOCKED** | four attempts, four nulls; doctrine 17 explains all four | an opponent exists that applies carol's early-coverage pressure |
| 16 | reduce bob's **paint churn** to close the gap to carol | CLOSED | bob's conv (0.671) already equals carol's (0.662) on small maps | — |
| 17 | raise bob's **mopper spawn share** | CLOSED | iter45: −5, −6, −11 wins out of 50, dose-monotone harm; displaced unit shown irrelevant; conv rose as designed while total paint actions fell 10–27% | a mechanism exists that raises mopper share *without* reducing total paint actions |
| 18 | **map-area-gated** mopper build | CLOSED by arithmetic, no run | best case is the small-map number: +1.1% of 333 tiles = +3.7 tiles against a 91-tile deficit | the small-map deficit falls below ~10 tiles |
| 19 | **redundant repainting** (paint a tile already holding exactly that colour) | CLOSED | iter46: **0 of 2,377** classified repaints, bob *and* alice, every stratum | — (an exact zero on the correct partition) |
| 20 | **unit-mix / composition** changes generally | CLOSED | local optimum in both directions: iter20's splasher peak interior at 2 of 5 slots, iter45's monotone mopper harm | either boundary moves in a re-measurement |
| 21 | raise **`conv`** (paint-to-coverage conversion) | CLOSED from both ends | bob wastes nothing reclaimable (#19), and answering alice's 47 unpaints/game costs more than it returns (#17) | — |
| 22 | the **low-paint cooldown** tax (`INCREASED_COOLDOWN_THRESHOLD`) as a brake on bob's action rate — incl. raising `REFILL_BELOW` *for that reason* | CLOSED by arithmetic, no run | iter47, bytecode of the pinned 3.1.0 jar: `addActionCooldownTurns` adds `round(num*(100-2X)/100)` only when `X<50`, so for a SOLDIER (base 10) the taxed value tops out at **19 < 20** and one decrement always clears it — **exactly zero rounds lost at any paint level where a soldier can still attack**. Real for MOPPER (3→5 turns/action) and SPLASHER (5→9), but both already run far below their untaxed ceilings (0.057 splashes/splasher-round vs 0.20; 0.150 unpaints/mopper-round vs 0.333) | a unit type is measured at or near its untaxed action ceiling *and* spends materially long below 50% stash |

## What this leaves

`tiles = acts × conv`. `conv` is closed (#21) and composition is closed (#20). **`acts` — total paint
actions per game — is the only remaining term**, and of its three sources — more units, units acting more
often, units living longer — **acting more often is now closed too (#22)**. What is left is **units living
longer**, which is what iteration 47 tests. Starvation is a candidate but a modest one: as a
share of units built it is bob 41.2%, alice 35.2%, carol 35.6%.

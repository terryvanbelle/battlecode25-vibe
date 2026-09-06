# Alice — TRAINING_LOG.md (append-only)

Conventions: every iteration logged with hypothesis, pre-registered variables,
measurements, decision. Snapshots in `src/alice_iterN/`. Gauntlet output in
`gauntlet/` (git-ignored, pruned).

**Standard eval map subset (EVAL12)**: DefaultSmall DefaultMedium DefaultLarge
DefaultHuge Paintball Money Gears Circuit maze sierpinski FourCorners Oasis
(mix of sizes/wall density; full 75-map list only for big evaluations).

---

## Phase 0 (2026-09-06)

- `RULES.md` written from spec v3.1.0 + engine source (GameWorld/InternalRobot/
  UnitType/GameConstants pulled from official repo; jar 3.1.0 on VM matches).
- **Determinism verified**: alice vs examplefuncsplayer on DefaultSmall run twice
  → replays byte-identical. Only engine nondeterminism: final tiebreak #6 uses
  `Math.random()`.
- Key asymmetries (details in RULES.md):
  - Splasher hits towers at up to dist^2 16 vs paint/money tower range 9 →
    free siege. Defense tower range 16 matches it exactly.
  - Defense towers (16) outrange soldiers (9); paint/money towers (9) tie soldiers.
  - Clumping tax: -1 paint/adjacent ally/turn (x2 on enemy paint).
  - Paint win = >=70% of (area minus walls); ruins count in denominator.
  - Messaging robot<->tower needs 4-adjacent ally-paint connectivity; tower->tower
    broadcast r^2<=80 unconditional.
- Turn order: robots execute by (roundsAlive, ID) — older first.
- Bytecode monitoring wired into iteration 0 (overrun = round advanced mid-logic;
  near-miss = within ~15% of limit; surfaced in indicator string every turn).

## Iteration 0 — baseline (ACCEPTED by definition, 2026-09-06)

Minimal instrumented bot, own code (package `alice`), replacing seeded example copy:
- soldiers complete money-tower patterns on ruins, paint own tile, wander (xorshift
  PRNG seeded by ID; tie-breaks randomized to avoid side bias)
- moppers mop adjacent enemy paint (prefer robbing robots), wander
- towers: single-target lowest-HP enemy + AoE, spawn ~75% soldiers / 25% moppers
- splashers: logic present but never built yet
- Result vs examplefuncsplayer, DefaultSmall side A: WIN by paint r250.
- Snapshot: `src/alice_iter0/`.

### Functional-area map
| area | status |
|---|---|
| ruin completion / tower building | basic (money towers only) |
| paint spread | soldier self-tile only |
| micro vs towers/units | none |
| splasher usage | none (never built) |
| mopper usage | basic |
| economy (chips curve, upgrades) | none |
| SRPs | none |
| comms | none |
| navigation | wander + slide |
| map symmetry inference | none |

### Closed-directions ledger
(empty)

---

## Iteration 1 — soldier idle-action painting (ACCEPTED, 2026-09-06)

**Hypothesis**: soldiers waste their action on most turns; spending idle actions
painting the nearest EMPTY tile in action radius (only when paint >= 15) increases
coverage, the de-facto victory metric (peer games all end at r2000 on the
painted-more tiebreak — observed in every candidate-vs-iter0 game).

**Change**: `runSoldier` — after own-tile painting, if action still ready and
paint >= 15, paint nearest empty passable tile within r^2 <= 9.

**Evaluation** (run 20260906-181657, EVAL12, both sides):
- Head-to-head vs alice_iter0: **17/24 (71%)** > 50% → accept gate cleared.
- vs examplefuncsplayer: 24/24 (100%) — efp reclassified **benchmark→swept**;
  keep in pool as sanity check only, it cannot resolve changes anymore.
- Diff shape: swept-loss on DefaultSmall (both sides, tiebreak) = one-directional,
  concentrated → real causal regression, carried as iteration-2 target.
  FourCorners loss r1295: iter0 reached 70% coverage against us (suspicious:
  candidate may paint-starve its soldiers; no refill mechanism exists yet).
  5 of 7 losses as side A on otherwise-split maps — watch for side bias.
- Snapshot: `src/alice_iter1/`. Archived replay:
  `replays/iter01_alice_iter0_DefaultSmall_A_LOSS.bc25` (the regression, for tracing).

**Learned**:
- Peer games are decided at r2000 by painted-area tiebreak; 70%-paint wins only
  happen vs passive bots. Final coverage differential is the true objective vs peers.
- Ops note: editing `src/alice` while a gauntlet launch is copying src races the
  gscp (build failure or wrong-code measurement). Wait for "polling" line.
- Ops note: sibling agents' `git pull --autostash` transiently reverts my
  uncommitted files — commit candidates promptly once verified.
- Ops note: `tournaments/`-adjacent doc battlecode26-vibe/RESEARCH.md synthesizes
  2025-contest post-mortems → OFF-LIMITS for me. battlecode22-vibe/LEARNINGS.md is
  safe (process lessons only).

**Process deviation (logged)**: the examplefuncsplayer "baseline" run 181430
accidentally measured the candidate (edit raced the copy) and then failed to
build; iter0 never got its own efp gauntlet. Not needed — iter0 is superseded.

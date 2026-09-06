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

**Noise floors** (binomial, one-sided vs p=0.5): 24-game H2H — 16/24 ≈ 92%
confidence, 17/24 ≈ 97%. Treat 13-15/24 as within noise of 50% (near-miss zone).

**Fixed-roster plan (per coordinator update 2026-09-06)**: run the fixed old-bot
roster every ~5 accepted iterations; roster = every 5th accepted snapshot
(iter1, iter5, iter10, ...), additive (never replace entries). First roster run
due at accepted iteration ~5; roster currently = {alice_iter1}.

---

## Iteration 2 — build PAINT towers, not money towers (running)

**Trace evidence** (replaydump on iter01 DefaultSmall loss): T1 ended r2000 with
$113k UNSPENT chips, 21 soldiers, 182 idle moppers, 5 towers (T2: 7). Coverage
stuck ~32-38% both sides. Zero combat deaths in 2000 rounds. Soldier id13054:
spawned 200 paint → 0 by r33 → dead of paint starvation r48 (~45-round life).
Money is worthless; PAINT is the binding resource; money towers have zero paint
income and go dead as spawners after ~2 units (start 500, no regen).

**Hypothesis**: replacing all soldier tower-builds (mark/complete
LEVEL_ONE_MONEY_TOWER) with LEVEL_ONE_PAINT_TOWER multiplies sustainable paint
production (each L1 paint tower +5/turn) and hence unit production + coverage.

**Pre-registered**: (1) H2H vs alice_iter1 > 50% on EVAL12 both sides;
(2) mechanism check — in the re-run DefaultSmall game, T1 spawns PAINT_TOWERs
(replay SPAWN lines); (3) vs alice_iter0 stays >= 60%.
Run: 20260906-182917 (OPPONENTS = alice_iter1 alice_iter0).

**Result: REJECTED as-is — 10/24 (42%) vs iter1, 12/24 (50%) vs iter0.**
Mechanism engaged (DefaultSmall replay: T1 built PAINT_TOWER r18, chips fully
spent ~$100-300 all game, 92 soldiers by r2000, coverage 524m vs 204m — flipped
the motivating swept-loss into a crushing win). Diff shape: swept-LOSSES
concentrated on the LARGE maps (DefaultMedium/Large/Huge, Money) — with all
builds as paint towers, the single L2 money tower (30 chips/turn) cannot fund
1000-chip tower builds + 250-chip soldiers on ruin-rich maps: chips become the
binding resource. Specific, well-understood failure mode → one targeted
refinement (2b).

**Economy model (established this iteration)**:
- Each NEW tower = +500 spawn-paint instantly for 1000 chips: the dominant
  chips→paint conversion. Tower count compounds through MONEY income.
- Upgrades do NOT refill tower paint (engine InternalRobot.upgradeTower —
  health/level only).
- When ruins run out, only paint towers + SRPs convert anything into paint.
- Well-fed soldier throughput is the coverage engine (DefaultSmall: 92 soldiers
  = 52% coverage vs 22 soldiers = 20%).

## Iteration 2b — self-calibrating tower type (running)

**Refinement**: tower type chosen at mark time: money < 1200 chips → MONEY
tower, else PAINT tower. Completion tries both types (mark decided the pattern).
**Pre-registered**: H2H vs iter1 > 50%; large-map swept-losses (DefaultMedium/
Large/Huge, Money) at least half recovered; DefaultSmall stays won.
Run: 20260906-184031 (OPPONENTS = alice_iter1 alice_iter0).

**Mid-run trace (DefaultLarge botA, LOSS)**: candidate built ONE tower after the
start (r23, paint) and then none for the rest of the game (3 towers vs iter1's
11). Money pinned $50-250 all game: unit spawns (250/chip each, greedy) consume
every chip, so the 1000-chip completeTowerPattern can never fund. iter1's chip
mountain was an accident that FUNDED its tower expansion. 2b's type threshold
(<1200 → money) is nearly always true under chip starvation, but type was never
the binding problem — completion funding was.

**Result 2b: NEAR MISS (not accepted)** — 13/24 (54%) vs alice_iter1,
17/24 (71%) vs alice_iter0. 13/24 sits inside my own noise band (13-15/24 ≈ 50%),
so this does not clear the primary accept test on the evidence, per doctrine
("~50% is a near miss, not an accept, absent a separate mechanistic argument").

Diff vs 2a (tools/diff-runs.py, 48 common games, 18 flips: +13/-5) has a clean
one-directional shape on exactly the pre-registered maps: DefaultHuge +4,
Money +3, Oasis +3, DefaultMedium +2, DefaultLarge +1 (all the big-map
swept-losses 2a created), paid for with DefaultSmall -2, Paintball -2,
sierpinski -1. The refinement did what it was designed to do; it just traded
small maps for big ones rather than fixing the underlying constraint.

**Why it is still not the right fix**: the DefaultLarge trace shows the binding
constraint is not tower TYPE at all — it is that unit spawning consumes every
chip so 1000-chip completions never fund. 2b only shifted which type gets built
in a chip-starved regime. Refine once more at the actual mechanism (2c).

## Iteration 2c — chip reserve for tower completion (running)

**Change** (chip-budget discipline): towers only spawn units when money >= 1450
(reserving ~1200 ≈ one tower build). Tower type switched from a money threshold
to ruin-position parity ((x+y)&1) — a ~50/50 money/paint mix decided by map
geometry, identical for both teams, immune to the timing artifact that made
every early mark a money tower under 2b's threshold.
**Pre-registered**: (1) H2H vs alice_iter1 > 50% AND >= 16/24 to clear the noise
band; (2) mechanism — towers built in a DefaultLarge trace materially above 3;
(3) the big-map recoveries from 2b (Huge/Money/Oasis) are retained.
Run: 20260906-185051.

**Result: ACCEPTED as iteration 2** (snapshot `src/alice_iter2/`).

| pre-registered criterion | result | verdict |
|---|---|---|
| (1) H2H vs alice_iter1 > 50% and >= 16/24 | **20/24 (83%)** | PASS (far outside the 13-15/24 noise band; 20/24 ≈ 99.9% one-sided) |
| (2) DefaultLarge towers materially above 3 | **16 towers** (vs iter1's 8) | PASS |
| (3) Huge/Money/Oasis recoveries retained | won from BOTH sides on all three | PASS |

Overall 41/48 (85.4%); vs alice_iter0 21/24 (88%) — regression check clean.
Mechanism replay archived: `replays/iter02_alice_iter1_DefaultLarge_A_WIN.bc25`
(r2000: mine 16 towers / cov 562‰ / 52 soldiers vs iter1 8 towers / cov 161‰ /
24 soldiers). The chip reserve works exactly as designed: iter1 stalls at 8
towers, 2c compounds to 16.

**Diff shape vs 2b** (48 common games, 19 flips, **+15 / -4**): gains spread
across 7 maps (Circuit +4, DefaultLarge/Medium/Small/Paintball +2 each,
Money/Oasis/sierpinski +1) — broad, one-directional, not churn. The only
concentrated regression is **maze: -3 (swept-loss vs iter1 both sides, plus
iter0 side A)**. Carried as a known unresolved regression, traced below; per the
precedent set at iteration 1 (DefaultSmall), a concentrated regression inside a
+15/-4 accept becomes the next target rather than a veto.

### Trace: why maze regressed (and the degeneracy it exposed)
`replay-dump` on `alice_iter1__maze__botA` (60x60, coverage 159‰ vs 168‰ at
r2000 — both teams are barely painting anything):
- T1 (2c) ends with **19 soldiers and 183 moppers**; T2 (iter1) 20 / 179.
- **`MopAction` count is 0 in every sample window of the entire game.** The
  moppers never mop. They never paint either (moppers have no paint action).
  They are ~90% of the army and contribute literally nothing.
The same shape, larger, on the DefaultLarge mechanism replay: **677 moppers vs
52 soldiers at r2000, with $120,840 unspent chips**, and coverage that *peaks*
at 604‰ (r1000) and then **declines to 562‰**.

**Root cause of the mopper glut (mechanistic, from the cost table)**: mopper
costs 100 tower-paint, soldier 200. Tower paint — not chips — is the binding
spawn resource (money towers produce 0 paint; paint towers 5-15/turn). A tower
sitting at 100-199 paint *cannot* build the soldier the 75% branch asks for, so
that turn spawns nothing; on the 25% mopper turns it always can. The spawn mix
is therefore nowhere near 3:1 in practice — it converges on moppers, and each
mopper built consumes exactly the paint a soldier needed.

**Secondary harm**: 677 wandering moppers put allies permanently inside the
adjacency tax (-1 paint per adjacent ally per turn, -2 on enemy paint), which
is a plausible cause of both the soldier paint starvation (~45-round lifetimes,
first seen at iteration 2) and the late-game coverage *decline*.

---

## Iteration 3 — stop building moppers (running)

**Target selection**: not a loss-sampled target — an absolute degeneracy signal
(TRAINING_ALGORITHM step 1: "prefer absolute degeneracy signals over
opponent-relative comparisons"). 677 units performing 0 actions needs no
opponent to be wrong. It also matches the recurring winner's profile in the
cross-year research: *removing pure waste*.

**Hypothesis**: moppers are pure waste in the current bot — 0 mop actions
observed across two full games, no paint contribution, 300 chips + 100
tower-paint each, and they crowd out soldiers for the binding resource (tower
paint) while taxing allies through adjacency. Building only soldiers redirects
tower paint into the coverage engine and raises final painted area.

**Change** (single, isolated): `runTower` spawn line — always `SOLDIER`.

**Pre-registered**:
1. H2H vs `alice_iter2` on EVAL12 both sides **> 50% and >= 16/24** (noise band).
2. Mechanism, on a DefaultLarge re-run vs alice_iter1: mopper count at r2000
   **< 50** (from 677) and soldier count **materially above 52**; final coverage
   **above 562‰**.
3. No new swept-loss on a map 2c wins from both sides (DefaultSmall/Medium/
   Large/Huge, Paintball, Money, Gears, Circuit, Oasis).
4. maze does not get worse (it is already a swept-loss; if it recovers, the
   adjacency-tax half of the hypothesis gains support).

**Representativeness pre-check (doctrine #4)**: moppers are the bot's only
answer to enemy paint, so cutting them is a defensive ablation. Does the
evaluating pool pose the threat? *No* — my whole lineage paints with soldiers,
which by engine rule cannot overwrite enemy paint, and no lineage member builds
splashers. So enemy paint is never contested by anyone and the defense is
untested by this instrument. Recorded explicitly: **if a sibling bot in the
tournament fields splashers/moppers aggressively, this decision must be
re-opened** — the gauntlet cannot see that threat.

### Standing bytecode check (2b build, DefaultLarge full 2000-round game)
Rounds 1000-1999: **0 overruns, 0 near-misses** (indicator counters OVR=/near=
never appear). Peak observed: soldiers 1638 / 17500 (9%), towers 534 / 20000
(3%). **Implication**: bytecode is nowhere near binding — expensive logic
(BFS/bug-nav, symmetry inference, per-tile pattern computation, wider sensing
loops) is affordable and should not be avoided on cost grounds.

### Planned: play-symmetry (mirror) audit — Phase 0 item 7
Once a candidate is snapshotted, `alice` vs `alice_iterN` is byte-identical, so
the acceptance H2H *is* a mirror match: any map with a persistent one-sided
result is a play-symmetry bug, not opponent strategy. Standing signal to watch:
iter1's losses were 5-of-7 on side A. Known fixed-absolute-order sites in my
code to audit if a lopsided split appears: `directions[]` compass order in
tower spawn-ring scan and `wander`, and every "first satisfying result" loop
over `senseNearbyMapInfos` (engine scan order is x-then-y ascending, an
absolute order — see RULES.md).

### Structural gap identified (candidate iteration 4)
Soldiers **cannot overwrite enemy paint** (engine: paints only if tile empty or
already ally). My coverage engine is entirely soldiers, so the bot is
structurally unable to convert enemy territory — a hard ceiling on the
painted-area tiebreak that decides every peer game. Only splashers convert
enemy paint directly (r^2<=2 of center), and the bot has never built one.
Coverage economics: soldier 0.20 tiles/paint (empty/ally only); splasher 0.26
tiles/paint plus up to 5 enemy conversions per attack. Draft prepared.

*Trigger-frequency pre-check* (BC22 lesson — verify the gate fires): at r1000 on
DefaultLarge, coverage was 31% mine / 39% enemy / ~30% empty, so a typical
13-tile splash area holds several enemy and several empty tiles; a
score>=6 gate (enemy*2 + empty) fires routinely rather than being dead code.
This is an estimate from aggregate coverage, not a per-tile count — if the
iteration is run, confirm with actual SPLASH action counts in the replay.

### Engine trap found (RULES.md updated)
`transferPaint(loc, -N)` credits the withdrawer through `addPaint`, which clamps
at capacity, while the tower is debited the FULL N. Over-asking silently burns
tower paint. Any refill code must request `min(myCapacity - myPaint, towerPaint)`.

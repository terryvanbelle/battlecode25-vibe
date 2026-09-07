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
- **`MopAction` count is 0 in every sample window of the entire game.**
  *(CORRECTION, made the same day — see the engine check below: `MopAction` is
  emitted only by `mopSwing`, which my bot never calls. A mopper's ordinary mop
  emits `UnpaintAction`. The zero is therefore uninformative; the real
  utilisation figure is in the correction and is ~0.3%, not 0%.)*
  Moppers never paint either (moppers have no paint action).
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

**CORRECTION — engine check of the replay-action semantics** (done while the
run was in flight, before reading its result; `InternalRobot.java` +
`GameMaker.java` from the official engine source):
- `Action.MopAction` is emitted **only** by `mopSwing` (the 6-tile cardinal
  swing), twice per swing. My bot never calls `mopSwing`, so `MopAction == 0`
  was guaranteed a priori and measures nothing. **My "zero mop actions" claim
  above was wrong as stated.**
- A mopper's ordinary `attack(loc)` emits `Action.UnpaintAction` (and
  additionally `AttackAction` when an enemy robot stands on the tile).
- `addUnpaintAction` has exactly one call site in the whole engine
  (`InternalRobot:417`, inside `mopperAttack`), so the dump's `u` counter is
  precisely "tiles mopped by this team", and nothing else.

**Restating the evidence correctly.** DefaultLarge, per 250-round window,
(moppers alive → tiles mopped): 33→48, 104→131, 187→79, 282→78, 381→90,
479→57, 577→34, 677→18. Mop cooldown is 30, so a fully-employed mopper mops
~8 times per 250-round window and 677 of them could mop ~5400 tiles; they
managed **18**. **Utilisation ≈ 0.3%, and the absolute output falls as the
mopper population grows.** A mopped tile also does not become mine — it becomes
EMPTY — so 18 tiles per 250 rounds on a ~2500-tile map is worth essentially
nothing on the painted-area tiebreak either way.

So the hypothesis survives the correction, with a weaker verb: moppers are
~0.3% utilised rather than literally idle. Logged rather than quietly patched,
because "count X was zero" from a replay dump is only evidence once the
emitting call site is confirmed — that check should precede any future claim
built on a replay counter.

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

### Non-blocking work while iteration 3 runs

**Tournament 20260906-1755 read (sanctioned channel)**: *every one of the 12
games was won by side B*, all on the painted-more tiebreak. Discount heavily
for replication — that run predates the protocol commit (18:05) and all three
bots were still the seeded example copy, so the 12 rows are really 2 distinct
games (DefaultSmall, DefaultMedium) replicated across 6 pairings. Evidence
value: **2/2 mirror games won by side B**, not 12/12.

But it lines up with signals in my own runs:
- 2c gauntlet, FourCorners: **side B won all 4 games** (I win as B at r584/r397,
  I lose as A at r1353/r1587 — two different opponents).
- sierpinski: within each pairing the same side won both games.
- iteration 1: 5 of 7 losses were as side A.

**Mechanism hypothesis for a B-side advantage (fixed-absolute-order bug class,
Phase 0 item 7)**: `senseNearbyMapInfos` returns tiles in x-ascending then
y-ascending order (RULES.md). Three of my selection loops break ties by
first-found with a *strict* comparison, so among equidistant candidates they
always take the most south-west one:
- `runSoldier` ruin choice — `if (d < bestD)`
- `runSoldier` idle-paint target — `if (d < paintD && ...)` (added in iteration 1)
- `runSplasher` target — `if (score > bestScore)`
(`runMopper` is the opposite: no `break`, so it takes the *last* = most
north-east tile.)
A south-west preference is not team-symmetric on a map where the two spawns sit
at opposite corners/edges: the bottom-left team paints back toward its own
already-owned corner and off the map edge, the top-right team paints toward the
unclaimed centre. Under all three guaranteed symmetry classes the SW-preferring
team that starts in the SW wastes its bias and the other team's bias points at
open ground — i.e. a systematic edge for whichever team starts further from the
origin. Timing cuts the other way (team A's robots have lower IDs and by
`(roundsAlive, ID)` act first every round), so if B still wins, the tie-break
bias is beating the first-mover edge.

**Instrument being built for this (iteration 4)**: `src/alice_mirror/` — a
byte-identical copy of `alice_iter2` under a different package, so
`alice` vs `alice_mirror` is a true mirror match. In a mirror, any map where
the *same side wins both games* is positional, and any inter-team stat
difference is positional rather than policy (TRAINING_ALGORITHM Phase 0 #7).
Measurement plan:
- **M0 (baseline asymmetry)**: `alice_iter2` vs `alice_mirror`, EVAL12, both
  sides. Pre-registered statistic: *number of maps out of 12 won by the same
  side twice*. Under a symmetric policy the null is Binomial(12, 1/2) ⇒ mean 6;
  ≥10 of 12 would be significant at ~2%.
- **M1**: same run after the tie-break fix; the statistic must fall.
Two candidate fixes, to be run as a dose pair rather than assumed:
  (a) randomize the equidistant tie-break (pure fairness);
  (b) prefer, among equidistant candidates, the one *farthest from my own
      nearest tower* — team-relative, therefore symmetric, and it adds real
      frontier expansion instead of noise.
Carrying the algorithm's caution explicitly: a consistent arbitrary preference
can be supplying formation cohesion that randomization destroys, so (a) may
regress even if it removes the asymmetry. Measure both; the mirror statistic
and the H2H win rate are separate questions.

### Soldier life-cycle trace (iter2 build, DefaultLarge, soldier id12472)
Full per-turn track from spawn to death, `replay-dump --robot 12472`:
- r2 spawn at 194 paint; paint falls ~5-6/round (5 = one paint action, +1 =
  neutral-tile upkeep); the r6 step is -30 (`markTowerPattern` costs 25).
- r6-r28 it oscillates between (3,16)/(4,15)/(2,15) filling the tower pattern,
  and completes a MONEY_TOWER at (3,15) on r28. Productive.
- **r17 onward its cooldowns start rising** (mCD/aCD 11 → 26): the low-paint
  cooldown penalty (below 50% stash, cooldowns scale by (100 - 2·paint%)).
  From ~r24 it acts roughly every other round instead of every round.
- r30-r43 it wanders to the map edge (0,6) and paint hits 0 at r44.
- r44+ it takes -20 HP/round and dies. **Total life 41 rounds for one tower
  pattern and ~35 painted tiles.**

Durable consequences (these constrain every future economic iteration):
1. **A soldier's whole output is bounded by the paint it was born with** — 200
   paint ⇒ at most 40 tile-paints at 5 each, minus upkeep, minus the 25 for a
   pattern mark. There is no refill anywhere in the bot. Cumulative team
   coverage is therefore bounded by cumulative *paint production*, not by chips
   or by unit count.
2. **The last third of every soldier's life is spent at penalty cooldowns**,
   i.e. paint is not just a budget, it is a throughput multiplier. Keeping a
   soldier above 50% stash is worth roughly double its action rate.
3. **Chips are not the binding resource and haven't been since iteration 2c**
   ($120,840 idle at r2000 on DefaultLarge; $57,440 on maze). Any chips→paint
   conversion is nearly free money.

### Chips→paint conversions available (ranked, for the next iterations)
Verified against the engine source, not inferred:
- **Tower self-upgrade — free action.** `assertCanUpgradeTower` calls
  `assertCanActLocation(loc, 2)`, which checks *only* range and on-map: it does
  NOT check action readiness, and `upgradeTower` adds no cooldown. A tower
  upgrading itself (distance 0) therefore costs chips and nothing else, every
  turn it can afford it. Paint income 5→10→15/turn; cost 2500 then 5000.
  `UnitType.getNextLevel()` returns null at L3, so the guard is trivial.
  Drafted (scratchpad `upgrade-draft.java`) as iteration 4.
- **SRP** — 200 chips for +3/turn to *every* producing tower, both kinds. At 16
  towers that is +24 paint/turn and +24 chips/turn for 200 chips, an order of
  magnitude better per chip than an upgrade, but it needs a 5x5 pattern held
  undisturbed for 50 rounds. Draft exists (scratchpad `srp-draft.java`) and
  needs porting to the current `rc`-as-parameter code shape.
- **New towers** — 1000 chips for +500 instant paint (established iteration 2);
  already implemented, capped by ruins and the 25-tower limit.

### Functional-area map (refreshed after iteration 2)
| area | status | last touched |
|---|---|---|
| ruin completion / tower building | money+paint by ruin parity; chip reserve funds completions | iter2 (accepted) |
| paint spread | soldier own-tile + nearest-empty idle paint | iter1 (accepted) |
| economy (chips curve, upgrades) | **chips pile up unspent ($120k)**; no upgrades, no SRPs | never |
| soldier paint sustain | none — 41-round life, no refill, penalty cooldowns for the last third | never |
| mopper usage | 25% of spawns, ~0.3% utilised; iteration 3 tests removing them | iter3 (running) |
| splasher usage | code exists, never built; only unit that can convert enemy paint | never |
| micro vs towers/units | none (zero combat deaths observed in 2000-round games) | never |
| SRPs | none | never |
| comms | none | never |
| navigation | wander + slide; soldiers walk into map corners and die there | iter0 |
| map symmetry inference | none | never |
| play-symmetry hygiene | 3 fixed-absolute-order tie-breaks identified, unfixed; mirror instrument built | iter4 planned |

---

## Instrument change (coordinator, 2026-09-06 ~20:30) — EVAL12 retired

`tools/gauntlet.sh` now draws a **fresh random 25-map sample** from the 75-map
list whenever `MAPS` is unset, and records it to `<run>/maps.txt`. Routine
evaluation runs must stop passing a hand-picked `MAPS=` list: a standing list is
an overfitting surface, and my `EVAL12` was exactly that. **EVAL12 is retired**;
default runs are now 25 maps x both sides x N opponents (100 games for two
opponents), `NMAPS=40` for close calls.

Consequences for how I read my own numbers:
1. **Within a run, comparisons stay exact** — the sample is drawn once and every
   opponent plays the same maps. My accept gate is a within-run head-to-head, so
   the gate itself is unaffected.
2. **Across runs the instrument now changes**, so raw win-rate deltas between
   two runs are no longer like-for-like. Iteration 2's 83% (EVAL12, run
   20260906-185051) and any later percentage are **not** measured on the same
   instrument and must not be trended against each other.
3. When run-to-run comparability is actually required — a regression check
   against an older snapshot, a feature ablation, a dose sweep, or re-running a
   single game to trace it — **pin the maps**:
   `MAPS="$(cat gauntlet/<run-id>/maps.txt)"`.
4. **Iteration 3 is the last EVAL12 run.** Its comparison to iteration 2 is
   still valid (both on EVAL12, and iteration 3's own head-to-head is
   within-run), but the sample is 12 maps and the noise band from iteration 1
   (13-15/24 ≈ 50%) applies to it, not to the wider 25-map runs that follow.
   New noise band for a 50-game head-to-head: ≥30/50 (60%) is ~92% one-sided,
   ≥32/50 (64%) is ~98%; treat 24-29/50 as inside noise of 50%.

---

## Iteration 3 — RESULT: REJECTED, and the hypothesis is refuted, not just unproven

Run 20260906-201852 (EVAL12, both sides, opponents alice_iter2 + alice_iter1).

| pre-registered criterion | result | verdict |
|---|---|---|
| (1) H2H vs alice_iter2 > 50% and >= 16/24 | **7/24 (29%)**, 7 swept-losses | FAIL, decisively |
| (2) moppers < 50, soldiers >> 52, coverage > 562‰ | moppers 0, soldiers **314**, coverage **467‰** | mechanism engaged; outcome inverted |
| (3) no new swept-loss on maps 2c swept | new swept-losses on DefaultSmall, DefaultLarge, Paintball, Money, Gears, Oasis, FourCorners | FAIL |
| (4) maze not worse | maze **flipped to 2/2 wins** | PASS (the one thing that worked) |

vs alice_iter1 it scored 13/24 (54%) — but iter1 also builds moppers, so that
comparison cannot separate the mechanism; the accept gate (vs iter2) is the
instrument that matters and it is unambiguous.

### Trace of the flip (DefaultLarge, bot=A, win→loss)
T1 = iteration 3 (no moppers), T2 = alice_iter2:

| round | T1 cov | T1 sold | T1 paint-acts | T2 cov | T2 mop | T2 unpaints |
|---|---|---|---|---|---|---|
| 250 | 536‰ | 51 | 743 | 200‰ | 7 | 8 |
| 500 | **562‰** | 88 | 57 | 398‰ | 15 | 19 |
| 750 | 519‰ | 127 | 85 | 456‰ | 54 | 148 |
| 1000 | 497‰ | 164 | 50 | 485‰ | 87 | 81 |
| 1500 | 478‰ | 238 | 128 | 502‰ | 222 | 136 |
| 2000 | **467‰** | **314** | 83 | **509‰** | 405 | 87 |

T1 finished with **$204,780 unspent**.

**Two mechanisms, both the opposite of what I predicted:**

1. **Unbounded soldier population is self-destructive.** Removing the mopper
   branch did not redirect tower paint into *painting* — it redirected it into
   *bodies*. 314 soldiers on a 50x30 (1500-tile) map is one unit per five tiles,
   so essentially every soldier is permanently adjacent to several allies, and
   the adjacency tax is -1 paint per adjacent ally per turn. The whole army sits
   at ~0 paint: paint actions collapse from 743 per 250 rounds at r250 to ~80
   for the rest of the game, with **four times as many soldiers doing them**.
   The mopper branch in iter2 was accidentally acting as a **population
   regulator** — it burned tower paint on units that then stopped consuming
   anything, capping the soldier count near the density where the adjacency tax
   is still survivable. That is why iteration 2c works, and I did not know it.

2. **Moppers are an offensive weapon and my pool does use it.** T2's `u`
   (UnpaintAction = tiles mopped) runs 81-148 per 250-round window all game.
   T1's coverage *peaks at r500 and then falls 95‰* — it is being erased faster
   than 314 starving soldiers can repaint it, and T1 has nothing that can erase
   T2's paint back (soldiers cannot overwrite enemy paint). My iteration-3
   representativeness note claimed "no lineage member contests enemy paint";
   **that was wrong** — moppers contest it, and I measured their utilisation on
   a game where they were starving in a 677-strong crowd rather than one where
   there was enemy paint worth mopping.

### What this iteration bought (a reject that paid for its run)
- **Coverage is not monotone.** It is a *stock* under attack, not a running
  total. Every previous iteration implicitly treated painting as cumulative.
- **Unit count has an interior optimum** set by the adjacency tax, and nothing
  in the bot currently regulates it. New functional area opened:
  *population control / anti-clumping*.
- **The paint-erasure race is a real axis of the game** that my bot participates
  in only by accident.

### Closed-directions ledger
| direction | closed by | can re-open if |
|---|---|---|
| Remove moppers entirely (spawn 100% soldiers) | iteration 3: 7/24 (29%) vs iter2, DefaultLarge trace shows soldier population runs to 314 and coverage decays 562→467‰ | a population cap exists *first*; the failure was density, not the mopper's absence per se. Re-test only after anti-clumping/population control is in. |

### Registered follow-ups from this trace (not started)
- **Mopper dose sweep** (0 measured, 1/4 = iter2 measured; missing 1/8 and 3/8).
  Cheap, and the curve would tell whether iter2's 1/4 is near the optimum. Must
  be run with `MAPS="$(cat gauntlet/20260906-201852/maps.txt)"` to stay
  comparable to the two doses already measured.
- **Anti-clumping**: soldiers prefer moves that reduce adjacent-ally count.
  Directly attacks the tax that iteration 3 exposed.
- **Purposeful moppers**: send moppers at enemy paint instead of wandering.

---

## Iteration 4 — towers upgrade themselves with idle chips — RESULT: ACCEPTED

**Area**: economy (leaving the mopper area after its reject, per the algorithm's
functional-area discipline).

**Motivating evidence, absolute rather than opponent-relative**: every game of
every iteration so far ends with a chip mountain the bot cannot spend —
$113k (iter1), $120,840 (iter2), **$204,780 (iter3)** — while paint bounds
everything the bot does. Chips are pure waste in a resource-conversion game.

**Hypothesis**: a tower upgrading itself converts idle chips into permanent
paint income (5→10→15/turn) and chip income (20→30→40/turn) at *zero* action
cost, raising the cumulative paint production that caps team coverage.

**Engine verification done before writing the code** (not inferred from
behaviour): `RobotControllerImpl.assertCanUpgradeTower` calls
`assertCanActLocation(loc, BUILD_TOWER_RADIUS_SQUARED=2)`, which checks *only*
range and on-map — it does **not** check action readiness — and `upgradeTower`
adds no cooldown. So a tower upgrading itself (distance 0) spends chips and
nothing else. `UnitType.getNextLevel()` returns null at level 3, so the guard is
exact rather than a magic constant.

**Change** (single, isolated), at the top of `runTower`:
upgrade self when `getNextLevel() != null` and
`money >= nextLevel.moneyCost + CHIP_RESERVE`. The existing spawn gate's literal
1450 is lifted into the named `CHIP_RESERVE` constant it already was
conceptually — no behaviour change there.

**Pre-registered**:
1. H2H vs `alice_iter2` **> 50%**, and clear of the noise band for this run's
   sample size (50 games ⇒ **>= 30/50**).
2. Mechanism: in a DefaultLarge trace, `UPGRADE` lines appear after round 1 for
   towers other than the four starting ones, and end-of-game unspent chips fall
   materially below iteration 2's $120,840.
3. Regression: vs `alice_iter1` stays >= 60%.
4. Watch (not a gate): whether higher paint income re-creates iteration 3's
   population blow-up. If soldier count at r2000 exceeds ~150 on DefaultLarge,
   the adjacency tax will eat the gain and population control becomes the
   blocking prerequisite for every economic iteration.

**First run on the new instrument**: `MAPS` unset ⇒ fresh random 25-map sample,
both sides, opponents alice_iter2 + alice_iter1 = 100 games.
Run: 20260906-2053 (id in `gauntlet/`).

**Ops note (2026-09-06, iteration 4 launch)**: my gauntlet's stdout was
redirected to a file under the session scratchpad
(`/tmp/claude-1000/-home-terryvanbelle-projects-vibe-2025/<session>/scratchpad/g4.log`)
and a sibling agent's gauntlet wrote its own progress into the *same absolute
path* — NUL padding plus interleaved lines, i.e. two processes with independent
offsets on one file. My progress output was clobbered and I was passively shown
another agent's gauntlet lines (an isolation hazard, since gauntlet results are
not a sanctioned channel — only `tournaments/` is). No measurement was
affected: the authoritative record is `gauntlet/<run>/results.txt`, pulled from
my own workspace-scoped remote path, which the collision cannot touch.
**Standing fix: never redirect run output into the shared /tmp tree — use
`agents/alice/logs/`, and poll `gauntlet/<run>/results.txt` for progress.**

### Iteration 5 prepared while iteration 4 runs — anti-clumping spread step

**Engine check first** (`InternalRobot.processEndOfTurn`, lines 622-639), because
the whole idea rests on how the adjacency tax is applied and I had been quoting
`RULES.md` rather than the code:
```
allyRobotCount = ally robots within r^2 <= 2 (the 8 neighbours), excluding self
neutral tile : -1*mopperMult  -1*allyRobotCount
enemy tile   : -2*mopperMult  -2*allyRobotCount
ALLY tile    :  0             -1*allyRobotCount
```
**The clumping tax is not waived by standing on your own paint** — the `else`
branch still charges `-allyRobotCount`. So a fully-surrounded robot pays up to
-8 paint/turn *anywhere on the map*, against a 200-paint soldier stash (100 for
a mopper). Nothing in the bot is aware of this, and iteration 3 showed it is the
binding failure once density rises.

**Change** (isolated, one dose parameter): a soldier with no ruin to work and
`>= SPREAD_AT` ally *robots* within r²≤2 steps away from their centroid instead
of wandering. Towers are excluded from the count — being next to a tower is not
the problem, and a soldier fleeing its own spawn tower would be a regression.
Draft in scratchpad `iter5-antclump-draft.java`.

**Dose plan** (doctrine #2, with the mandatory zero arm): SPREAD_AT off (= the
accepted build), 2, 3, 5 — run pinned to one map sample so the arms are
comparable.

### Play-symmetry instrument now exists
`src/alice_mirror/` created: byte-identical to `src/alice_iter2/` apart from the
package line (verified with a body diff). `BOT=alice_iter2
OPPONENTS=alice_mirror` is therefore a true mirror. **Not yet run** — the VM is
congested with three agents and an accept-gate run outranks an audit; queued as
the next non-candidate run. Pre-registered statistic stands: number of maps
where the same side wins both games, null Binomial(n, 1/2).

### Ops: throughput on the shared VM (iteration 4 run)
The 100-game run is completing ~4 games per 11 minutes with three agents plus
BC26 on the box (load ~7.6 on 8 vCPUs, all 5 BC25 semaphore slots held
continuously). That is ~4.5 hours for 100 games and longer than the runner's
180-minute poll deadline. **Not a failure — the semaphore is doing its job** —
but it changes run design:
- Opponents are iterated in the OUTER loop, so a truncated run yields complete
  data for the *first* opponent. Always list the accept-gate opponent first
  (`alice_iter2` here); a deadline truncation then costs the regression check,
  not the gate.
- For dose sweeps and audits, drop to `NMAPS=12..15`; resolution scales with
  sample size but three arms at 24 games each beats one arm at 100 that never
  finishes.
- Plan roster runs at `NMAPS=15` (60 games) rather than the default 25.

### If iteration 4 is a near miss, the pre-registered refinement is
**upgrade paint towers only.** Chips are not scarce, so a money tower's
20→30/turn buys more of the resource I already cannot spend, while a paint
tower's 5→10/turn buys the one that binds. The uniform version was run first
because it is the isolated single mechanism; "which towers" is a dose on the
same mechanism, not a new one.

### Iteration 4 — RESULT: ACCEPTED (snapshot `src/alice_iter4/`)

Run `20260906-203042`, 25-map random sample, both sides, 100 games,
`GAUNTLET-COMPLETE`. **Session note**: my driver session was killed by an SSH
hangup at ~21:07 while polling this run; the run itself finished on
battlecode-dev and was recovered with `tools/gauntlet-collect.sh`. Nothing I
had chained on the driver survived, and nothing of mine was left running on the
VM (`gauntlet-collect.sh --list` confirms 5 runs, all `complete`).

| pre-registered criterion | result | verdict |
|---|---|---|
| (1) H2H vs `alice_iter2` > 50%, and ≥ 30/50 for this sample | **39/50 (78%)** | **PASS**, clear of the noise band |
| (2) UPGRADE lines after r1 for non-starting towers; unspent chips ≪ $120,840 | **7 self-upgrades**; end-of-game chips **$1,740** | **PASS** |
| (3) regression vs `alice_iter1` ≥ 60% | **48/50 (96%)** | **PASS** |
| (4) watch: population blow-up (soldiers > ~150 at r2000 on DefaultLarge) | 175 on DefaultLarge, 63 on Racetrack | see below |

Overall 87/100. Diff shape (accept condition 3): **swept-loss 0 vs both
opponents**, swept-win 14/25 vs iter2 and 23/25 vs iter1, 11 split-by-side.
There is no map where iteration 4 loses from both sides — no one-directional
regression anywhere in the run.

**Arm identity check (doctrine #3)**: `src/alice` vs `src/alice_iter2` differ by
exactly the upgrade block (the `1450` → `CHIP_RESERVE` rename is a no-op), so
this is a clean single-mechanism comparison — verified by body diff, not assumed.

### Mechanism trace — Racetrack, alice=A, WIN (`replays/iter04_alice_iter2_Racetrack_A_WIN.bc25`)

7 self-upgrades beyond the engine's round-1 four (six L1→L2, one **L2→L3** on the
starting paint tower at r1441); `alice_iter2` performs **zero**. The arms are
cleanly separated in the replay itself.

| round | alice $ | alice cov | alice tw | iter2 $ | iter2 cov | iter2 tw |
|---|---|---|---|---|---|---|
| 250 | 2,750 | 495‰ | 7 | 5,700 | 436‰ | 6 |
| 500 | 3,990 | 488‰ | 7 | 17,800 | 379‰ | 6 |
| 1000 | 3,090 | 505‰ | 8 | 40,700 | 304‰ | 6 |
| 1500 | 1,590 | 527‰ | 8 | 64,200 | 313‰ | 6 |
| 2000 | **1,740** | **555‰** | 8 | **87,100** | **283‰** | 6 |

Win by AREA_PAINTED. **The chip mountain is gone** ($87,100 → $1,740) and the
hypothesised causal chain is visible end-to-end: chips → tower level → paint
income → coverage *held flat* (495→555‰) where the baseline decays (436→283‰).
Iteration 3 established that coverage is a *stock under attack*, not a running
total; iteration 4 is the first change that funds defending that stock.

**A second, unhypothesised channel**: paint income also gates *spawning* (a spawn
costs paint from the tower's stash). Upgraded towers spawn more, so alice ends
Racetrack with 690 units to iter2's 297. I did not predict this and it is doing
part of the work — see the new closed thread below, because it cuts both ways.

### Engine fact corrected (I had this wrong)
**Starting towers are already level 2** (`RULES.md` line 22 says so; I had not
connected it). The four round-1 `UPGRADE` events in every replay are
engine-emitted for *both* teams' starting towers — they are **not** my code.
Built towers are always L1, and L1→L2 costs 2,500, so my gate needs
$2,500 + $1,450 = **$3,950** before it ever fires. Anywhere the bot's treasury
sits near the spawn floor, the feature is **dead code**.

That is exactly what happened on **DefaultLarge**, where alice held only 9 towers,
hovered at $1,210–1,460 all game and performed **zero** self-upgrades — so that
loss is a true mirror decided positionally, not evidence against the mechanism.
It also explains the shape of the result: **iteration 4 is worth a lot on maps
where the bot out-expands, and worth exactly nothing where it does not.** The
11 split-by-side maps are where to look next.

Criterion (4) resolves the same way: the 175 soldiers on DefaultLarge are not
attributable to this change (it never fired there); on Racetrack, where it fired
7 times, soldiers were 63 at r2000. No population blow-up caused by iteration 4.

### The real finding of this iteration (bigger than the accept)
Both teams' **mopper counts run away**: 627 (alice) and 269 (iter2) at r2000 on
Racetrack, a **25x25 = 625-tile map**. Alice fields 690 units on 625 tiles —
*more units than the map has squares*. Soldiers are 63 against 627 moppers even
though the spawn rule is 25% moppers, so soldiers are dying ~30x faster while
moppers accumulate essentially forever.

Iteration 3 diagnosed the adjacency tax (−1 paint per adjacent ally per turn,
charged **even on your own paint**) and concluded "unbounded soldier population
is self-destructive". The correction iteration 4 forces: **the population that is
actually unbounded is the mopper population, and it is unbounded in the accepted
build right now.** Paint actions per 250 rounds decay 295 → 99 across the game
while unit count quadruples. This is the same failure iteration 3 hit, and my
lineage has been carrying it the whole time on the other unit type.

### Closed-directions ledger (updated)
| direction | closed by | can re-open if |
|---|---|---|
| Remove moppers entirely (spawn 100% soldiers) | iteration 3: 7/24 (29%) vs iter2 | a population cap exists *first*; the failure was density, not the mopper's absence |
| "Upgrade paint towers only" as iteration 4's refinement | **not needed** — iteration 4 passed outright at 78%, so the pre-registered refinement was never spent | still open as a *dose* on iteration 4 if tower-type mix later matters |

### Functional-area map
- economy/chip conversion — **iteration 4, ACCEPTED** (first accept since iter2)
- moppers/unit mix — closed by iteration 3's reject (1 reject)
- population control / anti-clumping — **open, now the highest-value target**,
  and re-aimed from soldiers to moppers by this iteration's trace

---

## Instrument bug found and fixed — every "alive unit count" I have ever logged was wrong

Found while forming iteration 5's hypothesis, before spending a run on it.

`tools/replaydump/ReplayDump.java` tracked live robots in a `teamOf` map, removing
an id only in the `Round.diedIds` handler. **BC25 does not report robot deaths
there.** Deaths arrive as `Action.DieAction` inside a `Turn`'s action vector, and
the dumper's `DieAction` case only *printed* exception-deaths — it never removed
the robot. A 2000-round dump containing hundreds of deaths printed **zero** `DIED`
lines, which is what gave it away.

So `aliveCounts()` only ever incremented: every "sold N / mop N" figure in this
log is **cumulative spawns**, not units alive.

**Fixed** (my own tooling, `agents/alice/tools/`): `DieAction` now removes the
robot and counts a death; the round line additionally reports per-window spawns
by type (`+soldN +mopN`) and deaths (`diedN`), because a stock alone can't
distinguish a standing army from a treadmill.

### What the corrected instrument says about the accepted bot (Racetrack, iter4 vs iter2)
Same replay, before and after the fix:

| figure | broken instrument | corrected |
|---|---|---|
| alice soldiers alive @r2000 | 63 | **4** |
| alice moppers alive @r2000 | 627 | **30** |
| iter2 soldiers alive @r2000 | 28 | **0** |
| total alice units on a 625-tile map | 690 (impossible) | 34 |

**Three conclusions reverse:**

1. **There is no population runaway.** Iteration 4's write-up claimed 690 units on
   a 625-tile map; the real army is ~34. The "anti-clumping / population control"
   area I had just named the highest-value target was built on this artifact, and
   **the drafted iteration 5 spread-step is now unmotivated** — I have no evidence
   the bot is ever dense enough for the adjacency tax to bind.
2. **Iteration 3's root cause was also an artifact.** Its headline was "unbounded
   soldier population is self-destructive — 314 soldiers on a 1500-tile map".
   That 314 was cumulative spawns. Iteration 3's *result* (7/24, decisive) stands;
   its *explanation* does not.
3. **The real degeneracy is the opposite one: the army is a treadmill that barely
   exists.** alice spawns ~102 units and loses ~104 per 250 rounds while holding
   ~34 alive. iter2 finishes the game with **zero soldiers** — and soldiers are the
   only unit that can paint.

### The measured defect that replaces the density story
Realized spawn mix over Racetrack r1750-2000: alice **+9 soldiers, +93 moppers**.
The spawn line reads `(rnd(4) == 0) ? MOPPER : SOLDIER` — an *intended* 25%
moppers. The realized share is ~90%.

Cause, from the cost table: a soldier costs **200 tower paint**, a mopper **100**,
and a tower's paint income is only 5-15/turn. The tower can fund a mopper twice
as often, so it never accumulates the 200 a soldier needs — and when the RNG picks
SOLDIER and paint is short, the build loop simply **fails and builds nothing**,
wasting the turn. The mopper is quietly eating the soldier pipeline's fuel.

**Doctrine #2 applies directly**: the mopper-fraction "dose sweep" I had registered
as a follow-up (0, 1/8, 1/4, 3/8) would not have been a dose at all — the constant
it varies does not control the quantity that matters.

### Closed-directions ledger (correction)
| direction | status change |
|---|---|
| Anti-clumping / spread step (drafted iteration 5) | **withdrawn before evaluation** — motivated entirely by the inflated counts; no evidence density ever binds. Re-open only if a corrected trace shows high adjacency. |
| Remove moppers entirely (iteration 3) | reject **stands**, explanation **retracted**. Cause is not density; see iteration 5's trace for the real one (paint-erasure race). |

---

## Iteration 5 — reserve tower paint so moppers stop starving the soldier pipeline (running)

**Area**: spawn economics (a new area; the anti-clumping area was withdrawn above
before it cost a run).

**Motivating evidence** — absolute, not opponent-relative, per the algorithm's
preference for degeneracy signals: the tower's realized army mix is ~90% moppers
against an intended 25%, because a mopper costs 100 tower paint and a soldier 200
against an income of 5-15/turn. Moppers cannot paint; painted area is the win
condition. Both teams in every traced game end with 0-4 soldiers alive.

**Hypothesis**: the mopper is not out-competing the soldier on merit, it is
out-competing it on *price* against a trickling paint stash. Reserving tower paint
so a mopper is only built when a soldier would also have been affordable should
raise the soldier share, the paint-action rate, and coverage.

**Change** (single, isolated, one dose parameter `MOPPER_PAINT_RESERVE`): a tower
refuses to build a MOPPER unless it would still hold `MOPPER_PAINT_RESERVE` paint
afterwards. Refusing does **not** substitute a cheaper unit — the build fails and
the paint accumulates until a soldier is affordable, which is the point.
`MOPPER_PAINT_RESERVE = 0` reproduces the iteration-4 build exactly, so the zero
arm is `alice_iter4` itself, already frozen.

**Mechanistic verification done before evaluating** (algorithm step 4), dose 200,
Racetrack vs alice_iter4 — outcome class 2, *lost but mechanism engaged*:

| | iter5 (dose 200) | iter4 (dose 0) |
|---|---|---|
| spawns/250r @r2000 | +38 soldiers, **+0 moppers** | +11 soldiers, +91 moppers |
| paint actions/250r | 58-160 | 2-18 |
| unpaint actions/250r | **0** | 64-165 |
| coverage 500→2000 | 484 → **416‰** (decaying) | 463 → **544‰** (climbing) |

Dose 200 drives moppers to **exactly zero** — i.e. it lands in the policy
iteration 3 already refuted, by a different route. It painted ~10x more and still
lost, because it did **zero** mopping while the opponent erased its paint all
game. This is the cleanest evidence yet for a claim I had only asserted:
**coverage is a contested stock, and a bot with no paint-removal loses the stock
regardless of how fast it paints.** So dose 200 is rejected on the trace alone,
without spending a gauntlet on it.

**Evaluation design** (doctrine #2 — dose-response with a mandatory zero arm):
run `20260906-213750`, `BOT=alice_iter4` (the zero arm) vs `OPPONENTS="alice_r100
alice_r50"`, NMAPS=15, both sides = **60 games**. Running the *baseline* as BOT is
deliberate: one shared map sample then measures both doses against the identical
zero arm exactly, which three separate candidate-vs-baseline gauntlets would not.
The accept-gate number for a dose is `1 - (iter4's win rate against it)`.

**Pre-registered**:
1. **Accept gate** — a dose beats `alice_iter4` head-to-head > 50%; with 30 games
   per dose the noise band requires the dose to take **>= 18/30 (60%)**, i.e.
   `alice_iter4` scores <= 12/30 against it.
2. **Dose-response shape** — with dose 0 at 50% by definition and dose 200 already
   shown catastrophic, an interior optimum is the predicted shape. A monotone
   curve rising to 200 would falsify the whole reading and is the outcome that
   would send me back to the trace.
3. **Mechanism** — the winning dose's realized mopper spawn share must land
   strictly between the extremes (0% at dose 200, ~90% at dose 0), verified in a
   replay, not inferred from the win rate.
4. **Watch (not a gate)** — soldier *deaths* per 250 rounds. If the soldier share
   rises but deaths rise in proportion and coverage does not move, the binding
   constraint is soldier survival, not spawn mix, and that becomes the next area.

---

## RobotController API sweep (mandated periodic check) — three whole mechanics unused

Run while iteration 5's sweep was playing. Method list from `javap` on the engine
jar, differenced against every `rc.` call in `src/alice/`. Never called:

`transferPaint` `canTransferPaint` · `sendMessage` `readMessages`
`broadcastMessage` `canSendMessage` `canBroadcastMessage` ·
`markResourcePattern` `completeResourcePattern` `canCompleteResourcePattern`
`getResourcePattern` · `mopSwing` `canMopSwing` · `mark` `removeMark`
`senseRobotAtLocation` `getNumberTowers` `getChips` `sensePassability`
`onTheMap` `getMapWidth` `getMapHeight` `setIndicatorDot` `setIndicatorLine`
`setTimelineMarker` `disintegrate` `resign`

Three of these are not conveniences, they are **whole game mechanics my lineage
has never touched**, and each maps onto a measured problem:

1. **`transferPaint` — paint refill.** Any robot may withdraw from an ally tower
   (`transferPaint(loc, -N)`, r²≤2, CD 10). My bot has no transfer code at all, so
   **a unit's entire lifetime output is the paint it was born with**, and at 0
   paint it takes -20 HP/turn and dies. This is the mechanism behind the treadmill
   the fixed instrument exposed: ~104 deaths per 250 rounds, ~34 units alive.
   Today the bot's only way to put fresh paint in the field is to *respawn*, which
   costs 200 tower paint **plus 250 chips** and throws away a positioned veteran —
   a refill costs the same paint and **zero chips**. Ranked #1: it attacks a
   measured degeneracy, and it is the "capability preserved at zero marginal cost"
   shape the algorithm names as the recurring winner's profile.
2. **SRPs.** An active SRP gives **+3/turn to every producing tower** for 200 chips
   — with 7 towers that is +21/turn, comparable to a tower upgrade, priced in the
   resource I provably cannot spend ($87k-180k unspent). Fragile (one enemy mop
   inside resets the 50-round timer), so it belongs in the interior. Ranked #2.
3. **Communication.** Entirely unused; enabling rather than directly scoring.

Also noted from iteration 5's dose-200 trace: **iteration 4's chip sink is finite.**
Once every tower reaches L3, `getNextLevel()` returns null and chips pile back up
($180,890 by r2000). SRPs would reopen that sink.

Registered as the iteration 6 candidate (paint refill), ahead of SRPs.

### Death-cause probe — starvation, not combat, is what kills this bot

`DieType` carries only UNKNOWN/EXCEPTION, so I derived the cause instead: the
dumper now records each robot's last observed paint and classifies a death as
starvation when that paint was 0 (a robot at 0 paint takes -20 HP/turn and cannot
act until refilled). Measured on the Racetrack iter5-vs-iter4 replay, per 250
rounds:

| team | deaths | starved | share | transfers |
|---|---|---|---|---|
| iter5 (dose 200, soldiers only) | 33-44 | 29-40 | **~90-100%** (100% at r1250) | **0** |
| iter4 (accepted build) | 69-102 | 46-68 | **~65-70%** | **0** |

**`xfer0` for both teams for the entire game** — the paint-transfer mechanic is
never invoked once, by either lineage member.

So the treadmill is not attrition from fighting. My units run their 200-paint tank
dry in ~85 rounds and die of exhaustion, and the bot's only response is to pay 200
tower paint **and 250 chips** to build a replacement that starts the same clock.
Iteration 6's premise is now measured rather than argued.

**Reachability note for iteration 6** (algorithm step 3, checked before writing
code): opportunistic refill alone is likely near-dead, because a soldier with no
ruin to work *wanders* and never approaches a tower deliberately. Vision is only
r²=20 (~4.5 tiles), so the unit must also remember a tower location. Iteration 6
is therefore seek-and-withdraw as **one** mechanism, not an opportunistic top-up.

### Iteration 5 mechanism check — dose 100, Racetrack vs alice_iter4 (pre-registered criterion 3)

Run as a single match while the sweep played. `alice_r100` (A) wins by
AREA_PAINTED. Per 250 rounds at r2000:

| | dose 100 | dose 0 (iter4) |
|---|---|---|
| spawns | +48 soldiers, +16 moppers | +11 soldiers, +91 moppers |
| **realized mopper share** | **25%** | **89%** |
| soldiers alive | 21-30 | 0-7 |
| paint actions | 113-210 | 3-47 |
| unpaint actions | 6-27 | 135-219 |
| coverage @r2000 | **493‰** | 479‰ |

**Criterion 3 PASS**: the realized mopper share lands at 25% — strictly between
the extremes (89% at dose 0, 0% at dose 200) and, notably, exactly the 25% the
spawn line always *claimed* to produce. Dose 100 does not change the policy; it
makes the written policy actually happen, by removing the price asymmetry.

Two things worth carrying forward:

1. **The erasure race is still lost, and the margin is thin.** Dose 100's coverage
   *peaks at 553‰ (r1250) and falls to 493‰*, while iter4 climbs 409→479‰ on the
   back of 135-219 unpaint actions per 250 rounds against dose 100's 6-27. The win
   is 493 vs 479 — 14‰. More soldiers paint more, but with only 5-8 moppers alive
   there is almost nothing contesting the opponent's paint. This is §2 again and
   it is the likely next target after refuelling: **purposeful moppers** (send them
   at enemy paint) rather than more of them.
2. **The treadmill is untouched.** Deaths are 62-67 per 250 rounds with 30-52
   starved, and `xfer0` all game. Iteration 5 changes *what* is spawned, not the
   fact that everything spawned starves. Iteration 6 (refuel) is unaffected by
   this iteration's outcome and stays the next target either way.

Watch criterion (4) reads: soldier share rose *and* coverage moved, so the spawn
mix was a real constraint — but starvation deaths did not fall, so it is not the
*only* one.

### Free play-symmetry check (no VM cost) — no side bias in the accepted build

The algorithm asks for periodic mirror-matching to catch fixed absolute-order
decisions that hand one side a compounding tempo edge. The full mirror
(`alice_mirror`) is still un-run, but iteration 4's 100-game run already answers
the cheap half of the question:

| | as side A | as side B |
|---|---|---|
| overall | 44/50 (88%) | 43/50 (86%) |
| vs alice_iter2 | 20/25 (80%) | 19/25 (76%) |
| vs alice_iter1 | 24/25 (96%) | 24/25 (96%) |

One game of difference on each split — nowhere near the noise floor for n=25.
Whatever else is wrong with this bot, **team identity is not correlated with its
result**, which is consistent with the two deliberate symmetry defences already
in the code (randomised tie-break order in `tryMove`, tower type chosen by ruin
coordinate parity rather than by treasury state at mark time).

This does **not** retire the mirror run: it cannot see a bias that is symmetric
between the two *lineage members* here, and 11 of 25 maps were split-by-side,
which is exactly where a per-map positional effect would hide. Still queued.

---

## Iteration 6 — soldiers refuel at towers instead of starving (prepared, verified, queued)

**Area**: unit sustain (new area; opened by the API sweep and the death-cause probe).

**Premise, measured**: 65-100% of unit deaths are paint starvation, and
`transferPaint` had been called **zero** times per game by either team across
this lineage's entire history. The bot's only way to deliver fresh paint to the
field is to respawn — 200 tower paint **plus 250 chips**, discarding a positioned
veteran, restarting the same ~85-round clock. A refill costs the same paint and
**no chips**.

**Change** (one mechanism, `src/alice_i6/`, built on the leading dose from
iteration 5): a soldier below `LOW_PAINT` walks to the last ally tower it has
seen and withdraws `min(capacity - paint, towerPaint)`. Seek and withdraw are
deliberately *not* split: vision is only r²=20, so a soldier that merely tops up
when it happens to stand beside a tower is dead code — with no ruin to work it
wanders and never approaches one on purpose. The withdrawal amount respects the
engine trap in `RULES.md` (over-asking clamps the credit but debits the tower in
full, silently burning its paint).

**Mechanistic verification — Racetrack, alice_i6 (A) vs alice_r100, WIN by
AREA_PAINTED.** Per 250 rounds at r2000:

| | alice_i6 | alice_r100 |
|---|---|---|
| **paint transfers** | **14-20** | **0** |
| starvation deaths | 28-35 | 29-45 |
| total deaths | 53-61 | 60-67 |
| coverage 1000→2000 | 489 → **502‰** | 486 → **473‰** |

Outcome class 1 (won, mechanism engaged). The mechanic fires for the first time
in this lineage, starvation deaths fall ~20-25%, and coverage trends up where the
baseline's trends down.

**But engagement is weak and that is the interesting part**: ~16 transfers per
~58 deaths means only about a quarter of soldiers ever refuel once. Two candidate
causes, and they have different fixes — (a) `LOW_PAINT = 60` triggers too late,
since cooldowns already scale up below 50% stash (=100 paint), so a soldier is
crippled long before it qualifies; (b) soldiers are simply too far from any tower
to make the trip. `LOW_PAINT` is therefore the natural dose, and the pre-registered
sweep is **60 / 100 / 140** with the zero arm being iteration 5's accepted build.

**Pre-registered** (to run when the VM frees):
1. **Accept gate** — H2H vs iteration 5's accepted snapshot > 50%, and >= 18/30
   at NMAPS=15 for the noise band.
2. **Mechanism** — `xfer` per 250 rounds must stay materially > 0 (it is 0 in every
   prior build), and the starvation share of deaths must fall.
3. **Dose-response** — with the zero arm at 0 transfers, a monotone rise through
   60→100→140 would say the trigger is simply too late; a peak at 60 would say
   distance-to-tower, not the threshold, is the binding constraint.
4. **Watch (not a gate)** — paint actions per 250 rounds. If refuelling merely
   trades painting turns for walking turns, coverage will not move and the real
   answer is to refuel *without* leaving the work site.

### Trace of iteration 5's one swept loss — starburst (accept condition 3)

Dose 100 lost starburst from **both** sides, the only swept loss in the run, so
per the diff-shape rule it is a real causal effect rather than churn and had to be
traced before accepting. Re-ran it (r100 as A, lost) and dumped. Per 250 rounds:

| | dose 100 | dose 0 (iter4) |
|---|---|---|
| paint actions | **110-151** | 62-84 |
| **unpaint actions** | 59-84 | **124-143** |
| moppers alive | 3-8 | 9-15 |
| coverage 1000→2000 | 463 → **443‰** (falling) | 508 → **539‰** (rising) |

**Dose 100 paints roughly twice as much and still loses the map**, because dose 0
erases roughly twice as much. This is not a new failure mode — it is precisely the
trade I flagged in the mechanism check, in its purest form: fewer moppers means
less contest, and on a map where erasure dominates, more painting cannot make up
for it. Coverage is a *contested stock* (LEARNINGS §2), and starburst is the map
that punishes forgetting it.

**Resolved, not ignored**: the regression has a specific mechanism, it is confined
to 1 of 15 maps, and the run-wide margin is far outside noise. It does not gate
the accept, and it names the next target precisely — **not more moppers (dose 0
already tested that and loses overall), but better ones.** Today a mopper wanders
and mops whatever enemy paint it randomly ends up adjacent to (sense radius r²≤2).
Making the 3-8 moppers I have seek enemy paint within vision (r²=20) attacks this
without giving back the soldier share that iteration 5 just bought.

Registered as the iteration 7 candidate: **purposeful moppers**, ahead of SRPs.

### Shared-pool instrumentation for iteration 6 — refills are drawn from the spawn budget

The algorithm requires instrumenting a contested pool in the *first* run of any
change that alters who draws on it. Iteration 6's refill and the tower's spawn
both draw on the same thing — **tower paint** — so I added `twPaint` (total paint
held across a team's towers) to the dumper before evaluating, and re-read the
verification game. Per 500 rounds:

| round | i6 twPaint | i6 +soldiers | i6 xfer | r100 twPaint | r100 +soldiers | r100 xfer |
|---|---|---|---|---|---|---|
| 500 | 553 | +54 | 30 | 745 | +55 | 0 |
| 1000 | 340 | +75 | 41 | 750 | +85 | 0 |
| 1500 | 221 | +83 | 35 | 650 | +98 | 0 |
| 2000 | **216** | +81 | 30 | **550** | +98 | 0 |

**Refilling is not additive — it substitutes for spawning.** i6 drains its tower
pool to ~40% of the baseline's and consequently spawns ~17% fewer soldiers
(+81 vs +98 per 500 rounds). It still wins (coverage 502 vs 473‰, starvation
deaths 68 vs 83), so the substitution is favourable at this dose — a refilled
veteran is worth more than the marginal recruit it displaces, which is exactly the
economic claim iteration 6 was built on, now measured rather than argued.

**This changes iteration 6's dose prediction.** I had pre-registered that a
monotone rise through 60→100→140 would mean "the trigger fires too late". That
reading is now wrong: a higher `LOW_PAINT` refills more often, drains the pool
harder, and suppresses spawning further. Both teams sit near **216-550 paint
across seven towers whose capacity is 7,000** — the pool is nearly dry in every
game, which independently re-confirms LEARNINGS §1 (paint, not chips, binds).

**Revised pre-registration for the dose sweep**: expect an interior optimum, and
add a gate — the winning dose must not reduce soldier spawns by more than it
reduces starvation deaths. `twPaint` at r2000 is now a reported variable for every
arm, not a watch.

### Structural observation — every unit navigates blind, and it is the same bug three times

Noticed while drafting iteration 7. The algorithm says to hunt for radius
asymmetries; this bot contains one in every unit, and it is self-inflicted rather
than an engine quirk:

| unit | vision r² | radius it picks targets in | navigates by |
|---|---|---|---|
| soldier (no ruin in sight) | 20 | 9 (action radius) | **random wander** |
| mopper | 20 | **2** (mop radius) | **random wander** |
| splasher | 20 | 4 | **random wander** |

Every unit can *see* roughly twice as far as it can *act*, and none of them uses
the difference. They act on whatever happens to fall inside the small circle and
otherwise walk in a random direction for 5-12 steps. The mopper is the worst case
by an order of magnitude — it selects targets from the 8 adjacent tiles while
seeing ~60.

So "purposeful moppers" (iteration 7) is really the first instance of a general
fix: **navigate toward the nearest thing you could act on**. The soldier version —
walk toward visible unpainted ground instead of wandering — is the same change and
becomes the iteration 8 candidate. Keeping them as separate iterations is
deliberate: they touch different units and must not be bundled, and the mopper
version has a specific map (starburst) that predicts its effect.

Ordering rationale: iteration 6 (refuel) is already verified and queued;
iteration 7 (moppers) has a named failing map; iteration 8 (soldiers) is the
largest population but has no specific failing map yet, so it is the weakest
pre-registration of the three and goes last.

### Non-blocking trace during the sweep — Mirage, and the death spiral iteration 5 actually fixes

Traced iteration 4's most distinctive loss from run `20260906-203042`: Mirage was
the only loss that ended **early** (r1569, `MAJORITY_PAINTED`) rather than on the
round-2000 paint tiebreak, so it was the one game where the bot was not merely
out-scored but destroyed. With the new `twPaint` instrument the cause is
unmistakable, and it is an *absolute* degeneracy — "the bot stalls at round N",
no opponent comparison needed:

| round | iter4 twPaint | iter4 towers | iter4 soldiers | iter4 +sold/+mop | iter4 coverage |
|---|---|---|---|---|---|
| 200 | **0** | 2 | 0 | +1 / +19 | 132‰ |
| 400 | 100 | 2 | 0 | +0 / +19 | 89‰ |
| 800 | **0** | 2 | 0 | +0 / +20 | 24‰ |
| 1400 | 100 | 2 | 1 | +1 / +18 | **19‰** |

**The bot is dead at round 200 and the game runs another 1,369 rounds.** Tower
paint hits zero, so the only unit it can ever afford again is the 100-paint
mopper; moppers cannot paint; so it never completes another tower pattern; so its
paint income never grows; so tower paint stays at zero. It spawned **1 soldier and
19 moppers** in the first 200 rounds and essentially no soldiers ever again, sat
at its 2 starting towers for the whole game, and watched coverage collapse
132 → 15‰ while the opponent went to 16 towers and 664‰.

This is the mopper price asymmetry at its most extreme: not a skewed mix, an
**absorbing state**.

**Iteration 5 breaks it.** Re-ran the same map, same side, with dose 50:

| | iter4 (lost, r1569) | alice_r50 (WON, r2000) |
|---|---|---|
| tower paint | 0-100 all game | **1915 → 1215**, never collapses |
| towers | 2 | 11-12 |
| coverage | 132 → **15‰** | 493 → **541‰** |
| result | loses MAJORITY_PAINTED | **wins** AREA_PAINTED |

And the spiral is now inflicted on the *baseline*: `alice_iter2` sits at twPaint
90-325 with **zero soldiers alive** from r800 and coverage falling 432 → 280‰.

This is the strongest causal evidence in the iteration: the reserve keeps tower
paint off zero → soldiers stay fundable → tower patterns keep completing → paint
income keeps growing. It also retro-explains iteration 4's loss list, where the
recurring shape was games that stalled rather than games that were out-fought.

### Generality check — the stall signature is in every traced loss

Algorithm step 3 asks for the hypothesis to be verified on at least one other
losing game. Checked two more of iteration 4's losses with `twPaint`:

| game | losing side twPaint @r2000 | its spawns/500r | winning side twPaint | its spawns/500r |
|---|---|---|---|---|
| Mirage (lost r1569) | **0-100 from r200** | +1 sold / +18 mop | 1520→910 | — |
| box | 290 → 290 → **90** | +15 sold / +71 mop | 2015 → **1140** | +53 sold / +39 mop |
| HungerGames | 5330 → 880 → **480** | **+7 sold / +210 mop** | 5330 → **1000** | +50 sold / +175 mop |

The signature is identical in all three: **the side that loses is the side whose
tower paint drains toward zero, and its spawn mix collapses toward pure moppers as
it does.** HungerGames is the clearest — at r2000 the losing side is spawning 97%
moppers (7 soldiers to 210) while the winner holds 22%.

**This also explains the 11 split-by-side maps in iteration 4's run**, which I had
filed as ordinary positional noise. In those games *both* sides run the same buggy
spawn rule, so the map is a race into the same absorbing state: whichever side's
tower paint drains first falls in, and small positional differences decide which.
That is why the outcome flips with side while neither side sweeps — it is one
mechanism, not fifteen coin flips.

So iteration 5 is not a marginal tuning of an army ratio. It removes a positive
feedback loop that this lineage has been losing games to since iteration 0, and
the loop is visible in every loss I have looked at.

---

## Iteration 5 — RESULT: ACCEPTED (snapshot `src/alice_iter5/`)

Run `20260906-213750`, 60 games, 15-map random sample, both sides, complete (no
`!! INCOMPLETE`). `BOT` was the **zero arm** (`alice_iter4`), so its win rate
inverts to give each dose's head-to-head against the accepted snapshot.

| dose | meaning | H2H vs alice_iter4 | gate (>=18/30) |
|---|---|---|---|
| 0 | current build | 50% by definition | — |
| **50** | mopper only if tower paint >= 150 | **23/30 (76.7%)** | PASS |
| **100** | mopper only if tower paint >= 200 | **21/30 (70.0%)** | PASS |
| 200 | mopper only if tower paint >= 300 | refuted on trace (moppers → 0) | — |

**Dose-response shape (criterion 2): PASS.** Concave with an interior optimum,
exactly as pre-registered — 50% at dose 0, ~70-77% across 50-100, collapsing by
200. A monotone curve would have falsified the reading; it did not appear.

**Criterion 1 PASS** (both doses clear 18/30). **Criterion 3 PASS** (realized
mopper share 25%, strictly interior). **Criterion 4** (watch): the soldier share
rose *and* coverage moved, so spawn mix was a real constraint — but starvation
deaths did not fall, so it is not the only one, which is what iteration 6 targets.

### Which dose — chosen against the raw score, on purpose

Dose 50 scored two games higher. I took **dose 100** anyway:

- **The difference is under the noise floor.** On the 27 (map,side) cells both
  arms actually played, they disagree on **3 cells** — a one-cell net difference.
  Doctrine #6 says distrust any delta under the binomial floor "regardless of how
  good the story is", and 2/30 is far under it.
- **Dose 100 is not a constant, it is a game rule.** Skipping a mopper below 200
  tower paint is exactly *"only build a mopper if a soldier was affordable too"* —
  `UnitType.SOLDIER.paintCost`. Dose 50's 150 is an arbitrary number that happened
  to win one extra cell on this particular 15-map sample. The algorithm's stated
  design preference is that **self-calibrating thresholds beat fixed constants**,
  and picking the arbitrary constant *because* it won by one cell on the sample it
  was measured on is the definition of fitting the instrument.

So the accepted code carries no magic number: the gate reads
`rc.getPaint() < UnitType.SOLDIER.paintCost`. Verified behaviourally identical to
the measured `alice_r100` arm by re-running Racetrack and reproducing its result.

### Diff shape
Dose 100 took 1 swept loss (**starburst**, traced above: it paints ~2x as much and
still loses because it erases half as much). Understood, confined to 1 of 15 maps,
and it names iteration 7's target. Not an unresolved regression.

### Why this iteration mattered more than its win rate suggests
The mopper price asymmetry is not a skewed ratio, it is an **absorbing state**:
tower paint → 0 ⇒ only the 100-paint mopper is affordable ⇒ moppers complete no
tower patterns ⇒ paint income never recovers. Traced in all three losses examined
(Mirage: dead at r200, coverage 132→15‰; box; HungerGames at 97% moppers), and it
re-explains iteration 4's 11 split-by-side maps as a *race into one absorbing
state* rather than positional noise. Archived replay
`replays/iter05_alice_iter4_Mirage_B_WIN.bc25` is the accepted build winning the
exact map and side where iteration 4 was eliminated at r1569.

### Functional-area map
- economy/chip conversion — iteration 4 ACCEPTED
- spawn economics — **iteration 5 ACCEPTED**
- unit sustain (refuel) — iteration 6, built and verified, evaluating next
- mopper targeting — iteration 7, named by the starburst trace
- soldier targeting — iteration 8 (same radius-asymmetry fix as 7)
- population control / anti-clumping — withdrawn (instrument artifact)

---

## Iteration 6 — soldiers refuel at towers (RUNNING, run `20260906-220906`)

Arms rebuilt from the accepted `alice_iter5` so the only difference is the refuel
mechanism. `BOT = alice_iter5` is a **true zero arm** — it makes literally zero
transfers, verified in every trace — so its win rate inverts to each dose's
head-to-head against the accepted snapshot, the same design that made iteration
5's sweep exact.

`OPPONENTS = alice_i6_60 alice_i6_120`, NMAPS=15, both sides = 60 games. Two
nonzero doses plus the zero arm gives the three points doctrine #2 requires; the
gate opponent (60, the dose the pool instrument predicts) is listed first so a
deadline truncation costs the other arm rather than the gate.

**Dose set revised from the pre-registered 60/100/140 to 60/120**, for a stated
reason rather than convenience: the `twPaint` instrument showed refills are drawn
from the *same pool that funds spawning*, so a higher `LOW_PAINT` refills more
often, drains harder and suppresses spawning further. My original reading — that a
monotone rise would mean "the trigger fires too late" — was wrong, and 140 is on
the side of the curve the instrument now predicts is bad. Two doses at 30 games
each also beats three at 20 for resolution.

**Pre-registered**:
1. **Accept gate** — a dose beats `alice_iter5` H2H > 50%, and >= 18/30 (60%).
2. **Mechanism** — `xfer` per 250 rounds materially > 0 (it is exactly 0 in every
   prior build), and the starvation share of deaths falls.
3. **Shared pool** — report `twPaint` at r2000 for the winning arm. A dose that
   wins while draining the pool to near zero is buying now and paying later, and
   should be treated as a near miss rather than an accept.
4. **Net-substitution gate** (new, from the pool finding) — the winning dose must
   not cut soldier spawns by more than it cuts starvation deaths. Refilling is a
   *substitute* for spawning, not an addition, so the trade has to be favourable
   on its own terms and not just on the scoreboard.
5. **Watch** — paint actions per 250 rounds; if refuelling merely trades painting
   turns for walking turns, coverage will not move and the answer is to refuel
   without leaving the work site.

---

## Iteration 7 — purposeful moppers (built and verified while iteration 6 evaluates)

**Area**: mopper targeting. Named by iteration 5's only swept loss.

**The defect is a self-inflicted radius asymmetry.** A mopper selects targets
within r²≤2 — the 8 adjacent tiles — while its vision is r²=20, about 60 tiles.
It has been blind to ~90% of what it can see, and when nothing is adjacent it
*wanders at random*.

**Change** (one mechanism, `src/alice_i7/`, built on `alice_iter5`): after mopping,
walk toward the nearest enemy-painted tile anywhere in vision; wander only when
none is visible; hold position when already in range.

**Targeted verification — starburst, the exact map iteration 5 lost from both
sides.** `alice_i7` (A) wins by AREA_PAINTED:

| per 500 rounds | alice_i7 | alice_iter5 |
|---|---|---|
| unpaint actions | 187-381 | 61-163 |
| moppers alive | 4-6 | 1-5 |
| **unpaints per mopper** (r1000) | **~76** | **~23** |
| coverage 500→2000 | 531 → **654‰** | 451 → **319‰** |

**Criterion 2 (the one that matters) passes**: productivity per mopper roughly
**triples**. This is deliberately measured per mopper alive rather than as a raw
count — raw unpaints scale with mopper population, and this change is meant to
raise productivity, not numbers. The mopper count is unchanged (4-6, same as the
baseline's 1-5); the same few units simply find work instead of wandering.

**Criterion 4 passes**: soldier count and coverage both *rose* (26 vs 9 soldiers,
654 vs 319‰), so the erasure capability was bought back without giving up the
soldier share iteration 5 gained — which was the whole design constraint.

**Caveat, stated before it can flatter me**: starburst was chosen *because* it is
the map where erasure matters most, so this is the friendliest possible sample.
Generality checks on Racetrack, Mirage and DefaultLarge are running. The accept
gate remains a full sweep against the then-accepted snapshot, not these matches.

### Iteration 6 interim read, and the arithmetic I should have done first

At 11/60 the zero arm is holding `alice_i6_60` to ~50%. Rather than wait to be
told, here is the accounting I should have done *before* building it:

| | respawn | refill |
|---|---|---|
| tower paint | 200 | up to 200 |
| chips | 250 | **0** |
| unit position | starts at the tower | keeps a positioned veteran |
| turns lost | none (tower acts anyway) | **the walk back, plus the transfer turn** |

**The paint cost is identical.** Tower paint is the binding resource, and a refill
consumes exactly as much of it as a fresh soldier does. The refill's only genuine
savings is **250 chips — which iteration 4 already established are not binding**
(the treasury sits on $100k+ in most games). So the mechanism trades a real cost
(turns spent walking back, plus one action spent transferring) against a saving in
the one resource I provably have too much of, and keeps a veteran's position.

That predicts near-neutrality, which is what the sweep is showing, and it matches
the `twPaint` finding exactly: refilling *substitutes* for spawning rather than
adding to it. The substitution is roughly break-even.

**Pre-registered near-miss refinement** (declared now, before the result, so it
cannot be retrofitted): if iteration 6 lands within `NearMissMargin`, the one
refinement is **refuel only when the tower is already close** — cap the trip at a
few tiles and otherwise keep working. That keeps the case where the walk is nearly
free (the soldier is working a ruin that has become a tower) and drops the case
where the walk costs more than the recruit it replaces. If it lands clearly below,
this is a **reject**, and the honest lesson is that saving a non-binding resource
buys nothing — which is LEARNINGS §1 turned into a prediction rather than a
post-hoc excuse.

Either way iteration 7 is unaffected: it is built on `alice_iter5` and touches a
different unit.

### Risk noted in iteration 7 before evaluating it — the bot has no pathfinding at all

`tryMove` is a three-way greedy step: try the direction, else its two rotations,
else give up. There is **no bug-nav, no BFS, nothing** — and until now it barely
mattered, because units that failed to move were *wandering* anyway and picked a
fresh random direction next turn.

Iterations 7 and 8 change that. A unit that commits to a distant target and is
blocked by a wall will re-target the same tile every turn and can stall against
concave terrain, where the old random wander would have escaped. In the starburst
verification the moppers were plainly productive (187-381 unpaints per 500 rounds),
so it is not catastrophic there, but starburst is open terrain. **Maze-like maps
are the place this would show**, and the gauntlet's random sample includes them.

Pre-registered as the diagnostic if iteration 7 underperforms: check whether its
losses concentrate on maps with high wall density, and whether moppers show
repeated failed moves. That is a specific, falsifiable prediction rather than a
general worry.

**Standing structural gap, logged for the ledger**: hybrid bug-navigation is one of
the perennial mechanics the cross-year research names, and this lineage has none.
It is a candidate in its own right, and it becomes a *prerequisite* rather than an
option the moment any target-seeking iteration is accepted. Note the bytecode
budget is not an obstacle — measured 1638/17500 (9%) peak for soldiers, so BFS is
affordable.

### Iteration 7 generality — 8/8, all four maps swept from both sides

Single matches vs the accepted `alice_iter5`, each map played from both sides:

| map | i7 as A | i7 as B |
|---|---|---|
| starburst (iteration 5's swept loss) | **win** | **win** |
| Racetrack | **win** | **win** |
| Mirage | **win** | **win** |
| DefaultLarge | **win** | **win** |

Four **swept** maps — won from both sides, so the result is immune to spawn-side
advantage, which is the property that made me distrust the single-side reads
earlier. Under a null of 50% per game, 8/8 is p≈0.004; treating each *map* as the
unit (a sweep is the informative event) it is 4/4 sweeps, p≈0.0625.

That is a prior, **not an accept**. These are four maps I chose, and starburst was
chosen precisely because it favours the mechanism. The gate remains a full sweep
on a fresh random sample against the then-accepted snapshot, and the recorded risk
(no pathfinding; units may stall on wall-heavy maps) is untested by any of these
four, which are open terrain. The random sample will include maze-like maps and is
the honest test.

### Wall-density instrument, and the quantified blind spot in iteration 7's prior

Added map wall density and ruin count to the dumper's `MatchHeader` line, because
both decide whether a target-seeking unit can be trapped and how far tower
expansion can go, and I was about to reason about "open vs maze-like" maps without
a number for it.

My four generality maps, measured:

| map | walls | ruins |
|---|---|---|
| DefaultLarge | 24/1500 (**1.6%**) | 24 |
| starburst | 56/900 (**6.2%**) | 12 |
| Mirage | 120/1600 (**7.5%**) | 22 |
| Racetrack | 63/625 (**10.1%**) | 14 |

The spec allows walls up to **20%** of a map. Every map in my 8/8 sweep sits in
the bottom half of that range, and the most obstructed is only 10.1%. So the
caveat I recorded by intuition is now a measured fact: **iteration 7's prior is
drawn entirely from open terrain and does not test the pathfinding risk at all.**

This is the representativeness rule (doctrine #4) applied to my own favourable
evidence rather than to an opponent's: an instrument that cannot pose the threat
cannot clear the feature of it. The random 15-map sample in the accept run will
include wall-heavy maps; if iteration 7 has a terrain problem, that is where it
appears, and the wall-density figure now lets me check the losses against it
directly instead of guessing.

---

## Iteration 6 — RESULT: REJECTED, and the prediction held

Run `20260906-220906`. Gate arm complete; second arm still playing at the time of
writing (numbers below marked interim are updated in the next entry).

| dose | H2H vs `alice_iter5` | gate (>=18/30) |
|---|---|---|
| 0 (no refuel) | 50% by definition | — |
| `LOW_PAINT` 60 | **13/30 (43.3%)** | **FAIL** |
| `LOW_PAINT` 120 | **0/6 (0%)** *(interim)* | FAIL, decisively |

Diff shape: 4 swept-wins against **5 swept-losses** and 6 splits — not a near
miss with a regression, just no directional advantage at all, tilted slightly
negative.

**The dose-response is monotone *decreasing*.** More refuelling is strictly worse,
and the 120 arm is catastrophic. That is the shape I predicted *after* the
`twPaint` instrument and *before* the sweep, and it is the opposite of the shape I
pre-registered before instrumenting the pool — which is exactly why the pool had
to be instrumented.

### Why it fails — the arithmetic, confirmed

A refill and a respawn cost the **same 200 tower paint**, and tower paint is the
binding resource. The refill's only genuine saving is **250 chips**, which
iteration 4 already proved are not binding (the treasury sits on $100k+). Against
that it pays the walk back plus a transfer turn, and — per `twPaint` — it drains
the pool that funds spawning (216 vs 550 at r2000, 17% fewer soldiers).

So iteration 6 spends the scarce resource to save the abundant one. A refilled
veteran is *not* worth more than the recruit it displaces; it is worth slightly
less, because the recruit arrives already at the front and the veteran spends
turns walking.

**The near-miss refinement is not triggered** (43.3% is outside `NearMissMargin`
of the 50% bar, let alone the 60% `WinPct`), so per the pre-registration this is a
full reject. `src/alice` was never touched — iteration 6 lived only in probe
packages — so there is nothing to revert.

### What the reject buys
1. **A general rule, stated as a rule**: *saving a non-binding resource buys
   nothing.* The mechanism engaged perfectly (first transfers in lineage history,
   starvation deaths down 20-25%) and still lost. This is the "metrics that improve
   without converting to wins" pattern the algorithm warns about, caught in the act.
2. **Starvation is not a problem to be solved by refilling.** 65-100% of deaths
   are starvation, but the fix is not to top units up — it is that a starved unit
   has *already delivered its 200 paint*, which is all it was ever going to
   deliver. Death at 0 paint is the unit finishing its job, not failing at it.
   This reframes the whole "treadmill" reading: the treadmill is the intended
   throughput mechanism, not a defect.
3. It kills the obvious follow-ups too (mopper refills, tower-to-unit pushes) for
   the same arithmetic, without spending a run on any of them.

### Closed-directions ledger
| direction | closed by | can re-open if |
|---|---|---|
| Refuel units from towers (`transferPaint` withdraw) | iteration 6: 13/30 at dose 60, 0/6 at dose 120, monotone decreasing; `twPaint` shows refills substitute for spawning | **paint becomes non-binding** (large SRP income, or many L3 paint towers), so the refill stops competing with spawning. Not before. |
| "Reduce starvation deaths" as a goal in itself | same | it is re-framed: a unit at 0 paint has delivered its full payload; dying is not the failure |

### Correction and an open instrument question (raised before it can mislead iteration 8)

Two things about the reject entry above need tightening.

**1. "A starved unit has delivered its full payload" is too strong.** A soldier's
200 paint is split between *painting* (5/action) and *upkeep* (−1/turn on neutral,
−2 on enemy, 0 on ally paint, plus −1 per adjacent ally). It is upkeep, not
painting, that empties most tanks. The defensible version of the claim is narrower
and still supports the reject: **topping the tank up does not change the
conversion rate of tower paint into painted tiles**, because the refill draws on
the same pool a new soldier would have used. The measurement (monotone-decreasing
dose-response) stands on its own regardless.

**2. `p` (PaintAction) may not be counting soldier tile-painting at all.** Working
the arithmetic: ~175 paint actions per 250 rounds across ~27 living soldiers is
~2.8% of soldier-turns, i.e. roughly **3 paint actions per soldier lifetime**. That
is implausibly low — a soldier can move and act in the same turn, so it should
manage tens. Meanwhile `a` (AttackAction) runs in the hundreds to thousands.

The likely explanation is that the engine records a soldier's tile-painting as
**AttackAction**, not PaintAction, and my `p` counter has been measuring something
else all along. This is *exactly* the failure already in LEARNINGS §4 — "a replay
counter means nothing until you have found its call site" — which I wrote about
`MopAction` and then walked into again.

**What this does and does not affect.** Every conclusion I have accepted rests on
**coverage** (`cov`, the engine's own painted-area figure) and on win/loss, not on
`p`: iterations 4, 5, 6 and 7's evidence are unaffected. What it *would* corrupt is
iteration 8's pre-registered mechanism gate, which I wrote as "paint actions per
soldier alive must rise". **Do not evaluate iteration 8 until the emitter of
PaintAction vs AttackAction is confirmed by reading the engine** — the same
one-minute check that settled the clumping-tax question. Logged as a blocking
prerequisite rather than a note.

### Iteration 7 — the predicted terrain failure is real (maze, 19.8% walls)

I recorded the pathfinding-stall risk before testing it, pre-registered the
diagnostic ("do its losses concentrate on high-wall-density maps"), then went
looking for the most obstructed map available rather than waiting for the random
sample to find it. Result:

| map | walls | ruins | outcome |
|---|---|---|---|
| **maze** | **712/3600 (19.8%)** | 32 | **alice_i7 LOSES** to alice_iter5 |
| starburst / Racetrack / Mirage / DefaultLarge | 1.6-10.1% | 12-24 | i7 sweeps all four, both sides |

19.8% is essentially the spec ceiling (walls ≤ 20% of a map). So the picture is
clean and it is the one I predicted: **iteration 7 is strong in open terrain and
fails where terrain is genuinely obstructive**, because a mopper that commits to a
distant target and is blocked re-targets the same tile every turn, where the old
random wander would have escaped.

This is the value of writing the risk down *before* the evidence: 8/8 on
self-chosen open maps would otherwise have read as an unqualified success, and
doctrine #4's representativeness rule applied to my own favourable evidence is
what sent me to look for the counter-case.

**Pre-registered refinement for iteration 7** (declared now, before its sweep):
if it clears the gate overall but its losses concentrate on high-wall maps, the
single refinement is a **stall guard, not a rewrite** — if the greedy step toward
the target fails to move the unit, fall back to `wander` for that turn instead of
re-targeting. That restores the escape behaviour the old code had for free, stays
inside the same mechanism, and does not bundle bug-nav in. Full hybrid bug-nav
(drafted, `bugnav-draft.java`) stays a separate iteration, and the maze result is
now its motivating evidence rather than a hypothetical.

### Correction to the entry above — wall density alone does not explain the maze loss

Second wall-heavy map came back and it does not fit the story I just wrote:

| map | size | walls | ruins | outcome |
|---|---|---|---|---|
| maze | **60x60** (3600) | 19.8% | 32 | **i7 loses** |
| yearofthesnake | 45x45 (2025) | **18.4%** | 20 | **i7 wins** |

At 18.4% walls — barely below maze's 19.8% — iteration 7 wins. So "iteration 7
fails where terrain is obstructive" was an over-read of a single game, and I am
striking it. Current standing is **9/10 across both sides, with one loss, on maze**.

What actually distinguishes maze is that it is also the **largest map in the pool**
(3600 tiles vs 2025). Longer distances mean a unit commits to a more distant target
and spends more turns travelling before re-evaluating, which is a *distance*
failure as much as a *terrain* one — and it would also predict trouble on
DefaultHuge. That is a hypothesis with one supporting game, not a finding.

**The refinement pre-registered above is unchanged and is robust to either
explanation**: falling back to `wander` when the greedy step fails to move costs
nothing and helps whether the unit is trapped by walls or merely committed too far.
The diagnostic for the sweep is now two-dimensional — check losses against both
wall density *and* map area, which the dumper now prints for free.

Noting the process point: I wrote a clean causal story off one game and the very
next game contradicted it. The map-property instrument is what caught it, minutes
after I built it.

### Instrument question RESOLVED — `p` is correct, and the arithmetic points somewhere better

Read the emitter rather than guessing. `GameMaker$MatchMaker` exposes:

```
addPaintAction(MapLocation, boolean)   <- tile painting  (takes a LOCATION)
addAttackAction(int)                   <- attacking a robot/tower (takes an ID)
```

So `PaintAction` **is** soldier tile-painting and my `p` counter was right all
along; `a` counts attacks on units/towers, which is why towers inflate it. The
blocking prerequisite on iteration 8 is **cleared**. (Cost: one command. This is
the third time this session that reading the engine settled in a minute what I was
about to reason about for an hour.)

**But the arithmetic that raised the question is still true, and it is the real
finding.** On Racetrack, alice_i7 per 500 rounds at r2000: 147 paint actions, 94
deaths, 26 soldiers alive ⇒ **~1.6 paint actions per soldier over its entire
life**. Cross-checked against the engine's own coverage figure: 654‰ of 900 tiles
≈ 585 tiles, against ~590 paint actions across the game. The two agree, so the
number is real.

**A soldier spends ~8 of its 200 paint on painting. The other ~192 goes to
upkeep.** That is a ~4% conversion rate of the binding resource into the win
condition.

**And upkeep is almost entirely self-inflicted**, per the engine's own table:
neutral tile −1/turn, enemy tile −2, **ally tile 0**, plus −1 per adjacent ally.
A soldier standing on its own paint with no ally adjacent pays **nothing and could
live indefinitely**. What drains it is *moving*: the bot's soldiers wander, so
every turn they step onto unpainted ground and pay −1 for the privilege.

### Iteration 8, rewritten — stand still and paint, don't wander and pay

My drafted iteration 8 ("seek unpainted ground in vision") would have made soldiers
move **more**, and on this arithmetic that means paying more upkeep to reach tiles
they could not afford to paint anyway. It is withdrawn before costing a run — the
same escape the corrected death instrument gave the anti-clumping draft.

The replacement is the opposite change, and it is the algorithm's named winner's
profile (*capability preserved at zero marginal cost*): **after painting its own
tile, a soldier should not move at all while an empty paintable tile remains within
action radius (r²≤9, ~28 tiles).** Painting from a standstill on ally paint costs
0 upkeep, so the soldier's whole 200 goes into tiles instead of into existing.

Pre-registered when it runs:
1. Gate: H2H vs the then-accepted snapshot > 50%, >= 18/30 at NMAPS=15.
2. Mechanism: **paint actions per soldier lifetime** (`p` ÷ deaths) must rise
   materially from ~1.6 — this is now a trustworthy counter.
3. Watch: coverage, and whether soldiers stop expanding the frontier and merely
   thicken a small painted blob. If coverage stalls, the standstill rule needs a
   "move on when your neighbourhood is finished" clause, which is exactly the
   `bd > 9` fallback the draft already contains.

## Iteration 8 — REJECTED ON THE TRACE, and it is the textbook "survival bought with inactivity"

Racetrack, alice_i8 (A) vs alice_iter5. **Lost**, 415‰ vs 560‰. Per 500 rounds at
r2000:

| | alice_i8 (stand still) | alice_iter5 |
|---|---|---|
| deaths | **83** | 173 |
| starvation deaths | **30** | 101 |
| paint actions per soldier lifetime | **0.48** | 0.31 |
| soldiers alive | 15 | **29** |
| **towers** | **6** | **8** |
| coverage @r2000 | **415‰** | **560‰** |

**Every mechanistic prediction came true.** Standing on ally paint does eliminate
the upkeep drain: deaths fell by 52%, starvation deaths by 70%, and paint per
soldier lifetime rose 55%. The units lived much longer and converted more of their
tank into tiles, exactly as designed — **and the bot lost by 145‰.**

TRAINING_ALGORITHM.md names this failure by name in "When the loop stalls":
*"survival bought with inactivity (halving the death rate cost 18 peer games —
units die doing the thing that wins)"*. I halved the death rate and it cost the
game. I did not recognise the shape while designing it, only on reading the trace.

### Why it loses — movement is not waste, it is the economy

The causal chain is visible in one column: **towers 6 vs 8**. A soldier standing
on its own paint never explores, so it never finds a fresh ruin, so no new tower
pattern is completed, so paint income never grows, so fewer soldiers can be
spawned (15 vs 29). Coverage follows the tower count, not the survival rate.

So the −1/turn upkeep I identified as "self-inflicted waste" is not waste at all:
**it is the price of exploration, and exploration is what buys tower income.** The
~4% conversion of soldier paint into painted tiles is real, but the other 96% is
not being thrown away — it is being spent on finding ruins, which is worth more
than the tiles it would have painted. This inverts the framing of the previous
entry, which I had already written before the trace existed.

**Rejected on the trace without spending a gauntlet**, the same way dose 200 was:
the mechanism engaged unambiguously, the outcome is clearly negative, and the
failure mode is a documented pattern rather than an unexplained loss. `src/alice`
was never touched.

### Closed-directions ledger
| direction | closed by | can re-open if |
|---|---|---|
| Soldiers stand still to avoid upkeep | iteration 8: towers 6 vs 8, coverage 415 vs 560‰ despite deaths −52% and starvation −70% | tower expansion is decoupled from soldier wandering — e.g. ruins are located by **communication** (unused mechanic) rather than by each soldier stumbling on them. Then standing still would cost nothing. **This is the specific reason the comms mechanic is now interesting.** |
| Soldiers seek unpainted ground (original iteration 8 draft) | withdrawn earlier by the upkeep arithmetic; now doubly so — it would move soldiers toward *tiles* rather than *ruins*, and the trace says ruins are what matter | — |

### Iteration 6 — final numbers (run `20260906-220906` complete, 60/60)

| dose | H2H vs `alice_iter5` |
|---|---|
| 0 (no refuel) | 50% by definition |
| `LOW_PAINT` 60 | **13/30 (43.3%)** |
| `LOW_PAINT` 120 | **4/30 (13.3%)** |

Monotone decreasing and steeply so — the interim reading holds and the reject is
decisive. Refuelling is not neutral, it is actively harmful, and more of it is much
more harmful. The `twPaint` substitution account explains the slope: every unit of
paint spent topping up a veteran is a unit not spent on a recruit, and the recruit
is worth more.

---

## Iteration 7 evaluation LAUNCHED — run `20260906-222958`

`BOT=alice_iter5` (zero arm) vs `OPPONENTS="alice_i7 alice_iter1 alice_iter0"`,
NMAPS=12, both sides = **72 games**. One run delivers two things that both want
`alice_iter5` as BOT on a single shared map sample:

1. **Iteration 7's accept gate** — `alice_i7`, listed first so a truncation costs
   the roster rather than the gate.
2. **The overdue fixed-roster point** for `alice_iter5` against `alice_iter0` and
   `alice_iter1` — the lineage's only absolute-strength instrument, last measured
   at iteration 4 and then only as a hollow backfilled point.

Gate at 24 games per opponent: **>= 16/24** (~92% one-sided), per the noise bands
in LEARNINGS §5.

Diagnostics to run on the result, both already pre-registered and now cheap because
the dumper prints map geometry: check iteration 7's losses against **wall density**
*and* **map area**, since maze (60x60, 19.8% walls) is its one known loss while
yearofthesnake (45x45, 18.4%) is a win — so area, not just terrain, is live as an
explanation.

---

## Strategic synthesis — tower count is the master variable, and ruin discovery is what limits it

Pulling four iterations' traces together, one column keeps deciding games:

| trace | winner towers | loser towers | winner cov | loser cov |
|---|---|---|---|---|
| Mirage (iter4 loss) | 16 | **2** | 664‰ | 15‰ |
| Racetrack (iter5 win) | 8 | 6 | 555‰ | 283‰ |
| Racetrack (iter8 loss) | 8 | **6** | 560‰ | 415‰ |
| starburst (iter7 win) | 6 | 6 | 654‰ | 319‰ |

Every accepted iteration so far has worked by protecting or raising tower count
(iteration 4 upgraded them, iteration 5 kept them fundable), and iteration 8 lost
purely by suppressing it. **Towers produce the binding resource; everything else
is downstream.**

**So what limits tower count?** A tower needs a ruin, and a soldier that paints its
5×5 pattern: 25 tiles at 5 paint = 125, plus 25 to mark = **~150 of a soldier's 200
paint**. Chips (1000 at completion) are not the constraint — they never are. The
constraint is **a soldier arriving at an unbuilt ruin with a full tank.**

And here is the defect: **`senseNearbyRuins` only sees within vision (r²=20).** The
bot's soldiers find ruins *by stumbling into them*. There is no memory: a soldier
that walks past a ruin it cannot yet afford, or that finishes one tower and turns
away, forgets every other ruin it has ever seen and reverts to random wander. On
Mirage there were **22 ruins** and the losing side held 2 towers all game.

This also explains iteration 8 exactly: standing still is only bad because
wandering is the *only* ruin-discovery mechanism the bot has.

### Iteration 9 candidate — remember ruins (ranked above SRPs and comms)

Keep a small per-robot list of unbuilt ruin locations seen, and when there is no
ruin in vision, head for the nearest remembered one instead of wandering. No
comms needed, no pathfinding needed beyond what iteration 7 already uses, and it
attacks the master variable directly.

Ranked **above** the two other unused mechanics for a specific reason: an SRP adds
+3/turn per tower and comms is merely enabling, whereas a single extra tower adds
**5-15 paint/turn plus a spawn point plus 500 starting paint**. The measured spread
between winners and losers is 2-16 towers, not a few points of income.

Pre-registered when it runs:
1. Gate: H2H vs the then-accepted snapshot, >= 16/24 at NMAPS=12.
2. Mechanism: **tower count at r2000 must rise** — the master variable itself, not
   a proxy.
3. Reachability check FIRST: count how often a soldier has no ruin in vision but a
   remembered unbuilt one. If that is rare the feature is dead code — and note the
   *guard* it nests inside is the existing `ruin != null` branch, which already
   excludes exactly the case it targets, so the check is mandatory rather than
   optional.

## Iteration 9 — DISCARDED on the reachability check, which I should have run first

Mirage, alice_i9 (A) vs alice_iter5. It *won* (493‰ vs 486‰) — and I am discarding
it anyway, because the pre-registered mechanism gate failed:

| | alice_i9 | alice_iter5 |
|---|---|---|
| **towers @r2000** (the gate) | **10** | **11** |
| coverage | 493‰ | 486‰ |

**Tower count did not rise. It fell by one.** The 7‰ win is not attributable to the
mechanism, and per step 4 that is "no evidence of engagement — discard, don't
evaluate further". Evaluating it would have bought a 72-game answer to a question
the trace already settled.

**Why it cannot work: ruins are saturated, not undiscovered.** Mirage has **22
ruins** and the two teams finished with **10 + 11 = 21 of them built**. There is
essentially never an unbuilt ruin left to remember. Racetrack is the same story —
14 ruins, 8 + 6 towers. The memory has nothing to find.

**This is exactly the reachability pre-check I pre-registered as mandatory and then
did not run.** I wrote "count how often a soldier has no ruin in vision but a
remembered unbuilt one — if that is rare the feature is dead code", and then built
the feature first. The check costs one dump of an existing replay; the map header
now prints the ruin count, and the round line prints tower counts, so the answer
(21 of 22) was already sitting in files I had.

### The synthesis above needs correcting

I wrote that "ruin **discovery** is what limits tower count". That is wrong. Ruin
**supply** limits it: a healthy bot builds out to the map's ruins and stops.
Tower-count *differences* between teams therefore come from **failing to build on
available ruins** — which is the iteration-5 absorbing state (no soldiers
affordable) or the iteration-8 failure (soldiers that never travel) — not from
failing to find them.

That is a sharper statement of the same master-variable finding, and it retires an
entire family of "help soldiers find ruins" ideas (memory, comms-shared ruin
locations, exploration heuristics) in one measurement. **Comms drops back down the
ranking**: iteration 8's ledger said comms would be interesting because it could
decouple ruin discovery from wandering, and that premise is now falsified.

### Closed-directions ledger
| direction | closed by | can re-open if |
|---|---|---|
| Remember/share unbuilt ruin locations | iteration 9: towers 10 vs 11, and 21 of Mirage's 22 ruins already built; nothing left to discover | a map class exists where ruins are *not* saturated by mid-game — check the ruin count against final tower totals before believing it |
| Comms for ruin sharing (iteration 8's proposed unlock) | same measurement | same condition |

---

## Iteration 10 — SRPs, and a three-step refinement each diagnosed from the trace

**Area**: economy (the last big unused mechanic). An active SRP adds **+3/turn to
every producing tower** for a one-off 200 chips — and chips are the resource this
bot provably cannot spend, especially once iteration 4's upgrade sink closes at
all-L3 and the treasury climbs past $150k.

All three arms measured on Mirage vs `alice_iter5`, one match each:

| arm | change | paint acts /500r | towers | coverage | result |
|---|---|---|---|---|---|
| **10a** | mark an SRP wherever a soldier stands | **1599** | 10 v 12 | **403 v 581‰** | lose badly |
| **10b** | + centres on a fixed lattice of period 5 | 151 | 9 v 11 | 476 v 507‰ | close loss |
| **10c** | + only once `getNumberTowers() >= 10` | 192 | 10 v 11 | **512 v 472‰** | **WIN** |

**10a's failure was diagnosable from one column.** Paint actions ran **8x** the
baseline while coverage *fell* — the signature of repainting the same tiles, not
covering new ground. Cause: every soldier marked a pattern centred on itself, so
neighbouring patterns overlapped and demanded conflicting primary/secondary colours
for shared tiles, and the soldiers repainted each other's work forever.

**10b fixed the thrash** (paint actions back to normal, coverage recovered 403 →
476‰) and exposed the *next* constraint underneath: 9 towers against 11. SRP work
was displacing tower building.

**10c applies the session's master-variable finding as a gate**: a tower is worth
5-15 paint/turn plus a spawn point plus 500 starting paint; an SRP is +3/turn per
tower. So towers come first and SRPs get the leftovers. Uses `getNumberTowers()`,
one of the API-sweep methods the bot had never called.

This is the near-miss refinement path working as designed — each step was chosen
from a specific trace column, not from a parameter search, and the sequence cost
three single matches rather than three gauntlets.

**Not accepted.** This is one map, and Mirage is ruin-rich (22), which flatters a
tower-saturation gate. Generality checks running; the gate remains a full sweep
against the then-accepted snapshot, queued behind iteration 7's run.

**Open question for the dose**: `SRP_MIN_TOWERS = 10` is a fixed constant, and this
session already established (iteration 5) that a self-calibrating threshold beats a
searched one. The principled form is "when no unbuilt ruin remains" — i.e. gate on
tower saturation rather than a magic 10 — and that is the first refinement to try
if the constant proves map-sensitive.

### Iteration 7 interim diff shape — the terrain worry resolves as positional

At 23/24 on the gate arm (20/23, 87%), the pre-registered loss diagnostic gives a
clean answer. All three losses so far, checked from both sides:

| map | i7 as A | i7 as B |
|---|---|---|
| maze | lost | **WON** |
| headphones | **WON** | lost |
| box | **WON** | lost |

**Zero swept losses.** Every loss is split-by-side, which by the diff-shape rule
(doctrine #7) is positional churn rather than a causal effect — there is no map
where iteration 7 loses from both sides.

**This settles the maze question against my own hypothesis, which is the useful
direction.** I had found iteration 7 losing maze in a single match, flagged a
pathfinding-stall mechanism, then struck the claim when yearofthesnake (18.4%
walls) came back a win. The gauntlet now plays maze from both sides and iteration 7
**wins one of them**. So the original maze loss was side-positional, and there is
no terrain law — the stall risk remains real in principle (the code genuinely has
no bug-nav) but it is not costing games at this wall density.

Consequence: **the pre-registered stall-guard refinement is not triggered.** I will
not spend it, because the evidence that motivated it evaporated. Hybrid bug-nav
stays drafted and unqueued, with its motivating evidence now retracted — logged so
a later session does not rediscover the draft and assume it was justified.

---

## Iteration 7 — RESULT: ACCEPTED (snapshot `src/alice_iter7/`)

Run `20260906-222958`, 12-map random sample, both sides. Gate arm complete.

| pre-registered criterion | result | verdict |
|---|---|---|
| H2H vs `alice_iter5` > 50%, >= 16/24 | **20/23 (87%)** | **PASS**, far clear |
| mechanism: unpaints **per mopper alive** must rise materially | ~76 vs ~23 per 500 rounds (**~3x**) | **PASS** |
| targeted: fix starburst, iteration 5's swept loss | starburst **swept** (both sides) | **PASS** |
| watch: soldier share / coverage must not fall | 26 vs 9 soldiers, 654 vs 319‰ | **PASS** |

Diff shape: **8 swept wins, 0 swept losses**, 4 split. No map is lost from both
sides, so accept condition 3 is met with nothing outstanding.

**The mechanism is one line of navigation.** A mopper picks targets within r²≤2 —
its 8 adjacent tiles — while seeing r²=20, about 60. It now walks toward the
nearest enemy paint in vision instead of wandering. Mopper *population* is
unchanged (4-6); the same few units simply stop being blind. This is the
"capability preserved at zero marginal cost" shape the algorithm names as the
recurring winner's profile — nothing extra is spent, an existing unit stops
wasting its own sensing.

**Why it mattered strategically**: iteration 5 bought a soldier-heavy army and
paid for it on maps where erasure decides the game (starburst: it painted ~2x the
baseline and still lost both sides). Iteration 7 buys the erasure back *without*
returning the soldier share, which was the design constraint. Coverage is a
contested stock, and this is the first iteration that contests it deliberately.

**Archived replay**: `replays/iter07_alice_iter5_starburst_A_WIN.bc25` — the
accepted build winning the exact map its predecessor lost from both sides.

### Functional-area map
- economy/chip conversion — iteration 4 ACCEPTED; iteration 10 (SRPs) queued
- spawn economics — iteration 5 ACCEPTED
- unit sustain (refuel) — iteration 6 REJECTED, closed
- mopper targeting — **iteration 7 ACCEPTED**
- soldier targeting/immobility — iteration 8 rejected on trace, closed
- ruin discovery — iteration 9 discarded on reachability, closed
- navigation (bug-nav) — drafted, unqueued, motivating evidence retracted

## Iteration 10 (SRPs) — rebuilt on iteration 7, pre-registered, queued

`src/alice_i10d` = accepted `alice_iter7` + the three-step SRP mechanism (lattice
centres, tower-saturation gate). Beats `alice_iter7` on Mirage; wider generality
checks running.

**Pre-registered before its sweep:**
1. **Gate** — H2H vs `alice_iter7` > 50%, **>= 16/24** at NMAPS=12.
2. **Mechanism** — `srp` (active resource patterns) must be materially > 0 for the
   candidate and 0 for the baseline, *and* paint actions per 500 rounds must stay in
   the normal band (~150-250). The second half is the important one: iteration 10a
   built SRPs successfully while running 1599 paint actions and losing by 178‰, so
   "SRPs exist" alone is not evidence the mechanism is working. **A count without a
   cost is not a measurement.**
3. **Shared pool / displacement** — tower count must not fall relative to the
   baseline. This is what killed 10b, and it is the master variable.
4. **Watch** — end-of-game chips. The whole premise is that SRPs reopen the chip
   sink that closes when towers max out at L3; if the treasury still climbs past
   $150k the mechanism is not doing the job it was justified by.

**Known weakness, declared now**: `SRP_MIN_TOWERS = 10` is a magic constant, and
this session already established that self-calibrating thresholds beat searched
ones (iteration 5). If the gate result is map-sensitive, the first refinement is
the principled form — gate on *ruin saturation* ("no unbuilt ruin in sight")
rather than an absolute tower count, which adapts to small maps automatically. I
am not searching over the constant.

---

# CURRENT STATE (resume here)

**Accepted lineage**: `alice_iter0` → `iter1` → `iter2` → `iter4` → `iter5` →
**`iter7`** (current). Gaps at 3 and 6 are rejected iterations. `src/alice` ==
`src/alice_iter7` and compiles; that is what plays in the tournament.

| iter | change | result |
|---|---|---|
| 4 | towers upgrade themselves with idle chips | ACCEPTED 39/50 (78%) |
| 5 | mopper only if a soldier was affordable (`SOLDIER.paintCost`) | ACCEPTED 21/30 (70%) |
| 6 | soldiers refuel at towers | REJECTED 13/30, 4/30 (monotone decreasing) |
| 7 | moppers navigate to visible enemy paint | ACCEPTED 20/23 (87%), 0 swept losses |
| 8 | soldiers stand still to save upkeep | rejected on trace (towers 6 v 8) |
| 9 | remember unbuilt ruins | discarded on reachability (ruins saturate) |
| 10 | SRPs (lattice centres + tower-saturation gate) | **queued**, `src/alice_i10d` |

**Immediately next**:
1. Record the roster point from run `20260906-222958`
   (`track_vs_old_bots.py gauntlet/20260906-222958`) — it played `alice_iter5`, so
   the tool's `snapshot_as_of` labelling is correct here without hand-editing.
   Interim: `alice_iter5` beats `alice_iter1` **19/20 (95%)**.
2. Launch iteration 10's sweep: `BOT=alice_iter7 OPPONENTS="alice_i10d" NMAPS=12`
   (gate >= 16/24). Pre-registration is three entries above.

**Standing facts a fresh session must not relearn**
- Deaths are `Action.DieAction` inside a Turn, **not** `Round.diedIds`. The dumper
  is fixed; any older "units alive" figure in this log before that fix is
  cumulative spawns.
- `PaintAction` = tile painting (takes a MapLocation); `AttackAction` = hitting a
  robot/tower (takes an id). Verified in `GameMaker$MatchMaker`.
- Towers are the master variable; ruin **supply** caps them, not discovery.
- Chips are never binding. Paint is. Tower paint is the pool that gates spawning.
- Coverage is a *contested stock*, and 81% of games are decided by the r2000
  painted-area tiebreak.

**Tooling added this session** (all in `agents/alice/tools/`): fixed death
accounting plus per-window spawns/deaths/transfers/starvation, tower-paint pool
(`twPaint`), map wall-density and ruin count, `sweep-tally.sh` (read a running
gauntlet, with the zero-arm inversion spelled out), `dose-compare.sh` (exact
within-run comparison on shared (map,side) cells).

**Drafted, unqueued**: hybrid bug-nav (`bugnav-draft.java`) — motivating evidence
retracted, see the maze entry; do not queue it without new evidence.

## Iteration 11 candidate — SPLASHERS: an entire unit type, never built, holding two exploits

`runSplasher` has existed since iteration 0 and **no tower has ever spawned one**.
The spawn line is `(rnd(4) == 0) ? MOPPER : SOLDIER` — a splasher cannot occur.
Two facts, both already sitting in my own `RULES.md`, make this the strongest
remaining direction:

1. **Splashers are the only unit that can *take* enemy ground.** A soldier cannot
   overwrite enemy paint at all (engine: `soldierAttack` paints only empty or
   already-ally). A mopper only clears enemy paint to *empty*. A splasher
   **overwrites enemy paint with ours** within r²≤2 of its target centre. Since
   **81% of games are decided by the round-2000 painted-area tiebreak**, the only
   unit that converts the opponent's score into ours has never been on the field.

2. **A splasher out-ranges paint and money towers, with zero retaliation.** Its
   effective reach to a tower is dist²=16 (centre at 4, splash 2 beyond) against
   those towers' action radius of r²=9. `RULES.md` line 119 records this and
   nothing in the bot uses it. Towers are the **master variable** of this game
   (LEARNINGS §3d), and this is a way to remove the opponent's towers for free —
   which also frees the ruin, since a dead tower leaves its ruin rebuildable by
   *either* team. Only defense towers (r²=16) can answer it.

So splashers attack both halves of the win condition at once: they raise our
painted area by lowering theirs, and they break the master variable on the
opponent's side. This is the "high-risk structural exploration" track the
algorithm calls first-class, and it is squarely the winner's-profile shape.

**Cost and the obvious risk**: 300 paint + 400 chips, the most expensive unit, and
paint is the binding resource while chips are not. Iteration 5's lesson applies
directly and in the *opposite* direction this time — the mopper was too cheap and
starved the soldier pipeline, so a splasher at 300 tower paint could starve it far
harder. Any spawn rule must therefore be gated the same way iteration 5's was:
**only build a splasher when doing so does not deny a soldier**, e.g. require tower
paint ≥ `SOLDIER.paintCost + SPLASHER.paintCost`.

**Pre-registered before writing it:**
1. Gate: H2H vs the then-accepted snapshot, >= 16/24 at NMAPS=12.
2. Mechanism: `spl` (splashers alive) > 0, **and** enemy tower deaths or our
   coverage-gain-on-contested-tiles must rise. "Splashers exist" is not evidence —
   the same trap iteration 10a fell into.
3. Displacement gate (from iteration 5 and 10b): soldier spawn count and tower
   count must not fall.
4. Reachability check FIRST, before coding: confirm from a trace that enemy paint
   in splash range actually occurs often — if the two armies never contact, the
   unit is dead weight at 300 paint a copy.

### Splasher reachability check — done BEFORE writing the code this time

The pre-registered question: does enemy paint in splash range actually occur often
enough to justify a 300-paint unit? Answered from traces already on disk, no new
games needed.

Enemy coverage in every game traced this session runs **280-590‰** — between a
quarter and three-fifths of the map is enemy-painted at any time, on both sides,
all game. A splasher's target centre only needs to be within dist²≤4 and it
overwrites enemy paint within r²≤2 of that centre. With enemy paint covering
hundreds of tiles, a splasher essentially cannot fail to find a target.

**Reachability: PASS, decisively.** This is the opposite of iteration 9, where the
same check (run too late) showed 21 of 22 ruins already built and killed the idea.
Doing it first cost one grep of existing logs.

### Fixed-roster point recorded — `alice_iter5` vs the frozen roster

Run `20260906-222958` was a deliberate roster run, so these are **solid** points:

| current build | opponent | result |
|---|---|---|
| `alice_iter5` | `alice_iter0` | **23/24 (95.8%)** |
| `alice_iter5` | `alice_iter1` | **23/24 (95.8%)** |

This is the lineage's only absolute-strength instrument, and it had been stale
since iteration 4 (and then only as a hollow, backfilled point). Both frozen
opponents are now beaten ~96%, which is the answer the moving gauntlet pool cannot
give: the bot is genuinely stronger, not just measured against softer opposition.

Note both roster opponents are now over the 80% retirement threshold. Per the
opponent-pool rules they would normally be retired — but roster members are
explicitly **never retired**, because the value is each line's long-run trend. They
stay.

### Ops hazard — a shared tool was rewritten underneath a running process

The roster run's 72 games completed and then collation died with
`tools/gauntlet.sh: line 170: syntax error near unexpected token '}'`. The script
is **not** broken: `bash -n` passes and `git status` shows no local modification.
What happened is that bash reads a script incrementally as it executes, so a
`git pull` that rewrote `tools/gauntlet.sh` while my hours-long invocation was
still running shifted the file underneath the interpreter.

Consequence and the fix, both already provided for: **only the collation is ever
lost** — the remote runner is `setsid`-detached, so the games are safe — and
`tools/gauntlet-collect.sh 20260906-222958` recovered the run in full
(`results.csv`, `reasons.txt`, `summary.txt`, `losses/`). No games were re-run.

Worth remembering because the symptom points at the wrong thing: a syntax error in
a shared tool looks like a broken tool, and the instinct is to fix or work around
it. The tool was fine.

## Iteration 11 — REJECTED on the trace, and two of my three diagnoses were my own reading error

**First, the correction, because it matters more than the result.** I concluded
twice that the splasher gate was "dead code" (`spl0`, `+spl0`) and twice changed it
— 11b lowered the threshold from 500 to 300, 11c made it deterministic. **Both
diagnoses were wrong.** `+spl` is a *per-window* counter and I only ever printed
the last two windows (r1500, r2000). Splashers are built **early**, while towers
still hold their initial 500 paint, so the windows I looked at were legitimately
zero while the mechanism was firing.

A probe bot settled it: DefaultSmall round 1, `SPAWN id11577(T1,SPLASHER)` and
`SPAWN id12772(T1,SPLASHER)`, `spl2 +spl2`. The full Mirage window set shows
**13 splashers built** (2 at r1, 11 by r500, 2 by r1000).

So iteration 11a's original gate was fine, and 11b/11c were changes made to fix a
problem that did not exist. Cost: two matches and a wrong entry above. **The rule I
broke is one already in my own LEARNINGS — "a replay counter means nothing until
you have found its call site" — restated: a *windowed* counter means nothing until
you have looked at every window.** `tail -2` is not a measurement.

(The probe also revealed a second instrument gap: `run()`'s `finally` block
overwrites every indicator string with the bytecode report, so `setIndicatorString`
is unusable for probes as the bot stands. I read the SPAWN lines instead.)

### The actual result: rejected, for the reason I pre-registered

| per window | alice_i11 | alice_iter7 |
|---|---|---|
| r500: soldiers spawned | **+45** | **+70** |
| r500: towers | **9** | **10** |
| r500: coverage | **368‰** | **506‰** |
| r2000: coverage | **448‰** | **535‰** |

**The displacement gate fails outright.** I pre-registered "soldier spawn count and
tower count must not fall", and both fall — hard, and *early*, which is when
expansion is decided. 13 splashers at 300 tower paint each is **3,900 paint**, or
roughly 19 soldiers, spent during the exact window when the bot should be racing to
complete tower patterns. Coverage is already 138‰ behind at r500 and never recovers.

This is iteration 5's lesson running in reverse, precisely as the pre-registration
predicted: the mopper was too *cheap* and starved soldiers by out-competing them on
price; the splasher is too *expensive* and starves them by consuming the whole
stash. Both fail through the same tower-paint bottleneck.

### The idea is not dead — the timing is wrong
Splashers remain the only unit that can take enemy ground, and that argument is
untouched by this result. What is refuted is **building them during expansion**.
The fix is the one iteration 10c already proved for SRPs: **towers first, luxuries
from the leftovers.** Next attempt (11d) gates splasher spawning behind tower
saturation, exactly as `SRP_MIN_TOWERS` does.

## Iteration 10 — NEAR MISS (13/24, 54.2%), refinement applied as pre-registered

Run `20260906-225531`, `BOT=alice_iter7` (zero arm), 12-map sample, both sides.

| criterion | result | verdict |
|---|---|---|
| gate: H2H vs `alice_iter7` >= 16/24 | **13/24 (54.2%)** | **NEAR MISS** — clears 50%, not the noise band |

Above the bar for "directionally right", below it for "accept". Per the loop this
earns a refinement of the *same* solution rather than a new target, and the
refinement was pre-registered before the sweep, so it is not retrofitted:

> "`SRP_MIN_TOWERS = 10` is a magic constant... If the gate result is
> map-sensitive, the first refinement is the principled form — gate on *ruin
> saturation* rather than an absolute tower count."

**10e implements exactly that**: build an SRP only where **no ruin is visible at
all**. It is self-calibrating (no constant to tune per map size or ruin density)
*and* it is the placement rule the engine demands — `updateResourcePatterns`
re-checks the whole 5×5 every round and resets the 50-round timer if a single tile
stops matching, so an SRP must sit in our interior. **Ruins are the frontier**:
they are precisely what both teams contest. So one gate now serves two purposes,
which is a better sign than a tuned number.

Beats `alice_iter7` on Mirage. Queued for the next sweep.

## Iteration 11 — REJECTED, confirmed by gauntlet (3/14, 21.4%)

The trace reject above is confirmed on the full instrument: the 11c build scored
**3/14 (21.4%)** against `alice_iter7` before the run finished the arm. Early
splashers are not a marginal loss, they are a large one — consistent with 3,900
tower paint diverted during the expansion window.

**11d (splashers gated behind tower saturation) is a different arm** and is not
covered by this result: it beats `alice_iter7` on Mirage with soldiers and towers
no longer suppressed (+62 vs +65 soldiers, 11 towers each, coverage 505 vs 478‰,
and `+spl5` confined to the post-saturation window). It goes into the next sweep
alongside 10e.

Both refinements are the same idea arrived at twice independently — **towers
first, luxuries from the leftovers** — which is now the strongest structural rule
this lineage has.

---

# CURRENT STATE v2 (supersedes the earlier index)

**Accepted lineage**: `iter0 → iter1 → iter2 → iter4 → iter5 → iter7` (current).
`src/alice` == `src/alice_iter7`, compiles, and is what plays in the tournament.
Gaps at 3 and 6 are rejected iterations.

| iter | change | result |
|---|---|---|
| 4 | towers self-upgrade with idle chips | ACCEPTED 39/50 |
| 5 | mopper only if a soldier was affordable | ACCEPTED 21/30 |
| 6 | soldiers refuel at towers | REJECTED 13/30, 4/30 |
| 7 | moppers navigate to visible enemy paint | ACCEPTED 20/23, 0 swept losses |
| 8 | soldiers stand still to save upkeep | rejected on trace |
| 9 | remember unbuilt ruins | discarded on reachability |
| 10 | SRPs, tower-count gate (`10d`) | **NEAR MISS 13/24** → refined to `10e` |
| 11 | splashers, ungated (`11c`) | REJECTED 5/18 → refined to `11d` |

**Fixed roster (absolute strength, solid points)**: `alice_iter5` beats
`alice_iter0` 23/24 and `alice_iter1` 23/24 — both 95.8%.

**Next action**: sweep `alice_i10e` and `alice_i11`(=11d) against `alice_iter7`,
`NMAPS=12`, gate >= 16/24.
- `10e` = SRPs built only where **no ruin is visible** (self-calibrating; also the
  engine-mandated interior placement, since ruins are the contested frontier).
- `11d` = splashers only once `getNumberTowers() >= 10`.

**The strongest structural rule found this session**: *towers first, luxuries from
the leftovers.* Reached independently by iteration 10 (SRPs displaced tower
building) and iteration 11 (early splashers displaced it harder). Towers are the
master variable; ruin **supply**, not discovery, caps them.

**Instrument warnings for a fresh session**
- Deaths are `DieAction` inside a Turn, not `Round.diedIds`.
- `PaintAction` = tile paint (MapLocation arg); `AttackAction` = hit a robot/tower (id arg).
- `+sold/+mop/+spl/died/xfer/starved` are **per-window** counters. **Read every
  window, not the tail** — that error produced two wrong "dead code" diagnoses.
- `setIndicatorString` is unusable for probes: `run()`'s `finally` overwrites it
  with the bytecode report every turn. Read SPAWN/action lines instead.
- A shared tool rewritten mid-run (`git pull`) can throw a bogus syntax error;
  only collation is lost, recover with `gauntlet-collect.sh`.

---

# Session 3 — the tournament breaks the lineage open

## Housekeeping: the runs that were in flight when session 2 was killed

Session 2 died at ~00:55 UTC to an account-wide API rate limit. All three
gauntlets finished on the VM and all were already collated. Nothing was re-run.

**Run `20260906-225531`** (bot=`alice_iter7`, 48 games, 12 maps) was the sweep
session 2 pre-registered. Note it measured `alice_i10d` and `alice_i11`, **not**
`alice_i10e` — 10e was written at 23:11, sixteen minutes *after* the run launched
at 22:55. So the pre-registered "sweep 10e and 11d" was only half executed.

| arm | H2H vs `alice_iter7` | gate (>=16/24) | decision |
|---|---|---|---|
| `alice_i10d` (SRP, `SRP_MIN_TOWERS=10`) | **13/24 (54%)** | FAIL | near miss again, on fresh maps |
| `alice_i11` (= 11d, splashers gated at 10 towers) | **8/24 (33%)** | FAIL | **REJECT** |

**Iteration 11 is closed.** Both arms are now measured: ungated splashers 3/14
(21%), tower-saturation-gated splashers 8/24 (33%). Gating fixed the mechanism —
splashers no longer displace tower building — and the result is still a third
below the bar. Splashers are not the missing piece; the gate was not the problem.

`alice_i10d` reproducing 13/24 on a *fresh* 12-map sample (it scored 13/24 before
on different maps) is worth recording: that is the same near-miss point measured
twice on disjoint ground, which is much stronger than one 13/24. SRPs are worth
about +4% and not more.

## Iteration 12 — the tournament exposes a whole-lineage blind spot

### The measurement that reframes everything

The first full round-robin tournament (`tournaments/20260907-0100`, 450 games)
was mid-flight. Alice's record against the independent lineage `bob`, over the
first 58 games:

**1 win, 57 losses.**

Not a side artifact (33 losses as A, 24 as B), not map-specific (every map but
Rose), not a forfeit (real games, 240-2000 rounds). 59 of the losses are
`MAJORITY_PAINTED` — bob reaching the 70% coverage win condition outright — and
many arrive by round 400-800.

This is the self-referential blind spot that `TRAINING_ALGORITHM.md` warns about,
landing exactly as predicted. Eleven iterations of within-lineage measurement,
including a fixed-roster instrument reading **95.8%**, could not see it, because
every instrument alice owns descends from alice.

### Trace 1 — Paintball (alice A, lost r383, `MAJORITY_PAINTED`)

| round | alice $ | alice tw | alice sold | alice twPaint | alice cov | bob tw | bob sold | bob cov |
|---|---|---|---|---|---|---|---|---|
| 100 | 1400 | 4 | **2** | 2205 | 370‰ | 6 | **11** | 588‰ |
| 200 | 1300 | 4 | 7 | 1675 | 314‰ | 7 | 8 | 638‰ |
| 300 | 2000 | 2 | 4 | 100 | 311‰ | 7 | 8 | 641‰ |

Alice's coverage **peaks at r60 and declines for the rest of the game**. That is
an absolute degeneracy signal, not an opponent-relative one.

The controlled comparison is round 100: **both teams hold ~$1300, and alice holds
three times bob's tower paint (2205 vs 755) — and fields 2 soldiers to bob's 11.**
With more of both resources, alice fields a fifth of the army. Resources are not
the constraint; conversion is.

### Trace 2 — gridworld (alice B, lost r335), generality confirmed

| round | alice $ | alice tw | alice cov | bob $ | bob tw | bob cov |
|---|---|---|---|---|---|---|
| 120 | 2440 | 5 | 273‰ | 1290 | 8 | 399‰ |
| 160 | 3240 | **5** | 277‰ | **10** | **14** | 596‰ |
| 320 | 3420 | 6 | 287‰ | 5780 | 15 | 675‰ |

gridworld has **25 ruins**. Bob claims 14 of them by round 160 while running its
treasury down to **$10** — it converts every chip into capacity. Alice claims 5,
builds *no* tower between r80 and r240, and sits on **$3,240**, enough for three
towers it never builds.

### Root cause, read out of the code the trace pointed at

`runSoldier` targets a ruin only if one is inside vision (`senseNearbyRuins`,
r²=20 ≈ 4.5 tiles). Otherwise it calls `wander`, which is a **random walk**:
a heading held for `5 + rnd(8)` steps (mean 8.5) and re-rolled on any block.

Random-walk displacement after T steps grows as **√T**; directed travel grows as
**T**. On a 31x31 map a soldier that has exhausted the ruins near its spawn tower
essentially never reaches a distant one. Alice does not fail to *build* ruins —
it fails to *arrive* at them. Chips then pile up because chips buy towers, and
towers need a soldier standing on a ruin.

### This falsifies iteration 9's synthesis

Iteration 9 concluded, and I wrote into the closed-directions ledger:

> Ruin **supply** limits tower count: a healthy bot builds out to the map's ruins
> and stops. [...] retires an entire family of "help soldiers find ruins" ideas.

That was inferred from self-play, where Mirage finished 10+11 of 22 ruins built.
Both sides were equally bad at arriving, so the ruins ran out *late and evenly*
and the ceiling looked like supply. Against a lineage that actually travels, the
same map class splits 15-6. **The ledger's own stated re-open condition — "a map
class exists where ruins are not saturated by mid-game" — is met**, and I am
re-opening on that basis plus external evidence, not on "feels under-explored".

### Hypothesis (pre-registered)

> Alice's expansion is diffusive, not directed. Making the wander heading
> persistent — one number, `WANDER_RUN` — converts the random walk into a
> ballistic one and lets soldiers reach unclaimed ruins.

Dose-response with a zero arm, one mechanism, nothing bundled:

| arm | `WANDER_RUN` | package |
|---|---|---|
| zero | `5 + rnd(8)` (mean 8.5) | `alice_iter7` |
| A | 25 | `alice_i12a` |
| B | 100 | `alice_i12b` |

**Pre-registered mechanism gate**: tower count at r400 must rise vs `alice_iter7`.
That is precisely the gate iteration 9 failed (10 vs 11), so it is a gate this
family has already proven it can fail.

**Pre-registered accept gate**: head-to-head vs `alice_iter7` > 50% (the
algorithm's primary test), mechanism gate passed, no one-directional regression.

### Mechanistic verification — gridworld, `alice_i12b` (A) vs `alice_iter7` (B)

| round | i12b tw | i12b cov | iter7 tw | iter7 cov |
|---|---|---|---|---|
| 200 | **11** | 449‰ | 4 | 225‰ |
| 400 | **15** | **620‰** | 4 | 233‰ |
| 2000 | 15 | 640‰ | 6 | 317‰ |

`alice_i12b` wins, and reproduces **bob's own profile** on this map: 15 towers,
~630‰ coverage. `alice_iter7` reproduces the losing profile it showed against bob:
stalled at 4-6 towers, coverage flat near 230-320‰.

**One constant.** Same ruin supply, same map, same everything else: 15 towers
against 4. Iteration 9's "supply, not discovery" is dead.

A second reading falls out of the same table: alice's treasury reaches **$697,960**
by r1800 in the i12b game but only crosses $50k *after* tower saturation at r600.
Iteration 6's reject rested on "chips are not binding — the treasury sits on
$100k+". That is true only in the saturated end-state; through the whole
contested phase (r0-r400) alice runs at $1,300-2,600, pinned just under
`CHIP_RESERVE = 1450`. The premise was measured in the wrong window. This does
not re-open iteration 6 (its dose-response was monotone decreasing, which stands
on its own), but the *stated reason* needs the correction on record.

### Queued for iteration 13 — the coverage plateau, read off the same replay

The i12b verification game supplies the next target for free. `alice_i12b` reaches
620‰ at r400 and then **flatlines at 628-640‰ for the remaining 1,600 rounds**
with 23 soldiers alive. A 1,600-round stall with a full army is an absolute
degeneracy signal of the kind step 1 says to prefer over opponent-relative ones.

The arithmetic says the plateau is structural, not behavioural: at the end
i12b holds 640‰ and `alice_iter7` holds 317‰, summing to **957‰ of a map that is
~4% walls**. Every paintable tile is already painted by someone. Per `RULES.md`,
a soldier's attack "paints tile if empty or already-ally" and **cannot overwrite
enemy paint**. So once the map saturates, soldiers have nothing legal left to do,
and the 70% instant win is unreachable by soldiers alone — it requires *taking*
enemy paint (moppers remove it; splashers overwrite it within r²≤2).

This does not re-open iteration 11 by itself — splashers were measured at 21% and
33% and that stands. What it does is name the condition those measurements were
taken under: both were played from round 1, competing with expansion, in a
lineage that stalls at 5-6 towers. A splasher's value is realised only *after*
saturation, which `alice_iter7` reaches at ~630‰ around r400 and which the losing
build never reached at all. If iteration 12 accepts, the post-saturation window
becomes a real, reachable, majority-of-the-game condition for the first time —
that is a specific reason the recorded cause no longer applies, and it is the
condition iteration 11's own ledger entry should be checked against before
anything is rebuilt.

**Reachability pre-check to run first** (the one iteration 9 skipped and paid for):
in an accepted-i12 game, count the rounds where alice has ≥1 soldier with a legal
paint target versus rounds where it has none. If soldiers are idle for 1,500
rounds, the plateau is real and worth an iteration; if they are busy, it is not.

### Interpretation registered in advance for the dose curve

`WANDER_RUN` is the wander policy for **every** unit that falls through to
`wander`, not just soldiers — moppers (iteration 7 sends them at visible enemy
paint, else wander) and splashers use it too. One mechanism, but two consumers.
If the curve peaks at the low dose (25) rather than rising to 400, the likely
reason is a mopper with no enemy paint in vision committing 400 steps to one
heading and leaving the contested area. Registering that now so it is a
prediction rather than a post-hoc story.

#### Iteration 13 reachability pre-check — RUN, and it passes decisively

Ran the check before building anything this time. `alice_i12b` paint actions per
200-round window on gridworld:

| window | r200 | r400 | r600 | r800 | r1000 | r1200 | r1400 | r1600 | r1800 | r2000 |
|---|---|---|---|---|---|---|---|---|---|---|
| paint acts | 375 | 179 | 25 | 21 | **2** | 11 | **4** | 14 | **3** | 3 |

Paint activity falls **95%** between r400 and r600 and never recovers, while
23-27 soldiers stay alive for the remaining 1,400 rounds. That is roughly
**34,000 idle soldier-turns** in one game. The plateau is not soldiers being lazy;
it is soldiers having no legal target, exactly as the saturation arithmetic
predicted. Iteration 13's premise is reachable — recorded before the fact, unlike
iteration 9.

**But its priority is correctly secondary**, and it is worth saying why so a later
session does not over-rank it. This is a 2,000-round self-play game. Against `bob`
the games *end* at r335-r800 because bob reaches 70% outright; the decisive phase
there is r0-r400, which is precisely the phase iteration 12 addresses. The idle
post-saturation window only exists in games alice is not already losing. Fix the
expansion race first; harvest the idle turns second.

### The tournament's other half: alice is not weak, alice is missing one capability

Partial standings at 323 of 450 games, once the alice-carol pair began:

| pair | record |
|---|---|
| bob beats alice | **143 - 7** (4.7%) |
| alice beats carol | **10 - 1** (90.9%) |

This materially changes the reading. Alice is not a weak bot in absolute terms —
against the *other* independent lineage it wins nine games in ten. The 4.7% is
one specific capability that bob has and that **both** alice and carol lack, which
is exactly what the traces say it is: directed expansion.

Two consequences for the method:
1. Per the opponent-pool classification, `bob` is a **benchmark** (<30%), not a
   peer: a target to close on, and it must never gate acceptance. `carol` is a
   peer that alice currently dominates and is close to the 80%-retire rule — but
   these are tournament opponents, not gauntlet opponents, so neither rule
   applies mechanically. Recorded so a later session does not misapply them.
2. Two of three independent lineages converged on the same blind spot. That is
   worth more than a single lineage's failure: it suggests the diffusive-expansion
   trap is what a bot naturally grows into from a reactive `senseNearbyRuins`
   soldier, and that escaping it is a deliberate act. It also means the tournament
   would have been a *weak* instrument if only alice and carol existed — the
   sanctioned channel is only as good as the most different bot in it.

### Iteration 12 — the remaining two pre-checks, for the record

**History.** `wander`'s `5 + rnd(8)` run length is iteration 0's arbitrary choice.
No iteration ever established it on evidence, so changing it supersedes nothing.
Better: the functional-area map has carried "wander + slide; soldiers walk into
map corners and die there | iter0" as a known defect since the beginning, and the
vision/action table already listed *random wander* as the fallback for soldier,
mopper and splasher alike. Iteration 7 fixed exactly this for moppers by giving
them a destination (accepted, 20/23). Iteration 12 is the same idea applied to
the fallback itself, for the units iteration 7 did not cover.

**Trigger frequency.** The branch is not rare — it is the soldier's *default*.
A soldier reaches `wander` on every turn with no unbuilt ruin inside r²=20, which
after the first ~80 rounds is nearly every turn for nearly every soldier: on
gridworld `alice_iter7` built no tower at all between r80 and r240 while holding
$3,240, so essentially the whole army was in the wander branch the whole time.

One risk this raises, registered before the sweep: the same "walks into a corner
and dies" defect gets *longer* commitment at dose 400. The re-roll-on-block should
catch it (a map edge fails `canMove`, forcing a fresh heading), which is why the
zero/25/100/400 curve is worth having rather than a single point.

## Iteration 10 — CLOSED, REJECTED. SRPs are below the instrument's resolution

Run `20260907-010620`, 48 games, 12 fresh maps, `bot=alice_i10e`.

| arm | H2H | pre-registered gate |
|---|---|---|
| `alice_i10e` vs `alice_iter7` | **14/24 (58.3%)** | >=16/24 — **FAIL** |
| `alice_i10e` vs `alice_i10d` | **12/24 (50.0%)** | — |

Two readings, and the second is the one that closes the thread.

**1. The headline misses the gate and sits inside the noise floor.** At n=24 with
p=0.5 the binomial sd is 2.45 games, so 14/24 is +0.8 sd — indistinguishable from
a coin. Doctrine #6 says distrust any delta under the noise floor regardless of
how good the story is, and the story here is good, which is exactly when the rule
earns its keep.

**2. The self-calibrating gate is exactly tied with the tuned constant: 12/24.**
This is the informative number. 10e replaced `SRP_MIN_TOWERS >= 10` with "build
only where no ruin is visible", which I argued was both map-adaptive and
engine-mandated. It is neither better nor worse. The design preference
"self-calibrating thresholds beat fixed constants" is a real pattern but it is not
a law, and here the threshold was never the binding term — the *feature* is.

Pooling everything iteration 10 ever measured, on three disjoint map samples:

| build | H2H vs `alice_iter7` |
|---|---|
| `alice_i10d` | 13/24, 13/24 |
| `alice_i10e` | 14/24 |

Three samples, 72 games, all within one sd of 12/24. SRPs are worth somewhere
between nothing and ~+4%, and this instrument cannot resolve which. Iteration 10
has now had four refinements (10b, 10c, 10d, 10e) against a `MaxNearMissRefinements`
of 3. **Reject and leave the area** — which is also what `MaxConsecutiveRejects`
requires, the economy area having produced iterations 10 and 11 back to back.

### Closed-directions ledger
| direction | closed by | can re-open if |
|---|---|---|
| SRPs (resource patterns) as a chip sink | iteration 10: 13/24, 13/24, 14/24 across 72 games on three disjoint map samples; all within 1sd of even | the *chip* constraint becomes binding in the contested phase (r0-r400). It is not today: iteration 12's trace shows chips pinned at CHIP_RESERVE while the real bottleneck is arriving at ruins. A future bot that expands properly and then runs out of chips would be a genuine re-open. |
| "Self-calibrating beats a tuned constant" as an automatic design win | 10e vs 10d = 12/24, a dead tie | it is still the right default when a constant is *known* to trade one opponent against another; it is not a reason to expect a gain when the constant was never the binding term |

**Both economy iterations (10 and 11) are now closed**, and the area is left. The
loop moves to navigation, where iteration 12 already has a mechanistic result that
dwarfs anything the economy area produced.

---

# CURRENT STATE v3 (supersedes v2)

**Accepted lineage**: `iter0 → iter1 → iter2 → iter4 → iter5 → iter7` (current).
`src/alice` == `src/alice_iter7`. Gaps at 3, 6, 8, 9, 10, 11 are all rejected.

## The one thing that matters right now

The first full round-robin (`tournaments/20260907-0100`) says **bob beats alice
143-7 (4.7%)**, while **alice beats carol 27-10 (73%)**. Alice is not a weak bot;
it is missing exactly one capability that bob has and that alice and carol both
lack: **directed expansion**.

Traced to one line. `runSoldier` targets a ruin only within vision (r²=20) and
otherwise calls `wander`, a random walk holding a heading `5 + rnd(8)` steps.
Random-walk displacement grows as √T, so soldiers never *arrive* at distant ruins;
chips then pile up ($3,240 unspent on gridworld) because chips buy towers and
towers need a soldier standing on a ruin. Bob reaches 14 towers by r160 on a
25-ruin map running its treasury at $10; alice reaches 5.

**Iteration 12** changes exactly one constant, `WANDER_RUN`. Mechanistic
verification on gridworld, `alice_i12b` vs `alice_iter7`: **15 towers / 620‰ at
r400 against 4 towers / 233‰**. That reproduces bob's own profile.

## IN FLIGHT — run `20260907-013038`, 60 games, resume here

`BOT=alice_iter7 OPPONENTS="alice_i12a alice_i12b alice_i12c" NMAPS=10 MAXJOBS=2`

Doses: `alice_i12a`=25, `alice_i12b`=100, `alice_i12c`=400; zero arm =
`alice_iter7` (`5 + rnd(8)`, mean 8.5). Rows read `LOSS` from **alice_iter7's**
perspective, so a `LOSS` row is a **win for the candidate**.

- **Interim: 4/4 for `alice_i12a`**, including both sides of Circuit and both
  sides of quack — two swept maps, immune to spawn advantage.
- The run is slow (~1 game/10 min) because the 450-game tournament plus a sibling
  gauntlet hold the rest of `GLOBAL_CAP`. That is the semaphore working.
- It is `setsid`-detached: it completes whether or not anyone watches. If this
  session died, **do not re-run it** — recover with
  `../../tools/gauntlet-collect.sh 20260907-013038`.

**Pre-registered gates** (do not move them after seeing data):
- accept: H2H vs `alice_iter7` **> 50%**, mechanism gate passed, no
  one-directional regression;
- mechanism gate: **tower count at r400 must rise** vs `alice_iter7` — the exact
  gate iteration 9 failed (10 vs 11), so this family has already proved it can
  fail it.

**On accept**: snapshot the winning dose to `src/alice_iter12` AND copy it into
`src/alice` (HEAD is what plays in the tournament — that is the whole point of
this iteration), archive a replay, redraw both charts, extend
`progress/vs_old_bots_history.csv`, commit atomically.

## Next targets, in order

1. **Iteration 13 — the coverage plateau.** Reachability check already RUN and
   passed: paint actions collapse 95% between r400 and r600 and stay near zero for
   1,400 rounds with 23-27 soldiers alive (~34k idle soldier-turns/game). Cause is
   structural: soldiers cannot overwrite enemy paint, and the map saturates
   (640‰ + 317‰ = 957‰ on a ~4% wall map). Taking enemy paint needs moppers or
   splashers. Secondary to iteration 12 because against bob the games end by r400.
2. **PlumberGame** — a genuine **swept** loss to carol (both sides, r772/r723),
   not a 2000-round tiebreak. The only such map. Worth one trace.

## Instrument warnings (carried forward, still all true)
- Deaths are `DieAction` inside a Turn, not `Round.diedIds`.
- `+sold/+mop/+spl/died/xfer/starved` are **per-window**; read every window.
- `setIndicatorString` is unusable for probes — `run()`'s `finally` overwrites it.
- `p` (PaintAction) may not count soldier tile-painting; **trust `cov`**, which is
  the engine's own figure, and win/loss. Every accepted conclusion rests on those.
- A gauntlet's `bot.txt` labels the build that actually played. `+cand` means
  "after iterN, not yet accepted".
- Every run launch prints `pgrep: no matching criteria specified` from the slot
  code. Cosmetic so far, but it is in the concurrency path — reported, not
  worked around.

### PlumberGame traced — alice's one swept loss to carol is the same failure, on the biggest map

`alice` (T1) vs `carol` (T2), lost r772 `MAJORITY_PAINTED`. Map is **60x30**, 22
ruins, 6.2% walls — roughly **twice the area** of the ~30x30 maps that dominate
the pool.

| round | alice $ | alice tw | alice cov | carol tw | carol cov |
|---|---|---|---|---|---|
| 200 | 1380 | 4 | 250‰ | 10 | 311‰ |
| 400 | 2960 | **5** | 308‰ | **15** | 565‰ |
| 700 | 1390 | 4 | 270‰ | 16 | 673‰ |

This is the **same failure mode as against bob**, produced by a different
opponent: alice stalls at 4-5 towers holding ~$3,000 while the opponent reaches
16. Alice's coverage again peaks (~308‰ at r400) and then declines.

The reason this is worth more than one more losing trace: **it is a prediction
that came true before I looked.** Iteration 12 says the defect is diffusive
search, whose cost scales with map area — √T displacement against an area that
grows as L². So the failure should be worst on the largest maps. PlumberGame is
alice's **only** swept loss to carol out of the whole pair, and it is the largest
map in it. Alice beats carol 27-10 everywhere else and loses both sides here.

That is a real out-of-sample confirmation of the mechanism, obtained for the cost
of one replay dump, and it makes iteration 12's map-size dependence a concrete
thing to check in the sweep diff rather than a story.

### One observation recorded, deliberately NOT acted on

Both independent lineages transfer paint constantly (`xfer` 7-14 per window for
carol, 1-5 for bob); alice's `xfer` is **0** in every window of every game. That
is iteration 6, which I rejected on a monotone-decreasing dose-response (13/30 at
dose 60, 0/6 at dose 120).

Two independent lineages converging on a mechanic I measured as harmful is worth
writing down, but it is **not** grounds to re-open: my measurement was a proper
dose-response with a zero arm, and "other bots do it" is not evidence about *my*
bot's marginal value — it is exactly the "feels under-explored" reasoning the
ledger forbids. The ledger's stated re-open condition stands unchanged: paint must
become non-binding first. Note that iteration 12, by multiplying tower count
three- to four-fold, is precisely the kind of change that could satisfy it — so
this should be re-checked *after* iteration 12 settles, on the stated condition
rather than on the coincidence.

### Pre-registered before the sweep data lands: the map-area check

The PlumberGame trace turns iteration 12's mechanism into a falsifiable
prediction about *which* maps should move, so I am registering it now, with the
sweep at 11/60 and only the `alice_i12a` arm partly played.

**Prediction.** Diffusive search covers area as T while directed search covers it
as T², so the deficit iteration 12 removes grows with map area. Therefore
`alice_i12a/b/c`'s margin over `alice_iter7` should be **larger on large maps and
smaller on small ones**, and on a small enough map it should vanish — a random
walk crosses a 20x20 map fine.

**What would falsify it.** A flat margin across map sizes, or a margin that is
*larger* on small maps. Either would mean the win comes from something other than
reaching distant ruins, and the mechanistic story would need rewriting even if the
headline accepted.

The sweep's 10-map sample is `Circuit quack galaxy BunnyGame windmill Bunny
DefaultLarge Fossil CastleDefense boxofchocolates`. Map dimensions come free from
each replay's `MatchHeader`, so this costs one dump per map and no VM game slots.

This is the "cheap unrun instrument" of doctrine #10, registered *before* it could
be used to rationalise whatever the headline turns out to be.

## Iteration 12 — arm A complete: `alice_i12a` (dose 25) beats `alice_iter7` 15/20

Run `20260907-013038`, first arm complete, 10 maps x both sides.

| | |
|---|---|
| H2H vs `alice_iter7` | **15/20 (75%)** |
| swept wins (both sides) | **5** — BunnyGame, Circuit, boxofchocolates, galaxy, quack |
| **swept losses** | **0** |
| split by side | 5 — Bunny, CastleDefense, DefaultLarge, Fossil, windmill |

**Every pre-registered gate clears.** H2H 75% > 50%; the mechanism gate (tower
count at r400 rises) was verified at 15 vs 4 on gridworld; and "no unresolved
one-directional regression" is satisfied in the strongest possible way — there is
**not one swept loss** in the arm. Under a fair coin, 15 of 20 has p = 0.021.

The diff shape is the one doctrine #7 calls a real causal effect rather than
churn: the flips are one-directional. Nothing regressed on both sides anywhere.

### The map-area check, run exactly as pre-registered

Map areas via a byte-size proxy on the `.map25` files, calibrated on two maps
whose headers I had already dumped (gridworld 31x31=961 tiles -> 2256 bytes;
PlumberGame 60x30=1800 -> 3912; so area ~ (bytes-359)/1.974). Stated as a proxy
because it is one: a 2-point calibration, good enough to rank maps, not to
measure them.

| outcome for `alice_i12a` | maps | mean est. area |
|---|---|---|
| **swept win** | quack 1013, Circuit 1235, BunnyGame 1472, galaxy 2050, boxofchocolates 3033 | **1,761 tiles** |
| split by side | CastleDefense 333, windmill 846, Fossil 870, Bunny 1303, DefaultLarge 1506 | **972 tiles** |

**The prediction holds.** Maps where the ballistic walk sweeps both sides average
**81% more area** than maps where it only splits. The three *smallest* maps in the
sample — CastleDefense (~18x18), windmill, Fossil — are all splits, and the two
largest are both swept wins. CastleDefense at ~333 tiles is precisely the case I
said should show no margin, because a random walk crosses a small map perfectly
well; it shows none.

**Honest caveats.** Ten maps, and the relation is not monotone — Bunny (1303) is a
split while quack (1013) is a swept win. So this confirms the *direction* the
mechanism predicts, at the extremes, and does not establish a clean curve. What
matters is that it was registered before I looked and could have come out flat or
inverted, which would have forced a rewrite of the mechanistic story even with a
75% headline.

Arms B (dose 100) and C (dose 400) are still playing. **The accept decision waits
for the curve**, because the dose that goes into `src/alice` should be the one the
curve picks, not the first one measured.

### Mechanism gate verified on a second map — boxofchocolates (55x55, 19.5% walls, 19 ruins)

gridworld alone would be a single-map mechanism check, so I pulled one of the
swept-win replays out of the sweep itself. `alice_iter7` (T1) vs `alice_i12a` (T2):

| round | iter7 tw | iter7 cov | i12a tw | i12a cov |
|---|---|---|---|---|
| 900 | 5 | 374‰ | 4 | 430‰ |
| 1200 | 5 | 437‰ | 6 | 493‰ |
| 1500 | 5 | 440‰ | **8** | 527‰ |
| 1800 | 5 | 434‰ | **8** | **531‰** |

The gate passes again — towers 8 vs 5, coverage 531‰ vs 434‰ — and `alice_iter7`
shows its signature failure a third time: **tower count frozen at 5 from r900
onward and coverage plateauing at ~437‰ while the candidate keeps climbing.**

Two things worth recording because they qualify the mechanism rather than just
confirming it:

1. **The margin is much smaller here than on gridworld (8v5 versus 15v4), and it
   arrives 1,000 rounds later.** This map is **19.5% walls** against gridworld's
   20%... but 55x55 with only 19 ruins, so ruins are sparse *and* the ballistic
   walk gets interrupted constantly — every blocked step re-rolls the heading,
   which is the diffusive behaviour creeping back in. That is a concrete,
   named limitation of the dose-only fix, and the obvious refinement (slide along
   the obstacle instead of re-rolling) is a **separate mechanism** and therefore a
   separate iteration, not something to bundle into this accept.
2. Both teams show `xfer0` and very large `starved` counts (49 and 72 per window
   late). Consistent with everything else this lineage does; noted, not acted on.

## Iteration 14 — PRE-REGISTERED NOW, to fire after iteration 12 lands

Written while the sweep's arm C is still playing, so the gate cannot be shaped by
the result. This is the mechanism I explicitly refused to bundle into iteration 12.

### The defect

Iteration 12 makes the wander heading persistent, but `wander` still **re-rolls
the heading to a fresh random direction whenever the next step is blocked**:

```java
} else {
    wanderDir = directions[rnd(8)];   // <-- throws the heading away
    wanderSteps = WANDER_RUN;
    if (rc.canMove(wanderDir)) { rc.move(wanderDir); wanderSteps--; }
}
```

So on obstructed ground the walk reverts to diffusive no matter how large
`WANDER_RUN` is: the effective run length is not `WANDER_RUN`, it is the mean free
path between obstacles. This is measured, not assumed — it is the named limitation
I recorded from boxofchocolates (55x55, 19.5% walls), where the candidate's margin
was only 8 towers to 5 and arrived ~1,000 rounds later than gridworld's 15 to 4.

### The change (one mechanism)

**Slide instead of re-rolling**: on a block, try `rotateLeft`/`rotateRight` of the
*current* heading and keep the heading, exactly as `tryMove` already does for
directed movement. Re-roll only when all three are blocked. `WANDER_RUN` keeps
whatever value iteration 12 accepts; nothing else changes.

Note this makes `wander` and `tryMove` use the same obstacle response, which is
the kind of change that should have been one function all along.

### Pre-registered gates

- **Accept**: H2H vs the accepted `alice_iter12` snapshot **> 50%**, no
  one-directional regression (zero unexplained swept losses).
- **Mechanism gate**: tower count at r400 must rise again versus `alice_iter12`
  **on the high-wall subset**. If towers do not move there, the mechanism did not
  engage and the change is discarded without a full run, per step 4.

### Map-class prediction, with its falsifier

Blocking frequency scales with **wall fraction**, so the margin should be
**concentrated on high-wall maps and ~zero on open ones**. Concretely: on maps
below ~10% walls I expect no measurable margin; on maps above ~18% (boxofchocolates
19.5%, gridworld 20.0%, and the 19.8%-wall maze that already broke iteration 7) I
expect the margin.

**Falsifier**: a margin that is flat across wall fraction, or larger on open maps.
Either kills the mechanistic story even if the headline passes — the same standard
I held iteration 12's map-area check to.

This is a *different* covariate from iteration 12's (**area**, not **wall
fraction**), which is what makes it a genuinely separate mechanism rather than
more of the same dose. If iteration 12's margin tracks area and iteration 14's
tracks walls, that is two independent confirmations of one model of the defect.

### Known risk, recorded before building

Naive wall-sliding is the classic failure case of hand-rolled navigation: a
concave pocket can trap a slider indefinitely, which is strictly worse than a
re-roll that at least escapes. Real bug-navigation (bug0/bug2, with a remembered
wall-following side and an exit test) is the principled fix and is a **larger,
separate mechanism** — the cross-year research names hybrid bug-nav as a perennial.
So: slide first because it is one line and tests the premise; bug-nav only if
slide engages but traps. If the trace shows trapping, that is a *success* of the
diagnosis, not a failed iteration.

### How the accepted dose will be chosen — written before arm C finishes

With arm C at 4 of 20 games, registering the selection rule now so it is not
chosen to suit the answer.

**The dose that ships is the one the CURVE picks, not the arm with the best
number.** These are different, and the difference matters:

- A maximum taken across three arms is **biased upward**. If all three doses were
  truly identical at 60%, the best of three at n=20 would still land near 70% by
  chance alone. So `alice_i12a`'s 15/20 is an over-estimate of dose 25's true
  value *because it is the maximum*, and I should not quote 75% as dose 25's
  effect size.
- The **shape** is what carries information, because it is not a maximum of
  anything. The curve so far is 50% (zero arm, by definition) → **75% at dose
  25** → **60% at dose 100**. That is concave with an interior optimum, which the
  algorithm names as stronger evidence than any single point, and it is what I
  predicted before the sweep: an over-long commitment sends moppers (which share
  `wander`) out of the contested area.

**So the rule is:** ship the dose at the curve's peak. If arm C at 400 comes in
at or below arm B, the curve is single-peaked at 25 and dose 25 ships. If arm C
comes in *above* arm B, the curve is not single-peaked, the interior-optimum story
is wrong, and I should say so rather than quietly shipping the best arm.

**And the honest effect size to report is the shape, not the peak**: iteration 12
is worth "clearly positive, somewhere in the 60-75% band against `alice_iter7`,
with the low dose better than the high one" — not "75%".

### A partial arm is a BIASED subsample, not a small one — caught before it misled me

Arm C at 9 of 20 games read **8/9 (89%)**, above arm A's 75% and arm B's 60%. Taken
at face value that falsifies the interior-optimum reading I had just registered,
and I was one step from writing that down.

It is an artifact. **The arms play the maps in the same order**, so a partial arm
is always the same *prefix* of the map list — never a random sample of it. Arm C's
nine games are BunnyGame, Circuit, galaxy, quack and windmill, which are precisely
the maps where every arm already does well; the maps that produced arms A and B's
losses (CastleDefense, Fossil, Bunny, DefaultLarge, boxofchocolates) are all still
unplayed in arm C.

Restricting every arm to arm C's five maps:

| arm | dose | on arm C's maps | full-arm |
|---|---|---|---|
| `alice_i12a` | 25 | 9/10 (90%) | 15/20 (75%) |
| `alice_i12b` | 100 | 8/10 (80%) | 12/20 (60%) |
| `alice_i12c` | 400 | 8/9 (89%) | *incomplete* |

Matched on maps the three arms are **90 / 80 / 89** — a dead heat, and arm C is
not evidence against the interior optimum. Every arm scores 15-25 points higher on
this easy prefix than on the full sample, which is exactly the size of the
distortion.

**The rule this earns:** the run's guarantee is that "the map sample is drawn once
and shared by every opponent, so opponent-vs-opponent comparisons *within* a run
are exact" — but that guarantee only holds **once every arm has played every map**.
Mid-run, arms are at different points in a *fixed* map order, so a cross-arm
comparison is confounded by map difficulty in a systematic direction, not a random
one. More games do not fix it; only completing the arms does.

So: **compare partial arms only on their shared map subset, or wait.** This is the
within-run twin of the cross-run warning in AGENT.md, and it is sharper, because
the shared-sample guarantee makes a mid-run comparison *look* exact when it is not.

## Iteration 12 — ACCEPTED at dose 25. The dose-response curve is single-peaked

Run `20260907-013038` complete, 60 games, 10 maps x both sides x 3 doses, one
shared map sample so the cross-arm comparison is exact.

| dose (`WANDER_RUN`) | candidate H2H vs `alice_iter7` | swept wins | **swept losses** |
|---|---|---|---|
| `5 + rnd(8)` ≈ 8.5 — **zero arm** | 50% by definition | — | — |
| **25** | **15/20 (75%)** | **5/10** | **0** |
| 100 | 12/20 (60%) | 3/10 | 1 |
| 400 | 12/20 (60%) | 3/10 | 1 |

**The curve is 50 → 75 → 60 → 60: single-peaked, with an interior optimum at the
lowest nonzero dose.** The falsifier I registered before arm C landed — "arm C
comes in above arm B" — did not occur; C and B tied to the game. So the
interior-optimum reading stands as a prediction that survived a stated test, not
as a description written afterwards.

**Two independent criteria pick the same dose, which is why this accept is not a
maximum-of-three artifact.** Dose 25 has the best headline *and* it is the only arm
with **zero swept losses**; doses 100 and 400 each introduce a map they lose from
both sides. The accept gate's third clause — "no unresolved one-directional
regression" — is therefore satisfied *only* by dose 25, independently of which arm
happened to score highest. And per the selection rule I committed before the data
landed, the smallest effective dose is also the right choice under a flat curve, so
every rule I had pre-registered points at 25.

**Effect size, stated honestly.** 75% is the maximum of three arms and is biased
upward as an estimate of dose 25's true value. The defensible claim is: *iteration
12 is worth roughly 60-75% against `alice_iter7`, with the low dose better than the
high ones, and the mechanism verified on two maps.*

### Why the high doses are worse — the predicted reason, confirmed

I registered this before the sweep: `WANDER_RUN` is the wander policy for **every**
unit that falls through to `wander`, moppers and splashers included, so an
over-long commitment should send a mopper with no enemy paint in vision out of the
contested area for hundreds of rounds. The curve turning down between 25 and 100,
and staying down at 400 rather than falling further, is the shape that predicts —
the cost saturates once the commitment already exceeds the map.

### Gates, all cleared
- **Primary accept** — H2H vs last accepted snapshot > 50%: **75%**, p = 0.021.
- **Mechanism gate** — tower count at r400 rises: verified twice, gridworld
  **15 v 4** and boxofchocolates **8 v 5**. This is the gate iteration 9 failed
  (10 v 11), so the family had already shown it can fail it.
- **No one-directional regression**: zero swept losses in the accepted arm.
- **Map-area check** (pre-registered, could have falsified the mechanism): swept
  maps average 81% more area than split maps; the three smallest maps are all
  splits, the two largest both swept.

### Lineage
`iter0 → iter1 → iter2 → iter4 → iter5 → iter7 → **iter12**`.
`src/alice` == `src/alice_iter12`, byte-identical to the measured `alice_i12a`
apart from the package line (verified by diff, not by assertion).

**This is the first iteration in this lineage accepted on a target found by an
external instrument.** Every previous one was chosen by looking at alice's own
games. It is also the largest single mechanical change the lineage has made, and
it is one constant.

## Iteration 14 — mechanism verified, evaluation running (`20260907-021333`)

Built from the pre-registration above, unchanged. Motivating game re-run first,
per step 4, on the map that motivated it.

**boxofchocolates (55x55, 19.5% walls), `alice_i14` (A) vs `alice_iter12` (B):**

| round | i14 tw | i14 cov | iter12 tw | iter12 cov |
|---|---|---|---|---|
| 400 | **6** | 366‰ | 3 | 242‰ |
| 800 | **10** | 634‰ | 5 | 339‰ |
| 2000 | **12** | **648‰** | 6 | 338‰ |

`alice_i14` wins, and the **pre-registered mechanism gate passes on the high-wall
map: towers at r400 are 6 against 3**, doubling by the end (12 v 6) with coverage
648‰ against 338‰.

The size of this is worth stating plainly. On this same map, iteration 12's
accepted dose managed only **8 towers to 5** against `alice_iter7`. Removing the
re-roll is worth *more here than the persistent heading was* — which is exactly
what the diagnosis predicted: on obstructed ground the effective run length was
never `WANDER_RUN`, it was the mean free path between obstacles, so the heading
being persistent bought little until it could survive contact with a wall.

Evaluation launched: `BOT=alice_iter12 OPPONENTS=alice_i14 NMAPS=14`, 28 games.
Gate as pre-registered: H2H vs `alice_iter12` **> 50%**, no one-directional
regression, and the **map-class check on wall fraction** — margin concentrated on
high-wall maps, ~zero below ~10% walls, with a flat or inverted relation as the
stated falsifier.

One caution carried forward: this is a single map and it is the map the mechanism
was designed against, so it is the *best* case by construction. The run decides.

### The iteration 14 sample's terrain, and what my own prediction implies about the headline

Pulled every map header for run `20260907-021333`'s sample straight out of the
tournament replays (one remote pass, compile once, no game slots). Saved to
`tools/map_terrain.txt` — reusable, and the first time this lineage has had wall
fraction and area as data rather than as an impression.

| band | maps | count |
|---|---|---|
| high (>=14%) | gridworld 20.0, yearofthesnake 18.4, Piglets2 15.3, roads 14.4 | 4 |
| mid (11-14%) | FourCorners 13.3, Flower 12.0, Snowman 11.5 | 3 |
| **low (<10%)** | SandyBeach 8.7, Portal 7.8, Mirage 7.5, Justice 7.4, SaltyPepper 7.3, Bunny 7.0, starburst 6.2 | **7** |

**This matters before the result, so I am writing it before the result.** My
pre-registered prediction is that iteration 14's margin lives on high-wall maps
and is ~zero below 10% walls. **Half the sample is below 10% walls.** So if my
prediction is right, the headline H2H must come in *modest* — something like
16-18 of 28 — because ten of the twenty-eight games are played on ground where I
have already said the mechanism should do nothing.

Two consequences I am binding myself to now:

1. **A headline near 60% would be a success, not a near miss**, provided the
   margin is concentrated where predicted. Judging this change by the same 75%
   yardstick iteration 12 hit would be judging it on a sample I already know is
   mostly irrelevant to it.
2. **A big headline driven by the low-wall maps would be bad news**, not good.
   It would mean the win comes from something other than surviving contact with
   walls, and the mechanism story would be wrong even though the bot got better.
   I would have to say so and re-diagnose.

This is doctrine #4's representativeness rule applied in advance: the instrument
resolves the question only on the part of the sample that poses it. The
`AGENT.md` rule against hand-picking maps is why I am not fixing the sample to
high-wall maps — the random draw is the honest instrument, and the fix is to
analyse by band, not to choose the band.

### Re-checking iteration 12's area finding against real numbers — it holds, with a caveat I have to report against myself

I claimed the area effect from a **byte-size proxy** calibrated on two maps. Now
that headers are data, here is the same check on true areas.

| outcome for `alice_i12a` | mean area (proxy) | **mean area (real)** |
|---|---|---|
| swept win (5 maps) | 1,761 | **1,772** |
| split by side (5 maps) | 972 | **1,004** |
| ratio | +81% | **+76%** |

The proxy was good and the finding stands: **maps the accepted dose sweeps are
76% larger than maps it only splits**, on measured areas.

**But now the caution, which cuts against me.** With the real headers I can also
compute wall fraction for that same sample — and it separates the outcome too:

| outcome | mean wall % |
|---|---|
| swept win | **13.5%** |
| split | **8.1%** |

So in iteration 12's ten maps, *two* covariates each "explain" the result. That is
precisely the trap of having three covariates and ten maps: some split will
separate sweeps from splits whether or not it is causal.

**The rule resolves it cleanly, and I am applying it against my own preferred
reading.** Area was **pre-registered** for iteration 12, before the run; wall
fraction was **not**. So:

- area remains the *evidence* for iteration 12's mechanism;
- wall fraction in that sample is a **post-hoc observation**, and therefore a
  hypothesis for the next run — **not** support for anything now.

And that hypothesis is already being tested properly: iteration 14 pre-registered
**wall fraction** as its covariate, before its candidate was even built, on a
freshly drawn sample. A post-hoc pattern from one run becoming a pre-registered
prediction in the next is exactly the right way round, and it happened here by
accident of ordering rather than by design — worth noticing so it can be done on
purpose next time.

**Honest summary of what iteration 12's map analysis proves**: the margin is
larger on maps that are bigger *and* wallier, and that sample cannot separate the
two. Iteration 14's run can, because half its maps are under 10% walls while
spanning 420 to 2,400 tiles.

## Iteration 14 — ACCEPTED. 17/28 (60.7%), and the falsifier did not fire

Run `20260907-021333`, 28 games, 14 maps x both sides, `alice_iter12` as the
zero arm.

| | |
|---|---|
| H2H vs `alice_iter12` | **17/28 (60.7%)** |
| swept wins | 4 |
| swept losses | **1 — starburst** |

### The pre-registered map-class check

| band | maps | candidate |
|---|---|---|
| **HIGH (>=14% walls)** | gridworld 20.0, yearofthesnake 18.4, Piglets2 15.3, roads 14.4 | **6/8 (75%)** |
| mid (11-14%) | FourCorners, Flower, Snowman | 3/6 (50%) |
| **LOW (<11% walls)** | SandyBeach, Portal, Mirage, Justice, SaltyPepper, Bunny, starburst | **8/14 (57%)** |

**The falsifier I committed before building the candidate — "a margin that is flat
across wall fraction, or larger on open maps" — did not fire.** The gradient runs
75% on high-wall ground against 57% on open ground, in the predicted direction.

**The extremes are the cleanest part of the result, and they were not chosen after
the fact:**
- **gridworld, the highest-wall map in the sample at 20.0%, is a swept win.**
- **starburst, the *lowest*-wall map at 6.2%, is the single swept loss.**

That the one both-sides regression lands precisely on the map where the mechanism
is supposed to do nothing is what makes it a **resolved** regression rather than an
unresolved one, which is the accept gate's third clause. It is also the strongest
single piece of evidence in the run, because a mechanism that only helps against
obstacles should be neutral-to-negative where there are none.

### But I am not going to overclaim, because two things do not fit

1. **The mid band is the worst (50%), not the middle.** A clean dose-response in
   wall fraction would be monotone. It is not.
2. **Two low-wall maps are swept wins** (Portal 7.8%, SandyBeach 8.7%). If walls
   were the whole story those should be coin flips.

And the honest statistics: 6/8 against 8/14 is a Fisher exact p of roughly 0.4.
**The band gradient is suggestive, not established.** The headline and the
mechanism gate carry this accept; the map-class check corroborates the direction
and rules out the falsifier, and that is all it does.

### Re-diagnosis, logged as a hypothesis for a future run and NOT as evidence here

Why would open maps benefit at all? Because `canMove` returns false when the tile
is occupied by **a robot**, not only by a wall — and this bot fields 20-45 units.
So the blocking rate that the re-roll was destroying is driven by **wall fraction
*and* unit density**, and wall fraction alone was always going to be a partial
proxy for it. That predicts the benefit should track *crowding* too, which would
explain a broad gain with a high-wall tilt — exactly the shape observed.

Per the rule I applied to iteration 12's wall finding, this is **post-hoc and
therefore a hypothesis**: it must be pre-registered against a fresh sample before
it counts. Recorded here so it can be tested rather than assumed.

### Lineage
`iter0 → iter1 → iter2 → iter4 → iter5 → iter7 → iter12 → **iter14**`.
`src/alice` == `src/alice_iter14`, byte-identical to the measured `alice_i14`
apart from the package line, verified by diff.

Both navigation iterations together take this lineage from a random walk to a
persistent heading that survives contact with obstacles — the capability the
tournament showed `bob` had and alice did not.

## Tournament `20260907-0100` — final, all 450 games

| pair | result |
|---|---|
| bob beats **carol** | 144-6 (96.0%) |
| bob beats **alice** | 143-7 (95.3%) |
| **alice** beats carol | 99-51 (66.0%) |

**Standings** (each bot plays 300 games): **bob 287/300 (95.7%)**, **alice
106/300 (35.3%)**, **carol 57/300 (19.0%)**.

Alice finishes second. The shape matters more than the placing: bob beats *both*
other lineages at ~96%, and alice beats carol at 66%. So this is not a ranking of
three bots on a continuum — it is one bot that has a capability and two that do
not, which is exactly what the traces said and what iterations 12 and 14 address.

**This tournament measured `alice_iter7`** — the pre-navigation build, HEAD at
01:00. Both accepted iterations landed afterwards. So the 7-143 is the *baseline*
for the fix, and the next tournament is the first genuine test of whether it
converts. That is the number to look for, and I should be honest in advance that
a within-lineage 75% and 61% need not translate into much against a bot that is
95% against everyone.

## The frozen roster has SATURATED — the instrument cannot see recent progress

Roster run `20260907-022504` (`bot.txt` label `alice_iter12`, so it measures the
iteration 12 build, as intended) is reading **20 wins in the first 21 games
(~95%)** against `alice_iter0` and `alice_iter1`.

`alice_iter5` scored **95.8%** against the same two opponents. So the roster
cannot distinguish the build that lost 7-143 from the build that beats it 75%
head-to-head. **Both roster opponents are pinned near 100%, and doctrine #4 says
an instrument pinned near an extreme cannot resolve anything.**

This is the failure mode the chart exists to prevent, arriving in the chart
itself: `vs_old_bots` is my only absolute-strength instrument, and it has gone
flat for reasons that have nothing to do with alice's strength.

**Fix**: `progress/roster_extra.txt` exists precisely for fixed yardsticks that
are not auto-derived snapshots, and qualifies them on the grounds that they never
change. `alice_iter7` is frozen, never changes, and is *known* to resolve — the
last two iterations scored 75% and 61% against this lineage's builds rather than
95%. Adding it gives the chart a rung that is actually in the measurable band,
without hand-editing the auto-derived roster, which `AGENT.md` forbids.

I am adding it after this run completes so the run's own labelling is unaffected.

### Why the roster saturated — a shared-tool flaw, reported rather than worked around

The saturation is not bad luck in the draw. It is structural, and it gets worse
the more disciplined an agent is.

`progress_lib.roster_numbers` strides over **iteration numbers**:
`{0} | range(1, newest+1, 5)`. For alice that is `{0, 1, 6, 11}`. Iterations 6 and
11 were **rejected**, so those snapshots do not exist and are silently dropped:

```
accepted snapshots:        [0, 1, 2, 4, 5, 7, 12, 14]
roster_numbers(14, 5):     [0, 1, 6, 11]
resulting roster:          ['alice_iter0', 'alice_iter1']
```

`AGENT.md` promises "every 5th accepted snapshot (iter1, iter5, iter10, ...)".
Striding over **accepted ordinals** instead would give `[iter0, iter7]` — and
`alice_iter7` is exactly the opponent that still resolves, since the last two
iterations scored 75% and 61% against this lineage rather than 95%.

**The perverse consequence**: an agent that rejects more candidates creates more
gaps in its iteration numbering, so *more* of its roster slots point at snapshots
that were never accepted, and its absolute-strength chart degrades. Rejecting bad
work is the loop functioning correctly, and it is being punished by the
instrument. The roster also cannot recover on its own, because the missing
numbers never come into existence.

This is the third infrastructure issue this session, and like the other two I am
reporting it rather than patching a shared tool from an agent workspace.

**Local fix, which is sanctioned**: `progress/roster_extra.txt` exists precisely
for pinned yardsticks, qualified on the grounds that they never change.
`alice_iter7` is frozen, never changes, and sits in the measurable band. Adding it
gives the chart a rung that can actually move, without hand-editing the
auto-derived roster.

### The roster result: it cannot answer the question. That is the finding.

Run `20260907-022504` complete, 48 games, `bot.txt` label `alice_iter12`:

| opponent | `alice_iter5` (2026-09-06) | **`alice_iter12`** (2026-09-07) |
|---|---|---|
| `alice_iter0` | 23/24 (95.8%) | **23/24 (95.8%)** |
| `alice_iter1` | 23/24 (95.8%) | **24/24 (100.0%)** |

**The roster does not confirm that iteration 12 made alice stronger — and it does
not refute it either. It cannot tell.** The total movement between the build that
lost 7-143 and the build that beats it 75% head-to-head is **one game**, on an
instrument already pinned against the ceiling.

I want to be exact about this, because the tempting reading is available and
wrong: 95.8% → 95.8% and 95.8% → 100% is *not* evidence that iteration 12 works,
and quoting "alice now beats iter1 100% of the time" as progress would be
precisely the error I wrote into LEARNINGS §6 rule 5 a few hours ago — a rising
number against a saturated opponent is not about strength.

**So the honest state of the absolute-strength question is: unmeasured.** The only
instrument that could answer it is the next tournament, where the accepted build
meets two lineages that are not descended from it. The 7-143 is the baseline and
the fix is untested against it.

**Instrument repaired for next time.** `alice_iter7` is now pinned in
`progress/roster_extra.txt`, and the roster reads `alice_iter0 alice_iter1
alice_iter7`. Run `20260907-023637` is playing the current build against it now to
lay the first point on that rung — the last two iterations scored 75% and 61%
against this lineage's builds, so unlike the other two rungs it sits in a band
where movement is visible.

---

# CURRENT STATE v4 (supersedes v3)

**Accepted lineage**: `iter0 → iter1 → iter2 → iter4 → iter5 → iter7 → iter12 →
iter14` (current). `src/alice` == `src/alice_iter14`. Gaps are rejected attempts.

## What this session established

The first full round-robin gave alice its first external measurement:
**bob 287/300 (95.7%), alice 106/300 (35.3%), carol 57/300 (19.0%)** — bob beats
alice 143-7 and carol 144-6; alice beats carol 99-51. One bot had a capability
that the other two lacked, and the traces named it: **directed expansion**.

`runSoldier` targets ruins only inside vision (r²=20) and otherwise wandered
**randomly**. Random-walk displacement grows as √T, so soldiers never *arrived* at
distant ruins, and chips piled up unspent because chips buy towers and towers need
a soldier standing on a ruin.

| iter | change | result |
|---|---|---|
| 10 | SRPs | **REJECTED** — 13/24, 13/24, 14/24 across 72 games, all within 1sd of even |
| 11 | splashers (both arms) | **REJECTED** — 3/14 ungated, 8/24 gated |
| **12** | wander heading persists (`WANDER_RUN`) | **ACCEPTED** — dose curve 50→**75**→60→60, peak at 25, zero swept losses |
| **14** | wander slides instead of re-rolling | **ACCEPTED** — 17/28 (60.7%); high-wall 75% vs open 57% |

Mechanism verified on three maps: gridworld **15 towers v 4**, boxofchocolates
**8 v 5** (iter12) and **12 v 6** (iter14).

## What is NOT established, stated plainly

- **Whether any of this converts against bob.** The tournament that produced
  7-143 measured `alice_iter7`. HEAD now carries both fixes; the next tournament
  is the first real test. A within-lineage 75% need not move a 4.7%.
- **Absolute strength.** The frozen roster is saturated (see below) and returned
  one game of movement. The question is *unmeasured*, not answered.
- **Iteration 14's wall-fraction story.** 6/8 vs 8/14 is Fisher p≈0.4 —
  suggestive, and the falsifier didn't fire, but not established.

## Instrument state — read before trusting a chart
- **The frozen roster is saturated.** `alice_iter0`/`alice_iter1` sit at 96-100%.
  A shared-tool flaw causes it: `roster_numbers` strides over iteration *numbers*
  (`{0,1,6,11}`), not accepted-snapshot ordinals, so every rejected iteration
  silently deletes a roster slot. **Reported to the coordinator, not patched.**
  Local fix: `alice_iter7` pinned in `progress/roster_extra.txt`; run
  `20260907-023637` lays its first point.
- **A partial gauntlet arm is a biased subsample, not a small one.** Arms play
  maps in a fixed shared order, so a partial arm is always the same easy prefix.
  This nearly produced a wrong conclusion; the coordinator has since made the
  summary print an UNEQUAL SAMPLES warning.
- `tools/map_terrain.txt` now holds wall%, area and ruin count per map — real
  data for map-class pre-registration instead of impressions.

## Next, in order
1. **Read the next tournament.** It is the only instrument that can answer the
   question this session opened.
2. **Iteration 15 — crowding, pre-registered:** `canMove` also fails on tiles held
   by **robots**, and this bot fields 20-45 units, so blocking rate depends on unit
   density as well as walls. This explains iteration 14's broad gain with a
   high-wall tilt. It is **post-hoc and must be pre-registered on a fresh sample**
   before it counts as anything.
3. **Iteration 13 — the coverage plateau** (reachability already passed: ~34k idle
   soldier-turns/game; soldiers cannot overwrite enemy paint once the map
   saturates). Secondary: against bob the games end before the window opens.

### The repaired rung's first point — and it corrects my own effect-size estimate downward

Run `20260907-023637`, `bot.txt` label `alice_iter14`, 12 fresh maps both sides
(including maze, gridworld, CastleDefense, DefaultLarge — a good terrain spread).

| | |
|---|---|
| `alice_iter14` vs **`alice_iter7`** | **15/24 (62.5%)** |
| swept wins | 4 |
| swept losses | 1 |

**The rung resolves, which is the point of adding it**: 62.5% sits in a band where
movement is visible, against 96-100% on the two auto-derived rungs that cannot
move at all.

**And it says something I would not have got from the head-to-heads.** Composing
them naively — iteration 12 beat `alice_iter7` at 75%, iteration 14 beat
`alice_iter12` at 60.7% — suggests `alice_iter14` should beat `alice_iter7` by
*more* than 75%. Measured on fresh ground, the cumulative gain is **62.5%**.

The two gains do not compose. Two reasons, both of which I had already written
down before seeing this:

1. **75% was the maximum of three arms and is biased upward**, exactly as
   registered before arm C landed. This is the correction arriving.
2. Each run draws its own map sample, so the two head-to-heads were measured on
   different ground; only this rung measures the *cumulative* change on ground
   neither iteration was selected against.

**So the honest statement of what this session's two accepted iterations bought
is 62.5% against the build they replaced — not 75%, and not 75% compounded with
61%.** That is a real gain and a smaller one than the individual gates implied,
and it is precisely the correction a frozen yardstick exists to supply. It is also
the first time this lineage's absolute-strength chart has had a rung capable of
delivering such a correction.

## Iteration 15 — PRE-REGISTERED before building: soldiers never attack enemy towers

Found by the API sweep Phase 0 #2 mandates ("periodically sweep the full
`RobotController` API for methods the bot never calls — a whole game mechanic sat
unused for 81 iterations once"). This is that, in this lineage.

### The gap

`runSoldier` calls `rc.attack(...)` in exactly three places, and **all three
target tiles**: paint the marked pattern tile, paint the tile underfoot, paint the
nearest empty tile in range. `senseNearbyRobots(..., opponent())` appears **only in
the tower code**. A soldier has never once been pointed at an enemy robot or tower.

Per `RULES.md`, engine-verified: *"Soldier attack: if target holds enemy TOWER →
50 dmg (never damages robots); else paints tile."* An L1 tower has 1000 HP, so
**~20 soldier actions destroy an enemy tower** — and destroying a tower removes a
spawn point, 5-15 paint/turn, and the 500 paint it started with.

Three things make this the right target now:

1. **The capacity is already paid for.** The iteration 13 reachability check
   measured ~**34,000 idle soldier-turns per game** after the map saturates.
   This is the algorithm's named winner's profile — *capability preserved at zero
   marginal cost* — rather than a new cost.
2. **Reachability is externally evidenced**, not assumed. On Paintball, **bob took
   alice from 4 towers to 2**. Bob's units reach alice's towers and kill them, so
   the geometry plainly permits it; alice simply never tries.
3. **It attacks the master variable directly.** Every accepted iteration in this
   lineage works by raising alice's own tower count. Nothing has ever *lowered the
   opponent's*, which is the same variable from the other side.

### The change (one mechanism, deliberately non-displacing)

In `runSoldier`, the **idle** action branch — the one that currently paints the
nearest empty tile because there is nothing better to do — first checks for an
enemy tower inside the action radius and attacks it instead.

It goes in the *idle* branch specifically. Ruin-building is this lineage's proven
master variable and iterations 10 and 11 were both rejected for displacing it, so
tower-attacking must spend only turns that were otherwise wasted. That history is
the reason for the placement, and it is exactly the "History" pre-check.

### Pre-registered gates
- **Accept**: H2H vs `alice_iter14` **> 50%**, no unresolved one-directional
  regression.
- **Mechanism gate**: the opponent's **tower count at r2000 must fall** relative to
  the baseline arm, and tower-destruction events must be non-zero. If soldiers
  never get in range, the branch is dead code and it is discarded on the trace
  without spending a full run — the iteration 9 mistake, not repeated.

### Reachability pre-check to run FIRST
Before evaluating: dump one existing game and count soldier-turns with an enemy
tower within r²=9. If that is ~zero in self-play, the feature is dead code *in the
instrument that would judge it*, even though bob demonstrably achieves it — and
that would be a representativeness problem (doctrine #4) to state before, not
after, the run.

## Iteration 15 — DISCARDED on the trace. Two distinct failures, both caught before a run

### 15a: the branch was dead code, and the "win" was a mirror artifact

I placed the tower-attack check in the *idle* branch to avoid displacing ruin
building. It never fired: **zero soldier→tower attacks in a full 2,000-round
game**, by either team.

The cause is the guard I nested inside. The block immediately above is:

```java
if (!here.getPaint().isAlly() && rc.canAttack(cur)) { rc.attack(cur); }
```

Painting the tile underfoot **consumes the action nearly every turn**, so
`isActionReady()` was already false by the time my branch was reached. This is
precisely the pre-check the algorithm spells out — *"read the guard you are
nesting inside: a new clause added under an outer condition that already excludes
the targeted case can never fire"* — and I wrote the clause without reading the
five lines above it.

**And 15a "won" its verification match 14 towers to 7.** Had I taken that as
evidence I would have promoted a no-op. Two independent checks caught it: the
attack census showed zero engagement, and `alice_i15` vs `alice_iter14` is
effectively a **mirror**, where my own Phase 0 note already says *any inter-team
stat difference is positional, not policy*. The 14-v-7 was the map, not the code.

### 15b: moved before the paint — it engages, and still does not convert

| | `alice_i15b` | baseline |
|---|---|---|
| soldier→tower attacks | **44** (37 money, 7 paint) | **0** |
| **enemy towers destroyed** | **0** | 0 |
| enemy tower count @r2000 | **8** | **8** |

The mechanism now demonstrably fires — the first time in this lineage's history a
soldier has attacked a robot — and the **pre-registered mechanism gate fails**:
*"the opponent's tower count at r2000 must fall, and tower-destruction events must
be non-zero."* It did not fall. Nothing died.

Two reasons, and the second matters more:

1. **The damage is spread, not concentrated.** 44 attacks × 50 = 2,200 damage
   against 7-8 towers of 1,000-1,500 HP each. Every soldier independently picks
   the weakest tower *within its own radius*, so no tower ever reaches zero.
   Concentrating fire needs coordination between units — comms — which is a far
   larger mechanism and not a refinement of this one.
2. **44 attacks across 2,000 rounds with 12-17 soldiers alive is almost no
   contact at all** — roughly one attack per 45 rounds. In self-play both
   lineages expand into their own halves and rarely meet. Against `bob`, alice's
   soldiers absorbed **38 tower attacks in 100 rounds** — contact is about
   twenty times more frequent.

### So the honest verdict is not "this feature is bad"

It is the case the algorithm names explicitly: *a mechanistically-correct feature
can be a no-op because upstream state never produces the situation it handles.*
**My own gauntlet cannot judge this feature**, because my own lineage does not
pose the threat it answers — doctrine #4's representativeness rule, which I
registered as a risk before running and which is exactly what happened.

I am **not** shipping it on that reasoning, because "my instrument can't see it"
is not evidence that it helps. It is discarded, and the condition for re-opening
is specific and checkable.

### Closed-directions ledger
| direction | closed by | can re-open if |
|---|---|---|
| Soldiers attack enemy towers with spare actions | iteration 15b: engages 44 times, destroys **zero** towers, enemy tower count unchanged at 8 | an instrument exists where soldier↔tower contact is frequent (the tournament shows ~20x more contact vs `bob` than in self-play). A synthetic archetype that contests our half would create one. Do not re-open on a self-play run. |
| Concentrating soldier fire on one tower | not tested — identified as the reason 15b fails | it requires comms to coordinate targets; that is a separate, larger mechanism, and should be proposed as one |

**Cost of this iteration: two verification matches.** The pre-registered mechanism
gate did exactly what it exists for — the 28-game run was never spent.

## Full roster on `alice_iter14` — the rung replicates, and the saturation is now total

Run `20260907-030654`, 72 games, 12 fresh maps, `bot.txt` label `alice_iter14`.

| rung | result | swept |
|---|---|---|
| `alice_iter0` | **24/24 (100%)** | 12/12 swept, 0 losses |
| `alice_iter1` | **24/24 (100%)** | 12/12 swept, 0 losses |
| **`alice_iter7`** | **14/24 (58.3%)** | 2 swept wins, **0 swept losses**, 10 splits |

**The two auto-derived rungs are now perfect scores.** Not 96%, not 98% — 24 of 24
and 24 of 24, every map swept from both sides. Whatever alice does next, those two
lines cannot move again. The saturation diagnosis is confirmed as completely as it
can be, and the repaired derivation arrived exactly when it was needed.

### The resolving rung replicates

| run | map sample | `alice_iter14` vs `alice_iter7` |
|---|---|---|
| `20260907-023637` | 12 maps | 15/24 (62.5%) |
| `20260907-030654` | 12 **different** maps | 14/24 (58.3%) |
| **pooled** | **24 maps, 48 games** | **29/48 (60.4%)** |

Two independent 24-game measurements on **disjoint map samples**, agreeing within
one game, with **zero swept losses in either**. That is a far stronger statement
than either alone: the cumulative gain of this session's two accepted iterations
over the build they replaced is **~60%**, and it is now replicated rather than
asserted.

It also closes the loop on the correction I made earlier. The individual accept
gates read 75% and 60.7%; naive composition implied well over 75% cumulative. The
frozen yardstick says **60.4%** across 48 games. The gates were not wrong — they
measured what they measured — but the number that describes the lineage's actual
progress is the smaller one, and only a frozen opponent could produce it.

**What the chart can and cannot show now.** `vs_old_bots.png` has 17 rows and three
tracked opponents, but two of its three lines are flat at 100% forever. The single
informative line is `alice_iter7`, and it has exactly two points. The honest
reading of my absolute-strength instrument is that it is **one rung deep** — which
is better than the zero it was this morning, and thin. It will not become
trustworthy until several more accepted snapshots give it rungs at 60-90%.

## Mirror calibration — the null is EXACTLY 50%, and identical code never sweeps a map

Run `20260907-032745`, `alice` vs `alice_mirror`, 12 maps both sides.
`alice_mirror` was **stale** — a fork of some early build — and was regenerated as
a byte-identical copy of `src/alice` differing only in its package line, verified
by diff. (The algorithm's warning that forked archetypes "go silently stale and
inflate win rates" was live in my own workspace and I had never checked it.)

```
overall: 12/24 wins (50.0%)
vs alice_mirror   swept-win 0/12   swept-loss 0/12   split-by-side 12
```

**Every one of the twelve maps split 1-1. Not one sweep in either direction.**

### What this establishes

1. **The null is exactly 50%.** My accept gates were calibrated against the right
   baseline. There is no hidden positional tilt inflating or deflating them.
2. **A swept map is an almost noise-free instrument.** Identical code produced
   **zero** swept wins and **zero** swept losses across 12 maps. So when a
   candidate sweeps a map it has beaten *both* spawn positions, which the null
   never does. That retroactively strengthens every swept-map claim this session:
   iteration 12 dose 25's **5 swept wins / 0 swept losses**, iteration 14's 4/1,
   and the rung runs' 2/0 are all real effects, not spawn luck.
3. **The per-map winner is decided by spawn position**, and it cancels exactly
   over both sides. This is why the algorithm insists on playing both sides, and
   the mirror shows the cancellation is perfect rather than approximate.

### And it invalidates the *reasoning* I used to reject iteration 10

I wrote, closing the SRP thread: *"At n=24 with p=0.5 the binomial sd is 2.45
games, so 14/24 is +0.8 sd — indistinguishable from a coin."*

**There is no coin.** The engine is deterministic and the mirror is exactly
balanced, so re-running produces identical games and there is no game-level
sampling noise for a binomial to describe. A candidate at 14/24 has flipped
**exactly two games** relative to a null that sits exactly at 12/24, and those two
games were flipped *by the code change*.

What variance remains is **map-sample** variance, not game variance — which is
precisely why pooling across disjoint samples is the right move. Pooling SRPs:

| build | H2H vs `alice_iter7` |
|---|---|
| `alice_i10d` | 13/24, 13/24 |
| `alice_i10e` | 14/24 |
| **pooled** | **40/72 (55.6%)** |

**So SRPs were probably a small real positive (+4 games in 72), not nothing.**
The reject decision still stands on its own terms — it missed the pre-registered
16/24 gate three times and had exhausted `MaxNearMissRefinements` — but the
*reason* I recorded was wrong, and the ledger entry needs correcting: SRPs are a
**small real effect below the accept bar**, not an unmeasurable one.

### Correction to the closed-directions ledger
| direction | corrected status |
|---|---|
| SRPs as a chip sink | Previously "within noise, cannot resolve". **Corrected: a small real gain (~+5.6 points, 40/72 pooled) that never cleared the pre-registered bar.** Re-open condition unchanged — it should be revisited if chips ever become binding in the contested phase — but it should be re-opened as "known small positive", not as "unknown". |

### Method note for every future gate
Quote **margin over the mirror null in games**, not standard deviations. "+2 games
against a null that never sweeps a map" is the honest form; "+0.8 sd" imports a
random-sampling model this engine does not have.

### The mirror's second, more valuable use: per-cell causal attribution

The mirror does not only give a scalar null. Because identical code produces a
**deterministic favoured side per map**, it gives a null for every
`(map, side)` cell. Saved as `tools/mirror_null.txt`:

```
Barcode B   BatSignal A   DefaultMedium A   DonkeyKong B
HungerGames B   MoneyTower A   Thirds A   catface B
gardenworld A   headphones B   sierpinski B   windmill B
```

**Method for future evaluations**: pin `MAPS="$(cat tools/mirror_null.txt | ...)"`
to this list, and then any game whose winner differs from `favoured_side` was
flipped **by the change** — not by spawn, not by chance. That converts an
aggregate ("17/28") into an attributed set ("these five specific games flipped,
here is what the mechanism did in each"), which is what the algorithm's
"diff game-by-game and read the diff's shape" actually asks for.

This is the check that would have settled iteration 15b directly. Instead of
concluding "my instrument cannot see this feature", I could have asked: of the
games where those 44 tower attacks occurred, how many deviated from the mirror
null? If zero, the attacks changed nothing and the discard is proven rather than
inferred. That is the form the re-open test should take when an instrument with
real contact exists.

**Standing caveat**: the null table is tied to the build that produced it
(`alice_iter14`). A mirror must be regenerated from the current build every time —
mine was **stale**, a fork of an early build, which would have made it an ordinary
head-to-head against a weak opponent rather than a null, and would never have
announced itself.

## Two new rungs, and iteration 14 replicated on a fresh sample

Run `20260907-033915`, 48 games, 12 fresh maps, `bot.txt` label `alice_iter14`.

| rung | result | swept (win/loss) |
|---|---|---|
| `alice_iter4` | **22/24 (91.7%)** | 10 / 0 |
| `alice_iter12` | **13/24 (54.2%)** | 4 / 3 |

Recording needed `--stride 3`: the tool will not write history for a snapshot that
is not currently in the roster, so the rungs had to be *bootstrapped* in. My
cheaper-path reasoning was right about the games (48 rather than 120) but I had
missed that the stride flag is still required at record time. **After one recorded
run they are permanent** — the roster at the *default* stride is now
`alice_iter0 alice_iter1 alice_iter4 alice_iter7 alice_iter12`, five rungs, exactly
as the history-preservation rule promises.

### Iteration 14 replicated — and it comes in lower

| run | maps | `alice_iter14` vs `alice_iter12` | swept |
|---|---|---|---|
| `20260907-021333` (the accept run) | 14 | 17/28 (60.7%) | 4 / 1 |
| `20260907-033915` (fresh) | 12 **different** | **13/24 (54.2%)** | 4 / 3 |
| **pooled** | 26 | **30/52 (57.7%)** | **8 / 4** |

**Iteration 14 stands, on a smaller effect than its gate suggested.** 57.7% pooled
over 52 games clears the >50% bar, and 8 swept wins against 4 swept losses is a
real effect measured against a mirror null of **0 and 0**. But the honest number
is ~58%, not 60.7%, and the swept ratio is 2:1 rather than the 4:1 the accept run
showed.

### The pattern across both accepts, stated carefully

| iteration | gate figure | replicated | why they differ |
|---|---|---|---|
| 12 | 75% | ~60% (cumulative rung) | 75% was the **maximum of three dose arms** — biased upward by selection, which I registered *before* seeing arm C |
| 14 | 60.7% | 57.7% (pooled) | **one arm, no selection** — the two samples simply bracket a true value near 58% |

These are two different mechanisms and I should not merge them into one law. What
they share is the practical consequence: **an accept gate is one sample, and the
effect size worth quoting is the pooled one after replication.** Both of this
session's accepts were quoted high on first measurement and settled lower, and in
both cases the correction came from measuring again on ground the candidate was
not selected on.

**Nothing here reverses an accept.** Both remain above the bar on pooled data with
positive swept ratios against a zero-zero null. What changes is the number I would
put in a report, which is now 57.7% for iteration 14 and ~60% cumulative for the
pair — not 60.7% and 75%.

## Iteration 16 — PRE-REGISTERED: `CHIP_RESERVE` is a dead band, measured policy-pure

### The measurement, and why this one is trustworthy

Run on a **mirror game** (`alice` vs `alice_mirror`, gardenworld) so both sides run
identical code — the money curve is a property of the *policy*, not of a matchup.

| round | 1 | 50 | 100 | 150 | 200 | 250 | 300 | 400 | 600 |
|---|---|---|---|---|---|---|---|---|---|
| T1 $ | 1980 | 1150 | 1300 | 1250 | 1250 | 250 | 1400 | 1360 | 1210 |
| T2 $ | 2030 | 1150 | 1200 | 650 | 910 | 1360 | 1060 | 1410 | 1360 |
| T2 tower paint | 610 | 880 | 1030 | 1655 | **3715** | 3210 | **4885** | 4020 | 1935 |

**`CHIP_RESERVE = 1450`. The treasury never reaches it, in 600 rounds, on either
side.** It oscillates in $650-1410 — pinned immediately beneath the gate.
Meanwhile **tower paint accumulates to 4,885**, four thousand of it unusable,
because spawning needs chips the gate will not release.

**One constant is stranding both resources at once.** This is the "resource pinned
in a dead band" degeneracy the algorithm names, measured on the current accepted
build rather than inferred.

### The change (one constant, principled rather than searched)

The reserve exists so a soldier can always fund a **1000-chip** tower completion.
The tight bound is therefore *"spawn only if 1000 chips remain afterwards"* —
`1000 + SOLDIER.moneyCost(250) = 1250`, not 1450. The extra 200 is unexplained
padding that costs a spawn every time income crosses it.

| arm | `CHIP_RESERVE` | rationale |
|---|---|---|
| zero | **1450** (`alice_iter14`) | current, unexplained |
| A | **1250** | tight bound: a tower completion still funded after the spawn |
| B | **1000** | aggressive: reserve the tower cost only, spawn may dip below it |

### History pre-check — this supersedes a prior deliberate decision

The code comment records the reasoning that set it: *"spawning greedily at 250/unit
pins money near zero and stalls tower expansion permanently."* That is a real
failure mode and dose B deliberately probes it, which is why B is in the sweep
rather than being assumed safe. The new evidence that supersedes the old reasoning
is the mirror curve above: the treasury is *already* pinned — not near zero, but
just under the gate — and 4,885 tower paint is idle behind it. The old decision
prevented one failure by installing another.

### Pre-registered gates
- **Accept**: H2H vs `alice_iter14` **> 50%**, judged in **games over the mirror
  null**, no unresolved one-directional regression (swept losses, against a
  measured null of 0).
- **Mechanism gate**: mean soldier count in r100-r400 must **rise**, and idle tower
  paint at r300 must **fall**. If neither moves, the gate was not the constraint
  and it is discarded on the trace.
- **Dose-response with a zero arm**, and I expect an interior optimum: if B (1000)
  is worse than A (1250), the old comment's failure mode is real and bounded, which
  is a more useful result than either arm alone.

**Sweep launched**: run `20260907-040318`, `BOT=alice_iter14
OPPONENTS="alice_i16a alice_i16b" NMAPS=12`, 48 games. Rows read `LOSS` from
`alice_iter14`'s perspective, so a `LOSS` is a **win for the candidate**.

### Note on `tools/mirror_null.txt` as a standing instrument

The mirror is not a one-off calibration; the per-map favoured-side table it
produced is **reusable**. Any future evaluation pinned with
`MAPS="$(awk '!/^#/{print $1}' tools/mirror_null.txt)"` can be diffed cell-by-cell
against `favoured_side`, and every deviation is *caused by the change* rather than
by spawn or by chance. That converts a headline into an attributed set of games.
It is tied to the build that generated it (`alice_iter14`) and must be regenerated
whenever the accepted build changes — a stale mirror is not a null at all, which
is exactly the state mine was in when I found it.

## Iteration 16 — arm A result, and the reading it forces on me

`alice_i16a` (`CHIP_RESERVE` 1450 -> **1250**) vs `alice_iter14`: **11/24 (45.8%)**.

Against the measured mirror null of exactly **12/24**, that is **-1 game**.
Lowering the reserve to its principled tight bound does **not** help; if anything
it is marginally negative. Dose B (1000) is still playing.

### I read the trace wrong, and the mirror shows how

I called the treasury sitting at $650-1410 beneath a 1450 gate a "dead band" and
matched it to the algorithm's *resource pinned in a dead band* degeneracy. The
measurement was right; **the diagnosis was not**.

A treasury pinned *just below* a spend gate is the **equilibrium signature of a
converter that is already spending everything above the gate**. Income arrives,
money crosses 1450, a spawn fires (-250), money falls back. The pin is what a
*working* spend policy looks like from the outside — it is not starvation, and
lowering the gate does not unlock spending that was blocked, it only shrinks the
buffer that guarantees a 1000-chip tower completion.

**The distinguishing test I should have applied before building**: a dead band is
pathological only if *capacity sits idle behind it*. I had evidence of idle
capacity — tower paint at **4,885** — and I attributed it to the wrong gate.

### Where that idle paint actually points — iteration 17, pre-registered now

Spawning consumes **250 chips and 200 tower paint**. If tower paint accumulates to
4,885 while chips stay pinned, then **paint income exceeds chip income and chips
are the binding resource** — so the lever is not the spend gate, it is the
*production mix*.

Tower type is currently chosen by **ruin parity**:

```java
UnitType wantTower = ((ruin.x + ruin.y) & 1) == 0
        ? LEVEL_ONE_MONEY_TOWER : LEVEL_ONE_PAINT_TOWER;
```

A fixed ~50/50 split, decided by map geometry, regardless of which resource the
bot is actually short of.

**Hypothesis**: build the tower type for the **scarcer** resource, self-calibrating
from observed stocks rather than from a constant or from geometry.

**History pre-check, and it is a real constraint.** The parity rule was chosen
deliberately: *"immune to the money-at-mark-time timing artifact that made every
early mark a money tower."* A naive "build money if money is low right now"
reintroduces exactly that artifact, because money is *always* low right at a mark.
So the decision must use a **ratio of stocks that is scale-free and slow**, e.g.
`totalTowerPaint / max(1, money)` against a threshold, never instantaneous money
against a constant. Any version that compares money to a fixed number is
disqualified by this pre-check before it is built.

That is registered before dose B lands, so the next iteration's premise cannot be
shaped by how iteration 16 finishes.

## Iteration 16 — REJECTED. Both doses land on exactly 11/24, and the mechanism gate fails

Run `20260907-040318` complete, 48 games, 12 maps both sides, `alice_iter14` as
the zero arm.

| arm | `CHIP_RESERVE` | H2H vs `alice_iter14` | vs mirror null | swept (w/l) |
|---|---|---|---|---|
| zero | 1450 | 12/24 by definition | — | — |
| A | 1250 | **11/24 (45.8%)** | **-1 game** | 1 / 2 |
| B | 1000 | **11/24 (45.8%)** | **-1 game** | 1 / 2 |

**The dose curve is flat and one game negative: 12 → 11 → 11.** Two very different
doses (a 200-chip cut and a 450-chip cut) produce *identical* records. A parameter
whose value does not change the outcome across that range is not the constraint.

### The pre-registered mechanism gate fails, and the trace says why

Gate: *"mean soldier count in r100-r400 must rise, and idle tower paint at r300
must fall."* From `alice_i16a` (T1, reserve 1250) vs `alice_iter14` (T2) on
BunnyGame:

| round | i16a $ | i16a sold | i16a tw | iter14 $ | iter14 sold | iter14 tw |
|---|---|---|---|---|---|---|
| 100 | 2600 | 3 | 2 | 1100 | 2 | 4 |
| 300 | 4630 | 2 | 3 | 600 | 11 | 8 |
| 400 | 2870 | 6 | 4 | 1200 | **19** | **10** |

**Soldier count did not rise — it fell**, and the *lower*-reserve build is the one
**accumulating** money ($2,600-4,630) while the higher-reserve build runs its
treasury down to $600 and fields three times the army. That is the exact opposite
of the predicted direction, so the gate fails outright and iteration 16 is a
reject rather than a near miss.

### And it confirms the re-diagnosis rather than merely failing

Money accumulating in the build that is *allowed* to spend sooner proves the gate
was never what stopped it spending. What stops it is having nothing to spend on —
too few soldiers reaching too few ruins — and once tower count diverges the
income difference dominates everything downstream.

Note also that **which** resource piles up flips with game state: in the mirror
game both sides sat on 4,885 tower paint with chips pinned; here the losing build
sits on $4,630 with tower paint at 205. **The stock that accumulates is a symptom
of the tower mix, not a fixed property of the economy** — which is precisely the
variable iteration 17 was pre-registered against, before this run finished.

### Closed-directions ledger
| direction | closed by | can re-open if |
|---|---|---|
| Lowering `CHIP_RESERVE` (the spend gate) | iteration 16: doses 1250 and 1000 both **11/24**, identical, one game below a zero-variance null; mechanism gate failed with soldier count *falling* | the tower mix is fixed first and chips are then shown to bind with soldiers idle for want of them. Not before — a flat response across a 450-chip range says the parameter is not live. |

**Cost: one 48-game run and one replay dump.** Iterations 12 and 14 were accepted
on this loop and 15 and 16 rejected; the two rejects together consumed less than
one accept's evaluation, which is the ratio the pre-registered mechanism gates are
supposed to produce.

## Iteration 17 — a LATENT BUG found: alice has never built a paint tower, and half of every map's ruins are thrown away

This started as the production-mix iteration pre-registered above. The
mechanism-engagement check found something much larger.

### The census that found it

`alice_i17a` vs `alice_iter14`, gridworld, 2000 rounds. Counting **tower creations**
(a soldier completing a pattern appears as `SOLDIER SPAWN <TOWER>`):

```
12 T1 built MONEY_TOWER      (alice_i17a)
 6 T2 built MONEY_TOWER      (alice_iter14)
 0 PAINT_TOWER built by either team, in the entire game
```

**Not one paint tower, by either side.** `alice_iter14`'s parity rule marks ~half
of all ruins as `LEVEL_ONE_PAINT_TOWER`. Zero of them ever become towers.

### The decisive diagnostic

Built `alice_i17c`: identical to `alice_iter14` except it always marks **MONEY**.
Same map, same opponent:

| build | tower-marking rule | towers built |
|---|---|---|
| `alice_iter14` | parity (~50% money / 50% paint) | **6** |
| `alice_i17c` | always money | **12** |
| `alice_i17a` | money when ally towers are ≥50% paint-full | **12** |

**Exactly double.** The paint-marked half of the ruins is not merely built more
slowly — it is **completely wasted**. A soldier marks the ruin as a paint tower,
paints toward that pattern, and the tower is never completed; the ruin is then
occupied by a mark and produces nothing for the rest of the game.

### Why this matters more than the iteration it came from

Tower count is this lineage's measured master variable — every accepted iteration
works by raising it. **This bug has been halving it since iteration 0.** It is
also the same *shape* as the defect the tournament exposed: a cap on tower count
that self-play could never reveal, because both sides threw away the same half.

It also re-frames the whole session's economy work. The 4,885 idle tower paint,
the pinned treasury, the "production mix" hypothesis — all of it was reasoning
about the *balance* between two tower types when in truth **only one type has ever
existed in an alice game.** Iteration 16's chip-gate hypothesis and iteration 17's
mix hypothesis were both built on a premise that was never true.

### What is NOT yet known, stated plainly

I have proved the paint-marked ruins are wasted. I have **not** yet found *why*
`completeTowerPattern(LEVEL_ONE_PAINT_TOWER, ...)` never succeeds — whether the
mark is refused, the secondary-colour paint is applied wrongly, or the completion
call is mis-ordered. That diagnosis is a separate step and I am not going to guess
at it in the log. What is established is empirical and sufficient to act on: the
paint branch produces nothing, and removing it doubles tower count.

**Evaluation launched**: run `20260907-043612`, `BOT=alice_iter14
OPPONENTS="alice_i17a alice_i17c" NMAPS=12`, 48 games. `alice_i17c` is the blunt
fix (always money); `alice_i17a` is the self-calibrating rule, which on current
evidence degenerates to nearly the same thing because the paint branch is dead.
Gate as pre-registered: H2H > 50% judged in games over the mirror null, no
unresolved swept losses, and the mechanism gate is **tower count must rise**.

## Iteration 17 — RETRACTED. There was no latent bug; the "census" was a
## single-map artifact, and the retraction produces a real result in its place

The previous entry claimed alice had never built a paint tower, that the parity
rule wasted half of every map's ruins, and that forcing MONEY doubled tower
count. **All three claims are false.** Here is the diagnosis I said I would not
guess at.

### 1. The engine does not block paint towers (verified against jar 3.1.0)

`LEVEL_ONE_PAINT_TOWER` and `LEVEL_ONE_MONEY_TOWER` differ in **exactly two
fields**: `paintPerTurn` 5 vs 0 and `moneyPerTurn` 0 vs 20. Both are moneyCost
1000, paintCost 0, health 1000, capacity 1000, cooldown 10, actionRadius^2 9,
attack 20/AoE 10. `assertCanCompleteTowerPattern` and `markTowerPattern` apply
identical gates to both, and `markPattern` writes markers to all 25 tiles for
either type. **No engine asymmetry exists.** Full decode of all four patterns
and the complete gate list are now in `RULES.md`.

### 2. The bug was in my *measurement*, not my code: gridworld has no odd ruins

I scanned the ruin coordinates of all 75 official maps out of the engine jar's
`.map25` resources. Across the corpus: **732 even-parity ruins, 642 odd**. But
per map the split varies, and **exactly three maps have no odd-parity ruin at
all: `gridworld` (21/21), `Filter` (5/5), `Snowman` (6/6)**.

`alice_iter14`'s rule is `((ruin.x+ruin.y)&1)==0 ? MONEY : PAINT`. **On
gridworld it selects MONEY for every ruin on the map.** "Alice never built a
paint tower" was a tautology on the one map I measured it on. The instrumented
build `alice_pdiag` emitted 22,092 census lines on gridworld and **not one had
`want=PAINT`** — the paint branch was never *reached*, so of course it never
completed anything.

### 3. The "doubling" was a side asymmetry, reproduced with identical code

`alice_pdiag` vs `alice_iter14` on gridworld — `alice_pdiag` is `alice` plus an
indicator string, so on this map the two builds are behaviourally identical:

```
12 SPAWN (T1,MONEY_TOWER)
 6 SPAWN (T2,MONEY_TOWER)
```

**The exact 12-v-6 I attributed to forcing MONEY, reproduced by byte-equivalent
code on both sides.** It is positional. I compared two arms across teams on one
map with no mirror control — the precise failure the mirror-null discipline
exists to prevent, and I had the tool sitting in `tools/mirror_null.txt`.

The pattern machinery works fine, incidentally: close-range census lines read
`mk=24 mkbad=0` (all 24 non-centre tiles marked, none mis-marked) with `ok`
climbing one tile per turn. Nothing was ever broken.

### 4. Paint towers get built normally wherever the branch is live

Mirror `alice_pdiag` vs `alice_pdiag` on two odd-ruin maps:

| map | odd ruins | T1 money / paint | T2 money / paint |
|---|---|---|---|
| `box` | 6 of 8 | 1 / **4** | 1 / **2** |
| `UnderTheSea` | 16 of 23 | 4 / **8** | 3 / **8** |

### 5. The evaluation was right, and splitting it by parity makes it decisive

Run `20260907-043612` (48 games, baseline `alice_iter14`) finished before the
session died. `alice_iter14` beat `alice_i17a` **13/24** and `alice_i17c`
**17/24** — the "blunt fix" scored **29%**. Both candidates rejected.

`alice_i17c` (always MONEY) differs from `alice_iter14` *only at odd-parity
ruins*, so the run contains its own arm-to-arm identity check. On the two
all-even maps in the sample the two builds are the same program:

| map | odd ruins | iter14 record vs i17c |
|---|---|---|
| `Filter` | 0 of 5 | 1/2 — one win per side (self-mirror) |
| `Snowman` | 0 of 6 | 1/2 — one win per side (self-mirror) |

Exactly the mirror null, which validates the split. Dropping those four
degenerate games, on the **10 maps where the change is live**:

**`alice_iter14` 15/20 (75%) vs `alice_i17c` 5/20 (25%).**

So the conclusion inverts. The paint branch is not waste — **it is load-bearing,
and deleting it costs 75–25.** Money-only starves the paint economy that every
soldier's 200-paint output depends on, which is consistent with iteration 5's
absorbing-state finding.

### Closed-directions ledger
| direction | closed by | can re-open if |
|---|---|---|
| Forcing all ruins to MONEY (drop the paint branch) | iteration 17 retraction: **5/20 (25%)** on the 10 maps where the branch is live, with the 4 all-even-map games discarded as a verified self-mirror | never on this evidence. A *mix* rule that still builds paint towers is a different question and remains open. |
| "alice has never built a paint tower" as a premise | refuted: 4/8 and 8/8 paint towers built in mirrors on `box` and `UnderTheSea` | — |

**Cost of the error: one 48-game run, three debug matches.** What it bought is
larger than the iteration: a corpus-wide map fact, the complete engine decode of
all four patterns, and a demonstrated 75–25 value for a feature I was about to
delete.

## Iteration 18 — PRE-REGISTERED: dose the money/paint tower mix, on a ladder
## whose middle rung is byte-identical to the baseline

**Area**: production mix (re-opened legitimately — iteration 17's retraction
replaced a false premise with a measured one).

### Why this is now a live question

The retraction established that at the money-only extreme the mix is worth
**75–25**. That is an enormous effect for one branch, and it says the mix is a
strong lever — but it says nothing about which *direction* from 53% is better,
because I have only measured one endpoint. A single endpoint is exactly what
Measurement doctrine #2 warns against; the curve is what carries the evidence.

An arithmetic prior, stated before the run so it can be wrong: a soldier costs
**250 chips + 200 tower paint**. L1 income is **20 chips** per money tower per
turn vs **5 paint** per paint tower per turn. A purely spawn-limited economy
therefore balances at roughly **1 money tower per 3 paint towers**, and tower
completions (1000 chips each) pull that back toward money by an amount I cannot
compute a priori. So the prior favours *more paint than 53%*, i.e. a peak at
K=1 — but iteration 16 taught me that chips and paint trade in ways the naive
ratio misses, so this is a prior, not a prediction.

### The ladder, and why K=2 is the zero arm

`p = (x+y)&1` (alice_iter14's existing bit), `q = ((x>>1)+(y>>1))&1`:

| arm | rule | corpus money-share | degenerate maps |
|---|---|---|---|
| K=0 | always PAINT | 0.00 | 75 (by construction) |
| K=1 | money iff `p==0 && q==0` | 0.26 | 4 |
| **K=2** | **money iff `p==0`** — **`alice_iter14` exactly** | **0.53** | 4 |
| K=3 | money iff `p==0 \|\| q==0` | 0.77 | 7 |
| K=4 | always MONEY (`alice_i17c`, already measured) | 1.00 | 75 |

K=2 *is* the baseline, byte for byte, so the zero arm has **zero variance** and
every rung sits on the same parity backbone — the dose changes the mix and
nothing else.

**Reachability was checked corpus-wide BEFORE the run this time**, which is the
whole lesson of the retraction. I also tested four other candidate hashes
(`(x+3y)&3`, `(x/2+y/2)&3`, a multiplicative hash, a mixed one): every one of
them is degenerate — money-share 0.00 or 1.00 — on at least one map, so no
position-keyed mix rule is map-neutral. The named degenerate maps for K=1/2/3
are recorded above so no arm gets traced on one by accident.

### Pre-registered gates
- **Accept**: H2H vs `alice_iter14` **> 50%**, judged in games over the mirror
  null, and a dose curve that is **not flat** (iteration 16 died on flatness).
- **Mechanism gate**: for any arm that beats the baseline, mean soldier count in
  r100–r400 must **rise**, and team tower-paint stock must **not** collapse to 0
  (iteration 5's absorbing state).
- **Falsifier**: a flat curve across 0.00→0.77 says the mix is not the
  constraint and closes the direction, exactly as iteration 16 closed the chip
  gate.

**Launched**: run `20260907-134502`, `BOT=alice_iter14
OPPONENTS="alice_i18k0 alice_i18k1 alice_i18k3" NMAPS=12`, 72 games.

## Instrument change — `alice_flood`, the spender archetype my pool has never had

**This is a process change, not an iteration.** Every peer I own descends from
my own code, so every one of them carries the same 1450-chip spawn stall, and
**no instrument I have can see what that stall costs** — the self-referential
blind spot, and Measurement doctrine #4's representativeness clause.

The tournament replay `alice` vs `bob` on Paintball makes it concrete:

| round | alice $ | alice soldiers | alice twPaint | bob $ | bob soldiers |
|---|---|---|---|---|---|
| 50 | 1150 | 4 | 910 | **0** | **8** |
| 75 | 900 | **1** | **1905** | 750 | **8** |
| 100 | 1400 | 2 | **2205** | 1200 | **11** |

Alice's army collapses to one soldier at r75 while its towers hold 1,905 paint
and its treasury sits just under the reserve; bob runs its treasury to zero and
fields eight. Alice's coverage peaks at 370‰ on r75 and **falls** to 254‰;
bob's climbs to 686‰ and wins on MAJORITY_PAINTED at r383.

`alice_flood` = `alice_iter14` with `CHIP_RESERVE = 0` and nothing else changed.
It is **frozen** and goes in `progress/roster_extra.txt` as a permanent
yardstick. It is not a candidate and will never be retuned; its whole value is
that it poses a behaviour my lineage never poses.

### Iteration 6 (paint refill) — re-open CONSIDERED and RE-CLOSED, without a run

The ledger permits re-opening the refill "if paint becomes non-binding". The
Paintball trace looked like exactly that (2,205 idle tower paint). I checked the
trigger frequency across four games before building anything:

| game | T1 twPaint ≥1000 | starvation deaths per sample |
|---|---|---|
| gridworld mirror | 985/2000 | **0** |
| box mirror | 1038/2000 | **0** |
| UnderTheSea mirror | 1943/2000 | 0–2 |
| Paintball vs bob | **7/18** — drains to 100–150 after r300 | 0–1 |

Two reasons this fails its own re-open condition. Tower paint is abundant **in
self-play only** — against a real opponent it drains to 100–150, which is where
the refill would compete with spawning exactly as iteration 6 measured. And
**starvation deaths are now 0–2 per sample**, not the 65–100% of deaths that
motivated iteration 6 at all; the premise has decayed. Re-closed, no run spent.

## Tournament `20260907-1300` — the external verdict on iterations 12 and 14

Both runs complete over the same 75 maps, so the deltas are real.

| | 0100 | 1300 | delta |
|---|---|---|---|
| alice overall | 35.3% | **38.0%** | **+2.7** |
| alice vs bob | 4.7% | **7.3%** | **+2.7** |
| alice vs carol | 66.0% | **68.7%** | +2.7 |
| swept maps alice–bob | 0 – 68 | **1 – 65** | +1 / −3 |

The navigation work is **real and small**. Three independent quantities move
together in the same direction — overall, the head-to-head, and the swept count
on both sides of it — which is the report's own criterion for signal rather than
noise. That is worth having, and it is nowhere near enough: bob still sweeps 65
of 75 maps against me.

**This is the instrument that matters.** My gauntlet says `alice_iter14` beats
its own predecessors; the tournament says it wins 7.3% of games against an
independent lineage. Only the second number is about strength.

## Iteration 19 — diagnosis, and the fix I discarded before running it

**Area**: tower expansion (the master variable — bob has 12 towers to my 5 at
r150 on gridworld, and 14 to my 6 at r250).

### The measurement

A soldier holds **200 paint** and each paint action costs **5**, so a soldier
has **40 actions in its whole life**. A tower pattern is **24 tiles = 120
paint**, plus 25 to mark. Instrumented census, `alice_iter14` self-play:

| map | soldier paint while travelling (median) | **soldier paint standing AT a ruin** | frac ≤30 |
|---|---|---|---|
| gridworld | 71 | **median 18** | 55.6% |
| box | 52 | **median 20** | 56.4% |
| UnderTheSea | 135 | **median 29** | 50.8% |

**A soldier arriving at a ruin has roughly four paint actions left against a
24-tile job.** No soldier can finish a pattern; towers only complete when enough
soldiers each donate three or four tiles. That is the tower-count gap.

### The fix I built and then discarded on the reachability pre-check

I built three arms (`alice_i19r60/120/185`) that withhold opportunistic painting
**while travelling to a ruin**, keeping a reserve for the pattern. Then I ran the
generality check across the three maps before launching, and it kills the design:

| map | ruin-targeted turns spent travelling (d>2) | spent at the ruin (d≤2) |
|---|---|---|
| gridworld | 18,422 (83%) | 3,670 |
| box | 244 (**12%**) | 1,804 |
| UnderTheSea | 639 (**10%**) | 5,838 |

The travel phase dominates on gridworld and is **near-absent on the other two**.
A reserve keyed on travelling would be **dead code on two maps out of three** —
the same shape of error as the iteration 17 retraction, caught this time before
a run instead of after one. The arms stay in the tree unevaluated.

### What the census actually points at

The distribution of pattern completeness while a soldier stands at a ruin is not
smooth — it piles up short of the finish:

```
ok=14: 514    ok=18: 298    ok=19: 173    ok=22: 637    ok=24: 15
```

**637 samples sitting at 22 of 24 tiles correct, against 15 samples that ever
reach 24.** Patterns stall two tiles from done.

The geometric candidate: the soldier's ruin logic only ever calls
`tryMove(rc, toRuin)` — it walks *toward* the ruin and then stays put. A soldier
adjacent to the ruin cannot reach the pattern's far corners: its action radius²
is **9**, while a corner at ruin-offset (±2,±2) sits up to **dsq 18** away from a
soldier on the opposite side. The soldier then finds no attackable mismatch,
falls through to opportunistic painting, and burns its remaining paint on ground
tiles beside a pattern it is two tiles from completing.

**Not yet proven** — I have extended `alice_pdiag` to split each mismatching tile
into in-action-range (`in=`) and out-of-range (`out=`) and will run one match to
confirm. If stalled samples read `in=0 out=2`, the mechanism is repositioning
around the ruin, not a paint reserve, and it is reachable on every map.

## Iteration 19 — PRE-REGISTERED: the thing stalling tower patterns is ENEMY
## PAINT, and only a mopper can clear it

The out-of-range geometry guess above is **wrong**, and the data I already had
settled it without a new match. Taking every census sample where a soldier
stands at a ruin with **≥20 of 24** pattern tiles already correct, and asking
what the remaining tiles are:

| map | samples | **enemy paint** | empty | wrong ally shade |
|---|---|---|---|---|
| gridworld | 724 | **87.2%** | 10.5% | 2.3% |
| UnderTheSea | 1,714 | **78.2%** | 20.3% | 1.5% |
| box | 211 | **62.1%** | 35.1% | 2.8% |

**A soldier can never overwrite enemy paint.** `RULES.md`, engine-verified:
`soldierAttack` paints a tile only if it is empty or already ally. So a tower
pattern with one enemy tile in it is **permanently stalled for every soldier
alive**, which is exactly the 637-samples-at-22-of-24 pile-up. The soldier then
stands beside a tower it is two tiles from finishing and spends its remaining
paint on ground.

Only a **mopper** can remove enemy paint (splashers can overwrite it within r²≤2
of a splash centre, but iteration 11 closed splashers at 3/14). Alice builds
moppers — one spawn in four — and since iteration 7 they walk to the nearest
enemy paint in vision. **They have no idea which enemy paint is holding up a
tower.**

### The change — one mechanism, and it only changes a preference

`alice_i19a` (soft) and `alice_i19b` (exclusive): a mopper prefers enemy paint
lying inside the 5×5 (r²≤8) of a ruin that has no tower on it, both when
choosing which adjacent tile to mop and when choosing which tile to walk to.
When nothing is blocked the behaviour is unchanged, so the cost is bounded.

| arm | rule |
|---|---|
| zero | `alice_iter14` — nearest enemy paint, no preference |
| A | pattern-blocking tiles sort first, then by distance |
| B | if any pattern-blocking tile is in vision, ignore all other enemy paint |

### Pre-checks, all three run BEFORE building this time

- **Reachability / trigger frequency**: the blocked state is common *and
  persistent* — 724 / 1,714 / 211 samples across three maps sit at ≥20/24 with
  enemy paint in the pattern. Not a corner case.
- **Generality**: holds on all three maps, at 87% / 78% / 62%. Different
  magnitudes, same sign.
- **History**: this refines iteration 7 (purposeful moppers, accepted) rather
  than reverting it, and does not touch iteration 3's rejected "stop building
  moppers" — it makes the moppers I already build worth more.

### Pre-registered gates
- **Accept**: H2H vs `alice_iter14` **> 50%** judged in games over the mirror
  null, and a dose curve that is **not flat**.
- **Mechanism gate**: **tower count must rise**, and the census fraction
  "near-complete patterns blocked by enemy paint" must **fall**.
- **Falsifier**: tower count flat means unblocking is not what limits expansion
  and the direction closes.

**Caveat recorded in advance** (Measurement doctrine #4): the census is
self-play, so the enemy paint being measured was laid down by a bot that paints
the way I do. Against bob — who paints far more — blocking should be worse, not
better, so the direction should hold; but the *size* measured here is not
transferable.

### Sizing the prize — and it is much larger than the stall count suggested

The pile-up at 22-of-24 is only the visible tip. Counting **every** soldier turn
spent on a ruin, and asking whether that ruin's pattern contains any enemy paint
at that moment:

| map | ruin-targeted soldier turns | **with enemy paint in the pattern** |
|---|---|---|
| gridworld | 22,092 | **7,915 (35.8%)** |
| box | 2,048 | **1,594 (77.8%)** |
| UnderTheSea | 6,477 | **5,258 (81.2%)** |

On two of three maps, **four out of five soldier-turns aimed at a ruin are aimed
at a ruin no soldier can finish.** The soldier walks there, paints what it can,
and then stands beside an unfinishable pattern burning its remaining paint on
ground tiles — which is also why the median soldier at a ruin holds only 18–29
paint. The paint-budget symptom and the tower-count symptom are the same defect
seen from two sides.

This does two things. It raises the expected value of iteration 19 (moppers
unblock) considerably. And it names **iteration 20** precisely and separately:
a soldier should *deprioritise a ruin whose pattern it cannot finish* and go
find one it can — pure waste removal, the "capability preserved at zero marginal
cost" profile, and a different mechanism from iteration 19 so the two must not
be bundled.

## Iteration 18 — REJECTED, and the dose curve is single-peaked ON THE CURRENT VALUE

Run `20260907-134502`, 72 games, 12 maps both sides, `alice_iter14` as the zero
arm (K=2, byte-identical by construction). Combining with `alice_i17c` (K=4)
from run `20260907-043612`:

| K | corpus money-share | candidate score | note |
|---|---|---|---|
| 0 | 0.00 | **1/24 (4.2%)** | always paint |
| 1 | 0.26 | **5/24 (20.8%)** | |
| **2** | **0.53** | **12/24 (50%)** | **`alice_iter14`, by definition** |
| 3 | 0.77 | **6/22 (27.3%)** live maps | |
| 4 | 1.00 | **5/20 (25.0%)** live maps | from run 043612 |

**The curve is single-peaked and the peak is the value I already have.** It
falls off monotonically in *both* directions — 4.2% and 20.8% below, 27.3% and
25.0% above. Measurement doctrine #2 calls a curve that peaks in the middle
stronger evidence than any single point; this one peaks on the incumbent, which
is the cleanest possible "leave it alone".

The arm-to-arm identity check held again: `Filter` is a self-mirror cell for K=3
(0 ruins decided differently) and returned exactly **1/2**, one win per side.

### My arithmetic prior was refuted, and that is the useful part

I pre-registered the reasoning that a spawn costs 250 chips + 200 tower paint
against L1 incomes of 20 chips vs 5 paint, so a spawn-limited economy should
want ~3 paint towers per money tower — i.e. a peak nearer K=1. The measured
peak is at 53% money and K=1 scores **20.8%**. The naive income ratio is simply
not what sets the optimum: tower completions cost 1000 chips each, and a paint
tower that cannot be paid for is worth nothing. Chips buy *towers*, and towers
are the master variable.

Also note K=0 at **4.2%** — worse than K=4's 25%. Building *only* paint towers
is far more damaging than building only money towers. Paint is useless without
the chips to convert it.

### Closed-directions ledger
| direction | closed by | can re-open if |
|---|---|---|
| Changing the money/paint tower mix ratio | iteration 18: five-point dose 0.00→1.00 scoring 4.2 / 20.8 / **50** / 27.3 / 25.0, single-peaked on the incumbent | the *mechanism* changes so the mix is no longer set per-ruin by geometry (e.g. a rule that reads the actual treasury/paint state). The ratio itself is settled; only a different decision rule could re-open it. |
| The "production mix" thread opened in iterations 16 and 17 | same | closed. Three iterations circled this; it is now measured with a curve. |

**Bytecode check** (Phase 0 #6, owed on every full evaluation): max
**3,782 of 17,500**, zero overruns, zero near-misses across the census game.
Ample headroom for iteration 20.

### Correction to my reading of tournament `20260907-1300`

The report gained a section after I first read it, and it corrects me: wins are
**conserved** across the three lineages (they sum to 450), so my +2.7 means
*improved relative to the other two*, not *got better*. Absolute strength is
what the frozen roster measures. My roster is overdue — last extended around
iteration 13 — and TRAINING_ALGORITHM §5b requires it on a schedule rather than
on suspicion. Queued behind iteration 19's evaluation.

## Iteration 19 — mechanism VERIFIED (class 2), evaluation running (`20260907-141653`)

`alice_i19diag` (arm A plus the census) vs `alice_iter14`, gridworld and
UnderTheSea. Both won. **Both are read against the mirror null, not raw** —
gridworld's null with byte-identical code is T1 12 towers to T2 6, which is
exactly the trap the iteration 17 retraction was about.

| | gridworld base | gridworld cand | UnderTheSea base | UnderTheSea cand |
|---|---|---|---|---|
| ruin-targeted soldier turns | 22,092 | **18,604** | 6,477 | **3,130** |
| % of them with enemy paint in the pattern | 35.8% | 36.1% | 81.2% | 81.4% |
| **near-stall samples (≥20/24 done, at the ruin)** | 724 | **358** | 1,714 | **465** |
| enemy share of the remaining tiles | 87.2% | **79.0%** | 78.2% | **73.2%** |
| median soldier paint at a ruin | 18 | **35** | 29 | 26 |
| towers built (T1) | 12 *(null)* | **13** | 12 *(null)* | **13** |

**The pre-registered gate passes, and one number in it is more interesting than
the gate.** The blocked *fraction* is dead flat on both maps (35.8→36.1,
81.2→81.4): moppers do not reduce how often a pattern contains enemy paint,
because it is an equilibrium — the opponent repaints as fast as we clear.

What changed is **throughput through that state**. Near-stall samples fall by
half or better (724→358, 1,714→465) and total ruin-targeted soldier turns fall
16% and 52%. Soldiers are getting unstuck and moving on. Tower count rises by
exactly **+1 over the null on both maps** — the right sign, and small.

**Recorded before the run resolves so it cannot be rationalised afterwards**:
+1 tower per map is a modest effect and I expect a modest H2H. The honest
prediction is a near miss rather than a clean accept.

**Launched**: run `20260907-141653`, `BOT=alice_iter14 OPPONENTS="alice_i19a
alice_i19b alice_flood" NMAPS=12`, 72 games. `alice_flood` rides along to buy
its first roster point — `alice_iter14` vs the spender archetype has never been
measured, and the shared map sample makes the comparison exact.

## Iteration 20 — PRE-REGISTERED and built, held until iteration 19 resolves

**Area**: tower expansion (same area as 19, different mechanism — 19 makes
moppers unblock patterns, 20 stops soldiers committing to patterns that are
blocked. They must not be bundled, and if 19 accepts, 20 is rebuilt on the new
baseline before it is run.)

**Premise, already measured**: 35.8% / 77.8% / 81.2% of *all* ruin-targeted
soldier turns (gridworld / box / UnderTheSea) are spent on a ruin whose pattern
holds enemy paint the soldier can never overwrite. On two maps of three, four in
five soldier-turns aimed at a ruin are aimed at one that cannot be finished.

**Change**: a soldier adds `BLOCK_PENALTY` to the squared distance of any ruin
whose 5×5 currently holds enemy paint, and picks the lowest score. Ruins are
sensed within vision (r²≤20), so the dose spans mild preference to strict
exclusion.

| arm | `BLOCK_PENALTY` | effect |
|---|---|---|
| zero | 0 | `alice_iter14` — `patternBlocked` is never called, byte-identical |
| A | 5 | mild |
| B | 10 | moderate |
| C | 25 | exceeds the maximum in-vision distance: strictly prefer unblocked |

**Known bias, recorded in the code and here rather than discovered later**: a
distant ruin whose 5×5 lies partly outside vision cannot be tested and so reads
as unblocked. A large penalty therefore biases toward ruins we merely cannot see
yet. That is precisely why the ladder is small and why the exclusive rung is
measured rather than assumed safe.

**Pre-registered gates**: H2H vs the then-current baseline > 50% over the mirror
null; mechanism gate = the fraction of ruin-targeted soldier turns spent on
blocked ruins must **fall** (this is the metric iteration 19 left dead flat, and
20 attacks it directly rather than through an equilibrium); falsifier = a flat
dose curve closes the direction.

## Iteration 21 — PRE-REGISTERED and built: the §5b PAIRWISE ablation, on the
## pair today's measurements nominate

**This is not a candidate. It is an audit**, run because the frozen roster —
the only instrument that sees lineage drift — is showing thin and possibly
falling margins against my own recent ancestors:

| frozen opponent | `alice_iter14` win% |
|---|---|
| `alice_iter0` | 95.8% |
| `alice_iter1` | 100% |
| `alice_iter4` | 91.7% |
| `alice_iter7` | **62.3% → 58.2%** (two runs) |
| `alice_iter12` | **54.2%** |

Saturated against distant ancestors, barely above even against recent ones, and
the `iter7` line is pointing down. Two points on different map samples is not
proof of drift, but §5b is explicit that a chain of individually-positive
accepts can walk downhill and that only pairwise ablation can see it.

### The nominated pair, and why this one

**Iteration 1 (soldiers spend idle actions painting) × iteration 12/14 (wander
became ballistic, `WANDER_RUN` 8.5 → 25).**

Each is fine alone and they fight over the same 200-paint tank. Iteration 1 was
accepted when soldiers barely travelled; iteration 12 then made them travel far,
and iteration 1 paints the whole way. Today's census is the evidence: a soldier
standing at a ruin holds a **median of 18 paint** against a 120-paint pattern.
This is exactly §5b's shape — an interaction invisible to both accept gates,
because each was measured against a baseline that already carried the other.

**Stated as a caution, per §5b's own warning**: a heuristic *nominates* a pair,
it is never evidence about one, and the sign of an interaction is not
predictable from its shape. I am not predicting the outcome.

| arm | iteration 1 idle painting | iteration 12 ballistic wander |
|---|---|---|
| zero (`alice_iter14`) | ON | ON (25) |
| `alice_i21a` | **OFF** | ON (25) |
| `alice_i21b` | ON | **OFF** (5 + rnd(8)) |
| `alice_i21c` | **OFF** | **OFF** |

Both features are gated rather than deleted, so each arm's diff against
`alice_iter14` is exactly one switch. The 2×2 is the point: single-feature
ablation would exonerate both halves of a destructive pair.

**Reading rule, fixed in advance.** Let the four scores be Z, A, B, C. The
interaction is `C − A − B + Z`. A large positive value means the two features
are substitutes I am paying for twice; a large negative value means they are
complements and the pair is doing real work together. **Only the interaction
term is interpreted** — the main effects are ordinary ablations and are already
covered by the accept gates that installed them.

Queued behind iteration 19 and 20; this is an audit and does not block the loop.

### Iteration 19 arm B — predicted failure mode, recorded before the result

`alice_i19b` is the exclusive rung: if any pattern-blocking enemy tile is in
vision, every other enemy tile is ignored. Two ways that can misfire, written
down now so neither can be invented afterwards as an explanation:

1. **Unreachable blocker.** A blocking tile visible but behind a wall keeps
   `anyBlocking` true forever, so the mopper walks at it and ignores all other
   enemy paint. `tryMove`'s slide keeps it from freezing outright, but it can
   oscillate against the obstacle. Arm A has no such failure mode because a
   blocked tile only reorders the preference, it never suppresses the fallback.
2. **Erasure withdrawn from the contest.** Iteration 5's starburst trace showed
   coverage is a *contested* stock and that a build which paints twice as much
   still loses to one that erases twice as much. Sending every mopper to ruins
   removes them from that contest.

If arm B underperforms arm A, these are the two candidate causes and they are
distinguishable in a trace: (1) shows as moppers with near-zero mop actions and
high movement, (2) as a fall in team unpaint actions per round with moppers
still busy.

### Iteration 19 — arm A is in at 15/24, and the decision rule is fixed HERE,
### before arm B lands

`alice_i19a` beats `alice_iter14` **15/24 (62.5%)**. Exact one-sided binomial
against p=0.5:

| record | win% | p |
|---|---|---|
| 14/24 | 58.3% | 0.271 |
| **15/24** | **62.5%** | **0.154** |
| 16/24 | 66.7% | 0.076 |
| 17/24 | 70.8% | 0.032 |

**p = 0.154 is not significant**, and it lands exactly where iteration 1's
recorded noise floor put it: *"treat 13–15/24 as within noise of 50%."* The
prediction I wrote down before the mechanism run — "a modest effect, expect a
near miss rather than a clean accept" — is what happened. I am not promoting
15/24 by forgetting my own floor.

**Decision rule, fixed before arm B is visible:**

- **ACCEPT** only if *all* hold: arm A ≥ 15/24; **arm B also > 12/24** (the two
  doses of one mechanism agree in direction, which per Measurement doctrine #2
  is stronger than either point alone); arm A's **swept wins > swept losses**
  (swept maps are immune to spawn advantage); and no one-directional regression
  is left unresolved.
- **NEAR MISS → refine** if arm B is at or below the null while arm A is up. One
  dose up and one flat is a single noisy point dressed as a curve.
- **REJECT** if both arms are at or below the null.

Pooling the two arms is *not* the test — they are different doses, not
replicates — but for reference 30/48 would give p = 0.056 and 32/48 p = 0.015.

## Iteration 19 — ACCEPTED (snapshot `src/alice_iter19/`), arm A

Run `20260907-141653`, 12 maps both sides, `alice_iter14` as baseline.

| arm | rule | H2H | swept-WIN | swept-LOSS | split |
|---|---|---|---|---|---|
| zero | `alice_iter14` | 12/24 by definition | 0 *(mirror null)* | 0 *(null)* | 12 |
| **A** `alice_i19a` | prefer pattern-blocking enemy paint | **15/24 (62.5%)** | **3** | **0** | 9 |
| B `alice_i19b` | ignore all other enemy paint | **15/24 (62.5%)** | **3** | **0** | 9 |

**Every condition of the decision rule I fixed before arm B was visible is met**:
arm A ≥ 15/24 ✓, arm B > 12/24 ✓, arm A swept wins > swept losses ✓ (3 > 0), no
unresolved one-directional regression ✓ (zero swept losses).

### The swept count is what carries this, not the 62.5%

15/24 alone is p = 0.154 — inside my own recorded noise band, and I said so
before arm B landed. What decides it is the swept-map column. Swept maps are
won from **both sides**, so they are immune to spawn advantage, and the mirror
null for this baseline is **0 swept wins and 0 swept losses with zero
variance**. Three swept wins against zero swept losses, reproduced
**identically by two independent doses**, is a one-directional result that the
raw win rate understates. Per Measurement doctrine #7, a one-directional diff
concentrated this way is a real causal effect rather than churn.

### The dose curve is a plateau, and that is why arm A is the rung taken

12 → 15 → 15. This is **not** iteration 16's flatness: that was flat *at the
null* and said the parameter was dead. This is flat *above* the null, which says
the mechanism saturates immediately — the soft preference already captures the
entire benefit and the exclusive rung adds nothing.

**Arm A is therefore the correct rung at equal measured value**, because arm B
additionally carries the two failure modes I recorded in advance (an unreachable
blocking tile capturing every mopper; moppers withdrawn from the coverage
contest). Neither fired on these 12 maps — but paying for exposure that buys
zero measured benefit is not a trade worth making. Prefer the smaller change.

### Mechanism, restated with the outcome known

The blocked *fraction* did not move (35.8→36.1, 81.2→81.4) and was never going
to: it is an equilibrium the opponent replenishes. What moved is throughput —
near-stall samples halved (724→358, 1,714→465) and total ruin-targeted soldier
turns fell 16% and 52% — and that converted to +1 tower per map over the null
and 3 swept maps. Distilled into `LEARNINGS.md` as a rule about pre-registering
rates rather than levels for contested quantities.

**Bytecode**: mopper max 1,898 → 3,385 of 17,500; zero overruns, zero
near-misses.

**Archived replay**: `replays/iter19_alice_iter14_UnderTheSea_A.bc25` — the
instrumented mechanism win, chosen over a gauntlet replay because it carries the
census that shows *why* it works.

**Still in flight in the same run**: `alice_flood` (22 games) for its first
roster point against `alice_iter14`. That measures the *old* baseline against
the new archetype, so it is a separate instrument reading and gets its own
commit when the run collates.

## `alice_flood` — the archetype's first roster point, and it says the opposite
## of what I built it to show

Run `20260907-141653`, same 12-map sample as iteration 19's arms, so the
comparison is exact.

**`alice_iter14` beats `alice_flood` 15/24 (62.5%), swept 5–2.**

I built `alice_flood` (`CHIP_RESERVE = 0`, nothing else changed) because the
Paintball tournament replay showed bob at $0 with 8 soldiers on round 50 while
alice sat at $1,150 with 4 and collapsed to 1 by round 75. The implied story was
that my 1450-chip stall is a handicap no lineage-only instrument could see.

**Measured, that story is wrong.** Removing the reserve entirely costs 12.5
points against the build that keeps it. The reserve is worth something real, and
this is a *third* independent line of evidence agreeing with iteration 16's flat
dose (1450 / 1250 / 1000 all tied) and iteration 18's finding that chips buy
towers and towers are the master variable. Spending chips down to zero does not
reproduce what bob is doing — bob is at $0 *and* fielding eight soldiers, which
means bob's chips are arriving faster, not merely being spent sooner. **The
treasury curve was a symptom I mistook for a cause.**

The archetype keeps its place in the roster regardless, and is now the more
useful for it: at **37.5%** from its own side it is a genuine *peer* by the
classification rule (30–90%), not a benchmark, so it can resolve future changes.
It is frozen and will not be retuned.

### Closed-directions ledger
| direction | closed by | can re-open if |
|---|---|---|
| Removing or lowering `CHIP_RESERVE` | now three independent measurements: iteration 16's flat dose across 1450/1250/1000; iteration 18's dose showing chips buy towers; and `alice_flood` at **37.5%** with the reserve deleted outright | a change first raises chip *income* — the reserve is a symptom of income, not the constraint itself |
| "The treasury sitting under the gate is why my army is small" | same — the spender fields no more army | — |

## Reachability scan for a future iteration 22 — and gridworld would have hidden
## this one too, in the same direction

Fraction of `alice_iter14` soldier turns with **no ruin anywhere in vision**
(soldiers only ever target ruins from `senseNearbyRuins`, vision r²=20, and have
no memory of any ruin they have walked past):

| map | ruins | soldier turns | with a ruin target | **blind wander** |
|---|---|---|---|---|
| gridworld | 21 on 31×31 | 29,490 | 22,092 (74.9%) | **7,398 (25.1%)** |
| box | 8 on 31×31 | 26,458 | 1,152 (4.4%) | **25,306 (95.6%)** |
| UnderTheSea | 23 on 45×45 | 58,457 | 3,342 (5.7%) | **55,115 (94.3%)** |

**On normal-density maps a soldier cannot see a ruin 94–96% of the time.** On
gridworld — 21 ruins on a 31×31 board, the densest map in the corpus — it is
25%.

This is the coordinator's generalisation landing a second time, in the same
direction and on the same map. Had I sized "soldiers cannot find ruins" on
gridworld, I would have called it a 25% problem and probably passed on it. It is
a 95% problem. **gridworld is not merely parity-degenerate; it is
density-degenerate, and both distortions make a real defect look small.** I am
treating it as disqualified for sizing any ruin-related quantity, and the check
is now cheap: `tools/mapdata/ruin_parity.txt` carries ruins-per-map alongside
parity.

**Not yet a candidate.** High blind-wander is necessary but not sufficient — it
only pays if there are unclaimed ruins the soldier has *already seen and walked
away from*. Sizing that needs memory instrumentation which does not exist yet,
so the honest status is: the trigger is verified common, the payoff is not yet
verified. That instrumentation is the first step of iteration 22, before any
mechanism is written.

**Deliberately not consulted**: another lineage's commit subjects are visible in
`tournaments/*/report.md`, and one of them names this area. A different bot's
result on its own navigation is not evidence about mine, and designing around it
would be borrowing a conclusion I have not earned. This will be measured from my
own traces or not at all.

## Iteration 20 — mechanism VERIFIED, and it moves the number iteration 19 could
## not. Evaluation running (`20260907-145851`)

`alice_i20diag` (penalty 10 + census) vs `alice_iter19`, gridworld and
UnderTheSea. Both won.

| build | map | ruin-targeted turns | **% blocked** | median paint at ruin |
|---|---|---|---|---|
| `alice_iter14` | gridworld | 22,092 | 35.8% | 18 |
| `alice_iter19` | gridworld | 18,604 | 36.1% | 35 |
| **`alice_i20` p10** | gridworld | **13,525** | **25.7%** | 33 |
| `alice_iter14` | UnderTheSea | 6,477 | 81.2% | 29 |
| `alice_iter19` | UnderTheSea | 3,130 | 81.4% | 26 |
| **`alice_i20` p10** | UnderTheSea | **1,346** | **62.0%** | 29 |

**The pre-registered gate passes on both maps**: −10.4 and −19.4 points on the
one metric iteration 19 left dead flat. That is the design working exactly as
argued — 19 raised *throughput* through an equilibrium it could not shift, 20
declines to pay for the equilibrium at all, so the level itself moves. Total
ruin-targeted soldier turns fall a further 27% and 57% on top of iteration 19's
reduction: soldiers now spend their turns on ruins they can actually finish.

### The caveat, recorded BEFORE the evaluation returns

**Tower count does not rise.** Against the mirror null:

| map | null | `alice_iter19` | `alice_i20` p10 |
|---|---|---|---|
| gridworld | T1 12 | 13 | **13** |
| UnderTheSea | T1 12 / T2 11 | 13 / 10 | **12 / 11 — exactly the null** |

So iteration 20 removes a large, real, measured waste and, on this evidence,
**converts none of it into towers**. That is precisely the failure shape the
algorithm names — *"metrics that improve without converting to wins"*, five
mechanism-verified damage increases converting to nothing in 2026 — and I am
naming it now rather than after the result.

**Honest prediction, recorded in advance**: a large mechanism move with a flat
tower count most often lands at or near the null. I expect a reject or a thin
near miss, and if the H2H does come in high I will treat the gap between "waste
removed" and "towers gained" as the thing to explain rather than as a bonus.

The saved soldier turns have to go *somewhere*, and the candidate explanation is
that they go into ground painting — which is coverage, the actual win condition,
and would show up as a win without a tower gain. That is checkable in the same
census and is the first thing I will look at.

**Launched**: run `20260907-145851`, `BOT=alice_iter19 OPPONENTS="alice_i20p5
alice_i20p10 alice_i20p25" NMAPS=12`, 72 games, alongside iteration 21's audit.

### A confound I nearly read as a finding (coverage check, iteration 20)

I went to test my own pre-registered explanation — that iteration 20's saved
soldier turns go into ground painting — by comparing coverage differentials.
The raw numbers looked alarming: on UnderTheSea the T1−T2 coverage gap at r2000
is **+148 for the iteration 19 game and only +46 for the iteration 20 game**,
and at r1500 the iteration 20 game is actually **behind at −1**.

**That comparison is invalid and I am recording it rather than quietly dropping
it.** The two games have *different opponents*: `alice_i19diag` played against
`alice_iter14`, while `alice_i20diag` played against `alice_iter19` — which is a
stronger bot, because iteration 19 was accepted in between. A shrinking
differential against a stronger opponent says nothing about the candidate. This
is the cross-run comparison trap in a new costume: I changed the baseline and
then compared across the change.

What *is* valid is within-game: `alice_i20diag` leads `alice_iter19` on coverage
at every checkpoint on gridworld (+236 / +259 / +251 / +234) and is essentially
level on UnderTheSea until the very end (+2 / +3 / −1 / +46). So on UnderTheSea
iteration 20 wins while barely out-painting — consistent with a thin effect, and
consistent with the flat tower count.

**The coverage explanation is therefore neither confirmed nor refuted here.** To
test it properly I would need a same-opponent pair, which the 72-game H2H
against `alice_iter19` supplies directly. Waiting for it rather than reading
tea leaves from two games.

### Iteration 20 — decision rule fixed BEFORE `p10` and `p25` are visible

`p5` is in at **12/24 — exactly the mirror null.** The mildest dose removes a
large measured waste (blocked fraction −10.4 and −19.4 points) and converts it
into precisely zero games.

The coordinator's note makes explicit what my own pre-registration implied, and
I am binding myself to it here rather than after the numbers:

> **The "tower count does not rise" caveat OUTRANKS the win rate.** If `p10` or
> `p25` returns a thin positive, that is not an accept. "Improves a metric
> without converting" is the shape this project has been fooled by repeatedly —
> five mechanism-verified damage increases converting to nothing in 2026, and
> my own iteration 16 chip-gate before that.

Concretely, for iteration 20 to be accepted it must clear **both**:

1. **≥ 16/24** on at least one dose — the point where the exact binomial gives
   p ≤ 0.076, i.e. outside the 13–15 band my own noise floor calls noise. A
   15/24 does **not** qualify here, even though it did for iteration 19,
   *because iteration 19 had 3–0 swept maps against a zero-variance null to
   carry it and iteration 20 has a flat tower count arguing against it.*
2. **A mechanism-to-outcome link that is not merely the win rate** — either
   tower count rising over the null, or swept maps clearly one-directional.

Anything less is a **reject**, and the direction closes with the waste measured
and documented: *soldiers stop wasting turns on unfinishable ruins, and it buys
nothing.* That is a genuinely useful negative — it says the wasted turns were
not the binding constraint, which redirects effort to what is.

**Falsifier for the whole thread, stated plainly**: if removing 27–57% of
ruin-targeted soldier turns changes nothing, then soldier *turns* are not scarce
— soldier *paint* is (median 18 at a ruin against a 120-paint pattern), and the
next iteration should attack the paint budget rather than the turn budget.

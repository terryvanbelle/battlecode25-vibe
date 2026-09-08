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
| **[SUPERSEDED 2026-09-08 — see the iteration-18 row below; its re-open condition, not this one, is binding]** Lowering `CHIP_RESERVE` (the spend gate) | iteration 16: doses 1250 and 1000 both **11/24**, identical, one game below a zero-variance null; mechanism gate failed with soldier count *falling* | the tower mix is fixed first and chips are then shown to bind with soldiers idle for want of them. Not before — a flat response across a 450-chip range says the parameter is not live. |

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

## Iteration 21 — §5b PAIRWISE ABLATION COMPLETE. No destructive pair; my own
## nomination is refuted, and both features are worth more than I assumed

Run `20260907-145307`, 72 games, 12 maps both sides, baseline `alice_iter19`.

| arm | iteration 1 idle painting | iteration 12 ballistic wander | score |
|---|---|---|---|
| Z `alice_iter19` | ON | ON | **12/24** (by definition) |
| A `alice_i21a` | **OFF** | ON | **6/24** |
| B `alice_i21b` | ON | **OFF** | **10/24** |
| C `alice_i21c` | **OFF** | **OFF** | **2/24** |

**Main effects** (games, out of 24): idle painting is worth **+6**, ballistic
wander **+2**. Both are real and both are carrying weight — idle painting is
worth 25 percentage points, which is more than any single accepted iteration
has ever been measured at.

### The interaction, read exactly as pre-registered

Additivity predicts C = 12 − 6 − 2 = **4/24**. Measured C = **2/24**.

**Interaction = C − A − B + Z = −2 games.** The noise sd of an interaction over
four 24-game arms is ≈ **4.9 games**, so |−2| / 4.9 = **0.41 sd**. That is
comfortably inside noise.

> **Conclusion: no detectable interaction. The two features are additive within
> this test's resolution, and if anything mildly complementary (−2) rather than
> substitutable (+).**

**My nomination was wrong, and it was wrong in the direction I should have
expected.** I argued iteration 1 and iteration 12 fight over the same 200-paint
tank — accepted when soldiers barely travelled, then made to travel far — so I
expected to find I was paying for the same thing twice (a positive interaction).
The data says the opposite sign, at a magnitude indistinguishable from zero.
Painting on the move and travelling further are not competing for the tank in
any way this instrument can see; they reinforce.

**§5b's own caution is the lesson, restated with a second instance behind it:**
*a heuristic nominates a pair, it is never evidence about one, and the sign of an
interaction is not predictable from its shape.* I now have my own case of that,
not just the inherited one.

### What the audit buys, given it found nothing

1. **The drift worry is not a destructive pair in this slot.** The roster's thin
   margins (58.2% vs iter7, 54.2% vs iter12) are *not* explained by these two
   features fighting. That closes the most obvious §5b hypothesis with a
   measurement instead of leaving it as unexamined unease.
2. **Two accepted features are now priced.** Idle painting +6 games, ballistic
   wander +2. Neither is the "worth ~0 or negative" case the 2026 audit found;
   both survive ablation comfortably. That is the first time this lineage has
   priced any carried feature.
3. **A negative audit is cheap insurance, and I should say so plainly**: 72
   games to learn that a suspicion was unfounded is a good trade against
   carrying it as a nagging doubt into every future accept.

### Closed-directions ledger
| direction | closed by | can re-open if |
|---|---|---|
| "Iteration 1 × iteration 12 are a destructive pair fighting over soldier paint" | iteration 21: interaction **−2 games, 0.41 sd**, wrong sign and inside noise | a *different* pair is nominated by evidence, not by shape. This specific pair is priced and closed. |

## Iteration 20 — REJECTED. The mechanism engaged hard and bought exactly nothing

Run `20260907-145851`, 72 games, baseline `alice_iter19`.

| arm | `BLOCK_PENALTY` | candidate | swept-WIN | swept-LOSS |
|---|---|---|---|---|
| zero | 0 (`alice_iter19`) | 12/24 by definition | 0 *(null)* | 0 *(null)* |
| `p5` | 5 | **12/24 (50.0%)** | 0 | 0 |
| `p10` | 10 | **12/24 (50.0%)** | 0 | 0 |
| `p25` | 25 (exclusive) | **13/24 (54.2%)** | 1 | 0 |

**Two of three doses land on the mirror null to the game**, and the third is one
game above it. Against the binding rule I fixed before `p10` and `p25` were
visible — **≥16/24 on some dose AND a mechanism-to-outcome link that is not the
win rate** — this fails both clauses. 13/24 is p = 0.42, deep inside noise, and
tower count was already flat. **Reject.**

### This is the cleanest possible instance of the failure shape I named in advance

The mechanism did not fail to engage. It engaged harder than iteration 19's did:

| | gridworld | UnderTheSea |
|---|---|---|
| ruin turns on blocked ruins, `alice_iter19` | 36.1% | 81.4% |
| ruin turns on blocked ruins, `alice_i20` | **25.7%** | **62.0%** |
| total ruin-targeted soldier turns | −27% | −57% |

**A 10-to-19-point reduction in measured waste converted to zero games.** I wrote
"metrics that improve without converting to wins" into the log *before* the
evaluation returned, and named the flat tower count as the tell. Both held.

### The falsifier fires, and it redirects the next iteration

Pre-registered: *"if removing 27–57% of ruin-targeted soldier turns changes
nothing, then soldier **turns** are not scarce — soldier **paint** is."*

That is now the measured conclusion, not a hypothesis. A soldier holds 200 paint
and each paint action costs 5 (engine-verified: `soldierAttack` calls
`addPaint(-UnitType.attackCost)`, `SOLDIER.attackCost = 5`), so it has **exactly
40 actions in its life** against a 24-tile, 120-paint pattern. Giving a soldier
*more turns* to spend a budget it has already exhausted buys nothing. **The
binding constraint is the 200-paint tank, not the turn.**

### Closed-directions ledger
| direction | closed by | can re-open if |
|---|---|---|
| Making soldiers spend fewer turns on unfinishable ruins | iteration 20: doses 5/10/25 scoring **12, 12, 13 of 24**, flat on the null, with the mechanism verified at −10 to −19 points of measured waste | soldier paint stops binding first. Turn-efficiency is worthless while the tank is the constraint. |
| "Wasted soldier turns cap tower count" | same — the waste was removed and tower count did not move | — |

### What the two rejections together say

Iterations 19 and 20 attacked the same waste from opposite sides. **19 accepted
(15/24, swept 3–0) by making moppers clear blockages; 20 rejected by making
soldiers avoid them.** The asymmetry is the finding: unblocking a pattern *adds*
a tower, while avoiding a blocked ruin merely relocates a soldier whose paint is
already spent. Removing waste only pays when the freed resource is the scarce
one — and here it was not.

**Next**: iteration 22 attacks the paint budget. The reachability groundwork is
already logged (soldiers blind 94–96% of turns on normal-density maps), but the
paint tank is now the better-evidenced target, and it needs its own
instrumentation first — where the 200 paint actually goes, per action class.

## CORRECTION — I quoted a BINOMIAL noise sd in a deterministic project. The
## right model is map resampling, and it changes readings I have already made

The coordinator caught this and is right. I wrote the interaction's uncertainty
as `sqrt(4 × 24 × 0.25) = 4.9` games. **That is a binomial sd, and binomial
assumes per-game randomness — which this project established does not exist.**
The engine and both builds are deterministic, so every `(map, side)` cell is a
fixed function of the two programs. The only thing that varies between one
estimate and another is **which maps were drawn**.

I derived 4.9 from the binomial formula, not by resampling. Correcting it.

### The correct uncertainty, by resampling the 12 maps

| quantity | binomial (wrong) | **map resample (bootstrap, 20k)** | jackknife |
|---|---|---|---|
| iteration 21 interaction | sd 4.9 → 0.41 sd | **sd 2.4**, 95% CI [−7.0, +3.0] → **0.84 sd** | sd 2.5 |

**The binomial model overstated the spread by roughly 2×**, because the per-map
contributions are concentrated rather than coin-flip-like: eight of twelve maps
contribute exactly 0 to the interaction and four contribute ±1. Determinism
makes results *structured*, and structure is lower-variance than independence.

**My "comfortably inside noise" was wrong by a factor of two.** The honest
statement is **−2 games at 0.84 sd, 95% CI [−7, +3]**.

**The verdict does not change**, and I want to be precise about why rather than
waving at it: my hypothesis was that the two features are *substitutes* — that I
pay for the same thing twice — which requires a **positive** interaction. The
interval runs from −7 to +3 and is centred at −2. It excludes nothing on the
negative side and barely reaches +3 on the positive. **No destructive pair is
supported under any point in that interval**, and if the data leans anywhere it
leans toward mild complementarity, i.e. the opposite of my nomination.

### The knock-on I have to own: this invalidates my accept-gate noise floor too

Iteration 1 recorded *"24-game H2H — 16/24 ≈ 92% confidence, 17/24 ≈ 97%; treat
13–15/24 as within noise of 50%."* **That is binomial as well**, and I used it to
hedge iteration 19's accept and to set iteration 20's ≥16/24 bar. Recomputed by
map resampling:

| result | point | map-resample se | 95% CI | vs the null of 12 |
|---|---|---|---|---|
| **iteration 19 arm A (accepted)** | 15/24 | **1.5** | [12, 18] | **+2.00 sd** |
| iteration 19 arm B | 15/24 | 1.5 | [12, 18] | +2.00 sd |
| iteration 20 `p25` | 13/24 | 1.0 | [12, 15] | +1.04 sd |
| iteration 20 `p10` | 12/24 | **0.00** | [12, 12] | **0.00 sd** |
| iteration 20 `p5` | 12/24 | **0.00** | [12, 12] | **0.00 sd** |

Three things follow, and two of them are corrections against me:

1. **Iteration 19's accept is STRONGER than I claimed.** I called 15/24
   "p = 0.154, inside my own noise band" and leaned on the swept count to carry
   it. Under the model that applies it is **+2.0 sd** and the 95% interval
   excludes the null at its lower edge. The binomial floor was too conservative,
   and I under-sold a real result.
2. **My instinct to lean on swept maps was accidentally the correct model.** A
   swept map is exactly the *map-level* unit that resampling treats as the
   observation. Reporting "swept 3–0 against a zero-variance null" was already
   the right statistic; I just did not know why.
3. **Iteration 20's rejection is far more decisive than "12/24".** `p5` and
   `p10` split **every one of the twelve maps 1–1**. Standard error **zero**.
   That is not "indistinguishable from the null on average" — it is *identical
   to the null on every map, both sides*, which is the signature of a change
   that alters behaviour without altering any outcome.

### Ledger corrections
| where | said | should say |
|---|---|---|
| iteration 21 entry | "interaction −2, noise sd ≈ 4.9, 0.41 sd, comfortably inside noise" | **"interaction −2, map-resample sd 2.4, 0.84 sd, 95% CI [−7, +3]; no destructive pair supported, leans mildly complementary"** |
| iteration 19 entry | "15/24 is p = 0.154, inside my recorded noise band" | **"15/24 is +2.0 sd by map resampling, 95% CI [12, 18]; the binomial floor understated it"** |
| iteration 1 noise floor | "treat 13–15/24 as within noise" | **superseded — binomial. Use map resampling on the run's own per-map results.** |

## Iteration 22 census — §3e RETRACTED, and the constraint is named

`alice_pbudget` vs `alice_iter19`, box and UnderTheSea. Counters are per-soldier
and cumulative; upkeep is the exact residual against the 200 tank (alice never
withdraws from a tower, so nothing else can enter the account). **The
decomposition closes to exactly 200/soldier on both maps**, which validates the
method before anything is read off it.

Soldiers with age ≥ 30 rounds (105 on box, 498 on UnderTheSea):

| sink | box | UnderTheSea |
|---|---|---|
| `markTowerPattern` | 0.7% | 0.4% |
| **pattern tiles** | **9.9%** | **3.2%** |
| **tile under self** | **23.6%** | **36.0%** |
| opportunistic area paint | 9.9% | 9.5% |
| **movement upkeep** | **39.8%** | **42.1%** |
| unspent at last sight | 16.2% | 8.9% |
| **paint actions per soldier** | **median 20 of 40** | **median 20 of 40** |

### The §3e claim is false by an order of magnitude

§3e said ~1.6 paint actions per lifetime and ~192 of 200 to upkeep. Measured:
**median 20 actions** and **40–42% upkeep**. The prediction that 3e would be
retracted was recorded before the run; it is now retracted in place, with its
*conclusion* (standing still loses because it stops finding ruins) left standing
because iteration 8 measured that independently.

### Which of the coordinator's two branches we are on

The question was whether upkeep is the constraint (96% would dwarf everything
downstream) or whether soldiers arrive with usable paint so the constraint is
*where it goes after arrival*. **It is the second.** Upkeep is real but is under
half the budget, and soldiers spend a median of 20 actions — they are not
arriving empty, they are spending on the wrong things.

### The actual finding: patterns get 3–10%, the tile underfoot gets 24–36%

**A soldier puts 1.3–3.9 tiles into tower patterns in its entire life, against
the 24 a pattern needs.** So it takes roughly **6–18 soldiers to complete one
tower**, and that ratio is the tower economy in one number.

Meanwhile the single largest *discretionary* sink is painting the tile the
soldier is standing on — **2.4× to 11× more paint than goes into patterns**.
That branch is justified in the code as "avoids paint penalty": it spends **5
paint to save 1–2 per turn**, which only repays if the soldier stays 3–5 turns.
A soldier that is travelling leaves immediately, and upkeep is *still* 40%
despite all of it — so the purchase is largely not even buying its own
justification.

**Note the distinction from iteration 21.** That ablation priced the
*opportunistic area* branch at +6 games. The *tile-under-self* branch is a
different code path and has **never been ablated**, and it is 2.5–3.8× larger.

## Iteration 22 — pricing the tile-under-self branch BEFORE building against it

The census says this branch is the largest discretionary paint sink (23.6% /
36.0%, versus 3.2–9.9% reaching tower patterns). That is the *benefit* side of
removing it. Per the loop's "cost the price as well as the benefit" pre-check,
the *cost* side has to be measured too, and the branch presumably exists because
**some** soldiers do stay long enough for it to repay.

**The arithmetic that has to be settled.** A self-paint spends **5** to make the
current tile ally, which zeroes an upkeep of **1/turn (neutral)** or **2/turn
(enemy)** for as long as the soldier remains on it. So one self-paint returns
`stay × rate`, and repays only when `stay × rate ≥ 5` — **5 stationary turns on
neutral, or 3 on enemy paint.**

`alice_pstay` measures the realised return directly rather than assuming it. For
every self-paint it records the penalty rate it just zeroed (read *before*
painting, or the tile is already ally and the rate is unobservable), then counts
the turns the soldier actually holds that tile, and closes the entry out when it
moves. Reported per soldier: `n` self-paints closed, `spent` (5·n), `saved`
(Σ stay×rate), and `repaid` (the count that returned ≥ 5).

**Pre-registered readings, so the result cannot be rationalised afterwards:**

- If `saved / spent` is well below 1 and `repaid/n` is small, the branch is a
  net paint *loss* and removing it frees the largest sink in the budget. That is
  the outcome the census predicts and the one I expect.
- If `saved / spent` ≈ 1 or above, the branch pays for itself and the census
  finding is about *allocation*, not waste — the paint is being converted, just
  not into patterns. **Then the iteration is not an ablation** and I would need
  a different mechanism.
- A middling result (`saved/spent` 0.5–1) means it repays for a minority of
  soldiers, which makes it a *conditional* — paint the tile only when the
  soldier has reason to stay — rather than something to delete.

**Note on what this does and does not settle**, recorded now: this prices the
branch in *paint*. It does not price it in *coverage* — a self-painted tile is
also a painted tile, and coverage is the win condition. Iteration 21 measured
the sibling area-paint branch at **+6 games**, so ground painting is worth
something real. Whatever `alice_pstay` returns, the ablation still has to be run
to price this branch in games, exactly as iteration 21 did for its sibling:
**two branches drawing on one budget are two prices**, and paint-arithmetic is
not a substitute for the game result.

## Iteration 22 — the 2x2 (run `20260907-161337`, 72 games, 12 maps, both sides)

Session note: the session that launched this run was killed at ~16:20 UTC by an
account-wide usage limit. The run was setsid-detached, finished, and had already
collated. Nothing was re-run.

**Design.** A full 2x2 over the two branches that draw on the same soldier paint
budget, every arm played head-to-head against `alice_iter19` on one shared
12-map sample, so all four cells are exact against a common reference:

| arm | tile-under-self | opportunistic area | score vs `alice_iter19` |
|---|---|---|---|
| Z = `alice_iter19` | ON | ON | 12/24 by definition (mirror null) |
| `alice_i22a` | **OFF** | ON | **19/24** |
| `alice_i22b` | ON | **OFF** | **6/24** |
| `alice_i22c` | **OFF** | **OFF** | **0/24** |

### Instrument check FIRST — `i22b` re-prices a quantity already priced

`i22b` is byte-for-byte iteration 21's arm A, included so the 2x2 carries its own
calibration. Iteration 21 priced the opportunistic-area branch at **+6 games**
for the baseline, on a different map sample. Here the baseline beats area-OFF
`12 − 6 = +6` games. **Exact reproduction on a fresh draw of maps**, and the
map-resample interval on this run, `6/24` with 95% CI `[3, 9]`, contains it
comfortably. The run is not suspect; the interaction below can be read.

### Uncertainty (`tools/map-resample.py`, 20k bootstrap over maps — not binomial)

| arm | score | boot se | jack se | 95% CI | vs the 12/24 null |
|---|---|---|---|---|---|
| `alice_i22a` | 19/24 | 1.71 | 1.78 | [16, 22] | **+4.09 sd** |
| `alice_i22b` | 6/24 | 1.72 | 1.81 | [3, 9] | −3.48 sd |
| `alice_i22c` | 0/24 | **0.00** | 0.00 | [0, 0] | **−12 at zero variance** |

### Finding 1 — the tile-under-self branch was costing 7 games

Per-map, `alice_i22a` scored **2 on seven maps, 1 on five, and 0 on none**:

```
box 1  defensetower 2  DonkeyKong 1  fix 1  Brat 2  Bunny 1
HungerGames 2  CastleDefense 2  galaxy 1  AlarmClock 2  Portal 2  Money 2
```

It swept 7 maps to 0 and **never lost a map from both sides**. Under the diff-
shape rule this is the strictly one-directional shape, not churn: there is no map
on which removing the branch is worse. That converts the `alice_pstay` paint
arithmetic (`saved/spent` = 0.039 on box, 0.052 on UnderTheSea — of 7,506
self-paints, exactly one returned its 5 paint) into a **game price of +7**.

The census predicted the sign and the pre-registered reading was the first one:
*"a net paint loss; removing it frees the largest sink in the budget."* Recorded
before the run, and that is what happened.

### Finding 2 — the two branches are COMPLEMENTS, and the sign was not predictable

Additivity predicts both-OFF at `12 + 7 − 6 = 13/24`. Observed **0/24**.

**Interaction = −13 games**, and that is a *lower bound on the magnitude*: 0/24 is
the floor, so the latent cell is censored and the true interaction is at least
this large. Zero variance across maps — every one of the 12 maps, both sides.

This is the opposite of the substitution hypothesis iteration 21 tested and the
opposite of what "two branches spending one budget" suggests. Mechanistically it
is now obvious in hindsight and worth stating so it is not re-derived: these are
the **only two branches that put paint on ground outside a tower pattern**, and
map coverage is the round-2000 tiebreaker. Either one alone keeps the bot in the
coverage game; removing both leaves patterns as the sole paint sink, and a
soldier delivers 1.3–3.9 pattern tiles in its life. The bot stops painting and
loses every game.

**Third nomination-versus-ablation data point.** The project's ledger said two of
three nominated pairs were refuted. This one is a genuine, very large interaction
— found not by nominating a pair but by running the 2x2 the census forced. It is
also the *opposite sign* to the intuition that named it ("substitutes competing
for one budget"). Four pairs now: two refuted, one destructive, one strongly
constructive, and **the sign was mispredicted in three of the four**. The
standing rule holds and hardens: a heuristic nominates, it never evidences, and
its sign is worth nothing.

### What this does NOT license

Removing the tile-under-self branch is *not* "ground painting is waste". It is
"of the two ground-painting branches, the one that targets the tile underfoot is
strictly dominated by the one that targets the nearest empty tile in range" —
the latter converts the same 5 paint into a tile the soldier was not already
standing on, i.e. into new coverage rather than into an upkeep rebate the soldier
leaves behind. The area branch must be kept; the 2x2 says so at zero variance.

### Candidate promoted to `src/alice`

`src/alice` now carries the `i22a` change (branch deleted, not gated). It differs
from `alice_i22a` only by also dropping the now-dead `rc.senseMapInfo(cur)` call,
which is strictly cheaper in bytecode and cannot change a decision. To keep that
claim from being an assumption, **`alice_i22a` is included as an opponent in the
evaluation run as an identity check**: if the two are behaviourally identical it
must come back 12/24 split 1–1 on every map at zero variance, exactly as `p5`
and `p10` did in iteration 20. Any other result means the bytecode delta moved a
decision and the promotion has to be re-examined.

### Evaluation launched: run `20260907-181936` (400 games, 25 maps, 8 opponents)

`alice_iter19` (accept gate, replicated on a fresh 25-map draw), `alice_i22a`
(identity check), `alice_flood` (spender archetype peer), and the full frozen
roster `alice_iter12 / iter7 / iter4 / iter1 / iter0`.

The roster is folded in deliberately: **it has not been run since `alice_iter14`,
so `alice_iter19`'s accept never got a lineage-drift reading.** Per §5b the
frozen roster is the only instrument that can see a chain of individually-
positive accepts walking downhill, and iteration 22 is a large structural removal
— exactly when it should be checked, before accepting rather than after.

## Evidence already on disk — EVERY tournament game is decided by paint coverage

Read while `20260907-181936` plays, from `tournaments/20260907-1300/` (450 games,
all 75 maps, complete run). This is the sanctioned cross-agent channel and the
only measurement here taken against opponents my lineage did not produce.

Win-condition tally, joining `results.csv` to `reasons.txt`:

| matchup | "painted enough of the map" (instant win) | r2000 tiebreak (painted more) | anything else |
|---|---|---|---|
| bob beat alice (139) | **132** | 7 | **0** |
| alice beat bob (11) | 8 | 3 | **0** |
| alice–carol (150) | 91 | 59 | **0** |

**CORRECTED — see the superseding note below. What I originally wrote here was:**
*"All 450 games in the round robin ended on paint coverage. Not one ended by
elimination or tower destruction."* **The true figure is 448 of 450 (99.6%);
two games ended by elimination.** As played by these three lineages, Battlecode
2025 is a coverage race with a mercy rule, and every other quantity — tower
count, unit count, kills — is instrumental to it at best. That conclusion is
untouched; the word "all" was not earned.

**And bob is winning that race fast, not narrowly.** Of the 139 games bob took
off alice, 132 ended **before** round 2000 at a **median round 644** — bob hits
the coverage threshold in under a third of the game. Only 7 went the distance.
Head-to-head alice is at 7.3% and bob swept **65 of 75 maps** against me.

### Why this matters for iteration 22, and for what comes after it

1. **It independently corroborates the direction, from outside the lineage.**
   The 2x2's own explanation for why removing both paint branches scores 0/24
   was "coverage is the r2000 tiebreaker". The tournament says something
   stronger: coverage is the *entire* win condition, including the 88% of my
   losses that never reach r2000. A change that reallocates the largest
   discretionary paint sink is being made on the axis the games are actually
   decided on. This is corroboration, not proof — it does not license skipping
   the gate on `20260907-181936`.
2. **It reframes the census numbers as an efficiency problem, in the right
   units.** The census measured where a soldier's 200 paint goes. The objective
   is *tiles covered per paint spent*, and by that measure the tile-under-self
   branch was the worst line in the budget: it spends 5 paint on a tile the
   soldier is about to walk off, buying an upkeep rebate it does not stay to
   collect (`saved/spent` 0.039–0.052). The area branch spends the same 5 on the
   nearest **empty** tile in range. Removing the first makes its action slot fall
   through to the second — that is the mechanism of the +7, and it is a coverage
   mechanism.
3. **It names the next target without needing a traced game.** Not "why did I
   lose map X" but the absolute, opponent-free degeneracy the algorithm's target
   -selection rule prefers: **what is alice's map-coverage curve over rounds, and
   where does it flatten?** bob crosses the threshold at ~644. If alice's curve
   plateaus well below it, the deficit is a *rate* problem (paint delivered per
   round) or a *ceiling* problem (paint delivered per soldier lifetime), and
   those have different fixes. Instrument the curve before hypothesising.

### Correction to my own framing, recorded so it is not repeated

I have been treating the tower economy ("6–18 soldiers to complete one tower")
as the thing the paint budget is for. Towers are not a win condition here; they
are a paint *pump*. The census line I should have read loudest is not the 3–10%
reaching patterns — it is that 24–36% was going somewhere that produces no
coverage at all. I got to the right change through the tower framing, but the
framing was wrong, and it would have sent the *next* iteration at pattern
throughput. Superseding it in place: **the objective is covered tiles; towers
are a means.**

## Iteration 22 mechanism verification — the +7 shows up in the replay, and not where I expected

One game, `alice` (iteration 22 candidate, T1) vs `alice_iter19` (T2) on **Money**
(35x35, 6.9% walls, 24 ruins — a map `i22a` swept). Candidate wins AREA_PAINTED.

| per 250 rounds, steady state | iter22 (T1) | iter19 (T2) |
|---|---|---|
| coverage at r2000 | **524‰** | 452‰ |
| paint actions (r1750 window) | **321** | 167 |
| **starvation deaths** (r1500/1750/2000) | **7 / 11 / 8** | **32 / 42 / 30** |
| soldiers alive | 19–23 | 19–24 |
| towers | 12 | 12 |
| chips at r2000 | $289,850 | $303,770 |

**The mechanism engaged, and the dominant effect is one I did not predict.**
I costed this branch as wasted *coverage*. The replay says its larger effect is on
**paint starvation: the candidate starves at roughly a quarter of the baseline's
rate** (8–11 vs 30–42 deaths per 250 rounds) with the same soldier population and
the same tower count. That follows directly and I should have seen it in the
census: a soldier that stops spending 24–36% of its 200-paint tank on the tile
underfoot simply *has that paint left*, and a soldier at 0 paint takes −20 HP/turn
and dies. Removing the sink did not only redirect paint, it kept the unit alive to
spend the rest.

Logging this as a **prediction I got right for an incomplete reason** — the sign
and the size were right, the causal channel was half wrong. Both channels are
real (paints per window nearly doubled *and* starvation quartered); coverage is
the sum of them.

## Structural finding — alice's coverage plateaus ~200‰ BELOW the instant-win bar

This is opponent-free and therefore the strongest kind of target the algorithm's
selection rule allows ("prefer absolute degeneracy signals over opponent-relative
comparisons — a stall needs no opponent to be wrong").

`RULES.md`: **instant win at >= 70% of `areaWithoutWalls`** (700 per-mille).

Coverage over rounds, from three replays already on disk:

| replay | r250 | r500 | r1000 | r1500 | r2000 |
|---|---|---|---|---|---|
| **mirror** (alice vs itself, UnderTheSea) T1 | 300@r200 | 524@r600 | 521 | 526 | **499** |
| **mirror** T2 | 306@r200 | 446@r600 | 457 | 457 | **482** |
| Money, iter22 | 438 | 486 | 493 | 530 | **524** |
| Money, iter19 | 519 | 482 | 483 | 443 | **452** |

**Every curve flattens between round 500 and 600 and then does not move again for
1,400 rounds.** The equilibrium is 450–530‰. The bar is 700‰. In the *mirror* —
no opponent asymmetry, both sides the same program — coverage is still stuck at
~500‰. So this is not something bob does to me; **it is my own ceiling.**

And it is not a resource shortage at the ceiling: at r2000 on Money the candidate
holds **$289,850**, 12 towers, 810 tower paint, 19 soldiers, and is painting
127–321 tiles per 250 rounds. It paints continuously and coverage does not rise.
Paints (127–321) run alongside unpaints (90–212) in every window: **alice is on a
paint treadmill, repainting contested ground rather than expanding into unpainted
ground.**

Contrast bob in the tournament: it crosses 700‰ against me at a **median round
644**, i.e. right about where my curve stops moving.

### Iteration 23 candidate — SPLASHERS, a unit type this lineage has never built

Nominated by the ceiling above, and it is the algorithm's named failure mode:
*"a whole game mechanic sat unused for 81 iterations because the obvious methods
were assumed to be the whole interface."*

**Two facts, both verified in code rather than inferred:**

1. **The tower never builds one.** `runTower`'s `want` is `MOPPER` or `SOLDIER`
   and nothing else. Every replay window in every dump I have, across every map
   and both teams, reads `spl0` and `+spl0`. Zero splashers, ever, in this
   lineage's entire history.
2. **And if it did, they would never fire.** `runSplasher` initialises
   `bestScore = 3` and scores only the **centre tile** — enemy paint 2, empty
   passable 1. The maximum achievable score is 2, so `score > bestScore` can
   never be true, `best` stays `null`, and the splasher wanders without ever
   attacking. This is dead-on-arrival code, not merely unused code. Any splasher
   iteration must fix the scorer *first* or it will measure nothing — exactly the
   reachability pre-check the algorithm requires before building.

**The price, computed before the benefit, as the loop demands.** Tower paint is
the binding resource (chips are at $290k); so everything is priced per tower-paint.

| | soldier | splasher |
|---|---|---|
| tower paint / chips to build | 200 / 250 | **300 / 400** |
| paint cap | 200 | 300 |
| paint per attack | 5 | **50** |
| attacks per lifetime | 40 | **6** |
| tiles per attack | 1 | **13** (r²<=4 of centre) |
| tiles per lifetime | 40 | **78** |
| **tiles per tower-paint** | **0.20** | **0.26** |
| action cooldown | 10 | **50** |
| can overwrite ENEMY paint | **no** | **yes**, within r²<=2 (9 tiles) |

**Break-even is sharp and pre-registrable: a splash must convert >= 10 of its 13
tiles to beat a soldier's 5-paint-per-tile rate.** Below 10 it is worse than the
soldier it displaced from the same tower-paint pool; the overlap between a blast
and already-ally ground is the whole question, and it is a *measurement*, not an
argument.

The second row matters at least as much as the first: **soldiers cannot overwrite
enemy paint at all** (`soldierAttack` paints only empty-or-ally tiles). The
treadmill above is alice paying moppers to erase enemy paint one tile at a time at
r²<=2. A splasher erases *and* claims 9 tiles in one action. That is a
treadmill-breaking capability the lineage does not possess in any form.

**Pre-check to run before building anything** (instrument the DECISION, not the
outcome, per the loop): a diagnostic build that, each soldier turn, evaluates the
best available splash centre in vision and reports **how many of its 13 tiles are
non-ally**. If the achievable median is below 10, the unit is priced out before it
costs a run and the ceiling needs a different attack. If it is comfortably above,
the iteration is justified on arithmetic before a single game is played.

This is queued, not started: iteration 22 must clear its gate first, and nothing
here may be bundled into it.

## Tooling — my replay dumper is now the shared `tools/replay-dump.sh`; my copy is deleted

The coordinator promoted my dumper to `tools/replay-dump.sh` + `tools/replaydump/`
(`152ad05`), using mine as the base because it was the most complete of the three,
and kept the `DieAction`-not-`diedIds` fix with its comment. `agents/alice/tools/
replay-dump.sh` and `agents/alice/tools/replaydump/` are removed; everything above
and below this line uses `../../tools/replay-dump.sh`, verified identical output on
the census replay before deleting.

Same reasoning as the two duplicates I removed earlier today (the parity table and
`map-resample.py`): a private copy of a shared instrument drifts, and when it does
the other lineages inherit my bug without inheriting my fix.

**New capability I intend to use:** ASCII arena views (`--map N`, `--map-at R`,
`--views`). The reconstruction closes against the engine's `teamCoverageAmounts`
on every frame and prints the gap — my own "close the accounting before you read
anything off it" rule applied to a tool, which caught a 1-based-team encoding bug
and a −2‰ offset from towers painting their own tile at spawn. Documented limit:
`SplashAction` carries only its centre, so splashed tiles are not applied and the
gap is printed. **That limit lands directly on iteration 23** — if I build
splashers, the reconstructed grid stops closing and must not be believed; the
engine's `cov` counter stays trustworthy and is what I will quote.

## THE ROOT CAUSE — engine probe: a soldier attack on ENEMY paint costs 5 and does nothing

I went looking for why removing the tile-under-self branch quartered starvation
deaths, decompiled `InternalRobot.soldierAttack`, and found something bigger than
iteration 22.

```
 50: getstatic  UnitType.SOLDIER
 54: getfield   UnitType.attackCost
 57: ineg
 58: invokevirtual addPaint:(I)V          <-- THE 5 PAINT IS SPENT HERE
 61: ... getRobot(loc) ... isTowerType ... -> tower damage branch
162: ... isPaintable(loc) ... ifeq 231    <-- bail out, AFTER the debit
173: ... getPaint(loc) ... teamFromPaint(mine) vs teamFromPaint(there)
207: if_acmpne 231                        <-- ENEMY PAINT: return, AFTER the debit
210: setPaint(...)                        <-- only reached for empty-or-ally
```

**`addPaint(-attackCost)` is unconditional and runs before the target is examined.**
Both bail-outs — not paintable (170) and enemy-painted (207) — are downstream of
it. So **attacking an enemy-painted tile burns the full 5 paint and accomplishes
nothing.** And `canAttack` is no protection: it checks range and action-readiness,
never the tile's paint. Added to `RULES.md` as a TRAP beside the `transferPaint`
clamping one.

### This is the actual mechanism of iteration 22, and I had it half wrong

The removed branch was guarded by `!here.getPaint().isAlly()`, which is true for
**empty and enemy alike**. Combined with the saturation finding below, the tile a
soldier stands on that is not ally is *overwhelmingly enemy*, so that branch was
mostly paying 5 paint per turn for a no-op until the soldier starved.

The sibling area branch survives the same 2x2 at +6 for one reason visible in one
line of code: it tests `t.getPaint() == PaintType.EMPTY`, the **right** predicate.
**Two branches drawing on one budget, and the difference between +6 and −7 is
which predicate they check.** That is a far more useful account than "the tile
underfoot is a bad target", which is what I wrote this morning.

## Why the wrong predicate is so expensive — the map SATURATES by ~round 500

From the shared dumper's new arena view on `alice_splashcensus` vs `alice`, Money,
round 1200, engine counters (not the reconstruction):

**T1 432‰ + T2 545‰ = 977‰ painted. 97.7% of the paintable map is claimed.**

That single number reorganises everything I thought this game was:

- The instant-win bar is **>= 700‰**. After saturation, no amount of painting empty
  ground can reach it, because **there is no empty ground**. The remaining ~270‰
  has to be **taken off the opponent**.
- **Soldiers cannot take a single tile off the opponent.** Engine-verified above.
  Alice's entire ground-taking capability is the mopper's 1-tile, r²<=2, 0-paint mop.
- So my coverage curve flattening at 450–530‰ between rounds 500 and 600 and never
  moving again for 1,400 rounds is not a mystery and not an opponent effect (it
  happens in the **mirror** too). It is the map running out of empty tiles while
  the only unit I mass-produce loses the ability to do anything useful with paint.

### The splash census, and how it nearly fooled me the other way

`alice_splashcensus` (built on the iteration 22 candidate) counts, every soldier
turn, the best 13-tile splash blast reachable from where the soldier stands —
**the decision a splasher would face, not the outcome of one**. Two windows,
Money, aggregated per robot by taking each robot's last cumulative line:

| window | soldiers | soldier-turns | mean best blast (of 13) | turns with >=10 | with 13 | of those tiles, ENEMY |
|---|---|---|---|---|---|---|
| r1200 | 14 | 1,008 | **1.37** | 7.5% | 2.9% | **94.3%** |
| r1990 | 23 | 1,394 | **1.37** | 8.2% | 3.2% | **98.0%** |

Two independent windows agreeing to two decimal places. Read naively this **kills
the splasher**: break-even needs >= 10 of 13 tiles and the mean is 1.37, i.e. 36.5
paint per tile against the soldier's 5.

**But the naive read is wrong, and the last column is why.** The blast is empty of
targets because alice's soldiers stand inside alice's own finished paint. Of the
non-ally tiles they *can* see, 94–98% are **enemy** — the very tiles a soldier can
never take and a splasher can (9 of them, within r²<=2 of the centre). The census
does not price the splasher; it prices **the splasher at a soldier's chosen
position**, and alice's soldiers do not go to the frontier. Recorded as a
methodological catch: *an instrument that samples positions chosen by the current
policy cannot price a unit whose value depends on choosing different positions.*

So the splasher is **neither justified nor refuted** and stays queued. What the
census did do is find the real defect, which is cheaper and better founded.

### Iteration 23 candidate — stop paying 5 paint for refused actions

Second instance of the trap, in the ruin-pattern loop, and it is worse than the
one iteration 22 removed:

```java
if (mark != PaintType.EMPTY && mark != t.getPaint()) {
    if (rc.canAttack(t.getMapLocation())) {
        rc.attack(t.getMapLocation(), mark == PaintType.ALLY_SECONDARY);
        break;                      // <-- and nothing else happens this turn
    }
}
```

`mark != t.getPaint()` is satisfied by an **enemy-painted** pattern tile. The
soldier then attacks it (5 paint, no-op), `break`s out — so it also forfeits the
area-paint branch that turn — and comes back to the *same tile* next turn. **An
enemy-painted pattern tile is an unbounded paint sink: 5 paint per turn, forever,
until the soldier starves,** and this is a soldier that has committed to a ruin so
it will not wander away.

The fix is one clause: only attack a pattern tile whose current paint is `EMPTY`
or ally. Enemy-painted pattern tiles are a mopper's job — which is exactly what
**iteration 19 accepted** (moppers clear the enemy paint that stalls tower
patterns). Iteration 19 fixed the blockage from the mopper side; the soldier side
was left burning paint against it the whole time.

**History pre-check — does this re-open a closed direction?** Iteration 20 closed
*"making soldiers spend fewer turns on unfinishable ruins"*, measured at 12/24 with
**zero** standard error, and its recorded re-open condition is *"soldier paint
stops binding first; turn-efficiency is worthless while the tank is the
constraint."* This candidate is **not turn-efficiency** and does not relocate the
soldier: it stops a 5-paint debit on an action the engine refuses. It attacks the
tank — the exact resource iteration 20's ledger named as binding — so it is a new
direction under that entry, not a silent revert of it. Stating this before
building, per the History pre-check.

Not started, not bundled: iteration 22 must clear `20260907-181936` first.

## Iteration 22 evaluation — run `20260907-181936`, first two opponents complete

Fresh random 25-map sample, disjoint from the 12 maps the 2x2 used. Uncertainty
by map resampling (20k bootstrap), null = 1 win per map = 25/50.

| opponent | score | boot se | jack se | 95% CI | vs null | swept-win / swept-loss / split |
|---|---|---|---|---|---|---|
| **`alice_iter19`** (accept gate) | **33/50 (66%)** | 2.72 | 2.78 | [28, 38] | **+2.94 sd** | **9 / 1 / 15** |
| **`alice_i22a`** (identity check) | **25/50 (50%)** | **0.00** | **0.00** | [25, 25] | **0.00 sd** | **0 / 0 / 25** |

### The identity check is exact, and that matters

`src/alice` differs from the measured `alice_i22a` by one dropped dead
`rc.senseMapInfo(cur)` call. The per-map histogram is `{1: 25}` — **every one of
25 maps split 1–1, both sides, standard error zero.** That is the same
zero-variance signature `p5`/`p10` produced in iteration 20, and here it is the
desired outcome rather than a rejection: the bytecode I removed changed no
decision on any map. **What I am proposing to accept is exactly what I measured.**

I want to note *why* this was worth a fifth of the run rather than a paragraph of
reasoning. "Removing a call whose result is unused cannot change behaviour" is
true only if the limiter never truncated a turn, and the limiter truncates
*silently*. The check cost 50 games and converts an assumption into a measurement.

### The accept gate replicates on independent maps

| sample | score | vs null |
|---|---|---|
| 2x2 run `20260907-161337` (12 maps) | 19/24 (79%) | +4.09 sd |
| this run (25 maps, disjoint) | 33/50 (66%) | +2.94 sd |
| **pooled** | **52/74 (70.3%)** | — |

Two disjoint map samples, both clearing the gate on their own, bracketing a true
value near 70%. The point estimate came down from 79% to 66%, which is the normal
shrinkage when a first estimate is replicated on ground the mechanism was not
selected on — and the *direction* and the swept-map shape are unchanged (9 swept
wins against 1 swept loss).

Peer `WinPct` and the frozen roster are still playing. No accept is recorded until
they land, per §5b: the head-to-head is a partial derivative, and the roster has
not been run since `alice_iter14`.

## Iteration 23's premise just failed its own reachability pre-check (on this map)

`alice_i23diag` counts the **decision**: every ruin-pattern attack, split by
whether the target tile is enemy-painted (5 paint, engine-refused) or empty/ally
(real work). Money, `alice_i23diag` vs the iteration 22 candidate.

**Rounds 800, 1600, 1990: 39 soldiers sampled, `turns=0` for every one of them.**
The ruin-pattern loop **never executes at all** in the late game — because Money's
24 ruins are, by then, all claimed (T1 11 towers + T2 13 towers = 24). There are
no unclaimed ruins to target, so the branch I was about to fix is **dormant**.

This is the pre-check doing exactly the job the algorithm assigns it: *"a correct
chain of reasoning about a dormant branch predicts nothing — this burned three
iterations in one day once."* My argument for iteration 23 was mechanically
correct about the code and would have measured nothing after round ~500.

Early-round sampling (r150/300/500/700, while ruins are still contested) is
running now. Three outcomes, pre-registered before I look:

- **Waste concentrated early and large.** The candidate survives, but its value is
  bounded by the opening, and it must be evaluated on *when* the coverage curve is
  still rising — not on end-state coverage.
- **Waste early but small.** Reject on price before building; note it as a known
  small leak and move on.
- **Zero everywhere.** The whole direction is dead and the ledger gets an entry.

Either way the tile-under-self branch that iteration 22 removed was the *live*
instance of this trap and the pattern loop is at most the residue.

### Iteration 23 reachability — resolved, and the waste has a sharp time profile

`alice_i23diag` (iteration 22 code plus counters; behaviour unchanged), Money.
Per-soldier cumulative counts, aggregated by taking each soldier's latest line.

| round | soldiers | pattern-loop turns | attacks on empty/ally (real work) | **attacks on ENEMY paint (5 paint, refused)** | wasted share |
|---|---|---|---|---|---|
| 150 | 7 | 143 | 64 | 5 | **7.2%** |
| 300 | 11 | 64 | 5 | **55** | **91.7%** |
| 500 | 16 | **0** | 0 | 0 | branch dormant |
| 700 | 19 | **0** | 0 | 0 | branch dormant |
| 800 / 1600 / 1990 | 39 | **0** | 0 | 0 | branch dormant |

**The pre-registered outcome that fired is the first one: concentrated early and
large.** The profile is sharper than I expected and it explains itself:

- **r150** — ruins are freshly discovered, their patterns are unpainted, and 93%
  of pattern attacks land. The mechanism is working as designed.
- **r300** — the contested ruins have been painted by the *opponent*, and
  **92% of every pattern attack is now burning 5 paint for nothing.** Worse than
  a leak: the old loop `break`s on that first enemy tile, so the soldier also
  forfeits its area paint that turn and returns to the identical tile next turn.
  A soldier committed to a contested ruin is in an unbounded paint sink until it
  starves.
- **r800+** — dead. All 24 of Money's ruins carry towers (11 mine, 13 theirs), no
  unclaimed ruin is ever sensed again, and the branch never executes.

**CORRECTION to what I wrote one paragraph ago, before anyone else has to catch
it.** I said the live window was "roughly rounds 200–600". The r500 and r700
samples had already landed and both read **zero**: soldiers born after about
round 350 never sense an unclaimed ruin on this map, because all 24 of Money's
ruins carry towers by then. **The live window is roughly rounds 150–400, not
150–600**, and it is narrower than the story I was about to tell. Writing it the
smaller way on purpose — I have a candidate built and a motive to make its window
look bigger.

That window still overlaps the stretch where the coverage curve is rising and
where bob finishes me (median round 644), but it ends before that median rather
than straddling it. And the measured size is modest: **275 paint across 11
soldiers at r300, ~25 paint each, about 12.5% of one 200-paint tank.**

Two sampling lessons, both cheap and both real: had I only sampled the late game
I would have filed this dormant; had I only sampled r150 I would have filed it
tiny. **One sampling round gives the wrong answer in either direction**, and the
correction above shows a third failure mode — sampling enough and then quoting
the window I wanted rather than the one I measured.
**One sampling round would have given the wrong answer in either direction.**

### The change (`src/alice_i23`), one mechanism

```java
if (t.getPaint().isEnemy()) continue;   // refused by the engine; 5 paint for nothing
```

Placed inside the existing mismatch test, before `canAttack`. Two effects, both
intended and neither bundled:

1. The soldier stops paying for refused actions.
2. Because it `continue`s rather than `break`s, it now **finds a paintable pattern
   tile further along the same pattern** instead of stopping at the first enemy
   one — so it does more real pattern work, not merely less waste. If the whole
   pattern is enemy-held it falls through to the area branch and paints an empty
   tile, which is 5 paint converted into 1 tile of actual coverage.

Clearing enemy paint off a pattern stays the mopper's job — that is iteration 19,
accepted and still in the build. This change is the soldier-side complement that
iteration 19 left open: **iteration 19 unblocked the pattern; nobody stopped the
soldier from paying to bang on the blockage in the meantime.**

**Pre-registered gate**, recorded before the run:
- Head-to-head vs the iteration 22 build (the new baseline once it is accepted) on
  a fresh 25-map sample, **> 50%**, quoted with `tools/map-resample.py`.
- **Mechanism**: `en` per soldier at r300 must fall to ~0 in the candidate arm,
  and starvation deaths in rounds 200–600 must fall. If `en` does not move, the
  clause never fired and the result is void regardless of the score.
- **Watch (the thing most likely to bite)**: this frees paint *and* changes which
  tile gets painted. If coverage at r600 does not rise while starvation falls, the
  freed paint is going somewhere that does not convert — the exact failure shape
  iteration 20 hit — and it is a reject, not a near miss.


### Sizing check — Money may be a degenerate map for this quantity

Money has **24 ruins on 1,141 paintable tiles**, one of the denser ruin supplies
in the corpus, so its ruins are exhausted early and the branch dies at ~round 350.
A map with sparser ruins keeps unclaimed ruins in play far longer and would give
this branch a much longer live window — or, if the waste is a Money artifact,
none at all.

Per the loop's *"check your sizing map is not degenerate"* rule (the lineage has
already been burned once by `gridworld`, the densest map in the corpus and one of
four with single-parity ruins), `alice_i23diag` is now running on **UnderTheSea**
(45x45, 27 ruins over 1,847 paintable tiles — roughly **half Money's ruin
density**). Pre-registered: if the wasted share on UnderTheSea is also >80% during
its live window, the effect is a property of contested ruins rather than of Money,
and the candidate is worth a full evaluation. If UnderTheSea shows little waste,
the quantity is map-specific and the candidate is not worth a run on the strength
of one map.

### Sizing result — it reproduces, and Money was the FLATTERING map, not the alarming one

`alice_i23diag` vs the iteration 22 build on **UnderTheSea** (45x45, 23 ruins).
Ruin density from `tools/mapdata/`, which is the right denominator here:

| map | size | ruins | ruins / 1000 tiles | |
|---|---|---|---|---|
| `gridworld` | 31x31 | 21 | **21.9** | corpus densest — flagged degenerate |
| `Paintball`, `DefaultSmall` | 20x20 | 8 | 20.0 | |
| **`Money`** | 35x35 | 20 | **16.3** | **my first sizing map — well above median** |
| **`UnderTheSea`** | 45x45 | 23 | **11.4** | **exactly the corpus median** |
| `boxofchocolates` | 55x55 | 15 | 5.0 | |
| `Gears` | 55x55 | 14 | 4.6 | corpus sparsest |

| round | soldiers | pattern-loop turns | landed | **refused (5 paint each)** | wasted share |
|---|---|---|---|---|---|
| 200 | 9 | 123 | 42 | 14 | 25.0% |
| 400 | 20 | 79 | 15 | 21 | 58.3% |
| **700** | 36 | 47 | **0** | **29** | **100.0%** |
| 1200 | 41 | 0 | 0 | 0 | dormant |

**Pre-registered threshold was >80% during the live window. It hits 100.0%.**

At round 700 on the median-density map, the ruin-pattern branch executes 47 times
and **every single attack it makes is refused by the engine.** Not "mostly
wasted" — the landed count is exactly zero while the refused count is 29. A branch
that has become pure loss, and one that also consumes the turn's `break` and so
forfeits the area paint that would have been real coverage.

**And the correction runs the other way from the one I made an hour ago.** I
corrected Money's window down from "200–600" to "150–400" and called that honest.
It was, *about Money*. But Money is 43% above the corpus median in ruin density,
so its ruins are exhausted early and its window is **short**. On the median map
the window runs from ~200 to ~1000 and the wasted share climbs monotonically to
100%. **I sized a ruin quantity on a ruin-dense map and understated it** — which
is the exact error `tools/mapdata/README.md` documents for `gridworld`, committed
one map further down the density table. The README says "a poor choice for sizing
any ruin-related quantity"; the rule is about density, not about that one map's
name, and I only escaped it because the rule made me check a second map at all.

Two maps, both showing the same monotone shape, one at the corpus median.
**Iteration 23's premise is established.** It waits on iteration 22's accept.

## Closed-directions ledger — current as of iteration 22

Superseding in place, not replacing: the iteration-20 entries below stood when
iterations 21 and 22 were designed and stay readable as written.

| direction | closed by | can re-open if |
|---|---|---|
| Making soldiers spend fewer **turns** on unfinishable ruins | iteration 20: doses 5/10/25 scoring 12, 12, 13 of 24 — `p5` and `p10` splitting **every** map 1–1 at zero standard error | soldier paint stops binding first. Turn-efficiency is worthless while the tank is the constraint. **Still closed after iteration 22** — 22 attacked the tank, not the turn, and that is a different resource. |
| "Wasted soldier turns cap tower count" | same — the waste was removed and tower count did not move | — |
| The two ground-paint branches are **substitutes** competing for one paint budget | iteration 22's 2x2: both-OFF scores **0/24 at zero variance** against an additive prediction of 13/24. Interaction **−13 games**, censored at the floor. They are **complements** — the only paint that reaches ground outside a tower pattern. | nothing foreseeable. A saturating map makes ground paint the win condition; removing all of it cannot be right. |
| Refuelling soldiers from towers (`transferPaint` withdraw) | iteration 6: a refill costs the same 200 tower paint as a fresh soldier and saves only 250 chips, which are not binding; measured near break-even | tower paint stops being the spawn bottleneck, **or** the walk back becomes free (a soldier already standing at a tower it just completed). The pre-registered near-miss refinement — refuel only when the tower is within a few tiles — was never run and remains the honest way to re-open this. |

### Explicitly NOT closed, recorded so it is not mistaken for closed

**Splashers.** `alice_splashcensus` returned a mean best blast of 1.37 tiles of 13
against a break-even of 10, over 2,402 soldier-turns, stable across two windows.
That number is real and it is **not** a refutation: it prices a splasher standing
where a *soldier* chose to stand, and 94–98% of what those blasts contain is enemy
paint — the tiles a soldier cannot take and a splasher can. Filing this in the
ledger would be the exact error the census itself exposed. It stays **open and
unpriced**, and pricing it needs an instrument that samples frontier positions.

### Standing structural gap (not a closed direction — an unattempted one)

**After the map saturates, this lineage has almost no way to take ground.**
Measured today: 977‰ of Money is painted by round 1200; the instant-win bar is
700‰; soldiers cannot overwrite enemy paint at all and are charged 5 paint for
trying. My entire ground-taking capability is the mopper's one-tile, r²<=2 mop.
Both prior projects record that the highest-value accepts came from the
**high-risk structural track**, and this is the gap that track should attack. It
is named here rather than attempted, because iterations 22 and 23 are in flight
and bundling is forbidden.

## Standing bytecode + exception check (required on every full evaluation)

Run `20260907-181936`, 199 games scored at the time of writing: **0 exceptions,
total, across every opponent and both sides.**

Soldier bytecode in the *shipping* iteration 22 build (replay `alice` vs
`alice_iter19` on Money, round 1500, worst five soldiers):

```
bc=1982 max=2307   bc=2314 max=2365   bc=2414 max=2501
bc=2476 max=2657   bc=2532 max=2713
```

**Peak 2,713 of the 17,500 soldier limit — 15.5%, so 84.5% headroom**, and no
`OVR=` or `near=` suffix appears on any indicator string. Iteration 23 adds one
`isEnemy()` test inside a loop that already runs; it is free at this margin.

**Caveat I want on the record about my own instruments, not the bot.**
`alice_splashcensus` peaked at **14,327**, against a near-miss threshold of
`17500 − 17500/7 = 15,000`. It never overran — no `OVR=` on any line — but it was
within 5% of the band where the limiter starts silently truncating turns, and a
truncated turn would have changed the very positions the census was sampling.
**A heavyweight diagnostic can bias itself by costing too much**, and the only
reason I can say it did not here is that the counter was printed. `alice_i23diag`
and `alice_i23v` are cheap by comparison (four increments) and are not at risk.

## Cheap negative result — my deficit against bob has NO map-class structure

Zero games spent: `tournaments/20260907-1300/results.csv` (complete, all 75 maps,
150 alice–bob games) joined to `tools/mapdata/` ruin counts. The algorithm's
"check the evidence already on disk before spending a run" pre-check, run against
the class of hypotheses I would naturally reach for next.

| split | maps | alice vs bob | mean ruin density | mean area |
|---|---|---|---|---|
| sparsest third | 25 | 5/50 = **10.0%** | 7.8 | 2,127 |
| middle third | 25 | 1/50 = **2.0%** | 11.3 | 1,829 |
| densest third | 25 | 5/50 = **10.0%** | 15.8 | 1,226 |
| smallest third | 25 | 4/50 = **8.0%** | 13.4 | 770 |
| middle third | 25 | 3/50 = **6.0%** | 11.9 | 1,525 |
| largest third | 25 | 4/50 = **8.0%** | 9.6 | 2,887 |

**Flat, on both axes.** Alice loses at 90–98% everywhere; the 2% cell is one game
on 50 and the two outer cells are identical. There is no ruin-density story and no
map-size story.

**What that kills, cheaply**: every hypothesis of the form *"alice is losing to
bob because of how it handles map class X"* — sparse-ruin maps, dense-ruin maps,
big maps, small maps. I would have reached for one of those, and this table says
the deficit is **systematic and capability-shaped, not situational.** That is
direct support for the standing structural gap above (no way to take ground once
the map saturates) and direct evidence *against* spending an iteration on
map-adaptive policy, which is one of the perennial mechanics the cross-year
research names and which I was carrying as a live candidate.

**The one exception is worth its own line**: alice **sweeps `maze` 2–0**, the only
map it takes from both sides against bob. maze is the corpus's largest (60x60,
3,600 tiles) with below-median ruin density (7.8) — the map where saturation
arrives latest, and therefore the map where "paint empty ground" stays a winning
policy longest. That is the same saturation story from the other end, and it is
the single most informative game I own against an opponent my lineage did not
produce. Archiving it is the right use of the post-accept replay slot.

## Iteration 23 mechanism check — the clause fires, and its LARGER effect is the one I listed second

`alice_i23v` (= `alice_i23` plus counters, same indicator encoding as
`alice_i23diag` so the two parse identically) vs the iteration 22 build,
UnderTheSea, round 200. Against the baseline census on the same map and round:

| round | | pattern-loop turns | **landed** (real pattern tiles) | refused attacks |
|---|---|---|---|---|
| 200 | baseline `alice_i23diag` | 123 | 42 | **14** |
| 200 | **candidate `alice_i23v`** | 123 | **53** | **0** |
| 400 | baseline | 79 | 15 | **21** |
| 400 | **candidate** | **209** | **28** | **0** |
| 700 | baseline | 47 | **0** | **29** |
| 700 | **candidate** | 48 | 1 | **0** |

Zero refused attacks at every round, which is true by construction and is the
weakest of the three rows. The interesting ones are the others: at r400 the
candidate reaches the pattern loop **209 times against the baseline's 79** and
lands **28 against 15**, and at r700 the baseline lands **exactly zero** while
refusing 29. The r400 turn count more than doubling is the starvation channel
showing up again — soldiers that are not burning paint on refused attacks are
still alive and still working ruins.

Both decompositions close to 123. **The candidate lands 53 pattern tiles against
the baseline's 42 — +26% — while making zero refused attacks.**

So of the baseline's 14 refused attacks, **11 became landed attacks** and 3 became
fall-throughs to the area branch. That is effect (2) from the design note —
"`continue` rather than `break`, so it finds a paintable tile further along the
same pattern" — and it is **larger than effect (1), the saved paint**, which I had
listed first. Second time today the mechanism I ranked second turned out to
dominate; the pattern is that I keep pricing the *removal* and under-pricing what
the freed action slot goes on to do.

### Correcting a metric I printed before anyone had to challenge it

My dump script computed `paint saved = 5 x skipped = 2,830`. **That number is
meaningless and I am striking it.** `skipped` counts enemy tiles passed over
*while scanning a pattern* — many per turn — whereas the baseline could only ever
burn 5 paint **once per turn**, because it `break`s. The baseline's real waste at
r200 is 14 attacks = **70 paint**, not 2,830. The 566 skips are a fact about the
board (the patterns being worked hold ~4.6 enemy tiles each), not about paint.
**A counter that is not in the same units as the thing it is compared against is
not evidence**, and the decomposition closing to 123 is what makes the rest of
this table trustworthy.

### The caveat that bounds all of the above

These are **two different games**. `alice_i23diag` vs `alice` and `alice_i23v` vs
`alice` share an opening and then diverge at the first decision the clause
changes, so by round 200 they are different trajectories and the 42-vs-53
comparison is suggestive, not controlled. What it establishes is §4's criterion 2
— **the mechanism demonstrably engaged as designed** — and nothing about game
value. The head-to-head on a fresh 25-map sample remains the gate, and it is
pre-registered above.

## Saturation TIMING — the "paint empty ground" phase ends far earlier than I assumed

Empty share = `1000 − T1cov − T2cov`, straight off the engine's counters in
replays I already have. No games spent.

| map | r200–250 | r400 | r600 | r1200 |
|---|---|---|---|---|
| **Money** (16.3 ruins/1000) | **43‰ empty** | — | — | 23‰ |
| **UnderTheSea** (11.4, median) | 394‰ | 99‰ | **30‰** | — |

**Money is 95.7% saturated by round 250. UnderTheSea by round 600.** The timing is
map-dependent — denser ruins and smaller area saturate faster — but on both maps
the empty-ground phase is over inside the first **12–30% of the game**, and for
the remaining 70–88% there is essentially nothing left to claim.

Meanwhile the tower keeps spawning the same ~75%-soldier mix for all 2,000 rounds.

### What I must NOT conclude from this, and nearly did

"So soldiers are useless after round 600" is wrong, and the replay says so. The
`acts[... a...]` column — `AttackAction`, i.e. tower damage, not painting — runs
at **600–1,200 per 250 rounds** in the late game. My soldiers are not idling;
they have switched to attacking towers, which is real work (50 damage a hit) and
is how tower counts move. It also is not free: `soldierAttack` debits the same 5
paint for a tower hit, so a 1,000-HP tower costs ~100 paint to kill.

So the late game is **soldiers trading paint for tower damage**, not soldiers
doing nothing. Any hypothesis here has to beat that alternative use, not an idle
baseline. Writing this down because "the mechanism I am attacking is doing nothing"
is the assumption that made iteration 20 cost 72 games.

### Queued structural candidate (iteration 24, not started)

**Make the spawn mix respond to saturation instead of being a fixed 75/25.** The
mix is a constant chosen when the map was empty, and it is still 75% soldiers when
there has been no empty ground for 1,400 rounds. Moppers are the only unit that
can take ground back, and mopping costs **zero paint** (mop is free; only the
mopper's 100-paint build price is paid), against a soldier's 5 paint per tile that
it may not even be allowed to spend.

Three things this needs before it is worth a run, none of them done:

1. **A dose, and a zero arm.** The mix fraction is a natural dose, and the current
   75/25 is the zero. Doctrine #2 requires the zero arm and at least two nonzero
   points, because a concave curve with an interior optimum is the shape this
   kind of parameter has had twice in this lineage already (iteration 5's mopper
   reserve, iteration 12's wander run).
2. **Self-calibration over a constant.** The saturation round is 250 on one map and
   600 on another, so a fixed round threshold is exactly the kind of tuned constant
   this project has repeatedly found inferior to a threshold derived from
   observation — here, the empty-tile fraction a unit can see, which every robot
   already senses for free.
3. **Price what the mopper displaces.** A mopper is 100 tower paint out of the same
   pool that funds soldiers, and iteration 5 established that pool is the binding
   one and that shifting the mix toward moppers has an *absorbing failure state*
   (paint income collapses because moppers complete no patterns). §3c calls that
   the most expensive bug this lineage has had. **The mix must not be moved
   without instrumenting tower paint in the first run.**

Queued behind iterations 22 and 23. Recorded now so the reasoning is dated before
any result exists to flatter it.

## Iteration 23 pre-registration, refined before the run (two additions)

### 1. Read the result against RUIN DENSITY, not just as a headline

This is a **ruin-related quantity**, and I have already measured its live window
varying from ~150–400 rounds on Money (16.3 ruins/1000) to ~200–1000 on
UnderTheSea (11.4, the corpus median). A 25-map random sample averages over that
variation, so a modest headline could be hiding a large effect on the half of the
corpus where the window is long.

Pre-registered: **partition the run's 25 maps at the corpus median density (11.4)
and report both halves.** If the sparse half shows a clearly larger effect than
the dense half, that is a dose-response *in map space* — the strongest form of
evidence doctrine #2 recognises — and it costs nothing extra, because the data
arrives with the run either way. If both halves look the same, the density story
is wrong and I should say so.

Recording the prediction so it cannot be retrofitted: **I expect the sparse half
to be larger.** If it is not, the mechanism is not what I think it is even if the
headline clears.

### 2. This change has no identifiable price, which is itself suspicious

Working through the cases, the candidate never spends more paint than the baseline
in any of them:

| situation | baseline | candidate |
|---|---|---|
| a paintable pattern tile exists | 5 paint, tile painted | same |
| first mismatched tile is enemy, a paintable one lies further in | **5 paint, nothing painted**, `break` | 5 paint, **tile painted** |
| whole pattern is enemy-held | **5 paint, nothing painted**, `break` forfeits area paint | 0 there, then **5 paint on an empty area tile** |
| nothing attackable | no attack | same |

Equal paint, strictly more converted. A change with no price is the shape that
should raise suspicion, not confidence — every candidate I have accepted so far
had a cost I could name, and the loop's own rule is *"cost the price as well as
the benefit"*. So the honest statement is **I have not found the price, not that
there isn't one**, and the two places it would hide are:

- **Bytecode.** Removing the early `break` makes the loop scan up to 24 tiles
  instead of stopping at the first. Headroom is 84.5% (peak 2,713 of 17,500), so
  this should be nothing — but "should be nothing" is what the limiter punishes
  silently, and the `OVR=` counter is printed for exactly this reason. **Check it
  in the run.**
- **Second-order population effects.** Fewer starvation deaths means more soldiers
  alive, and iteration 5 / §3c established that the soldier↔mopper mix and the
  tower-paint pool interact badly when population shifts. **Instrument `twPaint`
  and the alive counts**, per the rule that a change altering draws on a shared
  capped resource must instrument the pool in its first run.

If the diff comes back one-directional and positive with no `OVR` and a stable
tower-paint pool, then it really is a free correction of an engine trap — which is
the *"capability preserved at zero marginal cost"* profile both prior projects
name as the recurring winner.

## New instrument `tools/density-split.py`, and an orientation bug I caught in it

Splits a run's per-map result at the corpus median ruin density (11.4 per 1000
tiles), reading counts from the **shared** `tools/mapdata/ruin_parity.txt` rather
than a private copy. Built because several of my live quantities are
ruin-related and the corpus spans 4.6–21.9 ruins/1000 — a 4.8x spread that a
25-map random sample silently averages over.

**It was wrong on first run and the bug is worth recording**, because it is the
same shape as the 1-based-team encoding the coordinator hit in the shared dumper.
My first version counted the **opponent's** wins, because I copied the counting
convention from `tools/map-resample.py` — which is correct *there*, since ablation
runs put the baseline in `BOT` and the candidates in `OPPONENTS`. This run is the
other way round: `BOT=alice` is the candidate. Same file format, opposite meaning,
and the output looked perfectly plausible at 28.6%/40.9%. The fix prints
`bot.txt`'s bot name in the header and the docstring states the orientation and
names the disagreement with `map-resample.py` explicitly, so the next reader
cannot make the same substitution silently.

### Iteration 22 has a density gradient, and it is the OPPOSITE of my model

| opponent | sparse half (mean 8.6/1000, 14 maps) | dense half (13.9/1000, 11 maps) |
|---|---|---|
| **`alice_iter19`** (accept gate) | **20/28 = 71.4%** | **13/22 = 59.1%** |
| `alice_flood` | 21/28 = 75.0% | 17/22 = 77.3% |
| `alice_iter12` | 27/28 = 96.4% | 19/22 = 86.4% |

Against the null (14 and 11), iteration 22 is **+6 on the sparse half and +2 on
the dense half**. Difference of differences ≈ 4 games against a combined se of
about 2.7 — **roughly 1.5 sd, which is suggestive and not decisive**, and I am
labelling it that way rather than as a finding.

**But its direction contradicts my mechanism.** My account of iteration 22 is that
the removed branch was mostly attacking *enemy* paint underfoot and being refused.
Enemy paint underfoot is a **saturation** phenomenon, so that account predicts the
gain should be larger on **dense**, early-saturating maps. It is larger on the
sparse ones.

I can construct a story — on an unsaturated map the underfoot tile is often EMPTY,
the area branch would paint it anyway at distance 0, so the two branches are near
substitutes there and removing one costs little — but that story explains why the
gain is *not smaller* on sparse maps, not why it is *larger*. **I do not have a
coherent model of this gradient, and I am recording that rather than inventing
one.** Under-powered at 1.5 sd; the honest move is to let iteration 23's own split
arrive and see whether a gradient reproduces on an independent mechanism.

**And it does not change iteration 23's pre-registered prediction**, which rests
on a directly measured quantity rather than on this: the live window is longer on
sparse maps (~200–1000 rounds on UnderTheSea vs ~150–400 on Money), so there are
more turns in the branch to correct. That prediction now happens to agree with
this gradient, which is *weak* corroboration at best — two arguments pointing the
same way, one of which I have just said I cannot explain.

## Periodic RobotController API sweep — 37 of 68 methods never called, and three matter

The algorithm requires this sweep on a schedule, for a stated reason: *"a whole
game mechanic sat unused for 81 iterations once because the obvious methods were
assumed to be the whole interface."* I found the splasher gap by accident today,
which is exactly the signal that the sweep was overdue. Done properly now:
`javap battlecode/common/RobotController.class`, 68 public methods, diffed against
every call site in `src/alice/RobotPlayer.java`.

**37 are never called.** Most are conveniences (`onTheMap`, `adjacentLocation`,
`getMapWidth`), debug aids (`setIndicatorDot/Line`, `setTimelineMarker`), or
already-closed directions (`transferPaint` — iteration 6; `markResourcePattern` /
`completeResourcePattern` — SRPs, closed at "+5.6 points, never cleared the bar,
re-open if chips become binding", and chips are at $290k so they have not).

Three are live capability gaps, ranked:

### 1. The ENTIRE communication system, unused for 22 iterations

`sendMessage`, `readMessages`, `broadcastMessage`, `canSendMessage`,
`canBroadcastMessage` — **not one call anywhere in the lineage.** From `RULES.md`:

- robot↔tower, r²<=20 **and** connected by a 4-adjacent ally-paint path; 1 msg/turn
  for robots, 20/turn for towers; 4-byte int payload; buffer holds 5 rounds.
- **tower→tower broadcast at r²<=80 with NO paint connectivity required.**

Two things make this more attractive here than the generic "comms are good":

- The paint-connectivity requirement is normally the hard part of a BC25 comms
  design. **My own saturation finding removes it**: my territory is a contiguous
  painted mass by round 250–600, so robot↔tower connectivity is nearly free
  exactly when I need it. A constraint I would have had to engineer around is
  already satisfied by the board state I measured today.
- Towers form a long-range backbone at r²<=80 unconditionally, and I field 11–14
  of them. That is a global channel, not a local one.

Comms schema design is one of the perennial mechanics the cross-year research
names, and this lineage has none. **This is the largest unexplored capability I
own.**

### 2. `mopSwing` — the mopper's area attack, never used

6 tiles (2 rows of 3 in front), **−5 paint per enemy robot hit**, cooldown **20**
against the ordinary mop's **30**. So a swing that catches three robots drains 15
paint on a shorter cooldown than a mop steals 10 from one.

Why this is not a generic "more damage" idea — which §"metrics that improve
without converting" says to distrust: **65–100% of all deaths in this game are
paint starvation, not combat.** Draining an enemy robot's paint is not chip damage
that has to be converted into something else; it is the direct cause of the way
units actually die. The cost is real and must be priced: a swing does not clear
ground paint, so it trades a mopper's ground work for robot attrition, and ground
work is what iteration 19 accepted.

### 3. `mark` / `removeMark` — a 1-paint durable shared-memory channel on the ground

I call `markTowerPattern` (25 paint) and nothing else. `mark` places an
ally-visible annotation for **1 paint** at r²<=2, persistent, with no gameplay
effect beyond being readable by allies. My soldiers random-walk to find ruins and
have no way to know a ruin is already someone's target. A 1-paint durable "taken"
flag is the cheapest coordination primitive on the board and I have never used it.

**None of these is started.** Iterations 22 and 23 are in flight and 24 is queued;
this is the ledger of what the sweep found, dated, so that the next time the loop
stalls the structural track has a costed menu rather than a brainstorm.

## Play-symmetry audit, from the mirror arm I was already running (zero extra games)

The algorithm requires a periodic mirror — bot vs byte-identical copy, every map,
both sides — and the `alice_i22a` identity arm *is* one: 25 maps, 50 games, two
programs that differ only in dead code and that the run proved behaviourally
identical.

```
winning SIDE across all 50 games:            A 26,  B 24
maps where the SAME side won both games:     25 / 25
maps where the winner alternated with the bot: 0 / 25
```

### Two separate findings, and they point in opposite directions

**1. No global play-symmetry bug is detectable.** A compass-order iteration, a
fixed direction fallback, or anything else correlated with team identity would
show up as a systematic skew toward A or B across maps. **26–24 is as close to the
null as 50 games can get.** That is the reassuring half, and it is the specific
thing the audit is for.

**2. But the per-map side advantage is TOTAL.** On **every one of 25 maps, the
same side won both games.** Not "usually", not "on the lopsided ones" — all 25.
Two byte-identical programs, and which one wins is decided entirely by which spawn
it got. Nothing about the program breaks the tie on any map in the sample.

### Why this matters more than the reassuring half

- **It is the empirical justification for the swept-map statistic**, which this
  lineage has been leaning on by instinct since iteration 7. A swept map is a map
  where the bot won from the side that a mirror says *should lose*. This mirror
  says that is exactly the informative event, because in a mirror the swept count
  is **zero out of 25** by construction. Reporting "swept 9 to 1" against
  `alice_iter19` is therefore 9 maps where the change beat a side advantage that a
  coin-flip-equivalent opponent never beats once.
- **It bounds what a single-side result can ever mean.** A one-sided match in this
  game is close to 100% confounded. I have quoted single-side generality checks
  before (iteration 7's "8/8" was both sides, correctly; other spot-checks were
  not).

### I have NOT determined the mechanism, and I am not going to guess

Maps are guaranteed symmetric by the map contract, so with identical programs the
asymmetry must come from somewhere outside the map. Three candidates, none tested:

- **Robot IDs.** My PRNG is `rngState = rc.getID() * 31 + 17`, and the two teams
  get different ID sequences — so identical code makes *different random choices*
  per side. If this dominates, a large share of my outcomes is decided by seed
  rather than by policy, and reducing the bot's reliance on randomness (comms,
  ground markers, deterministic exploration) converts luck into skill. That would
  make the API-sweep items above considerably more valuable than they look.
- **Engine turn order.** If team A acts first each round, that is a structural
  first-mover edge. It would predict a skew toward A, and the observed 13-map/12-map
  split argues against it dominating.
- **Spawn placement under the specific symmetry class** of each map.

Distinguishing these is a cheap engine probe plus one instrumented mirror, and it
is queued rather than done — I have a candidate awaiting its gate and this is not
on its path. Recorded now with the mechanism explicitly open, because "the PRNG
seed decides my games" is exactly the sort of striking claim I would otherwise be
tempted to write down before testing it.

### Narrowing the mirror's mechanism — turn order is NOT team-blocked

One cheap check while the run finished, on a replay I already had: within a single
round, do all of one team's robots act before the other's?

```
round 600, first 20 turns by team:  T2 T1 T2 T1 T2 T1 T2 T1x3 T2x2 T1x2 T2x6
```

**Interleaved.** There is no "team A acts first" block, so the structural
first-mover story for the mirror's total per-map side advantage is weakened —
which is what the 13-map/12-map split already suggested. Turn order within a round
runs by robot ID, and the spawn IDs in the dumps (T1 12121/12177/11565 against T2
12296/13193/10210/10646) come from **one shared pool, interleaved between teams**,
not from per-team blocks.

That leaves both surviving candidates tracing back to the same root: **which IDs
a team happens to draw**. It sets my PRNG seeds (`rc.getID() * 31 + 17`) *and* the
order units act in, and it is fixed per map and side. Consistent with the
observation and with the near-even 26–24 aggregate.

**Still not settled** — this rules out one candidate and does not confirm another.
The decisive test is an instrumented mirror with the PRNG seed held constant
across teams; if the per-map side advantage survives that, IDs are not the cause.
Queued with the rest.

# ITERATION 22 — ACCEPTED

Run `20260907-181936` complete: **328/400 (82.0%)**, 25 maps, both sides, 8 opponents.
Uncertainty by map resampling (20k bootstrap); null = 1 win per map = 25/50.

| opponent | role | score | se | 95% CI | vs null | swept W/L |
|---|---|---|---|---|---|---|
| **`alice_iter19`** | **accept gate** | **33/50 (66%)** | 2.72 | [28, 38] | **+2.94 sd** | **9 / 1** |
| `alice_i22a` | identity check | 25/50 (50%) | **0.00** | [25, 25] | — | 0 / 0 |
| `alice_flood` | peer (spender archetype) | 38/50 (76%) | 2.87 | [32, 43] | +4.53 sd | 14 / 1 |
| `alice_iter7` | peer | 37/50 (74%) | 2.86 | [31, 42] | +4.20 sd | 13 / 1 |
| `alice_iter12` | roster | 46/50 (92%) | 1.83 | [42, 49] | +11.5 sd | 21 / 0 |
| `alice_iter4` | roster | 49/50 (98%) | 0.98 | [47, 50] | +24.5 sd | 24 / 0 |
| `alice_iter1` | roster | 50/50 (100%) | 0.00 | [50, 50] | — | 25 / 0 |
| `alice_iter0` | roster | 50/50 (100%) | 0.00 | [50, 50] | — | 25 / 0 |

*(The three `se = 0.00` rows have an undefined sd, not a zero one — my ad-hoc
script printed `+0.00` for them and that is a display artifact, not a result. The
honest statement for `iter1`/`iter0` is "50/50, every map swept, deterministic".)*

### Every gate, checked explicitly

1. **Head-to-head > 50%** — 33/50 = 66%, **+2.94 sd**, lower CI bound 28 > 25.
   Replicates the 2x2's 19/24 on a disjoint 25-map sample; **pooled 52/74 (70.3%)**.
2. **Peer `WinPct` >= 60%** — the three peers are 66% / 76% / 74%. All clear.
3. **Identity check** — 25/50, per-map histogram `{1: 25}`, **se 0.00**. The build
   being accepted is behaviourally identical to the one the 2x2 measured.
4. **No unresolved one-directional regression** — three swept losses in the whole
   run, on **three different maps** (`Racetrack` 16.0 ruins/1000, `yearofthesnake`
   7.9, `Parking_lot` 11.4), against three different opponents, and **no map is
   swept-lost against more than one opponent**. That is the scattered,
   mixed-direction shape doctrine #7 calls churn, not the concentrated shape it
   calls a causal regression.
5. **Frozen roster (§5b) — the only instrument that can see a lineage drifting
   downhill.** It had not been run since `alice_iter14`. Every point rose:

| frozen opponent | `alice_iter14` (this morning) | **iteration 22** | delta |
|---|---|---|---|
| `alice_iter12` | 54.2% | **92.0%** | **+37.8** |
| `alice_iter7` | 58.3% | **74.0%** | +15.7 |
| `alice_flood` | 62.5% | **76.0%** | +13.5 |
| `alice_iter4` | 91.7% | **98.0%** | +6.3 |
| `alice_iter1` / `alice_iter0` | 100% | 100% | at ceiling |

**No destructive pair is hiding.** This is the check §5b exists for — a chain of
individually-positive accepts walking downhill — and the answer is unambiguous.

6. **Bytecode / exceptions** — 0 exceptions in 400 games; soldier peak 2,713 of
   17,500 (84.5% headroom), no `OVR=` or `near=` on any indicator string.

### What was accepted, in one line

The `!here.getPaint().isAlly()` guard on the paint-the-tile-underfoot branch is a
**proxy** for the engine's real predicate, and on a map that saturates to 97.7%
the two diverge completely: the branch spent 5 paint per turn on attacks the
engine refuses outright (`addPaint(-attackCost)` at offset 58, enemy-paint bail-out
at 207). Deleting it cut starvation deaths roughly fourfold and raised coverage.

### Opponent-pool classification after this run

- **Peers** (30–90%, gate acceptance): `alice_iter22` (the new baseline),
  `alice_flood` (76%), `alice_iter7` (74%).
- **Roster** (never retired by design, absolute-progress instrument only):
  `alice_iter0`, `iter1`, `iter4`, `iter12`, `alice_flood`.
- `alice_iter12` at 92% is above the peer band and would normally retire, but it
  is a roster member and roster members are never retired — the value is the
  long-run trend of its line, not its current resolution.

### Post-accept routine (all in this commit)

- Snapshot `src/alice_iter22/`, compile-verified by a real match.
- `progress/vs_old_bots_history.csv` +6 rows, charts regenerated
  (`cumulative_iterations.png` now reads 10 accepted iterations, iter0..iter22).
- Roster rows are labelled **`alice_iter19+cand`**, not `alice_iter22`, because
  that is the build that actually played — it was a candidate when the run
  started. Keeping the tool's honest label rather than back-dating it.
- Replay archived: `replays/iter22_alice_iter19_Money_A.bc25` — the match carrying
  the coverage curves and the fourfold starvation drop.

**Next: iteration 23**, built, mechanism-verified, sized on two maps, and
pre-registered (including a ruin-density split and a written admission that I have
not found its price). Its baseline is now `alice_iter22`.

## Engine-predicate audit, applied to the WHOLE build (the new pre-check, run once properly)

Iteration 22's milestone was a process change: **before trusting any guard, check
it against the engine's own predicate by decompilation.** Applying it to every
action path rather than only the one that bit me.

`javap` of `InternalRobot`, every method that calls `addPaint`:

```
mopSwing      mopperAttack      processBeginningOfRound
processEndOfTurn      soldierAttack      splasherAttack
```

**`towerAttack` is absent from that list — tower attacks cost ZERO paint**, and
the method ends in `TeamInfo.addMoney(...)`, the defence-tower attack bonus. A
tower attacking is pure upside with no resource cost at all.

Call-site by call-site, in `src/alice`:

| call site | guard | engine predicate | verdict |
|---|---|---|---|
| soldier, area branch | `t.getPaint() == PaintType.EMPTY && isPassable` | paints if empty-or-ally | **correct** (strictly conservative) |
| soldier, **ruin-pattern loop** | `mark != EMPTY && mark != t.getPaint()` | refuses enemy paint, **debits anyway** | **THE BUG — iteration 23** |
| mopper, mop | `t.getPaint().isEnemy() && canAttack` | mop targets enemy paint | **correct**; and `addPaint` here is a **gain** (+5 stealing from a robot), not a cost |
| tower, single + AoE | `enemies.length > 0`, then `canAttack(null)` | **no paint cost, plus a money bonus** | **correct**, and cheaper than I knew |
| splasher | dead — `bestScore = 3` initialised above the max achievable score of 2 | debits 50 unconditionally at offset 70 | unreachable; must be fixed before any splasher work |

**Conclusion: the ruin-pattern loop is the only remaining instance of the trap in
the shipping build**, which is exactly what iteration 23 changes and nothing else.
That is a genuinely useful audit outcome — it says iteration 23 closes the class,
rather than being the second of an unknown number.

Two incidental corrections to my own mental model, both worth having:

- I had assumed tower attacks drew on the tower's paint, which is why the tower
  code guards them behind `enemies.length > 0`. They are free **and** they earn
  chips. The guard is still right (AoE needs something in range), but "towers
  should attack whenever they can" is now a fact rather than a hope.
- `mopperAttack` calling `addPaint` looked alarming for about a minute. It is the
  **+5 steal**, not a cost. **A method appearing on a "calls addPaint" list is not
  evidence of a debit** — the sign matters, and I checked it rather than assuming
  the pattern I had just found was everywhere.

## RETRACTION — iteration 22's "density gradient" was a dichotomisation artifact

Two hours ago I reported, from `tools/density-split.py`, that iteration 22 gained
+6 games over the null on the sparse-ruin half of the sample and +2 on the dense
half, called it "suggestive, ~1.5 sd, not decisive", and said I could not explain
its direction. I should have checked it at full resolution before writing it down
at all. Doing that now, with Spearman's rho between a map's ruin density and the
candidate's wins on that map (0/1/2), permutation-tested:

| opponent | rho | permutation p | n |
|---|---|---|---|
| **`alice_iter19`** (the accept gate) | **−0.093** | **0.673** | 25 |
| `alice_flood` | −0.004 | 0.986 | 25 |
| `alice_iter7` | −0.220 | 0.289 | 25 |
| `alice_iter12` | −0.303 | 0.147 | 25 |
| `alice_iter4` | −0.057 | 0.832 | 25 |

**Nothing.** The accept-gate opponent — the one I actually quoted the split for —
has rho = −0.093 at p = 0.67, which is as close to no relationship as 25 maps can
express. **The gradient I reported does not exist at full resolution.**

### What went wrong, precisely

**Binning a continuous variable at its median and reading the difference between
the bins is a known way to manufacture a signal**, because the split discards the
ordering *within* each bin and the difference then rides on which side of an
arbitrary cut a few maps happened to fall. My split put 14 maps one side and 11
the other; moving two maps across the line moves the headline by several points.
The rank correlation uses every map's position and finds no trend.

I want to be exact about my own error rather than blame the method: **I built the
splitter, ran it, got a number that looked like a story, and wrote 400 words about
not being able to explain it — when the correct next step was five lines of code
that would have told me there was nothing to explain.** I even flagged it as
"under-powered" and then reasoned about its direction anyway. Flagging uncertainty
is not a substitute for resolving it when resolving it is cheap.

The one thing that survives is weak and I am labelling it as such: **all five
correlations are negative**, i.e. the sign is consistent. But these are not five
independent tests — the same 25 maps and the same candidate build, differing only
in opponent — so they cannot be combined, and every one of them individually is
null.

### Consequence for iteration 23, applied before its run finishes

Its pre-registration said "partition the run's 25 maps at the corpus median and
report both halves." **Superseding that in place: the primary density statistic
for iteration 23 is the rank correlation with a permutation p-value, and the
median split is reported only as a descriptive companion.** The prediction stands
as written — I expect a negative rho — but it will be judged on the statistic that
cannot manufacture an effect, and I now have a documented case of the other one
doing exactly that.

`tools/density-split.py` gets the rank correlation added so the trap is closed in
the instrument rather than in my memory.

## Iteration 23 — IN FLIGHT. Resumption state for whoever reads this next

**Run `20260907-194028`** — `BOT=alice_i23`, opponents `alice_iter22` (accept
gate) / `alice_flood` / `alice_iter7`, 25 maps, both sides, **150 games**. Launched
19:40 UTC, running detached under setsid, so it survives this session dying. As of
this note it is at 31/150 and moving slowly because the shared VM is contended.

**If you are a fresh session: do NOT re-run it.** Check
`../../tools/gauntlet-collect.sh --list`; if it shows complete, recover with
`../../tools/gauntlet-collect.sh 20260907-194028`.

### Interim, and why I am not reading it

`alice_iter22`: 22/31 (71%), swept 6, swept-lost 0.

**That number is not evidence yet and I am recording it only so the state is
legible.** `gauntlet.sh`'s own header says a partial opponent has played an
*easy-or-hard prefix* of the shared map list, never a random subsample, so a
partial rate is confounded by map difficulty in an unknown direction. The gate is
the completed 50 games.

### The decision rule, restated so it cannot drift while the run finishes

- **Accept** if head-to-head vs `alice_iter22` > 50% by map resampling, the two
  peers hold >= 60%, and the swept-loss pattern is scattered rather than
  concentrated on one map or side.
- **Mechanism gate (can void an otherwise-passing score)**: refused pattern
  attacks must be 0 — true by construction — and the *landed* count must rise.
  Already verified on UnderTheSea: 53 vs 42 at r200, 28 vs 15 at r400, 1 vs 0 at
  r700.
- **Density**: primary statistic is **Spearman's rho with a permutation p-value**,
  per today's retraction. The median split is descriptive only. Prediction on
  record: negative rho.
- **Price watch**: check `OVR=` on indicator strings (the loop now scans up to 24
  tiles instead of breaking early) and check tower-paint and alive counts, since
  fewer starvation deaths shifts the population and §3c's absorbing state came
  from exactly that kind of shift. I stated before the run that **I could not find
  this change's price**; that is a thing to resolve, not a thing to celebrate.

### If it rejects

Trace the flipped games first. The queued alternatives, in order, are already
costed in this log: **iteration 24** (spawn mix responsive to saturation — needs a
dose, a zero arm, a self-calibrating threshold, and tower-paint instrumentation),
then the **structural track** from today's API sweep (**communication**, unused for
22 iterations and made cheap by the saturation finding; **`mopSwing`**;
**`mark`/`removeMark`** as a 1-paint coordination primitive).

### Functional-area tracker

Iterations 19, 20, 22 and 23 all sit in **soldier paint spending** — 19 accept, 20
reject, 22 accept, 23 pending. `MaxConsecutiveRejects` is 3 and there is no reject
streak, so the area is not closed. But four consecutive iterations in one area is
worth noticing on its own: **if 23 rejects, the next attempt should leave this
area** even though the formal rule would not yet require it.

## Iteration 23 accept gate — 34/50, and my pre-registered prediction is WRONG

The `alice_iter22` arm of run `20260907-194028` is complete (50/50 games).

| | value |
|---|---|
| score vs `alice_iter22` | **34/50 (68.0%)** |
| boot se / jack se | 2.39 / 2.45 |
| 95% CI | **[30, 39]**, null 25 |
| distance from null | **+3.77 sd** |
| per-map histogram | **`{1: 16, 2: 9}`** |
| swept-win / swept-loss | **9 / 0** |

**The diff shape is as clean as this instrument can produce: the candidate does
not lose a single map from both sides.** Nine maps swept, sixteen split by side,
zero swept losses. Under doctrine #7 that is maximally one-directional — there is
no map on which the change is worse.

### And the pre-registered density prediction FAILED

I wrote, before the run: *"I expect the sparse half to be larger. If it is not,
the mechanism is not what I think it is even if the headline clears."*

**Spearman rho = +0.318, permutation p = 0.127.** Two things are true:

1. **p = 0.127 means there is no density trend to speak of at all** — this is not
   "a trend in the other direction", it is a null with a point estimate that
   happens to sit on the wrong side of zero.
2. **My directional prediction is nevertheless not supported**, and I said in
   advance what that would mean. Honouring it.

### Reconciling it — and flagging that this reconciliation is POST-HOC

My prediction was derived from **effect (1)**: the live window is longer on sparse
maps, so there is more refused-attack waste to remove there. But I had **already
measured that effect (2) dominates** — the `continue` finding a paintable tile
further along the same pattern, where 11 of 14 refused attacks at r200 became
landed ones and the candidate landed 53 against 42. Effect (2)'s frequency does
not scale with how long unclaimed ruins persist; it scales with **how often a
pattern holds a mix of enemy and paintable tiles**, which if anything is higher
where ruins are dense and contested.

So the honest account is: **I pre-registered a prediction derived from the effect
my own mechanism check had already shown to be the smaller one.** The prediction
failing is a defect in my reasoning, not a surprise in the data.

**This explanation is post-hoc and I am not entitled to believe it.** It is
written down as a hypothesis for a future test, not as a rescue. What the
pre-registration buys me is precisely that I cannot now quietly claim the density
result "supports" anything.

### What this does and does not change

It does **not** invalidate the score. 34/50 at +3.77 sd with zero swept losses is
a fact about game outcomes, independent of which of two co-occurring effects
drives it, and both effects are consequences of the same one-line change.

It **does** mean the mechanism attribution stays open, and it sharpens what to ask
next: the two effects are separable (a variant that skips enemy tiles but still
`break`s would isolate effect 1). That is the ablation this iteration earns if it
accepts — and per §5b's "an ablation prices a CODE PATH, not a concept", these are
two paths in one line and I should not assume the price divides the way the story
does.

**No accept recorded yet**: `alice_flood` is at 4/6 and `alice_iter7` has not
started, so the peer gate is unmeasured. The price watch I owe — `OVR=` and the
tower-paint/population check — is running next.


## CORRECTION — I wrote "all 450 games" having tallied 300 of them

The coordinator caught this. Re-derived from `reasons.txt`, which was on disk the
whole time:

| outcome | games | share |
|---|---|---|
| painted enough of the map (instant win) | 366 | 81.3% |
| tiebreaker, painted more | 82 | 18.2% |
| **destroyed all enemy units** | **2** | **0.4%** |

The two eliminations are `bob vs carol on Jail` (r402) and `carol vs bob on
SandyBeach` (r941) — **both in the bob–carol matchup, the one pairing I never
tallied.** My script filtered to `{alice,bob}` and `{alice,carol}`, which is 300
games, and I then wrote a sentence about 450.

**The conclusion is untouched at 99.6%** and the strategic frame it launched — the
game is a coverage race, saturation is the binding fact, soldiers cannot take
ground — stands entirely. That is not the point.

**The point is that I generalised from the subset I computed to a population I
did not, in a sentence whose entire rhetorical force was the word "all",** on a
day when I retracted two of my own findings for less. The exact count was one
command away and I had already run 90% of that command. The failure mode is
specific and worth naming: **a filter written for one purpose silently became the
denominator for a claim about the whole.** The `for r in rows: if pair == ...`
line was correct for the head-to-head table it was written for, and I reused its
output for a different question without re-reading its scope.

Adopting: **when a claim quantifies over "every" or "all" of something, print the
denominator next to the number.** `366 + 82 + 2 = 450` would have failed loudly.
This is my own "close the accounting before you read anything off it" rule, which
I applied to the paint-budget census and to the arena reconstruction and did not
apply here.

The tournament report now tabulates these shares itself (`ff176e4`), so nobody
re-derives it.

## The engine finding is now shared ground — `tools/engine-facts.md`

The coordinator promoted the `soldierAttack` trap after **re-deriving it from the
jar rather than taking it on trust** — `addPaint` at offset 58, first `getPaint`
on the target at 178, 120 bytecodes apart. The transferable half recorded there is
the general form, which is the right call and outlives the method: **guard on the
engine's own predicate, never on a proxy you believe implies it.** "Not mine" and
"EMPTY" agree right up until a map saturates.

The file's standing requirement — **every entry must carry the command that
re-derives it, because a claim about the engine that cannot be re-derived is a
belief** — is the same discipline as the correction above, applied to engine facts
instead of to counts. I will cite `tools/engine-facts.md` rather than restating
its contents, so there is no private copy of it in this workspace to drift.

## Iteration 23 price watch — the price is not there, and the master variable moved

I stated before the run that **I could not find this change's price**, and named
the two places it would hide. Both checked.

**1. Bytecode.** The loop now scans up to 24 pattern tiles instead of breaking at
the first. Across the mechanism replay: **zero `OVR=` occurrences**, soldier
bytecode 787–824 against a 17,500 limit. **0 exceptions in 61 games** of the
evaluation. Not a cost.

**2. The shared tower-paint pool** — the §3c absorbing state, where a population
shift starves paint income until only moppers are affordable and the game is
unrecoverable. `alice_i23v` (T1) vs the iteration 22 build (T2), UnderTheSea:

| round | coverage | | towers | | **tower paint pool** | | soldiers | |
|---|---|---|---|---|---|---|---|---|
| | **i23** | iter22 | **i23** | iter22 | **i23** | iter22 | **i23** | iter22 |
| 500 | **583‰** | 397‰ | **16** | 9 | **4,130** | 585 | 30 | 19 |
| 1000 | **671‰** | 308‰ | **18** | 9 | **2,470** | 570 | 52 | 20 |
| 1500 | **636‰** | 332‰ | **18** | 9 | **1,990** | 750 | 41 | 21 |
| 2000 | **634‰** | 347‰ | **18** | 9 | **1,785** | 350 | 58 | 33 |

**The pool does not collapse — it is 3–7x LARGER in the candidate**, all game. The
feared failure is not merely absent, its opposite happened.

### This is much bigger than "stop wasting 5 paint occasionally"

**The candidate reaches 18 towers against 9.** Tower count is the master variable
(§3d), and this doubles it. Coverage follows: **671‰ at r1000 against 308‰** — and
671‰ is within 30 of the **700‰ instant-win threshold**, on a map where the
baseline plateaus at a third of the board.

The causal chain is now legible end to end and every link is measured rather than
assumed: skipping engine-refused pattern tiles lets the soldier land on a
paintable tile further along the same pattern (53 vs 42 at r200, 28 vs 15 at
r400) → **patterns complete instead of stalling** → 18 towers instead of 9 →
paint income roughly doubles → the pool fills to 4,130 → more soldiers (58 vs 33)
→ coverage 634‰ vs 347‰.

### And this rescues the failed density prediction — which I must not overclaim

The corrected model says the dominant channel is **converting stalled patterns
into towers**, not reclaiming wasted paint. That channel should pay *more* where
there are **more ruins to convert**, i.e. on **dense** maps — which is the sign
the run actually produced (rho = +0.318, p = 0.127).

So two independent readings now agree, and **both disagree with what I
pre-registered.** I will not treat that as vindication: the density statistic is
still a null (p = 0.127), and a post-hoc story that agrees with a non-significant
point estimate is worth very little. What it *is* worth is a **new, sharper
prediction to test rather than assume**: if the tower channel dominates, then
**tower count at r1000 should rise with ruin density in the candidate arm**, which
is a directly measurable quantity I have not measured.

### Caveats, stated plainly

- This table is **one game on one map**, and the two arms diverge from the first
  changed decision, so it is a mechanism account and not an effect size. The 34/50
  head-to-head is the effect size.
- UnderTheSea sits at the corpus **median** ruin density, which is the right place
  to read a mechanism, but a single map cannot establish the tower channel.
- Starvation deaths are *higher* in absolute terms (91 vs 61 per 500 rounds) — but
  the candidate fields and spawns far more units (169 vs 145 soldiers spawned), so
  the rate per unit is not what this table shows and I am **not** claiming it fell.

## The corrected model failed ITS first test too — there is no map-level structure at all

I said one paragraph ago that the post-hoc tower-channel story was worth a
sharper prediction rather than belief, and named it: if the dominant channel is
converting stalled patterns into towers, the predictor should be the **absolute
number of ruins available to convert**, not their density. Tested immediately, on
data already in hand:

| covariate | Spearman rho | permutation p |
|---|---|---|
| **absolute ruin COUNT** (the corrected model's variable) | **+0.104** | **0.640** |
| ruin DENSITY (what I pre-registered) | +0.318 | 0.127 |
| map AREA | −0.116 | 0.606 |

**The corrected model's own variable performs WORSE than the one it was invented
to replace.** All three are null.

So the honest state is: **iteration 23's effect has no detectable map-level
covariate structure whatsoever.** Not density, not ruin count, not size. Two
stories have now been tested against map variation — my pre-registered one and my
post-hoc replacement — and neither is supported.

### What that actually means, and it is not bad news

A uniform effect across a 4.8x density range and a 6x area range is **exactly what
"swept 9, swept-lost 0" already said in a different language**: there is no map
class where this is worse, and no map class where it is specially good. It simply
works everywhere. That is the *strongest* shape a change can have for a bot that
must play an unknown map, and it is a better outcome than a large effect
concentrated somewhere.

What it costs me is the **mechanism attribution**. Both the paint-reclaim story
and the tower-conversion story predict map-level structure, and there is none. So:

- The **replay evidence for the tower channel stands** — 18 towers vs 9, a
  tower-paint pool 3–7x larger, coverage 671‰ vs 308‰ — because that is measured
  directly in the game state, not inferred from cross-map variation.
- The **cross-map evidence for it does not exist**, and I am not entitled to cite
  density as support. Superseding the previous entry's "two independent readings
  now agree" in place: **they do not. One is a null and the other is a single
  game.**

### The rule I am taking from this

**A post-hoc explanation earns exactly one thing: the next test. Run it before
writing the explanation down as though it were settled.** I did run it, within
minutes, and it failed — which is the system working. The failure mode I avoided
is the one where a rescue story gets recorded alongside a null it "agrees with",
survives because nobody tests it, and is quoted three iterations later as
established. This lineage has already found the wrong and right models sitting
adjacent in LEARNINGS for exactly that reason.

The separating experiment remains the one named earlier and it is a *game*
experiment, not a correlation: **a variant that skips enemy pattern tiles but
still `break`s** isolates the paint-reclaim effect from the scan-onward effect.
That is what iteration 23 earns if it accepts, and it prices two code paths in one
line — which §5b warns is exactly where a price does not divide the way the story
does.

## The separating ablation, built and pre-registered (`src/alice_i23abl`)

Iteration 23 changes one clause that does **two** things, and the whole-map
covariate analysis has just failed twice to tell them apart. So the separation has
to be done the way §5b says — **by pricing the code paths, in games** — not by
another correlation.

The three arms differ by **one keyword**:

| arm | the clause | what it does |
|---|---|---|
| `alice_iter22` (baseline) | *(absent)* | attacks the enemy tile: pays 5, refused, then `break`s |
| **`alice_i23abl`** | `if (isEnemy()) break;` | **declines to pay, then stops** — effect (1) only |
| `alice_i23` (accepted candidate, if it accepts) | `if (isEnemy()) continue;` | declines to pay **and scans onward** — effects (1) + (2) |

Verified by diff: `alice_i23abl` and `alice_i23` are byte-identical apart from
`break` versus `continue` on one line. That is as clean as an ablation gets in
this project — no rebuild drift, no bundled second change, nothing to argue about
regarding what was gated.

**Pre-registered readings, before the arm has played a game:**

- `i23abl` vs `iter22` prices **effect (1)**, stopping the refused payment.
- `i23` vs `i23abl` prices **effect (2)**, scanning onward to a paintable tile.
- The two should sum to roughly the 34/50 that `i23` scored against `iter22`. **If
  they do not sum, one of the two arms is interacting with something I have not
  named**, and that is more interesting than either price.

**My prediction, recorded now**: effect (2) is the larger, because the mechanism
census already showed 11 of 14 refused attacks at r200 becoming *landed* attacks
rather than merely avoided ones, and because the tower count doubling needs
patterns to actually complete — which only effect (2) delivers. **I have been
wrong twice today about what drives this change**, so this prediction is worth
exactly what the last two were until it is measured.

**This does not run yet.** Iteration 23's peer gate is still playing, and running
an ablation on a candidate that has not been accepted would be spending shared VM
time on a question that might not arise.

# ITERATION 23 — ACCEPTED

Run `20260907-194028` complete: **118/150 (78.7%)**, 25 maps, both sides.
Baseline is the accepted `alice_iter22`. Uncertainty by map resampling.

| opponent | role | score | se | 95% CI | vs null | swept W/L | per-map histogram |
|---|---|---|---|---|---|---|---|
| **`alice_iter22`** | **accept gate** | **34/50 (68%)** | 2.39 | **[30, 39]** | **+3.77 sd** | **9 / 0** | `{1:16, 2:9}` |
| `alice_flood` | peer | **44/50 (88%)** | 2.54 | [39, 48] | +7.47 sd | 20 / 1 | `{0:1, 1:4, 2:20}` |
| `alice_iter7` | peer | **40/50 (80%)** | 2.84 | [34, 45] | +5.29 sd | 16 / 1 | `{0:1, 1:8, 2:16}` |

### Every gate

1. **Head-to-head > 50%** — 68%, **+3.77 sd**, lower CI bound 30 > null 25.
2. **Peer `WinPct` >= 60%** — 88% and 80%. Both peers also **rose** against
   iteration 22's readings (76% → 88%, 74% → 80%), which is a second, independent
   sign the change is real rather than a baseline artifact.
3. **Diff shape** — **zero swept losses against the baseline**: the per-map
   histogram `{1:16, 2:9}` has no `0` entry at all, so **there is no map on which
   this change loses from both sides.** The two swept losses in the whole run
   (`yearofthesnake` vs `flood`, `starburst` vs `iter7`) are on different maps
   against different opponents, unrepeated — churn, not regression.
4. **Mechanism** — refused pattern attacks 0 by construction; **landed** attacks
   up (53 vs 42 at r200, 28 vs 15 at r400, 1 vs 0 at r700). Gate met.
5. **Price watch** — **0 exceptions in 150 games**, no `OVR=` anywhere, bytecode
   787–824 of 17,500. The shared tower-paint pool did not collapse; it ran
   **3–7x larger** than the baseline's all game.
6. **Frozen roster** — run one hour ago at accept #10 and up on every point.
   Iteration 23 is accept #11; the every-~5 schedule does not call for another,
   and the margin here (+3.77 sd) is not the thin one doctrine #9 reserves the
   pre-accept roster run for.

### What was accepted

One clause: `if (t.getPaint().isEnemy()) continue;` in the ruin-pattern loop. The
engine debits 5 paint at `soldierAttack` offset 58 before it looks at the target
and refuses enemy-painted tiles at 207, so the old code paid for a no-op, `break`ed
(forfeiting that turn's area paint too), and returned to the identical tile next
turn until the soldier starved. Per the whole-build audit, **this was the last
instance of that trap in the shipping code.**

### What I got WRONG along the way, kept in the record

- **Pre-registered density prediction: failed.** I predicted a negative rho on the
  argument that sparse maps give the branch a longer live window. Observed
  **+0.318, p = 0.127** — wrong sign, and a null.
- **The post-hoc replacement also failed.** The tower-conversion story predicted
  absolute ruin *count* should be the better predictor; it scored **+0.104,
  p = 0.640**, worse than the variable it replaced. Map area: −0.116, p = 0.606.
- **There is no map-level covariate structure in this result at all**, which is
  the same fact as "swept 9, lost 0": it works everywhere, uniformly.

The mechanism attribution therefore remains **open**, and the separating
experiment is built and pre-registered: `src/alice_i23abl`, one keyword different
(`break` vs `continue`), isolating "stop paying" from "scan onward".

### Post-accept routine (this commit)

Snapshot `src/alice_iter23/`, compile-verified by a real match;
`progress/cumulative_iterations.png` redrawn (**11 accepted iterations,
iter0..iter23**); replay archived as
`replays/iter23_alice_iter22_UnderTheSea_A.bc25` — the game carrying 18 towers vs
9 and the 3–7x tower-paint pool. The vs-old-bots history is unchanged because no
roster opponent played this run; that is correct, not an omission.

### Pool classification

Peers: `alice_iter23` (new baseline), `alice_iter7` (80%), `alice_flood` (88%).
**`alice_flood` is now within 2 points of the 90% peer ceiling** — but it is in
`progress/roster_extra.txt` as a permanent yardstick and is never retired. If it
crosses 90% its value becomes trend-tracking rather than gating, and the peer pool
will need a new archetype. Flagging that now, before it happens.

## Iteration 23 ablation LAUNCHED — run `20260907-202412`, 100 games

Earned by the accept, and pre-registered before it started. `BOT=alice_i23abl`
(the `break` variant), opponents `alice_iter22` and `alice_iter23`, 25 maps, both
sides.

Three arms differing by **one keyword**, so there is no question what was gated:

| arm | clause | effects carried |
|---|---|---|
| `alice_iter22` | *(absent)* — pays 5 for a refused attack, then `break`s | neither |
| `alice_i23abl` | `if (isEnemy()) break;` | (1) stop paying |
| `alice_iter23` | `if (isEnemy()) continue;` | (1) + (2) scan onward |

**Readings, fixed now:**
- `i23abl` vs `iter22` → the price of **effect (1)**, stopping the refused payment.
- `i23abl` vs `iter23` → **inverse** of effect (2). `iter23` should win it if
  scanning onward is worth anything; a 25/50 split means effect (2) is worth zero.
- **Additivity check**: effect(1) + effect(2), measured as deviations from the
  25/50 null, should reconstruct iteration 23's observed **+9** (34/50 vs
  `iter22`). **If they do not sum, something is interacting that I have not
  named** — which per the 2x2 experience is the more valuable outcome of the two.

**Prediction on record: effect (2) is the larger.** I have been wrong twice today
about what drives this change, so this is worth what those were until measured.

**Why this is the right spend rather than a new iteration.** §5b: *"an ablation
prices a CODE PATH, not a concept"*, and *"two branches that consume the same
budget are two prices"*. Iteration 23 is a single accepted line carrying two
mechanisms, and I have already failed twice to separate them by correlation. If
effect (1) turns out to be worth ~0, then what I actually accepted is a
scan-onward policy and the engine-trap framing — which is currently the headline
of two commits and a shared `tools/engine-facts.md` entry — is the smaller half of
the story. That is worth 100 games to know.

## Binding-algorithm change to absorb: staged evaluation now has a step 3b

`TRAINING_ALGORITHM.md` (`ce8ef36`) adds:

> **3b. If the result holds but your explanation of it fails, accept the result
> and record the attribution as OPEN.** Do not back-fill a mechanism story
> because the number came out well — a plausible account that survives only
> because nobody tested it is worse than an admitted gap, since every later
> iteration will be built on it. [...] Note that no covariate structure and
> "swept everywhere" are often the *same* fact.

`TRAINING_ALGORITHM.md` is binding, so this is a rule I now follow rather than a
compliment I received. Two consequences I am writing down as obligations:

1. **It applies retroactively to what is already in this log.** Iteration 22's
   accept currently carries a confident mechanism sentence — *"the proxy guard
   diverges from the engine's predicate on a saturated map"* — supported by an
   engine probe, a census, and a single-game replay, but **never by a separating
   experiment.** The replay evidence is strong and the engine fact is verified;
   what is *not* verified is that the trap accounts for the +7/+8, rather than
   some other consequence of deleting that branch. Under 3b that attribution is
   **open too**, and I am marking it so. The `alice_i22a`/`i22b`/`i22c` 2x2 priced
   the *branch*, not the *reason the branch was bad*.
2. **The pairing the coordinator recorded cuts both ways for me.** 3b is the
   mirror of "reject a candidate whose mechanism never fired despite a favourable
   score" — my own iteration 20, which engaged hard and bought nothing. Both rules
   refuse to let the win rate imply the story. Iteration 20 was the easy rejection
   to get right; **3b is the hard one, because the number is good and nobody would
   have challenged the story.**

The coordinator's reframe is the part I did not see myself and want recorded in my
own words: **the failed covariate hunt was not a missing result, it was a
consequence of how uniform the result was.** A change that wins on every map
leaves no variance for a map property to explain. I spent two analyses looking for
structure that could not exist given the swept-map count I already had in hand.

**Next measurement**: `20260907-202412` (the one-keyword ablation) is playing, and
it is the instrument that can close iteration 23's attribution. Nothing closes
iteration 22's yet; if the ablation shows effect (1) — stopping the refused
payment — is worth ~0, that is direct evidence bearing on iteration 22's story as
well, since both rest on the same engine trap.

**Tournament**: iterations 22 and 23 are what the 01:00 UTC round-robin measures
against `bob` and `carol` — the only instrument here taken against lineages I did
not produce. Last reading was alice 38.0% overall, 7.3% against `bob`, with `bob`
sweeping 65 of 75 maps. That measurement is on `alice_iter14`; **HEAD is now nine
accepted iterations ahead of what last played.**

## Iteration 22's attribution — CLOSED by exhaustive case analysis, zero games

Step 3b told me to mark it open. Before spending a run on it, I checked whether
the code answers it, and it does. The key fact I had not noticed: the surviving
area branch scans `senseNearbyMapInfos(9)`, which **includes the tile underfoot at
distance 0**, and selects the *nearest* empty tile with a strict `d < paintD`
starting from `1<<30`. So a distance-0 empty tile always wins that selection.

The deleted branch had **no** `isActionReady()` and **no** `paint >= 15` guard, and
ran first. Exhaustive over the four possible states of the tile underfoot:

| tile underfoot | `alice_iter19` (deleted branch present) | iteration 22 (deleted) | net effect of deleting |
|---|---|---|---|
| **ALLY** | guard false, does nothing | area branch paints nearest empty | **identical** |
| **EMPTY**, paint >= 15 | self-paints it, consumes the action; area branch then skipped | **area branch paints that same tile (d = 0)** | **identical — byte for byte** |
| **EMPTY**, 5 <= paint < 15 | self-paints it | area branch gated off by `paint >= 15` → nothing | **deletion LOSES a legitimate paint** |
| **ENEMY** | attacks: 5 paint, engine-refused, nothing painted | area branch paints nearest empty | **deletion GAINS 5 paint and a real tile** |

**There is no third channel.** Two of four states are exactly identical between
the two builds; one is a small loss; one is the engine trap. **The +7/+8 that
iteration 22 measured can only have come from removing the ENEMY case**, because
that is the only state in which deletion is a gain.

That is not a story fitted to a good number — it is a case enumeration over the
code plus one engine fact (`tools/engine-facts.md`), and it is falsifiable: if
anyone shows the area branch can fail to select a distance-0 empty tile, row 2
stops being identical and the argument breaks. I checked the three ways it could:
`canAttack` on one's own tile is true (the deleted branch relied on it), the tile
one stands on is passable, and the strict `<` means no later tile displaces a
d = 0 hit.

**Marking iteration 22's attribution CLOSED**, and noting what closed it: not the
gauntlet, not the replay, and not the census — a decomposition that was available
before any of them. Step 3b says do not back-fill a story; it does not say leave a
question open that reading the code answers.

### And the analysis hands me iteration 24 for free

Row 3 is a **real loss that iteration 22 accepted without noticing**: a soldier
holding 5–14 paint has enough for one attack, is standing on an empty tile, and
now does nothing at all, because the surviving branch's `paint >= 15` gate excludes
it. That gate exists to stop a soldier spending its last paint on distant ground;
it was never meant to forbid painting **the tile it is already standing on**,
which costs no movement and is the cheapest possible target.

`src/alice_i24a`: restore the underfoot paint for exactly that window — tile is
**EMPTY** (the engine's predicate, not a proxy) and the area branch has declined.
Narrow by construction: rows 1, 2 and 4 are untouched.

**Pre-registered**: this fires only on soldiers with 5–14 paint standing on empty
ground. If the decision census shows that state is rare, the candidate is priced
out before it costs a gauntlet — **and I will run that census before the run**,
because "instrument the DECISION, not the outcome" is exactly what saved me from
the splasher.

## Iteration 24 — PRICED OUT before it cost a gauntlet, and it corrects my enumeration

`alice_i24diag` (iteration 23 code plus counters, behaviour unchanged) counts the
**decision**: how often is a soldier action-ready, holding 5–14 paint, and
standing on an **EMPTY** tile — the one case my case analysis said iteration 22's
deletion gave up? UnderTheSea, per-soldier cumulative counts.

| round | soldiers | action-ready turns | in the 5–14 band | **would fire** | in band but underfoot not empty |
|---|---|---|---|---|---|
| 300 | 21 | 1,055 | 43 (4.1%) | **0** | 43 |
| 800 | 32 | 3,276 | 11 (0.3%) | **0** | 11 |

**Across 4,331 action-ready soldier turns, the targeted state occurs ZERO times.**
The paint band itself is rare (0.3–4.1%), and in **every single** band-turn the
tile underfoot was not empty.

The reason is my own saturation finding, which I should have applied before
building: **by round 300 the map is ~90% painted**, so a soldier standing anywhere
is almost never standing on empty ground. The branch is dead on arrival.

**`src/alice_i24a` is discarded. It never plays a gauntlet.** Fourth candidate
killed cheaply today by a pre-check rather than by a run — after the splasher
(deferred on a census), iteration 23's premise (nearly filed dormant on late-game
reachability, saved only by sampling early), and the map-class hypotheses (killed
by tournament data already on disk).

### And it corrects the enumeration that produced it

I wrote that row 3 was *"a real loss that iteration 22 accepted without
noticing."* **Measured: it is zero, not small.** The correction runs in my favour,
which is exactly why it is worth stating explicitly rather than letting it pass:

| row | enumeration said | census says |
|---|---|---|
| EMPTY, 5 <= paint < 15 | "deletion LOSES a legitimate paint" | **the state never occurs — deletion loses nothing** |

So iteration 22's deletion was not a trade of a large gain against a small loss.
**It was a pure removal of the ENEMY-case waste, with the other three rows
contributing exactly nothing.** The attribution I closed by enumeration is now
*stronger* than the enumeration alone could establish — two of four rows are
identical by construction, and the third is empirically empty.

**The lesson is about the enumeration, not the result.** A case analysis tells you
which behaviours *differ*; it says nothing about which of them ever *happen*. I
correctly enumerated four rows and then silently assumed a non-identical row was
frequent enough to matter. **Enumerate the cases, then count them** — the second
half is the reachability pre-check, and I ran it here only because it was a
candidate, not because I thought the enumeration needed it. It did.

## Iteration 23 ablation, arm 1 COMPLETE — my prediction is wrong for the THIRD time

`alice_i23abl` (the `break` variant: **stops paying, does not scan onward**) vs
`alice_iter22`, 50 games, 25 maps, both sides.

| | score | se | 95% CI | vs null | swept W/L | per-map |
|---|---|---|---|---|---|---|
| **`i23abl` vs `iter22`** = **effect (1) alone** | **33/50 (66%)** | 2.72 | [28, 38] | **+2.94 sd** | 9 / 1 | `{0:1, 1:15, 2:9}` |
| `iter23` vs `iter22` = effects (1) + (2) | 34/50 (68%) | 2.39 | [30, 39] | +3.77 sd | 9 / 0 | `{1:16, 2:9}` |

**Effect (1) alone is +8 over the null. The full change is +9. Effect (2) is
therefore worth about +1 game — essentially nothing.**

I predicted: *"effect (2) is the larger."* Wrong. **That is my third failed
prediction about this one change** — the density direction, the ruin-count
replacement, and now the mechanism split. The two effects are not close: the
scan-onward behaviour I measured landing 11 extra pattern tiles at r200 converts
to roughly one game, while simply **declining to pay for a refused action** carries
essentially the whole result.

### What this settles, and it settles it in favour of the framing I was doubting

The engine-trap account is **the** mechanism, not the smaller half. That matters
beyond my own log: it is the framing in the shared `tools/engine-facts.md` entry
and in two of my commit headlines, and I flagged an hour ago that if effect (1)
priced near zero the shared entry would be overstated. **It does not — it prices
at +8 of the +9.** The shared entry stands as written.

Iteration 23's attribution is therefore **CLOSED**: the change works because it
stops paying 5 paint for actions the engine refuses, and the `continue`-versus-
`break` refinement is a rounding error on top of that.

### Two honest caveats on the arithmetic

1. **The +9 comes from a different map sample** (run `20260907-194028`) than the
   +8 (run `20260907-202412`), so subtracting them across runs is exactly the
   cross-run comparison the gauntlet header warns is noisier than it looks. The
   within-run arm — `i23abl` vs `iter23` — is the clean measurement of effect (2)
   and is still playing at 40/50. **I am not calling the additivity check passed
   until it lands.**
2. `i23abl` picks up **one swept loss** where `iter23` had none (`{0:1}` vs no `0`
   entry). One map, so it is not a finding — but it is the only per-map evidence
   that scanning onward does anything at all, and it points the same direction as
   the +1.

### The pattern in my three failures is worth naming

All three predictions shared a shape: **I reasoned from the mechanism I could see
working in a trace, rather than from the mechanism that was expensive.** The
scan-onward effect is *visible* — you can watch a soldier land a pattern tile it
would have missed. The refused payment is *invisible* — nothing happens, 5 paint
disappears, and no trace line records a non-event. **I kept betting on the
mechanism that produces observable events over the one that produces absences**,
and the absence was worth eight times more. That is the same reason the trap
survived 22 iterations in the first place.

## Ablation COMPLETE — and I have to correct the entry I wrote an hour ago

Run `20260907-202412`, both arms, **same 25 maps**, so the two comparisons are
exact against each other.

| arm | score | se | 95% CI | vs null | swept W/L | per-map |
|---|---|---|---|---|---|---|
| `i23abl` vs `iter22` = **effect (1) alone** | **33/50 (66%)** | 2.72 | [28, 38] | **+2.94 sd** | 9 / 1 | `{0:1, 1:15, 2:9}` |
| `i23abl` vs `iter23` = **inverse of effect (2)** | **19/50 (38%)** | 2.55 | [14, 24] | **−2.35 sd** | 1 / 7 | `{0:7, 1:17, 2:1}` |

### CORRECTION: effect (2) is +6, not "+1, essentially nothing"

An hour ago, with only the first arm complete, I wrote that effect (2) was *"worth
about +1 game — essentially nothing"* and headlined a commit *"effect (1) is +8 of
the +9."* **That was derived by subtracting a +8 measured on one map sample from a
+9 measured on a different one — the exact cross-run subtraction I flagged as
unreliable in the same entry, and then reasoned past anyway.**

Measured within-run, `iter23` beats `i23abl` **31/50, sweeping 7 maps to 1**:

| | within-run value |
|---|---|
| effect (1) — stop paying for engine-refused attacks | **+8** |
| effect (2) — scan onward to a paintable tile | **+6** |

My *prediction* is still wrong — I said effect (2) was the larger and it is not
(6 < 8) — but "essentially nothing" was wrong by six games, and it was wrong for a
reason I had already written down. **This is the density-gradient failure again in
a new costume: I flagged the uncertainty and then used the number anyway**, when
the instrument that resolved it was already running.

Superseding the earlier entry in place: **both effects are real and comparable in
size.** The engine-trap framing remains the larger half and `tools/engine-facts.md`
stands, but "the `continue`-versus-`break` refinement is a rounding error" is
retracted.

### The pre-registered additivity check FAILS, which is the outcome I said was more valuable

```
effect (1) + effect (2)  =  +8 + 6  =  +14
observed whole (iter23 vs iter22)   =   +9
                    additivity gap  =   +5 games, sub-additive
```

I pre-registered: *"If they do not sum, something is interacting that I have not
named — which is the more valuable outcome of the two."* They do not sum.

**But I am not calling it established, for the reason that just bit me.** The
+14 is measured on run `20260907-202412`'s maps; the +9 comes from run
`20260907-194028`'s different sample. Combining the standard errors
(2.72, 2.55, 2.39) puts the gap at roughly **1.1 sd — suggestive, not significant.**
I refuse to make the same cross-run mistake twice in one evening.

**So I am measuring the whole on the parts' own maps.** Run `20260907-205244`
launched: `alice_iter23` vs `alice_iter22`, **`MAPS` pinned to
`gauntlet/20260907-202412/maps.txt`**, 50 games. That makes all three comparisons
exact within one map sample and turns the additivity check from an estimate into
an arithmetic identity.

**Mechanistic prediction, recorded before it lands**: I expect the gap to survive,
because the two effects are **partial substitutes** — both convert the same wasted
soldier-turn into a productive one, so whichever fires first takes the credit and
the second has less left to fix. If that is right, the whole should land near +9
on the pinned maps rather than near +14. Given my record on this change (three
predictions, three wrong), that is worth exactly nothing until measured.

## Binding-doctrine change to absorb: measurement doctrine 6

`TRAINING_ALGORITHM.md` (`4910885`) adds, from my failure this evening:

> **6. A flagged caveat is not a discharged one.** [...] When you flag a
> comparison as unsound, either stop using it or say explicitly what you are
> spending the unsoundness on. The remedy is usually cheap: re-measure the whole
> on the parts' own pinned maps and the comparison stops being an estimate and
> becomes an arithmetic identity.

Two obligations I take from it, beyond not repeating the specific error:

1. **Audit my own log for other flagged-but-used comparisons.** I have written
   "suggestive, not decisive" and similar hedges several times today. Doctrine 6
   says each of those is a debt, not a payment. Sweeping them:
   - *"iteration 22's density gradient, suggestive at ~1.5 sd"* — **used**, then
     **retracted** when I finally computed the rank correlation. Discharged, late.
   - *"partial arm at 22/31, not evidence yet"* — flagged and **genuinely not
     used**; I waited for the complete 50. Clean.
   - *"the tower-channel story agrees with the density sign"* — **used**, then
     retracted the same hour when ruin count failed. Discharged, late.
   - *"effect (2) is about +1"* — **used**, headlined a commit, corrected at +6.
     The one that produced this doctrine.
   **Three of four hedges were spent rather than discharged.** The pattern is not
   occasional; it is my default, and the only ones I caught were the ones where a
   cheap resolution happened to be available.
2. **The remedy the doctrine names is one I should reach for first, not last.**
   Pinning `MAPS` to a prior run's `maps.txt` costs one 50-game run and converts
   an estimate into an identity. It was documented in my own `AGENT.md` from the
   start — *"pin `MAPS` to replay a run's exact maps, which is what you want for a
   regression check, an ablation, or chasing one map"* — and this is an ablation.
   **I had the remedy written down, in my own charter, and reached for a
   subtraction instead.**

Run `20260907-205244` is that remedy, in flight.

### Scope of my retraction, stated precisely

The coordinator is right to flag the boundary, so I am marking it explicitly:
**the retraction covers only the `continue`-versus-`break` characterisation**
("a rounding error" — false; it is +6). It does **not** touch the engine trap
itself, which is verified by decompilation, re-derived independently by the
coordinator before promotion, and recorded in `tools/engine-facts.md` with the
command that re-derives it. Effect (1) at +8 remains the larger half.

## Next target selection — the soldier-paint area is mined out, and I should leave it

**Functional-area tracker.** Iterations 19, 20, 22 and 23 all sit in **soldier
paint spending**: 19 accept, 20 reject, 22 accept, 23 accept. `MaxConsecutiveRejects`
is 3 and I have no reject streak, so the formal rule does not force me out. I am
leaving anyway, for a reason stronger than the rule:

**The area is measurably exhausted.** The whole-build engine-predicate audit
enumerated every call site that can spend paint on a refused action and found
exactly one remaining — the ruin-pattern loop — which iteration 23 fixed. There is
no third instance to find. The area did not run out of ideas; **it ran out of
defects, and I can name the audit that proves it.** That is a much better reason
to move than a reject counter.

### What the evidence on disk says to do next, ranked

1. **Communication** — `sendMessage` / `readMessages` / `broadcastMessage`, **zero
   calls in 23 iterations.** The largest unexplored capability I own, and my own
   saturation finding removes the constraint that normally makes BC25 comms
   awkward: robot↔tower messaging needs a 4-adjacent ally-paint path, and my
   territory is one contiguous painted mass from round 250–600 onward. Towers also
   broadcast at r²<=80 with no connectivity requirement, and I field 11–18 of them.
2. **Saturation-responsive spawn mix** — the tower spawns a fixed 75/25
   soldier/mopper split for all 2,000 rounds, chosen when the map was empty; the
   map is ~90% painted by round 300. Needs a dose with a zero arm, a
   self-calibrating threshold (the saturation round is 250 on one map and 600 on
   another, so a round constant is exactly the tuned constant this project keeps
   finding inferior), and **tower-paint instrumentation in the first run**, because
   §3c's absorbing state came from moving this very mix.
3. **`mopSwing`** — never called; 6 tiles, −5 paint per enemy robot, cooldown 20
   against the ordinary mop's 30. Attractive because **65–100% of deaths in this
   game are paint starvation**, so draining enemy paint is the direct cause of how
   units die rather than a metric needing conversion. Priced honestly: a swing does
   no ground work, and ground work is what iteration 19 accepted.

### The pre-check that must run before any of them

Today killed four candidates for free — the splasher (census), iteration 23's
premise (nearly filed dormant on late-game reachability, saved only by sampling
early), the map-class hypotheses (tournament data already on disk), and the
underfoot restore (decision census, zero occurrences in 4,331 turns). **Every one
of those was killed by counting a decision, not by running a gauntlet.**

So whichever of the three I take, the first artifact is a diagnostic build that
counts the decision, and the gauntlet is spent only if the count justifies it.
For comms that means: **how often is a robot within r²<=20 of an ally tower AND
paint-connected to it?** If that is rare the whole direction is priced out before
a schema is designed — and given saturation I expect it to be common, which is
exactly the kind of expectation that has been wrong three times today.

**Nothing starts until `20260907-205244` lands.** It is the arithmetic identity
that settles whether iteration 23's two effects are sub-additive, and starting a
new thread while an open question has a run in flight is how the flagged-caveat
failure happened in the first place.

## Resumption state — one run in flight

**`20260907-205244`** — `BOT=alice_iter23`, opponent `alice_iter22`, **`MAPS`
pinned** to `gauntlet/20260907-202412/maps.txt`, 50 games. Launched 20:52 UTC,
setsid-detached so it survives this session. At 15/50 and slow; the shared VM is
heavily contended (all three lineages active).

**A fresh session: do NOT re-run it.** `../../tools/gauntlet-collect.sh --list`,
then `../../tools/gauntlet-collect.sh 20260907-205244` if it shows complete.

### What it decides, and the arithmetic waiting for it

Everything else in the ablation is already measured on **these same 25 maps**:

| quantity | value | status |
|---|---|---|
| effect (1), stop paying for refused attacks (`i23abl` vs `iter22`) | **+8** | measured, complete |
| effect (2), scan onward (`i23abl` vs `iter23`) | **+6** | measured, complete |
| **the whole** (`iter23` vs `iter22`) | **pending** | this run |

Sum of parts is **+14**. If the whole comes back near **+14**, the effects are
additive and my substitutes hypothesis is refuted. If near **+9** (its value on a
different map sample), they are **sub-additive by ~5 games** and the two mechanisms
are partial substitutes — both convert the same wasted soldier-turn, so whichever
fires first takes the credit.

**Prediction on record: sub-additive, whole near +9.** My record on this change is
three predictions, three misses, so this is a coin flip with a story attached.

**Read it as an identity, not an estimate.** All three comparisons are on one
pinned map sample, which is the whole point of the run and the remedy measurement
doctrine 6 names. Do not subtract across runs to get an answer sooner — that is
the exact failure this run exists to repair.

### If it lands sub-additive

That is a real interaction inside a single accepted line, and §5b's warning
applies directly: *"a marginal accept is an unpriced liability against every
feature you have not written yet."* Neither effect here is marginal, but a pair
that overlaps by 5 games is a pair whose *individual* prices overstate their joint
value — worth knowing before anything else is built on top of them.

### If it lands additive

Then the +9 I measured on run `20260907-194028`'s maps was a low draw, iteration
23 is worth closer to +14, and the accept is stronger than recorded. **I would owe
an upward correction**, and by today's own audit — three of four hedges spent
rather than discharged — upward corrections are the ones I am least likely to
make unprompted. Writing that down now so it gets made.

## NEW BINDING CONSTRAINT — BC25 finals benchmark bots are a yardstick, not an instrument

From the project owner, effective immediately. Recorded at the **top** of
`AGENT.md` as well, because that is what a fresh session reads first and this must
not be discovered late.

- **Never read their code.** Never in this repo.
- **Never examine any game played against them** — no replays, logs, traces,
  dumps or per-game reasons. Do not seek them out, request them, or reason from
  them.
- **I do not run these matches.** The coordinator does; records are destroyed once
  scores are extracted.
- If a benchmark score lands in a committed results file, I may read **the score
  and nothing else**.
- **If I ever find myself holding such an artefact, stop and tell the
  coordinator.**

### What this changes in my own practice, concretely

Three of my habits point straight at the forbidden artefacts, so I am naming them
rather than trusting myself to remember:

1. **Replay dumping.** My first move on any interesting result today was
   `../../tools/replay-dump.sh` on a `.bc25`. That reflex must not fire on a
   benchmark game. **Rule I am adopting: only dump replays I produced myself** —
   files in my own `matches/` or `replays/`, from runs whose `bot.txt` I wrote.
2. **Tournament `reasons.txt` mining.** I read win-reason text and per-map
   outcomes out of `tournaments/*/` twice today, and both were genuinely valuable.
   If benchmark rows ever appear there, **the score column is readable and the
   per-game reason column is not**, for those rows only.
3. **Opponent pool and roster.** A benchmark never enters `OPPONENTS`, never
   enters the frozen roster, never enters `progress/roster_extra.txt`. It is not a
   peer, not a benchmark in the *pool* sense the algorithm defines, and beating it
   is not an accept criterion.

### Why this is not a loss

It costs me nothing I was using. `TRAINING_ALGORITHM.md`'s standing constraints
already forbid downloaded bot implementations and current-year post-mortems, and
the whole opponent-pool design exists *because* no external instrument was
available. My instruments are unchanged: my own gauntlet, the frozen roster —
which is what actually measures absolute progress here — and the twice-daily
inter-agent tournament.

And it removes a temptation the algorithm already warns about. A single external
number is exactly the kind of instrument a lineage starts optimising against, and
optimising against one opponent is how you acquire a weakness that opponent does
not punish. **The benchmark tells me how far I have to go; it does not tell me
what to do**, and I should not pretend otherwise even to myself.

I am also noting the symmetry: the rule is the same isolation that keeps me out of
`bob`'s and `carol`'s workspaces, and I have kept that one all session — the only
cross-agent evidence I used is `tournaments/`, which is the sanctioned channel.

# ADDITIVITY IDENTITY CLOSED — and it is a measured non-transitivity

Run `20260907-205244` complete. All three comparisons now sit on **one pinned
25-map sample**, so the arithmetic below is an **identity, not an estimate**.

| comparison | score | se | 95% CI | swept W/L | value |
|---|---|---|---|---|---|
| `i23abl` vs `iter22` — **effect (1)**, stop paying | 33/50 | 2.72 | [28, 38] | 9 / 1 | **+8** |
| `iter23` vs `i23abl` — **effect (2)**, scan onward | 31/50 | 2.55 | [26, 36] | 7 / 1 | **+6** |
| `iter23` vs `iter22` — **the WHOLE** | **33/50** | 2.74 | [28, 38] | **9 / 1** | **+8** |

```
effect (1) + effect (2)  =  +8 + 6  =  +14
the whole                            =   +8
                  ADDITIVITY GAP     =   +6      STRONGLY SUB-ADDITIVE
```

**My prediction was right** — sub-additive, whole near the +8/+9 range, not +14.
First correct prediction I have made about this change after three consecutive
misses. I am recording that it was *one* correct call inside a run of four, not a
recovery of calibration.

### The whole is not merely close to effect (1) — it is INDISTINGUISHABLE from it

`iter23` vs `iter22` scores **33/50, swept 9/1**. `i23abl` vs `iter22` scores
**33/50, swept 9/1**. Identical on every summary statistic. Aggregates can
coincide by accident, so I ran the deterministic cell check this project's own
§4 prescribes — counting the `(map, side)` cells on which two builds disagree:

```
50 cells compared.  6 disagree (12%).
  iter23 wins where i23abl loses:  Oasis B, Racetrack A, headphones A   (3)
  i23abl wins where iter23 loses:  Barcode A, SMILE B, mit B            (3)
```

**Six scattered, mixed-direction flips, split exactly 3–3 across six different
maps.** That is the churn signature doctrine #10 defines, not a causal effect.
**Against `alice_iter22`, the `continue` is not "worth a little" — it is worth
nothing, and the diff shape proves it rather than the aggregate merely failing to
detect it.**

Yet against `i23abl` the same clause scores 31/50 while sweeping **7 maps to 1** —
concentrated and one-directional, which is exactly what a real effect looks like.

### So this is a genuine, measured non-transitivity

```
i23abl  beats  iter22   by +8
iter23  beats  i23abl   by +6
iter23  beats  iter22   by +8     (not +14)
```

Not a contradiction and not noise — **matchup structure**. Effect (2) helps
specifically against an opponent that has *already* fixed the engine trap, and
buys nothing against one that has not. Mechanistically that is coherent: scanning
onward to a paintable pattern tile only matters when your opponent is also
converting patterns efficiently and the race is tight; against a bot bleeding
5 paint per refused attack, the race is not close enough for the refinement to
change an outcome.

### This is §5b's "partial derivative" made concrete, and it is worth more than the accept

§5b warns that the head-to-head accept gate *"measures a candidate's marginal
value conditional on everything the baseline already carries"* and that a chain of
individually-positive accepts can therefore walk downhill. **Here is that
conditionality measured directly, at cell level, in a single line of code**: a
feature worth +6 against my immediate predecessor is worth **exactly 0** against
the generation before it.

The transferable rule: **head-to-head margins do not chain.** "A beat B by 8" and
"C beat A by 6" does not license "C beats B by 14", and the only way to know is to
play C against B on the same maps. This is precisely why the **frozen roster**
exists and why a head-to-head chain cannot substitute for it.

### Decisions

1. **Iteration 23's accept STANDS.** +8 over `iter22` on the pinned sample,
   consistent with the 34/50 (+9) that accepted it on an independent sample.
   Nothing here weakens the accept; what it revises is the *attribution*.
2. **Attribution, final**: iteration 23's value over `alice_iter22` is
   **entirely effect (1)** — declining to pay 5 paint for an engine-refused
   action. The engine-trap framing in `tools/engine-facts.md` is not just the
   larger half, it is the whole of the improvement against the previous build.
3. **The `continue` stays in the shipping bot**, and I want the reason on record
   rather than assumed: it beats `i23abl` head-to-head 31/50 sweeping 7 maps, the
   accept gate is a head-to-head against the most recent accepted snapshot, and it
   costs nothing measurable in bytecode. It is carried as **insurance against
   opponents who fix their own trap**, not as a contributor to today's margin.
4. **Superseding my "essentially nothing" retraction, again, and more precisely.**
   Effect (2) is +6 against a trap-fixed opponent and **0 against `iter22`**. My
   original "+1, essentially nothing" was wrong about the mechanism and
   accidentally close about the number *in the matchup that produced it*. Neither
   the claim nor its retraction was right; the truth is matchup-dependent, which
   is a thing neither version of me had considered.

## Comms pre-check — the channel is REACHABLE, and connectivity costs almost nothing

`alice_commcensus` (iteration 23 code plus counters; sends nothing, behaviour
unchanged) counts the decision using **the engine's own `rc.canSendMessage(loc)`**
rather than my reconstruction of "within r²<=20 and paint-connected". Today's whole
lesson, applied prospectively: a proxy for an engine predicate diverges exactly
when the board state shifts, and connectivity *is* a board-state property.

Two maps, deliberately at opposite ends of the density table:

| map | round | robot turns | tower in vision | **CAN SEND** | of tower-in-vision turns, sendable |
|---|---|---|---|---|---|
| **UnderTheSea** (45x45, **median** density 11.4) | 300 | 1,163 | 55.3% | **53.0%** | **95.8%** |
| | 800 | 3,960 | 66.3% | **65.4%** | **98.7%** |
| DefaultSmall (20x20, density 20.0 — dense, small) | 200 | 576 | 69.1% | 63.9% | 92.5% |
| | 500 | 200 | 89.0% | 79.5% | 89.3% |
| | 880 | 439 | 89.1% | **89.1%** | **100.0%** |

### The finding, and it is the one I predicted

**The paint-connectivity requirement — normally the awkward part of BC25 comms —
costs almost nothing here: 96–99% of turns that have a tower in vision can also
send to it**, rising to 100% late on the small map. The binding constraint is
plain **range** (r²<=20 to a tower), not connectivity.

That is exactly what my saturation finding predicted: my territory is one
contiguous painted mass from round 250–600 onward, so a 4-adjacent ally-paint path
from a robot to a nearby ally tower almost always exists. **A constraint I would
otherwise have had to engineer around is already satisfied by the board state I
measured this afternoon.**

And the channel is available on **the majority of robot turns** — 53% at r300 and
65% at r800 on the median map, rising through the game. With 1 message/turn per
robot and 2–3 towers simultaneously in range, throughput is not the limit either.

**I checked the flattering map second, on purpose.** DefaultSmall is 20x20 at
density 20.0 — small and dense, so towers are near everything, and it reads
higher (up to 89%). Money taught me that lesson this afternoon at a cost; the
median-density map is the number to quote and it is 53–65%.

### What this does and does NOT establish

**Does**: the direction is not priced out. Unlike the splasher, the underfoot
restore, the map-class hypotheses and iteration 23's late-game premise — four
candidates killed cheaply today — this one survives its pre-check. **It is the
first green light of the session**, and I note that a pre-check regime that only
ever says no would be a broken regime.

**Does not**: reachability is not value. This says a message *can* be sent on most
turns; it says nothing about whether there is anything worth sending. That is a
design question, and the honest next step is not to build a schema but to name a
**specific decision my bot currently makes badly for lack of information**, then
check that the missing information is something a tower could actually supply.
Building a comms layer because the channel is open is exactly the "capability
looking for a use" shape that this project's ledger is full of.

**Candidate decision to attack, recorded now so it can be tested rather than
assumed**: soldiers find ruins by random walk within vision (`WANDER_RUN = 25`
ballistic), and the tournament shows `bob` reaching 14–15 towers by round 160 on
`gridworld` while this lineage stalled at 5–6. A tower knows where its own
completed patterns are and could broadcast "claimed" so soldiers stop converging
on ruins another soldier is already finishing. **Whether soldiers actually collide
on ruins is a countable quantity I have not counted** — and by today's consistency
pass, that count is the next artifact, not the schema.

## Resumption state — two things in flight

### 1. `20260907-211852` — the frozen roster on `alice_iter23` (300 games)

`BOT=alice_iter23` against the full roster `alice_iter0 / iter1 / iter4 / iter7 /
iter12 / alice_flood`, 25 maps, both sides. At 93/300. **Recover with
`gauntlet-collect.sh`, never re-run.**

**Why it is running**, in one line, and it is my own result that forced it:
**head-to-head margins do not chain**, so "iteration 23 beats iteration 22 by +8"
says nothing about where iteration 23 *stands*. The roster last saw the iteration
22 candidate; this build has never been measured against a fixed opponent.

Comparison table to fill in — the iteration 22 candidate's readings, so the delta
is the thing to read:

| frozen opponent | iteration 22 candidate | iteration 23 |
|---|---|---|
| `alice_iter0` | 100% | **100% (50/50, complete)** |
| `alice_iter1` | 100% | 100% so far (43/43) |
| `alice_iter4` | 98% | — |
| `alice_iter7` | **74%** | — |
| `alice_iter12` | **92%** | — |
| `alice_flood` | **76%** | — |

The three bolded rows are the ones with resolution; `iter0`/`iter1` are at ceiling
and can only confirm nothing broke. **Record the result with
`track_vs_old_bots.py <run>` and redraw both charts** — that is the post-accept
routine's roster half, which iteration 23 has not yet had.

### 2. `alice_ruincensus` — the count that must precede any comms schema

Built and queued behind the roster (one match, UnderTheSea). Reports each
soldier's **current ruin target** every turn; the counting happens **offline
across soldiers from the replay**, because a soldier cannot see another soldier's
target and doing it in-bot would be the instrument inventing its own answer.

**Pre-registered readings**, before it lands:
- For each round, group soldiers by target ruin. **If the modal group size is 1,
  soldiers are not colliding and the coordination hypothesis is dead** — the comms
  channel being reachable would not matter, and I would need a different use for
  it before spending anything.
- If groups of 3+ are common while other unclaimed ruins sit unworked, the
  hypothesis survives and the schema becomes worth designing.

**Prediction on record: collisions are common.** My calibration today is four
predictions, one hit — so this is worth nothing until counted, and I am writing it
down only so it cannot be adjusted afterwards.

**The discipline this enforces**: the comms channel is *reachable* (53–65% of
turns), which is a fact about the channel and not a reason to build anything.
**Reachable is not useful.** This count is what decides whether there is a
decision worth informing, and it costs one match against a 300-game gauntlet if I
guessed wrong.

## Ruin-collision census — the hypothesis is DEAD, killed by its own falsifier

`alice_ruincensus` reports each soldier's current ruin target; grouping done
offline across soldiers from the replay. UnderTheSea.

| round | soldiers | **no target** | targeting | distinct ruins | soldiers-per-ruin | largest group |
|---|---|---|---|---|---|---|
| 200 | 9 | 4 | 5 | 3 | `{1:1, 2:2}` | 2 |
| 300 | 21 | **13** | 8 | 3 | `{2:2, 4:1}` | 4 |
| 500 | 37 | **24 (65%)** | 13 | **3** | `{2:1, 5:1, 6:1}` | **6** |

### My pre-registered reading passes — and it is the wrong question

I pre-registered: *"modal group 1 → hypothesis dead; groups of 3+ common → schema
worth designing."* Groups of 3+ appear at r300 and r500, so **by the letter my
hypothesis survived and my prediction (collisions are common) was correct.**

It is still dead, because the number that matters is one I did not pre-register:
**65% of soldiers have no ruin target at all**, and the 13 that do are piled onto
**3** ruins.

### The falsifier I ran before claiming a dispatch opportunity

The obvious story — *"tell the idle 65% where the unworked ruins are"* — requires
unworked ruins to exist. Checking, from the same replay's own header and counters:

```
UnderTheSea: 27 ruins (engine header)
round 500:   T1 15 towers + T2 9 towers = 24 towers
             => 27 - 24 = 3 ruins unclaimed
```

**Soldiers were targeting exactly 3 distinct ruins. That is every unclaimed ruin
on the map.** The 24 soldiers with "no target" are not mis-dispatched — **there is
nothing left to dispatch them to.** And 5–6 soldiers per remaining ruin is not
waste either: the paint census put the ratio at **6–18 soldiers per completed
tower**, so those groups are, if anything, undersized.

**The coordination/dispatch use-case for comms is refuted.** Not "unsupported" —
refuted, by an arithmetic identity between towers, ruins, and targets.

### Third instance today of the same failure, and it is mine

I pre-registered two readings and **both were about collisions**. Neither asked
"how many targets exist to distribute". So this is the session's own theme —
*a valid analysis silent about frequency* — committed one more time, in the very
pre-registration written to prevent it. The generalised rule from this morning's
consistency pass says: when an argument turns on "this situation matters", the
next sentence must be a count. **I counted the collisions and not the supply.**

The saving grace is structural rather than personal: **the falsifier was one line
of arithmetic on data already in the replay**, and I ran it before writing a
schema. Cost: one match. That is the fifth candidate killed by a pre-check today.

### Where this leaves comms

The channel is reachable (53–65% of turns, connectivity nearly free) and **has no
use I can currently justify.** Recorded as **open and unpriced**, not closed — the
same status as the splasher, and for the same reason: I have refuted one
application, not the capability. Any future comms proposal must name a decision,
show the decision is made badly, **and show the information that would fix it
exists somewhere a tower can see.** This one failed the third test.

### Tooling note for the coordinator — a ruin-count discrepancy worth documenting

`tools/mapdata/ruin_parity.txt` lists **UnderTheSea ruins=23**; the shared
dumper's `MatchHeader` reads **ruins=27**. The gap is exactly **4**, which is the
number of towers on the board at spawn (2 per team) — so both are almost certainly
right and counting different things: **27 ruin tiles total, 4 pre-occupied at
spawn, 23 claimable.**

Not a bug, but it changed a number I published today: I called UnderTheSea "the
corpus median at 11.4 ruins/1000" using the 23 figure, where the all-ruins figure
is 13.3. **Both densities are defensible; which one `ruin_parity.txt` reports
should be stated in the file**, since it is shared ground and the two support
different claims.

## The roster chart and the drift check want DIFFERENT map policies — I had been conflating them

Noticed while watching `20260907-211852` fill in against iteration 22's readings.
`iter0` 100→100, `iter1` 100→100, `iter4` 98→98 so far — but **these two runs used
different random 25-map draws**, so every delta in that column is an estimate with
map-draw noise in it, not an identity.

That is a direct application of the lesson I was handed tonight (doctrine 6) to an
instrument I have been reading all day without noticing:

| purpose | right map policy | why |
|---|---|---|
| **the roster CHART** — long-run absolute trend | **fresh random draw each run** | a fixed list is an overfitting surface; accepted iterations would drift toward it. This is `AGENT.md`'s stated reason and it is correct. |
| **the DRIFT check** — "is accept N worse than accept N−1 against a common ancestor?" | **pinned to the previous roster run's maps** | it is a *difference between two builds*, and a difference measured on two different samples is an estimate. Pinned, it is an identity. |

**I had been treating one instrument as both.** The chart's fresh-draw policy is
right for the chart and wrong for the drift question, and the drift question is
the one §5b actually cares about — it is the reason another lineage's newest
accept turned out to be 6 games *worse* than its predecessor against their common
ancestor tonight, a result that is only trustworthy **because it was same-sample**.

### What I am doing about it

The run in flight stays as it is: it is a legitimate **chart** point on a fresh
draw, and that is what `track_vs_old_bots.py` wants.

If it shows any drop on the three rows with resolution (`iter7` 74%, `iter12` 92%,
`alice_flood` 76%), the confirmation is a **pinned** re-run of those three against
`gauntlet/20260907-181936/maps.txt` — iteration 22's exact roster maps — which
turns the iter22→iter23 delta into an arithmetic identity. 150 games, and I only
spend them if the fresh draw says there is something to confirm.

**Pre-registering the decision rule now**, so a drop cannot be explained away as a
map draw afterwards and a rise cannot be banked without the same scrutiny:

- **Any resolving row down by more than ~5 points → run the pinned check.** Do not
  attribute it to the draw; that is precisely the move doctrine 6 forbids.
- **All rows flat or up → no pinned run.** Record the chart point and move on,
  noting explicitly that "flat on a fresh draw" is weaker evidence of no-drift
  than "flat on pinned maps" would be, and that I am accepting the weaker evidence
  because the stronger costs 150 games I have no positive reason to spend.

That second bullet is the one I would normally leave unsaid. **A null result on a
noisy instrument is not the same as a null on a precise one**, and the asymmetry —
spending games to confirm bad news but not good news — is a bias I am choosing
deliberately rather than falling into, and it belongs on the record either way.

---

# SESSION RESUMED — the roster run survived, its collation did not

Session died between launching `20260907-211852` and reading it. Exactly the
casualty `gauntlet-collect.sh --list` exists to catch: the run itself is
**complete** (300 games, setsid-detached, unaffected by my death) and had even
been pulled back to `gauntlet/`, but `track_vs_old_bots.py` had never been run
on it, so the durable record — `progress/vs_old_bots_history.csv` — was missing
the point entirely. Recovered without replaying a single game.

## The iteration 23 roster point, against my pre-registered decision rule

| opponent | iter22 run `181936` | **iter23 run `211852`** | delta |
|---|---|---|---|
| alice_iter0 | 100% | 100% | 0 |
| alice_iter1 | 100% | 100% | 0 |
| alice_iter4 | 98% | 98% | 0 |
| alice_iter7 | **74%** | **94%** | +20 |
| alice_iter12 | 92% | 96% | +4 |
| alice_flood | **76%** | **92%** | +16 |
| overall | — | 290/300 (96.7%) | — |

I pre-registered before the run: *any resolving row down by more than ~5 points
→ pinned re-run on iteration 22's exact maps; all rows flat or up → record the
point and move on.* **Every row is flat or up. No pinned drift run.** §5b's
downhill-walk failure mode is not showing here.

### But I am explicitly NOT banking the rise

The rule I wrote committed me to spending 150 games to confirm bad news and none
to confirm good news, and I called that a deliberate bias at the time. It has now
been cashed, so the consequence has to be stated rather than enjoyed: **the two
big movers (+20 on `iter7`, +16 on `alice_flood`) are cross-run deltas on
different random 25-map draws, which doctrine 6 says is an estimate, not an
identity.** An unknown part of both is map draw. I have not measured how much and
I am not going to, so the honest claim is **"no drift, and possibly a real gain
of unknown size"** — not "+20 against iter7".

This is the comfortable correction doctrine warns about: the direction that
runs in my favour is the one least likely to get audited. Flagging it costs
nothing and keeps the number from hardening into a fact by repetition.

The three rows still at 98–100% (`iter0`, `iter1`, `iter4`) have no resolution
left and gate nothing; `iter7`, `iter12` and `alice_flood` are the instrument now,
and `alice_flood` at 92% is approaching the same ceiling.

## Tournament `20260907-1300` — read, with the caveat that it played STALE code

Standings: bob 92.3%, **alice 38.0% (+2.7)**, carol 19.7%. Head-to-head
**alice–bob 7.3%**, alice–carol 68.7%. Swept maps alice–bob: **alice 1, bob 65.**

The line that matters for how much weight this carries:

```
alice @ 688a75b  "ACCEPT iteration 14 -- wander slides along obstacles"
```

**The tournament exported iteration 14. I am on iteration 23.** Nine accepts —
including everything from the engine-predicate finding onward — are not in that
number. So the 7.3% against bob is a real measurement of a build I no longer run,
and I should neither despair at it nor discount it: it is the last *external*
reading I have, and the next tournament (01:00 UTC, ~2h) exports iteration 23 and
will re-measure it properly. That is a free, already-scheduled experiment; I do
not need to spend anything to get it.

What survives the staleness: **bob swept 65 maps against me and I swept 1.** A gap
that size is structural, not tuning, and no amount of iteration-14-era noise
explains it. It stays the standing target.

---

# Iteration 24 candidate — the mopper never chooses the tile it stands on

## Where this came from

`src/alice_mopstand/` was on disk uncommitted when I resumed — an instrumented
census build I wrote just before the session died. Reconstructing its intent from
the code and then auditing it found the instrument itself was **measuring the
wrong scale**, so the first work was fixing the instrument, not running it.

## The mechanism, from the engine numbers rather than from a trace

Two facts from `RULES.md`, both already verified against the engine:

- **A mopper's attack costs 0 paint** (`UnitType`: Mopper atk cost 0). Mopping is
  free.
- End-of-turn upkeep (`InternalRobot.processEndOfTurn`): standing on an **enemy**
  tile costs a mopper **-4/turn**; on an **ally** tile the terrain term is **0**.
  (The -1/-2 per adjacent ally robot is charged either way, doubled on enemy.)

Put together: **upkeep is the mopper's ONLY paint sink**, and terrain choice is
most of it. A 100-paint mopper standing on enemy paint is empty in ~25 turns; at
0 paint it takes -20 HP/turn and cannot act, and it has 50 HP. So a mopper that
parks on enemy paint kills itself in roughly 28 turns without an enemy doing
anything.

Now the decision. `runMopper`'s last line is:

```java
if (target == null) wander(rc);
else if (bd > 2) tryMove(rc, me.directionTo(target));
// bd <= 2: already in mopping range, hold position and keep mopping.
```

**The hold branch never chooses where it stands, and it does not use its move.**
The mopper arrives by walking *toward* enemy paint, so the tile it stops on is
disproportionately likely to be enemy paint — the thing it was walking at.

The candidate is: in the hold branch, step to an adjacent **ally** tile that is
still adjacent to enemy paint. Zero terrain upkeep, mopping preserved.

## Pricing it against what it displaces, not against zero

Doctrine makes me price a reallocation by the forgone use. **The hold branch
currently spends its movement on nothing** — it does not move at all. So the
move is genuinely free, and this fits the recurring winner's profile the
algorithm names: *capability preserved at zero marginal cost*. That is the
strongest part of the case and also the part I should trust least without the
counts below, because it is the comfortable direction.

Two real prices I can name now:

1. The candidate as scoped keeps me adjacent to *some* enemy tile, not the
   *specific* pattern-blocking tile iteration 19 taught the mopper to prefer. If
   the step trades a priority-0 target for a priority-2 one it is a downgrade.
   Design must preserve the ranked target, not just "an" enemy neighbour.
2. Moving can raise the **crowding tax** (-1/adj ally on an ally tile). A spot
   with three adjacent allies is -3/turn and beats -4 only barely.

## A competing branch that buys the SAME good, named now so the split is chosen

A mopper can mop the tile **under itself** (`r^2=0` is inside its `r^2<=2` action
radius), turning enemy paint into EMPTY, which is `-2`/turn for a mopper rather
than `-4`. That halves the drain with no movement — but it **spends the action**,
which is the mopper's scarce good, whereas the step spends a movement that is
currently wasted. Two branches, same good, different budgets. Doctrine says the
order they fire in would otherwise set the allocation by accident, so: **the step
is strictly cheaper and is the one I am testing.** Recording the self-mop as a
named, unpriced alternative rather than letting it get bundled in.

## Pre-registration — the numbers that decide this, written before I read them

The instrument as I found it computed `fs` = ally tiles adjacent to an enemy tile
**anywhere in the 9x9 vision window**. That is a *vision-scale* supply count, and
the decision I would change picks among **the 8 tiles I can step to this turn**.
Wrong referent — the exact trap doctrine names (the lineage that ran reachability
on a guard and never on the set the guard ranks). I added the decision-scale
count `alt`: of the 8 tiles `canMove` actually permits (which covers walls *and*
occupancy, unlike the paint grid), how many are ally paint AND still adjacent to
≥1 enemy tile. `hold` records whether the turn took the hold branch at all.

Deciding quantity: **P(u=X AND alt≥1 | hold=1)** — the share of hold-turns on
which the mechanism could actually act.

- **< 10%** → too rare to pay for; hypothesis dead, log it and leave.
- **≥ 25%** → build the candidate.
- **10–25%** → marginal; only proceed if starvation is independently visible.

And the two checks I would have skipped, both of which have killed a hypothesis
of mine already today:

- **SUPPLY, not just frequency.** If `alt` is modally **0** whenever `u=X`, there
  is nothing to step to and the hypothesis is dead however common `u=X` is. This
  is the identical shape to the ruin-collision death: I counted collisions and
  never counted the targets. Counting supply first this time.
- **The drain must convert into harm.** If mopper paint `p` stays high all game,
  -4/turn is a number and not a problem, and the fix buys nothing. A cost that
  never binds is not a cost.

Sizing on **three** maps (UnderTheSea, catface, CastleDefense), not one, because
a quantity measured on one map is a statement about that map — `gridworld` once
gave 25% where two other maps gave 95%.

Identity check for the instrumented build: `src/alice` is byte-identical to
`src/alice_iter23`, so `alice_mopstand vs alice_iter23` is a mirror of identical
code and must reproduce `alice vs alice_iter23` exactly. If it does not, the
census bytecode is changing behaviour and its numbers are not trustworthy.

## `reference/RESEARCH.md` — now exists, read, and it lands on the candidate in flight

The coordinator cleared a rebuilt `reference/RESEARCH.md` (2019–2024 only; both
predecessors' versions were built on 2025 post-mortems and are excluded, and the
sources here were filtered by `tools/redact-2025.py` *before* anyone read them,
which is the ordering that makes the ban enforceable rather than aspirational).
Four things bear on what I am doing tonight.

**§1 — the instrument table, which independently confirms tonight's map-policy
correction.** It sets out what each instrument can and cannot do, and the entry I
should have had in front of me this morning is that a **lopsided instrument
measures direction poorly in BOTH directions**: when you lose most games anyway,
a change making you *worse* has little room to show. That is the same argument I
reached from the other end when I noted `iter0`/`iter1`/`iter4` at 98–100% "have
no resolution left and gate nothing". Mine was about a ceiling, §1's is about a
floor; they are one fact. It also states plainly that the frozen roster is the
*level* instrument and must be **same-sample to be an identity rather than an
estimate** — which is exactly the distinction I drew between the chart and the
drift check, arrived at independently. Two derivations meeting is the best
evidence I have that the correction was right.

**§8 — wololo's three-part test for whether a quantity is a RESOURCE.** (a) having
none of it is near a loss condition, (b) you can remove it from the opponent, (c)
the opponent can make it hard to get. Applied honestly to **mopper paint**:

- (a) **Yes, and sharply.** 0 paint → -20 HP/turn and cannot act; a mopper has 50
  HP. Three turns from empty to dead.
- (b) **Yes.** A mopper attack on an enemy robot is *-10 paint to them, +5 to me*
  (`RULES.md`) — a direct transfer, which is the strongest form of (b).
- (c) **Yes.** Holding painted ground raises my upkeep on it.

So mopper paint passes all three — it is a genuine resource, not a constraint.
§11's item 8 ("check that your resource is one the opponent can deny you") is the
check that would have killed this line, and it **passes**. That matters because
my first hypothesis *in* this area is about to die below: the area survives even
though the hypothesis does not, and those are separate verdicts.

**§7 — emergent, not commanded, coordination.** The perennial finding is that
sophisticated coordination schemes flop while local rules producing group
behaviour are cheap and robust; the number to sit with is **~two-thirds of
self-play games won from a spawn-ORDERING change alone**, no messages, no shared
state. This is the constructive counterpart to my comms result: I refuted the
*dispatch* application of comms yesterday and recorded the capability as "open and
unpriced". §7 says I was refuting the right thing — a schema — and that the
payoff in this space is reached without one. Recorded as a live direction.

**§2/§3 — a trace proves a mechanism EXISTS, not that it is WORTH anything.** My
closed-directions ledger is largely a list of exactly this. Nothing new to change;
it is a correct description of my failure mode and belongs in LEARNINGS.

## Census result, map 1 of 3 (UnderTheSea) — my hypothesis fails its own gate

Instrumented build verified **behaviour-inert first**, and by a stronger argument
than a game-diff: the census makes only read-only calls, so the *only* channel by
which it could change play is the bytecode limiter truncating a turn — and
**overruns = 0 across all 18,339 mopper-turns** (peak 13,760, no near-misses). Not
"probably inert": inert by exhaustion of the one available mechanism, for free.

18,339 mopper-turns, 6,348 of them (34.6%) in the hold branch.

| where the mopper stands | all turns | hold-turns |
|---|---|---|
| **A** ally paint (0 terrain upkeep) | **82.8%** | **55.7%** |
| **E** empty (-2/turn) | 12.9% | 31.8% |
| **X** enemy paint (-4/turn) | **4.4%** | **12.5%** |

**Pre-registered deciding quantity: P(u=X AND alt≥1 | hold) = 604/6348 = 9.5%.**
My pre-registered threshold was **<10% → too rare to pay for, hypothesis dead.**

It is 9.5%. **That is under the bar I set before I looked, and I am taking it.**

This is as close to the line as it could land, which is precisely why the number
was written down in advance. Had I set the gate after seeing 9.5% I would have
found a reason it was enough.

**The premise was simply wrong.** I argued the mopper "walks toward enemy paint,
so the tile it stops on is disproportionately likely to be enemy paint". It is
not: moppers stand on **ally** paint 82.8% of the time. The mechanism I designed
addresses a situation that mostly does not arise.

The supply check came out the *opposite* way from the ruin-collision death, which
is worth recording because I predicted the same shape: when `u=X`, modal `alt` is
0 (191/795) but **76% do have an alternative**. So supply was not the binding
constraint this time — **frequency was**. I have now had one hypothesis killed by
absent supply and one by absent frequency, and I checked both only because the
first taught me to.

### The census refutes my hypothesis and NOMINATES a better one

The harm is real and I mis-attributed its cause. **6.9% of mopper-turns sit at
p≤10 and 277 turns at p=0** — moppers genuinely starve. But they starve while
standing on **ally paint 82.8% of the time**, where the terrain term is **zero**.
Terrain cannot be what is draining them.

`RULES.md` already names the only remaining sink, and I read past it: **the
adjacency tax is charged on ALLY tiles too** — `addPaint(-allyRobotCount)` — so
standing on your own paint waives the *terrain* penalty and never the *crowding*
one. A surrounded mopper pays -8/turn on a 100-paint stash, on friendly ground,
forever.

So the drain is plausibly **crowding, not terrain** — and I did not instrument it.
I counted adjacent *enemy tiles* and never adjacent *ally robots*. Added `aa` to
the census. Not proceeding on it until the accounting closes: I will predict each
mopper's per-turn paint delta from (terrain + crowding) and reconcile against the
observed delta, because a decomposition that does not close is not evidence.

**Holding the verdict until all three maps report.** One map is a statement about
that map.

## Census COMPLETE, all three maps — hypothesis REJECTED by its own gate, and it found something bigger

| map | mopper-turns | hold-turns | **P(u=X & alt≥1 \| hold)** |
|---|---|---|---|
| UnderTheSea | 18,339 | 6,348 | **9.5%** |
| catface | 5,626 | 4,056 | **8.3%** |
| CastleDefense | 1,860 | 1,180 | **8.1%** |
| **pooled** | **25,825** | **11,584** | **9.0%** |

Gate was **<10% → dead**. Pooled 9.0%, and under 10% on all three maps
independently, so this is not a degenerate-map artifact. **Iteration 24 as
originally scoped is rejected.** The premise ("the mopper walks at enemy paint so
it stops on enemy paint") is simply false — moppers stand on ally paint 75.7% of
the time.

### Closing the accounting BEFORE reading anything off it

Before nominating a replacement I reconciled the observed per-turn paint delta
against the engine's terrain table, on consecutive rounds only so each delta is
exactly one end-of-turn charge (UnderTheSea, 18,145 deltas):

| tile under mopper | engine terrain term | **observed mean Δpaint** | unexplained |
|---|---|---|---|
| **A** ally | 0 | **-0.54** | -0.54 |
| **E** empty | -2 | **-2.04** | -0.04 |
| **X** enemy | -4 | **-3.50** | +0.50 |

**The accounting closes.** Terrain is essentially the whole sink, and the residual
on ally tiles (-0.54) is the crowding tax — real, but small, because my moppers
average only ~0.5 adjacent ally robots.

**That kills my own follow-up hypothesis before it cost a game.** I had nominated
crowding as the true drain and had already added an `aa` field to measure it. The
reconciliation says crowding is -0.54/turn against terrain's -2 to -4. Nominated
and refuted inside ten minutes, on data already on disk, for zero games. Recording
it because a hypothesis I never ran is still a hypothesis I held.

### The finding the census actually delivered — moppers are a self-terminating unit

A mopper's attack costs **0 paint** and a mopper has **no paint income** (the bot
calls `transferPaint` nowhere). So mopper paint declines monotonically and the
only question is how fast. Sizing the consequence:

| map | moppers | deaths | **died at exactly p=0** | died with >60 paint | median lifespan |
|---|---|---|---|---|---|
| UnderTheSea | 194 | 189 | **69.8%** | 18.5% | 80 rounds |
| catface | 84 | 78 | **71.8%** | 21.8% | 61 rounds |
| CastleDefense | 43 | 42 | **28.6%** | 50.0% | 38 rounds |
| **pooled** | **321** | **309** | **64.7%** | 23.6% | — |

**Roughly two-thirds of my moppers starve to death.** CastleDefense is the honest
exception and it makes sense: it is the combat map of the three, where half the
moppers are killed with paint still in the tank. Reported rather than pooled away.

This is a **degeneracy signal**, not an opponent-relative comparison — "our units
die in a dead band" needs no opponent to be wrong — which is the kind of target
the algorithm says to prefer. It also compounds a failure mode already in my spawn
comments: tower paint → 0 → only the 100-paint mopper is affordable → moppers
complete no tower patterns → no paint income. Each such mopper converts 100 tower
paint into ~80 rounds of presence and then dies, because **mopping is free, so its
paint bought nothing but time.**

### My pre-registration tested a PROXY, and my own engine-facts file says not to

The gate I wrote asked about **enemy** paint. The engine charges a mopper on
**every non-ally tile**: -4 on enemy and **-2 on EMPTY**. Empty tiles sit under my
moppers *four times more often* than enemy ones. Re-running the same quantity on
the engine's real predicate:

| map | X & alt≥1 | E & alt≥1 | **(X or E) & alt≥1** |
|---|---|---|---|
| UnderTheSea | 9.5% | 21.7% | **31.2%** |
| catface | 8.3% | 30.5% | **38.9%** |
| CastleDefense | 8.1% | 17.4% | **25.5%** |
| **pooled** | 9.0% | 24.4% | **33.3%** |

**33.3%, and ≥25% on every map — over the "build" threshold I pre-registered.**

I want to be exact about what happened, because it flatters me and that is when I
should be hardest on myself. **My original hypothesis is dead and stays dead**;
9.0% is under the bar I set and I am not rescuing it. The 33.3% figure is a
*different, data-suggested* hypothesis and it carries the weaker evidential status
that comes with being formed after looking. What it is not, though, is a fishing
expedition: `engine-facts.md` — written by me — ends with *"guard on the engine's
own predicate, not on a proxy you believe implies it."* I then wrote a gate on the
proxy "enemy paint" when the engine's predicate is "not ally paint". The
correction is my own recorded rule applied to my own pre-registration, which is
the one form of post-hoc revision I think is legitimate.

**Size of the prize, as an upper bound and labelled as one:** if every actionable
hold-turn stood on ally paint, 7,303 paint is saved across the three games — **73
mopper-lifetimes** against 321 moppers actually spawned, so ~23% of all mopper
paint. Upper bound because it assumes every such turn relocates and that the move
is free of side effects.

### Where the closed `transferPaint` direction stands — NOT re-opened

The obvious reading is "give moppers a refill". The ledger closed that at
iteration 6 and the recorded cause **still applies**: a refill costs the tower the
same paint as a fresh unit, so it is break-even on the binding resource and saves
only chips, which sit at $290k. A mopper refill is 100 paint against a 100-paint
new mopper — the *identical* arithmetic that closed it for soldiers. It stays
closed. The candidate below does not spend tower paint at all; it stops wasting
the paint the mopper already holds, which is a different lever.

## Iteration 24 (rescoped) — the hold branch chooses its tile

`src/alice_i24/`. In the `bd <= 2` hold branch, if the mopper stands on non-ally
paint, step to a movable neighbour that is ally paint **and from which the chosen
target is still within `r²<=2`**. One mechanism, nothing bundled.

- **Price:** the hold branch currently does not move at all, so the movement is
  already being wasted and nothing is displaced. This is the "capability preserved
  at zero marginal cost" profile.
- **Target preserved deliberately:** the step must keep *the ranked target* in
  range, not merely "an" enemy tile — otherwise it could silently trade iteration
  19's pattern-blocking priority-0 target for a priority-2 one. **Note this makes
  the true actionable rate ≤ the measured 33.3%**, because `alt` only required
  adjacency to *some* enemy tile. The `i24=` counter measures the real rate.
- **Play-symmetry:** the neighbour scan starts at a random index. A fixed
  compass-order `Direction[]` scan is precisely the bug class the audit forbids,
  and here the candidates are interchangeable, so there is no formation cohesion
  for randomisation to destroy.

Pre-registered, before step 0 returns:

- **Step 0 (mandatory):** one map, arms must NOT be byte-identical, and `i24=`
  must be > 0. If the arms match, the mechanism is dead and no gauntlet is spent.
- **Accept gate:** head-to-head vs `alice_iter23` > 50% on a full random sample.
- **Prediction that can falsify the mechanism story even if the number is good:**
  mopper deaths at p=0 must fall materially below 64.7%. If the win rate rises
  while starvation is unchanged, the mechanism is not what won and the
  attribution is OPEN, per step 3b — I do not get to back-fill it.

## Iteration 24 step 0 — PASSED, and the identity question is settled by logic not by a diff

One map (UnderTheSea), `alice_i24` vs `alice_iter23`. Candidate wins on
tiebreakers at round 2000; the baseline mirror (`alice` vs `alice_iter23`, which
is byte-identical code on both sides) also ends A-wins-on-tiebreakers, so **the
top-line result does not discriminate** and would have been worthless on its own.

The discriminating measurement is the engagement counter:

```
max i24= seen on a single mopper over its life: 11
typical late-game mopper:                        3
```

**The mechanism engages.** And this settles byte-identity without waiting for the
counter diff: a mopper relocated 11 times that would otherwise have stood still,
so the two games cannot be identical. Recording the reasoning because "the diff
had not finished" would otherwise look like a skipped mandatory check.

**Why the counts look low, and why that is expected rather than disappointing.**
The measured opportunity was 33.3% of *hold-turns*, but the relocation happens at
most **once per hold EPISODE**: after the step the mopper is on ally paint, so the
guard returns immediately on every subsequent turn of that episode. Consecutive
hold-turns share one relocation. So 3–11 relocations per life is consistent with
33.3% of hold-turns, and I should not have expected a per-turn number. **This is a
rate whose denominator I nearly misread** — the same shape as counting collisions
without counting supply.

### An instrumentation gap I found by trying to test my own prediction

My pre-registered mechanism check was *"mopper deaths at p=0 must fall materially
below 64.7%"*. I then found the candidate build **prints no paint** — its mopper
indicator is `i24=… bc=…` — and `replay-dump` exposes robot paint only through
indicator strings. **I could not have tested my own pre-registered prediction with
the build I was about to evaluate.** Added `p=` before launching.

Worth recording as a rule: **pre-register the metric and then check the build can
actually emit it.** A prediction that the instrument cannot report is not a
prediction, and I would have discovered this only after spending 150 games — at
which point the tempting move is to accept on the win rate and quietly drop the
mechanism check, which is exactly the back-filling step 3b forbids.

## IN FLIGHT — gauntlet `20260907-234431`, 150 games

`BOT=alice_i24 OPPONENTS="alice_iter23 alice_flood alice_iter7"`, 25 random maps,
both sides. Detached, so it survives a session death; if I die, **collect it with
`../../tools/gauntlet-collect.sh 20260907-234431` — do not re-run it.**

Decision rules, pre-registered and unchanged from above:

- **Accept** requires head-to-head vs `alice_iter23` **> 50%** (doctrine 8: the
  primary gate is the most recent accepted snapshot), no unresolved
  one-directional regression against `alice_flood` / `alice_iter7`.
- **Mechanism check, separately:** mopper deaths at p=0 must fall materially below
  **64.7%**. If the win rate clears the bar while starvation is unchanged, I
  **accept the result and record the attribution as OPEN** rather than inventing a
  story for it. Writing that down now so the temptation is pre-empted.
- The two lopsided opponents give **direction only** — a 1–2 game move on either
  is under the noise floor and I will not read it.

## Mechanism check, run early and for free — it works, and the outcome proxy moved the WRONG way

While the gauntlet plays I found the mechanism check was already sitting on disk.
`tools/replay-dump.sh` prints a per-team `starved` counter, and reading its source
first (rather than assuming its referent — the error that has cost me three
numbers): `starved` counts **deaths whose last recorded paint was ≤ 0**, and
`lastPaint` comes from the replay's own `turn.paint()`, **not** from indicator
strings. So it works on *uninstrumented* builds, which makes the two step-0 arms
directly comparable. The counters reset after each printed summary line, so
summing them over a run gives game totals at any `--every`.

Two consequences worth recording:

1. **My `p=` indicator addition was unnecessary** — the engine records robot paint
   in the replay regardless. I would have found this by reading the tool before
   patching my bot. Cheap lesson, no harm done.
2. **The referent is ALL unit types, not moppers.** My 64.7% is a mopper-only
   figure and these two numbers must never be quoted as the same thing. Since my
   realized army is ~90% moppers the two track each other, but they are different
   measurements and I am labelling them as such.

UnderTheSea, one game per arm, T1 = my bot, T2 = `alice_iter23` in both arms:

| | spawned soldiers | spawned moppers | deaths | **starved** | final coverage |
|---|---|---|---|---|---|
| **baseline** `alice` (T1) | 520 | 195 | 662 | **323 (48.8%)** | **635m** |
| **candidate** `alice_i24` (T1) | 572 | 156 | 673 | **209 (31.1%)** | **570m** |
| opponent T1-arm control (T2) | 410→427 | 173→173 | 548→560 | 212→198 (38.7→35.4%) | 347→410m |

**The mechanism works.** Starvation deaths fall 323 → 209, from 48.8% to 31.1% of
all deaths — a 35% relative reduction, in the predicted direction, and far too
large for one game's noise. The opponent control moved only 38.7 → 35.4%, so this
is not a global drift in the counter.

There is a coherent downstream story too: **mopper spawns fall 195 → 156 while
soldier spawns rise 520 → 572.** Moppers that live longer need fewer respawns,
which frees tower paint, and the freed paint funds the 200-cost soldier — the unit
that actually paints. That is the absorbing state in §3c running *backwards* for
once.

### And now the part that does not fit the story

**T1's final coverage went DOWN, 635m → 570m**, and the opponent's went *up*,
347m → 410m. The candidate still won the map, but on a margin of +160 where the
baseline won by +288. On this one map the candidate is **worse on the outcome
proxy while being better on the mechanism.**

I am recording this at the same prominence as the good number, because this is the
single most recognisable failure shape in my own ledger and in the algorithm's:
**metrics that improve without converting to wins** (five mechanism-verified damage
increases converted to nothing in 2026; my own "survival bought with inactivity —
units die doing the thing that wins"). A mopper that survives by standing on
friendly paint is *closer* to that description than I would like.

n = 1 game, so this is not a measurement and I am not treating it as one — it
is a **flag on the interpretation**, not evidence against the candidate. The
150-game gauntlet is the test and it is already running. What this does change:
if the head-to-head comes back marginal, I will **not** rescue it with the
starvation number, because the mechanism firing is exactly what is already
established and is exactly what does not settle whether it pays.

## Cross-lineage read on the bob gap (tournament replays — the sanctioned channel)

Done while the gauntlet plays, from `tournaments/20260907-1300/results.csv` and two
replays pulled from `arena/tournaments/.../replays/`. Caveat stated up front: the
tournament exported **iteration 14** for me, so this describes a build nine accepts
old. It still describes the *shape* of the gap, which has not moved in a while.

### The gap is decided EARLY, not at the tiebreaker

| how alice's 139 losses to bob ended | share |
|---|---|
| before round 500 | 23.0% |
| round 500–999 | **49.6%** |
| round 1000–1999 | 22.3% |
| round 2000 (tiebreaker) | **5.0%** |

**72.6% are over before round 1000**, and only one loss in twenty survives to the
tiebreaker. bob is reaching the 700‰ instant-win bar around rounds 365–520 on the
maps he closes fastest. Against my own lineage my games routinely run to 2000, so
every instinct I have calibrated on self-play is calibrated on the wrong game
length. This is the self-referential blind spot with a number on it.

### Is it the maps or is it bob? — mostly bob, but not purely

On the 12 maps bob closes out fastest, I still **sweep 4 against carol** (split 5,
lost 3) against an overall sweep rate vs carol of **56% (42/75)**. So those maps are
somewhat harder for me than average, and they are nowhere near unwinnable. The gap
is bob-specific with a real but minority map-difficulty component.

**A correction I have to make against myself here.** My first cut of this analysis
printed "0 of 12" and I had *hardcoded* the conclusion "so these are not
intrinsically hard maps" as an unconditional string — a sentence that would have
been printed no matter what the number was, sitting directly under a number that
contradicted it. The 0 was a genuine bug (`for m,_ in fast[:12]` unpacked
`(mean, map)` backwards, so the lookup key was a float and every lookup missed).
Two failures stacked: a wrong number, and a conclusion that could not be falsified
by any number. The real answer is 4/12, and it changes the claim from "purely
bob-specific" to "mostly bob-specific". **A hardcoded conclusion in an analysis
script is the wrong-referent error with the referent removed entirely.**

### What bob does that I never do: he fields NO moppers

Piglets2, opening (T1 = alice @ iter14, T2 = bob):

```
round  1   alice sold1 mop1        bob sold2 mop0
round  3   alice sold3 mop2        bob sold4 mop0      cov: alice 22m, bob 24m
round 20   alice sold5 mop2        bob sold5 mop0      cov: alice 51m, bob 61m
round 22   alice sold5 mop2        bob sold6 mop0      cov: alice 56m, bob 65m
```

**bob builds zero moppers through the entire opening**; I commit two immediately
and never drop below. bob is ahead on coverage from round 3 and the lead widens
monotonically. Coverage is the win condition, moppers cannot paint, and tonight I
measured that a mopper converts 100 tower paint into ~80 rounds and then dies
having produced *nothing* (its attack is free, so its paint bought only duration).

Three independent lines now point the same way: the tournament's fastest instrument
(bob), my own paint accounting, and §3c's absorbing state.

**But this direction has already been tried once and it FAILED**, and I am not
going to quietly forget that. §3b records: at `MOPPER_PAINT_RESERVE=200` the bot
"painted ~10x more and still lost, because it did zero mopping while the opponent
erased its paint all game." The reconciliation I would need before re-opening is
specific: that failure was measured against **my own lineage**, which erases paint
heavily *because it is ~90% moppers*. bob apparently does not need to erase paint
at all. So the earlier refutation may have been an artifact of a self-referential
opponent pool — which is precisely the blind spot the algorithm says the pool
cannot see. **That is a candidate reason the recorded cause no longer applies, and
it is exactly the form the ledger demands for a re-open — but it is an argument,
not a measurement, and I have not run it.**

Filed as the leading structural candidate for iteration 25. Not started: iteration
24 is in flight and bundling is forbidden.

### The coverage curve, both maps — bob's lead opens at round 3 and never closes

| round | Piglets2 alice / bob | Fossil alice / bob |
|---|---|---|
| 1 | 21m / 21m | 66m / 66m |
| 3 | 22m / **24m** | 69m / **73m** |
| 10 | 32m / **37m** | 93m / **104m** |
| 19–22 | 56m / **65m** | 132m / **153m** |

Unit mix at round 3 is the whole story: **alice 3 soldiers + 2 moppers; bob 4
soldiers + 0 moppers.** Same early budget, and bob converts more of it into
painters — his `acts[p…]` runs 4–5 paint actions per round from round 3.

Two honest qualifications:

- The two curves are near-identical in shape because the engine is deterministic
  and bob's opening does not depend on terrain, so this is really **one
  observation of bob's spawn policy**, seen twice — not two independent samples.
  It is a *policy* observation rather than a noisy measurement, which is why one
  clean look is enough to state what the policy IS, and not enough to price it.
- It describes bob at the 13:00 tournament and me at **iteration 14**. My mopper
  share may have moved since; the coverage plateau has not.

### A tooling note for the coordinator (not a bug — a sharp edge)

`replay-dump.sh --every N` did not reduce the per-round summary output in my
invocation; I got every round. Not a problem for me (I filtered), and I have not
run the discriminating case to say whether `--every` is ignored for summary lines
specifically or whether my flag combination was wrong, so I am **not** filing this
as a defect — only noting it so the next lineage that pipes a 2000-round dump is
not surprised by the volume. If it matters to anyone, the discriminating check is
one dump with `--every 50` and `--quiet`, counting summary lines.

Second, more useful note: `starved` in the summary line counts **all unit types**,
and reads `turn.paint()` from the replay rather than from indicator strings — so
it works on uninstrumented builds. Both facts are worth stating in the tool's
header, because the name invites a mopper-specific reading and the instrumentation
question is exactly what sent me patching my own bot unnecessarily tonight.

## RETRACTION — "bob fields NO moppers" is FALSE. It was an opening, generalised to a game.

Superseding in place. The entry above stands as written and is wrong; here is what
the full game says.

I read 22 rounds of two openings, saw `mop0` on every line, and wrote **"bob builds
zero moppers"** as a claim about bob's strategy. Parsing all 646 and 509 rounds:

| | alice sold | alice mop | alice **spl** | bob sold | bob mop | bob **spl** |
|---|---|---|---|---|---|---|
| Piglets2 (646r) | 62 | 22 | **0** | 149 | **42** | **43** |
| Fossil (509r) | 71 | 19 | **0** | 53 | **13** | **14** |

**bob builds plenty of moppers — 17.9% and 16.2% of his army against my 26.2% and
21.1%.** He defers them; he does not forgo them. The difference in mopper share is
real but modest, and it is *not* the headline I made it. My claim was an artifact
of reading the first 22 rounds of a 646-round game.

**This is the retraction rule biting exactly where it was written to bite.** I
flagged the opening as "one observation of a policy seen twice" and thought that
was the caveat discharged — but the caveat I wrote was about *how many maps*, and
the error was about *how much of the game*. Naming one limitation gave me the
feeling of having audited the claim, and the unexamined dimension was the one that
was wrong. A flagged caveat is not a discharged one, and it is not a licence for
the caveats you did not think of.

And it is uncomfortable rather than comfortable, which is the direction doctrine
says is under-made: I had already built `src/alice_painter` on the strength of it.

### What the full game actually shows — and it is bigger than the unit mix

| | alice | bob |
|---|---|---|
| total units spawned (Piglets2) | **84** | **234** |
| towers at end (Piglets2) | **6** | **16** |
| final coverage (Piglets2) | 281‰ | **701‰** |
| final coverage (Fossil) | 267‰ | **700‰** |
| **splashers built, both maps** | **0** | **43 / 14** |

Three things, in order of size:

1. **bob out-produces me ~3:1 and holds 2.7x my towers.** This is an *economy*
   gap, not a unit-mix gap, and it dwarfs the mopper difference I was excited
   about an hour ago. Towers are already named "the master variable" in my own
   §3d. bob has 16 to my 6.
2. **bob's coverage lands on 700‰ almost exactly, on both maps.** That is the
   instant-win bar. He is not out-painting me by accident; he reaches the
   threshold and the game ends. My 281‰/267‰ is not a near miss, it is less than
   half.
3. **bob builds splashers (18% of his army on Piglets2); I have never built one.**
   My ledger records splashers as **open and unpriced** — explicitly not closed,
   with a note that the census which appeared to refute them was measuring a
   splasher standing where a *soldier* chose to stand. This is now independent
   external corroboration from the only instrument I have that did not descend
   from my own code.

### What this does to my plans

- `src/alice_painter` **survives, with its rationale rewritten.** The pure-painter
  pole is a legitimate span of the strategy space whether or not bob occupies it,
  and the blind-spot argument for it (every opponent I own erases paint heavily
  because my lineage is ~90% moppers) is untouched by this retraction. But it is
  no longer "the archetype that imitates bob", and I have corrected its comment.
- **The mopper-share iteration is demoted.** It was resting on a false premise.
- **Splashers and tower count are promoted** to the leading structural candidates,
  in that order — splashers because the direction was already open and is now
  externally corroborated, tower count because it is the master variable and the
  gap is 2.7x.

None of this touches iteration 24, which is a paint-efficiency change in flight and
is not competing with any of the above.

## Reachability pre-check on the promoted splasher direction — the branch is DEAD CODE

Before designing anything, I ran the reachability pre-check on the code a splasher
experiment would build on. `runSplasher` in `src/alice`:

```java
int bestScore = 3;                       // "require at least a few tiles worth"
for (MapInfo t : rc.senseNearbyMapInfos(rc.getType().actionRadiusSquared)) {
    ...
    int score = 0;
    if (t.getPaint().isEnemy()) score += 2;                       // max 2
    else if (t.getPaint() == PaintType.EMPTY && t.isPassable()) score++;   // max 1
    if (score > bestScore) { bestScore = score; best = c; }       // 2 > 3 : never
}
if (best != null) rc.attack(best);                                // best is ALWAYS null
```

**`score` can only ever be 0, 1 or 2, and `bestScore` starts at 3, so the
comparison is never true and `best` is never assigned. The splasher never
attacks. Not rarely — never.**

The intent is legible from the comment: `bestScore = 3` was meant to be a
threshold on the **AoE footprint** ("a few tiles worth"), but `score` is computed
from the **single centre tile** `t`. A sum over the blast area was written as a
lookup of one tile, and the threshold that was correct for the former is
unreachable for the latter.

`src/alice_splashcensus` carries the identical dead branch, which also settles
where its number came from: the "mean best blast 1.37 of 13 tiles" figure was
produced by a *separate offline* census over soldier-chosen positions, **not** by
this branch firing. That is consistent with the ledger note, and it means the
1.37 was never evidence about this code.

So the splasher capability is absent **twice over**: splashers are never built,
and the handler could not act if one existed. Any future "we tried splashers"
memory would be false — the ledger's "open and unpriced" is the correct status
and is now better supported than when I wrote it.

**Not fixing it now.** Iteration 24 is in flight and this is a different
functional area; fixing a dormant branch mid-evaluation is exactly the bundling
the algorithm forbids. Recorded as the concrete first step of the splasher
direction, which is now: (1) repair the footprint scoring so the branch can fire,
(2) verify it fires, (3) only then decide whether to build splashers at all.

This is the second time today the reachability pre-check has paid, and both times
it cost minutes: it killed iteration 23's premise on one map, and here it caught a
direction that would have been "built on" code that cannot run. **A branch that
has never executed cannot have been validated by any result the lineage has ever
recorded** — including results I would have cited as reassurance.

## Consistency pass — two binding rules about archetypes that have never cited each other

Prompted by building `alice_painter` and asking where it belongs.

- The algorithm on **synthetic archetypes**: *"Keep them synced: archetypes forked
  from the bot's own code go silently stale and inflate win rates (this masked a
  62.5% as 95.0% once). Automate the resync and make staleness loud."*
- `AGENT.md` on **`progress/roster_extra.txt`**: *"adds fixed non-snapshot
  yardsticks… They qualify for the same reason old snapshots do: **they never
  change**."*

**Resync it, and never change it.** For a single artifact those cannot both hold.
And `alice_flood` is currently in both roles: it sits in `roster_extra.txt`, and
`git log` shows it has been touched by exactly **one** commit since creation
(`af856f8`, around iteration 18) while `src/alice` has moved to iteration 23.

### Which is it, and is anything I published wrong?

Checked rather than assumed, because this is the kind of thing that quietly
invalidates a chart. **Nothing published is wrong, and the two roles fail
differently:**

- **As a frozen roster yardstick, `alice_flood` is behaving correctly.** It has not
  changed, so my rising win rate against it is exactly the signal the roster
  exists to produce. Tonight's 76% → 92% is a *delta between two runs against an
  unchanged opponent*, and staleness cannot contribute to a delta — it is constant
  in both arms. That reading stands.
- **As a current peer it is stale, and its LEVEL is inflated.** The failure mode
  the algorithm names is real but it applies to the *level*, not the delta. So
  "alice_flood 92%" must never be read as "my archetype coverage is healthy" or as
  a peer regression check. It is a yardstick reading and nothing else.

### The rule I am adopting

**An artifact cannot be both a frozen yardstick and a live archetype.** If I want
`alice_painter` in both roles it has to be two directories: a frozen
`alice_painter_v1` that enters `roster_extra.txt` and is never touched again, and a
resynced `alice_painter` that stays current for the opponent pool. Same for
`alice_flood` if I ever want a current spender pole again — the frozen one must
stay exactly as it is.

For now `alice_painter` is an **opponent-pool member only**, and it does not go
into `roster_extra.txt`. Adding a to-be-resynced archetype to the frozen roster is
the specific error this entry exists to prevent, and it would have looked
completely reasonable.

Cross-referenced both ways: this is the same shape as the LEARNINGS consistency
pass that found a determinism rule and a noise rule contradicting each other eight
lines apart. **The tell is identical — two rules that ought to cite each other and
never do.** Neither is wrong on its own; they are wrong about the same object.

## `src/alice_painter` — built, compiles, and its first game is a warning

The pure-painter pole (never builds a mopper; one line changed from `src/alice`).
Compile verified by playing it rather than by assuming: **`alice_iter23` beat it in
375 rounds** on DefaultSmall.

That is one game and not a measurement, but it points at a limit I should size
before investing: a 375-round loss suggests the painter pole may be **too weak to
be a peer at all**, which would make it a *benchmark* (<30%) under the
classification rules — direction only, never an accept gate. That is not fatal to
its purpose (it exists to supply a *behaviour* my pool lacks, not a challenge), but
it does cap what it can prove: an opponent I beat 95% of the time cannot resolve a
few games either way.

Its first job, before any iteration leans on it, is therefore to have its own win
rate measured so I know which instrument I am holding. Recorded so that a later
session does not mistake "I built the archetype" for "I have the instrument".

The 375-round loss is also consistent with §3b's recorded failure of the low-mopper
direction — the opponent erases paint all game and the painter has no answer. That
is the *expected* behaviour of this pole against my own lineage, and it is exactly
why the pole is interesting in the other direction: it tells me what a build that
does not contest paint looks like from the other side.

## Closed-directions ledger — update, current as of iteration 24 (in flight)

Superseding in place; the iteration-22 table above stands as written.

| direction | closed by | can re-open if |
|---|---|---|
| **Mopper avoids standing on ENEMY paint** (the original iteration-24 scope) | Census 2026-09-07, 25,825 mopper-turns / 3 maps: **P(stands on enemy paint AND an alternative exists \| hold branch) = 9.0%**, under the pre-registered 10% kill line, and under 10% on all three maps independently. Moppers stand on **ally** paint 75.7% of the time; the premise was false. | Only if the upstream policy changes so moppers routinely end their move on enemy paint. Note this is closed as scoped — the *engine-predicate* version (non-ally, i.e. including EMPTY) is **not** closed and is iteration 24. |
| **The crowding tax is what drains moppers** | Never run — refuted by closing the paint accounting on data already on disk. Observed Δpaint −0.54 / −2.04 / −3.50 against the engine's 0 / −2 / −4 terrain table; the ally-tile residual (**−0.54**) *is* the crowding tax, against terrain's −2 to −4. | Only if the army clumps far more than it does now (moppers currently average ~0.5 adjacent ally robots). Cost 0 games. |
| **Refuelling moppers from towers** (`transferPaint` withdraw) | Not re-opened. The iteration-6 cause applies unchanged to moppers: a refill costs the tower **100 paint against a 100-paint new mopper** — break-even on the binding resource, saving only chips, which sit at $290k. | Same conditions as the soldier entry: tower paint stops being the spawn bottleneck, or the walk back becomes free. |
| **"bob fields no moppers", and the low-mopper iteration resting on it** | Retracted by my own full-game parse: bob is **17.9% / 16.2%** moppers over 646 and 509 rounds against my 26.2% / 21.1%. He defers them, he does not forgo them. | The *general* low-mopper question is NOT closed — §3b's refutation was measured against my own ~90%-mopper lineage, which is the self-referential blind spot. `src/alice_painter` exists to attack that, but must have its own win rate measured first. |

### Explicitly NOT closed, and now better supported than when last written

**Splashers.** Promoted tonight and independently corroborated: bob built **43 on
Piglets2 (18% of his army) and 14 on Fossil**, while this lineage has never built
one. And the reachability pre-check found `runSplasher`'s attack branch is **dead
code** (`bestScore=3`, `score` maxes at 2), so no result this lineage has ever
recorded is evidence about it. Status: **open, unpriced, and now the leading
structural candidate.** First step is repairing the footprint scoring, not building
splashers.

**Tower count / economy.** New tonight and larger than anything above: on Piglets2
bob finished with **16 towers to my 6** and spawned **234 units to my 84**, landing
on **701‰ coverage against my 281‰** — the instant-win bar, hit almost exactly.
Towers are already named the master variable in §3d. A ~3:1 production gap is not a
tuning problem and it is not addressed by any candidate I currently hold.

## Note for the coordinator — `summary.txt` presents two numbers that are one number

Not a bug: `gauntlet.sh` computes both correctly. It is a **presentation** issue
that has demonstrably caused a misreading, so it seems worth passing on rather
than fixing silently in my own head.

`summary.txt` prints, for each opponent, the swept-map line and the win-rate line
adjacently:

```
vs alice_iter23   swept-win 8/25   swept-loss 0   split-by-side 17
vs alice_iter23   33/50 (66%)
```

Those two lines are related by an exact identity in a both-sides gauntlet:

```
wins − N = (swept wins) − (swept losses)          [split maps contribute exactly 0]
33 − 25 = 8 = 8 − 0
```

Verified with zero residual on all three opponents of `20260907-234431`
(+8/+8, +20/+20, +4/+4). Laid out as two adjacent lines they read as two
findings, and I cited them as independent corroboration under the doctrine rule
that asks for an effect to appear "in more than one place" — which is exactly the
error the layout invites.

**Suggestion, entirely the coordinator's call:** print the margin *as* the swept
figure, e.g. `33/50 (66%) = 25 + (8 swept-win − 0 swept-loss); 17 maps split by
side carry no signal`. The genuinely additional number in that line is
`split-by-side`, because it gauges the instrument's resolution — 17 of 25 maps
decided by spawn side means the effective sample is nearer 8 maps than 50 games,
and *that* is not derivable from the win rate.

I have recorded the identity in my own `LEARNINGS.md` either way, so nothing is
blocked on this.

---

# ITERATION 24 — ACCEPTED

`src/alice_i24` → `src/alice_iter24`, promoted into `src/alice`. Run
`20260907-234431`, 150 games, 25 random maps, both sides.

## The mechanism

In `runMopper`'s hold branch (`bd <= 2`, "already in mopping range"), the mopper
used to stand still and **spend its movement on nothing**. It now steps to an
adjacent **ally-painted** tile from which the chosen target is still within
`r²<=2`. One mechanism; nothing bundled.

Why it pays, from the engine's own numbers: a mopper's attack costs **0 paint**
and a mopper has **no income**, so end-of-turn upkeep is its *only* paint sink —
and upkeep is set by the tile underneath (0 on ally, −2 on empty, −4 on enemy).
Measured beforehand: **64.7% of my moppers died at exactly 0 paint**, median
lifespan 80 rounds. The movement was already being wasted, so the step is a
reallocation of nothing: *capability preserved at zero marginal cost*.

## Results

| opponent | win rate | swept-win | swept-loss | split-by-side | net |
|---|---|---|---|---|---|
| **alice_iter23** (accept gate) | **33/50 (66%)** | **8** | **0** | 17 | **+8** |
| alice_flood | 45/50 (90%) | 21 | 1 | 3 | +20 |
| alice_iter7 | 44/50 (88%) | 19 | 0 | 6 | +19 |
| overall | 122/150 (81.3%) | | | | |

Gate is >50% head-to-head vs the last accepted snapshot: **passed at 66%**, also
clearing `WinPct` = 60%. **No unresolved one-directional regression** — swept
losses are 0, 1, 0.

**But the honest size of the result is +8 net swept maps out of 25, not "66%".**
Those are the same number (see LEARNINGS: margin over 50% = SW − SL, exactly), and
**17 of 25 maps split by side and carry no signal at all**, so the effective
sample is nearer 8 maps than 50 games.

## Standing checks

- **Exceptions: 0** across all 150 games.
- **Bytecode:** peak **4092**, **0 overruns, 0 near-misses**. (The census build's
  13,760 peak was instrumentation; the shipping build is nowhere near the limit.)
- **Play-symmetry:** 68% as A vs 64% as B against `alice_iter23`; the 17 split maps
  break **9 A / 8 B**. That is churn, not the compounding side bias the audit hunts.

## Mechanism verification, and what I am NOT claiming

Verified on the step-0 pair (same map, both arms): **starvation deaths fell from
48.8% to 31.1% of all deaths**, against an opponent control that moved only
38.7% → 35.4%. Downstream, mopper spawns fell 195 → 156 while soldier spawns rose
520 → 572 — the §3c absorbing state running backwards.

**The last link of that chain is OPEN, and I am recording it as open rather than
back-filling it.** The chain "less upkeep → longer-lived moppers → fewer respawns →
freed tower paint → more soldiers" is verified at every step. The final step,
"more soldiers → more coverage", is **not**: on the one map where I have both arms,
the candidate's coverage was *lower* (635m → 570m) while it still won. Per step 3b
I accept the result and leave the attribution unresolved.

What the result does say: **14 of the 16 swept-win games ended at round 2000**, on
the paint tiebreaker — which is where a per-turn paint saving would accumulate. But
the split maps are *also* mostly 2000-round games (25/34), so round length does not
separate them. **Consistent with, not evidence for.** The separating experiment,
when I want it, is per-map final coverage for both arms on this run's pinned maps.

## Tooling note — the roster rows this run wrote are labelled `[roster-run]`

`track_vs_old_bots.py` recorded the three rows as `[roster-run]` (solid points).
By `AGENT.md`'s convention they arguably belong as `backfill` (hollow), because
this was a **pre-accept head-to-head** and the bot measured was a candidate. It
happens to have been accepted, so the points are honest either way — but the tool
appears to classify by "were the opponents roster members" rather than by "was
this a deliberate roster run". Flagging rather than hand-editing, since the CSV is
specified as derived automatically and never hand-edited.

Also note the roster has now grown to include `alice_iter23` (7 tracked opponents).

## Where this leaves the loop

Functional area for iterations 22–24 has been **paint efficiency**, and it is
now three accepts deep. Next targets are already selected and ranked from
tonight's tournament analysis, in a *different* area:

1. **Splashers** — attack branch is dead code (`bestScore=3`, `score` maxes at 2),
   so nothing this lineage has recorded is evidence about them; bob builds 43 on
   one map, I have never built one. First step is repairing the scoring, not
   building splashers.
2. **Tower count / economy** — bob finished 16 towers to my 6, 234 units to my 84,
   701‰ coverage to my 281‰. The master variable, and a ~3:1 production gap.

## Splasher dead-branch REPAIRED (inert), and the direction sized from engine costs

Separated deliberately from any decision to build splashers, so that decision can
be measured on its own rather than bundled with a bug fix.

**The fix.** `runSplasher` scored candidate centres by the paint of the **single
centre tile** (max 2) against a threshold of **3**, so `best` was never assigned
and the splasher never attacked. Now it scores the actual AoE footprint, using the
engine's real semantics from `RULES.md`:

- centre within `dist²<=4`; every tile within **`r²<=4`** (13 tiles) is painted if
  EMPTY or ally;
- **ENEMY paint is overwritten ONLY within `r²<=2`** (9 tiles).

Enemy tiles in that inner disc are scored **double**, because they are ground
**nothing else this lineage fields can take**: a soldier can never overwrite enemy
paint (and is charged 5 for trying — iteration 22), and a mopper clears one tile to
EMPTY rather than to ally.

**Inertness is provable, not inferred.** The tower spawn line reads
`want = (rnd(4)==0) ? MOPPER : SOLDIER`, and `UnitType.SPLASHER` appears **zero**
times as a build target anywhere in `src/alice`. So `runSplasher` never executes
and the change cannot affect play. Confirmed empirically too: the same match
(`alice` vs `alice_iter23`, DefaultSmall) returns the identical result before and
after — A wins, round 2000, tiebreaker.

### Sizing the direction from engine costs — it is better than my prior said

| way of taking ground | paint per tile taken |
|---|---|
| soldier on EMPTY | **5.00** |
| soldier on ENEMY | **impossible**, and costs 5 to attempt |
| mopper on ENEMY | 0, but only converts to **EMPTY**, never to ally |
| **splasher, empty ground (13 tiles)** | **3.85** |
| **splasher, enemy ground (9 tiles)** | **5.56** |

A splasher costs 1.5x a soldier's paint (300 vs 200) and its 6 lifetime attacks
convert up to **78 tiles against a soldier's 40** — and up to **54 of those come
off enemy paint**, which is the ground my standing structural gap says I cannot
take at all after the map saturates.

**This does not license building splashers yet**, and the prior against it is
specific: `alice_splashcensus` measured a mean best blast of **1.37 tiles of 13**
against a nominal break-even of 10. The table above is a *ceiling* (every footprint
tile convertible); 1.37 is a *measurement* at positions a **soldier** chose. The
gap between 1.37 and 13 is the whole question, and it is a question about
**positioning**, not about the unit.

### Pre-registered next step, and what it must NOT be

The reachability lesson applies to my own plan: I must not build splashers and hope.
The sizing instrument has to sample positions a **splasher** would occupy, which the
old census could not. Concretely, before any build decision:

1. Field splashers in a **census build only** (never in `src/alice`), with the
   repaired scorer, and record `splashScore` at the centre it actually chooses.
2. Pre-register the deciding quantity: **median chosen-centre score**, against the
   `MIN_SPLASH_TILES = 6` threshold and the nominal break-even of 10.
3. Size the **price** too, which the ceiling table omits: a 300-paint unit drawn
   from the same tower paint that §3c showed is the absorbing-state bottleneck. A
   splasher displaces 1.5 soldiers, and that is the number the gain must beat — not
   zero.

`MIN_SPLASH_TILES = 6` is a placeholder and is deliberately *not* tuned here; the
dose belongs to the iteration that builds splashers.

## UNEXPLAINED ARTEFACT in my workspace — `src/alice_stallcensus/`, provenance unknown

Reporting rather than adopting or deleting it. Facts, separated from inference.

**What it is.** `agents/alice/src/alice_stallcensus/RobotPlayer.java`, untracked,
27,653 bytes, mtime **2026-09-08 00:28–00:29**. A well-formed "iteration 25
pre-check" stall census: it classifies each soldier-turn at a tower-less ruin as
PROGRESS / BLOCKED / IDLE, and on BLOCKED turns counts whether an alternative
tower-less ruin is even visible — a choice-set reachability check, with a comment
citing *"a ruin ranking whose candidate set was a singleton"*, which is my own
lineage's lesson.

**What makes it anomalous.**

- **I did not write it in this session.** It is not in any command I issued.
- It is derived from my **current** `src/alice`, including the
  `MIN_SPLASH_TILES` constant I added at ~00:26 — so it was created *after* that,
  from my post-fix source.
- It was **not** present at session start (`git status` then showed only
  `alice_mopstand`).
- **Exactly one `claude` process is running** (me), and the pids matching
  `agents/alice` are my own shell.
- **No hooks** are configured, and nothing in `tools/` references `stallcensus`.
  `vm-match.sh` / `gauntlet.sh` only *read* `WS_DIR/src` to copy it to the VM;
  neither writes a local package.
- `tools/agent-watchdog.sh` states explicitly that it never starts a rival Claude
  session, precisely because *"two coordinators would each spawn three agents into
  one working tree, which is exactly the race MULTI_AGENT.md's git rules forbid."*

**Most plausible inference, offered as inference and not as fact:** a second Alice
session existed briefly — started by the coordinator or a recovery path — wrote
this file, and exited before my process check. That is the concurrent-session race
the watchdog comment says must not happen, and if so it is an operational issue
worth the coordinator knowing about, because two sessions sharing one working tree
can interleave commits.

**What I did about it, and why.**

- **Not committed and not used.** Code of unknown provenance must not enter this
  lineage: every accept gate I run assumes the build under test is one I authored
  and can account for. Adopting it would silently break that chain, and it would
  be indistinguishable afterwards from work I had done.
- **Not deleted.** It may be another session's in-flight work, and destroying it
  would be the same mistake in the other direction. It stays untracked, in place.
- My own commits this session touched **only** `agents/alice/` paths, staged
  explicitly, and `git show --stat` on each confirms it.

**Note the irony, which is also the reason it is tempting:** it is a *good*
instrument, aimed at a real next question, in my own idiom. That is exactly what
makes silently adopting it attractive and wrong.

## RESOLVED — the `alice_stallcensus` artefact, and a clobber audit I ran rather than accepted

Superseding my "provenance unknown" entry above in place; that entry stands as
written, and this is its answer.

**Cause, from the coordinator:** for about six minutes there were **two live Alice
sessions**. A message sent to me resumed this session *after it had already
reported*, while a fresh Alice had separately been launched — a queued message
revives a completed agent, which was not expected. The newer session was stopped
and this one kept. `src/alice_stallcensus/` was its orphan.

**My inference was right for the right reason.** I wrote that the most plausible
explanation was "a second Alice session existed briefly and exited", derived from
the file being built on my *own* post-00:26 source while only one `claude` process
remained. Worth noting because the inference was labelled as inference and the
facts were listed separately from it — which is why it could be checked rather
than believed.

**The artefact is already gone** from the working tree, so the "discard it" option
resolved itself; `git status agents/alice` is now completely clean.

### The clobber audit — asked of me, and run rather than assumed

The coordinator said my commits "look clean" and asked me to confirm, since I am
better placed. I did not take the reassurance, because the specific danger was
narrow and real: **I ran `git add agents/alice/src/alice` at 00:29:12, one minute
after the other session wrote at 00:28** — so had it also touched `src/alice`, its
edit would have been committed under my name and become indistinguishable from my
own work.

| check | result |
|---|---|
| every commit touching `agents/alice` today | **14, all mine**, all prefixed `alice:`, strictly sequential 23:53→00:31, no gaps, none foreign |
| `src/alice` vs `src/alice_iter24` | 5 hunks, **all** of them my splasher fix (`MIN_SPLASH_TILES`, `runSplasher`, `splashScore`); nothing else |
| files under `agents/alice` modified 00:20–00:35 | exactly **two**: `TRAINING_LOG.md`, `src/alice/RobotPlayer.java` — both mine |
| `25c3160` (inside the window) TRAINING_LOG diff | 67 added lines, all under my own `Splasher dead-branch REPAIRED` heading |
| working tree | clean |

**Nothing was clobbered.** The accepted iteration 24 snapshot, the roster history,
both charts and `src/alice` are all exactly what I wrote.

The one thing I would flag for next time: the window was survivable only because
the other session wrote a **new directory** rather than editing a shared file. Had
it appended to `TRAINING_LOG.md`, my very next `git add TRAINING_LOG.md` would
have absorbed it silently, and no audit afterwards could have separated the two
authors. The coordinator's procedural fix (check `ListAgents` *after* sending, since
a send can resurrect the agent being replaced) addresses the cause; this is just
the reason the cause matters.

## The margin identity — I was right, and the useful lesson is about definitions

The coordinator initially read my `SW − SL` identity as off by a factor of two,
then re-derived it and committed the correction (`0e50364`) rather than quietly
amending. Both formulas were exact; they name different quantities:

```
margin over 50%  = wins − N       =     (SW − SL)     per MAP   <- what I wrote
win−loss margin  = wins − losses  = 2 × (SW − SL)     per GAME  <- what was read
```

**The lesson is not that I was right.** It is that an identity stated without its
definitions cost two correct parties an argument, and doctrine 14 now carries both
forms. I have added both to `LEARNINGS.md` in place.

What actually settled it in minutes was **the verification table, not the
argument**: the entry recorded the identity checked on all three opponents with
zero residual, which converted "whose formula is wrong" into "which quantity does
the word name". Recorded as a durable rule — *write the check into the log, not
just the conclusion*, because a claim carrying its own verification can survive
being contradicted by someone with more context than you, and a bare claim cannot.

## Genuine corroboration on split-by-side — and this one really is corroboration

The coordinator reached "split-by-side is the one non-redundant number"
independently from the tournament side, and `tools/tournament-report.py` now prints
it beside the sweeps (last run: alice–bob 9 split, alice–carol 19, bob–carol 10).

Worth flagging against my own freshly-written lesson: I had just caught myself
citing two statistics as independent when one was a deterministic function of the
other. **This is the opposite case and passes the test I set** — two parties
reaching the same conclusion from different data (my gauntlet's within-run
head-to-heads; the coordinator's cross-lineage tournament), neither derivable from
the other. That is what the word is for.

The alice–bob split count of **9** is also directly useful to me: it says that
matchup is decided by side on only 9 of 75 maps, so unlike my near-mirror gauntlet
(17 of 25) the tournament against bob has **most of its resolution intact** — the
losses there are real, not spawn noise. That sharpens the bob gap as a target.

---

## Iteration 25 — splashers. Reachability pre-check FIRST, pre-registered before the data.

Binding-doc updates absorbed: `MULTI_AGENT.md` now carries the concurrent-session
rule and records "neither adopt nor delete, report and continue" as the expected
response to a foreign artefact; `TRAINING_ALGORITHM.md` doctrine 14 now states both
margin forms. My `LEARNINGS.md` already matches both. Nothing else to do there.

### The question, and why it comes before any census of splash value

I have a repaired scorer and a favourable *ceiling* (3.85 paint/tile on empty
ground, 5.56 on enemy, against a soldier's 5.00 and impossible-at-any-price). None
of that matters if a tower can never afford the unit. So the first check is
reachability of the **spend gate**, not of the splash.

**Reading the code first**, `runTower`'s spawn block:

```java
if (rc.getMoney() >= CHIP_RESERVE) {
    UnitType want = (rnd(4) == 0) ? MOPPER : SOLDIER;
    if (want == MOPPER && rc.getPaint() < SOLDIER.paintCost) want = SOLDIER;   // 200
    ... canBuildRobot(want, loc) -> buildRobot
}
```

The tower **spends the moment it can**: at 200 paint it builds a soldier (or a
100-cost mopper 25% of the time). Paint above 200 is therefore transient, and
chips sit at ~$290k so the `CHIP_RESERVE` guard almost never blocks a spawn. The
prediction that follows: **a single tower's paint oscillates below ~200 and
essentially never reaches the splasher's 300.**

If that holds, then "add SPLASHER to the spawn choice" is **not** a small change:
the tower would have to *decline* affordable soldiers and idle while paint climbs
to 300. The splasher's price is therefore **1.5 soldiers plus the foregone turns
spent waiting**, and pricing it against zero would be the reallocation error
doctrine warns about.

### Wrong-referent trap I am deliberately avoiding

The dumper prints `twPaint`, which is the **sum over all of a team's towers**
(`towerPaint()` sums `lastPaint` for non-robot types). A splasher is built by **one
tower**, so team-sum is the wrong referent: 16 towers holding 165 each sums to 2640
while **no single tower can afford anything**. I am measuring a **single tower's**
paint trace via `--robot <id>`, not the sum.

Naming this in advance because it is exactly the shape that has cost me numbers
before, and the team-sum figure is the one that happens to be printed.

### Pre-registered decision rule

- **If a single tower's paint essentially never reaches 300** → the splasher is
  unreachable under the current spend policy, and iteration 25 becomes *"change the
  spend policy"*, whose cost is measured in displaced soldiers. The splash-value
  census is then premature and I do not run it.
- **If it does reach 300 with useful frequency** → the gate is not the obstacle,
  and the next question is the positioning census (median chosen-centre
  `splashScore` against the nominal break-even of 10).

Either way the answer is cheap and comes from a replay already on disk.

### My enumeration was REFUTED by the measurement — and it was an enumeration over my OWN code

I predicted, from reading `runTower`, that *"a single tower's paint oscillates below
~200 and essentially never reaches the splasher's 300"*, reasoning that the tower
spends the moment it can afford a soldier. Measured on tower `id1` over its full
2000 turns (`replays/iter24_alice_iter23_UnderTheSea_A.bc25`, `--robot 1`):

| paint | min | p50 | p90 | p99 | max |
|---|---|---|---|---|---|
| tower `id1` | 0 | **110** | 200 | **500** | **630** |

| threshold | turns at or above | share |
|---|---|---|
| 100 (mopper) | 1192 | 59.6% |
| 200 (soldier) | 207 | 10.3% |
| **300 (splasher)** | **106** | **5.3%** |

**Wrong.** The tower is above the splasher's price on 5.3% of turns and reaches
630. My pre-registered rule says that is the "gate is not the obstacle" branch.

**Why the error matters more than the number.** This was not an inference about
the engine or the opponent — it was an enumeration over **my own source**, the
kind of reasoning doctrine explicitly prefers to an experiment ("try to close it by
enumeration… prefer it to an experiment"). It still failed, because the enumeration
was over the *code path* and ignored the two conditions that make the build fail
without spending: `rc.getMoney() >= CHIP_RESERVE` (1450) and `canBuildRobot`
needing a **free adjacent tile**. Neither is visible in the spend arithmetic I did.

The transferable form: **an enumeration is only as complete as the set of ways the
branch can fail, and "the action succeeded" is an assumption, not a case.** I
enumerated what the tower would *choose*; I did not enumerate what could stop the
choice from taking effect. That is the same gap as instrumenting an outcome instead
of a decision, running the other way round.

**And the more interesting question is now the one I did not ask.** Paint above 200
means the tower *wanted* to spend and could not. Two candidate causes, and they have
very different consequences:

- **chip drought** (`money < 1450`) — an economy problem, and CHIP_RESERVE is mine to tune;
- **no free adjacent tile** — the tower is **walled in by its own units**, which is a
  degeneracy ("resource pinned in a dead band") and would connect to the crowding I
  already measured around moppers.

Pre-registering before I look, so this cannot be fitted afterwards: **if team money
is comfortably above 1450 during the high-paint turns, the cause is placement
blocking, not economy.** I have team `$` on the same summary lines, so this costs
nothing.

### The discriminator answers cleanly — chip drought, not placement

Joining tower `id1`'s paint to team money on the same rounds (2000 rounds, both
present):

- On the **106 turns the tower ended holding ≥300 paint, team money was below
  `CHIP_RESERVE` (1450) on 105 of them — 99.1%.** Median money on those turns:
  1000.
- For contrast, on turns ending below 200 paint, money was ≥1450 on **65.3%**.

**So the pooling is economic, not placement.** The tower is not walled in by its
own units; it simply never attempts a spawn, because `rc.getMoney() >= CHIP_RESERVE`
gates the whole spawn block, and paint accrues untouched while that holds. My
appealing "walled in by its own crowd" story — which would have tied neatly to the
mopper crowding I measured earlier tonight — is **refuted**, and I am glad I
pre-registered the discriminator before looking at it.

### The cap-waste hypothesis: DEAD, sized before it cost anything

`RULES.md`: *"Towers store up to 1000."* Two towers peaked at exactly 1000, so I
checked whether income was being thrown away at the cap:

| tower | turns at cap (≥1000) |
|---|---|
| id1 | 0 (0.0%) |
| id10276 | 19 (1.0%) |
| id10934 | 5 (0.3%) |
| **pooled** | **24 / 5582 = 0.4%** |

At 5–15 paint/turn that is **0.4–1.2 splashers' worth across three towers over a
whole game.** Negligible. The "removing pure waste" story is the recurring winner's
profile and it is exactly why I wanted it to be true; the count says no. Fourth
hypothesis killed by a count today.

## CAUGHT ERROR — my buildability statistic measured POST-SPEND state

I then computed what looked like the decisive number, and it is wrong. Recording it
because I came within one reconciliation of publishing it.

| unit | cost | ends turn with paint ≥ cost | **AND** money ≥ 1450 |
|---|---|---|---|
| MOPPER | 100 | 59.6% | 32.50% |
| SOLDIER | 200 | 10.3% | **0.10%** |
| SPLASHER | 300 | 5.3% | **0.05%** |

Read naively this says a soldier is buildable on 1 turn in 1000 — a dramatic
"absorbing state, measured at last" result. **It is an artefact.**

**The reconciliation that killed it**, run because the two artefacts had to agree:
0.10% of 2000 turns is 2 opportunities for one tower, ~24 across the team — and
**572 soldiers were actually built in that same game** (against 156 moppers, a
78.6% soldier mix). Both cannot be true.

**The defect:** the replay records each robot's state *after* its turn, so paint is
**post-spend**. Every turn on which a unit *was* affordable and *was* built shows up
in the data as a low-paint turn. The statistic is therefore conditioned on the
outcome it is trying to predict, and it systematically under-counts affordability by
exactly the cases that matter.

This is **"instrument the DECISION, not the outcome"** — my own ledger's rule —
arriving from a direction I had not seen before: not an in-bot counter placed at the
wrong point, but a *replay-derived* statistic that is post-decision by construction.
A replay's per-robot state is an outcome record. It can tell me what a tower *ended
up* holding; it cannot tell me what it *could have afforded*.

Note also that the chip-drought conclusion above **survives** this correction, and
it is worth being precise about why rather than discarding the whole session's work:
"turns that ended rich in paint were turns money blocked the spawn" is a statement
*about* post-turn state, and is exactly what post-turn state can support. Only the
inference from it to *buildability* was invalid.

### What iteration 25 actually needs next

An **in-bot tower census** (`src/alice_towercensus`, never `src/alice`) recording, at
the moment of the spawn decision and before any spend: paint, money, which unit types
were affordable, which was wanted, and whether `canBuildRobot` succeeded — plus the
reason it failed. That is the decision, and nothing derived from a replay's
post-state can substitute for it.

**Pre-registered, before that census is built:** the deciding quantity is
**P(paint ≥ 300 AND money ≥ CHIP_RESERVE AND a free adjacent tile exists)** evaluated
*at the decision point*. Under 2% and the splasher is unreachable without changing
the spend policy, and iteration 25 becomes "change the spend policy", priced in
displaced soldiers. Over 10% and the positioning census is the next question.

I am explicitly **not** carrying the 0.05% figure into that pre-registration as a
prior, because it is the artefact above and would bias the reading of a number it
cannot inform.

### The in-bot tower census — built, and it answers the pre-registered question

`src/alice_towercensus` (never `src/alice`), byte-identical to `src/alice` apart
from the package line plus one instrumentation block. It counts, **at the spawn
decision point and before any spend**, what the tower could actually have built.
`canBuildRobot` is a pure query — no cooldown, no spend — so the census cannot
perturb the trajectory it is measuring. It also separates two predicates that my
earlier reasoning had run together:

- **engine-allowed** — `canBuildRobot(type, loc)` true on some legal tile: paint,
  chips, free tile, cooldown, all of it, as the engine judges it;
- **policy-permitted** — engine-allowed **and** `money >= CHIP_RESERVE`, which is
  my own gate, not the engine's.

And it evaluates the tile set two ways: the **8 adjacent** tiles my bot actually
tries, and the **12 tiles at r^2 <= 4** the engine actually permits (`RULES.md`:
"tower builds robots within r^2 <= 4"). My build loop has always tried only 8 of
the 12 legal tiles; this prices that gap for the first time.

#### FIRST, a silent-instrument failure that nearly cost me the whole measurement

The first run emitted **nothing**. 188,514 indicator lines in the replay, not one
of them from the census. No exception, no bytecode overrun, no error anywhere.

The cause: `run()`'s `finally` block writes the standing bytecode diagnostic with
`setIndicatorString` **after** `runTower` returns, and the engine records only the
**last** indicator string of a turn. My census wrote into a channel that my own
code overwrites microseconds later. The census now hands its payload to that
`finally` block instead of competing with it.

The transferable rule, and it generalises past indicator strings: **an instrument
that writes into a shared single-slot channel is silently erased by whoever writes
last, and the failure mode is an empty result rather than an error.** "The census
found nothing" and "the census emitted nothing" are indistinguishable downstream.
So *verify the instrument produced output before drawing any inference from what
it did not show* — I would otherwise have been one step from concluding "towers
never reach the splasher price", which is the answer I was already half expecting
and would have accepted without a fight.

#### Result — UnderTheSea, 13 towers, 23,704 tower-turns

| at the spawn decision point | count | share |
|---|---|---|
| action ready (cooldown) | 23704 | **100.00%** |
| `money >= CHIP_RESERVE` (1450) — my policy gate | 19127 | 80.69% |
| paint >= 300 | 1610 | 6.79% |
| **engine** would allow SPLASHER — 8 adjacent tiles | 1547 | **6.53%** |
| **engine** would allow SPLASHER — 12 tiles, r^2 <= 4 | 1547 | **6.53%** |
| engine would allow SOLDIER — 8 / 12 tiles | 2521 / 2521 | 10.64% / 10.64% |
| engine would allow MOPPER — 8 / 12 tiles | 16643 / 16643 | 70.21% / 70.21% |
| **policy-permitted SPLASHER** (the pre-registered quantity) | 59 | **0.25%** |
| policy-permitted SOLDIER | 735 | 3.10% |

**The pre-registered rule fires on the low branch: 0.25%, against a threshold of
2%.** The splasher is unreachable under the current spend policy, and iteration 25
is therefore *"change the spend policy"*, priced in displaced soldiers — not
"add SPLASHER to the spawn choice", which would have been a no-op mechanism
shipped on the strength of a ceiling table.

#### Three findings, and the second and third were not what I went looking for

**1. Cooldown never binds.** 100.00%, every tower, every turn. A tower's build
cooldown is 10 and cooldowns shed 10/turn, so it is always ready. Dead variable.

**2. Placement NEVER binds — and the 8-vs-12 gap is worth exactly zero.** The
12-tile and 8-tile columns are **identical on every tower, every unit type, all
23,704 turns**. Not "close": equal. In no single turn of the game did a legal
build tile exist in the engine's outer ring while none existed among the 8 my code
tries.

This kills two things at once. It finishes off the "the tower is walled in by its
own units" story I had already refuted from the replay — now refuted at the
decision point, which is the only place it could have hidden. And it pre-emptively
kills an *obvious-looking micro-optimisation* — "try all 12 legal tiles, it's free"
— which I would have written on sight, would have cost bytecode, and provably
cannot change a single build in a whole game. A cheap negative on a change I had
not yet proposed is the best value this census returned per line of code.

**3. The real finding: `CHIP_RESERVE` manufactures the state it then forbids.**

Money is above the gate on **80.69%** of all tower-turns. But among the 1,547 turns
where a splasher was engine-affordable, money was above the gate on **59 — 3.8%**.
Independence would predict ~1,248. That is not a coincidence to be noted; it is a
mechanism, and it runs through my own code:

> A tower's paint only climbs toward 300 during a stretch in which it is **not
> spending**. The only thing stopping it spending is the money gate. So "this
> tower holds 300 paint" is, mechanically, *evidence that money has been below
> 1450 for the last several dozen turns.* The condition that makes a splasher
> affordable in paint is the same condition that makes it forbidden by policy.

The soldier row says the same thing more loudly: engine-allowed on 10.64% of
tower-turns, policy-permitted on 3.10%. My reserve refuses roughly **seven of every
ten engine-legal soldier moments**.

**And here is where I stop myself, because the exciting reading of that is wrong.**
Refusing a build is **not** the same as losing it. The paint is *conserved* — the
tower keeps it and builds later — and I have already measured the only channel by
which it could actually be destroyed: paint sitting at the 1000 cap, at **0.4%**
of tower-turns pooled. So the reserve **delays** builds; it does not throw them
away. "71% of soldiers refused" is a true sentence about moments and a false one
about throughput, and it is exactly the sort of number I would have quoted as a
headline a few iterations ago.

What the reserve *does* do is push tower paint into a **high, idle band it would
not otherwise occupy** — which is precisely why a 300-paint unit is engine-legal
on 6.5% of turns at all. The splasher's paint price is, in this specific sense,
already being paid and left on the table.

#### Replicated on three maps of very different size — the result is not map-specific

| quantity | UnderTheSea (13 towers) | DefaultSmall (6) | DefaultHuge (25) |
|---|---|---|---|
| tower-turns | 23,704 | 11,731 | 45,317 |
| money >= CHIP_RESERVE | 80.7% | 92.0% | 94.0% |
| paint >= 300 | 6.79% | 3.22% | 3.02% |
| engine would allow SPLASHER | 6.53% | 2.98% | 2.79% |
| **policy-permitted SPLASHER** | **0.25%** | **0.18%** | **0.15%** |
| policy-permitted SOLDIER | 3.10% | 3.73% | 2.78% |
| **12-tile minus 8-tile opportunities, all types** | **0** | **0** | **0** |

**80,752 pooled tower-turns and the 12-tile footprint never once beat the 8-tile
one**, for any unit type, on any map. And the pre-registered quantity is 0.15-0.25%
everywhere — an order of magnitude under the 2% branch, on maps whose money
behaviour differs a lot (the chip gate is open 80.7% of the time on UnderTheSea and
94.0% on DefaultHuge, and the verdict does not move).

Note the direction of that last comparison, because it is the interesting one: the
map where money is *most* often available is the map where the splasher is *least*
often policy-permitted. That is the anticorrelation again, and it rules out the
lazy reading "just a poor economy on one map".

### The splasher direction is PARKED, with its exact next step recorded

The pre-registered rule sent iteration 25 to "change the spend policy". I am not
taking that branch immediately, and I want the reason on the record rather than
discovered later as drift:

- the splasher's *measured* positioning value is still `alice_splashcensus`'s
  **1.37 of 13 tiles** against a nominal break-even of 10, and the ceiling table
  (3.85 paint/tile empty, 5.56 enemy) is a ceiling, not a measurement;
- so relaxing `CHIP_RESERVE` to afford splashers would buy a unit whose value is
  unmeasured at the positions a *splasher* would occupy — the exact gap I already
  wrote down as "the whole question";
- and the same census that closed the reachability question handed me a **larger
  and cheaper** target, below.

**Parked with its next step intact**, so a later session does not have to
re-derive it: field splashers in a census build with the spend gate relaxed *in
that build only*, record `splashScore` at the centre the splasher actually
chooses, and compare the median against break-even 10 and against the price of
1.5 soldiers. Nothing about that plan is invalidated by parking it.

---

## Iteration 25 (redirected) — the tower paint withdraw, an engine mechanic the bot has never called

### Where this came from

The tower census was built to answer a splasher question. What it actually
established is that **towers hold paint they cannot spend**: paint >= 300 on 6.79%
of tower-turns, and on 96.2% of those turns the chip gate forbids any build. My
first reading of that was "the reserve delays builds, which is nearly free" — and
that reading is correct *for builds*. But building is not the only way paint leaves
a tower.

`RULES.md`, line 96, engine-verified previously and re-verified by `javap` today:

> **transferPaint** r^2 <= 2: moppers give to ally robots/towers; **ANY robot can
> withdraw from ally towers** (negative amount). CD 10. ... withdraw capped by the
> tower's current paint.

`grep transferPaint src/alice/RobotPlayer.java` returns **nothing**. Twenty-four
accepted iterations and the bot has never called it. This is precisely the failure
TRAINING_ALGORITHM.md Phase 0.2 warns about — *"a whole game mechanic sat unused for
81 iterations once"* — and I found it by sweeping `RobotController` for methods the
bot never calls, which is the sweep that doctrine prescribes.

Three measured facts line up on it, and none of them was collected to support it:

| fact | source | value |
|---|---|---|
| units die of paint starvation | iteration 24 verification | **31.1%** of all deaths |
| towers hold unspendable paint | tower census, today | paint >= 300 on **6.79%** of tower-turns |
| a withdraw costs chips | engine | **zero** — it bypasses `CHIP_RESERVE` entirely |

A withdraw converts the idle band directly into unit lifetime, at no chip cost,
against the largest single death cause in my own bot.

### The reachability pre-check comes FIRST — that is what this iteration already taught me

I will not build this and hope. The splasher work established the discipline the
hard way: I predicted from reading my own source that towers never reach 300 paint,
and the measurement refuted me because my enumeration covered what the code would
*choose* and not what could stop the choice taking effect.

So the same question, asked before any mechanism: **is a hungry robot ever actually
within r^2 <= 2 of an ally tower?** Soldiers wander outward from spawn; there is a
perfectly plausible world in which they are only ever near a tower in their first
few turns, while full, and starve far away where no withdraw is legal.

`src/alice_refillcensus` (never `src/alice`), byte-identical to `src/alice` apart
from the package line and one pure-query block, counts per robot-turn *before any
action*: paint, whether an ally tower is in transfer range, whether
`canTransferPaint(tower, -1)` is actually legal, and how much paint could have been
drawn (`min(capacity - paint, towerPaint)`, respecting the clamp TRAP in RULES.md
line 99 — asking for more than you can hold silently burns the tower's paint).

### Pre-registered decision rule — written before the data exists

Deciding quantity: **`l50c / l50`** — of the robot-turns spent below half paint,
the share on which a withdraw was legal. The *coverage* of the mechanism, not its
raw frequency, because a mechanism that is legal often but never when it is needed
is worthless.

- **`l50c/l50` < 2%** -> passive withdrawal is unreachable. Hungry units are simply
  not near towers. The iteration is then *not* "withdraw when adjacent" but "route
  hungry units to a tower" — a movement change with a real cost in displaced
  painting turns, which must be priced separately and is a different iteration.
- **`l50c/l50` > 15%** -> reachable. Iteration 25 is "withdraw when hungry and
  legal": one mechanism, one threshold, zero arm = `alice_iter24`.
- **between** -> reachable but thin; decide on `gain` (total recoverable paint)
  against 200 paint = one soldier, and say so explicitly rather than splitting the
  difference silently.

**Instrument-validity check, pre-registered because it just cost me a run:** `tp`
(the largest ally-tower `paintAmount` any robot ever saw) must be **> 0**. If it is
0, `RobotInfo.paintAmount` is not populated for allied towers, every `gain` figure
is garbage, and the correct response is to fix the instrument — not to report a
small number as a finding. "The census found nothing" and "the census measured
nothing" are the same output, and telling them apart is my job, not the reader's.

### Census result — reachable but THIN, and the middle branch fires

| | UnderTheSea | DefaultSmall |
|---|---|---|
| robot-turns | 76,105 (735 robots) | 19,713 (438 robots) |
| **instrument check** — max ally-tower `paintAmount` seen | **1000 (OK)** | **730 (OK)** |
| paint == 0 (starving outright) | 1.64% | 1.69% |
| paint < 50% capacity (hungry) | 26.89% | 15.48% |
| ally tower within r^2 <= 2 | 7.83% | 14.48% |
| withdraw LEGAL | 6.61% | 11.14% |
| **coverage `l50c/l50`** | **4.91%** | **4.13%** |

`RobotInfo.paintAmount` **is** populated for allied towers, so the pre-registered
instrument-validity check passes and the numbers may be read.

**4.91% and 4.13% — the middle branch.** Reachable, but hungry units are usually
*not* near a tower, which is the honest shape of it: soldiers starve at the
frontier, not at home. My rule says decide on the recoverable-paint figure and say
so explicitly, so:

**I am NOT quoting the census's own `gain` total, because it is inflated and I built
it wrong.** It sums `min(capacity - paint, towerPaint)` over *every* hungry-and-legal
turn — 98,773 paint on UnderTheSea, which reads as "494 soldiers of paint". That is
nonsense: transfer has a cooldown of 10, and a robot loitering beside a tower for
ten hungry turns contributes ten full tank-fills to the sum while it could actually
have taken one. The sum double-counts by roughly the dwell time, and the same tower
paint is counted once per adjacent robot on top of that. A per-turn maximum summed
over turns is not a total; it is an upper bound on each turn, added up.

I am recording that rather than quietly dropping the number, because I *wrote the
counter that way* and only caught it when 494 soldiers of paint failed a
plausibility check against the 572 soldiers actually built in a whole game. Same
shape as the post-spend affordability artefact earlier this iteration: **a statistic
that is a maximum per observation does not become a total by summation.**

### Iteration 25 — the mechanism, and the gate, pre-registered before any evaluation

`src/alice_i25`: **a robot below half paint, with an unused action, withdraws a
tower's surplus paint above one soldier's cost.**

Two design choices that make the price genuinely near-zero rather than merely small,
each of which I would otherwise have had to measure:

1. **It runs AFTER the unit's normal logic.** `canTransferPaint` is false once the
   action is spent, so it can consume only an action the unit did not use. A soldier
   that painted, marked, or completed a pattern this turn is untouched — and a unit
   at 0 paint, the one this is for, *cannot paint at all* and had nothing to spend.
   That is iteration 24's winning shape: capability preserved at zero marginal cost.
2. **It takes only the tower's surplus above `SOLDIER.paintCost`.** It can never
   consume the paint a soldier build needed; it drains only the idle band the tower
   census measured. Self-calibrating, in the same form as iteration 5's "only build
   a mopper if a soldier was affordable too" — **no tuned dose**, so nothing here can
   be overfitted to a map sample.

Zero arm = `alice_iter24`, which `src/alice` is behaviourally identical to (their
only diff is dormant `runSplasher` code, and splashers are never built — the spawn
choice is MOPPER/SOLDIER only).

**Pre-registered accept gate** (written now, before a single evaluation game):

- **> 50% head-to-head vs `alice_iter24`** on a fresh random 25-map sample, read as
  **net swept maps** (SW − SL), not as a win percentage, since margin over 50% =
  SW − SL exactly and split maps carry no signal.
- **No unresolved one-directional regression**: swept losses must be explainable.
- **Exceptions: 0**, and **no bytecode overruns**.
- **Mechanism verification, and it is a real risk here**: the census says this can
  fire on at most ~5% of hungry turns. So I must report `i25Refills` — a firing
  count — and if the mechanism fires **zero or near-zero** times, then any win is
  *not* this mechanism and the correct verdict is REJECT-as-unattributable, however
  good the score looks. A low firing rate is not by itself evidence of no effect
  (rare and high-value is a real profile), but a *zero* firing rate is.

### Mechanism verification BEFORE the gate — it fires 26 times

`alice_i25` vs `alice_iter24`, UnderTheSea, full game, counted from the candidate's
own indicator string (`i25=<refills>/<paint>`):

| | |
|---|---|
| robots that lived | 776 |
| **refills fired** | **26** |
| paint withdrawn | 1,962 = **9.8 soldiers' worth** |
| mean per refill | 75.5 paint |
| robots that ever refilled | 19 of 776 (**2.4%**) |

**That is rare — about 1.7% of the paint a game spends on soldiers.** I am recording
the number before the gauntlet returns, because the pre-registered rule turns on it
and I do not want to be reading it after seeing a win rate.

Where the 1,005 legal hungry turns the census counted went, down to 26 firings:
transfer has a **cooldown of 10** (so the same robot cannot refill each turn), the
unit must have an **unused action** (by design — this never displaces), and, almost
certainly dominant, the **tower must hold more than 200 paint of surplus**, which
the tower census says happens on only 3.0-6.8% of tower-turns.

The surplus reserve is the one number in the mechanism, so the honest next question
is whether it is set too conservatively. I have queued a **headroom probe**, not a
dose search: `alice_i25r0` is `alice_i25` with the reserve set to **0** — a bound on
how often this mechanism could *ever* fire, never a shipping candidate, because
draining towers to empty would starve the build pipeline outright. If R=0 barely
moves the firing count, the whole direction is thin and the surplus reserve is not
what limits it; if it multiplies it, there is a real dose to explore and it belongs
to this iteration.

### The tournament, read correctly the second time — and a parse error I nearly reported as a tooling bug

`tournaments/20260908-0100` is the first tournament to run my post-iteration-24 bot
(`alice` @ `25c3160`). It was still in flight, with both `alice` pairs complete at
150 games each and `bob-carol` partial, so I read only the complete pairs.

**First I got it badly wrong, and the way it went wrong is the lesson.** I tallied
field 2 of each `RESULT` line as the winner and got a perfect **75-75 in both alice
pairs, with zero swept maps out of 75, in every pair.** Zero sweeps is the exact
signature my own mirror null produces for *identical code*, so this looked like a
serious tournament-runner fault — three different bots at three different commits
behaving like copies of one another.

I did not report it, because the charter says to run the discriminating case before
naming a fault. The discriminating case here was not a match: it was **reading the
line that writes the field**. `tools/tournament.sh:163`:

```
printf 'RESULT %s %s %s %s %s\n' "$TA" "$TB" "$MAP" "${W:-?}" "${R:-?}"
```

Field 2 is **team A**, field 3 is **team B**, and the winner is the *fourth* field's
`A`/`B`. Since every map is played twice with the assignment swapped, field 2 is
`alice` in exactly half of the games **by construction** — my "perfect 1-1 split"
was an identity of the file format, and my "zero sweeps" measured nothing at all.

Two things worth keeping:

1. **A statistic that comes out *exactly* symmetric is a format hypothesis, not a
   finding.** 75-75, 75-75, and A=180/B=180 exactly — three independent-looking
   quantities all landing on perfect symmetry. Real bots do not do that; file
   formats do.
2. **The discriminating case for "what does this field mean" is the code that
   writes it, not more of the data.** I could have stared at winner/side/round
   patterns for a long time — and I did, for a while, building increasingly
   elaborate theories about side bias — while a one-line `grep` in a tool I am
   allowed to read settled it outright.

**Corrected standings, complete pairs only:**

| pair | record | win% | swept | swept against | split |
|---|---|---|---|---|---|
| **alice vs bob** | **39-111** | **26.0%** | **8** | 44 | 23 |
| alice vs carol | 103-47 | 68.7% | 39 | 11 | 25 |

Against the previous full tournament (`20260907-1300`, which ran `alice` at
**iteration 14**):

| | then (iter 14) | now (iter 24) |
|---|---|---|
| alice vs bob | 7.3%, swept **1** vs 65 | **26.0%, swept 8** vs 44 |
| alice vs carol | 68.7%, swept 42 vs 14 | 68.7%, swept 39 vs 11 |

**The bob gap has closed substantially** — 7.3% to 26.0%, and my swept maps went
1 -> 8 while bob's fell 65 -> 44. That is the ten iterations since, measured against
an opponent my lineage did not produce, which is the only instrument here that
cannot be self-referential. Against carol the headline is unchanged at 68.7%, but
carol accepted **nine** iterations in the same window (through iteration 29), so
holding station there is not stagnation.

Bob is still the target: 23 split maps out of 75 means that matchup has most of its
resolution intact, and 44 swept losses are real losses, not spawn luck.

### The headroom probe — the reserve IS the limiter, and taking the headroom would re-open iteration 5

`alice_i25r0` is `alice_i25` with the surplus reserve set to 0 (a bound, never a
shipping candidate). Same map, same opponent, same everything else:

| | R = 200 (shipping) | **R = 0 (bound)** |
|---|---|---|
| refills fired | 26 | **173** (6.7x) |
| paint withdrawn | 1,962 (9.8 soldiers) | **14,037 (70.2 soldiers)** (7.2x) |
| robots that ever refilled | 19 of 776 (2.4%) | **118 of 740 (15.9%)** |

So the answer to "is the reserve set too conservatively?" is **yes, mechanically** —
the reserve, not the cooldown and not the adjacency, is what holds firing down. The
direction is not thin. There is a 7x dose ladder sitting there.

**And I am not going to climb it, for a reason that is worth more than the ladder.**

`R = SOLDIER.paintCost` is not a cautious round number I picked. It is exactly the
value that guarantees **a tower can always still afford a soldier**, and iteration 5
exists because tower paint falling below that point is an **absorbing state**:

> once tower paint reaches 0 only the 100-paint mopper is affordable, moppers
> complete no tower patterns, so paint income never recovers (Mirage: dead at r200,
> coverage 132 -> 15 per-mille).

At R = 0 a single passing soldier can drain a tower to empty. That is not a dose of
the same mechanism; it is a re-opening of a failure mode this lineage already
measured, fixed, and accepted. R = 100 (mopper cost) is softer but sits *inside* the
same trap — it guarantees only the unit that cannot escape the absorbing state.

**The transferable form:** *the headroom in a mechanism is not free capacity if the
thing capping it is a previously accepted fix.* A 7x firing increase reads as
"under-dosed" only if you look at the mechanism alone; read against the ledger it is
"correctly dosed at the boundary of a known cliff". Before spending headroom, check
what put the cap there — and if the answer is an earlier accepted iteration, the
dose search is not a dose search, it is an **ablation of that iteration**, and it
must be gated on *that* iteration's metric (the mopper/soldier spawn mix and the
paint-income trajectory) rather than on a win rate.

So R=100 is recorded here as a **legitimate future ablation with a named gate**, not
as a tuning knob: it may be run only with the absorbing-state instrumentation from
iteration 5 attached, and it must clear that gate *before* its win rate is looked at.

## Replay evidence from the tournament — I do not plateau, I COLLAPSE, and bob uses the exact mechanic I just built

Non-blocking work while the iteration 25 gauntlet ran. Source:
`arena/tournaments/20260908-0100/replays/alice-vs-bob-on-DefaultLarge.bc25` — a
sanctioned cross-lineage channel, and the only games here against an opponent my
lineage did not produce. T1 is alice, T2 is bob. Bob won at round 1746,
`MAJORITY_PAINTED`.

| round | alice cov | bob cov | alice $ | bob $ | alice twPaint | bob twPaint | alice tw | bob tw | alice spl | bob spl | alice xfer | bob xfer |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 40 | 146 | 178 | 370 | 500 | 1300 | 380 | 4 | 3 | 0 | 0 | 0 | 2 |
| 280 | **589** | 390 | 3,690 | 1,225 | 1,205 | 2,516 | 15 | 8 | 0 | 5 | 0 | 0 |
| 400 | 562 | 418 | 1,320 | 1,245 | 1,335 | 2,366 | 14 | 8 | 0 | 8 | 0 | 18 |
| 800 | 494 | 484 | 1,860 | 1,295 | 1,000 | 3,410 | 13 | 9 | 0 | 7 | 0 | 3 |
| 1200 | 461 | 505 | **36,630** | 1,445 | 810 | 3,126 | 12 | 10 | 0 | 9 | 0 | 70 |
| 1600 | **349** | **627** | **36,830** | 1,447 | **680** | 2,072 | 10 | 12 | 0 | 10 | **0** | 65 |

**I had the shape of this game wrong.** I have been describing my weakness as a
*plateau* — "the map saturates and I cannot take enemy ground". It is not a plateau.
**Coverage peaks at 589 per-mille around round 280 and then falls monotonically to
349.** I lose ground I already painted, for 1,300 rounds, while bob climbs from 390
to 627. The crossover is at round ~800.

That is a different defect with a different cause, and the previous framing would
have sent me looking for a way to *take* new ground when the actual failure is that
I cannot *hold* what I have.

### The mechanism is visible in the same table, and it is a paint-logistics failure

- **My chips balloon to $36,830 unspent** while bob sits at $1,447. Chips are not
  the constraint and have not been since iteration 2 — but this is a new extreme.
- **My total tower paint falls to 680 across 10 towers — 68 each**, against bob's
  2,072 across 12. My towers are too poor to build anything, which is why the chips
  pile up. **This is iteration 5's absorbing state re-emerging in the late game**,
  where I only ever looked for it early.
- Per 400-round window at round 1600: I spawn 130 soldiers and 47 moppers and lose
  **198 units, 116 of them to starvation**. Bob spawns 111 and 38 and loses 161, 88
  starved.
- And the payoff line: **my paint actions are 734 in that window against bob's
  1,608.** Similar unit counts, similar spawn rates, *less than half the painting*.

So I am converting tower paint into soldiers that walk out, starve, and die without
painting much, and then spending another 200 tower paint on a replacement that does
the same. Bob is not out-producing me — **bob's units simply paint more than twice
as much each.**

### Bob uses `transferPaint`. I use it zero times, in every window, all game.

`xfer` counts paint-transfer actions. Bob: 2, 18, 3, **70, 65**. Me: **0, 0, 0, 0, 0**.

This is independent corroboration of iteration 25's direction from a source that
had nothing to do with it — I found the unused mechanic by sweeping
`RobotController`, and bob was already using it heavily. But the replay also
sharpens *why* it matters, in a way my own censuses could not:

> **A refill is strictly cheaper than a replacement.** Both cost the same 200 tower
> paint. The replacement additionally costs 250 chips, a walk from the tower to the
> frontier, and the death of a unit that had already made that walk. The refill
> keeps a unit that is *already in position*.

That is the loop bob is in and I am not: refill -> fewer deaths -> less tower paint
churn -> towers stay rich -> more refills. Mine runs the other way, and the $36,830
and the 68-paint towers are what the bottom of it looks like.

### Which makes my R=200 reserve look like the wrong call, for a NEW reason

I argued above that `R = SOLDIER.paintCost` is correct because dropping below it
re-opens iteration 5's absorbing state. The replay says the absorbing state
**arrives anyway** — my towers reach 68 paint each by round 1600 with the reserve
fully in place. The reserve is not preventing the collapse; it is only preventing
the withdrawal that might have averted it.

And the argument that draining a tower re-opens iteration 5 is weaker than I
credited: iteration 5's failure was tower paint being **burned on moppers that
cannot paint**. My spawn rule already refuses a mopper unless a soldier was
affordable, so a tower under 200 paint builds *nothing* rather than spamming
moppers. Paint moved into an existing soldier is not burned — it is in a unit that
paints. Those are different fates for the same paint, and I conflated them.

**I am not changing the dose on this reasoning alone** — that would be fitting the
knob to a story from one replay of one map, which is exactly the error this log is
full of. It is recorded as the pre-registered ablation below, with its gate.

### Two more mechanics I field at zero and bob fields

- **Splashers**: bob 5 by round 280, 10 by round 1600. Me: **0**, all game, every
  game. My tower census says why (unreachable under the chip gate at 0.15-0.25%).
- **SRPs**: bob completes 4 resource patterns. Me: **0**. Never touched.

I am recording these as observations, not adopting them: what an opponent does is
evidence that something is *possible and survivable*, never evidence that it is
right for my bot. But "zero, all game, every game" for three separate mechanics is a
pattern about my lineage rather than about any one of them.

### Chasing the collapse: one hypothesis killed by reading, one that survives

**Killed — the enemy-tile attack burn.** The obvious explanation for "units starve
faster as the enemy's share grows" is the engine trap in `RULES.md` line 82: a
soldier attack on an enemy-painted tile debits the full 5 paint via `addPaint`
*before* bailing out, so it costs 5 and does nothing. If my soldiers were doing that,
the loss would scale exactly with enemy coverage and would explain the whole curve.

**They are not.** Both attack sites are guarded: the pattern loop carries
`if (t.getPaint().isEnemy()) continue;` (iteration 23, which was accepted for exactly
this) and the opportunistic branch tests `t.getPaint() == PaintType.EMPTY`. Dead
hypothesis, closed by reading the source rather than running anything — the cheap
direction doctrine prefers.

**Survives — passive UPKEEP, which scales with enemy coverage the same way.**
`RULES.md` line 47: a robot pays **-1/turn standing on a neutral tile, -2/turn on an
enemy tile, and 0 on an ally tile.** And `wander()` — the movement every soldier uses
when it has no ruin to work on — chooses its heading at random and its slide
direction by a **coin flip**, considering paint not at all. Nothing in my movement
has ever looked at what it is standing on.

Sizing it from numbers already in the table, with no new run:

| regime | bob coverage | my expected upkeep/turn | turns a 200-paint tank survives on upkeep alone |
|---|---|---|---|
| round 280 (my peak) | 390m | ~1.4 | ~143 |
| round 1600 (collapse) | **627m** | **~1.7** | **~118** |
| hypothetical, on ally paint | — | **0** | unbounded |

That is the positive feedback loop the coverage curve draws: **the enemy's share of
the map is a tax on my units' lifetime, so as bob's coverage grows my units starve
faster, so I spend more tower paint replacing them, so I paint less, so bob's
coverage grows further.** It is self-amplifying, which is the right shape for a curve
that peaks and then falls rather than levelling off.

### Pre-registered iteration 26 (only if 25 resolves first) — pick the slide by upkeep, not by a coin flip

The mechanism must not disturb iterations 12/14, which established that a **ballistic**
walk (long straight runs) beats a diffusive one and that *sliding* along an obstacle
rather than re-rolling the heading is worth real tower count. So the change is
deliberately the smallest one that touches no heading:

> `wander()` already picks between the left and right slide **at random** when the
> heading is blocked (`if (rnd(2) == 0) swap(l, r)`). Replace that coin flip with a
> preference for the tile whose paint is **ALLY over EMPTY over ENEMY**.

The heading, the run length, and the slide-instead-of-reroll behaviour are all
untouched. The coin flip is being *spent* rather than *added to* — the same "capability
preserved at zero marginal cost" shape as iterations 22 and 24, both of which were
accepted. Zero tuned constants.

**Pre-registered gate**, before any data: > 50% head-to-head vs the accepted snapshot
read as net swept maps, zero exceptions, no bytecode overruns, plus a firing count
(how often the two slide candidates differ in paint type — if they almost never
differ, the mechanism cannot be the cause of any result, exactly as for iteration 25).

**And a named risk I am recording now so it cannot be rationalised later:** preferring
ally paint biases movement *back toward my own territory*, which is the opposite of
the outward exploration iterations 12 and 14 bought. If this wins, I must check tower
count and coverage-at-round-200 did not regress, because a bot that huddles on its own
paint could win the upkeep argument and lose the expansion one.

**Reachability pre-check FIRST, before writing iteration 26 — the lesson of this
whole session applied to my own next plan.** The slide only runs when the heading is
**blocked**, which on an open map may be rare. Twice today a mechanism that looked
obviously worthwhile turned out to be gated by something I had not counted (the
splasher at 0.15-0.25%, the refill at 26 firings a game). So iteration 26 does not get
written until a census answers: *how often is the heading blocked, and on what share
of those turns do the two slide candidates actually differ in paint type?* If that
product is small, the mechanism is thin no matter how good the upkeep argument is, and
the right change is a different one — biasing the heading re-roll, which happens every
`WANDER_RUN` = 25 steps and is therefore far more frequent, at the cost of touching
the ballistic walk that iterations 12 and 14 bought.

I am writing that down *before* the census rather than after, because "the mechanism
was thinner than I thought, so here is a bigger version of it" is a rationalisation if
constructed afterwards and a plan if committed beforehand.

### Caught before it mattered: my mirror null was STALE

`MULTI_AGENT.md` warns that a mirror must be regenerated from **the baseline the
candidate is measured against**, and that the subtle version of the failure bites
*after an accept*, because the baseline moves. Mine had drifted exactly that way:
`src/alice_mirror` was still a copy of a **pre-iteration-24** build — it lacked
`i24Moves` entirely, so it predates the mopper hold branch I accepted as iteration 24.

Had I read iteration 25's margin against it, I would have been attributing to the
refill every game that **iteration 24's already-accepted mechanism** flipped. The
document says two nulls one accept apart disagreed on 6 of 40 games — same net
margin, different games — which is precisely the size of effect I am trying to
resolve here, where the whole result is +1 map.

Regenerated from `alice_iter24` and verified byte-identical apart from the package
line. Recording the *tell* for next time, because I did not catch this by suspicion —
I caught it by running the diff as a routine step before using the instrument:
**a mirror is a build like any other, and "I made it once" is not "it is current".**
The check costs one `diff` and there is no reason ever to skip it.

## Iteration 26 is DEAD before it was written — the pre-check did its job for the third time today

`src/alice_upkeepcensus` on DefaultLarge (queries only; the `rnd()` stream is
untouched, so the RNG sequence is preserved). 82 robots, 5,115 robot-turns.

### The mechanism is unreachable: 4 firings in a whole game

| step | count | share |
|---|---|---|
| `wander()` calls | 2,280 | 44.6% of robot-turns |
| heading **blocked** (the slide runs) | 691 | 30.3% of wander calls |
| **both** slide candidates legal | 79 | **11.4% of blocked** |
| **the two candidates DIFFER in paint type** | **4** | **0.08% of robot-turns** |

The slide itself is common — 691 times a game, far more than I feared. What kills it
is the next step: when the heading is blocked, **usually only one of the two slides is
legal at all**, so there is no choice to make. The coin flip I proposed to spend is
only actually *spent* on a real decision 79 times, and the two options differ in paint
type **4 times in the entire game**.

So the pre-registered iteration 26 mechanism cannot cause any result, and per the rule
I wrote before building it, it does not get built. **Third mechanism killed by a
reachability pre-check today** (splasher: 0.15-0.25%; refill: 26 firings; slide: 4),
and this one cost a single match instead of an iteration.

Worth noting what the pre-check protected me from specifically: I had a *good* causal
story, a self-amplifying feedback loop that matched the shape of the coverage curve,
and a mechanism with the zero-cost shape that has twice been accepted. Every part of
that was persuasive and none of it was reachability.

### And the upkeep premise itself is 5x smaller than I sized it

| where units stand | share of robot-turns | upkeep |
|---|---|---|
| **ALLY paint** | **81.8%** | 0 |
| neutral | 13.4% | -1 |
| **ENEMY paint** | **4.8%** | -2 |
| | **total 1,554 paint = 7.8 soldiers** | **0.30/robot-turn** |

I predicted ~1.4-1.7 upkeep per robot-turn from the *map coverage shares* in the bob
replay. The measured value is **0.30**. The error is instructive and it is not
arithmetic:

> **A global share is not the distribution an agent samples.** I computed my units'
> exposure to enemy paint by assuming they are spread uniformly over the map. They are
> not — they stand on their own paint 81.8% of the time, *because they paint where they
> walk*. The tile under a unit is caused by that unit, so map-level coverage is close to
> the worst possible estimator of it.

That is the same family as the post-spend affordability artefact from earlier tonight:
in both cases a statistic was **conditioned on the very thing it was being used to
predict**, in opposite directions.

### The caveat that matters more than either result — my instrument cannot produce the regime I lose in

This game ended at **round 313** with my own bot winning on MAJORITY_PAINTED. The
upkeep hypothesis is about the **late** regime in the bob replay: after round 800, with
bob holding 63% of the map and my coverage falling. **I measured the early regime of a
game I was winning, and the hypothesis is about the late regime of a game I was
losing.**

I cannot fix that by choosing a different map, and the reason is structural:

> **Every opponent I can play is my own lineage, and my own lineage loses the way I
> lose.** A gauntlet against `alice_iter24` cannot produce a game in which a stronger
> opponent out-paints me for a thousand rounds, because there is no such opponent in my
> workspace. The only games that contain the losing regime are the twice-daily
> tournament games against bob and carol, which I can read as replays but cannot
> instrument, because instrumentation requires my code to be running and the tournament
> plays my last commit.

So: the *mechanism* verdict (4 firings, dead) is safe — reachability does not depend on
regime. The *premise* verdict (upkeep is only 0.30/turn) is **not** safe, and I am
recording it as **measured in the wrong regime and therefore unresolved**, rather than
as a refutation. Those are different claims and I would be over-reading the census to
merge them.

**What would resolve it**, for whoever picks this up: commit an instrumented build so a
*tournament* game carries the counters, then read them out of the tournament replay. The
tournament runs my last committed `src/alice`, so this costs one commit of a census
build — which also means shipping instrumentation into a rated game, and that trade
needs deciding on purpose rather than in passing.

### Control: the upkeep census did NOT perturb the game

The census game ended at round 313 with my own bot winning on MAJORITY_PAINTED, which
is not what a mirror-shaped matchup usually looks like, so I checked rather than
assumed. `alice_mirror` (byte-identical to `alice_iter24`) vs `alice_iter24` on the same
map: **alice_mirror (A) wins at round 313, same reason.** Identical winner, identical
round count.

So round 313 is a property of DefaultLarge's side asymmetry, not an artefact of the
instrumentation, and the census's counters describe the shipping bot's real behaviour.
That is the positive control this session's first LEARNINGS entry demands, run on an
instrument whose *output* was fine but whose *fidelity* was unverified — a different
question from "did it emit anything", and one I would not have asked a day ago.

## Iteration 25 result vs the accept gate — it passes the letter, and the letter is not enough

The gate opponent's 50 games completed first, so this is final for the gate:

| | |
|---|---|
| head-to-head vs `alice_iter24` | **26-24 (52%)** |
| swept wins / swept losses / split | **4 / 3 / 18** |
| net swept maps (= margin over 50% = wins − N) | **+1** |
| identity check | 26 − 25 = +1 = 4 − 3 ✓ |
| exceptions | **0** |
| bytecode overruns | **0** |
| side balance | as A 12-13, as B 14-11 |
| swept losses | DefaultSmall, defensetower, galaxy |
| swept wins | Filter, MoneyTower, catface, starburst |
| mechanism firing count | 26 refills/game, 1,962 paint |

Against my pre-registered gate: **>50% read as net swept maps** — +1, passes. **No
unresolved one-directional regression** — the three swept losses are spread across map
types and the side split is 12-13 / 14-11, so there is no direction to it; passes.
**Zero exceptions, zero overruns** — passes. **Non-zero firing count** — 26, passes.

**So it passes, and I am not going to snapshot it on that basis.** Here is the reason,
and I want it stated as a rule rather than as a feeling about this number.

### Sweeps measure SENSITIVITY; the sweep DIFFERENCE measures benefit, and I nearly conflated them

My mirror null sweeps **nothing** — identical code splits every map, measured twice in
this project. So *any* swept map is proof that the mechanism really changed that game.
Here there are **seven** swept maps (4 + 3). That is decisive evidence the refill has a
real effect on outcomes.

It is **not** evidence that the effect is good. Four went my way and three did not.

> **`SW + SL` measures how much the mechanism perturbs; `SW − SL` measures whether the
> perturbation helps. A zero-variance null makes the first large and significant while
> the second stays a coin flip, and quoting the first as if it supported the second is
> the error the whole swept-map doctrine is otherwise designed to prevent.**

This is the sharp form of something my ledger already half-contains. The doctrine says
"a swept map is a near noise-free instrument" and "swept-map counts deserve more weight
than headline win rates" — both true, and both about `SW − SL`. Read carelessly they
license "seven maps swept, that is a strong signal", which is exactly backwards here.

### The pre-registered criterion I am adding, stated so it binds future runs too

> **When `|SW − SL|` is small relative to `SW + SL`, the run has measured sensitivity
> rather than benefit, and a second fresh map sample is required before accepting.**

Here `SW + SL = 7` and `|SW − SL| = 1`. Compare iteration 24, which was `8` and `8` —
eight swept wins against **zero** swept losses. That is what a directed effect looks
like in this instrument, and iteration 25 does not look like it.

**This is a new hurdle and I am adding it after seeing the data, which is exactly the
move I criticise elsewhere — so I am being explicit about why it is legitimate here.**
It does not change the accept threshold and it cannot rescue or condemn this candidate
on its own; it demands *more evidence* rather than a different reading of the same
evidence, and it is stated in a form that binds every future iteration including ones
that would otherwise pass more easily. A goalpost that moves toward "measure again" is
different in kind from one that moves toward "and therefore I was right".

**Action: a confirmation gauntlet vs `alice_iter24` on a fresh random 25-map sample.**
Verdict on the pooled 100 games. Pre-registered now: pooled net swept maps > 0 accepts;
<= 0 rejects; and I will report the pooled `SW + SL` alongside, because if it stays
large with a small difference, the honest conclusion is *"this mechanism perturbs
outcomes without improving them"*, which is a finding about the refill and not a
failure of the experiment.

## An arithmetic self-check that reversed my conclusion — per-soldier output is EQUAL; bob just keeps twice the army alive

Working from the bob replay's round-1600 window I computed "paint actions per soldier
spawned": alice 734/130 = 5.6, bob 1608/111 = 14.5, and concluded **bob gets 2.6x more
painting out of every soldier he builds.** That reading had a whole strategy hanging off
it — that my soldiers wander with no legal paint target once the map saturates, and the
iteration to write was "steer a soldier toward EMPTY ground instead of wandering".

**The denominator is wrong.** Paint actions in a window are produced by the soldiers
*alive during* that window, not by the ones *spawned* in it. Against living soldiers:

| at round 1600, per 400-round window | alice | bob |
|---|---|---|
| soldiers alive | **25** | **51** |
| paint actions | 734 | 1,608 |
| **paint actions per soldier-turn** | **7.3%** | **7.9%** |
| soldiers spawned | 130 | 111 |
| deaths / of which starved | 198 / 116 | 161 / 88 |

**Per-soldier painting rate is the same.** Bob is not more efficient per unit at all —
he simply has **twice the standing army** while spawning *fewer* soldiers than I do. I
spawn 130 and hold 25; he spawns 111 and holds 51. The entire difference is **how long a
soldier lives.**

That inverts the strategy the bad denominator implied. "My soldiers have nothing to
paint" is not supported by anything — their painting rate is normal. The defect is that
they **die too fast**, and I compensate by spawning replacements, which is what drains
the towers to 68 paint and leaves $36,830 in chips with nothing to buy.

**And it points the other way on iteration 25 than my gauntlet did.** Unit lifetime is
exactly what a refill buys, and bob's `xfer` counts (65-70 per window against my zero)
say he buys it constantly. So the refill is aimed at the true defect; what the +1 net
result says is that **my dose is too small to move it** — 26 firings and 1,962 paint
against a deficit measured in *hundreds* of soldier-lifetimes.

I am recording the wrong version above rather than deleting it, because the error is
the fourth instance tonight of the same family — a statistic conditioned on, or divided
by, the wrong population — and the tell was available without new data: **"actions per
spawn" mixes a flow with a flow over different populations, while "actions per
soldier-turn" divides a flow by the stock that produced it.** When a ratio's numerator
and denominator are counted over different sets, the ratio names nothing.

## Mechanism verification for iteration 25 — the ENDS are verified, the proposed MIDDLE is not

Same map (UnderTheSea), same opponent (`alice_iter24`), baseline arm =
`alice_towercensus` (behaviourally the shipping bot; its instrumentation is
query-only and its fidelity was separately controlled above).

| T1 measure | baseline | **alice_i25 (R=200)** |
|---|---|---|
| coverage r500 / r1000 / r1500 / r2000 | 522 / 460 / 481 / **476** | 526 / 546 / 543 / **544** |
| tower paint r500 / r2000 | 1,260 / **850** | 1,620 / **2,253** |
| towers held | 13 | **15** |
| soldiers spawned (cumulative) | 187 | 193 |
| starvation deaths, windows at r1000 / r1500 | 47 / 46 | **35 / 33** |
| starvation deaths, final window | **66** | 85 |
| outcome | **LOST** (AREA_PAINTED) | **WON** (AREA_PAINTED) |

**The ends move exactly as predicted.** The baseline reproduces the decay I diagnosed
from the bob replay — coverage 522 -> 476 and tower paint 1,260 -> 850 — and the
candidate does not decay: coverage holds at ~544 and tower paint **rises** to 2,253,
which is the opposite direction. It also wins the map the baseline loses.

**The middle is not verified, and I am recording it open rather than asserting it.**
My proposed chain was *refill -> fewer starvation deaths -> fewer replacement spawns ->
tower paint accumulates*. Two of those links disagree with the data:

- **Cumulative soldier spawns are slightly HIGHER (193 vs 187), not lower.** The
  "fewer replacements" link is simply not there.
- Starvation deaths are lower in the middle windows (35/33 vs 47/46) but **higher in
  the final one** (85 vs 66), so even the first link is not monotone.

And there is a rival explanation sitting in the same table that I cannot exclude: the
candidate ends with **15 towers against 13**. More paint towers means more paint income,
which would raise tower paint stock on its own, with no help from the refill at all. Two
extra towers is also exactly the kind of difference a deterministic engine produces from
a handful of flipped actions — this arm is one map, and the mechanism only fired 26
times.

**So what this establishes is narrower than it looks:** the candidate's game does not
show the decay the baseline's does. It does **not** establish that 26 refills caused
that, and the honest competing hypothesis is chaotic divergence that happened to land
well. This is a single map chosen *because I already had its replay*, not sampled — so
it is mechanism verification, and it is not evidence of benefit. The gauntlet is the
only thing that speaks to benefit, and the gauntlet said **+1 net swept map with a 4-3
split**.

Both readings are now on the record and they point opposite ways. That is precisely
what the confirmation run is for, and it is why I did not let the encouraging replay
talk me out of running it.

## The R=0 ablation, resolved from replays already on disk — and it kills my proxy metric

I pre-registered that R=0 could only be judged on **iteration 5's absorbing-state
metric** (tower paint trajectory and spawn mix), *before* its win rate was looked at.
That gate can be evaluated entirely from replays already collected — no new games.

Three arms, same map (UnderTheSea), same opponent (`alice_iter24`):

| arm | refills fired | tower paint @r2000 | coverage @r2000 | starvation deaths, final window | outcome |
|---|---|---|---|---|---|
| baseline (R = infinity) | 0 | 850 | 476 | 66 | **LOST** |
| **alice_i25, R = 200** | 26 | **2,253** | **544** | 85 | **WON** |
| alice_i25r0, R = 0 | **173** | **728** | 490 | **29** | **LOST** |

**The absorbing-state gate rejects R=0 on its own terms.** Tower paint at R=0 ends at
**728 — the lowest of the three arms, below even the untreated baseline** — and its
trajectory falls all game (1,164 -> 1,030 -> 995 -> 728). That is the drain I argued
would happen, now measured rather than argued: withdrawing below one soldier's cost
takes paint the towers needed. `R = SOLDIER.paintCost` is vindicated as the boundary,
and the 7x firing headroom below it is headroom I was right not to spend.

### But the row that matters most is the one I did not expect

**R=0 more than halved starvation deaths — 29 against the baseline's 66 — and lost the
map anyway. R=200 had the *most* starvation of the three at 85, and won it.**

Across these three arms, **starvation deaths are anti-correlated with winning.** That is
the metric I have been treating as the objective since iteration 24, and the metric this
whole iteration was motivated by ("starvation is 31.1% of all deaths").

> **A symptom you can measure is not the objective, and a mechanism that improves the
> symptom most can be the one that loses.** R=0 buys unit lifetime by spending the tower
> paint that produces units at all. The starvation count sees only the first half of that
> trade, because the paint it consumed never became a unit that could starve.

That last clause is the whole trap in one line: **the metric improves partly *because*
the thing it measures was never created.** It is the same structure as the post-spend
affordability artefact from earlier tonight — a count conditioned on the outcome it is
being used to judge — arriving for the third time tonight in yet another disguise.

So: starvation deaths are demoted from objective to diagnostic. The objective is
coverage held and maps won, and on those the ordering is R=200 > R=0 > baseline.

**Caveat, stated plainly: this is one map.** All three arms are single games, chosen
because their replays already existed. The dose ordering is a hypothesis supported by a
coherent mechanism and one observation each, not a measurement of benefit. What it is
sufficient for is the pre-registered *gate* — R=0 fails the absorbing-state condition on
the tower-paint trajectory, which is a within-arm trend rather than a between-arm
comparison, and that verdict stands.

## My upkeep census was measuring only HALF the upkeep — caught by re-reading RULES, not by the data

The census reported **0.30 paint per robot-turn** of upkeep and I used that to say the
upkeep premise was "5x smaller than I sized it". That number is a **terrain-only**
figure, and `RULES.md` lines 48-54 are explicit that terrain is not the whole penalty:

> PLUS **-1 per adjacent (8-dir, r^2<=2) ally ROBOT**; doubled (-2/adj) on enemy tile.
> **The adjacency tax is charged on ALLY tiles too** — the ally-tile branch of
> `processEndOfTurn` is `addPaint(-allyRobotCount)`, so standing on your own paint
> waives only the *terrain* penalty, never the crowding one. A fully surrounded robot
> pays **-8/turn anywhere on the map**.

My census summed the terrain branch and never counted a neighbour. So the headline
finding of that census — *"units stand on ally paint 81.8% of the time, so upkeep is
small"* — is **not supported by what it measured**, and in the worst way: standing on
ally paint is exactly the case where the terrain term is **zero** and the *entire*
penalty is the adjacency term I omitted. The 81.8% figure that looked like reassurance
is the population for which my instrument was blind.

The terrain term is bounded at -2 (-4 for a mopper). The adjacency term is bounded at
**-8** and is unbounded in the sense that matters: it scales with how tightly my own
units pack, which is a property of my movement code and therefore something I can
change. I measured the small, fixed component and skipped the large, controllable one.

**How it was caught matters.** Not by the number looking wrong — 0.30 looked perfectly
plausible, and I had already written a conclusion on it. It was caught by re-reading the
spec line I was implementing *against the code I had implemented*, prompted by an
unrelated thought about crowding. The generalisation:

> **An instrument built from a rule you remember is an instrument that encodes your
> memory of the rule.** Re-read the source line beside the implementation, not before
> writing it — the error is invisible in the code, which computes exactly what its
> author believed.

Census extended to count adjacent ally robots and charge the tax at the correct rate
(doubled on enemy tiles; the mopper multiplier deliberately *not* applied to the
adjacency part, per the same rule). Re-running on **UnderTheSea**, a full 2000-round
game, rather than DefaultLarge, which ended at round 313 and gave me the early regime
when the question is about the late one.

**The prior conclusion is withdrawn, not merely amended:** "upkeep is only 0.30/turn"
should be read as "the *terrain* component is 0.30/turn, and the larger component was
not measured". The iteration-26 slide mechanism stays dead regardless — 4 firings a game
is a reachability fact that no upkeep number can rescue.


### Tournament 20260908-0100 completed — my corrected reading was exactly right

The coordinator's `report.md` landed for the run I had to re-parse. It confirms the
numbers I derived after fixing my awk, to the game:

| | report | my corrected reading |
|---|---|---|
| alice vs bob | **39-111 (26.0%)** | 39-111 (26.0%) |
| alice vs carol | **103-47 (68.7%)** | 103-47 (68.7%) |

Standings: **bob 70.3% (-22.0), alice 47.3% (+9.3), carol 32.3% (+12.7)**. My
head-to-head against bob moved **+18.7 points** and carol's overall moved +12.7 while
bob's fell 22 — consistent with both of us having closed ground on a bob whose bot did
not change as much in the window.

Worth noting for its own sake: the run I nearly reported as a **runner fault** is the run
that records my largest single improvement against the only opponent that matters. Had I
filed that report, the correction would have arrived attached to a claim that the
instrument was broken, which is a bad way to be right about anything.

## FOR THE COORDINATOR — a shared-working-tree git hazard whose recommended fix destroys a sibling's work

Hit while pushing a routine commit. `git pull --rebase --autostash` aborted with:

```
warning: fetch updated the current branch head.
fast-forwarding your working tree from commit 62fd64d...
error: Your local changes to the following files would be overwritten by merge:
        agents/bob/TRAINING_LOG.md
Please commit your changes or stash them before you merge.
Aborting
fatal: Cannot fast-forward your working tree.
After making sure that you saved anything precious from
$ git diff 62fd64d...
output, run
$ git reset --hard
to recover.
```

**The danger is the last line.** Git's own error text recommends `git reset --hard`,
and in this repo that would discard **a sibling agent's uncommitted work across the
whole tree** — precisely what `MULTI_AGENT.md`'s git rules exist to prevent. An agent
following the tool's advice, in good faith, at 3am, would destroy another lineage's
in-flight iteration and there would be no stash to recover it from.

The trigger is a race that is *normal* here rather than exceptional: three agents share
one working tree and one `.git`, so a sibling committing between my `fetch` and my
`merge` is an ordinary event, and it leaves the other agent's dirty files straddling a
branch head that moved underneath them.

**What I did instead** (recording the safe recipe, since I had to work it out under a
message actively recommending the unsafe one):

1. `git log --oneline -3` — confirmed my commit had already landed locally.
2. `git status --short --untracked-files=no` — confirmed **no** modified tracked files
   remained, i.e. nothing of anyone's was hanging.
3. `git stash list` and `git rev-parse --verify refs/stash` — confirmed **no orphaned
   autostash** was holding a sibling's work hostage.
4. `git log HEAD..origin/main` — empty, so `origin/main` was merely a stale ref and the
   local branch was *ahead*, not diverged. Nothing to reconcile at all.
5. Plain `git fetch` + `git pull --rebase` + `git push`, no `--autostash`, no reset.

I did **not** read `agents/bob/TRAINING_LOG.md` at any point to check whether their work
survived — that is their workspace and isolation binds regardless of how convenient an
exception would be. What I could verify without reading it is that the tree holds no
modified tracked files and no stash exists, and that a `bob` commit touching that file
sits on top of mine, which together are consistent with them having committed it
themselves.

**Suggested mitigation for `tools/`**: a shared `git-sync` helper that refuses to run
`reset --hard`, checks `refs/stash` and `HEAD..origin/main` before acting, and fails
loudly with the safe recipe rather than leaving each agent to improvise against git's
own bad advice. Reporting rather than working around it, per the charter — my step-by-step
recovery above is exactly the "hand-transformation that holds only as long as I remember"
the charter warns about, and it should not be the answer for three agents indefinitely.

## Corrected upkeep census — the component I omitted is the LARGER one, and upkeep burns 45% of all unit paint

`alice_upkeepcensus` with the adjacency tax added, on **UnderTheSea, full 2000 rounds**
(the regime the hypothesis is actually about). 735 robots, **76,105 robot-turns**.

| | paint | per robot-turn | share of upkeep |
|---|---|---|---|
| **terrain** (-1 neutral, -2 enemy, mopper x2) | 27,916 | 0.367 | 48.2% |
| **adjacency** (-1 per adjacent ally robot, x2 on enemy tile) | **29,967** | **0.394** | **51.8%** |
| **total upkeep** | **57,883** | **0.761** | |

**The half I never measured is the bigger half.** My withdrawn "0.30/robot-turn" was
not merely incomplete; it was the smaller of two comparable terms.

### Sizing it against the paint that exists

Cumulative spawns across the four windows: **550 soldiers and 180 moppers** =
`550x200 + 180x100` = **128,000 paint** committed to units all game.

> **Upkeep consumes 57,883 of that 128,000 — 45% of every drop of paint this bot puts
> into a unit is spent standing still.** The crowding component alone is 29,967 paint =
> **150 soldiers' worth**, or about 6,000 tiles never painted.

That reframes the whole late-game collapse. It is not that my units cannot find work; it
is that **nearly half their tank is gone before they do any.**

### Two checks on the instrument, both passing

- **Self-exclusion.** If `senseNearbyRobots(2, myTeam)` included the caller, mean
  adjacency would floor at 1.0. Measured mean is **0.362**, so it excludes self and the
  tax is not inflated by one per turn. I designed this check before reading the number,
  precisely because an off-by-one here would have been invisible and would have doubled
  the headline.
- **Regime.** Enemy-tile share is **16.0%** here against **4.8%** in the DefaultLarge
  game that ended at round 313. **The regime caveat I flagged was real and it mattered** —
  the short game understated enemy-tile exposure by more than 3x. Recording that as
  vindication of the caveat, not of the hypothesis: I was right that the measurement was
  in the wrong regime, which is a different thing from being right about upkeep.

### What this does and does not license

It does **not** resurrect iteration 26. The slide preference fires **4 times a game**;
that is a reachability fact and no upkeep figure changes it.

It does size a **new** direction properly for the first time: crowding is worth 150
soldiers of paint a game. But the tax is **diffuse, not concentrated** — mean adjacency
is 0.362 and only **1.3%** of turns have 3+ adjacent allies. So a "break up when crowded"
rule would fire rarely and capture little, while an "always prefer the less crowded move"
rule collides head-on with the ballistic wander that iterations 12 and 14 bought.

**That tension is the actual open question, and I am leaving it stated rather than
resolved:** the money is real (150 soldiers) but it is spread across 76,105 turns in
increments of one paint, and the only mechanisms that could collect it all are the ones
that would damage a previously accepted behaviour. Anyone picking this up should size the
*collectable* fraction first — the pre-check that this session's three dead mechanisms all
needed and only got twice.

### A reusable gate reader, and the contrast it makes visible

Wrote `tools/gate-read.sh` (my own workspace tools, not shared `tools/`): prints
record, `SW`, `SL`, split and margin per opponent, and **checks the margin identity
`wins − N == SW − SL` on every row**. It also carries the RESULT field layout in a
comment, because misreading field 2 as the winner is the error that cost me a phantom
"the tournament runner is broken" report earlier tonight, and a comment in the tool is
the only version of that lesson that survives a session ending.

Run 20260908-014924, all three opponents (identity `OK` on every row):

| opponent | record | SW | SL | split | margin |
|---|---|---|---|---|---|
| `alice_flood` | 44-6 | **19** | **0** | 6 | **+19** |
| **`alice_iter24`** (the gate) | **26-24** | **4** | **3** | 18 | **+1** |
| `alice_iter7` | 42-1 | **20** | **0** | 2 | **+20** |

**This is the sensitivity-versus-benefit distinction drawn in a single table.** Against
the bots this lineage has already left behind, the effect is enormous *and one-directional*:
19-0 and 20-0, not a single swept loss between them. Against the build it is actually
trying to beat, the same candidate goes **4-3**.

Twenty-four iterations of accumulated change produce a clean directed signal. This one
increment does not, and the shape of the failure — sweeps in *both* directions — is
exactly what a mechanism that perturbs without improving looks like. If I had reported
only the headline (**81.3% overall**, which is what this run's three opponents average to)
I would have described a triumph.

### Resampling over maps — the correct error model, and it says +0.38 sd

`tools/map-resample.py` on the completed run (bootstrap and jackknife over **maps**,
which is the unit that actually varies between one estimate and the next):

| opponent | score | boot se | 95% CI | distance from mirror null (25/50) | per-map wins {0,1,2} |
|---|---|---|---|---|---|
| `alice_flood` | 44/50 | 2.13 | [40, 48] | **+8.93 sd** | {1: 6, 2: 19} |
| **`alice_iter24`** | **26/50** | **2.65** | **[21, 31]** | **+0.38 sd** | **{0: 3, 1: 18, 2: 4}** |
| `alice_iter7` | 49/50 | 0.98 | [47, 50] | **+24.41 sd** | {1: 1, 2: 24} |

**The gate interval [21, 31] straddles the null.** +0.38 sd is as close to nothing as
this instrument reports, and it agrees with the sweep decomposition (4-3) that I reached
independently — two readings of the same run that could have disagreed and did not.

I want to be careful about *which* doctrine this run illustrates, because the ledger
carries a warning in both directions. `MULTI_AGENT.md` records a case where an sd-style
argument **under-sold** a real accept, and the fix was to resample over maps rather than
quote a binomial. That fix is exactly what produced the +0.38 here — this is the corrected
instrument, not the discredited one. And the per-map histogram is the reason: **18 of 25
maps split 1-1 and contributed literally nothing**, so the effective sample is 7 maps, not
50 games, and 4-3 on 7 maps is what it looks like.

The two flanking rows are the calibration that makes this readable. The same instrument,
on the same 25 maps, returns **+8.93 sd** and **+24.41 sd** against older builds. It is
perfectly capable of resolving an effect. It resolves nothing here.

**Confirmation launched** anyway, per the pre-registered action — 50 games, fresh random
25-map sample, vs `alice_iter24`. Pooled verdict on 100 games: net swept > 0 accepts,
<= 0 rejects. I am not cancelling it on the strength of +0.38 sd, because the pre-registered
rule said *measure again*, and quietly substituting *"the statistic already convinced me"*
for the measurement I promised is the same move as moving a goalpost, just in the
direction that happens to look rigorous.

### Absolute-strength instrument updated

Roster points recorded from the completed run and both charts regenerated:

| frozen opponent | `alice_i24` (previous) | **`alice_i25`** |
|---|---|---|
| `alice_iter7` | 88.0% | **98.0%** |
| `alice_flood` | 90.0% | 88.0% |

Read with the charter's own caveat: **these two runs used different random map samples**,
so 88 -> 98 against `alice_iter7` is a delta across samples and is noisier than it looks.
The within-run comparison is the sound one, and within *this* run the ordering is
`alice_iter7` 49/50, `alice_flood` 44/50, `alice_iter24` 26/50 — a clean monotone ladder
down the lineage's own history, which is what an improving bot should produce and is
independent of whether iteration 25 itself is real.

## Iteration 26, replacing the dead slide mechanism — the tower MIX is allocating 50% of my production to the resource I have $36,830 of

### The mismatch, stated from measurements already taken

| | mine | bob's |
|---|---|---|
| chips at r1200-1600 (bob replay) | **$36,830 unspent** | $1,447 |
| total tower paint at r1600 | **680 across 10 towers (68 each)** | 2,072 |
| tower type split | **~50/50 money/paint** | — |

`RULES.md`: a money tower produces **20/30/40 chips** by level; a paint tower produces
**5/10/15 paint**. My soldiers each cost 200 paint and 250 chips, and the census showed the
chip gate open on 80-94% of tower-turns while paint-affordability sat at 6-11%. **Paint is
the binding resource by every measurement I have, and I am spending half my tower slots on
the other one.**

Sizing, on the late-game state in that replay: shifting 4 of 16 towers from money to paint
adds roughly **40-60 paint/turn**, against a *whole-team* unit-paint budget of ~128,000
over 2,000 rounds (=64/turn). That is not a marginal adjustment — it is on the order of
**doubling** the paint income that feeds unit production, paid for with chips I demonstrably
cannot spend.

### The mechanism, and the trap I must not walk into

The obvious change — "decide the tower type from current money" — is **exactly what a
previous iteration removed**, and the code says why:

```java
// parity: ~50/50 money/paint mix, decided by the map (identical for
// both teams), immune to the money-at-mark-time timing artifact that
// made every early mark a money tower.
UnitType wantTower = ((ruin.x + ruin.y) & 1) == 0 ? MONEY : PAINT;
```

A ruin is *marked* long before its pattern is *completed*, so a money-sensitive rule reads
the wrong moment and collapsed to all-money early. That property was bought and must be
kept.

**So the trigger stays map-decided and only the RATIO moves** — one knob, one line, and the
timing-artifact immunity is preserved exactly:

```java
((ruin.x + ruin.y) & 3) == 0   ->  25% money / 75% paint
```

Still a function of ruin coordinates alone, still identical for both teams, still immune.

### Pre-registered, before any run

- **Reachability is not in question for once**: this fires on every tower mark, 13-16 times
  a game, and changes roughly a quarter of them. That is the first mechanism this session
  whose firing rate needs no pre-check — worth noting, because the three that did all died.
- **Gate**: >50% head-to-head vs the accepted baseline read as **net swept maps**, with `SW`
  and `SL` reported separately per tonight's rule; 0 exceptions; 0 overruns.
- **Named risk, and it is the real one**: chips are abundant *late* and tight *early* — at
  round 40 of the bob replay I held **$370**. Iteration 2's `CHIP_RESERVE` exists because
  greedy spending stalls tower completions permanently. So the failure mode is an early-game
  stall that never recovers, and **the diagnostic must be tower count at round 200**, not the
  end-state economy. If tower count at r200 regresses, the dose is wrong regardless of the
  win rate.
- **Dose discipline**: `& 3` (25% money) is one step. If it wins, the next question is `& 7`
  (12.5%), and that is a *separate* iteration — not a search run in the same breath.

Not started: the iteration 25 confirmation owns the VM, and starting a second candidate
before the first has a verdict is how a lineage ends up unable to attribute either.

### The confirmation's map sample OVERLAPS the first run's by 6 maps — pooling naively would double-count them

`comm -12` on the two runs' `maps.txt`: **6 of 25 maps are shared**, so the two samples
cover **44 distinct maps**, not 50.

This matters because of the property the whole session's reasoning rests on: **the engine
and both bots are deterministic**, so a repeated (map, side) cell is not a second
observation — it is *the same observation played again* and must produce the identical
result. Pooling the two runs by simply adding `SW` and `SL` would count those 6 maps
**twice**, biasing the pooled margin by whatever they happened to do the first time, in
whichever direction that was.

My pre-registered rule was *"pooled net swept maps > 0 accepts"* and I wrote it without
anticipating sample overlap. Correcting the arithmetic — pooling over **distinct maps** —
is not a goalpost move: it is the same rule computed on the population it always named,
and I am fixing it *before* seeing the second run's results, which is the only time such a
correction is cheap to trust.

**And the overlap is a free instrument check I would not otherwise have had.** Those 6
maps were played by the same two committed builds in both runs. If determinism holds, all
12 games must match exactly. If any differ, then the null is *not* variance-free, and the
reasoning behind "identical code sweeps nothing", "a swept map is a near noise-free
instrument", and tonight's whole sensitivity-versus-benefit argument would need revisiting.
I get that test for nothing, and it tests an assumption I have been leaning on all session
without ever having verified it myself in a full run.

Pre-registering the reading now: **12 of 12 identical -> determinism confirmed, pool over
44 distinct maps. Any mismatch -> stop and report it**, because a non-deterministic engine
is a bigger finding than iteration 25 either way.

## Dose sizing for the refill, all three variants — and the frequency knob runs BACKWARDS

`alice_i25h` = `alice_i25` with the hunger gate opened from "below half capacity" to
"any deficit at all". Two lines differ (package + gate); the surplus reserve is untouched,
so unlike `alice_i25r0` it cannot re-open iteration 5. One match each, UnderTheSea vs
`alice_iter24`:

| variant | reserve | hunger gate | **refills fired** | **paint delivered** | robots refilling |
|---|---|---|---|---|---|
| `alice_i25` | 200 | below half | 26 | **1,962 (9.8 soldiers)** | 2.4% |
| **`alice_i25h`** | 200 | **any deficit** | **59 (2.3x)** | **865 (4.3 soldiers) — 0.44x** | 3.0% |
| `alice_i25r0` | **0** | below half | 173 | 14,037 (70.2 soldiers) | 15.9% |

**Opening the hunger gate more than doubled the firing count and more than halved the paint
delivered.** The knob runs backwards on the quantity that matters.

The reason is mechanical once seen: a nearly-full unit that tops up takes only the few paint
it has room for (`min(capacity - paint, surplus)`), burns the **cooldown of 10**, and nibbles
the tower's surplus. When it is *actually* hungry a little later, the big top-up it could
have taken is smaller or gone. **The <50% gate is not a throttle — it is a rule that waits
until a withdrawal is worth its cooldown.**

And note what would have happened had I sized this by firing count, which is exactly what my
own pre-registered gate asks for: `i25h` fires 2.3x more often and looks like the stronger
dose on the number I told myself to watch. **A firing count answers "is this reachable?" and
nothing else. It is not a measure of how much the mechanism does.** Tonight's third
appearance of "the count is not the quantity", after the summed-maximum bound and the
starvation metric.

### What this settles about iteration 25

`alice_i25`'s original design — reserve at `SOLDIER.paintCost`, hunger at half capacity — is
**the best-calibrated of the three on the mechanism's own currency**, and both knobs were
chosen from engine constants rather than searched. R=0 delivers 7x more paint and loses the
map by draining towers; the open hunger gate delivers less than half.

So there is **no easy dose rescue**. The refill is simply a small mechanism: 1,962 paint in a
game that commits 128,000 to units — **1.5%**. That is entirely consistent with a +1 net
swept map and +0.38 sd, and it means the honest reading of iteration 25 is *"correctly built,
correctly aimed, and too small to measure"* rather than *"promising but under-dosed"*.

Which is the argument for iteration 26 being the tower mix instead: that one reallocates
**half of all tower production**, not 1.5% of unit paint.

## Session death, then the recovery — and the determinism check came back CLEAN

The confirmation run (`20260908-024242`, `alice_i25` vs `alice_iter24`, 50 games) **finished
on the VM and was never collated here**: the session died between the last poll and
`collate_run`. On disk it had `results.txt` with all 50 games and no `results.csv`,
no `summary.txt`. `gauntlet-collect.sh 20260908-024242` recovered it in one call. Nothing
was re-run; the finished games were still there, exactly as MULTI_AGENT.md says they would
be, because the runner is setsid-detached and outlives the session that started it.

### The pre-registered determinism check: 6 shared maps, 12 games, 12 matches

| shared map | run1 (side,winner) | run2 |
|---|---|---|
| DefaultHuge | AA, BA | identical |
| Filter | AA, BB | identical |
| PlumberGame | AB, BB | identical |
| Restart | AA, BA | identical |
| Snowglobe | AB, BB | identical |
| yearofthesnake | AB, BB | identical |

**12 of 12 identical -> determinism confirmed on a full run**, by my own hands rather than
by assumption. This is the first time this lineage has verified it end-to-end, and it is
the assumption underneath "identical code sweeps nothing", "a swept map is a near
noise-free instrument", and every dose-response argument in this log. It holds.

The check cost nothing — it was a by-product of an overlap I only noticed because I went
looking for the double-counting bug. Tool committed as `tools/determinism-check.sh`.

### Pooling over 44 DISTINCT maps, as pre-registered

| | SW | SL | split | record |
|---|---|---|---|---|
| run 1 (`20260908-014924`, 25 maps) | 3 | 3 | 19 | 25/50 |
| run 2 (`20260908-024242`, 25 maps) | 6 | 2 | 17 | 29/50 |
| **pooled, 44 distinct maps** | **9** | **5** | **30** | **48/88 (54.5%)** |

Pre-registered gate — *pooled net swept maps over distinct maps > 0* — **passes at +4**.

And a map-level bootstrap (20,000 resamples over the 44 maps) says what the gate cannot:
**54.5%, 95% CI [46.6%, 62.5%], +1.09 sd, P(<=50%) = 0.173.** The gate passes and the
interval straddles the null. That is the definition of a thin margin.

### Why the frozen roster is NOT the right check here, though rule 12 asks for one

Doctrine rule 12 says: on a thin accept margin, run the frozen roster *before* accepting.
I went to do exactly that and stopped, because rule 9 forbids what it would produce.
The roster's seven opponents sit, on their most recent readings, at:

`alice_iter0` 100%, `alice_iter1` 100%, `alice_iter4` 98%, `alice_iter12` 96%,
`alice_iter7` 88-98%, `alice_flood` 88-92%, `alice_iter23` 66%.

**Six of seven are pinned above 88%.** Rule 7: an instrument pinned near 100% cannot
resolve a few games. Rule 9: never accept or reject on a lopsided instrument alone. So 350
games of shared VM time would buy six numbers that *cannot move* in response to a 1.5%
paint mechanism, plus one that can. Rule 12's own justification — "it once caught a bad
accept by ten games" — describes an instrument with resolution to spare. Mine has none.

### The check that DOES resolve it: stop sampling maps and take the census

The 44 distinct maps are a sample from a population of exactly **75** (`tools/bc25-maps.txt`).
The bootstrap interval above is entirely map-sampling noise — determinism means there is no
other kind. So the remaining **31 maps, 62 games**, do not widen the sample: they *exhaust*
it. Pooled with what I have, the result is a **census of the whole map pool**, and the
question "would a different 25-map draw have said something else" stops being answerable-in-
principle and becomes vacuous, because there is no other draw left.

That is doctrine rule 6's remedy applied literally — "re-measure the whole on the parts'
own pinned maps and the comparison stops being an estimate and becomes an arithmetic
identity" — for 62 games instead of 350, on the one instrument that is actually even.

**Pre-registered now, before the run returns:** the accept gate is net swept maps over all
75, `SW` and `SL` reported separately, 0 exceptions. Net > 0 accepts. I am not entitled to
a confidence interval on the result and will not report one — over a census there is
nothing left to be uncertain about at the map level, and saying "significant" of a
population parameter would be a category error.

## ACCEPT iteration 25 — the census settles it: +11 net swept maps over the ENTIRE 75-map pool

The 31 remaining maps came back 38-24, **SW 9 / SL 2, net +7** — on their own a stronger
result than the 44 maps that preceded them. Pooled with those, over the whole population:

| sample | maps | SW | SL | split | record | net swept |
|---|---|---|---|---|---|---|
| run 1 | 25 | 3 | 3 | 19 | 25/50 | 0 |
| run 2 (confirmation) | 25 | 6 | 2 | 17 | 29/50 | +4 |
| run 3 (the remainder) | 31 | 9 | 2 | 20 | 38/62 | +7 |
| **CENSUS** | **75 (all)** | **18** | **7** | **50** | **86/150 (57.3%)** | **+11** |

0 exceptions. 0 overruns. The margin identity checks on every row (`wins - N = SW - SL`).
And the three runs overlap in 6 map-cells that were re-pooled here; **not one disagreed**,
so determinism held across all three runs, not just the two I checked earlier.

**Gate: net swept > 0 over the census. +11. Accept.** Snapshotted `src/alice_iter25`,
promoted into `src/alice`.

### What a census does and does not license me to say

It removes exactly one uncertainty, completely: **there is no other 25-map draw that could
have said something different, because there are no other maps.** 57.3% is not an estimate
of the bot's win rate over the pool — it *is* the bot's win rate over the pool. The
bootstrap CI I computed at the 44-map stage, [46.6%, 62.5%], was measuring the width of a
sampling distribution that no longer exists, and quoting it now would be quoting the
uncertainty of a question I have since answered exactly.

What remains uncertain is **generalization**, which is a different thing and is not
narrower for the census being complete: these 75 maps are themselves a sample of
"maps a Battlecode bot might face", and 57.3% over them does not become 57.3% over maps
outside the pool. The census closes the sampling question and leaves the generalization
question exactly where it was.

### The resolution economics, which is the reusable part

`LEARNINGS.md` "my gauntlet's resolution collapses exactly where I need it most" says the
effective sample is **decisive maps**, and that the accept gate always has the fewest
because a candidate is by construction most similar to its own predecessor. The census
puts numbers on the fix:

| | maps | decisive | cost |
|---|---|---|---|
| one 25-map run | 25 | 7 | 50 games |
| pooled two runs | 44 | 14 | 100 games |
| **census** | **75** | **25** | **150 games** |

**25 decisive maps against 7.** The split fraction (~2/3) is a property of the *pair*, not
of the sample, so decisive maps scale linearly with maps played and the census is simply
the largest value the instrument can take. 150 games ran in ~32 minutes at MAXJOBS 3 —
about the cost of a 3-opponent 25-map gauntlet, which would have bought 7 decisive maps on
the row that matters and ~45 on two rows that decide nothing.

**And it is not the map-list overfitting the charter forbids.** That rule exists because a
hand-picked *subset* is something accepted iterations can drift toward. The full population
has no subset to drift toward — it is the unbiased maximum, and it is the opposite failure
mode. Recording this as a process change in `progress/milestones.txt`.

### Standing change to how I run the accept gate

**The accept gate is now the full 75-map census against the most recent accepted snapshot,
one opponent, no other rows.** Reasons, in order: it is the only row that gates anything;
it has the worst resolution of any row I can run; the census is its maximum resolution; and
a single-opponent census costs less than the 3-opponent runs I was doing, which spent most
of their games on lopsided rows that rule 9 forbids deciding on anyway.

## Iteration 26, re-based and re-registered BEFORE the run returns

Accepting iteration 25 invalidated the candidate I had already built. `src/alice_i26` was
`alice_iter24` + the tower mix, and iter24 is no longer the baseline. Running it against
`alice_iter25` would have measured **two** changes at once — adding the tower mix *and
removing the refill* — and whichever way it came out I could not have attributed it.

So the candidate under test is `src/alice_i26b` = `alice_iter25` + the ratio change, and
nothing else. Verified as a diff, not by intention: `alice_i26b` vs `alice_iter25` is 22
lines, of which 21 are the explanatory comment and **one is the mechanism**:

```java
UnitType wantTower = ((ruin.x + ruin.y) & 3) == 0 ? MONEY : PAINT;   // was & 1
```

`src/alice_i26` is left in place as the dead-end it is, rather than deleted, so a future
session that finds it in the tree can see from this entry why it was not the one that ran.

### The gate, restated for the census

- **Instrument**: `alice_i26b` vs `alice_iter25`, **all 75 maps, both sides, 150 games**.
  One opponent. This is the new standing gate recorded in `progress/milestones.txt`.
- **Accept iff net swept maps > 0** over the census, `SW` and `SL` reported separately,
  0 exceptions, 0 overruns.
- **No confidence interval will be quoted**, for the reason the iteration 25 entry gives:
  over a census there is no sampling distribution to have an interval on.

### The named risk stands, and it is the one to check FIRST

Chips are abundant late and tight *early* — at round 40 of the bob replay I held **$370**,
and iteration 2's `CHIP_RESERVE` exists precisely because greedy spending stalls tower
completions permanently. Cutting money towers to 25% is a bet that the late-game surplus
of $36,830 is not paid for by the early-game squeeze.

**Pre-registered diagnostic, independent of the win rate: tower count at round 200.**
If that regresses, the dose is wrong *even if the census comes out positive*, because a
mechanism that wins while damaging the thing it was predicted not to damage is winning for
a reason I have not identified — and doctrine rule 13 says a real effect shows up in more
than one place, which cuts both ways.

### Dose discipline, stated before I can be tempted by the result

`& 3` is **one step**. If it wins, `& 7` (12.5% money) is a *separate* iteration with its
own census, not a search run bolted onto this one. If it loses, the zero arm is already
measured — `alice_iter25` itself is `& 1` — so a loss gives me a two-point dose-response
curve (50% money vs 25% money) rather than a single dead candidate, and the next question
is whether the optimum is interior at some ratio between them.

## REJECT iteration 26 — decisively, and the premise was backwards

| | maps | SW | SL | split | record | net swept |
|---|---|---|---|---|---|---|
| `alice_i26b` vs `alice_iter25`, census | 75 | **8** | **29** | 38 | **54/150 (36.0%)** | **−21** |

0 exceptions. Margin identity OK. The gate asked for net swept > 0 and got **−21**: this is
not a near miss and not noise — it is the largest margin either direction I have measured
against my own predecessor. `src/alice` stays at `alice_iter25`.

That is a good outcome for one specific reason: **a −21 tells me something a −1 would not.**
It says the mechanism is large and aimed the wrong way, which makes the diagnostic worth
running. So I ran the pre-registered one.

### The diagnostic said "tower count at r200", and tower count was the least of it

Paired round-200 state, candidate against baseline **inside the same game** — the cleanest
comparison available, since both bots are in one replay under identical map and identical
opponent pressure. Side mapping verified from each replay's own `GameHeader` rather than
assumed, because `botB` files swap team1/team2 and eyeballing it would have inverted five
rows:

| map (side) | towers c/b | **tower paint c/b** | **coverage c/b** | soldiers c/b |
|---|---|---|---|---|
| AlarmClock (A) | 7 / 8 | **3869 / 725** | **303 / 448** | 6 / 9 |
| Barcode (A) | 4 / 8 | 1875 / 1290 | 355 / 500 | 6 / 7 |
| BatSignal (B) | 5 / 8 | **3347 / 697** | **288 / 618** | 3 / 14 |
| Brat (A) | 5 / 8 | **2951 / 1039** | **330 / 527** | 4 / 14 |
| Bread (A) | 6 / 6 | 347 / 2819 | 462 / 377 | 16 / 3 |
| BunnyGame (B) | 4 / 6 | **2910 / 18** | **220 / 292** | 8 / 3 |

**These six games are all LOSSES, and that is a selection, not a sample.** `gauntlet.sh`
pulls back only the losing replays, so every game I can inspect locally is one the candidate
lost. That is fine for "why did it lose" and it is *not* fine for "what does the mechanism
do on average" — the winning games would have to say something different, or the record
would not be 54-150. I am reading these as a mechanism trace, not as an effect size, and
the effect size comes from the census above, which has no such selection.

Tower count at r200 does regress (5.2 vs 7.3 mean over these six) so the pre-registered
diagnostic fires.
But it is a symptom, and two other columns say what of.

**The candidate sits on a mountain of paint it cannot spend, and loses the map.** Tower
paint runs 3-160x the baseline's while coverage runs *below* it — and coverage is the win
condition. A soldier costs **250 chips AND 200 paint**; a tower needs both. Converting
money towers to paint towers did not relieve a paint constraint, it **created a chip one**,
and the surplus simply moved from the chip column to the paint column while unit production
fell.

### RETRACTED BELOW — I named this fault before running the discriminating case

*The section that follows called the premise a reverse-causation error. **It is wrong**, and
the data that refutes it was already on my disk when I wrote it. It is kept verbatim, with
the correction after it, because a retraction that deletes its own error hides the shape of
the mistake.*

### The premise was a reverse-causation error, and I can now name it exactly

Iteration 26 rested on "$36,830 unspent chips at r1200-1600 of the tournament replay vs
bob". **That was measured in a game I was losing badly.** A bot that is losing has few
units and few places to put them, so its chips pile up. The surplus was a *consequence* of
losing, not a cause of it, and I read a symptom as a diagnosis.

The test that would have caught it costs nothing and I did not run it: **would the surplus
still be there in a game I was winning?** A resource that accumulates only when you are
behind is not a resource you are failing to exploit.

And the census gave me the mirror image as proof. Swap the mix and the pile does not
disappear — **it changes currency.** Whichever resource I over-produce accumulates, because
the constraint is the *ratio*, and iteration 25's 50/50 was already close to the soldier's
own 250:200 cost ratio. That is why `& 1` is hard to beat from this direction.

### The census measurement that misled me was pooled over heterogeneous producers

The other pillar was the tower census: "the chip gate is open on 80-94% of tower-turns
while paint-affordability sits at 6-11%". Both numbers are correct. Neither is a
**team-level** constraint, because the pool is half money towers — which by construction
almost never hold paint. Pooling affordability over producers that specialise in different
resources measures the *specialisation*, not the shortage.

This is doctrine rule 5's wrong-referent error again, in the one form the ledger had not
yet recorded: not a number computed against the wrong object, but a rate **averaged over a
population that the rate is not homogeneous across**. The tell was available and I missed
it: if paint were team-binding at 6-11% affordability, tower paint stocks would be near
zero, and the same census reported towers holding **>= 300 paint on 3.0-6.8% of
tower-turns**. Stock and shortage cannot both be true. Two artefacts that should have
reconciled, didn't, and I used both in the same argument.

### What iteration 26 leaves behind, which is more than it cost

A **two-point dose-response curve on a knob I had never treated as one**, with the zero arm
already accepted:

| money share | build | census vs iter25 |
|---|---|---|
| 50% (`& 1`) | `alice_iter25` | — (baseline) |
| 25% (`& 3`) | `alice_i26b` | **36.0%, −21 swept** |

The curve is steeply downhill toward paint. Per my own pre-registered dose discipline the
next step *was* to be `& 7` if this won; it lost, so `& 7` is dead on arrival and running it
would be a search for a worse point on a slope I have already measured. **The interesting
direction is the other one** — more money towers than 50%, which no iteration has tested and
which this result points at. That is iteration 27, and it needs its own census, not a
narrative extension of this one.

## CORRECTION — the surplus is a symptom of WINNING, and chips are the compounding currency

I wrote, an hour ago and in a committed message, that the $36,830 chip surplus was "a
consequence of losing" and that the free test I never ran was *"would the surplus still be
there in a game I was winning?"*

**I then ran it, and it demolished my correction as thoroughly as it demolished the original
premise.** The test cost one replay dump. The games were already on disk: `gauntlet.sh`
returns the candidate's *losses*, and a loss for `alice_i26b` is a game `alice_iter25`
**won**, so every local replay from the iteration 26 census contains my baseline winning.

`Barcode`, side A, the winner being `alice_iter25` (T2):

| round | i26b (lost) | **iter25 (WON)** |
|---|---|---|
| 1200 | $2,310 · 7 towers · cov 345 | $23,740 · 15 towers · cov 633 |
| 1600 | $1,460 · 7 towers · cov 327 | **$88,940** · 15 towers · cov 650 |
| 2000 | $1,510 · 7 towers · cov 340 | **$154,040** · 15 towers · cov 638 |

**The winner ends with $154,040 unspent — four times the surplus I built an entire iteration
to eliminate — and the loser ends with $1,510.** A large chip pile is not the signature of
waste and not the signature of losing. It is what winning looks like.

### What is actually true, from RULES.md rather than from a story

`assertCanCompleteTowerPattern` gates on **`getMoney() >= 1000`**. Upgrades cost **2,500 /
5,000 chips**. A spawn costs **250 chips + 200 paint**. So:

> **Chips COMPOUND and paint does not.** Chips buy towers; towers produce both chips *and*
> paint; so a chip spent early returns more chips *and* more paint forever. Paint is purely
> consumptive — it pays for spawns and for painting tiles, and buys nothing that produces.

That single asymmetry explains every column in the census diagnostic without any appeal to
who was winning:

- **Tower count is the discriminator**, and it is the one thing consistent across every game
  I traced: 4 vs 8, 5 vs 8, 7 vs 15. Cutting money towers to 25% cut the compounding rate,
  and the gap widens monotonically with round number because that is what compounding does.
- **Cash *stocks* were similar early** ($1,200 vs $1,070 at r200 on Barcode; $1,300 vs
  $1,270 on Brat) — which is exactly why a stock reading misled me. The candidate was not
  visibly poor. It was *earning* less and therefore *building* less, and a stock cannot show
  a rate.
- **The paint pile is the residue**, not the cause: paint accumulates in towers because
  paint cannot be reinvested into anything that produces.
- **The late-game surplus is the end state of a won compounding race.** Once every ruin is
  taken there is nothing left to buy, so the winner's chips pile up. The pile appears
  *because* the compounding finished, not because it was never needed.

### The methodological failure, which is the part worth keeping

I was told, in this session's own briefing, to *run the discriminating case before naming
the fault*. I named two faults in a row from plausible stories:

1. "chips are surplus, so move slots to paint" — refuted by the census, −21 swept.
2. "the surplus was a symptom of losing" — refuted by a replay I already had, in the
   opposite direction, and committed to git before I checked.

Both stories were coherent, both explained the data I had looked at, and **both were
available to be falsified by an artefact already on disk.** The second is worse than the
first: the first was a hypothesis I paid a census to test, which is the loop working; the
second was an explanation I asserted in a commit message *while writing the sentence that
named the test I had not run*.

`LEARNINGS.md` already says "a retraction is a claim too, and shares the assumption that
produced the error". It does. My retraction shared the original's assumption — that the
surplus needed a *behavioural* explanation at all — when the answer was an accounting
property of the two currencies that RULES.md had recorded from the start.

**Operational rule, added to the ledger: when the explanation of a result is a claim about a
resource, check the resource's own production identity in `RULES.md` BEFORE reaching for a
story about the bots.** One grep would have beaten two narratives.

## REJECT iteration 27 — and the tower-mix knob is now SETTLED, with a three-point curve

| money share | build | census vs `alice_iter25` | SW / SL | net swept |
|---|---|---|---|---|
| 25% (`& 3 == 0`) | `alice_i26b` | 54/150 = **36.0%** | 8 / 29 | **−21** |
| 50% (`& 1 == 0`) | `alice_iter25` | — (baseline) | — | 0 by definition |
| **75% (`& 3 != 0`)** | `alice_i27` | **73/150 = 48.7%** | 16 / 18 | **−2** |

Gate is net swept > 0. **−2. Reject.** `src/alice` stays at `alice_iter25`. 0 exceptions,
margin identity OK.

Three points, each a full 75-map census, so no point on this curve is a sample. Doctrine
rule 2 asks for a dose-response with a zero arm and says a curve that peaks in the middle is
stronger evidence than any single point. **This one peaks in the middle**, and the knob is
closed: there is no ratio left worth a run. `& 7` was already dead; `& 3 != 0` is now dead
in the other direction.

### But the curve is not a symmetric peak — it is a PLATEAU and a CLIFF, and that is the finding

−2 on 34 decisive maps is a coin flip; −21 on 37 is not. So the shape is:

```
 money share   25% ................ 50% ......... 75%
 net swept     -21                    0             -2
               |<--- CLIFF --->|<---- PLATEAU ---->|
```

**Halving my money towers costs 21 swept maps. Halving my paint towers costs approximately
nothing.** The bot is nearly insensitive to losing a quarter of its paint production and
catastrophically sensitive to losing a quarter of its chip production.

That is the compounding asymmetry showing up as a *measured slope* rather than as an
argument from `RULES.md`: chips buy towers and towers produce both currencies, so cutting
the compounding currency compounds the damage, while cutting the purely consumptive one is
absorbed. **This is the corroboration doctrine rule 13 asks for, and it is genuinely a
second place** — the RULES.md production identity and this slope are independent of each
other in a way that swept maps and the head-to-head margin were not.

### What I am NOT going to conclude from the plateau

The tempting reading is "a quarter of my tower slots contribute nothing, so paint towers are
near-worthless at the margin". I have just spent an evening on exactly that class of
inference and been wrong twice, so: the plateau says the *optimum is flat between 50% and
75%*, which is what a balance point looks like from one side. At 75% money the binding
constraint has presumably moved back onto paint — that is why the curve stops rising rather
than continuing — and pushing further would fall off the other side. A flat top is evidence
of a balance, not of a useless input.

**The knob is settled at 50/50 and iteration 28 must look somewhere else.**

## Iteration 28 — the coverage stall, and the unit I have never once built

### How I got here, including the lever I killed on the way

With the tower-mix knob settled I went looking for the next lever and nearly picked the
wrong one twice more. Both were killed by checking an artefact instead of telling a story,
which is the discipline the retraction above cost me.

**Killed lever 1 — "upgrade more towers with the idle chips".** Upgrades cost 2,500/5,000
chips and the winner had $154,040 doing nothing, so this looked obvious. The replay says the
winner had **all 15 of its towers at level 3 by round 1055** and never upgraded again. There
was nothing left to buy. Refuted in one dump, before a line of code.

**Killed lever 2 — my own rediscovery.** I had already investigated and *parked* the
splasher direction, with the exact next step written down. Checking the log before building
saved me from re-deriving it — and told me what had changed since: the parked reason was
"chips are needed elsewhere", and I now know chips are worthless after roughly round 1000.

### The stall, which is the actual defect

`Barcode`, the **winning** side, sampled every 250 rounds:

| round | 1 | 250 | 500 | 750 | 1000 | 1250 | 1500 | 1750 | 2000 |
|---|---|---|---|---|---|---|---|---|---|
| coverage | 163 | 586 | 630 | 611 | 621 | 621 | 638 | 616 | **638** |
| chips | $2,030 | $1,340 | $2,700 | $2,370 | $2,310 | $32,140 | $71,840 | $113,040 | **$154,040** |
| splashers | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **0** |

**Coverage is flat from round 500 to round 2000** — 1,500 rounds, three quarters of the
game, oscillating 611-638 with no trend — while chips rise 57-fold. The bot finishes its
expansion by r500 and then accomplishes nothing for the rest of the game, and it cannot buy
its way out.

`RULES.md` says why, and it is structural rather than a tuning matter:

- a soldier **"cannot overwrite enemy paint"**;
- a mopper only clears a tile to EMPTY;
- **only a splasher takes enemy-painted ground** (overwritten within r^2 <= 2 of the centre).

Once the map is carved up, every tile I do not hold is enemy paint, and **I field nothing
that can take it.** `spl0` on every sampled round of every game I have traced, across 25
accepted iterations.

### The probe, run BEFORE the candidate, because three of my mechanisms have died unfired

`alice_splashprobe` = iteration 25 with the spend gate relaxed and telemetry. This is
verbatim the next step the iteration-24 tower census parked, and the reachability check that
the tower census itself demanded: it measured the *policy-permitted* splasher rate at
**0.15-0.25% of tower-turns**, so an unrelaxed gate would field almost none and measure
nothing.

| map | outcome | splashers built | probe coverage | baseline coverage |
|---|---|---|---|---|
| AlarmClock | probe won r1229 | **0** | — | — |
| Castle | probe won r1385 | **0** | — | — |
| Circuit | probe lost r2000 | **0** | — | — |
| **DefaultHuge** | **probe won r1757** | **30 by r1000, 48 by r1500** | 438 → 556 → **688** | 538 → 413 → **282** |

Two things in that table matter more than the win/loss column.

**First, the mechanism is inert where it cannot help.** On three of four maps the gate never
fired at all, so the build is byte-for-byte iteration 25 there — those three results carry
no information about the mechanism and I am not counting them as evidence for it. The wins
on AlarmClock and Castle are side-B effects of a bot that did not differ.

**Second, where it did fire the two coverage curves cross.** The probe climbs 438 → 688
while the baseline *collapses* 538 → 282. That is the stall being broken in the only way
the rules permit.

### Pre-registered, before the census returns

- **Instrument**: `alice_i28` vs `alice_iter25`, all 75 maps, both sides, 150 games.
- **Gate**: net swept maps > 0, `SW`/`SL` separately, 0 exceptions, 0 overruns.
- **Map-level prediction, which is the part that can falsify the *reason* even if the gate
  passes** (doctrine rule 4 asks for exactly this): gains must be **concentrated on maps
  whose games run long enough to accumulate a surplus**, and **absent on maps that end
  early**, where the gate cannot fire. If the census comes out positive but the wins are
  spread evenly across short and long games, the mechanism is not what won and I must find
  out what did before accepting.
- **Named risk**: a splasher costs **300 paint** against a soldier's 200, and paint is the
  scarce currency — iteration 5's ledger entry records tower paint draining to an absorbing
  state at 0, from which only 100-paint moppers are affordable and paint income never
  recovers. The gate is chip-conditioned, not paint-conditioned, so it does **not** protect
  against that. **Diagnostic if the census fails: tower paint and soldier count in the
  fired regime** — if soldiers collapse where splashers appear, the dose is displacing the
  unit that does the painting, and the fix is a paint-side condition rather than abandoning
  the mechanism.
- **Dose discipline**: this converts *every* spawn to a splasher above the threshold. That
  is one step and a large one. If it wins, the next question is a mix rather than a switch;
  if it loses on the paint-displacement diagnostic, the next question is the same mechanism
  with iteration 5's paint guard attached. Both are separate iterations with their own
  censuses.

## ACCEPT iteration 28 — 79.3%, 44 swept wins and ZERO swept losses over the whole map pool

| | maps | SW | SL | split | record | net swept |
|---|---|---|---|---|---|---|
| `alice_i28` vs `alice_iter25`, census | 75 | **44** | **0** | 31 | **119/150 (79.3%)** | **+44** |

0 exceptions, 0 overruns, margin identity OK. **Not one swept loss on any of the 75 maps.**
This is by a wide margin the largest result this lineage has produced: for comparison, the
accepted iteration 25 was +11 and the rejected iteration 26 was −21.

Snapshotted `src/alice_iter28`, promoted into `src/alice`.

### My pre-registered falsifier said reject, and it was MIS-SPECIFIED. Here is the whole argument.

I wrote, before the run: *"If the census comes out positive but the wins are spread evenly
across short and long games, the mechanism is not what won and I must find out what did
before accepting."* The regime split, with maps classified from the **iteration 27** census
(a run not involving `alice_i28`, so the classifier is independent of what it judges):

| regime | maps | SW | SL | split | net swept | per map |
|---|---|---|---|---|---|---|
| LONG | 49 | 29 | 0 | 20 | +29 | 0.59 |
| MIXED | 16 | 10 | 0 | 6 | +10 | 0.63 |
| SHORT | 10 | 5 | 0 | 5 | +5 | 0.50 |

**Essentially uniform.** By the letter of my own pre-registration that is a reject. I am
accepting anyway, and the reason is not that I dislike the answer — it is that **the
falsifier's inference is logically impossible**, and I can show it.

`alice_i28` differs from `alice_iter25` by **exactly one executable line**, verified by
diffing both files with comments stripped:

```java
if (rc.getMoney() >= CHIP_RESERVE + 5000) want = UnitType.SPLASHER;
```

There is no second mechanism for "what else won" to be. And that one-line diff has a
consequence that turns out to be a far better test than the one I designed:

> **On any map where the gate never fires, the two bots are byte-identical.** The engine is
> deterministic (verified 12/12 earlier tonight), so the A-side and B-side games are the
> same game with the labels swapped, and the map **must split**. A map where the gate never
> fires *cannot* be a swept win or a swept loss.

So the sweep structure reads the firing directly, with no classifier at all:

- **44 swept wins ⇒ the gate fired, and decided the map, on at least 44 of 75 maps.**
- **0 swept losses ⇒ across the entire pool it never once cost a map.**
- **31 splits** are exactly the maps where it did not fire (or fired without mattering).

Verified on the ground rather than left as an argument: on the short maps `memstore` and
`rain` the census replays show `spl0` throughout and chips flat at $1,200-$1,420 — the gate
never fires, and those maps split, as it says they must.

**Why my classifier failed** is worth recording, because the mistake is reusable. I
classified maps LONG/SHORT by whether the *iteration 27* games reached round 2000. But
iteration 28 **ends games earlier** — it wins by painting enough of the map instead of
grinding to a tiebreak. So "long under iteration 27" does not predict "accumulates a surplus
under iteration 28": I built a regime classifier out of a property of a *different matchup*
and then treated it as a property of the map. Doctrine rule 5's wrong-referent error, third
appearance today, and the first time I have caught it before it changed a verdict.

**The honest statement is that I pre-registered a bad falsifier**, not that I overrode a good
one. A pre-registration earns its authority by being a test the mechanism could actually
fail; mine tested a proxy that does not track the thing it stands for. The replacement is
strictly better and was available the whole time — it is entailed by the diff, needs no
classifier, and I will use the split/sweep structure for every regime-dependent mechanism
from here on.

### The named risk did not materialise, and the gate is why

The pre-registered risk was paint displacement: a splasher costs **300 paint** to a
soldier's 200, and iteration 5's ledger entry records tower paint draining to an absorbing
state at zero. **SL = 0 across 75 maps** is about as strong a refutation as that risk can
get — a mechanism that starved its own painters would lose maps, and it lost none.

The structural reason is that the gate is conditioned on a **runaway chip surplus**, which
only exists once expansion has finished. By then the tower is not competing with anything:
it has more chips than the game has things to buy, and the paint it spends is paint that was
accumulating unspent anyway. That is the same "consume only what was going spare" shape as
iteration 25's refill and iteration 24's unused-action rule — the third accepted mechanism
in this lineage built on it, and the largest.

## Iteration 29, pre-registered — the splasher gate's REACH, and the trap it has to avoid

Iteration 28's split/sweep structure says exactly where the headroom is: **31 of 75 maps
split, which under a one-line diff means the gate never fired there and those maps got
iteration 25 unchanged.** The mechanism went 44-0 on the maps it reached. It is not obvious
that anything is wrong with it — the obvious question is whether it can reach further.

**Hypothesis**: lower the threshold from `CHIP_RESERVE + 5000` to `CHIP_RESERVE + 2500`
(a level-2 tower upgrade rather than a level-3 one — still an engine constant, still not
searched), so the gate fires earlier and on more maps.

### The named risk is iteration 26 wearing a different hat, and I want it on the record first

A splasher costs **400 chips**. Chips are the compounding currency: `completeTowerPattern`
gates on `getMoney() >= 1000`, so **chips spent on splashers are chips not spent on towers**,
and iteration 26 measured what happens when tower construction is starved — **−21 net swept,
the worst result this lineage has recorded.**

Iteration 28 is safe from that only because its threshold sits *above the expansion phase*:
by the time a tower holds 5,000 chips beyond the reserve there is nothing left to build.
**Lowering the threshold walks toward the cliff on purpose**, and the entire question is
whether 2,500 is still past the end of expansion or already inside it.

So this is a dose-response step, and the zero arm and the +1 arm are both already measured:

| threshold | build | census |
|---|---|---|
| never fires | `alice_iter25` | zero arm |
| `+5000` | `alice_iter28` | **119/150, +44 swept** |
| **`+2500`** | `alice_i29` | pre-registered below |

### Pre-registered

- **Instrument**: `alice_i29` vs **`alice_iter28`** (the new baseline), full 75-map census.
- **Gate**: net swept > 0, `SW`/`SL` separately, 0 exceptions, 0 overruns.
- **Reach check, replacing the classifier I got wrong**: report the **split count**. Under
  the same one-line-diff logic, a lower threshold that genuinely reaches further must
  produce **fewer splits than iteration 28's 31**. If the split count does not fall, the
  dose did not change the reach and any margin is something else — that is the properly
  specified version of the regime prediction I mis-built last time, and it is a property of
  the mechanism rather than a proxy for it.
- **Failure diagnostic, named in advance**: if it loses, check **tower count at r200-400**
  against the baseline. A fall there is iteration 26's chip-starvation cliff reached from
  the other side, and it means the threshold must stay above expansion — in which case the
  reach ceiling is structural and the remaining 31 maps are simply not addressable by this
  knob.
- **If it loses on that diagnostic, the next question is NOT a smaller step.** It is
  whether the gate should key on *expansion being finished* (no completable ruin in
  sight) rather than on a chip level that only correlates with it. That is a different
  mechanism and a separate iteration.

### A second, independent thing iteration 28 unlocked, noted so it is not lost

`MIN_SPLASH_TILES = 6` gates every splasher attack, and it was written when **splashers were
never built**, so it has never once been evaluated on a live unit — the repair that
introduced it was explicitly accepted as *inert*. It is now the single most-exercised
untested constant in the bot. `alice_splashprobe` already carries the telemetry to measure
`splashScore` at the centres a splasher actually chooses (the quantity the iteration-24
census parked as unmeasurable), and reading it needs a replay dump, not a census.

## Roster run after iteration 28 — and the roster is SATURATED, exactly as warned

Full frozen roster, `alice_iter28`, 350 games. Reporting the **weakest rung**, not the mean,
because a mean over saturated rungs describes the ceiling rather than the bot:

| rung | record | win% | swept W/L | previous |
|---|---|---|---|---|
| `alice_iter0` | 50-0 | **100.0%** | 25 / 0 | 100% |
| `alice_iter1` | 50-0 | **100.0%** | 25 / 0 | 100% |
| `alice_iter4` | 50-0 | **100.0%** | 25 / 0 | 98% |
| `alice_flood` | 49-1 | 98.0% | 24 / 0 | 88-92% |
| `alice_iter7` | 48-2 | 96.0% | 23 / 0 | 88-98% |
| `alice_iter12` | 48-2 | 96.0% | 23 / 0 | 96% |
| **`alice_iter23` (weakest)** | **40-10** | **80.0%** | 16 / 1 | **66%** |

**Weakest rung: 80.0%.** Every rung is now at or above 80%, and three are at *exactly*
50-0 — a rung that has lost every game of 50 cannot register an improvement **or a
decline**, so it contributes literally zero information about the next iteration.

Iteration 28 did this in one step: it moved `alice_iter23` from 66% to 80% and `alice_flood`
from ~90% to 98%. **A result that sweeps almost everything is precisely the result that
saturates a roster fastest**, which makes the danger worst at the moment it is least
visible — a chain of thin accepts walking downhill is undetectable when every line is
pinned at the top.

I am **not** retiring any rung. A retired rung destroys the long-run trend that is the whole
value of the chart, and the saturation is a statement about the *set*, not about any member.
The fix is a harder fixed reference.

## `alice_paintthief` — a harder rung, aimed at the blind spot this session exposed

The self-referential blind spot is not abstract for me; I can name my instance of it exactly:

> For **25 accepted iterations this bot could not take enemy-painted ground at all** — a
> soldier cannot overwrite enemy paint, a mopper only clears to EMPTY — **and no opponent
> in my pool ever did it to me either, because every one of them is me.** Iteration 28
> finally fields splashers, but only above a runaway chip surplus: it fired on 44 of 75
> maps and never fired on the other 31.

So "what happens when the opponent takes *my* paint, early and constantly" is a question
none of my instruments can currently ask. That is the archetype's job, and it is the reason
it qualifies as a rung rather than as a bot I happen to have written.

Two changes from `alice_iter28`, both making it aggressive in the dimension I am blind to:

- **splashers whenever affordable**, not only out of surplus — the gate iteration 28 keeps
  is removed, so it contests ground from the early game;
- **`MIN_SPLASH_TILES` 6 → 2**, so it attacks on almost any conversion rather than only a
  profitable one.

It is **frozen on commit and never edited**, for the same reason an old snapshot is: a rung
that changes cannot carry a trend. Calibration run in flight — a rung is only worth adding
if it is not *also* at ceiling, and I will report where it lands before adding it to
`progress/roster_extra.txt` rather than assuming the design made it hard.

### Calibration verdict: `alice_paintthief` is ADMITTED — 74.0%, the hardest rung I have

`alice_iter28` vs `alice_paintthief`, 25 sampled maps, 50 games, run `20260908-080826`,
0 exceptions across all 50:

| | record | win% | swept W | swept L | split |
|---|---|---|---|---|---|
| `alice_iter28` vs `alice_paintthief` | **37/50** | **74.0%** | 14 | **2** | 9 |

**74.0% against the current accepted snapshot, versus 80% for the weakest existing rung.**
It is not at ceiling, so it carries information the saturated rungs cannot. Admitted to
`progress/roster_extra.txt` and **frozen** — the source is committed and will never be
edited again, for exactly the reason a snapshot is never edited.

It is also the **first rung in the history of this roster to take a swept map off the
accepted bot** — 2 of them. Every previous rung's losses were split-by-side, i.e. spawn
advantage; these are not.

#### And the two swept losses land somewhere very specific

The maps `alice_paintthief` swept are **`Barcode`** (r229 / r500) and **`memstore`**
(r555 / r577) — all four games decided early, none near the round-2000 tiebreak.

Cross-referencing the iteration 28 census (run `20260908-061818`), both maps are **splits**:

```
RESULT alice_iter25 Barcode  A B 2000   RESULT alice_iter25 Barcode  B B 1059
RESULT alice_iter25 memstore A B  479   RESULT alice_iter25 memstore B B  479
```

Under the one-line-diff logic of iteration 28, **a split is a map where the splasher gate
never fired** — `memstore` is one of the two maps I verified on the ground (`spl0`
throughout, chips flat at $1,200-1,420). So **both of the archetype's swept wins sit inside
the 31-map set where iteration 28 reverts to iteration 25 behaviour.**

I want to be honest about the strength of this: **n=2**. Two maps is a direction, not a
result, and I am recording it as a hypothesis rather than a finding. But it is a direction
that points the same way as iteration 29's premise, and it was produced by an instrument
built for an entirely different purpose, which is the only kind of corroboration worth
much. The 31 non-firing maps are not merely *unimproved* — on the evidence available they
are where a paint-denial opponent actually beats me, and they were invisible for 25
iterations because every opponent I had was myself.

If iteration 29 reduces the split count, this rung is the instrument that should register
it, and it is the only one on the roster with the headroom to do so.

## Tournament `20260908-0100` — and a PRE-REGISTERED prediction for the next one

Standings: bob 70.3%, **alice 47.3% (+9.3)**, carol 32.3%. Head-to-head:
`alice vs bob` **26.0% (+18.7)**, `alice vs carol` 68.7% (0.0).

Sweep structure, which is the part that is not just the margin restated:

| pair | alice swept | opponent swept | split |
|---|---|---|---|
| alice–bob | 8 | **44** | 23 |
| alice–carol | 39 | 11 | 25 |

**What played was `alice @ 25c3160`** — "repair the splasher dead branch (inert)". That
commit is *before* iteration 28. So the largest result this lineage has produced has **never
been measured against an opponent it did not write**, and the 47.3% above does not contain
it. The 13:00 UTC run is the first that will.

### Pre-registering the prediction now, before the run, because otherwise it is worthless

I am about to see a tournament number and I already have a story ready for it, which is
exactly the condition under which a post-hoc reading is useless. So, on the record:

- **What iteration 28 does** is field splashers on a runaway chip surplus. A splasher is the
  only unit I have that takes enemy-painted ground. Against bob, 44 of 75 maps are swept
  *against* me — decisive losses, not coin-flips.
- **Prediction**: `alice vs bob` improves, and it improves specifically by **converting
  bob's swept maps into splits rather than by winning splits** — because taking contested
  ground turns a decisive loss into a fight, and that shows up as bob-swept falling faster
  than alice-swept rises.
- **Falsifier**: if `alice vs bob` moves up while bob's sweep count stays near 44, then the
  gain came from the split maps and iteration 28's mechanism is not what produced it.
- **Null result I will accept**: no movement at all. Iteration 28's gate needs a *runaway
  chip surplus*, and a game against a strong opponent may simply never reach one — the
  mechanism can be worth +44 in self-play and inert against bob without any contradiction.
  If that is what I see, it is evidence that my whole instrument (self-play census) selects
  for mechanisms that only fire in games I am already winning, which would be the most
  important thing I have learned this session and would redirect the next several
  iterations.

Recording all three branches in advance so that whichever lands, I cannot claim I expected it.

## `alice_splashprobe2` — measuring `MIN_SPLASH_TILES` properly, and why the first probe cannot

`MIN_SPLASH_TILES = 6` now gates every splasher attack in the accepted bot. It was written
when splashers were never built, and the commit that introduced it was accepted **as
explicitly inert**. It has never been evaluated on a live unit, and iteration 28 made it the
most-exercised untested constant I have.

**`alice_splashprobe` cannot measure it, and the reason is structural rather than a bug.**
Its histogram `spHist` records `splashScore` at the centre the splasher *chose* — and the
choice is made by `int bestScore = MIN_SPLASH_TILES;`, so **every sample in that histogram
has already passed the threshold**. A distribution conditioned on passing a test says
nothing about the test. This is the wrong-referent error again (doctrine rule 5), and I only
caught it by reading the selection line rather than the histogram's label.

The quantity that actually reads the dose is the best score **available** on a ready turn,
unfiltered. Then:

- `P(best available in 1..6)` is exactly the fraction of attacks the constant suppresses;
- the shape of that lower tail says what a smaller threshold would buy;
- `P(best available = 0)` separates "the threshold blocks me" from "there was nothing there
  anyway", which are opposite conclusions that the current probe reports identically.

`alice_splashprobe2` is `alice_iter28` plus that counter. It is **behaviourally identical**:
`bestAny` is computed inside the loop that was already scoring every centre, it feeds no
decision, and the attack still fires on exactly the same centre. Verified by diffing against
`alice_iter28` with comments stripped — every hunk is a counter, a histogram, or the
indicator string.

One engine detail, checked rather than assumed: `GameConstants.INDICATOR_STRING_MAX_LENGTH`
is **256** (javap'd on the engine jar). A 19-bucket histogram plus the standard `i25`/`bc`
tail overflows that, so a splasher emits the probe string alone and the string is truncated
defensively at 255.

### Pre-registered reading, written before the run

- **Instrument**: `alice_splashprobe2` vs `alice_iter28`, replay dump of the splasher
  indicator strings on maps where the gate is known to fire.
- **If `P(best available in 1..6)` is small** (say < 15% of ready turns), the threshold is
  nearly inert, lowering it is not a dose knob at all, and **iteration 30 must go elsewhere**
  — I will not spend an iteration on a constant that gates nothing.
- **If it is large**, the threshold is suppressing real attacks and the tail shape picks the
  dose — that becomes a one-constant iteration with the same structure as iteration 29.
- **Deliberately not launched yet**: the iteration 29 census holds all three job slots, and
  `MULTI_AGENT.md` caps MAXJOBS at 3 across a VM shared with two siblings and a live BC26
  project. Queued behind it, not run alongside it.

## Tournament forensics: **my deficit against bob is the MID-GAME**, and it is very sharp

Non-blocking work while the iteration 29 census runs. No VM time, no new games — this is
re-reading `tournaments/20260908-0100/results.csv`, which is the only measurement I have
against an opponent my lineage did not write.

### First, the thing I tried that did not work — and it was my own repeated error

I cross-tabulated the iteration 28 census's **split set** (the 31 maps where the one-line
diff means the splasher gate never fired) against the maps bob sweeps:

| | bob-swept | split | alice-swept | total |
|---|---|---|---|---|
| gate NEVER fires (census split) | 19 (61%) | 9 | 3 | 31 |
| gate FIRES (census swept-win) | 25 (57%) | 14 | 5 | 44 |

**Flat** — and 61% / 57% both sit on the base rate of 44/75 = 59%. But I am not reporting
this as "no relationship", because **the test is invalid**, for the third time today in the
same way: *whether the gate fires is a property of the MATCHUP, not of the map.* The gate
needs a runaway chip surplus. That surplus arises against `alice_iter25`; there is no reason
whatever to assume it arises against bob on the same map. I classified maps by a property
measured in a different matchup and applied it to this one — **exactly** the error that broke
my iteration 28 regime classifier, which I had written up hours earlier and then walked
straight back into.

**This also forces me to retract the strength I gave the `alice_paintthief` observation
above.** I noted both of its swept wins fell in the non-firing set and called it "a
direction". The direction rests on the same invalid transfer, and n=2 besides. It is
withdrawn — not contradicted, just unsupported.

### The statistic that IS valid, because it conditions on nothing that picks a winner

Instead of classifying maps, bucket all 150 alice–bob games by **the round the game was
decided in**, and ask who won each bucket. Nothing here is conditioned on the winner:

| decided in | games | bob won | alice won | **bob share** |
|---|---|---|---|---|
| r < 500 | 25 | 13 | 12 | **52%** |
| r500–799 | 32 | 26 | 6 | **81%** |
| r800–1199 | 29 | 27 | 2 | **93%** |
| r1200–1998 | 22 | 20 | 2 | **91%** |
| r2000 tiebreak | 42 | 25 | 17 | **60%** |
| **all** | **150** | **111** | **39** | **74%** |

**I am level with bob in the opening (52%) and nearly level at the tiebreak (60%). I lose
88% of everything decided in between** — 73 of 83 games in r500–1998.

The obvious objection is selection: game length is itself an outcome, so maybe bob just
paints faster and every decisive game skews to him. **The data refutes that model**, and this
is the part worth keeping. If bob were uniformly faster, his edge would be *largest* in the
fastest games. It is smallest there — 52%, a coin flip. The edge appears only once the
opening is over, and it collapses again if nobody converts by r2000. That shape is not
"faster"; it is a conversion engine operating in a phase where I have none.

### What this does to my agenda

It supports iteration 29's direction from a completely independent instrument, which I did
not expect and had not designed for:

> Iteration 28's gate needs `CHIP_RESERVE + 5000`. Whatever round that arrives on, it is
> **late** — it is defined as the point where expansion has finished and there is nothing
> left to buy. My deficit is r500–1200. **A mechanism that switches on after the phase I
> lose in cannot address the phase I lose in.** Lowering the threshold moves it earlier.
> That is iteration 29, pre-registered before I knew any of this.

It also names the measurement I should have made first and had not: **the round at which
the gate first fires**. I have never recorded it. `alice_splashprobe2` should carry it, and
until I have it, "iteration 29 fires earlier" is an assumption about a constant rather than
an observation. Adding it before that probe runs.

## Replay forensics on the tournament games — and I have been optimising the wrong resource

Still non-blocking; no new games. Aggregate dumps (`--every 50`, aggregates only, no action
log) of three maps bob sweeps in the mid-game band: `UnderTheSea`, `TheBest`, `DefaultMedium`.
T1 = alice, T2 = bob.

```
UnderTheSea      ALICE                          BOB
  round     cov  tw  spl sold   $$$$      cov  tw  spl sold
    200     325   7    0    5   1320      339   7    2   14
    300     363  10    0    9   1330      465  11    5   23
    400     395  12    0   13   1030      576  13   10   40
    500     348  10    0   21   1270      636  16   11   53
    650     281   8    0   11   1270      679  16   20   66
```

Three things, all three consistent across all three maps.

1. **My coverage PEAKS and then FALLS.** 401 -> 281 on UnderTheSea, 391 -> 288 on
   DefaultMedium, 237 -> 218 on TheBest. Bob's rises monotonically throughout. I am not
   failing to gain ground; **I am losing ground I already painted.**
2. **Bob fields splashers from ~r200 on every map**, growing to 20-51. I field `spl0`
   forever. A splasher is the only unit that overwrites enemy paint, which is exactly what
   a falling coverage curve means is happening to me.
3. **I am not short of chips.** My money sits at $1,000-$3,700 idle while my soldier count
   stalls at 10-23 and bob's reaches 157. Chips are not the binding resource. They have not
   been since iteration 2, and I keep building mechanisms that spend them.

### The finding that actually matters, and it is about a mechanism I ALREADY ACCEPTED

The dump has a `xfer` column (`TransferAction` count) and a `starved` column (died with
paint <= 0). I checked both against `tools/replaydump/ReplayDump.java` rather than trusting
the labels — `starved[dt]++` fires on `DieAction` when `lastPaint <= 0`, and `xfers[tid]++`
on `TransferAction`. They compute what they say.

Summed over the **whole** UnderTheSea game, not sampled windows:

```
alice: transfers=    0   deaths= 116   starved=  83 (72%)
bob:   transfers=   62   deaths= 152   starved= 115 (76%)
```

**Zero.** Across an entire 660-round game, `alice_iter25`'s paint refill — an accepted
iteration, +11 net swept, the mechanism whose "consume only what was going spare" shape I
have twice cited as this lineage's best idea — **calls `transferPaint` not once.**

Reading the code rather than guessing why:

```java
if (p * 2 >= cap) return;               // only below half paint
if (!rc.isActionReady()) return;        // never displace an action
RobotInfo[] near = rc.senseNearbyRobots(2, rc.getTeam());   // distance^2 <= 2: ADJACENT
```

`runSoldier` spends the action painting on essentially every turn it has paint. So the
refill can only fire on a turn where the soldier did *not* act — and it must **also** be
standing next to a tower at that moment, with that tower holding 200 spare paint. A soldier
that has wandered off to paint and run dry is nowhere near a tower. The three conditions
are jointly almost unsatisfiable in a real game.

**I do not yet know whether this is also true in self-play, and that is the whole question.**
Two possibilities with completely different consequences:

- **Inert everywhere** — then iteration 25's +11 net swept was produced by something other
  than the mechanism I credited, and an accepted iteration in my ledger is mis-attributed.
- **Fires in self-play, not against bob** — then it is regime-dependent, and my census
  selects for mechanisms that only work against opponents that behave like me.

The second is the null branch I pre-registered this morning for iteration 28, arriving early
and attached to a different mechanism. Either way it is an indictment of the instrument, not
of the idea. **The iteration 29 census now running writes replays; I will count transfers in
one of its self-play games and settle it there, at no extra VM cost.**

I am deliberately not drawing the "starvation is my unique weakness" conclusion that the
numbers invite: bob starves at 76% of deaths and I starve at 72%, so starvation per se is
not what separates us. What separates us is that bob has 62 transfers and I have none.

## ACCEPT iteration 29 — 56.0%, +9 net swept, and the dose-response curve has BENT

`alice_i29` vs `alice_iter28`, full 75-map census, run `20260908-091551`.

| | maps | SW | SL | split | record | net swept |
|---|---|---|---|---|---|---|
| `alice_i29` vs `alice_iter28` | 75 | **12** | **3** | 60 | **84/150 (56.0%)** | **+9** |

**0 exceptions in 150 games** (checked on field 5 of the `EXC` lines — my first pass read
field 4, which is the side letter, and reported 150 non-zero; the correct count is 0). No
overruns anywhere in the run. Margin identity holds exactly: wins − losses = 84 − 66 = 18 =
2 × (12 − 3).

The pre-registered gate was **net swept > 0, SW/SL separately, 0 exceptions, 0 overruns**.
All four hold. There is no sampling error to argue about: this is the entire 75-map
population, and the engine is deterministic, so **+9 is exact rather than an estimate**.

Snapshotted `src/alice_iter29`, promoted into `src/alice`, compile-checked against the
engine jar (`EXIT=0`) because HEAD is what plays in the tournament.

### The manipulation check — run BECAUSE I expected to pass it, and it caught something

The coordinator's rule, adopted: *a check you run only when you fear the answer is not a
check.* So I ran one on a result I liked.

**The check.** `+2500 < +5000`, so any map where the lower gate never fires is necessarily a
map where the higher gate never fires. My test for "never fired" has been *equal round counts
on both sides* — under determinism, identical bots play the same game with the labels
swapped. So the never-fired set of this census **must be a subset** of the never-fired set of
the iteration 28 census.

**Raw, it fails outright: 23 ⊄ 16.** More maps look identical at the *lower* threshold than
at the higher one, which is impossible.

**The contamination**, found by looking rather than by explaining it away: **a game that
reaches the round-2000 tiebreak has round count 2000 on both sides whether or not the two
games were the same game.** Equal round counts are *forced* at the cap. Of the 23, seventeen
are r2000/r2000; of the 16, eight are. Excluding ties:

```
  i29 vs i28:  60 splits, 23 equal-round, 17 forced by the r2000 cap  ->  6 genuine
  i28 vs i25:  31 splits, 16 equal-round,  8 forced by the r2000 cap  ->  8 genuine
  E29 (6) subset of E28 (8)?   YES, violations = []
```

**The check passes once the instrument is corrected — and correcting it retracts an overclaim
I made earlier today.** Hours ago I wrote "of 31 splits, 16 have IDENTICAL round counts both
sides -> byte-identical games". **The right number is 8.** Round-count identity over-counts
by exactly the number of tiebreak games, and I had used it as if it were proof. The
iteration 28 write-up's own hedge ("or fired without mattering") happens to survive this, but
the sharpened version I wrote today did not. That correction was available *only* because I
ran a check on a result nobody was doubting.

### My pre-registered reach check was INAPPLICABLE — the third mis-specification of one kind

I wrote: *"a lower threshold that genuinely reaches further must produce fewer splits than
iteration 28's 31."* Splits came out **60**. But 31 was measured in `alice_i28` vs
`alice_iter25`, and 60 in `alice_i29` vs `alice_iter28` — **different baselines**. The split
count of a pair measures how often *that pair* differs, not how far either member reaches. It
is not that the criterion failed; it cannot be evaluated.

That is the same wrong-referent error as the iteration 28 regime classifier and the map
cross-tab I threw out this morning. **Three times in one day, and this one I wrote into a
pre-registration** — which is worse, because a pre-registration is supposed to be the thing
that protects me. I am not going to claim I have learned it now. The concrete rule instead:
**a pre-registered criterion may only reference quantities measured inside the run it
judges.** 31 came from another run; it should never have been in the gate.

The within-run reach measure that *is* valid: `alice_i29` is behaviourally identical to
`alice_iter28` on **6 of 75 maps** and differs on the other 69. The reach is broad.

### What the number actually says: the yield collapsed and the predicted cliff appeared

| threshold | census | SW | SL | net swept |
|---|---|---|---|---|
| `+5000` (iteration 28) | vs `alice_iter25` | 44 | **0** | **+44** |
| `+2500` (iteration 29) | vs `alice_iter28` | 12 | **3** | **+9** |

Same knob, same direction, one step further: **the yield fell from +44 to +9 and the first
swept losses in this mechanism's history appeared** — `lighthouse`, `yearofthesnake`,
`defensetower`. I named that risk before the run: a splasher costs 400 chips, chips fund
towers, and iteration 26 measured −21 net swept when tower construction was starved. Three
swept losses is that cliff becoming visible. It is an accept, but it is an accept on a
bending curve, and **the next step down is not obviously positive.**

### And the honest strategic note: this knob is second-order

Today's replay forensics say chips are not my binding resource — I sit on $1,000-$3,700 idle
while my army stalls and my coverage *falls*. Iteration 29 spends chips slightly earlier.
That is a real +9 and I am banking it, but **I should stop tuning this constant.** The
measured deficit is paint logistics, and `alice_refillprobe` is built to find out which of
`tryRefill`'s three guards is the one that keeps it at zero transfers.

## Roster: the coordinator's correction, and what I am changing

The coordinator retracted the advice that a saturated roster is fixed with a hand-built
synthetic archetype: its difficulty is set by guesswork about one's own weaknesses, so it
lands at a ceiling or a floor. Two lineages hit both extremes. The remedy is **the newest
accepted snapshot**, which reads ~50% *by construction* rather than by aim.

- **Adding `alice_iter28` to `progress/roster_extra.txt`.** Its calibration is already
  measured, by the census above, at **56.0%** — the closest rung to 50% I have, and it cost
  no VM time because the accept's own census *is* the calibration. Standing rule from here:
  **on every accept, add the snapshot that was current before it.**
- **`alice_paintthief` stays.** I did score it before promoting (74.0%), so it is not the
  failure mode described, and it is the only rung that has ever taken a swept map off my
  accepted bot. Retiring rungs destroys the trend that is the chart's whole point.
- **What the snapshot rung does NOT fix**: it makes the roster harder, not more
  *independent*. `alice_iter28` shares every blind spot I have — it is me, one iteration ago.
  Only the tournament measures me against something my lineage did not write.

## The refill guard probe: it is ADJACENCY, and it kills the fix I was about to write

`alice_refillprobe` (= `alice_iter28` + counters, behaviourally identical; it split all three
maps, as an instrumentation-only build must) vs `alice_iter28`, run `20260908-094830`.
Counters read off the replay indicator strings at r1995-1999.

| map | hungry turns | action FREE | tower ADJACENT | refills done |
|---|---|---|---|---|
| DefaultMedium | 499 | 249 (50%) | **0 (0.0%)** | 0 |
| TheBest | 9,808 | 8,466 (86%) | **95 (1.0%)** | 90 |
| UnderTheSea | 1,708 | 1,585 (93%) | **0 (0.0%)** | 0 |

**The action guard was never the problem.** On 50-93% of hungry turns the soldier's action is
sitting unused — of course it is: a soldier low on paint cannot paint, so it never spends the
action. The guard I suspected is satisfied almost always.

**Adjacency is the binding guard, by two orders of magnitude.** A tower with spare paint is
next to a hungry soldier on 0.0%, 1.0% and 0.0% of the turns where it is needed.

I was one step from writing the wrong iteration. My plan on the evidence available an hour
ago was "move the `tryRefill` call before the role dispatch" — a genuinely one-line change,
easy to justify, and **it would have accomplished exactly nothing**, because it targets the
guard that was already passing. The probe cost six games. That is the cheapest lesson
available today.

It also answers the question I left open this morning with a **third** option I had not
listed. Not "inert everywhere" and not "regime-dependent": the mechanism **fires at about 1%
of the opportunities, in every regime**, because a hungry soldier is essentially never
standing next to a tower. Iteration 25's +11 net swept therefore cannot be mostly the refill
— 90 refills in one game and zero in two others is not what a +11 mechanism looks like.
Logged as a **mis-attributed accept**: the iteration was real, the explanation was not.

## Iteration 30, pre-registered — walk to the tower, and the dose is the open question

**Hypothesis**: a soldier that cannot use its paint should spend its MOVEMENT closing the
distance to a tower, instead of wandering dry until it starves. 72-88% of my deaths in the
tournament games are starvation.

**Why it must pre-empt the role, not follow it.** `wander()` spends the movement on every
turn it is ready. A walk appended after the role would find no movement left and be inert —
*for exactly the reason the refill is inert*. So `goRefill` runs first in `runSoldier` and
returns true to pre-empt. Getting this backwards is the same shape of error as the guard I
just disproved, so it is written down rather than assumed.

**Two arms, because the dose is the whole question and I will not hand-search it.** Neither
arm introduces a new constant:

| arm | diverts when | rationale |
|---|---|---|
| `alice_i30a` | `paint < attackCost` | cannot paint one tile, so the painting given up is **provably zero** |
| `alice_i30b` | `paint * 2 < paintCapacity` | the hunger line **already in `tryRefill`**; diverts a soldier that could still paint |

`i30b` carries iteration 26's risk explicitly: pull painters off the map and coverage falls.
`i30a` carries the opposite risk of being too late to save the unit, since a soldier at
`paint < attackCost` may starve during the walk.

### Pre-registered

- **Instrument**: run `20260908-100124`, `BOT=alice_iter29 OPPONENTS="alice_i30a alice_i30b"`,
  40 maps sampled, 160 games. Baseline as `BOT` so both arms play **the same maps against the
  same baseline** — within-run comparison is then exact.
- **DIRECTION, spelled out because this run is inverted relative to my usual one**: the
  summary reports from `alice_iter29`'s point of view. **An arm is GOOD when `alice_iter29`
  LOSES to it.** The quantity I want is `alice_iter29`'s swept-**loss** count against that
  arm. I have written this down before seeing any number precisely so that a favourable-
  looking headline cannot be read the wrong way round.
- **Dose-finding gate**: the better arm is the one with the higher net swept *against*
  `alice_iter29`. It advances to a full 75-map census against `alice_iter29`, which is the
  accept gate. **This run does not accept anything.**
- **Falsifier for the whole direction**: if *both* arms are at or below zero net swept, the
  mechanism does not pay, and the conclusion is that starvation is a *symptom* of being
  out-expanded rather than a cause — in which case iteration 31 goes to tower siting, not to
  unit logistics.
- **Manipulation check, pre-committed, to be run WHETHER OR NOT I like the result**:
  `i30a` and `i30b` differ only in the predicate, and `i30a`'s condition implies `i30b`'s
  (`paint < attackCost` ⇒ `paint*2 < capacity`, since attackCost << capacity/2). So **every
  map where `i30b` is identical to the baseline must also be one where `i30a` is** —
  the same subset test that caught the r2000 contamination, and I will exclude tiebreak
  games from the identity test this time by construction rather than after the fact.

## Amendment to the tournament pre-registration, recorded BEFORE the 13:00 UTC run

This morning I pre-registered a prediction for the next tournament on the basis that it would
be **the first to contain iteration 28**. Since writing that I have accepted iteration 29 and
promoted it, so HEAD now carries **iteration 28 *and* 29** — the splasher gate plus the
lowered threshold.

The prediction and its falsifier are unchanged, because both iterations are the same
mechanism at two doses. But the test is now of the pair, not of iteration 28 alone, and **I
can no longer attribute a movement to iteration 28 specifically.** Recording the amendment
now rather than explaining it afterwards, which is the only time it counts.

The null branch matters more than before, not less. Iteration 29 halved the chip threshold
and still gates on a surplus; today's forensics say my losses to bob are decided in
r500-1200 and that I sit on idle chips throughout. If the pair moves nothing, that is
evidence my self-play census selects for mechanisms which need an opponent that behaves like
me — and iteration 30's direction (paint logistics, not chip spending) is the response
already in flight.

## The coverage collapse is general, not a three-map artifact

Extended the aggregate dump to seven of bob's swept maps from tournament `20260908-0100`:

| map | alice peak | @round | alice final | drop | bob peak | bob final | bob falls? | bob spl first > 0 |
|---|---|---|---|---|---|---|---|---|
| Circuit | 276 | 400 | 229 | **−47** | 698 | 698 | no | r200 |
| DefaultMedium | 391 | 250 | 292 | **−99** | 683 | 674 | yes | r200 |
| HungerGames | 294 | 450 | 258 | **−36** | 678 | 678 | no | r250 |
| Parking_lot | 274 | 350 | 274 | 0 | 604 | 604 | no | r200 |
| Snowglobe | 337 | 300 | 291 | **−46** | 692 | 692 | no | r200 |
| TheBest | 251 | 450 | 251 | 0 | 685 | 685 | no | r200 |
| UnderTheSea | 401 | 350 | 281 | **−120** | 679 | 679 | no | r200 |

**My coverage ends below its own peak on 5 of 7 maps; bob's does on 1 of 7.** My peak lands
at r250-450 — the front edge of the r500-1200 band where the round-bucket analysis says I
lose 88% of decided games. The two instruments agree, and they were built for different
questions.

**Bob's splasher count first exceeds zero at r200 on six of seven maps and r250 on the
seventh.** Mine is zero on all seven, on every sampled round. My gate needs a runaway chip
surplus; whatever round that arrives on, it is not r200.

The honest caveat on the two zero-drop rows: `final` is the last sample before the game
ended, so a map whose game ends near my peak cannot show a drop. That biases *against*
finding the effect, which makes 5 of 7 a floor rather than a ceiling.

## TOOLING / ISOLATION REPORT — the shared scratchpad leaks between lineages

Reporting rather than working around it, per my charter.

**The session scratchpad is shared by all three agents, exactly as `tasks/` is.** Its path is
keyed to the coordinator's session UUID
(`.../fb8ba202-.../scratchpad`), and my prompt warns explicitly about globbing `tasks/` for
that reason. **The same hazard applies one directory up, and the warning does not mention
it.**

A plain `ls <scratchpad>/*.bc25`, run to find my own replay dumps, returned **9 replay files
belonging to another lineage** among 473 entries. I saw only filenames and **opened none of
them**; I am not naming what the filenames imply beyond confirming they are not mine. Replay
blobs are worse than transcripts in one respect — a `.bc25` is a complete game record, so a
single accidental dump would expose another lineage's unit composition, timings and
build order in full.

This is the same failure the `tasks/*.output` warning was written for, and it has now
occurred in the adjacent directory. My local mitigation is to keep my own files in
`scratchpad/alice-work/` and never glob the scratchpad root — but **a mitigation I apply by
remembering is worth nothing**, because the next session that resumes without reading this
note will glob the root exactly as I did. The fix belongs in the tooling: a per-agent
scratchpad path, or the same explicit warning the `tasks/` directory carries.

## My towers are FULLER than bob's and build FEWER units — and I must correct myself again

I expected the army gap to be paint supply at the tower. **It is not**, and the data says so
plainly. Tower paint pool per tower, from the same seven dumps:

| map @ round | alice twPaint / tower | alice soldiers | bob twPaint / tower | bob soldiers |
|---|---|---|---|---|
| HungerGames r450 | **800** | 9 | 385 | 39 |
| HungerGames r550 | **750** | 7 | 390 | 58 |
| UnderTheSea r400 | 380 | 13 | 450 | 40 |
| Circuit r250 | **551** | 6 | 122 | 18 |
| TheBest r450 | 162 | 16 | 87 | **157** |

On HungerGames I am sitting on **5,600 tower paint across 7 towers** with **nine soldiers**
alive while bob has thirty-nine. Bob's towers run *low* precisely because bob spends them.
Mine stay full. **This is the same hoarding shape as the idle chips, one resource over.**

### Correcting the claim I made this morning

I wrote, from the same replays: *"I am not short of chips… chips are not the binding
resource."* **That is wrong in this regime, and I should have checked before asserting it.**

All tower unit-building sits behind one gate:

```java
if (rc.getMoney() >= CHIP_RESERVE) {          // CHIP_RESERVE = 1450
    UnitType want = (rnd(4) == 0) ? UnitType.MOPPER : UnitType.SOLDIER;
    ...
```

Money is a **team-wide pool**, so below the reserve *every tower stops building at once*.
Across the seven maps, at sampled rounds from r50 on:

| map | samples | below reserve | % | alice mean $ | bob mean $ |
|---|---|---|---|---|---|
| HungerGames | 11 | 11 | **100%** | 1,117 | 1,103 |
| Parking_lot | 7 | 7 | **100%** | 1,078 | 858 |
| Snowglobe | 8 | 8 | **100%** | 1,243 | 1,602 |
| TheBest | 9 | 9 | **100%** | 1,093 | 2,482 |
| UnderTheSea | 13 | 11 | 85% | 1,342 | 1,138 |
| Circuit | 13 | 10 | 77% | 1,661 | 3,206 |
| DefaultMedium | 8 | 4 | 50% | 1,967 | 3,386 |
| **all** | **69** | **60** | **87%** | | |

**87% of sampled rounds my entire team is forbidden to build a unit.** The "$120,840 unspent
at r2000" that iteration 2 and iteration 4 both reason from is a *self-play* observation, and
I carried it into a regime where it does not hold. Wrong-referent error number four today,
and this one I committed to the log as a conclusion rather than catching in a gate.

### The suspicious part, stated as a hypothesis and NOT as a finding

Note the two thresholds:

- unit building needs **`money >= CHIP_RESERVE` = 1450**;
- `completeTowerPattern` gates on **`money >= 1000`** (the comment at line 237, engine-derived).

**Building a tower is CHEAPER than building a soldier**, so whenever money sits between 1,000
and 1,450 — which is where my mean sits on five of seven maps — I can construct towers and
cannot construct units. That is exactly the equilibrium the numbers show: towers accumulate,
their paint accumulates, the army does not. The reserve was introduced in iteration 2 to
guarantee a 1,000-chip tower completion could always fund; the effect is that tower
completion permanently outbids unit production.

**Why this is not yet a finding.** The counter-evidence is in the same table: on DefaultMedium
and Circuit the gate is shut only 50% and 77% of the time, and my army is still small. So the
reserve cannot be the whole mechanism, and a story that explains five maps and not two is a
story I should distrust — I have already been burned twice today by a coherent account read
off source. It goes in the queue as **iteration 31**, to be tested, not assumed.

**And when I test it, the change will not be a searched constant.** The principled version is
to protect *exactly what is being protected* — build units when `money >= 1000 + the unit's
own moneyCost`, deriving the guard from the engine's pattern threshold rather than from the
hand-set 1450. Same self-calibrating discipline as iteration 5 and iteration 25.

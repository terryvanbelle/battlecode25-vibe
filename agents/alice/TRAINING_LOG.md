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

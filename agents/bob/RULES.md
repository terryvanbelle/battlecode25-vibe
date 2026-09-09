# BC25 "Chromatic Conflict" — Rules digest (Bob)

## STANDING PROHIBITION — BC25 finals bots are a YARDSTICK, not an opponent to study (2026-09-07)

Set by the project owner via the coordinator, effective immediately, and **binding on every
future session of mine**. It sits at the top of this file because a fresh session reads
`RULES.md` early and must not have to discover it by accident.

Finals bots from the BC25 contest have been downloaded to measure how far each lineage is
from a tournament-winning bot. I am **absolutely forbidden** to:

- read their source in any form;
- examine **any game played against them** — no replay, log, trace, dump, indicator
  string, or derived counter;
- seek out, request, or reason from any such artefact.

Enforcement I do not need to reproduce but should understand: their source lives only on
battlecode-dev outside this checkout and is `.gitignore`d; **no replay file is written for
those games at all**, so no artefact exists to examine; only the score survives (which side
won, in how many rounds); and **the coordinator runs those matches, not me.**

**What I may do:** read a benchmark score if it appears in a committed results file.
That is the whole of it. **If I ever find myself holding such an artefact, I stop and tell
the coordinator.**

**Why this lands on me in particular.** My last two days of work — the denial probes, the
per-unit replay counters, `--robot` tracing, and the whole habit of answering questions by
dumping a replay — point at exactly the artefacts now off limits *for benchmark games
only*. The reflex is the risk. So, concretely: **never point `tools/replay-dump.sh`, a
probe package, or any counter at a benchmark game**, and never go looking for the finals
bots' files on the VM.

**Unaffected, and to be used exactly as before:** my own gauntlet, my synthetic archetypes
(`bob_denier`), my frozen roster, and the three-way agent tournament in `tournaments/`.

A bad benchmark score is **information about distance, not a target**. Tuning toward it
would be both forbidden and self-defeating — it is the one instrument I have that my own
lineage did not produce, and its value comes entirely from my never having adapted to it.

The standing 2025 post-mortem ban and the no-downloaded-bot-implementations rule are
unchanged and still apply to me.


Ground truth from: official specs.pdf (V3.1.0 changelog current) + reflection dump of
`battlecode25-java-3.1.0.jar` (the engine the VM uses). Engine dump is authoritative for numbers.

## Objective / win conditions
- Win immediately by painting **>70% of paintable squares** (`PAINT_PERCENT_TO_WIN=70`), or by
  destroying ALL enemy robots AND towers.
- At round 2000 (`GAME_MAX_NUMBER_OF_ROUNDS`), tiebreakers in order:
  1. area painted, 2. allied towers alive, 3. total money, 4. sum of paint across robots+towers,
  5. allied robots alive, 6. coin flip.
- Teams may also lose by exceeding **20 min total team execution time** (`MAX_TEAM_EXECUTION_TIME`
  = 1.2e12 ns) — keep wall-clock cheap, not just bytecode.

## Map
- 20x20 .. 60x60. (0,0) bottom-left, x→East, y→North.
- Guaranteed symmetric by **rotation or reflection** (infer which; extrapolate hidden half).
- Walls ≤20% of map; not paintable/passable. Ruins: 5x5 zones, centers ≥5 apart
  (`MIN_RUIN_SPACING_SQUARED=25`), **never any walls in the 5x5 around a ruin center**; not
  passable/paintable. Ruins only visible within vision radius.
- Paintable squares = all non-wall, non-ruin squares (the 70% denominator).

## Resources
- **Paint** — per-robot/tower stash (capacity by type). Used to paint tiles, attack, mark.
- **Chips (money)** — team-global. Start `INITIAL_TEAM_MONEY=2500`. Money towers mine it.
- Start: 2 towers — 1 paint + 1 money — **both at LEVEL TWO** (V3.0.0 change), each with
  `INITIAL_TOWER_PAINT_AMOUNT=500` paint. Towers regen paint only if paint tower (paintPerTurn).

## Paint mechanics (the core)
- Only **soldiers** paint single tiles (their attack paints empty/ally tiles; CANNOT overwrite
  enemy paint). **Splashers** AoE-paint empty/ally tiles in r²≤4 and CAN replace enemy paint but
  only within r²≤2 of center (`SPLASHER_ATTACK_ENEMY_PAINT_RADIUS_SQUARED=2`). **Moppers** remove
  enemy paint (attack r²≤2). So enemy territory is only reduced by splashers/moppers.
- Primary vs secondary ally colors are identical for territory; only matter for pattern matching.
- **Paint penalties per turn** (from robot's own stash): end turn on neutral −1, on enemy −2
  (`PENALTY_NEUTRAL/ENEMY_TERRITORY`); PLUS 1 × (# adjacent allied robots in the 8 neighbors),
  doubled while in enemy territory. Moppers pay **2×** the territory penalties
  (`MOPPER_PAINT_PENALTY_MULTIPLIER=2`).
- **Low-paint cooldown**: stash <50% full (`INCREASED_COOLDOWN_THRESHOLD=50`) ⇒ cooldowns
  increased by (100−2X)% where X = percent full (intercept 100, slope −2).
- **Zero paint**: cannot move or act (except disintegrate), loses `NO_PAINT_DAMAGE=20` HP/turn.
  (`MAX_TURNS_WITHOUT_PAINT=10` ⇒ 10 turns to death from full HP 200... type-dependent.)
- Robots spawn with stash 100% full (paint cost of the unit is paid by the spawning tower's stash).
- Refill: withdraw from allied towers via `transferPaint(loc, negative)` r²≤2, cd +10; or a mopper
  transfers to allies r²≤2.

## Units (exact stats from engine)
| | HP | paint cap | cost paint/chips | attack cost | action r² | dmg | action cd |
|---|---|---|---|---|---|---|---|
| SOLDIER | 250 | 200 | 200/250 | 5 | 9 | 50 (towers only) | 10 |
| SPLASHER | 150 | 300 | 300/400 | 50 | 4 (target ≤2 tiles) | 100 AoE (towers only) | 50 |
| MOPPER | 50 | 100 | 100/300 | 0 | 2 | −10 paint to robot on tile (+5 to self) | 30 |

- Units **cannot damage enemy units' HP** — only towers take attack damage; unit-v-unit combat is
  paint attrition (mopper attack/swing) + luring under towers.
- Mopper `mopSwing(cardinal)`: −5 paint (`MOPPER_SWING_PAINT_DEPLETION`) to enemy robots in the
  2×3 zone (1 and 2 steps in that direction, 3 wide), cd 20 (`ATTACK_MOPPER_SWING_COOLDOWN`).
- Movement cd +10 per move; all cds decrement 10/turn; act when cd <10 (`COOLDOWN_LIMIT`).
- `BUILD_ROBOT_RADIUS_SQUARED=4` (tower spawns within 2 blocks), build cd +10.

## Towers
| | chips (L1/L2/L3) | HP | attack r² | single dmg | AoE dmg | mining |
|---|---|---|---|---|---|---|
| MONEY | 1000/2500/5000 | 1000/1500/2000 | 9 | 20 | 10 | 20/30/40 chips/turn |
| PAINT | 1000/2500/5000 | 1000/1500/2000 | 9 | 20 | 10 | 5/10/15 paint/turn |
| DEFENSE | 1000/2500/5000 | 2000/2500/3000 | 16 | 40/50/60 | 20/25/30 | 20/30/40 chips per successful attack |

- Tower paint capacity 1000. Every alive defense tower buffs allied towers' **single-block**
  attack +5/+7/+9 by level (`EXTRA_DAMAGE_FROM_DEFENSE_TOWER=5`, `+2`/level; AoE unaffected).
- Each turn a tower can do ONE single-block attack AND ONE AoE attack (AoE hits all enemies in range).
- **A TOWER attack adds NO action cooldown** (javap 3.1.0, `RobotControllerImpl.attack(loc, bool)`:
  the `addActionCooldownTurns` call sits behind `ifeq` on `getType().isRobotType()`). So a tower can
  attack AND build on the same turn, and "the enemy is in range" never blocks production. `buildRobot`
  DOES add the cooldown, and `assertCanAttack` asserts action-ready, so **attack first, then build** --
  the reverse order silently costs the attack. Verified iteration 41.
- **`assertCanBuildRobot` requires `tower.getPaint() >= type.paintCost`** as well as
  `teamMoney >= type.moneyCost` (javap 3.1.0). Paint costs differ by type -- **MOPPER 100, SOLDIER 200,
  SPLASHER 300** -- so a tower's paint stash decides *which* units it may build, not merely whether it
  may build. A tower holding 200-299 paint can build a soldier and cannot build a splasher. Combined
  with `paintPerTurn == 0` on money towers (which therefore never regain paint), a spawn policy with no
  cheaper fallback can wedge a tower permanently. Verified iteration 41.
- Build: paint the type's 5x5 pattern around a ruin, then `completeTowerPattern` (adjacent, r²≤2).
  `markTowerPattern` costs 25 paint, marks the 5x5. Towers always built at level 1; `upgradeTower`
  (r²≤2) costs the next level's chips. **Max 25 towers** (`MAX_NUMBER_OF_TOWERS`).
- Destroying a tower frees its ruin for either team to rebuild — towers are recapturable ground.

### 5x5 patterns (bit=secondary color; row 0 = bottom?  verify with getTowerPattern at runtime)
```
RESOURCE      PAINT tower   MONEY tower   DEFENSE tower
##.##         #...#         .###.         ..#..
#...#         .#.#.         ##.##         .###.
..#..         ..#..         #...#         #####
#...#         .#.#.         ##.##         .###.
##.##         ##.##→#...#   .###.         ..#..
```

## SRP (Special Resource Pattern)
- Paint RESOURCE_PATTERN anywhere paintable (center ≥? use canMarkResourcePattern), then
  `completeResourcePattern` costs 200 chips (`COMPLETE_RESOURCE_PATTERN_COST`).
- Must stay undisrupted **50 rounds** (`RESOURCE_PATTERN_ACTIVE_DELAY`) to activate; then ALL
  allied mining towers mine **+3 resources/turn per active SRP** (`EXTRA_RESOURCES_FROM_PATTERN`).
- `RESOURCE_PATTERN_RADIUS_SQUARED=8` (marking reach); `isResourcePatternCenter()` on MapInfo.

## Communication
- Message = 32-bit int (`MAX_MESSAGE_BYTES=4`) + sender id + round. Buffer keeps 5 rounds
  (`MESSAGE_ROUND_DURATION`).
- **Robot↔tower only**, within r²≤20 (`MESSAGE_RADIUS_SQUARED`) AND connected by ally paint
  (path over own-paint tiles). Robots send ≤1 msg/turn, towers ≤20.
- Towers broadcast tower→all allied towers within r²≤80 (`BROADCAST_RADIUS_SQUARED`), no paint
  connectivity needed, counts toward the 20.
- **Markers**: ally-visible map annotations (primary/secondary), `mark()` r²≤2 costs 1 paint, no
  cooldown; a free-ish persistent shared blackboard on terrain. No gameplay effect.

## Bytecode / limits
- Robots **17500**, towers **20000** (`ROBOT/TOWER_BYTECODE_LIMIT`) — LOW; nav must be cheap.
- Overrun silently pauses mid-instruction, resumes next turn. Detect: round number changed across
  own turn body, and `Clock.getBytecodeNum()` near limit.
- Exceptions cost 500 bytecode penalty. Array creation costs ≈ array length. java.util counted as
  own code. Banned: Class.forName, String.intern, wait/notify. 8Mb heap/robot.

## Radius/vision asymmetries (exploitables)
- Vision r²=20 for everything > all action radii — you always see attackers.
- **Defense tower attack r²=16 outranges soldier attack r²=9**: soldiers sieging a defense tower
  eat 40+ dmg before shooting. Paint/money towers r²=9 = soldier range: a soldier at exactly r²=9
  trades 50 dmg for 20+10.
- Splasher target range r²=4 but must get within 2 tiles of towers (r²16 defense) — splashers are
  glass (150 HP) vs defense towers.
- Mop swing reaches 2 tiles cardinally (beyond mopper attack r²=2).
- Message r²=20 = vision; broadcast r²=80 = tower relay backbone.

## Pattern mechanics (javap-verified, iteration 10)
- `assertCanMarkResourcePattern` has exactly four conditions: robot type,
  `assertCanActLocation(loc, 8)`, `GameWorld.isValidPatternCenter(loc, false)`, and
  `getPaint() >= 25`. So a pattern may be MARKED at any centre with r² ≤ 8 — all 25 tiles
  of the surrounding 5x5, since (2,2) is r² = 8.
- `isValidPatternCenter` = `x >= 2 && y >= 2 && x < width-2 && y < height-2 &&
  areaIsPaintable(loc)` (all 25 tiles free of walls and ruins). This is the dominant
  refusal in practice: measured at 87-99% of SRP start attempts.
- **Marking at range is legal; PAINTING at range is not.** Soldier action r² = 9 and the
  5x5 around the soldier's OWN tile tops out at r² = 8 — that exact fit is the design.
  A centre at r² = 8 puts the pattern's far corner at r² = 32, unreachable. Do pattern
  work from the centre tile.
- **`senseNearbyMapInfos(centre, r)` SILENTLY TRUNCATES**: it builds
  `getAllLocationsWithinRadiusSquared(centre, min(r, visionR2))` and then filters by
  `canSenseLocation` — it does NOT throw for tiles out of vision. Any area check around a
  remote point must verify the returned count, or it is approving ground it cannot see.
  With vision r² = 20, only the 13 offsets with dx²+dy² ≤ 4 have their whole 5x5 visible
  ((2,0) lands on 20, (2,1) on 25).
- **Marks are a contended, map-wide resource.** `markTowerPattern` blankets a 5x5 around
  every ruin under construction, and a resource pattern marked over those tiles would
  overwrite them and break the tower. Tower patterns and resource patterns compete for
  ground; measured, existing marks refuse >100% of geometrically-valid SRP candidates per
  turn in ruin-dense areas.

## Misc engine facts
- `getAllLocationsWithinRadiusSquared`, `senseNearbyRuins(int)` exist. `getChips()==getMoney()`.
- `attack(loc)` / `attack(loc, useSecondary)`; mopper attack with no target tile? attack(loc) mops.
- `canUpgradeTower/upgradeTower(loc)`, `transferPaint(loc,amt)` (neg = withdraw/mop-steal).
- Tower spawn list = SOLDIER/SPLASHER/MOPPER only; towers are built from patterns, never spawned.
- `Clock.yield()` ends turn; robot IDs ≥ 10000; engine deterministic per spec (verify done — see
  TRAINING_LOG Phase 0).
- Turn order is sequential within a round (spawn order). `GAME_DEFAULT_SEED=6370`.

## Engine internals (from GameWorld.java)
- **SRP integrity re-checked every round**: if ANY tile of an SRP stops matching, ownership
  resets to NEUTRAL and the 50-round activation clock restarts from 0. One enemy
  splash/mop inside the 5x5 de-activates it. SRPs deep in safe territory only.
- **Coverage denominator = areaWithoutWalls** (ruins ARE in the denominator though
  unpaintable). Coverage tracked in per-mil per round in replays.
- Pattern bit at (dx,dy): bit index 5*(dx+2)+(dy+2) — use rc.getTowerPattern()/
  getResourcePattern() rather than hand-decoding.
- Defense-tower buff applied on spawn/upgrade/destroy of defense towers, team-global.
- Tower destroyed → towersByLoc=NEUTRAL, ruin becomes rebuildable by either team.

## Economy quick math
- Start: 2500 chips + 30 chips/turn (money L2) + 10 paint/turn (paint L2), 500 paint per tower.
- Soldier = 250c+200p; new tower = 1000c (+ ~30-50 paint for the pattern, 25 mark).
- A 3rd tower (money L1, 20c/t) repays 1000 chips in 50 turns. Money L2 upgrade (2500c, +10c/t)
  repays in 250 turns — expansion-to-new-ruins dominates upgrades early.
- **SRP bonus — VERIFIED from bytecode 2026-09-08, no longer inferred.**
  `InternalRobot.processBeginningOfRound` reads:

  ```
  if (type.paintPerTurn != 0) addPaint(type.paintPerTurn + world.extraResourcesFromPatterns(team));
  if (type.moneyPerTurn != 0) teamInfo.addMoney(team, type.moneyPerTurn + world.extraResourcesFromPatterns(team));
  ```
  with `extraResourcesFromPatterns(team) = getNumResourcePatterns(team) * 3`.

  So with `S` active SRPs each tower gets **+3S of its own resource per turn**, once per tower
  — and the `!= 0` guards mean a MONEY tower (paintPerTurn 0) gets **no paint bonus at all**,
  and a PAINT tower (moneyPerTurn 0) gets no chip bonus. Per-turn yields:

  | | L1 | L2 | L3 |
  |---|---|---|---|
  | PAINT tower | 5+3S | 10+3S | 15+3S |
  | MONEY tower | 20+3S | 30+3S | 40+3S |

  **SRPs are disproportionately a PAINT multiplier**, because the flat +3S is a larger share of
  the smaller base: at L3 and S=4 a paint tower goes 15→27 (**+80%**) and a money tower 40→52
  (**+30%**). This is the engine fact behind iteration 12's mechanism ("an SRP's return is
  multiplied by your paint-tower count"), and that note stated only the paint half — the same
  +3S also lands on every money tower as chips.

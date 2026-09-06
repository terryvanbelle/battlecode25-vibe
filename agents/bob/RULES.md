# BC25 "Chromatic Conflict" — Rules digest (Bob)

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

## Misc engine facts
- `getAllLocationsWithinRadiusSquared`, `senseNearbyRuins(int)` exist. `getChips()==getMoney()`.
- `attack(loc)` / `attack(loc, useSecondary)`; mopper attack with no target tile? attack(loc) mops.
- `canUpgradeTower/upgradeTower(loc)`, `transferPaint(loc,amt)` (neg = withdraw/mop-steal).
- Tower spawn list = SOLDIER/SPLASHER/MOPPER only; towers are built from patterns, never spawned.
- `Clock.yield()` ends turn; robot IDs ≥ 10000; engine deterministic per spec (verify done — see
  TRAINING_LOG Phase 0).
- Turn order is sequential within a round (spawn order). `GAME_DEFAULT_SEED=6370`.

## Economy quick math
- Start: 2500 chips + 30 chips/turn (money L2) + 10 paint/turn (paint L2), 500 paint per tower.
- Soldier = 250c+200p; new tower = 1000c (+ ~30-50 paint for the pattern, 25 mark).
- A 3rd tower (money L1, 20c/t) repays 1000 chips in 50 turns. Money L2 upgrade (2500c, +10c/t)
  repays in 250 turns — expansion-to-new-ruins dominates upgrades early; SRPs (200c → +3/t per
  mining tower!) repay extremely fast once tower count grows: with T mining towers, an SRP is
  +3T/turn... (verify: is it +3 per tower per SRP? spec says "all allied mining towers will mine
  3 more resources per turn" per active pattern — yes, scales with tower count).

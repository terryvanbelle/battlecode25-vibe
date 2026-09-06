# BC25 "Chromatic Conflict" — Rules digest (engine v3.1.0)

Sources: official spec PDF (v3.1.0) + engine source (github.com/battlecode/battlecode25)
+ jar `battlecode25-java-3.1.0` on battlecode-dev. Engine source is authoritative;
line refs below are to `engine/src/main/battlecode/world/*.java`.

## Objective & win conditions
- Win instantly by painting **>= 70%** of `areaWithoutWalls` (TeamInfo.java:77 uses `>=`).
  NOTE: denominator = all squares minus walls; **ruin squares count in the denominator
  but cannot be painted**, so maps with many ruins raise the effective bar.
- Win instantly by destroying ALL enemy units (robots + towers both count;
  GameWorld.destroyRobot → DESTROY_ALL_UNITS).
- Round limit 2000. Tiebreaker order (GameWorld.checkEndOfMatch):
  1. more squares painted, 2. more towers alive, 3. more money,
  4. more paint stored across units+towers, 5. more robots alive,
  6. `Math.random()` (engine's ONLY nondeterminism — coin-flip ties are real).

## Map
- 20x20 .. 60x60. Symmetric by rotation or reflection (guaranteed). (0,0) = bottom-left.
- Walls: impassable, unpaintable, <= 20% of map. Ruins: impassable, unpaintable, permanent.
- Ruin centers >= sqrt(25) apart; no walls within the 5x5 around a ruin center.
- Each team starts with 2 towers (1 paint + 1 money), both **level 2**, sitting on ruins.
  When a tower dies, its ruin remains → either team can rebuild there.

## Resources
- **Paint**: per-unit stash. Robots spawn 100% full. Towers store up to 1000, start w/ 500.
- **Chips (money)**: team-wide. Start 2500. Money towers: 20/30/40 per turn by level.
- Paint towers: 5/10/15 paint/turn by level.
- **SRP (special resource pattern)**: 5x5 painted pattern; complete costs 200 chips;
  must survive undisturbed 50 rounds to activate; then **+3 resources/turn to EVERY
  producing tower** (engine adds `extraResourcesFromPatterns` to both paintPerTurn
  and moneyPerTurn towers — i.e., each active SRP gives every paint tower +3 paint
  AND every money tower +3 chips per turn). SRPs can be destroyed by disrupting paint.
  Pattern is fixed (GameConstants.RESOURCE_PATTERN = 28873275).

## Paint mechanics
- Tiles: EMPTY / ALLY_PRIMARY / ALLY_SECONDARY / ENEMY_* . Primary vs secondary
  identical except for pattern matching.
- End-of-turn paint penalties (InternalRobot.processEndOfTurn):
  - on neutral tile: -1 (mopper -2); on enemy tile: -2 (mopper -4); ally tile: 0.
  - PLUS -1 per adjacent (8-dir, r^2<=2) ally robot; **doubled (-2/adj) on enemy tile**.
    Clumping is taxed! (mopper multiplier does NOT apply to the adjacency part).
- 0 paint at end of turn → -20 HP/turn, and cannot move/act (except disintegrate) until refilled.
- Low paint cooldown scaling: below 50% stash, cooldowns multiplied by
  (100 - 2*X)% extra where X = paint %. (INCREASED_COOLDOWN_* in GameConstants).

## Units (UnitType.java ground truth)
| unit | HP | paint cap | cost paint/chips | atk cost | actionCD | actRadius^2 | dmg |
|---|---|---|---|---|---|---|---|
| Soldier | 250 | 200 | 200/250 | 5 | 10 | **9** | 50 to towers only |
| Splasher | 150 | 300 | 300/400 | 50 | 50 | **4** (center) | 100 to towers (AoE) |
| Mopper | 50 | 100 | 100/300 | 0 | 30 (mop), 10 (transfer), 20 (swing) | **2** | -10 paint from enemy robot (+5 to self) |

- All robots+towers: **vision^2 = 20** (sqrt20 ≈ 4.47).
- Movement cooldown 10; all cooldowns -10/turn; act when cooldown < 10.
- **Soldier attack** (InternalRobot.soldierAttack): if target holds enemy TOWER → 50 dmg
  (never damages robots); else paints tile if empty or already-ally. Cannot overwrite enemy paint.
- **Splasher attack**: target center within dist^2<=4; every tile within r^2<=4 of center:
  enemy tower there takes 100; empty/ally tiles painted; enemy paint overwritten ONLY within
  r^2<=2 of center. Effective max reach to a tower = 2+2 straight = **dist^2 16**.
- **Mopper attack** (mop, r^2<=2): removes enemy paint on tile; if enemy ROBOT on it:
  steals 10 paint (gains 5). Free (0 paint).
- **Mop swing** (cardinal, CD 20): 2 rows of 3 tiles in front, -5 paint per enemy robot hit (6 tiles).
- **transferPaint** r^2<=2: moppers give to ally robots/towers; ANY robot can withdraw
  from ally towers (negative amount). CD 10.

## Towers
| type | build/upg cost (chips) | actRadius^2 | single dmg | AoE dmg | prod | HP |
|---|---|---|---|---|---|---|
| Money L1/2/3 | 1000/2500/5000 | 9 | 20 | 10 | 20/30/40 chips | 1000/1500/2000 |
| Paint L1/2/3 | same | 9 | 20 | 10 | 5/10/15 paint | 1000/1500/2000 |
| Defense L1/2/3 | same | **16** | 40/50/60 | 20/25/30 | +20/30/40 chips per attack that hits | 2000/2500/3000 |

- Towers get BOTH one single-target attack AND one AoE attack per turn
  (`attack(null)` = AoE). AoE hits every enemy robot in action radius.
- Each live defense tower buffs ALL ally towers' single-target dmg +5/+7/+9 by level
  (0% of buff applies to AoE).
- Build: paint the type's 5x5 pattern around a ruin (primary/secondary must match
  pattern; `markTowerPattern` costs 25 paint, marking optional), then
  `completeTowerPattern`. Towers always built at L1; upgrade within r^2<=2 for chip cost.
  Tower cap: 25/team. New towers spawn with 500 paint.
- Spawn: tower builds robots within r^2 <= 4, costs paint (from tower stash) + chips; CD 10.

## Radius asymmetries (exploitable)
- **Splasher outranges paint/money towers**: splasher damages a tower at up to dist^2 16
  (center at 4, tower 2 beyond) vs tower attack r^2 9. A splasher can siege paint/money
  towers with ZERO retaliation. Defense towers (r^2 16) exactly match splasher max reach.
- **Defense towers outrange soldiers** (16 vs 9): soldiers eat hits closing on defense towers.
- Soldier vs paint/money tower is even range (9 = 9): soldier trades 50 dmg/turn vs
  20(+buff) taken — soldiers win the trade heavily; 3+ soldiers melt towers.
- All action radii < vision (20): everything you can hit, you can see.

## Communication
- Robot ↔ tower messaging only (never robot↔robot): r^2<=20 AND **connected by
  4-adjacent ally paint path** (GameWorld.connectedByPaint = BFS). 1 msg/turn robots,
  20/turn towers; 4-byte int + senderID + round; buffer keeps 5 rounds.
- **Tower→tower broadcast**: r^2 <= 80, no paint connectivity needed, counts as 1 msg.
- Markers: ally-visible map annotations (primary/secondary/empty), placed r^2<=2, cost 1
  paint (pattern-mark 25). No gameplay effect other than pattern guide; a durable
  ally-only shared-memory channel on the ground.

## Bytecode & determinism
- 17500/turn robots, 20000/turn towers. Exceeding pauses mid-instruction silently,
  resumes next turn. Exception throw = 500 bytecode penalty.
- `Clock.getBytecodeNum()`, `rc.getRoundNum()` for monitoring. 8MB heap cap/robot.
- Team execution time cap 20 min/match (wall clock) → auto-resign.
- Engine deterministic EXCEPT final random tiebreak (Math.random) and map-random seed
  fixed at 6370 by default. Turn/exec order: robots by (roundsAlive, ID) —
  older robots move first each round (InternalRobot.compareTo).
- Engine scan order (senseNearby*, getAllLocationsWithinRadiusSquared): x ascending
  then y ascending — fixed absolute order, audit for play-symmetry bugs.

## Misc engine facts
- addHealth clamps at type max (no overheal).
- Tower AoE dmg + single dmg can stack on one target (both attacks same turn).
- `canSenseRobotAtLocation` etc. limited to vision. Ruins sensed only within vision
  (`senseNearbyRuins`).
- Message/paint/mark constants all in GameConstants.java (copied to scratchpad).
- Defense tower "mining" = attackMoneyBonus 20/30/40 chips per attack that hits >=1
  robot (single and AoE each count, no stacking per extra target hit).

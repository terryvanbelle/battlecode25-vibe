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
  **SRPs are fragile (engine-verified)**: `GameWorld.updateResourcePatterns`
  re-checks the whole 5x5 EVERY round; if one tile stops matching, the centre is
  dropped and its lifetime **resets to 0**, so it must survive another full 50
  rounds after any disruption. One enemy mop inside an SRP costs 50 rounds of
  its income. Build them in our own interior, never at the frontier.
  Constants: COMPLETE_RESOURCE_PATTERN_COST 200, RESOURCE_PATTERN_RADIUS_SQUARED 8,
  RESOURCE_PATTERN_ACTIVE_DELAY 50. `MapInfo.isResourcePatternCenter()` detects one.

## Paint mechanics
- Tiles: EMPTY / ALLY_PRIMARY / ALLY_SECONDARY / ENEMY_* . Primary vs secondary
  identical except for pattern matching.
- End-of-turn paint penalties (InternalRobot.processEndOfTurn):
  - on neutral tile: -1 (mopper -2); on enemy tile: -2 (mopper -4); ally tile: 0.
  - PLUS -1 per adjacent (8-dir, r^2<=2) ally ROBOT; **doubled (-2/adj) on enemy tile**.
    Clumping is taxed! (mopper multiplier does NOT apply to the adjacency part).
    **The adjacency tax is charged on ALLY tiles too** — the ally-tile branch of
    `processEndOfTurn` is `addPaint(-allyRobotCount)`, so standing on your own
    paint waives only the *terrain* penalty, never the crowding one. A fully
    surrounded robot pays -8/turn anywhere on the map (200-paint soldier stash,
    100-paint mopper). Only robots count; adjacent towers are free.
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

### Reading `UnitType` from the jar — the field order (verified 2026-09-08)

**Resolve the jar with `tools/engine-jar.sh`, never with a bare `find`.** battlecode-dev's
gradle cache holds **both** `battlecode25-java-1.0.0.jar` and `3.1.0`, so
`find -name 'battlecode25*.jar' | head -1` can return either, and a wrong *constant* does not
announce itself the way a missing *method* does. Discriminating check on any jar you are
handed: `getChips` and `getNumberTowers` exist in 3.1.0 and in neither case in 1.0.0.
Everything in this section was read from the path `tools/engine-jar.sh --remote` resolves to,
confirmed byte-identical (2026-09-08).

`javap -p -c battlecode.common.UnitType` shows a 14-arg enum constructor
(`String, ordinal, then 13 ints`). The 13 ints are, in order:

```
paintCost, moneyCost, attackCost, health, level, paintCapacity, actionCooldown,
actionRadiusSquared, attackStrength, aoeAttackStrength, paintPerTurn, moneyPerTurn,
attackMoneyBonus
```

Confirmed against `javap -p` field declarations. Spot values that pin the order:
`SOLDIER` = 200, 250, 5, 250, -1, 200, 10, 9, 50, -1, 0, 0, 0;
`LEVEL_ONE_PAINT_TOWER` = 0, 1000, 0, 1000, 1, 1000, 10, 9, 20, 10, **5**, 0, 0;
`LEVEL_ONE_MONEY_TOWER` = same but **paintPerTurn 0, moneyPerTurn 20**.

**A money tower's `paintPerTurn` is 0.** It spawns from the 500 paint it is born
with and never regenerates any, absent a mopper transfer.

**But do NOT price the two tower types against each other with a per-turn rate.**
Chips buy towers (`completeTowerPattern` gates on `getMoney() >= 1000`; upgrades
2,500/5,000) and towers produce both currencies; paint buys nothing that
produces. Dividing both by `SOLDIER.*Cost` to get "soldiers funded per turn"
makes an investment and a consumable look commensurable and is a category error
-- it cost iteration 34 a full census. See LEARNINGS, "you cannot compare a
COMPOUNDING resource to a CONSUMPTIVE one with a per-turn rate".

- **Vision vastly exceeds action range for every unit** — the exploitable gap:

  | unit | vision r² | action r² | tiles seen vs actionable |
  |---|---|---|---|
  | soldier | 20 | 9 | ~60 vs ~28 |
  | splasher | 20 | 4 (centre) | ~60 vs ~12 |
  | **mopper** | 20 | **2** | **~60 vs 8** |

  A unit that only *acts* on what falls inside the small circle, and moves at
  random otherwise, throws away most of its own sensing. Navigating toward the
  nearest actionable target in vision is the cheap general fix (iteration 7, for
  moppers: unpaints per mopper alive roughly tripled).
- Movement cooldown 10; all cooldowns -10/turn; act when cooldown < 10.
- **Soldier attack** (InternalRobot.soldierAttack): if target holds enemy TOWER → 50 dmg
  (never damages robots); else paints tile if empty or already-ally. Cannot overwrite enemy paint.
  **TRAP (engine-verified by javap, 2026-09-07)**: `addPaint(-SOLDIER.attackCost)` is invoked
  at bytecode offset 58, **unconditionally and before the target is examined at all**. The
  enemy-paint bail-out is at offset 207 (`if getPaint(loc)!=0 && teamFromPaint(mine)!=
  teamFromPaint(there) -> return`), and the not-paintable bail-out at 170 -- both AFTER the
  debit. So **attacking an enemy-painted tile costs the full 5 paint and does nothing.**
  `canAttack` does not protect you: it checks range and action-readiness, not the tile's
  paint. Every soldier attack must be guarded by `paint == EMPTY || paint.isAlly()` at the
  call site. This is the single largest paint leak found in this lineage (iteration 22).
- **Splasher attack**: target center within dist^2<=4; every tile within r^2<=4 of center:
  enemy tower there takes 100; empty/ally tiles painted; enemy paint overwritten ONLY within
  r^2<=2 of center. Effective max reach to a tower = 2+2 straight = **dist^2 16**.
- **Mopper attack** (mop, r^2<=2): removes enemy paint on tile; if enemy ROBOT on it:
  steals 10 paint (gains 5). Free (0 paint).
- **Mop swing** (cardinal, CD 20): 2 rows of 3 tiles in front, -5 paint per enemy robot hit (6 tiles).
- **transferPaint** r^2<=2: moppers give to ally robots/towers; ANY robot can withdraw
  from ally towers (negative amount). CD 10. Cannot target self; amount != 0;
  withdraw capped by the tower's current paint.
  **TRAP (engine-verified)**: `transferPaint(loc, -N)` credits the withdrawer via
  `addPaint`, which CLAMPS at its capacity, while the tower is debited the FULL N.
  Asking for more than you can hold silently burns the tower's paint. Always
  request exactly `min(myCapacity - myPaint, towerPaint)`.

## Towers
- **A tower can upgrade ITSELF for free.** `assertCanUpgradeTower` only calls
  `assertCanActLocation(loc, BUILD_TOWER_RADIUS_SQUARED=2)`, which checks range
  and on-map and nothing else — **no action-readiness check** — and
  `upgradeTower` adds **no cooldown**. Distance to self is 0, so the only cost
  is chips. `UnitType.getNextLevel()` returns null at level 3.
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

### Tower patterns (engine-verified, jar 3.1.0)
`GameConstants` pattern ints, decoded with `GameWorld.getPatternBit(pat, dx, dy)`
= `(pat >> (5*(dx+2) + dy+2)) & 1`; bit 1 = **secondary**, bit 0 = **primary**:

```
 PAINT 18157905    MONEY 15583086    DEFENSE 4685252    RESOURCE 28873275
   S...S             .SSS.             ..S..              SS.SS
   .S.S.             SS.SS             .SSS.              S...S
   ..S..             S...S             SSSSS              ..S..
   .S.S.             SS.SS             .SSS.              S...S
   S...S             .SSS.             ..S..              SS.SS
```
Paint = an X (8 secondary + 16 primary off-centre); Money = the outer ring
(16 secondary + 8 primary). `checkPattern` **skips the centre** for tower
patterns and requires every other tile to match **exactly** — empty or enemy
paint fails.

- **The two L1 tower types are identical in every cost.** `UnitType` fields for
  `LEVEL_ONE_PAINT_TOWER` and `LEVEL_ONE_MONEY_TOWER` differ **only** in
  `paintPerTurn` (5 vs 0) and `moneyPerTurn` (0 vs 20). Both are
  paintCost 0, moneyCost 1000, health 1000, paintCapacity 1000, cooldown 10,
  actionRadius^2 9, attack 20, AoE 10. There is **no engine asymmetry** that
  makes one type harder to build than the other.
- `assertCanCompleteTowerPattern` gates, in order: caller is a robot; type is a
  tower; `assertCanActLocation(ruin, 2)` (so **action-ready and within r^2 2**);
  no tower already there; `hasRuin`; `getMoney() >= 1000`; `isValidPatternCenter`;
  no robot standing on the ruin tile; `checkTowerPattern`; team tower count < 25.
- `markTowerPattern` costs 25 of the **robot's own** paint, needs r^2 <= 2 and
  action-readiness, and writes a marker to **all 25 tiles including the ruin
  centre** (`markPattern` loops dx,dy in -2..2 with no centre skip). So the ruin
  tile always carries a mark it can never satisfy — a "paint every marked tile
  that mismatches" loop must not treat that tile as actionable.

### Ruin parity is NOT uniform — and three maps are a tracing trap
**Canonical copy is shared ground: `../../tools/mapdata/`** (promoted from my
scan in `11c664f`). Do not keep a second copy here — a duplicated data file goes
stale exactly the way a forked archetype does. The summary below is for reading
convenience; `tools/mapdata/ruin_parity.txt` is the authority.
Ruin coordinates in the 75 official maps: **732 even `(x+y)`, 642 odd**. But the
split is per-map, and **FOUR maps are single-parity**: `gridworld`, `Filter`
and `Snowman` have ruins on even tiles ONLY (21/21, 5/5, 6/6), and
`CastleDefense` on odd tiles ONLY (0/6). (I listed only the three even ones
here for a week; `tools/mapdata/README.md` has had all four the whole time,
and the odd-only map is the one that inverts a policy rather than freezing it.)
Any policy keyed on `(x+y)&1`
degenerates to a single branch on those four maps. `DefaultMedium` (14 even /
5 odd) and `DefaultHuge` (34/15) are strongly skewed too. Verify a
geometry-keyed branch is actually exercised before tracing it on one map.


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

## Replay-action schema (needed to read replay dumps correctly)
- `PaintAction` — a tile painted (soldier/splasher/tower pattern work).
- `UnpaintAction` — **the only call site in the engine is `mopperAttack`**
  (`InternalRobot:417`), so this counter is exactly "tiles mopped by this team".
- `MopAction` — emitted **only** by `mopSwing` (twice per swing), never by an
  ordinary mop. A bot that never swings has `MopAction == 0` a priori; that zero
  says nothing about mopper activity. (This misread cost me a hypothesis.)
- `AttackAction` — soldier/splasher damage to a tower, tower attacks, and a
  mopper mopping a tile with an enemy robot on it.

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

## 5x5 patterns (decoded; '#' = secondary color, '.' = primary; rows top=+dy)
```
SRP        PAINT_TWR   MONEY_TWR   DEFENSE_TWR
##.##      #...#       .###.       ..#..
#...#      .#.#.       ##.##       .###.
..#..      ..#..       #...#       #####
#...#      .#.#.       ##.##       .###.
##.##      #...#       .###.       ..#..
```

## Misc engine facts
- addHealth clamps at type max (no overheal).
- Tower AoE dmg + single dmg can stack on one target (both attacks same turn).
- `canSenseRobotAtLocation` etc. limited to vision. Ruins sensed only within vision
  (`senseNearbyRuins`).
- Message/paint/mark constants all in GameConstants.java (copied to scratchpad).
- Defense tower "mining" = attackMoneyBonus 20/30/40 chips per attack that hits >=1
  robot (single and AoE each count, no stacking per extra target hit).

## UNUSED API — standing check (run it every ~10 iterations; it found a whole mechanic)

> **A DOSE-FINDING CHOICE BETWEEN ARMS ADVANCES ONLY AFTER REPLICATION ON A DISJOINT
> MAP SAMPLE.** A run is exact for the maps it played; that is not the same as precise about
> the map population. Resampling 25 of the 75 maps puts the sd of a 50-game win count at
> **2.8-3.1 wins** (coordinator, measured on tournament data). A *paired* run shares its maps
> between arms, so map difficulty partly cancels and the sd of the DIFFERENCE is smaller --
> which means the honest resolution is empirical, and you get it by replicating on disjoint
> maps, not by assuming zero and not by assuming ~3.
>
> ```bash
> # the 35 maps a 40-map run did NOT use
> comm -23 <(sort tools/bc25-maps.txt) <(sort gauntlet/<run>/maps.txt)
> ```
> The **full 75-map census accept gate is unaffected** -- it samples nothing, so its margin is
> exact for the pool. What is exposed is every 40-map dose comparison, and one of those
> inverted a prior of mine on a 7-point gap whose resolution I had never measured.

> **BEFORE A CONSTANT ENTERS A COST TABLE, GREP ITS USE SITE AND READ THE ASSERT.**
> This is a step, not a resolution to be careful. It exists because on 2026-09-08 I got the
> currency of two constants wrong in one session — `MOPPER_SWING_PAINT_DEPLETION` (drains
> *robot* paint, not tile paint) and `COMPLETE_RESOURCE_PATTERN_COST` (**chips**, not paint) —
> the second within an hour of writing up the first as a lesson. Both errors made a mechanic
> look better than it was, along the exact axis of the problem I was then trying to solve.
> A name that is *nearly* right defeats suspicion in a way a wrong one does not.
>
> ```bash
> # what actually charges this?  read the assert, not the name
> javap -c -p -cp $BC_JAR battlecode.world.RobotControllerImpl | grep -B20 '<CONSTANT>'
> javap -c -p -cp $BC_JAR battlecode.world.InternalRobot     # for the effect body
> ```
> `getPaint()` / `addPaint` in the assert means paint. `TeamInfo.getMoney` / `addMoney` means
> chips. Neither is inferable from the constant's name.

Phase 0 item 2 requires periodically sweeping `RobotController` for methods the bot never
calls. First run of this project was at iteration 29 and found **37 of 68 unused**, including
one entire mechanic. Reproduce with:

```bash
# JAR RESOLUTION IS NOT OPTIONAL -- battlecode-dev's gradle cache holds BOTH
# battlecode25-java-1.0.0.jar and 3.1.0, so `find -name 'battlecode25*.jar' | head -1`
# can silently return the wrong one. tools/engine-jar.sh reads the wanted version from
# arena/engine_version.txt and REFUSES to print a non-matching path.
J="$(../../tools/engine-jar.sh --remote)"
# PATH IS NOT OPTIONAL EITHER: battlecode-dev has no system JDK (no /usr/lib/jvm,
# `which javap` is empty). The JDK lives in ~/jdk21, which tools/gauntlet.sh
# exports for itself; a bare gssh gets a non-login shell without it and the
# command dies with "javap: command not found" (verified 2026-09-09, iteration 44).
gssh "export PATH=\$HOME/jdk21/bin:\$PATH
      javap -cp $J battlecode.common.RobotController \
      | sed -n 's/.* \([a-zA-Z][a-zA-Z0-9]*\)(.*/\1/p' | sort -u" > rc_api.txt
while read m; do grep -q "rc\.$m(" src/alice/RobotPlayer.java || echo "  $m"; done < rc_api.txt
```

**The 68 is verified against the right jar (2026-09-08), by the discriminating case rather
than by assertion**: this exact pipeline yields **68 unique names on 3.1.0 and 62 on 1.0.0**,
so the sweep that produced "37 of 68" read 3.1.0. The cheap version check on any jar is
`getChips` / `getNumberTowers` -- both present in 3.1.0, both absent from 1.0.0.

### RESOURCE PATTERNS (unused through iteration 29)

- `markResourcePattern(loc)` / `completeResourcePattern(loc)` / `canCompleteResourcePattern`
  / `getResourcePattern()` -> `boolean[][]`.
- `COMPLETE_RESOURCE_PATTERN_COST = 200` **CHIPS, not paint** (verified: 
  `assertCanCompleteResourcePattern` reads `TeamInfo.getMoney(team)` and errors *"Not enough
  money to complete resource pattern"*; `completeResourcePattern` calls `TeamInfo.addMoney`).
  `MARK_PATTERN_PAINT_COST = 25` IS paint, charged to the marking robot
  (`assertCanMarkResourcePattern` reads `getPaint()`). `EXTRA_RESOURCES_FROM_PATTERN = 3` chips/turn;
  `RESOURCE_PATTERN_ACTIVE_DELAY = 50` rounds; `RESOURCE_PATTERN_RADIUS_SQUARED = 8` (5x5).
- **Needs no ruin** — placeable on any 5x5 block of own paint, so uncapped by map features,
  unlike towers.
- **STACKING: VERIFIED.** `GameWorld.extraResourcesFromPatterns(team)` is literally
  `getNumResourcePatterns(team) * 3` (`iconst_3; imul`), with no cap in the method. Income is
  **+3 chips/turn per active pattern**, linear.
- **ACTIVATION: VERIFIED per-pattern.** `getNumResourcePatterns` counts centres owned by the
  team whose `resourcePatternLifetimes[idx] >= 50` (`bipush 50; if_icmplt`), so the 50-round
  delay is each pattern's own age, not a one-off global delay.
- **PLACEMENT: no spacing rule found.** `GameWorld.isValidPatternCenter` checks only that the
  5x5 box fits on the map (`x,y >= 2`, `x < width-2`, `y < height-2`) and that
  `areaIsPaintable` holds for all 25 tiles (each `isPaintable`, i.e. passable, over
  `translate(dx,dy)` for dx,dy in -2..2). Patterns therefore need **no ruin and no spacing** —
  only a clear 5x5 block.
- Still unchecked: whether `assertCanMarkResourcePattern` forbids overlapping an existing
  centre (`hasResourcePatternCenter(loc, team)` exists and is presumably used for this).
- **COST/BENEFIT, corrected**: a pattern costs **200 chips** and returns **+3 chips/turn**
  starting 50 rounds later, so break-even is ~67 rounds of income, ~117 rounds after the
  outlay. It is a CHIP investment, not a paint-to-chip converter.
- **This kills the headline rationale I first gave it.** I claimed patterns "convert the
  resource I hoard (paint) into the resource throttling me (chips)". They do the opposite:
  they spend chips, and unit building is already blocked by `money < CHIP_RESERVE` on 87% of
  sampled rounds. A pattern competes with a soldier at exactly the moment chips are scarcest.
- Still viable on a long game, and the marking paint (25) is cheap. But it must be
  pre-registered as a chip investment with a ~117-round payback, and the second catch stands:
  a pattern pays rent only while intact, and this bot's measured failure is *losing painted
  ground* (coverage ends below its own peak on 5 of 7 maps).
- `assertCanCompleteResourcePattern` also calls `hasResourcePatternCenter(loc, team)`, so
  there IS a centre-already-exists check on completion (none on marking).

### MOPPER `mopSwing` (unused through iteration 30) — drains ROBOTS, does NOT clear tiles

**Read the method body, not the constant names.** `InternalRobot.mopSwing` was disassembled
after I first recorded this wrongly here. Per tile in its arc it does:
`onTheMap` -> `GameWorld.getRobot(loc)` -> `isRobotType`/`getTeam` ->
`addPaint(-MOPPER_SWING_PAINT_DEPLETION)`. **No tile-paint write exists in the method.**

- `canMopSwing(dir)` / `mopSwing(dir)`; **cardinal directions only**; MOPPER only.
- Hits **6 tiles**, a **3-wide x 2-deep block in front**. (Corrected twice. The body builds
  **two** `int[4][6]` tables — `astore_2` = dx, `astore_3` = dy — indexed `[dir][k]` with the
  loop bound at 6, not one table of coordinate pairs. For NORTH: dx `{-1,0,1,-1,0,1}`,
  dy `{1,1,1,2,2,2}` -> `(-1,1)(0,1)(1,1)(-1,2)(0,2)(1,2)`. EAST/WEST swap the roles.)
- **It therefore out-ranges the mopper's own attack**: the far row sits at dist^2 = 4-5, while
  `MOPPER.actionRadiusSquared = 2`. The swing reaches tiles the single-target attack cannot.
- Removes `MOPPER_SWING_PAINT_DEPLETION = 5` from each **enemy ROBOT** standing there — so up
  to **30 paint** across a full 6-robot arc, against the single-target attack's 10 on one.
- Cooldown **20** (hard-coded `bipush 20`), vs the normal attack's `MOPPER.actionCooldown = 30`
  (verified: `attack` applies `getType().actionCooldown` unmodified). Mopper `attackCost = 0`,
  so both are free in paint.
- **It does NOT dominate the single-target attack**: single-target clears a *tile* to EMPTY
  and drains a robot; the swing only drains robots, three at a time. Different jobs.
- **The "I cannot take enemy ground" premise therefore STANDS**: a soldier cannot overwrite
  enemy paint and a mopper still clears only one tile. Iterations 28/29 and `alice_paintthief`
  do not rest on a false foundation.
- Live hypothesis: a paint drain on units is an accelerant on starvation, which causes
  **76-90%** of bob's deaths and 72-88% of mine. That is about killing units, not holding
  ground.

### MESSAGING (unused through iteration 29)

- `sendMessage` / `broadcastMessage` / `readMessages` / `canSendMessage` /
  `canBroadcastMessage`. Every unit acts on purely local information.

### Also unused, lower value but noted

`getNumberTowers()` (a direct read of expansion state — iteration 28 wanted exactly this and
used a chip-level proxy instead), `getChips`, `getHealth`, `getAllLocationsWithinRadiusSquared`,
`sensePassability`, `isLocationOccupied`, `onTheMap`, `disintegrate`, `setIndicatorDot/Line`,
`setTimelineMarker`, `getResourcePattern`, `getTowerPattern`, mark/removeMark.

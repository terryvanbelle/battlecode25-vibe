# BC25 "Chromatic Conflict" — Rules Digest (Carol)

Sources: official specs.pdf v3.1.0 (final) + engine source at github.com/battlecode/battlecode25
(GameConstants.java, UnitType.java, InternalRobot.java, GameWorld.java, RobotController.java).
Engine-verified facts marked [E].

## Objective & win conditions

- Win immediately by painting **>70% of paintable squares** (paintable = not wall, not ruin;
  [E] coverage denominator is `areaWithoutWalls`), or by **destroying every enemy unit**
  ([E] `DESTROY_ALL_UNITS` fires when a team's unit count hits 0 — towers count as units).
- Game ends at **round 2000**; tiebreakers in order: area painted → towers alive → money →
  sum of paint in units+towers → robots alive → coin flip ([E] `Math.random()`, the one
  nondeterminism — only in the final tiebreak).

## Map

- 20×20 … 60×60. Rotational or reflectional symmetry guaranteed. ≤20% walls.
- Ruins: 5×5 buildable zones, centers ≥ sqrt(25) apart, no walls in the 5×5. Each team starts
  with 2 towers (1 paint + 1 money, both **level 2**) sitting on ruins.
- Coordinates: (0,0) bottom-left, x→East, y→North.

## Resources

- **Chips (money)**: team-shared. Start 2500. Money towers mine 20/30/40 per turn (lv1/2/3).
  Defense towers earn 20/30/40 chips per attack that hits ≥1 robot (single + AoE each count once).
- **Paint**: per-unit stash. Towers hold ≤1000, start with 500 when built; paint towers
  generate 5/10/15 per turn *into the tower*. Robots spawn with a full stash.
- **SRP (special resource pattern)**: 5×5 paint pattern; complete costs 200 chips; must sit
  undisturbed 50 rounds to activate; each active SRP gives **+3 paint/turn to every paint tower
  AND +3 chips/turn to every money tower** [E: `extraResourcesFromPatterns` added in both
  branches of `processBeginningOfRound`]. SRPs can overlap-tile? No — shape chosen to prevent
  tiling; centers marked in MapInfo.isResourcePatternCenter().

### Paint drain (end of each robot turn) [E]

- On neutral tile: −1 (mopper −2). On enemy tile: −2 (mopper −4). On ally tile: 0.
- Clumping: −1 per adjacent (8-dir) ally robot; −2 per adjacent ally on enemy territory
  (mopper multiplier does NOT apply to the clumping term).
- At 0 paint at end of turn: −20 HP/turn, and cannot move/act (except disintegrate) until refilled.
- Low-paint cooldown: if stash < 50% full, cooldowns increased by (100 − 2·X)% where X = %full
  [E: applied via round() in addActionCooldownTurns/addMovementCooldownTurns, robots only].

## Robots (all: vision r²=20, move cooldown +10, cooldowns −10/turn, act when cooldown <10)

| | Soldier | Splasher | Mopper |
|---|---|---|---|
| HP | 250 | 150 | 50 |
| Paint capacity | 200 | 300 | 100 |
| Cost paint/chips | 200/250 | 300/400 | 100/300 |
| Attack cost | 5 paint | 50 paint | 0 |
| Action r² [E] | 9 | 4 | 2 |
| Action cooldown | +10 | +50 | +30 (swing +20, transfer +10) |

- **Soldier attack** [E]: if target holds an enemy *tower* → 50 dmg. Else paints the tile ONLY
  if empty or already own-team paint (cannot overwrite enemy paint; does nothing vs enemy robots).
- **Splasher attack** [E]: pick center within r²=4; every tile within r²=4 *of the center*:
  enemy towers take 100 dmg; empty/ally tiles painted; enemy paint overwritten only within
  r²=2 of center. Effective painting reach from splasher: up to r²≈16 (center 2 away + AoE 2).
  Only unit that can bulk-convert enemy paint.
- **Mopper attack** [E]: target within r²=2. Removes enemy paint on tile; if enemy *robot*
  there, steals 10 paint (−10 them, +5 mopper). Mop swing (cardinal): 2×3 block in that
  direction, −5 paint to each enemy robot (up to 6), cooldown +20, removes no floor paint.
  Mopper transfer: give/take paint with ally robots AND towers (withdraw = negative amount),
  r²=2, +10 cooldown. All robots can withdraw from towers; only moppers transfer robot→robot
  and refill towers.
- **No unit damages enemy robots' HP directly.** Robot attrition = tower fire + paint
  starvation. Paint denial is the combat mechanic.

## Towers (bytecode 20000; robots 17500)

| | Money lv1/2/3 | Paint lv1/2/3 | Defense lv1/2/3 |
|---|---|---|---|
| Build/upgrade chips | 1000/2500/5000 | same | same |
| HP | 1000/1500/2000 | 1000/1500/2000 | 2000/2500/3000 |
| Attack r² [E] | 9 | 9 | 16 |
| Single dmg | 20 | 20 | 40/50/60 |
| AoE dmg | 10 | 10 | 20/25/30 |
| Mining | 20/30/40 chips | 5/10/15 paint | 20/30/40 chips per hit-attack |

- Each turn a tower may make **one single-target AND one AoE attack** [E: separate flags].
  `attack(null)` = AoE over full action radius; `attack(loc)` = single target.
- Each live defense tower adds +5/+7/+9 to *all* allied towers' single-target damage
  (upgrade adds +2 each level [E]); no effect on AoE.
- Spawning: tower builds robot within r²=4 (spec text says 2 blocks, constant
  BUILD_ROBOT_RADIUS_SQUARED=4), costs robot's paint (from tower stash) + chips, +10 cooldown.
- Building a tower: paint the type's 5×5 pattern (primary/secondary mix) around a ruin, then
  `completeTowerPattern` with any robot within r²=2 of the ruin center. Built at level 1.
  Upgrade via `upgradeTower(loc)` within r²=2. **Max 25 towers/team.**
  `markTowerPattern` (25 paint) lays marks; marks optional — pattern match is on paint only.
  Tower pattern bit encoding [E]: bit = 5*(dx+2) + (dy+2); patterns: paint=18157905,
  money=15583086, defense=4685252, SRP=28873275. Runtime: rc.getTowerPattern()/getResourcePattern().
- Tower survives even if its pattern is later painted over. Towers occupy the ruin tile
  (impassable). Ruin visible only within vision radius.

## Communication [E]

- Message = 32-bit int + sender id + round. Buffer keeps 5 rounds.
- Robot↔tower only, within r²=20 AND connected by own-team paint path (walkable ally-paint
  chain). Robots send ≤1 msg/turn; towers ≤20/turn.
- Tower→tower `broadcastMessage`: r²=80, no paint connection needed, counts against the 20.
- Markers: per-tile ally-visible annotations (primary/secondary), mark/removeMark r²=2,
  1 paint, no cooldown. Marks pruned only by ally overwrite/erase.

## Radii cheat-sheet (asymmetries to exploit)

- Vision r²=20 (~4.47) for everything, including towers.
- Defense tower attack r²=16 (4.0) < vision 20: robots can see a defense tower from r²∈(16,20]
  and stay safe; paint/money towers only reach r²=9.
- Soldier attacks towers from r²=9 = paint/money tower reach → soldier trades 50 dmg/2 turns
  vs tower's 20+10; 3 soldiers kill a lv1 tower before it kills one soldier. vs Defense tower
  (r²16 > soldier 9) soldiers eat fire on approach.
- Splasher hits towers from up to r²=16 center distance? No — center must be within r²=4 of
  splasher, tower within r²=4 of center → max tower distance ~r²=16 (e.g. 2+2 straight = 4
  tiles → r²=16). So splashers CAN out-range paint/money towers (r²=9) and match defense (16).
- Message r²=20 = vision; broadcast r²=80 (~8.9) links towers ≥2 ruin-spacings apart.

## Turn structure [E]

- Round: each robot takes a full turn in sequence (order: age then ID — `compareTo`), cooldowns
  −10 at own-turn start, paint mining at processBeginningOfRound (towers), paint penalties &
  0-paint damage at end of each robot's own turn.
- Bytecode overrun: turn silently pauses mid-instruction, resumes next turn. Exceptions cost
  500 bytecode. Determinism guaranteed except final random tiebreak.
- Team execution time limit: 1200s per team per match (wall-clock ns aggregate).

## Bot-relevant API notes

- `senseNearbyMapInfos()` returns MapInfo (paint, mark, ruin, wall, passable, SRP center).
- `senseNearbyRuins(r²)`, `getAllLocationsWithinRadiusSquared`, `canPaint`, `canAttack`.
- `getNumberTowers()`, `getChips()`/`getMoney()`, `getPaint()` (own stash).
- `disintegrate()` — could recycle a stuck 0-paint robot (unit count → careful re: destroy-all).
- Indicator strings ≤256 chars; `setTimelineMarker` for round labels.

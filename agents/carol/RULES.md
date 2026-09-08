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

## HARD LOSS CONDITION: no paint tower = unrecoverable [E, verified by disassembly]

**A team holding no paint tower, whose robots hold no paint, has already lost.** There is no
recovery path in the rules. The chain, each link read out of the engine rather than inferred:

1. `InternalRobot.processBeginningOfRound` gates paint income on the tower's OWN type:
   `if (type.paintPerTurn != 0) addPaint(type.paintPerTurn + 3*numSRPs)`.
2. A money tower has `paintPerTurn == 0`, so it gains paint from **nothing** — not mining, and
   **not from SRPs either**, because the SRP bonus sits inside that same guard.
3. A robot's build cost in paint is drawn from the **building tower's stash**, so a team whose
   towers are all dry cannot `buildRobot` at all, at any chip total.
4. No robot means no ruin can be painted, so no new tower — paint or money — can ever be built.

Observed: on Dominoes carol's starting paint tower died ~r200; she then held one dry money
tower for 1,800 rounds while chips climbed to **60,000 unspendable**, taking 29 soldier actions
in the whole game. It costs the accepted baseline 2 of 40 games vs `carol_rush`.

Consequences for design: the paint-tower count is a survival variable, not an economic one;
`NUMBER_INITIAL_PAINT_TOWERS = 1` means every game starts one death away from this state; and
chips are worthless the instant it happens, so any "spend the surplus" logic must not be what
you rely on to escape.

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
- **`transferPaint` range is r²≤2 for EVERY unit type, NOT the unit's action radius**
  [E, iteration 38]. `assertCanTransferPaint` calls `assertCanActLocation(loc, 2)` with a
  **hardcoded literal 2**; the action-radius column above (soldier 9, splasher 4, mopper 2)
  governs *attacks* only. So a soldier can attack a tower from r²=9 but must stand within
  r²=2 — the 8 surrounding tiles — to draw paint from one. **A unit can never top up in
  passing; it must physically walk to touch a tower.** Worth stating loudly because the
  mismatch between `senseNearbyRobots(2, ...)` in a refill helper and a soldier's r²=9 looks
  exactly like this lineage's most productive bug class (a gate narrower than its mechanism,
  which iterations 30/35/36 all were) and is not one. The remaining preconditions are
  `assertIsActionReady`, a robot present, not self, non-zero amount, same team, the *caller*
  not a tower ("Towers cannot transfer paint!"), withdrawal only from towers ("Paint can only
  be withdrawn from towers!"), giving to a non-tower ally only as a mopper, and both stashes
  sufficient.
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

## Provenance of every [E] fact in this file (added iteration 42)

battlecode-dev's gradle cache holds **both** `battlecode25-java-1.0.0.jar` and
`battlecode25-java-3.1.0.jar`, so any probe that locates the engine with
`find ... -name 'battlecode25*.jar' | head -1` can decompile the WRONG engine and produce a
confident, plausible, false constant. A missing method announces itself; a changed constant does
not.

**Derive engine facts only through `tools/engine-jar.sh`**, which resolves the version from
`arena/engine_version.txt` and refuses to print a mismatched path:

```
javap -p -c -cp "$(tools/engine-jar.sh)" battlecode.common.RobotController
```

My own probe used `find ... | sort -V | tail -1`, which takes the HIGHEST version and therefore
happened to resolve 3.1.0 correctly — but that was the luck of an ordering flag, not a check.
**Re-verified against the resolver-approved 3.1.0 jar on 2026-09-08**, all identical to what this
file already claimed:

- SRP: `COMPLETE_RESOURCE_PATTERN_COST=200`, `EXTRA_RESOURCES_FROM_PATTERN=3`,
  `RESOURCE_PATTERN_ACTIVE_DELAY=50`, `RESOURCE_PATTERN_RADIUS_SQUARED=8`,
  `MARK_PATTERN_PAINT_COST=25`, `PATTERN_SIZE=5`, `RESOURCE_PATTERN=28873275`.
- Comms/vision: `MESSAGE_RADIUS_SQUARED=20`, `BROADCAST_RADIUS_SQUARED=80`,
  `VISION_RADIUS_SQUARED=20`, `MAX_MESSAGES_SENT_ROBOT=1`, `MAX_MESSAGES_SENT_TOWER=20`,
  `MESSAGE_ROUND_DURATION=5`, `MAX_MESSAGE_BYTES=4`.

The Communication section below predates this session and had **no recorded provenance**; it is
now confirmed on 3.1.0. Anything added here in future must name how it was derived, because later
nobody can distinguish a fact that came from the right jar from one that did not.

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

## Pattern shapes (decoded from constants; X=secondary, .=primary; y up)

```
SRP      PAINT    MONEY    DEFENSE
XX.XX    X...X    .XXX.    ..X..
X...X    .X.X.    XX.XX    .XXX.
..X..    ..X..    X...X    XXXXX
X...X    .X.X.    XX.XX    .XXX.
XX.XX    X...X    .XXX.    ..X..
```
(center tile of tower patterns is the ruin — unpaintable; SRP center must be painted
and is its marked center. 24 paintable tiles per tower pattern, 25 for SRP.)

## Engine probes — exploitable details (from RobotControllerImpl.java) [E]

1. **Tower attacks are FREE.** `assertCanAttackTower` checks only the per-turn
   `hasTowerSingleAttacked`/`hasTowerAreaAttacked` flags — no `assertIsActionReady`, and
   `towerAttack` never adds action cooldown. A tower can single-attack, AoE-attack, AND
   build a robot in the same turn. Never gate tower attacks on `isActionReady()`.
2. `canAttack` for a soldier is TRUE on ally-painted tiles ("paint type is irrelevant for
   checking attack validity"). Repainting own paint silently wastes 5 paint + a turn.
   Check `MapInfo.getPaint()` yourself. `canPaint(loc)` does check paintability (wall/ruin).
3. `completeTowerPattern` additionally requires: no robot standing on the ruin center,
   team has the tower's moneyCost (1000 chips) in chips, team tower count < 25.
   A soldier that walks onto the ruin center blocks its own completion.
4. `buildRobot` requires paint from the TOWER's own stash (not team-wide) + team chips,
   target within r2=4, unoccupied and passable.
5. `upgradeTower` costs the NEXT level's moneyCost (2500 for lv2, 5000 for lv3), r2=2.
6. Mopper `attack` requires `isPassable(loc)` — cannot mop tiles with walls or ruins.
7. Mark/complete resource pattern radius is r2=8 (reach the whole 5x5 from the center-ish).
8. `getMoney()` is team-wide and shared; paint is strictly per-unit.

**Economic consequence**: paint is the binding resource. A lv2 paint tower makes 10
paint/turn; a soldier costs 200 paint to build and 5 paint per tile painted. Money towers
generate no paint, so a money tower can spawn ~2 robots from its 500 starting stash and
then goes dry until a mopper refills it. Each active SRP adds **+3 paint/turn to every PAINT
tower and +3 chips/turn to every MONEY tower** -- NOT +3 paint to both. The paint half sits
inside the `type.paintPerTurn != 0` guard, so a money tower gets no paint from an SRP at all
[E, and see the HARD LOSS section above, which turns on exactly this]. An earlier wording here
said "+3/turn to EVERY paint tower and EVERY money tower", which read as paint to both and
contradicted that section; corrected at iteration 40.

**Chips are not inert, and this is the trap iteration 40 fell into.** It is tempting to
summarise the above as "chips accumulate uselessly", and then to treat converting paint income
into chips as a trade of a useful resource for a harmless one. It is not. Chips clear the
soldier/splasher build gates, and **a robot's build cost is 200 paint drawn from the building
tower's own stash**. So chips convert straight back into demand on the paint account. Any
change that buys chips with paint income is charged twice: once for the income forgone, and
again when the chips are spent. Price both halves before proposing one.

## Pattern completion is exact [E: GameWorld.checkPattern]

Every one of the 24 non-centre tiles of a tower pattern (25 for an SRP, which has no
exempt centre) must hold exactly the right paint: **secondary where the bit is 1,
PRIMARY where it is 0**. Empty is not acceptable for a 0 bit. Consequences:

- Building a tower costs ~24 x 5 = 120 paint of soldier attacks plus 1000 chips.
- A single enemy-painted tile inside the 5x5 denies the ruin. Mopping it back to EMPTY
  does **not** restore the pattern — the tile must be repainted primary. So cheap
  pattern-denial is a real offensive option (one soldier attack blocks a whole tower),
  and defending our own ruins means repainting, not just mopping.
- SRPs must additionally stay exact for 50 consecutive rounds before paying out.

## Coverage economics (derived; drives unit mix)

Win condition is painted area, so the right unit metric is **tiles painted per turn** and
**paint per tile**.

| | tiles per attack | paint per attack | paint/tile | cooldown | tiles/turn (sustained) |
|---|---|---|---|---|---|
| Soldier | 1 | 5 | 5.0 | 10 (1 turn) | 1.00 |
| Splasher | up to 13 (r2<=4 disc) | 50 | 3.85 | 50 (5 turns) | up to 2.60 |

The r2<=4 disc is 13 tiles: (0,0), 4 orthogonal, 4 diagonal, 4 at distance 2.
So on virgin ground a splasher paints **2.6x faster per unit and 23% cheaper per tile**
than a soldier, and it is the ONLY unit that converts enemy paint in bulk (within r2<=2
of its centre). Its costs are 300 paint / 400 chips vs the soldier's 200 / 250.

Caveats: a splasher wastes paint on already-painted tiles inside the disc, so it is worth
much more on the frontier than inside owned territory, and it cannot paint tower/SRP
patterns precisely (it cannot choose per-tile colours). Soldiers remain necessary for
patterns and for chipping towers (50 dmg).

**Resource binding order observed in carol's own traces**: with all-money towers, paint
binds (10/turn team-wide, 213k idle chips). With all-paint towers plus a chip reserve,
chips bind (treasury pins at the reserve; ~30 chips/turn from the one starting lv2 money
tower funds roughly one soldier per 8 rounds). A mixed build is therefore likely optimal
once coverage throughput, not income, stops being the bottleneck.

## Engine probe — `GameWorld.markPattern` (added 2026-09-06, iteration 6)

Decompiled: `markPattern` loops `dx = -2..2`, `dy = -2..2` over **all 25 tiles including the
centre**, and calls `setMarker(team, centre.translate(dx, dy), getPatternBit(pattern,dx,dy) + 1)`.
Consequences relied on by carol's self-calibrating tower mix:

- **Every tile of a marked pattern carries a marker, primary as well as secondary** (marker
  value 1 = primary for a 0 bit, 2 = secondary for a 1 bit). So "is this ruin marked?" can be
  answered from any tile of the 5x5, not only the secondary ones.
- **The centre is marked too**, even though it is the unpaintable ruin tile.
- **No rotation or reflection is applied** — `dx,dy` are used directly, so patterns are
  axis-aligned and identical for both teams.
- Therefore the *type* of a marked tower pattern is recoverable from one `senseMapInfo`: the
  PAINT and MONEY patterns differ at 16 of the 24 non-centre tiles, and offset **(-2,-1)** is
  secondary in MONEY and primary in PAINT.

```
PAINT      MONEY      DEFENSE    SRP
X...X      .XXX.      ..X..      XX.XX
.X.X.      XX.XX      .XXX.      X...X
..X..      X...X      XXXXX      ..X..
.X.X.      XX.XX      .XXX.      X...X
X...X      .XXX.      ..X..      XX.XX
```
(rendered from the constants paint=18157905, money=15583086, defense=4685252, srp=28873275
with bit = 5*(dx+2) + (dy+2), y increasing upward — matches the spec's diagrams.)

## Engine probe — SRP completion preconditions, and marks are provably irrelevant [E, iteration 32]

Disassembled `GameWorld.checkPattern`, `GameWorld.isValidPatternCenter` and
`RobotControllerImpl.assertCanCompleteResourcePattern` (engine 3.1.0). Three facts, each read out
of the bytecode rather than inferred from behaviour:

1. **`checkPattern(pattern, team, centre, skipCentre)` reads PAINT ONLY.** Its whole body is
   `getPrimaryPaint(team)` / `getSecondaryPaint(team)` compared against
   `getPaint(centre.translate(dx,dy))` for dx,dy in −2..2, versus `getPatternBit(pattern,dx,dy)`.
   **There is no marker lookup anywhere in it.** So `markResourcePattern`/`markTowerPattern` are
   purely a convenience for the *bot* (they let you read the required colour back off the tile via
   `getMark()`); paying their 25 paint is never required to complete a pattern. `checkTowerPattern`
   passes `skipCentre = true` (the ruin tile is exempt); the resource variant does not, so an SRP
   needs all **25** tiles exact.

2. **`isValidPatternCenter(loc)` is exactly two conditions**: a 2-tile margin
   (`x >= 2 && y >= 2 && x < width−2 && y < height−2`) and `areaIsPaintable(loc)`, which requires
   `isPaintable` on all 25 tiles of the 5×5 — so a single wall **or ruin** anywhere in the block
   disqualifies the centre outright.

3. **`assertCanCompleteResourcePattern` additionally requires**: a robot type (not a tower),
   the centre within action range, team money ≥ the SRP cost, and
   `!hasResourcePatternCenter(loc, team)` — you cannot re-complete one already active.

**Consequence worth carrying forward.** Fact 2 means "can an SRP go here?" is a *static* property
of the map, decidable with no game running. `carol-tools/latticescan/` computes it over the
official 75-map corpus and gets **29.4% of 5-stride lattice cells viable** (median 25%/map, min
4.0%, max 63.6%, no map at zero) — and because the predicate is the engine's own, that number is
exact rather than a model of it. Anyone re-opening the SRP direction should start from there
instead of buying games to discover it.

## Messaging (BC25) — read off `battlecode.world.RobotControllerImpl`, not assumed

Found by the Phase 0 API sweep at iteration 37: carol had never called any of these in 37
iterations. Constants from `GameConstants`, preconditions disassembled from the engine jar
(`javap -p -c battlecode.world.RobotControllerImpl`).

| constant | value |
|---|---|
| `MAX_MESSAGE_BYTES` | 4 (a full 32-bit int payload; a MapLocation needs 12 bits) |
| `MESSAGE_RADIUS_SQUARED` | 20 (robot -> tower), same as a unit's vision |
| `BROADCAST_RADIUS_SQUARED` | 80 (tower -> robots), **4x the area of a unit's vision disc** |
| `MESSAGE_ROUND_DURATION` | 5 rounds |
| `MAX_MESSAGES_SENT_ROBOT` | 1 per round |
| `MAX_MESSAGES_SENT_TOWER` | 20 per round |

**`sendMessage(MapLocation, int)` — `assertCanSendMessage` enforces, in the engine's own words:**

- `"Only (robot <-> tower) communication is allowed!"` — **there is no robot-to-robot channel.**
- `"Location specified is not connected to current location by paint!"` (`GameWorld.connectedByPaint`)
- `"Location specified is not within the message radius!"` (r2=20)
- `"Robot has already sent too many messages this round!"` / the tower equivalent
- `"Cannot send messages to robots of the enemy team!"`

**`broadcastMessage(int)` — `assertCanBroadcastMessage` enforces ONLY:**

- `"Only towers can broadcast messages"`
- `"Tower has already sent too many messages this round!"`

and the body then calls `getAllLocationsWithinRadiusSquared` (r2=80) and delivers to every ally
robot found there.

### The asymmetry, which is the whole design constraint

> **The uplink is gated on paint connectivity. The downlink is not.**

A tower broadcasts to everything within r2=80 **regardless of paint**, 20 messages a round. But a
robot can only report back to a tower if it stands on a contiguous path of its own team's paint
back to that tower — and a soldier out exploring unpainted ground is, by definition, exactly the
robot that is *not* connected.

**This kills the obvious design before it costs a run.** "A soldier that finds a distant unclaimed
ruin tells a tower, which broadcasts it to the team" is infeasible: the discovering soldier is off
the painted network precisely when it has something new to report. Any messaging iteration in this
lineage must be built on the **downlink**, which is unconditional, and must not assume the uplink.

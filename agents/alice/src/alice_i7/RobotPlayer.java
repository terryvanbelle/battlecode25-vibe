package alice_i7;

import battlecode.common.*;

/**
 * Alice iteration 0: minimal instrumented bot.
 * - bytecode monitoring wired in (overrun + near-miss surfaced in indicator strings)
 * - soldiers: complete ruin tower patterns, paint own tile, wander
 * - moppers: mop enemy paint, wander
 * - towers: spawn soldiers/moppers, attack (single + AoE)
 */
public class RobotPlayer {
    static final Direction[] directions = {
        Direction.NORTH, Direction.NORTHEAST, Direction.EAST, Direction.SOUTHEAST,
        Direction.SOUTH, Direction.SOUTHWEST, Direction.WEST, Direction.NORTHWEST,
    };

    // --- instrumentation ---
    static int overruns = 0;       // confirmed bytecode overruns (round advanced mid-logic)
    static int nearMisses = 0;     // ended turn within 15% of the limit
    static int maxBc = 0;          // worst bytecode usage seen

    // --- state ---
    static int rngState;           // xorshift PRNG state (seeded from ID)
    static Direction wanderDir = null;
    static int wanderSteps = 0;

    static int rnd(int n) {        // cheap deterministic per-robot PRNG
        rngState ^= rngState << 13;
        rngState ^= rngState >>> 17;
        rngState ^= rngState << 5;
        int r = rngState % n;
        return r < 0 ? r + n : r;
    }

    @SuppressWarnings("unused")
    public static void run(RobotController rc) throws GameActionException {
        rngState = rc.getID() * 31 + 17;
        final int limit = rc.getType().isRobotType()
                ? GameConstants.ROBOT_BYTECODE_LIMIT : GameConstants.TOWER_BYTECODE_LIMIT;
        while (true) {
            int startRound = rc.getRoundNum();
            try {
                switch (rc.getType()) {
                    case SOLDIER: runSoldier(rc); break;
                    case MOPPER: runMopper(rc); break;
                    case SPLASHER: runSplasher(rc); break;
                    default: runTower(rc); break;
                }
            } catch (GameActionException e) {
                // illegal action; keep going
            } catch (Exception e) {
                // real bug; keep robot alive
            } finally {
                int bc = Clock.getBytecodeNum();
                if (bc > maxBc) maxBc = bc;
                if (rc.getRoundNum() > startRound) overruns++;
                else if (bc > limit - limit / 7) nearMisses++;
                rc.setIndicatorString("bc=" + bc + " max=" + maxBc
                        + (overruns > 0 ? " OVR=" + overruns : "")
                        + (nearMisses > 0 ? " near=" + nearMisses : ""));
                Clock.yield();
            }
        }
    }

    // ------------------------------------------------------------------ tower
    /** Chips held back so a 1000-chip tower completion can always fund (iteration 2). */
    static final int CHIP_RESERVE = 1450;


    static void runTower(RobotController rc) throws GameActionException {
        // Iteration 4: spend idle chips upgrading myself. Chips have not been the
        // binding resource since iteration 2 ($120,840 unspent at r2000 on
        // DefaultLarge) while PAINT bounds everything: a soldier's entire output
        // is the 200 paint it was born with. Upgrading raises paint income
        // 5->10->15/turn (money 20->30->40) permanently.
        // Engine-verified: assertCanUpgradeTower only checks range + on-map, and
        // upgradeTower adds no cooldown, so a tower upgrading ITSELF (distance 0)
        // costs chips and nothing else -- no action, no turn, no cooldown.
        UnitType nextLevel = rc.getType().getNextLevel();
        if (nextLevel != null && rc.getMoney() >= nextLevel.moneyCost + CHIP_RESERVE
                && rc.canUpgradeTower(rc.getLocation())) {
            rc.upgradeTower(rc.getLocation());
        }
        // Attack: single-target the lowest-HP enemy robot in range, then AoE if any enemy near.
        RobotInfo[] enemies = rc.senseNearbyRobots(rc.getType().actionRadiusSquared, rc.getTeam().opponent());
        if (enemies.length > 0) {
            RobotInfo best = null;
            for (RobotInfo e : enemies) {
                if (best == null || e.getHealth() < best.getHealth()) best = e;
            }
            if (best != null && rc.canAttack(best.getLocation())) rc.attack(best.getLocation());
            if (rc.canAttack(null)) rc.attack(null); // AoE
        }

        // Spawn: mostly soldiers, some moppers. Keep a chip reserve so 1000-chip
        // tower completions can always fund (spawning greedily at 250/unit pins
        // money near zero and stalls tower expansion permanently).
        if (rc.getMoney() >= CHIP_RESERVE) {
            UnitType want = (rnd(4) == 0) ? UnitType.MOPPER : UnitType.SOLDIER;
            // Iteration 5: reserve tower PAINT for soldiers. Measured defect --
            // a mopper costs 100 tower paint, a soldier 200, and a tower's paint
            // income is only 5-15/turn, so the tower can fund a mopper twice as
            // often and never accumulates the 200 a soldier needs. The realized
            // army mix is therefore ~90% moppers, not the 25% this line reads as
            // (Racetrack r1750-2000: +9 soldiers vs +93 moppers). Moppers cannot
            // paint, and painted area is the win condition. Worse, the drain is an
            // ABSORBING STATE: once tower paint reaches 0 only the 100-paint mopper
            // is affordable, moppers complete no tower patterns, so paint income
            // never recovers (Mirage: dead at r200, coverage 132 -> 15 per-mille).
            // The threshold is SOLDIER.paintCost rather than a tuned constant --
            // "only build a mopper if a soldier was affordable too". Doses 50 and
            // 100 were statistically tied (they disagreed on 3 of 27 shared cells),
            // so this picks the self-calibrating form over the searched one.
            // Refusing the mopper here does NOT substitute a cheaper unit: the
            // build below simply fails and the paint accumulates until a soldier
            // is affordable, which is the intent.
            if (want == UnitType.MOPPER && rc.getPaint() < UnitType.SOLDIER.paintCost) {
                want = UnitType.SOLDIER;
            }
            int off = rnd(8);
            for (int i = 0; i < 8; i++) {
                MapLocation loc = rc.getLocation().add(directions[(i + off) % 8]);
                if (rc.canBuildRobot(want, loc)) { rc.buildRobot(want, loc); break; }
            }
        }
    }

    // ---------------------------------------------------------------- soldier
    static void runSoldier(RobotController rc) throws GameActionException {
        // Find a nearby ruin without a tower and try to complete a pattern there.
        MapLocation ruin = null;
        MapLocation[] ruins = rc.senseNearbyRuins(-1);
        MapLocation me = rc.getLocation();
        int bestD = 1 << 30;
        for (MapLocation r : ruins) {
            if (rc.canSenseRobotAtLocation(r)) continue; // tower already there
            int d = me.distanceSquaredTo(r);
            if (d < bestD) { bestD = d; ruin = r; }
        }

        if (ruin != null) {
            Direction toRuin = me.directionTo(ruin);
            tryMove(rc, toRuin);
            me = rc.getLocation();
            // Mark the pattern if not already marked. Tower type by ruin-position
            // parity: ~50/50 money/paint mix, decided by the map (identical for
            // both teams), immune to the money-at-mark-time timing artifact that
            // made every early mark a money tower.
            UnitType wantTower = ((ruin.x + ruin.y) & 1) == 0
                    ? UnitType.LEVEL_ONE_MONEY_TOWER : UnitType.LEVEL_ONE_PAINT_TOWER;
            MapLocation markCheck = ruin.subtract(toRuin);
            if (rc.canSenseLocation(markCheck)
                    && rc.senseMapInfo(markCheck).getMark() == PaintType.EMPTY
                    && rc.canMarkTowerPattern(wantTower, ruin)) {
                rc.markTowerPattern(wantTower, ruin);
            }
            // Paint marked tiles that don't match yet.
            for (MapInfo t : rc.senseNearbyMapInfos(ruin, 8)) {
                PaintType mark = t.getMark();
                if (mark != PaintType.EMPTY && mark != t.getPaint()) {
                    if (rc.canAttack(t.getMapLocation())) {
                        rc.attack(t.getMapLocation(), mark == PaintType.ALLY_SECONDARY);
                        break;
                    }
                }
            }
            // Complete whichever pattern is actually painted (the mark decided it).
            if (rc.canCompleteTowerPattern(UnitType.LEVEL_ONE_PAINT_TOWER, ruin)) {
                rc.completeTowerPattern(UnitType.LEVEL_ONE_PAINT_TOWER, ruin);
            } else if (rc.canCompleteTowerPattern(UnitType.LEVEL_ONE_MONEY_TOWER, ruin)) {
                rc.completeTowerPattern(UnitType.LEVEL_ONE_MONEY_TOWER, ruin);
            }
        } else {
            wander(rc);
        }

        // Paint the tile under us if it isn't ours yet (avoids paint penalty).
        MapLocation cur = rc.getLocation();
        MapInfo here = rc.senseMapInfo(cur);
        if (!here.getPaint().isAlly() && rc.canAttack(cur)) {
            rc.attack(cur);
        }
        // Otherwise spend the idle action painting the nearest empty tile in range.
        if (rc.isActionReady() && rc.getPaint() >= 15) {
            MapLocation paintTarget = null;
            int paintD = 1 << 30;
            for (MapInfo t : rc.senseNearbyMapInfos(9)) {
                if (t.getPaint() == PaintType.EMPTY && t.isPassable()) {
                    int d = cur.distanceSquaredTo(t.getMapLocation());
                    if (d < paintD && rc.canAttack(t.getMapLocation())) {
                        paintD = d;
                        paintTarget = t.getMapLocation();
                    }
                }
            }
            if (paintTarget != null) rc.attack(paintTarget);
        }
    }

    // --------------------------------------------------------------- splasher
    static void runSplasher(RobotController rc) throws GameActionException {
        // Iteration 0: splashers are never built; behave like a wanderer that splashes
        // when enough enemy paint or a tower is in reach.
        if (rc.isActionReady() && rc.getPaint() >= 60) {
            MapLocation best = null;
            int bestScore = 3; // require at least a few tiles worth
            for (MapInfo t : rc.senseNearbyMapInfos(rc.getType().actionRadiusSquared)) {
                MapLocation c = t.getMapLocation();
                if (!rc.canAttack(c)) continue;
                int score = 0;
                if (t.getPaint().isEnemy()) score += 2;
                else if (t.getPaint() == PaintType.EMPTY && t.isPassable()) score++;
                if (score > bestScore) { bestScore = score; best = c; }
            }
            if (best != null) rc.attack(best);
        }
        wander(rc);
    }

    // ----------------------------------------------------------------- mopper
    static void runMopper(RobotController rc) throws GameActionException {
        // Mop adjacent enemy paint (prefer tiles with enemy robots on them).
        if (rc.isActionReady()) {
            MapLocation best = null;
            for (MapInfo t : rc.senseNearbyMapInfos(2)) {
                if (t.getPaint().isEnemy() && rc.canAttack(t.getMapLocation())) {
                    best = t.getMapLocation();
                    if (rc.canSenseRobotAtLocation(best)) break; // robot on it: steal paint
                }
            }
            if (best != null) rc.attack(best);
        }
        // Iteration 7: walk toward the nearest enemy paint ANYWHERE in vision
        // instead of wandering. The mopper picks targets within r^2<=2 -- the 8
        // adjacent tiles -- while its vision is r^2=20, roughly 60 tiles: it has
        // been blind to ~90% of what it can see. Motivated by the starburst trace,
        // where iteration 5 painted ~2x the baseline and still lost both sides
        // because the baseline erased ~2x as much.
        MapLocation me = rc.getLocation();
        MapLocation target = null;
        int bd = 1 << 30;
        for (MapInfo t : rc.senseNearbyMapInfos(-1)) {
            if (!t.getPaint().isEnemy()) continue;
            int d = me.distanceSquaredTo(t.getMapLocation());
            if (d < bd) { bd = d; target = t.getMapLocation(); }
        }
        if (target == null) wander(rc);
        else if (bd > 2) tryMove(rc, me.directionTo(target));
        // bd <= 2: already in mopping range, hold position and keep mopping.
    }

    // ------------------------------------------------------------------ moves
    static void wander(RobotController rc) throws GameActionException {
        if (!rc.isMovementReady()) return;
        if (wanderDir == null || wanderSteps <= 0) {
            wanderDir = directions[rnd(8)];
            wanderSteps = 5 + rnd(8);
        }
        if (rc.canMove(wanderDir)) {
            rc.move(wanderDir);
            wanderSteps--;
        } else {
            wanderDir = directions[rnd(8)];
            wanderSteps = 5 + rnd(8);
            if (rc.canMove(wanderDir)) { rc.move(wanderDir); wanderSteps--; }
        }
    }

    /** Move toward dir with simple slide fallback. */
    static void tryMove(RobotController rc, Direction dir) throws GameActionException {
        if (!rc.isMovementReady() || dir == Direction.CENTER) return;
        if (rc.canMove(dir)) { rc.move(dir); return; }
        Direction l = dir.rotateLeft(), r = dir.rotateRight();
        // Randomize tie-break order to avoid systematic side bias.
        if (rnd(2) == 0) { Direction t = l; l = r; r = t; }
        if (rc.canMove(l)) { rc.move(l); return; }
        if (rc.canMove(r)) { rc.move(r); return; }
    }
}

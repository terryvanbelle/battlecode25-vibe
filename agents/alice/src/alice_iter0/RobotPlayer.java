package alice_iter0;

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
    static void runTower(RobotController rc) throws GameActionException {
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

        // Spawn: mostly soldiers, some moppers.
        UnitType want = (rnd(4) == 0) ? UnitType.MOPPER : UnitType.SOLDIER;
        int off = rnd(8);
        for (int i = 0; i < 8; i++) {
            MapLocation loc = rc.getLocation().add(directions[(i + off) % 8]);
            if (rc.canBuildRobot(want, loc)) { rc.buildRobot(want, loc); break; }
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
            // Mark the pattern if not already marked.
            MapLocation markCheck = ruin.subtract(toRuin);
            if (rc.canSenseLocation(markCheck)
                    && rc.senseMapInfo(markCheck).getMark() == PaintType.EMPTY
                    && rc.canMarkTowerPattern(UnitType.LEVEL_ONE_MONEY_TOWER, ruin)) {
                rc.markTowerPattern(UnitType.LEVEL_ONE_MONEY_TOWER, ruin);
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
            if (rc.canCompleteTowerPattern(UnitType.LEVEL_ONE_MONEY_TOWER, ruin)) {
                rc.completeTowerPattern(UnitType.LEVEL_ONE_MONEY_TOWER, ruin);
            }
        } else {
            wander(rc);
        }

        // Paint the tile under us if it isn't ours yet.
        MapInfo here = rc.senseMapInfo(rc.getLocation());
        if (!here.getPaint().isAlly() && rc.canAttack(rc.getLocation())) {
            rc.attack(rc.getLocation());
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
        wander(rc);
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

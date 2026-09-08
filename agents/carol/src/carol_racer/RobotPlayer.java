package carol_racer;

import battlecode.common.*;
import java.util.Random;

/**
 * carol_racer -- a SYNTHETIC ARCHETYPE, not an iteration. It never changes, which is the whole
 * point: it exists to restore resolution to the frozen-roster instrument, which has saturated at
 * 94-100% against every member (see TRAINING_LOG, "the frozen roster has SATURATED").
 *
 * It is deliberately built around the one thing the TOURNAMENT reports carol losing: the coverage
 * race. 76.2% of tournament games end with "the winning team painted enough of the map", and the
 * head-to-head has carol behind on exactly that. So this archetype maximises painted area and does
 * almost nothing else -- no chip reserve, no economy tuning, no mopper, no tower upgrades, and no
 * defensive play at all. That single-mindedness is what makes it a useful yardstick rather than a
 * rival: it stresses one axis hard, and it cannot drift, because nobody will ever tune it.
 *
 * It is NOT and must never be a BC25 finals benchmark bot. Those are a yardstick and never an
 * opponent, and AGENT.md names roster_extra.txt as the specific trap. This is written from
 * scratch, from the public spec and this lineage's own RULES.md.
 *
 * Design, and the reasoning is all from RULES.md's coverage economics table:
 *  - Splashers paint up to 13 tiles for 50 paint (3.85 paint/tile, 2.6 tiles/turn sustained)
 *    against a soldier's 1 tile for 5 (5.0 paint/tile, 1.0 tiles/turn). So splashers are the
 *    coverage unit and this bot buys them whenever it can.
 *  - Splashers cannot paint patterns (no per-tile colour choice), so soldiers still build towers.
 *  - Every ruin becomes a PAINT tower: paint is the binding resource for a bot that never stops
 *    painting, and money towers generate no paint at all.
 */
public class RobotPlayer {
    static RobotController rc;
    static Random rng;
    static MapLocation explore = null;
    static int exploreAge = 0;

    static final Direction[] DIRS = {
        Direction.NORTH, Direction.NORTHEAST, Direction.EAST, Direction.SOUTHEAST,
        Direction.SOUTH, Direction.SOUTHWEST, Direction.WEST, Direction.NORTHWEST };

    public static void run(RobotController rc_) throws GameActionException {
        rc = rc_;
        rng = new Random(rc.getID());
        while (true) {
            try {
                if (rc.getType().isTowerType()) runTower(); else runRobot();
            } catch (Exception e) {
                // A yardstick that crashes measures nothing. Swallow and keep playing.
            }
            Clock.yield();
        }
    }

    static void runTower() throws GameActionException {
        // Tower attacks are free: no action cooldown, and single + AoE are separate flags.
        for (RobotInfo e : rc.senseNearbyRobots(-1, rc.getTeam().opponent())) {
            if (rc.canAttack(e.location)) { rc.attack(e.location); break; }
        }
        if (rc.senseNearbyRobots(-1, rc.getTeam().opponent()).length > 0 && rc.isActionReady())
            rc.attack(null);                              // AoE; guarded the way carol guards it

        // Splasher first -- the coverage unit. Soldier as the fallback, because patterns and
        // tower-chipping both need one and a splasher can do neither.
        UnitType want = UnitType.SPLASHER;
        if (rc.getChips() < UnitType.SPLASHER.moneyCost
                || rc.getPaint() < UnitType.SPLASHER.paintCost) want = UnitType.SOLDIER;
        for (int i = 0; i < 8; i++) {
            MapLocation l = rc.getLocation().add(DIRS[(i + rng.nextInt(8)) % 8]);
            if (rc.canBuildRobot(want, l)) { rc.buildRobot(want, l); return; }
        }
    }

    static void runRobot() throws GameActionException {
        UnitType t = rc.getType();
        refill();
        if (t == UnitType.SOLDIER) buildTowerOnRuin();
        move();
        if (!rc.isActionReady()) return;
        if (t == UnitType.SPLASHER) splash(); else paint();
    }

    static void refill() throws GameActionException {
        if (rc.getPaint() >= rc.getType().paintCapacity / 2) return;
        for (RobotInfo a : rc.senseNearbyRobots(2, rc.getTeam())) {
            if (!a.type.isTowerType()) continue;
            int want = rc.getType().paintCapacity - rc.getPaint();
            if (rc.canTransferPaint(a.location, -want)) { rc.transferPaint(a.location, -want); return; }
        }
    }

    /** Every ruin becomes a PAINT tower: a bot that never stops painting binds on paint. */
    static void buildTowerOnRuin() throws GameActionException {
        for (MapLocation r : rc.senseNearbyRuins(-1)) {
            if (rc.canSenseRobotAtLocation(r)) continue;
            if (rc.canCompleteTowerPattern(UnitType.LEVEL_ONE_PAINT_TOWER, r)) {
                rc.completeTowerPattern(UnitType.LEVEL_ONE_PAINT_TOWER, r);
                return;
            }
            if (!rc.isActionReady() || rc.getPaint() < UnitType.SOLDIER.attackCost) return;
            // Mark-then-match, the idiom carol has used since iteration 2. Preferred over
            // reading getTowerPattern() directly because a yardstick must never be subtly
            // wrong, and this path is the one with thousands of games behind it.
            if (rc.canMarkTowerPattern(UnitType.LEVEL_ONE_PAINT_TOWER, r)
                    && rc.senseMapInfo(r.add(Direction.NORTH)).getMark() == PaintType.EMPTY) {
                rc.markTowerPattern(UnitType.LEVEL_ONE_PAINT_TOWER, r);
            }
            for (MapInfo m : rc.senseNearbyMapInfos(r, 8)) {
                PaintType mark = m.getMark();
                if (mark == PaintType.EMPTY || mark == m.getPaint()) continue;
                if (m.getPaint().isEnemy()) continue;   // a soldier cannot overwrite enemy paint
                if (rc.canAttack(m.getMapLocation())) {
                    rc.attack(m.getMapLocation(), mark == PaintType.ALLY_SECONDARY);
                    return;
                }
            }
            return;
        }
    }

    /** Always head for the nearest EMPTY ground in vision; that is the whole strategy. */
    static void move() throws GameActionException {
        if (!rc.isMovementReady()) return;
        MapLocation me = rc.getLocation();
        MapLocation best = null;
        int bestD = Integer.MAX_VALUE;
        for (MapInfo m : rc.senseNearbyMapInfos(-1)) {
            if (m.getPaint() != PaintType.EMPTY || !m.isPassable()) continue;
            int d = me.distanceSquaredTo(m.getMapLocation());
            if (d < bestD) { bestD = d; best = m.getMapLocation(); }
        }
        if (best != null) { explore = best; exploreAge = 0; }
        if (explore == null || ++exploreAge > 40 || me.equals(explore)) {
            explore = new MapLocation(rng.nextInt(rc.getMapWidth()), rng.nextInt(rc.getMapHeight()));
            exploreAge = 0;
        }
        Direction d = me.directionTo(explore);
        for (Direction c : new Direction[]{d, d.rotateLeft(), d.rotateRight(),
                                           d.rotateLeft().rotateLeft(), d.rotateRight().rotateRight()}) {
            if (rc.canMove(c)) { rc.move(c); return; }
        }
        Direction r = DIRS[rng.nextInt(8)];
        if (rc.canMove(r)) rc.move(r);
    }

    /** Soldier/mopper paint: own tile first, then the nearest empty tile in action range. */
    static void paint() throws GameActionException {
        if (rc.getType() != UnitType.SOLDIER) return;
        if (rc.getPaint() < UnitType.SOLDIER.attackCost) return;
        MapLocation me = rc.getLocation();
        MapLocation best = null;
        int bestD = Integer.MAX_VALUE;
        for (MapInfo m : rc.senseNearbyMapInfos(9)) {
            if (m.getPaint() != PaintType.EMPTY || !m.isPassable()) continue;
            MapLocation l = m.getMapLocation();
            int d = me.distanceSquaredTo(l);
            if (d < bestD && rc.canAttack(l)) { bestD = d; best = l; }
        }
        if (best != null) rc.attack(best);
    }

    /** Splash where the r2<=4 disc covers the most convertible tiles. Enemy paint counts double. */
    static void splash() throws GameActionException {
        if (rc.getPaint() < UnitType.SPLASHER.attackCost) return;
        MapLocation best = null;
        int bestScore = 3;   // do not waste 50 paint on a near-empty disc
        for (MapInfo c : rc.senseNearbyMapInfos(4)) {
            MapLocation cl = c.getMapLocation();
            if (!rc.canAttack(cl)) continue;
            int score = 0;
            for (MapInfo m : rc.senseNearbyMapInfos(cl, 4)) {
                if (!m.isPassable()) continue;
                PaintType p = m.getPaint();
                if (p == PaintType.EMPTY) score += 1;
                else if (p.isEnemy() && cl.distanceSquaredTo(m.getMapLocation()) <= 2) score += 2;
            }
            if (score > bestScore) { bestScore = score; best = cl; }
        }
        if (best != null) rc.attack(best);
    }
}

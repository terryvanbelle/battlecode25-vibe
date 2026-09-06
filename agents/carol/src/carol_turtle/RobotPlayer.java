package carol_turtle;

import battlecode.common.*;

import java.util.Random;

/**
 * SYNTHETIC ARCHETYPE — pure economy / turtle. Deliberately NOT forked from carol's
 * strategy code.
 *
 * Policy: never seek combat. Claim every ruin it can reach with towers (paint towers
 * preferred while paint income is thin), upgrade towers with spare chips, lay SRPs on
 * clean ground, and paint a dense contiguous blob around home. Exists to answer "does
 * carol out-scale a pure economy opponent" and to be the opponent that wins on the
 * 2000-round paint tiebreak rather than by fighting.
 */
public class RobotPlayer {
    static RobotController rc;
    static Random rng;
    static MapLocation home = null;

    static final Direction[] DIRS = {
        Direction.NORTH, Direction.NORTHEAST, Direction.EAST, Direction.SOUTHEAST,
        Direction.SOUTH, Direction.SOUTHWEST, Direction.WEST, Direction.NORTHWEST,
    };

    @SuppressWarnings("unused")
    public static void run(RobotController rc) throws GameActionException {
        RobotPlayer.rc = rc;
        rng = new Random(rc.getID() * 3167 + 29);
        home = rc.getLocation();
        while (true) {
            try {
                if (rc.getType().isTowerType()) tower();
                else if (rc.getType() == UnitType.MOPPER) mopper();
                else soldier();
            } catch (Exception e) {
                rc.setIndicatorString("err " + e);
            }
            Clock.yield();
        }
    }

    static void tower() throws GameActionException {
        RobotInfo[] en = rc.senseNearbyRobots(-1, rc.getTeam().opponent());
        RobotInfo best = null;
        for (RobotInfo e : en) if (rc.canAttack(e.location) && (best == null || e.health < best.health)) best = e;
        if (best != null) rc.attack(best.location);
        if (en.length > 0) rc.attack(null);

        // Keep a small worker force; one mopper per four soldiers to shuttle paint.
        UnitType want = (rng.nextInt(5) == 0) ? UnitType.MOPPER : UnitType.SOLDIER;
        for (Direction d : DIRS) {
            MapLocation l = rc.getLocation().add(d);
            if (rc.canBuildRobot(want, l)) { rc.buildRobot(want, l); return; }
        }
    }

    static void soldier() throws GameActionException {
        refill();
        // Upgrade an adjacent tower whenever chips allow (pure econ gain).
        for (RobotInfo a : rc.senseNearbyRobots(2, rc.getTeam())) {
            if (a.type.isTowerType() && rc.canUpgradeTower(a.location)) { rc.upgradeTower(a.location); }
        }
        // Claim a ruin.
        MapLocation ruin = nearestFreeRuin();
        if (ruin != null) {
            UnitType kind = pickTowerType();
            if (rc.canMarkTowerPattern(kind, ruin)
                    && rc.senseMapInfo(ruin.add(Direction.NORTH)).getMark() == PaintType.EMPTY) {
                rc.markTowerPattern(kind, ruin);
            }
            paintToMarks(ruin);
            if (rc.canCompleteTowerPattern(kind, ruin)) rc.completeTowerPattern(kind, ruin);
            // Stand off the centre so completion is never self-blocked.
            if (rc.getLocation().equals(ruin)) stepAway(ruin); else step(ruin);
            rc.setIndicatorString("TURTLE ruin " + ruin + " " + kind);
            paintSelf();
            return;
        }
        // No ruin work: lay an SRP on clean nearby ground.
        if (tryResourcePattern()) { paintSelf(); return; }
        // Otherwise densify paint near home.
        step(home);
        paintNearestEmpty();
        rc.setIndicatorString("TURTLE fill");
    }

    static UnitType pickTowerType() {
        // Paint towers until we have a few, then money.
        return (rc.getNumberTowers() % 2 == 0)
            ? UnitType.LEVEL_ONE_PAINT_TOWER : UnitType.LEVEL_ONE_MONEY_TOWER;
    }

    static boolean tryResourcePattern() throws GameActionException {
        MapLocation me = rc.getLocation();
        if (rc.getChips() < 400) return false;
        for (MapInfo t : rc.senseNearbyMapInfos(8)) {
            MapLocation c = t.getMapLocation();
            if (rc.canCompleteResourcePattern(c)) { rc.completeResourcePattern(c); return true; }
        }
        if (rc.canMarkResourcePattern(me)) {
            boolean clean = true;
            for (MapInfo t : rc.senseNearbyMapInfos(me, 8)) {
                if (t.getPaint().isEnemy()) { clean = false; break; }
            }
            if (clean) { rc.markResourcePattern(me); }
        }
        paintToMarks(me);
        return false;
    }

    static void paintToMarks(MapLocation centre) throws GameActionException {
        if (!rc.isActionReady()) return;
        for (MapInfo t : rc.senseNearbyMapInfos(centre, 8)) {
            PaintType mark = t.getMark();
            if (mark != PaintType.EMPTY && mark != t.getPaint() && rc.canAttack(t.getMapLocation())) {
                rc.attack(t.getMapLocation(), mark == PaintType.ALLY_SECONDARY);
                return;
            }
        }
    }

    static void paintSelf() throws GameActionException {
        if (!rc.isActionReady()) return;
        MapLocation me = rc.getLocation();
        if (rc.senseMapInfo(me).getPaint() == PaintType.EMPTY && rc.canAttack(me)) rc.attack(me);
    }

    static void paintNearestEmpty() throws GameActionException {
        if (!rc.isActionReady()) return;
        MapLocation me = rc.getLocation();
        MapLocation best = null; int bd = Integer.MAX_VALUE;
        for (MapInfo t : rc.senseNearbyMapInfos(9)) {
            if (t.getPaint() != PaintType.EMPTY || !t.isPassable()) continue;
            int d = me.distanceSquaredTo(t.getMapLocation());
            if (d < bd && rc.canAttack(t.getMapLocation())) { bd = d; best = t.getMapLocation(); }
        }
        if (best != null) rc.attack(best);
    }

    static void mopper() throws GameActionException {
        // Ferry paint: take from paint towers, give to dry towers and thirsty allies.
        for (RobotInfo a : rc.senseNearbyRobots(2, rc.getTeam())) {
            if (a.type.isTowerType() && a.paintAmount > 300 && rc.getPaint() < 60) {
                int want = Math.min(100 - rc.getPaint(), a.paintAmount - 300);
                if (want > 0 && rc.canTransferPaint(a.location, -want)) { rc.transferPaint(a.location, -want); }
            }
        }
        for (RobotInfo a : rc.senseNearbyRobots(2, rc.getTeam())) {
            if (a.type.isTowerType() && a.paintAmount < 200 && rc.getPaint() > 50
                    && rc.canTransferPaint(a.location, rc.getPaint() - 20)) {
                rc.transferPaint(a.location, rc.getPaint() - 20); break;
            }
        }
        for (MapInfo t : rc.senseNearbyMapInfos(2)) {
            if (t.getPaint().isEnemy() && rc.canAttack(t.getMapLocation())) { rc.attack(t.getMapLocation()); break; }
        }
        step(home);
        rc.setIndicatorString("TURTLE mop p=" + rc.getPaint());
    }

    static void refill() throws GameActionException {
        int cap = rc.getType().paintCapacity;
        if (rc.getPaint() * 2 >= cap) return;
        for (RobotInfo a : rc.senseNearbyRobots(2, rc.getTeam())) {
            if (a.type.isTowerType()) {
                int want = Math.min(cap - rc.getPaint(), a.paintAmount);
                if (want > 0 && rc.canTransferPaint(a.location, -want)) { rc.transferPaint(a.location, -want); return; }
            }
        }
    }

    static MapLocation nearestFreeRuin() throws GameActionException {
        MapLocation me = rc.getLocation();
        MapLocation best = null; int bd = Integer.MAX_VALUE;
        for (MapLocation r : rc.senseNearbyRuins(-1)) {
            if (rc.canSenseRobotAtLocation(r)) continue;
            int d = me.distanceSquaredTo(r);
            if (d < bd) { bd = d; best = r; }
        }
        return best;
    }

    static void stepAway(MapLocation from) throws GameActionException {
        if (!rc.isMovementReady()) return;
        Direction d = from.directionTo(rc.getLocation());
        if (d != Direction.CENTER && rc.canMove(d)) { rc.move(d); return; }
        for (Direction x : DIRS) if (rc.canMove(x)) { rc.move(x); return; }
    }

    static void step(MapLocation to) throws GameActionException {
        if (!rc.isMovementReady() || to == null) return;
        Direction d = rc.getLocation().directionTo(to);
        if (d == Direction.CENTER) {
            // Sit still on home; wander a little to spread paint.
            Direction r = DIRS[rng.nextInt(8)];
            if (rc.canMove(r)) rc.move(r);
            return;
        }
        if (rc.canMove(d)) { rc.move(d); return; }
        for (Direction a : new Direction[]{ d.rotateLeft(), d.rotateRight() }) {
            if (rc.canMove(a)) { rc.move(a); return; }
        }
    }
}

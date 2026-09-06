package carol_rush;

import battlecode.common.*;

import java.util.Random;

/**
 * SYNTHETIC ARCHETYPE — pure tower rusher. Deliberately NOT forked from carol's
 * strategy code, so it cannot go stale as carol evolves.
 *
 * Policy: spend everything on soldiers, send them at the enemy half, and kill enemy
 * towers (soldier does 50 dmg/attack to towers). Paints only enough to stay alive.
 * Exists to answer "does carol survive an opponent that attacks its towers", a question
 * carol's own lineage can never pose.
 */
public class RobotPlayer {
    static RobotController rc;
    static Random rng;
    static MapLocation target = null;

    static final Direction[] DIRS = {
        Direction.NORTH, Direction.NORTHEAST, Direction.EAST, Direction.SOUTHEAST,
        Direction.SOUTH, Direction.SOUTHWEST, Direction.WEST, Direction.NORTHWEST,
    };

    @SuppressWarnings("unused")
    public static void run(RobotController rc) throws GameActionException {
        RobotPlayer.rc = rc;
        rng = new Random(rc.getID() * 6151 + 3);
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
        // All-in on soldiers.
        for (Direction d : DIRS) {
            MapLocation l = rc.getLocation().add(d);
            if (rc.canBuildRobot(UnitType.SOLDIER, l)) { rc.buildRobot(UnitType.SOLDIER, l); return; }
        }
    }

    static void soldier() throws GameActionException {
        // Refill at any adjacent friendly tower.
        if (rc.getPaint() < 60) {
            for (RobotInfo a : rc.senseNearbyRobots(2, rc.getTeam())) {
                if (a.type.isTowerType()) {
                    int want = Math.min(UnitType.SOLDIER.paintCapacity - rc.getPaint(), a.paintAmount);
                    if (want > 0 && rc.canTransferPaint(a.location, -want)) { rc.transferPaint(a.location, -want); break; }
                }
            }
        }
        // Kill any enemy tower in reach.
        RobotInfo prey = null;
        for (RobotInfo e : rc.senseNearbyRobots(-1, rc.getTeam().opponent())) {
            if (e.type.isTowerType() && (prey == null || e.health < prey.health)) prey = e;
        }
        if (prey != null) {
            target = prey.location;
            if (rc.canAttack(prey.location)) rc.attack(prey.location);
        }
        // Target: enemy tower if seen, else the mirrored image of our spawn (map symmetry guess).
        if (target == null) target = mirrorGuess();
        step(target);
        if (target != null && rc.getLocation().distanceSquaredTo(target) <= 2 && prey == null) target = null;

        // Stay alive: paint under us only if we're bleeding paint on hostile ground.
        MapLocation me = rc.getLocation();
        if (rc.isActionReady() && rc.getPaint() > 40) {
            MapInfo t = rc.senseMapInfo(me);
            if (t.getPaint().isEnemy() || t.getPaint() == PaintType.EMPTY) {
                if (rc.canAttack(me)) rc.attack(me);
            }
        }
        rc.setIndicatorString("RUSH -> " + target);
    }

    static void mopper() throws GameActionException {
        RobotInfo[] en = rc.senseNearbyRobots(2, rc.getTeam().opponent());
        if (en.length > 0) {
            Direction d = rc.getLocation().directionTo(en[0].location);
            Direction c = (d == Direction.NORTHEAST || d == Direction.NORTHWEST) ? Direction.NORTH
                        : (d == Direction.SOUTHEAST || d == Direction.SOUTHWEST) ? Direction.SOUTH : d;
            if (rc.canMopSwing(c)) rc.mopSwing(c);
            else if (rc.canAttack(en[0].location)) rc.attack(en[0].location);
        }
        step(mirrorGuess());
    }

    /** Crude symmetry guess: reflect our position through the map center. */
    static MapLocation mirrorGuess() {
        MapLocation me = rc.getLocation();
        return new MapLocation(rc.getMapWidth() - 1 - me.x, rc.getMapHeight() - 1 - me.y);
    }

    static void step(MapLocation to) throws GameActionException {
        if (!rc.isMovementReady() || to == null) return;
        Direction d = rc.getLocation().directionTo(to);
        if (d == Direction.CENTER) return;
        if (rc.canMove(d)) { rc.move(d); return; }
        Direction[] alt = { d.rotateLeft(), d.rotateRight(),
                            d.rotateLeft().rotateLeft(), d.rotateRight().rotateRight() };
        for (Direction a : alt) if (rc.canMove(a)) { rc.move(a); return; }
        Direction r = DIRS[rng.nextInt(8)];
        if (rc.canMove(r)) rc.move(r);
    }
}

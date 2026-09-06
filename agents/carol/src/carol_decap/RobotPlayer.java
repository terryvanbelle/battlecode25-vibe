package carol_decap;

import battlecode.common.*;

import java.util.Random;

/**
 * SYNTHETIC ARCHETYPE — economic decapitation. Deliberately NOT forked from carol's
 * strategy code, so it cannot go stale as carol evolves.
 *
 * Why this archetype exists, from carol's own trace rather than from theory: carol's
 * fatal degeneracy is that when its last MONEY tower dies, team chip income goes to zero,
 * the treasury freezes, and unit production stops permanently (measured: 1887, 1881 and 44
 * consecutive frozen rounds in three games). `carol_rush` triggers this only incidentally —
 * it hunts whichever tower is nearest and weakest — and wins just 7.5% of its games, which
 * is too lopsided to resolve anything.
 *
 * So this bot does the same thing on purpose and does it first:
 *   1. MONEY towers are hunted before any other target, at any distance in vision.
 *   2. Soldiers focus-fire ONE money tower (the lowest-id one currently visible to them)
 *      instead of spreading damage, because a tower at 1 HP still generates full income.
 *   3. It keeps a real economy, unlike carol_rush: soldiers that pass an unclaimed ruin
 *      build a PAINT tower on it. carol_rush's all-in soldier spend is exactly why it
 *      starves on large maps and can never apply the pressure this instrument is for.
 *
 * The point is to pose a threat carol's own lineage never poses, per the algorithm's
 * self-referential blind spot. Its value as an instrument is its EVENNESS, not its strength.
 */
public class RobotPlayer {
    static RobotController rc;
    static Random rng;
    static MapLocation target = null;
    static MapLocation ruin = null;

    static final Direction[] DIRS = {
        Direction.NORTH, Direction.NORTHEAST, Direction.EAST, Direction.SOUTHEAST,
        Direction.SOUTH, Direction.SOUTHWEST, Direction.WEST, Direction.NORTHWEST,
    };

    @SuppressWarnings("unused")
    public static void run(RobotController rc) throws GameActionException {
        RobotPlayer.rc = rc;
        rng = new Random(rc.getID() * 3557 + 11);
        while (true) {
            try {
                if (rc.getType().isTowerType()) tower();
                else if (rc.getType() == UnitType.MOPPER) mopper();
                else soldier();
            } catch (Exception e) {
                rc.setIndicatorString("DECAP err " + e);
            }
            Clock.yield();
        }
    }

    static boolean isMoneyTower(UnitType t) {
        return t == UnitType.LEVEL_ONE_MONEY_TOWER || t == UnitType.LEVEL_TWO_MONEY_TOWER
            || t == UnitType.LEVEL_THREE_MONEY_TOWER;
    }

    static void tower() throws GameActionException {
        RobotInfo[] en = rc.senseNearbyRobots(-1, rc.getTeam().opponent());
        RobotInfo best = null;
        for (RobotInfo e : en) if (rc.canAttack(e.location) && (best == null || e.health < best.health)) best = e;
        if (best != null) rc.attack(best.location);
        if (en.length > 0) rc.attack(null);
        // Keep 1000 chips so a soldier can always finish a ruin -- the economy carol_rush lacks.
        UnitType want = UnitType.SOLDIER;
        if (rc.getChips() >= 1000 + want.moneyCost) {
            for (Direction d : DIRS) {
                MapLocation l = rc.getLocation().add(d);
                if (rc.canBuildRobot(want, l)) { rc.buildRobot(want, l); return; }
            }
        }
    }

    static void soldier() throws GameActionException {
        if (rc.getPaint() < 60) refill();

        // 1. Economic decapitation: a MONEY tower outranks everything, at any visible range.
        RobotInfo prey = null;
        for (RobotInfo e : rc.senseNearbyRobots(-1, rc.getTeam().opponent())) {
            if (!e.type.isTowerType()) continue;
            boolean m = isMoneyTower(e.type);
            if (prey == null) { prey = e; continue; }
            boolean pm = isMoneyTower(prey.type);
            // money beats non-money; within a class, lowest id so every soldier picks the SAME
            // tower and the damage concentrates -- a tower at 1 HP still earns full income.
            if ((m && !pm) || (m == pm && e.getID() < prey.getID())) prey = e;
        }
        if (prey != null) {
            target = prey.location;
            if (rc.canAttack(prey.location)) rc.attack(prey.location);
        }

        // 2. Economy: claim a ruin we happen to be standing at.
        workRuin();

        if (target == null) target = mirrorGuess();
        step(target);
        if (target != null && rc.getLocation().distanceSquaredTo(target) <= 2 && prey == null) target = null;

        // 3. Stay alive on hostile ground.
        MapLocation me = rc.getLocation();
        if (rc.isActionReady() && rc.getPaint() > 40) {
            MapInfo t = rc.senseMapInfo(me);
            if (t.getPaint().isEnemy() || t.getPaint() == PaintType.EMPTY) {
                if (rc.canAttack(me)) rc.attack(me);
            }
        }
        rc.setIndicatorString("DECAP -> " + target + " ruin=" + ruin);
    }

    /** Build a PAINT tower on any unclaimed ruin in range; paint is what limits this bot. */
    static void workRuin() throws GameActionException {
        ruin = null;
        for (MapLocation r : rc.senseNearbyRuins(-1)) {
            if (rc.canSenseRobotAtLocation(r)) continue;
            ruin = r; break;
        }
        if (ruin == null) return;
        UnitType kind = UnitType.LEVEL_ONE_PAINT_TOWER;
        if (rc.canMarkTowerPattern(kind, ruin)
                && rc.senseMapInfo(ruin.add(Direction.NORTH)).getMark() == PaintType.EMPTY) {
            rc.markTowerPattern(kind, ruin);
        }
        for (MapInfo t : rc.senseNearbyMapInfos(ruin, 8)) {
            PaintType mark = t.getMark();
            if (mark != PaintType.EMPTY && mark != t.getPaint() && rc.canAttack(t.getMapLocation())) {
                rc.attack(t.getMapLocation(), mark == PaintType.ALLY_SECONDARY);
                break;
            }
        }
        if (rc.canCompleteTowerPattern(kind, ruin)) rc.completeTowerPattern(kind, ruin);
    }

    static void refill() throws GameActionException {
        for (RobotInfo a : rc.senseNearbyRobots(2, rc.getTeam())) {
            if (a.type.isTowerType()) {
                int want = Math.min(UnitType.SOLDIER.paintCapacity - rc.getPaint(), a.paintAmount);
                if (want > 0 && rc.canTransferPaint(a.location, -want)) { rc.transferPaint(a.location, -want); return; }
            }
        }
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

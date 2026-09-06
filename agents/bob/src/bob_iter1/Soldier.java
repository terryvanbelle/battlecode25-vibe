package bob_iter1;

import battlecode.common.*;

/** v0 soldier: refill when dry, capture ruins into towers, shoot enemy towers, paint, explore. */
public class Soldier {
    static final int REFILL_BELOW = 50;      // start seeking refill when paint below this
    static final int PAINT_FLOOR = 15;       // don't paint below this stash level

    static MapLocation workRuin = null;

    static void run() throws GameActionException {
        RobotController rc = G.rc;
        MapLocation me = rc.getLocation();

        // 0. Refill paint from a nearby allied tower when low.
        if (rc.getPaint() < REFILL_BELOW && tryRefill()) return;

        // 1. Ruin capture.
        chooseRuin();
        if (workRuin != null) {
            workOnRuin();
        }

        // 2. Attack enemy tower in range.
        if (rc.isActionReady()) {
            RobotInfo[] foes = rc.senseNearbyRobots(-1, G.them);
            for (RobotInfo f : foes) {
                if (f.getType().isTowerType() && rc.canAttack(f.getLocation())) {
                    rc.attack(f.getLocation());
                    break;
                }
            }
        }

        // 3. Movement: toward ruin if working one, else wander.
        if (workRuin != null) {
            Nav.navTo(workRuin);
        } else {
            Nav.wander();
        }

        // 4. Idle-action painting: own tile first, else nearest empty tile in range.
        paintSomething();
    }

    /** Use an otherwise-idle action to expand territory. */
    static void paintSomething() throws GameActionException {
        RobotController rc = G.rc;
        if (!rc.isActionReady() || rc.getPaint() <= PAINT_FLOOR) return;
        MapLocation me = rc.getLocation();
        if (!rc.senseMapInfo(me).getPaint().isAlly() && rc.canAttack(me)) {
            rc.attack(me);
            return;
        }
        MapLocation best = null;
        int bestD = Integer.MAX_VALUE;
        for (MapInfo t : rc.senseNearbyMapInfos(UnitType.SOLDIER.actionRadiusSquared)) {
            if (t.getPaint() == PaintType.EMPTY && t.isPassable()
                    && t.getMark() == PaintType.EMPTY) {
                MapLocation l = t.getMapLocation();
                int d = me.distanceSquaredTo(l);
                if (d < bestD) { bestD = d; best = l; }
            }
        }
        if (best != null && rc.canAttack(best)) rc.attack(best);
    }

    /** Pick the nearest visible ruin that has no tower on it. */
    static void chooseRuin() throws GameActionException {
        RobotController rc = G.rc;
        if (workRuin != null) {
            // drop it if it's visible and now occupied
            if (rc.canSenseLocation(workRuin) && rc.senseRobotAtLocation(workRuin) != null) {
                workRuin = null;
            }
        }
        if (workRuin == null) {
            MapLocation me = rc.getLocation();
            MapLocation[] ruins = rc.senseNearbyRuins(-1);
            int best = Integer.MAX_VALUE;
            for (MapLocation r : ruins) {
                if (rc.senseRobotAtLocation(r) != null) continue; // tower already there
                int d = me.distanceSquaredTo(r);
                if (d < best) { best = d; workRuin = r; }
            }
        }
    }

    /** Mark, paint, and complete the tower pattern at workRuin. */
    static void workOnRuin() throws GameActionException {
        RobotController rc = G.rc;
        MapLocation ruin = workRuin;
        UnitType want = towerTypeFor(ruin);

        // Mark the pattern once (probe: any pattern tile unmarked?).
        MapLocation probe = ruin.translate(0, 1);
        if (rc.canSenseLocation(probe) && rc.senseMapInfo(probe).getMark() == PaintType.EMPTY
                && rc.canMarkTowerPattern(want, ruin)) {
            rc.markTowerPattern(want, ruin);
        }

        // Paint marked tiles that don't match yet.
        if (rc.isActionReady() && rc.getPaint() > PAINT_FLOOR) {
            for (MapInfo t : rc.senseNearbyMapInfos(ruin, 8)) {
                PaintType mark = t.getMark();
                if (mark != PaintType.EMPTY && mark != t.getPaint()) {
                    MapLocation l = t.getMapLocation();
                    if (rc.canAttack(l)) {
                        rc.attack(l, mark == PaintType.ALLY_SECONDARY);
                        break;
                    }
                }
            }
        }

        // Complete when ready.
        if (rc.canCompleteTowerPattern(want, ruin)) {
            rc.completeTowerPattern(want, ruin);
            rc.setTimelineMarker("tower built", 0, 255, 0);
            workRuin = null;
        }
    }

    /** Deterministic, team-symmetric tower type choice: mix money and paint towers. */
    static UnitType towerTypeFor(MapLocation ruin) {
        return ((ruin.x + ruin.y) & 1) == 0
            ? UnitType.LEVEL_ONE_MONEY_TOWER : UnitType.LEVEL_ONE_PAINT_TOWER;
    }

    /** Withdraw paint from an allied tower if adjacent; else walk to one. True if handled. */
    static boolean tryRefill() throws GameActionException {
        RobotController rc = G.rc;
        RobotInfo bestTower = null;
        int best = Integer.MAX_VALUE;
        for (RobotInfo a : rc.senseNearbyRobots(-1, G.us)) {
            if (a.getType().isTowerType() && a.getPaintAmount() >= 100) {
                int d = rc.getLocation().distanceSquaredTo(a.getLocation());
                if (d < best) { best = d; bestTower = a; }
            }
        }
        if (bestTower == null) return false;
        int want = -Math.min(UnitType.SOLDIER.paintCapacity - rc.getPaint(),
                             bestTower.getPaintAmount() - 50);
        if (want < 0 && rc.canTransferPaint(bestTower.getLocation(), want)) {
            rc.transferPaint(bestTower.getLocation(), want);
            return true;
        }
        Nav.navTo(bestTower.getLocation());
        return true;
    }
}

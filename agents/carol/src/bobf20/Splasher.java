package bobf20;

import battlecode.common.*;

/** v0 splasher: seek clusters of non-ally paintable tiles / enemy towers, splash them. */
public class Splasher {
    static final int SPLASH_MIN_VALUE = 5; // tiles gained to justify 50 paint

    static void run() throws GameActionException {
        RobotController rc = G.rc;
        MapLocation me = rc.getLocation();

        // Splash the best target within range (targets up to r^2 4).
        if (rc.isActionReady() && rc.getPaint() >= UnitType.SPLASHER.attackCost + 10) {
            MapLocation bestLoc = null;
            int bestScore = SPLASH_MIN_VALUE - 1;
            for (MapLocation c : rc.getAllLocationsWithinRadiusSquared(me, 4)) {
                if (!rc.canAttack(c)) continue;
                int score = 0;
                for (MapInfo t : rc.senseNearbyMapInfos(c, 4)) {
                    PaintType p = t.getPaint();
                    if (!t.isPassable()) {
                        continue;
                    }
                    if (p == PaintType.EMPTY) score += 1;
                    else if (p.isEnemy()
                             && c.isWithinDistanceSquared(t.getMapLocation(), 2)) score += 2;
                }
                RobotInfo r = rc.canSenseLocation(c) ? rc.senseRobotAtLocation(c) : null;
                if (r != null && r.getTeam() == G.them && r.getType().isTowerType()) score += 8;
                if (score > bestScore) { bestScore = score; bestLoc = c; }
            }
            if (bestLoc != null) rc.attack(bestLoc);
        }

        // Move toward the nearest visible enemy/empty region.
        MapLocation tgt = null;
        int best = Integer.MAX_VALUE;
        for (MapInfo t : rc.senseNearbyMapInfos()) {
            PaintType p = t.getPaint();
            if (t.isPassable() && (p.isEnemy() || p == PaintType.EMPTY)) {
                int d = me.distanceSquaredTo(t.getMapLocation());
                if (d < best) { best = d; tgt = t.getMapLocation(); }
            }
        }
        if (tgt != null && best > 2) Nav.navTo(tgt);
        else Nav.wander();
    }
}

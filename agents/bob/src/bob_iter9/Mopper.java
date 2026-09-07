package bob_iter9;

import battlecode.common.*;

/** v0 mopper: drain enemy robots' paint, mop enemy tiles, avoid enemy terrain. */
public class Mopper {
    static void run() throws GameActionException {
        RobotController rc = G.rc;
        MapLocation me = rc.getLocation();

        RobotInfo[] foes = rc.senseNearbyRobots(-1, G.them);

        if (rc.isActionReady()) {
            // 1. Attack an adjacent enemy robot (steals 10 paint, mops its tile).
            for (RobotInfo f : foes) {
                if (f.getType().isRobotType() && rc.canAttack(f.getLocation())) {
                    rc.attack(f.getLocation());
                    break;
                }
            }
            // 2. Swing if 2+ enemy robots sit in a cardinal swing zone.
            if (rc.isActionReady() && foes.length >= 2) {
                Direction bestDir = null;
                int bestCount = 1;
                for (int i = 0; i < 4; i++) {
                    Direction d = new Direction[]{Direction.NORTH, Direction.EAST,
                        Direction.SOUTH, Direction.WEST}[i];
                    if (!rc.canMopSwing(d)) continue;
                    int cnt = 0;
                    for (RobotInfo f : foes) {
                        if (!f.getType().isRobotType()) continue;
                        int dx = f.getLocation().x - me.x, dy = f.getLocation().y - me.y;
                        boolean hit;
                        switch (d) {
                            case NORTH: hit = dy >= 1 && dy <= 2 && dx >= -1 && dx <= 1; break;
                            case SOUTH: hit = dy <= -1 && dy >= -2 && dx >= -1 && dx <= 1; break;
                            case EAST:  hit = dx >= 1 && dx <= 2 && dy >= -1 && dy <= 1; break;
                            default:    hit = dx <= -1 && dx >= -2 && dy >= -1 && dy <= 1; break;
                        }
                        if (hit) cnt++;
                    }
                    if (cnt > bestCount) { bestCount = cnt; bestDir = d; }
                }
                if (bestDir != null) rc.mopSwing(bestDir);
            }
            // 3. Mop an enemy-painted tile in reach.
            if (rc.isActionReady()) {
                for (MapInfo t : rc.senseNearbyMapInfos(2)) {
                    if (t.getPaint().isEnemy() && rc.canAttack(t.getMapLocation())) {
                        rc.attack(t.getMapLocation());
                        break;
                    }
                }
            }
        }

        // 4. Move toward nearest visible enemy paint; else wander.
        MapLocation tgt = null;
        int best = Integer.MAX_VALUE;
        for (MapInfo t : rc.senseNearbyMapInfos()) {
            if (t.getPaint().isEnemy()) {
                int d = me.distanceSquaredTo(t.getMapLocation());
                if (d < best) { best = d; tgt = t.getMapLocation(); }
            }
        }
        if (tgt != null) Nav.navTo(tgt);
        else Nav.wander();
    }
}

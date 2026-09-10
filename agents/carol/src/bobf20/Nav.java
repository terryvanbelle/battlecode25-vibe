package bobf20;

import battlecode.common.*;

/** v0 navigation: greedy with slide, mild enemy-paint avoidance, wander persistence. */
public class Nav {
    static Direction wanderDir = null;
    static int wanderSteps = 0;
    static MapLocation lastLoc = null;
    static int stuckTurns = 0;

    /** Greedy step toward target; prefers not stepping on enemy paint. */
    static void navTo(MapLocation tgt) throws GameActionException {
        RobotController rc = G.rc;
        if (!rc.isMovementReady()) return;
        MapLocation me = rc.getLocation();
        if (me.equals(tgt)) return;

        // stuck detection
        if (me.equals(lastLoc)) stuckTurns++; else stuckTurns = 0;
        lastLoc = me;
        if (stuckTurns >= 3) {
            Direction d = G.randomDir();
            if (rc.canMove(d)) { rc.move(d); return; }
        }

        Direction d = me.directionTo(tgt);
        Direction[] cands = {
            d, d.rotateLeft(), d.rotateRight(),
            d.rotateLeft().rotateLeft(), d.rotateRight().rotateRight(),
        };
        // first pass: avoid enemy paint
        for (Direction c : cands) {
            if (rc.canMove(c)) {
                MapLocation nl = me.add(c);
                PaintType p = rc.senseMapInfo(nl).getPaint();
                if (!p.isEnemy()) { rc.move(c); return; }
            }
        }
        // second pass: take anything
        for (Direction c : cands) {
            if (rc.canMove(c)) { rc.move(c); return; }
        }
    }

    /** Persistent-direction wander. */
    static void wander() throws GameActionException {
        RobotController rc = G.rc;
        if (!rc.isMovementReady()) return;
        if (wanderDir == null || wanderSteps <= 0 || !rc.canMove(wanderDir)) {
            // pick a new direction we can actually move in
            int start = G.rng.nextInt(8);
            wanderDir = null;
            for (int i = 0; i < 8; i++) {
                Direction c = G.DIRS[(start + i) & 7];
                if (rc.canMove(c)) { wanderDir = c; break; }
            }
            wanderSteps = 6 + G.rng.nextInt(10);
            if (wanderDir == null) return; // boxed in
        }
        rc.move(wanderDir);
        wanderSteps--;
    }
}

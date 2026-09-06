package bob;

import battlecode.common.*;

/**
 * Iteration 8: remembered-tower refill, shared by every unit type.
 *
 * The hole this closes, measured (TRAINING_LOG.md, "WE STARVE OUR OWN ARMY"):
 * 456 of 583 of our unit deaths across four games happened at <=10 paint, and
 * soldiers specifically died starved 315 times out of 368. `Soldier.tryRefill`
 * only ever looked at `senseNearbyRobots` -- vision r^2=20, about 4.5 tiles --
 * so a unit that ran low anywhere else simply kept wandering until it hit zero,
 * took NO_PAINT_DAMAGE (20 HP/turn) and died. Moppers and splashers had no
 * refill logic at all.
 *
 * Every robot spawns within BUILD_ROBOT_RADIUS_SQUARED=4 of the tower that built
 * it, so `home` is populated on the robot's very first turn and is never null
 * afterwards. That is what makes this cost nothing: no comms, no search, no
 * exploration -- the information was already in the robot's first sense call and
 * we were throwing it away.
 *
 * Only PAINT towers are worth remembering. Engine-verified in the iteration 4
 * probe: a money tower has paintPerTurn == 0 and a newly built tower starts at
 * paintAmount == 0, so a money tower built mid-game can never refill anybody.
 * The two starting towers are the exception (INITIAL_TOWER_PAINT_AMOUNT=500),
 * which is why any tower is remembered as a fallback when no paint tower has
 * been seen yet.
 */
public class Refill {
    /** Nearest allied PAINT tower ever seen. */
    static MapLocation home = null;
    /** Nearest allied tower of any kind ever seen; fallback before a paint tower is. */
    static MapLocation anyTower = null;

    /** Keep the tower memory current from an ally scan the caller already needed. */
    static void observe(RobotInfo[] allies) {
        MapLocation me = G.rc.getLocation();
        int bestPaint = Integer.MAX_VALUE, bestAny = Integer.MAX_VALUE;
        for (RobotInfo a : allies) {
            UnitType t = a.getType();
            if (!t.isTowerType()) continue;
            int d = me.distanceSquaredTo(a.getLocation());
            if (d < bestAny) { bestAny = d; anyTower = a.getLocation(); }
            if (t.paintPerTurn > 0 && d < bestPaint) { bestPaint = d; home = a.getLocation(); }
        }
    }

    /**
     * If below `below` paint, spend the turn getting more: withdraw from an adjacent
     * tower, else walk to the remembered one. Returns true if the turn was spent
     * refilling, in which case the caller should return.
     *
     * The sense call is gated rather than unconditional. Measured peak bytecode is
     * already 9148 of 17500 and the limiter truncates a turn silently, with no
     * exception -- so a full unit that already knows a tower does no extra sensing
     * at all. It only scans when it has no memory yet (its very first turn, at the
     * tower that built it) or when it is approaching the threshold and about to need
     * the answer.
     */
    static boolean seek(int below) throws GameActionException {
        RobotController rc = G.rc;
        int paint = rc.getPaint();
        if (home != null && paint >= below * 2) return false;

        RobotInfo[] allies = rc.senseNearbyRobots(-1, G.us);
        observe(allies);
        if (paint >= below) return false;

        // 1. A tower in sensing range with paint to spare: take it.
        MapLocation me = rc.getLocation();
        RobotInfo best = null;
        int bestD = Integer.MAX_VALUE;
        for (RobotInfo a : allies) {
            if (!a.getType().isTowerType() || a.getPaintAmount() < 100) continue;
            int d = me.distanceSquaredTo(a.getLocation());
            if (d < bestD) { bestD = d; best = a; }
        }
        if (best != null) {
            // Ask for what the tower can actually spare, not a flat 100: a request the
            // tower cannot cover makes canTransferPaint false, and the unit would then
            // fall through to navigating to a tower it is already standing next to and
            // slide around it forever. Leave 50 behind so the tower keeps a working
            // float, as the superseded tryRefill did.
            int avail = best.getPaintAmount() - 50;
            int want = -Math.min(rc.getType().paintCapacity - paint, avail);
            if (want < 0 && rc.canTransferPaint(best.getLocation(), want)) {
                rc.transferPaint(best.getLocation(), want);
                return true;
            }
            if (!me.isWithinDistanceSquared(best.getLocation(), 2)) {
                Nav.navTo(best.getLocation());
            }
            return true;
        }

        // 2. Nothing in sight: walk to the tower we remember. This is the whole point.
        MapLocation tgt = home != null ? home : anyTower;
        if (tgt == null) return false;
        // Already there and it had nothing to give: wait for it to regenerate rather
        // than sliding around it forever. A paint tower regains paintPerTurn every
        // round, so waiting terminates; wandering off to starve does not.
        if (me.isWithinDistanceSquared(tgt, 2)) return true;
        Nav.navTo(tgt);
        return true;
    }
}

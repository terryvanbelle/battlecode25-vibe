package bob;

import battlecode.common.*;

/** v0 soldier: refill when dry, capture ruins into towers, shoot enemy towers, paint, explore. */
public class Soldier {
    static final int REFILL_BELOW = 50;      // start seeking refill when paint below this
    static final int PAINT_FLOOR = 15;       // don't paint below this stash level

    static MapLocation workRuin = null;

    static void run() throws GameActionException {
        RobotController rc = G.rc;
        MapLocation me = rc.getLocation();

        // 0. Refill paint when low. Iteration 8: Refill.seek also WALKS to a
        //    remembered tower when none is in vision, which the old tryRefill could
        //    not do -- 86% of our soldier deaths were at <=10 paint.
        if (Refill.seek(REFILL_BELOW)) return;

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

    /**
     * Deterministic tower type choice: an avalanche hash of the ruin's coordinates,
     * so roughly one ruin in two becomes a money tower on ANY ruin lattice.
     *
     * Iteration 4 tried biasing this toward paint towers (1 ruin in 4) on the
     * reasoning that a MONEY tower is a permanently sterile spawn point -- engine
     * verified, it has paintPerTurn == 0 and InternalRobot's constructor gives a new
     * tower paintAmount == 0, so it can never accumulate the 200 paint a soldier
     * costs. That arm scored 17/40 against bob_iter3 and was REJECTED. The reasoning
     * was right about money towers and wrong about the trade: chips buy paint income
     * back through iteration 3's upgrades at +5 paint/turn per 2,500 chips, so
     * starving the treasury starves the upgrades and nets out worse. Do not re-open
     * without evidence that changes that arithmetic.
     *
     * The choice must also stay a pure function of the ruin and never of time: a
     * soldier marks the 5x5 with one type's pattern and the "already marked?" probe
     * in workOnRuin then refuses to re-mark, so a ruin whose type changed mid-build
     * could never be completed by a later soldier.
     */
    static UnitType towerTypeFor(MapLocation ruin) {
        // Iteration 7. The old rule was ((x + y) & 1): a parity, and parity is
        // INVARIANT along any lattice whose step is even. Ruins sit on a lattice, so
        // on every even ruin spacing the rule returned 100% of a single type for the
        // whole map (measured: gridworld 0 paint / 9 money; starburst 4 paint / 0
        // money; Snowglobe 4/0; Thirds 1/0). Simulated over grid and staggered ruin
        // lattices at spacings 5-8, it deviates from an even mix by up to 50 points.
        //
        // An avalanche hash's low bit is uncorrelated with any lattice: same simulation,
        // worst deviation 11 points, and the all-one-type rate on 4-ruin maps falls
        // from 33% to 15%. ~10 bytecodes. Still a pure function of the ruin, which the
        // marking protocol requires (see the note above: a type that changes over time
        // deadlocks workOnRuin's "already marked?" probe).
        int h = ruin.x * 0x27D4EB2D + ruin.y * 0x165667B1;
        h ^= h >>> 15;
        h *= 0x2545F491;
        h ^= h >>> 13;
        return (h & 1) == 0
            ? UnitType.LEVEL_ONE_MONEY_TOWER : UnitType.LEVEL_ONE_PAINT_TOWER;
    }

}

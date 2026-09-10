package bobf12;

import battlecode.common.*;

/** v0 soldier: refill when dry, capture ruins into towers, shoot enemy towers, paint, explore. */
public class Soldier {

    // ---- SRP construction (iteration 4) ----
    // Engine-verified (InternalRobot.processBeginningOfRound): a tower with
    // paintPerTurn != 0 gains paintPerTurn + extraResourcesFromPatterns(team) each
    // round, and extraResourcesFromPatterns = 3 * (number of active SRPs). So every
    // SRP is +3 PAINT/turn to EVERY allied paint tower (not just +3 chips to money
    // towers), for 200 chips -- and chips are this bot's dead resource (327k unspent
    // at r2000; see TRAINING_LOG structural trace). Paint income is the binding
    // constraint, so SRPs convert the dead resource into the scarce one.
    // An SRP costs 200 chips for +3 paint/turn on EVERY allied paint tower; a tower
    // upgrade costs 2500 for +5 paint/turn on ONE tower. With ~8 paint towers the SRP
    // is over an order of magnitude more chip-efficient, so its threshold sits well
    // below iteration 3's upgrade threshold and it wins the race for chips.
    static final int SRP_MIN_CHIPS = 500;
    static final int SRP_PATIENCE = 120;     // turns spent on one site before abandoning it
    static MapLocation srp = null;           // centre this soldier is building
    static int srpTurns = 0;
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

        // 1b. SRP construction, only when there is no ruin to capture. Uses the
        //     action and holds position (the whole 5x5 is inside the soldier's own
        //     action radius when it stands on the centre), so it returns early.
        if (workRuin == null && workOnSrp()) return;

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
        // ABLATION A7: iteration 7's avalanche hash removed; back to iteration 1's
        // team-symmetric parity rule. Under rotation (x+y) and (W-1-x + H-1-y) share
        // parity whenever W+H is even, so mirrored ruins agree on those maps and the
        // two halves get the same mix -- which is the property iteration 7 gave up.
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

    /**
     * Build a Special Resource Pattern on the spot. Returns true if this turn was
     * spent on SRP work (caller should not also wander/paint).
     */
    static boolean workOnSrp() throws GameActionException {
        RobotController rc = G.rc;
        MapLocation me = rc.getLocation();

        if (srp != null && ++srpTurns > SRP_PATIENCE) srp = null;

        if (srp == null) {
            // Start one here. canMarkResourcePattern already enforces the geometry
            // (centre >=2 from every edge, all 25 tiles paintable -- no walls, no
            // ruins) and that we hold the 25 paint the marking costs.
            if (rc.getChips() < SRP_MIN_CHIPS) return false;
            if (!rc.canMarkResourcePattern(me) || !srpSiteSafe(me)) return false;
            rc.markResourcePattern(me);
            srp = me;
            srpTurns = 0;
        } else if (me.distanceSquaredTo(srp) > 8) {
            Nav.navTo(srp);                      // wandered off (e.g. to refill)
            return true;
        }

        if (rc.canCompleteResourcePattern(srp)) {
            rc.completeResourcePattern(srp);
            rc.setTimelineMarker("SRP", 255, 200, 0);
            srp = null;
            return true;
        }

        // Paint one tile that does not yet match its mark. markResourcePattern has
        // already written the required colour of all 25 tiles into the marks, so
        // this reuses the tower-pattern painting path exactly.
        if (rc.isActionReady() && rc.getPaint() > PAINT_FLOOR) {
            for (MapInfo t : rc.senseNearbyMapInfos(srp, 8)) {
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
        return true;
    }

    /**
     * A site is only worth starting if no tile of the 5x5 is enemy-painted (soldiers
     * cannot overwrite enemy paint, so such a site could never be completed), it does
     * not overlap a finished SRP, and no tile already carries a mark. That last check
     * is what stops two soldiers standing a tile apart from each marking overlapping
     * resource patterns whose required colours contradict -- neither would ever
     * complete, and both would burn their 25 paint and their patience.
     */
    static boolean srpSiteSafe(MapLocation c) throws GameActionException {
        RobotController rc = G.rc;
        for (MapInfo t : rc.senseNearbyMapInfos(c, 8)) {
            if (t.getPaint().isEnemy()) return false;      // soldiers cannot repaint it
            if (t.isResourcePatternCenter()) return false;  // overlaps a finished SRP
            if (t.getMark() != PaintType.EMPTY) return false; // overlaps a pattern already
                                                             // being built (SRP or tower)
        }
        return true;
    }
}

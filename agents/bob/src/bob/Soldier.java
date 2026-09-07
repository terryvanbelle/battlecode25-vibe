package bob;

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

    // ---- SRP site search (iteration 10) ----
    // assertCanMarkResourcePattern permits any centre with r^2 <= 8 (javap-verified:
    // assertCanActLocation(loc, 8)), which is all 25 tiles of the 5x5 around us --
    // (2,2) is r^2 = 8 and qualifies. Iteration 9 tested exactly one of those 25, the
    // tile underfoot, and a probe measured 87-99% of its refusals as GEOMETRY
    // (isValidPatternCenter: >=2 from every edge, all 25 tiles free of walls/ruins).
    // So the bot was sampling one square of a 25-square neighbourhood and concluding
    // the neighbourhood was unusable.
    // Offsets are ordered by increasing r^2 so the nearest legal centre wins, and the
    // tail is rotated by robot ID so soldiers do not all probe the same tile first --
    // a fixed compass order here is exactly the play-symmetry bug class.
    // SRP_SCAN is capped at 13 for a hard reason, not as a tuning choice. srpSiteSafe
    // must inspect all 25 tiles of a candidate's 5x5, and senseNearbyMapInfos does NOT
    // throw for tiles out of vision -- it filters by canSenseLocation and silently
    // returns fewer (javap-verified). With vision r^2 = 20, the farthest tile of the
    // 5x5 around a centre at offset (dx,dy) sits at (|dx|+2)^2 + (|dy|+2)^2, which is
    // <= 20 exactly for the 13 offsets with dx^2+dy^2 <= 4 -- (2,0) lands on 20, (2,1)
    // on 25. The first 13 entries below are precisely those, in r^2 order. Scanning
    // past 13 marks patterns we cannot fully see.
    static final int SRP_SCAN = 13;          // candidate centres examined per turn (1 = iteration 9)
    static final int[] SRP_DX = {0, 1,0,-1,0, 1,1,-1,-1, 2,0,-2,0, 2,1,-1,-2,-2,-1,1,2, 2,2,-2,-2};
    static final int[] SRP_DY = {0, 0,1,0,-1, 1,-1,1,-1, 0,2,0,-2, 1,2,2,1,-1,-2,-2,-1, 2,-2,2,-2};
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
        int h = ruin.x * 0x27D4EB2D + ruin.y * 0x165667B1;
        h ^= h >>> 15;
        h *= 0x2545F491;
        h ^= h >>> 13;
        return (h & 1) == 0
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
            // Search the markable neighbourhood. canMarkResourcePattern enforces the
            // geometry and the 25-paint marking cost; srpSiteSafe is checked only on
            // a candidate that already passed, because it senses 25 tiles and is the
            // expensive half.
            if (rc.getChips() < SRP_MIN_CHIPS) return false;
            MapLocation site = null;
            // Rotate within the FULLY-VISIBLE offsets only (indices 1..12, the ones
            // with dx^2+dy^2 <= 4). Rotating over all 24 pulled in the r^2 = 5 and 8
            // offsets, whose 5x5 corner lies outside vision r^2 = 20 -- measured at
            // 70% of all attempts refused by the visibility guard, i.e. most scan
            // slots spent on candidates that could never pass.
            int rot = rc.getID() % 12;
            for (int k = 0; k < SRP_SCAN; k++) {
                int i = (k == 0) ? 0 : 1 + ((k - 1 + rot) % 12);
                MapLocation c = me.translate(SRP_DX[i], SRP_DY[i]);
                if (rc.canMarkResourcePattern(c) && srpSiteSafe(c)) { site = c; break; }
            }
            if (site == null) return false;
            rc.markResourcePattern(site);
            srp = site;
            srpTurns = 0;
        } else if (!me.equals(srp)) {
            // Walk to the centre and paint only from there. A soldier's action radius
            // is r^2 = 9, and the 5x5 around its OWN tile tops out at r^2 = 8, so
            // standing on the centre is what makes every pattern tile attackable.
            // Iteration 10 lets the SEARCH range out to r^2 = 8, which puts the far
            // corner of a remote pattern at r^2 = 32 -- unreachable. Searching at
            // range and painting from range are different things; only the first is
            // legal here, so the soldier commits to the site by standing on it.
            Nav.navTo(srp);
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
        MapInfo[] area = rc.senseNearbyMapInfos(c, 8);
        // isValidPatternCenter already guarantees the centre is >=2 from every map
        // edge, so all 25 tiles exist; anything short of 25 means we cannot SEE the
        // whole pattern, and marking one we cannot inspect is how two soldiers end up
        // with contradictory marks that never complete.
        if (area.length < 25) return false;
        for (MapInfo t : area) {
            if (t.getPaint().isEnemy()) return false;      // soldiers cannot repaint it
            if (t.isResourcePatternCenter()) return false;  // overlaps a finished SRP
            if (t.getMark() != PaintType.EMPTY) return false; // overlaps a pattern already
                                                             // being built (SRP or tower)
        }
        return true;
    }
}

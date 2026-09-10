package darla;

import battlecode.common.*;

/**
 * Darla — built 2026-09-10 by the coordinator, from scratch, using every finding
 * the alice, bob and carol lineages established. The isolation firewall that kept
 * them apart does not apply to me, so Darla is the first design in this project
 * that gets to use all of it at once.
 *
 * THE THESIS, in one paragraph. Both surviving lineages spent weeks optimising
 * ECONOMY and COVERAGE, both drove that framing to a complete enumeration, and
 * both lose three quarters of their games to the external standard. Meanwhile the
 * single strongest empirical result anyone produced was an accident: carol built a
 * 38-line fork of her own bot that sieges towers with splashers, intending it only
 * as a measuring stick, and it beat her 60/40 — the only opponent in her pool she
 * loses to. Nobody adopted it. Darla is built around it from the first line.
 *
 * WHAT IS ESTABLISHED, and where it came from:
 *
 *  1. SPLASHER-PRIMARY. carol's from-scratch soldier-primary rewrite was rejected
 *     at −5.71 sd. alice measured production efficiency per unit of build paint at
 *     splasher 0.1291 / soldier 0.0603 / mopper 0.0000 tiles-per-paint, and the
 *     same ordering replicated on carol's units (0.1893 / 0.0558) — two unrelated
 *     designs, one ordering, which makes it a property of the game.
 *
 *  2. NO MOPPERS, EVER. Zero production across 105 spawns, and not merely
 *     inefficient but SUPERSEDED: a splasher overwrites enemy paint directly
 *     within r²≤2 of a centre it can place r²≤4 away, converting enemy→ally in one
 *     step across up to 13 tiles, where a mopper yields enemy→EMPTY on one tile and
 *     still needs a soldier. alice checked the one exclusivity that could have
 *     saved them — a shade the splasher gets wrong on a pattern square — and the
 *     soldier's ruin branch already repairs it. No conversion rate rescues a
 *     superseded unit.
 *
 *  3. THE SPLASHER OUT-RANGES WHAT IT KILLS. SPLASHER.actionRadiusSquared = 4
 *     reaches distance 4; a paint or money tower answers only to distance 3.
 *     aoeAttackStrength 100 against LEVEL_ONE health 1000 is ten hits.
 *
 *  4. TOWER DAMAGE IS PERMANENT. alice verified from the engine that there is no
 *     restoration path, that upgradeTower explicitly carries the deficit forward,
 *     and that towers sit outside processEndOfTurn. So the ten hits need not be
 *     simultaneous — her own win sample converts at ~25 hits per kill. Every
 *     closure in this project that said "a unit cannot finish a tower" was burst
 *     arithmetic applied to an accumulating quantity.
 *
 *  5. KILLING MONEY TOWERS IS CATASTROPHIC FOR THE VICTIM. carol measured the
 *     absorbing state: with the last money tower gone, chip income is zero and
 *     production freezes permanently — 1,887 consecutive frozen rounds in one
 *     game. Both lineages have this vulnerability and neither exploited it.
 *
 *  6. SPENDING IS THE INVESTMENT. alice cut spawns 78% and banked nothing: paint
 *     per tower was 147.0 against 147.4, because income is per-tower and spawning
 *     is what builds the towers that generate it. You cannot save your way to a
 *     surplus here, so Darla never withholds production to accumulate.
 *
 *  7. NEVER GATE A PAINT-COSTLY ACTION ON CHIPS. alice measured rank correlation
 *     −0.496 between team chips and per-tower paint, and above a high chip gate the
 *     paint clears its requirement on 0.0% of 244 frames. Chips accumulate because
 *     nothing consumes them; tower paint cannot, because consuming it is how the
 *     generator grows. A chip gate opens exactly when the paint is gone.
 *
 *  8. PAINT TOWERS OVER MONEY TOWERS. A money tower has paintPerTurn == 0: it
 *     spawns about two robots from its starting stash and is a dry build site
 *     forever, and buildRobot draws paint from the BUILDING tower's stash.
 *
 *  9. DO NOT OVER-EXPAND AND UNDER-CONVERT. alice wins the r300 tower race 12–4
 *     and converts those leads at 75% against carol's 100%. More towers is not the
 *     objective; the objective is the win those towers were supposed to buy.
 */
public class RobotPlayer {

    static RobotController rc;
    static int turn = 0;

    /** Stamped into the indicator string so a replay of Darla vs a Darla snapshot splits by team. */
    static final String BUILD = "d1";

    // ---- per-robot memory -------------------------------------------------
    // Deliberately small. carol built a full remembered-ruin store and it was
    // rejected at every dose (21/50, 27/50 against a ≥31 gate) — the information
    // is cheap to acquire and worth little once acquired. What Darla remembers is
    // one enemy tower, because that is the target the whole design is about.
    static MapLocation siegeTarget = null;   // enemy tower this splasher is working
    static int siegeSeen = 0;                // turns since we last confirmed it
    static MapLocation home = null;          // an ally tower, for refills
    static Direction roam = null;            // persistent heading, re-rolled on block

    @SuppressWarnings("unused")
    public static void run(RobotController rc_) throws GameActionException {
        rc = rc_;
        roam = Direction.allDirections()[rc.getID() % 8];
        while (true) {
            turn++;
            try {
                switch (rc.getType()) {
                    case SOLDIER:  runSoldier();  break;
                    case SPLASHER: runSplasher(); break;
                    case MOPPER:   runMopper();   break;
                    default:       runTower();    break;
                }
            } catch (GameActionException e) {
                // A refused action is a bug in a guard, not a reason to die.
            } catch (Exception e) {
                // Never let one robot's exception end its turn loop.
            }
            Clock.yield();
        }
    }

    // =======================================================================
    // TOWERS
    // =======================================================================
    static void runTower() throws GameActionException {
        MapLocation me = rc.getLocation();

        // Attack first, always. A tower's attack is free of any resource we are
        // short of, and finding #4 says the damage it does is permanent — so a
        // shot that does not kill is still progress, and skipping it is the only
        // way to waste it.
        RobotInfo[] foes = rc.senseNearbyRobots(-1, rc.getTeam().opponent());
        if (foes.length > 0) {
            RobotInfo best = null;
            for (RobotInfo f : foes) {
                if (!rc.canAttack(f.getLocation())) continue;
                // Prefer the lowest-health enemy in range: damage is permanent,
                // so finishing something converts accumulated damage into a
                // removal, which is the only thing that reduces incoming fire.
                if (best == null || f.getHealth() < best.getHealth()) best = f;
            }
            if (best != null && rc.canAttack(best.getLocation())) rc.attack(best.getLocation());
        }
        if (rc.canAttack(null)) rc.attack(null);   // area attack, no target argument

        // Production. Finding #6: spending IS the investment, so build whenever
        // the tower can afford it and never hold back to accumulate.
        //
        // Finding #7 in force: the ONLY gate here is the building tower's own
        // paint, which is the resource that actually binds. There is deliberately
        // no chip threshold — a chip gate opens when the paint is gone.
        UnitType want = chooseSpawn();
        if (want != null) {
            for (Direction d : Direction.allDirections()) {
                MapLocation spot = me.add(d);
                if (rc.canBuildRobot(want, spot)) { rc.buildRobot(want, spot); break; }
            }
        }

        rc.setIndicatorString(BUILD + " T p=" + rc.getPaint() + " $" + rc.getChips());
    }

    /**
     * Findings #1 and #2: splasher-primary, no moppers ever.
     *
     * Soldiers exist only to complete tower patterns — the one job a splasher
     * cannot do — so Darla keeps a small, fixed number of them rather than a share.
     * A share of a growing army is how both lineages ended up with more soldiers
     * than they had work for; alice measured 96% of her army's action capacity
     * unused, with 71.98% of turns having no workable ground in vision at all.
     */
    static UnitType chooseSpawn() throws GameActionException {
        int paint = rc.getPaint();
        // A splasher costs more paint than a soldier; ask for it first, and fall
        // back rather than stall. Neither branch consults chips (finding #7).
        if (paint >= UnitType.SPLASHER.paintCost + 50) {
            // Keep a thin soldier tail for pattern completion only: roughly one
            // soldier per three splashers, decided by tower ID so towers do not
            // all make the same choice on the same turn.
            if ((rc.getID() + turn) % 4 == 0 && paint >= UnitType.SOLDIER.paintCost + 50)
                return UnitType.SOLDIER;
            return UnitType.SPLASHER;
        }
        if (paint >= UnitType.SOLDIER.paintCost + 50) return UnitType.SOLDIER;
        return null;
    }

    // =======================================================================
    // SPLASHER — the unit the whole design is about
    // =======================================================================
    static void runSplasher() throws GameActionException {
        MapLocation me = rc.getLocation();
        Team foe = rc.getTeam().opponent();

        // ---- 1. Siege, in preference to everything else --------------------
        // Findings #3, #4, #5. A splasher reaches distance 4; a paint or money
        // tower answers only to 3. So the correct behaviour is to stand at the
        // edge of our own reach and hit, not to close.
        RobotInfo target = null;
        for (RobotInfo r : rc.senseNearbyRobots(-1, foe)) {
            if (!r.getType().isTowerType()) continue;
            // Finding #5: money towers first. Removing the last one freezes the
            // opponent's production permanently.
            boolean money = r.getType() == UnitType.LEVEL_ONE_MONEY_TOWER
                         || r.getType() == UnitType.LEVEL_TWO_MONEY_TOWER
                         || r.getType() == UnitType.LEVEL_THREE_MONEY_TOWER;
            if (target == null) { target = r; continue; }
            boolean tMoney = target.getType() == UnitType.LEVEL_ONE_MONEY_TOWER
                          || target.getType() == UnitType.LEVEL_TWO_MONEY_TOWER
                          || target.getType() == UnitType.LEVEL_THREE_MONEY_TOWER;
            if (money && !tMoney) { target = r; continue; }
            if (money == tMoney && r.getHealth() < target.getHealth()) target = r;
        }

        if (target != null) {
            siegeTarget = target.getLocation();
            siegeSeen = turn;
            MapLocation t = siegeTarget;
            if (rc.isActionReady() && rc.canAttack(t) && rc.getPaint() >= UnitType.SPLASHER.attackCost) {
                rc.attack(t);
                rc.setIndicatorString(BUILD + " SIEGE " + t + " hp=" + target.getHealth());
                return;
            }
            // Not in range yet: approach only to the edge of our own reach.
            // me.distanceSquaredTo(t) > 4 means we cannot hit; closing past 4
            // walks into the tower's own radius for no gain.
            if (rc.isMovementReady() && me.distanceSquaredTo(t) > UnitType.SPLASHER.actionRadiusSquared) {
                stepToward(t);
            }
            rc.setIndicatorString(BUILD + " APPROACH " + t);
            return;
        }

        // A target we saw but can no longer see: keep walking to it for a while.
        if (siegeTarget != null && turn - siegeSeen < 30) {
            if (rc.isMovementReady()) stepToward(siegeTarget);
            rc.setIndicatorString(BUILD + " RECALL " + siegeTarget);
            return;
        }
        siegeTarget = null;

        // ---- 2. Otherwise paint, which is what a splasher is efficient at ---
        if (rc.isActionReady() && rc.getPaint() >= UnitType.SPLASHER.attackCost) {
            MapLocation best = null; int bestGain = 0;
            for (MapInfo t : rc.senseNearbyMapInfos(UnitType.SPLASHER.actionRadiusSquared)) {
                MapLocation c = t.getMapLocation();
                if (!rc.canAttack(c)) continue;
                int gain = splashGain(c);
                if (gain > bestGain) { bestGain = gain; best = c; }
            }
            // Two tiles is a low bar deliberately: finding #6 says unspent paint
            // does not accumulate, so a marginal splash beats holding.
            if (best != null && bestGain >= 2) { rc.attack(best); return; }
        }

        refillOrRoam();
        rc.setIndicatorString(BUILD + " S p=" + rc.getPaint());
    }

    /** Tiles a splash centred here would convert: empty or enemy-held, not already ours. */
    static int splashGain(MapLocation c) throws GameActionException {
        int n = 0;
        for (MapInfo t : rc.senseNearbyMapInfos(c, 4)) {
            if (t.isWall() || t.hasRuin()) continue;
            PaintType p = t.getPaint();
            if (p == PaintType.EMPTY) n++;
            else if (!p.isAlly()) n += 2;   // taking enemy ground moves the difference by two
        }
        return n;
    }

    // =======================================================================
    // SOLDIER — pattern completion only
    // =======================================================================
    static void runSoldier() throws GameActionException {
        MapLocation me = rc.getLocation();

        // Complete or mark a tower pattern on any ruin in reach. Finding #8:
        // paint towers, because a money tower is a dry build site after two robots.
        for (MapLocation ruin : rc.senseNearbyRuins(-1)) {
            if (rc.canSenseRobotAtLocation(ruin)) continue;      // already built
            UnitType want = UnitType.LEVEL_ONE_PAINT_TOWER;
            // One money tower in four keeps chips flowing for upgrades and
            // completions without starving paint (finding #8).
            if (((ruin.x * 31 + ruin.y) & 3) == 0) want = UnitType.LEVEL_ONE_MONEY_TOWER;

            if (rc.canCompleteTowerPattern(want, ruin)) { rc.completeTowerPattern(want, ruin); return; }
            if (rc.canMarkTowerPattern(want, ruin))     { rc.markTowerPattern(want, ruin);     return; }

            // Fill in the pattern squares we can reach.
            if (rc.isActionReady()) {
                for (MapInfo t : rc.senseNearbyMapInfos(ruin, 8)) {
                    if (t.getMark() != PaintType.EMPTY && t.getPaint() != t.getMark()) {
                        MapLocation c = t.getMapLocation();
                        if (rc.canAttack(c)) { rc.attack(c); return; }
                    }
                }
            }
            if (rc.isMovementReady() && me.distanceSquaredTo(ruin) > 4) { stepToward(ruin); return; }
        }

        // No ruin work: paint the ground under us rather than idle. alice measured
        // 96% of army action capacity unused; an unspent action is spent anyway.
        if (rc.isActionReady() && rc.canAttack(me)) {
            MapInfo here = rc.senseMapInfo(me);
            if (here.getPaint() == PaintType.EMPTY) { rc.attack(me); return; }
        }
        refillOrRoam();
        rc.setIndicatorString(BUILD + " D p=" + rc.getPaint());
    }

    // =======================================================================
    // MOPPER — never built (finding #2). Present only so a stray one is not idle.
    // =======================================================================
    static void runMopper() throws GameActionException {
        if (rc.isActionReady()) {
            for (MapInfo t : rc.senseNearbyMapInfos(2)) {
                PaintType p = t.getPaint();
                if (p != PaintType.EMPTY && !p.isAlly()) {
                    MapLocation c = t.getMapLocation();
                    if (rc.canAttack(c)) { rc.attack(c); return; }
                }
            }
        }
        refillOrRoam();
    }

    // =======================================================================
    // SHARED MOVEMENT / SUPPLY
    // =======================================================================

    /**
     * Refill from a tower when dry, otherwise roam.
     *
     * The threshold is a RATE-free absolute on our own tank, not a reserve held
     * back at the tower: alice shipped a reserve of 200 against towers that hold a
     * mean of 154.8, which disabled the mechanism on 82.9% of frames — a constant
     * set above the level the resource normally sits at. Darla asks only whether
     * the tower has anything to give.
     */
    static void refillOrRoam() throws GameActionException {
        MapLocation me = rc.getLocation();
        int cap = rc.getType().paintCapacity;

        if (rc.getPaint() * 2 < cap) {
            for (RobotInfo r : rc.senseNearbyRobots(2, rc.getTeam())) {
                if (!r.getType().isTowerType()) continue;
                int want = cap - rc.getPaint();
                int have = r.getPaintAmount();
                int take = Math.min(want, have);
                if (take > 0 && rc.canTransferPaint(r.getLocation(), -take)) {
                    rc.transferPaint(r.getLocation(), -take);
                    return;
                }
            }
            // Walk to a remembered tower rather than wander while dry.
            if (home != null && rc.isMovementReady()) { stepToward(home); return; }
        }
        for (RobotInfo r : rc.senseNearbyRobots(-1, rc.getTeam()))
            if (r.getType().isTowerType()) { home = r.getLocation(); break; }

        if (rc.isMovementReady()) roamStep();
    }

    /** One step toward a location, sliding around anything in the way. */
    static void stepToward(MapLocation t) throws GameActionException {
        if (!rc.isMovementReady()) return;
        Direction d = rc.getLocation().directionTo(t);
        if (d == null || d == Direction.CENTER) return;
        if (rc.canMove(d)) { rc.move(d); return; }
        if (rc.canMove(d.rotateLeft()))  { rc.move(d.rotateLeft());  return; }
        if (rc.canMove(d.rotateRight())) { rc.move(d.rotateRight()); return; }
        if (rc.canMove(d.rotateLeft().rotateLeft()))   { rc.move(d.rotateLeft().rotateLeft());   return; }
        if (rc.canMove(d.rotateRight().rotateRight())) { rc.move(d.rotateRight().rotateRight()); return; }
    }

    /**
     * Persistent heading, re-rolled only when blocked.
     *
     * carol measured that units blocked mid-map are stopped by ROBOTS, not walls —
     * 27–50% of stuck turns had no adjacent wall at all — and that her own
     * explore target was overwritten by a nearest-empty-tile rule that, for a
     * forward unit, points backwards. A heading that persists until it fails
     * avoids both.
     */
    static void roamStep() throws GameActionException {
        if (roam != null && rc.canMove(roam)) { rc.move(roam); return; }
        Direction start = roam == null ? Direction.NORTH : roam;
        Direction d = start;
        for (int i = 0; i < 8; i++) {
            d = d.rotateRight();
            if (rc.canMove(d)) { roam = d; rc.move(d); return; }
        }
    }
}

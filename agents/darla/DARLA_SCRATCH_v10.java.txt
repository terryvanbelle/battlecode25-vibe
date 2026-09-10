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
    static final String BUILD = "d10";

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
        // Remember the tower that built us. v4's units never refilled once (xfer0
        // in every window against the opponent's 4-6) and starved five at a time,
        // because `home` was only ever set from a tower that happened to be in
        // sense range while roaming. A unit that has wandered out of range of every
        // tower has nowhere to go and dies holding an empty tank.
        try {
            for (RobotInfo r : rc.senseNearbyRobots(2, rc.getTeam()))
                if (r.getType().isTowerType()) { home = r.getLocation(); break; }
        } catch (GameActionException e) { }
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
        buildBest(me);

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
    static void buildBest(MapLocation me) throws GameActionException {
        // v1 SHIPPED THE DEFECT THIS DESIGN WAS WRITTEN TO AVOID, and lost 0/90.
        // The gate was `paint >= paintCost + 50` — 350 for a splasher, 250 for a
        // soldier — against towers that alice measured holding a mean of 154.8,
        // below 200 on 82.9% of frames. A constant set above the level its
        // resource normally holds disables the mechanism it guards; I wrote that
        // rule into DESIGN.md and then shipped it in the one path that matters.
        //
        // The repair is not a better constant, it is no constant: `canBuildRobot`
        // already knows whether this tower can pay. Asking it is the only gate
        // that cannot be mis-set, and it keeps finding #7 (never consult chips)
        // automatically, since the engine checks what the engine requires.
        //
        // Preference order still encodes finding #1 — splasher first, soldier as
        // the fallback — which self-balances over a game: early towers are poor
        // and make soldiers, which build more towers, and the richer towers that
        // result make splashers. That is finding #6 running forwards rather than
        // a share imposed on top of it.
        // ...BUT NOT IN THE OPENING, and v3 proved it the hard way. With two
        // starting towers holding ~410 paint, "splasher first" spent the entire
        // opening stash on two splashers and left 20 paint and no soldiers. Only
        // a SOLDIER can complete a tower pattern, so Darla built no tower for the
        // whole game: it finished 469 rounds with the two towers it started with
        // while the opponent grew to six, and its coverage peaked at round 100
        // and fell away as its units died faster than two towers could replace
        // them. A flat economy, from one preference applied at the wrong time.
        //
        // Finding #9 says winning the tower race is not winning — but that
        // presumes being IN the race, and alice was winning it 12–4 when she said
        // it. Finding #6 is the one that governs here: spending IS the
        // investment, so the opening should buy the generator and the middle game
        // should buy the units the generator exists to make.
        boolean opening = rc.getNumberTowers() < 5;
        UnitType first  = opening ? UnitType.SOLDIER  : UnitType.SPLASHER;
        UnitType second = opening ? UnitType.SPLASHER : UnitType.SOLDIER;

        // A TOWER MUST KEEP ENOUGH TO SUSTAIN WHAT IT BUILDS. Through v8 Darla
        // spent 100% of tower paint on spawning: one paint tower at 10/turn, a
        // 200-paint soldier every twenty rounds, tower paint pinned at exactly 200
        // all game, and therefore NOTHING left when a unit came back dry -- xfer0
        // and starved5 in every window, units dying before they could finish a
        // pattern, and two towers at round 240 against the opponent's fifteen.
        //
        // This is not the "withhold to accumulate" that finding #6 forbids. That
        // was about banking a resource whose income is per-tower; this is
        // ALLOCATION between two uses of the same resource, and starving the units
        // you already built to buy one more is strictly worse than both.
        //
        // 150 sits below the 200-600 a tower reaches, so unlike v1's spawn gate it
        // is a threshold the resource actually crosses.
        int reserve = 150;
        for (Direction d : Direction.allDirections()) {
            MapLocation spot = me.add(d);
            if (rc.getPaint() >= first.paintCost + reserve && rc.canBuildRobot(first, spot)) {
                rc.buildRobot(first, spot); return;
            }
        }
        for (Direction d : Direction.allDirections()) {
            MapLocation spot = me.add(d);
            if (rc.getPaint() >= second.paintCost + reserve && rc.canBuildRobot(second, spot)) {
                rc.buildRobot(second, spot); return;
            }
        }
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
        // A DRY SOLDIER MUST BE ALLOWED TO LEAVE. Every version through v9 returned
        // unconditionally from the ruin branch, so a soldier that could see any
        // unbuilt ruin never reached the supply path at all: the replay shows one
        // sitting at its ruin with p=0, permanently, and that single `return` is
        // the whole of the xfer0 that has been in every window since v1. Fixing
        // the supply threshold three times could never have found it, because the
        // supply code was unreachable.
        boolean canWork = rc.getPaint() * 3 >= rc.getType().paintCapacity;

        for (MapLocation ruin : canWork ? rc.senseNearbyRuins(-1) : new MapLocation[0]) {
            if (rc.canSenseRobotAtLocation(ruin)) continue;      // already built

            // ALWAYS A PAINT TOWER. Finding #8: a money tower has paintPerTurn == 0
            // and is a dry build site after about two robots. v7 made one ruin in
            // four a money tower and spent the game on 10 paint per turn from a
            // single paint tower, unable to afford a 200-paint soldier, while
            // $5,700 in chips sat idle. Chips are not the binding resource here and
            // completeTowerPattern's 1000 is affordable many times over (finding #7).
            UnitType want = UnitType.LEVEL_ONE_PAINT_TOWER;

            // Mark, then paint, then complete -- IN THE SAME TURN. Marking does not
            // consume the action, so v7's `if (canMark) { mark; return; }` threw away
            // a paint action on every ruin it opened.
            if (rc.canMarkTowerPattern(want, ruin)) rc.markTowerPattern(want, ruin);

            if (rc.isActionReady()) {
                for (MapInfo t : rc.senseNearbyMapInfos(ruin, 8)) {
                    PaintType mark = t.getMark();
                    if (mark == PaintType.EMPTY || mark == t.getPaint()) continue;

                    // A SOLDIER CANNOT OVERWRITE ENEMY PAINT, and `canAttack` does
                    // not check it -- so the attack is legal, costs the full 5, and
                    // does nothing. carol's iteration 29 measured this at 71-85% of
                    // ALL soldier attacks, burning 42-55% of the soldier paint
                    // budget, and it is why Darla's soldiers starved five at a time
                    // with xfer0. Skipping the tile also lets the loop reach one
                    // that IS paintable instead of stalling on an impossible one.
                    if (t.getPaint().isEnemy()) continue;

                    MapLocation c = t.getMapLocation();
                    if (rc.canAttack(c)) { rc.attack(c, mark == PaintType.ALLY_SECONDARY); break; }
                }
            }

            if (rc.canCompleteTowerPattern(want, ruin)) { rc.completeTowerPattern(want, ruin); return; }
            if (rc.isMovementReady() && me.distanceSquaredTo(ruin) > 4) { stepToward(ruin); }
            rc.setIndicatorString(BUILD + " RUIN " + ruin + " p=" + rc.getPaint());
            return;
        }

        // No ruin in reach: HEAD FOR ONE. v4 finished on three towers against
        // seven because soldiers roamed at random and only ever worked a ruin they
        // happened to stumble into. Expansion is the generator (finding #6), so a
        // soldier with nothing to do walks toward the nearest unclaimed ruin it
        // can see rather than in whatever direction it was already going.
        MapLocation freeRuin = null; int bestD = Integer.MAX_VALUE;
        for (MapLocation ruin : rc.senseNearbyRuins(-1)) {
            if (rc.canSenseRobotAtLocation(ruin)) continue;
            int d = me.distanceSquaredTo(ruin);
            if (d < bestD) { bestD = d; freeRuin = ruin; }
        }
        if (freeRuin != null && rc.isMovementReady() && rc.getPaint() >= rc.getType().attackCost) {
            stepToward(freeRuin);
            rc.setIndicatorString(BUILD + " ->RUIN " + freeRuin);
            return;
        }

        // Otherwise paint the ground under us rather than idle. alice measured 96%
        // of army action capacity unused; an unspent action is spent anyway.
        // ...but not out of the tank a pattern needs. A soldier self-painting every
        // turn spends its whole capacity on ~20 tiles of coverage and then has
        // nothing left to complete a ruin, which is the job only it can do.
        if (rc.isActionReady() && rc.getPaint() * 2 > rc.getType().paintCapacity && rc.canAttack(me)) {
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
        int cap = rc.getType().paintCapacity;

        // ONE threshold governs both halves of supply, because v6 decoupled them
        // and got the worst of each: it refilled at a quarter tank but only walked
        // home below a single action's cost, so a unit that went low far from a
        // tower kept working until it was inert and then starved on the way back.
        // xfer0 and starved5 in every window, and not one tower built all game.
        //
        // v5 had the opposite failure -- refill whenever below CAPACITY glued
        // units to the tower, 171 transfers across four units in 60 rounds for two
        // paint actions. So: one line, one number. Below a third of tank, go and
        // get paint; take everything the tower will give; otherwise work.
        boolean low = rc.getPaint() * 3 < cap;

        if (low) {
            for (RobotInfo r : rc.senseNearbyRobots(2, rc.getTeam())) {
                if (!r.getType().isTowerType()) continue;
                int take = Math.min(cap - rc.getPaint(), r.getPaintAmount());
                if (take > 0 && rc.canTransferPaint(r.getLocation(), -take)) {
                    rc.transferPaint(r.getLocation(), -take);
                    return;
                }
            }
            if (home != null && rc.isMovementReady()) {
                stepToward(home);
                rc.setIndicatorString(BUILD + " ->HOME " + home + " p=" + rc.getPaint());
                return;
            }
        }

        // Keep `home` fresh from anything we can see. A unit that has just been
        // built knows its builder (set on turn 1); one that has wandered adopts
        // whatever tower it passes, which is what makes the walk above terminate.
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

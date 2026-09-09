package carol_r1;

import battlecode.common.*;

import java.util.Random;

/**
 * carol_r1 -- FROM-SCRATCH SOLDIER-PRIMARY REWRITE.
 *
 * Registered at the end of the post-58 survey. It is not a fork of src/carol with knobs
 * moved: it is a second architecture, written to be evaluated against the first one on the
 * standing gate. A rejection is a normal and useful outcome -- it would be direct evidence
 * that the splasher-primary local maximum is the better of the two.
 *
 * WHY A REWRITE AND NOT ANOTHER KNOB
 * ----------------------------------
 * Every parametric axis this lineage has is bracketed and most sit at their incumbent value
 * (see TRAINING_LOG.md, "the closure map is now essentially complete"). The closures are
 * mutually load-bearing: soldiers need chips, chips need towers, towers need soldiers. The
 * measured architecture gap, from the tournament replays on Leaf:
 *
 *     capability      carol   alice
 *     towers built        8      25 (cap)
 *     soldiers built      2     177
 *     unpaint (mops)      0     740
 *
 * Iteration 47 set SPLASH_FLOOR = 0 -- a one-constant step toward soldier-primary -- and
 * scored 11/50, WORSE than either endpoint of the ladder. That is doctrine 5b's
 * destructive-pair logic operating across a whole design: each intermediate state has one
 * architecture's constants driving the other's unit mix. So the constants below are derived
 * TOGETHER, from the resource arithmetic, rather than inherited one at a time.
 *
 * THE FIVE DESIGN DECISIONS, EACH WITH ITS DERIVATION
 * --------------------------------------------------
 * D1. SPAWN IS SURPLUS-MATCHED, NOT A RANDOM ROLL.
 *     The incumbent rolls a fixed 20-sided die for the unit type and then applies three
 *     independently-inherited floors (SPLASH_FLOOR 2000, CHIP_RESERVE 1200, PAINT_FLOOR 200).
 *     Their joint effect is that a soldier needs chips >= 2250 while a splasher needs only
 *     1600, which is the whole reason this bot fields 2 soldiers and 41 splashers.
 *     carol_r1 instead picks the unit whose COST VECTOR fits the current surplus. buildRobot
 *     draws paint from the BUILDING tower's stash (RULES.md [E]), so the two scarce
 *     quantities at a tower are its own paint and the shared treasury:
 *         soldier  200 paint / 250 chips   -- the only unit that can complete a ruin
 *         mopper   100 paint / 300 chips   -- cheapest in the binding resource
 *         splasher 300 paint / 400 chips   -- most expensive in the binding resource
 *     Soldier is the default. A mopper is built only in the band where the tower cannot
 *     afford a soldier but can afford a mopper -- turning a stash that would otherwise sit
 *     idle into a unit. A splasher is built only from genuine paint surplus, so it can never
 *     displace a soldier. No arm of this policy can starve soldier production, which is the
 *     specific failure the incumbent's floors produce.
 *
 * D2. MONEY_MOD = 3, NOT THE INCUMBENT'S 4.
 *     This is the clearest case of a constant co-adapted to the OLD architecture, and the
 *     log records its peak measured at 4 -- in a regime of 8 towers and 2 soldiers, i.e.
 *     permanent saturation. Redo the arithmetic for a bot that is actually growing.
 *     Per round, at level 1: a money tower makes 20 chips, a paint tower makes 5 paint.
 *       - Saturated (no ruins left, chips buy only soldiers): 250 chips and 200 paint per
 *         soldier, so 20M/250 = 5P/200 gives P = 3.2M -- money share 24%, i.e. MONEY_MOD 4.
 *       - Growing: every ~3 soldiers also completes a ruin at 1000 chips, so the chip cost
 *         per soldier is ~250 + 333 = 583, and 20M/583 = 5P/200 gives P = 1.37M -- money
 *         share 42%.
 *     A bot that never leaves the growth phase wants far more money towers than the
 *     incumbent's key gives it. MONEY_MOD = 3 (33%) sits between the two regimes and is
 *     reachable without making the key asymmetric. The key itself is unchanged and remains
 *     invariant under both map symmetries, so neither team gets a different build mix.
 *
 * D3. PAINT LOGISTICS WITH HYSTERESIS -- the structural addition.
 *     The incumbent refills only if it HAPPENS to be standing next to a tower; nothing ever
 *     walks to one. transferPaint is hardcoded to r^2 <= 2 for every unit type (RULES.md
 *     [E], iteration 38), so a unit must physically touch a tower -- it can never top up in
 *     passing. A robot at 0 paint takes -20 HP/turn and cannot act at all. The iteration-58
 *     trace is the whole argument in one line: soldier id12362 built 4 towers, refilling from
 *     each one it built, and then STARVED TO DEATH at r220, after which carol built no
 *     soldier for the remaining 527 rounds. With 2 soldiers who stand next to what they
 *     build, opportunistic refill nearly works. With 100 soldiers spread over a 60x60 map it
 *     cannot, and I believe this -- not the unit mix -- is why iteration 47's soldier-primary
 *     arm scored 11/50. Every mobile unit here remembers ally tower locations and walks back
 *     to one below a floor, with hysteresis so it does not oscillate.
 *
 * D4. RUIN DISPERSAL.
 *     A soldier skips a ruin that already has >= RUIN_CROWD allies within r^2 <= 8. With 2
 *     soldiers this is a no-op; with 100 it is what stops the swarm stacking on one ruin.
 *     Clumping is not free: end-of-turn drain is -1 per adjacent ally, -2 per adjacent ally
 *     on enemy territory (RULES.md [E]), so a stacked swarm pays the binding resource for the
 *     privilege of duplicating work.
 *
 * D5. MOPPERS ARE AIMED AT DENIED RUINS.
 *     Iteration 44 established the mechanism: a soldier cannot overwrite enemy paint and
 *     completion is exact, so ONE enemy-painted tile inside the 5x5 denies a ruin to soldiers
 *     permanently. It measured carol's UNPAINT at 0 on every map against alice's 740 on Leaf,
 *     and priced the resulting idle at 24.8-43.2% of all soldier turns. The incumbent's
 *     answer was to BAN the denied ruin -- correct when nothing can clear it, and a
 *     capitulation once moppers exist. Here a mopper navigates to the nearest ruin holding
 *     enemy paint, which makes the ban list recoverable instead of permanent.
 *
 * WHAT IS DELIBERATELY CARRIED OVER, AND WHY
 * ------------------------------------------
 * Tower attack (single + AoE every turn), the symmetry-invariant tower-type key, the
 * exploration target loop, and the greedy stepToward with an ID-parity tiebreak. These are
 * measured-good or measured-neutral and are not what the rewrite is testing; changing them
 * would confound the comparison. Upgrades are opportunistic-only at a large surplus: the log
 * measured "fund upgrades by withholding spawning" at 12/40 = 30.0%, and while ruins remain a
 * new paint tower is 1000 chips for +5 paint/turn against an upgrade's 2500 for the same +5.
 */
public class RobotPlayer {
    static RobotController rc;
    static Random rng;
    static int turnCount = 0;

    /** Build tag. Frozen when this build is snapshotted; shifts the replay hash, so a dose
     *  pair must share one tag for doctrine 3's byte-identity check to work on raw hashes. */
    static final String BUILD = "r1";

    // ---- bytecode monitoring (Phase 0 item 6: on every full evaluation, forever) -----------
    static int bcOverruns = 0, bcNearMisses = 0, bcMaxUsed = 0;

    // ---- D2: economy mix -------------------------------------------------------------------
    /** ~1 ruin in MONEY_MOD becomes a money tower. See D2 for the derivation. */
    static final int MONEY_MOD = 3;

    // ---- D1: surplus-matched spawn ---------------------------------------------------------
    /** Chips held back so a soldier can always complete a ruin pattern. This is the EXACT
     *  engine cost of completeTowerPattern, not a tuned number: 1000. Released once the
     *  tower cap is reached, at which point no ruin can be claimed and the reserve is dead
     *  weight. */
    static final int RUIN_RESERVE = 1000;
    static final int TOWER_CAP = 25;
    /**
     * D3b (stage 0 correction, iteration 59). Tower paint kept back from SPAWNING, because
     * under D3 a tower's stash is primarily the standing army's fuel depot, not a spawn buffer.
     *
     * The first version set this to 40 ("one soldier refill"), sized for the incumbent's world
     * where nothing ever walks home. Stage 0 showed what that does once 70 soldiers are
     * cycling: paint acts collapsed 2000 -> 15 per 500 rounds between r500 and r2000 while
     * 322 soldiers were built and 321 starved -- the entire paint income converted into dead
     * soldiers and no painting at all, with $7,220 chips left idle.
     *
     * The arithmetic I should have done first. ~17 paint towers at 5/turn plus two starting
     * lv2 towers is ~100 paint/turn of income. A soldier that paints every turn costs 5
     * (attack) + 1 (neutral-tile drain) = 6/turn, and clumping adds -1 per adjacent ally. So
     * income supports an army of order 16-33 continuously-active soldiers, NOT 70. Above that
     * the standing army's passive drain alone exceeds total income and every soldier starves
     * no matter how good the logistics are.
     *
     * A tower cannot count the army, but it does not need to: if the army is too big, the
     * army drains the depot, and a drained tower stops spawning. Gating spawn on a large
     * reserve therefore makes production SELF-REGULATING against the true constraint. At 300,
     * a soldier needs the tower to hold 500 of its 1000 capacity.
     */
    static final int TOWER_PAINT_KEEP = 300;
    /**
     * D1c. Depot reserve kept back when spawning a SPLASHER, deliberately smaller than
     * TOWER_PAINT_KEEP. In the contested regime a soldier's marginal value is zero -- it cannot
     * touch enemy paint -- so holding depot paint back to spawn one instead is strictly worse.
     */
    static final int SPLASHER_KEEP = 150;
    /** Opportunistic upgrade only: strictly leftover chips, never withheld from spawning. */
    static final int UPGRADE_SURPLUS = 5000;

    // ---- D3: paint logistics ---------------------------------------------------------------
    static final int TOWER_MEM = 12;
    static int[] towerMem = new int[TOWER_MEM];      // (x<<6)|y of ally towers ever seen
    static int towerN = 0;
    static boolean refilling = false;                // hysteresis latch
    static int refillTrips = 0, refillTopUps = 0, dryTurns = 0;

    // ---- D4/D5 ------------------------------------------------------------------------------
    static final int RUIN_CROWD = 2;                 // allies within r^2<=8 that make a ruin "taken"
    static int crowdSkips = 0, mopTargets = 0, unpaints = 0;

    // ---- ruin persistence (carried over) ----------------------------------------------------
    static MapLocation ruinFocus = null;
    static int ruinTurns = 0;
    static final int RUIN_PATIENCE = 40;
    static final int RUIN_BAN_ROUNDS = 250;
    static final int BAN_CAP = 24;
    static int[] banLoc = new int[BAN_CAP];
    static int[] banUntil = new int[BAN_CAP];
    static int banN = 0;
    static int denyBans = 0, patienceBans = 0;

    // ---- exploration ------------------------------------------------------------------------
    static MapLocation explore = null;
    static MapLocation lastLoc = null;
    static int stuckTurns = 0, exploreAge = 0;

    static final Direction[] DIRS = {
        Direction.NORTH, Direction.NORTHEAST, Direction.EAST, Direction.SOUTHEAST,
        Direction.SOUTH, Direction.SOUTHWEST, Direction.WEST, Direction.NORTHWEST
    };

    public static void run(RobotController rc_) throws GameActionException {
        rc = rc_;
        // Seeded per robot, never from team identity (Phase 0 item 7, play-symmetry).
        rng = new Random(rc.getID() * 7919 + 13);

        while (true) {
            turnCount += 1;
            int startRound = rc.getRoundNum();
            String state = "";
            try {
                rememberTowers();
                switch (rc.getType()) {
                    case SOLDIER:  state = runSoldier();  break;
                    case MOPPER:   state = runMopper();   break;
                    case SPLASHER: state = runSplasher(); break;
                    default:       state = runTower();    break;
                }
            } catch (GameActionException e) {
                state = "GAE:" + e.getMessage();
            } catch (Exception e) {
                state = "EXC:" + e;
            } finally {
                monitorAndYield(startRound, state);
            }
        }
    }

    static void monitorAndYield(int startRound, String state) {
        int used = Clock.getBytecodeNum();
        int limit = rc.getType().isRobotType()
            ? GameConstants.ROBOT_BYTECODE_LIMIT : GameConstants.TOWER_BYTECODE_LIMIT;
        int endRound = rc.getRoundNum();
        if (endRound != startRound) bcOverruns++;
        else if (used * 5 > limit * 4) bcNearMisses++;
        if (used > bcMaxUsed) bcMaxUsed = used;
        rc.setIndicatorString("[" + BUILD + "] bc=" + used + "/" + limit + " max=" + bcMaxUsed
            + " ov=" + bcOverruns + " nm=" + bcNearMisses
            + " rf=" + refillTrips + "/" + refillTopUps + " dry=" + dryTurns
            + " cs=" + crowdSkips + " mt=" + mopTargets + " up=" + unpaints
            + " db=" + denyBans + " pb=" + patienceBans
            + " | " + state);
        Clock.yield();
    }

    // ================================================================== towers

    static String runTower() throws GameActionException {
        RobotInfo[] enemies = rc.senseNearbyRobots(-1, rc.getTeam().opponent());
        RobotInfo best = null;
        for (RobotInfo e : enemies) {
            if (rc.canAttack(e.location) && (best == null || e.health < best.health)) best = e;
        }
        if (best != null && rc.canAttack(best.location)) rc.attack(best.location);
        if (enemies.length > 0 && rc.isActionReady()) rc.attack(null);   // AoE

        int chips = rc.getChips();
        int tp = rc.getPaint();
        int towers = rc.getNumberTowers();

        // D1: reserve exactly one ruin completion, and only while a ruin can still be claimed.
        int reserve = (towers < TOWER_CAP) ? RUIN_RESERVE : 0;
        int freeChips = chips - reserve;
        int freePaint = tp - TOWER_PAINT_KEEP;

        // Opportunistic upgrade: strictly leftover, never withheld. While ruins remain a new
        // paint tower is 1000 chips for +5 paint/turn against an upgrade's 2500 for the same.
        String upg = "";
        if (rc.getType().getBaseType() == UnitType.LEVEL_ONE_PAINT_TOWER
                && rc.getType().canUpgradeType()) {
            int need = rc.getType().getNextLevel().moneyCost;
            if (freeChips - need >= UPGRADE_SURPLUS && rc.canUpgradeTower(rc.getLocation())) {
                rc.upgradeTower(rc.getLocation());
                upg = " UPG";
                chips = rc.getChips();
                freeChips = chips - reserve;
            }
        }

        // D1c (stage 0 correction, iteration 59). THE REGIME TEST.
        //
        // Stage 0's second run traced the rewrite's actual loss mechanism, and it is not an
        // economy failure at all. carol_r1 wins the land-grab outright -- coverage 613 vs 237
        // at r500, 25 towers, 2,480 paint acts against 980 -- and then decays to 400 while the
        // incumbent climbs to 531. At r1500 its paint actions are ZERO, with towers holding
        // 4,039 paint and $9,340 chips idle. Nothing is scarce; there is simply nothing a
        // soldier is permitted to do.
        //
        // The reason is in RULES.md [E]: a soldier's attack paints a tile ONLY if it is empty
        // or already own-team. It can NEVER overwrite enemy paint. So a soldier's conversion
        // rate against contested ground is exactly zero, and the incumbent's splashers -- the
        // only unit that bulk-converts enemy paint -- turn carol_r1's territory into ground its
        // entire army is legally unable to touch. Standing there also costs 2 paint/turn
        // instead of 1, which is why 256 soldiers starved per 500 rounds while the depots were
        // full.
        //
        // So the unit mix cannot be a function of the treasury alone; it must be a function of
        // the MAP STATE. Soldiers take empty ground and claim ruins; splashers are the only
        // thing that recaptures. A tower can read which regime it is in for free -- it senses
        // its own vision disc -- so the build follows the ground rather than a fixed roll.
        UnitType want = null;
        String why = "none";
        int enemyTiles = 0, seenTiles = 0;
        for (MapInfo t : rc.senseNearbyMapInfos(-1)) {
            if (!t.isPassable()) continue;
            seenTiles++;
            if (t.getPaint().isEnemy()) enemyTiles++;
        }
        boolean contested = seenTiles > 0 && enemyTiles * 4 >= seenTiles;   // >= 25% enemy

        if (contested && tp - SPLASHER_KEEP >= UnitType.SPLASHER.paintCost
                && freeChips >= UnitType.SPLASHER.moneyCost) {
            want = UnitType.SPLASHER; why = "spl";
        } else if (freePaint >= UnitType.SOLDIER.paintCost
                   && freeChips >= UnitType.SOLDIER.moneyCost) {
            want = UnitType.SOLDIER; why = "sol";
        } else if (rc.getType().paintPerTurn == 0
                   && freePaint >= UnitType.MOPPER.paintCost
                   && freeChips >= UnitType.MOPPER.moneyCost) {
            // D1b (stage 0 correction, iteration 59). The mopper branch is for a stash that is
            // genuinely idle, and "idle" must mean idle OVER TIME, not at a snapshot. The first
            // version tested only `paint in [mopper cost, soldier cost)`, which with 25 towers
            // spawning continuously is the band a PAINT tower's stash passes through on every
            // refill cycle -- so the branch captured the majority of all builds (+113 moppers
            // against +35 soldiers per 250 rounds, and paint acts 749 against the incumbent's
            // 1645). That is doctrine 10 in the wild: a band fed by the thing it measures.
            //
            // The genuinely idle stash is a MONEY tower's. `paintPerTurn == 0` for money towers
            // [E, verified on the pinned 3.1.0 jar via tools/engine-javap.sh], so a money tower
            // holds the 500 paint it was built with and NEVER regains any -- a finite,
            // non-renewing resource where the choice really is "a cheap unit now or nothing
            // ever". A paint tower regenerates 5-15/turn and should always wait for a soldier.
            want = UnitType.MOPPER; why = "mop";
        }

        if (want != null) {
            int d0 = rng.nextInt(8);
            for (int i = 0; i < 8; i++) {
                MapLocation loc = rc.getLocation().add(DIRS[(d0 + i) & 7]);
                if (rc.canBuildRobot(want, loc)) { rc.buildRobot(want, loc); break; }
            }
        }

        return "T r=" + rc.getRoundNum() + " ch=" + chips + " tw=" + towers
             + " tp=" + tp + " fc=" + freeChips + " fp=" + freePaint
             + " want=" + why + upg + " lv=" + rc.getType().level;
    }

    // ================================================================== soldier

    static String runSoldier() throws GameActionException {
        String state = "S";
        int paint = rc.getPaint();
        if (paint == 0) dryTurns++;

        // D3: logistics come first -- a dry soldier is worth nothing at any position.
        if (handleRefill(UnitType.SOLDIER.paintCapacity)) {
            return state + " REFILL p=" + rc.getPaint();
        }

        MapLocation ruin = pickRuin();
        if (ruin != null) {
            state += " ruin=" + ruin;
            workOnRuin(ruin);
        }

        RobotInfo[] enemies = rc.senseNearbyRobots(-1, rc.getTeam().opponent());
        for (RobotInfo e : enemies) {
            if (e.type.isTowerType() && rc.canAttack(e.location)) {
                rc.attack(e.location);
                state += " hitT";
                break;
            }
        }

        moveExploring(ruin);

        if (rc.isActionReady() && rc.getPaint() >= UnitType.SOLDIER.attackCost) {
            MapLocation me = rc.getLocation();
            MapInfo myTile = rc.senseMapInfo(me);
            if (myTile.getPaint() == PaintType.EMPTY && rc.canAttack(me)) {
                rc.attack(me);
                state += " slf";
            } else {
                MapLocation tgt = null;
                int bestD = Integer.MAX_VALUE;
                for (MapInfo t : rc.senseNearbyMapInfos(9)) {
                    if (t.getPaint() != PaintType.EMPTY || !t.isPassable()) continue;
                    MapLocation l = t.getMapLocation();
                    int d = me.distanceSquaredTo(l);
                    if (d < bestD && rc.canAttack(l)) { bestD = d; tgt = l; }
                }
                if (tgt != null) { rc.attack(tgt); state += " pnt"; }
                else {
                    MapLocation f = nearestVisibleEmpty();
                    if (f != null) { explore = f; exploreAge = 0; state += " front"; }
                    else state += " idle";
                }
            }
        }
        return state + " p=" + rc.getPaint();
    }

    // ================================================================== mopper

    /**
     * D5. The mopper's job is to unblock ruins, not to mop at random. It navigates to the
     * nearest visible ruin holding enemy paint and clears it; only when no such ruin is in
     * view does it fall back to opportunistic mopping and exploration.
     */
    static String runMopper() throws GameActionException {
        String state = "M";
        if (handleRefill(UnitType.MOPPER.paintCapacity)) {
            return state + " REFILL p=" + rc.getPaint();
        }

        MapLocation me = rc.getLocation();

        // Clear enemy paint within reach first (r^2 <= 2).
        for (MapInfo t : rc.senseNearbyMapInfos(2)) {
            if (t.getPaint().isEnemy() && rc.canAttack(t.getMapLocation())) {
                rc.attack(t.getMapLocation());
                unpaints++;
                state += " mop";
                break;
            }
        }

        RobotInfo[] near = rc.senseNearbyRobots(2, rc.getTeam().opponent());
        if (near.length > 0 && rc.isActionReady()) {
            Direction card = cardinal(me.directionTo(near[0].location));
            if (rc.canMopSwing(card)) { rc.mopSwing(card); state += " swing"; }
        }

        MapLocation tgt = nearestDeniedRuin();
        if (tgt != null) { mopTargets++; state += " deny=" + tgt; }
        moveExploring(tgt);
        return state + " p=" + rc.getPaint();
    }

    /** Nearest visible tower-less ruin with at least one enemy-painted tile in its 5x5. */
    static MapLocation nearestDeniedRuin() throws GameActionException {
        MapLocation me = rc.getLocation();
        MapLocation best = null;
        int bestD = Integer.MAX_VALUE;
        for (MapLocation r : rc.senseNearbyRuins(-1)) {
            if (rc.canSenseRobotAtLocation(r)) continue;
            int d = me.distanceSquaredTo(r);
            if (d >= bestD) continue;
            for (MapInfo t : rc.senseNearbyMapInfos(r, 8)) {
                if (t.getPaint().isEnemy()) { bestD = d; best = r; break; }
            }
        }
        return best;
    }

    static Direction cardinal(Direction d) {
        switch (d) {
            case NORTHEAST: case NORTHWEST: return Direction.NORTH;
            case SOUTHEAST: case SOUTHWEST: return Direction.SOUTH;
            default: return d;
        }
    }

    // ================================================================== splasher

    static String runSplasher() throws GameActionException {
        if (handleRefill(UnitType.SPLASHER.paintCapacity)) {
            return "P REFILL p=" + rc.getPaint();
        }
        String tag = "";
        int bestScore = 0;
        if (rc.isActionReady() && rc.getPaint() >= UnitType.SPLASHER.attackCost) {
            MapLocation me = rc.getLocation();
            MapLocation best = null;
            for (MapLocation c : rc.getAllLocationsWithinRadiusSquared(me, 4)) {
                if (!rc.canAttack(c)) continue;
                int score = 0;
                for (MapInfo t : rc.senseNearbyMapInfos(c, 4)) {
                    PaintType p = t.getPaint();
                    if (p.isEnemy()) {
                        if (c.distanceSquaredTo(t.getMapLocation()) <= 2) score += 3;
                    } else if (p == PaintType.EMPTY && t.isPassable()) {
                        score += 2;
                    }
                }
                if (score > bestScore) { bestScore = score; best = c; }
            }
            if (best != null) { rc.attack(best); tag = " SPLASH"; }
            else tag = " noTgt";
        } else {
            tag = rc.isActionReady() ? " noPaint" : " cd";
        }
        moveExploring(null);
        return "P" + tag + " s=" + bestScore + " p=" + rc.getPaint();
    }

    // ================================================================== D3: logistics

    /** Record every distinct ally tower location seen, up to TOWER_MEM. */
    static void rememberTowers() throws GameActionException {
        if (!rc.getType().isRobotType() || towerN >= TOWER_MEM) return;
        for (RobotInfo t : rc.senseNearbyRobots(-1, rc.getTeam())) {
            if (!t.type.isTowerType()) continue;
            MapLocation l = t.getLocation();
            int key = (l.x << 6) | l.y;
            boolean known = false;
            for (int i = towerN; --i >= 0; ) if (towerMem[i] == key) { known = true; break; }
            if (known) continue;
            if (towerN >= TOWER_MEM) return;
            towerMem[towerN++] = key;
        }
    }

    /**
     * Withdraw from any adjacent ally tower; if below the floor, latch into REFILL mode and
     * walk to the nearest remembered tower. Returns true if the whole turn was spent on
     * logistics. Hysteresis (floor to unlatch at half capacity) stops a soldier oscillating
     * between painting one tile and walking home.
     */
    static boolean handleRefill(int cap) throws GameActionException {
        int paint = rc.getPaint();
        int low = cap / 5;                 // soldier 40 = 8 attacks; splasher 60; mopper 20
        int high = cap / 2;

        // Always top up when touching a tower, latched or not: it is free.
        if (paint < cap) {
            for (RobotInfo ally : rc.senseNearbyRobots(2, rc.getTeam())) {
                if (!ally.type.isTowerType()) continue;
                // D3b: never empty the depot. Taking everything means the first customer
                // leaves nothing for the next five, which is how stage 0 held 25 towers at
                // ~86 paint each while 321 robots starved. Half, so a tower serves a queue.
                int want = Math.min(cap - paint, ally.paintAmount / 2);
                if (want > 0 && rc.canTransferPaint(ally.location, -want)) {
                    rc.transferPaint(ally.location, -want);
                    refillTopUps++;
                    paint = rc.getPaint();
                    break;
                }
            }
        }
        if (paint >= high) { refilling = false; return false; }
        if (!refilling && paint > low) return false;
        if (!refilling) { refilling = true; refillTrips++; }

        MapLocation home = nearestRememberedTower();
        if (home == null) { refilling = false; return false; }
        if (rc.isMovementReady()) stepToward(home);
        return true;
    }

    static MapLocation nearestRememberedTower() {
        MapLocation me = rc.getLocation();
        MapLocation best = null;
        int bestD = Integer.MAX_VALUE;
        for (int i = towerN; --i >= 0; ) {
            MapLocation l = new MapLocation(towerMem[i] >> 6, towerMem[i] & 63);
            int d = me.distanceSquaredTo(l);
            if (d < bestD) { bestD = d; best = l; }
        }
        return best;
    }

    // ================================================================== ruins

    /**
     * D4. Nearest unclaimed, unbanned ruin that is not already crowded with allies. The crowd
     * test uses a single senseNearbyRobots call and filters by distance, rather than one
     * sense call per ruin.
     */
    static MapLocation pickRuin() throws GameActionException {
        MapLocation me = rc.getLocation();
        RobotInfo[] allies = rc.senseNearbyRobots(-1, rc.getTeam());
        MapLocation best = null;
        int bestD = Integer.MAX_VALUE;
        for (MapLocation r : rc.senseNearbyRuins(-1)) {
            if (rc.canSenseRobotAtLocation(r)) continue;     // tower already there
            if (ruinBanned(r)) continue;
            int d = me.distanceSquaredTo(r);
            if (d >= bestD) continue;
            int crowd = 0;
            for (RobotInfo a : allies) {
                if (a.type.isTowerType()) continue;
                if (a.getLocation().distanceSquaredTo(r) <= 8) crowd++;
            }
            if (crowd >= RUIN_CROWD) { crowdSkips++; continue; }
            bestD = d; best = r;
        }

        if (best != null && best.equals(ruinFocus)) {
            if (++ruinTurns > RUIN_PATIENCE) {
                banRuin(best);
                patienceBans++;
                ruinFocus = null; ruinTurns = 0; explore = null;
                return null;
            }
        } else {
            ruinFocus = best; ruinTurns = 0;
        }
        return best;
    }

    /** Pure function of the ruin, invariant under both map symmetries (play-symmetry). */
    static UnitType towerTypeFor(MapLocation ruin) {
        int k = Math.min(ruin.x, rc.getMapWidth() - 1 - ruin.x)
              + Math.min(ruin.y, rc.getMapHeight() - 1 - ruin.y);
        return (k % MONEY_MOD == 0) ? UnitType.LEVEL_ONE_MONEY_TOWER
                                    : UnitType.LEVEL_ONE_PAINT_TOWER;
    }

    static void workOnRuin(MapLocation ruin) throws GameActionException {
        UnitType kind = towerTypeFor(ruin);
        if (rc.canMarkTowerPattern(kind, ruin)
                && rc.senseMapInfo(ruin.add(Direction.NORTH)).getMark() == PaintType.EMPTY) {
            rc.markTowerPattern(kind, ruin);
        }

        int enemyBlock = 0, marked = 0;
        boolean acted = false;
        for (MapInfo tile : rc.senseNearbyMapInfos(ruin, 8)) {
            PaintType mark = tile.getMark();
            if (mark == PaintType.EMPTY) continue;
            marked++;
            if (mark == tile.getPaint()) continue;
            if (tile.getPaint().isEnemy()) { enemyBlock++; continue; }
            if (!acted && rc.canAttack(tile.getMapLocation())) {
                rc.attack(tile.getMapLocation(), mark == PaintType.ALLY_SECONDARY);
                acted = true;
            }
        }
        if (rc.canCompleteTowerPattern(kind, ruin)) {
            rc.completeTowerPattern(kind, ruin);
            return;
        }
        // D5 changes the meaning of this ban: it is now a TEMPORARY yield to a mopper, not a
        // permanent write-off, because carol_r1 actually fields units that can clear the tile.
        if (enemyBlock > 0 && marked > 0) {
            banRuin(ruin);
            denyBans++;
            if (ruin.equals(ruinFocus)) { ruinFocus = null; ruinTurns = 0; }
            explore = null;
        }
    }

    static boolean ruinBanned(MapLocation r) {
        int key = (r.x << 6) | r.y;
        int now = rc.getRoundNum();
        for (int i = banN; --i >= 0; ) {
            if (banLoc[i] == key) return banUntil[i] > now;
        }
        return false;
    }

    static void banRuin(MapLocation r) {
        int key = (r.x << 6) | r.y;
        int until = rc.getRoundNum() + RUIN_BAN_ROUNDS;
        for (int i = banN; --i >= 0; ) {
            if (banLoc[i] == key) { banUntil[i] = until; return; }
        }
        if (banN < BAN_CAP) { banLoc[banN] = key; banUntil[banN] = until; banN++; }
        else { int i = rng.nextInt(BAN_CAP); banLoc[i] = key; banUntil[i] = until; }
    }

    // ================================================================== movement

    static MapLocation nearestVisibleEmpty() throws GameActionException {
        MapLocation me = rc.getLocation();
        MapLocation best = null;
        int bestD = Integer.MAX_VALUE;
        for (MapInfo t : rc.senseNearbyMapInfos(-1)) {
            if (t.getPaint() != PaintType.EMPTY || !t.isPassable()) continue;
            int d = me.distanceSquaredTo(t.getMapLocation());
            if (d < bestD) { bestD = d; best = t.getMapLocation(); }
        }
        return best;
    }

    static void newExploreTarget() {
        MapLocation me = rc.getLocation();
        int w = rc.getMapWidth(), h = rc.getMapHeight();
        MapLocation best = null;
        int bestD = -1;
        for (int i = 0; i < 4; i++) {
            MapLocation c = new MapLocation(rng.nextInt(w), rng.nextInt(h));
            int d = me.distanceSquaredTo(c);
            if (d > bestD) { bestD = d; best = c; }
        }
        explore = best;
        exploreAge = 0;
    }

    static void moveExploring(MapLocation target) throws GameActionException {
        MapLocation me = rc.getLocation();
        if (me.equals(lastLoc)) stuckTurns++; else stuckTurns = 0;
        lastLoc = me;

        if (!rc.isMovementReady()) return;
        if (target != null && stepToward(target)) return;

        if (explore == null || me.distanceSquaredTo(explore) <= 8
                || stuckTurns >= 6 || ++exploreAge > 120) {
            newExploreTarget();
            stuckTurns = 0;
        }
        if (stepToward(explore)) return;
        for (int i = 0; i < 4; i++) {
            Direction d = DIRS[rng.nextInt(8)];
            if (rc.canMove(d)) { rc.move(d); return; }
        }
    }

    static boolean stepToward(MapLocation to) throws GameActionException {
        Direction d = rc.getLocation().directionTo(to);
        if (d == Direction.CENTER) return false;
        if (rc.canMove(d)) { rc.move(d); return true; }
        Direction l = d.rotateLeft(), r = d.rotateRight();
        if ((rc.getID() & 1) == 0) {
            if (rc.canMove(l)) { rc.move(l); return true; }
            if (rc.canMove(r)) { rc.move(r); return true; }
        } else {
            if (rc.canMove(r)) { rc.move(r); return true; }
            if (rc.canMove(l)) { rc.move(l); return true; }
        }
        Direction l2 = l.rotateLeft(), r2 = r.rotateRight();
        if (rc.canMove(l2)) { rc.move(l2); return true; }
        if (rc.canMove(r2)) { rc.move(r2); return true; }
        return false;
    }
}

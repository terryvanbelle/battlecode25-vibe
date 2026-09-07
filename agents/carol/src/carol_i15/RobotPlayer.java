package carol_i15;

import battlecode.common.*;

import java.util.Random;

/**
 * Carol iteration 0: minimal instrumented bot.
 * - Towers: spawn soldiers/moppers, always attack (single + AoE).
 * - Soldiers: paint own tile, finish tower patterns on ruins, hit enemy towers, wander.
 * - Moppers: mop enemy paint, swing at enemy robots, wander.
 * - Bytecode monitoring wired into every turn (overrun + near-miss in indicator string).
 */
public class RobotPlayer {
    static RobotController rc;
    static Random rng;
    static int turnCount = 0;

    // Bytecode monitoring
    static int bcOverruns = 0;      // confirmed: our logic crossed a round boundary
    static int bcNearMisses = 0;    // used > 80% of limit
    static int bcMaxUsed = 0;

    /** Chips held back from robot production so a ruin can always be completed (1000). */
    static final int CHIP_RESERVE = 1200;

    /**
     * Build tag stamped into every indicator string, so a replay containing carol and one of
     * its own snapshots can be split by team. Bump every iteration; a snapshot then freezes
     * its own tag. Play-neutral (indicator strings cannot affect the game) but NOT
     * measurement-neutral -- it shifts the replay hash, so a dose pair must share one tag if
     * doctrine #3's byte-identity check is to work on raw hashes.
     */
    static final String BUILD = "i15";

    /**
     * Consecutive turns this tower has seen the team treasury EXACTLY unchanged, and the count
     * after which CHIP_RESERVE is treated as unreachable and dropped to zero.
     *
     * Exact equality, not "did not increase": chips fall whenever anything is built, so
     * `chips <= last` would score a healthy build spree as stagnation and disarm the reserve
     * precisely when it is working. `chips == last` means income is zero AND nothing was built
     * -- the only state in which the reserve can never be reached again.
     *
     * Measured before implementing: the three carol_rush losses hold exact equality for 1887,
     * 1881 and 44 consecutive rounds; three carol_rush wins never reach 5; 21 of 22 h2h loss
     * replays never reach 5. So this fires almost only in the terminal case.
     */
    /**
     * Splasher share of the tower spawn roll, in twentieths. Iteration 11.
     *
     * Why now, after three iterations that raised unit production and converted nothing
     * (5 accepted on other grounds, 8 at 50.0%, 10 at 47.5% while fielding 4.1x the soldiers):
     * carol's soldiers are IDLE on 38.4% of their turns and paint on only 12.4%, and the single
     * largest block is IDLE-ENEMY at 22.5% -- soldiers stood beside enemy paint they physically
     * cannot convert, because a soldier paints only EMPTY or ally tiles. Splashers are the ONLY
     * unit that bulk-converts enemy paint. Carol has never built one.
     *
     * Reachability measured before writing this: a splasher costs 400 chips so the gate is
     * CHIP_RESERVE + 400 = 1600, which is met on 61.6% of tower-turns against a median treasury
     * of 2,260. Iteration 4 bundled splashers precisely because that gate then failed nearly
     * always at a 1200-1400 treasury; iteration 5's income fix removed that condition.
     *
     * Dose: 0 (zero arm) / 3 (15%) / 6 (30%, iteration 4's untested value). The real cost is
     * paint, not chips -- a splasher is 300 paint against a soldier's 200 -- so start low.
     */
    static final int SPLASHER_IN_20 = 3;

    /** Minimum splash score worth spending 50 paint on. Named so it can be a dose. */
    static final int SPLASH_MIN_SCORE = 8;

    /** Iteration 12: see TRAINING_LOG.md. Gate is computed per level, never a constant --
     *  a fixed CHIP_RESERVE+2500 would let a lv2->lv3 upgrade (5,000) strand the treasury
     *  below the ruin-completion reserve, which is how iteration 6 lost DefaultSmall. */
    static final int STAGNANT_ROUNDS = 10;
    static int lastChips = -1;
    static int stagnantTurns = 0;

    // Persistent exploration state (iteration 3).
    static MapLocation explore = null;
    static MapLocation lastLoc = null;
    static int stuckTurns = 0;
    static int exploreAge = 0;

    // --- Iteration 15: VISIT MEMORY replaces the random exploration target ------------
    // newExploreTarget() samples 4 uniformly random map coordinates and keeps the
    // farthest. It has no idea where this robot has already been, so a soldier that has
    // painted out its corner is as likely to be sent back into it as out of it. That is
    // the fallback taken on every turn iteration 14's visible-frontier check comes up
    // empty -- `frontNone`, 699-7,162 turns per game (23%-96% of idle turns).
    //
    // Rejected on measurement first (logged): remembering where EMPTY ground was SEEN
    // starves, because a robot can only learn a cell on the turns it already has a
    // visible target -- 4% of idle turns on Castle. memNone fired 8,084 times against
    // 1,250 memHit. Visit memory has the opposite density: at spawn EVERY cell is
    // unknown, and "somewhere I have never been" is exactly where unpainted ground can
    // still be. One array write per turn, no sensing, no resource.
    static final int MEM_CELL = 5;      // tiles per cell edge (<=144 cells on a 60x60 map)
    static int memW = 0, memH = 0;
    static int expNew = 0, expOld = 0;   // targets: never-visited cell / least-recent
    static int[] memSeen = null;        // last round this robot stood in each cell, 0 = never

    // Ruin persistence: a soldier that cannot finish a ruin must stop orbiting it.
    static MapLocation ruinFocus = null;   // ruin currently being worked
    static int ruinTurns = 0;              // turns spent on it
    static MapLocation ruinBanned = null;  // ruin abandoned as unfinishable
    static int ruinBanUntil = 0;           // round after which the ban lapses
    static final int RUIN_PATIENCE = 40;   // turns before giving up on a ruin
    static final int RUIN_BAN_ROUNDS = 250;

    static final Direction[] DIRS = {
        Direction.NORTH, Direction.NORTHEAST, Direction.EAST, Direction.SOUTHEAST,
        Direction.SOUTH, Direction.SOUTHWEST, Direction.WEST, Direction.NORTHWEST,
    };

    @SuppressWarnings("unused")
    public static void run(RobotController rc) throws GameActionException {
        RobotPlayer.rc = rc;
        // Seed per-robot so behavior is not correlated with team identity (play-symmetry).
        rng = new Random(rc.getID() * 7919 + 13);
        memW = (rc.getMapWidth()  + MEM_CELL - 1) / MEM_CELL;
        memH = (rc.getMapHeight() + MEM_CELL - 1) / MEM_CELL;
        memSeen = new int[memW * memH];

        while (true) {
            turnCount += 1;
            int startRound = rc.getRoundNum();
            memSeen[memIdx(rc.getLocation())] = startRound;   // iteration 15: visit memory
            String state = "";
            try {
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

    /** Bytecode monitor: compare round before/after our logic, and usage vs limit. */
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
            + " xn=" + expNew + " xo=" + expOld + " | " + state);
        Clock.yield();
    }

    // ------------------------------------------------------------------ towers

    static String runTower() throws GameActionException {
        // Attack: single-target the lowest-HP enemy robot in range, plus AoE if any enemy near.
        RobotInfo[] enemies = rc.senseNearbyRobots(-1, rc.getTeam().opponent());
        RobotInfo best = null;
        for (RobotInfo e : enemies) {
            if (rc.canAttack(e.location) && (best == null || e.health < best.health)) best = e;
        }
        if (best != null && rc.canAttack(best.location)) rc.attack(best.location);
        if (enemies.length > 0 && rc.isActionReady()) rc.attack(null); // AoE

        // Spawn: mostly soldiers, some moppers. Keep a chip reserve so that tower
        // construction (1000 chips) is never starved by robot production — iter2's trace
        // showed unreserved spawning burning the treasury to ~0 and towers falling 8 -> 3.
        // The reserve protects a 1000-chip ruin completion. Once team income has stopped it can
        // never be reached again, and holding it is strictly fatal: iteration 6 lost DefaultSmall
        // by annihilation at round 69 with 1350 chips banked and a paint tower filling to its
        // cap, because 1200 <= 1350 < 1200 + 250 left the treasury permanently between the
        // reserve and the build gate. Iteration 2's reserve stays fully armed whenever income is
        // positive -- the only regime it was ever measured in -- so this covers the unmeasured
        // regime rather than reverting it.
        int chips = rc.getChips();
        stagnantTurns = (lastChips == chips) ? stagnantTurns + 1 : 0;
        lastChips = chips;
        int reserve = (stagnantTurns >= STAGNANT_ROUNDS) ? 0 : CHIP_RESERVE;

        // Mopper share held at 25% exactly as before; the splasher share comes out of soldiers,
        // so this is one change (add splashers), not two.
        // ---- Iteration 12: upgrade THIS paint tower when chips are abundant. ----
        String upg = "";
        if (rc.getType().getBaseType() == UnitType.LEVEL_ONE_PAINT_TOWER
                && rc.getType().canUpgradeType()) {
            int need = CHIP_RESERVE + rc.getType().getNextLevel().moneyCost;
            if (chips >= need && rc.canUpgradeTower(rc.getLocation())) {
                rc.upgradeTower(rc.getLocation());
                upg = " UPG";
                chips = rc.getChips();
            } else {
                upg = (chips < need) ? " upgPoor" : " upgNo";
            }
        }

        int roll = rng.nextInt(20);
        UnitType want = (roll < SPLASHER_IN_20) ? UnitType.SPLASHER
                      : (roll < SPLASHER_IN_20 + 5) ? UnitType.MOPPER
                      : UnitType.SOLDIER;
        if (chips >= reserve + want.moneyCost) {
            Direction dir = DIRS[rng.nextInt(8)];
            MapLocation loc = rc.getLocation().add(dir);
            if (rc.canBuildRobot(want, loc)) rc.buildRobot(want, loc);
        }
        // Team-level econ trace (towers see chips + tower count; paint is per-tower).
        return "T r=" + rc.getRoundNum() + " chips=" + chips + " tw=" + rc.getNumberTowers()
             + " tp=" + rc.getPaint() + " e=" + enemies.length
             + " rsv=" + reserve + " stag=" + stagnantTurns + upg
             + " lv=" + rc.getType().level;
    }

    // ----------------------------------------------------------------- soldier

    static String runSoldier() throws GameActionException {
        String state = "S";

        // Refill if low and next to an allied tower with paint.
        refillIfPossible();

        // Try to finish a tower on a nearby ruin.
        MapLocation ruin = nearestEmptyRuin();
        if (ruin != null) {
            state += " ruin=" + ruin;
            workOnRuin(ruin);
        }

        // Attack an enemy tower if one is in reach.
        RobotInfo[] enemies = rc.senseNearbyRobots(-1, rc.getTeam().opponent());
        for (RobotInfo e : enemies) {
            if (e.type.isTowerType() && rc.canAttack(e.location)) {
                rc.attack(e.location);
                state += " hitT";
                break;
            }
        }

        // Move: prefer a direction whose destination is unpainted (expands territory).
        moveExploring(ruin);

        // Paint: own tile first if unpainted, else the nearest empty tile in action radius.
        if (rc.isActionReady() && rc.getPaint() >= UnitType.SOLDIER.attackCost) {
            MapLocation me = rc.getLocation();
            MapInfo myTile = rc.senseMapInfo(me);
            if (myTile.getPaint() == PaintType.EMPTY && rc.canAttack(me)) {
                rc.attack(me);
                state += " slf";
            } else {
                MapLocation best = null;
                int bestD = Integer.MAX_VALUE;
                for (MapInfo t : rc.senseNearbyMapInfos(9)) {
                    if (t.getPaint() != PaintType.EMPTY || !t.isPassable()) continue;
                    MapLocation l = t.getMapLocation();
                    int d = me.distanceSquaredTo(l);
                    if (d < bestD && rc.canAttack(l)) { bestD = d; best = l; }
                }
                if (best != null) { rc.attack(best); state += " pnt"; }
                else {
                    // Why is it idle? ally paint everywhere = nav problem; enemy paint in
                    // reach = capability problem (soldiers cannot overwrite enemy paint).
                    int ally = 0, foe = 0;
                    for (MapInfo t : rc.senseNearbyMapInfos(9)) {
                        PaintType p = t.getPaint();
                        if (p.isAlly()) ally++; else if (p.isEnemy()) foe++;
                    }
                    // Iteration 14: FRONTIER-SEEKING.
                    // Reaching here means nothing paintable inside the ACTION radius (r2=9) --
                    // but vision is r2=20, more than twice the area, so there is usually
                    // paintable ground in sight that this soldier simply never heads for:
                    // newExploreTarget() picks a RANDOM map coordinate with no notion of where
                    // unpainted ground is, so an idle soldier deep in our own territory wanders
                    // toward more of our own territory.
                    //
                    // Measured motivation: IDLE-ALLY is 34.9%-46.2% of soldier turns, the
                    // largest single block of waste left, and the tournament says carol loses
                    // the COVERAGE race (bob wins 49 of 53 by painting, at a median of 737
                    // rounds). This spends no resource -- it only redirects a move that was
                    // already going to happen -- which is the "capability at zero marginal
                    // cost" shape.
                    //
                    // frontFound/frontNone is the CONDITIONAL reachability counter: how often a
                    // visible empty tile exists AMONG THE TURNS THAT REACH THIS LINE. If
                    // soldiers are idle because nothing is visible either, this cannot help and
                    // the counter says so in one replay rather than one full run.
                    if (foe == 0) {
                        MapLocation f = nearestVisibleEmpty();
                        if (f != null) { explore = f; exploreAge = 0; state += " frontFound"; }
                        else state += " frontNone";
                    }
                    state += (foe > 0 ? " IDLE-ENEMY" : " IDLE-ALLY") + ally + "/" + foe;
                }
            }
        }
        return state + " p=" + rc.getPaint();
    }

    /**
     * Nearest visible ruin with no tower standing on it, excluding one we have given up
     * on. Without the give-up rule a soldier orbits an unfinishable ruin forever: the
     * ruin tile is impassable, so `stepToward` always succeeds sideways and the soldier
     * never reaches the exploration branch. iter2's trace showed a ruin in view on ~79%
     * of soldier turns, which would have left the new exploration logic mostly dormant.
     */
    static MapLocation nearestEmptyRuin() throws GameActionException {
        if (ruinBanned != null && rc.getRoundNum() > ruinBanUntil) ruinBanned = null;
        MapLocation me = rc.getLocation();
        MapLocation best = null;
        int bestD = Integer.MAX_VALUE;
        for (MapLocation r : rc.senseNearbyRuins(-1)) {
            if (rc.canSenseRobotAtLocation(r)) continue;      // tower already there
            if (r.equals(ruinBanned)) continue;               // given up on this one
            int d = me.distanceSquaredTo(r);
            if (d < bestD) { bestD = d; best = r; }
        }
        // Track how long we have been on the same ruin; abandon it if it never completes.
        if (best != null && best.equals(ruinFocus)) {
            if (++ruinTurns > RUIN_PATIENCE) {
                ruinBanned = best;
                ruinBanUntil = rc.getRoundNum() + RUIN_BAN_ROUNDS;
                ruinFocus = null; ruinTurns = 0;
                explore = null;                               // force a fresh far target
                return null;
            }
        } else {
            ruinFocus = best; ruinTurns = 0;
        }
        return best;
    }

    /**
     * Which tower to build at a ruin. Must be a pure function of the ruin so that every
     * soldier agrees every turn — two soldiers painting different patterns on one ruin
     * would deadlock it.
     *
     * Iteration 5 — roughly one ruin in three becomes a MONEY tower. iteration 3's galaxy
     * trace: chip income is exactly 30/turn (the one starting lv2 money tower, because
     * iterations 2-3 build a paint tower at every ruin), so with six towers the team builds
     * one soldier per 8.3 rounds forever while tower paint climbs +5/turn net and is never
     * spent. Chips cap the unit-production RATE; the reserve only shifts the level once
     * (iteration 4 tested that and was rejected at 40%). A ruin costs 1000 chips whichever
     * type is built, so this is income bought at zero marginal cost.
     *
     * The key is invariant under both map symmetries — reflection and 180-degree rotation
     * both preserve min(x, W-1-x) and min(y, H-1-y) — so neither team gets a different
     * build mix (play-symmetry requirement).
     *
     * History: iteration 1's trace found paint binding (213k idle chips, tower paint ~0)
     * and iteration 2 answered it by making every ruin a paint tower. That was right then;
     * it over-corrected, and this supersedes it on the new trace rather than reverting it —
     * two ruins in three are still paint towers.
     */
    static UnitType towerTypeFor(MapLocation ruin) {
        int k = Math.min(ruin.x, rc.getMapWidth() - 1 - ruin.x)
              + Math.min(ruin.y, rc.getMapHeight() - 1 - ruin.y);
        return (k % 3 == 0) ? UnitType.LEVEL_ONE_MONEY_TOWER
                            : UnitType.LEVEL_ONE_PAINT_TOWER;
    }

    static void workOnRuin(MapLocation ruin) throws GameActionException {
        UnitType kind = towerTypeFor(ruin);
        // Mark pattern once (cheap orientation: only if no mark next to ruin center yet).
        if (rc.canMarkTowerPattern(kind, ruin)
                && rc.senseMapInfo(ruin.add(Direction.NORTH)).getMark() == PaintType.EMPTY) {
            rc.markTowerPattern(kind, ruin);
        }
        // Paint marked squares to match.
        for (MapInfo tile : rc.senseNearbyMapInfos(ruin, 8)) {
            PaintType mark = tile.getMark();
            if (mark != PaintType.EMPTY && mark != tile.getPaint()) {
                if (rc.canAttack(tile.getMapLocation())) {
                    rc.attack(tile.getMapLocation(), mark == PaintType.ALLY_SECONDARY);
                    break;
                }
            }
        }
        if (rc.canCompleteTowerPattern(kind, ruin)) {
            rc.completeTowerPattern(kind, ruin);
        }
    }

    // ------------------------------------------------------------------ mopper

    static String runMopper() throws GameActionException {
        String state = "M";
        refillIfPossible();

        // Mop enemy paint / steal from enemy robots nearby.
        MapInfo[] tiles = rc.senseNearbyMapInfos(2);
        for (MapInfo t : tiles) {
            if (t.getPaint().isEnemy() && rc.canAttack(t.getMapLocation())) {
                rc.attack(t.getMapLocation());
                state += " mop";
                break;
            }
        }
        // Swing if enemies adjacent.
        RobotInfo[] enemies = rc.senseNearbyRobots(2, rc.getTeam().opponent());
        if (enemies.length > 0) {
            Direction d = rc.getLocation().directionTo(enemies[0].location);
            Direction card = cardinal(d);
            if (rc.canMopSwing(card)) { rc.mopSwing(card); state += " swing"; }
        }
        moveExploring(null);
        return state;
    }

    static Direction cardinal(Direction d) {
        switch (d) {
            case NORTHEAST: case NORTHWEST: return Direction.NORTH;
            case SOUTHEAST: case SOUTHWEST: return Direction.SOUTH;
            default: return d;
        }
    }

    // ---------------------------------------------------------------- splasher

    static String runSplasher() throws GameActionException {
        refillIfPossible();
        String tag = "";
        int bestScore = 0;
        // Splash toward the most enemy/empty paint within reach.
        boolean ready = rc.isActionReady();
        boolean fueled = rc.getPaint() >= UnitType.SPLASHER.attackCost;
        if (ready && fueled) {
            MapLocation me = rc.getLocation();
            MapLocation best = null;
            for (MapLocation c : rc.getAllLocationsWithinRadiusSquared(me, 4)) {
                if (!rc.canAttack(c)) continue;
                int score = 0;
                for (MapInfo t : rc.senseNearbyMapInfos(c, 4)) {
                    PaintType p = t.getPaint();
                    if (p.isEnemy()) {
                        // BUG FIX (this iteration): enemy paint is overwritten ONLY within
                        // r2=2 of the centre [E: RULES.md splasher attack]. The original scored
                        // enemy tiles anywhere in r2=4, so it preferred centres ringed by enemy
                        // paint it could not actually convert. Scoring a target the mechanism
                        // cannot hit would make a rejection uninterpretable, so this is part of
                        // making the mechanism testable, not a second hypothesis.
                        if (c.distanceSquaredTo(t.getMapLocation()) <= 2) score += 3;
                    } else if (p == PaintType.EMPTY && t.isPassable()) {
                        score += 2;
                    }
                }
                if (score > bestScore) { bestScore = score; best = c; }
            }
            if (best != null && bestScore >= SPLASH_MIN_SCORE) {
                rc.attack(best);
                tag = " SPLASH";
            } else {
                tag = (best == null) ? " noTgt" : " lowScore";
            }
        } else {
            // Splasher action cooldown is +50 and cooldowns fall 10/turn, so 4 turns in 5
            // after a fire are necessarily blocked -- an engine ceiling, not a bot defect.
            // Conflating that with paint starvation would misread the ceiling as a fault.
            tag = !ready ? " cd" : " noPaint";
        }
        moveExploring(null);
        // Instrumented: the old version returned a bare "P", so a splasher was invisible in
        // every replay and its mechanism gate could not be checked at all.
        return "P" + tag + " s=" + bestScore + " p=" + rc.getPaint();
    }

    // ------------------------------------------------------------------ shared

    static void refillIfPossible() throws GameActionException {
        int cap = rc.getType().paintCapacity;
        if (rc.getPaint() * 2 >= cap) return;
        for (RobotInfo ally : rc.senseNearbyRobots(2, rc.getTeam())) {
            if (ally.type.isTowerType()) {
                int want = Math.min(cap - rc.getPaint(), ally.paintAmount);
                if (want > 0 && rc.canTransferPaint(ally.location, -want)) {
                    rc.transferPaint(ally.location, -want);
                    return;
                }
            }
        }
    }

    /** Pick a fresh far-away exploration target, uniformly over the map. */
    /**
     * Nearest EMPTY passable tile anywhere in vision (r2=20), or null. Deliberately searches
     * the whole vision disc rather than the action radius: the action radius is exactly the
     * region we already know holds nothing worth painting.
     */
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

    static int memIdx(MapLocation l) { return (l.y / MEM_CELL) * memW + (l.x / MEM_CELL); }

    /**
     * Iteration 15: head for the NEAREST cell this robot has never stood in; if it has
     * been everywhere, the one it has not seen for longest. Falls back to the old random
     * pick only if the grid says nothing, which cannot happen once memW*memH > 1.
     *
     * Nearest rather than farthest is deliberate and is the opposite of what the random
     * version did (it kept the farthest of 4 samples). Unvisited ground next to us is
     * reached in a few turns and starts paying immediately; unvisited ground across the
     * map costs a long unpainting walk to reach, and a soldier that re-rolls its target
     * every 120 turns may never arrive at all.
     */
    static void newExploreTarget() {
        MapLocation me = rc.getLocation();
        int bestD = Integer.MAX_VALUE, bestOldD = Integer.MAX_VALUE, bestOld = Integer.MAX_VALUE;
        MapLocation best = null, oldest = null;
        for (int i = memSeen.length - 1; i >= 0; i--) {
            int cx = Math.min((i % memW) * MEM_CELL + MEM_CELL / 2, rc.getMapWidth() - 1);
            int cy = Math.min((i / memW) * MEM_CELL + MEM_CELL / 2, rc.getMapHeight() - 1);
            int d = (cx - me.x) * (cx - me.x) + (cy - me.y) * (cy - me.y);
            int seen = memSeen[i];
            if (seen == 0) {                       // never been here: strictly preferred
                if (d < bestD) { bestD = d; best = new MapLocation(cx, cy); }
            } else if (best == null && (seen < bestOld || (seen == bestOld && d < bestOldD))) {
                bestOld = seen; bestOldD = d; oldest = new MapLocation(cx, cy);
            }
        }
        if (best != null) expNew++; else { best = oldest; expOld++; }
        if (best == null) {                        // 1x1 grid: keep the old behaviour
            best = new MapLocation(rng.nextInt(rc.getMapWidth()), rng.nextInt(rc.getMapHeight()));
        }
        explore = best;
        exploreAge = 0;
    }

    /**
     * Move toward `target` if one is given; otherwise walk toward a persistent far
     * exploration target. The old local random walk left soldiers idle ("NOTGT": no
     * empty tile within action radius) for ~57% of their turns once the ground around
     * home was painted — a random walk cannot find the frontier on a 40x40+ map.
     */
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
        for (int i = 0; i < 4; i++) {   // fully blocked: any legal move beats standing still
            Direction d = DIRS[rng.nextInt(8)];
            if (rc.canMove(d)) { rc.move(d); return; }
        }
    }

    /** Greedy step toward `to`, trying the direct direction then widening rotations. */
    static boolean stepToward(MapLocation to) throws GameActionException {
        Direction d = rc.getLocation().directionTo(to);
        if (d == Direction.CENTER) return false;
        if (rc.canMove(d)) { rc.move(d); return true; }
        Direction l = d.rotateLeft(), r = d.rotateRight();
        // Break the left/right tie on robot ID rather than a fixed compass preference,
        // so obstacle-skirting is not correlated with team identity (play-symmetry).
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

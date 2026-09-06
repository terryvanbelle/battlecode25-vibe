package carol_i8;

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
    static final String BUILD = "i8";

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
     * Chips that must remain AFTER paying for an SRP so a ruin completion (1000 chips) is
     * never starved by one. The effective gate is 1000 + 200 = 1200 = CHIP_RESERVE exactly, so
     * an SRP is affordable precisely when the treasury is at or above the band runTower spends
     * down to: it competes with ROBOT SPAWNING and never with tower construction. That
     * competition is deliberate -- a gate of CHIP_RESERVE + 200 would sit above the treasury's
     * equilibrium and never fire, the dead-band failure this bot has already been bitten by.
     */
    static final int SRP_KEEP_CHIPS = 1000;
    static int srpBuilt = 0;

    static final int STAGNANT_ROUNDS = 10;
    static int lastChips = -1;
    static int stagnantTurns = 0;

    // Persistent exploration state (iteration 3).
    static MapLocation explore = null;
    static MapLocation lastLoc = null;
    static int stuckTurns = 0;
    static int exploreAge = 0;

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

        while (true) {
            turnCount += 1;
            int startRound = rc.getRoundNum();
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
            + " ov=" + bcOverruns + " nm=" + bcNearMisses + " | " + state);
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

        UnitType want = (rng.nextInt(4) == 0) ? UnitType.MOPPER : UnitType.SOLDIER;
        if (chips >= reserve + want.moneyCost) {
            Direction dir = DIRS[rng.nextInt(8)];
            MapLocation loc = rc.getLocation().add(dir);
            if (rc.canBuildRobot(want, loc)) rc.buildRobot(want, loc);
        }
        // Team-level econ trace (towers see chips + tower count; paint is per-tower).
        return "T r=" + rc.getRoundNum() + " chips=" + chips + " tw=" + rc.getNumberTowers()
             + " tp=" + rc.getPaint() + " e=" + enemies.length
             + " rsv=" + reserve + " stag=" + stagnantTurns;
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
                    int ally = 0, foe = 0, cen = 0;
                    for (MapInfo t : rc.senseNearbyMapInfos(9)) {
                        PaintType p = t.getPaint();
                        if (p.isAlly()) ally++; else if (p.isEnemy()) foe++;
                        if (t.isResourcePatternCenter()) cen++;
                    }
                    if (foe > 0) {
                        state += " IDLE-ENEMY" + ally + "/" + foe;
                    } else {
                        // Genuinely idle on our own paint: build economy instead of nothing.
                        state += " IDLE-ALLY" + ally + "/" + foe + workOnSRP();
                    }
                    state += " srp=" + cen + "/" + srpBuilt;
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

    /**
     * SRP centre to work on, or null if here is a bad place for one.
     *
     * Centres snap to a lattice of spacing PATTERN_SIZE anchored at the MAP CENTRE:
     *  - spacing 5 tiles the plane without overlap, so two soldiers on different centres never
     *    contend for a tile. The engine does NOT forbid overlapping SRPs (verified by
     *    disassembling isValidPatternCenter), so this has to be our own invariant.
     *  - a pure function of absolute coordinates means every soldier agrees with no comms, the
     *    same consistency argument workOnRuin needs.
     *  - anchoring at the MAP CENTRE keeps the lattice invariant under both guaranteed map
     *    symmetries, so neither team gets better-aligned sites. An origin-anchored lattice
     *    would be exactly the team-correlated absolute-order bug the play-symmetry audit
     *    exists to catch.
     * Scans the nearest few lattice points, so one blocked site does not park a soldier.
     */
    static MapLocation srpCenterNear(MapLocation me) throws GameActionException {
        int n = GameConstants.PATTERN_SIZE;
        int cx = rc.getMapWidth() / 2, cy = rc.getMapHeight() / 2;
        int bx = cx + n * Math.floorDiv(me.x - cx + n / 2, n);
        int by = cy + n * Math.floorDiv(me.y - cy + n / 2, n);
        MapLocation best = null; int bestD = Integer.MAX_VALUE;
        for (int dx = -n; dx <= n; dx += n) {
            for (int dy = -n; dy <= n; dy += n) {
                MapLocation c = new MapLocation(bx + dx, by + dy);
                int d = me.distanceSquaredTo(c);
                if (d > GameConstants.RESOURCE_PATTERN_RADIUS_SQUARED || d >= bestD) continue;
                if (c.x < 2 || c.y < 2 || c.x >= rc.getMapWidth() - 2
                        || c.y >= rc.getMapHeight() - 2) continue;      // isValidPatternCenter
                if (!srpAreaUsable(c)) continue;
                bestD = d; best = c;
            }
        }
        return best;
    }

    /**
     * Two separate requirements, both checked early so we never park on a site
     * canMarkResourcePattern will refuse forever:
     *
     * 1. The engine's areaIsPaintable: all 25 tiles free of wall and ruin.
     * 2. **No ruin within Chebyshev 4 of the centre.** This one is ours, not the engine's, and
     *    it is load-bearing. SRP marks and tower-pattern marks are the same PaintType marks on
     *    the same tiles, and workOnRuin paints whatever marks it finds within r2=8 of a ruin.
     *    Requirement 1 alone only keeps ruins out of the SRP's own 5x5, which still allows an
     *    SRP tile to sit Chebyshev 1 from a ruin -- squarely inside that ruin's tower pattern.
     *    The two would then overwrite each other's marks and deadlock the ruin, which is the
     *    exact failure iteration 6's mark-readback was built to prevent. Chebyshev >= 5
     *    between centres makes the two 5x5s disjoint.
     */
    static boolean srpAreaUsable(MapLocation c) throws GameActionException {
        for (MapLocation r : rc.senseNearbyRuins(-1)) {
            if (Math.abs(r.x - c.x) <= 4 && Math.abs(r.y - c.y) <= 4) return false;
        }
        for (MapInfo t : rc.senseNearbyMapInfos(c, 8)) {
            MapLocation l = t.getMapLocation();
            if (Math.abs(l.x - c.x) > 2 || Math.abs(l.y - c.y) > 2) continue;
            if (t.isWall() || t.hasRuin()) return false;
        }
        return true;
    }

    /**
     * Lay or advance a special resource pattern. Called ONLY on turns a soldier would
     * otherwise spend idle on friendly paint -- the IDLE-ALLY case iteration 5 measured at
     * 34,821 turns on Leaf -- so it consumes no action the bot was already using.
     *
     * Payout, read out of InternalRobot.processBeginningOfRound rather than inferred:
     *   paint tower: addPaint(paintPerTurn + 3*numSRPs)
     *   money tower: addMoney(moneyPerTurn + 3*numSRPs)
     * applied PER TOWER. A lv1 paint tower mines 5/turn, so ten SRPs make it 35 -- 7x on the
     * resource measured to be the binding one, for chips that are otherwise idle.
     */
    static String workOnSRP() throws GameActionException {
        MapLocation c = srpCenterNear(rc.getLocation());
        if (c == null) return " SRP-nosite";
        if (rc.canCompleteResourcePattern(c)) {
            if (rc.getChips() < GameConstants.COMPLETE_RESOURCE_PATTERN_COST + SRP_KEEP_CHIPS)
                return " SRP-poor";
            rc.completeResourcePattern(c);
            srpBuilt++;
            return " SRP-DONE";
        }
        // Mark once, then repaint mismatched tiles. Reuses workOnRuin's proven
        // mark-then-match loop rather than decoding getResourcePattern()'s array orientation,
        // which is unverified -- one fewer thing that can be silently wrong.
        if (rc.canMarkResourcePattern(c) && rc.senseMapInfo(c).getMark() == PaintType.EMPTY) {
            rc.markResourcePattern(c);
            return " SRP-mark";
        }
        for (MapInfo t : rc.senseNearbyMapInfos(c, 8)) {
            PaintType mark = t.getMark();
            if (mark != PaintType.EMPTY && mark != t.getPaint()
                    && rc.canAttack(t.getMapLocation())) {
                rc.attack(t.getMapLocation(), mark == PaintType.ALLY_SECONDARY);
                return " SRP-paint";
            }
        }
        return " SRP-wait";
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
        // Splash toward the most enemy/empty paint within reach.
        if (rc.isActionReady() && rc.getPaint() >= UnitType.SPLASHER.attackCost) {
            MapLocation me = rc.getLocation();
            MapLocation best = null;
            int bestScore = 0;
            for (MapLocation c : rc.getAllLocationsWithinRadiusSquared(me, 4)) {
                if (!rc.canAttack(c)) continue;
                int score = 0;
                for (MapInfo t : rc.senseNearbyMapInfos(c, 4)) {
                    PaintType p = t.getPaint();
                    if (p == PaintType.EMPTY && t.isPassable()) score += 2;
                    else if (p.isEnemy()) score += 3;
                }
                if (score > bestScore) { bestScore = score; best = c; }
            }
            if (best != null && bestScore >= 8) rc.attack(best);
        }
        moveExploring(null);
        return "P";
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
    static void newExploreTarget() {
        MapLocation me = rc.getLocation();
        int w = rc.getMapWidth(), h = rc.getMapHeight();
        MapLocation best = null;
        int bestD = -1;
        for (int i = 0; i < 4; i++) {   // sample a few, keep the farthest
            MapLocation c = new MapLocation(rng.nextInt(w), rng.nextInt(h));
            int d = me.distanceSquaredTo(c);
            if (d > bestD) { bestD = d; best = c; }
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

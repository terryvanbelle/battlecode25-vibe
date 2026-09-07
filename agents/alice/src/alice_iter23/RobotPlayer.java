package alice_iter23;

import battlecode.common.*;

/**
 * Alice iteration 0: minimal instrumented bot.
 * - bytecode monitoring wired in (overrun + near-miss surfaced in indicator strings)
 * - soldiers: complete ruin tower patterns, paint own tile, wander
 * - moppers: mop enemy paint, wander
 * - towers: spawn soldiers/moppers, attack (single + AoE)
 */
public class RobotPlayer {
    static final Direction[] directions = {
        Direction.NORTH, Direction.NORTHEAST, Direction.EAST, Direction.SOUTHEAST,
        Direction.SOUTH, Direction.SOUTHWEST, Direction.WEST, Direction.NORTHWEST,
    };

    // --- instrumentation ---
    static int overruns = 0;       // confirmed bytecode overruns (round advanced mid-logic)
    static int nearMisses = 0;     // ended turn within 15% of the limit
    static int maxBc = 0;          // worst bytecode usage seen

    // --- state ---
    static int rngState;           // xorshift PRNG state (seeded from ID)
    static Direction wanderDir = null;
    static int wanderSteps = 0;

    static int rnd(int n) {        // cheap deterministic per-robot PRNG
        rngState ^= rngState << 13;
        rngState ^= rngState >>> 17;
        rngState ^= rngState << 5;
        int r = rngState % n;
        return r < 0 ? r + n : r;
    }

    @SuppressWarnings("unused")
    public static void run(RobotController rc) throws GameActionException {
        rngState = rc.getID() * 31 + 17;
        final int limit = rc.getType().isRobotType()
                ? GameConstants.ROBOT_BYTECODE_LIMIT : GameConstants.TOWER_BYTECODE_LIMIT;
        while (true) {
            int startRound = rc.getRoundNum();
            try {
                switch (rc.getType()) {
                    case SOLDIER: runSoldier(rc); break;
                    case MOPPER: runMopper(rc); break;
                    case SPLASHER: runSplasher(rc); break;
                    default: runTower(rc); break;
                }
            } catch (GameActionException e) {
                // illegal action; keep going
            } catch (Exception e) {
                // real bug; keep robot alive
            } finally {
                int bc = Clock.getBytecodeNum();
                if (bc > maxBc) maxBc = bc;
                if (rc.getRoundNum() > startRound) overruns++;
                else if (bc > limit - limit / 7) nearMisses++;
                rc.setIndicatorString("bc=" + bc + " max=" + maxBc
                        + (overruns > 0 ? " OVR=" + overruns : "")
                        + (nearMisses > 0 ? " near=" + nearMisses : ""));
                Clock.yield();
            }
        }
    }

    // ------------------------------------------------------------------ tower
    /** Chips held back so a 1000-chip tower completion can always fund (iteration 2). */
    static final int CHIP_RESERVE = 1450;

    /** Iteration 12 dose: how many steps a wandering unit holds one heading.
     *  alice_iter7 used 5+rnd(8) (mean 8.5) -- a DIFFUSIVE random walk, whose
     *  displacement after T steps grows as sqrt(T). Tournament replays show the
     *  independent lineage 'bob' reaching 14-15 towers by round 160 on gridworld
     *  (25 ruins) while this lineage stalls at 5-6 while holding $3,240 unspent.
     *  Soldiers only target ruins within vision (r^2=20) and random-walk otherwise,
     *  so unclaimed ruins are stumbled upon rather than travelled to. Raising the
     *  run length makes the walk BALLISTIC (displacement ~ T). One mechanism, one
     *  number, zero arm = alice_iter7. */
    static final int WANDER_RUN = 25;


    static void runTower(RobotController rc) throws GameActionException {
        // Iteration 4: spend idle chips upgrading myself. Chips have not been the
        // binding resource since iteration 2 ($120,840 unspent at r2000 on
        // DefaultLarge) while PAINT bounds everything: a soldier's entire output
        // is the 200 paint it was born with. Upgrading raises paint income
        // 5->10->15/turn (money 20->30->40) permanently.
        // Engine-verified: assertCanUpgradeTower only checks range + on-map, and
        // upgradeTower adds no cooldown, so a tower upgrading ITSELF (distance 0)
        // costs chips and nothing else -- no action, no turn, no cooldown.
        UnitType nextLevel = rc.getType().getNextLevel();
        if (nextLevel != null && rc.getMoney() >= nextLevel.moneyCost + CHIP_RESERVE
                && rc.canUpgradeTower(rc.getLocation())) {
            rc.upgradeTower(rc.getLocation());
        }
        // Attack: single-target the lowest-HP enemy robot in range, then AoE if any enemy near.
        RobotInfo[] enemies = rc.senseNearbyRobots(rc.getType().actionRadiusSquared, rc.getTeam().opponent());
        if (enemies.length > 0) {
            RobotInfo best = null;
            for (RobotInfo e : enemies) {
                if (best == null || e.getHealth() < best.getHealth()) best = e;
            }
            if (best != null && rc.canAttack(best.getLocation())) rc.attack(best.getLocation());
            if (rc.canAttack(null)) rc.attack(null); // AoE
        }

        // Spawn: mostly soldiers, some moppers. Keep a chip reserve so 1000-chip
        // tower completions can always fund (spawning greedily at 250/unit pins
        // money near zero and stalls tower expansion permanently).
        if (rc.getMoney() >= CHIP_RESERVE) {
            UnitType want = (rnd(4) == 0) ? UnitType.MOPPER : UnitType.SOLDIER;
            // Iteration 5: reserve tower PAINT for soldiers. Measured defect --
            // a mopper costs 100 tower paint, a soldier 200, and a tower's paint
            // income is only 5-15/turn, so the tower can fund a mopper twice as
            // often and never accumulates the 200 a soldier needs. The realized
            // army mix is therefore ~90% moppers, not the 25% this line reads as
            // (Racetrack r1750-2000: +9 soldiers vs +93 moppers). Moppers cannot
            // paint, and painted area is the win condition. Worse, the drain is an
            // ABSORBING STATE: once tower paint reaches 0 only the 100-paint mopper
            // is affordable, moppers complete no tower patterns, so paint income
            // never recovers (Mirage: dead at r200, coverage 132 -> 15 per-mille).
            // The threshold is SOLDIER.paintCost rather than a tuned constant --
            // "only build a mopper if a soldier was affordable too". Doses 50 and
            // 100 were statistically tied (they disagreed on 3 of 27 shared cells),
            // so this picks the self-calibrating form over the searched one.
            // Refusing the mopper here does NOT substitute a cheaper unit: the
            // build below simply fails and the paint accumulates until a soldier
            // is affordable, which is the intent.
            if (want == UnitType.MOPPER && rc.getPaint() < UnitType.SOLDIER.paintCost) {
                want = UnitType.SOLDIER;
            }
            int off = rnd(8);
            for (int i = 0; i < 8; i++) {
                MapLocation loc = rc.getLocation().add(directions[(i + off) % 8]);
                if (rc.canBuildRobot(want, loc)) { rc.buildRobot(want, loc); break; }
            }
        }
    }

    // ---------------------------------------------------------------- soldier
    static void runSoldier(RobotController rc) throws GameActionException {
        // Find a nearby ruin without a tower and try to complete a pattern there.
        MapLocation ruin = null;
        MapLocation[] ruins = rc.senseNearbyRuins(-1);
        MapLocation me = rc.getLocation();
        int bestD = 1 << 30;
        for (MapLocation r : ruins) {
            if (rc.canSenseRobotAtLocation(r)) continue; // tower already there
            int d = me.distanceSquaredTo(r);
            if (d < bestD) { bestD = d; ruin = r; }
        }

        if (ruin != null) {
            Direction toRuin = me.directionTo(ruin);
            tryMove(rc, toRuin);
            me = rc.getLocation();
            // Mark the pattern if not already marked. Tower type by ruin-position
            // parity: ~50/50 money/paint mix, decided by the map (identical for
            // both teams), immune to the money-at-mark-time timing artifact that
            // made every early mark a money tower.
            UnitType wantTower = ((ruin.x + ruin.y) & 1) == 0
                    ? UnitType.LEVEL_ONE_MONEY_TOWER : UnitType.LEVEL_ONE_PAINT_TOWER;
            MapLocation markCheck = ruin.subtract(toRuin);
            if (rc.canSenseLocation(markCheck)
                    && rc.senseMapInfo(markCheck).getMark() == PaintType.EMPTY
                    && rc.canMarkTowerPattern(wantTower, ruin)) {
                rc.markTowerPattern(wantTower, ruin);
            }
            // Paint marked tiles that don't match yet.
            // ITERATION 23: skip pattern tiles that currently hold ENEMY paint.
            // Engine-verified by javap: soldierAttack calls addPaint(-attackCost)
            // at offset 58 UNCONDITIONALLY, and only then bails out at offset 207
            // when the tile belongs to the other team. So attacking an enemy
            // pattern tile costs the full 5 paint and changes nothing -- and the
            // old code `break`ed on it, forfeiting the turn's area paint as well
            // and returning to the SAME tile next turn until the soldier starved.
            // canAttack is no guard: it tests range and action-readiness only.
            // Measured on Money at r300: 55 of 60 pattern attacks (91.7%) were
            // aimed at enemy paint. Clearing them is the mopper's job, which is
            // what iteration 19 accepted; the soldier just must not pay for it.
            for (MapInfo t : rc.senseNearbyMapInfos(ruin, 8)) {
                PaintType mark = t.getMark();
                if (mark != PaintType.EMPTY && mark != t.getPaint()) {
                    if (t.getPaint().isEnemy()) continue;   // refused by the engine; 5 paint for nothing
                    if (rc.canAttack(t.getMapLocation())) {
                        rc.attack(t.getMapLocation(), mark == PaintType.ALLY_SECONDARY);
                        break;
                    }
                }
            }
            // Complete whichever pattern is actually painted (the mark decided it).
            if (rc.canCompleteTowerPattern(UnitType.LEVEL_ONE_PAINT_TOWER, ruin)) {
                rc.completeTowerPattern(UnitType.LEVEL_ONE_PAINT_TOWER, ruin);
            } else if (rc.canCompleteTowerPattern(UnitType.LEVEL_ONE_MONEY_TOWER, ruin)) {
                rc.completeTowerPattern(UnitType.LEVEL_ONE_MONEY_TOWER, ruin);
            }
        } else {
            wander(rc);
        }

        // ITERATION 22: the "paint the tile under us" branch is REMOVED.
        // The iteration 22 census found it was the largest discretionary paint
        // sink (23.6% of the 200-paint tank on box, 36.0% on UnderTheSea) while
        // tower patterns received only 3.2-9.9%. `alice_pstay` then priced its
        // return directly: across 7,506 self-paints on two maps, saved/spent was
        // 0.039 and 0.052 -- it spends 5 paint to zero a 1-2/turn penalty that
        // the soldier almost never stays long enough to recoup. Ablating it
        // (alice_i22a) beat alice_iter19 19/24, sweeping 7 maps to 0.
        // The sibling opportunistic-area branch below is DELIBERATELY KEPT: the
        // same 2x2 showed removing both is catastrophic (0/24), so the two are
        // complements, not substitutes. See TRAINING_LOG iteration 22.
        MapLocation cur = rc.getLocation();
        // Spend the idle action painting the nearest empty tile in range.
        if (rc.isActionReady() && rc.getPaint() >= 15) {
            MapLocation paintTarget = null;
            int paintD = 1 << 30;
            for (MapInfo t : rc.senseNearbyMapInfos(9)) {
                if (t.getPaint() == PaintType.EMPTY && t.isPassable()) {
                    int d = cur.distanceSquaredTo(t.getMapLocation());
                    if (d < paintD && rc.canAttack(t.getMapLocation())) {
                        paintD = d;
                        paintTarget = t.getMapLocation();
                    }
                }
            }
            if (paintTarget != null) rc.attack(paintTarget);
        }
    }

    // --------------------------------------------------------------- splasher
    static void runSplasher(RobotController rc) throws GameActionException {
        // Iteration 0: splashers are never built; behave like a wanderer that splashes
        // when enough enemy paint or a tower is in reach.
        if (rc.isActionReady() && rc.getPaint() >= 60) {
            MapLocation best = null;
            int bestScore = 3; // require at least a few tiles worth
            for (MapInfo t : rc.senseNearbyMapInfos(rc.getType().actionRadiusSquared)) {
                MapLocation c = t.getMapLocation();
                if (!rc.canAttack(c)) continue;
                int score = 0;
                if (t.getPaint().isEnemy()) score += 2;
                else if (t.getPaint() == PaintType.EMPTY && t.isPassable()) score++;
                if (score > bestScore) { bestScore = score; best = c; }
            }
            if (best != null) rc.attack(best);
        }
        wander(rc);
    }

    // ----------------------------------------------------------------- mopper
    static void runMopper(RobotController rc) throws GameActionException {
        // Iteration 19: a mopper prefers enemy paint that BLOCKS a tower pattern.
        // Census over alice_iter14 self-play, samples where a soldier stands at a
        // ruin with >=20 of the 24 pattern tiles already correct: the remaining
        // tiles are ENEMY paint 87% (gridworld), 78% (UnderTheSea), 62% (box)
        // of the time. A soldier can NEVER overwrite enemy paint (engine:
        // soldierAttack paints only empty or already-ally tiles), so those
        // patterns are permanently stalled -- 637 samples sat at 22 of 24 tiles
        // against 15 that ever reached 24. Only a mopper can unblock them, and
        // today a mopper walks to the nearest enemy paint without caring whether
        // it is holding up a tower. This changes WHICH enemy paint it prefers and
        // nothing else, so it costs nothing when no pattern is blocked.
        MapLocation[] openRuins = rc.senseNearbyRuins(-1);
        int nOpen = 0;
        for (int i = 0; i < openRuins.length; i++) {
            if (!rc.canSenseRobotAtLocation(openRuins[i])) openRuins[nOpen++] = openRuins[i];
        }
        // Mop adjacent enemy paint (prefer pattern-blocking tiles, then robots).
        if (rc.isActionReady()) {
            MapLocation best = null;
            int bestPri = 3;
            for (MapInfo t : rc.senseNearbyMapInfos(2)) {
                MapLocation l = t.getMapLocation();
                if (!t.getPaint().isEnemy() || !rc.canAttack(l)) continue;
                int pri = blocksPattern(openRuins, nOpen, l) ? 0 : 2;
                if (pri == 2 && rc.canSenseRobotAtLocation(l)) pri = 1; // robot on it: steal paint
                if (pri < bestPri) { bestPri = pri; best = l; if (pri == 0) break; }
            }
            if (best != null) rc.attack(best);
        }
        // Iteration 7: walk toward the nearest enemy paint ANYWHERE in vision
        // instead of wandering. The mopper picks targets within r^2<=2 -- the 8
        // adjacent tiles -- while its vision is r^2=20, roughly 60 tiles: it has
        // been blind to ~90% of what it can see. Motivated by the starburst trace,
        // where iteration 5 painted ~2x the baseline and still lost both sides
        // because the baseline erased ~2x as much.
        MapLocation me = rc.getLocation();
        MapLocation target = null;
        int bd = 1 << 30;
        int bestPri = 1;
        for (MapInfo t : rc.senseNearbyMapInfos(-1)) {
            if (!t.getPaint().isEnemy()) continue;
            MapLocation l = t.getMapLocation();
            int pri = blocksPattern(openRuins, nOpen, l) ? 0 : 1;
            int d = me.distanceSquaredTo(l);
            if (pri < bestPri || (pri == bestPri && d < bd)) { bestPri = pri; bd = d; target = l; }
        }
        if (target == null) wander(rc);
        else if (bd > 2) tryMove(rc, me.directionTo(target));
        // bd <= 2: already in mopping range, hold position and keep mopping.
    }

    // ------------------------------------------------------------------ moves
    static void wander(RobotController rc) throws GameActionException {
        if (!rc.isMovementReady()) return;
        if (wanderDir == null || wanderSteps <= 0) {
            wanderDir = directions[rnd(8)];
            wanderSteps = WANDER_RUN;
        }
        if (rc.canMove(wanderDir)) {
            rc.move(wanderDir);
            wanderSteps--;
        } else {
            // Iteration 14: SLIDE along the obstacle, keeping the heading, instead
            // of throwing it away. Re-rolling on every block makes the effective
            // run length the mean free path between obstacles rather than
            // WANDER_RUN -- which is why iteration 12's margin was only 8 towers
            // to 5 on boxofchocolates (19.5% walls) against 15 to 4 on gridworld.
            // Randomise which side is tried first: a fixed rotate order is exactly
            // the compass-order tie-break that Phase 0 #7 warns compounds into a
            // per-side tempo edge.
            Direction l = wanderDir.rotateLeft(), r = wanderDir.rotateRight();
            if (rnd(2) == 0) { Direction t = l; l = r; r = t; }
            if (rc.canMove(l)) { rc.move(l); wanderSteps--; }
            else if (rc.canMove(r)) { rc.move(r); wanderSteps--; }
            else {
                wanderDir = directions[rnd(8)];
                wanderSteps = WANDER_RUN;
                if (rc.canMove(wanderDir)) { rc.move(wanderDir); wanderSteps--; }
            }
        }
    }

    /** Move toward dir with simple slide fallback. */
    static void tryMove(RobotController rc, Direction dir) throws GameActionException {
        if (!rc.isMovementReady() || dir == Direction.CENTER) return;
        if (rc.canMove(dir)) { rc.move(dir); return; }
        Direction l = dir.rotateLeft(), r = dir.rotateRight();
        // Randomize tie-break order to avoid systematic side bias.
        if (rnd(2) == 0) { Direction t = l; l = r; r = t; }
        if (rc.canMove(l)) { rc.move(l); return; }
        if (rc.canMove(r)) { rc.move(r); return; }
    }

    /** Is `l` inside the 5x5 tower pattern of any ruin that has no tower on it?
     *  Pattern radius is r^2 <= 8 around the ruin centre (the 5x5 box corners). */
    static boolean blocksPattern(MapLocation[] ruins, int n, MapLocation l) {
        for (int i = 0; i < n; i++) {
            if (ruins[i].distanceSquaredTo(l) <= 8) return true;
        }
        return false;
    }
}

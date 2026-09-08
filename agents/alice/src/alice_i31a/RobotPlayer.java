package alice_i31a;

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

    /** Minimum converted tiles before a splash is worth its 50 paint. A splash costs
     *  50 and a soldier pays 5 per tile, so 10 tiles is nominal break-even against a
     *  soldier -- but a soldier CANNOT take enemy ground at any price, so the enemy
     *  tiles in the score are worth more than this arithmetic admits. Unused until
     *  splashers are actually built; the dose belongs to that iteration, not this fix. */
    static final int MIN_SPLASH_TILES = 6;

    // --- instrumentation ---
    static int overruns = 0;    // confirmed bytecode overruns (round advanced mid-logic)
    static int i24Moves = 0;   // engagement counter: times the hold branch relocated
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
                if (rc.getType().isRobotType()) tryRefill(rc);
            } catch (GameActionException e) {
                // illegal action; keep going
            } catch (Exception e) {
                // real bug; keep robot alive
            } finally {
                int bc = Clock.getBytecodeNum();
                if (bc > maxBc) maxBc = bc;
                if (rc.getRoundNum() > startRound) overruns++;
                else if (bc > limit - limit / 7) nearMisses++;
                rc.setIndicatorString("i25=" + i25Refills + "/" + i25Paint + " "
                        + (rc.getType() == UnitType.MOPPER
                        ? "i24=" + i24Moves + " p=" + rc.getPaint() + " " : "")
                        + "bc=" + bc + " max=" + maxBc
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


    // ------------------------------------------------- iteration 25: refill
    /** Iteration 25: a robot WITHDRAWS a tower's SURPLUS paint.
     *
     *  `transferPaint(towerLoc, -N)` lets ANY robot draw from an ally tower within
     *  r^2 <= 2 (RULES.md line 96, engine-verified). It costs ZERO chips, so it is
     *  not gated by CHIP_RESERVE. Through 24 accepted iterations this bot has never
     *  called it -- the "whole game mechanic sat unused" failure Phase 0.2 warns of.
     *
     *  Three measurements motivate it, none collected for this purpose:
     *   - starvation is 31.1% of all deaths (iteration 24 verification);
     *   - towers hold paint >= 300 on 3.0-6.8% of tower-turns, unspendable because
     *     the chip gate is shut (tower census, 80,752 tower-turns, 3 maps);
     *   - a withdraw is legal on 4.1-4.9% of the robot-turns spent below half paint
     *     (refill census, 95,818 robot-turns, 2 maps).
     *
     *  TWO deliberate design choices, each removing a way this could cost something:
     *
     *  1. It runs AFTER the unit's normal logic, so it can only ever consume an
     *     action the unit DID NOT USE. `canTransferPaint` is false once the action
     *     is spent, so a soldier that painted, marked or completed a pattern this
     *     turn is untouched. A starving unit is exactly the unit with nothing to
     *     spend its action on -- at 0 paint it cannot paint at all. This is the
     *     iteration-24 pattern: capability preserved at zero marginal cost.
     *
     *  2. It takes only the tower's surplus ABOVE one soldier (`SOLDIER.paintCost`),
     *     so it can never consume the paint a soldier build needed. That is the idle
     *     band the tower census measured, and nothing else. Self-calibrating, like
     *     iteration 5's "only build a mopper if a soldier was affordable too" --
     *     no tuned dose to overfit.
     *
     *  Amount is exactly `min(capacity - paint, surplus)`: RULES.md line 99 records
     *  the engine TRAP that a withdraw credits via `addPaint` (which CLAMPS at
     *  capacity) while debiting the tower the FULL amount, so over-asking silently
     *  burns the tower's paint. */
    static int i25Refills, i25Paint;

    static void tryRefill(RobotController rc) throws GameActionException {
        int cap = rc.getType().paintCapacity;
        int p = rc.getPaint();
        if (p * 2 >= cap) return;               // not hungry
        if (!rc.isActionReady()) return;        // action already used: never displace it
        RobotInfo[] near = rc.senseNearbyRobots(2, rc.getTeam());
        int bestAmt = 0;
        MapLocation bestLoc = null;
        for (int i = 0; i < near.length; i++) {
            RobotInfo t = near[i];
            if (!t.getType().isTowerType()) continue;
            int surplus = t.getPaintAmount() - UnitType.SOLDIER.paintCost;
            if (surplus <= 0) continue;
            int amt = cap - p;
            if (surplus < amt) amt = surplus;   // never over-ask: the clamp TRAP burns paint
            if (amt > bestAmt && rc.canTransferPaint(t.getLocation(), -amt)) {
                bestAmt = amt; bestLoc = t.getLocation();
            }
        }
        if (bestLoc != null) {
            rc.transferPaint(bestLoc, -bestAmt);
            i25Refills++; i25Paint += bestAmt;
        }
    }

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
            // ITERATION 28: spend a RUNAWAY chip surplus on SPLASHERS.
            //
            // The gap this closes is structural, not a tuning matter. RULES.md: a
            // soldier "cannot overwrite enemy paint" and a mopper only clears a tile
            // to EMPTY; the ONLY unit I can field that takes enemy-painted ground is
            // the splasher (enemy paint overwritten within r^2 <= 2 of the centre).
            // Through 25 accepted iterations this bot has built ZERO splashers -- spl0
            // on every sampled round of every game traced.
            //
            // The cost of that shows up as a COVERAGE STALL. On Barcode the winning
            // side's coverage is flat from r500 to r2000 -- 1,500 rounds, 75% of the
            // game, oscillating 611-638 with no trend -- while its chips run from
            // $2,700 to $154,040. It has stopped being able to gain ground and cannot
            // spend its way out, because every remaining tile is enemy paint and it
            // fields nothing that can take it.
            //
            // The threshold is the engine's own largest single purchase: a level-3
            // tower upgrade costs 5,000 chips, so "CHIP_RESERVE + 5000" means chips in
            // excess of anything else the game lets me buy. Not a searched constant --
            // the same self-calibrating discipline as iteration 5's "only build a
            // mopper if a soldier was affordable too" and iteration 25's reserve.
            //
            // REGIME-MATCHED BY CONSTRUCTION (doctrine rule 4). Probe evidence, from
            // alice_splashprobe on four maps: on AlarmClock, Castle and Circuit the
            // gate NEVER fired (spl0) because those games end before a surplus forms,
            // so the build is byte-for-byte iteration 25 there. On DefaultHuge it fired
            // hard -- 30 splashers by r1000, 48 by r1500 -- and coverage went
            // 438 -> 556 -> 688 while the baseline's COLLAPSED 538 -> 413 -> 282.
            // ITERATION 29: lower the gate from an L3 upgrade (5000) to an L2 (2500), to
            // reach the 31 maps that split under iteration 28 -- i.e. never fired at all.
            // Deliberately walks toward iteration 26 cliff: a splasher costs 400 CHIPS and
            // completeTowerPattern gates on getMoney() >= 1000, so this is only safe while
            // the threshold still sits past the end of expansion.
            if (rc.getMoney() >= CHIP_RESERVE + 2500) want = UnitType.SPLASHER;
            int off = rnd(8);
            for (int i = 0; i < 8; i++) {
                MapLocation loc = rc.getLocation().add(directions[(i + off) % 8]);
                if (rc.canBuildRobot(want, loc)) { rc.buildRobot(want, loc); break; }
            }
        }
    }

    // ---------------------------------------------------------------- soldier
    /** ARM B -- the larger dose. Reuses the hunger line ALREADY in tryRefill
     *  (below half capacity), so it introduces no new constant either, but it
     *  diverts a soldier that can still paint. This is the arm that carries
     *  iteration 26's risk: pull too many painters off the map and coverage falls.
     */
    static boolean REFILL_WALK(RobotController rc) {
        return rc.getPaint() * 2 < rc.getType().paintCapacity;
    }

    /** ITERATION 30: walk to a tower when out of paint, instead of wandering dry.
     *
     *  MEASURED, not guessed (alice_refillprobe, 3 self-play games, counters read
     *  off the replay indicator strings). At tryRefill's call site a soldier is
     *  hungry on 13-30% of its turns; on 50-93% of those hungry turns its ACTION
     *  is still free; and a tower with spare paint is ADJACENT on 0.0%, 1.0% and
     *  0.0% of them. Adjacency is the binding guard by two orders of magnitude,
     *  which kills the one-line "move tryRefill earlier" fix outright -- the
     *  action guard was never what stopped it. The unit has to close the distance.
     *
     *  And the distance has to be paid for out of MOVEMENT, because wander()
     *  already spends the movement every single turn. Appending a walk after the
     *  role runs would be inert for exactly the reason the refill is inert, so
     *  this runs BEFORE the role and returns true to pre-empt it.
     *
     *  @return true if the soldier was redirected this turn (caller must return).
     */
    static boolean goRefill(RobotController rc) throws GameActionException {
        if (!REFILL_WALK(rc)) return false;
        MapLocation me = rc.getLocation();
        RobotInfo[] near = rc.senseNearbyRobots(-1, rc.getTeam());
        MapLocation tgt = null;
        int bestD = 1 << 30;
        for (int i = 0; i < near.length; i++) {
            RobotInfo t = near[i];
            if (!t.getType().isTowerType()) continue;
            if (t.getPaintAmount() - UnitType.SOLDIER.paintCost <= 0) continue;
            int d = me.distanceSquaredTo(t.getLocation());
            if (d <= 2) return false;            // already adjacent: tryRefill handles it
            if (d < bestD) { bestD = d; tgt = t.getLocation(); }
        }
        if (tgt == null) return false;           // no tower in sight: nothing to walk to
        // ITERATION 31: return the MOVE's success. A soldier boxed in moved nowhere, so
        // pre-empting its role would spend the turn on nothing at all.
        return tryMove(rc, me.directionTo(tgt));
    }

    static void runSoldier(RobotController rc) throws GameActionException {
        // ITERATION 31: walk AND paint. goRefill spends only the MOVEMENT; movement and
        // the action are independent in this engine, so a commuting soldier that still
        // holds paint keeps painting the whole way home. Iteration 30b threw that action
        // away by returning here, which means its measured +10 net swept was a LOWER
        // BOUND on the mechanism rather than its value. The divert predicate is
        // UNCHANGED, so this must not move where the mechanism fires -- only what it
        // costs. That is the pre-registered prediction and the way to falsify this.
        goRefill(rc);
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
        // BUG FIX (2026-09-08). The previous version could never attack at all:
        // `bestScore` started at 3 while `score` was computed from the single CENTRE
        // tile and could only reach 2, so `score > bestScore` was never true and
        // `best` stayed null on every turn of every game. The threshold had been
        // written for an AoE FOOTPRINT sum ("a few tiles worth" -- its own comment)
        // but the sum was never taken. Splashers are never built today, so this is
        // dormant and the fix is behaviourally inert until one is spawned; it is
        // separated from any decision to build them precisely so that change can be
        // measured on its own.
        //
        // Engine semantics (RULES.md, verified): centre within dist^2<=4; every tile
        // within r^2<=4 of the centre gets painted if EMPTY or ally, but ENEMY paint
        // is overwritten ONLY within r^2<=2. That inner disc is the whole reason this
        // unit matters: a soldier can NEVER overwrite enemy paint, and a mopper only
        // clears one tile to EMPTY. So enemy tiles inside r^2<=2 are scored double --
        // they are ground no other unit I field can take.
        if (rc.isActionReady() && rc.getPaint() >= 60) {
            MapLocation best = null;
            int bestScore = MIN_SPLASH_TILES;   // real footprint threshold now
            for (MapInfo t : rc.senseNearbyMapInfos(rc.getType().actionRadiusSquared)) {
                MapLocation c = t.getMapLocation();
                if (!rc.canAttack(c)) continue;
                int score = splashScore(rc, c);
                if (score > bestScore) { bestScore = score; best = c; }
            }
            if (best != null) rc.attack(best);
        }
        wander(rc);
    }

    /** Value of splashing centred on `c`, in tiles actually converted.
     *  EMPTY tile inside r^2<=4  -> +1 (ground taken)
     *  ENEMY tile inside r^2<=2  -> +2 (ground taken that NOTHING else I field can take)
     *  ally paint, walls, enemy paint outside r^2<=2 -> 0 (the splash does nothing there)
     *  Counts the DECISION's value, not a downstream outcome. */
    static int splashScore(RobotController rc, MapLocation c) throws GameActionException {
        int score = 0;
        for (int dx = -2; dx <= 2; dx++) {
            for (int dy = -2; dy <= 2; dy++) {
                int d2 = dx * dx + dy * dy;
                if (d2 > 4) continue;                 // outside the splash footprint
                MapLocation l = c.translate(dx, dy);
                if (!rc.canSenseLocation(l)) continue;
                MapInfo m = rc.senseMapInfo(l);
                if (!m.isPassable()) continue;
                PaintType pt = m.getPaint();
                if (pt == PaintType.EMPTY) score += 1;
                else if (pt.isEnemy() && d2 <= 2) score += 2;   // engine: only the inner disc
            }
        }
        return score;
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
        else standOnAllyPaint(rc, me, target);
        // bd <= 2: already in mopping range -- keep mopping, but choose the tile.
    }


    /** Iteration 24: the hold branch used to spend its movement on NOTHING.
     *
     *  A mopper's attack costs 0 paint and a mopper has no paint income, so
     *  end-of-turn upkeep is its ONLY paint sink -- and upkeep is set by the paint
     *  UNDER it: 0 on ally paint, -2 on empty, -4 on enemy (mopper doubling).
     *  Measured over 25,825 mopper-turns on 3 maps: 64.7% of my moppers die at
     *  EXACTLY 0 paint, median lifespan 80 rounds. The paint accounting closes to
     *  the engine's terrain table (observed -0.54 / -2.04 / -3.50 against a
     *  predicted 0 / -2 / -4), so terrain is the whole sink; crowding is -0.54.
     *
     *  On 33.3% of hold-turns the mopper stands on non-ally paint while a movable
     *  neighbour is ally paint. This steps onto it while KEEPING the chosen target
     *  in mop range, so nothing is given up: the movement was already being wasted.
     *
     *  Engine predicate, not a proxy: the charge is waived only on ALLY paint.
     *  "not enemy" is NOT the same test -- EMPTY still costs a mopper -2/turn, and
     *  empty tiles sit under my moppers 4x more often than enemy ones. Gating on
     *  enemy paint alone measured 9.0% and would have failed its own bar. */
    static void standOnAllyPaint(RobotController rc, MapLocation me, MapLocation target)
            throws GameActionException {
        if (!rc.isMovementReady()) return;
        if (rc.senseMapInfo(me).getPaint().isAlly()) return;   // already free; nothing to do
        // Randomised start index: a fixed compass-order scan over Direction[] is
        // exactly the play-symmetry bug class the audit forbids. These candidates
        // are interchangeable (all zero-upkeep, all keep the target in range), so
        // there is no formation cohesion for randomisation to destroy here.
        int s = rnd(8);
        for (int k = 0; k < 8; k++) {
            Direction d = directions[(s + k) & 7];
            if (!rc.canMove(d)) continue;
            MapLocation l = me.add(d);
            if (l.distanceSquaredTo(target) > 2) continue;     // must still be able to mop it
            if (!rc.senseMapInfo(l).getPaint().isAlly()) continue;
            rc.move(d);
            i24Moves++;
            return;
        }
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
    /** ITERATION 31: now reports whether it actually moved. Callers that ignore the
     *  result behave exactly as before; goRefill uses it so that a soldier boxed in
     *  by walls or allies falls through to its normal role instead of wasting the turn. */
    static boolean tryMove(RobotController rc, Direction dir) throws GameActionException {
        if (!rc.isMovementReady() || dir == Direction.CENTER) return false;
        if (rc.canMove(dir)) { rc.move(dir); return true; }
        Direction l = dir.rotateLeft(), r = dir.rotateRight();
        // Randomize tie-break order to avoid systematic side bias.
        if (rnd(2) == 0) { Direction t = l; l = r; r = t; }
        if (rc.canMove(l)) { rc.move(l); return true; }
        if (rc.canMove(r)) { rc.move(r); return true; }
        return false;
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

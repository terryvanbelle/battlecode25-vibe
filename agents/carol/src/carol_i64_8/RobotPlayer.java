package carol_i64_8;

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

    // ---- Iteration 25: census-gated tower-mix override -------------------------------------
    // carol decides each ruin's tower type from a coordinate modulus. tools/towerkeyscan over
    // all 75 official maps: that key is ALL-MONEY on gridworld (21/21 ruins) and ALL-PAINT on
    // five others, and a sweep of 11 replacement keys found no non-degenerate member of the
    // family -- every alternative reassigns 40-65% of all ruins to half-fix 6 maps. So the fix
    // is not a better key; it is to stop deciding from position ALONE.
    //
    // carol has no comms and getNumberTowers() returns a count, not a composition, so no robot
    // can read the global tower mix. But a robot can accumulate a LOCAL SAMPLE of it: the
    // distinct ally towers it has ever seen, by type. Two earlier predicates were bracketed and
    // both killed by their own decision counters before costing a run:
    //     24a "no ally paint tower in vision right now" -> fired 41/41 asks on healthy ground
    //     24b "never sensed an ally paint tower ever"   -> fired  0/185 (RULES.md guarantees
    //                                                       NUMBER_INITIAL_PAINT_TOWERS = 1)
    // The census threshold below is DERIVED from the 24c instrumentation run, not guessed:
    //     map            deciding lines   fires (no guard)   fires (census >= 3)
    //     gridworld            5535            4962               4603
    //     Fossil                633              44                  0
    //     DefaultMedium         458               0                  0
    //     Bunny                  78               0                  0
    // Fossil's only firing state was a robot that had seen exactly ONE tower; requiring a
    // census of >= 3 removes it and leaves the degenerate map's firing rate essentially intact.
    static final int SEEN_CAP = 64;
    static final int CENSUS_MIN = 3;            // smallest local sample allowed to override
    static int[] seenLoc = new int[SEEN_CAP];   // (x<<6)|y of each distinct ally tower seen
    static int seenN = 0;
    static int seenPaint = 0, seenMoney = 0;
    static int mixAsk = 0, mixFlip = 0;         // instrument the DECISION, not the outcome

    /** Chips held back from robot production so a ruin can always be completed (1000). */
    static final int CHIP_RESERVE = 1200;

    /**
     * Build tag stamped into every indicator string, so a replay containing carol and one of
     * its own snapshots can be split by team. Bump every iteration; a snapshot then freezes
     * its own tag. Play-neutral (indicator strings cannot affect the game) but NOT
     * measurement-neutral -- it shifts the replay hash, so a dose pair must share one tag if
     * doctrine #3's byte-identity check is to work on raw hashes.
     */
    static final String BUILD = "i64";

    // ---- Iteration 34: fewer MONEY towers, because paint binds and chips do not -------------
    // towerTypeFor makes a ruin a money tower when k % MONEY_MOD == 0, so MONEY_MOD sets the
    // money share (~1 in MONEY_MOD). The incumbent value is 3, and it was fixed in ITERATION 5
    // from ITERATION 3's trace ("chip income is exactly 30/turn"). That is a constant from
    // iteration 3 still setting the build mix at iteration 30 -- precisely the stale-constant
    // failure LEARNINGS recorded an hour ago, and the binding resource has been re-measured
    // since, on THIS build, three separate ways:
    //   - 100.0% of chips-available no-builds are `tpIn < paintCost` (iteration 31 probe)
    //   - 63% of idle soldier turns are below half paint (iteration 32 probe)
    //   - iteration 33's tower stash collapsed to 4.4x below baseline as spending rose, while
    //     BOTH teams' chips sat idle above $2,200 (Snowglobe, round 400)
    // And RULES.md gives the mechanism: a money tower has paintPerTurn == 0, so it gains paint
    // from nothing -- not mining, and not from SRPs either. It can spawn ~2 robots from its 500
    // starting stash and is then a dry build site forever. A paint tower makes 10/turn into its
    // own stash, and buildRobot draws paint from the BUILDING tower's stash.
    static final int MONEY_MOD = 4;

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
    // Iteration 21: mopper share BELOW the incumbent 5. Run 20260907-142542 measured the dose
    // curve against a common dose-0 opponent on identical maps: dose 2 beats dose 0 by 29-11
    // (72.5%), dose 5 beats dose 0 by 26-14 (65.0%). So the curve is CONCAVE with an interior
    // optimum near 2, not monotone -- measurement doctrine #2's exact warning shape. Moppers
    // are still worth having (the zero arm loses badly: they are the cheap unit at 100 paint
    // against a soldier's 200, and mopping is carol's only way to reclaim enemy paint since
    // soldiers cannot overwrite it) -- there are simply too many of them at 5.
    static final int MOPPER_IN_20 = 2;

    /** Minimum splash score worth spending 50 paint on. Named so it can be a dose. */
    static final int SPLASH_MIN_SCORE = 8;

    /** Iteration 12: see TRAINING_LOG.md. Gate is computed per level, never a constant --
     *  a fixed CHIP_RESERVE+2500 would let a lv2->lv3 upgrade (5,000) strand the treasury
     *  below the ruin-completion reserve, which is how iteration 6 lost DefaultSmall. */
    static final int STAGNANT_ROUNDS = 10;
    static int lastChips = -1;
    static int stagnantTurns = 0;
    // Iteration 18: turns the treasury has sat in the DEAD BAND -- at or above the reserve but
    // below reserve + the cheapest unit, so the reserve alone is what blocks production.
    static int pinnedTurns = 0;
    static int pinFree = 0;      // times the dead-band escape released the reserve

    // Persistent exploration state (iteration 3).
    static MapLocation explore = null;
    static MapLocation lastLoc = null;
    static int stuckTurns = 0;
    static int exploreAge = 0;

    // Ruin persistence: a soldier that cannot finish a ruin must stop orbiting it.
    static MapLocation ruinFocus = null;   // ruin currently being worked
    static int ruinTurns = 0;              // turns spent on it
    static final int RUIN_PATIENCE = 40;   // turns before giving up on a ruin
    static final int RUIN_BAN_ROUNDS = 250;

    // ---- Iteration 44: DENIED RUINS ------------------------------------------------------
    // Measured on the 20260908-1300 tournament replays, which is the only evidence in this
    // project taken against opponents this lineage did not produce.
    //
    // A soldier commits to the nearest unclaimed ruin and works its 5x5 tower pattern. The
    // engine will not let a SOLDIER overwrite enemy paint (RULES.md, soldier attack [E]), and
    // completion is exact -- every one of the 24 non-centre tiles must hold the right colour
    // (GameWorld.checkPattern). So ONE enemy-painted tile inside the 5x5 makes the ruin
    // impossible for a soldier, permanently, until a mopper or splasher clears it. carol
    // fields no moppers at all in these games (mop0 on every map sampled) and her splashers
    // are not steered at patterns, so nothing ever clears it.
    //
    // The incumbent notices none of this. It keeps the soldier on the ruin for RUIN_PATIENCE
    // = 40 turns and then remembers exactly ONE banned ruin, so on a ruin-rich map the
    // soldier walks to the next denied ruin and the previous ban is overwritten -- it can
    // cycle among denied ruins for the whole game.
    //
    // Measured cost, from carol's own indicator strings in the tournament replays
    // (soldier-turns that are IDLE while holding a ruin target):
    //     BatSignal   14 ruins   24.8% of ALL soldier turns
    //     AlarmClock  20 ruins   35.5%
    //     Rose        30 ruins   43.2%
    // and on Rose the arena at round 176 shows ruin (20,26) with a complete carol pattern
    // except for two alice-painted tiles at (19,25) and (20,25), an alice mopper parked
    // beside it, and carol's soldiers orbiting it from round 62 to past round 210.
    //
    // This is why carol's deficit tracks RUIN COUNT rather than map area: pooled over 1,208
    // tournament games her win rate falls 43.5% -> 34.9% -> 23.1% -> 14.0% across ruin-count
    // quartiles (Cochran-Armitage trend z = -8.44), while the area effect vanishes once ruin
    // count is held fixed. A single ban slot is enough on a 10-ruin map and useless on a
    // 30-ruin one, which is exactly the shape of the gradient.
    //
    // The fix spends NO paint -- it only changes which ruin a soldier commits to. That
    // matters because the ledger closes "spend idle soldier turns on additional work" as a
    // class and allows re-opening only at literally zero paint cost. This is not even that:
    // it is a GATE CORRECTION. nearestEmptyRuin() accepts ruins it can prove uncompletable.
    static final int BAN_CAP = 8;               // remembered denied ruins, was effectively 1
    static int[] banKey = new int[BAN_CAP];     // (x<<6)|y of a banned ruin, 0 = empty slot
    static int[] banUntil = new int[BAN_CAP];   // round the ban lapses
    static int banNext = 0;                     // ring cursor when every slot is live

    // Decision counters -- link 1 of the pre-registered chain is "the predicate fires".
    static int denyBans = 0;      // ruins banned because enemy paint denies the pattern
    static int patienceBans = 0;  // ruins banned by the old 40-turn timeout
    static int banSkips = 0;      // times a candidate ruin was skipped as banned
    static int banPeak = 0;       // most simultaneously-live bans (proves >1 is needed)

    static boolean ruinBanned(MapLocation r) {
        int key = (r.x << 6) | r.y, now = rc.getRoundNum();
        for (int i = BAN_CAP; --i >= 0; )
            if (banKey[i] == key && now <= banUntil[i]) return true;
        return false;
    }

    static void banRuin(MapLocation r) {
        int key = (r.x << 6) | r.y, now = rc.getRoundNum();
        int slot = -1, live = 0;
        for (int i = BAN_CAP; --i >= 0; ) {
            if (banKey[i] == key) { slot = i; }          // refresh an existing ban
            else if (banKey[i] == 0 || now > banUntil[i]) { if (slot < 0) slot = i; }
            else live++;
        }
        if (slot < 0) { slot = banNext; banNext = (banNext + 1) % BAN_CAP; }
        banKey[slot] = key;
        banUntil[slot] = now + RUIN_BAN_ROUNDS;
        if (live + 1 > banPeak) banPeak = live + 1;
    }

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
            censusTowers();
            rememberTowers();
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
            + " ma=" + mixAsk + " mf=" + mixFlip
            + " sp=" + seenPaint + " sm=" + seenMoney
            + " rt=" + refillTrips + " ht=" + homeTurns + " dn=" + denyBans + " pb=" + patienceBans + " bs=" + banSkips + " bp=" + banPeak
            + " | " + state);
        Clock.yield();
    }

    // ------------------------------------------------------------------ towers


    // ================= ITERATION 60: D3, paint logistics with hysteresis =================
    // Ported from the REJECTED iteration-59 rewrite. The census rejected that bot's
    // ARCHITECTURE (38/150, margin -74); it never tested this mechanism against the
    // splasher-primary design, where the traced deficit actually lives.
    //
    // The deficit, measured in the post-58 splasher census with no new games: carol's splashers
    // are INERT, not starving. Of 1,363 splasher decision-turns on Leaf, 41.2% of READY turns
    // are `noPaint`, at median paint 15 against a splash cost of 50, and only 23.7% of ready
    // turns fire. A splasher below 50 has no cheaper action -- it is alive, mobile and unable to
    // act.
    //
    // The mechanism matches the deficit exactly. `transferPaint` is hardcoded r^2 <= 2 for EVERY
    // unit type [E, iteration 38], so a stranded splasher must physically walk to a tower, and
    // the incumbent has no code that ever does: `refillIfPossible` only tops up when the unit
    // already happens to be standing next to one. This walks.
    //
    // REFILL_LOW is the dose. 0 disables the branch entirely (zero arm, byte-identical play).
    static final int REFILL_LOW = 50;
    static final int TOWER_MEM = 12;
    static int[] towerMem = new int[TOWER_MEM];
    static int towerN = 0;
    static boolean refilling = false;
    static int refillTrips = 0, homeTurns = 0;

    /** Record every distinct ally tower this robot has ever seen. */
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

    /**
     * Below REFILL_LOW, latch and walk to the nearest remembered tower; unlatch at half
     * capacity. Hysteresis, so a unit does not alternate between one action and a walk home.
     * Returns true if the whole turn went to logistics.
     */
    static boolean walkHomeIfDry(int cap) throws GameActionException {
        if (REFILL_LOW <= 0) return false;                 // zero arm: mechanism disabled
        int paint = rc.getPaint();
        if (paint >= cap / 2) { refilling = false; return false; }
        if (!refilling && paint > REFILL_LOW) return false;
        if (!refilling) { refilling = true; refillTrips++; }
        MapLocation home = nearestRememberedTower();
        if (home == null) { refilling = false; return false; }
        homeTurns++;
        if (rc.isMovementReady()) stepToward(home);
        return true;
    }

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
        // Iteration 18: the existing escape hatch (iteration 6) drops the reserve when chips
        // are EXACTLY unchanged for STAGNANT_ROUNDS turns. Measured across 8 complete
        // iteration-14 games, that condition is unreachable whenever income is positive --
        // chips move by a few every turn -- and the positive-income regime is exactly where
        // the damage is: on Castle 83.4% of tower turns, DefaultLarge 79.3%, DefaultMedium
        // 64.4% sit in [CHIP_RESERVE, CHIP_RESERVE + 250). The team HOLDS a soldier's 250
        // chips (chips < 250 on 0.6% of turns) and the reserve forbids spending them, forever.
        // Iteration 6 diagnosed this exact failure -- it lost DefaultSmall by annihilation at
        // round 69 with 1350 banked -- and its guard cannot reach it. This supersedes that
        // guard on new evidence rather than reverting it: the zero-income case it covers still
        // trips stagnantTurns, and this adds the pinned-but-earning case it cannot see.
        int cheapest = UnitType.SOLDIER.moneyCost;
        boolean pinned = chips >= CHIP_RESERVE && chips < CHIP_RESERVE + cheapest;
        pinnedTurns = pinned ? pinnedTurns + 1 : 0;
        boolean freed = stagnantTurns >= STAGNANT_ROUNDS || pinnedTurns >= STAGNANT_ROUNDS;
        if (freed && pinnedTurns >= STAGNANT_ROUNDS) pinFree++;
        int reserve = freed ? 0 : CHIP_RESERVE;

        // Mopper share held at 25% exactly as before; the splasher share comes out of soldiers,
        // so this is one change (add splashers), not two.
        // ---- Iteration 12: upgrade THIS paint tower when chips are abundant. ----
        String upg = "";
        if (rc.getType().getBaseType() == UnitType.LEVEL_ONE_PAINT_TOWER
                && rc.getType().canUpgradeType()) {
            // Iteration 35: the CHIP_RESERVE term is GONE. Measured on the iteration-33 build
            // from a replay already on disk at zero VM cost: the old gate (1200 + 2500 = 3700)
            // fired 4 times against 9,147 `upgPoor` on Snowglobe -- 0.04% of eligible tower
            // turns -- because the treasury is measured to oscillate in roughly [1600, 2450]
            // and simply never reaches 3700. This is the SAME fault iteration 30 fixed for
            // splashers and was accepted on at 44/50: "50-95% of splasher rolls die at the
            // chips gate because cheaper units drain the shared treasury below it first,
            // pinning the realized share at 1.2-2.7% against an intended 15%". A gate above
            // where the treasury actually sits is not a policy, it is an off switch.
            //
            // Why drop the reserve rather than add a floor: CHIP_RESERVE exists to protect a
            // 1000-chip ruin COMPLETION from robot production. An upgrade is not robot
            // production -- it is the same class of investment the reserve protects -- so
            // charging it the reserve on top of its own 2500 cost double-counts. There is no
            // dose below this: canUpgradeTower checks affordability itself, so any `need`
            // under 2500 is identical to 2500. And there is effectively no dose above it
            // either: the measured p99 treasury is 2,600 and the max 2,800, so 3,000 would be
            // back to near-off. This axis has exactly one reachable setting.
            int need = rc.getType().getNextLevel().moneyCost;
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
                      : (roll < SPLASHER_IN_20 + MOPPER_IN_20) ? UnitType.MOPPER
                      : UnitType.SOLDIER;
        // ---- ITERATION 64: GROW, THEN HARVEST ---------------------------------------------
        // Iterations 62 and 63 killed both directions of a paint gate for four games between
        // them, and left one invariant: splasher production is pinned at 26 whether it competes
        // with 331 soldiers (carol_iter45, 9 towers held at ~42 paint) or with NONE
        // (carol_i63, 2 towers). Same ceiling, opposite routes -- which is why it looked like
        // crowding out for so long.
        //
        // Quantified, that invariant is a chicken-and-egg rather than a contention problem:
        //   carol_iter45  9 towers, ~37 paint/turn; 331x200 = 66,200 to soldiers (89%)
        //                 + 26x300 = 7,800 to splashers  -> 26 splashers
        //   carol_i63     0 soldiers -> only 2 towers, ~7 paint/turn -> 7,800  -> 26 splashers
        // Throttling soldiers frees paint and destroys the tower income that makes paint, at
        // almost exactly the same rate. No PAINT gate can separate them, because both effects
        // run through the same variable.
        //
        // Separate them in TIME instead. Soldiers exist to build towers; once enough towers
        // stand, a soldier's marginal value collapses and the accumulated income should buy the
        // unit that actually paints. `getNumberTowers()` is an EXACT team-global count, free,
        // and needs no comms [E, verified on the pinned 3.1.0 jar] -- note there is no
        // robot-count API at all, which is why a soldier CEILING is infeasible in-bot and this
        // is the observable that exists.
        if (want == UnitType.SOLDIER && rc.getNumberTowers() >= 8) {
            want = UnitType.SPLASHER;
        }
        // Iteration 30: SPLASHER FLOOR. Measured on four maps with a verified no-op decision
        // probe, 50-95% of splasher rolls die at the chips gate (1600 = CHIP_RESERVE + 400)
        // because cheaper units drain the shared treasury below it first, pinning the realized
        // splasher share at 1.2-2.7% against an intended 15%. A splasher paints 2.4-4.7x more
        // tiles per unit of BUILD paint than a soldier and costs ~4x less per tile in chips
        // (re-measured AFTER iteration 29 fixed the soldier, since the soldier is what it
        // displaces). Chips are team-shared, so every tower evaluates this identical predicate
        // and they coordinate without communicating.
        //
        // SPLASH_FLOOR IS 2000, NOT 0. An earlier version of this comment claimed "SPLASH_FLOOR = 0
        // is the current code", which was false and contradicted the line directly beneath it.
        // The value matters and is easy to misread: with reserve = CHIP_RESERVE = 1200, a SPLASHER
        // needs chips >= 1600 (it is exempt from the floor), while a SOLDIER needs
        // chips >= 1200 + 250 + 2000 = 2250 and a MOPPER >= 2300. The CHEAPER unit is gated
        // HIGHER, at a level a ~1,400-chip median treasury reaches only in spikes -- which is why
        // the realized mix is ~95% splasher / ~5% soldier, and why only 2-3 soldiers are built per
        // game. Soldiers are the only unit that calls workOnRuin, so this constant is also the
        // lineage's ruin-conversion throttle. See src/carol_conv, the archetype that sets it to 0.
        final int SPLASH_FLOOR = 2000;
        boolean afford = chips >= reserve + want.moneyCost;
        if (afford && want != UnitType.SPLASHER && chips - want.moneyCost < SPLASH_FLOOR) {
            afford = false;
        }
        // ---- Iteration 36: PAINT FLOOR. The exact analogue of iteration 30's SPLASH_FLOOR,
        // one resource over. `afford` above tests CHIPS ONLY; paint is never checked, so a
        // roll the tower cannot pay for in paint dies silently inside canBuildRobot.
        //
        // Why that inverts the mix rather than merely thinning it. Tower paint accrues at 5/turn
        // (10 once iteration 35's upgrade fires) and is capped at 1000. A mopper needs 100, a
        // soldier 200. Starting from a dry tower, the 100 line is crossed at turn ~20 and from
        // then on every mopper roll (10%) succeeds and resets the stash to ~0. To reach 200 the
        // tower must go ~40 consecutive turns without rolling a mopper: 0.9^40 = 1.5%. The cheap
        // unit does not merely get built more often -- it PREVENTS the expensive one from ever
        // being afforded. Note the chips gate cannot produce this: a mopper costs MORE chips than
        // a soldier (300 vs 250). Only the unchecked paint gate favours it.
        //
        // Measured on this lineage from tournament replays (the sanctioned cross-agent channel),
        // realized share against an intended 75% soldier / 10% mopper / 15% splasher:
        //     tower-paint median  100 -> soldier 35.0%  mopper 60.0%   (alice-carol UglySweater)
        //                         438 -> soldier 27.6%  mopper 71.4%   (bob-carol Gears)
        //                         507 -> soldier 24.7%  mopper 74.8%   (alice-carol Gears)
        //                         974 -> soldier 66.7%  mopper 25.0%   (bob-carol DefaultSmall)
        //                        2535 -> soldier 83.9%  mopper 13.8%   (bob-carol DonkeyKong)
        // The mix is set by tower paint, not by MOPPER_IN_20. And ONLY soldiers call workOnRuin,
        // so every displaced soldier is a ruin not claimed -- which is the coverage race carol
        // loses, and loses worst on large maps where towers are fewest and paint scarcest.
        //
        // The floor protects the expensive unit from the cheap one. Stated as a cost comparison
        // rather than `want == MOPPER` so it says what it means. Banking is safe: the floor is
        // 200 against a 1000 cap, so this cannot idle a tower into wasting income.
        final int PAINT_FLOOR = 200;
        if (afford && want.paintCost < UnitType.SOLDIER.paintCost
                && rc.getPaint() - want.paintCost < PAINT_FLOOR) {
            afford = false;
        }
        if (afford) {
            Direction dir = DIRS[rng.nextInt(8)];
            MapLocation loc = rc.getLocation().add(dir);
            if (rc.canBuildRobot(want, loc)) rc.buildRobot(want, loc);
        }
        // Team-level econ trace (towers see chips + tower count; paint is per-tower).
        return "T r=" + rc.getRoundNum() + " chips=" + chips + " tw=" + rc.getNumberTowers()
             + " tp=" + rc.getPaint() + " e=" + enemies.length
             + " rsv=" + reserve + " stag=" + stagnantTurns
             + " pin=" + pinnedTurns + " pf=" + pinFree + upg
             + " lv=" + rc.getType().level;
    }

    // ----------------------------------------------------------------- soldier

    static String runSoldier() throws GameActionException {
        String state = "S";

        // Refill if low and next to an allied tower with paint.
        refillIfPossible();
        if (walkHomeIfDry(UnitType.SOLDIER.paintCapacity)) return "S HOME p=" + rc.getPaint();

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
        MapLocation me = rc.getLocation();
        MapLocation best = null;
        int bestD = Integer.MAX_VALUE;
        for (MapLocation r : rc.senseNearbyRuins(-1)) {
            if (rc.canSenseRobotAtLocation(r)) continue;      // tower already there
            if (ruinBanned(r)) { banSkips++; continue; }      // given up on this one
            int d = me.distanceSquaredTo(r);
            if (d < bestD) { bestD = d; best = r; }
        }
        // Track how long we have been on the same ruin; abandon it if it never completes.
        if (best != null && best.equals(ruinFocus)) {
            if (++ruinTurns > RUIN_PATIENCE) {
                banRuin(best);
                patienceBans++;
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
    /**
     * Iteration 25. Record each DISTINCT ally tower this robot has ever seen, by type. Linear
     * scan over <= 64 remembered locations against the few towers actually in vision; peak
     * robot bytecode was 37.5% of 17500 before this, and the monitor already in the indicator
     * will surface it if that changes.
     */
    static void censusTowers() throws GameActionException {
        if (seenN >= SEEN_CAP) return;
        for (RobotInfo t : rc.senseNearbyRobots(-1, rc.getTeam())) {
            UnitType bt = t.type.getBaseType();
            int kind;
            if (bt == UnitType.LEVEL_ONE_PAINT_TOWER) kind = 1;
            else if (bt == UnitType.LEVEL_ONE_MONEY_TOWER) kind = 2;
            else continue;                       // defense tower or a mobile unit: not counted
            MapLocation l = t.getLocation();
            int key = (l.x << 6) | l.y;
            boolean known = false;
            for (int i = seenN; --i >= 0; ) if (seenLoc[i] == key) { known = true; break; }
            if (known) continue;
            if (seenN >= SEEN_CAP) return;
            seenLoc[seenN++] = key;
            if (kind == 1) seenPaint++; else seenMoney++;
        }
    }

    static UnitType towerTypeFor(MapLocation ruin) {
        int k = Math.min(ruin.x, rc.getMapWidth() - 1 - ruin.x)
              + Math.min(ruin.y, rc.getMapHeight() - 1 - ruin.y);
        // Iteration 34: MONEY_MOD replaces the literal 3. k is invariant under both map
        // symmetries and k % MONEY_MOD is a pure function of k, so the play-symmetry and
        // every-soldier-agrees properties this method depends on are both preserved.
        if (k % MONEY_MOD != 0) return UnitType.LEVEL_ONE_PAINT_TOWER;
        mixAsk++;
        // Override ONLY toward paint, and only on a local sample big enough to mean something.
        // Paint is the binding resource and RULES.md records losing the last paint tower as an
        // instant unrecoverable loss; zero chip income is survivable, and iteration 18 already
        // unpins the treasury. So the one-sided override is the cheap direction to be wrong in.
        if (seenPaint + seenMoney >= CENSUS_MIN && seenPaint * 2 < seenMoney) {
            mixFlip++;
            return UnitType.LEVEL_ONE_PAINT_TOWER;
        }
        return UnitType.LEVEL_ONE_MONEY_TOWER;
    }

    static void workOnRuin(MapLocation ruin) throws GameActionException {
        UnitType kind = towerTypeFor(ruin);
        // Mark pattern once (cheap orientation: only if no mark next to ruin center yet).
        if (rc.canMarkTowerPattern(kind, ruin)
                && rc.senseMapInfo(ruin.add(Direction.NORTH)).getMark() == PaintType.EMPTY) {
            rc.markTowerPattern(kind, ruin);
        }
        // Paint marked squares to match.
        //
        // Iteration 44 turns this loop into a DECISION as well as an action. It already had to
        // fetch all ~25 MapInfos, and iteration 29 already had to recognise an enemy-painted
        // pattern tile in order to skip it -- so counting those skips costs one int and tells
        // us something iteration 29 threw away: whether this ruin is completable AT ALL.
        int enemyBlock = 0;   // mismatched pattern tiles held by enemy paint (unfixable by us)
        int marked = 0;       // pattern tiles carrying a mark, i.e. is the pattern laid out yet
        boolean acted = false;
        for (MapInfo tile : rc.senseNearbyMapInfos(ruin, 8)) {
            PaintType mark = tile.getMark();
            if (mark == PaintType.EMPTY) continue;
            marked++;
            if (mark == tile.getPaint()) continue;
            // Iteration 29: a SOLDIER cannot overwrite enemy paint -- the engine paints a
            // tile only if it is EMPTY or already own-team (RULES.md, soldier attack [E]).
            // `canAttack` does not check this, so attacking an enemy-painted pattern tile
            // is legal, costs the full 5 paint, and does nothing. Measured on four maps
            // with a verified no-op probe: 71-85% of ALL soldier attacks were discarded
            // this way, burning 42-55% of the entire soldier paint budget, and it is the
            // sink that made the paint accounting fail to close by 41-53%. Skipping the
            // tile also lets the loop reach a pattern tile that IS paintable, instead of
            // breaking on an impossible one.
            if (tile.getPaint().isEnemy()) { enemyBlock++; continue; }
            if (!acted && rc.canAttack(tile.getMapLocation())) {
                rc.attack(tile.getMapLocation(), mark == PaintType.ALLY_SECONDARY);
                acted = true;   // one attack per turn; keep scanning to finish the census
            }
        }
        if (rc.canCompleteTowerPattern(kind, ruin)) {
            rc.completeTowerPattern(kind, ruin);
            return;
        }
        // DENIED: the pattern is laid out and at least one of its tiles is enemy paint. No
        // soldier can ever fix that tile, so every further turn spent here is dead. Leave now
        // and remember it, instead of burning the remaining RUIN_PATIENCE turns and then
        // remembering only the single most recent ruin.
        if (enemyBlock > 0 && marked > 0) {
            banRuin(ruin);
            denyBans++;
            if (ruin.equals(ruinFocus)) { ruinFocus = null; ruinTurns = 0; }
            explore = null;                                   // force a fresh far target
        }
    }

    // ------------------------------------------------------------------ mopper

    static String runMopper() throws GameActionException {
        String state = "M";
        refillIfPossible();
        if (walkHomeIfDry(UnitType.MOPPER.paintCapacity)) return "M HOME p=" + rc.getPaint();

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
        if (walkHomeIfDry(UnitType.SPLASHER.paintCapacity)) return "P HOME p=" + rc.getPaint();
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

package bobf20;

import battlecode.common.*;

/** v0 tower: attack enemies (AoE + focused), spawn a soldier-heavy mix, reserve for expansion. */
public class Tower {
    static int spawned = 0;

    /** Iteration 20 dose (bitmask over spawned%5). 0b00100 = exact zero arm. */
    static final int SPLASHER_SLOTS = 0b01100;

    /** Chips kept in hand after a self-upgrade (expansion is 1000/tower). */
    static final int UPGRADE_RESERVE = 4000;

    static void run() throws GameActionException {
        RobotController rc = G.rc;

        // 1. Attacks: AoE hits every enemy in range; single-block focuses lowest HP.
        RobotInfo[] foes = rc.senseNearbyRobots(-1, G.them);
        if (foes.length > 0) {
            if (rc.canAttack(null)) rc.attack(null);
            RobotInfo best = null;
            for (RobotInfo f : foes) {
                if (rc.canAttack(f.getLocation())
                        && (best == null || f.getHealth() < best.getHealth())) {
                    best = f;
                }
            }
            if (best != null) rc.attack(best.getLocation());
        }

        int chips = rc.getChips();

        // 2. Idle-chip conversion (iteration 3). Traced degeneracy: our chips pass
        //     8k by ~r180 and reach 327k unspent at r2000, while coverage PEAKS at
        //     r150 (~49%) and then declines to ~45% -- chips are a dead resource and
        //     paint is what actually gates production (a newly completed tower spawns
        //     with paintAmount 0, and money towers have paintPerTurn 0 so they never
        //     regain any). upgradeTower is engine-verified (RobotControllerImpl:
        //     assertCanUpgradeTower) to require only r^2<=2, ally tower, upgradable
        //     level and chips -- it consumes NO action and adds NO cooldown -- so a
        //     tower can upgrade itself on any turn it can afford to. Each level is
        //     +5 paint/turn (paint tower) or +10 chips/turn (money tower), +500 HP.
        UnitType selfType = rc.getType();
        if (selfType.canUpgradeType()
                && chips >= selfType.getNextLevel().moneyCost + UPGRADE_RESERVE) {
            MapLocation here = rc.getLocation();
            if (rc.canUpgradeTower(here)) {
                rc.upgradeTower(here);
                rc.setTimelineMarker("upgrade", 0, 128, 255);
                chips = rc.getChips();
            }
        }

        // 3. Spawning. Early game: pump units. Later: keep a reserve so soldiers can
        //    complete new towers (1000 chips) the moment a pattern is done.
        int reserve = rc.getRoundNum() <= 30 ? 0 : 1200;
        /** ITERATION 20 dose. Which of the 5 spawn slots build a SPLASHER, as a bitmask
         *  over (spawned % 5). 0b00100 = slot 2 only = the iteration-0 default 3:1:1,
         *  and is an EXACT zero arm: this expression then reduces to the original one.
         *  Motivation, measured offline over rounds 900-920 on four maps, counting the
         *  DECISION not the outcome: soldiers act on 0.4-5.2% of their turns late game
         *  (on Gears, 2441 soldier-turns produced 10 painted tiles) because the map is
         *  fully painted -- 10 of 12 maps fill by ~25% of game length -- and a SOLDIER
         *  CANNOT OVERWRITE ENEMY PAINT AT ALL. Only splashers and moppers can. Tiles
         *  converted per unit-turn, splasher : soldier = 15.1x (Gears), 8.8x
         *  (DefaultLarge), 16.4x (Money), 7.8x (Parking_lot); 5-11x per unit of paint
         *  at 300 vs 200 cost. A soldier costs the tower a full 200-paint stash and
         *  ~95% of soldier deaths are starvation, so this is paint spent re-buying
         *  units that cannot change the score. */
        int slot = spawned % 5;
        UnitType want = (slot == 4) ? UnitType.MOPPER
                       : (((SPLASHER_SLOTS >> slot) & 1) != 0 && rc.getRoundNum() > 60)
                         ? UnitType.SPLASHER
                       : UnitType.SOLDIER;
        if (chips >= want.moneyCost + reserve) {
            int start = G.rng.nextInt(8);
            for (int i = 0; i < 8; i++) {
                MapLocation l = rc.getLocation().add(G.DIRS[(start + i) & 7]);
                if (rc.canBuildRobot(want, l)) {
                    rc.buildRobot(want, l);
                    spawned++;
                    break;
                }
            }
        }
    }
}

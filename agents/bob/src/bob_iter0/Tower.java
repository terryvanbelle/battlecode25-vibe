package bob_iter0;

import battlecode.common.*;

/** v0 tower: attack enemies (AoE + focused), spawn a soldier-heavy mix, reserve for expansion. */
public class Tower {
    static int spawned = 0;

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

        // 2. Spawning. Early game: pump units. Later: keep a reserve so soldiers can
        //    complete new towers (1000 chips) the moment a pattern is done.
        int chips = rc.getChips();
        int reserve = rc.getRoundNum() <= 30 ? 0 : 1200;
        UnitType want = (spawned % 5 == 4) ? UnitType.MOPPER
                       : (spawned % 5 == 2 && rc.getRoundNum() > 60) ? UnitType.SPLASHER
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

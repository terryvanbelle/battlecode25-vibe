package bob_symprobe;

import battlecode.common.*;

/**
 * Bob v0 — minimal instrumented baseline (Iteration 0).
 * Bytecode monitoring: detects confirmed overruns (round changed during our own
 * logic) and near-misses (usage vs limit), surfaced in the indicator string.
 */
public class RobotPlayer {
    static int overruns = 0;
    static int maxBc = 0;

    public static void run(RobotController rc) {
        G.init(rc);
        Sym.init();
        boolean isTower = rc.getType().isTowerType();
        boolean symLogged = false;

        while (true) {
            int startRound = rc.getRoundNum();
            try {
                if (!isTower) Sym.observe(rc.senseNearbyMapInfos());
                if (!symLogged && Sym.alive <= 1) {
                    symLogged = true;
                    System.out.println("SYMRES type=" + rc.getType() + " born=" + Sym.born
                        + " res=" + Sym.resolvedRound + " life=" + (Sym.resolvedRound - Sym.born)
                        + " which=" + Sym.which());
                }
                if (isTower) {
                    Tower.run();
                } else {
                    switch (rc.getType()) {
                        case SOLDIER: Soldier.run(); break;
                        case MOPPER: Mopper.run(); break;
                        case SPLASHER: Splasher.run(); break;
                        default: break;
                    }
                }
            } catch (GameActionException e) {
                System.out.println("GAE@" + rc.getRoundNum() + ": " + e.getMessage());
            } catch (Exception e) {
                System.out.println("EXC@" + rc.getRoundNum() + ": " + e);
                e.printStackTrace();
            }

            // --- bytecode monitor (keep forever; see TRAINING_ALGORITHM Phase 0.6) ---
            try {
                int used = Clock.getBytecodeNum();
                if (used > maxBc) maxBc = used;
                if (rc.getRoundNum() != startRound) overruns++;
                rc.setIndicatorString("ov=" + overruns + " bc=" + used + "/" + G.myBcLimit
                    + " mx=" + maxBc + " p=" + rc.getPaint() + " " + Sym.tag());
                int r = rc.getRoundNum();
                if (r % 500 == 0 || r == GameConstants.GAME_MAX_NUMBER_OF_ROUNDS) {
                    System.out.println("BCMON " + rc.getType() + " mx=" + maxBc
                        + "/" + G.myBcLimit + " ov=" + overruns);
                }
            } catch (Exception e) { /* never die on instrumentation */ }

            Clock.yield();
        }
    }
}

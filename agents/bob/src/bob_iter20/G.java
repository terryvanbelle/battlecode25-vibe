package bob_iter20;

import battlecode.common.*;

/** Shared globals + tiny utilities. */
public class G {
    static RobotController rc;
    static java.util.Random rng;
    static Team us, them;
    static int mapW, mapH;
    static int myBcLimit;

    static final Direction[] DIRS = {
        Direction.NORTH, Direction.NORTHEAST, Direction.EAST, Direction.SOUTHEAST,
        Direction.SOUTH, Direction.SOUTHWEST, Direction.WEST, Direction.NORTHWEST,
    };

    static void init(RobotController r) {
        rc = r;
        rng = new java.util.Random(r.getID());
        us = r.getTeam();
        them = us.opponent();
        mapW = r.getMapWidth();
        mapH = r.getMapHeight();
        myBcLimit = r.getType().isTowerType()
            ? GameConstants.TOWER_BYTECODE_LIMIT : GameConstants.ROBOT_BYTECODE_LIMIT;
    }

    /** Random direction. */
    static Direction randomDir() {
        return DIRS[rng.nextInt(8)];
    }
}

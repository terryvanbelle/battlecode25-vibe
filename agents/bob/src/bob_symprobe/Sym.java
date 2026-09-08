package bob_symprobe;

import battlecode.common.*;

/**
 * PROBE ONLY -- per-robot map-symmetry inference, measured but not acted on.
 *
 * The engine has exactly three symmetries (battlecode.world.MapSymmetry:
 * ROTATIONAL, HORIZONTAL, VERTICAL -- decompiled 2026-09-08). That class lives in
 * battlecode.world, NOT battlecode.common, so it is not exposed to bots and must
 * be inferred. Phase 0.8 of the algorithm treats inferring it as standard practice.
 *
 * Local indices are TRANSFORMS, deliberately not the engine's NAMES, because
 * "HORIZONTAL" is ambiguous between "mirror across the horizontal axis" and
 * "mirror horizontally" and the bot only ever needs the transform:
 *   0 = 180-degree rotation      (x,y) -> (W-1-x, H-1-y)
 *   1 = mirror the y coordinate  (x,y) -> (x,     H-1-y)
 *   2 = mirror the x coordinate  (x,y) -> (W-1-x, y    )
 *
 * THE QUESTION THIS PROBE EXISTS TO ANSWER: memory is per-robot, and a mopper
 * lives ~86 rounds (measured today). A robot can only eliminate a hypothesis once
 * it has seen a tile AND that tile's image, so it is genuinely unclear whether a
 * single short-lived robot ever resolves the symmetry at all. Measure before
 * building anything on it.
 */
public class Sym {
    static byte[] terr;                       // 0 unknown, 1 floor, 2 wall, 3 ruin
    static boolean[] ok = {true, true, true};
    static int alive = 3;
    static int resolvedRound = -1;            // round this robot first got down to one
    static int born = -1;

    static void init() {
        terr = new byte[G.mapW * G.mapH];
        born = G.rc.getRoundNum();
    }

    static int mirror(int idx, int h) {
        int x = idx % G.mapW, y = idx / G.mapW;
        if (h == 0) { x = G.mapW - 1 - x; y = G.mapH - 1 - y; }
        else if (h == 1) { y = G.mapH - 1 - y; }
        else { x = G.mapW - 1 - x; }
        return y * G.mapW + x;
    }

    /** Feed everything in vision. Free once resolved: returns on the first line. */
    static void observe(MapInfo[] infos) {
        if (alive <= 1) return;
        for (int i = infos.length; --i >= 0; ) {
            MapInfo t = infos[i];
            MapLocation l = t.getMapLocation();
            int idx = l.y * G.mapW + l.x;
            byte c = t.isWall() ? (byte) 2 : t.hasRuin() ? (byte) 3 : (byte) 1;
            if (terr[idx] == 0) terr[idx] = c;
            for (int h = 0; h < 3; h++) {
                if (!ok[h]) continue;
                byte m = terr[mirror(idx, h)];
                if (m != 0 && m != c) { ok[h] = false; alive--; }
            }
        }
        if (alive <= 1 && resolvedRound < 0) resolvedRound = G.rc.getRoundNum();
    }

    static int which() { return ok[0] ? 0 : ok[1] ? 1 : 2; }

    static String tag() {
        return "sym[" + (ok[0] ? "R" : "-") + (ok[1] ? "Y" : "-") + (ok[2] ? "X" : "-")
             + "]n=" + alive + " born=" + born + " res=" + resolvedRound;
    }
}

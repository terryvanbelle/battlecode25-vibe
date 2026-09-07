#!/usr/bin/env python3
"""Iteration 11: give each soldier a memory of ruins it has walked past.

chooseRuin() targets only ruins inside CURRENT vision (senseNearbyRuins, r^2=20).
A soldier that cannot presently see an unoccupied ruin has no expansion target and
falls through to Nav.wander(). Measured from the iteration-9 probe: soldiers have no
ruin target on 79% (Castle) to 89% (quack) of their turns -- and the dominant loss
shape is 0-3 towers built against 10-14 in wins, on maps with 8-28 ruins.

Statics are per-robot in this engine (each robot gets its own class loader), which the
bot already relies on for workRuin/srp -- so this is per-soldier memory, not team
memory. Sharing it is the comms follow-on, deliberately not bundled here.

Usage: apply.py <capacity>    capacity 0 reproduces the current bot exactly (zero arm)
"""
import sys, pathlib

cap = int(sys.argv[1])
p = pathlib.Path(__file__).resolve().parents[3] / 'src' / 'bob' / 'Soldier.java'
s = p.read_text()

decl = "    static final int PAINT_FLOOR = 15;"
assert decl in s
s = s.replace(decl, """    // ---- ruin memory (iteration 11) ----
    static final int RUIN_MEM = %d;          // remembered ruin sites (0 = pre-iter11)
    static final MapLocation[] ruinMem = new MapLocation[RUIN_MEM];
    static int nRuinMem = 0;
%s""" % (cap, decl))

old = """        } else {
            Nav.wander();
        }"""
new = """        } else if (!seekRememberedRuin()) {
            Nav.wander();
        }"""
assert old in s
s = s.replace(old, new)

# record every unoccupied ruin we can see, inside the existing sensing loop
old2 = """            for (MapLocation r : ruins) {
                if (rc.senseRobotAtLocation(r) != null) continue; // tower already there
                int d = me.distanceSquaredTo(r);
                if (d < best) { best = d; workRuin = r; }
            }"""
new2 = """            for (MapLocation r : ruins) {
                if (rc.senseRobotAtLocation(r) != null) { forgetRuin(r); continue; }
                rememberRuin(r);
                int d = me.distanceSquaredTo(r);
                if (d < best) { best = d; workRuin = r; }
            }"""
assert old2 in s
s = s.replace(old2, new2)

helpers = """
    /** Record an unoccupied ruin we can see, if it is new and there is room. */
    static void rememberRuin(MapLocation r) {
        for (int i = nRuinMem; --i >= 0; ) if (ruinMem[i].equals(r)) return;
        if (nRuinMem < RUIN_MEM) ruinMem[nRuinMem++] = r;
    }

    /** Drop a remembered ruin once we can see a tower standing on it. */
    static void forgetRuin(MapLocation r) {
        for (int i = nRuinMem; --i >= 0; ) {
            if (ruinMem[i].equals(r)) { ruinMem[i] = ruinMem[--nRuinMem]; return; }
        }
    }

    /**
     * Walk toward the nearest remembered unoccupied ruin. Only called when nothing is
     * visible to work on, so it costs a move the bot was going to spend wandering
     * anyway -- capability at zero marginal cost, which is the recurring winner's
     * profile in TRAINING_ALGORITHM.md.
     */
    static boolean seekRememberedRuin() throws GameActionException {
        if (nRuinMem == 0) return false;
        MapLocation me = G.rc.getLocation();
        MapLocation best = null;
        int bestD = Integer.MAX_VALUE;
        for (int i = nRuinMem; --i >= 0; ) {
            int d = me.distanceSquaredTo(ruinMem[i]);
            if (d < bestD) { bestD = d; best = ruinMem[i]; }
        }
        if (best == null) return false;
        Nav.navTo(best);
        return true;
    }
"""
# insert before the final closing brace
i = s.rstrip().rfind('}')
s = s[:i] + helpers + s[i:]
p.write_text(s)
print("ruin memory capacity %d" % cap)

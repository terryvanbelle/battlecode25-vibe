#!/usr/bin/env bash
# ITERATION 41 SIZING PROBE -- instrument the SPAWN DECISION, change no behaviour.
#
# THE SUSPICION. Tower.run() picks `want` from a fixed 5-slot rotation and, if
# canBuildRobot(want, ...) fails in all 8 directions, builds NOTHING and does not
# advance `spawned`. So the tower retries the same slot next turn. The engine
# (javap, RobotControllerImpl.assertCanBuildRobot, 3.1.0) throws on
# `robot.getPaint() < type.paintCost` and on `teamMoney < type.moneyCost`, and the
# paint costs differ per type: MOPPER 100, SOLDIER 200, SPLASHER 300. A tower
# holding 200-299 paint can therefore build a soldier but NOT a splasher -- and
# 2 of the 5 slots want a splasher.
#
# Measured over the 150 bob-vs-carol games of tournament 20260909-1300, bob's mean
# tower paint sits at 185-210 for the whole game (twPaint/tw at every 25-round
# sample from r75 to r500). That is just above the soldier bar and permanently
# below the splasher bar, which is why this earns a probe rather than an assumption.
#
# WHAT THIS PROBE SEPARATES, and it is the whole point. "The tower built nothing"
# has two completely different causes and they call for opposite work:
#   R  = wanted X, could not build X, but a CHEAPER type WAS buildable
#        -> a recoverable rotation stall; the fix is a fallback and it is free.
#   N  = wanted X, could not build X, and nothing else was buildable either
#        -> genuine bankruptcy; a fallback buys nothing and the real problem is
#           upstream paint income.
# A bare count of empty tower-turns cannot tell these apart, so it would not be a
# measurement (measurement doctrine 15: check the statistic separates the benign
# case from the pathological one BEFORE building the tool).
#
# INERTNESS. The probe adds only canBuildRobot() queries (pure -- no cooldown, no
# state, no RNG) and setIndicatorString. It draws NO RNG: G.rng.nextInt(8) stays
# inside the original guard, untouched, because a PRNG draw inside a conditional
# makes that conditional part of the behaviour (LEARNING 35; LEARNING 52 is about
# skipping exactly this check). bob_sq0 is a byte-identical baseline, so the
# arm-to-arm identity check validates the instrumented build itself -- which the
# algorithm requires before believing anything an instrumented build reports.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOB="$(cd "$HERE/.." && pwd)"
cd "$BOB"

for arm in bob_sq0 bob_sq1; do
    rm -rf "src/$arm"
    cp -r src/bob "src/$arm"
    for f in "src/$arm"/*.java; do sed -i "s/^package bob;/package $arm;/" "$f"; done
done

T=src/bob_sq1/Tower.java

# 1. Record whether the build succeeded. A local boolean; no game effect.
perl -0pi -e 's/\n        if \(chips >= want\.moneyCost \+ reserve\) \{/\n        boolean built = false;\n        if (chips >= want.moneyCost + reserve) {/' "$T"
perl -0pi -e 's/rc\.buildRobot\(want, l\);\n                    spawned\+\+;/rc.buildRobot(want, l);\n                    spawned++;\n                    built = true;/' "$T"

# 2. Call the probe as the last statement of run(), and append the method.
#    Done by replacing the file's unique closing literal rather than by
#    brace-matching in a regex: an earlier version of this script matched the
#    wrong brace and closed run() one statement early. The javac check below is
#    what actually proves the splice, not the greps.
python3 - "$T" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
tail = "                    break;\n                }\n            }\n        }\n    }\n}\n"
assert s.endswith(tail), "Tower.java tail changed -- reread it and update this splice"
probe = '''                    break;
                }
            }
        }
        spawnProbe(want, built, chips, reserve);
    }

    /** PROBE ONLY. No game action, no RNG draw. Classifies this tower-turn:
     *   B built something;
     *   R wanted `want`, could not build it, but a different type WAS buildable
     *     (recoverable rotation stall -- a fallback would have produced a unit);
     *   N wanted `want`, could not build it, and no type was buildable either
     *     (genuine bankruptcy -- a fallback buys nothing here).
     *  Cumulative counters ride in the string, so one narrow replay window reads
     *  the whole game instead of a dump of every round. */
    static int tB, tR, tN;
    static final UnitType[] ALT = { UnitType.MOPPER, UnitType.SOLDIER, UnitType.SPLASHER };

    static void spawnProbe(UnitType want, boolean built, int chips, int reserve)
            throws GameActionException {
        RobotController rc = G.rc;
        char code;
        if (built) { tB++; code = 'B'; }
        else {
            boolean alt = false;
            for (UnitType t : ALT) {
                if (t == want || chips < t.moneyCost + reserve) continue;
                for (int i = 0; i < 8; i++) {
                    if (rc.canBuildRobot(t, rc.getLocation().add(G.DIRS[i]))) { alt = true; break; }
                }
                if (alt) break;
            }
            if (alt) { tR++; code = 'R'; } else { tN++; code = 'N'; }
        }
        rc.setIndicatorString("SPW " + code + " w=" + want + " p=" + rc.getPaint()
                + " B" + tB + " R" + tR + " N" + tN);
    }
}
'''
open(p, 'w').write(s[:-len(tail)] + probe)
PY

for pat in 'boolean built = false;' 'built = true;' \
           'spawnProbe(want, built, chips, reserve);' 'static int tB, tR, tN;'; do
    grep -q "$pat" "$T" || { echo "!! bob_sq1: patch did not land: $pat" >&2; exit 1; }
done
if grep -q 'spawnProbe' src/bob_sq0/Tower.java; then
    echo "!! bob_sq0 is not a clean baseline" >&2; exit 1
fi

bob-tools/compile-check.sh bob_sq0 >/dev/null
bob-tools/compile-check.sh bob_sq1 >/dev/null
echo "bob_sq0  baseline (byte-identical to src/bob)"
echo "bob_sq1  + spawn-decision probe (B/R/N), behaviour-inert, compiles"

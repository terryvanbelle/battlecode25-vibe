#!/usr/bin/env python3
"""Rebuild src/carol_i12 = current src/carol (i11) + the tower-upgrade mechanism ONLY.

Used when iteration 11 is accepted, so that iteration 12's head-to-head measures exactly one
change against the new baseline instead of "add upgrades AND remove splashers" -- the bundling
error that made iteration 4 uninterpretable.
"""
import pathlib, sys
root = pathlib.Path(__file__).resolve().parent.parent
src = (root / "src/carol/RobotPlayer.java").read_text()
s = src.replace("package carol;", "package carol_i12;", 1)
s = s.replace('static final String BUILD = "i11";', 'static final String BUILD = "i12";', 1)
if "BUILD = \"i12\"" not in s:
    sys.exit("!! BUILD tag not i11 -- src/carol is not the accepted iteration 11")

anchor = "    static final int STAGNANT_ROUNDS = 10;"
if anchor not in s: sys.exit("!! STAGNANT_ROUNDS anchor missing")
s = s.replace(anchor, """    /** Iteration 12: see TRAINING_LOG.md. Gate is computed per level, never a constant --
     *  a fixed CHIP_RESERVE+2500 would let a lv2->lv3 upgrade (5,000) strand the treasury
     *  below the ruin-completion reserve, which is how iteration 6 lost DefaultSmall. */
""" + anchor, 1)

# find the spawn roll (iteration 11 form) and insert the upgrade before it
spawn = "        int roll = rng.nextInt(20);"
if spawn not in s: sys.exit("!! iteration 11 spawn roll not found")
s = s.replace(spawn, """        // ---- Iteration 12: upgrade THIS paint tower when chips are abundant. ----
        String upg = "";
        if (rc.getType().getBaseType() == UnitType.LEVEL_ONE_PAINT_TOWER
                && rc.getType().canUpgradeType()) {
            int need = CHIP_RESERVE + rc.getType().getNextLevel().moneyCost;
            if (chips >= need && rc.canUpgradeTower(rc.getLocation())) {
                rc.upgradeTower(rc.getLocation());
                upg = " UPG";
                chips = rc.getChips();
            } else {
                upg = (chips < need) ? " upgPoor" : " upgNo";
            }
        }

""" + spawn, 1)

t = '             + " rsv=" + reserve + " stag=" + stagnantTurns;'
if t not in s: sys.exit("!! tower trace anchor missing")
s = s.replace(t, '             + " rsv=" + reserve + " stag=" + stagnantTurns + upg\n             + " lv=" + rc.getType().level;', 1)
(root / "src/carol_i12/RobotPlayer.java").write_text(s)
print("carol_i12 rebuilt from i11 (+ upgrades only)")

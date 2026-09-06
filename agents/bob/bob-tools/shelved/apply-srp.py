#!/usr/bin/env python3
"""Apply the shelved SRP mechanic to a Soldier.java, whatever its base.

The shelved iter9-srp/Soldier.java is a whole file from the iteration 3/4 era, so
copying it over would silently revert every accept since. This lifts only the SRP
fragments (constants, fields, the step-1b call, workOnSrp, srpSiteSafe) and grafts
them onto the current file, and refuses to run if the anchors it needs are missing.

Usage: apply-srp.py <path-to-Soldier.java>
"""
import re, sys, pathlib

SRC = pathlib.Path(__file__).parent / "iter9-srp" / "Soldier.java"
dst_path = pathlib.Path(sys.argv[1])
src = SRC.read_text()
dst = dst_path.read_text()

def grab(pattern, text, what):
    m = re.search(pattern, text, re.S)
    if not m:
        sys.exit(f"anchor missing in the shelved source: {what}")
    return m.group(0)

consts = grab(r"    // ---- SRP construction.*?static int srpTurns = 0;\n", src, "SRP constants")
work   = grab(r"    /\*\*\n     \* Build a Special Resource Pattern.*?\n    }\n", src, "workOnSrp")
safe   = grab(r"    /\*\*\n     \* A site is only worth starting.*?\n    }\n", src, "srpSiteSafe")

if "workOnSrp" in dst:
    sys.exit("Soldier.java already carries the SRP mechanic - nothing to do")

# 1. constants + fields, right after the class opens
anchor = "public class Soldier {\n"
if anchor not in dst:
    sys.exit("could not find the Soldier class declaration")
dst = dst.replace(anchor, anchor + "\n" + consts, 1)

# 2. the step-1b call, immediately after ruin capture
call = ("""
        // 1b. SRP construction, only when there is no ruin to capture. Uses the
        //     action and holds position (the whole 5x5 is inside the soldier's own
        //     action radius when it stands on the centre), so it returns early.
        if (workRuin == null && workOnSrp()) return;
""")
ruin_block = """        chooseRuin();
        if (workRuin != null) {
            workOnRuin();
        }
"""
if ruin_block not in dst:
    sys.exit("could not find the ruin-capture block to insert step 1b after")
dst = dst.replace(ruin_block, ruin_block + call, 1)

# 3. the two methods, before the final class brace
i = dst.rindex("}\n")
dst = dst[:i] + "\n" + work + "\n" + safe + dst[i:]

dst_path.write_text(dst)
print(f"grafted SRP onto {dst_path}: constants, step 1b, workOnSrp, srpSiteSafe")

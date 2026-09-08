#!/usr/bin/env python3
"""Apply carol's standing accept gate (adopted at commit 5443d59) to a gauntlet run.

The gate exists because the old one was set against se = 0. The engine is deterministic, so a
rerun on the same maps reproduces exactly -- but an accept asks about the map POPULATION, and a
25-of-75 draw carries real sampling variance. Measured over 59 of my own arms, a near-even
50-game arm has sd ~2.4 wins (with the finite-population correction; ~3.0 without, which is what
tools/map-resample.py's jackknife reports).

    >= 29/50  ACCEPT        <= 25/50  REJECT        26-28  UNRESOLVED
    (unresolved may not accept without a replication on a DISJOINT map sample)

D (split maps) and the swept counts are REPORTED, never gated: wins - N == SW - SL is an exact
identity, so a swept-count condition is the margin written twice. The one thing sweeps add is D,
decisiveness -- and an absolute floor on SW is not resolvable either (among my dead-even arms SW
ran as high as 9).

  gateverdict.py <run-dir> <baseline-opponent> [other-opponent ...]
"""
import csv, os, sys, math, collections

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
N_POP, N_DRAW = 75, 25
BINS = [(0, 1999, "small"), (2000, 10**9, "large")]

def areas():
    a = {}
    for line in open(os.path.join(REPO, "tools", "mapdata", "ruin_parity.txt")):
        if line.startswith("#") or not line.strip(): continue
        f = line.split()
        for tok in f[1:]:
            if "x" in tok:
                try:
                    w, h = tok.split("x"); a[f[0]] = int(w) * int(h)
                except ValueError: pass
                break
    return a

def arm(run, opp):
    mw, ng = collections.defaultdict(int), collections.defaultdict(int)
    for r in csv.DictReader(open(os.path.join(run, "results.csv"))):
        if r["opponent"] != opp: continue
        mw[r["map"]] += 1 if r["bot_result"] == "win" else 0
        ng[r["map"]] += 1
    maps = [m for m in mw if ng[m] == 2]
    return maps, mw

def report(run, opp, A, primary):
    maps, mw = arm(run, opp)
    n = len(maps)
    if n == 0:
        print(f"  {opp}: no complete both-sides pairs"); return
    w = [mw[m] for m in maps]
    wins, mean = sum(w), sum(w)/n
    s2 = sum((x-mean)**2 for x in w)/(n-1) if n > 1 else 0.0
    fpc = (N_POP - n)/(N_POP - 1)
    sd, sd_inf = math.sqrt(n*s2*fpc), math.sqrt(n*s2)
    SW = sum(1 for x in w if x == 2); SL = sum(1 for x in w if x == 0); D = n - SW - SL
    z = (wins - n)/sd if sd else float('inf') if wins != n else 0.0
    print(f"  {opp:<18} {wins}/{2*n}   sd {sd:.2f} (fpc) / {sd_inf:.2f} (no fpc)   "
          f"{z:+.2f} sd from the mirror null")
    print(f"  {'':<18} SW {SW}  SL {SL}  D {D}  ({100*D/n:.0f}% of maps split by spawn side)"
          f"   [identity wins-N == SW-SL: {wins-n == SW-SL}]")
    for lo, hi, lbl in BINS:
        sel = [m for m in maps if lo <= A.get(m, 0) <= hi]
        if not sel: continue
        sw2 = sum(mw[m] for m in sel)
        print(f"  {'':<18} {lbl:<6} {sw2}/{2*len(sel)} = {100*sw2/(2*len(sel)):.1f}%  ({len(sel)} maps)")
    if primary:
        v = ("ACCEPT" if wins >= 29 else "REJECT" if wins <= 25 else
             "UNRESOLVED -- needs a disjoint-sample replication before it can accept")
        print(f"\n  ==> GATE ({wins}/50 vs >=29 accept / <=25 reject): {v}")

run = sys.argv[1]; A = areas()
print(f"{run}  (standing gate: >=29 accept, <=25 reject, 26-28 unresolved)\n")
for i, opp in enumerate(sys.argv[2:]):
    report(run, opp, A, primary=(i == 0)); print()

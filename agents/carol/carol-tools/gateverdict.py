#!/usr/bin/env python3
"""Apply carol's standing accept gate (adopted at commit 5443d59) to a gauntlet run.

The gate exists because the old one was set against se = 0. The engine is deterministic, so a
rerun on the same maps reproduces exactly -- but an accept asks about the map POPULATION, and a
25-of-75 draw carries real sampling variance. Measured over 59 of my own arms, a near-even
50-game arm has sd ~2.4 wins (with the finite-population correction; ~3.0 without, which is what
tools/map-resample.py's jackknife reports).

SUPERSEDED IN PLACE, 2026-09-09. The thresholds below were the STANDING gate until the
sampled-gate correction (commit 2b2ced6). They are kept here so that log entries decided
under them remain readable, and they are NOT what this tool applies any more:

    OLD (superseded):  >= 29/50 ACCEPT   <= 25/50 REJECT   26-28 UNRESOLVED

29/50 is a margin of +8. Measured sd of a 50-game sampled MARGIN is 8.59 -- map sampling
5.45 and perturbation 6.63, and the old figure above (sd ~2.4 wins = 4.8 margin) captured
only the first. So +8 is 0.93 sd: a ~1.0 sd gate wearing a 2.0 sd label. Corroborated
independently at sd 7.48 by a different route, which would set ACCEPT >= 33.

    CURRENT: >= 34/50 ACCEPT   <= 30/50 REJECT   31-33 UNRESOLVED
    (unresolved may not accept without a replication on a DISJOINT map sample)

Regenerate rather than remember: carol-tools/sampledgate.py derives these from any census.

D (split maps) and the swept counts are REPORTED, never gated: wins - N == SW - SL is an exact
identity, so a swept-count condition is the margin written twice. The one thing sweeps add is D,
decisiveness -- and an absolute floor on SW is not resolvable either (among my dead-even arms SW
ran as high as 9).

  gateverdict.py <run-dir> <baseline-opponent> [other-opponent ...]
"""
import csv, os, re, sys, math, collections

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
N_POP, N_DRAW = 75, 25
# Corrected sampled gate (commit 2b2ced6): sd(margin) = 8.59 on a 50-game arm, so 2.0 sd
# is a margin of +17.2, i.e. wins >= 33.6. Regenerable via carol-tools/sampledgate.py.
ACC, REJ = 34, 30
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
        # bot_result refers to the BOT argument. Under this lineage's standing
        # convention BOT is the BASELINE and the opponents are the CANDIDATES, so the
        # candidate wins exactly when the bot LOSES. Counting "win" here inverted every
        # verdict -- it once printed ACCEPT for an arm measured at -28. See TRAINING_LOG,
        # "TOOL BUG -- gateverdict.py INVERTS the verdict".
        mw[r["map"]] += 1 if r["bot_result"] == "loss" else 0
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
        v = ("ACCEPT" if wins >= ACC else "REJECT" if wins <= REJ else
             "UNRESOLVED -- needs a disjoint-sample replication before it can accept")
        print(f"\n  ==> GATE ({wins}/50 vs >={ACC} accept / <={REJ} reject): {v}")
        if 29 <= wins < ACC:
            print("      NOTE: this would have ACCEPTED under the superseded >=29 gate, which was"
                  "\n            ~1.0 sd wearing a 2.0 sd label. It does not accept now.")

def baseline_name(run):
    """Read who the bot_result column refers to. Refuse to guess."""
    try:
        txt = open(os.path.join(run, "bot.txt")).read()
        m = re.search(r"^bot=(\S+)", txt, re.M)
        return m.group(1) if m else None
    except OSError:
        return None

run = sys.argv[1]; A = areas()
_BASE = baseline_name(run)
if _BASE is None:
    sys.exit("!! cannot read bot.txt: refusing to guess which side bot_result names")
if len(sys.argv) > 2 and _BASE in sys.argv[2:]:
    sys.exit(f"!! {_BASE} is the BASELINE of this run, not a candidate arm")
print(f"  [roles] BOT/baseline = {_BASE};  scores below are the CANDIDATE's wins\n")
print(f"{run}  (standing gate: >={ACC} accept, <={REJ} reject, {REJ+1}-{ACC-1} unresolved;"
      f" superseded gate was >=29/<=25)\n")
for i, opp in enumerate(sys.argv[2:]):
    report(run, opp, A, primary=(i == 0)); print()

#!/usr/bin/env python3
"""Within-game build-mix and treasury trajectory, from cached replay dumps.

The discriminating test for iteration 37. Across games, realized soldier share correlates
with game LENGTH (rho=-0.654) far more strongly than with map area (-0.389). Two readings
fit that equally well:

  (A) mechanism  -- the treasury settles into the band where only splashers pass the chips
                    gate, so the mix collapses as a game goes on, in every game;
  (B) reverse    -- carol losing makes games drag to round 2000, and the mix is a symptom.

They differ WITHIN a game: (A) predicts the soldier share decays over rounds even in games
that end early and even in games carol wins; (B) predicts no within-game trend. This reads
the per-200-round SPAWN deltas and the treasury out of one cached dump, so it costs no VM.

  trajectory.py <cached-dump.txt> [...]
"""
import re, sys, os

def parse(path):
    n1 = n2 = None
    buckets = []
    for line in open(path):
        if line.startswith("=== GameHeader"):
            m1 = re.search(r"team1=(\S+)", line); m2 = re.search(r"team2=(\S+)", line)
            n1, n2 = m1.group(1), m2.group(1)
        if " | T" not in line:
            continue
        rm = re.match(r"\s*round\s+(\d+)", line)
        rnd = int(rm.group(1)) if rm else None
        rec = {}
        for blk in line.split("| ")[1:]:
            t = re.match(r"T(\d+)\s", blk)
            if not t: continue
            tid = int(t.group(1))
            g = lambda pat: int(re.search(pat, blk).group(1)) if re.search(pat, blk) else 0
            rec[tid] = dict(chips=g(r"\$(\d+)"), sold=g(r"\+sold(\d+)"),
                            mop=g(r"\+mop(\d+)"), spl=g(r"\+spl(\d+)"),
                            tw=g(r"\btw(\d+)"), twp=g(r"twPaint(\d+)"))
        if rec: buckets.append((rnd, rec))
    return n1, n2, buckets

for path in sys.argv[1:]:
    n1, n2, bs = parse(path)
    if not bs: print(f"{path}: no aggregate lines"); continue
    print(f"\n=== {os.path.basename(path)}  T1={n1}  T2={n2}")
    print(f"{'round':>6} | {'T1 s/m/p':>12} {'sold%':>6} {'chips':>6} {'tw':>3} | {'T2 s/m/p':>12} {'sold%':>6} {'chips':>6} {'tw':>3}")
    for rnd, rec in bs:
        cols = []
        for tid in (1, 2):
            r = rec.get(tid, {})
            tot = r.get("sold",0)+r.get("mop",0)+r.get("spl",0)
            sh = f"{100*r.get('sold',0)/tot:.0f}%" if tot else "  -"
            cols.append(f"{r.get('sold',0)}/{r.get('mop',0)}/{r.get('spl',0):<4}".rjust(12)
                        + f" {sh:>6} {r.get('chips',0):>6} {r.get('tw',0):>3}")
        print(f"{rnd:>6} | " + " | ".join(cols))

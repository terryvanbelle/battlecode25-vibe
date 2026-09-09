#!/usr/bin/env python3
"""Race-to-70% CLOCK: how fast does one build close a map, against a FIXED third party?

WHY THIS EXISTS. Carol's ruin-count deficit lives entirely in games decided by the >70%
paint condition (tournament 20260909-0100, dense maps: 8-45 in decided games, 7-8 in
tiebreaks). But "who reached 70% first" is ZERO-SUM inside a head-to-head -- only one side
can finish -- so a head-to-head can never separate "my build got faster" from "the other
build got slower". Worse, conditioning on whether a game was `decided` conditions on an
OUTCOME the build itself causes (doctrine 18's error family).

The fix is to take the opponent out of the statistic. Each arm plays the SAME fixed weak
opponent on the SAME maps, and we read the clock off each arm separately. Neither arm can
interfere with the other's clock because they never meet.

    clock.py <runA-dir> <labelA> <runB-dir> <labelB>

Reports per arm: maps closed by the 70% condition, median rounds to close, and the maps
where the two arms disagree. A game ending by annihilation is counted separately -- it stops
the clock for an unrelated reason and must not be read as "closed the map".
"""
import csv, os, sys, collections, statistics

def load(run):
    rows = list(csv.DictReader(open(os.path.join(run, "results.csv"))))
    reason = {}
    rp = os.path.join(run, "reasons.txt")
    if os.path.exists(rp):
        for line in open(rp):
            f = line.split()
            if len(f) >= 4:
                reason[(f[1], f[2])] = " ".join(f[3:])
    out = []
    for r in rows:
        why = reason.get((r["map"], r["bot_side"]), "")
        kind = ("paint70" if "painted enough" in why else
                "tiebreak" if "tiebreak" in why else
                "annihilation" if "destroy" in why.lower() or "all" in why.lower() else "?")
        out.append(dict(map=r["map"], side=r["bot_side"], won=r["bot_result"] == "win",
                        rounds=int(r["rounds"]), kind=kind))
    return out

def report(rows, label):
    closed = [r for r in rows if r["won"] and r["kind"] == "paint70"]
    ann    = [r for r in rows if r["won"] and r["kind"] == "annihilation"]
    tb     = [r for r in rows if r["won"] and r["kind"] == "tiebreak"]
    lost   = [r for r in rows if not r["won"]]
    n = len(rows)
    print(f"\n=== {label} ===   {n} games")
    print(f"  CLOSED by >70% paint : {len(closed):3d}  "
          f"median rounds {statistics.median([r['rounds'] for r in closed]):.0f}" if closed
          else f"  CLOSED by >70% paint : {len(closed):3d}")
    print(f"  won on tiebreak      : {len(tb):3d}   (did NOT close the map)")
    print(f"  won by annihilation  : {len(ann):3d}   (clock stopped for another reason)")
    print(f"  lost                 : {len(lost):3d}")
    return {(r["map"], r["side"]): r for r in rows}, closed

def main(a, la, b, lb):
    ra, ca = report(load(a), la)
    rb, cb = report(load(b), lb)
    print(f"\n=== PRE-REGISTERED COMPARISON ===")
    print(f"  maps CLOSED by 70%:  {la} {len(ca)}   vs   {lb} {len(cb)}   diff {len(cb)-len(ca):+d}")
    both = [k for k in ra if k in rb]
    faster = sum(1 for k in both
                 if ra[k]["kind"] == "paint70" and rb[k]["kind"] == "paint70"
                 and rb[k]["rounds"] < ra[k]["rounds"])
    slower = sum(1 for k in both
                 if ra[k]["kind"] == "paint70" and rb[k]["kind"] == "paint70"
                 and rb[k]["rounds"] > ra[k]["rounds"])
    print(f"  where BOTH closed:   {lb} faster on {faster}, slower on {slower}")
    print(f"\n  cells where only ONE arm closed the map:")
    for k in sorted(both):
        x, y = ra[k]["kind"] == "paint70", rb[k]["kind"] == "paint70"
        if x != y:
            who = lb if y else la
            print(f"    {k[0]:16s} side {k[1]}  closed only by {who}")

if __name__ == "__main__":
    main(*sys.argv[1:5])

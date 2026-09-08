#!/usr/bin/env python3
"""Iteration 40's two-channel check, read off an --every 1 replay dump.

Channel A (registered):  chips -> paint-tower UPGRADES -> paint income -> coverage.
Channel B (tether):      chips -> SOLDIERS built -> ruins become towers -> anchors move out.

Plus the falsifiable iteration-37 discriminator I put on record BEFORE the run:
"if iteration 40 fails the same way 37 did, the SPLASHER build count will fall."

Build counts come from the per-round '+soldN +mopN +splN' deltas, so the dump must be
--every 1 or the sums are a stride sample, not a total.  Tower creations come from SPAWN
events, which are logged at every round regardless of stride.

  channels.py <dump.txt> [...]
"""
import re, sys, collections

AGG = re.compile(r'^round (\d+) \| (.*)$')
ARM = re.compile(
    r'\$(\d+) cov(\d+)m .*?sold(\d+) spl(\d+) mop(\d+) tw(\d+) twPaint(\d+) '
    r'acts\[p(\d+) u(\d+) a(\d+) s(\d+) m(\d+)\] '
    r'\+sold(\d+) \+mop(\d+) \+spl(\d+) died(\d+) xfer(\d+) starved(\d+)')
SPAWN = re.compile(r'^round (\d+) id\d+\((T\d),\w+\) SPAWN id\d+\(T\d,(\w+)\) at')
UPG = re.compile(r'^round (\d+) UPGRADE id\d+\((T\d),(\w+)\)')

def main(paths):
    hdr = ("map", "team", "bSold", "bSpl", "bMop", "twPAINT", "twMONEY",
           "pUpg", "cov_end", "tw_end", "spl_end", "$med", "twPaint_med", "starve%")
    print("%-14s %-14s %6s %6s %6s %8s %8s %5s %8s %7s %8s %7s %11s %7s" % hdr)
    for p in paths:
        txt = open(p).read().splitlines()
        mp = "?"
        for ln in txt[:3]:
            m = re.search(r'map=(\S+)', ln)
            if m: mp = m.group(1)
        teams = {}
        for ln in txt[:2]:
            for t, n in re.findall(r'(team\d)=(\S+)', ln):
                teams["T" + t[-1]] = n
        build = collections.defaultdict(lambda: collections.Counter())
        towers = collections.defaultdict(lambda: collections.Counter())
        upg = collections.defaultdict(lambda: collections.Counter())
        series = collections.defaultdict(list)
        for ln in txt:
            m = SPAWN.match(ln)
            if m: towers[m.group(2)][m.group(3)] += 1
            m = UPG.match(ln)
            if m and m.group(1) != "1": upg[m.group(2)][m.group(3)] += 1
            m = AGG.match(ln)
            if not m: continue
            arms = ARM.findall(m.group(2))
            for i, g in enumerate(arms):
                t = "T%d" % (i + 1)
                (mon, cov, sold, spl, mop, tw, twp,
                 ap, au, aa, asp, am, bs, bm, bsp, died, xfer, starv) = map(int, g)
                build[t]["sold"] += bs; build[t]["spl"] += bsp; build[t]["mop"] += bm
                series[t].append((int(m.group(1)), mon, cov, tw, spl, twp, starv, sold))
        for t in ("T1", "T2"):
            s = series[t]
            if not s: continue
            med = lambda k: sorted(x[k] for x in s)[len(s) // 2]
            last = s[-1]
            starve_rounds = sum(1 for x in s if x[6] > 0)
            print("%-14s %-14s %6d %6d %6d %8d %8d %5d %8d %7d %8d %7d %11d %6.1f%%" % (
                mp, teams.get(t, t), build[t]["sold"], build[t]["spl"], build[t]["mop"],
                towers[t]["PAINT_TOWER"], towers[t]["MONEY_TOWER"],
                sum(v for k, v in upg[t].items() if k == "PAINT_TOWER"),
                last[2], last[3], last[4], med(1), med(5),
                100.0 * starve_rounds / len(s)))
        print()

main(sys.argv[1:])

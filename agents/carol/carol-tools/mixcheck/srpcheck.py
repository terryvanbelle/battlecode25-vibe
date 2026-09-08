#!/usr/bin/env python3
"""Iteration 41's link checks, read off an --every 1 replay dump.

The team's active-SRP counter is an unusually clean instrument: it has read 0 in every game
this lineage played before iteration 41, so any non-zero value proves the mechanism ran.

What it reports, per team:
  completed   patterns that reached `completeResourcePattern` (from the SRPDONE indicator tag,
              so this needs the strings too -- reported as '-' when unavailable)
  actRounds   rounds with >= 1 ACTIVE pattern      <- link 2: did it survive the 50-round delay
  srpRounds   sum of active patterns over rounds   <- the quantity actually PAID
  firstAct    round of first activation
  maxConc     most patterns active at once
  twPaint~    median fleet tower paint             <- link 3: did activation become income
  bSpl/bSold  builds, and twPAINT built            <- the price: towers must NOT fall
  cov_end     final coverage

Usage: srpcheck.py <dump.txt> [...]
"""
import re, sys, collections

AGG = re.compile(r'^round (\d+) \| (.*)$')
ARM = re.compile(
    r'\$(\d+) cov(\d+)m srp(\d+) sold(\d+) spl(\d+) mop(\d+) tw(\d+) twPaint(\d+) '
    r'acts\[p(\d+) u(\d+) a(\d+) s(\d+) m(\d+)\] '
    r'\+sold(\d+) \+mop(\d+) \+spl(\d+) died(\d+) xfer(\d+) starved(\d+)')
SPAWN = re.compile(r'^round (\d+) id\d+\((T\d),\w+\) SPAWN id\d+\(T\d,(\w+)\) at')


def main(paths):
    print("%-14s %-14s %9s %9s %9s %8s %9s %7s %7s %8s %8s" % (
        "map", "team", "actRounds", "srpRnds", "firstAct", "maxConc",
        "twPaint~", "bSpl", "bSold", "twPAINT", "cov_end"))
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
        st = collections.defaultdict(lambda: dict(
            act=0, srp=0, first=None, mx=0, tw=collections.Counter(),
            bspl=0, bsold=0, tp=[], cov=0))
        for ln in txt:
            m = SPAWN.match(ln)
            if m: st[m.group(2)]["tw"][m.group(3)] += 1
            m = AGG.match(ln)
            if not m: continue
            rnd = int(m.group(1))
            for i, g in enumerate(ARM.findall(m.group(2))):
                t = "T%d" % (i + 1)
                v = list(map(int, g))
                mon, cov, srp, sold, spl, mop, tw, twp = v[:8]
                bs, bm, bsp = v[13], v[14], v[15]
                d = st[t]
                if srp > 0:
                    d["act"] += 1; d["srp"] += srp
                    if d["first"] is None: d["first"] = rnd
                    d["mx"] = max(d["mx"], srp)
                d["bspl"] += bsp; d["bsold"] += bs
                d["tp"].append(twp); d["cov"] = cov
        for t in ("T1", "T2"):
            d = st.get(t)
            if not d or not d["tp"]: continue
            tp = sorted(d["tp"])
            print("%-14s %-14s %9d %9d %9s %8d %9d %7d %7d %8d %8d" % (
                mp, teams.get(t, t), d["act"], d["srp"],
                d["first"] if d["first"] is not None else "-", d["mx"],
                tp[len(tp)//2], d["bspl"], d["bsold"],
                d["tw"]["PAINT_TOWER"], d["cov"]))
        print()

main(sys.argv[1:])

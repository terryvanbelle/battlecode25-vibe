#!/usr/bin/env python3
"""Reachability pre-check for SYMMETRY INFERENCE: are there unclaimed ruins left
while alice's expansion is still running?

    tools/ruin-supply.py <label> <census.tsv> [...]

Symmetry inference predicts where ruins are on ground you have not seen. It can
only be worth anything if UNCLAIMED RUINS EXIST at the time expansion is running.
If every ruin is already taken by the time alice is still trying to expand, the
mechanism has nothing to find -- dead on reachability, for zero games, exactly as
iteration 47's singleton choice set and iteration 9's saturated ruins died.

claimable ruins come from tools/mapdata/ruin_parity.txt, which EXCLUDES the four
tiles the starting towers occupy (a replay MatchHeader reports 4 more; that file
says so explicitly and the two answer different questions).

    claimed at round R = (alice_tw - 2) + (carol_tw - 2)
    unclaimed          = claimable - claimed

Caveat stated rather than hidden: a destroyed tower frees its ruin and lowers tw,
so this UNDERSTATES claimed and therefore OVERSTATES unclaimed -- i.e. the bias
runs in favour of the mechanism being worth building. A null here is safe.
"""
import re
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PARITY = os.path.join(HERE, "..", "..", "..", "tools", "mapdata", "ruin_parity.txt")


def load_ruins():
    out = {}
    for line in open(PARITY):
        m = re.match(r"^(\w+)\s+(\d+)x(\d+)\s+ruins=\s*(\d+)", line)
        if m:
            out[m.group(1)] = (int(m.group(4)), int(m.group(2)) * int(m.group(3)))
    return out


def main():
    ruins = load_ruins()
    args = sys.argv[1:]
    for i in range(0, len(args), 2):
        label, path = args[i], args[i + 1]
        rows = []
        for line in open(path):
            p = line.rstrip("\n").split("\t")
            if len(p) < 5 or p[2] != "OK":
                continue
            mp, side = p[0], p[1]
            if mp not in ruins:
                continue
            seg = p[4].split("|")
            def tw(s):
                m = re.search(r"\btw(\d+)", s)
                return int(m.group(1)) if m else None
            a, c = tw(seg[1 if side == "T1" else 2]), tw(seg[2 if side == "T1" else 1])
            if a is None or c is None:
                continue
            claimable, area = ruins[mp]
            claimed = max(0, a - 2) + max(0, c - 2)
            rows.append((mp, claimable, claimed, claimable - claimed, a, area))
        if not rows:
            print(f"\n===== {label}: no games reached the census round =====")
            continue
        n = len(rows)
        f = lambda i: sum(r[i] for r in rows) / n
        zero = sum(1 for r in rows if r[3] <= 0)
        low = sum(1 for r in rows if r[3] <= 1)
        print(f"\n===== {label}  ({n} games) =====")
        print(f"  claimable ruins per map : {f(1):6.1f}")
        print(f"  claimed by both teams   : {f(2):6.1f}   (alice holds {f(4):.1f} towers)")
        print(f"  **UNCLAIMED REMAINING**  : {f(3):6.1f}"
              f"   = {100*f(3)/f(1):.0f}% of the map's ruins")
        print(f"  games with ZERO left    : {zero}/{n} = {100*zero/n:.0f}%"
              f"      with <=1 left: {low}/{n} = {100*low/n:.0f}%")


if __name__ == "__main__":
    main()

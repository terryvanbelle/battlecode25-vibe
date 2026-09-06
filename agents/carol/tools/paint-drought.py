#!/usr/bin/env python3
"""Measure the no-paint-tower absorbing state (RULES.md hard loss condition).

A team whose every surviving tower holds 0 paint can never build a robot, so it can never
paint a ruin, so it can never rebuild a paint tower. Chips are irrelevant. This measures the
longest run of consecutive rounds in which carol holds towers and the MAXIMUM paint across
all of them is 0 -- i.e. every tower is dry at once.

Distinct from tools/frozen-treasury.py, which measures the CHIP side (treasury stuck between
the reserve and the build gate). A game can show one without the other: on Dominoes chips rise
to 60,000 while paint is the thing that is dead.

Usage:  tools/paint-drought.py [--gate N] <replay.bc25> ...
"""
import argparse, collections, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
STRINGS = os.path.join(HERE, "replay-strings.py")
ROW = re.compile(r'(?:\[(\w+)\] )?.*T r=(\d+) chips=(\d+) tw=(\d+) tp=(\d+)')


def series(path):
    """{label: {round: (max_tower_paint, towers, chips)}} -- max, because ANY tower with paint
    is enough to keep spawning; the absorbing state needs every tower dry simultaneously."""
    out = subprocess.run([sys.executable, STRINGS, path], capture_output=True, text=True).stdout
    g = collections.defaultdict(lambda: collections.defaultdict(list))
    for line in out.splitlines():
        m = ROW.search(line)
        if m:
            tag, r, c, tw, tp = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
            g[tag][r].append((tp, tw, c))
    res = {}
    for tag, byr in g.items():
        res[tag or "untagged"] = [(r, max(v)[0], max(x[1] for x in v), max(x[2] for x in v))
                                  for r, v in sorted(byr.items())]
    return res


def longest_drought(s):
    best = run = 0
    at = None
    for r, maxtp, tw, chips in s:
        if tw > 0 and maxtp == 0:
            run += 1
            if run > best:
                best, at = run, (r, tw, chips)
        else:
            run = 0
    return best, at


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", type=int, default=None)
    ap.add_argument("replays", nargs="+")
    a = ap.parse_args()
    worst = 0
    for p in a.replays:
        parts = []
        for label, s in series(p).items():
            n, at = longest_drought(s)
            worst = max(worst, n)
            parts.append(f"{label}={n}" + (f"@r{at[0]}/{at[1]}tw/{at[2]}chips" if n >= 100 else ""))
        print(f"{os.path.basename(p)[:46]:48s} " + "  ".join(parts))
    if a.gate is not None:
        print(f"\nworst paint drought = {worst}; gate = {a.gate} -> "
              + ("FAIL" if worst >= a.gate else "PASS"))
        return 1 if worst >= a.gate else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())

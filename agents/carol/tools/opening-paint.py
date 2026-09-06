#!/usr/bin/env python3
"""Measure carol's opening paint starvation -- the mechanism gate for the tower paint reserve.

Counts rounds in the opening window where NO carol tower holds enough paint to build a soldier
(200). Those are rounds in which the team cannot produce a unit anywhere on the board, however
many chips it has. Baseline on the accepted build: median 28 of the first 100 rounds across 27
games, with 9 of 27 above 50.

Uses max paint across carol's towers, because ANY tower with 200 can spawn; the team is only
blocked when every tower is under it.

Usage:  tools/opening-paint.py [--window 100] [--cost 200] <replay.bc25> ...
"""
import argparse, collections, os, re, statistics, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
STRINGS = os.path.join(HERE, "replay-strings.py")
ROW = re.compile(r'(?:\[(\w+)\] )?.*T r=(\d+) chips=(\d+) tw=(\d+) tp=(\d+)')


def carol_series(path):
    """Rounds -> max tower paint, for carol's side only.

    carol carries a BUILD tag from iteration 7 on; a frozen snapshot or an archetype does not,
    so the tagged group is carol. When nothing is tagged (older replays, or an archetype-only
    opponent that emits no tower rows) there is a single group and it is carol's.
    """
    out = subprocess.run([sys.executable, STRINGS, path], capture_output=True, text=True).stdout
    g = collections.defaultdict(lambda: collections.defaultdict(int))
    for line in out.splitlines():
        m = ROW.search(line)
        if m:
            tag, r, tp = m.group(1), int(m.group(2)), int(m.group(5))
            g[tag][r] = max(g[tag][r], tp)
    tagged = [k for k in g if k]
    if tagged:
        return g[tagged[0]]
    return g[None] if len(g) == 1 else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=int, default=100)
    ap.add_argument("--cost", type=int, default=200)
    ap.add_argument("replays", nargs="+")
    a = ap.parse_args()
    rows = []
    for p in a.replays:
        s = carol_series(p)
        win = {r: tp for r, tp in s.items() if r <= a.window}
        if not win:
            continue
        blocked = sum(1 for tp in win.values() if tp < a.cost)
        rows.append((os.path.basename(p)[:44], blocked, len(win)))
    if not rows:
        print("no carol tower rows found")
        return 0
    rows.sort(key=lambda x: -x[1])
    for n, b, t in rows[:12]:
        print(f"  {n:46s} {b:3d} blocked of first {t}")
    vals = [r[1] for r in rows]
    print(f"\n  n={len(rows)} games   median blocked = {statistics.median(vals):.0f}"
          f" of the first {a.window}   above half: {sum(1 for v in vals if v > a.window // 2)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

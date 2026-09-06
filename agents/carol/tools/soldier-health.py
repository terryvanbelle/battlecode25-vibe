#!/usr/bin/env python3
"""Measure soldier paint starvation -- the COUNTER-metric for the tower paint reserve.

The reserve makes towers withhold paint from refilling soldiers. The obvious way that backfires
is that soldiers run dry: at 0 paint a robot takes -20 HP/turn and cannot move or act until
refilled. So a run that improves the opening-paint metric while losing the head-to-head has
most likely bought production with unit deaths, and this is what distinguishes that from noise.

Reports per build tag:
  turns      total soldier turns observed (a crude activity/population measure)
  dry        soldier turns at exactly 0 paint (frozen, bleeding 20 HP/turn)
  low        soldier turns under one attack's worth of paint (<5, cannot even paint a tile)
  dry%       dry / turns

Usage:  tools/soldier-health.py <replay.bc25> ...
"""
import collections, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
STRINGS = os.path.join(HERE, "replay-strings.py")
# soldier lines look like:  [i10] bc=.. max=.. ov=0 nm=0 | S pnt p=88
ROW = re.compile(r'(?:\[(\w+)\] )?.*\|\s*S\b.*\bp=(\d+)')


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    agg = collections.defaultdict(lambda: [0, 0, 0])
    for p in sys.argv[1:]:
        out = subprocess.run([sys.executable, STRINGS, p], capture_output=True, text=True).stdout
        per = collections.defaultdict(lambda: [0, 0, 0])
        for line in out.splitlines():
            m = ROW.search(line)
            if not m:
                continue
            tag = m.group(1) or "untagged"
            paint = int(m.group(2))
            per[tag][0] += 1
            if paint == 0:
                per[tag][1] += 1
            if paint < 5:
                per[tag][2] += 1
        bits = []
        for tag, (t, d, l) in sorted(per.items()):
            bits.append(f"{tag}: turns={t} dry={d} ({100*d/t:.1f}%)" if t else f"{tag}: none")
            a = agg[tag]
            a[0] += t; a[1] += d; a[2] += l
        print(f"{os.path.basename(p)[:44]:46s} " + "   ".join(bits))
    print()
    for tag, (t, d, l) in sorted(agg.items()):
        if t:
            print(f"  TOTAL {tag:10s} soldier turns={t:7d}  dry={d:6d} ({100*d/t:.1f}%)"
                  f"  low<5={l:6d} ({100*l/t:.1f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

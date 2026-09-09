#!/usr/bin/env python3
"""Iteration 50 pre-check: is the wander HEADING choice set degenerate?

    tools/heading-read.py <label> <dump.txt> [...]

Reads the `R n= ch= bs= wo= chE= bsE= se=` block the i50 probe writes.
Shares are per mille of the tiles in that 45-degree sector.

WHY THE NULL MATTERS, and why my first bar was worthless: `best of 8 sector
estimates` is a MAXIMUM of eight noisy ~9-tile samples, so `best - chosen` is
upward-biased even when paint is spatially random and there is nothing whatever
to steer toward. Simulated, that winner's-curse floor is ~233 per mille. I
pre-registered a bar of 100, which pure noise clears comfortably -- so the bar
was not a bar. The comparison below is against the SIMULATED NULL, not zero.

Necessary, not sufficient: beating the noise floor shows spatial structure
exists. Whether that structure PERSISTS over the 25 turns a heading is held is a
separate question and the next rung.
"""
import re
import sys

LINE = re.compile(
    r'^round (\d+) id(\d+)\(T(\d),(\w+)\) IND "R '
    r'n=(\d+) ch=(\d+) bs=(\d+) wo=(\d+) chE=(\d+) bsE=(\d+) se=(\d+)')

try:
    import numpy as np
except ImportError:
    np = None


def null_headroom(p, tiles, sectors=8, trials=200000, seed=50):
    """Winner's-curse floor: E[best - randomly chosen] with NO spatial structure."""
    if np is None:
        return float("nan")
    rng = np.random.default_rng(seed)
    s = rng.binomial(max(1, int(round(tiles))), p, size=(trials, sectors)) / max(1, int(round(tiles)))
    chosen = s[np.arange(trials), rng.integers(0, sectors, trials)]
    return 1000 * (s.max(axis=1) - chosen).mean()


def load(path):
    last = {}
    for line in open(path, errors="replace"):
        m = LINE.match(line)
        if m:
            last[m.group(2)] = (m.group(4),) + tuple(int(m.group(i)) for i in range(5, 12))
    return list(last.values())


def report(label, rows):
    print(f"\n===== {label} =====")
    g = rows
    n = sum(r[1] for r in g)
    if n == 0:
        print("  no re-roll samples")
        return
    ch, bs, wo = (sum(r[i] for r in g) / n for i in (2, 3, 4))
    chE, bsE = (sum(r[i] for r in g) / n for i in (5, 6))
    sect = sum(r[7] for r in g) / n
    tiles = 68.0 / sect if sect else 8.5
    obs = bs - ch
    null = null_headroom(ch / 1000.0, tiles)
    print(f"  re-rolls={n}  robots={len(g)}  live sectors/sample={sect:.2f}"
          f"  (~{tiles:.1f} tiles/sector)")
    print(f"  ally share : chosen {ch:6.1f}   best {bs:6.1f}   worst {wo:6.1f}")
    print(f"  OBSERVED headroom (best-chosen) : {obs:7.1f} per mille")
    print(f"  NULL headroom (winner's curse)  : {null:7.1f} per mille"
          f"   [8 sectors x {tiles:.0f} tiles, p={ch/1000:.3f}]")
    print(f"  EXCESS over the noise floor     : {obs-null:+7.1f} per mille")
    print(f"  enemy share: chosen {chE:6.1f}   lowest available {bsE:6.1f}"
          f"   (avoidable {chE-bsE:+.1f})")
    print("  VERDICT: " + ("structure beyond noise" if obs - null > 50
                           else "INDISTINGUISHABLE FROM NOISE -- degenerate"))


if __name__ == "__main__":
    args = sys.argv[1:]
    for i in range(0, len(args), 2):
        report(args[i], load(args[i + 1]))

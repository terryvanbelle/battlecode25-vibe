#!/usr/bin/env python3
"""B0's NULL and CEILING -- what the registered ratio could ever have been.

B0 was pre-registered as |union| / (n*69) with a kill bar of 0.92.  Running it
produced 0.483, which reads as "enormous headroom".  Before spending anything on
that reading, this asks the question the registered form skipped: WHAT IS 0.92 A
RATIO OF?  n*69 assumes n discs that overlap nowhere and fall entirely on the
board.  On a 60x60 map with 83 soldiers that demands 5727 distinct tiles from a
3600-tile board.  The bar was unreachable by arithmetic, not by any fact about
how alice plays.

So three reference points per frame, not one:

  CEILING  min(non-wall tiles on the board, sum of clipped discs)
           the best any spacing rule could do -- perfect spread, nothing wasted.
  RANDOM   A * (1 - prod(1 - d_i/A)) for the frame's actual clipped disc sizes
           where the SAME n soldiers are dropped uniformly at random.  This is
           the null a movement rule has to beat: scatter with no coordination
           at all already de-overlaps, because independent points rarely stack.
  OBSERVED what alice actually does.

The number that matters for B is not OBSERVED/CEILING, it is where OBSERVED sits
BETWEEN RANDOM and CEILING.  Below RANDOM means alice clusters harder than chance
and even a crude repulsion recovers tiles.  At or above RANDOM means the spread
is already doing work and only a genuinely clever rule gains anything.
"""
import sys, re

VIS = [(dx, dy) for dx in range(-5, 6) for dy in range(-5, 6) if dx*dx + dy*dy <= 20]
GLYPHS = set(".#o*aAbBtTnNdDsSmMpP")
SOLDIER = {1: "s", 2: "S"}

def frames(lines):
    W = H = None; mapname = None; i = 0
    while i < len(lines):
        m = re.match(r"=== MatchHeader map=(\S+) (\d+)x(\d+)", lines[i])
        if m: mapname = m.group(1)
        m = re.match(r"=== ARENA round (\d+)\s+(\d+)x(\d+)", lines[i])
        if m:
            rnd, W, H = int(m.group(1)), int(m.group(2)), int(m.group(3))
            rows, j = {}, i + 1
            while j < len(lines) and not lines[j].startswith("    census"):
                rm = re.match(r"^\s*(\d+) (\S+)$", lines[j])
                if rm and len(rm.group(2)) == W and set(rm.group(2)) <= GLYPHS:
                    rows[int(rm.group(1))] = rm.group(2)
                j += 1
            if len(rows) == H:
                yield (mapname, rnd, W, H, [rows[y] for y in range(H)])
            i = j; continue
        i += 1

def analyse(grid, W, H, glyph):
    wall = [[grid[y][x] == '#' for x in range(W)] for y in range(H)]
    # A wall tile is a tile no soldier will ever paint. Counting it as
    # "information gathered" would inflate every figure here equally, so it is
    # excluded from board, discs and union alike.
    A = sum(1 for y in range(H) for x in range(W) if not wall[y][x])
    pos = [(x, y) for y in range(H) for x in range(W) if grid[y][x] == glyph]
    n = len(pos)
    if n == 0 or A == 0: return None
    union, sizes = set(), []
    for (x, y) in pos:
        s = 0
        for dx, dy in VIS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and not wall[ny][nx]:
                union.add((nx, ny)); s += 1
        sizes.append(s)
    U = len(union)
    ceiling = min(A, sum(sizes))
    # independent uniform drops: P(tile uncovered) = prod_i (1 - d_i/A)
    p_un = 1.0
    for d in sizes:
        p_un *= max(0.0, 1.0 - d / A)
    rand = A * (1.0 - p_un)
    return dict(n=n, A=A, U=U, ceiling=ceiling, rand=rand, disc=sum(sizes) / n)

def main():
    lines = [l.rstrip("\n") for l in sys.stdin]
    rows = []
    for (mapname, rnd, W, H, grid) in frames(lines):
        for team in (1, 2):
            r = analyse(grid, W, H, SOLDIER[team])
            if r: r.update(map=mapname, rnd=rnd, W=W, H=H, team=team); rows.append(r)
    if not rows:
        print("!! no frames -- refusing to print a ratio", file=sys.stderr); return 1

    print(f"{'map':<13}{'rnd':>5}{'tm':>3}{'n':>4}{'board':>7}"
          f"{'OBS':>7}{'RAND':>7}{'CEIL':>7}{'obs/ceil':>9}{'obs/rand':>9}")
    for r in rows:
        print(f"{r['map']:<13}{r['rnd']:>5}{r['team']:>3}{r['n']:>4}{r['A']:>7}"
              f"{r['U']:>7}{r['rand']:>7.0f}{r['ceiling']:>7}"
              f"{r['U']/r['ceiling']:>9.3f}{r['U']/r['rand']:>9.3f}")

    def agg(rs, label):
        if not rs: print(f"  {label}: no cells"); return
        U = sum(r["U"] for r in rs); C = sum(r["ceiling"] for r in rs)
        R = sum(r["rand"] for r in rs); N = sum(r["n"] for r in rs)
        S = sum(r["n"] * 69 for r in rs)
        mor = sum(r["U"] / r["rand"] for r in rs) / len(rs)
        print(f"  {label:<22} frames={len(rs):>3} soldiers={N:>5}")
        print(f"      registered  B0 = U/(n*69)      = {U/S:.3f}   (bar: >=0.92 kills B)")
        print(f"      vs ceiling  U/CEIL             = {U/C:.3f}   (1.000 = perfect spread)")
        print(f"      vs random   U/RAND pooled      = {R and U/R:.3f}   mean-of-frames = {mor:.3f}")
        print(f"      recoverable by beating random  = {R-U:>8.0f} tiles"
              f"  ({100*(R-U)/U:.1f}% more than seen now)")
        print(f"      recoverable by perfect spread  = {C-U:>8.0f} tiles"
              f"  ({100*(C-U)/U:.1f}% more than seen now)")

    print("\n=== AGGREGATE ===")
    agg(rows, "all frames")
    agg([r for r in rows if r["n"] >= 6], "n>=6 soldiers")
    print("\n=== by phase ===")
    for lo, hi, lab in ((0, 300, "early (<300)"), (300, 800, "mid"), (800, 9999, "late (>=800)")):
        agg([r for r in rows if lo <= r["rnd"] < hi], lab)
    return 0

sys.exit(main())

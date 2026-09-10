#!/usr/bin/env python3
"""C2 -- does a LOCAL signal point at the work?  Bars registered in this docstring
before the script was ever run.

C1 settled two things.  79.4% of soldiers see no empty tile at all, so they have no
gradient to follow; and the nearest empty tile is a median 14 tiles away (20 for
the blind ones) with 99.4% of soldiers able to walk to work inside a lifetime.
DISTANCE IS NOT THE BARRIER.  Direction is.

So the only question left for C is whether anything a soldier can compute FROM ITS
OWN DISC correlates with the true bearing to the nearest empty tile.  The candidate
signal is free and needs no memory, no messaging and no allies: a soldier deep in
friendly territory sees mostly its own paint, and the frontier is whichever way
that thins out.  MOVE DOWN THE OWN-PAINT GRADIENT.

  signal    of the 8 sectors of its own vision disc, the one with the lowest
            own-paint fraction
  truth     the sector containing the first step of the shortest walk to the
            nearest empty tile (multi-source BFS, 8-connected, around walls)

REGISTERED BEFORE RUNNING -- and registered against a SIMULATED null, not against
zero, because this lineage has already been burned once by scoring a best-of-8
statistic against a bar of zero when the winner's-curse floor was twice the bar:

  null        the same soldiers, same discs, sector chosen UNIFORMLY AT RANDOM.
              Computed here, not assumed to be 12.5%: walls and board edges make
              the sectors unequal, so chance is not 1/8 and must be measured.
  PASS        exact-sector agreement >= 30%, or within-one-sector >= 60%,
              AND at least 2.0x the simulated null on the exact figure.
  KILL        exact-sector agreement < 20%, or < 1.5x the simulated null.
  between     the signal is real but weak: dose it, never rebuild for it.

A control signal is scored alongside: the sector with the most EMPTY tiles, which
is what a sighted soldier would use.  On blind soldiers it has nothing to work
with, so it should collapse to the null -- if it does not, the instrument is wrong.
"""
import sys, re, random
from collections import deque

VIS = [(dx, dy) for dx in range(-5, 6) for dy in range(-5, 6) if dx*dx + dy*dy <= 20]
GLYPHS = set(".#o*aAbBtTnNdDsSmMpP")
T = {1: ("s", set("aA")), 2: ("S", set("bB"))}
DIRS = [(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]

def sector(dx, dy):
    """8 sectors by nearest compass direction; (0,0) has none."""
    if dx == 0 and dy == 0: return None
    best, bi = -2.0, 0
    n = (dx*dx + dy*dy) ** 0.5
    for i, (ux, uy) in enumerate(DIRS):
        un = (ux*ux + uy*uy) ** 0.5
        dot = (dx*ux + dy*uy) / (n*un)
        if dot > best: best, bi = dot, i
    return bi

SEC = {(dx, dy): sector(dx, dy) for dx, dy in VIS}

def frames(lines):
    mapname = None; i = 0
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

def bfs_field(grid, W, H):
    INF = 10**9
    d = [[INF]*W for _ in range(H)]; q = deque()
    for y in range(H):
        for x in range(W):
            if grid[y][x] == '.': d[y][x] = 0; q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                if dx == 0 and dy == 0: continue
                nx, ny = x+dx, y+dy
                if 0 <= nx < W and 0 <= ny < H and grid[ny][nx] != '#' and d[ny][nx] == INF:
                    d[ny][nx] = d[y][x] + 1; q.append((nx, ny))
    return d

def main():
    lines = [l.rstrip("\n") for l in sys.stdin]
    rng = random.Random(20260910)
    rows = []
    for (mapname, rnd, W, H, grid) in frames(lines):
        d = bfs_field(grid, W, H)
        for team in (1, 2):
            glyph, own = T[team]
            for y in range(H):
                for x in range(W):
                    if grid[y][x] != glyph: continue
                    if d[y][x] >= 10**9 or d[y][x] == 0: continue
                    # TRUTH: the neighbour step that strictly decreases BFS distance
                    # Tie-break among ALL strictly-decreasing neighbours must be
                    # RANDOM. Taking the first in DIRS order biased truth toward
                    # east, which silently inflated any east-preferring signal --
                    # caught because the empty-tile control scored 21.8% on BLIND
                    # soldiers, who have no empty tile to point at and whose argmax
                    # therefore degenerates to sector 0 (east). A control that
                    # cannot work scoring above chance is an instrument bug, and
                    # this is the second time that check has earned its keep.
                    cands = [i for i, (ux, uy) in enumerate(DIRS)
                             if 0 <= x+ux < W and 0 <= y+uy < H
                             and d[y+uy][x+ux] == d[y][x]-1]
                    if not cands: continue
                    truth = rng.choice(cands)
                    ownc = [0]*8; tot = [0]*8; empt = [0]*8
                    for dx, dy in VIS:
                        s = SEC[(dx, dy)]
                        if s is None: continue
                        nx, ny = x+dx, y+dy
                        if not (0 <= nx < W and 0 <= ny < H): continue
                        g = grid[ny][nx]
                        if g == '#': continue
                        tot[s] += 1
                        if g in own: ownc[s] += 1
                        if g == '.': empt[s] += 1
                    if sum(tot) == 0: continue
                    frac = [(ownc[s]/tot[s] if tot[s] else 2.0) for s in range(8)]
                    sig = min(range(8), key=lambda s: frac[s])
                    emp = max(range(8), key=lambda s: empt[s])
                    rows.append(dict(map=mapname, truth=truth, sig=sig, emp=emp,
                                     blind=(sum(empt) == 0), rnd=rnd,
                                     rand=rng.randrange(8)))
    if not rows:
        print("!! no scorable soldiers", file=sys.stderr); return 1

    def score(rs, key):
        n = len(rs)
        ex = sum(1 for r in rs if r[key] == r['truth'])
        w1 = sum(1 for r in rs if min((r[key]-r['truth']) % 8, (r['truth']-r[key]) % 8) <= 1)
        return n, 100*ex/n, 100*w1/n

    print("=== C2: does the local own-paint gradient point at the work? ===")
    print("    BARS REGISTERED BEFORE THIS RAN: pass exact>=30% or within-1>=60%,")
    print("    AND >=2.0x the simulated null.  Kill exact<20% or <1.5x null.\n")
    print(f"{'population':<26}{'n':>6}{'signal':>18}{'empty-ctl':>18}{'NULL(random)':>20}")
    for label, sub in (("all soldiers", rows),
                       ("BLIND (no empty seen)", [r for r in rows if r['blind']]),
                       ("sighted", [r for r in rows if not r['blind']])):
        if not sub: continue
        n, se, sw = score(sub, 'sig')
        _, ee, ew = score(sub, 'emp')
        _, re_, rw = score(sub, 'rand')
        print(f"{label:<26}{n:>6}"
              f"{se:>9.1f}%{sw:>8.1f}%"
              f"{ee:>9.1f}%{ew:>8.1f}%"
              f"{re_:>11.1f}%{rw:>8.1f}%")
    print("    (each pair is exact-sector % then within-one-sector %)")

    n, se, sw = score([r for r in rows if r['blind']], 'sig')
    _, re_, rw = score([r for r in rows if r['blind']], 'rand')
    ratio = se/re_ if re_ else float('inf')
    print(f"\n  BLIND soldiers are the population the mechanism exists for.")
    print(f"  exact {se:.1f}% vs simulated null {re_:.1f}%  ->  {ratio:.2f}x")
    if se < 20 or ratio < 1.5:  verdict = "KILL (registered: exact<20% or <1.5x null)"
    elif (se >= 30 or sw >= 60) and ratio >= 2.0: verdict = "PASS"
    else: verdict = "BETWEEN -- real but weak: dose it, never rebuild for it"
    print(f"  VERDICT: {verdict}")

    print("\n=== by map ===")
    for mp in sorted({r['map'] for r in rows}):
        sub = [r for r in rows if r['map'] == mp and r['blind']]
        if not sub: continue
        n, se, sw = score(sub, 'sig'); _, re_, _ = score(sub, 'rand')
        print(f"  {mp:<13} blind n={n:>5}  exact={se:>5.1f}%  within1={sw:>5.1f}%"
              f"  null={re_:>5.1f}%  ratio={se/re_ if re_ else 0:.2f}x")
    return 0

sys.exit(main())

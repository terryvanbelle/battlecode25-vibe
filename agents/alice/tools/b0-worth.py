#!/usr/bin/env python3
"""B0 follow-on: are the tiles alice's soldiers CANNOT see worth seeing?

B0 says the team's vision overlaps heavily and a spread would see ~25% more
distinct tiles.  P1 says that may be worth exactly nothing: a soldier gains
coverage only on an EMPTY tile, and 'more area seen' is not 'more area worth
painting'.  This settles it from the same frames, with no new games.

In the ASCII arena, for team 1:
  '.'      unpainted, no wall, no ruin  -> THE ONLY TILE A SOLDIER GAINS ON
  'a'/'A'  own paint      -> repainting gains nothing
  'b'/'B'  enemy paint    -> a soldier CANNOT paint it (engine-verified)
  '#'      wall           -> never paintable
  'o'      bare ruin      -> not a paint gain, but a tower site, counted apart

So the question is exactly: of the paintable-empty tiles that exist on the board
right now, how many are inside the union of the team's soldier vision, and how
many are invisible to the ENTIRE TEAM at once?

KNOWN BIAS, stated not hidden: units and towers occlude the paint under them, so
a tile standing under a robot is scored as whatever the robot is, never as '.'.
That undercounts empties, and it undercounts them PREFERENTIALLY WHERE SOLDIERS
ARE -- i.e. inside the union.  The bias therefore inflates the outside-share,
which is the direction that favours B.  It is bounded by the robot count, which
is printed alongside so the reader can size it.
"""
import sys, re

VIS = [(dx, dy) for dx in range(-5, 6) for dy in range(-5, 6) if dx*dx + dy*dy <= 20]
GLYPHS = set(".#o*aAbBtTnNdDsSmMpP")
SOLDIER = {1: "s", 2: "S"}

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

def main():
    lines = [l.rstrip("\n") for l in sys.stdin]
    out = []
    for (mapname, rnd, W, H, grid) in frames(lines):
        robots = sum(1 for y in range(H) for x in range(W)
                     if grid[y][x] in "sSmMpPtTnNdD")
        for team in (1, 2):
            pos = [(x, y) for y in range(H) for x in range(W)
                   if grid[y][x] == SOLDIER[team]]
            if not pos: continue
            union = set()
            for (x, y) in pos:
                for dx, dy in VIS:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H: union.add((nx, ny))
            empt_in = empt_out = ruin_in = ruin_out = 0
            for y in range(H):
                for x in range(W):
                    g = grid[y][x]
                    if g == '.':
                        if (x, y) in union: empt_in += 1
                        else: empt_out += 1
                    elif g == 'o':
                        if (x, y) in union: ruin_in += 1
                        else: ruin_out += 1
            out.append(dict(map=mapname, rnd=rnd, team=team, n=len(pos),
                            robots=robots, ei=empt_in, eo=empt_out,
                            ri=ruin_in, ro=ruin_out, un=len(union), A=W*H))
    if not out:
        print("!! no frames", file=sys.stderr); return 1

    print(f"{'map':<13}{'rnd':>5}{'tm':>3}{'n':>4}"
          f"{'empty_in':>9}{'empty_out':>10}{'%out':>7}{'ruin_in':>8}{'ruin_out':>9}")
    for r in out:
        tot = r['ei'] + r['eo']
        pct = 100 * r['eo'] / tot if tot else float('nan')
        print(f"{r['map']:<13}{r['rnd']:>5}{r['team']:>3}{r['n']:>4}"
              f"{r['ei']:>9}{r['eo']:>10}{pct:>7.1f}{r['ri']:>8}{r['ro']:>9}")

    def agg(rs, label):
        if not rs: print(f"  {label}: no cells"); return
        EI = sum(r['ei'] for r in rs); EO = sum(r['eo'] for r in rs)
        RI = sum(r['ri'] for r in rs); RO = sum(r['ro'] for r in rs)
        RB = sum(r['robots'] for r in rs)
        tot = EI + EO
        print(f"  {label:<18} frames={len(rs):>3}"
              f"  empty tiles: {tot:>7}  inside team vision {EI:>7} ({100*EI/tot:.1f}%)"
              f"  OUTSIDE {EO:>7} ({100*EO/tot:.1f}%)")
        print(f"  {'':<18}  bare ruins:  {RI+RO:>7}  inside {RI:>7}"
              f"  OUTSIDE {RO:>7}"
              + (f" ({100*RO/(RI+RO):.1f}%)" if RI+RO else "")
              + f"   [occlusion bound: {RB} robots]")

    print("\n=== AGGREGATE ===")
    agg(out, "all frames")
    print("\n=== by phase ===")
    for lo, hi, lab in ((0,300,"early (<300)"),(300,800,"mid"),(800,9999,"late (>=800)")):
        agg([r for r in out if lo <= r['rnd'] < hi], lab)
    print("\n=== by map ===")
    for mp in sorted({r['map'] for r in out}):
        agg([r for r in out if r['map']==mp], mp)
    return 0

sys.exit(main())

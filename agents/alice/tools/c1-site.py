#!/usr/bin/env python3
"""C1 measured AT THE SITE -- what one soldier can actually see when it chooses a move.

B0 established a TEAM-level famine: 93.6% of paintable-empty tiles are outside the
union of the whole team's vision.  That is a fact about the team, and no soldier
can compute it.  A mechanism lives inside one robot, which knows only its own
69-tile disc and the allies inside it.  So C1 is re-stated in SITE-OBSERVABLE
terms, and the substitution is declared rather than made quietly:

  registered C1  "destination already inside TEAM vision"
  site C1        composition of THIS soldier's own disc, + allies inside it

The registered form was not measurable at the site -- exactly the failure the
funnel discipline exists to catch, caught here before anything was built.  The
registered TERMINAL quantity and its bars (>=48 pass / <12 kill, empty tiles
brought into team vision per game) are unchanged; only the reachability stages
move to where the code would live.

THE MARGINAL STAGE, which is where A5 was going to die and C is not exempt:
for every soldier with NO empty tile in its own vision, how far away is the
nearest empty tile?  Ballistic travel covers roughly one tile per turn and a
soldier lives ~87.8 turns.  If the nearest work is a few tiles off, wander finds
it and no mechanism is needed.  If it is tens of tiles off, wander cannot get
there in a lifetime and the direction a unit is SENT is the whole game.
"""
import sys, re
from collections import deque

VIS = [(dx, dy) for dx in range(-5, 6) for dy in range(-5, 6) if dx*dx + dy*dy <= 20]
GLYPHS = set(".#o*aAbBtTnNdDsSmMpP")
# team -> (own soldier glyph, own paint glyphs, enemy paint glyphs)
T = {1: ("s", set("aA"), set("bB")), 2: ("S", set("bB"), set("aA"))}

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

def dist_to_empty(grid, W, H, starts):
    """Multi-source BFS FROM every empty tile, over non-wall tiles, 8-connected.
    Gives each soldier the true walk distance to the nearest paintable tile --
    not a straight line, so ruins and wall mazes are paid for honestly."""
    INF = 10**9
    d = [[INF]*W for _ in range(H)]
    q = deque()
    for y in range(H):
        for x in range(W):
            if grid[y][x] == '.':
                d[y][x] = 0; q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                if dx == 0 and dy == 0: continue
                nx, ny = x+dx, y+dy
                if 0 <= nx < W and 0 <= ny < H and grid[ny][nx] != '#' and d[ny][nx] == INF:
                    d[ny][nx] = d[y][x] + 1; q.append((nx, ny))
    return {(x, y): d[y][x] for (x, y) in starts}

def main():
    lines = [l.rstrip("\n") for l in sys.stdin]
    obs = []
    for (mapname, rnd, W, H, grid) in frames(lines):
        for team in (1, 2):
            glyph, own, enemy = T[team]
            pos = [(x, y) for y in range(H) for x in range(W) if grid[y][x] == glyph]
            if not pos: continue
            dd = dist_to_empty(grid, W, H, pos)
            for (x, y) in pos:
                c = dict(empty=0, ownp=0, enemyp=0, wall=0, ruin=0, allies=0)
                for dx, dy in VIS:
                    nx, ny = x+dx, y+dy
                    if not (0 <= nx < W and 0 <= ny < H): continue
                    g = grid[ny][nx]
                    if g == '.': c['empty'] += 1
                    elif g == '#': c['wall'] += 1
                    elif g == 'o': c['ruin'] += 1
                    elif g in own: c['ownp'] += 1
                    elif g in enemy: c['enemyp'] += 1
                    if g == glyph and (nx, ny) != (x, y): c['allies'] += 1
                c.update(map=mapname, rnd=rnd, team=team, dist=dd[(x, y)])
                obs.append(c)
    if not obs:
        print("!! no soldiers", file=sys.stderr); return 1

    n = len(obs)
    def mean(k): return sum(o[k] for o in obs) / n
    blind = [o for o in obs if o['empty'] == 0]
    print(f"=== C1 AT THE SITE: {n} soldier-observations ===")
    print(f"  mean own-disc composition (of 69):"
          f"  empty {mean('empty'):.2f}   own paint {mean('ownp'):.2f}"
          f"   enemy paint {mean('enemyp'):.2f}   wall {mean('wall'):.2f}"
          f"   bare ruin {mean('ruin'):.3f}")
    print(f"  mean ALLY SOLDIERS inside own vision: {mean('allies'):.2f}")
    print(f"  soldiers with ZERO empty tile in vision: {len(blind)}/{n}"
          f" = {100*len(blind)/n:.1f}%   <- no local gradient at all")
    print(f"  soldiers with ZERO empty AND >=1 ally in vision: "
          f"{sum(1 for o in blind if o['allies']>0)}/{n}"
          f" = {100*sum(1 for o in blind if o['allies']>0)/n:.1f}%")

    print(f"\n=== THE MARGINAL STAGE: walk distance to the nearest empty tile ===")
    print(f"    (8-connected BFS around walls; ~1 tile/turn; soldier lifetime ~87.8 turns)")
    for label, sub in (("ALL soldiers", obs), ("only the blind ones", blind)):
        if not sub: continue
        ds = sorted(o['dist'] for o in sub if o['dist'] < 10**9)
        if not ds: continue
        def pct(p): return ds[min(len(ds)-1, int(p*len(ds)))]
        reach = sum(1 for d in ds if d <= 88)
        print(f"  {label:<22} n={len(ds):>5}  median={pct(.5):>3}"
              f"  p75={pct(.75):>3}  p90={pct(.90):>3}  p99={pct(.99):>4}"
              f"  max={ds[-1]:>4}   within a lifetime (<=88): {100*reach/len(ds):.1f}%")

    print(f"\n=== by map (blind-rate and how far the work is) ===")
    for mp in sorted({o['map'] for o in obs}):
        sub = [o for o in obs if o['map'] == mp]
        b = [o for o in sub if o['empty'] == 0]
        ds = sorted(o['dist'] for o in sub if o['dist'] < 10**9)
        med = ds[len(ds)//2] if ds else -1
        print(f"  {mp:<13} n={len(sub):>5}  blind={100*len(b)/len(sub):>5.1f}%"
              f"  mean empty in disc={sum(o['empty'] for o in sub)/len(sub):>5.2f}"
              f"  median dist to work={med:>3}")
    return 0

sys.exit(main())

#!/usr/bin/env python3
"""ITERATION 48: mean CROWDING penalty per mobile-unit-round, from rendered arenas.

Usage: crowd_agg.py <crowd-census.tsv> [--names a,b]

ENGINE TARGET (InternalRobot.processEndOfTurn, bytecode-verified 2026-09-09):

    crowd = |getAllRobotsWithinRadiusSquared(myLoc, 2, myTeam)| excluding self
    own/neutral paint: -crowd     enemy paint: -2*crowd      EVERY TURN

r^2 <= 2 is exactly the 8 surrounding cells, so grid row order is irrelevant and
no coordinate convention can be got wrong here. `crowd` counts ALL allied robots,
TOWERS INCLUDED -- which is why the tower/mobile split below is reported, and why
the pre-registration made that split decisive rather than descriptive.

WHAT THIS CANNOT SEE, stated because it bounds the answer: units OCCLUDE paint in
this grid, so a unit's own tile colour is unknown and the enemy-territory doubling
cannot be applied. The reported number is therefore `crowd` itself, and the paint
cost lies between 1x and 2x it. The LOWER bound is what the thresholds are set on.

Encoding: towers t/n/d, mobiles s/m/p; team1 lower-case, team2 UPPER-CASE; the two
letter sets are disjoint so no glyph is ambiguous.
"""
import sys, collections

TOWERS = set('tnd')
MOBILE = set('smp')
UNITS  = TOWERS | MOBILE
NB = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]   # r^2 <= 2 exactly

path = sys.argv[1]
teams = {}
frames = collections.defaultdict(dict)      # (file, round) -> {y: row}
order  = []

cur = None
for line in open(path):
    p = line.rstrip("\n").split("\t")
    if p[0] == 'HDR' and len(p) >= 4:
        teams[p[1]] = (p[2], p[3])
    elif p[0] == 'ARENA' and len(p) >= 3:
        cur = (p[1], int(p[2]))
        if cur not in frames: order.append(cur)
    elif p[0] == 'G' and len(p) >= 4 and cur:
        frames[cur][int(p[2])] = p[3]

stat = collections.defaultdict(lambda: collections.defaultdict(float))
for key in order:
    f, rnd = key
    rows = frames.get(key)
    if not rows or f not in teams: continue
    t1, t2 = teams[f]
    ys = sorted(rows)
    grid = {}
    for y in ys:
        for x, ch in enumerate(rows[y]):
            if ch.lower() in UNITS: grid[(x, y)] = ch
    for (x, y), ch in grid.items():
        low = ch.lower()
        if low not in MOBILE: continue          # census the units that PAY, i.e. mobiles
        upper = ch.isupper()
        name = t2 if upper else t1
        s = stat[name]
        s['n'] += 1
        for dx, dy in NB:
            o = grid.get((x+dx, y+dy))
            if o is None: continue
            if o.isupper() != upper: continue    # allied only
            s['crowd'] += 1
            if o.lower() in TOWERS: s['tower'] += 1
            else: s['mob'] += 1
        if low == 's': s['sold'] += 1

print(f"{'bot':<14}{'unitObs':>9}{'crowd/unit':>12}{'fromTower':>11}{'fromMobile':>12}"
      f"{'towerShare':>12}{'paint/1000 unit-rounds':>24}")
for name in sorted(stat):
    s = stat[name]
    n = s['n']
    if not n: continue
    c, tw, mb = s['crowd']/n, s['tower']/n, s['mob']/n
    print(f"{name:<14}{int(n):>9}{c:>12.3f}{tw:>11.3f}{mb:>12.3f}"
          f"{(tw/c*100 if c else 0):>11.1f}%{c*1000:>24.0f}")

#!/usr/bin/env python3
"""D1 -- the messaging successor's delivery funnel, measured JOINTLY.

Registered before this ran (previous log entry):
  DELIVERY     PASS >= 50% of BLIND-soldier-turns able to reach a tower; KILL < 25%.
               Note the denominator: blind soldiers at the moment they need telling,
               NOT iteration 23's 53-65% of ALL robot turns.
  AGGREGATION  >= 3 distinct reporters per tower per 100 rounds.

JOINTLY, not as a product of marginals -- the rule this lineage's own 2.3x
overestimate established.  Every condition below is evaluated on THE SAME soldier
at THE SAME instant: it is blind (or sighted) AND within r^2<=20 of an ally tower
AND connected to it by a 4-adjacent ally-paint path.  Never P(range) x P(payload).

THE ENGINE CONSTRAINT THAT DECIDES THIS (RULES.md, verified):
  Robot <-> tower messaging only, never robot<->robot; r^2 <= 20 AND connected by a
  4-adjacent ALLY PAINT path (GameWorld.connectedByPaint, a BFS).
The paint-path clause is why the two sides of the channel are not symmetric.  A
BLIND soldier sits deep in its own paint (36.48 of 69 tiles) and should connect
easily.  A REPORTER -- a soldier that can see empty tiles -- is at the frontier BY
DEFINITION, which is exactly where the ally-paint path runs out.

GENEROUS BIAS, deliberate and declared: units occlude the paint beneath them in the
ASCII frame, so a tile under a robot cannot be read as paint.  Every own-team robot
tile is therefore counted AS ally paint here, which can only ADD connectivity.
Frontier tiles that merely have not been painted are not invented.  So every figure
below is an UPPER BOUND on what the real engine would allow, and a KILL under a
generous bias is a strong kill.

Reporter-turns is likewise an upper bound on DISTINCT reporters (one soldier
loitering in range for ten rounds is ten reporter-turns and one reporter), so the
aggregation bar is tested against a quantity that cannot understate it.
"""
import sys, re
from collections import deque

VIS = [(dx, dy) for dx in range(-5, 6) for dy in range(-5, 6) if dx*dx + dy*dy <= 20]
MSG = [(dx, dy) for dx in range(-5, 6) for dy in range(-5, 6) if dx*dx + dy*dy <= 20]
GLYPHS = set(".#o*aAbBtTnNdDsSmMpP")
# team -> soldier glyph, own paint, own towers, own mobile
T = {1: ("s", set("aA"), set("tnd"), set("smp")),
     2: ("S", set("bB"), set("TND"), set("SMP"))}

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
    rows = []; towerstat = []
    for (mapname, rnd, W, H, grid) in frames(lines):
        for team in (1, 2):
            sg, paint, towers, mobile = T[team]
            # traversable = ally paint, ally towers, ally mobile (generous: see docstring)
            trav = [[(grid[y][x] in paint or grid[y][x] in towers or grid[y][x] in mobile)
                     for x in range(W)] for y in range(H)]
            tw = [(x, y) for y in range(H) for x in range(W) if grid[y][x] in towers]
            if not tw: continue
            # one BFS per tower over the ally-paint component, 4-adjacent
            reach = {}
            for ti, (tx, ty) in enumerate(tw):
                seen = {(tx, ty)}; q = deque([(tx, ty)])
                while q:
                    x, y = q.popleft()
                    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < W and 0 <= ny < H and trav[ny][nx] and (nx, ny) not in seen:
                            seen.add((nx, ny)); q.append((nx, ny))
                reach[ti] = seen
            sold = [(x, y) for y in range(H) for x in range(W) if grid[y][x] == sg]
            per_tower = {ti: 0 for ti in range(len(tw))}
            for (x, y) in sold:
                empt = ruin = 0
                for dx, dy in VIS:
                    nx, ny = x+dx, y+dy
                    if 0 <= nx < W and 0 <= ny < H:
                        if grid[ny][nx] == '.': empt += 1
                        elif grid[ny][nx] == 'o': ruin += 1
                blind = (empt == 0)
                # JOINT: same soldier, same instant -- in range AND connected
                inrange = conn = False
                hit = None
                for ti, (tx, ty) in enumerate(tw):
                    if (tx-x)**2 + (ty-y)**2 <= 20:
                        inrange = True
                        if (x, y) in reach[ti]:
                            conn = True; hit = ti; break
                if conn and not blind: per_tower[hit] += 1
                rows.append(dict(map=mapname, rnd=rnd, team=team, blind=blind,
                                 empt=empt, ruin=ruin, inrange=inrange, conn=conn))
            for ti in range(len(tw)):
                towerstat.append(dict(map=mapname, rnd=rnd, reporters=per_tower[ti]))
    if not rows:
        print("!! no soldiers", file=sys.stderr); return 1

    def rate(sub, key):
        return 100*sum(1 for r in sub if r[key])/len(sub) if sub else float('nan')

    blind = [r for r in rows if r['blind']]
    sighted = [r for r in rows if not r['blind']]
    seeruin = [r for r in rows if r['ruin'] > 0]

    print("=== D1 DELIVERY, measured jointly at the soldier ===")
    print("    BARS REGISTERED BEFORE THIS RAN:")
    print("      delivery    PASS >=50% of blind-soldier-turns, KILL <25%")
    print("      aggregation >=3 distinct reporters per tower per 100 rounds\n")
    print(f"{'population':<34}{'n':>6}{'r^2<=20':>10}{'AND paint-connected':>22}")
    for lab, sub in (("BLIND soldiers (receive side)", blind),
                     ("SIGHTED soldiers (report side)", sighted),
                     ("soldiers seeing a bare RUIN", seeruin),
                     ("all soldiers", rows)):
        if not sub: continue
        print(f"{lab:<34}{len(sub):>6}{rate(sub,'inrange'):>9.1f}%{rate(sub,'conn'):>21.1f}%")

    d = rate(blind, 'conn')
    print(f"\n  DELIVERY (blind soldiers, joint): {d:.1f}%")
    print("  VERDICT: " + ("PASS" if d >= 50 else "KILL" if d < 25
                           else "BETWEEN -- dose, never rebuild"))

    r = rate(sighted, 'conn')
    print(f"\n  REPORT SIDE (sighted soldiers, joint): {r:.1f}%")
    print("    Not separately barred -- but the channel needs BOTH ends, and the")
    print("    payload cannot exist if nobody can report it.")

    if towerstat:
        n = len(towerstat)
        tot = sum(t['reporters'] for t in towerstat)
        zero = sum(1 for t in towerstat if t['reporters'] == 0)
        print(f"\n=== AGGREGATION: reporter-turns per tower per round ===")
        print(f"  tower-frames={n}  mean connected reporters per tower = {tot/n:.3f}")
        print(f"  towers with ZERO connected reporter: {zero}/{n} = {100*zero/n:.1f}%")
        print(f"  implied reporter-TURNS per tower per 100 rounds = {100*tot/n:.1f}"
              f"   (an UPPER BOUND on distinct reporters; bar was >=3)")
        print("  VERDICT: " + ("PASS" if 100*tot/n >= 3 else "KILL"))

    # THE STRUCTURAL QUESTION. The paint-path clause means every report must
    # originate from INSIDE painted territory. So: does a soldier that CAN report
    # see the same thing as one that cannot? If connected reporters systematically
    # see less empty map, the channel carries news about where we already are.
    print("\n=== WHAT A REPORTER CAN SEE (the paint-path clause's real consequence) ===")
    for lab, sub in (("sighted soldiers", sighted), ("soldiers seeing a bare ruin", seeruin)):
        c = [r for r in sub if r['conn']]; u = [r for r in sub if not r['conn']]
        if not c or not u: continue
        me = lambda z, k: sum(r[k] for r in z)/len(z)
        print(f"  {lab}:")
        print(f"    CAN report      n={len(c):>5}  mean empty seen={me(c,'empt'):>6.2f}"
              f"  mean bare ruins seen={me(c,'ruin'):>5.3f}")
        print(f"    CANNOT report   n={len(u):>5}  mean empty seen={me(u,'empt'):>6.2f}"
              f"  mean bare ruins seen={me(u,'ruin'):>5.3f}")
        print(f"    ratio (cannot/can) empty = {me(u,'empt')/me(c,'empt') if me(c,'empt') else float('nan'):.2f}x")
    # dwell correction: reporter-TURNS is not distinct reporters. A soldier crossing
    # the r<=4.47 message disc ballistically occupies it for ~7-9 turns.
    if towerstat:
        rt = 100*sum(t['reporters'] for t in towerstat)/len(towerstat)
        print("\n=== AGGREGATION, dwell-corrected ===")
        print(f"  reporter-TURNS per tower per 100 rounds = {rt:.1f} (measured, upper bound)")
        for dwell in (5, 7, 9):
            print(f"    at ~{dwell}-turn dwell in the message disc -> "
                  f"{rt/dwell:>4.1f} DISTINCT reporters per tower per 100 rounds"
                  f"   {'PASS' if rt/dwell>=3 else 'FAILS the >=3 bar'}")
        print("  The registered quantity was DISTINCT reporters; reporter-turns was a")
        print("  proxy chosen because it cannot understate. Correcting it DEFLATES a")
        print("  pass -- a correction that moves against the outcome I wanted, which")
        print("  is the direction that makes a correction credible.")
    print("\n=== by map: blind delivery / sighted report ===")
    for mp in sorted({r['map'] for r in rows}):
        b = [r for r in blind if r['map']==mp]; s = [r for r in sighted if r['map']==mp]
        print(f"  {mp:<13} blind n={len(b):>5} deliver={rate(b,'conn'):>5.1f}%"
              f"   sighted n={len(s):>4} report={rate(s,'conn'):>5.1f}%")
    return 0

sys.exit(main())

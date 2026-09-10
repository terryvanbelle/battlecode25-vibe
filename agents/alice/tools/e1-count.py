#!/usr/bin/env python3
"""E1 -- pricing the COUNT leg of the vision union.  The last free question.

Team vision union = f(placement, count).  Placement is bounded (+4 points, B0) and
the other three routes are closed.  Count has never been priced: "spawning FEWER is
arithmetically worse" is not the same claim as "spawning MORE would not help".

Three independent caps are checked, because whichever binds first is the answer:

  CAP 1  SPAWN COOLDOWN.  UnitType spawn CD is 10, so ONE tower emits at most one
         robot per 10 rounds.  Steady-state mobile population <= towers/10 * mean
         lifetime.  Lifetime is map-dependent and measured: 87.8 turns on small
         maps, 220.0 on large.  So the ceiling is 8.78 mobile/tower small,
         22.0 large -- from the engine, before paint is even considered.

  CAP 2  PAINT INCOME.  A soldier costs 200 paint.  A paint tower makes 5/10/15 per
         turn by level; a MONEY tower makes ZERO paint and spawns only from the 500
         it is born with.  Sustainable population = income/200 * lifetime.

  CAP 3  MARGINAL RETURN.  Even with slack in 1 and 2, discs saturate: the k-th
         soldier adds fewer NEW tiles than the (k-1)th.  Fitted per map from the
         frames as union = A*(1-(1-d_eff/A)^n), then differentiated at alice's
         actual operating point, and converted into EMPTY tiles using the empty
         density OUTSIDE the current union -- which is where new tiles come from.

Currency, unchanged from every other entry: a soldier's attack costs 5 paint, so
its 200-paint price is 40 paintable tiles gross, of which ~16.7-20 are realised
(half the tank goes to upkeep over its lifetime -- three instruments agree).
A ruin needs 24 tiles for +1 tower.
"""
import sys, re, math

VIS = [(dx, dy) for dx in range(-5, 6) for dy in range(-5, 6) if dx*dx + dy*dy <= 20]
GLYPHS = set(".#o*aAbBtTnNdDsSmMpP")
T = {1: (set("smp"), set("tnd"), "s", "t"), 2: (set("SMP"), set("TND"), "S", "T")}

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
    rows = []
    for (mapname, rnd, W, H, grid) in frames(lines):
        A = sum(1 for y in range(H) for x in range(W) if grid[y][x] != '#')
        for team in (1, 2):
            mob, tow, sg, pt = T[team]
            towers = [(x, y) for y in range(H) for x in range(W) if grid[y][x] in tow]
            painttow = sum(1 for (x, y) in towers if grid[y][x] == pt)
            mobile = [(x, y) for y in range(H) for x in range(W) if grid[y][x] in mob]
            sold = [(x, y) for y in range(H) for x in range(W) if grid[y][x] == sg]
            if not towers or not sold: continue
            union = set()
            for (x, y) in sold:
                for dx, dy in VIS:
                    nx, ny = x+dx, y+dy
                    if 0 <= nx < W and 0 <= ny < H and grid[ny][nx] != '#':
                        union.add((nx, ny))
            eo = sum(1 for y in range(H) for x in range(W)
                     if grid[y][x] == '.' and (x, y) not in union)
            outside = A - len(union)
            rows.append(dict(map=mapname, rnd=rnd, team=team, A=A, big=max(W, H),
                             tow=len(towers), painttow=painttow, mob=len(mobile),
                             n=len(sold), U=len(union),
                             dens=(eo/outside if outside > 0 else 0.0)))
    if not rows:
        print("!! no frames", file=sys.stderr); return 1

    print("=== CAP 1: SPAWN COOLDOWN (engine CD=10, one robot per tower per 10 rounds) ===")
    print("    ceiling = towers/10 * lifetime;  lifetime 87.8 small / 220.0 large (measured)")
    for lab, sub in (("small maps (<30)", [r for r in rows if r['big'] < 30]),
                     ("large maps (>=45)", [r for r in rows if r['big'] >= 45])):
        if not sub: continue
        life = 87.8 if "small" in lab else 220.0
        cap = life / 10.0
        util = [r['mob'] / (r['tow'] * cap) for r in sub if r['tow']]
        mt = sum(r['mob'] for r in sub) / sum(r['tow'] for r in sub)
        print(f"  {lab:<20} frames={len(sub):>3}  mean towers={sum(r['tow'] for r in sub)/len(sub):>5.2f}"
              f"  mobile/tower={mt:>5.2f}  ceiling={cap:>5.2f}"
              f"  UTILISATION={100*sum(util)/len(util):>5.1f}%")

    print("\n=== CAP 2: PAINT INCOME (soldier = 200 paint; paint tower 5/L1 10/L2 15/L3;")
    print("           MONEY TOWER MAKES ZERO PAINT) ===")
    for lab, sub in (("small maps", [r for r in rows if r['big'] < 30]),
                     ("large maps", [r for r in rows if r['big'] >= 45])):
        if not sub: continue
        life = 87.8 if "small" in lab else 220.0
        pt = sum(r['painttow'] for r in sub) / len(sub)
        obs = sum(r['mob'] for r in sub) / len(sub)
        for lvl, rate in ((1, 5), (2, 10)):
            sustain = (pt * rate) / 200.0 * life
            print(f"  {lab:<12} mean PAINT towers={pt:>5.2f}  at L{lvl} ({rate}/turn)"
                  f" -> sustainable mobile = {sustain:>6.1f}   observed = {obs:>5.1f}"
                  f"   {'INCOME-LIMITED' if obs > sustain else 'income has slack'}")

    print("\n=== CAP 3: MARGINAL UNION RETURN, fitted per map and differentiated ===")
    print(f"{'map':<13}{'frames':>7}{'meanN':>7}{'d_eff':>7}{'marg tiles/soldier':>20}"
          f"{'empty dens':>12}{'MARG EMPTY':>12}")
    tot_marg_empty = []
    for mp in sorted({r['map'] for r in rows}):
        sub = [r for r in rows if r['map'] == mp and r['n'] >= 2 and r['U'] < r['A']]
        if len(sub) < 3: continue
        # union = A(1-(1-d/A)^n)  =>  ln(1-U/A) = n ln(1-d/A);  least squares through origin
        num = den = 0.0
        for r in sub:
            y = math.log(max(1e-9, 1.0 - r['U'] / r['A'])); num += r['n'] * y; den += r['n'] ** 2
        if den == 0: continue
        k = num / den                     # = ln(1 - d_eff/A)
        A = sum(r['A'] for r in sub) / len(sub)
        d_eff = A * (1.0 - math.exp(k))
        nbar = sum(r['n'] for r in sub) / len(sub)
        marg = d_eff * math.exp(k * nbar)  # dU/dn at the operating point
        dens = sum(r['dens'] for r in sub) / len(sub)
        me = marg * dens
        tot_marg_empty.append(me)
        print(f"{mp:<13}{len(sub):>7}{nbar:>7.1f}{d_eff:>7.1f}{marg:>20.1f}"
              f"{dens:>12.3f}{me:>12.1f}")

    if tot_marg_empty:
        m = sum(tot_marg_empty) / len(tot_marg_empty)
        print(f"\n  mean MARGINAL EMPTY TILES brought into team vision by one extra soldier"
              f" = {m:.1f}")
        print(f"  that soldier costs 200 paint = 40 paintable tiles gross,"
              f" ~16.7-20 realised, and 24 tiles = +1 tower")
        print(f"  it also PAINTS ~16.7 of what it finds, so the honest comparison is")
        print(f"  marginal-empty-SEEN ({m:.1f}) against what the same 200 paint buys elsewhere.")
    return 0

sys.exit(main())

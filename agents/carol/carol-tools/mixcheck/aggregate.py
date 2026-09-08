#!/usr/bin/env python3
"""Aggregate spawnmix.sh output into the iteration-36 manipulation check.

Input lines: <replay> <name1> s m p <name2> s m p <twPaint1> <twPaint2>
Both bots are in the SAME game, so every row is a PAIRED observation: same map,
same round count, same opponent. Soldier SHARE (a ratio) is the pre-registered
quantity precisely because counts scale with how well a bot is doing in that game
and shares are far less sensitive to it.
"""
import sys, collections

CAND = "carol_i36_200"
rows = []
for line in open(sys.argv[1]):
    f = line.split()
    if len(f) < 11: continue
    rep, n1, s1, m1, p1, n2, s2, m2, p2, tp1, tp2 = f[0], f[1], *map(int, f[2:5]), f[5], *map(int, f[6:9]), int(f[9]), int(f[10])
    a = (n1, s1, m1, p1, tp1); b = (n2, s2, m2, p2, tp2)
    cand, inc = (a, b) if n1 == CAND else (b, a)
    rows.append((rep.replace("carol_iter35__", "").replace(".bc25", ""), cand, inc))

def share(r):
    tot = r[1] + r[2] + r[3]
    return (100.0 * r[1] / tot) if tot else None

print(f"{'map/side':26} {'cand s/m/p':>16} {'sh%':>6} {'inc s/m/p':>16} {'sh%':>6} {'d(sh)':>7} {'incMop':>7}")
ds, fired, inert = [], [], []
for name, c, i in rows:
    sc, si = share(c), share(i)
    d = (sc - si) if (sc is not None and si is not None) else None
    print(f"{name:26} {str(c[1])+'/'+str(c[2])+'/'+str(c[3]):>16} {sc if sc is None else round(sc,1):>6} "
          f"{str(i[1])+'/'+str(i[2])+'/'+str(i[3]):>16} {si if si is None else round(si,1):>6} "
          f"{d if d is None else round(d,1):>7} {i[2]:>7}")
    if d is None: continue
    ds.append(d)
    (fired if i[2] >= 5 else inert).append(d)

def summ(lab, xs):
    if not xs: return
    xs2 = sorted(xs)
    med = xs2[len(xs2)//2] if len(xs2) % 2 else (xs2[len(xs2)//2-1]+xs2[len(xs2)//2])/2
    pos = sum(1 for x in xs if x > 0)
    print(f"{lab:38} n={len(xs):2d}  mean d(share)={sum(xs)/len(xs):+6.1f}pp  median={med:+6.1f}pp  positive {pos}/{len(xs)}")

print()
summ("ALL paired games", ds)
summ("incumbent built >=5 moppers (fired)", fired)
summ("incumbent built <5 moppers (inert)", inert)

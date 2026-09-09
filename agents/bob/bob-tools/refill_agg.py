#!/usr/bin/env python3
"""ITERATION 47 aggregator: did refilling earlier buy soldier-rounds, and what paid?

Usage: refill_agg.py <census.tsv> [--stride N] [--arms g0,g1,g2]

Reads bob-tools/refill-census.sh output and reports, per ARM (the opponent bot in
each game, which is the thing the dose was applied to), the four secondaries
registered in TRAINING_LOG before the run existed:

  1 xfer/game      refill (TransferAction) events        MUST RISE with dose
  2 paint/soldR    paint actions per soldier-round       THE PAYER -- a refill turn paints nothing
  3 starv/game     starvation deaths                     MUST FALL
    soldR/game     soldier-rounds                        MUST RISE  (the mechanism's whole claim)
  4 dTiles         net coverage gained, in tiles         THE OBJECTIVE

EXACTNESS -- USE --stride 1. ReplayDump flushes and resets its cumulative
counters on every printed line, so summing printed lines is exact ONLY if every
round is printed. At a coarser stride each game silently drops up to (stride-1)
rounds off its end: measured -0.9% on paints and -8% on starvations at stride 50.
That loss depends on each game's end-round, so it does NOT cancel between arms --
and this iteration's claim is precisely that games run longer. Stride 1 loses
nothing; anything coarser is a smoke test, not a measurement.

DOUBLE-COUNTING, avoided deliberately (LEARNINGS 71/79): `acts` here is
paints + splashes, and iteration 44's addendum showed acts[p] ALREADY contains
one entry per splash-footprint tile. So paints alone is the honest count of
paint actions and `acts_incl_splash` is reported beside it, labelled, rather
than silently summed into one number.
"""
import sys, re, collections

ROW = re.compile(
    r"T(?P<tid>\d) \$(?P<money>\d+) cov(?P<cov>\d+)m srp(?P<srp>\d+) sold(?P<sold>\d+) "
    r"spl(?P<spl>\d+) mop(?P<mop>\d+) tw(?P<tw>\d+) twPaint(?P<twp>\d+) "
    r"acts\[p(?P<p>\d+) u(?P<u>\d+) a(?P<a>\d+) s(?P<s>\d+) m(?P<m>\d+)\] "
    r"\+sold(?P<ps>\d+) \+mop(?P<pm>\d+) \+spl(?P<pl>\d+) "
    r"died(?P<died>\d+) xfer(?P<xfer>\d+) starved(?P<starv>\d+)")

args = sys.argv[1:]
path = args[0]
stride = 10
arms = None
for i, a in enumerate(args):
    if a == '--stride': stride = int(args[i+1])
    if a == '--arms': arms = args[i+1].split(',')

teams = {}          # file -> (team1, team2)
area  = {}          # file -> map area (from MatchHeader if present)
acc   = collections.defaultdict(lambda: collections.defaultdict(float))
covfirst, covlast = {}, {}
games = collections.defaultdict(set)

for line in open(path):
    parts = line.rstrip("\n").split("\t")
    if parts[0] == 'HDR' and len(parts) >= 4:
        teams[parts[1]] = (parts[2], parts[3])
    elif parts[0] == 'ROW' and len(parts) >= 3:
        f = parts[1]
        if f not in teams: continue
        t1, t2 = teams[f]
        for m in ROW.finditer(parts[2]):
            d = m.groupdict()
            name = t1 if d['tid'] == '1' else t2
            k = (f, name)
            a = acc[k]
            a['p'] += int(d['p']); a['s'] += int(d['s']); a['u'] += int(d['u'])
            a['died'] += int(d['died']); a['xfer'] += int(d['xfer'])
            a['starv'] += int(d['starv']); a['soldsum'] += int(d['sold'])
            a['spawn'] += int(d['ps']) + int(d['pm']) + int(d['pl'])
            a['twp'] += int(d['twp']); a['tw'] += int(d['tw']); a['rows'] += 1
            cov = int(d['cov'])
            if k not in covfirst: covfirst[k] = cov
            covlast[k] = cov
            games[name].add(f)

# ---- per-arm aggregation -------------------------------------------------
names = sorted(games)
if arms: names = [n for n in names if any(n.endswith(x) for x in arms)] or names

print(f"{'bot':<14}{'n':>5}{'xfer/g':>9}{'starv/g':>9}{'died/g':>8}"
      f"{'soldR/g':>10}{'paint/g':>9}{'paint/soldR':>13}{'dCov(m)':>9}{'spawn/g':>9}{'twPaint':>9}{'tw':>7}")
rows = {}
for n in names:
    fs = sorted(games[n])
    N = len(fs)
    if not N: continue
    tot = collections.defaultdict(float)
    for f in fs:
        a = acc[(f, n)]
        for k, v in a.items(): tot[k] += v
        tot['dcov'] += covlast[(f, n)] - covfirst[(f, n)]
    soldR = tot['soldsum'] * stride
    rows[n] = dict(N=N, xfer=tot['xfer']/N, starv=tot['starv']/N, died=tot['died']/N,
                   soldR=soldR/N, paint=tot['p']/N,
                   psr=(tot['p']/soldR if soldR else float('nan')),
                   dcov=tot['dcov']/N, spawn=tot['spawn']/N,
                   twp=tot['twp']/tot['rows'], tw=tot['tw']/tot['rows'])
    r = rows[n]
    print(f"{n:<14}{N:>5}{r['xfer']:>9.1f}{r['starv']:>9.2f}{r['died']:>8.2f}"
          f"{r['soldR']:>10.0f}{r['paint']:>9.1f}{r['psr']:>13.3f}{r['dcov']:>9.1f}{r['spawn']:>9.1f}{r['twp']:>9.1f}{r['tw']:>7.2f}")

# ---- secondaries, read against the pre-registration ----------------------
base = None
for n in names:
    if n.endswith('g0'): base = n
if base and base in rows:
    b = rows[base]
    print(f"\nagainst the exact zero arm ({base}), as % change:")
    print(f"{'bot':<14}{'xfer':>9}{'starv':>9}{'soldR':>9}{'paint':>9}{'paint/soldR':>13}{'dCov':>9}{'twPaint':>9}{'spawn':>8}{'conv':>8}")
    for n in names:
        if n == base or n not in rows: continue
        r = rows[n]
        def pc(k):
            return (r[k]-b[k])/b[k]*100 if b[k] else float('nan')
        print(f"{n:<14}{pc('xfer'):>+9.1f}{pc('starv'):>+9.1f}{pc('soldR'):>+9.1f}"
              f"{pc('paint'):>+9.1f}{pc('psr'):>+13.1f}{pc('dcov'):>+9.1f}"
              f"{pc('twp'):>+9.1f}{pc('spawn'):>+8.1f}"
              f"{((r['dcov']/r['paint'])-(b['dcov']/b['paint']))/(b['dcov']/b['paint'])*100:>+8.1f}")

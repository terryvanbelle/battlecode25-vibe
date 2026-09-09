#!/usr/bin/env python3
"""Aggregate bob-tools/early-paint-census.sh output.

Reads the raw `round N | T1 ... | T2 ...` lines and reports, per map-area
stratum, the early-game PAINT FLOW of each side: paint actions taken, splash
actions taken, coverage reached, tower paint remaining, units alive.

The point of separating actions from coverage: they answer different questions.
Actions say how much the army DID; coverage says how much of it stuck.
"""
import sys, re, csv, collections, statistics

LIMIT = 30
geo = {}
with open(sys.argv[2]) as fh:
    for r in csv.DictReader(fh):
        if not r.get('W'): continue
        geo[r['map']] = int(r['W']) * int(r['H'])

TEAM = re.compile(
    r"T(?P<tid>\d) \$(?P<money>\d+) cov(?P<cov>\d+)m srp(?P<srp>\d+) "
    r"sold(?P<sold>\d+) spl(?P<spl>\d+) mop(?P<mop>\d+) tw(?P<tw>\d+) "
    r"twPaint(?P<twp>\d+) acts\[p(?P<p>\d+) u(?P<u>\d+) a(?P<a>\d+) "
    r"s(?P<s>\d+) m(?P<m>\d+)\] \+sold(?P<ns>\d+) \+mop(?P<nm>\d+) "
    r"\+spl(?P<nl>\d+) died(?P<died>\d+) xfer(?P<xf>\d+) starved(?P<st>\d+)")

games = collections.defaultdict(lambda: {'t': {}, 'cum': collections.defaultdict(collections.Counter),
                                         'last': {}, 'cov20': {}})
for line in open(sys.argv[1]):
    parts = line.rstrip('\n').split('\t')
    if len(parts) < 3:
        continue
    f, kind, body = parts[0], parts[1], parts[2]
    g = games[f]
    if kind == 'HDR':
        m = re.search(r'team1=(\S+)\s+team2=(\S+)', body)
        if m:
            g['t'] = {'1': m.group(1), '2': m.group(2)}
    elif kind == 'RND':
        mr = re.match(r'round (\d+) \|', body)
        if not mr:
            continue
        rnd = int(mr.group(1))
        if rnd > LIMIT:
            continue
        for mt in TEAM.finditer(body):
            d = mt.groupdict(); tid = d['tid']
            for k in ('p', 'u', 'a', 's', 'm', 'ns', 'nl', 'nm', 'died', 'st', 'xf'):
                g['cum'][tid][k] += int(d[k])
            g['last'][tid] = d
            if rnd == 20:
                g['cov20'][tid] = int(d['cov'])
    elif kind == 'FTR':
        mw = re.search(r'winner=team(\d)', body)
        if mw:
            g['win'] = mw.group(1)

if not games:
    sys.exit("!! parsed ZERO games -- input empty or format changed")

rows = []
for f, g in games.items():
    if not g['t'] or '1' not in g['last'] or '2' not in g['last']:
        continue
    mp = re.search(r'-on-(.+)\.bc25', f).group(1)
    area = geo.get(mp)
    if area is None:
        sys.stderr.write(f"!! no geometry for map {mp}\n"); continue
    rec = {'map': mp, 'area': area, 'file': f}
    for tid in ('1', '2'):
        who = g['t'][tid]
        L, C = g['last'][tid], g['cum'][tid]
        rec[who] = dict(cov=int(L['cov']), cov20=g['cov20'].get(tid, 0), sold=int(L['sold']),
                        spl=int(L['spl']), twp=int(L['twp']), money=int(L['money']),
                        p=C['p'], s=C['s'], a=C['a'], died=C['died'], st=C['st'],
                        nsold=C['ns'], nspl=C['nl'], xfer=C['xf'])
    rec['win'] = g['t'][g['win']] if 'win' in g else '?'
    rows.append(rec)

rows.sort(key=lambda r: r['area'])
n = len(rows)
strata = [('small', rows[:n // 3]), ('medium', rows[n // 3:2 * n // 3]), ('large', rows[2 * n // 3:])]
A, B = 'bob', 'carol'

print(f"{n} games,  rounds 1-{LIMIT},  {A} vs {B}\n")
hdr = (f"{'stratum':>8} {'n':>3} {'area':>5} {'win%':>6} | "
       f"{A+' paintAct':>11} {A+' splash':>9} {A+' cov':>7} {A+' twP':>7} {A+' sold':>8} | "
       f"{B+' paintAct':>13} {B+' splash':>11} {B+' cov':>9} {B+' twP':>9} {B+' sold':>10}")
print(hdr); print('-' * len(hdr))
for name, rs in strata:
    if not rs:
        continue
    mean = lambda who, k: statistics.mean(r[who][k] for r in rs)
    wr = 100.0 * sum(1 for r in rs if r['win'] == A) / len(rs)
    print(f"{name:>8} {len(rs):>3} {statistics.mean(r['area'] for r in rs):>5.0f} {wr:>5.1f}% | "
          f"{mean(A,'p'):>11.1f} {mean(A,'s'):>9.1f} {mean(A,'cov'):>7.1f} {mean(A,'twp'):>7.0f} {mean(A,'sold'):>8.2f} | "
          f"{mean(B,'p'):>13.1f} {mean(B,'s'):>11.1f} {mean(B,'cov'):>9.1f} {mean(B,'twp'):>9.0f} {mean(B,'sold'):>10.2f}")

print("\ncoverage trajectory (per-mille) and paint stock")
h2 = (f"{'stratum':>8} | {A+' cov20':>9} {A+' cov30':>9} {A+' d20-30':>10} {A+' twP30':>9} {A+' starv':>8} "
      f"| {B+' cov20':>11} {B+' cov30':>11} {B+' d20-30':>12} {B+' twP30':>11}")
print(h2); print('-' * len(h2))
for name, rs in strata:
    if not rs:
        continue
    mean = lambda who, k: statistics.mean(r[who][k] for r in rs)
    print(f"{name:>8} | {mean(A,'cov20'):>9.1f} {mean(A,'cov'):>9.1f} "
          f"{mean(A,'cov')-mean(A,'cov20'):>10.1f} {mean(A,'twp'):>9.0f} {mean(A,'st'):>8.2f} "
          f"| {mean(B,'cov20'):>11.1f} {mean(B,'cov'):>11.1f} "
          f"{mean(B,'cov')-mean(B,'cov20'):>12.1f} {mean(B,'twp'):>11.0f}")

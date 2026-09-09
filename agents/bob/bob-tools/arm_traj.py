#!/usr/bin/env python3
"""Compare the PRODUCTION of several arms from early-paint-census.sh output.

Written for iteration 41's zero-game re-read of iteration 40's own run. Iteration
40 lifted the round-60 splasher gate on small maps and produced only 1.00 splasher
at r30 where the 2-of-5 slot mix predicts about 2. The question this answers is
whether the arm ALSO built fewer units in total -- which is what the spawn stall
predicts (a tower on an unaffordable splasher slot builds nothing and does not
advance the slot), and which would mean iteration 40 never tested early splashers
at all, only early splashers crippled by a jam.

Usage: arm_traj.py <census.tsv> <srp-sites.csv> <maxArea> <arm> [arm ...]
"""
import sys, re, csv, statistics, collections

TEAM = re.compile(r"T(?P<tid>\d) \$(?P<money>\d+) cov(?P<cov>\d+)m srp(?P<srp>\d+) sold(?P<sold>\d+) spl(?P<spl>\d+) mop(?P<mop>\d+) tw(?P<tw>\d+) twPaint(?P<twp>\d+) acts\[p(?P<p>\d+) u(?P<u>\d+) a(?P<a>\d+) s(?P<s>\d+) m(?P<m>\d+)\] \+sold(?P<ns>\d+) \+mop(?P<nm>\d+) \+spl(?P<nl>\d+) died(?P<died>\d+) xfer(?P<xf>\d+) starved(?P<st>\d+)")

census, sites, maxArea = sys.argv[1], sys.argv[2], int(sys.argv[3])
arms = sys.argv[4:]
geo = {r['map']: int(r['W']) * int(r['H']) for r in csv.DictReader(open(sites)) if r.get('W')}

G = collections.defaultdict(lambda: {'t': {}, 'c': collections.defaultdict(collections.Counter),
                                     'last': {}})
for line in open(census):
    p = line.rstrip('\n').split('\t')
    if len(p) < 3:
        continue
    f, kind, body = p
    g = G[f]
    if kind == 'HDR':
        m = re.search(r'team1=(\S+)\s+team2=(\S+)', body)
        if m:
            g['t'] = {'1': m.group(1), '2': m.group(2)}
    elif kind == 'RND':
        for mt in TEAM.finditer(body):
            d = mt.groupdict(); tid = d['tid']
            for k in ('p', 'ns', 'nl', 'nm', 'died'):
                g['c'][tid][k] += int(d[k])
            g['last'][tid] = d
    elif kind == 'FTR':
        mw = re.search(r'winner=team(\d)', body)
        if mw:
            g['win'] = mw.group(1)

acc = collections.defaultdict(list)
for f, g in G.items():
    if not g['t'] or '1' not in g['last']:
        continue
    mp = re.search(r'__(.+?)__bot', f)
    if not mp:
        continue
    area = geo.get(mp.group(1))
    if area is None or area >= maxArea:
        continue
    for tid, who in g['t'].items():
        if who not in arms:
            continue
        L, C = g['last'][tid], g['c'][tid]
        acc[who].append(dict(sold=int(L['sold']), spl=int(L['spl']), mop=int(L['mop']),
                             twp=int(L['twp']), cov=int(L['cov']), p=C['p'],
                             ns=C['ns'], nl=C['nl'], nm=C['nm'], died=C['died'],
                             win=(g.get('win') == tid)))

if not acc:
    sys.exit("!! no games matched -- check arm names and maxArea")

print(f"maps with area < {maxArea}; arm-side totals through the censused window\n")
print(f"{'arm':>9} {'n':>4} {'win%':>6} {'+sold':>6} {'+spl':>6} {'+mop':>6} {'TOTAL built':>12} "
      f"{'alive':>6} {'died':>6} {'twPaint':>8} {'paintAct':>9} {'cov':>7}")
for a in arms:
    rs = acc.get(a)
    if not rs:
        print(f"{a:>9}   (no games)"); continue
    m = lambda k: statistics.mean(r[k] for r in rs)
    tot = m('ns') + m('nl') + m('nm')
    print(f"{a:>9} {len(rs):>4} {100*sum(r['win'] for r in rs)/len(rs):>5.1f}% "
          f"{m('ns'):>6.2f} {m('nl'):>6.2f} {m('nm'):>6.2f} {tot:>12.2f} "
          f"{m('sold')+m('spl')+m('mop'):>6.2f} {m('died'):>6.2f} {m('twp'):>8.0f} "
          f"{m('p'):>9.1f} {m('cov'):>7.1f}")

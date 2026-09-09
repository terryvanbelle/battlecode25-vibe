#!/usr/bin/env python3
"""Iteration 43 secondaries, from a run's own replays.

Usage: seek_eval.py <census.tsv> <srp-sites.csv> <arm> [arm ...]

Reports per arm, split by map-area tercile:
  soldierRounds   integrated alive count (NOT final headcount x rounds -- LEARNING 71)
  paintAct        PaintActions in the window
  tiles/soldRnd   the registered MECHANISM secondary; must rise vs the zero arm
  tw, cov         tower count and coverage at the window's end
The arm's own team is identified from the GameHeader, so side never has to be
inferred from the filename.
"""
import sys, re, csv, statistics, collections

TEAM = re.compile(r"T(?P<tid>\d) \$(?P<money>\d+) cov(?P<cov>\d+)m srp(?P<srp>\d+) sold(?P<sold>\d+) spl(?P<spl>\d+) mop(?P<mop>\d+) tw(?P<tw>\d+) twPaint(?P<twp>\d+) acts\[p(?P<p>\d+) u(?P<u>\d+) a(?P<a>\d+) s(?P<s>\d+) m(?P<m>\d+)\] \+sold(?P<ns>\d+) \+mop(?P<nm>\d+) \+spl(?P<nl>\d+) died(?P<died>\d+) xfer(?P<xf>\d+) starved(?P<st>\d+)")

census, sites = sys.argv[1], sys.argv[2]
arms = sys.argv[3:]
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
            d = mt.groupdict(); tid = d['tid']; C = g['c'][tid]
            C['p'] += int(d['p']); C['a'] += int(d['a']); C['s'] += int(d['s'])
            C['soldR'] += int(d['sold'])          # stride-1 integral of alive count
            C['splR'] += int(d['spl'])
            g['last'][tid] = d
    elif kind == 'FTR':
        mw = re.search(r'winner=team(\d)', body)
        if mw:
            g['win'] = mw.group(1)

rows = []
for f, g in G.items():
    if not g['t'] or '1' not in g['last']:
        continue
    mp = re.search(r'__(.+?)__bot', f)
    if not mp:
        continue
    area = geo.get(mp.group(1))
    if area is None:
        continue
    for tid, who in g['t'].items():
        if who not in arms:
            continue
        L, C = g['last'][tid], g['c'][tid]
        rows.append(dict(arm=who, area=area, soldR=C['soldR'], p=C['p'],
                         tw=int(L['tw']), cov=int(L['cov']),
                         win=(g.get('win') == tid)))
if not rows:
    sys.exit("!! no games matched -- check arm names")

rows.sort(key=lambda r: r['area'])
n = len(rows) // len(arms)
def stratum(r, cut):
    return r['area'] < cut[0] and 'small' or (r['area'] < cut[1] and 'medium' or 'large')
areas = sorted({r['area'] for r in rows})
cut = (areas[len(areas)//3], areas[2*len(areas)//3])

print(f"area cuts: small < {cut[0]} <= medium < {cut[1]} <= large\n")
hdr = f"{'stratum':>8} {'arm':>9} {'n':>4} {'win%':>6} {'soldRnd':>9} {'paintAct':>9} {'tiles/soldRnd':>14} {'tw':>5} {'cov':>7}"
print(hdr); print('-' * len(hdr))
for s in ('small', 'medium', 'large', 'ALL'):
    for a in arms:
        rs = [r for r in rows if r['arm'] == a and (s == 'ALL' or stratum(r, cut) == s)]
        if not rs:
            continue
        m = lambda k: statistics.mean(r[k] for r in rs)
        sr = m('soldR')
        print(f"{s if a==arms[0] else '':>8} {a:>9} {len(rs):>4} "
              f"{100*sum(r['win'] for r in rs)/len(rs):>5.1f}% {sr:>9.1f} {m('p'):>9.1f} "
              f"{m('p')/sr if sr else 0:>14.3f} {m('tw'):>5.2f} {m('cov'):>7.1f}")
    print()

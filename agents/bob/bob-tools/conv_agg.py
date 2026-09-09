#!/usr/bin/env python3
"""Paint-action -> COVERAGE conversion, in the objective's own units (LEARNING 76).

Usage: conv_agg.py <census.tsv> <srp-sites.csv> [--window R] [--names a,b]

Every prize this lineage priced in iterations 37-43 was a per-soldier-round RATIO,
and iteration 43 showed the mechanism can shrink that ratio's denominator. The
objective is TOTAL PAINTED AREA. This reads, per team per game:

  acts        paint actions taken in the window   (acts[p] per-round + acts[s] splash)
  dTiles      NET coverage gained, in tiles       (d(cov per-mille) * area / 1000)
  conv        dTiles / acts -- tiles of coverage bought per action taken

conv < 1 means actions are not becoming coverage: repainting own tiles, painting
tiles the enemy then takes back, or pattern churn. It is a LOWER bound on gross
painting because the enemy subtracts from cov -- so it is a conversion measure,
not a churn measure, and the writeup must say so.
"""
import sys, re, csv, collections, statistics

TEAM = re.compile(r"T(?P<tid>\d) \$(?P<money>\d+) cov(?P<cov>\d+)m srp(?P<srp>\d+) sold(?P<sold>\d+) "
                  r"spl(?P<spl>\d+) mop(?P<mop>\d+) tw(?P<tw>\d+) twPaint(?P<twp>\d+) "
                  r"acts\[p(?P<p>\d+) u(?P<u>\d+) a(?P<a>\d+) s(?P<s>\d+) m(?P<m>\d+)\]")

args = sys.argv[1:]
census, sites = args[0], args[1]
window = 10**9
names = None
for i, a in enumerate(args):
    if a == '--window': window = int(args[i+1])
    if a == '--names':  names = args[i+1].split(',')

geo = {r['map']: int(r['W']) * int(r['H']) for r in csv.DictReader(open(sites)) if r.get('W')}

G = collections.defaultdict(lambda: {'t': {}, 'acts': collections.Counter(),
                                     'cov0': {}, 'cov1': {}, 'sold': collections.Counter(),
                                     'mop': collections.Counter(), 'n': collections.Counter(),
                                     'robo': collections.Counter(), 'splU': collections.Counter(),
                                     'mopU': collections.Counter(), 'actP': collections.Counter(),
                                     'actS': collections.Counter()})
for line in open(census):
    parts = line.rstrip('\n').split('\t')
    if len(parts) < 3: continue
    f, kind, body = parts
    g = G[f]
    if kind == 'HDR':
        m = re.search(r'team1=(\S+)\s+team2=(\S+)', body)
        if m: g['t'] = {'1': m.group(1), '2': m.group(2)}
    elif kind == 'RND':
        rm = re.match(r'round (\d+)', body)
        if not rm: continue
        rnd = int(rm.group(1))
        if rnd > window: continue
        for mt in TEAM.finditer(body):
            d = mt.groupdict(); tid = d['tid']
            g['acts'][tid] += int(d['p']) + int(d['s'])
            g['mop'][tid] += int(d['m'])
            g['sold'][tid] += int(d['sold'])
            g['robo'][tid] += int(d['sold']) + int(d['spl']) + int(d['mop'])
            g['splU'][tid] += int(d['spl'])
            g['mopU'][tid] += int(d['mop'])
            g['actP'][tid] += int(d['p'])
            g['actS'][tid] += int(d['s'])
            g['n'][tid] += 1
            if tid not in g['cov0']: g['cov0'][tid] = int(d['cov'])
            g['cov1'][tid] = int(d['cov'])

rows = []
for f, g in G.items():
    mp = re.search(r'__(.+?)__bot', f) or re.search(r'-on-(.+?)\.bc25', f)
    if not mp or not g['t']: continue
    area = geo.get(mp.group(1))
    if area is None: continue
    for tid, who in g['t'].items():
        if names and who not in names: continue
        if tid not in g['cov0']: continue
        dt = (g['cov1'][tid] - g['cov0'][tid]) * area / 1000.0
        other = '2' if tid == '1' else '1'
        rows.append(dict(who=who, area=area, acts=g['acts'][tid], dT=dt,
                         soldR=g['sold'][tid], rounds=g['n'][tid], map=mp.group(1),
                         roboR=g['robo'][tid], splU=g['splU'][tid], mopU=g['mopU'][tid],
                         actP=g['actP'][tid], actS=g['actS'][tid],
                         oppMop=g['mop'][other], oppActs=g['acts'][other],
                         opp=g['t'].get(other, '?'), game=f))
if not rows:
    sys.exit("!! no rows -- check names/filter")

areas = sorted({r['area'] for r in rows})
cut = (areas[len(areas)//3], areas[2*len(areas)//3])
def stratum(r):
    return 'small' if r['area'] < cut[0] else ('medium' if r['area'] < cut[1] else 'large')

who_list = names or sorted({r['who'] for r in rows})
print(f"window <= r{window}   area cuts: small < {cut[0]} <= medium < {cut[1]} <= large\n")
hdr = f"{'stratum':>8} {'team':>12} {'n':>4} {'acts':>8} {'dTiles':>9} {'conv':>7} {'soldRnd':>9} {'a/soldR':>8} {'a/roboR':>8} {'splU%':>6} {'mopU%':>6} {'actS%':>6}"
print(hdr); print('-'*len(hdr))
for s in ('small','medium','large','ALL'):
    for w in who_list:
        rs = [r for r in rows if r['who']==w and (s=='ALL' or stratum(r)==s)]
        if not rs: continue
        m = lambda k: statistics.mean(r[k] for r in rs)
        A, T, SR = m('acts'), m('dT'), m('soldR')
        print(f"{s if w==who_list[0] else '':>8} {w:>12} {len(rs):>4} {A:>8.1f} {T:>9.1f} "
              f"{T/A if A else 0:>7.3f} {SR:>9.1f} {A/SR if SR else 0:>8.3f} "
              f"{A/m('roboR') if m('roboR') else 0:>8.3f} "
              f"{100*m('splU')/m('roboR') if m('roboR') else 0:>6.1f} "
              f"{100*m('mopU')/m('roboR') if m('roboR') else 0:>6.1f} "
              f"{100*m('actS')/A if A else 0:>6.1f}")
    print()


# ---- PAIRED within-game ratios: the registered primary for iteration 44 ----
# Pair rows by game file so map, round count and board state are held exactly.
by_game = collections.defaultdict(dict)
for r in rows:
    by_game[r['game']][r['who']] = r

def paired(me, them, want):
    out = []
    for f, d in by_game.items():
        if me in d and them in d and (want is None or stratum(d[me]) == want):
            out.append((d[me], d[them]))
    return out

mine = [w for w in who_list if w.startswith('bob')]
others = sorted({r['opp'] for r in rows if not r['opp'].startswith('bob')})
if mine and others:
    print("PAIRED within-game (registered primary). ratio = mean(bob) / mean(opponent) on the SAME games.\n")
    h2 = f"{'stratum':>8} {'me':>10} {'vs':>10} {'games':>6} {'ratio_acts':>11} {'ratio_tiles':>12} {'conv_me':>8} {'conv_opp':>9}"
    print(h2); print('-'*len(h2))
    for s_ in ('small','medium','large','ALL'):
        for me in mine:
            for th in others:
                pr = paired(me, th, None if s_=='ALL' else s_)
                if not pr: continue
                aM = statistics.mean(a['acts'] for a,b in pr); aO = statistics.mean(b['acts'] for a,b in pr)
                tM = statistics.mean(a['dT'] for a,b in pr);  tO = statistics.mean(b['dT'] for a,b in pr)
                print(f"{s_:>8} {me:>10} {th:>10} {len(pr):>6} {aM/aO if aO else 0:>11.3f} "
                      f"{tM/tO if tO else 0:>12.3f} {tM/aM if aM else 0:>8.3f} {tO/aO if aO else 0:>9.3f}")
        print()

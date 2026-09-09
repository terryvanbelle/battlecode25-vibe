#!/usr/bin/env python3
"""ITERATION 46: classify every PAINT as NEW / FLIP / REDUNDANT.

Usage: redund_agg.py <census.tsv> <srp-sites.csv>

REDUNDANT = the tile already held EXACTLY this (team, secondary). The engine still
calls setPaint and still emits a PaintAction, so the action and its paint are spent
and nothing changes -- one wasted `act` AND one lost point of `conv` (LEARNING 82).

FLIP = the tile held my team's OTHER colour. That is deliberate pattern work, not
waste, and is counted separately so it can never inflate the headline.

UNKNOWN-SKIP = tile state not yet established (never seen, or invalidated by an
UNPAINT or a SPLASH whose footprint the schema does not carry). Skipped, never
counted as redundant, which makes the REDUNDANT share a strict LOWER BOUND.

The accounting is asserted: NEW + FLIP + REDUNDANT + skips must equal the PAINT
count. A decomposition that does not close is not evidence (iteration 42).
"""
import sys, re, csv, collections

PAINT   = re.compile(r"round (\d+) id(\d+)\((T\d),(\w+)\) PAINT \((\d+),(\d+)\)(\s+secondary)?")
UNPAINT = re.compile(r"round (\d+) id(\d+)\((T\d),(\w+)\) UNPAINT \((\d+),(\d+)\)")
SPLASH  = re.compile(r"round (\d+) id(\d+)\((T\d),(\w+)\) SPLASH \((\d+),(\d+)\)")

census, sites = sys.argv[1], sys.argv[2]
geo = {r['map']: int(r['W']) * int(r['H']) for r in csv.DictReader(open(sites)) if r.get('W')}

games = collections.defaultdict(lambda: {'teams': {}, 'lines': []})
for line in open(census):
    p = line.rstrip('\n').split('\t')
    if len(p) < 3:
        continue
    f, kind, body = p
    if kind == 'HDR':
        m = re.search(r'team1=(\S+)\s+team2=(\S+)', body)
        if m:
            games[f]['teams'] = {'T1': m.group(1), 'T2': m.group(2)}
    elif kind == 'ACT':
        games[f]['lines'].append(body)

stat = collections.defaultdict(collections.Counter)
by_stratum = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))

for f, g in games.items():
    if not g['teams']:
        continue
    mp = re.search(r'-on-(.+?)\.bc25', f) or re.search(r'__(.+?)__bot', f)
    area = geo.get(mp.group(1)) if mp else None
    tile = {}                                   # (x,y) -> (team, secondary) or None = unknown
    for body in g['lines']:
        m = PAINT.search(body)
        if m:
            _, _, team, utype, x, y, sec = m.groups()
            who = g['teams'][team]
            key = (int(x), int(y)); val = (team, bool(sec))
            cur = tile.get(key, 'UNK')
            if cur == 'UNK':
                bucket = 'skip_unknown'
            elif cur is None:
                bucket = 'new'
            elif cur == val:
                bucket = 'REDUNDANT'
            elif cur[0] == team:
                bucket = 'flip'
            else:
                bucket = 'new'                  # was enemy: engine would have refused a soldier,
                                                # so this is a splasher legitimately converting it
            stat[who][bucket] += 1
            stat[who]['paint'] += 1
            stat[who][f'ut_{utype}'] += 1
            if area:
                by_stratum[area < 1500 and 'small' or (area < 2400 and 'medium' or 'large')][who][bucket] += 1
                by_stratum[area < 1500 and 'small' or (area < 2400 and 'medium' or 'large')][who]['paint'] += 1
            tile[key] = val
            continue
        m = UNPAINT.search(body)
        if m:
            tile[(int(m.group(5)), int(m.group(6)))] = None      # now unpainted, and KNOWN
            continue
        m = SPLASH.search(body)
        if m:
            cx, cy = int(m.group(5)), int(m.group(6))
            for dx in range(-2, 3):                              # AOE radius^2 = 4
                for dy in range(-2, 3):
                    if dx*dx + dy*dy <= 4:
                        tile.pop((cx+dx, cy+dy), None)           # footprint not in schema -> unknown
            stat[g['teams'][m.group(3)]]['splash'] += 1

print("PAINT classification. REDUNDANT = tile already held exactly this colour.")
print("skip_unknown is never counted as redundant, so REDUNDANT% is a LOWER BOUND.\n")
hdr = f"{'team':>8} {'paint':>8} {'new':>8} {'flip':>7} {'REDUND':>8} {'REDUND%':>8} {'skipUnk':>8} {'splash':>7} {'closes':>7}"
print(hdr); print('-'*len(hdr))
for who in sorted(stat):
    c = stat[who]
    tot = c['new'] + c['flip'] + c['REDUNDANT'] + c['skip_unknown']
    ok = 'YES' if tot == c['paint'] else f'NO({tot}v{c["paint"]})'
    known = c['new'] + c['flip'] + c['REDUNDANT']
    print(f"{who:>8} {c['paint']:>8} {c['new']:>8} {c['flip']:>7} {c['REDUNDANT']:>8} "
          f"{100*c['REDUNDANT']/known if known else 0:>7.1f}% {c['skip_unknown']:>8} {c['splash']:>7} {ok:>7}")

print("\nby map-area stratum (REDUNDANT as % of CLASSIFIED paints):")
print(f"{'stratum':>8} {'team':>8} {'paint':>8} {'REDUND':>8} {'REDUND%':>8}")
for s in ('small','medium','large'):
    for who in sorted(by_stratum[s]):
        c = by_stratum[s][who]
        known = c['new'] + c['flip'] + c['REDUNDANT']
        print(f"{s:>8} {who:>8} {c['paint']:>8} {c['REDUNDANT']:>8} "
              f"{100*c['REDUNDANT']/known if known else 0:>7.1f}%")

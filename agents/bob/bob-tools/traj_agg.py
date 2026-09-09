#!/usr/bin/env python3
"""Per-round-bucket trajectory from early-paint-census.sh output (any stride).

Prints, for each sampled round, both teams' unit mix, tower paint, chips,
coverage and paint actions in the preceding window. Used to test whether bob's
fixed spawn rotation stalls: a tower holding 200-299 paint can build a SOLDIER
but not a SPLASHER (engine: assertCanBuildRobot throws on paint < paintCost),
and Tower.run() advances `spawned` only on a successful build.
"""
import sys, re, csv, statistics, collections

TEAM = re.compile(r"T(?P<tid>\d) \$(?P<money>\d+) cov(?P<cov>\d+)m srp(?P<srp>\d+) sold(?P<sold>\d+) spl(?P<spl>\d+) mop(?P<mop>\d+) tw(?P<tw>\d+) twPaint(?P<twp>\d+) acts\[p(?P<p>\d+) u(?P<u>\d+) a(?P<a>\d+) s(?P<s>\d+) m(?P<m>\d+)\] \+sold(?P<ns>\d+) \+mop(?P<nm>\d+) \+spl(?P<nl>\d+) died(?P<died>\d+) xfer(?P<xf>\d+) starved(?P<st>\d+)")

geo = {}
for r in csv.DictReader(open(sys.argv[2])):
    if r.get('W'):
        geo[r['map']] = int(r['W']) * int(r['H'])

# per (round, team) -> list of dicts ; only games still alive at that round
data = collections.defaultdict(lambda: collections.defaultdict(list))
names = {}
alive = collections.Counter()
for line in open(sys.argv[1]):
    p = line.rstrip('\n').split('\t')
    if len(p) < 3 or p[1] != 'RND':
        if len(p) >= 3 and p[1] == 'HDR':
            m = re.search(r'team1=(\S+)\s+team2=(\S+)', p[2])
            if m:
                names[p[0]] = {'1': m.group(1), '2': m.group(2)}
        continue
    f, body = p[0], p[2]
    mr = re.match(r'round (\d+) \|', body)
    if not mr or f not in names:
        continue
    rnd = int(mr.group(1))
    for mt in TEAM.finditer(body):
        d = mt.groupdict()
        data[rnd][names[f][d['tid']]].append({k: int(v) for k, v in d.items()})
    alive[rnd] += 1

if not data:
    sys.exit("!! parsed ZERO rounds")

print(f"{'round':>6} {'games':>6} | {'who':>6} {'sold':>5} {'spl':>5} {'mop':>5} {'tw':>4} {'twPaint':>8} {'chips':>6} {'cov':>6} {'paintAct/rnd':>13} {'+sold':>6} {'+spl':>5}")
for rnd in sorted(data):
    if alive[rnd] < 15:
        break
    for who in ('bob', 'carol'):
        rs = data[rnd].get(who)
        if not rs:
            continue
        m = lambda k: statistics.mean(r[k] for r in rs)
        print(f"{rnd if who=='bob' else '':>6} {alive[rnd] if who=='bob' else '':>6} | {who:>6} "
              f"{m('sold'):>5.2f} {m('spl'):>5.2f} {m('mop'):>5.2f} {m('tw'):>4.1f} {m('twp'):>8.0f} "
              f"{m('money'):>6.0f} {m('cov'):>6.1f} {m('p'):>13.1f} {m('ns'):>6.2f} {m('nl'):>5.2f}")
    print()

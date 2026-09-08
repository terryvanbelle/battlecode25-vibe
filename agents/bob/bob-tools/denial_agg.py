#!/usr/bin/env python3
"""Aggregate bob-tools/denial-probe.sh batch output.

Splits every (team, unit-type) observation by whether that team WON the game,
because the only replays kept locally are losses and each one therefore
contains exactly one winning and one losing side. Reporting a pooled number
would mix the two populations.
"""
import re, sys, collections

txt = open(sys.argv[1]).read()
blocks = txt.split('## ')[1:]
acc = collections.defaultdict(lambda: collections.Counter())
games = collections.Counter()

row_re = re.compile(r'^\s+T(\d)\s+(MOPPER|SPLASHER)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+\|\s+(\d+)\s+(\d+)\s+([\d.]+)', re.M)
take_re = re.compile(r'T(\d) (MOPPER|SPLASHER)\s+utilisation.*?\((\d+) taken / (\d+) opportunities\).*?nothing in vision\s+([\d.]+)%', re.M)
win_re = re.compile(r'winner=team(\d)')

for b in blocks:
    w = win_re.search(b)
    if not w:
        continue
    winner = int(w.group(1))
    takes = {(int(m.group(1)), m.group(2)): (int(m.group(3)), int(m.group(4))) for m in take_re.finditer(b)}
    for m in row_re.finditer(b):
        t = int(m.group(1)); ty = m.group(2)
        key = ('WON ' if t == winner else 'LOST', ty)
        c = acc[key]
        c['rounds'] += int(m.group(3)); c['ready'] += int(m.group(4))
        c['vis'] += int(m.group(5)); c['inRange'] += int(m.group(6))
        c['rdyInR'] += int(m.group(7)); c['acted'] += int(m.group(8))
        c['denied'] += int(m.group(9))
        tk = takes.get((t, ty))
        if tk:
            c['taken'] += tk[0]; c['opp'] += tk[1]
        games[key] += 1

CEIL = {'MOPPER': 1/3.0, 'SPLASHER': 1/5.0}
print(f"{'side':5} {'type':9} {'games':>5} {'unit-rounds':>12} {'acted':>7} {'util%ceil':>10} "
      f"{'inRange%':>9} {'take-rate%':>11} {'idle,noTgt%':>12}")
for key in sorted(acc):
    side, ty = key
    c = acc[key]
    n = c['rounds']
    util = 100.0 * (c['acted'] / n) / CEIL[ty]
    take = 100.0 * c['taken'] / c['opp'] if c['opp'] else float('nan')
    print(f"{side:5} {ty:9} {games[key]:5d} {n:12d} {c['acted']:7d} {util:10.1f} "
          f"{100.0*c['inRange']/n:9.1f} {take:11.1f} {100.0*(c['ready']-c['rdyInR'])/n:12.1f}")

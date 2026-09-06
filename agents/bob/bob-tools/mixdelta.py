#!/usr/bin/env python3
"""Join a gauntlet's per-map result against how much iteration 7's hash actually
changed that map's tower mix.

The point: a win-rate delta alone cannot tell a real causal effect from churn.
But this change's size is known EXACTLY per map before any game is played (it is a
pure function of the ruin coordinates in the map file), so the per-map results can
be sorted by dose. If the maps the change improves are the maps we win and the maps
it worsens are the maps we lose, that is dose-response, not noise.

Usage: mixdelta.py <gauntlet-run-dir> <ruins.csv> [opponent]
"""
import sys, csv, collections

run, ruins_path = sys.argv[1], sys.argv[2]
opp = sys.argv[3] if len(sys.argv) > 3 else None

gain = {}
for line in open(ruins_path):
    p = line.strip().split(',')
    if len(p) < 8 or p[0] == 'map':
        continue
    try:
        r, om, nm = int(p[3]), int(p[4]), int(p[5])
    except ValueError:
        continue
    old_dev = abs(100 * om / r - 50)
    new_dev = abs(100 * nm / r - 50)
    gain[p[0]] = old_dev - new_dev      # >0: the hash makes this map's mix better

res = collections.defaultdict(list)
for row in csv.DictReader(open(f"{run}/results.csv")):
    if opp and row['opponent'] != opp:
        continue
    res[row['map']].append(row['bot_result'])

rows = []
for m, rs in res.items():
    if m not in gain:
        continue
    w = rs.count('win')
    rows.append((gain[m], m, w, len(rs)))
rows.sort(reverse=True)

print(f"{'map':<18}{'mixGain':>9}{'wins':>7}{'games':>7}  shape")
buckets = {'better': [0, 0], 'same': [0, 0], 'worse': [0, 0]}
for g, m, w, n in rows:
    shape = 'SWEPT WIN' if w == n else ('SWEPT LOSS' if w == 0 else 'split')
    print(f"{m:<18}{g:>9.0f}{w:>7}{n:>7}  {shape}")
    k = 'better' if g > 5 else ('worse' if g < -5 else 'same')
    buckets[k][0] += w
    buckets[k][1] += n

print()
print("win rate grouped by whether the change improved that map's tower mix:")
for k in ('better', 'same', 'worse'):
    w, n = buckets[k]
    if n:
        print(f"  mix {k:<7} {w:>3}/{n:<3} ({100*w/n:.0f}%)")

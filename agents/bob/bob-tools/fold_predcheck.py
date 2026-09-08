#!/usr/bin/env python3
"""Iteration 22's map-level prediction, checked as an exact identity.

min(x, W-1-x) is congruent to x (mod 2) exactly when W is odd, so on a map with
BOTH dimensions odd the folded tower rule is the same function as the plain one
and the games must be identical. All deviation must land on maps with an even
dimension.

Deterministic-engine proxy for "identical game": same winner AND same round count.
That is the proxy this lineage already uses; it is not literal byte-identity, so a
deviation it reports is certain while an agreement it reports is very strong but
not a proof.

Usage: bob-tools/fold_predcheck.py gauntlet/<run-id> [control-arm] [candidate-arm]
"""
import csv, re, sys, os

run = sys.argv[1]
ctrl = sys.argv[2] if len(sys.argv) > 2 else 'bob_tp0'
cand = sys.argv[3] if len(sys.argv) > 3 else 'bob_tp1'
here = os.path.dirname(os.path.abspath(__file__))

dims = {}
for ln in open(os.path.join(here, 'foldscan', 'fold_vs_plain.txt')):
    m = re.match(r'^(\S+)\s+(\d+)x(\d+)\s', ln)
    if m:
        dims[m.group(1)] = (int(m.group(2)), int(m.group(3)))

games = {}
with open(os.path.join(run, 'results.csv')) as f:
    for r in csv.DictReader(f):
        games[(r['opponent'], r['map'], r['bot_side'])] = (r['winner_side'], r['rounds'])

maps = sorted({k[1] for k in games})
oddodd_dev, even_dev, oddodd_n, even_n = [], [], 0, 0
for mp in maps:
    W, H = dims.get(mp, (0, 0))
    both_odd = W % 2 == 1 and H % 2 == 1
    for side in ('A', 'B'):
        a, b = games.get((ctrl, mp, side)), games.get((cand, mp, side))
        if a is None or b is None:
            continue
        if both_odd: oddodd_n += 1
        else: even_n += 1
        if a != b:
            (oddodd_dev if both_odd else even_dev).append((mp, side, a, b))

print(f"run {os.path.basename(run.rstrip('/'))}   {ctrl} (control) vs {cand} (candidate)")
print(f"  odd x odd cells        {oddodd_n:3d}   deviations {len(oddodd_dev)}   <- PREDICTED 0")
print(f"  even-dimension cells   {even_n:3d}   deviations {len(even_dev)}   <- all change predicted here")
if oddodd_dev:
    print("\n  !! PREDICTION VIOLATED -- the fold cannot change these games:")
    for d in oddodd_dev: print(f"     {d[0]:<18} side {d[1]}  control {d[2]}  candidate {d[3]}")
else:
    print("\n  prediction HOLDS: every odd x odd cell is identical.")
if even_dev:
    print(f"\n  deviating even-dimension cells ({len(even_dev)}):")
    for d in even_dev: print(f"     {d[0]:<18} side {d[1]}  control {d[2]}  candidate {d[3]}")
    rate = 100.0 * len(even_dev) / even_n if even_n else 0
    print(f"\n  engagement rate on eligible cells: {len(even_dev)}/{even_n} = {rate:.1f}%")
    print("  (a rate near 0 means the mechanism barely executes; doctrine 5 step 0)")

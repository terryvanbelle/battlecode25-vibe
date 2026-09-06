#!/usr/bin/env python3
"""Diff two gauntlet runs game-by-game (opponent, map, side) and report the
shape of the flips: one-directional/concentrated = causal; scattered/mixed =
churn. Usage: diff-runs.py gauntlet/RUN_A gauntlet/RUN_B  (A = older/baseline)."""
import csv, sys, collections

def load(run):
    games = {}
    with open(f"{run}/results.csv") as f:
        for row in csv.DictReader(f):
            games[(row["opponent"], row["map"], row["bot_side"])] = row["bot_result"]
    return games

a, b = load(sys.argv[1]), load(sys.argv[2])
keys = sorted(set(a) & set(b))
flips = [(k, a[k], b[k]) for k in keys if a[k] != b[k]]
won, lost = [], []
for k, ra, rb in flips:
    (won if rb == "win" else lost).append(k)
print(f"common games: {len(keys)}   flips: {len(flips)}  (+{len(won)} newly-won, -{len(lost)} newly-lost)")
bymap = collections.Counter()
for k in won: bymap[(k[1], "+")] += 1
for k in lost: bymap[(k[1], "-")] += 1
print("\nby map:")
for (m, d), n in sorted(bymap.items()):
    print(f"  {d} {m:24s} {n}")
print("\nnewly-lost detail:")
for k in lost: print("  -", *k)
print("newly-won detail:")
for k in won: print("  +", *k)

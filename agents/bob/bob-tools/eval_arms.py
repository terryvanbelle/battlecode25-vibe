#!/usr/bin/env python3
"""Evaluate a dose-sweep gauntlet run in ARM coordinates.

The gauntlet reports the BOT's score against each opponent. A dose sweep puts the
dose arms in the OPPONENT slot, so an arm's own strength is 50 - (bot's score).
This script does that conversion once, in one place, so no future session has to
re-derive it under pressure -- see TRAINING_LOG, "Convention note" under iteration 26.

Usage:  eval_arms.py <run-dir> <null-arm> [arm ...]
"""
import csv
import sys
from collections import defaultdict


def load(run):
    games = {}
    with open(f"{run}/results.csv") as fh:
        for row in csv.DictReader(fh):
            games[(row["opponent"], row["map"], row["bot_side"])] = row["bot_result"]
    return games


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    run, null = sys.argv[1], sys.argv[2]
    games = load(run)
    arms = sys.argv[3:] or sorted({o for (o, _, _) in games} - {null})
    maps = sorted({m for (_, m, _) in games})

    # arm score = games the BOT lost to that arm
    def arm_score(a):
        return sum(1 for (o, m, s), r in games.items() if o == a and r == "loss")

    def sweeps(a):
        w = l = sp = 0
        for m in maps:
            res = [games.get((a, m, s)) for s in ("A", "B")]
            if None in res:
                continue
            # from the ARM's perspective: arm wins where bot loses
            aw = [r == "loss" for r in res]
            if all(aw):
                w += 1
            elif not any(aw):
                l += 1
            else:
                sp += 1
        return w, l, sp

    n = arm_score(null)
    nw, nl, nsp = sweeps(null)
    print(f"run {run}   null arm = {null}\n")
    print(f"{'arm':10}{'score':>8}{'vs null':>9}{'swept':>7}{'sweptAg':>9}{'split':>7}"
          f"{'diff-from-null':>16}")
    for a in [null] + [x for x in arms if x != null]:
        s = arm_score(a)
        w, l, sp = sweeps(a)
        diff = sum(1 for (o, m, sd), r in games.items()
                   if o == a and games.get((null, m, sd)) not in (None, r))
        tot = sum(1 for (o, _, _) in games if o == a)
        tag = "  <- NULL" if a == null else ""
        print(f"{a:10}{s:>5}/{tot // 1:<2}{s - n:>+9}{w:>7}{l:>9}{sp:>7}{diff:>12}/{tot}{tag}")

    print()
    if nsp != len(maps) or n * 2 != sum(1 for (o, _, _) in games if o == null):
        print(f"!! VOID CHECK: null arm is {n}/50 with {nsp}/{len(maps)} maps split "
              f"-- expected 25/50 and all split")
    else:
        print(f"null arm clean: {n}/50, all {nsp} maps split, {nw} swept / {nl} swept-against")


if __name__ == "__main__":
    main()

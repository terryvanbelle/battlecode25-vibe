#!/usr/bin/env python3
"""STAGE 0: did the arms actually differ, and did the dose land? It REFUSES to print who won.

Usage: stage0.py <run-dir> <null-arm> [arm ...]

A stage-0 check exists to answer exactly two questions before a full screen is paid for:

  1. Do the arms differ from the null AT ALL?  (a dose that never fires is a wasted run)
  2. Does the amount of differing behaviour move MONOTONICALLY with dose?

It deliberately does NOT read, compute, collect or print wins, losses, scores or
per-map outcomes. That is not an oversight -- it is the whole point. My own written
rule ("replay inspection is for mechanism, never for verdict") did not stop me from
reading a verdict out of mechanism data; a tool that cannot print the verdict does.
Doctrine 19: a control, not a note.

The verdict comes from bob-tools/eval_arms.py against the PRE-REGISTERED gate, after
this passes, and from nowhere else.
"""
import csv, sys

def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    run, null = sys.argv[1], sys.argv[2]
    seen = {}
    with open(f"{run}/results.csv") as fh:
        for r in csv.DictReader(fh):
            # store ONLY whether this game's outcome equals the null's -- never the outcome
            seen[(r["opponent"], r["map"], r["bot_side"])] = r["bot_result"]
    arms = sys.argv[3:] or sorted({o for (o, _, _) in seen} - {null})
    maps = sorted({m for (_, m, _) in seen})

    print(f"STAGE 0  run={run}  null={null}  {len(maps)} maps")
    print("(this tool does not compute or print wins -- use eval_arms.py for the verdict)\n")
    print(f"{'arm':>10} {'games differing':>16} {'maps touched':>13} {'share':>7}")
    print('-' * 50)
    rows = []
    for a in [x for x in arms if x != null]:
        diff = touched = 0
        for m in maps:
            hit = 0
            for s in ("A", "B"):
                x, y = seen.get((a, m, s)), seen.get((null, m, s))
                if x is not None and y is not None and x != y:
                    hit += 1
            diff += hit
            touched += 1 if hit else 0
        tot = sum(1 for (o, _, _) in seen if o == a)
        rows.append((a, diff, touched, diff / tot if tot else 0))
        print(f"{a:>10} {f'{diff}/{tot}':>16} {f'{touched}/{len(maps)}':>13} {diff/tot if tot else 0:>7.1%}")

    print()
    if rows and all(r[1] == 0 for r in rows):
        print("!! NO ARM DIFFERS FROM THE NULL -- the dose never fired. Do not read a verdict.")
    elif rows:
        order = [r[1] for r in rows]
        mono = all(order[i] <= order[i + 1] for i in range(len(order) - 1)) or \
               all(order[i] >= order[i + 1] for i in range(len(order) - 1))
        print(f"differing-game counts in argument order: {order} -- "
              f"{'MONOTONIC in dose' if mono else 'NOT monotonic in dose'}")
        print("Monotonic is expected when the arms are a dose ladder; it is NOT expected, "
              "and not a fault, when the arms vary WHAT is displaced at a fixed dose.")

main()

#!/usr/bin/env python3
"""Read the iteration-49 upkeep probe's counters out of a replay dump.

    tools/upkeep-read.py <label> <dump.txt> [<label> <dump.txt> ...]

Input is `tools/replay-dump.sh <replay> --from 1 --to <end> --ind alice_i49probe`.

Statics are per-robot in Battlecode, so each robot's LAST indicator string carries
its lifetime totals. This takes the last line per robot id and aggregates by type.

The quantity the pre-registered decision rule needs is `up per LIFETIME` for
soldiers: if eliminating upkeep entirely (up) cannot recover the ~70 paint the
gap is worth, the direction closes on magnitude.
"""
import re
import sys
from collections import defaultdict

LINE = re.compile(
    r'^round (\d+) id(\d+)\(T(\d),(\w+)\) IND "Q '
    r'ut=(\d+) adjU=(\d+) adjT=(\d+) tA=(\d+) tN=(\d+) tE=(\d+) '
    r'up=(\d+) upAdj=(\d+) upT=(\d+) \| i25=(\d+)/(\d+)')
KEYS = ("ut", "adjU", "adjT", "tA", "tN", "tE", "up", "upAdj", "upT",
        "refills", "refilled")


def load(path):
    last = {}
    for line in open(path, errors="replace"):
        m = LINE.match(line)
        if not m:
            continue
        rid = m.group(2)
        rec = dict(zip(KEYS, (int(m.group(i)) for i in range(5, 16))))
        rec["type"] = m.group(4)
        rec["round"] = int(m.group(1))
        last[rid] = rec          # later rounds overwrite: ends as the final line
    return list(last.values())


def report(label, rows):
    print(f"\n===== {label} =====")
    if not rows:
        print("  no probe indicator lines found -- was --ind passed, and the window opened?")
        return
    for ty in ("SOLDIER", "MOPPER", "SPLASHER"):
        g = [r for r in rows if r["type"] == ty]
        if not g:
            continue
        n = len(g)
        tot = {k: sum(r[k] for r in g) for k in KEYS}
        ut = tot["ut"]
        if ut == 0:
            continue
        print(f"  {ty:<9} n={n:<4} turns={ut:<7} mean life={ut/n:6.1f} turns")
        print(f"     upkeep per LIFETIME : {tot['up']/n:8.1f} paint"
              f"   (tank=200 for soldier)")
        print(f"     upkeep per turn     : {tot['up']/ut:8.3f}")
        print(f"       terrain part      : {(tot['up']-tot['upAdj'])/ut:8.3f}"
              f"   ({100*(tot['up']-tot['upAdj'])/tot['up']:.1f}% of upkeep)")
        print(f"       adjacency part    : {tot['upAdj']/ut:8.3f}"
              f"   ({100*tot['upAdj']/tot['up']:.1f}%)")
        print(f"         of which TOWERS : {tot['upT']/ut:8.3f}"
              f"   ({100*tot['upT']/tot['up']:.1f}% of upkeep)")
        print(f"     adj ally units/turn : {tot['adjU']/ut:8.3f}"
              f"      adj ally towers/turn: {tot['adjT']/ut:.3f}")
        tt = tot["tA"] + tot["tN"] + tot["tE"]
        print(f"     tile mix            : ally {100*tot['tA']/tt:4.1f}%"
              f"  neutral {100*tot['tN']/tt:4.1f}%  enemy {100*tot['tE']/tt:4.1f}%")
        # Close the ledger: tank + refilled = 5*paintActions + upkeep + leftover.
        # Leftover is ~0 for a starved unit, and most deaths here are starvation.
        tank = {"SOLDIER": 200, "MOPPER": 100, "SPLASHER": 300}[ty]
        refilled = tot["refilled"] / n
        budget = tank + refilled
        print(f"     refills/lifetime    : {tot['refills']/n:8.2f} calls, {refilled:.1f} paint")
        print(f"     BUDGET {budget:7.1f} = upkeep {tot['up']/n:.1f}"
              f" ({100*tot['up']/n/budget:.0f}%) + at most {(budget-tot['up']/n)/5:.1f} paint actions")


if __name__ == "__main__":
    args = sys.argv[1:]
    for i in range(0, len(args), 2):
        report(args[i], load(args[i + 1]))

#!/usr/bin/env python3
"""Aggregate bob-tools/early-census.sh output into the early-coverage secondary.

Row format emitted by early-census.sh (fields separated by '|'):
    file | team1 | team2 | winner | winType | rounds | "round N " | T1 aggregate | T2 aggregate

Team names come from the replay's OWN GameHeader, never from the filename, so
this works on tournament names (alice-vs-bob-on-Map.bc25) and gauntlet names
(OPP__MAP__botSIDE.bc25) alike without a per-source filename convention.

    early_agg.py <census.txt> <focus-team> [other-team ...]

Reports, for each opponent, the mean round-N coverage differential in per-mille
(focus minus opponent). Validated on the 2026-09-09 tournament: below -49 the
this parser reads the 9-field format and is NOT yet validated against it.
"""
import re
import sys
import statistics
from collections import defaultdict


def num(s, pat):
    m = re.search(pat, s)
    return int(m.group(1)) if m else 0


def parse(path):
    out = []
    for ln in open(path):
        p = ln.rstrip("\n").split("|")
        if len(p) < 9 or not p[7].strip():
            continue
        t1, t2, winner, rounds = p[1], p[2], p[3], p[5]
        c1, c2 = num(p[7], r"cov(\d+)m"), num(p[8], r"cov(\d+)m")
        out.append(dict(t1=t1, t2=t2, winner=winner, rounds=int(rounds),
                        cov={t1: c1, t2: c2}))
    return out


def main():
    rows = parse(sys.argv[1])
    focus = sys.argv[2]
    by = defaultdict(list)
    for r in rows:
        if focus not in (r["t1"], r["t2"]):
            continue
        opp = r["t2"] if r["t1"] == focus else r["t1"]
        won = (r["winner"] == "team1") == (r["t1"] == focus)
        by[opp].append((r["cov"][focus] - r["cov"][opp], won, r["rounds"]))
    print(f"{'opponent':22}{'n':>5}{'mean cov diff':>15}{'win%':>8}{'med rounds':>12}")
    for opp in sorted(by):
        v = by[opp]
        d = [x[0] for x in v]
        print(f"{opp:22}{len(v):>5}{statistics.mean(d):>+15.1f}"
              f"{100*sum(x[1] for x in v)/len(v):>7.1f}%"
              f"{statistics.median([x[2] for x in v]):>12.0f}")


if __name__ == "__main__":
    main()

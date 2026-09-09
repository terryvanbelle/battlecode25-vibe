#!/usr/bin/env python3
"""When alice abandons a tower pattern, is the soldier DEAD or ALIVE and elsewhere?

    tools/abandon-why.py <round> <ruincoords.txt> <mix.tsv> <ptrace2.txt>

This decides which CLASS of fix is eligible, before any mechanism is chosen:

  DEAD        -> an ENDURANCE limit. No targeting or commitment rule can fix it;
                 only lifetime/refill can, and iteration 44 lost 58 swept there.
  ALIVE, LEFT -> a DECISION limit. Commitment / stickiness / relay-steering are
                 eligible.
  STALLED     -> alive but does nothing more before the census round (out of paint
                 or blocked). Named in advance so it is not folded into either camp.

For each ruin still unclaimed at <round>, every alice unit that painted inside its
5x5 is followed from its LAST paint near that ruin.
"""
import re
import sys
from collections import defaultdict

SPAWN = re.compile(r"^round (\d+) id\d+\([^)]*\) SPAWN id\d+\(T(\d),(\w+)_TOWER\) at \((\d+),(\d+)\)")
PAINT = re.compile(r"^round (\d+) id(\d+)\(T(\d),(\w+)\) PAINT \((\d+),(\d+)\)")
DIED = re.compile(r"^round (\d+) DIED id(\d+)\(T(\d),(\w+)\)")


def load_ruins(path):
    out = {}
    for line in open(path):
        p = line.split()
        if len(p) >= 3:
            out[p[0]] = [tuple(int(v) for v in c.split(",")) for c in p[3:]]
    return out


def load_towers(path, upto):
    out = defaultdict(dict)
    for line in open(path):
        p = line.rstrip("\n").split("\t")
        if len(p) < 4 or p[2] != "EV":
            continue
        m = SPAWN.match(p[3])
        if m and int(m.group(1)) <= upto:
            who = "alice" if ("T" + m.group(2)) == p[1] else "opp"
            out[(p[0], p[1])][(int(m.group(4)), int(m.group(5)))] = who
    return out


def main():
    upto = int(sys.argv[1])
    ruins = load_ruins(sys.argv[2])
    towers = load_towers(sys.argv[3], upto)

    games = {}
    cur = None
    for line in open(sys.argv[4], errors="replace"):
        line = line.rstrip("\n")
        if line.startswith("# GAME"):
            p = line.split()
            cur = (p[2], p[3])
            games[cur] = dict(paints=defaultdict(list), died={})
            continue
        if cur is None:
            continue
        m = PAINT.match(line)
        if m:
            rnd = int(m.group(1))
            if rnd <= upto and ("T" + m.group(3)) == cur[1]:
                games[cur]["paints"][m.group(2)].append(
                    (rnd, int(m.group(5)), int(m.group(6)), m.group(4)))
            continue
        m = DIED.match(line)
        if m:
            rnd = int(m.group(1))
            if rnd <= upto and ("T" + m.group(3)) == cur[1]:
                games[cur]["died"][m.group(2)] = rnd

    cls = defaultdict(int); left_with = []; shortfall = []
    by_type = defaultdict(lambda: defaultdict(int))
    ruins_seen = 0
    for key, g in games.items():
        mp = key[0]
        if mp not in ruins or key not in towers:
            continue
        tw = towers[key]
        for (rx, ry) in ruins[mp]:
            if tw.get((rx, ry)) is not None:
                continue                       # built by someone -> not abandoned
            ruins_seen += 1
            for rid, evs in g["paints"].items():
                near = [e for e in evs if abs(e[1] - rx) <= 2 and abs(e[2] - ry) <= 2]
                if not near:
                    continue
                last = max(e[0] for e in near)
                utype = near[0][3]
                later_far = [e for e in evs
                             if e[0] > last and not (abs(e[1] - rx) <= 2 and abs(e[2] - ry) <= 2)]
                d = g["died"].get(rid)
                if later_far:
                    k = "ALIVE, LEFT"
                elif d is not None and d >= last:
                    k = "DEAD"
                else:
                    k = "STALLED"
                cls[k] += 1
                by_type[utype][k] += 1
                # THE CEILING, measured not assumed: for a soldier that left ALIVE,
                # the paints it performed elsewhere afterwards are exactly what a
                # stickiness rule could have redirected into this pattern. If that
                # is smaller than the shortfall, no commitment rule can complete it
                # and the decision-class fix is dead on magnitude.
                if k == "ALIVE, LEFT":
                    left_with.append(len(later_far))
                    shortfall.append(28 - sum(1 for _ in near))

    tot = sum(cls.values())
    print(f"\nabandonments at ruins still unclaimed by round {upto}")
    print(f"  {ruins_seen} unclaimed-ruin observations, {tot} unit-abandonment events\n")
    for k in ("DEAD", "ALIVE, LEFT", "STALLED"):
        print(f"  {k:<12}{cls[k]:>7}   {100*cls[k]/tot:>5.1f}%" if tot else k)
    print("\n  by unit type:")
    for t, d in sorted(by_type.items(), key=lambda kv: -sum(kv[1].values())):
        n = sum(d.values())
        parts = "  ".join(f"{k} {100*v/n:.0f}%" for k, v in sorted(d.items()))
        print(f"    {t:<10} n={n:<6} {parts}")
    if tot:
        print("\n  PRE-REGISTERED RULE: DEAD>=60% -> endurance limit (targeting rules INELIGIBLE);"
              "\n                       ALIVE,LEFT>=60% -> decision limit (commitment rules eligible)")
        d, a = 100*cls["DEAD"]/tot, 100*cls["ALIVE, LEFT"]/tot
        v = ("ENDURANCE limit" if d >= 60 else
             "DECISION limit" if a >= 60 else "MIXED -- no mechanism chosen on this")
        print(f"  -> {v}")
    if left_with:
        lw = sorted(left_with); n = len(lw)
        print(f"\n  CEILING of a stickiness rule, measured: for the {n} ALIVE-LEFT soldiers,")
        print(f"    paints they performed ELSEWHERE after leaving: mean {sum(lw)/n:.1f}, median {lw[n//2]}")
        print(f"    (that is exactly what a commitment rule could have redirected here)")
        per_ruin = defaultdict(int)
        enough = sum(1 for x, sf in zip(left_with, shortfall) if x >= sf)
        print(f"    cases where that alone covers the ruin's shortfall to 28: {enough}/{n}"
              f" = {100*enough/n:.1f}%")


if __name__ == "__main__":
    main()

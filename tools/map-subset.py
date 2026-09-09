#!/usr/bin/env python3
"""Pooled-vs-pair decomposition of tournament results on a subset of maps.

    tools/map-subset.py --grep 'Ruins?'            # maps matching a regex
    tools/map-subset.py --maps Barcode,Piglets2    # an explicit list
    tools/map-subset.py --maps-file mymaps.txt     # one map per line
    tools/map-subset.py --grep X --last 3          # pool the last 3 tournaments

This exists because of TRAINING_ALGORITHM.md doctrine 20: a POOLED win rate on a
map subset is a statement about a three-body system. It moves when either
opponent is unusually strong or weak on those maps, so on its own it cannot tell
"I am bad at this" from "one of them is good at this" -- and a lineage has
already read a 25.0%-vs-49.9% pooled rate (z = 4.15) as a private defect when the
pair decomposition showed one pair dead flat and the whole effect sitting in the
two pairs involving the third lineage.

So this tool never prints a pooled rate without the three pair rates beside it.
Every rate is also shown against its COMPLEMENT (the same lineages on the maps
outside the subset), because a subset rate with no complement is not a
comparison; z is the two-proportion test between subset and complement.

Pooling runs: games from two tournaments are byte-identical for any matchup whose
BOTH commits are unchanged (the engine is deterministic), so pooling them
inflates n without adding information. Repeated pairs are detected and excluded
from the later run, and the exclusion is reported.
"""
import argparse
import csv
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TDIR = REPO / "tournaments"
RUN_ID = re.compile(r"^\d{8}-\d{4}$")


def runs():
    return sorted(p for p in TDIR.iterdir()
                  if p.is_dir() and RUN_ID.match(p.name) and (p / "results.csv").is_file())


def commits(run):
    f = run / "bots.txt"
    if not f.is_file():
        return {}
    out = {}
    for line in f.read_text().splitlines():
        parts = line.split()
        if len(parts) >= 2:
            out[parts[0]] = parts[1]
    return out


def rows_of(run):
    rs = list(csv.DictReader((run / "results.csv").open()))
    return [r for r in rs if r.get("winner_bot") and r["winner_bot"] != "unknown"]


def two_prop_z(w1, n1, w2, n2):
    """Subset vs complement, pooled-proportion two-sample z. None if degenerate."""
    if n1 == 0 or n2 == 0:
        return None
    p = (w1 + w2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0:
        return None
    return (w1 / n1 - w2 / n2) / se


def fmt(w, n, z=None):
    if n == 0:
        return "     -  (0)"
    s = f"{100*w/n:5.1f}% ({w}/{n})"
    return s if z is None else s + f"  z={z:+5.2f}"


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--grep", help="regex matched against the map name")
    g.add_argument("--maps", help="comma-separated map names")
    g.add_argument("--maps-file", help="file with one map name per line")
    ap.add_argument("--runs", help="comma-separated run ids (default: the latest)")
    ap.add_argument("--last", type=int, help="pool the last N runs")
    a = ap.parse_args()

    allruns = runs()
    if not allruns:
        sys.exit(f"no tournament runs under {TDIR}")
    if a.runs:
        want = set(a.runs.split(","))
        use = [r for r in allruns if r.name in want]
        missing = want - {r.name for r in use}
        if missing:
            sys.exit("no such run(s): " + ", ".join(sorted(missing)))
    elif a.last:
        use = allruns[-a.last:]
    else:
        use = allruns[-1:]

    # Pool, dropping matchups already played byte-identically in an earlier run.
    seen = {}          # (bot_x, bot_y) -> (commit_x, commit_y) already counted
    rows, dropped = [], []
    for run in use:
        c = commits(run)
        for r in rows_of(run):
            pair = tuple(sorted((r["team_a"], r["team_b"])))
            key = (c.get(pair[0]), c.get(pair[1]))
            if None in key:
                rows.append(r)          # no bots.txt: cannot dedup, keep it
                continue
            if seen.get(pair) == key:
                dropped.append((run.name, pair))
                continue
            rows.append(r)
        for r in rows_of(run):
            pair = tuple(sorted((r["team_a"], r["team_b"])))
            key = (c.get(pair[0]), c.get(pair[1]))
            if None not in key:
                seen[pair] = key

    if a.grep:
        rx = re.compile(a.grep)
        inset = lambda m: bool(rx.search(m))
    else:
        names = (Path(a.maps_file).read_text().split() if a.maps_file
                 else a.maps.split(","))
        names = {n.strip() for n in names if n.strip()}
        inset = lambda m: m in names

    played_maps = sorted({r["map"] for r in rows})
    sub = [m for m in played_maps if inset(m)]
    if not sub:
        sys.exit("subset selects none of the %d maps played in %s"
                 % (len(played_maps), ", ".join(r.name for r in use)))

    bots = sorted({r["team_a"] for r in rows} | {r["team_b"] for r in rows})
    # w[in_subset][bot], n[in_subset][bot]; pw/pn keyed (winner, loser-side bot)
    w = [defaultdict(int), defaultdict(int)]
    n = [defaultdict(int), defaultdict(int)]
    pw = [defaultdict(int), defaultdict(int)]
    pn = [defaultdict(int), defaultdict(int)]
    for r in rows:
        i = 1 if inset(r["map"]) else 0
        x, y, win = r["team_a"], r["team_b"], r["winner_bot"]
        n[i][x] += 1
        n[i][y] += 1
        w[i][win] += 1
        pair = tuple(sorted((x, y)))
        pn[i][pair] += 1
        pw[i][(pair, win)] += 1

    print(f"runs      : {', '.join(r.name for r in use)}")
    print(f"subset    : {len(sub)} of {len(played_maps)} maps played")
    print(f"            {' '.join(sub)}")
    if dropped:
        byrun = defaultdict(set)
        for rn, pair in dropped:
            byrun[rn].add("–".join(pair))
        print("!! excluded as byte-identical repeats of an earlier run in this pool:")
        for rn in sorted(byrun):
            print(f"     {rn}: {', '.join(sorted(byrun[rn]))}")
    small = [str(x) for x in (sum(n[1].values()) // 2, sum(n[0].values()) // 2)]
    print(f"games     : {small[0]} in subset, {small[1]} in complement")
    print()

    print("POOLED  (mixes both opponents -- not a property of one lineage)")
    print(f"  {'bot':6} {'subset':>22}   {'complement':>18}   delta")
    for b in bots:
        z = two_prop_z(w[1][b], n[1][b], w[0][b], n[0][b])
        d = (100*w[1][b]/n[1][b] - 100*w[0][b]/n[0][b]) if n[1][b] and n[0][b] else 0
        print(f"  {b:6} {fmt(w[1][b], n[1][b], z):>22}   {fmt(w[0][b], n[0][b]):>18}   {d:+6.1f}")
    print()

    print("PAIRS  (this is the evidence; a FLAT pair means the deficit is SHARED)")
    print(f"  {'matchup':16} {'subset':>22}   {'complement':>18}   delta")
    flat, moved = [], []
    for i, x in enumerate(bots):
        for y in bots[i+1:]:
            pair = (x, y)
            sw, sn = pw[1][(pair, x)], pn[1][pair]
            cw, cn = pw[0][(pair, x)], pn[0][pair]
            z = two_prop_z(sw, sn, cw, cn)
            d = (100*sw/sn - 100*cw/cn) if sn and cn else 0
            print(f"  {x+' vs '+y:16} {fmt(sw, sn, z):>22}   {fmt(cw, cn):>18}   {d:+6.1f}")
            (moved if z is not None and abs(z) >= 2 else flat).append((x, y, d, z))
    print()

    if moved and flat:
        involved = defaultdict(int)
        for x, y, *_ in moved:
            involved[x] += 1
            involved[y] += 1
        common = [b for b in bots if involved[b] == len(moved) and
                  all(b not in (x, y) for x, y, *_ in flat)]
        if common:
            c = common[0]
            fx, fy, _, fz = flat[0]
            # WHICH WAY the moved pairs go decides the whole conclusion, and it
            # is not implied by the pattern of movement. An earlier version of
            # this tool printed the "the other two lack it" reading
            # unconditionally, selecting the branch purely from which pairs
            # moved -- so on a subset where the common lineage LOSES it told
            # that lineage its rivals were the deficient ones, and it read
            # correctly on the mirror subset, which is what made it dangerous.
            # A lineage caught it by running both subsets. Orient every moved
            # pair's delta toward the common lineage and let the sign speak.
            dcs = [d if x == c else -d for x, y, d, _ in moved]
            dc = sum(dcs) / len(dcs)
            print(f"READ: every pair that moved involves {c}, and {fx}–{fy} is flat.")
            print("      Two builds carrying the same deficit cancel (doctrine 17), so the")
            print("      flat pair is the CONTROL for whatever this subset is measuring.")
            if dc > 0:
                print(f"      {c} GAINS on the subset ({dc:+.1f} pts averaged over both moved")
                print(f"      pairs), so the reading is: {fx} and {fy} both lack a capability")
                print(f"      {c} has. It is shared, so no self-play instrument of either can")
                print("      see it.")
            else:
                print(f"      {c} LOSES on the subset ({dc:+.1f} pts averaged over both moved")
                print(f"      pairs), so the reading is: {c} lacks a capability {fx} and {fy}")
                print(f"      both have -- a defect private to {c}, and one its own gauntlet")
                print(f"      cannot see either, since every arm in it is {c}.")
            print("      Derive the capability from the maps and the engine: isolation means")
            print("      you cannot look at who has it.")
            if fz is not None and abs(fz) >= 1.5:
                print(f"      !! the flat pair is only marginally flat (z={fz:+.2f}). Treat the")
                print("         control as weak and say so rather than leaning on it.")
    elif moved:
        print("READ: no flat pair, so nothing here separates a shared deficit from a")
        print("      private one. Widen the pool or cut the subset differently.")
    else:
        print("READ: no pair moved by |z| >= 2. The subset is not distinguishing anything.")


if __name__ == "__main__":
    main()

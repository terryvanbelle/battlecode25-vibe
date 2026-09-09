#!/usr/bin/env python3
"""WHY do ruins go unclaimed? The discriminator between three hypotheses.

    tools/ruin-why.py <round> <ruincoords.txt> <mix.tsv> <ptrace.txt>

For every ruin on every map, up to <round>, classify it as built by alice, built
by the opponent, or UNCLAIMED -- then count alice's PAINT actions inside the 5x5
tower pattern centred on it.

  unclaimed with ~0 alice paints nearby  -> alice never worked there.
                                            A DISCOVERY / DISTANCE limit, which is
                                            what symmetry inference or ruin memory
                                            would serve.
  unclaimed with MANY alice paints nearby -> alice started the pattern and did not
                                            finish it. A PATTERN-COMPLETION limit,
                                            which those tools would NOT fix.

The comparison that makes it readable is the third column: how many paints alice
spends on the ruins it DOES complete. An unclaimed ruin sitting at a similar count
is an abandoned build; one at zero was never visited.
"""
import re
import sys
from collections import defaultdict

SPAWN = re.compile(r"^round (\d+) id\d+\([^)]*\) SPAWN id\d+\(T(\d),(\w+)_TOWER\) at \((\d+),(\d+)\)")
PAINT = re.compile(r"^round (\d+) id(\d+)\(T(\d),(\w+)\) PAINT \((\d+),(\d+)\)")


def load_ruins(path):
    out = {}
    for line in open(path):
        p = line.split()
        if len(p) < 3:
            continue
        out[p[0]] = [tuple(int(v) for v in c.split(",")) for c in p[3:]]
    return out


def load_towers(path, upto):
    """(map, side) -> {(x,y): 'alice'|'opp'} for towers BUILT by round `upto`."""
    out = defaultdict(dict)
    for line in open(path):
        p = line.rstrip("\n").split("\t")
        if len(p) < 4 or p[2] != "EV":
            continue
        m = SPAWN.match(p[3])
        if not m:
            continue
        rnd = int(m.group(1))
        if rnd > upto:
            continue
        who = "alice" if ("T" + m.group(2)) == p[1] else "opp"
        out[(p[0], p[1])][(int(m.group(4)), int(m.group(5)))] = who
    return out


def load_paints(path, upto):
    """(map, side) -> {(x,y): count} of ALICE paint actions by round `upto`."""
    out = defaultdict(lambda: defaultdict(int))
    who = defaultdict(lambda: defaultdict(set))   # tile -> set of painter robot ids
    cur = None
    for line in open(path, errors="replace"):
        line = line.rstrip("\n")
        if line.startswith("# GAME"):
            p = line.split()
            cur = (p[2], p[3])
            continue
        if cur is None:
            continue
        m = PAINT.match(line)
        if not m or int(m.group(1)) > upto:
            continue
        if ("T" + m.group(3)) != cur[1]:
            continue
        loc = (int(m.group(5)), int(m.group(6)))
        out[cur][loc] += 1
        who[cur][loc].add(m.group(2))
    return out, who


def main():
    upto = int(sys.argv[1])
    ruins = load_ruins(sys.argv[2])
    towers = load_towers(sys.argv[3], upto)
    paints, painters = load_paints(sys.argv[4], upto)

    buckets = defaultdict(list); nsold = defaultdict(list)
    games = 0
    for key, tw in towers.items():
        mp = key[0]
        if mp not in ruins or key not in paints:
            continue
        games += 1
        pp = paints[key]; ww = painters[key]
        for (rx, ry) in ruins[mp]:
            near = sum(pp.get((rx + dx, ry + dy), 0)
                       for dx in range(-2, 3) for dy in range(-2, 3)
                       if not (dx == 0 and dy == 0))
            ids = set()
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    if dx or dy:
                        ids |= ww.get((rx + dx, ry + dy), set())
            owner = tw.get((rx, ry))
            k = ("alice-built" if owner == "alice"
                 else "opp-built" if owner == "opp" else "UNCLAIMED")
            buckets[k].append(near)
            nsold[k].append(len(ids))

    print(f"\nruins classified by round {upto}, over {games} games\n")
    print(f"{'class':<14}{'n':>6}{'mean alice paints in the 5x5':>32}{'median':>9}")
    for k in ("alice-built", "opp-built", "UNCLAIMED"):
        v = buckets[k]
        if not v:
            continue
        v_s = sorted(v)
        ns = nsold[k]
        print(f"{k:<14}{len(v):>6}{sum(v)/len(v):>32.1f}{v_s[len(v_s)//2]:>9}"
              f"   distinct alice painters: mean {sum(ns)/len(ns):.2f}")

    u = buckets["UNCLAIMED"]
    if not u:
        return
    n = len(u)
    print(f"\nUNCLAIMED ruins ({n}) by how much alice painted around them:")
    for lo, hi, lab in ((0, 0, "ZERO -- never worked"), (1, 4, "1-4  -- passed through"),
                        (5, 14, "5-14 -- started"), (15, 10**9, "15+  -- heavily worked")):
        c = sum(1 for x in u if lo <= x <= hi)
        print(f"   {lab:<26}{c:>6}   {100*c/n:>5.1f}%")
    ab = buckets["alice-built"]
    if ab:
        thresh = sorted(ab)[len(ab) // 2]
        started = sum(1 for x in u if x >= thresh)
        print(f"\n   alice's MEDIAN paint cost for a ruin it completed: {thresh}")
        print(f"   unclaimed ruins already at or above that cost: {started}/{n}"
              f" = {100*started/n:.1f}%  <- abandoned builds, not undiscovered ground")


if __name__ == "__main__":
    main()

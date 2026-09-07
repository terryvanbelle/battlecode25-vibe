#!/usr/bin/env python3
"""Split a gauntlet run's per-map result by the map's RUIN DENSITY.

Why this exists: several quantities in this lineage are ruin-related, and the
official corpus is very uneven -- 4.6 to 21.9 ruins per 1000 tiles, a 4.8x
spread (tools/mapdata/README.md). A 25-map random sample averages over that,
so a mechanism whose live window depends on ruin supply can show a modest
headline while being large on half the corpus and absent on the other half.

Reads ruin counts from the SHARED tools/mapdata/ruin_parity.txt -- never a
private copy -- and the run's own results, and reports each half with a
bootstrap over maps (the map is the unit of uncertainty in a deterministic
game; see LEARNINGS "in a deterministic game, the MAP is the unit").

  tools/density-split.py gauntlet/<run-id> [opponent ...]
"""
import csv, sys, os, re, collections, random, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
SHARED = os.path.join(HERE, "..", "..", "..", "tools", "mapdata", "ruin_parity.txt")
MEDIAN = 11.4          # corpus median ruins per 1000 tiles, from mapdata/README.md


def densities():
    d = {}
    for line in open(SHARED):
        m = re.match(r"^(\S+)\s+(\d+)x(\d+)\s+ruins=\s*(\d+)", line)
        if m:
            n, w, h, r = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
            d[n] = 1000.0 * r / (w * h)
    return d


def load(run):
    """Wins of the run's BOT, per (opponent, map), out of 2 (both sides).

    ORIENTATION, stated because getting it backwards silently inverts every
    number: this counts the BOT named in bot.txt -- the thing the run is
    testing. tools/map-resample.py counts the OPPONENT, because it was written
    for ablation runs where the BOT is the baseline and each opponent is a
    candidate. Both are right for their run shape and they disagree by
    construction; check bot.txt before comparing the two.
    """
    per = collections.defaultdict(lambda: collections.defaultdict(int))
    csvp = os.path.join(run, "results.csv")
    if os.path.exists(csvp):
        for r in csv.DictReader(open(csvp)):
            per[r["opponent"]][r["map"]] += (1 if r["bot_result"] == "win" else 0)
    else:
        for line in open(os.path.join(run, "results.txt")):
            f = line.split()
            if len(f) >= 6 and f[0] == "RESULT":
                per[f[1]][f[2]] += (1 if f[3] == f[4] else 0)
    return per


def boot(wins, maps, iters=20000, seed=7):
    n = len(maps)
    if n == 0:
        return 0.0, 0.0, 0, 0
    score = lambda s: sum(wins[m] for m in s) * n / len(s)
    pt = score(maps)
    random.seed(seed)
    b = sorted(score([random.choice(maps) for _ in range(n)]) for _ in range(iters))
    return pt, statistics.pstdev(b), b[int(.025 * len(b))], b[int(.975 * len(b))]


if __name__ == "__main__":
    run = sys.argv[1]
    want = sys.argv[2:]
    dens, per = densities(), load(run)
    botf = os.path.join(run, "bot.txt")
    bot = "?"
    if os.path.exists(botf):
        for l in open(botf):
            if l.startswith("bot="):
                bot = l.strip().split("=", 1)[1]
    print(f"{run}  scores are BOT={bot}'s wins.  Split at the corpus median {MEDIAN} ruins/1000 tiles")
    for opp in sorted(per):
        if want and opp not in want:
            continue
        maps = [m for m in per[opp] if m in dens]
        miss = [m for m in per[opp] if m not in dens]
        lo = sorted(m for m in maps if dens[m] < MEDIAN)
        hi = sorted(m for m in maps if dens[m] >= MEDIAN)
        print(f"\n{opp}   ({len(maps)} maps priced" + (f", {len(miss)} unpriced: {' '.join(miss)}" if miss else "") + ")")
        for label, sub in (("SPARSE ruins (long live window)", lo),
                           ("DENSE  ruins (short live window)", hi)):
            if not sub:
                print(f"  {label:34} -- no maps")
                continue
            pt, se, l, h = boot(per[opp], sub)
            n = len(sub)
            print(f"  {label:34} {pt:5.1f}/{2*n:<3} ({100*pt/(2*n):5.1f}%)  "
                  f"se={se:4.2f}  95% CI [{l:.0f}, {h:.0f}]  null={n}  "
                  f"mean density={statistics.mean(dens[m] for m in sub):4.1f}")

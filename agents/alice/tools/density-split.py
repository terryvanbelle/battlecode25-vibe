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

# WARNING, paid for on 2026-09-07: the median SPLIT below manufactured a
# "density gradient" for iteration 22 that does not survive full resolution
# (split said +6 sparse vs +2 dense; Spearman rho = -0.093, permutation
# p = 0.673). Dichotomising a continuous variable discards the ordering within
# each bin and lets the headline ride on which side of an arbitrary cut a few
# maps fell. THE RANK CORRELATION IS THE PRIMARY STATISTIC; the split is a
# descriptive companion. Both are printed so the two can never be quoted apart.


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


def _rank(v):
    s = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(v):                       # average ties, or dense maps tie badly
        j = i
        while j + 1 < len(v) and v[s[j + 1]] == v[s[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            r[s[k]] = avg
        i = j + 1
    return r


def _sp(rx, ys):
    ry = _rank(ys)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** .5
    return num / den if den else 0.0


def spearman(xs, ys, iters=3000, seed=11):
    """rho plus a permutation p-value -- no distributional assumption, which
    matters because per-map wins take only the values 0, 1 and 2."""
    rx = _rank(xs)
    rho = _sp(rx, ys)
    random.seed(seed)
    z, cnt = list(ys), 0
    for _ in range(iters):
        random.shuffle(z)
        if abs(_sp(rx, z)) >= abs(rho) - 1e-12:
            cnt += 1
    return rho, cnt / iters


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
        if len(maps) >= 8:
            rho, pv = spearman([dens[m] for m in maps], [per[opp][m] for m in maps])
            verdict = "no trend" if pv > 0.10 else "TREND"
            print(f"  PRIMARY  Spearman rho vs density = {rho:+.3f}   permutation p = {pv:.3f}   -> {verdict}")
            print(f"  (negative rho = better on sparse-ruin maps. The split below is DESCRIPTIVE ONLY.)")
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

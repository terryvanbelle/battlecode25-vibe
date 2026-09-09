#!/usr/bin/env python3
"""Split a gauntlet run's per-map result along a MAP AXIS (density or size).

Was tools/density-split.py through iteration 43; density-split.py is now a shim
that calls this with --axis density, so commands recorded in TRAINING_LOG.md
still work. It was generalised at iteration 44 because the "sparse maps" finding
turned out to be a CONFOUND -- the axis that separates this lineage's results is
map SIZE, and density was riding on its correlation with area (TRAINING_LOG.md,
"The standing 'sparse maps' finding is a CONFOUND"). A tool that can only cut on
the confounded axis invites the cut to be redone by hand, and a hand cut is not
a fix.

Why this exists: several quantities in this lineage are ruin-related, and the
official corpus is very uneven -- 4.6 to 21.9 ruins per 1000 tiles, a 4.8x
spread (tools/mapdata/README.md). A 25-map random sample averages over that,
so a mechanism whose live window depends on ruin supply can show a modest
headline while being large on half the corpus and absent on the other half.

Reads ruin counts from the SHARED tools/mapdata/ruin_parity.txt -- never a
private copy -- and the run's own results, and reports each half with a
bootstrap over maps (the map is the unit of uncertainty in a deterministic
game; see LEARNINGS "in a deterministic game, the MAP is the unit").

  tools/map-axis-split.py [--axis size|density] gauntlet/<run-id> [opponent ...]
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


AXES = {
    # name: (value fn from (w, h, ruins), median, unit, low label, high label,
    #        what a NEGATIVE rho means)
    "density": (lambda w, h, r: 1000.0 * r / (w * h), 11.4, "ruins/1000 tiles",
                "SPARSE ruins (long live window)", "DENSE  ruins (short live window)",
                "negative rho = better on sparse-ruin maps"),
    "size":    (lambda w, h, r: float(w * h), None, "tiles of area",
                "SMALL maps (70% coverage race)", "LARGE maps (room to expand)",
                "negative rho = better on small maps"),
}


def axis_values(axis):
    """Per-map value of the chosen axis, read from the SHARED mapdata file.

    The median for `size` is computed from the corpus itself rather than
    hardcoded, because unlike the density median it is not published in
    mapdata/README.md and a hardcoded copy would go stale silently.
    """
    fn = AXES[axis][0]
    d = {}
    for line in open(SHARED):
        m = re.match(r"^(\S+)\s+(\d+)x(\d+)\s+ruins=\s*(\d+)", line)
        if m:
            n, w, h, r = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
            d[n] = fn(w, h, r)
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
    args = sys.argv[1:]
    axis = "density"
    if args and args[0] == "--axis":
        axis = args[1]
        args = args[2:]
    if axis not in AXES:
        sys.exit(f"unknown --axis {axis!r}; choose from {', '.join(AXES)}")
    _, med, unit, lolab, hilab, rho_note = AXES[axis]
    run = args[0]
    want = args[1:]
    vals, per = axis_values(axis), load(run)
    if med is None:                       # corpus median, computed not hardcoded
        med = statistics.median(vals.values())
    botf = os.path.join(run, "bot.txt")
    bot = "?"
    if os.path.exists(botf):
        for l in open(botf):
            if l.startswith("bot="):
                bot = l.strip().split("=", 1)[1]
    print(f"{run}  scores are BOT={bot}'s wins.  "
          f"axis={axis}, split at the corpus median {med:g} {unit}")
    for opp in sorted(per):
        if want and opp not in want:
            continue
        maps = [m for m in per[opp] if m in vals]
        miss = [m for m in per[opp] if m not in vals]
        # Sorted by NAME, not by axis value: boot() draws with random.choice
        # over this list, so re-ordering it changes the bootstrap realisation
        # (se moved 2.70 -> 2.73 when I sorted by value) and would silently
        # break reproduction of se figures already recorded in TRAINING_LOG.md.
        lo = sorted(m for m in maps if vals[m] < med)
        hi = sorted(m for m in maps if vals[m] >= med)
        print(f"\n{opp}   ({len(maps)} maps priced"
              + (f", {len(miss)} unpriced: {' '.join(miss)}" if miss else "") + ")")
        if len(maps) >= 8:
            rho, pv = spearman([vals[m] for m in maps], [per[opp][m] for m in maps])
            verdict = "no trend" if pv > 0.10 else "TREND"
            print(f"  PRIMARY  Spearman rho vs {axis} = {rho:+.3f}   "
                  f"permutation p = {pv:.3f}   -> {verdict}")
            print(f"  ({rho_note}. The split below is DESCRIPTIVE ONLY.)")
        for label, sub in ((lolab, lo), (hilab, hi)):
            if not sub:
                print(f"  {label:34} -- no maps")
                continue
            pt, se, l, h = boot(per[opp], sub)
            n = len(sub)
            print(f"  {label:34} {pt:5.1f}/{2*n:<3} ({100*pt/(2*n):5.1f}%)  "
                  f"se={se:4.2f}  95% CI [{l:.0f}, {h:.0f}]  null={n}  "
                  f"mean {axis}={statistics.mean(vals[m] for m in sub):6.1f}")

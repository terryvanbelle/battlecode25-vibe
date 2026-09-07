#!/usr/bin/env python3
"""Uncertainty for a gauntlet result, by resampling MAPS -- not binomially.

The engine and both builds are deterministic, so every (map, side) cell is a
fixed function of the two programs. Nothing is random per game. The only thing
that varies between one estimate and another is WHICH MAPS WERE DRAWN, so the
map is the unit of resampling and the binomial sd is the wrong model. In
practice binomial has overstated the spread here by ~2x, because deterministic
per-map outcomes are concentrated rather than coin-flip-like.

  tools/map-resample.py gauntlet/<run-id> [opponent ...]

Reports, per opponent, the candidate's score, a bootstrap and jackknife se over
maps, a 95% interval, and the distance from the 12/24 mirror null.
"""
import csv, sys, collections, random, statistics, os

def load(run):
    per = collections.defaultdict(lambda: collections.defaultdict(int))
    maps = set()
    for r in csv.DictReader(open(os.path.join(run, "results.csv"))):
        maps.add(r["map"])
        if r["bot_result"] != "win":          # baseline lost => candidate won
            per[r["opponent"]][r["map"]] += 1
    return per, sorted(maps)

def stats(wins, maps, iters=20000, seed=7):
    n = len(maps)
    score = lambda s: sum(wins[m] for m in s) * n / len(s)
    pt = score(maps)
    random.seed(seed)
    boot = sorted(score([random.choice(maps) for _ in range(n)]) for _ in range(iters))
    bse = statistics.pstdev(boot)
    jack = [score([x for x in maps if x != m]) for m in maps]
    jb = statistics.mean(jack)
    jse = ((n - 1) / n * sum((j - jb) ** 2 for j in jack)) ** 0.5
    return pt, bse, jse, boot[int(.025 * len(boot))], boot[int(.975 * len(boot))]

if __name__ == "__main__":
    run = sys.argv[1]
    per, maps = load(run)
    want = sys.argv[2:] or sorted(per)
    null = len(maps)          # the mirror null: every map splits 1-1
    print(f"{run}  maps={len(maps)}  mirror null = {null}/{2*len(maps)}\n")
    for opp in want:
        pt, bse, jse, lo, hi = stats(per[opp], maps)
        sd = f"{(pt-null)/bse:+.2f} sd" if bse else "exact null (se=0)"
        dist = dict(sorted(collections.Counter(per[opp][m] for m in maps).items()))
        print(f"{opp:18s} {pt:.0f}/{2*len(maps)}  boot_se={bse:.2f} jack_se={jse:.2f}"
              f"  95% CI [{lo:.0f}, {hi:.0f}]  {sd}")
        print(f"{'':18s} per-map candidate wins (0/1/2): {dist}")

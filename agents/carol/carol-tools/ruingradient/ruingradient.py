#!/usr/bin/env python3
"""Carol's win rate against the other two lineages, bucketed by the map's ruin count.

WHY THIS IS A FILE. Iteration 34 published a Spearman rho of +0.624 that was computed
ad hoc in session, never written down, and therefore never checkable; it turned out to
correspond to no computation over the data at all. Every covariate claim this lineage
makes now has to be re-runnable from committed inputs. Both inputs here are committed:

    tournaments/<run>/results.csv        one row per decided game
    tools/mapdata/ruin_parity.txt        CLAIMABLE ruins per map, from the .map25 files

NOTE ON THE RUIN COUNT. ruin_parity.txt counts CLAIMABLE ruins -- it excludes the four
tiles the starting towers sit on, so it is consistently 4 lower than a replay
MatchHeader's ruin count. The buckets below are in claimable ruins. Say which you used.

    python3 ruingradient.py [tournaments_dir] [mapdata_file]
"""
import csv, os, re, sys, math, collections

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
TDIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "tournaments")
MDAT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, "tools", "mapdata", "ruin_parity.txt")
ME = "carol"
EDGES = [11, 17, 23]                      # bucket upper bounds; last bucket is open
LABELS = ["ruins<=11", "ruins 12-17", "ruins 18-23", "ruins>=24"]


def load_maps(path):
    maps = {}
    for line in open(path):
        m = re.match(r"^(\S+)\s+(\d+)x(\d+)\s+ruins=\s*(\d+)", line)
        if m:
            maps[m.group(1)] = (int(m.group(2)) * int(m.group(3)), int(m.group(4)))
    return maps


def bucket(r):
    for i, e in enumerate(EDGES):
        if r <= e:
            return i
    return len(EDGES)


def trend_z(n, x):
    """Cochran-Armitage test for trend in proportions across ordered buckets.

    Scores are the bucket indices 0..k-1. Returns z; negative means the rate FALLS
    as the bucket index rises. This is the standard statistic, written out rather
    than pulled from a library so the arithmetic is visible and checkable.
    """
    N, X = sum(n), sum(x)
    if not N or X in (0, N):
        return float("nan")
    pbar = X / N
    s = list(range(len(n)))
    sbar = sum(s[i] * n[i] for i in range(len(n))) / N
    num = sum(s[i] * (x[i] - n[i] * pbar) for i in range(len(n)))
    den = pbar * (1 - pbar) * sum(n[i] * (s[i] - sbar) ** 2 for i in range(len(n)))
    return num / math.sqrt(den) if den > 0 else float("nan")


def main():
    maps = load_maps(MDAT)
    runs = sorted(d for d in os.listdir(TDIR) if re.match(r"^\d{8}-\d{4}$", d))
    pooled = [[0, 0] for _ in LABELS]
    per_opp = collections.defaultdict(lambda: [[0, 0] for _ in LABELS])
    skipped = set()

    print(f"maps with ruin data: {len(maps)}    tournament runs: {len(runs)}\n")
    for run in runs:
        f = os.path.join(TDIR, run, "results.csv")
        if not os.path.exists(f):
            continue
        b = [[0, 0] for _ in LABELS]
        for row in csv.DictReader(open(f)):
            a, t = row["team_a"], row["team_b"]
            if ME not in (a, t):
                continue
            if row["map"] not in maps:
                skipped.add(row["map"])
                continue
            opp = t if a == ME else a
            k = bucket(maps[row["map"]][1])
            won = int(row["winner_bot"] == ME)
            for tab in (b, pooled, per_opp[opp]):
                tab[k][0] += won
                tab[k][1] += 1
        cells = "  ".join(
            f"{LABELS[i]}:{b[i][0]}/{b[i][1]}={100*b[i][0]/b[i][1]:.0f}%"
            for i in range(len(LABELS)) if b[i][1]
        )
        print(f"{run}  {cells}")

    def report(title, tab):
        print(f"\n{title}")
        for i, lab in enumerate(LABELS):
            if tab[i][1]:
                print(f"   {lab:12s} {tab[i][0]:4d}/{tab[i][1]:4d} = {100*tab[i][0]/tab[i][1]:5.1f}%")
        z = trend_z([c[1] for c in tab], [c[0] for c in tab])
        print(f"   Cochran-Armitage trend z = {z:+.2f}   (negative = rate falls as ruins rise)")

    report(f"POOLED -- {ME} vs all other lineages", pooled)
    for opp in sorted(per_opp):
        report(f"{ME} vs {opp} only", per_opp[opp])
    if skipped:
        print(f"\nmaps in results.csv with no ruin data (EXCLUDED): {sorted(skipped)}")


if __name__ == "__main__":
    main()

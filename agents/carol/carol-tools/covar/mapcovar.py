#!/usr/bin/env python3
"""Join a gauntlet arm's per-map record against exogenous map facts (area, ruins).

Map facts come from tools/mapdata/ruin_parity.txt -- the shared neutral corpus file, read
from the engine jar's .map25 flatbuffers. Nothing here touches another agent's workspace.

  mapcovar.py <run-dir> <opponent>            # per-map join + Spearman rho
  mapcovar.py --corpus                        # collinearity of area vs ruins over all 75 maps

Spearman rho is computed on midranks with the tie-corrected t approximation, which is what a
25-map sample supports; it is NOT an exact permutation test and is quoted as such.
"""
import sys, os, csv, math, re

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
PARITY = os.path.join(REPO, "tools", "mapdata", "ruin_parity.txt")

def map_facts():
    facts = {}
    pat = re.compile(r"^(\S+)\s+(\d+)x(\d+)\s+ruins=\s*(\d+)")
    for line in open(PARITY):
        if line.startswith("#"):
            continue
        m = pat.match(line.strip())
        if m:
            name, w, h, r = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
            facts[name.lower()] = {"name": name, "w": w, "h": h, "area": w * h, "ruins": r}
    return facts

def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        mid = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            r[order[k]] = mid
        i = j + 1
    return r

def spearman(xs, ys):
    n = len(xs)
    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    if den == 0:
        return 0.0, 0.0, n - 2
    rho = num / den
    df = n - 2
    t = rho * math.sqrt(df / (1 - rho ** 2)) if abs(rho) < 1 else float("inf")
    return rho, t, df

def main():
    if sys.argv[1] == "--corpus":
        f = map_facts()
        a = [v["area"] for v in f.values()]
        r = [v["ruins"] for v in f.values()]
        rho, t, df = spearman(a, r)
        print(f"corpus n={len(a)} maps  rho(area, ruins) = {rho:+.3f}  t={t:.2f} df={df}")
        return
    run, opp = sys.argv[1], sys.argv[2]
    facts = map_facts()
    wins, games = {}, {}
    for row in csv.DictReader(open(os.path.join(run, "results.csv"))):
        if row["opponent"] != opp:
            continue
        m = row["map"].lower()
        games[m] = games.get(m, 0) + 1
        wins[m] = wins.get(m, 0) + (1 if row["bot_result"] == "win" else 0)
    miss = [m for m in games if m not in facts]
    if miss:
        print(f"NOT IN CORPUS (excluded): {miss}")
    maps = sorted(m for m in games if m in facts)
    print(f"{'map':<22}{'area':>7}{'ruins':>7}{'w-l':>8}")
    for m in maps:
        f = facts[m]
        print(f"{f['name']:<22}{f['area']:>7}{f['ruins']:>7}{str(wins[m])+'-'+str(games[m]-wins[m]):>8}")
    W = [wins[m] for m in maps]
    G = [games[m] for m in maps]
    print(f"\ntotal {sum(W)}/{sum(G)} ({100.0*sum(W)/sum(G):.1f}%) over {len(maps)} maps")
    for key in ("area", "ruins"):
        xs = [facts[m][key] for m in maps]
        rho, t, df = spearman(xs, W)
        print(f"  rho(wins, {key:<5}) = {rho:+.3f}   t={t:+.2f} df={df}")
        med = sorted(xs)[len(xs) // 2]
        lo = [(wins[m], games[m]) for m in maps if facts[m][key] < med]
        hi = [(wins[m], games[m]) for m in maps if facts[m][key] >= med]
        for lbl, half in (("low ", lo), ("high", hi)):
            if half:
                w, g = sum(x[0] for x in half), sum(x[1] for x in half)
                print(f"      {lbl} {key:<5} half: {len(half):>2} maps  {w}/{g}  {100.0*w/g:.1f}%")

main()

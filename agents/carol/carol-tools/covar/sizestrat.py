#!/usr/bin/env python3
"""Map-size stratification of a tournament record. Carol, iteration 35 session.

Why this exists: carol's gauntlet reports ONE aggregate win rate over a random 25-map sample.
A change that helps small maps a lot and hurts large maps a little passes that gate every time,
and the frozen roster cannot see it either because carol's own snapshots share the weakness --
the deficit cancels in every head-to-head carol runs. Only the tournament plays opponents this
lineage did not produce, so only the tournament can show it.

  sizestrat.py                       # every tournament, every bot, binned by map area
  sizestrat.py <run> <bot>           # per-map detail for one bot in one tournament

Map areas come from tools/mapdata/ruin_parity.txt (shared neutral corpus, read from the engine
jar). Tournament results are tournaments/<run>/results.csv -- the sanctioned cross-agent channel.
Nothing here reads another agent's workspace.
"""
import csv, re, os, sys, math, collections

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
BINS = [(0, 900, "tiny<=900"), (901, 1600, "small"), (1601, 2500, "large"), (2501, 10**9, "huge>2500")]

def areas():
    a = {}
    for line in open(os.path.join(REPO, "tools", "mapdata", "ruin_parity.txt")):
        if line.startswith("#"):
            continue
        m = re.match(r"^(\S+)\s+(\d+)x(\d+)\s+ruins=\s*(\d+)", line.strip())
        if m:
            a[m.group(1).lower()] = int(m.group(2)) * int(m.group(3))
    return a

def midrank(xs):
    o = sorted(range(len(xs)), key=lambda i: xs[i]); r = [0.0]*len(xs); i = 0
    while i < len(o):
        j = i
        while j+1 < len(o) and xs[o[j+1]] == xs[o[i]]: j += 1
        for k in range(i, j+1): r[o[k]] = (i+j)/2.0 + 1
        i = j + 1
    return r

def pear(a, b):
    n = len(a); ma = sum(a)/n; mb = sum(b)/n
    num = sum((x-ma)*(y-mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x-ma)**2 for x in a) * sum((y-mb)**2 for y in b))
    return num/den if den else 0.0

def record(rows, bot, A):
    per = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        if bot not in (r["team_a"], r["team_b"]):
            continue
        per[r["map"]][0] += (r["winner_bot"] == bot)
        per[r["map"]][1] += 1
    return per

def main():
    A = areas()
    tdir = os.path.join(REPO, "tournaments")
    if len(sys.argv) == 3:
        run, bot = sys.argv[1], sys.argv[2]
        rows = list(csv.DictReader(open(os.path.join(tdir, run, "results.csv"))))
        per = record(rows, bot, A)
        for m in sorted(per, key=lambda m: A[m.lower()]):
            w, g = per[m]
            print(f"{m:<22}{A[m.lower()]:>7}  {w}/{g}")
        return
    runs = sorted(d for d in os.listdir(tdir) if d[0].isdigit())
    hdr = "".join(f"{b:>11}" for _, _, b in BINS)
    print(f"{'tournament':<16}{'bot':<7}{'overall':>9}{hdr}{'rho(area)':>11}{'t':>7}")
    for run in runs:
        f = os.path.join(tdir, run, "results.csv")
        if not os.path.exists(f):
            continue
        rows = list(csv.DictReader(open(f)))
        for bot in sorted({r["team_a"] for r in rows} | {r["team_b"] for r in rows}):
            per = record(rows, bot, A)
            maps = sorted(per)
            if not maps:
                continue
            W = [per[m][0]/per[m][1] for m in maps]
            X = [A[m.lower()] for m in maps]
            rho = pear(midrank(W), midrank(X)); df = len(maps)-2
            t = rho*math.sqrt(df/(1-rho**2)) if abs(rho) < 1 else 0.0
            tw = sum(v[0] for v in per.values()); tg = sum(v[1] for v in per.values())
            cells = ""
            for lo, hi, _ in BINS:
                w = sum(per[m][0] for m in maps if lo <= A[m.lower()] <= hi)
                g = sum(per[m][1] for m in maps if lo <= A[m.lower()] <= hi)
                cells += f"{100.0*w/g:>10.1f}%" if g else f"{'-':>11}"
            print(f"{run:<16}{bot:<7}{100.0*tw/tg:>8.1f}%{cells}{rho:>+11.3f}{t:>7.2f}")
        print()

main()

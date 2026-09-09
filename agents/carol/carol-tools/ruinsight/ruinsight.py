#!/usr/bin/env python3
"""ruinsight -- does an instrument SEE the ruin-count gradient?

Carol's deficit against alice and bob is a monotone decline in win rate with map
ruin count (z ~ -6 in every tournament, five runs running). Carol's self-play
accept gate is measurably BLIND to it: 5,768 games give rho = +0.0093,
95% CI [-0.017, +0.035], and against carol_iter44 alone, 500 games give
rho = -0.0123, z = -0.28.

That is why this exists. Ten consecutive iterations aimed at ruin conversion were
gated on an instrument with no sensitivity to ruin conversion. Before trusting any
future ruin-conversion verdict, run this on the run that produced it and check the
instrument could have registered the effect at all.

    ruinsight.py gauntlet/<run-id> [...]        # one or more gauntlet runs
    ruinsight.py --tournament <run>             # a tournament run, carol's games

A NOTE ON WHAT IS NOT INDEPENDENT (doctrine 14): the bucket table and rho are two
displays of the same games. The table shows the SHAPE (monotone, or one odd
bucket); it does not corroborate the z. Do not cite both as agreeing evidence.
"""
import csv, glob, math, os, re, sys

def _repo_root():
    # Walk up until tools/mapdata/ruin_parity.txt exists, rather than counting
    # '..' levels -- an off-by-one there fails loudly here but would fail SILENTLY
    # in anything that treats a missing map as "no ruins".
    d = os.path.abspath(os.path.dirname(__file__))
    while True:
        if os.path.exists(os.path.join(d, 'tools', 'mapdata', 'ruin_parity.txt')):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            raise SystemExit("ruinsight: cannot locate tools/mapdata/ruin_parity.txt above "
                             + os.path.dirname(__file__))
        d = parent

REPO = _repo_root()
PARITY = os.path.join(REPO, 'tools', 'mapdata', 'ruin_parity.txt')

def ruins():
    d = {}
    for line in open(PARITY):
        m = re.match(r'(\S+)\s+(\d+)x(\d+)\s+ruins=\s*(\d+)', line)
        if m:
            d[m.group(1)] = int(m.group(4))
    return d

def trend(pairs):
    n = len(pairs)
    if n < 10:
        return None
    xs = [p[0] for p in pairs]; ys = [p[1] for p in pairs]
    mx = sum(xs)/n; my = sum(ys)/n
    sxy = sum((a-mx)*(b-my) for a, b in pairs)
    sxx = sum((a-mx)**2 for a in xs); syy = sum((b-my)**2 for b in ys)
    if sxx*syy == 0:
        return None
    rho = sxy/math.sqrt(sxx*syy)
    return rho, rho*math.sqrt(n-1), my, n

BUCKETS = [('<=11', 0, 11), ('12-17', 12, 17), ('18-23', 18, 23), ('>=24', 24, 999)]

def report(label, pairs):
    t = trend(pairs)
    if not t:
        print(f"{label}: too few games ({len(pairs)})"); return
    rho, z, my, n = t
    se = 1/math.sqrt(n-1)
    verdict = "SEES IT" if (rho < 0 and abs(z) >= 3) else "BLIND"
    print(f"\n{label}")
    print(f"  n={n}  win={100*my:.1f}%   rho={rho:+.4f}  z={z:+.2f}  "
          f"95% CI [{rho-1.96*se:+.4f}, {rho+1.96*se:+.4f}]   -> {verdict}")
    rows = []
    for name, lo, hi in BUCKETS:
        sub = [w for ru, w in pairs if lo <= ru <= hi]
        if sub:
            rows.append((name, sum(sub), len(sub), 100*sum(sub)/len(sub)))
    for name, w, nn, pct in rows:
        print(f"    {name:>6s}: {w:5d}/{nn:5d} = {pct:5.1f}%")
    if len(rows) >= 2:
        print(f"    spread (first-last): {rows[0][3]-rows[-1][3]:+.1f} points"
              f"   [shape only -- same games as the z above, not corroboration]")

def main(argv):
    R = ruins()
    if not argv:
        print(__doc__); return 1
    if argv[0] == '--tournament':
        for run in argv[1:]:
            p = run if run.endswith('.csv') else os.path.join(REPO, 'tournaments', run, 'results.csv')
            pairs = []
            for r in csv.DictReader(open(p)):
                if 'carol' not in (r['team_a'], r['team_b']) or r['map'] not in R:
                    continue
                pairs.append((R[r['map']], 1 if r['winner_bot'] == 'carol' else 0))
            report(f"TOURNAMENT {run} (carol vs alice/bob)", pairs)
        return 0
    for run in argv:
        p = run if run.endswith('.csv') else os.path.join(run, 'results.csv')
        byopp = {}
        missing = set()
        for r in csv.DictReader(open(p)):
            if r['map'] not in R:
                missing.add(r['map']); continue
            byopp.setdefault(r['opponent'], []).append(
                (R[r['map']], 1 if r['bot_result'] == 'win' else 0))
        if missing:
            print(f"  !! {len(missing)} map(s) absent from ruin_parity.txt and DROPPED: "
                  f"{', '.join(sorted(missing))}")
        for opp, pairs in sorted(byopp.items()):
            report(f"{os.path.basename(run.rstrip('/'))} vs {opp}", pairs)
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

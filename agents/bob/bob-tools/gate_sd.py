#!/usr/bin/env python3
"""What is my '+10 wins out of 50' gate actually worth, in sd?

The engine is deterministic, so re-running the SAME maps reproduces exactly and it
is tempting to treat the screen's standard error as zero. But an accept is a claim
about the map POPULATION (75 maps in tools/bc25-maps.txt), and a run samples 25 of
them. The sampling variance of `vs null` is what the gate must clear.

Method (paired per map, which is what makes it tight):
  d_m = (arm wins on map m, over BOTH sides) - (null wins on map m) in {-2..+2}
  vs_null = sum over the 25 sampled maps of d_m
  Var(vs_null) = n * s2(d) * (N-n)/(N-1)      n=25, N=75  -> FPC = 50/74 = 0.676

Pairing per map cancels map difficulty and spawn advantage exactly, because each
map contributes both sides to both arms. The FPC is an 18% cut in sd and is not a
nicety at n/N = 1/3.

Usage: gate_sd.py <run-dir> <null-arm> [arm ...]
"""
import csv, sys, statistics

NPOP = 75

def main():
    run, null = sys.argv[1], sys.argv[2]
    games = {}
    with open(f"{run}/results.csv") as fh:
        for r in csv.DictReader(fh):
            games[(r["opponent"], r["map"], r["bot_side"])] = r["bot_result"]
    arms = sys.argv[3:] or sorted({o for (o, _, _) in games} - {null})
    maps = sorted({m for (_, m, _) in games})
    n = len(maps)
    fpc = (NPOP - n) / (NPOP - 1)

    def wins(a, m):
        return sum(1 for s in ("A", "B") if games.get((a, m, s)) == "loss")

    print(f"run {run}   null={null}   n={n} of N={NPOP}   FPC={fpc:.3f} "
          f"(sd x{fpc**0.5:.3f})\n")
    print(f"{'arm':>10} {'vs null':>8} {'sd(vs null)':>12} {'z':>7} {'+10 gate = ':>12}{'sd':>5}")
    print('-'*60)
    for a in arms:
        if a == null:
            continue
        d = [wins(a, m) - wins(null, m) for m in maps]
        tot = sum(d)
        if len(d) < 2:
            continue
        var = statistics.variance(d) * n * fpc
        sd = var ** 0.5
        print(f"{a:>10} {tot:>+8} {sd:>12.2f} {tot/sd if sd else 0:>7.2f} "
              f"{10/sd if sd else 0:>12.2f}{'':>5}")
    # pooled estimate across arms, which is the number to quote for the GATE itself
    alld = []
    for a in arms:
        if a == null:
            continue
        alld += [wins(a, m) - wins(null, m) for m in maps]
    if len(alld) > 1:
        sd = (statistics.variance(alld) * n * fpc) ** 0.5
        print(f"\nPOOLED over arms: sd(vs null) = {sd:.2f} wins  ->  "
              f"a +10 gate is {10/sd:.2f} sd, a +7 gate is {7/sd:.2f} sd")

main()

#!/usr/bin/env python3
"""Derive the SAMPLED-gauntlet gate (25 maps of 75, both sides = 50 games) from a census.

Two independent variance components, and the standing gate accounted for neither explicitly:

 1. MAP SAMPLING. The engine is deterministic: for a fixed pair, a fixed map and a fixed side, the
    outcome never varies. So a census margin is a FIXED number, and the only thing a sampled run
    randomises is WHICH maps are in it. Per map the margin contribution is X = +2 / 0 / -2 (swept
    win / split / swept loss). Drawing k of N maps without replacement:
        Var(sum) = k * Var(X) * (N-k)/(N-1)
    This is computable EXACTLY from a full census -- no modelling assumption at all.

 2. PERTURBATION. A policy-neutral code change reshuffles which maps get swept. Under the null,
    sweeps fall either way with equal probability, so over k maps Var = 4 * k * sweep_rate.

Both must be taken from a POLICY-IDENTICAL census (a phase twin), never from the pair under test.

  sampledgate.py <census-run-dir> <policy-identical-opponent> [k]
"""
import csv, os, sys, math, collections

def main(run, opp, k=25):
    per = collections.defaultdict(dict)
    for r in csv.DictReader(open(os.path.join(run, "results.csv"))):
        if r["opponent"] != opp: continue
        per[r["map"]][r["bot_side"]] = 1 if r["bot_result"] == "win" else 0
    maps = [m for m, v in per.items() if len(v) == 2]
    N = len(maps)
    X = [2 * (sum(per[m].values()) - 1) for m in maps]      # +2 / 0 / -2
    sweeps = sum(1 for x in X if x != 0)
    mean = sum(X) / N
    varX = sum((x - mean) ** 2 for x in X) / N

    var_samp = k * varX * (N - k) / (N - 1)
    var_pert = 4 * k * (sweeps / N)
    sd = math.sqrt(var_samp + var_pert)

    print(f"sampled-gate derivation from {run} vs {opp}   (k={k} maps of N={N}, {2*k} games)")
    print(f"  census margin {sum(X):+d}   sweeps {sweeps}/{N} = {sweeps/N:.3f}   Var(per-map X) {varX:.3f}")
    print(f"  sd from MAP SAMPLING     {math.sqrt(var_samp):.2f}")
    print(f"  sd from PERTURBATION     {math.sqrt(var_pert):.2f}")
    print(f"  ==> sd of the {2*k}-game MARGIN  {sd:.2f}   (sd of the WIN COUNT {sd/2:.2f})")
    print()
    for z, name in ((2.0, "ACCEPT"), (1.4, "replicate floor")):
        m = z * sd
        print(f"  {name:16s} margin >= {m:+.1f}  ->  wins >= {(2*k + m)/2:.1f}/{2*k}")
    a = math.ceil((2 * k + 2.0 * sd) / 2)
    r = math.floor((2 * k + 1.4 * sd) / 2) - 1
    print(f"\n  GATE:  ACCEPT >= {a}/{2*k}   UNRESOLVED {r+1}..{a-1}   REJECT <= {r}")

main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 25)

#!/usr/bin/env python3
"""Estimate carol's census noise floor from a POLICY-IDENTICAL head-to-head.

A full-corpus census removes map SAMPLING error. It does not remove engine chaos: a code change
perturbs the PRNG stream, and two arms that differ only in phase still disagree. That residue is
what a census margin must clear, and it cannot be reduced by running more of the same maps.

Two arm totals cannot estimate a standard deviation -- but a fixed corpus gives 75 PAIRED map
records for free. Each map is played from both sides, so per map we have Sa (won as A) and Sb
(won as B), each 0/1. For policy-identical arms those differ only by noise, so

    E[(Sa - Sb)^2] = 2 * Var(S)        =>   Var(S) = mean(d^2) / 2,  d = Sa - Sb

and the standard deviation of a 150-game total is sqrt(150 * Var(S)).

DO NOT read the floor off the two arm totals. A near-draw between policy-identical arms is exactly
what binomial predicts, so it cannot even weakly reject binomial; a small total difference is the
convenient reading, not the informative one. The per-map variance is the whole point.

  noisefloor.py <run-dir> <opponent>
"""
import csv, os, sys, math, collections

def main(run, opp):
    per = collections.defaultdict(dict)
    for r in csv.DictReader(open(os.path.join(run, "results.csv"))):
        if r["opponent"] != opp: continue
        per[r["map"]][r.get("bot_side", r.get("side", "?"))] = 1 if r["bot_result"] == "win" else 0
    maps = [m for m, v in per.items() if len(v) == 2]
    if not maps:
        print("no complete both-sides pairs -- check the side column name"); return
    d2 = []
    swept = split = 0
    wins = 0
    for m in maps:
        a, b = list(per[m].values())
        d2.append((a - b) ** 2)
        wins += a + b
        if a == b: swept += 1
        else: split += 1
    n = len(maps)
    varS = sum(d2) / n / 2.0
    sd_total = math.sqrt(2 * n * varS)
    binom = math.sqrt(2 * n * 0.25)
    print(f"policy-identical calibration: {run}  vs {opp}")
    print(f"  maps paired            {n}   games {2*n}")
    print(f"  arm total              {wins}/{2*n}   margin (wins-losses) {wins - (2*n - wins):+d}")
    print(f"  maps DECIDED the same both sides (survive a phase change)  {swept}/{n} = {100*swept/n:.0f}%")
    print(f"  maps split by side (still a coin flip)                     {split}/{n} = {100*split/n:.0f}%")
    print()
    print(f"  Var(single-game S) from per-map pairs   {varS:.4f}   (binomial max 0.25)")
    print(f"  ==> sd of the {2*n}-game WIN COUNT       {sd_total:.2f} games"
          f"   = {100*sd_total/binom:.0f}% of binomial ({binom:.2f})")

    # UNITS. Fixed 2026-09-08 after this tool set a gate half as strict as it claimed.
    # sd_total is the sd of the WIN COUNT W. The gate below is quoted on the MARGIN
    # M = W - (N - W) = 2W - N, and Var(M) = 4*Var(W), so sd(M) = 2*sd(W). The original
    # version multiplied sd_total by 2 and called the result "2.0 sd" -- but that factor
    # of 2 is the win-count-to-margin conversion, so it was quoting a 1.0 sd threshold as
    # a 2.0 sd one. Every census gate derived from it was half as strict as advertised.
    # No verdict moved (iteration 42 was -0.77 sd and rejected; iteration 44 was +3.39 sd
    # and accepted on either gate), but the published effect sizes were inflated 2x.
    sd_margin = 2 * sd_total
    print(f"  ==> sd of the {2*n}-game MARGIN (wins-losses)  {sd_margin:.2f} games")
    print()
    print(f"  suggested census gate on MARGIN (wins-losses), from this floor:")
    print(f"    ACCEPT     >= +{2*sd_margin:.0f}   (2.0 sd)")
    print(f"    REPLICATE  +{1.4*sd_margin:.0f} .. +{2*sd_margin-1:.0f}   (1.4 - 2.0 sd)")
    print(f"    REJECT     <= +{1.4*sd_margin-1:.0f}")
    print()
    print(f"  to score a result:  z = margin / {sd_margin:.2f}"
          f"   (NOT margin / {sd_total:.2f} -- that is the win-count sd)")

main(sys.argv[1], sys.argv[2])

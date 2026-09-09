#!/usr/bin/env python3
"""Estimate carol's census noise floor from a POLICY-IDENTICAL head-to-head.

A full-corpus census removes map SAMPLING error. It does not remove engine chaos: a code change
perturbs the PRNG stream, and two arms that differ only in phase still disagree. That residue is
what a census margin must clear, and it cannot be reduced by running more of the same maps.

  noisefloor.py <run-dir> <opponent>

WHAT THE MARGIN IS MADE OF -- the exact identity, verified on all 7 census pairs on disk
--------------------------------------------------------------------------------------
Every map is played from both sides. Per map the bot wins Sa+Sb of 2 games, so its margin
contribution is 2*(Sa+Sb) - 2, which is +2 on a swept win, -2 on a swept loss, and EXACTLY ZERO
on a map that splits by side. Summing:

    margin (wins - losses)  ==  2 * (swept_wins - swept_losses)

**Split maps contribute nothing to the margin.** They are not a small term, they are identically
zero. The margin is a statistic of the SWEPT maps alone.

THE BUG THIS FILE USED TO HAVE (fixed 2026-09-09), and why it was invisible
--------------------------------------------------------------------------
The original estimator formed d = Sa - Sb per map and set Var(S) = mean(d^2)/2. But d^2 is 1
exactly when the map SPLITS and 0 when it is swept. So the old tool estimated the margin's noise
floor from the maps that contribute nothing to the margin, and ignored the maps that are the
entire margin. It had the relationship inverted, not merely mis-scaled.

It went unnoticed because the calibration run happened to sit near the crossover (56% split /
44% swept), where the wrong formula returns a number close to the right one: 12.96 vs 11.49.
The discriminating case was already on disk. Run 20260908-204655 vs carol_i44_c32 splits 73 of 75
maps; the old estimator calls that pair the NOISIEST ever measured, sd(margin) = 17.09, when it is
in fact by far the QUIETEST, sd(margin) = 2.83, precisely because almost nothing is swept. Two
hypotheses that agree on the calibration run disagree 6x on that one, in opposite directions.

Lesson recorded in LEARNINGS.md: an estimator validated on a single near-symmetric case has not
been validated at all -- find the lopsided case, which is usually already in gauntlet/.

ESTIMATING THE FLOOR CORRECTLY
------------------------------
Per map let X = I(swept win) - I(swept loss). Then margin = 2 * sum(X). Under the null (the two
arms are policy-identical, so sweeps happen only by chaos and are equally likely in either
direction) E[X] = 0 and Var(X) = p + q = the SWEEP RATE. Hence

    sd(margin) = 2 * sqrt(n_maps * sweep_rate)

**The sweep rate must come from a POLICY-IDENTICAL pair**, not from the pair under test: a pair
that really does differ sweeps more maps, and feeding that back in would build the null out of the
alternative. Calibrate on a phase twin (run 20260908-173918, carol_phase vs carol_iter36, one
character apart) and apply the resulting constant gate to every census.
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
    n = len(maps)
    sw = sum(1 for m in maps if sum(per[m].values()) == 2)
    sl = sum(1 for m in maps if sum(per[m].values()) == 0)
    split = n - sw - sl
    wins = sum(sum(per[m].values()) for m in maps)
    margin = wins - (2 * n - wins)

    print(f"census calibration: {run}  vs {opp}")
    print(f"  maps paired            {n}   games {2*n}")
    print(f"  arm total              {wins}/{2*n}   margin (wins-losses) {margin:+d}")
    print(f"  swept wins {sw}   swept losses {sl}   split by side {split}")
    print(f"  identity check: 2*(SW-SL) = {2*(sw-sl):+d}  (must equal the margin above)")
    print()
    sweep_rate = (sw + sl) / n
    sd_margin = 2 * math.sqrt(n * sweep_rate)
    print(f"  sweep rate             {sw+sl}/{n} = {sweep_rate:.3f}   <-- the ONLY driver of margin noise")
    print(f"  ==> sd of the {2*n}-game MARGIN   {sd_margin:.2f} games")
    print(f"      (split maps contribute exactly 0; they are not part of this)")
    print()
    print(f"  gate on MARGIN, valid ONLY if this run is a policy-identical calibration:")
    print(f"    ACCEPT     >= +{2*sd_margin:.0f}   (2.0 sd)")
    print(f"    REPLICATE  +{1.4*sd_margin:.0f} .. +{2*sd_margin-1:.0f}   (1.4 - 2.0 sd)")
    print(f"    REJECT     <= +{1.4*sd_margin-1:.0f}")
    print(f"  to score a result:  z = margin / {sd_margin:.2f}")
    print()
    old = 2 * math.sqrt(2 * n * (split / n / 2.0))
    print(f"  [superseded estimator, for comparison only: {old:.2f} -- built from the SPLIT maps,")
    print(f"   which contribute nothing to the margin. Do not use.]")

main(sys.argv[1], sys.argv[2])

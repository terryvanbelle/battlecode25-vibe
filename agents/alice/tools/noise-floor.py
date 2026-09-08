#!/usr/bin/env python3
"""Estimate this lineage's census noise floor from a POLICY-IDENTICAL, PHASE-DIFFERENT pair.

    tools/noise-floor.py gauntlet/<run>/results.txt <opponent>

Why this exists: a census re-run of ONE build is exact (measured: 150/150 identical games).
A census MARGIN between two DIFFERENT builds is not, because any code change perturbs the
PRNG stream. So the floor must be measured with arms whose POLICY is identical and whose
PHASE differs -- for this lineage, src/alice_phase, which is alice_iter30 with the PRNG seed
offset changed from +17 to +18 and nothing else.

Two independent estimates of sd(net swept), which should agree:

  1. DECISIVE-MAP COUNT. Under a true null every decisive (non-split) map is a coin flip
     contributing +1 or -1 to net swept, so Var = #decisive and sd = sqrt(#decisive).
     Split maps contribute 0 and cancel exactly.
  2. PER-GAME BINOMIAL, for contrast: sd(wins) = sqrt(n/4) over n games. The ratio of (1)
     to this is the "% of binomial" figure -- below 100% means map-level pairing is
     removing some, but nowhere near all, of the variance.

Read the OUTPUT as a floor on |net swept|, not as a p-value: a margin inside ~1 sd of zero
is indistinguishable from engine chaos on this corpus, and MORE OF THE SAME MAPS CANNOT FIX
THAT -- the residue is chaos on a fixed corpus, not sampling error.
"""
import sys, collections, math

path, opp = sys.argv[1], sys.argv[2]
rec = collections.defaultdict(lambda: [0, 0])   # map -> [bot wins, games]
for line in open(path):
    f = line.split()
    if f[0] != "RESULT" or f[1] != opp:
        continue
    rec[f[2]][1] += 1
    if f[3] == f[4]:
        rec[f[2]][0] += 1

full = {m: w for m, (w, n) in rec.items() if n == 2}
sw = sum(1 for w in full.values() if w == 2)
sl = sum(1 for w in full.values() if w == 0)
split = sum(1 for w in full.values() if w == 1)
games = sum(n for _, n in rec.values())
wins = sum(w for w, _ in rec.values())
decisive = sw + sl

sd_map = math.sqrt(decisive) if decisive else 0.0
sd_binom = math.sqrt(games / 4) if games else 0.0

print(f"opponent            : {opp}")
print(f"maps (both sides)   : {len(full)}   games: {games}")
print(f"record              : {wins}/{games} ({100*wins/games:.1f}%)")
print(f"SW / SL / split     : {sw} / {sl} / {split}")
print(f"NET SWEPT           : {sw-sl:+d}")
print()
# NB: "decisive" = one arm swept the map (won both sides). It is NOT the same statistic as
# "maps whose result survives a phase change", which compares two runs map-by-map. Only
# decisive maps contribute to net swept; split maps cancel exactly.
print(f"decisive maps       : {decisive} of {len(full)}  "
      f"({100*decisive/len(full):.0f}% decisive, {100*split/len(full):.0f}% split)")
print(f"sd(net swept)       : {sd_map:.2f}   [= sqrt(decisive); each decisive map is a coin flip]")
# net_swept = wins - N exactly (wins = 2*SW + split, losses = 2*SL + split, N = maps),
# so sd(net swept) and sd(wins) are the SAME quantity and compare directly -- no factor of 2.
print(f"sd(wins), binomial  : {sd_binom:.2f}   -> map pairing keeps "
      f"{100*sd_map/sd_binom:.0f}% of binomial")
print()
print(f"FLOOR: a |net swept| below ~{sd_map:.0f} is 1 sd -- indistinguishable from chaos.")
print(f"       accept >= ~{2*sd_map:.0f} (2 sd); replicate between ~{sd_map:.0f} and ~{2*sd_map:.0f}.")

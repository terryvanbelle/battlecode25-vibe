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
    if len(f) < 5 or f[0] != "RESULT" or f[1] != opp:
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

# --- UNIT-BEARING NAMES (coordinator, 2026-09-08) -------------------------------
# Another lineage's gate tool computed sd of the WIN COUNT and printed a threshold
# quoted on the MARGIN, so every gate it produced was 1.0 sd wearing a 2.0 sd label.
# The three statistics here, and their exact relationships, derived not assumed:
#
#   net_swept      = SW - SL
#   wins           = 2*SW + split ,  N = SW + SL + split
#   wins - N       = SW - SL              = net_swept          (EXACT, so sd is EQUAL)
#   wins - losses  = 2*(SW - SL)          = 2 * net_swept      (so sd is DOUBLED)
#
# Var(net_swept) = Var(2*SW - decisive) = 4 * decisive/4 = decisive, hence sqrt(decisive).
# This gate and this floor are BOTH in net_swept units, so the sd-multiple is invariant
# to the choice -- that invariance is the protection, not luck.
sd_net_swept = math.sqrt(decisive) if decisive else 0.0
sd_wins      = sd_net_swept          # identical by wins - N == net_swept, above
sd_win_minus_loss = 2 * sd_net_swept # the OTHER margin; never compare a net_swept gate to this
sd_binom_wins = math.sqrt(games / 4) if games else 0.0

# THE CONTROL, not a note (doctrine 16): the identity above is checked on every run, so a
# future change that breaks it fails loudly here instead of silently halving a gate.
_net_from_sweeps = sw - sl
_net_from_wins   = wins - len(full)
assert _net_from_sweeps == _net_from_wins, (
    "UNIT ERROR: net_swept from sweeps (%d) != wins - N (%d). The gate and the floor are no "
    "longer in the same unit; do NOT read a verdict off this run."
    % (_net_from_sweeps, _net_from_wins))

sd_map = sd_net_swept      # legacy alias used by the prints below
sd_binom = sd_binom_wins

print(f"opponent            : {opp}")
print(f"maps (both sides)   : {len(full)}   games: {games}")
print(f"record              : {wins}/{games} ({100*wins/games:.1f}%)")
print(f"SW / SL / split     : {sw} / {sl} / {split}")
print(f"NET SWEPT (=wins-N) : {sw-sl:+d}   [unit: net_swept; wins-losses would be {2*(sw-sl):+d}]")
print()
# NB: "decisive" = one arm swept the map (won both sides). It is NOT the same statistic as
# "maps whose result survives a phase change", which compares two runs map-by-map. Only
# decisive maps contribute to net swept; split maps cancel exactly.
print(f"decisive maps       : {decisive} of {len(full)}  "
      f"({100*decisive/len(full):.0f}% decisive, {100*split/len(full):.0f}% split)")
print(f"sd_net_swept        : {sd_net_swept:.2f}   [= sqrt(decisive); == sd_wins; sd(wins-losses) = {sd_win_minus_loss:.2f}]")
# net_swept = wins - N exactly (wins = 2*SW + split, losses = 2*SL + split, N = maps),
# so sd(net swept) and sd(wins) are the SAME quantity and compare directly -- no factor of 2.
print(f"sd(wins), binomial  : {sd_binom:.2f}   -> map pairing keeps "
      f"{100*sd_map/sd_binom:.0f}% of binomial")

# --- Var(S) against the Bernoulli ceiling (coordinator's contamination check) ---
# S = this arm's per-map win proportion, in {0, 0.5, 1}. Under a genuine null E[S] = 0.5 and
# Var(S) <= 0.25, the maximum a proportion can have. A paired/squared estimator absorbs any
# DETERMINISTIC per-map asymmetry and charges it to chaos, so Var(S) > 0.25 is a contamination
# signal, not a surprise -- and the resulting floor is an UPPER BOUND, defensible to adopt only
# if adopted knowing it is a ceiling.
S = [w / 2.0 for w in full.values()]
var_null = sum((x - 0.5) ** 2 for x in S) / len(S)
mean_S = sum(S) / len(S)
var_obs = sum((x - mean_S) ** 2 for x in S) / len(S)
print()
print(f"mean per-map S      : {mean_S:.3f}   (a genuine null sits at 0.500)")
print(f"Var(S) about 0.500  : {var_null:.3f}   ceiling 0.250  "
      f"{'*** EXCEEDS CEILING -> contaminated, floor is an UPPER BOUND ***' if var_null > 0.25 else 'OK'}")
print(f"Var(S) about mean   : {var_obs:.3f}")
print()
print(f"FLOOR (net_swept unit): |net_swept| below ~{sd_net_swept:.0f} is 1 sd -- indistinguishable from chaos.")
print(f"       accept >= ~{2*sd_map:.0f} (2 sd); replicate between ~{sd_map:.0f} and ~{2*sd_map:.0f}.")

# --- the check that matters most: is this "null" actually null? ---
if sd_map and abs(sw - sl) > 2 * sd_map:
    print()
    print(f"*** WARNING: net swept {sw-sl:+d} is {abs(sw-sl)/sd_map:.1f} sd from zero.")
    print("    A POLICY-IDENTICAL pair must be mean-zero. It is not, so this pair is NOT a")
    print("    valid null: the perturbation has a SYSTEMATIC effect and the sd above is")
    print("    understated. Treat |net swept| of this size as reachable by an incidental")
    print("    PRNG-stream shift -- i.e. by a change with no policy content at all.")

#!/usr/bin/env python3
"""How much does a 50-game head-to-head arm move when only the MAP DRAW changes?

The engine is deterministic, so a rerun on the same maps reproduces exactly. That makes
se = 0 for the question "what happened on these 25 maps" and says nothing about the
question an accept actually asks: does the change help over the 75-map population?

The estimator is paired by construction. Each map contributes both sides, so the natural
sampling unit is per-map wins w in {0,1,2}; map difficulty and spawn advantage live inside
w and cancel when the same map is drawn for both arms. A run's 50-game count is
sum(w) over a sample of n=25 maps drawn without replacement from N=75, so

    Var(count) = n * s^2 * (N-n)/(N-1)      with s^2 the population variance of w,
                                             estimated from the run's own 25 maps.

The (N-n)/(N-1) = 50/74 term is a real 18% reduction in sd, not a nicety: a third of the
corpus is in every sample.
"""
import csv, glob, os, sys, math
from collections import defaultdict

N_POP, N_DRAW = 75, 25
FPC = (N_POP - N_DRAW) / (N_POP - 1)

rows = []
for run in sorted(glob.glob("gauntlet/*/results.csv")):
    per = defaultdict(lambda: defaultdict(int))
    ngames = defaultdict(lambda: defaultdict(int))
    for r in csv.DictReader(open(run)):
        per[r["opponent"]][r["map"]] += 1 if r["bot_result"] == "win" else 0
        ngames[r["opponent"]][r["map"]] += 1
    for opp, mw in per.items():
        maps = [m for m in mw if ngames[opp][m] == 2]      # both sides played
        if len(maps) < 20: continue
        w = [mw[m] for m in maps]
        n = len(w); mean = sum(w)/n
        s2 = sum((x-mean)**2 for x in w)/(n-1)
        sd_count = math.sqrt(n * s2 * FPC)
        sw = sum(1 for x in w if x == 2); sl = sum(1 for x in w if x == 0)
        p_sw = sw/n
        sd_sw = math.sqrt(n * p_sw*(1-p_sw) * FPC)
        rows.append((os.path.basename(os.path.dirname(run)), opp, n, sum(w),
                     sd_count, sw, sl, sd_sw))

print(f"{'run':<16}{'opponent':<18}{'maps':>5}{'wins':>6}{'sd(wins)':>9}"
      f"{'SW':>4}{'SL':>4}{'sd(SW)':>8}")
for r in rows:
    print(f"{r[0]:<16}{r[1]:<18}{r[2]:>5}{r[3]:>6}{r[4]:>9.2f}{r[5]:>4}{r[6]:>4}{r[7]:>8.2f}")

sds  = [r[4] for r in rows]
sdsw = [r[7] for r in rows]
print(f"\narms = {len(rows)}")
print(f"sd(50-game win count):  median {sorted(sds)[len(sds)//2]:.2f}   "
      f"range {min(sds):.2f}-{max(sds):.2f}")
print(f"sd(swept-map count SW): median {sorted(sdsw)[len(sdsw)//2]:.2f}   "
      f"range {min(sdsw):.2f}-{max(sdsw):.2f}")
m = sorted(sds)[len(sds)//2]
print(f"\nA one-sided 95% gate on a single 50-game arm needs the margin over 25 to exceed")
print(f"1.645 * sd = {1.645*m:.1f} wins, i.e. a raw count of about {25 + 1.645*m:.0f}/50")
print(f"before the map draw alone stops being an adequate explanation.")

# ---- restricted to the arms that actually gate an accept -------------------
# A lopsided arm has little variance because per-map wins are pinned at 0 or 2, so
# pooling all 59 arms understates the sd exactly where the gate lives. The accept
# question is only ever asked of a near-even arm.
comp = [r for r in rows if 20 <= r[3] <= 30]
if comp:
    s = sorted(r[4] for r in comp)
    med = s[len(s)//2]
    print(f"\n--- competitive arms only (20-30 wins of 50): n = {len(comp)} ---")
    print(f"sd(win count): median {med:.2f}  range {min(s):.2f}-{max(s):.2f}")
    print(f"95% one-sided accept needs >= {25 + 1.645*med:.1f}/50  "
          f"(observed practice was >25, i.e. 26)")
    print(f"\nSW under a DEAD-EVEN arm (24-26 wins), which is the null the floor must exclude:")
    for r in sorted((x for x in comp if 24 <= x[3] <= 26), key=lambda x: -x[5]):
        print(f"  {r[0]} {r[1]:<16} wins={r[3]:<3} SW={r[5]:<3} SL={r[6]:<3} split={r[2]-r[5]-r[6]}")
    print(f"\nIdentity check (wins - maps == SW - SL) on every arm:",
          all(r[3] - r[2] == r[5] - r[6] for r in rows))

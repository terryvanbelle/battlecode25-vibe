#!/usr/bin/env python3
"""THE BINDING BUDGET. A production ranking denominated in SPAWN paint optimises a
BUILD budget. Total output is bounded by ACTION paint. Before acting on such a
ranking, check that the quantity you want to move is bounded by the same budget.

Per action-capable unit-turn, split the idle turns by CAUSE:
  1 acted
  2 idle: paint < ENGINE attack cost      -- hard starvation, the action budget binds
  3 idle: paint >= cost but < MY guard    -- self-imposed reserve, MY choice not the engine's
  5 off-duty: walking to a tower to refill -- also caused by paint, just earlier
  4 idle: could afford it, NO TARGET in range -- the mix is not the constraint
  0 not action-ready (cooldown)           -- excluded from the denominator
"""
import sys, re, collections
PAT = re.compile(r'IND "ZZ([SMPT])(\d)')
NAME = {1:"acted", 2:"idle: PAINT (< engine cost)", 3:"idle: paint < my guard",
        4:"idle: NO TARGET", 5:"off-duty: walking to refill"}
ORDER = [1,2,3,5,4]

def tally(path):
    c = collections.Counter()
    for ln in open(path):
        m = PAT.search(ln)
        if m: c[(m.group(1), int(m.group(2)))] += 1
    return c

def show(label, c):
    print(f"\n=== {label} ===")
    for u, uname in (("S","SOLDIER  (attack costs 5, my guard 15)"),
                     ("P","SPLASHER (attack costs 50, my guard 60)"),
                     ("M","MOPPER   (attack costs 0 -- can never lack paint)")):
        tot = sum(v for (uu, k), v in c.items() if uu == u and k != 0)
        if not tot: continue
        print(f"  {uname}   action-capable turns: {tot}")
        for k in ORDER:
            v = c.get((u, k), 0)
            if v or k in (1, 2, 4):
                print(f"      {NAME[k]:<34}{v:>8}  {100.0*v/tot:>6.2f}%")
    return c

a = tally(sys.argv[1]); b = tally(sys.argv[2])
show("ARM  alice_m3  (= m2: build a SPLASHER whenever affordable)", a)
show("CTL  alice_m3ctl", b)

print("\n=== the discriminating comparison, pooled over robot types ===")
def pooled(c):
    tot = sum(v for (u, k), v in c.items() if u != "T" and k != 0)
    return tot, {k: sum(v for (u, kk), v in c.items() if u != "T" and kk == k) for k in ORDER}
ta, da = pooled(a); tb, db = pooled(b)
print(f"  {'cause':<34}{'ARM':>16}{'CTL':>16}")
for k in ORDER:
    print(f"  {NAME[k]:<34}{da[k]:>9} {100.0*da[k]/ta:>5.1f}%{db[k]:>9} {100.0*db[k]/tb:>5.1f}%")
print(f"  {'TOTAL action-capable turns':<34}{ta:>9}       {tb:>9}")
paint_a = (da[2] + da[3] + da[5]) / ta; paint_b = (db[2] + db[3] + db[5]) / tb
tgt_a = da[4] / ta; tgt_b = db[4] / tb
print(f"\n  idle for want of PAINT (2+3+5)   arm {100*paint_a:>5.1f}%   ctl {100*paint_b:>5.1f}%")
print(f"  idle for want of TARGET (4)      arm {100*tgt_a:>5.1f}%   ctl {100*tgt_b:>5.1f}%")
print(f"  acted                            arm {100*da[1]/ta:>5.1f}%   ctl {100*db[1]/tb:>5.1f}%")

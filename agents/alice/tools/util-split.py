#!/usr/bin/env python3
"""TRAVEL-bound or SIGHT-bound? Registered gate, branch order fixed:
   >=60% of "no target in action range" turns have work IN VISION -> TRAVEL-BOUND
   <=30% -> SIGHT-BOUND (folds into B0's 93.6% information ceiling)
   between -> INCONCLUSIVE, split by phase, act on nothing."""
import sys, re, collections
PAT = re.compile(r'round (\d+) .*IND "ZZ([SMPT])(\d)')
NAME = {1:"acted", 2:"idle: PAINT < engine cost", 3:"idle: below my own guard",
        5:"off-duty: refill walk", 6:"idle: NO TARGET, work IS in vision",
        4:"idle: NO TARGET, no work in vision"}
ORDER = [1,2,3,5,6,4]
c = collections.Counter()
for ln in open(sys.argv[1]):
    m = PAT.search(ln)
    if not m: continue
    r, u, k = int(m.group(1)), m.group(2), int(m.group(3))
    if u == "T" or k == 0: continue
    c[(u,k)] += 1; c[('*',k)] += 1
    band = next(b for b in (300,600,1000,3000) if r <= b)
    c[(band,k)] += 1

def block(title, key):
    tot = sum(c[(key,k)] for k in ORDER)
    if not tot: return None
    print(f"\n  {title}   action-capable turns: {tot}")
    for k in ORDER:
        print(f"      {NAME[k]:<38}{c[(key,k)]:>8}  {100.0*c[(key,k)]/tot:>6.2f}%")
    return tot

print("=== HEAD (src/alice) vs alice_iter43, 6 maps, behaviour-neutral probe ===")
for u, n in (("S","SOLDIER"),("P","SPLASHER"),("M","MOPPER")): block(n, u)
tot = block("ALL MOBILE UNITS", '*')

print("\n=== THE REGISTERED GATE: population = 'no target in action range', AFTER r300 ===")
nt6 = sum(c[(b,6)] for b in (600,1000,3000))
nt4 = sum(c[(b,4)] for b in (600,1000,3000))
share = 100.0*nt6/(nt6+nt4)
print(f"  work IS in vision but out of action range : {nt6:>8}")
print(f"  no workable tile in vision at all         : {nt4:>8}")
print(f"  ---- share with work in vision            : {share:>7.1f}%")
v = "TRAVEL-BOUND" if share >= 60 else ("SIGHT-BOUND" if share <= 30 else "INCONCLUSIVE")
print(f"\n  VERDICT: {v}   (>=60 travel | <=30 sight | else inconclusive)")

print("\n=== phase split (registered as the follow-up, reported regardless) ===")
print(f"  {'rounds':<12}{'turns':>9}{'acted':>8}{'PAINT':>8}{'in-vision':>11}{'no-vision':>11}{'travel share':>14}")
prev = 0
for b in (300,600,1000,3000):
    t = sum(c[(b,k)] for k in ORDER)
    if not t: continue
    s6, s4 = c[(b,6)], c[(b,4)]
    ts = 100.0*s6/(s6+s4) if (s6+s4) else 0
    print(f"  {str(prev+1)+'-'+str(b):<12}{t:>9}{100.0*c[(b,1)]/t:>7.1f}%{100.0*c[(b,2)]/t:>7.1f}%"
          f"{100.0*s6/t:>10.1f}%{100.0*s4/t:>10.1f}%{ts:>13.1f}%")
    prev = b

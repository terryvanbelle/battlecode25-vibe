#!/usr/bin/env python3
"""Evaluate bob_symprobe SYMRES traces.

Written BEFORE the probe ran, per the pre-registration in TRAINING_LOG
("pre-register the estimator, not just the cut-offs" -- LEARNINGS 48).

Input: one or more verbose match logs, each named <map>.log, containing lines
    SYMRES type=MOPPER born=310 res=352 life=42 which=0
and (optionally) a line carrying the engine's own truth for that map, e.g.
    # map=Leaf 60x60 symmetry=2

CHECK ORDER IS DELIBERATE. Correctness first, timing second: a probe that
resolves fast and resolves WRONG looks identical in the output to one that
works. Only if `which` forms a consistent bijection with the engine's
`symmetry` across maps does any timing number mean anything.
"""
import re, sys, collections, statistics

res_re = re.compile(r'SYMRES type=(\w+) born=(-?\d+) res=(-?\d+) life=(-?\d+) which=(\d)')
truth_re = re.compile(r'symmetry=(\d)')

per_map = collections.defaultdict(list)
truth = {}
for path in sys.argv[1:]:
    name = path.split('/')[-1].rsplit('.', 1)[0]
    for line in open(path, errors='replace'):
        m = res_re.search(line)
        if m:
            per_map[name].append((m.group(1), int(m.group(2)), int(m.group(3)),
                                  int(m.group(4)), int(m.group(5))))
        t = truth_re.search(line)
        if t and name not in truth:
            truth[name] = int(t.group(1))

print("=== 1. CORRECTNESS: is `which` a consistent bijection with engine `symmetry`? ===")
pairs = collections.defaultdict(collections.Counter)
for name, rows in per_map.items():
    if name not in truth:
        continue
    for _, _, _, _, w in rows:
        pairs[truth[name]][w] += 1
if not pairs:
    print("  no map had both a SYMRES and an engine symmetry= line -- cannot check")
else:
    bad = False
    for eng in sorted(pairs):
        c = pairs[eng]
        tot = sum(c.values())
        top, n = c.most_common(1)[0]
        print(f"  engine symmetry={eng}: probe says {dict(c)}  -> {100*n/tot:.1f}% agree on {top}")
        if n != tot:
            bad = True
    seen = [c.most_common(1)[0][0] for c in pairs.values()]
    if len(set(seen)) != len(seen):
        bad = True
        print("  !! NOT a bijection: two engine symmetries map to the same probe answer")
    print("  VERDICT:", "INCONSISTENT -- timing numbers below are meaningless" if bad
          else "consistent bijection; timing is interpretable")

print()
print("=== 2. TIMING: rounds from a robot's birth to resolving ===")
allrows = [r for rows in per_map.values() for r in rows]
if not allrows:
    print("  no SYMRES lines at all -- no robot ever resolved. Direction is dead in its per-robot form.")
    sys.exit(0)
print(f"  {'map':16} {'robots resolved':>15} {'median life':>12} {'p90 life':>9}")
for name in sorted(per_map):
    lives = sorted(r[3] for r in per_map[name])
    print(f"  {name:16} {len(lives):15d} {statistics.median(lives):12.0f} "
          f"{lives[int(0.9*(len(lives)-1))]:9d}")
lives = sorted(r[3] for r in allrows)
med = statistics.median(lives)
print(f"  {'ALL':16} {len(lives):15d} {med:12.0f} {lives[int(0.9*(len(lives)-1))]:9d}")
print()
by_type = collections.Counter(r[0] for r in allrows)
print("  resolved robots by type:", dict(by_type))
print()
print("=== 3. PRE-REGISTERED READING ===")
if med <= 100:
    print(f"  median resolve-life {med:.0f} <= 100  ->  fires within a typical unit's lifetime.")
    print("     BUILD THE TREATMENT ARM.")
elif med <= 300:
    print(f"  median resolve-life {med:.0f} in 100-300  ->  fires only for long-lived units.")
    print("     ATTACH THE TREATMENT TO TOWERS, not to moppers. Do not paper over this.")
else:
    print(f"  median resolve-life {med:.0f} > 300  ->  too slow for the per-robot form.")
    print("     CLOSE the direction; do not re-open comms through the back door.")
print()
print("  NB this counts only robots that DID resolve. The share that never resolved")
print("  is the other half of the answer and is not in these lines by construction --")
print("  compare `resolved robots by type` against the spawn counts in the same log.")

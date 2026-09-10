#!/usr/bin/env python3
"""BEFORE removing or replacing a mechanism: measure what it is CURRENTLY producing,
in the control, on the maps you will test on.

    tools/baseline-yield.py <dump-of-control-on-the-test-maps>

WHY THIS EXISTS. Three times in one session I valued a mechanism in one population
and acted on it in another:
  1. stage-1 targets imported from one opponent's corpus onto another's maps, where
     the control already met them -- so the test could not register a pass;
  2. a 3.8x share discrepancy that resolved as pure opponent-dependence;
  3. M1: I deleted a chip-gated override priced at 2.8% of decisive-window frames
     AGAINST CAROL, in a population where it was producing 38.2% of spawns.
Manipulation checks measure what an arm ADDS. Nothing measured what it TAKES AWAY.
This does, and it is mechanical, so it does not depend on my remembering that yields
are opponent-dependent -- which is the thing I demonstrably do not remember.

REGISTERED as a required item: an arm that removes or disables any existing
condition must cite this table for its own test population before it is built.
"""
import sys, re, collections

PAT = re.compile(r"T1 \$\d+ cov(\d+)m srp\d+ sold\d+ spl\d+ mop\d+ tw(\d+) twPaint(\d+) "
                 r"acts\[p(\d+) u(\d+) a\d+ s\d+ m\d+\] \+sold(\d+) \+mop(\d+) \+spl(\d+)")

def main():
    bot=None; acc=collections.defaultdict(lambda: collections.Counter()); maps=set()
    for ln in open(sys.argv[1]):
        m=re.match(r"=== GameHeader\s+team1=(\S+)",ln)
        if m: bot=m.group(1)
        m=re.match(r"=== MatchHeader map=(\S+) ",ln)
        if m: maps.add(m.group(1))
        if "| T1 " not in ln: continue
        g=PAT.search(ln)
        if not g: continue
        cov,tw,twp,p,u,ss,sm,sp=[int(x) for x in g.groups()]
        d=acc[bot]
        d['cov']=max(d['cov'],cov); d['tw']+=tw; d['twp']+=twp; d['p']+=p; d['u']+=u
        d['ss']+=ss; d['sm']+=sm; d['sp']+=sp; d['n']+=1
    print(f"=== BASELINE YIELD on the test population ({len(maps)} maps) ===")
    print("    what each mechanism is ALREADY producing here. Removing any of these")
    print("    costs you the number in its row.\n")
    for b in sorted(acc):
        d=acc[b]; t=d['ss']+d['sm']+d['sp']
        if not t: continue
        print(f"  {b}")
        print(f"    spawns {t:>5}   soldier {100*d['ss']/t:>5.1f}%   mopper {100*d['sm']/t:>5.1f}%"
              f"   splasher {100*d['sp']/t:>5.1f}%")
        print(f"    paint actions {d['p']:>6}   unpaint {d['u']:>6}"
              f"   mean towers {d['tw']/d['n']:>5.2f}   paint/tower {d['twp']/d['tw'] if d['tw'] else 0:>6.1f}"
              f"   peak cov {d['cov']}")
        print()
    return 0
sys.exit(main())

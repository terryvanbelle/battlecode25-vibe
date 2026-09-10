#!/usr/bin/env python3
"""Production efficiency: tiles painted per paint spent spawning, by unit type.

ONE PASS over full action logs. PAINT lines carry the actor's type and SPAWN lines
carry the built type, so numerator and denominator come from the same events in the
same games -- no chain of separately-measured ratios.

Registered before running (commit 3922a66): this is OUTPUT per paint, declared as
production efficiency, NOT outcome contribution. The named inversion condition is
that a type taking ENEMY-held ground is worth ~2x a type taking empty ground on a
coverage difference, and the production number cannot see that.
"""
import sys, re, collections
COST = {'SOLDIER':200, 'SPLASHER':300, 'MOPPER':100}

def main():
    t1=t2=None
    paint=collections.Counter(); spawn=collections.Counter(); games=set()
    for ln in open(sys.argv[1]):
        m=re.match(r"=== GameHeader\s+team1=(\S+)\s+team2=(\S+)",ln)
        if m: t1,t2=m.group(1),m.group(2)
        m=re.match(r"=== MatchHeader map=(\S+) ",ln)
        if m: games.add(m.group(1))
        p=re.match(r"round \d+ id\d+\(T(\d),(\w+)\) PAINT ",ln)
        if p: paint[(p.group(1),p.group(2))]+=1
        s=re.search(r"SPAWN id\d+\(T(\d),(\w+)\) at ",ln)
        if s: spawn[(s.group(1),s.group(2))]+=1
    who={'1':t1,'2':t2}
    print(f"=== PRODUCTION EFFICIENCY, {len(games)} games, one pass ===")
    print("    tiles painted / paint spent spawning that type. Declared: OUTPUT per")
    print("    paint, not outcome per paint.\n")
    print(f"  {'team':<8}{'type':<10}{'spawned':>9}{'spawn paint':>13}{'tiles':>9}{'TILES/PAINT':>13}{'rank':>6}")
    for team in ('1','2'):
        nm=who[team] or ('T'+team)
        rows=[]
        for ty in ('SOLDIER','SPLASHER','MOPPER'):
            n=spawn[(team,ty)]; tl=paint[(team,ty)]
            if not n and not tl: continue
            sp=n*COST[ty]
            rows.append((ty,n,sp,tl,tl/sp if sp else 0))
        rows.sort(key=lambda r:-r[4])
        for i,(ty,n,sp,tl,v) in enumerate(rows):
            print(f"  {nm[:7]:<8}{ty:<10}{n:>9}{sp:>13}{tl:>9}{v:>13.4f}{i+1:>6}")
        print()
    return 0
sys.exit(main())

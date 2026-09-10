#!/usr/bin/env python3
"""K2 -- the reachability half of the refill question: GATING or POSITIONING?

K1 found carol withdraws paint from its towers 5.3x more often per unit than alice
does, on a mechanism alice already ships (iteration 25). Two explanations, and they
cost very different amounts to fix:

  GATING      alice's units stand next to towers just as often and decline to
              withdraw -- a condition bug, cheap.
  POSITIONING alice's units are rarely next to a tower at all -- a movement
              problem, expensive.

`transferPaint` needs r^2 <= 2, i.e. CHEBYSHEV <= 1: the unit must be ADJACENT to
the tower. That half of the registered condition is purely positional, so it is
free from arena frames -- and measuring BOTH teams inside the SAME games makes it a
matched comparison with no cross-lineage source read at all.

What this CANNOT see, stated up front: a unit's own paint level and a tower's
stored paint. So this measures OPPORTUNITY, not the full registered predicate
(which also required <half tank and >=50 tower paint). Opportunity is an UPPER
BOUND on the withdraw rate, which is the useful direction: if alice's opportunity
is as high as carol's, the shortfall is gating.
"""
import sys, re
G=set(".#o*aAbBtTnNdDsSmMpP")
SIDE={'T1':(set("smp"),set("tnd")),'T2':(set("SMP"),set("TND"))}

def frames(lines):
    t1=t2=None;mapname=None;i=0
    while i<len(lines):
        m=re.match(r"=== GameHeader\s+team1=(\S+)\s+team2=(\S+)",lines[i])
        if m: t1,t2=m.group(1),m.group(2)
        m=re.match(r"=== MatchHeader map=(\S+) ",lines[i])
        if m: mapname=m.group(1)
        m=re.match(r"=== ARENA round (\d+)\s+(\d+)x(\d+)",lines[i])
        if m:
            rnd,W,H=int(m.group(1)),int(m.group(2)),int(m.group(3))
            rws={};j=i+1
            while j<len(lines) and not lines[j].startswith("    census"):
                rm=re.match(r"^\s*(\d+) (\S+)$",lines[j])
                if rm and len(rm.group(2))==W and set(rm.group(2))<=G: rws[int(rm.group(1))]=rm.group(2)
                j+=1
            if len(rws)==H: yield (t1,t2,mapname,rnd,W,H,[rws[y] for y in range(H)])
            i=j;continue
        i+=1

def main():
    lines=[l.rstrip("\n") for l in sys.stdin]
    tot={}
    for (t1,t2,mp,rnd,W,H,g) in frames(lines):
        who={'T1':t1,'T2':t2}
        for side,(mob,tow) in SIDE.items():
            nm='alice' if 'alice' in who[side] else ('carol' if 'carol' in who[side] else None)
            if nm is None: continue
            towers=[(x,y) for y in range(H) for x in range(W) if g[y][x] in tow]
            units=[(x,y) for y in range(H) for x in range(W) if g[y][x] in mob]
            if not units: continue
            adj=sum(1 for (x,y) in units
                    if any(max(abs(x-tx),abs(y-ty))<=1 for (tx,ty) in towers))
            near2=sum(1 for (x,y) in units
                      if any(max(abs(x-tx),abs(y-ty))<=2 for (tx,ty) in towers))
            d=tot.setdefault(nm,{'u':0,'adj':0,'near2':0,'tw':0,'f':0})
            d['u']+=len(units); d['adj']+=adj; d['near2']+=near2
            d['tw']+=len(towers); d['f']+=1
    if len(tot)<2: print("!! need both lineages",file=sys.stderr); return 1
    print("=== K2: is the refill shortfall GATING or POSITIONING? ===")
    print("    matched within the same games; positional half only (see docstring)\n")
    print(f"  {'':<8}{'unit-frames':>13}{'mean towers':>13}{'ADJACENT (r^2<=2)':>20}{'within Chebyshev 2':>21}")
    for nm in ('alice','carol'):
        d=tot[nm]
        print(f"  {nm:<8}{d['u']:>13}{d['tw']/d['f']:>13.2f}"
              f"{100*d['adj']/d['u']:>19.2f}%{100*d['near2']/d['u']:>20.2f}%")
    a,c=tot['alice'],tot['carol']
    ra,rc=a['adj']/a['u'],c['adj']/c['u']
    print(f"\n  adjacency ratio alice/carol = {ra/rc if rc else float('nan'):.2f}x")
    print(f"  K1 transfer ratio alice/carol = 0.19x (0.383 vs 2.044 per unit spawned)")
    print()
    print("  REGISTERED READING:")
    print("    if adjacency is comparable (>=0.7x) but transfers are 0.19x -> GATING, cheap")
    print("    if adjacency is itself far lower (<0.5x)                    -> POSITIONING, expensive")
    r=ra/rc if rc else 0
    print("  VERDICT: " + ("GATING -- alice stands beside its towers as often and does not draw"
                           if r>=0.7 else
                           "POSITIONING -- alice's units are rarely beside a tower"
                           if r<0.5 else "MIXED -- adjacency partly explains it; neither pure"))
    return 0
sys.exit(main())

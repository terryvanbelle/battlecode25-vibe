#!/usr/bin/env python3
"""J1 -- how many soldiers actually WORK a bare ruin, and what latency that implies.

Little's law on the measured working set raised a term I had never checked:
L = 1.56 visible bare ruins, lambda ~ 0.021 towers/round (built 2.75 -> 6.88 over
r100-300), so W = L/lambda ~ 75 rounds from "ruin visible" to "tower complete".
A flat working set is consistent with a discovery famine AND with a long service
time, and those imply opposite mechanisms. This measures the service side.

  crew          ally soldiers within the tower pattern's own footprint of a bare
                ruin: the 5x5 around it, i.e. Chebyshev <= 2 (r^2 <= 8).
  implied W     the pattern needs 24 tiles painted and a soldier paints on 19.0%
                of its turns (measured, three instruments), so with a crew of c
                the pattern takes about 24 / (0.19 * c) rounds.

LEDGER CHECKED FIRST, and it does NOT cover this. Iteration 56 closed
"concentration" at 1.01 soldiers -- but its subject was ENEMY TOWERS, whether
enough soldiers reach the same tower to convert 5-paint hits into a kill. This is
friendly ruins and pattern completion: a different site, a different action, and a
different payoff. Citing that kill here would be the scope creep I caught myself in
this morning with C2.
"""
import sys, re
from collections import Counter

VIS=[(dx,dy) for dx in range(-5,6) for dy in range(-5,6) if dx*dx+dy*dy<=20]
PAT=[(dx,dy) for dx in range(-2,3) for dy in range(-2,3)]
G=set(".#o*aAbBtTnNdDsSmMpP")
T={1:"s",2:"S"}

def frames(lines):
    mapname=None;i=0
    while i<len(lines):
        m=re.match(r"=== MatchHeader map=(\S+) (\d+)x(\d+)",lines[i])
        if m: mapname=m.group(1)
        m=re.match(r"=== ARENA round (\d+)\s+(\d+)x(\d+)",lines[i])
        if m:
            rnd,W,H=int(m.group(1)),int(m.group(2)),int(m.group(3))
            rws={};j=i+1
            while j<len(lines) and not lines[j].startswith("    census"):
                rm=re.match(r"^\s*(\d+) (\S+)$",lines[j])
                if rm and len(rm.group(2))==W and set(rm.group(2))<=G: rws[int(rm.group(1))]=rm.group(2)
                j+=1
            if len(rws)==H: yield (mapname,rnd,W,H,[rws[y] for y in range(H)])
            i=j;continue
        i+=1

def main():
    lines=[l.rstrip("\n") for l in sys.stdin]
    crews=[]; early=[]
    for (mp,rnd,W,H,g) in frames(lines):
        for team in (1,2):
            sg=T[team]
            sold=[(x,y) for y in range(H) for x in range(W) if g[y][x]==sg]
            if not sold: continue
            un=set()
            for (x,y) in sold:
                for dx,dy in VIS:
                    nx,ny=x+dx,y+dy
                    if 0<=nx<W and 0<=ny<H: un.add((nx,ny))
            for y in range(H):
                for x in range(W):
                    if g[y][x]!='o' or (x,y) not in un: continue
                    c=sum(1 for (dx,dy) in PAT
                          if 0<=x+dx<W and 0<=y+dy<H and g[y+dy][x+dx]==sg)
                    # WIDER BOUND, because Chebyshev<=2 UNDERCOUNTS: a soldier's
                    # action radius is r^2<=9 (Chebyshev 3), so one standing up to
                    # 3 tiles outside the 5x5 can still paint pattern tiles. Any
                    # soldier within Chebyshev 5 of the centre can reach at least
                    # one pattern tile, so `wide` is an over-count and `crew` an
                    # under-count: the truth is bracketed.
                    wide=sum(1 for dx in range(-5,6) for dy in range(-5,6)
                             if 0<=x+dx<W and 0<=y+dy<H and g[y+dy][x+dx]==sg)
                    rec=dict(map=mp,rnd=rnd,team=team,crew=c,wide=wide)
                    crews.append(rec)
                    if rnd<=300: early.append(rec)
    if not crews:
        print("!! no visible bare ruins found",file=sys.stderr); return 1
    def blk(lab,rs):
        n=len(rs); c=Counter(r['crew'] for r in rs)
        mean=sum(r['crew'] for r in rs)/n
        print(f"  {lab:<34} visible bare ruins={n:>4}   MEAN CREW={mean:>5.2f}")
        print(f"  {'':<34} crew=0: {100*c[0]/n:>5.1f}%   1: {100*c[1]/n:>5.1f}%"
              f"   2: {100*c[2]/n:>5.1f}%   >=3: {100*sum(v for k,v in c.items() if k>=3)/n:>5.1f}%")
        eff=max(mean,1e-9)
        wm=sum(r['wide'] for r in rs)/n
        print(f"  {'':<34} implied completion time = 24 / (0.19 * {mean:.2f})"
              f" = {24/(0.19*eff):>6.0f} rounds")
        print(f"  {'':<34} WIDE crew (Chebyshev<=5, an OVER-count) = {wm:.2f}"
              f"  -> {24/(0.19*max(wm,1e-9)):>4.0f} rounds")
        print(f"  {'':<34} so completion is bracketed: "
              f"{24/(0.19*max(wm,1e-9)):.0f}-{24/(0.19*eff):.0f} rounds")
    print("=== J1: the crew on a visible bare ruin ===\n")
    blk("all rounds",crews)
    blk("DECISIVE WINDOW (r<=300)",early)
    print("\n  Little's law cross-check: L = 1.56 visible ruins, lambda = 0.021 towers/round")
    print("  -> W = L/lambda = 74 rounds. Compare with the implied completion time above:")
    print("  if they agree, the working set IS service time and discovery is not the limiter.")
    return 0
sys.exit(main())

#!/usr/bin/env python3
"""Is alice's dispersal a POLICY, or a CONSEQUENCE of expansion-first?

The two hypotheses differ sharply on ONE population: units with no distant
assignment. In alice's code a soldier targets a ruin it can SEE and otherwise
wanders ballistically (WANDER_RUN=25).

  POLICY      -> unassigned units spread anyway; their distance to an ally tower
                 is no smaller than an assigned unit's.
  CONSEQUENCE -> unassigned units stay near towers; only assigned ones are far.

Measured on the same frames for BOTH lineages, so the comparison is like-for-like.
"""
import sys,re,statistics
from collections import deque
VIS=[(dx,dy) for dx in range(-5,6) for dy in range(-5,6) if dx*dx+dy*dy<=20]
G=set(".#o*aAbBtTnNdDsSmMpP")
T={1:("s",set("tnd")),2:("S",set("TND"))}

def frames(lines):
    t1=t2=None;mp=None;i=0
    while i<len(lines):
        m=re.match(r"=== GameHeader\s+team1=(\S+)\s+team2=(\S+)",lines[i])
        if m: t1,t2=m.group(1),m.group(2)
        m=re.match(r"=== MatchHeader map=(\S+) ",lines[i])
        if m: mp=m.group(1)
        m=re.match(r"=== ARENA round (\d+)\s+(\d+)x(\d+)",lines[i])
        if m:
            rnd,W,H=int(m.group(1)),int(m.group(2)),int(m.group(3))
            rows,j={},i+1
            while j<len(lines) and not lines[j].startswith("    census"):
                rm=re.match(r"^\s*(\d+) (\S+)$",lines[j])
                if rm and len(rm.group(2))==W and set(rm.group(2))<=G: rows[int(rm.group(1))]=rm.group(2)
                j+=1
            if len(rows)==H: yield (t1,t2,mp,rnd,W,H,[rows[y] for y in range(H)])
            i=j;continue
        i+=1

def main():
    lines=[l.rstrip("\n") for l in sys.stdin]
    out={}
    for (t1,t2,mp,rnd,W,H,g) in frames(lines):
        for team in (1,2):
            sg,tow=T[team]
            who=t1 if team==1 else t2
            nm='alice' if 'alice' in who else ('carol' if 'carol' in who else None)
            if nm is None: continue
            tw=[(x,y) for y in range(H) for x in range(W) if g[y][x] in tow]
            if not tw: continue
            # BFS distance from towers over non-wall tiles
            INF=10**9; d=[[INF]*W for _ in range(H)]; q=deque()
            for (x,y) in tw: d[y][x]=0; q.append((x,y))
            while q:
                x,y=q.popleft()
                for dx in (-1,0,1):
                    for dy in (-1,0,1):
                        if dx==0 and dy==0: continue
                        nx,ny=x+dx,y+dy
                        if 0<=nx<W and 0<=ny<H and g[ny][nx]!='#' and d[ny][nx]==INF:
                            d[ny][nx]=d[y][x]+1; q.append((nx,ny))
            for y in range(H):
                for x in range(W):
                    if g[y][x]!=sg: continue
                    ruin=any(0<=x+dx<W and 0<=y+dy<H and g[y+dy][x+dx]=='o' for dx,dy in VIS)
                    if d[y][x]>=INF: continue
                    out.setdefault((nm,ruin),[]).append(d[y][x])
    print("=== distance to the nearest ALLY TOWER, by whether a ruin is in vision ===\n")
    print(f"  {'lineage':<8}{'ruin in vision':>16}{'n':>7}{'median':>9}{'mean':>8}{'p90':>7}")
    for nm in ('alice','carol'):
        for r in (True,False):
            v=sorted(out.get((nm,r),[]))
            if not v: continue
            print(f"  {nm:<8}{('ASSIGNED' if r else 'unassigned'):>16}{len(v):>7}"
                  f"{statistics.median(v):>9.1f}{statistics.mean(v):>8.1f}{v[int(.9*len(v))]:>7}")
    a1=out.get(('alice',True),[]); a0=out.get(('alice',False),[])
    if a1 and a0:
        m1,m0=statistics.median(a1),statistics.median(a0)
        print(f"\n  alice: unassigned median {m0:.1f} vs assigned {m1:.1f}  -> ratio {m0/m1 if m1 else 0:.2f}x")
        print("  POLICY if unassigned are NOT closer (ratio >= ~0.9); CONSEQUENCE if clearly closer.")
        print("  VERDICT: " + ("POLICY -- unassigned units disperse anyway" if m0>=0.9*m1
                               else "CONSEQUENCE -- dispersal tracks assignment"))
    return 0
sys.exit(main())

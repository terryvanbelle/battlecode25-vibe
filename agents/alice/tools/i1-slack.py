#!/usr/bin/env python3
"""Requirement I, stage 1 -- counting the population the gradient's re-open needs.

Stage 0 closed the own-paint gradient in both framings and left one condition,
written as a testable sentence: *re-open only if a measurement shows a population
of soldiers that are SIMULTANEOUSLY idle and near unexplored ground.* This counts
it. It is the same 51-frame starved-map trajectory data; no new games.

  IDLE            zero EMPTY tiles anywhere in the soldier's 69-tile vision disc.
                  That is the strong form -- not merely "no work in action range"
                  but "no work in sight at all".
  NEAR UNEXPLORED walking distance (8-connected, around walls) from the soldier to
                  the nearest tile outside the TEAM's current vision union.
  SLACK           an idle soldier near unexplored ground that is NOT already
                  heading into it. Measured, not assumed: its realised new-to-team
                  area over the following 50 turns.

THE POINT. Stage 0 found that idle soldiers already cover MORE ground than working
ones. If every idle-and-near soldier is already converting that into new team area,
there is no slack for a mechanism to recover and the re-open condition fails on
supply rather than on signal. If a large fraction sit idle beside unexplored ground
and bring back nothing, the condition is met and the direction re-opens.
"""
import sys, re
from collections import deque

VIS=[(dx,dy) for dx in range(-5,6) if True for dy in range(-5,6) if dx*dx+dy*dy<=20]
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

def disc(x,y,W,H,g):
    s=set()
    for dx,dy in VIS:
        nx,ny=x+dx,y+dy
        if 0<=nx<W and 0<=ny<H and g[ny][nx]!='#': s.add((nx,ny))
    return s

def main():
    lines=[l.rstrip("\n") for l in sys.stdin]
    bymap={}
    for (mp,rnd,W,H,g) in frames(lines): bymap.setdefault(mp,{})[rnd]=(W,H,g)
    recs=[]
    for mp,fr in bymap.items():
        rounds=sorted(fr); t0=rounds[0]; W,H,g0=fr[t0]
        for team in (1,2):
            sg=T[team]
            start=[(x,y) for y in range(H) for x in range(W) if g0[y][x]==sg]
            if not start: continue
            teamu=set()
            for (sx,sy) in start: teamu|=disc(sx,sy,W,H,g0)
            # multi-source BFS from every tile OUTSIDE the team union
            INF=10**9; d=[[INF]*W for _ in range(H)]; q=deque()
            for y in range(H):
                for x in range(W):
                    if g0[y][x]!='#' and (x,y) not in teamu:
                        d[y][x]=0; q.append((x,y))
            while q:
                x,y=q.popleft()
                for dx in (-1,0,1):
                    for dy in (-1,0,1):
                        if dx==0 and dy==0: continue
                        nx,ny=x+dx,y+dy
                        if 0<=nx<W and 0<=ny<H and g0[ny][nx]!='#' and d[ny][nx]==INF:
                            d[ny][nx]=d[y][x]+1; q.append((nx,ny))
            # track
            tracks={i:[p] for i,p in enumerate(start)}
            alive={i:p for i,p in enumerate(start)}
            for t in rounds[1:]:
                Wn,Hn,gn=fr[t]
                cand=[(x,y) for y in range(Hn) for x in range(Wn) if gn[y][x]==sg]
                pairs=[]
                for i,(px,py) in alive.items():
                    for c in cand:
                        dd=max(abs(c[0]-px),abs(c[1]-py))
                        if dd<=1: pairs.append((dd,i,c))
                pairs.sort(); used=set(); na={}
                for dd,i,c in pairs:
                    if i in na or c in used: continue
                    na[i]=c; used.add(c); tracks[i].append(c)
                alive=na
            for i,p in enumerate(start):
                x,y=p; d0=disc(x,y,W,H,g0)
                empt=sum(1 for (nx,ny) in d0 if g0[ny][nx]=='.')
                seen=set()
                for (px,py) in tracks[i]: seen|=disc(px,py,W,H,g0)
                recs.append(dict(map=mp,idle=(empt==0),dist=d[y][x],
                                 newteam=len(seen-teamu),steps=len(tracks[i])))
    if not recs: print("!! nothing",file=sys.stderr); return 1
    n=len(recs)
    idle=[r for r in recs if r['idle']]; busy=[r for r in recs if not r['idle']]
    print(f"=== Requirement I stage 1: the re-open condition, counted ({n} soldiers, starved maps) ===\n")
    def blk(lab,rs):
        if not rs: print(f"  {lab:<28} none"); return
        ds=sorted(r['dist'] for r in rs)
        print(f"  {lab:<28} n={len(rs):>3} ({100*len(rs)/n:>4.1f}%)"
              f"  median dist to unexplored={ds[len(ds)//2]:>3}"
              f"  mean NEW team area in 50t={sum(r['newteam'] for r in rs)/len(rs):>7.1f}")
    blk("IDLE (no empty in vision)",idle)
    blk("busy (work in sight)",busy)
    for thr in (3,6,10):
        near=[r for r in idle if r['dist']<=thr]
        if not near: continue
        dead=[r for r in near if r['newteam']<20]
        print(f"\n  idle AND within {thr:>2} tiles of unexplored ground: {len(near)}/{n}"
              f" = {100*len(near)/n:>4.1f}%   mean new team area={sum(r['newteam'] for r in near)/len(near):>7.1f}")
        print(f"    of those, bringing back <20 tiles (the SLACK): {len(dead)}/{len(near)}"
              f" = {100*len(dead)/len(near):>4.1f}%  -> {100*len(dead)/n:.1f}% of all soldiers")
    return 0
sys.exit(main())

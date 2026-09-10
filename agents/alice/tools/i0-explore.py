#!/usr/bin/env python3
"""Requirement I, stage 0 -- is the own-paint gradient an EXPLORATION signal?

C2 killed the own-paint gradient at 0.95x random, but its registered truth was the
first step of the SHORTEST WALK to the nearest empty tile: a TARGETING criterion.
That refutes aiming and says nothing about spreading.  This tests spreading.

REGISTERED BEFORE THIS RAN:
  question   does a soldier's own-paint fraction at time t predict the NEW area it
             covers over the following 50 turns?
  subset     the STARVED maps only (maze, mit) -- levers must be scored where there
             is room, never pooled with maps whose ruins are already exhausted.
  PASS       top own-paint quartile covers >= 30% LESS new area than the bottom
  KILL       < 10%
  null arm   required, because the starved subset's noise floor is unmeasured.
             Here it is a PERMUTATION null: shuffle the own-paint labels across
             soldiers and recompute the same quartile gap, many times.  That is the
             exact noise floor of this statistic on this sample, not an analogue of
             it.

NEW AREA = union of the soldier's vision discs over t..t+50, MINUS its disc at t.
Tiles it had already seen at t are not new by definition.

TRACKING: frames are one round apart and a robot moves at most one tile, so
identity is recovered by nearest-neighbour matching within Chebyshev distance 1.
Where two soldiers are adjacent a swap is possible -- and harmless here, because
two soldiers one tile apart contribute nearly the same vision union, so a swapped
assignment barely perturbs the quantity being measured.  Soldiers that die or
become unmatchable keep the trajectory they had; their window is recorded so a
short-tracked soldier is not silently compared with a fully-tracked one.
"""
import sys, re, random, statistics

VIS=[(dx,dy) for dx in range(-5,6) for dy in range(-5,6) if dx*dx+dy*dy<=20]
G=set(".#o*aAbBtTnNdDsSmMpP")
T={1:("s",set("aA")),2:("S",set("bB"))}

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

def disc(x,y,W,H,grid):
    s=set()
    for dx,dy in VIS:
        nx,ny=x+dx,y+dy
        if 0<=nx<W and 0<=ny<H and grid[ny][nx]!='#': s.add((nx,ny))
    return s

def main():
    lines=[l.rstrip("\n") for l in sys.stdin]
    bymap={}
    for (mp,rnd,W,H,g) in frames(lines):
        bymap.setdefault(mp,{})[rnd]=(W,H,g)
    recs=[]
    for mp,fr in bymap.items():
        rounds=sorted(fr)
        if len(rounds)<2: continue
        t0=rounds[0]
        W,H,g0=fr[t0]
        for team in (1,2):
            sg,own=T[team]
            start=[(x,y) for y in range(H) for x in range(W) if g0[y][x]==sg]
            tracks={i:[p] for i,p in enumerate(start)}
            alive={i:p for i,p in enumerate(start)}
            for t in rounds[1:]:
                Wn,Hn,gn=fr[t]
                cand=[(x,y) for y in range(Hn) for x in range(Wn) if gn[y][x]==sg]
                used=set();newalive={}
                pairs=[]
                for i,(px,py) in alive.items():
                    for c in cand:
                        d=max(abs(c[0]-px),abs(c[1]-py))
                        if d<=1: pairs.append((d,i,c))
                pairs.sort()
                for d,i,c in pairs:
                    if i in newalive or c in used: continue
                    newalive[i]=c;used.add(c);tracks[i].append(c)
                alive=newalive
            # TEAM union at t: the mechanism cares about area new to the TEAM,
            # not area merely new to one soldier. The registered quantity said
            # "new area it covers" and I operationalised it soldier-relative;
            # both are computed and the registered one is the one that binds.
            teamu=set()
            for (sx,sy) in start: teamu|=disc(sx,sy,W,H,g0)
            for i,p in enumerate(start):
                x,y=p
                d0=disc(x,y,W,H,g0)
                c={'own':0,'tot':0}
                for (nx,ny) in d0:
                    c['tot']+=1
                    if g0[ny][nx] in own: c['own']+=1
                if c['tot']==0: continue
                seen=set()
                for (px,py) in tracks[i]:
                    seen|=disc(px,py,W,H,g0)
                recs.append(dict(map=mp,team=team,
                                 frac=c['own']/c['tot'],
                                 new=len(seen-d0),
                                 newteam=len(seen-teamu),
                                 steps=len(tracks[i])))
    if len(recs)<8:
        print("!! too few tracked soldiers to quartile -- refusing a verdict",file=sys.stderr)
        return 1

    full=[r for r in recs if r['steps']>=len(sorted(bymap[r['map']]))*0.8]
    print(f"=== Requirement I stage 0: {len(recs)} soldiers tracked "
          f"({len(full)} for >=80% of the window) on the STARVED maps ===")
    print("    BARS REGISTERED BEFORE THIS RAN: PASS top quartile >=30% less new area")
    print("    than bottom quartile; KILL <10%. Permutation null.\n")

    def gap(rs):
        rs=sorted(rs,key=lambda r:r['frac'])
        q=max(1,len(rs)//4)
        bot=statistics.mean(r['new'] for r in rs[:q])
        top=statistics.mean(r['new'] for r in rs[-q:])
        return bot,top,(100*(bot-top)/bot if bot else float('nan'))

    for lab,rs in (("all tracked",recs),("tracked >=80% of window",full)):
        if len(rs)<8: continue
        bot,top,g=gap(rs)
        fr=[r['frac'] for r in rs]
        print(f"  {lab:<26} n={len(rs):>4}  own-paint frac {min(fr):.2f}-{max(fr):.2f}"
              f"  new area: bottom-q {bot:>6.1f}  top-q {top:>6.1f}   GAP = {g:+.1f}%")

    rs=full if len(full)>=8 else recs
    def gap2(rss,key):
        rss=sorted(rss,key=lambda r:r['frac']); q=max(1,len(rss)//4)
        b=statistics.mean(r[key] for r in rss[:q]); t=statistics.mean(r[key] for r in rss[-q:])
        return b,t,(100*(b-t)/b if b else float('nan'))
    tb,tt,tg=gap2(rs,'newteam')
    print(f"\n  DIAGNOSTIC, area new to the TEAM (not merely to the soldier):")
    print(f"    bottom-q {tb:>6.1f}   top-q {tt:>6.1f}   gap = {tg:+.1f}%")
    print("    This is the quantity the mechanism would need. It is reported as a")
    print("    diagnostic; the REGISTERED quantity below is the one that binds.")
    bot,top,obs=gap(rs)
    rng=random.Random(20260910)
    perm=[]
    for _ in range(2000):
        vals=[r['new'] for r in rs]; rng.shuffle(vals)
        sh=[dict(frac=r['frac'],new=v) for r,v in zip(rs,vals)]
        perm.append(gap(sh)[2])
    perm.sort()
    lo,hi=perm[int(.025*len(perm))],perm[int(.975*len(perm))]
    pv=sum(1 for v in perm if abs(v)>=abs(obs))/len(perm)
    print(f"\n  PERMUTATION NULL (2000 shuffles): 95% of gaps fall in "
          f"[{lo:+.1f}%, {hi:+.1f}%]   two-sided p = {pv:.3f}")
    print(f"  OBSERVED GAP = {obs:+.1f}%")
    print("  VERDICT: " + ("PASS" if obs>=30 else "KILL" if obs<10 else
                           "BETWEEN -- real but under the bar"))
    if abs(obs) < max(abs(lo),abs(hi)):
        print("  NOTE: the observed gap is INSIDE the null's own 95% band -- this")
        print("  statistic cannot distinguish it from chance on this sample.")
    return 0

sys.exit(main())

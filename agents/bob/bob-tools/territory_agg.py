#!/usr/bin/env python3
"""ITERATION 51: the TERRITORY half of the per-turn paint penalty.

Usage: territory_agg.py <census.tsv (--views)> [--team-substr bob]

ENGINE TARGET (InternalRobot.processEndOfTurn, bytecode-verified):
    mult = (type == MOPPER) ? 2 : 1
    OWN paint     -> 0            (territory term only; crowding is charged separately)
    NEUTRAL       -> -1 * mult
    ENEMY paint   -> -2 * mult

METHOD. Each --views frame gives a units grid (G1) and a units-hidden paint-only
grid (G2) for the SAME round, so the tile colour under every unit is readable.
Units are t/n/d towers and s/m/p mobiles, team1 lower-case, team2 UPPER-CASE;
paint is a/A team1 and b/B team2, '.' unpainted, '#' wall, 'o' ruin, '*' splash
centre.

BIAS, ESTABLISHED BEFORE THE NUMBERS WERE READ AND ONE-SIDED. The paint grid is a
reconstruction: splash footprints are not in the replay schema. The frame-level
coverage check reads recon ABOVE engine by <1% of the map, i.e. it believes more
tiles are painted than there are. Over-counting painted tiles UNDERSTATES the
NEUTRAL class, and NEUTRAL is what the territory penalty is charged on -- so every
number here is a LOWER BOUND on the true cost. The gap distribution is printed so
the bound can be checked rather than trusted.

'*' (splash centre) is counted as UNKNOWN, not as paint: it occludes the tile and
attributing it either way would be a guess.
"""
import sys, collections, re

TOWERS=set('tnd'); MOBILE=set('smp')
COVRE = re.compile(r"T1 recon=(\d+) engine=(\d+) gap=([+-]\d+)\s+T2 recon=(\d+) engine=(\d+) gap=([+-]\d+)")

path=sys.argv[1]
want=None
for i,a in enumerate(sys.argv):
    if a=='--team-substr': want=sys.argv[i+1]

teams={}; units=collections.defaultdict(dict); paints=collections.defaultdict(dict)
order=[]; cur=None; gaps=[]
for line in open(path):
    p=line.rstrip("\n").split("\t")
    if p[0]=='HDR' and len(p)>=4: teams[p[1]]=(p[2],p[3])
    elif p[0]=='ARENA' and len(p)>=3:
        cur=(p[1],int(p[2]))
        if cur not in units: order.append(cur)
    elif p[0]=='COV' and len(p)>=3:
        m=COVRE.search(p[2])
        if m: gaps.append((int(m.group(3)), int(m.group(6))))
    elif p[0]=='G1' and len(p)>=4 and cur: units[cur][int(p[2])]=p[3]
    elif p[0]=='G2' and len(p)>=4 and cur: paints[cur][int(p[2])]=p[3]

st=collections.defaultdict(collections.Counter)
for key in order:
    u=units.get(key); pg=paints.get(key); f=key[0]
    if not u or not pg or f not in teams: continue
    t1,t2=teams[f]
    for y,row in u.items():
        prow=pg.get(y)
        if prow is None or len(prow)!=len(row): continue
        for x,ch in enumerate(row):
            lo=ch.lower()
            if lo not in MOBILE: continue
            upper=ch.isupper(); name=t2 if upper else t1
            myp = 'B' if upper else 'A'                 # my paint letter (case-insensitive)
            tile=prow[x]
            s=st[name]
            s['n']+=1
            if lo=='m': s['moppers']+=1
            if tile=='*': s['unknown']+=1
            elif tile in ('.','o'): s['neutral']+=1; s['costN']+= (2 if lo=='m' else 1)
            elif tile.upper()==myp: s['own']+=1
            elif tile.upper() in ('A','B'): s['enemy']+=1; s['costE']+= (4 if lo=='m' else 2)
            else: s['unknown']+=1

if gaps:
    g1=[a for a,_ in gaps]; g2=[b for _,b in gaps]
    allg=sorted(g1+g2)
    print(f"coverage-gap check over {len(gaps)} frames (recon - engine, per-mille):")
    print(f"  min {allg[0]:+d}  p25 {allg[len(allg)//4]:+d}  median {allg[len(allg)//2]:+d}"
          f"  p75 {allg[3*len(allg)//4]:+d}  max {allg[-1]:+d}   mean {sum(allg)/len(allg):+.1f}")
    print(f"  frames with recon BELOW engine (bias would run the other way): "
          f"{sum(1 for v in allg if v<0)}/{len(allg)}\n")

print(f"{'bot':<14}{'unitObs':>9}{'own%':>8}{'neutral%':>10}{'enemy%':>9}{'unk%':>7}"
      f"{'terrPaint/unit-rnd':>20}")
for name in sorted(st):
    if want and want not in name: continue
    s=st[name]; n=s['n']
    if not n: continue
    cost=(s['costN']+s['costE'])/n
    print(f"{name:<14}{n:>9}{s['own']/n*100:>7.1f}%{s['neutral']/n*100:>9.1f}%"
          f"{s['enemy']/n*100:>8.1f}%{s['unknown']/n*100:>6.1f}%{cost:>20.3f}")
    print(f"{'':<14}{'':>9}   of that cost: neutral {s['costN']/n:.3f}  enemy {s['costE']/n:.3f}"
          f"   (moppers {s['moppers']/n*100:.1f}% of obs, they pay 2x)")

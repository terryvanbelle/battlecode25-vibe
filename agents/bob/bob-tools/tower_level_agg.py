#!/usr/bin/env python3
"""ITERATION 52: FOREGONE paint income -- paint/turn left on the table by towers below L3.

Usage: tower_level_agg.py <tower-level-census.tsv>

ENGINE. PAINT tower paintPerTurn by level = 5 / 10 / 15; tower max HP by level =
1000 / 1500 / 2000 (money & paint), 2000 / 2500 / 3000 (defense). A tower's
UpgradeAction carries the NEW max health, so hp-> names the new level given the
type. Both starting towers are created at LEVEL TWO (V3.0.0), which shows up as an
UPGRADE at round 1 for a tower that has no SPAWN line -- those are seeded here as
alive from round 1 rather than treated as policy upgrades.

PRIMARY = sum over PAINT-tower-rounds of (15 - paintPerTurn), i.e. paint per turn
foregone. SRP's +3S is level-independent and excluded from both sides.

CONFOUND, registered before the run: a tower that dies young cannot be upgraded, so
foregone income partly measures SURVIVAL rather than upgrade policy. Output is split
by whether the tower ever reached L3, and the mean life of those that did not.
"""
import sys, re, collections

SPAWN = re.compile(r"^round (\d+) .*? SPAWN id(\d+)\(T(\d),([A-Z_]+)\)")
UPG   = re.compile(r"^round (\d+) UPGRADE id(\d+)\(T(\d),([A-Z_]+)\) hp->(\d+)")
DIED  = re.compile(r"^round (\d+) DIED id(\d+)\(T(\d),([A-Z_]+)\)")
FTR   = re.compile(r"rounds=(\d+)")
HP2LVL = {"PAINT_TOWER":{1000:1,1500:2,2000:3}, "MONEY_TOWER":{1000:1,1500:2,2000:3},
          "DEFENSE_TOWER":{2000:1,2500:2,3000:3}}
PPT = {1:5, 2:10, 3:15}

teams={}; ev=collections.defaultdict(list); last={}
for line in open(sys.argv[1]):
    p=line.rstrip("\n").split("\t")
    if p[0]=='HDR' and len(p)>=4: teams[p[1]]=(p[2],p[3])
    elif p[0]=='FTR' and len(p)>=3:
        m=FTR.search(p[2])
        if m: last[p[1]]=int(m.group(1))
    elif p[0]=='E' and len(p)>=3: ev[p[1]].append(p[2])

agg=collections.defaultdict(collections.Counter)
lives=collections.defaultdict(list)
for f, lines in ev.items():
    if f not in teams: continue
    t1,t2=teams[f]; end=last.get(f, 2000)
    born={}; ttype={}; tteam={}; upg=collections.defaultdict(list); death={}
    for L in lines:
        m=SPAWN.match(L)
        if m and m.group(4).endswith("TOWER"):
            born[m.group(2)]=int(m.group(1)); ttype[m.group(2)]=m.group(4); tteam[m.group(2)]=m.group(3); continue
        m=UPG.match(L)
        if m:
            i=m.group(2); ttype.setdefault(i,m.group(4)); tteam.setdefault(i,m.group(3))
            upg[i].append((int(m.group(1)), int(m.group(5)))); continue
        m=DIED.match(L)
        if m and m.group(4).endswith("TOWER"):
            i=m.group(2); ttype.setdefault(i,m.group(4)); tteam.setdefault(i,m.group(3))
            death[i]=int(m.group(1))
    for i, ty in ttype.items():
        if ty != "PAINT_TOWER": continue
        name = t1 if tteam[i]=='1' else t2
        b = born.get(i, 1)                     # no SPAWN => starting tower, alive from r1
        d = death.get(i, end)
        if d <= b: continue
        # build level timeline
        lvl = 1
        segs=[]; cur=b
        for (r, hp) in sorted(upg[i]):
            if r < b or r > d: continue
            nl = HP2LVL[ty].get(hp)
            if nl is None: continue
            if r > cur: segs.append((cur, r, lvl))
            lvl = nl; cur = r
        if d > cur: segs.append((cur, d, lvl))
        a=agg[name]
        reached3 = (lvl==3)
        for (s,e,l) in segs:
            rounds = e-s
            a['rounds'] += rounds
            a['income'] += rounds*PPT[l]
            a['foregone'] += rounds*(15-PPT[l])
            a['r%d'%l] += rounds
        a['towers'] += 1
        if reached3: a['reached3'] += 1
        else: lives[name].append(d-b)
    agg[t1]['games_seen']+=0; agg[t2]['games_seen']+=0

games=collections.Counter()
for f in ev:
    if f in teams:
        games[teams[f][0]]+=1; games[teams[f][1]]+=1

print(f"{'bot':<14}{'games':>6}{'paintTw':>9}{'reachL3':>9}{'twRnds/g':>10}"
      f"{'income/g':>10}{'FOREGONE/g':>12}{'%rndsL1':>9}{'%L2':>7}{'%L3':>7}")
for n in sorted(agg):
    a=agg[n]; g=games[n]
    if not g or not a['rounds']: continue
    R=a['rounds']
    print(f"{n:<14}{g:>6}{int(a['towers']):>9}{int(a['reached3']):>9}{R/g:>10.0f}"
          f"{a['income']/g:>10.0f}{a['foregone']/g:>12.0f}"
          f"{a['r1']/R*100:>8.1f}%{a['r2']/R*100:>6.1f}%{a['r3']/R*100:>6.1f}%")
    if lives[n]:
        lv=sorted(lives[n])
        print(f"{'':<14}  towers that never reached L3: {len(lv)}  median life {lv[len(lv)//2]} rounds")

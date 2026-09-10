#!/usr/bin/env python3
"""Does alice LOSE painted ground it has already taken, and does that decide games?

The three games alice led at r300 and lost all show the same shape: alice's coverage
peaks and then falls while carol's rises monotonically. If that shape also appears in
the games alice WINS, it is not the defect. Measured per game, one pass.
"""
import sys, re, statistics
PAT = re.compile(r"(T[12]) \$\d+ cov(\d+)m srp\d+ sold\d+ spl\d+ mop\d+ tw(\d+) twPaint\d+")

def main():
    t1=t2=None; cur=None; g={}
    for ln in open(sys.argv[1]):
        m=re.match(r"=== GameHeader\s+team1=(\S+)\s+team2=(\S+)",ln)
        if m: t1,t2=m.group(1),m.group(2)
        m=re.match(r"=== MatchHeader map=(\S+) ",ln)
        if m: cur=m.group(1); g[cur]={'t1':t1,'t2':t2,'a':[],'c':[],'win':None}
        if cur is None: continue
        w=re.match(r"=== MatchFooter winner=team(\d)",ln)
        if w: g[cur]['win']=w.group(1)
        if "| T1 " not in ln: continue
        rm=re.match(r"round (\d+) \|",ln)
        if not rm: continue
        for mm in PAT.finditer(ln):
            who=g[cur]['t1'] if mm.group(1)=='T1' else g[cur]['t2']
            k='a' if 'alice' in who else 'c'
            g[cur][k].append((int(rm.group(1)), int(mm.group(2))))
    rows=[]
    for mp,v in g.items():
        if not v['a'] or not v['c'] or not v['win']: continue
        aw = (v['win']=='1') == ('alice' in v['t1'])
        ap=max(c for _,c in v['a']); af=v['a'][-1][1]
        cp=max(c for _,c in v['c']); cf=v['c'][-1][1]
        rows.append((mp,aw,ap,af,cp,cf))
    print("=== does alice LOSE ground it has taken? peak coverage vs final, per game ===\n")
    print(f"  {'map':<16}{'won':>5}{'alice peak':>11}{'alice final':>12}{'kept':>7}"
          f"{'carol peak':>11}{'carol final':>12}{'kept':>7}")
    for mp,aw,ap,af,cp,cf in sorted(rows,key=lambda r:(r[1],r[0])):
        print(f"  {mp:<16}{('Y' if aw else 'n'):>5}{ap:>11}{af:>12}{100*af/ap if ap else 0:>6.0f}%"
              f"{cp:>11}{cf:>12}{100*cf/cp if cp else 0:>6.0f}%")
    for lab,sel in (("alice WON",True),("alice LOST",False)):
        s=[r for r in rows if r[1]==sel]
        if not s: continue
        ak=statistics.mean(100*r[3]/r[2] for r in s if r[2])
        ck=statistics.mean(100*r[5]/r[4] for r in s if r[4])
        print(f"\n  {lab:<12} n={len(s):>3}   alice keeps {ak:>5.1f}% of its peak"
              f"   carol keeps {ck:>5.1f}%")
    aw=[100*r[3]/r[2] for r in rows if r[1] and r[2]]
    al=[100*r[3]/r[2] for r in rows if not r[1] and r[2]]
    if aw and al:
        print(f"\n  alice's retention in games it WON {statistics.mean(aw):.1f}%"
              f" vs LOST {statistics.mean(al):.1f}%  -> gap {statistics.mean(aw)-statistics.mean(al):+.1f} pts")
    return 0
sys.exit(main())

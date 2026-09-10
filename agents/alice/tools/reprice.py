#!/usr/bin/env python3
"""Re-price the closed set in the deficit's own regime.

Subpopulation, FROZEN before computing (commit 83029b3): alice leads on towers at
r300 AND alice's coverage at r300 is below carol's -- both read at r300, before any
outcome. A mechanism's ceiling is set by its binding constraint, so the re-price
measures those constraints inside the subpopulation against the rest.
"""
import sys, re, statistics
PAT = re.compile(r"(T[12]) \$(\d+) cov(\d+)m srp\d+ sold(\d+) spl(\d+) mop(\d+) tw(\d+) twPaint(\d+) "
                 r"acts\[p(\d+) u\d+ a\d+ s\d+ m\d+\] \+sold(\d+) \+mop(\d+) \+spl(\d+)")

def main():
    t1=t2=None; cur=None; g={}
    for ln in open(sys.argv[1]):
        m=re.match(r"=== GameHeader\s+team1=(\S+)\s+team2=(\S+)",ln)
        if m: t1,t2=m.group(1),m.group(2)
        m=re.match(r"=== MatchHeader map=(\S+) ",ln)
        if m: cur=m.group(1); g[cur]={'t1':t1,'t2':t2,'rows':[],'win':None}
        if cur is None: continue
        w=re.match(r"=== MatchFooter winner=team(\d)",ln)
        if w: g[cur]['win']=w.group(1)
        if "| T1 " not in ln: continue
        rm=re.match(r"round (\d+) \|",ln)
        if not rm: continue
        d={}
        for mm in PAT.finditer(ln):
            f=mm.groups(); who=g[cur]['t1'] if f[0]=='T1' else g[cur]['t2']
            k='a' if 'alice' in who else 'c'
            d[k]=dict(money=int(f[1]),cov=int(f[2]),sold=int(f[3]),spl=int(f[4]),
                      mop=int(f[5]),tw=int(f[6]),twp=int(f[7]),p=int(f[8]),
                      ss=int(f[9]),sm=int(f[10]),sp=int(f[11]))
        if len(d)==2: g[cur]['rows'].append((int(rm.group(1)),d))
    sub=[]; rest=[]
    for mp,v in g.items():
        r300=[d for r,d in v['rows'] if r==300]
        if not r300 or not v['win']: continue
        d=r300[0]
        qualifies = d['a']['tw'] > d['c']['tw'] and d['a']['cov'] < d['c']['cov']
        (sub if qualifies else rest).append((mp,v))
    print(f"=== subpopulation (frozen def): leads on towers at r300 AND behind on coverage at r300 ===")
    print(f"    qualifying {len(sub)} of {len(sub)+len(rest)} games: {', '.join(m for m,_ in sub)}\n")
    def stats(games,lab):
        if not games: print(f"  {lab}: empty"); return None
        pt=[]; ch=[]; pu=[]; ms=[]; won=0
        for mp,v in games:
            aw=(v['win']=='1')==('alice' in v['t1']); won+=aw
            tp=0; tn=0; P=0; S=0; M=0; SP=0
            for r,d in v['rows']:
                a=d['a']
                if a['tw']: pt.append(a['twp']/a['tw']); ch.append(a['money'])
                P+=a['p']; S+=a['ss']; M+=a['sm']; SP+=a['sp']
            if S+M+SP: pu.append(P/(S+M+SP)); ms.append(M/(S+M+SP))
        print(f"  {lab:<26} n={len(games):>2}  alice won {won}/{len(games)}")
        print(f"  {'':<26} paint/tower mean {statistics.mean(pt):>6.1f}"
              f"   >=300 {100*sum(1 for x in pt if x>=300)/len(pt):>5.1f}%"
              f"   >=200 {100*sum(1 for x in pt if x>=200)/len(pt):>5.1f}%")
        print(f"  {'':<26} paint actions per unit {statistics.mean(pu):>6.2f}"
              f"   mopper share {100*statistics.mean(ms):>5.1f}%"
              f"   mean chips {statistics.mean(ch):>7.0f}")
        return dict(p300=100*sum(1 for x in pt if x>=300)/len(pt),
                    p200=100*sum(1 for x in pt if x>=200)/len(pt),
                    pu=statistics.mean(pu), ms=statistics.mean(ms))
    a=stats(sub,"SUBPOP (the deficit)"); print()
    b=stats(rest,"the rest"); print()
    if a and b:
        print("  === re-price: is any binding constraint LOOSER in the deficit's regime? ===")
        for lab,x,y,bar in (("K8: paint/tower >=300",a['p300'],b['p300'],"needs 2x looser"),
                            ("soldier affordability >=200",a['p200'],b['p200'],""),
                            ("per-unit paint actions",a['pu'],b['pu'],""),
                            ("mopper share",100*a['ms'],100*b['ms'],"")):
            r = x/y if y else float('inf')
            print(f"    {lab:<30} subpop {x:>6.1f}   rest {y:>6.1f}   ratio {r:>5.2f}x  {bar}")
    return 0
sys.exit(main())

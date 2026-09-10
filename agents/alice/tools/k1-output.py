#!/usr/bin/env python3
"""K1 -- decomposing PER-TOWER OUTPUT, the term that actually carries alice's loss.

My own falsifier-backed decomposition says production = tower ratio / per-tower
output ratio = 1.12 / 2.03. Alice WINS the tower race and loses entirely on output
per tower. Checked for the ratio trap first: if totals were equal, holding 1.12x
towers would put per-tower output at 0.893 by arithmetic alone; observed is 0.492.
The denominator explains 0.107 of a 0.508 shortfall, so ~79% of it is real --
ALICE PRODUCES ~45% LESS PAINTED GROUND IN TOTAL WHILE HOLDING 12% MORE TOWERS.

So the quantity to decompose is total production, and its identity is:

    paint actions = towers x (spawns per tower) x (actions per unit)

Every term is in the replay aggregates. Sinks that steal from the last term are
there too: `died`, `starved`, `xfer`.

REGISTERED BEFORE THIS RAN: continue if any single sink accounts for >=25% of the
2.03x gap; KILL the whole "output" framing if no sink exceeds 10% and the gap is
diffuse.

Measured on games alice PLAYED against carol -- what an opponent achieves is
visible in the replay; how it achieves it is not mine to read, and no carol source
is opened here.
"""
import sys, re

PAT = re.compile(r"(T[12]) \$(\d+) cov(\d+)m srp(\d+) sold(\d+) spl(\d+) mop(\d+) tw(\d+) "
                 r"twPaint(\d+) acts\[p(\d+) u(\d+) a(\d+) s(\d+) m(\d+)\] "
                 r"\+sold(\d+) \+mop(\d+) \+spl(\d+) died(\d+) xfer(\d+) starved(\d+)")

def main():
    games={}; cur=None; t1=t2=None
    for ln in sys.stdin:
        m=re.match(r"=== GameHeader\s+team1=(\S+)\s+team2=(\S+)",ln)
        if m:
            t1,t2=m.group(1),m.group(2); cur=None
        m=re.match(r"=== MatchHeader map=(\S+) ",ln)
        if m:
            cur=m.group(1); games[cur]={'t1':t1,'t2':t2,'rows':[]}
        if "| T1 " not in ln or cur is None: continue
        rm=re.match(r"round (\d+) \|",ln)
        if not rm: continue
        rnd=int(rm.group(1)); d={}
        for g in PAT.finditer(ln):
            f=g.groups(); d[f[0]]=dict(money=int(f[1]),cov=int(f[2]),
                sold=int(f[4]),spl=int(f[5]),mop=int(f[6]),tw=int(f[7]),
                twp=int(f[8]),p=int(f[9]),spawn=int(f[14])+int(f[15])+int(f[16]),
                died=int(f[17]),xfer=int(f[18]),starved=int(f[19]))
        if len(d)==2: games[cur]['rows'].append((rnd,d))
    if not games: print("!! nothing parsed",file=sys.stderr); return 1

    tot={'alice':{},'carol':{}}
    for k in tot: tot[k]={'p':0,'spawn':0,'died':0,'starved':0,'xfer':0,
                          'twsum':0,'n':0,'cov':0,'unitsum':0}
    ngames=0
    for mp,g in games.items():
        if not g['rows']: continue
        who={'T1':g['t1'],'T2':g['t2']}
        if not all(('alice' in v or 'carol' in v) for v in who.values()): continue
        ngames+=1
        for rnd,d in g['rows']:
            for side in ('T1','T2'):
                nm='alice' if 'alice' in who[side] else 'carol'
                r=d[side]; t=tot[nm]
                t['p']+=r['p']; t['spawn']+=r['spawn']; t['died']+=r['died']
                t['starved']+=r['starved']; t['xfer']+=r['xfer']
                t['twsum']+=r['tw']; t['unitsum']+=r['sold']+r['spl']+r['mop']
                t['n']+=1; t['cov']=max(t['cov'],0)
        # end-of-game coverage
        rnd,d=g['rows'][-1]
        for side in ('T1','T2'):
            nm='alice' if 'alice' in who[side] else 'carol'
            tot[nm]['cov']+=d[side]['cov']

    print(f"=== K1: production decomposition, {ngames} alice-vs-carol tournament games ===")
    print("    BAR REGISTERED BEFORE THIS RAN: continue if a single sink is >=25% of")
    print("    the 2.03x gap; KILL the output framing if none exceeds 10%.\n")
    a,c=tot['alice'],tot['carol']
    def row(lab,fa,fc,fmt="{:>10.2f}"):
        rat=fa/fc if fc else float('nan')
        print(f"  {lab:<34}"+fmt.format(fa)+fmt.format(fc)+f"   alice/carol = {rat:>5.2f}x")
    print(f"  {'quantity':<34}{'alice':>10}{'carol':>10}")
    row("total paint actions",a['p'],c['p'])
    row("mean towers alive",a['twsum']/a['n'],c['twsum']/c['n'])
    row("total units spawned",a['spawn'],c['spawn'])
    row("mean units alive",a['unitsum']/a['n'],c['unitsum']/c['n'])
    row("end coverage (per mille, summed)",a['cov'],c['cov'])
    print()
    row("PAINT ACTIONS PER TOWER-ROUND",a['p']/a['twsum'],c['p']/c['twsum'],"{:>10.3f}")
    row("spawns per tower-round",a['spawn']/a['twsum'],c['spawn']/c['twsum'],"{:>10.4f}")
    row("paint actions per UNIT-round",a['p']/a['unitsum'],c['p']/c['unitsum'],"{:>10.3f}")
    print()
    print("  SINKS (units lost, per unit spawned):")
    row("died / spawned",a['died']/max(a['spawn'],1),c['died']/max(c['spawn'],1),"{:>10.3f}")
    row("starved / spawned",a['starved']/max(a['spawn'],1),c['starved']/max(c['spawn'],1),"{:>10.3f}")
    row("paint transfers / spawned",a['xfer']/max(a['spawn'],1),c['xfer']/max(c['spawn'],1),"{:>10.3f}")
    return 0
sys.exit(main())

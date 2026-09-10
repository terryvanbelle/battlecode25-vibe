#!/usr/bin/env python3
"""Which budget binds: the BUILD budget or the ACTION budget?

My production ranking is denominated in SPAWN paint -- tiles produced per unit of
paint spent BUILDING the unit. That is the right metric for a build decision under a
build budget. But total output is not bounded by the build budget: a unit, once
built, paints by spending paint AGAIN, and the tiles come out of that second budget.

If action paint binds, the ranking is correct about which unit to build and CANNOT
raise total output, because the quantity it optimises is not the quantity that binds.

Signature of a paint-bound economy: more units, each doing proportionally less, with
total roughly flat -- and starvation rising.
"""
import sys, re
PAT = re.compile(r"T1 \$\d+ cov\d+m srp\d+ sold\d+ spl\d+ mop\d+ tw(\d+) twPaint(\d+) "
                 r"acts\[p(\d+) u\d+ a\d+ s\d+ m\d+\] \+sold(\d+) \+mop(\d+) \+spl(\d+) "
                 r"died(\d+) xfer\d+ starved(\d+)")

def main():
    bot=None; acc={}
    for ln in open(sys.argv[1]):
        m=re.match(r"=== GameHeader\s+team1=(\S+)",ln)
        if m: bot=m.group(1)
        if "| T1 " not in ln: continue
        g=PAT.search(ln)
        if not g: continue
        tw,twp,p,ss,sm,sp,died,starv=[int(x) for x in g.groups()]
        d=acc.setdefault(bot,{k:0 for k in ('tw','twp','p','spawn','died','starv','n')})
        d['tw']+=tw; d['twp']+=twp; d['p']+=p; d['spawn']+=ss+sm+sp
        d['died']+=died; d['starv']+=starv; d['n']+=1
    print("=== WHICH BUDGET BINDS? build paint, or action paint? ===\n")
    print(f"  {'bot':<14}{'spawns':>8}{'paint acts':>12}{'acts/UNIT':>11}"
          f"{'starved/spawn':>15}{'died/spawn':>12}{'tower paint/frame':>19}")
    for b in sorted(acc):
        d=acc[b]; s=max(d['spawn'],1)
        print(f"  {b:<14}{d['spawn']:>8}{d['p']:>12}{d['p']/s:>11.2f}"
              f"{d['starv']/s:>15.3f}{d['died']/s:>12.3f}{d['twp']/d['n']:>19.1f}")
    ks=sorted(acc)
    if len(ks)==2:
        a,c=acc[ks[0]],acc[ks[1]]
        if 'ctl' in ks[0]: a,c=c,a
        sa=max(a['spawn'],1); sc=max(c['spawn'],1)
        print(f"\n  units          {a['spawn']/sc/(sa/sc):.2f}      arm {a['spawn']} v ctl {c['spawn']}"
              f"   = {a['spawn']/sc:>5.2f}x")
        print(f"  output PER UNIT               arm {a['p']/sa:>6.2f} v ctl {c['p']/sc:>6.2f}"
              f"   = {(a['p']/sa)/(c['p']/sc):>5.2f}x")
        print(f"  TOTAL output                  arm {a['p']:>6} v ctl {c['p']:>6}"
              f"   = {a['p']/c['p']:>5.2f}x")
        print(f"  starvation rate               arm {a['starv']/sa:>6.3f} v ctl {c['starv']/sc:>6.3f}"
              f"   = {(a['starv']/sa)/(c['starv']/sc) if c['starv'] else 0:>5.2f}x")
        print()
        dil = (a['p']/sa)/(c['p']/sc)
        print("  VERDICT: " + ("PAINT-BOUND -- more units each doing proportionally less"
                               if dil < 0.85 else
                               "NOT dilution -- per-unit output held up"))
    return 0
sys.exit(main())

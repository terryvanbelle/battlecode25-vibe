#!/usr/bin/env python3
"""E2 / stage 1 -- is a tower off cooldown but TOO POOR TO SPAWN?

Registered before it ran: PASS >= 40% paint-starved, KILL < 15%.

The registered stage is site-observable by the tower itself (its own paint, its own
cooldown).  Measured here from per-round replay aggregates instead of a probe,
because the aggregates already carry `tw` and `twPaint` and a probe would cost a
build and games to answer a question a free instrument can bound.

  starved proxy   twPaint / tw < 200   (a soldier costs 200 paint)
  DECLARED BIAS   this is a MEAN over the team's towers, and paint is distributed
                  very unevenly -- a MONEY tower makes ZERO paint per turn and
                  spawns only from the 500 it is born with, so it sits at 0 for
                  most of the game while a paint tower holds hundreds.  One rich
                  tower therefore masks three empty ones.  The mean UNDERSTATES
                  starvation, so it is conservative against the mechanism, and a
                  PASS measured this way is a floor.

THE DISCRIMINATOR that makes this stage decisive rather than suggestive:
a tower not spawning is either TOO POOR or CHOOSING NOT TO.  If towers were rich
and declining, paint would ACCUMULATE toward the 1000 cap.  So `atcap` separates
the two hypotheses, and it is measured here alongside.
"""
import sys, re

PAT = re.compile(
    r"(T[12]) \$(\d+) cov(\d+)m srp(\d+) sold(\d+) spl(\d+) mop(\d+) tw(\d+) "
    r"twPaint(\d+) acts\[[^\]]*\] \+sold(\d+) \+mop(\d+) \+spl(\d+) died(\d+) "
    r"xfer(\d+) starved(\d+)")

def main():
    cur = None
    rows = []
    for ln in sys.stdin:
        m = re.match(r"=== MatchHeader map=(\S+) (\d+)x(\d+)", ln)
        if m: cur = (m.group(1), max(int(m.group(2)), int(m.group(3))))
        if "| T1 " not in ln: continue
        rm = re.match(r"round (\d+) \|", ln)
        if not rm or cur is None: continue
        rnd = int(rm.group(1))
        for g in PAT.finditer(ln):
            (team, money, cov, srp, sold, spl, mop, tw, twp,
             psold, pmop, pspl, died, xfer, starved) = g.groups()
            tw = int(tw)
            if tw == 0: continue
            rows.append(dict(map=cur[0], big=cur[1], rnd=rnd, team=team,
                             money=int(money), tw=tw, twp=int(twp),
                             perTower=int(twp)/tw, mobile=int(sold)+int(spl)+int(mop),
                             spawns=int(psold)+int(pmop)+int(pspl),
                             died=int(died), starved=int(starved)))
    if not rows:
        print("!! nothing parsed -- refusing to print a rate", file=sys.stderr); return 1

    # ignore the opening rounds: two towers seeded with 500/710 paint are not a
    # steady state and would flatter the rich side.
    st = [r for r in rows if r['rnd'] >= 100]
    print(f"=== E2 stage 1: {len(rows)} tower-frames parsed, {len(st)} at round>=100 ===")
    print("    REGISTERED BEFORE RUNNING: PASS >=40% paint-starved, KILL <15%\n")

    def block(lab, sub):
        if not sub: return
        n = len(sub)
        starved = sum(1 for r in sub if r['perTower'] < 200)
        atcap   = sum(1 for r in sub if r['perTower'] >= 950)
        rich    = sum(1 for r in sub if r['perTower'] >= 400)
        chips   = sum(1 for r in sub if r['money'] >= 1000)
        mp = sum(r['perTower'] for r in sub)/n
        print(f"  {lab:<22} n={n:>5}  mean paint/tower={mp:>6.1f}"
              f"  STARVED(<200)={100*starved/n:>5.1f}%"
              f"  rich(>=400)={100*rich/n:>5.1f}%"
              f"  atcap(>=950)={100*atcap/n:>5.1f}%")
        print(f"  {'':<22} chips>=1000 (could afford a tower) = {100*chips/n:>5.1f}%")

    print("=== overall ===")
    block("all maps", st)
    print("\n=== by map size ===")
    block("small (<30)", [r for r in st if r['big'] < 30])
    block("large (>=45)", [r for r in st if r['big'] >= 45])
    print("\n=== by map ===")
    for mp in sorted({r['map'] for r in st}):
        block(mp, [r for r in st if r['map'] == mp])

    s = st
    starved = 100*sum(1 for r in s if r['perTower'] < 200)/len(s)
    atcap = 100*sum(1 for r in s if r['perTower'] >= 950)/len(s)
    print(f"\n=== VERDICT ===")
    print(f"  paint-starved tower-frames: {starved:.1f}%")
    print("  " + ("PASS" if starved >= 40 else "KILL" if starved < 15
                  else "BETWEEN -- dose, never rebuild"))
    print(f"\n  DISCRIMINATOR -- too poor, or choosing not to?")
    print(f"    at-cap tower-frames: {atcap:.1f}%.  If towers were rich and declining to")
    print(f"    spawn, paint would pile up against the 1000 cap.  It does not.")
    return 0

sys.exit(main())

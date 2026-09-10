#!/usr/bin/env python3
"""K8's fixed point: is the splasher rate gate-limited, or limited by something the
gate cannot touch?

The gate self-limits (it reads the chips it spends), so the quantity that decides
the direction is neither the static reachability (21x) nor the realised 2.22x, but
the EQUILIBRIUM rate a given gate setting can sustain.

But a splasher costs TWO resources: 400 chips AND 300 PAINT, from the tower's own
stash. The gate tests only the chips. So before modelling the chip fixed point, ask
which resource binds -- because if paint binds, no chip-gate setting reaches any
rate at all, and the direction closes on magnitude rather than on dose.
"""
import sys, re

PAT = re.compile(r"(T[12]) \$(\d+) cov\d+m srp\d+ sold\d+ spl\d+ mop\d+ tw(\d+) twPaint(\d+)")

def main():
    t1 = t2 = None; rows = []
    for ln in open(sys.argv[1]):
        m = re.match(r"=== GameHeader\s+team1=(\S+)\s+team2=(\S+)", ln)
        if m: t1, t2 = m.group(1), m.group(2)
        if "| T1 " not in ln: continue
        rm = re.match(r"round (\d+) \|", ln)
        if not rm: continue
        for g in PAT.finditer(ln):
            who = t1 if g.group(1) == 'T1' else t2
            if 'alice' not in who: continue
            tw = int(g.group(3))
            if tw: rows.append((int(rm.group(1)), int(g.group(2)), int(g.group(4))/tw))
    print("=== which resource actually gates a splasher? ===")
    print("    a splasher costs 400 CHIPS (team) AND 300 PAINT (the tower's own stash).")
    print("    the K8 gate tests only the chips.\n")
    print(f"  {'band':<16}{'frames':>8}{'chips>=1850':>13}{'PAINT/tower>=300':>19}"
          f"{'>=200 (soldier)':>18}{'>=100 (mopper)':>17}")
    for lo, hi, lab in ((1,300,"DECISIVE 1-300"),(300,600,"300-600"),
                        (600,1200,"600-1200"),(1200,9999,"1200+")):
        s = [(c,p) for r,c,p in rows if lo <= r < hi]
        if not s: continue
        n = len(s)
        print(f"  {lab:<16}{n:>8}"
              f"{100*sum(1 for c,_ in s if c>=1850)/n:>12.1f}%"
              f"{100*sum(1 for _,p in s if p>=300)/n:>18.1f}%"
              f"{100*sum(1 for _,p in s if p>=200)/n:>17.1f}%"
              f"{100*sum(1 for _,p in s if p>=100)/n:>16.1f}%")
    e = [(c,p) for r,c,p in rows if r < 300]
    n = len(e)
    ch = sum(1 for c,_ in e if c >= 1850)/n
    pa = sum(1 for _,p in e if p >= 300)/n
    print(f"\n  In the decisive window: the CHIP condition is satisfiable on {100*ch:.1f}% of frames")
    print(f"  and the PAINT condition on {100*pa:.1f}%.")
    print(f"  JOINT ceiling (independent) = {100*ch*pa:.1f}% -- and the old gate already")
    print(f"  reached 2.8% on chips alone.")
    print()
    print(f"  => the binding resource is {'PAINT' if pa < ch else 'CHIPS'}, and the gate tests the other one.")
    print(f"  No setting of a CHIP gate can raise the rate above the PAINT ceiling of {100*pa:.1f}%.")
    return 0

sys.exit(main())

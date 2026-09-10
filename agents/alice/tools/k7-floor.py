#!/usr/bin/env python3
"""K7 pre-check: the NOISE FLOOR of "realised refills per unit".

I revised a registered prediction downward before the run (>=3x -> >=1.7x) with
three of the four protections in place: before the data, both numbers recorded, and
the new figure derived rather than chosen. The fourth was missing -- the revised bar
had never been checked against a floor. >=1.7x with a <1.5x falsifier are a hand's
breadth apart on an unmeasured scale.

THE RIGHT FLOOR, and why a literal placebo cannot give it: the engine is
deterministic, so a policy-identical null playing the same opponent on the same map
reproduces the game EXACTLY -- floor zero, and uninformative. The noise in my 1.15x
came from somewhere else: arm and control play DIFFERENT games because their
trajectories diverge, so the estimate inherits game-to-game variation in the refill
rate. The floor for a 3-map comparison is therefore the MAP-TO-MAP DISPERSION of
refills-per-unit under a FIXED policy, divided by sqrt(n).

Measured on 21 alice-vs-carol tournament games from run 20260910-0100, which
predates K3 -- so it is one fixed policy across 21 draws, exactly what is needed.
"""
import sys, re, math, statistics

PAT = re.compile(r"(T[12]) \$\d+ cov\d+m srp\d+ sold\d+ spl\d+ mop\d+ tw\d+ twPaint\d+ "
                 r"acts\[p(\d+) u\d+ a\d+ s\d+ m\d+\] \+sold(\d+) \+mop(\d+) \+spl(\d+) "
                 r"died\d+ xfer(\d+) starved\d+")

def main():
    games = {}; t1 = t2 = None; cur = None
    for ln in sys.stdin:
        m = re.match(r"=== GameHeader\s+team1=(\S+)\s+team2=(\S+)", ln)
        if m: t1, t2 = m.group(1), m.group(2); cur = None
        m = re.match(r"=== MatchHeader map=(\S+) ", ln)
        if m: cur = m.group(1); games[cur] = {'t1': t1, 't2': t2, 'x': 0, 's': 0, 'p': 0}
        if "| T1 " not in ln or cur is None: continue
        for g in PAT.finditer(ln):
            side, p, ps, pm, psp, x = g.groups()
            who = games[cur]['t1'] if side == 'T1' else games[cur]['t2']
            if 'alice' not in who: continue
            games[cur]['x'] += int(x); games[cur]['s'] += int(ps)+int(pm)+int(psp)
            games[cur]['p'] += int(p)
    rates = [(mp, g['x']/g['s']) for mp, g in games.items() if g['s'] > 0]
    if len(rates) < 5:
        print("!! too few games for a floor", file=sys.stderr); return 1
    vals = [r for _, r in rates]
    mu = statistics.mean(vals); sd = statistics.stdev(vals)
    print(f"=== K7 pre-check: noise floor of refills-per-unit, one FIXED policy ===")
    print(f"    {len(vals)} games, run 20260910-0100 (predates K3)\n")
    print(f"  mean refills/unit  = {mu:.4f}")
    print(f"  sd across games    = {sd:.4f}   ({100*sd/mu:.1f}% of the mean)")
    print(f"  range              = {min(vals):.4f} .. {max(vals):.4f}"
          f"   ({max(vals)/min(vals) if min(vals) else float('inf'):.2f}x)")
    for n in (3, 25):
        sem = sd/math.sqrt(n)
        # a RATIO of two independent n-game means has ~sqrt(2)x that relative error
        rel = math.sqrt(2)*sem/mu
        print(f"\n  for an n={n} arm-vs-control comparison:")
        print(f"    sem of one mean          = {sem:.4f}  ({100*sem/mu:.1f}%)")
        print(f"    1 sd on the RATIO        = {rel:.3f}  -> a null ratio of 1.00 +/- {rel:.2f}")
        print(f"    95% band for a TRUE 1.0  = {1-1.96*rel:.2f} .. {1+1.96*rel:.2f}")
        for lab, v in (("K3 realised 1.15x", 1.15), ("revised bar 1.70x", 1.70),
                       ("falsifier 1.50x", 1.50)):
            z = (v-1.0)/rel
            print(f"    {lab:<20} = {z:>5.2f} sd above a null of 1.0"
                  + ("   <- INSIDE the floor" if abs(z) < 1.96 else ""))
    return 0

sys.exit(main())

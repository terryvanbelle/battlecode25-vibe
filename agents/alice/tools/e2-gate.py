#!/usr/bin/env python3
"""Apply iteration E2's PRE-REGISTERED gate to a gauntlet run. Nothing else.

    tools/e2-gate.py gauntlet/<run>/results.txt

The run is BOT=alice_e2ctl against OPPONENTS="alice_e2 alice_e2null", so every
RESULT line is scored from the CONTROL's side and the arm's net is its negation.
`collate.sh` defines the encoding and this matches it exactly: the bot won the
game iff winner_side == bot_side.

REGISTERED BEFORE THE SCREEN RAN, and applied here verbatim:

  net      = arm wins - 25          (25 maps, both sides, 50 games)
  ACCEPT   net >= +4                 -- and no other outcome is an accept
  VOID     |net_null| >= 4           -- the null arm is the control against
                                        itself on the IDENTICAL map sample, so
                                        its true net is 0. If the instrument
                                        cannot hold zero to within the bar, the
                                        bar cannot resolve the effect and this
                                        is VOID, not a reject.
  REJECT   everything else

VOID is checked FIRST. A reject read off an instrument that cannot resolve the
bar is not a reject, and deciding the order after seeing the numbers is how a
void quietly becomes whichever verdict the author preferred.
"""
import sys, collections

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "results.txt"
    # arm/null package names are arguments so the same gate serves later
    # iterations unchanged -- the thresholds and the branch ORDER are the
    # part that must not be re-typed per experiment.
    ARM  = sys.argv[2] if len(sys.argv) > 2 else "alice_e2"
    NULL = sys.argv[3] if len(sys.argv) > 3 else "alice_e2null"
    # BAR is an argument so a census (+12 on 75 maps) uses the SAME tool and
    # the same branch order as a screen (+4 on 25). Re-typing a gate per
    # experiment is how a threshold drifts.
    BAR  = float(sys.argv[4]) if len(sys.argv) > 4 else 4.0
    games = []
    complete = False
    for ln in open(path):
        if ln.startswith("GAUNTLET-COMPLETE"): complete = True
        if not ln.startswith("RESULT "): continue
        p = ln.split()
        if len(p) < 6: continue
        _, opp, mp, side, win, rnd = p[0], p[1], p[2], p[3], p[4], p[5]
        games.append(dict(opp=opp, map=mp, side=side, win=win,
                          rnd=int(rnd) if rnd.isdigit() else -1,
                          ctl_won=(win == side)))
    if not games:
        print("!! no RESULT lines -- refusing to print a verdict"); return 1

    print(f"run complete marker: {'YES' if complete else 'NO -- PARTIAL, verdict withheld'}")
    by = collections.defaultdict(list)
    for g in games: by[g['opp']].append(g)

    nets = {}
    for opp in sorted(by):
        gs = by[opp]
        ctlw = sum(1 for g in gs if g['ctl_won'])
        oppw = len(gs) - ctlw
        maps = len({g['map'] for g in gs})
        net = oppw - maps          # opponent's net, in the registered units
        nets[opp] = (net, oppw, ctlw, len(gs), maps)
        print(f"  {opp:<16} games={len(gs):>3} maps={maps:>3}"
              f"  {opp} wins={oppw:>3}  ctl wins={ctlw:>3}"
              f"  net({opp}) = {oppw} - {maps} = {net:+d}")

    if not complete:
        print("\nPARTIAL RUN -- no verdict. The gate is applied only to a finished screen.")
        return 0

    arm = nets.get(ARM); null = nets.get(NULL)
    if arm is None:
        print("\n!! the ARM is missing -- cannot apply the gate"); return 1
    if null is None:
        # A census is run arm-vs-control only; its bar is derived from a floor
        # measured earlier (sd_net_swept = 5.29), so the VOID branch has nothing
        # to evaluate. Say so LOUDLY rather than letting a protection vanish
        # quietly: a missing null is a weaker run, not an equivalent one.
        print("\n=== NO NULL ARM IN THIS RUN ===")
        print("  The VOID branch cannot be evaluated. This run's bar rests on the")
        print("  PREVIOUSLY measured floor sd_net_swept = 5.29, not on a floor")
        print("  measured on this draw. That is weaker, and it is stated, not hidden.")
        print(f"\n=== GATE ===\n  net_arm = {arm[0]:+d}   bar = {BAR:+.0f}")
        print("  VERDICT: " + ("**PASS**" if arm[0] >= BAR else "**FAIL**"))
        return 0

    print(f"\n=== GATE, as registered ===")
    print(f"  net_null = {null[0]:+d}   (true value is 0: control vs itself)")
    if abs(null[0]) >= BAR:
        print(f"  |net_null| = {abs(null[0])} >= 4  ->  **VOID**")
        print("  The instrument cannot hold zero to within the bar on this map sample,")
        print("  so it cannot resolve a +4 effect. This is NOT a reject: the mechanism")
        print("  was not tested. Re-run on a fresh sample or widen the screen.")
        print(f"  (for the record, net_arm = {arm[0]:+d}, but it is not interpretable here)")
        return 0
    print(f"  |net_null| = {abs(null[0])} < 4  ->  instrument resolves the bar; gate applies")
    print(f"  net_arm  = {arm[0]:+d}   bar = {BAR:+.0f}")
    print("  VERDICT: " + ("**ACCEPT**" if arm[0] >= BAR else "**REJECT**"))
    if arm[0] < BAR:
        print("  A rejected iteration is a delivered result: the mechanism fired")
        print("  (manipulation check passed) and did not clear the bar.")

    print("\n=== per-map table (arm vs control) -- read it even on a reject ===")
    print(f"  {'map':<20}{'arm wins':>10}{'of':>4}")
    per = collections.defaultdict(lambda: [0, 0])
    for g in by[ARM]:
        per[g['map']][1] += 1
        if not g['ctl_won']: per[g['map']][0] += 1
    for mp in sorted(per, key=lambda m: (-per[m][0], m)):
        w, n = per[mp]
        flag = "  <- swept" if w == n and n > 1 else ("  <- lost both" if w == 0 and n > 1 else "")
        print(f"  {mp:<20}{w:>10}{n:>4}{flag}")
    sw = sum(1 for m in per if per[m][0] == per[m][1] and per[m][1] > 1)
    sl = sum(1 for m in per if per[m][0] == 0 and per[m][1] > 1)
    print(f"  maps swept by arm: {sw}   swept by control: {sl}   SW-SL = {sw-sl:+d}")
    return 0

sys.exit(main())

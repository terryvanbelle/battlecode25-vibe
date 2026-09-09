#!/usr/bin/env python3
"""Iteration 40 secondary: split a dose-sweep run's arms by MAP AREA, and read the
round-30 splasher count that the mechanism is supposed to move.

    bob-tools/sa_eval.py <early-census-file> <results.csv> [--thresh 1000]

REGISTERED UNDERPOWERED, IN ADVANCE. A 25-map uniform draw holds only ~8 maps below
1000 tiles, so the small stratum is ~16 games per arm. This is a DIRECTION CHECK on a
mechanism whose sign was pre-committed, never a second accept gate -- the gate is the
uniform head-to-head in eval_arms.py. Narrowing the gate to small maps would be the
hand-picked-map-list overfitting surface AGENT.md forbids.

SIGN CONVENTION, stated because this lineage has been bitten by it twice: the census
prints bob_iter20 (the BOT) as one team and the ARM as the other, and which is T1
depends on the side. The arm is T2 in botA games and T1 in botB games.
"""
import csv, re, sys, statistics as st
from collections import defaultdict

def main():
    census, results = sys.argv[1], sys.argv[2]
    thresh = 1000
    if "--thresh" in sys.argv:
        thresh = int(sys.argv[sys.argv.index("--thresh") + 1])
    feat = {r["map"]: r for r in csv.DictReader(open("bob-tools/srp-sites.csv"))
            if r.get("W") and r["W"].isdigit()}
    area = {m: int(f["W"]) * int(f["H"]) for m, f in feat.items()}

    # win/loss per (arm, map, side) from the ARM's perspective: arm wins where bot loses
    won = {}
    for row in csv.DictReader(open(results)):
        won[(row["opponent"], row["map"], row["bot_side"])] = (row["bot_result"] == "loss")

    per = defaultdict(lambda: defaultdict(list))
    for line in open(census):
        p = [x.strip() for x in line.strip().split("|")]
        if len(p) < 9:
            continue
        m = re.match(r"(bob_sa\d)__(.+?)__bot([AB])\.bc25", p[0])
        if not m or m.group(2) not in area:
            continue
        arm, mp, side = m.group(1), m.group(2), m.group(3)
        s1, s2 = p[-2], p[-1]
        if not s1.startswith("T1") or not s2.startswith("T2"):
            continue
        armseg, botseg = (s2, s1) if side == "A" else (s1, s2)
        def g(seg, key):
            mm = re.search(key + r"(\d+)", seg)
            return int(mm.group(1)) if mm else None
        cov_a, cov_b = g(armseg, "cov"), g(botseg, "cov")
        spl_a, spl_b = g(armseg, "spl"), g(botseg, "spl")
        if None in (cov_a, cov_b, spl_a, spl_b):
            continue
        w = won.get((arm, mp, "A" if side == "A" else "B"))
        stratum = "small" if area[mp] < thresh else "large"
        per[arm][stratum].append((cov_a - cov_b, spl_a, spl_b, w))

    print(f"threshold: area < {thresh} tiles = 'small'\n")
    print(f"{'arm':10}{'stratum':>8}{'n':>4}{'arm win%':>10}{'r30 cov diff':>14}"
          f"{'arm spl@30':>12}{'bot spl@30':>12}")
    for arm in sorted(per):
        for stratum in ("small", "large"):
            L = per[arm][stratum]
            if not L:
                continue
            wins = [w for _, _, _, w in L if w is not None]
            wr = 100.0 * sum(wins) / len(wins) if wins else float("nan")
            print(f"{arm:10}{stratum:>8}{len(L):4d}{wr:9.1f}%"
                  f"{st.mean(x[0] for x in L):14.1f}{st.mean(x[1] for x in L):12.2f}"
                  f"{st.mean(x[2] for x in L):12.2f}")
    print("\nMechanism check: 'arm spl@30' must RISE in the small stratum for the arms with")
    print("SMALL_AREA > 0. If it does not, the gate never fired and any win change is not")
    print("this mechanism -- do not attribute it (iteration 37's lesson, iteration 38's proof).")

main()

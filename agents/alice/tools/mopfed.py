#!/usr/bin/env python3
"""Iteration 52 pre-check: are alice's post-saturation paints MOP-FED?

    tools/mopfed.py <from_round> <trace.txt> [...]

Input is tools/paint-trace.sh output. For every alice PAINT after <from_round>,
classify the tile by the most recent PRIOR action on that same tile.

  mop-fed (own)   last action was alice UNPAINT  -- alice's mopper made this target
  enemy-mop-fed   last action was enemy UNPAINT
  repaint own     last action was alice PAINT    -- ZERO coverage gain
  over enemy      last action was enemy PAINT    -- only a splasher can do this
  no prior action tile untouched since game start (INCLUDES the map's initial
                  paint around starting towers, which is emitted as map state and
                  not as an action -- so this class is "no action", not "virgin")

PRE-REGISTERED: mop-fed under 50% of alice's post-r200 paints kills the claim that
mopper throughput caps soldier output.
"""
import sys
from collections import defaultdict


def classify(path, r0):
    games = []
    cur = None
    for line in open(path, errors="replace"):
        line = line.rstrip("\n")
        if line.startswith("# GAME"):
            p = line.split()
            cur = dict(map=p[2], side=p[3], last={}, counts=defaultdict(int),
                       paints=0, unpaints=0, opp_paints=0, lastsec={},
                       shade=defaultdict(int), overby=defaultdict(int),
                       wasteby=defaultdict(int), allby=defaultdict(int))
            games.append(cur)
            continue
        if cur is None or " PAINT " not in line and " UNPAINT " not in line:
            continue
        try:
            parts = line.split()
            rnd = int(parts[1])
            team = parts[2].split("(")[1].split(",")[0]
            kind = "PAINT" if parts[3] == "PAINT" else "UNPAINT"
            loc = parts[4]
            utype = parts[2].split(",")[1].rstrip(")")
            sec = line.rstrip().endswith(" secondary")
        except (IndexError, ValueError):
            continue
        mine = (team == cur["side"])
        if kind == "PAINT" and mine and rnd > r0:
            prev = cur["last"].get(loc)
            if prev is None:
                k = "no prior action"
            elif prev == (True, "UNPAINT"):
                k = "mop-fed (own)"
            elif prev == (False, "UNPAINT"):
                k = "enemy-mop-fed"
            elif prev == (True, "PAINT"):
                k = "repaint own"
            else:
                k = "over enemy"
            cur["counts"][k] += 1
            cur["allby"][utype] += 1
            # Discriminating detail, because two classes have innocent readings:
            #  - "repaint own" is only WASTE if the shade is unchanged; flipping
            #    primary<->secondary is tower-pattern work.
            #  - "over enemy" should be IMPOSSIBLE for a soldier (verified trap:
            #    the attack debits 5 paint and does nothing), so the unit type
            #    doing it decides whether my model or my parser is wrong.
            if k == "repaint own":
                same = (sec == cur["lastsec"].get(loc))
                cur["shade"][same] += 1
                # THE discriminator: a SPLASHER re-covering its own ground is an
                # unavoidable side effect of an area weapon, not a decision. A
                # SOLDIER doing it spent 5 paint on a tile it already held, by
                # choice. Naming this "waste" without the split would blame a
                # targeting bug for the geometry of a splash.
                if same:
                    cur["wasteby"][utype] += 1
            if k == "over enemy":
                cur["overby"][utype] += 1
        if rnd > r0:
            if mine and kind == "PAINT":
                cur["paints"] += 1
            elif mine and kind == "UNPAINT":
                cur["unpaints"] += 1
            elif not mine and kind == "PAINT":
                cur["opp_paints"] += 1
        cur["last"][loc] = (mine, kind)
        if kind == "PAINT":
            cur["lastsec"][loc] = sec
    return games


def main():
    r0 = int(sys.argv[1])
    tot = defaultdict(int); shade = defaultdict(int); overby = defaultdict(int)
    wasteby = defaultdict(int); allby = defaultdict(int)
    P = U = OP = 0
    ngames = 0
    for path in sys.argv[2:]:
        for g in classify(path, r0):
            if g["paints"] == 0:
                continue
            ngames += 1
            for k, v in g["counts"].items():
                tot[k] += v
            P += g["paints"]; U += g["unpaints"]; OP += g["opp_paints"]
            for kk, vv in g["shade"].items(): shade[kk] += vv
            for kk, vv in g["overby"].items(): overby[kk] += vv
            for kk, vv in g["wasteby"].items(): wasteby[kk] += vv
            for kk, vv in g["allby"].items(): allby[kk] += vv
    n = sum(tot.values())
    print(f"\nalice PAINT actions after round {r0}: {n}  over {ngames} games")
    if n == 0:
        return
    for k in ("mop-fed (own)", "enemy-mop-fed", "repaint own", "over enemy", "no prior action"):
        print(f"  {k:<18}{tot[k]:>7}   {100*tot[k]/n:>5.1f}%")
    mf = 100 * tot["mop-fed (own)"] / n
    print(f"\n  PRE-REGISTERED BAR: mop-fed >= 50%  ->  "
          f"{'CAP IS BINDING' if mf >= 50 else 'NOT BINDING -- direction closes'}  ({mf:.1f}%)")
    if shade:
        same, diff = shade[True], shade[False]
        print(f"\n  'repaint own' split: SAME shade (pure waste) {same}"
              f"   shade CHANGED (pattern work) {diff}")
    if overby:
        print(f"  'over enemy' by unit type: {dict(overby)}")
    if wasteby:
        print(f"  SAME-SHADE REPAINTS by unit type: {dict(wasteby)}")
    if allby:
        print(f"  ALL alice post-r{r0} paints by unit type: {dict(allby)}")
    print(f"\n  alice paints after r{r0} : {P}")
    print(f"  alice unpaints (mops)   : {U}"
          f"    ratio paints/mops = {P/U:.2f}" if U else "")
    print(f"  opponent paints         : {OP}   (alice/opp = {P/OP:.2f})" if OP else "")


if __name__ == "__main__":
    main()

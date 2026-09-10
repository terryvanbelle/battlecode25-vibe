#!/usr/bin/env python3
"""The registered load-bearing half: is a MOPPED tile ever CLAIMED?

A mopper does not paint. `mopperAttack` emits UnpaintAction and leaves the tile
EMPTY -- not ours. So the paint that bought the mopper buys territory only if a
soldier subsequently paints that tile. If the tile is never claimed, or the enemy
re-takes it first, the mop bought nothing.

REGISTERED BEFORE THIS RAN (previous entry):
    PASS to dose down the mopper share if < 40% of mopped tiles are claimed.
    KILL                                if > 70% -- moppers are earning their share.

Reads one game's full action log. Every event is located and timestamped, so the
claim rate is measured WITHIN the game -- no cross-game term (the defect that made
me retract a manipulation check earlier today).
"""
import sys, re, statistics
from collections import defaultdict

EV = re.compile(r"round (\d+) id\d+\(T(\d),(\w+)\) (PAINT|UNPAINT) \((\d+),(\d+)\)")

def main():
    alice_team = None
    events = defaultdict(list)          # (x,y) -> [(round, team, verb)]
    for ln in open(sys.argv[1]):
        m = re.match(r"=== GameHeader\s+team1=(\S+)\s+team2=(\S+)", ln)
        if m:
            alice_team = '1' if 'alice' in m.group(1) else '2'
        g = EV.match(ln)
        if not g: continue
        rnd, team, _typ, verb, x, y = g.groups()
        events[(int(x), int(y))].append((int(rnd), team, verb))
    if alice_team is None:
        print("!! could not identify alice", file=sys.stderr); return 1

    mops = claimed = retaken = never = 0
    delays = []
    for tile, evs in events.items():
        evs.sort()
        for i, (r, t, v) in enumerate(evs):
            if v != 'UNPAINT' or t != alice_team: continue
            mops += 1
            nxt = None
            for (r2, t2, v2) in evs[i+1:]:
                if r2 <= r: continue
                if v2 == 'PAINT':
                    nxt = (r2, t2); break
            if nxt is None: never += 1
            elif nxt[1] == alice_team: claimed += 1; delays.append(nxt[0]-r)
            else: retaken += 1

    print(f"=== mopped-tile fate, one game (Bunny), measured within-game ===")
    print(f"    registered: PASS to dose if < 40% claimed; KILL if > 70%\n")
    print(f"  alice mop events               {mops:>6}")
    if not mops: return 0
    print(f"  -> next paint is ALICE'S       {claimed:>6}   {100*claimed/mops:>5.1f}%   CLAIMED")
    print(f"  -> next paint is the ENEMY'S   {retaken:>6}   {100*retaken/mops:>5.1f}%   re-taken")
    print(f"  -> never painted again         {never:>6}   {100*never/mops:>5.1f}%   wasted")
    if delays:
        delays.sort()
        print(f"\n  delay to claim: median {statistics.median(delays):.0f} rounds"
              f"   p90 {delays[int(.9*len(delays))]}   max {delays[-1]}")
    rate = 100*claimed/mops
    print(f"\n  CLAIM RATE = {rate:.1f}%")
    print("  VERDICT: " + ("**PASS -- dose the mopper share down**" if rate < 40 else
                           "**KILL -- moppers earn their share**" if rate > 70 else
                           "**BETWEEN -- neither branch fires**"))
    return 0

sys.exit(main())

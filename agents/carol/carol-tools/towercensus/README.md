# Cross-lineage tower census, and two offline map scans (iteration 48)

Three instruments built for iteration 48. The first is the only one in this
workspace whose opponents carol did not produce; the other two cost no games at
all and both changed a hypothesis before it was built.

## `towercensus.py` — who converts ruins into towers, and into WHICH towers

Runs `tools/replaydump/ReplayDump.java` over every replay of a tournament and
counts `SPAWN` events by tower type, per team, per map.

```bash
# on battlecode-dev, with ReplayDump.java compiled beside it
python3 towercensus.py ~/battlecode25-vibe/arena/tournaments/<run>/replays "$BC_JAR" > census.csv
```

Result over `20260909-0100` (450 replays, 900 team-games): alice 54.0% money
share / 66.2% ruin conversion, bob 53.2% / 43.7%, **carol 24.9% / 28.2%** —
carol's share is 23-29% in every pair and every regime, so it is a property of
her policy and not of one rival (doctrine 20).

**Read the `ruins` column carefully**: it comes from the replay MatchHeader and
counts ALL ruin tiles, which is exactly FOUR more than the claimable ruins in
`tools/mapdata`. The two answer different questions; this file's analysis
subtracts 4 to get claimable. Say which you used.

**A bug worth remembering**: the first version indexed the SPAWN regex groups
one off, keying counts by round number instead of by team. Every tower column
came back 0, which is what exposed it. A subtler off-by-one would have looked
entirely plausible — check a derived table against a total you already know.

## `KScan.java` — what money share `k % MONEY_MOD` actually ASKS for

Reads the 75 official `.map25` maps out of the engine jar and computes
`k = min(x,W-1-x) + min(y,H-1-y)` for every claimable ruin.

- Intended corpus money share: MOD 4 = 27.1%, MOD 3 = 32.5%, **MOD 2 = 55.6%**.
- Carol's *realized* share is 24.9% against an intended 27.1%, so the realized
  share is NOT a lottery over which ruins get claimed — that hypothesis died here.
- **MOD 4 is single-branch (zero money ruins) on 6 of 75 maps**: DefaultSmall,
  Fossil, FourCorners, Racetrack, SaltyPepper, roads. MOD 2 on only 1 (roads).
  Same class as the `(x+y)&1` trap in `tools/mapdata/README.md`.

## `SrpScan.java` — where a special resource pattern can legally go

`isValidPatternCenter` needs `2 <= x < W-2`, `2 <= y < H-2` and all 25 tiles of
the 5x5 free of walls AND ruins. Counted per map, straight from the jar.

- corpus: min 0, median 206, max 1685.
- **the 17 ruin-dense maps: min 86, median 502** — sites are ~4x more abundant
  in the regime carol loses, so SRP is regime-matched rather than diluted there.
- **ZERO valid centres on `Brat`, `CastleDefense`, `DefaultSmall`, `Paintball`,
  `gridworld`** (and 6 on `Justice`, 9 on `Snowman`). `DefaultSmall` is this
  project's default trace map: tracing SRP there would measure a mechanism that
  cannot fire and report it as dead code. Reported for `tools/mapdata/`.

Both scans reconcile exactly against the replay MatchHeader (Leaf: walls
160/3600, ruins 56) — which is what verifies the assumed flat-vector index
order rather than merely asserting it.

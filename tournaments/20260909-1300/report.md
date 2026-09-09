# Tournament 20260909-1300 (UTC)

450 decided games, against 450 in `20260909-0100`.


## Standings

| bot | won | played | win% | vs last |
|---|---|---|---|---|
| alice | 184 | 300 | 61.3% |   +8.0 |
| carol | 142 | 300 | 47.3% |   -3.0 |
| bob | 124 | 300 | 41.3% |   -5.0 |

## Head to head

| matchup | record | win% | vs last |
|---|---|---|---|
| alice vs bob | 90–60 | 60.0% |  +10.0 |
| alice vs carol | 94–56 | 62.7% |   +6.0 |
| bob vs carol | 64–86 | 42.7% |   0.0 |

## !! Do not pool these games with the previous run

These matchups reproduce their games in `20260909-0100` exactly — same winners, same round counts. The engine is deterministic, so pooling the two tournaments multiplies apparent sample size while adding no information, and any z-score over the pooled set is inflated.

- **bob–carol** — commits DIFFER, but all 150 games reproduce to the round count — a behaviour-preserving commit (150/150 identical)

Deduplicate on the **games**, not the run id and not the commit pair: a commit hash is a proxy for behaviour, and scaffolding that defaults to an exact zero arm changes the hash while the bot plays the identical game.


## Swept maps

Won from *both* sides, so a sweep is immune to spawn advantage.


**These do not corroborate the head-to-head margin — they restate it.** Every map is played twice, so wins = 2·SW + D and losses = 2·SL + D, where D is the split maps; the D cancels and, over N maps


> wins − losses = 2 × (swept − swept against)  
> wins − N = (swept − swept against)   *("margin over 50%")*


Both forms are exact; they differ only in which quantity "margin" names, so say which you mean.


Verified on every pair of every run. So citing a margin *and* its sweep counts as two agreeing pieces of evidence is citing one number twice. What the sweep counts add that the margin cannot is **D, the number of split maps** — how decisive the pair is, not who is ahead. A 60–40 pair with few splits is a different animal from a 60–40 pair that is mostly coin-flips, and only the sweep counts tell them apart.

- **alice–bob**: alice swept 29, bob swept 14, 32 split
- **alice–carol**: alice swept 36, carol swept 17, 22 split
- **bob–carol**: bob swept 23, carol swept 34, 18 split

## What played

Each bot is exported from HEAD at tournament time, never the working tree.

- `alice` @ `55c8037` alice: ACCEPT iteration 43 -- de-degenerate the tower key; +3 on the four, 0 on the other 71
- `bob` @ `eb894c1` bob: iteration 40 scaffolding -- SMALL_AREA, defaulted to the exact zero arm
- `carol` @ `5be82ca` carol: ACCEPT iteration 44 -- 97/150, margin +44 (6.8 sd); DENIED RUINS

## How games ended

| outcome | games | share |
|---|---|---|
| The winning team painted enough of the map. | 388 | 86.2% |
| The winning team won on tiebreakers (painted more of the map). | 62 | 13.8% |

## What this cannot tell you

**These standings are relative, not absolute.** Every game has a winner
among the three, so wins are conserved — the three win counts always sum
to 450. If all three lineages improve by the same amount, every
number above stays exactly where it is. A delta therefore means *changed
relative to the other two*, and can never mean *got better* or *got worse*
on its own. Absolute strength is what each agent's frozen roster measures
(`progress/vs_old_bots.png`), because a frozen opponent cannot improve
alongside you. Read the two together: a lineage can gain real absolute
strength and move nowhere here, which is the normal case when all three
are working.

**And weigh the delta by the work behind it.** Between `20260909-0100` and
this run — a 12-hour gap — the agents committed 84 times across 5 distinct
hours. Commits are only a proxy, but a small delta over a mostly idle
interval says little about the lineages and a lot about their uptime;
sessions here are killed regularly by usage limits and dropped
connections, which is not the agents' doing.


## Reading this

Deltas compare against `20260909-0100`. Both runs were complete, so both
played the full map list and the two are measured on the same ground.
Treat a few points as noise; a pair moving together with its swept-map
count is the signal worth chasing.

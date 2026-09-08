# Tournament 20260908-1300 (UTC)

450 decided games, against 450 in `20260908-0100`.


## Standings

| bot | won | played | win% | vs last |
|---|---|---|---|---|
| alice | 169 | 300 | 56.3% |   +9.0 |
| bob | 145 | 300 | 48.3% |  -22.0 |
| carol | 136 | 300 | 45.3% |  +13.0 |

## Head to head

| matchup | record | win% | vs last |
|---|---|---|---|
| alice vs bob | 75–75 | 50.0% |  +24.0 |
| alice vs carol | 94–56 | 62.7% |   -6.0 |
| bob vs carol | 70–80 | 46.7% |  -20.0 |

## Swept maps

Won from *both* sides, so a sweep is immune to spawn advantage.


**These do not corroborate the head-to-head margin — they restate it.** Every map is played twice, so wins = 2·SW + D and losses = 2·SL + D, where D is the split maps; the D cancels and, over N maps


> wins − losses = 2 × (swept − swept against)  
> wins − N = (swept − swept against)   *("margin over 50%")*


Both forms are exact; they differ only in which quantity "margin" names, so say which you mean.


Verified on every pair of every run. So citing a margin *and* its sweep counts as two agreeing pieces of evidence is citing one number twice. What the sweep counts add that the margin cannot is **D, the number of split maps** — how decisive the pair is, not who is ahead. A 60–40 pair with few splits is a different animal from a 60–40 pair that is mostly coin-flips, and only the sweep counts tell them apart.

- **alice–bob**: alice swept 23, bob swept 23, 29 split
- **alice–carol**: alice swept 36, carol swept 17, 22 split
- **bob–carol**: bob swept 26, carol swept 31, 18 split

## What played

Each bot is exported from HEAD at tournament time, never the working tree.

- `alice` @ `920dafd` alice: ACCEPT iteration 30 -- 58.0%, +12 net swept, fires on EVERY map
- `bob` @ `e425f46` bob: ACCEPT iteration 20 -- spawn 2 splashers per 5 units, not 1
- `carol` @ `432d702` carol: ACCEPT iteration 36 -- the PAINT floor; 28/50, and the mopper share falls 12.8% -> 0.19%

## How games ended

| outcome | games | share |
|---|---|---|
| The winning team painted enough of the map. | 384 | 85.3% |
| The winning team won on tiebreakers (painted more of the map). | 65 | 14.4% |
| The winning team destroyed all of the enemy team's units. | 1 | 0.2% |

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

**And weigh the delta by the work behind it.** Between `20260908-0100` and
this run — a 12-hour gap — the agents committed 200 times across 10 distinct
hours. Commits are only a proxy, but a small delta over a mostly idle
interval says little about the lineages and a lot about their uptime;
sessions here are killed regularly by usage limits and dropped
connections, which is not the agents' doing.


## Reading this

Deltas compare against `20260908-0100`. Both runs were complete, so both
played the full map list and the two are measured on the same ground.
Treat a few points as noise; a pair moving together with its swept-map
count is the signal worth chasing.

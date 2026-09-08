# Tournament 20260908-0100 (UTC)

450 decided games, against 450 in `20260907-1300`.


## Standings

| bot | won | played | win% | vs last |
|---|---|---|---|---|
| bob | 211 | 300 | 70.3% |  -22.0 |
| alice | 142 | 300 | 47.3% |   +9.3 |
| carol | 97 | 300 | 32.3% |  +12.7 |

## Head to head

| matchup | record | win% | vs last |
|---|---|---|---|
| alice vs bob | 39–111 | 26.0% |  +18.7 |
| alice vs carol | 103–47 | 68.7% |   0.0 |
| bob vs carol | 100–50 | 66.7% |  -25.3 |

## Swept maps

Won from *both* sides, so a sweep is immune to spawn advantage.


**These do not corroborate the head-to-head margin — they restate it.** Every map is played twice, so wins = 2·SW + D and losses = 2·SL + D, where D is the split maps; the D cancels and, over N maps


> wins − losses = 2 × (swept − swept against)  
> wins − N = (swept − swept against)   *("margin over 50%")*


Both forms are exact; they differ only in which quantity "margin" names, so say which you mean.


Verified on every pair of every run. So citing a margin *and* its sweep counts as two agreeing pieces of evidence is citing one number twice. What the sweep counts add that the margin cannot is **D, the number of split maps** — how decisive the pair is, not who is ahead. A 60–40 pair with few splits is a different animal from a 60–40 pair that is mostly coin-flips, and only the sweep counts tell them apart.

- **alice–bob**: alice swept 8, bob swept 44, 23 split
- **alice–carol**: alice swept 39, carol swept 11, 25 split
- **bob–carol**: bob swept 39, carol swept 14, 22 split

## What played

Each bot is exported from HEAD at tournament time, never the working tree.

- `alice` @ `25c3160` alice: repair the splasher dead branch (inert), and size the direction
- `bob` @ `f67ac8b` bob: ACCEPT iteration 18 -- spend the last paint on the tower pattern
- `carol` @ `6c55fc4` carol: ACCEPT iteration 29 -- 88% and 19 swept wins to zero on a fresh random 25-map sample

## How games ended

| outcome | games | share |
|---|---|---|
| The winning team painted enough of the map. | 343 | 76.2% |
| The winning team won on tiebreakers (painted more of the map). | 107 | 23.8% |

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

**And weigh the delta by the work behind it.** Between `20260907-1300` and
this run — a 12-hour gap — the agents committed 214 times across 10 distinct
hours. Commits are only a proxy, but a small delta over a mostly idle
interval says little about the lineages and a lot about their uptime;
sessions here are killed regularly by usage limits and dropped
connections, which is not the agents' doing.


## Reading this

Deltas compare against `20260907-1300`. Both runs were complete, so both
played the full map list and the two are measured on the same ground.
Treat a few points as noise; a pair moving together with its swept-map
count is the signal worth chasing.

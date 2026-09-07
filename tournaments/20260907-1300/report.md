# Tournament 20260907-1300 (UTC)

450 decided games, against 450 in `20260907-0100`.


## Standings

| bot | won | played | win% | vs last |
|---|---|---|---|---|
| bob | 277 | 300 | 92.3% |   -3.3 |
| alice | 114 | 300 | 38.0% |   +2.7 |
| carol | 59 | 300 | 19.7% |   +0.7 |

## Head to head

| matchup | record | win% | vs last |
|---|---|---|---|
| alice vs bob | 11–139 | 7.3% |   +2.7 |
| alice vs carol | 103–47 | 68.7% |   +2.7 |
| bob vs carol | 138–12 | 92.0% |   -4.0 |

## Swept maps

Won from *both* sides, so immune to spawn advantage — the honest read on a pair.

- **alice–bob**: alice swept 1, bob swept 65
- **alice–carol**: alice swept 42, carol swept 14
- **bob–carol**: bob swept 64, carol swept 1

## What played

Each bot is exported from HEAD at tournament time, never the working tree.

- `alice` @ `688a75b` alice: ACCEPT iteration 14 -- wander slides along obstacles instead of re-rolling
- `bob` @ `ceef7af` bob: iteration 12 -- revert the hash, REMOVE the ruin memory, on sweep evidence
- `carol` @ `c213c1b` carol: REVERSE the iteration 12 rejection -- ACCEPT it; the mirror control refutes my noise argument

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

**And weigh the delta by the work behind it.** Between `20260907-0100` and
this run — a 12-hour gap — the agents committed 102 times across 4 distinct
hours. Commits are only a proxy, but a small delta over a mostly idle
interval says little about the lineages and a lot about their uptime;
sessions here are killed regularly by usage limits and dropped
connections, which is not the agents' doing.


## Reading this

Deltas compare against `20260907-0100`. Both runs were complete, so both
played the full map list and the two are measured on the same ground.
Treat a few points as noise; a pair moving together with its swept-map
count is the signal worth chasing.

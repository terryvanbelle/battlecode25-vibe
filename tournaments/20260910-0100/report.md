# Tournament 20260910-0100 (UTC)

450 decided games, against 450 in `20260909-1300`.


## Standings

| bot | won | played | win% | vs last |
|---|---|---|---|---|
| alice | 175 | 300 | 58.3% |   -3.0 |
| carol | 161 | 300 | 53.7% |   +6.3 |
| bob | 114 | 300 | 38.0% |   -3.3 |

## Head to head

| matchup | record | win% | vs last |
|---|---|---|---|
| alice vs bob | 90–60 | 60.0% |   0.0 |
| alice vs carol | 85–65 | 56.7% |   -6.0 |
| bob vs carol | 54–96 | 36.0% |   -6.7 |

## !! Do not pool these games with the previous run

These matchups reproduce their games in `20260909-1300` exactly — same winners, same round counts. The engine is deterministic, so pooling the two tournaments multiplies apparent sample size while adding no information, and any z-score over the pooled set is inflated.

- **alice–bob** — commits DIFFER, but all 150 games reproduce to the round count — a behaviour-preserving commit (150/150 identical)

Deduplicate on the **games**, not the run id and not the commit pair: a commit hash is a proxy for behaviour, and scaffolding that defaults to an exact zero arm changes the hash while the bot plays the identical game.


## Swept maps

Won from *both* sides, so a sweep is immune to spawn advantage.


**These do not corroborate the head-to-head margin — they restate it.** Every map is played twice, so wins = 2·SW + D and losses = 2·SL + D, where D is the split maps; the D cancels and, over N maps


> wins − losses = 2 × (swept − swept against)  
> wins − N = (swept − swept against)   *("margin over 50%")*


Both forms are exact; they differ only in which quantity "margin" names, so say which you mean.


Verified on every pair of every run. So citing a margin *and* its sweep counts as two agreeing pieces of evidence is citing one number twice. What the sweep counts add that the margin cannot is **D, the number of split maps** — how decisive the pair is, not who is ahead. A 60–40 pair with few splits is a different animal from a 60–40 pair that is mostly coin-flips, and only the sweep counts tell them apart.

- **alice–bob**: alice swept 29, bob swept 14, 32 split
- **alice–carol**: alice swept 31, carol swept 21, 23 split
- **bob–carol**: bob swept 15, carol swept 36, 24 split

## What played

Each bot is exported from HEAD at tournament time, never the working tree.

- `alice` @ `55c8037` alice: ACCEPT iteration 43 -- de-degenerate the tower key; +3 on the four, 0 on the other 71
- `bob` @ `b85c7cf` bob: the "ABLATION A7" comment is shipping code -- say so, in the comment
- `carol` @ `3610230` carol: ACCEPT iteration 60 as carol_iter45 -- 88/150, margin +26 (+2.01 sd); D3 paint logistics (REFILL_LOW=50)

## How games ended

| outcome | games | share |
|---|---|---|
| The winning team painted enough of the map. | 385 | 85.6% |
| The winning team won on tiebreakers (painted more of the map). | 65 | 14.4% |

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

**And weigh the delta by the work behind it.** Between `20260909-1300` and
this run — a 12-hour gap — the agents committed 218 times across 10 distinct
hours. Commits are only a proxy, but a small delta over a mostly idle
interval says little about the lineages and a lot about their uptime;
sessions here are killed regularly by usage limits and dropped
connections, which is not the agents' doing.


## Reading this

Deltas compare against `20260909-1300`. Both runs were complete, so both
played the full map list and the two are measured on the same ground.
Treat a few points as noise; a pair moving together with its swept-map
count is the signal worth chasing.

**Attribution.** `alice` is unchanged since `20260909-1300` — same commit, so the same bot played. Standings are relative and a delta normally cannot separate *I improved* from *they got worse*, but a delta against an unchanged opponent can: for `bob`, `carol`, the head-to-head move against `alice` is attributable to their own changes, not to opponent drift. (The reverse also holds: a frozen bot's own delta is a readout of what the others did.)

But `bob` has a changed commit whose games reproduce the previous run exactly (see above), so the commit changed and the play did not. Read that bot's zero delta as the absence of a behavioural change, not as a change that happened to score the same.

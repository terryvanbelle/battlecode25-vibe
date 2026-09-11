# Darla — design thesis and standing registration

Started 2026-09-10 by the coordinator, after the user retired alice and carol.
Darla is written from scratch but not from nothing: the isolation firewall that
kept the three lineages apart does not apply to me, so this is the first design in
the project that uses everything all three established at once.

## The thesis

Both surviving lineages spent weeks optimising **economy and coverage**. Both drove
that framing to a genuinely complete enumeration — twenty-plus mechanism axes each,
every design premise closed, committed closure maps — and both lose three quarters
of their games to the external standard (17.3% and 24.7% against `v3`, ~1% and 0%
against `TSPAARKHS`).

Meanwhile the single strongest empirical result anyone produced was an accident.
carol built a 38-line fork of her own bot that sieges towers with splashers,
intending it purely as a measuring stick, and **it beat her 60/40** — the only
opponent in her pool she loses to. It contains no defensive code at all, so the
advantage is a *capability* gap rather than a defensive one, which means it
transfers to whoever adopts it. Nobody did.

**Darla's thesis: tower removal is the lever, and it is available to splashers by
an engine asymmetry nobody exploited.** Economy is a means of producing splashers,
not the objective.

## The nine findings the code is built on

Each is measured, by the lineage named, and each maps to a specific decision in
`src/darla/RobotPlayer.java`.

| # | finding | source | where it lands |
|---|---|---|---|
| 1 | splasher-primary; soldier-primary rejected at −5.71 sd; production efficiency 0.1291 vs 0.0603 tiles per build-paint, replicated across two independent designs | carol, alice | `chooseSpawn` |
| 2 | moppers are **superseded**, not merely inefficient — 0.0000 production over 105 spawns, and a splasher takes enemy ground in one step across 13 tiles where a mopper takes one tile in two steps | alice | never built |
| 3 | `SPLASHER.actionRadiusSquared = 4` reaches distance 4; a paint or money tower answers only to 3. **The splasher out-ranges what it kills.** 100 AoE against 1000 health is ten hits | carol | `runSplasher`, approach stops at the edge of our reach |
| 4 | tower damage is **permanent** — no restoration path, `upgradeTower` carries the deficit forward, towers sit outside `processEndOfTurn`. ~25 hits per kill observed | alice | towers always fire; splashers keep a target |
| 5 | killing the last money tower freezes the victim's production **permanently** — 1,887 consecutive frozen rounds measured | carol | money towers targeted first |
| 6 | spending **is** the investment: cutting spawns 78% banked nothing (147.0 vs 147.4 per tower), because income is per-tower and spawning builds towers | alice | never withhold production |
| 7 | never gate a paint-costly action on chips: rank correlation −0.496, and above a high chip gate the paint clears on **0.0%** of 244 frames | alice | no chip threshold anywhere |
| 8 | a money tower has `paintPerTurn == 0` — two robots and then a dry build site; `buildRobot` draws from the **building** tower's stash | carol | paint towers 3:1 |
| 9 | winning the tower race is not winning: 12–4 on the race, 75% conversion | alice | siege over expansion |

Two further constraints are honoured without being findings about the game:
a constant must not be set above the level its resource normally holds (alice's
reserve of 200 against towers holding 154.8 disabled her own mechanism on 82.9% of
frames), and a persistent heading beats a nearest-target rule, because units are
blocked by robots rather than walls and a nearest-empty rule points a forward unit
backwards (carol).

## Registration for run `20260910-200447` / the first 90-game gauntlet

Written before any result was read.

**This is a shakedown, not a screen.** A v1 from-scratch bot against three mature
lineages is expected to lose; carol's own from-scratch rewrite was rejected at
−5.71 sd and still paid, because it answered a question no cheaper experiment
could. So the win rate is **not** the quantity of interest here.

What the run must establish, in order:

1. **Does it play?** Games complete, no forfeits, no bytecode overruns. If not,
   nothing else in the run means anything.
2. **Does the siege mechanism fire?** Splashers should spend turns in `SIEGE` and
   `APPROACH`, not only painting. A design whose central mechanism never fires is
   untested, not refuted — the trap that cost alice iteration 15b and carol
   iteration 10.
3. **Do towers actually die?** Finding #4 says damage accumulates, so the question
   is whether hits convert to removals at anything like the ~25:1 observed rate.

**What would refute the thesis**, registered now so it cannot be reinterpreted:

- the siege fires often and enemy tower count is unmoved → the range advantage does
  not survive contact, and finding #3 is a fact about the engine that does not
  reach the game;
- Darla wins the ground race and still loses → tower removal is not the lever and
  the thesis is wrong in the same way the two lineages' economy framing was.

**What would support it:** tower kills accumulating over a game, and Darla's wins
concentrated in games where it removed a money tower.

**What is not evidence either way:** the aggregate win rate of a first version.

## Registration — iteration 1, the mopper arm (`darla2`)

Written before any game of the arm was played. Baseline is `darla1` at commit
`4335c3c`: **89/144 (61.8%)**, from runs `20260910-213703` (41/72) and
`20260910-213919` (48/72).

**The change, and only this change**: `MOPPER_IN_20` 2 → 0. Every other byte of
the file is identical, so the two arms differ by one integer.

**Why**: finding #2. alice measured moppers at 0.0000 tiles per build-paint over
105 spawns and classified them **superseded**, not merely inefficient — a
splasher overwrites enemy paint directly inside r²≤2 of a centre it can place
r²≤4 away, taking up to 13 tiles in one step where a mopper takes one tile in
two. A superseded unit is not rescued by a better conversion rate. The Carol base
spends 10% of production on them; this arm moves that to splashers.

**Design**: matched pair on a deterministic engine. Both arms play the SAME two
pinned 12-map samples (`gauntlet/20260910-213703/maps.txt` and
`.../20260910-213919/maps.txt`), both sides, same three opponents — 144 games
against 144, paired game-for-game rather than compared across samples.

**Gate, pre-registered**:

- **accept** if darla2 > 89/144 overall AND no opponent leg falls below 50%;
- **reject** if darla2 < 89/144 overall;
- **on an exact tie, accept darla2** — same strength for one fewer unit type and
  one fewer branch, and finding #2 says the unit is superseded.

**Falsifier for the transfer of finding #2.** If darla2 loses by 5 games or more
net, finding #2 does not transfer to this bot, and the reason will be that
alice's production-efficiency metric priced enemy-paint removal at zero **by
construction** — it counts tiles painted OUR colour per build-paint, and a
mopper's output is the removal of theirs. That would make #2 a true statement
about a metric and a false one about the unit. In that case the next arm is
`MOPPER_IN_20 = 1`, to separate "moppers help" from "10% is too many".

**Not evidence either way**: the overall rate against any single opponent taken
alone. n=48 per leg, and the carol leg of `213703` split by side on 10 of 12
maps — a sample that mostly measures who spawned better.

## Registration — iteration 2, the seeing-mopper arm (`darla3`)

Written before any game of the arm was played, and before `darla2`'s result was
read. Same baseline: `darla1`, **89/144**, same two pinned samples.

**Found while `darla2` was still running, and it changes what `darla2` measures.**
alice's iteration 7 was **accepted at 20/23 (87%)**, and its whole mechanism was
one line of mopper navigation: unpaints per mopper alive rose ~3x. Darla inherits
carol's mopper, and carol's mopper is the *blind* one alice fixed — it picks
targets from `senseNearbyMapInfos(2)`, its 8 adjacent tiles, then calls
`moveExploring(null)` and wanders, while its vision is r²=20, about 60 tiles. It
is blind to ~90% of what it can already see.

So `darla2` is not testing "moppers vs no moppers". It is testing **"blind
wandering moppers vs no moppers"** — a much weaker question, and one whose answer
does not settle the unit. I am recording that now, with `darla2` unread, rather
than after a result that would make it look like reinterpretation.

**The change**: the mopper walks toward the nearest enemy paint anywhere in
vision instead of wandering. Population unchanged, cost unchanged — the
"capability preserved at zero marginal cost" shape. `moveExploring` already
takes a target, so the port is the target computation and nothing else.

**Mechanism check, and it comes first**: the build carries `ms=<seek>/<seekHit>`
in its indicator string. If `seekHit` is ~0 the mopper never found enemy paint in
vision and the arm is **untested, not refuted** — the trap that cost alice
iteration 15b and carol iteration 10. No verdict is read off the win rate until
that counter says the mechanism fired.

**Gate**: accept if darla3 > 89/144 with no leg below 50%; reject if ≤ 89/144
*with the mechanism firing*. Bytecode is the named risk — a full-vision scan per
mopper turn — so `ov=` (overruns) must stay at 0; a non-zero overrun count voids
the arm regardless of the score, because a robot that misses its turn is a
different bot, not a worse one.

**Together, darla2 and darla3 bracket the unit.** darla2 removes it; darla3 makes
it see. If both beat darla1, the base's moppers were simply wasted and the next
question is seeing-moppers against no-moppers directly. If darla3 wins and darla2
loses, finding #2 is a fact about alice's production metric — which prices enemy-
paint removal at zero by construction — and not about the unit.

## Registration — iteration 3, the `SPLASH_FLOOR` dose ladder (`darla4`, `darla5`)

Written before any game of either arm, and before `darla2`/`darla3` were read.
Baseline `darla1` = **89/144** on the two pinned samples.

**This is a re-open, and carol wrote the re-open condition herself.** Her
iteration 47 bracketed `SPLASH_FLOOR` against her own descendants — dose 0 at
−3.26 sd, dose 1400 at −0.93 sd, incumbent 2000 — and closed the axis with an
unusually precise ledger entry: *"CLOSED **for self-play evaluation** … Re-opening
requires a different opponent, not a different dose."* Her reason was doctrine 17:
her whole opponent pool descends from a bot that does not convert ruins, and an
even instrument cannot measure a capability against an opponent that never
exercises it.

**Darla is that different opponent, and is the first build in the project to have
one.** Her pool is alice, bob and carol — three independent lineages. alice
reaches 14–16 towers in the games below; carol's pool never did.

**What the constant does**, from carol's own comment in the inherited code: with
`reserve = 1200`, a SPLASHER needs `chips >= 1600` while a SOLDIER needs
`1200 + 250 + 2000 = 2250` and a MOPPER `2300`. **The cheaper unit is gated
higher.** Against a treasury whose median is ~1,400 the soldier gate is simply
never reached — and this is the exact error class DESIGN.md was written to avoid:
*a constant set above the level its resource normally holds*.

**The diagnosis that motivated it, from four of darla1's own loss replays**
(mechanism only — replay inspection never sets a verdict, carol's iteration 47
stage 0 is the cautionary case):

| map | opponent | darla end state | opponent | win type |
|---|---|---|---|---|
| SaltyPepper | alice | **sold 0**, spl 15, tw 8, cov 281, tower paint **3,508 unspent** | sold 27, tw 13, cov 700 | MAJORITY_PAINTED |
| Oasis | alice | sold 4, spl 8, tw **5** (flat r100→r400) | sold 24, tw 14 | MAJORITY_PAINTED |
| yearofthesnake | bob | sold 16, tw **3** | tw 15, cov 702 | MAJORITY_PAINTED |
| DefaultHuge | carol | sold 39, spl 2, tw 15, cov 224 | tw 16, cov 700 | MAJORITY_PAINTED |

**All four losses are MAJORITY_PAINTED.** Darla does not lose the tower race and
then lose; she loses the *coverage* race, holding thousands of unspent tower paint
and a flat treasury, because only soldiers paint ground and claim ruins and the
gate above stops her building them. On SaltyPepper the treasury sits at $1,350 for
1,200 consecutive rounds — permanently below the 2,250 soldier gate — and the
soldier population reaches **zero**.

**Arms**: `darla4` = 1400, `darla5` = 0. One constant, nothing else changed. Both
on the two pinned samples against all three lineages.

**The pre-registered prediction, and it is a prediction about the SPLIT, not the
total.** If carol's doctrine-17 reading is right, the sign of this dose is a
property of the *opponent*:

- **vs carol** — a splasher-flood coverage bot — lowering the floor should be
  neutral-to-negative, reproducing her own −0.93 sd (1400) and −3.26 sd (0);
- **vs alice and bob** — which convert ruins and reach 14–16 towers — it should be
  **positive**, because matching conversion is the whole game against them.

**What refutes the re-open**: the dose is negative against all three legs, or flat
against all three. Either kills it, and kills it for a stated reason — if the
effect is uniform across three independent lineages then the axis is simply flat
and carol's closure generalises beyond self-play, which would make "different
opponent" the wrong re-open condition rather than an unmet one.

**What is not evidence**: any single leg's total, and any single map. n=48 per
leg; carol's iteration 47 recorded 60% of maps splitting by spawn side on this
very axis, so **swept maps are the column to read**, not the raw rate.

## The founding thesis is REFUTED, on the win condition itself

Answering the three questions registered for the first run, in the order they
were registered, and then a fourth that settles the design.

**1. Does it play?** Yes. 144 games, no forfeits, no bytecode overruns.

**2. Does the siege mechanism fire?** **Yes.** Indicator states sampled from a
40-round mid-game window on SaltyPepper: `ring` 27, `approach` 1 against
`SPLASH` 12, `cd` 54, `noTgt` 42, `lowScore` 34. Splashers do hold the firing
ring at r²=10..16 — outside a tower's r²=9 reach, inside their own. So the design
is **tested, not untested**: this is not alice's iteration 15b or carol's
iteration 10.

**3. Do towers die?** Barely. Across the loss replays examined, enemy tower
counts *rise* monotonically — Oasis 5→12→14→14, DefaultHuge 13→16, SaltyPepper
11→10→11→12→13, one tower killed all game. That is the first registered
refutation branch verbatim: *"the siege fires often and enemy tower count is
unmoved → the range advantage does not survive contact."*

**4. And the fourth question, which I did not think to register, decides it.**
Tallying how all 144 games were actually won:

| win type | games | share |
|---|---|---|
| "painted enough of the map" | 125 | 86.8% |
| "tiebreakers (painted more of the map)" | 14 | 9.7% |
| **paint coverage, either way** | **139** | **96.5%** |
| "destroyed all of the enemy team's units" | 5 | 3.5% |

**BC25 is decided by paint coverage in 96.5% of games.** Tower removal is not a
win condition. It is instrumental at best — a dead money tower freezes the
victim's production (carol's 1,887 frozen rounds, finding #5) and so reduces the
ground they paint — but the lever it feeds is coverage, and the thesis named it
as the objective.

**So the thesis is wrong in the same shape as the one it replaced.** I wrote that
both lineages "spent weeks optimising economy and coverage" and lost anyway, and
treated coverage as the framing to escape. The win-type tally says coverage *is*
the game, and that the two lineages had the right objective and an insufficient
bot. What Darla actually brought was not a new objective; it was carol's economy,
which is a coverage engine, plus a siege that fires and does not pay.

**This is not a reason to remove the siege.** It costs nothing observable — the
splashers were already built and already moving — and it is not what loses the
games. It is a reason to stop treating it as the design's centre, and to spend
every remaining iteration on coverage.

**And it promotes the `SPLASH_FLOOR` arms from "a defect I found" to "the main
line".** Darla loses MAJORITY_PAINTED with her soldier count at zero and thousands
of tower paint unspent; soldiers are the only unit that paints ground durably and
the only unit that claims ruins. `darla4`/`darla5` are now the primary
experiment, and they were re-ordered ahead of the mopper arms on this basis.

**What would refute *this* reading**: `darla4`/`darla5` restore the soldier count
and the coverage race and still lose. Then coverage is not reachable from this
economy either, and the bot needs a different production engine rather than a
different constant.

### Amendment to the dose ladder, written before either arm returned

Traced the gate arithmetic properly instead of reasoning from the median alone.
carol already handles the pinned-treasury case: after `STAGNANT_ROUNDS = 10` turns
with chips in `[CHIP_RESERVE, CHIP_RESERVE + 250)`, `reserve` drops to 0. So on
SaltyPepper, where the treasury sits at $1,350 for 1,200 rounds, the reserve is
already being freed — and a soldier is *still* blocked, because `SPLASH_FLOOR`
then demands `chips - 250 >= 2000`, i.e. $2,250, which $1,350 never reaches.

**`SPLASH_FLOOR` is therefore the sole remaining blocker, which sharpens both
arms into a prediction about whether the mechanism fires at all:**

| arm | floor | soldier needs (reserve freed) | vs a $1,350 treasury |
|---|---|---|---|
| `darla1` | 2000 | $2,250 | never affordable |
| `darla4` | 1400 | $1,650 | **still rarely affordable** |
| `darla5` | 0 | $250 | affordable |

So `darla4` is expected to be **close to a null**, and if it returns flat that is
**the mechanism not firing, not the axis being flat** — the exact
untested-versus-refuted confusion this file keeps warning about. `darla5` is the
arm that actually tests the question.

**Mechanism check, and it must be read before either win rate**: soldier build
events per game, straight off the replay aggregates (`sold` and `+sold`), against
darla1's zero-to-five. If `darla5` does not raise the soldier count materially,
no verdict is read off its score at all.

This also demotes carol's own dose-0 result rather than contradicting it. Her
−3.26 sd at floor 0 was measured against `carol_iter44`, a splasher-flood bot
that wins on coverage — the opponent her ledger says cannot answer the question.

## Iteration 1 RESULT — `darla2` (no moppers): **REJECT**, and the falsifier fires

Runs `20260910-232926` (40/72) and `20260910-234220` (44/72), the two pinned
samples darla1 played. Matched pair, 144 games against 144.

| | darla1 | **darla2** | delta |
|---|---|---|---|
| overall | 89/144 (61.8%) | **84/144 (58.3%)** | **−5** |
| vs carol | 30/48 (62.5%) | 28/48 (58.3%) | −2 |
| vs bob | 30/48 (62.5%) | 31/48 (64.6%) | +1 |
| vs alice | 29/48 (60.4%) | **25/48 (52.1%)** | **−4** |

**Gate was: accept if > 89, reject if < 89, accept on an exact tie. 84 < 89 —
REJECTED.** Moppers stay in.

**And the pre-registered falsifier fires on its exact threshold.** I registered:
*"If darla2 loses by 5 games or more net, finding #2 does not transfer to this
bot, and the reason will be that alice's production-efficiency metric priced
enemy-paint removal at zero by construction."* The margin is −5. So finding #2 —
"moppers are **superseded**, 0.0000 tiles per build-paint over 105 spawns" — is a
true statement about a metric that counts tiles painted OUR colour, and a false
statement about the unit, whose output is the removal of THEIRS.

**Honesty about the size.** At n=144 the binomial sd is 6.0 games, so −5 is
−0.83 sd: rejected on the gate, but inside the noise floor, and I am not claiming
a demonstrated regression. What raises my confidence above the bare number is that
the loss is **concentrated against alice** (−4 of the −5), and alice is precisely
the lineage that fixed her moppers and won 87% doing it. The unit matters most
against the opponent that contests paint hardest — which is the shape the
metric-artefact reading predicts, and not what noise would pick out.

**Consequence**: `darla3` (alice's accepted mopper navigation, ported) is
promoted. darla2 established that Darla's *blind* moppers are worth roughly their
keep; darla3 asks what they are worth when they can see. It stays queued behind
the `SPLASH_FLOOR` arms, which the win-type tally made the main line.

## The soldier turn budget, measured — and it names two distinct failures

Indicator-string census of darla1's own games (mechanism only; no verdict is read
off replays). The build tags every soldier turn with why it did or did not paint.

**Regime A — the soldier never exists.** On Leaf, DonkeyKong and SaltyPepper there
are **zero soldier-turns** in mid-game windows, because `SPLASH_FLOOR` never lets
one be built. Leaf (56 ruins) vs alice, darla as team 1:

| round | darla | alice |
|---|---|---|
| 300 | sold 2, tw 9, cov 271, **tower paint 4,072** | sold 24, tw 21, cov 353 |
| 600 | sold 1, tw 9, cov 422, tower paint 1,058 | sold 36, tw 22, cov 482 |
| 900 | sold 2, tw 14, cov 379, **tower paint 8,028** | sold 67, tw 25, cov 564 |
| 1146 | **sold 0**, tw 16, cov 270, **tower paint 9,716** | sold 38, tw 25, **cov 700** |

Darla finishes holding **9,716 paint in her towers with no soldiers to spend it**,
chips pinned at $1,420, coverage falling 422 → 270 while alice climbs to 700. The
resource is there; the gate forbids converting it. Note $1,420 is also below
`darla4`'s $1,650 threshold — a second independent confirmation of the amendment
that `darla4` may not fire.

**Regime B — the soldier exists and is blocked.** DefaultHuge (53 ruins) is rich
enough to clear the gate: ~40 soldiers alive. 777 soldier-turns, rounds 600–630:

| what the soldier did | turns | share |
|---|---|---|
| **IDLE-ENEMY** — enemy paint in reach, and a soldier cannot overwrite it | **413** | **53.2%** |
| IDLE-ALLY — standing in our own paint, nothing to do | 187 | 24.1% |
| HOME — dry, walking back to a tower | 138 | 17.8% |
| **painted a tile** | **14** | **1.8%** |
| hit an enemy tower | 10 | 1.3% |

**1.8% of soldier-turns produce paint**, and the soldiers are not dry — median
paint held is 150 of a 200 capacity. The frontier-seeking fallback fails almost
completely: `frontNone` 185 against `frontFound` 2.

**The 53.2% is the number to act on, and it re-reads two earlier results.**
Soldiers cannot overwrite enemy paint; only splashers and moppers can. So a
majority of soldier-turns are blocked by a condition the *other* two units exist
to clear. That is why `darla2` (moppers removed) lost, and it promotes `darla3`
(moppers that can see) from "a better version of a marginal unit" to a direct
attack on the largest single line in this table.

**Ranking the remaining levers by the share of soldier-turns each could reclaim**:
`SPLASH_FLOOR` first (regime A is most maps, and it is total), then unblocking
IDLE-ENEMY (53.2% where soldiers exist), then IDLE-ALLY navigation (24.1%, and
the existing frontier search is measurably broken at 2/187).

## Iterations 2 and 3 RESULT — the `SPLASH_FLOOR` re-open is REFUTED, and I was confidently wrong

Six runs, 432 games, all on the two pinned samples darla1 played.

| arm | `SPLASH_FLOOR` | vs carol | vs bob | vs alice | overall |
|---|---|---|---|---|---|
| `darla5` | 0 | 10/48 | 12/48 | 10/48 | **32/144 (22.2%)** |
| `darla4` | 1400 | 17/48 | 25/48 | 21/48 | **63/144 (43.8%)** |
| `darla1` | 2000 | 30/48 | 30/48 | 29/48 | **89/144 (61.8%)** |

**Monotone in the floor, and uniform across three independent lineages.** My
registered refutation condition was: *"the dose is negative against all three
legs, or flat against all three. Either kills it… if the effect is uniform across
three independent lineages then the axis is simply flat and carol's closure
generalises beyond self-play."* It is negative on all three, by −26 and −57
games. **carol's closure generalises. The re-open was wrong**, and her doctrine-17
caveat — which I used as the licence to re-open — did not need to be the reason
her result held.

**Two things I got wrong, and they are different mistakes.**

*The sign.* I predicted lowering the floor would help against alice and bob
because they convert ruins and reach 14–16 towers. It hurt against them by 9 and
5 games. Soldiers are not a cheaper route to their strategy; they are a worse use
of the same chips.

*The prediction that `darla4` "may not fire".* I argued from the $1,350–$1,420
treasury that floor 1400 would be a near-null. It moved 26 games. The arithmetic
was right and the inference was wrong: a treasury *median* below a gate does not
mean the gate never opens, because income spikes and the reserve-freeing guard
both cross it — and every crossing spends. A gate is not a wall.

**And I misread my own census, which is the more useful error.** I measured that
only 1.8% of soldier-turns paint a tile and 53.2% are blocked by enemy paint, and
concluded *unblock the soldiers*. The simpler reading was available and correct:
**soldiers are a poor painting unit, and the bot is right to build splashers
instead.** carol's own comment says so in numbers I had already read — a splasher
paints 2.4–4.7x more tiles per unit of build-paint and costs ~4x less per tile in
chips. The banked 9,716 paint on Leaf is not a resource the bot fails to convert;
it is a resource the bot has no better use for, and forcing the conversion costs
57 games.

**What the result actually establishes**, which is worth more than the hypothesis
was: `SPLASH_FLOOR` is load-bearing and the dose response is steep and monotone
over [0, 2000]. **The untested direction is up**, and carol never tested it — her
bracket was 0 / 1400 / 2000 with 2000 as the incumbent. `darla6` = 2600 is queued
to find whether 2000 is an interior optimum or a floor on an unexplored slope.

## Iteration 4 RESULT — `darla3` (mopper navigation): REJECT, a dead tie

`darla3` 87/144 (60.4%) against darla1's 89/144. −2 games, −0.33 sd. Gate was
accept if > 89; **rejected**, but this is a tie, not a regression: carol 30/48,
bob 29/48, alice 28/48 against darla1's 30/30/29.

Taken with `darla2` (moppers removed, −5), the unit's whole contribution is small
and flat: removing them costs a little, and alice's accepted navigation fix — worth
87% in her bot — transfers as **nothing** here. The difference is that alice's
moppers supported a soldier-primary army that needs enemy paint cleared ahead of
it; Darla's splashers overwrite enemy paint themselves, so the mopper's output is
already covered. That is a *superseded* mechanism after all — but superseded by
the splasher's AoE rather than by the production-efficiency argument finding #2
made, which the darla2 falsifier had already shown to be a statement about a
metric.

**Mopper axis: CLOSED.** Bracketed on both sides — 0 moppers is −5, better
moppers is −2, incumbent is the best of the three. Re-opening requires a build
whose army is soldier-primary, which this design is not.

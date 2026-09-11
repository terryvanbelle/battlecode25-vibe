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

## Iterations 5 and 6 RESULT — `SPLASH_FLOOR` has an INTERIOR OPTIMUM, and the axis is closed

| arm | `SPLASH_FLOOR` | overall |
|---|---|---|
| `darla5` | 0 | 32/144 (22.2%) |
| `darla4` | 1400 | 63/144 (43.8%) |
| **`darla1`** | **2000 (inherited)** | **89/144 (61.8%)** |
| `darla6` | 2600 | 81/144 (56.2%) |

**The curve rises to 2000 and falls past it.** So the response is not monotone
after all — it has an interior optimum, and carol's inherited constant is sitting
on it. Her bracket (0 / 1400 / 2000) found the right value without ever testing
above it; I tested above it, and above is worse by 8 games.

**`SPLASH_FLOOR`: CLOSED, bracketed on both sides.** 0 (−57), 1400 (−26),
2600 (−8), incumbent 2000 best of four doses across 576 games. Re-opening
requires a different *army composition*, not a different dose — the constant
prices soldiers against splashers, so it can only move if what those units are
worth changes.

## Iteration 7 RESULT — `darla7` (`SPLASH_MIN_SCORE` 8 → 4): **REJECT**, −11

78/144 (54.2%). Splashers firing at half the previous score threshold is worse by
11 games, −1.8 sd. The `lowScore` census that motivated it (34 of 142 splasher
decisions withholding fire) measured a real behaviour and priced it wrong: a
splash below the threshold is not free coverage, it is 50 paint spent for few
tiles, and paint is the binding resource for a splasher-primary army. **The
threshold is doing the same job as `SPLASH_FLOOR` one level down** — protecting a
scarce resource from a cheap-looking use — which is the third time this design
has punished me for reading a withheld action as a wasted one.

**Standing after seven arms and 1,008 matched games: the inherited build is still
the best thing measured.** Every axis I have opened — moppers (both directions),
`SPLASH_FLOOR` (both directions), splash threshold — has closed at or below the
value carol shipped. That is worth stating plainly rather than burying: Darla's
gain over the lineages came from *combining* carol's economy with her unadopted
siege, and none of my seven subsequent single-constant changes has improved on it.

## Registration — iteration 8, the unreachable frontier branch (`darla8`)

Written before any game. Baseline `darla1` = 89/144.

**The defect is structural, not a dose.** The frontier-seeking branch is guarded
by `if (foe == 0)` — it only runs when there is *no* enemy paint within r²=9. The
census says 53.2% of soldier-turns are IDLE-ENEMY, i.e. exactly the turns where
`foe > 0`. So on the majority of idle turns the soldier never looks for anywhere
better to be, and keeps whatever stale heading it had while standing on ground it
cannot use. `darla8` removes the guard.

**Why this arm is a different shape from the seven that failed.** Every previous
arm moved a constant that prices one unit against another, and each one closed at
or below carol's shipped value. This one **spends nothing** — no build, no attack,
no extra paint. It redirects a move that already happens. That is the
"capability preserved at zero marginal cost" profile, which is the shape of every
mechanism that has ever been accepted in this project (alice's iteration 7 mopper
navigation, carol's iteration 12 navigation result).

**My prior is still that it loses.** Seven of seven arms have been rejected, and
three times now I have read a withheld or blocked action as a wasted one and been
wrong. Registering that here so the result is read against an honest expectation
rather than a hopeful one.

**Mechanism check, read before the win rate**: `frontFound` / `frontNone` in the
indicator string. In darla1 the branch reached 187 turns and found a target twice.
darla8 must reach materially more turns; if `frontFound` stays near zero, the
branch is being reached and there is genuinely no visible empty ground, which
makes the arm **untested** rather than refuted and points at vision range rather
than the guard.

**Gate**: accept if > 89/144 with no leg below 50%; reject if <= 89/144 with the
mechanism firing.

## Standing arrangement so the machine is never idle (2026-09-11, user requirement)

Three pieces, in order of how much they depend on a session being awake.

**1. `tools/arm-runner.sh` — the work queue.** Drains
`progress/pending-arms.txt`, one package per line, each run on BOTH pinned
samples so every result is a matched pair against the 89/144 baseline. Adding a
line starts a gauntlet with no session involved. It holds a flock (a second
launch is a no-op), is setsid-detached (survives session death), and skips any
arm that already has 144 collated games rather than paying twice for the same
measurement.

**2. `tools/idle-filler.sh` — the guarantee.** The runner's failure mode is that
it *waits* when the queue empties, so if the last arm lands while nobody is
awake the machine sits idle. The filler removes that dependency: whenever the
queue is empty and no gauntlet is in flight, it runs a **fresh random 25-map
sample of the shipped baseline against the three frozen lineages** and records it
into `progress/vs_old_bots_history.csv`.

That job is chosen so it is never wasted and always safe to run unattended:
fresh random maps each time (so it is not an overfitting surface — the pinned
samples are for matched pairs, this is for absolute strength), frozen opponents
(so a moving line is real change rather than a moving instrument), and it extends
the one time series in this workspace that currently has a single date on it. It
never touches `src/`, never commits, and cannot change what plays anywhere.

**3. A persistent monitor** on both logs, filtered to `ARM COMPLETE`,
`ARM ERROR`, `ARM SKIP`, `QUEUE IDLE`, `FILLER COMPLETE`, `FILLER ERROR`,
`FILLER WARN` — so a finished arm wakes the session immediately instead of
waiting to be noticed. The filter deliberately covers the failure signatures too:
a monitor that watches only for success is silent through a crash, and silence
looks exactly like "still running".

**One thing already answered without an arm.** DESIGN.md asserted the siege
"costs nothing observable". That was untested when written, but it does not need
an ablation: `darla1` is carol's economy **plus** the siege, carol is in the
opponent pool frozen, and darla1 beats carol **30/48 (62.5%)**. The siege is the
only difference between them, so it is worth roughly +12 points, measured.

## Iterations 8 and 9 RESULT — both navigation arms REJECT, and the replay names the real lever

| arm | change | vs carol | vs bob | vs alice | overall |
|---|---|---|---|---|---|
| `darla8` | frontier guard removed | 20/48 | 30/48 | 29/48 | **79/144 (54.9%)** −10 |
| `darla9` | idle soldiers head for enemy paint | 24/48 | 28/48 | 27/48 | **79/144 (54.9%)** −10 |

**The mechanism fired — this is not an untested arm.** As registered, the counter
was read before the score. On DefaultHuge, rounds 600–630:

| | darla1 | `darla8` |
|---|---|---|
| turns reaching the frontier branch | 187 | **591** |
| `frontFound` | 2 | **41** |
| dry, commuting home | 17.8% | **28.0%** |

The guard removal did exactly what it was designed to do. It is the fourth
"mechanism confirmed, value nil-or-negative" result in this project.

**And the same replay contains the finding that matters.** darla8 vs carol on
DefaultHuge, at round 2000:

| | darla8 | carol |
|---|---|---|
| towers | **19** | 4 |
| soldiers | **64** | **0** |
| splashers | 0 | 7 |
| chips | **$27,300 unspent** | $1,560 |
| **coverage** | **263, falling from 456** | **691, rising** |

**Darla wins the tower race 19–4, fields 64 soldiers against zero, and loses the
coverage race to seven splashers.** That is the *second* registered refutation
branch from the original thesis, hit exactly: *"Darla wins the ground race and
still loses."*

**Why, mechanically.** The spawn mix is a roll: `SPLASHER_IN_20 = 3` (15%),
mopper 2, soldier the remaining 75%. `SPLASH_FLOOR` only forces splashers while
chips are *scarce* — it blocks non-splashers below a threshold. At $27,300 the
floor never binds, so the realized mix relaxes to the **intended** 75% soldier,
and 75% soldier is the wrong army. Six or seven splashers painting up to 13 tiles
per action out-paint 64 soldiers painting one.

**So the axis I have been on was the wrong one the whole time.** Every arm so far
moved when soldiers may be built. The lever is **how many splashers are built at
all**, and `SPLASHER_IN_20` has never been touched — it sits at carol's 3.

**Queued**: `darla10` (splasher share 15% → 40%) and `darla11` (15% → 70%).
Registered prediction: if the reading above is right, both beat 89/144 and the
curve is *increasing* in splasher share, opposite in sign to every dose ladder so
far. If both lose, the mix is not the lever either and the coverage gap is coming
from somewhere I have not yet measured.

## Instrument check, produced by the idle filler rather than planned

The filler's standing job — a fresh random 25-map sample of the shipped baseline
against the three frozen lineages — landed as run `20260911-041301`, and it
answers a question I had been assuming rather than testing: **how much of the
matched-pair signal is map-sample luck?**

| | pinned samples (144 games) | fresh 25-map sample (150 games) |
|---|---|---|
| overall | 89/144 — **61.8%** | 97/150 — **64.7%** |
| vs carol | 62.5% | 62.0% |
| vs bob | 62.5% | **72.0%** |
| vs alice | 60.4% | 60.0% |

**The aggregate replicates**: 61.8% against 64.7% on disjoint map sets, a 2.9-point
gap against a binomial sd of ~4.2 points at this n. So map-sample variance is not
swamping the instrument, and the nine rejections measured on the pinned samples
stand — a −10 or −26 game margin is not an artefact of which twelve maps were
drawn.

**Two of the three legs replicate almost exactly** (carol 62.5 → 62.0, alice
60.4 → 60.0). **bob's moves 9.5 points**, which at n=48 is 1.3 sd — inside noise,
but it is the concrete reason not to read a single opponent leg as a result. I
have been saying that in registrations; this measures it.

Neither of these numbers is a new capability. The point is that the filler was
designed as "never waste the VM" and its first output was a control I would not
have scheduled, because I did not notice I was assuming it.

## Iteration 10 RESULT — `darla10` (splasher share 15% → 40%): **REJECT**, −11

78/144 (54.2%). carol 26/48, bob 30/48, alice 22/48. My registered prediction was
that this curve *rises*. It fell, and that makes ten arms rejected out of ten.

**But the mechanism read says the arm did not test what I aimed it at.** Build
events on DefaultHuge:

| round | soldiers built | splashers built | splashers alive | coverage |
|---|---|---|---|---|
| ~600 | 32 | **67** | 23 | 552 |
| ~1200 | 227 | 52 | 7 | 423 |
| ~2000 | 113 | **0** | **0** | 284 |

The raised roll worked *early* — 67 splashers against 32 soldiers in the opening.
Then splasher production **falls to zero** while chips sit at $28,850. Tower paint
at that point is 1,361 across 25 towers: **~54 per tower, against a splasher's 300
paint cost.** The roll asks for a splasher and the tower cannot pay, every time.

**So the binding resource in the late game is per-tower paint, not chips or the
roll** — and the reason the tower never accumulates 300 is a dynamic carol already
documented one unit lower down. Her `PAINT_FLOOR` exists because a MOPPER (100)
crosses its paint line before a SOLDIER (200) can, resetting the stash, so the
expensive unit is never afforded: *"the cheap unit does not merely get built more
often — it PREVENTS the expensive one from ever being afforded."*

**Exactly that runs one level further up, and nothing guards it.** SOLDIER (200)
crosses before SPLASHER (300). carol's floor protects soldier from mopper; no
floor protects splasher from soldier.

**Queued**: `darla12` (splasher paint floor 300) and `darla13` (150), the exact
analogue of `PAINT_FLOOR` one unit up.

**Registered risk, because this is the shape that has burned me twice.** A floor
of 300 requires a tower to hold 500 before it may build a soldier, against an
observed ~54. That is "a constant set above the level its resource normally
holds" — the error DESIGN.md opens with, and the error that made `darla5` a
57-game loss. The counter-argument is that ~54 is an *equilibrium of the current
rule* rather than a capacity limit (tower paint caps at 1,000 and accrues 5–10 a
turn), so the floor changes the level it is measured against. That argument is
exactly the one carol corrected me on once before, so `darla13` at 150 is carried
as the milder dose and **the pair is read as a ladder, not as two chances at a
win.** If both lose, the reading above is wrong and per-tower paint is a capacity
ceiling rather than a queueing artefact.

## Iteration 11 RESULT — `darla11` (splasher share 70%): +2, and that is NOT an accept

91/144 (63.2%). carol 31/48, bob 32/48, alice 28/48 — all three legs above 50%,
and 91 > 89, so it passes the letter of its gate. **I am not accepting it.**

+2 at n=144 is **0.33 sd**. Doctrine: distrust any delta under the noise floor
regardless of how good the story is, and the story here is good, which is exactly
when that rule earns its keep. carol's iteration 10 died on this same point.

**The ladder is U-shaped, which is the interesting part:**

| `SPLASHER_IN_20` | share | result |
|---|---|---|
| 3 | 15% | 89/144 (baseline) |
| 8 | 40% | **78/144 (−11)** |
| 14 | 70% | 91/144 (+2) |

A smooth axis should not dip in the middle. Two readings:

1. **The axis is flat and 78 is a fluctuation** (−1.8 sd). Then splasher share
   does not matter and my whole mechanism story is wrong.
2. **The dip is real and mechanical**, and it is the same paint-queueing effect
   `darla12`/`darla13` were built for: at 40%, soldier builds are frequent enough
   to keep tower paint below a splasher's 300 cost, but splasher rolls are too few
   to compensate — the worst of both. At 70%, soldiers are rare enough that towers
   actually accumulate to 300, so the splashers that are rolled can be paid for.

Reading 2 predicts that `darla12`/`darla13` (which protect splasher paint
directly) make the *low* splasher shares work, and it is testable rather than
decorative.

**Queued: an independent replication of `darla11` on a FRESH random 25-map
sample** (`tools/replicate.sh`), waiting behind the pending arms so it never
competes with them. The pinned pair is the ground `darla11` was screened on, and
a +2 selected there is exactly the number that does not survive new ground. The
comparison is like-for-like because the baseline's own fresh-sample score is
already measured: **97/150 (64.7%)** on run `20260911-041301`. So `darla11` has
to beat ~97/150, not 89/144.

## Iteration 12 RESULT — `darla12` (splasher paint floor 300): **REJECT**, −15, exactly as registered

74/144 (51.4%). carol 24/48, bob 27/48, alice 23/48.

**The registered risk is what happened, and the mechanism read confirms it rather
than the theory.** Build events on DefaultHuge:

| round | soldiers built | splashers built | towers | coverage |
|---|---|---|---|---|
| 600 | **0** | 36 | 5 | 240 |
| 1200 | **1** | 34 | 3 | 257 |
| 1534 | **1** | 19 | 4 | 248 |

The floor **did** protect splasher paint — splashers were built steadily. It also
built **essentially zero soldiers all game**, and only soldiers call
`workOnRuin`, so the tower count collapsed to 3–5 against the baseline's 15–25
and coverage never left ~250. A 300 floor requires a tower to hold 500 before a
soldier may be built, against an observed ~54. That is the `darla5` error
repeated at the resource one over, in the place I said it might be.

**Soldiers have a dual role, and that is the finding.** They are poor *painters*
— 1.8% of their turns paint a tile — but they are the **only** unit that converts
a ruin into a tower, and towers are the entire paint economy. Any rule that
prices soldiers purely as painters will delete them and take the economy with it.
That resolves the apparent contradiction between `darla5` (more soldiers, −57)
and `darla12` (no soldiers, −15): **soldier count has an interior optimum, and
carol's constants are sitting on it.**

## Standing conclusion after twelve arms

| axis | tested | verdict |
|---|---|---|
| `SPLASH_FLOOR` | 0, 1400, **2000**, 2600 | interior optimum at the inherited value |
| moppers | none, better nav, **incumbent** | bracketed both sides, incumbent best |
| `SPLASH_MIN_SCORE` | 4, **8** | incumbent |
| soldier navigation | 2 mechanisms, both fired | both −10 |
| `SPLASHER_IN_20` | 15%, 40%, 70% | U-shaped; +2 at 70% is inside noise |
| splasher paint floor | 300, 150 pending | 300 deletes the economy |

**Every constant axis reachable in this build is at a local optimum, and the
optimum is the value carol shipped.** Twelve single-mechanism arms, 1,700+
matched games, and the best measured result is still the inherited build. Darla's
one real gain over the lineages remains the *combination* she started from —
carol's economy plus the siege carol built and never adopted, worth about +12
points against carol herself.

**Two operational facts learned the hard way:**

1. **Replays expire.** `driver-prune.sh` deletes `.bc25` blobs, `losses/`
   included, once a run is old enough. The baseline runs' replays are already
   gone, so the soldier-turn census above cannot be re-run on them. **A mechanism
   census has to be taken while the run is fresh**, not queued for later.
2. **Upgrades are not the gap.** On a rich map darla performs 24 paint-tower
   upgrades against 1 money-tower, alice the reverse (23 money, 13 paint). Given
   per-tower paint is the binding resource, darla's split is the correct one and
   is already happening — so the paint shortage is a *flow* limit (25 towers at
   ~10/turn against a splasher's 300), not an unspent-chips failure.

**Queued**: `darla14` at 55% splasher share, to fill the gap between 40% (−11)
and 70% (+2). If 55% lands near the baseline, the U was noise and the axis is
flat; if it dips, the dip is real and mechanical.

## Iteration 13 RESULT — `darla13` (splasher paint floor 150): **REJECT**, −8. Axis closed.

| splasher paint floor | result |
|---|---|
| none (inherited) | 89/144 (61.8%) |
| 150 | 81/144 (56.2%) — **−8** |
| 300 | 74/144 (51.4%) — **−15** |

**Monotone decreasing, so this is a bracket and not a near-miss.** The milder
dose was carried precisely so that a loss at 300 could not be explained away as
"the right idea at the wrong level", and 150 loses too, proportionately. The
paint-queueing theory is **refuted**: protecting splasher paint does not help at
any dose, because the paint it protects is taken from the unit that builds the
economy. **CLOSED.**

## Disk: the run queue nearly killed itself, and the cause is not this project

The driver's root filesystem hit **100% (6.6M free)** and a `git commit` failed
with ENOSPC mid-session. Cause, measured:

| | size |
|---|---|
| `/Users/terryvanbelle/projects/vibe_bc26/gauntlet` | **18G** |
| this entire project | 2.1G |
| our gauntlet replays specifically | 1.25G |

The 18G is the **archived BC26 project's** replay data on a 30G disk. It is
another project's recorded results, so deleting it is the owner's decision and
has been put to them; nothing here touches it.

What was done instead, all within this project:
- ran the sanctioned `driver-prune.sh` at `KEEP_RUNS=1 MIN_AGE_MIN=20`,
  reclaiming **704M** (950M free, 97%);
- verified first that the 34 **git-tracked** replays live in `agents/*/replays/`,
  which the prune tool never touches — only `gauntlet/` and `matches/` blobs go;
- added `tools/disk-guard.sh`, a detached loop that runs the same tool whenever
  free space drops below 2GB, and shouts `DISK CRITICAL` if pruning everything we
  own still leaves under 400MB.

**Why a guard rather than a one-off prune**: the "never idle" arrangement turns
runs over several times an hour, each writing 40–70MB of lost games. The hourly
`bc25-driver-prune` timer keeps two runs per workspace and spares anything under
an hour old — sized for a much slower loop. Without the guard the queue would
have filled the disk again within the hour and every subsequent gauntlet would
have died on ENOSPC, which is the same outcome as being idle, arrived at less
visibly.

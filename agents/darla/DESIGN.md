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

## Iteration 14 — **VOID**, not a result. A build that never ran.

`darla14` returned **0/144**, every game lost to "destroyed all of the enemy
team's units". That is not a score, it is a bot that never loaded.

**Cause**: `src/darla14/RobotPlayer.java` was a **byte-identical copy of the
baseline**. The `sed` that should have set `SPLASHER_IN_20 = 11` matched nothing,
so the file kept `package darla;`; the classes compiled into package `darla`, the
engine looked for `darla14.RobotPlayer`, found nothing, and forfeited 144 games.

**Why the existing check did not catch it, which is the part worth keeping.** I
verify each arm with `javac ... && echo COMPILE_OK`, and it printed `COMPILE_OK`
— because it compiled *the baseline* under a new directory name. A compile step
cannot detect that a file was not edited. The real signal was that my
verification `grep` printed **nothing**, and I read the `COMPILE_OK` on the next
line as success. **A verification whose failure mode is silence is not a
verification.**

**Fixed structurally, not by intending to be careful**: `tools/make-arm.sh` now
builds every arm and refuses to leave it on disk unless

1. the package line actually names the arm,
2. the `BUILD` constant actually names the arm,
3. the intended change is present, and
4. the diff against the baseline below the package line is non-empty.

Any failure deletes the directory, so a broken arm cannot reach the queue. The
guard was tested against a deliberately non-matching `sed` and correctly refused.
The compile check now also lists the output directory, so the package landing in
the wrong place is visible.

**The two void runs are quarantined**, `bot=` rewritten to `darla14VOID` with a
`VOID.md` beside each, so `plot_arms.py` cannot aggregate them. The evidence is
kept; the number is excluded. **`darla14` has been rebuilt correctly and requeued**
— the 55% question is still open and still unmeasured.

**What made it visible was the result being impossible.** A one-constant change
cannot lose 144 of 144. Worth holding onto as a check: a result far outside what
the mechanism could produce is a bug report about the harness, not a finding.

## `darla11` replication — two independent looks, both small, neither decisive

`tools/replicate.sh` ran `darla11` on a **fresh random 25-map sample**, ground it
was never screened on, and the idle filler independently added a second baseline
point on another fresh sample. So the comparison is now like-for-like on both
sides:

| build | pinned pair | fresh sample A | fresh sample B |
|---|---|---|---|
| baseline `darla1` | 89/144 (61.8%) | **97/150 (64.7%)** | **94/150 (62.7%)** |
| `darla11` (70% splasher) | 91/144 (+2) | **99/150 (66.0%)** | — |

**The baseline's own two fresh samples differ by 3 games** (97 vs 94, 0.49 sd).
That is the run-to-run noise of this instrument, measured rather than assumed —
and `darla11` is **+3.5 games over the baseline's mean of 95.5**, which is 0.57 sd
and *the same size as the baseline's disagreement with itself*.

Pooled over everything either build has played: `darla11` 190/294 (64.6%) against
the baseline's 280/438 (63.9%). **+0.7 points.**

**Verdict: not accepted, and not rejected either — indistinguishable.** Two
independent looks both lean positive, which is weakly encouraging and nothing
more. I am recording it that way rather than banking a +2 as a win, because a
0.5 sd effect is exactly what this instrument cannot resolve, and because the
honest description of a 0.7-point difference is "the same".

**And I will not settle it on the benchmark.** Running `darla11` against `v3` and
picking whichever scores higher would be tuning against the yardstick — the one
thing the benchmark rule exists to prevent. The benchmark measures what ships; it
does not choose it. Whatever wins on lineage evidence gets benchmarked, in that
order.

## Registration — iteration 15, siege target priority (`darla15`)

The siege currently ranks **money towers above paint towers**, from carol's
finding #5: killing the last money tower freezes the victim's production
permanently (1,887 frozen rounds measured).

**But the win condition is coverage in 96.5% of games, and the census says
per-tower PAINT is the binding resource** — for both sides. A paint tower is what
feeds the opponent's splashers, and splashers are what win the coverage race:
carol took 691 coverage off seven splashers while darla held 19 towers and 64
soldiers. Killing money slows their *economy*; killing paint slows the units that
actually take ground.

One line: `rank = (moneyPerTurn > 0) ? 1 : 2`, inverting the priority. Built
through `tools/make-arm.sh`, so the change is verified present rather than
assumed.

**Gate**: accept if > 89/144 on the pinned pair AND the fresh-sample replication
clears the baseline's 95.5/150 mean by more than its own 0.49 sd spread. Two
hurdles deliberately, because `darla11` has just shown what a single +2 is worth.

## Iteration 14 (rebuilt) RESULT — the dip is REAL, and the axis is bimodal

| `SPLASHER_IN_20` | splasher share | soldier share | result | |
|---|---|---|---|---|
| 3 | 15% | 75% | 89/144 (61.8%) | baseline |
| 8 | 40% | 50% | 78/144 (54.2%) | **−11 (−1.83 sd)** |
| 11 | 55% | 35% | 81/144 (56.2%) | **−8 (−1.33 sd)** |
| 14 | 70% | 20% | 91/144 (63.2%) | +2 (+0.33 sd) |

**Two adjacent interior points, both negative, independently measured.** Pooled,
40% and 55% together are **−19 over 288 games, −2.24 sd** — well past the noise
floor, and far more credible than the single −11 that I nearly wrote off as a
fluctuation when `darla11` came back positive.

**So the axis is bimodal, not flat and not single-peaked.** Two workable regimes
with a bad valley between them:

- **soldier-heavy (15%)** — soldiers claim ruins, towers accumulate, the economy
  compounds; the inherited setting;
- **splasher-heavy (70%)** — few enough soldiers that towers actually reach a
  splasher's 300 paint, and splashers take ground far faster than soldiers;
- **the middle (40–55%)** — enough soldiers to keep tower paint below 300, too
  few splasher rolls to compensate. The worst of both, which is exactly the
  mechanism `darla10`'s build-event census pointed at.

This is the first axis in Darla's work that is not simply "carol's value is
best". carol's 15% is one of two optima rather than the only one, and the
alternative is at least its equal.

**Note what the void nearly cost.** The broken `darla14` returned 0/144 and, had
I aggregated it, would have drawn this ladder as a cliff at 55% — an artefact
with a tidy story available (*"too few soldiers, economy collapses"*) that would
have looked like a finding and been entirely a build error.

**Queued**: `darla16` at 80% splasher (10% soldier, 10% mopper) — the ladder is
*rising* from 55% to 70%, so the upper edge is the untested direction. It is
bounded: `darla12` established that driving soldiers to zero deletes the economy,
so 80% is probed and 90%+ is not.

## Iteration 15 RESULT — `darla15` (siege hits paint towers first): **exact tie**, 89/144

carol 29/48, bob 30/48, alice 30/48, against the baseline's 30/30/29. Not −1 or
+1 in any meaningful sense: the same bot.

**An exact tie is a finding when it is this exact**, and the replay says why.
Tower counts through a full 1,886-round game, `darla15` vs alice on DefaultHuge:

| round | alice towers | darla towers |
|---|---|---|
| 500 | 23 | 23 |
| 1000 | 24 | 24 |
| 1500 | 25 | 24 |
| 1886 | 25 | 24 |

**Monotone increasing on both sides. No tower is destroyed by either team, in the
entire game.** The siege's target *priority* cannot matter when the siege never
completes a kill — which is why inverting it changed nothing, and it is a
stronger version of the earlier observation that enemy tower counts "rise".

**So what is the siege worth, given darla1 beats carol by ~12 points and the
siege is the only difference between them?** It cannot be tower removal. The
remaining candidate is **positioning**: the firing-ring movement holds splashers
at r²=10–16 of enemy towers, which is deep in contested territory, and splashers
paint wherever they stand. The value is plausibly that the siege walks the
coverage engine to the right part of the map, and the tower-killing rationale it
was built on is incidental.

**That reframes the design.** DESIGN.md's thesis was "tower removal is the lever",
refuted on the win condition at 96.5% coverage. This is the second, sharper
refutation: tower removal does not merely fail to win games, **it does not
happen at all**.

**Queued: `darla17`, the discriminating experiment.** The splash scorer adds
+100/+60 for a tower inside the blast. If no tower ever dies, that bonus diverts
AoE onto 1,000-HP targets that absorb it harmlessly, instead of onto paint. So:
**keep the firing-ring movement, remove the tower bonus from splash scoring.**

- If `darla17` ≥ baseline, the siege's value is **positioning**, the tower-kill
  scoring was a tax, and the mechanism should be renamed and rebuilt around
  contested ground.
- If `darla17` < baseline, the tower bonus is doing something real that tower
  *counts* do not reveal — most likely suppressing tower attacks by keeping them
  damaged, or drawing enemy units to defend.

Either way it separates the two explanations, which no result so far has.

## Iteration 16 RESULT — `darla16` (80% splasher): −3. The axis is fully mapped and CLOSED.

| splasher / soldier | arm | result | |
|---|---|---|---|
| 15% / 75% | `darla` | 89/144 (61.8%) | inherited |
| 40% / 50% | `darla10` | 78/144 | −11 (−1.83 sd) |
| 55% / 35% | `darla14` | 81/144 | −8 (−1.33 sd) |
| **70% / 20%** | `darla11` | **91/144** | +2 (+0.33 sd) |
| 80% / 10% | `darla16` | 86/144 | −3 (−0.50 sd) |

**Five doses, 720 matched games, and the second mode turns over.** 70% is the
peak of the splasher-heavy regime and 80% falls back — so the upper edge is not
an unexplored slope, it is a summit already passed.

**The axis is bimodal with two statistically indistinguishable optima** (89 and
91, 0.33 sd apart) separated by a real valley (40% and 55% pooled: −19 over 288
games, −2.24 sd). **CLOSED**: no setting beats the inherited value by anything
this instrument can resolve, and both ends now turn over.

The honest summary is that carol's 15% is *one of two* equally good answers, not
the unique one — a finding about the shape of the problem rather than an
improvement to the bot.

**Charting generalised**: `tools/plot_arms.py` now draws a dose-response for
every axis with three or more measured points, reading the shipped baseline's
position on each axis from `progress/baseline-doses.txt` so the inherited value
appears as a point rather than only as a line. Three ladders are drawn today
(`SPLASHER_IN_20`, `SPLASH_FLOOR`, `SPLASH_PAINT_FLOOR`).

## The instrument's resolution, measured — and what it means for every gate here

The idle filler has now produced **three independent fresh-sample baseline runs**,
which is enough to stop assuming the noise floor and measure it.

| baseline, fresh random 25-map sample | |
|---|---|
| `20260911-041301` | 97/150 (64.7%) |
| `20260911-052326` | 94/150 (62.7%) |
| `20260911-063718` | 101/150 (67.3%) |
| **pooled** | **292/450 (64.9%)** |

**Observed run-to-run sd: 2.34 points. Range: 62.7–67.3.** (The binomial estimate
at n=150 is 4.08 points, so binomial is a conservative upper bound here, as it
should be.)

**`darla11`'s replication was 99/150 = 66.0% — inside the baseline's own range.**
That settles it properly: the +2 on the pinned pair and the +3.5 on a fresh
sample are both smaller than the baseline's disagreement with itself. `darla11`
is **not an improvement**, and I now have the measurement to say so rather than
the intuition.

**The strategic consequence is uncomfortable and worth stating plainly.** A
150-game fresh sample cannot resolve anything under about **5 points** (2 sd).
Every result this project has produced falls into two classes:

- **big and obvious** — `darla5` −57, `darla12` −15, `darla17` −17. All real, all
  far outside the floor, and all *losses*.
- **inside the floor** — every candidate that looked like a gain: +2, +3, +0.7.
  None of them survives contact with the instrument.

So the honest position after seventeen arms is not "nothing works", it is:
**this instrument can only see damage, not improvement, at the sizes I have been
producing.** Detecting a real +3% would need on the order of a thousand games per
arm, which at current throughput is hours per candidate rather than minutes.

That reframes what remaining effort is worth spending. Chasing +2s with 144-game
screens is measuring noise. The two things that are worth doing are (a) changes
large enough to clear the floor — which historically have been *mechanisms*, not
constants, and (b) making the instrument cheaper or sharper, because right now it
is the binding constraint on learning rather than the VM.

## Iteration 18 RESULT — `darla18` (attractor doubled): **exact tie**, 89/144. The attractor is a SWITCH, not a dial.

| tower bonus | arm | result |
|---|---|---|
| 0 | `darla17` | 72/144 — **−17 (−2.83 sd)** |
| 100/60 | `darla` | 89/144 — inherited |
| 200/120 | `darla18` | 89/144 — **+0, exactly** |

Doubling the attractor changes **nothing**, to the game. That is mechanically
right rather than surprising: the paint terms in the splash scorer are small
integers, so a +100 tower term already dominates any centre comparison the moment
a tower is in range. Beyond the threshold where it wins, its size is irrelevant.

**So the axis is binary: having the attractor is worth 17 games, its magnitude is
worth nothing.** `darla19` at 50/30 is running to find where the switch flips —
almost certainly still "on", which would put the threshold below 50.

**This is the useful shape of the finding.** A parameter that looks like a dial
and behaves like a switch has one bit of information in it, and I have now spent
three arms extracting that bit. It is also the clearest possible sign that
further dose work on this axis is worthless.

## Registration — iteration 20, generalise the attractor (`darla20`)

The one mechanism measured to pay in this design is **positioning**, and it
currently has a hard range limit: `siege` is only non-null when an enemy tower is
in vision (r²=20). With no tower in sight the splasher calls
`moveExploring(null)` and **wanders at random — no heading at all.**

`darla20` gives it one: when no tower is visible, head for the **nearest enemy
paint in vision**. Enemy paint is the same signal the tower bonus is a proxy for
— "the opponent's ground is over there" — without the range limit.

**Why this is not `darla9` again.** `darla9` gave soldiers exactly this heading
and lost 10 games. The difference is capability, and it is a real prediction
rather than an excuse: **a soldier cannot overwrite enemy paint** (53.2% of
soldier-turns are IDLE-ENEMY for precisely that reason), so walking one toward
enemy paint walks it toward ground it can do nothing with. A splasher's AoE
overwrites enemy paint directly. The same heading should therefore be worthless
for soldiers and useful for splashers — and if `darla20` also loses, that
prediction is wrong and positioning does not generalise beyond towers.

**Read against the measured floor**: the instrument cannot resolve under ~5
points, so this is worth taking seriously only if it moves by more than the −17
/ +0 scale already seen. A +2 here means nothing.

**Mechanism check first, as always**: the build tags `lure` when it takes the new
heading and `roam` when it falls through. If `lure` is rare, no tower-free
splasher-turns exist and the arm is untested rather than refuted.

## Iteration 19 RESULT — and the arms were NO-OPS, provably, which I could have known statically

`darla19` (attractor 50/30): **89/144, +0.** Completing the ladder:

| tower bonus | result |
|---|---|
| 0 | 72/144 — **−17** |
| 50/30 | 89/144 — +0 |
| 100/60 | 89/144 — inherited |
| 200/120 | 89/144 — +0 |

**Then I checked whether these were merely equal in score or equal in play.**
Comparing per-game rows against the baseline on the identical pinned sample:

    darla19 vs baseline: 0 differing game rows
    darla18 vs baseline: 0 differing game rows

**Byte-identical games** — every map, every side, same winner, same round count.
`darla18` and `darla19` are not "ties", they are the baseline. 288 games bought
zero information.

**And it was determinable by reading the scorer.** The paint terms are +3 per
enemy tile within r²≤2 of the centre (9 such tiles) and +2 per empty tile in
r²≤4 (4 more), so the **maximum achievable paint score is 9x3 + 4x2 = 35.** Any
tower bonus above 35 wins the argmax outright whenever a tower is in range, and
changing it cannot alter which centre is chosen. 50, 100 and 200 are *all* above
35, so all three were guaranteed no-ops before a single game was played.

**The practice this earns, stated so it is not just an apology**: before queueing
a dose, check whether the term can change the decision it feeds. A constant that
already dominates its competitors has no dose-response — it has a threshold, and
the only informative doses are near that threshold. This is the cheap static
analogue of the mechanism check I already do on results, moved to before the run.

**Queued: `darla21` at 20/12 — the first dose on this axis that is not a
guaranteed no-op**, because 20 sits *below* the 35-point paint ceiling and so
paint can genuinely outvote a tower. This tests something new and specific:
whether a *blended* rule — prefer towers only when nearby paint is poor — beats
the current always-tower rule. That is a real design question; 50 / 100 / 200
never were.

## Iteration 20 RESULT — `darla20` (splashers head for nearest enemy paint): **−38 (−6.33 sd)**, the worst arm yet

51/144 (35.4%). carol 6/48, bob 25/48, alice 20/48. 142 of 144 game rows differ
from the baseline, so the mechanism unquestionably fired — this is a refutation,
not a dud build.

**My registered prediction was wrong.** I argued the heading would be worthless
for soldiers (which it was, `darla9` −10) and useful for splashers because a
splasher can overwrite enemy paint. It is far worse for splashers.

**The census says precisely why, and it is not the reason I would have guessed:**

| splasher tag | count |
|---|---|
| **`lowScore lure`** | **240 of 328** |
| `HOME` (dry) | ~30 |
| `cd lure` | 3 |
| fired | **0** |

Median paint held: 99, against an attack cost of 50. So the splashers are
**fuelled, ready, on target and refusing to fire** — the best centre scores under
`SPLASH_MIN_SCORE = 8`, every turn, for the whole window.

**The nearest enemy tile is a lone frontier tile.** A splash centred there covers
one or two enemy tiles at +3 each and never reaches 8. The splasher walks to it,
finds nothing worth 50 paint, holds fire, and repeats — permanently parked on the
frontier doing nothing.

**So the tower attractor was never about towers.** A tower sits inside a *mass*
of enemy paint, and mass is what makes a splash worth firing. `darla17` proved
the attractor is worth 17 games; this proves what it is a proxy for. **Nearest is
a proxy for proximity, which is worthless. The tower was a proxy for density,
which is the thing.**

**And I re-made a documented mistake.** DESIGN.md's own opening records carol's
rule — *a persistent heading beats a nearest-target rule, because a nearest rule
points a forward unit backwards.* I quoted it in the founding document and then
built a nearest-target rule anyway, twice (`darla9`, `darla20`), for a combined
−48 games.

**Queued: `darla22`, the same mechanism aimed at density instead of proximity** —
head for the **centroid of all visible enemy paint**. O(n) over vision, no memory,
and it points at the middle of the enemy's mass rather than at its nearest edge.
If density is the right reading, this should behave like the tower attractor
without its range limit; if it also loses, positioning genuinely does not
generalise beyond an actual tower and the axis closes.

## Iteration 21 RESULT — `darla21` (attractor 20/12): −6. The axis is now COMPLETE and closed.

| tower bonus | result | play differs from baseline? |
|---|---|---|
| 0 | 72/144 — **−17 (−2.83 sd)** | yes |
| 20/12 | 83/144 — **−6 (−1.00 sd)** | yes, 104 rows |
| 50/30 | 89/144 — +0 | **no, 0 rows** |
| 100/60 | 89/144 — inherited | — |
| 200/120 | 89/144 — +0 | **no, 0 rows** |

**The static prediction held exactly.** 20 sits below the 35-point paint ceiling,
so it could change the argmax — and it did, in 104 of 144 games. 50 and above
cannot, and did not, in any game. The scorer's arithmetic predicted which doses
were capable of doing anything, before any of them ran.

**And the design question it was built to ask has a clean answer: do not blend.**
A partially-dominant attractor (20) is *worse* than a fully-dominant one, and
better than none — the response rises monotonically to the saturation threshold
and is flat above it. "Prefer a tower only when nearby paint is poor" loses 6
games to "always prefer the tower".

That fits the density reading `darla20` produced: the tower marks where enemy
paint is *massed*, and local paint score is a poor substitute because it is
computed over 13 tiles while the mass extends far past them. Letting a small
local score outvote the tower trades a good long-range signal for a noisy
short-range one.

**`TOWER_BONUS`: CLOSED.** Five doses, fully characterised, inherited value on the
optimal plateau. Any value ≳35 is equivalent; below that it degrades smoothly to
−17 at zero.

## Iteration 22 RESULT — `darla22` (enemy-paint centroid): **−22 (−3.67 sd)**. Positioning is tower-specific. CLOSED.

| heading when no tower is visible | result |
|---|---|
| **wander at random (inherited)** | **89/144** |
| centroid of visible enemy paint | 67/144 — **−22** |
| nearest enemy paint | 51/144 — **−38** |

Both directed headings lose badly, and **random wandering beats both.** The
density reading was better than the proximity one (−22 against −38), so the
diagnosis of `darla20` was right as far as it went — and it still does not
rescue the mechanism.

**Why random wins, and it is not a paradox.** Coverage is an area-covering
problem. A directed heading *concentrates* splashers: nearby units see similar
vision, compute similar targets, and converge, so their blast radii overlap and
the same tiles get painted repeatedly while the rest of the map is left alone.
Random wandering disperses them, and dispersion is what covers area.

**The tower attractor escapes this because towers are themselves dispersed.**
There are twenty-odd of them scattered across the map, each splasher locks onto
whichever it can see, and the fleet spreads out *while* pointing at valuable
ground. A centroid is a single point; every splasher that can see the same mass
walks to the same place.

**So the mechanism is not "head toward enemy paint" at all. It is "lock onto a
dispersed landmark inside enemy territory", and the tower is the only such
landmark the map provides.** Positioning: CLOSED, tower-specific, five arms.

## Registration — iteration 23, the mopper as a paint mule (`darla23`)

Three measurements meet, and an engine rule makes exactly one thing possible.

1. **Splashers run dry and walk home.** Paint, not chips, is the binding resource
   late: tower paint sits near 54 each against a splasher's 300 cost, and every
   HOME turn is a turn not painting.
2. **Moppers are nearly worthless as they stand.** Removing them entirely cost 5
   games; giving them alice's accepted navigation was a dead tie. They are 10% of
   production doing almost nothing.
3. **[E, carol's verified RULES.md] only moppers may transfer paint robot→robot.**
   I first wanted idle *soldiers* to mule — they hold median 150 paint and paint
   on 1.8% of turns — and the engine forbids it outright: "giving to a non-tower
   ally only as a mopper". Checked before building, which is the first time this
   session that a static check killed an arm before it cost any games.

So the near-useless unit is the **only** unit that can carry paint to the unit
that runs out of it. `darla23` has moppers hand paint to any adjacent splasher
with room for 50 or more, keeping 20 for themselves.

**Mechanism check, read before the score**: the build carries `mu=<trips>/<paint>`
in its indicator. Transfer range is a hardcoded r²≤2 for every unit type, so the
mopper must physically touch the splasher — if `mu` is near zero, moppers and
splashers simply never stand adjacent, and the arm is **untested**, pointing at
rendezvous rather than at the idea.

**Read against the measured floor.** This instrument cannot resolve under ~5
points, so only a move on the scale of the real results (−17, −22, −38) counts
either way. A +3 is noise.

## Iteration 23 — `darla23` (mopper paint mule): **UNTESTED**, and it corrects two earlier closures

88/144, −1. Then the mechanism check, read before any verdict: **`mu=0/0` — not a
single transfer.** And the reason is not rendezvous:

**There are no moppers.** A full game, build events by round 2000:

| | built |
|---|---|
| soldiers | **217** |
| splashers | 24 |
| **moppers** | **1** |

`mop0` alive at every sample point. `MOPPER_IN_20 = 2` asks for 10% of production
and delivers roughly one mopper per game.

**Cause, from carol's own accepted iteration 36.** `PAINT_FLOOR = 200` blocks any
unit cheaper than a soldier unless the tower keeps 200 paint after the build — so
a mopper (100 paint) needs its tower to hold **300**, against an observed ~54.
The floor was built to stop moppers crowding soldiers out, and it does that by
preventing moppers almost entirely.

**So the mule arm is `gate-unimplementable`, not refuted.** The carrier unit does
not exist, and it cannot be made to exist without deleting the floor — which
re-creates the 60–75% mopper share carol fixed. Recorded as unavailable rather
than as a failed idea.

### The correction this forces, which matters more than the arm

**I closed the "mopper axis" earlier, bracketed on both sides. That closure was
wrong, and so was one of its two data points.**

- **`darla3`** (alice's mopper navigation, dead tie) improved the navigation of a
  unit that appears **once per game**. That is not a tie, it is **untested** — the
  exact trap I have quoted at myself repeatedly.
- **`darla2`** (`MOPPER_IN_20 = 0`, −5) never tested moppers at all. Removing the
  mopper rolls hands those 2-in-20 rolls to **soldiers**, so it silently raised
  soldier share from 75% to 85%. It was a soldier-share arm wearing a mopper
  label — and its −5 is consistent with the bimodal `SPLASHER_IN_20` ladder found
  later, not with anything about moppers.

**Corrected closure: moppers are `structurally-unavailable` in this economy.**
Nothing has been measured about the unit. What was measured is a spawn-roll
reallocation and a no-op.

**The general lesson, and it is not the one I already had.** I check that a
*mechanism* fires. I did not check that the *unit the mechanism acts on exists*.
A population census is as necessary as a mechanism census, and it is cheaper —
`+mop` was sitting in every aggregate line I had already dumped, and I read past
it a dozen times.

## Registration — iteration 24/25, the tower mix (`MONEY_MOD`)

The one axis that targets the measured binding resource and has never been
touched. `MONEY_MOD = 4` makes 1 ruin in 4 a money tower.

**Motivation is direct**: chips pile to **$27,000–$46,000 unspent** while
per-tower paint sits at ~54 against a splasher's 300 cost. The team is drowning
in the resource it does not need and starved of the one it does.

`darla24` = 8 (fewer money towers), `darla25` = 2 (more), read as a ladder so the
inherited 4 is bracketed. Read against the measured floor: only a move on the
−17/−22/−38 scale counts.

## Iteration 24 — `darla24` (`MONEY_MOD` 4 → 8, fewer money towers): −2, inside the floor

87/144 (60.4%). carol 25/48, bob 33/48, alice 29/48. −0.33 sd — indistinguishable.

**This is a surprise worth recording.** The motivation was as direct as any this
session: chips pile to **$27,000–46,000 unspent** while per-tower paint sits at
~54 against a splasher's 300 cost. Halving money-tower production should convert
a useless surplus into the binding resource, and it does **nothing measurable**.

Two readings, and `darla25` (`MONEY_MOD` 2, more money towers) will separate them:
either tower *type* matters far less than tower *count* — each tower is also a
spawn point and a paint stash regardless of kind — or the paint bottleneck is not
total income but the per-tower stash dynamics that `darla12` already ran into.

## A better instrument for the one candidate that has ever looked positive

`darla11` (70% splasher) is the only arm in twenty-five to lean positive twice:
+2 on the pinned pair, and 99/150 on a fresh sample against a baseline that
scored 97, 94 and 101 on its own fresh samples. Both leans are inside the ~5-point
floor, so neither settles anything.

**The screens are a difference of differences.** A 3-opponent gauntlet asks how
each build fares against carol/bob/alice, and the candidate-versus-baseline
question is then the difference between those two answers — which is why the
floor is so high. Playing the candidate **directly against the baseline** measures
the marginal change once instead of twice, across all 75 maps instead of a 12-map
sample.

`tools/head-to-head.sh darla11` is queued behind the arm queue: 150 games,
`darla11` vs `darla`, both sides of every map in the pool.

**This is not the self-play blindness carol's doctrine 17 warns about.** That rule
is about measuring a *capability* against an opponent that never exercises it.
The question here is narrower and self-play answers it exactly: the two builds
differ by one constant, so a direct match measures that constant and nothing else.

**Pre-registered**: 75/150 is the null. Accept `darla11` as a genuine improvement
only at **>= 86/150 (57.3%)**, which is 2 sd on a 150-game head-to-head. Anything
between is another way of saying "the same", and I will record it as such rather
than reach for the third significant figure.

## Iteration 25 RESULT — `MONEY_MOD` is a one-sided cliff, and it resolves the paint question

| money towers | arm | result |
|---|---|---|
| 1 in 2 | `darla25` | 59/144 (41.0%) — **−30 (−5.00 sd)** |
| **1 in 4** | `darla` | 89/144 — inherited |
| 1 in 8 | `darla24` | 87/144 — −2 (−0.33 sd) |

**Asymmetric, and that asymmetry is the finding.** Building *more* money towers
is catastrophic; building *fewer* does nothing. Paint income is binding
**downward** — cut it and the bot dies — and **saturated upward** — add more and
nothing happens.

**So paint is the binding resource, but total paint income is not the
constraint.** That looks contradictory and is not: the team already produces more
paint than it can route. What limits spending is the **per-tower stash and the
spend gates** — a splasher needs 300 paint *in one tower*, and `SPLASH_FLOOR`,
`PAINT_FLOOR` and the build rolls decide who gets it. Adding a fourth paint tower
adds income to a system that is already gate-limited, not income-limited.

That is consistent with everything measured tonight: `darla12` (reserve paint for
splashers) killed the economy, `darla5` (open the chip gate) killed it harder,
and every gate sits at carol's value. **`MONEY_MOD`: CLOSED**, inherited value on
the edge of a plateau with a cliff on the other side.

## Registration — iterations 26/27, the splash threshold upward

`SPLASH_MIN_SCORE = 8` is the last untouched gate in the splasher path. Only
**downward** has been tested: `darla7` at 4 lost 11 games. Upward is unmeasured,
and it is the direction the evidence points — paint is precious and gate-limited,
so firing *less often on better targets* is the change that fits the diagnosis.

`darla26` = 14, `darla27` = 22. The scorer's ceiling is 35 (9 enemy tiles at +3
plus 4 empty at +2), so 22 is strict but reachable and 35 would be an off-switch —
the static check applied **before** queueing this time, which is the practice the
288 wasted no-op games bought.

Read against the floor: only a move past ~5 points counts.

## The floor widens with a fourth baseline point — and it matters

The idle filler's fourth fresh-sample run of the shipped baseline came back
**89/150 (59.3%)**, the lowest yet.

| baseline, fresh random 25-map samples |
|---|
| 97/150 (64.7%), 94/150 (62.7%), 101/150 (67.3%), **89/150 (59.3%)** |
| pooled **381/600 (63.5%)** |
| run-to-run sd **3.37 points** (was 2.34 on three points) |
| **2 sd floor: 6.7 points**, range 59.3–67.3 |

**The estimate moved 44% when a fourth point arrived**, which is itself the
lesson: three points is not enough to pin a variance, and I stated a floor from
three of them an hour ago as though it were settled. The floor is **wider** than
I said, not narrower — nearly 7 points at 2 sd on a 150-game fresh sample.

`darla11`'s 66.0% sits comfortably inside a 59.3–67.3 range. Every apparent gain
this session is smaller than the baseline's disagreement with itself, by a
margin that has grown rather than shrunk with more data.

**This does not weaken the head-to-head gate, and the difference is worth being
precise about.** Fresh-sample runs vary because the *maps* vary; a direct
head-to-head plays the candidate and the baseline against each other on the same
75 maps, so map difficulty cancels rather than adding noise. The registered
`>= 86/150` gate is a binomial 2 sd on paired games and stands as written.

## Iteration 26 RESULT — `darla26` (splash threshold 8 → 14): +2, inside the floor

| `SPLASH_MIN_SCORE` | arm | result |
|---|---|---|
| 4 | `darla7` | 78/144 — −11 (−1.83 sd) |
| 8 | `darla` | 89/144 — inherited |
| 14 | `darla26` | **91/144 — +2 (+0.33 sd)** |
| 22 | `darla27` | running |

The direction the diagnosis predicted — fire less often on better targets — is
the direction that leans positive, and by exactly the same +2 as `darla11`. Both
are inside the floor; neither is a result on its own.

## Registration — iteration 28, the COMBINATION, and why this is not fishing

**Two arms out of twenty-six lean positive, both by +2, and they are independent
changes**: `darla11` raises splasher *share* (SPLASHER_IN_20 3 → 14), `darla26`
raises the splash *threshold* (8 → 14). One decides how many splashers exist, the
other decides when a splasher spends 50 paint. Nothing in the code couples them.

**`darla28` sets both.** I am registering the reasoning before the result because
combining candidates after seeing their scores is exactly how noise gets promoted:

1. **This is a combination arm, declared as one.** It is not a single-mechanism
   test and will never be reported as one. If it wins, the credit is joint and
   neither constant is established alone.
2. **The prior is weak and I am saying so now.** Two +2s at +0.33 sd each are
   consistent with pure noise. If they are real and additive the combination is
   ~+4, which is *still* inside the 6.7-point 2 sd floor of the screening
   instrument — so **the screen cannot settle this and is not being asked to.**
3. **The powered instrument decides it.** `tools/head-to-head.sh darla28` plays
   the combination directly against the shipped baseline on all 75 maps, both
   sides, where map difficulty cancels instead of adding noise. Gate as
   registered for `darla11`: null 75/150, **accept only at >= 86/150**.
4. **The falsifier**: if the combination lands near 75/150 in the head-to-head,
   both +2s were noise, and the correct reading of this whole session is that the
   inherited build is unimprovable by any constant in it.

## Iteration 27 RESULT — the splash threshold is FLAT above 8, and that undercuts `darla26`'s lean

| `SPLASH_MIN_SCORE` | result | play differs from baseline? |
|---|---|---|
| 4 | 78/144 — **−11 (−1.83 sd)** | yes |
| **8** | 89/144 — inherited | — |
| 14 | 91/144 — +2 (+0.33 sd) | yes, 142 rows |
| 22 | **89/144 — +0** | yes, **136 rows** |

**Threshold 22 changes 136 of 144 games and lands on exactly the baseline score.**
Two substantially different behaviours, identical outcome — which is the strongest
possible statement that this axis is **flat above 8**, with a cliff below it.

**So `darla26`'s +2 sits between two neighbours that are both exactly 0.** A
genuine optimum at 14 would leave some trace at 22; there is none. The honest
reading is that the +2 is noise, and I am recording that **before** the
combination arm returns rather than after.

**Consequence for `darla28`, stated now.** I registered the combination on the
premise that two independent +2s might be real and additive. One of the two now
looks like noise on the shape of its own ladder, so **the prior is weaker than
when I registered it**, and my expectation for the head-to-head is a result near
the 75/150 null. The gate does not move — it was pre-registered at >= 86/150 and
stays there — but the prediction attached to it is now explicitly pessimistic.

**`SPLASH_MIN_SCORE`: CLOSED.** Four doses, flat in [8, 22], cliff at 4, inherited
value on the plateau.

### Where twenty-seven arms leave the design

Every constant in the splasher path is now bracketed on both sides, and every one
sits at or on the plateau containing carol's value:

| axis | doses | verdict |
|---|---|---|
| `SPLASH_FLOOR` | 0, 1400, 2000, 2600 | interior optimum at inherited |
| `SPLASHER_IN_20` | 15/40/55/70/80% | bimodal, inherited is one of two optima |
| `SPLASH_PAINT_FLOOR` | 0, 150, 300 | monotone worse |
| `TOWER_BONUS` | 0, 20, 50, 100, 200 | switch; inherited on the plateau |
| `MONEY_MOD` | 2, 4, 8 | one-sided cliff; inherited on the edge |
| `SPLASH_MIN_SCORE` | 4, 8, 14, 22 | flat above 8; inherited on the plateau |

Plus five mechanism arms (two navigations, two positionings, one logistics), all
rejected or unimplementable. **The inherited build is the best measured thing in
27 arms and ~3,900 matched games**, and for each axis I can now say *why* rather
than only *that*.

## Iteration 28 — the combination screens at +4, exactly as predicted, and settles nothing

| arm | change | result | legs (carol / bob / alice) |
|---|---|---|---|
| `darla11` | splasher share 70% | 91/144 — +2 | 31 / 32 / 28 |
| `darla26` | splash threshold 14 | 91/144 — +2 | 31 / 31 / 29 |
| **`darla28`** | **both** | **93/144 — +4 (+0.67 sd)** | **33 / 35 / 25** |

**The two +2s added to +4**, which is what independent effects do — and also what
three independent noise draws do. +0.67 sd is inside the screening floor, exactly
as the registration said it would be, so **the screen is not being asked to
settle this and has not.**

One detail worth flagging rather than smoothing over: the combination's gain is
carried by carol (+3) and bob (+5) while **alice drops 4**. A real economic
improvement would not be expected to reverse sign against one of three
independent opponents; a noise draw would do exactly this. It is one more reason
to distrust the +4.

Both head-to-heads are now running or queued — `darla28` vs `darla` on all 75
maps both sides, and `darla11` vs `darla` behind it. Null 75/150, accept at
>= 86/150, as registered before any of these numbers existed.

# ITERATION 1 — ACCEPTED. The first improvement in twenty-eight arms.

**Head-to-head, `darla28` vs the shipped baseline, all 75 maps, both sides:**

| | |
|---|---|
| result | **97–53 (64.7%)** |
| pre-registered null | 75/150 |
| pre-registered gate | **>= 86/150** |
| z | **+3.59 sd** |
| **swept maps** (won from BOTH sides, immune to spawn) | **32 win / 10 loss** |

The identity holds — wins − losses = 2 × (swept − swept-against): 97 − 53 = 44 =
2 × (32 − 10) — so the margin is carried by maps won from both sides, not by
spawn luck.

**The change**: `SPLASHER_IN_20` 3 → 14 (splasher share 15% → 70%) and
`SPLASH_MIN_SCORE` 8 → 14, jointly. **Neither constant is established alone**;
this was registered as a combination arm and is accepted as one.

**Why the screens could not see it, which is the methodological result.** Both
constants screened at +2 and the pair at +4, all inside a 6.7-point floor. On
that evidence I wrote — correctly, given the instrument — that the leans were
probably noise, and I said so twice before the head-to-head ran. The screens were
not wrong; **they were the wrong instrument.** A 3-opponent gauntlet makes
candidate-vs-baseline a difference of differences across two independently
sampled map sets. A direct match plays both builds on the same 75 maps, so map
difficulty cancels instead of compounding, and a +4-on-144 lean resolves into
+22-on-150.

**The lesson is about instrument design, not about being more optimistic.** I ran
twenty-seven arms through a screen that could only ever see damage. The moment I
built an instrument matched to the question — "does this one change help?" rather
than "how does this build fare against three opponents?" — the answer was
immediate and unambiguous. **The bottleneck was never the VM or the ideas; it was
measuring the wrong difference.**

**Bookkeeping**: `src/darla_iter0` is the frozen pre-acceptance baseline, kept so
every result above stays interpretable and so attribution runs have a fixed
reference. `src/darla` is now the accepted build, `BUILD = "darla-i1"`.

**Owed next, in order**: attribution (each constant alone against
`darla_iter0`, since the accept is joint), then the benchmark against `v3` — in
that order, because the benchmark measures what ships and must never choose it.

## The floor, settled on six points — and the accept clears it either way

The idle filler produced six independent fresh-sample runs of the **pre-acceptance**
baseline before the promotion landed (each confirmed pre-accept by its recorded
commit and a clean tree):

| | |
|---|---|
| samples | 97, 94, 101, 89, 92, 95 — all /150 |
| pooled | **568/900 (63.1%)** |
| run-to-run sd | **2.75 points** (2.34 on 3 points, 3.37 on 4) |
| **2 sd floor** | **5.5 points**, range 59.3–67.3 |

The estimate has now stopped swinging: 2.34 → 3.37 → 2.75 as points arrived, and
a settled floor of about **5.5 points on a 150-game fresh sample**. That is the
number to hold, and it retires the two earlier ones I quoted with more confidence
than three or four points could support.

**It also frames what the accept was worth.** In screening terms the combination
was +4 on 144 — under this floor, correctly judged as noise. In head-to-head terms
it is +22 on 150, **+3.59 sd**, against a floor that does not apply because map
difficulty cancels in a paired match. **Same change, same bot, two instruments,
opposite verdicts — and the paired one is the one that answers the question that
was actually being asked.**

A milestone marker is recorded at the accept commit, so the step the shipped
build takes in `vs_old_bots.png` from here on reads as the acceptance rather than
as drift.

## Attribution — both constants contribute, and they are roughly additive

Each constant alone, head-to-head against the frozen `darla_iter0`, all 75 maps
both sides:

| build | change | result | z vs null |
|---|---|---|---|
| `darla11` | splasher share only | **91/150 (60.7%)** | +2.61 sd |
| `darla26` | splash threshold only | **86/150 (57.3%)** | +1.80 sd |
| **`darla28`** | **both** | **97/150 (64.7%)** | **+3.59 sd** |

**Both are real.** `darla11` clears the pre-registered >= 86/150 gate outright;
`darla26` lands exactly on it. And the joint build beats either alone, by +6 and
+11 games, which is what two partially-independent effects look like: +16 and +11
over the null separately, +22 together — additive with some overlap, not
redundant and not synergistic.

**This retires a call I made twice.** I wrote that `darla26`'s +2 screen was
"noise" because its neighbours at thresholds 8 and 22 were both exactly 0, and
that the flat ladder undercut it. The ladder *was* flat within the screen's
resolution — that reading was correct about the instrument — but the conclusion
drawn from it was wrong. **A flat curve measured with a blunt instrument is not a
flat curve.** The same 5.5-point floor that hid the effect also flattened the
ladder I used to argue it away.

**So the accepted iteration is properly attributed**: splasher share carries
about two-thirds of the gain, the splash threshold about one-third, and both
belong in the build. Neither would have survived on screen evidence alone.

**What this session actually established**, stated plainly: carol's constants
were not at a local optimum after all. They looked that way for twenty-seven arms
because every one of those arms was judged by an instrument whose floor was
larger than the effects being measured. The bot did not change when the answer
changed — the measurement did.

## `SPLASH_FLOOR` re-tested on the accepted baseline — the axis CHANGED SHAPE

Paired head-to-head against the accepted build, 75 maps both sides, against the
old screen verdicts measured on the pre-accept baseline (75% soldier):

| floor | old screen (75% soldier) | new paired H2H (20% soldier) |
|---|---|---|
| 1400 | 63/144 — **−26 (−4.33 sd)** | 71/150 — **−0.65 sd, indistinguishable** |
| 2000 | inherited, best | **accepted baseline** |
| 2600 | 81/144 — −8 (−1.33 sd) | 58/150 — **−2.78 sd, clearly worse** |

**The two doses swapped places.** Lowering the floor was catastrophic at 75%
soldier and is now free; raising it was mild at 75% soldier and now costs
clearly. That is a real interaction, not an instrument artefact — the −26 on 144
games was far outside the screen's floor, so it was a genuine effect that has
genuinely gone away.

**The mechanism is straightforward once stated.** `SPLASH_FLOOR` blocks
non-splasher builds. At 75% soldier it was holding back a flood, so removing it
drowned the economy. At 20% soldier there is no flood to hold back — so the lower
bound stops mattering, while the upper bound now bites the few soldiers the bot
still needs to convert ruins into towers.

**No improvement: 2000 is still best.** But the *reason* it is best has changed
completely, and the old closure — "interior optimum" — was true of a bot that no
longer exists.

**The general point, which applies to every axis closed before the accept:** a
closure is a statement about a build, not about the game. Changing the unit mix
invalidated one closure outright. The others are now suspect by the same
argument, and re-testing them on the accepted baseline with the paired instrument
is the cheapest real work available.

**Queued on exactly that basis** — soldier share, which the accept cut from 75%
to 20%, bracketed by two routes to the same variable:

- `darla31`: `MOPPER_IN_20` 2 → 0, mix 70/0/**30** (mopper rolls to soldiers)
- `darla32`: `SPLASHER_IN_20` 14 → 16, mix 80/10/**10**

Soldier share 30% / 20% (accepted) / 10%. Both head-to-head against the accepted
build. Null 75/150, gate >= 86/150 as before.

## Soldier share on the accepted baseline — a plateau, and an hour lost to a blind monitor

Paired head-to-head against the accepted build, bracketing its 20% soldier share
by two independent routes:

| arm | mix (spl/mop/sold) | result | |
|---|---|---|---|
| `darla31` | 70 / 0 / **30** | 64/150 (42.7%) | z = −1.80, indistinguishable |
| **`darla`** | 70 / 10 / **20** | — | accepted baseline |
| `darla32` | 80 / 10 / **10** | 75/150 (50.0%) | z = **+0.00**, dead level |

Both directions are inside the gate, so the accepted 20% sits on a **plateau**
rather than a peak — and `darla32`'s exact 75/150 is as clean a null as this
instrument produces. No improvement on this axis.

**Both results finished at 16:33 and 16:46 and sat unread until 17:49.** The
monitor was watching `darla-arm-runner.log` and `darla-idle-filler.log` — the two
logs that existed when I armed it — and **not** `darla-h2h-*.log`, which I created
later and then moved every important measurement into. The VM kept working; I did
not. An hour of wall-clock was lost to a notification path that quietly stopped
covering the thing it mattered most for.

Fixed: the monitor now tails every queue log, including head-to-heads,
replications and the disk guard's `DISK CRITICAL`. **The lesson is the same one
the `vm-prune` roster bug taught eight hours ago** — a watcher with a hardcoded
list of what to watch degrades silently every time the system grows, and reports
nothing rather than reporting a gap.

**Queued next**, both targeting verdicts that were *inside* the discredited floor
and so were never really measured:

- `darla33`: `MONEY_MOD` 8 — screened at −2 on the old baseline.
- `darla34`: `SPLASH_MIN_SCORE` 20 — refining the accepted 14 upward, now that 14
  is known to be a real effect rather than the noise I twice called it.

## The accept, consolidated on 3,150 games of absolute strength

The idle filler has now produced twenty-one fresh random 25-map samples against
the three frozen lineages, six before the accept and fifteen after:

| | n | pooled | run-to-run sd |
|---|---|---|---|
| pre-accept | 6 | **568/900 — 63.1%** | 2.75 pts |
| post-accept | 15 | **1549/2250 — 68.8%** | 4.79 pts |
| difference | | **+5.7 points** | SE 1.67, **t = 3.41** |

**Three instruments, three designs, one answer:** the paired head-to-head at
+3.59 sd, the absolute-strength series at t = 3.41 over 3,150 games, and the
benchmark against `v3` moving 34.0% → 42.0%. The accept is not an artefact of the
instrument that found it.

**One detail worth keeping.** The post-accept run-to-run sd is **4.79 points
against the pre-accept 2.75** — the accepted build is noticeably *more variable*
across map samples, not just better on average. That fits a splasher-heavy army:
more of its output depends on terrain and on where the opponent's paint happens
to mass. It also means the screening floor for any future work on this build is
**wider** than the 5.5 points measured before the accept, which is one more reason
the paired head-to-head is now the only screen worth using.

## Fixing the idleness, at the class level rather than the instance

The owner observed that I had been stopping and idling. Measured over the last
eight hours: **10 commits, mean gap 44 minutes**, with gaps of 86, 66 and 123
minutes, against a 10–15 minute cadence earlier in the session. The VM was busy
throughout; the idleness was mine.

**Two causes, and I had been patching instances of the first.**

1. **The watcher went blind.** Every watcher I built named the logs it watched,
   and each went stale the moment the system grew a producer. The monitor tailed
   `arm-runner` and `idle-filler`, then I moved every important measurement into
   `head-to-head.sh` and never added it — two results sat unread for 73 minutes.
   **And my fix was the same bug**: `tail -F /tmp/darla-h2h-*.log` expands the glob
   once at startup, so the next head-to-head log would have been missed too.

2. **I gated on single results.** One or two experiments in flight, then waiting.
   With runs taking ~13 minutes and a VM that holds seven concurrent games, that
   leaves most of the wall-clock spent waiting on something I could have queued
   four of.

**Three layers, each covering the failure of the one above:**

- **`tools/watch-state.sh`** replaces log-tailing entirely. It scans for *run
  directories with a `summary.txt`* and reports any it has not reported before.
  It cannot go blind to a new producer, because every producer ends by writing a
  summary — the artefact is the signal, not the log. It also emits `IDLE` when
  nothing is queued, running, or waiting.
- **A 17-minute cron backstop** that wakes me to check for unread results and an
  idle VM even if the watcher dies completely. Session-only, expires in 7 days.
- **Queue depth ≥ 3**, so draining the pipeline takes an hour rather than one
  turn.

**Queued now** (five deep): `darla33` `MONEY_MOD` 8, `darla34` threshold 20,
`darla35` `TOWER_BONUS` 0 — the positioning control re-run on a build that is now
70% splashers, where it should matter *more* than the −17 it was worth at 15% —
`darla36` `CHIP_RESERVE` 600, an axis untouched in 34 arms that gates every
build while chips sit $27k–46k idle, and `darla37` threshold 10.

## Two more axes re-tested on the accepted build — both null

Paired head-to-head, 75 maps both sides, null 75/150:

| arm | change | result | |
|---|---|---|---|
| `darla33` | `MONEY_MOD` 8 | 73/150 (48.7%) | z = −0.33, indistinguishable |
| `darla34` | `SPLASH_MIN_SCORE` 20 | 77/150 (51.3%) | z = +0.33, indistinguishable |

Both were screened at −2 and +0 on the old baseline — inside the floor, so never
really measured. Now measured with the powered instrument: genuinely null. The
old verdicts were right, for the wrong reason.

**Not every re-test finds something**, and that is worth recording explicitly. The
`SPLASH_FLOOR` re-test found the axis had changed shape; these two found nothing.
Re-testing a closure made with a blunt instrument is worth doing and is not
guaranteed to pay.

## Making "waiting" visible

The owner's observation, which was correct: from their side, waiting on a run and
doing nothing look identical. Two things now distinguish them:

- **`tools/status-line.sh`** prints one line — which build is playing, how many
  games in, how many head-to-heads are queued behind, how many arms pending.
- **A 9-minute heartbeat** that prints exactly that line and nothing else while
  work is progressing, and treats `IDLE` as a failure to fix rather than a state
  to report.

**And one false alarm of my own, recorded because the reasoning was wrong.** I saw
the filler take the VM while three head-to-heads were queued and assumed the yield
fix had failed a fourth time. The timestamps say otherwise: the filler started at
19:09:07 when only `darla33`/`darla34` existed and both had finished; I launched
`darla35`–`37` at 19:25–19:27, sixteen minutes later. The yield was working. After
three genuine instances of the same bug class I had started assuming the fourth,
which is its own failure mode — the check took two minutes and would have been
worth it either way.

## Iteration 35 RESULT — the positioning attractor is worth MORE on the new build, as predicted

`darla35` (`TOWER_BONUS` 0) against the accepted build, paired, 75 maps both
sides: **51/150 (34.0%), z = −3.92.** The baseline beats it **99–51**, about 2:1.

**This was a registered prediction, not a re-run.** When the accept changed the
army from 15% splashers to 70%, I wrote that the positioning attractor should
matter *more* than the −17 games it was worth before, because it is the mechanism
that walks splashers onto enemy ground and there are now four times as many of
them. It is the **largest single-constant effect measured in 35 arms** — larger
than `SPLASH_FLOOR` at 0 (−57 on a 144-game screen) once instrument scale is
accounted for, and far larger than anything on the axes I spent the night
closing.

**Which makes the design read differently in hindsight.** Twenty-seven arms were
spent asking *how much of each unit to build* and *when to allow a build*. The
two things that have actually moved this bot are the splasher share and the
attractor that tells splashers where to go — production and positioning, not
gating. The gates were all at carol's values because carol had already tuned them;
the positioning mechanism was hers too, built as a tower-killing weapon, and its
real value is somewhere she never looked.

## Iteration 36 — `CHIP_RESERVE` 1200 → 600: null

76/150 (50.7%), z = +0.16 against the accepted build. An axis untouched in 34
arms, motivated by chips sitting $27k–46k idle — and halving the reserve does
nothing. `darla38` (2400) is queued to close the bracket rather than leave one
side probed.

## Iteration 37 — `SPLASH_MIN_SCORE` 14 → 10: null

74/150 (49.3%), z = −0.08 against the accepted build. With `darla34` (20) also
null, the threshold is **flat in [10, 20]** on the accepted build, with the
accepted 14 in the middle of a plateau rather than on a peak. Consistent with the
pre-accept ladder, which was flat in [8, 22] — the difference being that the
accept established 14 is better than 8 by a real margin, so the plateau has
moved rather than merely been re-confirmed.

## Iteration 38 — `CHIP_RESERVE` 2400: **−9.31 sd**, and the same shape for the third time

| `CHIP_RESERVE` | result |
|---|---|
| 600 | 76/150 — null |
| **1200 (inherited)** | accepted baseline |
| 2400 | **18/150 (12.0%) — z = −9.31** |

A one-sided cliff, identical in shape to `MONEY_MOD`: lowering it does nothing,
raising it is catastrophic. The mechanism is the one this file opens with — the
reserve gates *every* build, and at 2400 it sits above the level the treasury
normally holds (~1,400), so production nearly stops.

**That is the third time tonight the same error shape has produced the session's
worst results**: `darla5` (chip floor to 0, −57), `darla12` (splasher paint floor
300 against ~54 held, −15), and now this. Every one is *a constant set above the
level its resource normally holds* — the exact error `DESIGN.md` was written to
avoid, quoted from alice on the first page.

The useful form of the lesson is that the failure is **not symmetric**. Every
gate axis measured tonight — `MONEY_MOD`, `CHIP_RESERVE`, `SPLASH_PAINT_FLOOR` —
is flat or mildly negative below the inherited value and catastrophic above it.
Gates that are too loose waste a little; gates that are too tight stop the economy
outright. When probing an unknown gate, **probe downward first**: it is the cheap
direction to be wrong in.

## Iteration 39 — `PAINT_FLOOR` 200 → 100: −2.29 sd, and it qualifies the gate lesson

61/150 (40.7%) against the accepted build. A **downward** probe that cost 14
games, which is the direction I had just called "the cheap direction to be wrong
in".

**The mechanism confirms carol's, and closes the mopper question causally.**
`PAINT_FLOOR = 200` exists to stop a mopper (100 paint) crossing its build line
before a soldier (200) can. At 100 the mopper is affordable again, so moppers get
built and crowd out soldiers — and soldiers are now only 20% of the rolls and the
only unit that converts ruins into towers. Earlier I established moppers were
*structurally absent* by observation (one built per game). This establishes it
**causally**: open the gate and they come back, and it costs games.

**The qualification, stated because I overreached.** I wrote that gate axes are
"flat or mildly negative below the inherited value and catastrophic above it".
The asymmetry survives — −2.29 sd here against −9.31 sd for `CHIP_RESERVE`
upward — but "downward is cheap" was too strong on three data points. The honest
version: **gates fail worse upward than downward, and neither direction is free.**

## Iteration 40 — `STAGNANT_ROUNDS` 10 → 4: null

70/150 (46.7%), z = −0.82 against the accepted build. How fast a pinned treasury
frees its reserve does not matter at this mix. Untouched in 39 arms, now measured
and closed.

## Re-testing positioning mechanisms on a build where splashers are the army

Three queued, and the first is the interesting one.

**`darla41` re-runs `darla22`'s centroid heading.** That lost 22 games when
splashers were **15%** of the army; they are now **70%**, and this build is more
sensitive to positioning than to anything else measured — removing the tower
attractor costs **99–51**. The old verdict was measured on a bot whose splashers
were a minority side-show, which is exactly the condition under which
`SPLASH_FLOOR`'s verdict also turned out not to survive the new mix.

The prediction, registered: if positioning dominates this build, a heading that
covers the *tower-free* case should now help rather than hurt, because 70% of the
army spends its idle turns wandering at random. If it loses again by a similar
margin, then dispersion genuinely beats direction regardless of how many
splashers there are, and the positioning axis closes for good.

**`darla42`** (`PAINT_FLOOR` 300) completes the bracket around the inherited 200,
now that 100 is known to cost 14 games. **`darla43`** reaches 30% soldier via the
splasher route, where `darla31` reached it via the mopper route and scored −1.80 —
same target, different lever, which tests whether that result was about the
soldier share or about the moppers.

## Iteration 41 — the centroid heading is MUCH worse at 70% splashers: **−7.84 sd**

27/150 (18.0%) against the accepted build. The baseline wins **123–27**.

**My registered prediction was wrong, and not marginally.** I argued that because
this build is more sensitive to positioning than to anything else measured
(removing the tower attractor costs 99–51), a heading covering the tower-free
case should now *help*. Instead the same mechanism that cost 22 games when
splashers were 15% of the army costs far more now that they are 70%.

**The registered falsifier fires, and the direction sharpens it.** I wrote: *"if
it loses again by a similar margin, dispersion genuinely beats direction
regardless of how many splashers there are."* It lost by a **much larger** margin,
which says something stronger than the falsifier anticipated — **the more
splashers you have, the more damage concentrating them does.** That is
mechanically right and I should have predicted it: a centroid pulls every
splasher that can see the same enemy mass to the same place, so the overlap
penalty scales with the number of units doing the overlapping.

**Positioning splits cleanly into two things, and only one of them is good.**

| | effect |
|---|---|
| **dispersed landmark** — each splasher locks onto whichever enemy tower *it* can see | **worth 99–51** |
| **shared heading** — every splasher computes the same target from the same vision | **−7.84 sd** |

The tower attractor is the first kind. Every heading I have built — nearest enemy
tile, centroid, at both mix levels — is the second. **Positioning: CLOSED**, with
the distinction that makes the tower attractor work now stated explicitly rather
than inferred.

## Iteration 42 — `PAINT_FLOOR` 300: exactly 75/150, and the bracket closes asymmetrically the *other* way

| `PAINT_FLOOR` | result |
|---|---|
| 100 | 61/150 — **−2.29 sd** |
| **200 (inherited)** | accepted baseline |
| 300 | **75/150 — exactly null** |

An exact 75/75 in a head-to-head is the signature of two identical bots, so I
checked: **67 of 75 maps split 1–1 by side** (what identical play produces), and
**8 genuinely diverge** and happen to cancel. So 300 is a real change with a net
effect of precisely zero, not a no-op.

**Mechanically it is a switch that is already off.** `PAINT_FLOOR` decides whether
moppers can be afforded. At 200 they essentially never are (one built per game);
raising to 300 blocks a unit that was already blocked, and only perturbs the
handful of maps rich enough for the gate to bind at all. Lowering to 100 lets them
back in, and that costs 14 games.

**Note the asymmetry runs opposite to the other gates.** `CHIP_RESERVE` and
`MONEY_MOD` are flat below and catastrophic above. `PAINT_FLOOR` is flat *above*
and costly *below*. The common rule is not about direction at all: **a gate is
flat on the side where it is already saturated, and bites on the side where it
starts admitting something.** That is a better statement than the "probe
downward" heuristic I wrote two hours ago and had to qualify one hour ago.

## Iteration 44 — `REFILL_LOW` 50 → 25: null

70/150 (46.7%), z = −0.82. The refill trigger — how empty a unit gets before it
walks back to a tower — was untouched in 43 arms and motivated by HOME turns
being 17–28% of a unit's budget on the old build. Halving it does nothing
measurable. `darla45` (100) is queued to close the bracket.

## Iteration 45 — `REFILL_LOW` 100: **−6.37 sd**. Commuting is expensive, and the inherited value already knows it.

| `REFILL_LOW` | result |
|---|---|
| 25 | 70/150 — null (−0.82) |
| **50 (inherited)** | accepted baseline |
| 100 | **36/150 (24.0%) — z = −6.37** |

Raising the trigger means a unit turns for home at 100 paint instead of 50, so a
far larger share of the army is commuting at any moment instead of painting. It
costs 39 games — the largest effect from any logistics constant, and the third
largest of the session behind the positioning attractor and `CHIP_RESERVE`.

**It fits the corrected gate rule exactly.** Flat on the saturated side (at 25 the
trigger already almost never fires), sharply negative on the side where it starts
admitting something (at 100 it admits a flood of refill trips). That rule has now
predicted the shape of `PAINT_FLOOR`, `CHIP_RESERVE`, `MONEY_MOD` and
`REFILL_LOW` — four gates, two in each direction — which is the first
generalisation this session that has held up on out-of-sample axes rather than
being fitted to the ones that produced it.

**And it settles the HOME-turn diagnosis from this morning.** I measured 17–28% of
unit turns spent commuting and read it as waste to be recovered. It is not
recoverable slack: the inherited trigger is already close to the point where
cutting it further gains nothing and loosening it collapses the bot. The
commuting is the price of a paint economy, not a defect in it.

## Iteration 46 — `SPLASH_FLOOR` 1700: null, and the axis is fully mapped on the accepted build

68/150 (45.3%), z = −0.94.

| `SPLASH_FLOOR` on the accepted build | result |
|---|---|
| 1400 | 71/150 — null (−0.65) |
| 1700 | 68/150 — null (−0.94) |
| **2000 (inherited)** | baseline |
| 2600 | 58/150 — **−2.78 sd** |

Flat across [1400, 2000], falling above it. Combined with the pre-accept ladder,
where 1400 cost 26 games at 75% soldier, this axis has gone from **steep on both
sides to flat below and sloped above** — the clearest single demonstration that a
gate's shape is a property of the build, not of the game. Mapped and closed.

## Iteration 47 — the dispersed landmark is the WORST arm of the session: **−10.78 sd**

9/150 (6.0%). The baseline wins **141–9**.

**I predicted this would behave like the tower attractor and it behaved worse than
anything else I have built.** The full positioning record:

| heading, when no tower is visible | result |
|---|---|
| **none — wander at random (inherited)** | **baseline** |
| nearest enemy tile | −38 games (screen, 15% splashers) |
| enemy-paint centroid | −22 games (screen) / **−7.84 sd** (paired, 70% splashers) |
| **ID-indexed enemy tile (dispersed)** | **−10.78 sd** |

**So dispersion was the wrong explanation, and the right one was in DESIGN.md's
first page all along.** carol's rule: *a persistent heading beats a nearest-target
rule*. A tower is a **fixed landmark** — it sits in the same square for the whole
game, so a splasher that locks onto one keeps the same heading for many turns. Every
heading I have built targets **paint**, which moves every time anybody paints, so
the target is recomputed into a different place each turn and the unit oscillates.

The ID-indexed version is the extreme case and that is why it is the worst: the
index is taken over a *set that changes every turn*, so `id % k` selects a
completely different tile whenever `k` changes. It is the least persistent
heading possible — noise dressed as a policy.

**Three explanations, three refutations, and the pattern is worth naming.** I
explained the attractor as tower-killing (refuted: no tower ever dies), then as
proximity-to-enemy-ground (refuted: nearest and centroid both lose), then as
dispersion (refuted here). Each explanation was built to fit the results I had,
and each predicted a new mechanism that failed. **The one explanation I never
tested is the one the founding document already contained** — and it is the only
one consistent with all five data points.

**Positioning: CLOSED, and correctly this time.** The requirement is a *stable
target*, not a good one. The map supplies exactly one: a tower.

## Iteration 48 — `TOWER_BONUS` 20 on the accepted build: null

70/150 (46.7%), z = −0.82. At 15% splashers this dose cost 6 games; at 70% it is
indistinguishable. So the attractor's *threshold* has softened even as its
*presence* has become far more valuable (removing it entirely costs 99–51). Both
facts fit the persistence reading: what matters is that a stable landmark wins
the argmax often enough to hold a heading, not by how much it wins.

## Iteration 49 — remembering the landmark: null, and **untested**, for a reason that confirms the explanation

74/150 (49.3%), z = −0.08 — the **first positioning arm in five that is not
harmful**. But the mechanism check comes first, and it says the arm never ran:

| | |
|---|---|
| splasher turns sampled | 93 |
| `ring` (a tower in vision) | 31 |
| **`recall` (walking to a remembered tower)** | **0** |

**The recall branch never fires**, because it requires a splasher to be more than
r²=20 from *any* visible enemy tower while remembering one — and towers are dense
(20–50 per map, both teams building all game). A splasher is essentially never out
of sight of one.

So this is `gate-unimplementable` rather than refuted: there is no range gap to
extend the landmark across. **And that is itself the confirmation.** The attractor
works because a tower is stable *and* almost always visible; the reason no
paint-targeted heading could substitute is not that paint is a worse signal in
principle, but that the stable-and-visible combination is already saturated by
towers. There was never a gap for a second mechanism to fill.

**Positioning is now closed on evidence rather than on exhaustion**: one mechanism,
worth 99–51, working for a stated reason, with the four alternatives refuted and
the fifth shown to have nothing to do.

## Iteration 50 — `SPLASHER_IN_20` 15: null

79/150 (52.7%), z = +0.65. One notch off the accepted 14, and unresolvable — as
expected from the bimodal ladder, whose second mode was a plateau rather than a
peak. The accepted value is a good place on that plateau, not a tuned optimum,
and one notch either way is beneath this instrument.

## Iteration 51 — splash scoring weights, enemy:empty 3:2 → 2:1: null

74/150 (49.3%), z = −0.08. The argument was that against a coverage win condition
an enemy tile is worth two points (one gained, one denied) and an empty tile one,
so the inherited 3:2 underprices enemy ground. The bot disagrees: repricing to
the "correct" ratio changes nothing measurable.

**The likely reason is that the ratio rarely decides anything.** A splash centre
is chosen from at most 13 candidates within r²≤4, and the tower term (+100, or
+20 and still null) dominates whenever a tower is in range. Where no tower is in
range, the candidates differ mostly in *how many* tiles they cover rather than in
the enemy/empty mix, so both weightings pick the same centre. `darla52` at 3:1 is
running to see whether a larger move resolves anything.

## Iteration 52 — enemy:empty 3:1: null. The scoring-weight axis is closed.

72/150 (48.0%), z = −0.49.

| enemy : empty | result |
|---|---|
| **3 : 2 (inherited)** | baseline |
| 4 : 2 (2:1) | 74/150 — null |
| 6 : 2 (3:1) | 72/150 — null |

Doubling and tripling the relative value of enemy ground both change nothing,
which confirms the reading from `darla51`: **the ratio almost never decides which
centre is chosen.** The tower term dominates when a tower is in range, and
elsewhere the candidates differ in how many tiles they cover rather than in their
composition. The scorer's weights are not a lever on this design, however
reasonable the coverage argument for changing them was.

**Worth noting as a pattern:** this is the fourth axis tonight where a
well-argued, mechanism-grounded prediction produced a flat null — alongside the
`MONEY_MOD` chip-surplus argument, the `CHIP_RESERVE` idle-chips argument, and
the refill-logistics argument from the HOME-turn census. Each was a sound reading
of a real measurement, and each turned out to describe something the decision
procedure never actually consults.

## Iteration 53 — soldiers stop plinking towers: null (−0.98 sd)

69/150 (46.0%). The argument was clean — a soldier does 50 damage to a 1,000+ HP
tower, **no tower ever dies**, so the action is spent on a target that never
falls, and soldiers are now scarce enough for each wasted turn to matter. Removing
it changes nothing measurable.

The reason is the size of the thing being recovered: tower attacks were 1.3% of
soldier turns, soldiers are 20% of the army, so the action being eliminated is
about **0.3% of all unit-turns**. Correctly identified as waste and far too small
to see — which is a useful calibration for the rest of this file. Several
mechanisms I have called "clearly wasteful" from a census are of this order, and
this measures what that order is worth: nothing this instrument can resolve.

## Iteration 54 — the paint/money census override is a provable NO-OP

75/150 exactly, and **all 75 maps split 1–1 by side** — the signature of two
behaviourally identical bots. Disabling the override changes not one game.

The override re-routes a ruin to a paint tower when a local census finds paint
towers outnumbered more than 2:1. It never fires, because `MONEY_MOD = 4` already
builds three paint towers for every money tower, so `seenPaint * 2 < seenMoney`
is unreachable by construction. A guard conditioned on a ratio its own lattice
makes impossible.

**This is the second provable no-op found by checking the 1–1 split** (after the
`TOWER_BONUS` saturation doses), and both were free to detect: an exact 75/150 in
a paired head-to-head is worth two seconds of checking, because it distinguishes
"genuinely neutral" from "never ran" at no cost. Compare `darla42`, which also
scored exactly 75/150 but diverged on 8 maps — same number, different fact.

## Iteration 55 — defense towers: null (−0.98 sd). The last unused engine mechanic is closed.

69/150 (46.0%). Routing roughly one ruin in seven to a `LEVEL_ONE_DEFENSE_TOWER`
— a unit type **no lineage in this project has ever built** — costs nothing
measurable and gains nothing.

That is the expected answer for a coherent reason: a defense tower produces
neither paint nor chips, and this game is decided by paint coverage in 96.5% of
matches. Trading one producing tower in seven for a stronger gun buys defence of
something that is never attacked — **no tower dies in these matchups at all**. The
result is null rather than negative because one ruin in seven is a small enough
share of the economy for the loss to sit under the floor.

**With this, every mechanic the engine offers has been tried by this lineage**:
resource patterns (closed by alice), defense towers (here), robot-to-robot paint
transfer (unimplementable — only moppers may, and moppers are structurally
absent), tower upgrades (already in use), and the full unit roster. There is no
remaining unused capability to reach for; further gains have to come from using
the existing ones better.

## The confirming benchmark was a no-op, and that is a fact about the instrument

Run `20260912-0011`: **63/150 (42.0%), swept 23, swept-against 35** — byte-identical
to run `20260911-1112`. Of course it is. The engine is deterministic, the
benchmark plays a fixed list of all 75 maps from both sides, and the build had not
changed. Re-running it **cannot** produce a different answer.

So the benchmark has no run-to-run variance to average out, and a second run buys
nothing: 300 games spent re-deriving a number already in hand. The uncertainty in
"42.0% against v3" is not sampling noise at all — it is entirely *map-selection*
uncertainty, and the map list is fixed, so within this instrument the figure is
exact and within any other instrument it is unmeasured.

This also applies retroactively to the lineage gauntlets: the pinned-sample screens
were exactly reproducible for the same reason, which is why matched pairs on them
were trustworthy, and why the *fresh random* samples were the only source of
genuine variance. I had both facts separately and had not put them together.

## The accepted build has a large-map weakness, and the accept created most of it

Pooling every fresh-sample run of the shipped build against the three lineages,
split by map area (small = under 1,600 tiles, the median):

| | small maps | large maps | gap |
|---|---|---|---|
| pre-accept | 56.9% (766 games) | 48.2% (620 games) | 8.7 pts |
| **post-accept** | **82.3%** (1,602 games) | **56.4%** (1,548 games) | **25.9 pts** |
| accept's gain | **+25.4** | **+8.2** | |

**The accept is worth three times as much on small maps as on large ones**, and
the disparity it created is now the single largest structured weakness in the
build — bigger than any constant effect measured tonight.

**It also corrects the census that prompted this.** I regenerated a lost game on
`gridworld` (31x31, 20% walls) and found 4 towers, 30 tower paint and $16,970
idle — and read it as "the splasher mix fails on small walled maps". Exactly
wrong: small maps are where this build is strongest at 82.3%. `gridworld` is a
loss *within* the bot's best regime, and generalising from one regenerated replay
would have sent the next several arms in precisely the wrong direction. The
pooled split took two minutes and pointed the opposite way.

**Note what does *not* follow.** The obvious fix — fewer splashers on large maps —
is contradicted by the same table: the pre-accept build *was* soldier-heavy and
scored 48.2% there, worse than the current 56.4%. More splashers helped large
maps too, just less. So the weakness is not "too few soldiers for a big map"; it
is something about large maps that neither mix addresses, and the next arm has to
find out what rather than assume.

## Iteration 56 — the map-size-adaptive mix: null, and the split confirms the arm did exactly what it should

75/150 overall, and splitting by the axis the arm keys on:

| | result | identical-play maps |
|---|---|---|
| small (<1600 tiles) | 38/76 — 50.0% | **38 of 38** |
| large (≥1600) | 37/74 — 50.0% | 21 of 37 |

**The mechanism is verified by construction.** On small maps the arm is the
baseline by definition, and all 38 split 1–1 — exactly the identical-play
signature. On large maps, where it switches to 50% splashers, **16 of 37 maps
diverge** and the result is still dead level.

So fewer splashers on large maps is **neither better nor worse**, which together
with `darla57`'s mis-specification leaves the upper side to `darla58`. The
large-map weakness is real (56.4% against 82.3%) and the mix is not the lever
for it — the same conclusion the pooled pre/post table already implied, now
tested directly rather than inferred.

**Worth noting what this arm demonstrates methodologically**: keying a rule on
map geometry is legal, symmetric, and costs nothing — both teams and every robot
compute the same value from the same map, so no communication or side-asymmetry
is introduced. That makes map-conditioned policy a usable tool for any future
regime split, even though this particular split found nothing.

## Iteration 58 — the adaptive mix is null in both directions; the axis is closed

69/150 (46.0%), z = −0.98, against `darla56`'s 75/150 at the other extreme. So on
large maps, 50% splashers, 70% (the accepted value) and 80% are all equivalent.
**The unit mix is not the lever for the large-map weakness**, tested from both
sides rather than inferred. Closed.

# The large-map weakness is OPPONENT-SPECIFIC — and my instrument cannot see it

Post-accept win rate, split by opponent *and* map size:

| opponent | small maps | large maps | gap |
|---|---|---|---|
| **carol** | 71.5% (586) | **72.5%** (564) | **−1.0** |
| **bob** | 90.1% (586) | **54.1%** (564) | **36.0** |
| **alice** | 84.3% (586) | **42.4%** (564) | **41.9** |

**Against carol there is no size effect at all.** The entire large-map weakness is
against bob and alice. That makes mechanistic sense: Darla *is* carol's economy,
so against carol the matchup is symmetric and map size scales both sides equally.
alice and bob run soldier-heavy, ruin-converting economies that scale with the
number of ruins — and large maps here carry 38–49 of them.

## The methodological consequence, which is serious

**`darla56` and `darla58` were measured head-to-head against the accepted build —
that is, against a carol-shaped opponent, the one opponent with no size effect to
fix.** A paired self-play match cannot detect an improvement that only matters
against a *different* economy. Both came back null, and that null is
uninformative rather than negative.

This is carol's doctrine 17 exactly — *an even instrument cannot measure a
capability against an opponent that never exercises it* — and I walked into it
while holding the quote. Worse, I built the head-to-head instrument *because* the
3-opponent screen was too noisy, and in doing so traded away the only property
that could have caught this: the screen plays alice and bob.

**So the instrument choice is not "paired is better".** It is:

| question | instrument |
|---|---|
| does this change help *in general*? | paired head-to-head vs the accepted build |
| does this change help *against a specific economy*? | 3-opponent screen, split by opponent |

The second is noisier per game and is the only one that can answer the question I
now have. `darla56` re-run against alice and bob on large maps is the correct
test, and it is queued.

## The large-map test, measured with the right instrument: +4.7 points, z = +1.12 — promising, not proven

`darla56` (50% splashers on large maps) against alice and bob, on the 37 large
maps, both sides — with the **baseline run on exactly the same 148 games**:

| | large-map score |
|---|---|
| accepted baseline | 69/148 — 46.6% |
| **`darla56`** | **76/148 — 51.4%** |
| paired difference | **+7 games, +4.7 points** |

Because the engine is deterministic and both runs used the same pinned maps,
opponents and sides, the comparison is **paired game-for-game**: 109 of 148 games
had identical outcomes, and of the 39 that differed, `darla56` won 23 and the
baseline 16. **McNemar z = +1.12** — the right direction, not yet significant.

**Two things this settles regardless of significance.**

1. **The earlier null was an instrument artefact, as diagnosed.** The same arm
   measured head-to-head against the accepted build scored exactly 75/150 — dead
   level — because that instrument plays a carol-shaped opponent, and carol shows
   no size effect at all. Against the opponents that *do* exercise the weakness,
   the same code leans positive. The prediction that the null was uninformative
   rather than negative is confirmed.
2. **109 identical games out of 148** is itself informative: the mix change only
   alters about a quarter of large-map games, which bounds how much any
   mix-based fix can possibly be worth.

**Next**: this needs more power, not another idea. The cheapest way to get it is
more large maps games of the same pair — the discordant count is what carries the
signal, and 39 discordant games is a small sample of the thing being measured.

### Determinism, demonstrated rather than asserted

The accidental repeat of `darla56`'s large-map run returned **76/148 — identical
to `20260912-021951`**, as it had to: same build, same 37 pinned maps, same
opponents, deterministic engine. I had written this lesson three hours earlier
about the benchmark and then queued two repeat runs anyway while saying the
result "needs more power".

**Repetition is never power here.** On a fixed map list the only sources of new
information are a different build, different opponents, or different maps. The
large band (37 maps, 148 games) is fully consumed; the medium band (12 maps, 48
games) is the untouched ground, and it doubles as a test of whether the effect
extends below the 1,600-tile cutoff.

The baseline's medium-band run returned **40/48, identical to `darla56`'s**, which
confirms the no-op diagnosis empirically rather than by reading the code alone.
It is also the control `darla59` needs, so the wasted run is not wasted twice.

## Iteration 59 — the map-size rule on medium maps: null

`darla59` (threshold moved to 1,200, so medium maps get the large-map treatment)
scored **41/48 against the baseline's 40/48** on the same 48 games. Paired: 37
identical outcomes, 6 won only by `darla59`, 5 only by the baseline —
**McNemar z = +0.30 on 11 discordant games.**

So the treatment that leans positive on large maps does **nothing** on medium
ones, which is a cleaner boundary than the size split alone suggested: the effect
is specific to genuinely large maps rather than scaling smoothly with area. With
only 11 discordant games the medium band is also nearly exhausted as an
instrument — 37 of 48 games are identical whatever the rule says.

**Where that leaves the large-map question.** The only real evidence remains the
large-band pair: +7 games, z = +1.12, 39 discordant. The large band is fully
consumed and the medium band says the effect does not extend downward, so there
is no cheap way to add power to this axis. It stays an open lead, honestly
labelled as one, rather than a result.

## Iteration 60 — the large-map dose curve turns over

Large band (37 maps, alice + bob, both sides, 148 games), each paired against the
baseline's own run on the identical games:

| large-map mix | arm | score | paired (arm / base) | z |
|---|---|---|---|---|
| 70% spl / 20% sold (baseline) | — | 69/148 | — | — |
| **50% spl / 40% sold** | `darla56` | **76/148** | 23 / 16 | **+1.12** |
| 30% spl / 60% sold | `darla60` | 66/148 | 19 / 22 | −0.47 |

**So the lead has a shape, not just a sign.** Pushing the large-map mix further
toward soldiers past 50% gives the gain back — 30% splasher is slightly *worse*
than doing nothing. That makes `darla56`'s +1.12 more interesting than a lone
positive would be: it sits at an interior point with a turnover on the far side,
which is what a real optimum looks like and what pure noise usually does not
produce.

It remains under the significance line. `darla61` (40% spl / 50% sold) is running
and sits between the two measured points; if the curve is real it should land
between +1.12 and −0.47, and if it lands outside that range the shape was noise.
That is a genuine out-of-sample prediction on an axis that costs nothing extra to
test, rather than another arm chosen because it was available.

## Iteration 61 — the registered prediction HOLDS, and the large-map curve is coherent

| large-map mix | score | discordant | z |
|---|---|---|---|
| 70/20 (baseline) | 69/148 | — | control |
| **50% spl / 40% sold** | **76/148** | 39 | **+1.12** |
| 40% spl / 50% sold | 69/148 | 38 | **+0.00** |
| 30% spl / 60% sold | 66/148 | 41 | −0.47 |

**`darla61` was predicted before it ran to land between +1.12 and −0.47. It landed
at +0.00**, and the four points form a monotone curve with a peak near 50%
splasher. That is an out-of-sample confirmation of the *shape*, which no single
point could provide — and it is the reason to treat this lead differently from
the dozen nulls tonight, none of which had a predicted structure to confirm.

**Robustness, split by opponent** (free, from data already collected):

| | baseline → arm | discordant | z |
|---|---|---|---|
| vs alice | 29/74 → 34/74 | 15 | +1.29 |
| vs bob | 40/74 → 42/74 | 24 | +0.41 |

Same sign against both, larger against alice — which is the opponent with the
bigger size gap (42.4% vs bob's 54.1%), so the effect is largest where the
weakness is worst. Three independent consistencies: the dose curve, the
interpolated prediction, and the per-opponent split.

**It still does not clear the bar, and I am not accepting it.** The best point is
+7 games at +1.12 sd. What has improved is not the evidence for the size of the
effect but the evidence that there *is* one — and the honest label is a
well-characterised lead whose instrument is exhausted: 37 large maps is all the
map pool contains, and every dose costs a full pass over them.

# The large-map lead is a TRADE, not a gain — and the pre-ship check caught it

`darla56` on large maps, paired against the baseline on identical games, now
against **all three** opponents:

| opponent | paired result | z |
|---|---|---|
| alice | **+5 games** | +1.29 |
| bob | **+2 games** | +0.41 |
| **carol** | **−5 games** | **−1.00** |
| **net over 222 games** | **+2** | ~0 |

**The rule does not make the bot better. It moves wins from one opponent to
another.** Against the two soldier-heavy lineages it gains; against the
same-economy opponent it loses almost exactly as much. Across a full field it
nets nothing.

**This is why the check existed, and it is the one arm tonight that would have
shipped on the evidence available before it.** Every earlier reading pointed the
right way — a 26-point size gap, a monotone dose curve, an out-of-sample
prediction that held, consistent signs against both tested opponents. All of it
was true and none of it was sufficient, because **every one of those
measurements excluded the opponent the change hurts.** I chose alice and bob
deliberately, for the good reason that they exercise the weakness — and in doing
so built an instrument that could only see the upside.

**The generalisable form**: when a change is motivated by a weakness against a
*subset* of opponents, the natural instrument is that subset, and that instrument
is blind to what the change costs elsewhere. The pre-ship run against the
excluded opponent is not a formality; here it converted a +7 into a +2 and a
decision to ship into a decision not to.

**Verdict: `darla56` is NOT adopted.** The shipped build stays at a uniform 70%
splasher share. The large-map weakness (56.4% against 82.3%) is real, measured,
and **remains unsolved** — the mix is not its cause, and three doses plus two map
bands have not found what is.

**And a caution for whatever comes next**: `v3` is a fourth opponent whose economy
nobody here may inspect. A change that redistributes performance across opponent
types is exactly the kind whose effect on `v3` is unpredictable — and the
benchmark may not be used to choose between builds, so there is no way to find
out before shipping. That asymmetry argues for preferring changes that help
uniformly over changes that trade, independently of their measured net.

## Iteration 62 — expansion insurance: **−6.54 sd**, because "only in the failure state" was wrong

35/150 (23.3%). The rule forces a soldier on every build while the team holds
fewer than 8 towers — and **every game starts at 2 towers**, so it fires through
the entire opening of every match, not only in stalled ones.

**I could have checked this before running it, from a census I had already
taken.** DefaultHuge, the game I used to *motivate* the arm: 7 towers at round
300, 21 by round 600. So a healthy game sits below the threshold for roughly the
first 300 rounds — nearly half of a 700-round match — and `darla62` spends all of
it building soldiers only. That deletes the splasher opening the entire accepted
build rests on, which is worth 99–51 when removed at the attractor and is worth
about the same here.

**The flaw is in the trigger, not the idea.** "Fewer than 8 towers" is a proxy for
*early*, not for *stalled*. The death spiral is defined by expansion having
**stopped** — `DonkeyKong` sat at 6 towers from round 300 to round 590 — and a
count threshold cannot distinguish "6 towers and climbing" from "6 towers and
frozen".

**`darla63` uses the actual signal**: force soldiers only when the team's tower
count has not increased for 150 rounds. That is inert in a healthy opening,
because a healthy opening is adding towers continuously, and fires exactly in the
state the contrast census identified.

## Iteration 63 — stall-triggered insurance also fails, and the line CLOSES on an unavailable signal

40/150 (26.7%), against `darla62`'s 35/150. Both attempts are catastrophic, and
they fail for the same underlying reason.

**"Expansion has stalled" and "expansion is complete" are the same observation.**
When every reachable ruin has been claimed, the team's tower count plateaus
permanently — which is the *healthy* end state of a won game, and is
indistinguishable from the death spiral by tower count alone. Once the rule
latches it never releases, so the whole late game is built with soldiers only,
which deletes the splasher production that the accepted build depends on. That is
why 150-round stall detection scores about the same as the cruder threshold.

**The signal that would separate them is "are there unclaimed ruins left?", and
the bot cannot cheaply have it.** A robot senses ruins within its own vision;
there is no team-wide count, and building one would need communication, which
this design has never used and which would have to be symmetric and agreed across
every tower. Per-robot vision cannot distinguish "no ruins near me" from "no ruins
anywhere".

**Expansion insurance: CLOSED, `gate-unimplementable`.** The diagnosis behind it
stands — the contrast census showing 6 frozen towers against alice's 25 is real,
and the death spiral is a genuine failure mode. What does not exist is a trigger
the engine lets this design compute.

### Where 63 arms leave the build

**Nothing has beaten the accepted build since it was adopted.** Thirty-plus arms
against it: every constant bracketed, every engine mechanic tried, positioning
closed on a stated mechanism, the one lead (large-map mix) shown to be a trade
rather than a gain, and the one genuine diagnosis (the expansion spiral) blocked
by a signal the engine does not provide.

The shipped build stands at **42.0% against `v3`** — from carol's 24.7% best —
and its own absolute strength has been stable across 21 fresh samples.

## Iteration 64 — the local ruin signal is a provable NO-OP, because towers cannot see other ruins

75/150 exactly, **all 75 maps splitting 1–1** — behaviourally identical to the
baseline. The condition never fires, and the arithmetic says why:

| | |
|---|---|
| tower vision radius | √20 = **4.5 tiles** |
| median spacing between ruins | **9.4 tiles** (min 6.8, max 14.7 across 75 maps) |

**A tower occupies a ruin and the next one is roughly twice its vision away.** So
"can this tower see an unclaimed ruin?" is almost always *no*, whatever the state
of the game. The signal I reached for is real and locally computable and simply
**out of range**.

**This was checkable in one line before running it**, from two numbers already in
the repo — `VISION_RADIUS_SQUARED` and the ruin counts in
`tools/mapdata/ruin_parity.txt`. It is the fourth guaranteed-identical comparison
I have launched tonight, and the second where the check was arithmetic rather than
judgement.

**Expansion insurance: CLOSED for real now**, and the closure is sharper than the
earlier "unimplementable". Three triggers tried: team tower count (fires all
opening, −6.54 sd), stall detection (cannot distinguish stalled from complete,
−4.58 sd), local ruin sighting (out of range, no-op). The spiral is real; the
engine gives towers neither the range nor the team-wide state to detect it, and
the one remaining route — inter-robot communication — is a capability no lineage
in this project has ever used and a far larger undertaking than a spawn-rule
tweak.

## Iteration 65 RESULT — communication works, and it is the first positive arm since the accept

**82/150 (54.7%), z = +1.14.**

**Mechanism check, read first as registered:** `ms=<sent>/<heard>`, sampled across
robots in one game — soldiers reach **36 messages sent**, towers reach **100
messages heard**. Both halves of the channel are live. (The first sample I looked
at showed `36/0` and I nearly called it half-broken; those are per-robot counters
and a *soldier* never reads, so a soldier's heard-count is 0 by construction. The
tower side had to be read separately.)

So this is a real mechanism firing at volume, not a no-op — the first thing to
establish after four arms on this question that turned out to be no-ops or
mis-specified.

**Where it sits.** +7 games, +1.14 sd, is the same size as the `darla56` large-map
lead was before the carol check killed it. That is a warning, not an endorsement:
the lesson from `darla56` is that an arm motivated by one opponent's weakness must
be checked against the opponent it was not designed for, **before** any decision.

`darla65` differs in one respect that matters — it is not opponent-targeted. It
fires whenever a soldier finds an unclaimed ruin, which happens in every game
against every opponent. Its per-opponent split is therefore a real test rather
than a formality, and it is the next thing to run.

## `darla65` passes the check that killed `darla56`

Against **carol** on large maps — the opponent and regime where the previous lead
turned out to be a trade — paired on the same 74 games:

| | vs carol, large maps | z |
|---|---|---|
| `darla56` (the killed lead) | **−5 games** | −1.00 |
| **`darla65`** | **−1 game** | **−0.30** |

`darla65` costs essentially nothing against the same-economy opponent, where
`darla56` gave back everything it gained. That is the difference between a rule
that redistributes wins and one that adds them — and it is exactly the property I
argued for when the trade finding landed: **prefer a change that helps uniformly
over one that trades, independently of measured net.**

**Current standing for `darla65`:**

| measurement | result |
|---|---|
| head-to-head vs the accepted build (all maps) | 82/150, **z = +1.14** |
| vs carol, large maps | −1 game, z = −0.30 |
| mechanism | soldiers sent 36, towers heard 100 — live at volume |

Still under the significance bar, and I am not accepting on +1.14. But unlike
every previous lead tonight it has now survived the check designed to kill it,
and the remaining question is power rather than direction. `darla65` against
alice and bob on large maps is running.

## `darla65`'s gain is real but NOT where the diagnosis said it would be

Two measurements, both paired:

| regime | result | z |
|---|---|---|
| vs alice + bob, **large maps** | 68/148 (−1 game) | **−0.23** |
| vs carol, large maps | 50/74 (−1 game) | −0.30 |

**On large maps — the regime the arm was built for — it does nothing at all.**
Yet its head-to-head against the accepted build was +7. Splitting that by map size
shows where the gain actually lives:

| map size | darla65 vs accepted build |
|---|---|
| small (<1200) | 30/52 — **57.7%** |
| medium (1200–1599) | 16/24 — **66.7%** |
| **large (≥1600)** | **36/74 — 48.6%** |

**The mechanism helps on small and medium maps and is inert on large ones — the
exact opposite of its motivation.** I built it to break the expansion death
spiral, which I measured on large maps; it does not touch that, and instead
improves the regime that was already this build's strongest.

**A coherent explanation, offered as a hypothesis rather than a finding.** On
small maps ruins are close together, so a soldier standing at one is frequently
within r²=20 of a tower *and* connected by ally paint — the two preconditions for
a message. On large maps the same soldier is usually out of range of any tower, so
the channel rarely closes. That is testable: the `ms=` counters should show a far
lower sent-to-heard ratio on large maps, and it would explain both halves of this
result with one fact about geometry.

**Status: still a lead, now a better-characterised one.** It survives the carol
check, it is positive overall, and its regime profile is the opposite of what I
predicted — which means the reasoning that produced it was wrong even though the
arm works. That is worth separating clearly: **the arm is a candidate; the
diagnosis behind it is refuted.**

## `darla65` — the verdict: a persistent small positive the instruments cannot resolve

Two independent instruments, both leaning the same way and neither sufficient:

| instrument | result |
|---|---|
| head-to-head vs the accepted build, all 75 maps | 82/150 — **z = +1.14** |
| four fresh 25-map samples vs the three lineages | 422/600 = **70.3%** vs the baseline series' 68.8% — **t = +0.95** |
| vs carol, large maps (the check that killed `darla56`) | −1 game, z = −0.30 |
| **combined across the two independent instruments** | **z ≈ 1.48** |

**Not accepted.** The bar is 2 sd and this is 1.48, and the session has already
shown twice what happens to a lead in this range: `darla56` was +1.12 and turned
out to be a trade; `darla26` was +2 on a screen and was flat on a ladder. A
persistent lean at +1.5 points is exactly what both of those looked like before
the decisive check.

**What is different, and worth stating:** `darla65` is the only candidate tonight
to lean positive on *two independent instruments*, pass the carol check that
killed the previous lead, and fire at measured volume (36 sent / 100 heard). It
is the strongest unadopted candidate this project has produced.

**The cost of deciding it** is now arithmetic rather than judgement: at an effect
of +1.5 points and the measured variances, **~18 fresh samples** would reach 2 sd,
against the 4 in hand. That is about 2,100 more games — roughly four hours of VM
time, and the only route left, since the head-to-head instrument is exhausted at
150 games and repeats are byte-identical.

**Queued: 14 more fresh samples.** If the lean holds it clears the bar and ships;
if it decays toward zero, it joins the night's other +1s and the accepted build
stands unchallenged. Either outcome is a decision rather than an open question,
which is the thing this candidate currently lacks.

# `darla65` — REJECTED on the pre-registered bar. 18 samples, 2,700 games.

| | |
|---|---|
| fresh samples (n=18) | 110 103 105 104 110 90 105 107 109 113 120 100 91 98 102 114 97 95 |
| pooled | **1873/2700 = 69.37%** |
| baseline series | 68.80% (15 samples) |
| **difference** | **+0.57 points, SE 1.77, t = 0.32** |
| pre-registered bar | 2.0 sd |

**Rejected.** And the shape of the decay is the part worth keeping: the estimate
ran **+1.5 (n=4) → +0.3 (n=6) → +1.6 (n=10) → +2.5 (n=11) → +0.8 (n=15) → +0.57
(n=18)**. At four samples it looked like a +1.5-point improvement worth shipping;
at eighteen it is +0.57 with a standard error three times its size.

**The head-to-head said +1.14 and the 2,700-game series says +0.32.** Both
measured the same build against the same opponents. The head-to-head is a single
draw of one 150-game instrument, and a single draw at +1.14 is what a zero effect
produces about one time in eight. **The instrument was not wrong; reading one
draw of it as an effect was.**

**What this closes.** `darla65` was the strongest unadopted candidate this project
produced: positive on two instruments, passing the carol check that killed the
previous lead, firing at measured volume. All of that was true and none of it
survived 2,700 games. The accepted build stands.

## Standing at 65 arms

**No change has beaten the accepted build since it was adopted.** What the session
produced instead is a map of why: every constant bracketed on both sides, every
engine mechanic tried including the first use of communication in this project,
positioning closed on a stated mechanism, the large-map weakness measured and its
one candidate fix shown to be a trade, the expansion spiral diagnosed and its
trigger shown to be unavailable.

The shipped build remains **42.0% against `v3`** (from carol's 24.7%), with
absolute strength stable across 33 fresh samples.

**And the methodological result is the one I would carry forward**: the only
accept tonight came from an instrument built to match the question (paired, same
maps), and every subsequent lead died on the instrument that could see what it
cost. Both halves of that matter — the first found a real effect the screens
could not, and the second killed four candidates the screens would have shipped.

## Iteration 66 — `RUIN_PATIENCE` 40 → 120: null

77/150 (51.3%), z = +0.33. Letting a soldier persist three times as long on a
ruin before abandoning it changes nothing measurable. The motivation was that
large maps mean longer travel and so more chances to hit the abandon limit before
a pattern completes; if that were the binding constraint, tripling the limit
should have shown it. `darla67` (patience 15) is running to bracket the other
side.

## Iteration 67 — `RUIN_PATIENCE` 15: −2.45 sd. Axis closed, and "exhausted" was wrong.

60/150 (40.0%). With `darla66` (120) null, the axis is asymmetric in the now-familiar
way: **abandoning a ruin sooner costs 15 games, waiting longer is free.** Flat on
the side where the limit is rarely reached, biting on the side where it starts
firing — the same shape as `PAINT_FLOOR`, `CHIP_RESERVE`, `MONEY_MOD` and
`REFILL_LOW`. Five gates now, and the rule has predicted every one.

### And a correction: I said the constant space was exhausted. It was not.

Enumerating every tunable constant in the shipped build and counting how many
distinct values each has been given across all 67 arms:

| tested | constants |
|---|---|
| 3–6 variants | `SPLASH_MIN_SCORE`, `SPLASH_FLOOR`, `PAINT_FLOOR`, `CHIP_RESERVE`, `MONEY_MOD`, `REFILL_LOW`, `RUIN_PATIENCE` |
| 2 variants | `STAGNANT_ROUNDS` |
| **never varied** | **`BAN_CAP`, `CENSUS_MIN`, `RUIN_BAN_ROUNDS`, `SEEN_CAP`, `TOWER_MEM`** |

**Five constants had never been touched** when I twice told the owner the space was
exhausted. That claim was an impression, and the check that refutes it is one
`grep` — the same category of error as every "guaranteed identical" arm I
launched: a statement about the code that I never asked the code.

One of the five is genuinely moot by static argument: `CENSUS_MIN` gates the
paint/money census override, and `darla54` proved that override unreachable —
`MONEY_MOD = 4` makes its condition impossible, so any `CENSUS_MIN` is a no-op.
That leaves four, and two are queued now: `darla68` (`RUIN_BAN_ROUNDS` 250 → 60,
the patience lever from the other end) and `darla69` (`TOWER_MEM` 12 → 40, which
may be short on large maps carrying 25+ towers).

## Iteration 70 RESULT — the symmetry arm was a NO-OP: statics are per-robot

75/150 exactly, **all 75 maps splitting 1–1**, and the mechanism counter reads
**`sy=0/0`** — not one candidate eliminated, not one heading taken.

**The cause is an engine fact I had already tripped over tonight.** Static fields
in this engine are **per robot**, not per team. `darla70` set `myStart` only on a
tower:

    if (myStart == null && rc.getType().isTowerType()) myStart = rc.getLocation();

so every *soldier* kept `myStart == null`, `enemyBase()` returned null, and the
entire inference never ran. I hit exactly this two arms ago reading `darla65`'s
`ms=36/0` and concluding the channel was half-broken, when soldiers simply never
execute the tower's counter. **Having diagnosed it once did not stop me writing
it again**, in the very next mechanism.

**`darla71` fixes the reference rather than the derivation.** Any *allied tower*
serves: it stands on a ruin, so its mirror holds a ruin, and the elimination
argument is unchanged. A soldier takes the first allied tower it sees.

**One honest limitation, registered now.** Eliminating candidates requires *seeing*
a mirrored location, which sits across the map. On large maps that may never
happen, so `enemyBase()` will often return the rotational mirror un-eliminated —
a **guess**, not a derivation, though still a stable one. The `sy=` counter will
show which regime the arm is actually in: non-zero eliminations mean the
inference resolved; zero with non-zero uses means it is running on the default
candidate.

## Iteration 69 — `TOWER_MEM` 12 → 40: provable NO-OP

75/150 exactly, all 75 maps splitting 1–1. The buffer holds remembered allied
tower locations for refill navigation, and raising its capacity changes nothing
because **it never fills**: a robot only ever records towers it has personally
seen, and `towerN` reaching 12 within one robot's lifetime does not happen at
this vision range. Raising the cap of a buffer that never reaches its cap is
inert by construction.

**Determinable statically, again** — the fourth no-op tonight and the third whose
refutation needed only the code plus one number I already had. The pattern across
all of them is identical: **I varied a limit without first asking whether the
limit binds.** `SPLASH_MIN_SCORE` at 50+, `PAINT_FLOOR` at 300, `CENSUS_MIN`,
`TOWER_MEM` — every one a bound that was never being hit.

That is now a checkable rule rather than an observation: **before varying a
capacity or threshold, measure how often the current value is actually reached.**
Each of these four cost a 150-game run to learn what an instrumented counter or a
back-of-envelope would have said for nothing.

## Iteration 68 — `RUIN_BAN_ROUNDS` 250 → 60: −1.31 sd

67/150 (44.7%). Shortening how long an abandoned ruin stays banned makes the bot
worse, not better. Together with `RUIN_PATIENCE` this completes a coherent
picture of the ruin-abandonment machinery:

| change | direction | result |
|---|---|---|
| `RUIN_PATIENCE` 15 (give up sooner) | more abandonment | **−2.45 sd** |
| `RUIN_PATIENCE` 120 (persist longer) | less abandonment | null |
| **`RUIN_BAN_ROUNDS` 60 (retry sooner)** | **more retrying** | **−1.31 sd** |

**Both directions of "revisit ruins more" lose, and both directions of "leave
them alone" are free.** A soldier that returns to a ruin it already failed on is
a soldier not painting, and the inherited values are on the safe side of both
levers. Consistent with the saturated-side rule, and consistent with the deeper
finding that soldiers are poor painters whose value is ruin *conversion* — so
anything that makes them re-attempt failures costs their only productive output.

That leaves `BAN_CAP` and `SEEN_CAP` as the last two never-varied constants, and
both are capacities rather than thresholds — so by the rule `darla69` just earned,
they get an instrumented check for whether the cap is ever reached *before* any
150-game run is spent on them.

## Iteration 71 — symmetry inference fires, and is null (−0.49 sd)

72/150 (48.0%). **The mechanism now runs**: 17 of 75 maps diverge from the
baseline, and the counter reads `sy=0/3` to `sy=0/4` — soldiers take the
symmetry heading a handful of times per game.

**But the first number is the informative one: eliminations are ZERO.** No
candidate symmetry is ever ruled out, because ruling one out requires *seeing*
the mirrored location, which sits across the map. So the arm is not running the
derivation `RESEARCH.md` describes at all — it is running an un-eliminated
**guess** at the rotational mirror. The limitation I registered before the run is
what actually happened.

**So this does not test the idea.** It tests "send idle soldiers toward the
180°-rotated image of a friendly tower", which is a fixed guess that is right on
rotational maps and wrong on the other two. Against that, −0.49 sd is about what
a coin-flip heading should score.

**What a real test needs**, stated so the next attempt does not repeat this:
elimination must use evidence a robot *actually gathers*, not a location it must
travel to. The candidates differ in where they map **nearby terrain**, so the
check should compare observed walls against each candidate's prediction for tiles
already in vision — every wall seen constrains every candidate immediately, with
no travel. That is the version `RESEARCH.md` means by "eliminate them as terrain
is observed", and I implemented the one check that needs a journey instead.

**Recorded as `untested`, not refuted** — and the third arm tonight where the
mechanism fired but on a degraded version of the intended signal (`darla49` out
of range, `darla64` out of range, this one un-eliminated).

## Iterations 72 and 73 — terrain-in-vision elimination works, and both arms are VOID on bytecode

`darla71` above said what a real test needed: eliminate candidates from terrain
**already in vision**, so no robot has to travel to the mirrored start. Both of
the next two arms implemented exactly that, and neither produced a readable
score.

| arm | change | result | counters |
|---|---|---|---|
| `darla72` | full vision sweep × 3 candidates, every turn | 61/150 | `sy=1/0`, `sy=2/0` — **eliminations happen** |
| `darla73` | same, bounded: stop at 1 survivor, sweep every 5th round | 66/150 | `sy=0/…`–`sy=1/…`, **`ov` up to 8** |

**The inference is correct and the cost is the whole story.** `darla72` overran
at `ov=3`; `darla73` bounded the cost two ways and still overran at `ov=4`–`8` on
`Barcode` around round 400. `senseNearbyMapInfos(-1)` is ~69 tiles, and for each
one a live candidate costs a `canSenseLocation` plus a `senseMapInfo` — the
every-5th-round gate divides the *frequency* but not the per-invocation spike,
and it is the spike that overruns. By the rule registered at `darla8`, an arm
whose robots miss turns is void regardless of its score, so neither 61/150 nor
66/150 is evidence about symmetry inference.

**The finding that actually closes this line is not about cost.** Reading
`darla73`'s consumer:

```java
if (foe == 0) {
    MapLocation f = nearestVisibleEmpty();
    if (f != null) { explore = f; ... }        // almost always taken
    else { MapLocation eb = enemyBase(); ... } // the symmetry heading
}
```

The symmetry answer is consumed in **one place, as the fallback of a fallback** —
only when no enemy is visible *and* no empty tile is visible. And when
eliminations are zero, `enemyBase()` returns the first live candidate, which is
always `symRot`. So on `Barcode`, where `sy=0/3`, every single use of the
"inferred" answer was an **un-eliminated rotational guess** — the same fixed
heading `darla71` was scored on, arrived at by 69 tiles of sensing per robot.

So three arms have been spent building a derivation whose answer reaches at most
a narrow fallback branch, and I have never once measured whether that branch
matters. That is the `darla70` mistake in a new costume: `darla70` built a
mechanism nothing could read because statics are per-robot; this built one whose
reader is a third-choice branch.

**`darla74` registered, and it deliberately contains no inference at all.** It
replaces the one line the baseline uses to give up:

```java
else state += " frontNone";                          // baseline
else { explore = <180° rotation of my own location>; // darla74
       exploreAge = 0; state += " symTgt"; }
```

Two subtractions, no sensing, so `ov` is structurally 0 — and no symmetry state,
so the result is attributable to the **consumer** and nothing else: *does an
enemy-side heading beat giving up, on the turns where the bot currently gives
up?* If it is null, §6 of `RESEARCH.md` is closed for this bot — not because
inference is impossible but because there is nothing here to inform. If it moves,
then and only then is a cheap inference worth a fourth arm, and the target to
refine toward is the mirrored **start**, not the mirrored current location.

Registered before the run: the baseline's own `frontNone` counter says how often
this branch is even reached, so a null result is interpretable either way.

## `SEEN_CAP` is a provable NO-OP, settled from map data without a run

`SEEN_CAP` and `BAN_CAP` were the last two never-varied constants, and the rule
`darla69` earned says a capacity gets an instrumented reached-check before any
150-game run is spent on it. `SEEN_CAP` needs no instrumentation at all:

| | |
|---|---|
| `SEEN_CAP` | **64** |
| `seenLoc` holds | one entry per **distinct ally tower** seen |
| ally towers ≤ towers ≤ | **ruins on the map** |
| max ruins on any official map | **52** (`Leaf`; then `DefaultHuge` 49, `DonkeyKong` 46) |
| median | 16 |

A robot cannot record a 64th distinct ally tower on a map that has 52 ruins, so
`seenN >= SEEN_CAP` never fires and every value from 53 up is byte-identical.
**Raising `SEEN_CAP` is guaranteed to change nothing**; only a cut below 52 could
alter play, and then only on the three or four densest maps.

That is the fifth provable no-op in this lineage and the third settled by
arithmetic over numbers already in the repo (`darla64` tower vision vs ruin
spacing, the `CENSUS_MIN` override, this). The cheap check keeps paying.

## `BAN_CAP` is the first capacity the reached-check says IS saturated

Same rule, opposite answer. `BAN_CAP = 8` bounds how many abandoned ruins one
robot remembers, and the shipped build **already instruments it** — `banPeak`,
emitted as `bp=` in every indicator string, was added when the table grew from
effectively 1 slot, precisely to show whether more than one was needed. So this
check cost no arm and no games, only a replay census.

`banPeak` records `live + 1`, and `live` counts slots that are neither the key
being written nor lapsed. It therefore reaches **9 exactly when all 8 slots hold
live, non-matching bans** — the saturation signature, since the write must then
evict a ban that has not expired.

Census on `20260912-150525`, a clean baseline run, full games:

| replay | max `bp` |
|---|---|
| `alice__DonkeyKong__botB` | **9 — saturated** |
| `carol__DonkeyKong__botA` | **9 — saturated** |
| `bob__DonkeyKong__botA` | 6 |
| `alice__DonkeyKong__botA` | 5 |
| `alice__Oasis__botA` / `botB` | 3 / 2 |

`DonkeyKong` has 46 ruins; `Oasis` is ordinary and never comes close. So the cap
binds where the arithmetic says it should — on the ruin-dense maps — and not
elsewhere. This is the **first** of the capacity checks to come back positive;
`TOWER_MEM`, `CENSUS_MIN`, the tower vision signal and `SEEN_CAP` all came back
unreachable.

**But the interesting defect is not the size, it is the eviction policy.** When
the table is full the victim is `banNext`, a ring cursor, so the bot can evict the
ban it created last turn while keeping one that lapses two turns from now — the
memory it throws away is chosen by an unrelated counter.

**`darla75` registered:** on the saturated path only, evict the slot whose ban
**lapses soonest** instead of the ring slot. It is one line inside a loop that is
already walking all 8 entries, it runs only when `slot < 0`, and it leaves
`BAN_CAP` at 8 — so this is a policy change, not a dose, and any effect is
attributable to *which* memory is discarded rather than to how much is kept.

Registered before the run: this can only act on the turns where `bp` reaches 9,
which the census puts on the ruin-dense end of the pool and nowhere else — so a
small overall number with the gain concentrated on large, ruin-dense maps is the
predicted shape, and a flat result across all 75 maps would mean the saturated
path is too rare to matter at all. If `darla75` is null, `BAN_CAP` is closed as
measured-and-small and every constant in this bot has been varied or proved
unreachable.

## Iteration 74 — RESEARCH.md §6 is CLOSED for this bot, and the reason is the branch, not the inference

73/150 (48.7%), **63 of 75 maps splitting 1–1** and 12 diverging. A −2-game null
on a change that fires on one map in six.

And the number that explains it was available from a single replay, before the
run. Counting soldier `state` tokens on the baseline over a 60-round window:

| map / side | `frontFound` | `frontNone` | `S HOME` | share of soldier-turns reaching `frontNone` |
|---|---|---|---|---|
| `DonkeyKong` botB | 43 | **1** | 48 | 0.8% |
| `Oasis` botA | 11 | **0** | 144 | 0% |
| `TheBest` botA | 19 | 4 | 116 | 2.2% |
| `TheBest` botB | 185 | **100** | 20 | 33% |

`enemyBase()` is consumed only when no enemy *and* no empty tile is visible, and
on three of four map-sides a soldier essentially always has a visible empty tile
to walk to. So the symmetry answer had almost no turns on which to act — and on
the one side where it did (`TheBest` botB, 33%), an enemy-side heading is worth
nothing measurable.

**Four arms — 71, 72, 73, 74 — closed by measuring the consumer once.** The
progression is worth stating plainly because the failure was mine, not the idea's:

| arm | what I tested | why it could not answer |
|---|---|---|
| 71 | mirrored-start check | needs travel; eliminations 0 |
| 72 | terrain-in-vision | works, but `ov=3` — VOID |
| 73 | same, cost-bounded | still `ov=4`–`8` — VOID |
| 74 | the consumer alone, no inference | **null, and the branch is <1% of turns** |

`darla69` earned the rule "before varying a capacity, measure how often the
current value is reached". The general form, which I should have applied at
`darla71` and have now paid four arms for, is: **before improving what a branch
decides, measure how often that branch is reached.** It is the same one-replay
check, and it costs nothing.

Registered closure: **§6 `structurally-unavailable`** for this architecture — not
refuted. Inferring symmetry works (`darla72` proved the derivation fires); this
bot simply has nowhere to spend the answer, because its soldiers are never short
of a nearer thing to walk toward. A bot that *did* spend it — coordinated early
rushes, tower-siting on the enemy half — would be a different bot.

## The same census found a much larger target: `S HOME` is 63–79% of soldier-turns

The column I went looking past is the one that matters. On `Oasis` botA, 144 of
183 soldier-turns are `S HOME` — walking to a tower to refill. On `TheBest` botA,
116 of 183. This is the single largest block of soldier time in the bot and it
has never been examined.

It is not commuting cost. The refill counters say what it actually is:

| | `rt` (latches) | `ht` (turns latched) |
|---|---|---|
| `Oasis` botA, one soldier | **6** | **398 → 408** (rising 1/round) |
| `TheBest` botA, one soldier | **1** | **406 → 416** (rising 1/round) |

A soldier that has latched **once** and spent **416 consecutive turns** in the
HOME state never arrived. `walkHomeIfDry` latches below `REFILL_LOW` and unlatches
only at half capacity, so a soldier that cannot refill is latched for the rest of
the game — and every one of those turns is spent walking instead of painting.

**The root cause is three lines apart in the source, and it is a type error, not a
tuning error:**

```java
static void rememberTowers() { ...
    if (!t.type.isTowerType()) continue;     // EVERY ally tower, money ones too
    int key = (l.x << 6) | l.y;              // type is thrown away here
static MapLocation nearestRememberedTower() { ...
    int d = me.distanceSquaredTo(l);         // nearest of ANY type
static void refillIfPossible() { ...
    int want = Math.min(cap - rc.getPaint(), ally.paintAmount);   // money tower: 0
```

A dry soldier walks to the nearest remembered tower. If that is a **money** tower
— `tp=0` in every indicator I have read — then `want = min(deficit, 0) = 0`, no
paint transfers, the soldier never reaches half capacity, stays latched, and
burns every remaining turn of the game commuting to a tower that cannot help it.
`rt=1, ht=416` is that failure written down.

No lineage in this project has ever tested tower *type* at refill time: `grep`
across `agents/*/src/*/*.java` finds `LEVEL_ONE_PAINT_TOWER` only in
build-decision and pattern-completion code.

**`darla76` registered** — the type is free at the moment of observation, so
record it and prefer it:

```java
int key = (l.x << 6) | l.y | (t.type.getBaseType() == UnitType.LEVEL_ONE_PAINT_TOWER ? 4096 : 0);
MapLocation l = new MapLocation((towerMem[i] >> 6) & 63, towerMem[i] & 63);  // mask the new bit
int d = me.distanceSquaredTo(l); if ((towerMem[i] & 4096) != 0) d -= 100000;
```

One spare bit in a key that had six free, one mask on the decode, one subtraction
that makes any paint tower beat any money tower while distance still orders
within a class. `BAN_CAP`-style capacity untouched; no constant changed.

Registered prediction: this should be largest exactly where `S HOME` dominates —
`Oasis`, `TheBest` — and near-null on maps where soldiers already reach a paint
tower. Falsifier: if `ht/rt` stays high in `darla76`'s own replays, the stuck
soldiers are not at money towers and the diagnosis is wrong.

**Building it also caught a near-miss of the `darla14` class.** The first attempt
used pattern-matched `sed`, and `int key = (l.x << 6) | l.y;` and
`int d = me.distanceSquaredTo(l);` each appear **twice** in the file — the second
`key` site is the `seenLoc` tower census and the second `d` site is the
paint-target scan, neither of which has a `towerMem` in scope. `make-arm.sh`
reported "6 changed line(s)" where 4 were intended, which is what made me look.
The rebuild addresses the three lines **by line number**, which is exact here
because no edit changes the line count. The arm-builder's diff count earned its
keep a second time.

## Iteration 75 — soonest-lapsing eviction: +4, and every diverging map swept

79/150 (52.7%). On its own that is +0.65 sd and unremarkable. The map-level
breakdown is not:

| | |
|---|---|
| maps playing 1–1 (identical) | **71 of 75** |
| maps diverging | **4** |
| of those, won 2–0 by `darla75` | **4 of 4** |

So the saturated path is as rare as the `bp` census said — the eviction policy
changes nothing whatever on 71 maps — and on every map where it changes anything
at all, the new policy wins **both sides**. Given divergence, direction is the
informative quantity, and 4/4 one-sided is p ≈ 0.06. Suggestive, not decided, on
n = 4 maps.

**One registered prediction was wrong and is recorded as such.** I predicted the
gain would concentrate on ruin-dense maps, since that is where `bp` reaches 9.
The four diverging maps have **20, 20, 18, 16** ruins — `Dominoes`,
`DefaultLarge`, `Barcode`, `AlarmClock`. `Leaf` (52), `DefaultHuge` (49) and
`DonkeyKong` (46), the three maps the census actually caught saturating, all
played 1–1. So saturation is necessary but plainly not sufficient: it matters
where the *discarded* ban was about to be needed again, which is a property of
ruin layout and soldier routing, not of ruin count.

**Not accepted.** The engine is deterministic, so re-running this head-to-head
returns byte-identical games and cannot corroborate anything. `tools/replicate.sh
darla75` queued behind `darla76` — a fresh random 25-map sample against all three
lineages, ground the candidate was not selected on, which is the only instrument
here with genuine run-to-run variance.

## Iteration 76 — the type error is real, worth nothing, and NOT the cause of `S HOME`

76/150 (50.7%). **17 maps diverge, 9 swept by `darla76` and 8 by the baseline** —
a coin flip, +1 game.

So the bug I diagnosed is real: on 17 of 75 maps a dry robot's nearest remembered
tower was a **money** tower at least once, and preferring a paint tower changed
play. It just does not matter to the outcome.

**The registered falsifier fired, and it is the useful part of this run.**
`Oasis` and `TheBest` — the two map-sides where `S HOME` was 63–79% of
soldier-turns, the whole reason I built this — **both played 1–1 identical**. The
paint-tower preference never changed a single decision there. So the stranded
soldiers on those maps were already walking to paint towers, and tower *type* is
not what strands them.

**What does, read off the same replay:** our own paint towers' `tp=` at round 300
on `Oasis` were `0, 5, 10, 55, 60, 65, 100, 110, 120, 125, 130`. Several are
nearly dry, and the unlatch condition is *half capacity* — 100 for a soldier:

```java
static boolean walkHomeIfDry(int cap) {
    if (paint >= cap / 2) { refilling = false; return false; }   // needs 100
...
static void refillIfPossible() {
    int want = Math.min(cap - rc.getPaint(), ally.paintAmount);  // tower holds 5
```

A soldier arrives at a paint tower holding 5, takes 5, is still far below 100,
**stays latched, and spends the rest of the game commuting to a tower that cannot
fill it.** `rt=1, ht=416` is a supply failure, not a routing failure. The
diagnosis was one level too shallow: I fixed *which* tower, and the problem is
that the tower is empty.

This also reframes `darla76` itself — the reason preferring paint towers is worth
nothing is that on the maps where refill actually binds, the paint towers are dry
too, so there was never a better tower to prefer.

**`darla77` registered.** `refillIfPossible()` is called immediately before
`walkHomeIfDry` for all three unit types (lines 494, 727, 761), so a robot still
below half capacity while standing within transfer range of its target tower has
*already* taken everything that tower had. One line:

```java
if (rc.getLocation().distanceSquaredTo(home) <= 2) { refilling = false; return false; }
```

r² ≤ 2 is exactly `refillIfPossible`'s own scan radius, so the two agree by
construction. No constant changed; the latch threshold and `cap / 2` both stay.
The claim is only that **queueing at a dry tower is strictly worse than acting
with what you hold** — a soldier's attack costs 5 paint, so even 20 paint buys
four painted tiles, against zero for waiting.

Registered falsifier: if `rt` (latch count) climbs sharply while `ht` falls, the
arm has traded one stuck soldier for a thrashing one — latch at 50, unlatch at a
dry tower, paint down to 50, re-latch — and that is a refutation, not a win, even
if the score moves.

## `darla75` replication — and the discovery that neither instrument can decide it

Fresh random 25-map sample against all three lineages: **103/150 (68.7%)**.
Against the shipped build's own 37 fresh samples — mean **102.5/150**, sd
**7.34** — that is **+0.07 sd**.

**That is not evidence that `darla75` does nothing.** It is an instrument that
cannot see the effect in question. The two instruments in use have a gap between
them that this arm fell straight into:

| instrument | pairing | what limits it | verdict on `darla75` |
|---|---|---|---|
| head-to-head, 150 games | exact, on (map, side) | **discordant maps** — only 4 of 75 diverge | 4/4 swept, p ≈ 0.06 |
| `replicate.sh`, 150 games | none; fresh 25-map sample | sd 7.34 ⇒ 2-sd floor ≈ **15 games** | +0.07 sd |

A change that fires on a rare code path diverges on a handful of maps, so the
paired instrument runs out of discordant pairs, and determinism forbids simply
re-running it. Meanwhile the unpaired instrument's floor is four times the effect
size. **Every future small-effect arm hits this same wall**, so the fix belongs in
the instrument, not in this arm.

**`tools/paired-roster.sh`** — the candidate against all three lineages on all 75
maps, both sides: **450 games**, paired on **(opponent, map, side)** instead of
(map, side). Same exact pairing, three times the keys, so roughly three times the
discordant pairs. The baseline's own 450-game run is the shared reference and is
computed once; every later arm compares against it for free.

Queued: the baseline reference, then `darla75` on the same ground. `darla75` stays
**undecided** until then — the 4/4 sweep is too suggestive to reject and far too
thin to accept.

## Iteration 77 — don't queue at a dry tower: **+12 games**, the largest move since iteration 1

**87/150 (58.0%)**, +1.96 sd on the paired instrument.

| | |
|---|---|
| maps playing 1–1 | 49 |
| maps diverging | **26** |
| swept 2–0 by `darla77` | **19** |
| swept 2–0 by the baseline | **7** |

Given divergence the direction is the informative quantity, and 19–7 is p ≈ 0.014.
This is not the 4-discordant-map situation `darla75` was stuck in: the mechanism
fires on a third of the pool.

**`Oasis` — the map the diagnosis came from — was swept 2–0**, both sides. That
was the registered prediction: it is the map where `S HOME` was 144 of 183
soldier-turns and where our own paint towers sat at `tp = 0, 5, 10`.

**The falsifier was checked first and came back clean.** Both builds play in the
same replay, so their counters are directly comparable on identical ground
(`AlarmClock` botA, round 300):

| | worst `rt` (latches) | worst `ht` (turns commuting) |
|---|---|---|
| baseline | **5** | **138** |
| `darla77` | **2** | **49** |

The registered refutation was "`rt` climbs sharply while `ht` falls" — a soldier
thrashing between latch and unlatch. The opposite happened: **both** fell.
Unlatching at a dry tower does not send robots back for more, it stops them
queueing in the first place, and the commute time they were burning goes back
into painting. (These are different robot populations, not matched robots, so
this is a population comparison — but the direction is unambiguous and the
falsifier required `rt` to rise.)

**Mechanism, stated in full, because the three arms before it were each one level
too shallow:**

- `darla71`–`74`: the symmetry answer had no branch to act on. Wrong layer.
- `darla76`: the refill target was the wrong *tower type*. Real, but worth +1.
- `darla77`: the refill target had **no paint to give**, and the bot waited
  anyway, because the unlatch condition asks about the robot's paint rather than
  the tower's ability to supply it.

A soldier's attack costs 5 paint. A soldier latched at 60 paint beside a tower
holding 5 has twelve painted tiles available to it and spends the turn walking
instead. That is the whole change.

**Not accepted yet.** `darla65` went +2.5 sd at n=11 and evaporated to +0.57 at
n=18; one head-to-head is one draw. `tools/paired-roster.sh darla77` queued —
450 games against all three lineages on all 75 maps, which is the instrument
built two entries ago for exactly this decision. The baseline's 450-game
reference is queued ahead of it.

### Baseline fresh sample 38: 86/150 — and it sharpens the point above

An unchanged baseline scored **86/150 (57.3%)** on run `20260912-170047`,
**−2.08 sd** and the second-lowest of its 38 samples. Updated distribution:
**mean 102.0, sd 7.71** (was 102.5 / 7.34), which moves `darla75`'s replication
to +0.13 sd.

Worth recording because it is the cleanest possible demonstration of the
instrument gap: **the same build, changing nothing, moved 16 games** — larger
than `darla77`'s entire +12 head-to-head effect. Any conclusion drawn from a
single fresh sample about an effect of that size is noise. The 450-game paired
runs are queued for exactly this reason.

### `darla75` on the 450-game paired instrument: 309/450 (68.7%) — reference still pending

First run of `tools/paired-roster.sh`. Per opponent:

| opponent | won | win% |
|---|---|---|
| alice | 94/150 | 62.7% |
| bob | 110/150 | 73.3% |
| carol | 105/150 | 70.0% |

**This number decides nothing on its own.** The instrument's whole point is
pairing on (opponent, map, side), and the baseline's own 450-game run — the
reference every key is paired against — has not run yet: all three paired jobs
wait on the same lock and `darla75` then `darla77` won the race ahead of it.
Comparing 68.7% here against the baseline's fresh-sample mean of 68.0% would be
comparing all 75 maps to a random 25 of them, which is exactly the
apples-to-oranges the paired design exists to avoid.

`darla75` remains **undecided**; the comparison is one run away.

## `darla77` on the 450-game paired instrument: 326/450 (72.4%), and the instrument earns its keep

Per opponent:

| opponent | won | win% |
|---|---|---|
| alice | 100/150 | 66.7% |
| bob | 113/150 | 75.3% |
| carol | 113/150 | 75.3% |

`darla75` ran the identical instrument (same 75 maps, same three lineages, same
sides), so those two runs are **paired on all 450 keys** without needing the
baseline reference. McNemar on (opponent, map, side):

| | |
|---|---|
| shared keys | **450** |
| `darla77` wins where `darla75` loses | **39** |
| `darla75` wins where `darla77` loses | **22** |
| discordant pairs | **61** |
| χ² | **4.74** (z = 2.18, p ≈ 0.029) |

**61 discordant pairs, against 4 in `darla75`'s head-to-head.** That is the whole
argument for building `paired-roster.sh`: fifteen times the usable evidence from
three times the games, because the pairing is preserved while the keys multiply.
The old choice was an exact instrument with nothing to measure or a noisy one with
a floor four times the effect size.

`darla77` is now ahead of `darla75` at z = 2.18 and ahead of the **baseline** by
+12 games (z ≈ 1.96) on the head-to-head. Two instruments, two references, same
direction. The baseline's own 450-game reference is the one remaining run and
gives `darla77` a direct 450-key comparison — that is the acceptance decision,
and it is deliberately the last thing standing between this arm and the shipped
build.

# ITERATION 2 ACCEPTED — don't queue at a dry tower

The baseline's own 450-game reference landed at **307/450 (68.2%)**, which makes
all three runs paired on the same (opponent, map, side) keys:

| comparison | total | discordant | split | χ² | z |
|---|---|---|---|---|---|
| **`darla77` vs baseline** | **326 vs 307** | **63** | **41–22** | **5.73** | **+2.39** |
| `darla77` vs `darla75` | 326 vs 309 | 61 | 39–22 | 4.74 | +2.18 |
| `darla75` vs baseline | 309 vs 307 | **2** | 2–0 | 2.00 | +1.41 |

**`darla77` is accepted.** +19 games over the baseline on 450 paired keys,
z = +2.39, agreeing with the head-to-head's +12 (z ≈ 1.96) on a different
reference set, with the mechanism confirmed by counters (`rt`/`ht` both falling,
5/138 → 2/49) and the registered falsifier checked and clean before the score was
read. `src/darla` now carries it as `darla-i2`; the outgoing build is frozen at
`src/darla_i1`.

**`darla75` is closed, `measured-and-small`, and its story is a warning.** Two
discordant pairs in 450 keys. Against real opponents the saturated-ban path
essentially never changes an outcome — the eviction policy is correct, and
correctness is not the same as mattering. Its head-to-head looked like p ≈ 0.06
because all four of its diverging maps swept, and four maps is simply not enough
ground to stand on. Had I accepted on that, I would have shipped a no-op and
spent the next arms measuring against a moved baseline.

**What actually produced iteration 2**, in order, because none of it came from
choosing a promising constant:

1. Reading `RESEARCH.md` §6 and failing at it four times.
2. Counting soldier `state` tokens in one replay to find out why — which showed
   the symmetry branch was reached <1% of the time, and incidentally that
   `S HOME` was 63–79%.
3. Following `S HOME` to `rt=1, ht=416` — a soldier latched for refill once and
   commuting for 416 straight turns.
4. Fixing the wrong cause first (`darla76`, tower *type*, +1 and null) and
   letting its registered falsifier point at the right one: the towers are dry.
5. Building the instrument that could actually decide the result.

The shipped bar is unchanged and still met: ≥50% against each lineage
(alice 62.7%, bob 73.3%, carol 70.0% for the new build's arm run) and at least as
good against the benchmark as any previous agent — the latter needs a fresh
benchmark now that the build has moved, since the standing 42.0% vs `v3` belongs
to `darla-i1`.

**Promotion test queued.** The engine is deterministic, so `src/darla`
(`darla-i2`) against the frozen `src/darla_i1` must return **exactly 87/150** —
byte-identical to `darla77` vs `darla`, because the code is byte-identical. Any
other number means the promotion edit is not what I think it is.

### Bookkeeping after the accept: the two builds' samples must not pool

The first fresh sample of `darla-i2` landed immediately — `20260912-192736`,
**100/150 (66.7%)**, alice 66.0 / bob 72.0 / carol 62.0. Against `darla-i1`'s 38
samples (mean 102.0, sd 7.71) that is −0.26 sd, which as established says nothing
either way about a +19/450 effect; it is recorded, not interpreted.

The trap it exposed is real. Every row in `vs_old_bots_history.csv` carried the
label `darla_iter0+cand` — "something after iteration 0, not yet accepted" —
which was correct for all 38 `i1` samples and would have been silently applied to
every `i2` sample too, pooling two different builds into one distribution and
inflating the sd that every future accept decision is measured against.

Two corrections:

1. **The freeze is named `src/darla_iter1`**, not `darla_i1`. `iterN` is the
   convention the tracker's `resolve_cand` already understands, and the rest of
   the project uses. (`src/darla_i1` stays on disk only until the in-flight
   promotion test, launched against that name, finishes.)
2. The new sample is recorded as **`darla_iter1+cand`**, so `i1` and `i2` samples
   are separable from here on.

`tools/track_vs_old_bots.py --all` is **not** the way to do this, and the attempt
is worth recording: it backfilled every arm's screening run into a file that had
only ever held baseline roster runs — 140 rows to 431 — and relabelled the `i2`
sample as `darla_iter1`, since `resolve_cand` cannot tell which `+cand` rows
predate an accept and which follow it. Reverted with `git checkout`. The file is
curated, not derived.

## Iteration 78 — the mopper paint ferry fired ZERO times: untested, not refuted

73/150 (48.7%), **71 of 75 maps identical**, `ov=0`. Its registered falsifier said
a zero `give` count means untested, and that is exactly what happened: **0 give
events** across every replay window sampled.

The replay says why, and it is not subtle. On `Flower`, of 54 mopper turns:

| mopper state | turns |
|---|---|
| `M HOME` | **23** |
| bare `M` (explore) | 24 |
| `M mop` | 6 |
| `M swing` | 1 |

**The mopper is itself commuting for paint on 43% of its turns**, and
`walkHomeIfDry` returns before the hand-off code is ever reached. A unit that is
short of paint cannot be the one distributing it. On two other maps sampled there
were no mopper turns in the window at all.

So the placement is wrong, and possibly the whole shape is: the arm waits for a
mopper to *happen* to stand within r² ≤ 2 of a dry soldier, which is a coincidence
nobody arranged.

**`darla79` registered — instrumentation only, no action.** The rule earned at
`darla74` is to measure how often a branch is reached before improving what it
decides, and I skipped it for `darla78`. Two counters, emitted as `gv=<opp>/<blocked>`:

- `gvOpp` — mopper turns with an ally at or below `REFILL_LOW` within transfer
  range while the mopper holds a surplus. The opportunity rate.
- `gvBlocked` — how many of those the mopper was itself latched for refill, and
  so returned before any hand-off could happen.

Play must be **byte-identical** — the only additions are two counters, one
`senseNearbyRobots(2)` and a string concatenation — so a 1–1 split on all 75 maps
is a built-in check that the instrumentation is inert. `ov` must also stay 0.

The decision it feeds: if `gvOpp` is near zero, the ferry needs moppers to *seek*
dry soldiers rather than pass them, which is a targeting change in
`moveExploring`; if `gvOpp` is healthy but `gvBlocked` accounts for most of it,
the fix is just ordering the hand-off before the mopper's own refill latch.

### `darla78` on 450 paired keys: provably inert, and it verifies the promotion for free

326/450 — the same total as `darla77`. Paired on identical keys:

| comparison | discordant | split | z |
|---|---|---|---|
| `darla78` vs `darla77` | **4** | 2–2 | **+0.00** |
| `darla78` vs baseline `i1` | 63 | 41–22 | +2.39 |

Four discordant pairs out of 450, split evenly. The mopper hand-off is **inert**,
exactly as its zero `give` count said — closed as `untested`, with `darla79`
already queued to find out whether the opportunity even exists.

**The second row is the useful accident.** `darla78` was built from `src/darla`
*after* the promotion edit, and against the same reference it reproduces
`darla77`'s numbers **exactly** — 41–22 of 63 discordant, not merely a similar
total. Since the ferry contributes nothing, that is a 450-key proof that
`src/darla` (`darla-i2`) carries `darla77`'s behaviour and the promotion edit is
what I believe it is. The queued `darla-i2` vs `darla_iter1` head-to-head is now
belt-and-braces rather than the only check.

## `darla80` registered — instrumentation for `RESEARCH.md` §5, before building it

§5 is the most consistent finding in the whole digest: every year, teams start
with textbook pathfinding, blow the bytecode budget, and converge on bug
navigation plus a bounded escape for the concave obstacles greedy movement
actually sticks on. `stepToward` here is memoryless greedy — target direction,
then ±45°, then ±90°, with the left/right tie broken on robot ID — and has **no
stuck detection of any kind**.

Rather than build that on the strength of a document, `darla80` counts the
failure first: consecutive calls toward the **same** target where the distance did
not fall, emitted as `mv=<stuck>/<tries>`. Instrumentation only; play must be
byte-identical, so a 1–1 split on all 75 maps is the check that it is inert.

Timing is deliberate. Iteration 2 removed the supply stall that was consuming
63–79% of soldier turns on some maps; if movement is what wastes soldier turns
now, this is where it shows up first, and if `mv` is near zero then §5 is closed
for this bot the same way §6 was — by measurement rather than by four arms.

## Iteration 79 — the mopper ferry is dead by construction: **this bot has no moppers**

75/150 with **all 75 maps splitting 1–1**, which is the built-in proof that the
instrumentation is inert. `ov=0`. And the counter it was built for reads
**`gv=0/0` everywhere** — not a low opportunity rate, *zero*, including the
`gvBlocked` term.

The spawn census says why, and it is not about placement at all:

| replay, rounds 1–800 | SOLDIER | SPLASHER | MOPPER |
|---|---|---|---|
| `Portal` botB | 16 | 15 | **0** |
| second map | 24 | 29 | **0** |

**Zero moppers in 84 robot spawns.** The unit does not exist in this army, so no
placement of a hand-off could ever have fired, and `darla78`'s zero `give` count
was never about where the code sat.

The mechanism is an interaction between two things already in the notebook, and
neither is a bug:

```java
int roll = rng.nextInt(20);                       // MOPPER_IN_20 = 2, so 10% of rolls
...
final int PAINT_FLOOR = 200;                      // iteration 30, ACCEPTED
if (afford && want.paintCost < UnitType.SOLDIER.paintCost
        && rc.getPaint() - want.paintCost < PAINT_FLOOR) afford = false;
```

Paint costs are **MOPPER 100, SOLDIER 200, SPLASHER 300**. The floor's condition
`want.paintCost < SOLDIER.paintCost` selects **exactly the mopper** — a splasher
at 300 is never gated by it — so a mopper is only ever built by a tower holding
≥ 300 paint. Iteration 2 established what tower paint actually looks like on the
maps where it matters: `tp = 0, 5, 10, 55, 60`. The 10% mopper roll almost always
dies at that gate.

Iteration 30 introduced the floor deliberately, to stop cheap units draining the
treasury away from splashers, and it was accepted on measured evidence. It did
what it was built to do. The unintended consequence — that it also removes the
only unit in the game that can mop enemy paint or transfer paint robot-to-robot —
was never measured, because nothing had ever needed a mopper before.

**`darla78` and `darla79` are closed `structurally-unavailable`**, the same
verdict `RESEARCH.md` §6 got, and for the same kind of reason: the mechanism is
real, the engine supports it, and this bot has nothing to run it with. Closing it
cost two arms, one of which was pure instrumentation — against `darla71`–`74`,
which cost four before I thought to measure.

**The open question this leaves is worth stating and not answering here**: whether
a bot with no moppers is the right bot. That is an army-composition question
touching an accepted iteration, and it needs its own measurement — not a
follow-on to a hand-off that never fired. `darla80`, already queued, is on the
other live thread (`RESEARCH.md` §5, movement).

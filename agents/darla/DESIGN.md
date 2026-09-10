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

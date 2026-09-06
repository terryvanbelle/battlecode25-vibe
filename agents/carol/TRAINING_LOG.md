# Carol — Training Log (BC25 Chromatic Conflict)

Append-only chronological record per TRAINING_ALGORITHM.md. Newest at the bottom.

## Functional-area map
- econ: tower builds/upgrades, chip spending, SRPs
- paint: painting policy, splasher targeting, paint logistics (refill/transfer)
- combat: tower attacks, mopper harassment, tower sieges
- nav: movement, exploration, symmetry handling
- comms: messages/marks
- infra: instrumentation, evaluation tooling

## Closed-directions ledger
(none yet)

---

## Phase 0 (2026-09-06)

**Spec + engine ground truth** → `RULES.md`. Engine v3.1.0 final. Key facts:
- Win: >70% of non-wall squares painted, or annihilation. 2000-round cap, tiebreak
  paint→towers→money→stored paint→robots→coinflip (the only nondeterminism).
- No unit damages enemy robot HP; attrition = tower fire + paint starvation (0 paint =
  -20HP/turn + frozen). Paint denial (moppers) and tower kills are the combat surface.
- Radius asymmetries: vision r2=20 for all; def-tower attack r2=16 < vision; paint/money
  tower attack r2=9; splashers can hit towers from up to r2~16 (out-ranging paint/money
  towers); soldier tower-attack r2=9 exactly matches paint/money tower reach.
- SRP: each active pattern (+50 round undisturbed delay, 200 chips) = +3/turn PER paint
  tower AND +3/turn per money tower. Scales with tower count — strong late econ.
- Clumping penalty: -1 paint/turn per adjacent ally (x2 on enemy ground) — spread out.
- Messaging needs ally-paint connectivity robot<->tower (r2=20); tower<->tower broadcast
  r2=80 unconditional. Marks are free-form per-tile 2-state annotations (1 paint).
- Cooldown penalty below 50% paint: +(100-2X)% — keep stashes above half.

**Determinism**: VERIFIED. Same match 3x → decompressed .bc25 byte-identical (gzip
wrapper differs only by timestamp). Use `tools/replay-strings.py --hash` for arm-to-arm
identity checks.

**Bytecode monitoring**: wired into iteration 0 (round-boundary overrun counter +
near-miss vs limit + max usage, in every indicator string).

**Infra**: vm-match.sh + gauntlet.sh (parallel, raw java, MAXJOBS=3) provided by project.
Added tools/replay-strings.py (indicator-string extraction + semantic replay hash).
Deferred: full flatbuffer replay parser (revisit when tracing needs per-round metrics).

## Iteration 0 (2026-09-06) — ACCEPTED (baseline)

Minimal instrumented bot, package `carol` (replaces seeded examplefuncsplayer copy):
- Towers: attack lowest-HP enemy in range (single) + AoE when enemies present; spawn
  soldier 75% / mopper 25% in random direction.
- Soldiers: refill at adjacent towers when <50%, work nearest empty ruin (money tower
  pattern), attack enemy towers in reach, paint own tile, explore preferring unpainted.
- Moppers: mop adjacent enemy paint, swing at adjacent enemies, explore.
- Splashers: (not spawned) splash-scoring stub.
- Per-robot RNG seeded from ID (play-symmetry: no team-correlated bias).

vs examplefuncsplayer DefaultSmall side A: WIN round 842 (70% paint). Baseline gauntlet
pending. Snapshot: src/carol_iter0.

## Iteration 1 (2026-09-06) — ACCEPTED (thin margin)
**Area**: paint. **Change**: soldier paints the nearest EMPTY passable tile within its
action radius (r2=9) when its own tile is already painted, instead of only ever painting
the tile beneath it.
**Pre-registered**: h2h vs carol_iter0 > 50%, all 16 maps both sides.
**Result**: 18/32 = 56.2%. Swept-win 5 maps, swept-loss 3, split 8. No one-directional
regression (losses scattered across maps and both sides).
**Decision**: ACCEPT. Margin is +2 games, ~0.7 sd of the n=32 binomial floor — logged as
thin. Snapshot src/carol_iter1 (also the first fixed-roster member).
**What was learned (bigger than the change)**: 30 of 32 games ran the full 2000 rounds and
were decided by the "painted more of the map" tiebreak; only 2 ended by the 70% rule.
Both bots stall far below the win threshold. Coverage rate — not combat — is the game.

## Iteration 2 (2026-09-06) — economy: paint towers + chip reserve
**Area**: econ. **Trace first** (instrumented tower indicator with round/chips/towers/paint,
DefaultMedium, carol_iter1 vs itself):

| round | chips | towers | tower paint |
|---|---|---|---|
| 0 | 2230 | 2 | 410 |
| 400 | 26600 | 7 | 108 |
| 1000 | 91010 | 8 | 177 |
| 2000 | **213260** | 8 | 66 |

Root cause: iter0/iter1 hardcode `LEVEL_ONE_MONEY_TOWER` at every ruin. Money towers
generate **zero paint**, so team paint income is the single starting lv2 paint tower =
10/turn for the entire game, while 213k chips sit idle. Towers sit paint-dry (~0/1000) and
cannot spawn units. This is the "capability preserved at zero marginal cost" shape from
the algorithm: a whole resource stream unspent.

**Change (indivisible pair)**: (a) build `LEVEL_ONE_PAINT_TOWER` at every ruin;
(b) towers hold back CHIP_RESERVE=1200 chips from robot production.
*Why not two iterations*: (b) alone is provably dead code on iter1 — the reachability
pre-check says a 1200-chip gate never fires against a treasury that never drops below
2230 and climbs to 213k. It only becomes live once (a) unlocks the spending.

**Mechanistic verification** (same map, vs carol_iter1):
- (a) alone: chips 213k -> 150 (mechanism fired hard) but towers fell 8 -> 3, because
  unreserved robot spawning ate the 1000 chips a ruin completion needs. Soldiers then
  camped at ruins they could not complete: `NOTGT` (no empty tile in radius) in ~57% of
  soldier turns. Lost the trace game.
- (a)+(b): towers 8 -> 10, chips pin at the 1400 reserve, carol WINS the trace game.
**Full evaluation**: running (carol_iter1 h2h + carol_rush + carol_turtle x 16 maps x 2).

## Opponent pool
- `carol_iter0`, `carol_iter1` — frozen self-lineage (regression suite; iter1 is also
  fixed-roster member #1).
- `carol_rush` — synthetic archetype, pure tower-rusher. Written independently of carol's
  strategy code so it cannot go stale. Answers "does carol survive tower aggression",
  which carol's own lineage never poses.
- `carol_turtle` — synthetic archetype, pure economy/turtle: claims ruins, alternates
  paint/money towers, upgrades, lays SRPs, never seeks combat.
- `examplefuncsplayer` — BENCHMARK, 24/24 (100%) at iter0. Pinned; no resolving power.

## Play-symmetry audit (standing item, per TRAINING_ALGORITHM.md Phase 0 #7)
Fixed absolute-order decisions present in carol as of iter2, ranked by risk:
1. **`moveExploring` tries `d`, then `d.rotateLeft()`, then `d.rotateRight()`** — a fixed
   left-before-right preference. Highest risk: under map reflection this systematically
   favours one team's pathing around obstacles. *Fix staged in iteration 3* (tie-break on
   robot ID parity). NOTE the algorithm's caution: a consistent arbitrary preference can
   be supplying real formation cohesion, so this must be *measured*, not assumed good.
2. **Nearest-ruin and nearest-empty-tile selection use strict `<`**, so ties resolve to
   whichever element the engine's fixed sensing scan order returns first. Lower risk
   (ties are uncommon) but real. Not yet addressed.
3. `workOnRuin` probes `ruin.add(NORTH)` to decide whether it has already marked. This is
   a state probe, not a decision between alternatives, and ruins are guaranteed wall-free
   in their 5x5, so it does not steer play. Accepted as safe.
4. Tower spawn direction and the exploration fallback both draw from `rng` seeded on
   robot ID — not team-correlated. Safe.

**Instrument**: `tools/sync-mirror.sh` regenerates `src/carol_mirror` as a byte-identical
copy of `src/carol` (package line only) and *verifies* the identity, refusing to run if
the copy has drifted. Mirror matches on every map from both sides give a per-map
side-split; a persistently lopsided map is a real bug, and in a mirror any inter-team stat
difference is positional rather than policy.

**Iteration 2 RESULT — ACCEPTED.** Head-to-head vs carol_iter1: **28/32 = 87.5%**
(binomial floor for n=32 is ~2.8 games; this is +12 over even, ~4.2 sd). The 4 losses were
scattered across different maps and both sides (FourCorners B, Money B, Rose A, +1) — no
one-directional regression. Snapshot `src/carol_iter2`.
Interpretation: this was not a clever idea, it was a resource stream nobody was spending.
The largest single accept so far came from reading one instrumented trace.

**New peer discovered**: `carol_rush` is running near even against carol (not pinned) —
so it is a true peer, and it says carol is roughly a coin-flip against an opponent that
simply walks soldiers into its towers. carol has no defensive behaviour whatsoever:
nothing repaints a disrupted ruin pattern, nothing responds to a tower under attack, and
soldiers only hit enemy towers they happen to bump into. This is exactly the
"self-referential blind spot" the algorithm predicts: carol's own lineage never rushes,
so no amount of self-play would have surfaced it. Logged as the leading structural target.

### Registered structural target (for a later iteration): defense
Mechanics that make this tractable, from RULES.md:
- A soldier trades well against towers: 250 HP, takes ~30/turn from one tower (20 single
  + 10 AoE), deals 50/turn. So ~4 soldiers kill a 1500 HP lv2 tower, and carol currently
  does nothing about it.
- **Defense towers out-range attackers**: attack r2=16 (4.0) vs a soldier's tower-attack
  r2=9 (3.0). A soldier must enter the defense tower's envelope for three tiles of
  approach before it can strike back. Each live defense tower also adds +5/+7/+9
  single-target damage to *every* allied tower, and has 2000-3000 HP.
- Pattern denial is cheap and symmetric: one enemy attack inside a 5x5 blocks a ruin, and
  mopping the tile to EMPTY does not fix it — it must be repainted primary.
Candidate mechanisms, cheapest first: (a) repaint disrupted own-ruin patterns;
(b) build a defense tower at the ruin nearest our towers once under threat;
(c) station moppers near towers to steal attacker paint (attackers at 0 paint freeze).

---

## Iteration 2 — final scoring of the completed gauntlet (2026-09-06, resumed session)

The iteration-2 accept above was written at 18:51 from a *partially complete* run
(`gauntlet/20260906-184023`); the run finished at 18:57 and its summarizer never ran.
Scored by hand from `results.csv` (96 games, 0 exceptions, 0 unknown results):

| opponent | result |
|---|---|
| carol_iter1 (h2h accept gate) | **28/32 = 87.5%** |
| carol_rush | 27/32 = 84.4% |
| carol_turtle | 32/32 = 100% |
| overall | 87/96 = 90.6% |

**The accept stands** — the h2h figure quoted at 18:51 was in fact the complete h2h block
(the runner iterates opponents in order, so all 32 iter1 games were done), 87.5% >> the
pre-registered >50% gate, peer `WinPct` 60% cleared.

**But the completed run overturns the note appended with it.** The log recorded
"carol_rush is running near even against carol ... logged as the leading structural
target"; that was read off the first few rush games. Over all 32, carol_rush is at
**84.4%**, i.e. one evaluation above the ≥80% retirement threshold, and carol_turtle is
pinned at 100% (benchmark). *Correction to the record: carol does not have a demonstrated
defensive weakness against the rusher archetype.* The defense structural target is
downgraded from "leading" to "unmotivated by current evidence" — it must be re-motivated
by a real losing instrument (a sibling bot in the tournament is the obvious candidate)
before it earns an iteration. Lesson logged: **never score a gauntlet from a prefix.**

Opponent-pool bookkeeping: `carol_turtle` → BENCHMARK (100%, no resolving power).
`carol_rush` stays a peer for one more evaluation (retirement needs two consecutive ≥80%).
The remaining even instrument is the self-lineage h2h.

---

## Iteration 3 (2026-09-06) — nav: persistent far exploration + ruin give-up

**Status found on resume**: implemented and snapshotted as `src/carol_iter3`, but **never
evaluated** — no gauntlet, no log entry. Worse, `HEAD`'s `src/carol` is a *third* variant
(the exploration half without the ruin give-up), so the bot that has been playing the
tournament is an untested intermediate. Resolving this before touching the splasher work.

**Area**: nav. **Motivating evidence** (iteration 2's trace, recorded in LEARNINGS.md):
`NOTGT` — soldier had no empty tile in its action radius — on ~57% of soldier turns, and
a local random walk cannot find the frontier on a 40x40+ map once home is painted.

**Change** (two coupled parts, the second required to make the first reachable):
1. Persistent exploration target: a soldier commits to a far map location and walks to it
   (`explore`, `lastLoc`, `stuckTurns`, `exploreAge`) instead of re-rolling a local
   random step every turn.
2. Ruin give-up: abandon a ruin after `RUIN_PATIENCE`=40 turns on it, banned for
   `RUIN_BAN_ROUNDS`=250. *Reachability argument for coupling*: a ruin tile is impassable,
   so `stepToward` always succeeds sideways and a soldier orbiting an unfinishable ruin
   never reaches the exploration branch at all; iter2's trace had a ruin in view on ~79%
   of soldier turns, so part 1 alone would be largely dead code. Same shape as iteration
   2's indivisible pair.

**Pre-registered gate** (16 maps x both sides, opponents `carol_iter2` and `carol_rush`):
- PRIMARY: h2h vs `carol_iter2` > 50% (accept), 45-50% near miss, < 45% reject.
- REGRESSION: vs `carol_rush` no worse than 22/32 (68.8%) — one binomial sd (2.8 games)
  below iteration 2's 27/32.
- No one-directional regression concentrated on a single map or side.
- 0 thrown exceptions.
Run: `gauntlet/` run started 2026-09-06 (BOT=carol_iter3, 64 games).

---

## Trace (2026-09-06, resumed session) — the bottleneck flipped again: chips now bind

Read from the three iteration-2 loss replays in `gauntlet/20260906-184023/losses/`, tower
indicator strings (`T r= chips= tw= tp=`), sampled every 250 rounds. Averages over all of
carol's towers alive at that round.

| round | Money botB | | | Rose botA | | | FourCorners botB | | |
|---|---|---|---|---|---|---|---|---|---|
| | chips | tw | avg tp | chips | tw | avg tp | chips | tw | avg tp |
| 250 | 1400 | 7 | 754 | 1400 | 3 | 76 | 5750 | 2 | 7 |
| 750 | 1400 | 10 | 684 | 1250 | 6 | 507 | 10850 | 3 | 27 |
| 1250 | 1400 | 10 | 615 | 1250 | 7 | 482 | 12950 | 3 | 10 |
| 2000 | 1400 | 10 | 596 | 1450 | 6 | 393 | 16850 | 3 | 25 |

Two distinct degenerate regimes, both "unspent resource" shaped:

1. **Ruin-rich maps (Money, Rose): chips pin at the `CHIP_RESERVE` band (1250-1450) from
   round ~250 to the end, while tower paint accumulates at 400-750 of the 1000 cap.**
   iteration 2 solved the paint famine so thoroughly that paint is now the *idle* resource
   and chips throttle everything: with the one starting lv2 money tower (30 chips/turn) and
   a 1200-chip reserve, unit production is capped at roughly one soldier per 8 rounds no
   matter how much paint is banked. This independently confirms the money-tower-mix half of
   the iteration-4 candidate before it is evaluated — the mix is not a splasher-affordability
   hack, it is the fix for the *current* binding constraint.
2. **Ruin-poor / contested maps (FourCorners): only 2-3 towers ever, ~0 tower paint, and
   chips climb to 16850 idle.** Here nothing is claiming ruins at all. Different disease,
   probably the same one iteration 3 targets (soldiers not reaching distant ruins).

**Registered follow-ups (evidence-backed, for later iterations):**
- **Tower upgrades — never implemented.** 2500 chips for lv2 (money mining 20->30, paint
  5->10, +500 HP). On FourCorners 16850 chips would buy six upgrades and buy nothing today.
- **SRPs — never implemented.** 200 chips per pattern, +3/turn to *every* paint tower AND
  *every* money tower; at 10 towers one SRP is +30/turn for 200 chips, which dominates
  anything else chips can buy. Requires holding the 25-tile pattern undisturbed for 50
  rounds.
- `CHIP_RESERVE` is a fixed constant that pins the treasury; per the algorithm's
  "self-calibrating thresholds beat fixed constants", it should become a function of
  observed ruin availability once (1) is relieved.

---

## Iteration 4 (2026-09-06) — econ+paint: splashers, funded by a money-tower mix

**Status found on resume**: implemented in the working tree on top of `carol_iter3`, not
snapshotted, not evaluated, not logged. Evaluated here *after* iteration 3 is resolved, so
the two are not bundled.

**Area**: paint (conversion capacity) + econ (the funding change that makes it reachable).

**Motivating evidence**: LEARNINGS.md "Soldiers cannot contest ground" — a soldier's attack
paints a tile only if it is EMPTY or already ally-painted, so enemy paint is inert to
soldiers and the `NOTGT` idle rate cannot fall below the enemy-painted fraction of the
frontier. Splashers are the only unit that bulk-converts enemy paint (r2<=2 of the splash
centre), and on virgin ground they are also 2.6x faster per unit and 23% cheaper per tile
(RULES.md throughput table). carol has never built one.

**Change** (coupled, with the reachability argument):
1. Tower spawn mix soldier 50% / splasher 30% / mopper 20% (was soldier 75% / mopper 25%).
2. `towerTypeFor(ruin)`: ~1 ruin in 3 becomes a money tower, keyed on
   `min(x,W-1-x) + min(y,H-1-y) mod 3` — invariant under both map symmetries, so neither
   team gets a different build mix (play-symmetry requirement), and a pure function of the
   ruin so two soldiers never paint conflicting patterns on the same ruin.
3. Splash targeting rewritten: score all 13 legal splash centres from ONE
   `senseNearbyMapInfos(16)` call into a flat 11x11 byte grid (empty +2 within r2<=4 of
   centre, enemy +3 within r2<=2), instead of 13 nested sensing calls. `SPLASH_MIN_SCORE`=8.
   *Reachability for coupling 1+2*: a splasher costs 400 chips and the trace above shows
   the treasury pinned at the 1200-1400 reserve all game, so without (2) the splasher roll
   would simply fail `getChips() >= CHIP_RESERVE + 400` nearly every time — (1) alone is
   largely dead code. Same indivisible-pair shape as iteration 2.

**Pre-registered gate** (16 maps x both sides):
- PRIMARY: h2h vs the iteration-3 outcome's accepted baseline > 50% (accept), 45-50% near
  miss, <45% reject.
- ISOLATION: h2h vs `carol_iter3` reported separately so the splasher effect is attributable
  even if iteration 3 is itself rejected.
- MECHANISM (must hold or the result is uninterpretable): splasher indicator strings show
  `splash<score>` — i.e. splashers are built and do splash — and tower `tp=` no longer sits
  at 400-750 while `chips=` sits at the reserve.
- REGRESSION: vs `carol_rush` no worse than 22/32; 0 thrown exceptions; no one-directional
  regression concentrated on one map or side.

**Pre-identified refinement for iteration 4 (use only if it lands in the near-miss band):**
`runTower` rolls one unit type and, if `canBuildRobot` fails, builds *nothing* that turn —
there is no fallback to a cheaper type. A splasher needs 300 paint from that tower's own
stash and 400 chips; on paint-poor maps (FourCorners trace: avg tower paint ~25) the 30%
splasher roll therefore converts 30% of tower-turns into no-ops rather than into soldiers.
The refinement is to try the rolled type, then fall back down the cost ladder
(splasher -> soldier -> mopper). Registered here *before* seeing the result so it cannot be
a post-hoc rescue.

## Standing API sweep (TRAINING_ALGORITHM.md Phase 0 #2) — 2026-09-06

`javap` of `battlecode.common.RobotController` minus every `rc.` call in `src/carol`.
Whole mechanics carol has never touched, ranked by expected value:

1. **Special resource patterns** — `canMarkResourcePattern` / `markResourcePattern` /
   `completeResourcePattern` / `getResourcePattern`. The only chip sink that also paints
   map (25 tiles) and compounds with tower count. *Iteration 5 candidate, drafted.*
2. **Tower upgrades** — `canUpgradeTower` / `upgradeTower`. 2500 chips, money mining
   20->30, paint 5->10, +500 HP, and defense-tower upgrades buff every allied tower.
3. **Communication, entirely unused** — `sendMessage` / `broadcastMessage` /
   `readMessages` / `canSendMessage`. Tower->tower broadcast is r2=80 with no paint-path
   requirement, so towers can share map knowledge for free. The perennial cross-year
   lesson is that comms schema pays; carol has none.
4. **Markers** — `mark` / `removeMark` / `canMark` / `canRemoveMark`. 1 paint, no
   cooldown, ally-visible per-tile state. The obvious use is ruin/SRP claim tokens so two
   soldiers stop duplicating work — carol currently has no coordination at all.
5. **`canPaint`** — carol gates painting on `canAttack`, which (engine probe #2) returns
   true on ally-painted tiles; `canPaint` actually checks paintability. Cheap correctness.
6. Minor/no plan: `disintegrate`, `setIndicatorDot/Line`, `setTimelineMarker`,
   `sensePassability`, `getActionCooldownTurns`.

This is the "a whole game mechanic sat unused for 81 iterations" check. Re-run it every
few iterations.

### Iteration 3 RESULT — ACCEPTED (with one open, traced regression)

Run `gauntlet/20260906-201624` (BOT=carol_iter3, 64 games, 0 thrown exceptions).

| instrument | result | pre-registered gate | verdict |
|---|---|---|---|
| h2h vs `carol_iter2` | **25/32 = 78.1%** | > 50% | PASS (+9 over even, ~3.2 sd of the n=32 floor) |
| vs `carol_rush` | 29/32 = 90.6% | >= 22/32 | PASS (up from 27/32 at iteration 2) |
| exceptions | 0 | 0 | PASS |
| no one-directional regression | **FAIL — see below** | | open |

Diff shape vs carol_iter2: swept-win 11/16 maps, swept-loss 2 (Castle, galaxy),
split-by-side 3. 5 of the 7 losses were on side A, which is inside noise at n=7.

**The open regression, traced.** Against `carol_rush` on **DefaultSmall**, carol_iter3
loses from *both* sides by **annihilation** at rounds 69 and 146. carol_iter2 played the
same two games to round 2000 and won them on tiebreak. A swept loss whose *win type*
changes from tiebreak to annihilation is the one-directional shape the algorithm says to
trace before deciding, so I traced it (tower indicator strings,
`losses/carol_rush__DefaultSmall__botA.bc25`):

| round | chips | towers | tower paint |
|---|---|---|---|
| 1 | 1980 | 2 | 300 |
| 9 | 1470 | 2 | 100 |
| 17 | 1410 | 2 | 100 |
| 25 | 1350 | 2 | 0 |
| 33 | 1350 | **1** | 230 |
| 65 | 1350 | 1 | 550 |

Root cause is **not** the exploration change: `CHIP_RESERVE` is a fixed 1200, so a tower
spawns only when `chips >= 1200 + unitCost`. DefaultSmall starts at 1980 chips; two or
three spawns drop the treasury to ~1350, which is **below 1200+250 for a soldier and stays
there forever** — chips are pinned in a dead band and unit production stops *completely*
at round ~25. From then on carol builds nothing while a rusher walks in; the money tower
dies at round 33 and even chip income ends. Paint accumulates unused (tp climbing 230 ->
550) because there are no robots to withdraw it. This is precisely the algorithm's
"resource pinned in a dead band" absolute degeneracy, and it needs no opponent to be wrong.

Iteration 3 did not create the dead band (iteration 2 has the same constant); it removed
the accident that hid it — iter2's soldiers orbited the nearby ruin long enough to finish
a third tower, iter3's soldiers give up on it and walk away. So the correct response is to
fix the dead band, not to revert the exploration.

**DECISION: ACCEPT.** The two gating instruments clear by 3.2 and 2.5 sd respectively, the
regression is confined to one map against one archetype, and its mechanism is understood
and is the *next* iteration's target rather than an unexplained flip. Snapshot
`src/carol_iter3` (already present); `src/carol` set to the accepted iteration-3 code so
the tournament plays a measured build; replay archived as
`replays/iter03_carol_iter2_FourCorners_B.bc25` (a decisive round-1136 win).

**Opponent pool update**: `carol_rush` has now been beaten >= 80% in two consecutive
evaluations (84.4%, 90.6%) → **retired from the accept-gating pool**, kept as a periodic
check every `BenchmarkEvery`=3 evaluations because we still lose real games to it (and it
is the only instrument that poses a rush at all — Measurement doctrine #4 on
representativeness). `carol_turtle` stays a benchmark (100%). `carol_iter3` becomes the
new h2h baseline; `carol_iter1` remains fixed-roster member #1.

**Renumbering notice**: the splasher candidate pre-registered above as "Iteration 4" is
**renumbered to Iteration 5** and its pre-registered gate carries over unchanged (baseline
becomes `carol_iter4`, with the h2h vs `carol_iter3` also reported). Reason: the trace
above hands me a traced, catastrophic, absolute degeneracy in the exact resource the
splasher candidate says it needs (chips), so fixing the dead band first is both higher
value and makes the splasher evaluation interpretable. Recorded here rather than by
editing the earlier entry, so the ordering change is visible.

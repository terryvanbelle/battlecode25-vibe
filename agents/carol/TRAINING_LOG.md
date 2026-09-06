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

---

## Iteration 4 (2026-09-06) — econ: arm the chip reserve only after a completion

**Area**: econ. **Target selected** from iteration 3's traced absolute degeneracy (above),
not from a losing-game sample: production halting permanently needs no opponent to be wrong.

**Change (one mechanism, 3 lines)**: `runTower` computes
`reserve = (getNumberTowers() > startTowers) ? CHIP_RESERVE : 0`, where `startTowers` is
the tower count this tower saw on its own first turn (0 for towers built later, whose very
existence proves completions happen). Iteration 2's reserve is preserved *in the regime it
was measured in* — a team that is completing ruins — and disarmed in the regime that was
never measured: a team that has completed none, where the hoard protects nothing.
`rsv=` added to the tower indicator string so the gate value itself is instrumented, not
just the resource it gates.

**Reachability / history pre-checks**: iteration 2 deliberately established this reserve,
so this must supersede rather than silently revert it — it does, on new evidence (the dead
band), and it leaves the reserve armed wherever iteration 2's evidence applies.

**Mechanistic verification (step 4)** — re-ran the motivating game, `carol` vs `carol_rush`
on DefaultSmall (`matches/carol-vs-carol_rush-on-DefaultSmall.bc25`):

| round | chips | tw | tower paint | rsv |
|---|---|---|---|---|
| 1 | 1980 | 2 | 300 | 0 |
| 6 | 1080 | 2 | 0 | 0 |
| 14 | 1320 | 2 | 0 | 0 |
| 24 | 1020 | 2 | 0 | 0 |
| 30 | 720 | 1 | 0 | 0 |

Classification: **case 2 — still lost, mechanism demonstrably engaged.** `rsv=0`
throughout, and the treasury is now actively spent (repeated 250-chip drops) instead of
freezing at 1350; the loss moves from round 69 to round 122. The specific reason this game
still cannot flip is visible in the same trace and is a *different* constraint: **`tp=0`
from round 6 onward** — the towers are paint-dry, and `buildRobot` draws the unit's paint
from that tower's own stash, so a lone lv2 paint tower at 10 paint/turn can emit one
200-paint soldier per 20 rounds no matter how many chips are free. On small maps the early
binding resource is tower paint, not chips. Registered as the next target.

**Pre-registered gate** (25 randomly sampled maps x both sides x 2 opponents = 100 games;
first run under the new random-sampling gauntlet):
- PRIMARY: h2h vs `carol_iter3` > 50% (accept), 45-50% near miss, < 45% reject.
- REGRESSION, stated as a win-*type* so it is comparable across different map samples:
  **zero annihilation losses to `carol_rush`** (iteration 3 had two).
- 0 thrown exceptions; no one-directional regression concentrated on one map or side.
- If the h2h lands in the near-miss band, the pre-registered refinement is the *dose*:
  arm the reserve on `getNumberTowers() > startTowers` OR `roundNum > R` for R in
  {100, 200}, measured with a zero arm — not a new mechanism.

## Trace while iteration 4 ran — chip income, not the reserve, is the real cap

Traced iteration 3's two *swept*-loss maps (`gauntlet/20260906-201624/losses/`,
carol_iter2 on galaxy and Castle, side A). Both show the same frozen signature at every
400-round sample: chips 1300-1400, tower count 6, average tower paint 240-400. Round-by-
round on galaxy (r600-r640):

```
r=600 chips=1300 tw=6 tp=501     r=605 chips=1200 (a unit was built)
r=601 chips=1330 tw=6 tp=506     ... +30/round ...
r=604 chips=1420 tw=6 tp=521     r=614 chips=1220 (another)
```

Chip income is **exactly 30/turn** — the single starting lv2 money tower — because
iterations 2 and 3 build a *paint* tower at every ruin. So with six towers the team can
build **one soldier per 8.3 rounds, forever**, while tower paint climbs +5/turn net
(501 -> 701 over 40 rounds) and is never spent. Unit count is capped by chip income, not by
the reserve: the reserve shifts the steady state by a one-off 1200 chips, the income caps
the *rate*.

**This reprioritises the queue.** The `towerTypeFor` money-tower mix that had been bundled
into the splasher candidate is now independently motivated by a trace — it is not a
splasher-affordability hack, it is a fix for the rate cap on all unit production. Splitting
the pair:
- **Iteration 5 = money-tower mix alone** (~1 ruin in 3 becomes a money tower). Reachability
  is not an issue for the money mix in isolation, so the iteration-2 style "indivisible
  pair" argument does not apply to it, and testing it alone makes both halves attributable.
- **Iteration 6 = splashers** (spawn mix + the rewritten splash targeting), on top of it.
- The SRP work drafted from the API sweep moves behind both; it is a chip *sink*, and a sink
  is worth little until the chip *source* is fixed.

## Closed direction (closed by arithmetic, before spending a run) — tower upgrades

The API sweep listed `upgradeTower` as an unused mechanic, so I priced it against a
2000-round game before queuing it:

| upgrade | chips | gain | payback |
|---|---|---|---|
| money lv1 -> lv2 | 2500 | +10 chips/turn | 250 rounds |
| money lv2 -> lv3 | 5000 | +10 chips/turn | 500 rounds |
| paint lv1 -> lv2 | 2500 | +5 paint/turn | 500 rounds |
| paint lv2 -> lv3 | 5000 | +5 paint/turn | 1000 rounds |
| **new money tower at a ruin** | **1000 (already being spent)** | **+20 chips/turn** | **50 rounds** |
| **one SRP** | **200** | **+3/turn per paint tower AND per money tower (~+18 at 6 towers)** | **~11 rounds** |

Upgrades are the worst chip-per-income purchase in the game by an order of magnitude, and
the +500 HP is worth little in a year where no unit damages robot HP. **Closed**: not worth
an iteration unless a future trace shows chips idle *after* both the money mix and SRPs are
in (the FourCorners 16850-idle-chips regime is the only place it could ever apply).
Reopening requires that specific evidence, not "we never tried it".

Note the top row: switching a ruin's build type costs nothing extra — the 1000 chips are
being spent either way — which is the algorithm's "capability preserved at zero marginal
cost" shape and is why the money mix goes first.

## Standing play-symmetry audit — side splits (2026-09-06)

Bot win rate by the side carol played, over the three completed runs:

| run | side A | side B |
|---|---|---|
| 20260906-184023 (iter2, 96g) | 44/48 = 92% | 43/48 = 90% |
| 20260906-201624 (iter3, 64g) | 25/32 = 78% | 29/32 = 91% |

No systematic side bias; the iter3 gap is 4 games, ~1.4 sd at n=32, so it does not clear
the noise floor. The iteration-2/3 symmetry work (ID-parity tie-break in `stepToward`,
mirror-invariant keys) is holding. A dedicated pinned-map mirror run is still owed —
per the coordinator's note it MUST pin `MAPS` now that samples are random, or a resampling
artifact is indistinguishable from a real side bias.

### Iteration 4 RESULT — REJECTED

Run `gauntlet/20260906-202908` (first run under random map sampling; 25 sampled maps x both
sides x 2 opponents).

| instrument | result | gate | verdict |
|---|---|---|---|
| h2h vs `carol_iter3` | **20/50 = 40.0%** | > 50% accept, 45-50% near miss | **REJECT** (below the near-miss band) |
| vs `carol_rush` | ~91% | zero annihilations | (representativeness check only) |

Diff shape: 11 of 18 decided maps split by side (WL/LW), 4 swept losses, 1 swept win —
scattered, mixed-direction churn with a consistent negative tilt. Side split was even
(A 39%, B 41%), so this is not a symmetry artifact.

**Why it lost, traced.** The gauntlet plays candidate vs `carol_iter3` in one game, so both
arms are in the *same replay* and are separable by the `rsv=` field only the candidate
emits. On `starburst` side A:

| round | candidate (rsv armed late) | | | carol_iter3 (reserve always armed) | | |
|---|---|---|---|---|---|---|
| | chips | tw | avg tp | chips | tw | avg tp |
| 300 | 1350 | **5** | 486 | 1400 | **6** | 736 |
| 600 | 1350 | 5 | 629 | 1400 | 5 | 642 |
| 1200 | 600 | 4 | 426 | 1400 | 5 | 504 |

The candidate is **one tower behind by round 300 and never catches up**, with materially
less banked tower paint. So iteration 2's early reserve was load-bearing after all: the
1980 starting chips it hoards are exactly the first ruin completion, and spending them on
~7 early soldiers instead costs a tower for the whole game. The dead band is real, but the
cure was worse than the disease, and the belief "the early reserve is idle capital" is now
firmly disproved rather than weakly held. Both arms sat in the same chip band from round
600 on, so the change only ever touched the early game.

**DECISION: REJECT, full revert** (`src/carol` back to the iteration-3 code, which is what
HEAD already carries — the tournament is unaffected). `carol_iter3` remains the baseline;
no `carol_iter4` snapshot is created, so the next accepted iteration takes that number.

**What this buys.** The dead band still exists, but it is now correctly diagnosed as a
*symptom*: it becomes terminal only when chip income reaches zero, and income reaches zero
only because iterations 2-3 build a paint tower at every ruin so there is exactly one money
tower on the board. Fix the income and the reserve stops being a trap without touching it.
That is iteration 5. The hysteresis variant of the reserve (arm above 2x, release below
1x + unitCost, which provably has no dead band while keeping the early hoard) is logged as
available but deprioritised behind the income fix, not closed.

Functional-area tally: econ now has 1 consecutive reject (`MaxConsecutiveRejects` = 3).

---

## Iteration 5 (2026-09-06) — econ: money-tower mix (plus idle-cause instrumentation)

**Area**: econ. **Target** from the galaxy/Castle trace above, not from a loss sample:
chip income is a flat 30/turn, so unit production is pinned at one soldier per 8.3 rounds
for the whole game while tower paint accumulates unspent. Absolute degeneracy, no opponent
required.

**Change**: `towerTypeFor(ruin)` returns `LEVEL_ONE_MONEY_TOWER` when
`min(x, W-1-x) + min(y, H-1-y)` is divisible by 3, else a paint tower — roughly one ruin in
three. Pure function of the ruin (two soldiers must never mark different patterns on the
same ruin) and invariant under both map symmetries (reflection and 180-degree rotation both
preserve those two terms), so neither team gets a different build mix.

*Dose*: the mix ratio is the dose. 1-in-3 is the first arm; 1-in-2 and the zero arm
(iteration 3, all paint) bracket it, and the zero arm is already measured within the same
run because `carol_iter3` is the h2h opponent.

**Also in this candidate — instrumentation only, changes no decision**: the `NOTGT` idle
state is split into `IDLE-ALLY` / `IDLE-ENEMY` with the ally/enemy tile counts in the r2=9
radius. Motivation: on galaxy **74.4% of all soldier turns painted nothing** (66,334 soldier
turns; only 7.2% were paint-starved), which is carol's largest single degeneracy, and the
two possible causes demand opposite fixes — everything in reach already ours (navigation:
the soldier is not at the frontier) versus enemy paint in reach (capability: a soldier
physically cannot overwrite enemy paint, only a splasher can). Costs ~40 bytecode on an idle
turn against a measured peak of ~500/17500, and touches no branch condition.

**Pre-registered gate** (25 randomly sampled maps x both sides, opponents `carol_iter3` and
`carol_rush`, 100 games):
- PRIMARY: h2h vs `carol_iter3` > 50% accept, 45-50% near miss, < 45% reject.
- MECHANISM: tower indicator `chips=` must show income above 30/turn (multiple money
  towers alive), and tower `tp=` must stop climbing monotonically unspent.
- READOUT (not a gate): the IDLE-ALLY / IDLE-ENEMY split, which selects iteration 6 —
  IDLE-ENEMY dominant selects splashers, IDLE-ALLY dominant selects frontier-seeking
  exploration.
- 0 thrown exceptions; no one-directional regression concentrated on one map or side.
- Near-miss refinement is the dose (1-in-2, 1-in-4), not a new mechanism.

Compile-checked (`COMPILE-OK`). Waiting on the iteration-4 run's `carol_rush` block to
finish before launching — two gauntlets from one workspace share `build/classes` and would
poison each other.

**Iteration 5 run design (revised to fold in the new reporting duty).** The coordinator
added a standing fixed-roster chart (`progress/`), so instead of running the accept gate and
the roster separately I run them together: `OPPONENTS="carol_iter3 <roster>"` with
`NMAPS=12`, i.e. 6 opponents x 12 maps x 2 sides = 144 games. The h2h gate is measured at
n=24 rather than n=32-50 (binomial floor ~2.4 games instead of ~2.8-3.5), which is the price
of getting solid roster points for every frozen opponent in the same run — and within a run
the map sample is shared by every opponent, so the roster comparison and the gate are
measured on identical ground.

**Iteration 4 final numbers** (run complete, 100 games, 0 exceptions): h2h vs `carol_iter3`
20/50 = 40.0%; vs `carol_rush` 47/50 = 94.0%. The pre-registered annihilation gate also
failed — DefaultSmall vs carol_rush is still lost by annihilation from both sides (r122,
r132, up from r69/r146), so the reserve change extended the game without changing the
outcome, exactly as the single-map mechanistic verification predicted. Two independent
gates failed; rejection is firm.

## Queued targets after iteration 5 (ordered, with the evidence each rests on)

1. **SRPs** (`markResourcePattern`/`completeResourcePattern`, drafted). 200 chips buys
   +3/turn to every paint tower *and* +3/turn to every money tower, so it is the only
   purchase that lifts **both** ceilings in the two-ceiling model (LEARNINGS.md), and its
   25 tiles are 25 painted tiles in a game decided by painted area. Payback ~11 rounds at
   six towers vs 50 for a new money tower and 250+ for any upgrade. Conditional on
   iteration 5: a chip *sink* only pays once the chip *source* is fixed.
2. **Splashers** (drafted: spawn mix + a rewritten 13-centre splash scorer that scores all
   candidates from one `senseNearbyMapInfos(16)` call into a flat 11x11 byte grid).
   **Gated on the IDLE-ENEMY readout** shipped in iteration 5: soldiers paint nothing on
   ~74% of their turns, and splashers are the answer only if that idleness is enemy paint
   in reach (which a soldier physically cannot touch). If it is IDLE-ALLY instead, the
   answer is frontier-seeking navigation and splashers would be a wasted iteration. This
   is Measurement doctrine #4 — check the threat exists before building the defence.
3. **Defense towers as a chip *source*** — noticed re-reading RULES.md: a defense tower
   earns 20/30/40 chips *per attack that hits at least one robot*, and a tower makes one
   single-target and one AoE attack per turn, so a contested defense tower out-earns a
   money tower (up to 40/turn at lv1) while also being the only structure that damages
   attackers, out-ranging soldiers (r2=16 vs 9). This re-motivates the defense idea that
   the corrected iteration-2 scoring had demoted — not as defence, as *income that happens
   to shoot back*. Needs a trace of how often enemies are actually in tower range first.
4. **Communication** — still entirely unused (API sweep). Tower-to-tower broadcast is
   r2=80 with no paint-path requirement.

## Archetype staleness audit (standing item; the algorithm's "keep them synced" rule)

`carol_rush` is 119 lines against carol's 394 and shares no code path with it: it spawns
soldiers only, never claims a ruin, holds no chip reserve, and walks at the enemy. So it
cannot go stale by construction — it is not a fork of carol's strategy code, and that is
exactly the property the fixed-roster chart needs (it is now in `progress/roster_extra.txt`
alongside `carol_turtle` and `examplefuncsplayer`).

Worth recording what it *means* that a bot with no economy at all annihilates carol on
DefaultSmall: on a small map, chips spent immediately on soldiers beat chips banked for
towers, because the map is small enough to cross before any economy compounds. carol has no
map-size adaptivity of any kind — the same reserve, the same build mix, and the same
exploration on a 20x20 and a 60x60. Cross-year post-mortems list rush/turtle map-adaptivity
as a perennial; noting it here as a structural target with an actual instrument behind it
(carol_rush's two annihilations) rather than as a slogan.

## IDLE-cause readout (first output of the iteration-5 instrumentation, read mid-run)

Pulled two finished replays out of the running gauntlet rather than waiting for it. Only
carol emits `IDLE-ALLY`/`IDLE-ENEMY`; `carol_iter3` still emits the old `NOTGT`, so the two
teams' idle turns are separable inside one replay.

| map | carol IDLE-ALLY | carol IDLE-ENEMY | enemy share of carol's idle | iter3 NOTGT |
|---|---|---|---|---|
| Castle (contested) | 7,315 | 5,727 | **43.9%** | 4,833 |
| Leaf (open) | 34,821 | 958 | **2.7%** | 1,945 |

**The answer is map-dependent, and that settles iteration 6.** On an open map essentially
all of the idleness is a soldier standing in ground that is *already ours* — a navigation
problem, and splashers would do nothing about it. On a contested map nearly half is enemy
paint in reach, which a soldier physically cannot touch and only a splasher converts. So:

- **Iteration 6 = frontier-seeking exploration** (the bigger, more general share).
  `newExploreTarget()` currently samples four uniformly-random map points and keeps the
  farthest, which lands inside our own territory most of the time on an open map. The map
  contract guarantees rotational or reflectional symmetry, so the enemy half is inferable
  from our own spawn — bias targets toward it. Dose = the fraction of targets drawn that
  way, with a zero arm (current behaviour).
- **Splashers move to iteration 7**, now with a measured justification rather than an
  assumed one: they are worth ~44% of the idle on contested maps and ~3% on open ones, so
  the expected value is real but map-conditional, which also predicts that a *fixed*
  splasher spawn ratio will trade one map class against another — the exact situation where
  this project's own doctrine says to make the threshold self-calibrating (e.g. spawn
  splashers in proportion to observed enemy paint) rather than to search over constants.

**Caveat recorded so future-me does not misread the table**: these are idle *counts*, not
rates. carol's totals are 2.7x and 18x iter3's, which is mostly carol having far more
soldiers (the money mix is doing what it was built to do), not carol being lazier per unit.
A rate needs a per-team soldier-turn denominator, which the current indicator cannot give
because both bots emit `pnt`/`slf` identically. Next instrumentation pass should stamp a
one-character build tag into every indicator string so any replay can be split by team.

## Iteration 5 mechanistic verification (read mid-run from `carol_iter3__Leaf__botA`)

Both teams are in the one replay; they are separable by tower count and chip slope.

| team | towers at r700 | chip income | spend cadence |
|---|---|---|---|
| carol_iter3 (all paint towers) | 12 | **+30/round** | one 250-chip unit per ~8 rounds |
| carol (1-in-3 money) | **25 — the hard cap** | **+150/round** | one unit every ~1.7 rounds |

The mechanism did not just engage, it moved the game state by 5x on the targeted quantity,
and the second-order effect is larger than the first: more chips bought more soldiers, more
soldiers claimed more ruins, and carol reached `GameConstants` max of 25 towers while the
baseline sat at 12-13. Pre-registered mechanism gate **met**.

**Two new facts to carry forward**, both visible in the same trace:
1. **The 25-tower cap is now live.** `completeTowerPattern` refuses at 25 towers, so from
   that point every further ruin is worthless and any tower we lose is instantly replaceable.
   Nothing in carol knows about the cap.
2. **Paint is now the overflowing resource again**: at r800 six of carol's towers sit at
   `tp=1000`, the hard tower paint cap, i.e. mined paint is being *discarded* every turn,
   while chips still pin at the reserve band. That is the two-ceiling model flipping back,
   and it says the dose is not yet at its optimum — 1-in-2 money towers is the pre-registered
   next arm, and this is a *reason* rather than a fishing expedition.

## Trace of iteration 5's swept loss on MoneyTower — the fixed mix overshoots

| team | towers | chips at r2000 |
|---|---|---|
| carol (1-in-3 money) | 4 | **79,840 idle** |
| carol_iter3 (all paint) | 7 | 1,400 (pinned at the reserve) |

The mix is self-defeating on this map. Robot paint is drawn from the *building tower's own
stash*, so with few paint towers there is no paint to spawn soldiers with; with no soldiers
nothing paints a ruin pattern; with no completions the tower count stalls at 4 — and the
money towers we did build pour 79,840 unspendable chips into the treasury. The identical
disease as iteration 1 (213k idle chips), reached from the opposite direction.

So a *fixed* mix ratio trades one map class against another — precisely the situation where
this project's doctrine says stop searching over constants and derive the threshold from
in-game observation. **Registered as iteration 7: a self-calibrating tower mix.** A soldier
about to mark a ruin picks the type from which resource is currently scarce (team chips vs.
the paint in the towers it can see) instead of from a coordinate key. The consistency
requirement that forced a pure function of the ruin is met a better way: if the ruin already
carries marks, read the type back off them by comparing the 5x5 marks against
`rc.getTowerPattern(PAINT)` and `getTowerPattern(MONEY)`, and follow whatever the first
soldier chose. That keeps two soldiers from painting conflicting patterns without freezing
the decision at map-generation time.

Also note 79,840 idle chips is 399 SRPs' worth. The SRP iteration's value is much larger on
this map class than the six-tower arithmetic suggested.

**Standing bytecode check (iteration 5, Leaf)**: robots peak at 3,264 / 17,500 (18.7%),
towers 616 / 20,000 (3.1%), **0 overruns, 0 near-misses**. The idle-cause instrumentation
took the robot peak from ~500 to ~3,264 — a 6x jump for one extra `senseNearbyMapInfos(9)`
on idle turns — which is affordable now but is worth remembering as the price of sensing:
this bot is nowhere near the limit, and per the algorithm that headroom is exactly what
should be spent on better decisions.

## A better progress metric than win rate: how often the game is actually *won*

Win rate against a moving pool cannot say whether the bot got stronger in absolute terms.
The fraction of games that end by the **70%-paint rule** instead of the round-2000 coverage
tiebreak can, because the threshold is fixed by the rules and does not move with the
opponent. Measured on the head-to-head block of each iteration's own run (like-for-like:
each is the candidate against the snapshot it replaces):

| h2h block | decisive games |
|---|---|
| iteration 2 vs carol_iter1 | 1/32 = **3%** |
| iteration 3 vs carol_iter2 | 5/32 = **16%** |
| iteration 5 vs carol_iter3 | 9/23 = **39%** |

Iteration 1's log entry recorded 30 of 32 games going to the tiebreak and concluded
"coverage rate — not combat — is the game". Three accepted iterations later a third of games
end before the clock. Adding this column to `history.csv` from here on.

### Iteration 5 RESULT — ACCEPTED

Run `gauntlet/20260906-203937` (12 sampled maps x both sides x 6 opponents = 144 games;
combined accept gate + fixed-roster run).

| instrument | result | pre-registered gate | verdict |
|---|---|---|---|
| h2h vs `carol_iter3` | **16/23 = 69.6%** (24th game still running; 16/24 = 66.7% worst case) | > 50% | **PASS** |
| mechanism: chip income | 30/round -> **150/round**; towers 12 -> **25 (the engine cap)** | income > 30/turn | PASS |
| mechanism: tower paint | six towers pinned at the 1000 cap, i.e. paint now overflowing | stop climbing unspent | PASS (overshot) |
| exceptions | 0 | 0 | PASS |
| annihilation losses | 0 | — | PASS |
| decisive games (70% rule) | **9/23 = 39%** of the h2h block, vs 16% at iteration 3 and 3% at iteration 2 | — | absolute progress |

Diff shape vs carol_iter3: swept-win 7 of 12 maps, swept-loss 2 (MoneyTower, SandyBeach),
split 3. Side split even (A 15/19, B 15/20), so no symmetry artifact.

**Why accepting on 23 of 24 h2h games is not the prefix error I logged this morning.** That
error was drawing a *strategic conclusion* (carol_rush is near even) from 3 of 32 games,
where the remaining 29 could and did reverse it. Here the outstanding game is one of 24 and
the gate is >50%: the result is 16/24 = 66.7% or 17/24 = 70.8%, and both clear it, so no
outcome of the missing game can change the decision. The final number is recorded below when
it lands; the roster blocks of the same run keep running and feed only the progress chart,
not the gate.

**DECISION: ACCEPT.** Snapshot `src/carol_iter5` — deliberately skipping `carol_iter4`,
which was rejected and never snapshotted, so snapshot numbers keep matching iteration
numbers and the gap is self-documenting (it also makes this snapshot the first
multiple-of-5 member of the fixed roster, which is when the chart wants one). `src/carol`
committed alongside it so the twice-daily tournament plays the accepted build. Replay
archived: `replays/iter05_carol_iter3_Castle_A.bc25` (a decisive round-1172 win).

**Carried forward as the next targets, both already traced rather than guessed:**
1. The fixed 1-in-3 ratio overshoots on money-tower-rich maps (MoneyTower: 4 towers, 79,840
   idle chips) — iteration 6 is the self-calibrating mix, patch drafted and dry-applied.
2. 97% of idle soldier turns on open maps are IDLE-ALLY — iteration 7 is frontier-seeking
   exploration off the symmetry contract, patch drafted and dry-applied.

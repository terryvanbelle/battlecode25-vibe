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

---

## Iteration 6 (2026-09-06) — econ: self-calibrating tower mix

**Area**: econ (2nd consecutive attempt in this area after one accept and one reject;
`MaxConsecutiveRejects` is not implicated because iteration 5 was an accept).

**Target** from iteration 5's own traced swept loss: on MoneyTower the fixed 1-in-3 ratio
produced 4 towers and 79,840 idle chips against carol_iter3's 7 towers — too few paint
towers means no paint in tower stashes, no soldiers, no ruin completions, and the money
towers we did build pour unspendable chips into the treasury. A fixed ratio must trade one
map class against another; this project's doctrine (and both predecessor projects') says
that is the moment to stop searching over constants.

**Change**: `towerTypeFor(ruin)` now decides from observation.
1. If the ruin is already marked, read the choice back off the marks and follow it. The
   PAINT and MONEY 5x5 patterns differ at 16 of the 24 markable tiles; offset (-2,-1) is
   secondary in MONEY and primary in PAINT, so one `senseMapInfo` recovers the type. This
   is what preserves the consistency the old coordinate key was there to give — two
   soldiers can never paint conflicting patterns — without freezing the decision at
   map-generation time.
2. Otherwise build whichever resource is scarce: MONEY if the ally towers this soldier can
   sense average >= `PAINT_PLENTIFUL` (500) paint, else PAINT. Robot paint is drawn from
   the *building tower's* stash, so nearby tower stashes are the right measurement, not the
   soldier's own.
3. If no tower is in sense range, fall back to iteration 5's symmetry-invariant key.

**Pre-checks.** *Reachability*: soldiers working a ruin are near their own towers on every
trace so far, so branch 2 is live rather than falling through to 3. *History*: this
supersedes iteration 5's key rather than reverting it — the key survives as the no-tower
fallback, and iteration 5's evidence (chip income was the binding rate cap) is unchanged;
what changes is that the ratio is no longer fixed. *Play-symmetry*: the new inputs are tower
paint and marks, neither correlated with team identity, and the fallback is the same
mirror-invariant key.

**Pre-registered gate** (roster + h2h, same shape as iteration 5):
- PRIMARY: h2h vs `carol_iter5` > 50% accept, 45-50% near miss, < 45% reject.
- MECHANISM: the money/paint split must actually *differ by map* — MoneyTower should show
  more paint towers than 1-in-3 and the idle-chip pile should shrink; a map where the mix
  comes out identical to 1-in-3 everywhere means branch 2 is not firing and the result is
  uninterpretable.
- REGRESSION: no swept-loss map where iteration 5 swept a win; 0 exceptions.
- Near-miss refinement is `PAINT_PLENTIFUL` as the dose (250 / 500 / 750), with the zero
  arm being iteration 5's fixed key.

Blocked from evaluating until `gauntlet/20260906-203937` finishes: its remaining games load
classes from the shared `build/classes` on battlecode-dev, so compiling or launching
anything from this workspace now would poison them. Implemented and dry-applied meanwhile.

**Iteration 5 h2h final**: the 24th game (CastleDefense side A) landed as a loss, giving
**16/24 = 66.7%** vs `carol_iter3` — the worst case computed at accept time, and still
+4.5 games over even (~2.3 sd of the n=24 binomial floor). The accept stands unchanged.

**Iteration 6 launch is chained** behind `gauntlet/20260906-203937` (compile-check + gauntlet
fire automatically the moment `GAUNTLET-COMPLETE` appears), so no VM time is lost to the
serialisation the shared `build/classes` forces. Opponents `carol_iter5` (the gate),
`carol_rush` and `carol_turtle` (fixed-roster points), `NMAPS=20` -> 120 games, which puts
the gate back at n=40 after iteration 5's n=24.

### Session recovery (2026-09-06 ~21:20) — what the SSH hangup did and did not cost

The previous session died to a SIGHUP on claude-driver at ~21:07, not to anything on the
VM. Reconciled on resume:

- `gauntlet/20260906-203937` **finished** (144 games, `GAUNTLET-COMPLETE`, no `!! INCOMPLETE`
  banner) and was recovered by the coordinator with the new `tools/gauntlet-collect.sh`.
  Only the driver-side poll loop was lost. Iteration 5's accept therefore stands on complete
  data, and the h2h final is confirmed at **16/24 = 66.7%** vs `carol_iter3` — exactly the
  worst case computed at accept time.
- The chained iteration-6 launch **did not fire**: the watcher lived on the driver.
  `gauntlet-collect.sh --list` confirms six finished runs on the VM and nothing in flight.
  The serialisation constraint that forced the chaining (shared `build/classes`) is gone
  with that run, so iteration 6 was launched directly instead.
- `src/carol/RobotPlayer.java` still holds iteration 6's patch, intact and uncommitted.
  Re-verified it before launching rather than trusting the note (see below).

**Re-verification of the mark-readback before spending a run.** The patch's correctness
rests on one claim: offset (-2,-1) distinguishes the two tower patterns. Checked against the
decoded constants in `RULES.md` rather than re-asserted. With rows printed y-up, dy=-1 is
`.X.X.` for PAINT and `XX.XX` for MONEY; at dx=-2 that is `.` (primary) and `X` (secondary)
respectively — so `ALLY_SECONDARY -> MONEY`, `ALLY_PRIMARY -> PAINT` is right.

Also traced the failure mode of a *wrong* read, which turns out to be benign: `kind` is used
only by `markTowerPattern` and `canCompleteTowerPattern`. The painting loop reads
`tile.getMark()`, not `kind`, so a soldier that mis-decides paints nothing conflicting — it
simply fails `canCompleteTowerPattern` and another soldier finishes the ruin. The
"conflicting patterns deadlock" I was guarding against cannot occur through this path. Worth
recording because it downgrades the risk of the whole mechanism.

### Instrument correction — two mislabelled rows in `vs_old_bots_history.csv`

Running `track_vs_old_bots.py` on the recovered run exposed that the tool derives
`current_snapshot` from the snapshots existing at collation time, not from the build that
actually played — the exact failure TRAINING_ALGORITHM.md §6 names ("label rows with the
build that actually played"). Two corrections, both to my only absolute-strength instrument:

| row | was | now | why |
|---|---|---|---|
| 20:29:08 vs carol_rush (47/50) | `carol_iter3`, `roster-run` | `carol_iter4rej`, `backfill` | that run was played by the **iteration-4 candidate, which was REJECTED**. `source` is load-bearing: it draws the marker solid, i.e. as if it were accepted lineage. Hollow is the honest marker. |
| 20:39:37 x5 (the recovered run) | `carol_iter3` | `carol_iter5` | played by the iteration-5 candidate, since accepted and snapshotted as `carol_iter5`. |

The x-axis is date, so neither mislabel moved a point; what was wrong was a rejected
candidate being drawn as accepted lineage. Noting the re-clobber hazard: re-processing
either run with `track_vs_old_bots.py` will overwrite these rows with the derived labels
again, because rows are keyed by (date, opponent). Do not re-process those two run ids.

Charts redrawn: 5 accepted iterations (carol_iter0..carol_iter5), 10 history rows.

## RobotController API sweep (2026-09-06, run while iteration 6 evaluates)

TRAINING_ALGORITHM.md Phase 0.2 mandates periodically sweeping the full API for methods the
bot never calls ("a whole game mechanic sat unused for 81 iterations once"). Did it: carol
calls **33** `rc.*` methods. Diffed against `javap battlecode.common.RobotController` on the
3.1.0 jar. **Three entire mechanics are unused:**

| unused mechanic | API | status |
|---|---|---|
| **Special Resource Patterns** | `canMarkResourcePattern` / `markResourcePattern` / `canCompleteResourcePattern` / `completeResourcePattern` / `getResourcePattern` | never called |
| **Tower upgrades** | `canUpgradeTower` / `upgradeTower` | never called |
| **Communications** | `sendMessage` / `broadcastMessage` / `readMessages` | never called — carol has no comms of any kind |

The embarrassing part is that `RULES.md` *already documents all three*, including the line
"Chips accumulate uselessly unless spent on towers/upgrades/SRPs... SRP value scales with
tower count." The digest reached the conclusion; the bot never acted on it. Recording this
as the shape of the failure, not just the instance: **a rules digest is not an instrument.
Only a call-site diff is.** Adding the sweep to the standing per-evaluation checklist
alongside the bytecode check.

**Fresh engine probe** (`javap -constants GameConstants`, not inferred from behaviour):

```
COMPLETE_RESOURCE_PATTERN_COST = 200      RESOURCE_PATTERN_ACTIVE_DELAY = 50
EXTRA_RESOURCES_FROM_PATTERN  = 3         RESOURCE_PATTERN_RADIUS_SQUARED = 8
MAX_NUMBER_OF_TOWERS          = 25        MARK_PATTERN_PAINT_COST = 25
```
`markResourcePattern(MapLocation)` takes a free location — SRP centres are **chosen**, not
pre-placed map features (`MapInfo.isResourcePatternCenter()` reports a completed one). There
is **no constant capping the number of active SRPs.**

### Ranking the three by measured evidence, not appeal

- **Tower upgrades: much weaker than they look.** lv1->lv2 costs 2500 chips for +10
  chips/turn (money) or +5 paint/turn (paint) — a **250-round payback**, and the paint half
  is worthless on maps where iteration 5 already measured towers pinned at the `tp=1000`
  cap. A *new* tower is 1000 chips for +20/turn (50-round payback) and is strictly better
  until the 25-cap binds.
- **SRP: an order of magnitude better.** 200 chips for +3/turn to *every* paint tower and
  +3/turn to *every* money tower. At iteration 5's measured 25 towers (~8 money / ~17 paint)
  that is **+24 chips/turn and +51 paint/turn for 200 chips — an ~8-round payback**, and it
  scales with a tower count that iteration 5 proved now saturates the engine cap. Uncapped
  in count.
- **Comms**: largest scope, no *measured* waste behind it. Deferred.

### The convergence that promotes SRP over frontier exploration

Iteration 7 was registered as frontier-seeking exploration, on the finding that 97% of idle
soldier turns on open maps are `IDLE-ALLY` (34,821 turns on Leaf) — a soldier standing on
ground that is already ours with nothing to paint. Frontier exploration walks those soldiers
to the enemy half.

But an SRP needs exactly one thing: **an idle soldier standing on friendly paint.** The
IDLE-ALLY finding is not only the motivation for exploration, it is the *supply* for SRPs,
and this is the algorithm's named winner's profile verbatim — "capability preserved at zero
marginal cost: spending idle resources". Exploration's payoff is speculative coverage; the
SRP's is arithmetic with an engine constant behind it.

Cheaper than it looks, too: an SRP is 13 secondary + 12 primary tiles, and IDLE-ALLY means
the patch is *already ally paint*, so only the ~13 secondary tiles need repainting (~65
paint) on top of the 200 chips. carol also already owns the machinery — `workOnRuin`'s
mark-then-paint-the-marks loop transfers directly.

**Decision: iteration 7 = SRP. Frontier-seeking exploration demotes to iteration 8** (it is
not withdrawn — the IDLE-ALLY trace still supports it, it is just second in line).

### The one pre-check that is not yet satisfied — logged so it is not skipped

*Reachability of the completion branch.* `completeResourcePattern` needs 200 chips, and
`runTower` spends everything above `CHIP_RESERVE`(1200) on robots, so the treasury oscillates
just above 1200. A naive gate of `CHIP_RESERVE + 200` would sit above the equilibrium band
and **never fire** — precisely the dead-branch failure the algorithm says burned three
iterations in a day. So iteration 7's SRP spend must deliberately *compete* with robot
spawning rather than wait for a surplus that the spawn logic guarantees never appears.

That makes it a change to who draws on a shared capped resource, which triggers §4's caveat:
**the treasury itself must be instrumented in the very first run** (chips, active SRP count,
and chip income per round in the tower indicator), or the result will be uninterpretable in
the same way three prior iterations were. Pre-registering that now.

### Iteration 6 RESULT — NEAR MISS (45.0%), one refinement taken

Run `gauntlet/20260906-212704` (20 maps x both sides x 3 opponents = 120 games). Map sample
is 19 fresh random draws **plus MoneyTower pinned in deliberately**: MoneyTower is the map
the hypothesis was traced on, and the pre-registered mechanism gate is unmeasurable without
it. Noting the deviation from "leave MAPS unset" explicitly — 19/20 of the sample is still a
fresh draw, so the anti-overfitting property is essentially intact.

| instrument | result | pre-registered gate | verdict |
|---|---|---|---|
| h2h vs `carol_iter5` | **18/40 = 45.0%** | >50% accept / 45-50% near miss / <45% reject | **NEAR MISS** (at the exact bottom edge) |
| mechanism: mix differs by map | **yes — verified in two replays** | must differ, else uninterpretable | **PASS** |
| mechanism: MoneyTower tower count | **4-5 -> 8** | more paint towers than 1-in-3 | PASS |
| mechanism: MoneyTower idle chips | 100,190 -> **158,950 (grew)** | should shrink | **FAIL** |
| side split | A 8/20, B 10/20 | even | PASS (no symmetry artifact) |

Diff shape vs `carol_iter5`: swept-win 3 (CastleDefense, DefaultMedium, windmill),
swept-loss 5 (Fossil, Mirage, Money, Portal, UnderTheSea), **split-by-side 12 of 20** — and
the splits run in both directions (7 are A-loss/B-win, 5 are A-win/B-loss). Per measurement
doctrine #7 that mixed-direction scatter is churn; the real signal is the 5-vs-3 swept tilt.

**Mechanism check passed, and this is what settles the refinement direction.** Pulled two
replays mid-run rather than waiting:

- *MoneyTower* (the motivating map): tower paint sits at **0-150 all game on every tower**,
  so `avg >= PAINT_PLENTIFUL(500)` is never true and every ruin becomes a PAINT tower.
  Towers went 4-5 -> 8. The fix worked in the intended direction here.
- *Mirage* (a swept loss): tower paint spans **0-1000**, with 1-5 towers above 500 at any
  time, so the gate genuinely fires and flips. Not dead code.

So the mix really is self-calibrating — but the threshold is set **too high**. Mid-game on a
normal map the tower-paint average sits around 400 (Mirage r1000: `[0,90,225,230,318,440,
560,865,1000]`), i.e. just *below* 500, so carol builds PAINT at nearly every ruin. That
quietly reverts iteration 5's central finding — 1-in-3 money took chip income 30 -> 150/round
and towers 12 -> 25 — which is exactly why it loses 45-55 to iteration 5 while still fixing
MoneyTower.

**Refinement (near-miss #1 of 3): `PAINT_PLENTIFUL` 500 -> 250.** This is the pre-registered
dose and it is verified live in both regimes before spending the run, which is what
measurement doctrine #2 demands:
- Mirage r1000 average 414: `>=500` false -> PAINT, `>=250` true -> MONEY. **Flips.**
- MoneyTower average ~20: false under both -> PAINT either way. **The motivating-map fix is
  preserved.**

That is the whole design goal — money towers on maps that can feed them, paint towers on
maps that cannot — and 500 was simply above the operating band on ordinary maps.

### Correction to the API sweep's ranking: I ranked chip-sinks by chip ROI, and chips are the worthless resource

The MoneyTower trace forces a revision of the ranking I logged an hour ago. I dismissed tower
upgrades on a "250-round payback" computed **in chips**. But that trace shows both teams
ending with **100,190 and 158,950 idle chips** while *every tower sits at tp<=150* — chips
are free and worthless there, and **paint generation is the hard cap**. A lv1 paint tower
mines 5/turn; a soldier costs 200 paint, so one tower funds a soldier every 40 rounds no
matter how many chips are banked.

Repriced in the binding resource:
- **lv2 paint tower**: 2500 (free) chips **doubles** that tower's paint rate 5 -> 10/turn.
- **SRP**: 200 (free) chips adds +3/turn to *every* paint tower. 158,950 idle chips is
  **794 SRPs**.

Both convert the most abundant wasted resource directly into the binding one. SRP still wins
on scaling (it multiplies across all towers), so iteration 7 is unchanged — but **tower
upgrades are promoted from "much weaker than they look" to a genuine candidate**, and the
lesson generalises: *price a sink in the resource that is actually binding, not in the one
it is denominated in.* Adding that to LEARNINGS.md.

**Instrumentation debt now blocking analysis.** Separating the two teams in these replays took
inference from tower counts, because carol and its snapshot emit byte-identical indicator
formats. The iteration-5 log already flagged this; it has now cost real time twice. The
refinement run will stamp a build tag into every indicator string. This is play-neutral —
indicator strings cannot affect the game — so it is instrumentation, not a bundled mechanism.

## Iteration 6b (2026-09-06) — near-miss refinement #1 of 3: `PAINT_PLENTIFUL` 500 -> 250

**Area**: econ (3rd consecutive attempt). `MaxConsecutiveRejects` is not yet implicated —
iteration 5 accepted and iteration 6 is a near miss, not a reject — but if 6b fails the next
attempt must leave econ. Recording that trigger now so it is not negotiated away later.

**Change**: one constant, 500 -> 250. Plus a play-neutral build tag in the indicator string.

**Pre-registered gate**:
- PRIMARY: h2h vs `carol_iter5` > 50% accept, 45-50% near miss (refinement #2), < 45% reject.
- DOSE: h2h vs `carol_i6a` (the 500 arm, byte-identical but for the constant and its tag)
  must be > 50%. This is the arm the whole refinement claims to beat; losing it while beating
  `carol_iter5` would mean the gain came from somewhere other than the dose.
- MECHANISM: on Mirage the money-tower share must rise vs the 500 arm; on MoneyTower it must
  NOT (average tower paint ~20 there is below both thresholds, so that map must be
  *unchanged*). A run where MoneyTower also moves means something other than the dose changed.
- REGRESSION: no new swept-loss map that the 500 arm swept as a win; 0 exceptions.

**Design of the run**: `MAPS` **pinned to `gauntlet/20260906-212704/maps.txt`** — the same 20
maps as the 500 arm. AGENT.md's default is a fresh random sample, and that is right for an
accept gate, but this is a dose comparison and doctrine #1/#2 want the two arms measured on
identical ground. `OPPONENTS="carol_iter5 carol_i6a"` -> 2 x 20 x 2 = 80 games. Both arms
were built from the same file (`src/carol_i6a/` differs from `src/carol/` in exactly two
lines: the constant and the build tag), so this is a true zero-vs-dose comparison rather than
two independently-written bots.

**Arm-to-arm identity check** (doctrine #3) planned before interpreting anything: hash the
250-arm's replays against the 500-arm's from run 20260906-212704 on the same (map, side).
All-identical would mean the constant never changed a decision and the result is the same bot
measured twice. Some identical games are expected and fine — MoneyTower's should be identical
by the mechanism prediction above, which makes that map a built-in positive control.

## Engine probe — the SRP payout, read out of the bytecode (settles iteration 7's ROI)

Disassembled `InternalRobot.processBeginningOfRound()` rather than trusting the digest,
because iteration 7's entire case is this one formula. It reduces to:

```java
if (type.paintPerTurn != 0) addPaint(type.paintPerTurn + 3 * numSRPs);          // per PAINT tower
if (type.moneyPerTurn != 0) teamInfo.addMoney(team, type.moneyPerTurn + 3 * numSRPs); // per MONEY tower
```
(`extraResourcesFromPatterns(team)` is literally `getNumResourcePatterns(team) * 3`.)

`processBeginningOfRound` runs **per robot**, so the bonus is applied once per tower, gated
on that tower's own type. Confirms the per-tower reading, and sharpens the ROI beyond what I
logged earlier:

- A lv1 paint tower mines **5** paint/turn. Ten SRPs make it **5 + 30 = 35/turn — a 7x
  multiplier** on the resource the MoneyTower trace showed to be the hard cap.
- The lv2 upgrade buys **+5**/turn for 2500 chips. One SRP buys **+3/turn to every paint
  tower simultaneously** for 200 chips.

So the two candidates are not close, and the earlier ranking correction stands but understated
it: SRPs beat upgrades by more than an order of magnitude once the bonus is counted per tower.

`isValidPatternCenter(loc, isTower)` also disassembled: requires only `2 <= x < W-2`,
`2 <= y < H-2`, and (for SRPs) `areaIsPaintable(loc)` — every one of the 25 tiles free of
walls and ruins. **There is no engine constraint against SRPs overlapping each other**; the
only thing stopping two SRPs sharing tiles is that both patterns must hold simultaneously.
The map-centre lattice in the iteration-7 draft avoids the issue by construction, and the
draft must also skip centres whose 5x5 contains a wall, not just a ruin.

## DEGENERACY FOUND: the CHIP_RESERVE dead band is still live and still fatal

Iteration 6's run lost to `carol_rush` on DefaultSmall by **annihilation at round 69**.
LEARNINGS.md records that exact signature — "production stopped completely and permanently at
round 25, with a full paint stash and 1350 chips unspent, ending in annihilation at round 69"
— under the heading "Fixed constants rot into dead bands". **The lesson was written and the
code was never changed.** Same pathology as the API sweep two hours ago: the diagnosis lives
in my notes, the bot is unaffected.

Traced the replay rather than assuming it was the same bug. Tower indicator, side A:

| round | chips | towers | tower paint |
|---|---|---|---|
| 1-25 | 1230-1530, moving | 2 | 100 -> 0 |
| **26** | **1350** | **1** | 160 |
| 30 | **1350** | 1 | 200 |
| 40 | **1350** | 1 | 300 |
| ... | **1350, never once changing** | 1 | climbing to full |
| 69 | — | 0 | annihilated |

The arithmetic, with costs re-read from `RULES.md` rather than recalled: `runTower` builds only
when `chips >= CHIP_RESERVE(1200) + want.moneyCost`, and a soldier costs **250** chips, a
mopper **300**. So the build gate is **1450** (soldier) or **1500** (mopper). Once the last
money tower dies, team income is 0 and the treasury freezes — here at exactly **1350**.

**1200 <= 1350 < 1450: the treasury is above the reserve and below the gate, permanently.**
Unit production stops for good at round 26, with a paint tower filling to its cap and 1350
chips banked, and the bot is killed 43 rounds later without building a single robot. The
reserve is protecting a 1000-chip tower completion that can never happen because it also
prevents building the soldiers that would complete a ruin.

This is an *absolute* degeneracy — "our bot stalls at round N" — which the algorithm ranks
above any opponent-relative signal, and it needs no opponent to be wrong.

### Iteration 7 (promoted): make the reserve self-cancelling when income stops

Registered now, ahead of SRPs, because it is smaller, safer, and converts guaranteed losses.

**Change** (in `runTower`, ~6 lines): a tower remembers last turn's chip total. Chips rise
every round there is income and fall whenever anything is built, so "chips did not increase
for N consecutive turns" is a direct, self-calibrating read of *income has stopped and nothing
is being built*. In that state the reserve cannot ever be reached, so hoarding is strictly
fatal — drop it to 0 and spend.

```java
int chips = rc.getChips();
stagnant = (lastChips >= 0 && chips <= lastChips) ? stagnant + 1 : 0;
lastChips = chips;
int reserve = (stagnant >= STAGNANT_ROUNDS) ? 0 : CHIP_RESERVE;   // dose = STAGNANT_ROUNDS
```

**Pre-checks.** *Reachability*: the trace above is the branch, and it holds for 43 consecutive
rounds in this game alone. *History*: this does **not** revert iteration 2's reserve, which was
accepted on a real tower collapse and stays fully armed whenever income is positive — it only
covers the regime iteration 2 never measured, which is the precise rule LEARNINGS.md already
derived ("arm a reserve only once the thing it protects is demonstrably happening").
*Play-symmetry*: inputs are team chips and a turn counter, neither correlated with team
identity. *Trigger frequency*: must be checked across other replays before the run — if
`stagnant` climbs during normal play the reserve would be disarmed when it is still wanted,
which is the one way this change can do harm.

**Pre-registered gate**: h2h vs the then-accepted snapshot > 50%; MECHANISM — zero games where
chips sit unchanged for >20 consecutive rounds while towers stand (that counter goes in the
indicator, per LEARNINGS.md's own unimplemented advice to "instrument the gate value itself");
REGRESSION — no loss of the tower-collapse protection, checked as tower count never falling
below iteration 5's on the same maps. Dose = `STAGNANT_ROUNDS` (5 / 10 / 20), zero arm = the
current always-armed reserve.

**SRPs move to iteration 8.**

### Iteration 7 trigger-frequency pre-check — a clean separation, and one design correction

The algorithm's §3 pre-check asks how often the triggering condition fires in *other* games,
because "helps the diagnosed case, hurts broadly" is the recognisable failure shape. Measured
the longest run of consecutive rounds with the treasury exactly unchanged while towers stand,
across every `carol_rush` game I have (that opponent emits `RUSH -> [..]` indicators, so its
replays isolate carol's own treasury cleanly — no team-separation guesswork):

| map | outcome | longest frozen-treasury run | frozen at |
|---|---|---|---|
| DefaultMedium | LOSS | **1887 rounds** (r113 -> r2000) | 290 chips, 3 towers |
| Fossil | LOSS | **1881 rounds** | 1220 chips, 2 towers |
| DefaultSmall | LOSS (annihilated r69) | **44 rounds** | 1350 chips, 1 tower |
| Leaf | WIN | **0** | — |
| Portal | WIN | **0** | — |
| windmill | WIN | **0** | — |

**All three losses to `carol_rush` are this one bug, and it fires in none of the wins** — zero
false positives across 2,955 won rounds. The condition cannot disarm the reserve in a game
that is going well, because while any money tower lives the treasury changes every single
round. That is as clean a trigger-frequency result as this project has produced, and it also
re-prices the fix: `carol_rush` was 37/40, and all three losses are potentially recoverable.

**All three are recoverable by the same one-line disarm**, which I checked rather than
assumed: the frozen totals are 290, 1220 and 1350 chips, and a soldier costs 250 — so with
the reserve dropped to 0 the bot can build in *every* one of them. (I had expected
DefaultMedium's 290 to be beyond help; it is not.)

**Design correction found by this check.** My first sketch used `chips <= lastChips`. That is
wrong: heavy spending also drives chips down, so a healthy build spree would count as
stagnation and disarm the reserve exactly when it is doing its job. The condition must be
`chips == lastChips` — strict equality is what means *income is zero AND nothing was built*,
which is the only state where the reserve is unreachable. The three frozen traces hold exact
equality for hundreds of rounds, so the strict test loses nothing.

### Opponent-pool classification update (required by the algorithm, overdue)

Reclassifying from results rather than habit:

| opponent | last two evaluations | classification |
|---|---|---|
| `carol_turtle` | 24/24 (100%), 40/40 (100%) | **RETIRE from the gauntlet pool.** Beaten >=80% twice consecutively and now literally unbeaten in 64 games — it has zero resolving power and every game spent on it is shared VM time bought back nothing. |
| `carol_rush` | 24/24 (100%), 37/40 (92.5%) | **Demote to benchmark; stop gating on it.** Above 80% twice, so the retirement rule applies — but the rule also says *never retire an opponent we lose to*, and it took 3 games off us. Those 3 are the whole frozen-treasury bug, so it is currently the only instrument that surfaces the degeneracy. Keep it, play it less often. |
| `carol_iter5` | 45.0% | **peer**, the accept gate. |

Both stay in `progress/roster_extra.txt` regardless — the fixed-roster chart wants opponents
that never change, and a line pinned at 100% there correctly reads "this instrument is spent"
rather than being noise. Retirement is from the *gauntlet pool*, which is a different thing;
noting the distinction because conflating them would either corrupt the chart or waste games.

`carol_turtle`'s retirement frees ~40 games per run — enough to widen `NMAPS` from 20 to 25
at no extra cost, which buys real resolution on the accept gate.

### Secondary prediction registered for 6b, before its results land

The frozen-treasury trace says DefaultMedium sat at **290 chips with 3 towers standing** for
1,887 rounds. Income zero with three towers alive means *all three are paint towers* — which
is exactly what iteration 6's `PAINT_PLENTIFUL = 500` produces once tower paint drops below
the threshold, since it then answers PAINT at every ruin. **So iteration 6 plausibly made the
frozen-treasury degeneracy more common, not less.**

That gives 6b a second, independent prediction to check, registered now rather than
rationalised later: lowering the threshold to 250 restores money towers, and money towers are
what keep income positive, so **6b should show strictly fewer frozen-treasury rounds than the
500 arm on the same maps**. `carol_i6a` is in the run precisely so this is a within-run,
same-map comparison. If 6b wins the h2h *and* reduces frozen rounds, the two independent
instruments agree and the accept is much better founded than a bare 50-something percent —
which is what measurement doctrine #10 asks for.

### The deeper root cause behind DefaultMedium: iteration 6's rule is one-sided

Pushed the DefaultMedium trace further, because the reserve disarm only *partly* rescues it
and I wanted to know what the rest of the gap is. carol sat at 290 chips with **3 towers**
standing for 1,887 rounds. The engine starts each team with exactly one paint tower and one
money tower (`NUMBER_INITIAL_PAINT_TOWERS = 1`, `NUMBER_INITIAL_MONEY_TOWERS = 1`), so income
zero with three towers alive means the starting money tower died and **every ruin carol
completed afterwards became a paint tower**.

Disarming the reserve buys one soldier there (290 chips, soldier 250) and no more — carol can
never build another tower, because `completeTowerPattern` needs 1000 chips it will never earn
again. So the reserve fix converts an inert loss into a fighting loss on that map, which is
worth having but is not the cure.

The cure is upstream, and looking for it exposed a real gap in iteration 6 itself:

```java
return (paint / towers >= PAINT_PLENTIFUL) ? MONEY : PAINT;   // chips are never read
```

The rule is described in my own log as "build whichever resource is currently scarce", but it
**only ever measures paint**. `rc.getChips()` is sitting right there, is team-wide and exact,
and is never consulted. So the rule cannot distinguish "paint is scarce" from "paint is scarce
*and we also have no income at all*", and in the second case it does the one thing that
guarantees the game is unrecoverable: it builds another paint tower.

That is a one-sided implementation of a two-sided idea, and it is very likely a large part of
why iteration 6 measured 45% — it can walk a team into permanent zero income and has no term
that objects.

**Registered as iteration 9 (candidate): a genuinely two-sided mix.** Compare the two
scarcities instead of testing one — e.g. build MONEY when chips are the binding side
(`getChips()` low relative to what a tower completion costs) and PAINT when nearby tower
stashes are, with the existing mark-readback and symmetry-invariant fallback untouched. It
also subsumes the "never let the last money tower go unreplaced" case without needing to count
tower types.

Deliberately *not* folding this into 6b or iteration 7: 6b is already running as a clean
single-constant dose, and iteration 7 is a separate mechanism with its own pre-checks done.
Bundling either would make all three uninterpretable. Order stands: 6b -> 7 (self-cancelling
reserve) -> 8 (SRPs) -> 9 (two-sided mix), each measured alone.

### STOP — iteration 7's accept gate would have been blind to it (doctrine #4 caught this)

Before building the reserve fix I measured how often the frozen treasury appears in the games
the **accept gate** actually plays: all 22 head-to-head loss replays vs `carol_iter5`, using a
two-team chip-series splitter (cluster each round's two `chips=` values by continuity, skip
rounds that don't resolve).

| instrument | replays | longest frozen-treasury run |
|---|---|---|
| h2h vs `carol_iter5` (the accept gate) | 22 losses | **21 of 22 are 0-4 rounds**; one outlier (rain botB, 233) |
| vs `carol_rush` | 3 losses | **1887 / 1881 / 44** |
| vs `carol_rush` | 3 wins | 0 / 0 / 0 |

**The degeneracy is essentially absent from the accept gate and concentrated entirely against
the rusher** — and the reason is mechanical: the treasury only freezes when the last money
tower dies, and killing towers is something `carol_rush` does and my own lineage does not.

This is measurement doctrine #4 verbatim: *"an even instrument cannot measure a defense
against a behavior its opponents never perform — a mirror proved a defensive feature
'worthless' that was in fact worth several games against rushers, because the lineage never
rushes. For any defensive feature, first check whether the evaluating opponents pose the
threat at all."* I was one step from spending a run whose primary gate physically could not
see the effect, then reading the inevitable ~50% as a rejection and closing a direction that
is worth three games.

**Revised iteration 7 evaluation design, pre-registered:**
- **PRIMARY = the mechanism**, not the h2h: zero games in which the treasury sits unchanged
  for >=50 consecutive rounds while towers stand. This is an *absolute* degeneracy — no
  opponent is needed for it to be wrong — which is the class the algorithm ranks above
  opponent-relative signals in the first place.
- **CONFIRMATION = `carol_rush`**, the only instrument in the pool that poses the threat.
  37/40 -> 40/40 is the ceiling. Noting honestly that a 3-game move on n=40 is at the
  binomial noise floor and is corroboration, not proof.
- **h2h vs the accepted snapshot: expected to be flat, and pre-committed as NOT a rejection
  signal.** It gates only against regression — a h2h *below* the near-miss band would mean the
  disarm hurt normal play, which is the one real risk.
- The `carol_turtle` retirement pays for this directly: those ~40 freed games become a wider
  `carol_rush` block, which is where the resolution has to come from.

**Pool consequence.** The lineage cannot generate this threat, so it cannot regression-test
against it — the self-referential blind spot in its exact textbook form. `carol_rush` is
currently the only mitigation and it is nearly spent as an instrument (92.5%). The right
answer is a *second* tower-killing archetype tuned to be even rather than lopsided, and the
tournament (Alice and Bob are independent lineages that may well pressure towers) is the other
sanctioned source. Registering the archetype as real work, not a nice-to-have.

### New synthetic archetype: `carol_decap` (economic decapitation)

Built during the 6b wait, to close the blind spot the doctrine-#4 catch exposed. Derived from
carol's own trace, not from theory: the fatal event is the **last money tower dying**, after
which income is zero and the treasury freezes forever. `carol_rush` triggers that only
incidentally — it hunts whichever tower is nearest and weakest — and wins 7.5% of its games,
which is far too lopsided to resolve a 3-game effect.

`carol_decap` does the same thing deliberately:
1. **Money towers outrank every other target** at any visible range.
2. **Focus fire by lowest ID**, so every soldier picks the same tower. Spreading damage is
   worthless against towers specifically: a money tower at 1 HP still generates full income,
   so partial damage buys exactly nothing.
3. **It keeps an economy**, which `carol_rush` does not — soldiers claim ruins as paint towers
   and its towers hold 1000 chips back. carol_rush's all-in soldier spend is precisely why it
   starves on large maps and never gets to apply the pressure this instrument exists for.

Written from scratch rather than forked from carol's strategy code, per the pool rules —
a forked archetype goes silently stale and inflates win rates (the project's own recorded
62.5%-read-as-95.0% failure). API names verified against `javap RobotInfo` / `UnitType`
rather than recalled, and the whole `src/` tree compile-checked on the VM (COMPILE-OK) using
`tools/vm-compile.sh`, which builds to `/tmp` and so cannot disturb the gauntlet running off
the shared `build/classes`.

**Its value as an instrument is evenness, not strength**, and that is an empirical question:
if it lands in the 30-90% band it is a peer and becomes the regression test for every
economy change from here. If it comes out as lopsided as `carol_rush`, that is a negative
result about the instrument and gets logged as one rather than quietly reused. Measured on
its first appearance in a gauntlet, after iteration 7.

Same compile check also confirms the **6b candidate compiles**, so the run cannot fail on a
build error.

### Functional-area map (kept current, per §1's "track functional areas, not just games")

| iteration | area | outcome |
|---|---|---|
| 1 | paint | accepted |
| 2 | econ | accepted |
| 3 | nav | accepted |
| 4 | paint + econ | **rejected** |
| 5 | econ | accepted |
| 6 | econ | **near miss (45.0%)** |
| 6b | econ | running |
| 7 (queued) | **robustness** (degeneracy fix) | — |
| 8 (queued) | econ (SRPs) | — |
| 9 (queued) | econ (two-sided mix) | — |

`MaxConsecutiveRejects` is **not** triggered — econ has one reject, one accept and one near
miss, not three consecutive rejects — so the letter of the rule permits continuing. But the
concentration is worth naming honestly: **six of the last seven attempts, and two of the three
queued, are econ.** The spirit of §1 is that a thread can close without anyone noticing.

Two things keep this from being that failure, and I want them written down so the claim can be
checked later rather than assumed:
- Iteration 7 is not an econ *strategy* bet at all. It is a robustness fix for an absolute
  degeneracy with a mechanism gate, a perfect trigger-frequency separation (fires in 3/3
  losses, 0/3 wins) and a known cause. Reclassified as `robustness` for exactly that reason.
- Iteration 8 (SRPs) is econ, but it is not another turn of the same screw — every previous
  econ attempt tuned the *ratio between two tower types*, whereas SRPs are an entire unused
  game mechanic with a 7x effect on the binding resource. Same area label, different thread.

**Standing trigger**: if 6b rejects and iteration 9 (the two-sided mix) also fails, that is
three econ tower-mix attempts closed and the mix thread is done — the next attempt after that
must leave econ entirely, and the candidates are nav (frontier-seeking exploration, already
traced at 97% of idle turns on open maps) and combat/micro, which this lineage has never
touched at all.

### 6b arm-to-arm identity check — the positive control passes exactly

Doctrine #3 says count how many `(opponent, map, side)` games are byte-identical between two
arms before interpreting anything. Ran it on MoneyTower, which I had pre-registered as the
**positive control**: average tower paint there is ~20, below *both* 500 and 250, so the two
arms must make identical decisions and the game must be identical.

First attempt failed for an avoidable reason: the raw replay hashes differ
(`f632ac35…` vs `b70331…`, 7,555,148 vs 7,705,908 bytes). That is not a behavioural
difference — it is the `[i6b]` build tag I added to every indicator string. ~25,000 indicator
strings x 6 bytes accounts for the entire 150,760-byte gap.

**The tag is play-neutral but it is not measurement-neutral**, and I should have seen that
before adding it in the same build: it defeats the one check that proves two arms are the same
bot. Logging it as a real cost of the instrumentation, not a footnote.

The check still works one level up, on behaviour rather than bytes — extract the tower
indicator trajectory (`T r=… chips=… tw=… tp=… e=…`) from both replays and diff:

```
24,350 lines from the 500 arm
24,350 lines from the 250 arm
IDENTICAL
```

**Exactly identical, every round, both teams.** So:
1. The pre-registered mechanism prediction is confirmed — the dose changes nothing on
   MoneyTower, as it must, which means the motivating-map fix from iteration 6 is preserved
   intact rather than traded away.
2. The engine is confirmed deterministic on this build pair, so any difference on the other
   19 maps is caused by the dose and nothing else.
3. The arms are demonstrably *not* the same bot measured twice on those other maps (games are
   already flipping), so the run is interpretable.

**Method fix carried forward**: compare arms on the indicator trajectory, not the replay hash,
whenever the arms differ in instrumentation. Better still, keep the tag constant across a dose
pair — `carol_i6a` and the candidate should have shared one tag and differed only in the
constant, and then the raw hash would have worked.

### The one h2h outlier, checked — and a moderation of the previous claim

`rain botB` was the single head-to-head replay showing a long frozen treasury (233 rounds), so
I traced it rather than leaving it as an unexplained outlier.

| round | (chips, towers) per team |
|---|---|
| 200 | (1400, 5) (1400, 6) |
| 600 | (1400, 5) (1400, 7) |
| 900 | (400, 5) (1150, 7) |
| 1300 | (1400, 6) (1400, 7) |
| 2000 | (500, 3) (1400, 6) |

The freeze here is **transient, not terminal**: chips move again by r900 and the team recovers.
And note where it rests — **exactly 1400 chips**, repeatedly. The soldier gate is
`1200 + 250 = 1450` and the mopper gate `1500`, so **1400 sits inside the dead band**; the
treasury is idling one build short of the threshold, with 5-7 towers standing, on a map where
nobody is killing towers.

Two consequences, one of which moderates what I wrote earlier:

1. **The h2h is not completely blind after all.** I claimed it "physically cannot see" the
   fix. That is right for the *terminal* form (which needs the last money tower to die) but
   too strong for the *transient* form, which does occur in ordinary play. The gate will see a
   little of the effect. The restructured mechanism-primary gate stands — 1 of 22 replays is
   still far too thin to gate on — but the claim as written overstated it, and I would rather
   correct it here than have it quoted back at me later as established.
2. **The trigger stays rare enough to be safe.** 21 of 22 h2h loss replays show 0-4 frozen
   rounds and three won games show 0, so `STAGNANT_ROUNDS = 10` still fires almost only in the
   terminal case. Had transient freezes been common, disarming the reserve during them would
   risk spending the very chips that protect a ruin completion — that was the live risk, and
   this measurement retires it.

### Iteration 6b RESULT — 47.5%, and the paired diff closes the whole tower-mix thread

Run `gauntlet/20260906-214451`, same 20 pinned maps as the 500 arm, so the comparison is
**paired game-for-game** rather than two independent samples.

| instrument | 500 arm | 250 arm |
|---|---|---|
| h2h vs `carol_iter5` | 18/40 = 45.0% | **19/40 = 47.5%** |
| side split | A 8 / B 10 | A 8 / B 11 |
| swept-win / swept-loss | 3 / 5 | 4 / 5 |

**Paired diff — only 3 of 40 games changed outcome at all:**
```
unchanged           37
LOSS -> win (250)    2   Portal B, Snowglobe A
win -> LOSS (250)    1   galaxy A
```
Net +1 game against a binomial noise floor of ~3.2 games (1 sd at n=40). **That is noise**, and
the flips are scattered and mixed-direction, which doctrine #7 classifies as churn.

**Then the arm-to-arm identity check explains why, and it is the real finding.** Compared
indicator trajectories on five maps whose outcomes were unchanged:

| map | trajectories | dose |
|---|---|---|
| Mirage | differ, 31,274 lines | **engaged hugely** |
| Leaf | differ, 59,798 lines | **engaged hugely** |
| Fossil | identical | did not engage |
| UnderTheSea | identical | did not engage |
| windmill | identical | did not engage |

So the dose is not dead — on Mirage and Leaf it rewrites essentially the entire game — but
**where it engages most, the outcome does not move at all.** Tens of thousands of differing
robot-turns, same winner. On the other three maps tower paint never crosses between 250 and
500, so the arms are literally the same bot.

That is this project's recurring pattern in its purest form, and LEARNINGS.md already names it:
*"metrics that improve without converting to wins"*. Here it is a whole mechanism engaging
without converting.

**DECISION: REJECT iteration 6/6b.** Reverting `src/carol` to iteration 5's fixed
symmetry-invariant key. Two doses (500, 45.0%; 250, 47.5%) both sit below the fixed key they
replace, the trend toward it cannot continue — threshold 0 means *always MONEY*, which
iteration 5's MoneyTower trace already showed is disastrous — and the paired diff says the
lever does not reach the scoreboard. Refinements #2 and #3 are available under the near-miss
rule and I am **declining them**: a third constant on a lever measured not to convert would be
searching over constants, which is exactly what the doctrine says to stop doing.

**Closed-directions ledger entry.** *Tower mix by observed tower-paint scarcity (paint-only,
self-calibrating)* — CLOSED. Killed by: paired 40-game diff at two doses on identical maps,
37/40 outcomes unchanged, net +1 game; trajectory diff proving the mechanism engages on the
maps where it matters and converts nothing. Re-opening requires a reason the *decision rule*
changed, not a new constant — and there is one already registered (iteration 9's two-sided
rule, which reads chips as well as paint), which is a different rule, not a different dose.

`carol_i6a` stays in the tree as a permanent ablation arm rather than being deleted: it is the
zero-cost way to re-test this if the two-sided rule revives the idea.

## Iteration 7 (2026-09-06) — robustness: the self-cancelling chip reserve

**Area**: robustness (leaves econ after three consecutive tower-mix attempts, one rejected
outright and two near-missed).

**Base**: `src/carol` reverted to the accepted iteration-5 build; iteration 6/6b's
`towerTypeFor` is gone. Compile-checked (COMPILE-OK).

**Change** (runTower, plus instrumentation):
```java
int chips = rc.getChips();
stagnantTurns = (lastChips == chips) ? stagnantTurns + 1 : 0;
lastChips = chips;
int reserve = (stagnantTurns >= STAGNANT_ROUNDS) ? 0 : CHIP_RESERVE;
```
plus `rsv=` and `stag=` in the tower indicator — the gate value itself, which LEARNINGS.md
asked for the *first* time this bug appeared and which was never actually added.

**Run design**: `OPPONENTS="carol_iter5 carol_rush carol_decap"`, 20 maps x both sides = 120
games. `carol_turtle` is retired (unbeaten in 64 games) and its ~40 games are spent on
`carol_decap` instead. **Three maps pinned** — DefaultSmall, DefaultMedium, Fossil, the three
where the frozen treasury was actually measured — with the other 17 drawn fresh at random.
Same justification as MoneyTower in iteration 6: the mechanism gate is unmeasurable if the
sample can miss every map the bug occurs on, and 17/20 stays a fresh draw.

**Pre-registered gate** (restructured by the doctrine-#4 finding above — the h2h cannot carry
this one):
- **PRIMARY (mechanism)**: zero games in which the treasury sits *exactly* unchanged for >=50
  consecutive rounds while towers stand. Baseline: 3 of 40 `carol_rush` games, and
  1,887 / 1,881 / 44 rounds in the three losses.
- **CONFIRMATION**: `carol_rush` >= 37/40, ideally 40/40 (all three of its wins are this bug).
  Stated honestly as corroboration — a 3-game move at n=40 is at the binomial noise floor.
- **REGRESSION (not an accept signal)**: h2h vs `carol_iter5` must not fall below the 45%
  near-miss floor. It is expected to be ~50%: the threat is largely absent from that
  instrument, so a flat result here is the *prediction*, not a rejection.
- **INSTRUMENT**: `carol_decap`'s first measurement. If it lands in 30-90% it becomes the peer
  that regression-tests every future economy change; outside that band is a negative result
  about the instrument and gets logged as one.
- Dose = `STAGNANT_ROUNDS` (5 / 10 / 20), zero arm = the always-armed reserve (iteration 5).

**Pre-checks all done and recorded above**: reachability (43+ consecutive rounds in the
motivating game), trigger frequency (fires 3/3 losses, 0/3 wins, 1/22 h2h replays), generality
(three different maps, two different opponents), history (supersedes nothing — iteration 2's
reserve stays armed whenever income is positive), play-symmetry (inputs are team chips and a
turn counter, neither team-correlated).

### New instrument: `tools/frozen-treasury.py` (iteration 7's mechanism gate, automated)

The iteration-7 gate is "zero games with the treasury exactly unchanged for >=50 consecutive
rounds while towers stand". That has to be measurable by command, not by hand-reading replays,
or it will quietly stop being checked — which is precisely how this bug survived four
iterations after being diagnosed. Infrastructure before strategy (Phase 0.4).

```
tools/frozen-treasury.py --gate 50 <replays...>     # prints per-replay, exits 1 on failure
```

Validated against the known answers before trusting it:

| replays | tool output | expected |
|---|---|---|
| 3 `carol_rush` losses | 1887, 44, 1881 -> **FAIL** | the hand-measured values |
| 3 `carol_rush` wins | 0, 0, 0 -> **PASS** | 0 |

**Two real bugs found while building it**, both of the kind that would have silently reported
"no problem":
1. It first returned **0 for all three known-bad games**. The continuity clustering assumed
   two teams emit tower rows, but `carol_rush` prints `RUSH -> ..` and emits none, so every
   round was discarded as unresolvable.
2. Then it still returned 0, because within *one* team several towers report in the same round
   and their `chips=` readings differ whenever one of them builds mid-round — so the clusterer
   read one team's two towers as two teams. Fixed by grouping on the **BUILD tag** (exact from
   iteration 7 on: carol is tagged, a frozen snapshot is not) and collapsing each
   (team, round) to its minimum.

Worth recording that a gate tool that silently reports success is worse than no tool, and the
only defence is validating it against a case whose answer is already known. Both bugs made it
*pass* the baseline it was written to fail.

**Known limitation until iteration 7's tag is in a replay**: with neither team tagged, both
collapse into one series (the rain h2h reads 246 rather than the 233 measured for a single
team). Directionally fine, exact from the next run onward.

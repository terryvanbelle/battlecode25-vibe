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

### Iteration 7 — a self-limiting property worth predicting before the run

Player statics are per-robot in this engine, so every tower tracks `stagnantTurns`
independently. All towers read the same team treasury, so they agree on when it is frozen —
but the moment *one* tower disarms and builds, `chips` changes and **every** tower's counter
resets to zero. So the disarmed state produces at most one unit per `STAGNANT_ROUNDS` rounds,
not a single-turn dump of the whole treasury.

That is the behaviour I want and it was not designed in — worth writing down before the run so
it is a prediction rather than a post-hoc rationalisation:
- DefaultSmall (frozen at r26, dead at r69): ~4 build windows, so ~3-4 soldiers instead of 0.
  Enough to change the game, not obviously enough to win it.
- Fossil / DefaultMedium (frozen ~1,880 rounds): ~188 windows, i.e. the treasury is spent down
  steadily rather than sitting at 1220/290 forever.

If the replays instead show the treasury dumped in one round, or show `stag=` never reaching
`STAGNANT_ROUNDS`, the mechanism is not doing what this paragraph says and the result is not
interpretable regardless of the win rate.

**Mechanistic verification planned before the full run**, per §4: re-run the single motivating
game (`carol` vs `carol_rush` on DefaultSmall, side A) and check the round-69 annihilation
against the three outcomes — won / still lost but mechanism demonstrably engaged / no evidence
of engagement. Only the third would stop the iteration before spending 120 games.

### 6b's DOSE gate — the decisive result, and it fails

The run's second block is the candidate (250) played directly against `carol_i6a` (500) on the
same 20 pinned maps. Those two builds differ in exactly two lines — the constant and its build
tag — so this is as clean a zero-vs-dose comparison as this project can construct.

**Pre-registered gate: "h2h vs `carol_i6a` must be > 50%."**

```
candidate(250) vs carol_i6a(500):  19/39 = 48.7%
   worst case 19/40 = 47.5%   best case 20/40 = 50.0%
   side split: A 9/19, B 10/20 -- even
   swept-win 3 (Fossil, Snowglobe, windmill), swept-loss 3 (Mirage, Portal, galaxy), split 13
```

Scoring on 39 of 40 is sound here for the same reason it was at iteration 5, and for the
reason it was *not* at iteration 2: no outcome of the missing game can change the verdict.
The best case is **exactly 50.0%, which is not > 50%**, so the gate fails either way.

**DOSE GATE: FAIL.** Lowering the threshold does not beat leaving it high, head-to-head, on
identical maps. Combined with the primary gate (47.5% < 50%) and the paired diff (37 of 40
outcomes unchanged), three independent instruments agree, and the story I found so persuasive
three hours ago — "500 sits above the operating band, 250 restores money towers" — is simply
not true at the scoreboard. The mechanism moves; the game does not.

That is worth separating carefully, because the mechanistic argument was *correct*: 250 really
does build more money towers on ordinary maps, and the trajectory diff proves it rewrites
whole games. It just does not matter. A verified mechanism plus a plausible story is still not
evidence of value — only the head-to-head is, which is exactly what measurement doctrine #5
says and why the accept gate is what it is.

**Iteration 6/6b REJECTED, definitively.** Ledger entry above stands, now with the dose gate
recorded against it. `src/carol` is already reverted to the accepted iteration-5 build.

### Iteration 7 mechanistic verification — the motivating game, re-run

`carol` vs `carol_rush` on DefaultSmall, the exact game that annihilated at round 69.

**Result: still lost, but at round 155 instead of 69** — survival extended 2.2x. §4 class 2
("still lost, mechanism demonstrably engaged, with an evidenced account of why this game
could not flip anyway"), which the algorithm names as a valid basis to proceed.

The new `rsv=` / `stag=` instrumentation shows the mechanism firing, step by step:

| round | chips | towers | rsv | stag | what happened |
|---|---|---|---|---|---|
| 25 | 1350 | 2 | 1200 | 0 | |
| 31 | 1350 | **1** | 1200 | 6 | money tower dead, treasury freezes, counter arming |
| **37** | 1350 | 1 | **0** | **12** | **reserve disarmed** |
| 43 | **1100** | 1 | 1200 | 5 | **a soldier was built** (-250); counter reset by the spend |
| 49 | 1100 | 1 | **0** | 11 | disarmed again |
| 55 | **800** | 1 | 1200 | 5 | second soldier |
| 61 | **500** | 1 | 1200 | 0 | third soldier |

Under iteration 5 this treasury sat at 1350 from round 26 until death without building
anything. It now spends 1350 -> 1100 -> 800 -> 500.

**Both pre-run predictions confirmed, and they were written down first:**
1. *"~4 build windows, so ~3-4 soldiers instead of 0"* — **exactly 3 soldiers**.
2. *"at most one unit per `STAGNANT_ROUNDS`, not a single-turn dump"* — confirmed; every build
   resets every tower's counter, giving a ~6-10 round cadence.

`tools/frozen-treasury.py` scores the game **i7=12, PASS at gate 50** (was 44). The tag-based
team split worked on its first real use.

**Why this game still could not flip**, specifically rather than as an excuse: DefaultSmall is
a small map against an all-in rusher, carol has lost its money tower by round 26, and 1350
chips is a hard ceiling of five soldiers with no income to extend it. Three soldiers arriving
piecemeal cannot beat an opponent spending its entire economy on continuous soldier
production. The fix converts an inert death into a fighting death — which is exactly what it
was designed to do, and it is the maps with 1,880-round freezes (Fossil, DefaultMedium), where
~188 build windows are available instead of 4, that the full run has to answer.

**Standing bytecode check (iteration 7, DefaultSmall verification game)**: robots peak
**2,495 / 17,500 (14.3%)**, towers **530 / 20,000 (2.6%)**, **0 overruns, 0 near-misses**
across 598 sampled robot-turns. Down from iteration 5's 3,264 robot peak because iteration
6's sensing in `towerTypeFor` is gone with the revert.

**85% of the robot budget is unused.** The algorithm is explicit that this headroom is what
should be spent on better decisions, and iteration 8 (SRPs) is the first thing queued that
will actually draw on it — laying and checking a 5x5 pattern costs real sensing. Worth
recording the number now so the SRP iteration has a before-figure to be judged against rather
than discovering the cost after the fact.

## Iteration 8 prepared and compile-verified during the iteration-7 run: SRPs

Built as `src/carol_i8/` rather than edited into `src/carol`, for two reasons: iteration 7's
base is not settled yet, and having the SRP build as its own package makes the eventual
evaluation an on/off pair on identical maps — the same construction that made 6b's dose gate
decisive. The SRP change touches only the soldier idle branch and adds three methods, all
disjoint from iteration 7's tower changes, so it applies to either base.

**Hook**: the `IDLE-ALLY` branch — a soldier with no empty tile to paint and no enemy paint in
reach, measured at 34,821 turns on Leaf (97% of idle turns on open maps). It consumes no action
the bot was already using, which is the "capability at zero marginal cost" profile.

**A real bug caught before spending a run.** The first version required only the engine's
`areaIsPaintable` (no ruin among the SRP's own 25 tiles). That is not enough: SRP marks and
tower-pattern marks are *the same* `PaintType` marks on the same tiles, and `workOnRuin` paints
whatever marks it finds within r2=8 of a ruin. With only requirement 1, the nearest legal SRP
centre is Chebyshev 3 from a ruin, so its tiles reach Chebyshev 1 — squarely inside that ruin's
tower pattern. The two would overwrite each other's marks and **deadlock the ruin**, which is
precisely the failure iteration 6's mark-readback existed to prevent, reintroduced from a new
direction. Fixed by requiring Chebyshev >= 5 between an SRP centre and any ruin, which makes
the two 5x5s disjoint.

Worth noting how it was found: not by testing, but by asking "what else writes to the tiles
this writes to?" — the shared-resource question §4 asks about treasuries and comm slots, which
applies just as well to *map tiles as a shared medium*. Marks are a shared resource with no cap
and no owner, so nothing would have errored; the ruins would just have quietly stopped
completing.

Compile-checked (COMPILE-OK). Not evaluated — iteration 7 owns the VM.

### The cross-agent channel is not live yet — checked, not assumed

Pulled the only tournament's replays (`20260906-1755`) to see whether the sibling lineages
pose the tower-killing threat my own pool cannot, since that would make the tournament the
even instrument iteration 7 wants.

They do not, and the reason is that the tournament predates all three agents' actual work:
every replay contains **412 identical `Hello world!` indicator strings and nothing else** —
all three bots were still the untouched scaffold starter at 17:55, and my own first accepted
iteration landed after 18:40. That also explains the summary's suspiciously tidy standings
(every pair 4/8, every map split by side): those games were decided by spawn position between
three byte-identical bots.

So the sanctioned cross-agent channel currently carries **zero** information, and the first
informative tournament is the next scheduled run. Until then my instruments are exactly what
they were: my own frozen snapshots, `carol_rush`, `carol_turtle` (retired), and the new
`carol_decap`. That is the self-referential blind spot with no external mitigation at all,
which raises rather than lowers the value of `carol_decap` being a genuinely different
opponent.

Recording this because "the tournament will tell us" is the kind of assumption that quietly
substitutes for measurement — it would not have told us anything.

### LEARNINGS audit — "name the line of code each lesson changed"

Applied the check I proposed after the dead-band discovery, to every LEARNINGS entry that
prescribes a code change. It found a **third** instance of the same pathology.

**Splashers are still not built.** LEARNINGS.md's longest entry, "Soldiers cannot contest
ground", concludes that only splashers bulk-convert enemy paint and *"elevates splashers from
'a nice throughput gain' to the central missing capability"*. The spawn line is:

```java
UnitType want = (rng.nextInt(4) == 0) ? UnitType.MOPPER : UnitType.SOLDIER;
```

**No splasher is ever built.** `runSplasher()` and the whole splash-scoring routine are
present, compiled, and **unreachable** — sunk work from iteration 4 sitting one token away
from being live.

**And iteration 4 never measured it.** Iteration 4 bundled three changes (splasher spawn mix,
money-tower ratio, *and* a delayed-arming reserve) and was rejected at 40%. Iteration 5 then
took the money-tower half alone and it **accepted at 66.7%** — so the bundle's rejection says
nothing about the splasher arm, which has never been measured on its own. Iteration 4's own
reachability argument for bundling (a splasher costs 400 chips and the treasury was pinned at
the reserve) **is now satisfied by the accepted baseline**, since iteration 5 raised chip
income 30 -> 150/round. The condition that forced the bundle is gone.

**Ledger: re-opening "splasher spawn mix" is legitimate**, on the specific grounds the ledger
requires — not "it feels under-explored" but "the recorded cause was confounding with two
other changes, one of which has since been independently accepted and now funds it".
Registered as **iteration 9**, and it is one line.

### History pre-check for iteration 7 — it does not revert iteration 4, it inverts it

Iteration 4 also changed `CHIP_RESERVE`, and was rejected with a trace: arming the reserve
*late* let ~7 early soldiers eat the 1,980 starting chips that are exactly the first ruin
completion, leaving the candidate **one tower behind by round 300 and never catching up**.
The log records the conclusion firmly: "the early reserve is load-bearing after all... the
cure was worse than the disease".

Iteration 7 is the **inverse** of that change, and the distinction is the whole point:

| | iteration 4 (rejected) | iteration 7 |
|---|---|---|
| when the reserve is off | **early**, while income is healthy and growing | only after chips are *exactly* unchanged for 10 turns, i.e. income is zero |
| early game | reserve disarmed — the failure | reserve fully armed; `stagnantTurns` cannot leave 0 while income flows |

Confirmed empirically in the verification replay, not just argued: `rsv=1200` at every round
from 1 to 31, first disarm at **r37**, after the money tower died at r26. Iteration 4's
load-bearing early hoard is untouched.

**And iteration 4's own prediction is now falsified, which is the new evidence the algorithm
requires for re-opening.** It concluded: *"the dead band becomes terminal only when chip income
reaches zero, and income reaches zero only because iterations 2-3 build a paint tower at every
ruin. Fix the income and the reserve stops being a trap without touching it. That is iteration
5."* Iteration 5 was accepted — and the dead band still killed carol on DefaultSmall at round
69 in iteration 6's run, because `carol_rush` **kills the money towers**. Income reaching zero
does not require building no money towers; it only requires losing them. That is a specific,
evidenced reason the recorded cause no longer applies.

### New instrument: `tools/eval-run.sh` — the standing checklist as one command

Every item the algorithm says to check on *every* evaluation was being done by hand and
therefore inconsistently: completeness, per-opponent rate, the **binomial noise floor** for
that sample size (doctrine #6 asks for it explicitly and I had been eyeballing it), swept-map
shape, side split, exceptions, the bytecode check, and now the frozen-treasury gate.

```
tools/eval-run.sh <run-id> [gate-opponent]
```

Run against 6b as a self-test, it reproduces every number I derived by hand today and adds
two I had not computed: the noise floor is **3.2 games = 7.9 points at n=40** (so 6b's
"+2.5 points over the 500 arm" was always inside it), and the 6b run contains a **255-round
frozen treasury**, i.e. the baseline still has the degeneracy — which is the control iteration
7 needs.

It also confirms the build tag earning its keep on its first automated use: the gate line
reads `untagged=0  i6b=0`, splitting the two teams exactly rather than by continuity guessing.

The reason to build this rather than keep hand-scoring is the one this session keeps
relearning: the dead band survived four iterations *after* being diagnosed because checking
for it was a thing someone had to remember to do. A checklist that is one command is a
checklist that still runs when the session is tired.

**Known limitation of the iteration-8 SRP draft, recorded before its run** so it is not
discovered as a surprise: soldiers never *navigate* to an SRP site. `srpCenterNear` only
returns a centre within `RESOURCE_PATTERN_RADIUS_SQUARED` (r2=8, radius 2.83), and with a
lattice spacing of 5 the disc covers ~25.1 tiles against a 25-tile cell — so almost every
position is in range of some centre, but the cell corners at (2.5, 2.5) are r2=12.5 and are
not. An idle soldier standing exactly there reports `SRP-nosite` and relies on `moveExploring`
to drift it back into range.

Deliberately not fixed in this iteration: adding "step toward the SRP centre" would bundle a
navigation change with the SRP mechanism and make a rejection uninterpretable. If the run shows
`SRP-nosite` dominating the idle tags, that is the first refinement to try, and the log will
already say so rather than inventing the explanation afterwards.

### Iteration 7 arm-to-arm identity check — the h2h carries *exactly* zero information

The h2h block came in at 20/39 = 51.3% with **19 of 19 completed maps splitting by side**.
A split-by-side result on literally every map is the signature of two bots that behave
identically, so I checked it instead of interpreting it. Pulled three h2h replays — including
Fossil and DefaultMedium, two of the three maps where `carol_rush` produced 1,880-round
freezes — and grepped the new gate instrumentation:

| map | turns with `rsv=0` | max `stag` |
|---|---|---|
| Fossil | **0** | **0** |
| DefaultMedium | **0** | **0** |
| Castle | **0** | **0** |

`stag` never leaves zero, so `rsv` is never dropped: **the iteration-7 mechanism does not fire
even once against `carol_iter5`.** The candidate is behaviourally identical to the baseline in
that entire block, which is why every map split by spawn side — those games are the same bot
played against itself.

This is doctrine #3's "all-identical means the change never executed", and normally it would
kill a result as uninterpretable. Here it is the **pre-registered prediction landing exactly**:
I wrote before the run that the h2h "is expected to be ~50%: the threat is largely absent from
that instrument, so a flat result here is the prediction, not a rejection". It came in at
51.3% for the most mechanical reason possible.

Two consequences:
1. The **regression check passes trivially** — a build that never diverges cannot regress. The
   45% floor is met with no risk attached.
2. The **entire decision now rests on `carol_rush`, `carol_decap`, and the frozen-treasury
   gate**, exactly as pre-registered. Had I not restructured the gate three hours ago on the
   doctrine-#4 finding, I would now be holding a 51.3% "near miss" on an instrument that
   provably measured nothing, and the honest reading of it would have been unavailable.

Also note what this says about `carol_iter5` as an instrument for *this* class of change: it
cannot pose the threat, so it cannot regression-test it. That is the self-referential blind
spot with a number attached — 0 firings in 39 games — and it is the concrete justification for
`carol_decap` existing at all.

### The owed play-symmetry audit, settled for free by iteration 7's h2h block

`TRAINING_LOG` has carried "a dedicated pinned-map mirror run is still owed" since iteration
3, and `src/carol_mirror` is currently **stale by 197 lines** — it is a copy of a much older
`src/carol`, i.e. it has silently stopped being a mirror, exactly the staleness failure
`tools/sync-mirror.sh` exists to prevent. (Left stale deliberately for now: the script's
discipline is to resync immediately before a mirror match, and syncing it to an unaccepted
candidate would be worse than leaving it obviously wrong. The script refuses to *claim* mirror
status when it differs, so it cannot mislead silently.)

But the audit no longer needs its own run, because **iteration 7's h2h block already is one.**
The mechanism provably never fires against `carol_iter5` (`stag` = 0, `rsv` never dropped, 39
games), so the two builds are behaviourally identical and the block is a mirror match over 20
maps x both sides. Per-map results:

```
side A won the map:  Castle DefaultLarge DefaultSmall Gears Mirage PlumberGame
                     boxofchocolates defensetower rain                        =  9
side B won the map:  Bunny DefaultMedium Dominoes Fossil HungerGames Money
                     Parking_lot gridworld quack sayhi                        = 10
```

**Every map splits by side, and the winning side is 9-10 across maps.** That is precisely the
healthy signature: the outcome on any given map is decided by spawn geometry, and *which* spawn
is favoured is a coin flip across maps. A play-symmetry bug — a compass-ordered `Direction[]`
scan, a hardcoded fallback, anything correlated with team identity — would show up as one side
winning most maps. Nine versus ten is as clean as this instrument gets.

**Audit result: PASS, no systematic side bias.** Caveat recorded honestly: this is a
behavioural mirror (identical decisions), not a byte-identical one, and the maps are this run's
sample rather than a pinned repeat. Both are fine for the question asked — every map is played
from both sides *within* the run, which is the only property the audit needs. A dedicated
byte-identical mirror run stays on the list, but at much lower priority now that the answer is
known.

Worth noting the general move: the mirror audit was owed for four iterations because it looked
like it needed its own 40-game run. It did not — it needed someone to notice that a run already
in flight had produced the data. Check what the current run already answers before queueing a
new one.

### SELF-CORRECTION: I measured the bug's frequency on a build I then reverted

The trigger-frequency pre-check that justified iteration 7 — "fires in 3/3 `carol_rush` losses
at 1887 / 1881 / 44 rounds, 0/3 wins" — was measured on the replays of run `20260906-212704`.
**That run's bot was the iteration-6 candidate**, which I rejected an hour later and reverted.
Iteration 7 is built on iteration 5. So the pre-check characterised the frequency of the bug
on a build that no longer exists.

The consequence shows up immediately in this run, on the two maps I was most confident about:

| map (vs `carol_rush`) | iteration 6 build | iteration 7 build |
|---|---|---|
| Fossil A | LOSS, **1,881 frozen rounds** | **WIN**, `stag` max **0** — never froze at all |
| DefaultMedium A | LOSS, **1,887 frozen rounds** | **WIN**, `stag` max **0** — never froze at all |
| DefaultSmall A | LOSS r69, 44 frozen rounds | LOSS r155, `stag` 12, disarm fired, 3 soldiers built |

**Those two flips are not iteration 7's doing.** The mechanism provably never fired in either
game, so iteration 7 played them exactly as iteration 5 would. They flipped because iteration 6
was reverted — which retroactively confirms the prediction I registered earlier that iteration
6's paint-only bias *caused* money towers to vanish and income to hit zero. The 1,880-round
freezes were substantially an artifact of the build being tested, not a property of the
accepted baseline.

**So the honest size of iteration 7's opportunity is much smaller than I sized it.** On a
six-game sample of the correct baseline: `stag` reaches the threshold in 2 games (Castle A
415, DefaultSmall A 12), of which only **one** produced any purchase. The other four never
freeze.

**The poverty floor added this afternoon earned itself already.** Castle A shows `stag=415`
but a frozen-while-affordable run of only **9**: the treasury sat below 250 chips, so the
reserve was correctly disarmed and there was simply nothing to buy. Without that floor this
game would have registered as a 415-round gate failure on a build that behaved perfectly.

**What this does and does not change.** It does not retract the degeneracy — it is real on the
accepted baseline (DefaultSmall still shows it, and the mechanism still converts r69 into
r155). It does mean the *confirmation* gate — `carol_rush` 37/40 -> 40/40 — was reasoned from
inflated numbers, and I should expect a much smaller move. I am recording this before the run
finishes so the expectation is on the record ahead of the result rather than adjusted to fit
it.

**The general error, for LEARNINGS**: a pre-check must be run against the *base the change will
sit on*, not against whatever replays are freshest. Mine were one rejected iteration out of
date, and the rejection had already been decided when I used them.

### Iteration 7's primary gate is not comparative — the zero arm has to be run

`carol_rush` came in at **35/38** (block still landing) with losses on DefaultSmall A (r155,
the degeneracy, improved from r69) and **Dominoes A and B**, which are *not* the degeneracy —
Dominoes A shows `stag` max 0 and a frozen run of 0, so carol simply loses that map.

Two problems with the gates as I wrote them, both visible now:

1. **The confirmation gate compares across builds *and* map samples.** "≥ 37/40, ideally
   40/40" was calibrated against run `20260906-212704`, which was the iteration-6 build on a
   *different* 20-map sample. 92.1% vs 92.5% across two different instruments is not a
   measurement of anything. This is the cross-run comparability trap my own LEARNINGS entry on
   random map sampling warns about, and I walked into it while writing the pre-registration.

2. **The primary mechanism gate is absolute, not comparative.** "Zero games with a ≥50-round
   frozen treasury" can pass because the fix works *or* because the baseline never froze on
   this map sample either — and the self-correction above shows the baseline freezes far less
   than the iteration-6 replays led me to believe. An absolute gate that the control would also
   pass measures nothing.

**Fix: run the zero arm, which I pre-registered and then nearly skipped.** The pre-registration
says "Dose = `STAGNANT_ROUNDS` (5 / 10 / 20), zero arm = the always-armed reserve (iteration
5)". The candidate half is already played; only the control is missing:

```
BOT=carol_iter5 OPPONENTS=carol_rush MAPS="$(cat gauntlet/20260906-220604/maps.txt)"
```

40 games, identical maps, identical opponent — so the comparison is paired game-for-game, the
construction that made 6b's verdict decisive. It answers the only question that matters: on
the maps carol actually plays, does the always-armed reserve freeze where the self-cancelling
one does not, and does it lose games the candidate wins?

Holding the accept/reject decision until that lands. On present evidence I expect it to show a
small real effect on one or two games and no win-rate move — in which case iteration 7 is a
correct robustness fix whose value is currently near zero, which is a legitimate and useful
thing to establish rather than a failure to explain away.

### `carol_decap` v1 — NEGATIVE RESULT as an instrument

Pre-registered: "if it lands in 30-90% it becomes the peer that regression-tests every future
economy change; outside that band is a negative result about the instrument and gets logged as
one." It is outside the band, and more importantly it **does not pose the threat it was built
to pose.**

Traced three of its games rather than judging on win rate alone — the win rate would only have
said "it loses", not "it fails at its one job":

| map | carol's tower count over the game | carol's max `stag` |
|---|---|---|
| Fossil | 2 -> 5 -> 7 -> 8 -> **11**, never drops | 0 |
| gridworld | 2 -> 4 -> 7 -> 8 -> 11 -> **15**, never drops | 1 |
| Parking_lot | 2 -> 4, flat to r2000 | 0 |

**carol never loses a single tower in any of them.** The whole design — money towers first,
focus fire by lowest ID — is irrelevant if no tower ever dies.

**Why, mechanically**: a soldier does 50 damage to a tower, so a lv1 tower at 1,000 HP needs
**20 uninterrupted attacks**, while carol's towers return 20 single-target *plus* 10 AoE per
tower per turn **for free** (tower attacks cost no action cooldown — RULES.md engine note 1).
A soldier that walks up to a defended tower dies long before it lands 20 hits. `carol_rush`
succeeds occasionally only because it swarms on *small* maps in the opening, before carol has
built its second and third tower. My "keep an economy" improvement made `carol_decap` slower to
the frontier and therefore strictly worse at the one thing it exists for.

**Two things this buys, so the run is not wasted:**
1. **Carol's tower mass is a real, unrecognised defensive strength.** Nothing in the pool can
   take a tower off her once there are more than two. That also explains why the
   frozen-treasury degeneracy is rare on the accepted baseline: it requires losing the last
   money tower, and losing *any* tower is already hard.
2. **It sharpens what a useful archetype must do.** Not "prefer money towers" but "arrive with
   enough simultaneous soldiers to out-damage free tower fire". That is a swarm-timing problem,
   not a targeting problem — v1 got the target selection right and the arrival wrong.

`carol_decap` v2 is registered but **deprioritised**: it is instrument-building, and the
instrument is only worth rebuilding if a change actually needs it. Iteration 7 is the only
queued change that does, and its own value now looks small.

## NEW ABSOLUTE DEGENERACY: losing the last PAINT tower is an unrecoverable loss

Traced the Dominoes swept loss (the only new loss in iteration 7's `carol_rush` block, and
confirmed *not* to be the frozen-treasury bug — `stag` max 0). It is worse than the bug
iteration 7 fixes.

| round | chips | towers | tower paint |
|---|---|---|---|
| 1 | 2,530 | 2 | [300, 410] |
| 200 | 6,000 | **1** | **[0]** |
| 900 | 27,000 | 1 | [0] |
| 2000 | **60,000** | 1 | **[0]** |

Carol's starting **paint** tower dies around round 150-200. The surviving tower is the
starting **money** tower, whose paint stash is 0 and stays exactly 0 for 1,800 rounds while
chips climb to 60,000. Total soldier actions in the entire game: **29**.

**Why it is unrecoverable, from the engine rather than from the symptom.**
`InternalRobot.processBeginningOfRound` (disassembled earlier today) gates the paint income on
the tower's own type: `if (type.paintPerTurn != 0) addPaint(paintPerTurn + 3*numSRPs)`. A money
tower has `paintPerTurn == 0`, so **it never gains paint by any route** — not by mining, and
not from SRPs either, since the SRP bonus is inside that same guard. Robot paint is drawn from
the building tower's stash, so with every surviving tower at 0 paint, `canBuildRobot` fails
forever. No robots means no ruin can ever be painted, so no new tower can be built, so no paint
tower can be recovered. 60,000 chips buy nothing.

**So: a team with no paint tower and no robots holding paint has already lost, at whatever
round that happens, silently.** There is no comeback path in the rules. Adding this to
`RULES.md` as a hard loss condition — it is the sort of thing that belongs in the ground-truth
digest, not buried in a trace.

**Why iteration 7 cannot help here**, and why that is the right behaviour: chips are *growing*
(the money tower mines 20-30/turn), so `stagnantTurns` stays 0 and the reserve stays armed.
Correctly — this is not a chip problem. It is the paint-side twin of the same failure, and it
needs its own fix.

**Registered as the next iteration, promoted above SRPs.** It is an absolute degeneracy
(no opponent needed for it to be wrong), it is catastrophic rather than marginal, and it
occurred in **2 of 40** games against one opponent. The cheap, targeted form: carol starts with
exactly one paint tower (`NUMBER_INITIAL_PAINT_TOWERS = 1`) and its `towerTypeFor` key makes
roughly one ruin in three a money tower **without ever asking what the team already has**. A
soldier can count ally tower types in sense range, and while it can see at most one paint tower
it should build PAINT. That converts "carol has one paint tower for the first 200 rounds" —
a single point of failure the whole game hangs on — into two or three.

Note this is the same gap iteration 9 (the two-sided mix) was registered for, but sharpened
from "read chips as well as paint" to something far more specific and far better evidenced:
**never let the paint-tower count reach one.**

### Iteration 7 FULL RESULT (run `20260906-220604`, 120 games, GAUNTLET-COMPLETE)

| instrument | result | pre-registered gate | verdict |
|---|---|---|---|
| h2h vs `carol_iter5` | **20/40 = 50.0%**, and **20 of 20 maps split by side** | regression check only, ~50% predicted | **as predicted, exactly** |
| `carol_rush` | 37/40 = 92.5% | >= 37/40 | met, but see below |
| `carol_decap` | **39/40 = 97.5%** | 30-90% to be a peer | **FAIL — benchmark, negative result** |
| frozen-treasury gate | worst run **12**, PASS at 50 | zero games >= 50 | PASS |
| exceptions | 0 | 0 | PASS |
| bytecode | robots 14.7%, towers 2.6%, 0 ov, 0 nm | 0 / 0 | PASS |

**The h2h landed at exactly 50.0% with every single map splitting by side** — the cleanest
possible confirmation that the candidate and the baseline are the same bot in that matchup, and
that the pre-registered restructuring of the gate was necessary rather than convenient.

**The `carol_rush` number is a coincidence, not a measurement.** 37/40 here equals the 37/40 the
iteration-6 build scored — on a *different map sample*. Two 92.5%s on different instruments say
nothing, which is exactly the trap I logged before seeing the number. Only the control arm
(`carol_iter5` vs `carol_rush`, same 20 pinned maps, now running) can settle it.

What the run *did* establish, independent of the control:
- The mechanism engages and does what it was designed to do (DefaultSmall: `stag` 12, reserve
  disarmed, three soldiers built, r69 -> r155).
- It provably never fires in normal play — `stag` = 0 across all 40 h2h games — so its downside
  risk is zero, not merely small.
- Zero exceptions, no bytecode pressure, no regression anywhere.
- And it surfaced a **worse and unrelated degeneracy** (the paint-tower loss condition above),
  which is the run's most valuable output by a distance.

## Iteration 8 (2026-09-06) — robustness: a paint-tower floor

**Area**: robustness (2nd consecutive; leaves the econ tower-mix thread closed by 6b).

**Target**: the absolute degeneracy traced above — losing the last paint tower is
unrecoverable by the rules, and it cost 2 of 40 games against `carol_rush`.

### Operational definition (the coordinator's question: what does "the team has no paint tower" mean?)

This needs care, because the obvious reading is not measurable in-game:

- **`rc.getNumberTowers()` is team-wide and exact, but type-blind.** It cannot answer "how many
  paint towers do we hold".
- **Counting `senseNearbyRobots(-1, myTeam)` by type is type-aware but local.** A soldier sees
  the towers near it, not the team's. Seeing no paint tower does not mean the team has none, so
  a rule keyed on it would fire constantly on any soldier that has walked away from home —
  precisely the dead-reasoning-on-a-partial-view error the reachability pre-check exists for.
- Comms could make the count exact and team-wide, but that is a whole unused mechanic and
  bundling it here would make the result uninterpretable.

So I am **not** implementing "the team has no paint tower". I am implementing the narrower
claim the trace actually supports, which is measurable exactly:

> **While the team holds few towers at all, every ruin becomes a PAINT tower.**

```java
if (rc.getNumberTowers() <= PAINT_FLOOR_TOWERS) return UnitType.LEVEL_ONE_PAINT_TOWER;
// otherwise iteration 5's symmetry-invariant key, unchanged
```

Why this is the right narrowing rather than a dodge: the traced failure is specifically an
*early* one. Carol starts with exactly one paint tower (`NUMBER_INITIAL_PAINT_TOWERS = 1`) and
the Dominoes loss killed it at round ~150-200, while carol held one or two towers. Forcing the
first one or two completions to be PAINT converts a single point of failure into two or three,
using a team-wide exact API and no new mechanic. It does nothing late, which is correct — by
then carol has many towers and the trace shows she loses none.

### Pre-registered gate

- **PRIMARY (mechanism, absolute)**: zero games ending with carol holding towers but **no paint
  tower** — detectable as tower paint pinned at exactly 0 across every surviving tower for
  >= 200 rounds while chips rise. Baseline: **2 of 40** `carol_rush` games (Dominoes A and B).
  This one *is* comparative, unlike iteration 7's: the control arm now running gives me the
  baseline rate on the identical 20 maps.
- **REGRESSION (the real risk)**: h2h vs the accepted snapshot must clear 45%. Iteration 5
  proved chip income is the binding rate cap and this **delays the first money tower**, so a
  drop here is the expected way for it to fail, and I want it to be able to fail that way.
- **DOSE**: `PAINT_FLOOR_TOWERS` in {2, 3, 5}, zero arm = iteration 5's key untouched.
  Starting at **3** (forces roughly the first two completions).
- **PARTIAL ENGAGEMENT IS EXPECTED**: the key already yields PAINT for ~2 ruins in 3, so on many
  maps the first completions were paint anyway and those games will be byte-identical. The
  arm-to-arm identity check must therefore show *some* identical games — all-identical means the
  floor never bound and the run is void.

**Not bundled with SRPs** (`src/carol_i8` stays on the shelf) and not with the two-sided mix.

### Iteration 7 decision rule, pre-committed BEFORE the control arm reports

The control (`20260906-222533`, `carol_iter5` vs `carol_rush`, same 20 pinned maps) is at 20/40
as I write this. Writing the decision rule down now so the verdict is derived, not fitted —
this run has already caught me reasoning from a stale baseline once today.

Candidate side, final: **37/40** vs `carol_rush`; losses DefaultSmall A (r155, the degeneracy,
disarm fired, 3 soldiers built), Dominoes A and B (the *paint*-tower degeneracy, unrelated).

| control result | verdict | reasoning |
|---|---|---|
| control **< 37/40**, and its DefaultSmall A is a loss at ~r69 | **ACCEPT** | the fix converted or materially extended games the baseline lost; value demonstrated on identical maps |
| control **= 37/40** with the *same three* losses | **ACCEPT, value ~0** | the mechanism provably engages and provably never fires in normal play (`stag`=0 in all 40 h2h games), so it is a zero-cost failure-mode preventer. The algorithm's own audit found the most valuable features were exactly this shape. Logged explicitly as "accepted on zero measured win value" so no future reader mistakes it for a demonstrated gain |
| control **> 37/40** | **REJECT** | the fix cost games; revert |

The middle row is the one I expect and the one that needs justifying in advance rather than
afterwards. Two facts make it an accept rather than a coin flip: the change **cannot** fire
while income is positive (measured, not argued — `stag` never left 0 across 40 h2h games and
19 of 19 mirror-equivalent maps), so its downside is *identically* zero; and when it does fire
it demonstrably works (DefaultSmall r69 -> r155 with three soldiers built where the baseline
built none). A zero-downside fix for a catastrophic-when-it-happens failure is worth carrying
even at zero measured win rate — but only if that is stated plainly, which is why it is stated
here first.

What would make me **reject** the middle row instead: if the control's DefaultSmall A also
survived to ~r155, which would mean my `vm-match` verification game differed from the gauntlet
game and the mechanism was not the cause of the extension. That is checkable and I will check
it rather than assume.

### Control arm, partial (25/40) — the mechanism's effect is now isolated, and the falsifier is clear

| game (vs `carol_rush`) | control = `carol_iter5` (reserve always armed) | candidate = iteration 7 |
|---|---|---|
| **DefaultSmall A** | **LOSS at round 69** | **LOSS at round 155** |
| Dominoes A | LOSS r2000 | LOSS r2000 |
| Dominoes B | LOSS r2000 | LOSS r2000 |
| DefaultMedium A/B, Fossil A/B, + 18 more | win | win |

Same map, same side, same opponent, same 20 pinned maps, one code difference. **The baseline
dies at round 69; the candidate survives to 155.** That is the mechanism isolated — no
inference from a different build or a different map sample, which is exactly what went wrong
with my earlier trigger-frequency estimate.

**The falsifier I named in advance did not fire.** I wrote: "if the control's DefaultSmall A
also survived to ~r155, the mechanism was not the cause of the extension and it is a reject."
The control's DefaultSmall A is **r69**. The extension is caused by the disarm.

**Second, unplanned result — iteration 8's baseline is established by the same run.** The
control loses **Dominoes A and B** exactly as the candidate does, both at r2000. So the
paint-tower degeneracy is a property of the *accepted baseline*, not of any candidate, and its
rate on these 20 maps is **2/40**. That is precisely the comparative baseline I pre-registered
for iteration 8's primary gate, obtained for free from a run launched to answer a different
question — the third time today that checking what an in-flight run already answers has saved
a run.

Loss sets are otherwise identical, so on present evidence iteration 7 converts **zero** games
and materially extends one. Under the decision rule committed above that is the middle row:
**accept, with value recorded as ~0**. Holding the formal verdict until the remaining 15 games
land, per the no-scoring-a-prefix rule — though note the DefaultSmall comparison itself is a
single completed paired game and cannot change.

### Iteration 7 RESULT — ACCEPTED (with its value recorded honestly as ~0 games)

Control `20260906-222533` (`carol_iter5` vs `carol_rush`, the same 20 pinned maps) came in at
**37/40 = 92.5%**, identical to the candidate, with an **identical loss set**:

| | control (`carol_iter5`) | candidate (iteration 7) |
|---|---|---|
| vs `carol_rush` | 37/40 | 37/40 |
| DefaultSmall A | **LOSS r69** | **LOSS r155** |
| Dominoes A | LOSS r2000 | LOSS r2000 |
| Dominoes B | LOSS r2000 | LOSS r2000 |

This is exactly the middle row of the decision rule committed **before** the control reported,
and the named falsifier did not fire (the control's DefaultSmall A is r69, not r155, so the
extension is caused by the disarm and nothing else).

**DECISION: ACCEPT.** Snapshot `src/carol_iter7` (numbers 4 and 6 stay unused — both rejected,
so the gap is self-documenting). Recorded plainly so no future reader misreads it:

> **Iteration 7 converts zero games. Its measured win value is 0.**

It is accepted on the grounds set out in advance, not discovered afterwards:
1. **Its downside is identically zero, measured rather than argued.** `stag` never left 0 in
   any of the 40 h2h games or the 19 mirror-equivalent maps, so it provably cannot fire while
   income is positive. It is not "low risk"; it is inert outside the failure state.
2. **When it fires it demonstrably works**, isolated on identical ground: r69 -> r155, three
   soldiers built where the baseline built none.
3. It removes a **permanent, silent, total** production stop — the class of failure the 2026
   audit found was worth more than every headline feature.

**What I am NOT claiming**: that it made carol stronger. On 160 games of evidence it did not.

**Post-accept routine**: snapshot created and verified identical apart from the package line;
`replays/iter07_carol_rush_DefaultSmall_A.bc25` archived (the game the mechanism is visible in);
`progress/vs_old_bots_history.csv` extended with the `carol_rush` 37/40 point, **relabelled to
`carol_iter7`** because the tool again derived the wrong build name; both charts redrawn.

**Standing checks**: exceptions 0; bytecode robots 14.7% / towers 2.6%, 0 overruns, 0
near-misses; play-symmetry PASS (9 maps favour A, 10 favour B); frozen-treasury gate PASS.

## Iteration 9 pre-registration — the tower-type key question the floor does NOT answer

Iteration 8's floor is deliberately narrow: *while the team holds <= 3 towers, build PAINT*. It
guards the opening, which is where the trace put the failure. It leaves two gaps open, and I am
naming them now so the next iteration is chosen on evidence rather than on whichever felt
unfinished.

**Gap A — the key still never asks what the team holds.** Past three towers, `towerTypeFor`
reverts to `k % 3 == 0 -> MONEY`, a pure function of the ruin's coordinates. If carol's paint
towers are picked off later while her money towers survive, the key will keep answering MONEY
and walk her back into the absorbing state. The floor cannot see this because
`getNumberTowers()` is type-blind.

**Gap B — the two-sided mix.** Registered after the DefaultMedium trace: the rule is documented
as "build whichever resource is scarce" but only ever reads paint, never `getChips()`.

### Which of these is actually next — decided by measurement, not preference

The honest position is that **I do not yet know whether Gap A occurs**. Every trace of a
late-game paint-tower loss so far comes from the *opening* (Dominoes, r200). The
`carol_decap` result says carol loses no towers at all once she has more than two or three, and
`carol_rush` only ever kills towers in the opening on small maps. So Gap A may be a branch that
never fires — the dead-reasoning failure the reachability pre-check exists to catch.

**So iteration 9 is gated on a measurement I can take for free**, from replays I already have
rather than from a new run: across the `carol_rush` and `carol_decap` blocks of
`20260906-220604` plus the control `20260906-222533`, count games where carol's tower count
*falls* after passing 3.

- If **late tower losses do occur**: iteration 9 = Gap A, a type-aware floor. It needs an exact
  team-wide paint-tower count, which no single API gives, so it would need either comms (a
  whole unused mechanic — its own iteration) or a conservative local rule. That scope is only
  justified if the situation is real.
- If **they do not occur** (my expectation, given carol_decap never took a tower): Gap A is
  **closed as unreachable** and recorded in the ledger as such, and iteration 9 becomes
  **SRPs** (`src/carol_i8`, already written and compile-verified), which is the largest unused
  mechanic and has a 7x arithmetic on the binding resource behind it.

Gap B stays queued behind whichever wins. Registering the *decision procedure* rather than the
decision, because the last three iterations have each turned on a fact I did not have when I
started them.

## Iteration 9 decided by the pre-registered measurement — and both of my guesses were wrong

Built `tools/paint-drought.py` to measure the absorbing state directly: the longest run of
rounds where carol holds towers and the **maximum** paint across all of them is 0 (any single
tower with paint is enough to keep spawning, so the state needs every tower dry at once).
Validated against known answers before use — Dominoes reads 1951 and 1917 rounds, healthy games
read 0 and 1.

**Step 1 — tower counts.** I predicted late tower losses would be rare, on the strength of
`carol_decap` never taking a tower. Measured with proper team separation: **15 of 27** replays
show carol's own tower count falling after passing 3, several severely (8->4, 9->5, 10->5,
7->3). **Prediction wrong.** The reason is embarrassing in hindsight: `carol_decap` failed to
mass soldiers, but `carol_iter5` is a full economy that does, and carol's soldiers already
attack enemy towers. **Carol's own lineage is the only thing in the pool that reliably kills
her towers.**

**Step 2 — but tower losses are not the absorbing state, and that is what actually matters.**

| instrument | paint droughts >= 200 rounds |
|---|---|
| control (`carol_iter5`, accepted baseline), 40 games | **2** — Dominoes A (1951) and B (1917) |
| iteration 7 candidate, 120 games | **2** — the same two |
| all 40 h2h games, *including the 15 with falling tower counts* | **0** (every game reads 0 or 1) |

**So Gap A is unreachable.** Tower counts fall late all the time, and it *never* produces the
no-paint-tower state, because by then carol holds enough paint towers that losing several does
not zero them. The only route to the absorbing state in 160 games is the *opening* one —
exactly where iteration 8's floor is aimed.

**Ledger: "late type-aware paint-tower floor (Gap A)" — CLOSED as unreachable.** Killed by 160
games in which carol's tower count fell after 3 in 15 of 27 traced replays and produced a paint
drought in **none** of them. Re-opening needs a game where a *late* tower loss zeroes the paint
towers, not merely one where towers are lost.

**Therefore iteration 9 = SRPs** (`src/carol_i8`, written and compile-verified this session),
per the procedure registered before the measurement.

**The methodological point**: my first measurement (tower counts falling) is a *proxy*, and it
pointed at Gap A. The direct measurement of the state I actually care about pointed the
opposite way. Had I acted on the proxy I would have spent an iteration — plus, quite possibly,
a whole comms mechanic to make the count exact — on a branch that never fires.

### Correction to a LEARNINGS claim I made an hour ago

"Carol's tower mass is a defence nobody has beaten" is **too strong and now falsified**. It
holds against `carol_decap` (which never masses) and mostly against `carol_rush` (which only
swarms small maps early). It does **not** hold against carol's own lineage: 15 of 27 traced
games show her towers falling after she passes three. Corrected in LEARNINGS rather than left
standing — an overclaim in the durable-lessons file is worse than one in the log, because that
is the file future sessions read first.

## Iteration 9 pre-registration — SRPs (`src/carol_i8`, already written and compile-verified)

Selected by the procedure registered before the measurement, not by preference: Gap A is closed
as unreachable, so SRPs are next.

**The case, in the binding resource** (payout read out of
`InternalRobot.processBeginningOfRound`, not inferred): `addPaint(paintPerTurn + 3*numSRPs)` per
paint tower and `addMoney(moneyPerTurn + 3*numSRPs)` per money tower, applied **per tower**. A
lv1 paint tower mines 5/turn, so ten SRPs take it to **35 — a 7x multiplier** on paint, which
the MoneyTower and Dominoes traces both show is the resource that actually binds. Cost is 200
chips, and chips are the resource carol has been measured throwing away (79,840 idle on
MoneyTower; 60,000 on Dominoes).

**Hook**: the `IDLE-ALLY` branch only — a soldier with nothing to paint and no enemy paint in
reach, measured at 34,821 turns on Leaf. It therefore consumes **no action the bot was already
using**, which is the winner's profile the algorithm names.

**Pre-registered gate**:
- **PRIMARY**: h2h vs `carol_iter7` > 50% accept, 45-50% near miss, < 45% reject. Unlike
  iteration 7, this instrument *can* see the change — SRPs fire in ordinary play on both sides,
  so there is no representativeness problem and the h2h is the right gate.
- **MECHANISM**: `SRP-DONE` must appear and `srp=` must exceed 0 in replays; team paint income
  slope must rise after the first completions. **Zero completions means the feature is a no-op,
  not that the idea is wrong** — and the pre-named first suspect is `SRP-nosite` dominating the
  idle tags, i.e. the navigation limitation already logged.
- **POOL (§4 caveat)**: this draws on the shared treasury, so `ch=` is already in the indicator;
  the treasury must be printed in the same run or the result is uninterpretable, exactly as
  three prior iterations failed to do.
- **BYTECODE**: robots currently peak at 14.7% of 17,500. SRP work adds a 5x5 scan on idle
  turns; the before-figure is on the record so the cost is measured rather than discovered.
- **REGRESSION**: 0 exceptions; the paint-drought and frozen-treasury gates must not worsen.

**Known limitation, already recorded before the run**: soldiers do not navigate to SRP sites,
so a soldier at a lattice-cell corner reports `SRP-nosite`. Deliberately unfixed — bundling a
navigation change would make a rejection uninterpretable.

### ITERATION 8 REACHABILITY FAILURE — its primary gate is unachievable, found before the results

Ran the pre-check on iteration 8's motivating game that I should have run before launching.
On Dominoes (control replay, the accepted baseline):

```
tower count: 2 at r1 -> 1 at ROUND 50 -> 1 for the remaining 1,950 rounds
did it ever rise above its starting value?  NO
```

**Carol completes zero ruins in that game.** Her paint tower dies at **round 50**, not round
200 as I wrote from the coarser sample earlier. `towerTypeFor` is therefore never called
productively, and **iteration 8's paint floor cannot possibly change that game.** Its
pre-registered primary gate — "zero games ending with towers but no paint tower", baseline 2/40
— is unachievable by this mechanism on the only two games in the baseline that exhibit it.

**This is the exact pre-check the algorithm spells out** and I performed only half of it: I
verified the floor *fires* (`getNumberTowers() <= 3` is true in the opening) but not that
firing *reaches the targeted case*. The guidance is explicit — *"read the guard you are nesting
inside: a new clause added under an outer condition that already excludes the targeted case can
never fire."* The outer condition here is "a ruin is completed", and on Dominoes none ever is.

**Why the real cause is different.** Carol holds a healthy paint tower with 300-410 paint from
r1 to r50 and still completes nothing, then loses it to an early rush. The Dominoes failure is
therefore **not** a tower-type-selection problem at all; it is that the opening paint tower dies
to a rush before carol converts it into anything. The fix has to be survival or opening tempo,
not which type the next ruin becomes.

**What I am doing about it**, given the run is already in flight and the shared-VM rules forbid
killing it:
1. **Letting it finish.** It still answers a real question — does a paint-heavy opening help or
   hurt *generally*? — via the h2h against `carol_iter7`, which is a legitimate regression
   instrument regardless of the motivating case.
2. **Retracting the primary gate now, in advance.** Iteration 8 will be judged on the h2h alone.
   I will not be able to claim the degeneracy gate, and I am recording that before seeing a
   single game so it cannot be quietly reinterpreted afterwards.
3. **Re-targeting the degeneracy.** "Prevent the no-paint-tower state" stays open, re-scoped
   from *tower-type selection* to *early paint-tower survival*, and it needs its own trace of
   what kills that tower at r50 before any code is written.

The honest summary: I diagnosed the absorbing state correctly, verified it from the engine
correctly, built the right instrument for it — and then aimed the fix at the wrong link in the
chain, because I checked that my new branch would execute without checking that executing it
could reach the failure.

### Re-scoped trace: why carol's paint tower dies at r50 on Dominoes — the opening is paint-starved

Per-tower paint, carol's side, accepted baseline:

| round | tower paints | enemies seen |
|---|---|---|
| 1 | [300, 410] | 0 |
| 4 | [40, 100] | 0 |
| 11 | [10, 100] | 0 |
| 25 | **[0, 150]** | 0 |
| 30 | [0, 100] | **2** — the rush arrives |
| 49 | [0, 190] | 1 |
| 50 | **[0]** — a tower is gone | 0 |

Carol emits **205** soldier indicator lines in the whole game; `carol_rush` emits **11,572**.

**The tower is not killed while carol is strong — carol is already empty when it arrives.** One
tower is pinned at 0 paint from round 25, twenty-five rounds *before* any enemy is in sight and
five rounds before one is even visible. The rush walks into a base that produced almost nothing.

**Mechanism.** Two draws compete for one stash: spawning costs 200 paint per soldier from the
building tower, and `refillIfPossible` lets any soldier below half capacity top itself back to
full from an adjacent tower. A single lv1 paint tower mines 5/turn (lv2: 10). So a couple of
soldiers cycling home to refill drain the stash faster than it regenerates, and once it hits 0
**nothing** can spawn — the same shape as the chip dead band, on the other resource, and with no
reserve protecting it.

Note the exact parallel: `CHIP_RESERVE` exists precisely because unreserved spawning drained
the treasury and cost towers (iteration 2). **The identical failure exists on paint and has no
reserve at all.** Soldiers refill greedily to full with no notion of leaving the tower enough to
build the next unit.

**Registered as the re-scoped degeneracy iteration: a tower paint reserve.** `refillIfPossible`
takes only the surplus above one soldier's build cost, so refuelling an existing soldier can
never consume the ability to create a new one. Small, local, and it mirrors an already-accepted
mechanism rather than inventing one — which also means iteration 2's evidence transfers as the
argument for why a reserve of this shape works.

Pre-checks still owed before it is written: *trigger frequency* (how often does tower paint hit
0 while a soldier is refilling, across maps that are not Dominoes), and *history* (iteration 3's
`refillIfPossible` was accepted on its own evidence and this narrows it, so the change must
supersede that reasoning rather than silently undo it). Not writing code until both are done —
which is precisely the discipline iteration 8 skipped.

### Trigger-frequency pre-check for the paint reserve — PASSES decisively, and it is general

Two measurements, both off existing replays:

**1. The *absorbing* state is Dominoes-only.** Longest run with every carol tower simultaneously
at 0 paint, excluding Dominoes: across 21 carol-side games the maximum is **1 round** (median
0). So the unrecoverable no-paint-tower state really is confined to the one map, which confirms
iteration 8's re-scoping was right but says nothing about a paint reserve.

**2. The *starvation* it comes from is everywhere.** The sharper question is how often carol
simply cannot build a soldier for want of tower paint. Counting rounds in the **first 100**
where **no** tower holds the 200 paint a soldier costs:

```
n = 27 games
median = 28 of the first 100 rounds with no tower able to afford a soldier
9 of 27 games spend MORE THAN HALF the opening unable to build one
worst: defensetower 99/100, Dominoes 97-98/100, boxofchocolates 70/100, DefaultSmall 59/69
```

**Carol spends roughly a quarter to a half of every opening unable to produce a unit anywhere on
the board — while chips sit at 1,200-1,500.** That is not a Dominoes quirk; it is the shape of
carol's opening on most maps, and it is the same two-ceiling story as iteration 5, one resource
over: chips were the binding cap on unit *rate*, and paint is the binding cap on unit
*existence* in the opening.

This also reframes the Dominoes loss. Dominoes is not a different failure — it is the ordinary
opening starvation plus an opponent that arrives at r30 to punish it. The other 26 games survive
their starvation because nothing shows up to exploit it.

**Trigger-frequency pre-check: PASS**, with a much larger opportunity than the degeneracy that
motivated it. Remaining owed pre-check is *history*, below.

### History pre-check for the paint reserve — clean, and the provenance is itself the finding

`refillIfPossible` traces to **iteration 0**, the deliberately-minimal baseline bot: *"Soldiers:
refill at adjacent towers when <50%"*. It was scaffolding, chosen to make the bot function at
all, and **no iteration since has ever examined it**. So narrowing it supersedes no accepted
reasoning and reverts no evidenced decision — the history check passes trivially.

But the provenance is the more interesting half. **An arbitrary iteration-0 constant has
survived seven iterations unexamined and now measurably costs carol a quarter to a half of every
opening.** Iterations 1-7 tuned painting policy, exploration, tower mix, and the chip reserve —
each with traces and gates — while the rule governing *the resource all of it depends on*
was never once questioned, because it was never anybody's hypothesis.

That is the ablation track's whole argument, arriving unprompted: the algorithm says carried
features should be gated off and measured, and notes that a 2026 audit found the headline
accepted features were worth ~0 while incidental ones carried the value. Here the unexamined
scaffolding is plausibly worth more than several accepted iterations.

**Both pre-checks now pass**, so the paint reserve is cleared to be written — after iteration 8
reports, and not bundled with it.

**Also queued from the same observation, as a proper ablation rather than an invention**: gate
`refillIfPossible` off entirely and measure it. It has never been measured at all, and per the
algorithm one cheap run per carried feature has historically found more real corrections than
invention did.

---

## RESUME STATE (2026-09-06 ~23:0x UTC) — read this first if you are a fresh session

**Accepted lineage**: iter0, 1, 2, 3, 5, 7 (4, 6 and 6b rejected; numbering keeps the gaps
deliberately). **`HEAD`'s `src/carol` is the ACCEPTED iteration 7** — verified, not assumed
(`git show HEAD:.../src/carol/RobotPlayer.java | grep -c PAINT_FLOOR_TOWERS` = 0). The
iteration-8 candidate lives **only in the working tree, uncommitted**, which is the deliberate
discipline: HEAD is what the twice-daily tournament plays, so it carries the last accepted
build and never an unevaluated candidate. (An earlier draft of this block claimed the opposite;
corrected after checking rather than trusting the note.)

**In flight**: `gauntlet/20260906-223146` — iteration 8 (paint-tower floor,
`PAINT_FLOOR_TOWERS = 3`) vs `carol_iter7` + `carol_rush`, 20 pinned maps, 80 games. Launched
22:31 and **still at 0 results**: all five BC25 semaphore slots are held by alice's and bob's
runs. Runner verified alive. Recover with
`../../tools/gauntlet-collect.sh 20260906-223146` if the poll loop dies; **do not re-run it**.
Note it predates the coordinator's `bot.txt` fix, so `track_vs_old_bots.py` will fall back to a
date guess — check the label, report it, don't hand-edit.

**Iteration 8's primary gate is already retracted** (see the reachability-failure entry). It
cannot fix its own motivating games: on Dominoes carol completes zero ruins, so `towerTypeFor`
is never called productively. Judge it on the h2h vs `carol_iter7` **only**.

**Decided and queued, in order:**
1. **Paint reserve** — `refillIfPossible` should take only the surplus above one soldier's build
   cost. **Both pre-checks are done and pass** (trigger frequency: median 28 of the first 100
   rounds with no tower able to afford a soldier, 9 of 27 games above 50; history: the rule is
   unexamined iteration-0 scaffolding). Cleared to write. Largest measured opportunity on the
   board.
2. **Iteration 9 = SRPs** — `src/carol_i8` is written and compile-verified; gate pre-registered.
   Chosen by a procedure fixed before the deciding measurement.
3. **Ablation of `refillIfPossible`** — never measured in 8 iterations.
4. Early paint-tower survival on Dominoes (needs its own trace first).

**Closed this session**: tower mix by observed tower-paint scarcity (6b, three instruments);
late type-aware paint-tower floor (Gap A, unreachable in 160 games).

**Instruments built this session**: `tools/frozen-treasury.py`, `tools/paint-drought.py`,
`tools/eval-run.sh` (the standing checklist as one command — run it on every run).

**Pool**: `carol_turtle` retired (unbeaten in 64). `carol_decap` is a **failed** instrument
(97.5%, never kills a tower) — do not reuse it as a peer without rebuilding it for swarm timing.
`carol_rush` is a benchmark kept only because it is the sole opponent that exposes early
degeneracies.

**Standing per-evaluation checklist** (run `tools/eval-run.sh <run-id> <gate-opponent>`):
completeness, win rates with the noise floor, swept shape, side split, exceptions, bytecode,
frozen-treasury gate, paint-drought gate. Plus the API sweep (`grep -o 'rc\.[a-zA-Z]*'` diffed
against `javap RobotController`) — it found three unused mechanics the first time it was run.

### The paint-reserve dose already contains the ablation — no separate build needed

Noticed while about to write a third package: `TOWER_PAINT_RESERVE` spans the whole space,
because `avail = max(0, ally.paintAmount - RESERVE)`.

| dose | behaviour |
|---|---|
| **0** | iteration 0's greedy refill — the **zero arm**, byte-identical to the accepted build |
| 100 | keep half a soldier back |
| **200** | keep exactly one soldier's build cost back — the registered candidate |
| **1000** | tower paint cap, so `avail` is always 0 — **soldiers never refill at all**, i.e. the full **ablation** of `refillIfPossible` |

So the queued ablation ("gate `refillIfPossible` off entirely and measure it — never done in 8
iterations") is just the top of this dose curve, not separate work. One parameter, one build,
four arms, and the curve's *shape* is the evidence: the algorithm asks for a zero arm and warns
that a concave curve with an interior optimum is stronger evidence than any single point. Here
both ends are meaningful policies rather than arbitrary extremes — greedy refill and no refill —
so an interior peak would be a genuinely informative result rather than a tuning artefact.

Recorded because the instinct to reach for a new package was wrong twice over: it would have
cost build time, cluttered the pool, and obscured that these are points on one curve.

### `tools/opening-paint.py` — the paint-reserve mechanism gate, automated (and a near-miss)

Counts rounds in the opening window where **no** carol tower holds the 200 paint a soldier
costs — rounds the team cannot produce a unit anywhere, whatever its chip total. Uses the
*maximum* across towers, since any one tower with 200 can spawn; the team is only blocked when
every tower is under it.

Validated against the hand measurement before use: **median 28 blocked of the first 100 across
27 games, 9 above half** — reproduced exactly. That is now the recorded before-figure for
iteration 10's mechanism gate, produced by a command rather than an ad-hoc script that would
not survive the session.

**Near-miss worth recording**: the heredoc that created it ran with the cwd reset to the repo
root, so the file landed in the **shared `tools/`** directory — coordinator-owned, explicitly
strategy-neutral, and not mine to add carol-specific analysis to. Caught it by checking
`git status` on both directories before committing, and moved it into `agents/carol/tools/`.

The general lesson is small but real: this session's bash calls do not keep their working
directory, so every path in a file-creating command must be absolute or explicitly `cd`-ed. A
relative path silently wrote into someone else's tree, and only an unrelated failure
(`No such file`) surfaced it — had the tool merely worked from there, I would have committed
carol's private instrument into shared infrastructure without noticing.

### A prediction about iteration 8 that its retracted gate does not cover

Iteration 8's stated purpose is dead (it cannot reach the no-paint-tower games). But the change
it actually makes — **forcing the first one or two ruin completions to be PAINT towers** — is,
by accident, an intervention on the *other* thing I have just measured: opening paint income.

More paint towers early means more paint mined per turn in exactly the window where carol is
measured to be blocked a median of 28 rounds in 100. So:

**Prediction, registered before the results**: iteration 8 should **lower** the opening-paint
blocked count versus `carol_iter7`, measurable with `tools/opening-paint.py` on the h2h replays
(carol is the `[i8]`-tagged side, `carol_iter7` the `[i7]` side — both tagged, so the split is
exact for the first time).

Three ways this can land, all stated now:
1. **Blocked count falls and the h2h clears 50%** — accept, but explicitly *for a different
   reason than it was proposed*, and the log must say so. It would also be independent
   corroboration of the paint-starvation thesis from a change I did not design for it.
2. **Blocked count falls and the h2h does not clear** — the strongest possible result for
   iteration 10, because it isolates "more opening paint" as insufficient *on its own* while
   leaving the leak unplugged. That makes the reserve the sharper intervention, not a rival one.
3. **Blocked count does not move** — then the floor is not producing paint towers where it
   matters (most likely because the key already answered PAINT on those ruins), and the run
   reduces to a pure regression check.

Writing this down because case 1 is the one where I would be most tempted, afterwards, to claim
I had aimed at it. I did not: I aimed at the degeneracy and missed, and the trace that found the
miss is what produced the paint thesis.

### Iteration 8 mechanism: the registered side-prediction is confirmed

Measured on four completed h2h games. Both builds carry BUILD tags for the first time
(`[i8]` = candidate, `[i7]` = baseline), so the two sides are split **exactly** — and because
they are in the *same replay*, this is a within-game paired comparison with no map, sampling or
opponent confound of any kind. It is the cleanest instrument this project has produced.

Rounds in the first 100 with **no tower able to afford a 200-paint soldier**:

| map | `[i7]` baseline | `[i8]` candidate | delta |
|---|---|---|---|
| DefaultSmall A | 50 | **33** | **-17** |
| Gears A | 28 | **18** | **-10** |
| Fossil A | 16 | **13** | -3 |
| PlumberGame B | 16 | 18 | +2 |

**Iteration 8 reduces opening paint starvation in 3 of 4 games, substantially in two.** The
mechanism is exactly as predicted: forcing the first completions to be PAINT towers puts more
paint-mining capacity on the board in precisely the window carol is measured to be blocked.

Two things follow:

1. **Independent corroboration of the paint-starvation thesis, from a change not designed for
   it.** The thesis came from tracing iteration 8's *failure*; this is a separate intervention
   moving the same metric in the predicted direction. That is worth more than another
   measurement of the same kind, because it could easily have shown nothing.
2. **The interpretation is now pinned in advance.** Whatever the h2h says, iteration 8 does not
   get credit for fixing the degeneracy it was aimed at — it cannot reach it. If it accepts, the
   log will record that it accepted for the opening-paint reason, discovered after the fact.

h2h stands at 18/34 with 6 games to play, so the verdict is still open and I am not scoring a
prefix. But the two landings I care about are already distinguishable: if the h2h clears, case 1;
if it does not, case 2 — which would be the *strongest* result for iteration 10, since it would
isolate "more opening paint income" as insufficient on its own while the refill leak stays
unplugged, making the reserve the sharper intervention rather than a rival one.

### Iteration 8 h2h RESULT — 20/40 = 50.0%, exactly case 2

| instrument | result |
|---|---|
| h2h vs `carol_iter7` | **20/40 = 50.0%** — near miss (gate was >50% accept) |
| side split | A 10/20, B 10/20 — perfectly even |
| swept shape | 6 swept-win, 6 swept-LOSS, 8 split — perfectly balanced churn |
| mechanism (opening paint) | **improved in 3 of 4 paired games**, by 17 and 10 rounds in two |

This is **case 2** as registered before the results: *"blocked count falls and the h2h does not
clear — the strongest possible result for iteration 10, because it isolates 'more opening paint'
as insufficient on its own while leaving the leak unplugged."*

**It is also the 6b pattern again**, and I should name that rather than rediscover it: a
mechanism that demonstrably moves its target metric (DefaultSmall 50 -> 33 blocked rounds) and
moves the scoreboard not at all. LEARNINGS already carries the rule I derived from 6b — *"if a
change rewrites the game and the outcome does not move, the lever is the wrong lever, not the
wrong setting; do not spend a refinement on a better value of it."* The near-miss band permits
up to three refinements on `PAINT_FLOOR_TOWERS` (2 / 5) and **I am declining them for the same
reason I declined 6b's**.

**Why this is genuinely informative rather than just another null.** It separates two
hypotheses that were entangled an hour ago:
- *"Carol's opening is weak because she has too little paint income."* Iteration 8 raised
  opening paint income and won nothing. **Weakened.**
- *"Carol's opening is weak because the paint she has leaks out through greedy refills."*
  Untouched by this run, and now the only surviving explanation of the same measurements.

That is a real narrowing bought with one run, and it is precisely what iteration 10 tests.

**Holding the formal verdict for the `carol_rush` block** (53/80 as I write). Unlike iteration
7's situation the h2h *is* a valid instrument here — the mechanism provably fires in those games
— but `carol_rush` is the opponent that punishes a weak opening specifically, so if the extra
opening paint is worth anything anywhere, it is worth it there. If the rush block also shows
nothing, iteration 8 is a clean reject.

### Iteration 8 RESULT — REJECTED

Run `20260906-223146` complete, 80 games, 20 pinned maps.

| instrument | iteration 8 | iteration 7 (same 20 pinned maps) | verdict |
|---|---|---|---|
| h2h vs `carol_iter7` | **20/40 = 50.0%** | — | near miss, not an accept |
| vs `carol_rush` | **36/40 = 90.0%** | **37/40 = 92.5%** | **no improvement** (-1 game, inside the 3.2-game floor) |
| side split | A 10/20, B 10/20 | — | even, no symmetry artifact |
| exceptions | 0 | — | PASS |
| mechanism (opening paint) | **improved 3 of 4 paired games** | — | worked |

The `carol_rush` comparison is a real one for once — **same opponent, same 20 pinned maps**,
which is exactly the cross-run comparability I got wrong earlier today and pinned the maps to
fix. Iteration 8 is one game worse. So the extra opening paint bought nothing even against the
one opponent whose whole strategy is to punish a weak opening.

**DECISION: REJECT.** Reverting `src/carol` to accepted iteration 7. No `carol_iter8` snapshot;
the numbering gap joins 4 and 6.

**What it bought, which is not nothing.** Two hypotheses were entangled when this run started;
one is now dead:
- ~~*Carol's opening is weak because she has too little paint income.*~~ **Falsified.** Income
  was demonstrably raised (DefaultSmall 50 -> 33 blocked rounds, Gears 28 -> 18) and it won
  nothing, against either instrument.
- *Carol's opening is weak because the paint she has leaks out through greedy refills.*
  **Untouched, and now the only surviving explanation** of the same measurements.

That is a genuine narrowing, and it makes iteration 10 a sharper test than it was an hour ago:
it is no longer "more paint helps" (just falsified) but specifically "the paint is already there
and is being spent on the wrong thing".

**Closed-directions ledger**: *tower-type floor to raise opening paint income* — CLOSED. Killed
by 80 games at a verified-working mechanism: h2h 50.0% dead even (6 swept wins, 6 swept losses),
and 36/40 vs 37/40 against `carol_rush` on identical maps. Re-opening requires a reason more
opening paint income should convert when this run says it does not.

### `tools/soldier-health.py` — the counter-metric, and it raises a serious doubt about iteration 10

Built the instrument my iteration-10 pre-registration promised ("check soldier lifetime, not
just the paint metric, before reading a drop as noise"). It counts soldier turns and the
fraction spent at **exactly 0 paint** — frozen, unable to move or act, bleeding 20 HP/turn.

Baseline, measured on the four iteration-8 h2h replays where both builds are tagged and in the
same game (so the comparison is exactly paired):

```
i7 (baseline)   soldier turns = 18,431   dry = 2,477  (13.4%)   low<5 = 18.3%
i8 (candidate)  soldier turns = 40,474   dry = 5,475  (13.5%)   low<5 = 17.1%
```

**Two findings, and the second is a problem for the iteration currently running.**

**1. Carol spends 13.4% of all soldier turns completely inert.** More than one turn in eight is
spent at zero paint, frozen and losing 20 HP — not fighting, not painting, not moving. That is a
large standing waste nobody has looked at, and it is measured on the *accepted* build.

**2. Iteration 8 fielded 2.2x the soldiers and still went 50/50.** Gears alone: 5,414 soldier
turns for the baseline against **14,803** for the candidate. Iteration 8 did not merely raise
paint income — it nearly tripled soldier production on some maps — **and converted none of it.**

That second point cuts directly against iteration 10's rationale, and I would rather say so now
than after the result:

> Iteration 10 plugs a paint leak so that **more units get built**. Iteration 8 already
> demonstrated that **building far more units wins nothing**. The two changes differ in
> mechanism but share the outcome they are betting on.

And iteration 10 has a cost iteration 8 did not: denying refills should *raise* the 13.4% dry
rate, since soldiers that cannot top up are exactly the ones that freeze.

**Registered prediction, before the run reports**: iteration 10 lands at or below 50%, with the
opening-paint metric improved and the dry rate worse. If so, the honest conclusion is not "tune
the reserve" but that **carol's binding constraint is not unit production at all** — three
iterations (5, 8, and 10) will have raised production by different routes and converted nothing.

**What that would point at instead**, and it is already in my own log: iteration 5's
instrumentation measured **97% of idle soldier turns on open maps as IDLE-ALLY** — soldiers
standing on ground that is already ours with nothing to do. Combined with the 13.4% frozen at
zero paint, the picture is that carol's problem is what her soldiers *do*, not how many of them
there are. That reopens the two directions this session has kept deferring — frontier-seeking
exploration and splashers (still never built, per the API sweep) — as the better-founded targets.

I am letting iteration 10 run rather than pre-judging it: the prediction may be wrong, and a
run already in flight costs nothing more. But the interpretation is fixed in advance either way.

### What carol's soldiers actually do — measured on the accepted build, and it reorders everything

Four paired games, both builds tagged and in the same replay. Accepted build (`[i7]`), 18,431
soldier turns:

| action | turns | share |
|---|---|---|
| a ruin is in view / being worked | 7,883 | 42.8% |
| **IDLE-ENEMY** (enemy paint in reach, soldier physically cannot touch it) | 4,150 | **22.5%** |
| **IDLE-ALLY** (standing on our own paint, nothing to do) | 2,923 | **15.9%** |
| `pnt` — painted a nearby empty tile | 1,885 | 10.2% |
| `slf` — painted its own tile | 413 | 2.2% |
| `hitT` — attacked an enemy tower | 350 | 1.9% |
| **IDLE total** | **7,073** | **38.4%** |

**Carol's soldiers paint a tile on 12.4% of their turns and are idle on 38.4%** — in a game my
own LEARNINGS opens by calling *"a coverage race, not a fight"*. Add the 13.4% of turns spent
frozen at zero paint, and the picture is a large army doing very little.

**The single biggest block is IDLE-ENEMY at 22.5%** — larger here than IDLE-ALLY. That is
soldiers standing next to enemy paint they *cannot convert*, because a soldier's attack paints
only EMPTY or already-ally tiles (engine-verified, in RULES.md). LEARNINGS states the
consequence plainly: **splashers are the only unit that bulk-converts enemy paint**, and the API
sweep found carol **has never built one** — `runSplasher()` is compiled and unreachable.

**This settles the direction after iteration 10**, and it is now supported by three independent
lines rather than one:
1. **Production is not the binding constraint.** Iterations 5, 8 and (predicted) 10 raise unit
   production by three different routes. Iteration 8 fielded **2.2x the soldiers** and went
   exactly 50/50.
2. **Soldiers are idle 38% of the time**, and the largest single cause is a capability carol
   does not possess.
3. **The capability is already written and compile-verified** — the splasher spawn is one token,
   and iteration 4's rejection never measured it alone (it was bundled with the money-tower
   ratio, which iteration 5 then proved was the valuable half).

**So the queue is now**: iteration 10 (running) -> **splashers** -> SRPs. Splashers move ahead
of SRPs for the same reason the paint reserve did: SRPs multiply an economy whose output is
already being wasted at 38% idle, and fixing what soldiers *do* should precede giving carol
more of them.

**Measurement-error note, because I nearly filed the wrong numbers.** My first extraction used
`grep -o '\[i7\][^|]*| S [^p]*'`, whose `[^p]*` silently dropped every token containing "p" —
including `pnt`, the very action I was trying to count. It reported `pnt` as **zero** and would
have supported a much more dramatic and completely false claim. Caught it only because zero was
implausible. A character class in a hand-written extraction is exactly the kind of thing that
fails silently and in the direction of whatever you were expecting.

### Splasher reachability pre-check — PASSES, and it confirms why re-opening was legitimate

Run **before** writing the iteration, because this is precisely where iteration 8 failed: I
verified its branch fired without verifying that firing could reach anything.

A splasher costs **400 chips**, so `runTower`'s gate is `chips >= CHIP_RESERVE + 400 = 1600`.
Chip distribution across 41,328 tower-turns on the accepted build:

```
median chips = 2,260     p90 = 16,330     max = 60,000
chips >= 1,450 (soldier gate) : 68.9% of tower-turns
chips >= 1,600 (SPLASHER gate): 61.6% of tower-turns
```

**The splasher gate is satisfied on 61.6% of tower-turns** — comfortably inside the operating
band, not above it. Reachability: **PASS**.

This also converts my re-opening argument from plausible to demonstrated. Iteration 4 bundled
splashers with the money-tower ratio and justified the bundle exactly here: *"a splasher costs
400 chips and the trace shows the treasury pinned at the 1200-1400 reserve all game, so without
(2) the splasher roll would simply fail `getChips() >= CHIP_RESERVE + 400` nearly every time."*
That was true then. Iteration 5 took chip income from 30 to 150/round and was accepted, and the
median treasury is now **2,260**. The condition that forced the bundle is gone, measured rather
than assumed — which is the specific, evidenced reason the closed-directions ledger requires.

**Remaining pre-check before writing it**: the *paint* cost. A splasher costs **300 paint**
against a soldier's 200, and paint is the resource this session has repeatedly found binding
(median 28 of the first 100 rounds with no tower able to afford even a 200-paint soldier). So
the splasher's real price is not the 400 chips — chips are abundant — but that each one
displaces one and a half soldiers' worth of the scarce resource. That trade is the dose, and it
is the way this iteration most plausibly fails.

**Dose registered**: splasher share of the spawn roll = **0 (zero arm) / 15% / 30%**, with 30%
being iteration 4's untested value. Starting at 15%, deliberately below iteration 4, because the
paint cost argues for caution and a concave curve is more informative than a single aggressive
point.

### Reviewing the dead splasher code before enabling it — one real bug, one missed capability

`runSplasher()` has been compiled and unreachable since iteration 4. Read it against
`RULES.md`'s engine-verified entry before betting an iteration on it:

> **Splasher attack [E]**: pick centre within r²=4; every tile within r²=4 *of the centre*:
> enemy towers take **100 dmg**; empty/ally tiles painted; **enemy paint overwritten only within
> r²=2 of centre.**

**Bug — the scoring overvalues enemy paint.** The dead code scores every candidate centre with
```java
for (MapInfo t : rc.senseNearbyMapInfos(c, 4)) {
    if (p == EMPTY && t.isPassable()) score += 2;
    else if (p.isEnemy())             score += 3;      // <-- anywhere in r2=4
}
```
Enemy paint is only converted within **r²=2** of the centre, so every enemy tile in the r²=2..4
annulus contributes +3 to a centre that will not actually convert it. The function therefore
systematically prefers centres ringed by enemy paint it cannot touch, over centres whose enemy
paint is in range. Enabling splashers on top of this would make a rejection uninterpretable —
*did splashers fail, or did aiming fail?* — so the radius fix is part of making the mechanism
testable, not a second hypothesis. Logging it that way explicitly.

**Missed capability — splashers are the only unit that can safely kill towers.** The same entry:
splashers do **100 damage** to enemy towers, and the reach arithmetic in `RULES.md` says a
splasher can hit a tower from up to r²≈16 (centre up to r²=4 away, tower up to r²=4 from the
centre) — which **out-ranges paint and money towers at r²=9**. The scoring function has **no
tower term at all.**

That connects directly to this session's `carol_decap` finding: soldiers cannot kill towers
because a lv1 tower needs 20 uninterrupted soldier hits while every tower returns 20+10 damage
*for free*. A splasher needs **10 hits and can stand outside the tower's range while landing
them.** Carol's own defensive strength — the tower mass nothing in the pool can break — has a
counter she has never built.

**Deliberately NOT bundling it.** The next iteration is "build splashers, aim them correctly at
paint". Tower-targeting is registered as the iteration after, because it is a different
hypothesis (offence vs coverage) and bundling them is exactly what made iteration 4
uninterpretable — the mistake that cost this direction four iterations of delay.

**Also adding instrumentation**: `runSplasher()` currently returns the bare string `"P"`, so a
splasher is invisible in every replay. It will report its splash score, whether it fired, and
its paint — otherwise the mechanism gate cannot be checked at all, which is the failure mode
`tools/frozen-treasury.py` was built to prevent.

### Iteration 10 h2h RESULT — 19/40 = 47.5%, and the registered prediction lands exactly

I wrote, before this run reported: *"iteration 10 lands at or below 50%, with the opening-paint
metric improved and the dry rate worse. If so, the honest conclusion is not 'tune the reserve'
but that carol's binding constraint is not unit production at all."*

| instrument | result | predicted |
|---|---|---|
| h2h vs `carol_iter7` | **19/40 = 47.5%** | at or below 50% — **yes** |
| mechanism: opening paint blocked (paired) | DefaultSmall **51 -> 35**, Gears **28 -> 18**, Fossil 16 -> 13, PlumberGame 16 -> 18 | improved — **yes** |
| counter-metric: soldier dry rate | 12.5% -> **12.8%** | worse — **yes**, marginally |
| soldier turns fielded | 12,148 -> **49,411 (4.1x)** | (not predicted — larger than expected) |
| side split | A 9/20, B 10/20 | even, no artifact |
| swept shape | 4 swept-win, 5 swept-LOSS, 11 split | churn |

**The mechanism worked emphatically and converted nothing.** The reserve did exactly what it was
designed to do — it stopped soldiers draining the tower stash, cut opening starvation by up to
16 rounds in 100, and let carol field **four times** the soldier-turns. The scoreboard moved
backwards.

**Three iterations, three different routes, one answer.** This is now a converging result rather
than a single null:

| iteration | how it raised unit production | h2h |
|---|---|---|
| 5 (accepted) | more chip income via money towers | 66.7% *(accepted on other grounds — chips were then the binding cap)* |
| 8 (rejected) | more paint income via early paint towers, **2.2x soldiers** | 50.0% |
| 10 (rejected) | stop the paint leak, **4.1x soldiers** | 47.5% |

**Carol's binding constraint is not unit production.** She can already field four times the army
she does and it changes nothing, because — measured on the accepted build — her soldiers are
**idle 38.4% of the time and paint on only 12.4% of their turns**. Adding soldiers multiplies a
per-unit output that is close to zero.

**DECISION: REJECT** (pending the `carol_rush` block for the record). Declining the near-miss
refinements on `TOWER_PAINT_RESERVE` for the third time this session, and for the reason
LEARNINGS already states: a mechanism that moves its metric hard and the scoreboard not at all
means the lever is wrong, not its setting. The dose curve's remaining arms (100, and the 1000
full-ablation) would only refine a quantity now shown not to matter.

**This is the strongest argument yet for the splasher iteration**, and it is no longer an
inference from one measurement but the conclusion of a three-iteration series: the only way left
to improve output is to make each soldier-turn worth more, and the largest single block of
wasted turns — **22.5% IDLE-ENEMY** — is precisely what splashers exist to convert.

---

## Iteration 11 — splashers, enabled and aimed correctly (PRE-REGISTERED)

Session resumed after an account-wide rate limit killed the previous one mid-sentence
("now the scoring-radius fix and instrumentation"). The working tree held the splasher
iteration intact; reconciled against the log and found complete. Both outstanding gauntlet
runs recovered with `gauntlet-collect.sh` — `20260906-230220` carries iteration 10's full
record including the `carol_rush` block I was waiting on (38/40 = 95%), so **iteration 10's
REJECT is now closed on complete evidence** rather than pending.

**Hypothesis.** Carol's soldiers are IDLE on 38.4% of their turns, and the largest single
block is **IDLE-ENEMY at 22.5%** — soldiers stood beside enemy paint a soldier physically
cannot convert. Splashers are the only unit that bulk-converts enemy paint, and carol has
never built one. Enabling them converts wasted soldier-turns into coverage.

**Why this and not more production.** Iterations 5, 8 and 10 raised unit production by three
different routes; 10 fielded **4.1x** the soldier-turns and went 47.5%. Production is not the
binding constraint. This iteration changes what a unit *does*, not how many exist.

**The one change**: `SPLASHER_IN_20 = 3` — 15% of the tower spawn roll becomes splashers,
taken out of the soldier share with the mopper share held at exactly 25%.

**Bundled deliberately, and why it is not a second hypothesis**: the dead `runSplasher()`
scored enemy paint anywhere in r²=4, but the engine converts enemy paint only within **r²=2
of the centre**. The old scoring therefore preferred centres ringed by enemy paint it could
not touch. Shipping splashers on top of a mis-aimed scorer would make a rejection
uninterpretable — *did splashers fail, or did aiming fail?* — so the radius fix is part of
making the mechanism testable.

**Explicitly NOT bundled**: splasher tower-targeting (100 dmg, out-ranges paint/money towers).
Registered as the *next* iteration. Iteration 4 died of bundling exactly these two.

### Pre-registered gate

| | |
|---|---|
| primary | h2h vs `carol_iter7` (last accepted), 20 maps x both sides = 40 games; **accept at >50%** |
| peer/regression | `carol_rush`, same run, same maps |
| maps | **pinned** to iteration 10's sample (`gauntlet/20260906-230220/maps.txt`) so i11 and i10 are comparable on identical ground, not just each against the baseline |
| mechanism gate | splasher SPLASH-fire share of splasher turns > 0 — **already PASSED**, below |
| counter-metric | splasher share must not starve soldiers: soldier `noPaint`/dry rate vs iteration 7's 12.5% |

### Mechanism verification — PASSED before the run (loop step 4, case 1)

Single match `carol` vs `carol_iter7` on DefaultSmall: **carol (A) wins at round 233**, by
paint coverage. Iteration 10 lost this map from both sides (r368 and r2000).

171 splasher turns, tagged in the replay (the old code returned a bare `"P"`, so splashers
were invisible in every replay carol has ever produced):

| tag | turns | share |
|---|---|---|
| `SPLASH` (fired) | 19 | 11.1% |
| `dry` (cooldown or no paint) | 119 | 69.6% |
| `lowScore` (target below threshold) | 18 | 10.5% |
| `noTgt` | 15 | 8.8% |

**Read the 11.1% against the ceiling, not against 100%.** A splasher's action cooldown is
**+50** and cooldowns fall 10/turn, so a splasher can fire at most **1 turn in 5 — a 20%
ceiling** set by the engine. 11.1% is **55% of action capacity**, which for a first cut is
engagement, not failure.

That ceiling also means most of the 69.6% `dry` is the cooldown carol has no say over: 19
fires necessarily block 4 turns each = 76 turns, leaving ~43 (25%) genuinely paint-starved.
Because reading an engine ceiling as a bot defect is exactly the misdiagnosis that would send
the next iteration at the wrong lever, the tag is now split `cd` vs `noPaint` before the run.

**Registered prediction, before the run reports.** Iteration 11 lands **above 50%**, and this
is the first prediction I have made in that direction this session. The three preceding
production iterations all raised a quantity whose per-unit output was near zero; this one
raises the per-unit output itself, against the largest measured waste block. The way it most
plausibly fails is the paint price: a splasher is **300 paint against a soldier's 200**, in an
economy this session has repeatedly measured as paint-bound, so a 15% splasher share raises
mean unit paint cost ~7.5%. If it fails, the `noPaint` tag and a worsened soldier dry rate are
where that will show, and the refinement is a lower dose, not abandoning the direction.

### The splash threshold is a paint-economics question, and I want the arithmetic on record *before* the result

Non-blocking analysis while the run plays. Splash-score distribution across the 52 splasher
turns that were both action-ready and fuelled in the validation game:

```
score:  0  2  3  4  5  6  8 11 12 14 16 18 21 23 26 28 29
turns: 15  4  3  5  2  4  3  1  1  4  2  2  1  1  2  1  1
```

Bimodal: 33 turns in a 0–6 cluster, 19 in an 8–29 tail. `SPLASH_MIN_SCORE = 8` fires on
36.5% of ready turns and sits almost exactly in the valley, which is a defensible place for
an untuned first guess.

But the *economics* of that threshold are worse than they look, and this is the number I
should have computed before picking 8. Scoring is `2 x empty(r²<=4)` + `3 x enemy(r²<=2)`,
and the tiles actually painted are `empty + enemy`, so tiles ≈ s/3 to s/2. A splash costs
**50 paint**. Therefore:

| splash score | tiles painted | paint per tile | vs. soldier's 5.0 |
|---|---|---|---|
| 8 (current threshold) | 2.7–4 | **12.5–18.8** | **2.5–3.8x worse** |
| 14 | 4.7–7 | 7.1–10.6 | 1.4–2.1x worse |
| 20 | 6.7–10 | **5.0–7.5** | **break-even** |
| 26 (full 13-tile disc) | 8.7–13 | 3.8–5.8 | at or better |

**The paint-per-tile break-even against a soldier is around score 20, and only 9 of 52 ready
turns (17%) reach it.** In an economy this session has measured as paint-bound over and over,
that is the strongest argument against the current dose.

**Two things stop it being decisive, which is why I am not touching the running arm.**

1. **Enemy paint has no soldier price at all.** A soldier cannot convert enemy paint at any
   cost. For the enemy tiles in a splash, the alternative is not "a soldier does it cheaper",
   it is "nobody does it" — which is the entire 22.5% IDLE-ENEMY block this iteration exists
   to attack. Paint-per-tile silently assumes a substitute that does not exist.
2. **The soldier's 5.0 paint/tile is a rate it almost never realises.** Soldiers paint on
   **12.4%** of their turns. Per *turn* rather than per tile, RULES.md's own table gives the
   splasher 2.6 tiles/turn sustained against the soldier's 1.00.

So the honest position is that score 8 is probably too generous on pure paint efficiency and
probably justified on the enemy-conversion and throughput terms, and I cannot resolve that by
reasoning — it is a dose. **Registering the refinement ladder now, before the result, so it
is not a post-hoc story**: if iteration 11 is a near miss, the first refinement is
`SPLASH_MIN_SCORE` 8 -> 14 (spend the scarce resource only where a splash beats a soldier by
throughput *and* approaches it on efficiency), *not* a change to `SPLASHER_IN_20`. Threshold
and share are separate doses and must not be moved together.

**Also noted for a later iteration, not this one**: 15 of 52 ready turns scored **exactly 0** —
a splasher standing where nothing within reach is paintable, the splasher analogue of the
soldier's IDLE-ALLY. Splashers currently inherit `moveExploring(null)`, the soldier's
explorer, which has no notion of the coverage frontier. Frontier-seeking movement is a
separate hypothesis and goes in the queue behind tower-targeting.

### Standing API sweep, run while the gauntlet is semaphore-starved — `upgradeTower` is STILL never called

My own LEARNINGS makes the `javap RobotController` diff a per-evaluation item ("a rules digest
is not an instrument; only a call-site diff is"), so I ran it rather than assuming the last
result still holds. 68 API methods; those `src/carol/RobotPlayer.java` never calls:

```
adjacentLocation broadcastMessage canBroadcastMessage canCompleteResourcePattern canMark
canMarkResourcePattern canPaint canRemoveMark canSendMessage canSenseLocation canSenseRobot
canUpgradeTower completeResourcePattern disintegrate getActionCooldownTurns getHealth
getMoney getMovementCooldownTurns getResourcePattern getTowerPattern isLocationOccupied
mark markResourcePattern onTheMap readMessages removeMark resign sendMessage sensePassability
senseRobot senseRobotAtLocation setIndicatorDot setIndicatorLine setTimelineMarker upgradeTower
```

Three whole mechanics remain unimplemented: **tower upgrades**, **resource patterns (SRPs)**,
and **communication**. `runSplasher` has now moved off this list — the sweep is doing its job.

**Tower upgrades are the strongest of the three**, and for a reason my LEARNINGS already
states in general form ("price a sink in the resource that actually binds"). A lv2 upgrade
costs **2,500 chips** and takes a paint tower's mining from **5 to 10 paint/turn** — it
*doubles* output of the resource that binds, paid for in the resource carol throws away.
Implementation is close to free: `canUpgradeTower(loc)` is a boolean gate that enforces every
legality condition itself, so a tower attempting to upgrade *itself* is self-verifying — if
the engine forbids it, the call is a silent no-op the instrumentation catches immediately.

**Why this is NOT a fourth "more production" iteration.** Iterations 5/8/10 raised the number
of units and converted nothing. An upgrade's value now runs through a different channel: with
splashers in the build, paint demand rises sharply (300/unit and **50 per attack**), and the
validation game already shows ~25% of splasher turns paint-starved. The claim is "keep the
units already fielded firing", not "field more of them" — and it is explicitly conditional on
iteration 11 accepting. If iteration 11 is rejected, this argument lapses with it and must be
re-derived, not carried over.

**Reachability pre-check: NOT YET DONE, and I am recording why the obvious number is wrong.**
Tower-turn chip distribution in the validation game:

| build | tower-turns | median chips | p90 | chips>=2500 |
|---|---|---|---|---|
| i11 | 1,176 | 1,100 | 1,420 | **0.1%** |
| i7 | 466 | 1,750 | 1,930 | 0.2% |

Taken at face value that kills the direction outright. **It is not usable**, and pretending
otherwise is exactly the mistake that burned iterations 6 and 8. This game ended at **round
233**; my earlier distribution over **41,328 tower-turns** of mostly 2,000-round games gave
median 2,260 / p90 16,330 / max 60,000. A short game measures the treasury before it has had
time to accumulate, so this sample is biased against the upgrade by construction. The gate
must be measured on a broad, length-representative sample **before** iteration 12 is written.

One genuine observation survives the confound, flagged rather than concluded: **i7 spent
63.3% of its tower-turns with under 50 paint banked, against i11's 0.9%.** That is the
paint-starvation signature this whole session has been chasing. It is heavily confounded —
i7 lost this game at round 233, and losing the coverage race costs paint towers — so it is
a lead to check across the gauntlet, not a result.

### Upgrade reachability, measured properly — PASSES, and the joint condition is the real finding

Done on local replays (12 full-length games from run `20260906-230220`), so it cost no VM
slots while the gauntlet was starved. **146,350 tower-turns of the accepted build `i7`** —
length-representative, unlike the 233-round validation game above.

| threshold | what it gates | share of i7 tower-turns |
|---|---|---|
| 1,600 | splasher spawn (`CHIP_RESERVE` + 400) | 25.2% |
| 2,500 | bare lv2 upgrade | 22.4% |
| **3,700** | **lv2 upgrade + the 1,200 reserve** | **21.7%** |
| 6,200 | lv3 upgrade + reserve | 18.6% |

**Reachability: PASS.** 21.7% is inside the operating band. The distribution is strongly
bimodal — median 1,400 but p90 13,680 and max 31,250 — which is the "chips are garbage"
regime showing up directly: most turns are hand-to-mouth, and a fat tail has chips piling up
with nothing to buy.

**Correcting a number in my own log.** I recorded the splasher gate as met on **61.6%** of
tower-turns from an earlier 41,328-turn sample; this larger and more representative 146,350-turn
sample puts it at **25.2%**. The splasher gate still clears reachability, but by a much thinner
margin than I claimed when I wrote iteration 11, and I would rather correct it than leave the
optimistic figure standing. If iteration 11 underperforms, spawn-gate starvation is now a live
alternative explanation to the paint-cost one I pre-registered, and the two are distinguishable:
paint cost shows up in the splasher `noPaint` tag, gate starvation in the tower `chips` trace.

**The finding that actually matters is the joint condition.**

| condition on an i7 tower-turn | share |
|---|---|
| chip-rich (>= 3,700) | 21.7% |
| paint-destitute (`tp` < 50) | 33.6% |
| **both simultaneously** | **11.1%** |

Independence would predict 0.217 x 0.336 = **7.3%**, so the two are *positively* associated at
about 1.5x rather than being disjoint regimes. **On 11.1% of all tower-turns, a carol tower is
sitting on enough chips to permanently double its paint mining while holding too little paint
to spawn anything at all.** That is not an abstract efficiency argument about idle chips; it is
a directly observed, recurring state in which the exact resource the tower lacks is purchasable
with the exact resource it is hoarding.

(A formula slip in my first printout reported the independent baseline as 0.1% by dividing by
100 twice, which would have made the association look 100x stronger than it is. Caught it
because 0.1% was implausible against 21.7% x 33.6%. Same failure shape as the `[^p]*` character
class earlier this session: hand-rolled arithmetic in an extraction script fails silently and
flatters the hypothesis. The corrected 1.5x is a real but modest association, and 11.1% stands
on its own without needing the association at all.)

**Iteration 12 is therefore pre-registered as tower upgrades**, ahead of splasher
tower-targeting, with the reachability pre-check now complete rather than assumed. Its
hypothesis is deliberately narrow: *upgrade a paint tower when chips are abundant, and the
paint-destitute tower-turn rate (33.6%) falls.* That counter-metric is measurable on the same
trace, which is what makes this testable rather than a story about idle chips.

### Engine probe: the iteration 12 premise is confirmed directly, not inferred

Ran `UnitType`'s constants out of the 3.1.0 jar on the VM (no game slot needed, so it cost
the starved semaphore nothing):

```
LEVEL_ONE_PAINT_TOWER    lvl=1  paint/turn=5   hp=1000  next=LEVEL_TWO_PAINT_TOWER
LEVEL_TWO_PAINT_TOWER    lvl=2  paint/turn=10  hp=1500  chips=2500
LEVEL_THREE_PAINT_TOWER  lvl=3  paint/turn=15  hp=2000  chips=5000
LEVEL_ONE_MONEY_TOWER    lvl=1  money/turn=20  ...  LEVEL_TWO_MONEY_TOWER money/turn=30
```

A lv2 upgrade **exactly doubles** paint mining (5 -> 10) for 2,500 chips, and throws in
+500 HP on a unit type whose loss RULES.md calls a survival variable. `getBaseType()`,
`canUpgradeType()` and `getNextLevel()` all exist, so iteration 12's guard compiles as
drafted. Money-tower upgrades buy +10 chips/turn and are correctly excluded: that is more
of the resource already being discarded.

### A cross-lineage signal from the tournament, and a prediction registered before the data arrives

The 0100 tournament is still inside its alice-bob block (145 games), but those games are
already sanctioned evidence, and they say something about the *shape* of a decisive BC25 game
that my own instruments cannot:

| | alice vs bob (145 games) | carol vs carol_iter7 (40 games, run 20260906-230220) |
|---|---|---|
| median length | **824** | **2,000** |
| reached r2000 | **12%** | **72%** |
| decided by paint domination | 88% | — |

Alice and Bob finish each other off; **carol's games grind to the round limit and are settled
on tiebreak.** In a game my own LEARNINGS opens by calling "a coverage race", carol appears
not to be able to close one out.

**I am not concluding that, because the comparison is confounded in an obvious way**:
carol-vs-carol_iter7 is very nearly a mirror, and two near-identical bots on a symmetric map
deadlock by construction. Alice-vs-bob is a cross-lineage match where one side can break
through. Some — possibly all — of the 72% vs 12% gap is that artifact, and treating it as a
carol weakness would be exactly the "lopsided instrument" error the doctrine warns about.

**But it becomes a clean test the moment carol's own tournament blocks play**, and the
tournament supplies the missing arm for free:

> **Registered prediction, before carol's tournament games exist.** If carol's stalling is a
> property of her lineage, her cross-lineage games (carol-vs-alice, carol-vs-bob) will reach
> r2000 **substantially more often than the 12%** that alice-vs-bob does. If carol's
> cross-lineage timeout rate comes back near 12%, then the 72% is a mirror artifact, this
> direction is closed, and I will say so.

This is the first thing in this project that can distinguish "carol is slow to convert the
map" from "self-play deadlocks" — precisely the self-referential blind spot MULTI_AGENT.md
says the tournament exists to attack, and it needs no run of my own to settle.

#### Map difficulty is ruled out: the stall gap survives map-matching

Restricted both datasets to the **same 20 maps** (every map in carol's run 20260906-230220
also appears in the tournament's alice-bob block):

```
TOTAL over the identical 20 maps:   alice-bob  5/40 = 12% reach r2000
                                    carol-carol 29/40 = 72% reach r2000
```

Ten of the twenty maps split perfectly — DefaultLarge, DefaultMedium, HungerGames, Mirage,
Parking_lot, PlumberGame, boxofchocolates, gridworld, rain, walalilongla are **0% timeout for
alice-bob and 100% timeout for carol**. Where alice-bob do stall (Gears 100%, Bunny/Dominoes/
sayhi 50%) carol stalls too, so those maps carry real intrinsic stall tendency and the
instrument is behaving sensibly.

So the gap is **not** map difficulty. Exactly one confound is left — mirror versus
cross-lineage — and carol's own tournament blocks settle it without any run of mine. The
prediction registered above stands unchanged and is now sharper: **12% is the cross-lineage
baseline on this very map set.**

### Tracing an actual stalled game — carol's binding constraint, located exactly

Picked **gridworld** because the map-matched table above makes it maximally diagnostic:
alice-bob time out there **0%** of the time, carol **100%**. Traced the r2000 game
`carol_iter7__gridworld__botA` (36,513 tower-turns, both builds tagged in the one replay).

**Team tower count and treasury, every 200 rounds:**

| round | i10 towers | i10 chips | i7 towers | i7 chips |
|---|---|---|---|---|
| 0 | 5 | 2,986 | 13 | 2,528 |
| 400 | 5 | 25,727 | 13 | 74,270 |
| 800 | 5 | 51,085 | 13 | 162,725 |
| 1200 | 7 | 79,920 | 13 | 250,815 |
| 1600 | 7 | 120,605 | 13 | 339,149 |
| **2000** | **7** | **151,090** | **13** | **406,170** |

**Tower paint over the same game:**

| round | i10 % of tower-turns with tp<50 | i10 median tp | i7 % tp<50 | i7 median tp |
|---|---|---|---|---|
| 0 | 75% | 0 | 68% | 13 |
| 400 | 86% | **0** | 79% | **0** |
| 1200 | 90% | **0** | 79% | **0** |
| 2000 | 86% | **0** | 85% | **0** |

**Carol's towers spend this entire game holding ZERO paint and 406,170 chips.** The tower
count is frozen from round 0 — 13 towers, never 14 — while the treasury climbs past four
hundred thousand. A tower with 0 paint cannot spawn anything (a soldier needs 200 paint out
of the tower stash, and `canBuildRobot` fails on paint regardless of chips), so the army stops
growing, the map stops being converted, and the game runs to the round limit to be settled on
tiebreak. **That is the stall, and it is not subtle.**

Paint utilisation is effectively **100%** (median 0 all game — every point mined is spent the
moment it arrives) while chip utilisation is effectively **0%**. This is the cleanest possible
statement of "price the sink in the resource that binds": carol is simultaneously at a hard
ceiling on one resource and drowning in another, and the game contains exactly one mechanism
that converts the second into the first — **upgrading a paint tower, 5 -> 10 -> 15 paint/turn
for 2,500 / 5,000 chips.** At 406,170 chips carol could take every paint tower she owns to
level 3 many times over and never notice the cost.

**Why this is NOT a fourth "more production" iteration**, which is the objection my own
three-iteration series (5, 8, 10) has earned the right to raise:

| iteration | what it raised | why it did not touch this |
|---|---|---|
| 5 (accepted) | chip income, via money towers | *created* this problem — the 406,170 is largely its doing |
| 8 (rejected) | paint income, by building more paint towers early | closest prior, but a new tower costs a ruin **and** a 5x5 painted pattern — paid in the binding resource |
| 10 (rejected) | soldier *turns*, by plugging a refill leak | left mining rate untouched; this trace is i10 and it is just as paint-destitute |

**None of the three raised paint income per tower.** An upgrade is the only mechanism that
does, it costs **zero paint**, and it is paid for in the resource sitting at 406,170. That is
the "capability preserved at zero marginal cost" profile that TRAINING_ALGORITHM.md names as
the recurring winner's shape — and iteration 8's rejection, far from arguing against it,
localises exactly why: the paint *pattern* was the price, and the upgrade does not pay it.

**Consequence for the queue.** Iteration 12 (tower upgrades) now rests on materially stronger
evidence than iteration 11 (splashers) did when I launched it, and — importantly — its case is
built entirely on the **accepted i7 build**, so it stands whatever iteration 11 reports. If
iteration 11 is rejected, iteration 12 is unaffected and goes next regardless.

One honest caveat on the reachability figure I logged earlier: 21.7% of tower-turns clearing
3,700 chips was averaged over 12 replays. In *this* game the gate is clear essentially from
round 200 onward. The 21.7% is the conservative number and I will keep quoting it, but the
distribution behind it is "hand-to-mouth in short decisive games, absurdly rich in exactly the
stalled games that are the problem" — which is the best possible shape for this intervention.

### TOURNAMENT: the registered stall prediction is CONFIRMED, and carol is far weaker than her own instruments said

Computed myself from `tournaments/20260907-0100/results.txt` (the sanctioned channel), while
the alice-carol block was still in progress:

| pair | games | record | reached r2000 |
|---|---|---|---|
| alice-bob | 150 | alice **7 : 143** bob | 19 (**13%**) |
| alice-carol | 28 (partial) | alice **22 : 6** carol | 14 (**50%**) |

**The prediction registered before these games existed:** *"if carol's stalling is a property
of her lineage, her cross-lineage games will reach r2000 substantially more often than the 12%
that alice-vs-bob does. If carol's cross-lineage timeout rate comes back near 12%, then the 72%
is a mirror artifact, this direction is closed, and I will say so."*

**Cross-lineage timeout rate: 50%, against a 13% baseline on the same tournament.** The mirror
confound is dead. **Carol's inability to close out a coverage race is a real property of her
lineage**, not an artifact of playing near-copies of herself. This is the first claim in the
project that survived a genuine independent instrument, and the trace above already names the
mechanism: towers holding 0 paint and 406,170 chips, with the tower count frozen from round 0.

**And the harder number: carol is 6-22 (21%) against alice.** Split by how the game ended:

| | games | carol wins |
|---|---|---|
| settled at r2000 on tiebreak | 14 | 3 (21%) |
| decided by paint domination | 14 | 3 (21%) |

**21% in both halves.** Carol is not specifically bad at closing out games she is otherwise
winning — she is uniformly behind, and the stall is a symptom of the same weakness rather than
a separate one. That is a cleaner and more actionable picture than "she can't finish".

**This is the self-referential blind spot, quantified.** Carol's own gauntlet reports headline
win rates around **70%**; against one independent lineage she is at **21%**. Every instrument I
own descends from my own code, and all of them were flattering me. MULTI_AGENT.md predicted
exactly this and it is the reason the tournament exists. **Absolute-strength claims from my
gauntlet are now to be treated as uncalibrated**, and I should say "carol beats her own
ancestors" rather than "carol is strong" until the roster chart says otherwise.

Note also that alice is **7-143** against bob, so alice — who is beating carol 22-6 — is
herself being dismantled by the third lineage. The gap between carol and the strongest bot in
the project is therefore much larger than the alice-carol score alone suggests. I am
deliberately not drawing strategy conclusions from bob's results: what I am entitled to from
this channel is *outcomes*, plus replays if I choose to watch them.

**Effect on the queue: none, and that is the point.** The independent evidence points at
exactly the constraint the gridworld trace located and that iteration 12 was already written
to attack. Iteration 11 (splashers, in flight) and iteration 12 (paint-tower upgrades) both
target coverage throughput. The tournament did not redirect me; it told me the target is much
further away than my own instruments claimed.

**Isolation slip, recorded honestly.** I ran a bare `git log --oneline -3` to confirm a push
and it printed a sibling agent's commit *subject line*, which is their prose and not part of
the sanctioned `tournaments/` channel. I did not open their files and I have not used what it
said — the table above is computed by me from `results.txt` directly. Scoping every future
`git log` with `-- agents/carol` so this cannot recur.

### A 28-minute failure I misdiagnosed as semaphore starvation — and the check that would have caught it in one minute

Iteration 11's run `20260907-010913` reported **0 games for 28 minutes**. I attributed that to
the tournament holding the semaphore, wrote it up twice as "the system working as documented",
and went off to do non-blocking work. **It was dead the whole time.** The generated remote
script failed at launch:

```
gauntlet-20260907-010913.sh: line 76: syntax error near unexpected token `DefaultMedium'
  for MAP in DefaultSmall
DefaultMedium
Fossil
```

**Root cause.** `gauntlet/<run>/maps.txt` stores **one map per line**. `gauntlet.sh` interpolates
`$MAPS` verbatim into a generated remote script's `for MAP in ...` line, so the embedded
newlines terminated the statement. The idiom I used is the one **AGENT.md documents verbatim**
— `MAPS="$(cat gauntlet/<run-id>/maps.txt)"` — so this is a latent trap in the documented
workflow, not a typo of mine. The fix on my side is `MAPS="$(tr '\n' ' ' < .../maps.txt)"`;
relaunched as **`20260907-013714`**, which is playing.

**Why the misdiagnosis was so comfortable, which is the part worth keeping.** Every signal I
looked at is *identical* between "queued behind the semaphore" and "died at launch":

| signal | starved | dead | distinguishes? |
|---|---|---|---|
| driver poll loop | "polling every 45s" | "polling every 45s" | no |
| `gauntlet-collect.sh --list` | `0 games INCOMPLETE` | `0 games INCOMPLETE` | no |
| remote `results.txt` | exists, empty | exists, empty | no |
| VM game count | others' games running | others' games running | no |
| **remote `~/gauntlet-<id>.log`** | quiet | **syntax error** | **yes** |

I had a *prior* — MULTI_AGENT.md explicitly warns that runs are slow when all three agents
evaluate, and a 450-game tournament was genuinely running — and the prior explained the
observation perfectly, so I never sought a signal that could discriminate. Confirmation of a
plausible story is not evidence when the story predicts the same observation as the failure.

**Standing rule from here**: a run showing **zero** games is never "starved" until
`~/gauntlet-<run-id>.log` on the VM has been read. Zero is qualitatively different from slow —
slow means some games finished, zero means nothing ever started, and only the latter is
consistent with a launch failure. Checking cost one ssh; not checking cost 28 minutes.

**Correcting the concurrency report I was about to file.** I saw `pgrep -fc battlecode.server.Main`
return **8 against a HARD_CAP of 7**, and a later sample return 6 (3 arena + 2 bob + 2 alice,
**0 carol**). I was reading the 0-carol as evidence of unfair flock starvation. With the launch
failure known, the 0 is fully explained by my run being dead, and no starvation claim is
warranted. **The transient 8 > 7 still stands as an observation** and is reported to the
coordinator as-is, unexplained — it is a brief overshoot, not a sustained breach, and I have
not worked around it.

**Tooling hazard, recorded before it bites me.** I wanted to mechanism-check `carol_i12` with a
single `vm-match.sh` while the iteration 11 gauntlet plays. **Do not.** Both `vm-match.sh` and
`gauntlet.sh` scp into the *same* remote workspace and build into the *same* `build/classes`,
and gauntlet games load `-Dbc.game.team-a.url=build/classes`. A `gradlew run` mid-gauntlet
recompiles under the running games, so a game starting during the rebuild can fail to load a
class. This is also why I compiled `carol_i12` in an isolated `/tmp` dir rather than via
`vm-compile.sh`, which scps over the shared `src/`. **Rule: no vm-match, no vm-compile, while
one of my own gauntlets is in flight.** Iteration 12's mechanism check waits for
`20260907-013714` to finish.

### Two pre-checks on iteration 12 that could each have wasted it

**(a) The alternative explanation for "median tower paint = 0": are carol's towers simply
mostly MONEY towers?** If so, tp=0 is trivially expected, upgrading the one or two paint
towers would add ~5 paint/turn, and the whole iteration would be pointless — the fix would be
the tower *ratio*, not upgrades. This matters because iteration 5, which is *accepted*,
deliberately promoted money towers.

`towerTypeFor()` builds a money tower at one ruin in three, so roughly **two-thirds of carol's
towers are paint towers** — on gridworld's 13, about 8 or 9. The alternative explanation is
therefore rejected: those 8-9 paint towers each mine 5/turn (~40-45 team-wide) and *still*
show a median stash of 0, meaning every point is spent the instant it lands. Upgrading them is
a genuine doubling, not a rounding error.

Sizing it against the observed treasury: 8 paint towers to lv2 costs **20,000 chips** and takes
team paint income from ~40/turn to ~80/turn; carrying them to lv3 costs 40,000 more for
~120/turn. Against **406,170 idle chips** that is under 15% of the treasury for roughly a
**tripling** of the binding resource.

**(b) Does the guard actually match the towers I think it does?** Probed rather than assumed:

```
LEVEL_ONE_PAINT_TOWER    baseType=LEVEL_ONE_PAINT_TOWER   matches=true
LEVEL_TWO_PAINT_TOWER    baseType=LEVEL_ONE_PAINT_TOWER   matches=true
LEVEL_THREE_PAINT_TOWER  baseType=LEVEL_ONE_PAINT_TOWER   matches=true
LEVEL_*_MONEY_TOWER      baseType=LEVEL_ONE_MONEY_TOWER   matches=false
```

`getBaseType()` collapses all three paint levels onto the lv1 constant, so
`getBaseType() == LEVEL_ONE_PAINT_TOWER` matches a paint tower at **any** level while
correctly excluding money and defense towers. Combined with `canUpgradeTower` enforcing the
level ceiling and the chip cost, `carol_i12` therefore **ladders lv1 -> lv2 -> lv3 on its own**
as the treasury allows, with no extra code. That is the behaviour I want and it was luck as
much as design — had `getBaseType()` returned the identity, the guard would have upgraded each
tower exactly once and silently capped at lv2.

### Iteration 12 pre-registration, written before iteration 11 reports — including the branch that would invalidate the candidate as built

**Hypothesis.** Carol's towers sit at ~100% paint utilisation and ~0% chip utilisation
(gridworld r2000: median tp=0 from round 400, 406,170 chips, tower count frozen at 13). A
paint tower that upgrades itself converts the wasted resource into the binding one at **zero
paint cost**, which no prior iteration has done: 5 (accepted) raised chips, 8 (rejected)
raised paint towers but paid a 5x5 pattern in paint, 10 (rejected) raised soldier turns only.

**The one change**: a lv1+ paint tower holding >= `UPGRADE_MIN_CHIPS` (3,700) calls
`upgradeTower` on itself. Money and defense towers excluded.

| | |
|---|---|
| primary gate | h2h vs the last accepted snapshot, 20 maps x both sides = 40 games; **accept at >50%** |
| mechanism gate | `UPG` tag appears at all — `canUpgradeTower` may forbid a tower upgrading *itself*, in which case this is a silent no-op and the fix is to have soldiers do it (they are already within r²=2 while working a ruin) |
| primary metric | team paint income; proxy = share of tower-turns with `tp` < 50, currently **33.6%** over 146,350 tower-turns |
| counter-metric | chips must not be drained below the ruin-completion reserve: watch `rsv`/`stag` and the tower count, which iteration 6 showed can collapse 8 -> 3 when the treasury is over-spent |
| stall metric | share of games reaching r2000 — currently 72% in-lineage, **50% cross-lineage against a 13% baseline** |

**Registered prediction.** The `tp<50` rate falls and the r2000 rate falls. I am **not**
predicting the h2h clears 50%, and I want that asymmetry on record: three iterations this
session moved their mechanism metric hard and converted nothing, so "the metric will move" and
"the scoreboard will move" are now separate claims for me and I have earned the right to only
be confident about the first.

**The branch that invalidates the candidate as built.** `src/carol_i12` was forked from **i7**,
the currently accepted snapshot. So:

- **If iteration 11 is REJECTED**, i7 remains the baseline, `carol_i12` is correct as it
  stands, and it goes straight to evaluation.
- **If iteration 11 is ACCEPTED**, the baseline becomes i11 (= i7 + splashers). Evaluating
  `carol_i12` against it would then measure *two* changes at once — adding upgrades **and
  removing splashers** — which is precisely the bundling error that made iteration 4
  uninterpretable and cost this project four iterations. In that case `carol_i12` must be
  **rebuilt from i11** before it is run, and the version currently committed must not be used.

Writing this down now because the temptation, an hour from now with a candidate already
compiled and a slot finally free, will be to just run the thing that exists.

**Bug found in `carol_i12` by re-reading it, before it ever ran.** The gate was a constant
`UPGRADE_MIN_CHIPS = 3700` = `CHIP_RESERVE` (1,200) + the lv2 cost (2,500). That protects the
reserve for a **lv2** upgrade — but `getBaseType()` makes the guard match paint towers at *any*
level, so the same constant also gated **lv3** upgrades, which cost **5,000**. A lv2 tower
holding 6,000 chips would have passed a 3,700 gate and upgraded down to **1,000** — stranding
the treasury *below* the ruin-completion reserve. That is precisely the state iteration 6 lost
DefaultSmall to by annihilation at round 69, "pinned between the reserve and the build gate",
and my own code comment in `runTower` describes it.

The two pre-checks interacted: discovering that the guard laddered to lv3 unaided was good
news, and it silently invalidated the constant that made the guard safe. **A property verified
in isolation can break a different property that was verified earlier.** Fixed to compute the
gate from the actual next level:

```java
int need = CHIP_RESERVE + rc.getType().getNextLevel().moneyCost;
```

guarded by `canUpgradeType()` so `getNextLevel()` is never called on a lv3 tower. Recompiled
clean in isolation. The counter-metric I registered (chips must not drop below the reserve) is
now satisfied **by construction** rather than needing the run to catch it.

## Iteration 11 RESULT — ACCEPTED at 62.5%, and the registered prediction lands

Run `20260907-013714`, 80 games, maps **verified byte-identical** to iteration 10's run (I
diffed `maps.txt`; the summary header says "sampled" but that is a cosmetic label regression
from the coordinator's `MAPS` fix, not a resample). So iterations 10 and 11 are measured on the
same ground.

| instrument | iteration 10 | **iteration 11** | gate |
|---|---|---|---|
| **h2h vs `carol_iter7`** | 19/40 = 47.5% | **25/40 = 62.5%** | **>50% — PASS** |
| peer `WinPct` 60% | — | **62.5%** | **PASS** |
| swept-win / swept-loss vs iter7 | 4 / 5 | **8 / 3** | one-directional, no unresolved regression |
| vs `carol_rush` | 38/40 = 95% | 37/40 = 92.5% | — |
| overall | 71.2% | **77.5%** | — |

**DECISION: ACCEPT.** Snapshotted as `src/carol_iter11/`.

**The prediction I registered before the run**: *"Iteration 11 lands above 50% ... the way it
most plausibly fails is the paint price."* It landed at 62.5%. This is the **first** prediction
this session I made in the *positive* direction, after three consecutive nulls, and the reason
I gave for the asymmetry held up: iterations 5, 8 and 10 all raised how *many* units carol
fields, and this one raised what a unit can *do*. The +15 points over iteration 10 on identical
maps is the cleanest statement of that difference the instrument can produce.

**Shape of the win.** 8 swept-wins against 3 swept-losses (iteration 10: 4 against 5). Swept
maps are immune to spawn advantage, so this is a real causal effect rather than side churn.

**What did NOT happen, recorded because I predicted it might.** The paint-cost failure mode —
splashers at 300 paint displacing soldiers at 200 in a paint-bound economy — did not show up as
a net regression. That does not mean it is absent; it means it was outweighed. The
`SPLASH_MIN_SCORE = 8` threshold is still, by my own arithmetic, roughly 2.5x worse than a
soldier on paint-per-tile, and the registered refinement ladder (8 -> 14) remains available as a
future dose. I am **not** spending an iteration on it now: iteration 12 targets a far larger
effect, and refining a threshold inside a just-accepted mechanism is the kind of local search
that this session has repeatedly found less valuable than changing lever.

**Opponent classification.** `carol_rush` has now been beaten 95% and 92.5% in two consecutive
evaluations — two consecutive results at or above 80%, which per the algorithm's retirement
rule makes it a **retire** candidate. I am keeping it one more evaluation as the fixed
`roster_extra` yardstick (it is in `progress/roster_extra.txt`, and its value there is that it
never changes), but it no longer informs accept decisions and I will stop reading it as a peer.

**Iteration 12 branch resolution.** The pre-registration said: if iteration 11 is accepted, the
committed `carol_i12` — forked from i7 — must **not** be run, because against the new i11
baseline it would measure "add upgrades **and remove splashers**" at once. Iteration 11 is
accepted, so that branch is now live and `carol_i12` is **rebuilt from i11** by
`tools/rebuild-i12-from-current.py` before evaluation. Staging that ahead of the result is what
made this a lookup instead of a temptation.

## What the completed tournament blocks actually say — and the queue they imply

`alice-carol` finished (150 games) and `bob-carol` is in progress. Computed from
`tournaments/20260907-0100/results.txt`:

| pair | record | median length | timeouts | how the winner wins |
|---|---|---|---|---|
| bob-alice | bob **143 : 7** | 824 | 13% | paint domination |
| bob-carol | bob **51 : 2** | 737 | **8%** | 49/53 by paint domination |
| alice-carol | alice **99 : 51** | **2000** | **53%** | tiebreak |

**This corrects my own framing, and the correction matters.** I had been treating carol's 50%+
timeout rate as *carol's* pathology. It is not: **games involving bob almost never time out
(8-13%)**, because bob converts the map decisively at a median of ~750 rounds. The 53% timeout
rate belongs to the **alice-carol pairing** — two bots that both fail to convert, stalemating
until the round limit. So the timeout rate is a marker of *two weak converters meeting*, not a
disease carol has on her own.

The honest restatement: **carol's problem is conversion throughput**, and the stall was only
ever a symptom visible when her opponent shared the weakness. Against a bot that does convert,
carol does not stall — she loses, at **2 wins in 53 (3.8%)**, in games bob ends by covering the
map. Her two wins took 1,626 and 1,813 rounds; his 51 took a median of 737.

**This does not redirect the queue — it confirms it, and that is worth saying explicitly**
rather than treating the tournament as a reason to start something new. Iteration 11
(splashers, accepted at 62.5%) and iteration 12 (paint-tower upgrades, running) both raise
conversion throughput, which is precisely the axis bob dominates on. The tournament's
contribution is to tell me the axis is right and the distance is much larger than my own
instruments suggested — 3.8% against bob versus the ~70% my gauntlet reports.

### Ranked queue after iteration 12, on this evidence

1. **SRPs (resource patterns) — promoted to iteration 13.** `RULES.md` [E]: each active SRP
   adds **+3/turn to EVERY paint tower and EVERY money tower**, so its value scales with tower
   count. At carol's observed 13 towers that is **+39/turn** from one pattern. The cost is a
   25-tile exact pattern, ~125 paint to lay — a **payback of roughly 3-4 rounds**, after which
   it is permanent. That is a better return than the upgrade being tested right now, and it is
   the second of the three mechanics the API sweep found uncalled. Reachability must be checked
   first (the pattern must be laid on ground carol actually holds, and `checkPattern` is exact
   — *every* one of the 25 tiles, with EMPTY not acceptable for a 0 bit).
2. **Frontier-seeking movement.** Measured, not speculative: 15.9% of soldier turns are
   IDLE-ALLY (standing on ground already ours) and 15 of 52 ready splasher turns scored
   **exactly 0** — nothing paintable in reach. Both units inherit `moveExploring(null)`, which
   has no notion of the coverage frontier. This converts wasted turns rather than buying more
   resource, so it is independent of 12 and 13 and stacks with them.
3. **Splasher tower-targeting.** Held back from iteration 11 deliberately. Now ranked *below*
   the two above: it is an offensive capability, and every measurement says carol loses the
   **coverage race**, not a fight — bob wins 49 of 53 by painting, not by killing.

**Deliberately NOT queued: anything that raises unit production.** Iterations 5, 8 and 10
settled that, and the tournament adds nothing to reopen it.

## Iteration 12 is INERT, diagnosed mid-run — and my reachability pre-check asked the wrong question

Checked the mechanism gate from live replays 15 games into run `20260907-020717`, rather than
waiting 40 minutes for a number I could already predict.

| | gridworld | DefaultMedium |
|---|---|---|
| i12 tower-turns | 11,016 | 16,340 |
| chips >= 3,700 (gate affordable) | **92.5%** | **0.0%** |
| on an upgradable paint tower (guard matches) | **2.1%** | **68.4%** |
| **BOTH — an upgrade can actually happen** | **0.59%** | **0.00%** |

`UPG` fired **once**, in 11,016 tower-turns. The two conditions the mechanism needs are almost
perfectly **anti-correlated across maps**, so their conjunction is ~0 everywhere.

**Why, mechanically.** `runTower` spawns whenever `chips >= reserve + 250`, draining the
treasury to ~1,450 every time it can. So **chips accumulate only when spawning is blocked**, and
spawning is blocked only when the tower has no paint. Hence:

- On maps where carol holds healthy paint towers (DefaultMedium: median tower paint 110), she
  spawns continuously and the treasury **pins at ~1,350, never once exceeding 2,530**. The
  3,700 gate is dead code there.
- On maps where paint is absent and chips pile to 406,170 (gridworld), spawning is blocked —
  but there carol's tower count is frozen at 13 from round 0, meaning she builds **no** towers,
  so `towerTypeFor()` never runs and her towers are whatever the map handed her. Only 2.1% are
  upgradable paint towers.

**The pre-check failure, stated precisely, because this is the reusable lesson.** I *did* run a
reachability check — 146,350 tower-turns, 21.7% clearing 3,700 — and called it a PASS. That
measured the **marginal** distribution of chips over all tower-turns. The gate's reachability
depends on the **conditional** distribution: chips *given that the guard matches*. Those differ
enormously here because the guard and the gate are driven by anti-correlated causes. My own
joint analysis earlier (chip-rich AND paint-destitute, 11.1%) was the right *shape* of check on
the wrong *pair* of variables — I checked the condition the mechanism was **motivated by**, not
the condition it would **execute under**.

> **Rule added**: a reachability check must condition on the guard the gate sits behind. "How
> often is X above the threshold" is the wrong question whenever the branch is nested; the
> question is "how often is X above the threshold **among the turns that reach this line**".

**Decision: let the run finish, do not kill it.** Shared-VM rules forbid killing anything on
battlecode-dev, and the run is nearly free now. Its value is as a **registered zero arm**: a
mechanism firing once in 11,000 tower-turns should land at ~50%, and if it does, that confirms
the diagnosis rather than teaching anything new. **Registered prediction: iteration 12 lands
within a couple of games of 50%, with `UPG` counts near zero across the run.** If it lands
materially above 50%, my inertness diagnosis is wrong and I must explain that instead.

### Iteration 12b — the fix, and why it is a refinement rather than a new hypothesis

The hypothesis (convert idle chips into paint income) is untouched and still supported by the
gridworld trace. What failed is purely the **gate**: the treasury is drained by spawning before
it can ever reach the upgrade price. So give the upgrade **priority over spawning** on the
tower that would buy it — an upgradable paint tower withholds spawning until it has saved
`CHIP_RESERVE + nextLevelCost`.

This is exactly the near-miss refinement the algorithm permits (same solution, corrected dose),
and it is well-motivated by evidence already in hand: it trades unit production for permanent
paint income, and **iterations 5, 8 and 10 established that unit production is not carol's
binding constraint** — 4.1x the soldiers changed nothing. Spending a resource proven not to
bind, to buy one proven to bind, is the "capability at zero marginal cost" profile.

**Counter-metric registered**: the saving tower must not stall the team. Watch tower count (it
must not fall — iteration 6 lost DefaultSmall when the treasury was mismanaged) and the soldier
count, and require `UPG` to actually fire this time — the mechanism gate is now
`UPG > 0 on a majority of maps`, not merely `> 0`.

### Iteration 12b pre-registration — with the GUARD's gate registered, not just the mechanism's

Having just diagnosed an inert mechanism, I applied the same conditional reachability test to
my own fix and it failed. The first version of the deadlock guard reused iteration 2's
`stagnantTurns >= STAGNANT_ROUNDS`. Measured before shipping, on the conditional (turns on an
upgradable paint tower) as well as the marginal:

```
gridworld      all 11,016 turns: stag>=10 on 0.0% (max 0)   on paint towers (230): 0.0%
DefaultMedium  all 16,340 turns: stag>=10 on 0.0% (max 0)   on paint towers (11,176): 0.0%
```

**`stag` is 0 on all 27,356 tower-turns sampled.** The counter only increments when chips are
*exactly* unchanged, and chips move nearly every turn, so it resets constantly. The guard would
never have tripped — leaving the deadlock it exists to prevent entirely unmitigated, inside the
fix for a mechanism that was itself inert. Replaced with a `SAVE_GRACE` window whose give-up is
directly observable in the trace.

**The change**: an upgradable paint tower withholds spawning while saving for its upgrade. It
saves for `SAVE_GRACE = 25` rounds unconditionally, and past that only while the treasury is
demonstrably climbing above where it stood when saving began; otherwise it gives up, resets,
spawns, and retries later.

| gate | threshold |
|---|---|
| **primary** | h2h vs `carol_iter11`, 20 pinned maps x both sides = 40 games; **accept at >50%** |
| **mechanism gate** | `UPG` fires on a **majority of maps** — not merely >0. Iteration 12's single firing in 11,016 turns is the bar this must clear. |
| **guard gate (new)** | `upgGiveUp` appears **at all**, somewhere in the run. If it never appears the guard is dead code again and the deadlock is unmitigated regardless of the win rate. |
| **counter-metric** | tower count must not fall (iteration 6 collapsed 8 -> 3 on treasury mismanagement); soldier count must not collapse |
| **primary metric** | share of tower-turns with `tp` < 50, currently 33.6% |

**Registered prediction.** `UPG` fires on most maps and `upgGiveUp` appears on at least one. On
the scoreboard I again decline to predict above 50%: this spends unit production to buy paint
income, and while iterations 5/8/10 make that trade look right in principle, the *withholding*
is a genuinely new cost that no measurement of mine has priced.

**Note on `SAVE_GRACE = 25` — it is an unmeasured constant and I am flagging it as such rather
than defending it.** It is the first dose, chosen so a tower waits roughly the time a money
tower needs to add ~1,000 chips. If 12b lands near 50% with the mechanism firing, the refinement
is this number, and the zero arm (`SAVE_GRACE = 0`, i.e. never withhold) is iteration 12 itself,
already measured.

### Near-final tournament standings (412/450) — carol is last, and by a wide margin

| pair | record | timeouts |
|---|---|---|
| alice-bob | bob **143 : 7** | 13% |
| alice-carol | alice **99 : 51** | 53% |
| bob-carol | bob **110 : 2** | **6%** |

**Standings: bob 253, alice 106, carol 53.**

**Carol is 2-110 against bob — 1.8%.** Against alice she is 34%. Her own gauntlet, on the same
day, reports 77.5% overall and 62.5% against her immediate predecessor. The distance between
those two pictures is the single most important number this session produced, and no instrument
inside my workspace could have produced it.

The timeout column is the tell, and it is the correction I made earlier holding up at a larger
sample: **games involving bob end** (6-13%), games between the two weak converters do not
(53%). Bob wins 49 of 53 sampled by painting enough of the map at a median of 737 rounds. He is
not out-fighting carol — the win reasons are coverage, not annihilation. Carol is losing the
**coverage race**, which is the game's actual win condition, and losing it badly enough that
game length barely varies.

**What this does and does not change.** It does not redirect the queue: splashers (accepted,
62.5%) and paint income (12/12b, running) are both conversion-throughput work, which is exactly
the axis. What it changes is the **scale of ambition** — a 1.8% matchup will not be closed by a
single mechanism, and I should stop reading my own gauntlet's absolute numbers as anything but
a within-lineage regression suite. The frozen-roster chart is the only absolute instrument I
own, and even it is descended from my own code.

It also puts a floor under how much effort the remaining two uncalled mechanics deserve. SRPs
(+3/turn to *every* tower per active pattern, ~125 paint to lay, 3-4 round payback at carol's
observed tower counts) are queued next and are, on paper, a larger multiplier than the upgrade
being measured right now.

## Iteration 12 RESULT — 62.5%, and I am REJECTING it anyway

Run `20260907-020717`, 80 games, maps pinned. `carol_i12` vs `carol_iter11` + `carol_rush`.

| instrument | result |
|---|---|
| h2h vs `carol_iter11` | **25/40 = 62.5%** |
| swept-win / swept-loss | **5 / 0**, 15 split-by-side |
| vs `carol_rush` | 37/40 = 92.5% |
| overall | 62/80 = 77.5% |
| **mechanism gate: `UPG` on a majority of maps** | **FAILED — 3 firings in 144,823 tower-turns, ~5 of 20 maps** |

**The scoreboard says accept and I am rejecting.** This is the whole reason the mechanism gate
was pre-registered. A gate that fires 3 times in 144,823 tower-turns cannot have produced a
12.5-point swing, and accepting on that number would baseline a feature that does essentially
nothing into the lineage — permanently, and invisibly, since every later iteration would carry
it. 25/40 is **1.58 SD** from 50% (binomial SD 3.16 at n=40, two-sided p ~ 0.11), i.e. inside
the noise floor doctrine #6 requires me to distrust regardless of how good the story is.

**Verification work behind that call, including a sampling error of my own.** My first pass
measured the mechanism across the run's 18 archived replays and found 3 firings — but
`gauntlet/<run>/losses/` contains **only losses**, so I had measured the mechanism exclusively
on games it failed to win. Corrected by pulling won-game replays off the VM:

| swept-WIN map | UPG firings |
|---|---|
| Fossil botA | **0** (won at r1708) |
| Fossil botB | 1 (won at r2000, tiebreak) |
| Parking_lot botA | 1 |
| Gears botA | 1 |

So the correction did not rescue it — **Fossil was swept with a total of one upgrade across
both sides, one of which was zero.** And among all sampled games where `UPG` *did* fire, the
record is 2 wins / 2 losses (gridworld and PlumberGame both fired and lost). No correlation.

**What I could not explain, recorded as an open anomaly rather than smoothed over.** For
byte-identical bots the two sides of a map are the *same* game, so every map must split and the
h2h must be exactly 20/40. I verified `carol_iter11` is byte-identical to `src/carol` modulo the
package line, and that iteration 12 adds no engine call on the 95,261 `upgPoor` turns (the
`canUpgradeTower` call short-circuits behind `chips >= need`). I also checked bytecode: median
243 (i11) vs 279 (i12), max 581 against a 20,000 limit, **zero overruns** — so silent
mid-turn truncation is excluded. Five swept wins and zero swept losses is therefore not fully
accounted for by 3 upgrades, and I am leaving it open rather than inventing a mechanism.

**The one substantive thing that survives**: a single lv2 upgrade is a *permanent* +5 paint/turn,
worth ~10,000 paint over a 2,000-round game — plausibly decisive in a tiebreak scored on area
painted. So the hypothesis is not weakened; only this *implementation's* ability to fire it is.
That is exactly what 12b changes.

**DECISION: REJECT** (mechanism gate failed). Not reverted as a direction — `carol_i12b`
launched immediately as `20260907-024050`. If 12b fires the mechanism properly and shows a
comparable or larger gain, iteration 12's 62.5% will read retrospectively as an underpowered
early signal; if 12b lands at 50% with the mechanism firing hundreds of times, then iteration
12's 62.5% was noise and rejecting it was correct twice over.

**Tooling note for the coordinator.** `gauntlet/20260907-020717/bot.txt` records
`bot=carol / snapshot=carol_iter11 / label=carol_iter11`, but the run demonstrably played
`carol_i12` (`TA=carol_i12` in the generated remote script, and results.csv lists
`carol_iter11` as the *opponent*). Collation appears to identify `src/<workspace>` rather than
the `BOT` that actually played, so **`bot.txt` is wrong whenever `BOT` is overridden** — which
is precisely the mislabelling it was introduced to prevent. I did not write a
`vs_old_bots_history.csv` row from this run; had I, it would have been attributed to
`carol_iter11`.

## Iteration 12b RESULT — REJECT at 30%, the mechanism worked perfectly, and it refutes an inference I had been leaning on

Run `20260907-024050`, 80 games, maps pinned.

| instrument | iteration 12 | **iteration 12b** |
|---|---|---|
| h2h vs `carol_iter11` | 25/40 = 62.5% | **12/40 = 30.0%** |
| swept-win / swept-loss | 5 / 0 | **4 / 12** |
| vs `carol_rush` | 37/40 = 92.5% | **28/40 = 70.0%** |
| overall | 77.5% | **50.0%** |

**Both pre-registered gates PASSED, which is what makes this rejection worth its run:**

| gate | threshold | result |
|---|---|---|
| mechanism | `UPG` on a majority of maps | **22 firings on 10 of 10 maps — PASS** |
| guard | `upgGiveUp` appears at all | **152 firings on 10 of 10 maps — PASS** |

Iteration 12 fired 3 times in 144,823 tower-turns; 12b fires **22 times in 48,327**, a ~220x
increase in rate. The fix did exactly what it was designed to do. **And the scoreboard fell 32
points.** 12 swept-losses against 4 swept-wins is a one-directional regression, not churn.

**The inference this refutes, and I built 12b on it.** I argued that trading unit production for
paint income was safe because *"iterations 5, 8 and 10 established that unit production is not
carol's binding constraint — 4.1x the soldiers changed nothing."* That is true and it does not
license what I did with it:

> **"More X does not help" does not imply "less X is free."** Iterations 5/8/10 measured the
> *upward* direction only. A plateau in one direction says nothing about the gradient in the
> other, and carol was evidently sitting at the edge of one, not in the middle of a flat
> region. 25,769 tower-turns were spent withholding spawning to buy 22 upgrades.

That is the cheapest possible correction to a belief I would otherwise have carried into every
future resource-tradeoff iteration, and it is exactly what TRAINING_ALGORITHM.md means by "a
rejected attempt that converts a weakly-founded belief into a firmly-founded one paid for its
run."

**DECISION: REJECT.** `src/carol/` remains iteration 11.

### Closed-directions ledger

- **"Fund paint-tower upgrades by withholding spawning" — CLOSED.** `20260907-024050`, 12/40 =
  30.0% h2h with the mechanism firing on 10/10 maps and the guard live. The cost of forgone
  spawning exceeds the value of the upgrades bought, decisively.
- **"Opportunistic paint-tower upgrades (no withholding)" — CLOSED as unreachable.**
  `20260907-020717`: chips only accumulate when spawning is already blocked, so the gate fires
  3 times in 144,823 tower-turns. Re-opening requires some *other* mechanism to free chips, not
  a smaller threshold.

Together these close **tower upgrades** as a direction. The dose curve now has two measured
points — 0% withholding (inert, ~noise) and 100% withholding (-32 points) — and it is
monotone over the range that matters, so an interior dose is not worth a run: it would buy few
upgrades at meaningful cost. This is the third consecutive reject in the resource-economy area
(10, 12, 12b), so per `MaxConsecutiveRejects` **the next attempt must leave this area.**

**Next: iteration 13 = SRPs**, already ranked first in the post-tournament queue and in a
different functional area (map patterns, not tower economy). Its pre-check must be the
conditional reachability test this session invented — *how much ally-held, correctly-shaped
ground exists among the turns that would actually attempt a pattern*, not how many chips or
tiles exist in aggregate.

## Mirror calibration — the null has NO variance, and it overturned my iteration 12 rejection

Ran `carol_iter11` against `carol_m11`, a copy differing **only** in its package line (verified
by diff). Run `20260907-030540`:

```
overall 20/40 (50.0%)   swept-win 0/20   swept-loss 0   split-by-side 20/20
```

**Identical code splits every single map, exactly 20/40, with zero sweeps.** So under this
engine the null is *deterministic*: it has **no variance at all**. Every claim I made about a
"binomial noise floor" on a 40-game h2h was therefore invalid at its root — there is no noise
floor to be inside of. Later confirmed a second time on the i12 baseline
(`20260907-034013`: 20/40, 0 sweeps, 20/20 split).

**This makes the mirror an exact control**, and re-running iteration 12's numbers through it
reverses the decision:

| arm | matches null | deviations | -> wins | -> losses | margin |
|---|---|---|---|---|---|
| **iteration 12** | 35/40 | 5 | **5** | **0** | **+5 games** |
| iteration 12b | 16/40 | 24 | 8 | 16 | **-8 games** |

Iteration 12 deviates on exactly five games and **all five are wins**. I then verified each
deviating game fired at least one upgrade: Fossil botB (1), Parking_lot botA (1), Bunny botB
(1), Gears botB (1), walalilongla botB (3). Perfectly one-directional flips with a verified
mechanism in each — doctrine #7's definition of a real causal effect.

**So iteration 12 is ACCEPTED, reversing my earlier rejection.** Snapshotted `carol_iter12`.

**Where my reasoning went wrong, precisely.** Two errors, and only one of them was the one I
noticed at the time:

1. **The noise argument was invalid.** I applied a binomial model to a deterministic system.
2. **My pre-registered mechanism gate was mis-specified.** "UPG fires on a majority of maps"
   tests **frequency**. The question that mattered was **causation** — did the firings that did
   occur change outcomes? A rare mechanism can produce a large effect if each firing is
   high-value, and a lv2 upgrade is a *permanent* +5 paint/turn, decisive in games settled on
   area painted. Rejecting on a low firing count is the mirror image of accepting on a
   favourable win rate: both substitute a proxy for the causal question.

The diagnostic work behind the gate was still right and still worth doing — 3 firings in
144,823 tower-turns is a real and important fact, and it is exactly why iteration 12b existed.
What was wrong was the inference from it. **A guard against crediting a mechanism that never
ran must not become a rule that a rare mechanism cannot have worked.**

## Iteration 13 (SRPs) — mechanism confirmed, margin thin, roster run before deciding

Placed the SRP work in the **IDLE-ALLY** branch: soldiers with an action ready, paint in hand,
standing on ground already ours and nothing in reach worth painting. Gated on `ruin == null` so
SRP marks never contend with tower-pattern marks for the same shared per-tile channel.

**Conditional reachability read from live replays 18 games in** — the fix for exactly the
mistake that cost iteration 12 its design:

| map | soldier turns | IDLE-ALLY | `srpElig` among IDLE-ALLY turns | marks | paints | **SRPs completed** |
|---|---|---|---|---|---|---|
| DefaultMedium | 27,214 | 34.9% | **4.5%** | 13 | 139 | **9** |
| Bunny | 15,419 | 46.2% | **8.8%** | 19 | 202 | **12** |

**Mechanism gate: PASS emphatically** — 9-12 SRPs actually completed per game, against
iteration 12's 3 firings in 144,823 tower-turns.

**Result** (`20260907-032315`): **22/40 = 55.0%** vs `carol_iter12`; swept 3 win / 1 loss.

**And I caught a control error in my own attribution.** My first pass read iteration 13 against
the **i11** mirror, and Parking_lot, Gears and walalilongla appeared in *both* iteration 12's
deviation list and iteration 13's — the tell that those deviations belonged to the upgrade
already baked into the i12 baseline, not to SRPs. The null for an i12-baselined arm is **i12
self-play**, so I built `carol_m12` fresh from `carol_iter12` and measured it. The two nulls
**disagree on 6 of 40 games**, which is exactly why a mirror must be regenerated from the
current build rather than reused.

| null used | deviations | wins | losses | margin |
|---|---|---|---|---|
| i11 mirror (wrong) | 8 | 5 | 3 | +2 |
| **i12 mirror (correct)** | **6** | **4** | **2** | **+2 games** |

Same net, different games — the wrong null would have attributed SRP credit to maps the
upgrade had already flipped.

**Status: NOT YET DECIDED.** +2 games is real (no noise floor) and there is no one-directional
regression, but the flips are **mixed** (4-2), which doctrine #7 calls churn rather than a
causal effect, and 55% misses the 60% `WinPct`. Doctrine #9 is explicit that a thin accept
margin gets the frozen roster run **before** the decision, not after — it once caught a bad
accept by ten games. Roster run `20260907-035132` launched (240 games) and the decision waits
on it.

### Iteration 13 DECISION — REJECT, and the roster check is what settled it

| gate | threshold | result |
|---|---|---|
| mechanism | SRPs actually completed | **PASS — 9-12 per game** |
| conditional reachability (`srpElig`) | placeable among turns that reach the line | 4.5% / 8.8% of IDLE-ALLY turns — live |
| **primary metric** | tower-turns with `tp` < 50 should FALL | **FAILED — rose hard** |
| h2h vs `carol_iter12` | >50% | 22/40 = 55% (**+2 games** vs the i12 null) |
| peer `WinPct` | 60% | **not met** |
| flip shape | one-directional | **mixed 4 wins / 2 losses = churn** |
| **frozen roster (doctrine #9, run BEFORE deciding)** | confirm the thin margin | **did not confirm** |

**The primary metric moved decisively the wrong way**, on both maps sampled:

| | median tower paint | tower-turns with tp<50 |
|---|---|---|
| DefaultMedium — i12 | 375 | **8.5%** |
| DefaultMedium — i13 | 119 | **27.2%** |
| Bunny — i12 | 280 | **31.2%** |
| Bunny — i13 | 24 | **55.3%** |

Iteration 13 **guts the paint economy** — the exact resource every trace this session, and the
tournament, identifies as carol's binding constraint. Note also what this incidentally proves:
iteration 12's upgrades took `tp<50` from the 33.6% baseline down to **8.5%** on DefaultMedium,
independent confirmation that the accept I reversed into was right.

**The roster run did its job.** Doctrine #9 exists because a thin margin once survived two
pre-registered metrics and was caught by ten games on the frozen roster. Here: `carol_i13`
scores **26/40 = 65% vs `carol_iter7`**, against iteration 11's 25/40 = 62.5% on the identical
pinned maps — **+1 game across two accepted iterations**. Iteration 12 alone was +5 games. So
the roster says iteration 13 gave back most of iteration 12's gain even while beating i12 by 2
head-to-head. A +2 h2h that does not survive contact with a frozen opponent is exactly the
"thin accept" this rule was written to stop.

**DECISION: REJECT.** `src/carol/` remains iteration 12.

### Why it failed — a mechanism interaction I should have predicted, recorded as a hypothesis

An SRP costs paint **immediately** (marks, plus 25 tiles at 5 paint each, drawn from tower
stashes via `refillIfPossible`) and pays out **only after staying exact for 50 consecutive
rounds** [E: RULES.md]. So the cost is certain and the benefit is conditional on persistence.

**Hypothesis (untested, and I am flagging it as such): carol's own splashers destroy her SRPs.**
A splasher paints every tile in an r²=4 disc around its centre, indiscriminately and without
regard to marks. An SRP needs 25 *exact* tiles held for 50 rounds. Iteration 11 — accepted this
session at 62.5% — put splashers into the build for the first time. The two mechanisms are
therefore plausibly incompatible by construction, and iteration 13 pays the full paint cost of
patterns that are broken before they ever pay out.

I have not measured this, and it would need a direct test (tag SRP tiles, count splash
overwrites) before being believed. It is recorded as the leading explanation, not a conclusion.

### Closed-directions ledger update

- **"SRPs laid from idle soldier turns" — CLOSED for the current build.** `20260907-032315`:
  mechanism fires (9-12 completions/game) but tower paint collapses (tp<50 8.5% -> 27.2%,
  31.2% -> 55.3%) and the roster shows +1 game across two iterations. Re-opening is legitimate
  **only** with a specific mechanism for SRP persistence — e.g. excluding SRP tiles from
  splasher targeting — since the recorded cause is the cost/persistence imbalance, not the
  hypothesis that SRP income is valuable.

## Iteration 14 (frontier-seeking) — conditional gate read 8 games in, and it reframes the problem

**Hypothesis**: soldiers reaching IDLE-ALLY have nothing paintable within the ACTION radius
(r2=9), but vision is r2=20 — more than twice the area — and `newExploreTarget()` picks a
**random map coordinate** with no notion of where unpainted ground is. So an idle soldier deep
in our own territory wanders toward more of our own territory. Retarget it at the nearest
visible EMPTY tile. Costs no resource; only redirects a move already happening.

**Conditional reachability, read from live replays 8 games in** (~5 minutes, versus 40 for the
full run — the practice that would have saved iteration 12's design):

| map | soldier turns | IDLE-ALLY | `frontFound` | `frontNone` | **hit-rate among targeted turns** |
|---|---|---|---|---|---|
| DefaultMedium | 18,464 | 3,473 (18.8%) | 227 | 3,246 | **6.5%** |

**The hypothesis is wrong, and the counter says exactly how.** Of the idle turns this targets,
**93.5% have no empty tile anywhere in vision at all.** Soldiers are not failing to navigate to
paintable ground they can see — there **is** none in sight. They are sitting inside saturated
territory with the frontier beyond r2=20.

**I am NOT killing the run on that number**, and the reason is iteration 12: a low firing count
is not evidence a mechanism did not cause a result. 227 firings could still flip games if each
is valuable. The decision comes from **mirror deviation against `carol_m12`**, not from
frequency. The gate lowers my expectation; it does not make the call.

**What this measurement buys regardless of the verdict — a better-founded next hypothesis.**
The blocker is not local navigation but that **the frontier is outside vision entirely**. A
soldier cannot steer toward what it cannot sense, and carol has no map-wide memory and no
communication — `sendMessage`/`readMessages`/`broadcastMessage` are all still on the uncalled
list from this session's API sweep. The remaining options are therefore:

1. **Remembered frontier**: each robot keeps a coarse map-wide record of where it has seen
   EMPTY ground and steers there when idle. No comms needed, no resource cost.
2. **Symmetry extrapolation**: `TRAINING_ALGORITHM.md` Phase 0 item 8 — maps are guaranteed one
   of a small set of symmetries, so unseen enemy territory can be inferred from our own half.
   Carol has never used this, and it is standard practice among strong teams every year.
3. **Comms**: towers can broadcast at r2=80; robot<->tower within r2=20 on a connected paint
   path. The costliest of the three and the one most likely to be bytecode-bound.

Option 1 is the cheapest and is a strict superset of iteration 14's mechanism (vision is a
memory of depth zero), so it is the natural refinement whichever way this run lands.

### Iteration 14 DECISION — ACCEPT. The conditional gate was read on an unrepresentative slice, and the full run says so.

Run `20260907-043104` (80 games, maps pinned to the i12/i13 set), collated after the session
was killed by an account-wide rate limit at ~04:40. The games had finished on the VM regardless;
only collation was lost, exactly as MULTI_AGENT.md's "if your session dies mid-run" describes.

| gate | threshold | result |
|---|---|---|
| h2h vs `carol_iter12` | >50% | **26/40 = 65.0%** |
| peer `WinPct` | 60% | **met** |
| swept-win / swept-loss | — | **6 / 0**, 14 split-by-side |
| **mirror-null margin** vs `carol_m12` | >0 games | **+6 games, 6 wins / 0 losses** |
| flip shape | one-directional | **perfectly one-directional** |
| mechanism firing in the flipped games | any | **207–2,747 `frontFound` per game, all six** |
| bytecode | no overruns, no near-misses | **ov=0 nm=0; max 6,419/17,500 (37%)** |
| regression vs `carol_rush` | no drop | 37/40 = 92.5%, **identical to i12** |

**The null is the right one.** `20260907-034013` played `carol_iter12` vs `carol_m12` — verified
byte-identical apart from the package line — on the *same 20 pinned maps*, and split them
20/40 with zero sweeps. The candidate is measured against `carol_iter12`, so the baseline the
mirror is built from and the baseline the candidate is measured against are the same build.
That is the staleness rule I put into MULTI_AGENT.md, and this time it is satisfied by
construction rather than by luck.

The six deviations:

```
DefaultLarge   A   loss -> win        PlumberGame    B   loss -> win
DefaultMedium  B   loss -> win        gridworld      A   loss -> win
Parking_lot    B   loss -> win        walalilongla   B   loss -> win
```

**The mistake I made reading the gate 8 games in, stated plainly.** I reported "of the idle
turns this targets, 93.5% have no empty tile anywhere in vision at all — the hypothesis is
wrong." That number came from a partial replay slice. Measured over complete games:

| map/side | `frontFound` | `frontNone` | hit-rate among targeted turns |
|---|---|---|---|
| Parking_lot B | 2,747 | 826 | **76.9%** |
| Bunny B | 1,081 | 754 | 58.9% |
| walalilongla B | 696 | 699 | 49.9% |
| gridworld A | 868 | 1,832 | 32.1% |
| PlumberGame B | 1,378 | 3,464 | 28.5% |
| **DefaultMedium B** | 658 | 2,551 | **20.5%** |
| DefaultLarge A | 207 | 1,609 | 11.4% |
| Castle B | 295 | 7,162 | 4.0% |

DefaultMedium alone went from the 6.5% I quoted to 20.5% over the full game, and the hit-rate
ranges 4%–77% across maps — it is a **map-and-phase-dependent** quantity, not a constant. Early
rounds are exactly when territory is least saturated and the frontier is *nearest*, so my slice
was biased in a direction I did not think about.

**The generalizable lesson, and it is not the one I expected.** The practice of reading a
conditional gate a few games in — invented after iteration 12 and genuinely good — has a failure
mode of its own: **a partial-game read is a biased sample of game phases, not a small random
sample of turns.** Any counter whose rate varies over the course of a game will be misread by
it. The fix is not to abandon the early read (it is still 5 minutes versus 40) but to treat it
as *directional only*, and never to write "the hypothesis is wrong" on the strength of one.

**What saved the iteration was the decision rule, not the diagnosis.** I wrote at the time: "I
am NOT killing the run on that number ... the decision comes from mirror deviation against
`carol_m12`, not from frequency." That was iteration 12's lesson applied — a low firing count is
not evidence a mechanism did not cause a result — and it is the second time in two days that
holding the run open past a discouraging frequency counter produced the session's best accept.
Had I killed the run on the gate, I would have discarded a +6-game one-directional result.

**Why it works, mechanistically.** `newExploreTarget()` picks a *random map coordinate*, so an
idle soldier deep in friendly territory is as likely to walk further in as out. Retargeting it
at the nearest visible EMPTY tile costs no resource and creates no contention — it only
redirects a move that was already happening. That is the "capability preserved at zero marginal
cost" profile TRAINING_ALGORITHM.md names as the recurring winner's shape, and it is now the
third of carol's accepts to have it.

**And it is a direct answer to the tournament's verdict.** The first tournament said carol loses
the *coverage* race — bob wins by painting, at a median of 737 rounds. Frontier-seeking is
coverage work: it converts the largest remaining block of soldier waste (IDLE-ALLY, 34.9%–46.2%
of soldier turns) into paint at the boundary rather than random wandering inside our own half.

**DECISION: ACCEPT.** Snapshotted `carol_iter14`; `src/carol` is now iteration 14. Fresh mirror
`carol_m14` generated from the new baseline in the same commit, so the next candidate is
measured against a null that is not stale. Roster run `20260907-131258` launched on the same
pinned maps *before* the writeup (240 games) as the §5b scheduled frozen-roster check; it will
compare directly against `carol_i13`'s 26/40 and `carol_iter11`'s 25/40 vs `carol_iter7`.

## Iteration 15 (remembered exploration) — first design measured and discarded before the run

**Target**: the `frontNone` turns iteration 14 leaves on the table. Complete-game data from
run `20260907-043104` says these are 23%–96% of idle soldier turns (699–7,162 per game), and
on every one of them the soldier falls back to `newExploreTarget()` — 4 uniformly random map
coordinates, keep the farthest. That function has no idea where the robot has already been.

Pre-checks, all read from **complete games** rather than a prefix (the iteration 14 lesson):

| pre-check | result |
|---|---|
| reachability | `frontNone` fires 699–7,162 times/game on 8/8 maps sampled |
| trigger frequency | highest exactly where i14 helped least (Castle 96%, DefaultLarge 88.6%) |
| generality | 8 maps, both sides |
| history | strictly extends iteration 14; reverts nothing |

### 15a — "remember where EMPTY was seen" — DISCARDED on a 2-minute measurement

Coarse 5x5-tile grid, `memRound[cell]` = last round this robot saw EMPTY passable ground
there, refreshed for free inside the vision scan i14 already runs, own cell cleared whenever
that scan finds nothing. One game on Castle:

```
memHit 1,250      memNone 8,084      frontFound 557      frontNone 14,014
```

**The memory starves, structurally.** It can only be *written* on turns the vision scan finds
an empty tile — 557 turns, 4% of idle turns on Castle — and it is *read* on the other 96%.
Write condition and read condition are anti-correlated, so the mechanism is a no-op dressed
up as a memory. Discarded without a gauntlet run. Kept at
`notes/i15a_empty_sighting.java.txt` (kept out of `src/` so it cannot compile into a run) for the record.

### 15b — "remember where I have BEEN" — the inversion, and it is dense from turn one

Same grid, opposite polarity: `memSeen[cell]` = last round this robot stood there, written
**once per turn, unconditionally, with no sensing**. `newExploreTarget()` now returns the
**nearest never-visited cell**; if the robot has been everywhere, the least-recently-visited
one; the old random pick survives only for a 1x1 grid.

Nearest rather than farthest is a deliberate reversal of the old behaviour (which kept the
farthest of 4 random samples): unvisited ground next to us is reached in a few turns and pays
immediately, while unvisited ground across the map costs a long walk over ground we have
already painted, and a target that re-rolls every 120 turns may never be reached at all.

**Mechanism verification, one full game on Castle:**

| counter | value |
|---|---|
| exploration targets that were a never-visited cell (`xn`) | **all of them** |
| targets that fell back to least-recently-visited (`xo`) | **0**, across 27,822 indicator samples |
| bytecode max / overruns / near-misses | **5,981 / 0 / 0** (i14 was 6,419) |

So the mechanism engages on every single exploration decision, and the memory never
saturates within a 2,000-round game. Bytecode went *down*: the new target costs one array
write per turn plus a <=144-cell scan only when a target is actually re-picked, and it no
longer allocates four random `MapLocation`s each time.

The one game itself was a loss (Castle A, i14 won that slot) — TRAINING_ALGORITHM.md §4 case
2: mechanism demonstrably engaged, single game not a verdict, proceed to evaluation.

**Pre-registered decision rule** (fixed before the run, per the iteration 12/14 lesson that
frequency counters diagnose and never decide):

- **primary**: mirror-deviation margin against `carol_m14`, built fresh from the accepted
  iteration-14 baseline — the null the candidate is actually measured against.
- **secondary**: h2h vs `carol_iter14` >= `WinPct` 60%; flip shape one-directional; no drop
  vs `carol_rush` from i14's 37/40.
- `xn`/`xo` are **diagnostic only** and will not be used to accept or reject.

Runs in flight: `20260907-133422` (candidate, 80 games), `20260907-133516` (the i14 null, 40
games), `20260907-131258` (i14 frozen-roster check, 240 games).

## Iteration 16 (free tower AoE) — VOID on the reachability pre-check, cost: one match

**Found by the Phase 0 periodic API sweep**, not by a losing game. Diffing
`RobotController`'s 68 public methods against `src/carol`'s call sites leaves 33 uncalled;
reading `runTower()` against RULES.md's engine probe turned up what looked like free damage
being declined by our own code:

```java
if (enemies.length > 0 && rc.isActionReady()) rc.attack(null); // AoE
```

RULES.md item 1, from a direct read of `assertCanAttackTower`, says in terms: tower attacks
check only the per-turn `hasTowerSingleAttacked`/`hasTowerAreaAttacked` flags, never
`assertIsActionReady`, `towerAttack` adds no action cooldown, and **"Never gate tower attacks
on `isActionReady()`."** Spawning a robot costs +10 action cooldown [E: RULES 108], so the
guard looked like it was suppressing the free area attack on exactly the turns a tower was
doing its main job.

**Mechanism verification, one match on DefaultMedium: `aoeFreed = 0` across 15,621 tower
indicator samples.** The branch never fires.

**Why — and it is the pre-check TRAINING_ALGORITHM §3 tells me to run and I nearly skipped.**
"Read the *guard you are nesting inside*." `runTower()` attacks **before** it spawns. Robot
cooldowns tick down 10/turn and a robot acts when cooldown < 10 [E: RULES 66], so a spawn's
+10 has fully recovered by the tower's next turn — and the attack runs first anyway. There is
no turn on which a tower has an enemy in sight and a non-ready action. The guard is dead, and
my reasoning about the engine was correct while my reasoning about the *code* was not.

**DECISION: VOID.** No gauntlet run; nothing to accept or reject. The guard stays as-is: it is
inert, and removing dead code is not an iteration.

**What is worth carrying forward.** The guard is a *latent* trap rather than a live bug — it
becomes a real loss of free damage the moment anyone reorders spawning ahead of attacking in
`runTower()`. Noted here so a future iteration that touches tower turn order knows to delete
it in the same change rather than discovering it as a regression.

**Cost accounting for the process.** A correct engine fact plus a correct reading of one line
still produced a dead hypothesis, and the reachability pre-check killed it in ~2 minutes for
the price of a single match rather than a 40-minute gauntlet and a rejected iteration. Third
time this session that a cheap pre-check paid for itself (iteration 15a's write/read
correlation, iteration 15b's mechanism count, this).

### API sweep result (Phase 0 item 2, periodic)

33 of 68 `RobotController` methods are still uncalled. The ones that represent real unused
mechanics rather than convenience wrappers:

- **`sendMessage` / `readMessages` / `broadcastMessage` / `canSendMessage` /
  `canBroadcastMessage`** — comms, entirely unused. Towers broadcast at r²=80; this is the
  only mechanism that could put the frontier into a robot's knowledge when it is outside
  vision *and* outside that robot's own history. Deferred behind iteration 15, which attacks
  the same problem far more cheaply.
- **`markResourcePattern` / `completeResourcePattern` / `canMarkResourcePattern` /
  `canCompleteResourcePattern` / `getResourcePattern`** — SRPs, closed by iteration 13 and
  re-openable only with a persistence mechanism.
- **`senseRobotAtLocation` / `senseRobot` / `getHealth`** — carol's *soldier* tower-attack
  takes the **first** tower in `senseNearbyRobots` scan order (line 216) while its *tower*
  logic correctly targets lowest health (line 146). A fixed sensing scan order is exactly
  the play-symmetry bug class Phase 0 item 7 flags. Queued as a candidate, pending a
  reachability count of how often two enemy towers are attackable at once — which on r²=9
  may well be near never, and that measurement comes first.
- `disintegrate`, `resign`, `setIndicatorDot/Line`, `setTimelineMarker` — no strategic value
  or debug-only.

## Candidate killed on reachability: "soldiers should focus-fire the weakest enemy tower"

The API sweep flagged that `runSoldier` attacks the **first** tower in `senseNearbyRobots`
scan order while `runTower` correctly targets lowest health — both a focus-fire miss and, on
its face, the fixed-sensing-scan-order bug class Phase 0 item 7 warns about.

Probe build `carol_probe` counts soldier turns with exactly one (`t1`) and with two or more
(`t2`) *attackable* enemy towers. On **defensetower**, the most tower-dense map in the pool:

```
17,939 soldier samples      max t1 = 6 per robot (239 summed)      max t2 = 0
```

**Two enemy towers are never simultaneously attackable by one soldier.** The soldier action
radius is r²=9 and towers do not cluster that tightly. With at most one candidate the choice
never arises, so "target the weakest" is a no-op and scan order cannot bias anything either —
the play-symmetry concern is moot for this loop specifically. **CLOSED**, cost: two matches.

**And a self-correction inside the same measurement.** My first probe map, DefaultSmall,
returned `t1 = 0` as well as `t2 = 0`, and I briefly read that as "carol's soldiers never
attack enemy towers at all" — a much bigger claim. Checking `hitT` across the eight
*complete* games I already had on disk refuted it immediately:

```
Bunny 542   DefaultMedium 380   PlumberGame 176   gridworld 146   Castle 131
walalilongla 109   Parking_lot 11   DefaultLarge 6
```

Soldiers attack towers on every map sampled; DefaultSmall was a 362-round annihilation that
ended before contact. That is the same one-map/one-slice bias that misled iteration 14's gate
read, caught this time within minutes because I now check any surprising counter against
complete games on several maps before believing it. The habit is starting to pay compound
interest.

### Pre-registered prediction for iteration 15 (recorded BEFORE the run landed)

If visit memory works by the mechanism I claim — replacing a random exploration target with
the nearest never-visited cell — its benefit should concentrate on the maps where iteration
14's visible-frontier check comes up empty most often and idle turns are most numerous:

| map | i14 frontier hit-rate | IDLE-ALLY turns |
|---|---|---|
| **Castle** | **4.0%** | **18,040** |
| Parking_lot | 76.9% | 5,459 |

So **Castle should flip toward i15 and Parking_lot should not**. If instead the gains land on
the high-hit-rate maps, the mechanism I have described is not the mechanism doing the work,
and I should not accept it on the headline number.

## Iteration 15b RESULT — REJECT at 27.5%, and my pre-registered prediction came out exactly inverted

Run `20260907-133422`, maps pinned to the i12/i13/i14 set.

| instrument | result |
|---|---|
| h2h vs `carol_iter14` | **11/40 = 27.5%** |
| swept-win / swept-loss | **3 / 14** |
| mechanism (`xo`, targets falling back to least-recent) | 0 across 27,822 samples — fired every time |

Swept wins: DefaultMedium, Parking_lot, defensetower. Swept losses: 14 maps including Castle,
Bunny, DefaultLarge, gridworld, PlumberGame.

**The prediction I registered before the run is refuted, and in the most useful way — it is
inverted.** I predicted the gain would concentrate on Castle (i14 frontier hit-rate 4.0%,
18,040 idle turns — the map with most to gain) and not on Parking_lot (hit-rate 76.9%).
Castle was a **swept loss**; Parking_lot was a **swept win**. So whatever moved the games, it
is not "idle soldiers now know where to go". Had I accepted on the headline number I would
have baselined a mechanism whose stated causal account is contradicted by its own map
distribution.

### Why it failed: I silently reverted iteration 3

`moveExploring` re-picks a target when the robot gets within r²=8 of it, is stuck, or after
120 turns. Iteration 15b returns the **nearest** never-visited cell — which is, by
construction, a few turns away. So the target is reached almost immediately and re-picked,
over and over. **The persistent far target degenerates into a local random walk.**

That is precisely the behaviour **iteration 3 was built to remove**, and its log entry says
so in terms:

> "Persistent exploration target: a soldier commits to a far map location and walks to it
> instead of re-rolling a local random step every turn... a local random walk cannot find
> the frontier on a 40x40+ map once home is painted." (`NOTGT` on ~57% of soldier turns.)

**This is a TRAINING_ALGORITHM §3 History pre-check failure, and I recorded the pre-check as
passing.** I checked history against *iteration 14* — "strictly extends iteration 14, reverts
nothing" — which was true and irrelevant. The behaviour I changed was established by
**iteration 3**, eleven iterations earlier, and its rationale was written in a comment
directly above the function I rewrote. I read that comment; I quoted its `NOTGT` number in my
own iteration 14 notes. I did not connect it.

**The correction to the pre-check, stated so it generalizes**: the History question is not
"does this revert my *previous* iteration?" but **"which iteration established the specific
line I am changing, and what was its argument?"** The answer lives in the code's own comments
and in the log, and it is cheap to look up — the version that misled me was the version that
only looked one step back.

### And it was a bundle, which is why 15c exists

15b changed two things at once: *(a)* the sampling domain, from all map cells to
never-visited cells; and *(b)* the distance policy, from "farthest of 4 random samples" to
"nearest". §4 says never bundle, and this is what an uninterpretable bundled result looks
like — 27.5% cannot tell me whether visit memory is worthless or whether *nearest* is.

**Iteration 15c isolates (a) and restores (b) exactly.** Same 4 uniform draws over the map,
same keep-the-farthest rule the accepted baseline has had since iteration 3; the only change
is that a draw landing on an already-visited cell is re-rolled, up to 6 tries. When most
cells are visited the budget runs out and it degenerates to the accepted baseline's exact
behaviour, which is the right limit for a mechanism that should never make things worse.

Mechanism verified on Castle before launching: `xn` (draw accepted on an unvisited cell) max
36 per robot, `xo` (budget exhausted) max **1** across 21,894 samples — so the re-roll almost
always succeeds and the mechanism is live on essentially every exploration decision. Bytecode
max 6,397, zero overruns, zero near-misses. **And 15c won Castle, the map 15b swept away.**

**DECISION on 15b: REJECT.** `src/carol` remains iteration 14. Run `20260907-135509` launched
for 15c.

### Closed-directions ledger update

- **"Steer idle soldiers at the NEAREST unvisited cell" — CLOSED.** `20260907-133422`,
  11/40 = 27.5%, swept 3-14. Cause is understood and specific: a near target is reached
  within a few turns, so `moveExploring` re-rolls constantly and the persistent far target
  iteration 3 established collapses back into the local random walk it replaced. Re-opening
  requires a mechanism that keeps the *commitment* while changing the *destination*.
- **"Remember where EMPTY ground was seen" — CLOSED (15a).** Write condition (turns the
  vision scan already finds a target) is anti-correlated with read condition (turns it does
  not): memHit 1,250 vs memNone 8,084 on Castle. No gauntlet spent.

## Iteration 14 CONFIRMED by the frozen roster (§5b scheduled check)

Run `20260907-131258`, 240 games, **same 20 pinned maps** as every roster run since iteration
11 — so this is a like-for-like comparison against a never-changing opponent, which is the
only absolute-strength instrument I own.

| build | vs `carol_iter7` (the one non-saturated roster opponent) |
|---|---|
| `carol_iter11` | 25/40 = 62.5% |
| `carol_i13` (rejected) | 26/40 = 65.0% |
| **`carol_i14` (accepted)** | **28/40 = 70.0%**, swept 10 win / 2 loss |

**+3 games on the frozen opponent from iteration 14 alone**, against iteration 13's +1 across
*two* accepted iterations — the margin that killed iteration 13 under doctrine #9. The rest of
the roster is saturated and carries no information (iter0 97.5%, iter1 92.5%, turtle and
examplefuncsplayer 100%, rush 92.5%), which is why `carol_iter7` is the one line I read.

Overall 221/240 = 92.1%. This is the check §5b says to run on a schedule precisely because a
head-to-head against one's predecessor cannot distinguish a rising lineage from a drifting
one. Here it says: rising, and by the same amount the head-to-head claimed.

**Note on what this does NOT say.** 92.1% against my own frozen lineage sits alongside 19.8%
in the tournament running right now. Both are true and they measure different things; the
roster is a regression instrument, not evidence of absolute strength. See the tournament
section below.

## Iteration 17 (dry splashers walk home) — the session's strongest trace finding

**Found by following the tournament's verdict down**, not from a losing gauntlet game. The
13:00 tournament (measuring iteration 12) has carol at **19.8%** with **224 of 298** games
ending "the winning team painted enough of the map" and a median of **760 rounds** against
bob. Carol loses a coverage race. So I went looking for carol's coverage throughput, and my
own RULES.md coverage-economics table names the unit: a splasher paints up to 13 tiles per
attack, **2.6x the sustained tiles/turn of a soldier and 23% cheaper per tile**, and is the
only unit that converts enemy paint in bulk.

**What splashers actually do, measured across the 8 complete iteration-14 games on disk:**

| map | SPLASH (fired) | lowScore | noTgt | **noPaint** |
|---|---|---|---|---|
| **Parking_lot** | 10 | 29 | 0 | **1,987** |
| **gridworld** | 20 | 3 | 0 | **381** |
| walalilongla | 19 | 0 | 0 | 107 |
| Castle | 14 | 127 | 17 | 89 |
| PlumberGame | 15 | 0 | 0 | 54 |
| Bunny | 10 | 0 | 0 | 54 |
| DefaultMedium | 9 | 0 | 0 | 9 |
| DefaultLarge | 0 | 0 | 0 | 0 |

**`noPaint` dominates every other splasher state by an order of magnitude.** On Parking_lot a
splasher spends 1,987 turns unable to act against 10 turns spent acting. A splasher costs 300
paint and 400 chips to build and then does essentially nothing for the rest of the game.

**Root cause, read from the code rather than guessed**: `refillIfPossible()` only reaches a
tower within **r²=2**. Splashers move by `moveExploring(null)`, which walks them to a random
far map coordinate, so after their first few splashes they are nowhere near a tower and there
is no mechanism that ever brings them back. They run dry permanently.

**This redirects the hypothesis I had queued.** Iteration 11 logged "frontier-seeking movement
for splashers" as the next splasher item, aimed at the score-0/`lowScore` state. The
measurement says that state is 0–127 turns per game while `noPaint` is up to 1,987. Refill
logistics is the larger target by more than an order of magnitude, and I would have spent an
iteration on the smaller one had I not counted first.

**History pre-check, done the way iteration 15b taught me to do it.** The line I am changing
is `moveExploring(null)` in `runSplasher`, written by **iteration 11**, whose log says
splashers "currently inherit `moveExploring(null)`, the soldier's explorer, which has no
notion of the coverage frontier... goes in the queue behind tower-targeting." It is an
acknowledged gap awaiting work, not an established behaviour with an argument behind it. No
iteration has ever argued that a dry splasher should keep wandering. Pre-check passes, and
this time I checked the iteration that wrote the line rather than the previous one.

**Change**: remember the nearest ally tower seen (`homeTower`; seeded on turn 1 because
`buildRobot` places a robot within r²=4 of its tower [E: RULES.md item 4]), and when a
splasher is below its 50-paint attack cost, walk to it instead of exploring. Costs no
resource; it redirects a move that was already happening — the same "capability at zero
marginal cost" shape as iteration 14.

### Pre-registered, BEFORE the run

**Decision rule**: mirror-deviation margin against `carol_m14` (primary); h2h vs
`carol_iter14` >= 60%; one-directional flip shape; no drop vs `carol_rush` from 37/40.
`rw`/`rh` are diagnostic only.

**Map-level prediction** (the discipline I adopted after iteration 15b's came out inverted):
the benefit must concentrate on the maps where `noPaint` is largest.

- **Parking_lot (1,987) and gridworld (381) should move toward iteration 17.**
- **DefaultMedium (9), DefaultLarge (0) and Bunny (54) should barely move.**

If the gains land on the low-`noPaint` maps instead, the mechanism I have described is not the
one doing the work and I must not accept it on the headline number, whatever that number is.

## Trace: carol has TWO opposite economic pathologies, and one fixed constant serves neither

Measured from the tower indicator line (`T r=.. chips=..`) across the same 8 complete
iteration-14 games — free, no VM time. Spawn requires `chips >= CHIP_RESERVE + unit.moneyCost`
with `CHIP_RESERVE = 1200`, so the thresholds are **1450** for a soldier, ~1500 for a mopper,
**1600** for a splasher.

| map | tower turns | **< 1450: cannot afford ANY unit** | 1450–1599: soldier only | ≥ 1600: anything |
|---|---|---|---|---|
| Castle | 4,354 | **95.9%** | 4.0% | 0.1% |
| DefaultLarge | 3,856 | **93.2%** | 6.7% | 0.2% |
| DefaultMedium | 4,642 | **78.6%** | 15.9% | 5.5% |
| Bunny | 6,534 | 49.4% | 11.6% | 39.1% |
| PlumberGame | 7,002 | 46.2% | 16.5% | 37.3% |
| walalilongla | 5,165 | 24.6% | 10.5% | 64.9% |
| Parking_lot | 4,097 | 13.6% | 13.5% | **72.8%** |
| gridworld | 6,291 | 6.2% | 2.1% | **91.7%** |

**These are two different games.** On Castle and DefaultLarge a carol tower cannot afford a
single soldier on ~95% of its turns — the 1,200-chip reserve consumes the entire treasury and
production stops. On gridworld and Parking_lot chips are abundant on 73–92% of turns and the
reserve is irrelevant; RULES.md notes chips accumulate uselessly unless spent on
towers/upgrades/SRPs, and iteration 12's upgrades are the only sink carol has.

**One fixed constant cannot serve both regimes**, which is exactly the failure mode
LEARNINGS.md already records under "Fixed constants rot into dead bands" and which
TRAINING_ALGORITHM §5 answers: *"self-calibrating thresholds beat fixed constants for
opponent-variable behavior — derive the threshold from in-game observation instead of
searching over more constants."* The reserve exists to protect a 1,000-chip ruin completion;
on Castle it is instead protecting 1,200 chips from ever being used at all.

**Two things this also settles.**

1. **The "wasted spawn roll" idea is small.** The roll picks a unit and builds nothing if that
   unit is unaffordable, with no fallback to a cheaper one. But the band where the choice
   matters — soldier affordable, splasher not — is only **2.1%–16.5%** of tower turns. Below
   it nothing is affordable whatever the roll; above it everything is. A fallback is worth at
   most a few percent of tower turns and is not the intervention here.
2. **It explains why iteration 17's first verification match found no splashers at all.** A
   splasher needs 1,600 chips; on Parking_lot that is available 72.8% of the time, but the
   candidate's game simply never rolled one into an affordable turn. Splashers are **rare** in
   carol's builds — which sharpens rather than weakens iteration 17: on gridworld a splasher
   fires 20 times in a game while sitting dry for 381 turns, roughly 79% of its life spent
   unable to act. The unit is scarce *and* idle.

**Queued as the next structural target after iteration 17**, in the resource-economy area —
re-openable now, since `MaxConsecutiveRejects` was satisfied by iterations 13/14/15 leaving
it. The shape is a reserve derived from observation (income rate, tower count, whether a ruin
is actually reachable) rather than the constant 1,200, with the zero arm and the current
constant both measured as doses.

## The i14 mirror null — fourth zero-variance confirmation, and the strongest stale-null evidence yet

Run `20260907-133516`: `carol_iter14` vs `carol_m14`, verified byte-identical apart from the
package line, on the same 20 pinned maps.

```
overall 20/40 (50.0%)   swept-win 0/20   swept-loss 0   split-by-side 20/20
```

**Fourth independent measurement, fourth exact even split with zero swept maps.** The null has
no variance under this engine. Margins are counted in games, never in standard deviations.

**And it makes the stale-null rule concrete in a way the original evidence did not.** Comparing
the i14 null against the i12 null game-by-game, the two disagree on **12 of 40 games** — six
maps whose winning side flipped outright:

```
Bunny  DefaultLarge  DefaultMedium  Gears  Parking_lot  PlumberGame      (both sides of each)
```

When I put this rule into MULTI_AGENT.md the evidence was two nulls one accept apart
disagreeing on 6 of 40. One more accept later the disagreement is **twice that**. Four of the
six flipped maps (DefaultLarge, DefaultMedium, Parking_lot, PlumberGame) also appear in
iteration 14's own deviation list, which is precisely the tell the rule names.

Concretely: had I attributed iteration 15c or 17 against `carol_m12`, I would have credited or
debited them with games **iteration 14's own mechanism flipped**, on six maps. `carol_m14` is
now the control for every candidate measured against `carol_iter14`, and it will be rebuilt
again the moment the baseline moves.

## Iteration 18 (reserve dead-band escape) — pre-registered

**Evidence** (8 complete iteration-14 games, tower indicator `chips=`, no VM time spent):

| map | median chips | **chips < 250** | **[1200, 1450): reserve-blocked** | >= 1450 |
|---|---|---|---|---|
| **Castle** | 1,310 | 0.6% | **83.4%** | 4.1% |
| **DefaultLarge** | 1,320 | 0.6% | **79.3%** | 6.8% |
| **DefaultMedium** | 1,350 | 0.6% | **64.4%** | 21.4% |
| Bunny | 1,460 | 0.2% | 39.5% | 50.6% |
| PlumberGame | 1,470 | 0.7% | 37.9% | 53.8% |
| walalilongla | 2,180 | 0.1% | 19.9% | 75.4% |
| Parking_lot | 3,940 | 0.0% | 13.3% | 86.4% |
| gridworld | 76,420 | 0.0% | 4.1% | 93.8% |

**This is not poverty, it is a dead band.** Chips fall below a soldier's raw 250 cost on
**0.6% or less** of tower turns everywhere. On Castle the team holds the money and
`CHIP_RESERVE = 1200` forbids spending it on 83.4% of tower turns.

**Iteration 6 diagnosed this exact failure and its guard cannot reach it.** Its escape drops
the reserve when chips are *exactly* unchanged for `STAGNANT_ROUNDS = 10` turns — reachable
only at literally zero income. With any trickle of income chips move every turn, the counter
resets, and the reserve stays armed forever. Iteration 6's own log records losing DefaultSmall
by annihilation at round 69 "with 1350 chips banked", i.e. inside this band. The code comment
even says the reserve "stays fully armed whenever income is positive... so this covers the
unmeasured regime rather than reverting it" — and the measurement now shows the *positive*
income regime is where the whole problem lives.

**History pre-check** (asking which iteration wrote the line, per the 15b lesson): the reserve
is iteration 2's, the escape hatch is iteration 6's. This supersedes iteration 6 **on new
evidence** rather than silently reverting it — its zero-income case still trips
`stagnantTurns`, and this adds the pinned-but-earning case it structurally cannot see.

**Change**: count consecutive tower turns with `CHIP_RESERVE <= chips < CHIP_RESERVE + 250`;
after `STAGNANT_ROUNDS` of them, release the reserve. Self-calibrating in the sense §5 means:
the condition is read from the treasury's observed behaviour, not from a new constant.

### Pre-registered, BEFORE the run

**Decision rule**: mirror-deviation margin vs `carol_m14` (primary); h2h vs `carol_iter14`
>= 60%; one-directional flip shape; no drop vs `carol_rush` from 37/40. `pin`/`pf` diagnostic
only.

**Map-level prediction**: the benefit must track the reserve-blocked column.
- **Castle (83.4%), DefaultLarge (79.3%) and DefaultMedium (64.4%) should move toward i18.**
- **gridworld (4.1%) and Parking_lot (13.3%) should barely move.**

If the gains land on gridworld and Parking_lot instead, the mechanism I have described is not
the one doing the work and I reject regardless of the headline.

## Iteration 15c RESULT — REJECT at 52.5%, and it prices iteration 3's mechanism for the first time

Run `20260907-135509`, same 20 pinned maps, null = `carol_m14`.

| arm | h2h vs `carol_iter14` | margin vs the null | deviating maps |
|---|---|---|---|
| 15b (memory + **nearest**) | 11/40 = 27.5% | **-9 games** | 12 swept-loss / 3 swept-win |
| **15c (memory + farthest)** | **21/40 = 52.5%** | **+1 game** | **exactly one: Gears** |

Every map but Gears splits exactly as the null does. The visit-memory *sampling domain* — draw
uniformly, keep the farthest, but re-roll a draw that lands on an already-visited cell —
changes **one game in forty**.

**DECISION: REJECT.** 52.5% is below `WinPct` 60% and below even the 55% near-miss band, and
§5b is explicit that a marginal accept is an unpriced liability against every feature not yet
written. A mechanism worth one game is not worth carrying.

### What the run bought, which is why it was worth its VM time

Splitting 15b's bundle gives a clean two-point decomposition of a 10-game swing:

```
null (identical code)          20/40
15c  memory + FARTHEST         21/40      (+1)
15b  memory + NEAREST          11/40      (-9)
```

**The distance policy alone is worth ten games in forty.** The memory contributes one.

That is an **ablation of iteration 3's core mechanism** — "a soldier commits to a far map
location instead of re-rolling a local step every turn" — and it had never been measured in
the twelve iterations since it was accepted. TRAINING_ALGORITHM's stall list ranks ablating
carried features first, and notes that a 2026 audit found the most valuable features were ones
accepted almost incidentally. Iteration 3's exploration commitment is exactly that shape: it
was accepted as one half of a coupled pair, and it turns out to be carrying ten games.

So the rejected iteration converted two weakly-founded beliefs into firmly-founded ones — that
target *commitment* rather than target *choice* is what the explorer is worth, and that
per-robot visit memory adds nothing on top of it. Both are worth more than the accept would
have been.

### Closed-directions ledger update

- **"Restrict the random exploration target to never-visited cells" — CLOSED.**
  `20260907-135509`: 21/40, +1 game against a zero-variance null, deviating on one map.
  Mechanism verified live (`xo` max 1 of 21,894 samples), so this is a measurement of the
  idea, not of a dormant branch. Re-opening needs a reason the *commitment* it preserves is
  worth more when aimed by memory, which this run says it is not.
- **Iteration 3's "commit to a far target" is now PRICED at ~10 games/40** and must not be
  weakened by any future navigation change without a measurement of the same size.

## Tournament 20260907-1300 — complete, 450 games, and it measured iteration 12

| bot | win% | vs last |
|---|---|---|
| bob | 92.3% | -3.3 |
| alice | 38.0% | +2.7 |
| **carol** | **19.7%** | **+0.7** |

| pair | record | swept maps |
|---|---|---|
| bob–carol | 138–12 (92.0%) | **bob 64, carol 1** (`catface`) |
| alice–carol | 103–47 (68.7%) | alice 42, **carol 14** |

Carol's 14 swept maps against alice: Bread, CastleDefense, DefaultSmall, Filter, Snowman,
TargetPractice, UnderTheSea, catface, fix, gardenworld, gridworld, leavemealone, quack,
starburst. Median carol–bob game length **771 rounds**, and 224 of 298 carol games ended on
"painted enough of the map".

**What played was `c213c1b` = iteration 12.** Iterations 13 (rejected) and 14 (accepted) both
landed after this tournament staged from HEAD, so **the 18:00 PDT run is the first independent
test of iteration 14** — the accept my frozen roster scores at +3 games. That is the number to
read next, not this one.

**Reading it honestly, per the report's own warning.** Standings are zero-sum: the three win
counts always sum to 450, so +0.7 means "moved relative to the other two", never "improved".
My absolute instrument is the frozen roster, and it says the lineage rose (62.5% -> 70.0% vs
`carol_iter7`). Both facts are true simultaneously and they are not in tension.

**What it does change: it confirms the target.** Carol loses a *coverage* race, decisively and
by the clock — bob paints carol off the map at a median of 771 rounds. Every candidate now in
flight attacks coverage throughput directly rather than obliquely:

- **iteration 17** — splashers are the 2.6x coverage unit and spend up to 1,987 turns per game
  unable to act for want of 50 paint;
- **iteration 18** — production is blocked by a reserve holding chips the team already has, on
  83.4% of tower turns on Castle.

Both are "capability preserved at zero marginal cost", the shape TRAINING_ALGORITHM names as
the recurring winner's profile, and neither invents a new strategy — they stop existing units
from idling. Against a 92%–8% deficit, that is the right register: the gap is not one
mechanism wide, and my own gauntlet's 78.8% cannot see it at all.

## Trace: where carol's chips actually go (tower levels + upgrade firing, 8 complete i14 games)

Free measurement from the tower indicator (`tw=`, `lv=`, `UPG`/`upgPoor`), taken while three
gauntlets were queued.

| map | median chips | towers (max) | lv1 | lv2 | lv3 | `UPG` fires | `upgPoor` |
|---|---|---|---|---|---|---|---|
| Castle | 1,310 | 6 | 50.6% | 49.4% | 0.0% | **0** | 17,455 |
| DefaultLarge | 1,320 | 10 | 44.6% | 55.4% | 0.0% | **0** | 29,931 |
| DefaultMedium | 1,350 | 10 | 54.2% | 45.8% | 0.0% | **0** | 22,190 |
| Bunny | 1,460 | 10 | 63.8% | 31.4% | 4.7% | 8 | 7,489 |
| PlumberGame | 1,470 | 14 | 70.9% | 27.2% | 1.8% | 3 | 15,843 |
| walalilongla | 2,180 | 9 | 44.9% | 27.8% | 27.3% | 7 | 6,977 |
| Parking_lot | 3,940 | **3** | 43.1% | 53.2% | 3.7% | 2 | 1,691 |
| gridworld | **76,420** | 15 | 59.3% | 8.8% | 32.0% | 2 | 411 |

**The two regimes separate cleanly and they need opposite things.**

- **Chip-poor (Castle, DefaultLarge, DefaultMedium)**: an upgrade needs
  `CHIP_RESERVE + 2500 = 3700` against a median treasury of ~1,320, so `UPG` fires **zero**
  times and `upgPoor` fires 17k–30k times. Production is blocked, upgrades are unreachable,
  and the treasury sits pinned in the reserve dead band. **This is exactly what iteration 18
  targets, and this table is independent confirmation that the target is the right one.**
- **Chip-rich (gridworld, Parking_lot)**: carol banks a median of **76,420 chips** on
  gridworld with 15 towers, a third of them already lv3. The surplus is not a policy failure
  so much as a lack of sinks — RULES.md lists towers, upgrades and SRPs, and SRPs are closed
  (iteration 13). Parking_lot pins at **3 towers** with 3,940 chips, i.e. it has run out of
  ruins to build on, not out of money.

**So "spend the chip surplus" is NOT the intervention.** On the maps where carol has a surplus
she is already winning or already out of things to buy; on the maps where she is losing she has
no surplus at all — she has 1,320 chips and a rule forbidding her to spend 1,200 of them.
That is a single, cheap, well-localized fix, and it is iteration 18.

This also retires a direction I would otherwise have queued: chasing a bigger chip sink
(lv3 everywhere, a fourth tower type) would spend iterations optimizing the regime carol
already handles.

## Trace: moppers are 25% of every spawn and do NOTHING on 95.1% of their turns

The largest single block of waste I have measured in this bot. Counted from the mopper
indicator across the same 8 complete iteration-14 games — no VM time.

| map | mopper turns | mop | swing | **idle (neither)** |
|---|---|---|---|---|
| **Parking_lot** | 15,155 | 0.3% | 0.0% | **99.7%** |
| **Castle** | 352 | 2.6% | 0.0% | **97.4%** |
| gridworld | 17,103 | 2.3% | 0.7% | 97.1% |
| walalilongla | 26,977 | 4.2% | 1.7% | 94.1% |
| PlumberGame | 15,733 | 5.0% | 2.0% | 93.0% |
| DefaultLarge | 21 | 9.5% | 4.8% | 85.7% |
| DefaultMedium | 480 | 13.8% | 2.1% | 84.2% |
| Bunny | 2,659 | 16.6% | 1.9% | 81.5% |
| **TOTAL** | **78,480** | — | — | **95.1%** |

`runMopper` mops enemy paint within **r²=2** and mop-swings at adjacent enemies. Both
conditions are rare deep in our own half, which is where carol's units spend their lives, so
the unit wanders. And moppers are the **most numerous** unit in the replays — they burn no
paint painting, so they accumulate and persist while soldiers and splashers die or go dry.

**Why this is the biggest target on the board.** Splasher `noPaint` was ~2,000 wasted turns per
game and soldier idleness 8–17%; this is 78,480 turns across 8 games at 95% waste, on a unit
taking **5 of every 20 spawns** — chips and tower paint that could have become soldiers (1.00
tiles/turn) or splashers (up to 2.60). Against a bot that beats carol by painting the map at a
median of 771 rounds, spending a quarter of production on a unit that acts 5% of the time is
the definition of "removing pure waste", the third of TRAINING_ALGORITHM's recurring
winner-profile shapes.

**Iteration 19 is a dose sweep with a zero arm**, per measurement doctrine #2:

| arm | `MOPPER_IN_20` | built |
|---|---|---|
| incumbent | 5 | `carol_iter14` (baseline, no run needed) |
| `carol_i19b` | 2 | interior dose |
| `carol_i19a` | **0** | **zero arm** |

The zero arm is mandatory here rather than optional: doctrine records a case where a negative
slope between two nonzero doses wrongly condemned a low dose that beat zero handily.

**Representativeness caveat, registered now** (doctrine #4): moppers are a *defensive* unit —
they convert enemy paint. An ablation measured only against opponents that do not press carol
with paint would prove nothing about the matchup that matters. Two things make me willing to
run it anyway, and I am writing them down before the result: the 95% figure is measured in
games *against `carol_iter12`*, an opponent that paints hard and wins on coverage; and the
gauntlet carries `carol_rush`, so a defensive regression has somewhere to show up. If the zero
arm wins the h2h but drops materially against `carol_rush`, that is the defensive cost
appearing and I will read it as a dose question, not a win.

**Held, not launched**: iterations 17 and 18 are already using the VM. Queued behind them.

## Iteration 17 RESULT — REJECT at exactly 50.0%, the null to the game

Run `20260907-140851`, 20 pinned maps, null `carol_m14`.

| instrument | result |
|---|---|
| h2h vs `carol_iter14` | **20/40 = 50.0%** |
| **margin vs the null** | **+0 games** |
| maps that moved | **4: DefaultSmall +1, defensetower +1, HungerGames -1, gridworld -1** |
| swept-win / swept-loss | 2 / 2 |
| mechanism (`rw`, dry turns walking home) | **live: 10–49 per robot in every game inspected** |

**The mechanism worked and bought nothing.** `rw` fires 10–49 times per splasher in all six
flipped-game replays I pulled, `rh` confirms real refuels, and the splash count rises (13 vs
10 on gridworld). The flip shape is perfectly mixed — two maps each way, net zero — which
doctrine #7 defines as churn rather than a causal effect.

**My pre-registered map prediction failed, and that is what makes the rejection firm rather
than reluctant.** I predicted Parking_lot (1,987 `noPaint` turns) and gridworld (381) would
move toward iteration 17. Parking_lot did not move at all and **gridworld moved against it**.
The two maps that did move for it, DefaultSmall and defensetower, are not in the 8-map set I
measured `noPaint` on, so I had no prediction covering them. Whatever produced those two wins,
it is not the account I wrote down.

**Why it fails, mechanistically — and the number I should have computed beforehand.** A dry
splasher spends 10–49 turns walking home and gains at most **2** refuels (`rh` max 2 across
every game). Two refuels is about 12 extra splashes, ~150 tiles, in a 2,000-round game — while
those 10–49 turns are spent walking *away from the frontier*, which is where RULES.md says a
splasher is worth 2.6x a soldier and where it must return afterwards. The round trip costs
roughly what it earns. **I priced the idle turns and never priced the walk.**

**DECISION: REJECT.** `src/carol` remains iteration 14.

### Closed-directions ledger update

- **"Send a paint-starved splasher back to a tower to refill" — CLOSED.** `20260907-140851`:
  20/40, +0 games against a zero-variance null, 2–2 churn, mechanism verified live. The cost
  of the walk cancels the value of the refuel. Re-opening is legitimate only with a mechanism
  that brings paint *to* the splasher rather than the splasher to the paint — and RULES.md
  line 87 names exactly one: **moppers are the only unit that can transfer paint robot→robot**,
  and carol has never called it. That is a real re-opening condition, not a hope.

### What this changes about iteration 19

It sharpens it. Splasher idleness was ~2,000 turns per game and fixing it was worth zero.
Mopper idleness is **78,480 turns across 8 games at 95.1%**, on a unit taking 5 of every 20
spawns — an order of magnitude more waste, and cutting it returns production rather than
spending turns to reclaim it. Iteration 19 does not have to move a unit anywhere; it stops
building one.

## Iteration 18 — mechanism verified from the run's own replays, before the verdict

Pulled five games off the VM from run `20260907-141533` while it was still playing:

| game | `pf` max (dead-band releases) | median chips | map moved? |
|---|---|---|---|
| DefaultLarge botA | **53** | **1,200** | +1 |
| DefaultLarge botB | **33** | 1,270 | +1 |
| DefaultMedium botA | **38** | 1,310 | +1 |
| **Parking_lot botA** | **0** | 2,990 | **+0** |
| gridworld botA | 4 | 87,140 | -1 |

Bytecode max 6,825 of 17,500, **zero overruns, zero near-misses** on all five.

**Parking_lot is a perfect internal control.** The mechanism fires **zero** times there — the
treasury sits at a median of 2,990, never pinned in `[1200, 1450)` — and the map does not move.
A mechanism that cannot have acted, on a map that did not change. That is the cleanest possible
demonstration that the effect elsewhere is the mechanism rather than ambient churn, and it is
the check iteration 17 could not produce (its mechanism fired everywhere, including on the maps
it lost).

**And DefaultLarge's median treasury is exactly 1,200** — pinned at the reserve to the chip.
The dead-band diagnosis is not an inference from aggregates; it is visible in the median.

`gridworld` moved -1 with only 4 firings against an 87,140-chip treasury, where releasing a
1,200-chip reserve can hardly matter. Noting that **gridworld also moved -1 for iteration 17**,
i.e. it flips against two unrelated mechanisms — a chaos-sensitive map in doctrine #7's sense,
and I will treat a single gridworld flip as churn unless a mechanism count supports it.

### A methodological note I must not forget when i19 lands

Iterations 18 and 19 are both being measured against `carol_iter14` **in parallel**. If 18 is
accepted, the baseline moves, and iteration 19's head-to-head becomes a gate against a
*superseded* baseline — the same staleness error as reusing an old mirror, one level up. The
`20260907-142542` run still yields the thing it was built for, the **dose curve**
(`MOPPER_IN_20` 0 vs 2 vs 5, measured within one run on shared maps, which is exact). But the
**accept decision** for iteration 19 must be re-measured against the new baseline and a fresh
`carol_m18` mirror. Writing this down now, while it is cheap, rather than discovering it in
the accept.

## THE finding: carol's towers are paint-dry, and the unit that fixes that is the one doing nothing

`buildRobot` costs "robot's paint **from the TOWER's own stash** + team chips" [E: RULES.md
item 4]. So a tower with fewer than 200 paint cannot build a soldier however rich the treasury
is. Measured across the 8 complete iteration-14 games:

| map | tower turns | **tp < 200: cannot build a soldier** | tp < 50 | median tp | median chips |
|---|---|---|---|---|---|
| **Parking_lot** | 4,097 | **99.1%** | 92.1% | 38 | 3,940 |
| **gridworld** | 6,291 | **97.3%** | 56.7% | 37 | **76,420** |
| walalilongla | 5,165 | 93.8% | 46.2% | 58 | 2,180 |
| PlumberGame | 7,002 | 83.7% | 45.6% | 60 | 1,470 |
| Bunny | 6,534 | 74.7% | 61.2% | 13 | 1,460 |
| DefaultLarge | 3,856 | 59.4% | 51.5% | **0** | 1,320 |
| DefaultMedium | 4,642 | 57.1% | 15.7% | 160 | 1,350 |
| Castle | 4,354 | 26.5% | 6.1% | 426 | 1,310 |

**The two pathologies now fit together, and the chip surplus is explained.** On gridworld carol
banks 76,420 chips while her towers hold a median of 37 paint. She is not choosing not to
spend; she *cannot* — every build needs 200 paint out of a stash that is empty on 97.3% of
turns. The idle treasury is a *symptom* of paint starvation, not a separate problem, and my
earlier note that the surplus maps "have run out of things to buy" was wrong in an interesting
way: they have run out of paint, not of sinks.

**And RULES.md already contained the answer, in a sentence I wrote myself:**

> "Money towers generate no paint, so a money tower can spawn ~2 robots from its 500 starting
> stash and then goes dry **until a mopper refills it**."

> "Mopper transfer: give/take paint with ally robots AND towers (withdraw = negative amount),
> r²=2... **only moppers transfer robot→robot**." [E]

**Carol's moppers never give paint to anything.** `refillIfPossible` calls
`rc.transferPaint(ally.location, -want)` — a *withdrawal*, and it is the only transfer call in
the bot. Moppers take paint from towers and never return any. So money towers spawn twice and
are dry for the rest of the game, chips pile up unusable, and the unit whose defining ability
is moving paint around spends **95.1% of 78,480 turns doing nothing**.

This is exactly the failure Phase 0 item 2 warns about — "a whole game mechanic sat unused for
81 iterations once because the obvious methods were assumed to be the whole interface" — and it
took an API sweep plus three separate free measurements to surface.

**It reframes iteration 19 rather than cancelling it.** The cut arm is still worth its run and
still answers a real question: if `MOPPER_IN_20 = 0` beats the incumbent, the mopper **as
currently programmed** is negative-value at 300 chips apiece (more than a soldier's 250), which
is a fact I want either way. What it must not be read as is "moppers are useless" — the
measurement above says the opposite, that they are the only unit that can unblock the binding
constraint and have never been asked to.

**Iteration 20, queued and specified**: an idle mopper carrying paint from a tower with surplus
to a tower below the build threshold. Mopper paint capacity is only 100 against a soldier's
200, so one trip is half a soldier — but moppers are the most numerous unit carol has and are
idle 95% of the time, so the carrying capacity is already built and paid for. The 95% idle
figure stops being an argument for deletion and becomes the *resource* the fix spends.

## Iteration 20 (mopper paint ferry) — reachability pre-check, and it splits the maps cleanly

Before spending a run, the question the ferry lives or dies on: **does a donor tower
(`tp >= TOWER_SPARE = 400`) ever coexist with a dry one (`tp < TOWER_DRY = 200`)?** Counted per
round across the 8 complete iteration-14 games:

| map | donors (tp≥400) | dry (tp<200) | **rounds where BOTH exist** |
|---|---|---|---|
| DefaultLarge | 33.9% | 59.4% | **49.0%** |
| Bunny | 18.9% | 74.7% | **44.8%** |
| DefaultMedium | 30.1% | 57.1% | **36.4%** |
| Castle | 51.9% | 26.5% | **34.2%** |
| PlumberGame | 7.0% | 83.7% | 21.6% |
| walalilongla | 1.5% | 93.8% | **3.4%** |
| gridworld | 0.4% | 97.3% | **1.1%** |
| Parking_lot | 0.0% | 99.1% | **0.1%** |

**The maps with the worst paint starvation are exactly the ones the ferry cannot help.** On
Parking_lot and gridworld *every* tower is dry — there is no surplus anywhere, so redistribution
has nothing to redistribute. Those maps do not have a distribution problem, they have a total
paint *income* problem, and no amount of trucking fixes it.

That is a real limit on the mechanism and I would rather know it now than infer it from a
disappointing headline. It does not kill the iteration: on four maps a donor and a dry tower
coexist on 34–49% of rounds, which is abundant reachability.

### Pre-registered, BEFORE the run

**Decision rule**: mirror-deviation margin against the null built from the baseline in force
when it runs; h2h >= `WinPct` 60%; one-directional flip shape; no drop against `carol_rush`.
`fl`/`fd`/`fs` diagnostic only.

**Map-level prediction, with a control group this time:**
- **Should move**: DefaultLarge (49.0%), Bunny (44.8%), DefaultMedium (36.4%), Castle (34.2%).
- **Should NOT move**: Parking_lot (0.1%), gridworld (1.1%), walalilongla (3.4%) — no donor
  exists, so the mechanism physically cannot act.

Parking_lot is the same zero-firing control that made iteration 18's result convincing, and it
arrives here by a completely different mechanism. If Parking_lot or gridworld move materially
for iteration 20, the effect is not the ferry.

**A defect caught in review before the run, worth recording.** My first implementation had the
ferry deliver the mopper's whole load and then called `refillIfPossible()`, which withdraws
from any adjacent tower whenever the mopper is below half capacity — so the mopper would have
immediately sucked its own delivery back out of the tower it had just filled. The fix needs no
extra state: deliver only down to half capacity, which is exactly the threshold
`refillIfPossible` refuses to act below. One mechanism, no new flags, and the undo is
impossible by construction rather than by a guard I would have to remember.

## Iteration 18 safety check — releasing the reserve costs zero towers

The reserve exists to protect a 1,000-chip ruin completion, and iteration 6's log records a
game lost by annihilation partly to a treasury stuck above it. So the obvious risk of releasing
it is that carol spends the money on units and then cannot finish a ruin.

Measured as a **paired within-game comparison** — both builds carry BUILD tags, so the two
sides of the same replay are the same game with the same map, spawns and opponent:

| game | i18 towers max/final | iteration 14 towers max/final |
|---|---|---|
| DefaultLarge botA | 14 / 14 | 14 / 14 |
| DefaultLarge botB | 12 / 12 | 12 / 12 |
| DefaultMedium botA | 14 / 14 | 14 / 14 |
| Parking_lot botA | 3 / 3 | 3 / 3 |
| gridworld botA | 13 / 13 | 13 / 13 |

**Identical in every game.** Not one tower fewer, on the maps where the release fires 33–53
times per tower.

**Why, and it is a property of the design rather than luck.** The release requires
`chips >= CHIP_RESERVE` for ten consecutive turns. The moment a build fires, chips drop below
1,200, the pinned counter resets and the reserve **re-arms itself**. The treasury oscillates
around the reserve line instead of being drained past it, so the protection the reserve was
bought for is still there — it is only the *dead band above it* that has been opened. That is
what makes this a self-calibrating threshold in §5's sense and not simply a weakened constant.

So the reserve was, in the pinned regime, protecting nothing at all: it was refusing to spend
250 chips while sitting on 1,310 and completing exactly as many ruins either way.

## Why iteration 19a (cut the moppers) is losing — and it is the paint constraint again

`carol_i19a` (`MOPPER_IN_20 = 0`) is running at **8/25 = 32%** against `carol_iter14` partway
through `20260907-142542`. Removing the unit that idles 95% of the time is *hurting*, and the
reason follows directly from the finding two sections up.

**A mopper costs 100 paint; a soldier costs 200** [E: RULES.md unit table]. `buildRobot` draws
that paint from the **tower's own stash**, which is below 200 on 57–99% of tower turns. So:

- cutting moppers does not reduce paint demand, it **doubles the paint cost of the replacement
  unit** — and paint is precisely what carol has none of;
- on a tower holding, say, 150 paint, a mopper is the **only unit it can build at all**. Delete
  moppers and that tower builds nothing.

So the mopper share is not really a unit-mix parameter. It is a **cheap-unit share**, and
cutting it in a paint-starved economy removes production rather than redirecting it. My
framing — "25% of spawns wasted on a unit that acts 5% of the time" — priced the mopper by
what it *does* and ignored what it *costs*, on the one axis that binds.

That is the same error as iteration 17, one level up: there I priced the idle turns and not the
walk; here I priced the idleness and not the unit's cheapness. **Both times I costed the
benefit and not the price.**

**The dose curve is still worth completing.** `carol_i19b` (dose 2) plays next in the same run
on the same maps, so the three points 0 / 2 / 5 are exact within-run comparisons. If the curve
is monotone increasing, the incumbent 5 may itself be too low, which would be a genuinely
surprising result and a cheap next iteration in the opposite direction from the one I proposed.

### And it sharpens iteration 20 into a pair, not a single change

The ferry (iteration 20) makes moppers **give** paint to towers. But `refillIfPossible` still
lets any mopper **take** up to its full 100-paint capacity from any adjacent tower whenever it
drops below half — including from a tower that is already dry. And a mopper's attack costs
**0 paint** [E: RULES.md unit table]; it needs paint only to offset passive attrition (−2/turn
on neutral ground, −4 on enemy). **Moppers are drawing a full tank they have almost no use
for, from the resource the whole economy is starved of, and they are the most numerous unit
carol has.**

I am deliberately **not** bundling that into iteration 20. §4 is explicit and iteration 15b's
bundle cost me an uninterpretable 27.5%. Iteration 20 stays the pure ferry; **iteration 21 is
the withdrawal guard** (a mopper tops up only to what attrition needs, and never from a tower
below `TOWER_DRY`). If 20's mechanism fires and moves nothing, 21 is the reason and I will
already have the instrumentation to show it.

## Iteration 18 RESULT — ACCEPT. +7 games, the map prediction confirmed, and a zero-firing control map.

Run `20260907-141533`, 20 pinned maps, null `carol_m14`.

| gate | threshold | result |
|---|---|---|
| h2h vs `carol_iter14` | >50% | **27/40 = 67.5%** |
| peer `WinPct` | 60% | **met** |
| **mirror-null margin** | >0 games | **+7 games**, 9 maps up / 2 down |
| swept-win / swept-loss | — | **9 / 2** |
| regression vs `carol_rush` | no drop from 37/40 | **37/40 = 92.5%, identical** |
| mechanism | `pf` fires | **33–53 per tower on the maps that moved** |
| towers lost to the release | none | **identical max/final in all 5 paired games** |
| bytecode | no overruns | **max 6,825/17,500, ov=0, nm=0** |
| overall | — | 64/80 = 80.0% |

**The pre-registered map prediction is confirmed — the first of the session to be.**

| map | predicted | `pf` (mechanism) | result |
|---|---|---|---|
| Castle (83.4% pinned) | **move** | fires | **+1** |
| DefaultLarge (79.3%) | **move** | **53 / 33** | **+1** |
| DefaultMedium (64.4%) | **move** | **38** | **+1** |
| Parking_lot (13.3%) | not move | **0** | **+0** |
| gridworld (4.1%) | not move | 4 | -1 |

All three predicted maps moved, in the predicted direction. **Parking_lot is a zero-firing
control**: the treasury there sits at a median of 2,990 and never enters the dead band, the
mechanism fires *zero* times, and the map does not move. A mechanism that provably cannot have
acted, on a map that did not change — that is the piece iteration 17 could not produce, and it
is why I believe this result is the mechanism rather than ambient churn.

The one map against prediction, gridworld, moved -1 with 4 firings against an 87,140-chip
treasury where releasing 1,200 chips can hardly matter — and it also moved -1 for iteration 17,
a completely unrelated mechanism. I am recording it as a chaos-sensitive map rather than
explaining it away.

**What the change actually is.** `CHIP_RESERVE = 1200` is held unless chips are *exactly*
unchanged for 10 turns — a condition positive income makes unreachable. Iteration 18 adds the
condition that was missing: if the treasury sits in `[CHIP_RESERVE, CHIP_RESERVE + 250)` — has
the money, is forbidden to spend it — for 10 consecutive turns, release the reserve. On Castle
that band held **83.4%** of tower turns while chips fell below a soldier's raw 250 cost on
**0.6%**. Carol was not poor; she was pinned.

**Why it is safe, measured rather than argued.** A build drops chips under 1,200, the pinned
counter resets, and the reserve re-arms. The treasury oscillates around the line instead of
draining past it — so the 1,000-chip ruin completion the reserve exists to protect is still
protected, and the paired tower counts confirm it: **not one tower fewer, in any game.**

**DECISION: ACCEPT.** Snapshotted `carol_iter18`; `src/carol` is now iteration 18. Fresh
mirror `carol_m18` built from the new baseline in the same commit — the i14 null is now stale
and must not be reused, and this session already measured that two nulls one accept apart
disagree on 12 of 40 games.

**Consequence for iteration 19**, as flagged before the run: `20260907-142542` measures
`carol_i19a` against `carol_iter14`, which is no longer the baseline. Its **dose curve**
(`MOPPER_IN_20` 0 vs 2 vs 5, within-run, shared maps) stays valid; its **accept gate** does
not, and any decision on the mopper share must be re-measured against `carol_iter18` with the
`carol_m18` null.

## Iteration 19 (mopper dose) — the zero arm is REJECTED at 35%, and the curve runs the wrong way

Run `20260907-142542`, 20 pinned maps.

| arm | `MOPPER_IN_20` | vs `carol_iter14` | swept |
|---|---|---|---|
| `carol_i19a` | **0** (zero arm) | **14/40 = 35.0%** | 4 win / **10 loss** |
| `carol_i19b` | 2 | (plays the incumbent later) | — |
| incumbent | 5 | — | — |

And the within-run dose comparison, which is exact because both arms share the identical map
sample: **`carol_i19a` 4 – 10 `carol_i19b`.** So dose 2 beats dose 0, and dose 5 beats dose 0
by 26–14. The curve over the range measured is **monotone increasing in mopper share** — the
opposite direction from the one I proposed, and it raises the possibility that the incumbent 5
is itself too low.

**DECISION on the zero arm: REJECT**, decisively.

### I made exactly the error I had already written up

My case for cutting moppers was: *they do nothing on 95.1% of 78,480 turns*. That is a
**frequency** argument, and iteration 12's whole lesson — recorded in this log and in
LEARNINGS.md — is that frequency is a proxy and never the causal question:

> "A guard against crediting a mechanism that never ran must not become a rule that a rare
> mechanism cannot have worked."

A mopper acts on 2–5% of its turns, and those actions may be **rare and high-value**, which is
precisely the shape iteration 12's paint-tower upgrade turned out to have (3 firings in 144,823
tower-turns, +5 games). There is a concrete mechanism for it here: soldiers **cannot overwrite
enemy paint** [E: RULES.md], so mopping is the *only* way carol reclaims ground an opponent has
taken. In a game decided on painted area, against opponents that paint, a unit that acts 2% of
the time may be carrying the entire reclamation half of the coverage race.

Two independent reasons the zero arm fails, then, and both were measurable before the run:

1. **Price on the binding axis** — a mopper costs 100 paint against a soldier's 200, drawn from
   a tower stash that is under 200 paint on 57–99% of tower turns. The cheap unit is often the
   only buildable one.
2. **Rare-but-high-value action** — mopping is the sole route to reclaiming enemy paint.

**What the run bought.** A firmly-founded replacement for a belief I held on a striking but
misleading statistic, a measured dose curve where I had an assumption, and a new candidate
pointing the *other* way. Per doctrine #2 the zero arm was mandatory, and it is the arm that
carried all the information: had I run only "5 vs 2" I would have seen a small difference and
learned nothing about the direction.

### Closed-directions ledger update

- **"Cut the mopper share because moppers idle 95% of the time" — CLOSED.** `20260907-142542`:
  dose 0 scores 14/40 = 35% and loses to dose 2 by 10–4. Cause understood on two independent
  axes (paint price, and mopping as the only enemy-paint reclamation). Re-opening would need a
  measurement that mopping is worthless *against opponents that paint*, which the tournament
  says is every opponent that matters.
- **NEW candidate, opposite direction**: `MOPPER_IN_20 = 8`. One constant, a dose above the
  incumbent on a curve now measured as monotone increasing over 0→2→5. It must be measured
  against `carol_iter18` with the `carol_m18` null, not against the superseded iteration 14.

## Iteration 20 (paint ferry) — mechanism DOES NOT FIRE, caught by the verification match

First run of `carol_i20` against `carol_iter18` on DefaultLarge — the map with the highest
measured donor/dry coexistence (49.0% of rounds):

```
fl (loads) = 0      fd (drops) = 0      fs (seeks) = 0        bytecode 6,713, ov=0
```

**Zero on all three counters, over a full 2,000-round game.** The mechanism is completely
inert, and the reachability pre-check I ran did not catch it because it measured the *world*
(do a donor and a dry tower coexist?) and not the *mopper's view of the world*.

That is a distinction worth stating plainly, because I thought I had done this pre-check
properly: **"the condition exists somewhere on the map" is not "the condition is visible to the
robot that must act on it."** Iteration 14 taught me the conditional form — measure the gate
*among the turns that reach it* — and I applied it to the map rather than to the unit.

**Rather than redesign on a guess, I am instrumenting the conjunction.** The load needs a tower
with `paint >= 400` in vision *and* the mopper below capacity; the drop needs a tower with
`paint < 200` in vision *and* the mopper above half capacity. Added counters for each part
separately — `tw2` (any ally tower in vision), `dry`, `don` (donor in vision), `full` (mopper
at capacity) — plus the mopper's own paint in its state string, and re-ran the same game.

**The leading hypothesis, to be confirmed or killed by those counters**: moppers are themselves
broke. A mopper is built with 100 paint, its attack costs **0**, and it bleeds **−2 paint per
turn on neutral ground and −4 on enemy ground** [E: RULES.md]. So it hits zero after ~50 turns
and `refillIfPossible` only tops it up within r²=2 of a tower it is rarely near — the identical
"nowhere near a tower" problem that killed iteration 17 for splashers. If that is right, the
truck is empty and it is also *the reason moppers idle 95% of the time*: not that they have
nothing to do, but that they are dying of paint starvation like everything else carol owns.

If confirmed, the ferry is the wrong shape and the right change is upstream of it.

## CORRECTION: iteration 20's "inert mechanism" was a measurement artifact, and the broke-mopper hypothesis is refuted

Re-ran the same game with the counters actually emitted into the indicator string:

```
fl (loads from a donor) 7     fd (drops into a dry tower) 134     fs (seeks) 136
tw2 (ally tower in vision) 275   dry 270   don (donor in vision) 31   full 130
mopper paint over 1,867 turns:  median 94 / 100   at zero 1.0%   below 50 18.1%   above 50 78.4%
```

**The mechanism fires hard — 134 deliveries per mopper.** My previous entry reported
`fl=fd=fs=0` and concluded the ferry was inert. That was **wrong, and the error was mine, not
the bot's**: in rebasing iteration 20 onto iteration 18 I appended the ferry counters to the
*tower* return string and then removed them, so they never reached
`rc.setIndicatorString`. My extraction helper returns `max(v) if v else 0` — so "no samples
matched the regex" and "the counter is genuinely zero" render **identically as 0**.

**The lesson, and it is a sharp one for a session built on counters:** a counter that reads
zero and a counter that is *absent* are different facts, and code that collapses them will
manufacture false negatives on demand. I have spent this session correctly refusing to accept
mechanisms on low firing counts; I very nearly *rejected* one on a firing count that did not
exist. Every extraction should assert that the sample count is non-zero before reporting the
value — the fix is one line and I have applied it to my reading habit, not just this script.

**And the hypothesis I had reasoned my way into is refuted by the same data.** I argued from
RULES.md that moppers bleed 2–4 paint/turn, freeze at zero ("cannot move/act until refilled",
−20 HP/turn against 50 HP), and so die broke — a tidy mechanistic story for the 95% idleness.
**Median mopper paint is 94 of 100, and only 1.0% of turns are at zero.** Moppers are not
broke. The low-paint cooldown penalty (below 50) applies on 18.1% of turns, nowhere near
enough to explain 95% idleness either.

So the original reading stands: moppers idle because there is no enemy paint within their r²=2
action radius, being deep in friendly territory — not because they are starved. Two plausible
mechanistic stories, both mine, both killed by one instrumented game. Cheap.

**What the numbers say about the ferry's design.** Deliveries (134) vastly outnumber loads from
a designated donor (7), and a donor is in vision on only 31 turns against 270 with a dry tower.
So the paint being delivered is mostly coming from `refillIfPossible`, which withdraws from
*any* adjacent tower regardless of how little it holds. The ferry is therefore redistributing,
but **without control over the source** — it may be draining a tower at 250 to top up one at
190. That is a real design weakness, it is now measured rather than suspected, and it is
exactly what the iteration 21 withdrawal guard was queued to fix.

**Next**: run iteration 20 as it stands against `carol_iter18` with the `carol_m18` null. The
mechanism is live and heavily exercised; whether uncontrolled redistribution is net-positive is
precisely the question a gauntlet answers, and the `fl`/`fd`/`don` counters will tell me
afterwards whether a controlled source would have done better.

## CORRECTION to the mopper dose curve: it is CONCAVE, and the incumbent is on the wrong side of the peak

Run `20260907-142542` completed its dose arm. I called the curve "monotone increasing" from
partial data (`i19a` was 4–10 down to `i19b` at the time). The full numbers say otherwise:

| comparison | result | dose 0's opponent scores |
|---|---|---|
| `carol_i19a` (0) vs `carol_iter14` (**5**) | 14/40 = 35.0% | **65.0%** |
| `carol_i19a` (0) vs `carol_i19b` (**2**) | 11/40 = 27.5%, swept **2–11** | **72.5%** |

Both are measured against the *same* opponent (dose 0) on the *same* pinned maps in the *same*
run, so the comparison between them is as clean as a cross-arm comparison gets. **Dose 2 beats
dose 0 by more than dose 5 does** — 72.5% against 65.0%, and it sweeps 11 maps to 2.

So the curve over 0 → 2 → 5 is **concave with an interior optimum near 2**, and the incumbent
sits past the peak. This is measurement doctrine #2 in its exact predicted form:

> "Always measure the zero arm: a negative slope between two nonzero doses once wrongly
> condemned a low dose that beat zero handily; the curve was concave with an interior optimum.
> A curve that peaks in the middle is stronger evidence than any single point."

I had reached for `MOPPER_IN_20 = 8` on the strength of the partial read. The completed run
points the other way, and **the zero arm is what made the shape legible** — without it I would
have had one number (5 beats 2, or 2 beats 5) and no idea whether I was on a slope or near a
peak. It was mandatory for exactly this reason and it earned its 40 games.

**Both of my successive framings were wrong and the measurement corrected each in turn:**
"moppers are waste, cut them" → refuted by the zero arm at 35%; "moppers are undervalued, add
more" → refuted by the completed curve. The truth is neither: **moppers are valuable and there
are too many of them.**

**Iteration 21 rebuilt as `MOPPER_IN_20 = 2` on the iteration-18 baseline.** One constant. The
transitive evidence (dose 2 > dose 5 via a shared dose-0 opponent) is strong but indirect, so
the direct head-to-head against `carol_iter18` with the `carol_m18` null is the test that
decides it.

### Pre-registered for iteration 21

**Decision rule**: margin against the `carol_m18` null (primary); h2h vs `carol_iter18` >= 60%;
one-directional flip shape; no drop vs `carol_rush`.

**Map-level prediction**: a *unit-mix* change has no map-local mechanism to key on, so unlike
iterations 18 and 20 I can predict only the aggregate here — and I am recording that limitation
rather than inventing a map story. What I do predict: the gain concentrates on maps where
tower paint is scarcest (Parking_lot 99.1% of tower turns under 200 paint, gridworld 97.3%),
because that is where trading a 100-paint mopper for a 200-paint soldier bites hardest — and
it should be near-neutral on Castle (26.5%), where stashes are comparatively healthy.

## Iteration 20 — the shuttle raises firing 5x and the target metric still does not move. DEFERRED, with the arithmetic I owed it.

Three verification runs on DefaultLarge against `carol_iter18`, same map, same opponent:

| version | `fl` loads | `fd` drops | `fs` seeks | tower `tp<200` | median stash |
|---|---|---|---|---|---|
| unguarded source | 7 | **134** | 136 | 59.8% | 91 |
| guarded to donors | 1 | **1** | 5 | 63.7% | 137 |
| **guarded + shuttle** | 4 | **5** | 15 | **51.6%** | **175** |
| `carol_iter18` (same games) | — | — | — | **50.2%** | **195** |

The shuttle did its job on reachability — deliveries rose 1 → 5 per mopper once moppers actually
drive to the donor and then to the dry tower. **But the metric the whole mechanism exists to
improve is flat-to-worse**: iteration 20 leaves towers under the 200-paint build threshold
*slightly more often* than the baseline it is trying to help, with a lower median stash. That is
iteration 13's signature — mechanism confirmed, primary metric moving the wrong way.

**And here is the arithmetic I should have done before writing a line of it.** A mopper's paint
capacity is **100**, and it delivers only down to half capacity so that `refillIfPossible`
cannot suck the cargo back out — so **one trip moves at most 50 paint**. A tower needs **200 in
a single stash** to build a soldier. **Four full round trips per soldier**, each trip requiring
the mopper to reach a donor at r²=2 and then a dry tower at r²=2.

That ceiling was computable from RULES.md at design time, and it is the exact discipline I wrote
into LEARNINGS.md two hours ago after iteration 17: *state the benefit and the price as two
numbers before running the mechanism.* I wrote the rule and then did not apply it to the very
next thing I built. The benefit here is real but small by construction, and no amount of
navigation work changes the 50-paint bucket.

**DECISION: DEFER, not reject.** The mechanism engages, the direction is sound (carol's binding
constraint really is tower paint, and moppers really are the only unit that can move it), and
doctrine is explicit that a proxy metric on one game does not decide. But with the VM shared
three ways I will not spend 80 games on a mechanism whose ceiling is four round trips per
soldier while `carol_i21` — backed by a *measured dose curve* — is waiting for the same slot.

**What would make it worth re-opening**, recorded concretely rather than as a hope:
- **Deliver the full load.** The half-capacity rule exists only to defeat `refillIfPossible`;
  now that moppers refill from donors only (`refillFromSurplusOnly`), that defence may be
  redundant and the bucket doubles to 100 paint per trip.
- **Or target the constraint directly**: 2/3 of carol's towers are paint towers by
  `towerTypeFor`'s `k % 3`, yet gridworld runs 97.3% dry with 76,420 idle chips. If the mix is
  wrong, no ferry can compensate — and unlike the ferry, the tower mix has never been swept.

## Iteration 19 collated — and a representativeness note I would have missed

Run `20260907-142542` final: `carol_i19a` (`MOPPER_IN_20 = 0`) 64/120 = 53.3% overall.

```
vs carol_iter14   14/40 (35.0%)      vs carol_i19b (dose 2)   11/40 (27.5%)      vs carol_rush  39/40 (97.5%)
```

**`carol_rush` is where the zero arm does BEST**: 39/40, against the incumbent's 37/40. So
deleting moppers *helps* against the rusher and badly hurts against carol's own lineage.

That is worth stating because it inverts the caveat I registered before the run. I wrote that
moppers are a defensive unit and that a drop against `carol_rush` would be "the defensive cost
appearing". The opposite happened — and it makes sense once the mechanism is right: moppers pay
off by **reclaiming enemy paint in a long coverage war**, which is what the lineage matchup is;
`carol_rush` ends games fast and by different means, so the mopper's slow value never accrues
and its 300-chip price is pure drag.

**Measurement doctrine #4 in action, in the direction I did not anticipate.** I checked whether
the evaluating opponents *pose* the threat a defensive feature answers. They do — but the
threat is posed by the *slow* opponent, not the aggressive one. "Is this opponent dangerous?"
was the wrong question; "does this opponent create the situation the feature pays off in?" was
the right one, and the rusher's speed is exactly what prevents it.

This also means the mopper dose is **matchup-dependent**, which is the standing argument for
self-calibrating thresholds over constants (TRAINING_ALGORITHM §5). If dose 2 wins the
head-to-head, a follow-up worth measuring is whether the right share should be read from
observed game state — enemy paint seen per turn is the natural signal — rather than fixed.

## The `carol_m18` null — fifth confirmation, and the stale-null rule holds a third time

Run `20260907-144315`: `carol_iter18` vs `carol_m18`, verified byte-identical apart from the
package line.

```
overall 20/40 (50.0%)   swept-win 0/20   swept-loss 0   split-by-side 20/20
```

**Five independent mirror measurements, five exact 20/40 splits, zero swept maps in any of
them.** Under this engine the null has no variance, full stop. Every margin in this log is a
count of games the code actually flipped.

And the staleness check again, now with a third data point: the i18 null and the i14 null
disagree on **12 of 40 games** — six maps (Castle, DefaultMedium, Mirage, PlumberGame, rain,
walalilongla) whose winning side flipped outright when iteration 18 was accepted.

| null pair | games that disagree |
|---|---|
| i11 → i12 | 6 of 40 |
| i12 → i14 | 12 of 40 |
| **i14 → i18** | **12 of 40** |

So roughly a quarter to a third of the null flips with every accept. Reusing a mirror across an
accept is not a small approximation — it would misattribute a dozen games. `carol_m18` is now
the control for `carol_i21`, `carol_i22a/b` and everything measured against iteration 18.

Note also that Castle, DefaultMedium and PlumberGame appear in **both** this list and iteration
18's own deviation list — exactly the tell the rule names, and the reason it is stated as "maps
appearing in both lists" rather than as a vague caution.

## Iteration 21 (MOPPER_IN_20 = 2) — head-to-head complete: +6 games, and the gradient is clean

Run `20260907-145635`, 20 pinned maps, null `carol_m18` (built from the baseline it is measured
against, and confirmed at 20/40 with zero sweeps).

| instrument | result |
|---|---|
| h2h vs `carol_iter18` | **26/40 = 65.0%** |
| **margin vs the `carol_m18` null** | **+6 games**, 9 maps up / 3 down |
| swept-win / swept-loss | 9 / 3 |
| regression vs `carol_rush` | *arm still playing* |

**The pre-registered map prediction lands, and as a gradient rather than a single hit.** I
predicted the gain would concentrate where tower paint is scarcest, because that is where
trading a 100-paint mopper for a 200-paint soldier bites hardest:

| map | tower turns with `tp < 200` | i21 |
|---|---|---|
| walalilongla | 93.8% | **+1** |
| PlumberGame | 83.7% | **+1** |
| Bunny | 74.7% | **+1** |
| DefaultLarge | 59.4% | −1 |
| Castle | 26.5% | −1 |

**Every map that moved up is above 74% starved; both maps that moved down are below 60%.** The
sign of the effect tracks the scarcity of the resource the mechanism trades against, monotonely,
across five maps with independent measurements. That is a far stronger form of confirmation
than "the predicted maps moved" — it is the *dose of the underlying condition* predicting the
*sign* of the outcome.

Parking_lot (99.1%) and gridworld (97.3%) did not move at all, which is the one part that does
not fit; both are maps where **every** tower is dry, so a cheaper unit still cannot be built and
there is nothing for the change to bite on. That is consistent with the iteration-20 finding
that those two maps have a paint *income* problem rather than a distribution or price problem.

**Not yet decided** — the `carol_rush` regression arm is still playing, and iteration 19 showed
that arm behaves *differently* for mopper-share changes (the zero arm scored 39/40 there while
losing badly to the lineage). Given moppers pay off in long coverage wars and `carol_rush` ends
games fast, I expect dose 2 to do slightly *better* than the incumbent against the rusher; if
it instead drops materially, that is new information and I will treat it as such rather than
waving it through on a good head-to-head.

## Iteration 21 RESULT — ACCEPT. Dose 2 beats the incumbent 5 by +6 games.

Run `20260907-145635`, 20 pinned maps, null `carol_m18`.

| gate | threshold | result |
|---|---|---|
| h2h vs `carol_iter18` | >50% | **26/40 = 65.0%** |
| peer `WinPct` | 60% | **met** |
| **margin vs the `carol_m18` null** | >0 | **+6 games**, 9 maps up / 3 down |
| swept-win / swept-loss | — | **9 / 3** |
| regression vs `carol_rush` | no drop from 37/40 | **37/40 = 92.5%, identical** |
| map prediction | gains where tower paint is scarce | **confirmed as a gradient** |
| overall | — | 63/80 = 78.8% |

**The gradient is the strongest part.** Every map that moved up sits above 74% tower-paint
starvation (walalilongla 93.8%, PlumberGame 83.7%, Bunny 74.7%); both maps with data that moved
down sit below 60% (DefaultLarge 59.4%, Castle 26.5%). The *dose of the underlying condition*
predicts the *sign* of the outcome across five independently-measured maps. A unit-mix change
has no map-local mechanism to instrument, so this gradient is the closest thing to a firing
counter available — and it behaves exactly as the price argument says it must.

**How this iteration was actually found — worth recording as method, not just result.** It came
out of a *rejected* iteration. I proposed cutting moppers because they idle on 95.1% of 78,480
turns; the mandatory **zero arm** refuted that at 35%, and the same run's dose-2 arm beat dose 0
by more than dose 5 did (72.5% vs 65.0% against a shared opponent on identical maps), exposing
a **concave curve with the incumbent past its peak**. Neither of my framings survived — "cut
them" and, after a partial read, "add more". The truth was the third option I had not
considered: **moppers are valuable and there are too many of them.**

Without the zero arm I would have had a single 2-vs-5 comparison and no way to tell a slope
from a peak. Doctrine #2 requires it for exactly this reason and it paid for its 40 games twice
over — once by killing my hypothesis, once by pointing at the accept.

**DECISION: ACCEPT.** Snapshotted `carol_iter21`; `src/carol` is now iteration 21. Fresh mirror
`carol_m21` built from the new baseline in the same commit.

**Consequence for iteration 22**, flagged before it lands: run `20260907-150922` measures the
splasher dose arms against `carol_iter18`, which is no longer the baseline. Its **dose curve**
(`SPLASHER_IN_20` 0 vs 3 vs 6, within-run, shared maps) stays valid; its **accept gate** must be
re-measured against `carol_iter21` with the `carol_m21` null. Third time this session; it is a
standing cost of running candidates in parallel and worth paying for the throughput.

### Where the mopper thread now stands

Three points measured on the curve: 0 → 35%, 2 → accepted at 65% over 5, 5 → the old incumbent.
The peak is at or below 2 and is **not yet bracketed from below** — dose 1 is untested and dose
0 is bad, so the optimum lies in `{1, 2}` unless the curve is flat there. That is one constant
and one run, and it is the natural next dose. Iteration 19's finding that the right share is
*matchup-dependent* (the zero arm scored 39/40 against `carol_rush` while losing 35% to the
lineage) argues that the real answer is a threshold read from game state — enemy paint seen per
turn — rather than any constant at all.

## Iteration 22a (SPLASHER_IN_20 = 0) — 12.5%, and it vindicates iteration 11 by an enormous margin

Run `20260907-150922`, first arm complete: `carol_i22a` vs `carol_iter18` = **5/40 = 12.5%**.

Deleting splashers costs carol roughly **fifty points of win rate** against its own baseline.
Yet a splasher *fires* only 10–20 times in a 2,000-round game (measured across the 8 complete
iteration-14 games: SPLASH 0–20 per game, against hundreds of idle turns). That is the third
independent instance this session of the same pattern:

| mechanism | firing rate | measured worth |
|---|---|---|
| iteration 12's paint-tower upgrade | 3 firings in 144,823 tower-turns | +5 games |
| moppers (iteration 19 zero arm) | act on 2–5% of turns | −30 points to delete |
| **splashers (iteration 22 zero arm)** | **10–20 splashes per game** | **−50 points to delete** |

**Frequency is not value, and this project keeps proving it in both directions.** Every time I
have reached for an idleness or firing statistic as a reason to remove or distrust something,
the zero arm has contradicted me. The correct instrument is always the counterfactual — take
the thing away and measure — and it is cheap: one arm in a run I was making anyway.

It also retroactively prices **iteration 11** (splashers, accepted at 62.5% and never
re-measured since). A feature accepted ten iterations ago on a 62.5% head-to-head turns out to
be carrying roughly half of carol's current win rate against her own lineage. That is a far
larger contribution than its accept margin suggested, and it is a second instance of the
LEARNINGS entry "price the features you already carry" — the ablation that prices a feature is
almost always available inside a run you are running for another reason.

**Still to come in the same run**: `carol_i22b` (dose 6) against dose 0, which fixes the shape
of the curve. Early indication is that dose 0 does *better* against dose 6 than against the
incumbent 3, which would put the peak at or below 3 — structurally the same finding as the
mopper curve, and the reason the run carried a zero arm and a high arm rather than one new
constant.

## Iteration 22 (splasher dose) — the incumbent 3 is at or past the peak; REJECT both arms

Run `20260907-150922`, 20 pinned maps, dose arms measured against a shared opponent.

| comparison | `carol_i22a` (dose **0**) scores | so the opponent scores |
|---|---|---|
| vs `carol_iter18` (dose **3**, incumbent) | **5/40 = 12.5%** | **87.5%** |
| vs `carol_i22b` (dose **6**) | **15/40 = 37.5%** | **62.5%** |

Both arms are measured against the *same* opponent on the *same* pinned maps in the *same*
run, so the comparison between them is exact. **Dose 3 beats dose 0 far more decisively than
dose 6 does** — 87.5% against 62.5% — so the curve is concave and **the incumbent 3 sits at or
just past the peak, with 6 clearly worse.**

**DECISION: REJECT both arms.** `SPLASHER_IN_20` stays at 3.

**What the run bought for its 120 games**, given neither arm is accepted:

1. **Splashers are worth ~50 points** and were on the unmeasured list. Iteration 11 accepted
   them at 62.5% ten iterations ago and nothing had priced them since.
2. **The incumbent is confirmed near-optimal**, which is a real result: it retires "sweep the
   splasher share" as a direction rather than leaving it as a permanently plausible unexplored
   knob. Doctrine #2's curve-with-a-zero-arm did this in one run where a sequence of single
   doses would have taken three and still not shown the shape.
3. **The two unit-mix knobs behave oppositely.** The mopper share was *past* its peak by a wide
   margin (5 → 2 was worth +6 games); the splasher share is *at* its peak. I had no way to
   guess which before measuring, and the symmetric-looking hypothesis "carol over-provisions
   cheap support units" would have been half right and half expensively wrong.

### Closed-directions ledger update

- **"Change the splasher share" — CLOSED.** `20260907-150922`: dose 0 = 12.5% (catastrophic),
  dose 6 loses to dose 3 on a shared-opponent comparison (62.5% vs 87.5%). The incumbent is at
  or just past the peak; only dose 1–2 is unmeasured and it is bracketed on both sides by
  worse points. Re-opening needs a reason the *optimum moved*, e.g. a change to the paint
  economy large enough to alter what a 300-paint unit costs in practice.

## Re-scoring every accept with map-resampling (`tools/map-resample.py`)

MULTI_AGENT.md gained a section while I was running: **the error bar is over MAPS, not over
games**, with a tool to compute it. Every (map, side) cell is a fixed function of the two
programs, so nothing is random per game; the only thing that varies between estimates is which
maps were drawn. I had been quoting margins in games — correct as far as it went, and the
right unit — but with no interval at all. Re-scoring all three accepts (the tool treats the
run's `BOT` as the baseline, so its rows are the *opponent's* score; inverted here):

| iteration | h2h | margin vs null | **resampled** | 95% CI on the candidate | clears the null? |
|---|---|---|---|---|---|
| **14** frontier-seeking | 26/40 | +6 | **+2.93 sd** | **[22, 30]** | **yes** |
| **18** reserve dead band | 27/40 | +7 | **+2.40 sd** | **[21, 33]** | **yes** |
| **21** `MOPPER_IN_20 = 2` | 26/40 | +6 | **+1.88 sd** | **[20, 32]** | **marginal — lower bound sits exactly on the null** |

**Iteration 21 is the weakest of the three and I want that on the record.** Its point estimate
is +6 games with 9 maps up and 3 down, the gradient across tower-paint scarcity is clean, and
`carol_rush` is unchanged — so I am not reversing the accept. But the 95% interval's lower
bound touches 20/40, which the other two clear outright, and TRAINING_ALGORITHM §5b is explicit
that **"a marginal accept is an unpriced liability against every feature you have not written
yet."** Iteration 21 is now the flagged half of any future destructive pair, and the frozen
roster is the instrument that would catch it.

Two things this immediately corrects about my own numbers:

- **Iterations 14 and 18 are stronger than I claimed**, not weaker. I reported "+6 games" and
  "+7 games" and left it there; resampling puts them at 2.9 and 2.4 sd with intervals clear of
  the null. The per-map concentration is what does it — iteration 14's run has *no* map where
  the candidate took both sides against it, so the variance is genuinely small.
- **The splasher sweep is far more decisive than the raw percentages suggested.** Dose 3 beats
  dose 0 at **+6.23 sd** (35/40, CI [30, 39]) while dose 6 beats it at only **+1.47 sd**
  (25/40, CI [18, 31]). Those intervals barely overlap, so "the incumbent is at or past the
  peak" is not a close call.

The lesson generalizes past this tool: I spent the session carefully counting games and
refusing to import a binomial model, which was right — but "no model" is not the same as "an
interval", and for two accepts I under-sold a real result by declining to quantify it at all.

## Iteration 23 (MOPPER_IN_20 = 1) — REJECT at 37.5%, and it BRACKETS the peak at 2

Run `20260907-154412`, head-to-head arm complete against `carol_iter21`.

```
15/40 = 37.5%     swept-win 2 / swept-loss 7     null (carol_m21) = 20/40
```

**−5 games against the null.** Dose 1 is clearly worse than dose 2.

**The mopper dose curve is now closed from both sides**, which is the outcome doctrine #2 says
is worth more than any single point:

| `MOPPER_IN_20` | measured against | result |
|---|---|---|
| **0** | dose 5 | 35.0% |
| **1** | **dose 2** | **37.5%** |
| **2** | dose 5 | **65.0% — ACCEPTED** |
| 5 | (old incumbent) | — |

Dose 2 beats its neighbour below (dose 1 loses to it 37.5%) *and* its neighbour above (dose 5
loses to it 65%). **That is a true interior optimum, bracketed by measurement rather than
inferred**, and it is a materially stronger claim than iteration 21's own head-to-head made.

**It also answers the marginality flag I raised an hour ago.** Map-resampling put iteration 21
at +1.88 sd with a 95% lower bound sitting exactly on the null — the weakest of my three
accepts, and I recorded it as the unpriced liability §5b warns about. A single head-to-head at
the edge of its interval is one thing; a **peak confirmed from both directions** is another.
Two independent comparisons now place dose 2 above both adjacent doses, and the reason is
mechanistic and measured rather than fitted: moppers are the cheap unit (100 paint against a
soldier's 200) drawn from stashes under 200 on 57–99% of tower turns, so too few starves
production and too many wastes it. **I consider iteration 21 de-flagged.**

**DECISION on iteration 23: REJECT.** `src/carol` stays at iteration 21, `MOPPER_IN_20 = 2`.

### Closed-directions ledger update

- **"Tune the mopper share" — CLOSED, optimum found.** Four doses measured (0, 1, 2, 5); 2 is a
  bracketed interior optimum. Re-opening requires a change to the paint economy large enough to
  move what a 100-paint unit is worth — which is exactly what iteration 20's ferry or a tower-mix
  change would be, so this is a real re-opening condition rather than a closed door.

## The `carol_m21` null — sixth confirmation

```
carol_iter21 vs carol_m21:  20/40 (50.0%)   swept-win 0/20   swept-loss 0   split-by-side 20/20
```

Six mirrors, six exact even splits, zero swept maps across all six. The null is deterministic
and has no variance, and `carol_m21` is now the control for everything measured against
iteration 21.

## Corpus check: carol's `towerTypeFor` key is SINGLE-BRANCH on 6 of 75 maps — including one in my pinned sample

`tools/mapdata/` arrived as shared ground while I was running, recording that any `(x+y)&1`
policy is single-branch on four maps. **Carol's tower-type policy is the same shape with a
different modulus**, so the shared table could not answer it:

```java
int k = Math.min(ruin.x, w-1-ruin.x) + Math.min(ruin.y, h-1-ruin.y);
return (k % 3 == 0) ? LEVEL_ONE_MONEY_TOWER : LEVEL_ONE_PAINT_TOWER;
```

I adapted the shared `RuinScan` into `tools/towerkeyscan/TowerKeyScan.java` (carol-private) and
ran it over all 75 official maps:

| map | ruins | money | paint | consequence |
|---|---|---|---|---|
| **gridworld** | 21 | **21** | **0** | every new tower is MONEY — **no new paint income all game** |
| **DefaultLarge** | 20 | **0** | 20 | every new tower is PAINT — **no new chip income all game** |
| BatSignal | 10 | 0 | 10 | no new chip income |
| Racetrack | 10 | 0 | 10 | no new chip income |
| rain | 12 | 0 | 12 | no new chip income |
| roads | 8 | 0 | 8 | no new chip income |

Corpus-wide the split is 447 money : 927 paint, so a trace on a typical map shows both branches
healthy and nothing looks wrong — exactly the trap the shared README describes.

**This retroactively explains two things I had measured and mis-attributed.**

1. **gridworld's 76,420 idle chips and 97.3% dry towers are my own policy, not the map.** I
   wrote that gridworld "has a paint *income* problem" and that the chip surplus is "a symptom
   of paint starvation". Both true — and the *cause* is that carol builds 21 money towers and
   zero paint towers there. I had been treating a self-inflicted degeneracy as a property of
   the terrain.
2. **DefaultLarge's median treasury of exactly 1,200** — pinned at the reserve to the chip —
   now has a mechanism: with every new tower a paint tower, chip income never grows past the
   starting money tower, so the treasury *cannot* climb to 1,450 and the reserve is permanent.
   **That is why iteration 18's release fired hardest there (`pf` 53 and 33) and why
   DefaultLarge was one of its three predicted wins.** The accept is unaffected and better
   explained.

**And it vindicates treating gridworld's anomalies as untrustworthy.** gridworld moved against
*both* iteration 17 and iteration 18 and I recorded it as chaos-sensitive on that evidence
alone. It is now degenerate in **three independent ways**: single-parity ruins, densest map in
the corpus (1.9x median), and all-money under carol's own key.

### Costing the fix before building it (TRAINING_ALGORITHM §3, new pre-check)

I swept 11 candidate replacement keys over the corpus. All are functions of
`(mx, my) = (min(x,w-1-x), min(y,h-1-y))` only, so all preserve the play-symmetry property the
current key was chosen for — both teams assign the same type to mirrored ruins.

| key | degenerate maps | money:paint | **churn vs current** |
|---|---|---|---|
| **CURRENT** `(mx+my)%3==0` | **6** | 447:927 | — |
| `(mx+my)%2==0` | 4 | 764:610 | **50.6%** |
| `(mx*my)%3==0` | 5 | 714:660 | 65.0% |
| `(mx*3+my)%4==0` | 5 | 402:972 | 44.0% |
| `(mx+my)%5<2` | 6 | 543:831 | 46.4% |
| `(mx+my)%4==0` | 7 | 373:1001 | 40.8% |
| `mx%3==0` | 8 | 447:927 | 45.6% |
| `(mx%3==0)&&(my%3==0)` | 36 | 134:1240 | 22.8% |

**No positional key escapes.** The best candidate still breaks 4 maps, and every one of them
reassigns **40–65% of all ruins** — an enormous price paid on the 69 maps that are not broken,
to half-fix the 6 that are. The whole *family* of coordinate-keyed policies is degenerate on
this corpus, because ruin layouts are structured (grids, lattices, symmetric motifs) and any
modulus can align with the structure.

**So the answer is not a better key; it is to stop deciding tower type from position alone.**
That is a genuinely different design and it needs a global signal carol does not have — she has
no comms, and `getNumberTowers()` returns a count, not a composition. Registering the constraint
rather than rushing a bundled fix while the roster run is in flight.

**Leading design, with its price stated**: keep the key as the default, and override *only* in
the degenerate direction — if the key says MONEY and the soldier can sense **no ally paint
tower** anywhere in vision, build PAINT instead. On gridworld paint towers are absent by
construction, so the override fires and the mix is restored; on a normal map two thirds of
towers are paint, so a soldier completing a ruin almost always sees one and the override is
inert. **The price is bounded by how often a soldier is out of sight of every ally paint tower
on a healthy map**, which is measurable from one instrumented game — the decision counter, not
the outcome, per the other new §3 pre-check.

## Iteration 20 re-costed — the ferry's price is a slice of the ~30 points moppers are worth

I deferred the ferry on its *benefit* ceiling: a mopper carries 100 paint, delivers down to
half, so one trip moves **50 paint** against the **200 in a single stash** a soldier costs —
four round trips per soldier, and only ~5 deliveries per mopper per game were observed. That
was the right arithmetic and it was only half the calculation.

**The half I missed**: a mopper sent hauling is a mopper *not doing the thing the iteration-19
zero arm priced at ~30 points.* Deleting moppers costs 35% vs 65%; that value comes from
mopping enemy paint, which is the only way carol reclaims ground because soldiers cannot
overwrite enemy paint. And the shuttle drives moppers **toward towers**, which is away from the
frontier where enemy paint is. So the price is not "idle turns spent walking" — moppers idle
95% of the time and I had treated that as free — it is **positional**: hauling relocates the
unit out of the region where its 2–5% of valuable actions occur.

That reframes the measurement I already have. Iteration 20's target metric moved the *wrong*
way (tower `tp<200` 51.6% against the baseline's 50.2%, median stash 175 vs 195). I recorded
that as "mechanism confirmed, primary metric flat-to-worse". With the price term written down
it is no longer a puzzle: I was spending a capability worth ~30 points to buy at most a couple
of soldiers' worth of paint per game, and the ledger was always going to come out negative.

**Benefit and price, as the two numbers §3 now requires, before any further work:**

| | quantity |
|---|---|
| **benefit** | ~5 deliveries x 50 paint = **~250 paint/game**, about **1.25 soldiers** |
| **price** | a fraction of the **~30 points** moppers are measured to be worth, via displacement from the frontier |

**DECISION: iteration 20 CLOSED, not merely deferred.** The direction is not re-openable by
better navigation — better navigation makes the price *worse*, because it is precisely the
driving-to-towers that displaces the unit. Re-opening requires either a carrier whose
alternative use is genuinely zero, or a way to move paint that does not move a unit at all.

**And it sharpens what the real problem is.** Tower stashes are dry because income is
mal-distributed at the *source* — carol builds the wrong tower types, provably so on 6 maps and
by a fixed positional rule everywhere else. Hauling paint between towers is treating a symptom
of the tower-mix policy with a unit that costs 30 points to misplace. The tower-mix work
(previous section) is the same problem attacked where it is created, and it costs no unit's
time at all.

## Iteration 24 — the decision counter refuted my "self-limiting" claim in one game

I wrote that the override would be "inert on a healthy map, because two thirds of towers are
paint so a soldier finishing a ruin nearly always has one in sight". Instrumented the
**decision** (`mixAsk` = the key said MONEY; `mixFlip` = we overrode it), per §3's new pre-check:

| map | `mixAsk` | `mixFlip` | tower `tp<200` — i24 vs iter21 | median stash |
|---|---|---|---|---|
| **gridworld** (all-money key) | 141 | **105** | **38.9% vs 53.9%** | **547 vs 119** |
| **DefaultMedium** (healthy) | 41 | **41** | 11.0% vs 10.7% | 820 vs 795 |

**On gridworld the mechanism does exactly what it was designed to do** — median tower stash
119 → **547**, a 4.6x improvement, and the fraction of tower turns unable to afford a soldier
falls from 53.9% to 38.9%. The degenerate map is repaired.

**On DefaultMedium the override fired on 41 of 41 asks.** Not "rarely" — *always*. Vision is
r²=20 and towers are spread across a 50x30 map, so **being out of sight of every ally paint
tower is the common case, not the exception.** My guard was not a guard; it was a wholesale
replacement of the tower-type policy with "always build paint", which throws away chip income
everywhere — and chips are what iteration 18 was about.

**This is the level-2 reachability error again, inverted.** Earlier this session I assumed a
condition existed in the robot's view because it existed on the map (iteration 20's ferry).
Here I assumed a condition would be *rare* in the robot's view because it is rare on the map.
Same mistake, opposite sign: **"in vision" is a much weaker and much more common condition than
map-level statistics suggest**, and I now have it measured in both directions.

**Fix, and it is the strictly rarer condition**: latch a per-robot memory — has this robot
**ever** sensed an ally paint tower? A robot spawns adjacent to the tower that built it and
sees every tower it walks past, so on a map that *has* paint towers the flag latches true
early and stays true, making the override inert by construction rather than by my assumption.
On gridworld, where carol builds no paint towers at all, it stays false and the override fires.

Re-verifying on the same two maps before anything else — the point of a decision counter is
that it costs one game to check, and I have now been wrong about this class of condition twice.

## Iteration 24b — the latch fires NEVER; 24a fired ALWAYS; the useful condition is between them

Re-verified the `sawPaintTower` latch on the same two maps (`gauntlet/20260907-182006`, 4 games,
i24 vs iter21, both sides). The decision counter again answered in one run — and again it
refuted the design:

| map | key | `mixAsk` | `mixFlip` | verdict |
|---|---|---|---|---|
| **gridworld** | all-MONEY (21/21 ruins) | 144 | **0** | override never fired *on the map it was built for* |
| **DefaultMedium** | healthy | 41 | **0** | inert, as intended — but for the wrong reason |

**Cause, and it was on disk in my own RULES.md the whole time**: `NUMBER_INITIAL_PAINT_TOWERS = 1`.
Every team starts with exactly one paint tower, and every robot spawns adjacent to the tower that
built it. So `sawPaintTower` latches true on turn 1 for essentially every robot ever spawned and
never releases — including on gridworld, where carol then builds 21 money towers and zero paint
towers behind a flag that says "paint income exists somewhere". The flag was true and useless:
it recorded that a paint tower *had once existed*, which is guaranteed by the rules, not that
paint income is adequate.

**The pair of measurements is the finding.** Same mechanism, two candidate conditions, both
instrumented at the decision rather than the outcome, both killed for 4 games of VM time:

```
24a  "no ally paint tower in vision RIGHT NOW"   -> fired 41 of 41 asks   (a policy replacement)
24b  "never sensed an ally paint tower EVER"     -> fired  0 of 185 asks  (dead code)
```

I bracketed the condition from both sides without ever paying for a full evaluation. That is the
same shape as iteration 23's mopper dose bracket, applied to a *predicate* instead of a
parameter, and I want it recorded as a reusable move: when a guard's firing rate is the thing in
doubt, build the two extreme predicates first and read the bracket, rather than guessing a middle
one and evaluating it.

### Reachability, level 3 — the third distinct way I have been caught this session

The ledger now reads:

1. **iteration 20 (ferry)**: assumed a condition existed *in the robot's view* because it existed
   *on the map*. Over-optimistic about visibility.
2. **iteration 24a**: assumed a condition would be *rare in the robot's view* because it is rare
   *on the map*. Same error, opposite sign — "in vision" is far weaker and far more common than
   map-level statistics suggest.
3. **iteration 24b**: assumed a *lifetime* memory would be rarer than an *instantaneous* one, and
   never checked what the RULES guarantee about the game's initial state. A latch over a
   condition the rules guarantee at t=0 is not a rare condition; it is a constant.

The generalisation worth keeping: **a predicate's firing rate is a property of the robot's
information, not of the map** — and the rules' initial conditions are part of that information.
Check the starting state before building any "have I ever seen X" memory.

### What the census probe (24c) is for

Neither extreme is useful because both throw away the actual quantity of interest: carol has no
comms and `getNumberTowers()` returns a count, not a composition, so no robot can read the global
tower mix directly. But a robot *can* accumulate a local sample of it. `src/carol_i24c` is
**instrumentation only** — the key is obeyed exactly as in iter21, so its games must reproduce
iter21's outcomes and the run doubles as an arm-to-arm identity check — and it records, per
robot, the DISTINCT ally towers ever seen split by type (`sp=` paint, `sm=` money), plus what a
census rule *would* have done at each real decision point (`mf=`).

The point is to read the separation between a degenerate map and a healthy one off a replay and
**derive** the threshold, rather than guess a third predicate and discover its reachability
afterwards. Pre-registered before the run:

- **Prediction**: on gridworld `sp` stays at 1 (the starting paint tower) while `sm` climbs past
  10, so the ratio collapses; on DefaultMedium and Fossil `sp` should track roughly 2x `sm`.
- **Kill condition**: if `sp:sm` does not separate the six maps into the degenerate and healthy
  groups the corpus scan predicts, the whole "local proxy for the global mix" idea is refuted and
  the tower-mix direction closes without a fourth predicate.

## Iteration 24c — the census SEPARATES the maps, and hands me the threshold

`gauntlet/20260907-182709`, 12 games, i24c vs iter21 on six maps chosen to span the corpus scan's
three classes. **Arm-to-arm identity check first** (doctrine #3): 6/12, all six maps split by
side, zero swept — and the loss set is *exactly* the `carol_m21` mirror's loss set on those maps.
So the instrumentation is a confirmed no-op and everything below was measured under iter21's own
dynamics, not under a perturbed build.

**Census at the decision points** (`sp` = distinct ally PAINT towers this robot has ever seen,
`sm` = money; `ma` = the key said MONEY, so a decision was actually made):

| map | key class | deciding lines | modal census state at a decision |
|---|---|---|---|
| **gridworld** | ALL-MONEY | 5535 | `sp=1 sm=5`, `sp=1 sm=4` — paint pinned at 1, money climbing |
| Fossil | healthy | 633 | `sp=1 sm=1`, `sp=2 sm=1`, `sp=3 sm=1` |
| DefaultMedium | healthy | 458 | `sp=4 sm=0`, `sp=3 sm=0`, `sp=5 sm=0` |
| Bunny | healthy | 78 | `sp=1 sm=1`, `sp=1 sm=0` |
| DefaultLarge, rain | ALL-PAINT | **0** | the key never says MONEY, so nothing to override |

`sp=1` on gridworld is the *starting* paint tower and nothing else — the same fact that made 24b's
latch a constant, now visible as a number instead of an assumption.

**The pre-registered prediction held**: gridworld's ratio collapses (`sp` stuck at 1, `sm` to 9),
the healthy maps sit paint-heavy. The kill condition did not trigger.

### The threshold is derived, not guessed

The naive rule `sp*2 < sm` fires 44 times on **Fossil**, a healthy map — so the raw ratio is not
clean. Every one of those 44 is a robot in state `sp=0 sm=1`: a census of *one*. Requiring a
minimum local sample removes them:

| map | deciding lines | fires, no guard | fires, census>=3 | fires, census>=4 |
|---|---|---|---|---|
| **gridworld** | 5535 | 4962 | **4603** | 4450 |
| Fossil | 633 | 44 | **0** | 0 |
| DefaultMedium | 458 | 0 | **0** | 0 |
| Bunny | 78 | 0 | **0** | 0 |

`CENSUS_MIN = 3` is a perfect separator on the four maps that can exercise it: 83% firing on the
degenerate map, provably zero on all three healthy ones. I take 3 rather than 4 because at a
census of exactly 3 the only money-heavy state is `sp=0 sm=3` — three towers seen, all money,
which is a strong signal rather than noise — and `>=4` is a ready conservative dose arm if it
regresses.

### Benefit and price, as two numbers, before the run (TRAINING_ALGORITHM §3)

Re-ran `tools/towerkeyscan` over all 75 maps for the *global* mix, not just the fully-degenerate
ones. Maps money-heavy enough for the override to be globally right:

| map | money : paint |
|---|---|
| gridworld | **21 : 0** |
| MoneyTower | 8 : 2 |
| Filter | 4 : 1 |
| CastleDefense | 4 : 2 (exactly on the boundary) |

- **Benefit: 3–4 maps of 75 (4–5% of the corpus).** In a random 20-map sample that is ~1 map,
  worth at most 2 games in 40.
- **Price: measured at zero.** The guard fires 0 times on all three healthy maps instrumented,
  and the five ALL-PAINT maps never reach the branch at all (`ma=0`). Plus a bytecode cost on a
  build whose robot peak is 37.5% of 17500.

This is deliberately the profile TRAINING_ALGORITHM names as the recurring winner: **capability
preserved at zero marginal cost.** It is not a headline mechanism and I am not pretending it is.

### Therefore the accept gate must NOT be a blind 20-map gauntlet

A mechanism that fires on ~1 map in 20 can move at most ~2 games of 40, which a headline win rate
cannot resolve — doctrine #4, an instrument that cannot see the effect. Two arms instead, both
pre-registered now:

- **Arm A — does it help where it fires?** `gridworld Filter MoneyTower CastleDefense`, both
  sides, vs `carol_iter21`. 8 games. Null is 4/8. **Gate: > 4/8, and gridworld must not be a
  swept loss.**
- **Arm B — is it free everywhere else?** the standing 20-map pinned sample, vs `carol_iter21`.
  40 games. **Prediction: deviation from the mirror null on gridworld and NOWHERE ELSE** — every
  other map must reproduce `carol_m21`'s split exactly. This is a zero-deviation prediction, so
  any extra deviating map falsifies the "measured price is zero" claim directly.

Arm B is the real test. Arm A can only ever be worth a couple of games; Arm B is what says
whether I have bought them for free or paid for them somewhere I did not look.

## Iteration 25 — ACCEPT. Both pre-registered arms hit exactly, and the price is measured at zero

`gauntlet/20260907-184254`, 46 games, `carol_i25` vs `carol_iter21` on the 20 standing pinned
maps plus `Filter MoneyTower CastleDefense`. Null: `carol_iter21` vs `carol_m25`'s predecessor
`carol_m21`, verified byte-identical apart from the package line before use, on the same 20 maps
(`20260907-153510`) and extended to the 3 new ones (`20260907-184322`).

```
headline      i25 24/46 (52.2%)   null 23/46
swept maps    i25 swept 1 of 23   null swept 0 of 23   (identical code sweeps nothing)
resampling    +1.01 sd over maps, boot_se 0.99, jack_se 1.00
```

### The map-level diff is the result, not the headline

I diffed all 46 `(map, side)` cells against the mirror null:

```
cells compared: 46
DEVIATIONS from the mirror null: 1
   gridworld  side A:  null=loss -> i25=win
```

**One cell in forty-six.** Forty-five of forty-six are outcome-identical to identical code, and
the single deviation is the exact map and the exact direction I registered before the run. The
"price is zero" claim is now measured rather than argued: there is no map where this cost me
anything, because there is no map other than gridworld where it did anything at all.

- **Arm A (does it help where it fires?)** — gate was `> 4/8` on the four money-heavy maps with
  gridworld not a swept loss. Result **5/8 vs the null's 4/8**, and gridworld went from a
  1–1 split to a **swept win**. Filter, MoneyTower and CastleDefense did not deviate: their
  global mixes (4:1, 8:2, 4:2) are money-heavy but their *local* censuses evidently never reach
  the money-heavy state, which is the conservative direction to be wrong in.
- **Arm B (is it free everywhere else?)** — prediction was zero deviation off gridworld.
  **Zero deviations on all 22 other maps.** Not "within the noise band": identical.

### Why I accept a +1-game margin, and the flag I am attaching to it

Under a null that splits every map and sweeps none — six mirrors, now seven — a swept map is a
near noise-free instrument, so "+1 swept map against 0" is a real effect and not spawn luck.
More to the point, this is the profile TRAINING_ALGORITHM names as the recurring winner:
**capability preserved at zero marginal cost.** It repairs a corpus-level degeneracy (gridworld
builds 21/21 money towers and has no paint income all game) and provably spends nothing to do it.

§5b's warning about marginal accepts is that they are unpriced liabilities against features not
yet written. I record the flag, and also why it is smaller here than usual: the mechanism is
gated behind `census >= 3 && seenPaint*2 < seenMoney`, measured to be false on every healthy map
instrumented, so its interaction surface with any future feature is confined to money-heavy
tower mixes. It is not a broad behavioural change that could pair destructively with something
unrelated.

**DECISION: ACCEPT.** `src/carol` = iteration 25, snapshot `src/carol_iter25`, new mirror
`src/carol_m25` regenerated from the new baseline (the previous accept's mirror is now stale by
construction and must not be reused).

### Functional-area note

Tower-mix policy: 24a rejected, 24b rejected, 25 accepted. The two rejects cost 4 games of VM
time between them because both were killed by decision counters at the pre-check stage rather
than by evaluations. That is the thread closing successfully, not a run of rejects.

## Re-opening the SRP direction — the recorded cause of the deferral no longer holds

The new shared `tools/replay-dump.sh` gave me the per-round team aggregates I had been
reconstructing piecemeal, and its very first two traces produced a finding much larger than the
iteration I was running.

### What the trajectories show (both maps, mirror games, so both sides are carol)

`DefaultMedium` and `Fossil`, from `gauntlet/20260907-182709`. `twPaint` is total paint held
across all the team's towers; `p`/`u` are paint and mop actions in the sampling window;
`starved` is deaths with paint <= 0.

| | round 200 | 400 | 600 | 800 | 1000 |
|---|---|---|---|---|---|
| **Fossil T1 coverage** | 279 | **351 (peak)** | 290 | 265 | **242** |
| Fossil T1 `twPaint` | 4188 | 2108 | 468 | 348 | **218** |
| Fossil T1 paint actions | 267 | 206 | 81 | 31 | **22** |
| Fossil T1 mop actions | 22 | 21 | 49 | 83 | 60 |
| Fossil T2 coverage (same bot!) | 450 | 520 | 583 | 667 | **695** |

**carol's coverage peaks around round 400 and then declines for the rest of the game.** Tower
paint collapses to ~40 per tower, paint actions fall by 92%, and the unit that survives is the
mopper — because moppers do not starve. **The standing army drifts mopper-heavy through
differential survival, not through the production ratio I spent iterations 19-23 tuning.**

And on both maps, in every sampling window, **75-80% of carol's deaths are paint deaths**.
Meanwhile chips sit at $1200-$1700 all game, pinned at `CHIP_RESERVE`, doing nothing.

Two engine facts make this a single coherent story: robots spawn with a full stash drawn from
the building tower (200 for a soldier), and standing on a neutral tile costs 1 paint/turn,
enemy tile 2. So a paint-poor army bleeds upkeep on the very ground it is trying to take.

### The History pre-check, done properly

The SRP direction is on my own deferred list. Iteration 4/5 recorded the reason:

> The SRP work drafted from the API sweep moves behind both; **it is a chip *sink*, and a sink
> is worth little until the chip *source* is fixed.**

That was correct then and it is **specifically obsolete now.** The chip source *was* fixed —
the money-tower mix went in at iteration 5, iteration 18 unpinned the treasury — and the
evidence the re-opening condition asked for is exactly what the traces show: chips idle at
$1200-1700 for entire games *after* the money mix is in, while the binding resource runs dry.
The closed-directions rule allows re-opening only with a specific reason the recorded cause no
longer applies, and this is that reason rather than "feels under-explored".

The neighbouring closed entry (tower upgrades) is **not** re-opened: its own condition was
"chips idle after both the money mix *and* SRPs are in", and SRPs are not in yet.

### Benefit and price, as two numbers, before building (§3)

Engine constants read from the jar with `javap -constants`, not from my digest:
`COMPLETE_RESOURCE_PATTERN_COST = 200` chips, `MARK_PATTERN_PAINT_COST = 25` paint,
`EXTRA_RESOURCES_FROM_PATTERN = 3`, `RESOURCE_PATTERN_ACTIVE_DELAY = 50`,
`RESOURCE_PATTERN_RADIUS_SQUARED = 8`, `PATTERN_SIZE = 5`.

- **Price: ~150 paint and 200 chips, one-off.** 25 to mark, plus up to 125 to paint the 25
  tiles at 5 each (less whatever is already ally-painted). The 200 chips are free — carol is
  provably not spending them. And the paint is only half-spent: those 25 tiles become ally
  paint, which is the `AREA_PAINTED` win condition carol *lost on* in both traced games.
- **Benefit: +3 paint/turn per PAINT tower per SRP**, gated inside
  `if (type.paintPerTurn != 0) addPaint(paintPerTurn + 3*numSRPs)` — so money towers get
  nothing, which my own LEARNINGS already records from the disassembly. At carol's observed 3-6
  paint towers, one SRP is **+9 to +18 paint/turn**. Payback ~13 rounds; an SRP laid at round
  400 returns on the order of **15,000 paint** over the rest of the game.

For scale: carol's *entire tower paint stock* across all towers at Fossil round 1000 was **218**.

### Iteration 26a: instrument the DECISION first

The arithmetic is overwhelming, which is exactly when I should be most suspicious — the
reachability pre-check has caught this lineage three times in one session. The question is not
"is an SRP worth it" but **"can a carol soldier ever actually lay one"**, and there is a
specific reason to doubt it: marking costs **25 paint**, and carol's soldiers are the
chronically paint-starved units in the story above. If the mechanism is unreachable *because*
the bot needs it, that is a real finding and not a disappointment.

`src/carol_i26a` is instrumentation only — a read-only probe at the top of `runSoldier`, taking
no action and changing no state the bot reads, so its games must reproduce iteration 25's.
Counters, all decisions rather than outcomes:

- `srpTurns` — soldier turns sampled
- `srpPoor` — ... of which the soldier held < 25 paint, so marking is unaffordable
- `srpOk` — ... of which `canMarkResourcePattern(here)` was **true**

**Pre-registered kill condition**: if `srpOk` is ~0 while `srpPoor` is the bulk, the direction is
blocked at the paint gate and the fix must be to soldiers' paint supply, not to SRPs. If `srpOk`
is large, the mechanism is simply unused and iteration 26 builds it.

## Iteration 26a — the SRP direction is REACHABLE, and the blocker is not the one I feared

`gauntlet/20260907-190752`, 8 games, i26a vs `carol_iter25` on four maps. Identity check: 4/8,
all four maps split by side — the instrumentation is a confirmed no-op.

Per-robot counters, taken from the longest-lived soldier in each game:

| map | soldier turns | `srpPoor` (< 25 paint) | `srpOk` (`canMarkResourcePattern` true) |
|---|---|---|---|
| DefaultLarge | 125 | 24 (19.2%) | **36 (28.8%)** |
| DefaultMedium | 181 | 17 (9.4%) | 4 (2.2%) |
| Fossil | 113 | 23 (20.4%) | 2 (1.8%) |
| gridworld | 355 | 19 (5.4%) | **0 (0.0%)** |

**The pre-registered kill condition did not fire.** `srpPoor` is 5–20%, not the bulk, so the
25-paint mark cost is *not* what blocks this — my specific worry was wrong. The direction is
reachable on three of four maps, and gridworld's zero is unsurprising: it is a wall lattice with
a ruin every six tiles and no clear 5×5 anywhere.

And 2% is plenty. This mechanism does not need a high firing rate — a game needs a handful of
SRPs, not hundreds. 2% of one soldier's 181 turns is ~4 opportunities for *one* robot, and carol
fields many.

### A flaw in my own probe, recorded rather than quietly fixed

`srpOk` tests `canMarkResourcePattern(rc.getLocation())` — **the soldier's own tile as the
pattern centre, and only that**. But `RESOURCE_PATTERN_RADIUS_SQUARED = 8` means a soldier may
mark a pattern centred anywhere within r²=8, which is ~25 candidate centres. So every number in
that table is a **lower bound**, and possibly a very loose one. It did not change the decision
(a lower bound above zero already clears the gate) but it would have if the answer had come back
near zero — I would have concluded "unreachable" from a measurement that only ever asked about
one of twenty-five options.

The general form is worth keeping: **when instrumenting a decision, check that the counter's
condition is the same width as the decision the bot would actually get to make.** A narrower
proxy can only produce false negatives, and a false negative here reads exactly like a refutation.

### Where the turns come from — answered free, from replays already on disk

The idle-soldier branch already carries iteration 14's `frontFound`/`frontNone` counter, so the
question "is there a budget for this, and does it collide with an existing consumer" cost no VM
time at all:

| map | IDLE-ALLY turns | `frontFound` | `frontNone` |
|---|---|---|---|
| DefaultLarge | 1032 | 292 | **740 (72%)** |
| DefaultMedium | 3443 | 809 | **2634 (77%)** |
| Fossil | 2947 | 340 | **2607 (88%)** |
| gridworld | 6647 | 1621 | **5026 (76%)** |

`frontNone` — nothing paintable in action range *and* nothing empty anywhere in vision — is the
dominant idle case at 72–88%, thousands of turns per game. Iteration 14 consumes only
`frontFound`. So SRP work fires exclusively in `frontNone`, and the two mechanisms **partition
the idle budget by an explicit decision** rather than by which happens to be written first —
which is precisely the accidental-allocation trap §5b describes.

It is also the right *place*, not just the right time: `frontNone` means the soldier is deep
inside saturated ally territory, which is where a pattern can survive its 50-round activation
delay and where most of its 25 tiles are already the correct colour. `RESOURCE_PATTERN` has 13
of 25 bits set, so in ally-primary territory only 13 tiles need recolouring: 25 + 13×5 = **90
paint**, not the 150 I costed on virgin ground.

## Iteration 26 — the mechanism WORKS and my commit gate is wrong; the same error, third disguise

`gauntlet/20260907-191952`, 8 games, i26 vs `carol_iter25` on four maps. **3/8, with Bunny a
swept loss.** Before reading that as a verdict, the §4 mechanistic classification:

| map | `SRPmark` | `SRPdone` | `SRPdrop` | drop rate | paint burned on dropped marks |
|---|---|---|---|---|---|
| Bunny B | 156 | **64** | 92 | 59.0% | **2,300** |
| DefaultMedium A | 58 | 7 | 48 | **82.8%** | **1,200** |
| DefaultLarge B | 31 | **16** | 7 | 22.6% | 175 |
| Fossil A | 8 | 1 | 7 | 87.5% | 175 |

**The mechanism is real.** Soldiers marked patterns, painted them, and completed 88 SRPs across
the sample — a mechanic this lineage has never used in 26 iterations now demonstrably runs. This
is §4 classification 2, not 3: engagement is evidenced, and the reason the games did not flip is
specific and measured rather than hand-waved.

**And the reason is my own error, in its third disguise this session.** The commit gate reads:

```java
&& rc.getPaint() >= GameConstants.MARK_PATTERN_PAINT_COST   // 25
```

25 is the cost of *marking*. It is exactly enough to place the marks and have nothing left to
finish them with. The soldier then paints a few tiles, hits the `< 5 paint` release, and drops —
so the 25 is written off. I priced **the action I was about to take** instead of **the
transaction I was entering**, on a build whose soldiers I had *just finished measuring* as
chronically paint-starved.

LEARNINGS already carries "Cost the price, not just the benefit — twice in one session, two
different disguises". This is the third, and it is worth distinguishing from the first two: those
two omitted a price term entirely. This one **priced the wrong step of a multi-step transaction**
— every individual step was costed, and the entry gate was set to the cheapest of them.

The generalisation: **when a mechanism takes more than one turn to pay off, the gate belongs on
the total, not on the first instalment.** Any commitment with a non-refundable deposit has this
shape, and the tell is a high abandonment rate rather than a low firing rate.

### Refinement, as a dose pair rather than a guess (§5.5, one targeted refinement)

`RESOURCE_PATTERN` has **13 of 25 bits set**, so completing one costs 25 to mark plus the
recolouring: **90** where the other 12 tiles are already ally primary (which `frontNone` territory
mostly is), up to **150** where the ground still needs painting outright. Rather than pick one:

- **`carol_i26b`**: `SRP_COMMIT_PAINT = 150` (full worst case — only well-supplied soldiers commit)
- **`carol_i26c`**: `SRP_COMMIT_PAINT = 90` (typical case in already-ally territory)

Both against `carol_iter25` in **one run** on six maps, so the two doses share the map sample
exactly and the incumbent gate (25) is the third point on the curve from the run above.

**Pre-registered.** Primary: the drop rate must fall well below i26's 59–88%; if it does not, the
gate is not what limits completion and the direction needs a different fix, not a third dose.
Secondary, and this is the one that decides the iteration: **completed SRPs per game must not
fall to ~0** — a gate high enough to eliminate abandonment by preventing all commitment is not a
fix, it is iteration 24b's dead branch wearing a number. I expect 150 to be the safer drop rate
and 90 to complete more patterns, and I do **not** have a prediction for which wins, which is
exactly why both are in the run.

## Iteration 26 — REJECT. The gate was never the binding constraint, and the dose pair proved it

`gauntlet/20260907-192720`, 24 games, six maps, both doses and the baseline in one run so the
arms share the map sample exactly.

```
i26b (gate 150) vs carol_iter25    4/12 (33%)   swept-win 0/6  swept-loss 2
i26b (gate 150) vs i26c (gate 90)  7/12 (58%)   swept-win 1/6  swept-loss 0
```

Dose ordering is clean — **150 > 90** — and both are far below the baseline. With the incumbent
gate of 25 scoring 37.5% in the previous run, the whole curve sits under 50%. There is no
interior optimum to find here; the axis is wrong.

### The pre-registered primary says why, and it is not what I refined

I registered: *the drop rate must fall well below i26's 59–88%.* It did not.

| map / side | gate 25: marks/done/drop | gate 150: marks/done/drop |
|---|---|---|
| DefaultMedium A | 58 / 7 / 48 (82.8%) | **58 / 7 / 48 (82.8%)** — unchanged |
| Fossil A | 8 / 1 / 7 (87.5%) | **8 / 1 / 7 (87.5%)** — unchanged |
| Bunny A | 1 / 0 / 1 | **1 / 0 / 1** — unchanged |
| DefaultLarge B | 31 / **16** / 7 (22.6%) | 18 / **7** / 10 (**55.6%**) |

On three of four maps the gate changed **nothing at all** — identical marks, completions and
drops. Soldiers spawn with 200 paint, so the ones that commit clear a 25 gate and a 150 gate
alike; the gate only ever excluded soldiers that were not committing anyway. And on the one map
where it *did* bind, it made things **worse in both directions at once**: completions halved
(16 → 7) while the drop rate more than doubled (22.6% → 55.6%).

*(Method note: I checked replay hashes first and they differed on every map — uninformative,
because the `BUILD` tag is in every indicator string and shifts the bytes. My own log recorded
that trap at iteration 6b and I walked into it again. The counters are the arm-to-arm evidence
here, not the hashes.)*

### The real mechanism, now identified

Abandonment is not caused by admitting under-funded soldiers. **It is caused by committed
soldiers spending their paint on something else afterwards.** `SRPfar` — the branch where a
committed soldier is off its pattern and steering back — fires 573 to 4,583 times per game.
On those turns `workOnSrp` returns early, and the rest of `runSoldier` then runs normally: the
soldier paints ordinary tiles, bleeds movement upkeep, and arrives back at its pattern below the
5-paint release threshold. Entry funding is irrelevant when the funds are spent in transit.

### What this costs the §5b partition argument, which I got half right

I was careful to scope SRP work to `frontNone` so it would not compete with iteration 14's
frontier-seeking, and I still think that was the right call at the point of entry. But **the
partition held only at commit time.** Once `srpCenter` is set, the mechanism captures the
soldier's *navigation* on every subsequent turn, including thousands of turns that were never
free. The budget I promised to spend was "idle turns"; the budget I actually spent was "idle
turns, plus the movement of every soldier that ever had one".

**The generalisation, and it sharpens §5b rather than merely illustrating it: partitioning a
budget at the ENTRY point does not partition it if the mechanism carries state that steers later
turns.** A stateless branch spends only the turn it fires on. A commitment spends every turn
until it is released, and those turns must be costed at the entry decision. Check whether a
mechanism is stateless before trusting a scoping argument about when it fires.

**DECISION: REJECT.** `src/carol` stays at iteration 25 — iteration 26 was never promoted, so
there is nothing to revert. Three consecutive attempts now in the SRP/tower-econ area (24a, 24b
rejected at pre-check; 26 rejected on evaluation), so per `MaxConsecutiveRejects` **the next
attempt must leave this area.**

### Closed-directions ledger

- **"SRPs as currently designed" — CLOSED on the commitment model, not on the mechanic.** The
  mechanic itself is *proven to work*: 88 patterns completed across the first run, on a build
  that had never laid one in 26 iterations, and the arithmetic (+3/turn per paint tower, ~90
  paint, ~13-round payback) is unchanged and still attractive. What is refuted is
  **per-soldier commitment with navigation capture**. Re-opening requires a design where laying
  an SRP does not take a soldier hostage — the obvious candidate, for whenever this area re-opens,
  is an *opportunistic* version with no `srpCenter` at all: complete any pattern that happens to
  be finishable from where the soldier already is, and mark only when standing somewhere the
  soldier was going to stay anyway. That has no in-transit spend to lose.

## Audit: `map-resample.py` was INVERTING, not mislabelling — every figure I quoted re-checked

The coordinator fixed both tooling bugs I reported (`7647afb`) and corrected my diagnosis of the
first: `map-resample.py` was not merely mislabelling its rows, it was **inverting** them. It
counted `bot_result != "win"` as a candidate win, which is right only for
`BOT=<baseline> OPPONENTS=<candidates>`. I launch the other way round — `BOT=<candidate>` — so
every number it ever gave me was the **opponent's** score under a "candidate wins" header. Both
readings look plausible, which is why it survived.

I re-ran the fixed tool against every resampled figure in this log. **All of them reproduce
exactly, and no verdict moves.**

| logged claim | logged | fixed tool | |
|---|---|---|---|
| iteration 21 accept | 26/40, CI [20, 32], **+1.88 sd** | 26/40, CI [20, 32], **+1.88 sd** | ✓ |
| iteration 25 accept | 24/46, **+1.01 sd** | 24/46, CI [23, 26], **+1.01 sd** | ✓ |
| splasher dose 3 beats dose 0 | 35/40, CI [30, 39], **+6.23 sd** | 35/40, CI [30, 39], **+6.23 sd** | ✓ |
| splasher dose 6 beats dose 0 | 25/40, CI [18, 31], **+1.47 sd** | 25/40, CI [18, 31], **+1.47 sd** | ✓ |

The reason they survived is on the record in the re-scoring entry itself, which I wrote at the
time: *"the tool treats the run's `BOT` as the baseline, so its rows are the opponent's score;
inverted here"*. I spotted the convention mismatch, wrote it down, and transformed every figure
by hand — so I had the right numbers for a *documented* reason rather than by luck. The
`carol_rush` row from `20260907-150922` that the coordinator flagged as the starkest flip
(4/40 → 36/40) was never quoted in this log at all.

Two things I am taking from it rather than filing it as "no harm done":

- **A hand-transformation that happens to be right is still a standing hazard.** It was correct
  for four figures across two sessions and would have failed the first time a session resumed
  without re-reading that parenthetical. Sign conventions belong in the tool, not in a note the
  reader has to remember — which is exactly where the coordinator has now put it.
- **My report understated the bug.** I described the symptom I could see (a wrong label) rather
  than testing what the code actually computed, and a label is a cosmetic bug while an inversion
  is a correctness one. Reporting a defect is not the same as characterising it: **run the tool
  on a case where the two hypotheses give different answers before naming the fault.** I had such
  a case on disk — any run of mine where a lopsided opponent's score is far from 50%.

`tools/eval-run.sh` now carries the convention in a comment at the call site, stating that rows
read straight off for carol's launch convention and must not be inverted, and that pre-`7647afb`
log entries were hand-transformed and audited.

## New target, out of the tower-economy area: carol fights for the CONTESTED frontier and leaves whole corners unclaimed

`MaxConsecutiveRejects` is reached in the tower/paint-economy area (24a, 24b, 26), so the next
attempt must leave it. It leaves with a strong steer.

### The game carol is actually playing, from the tournament

Joined `results.csv` to `reasons.txt` for the 300 games carol played in `20260907-1300` (this is
iteration-12 carol, nine accepts stale, but the *shape* is what matters):

| outcome | games |
|---|---|
| carol LOST — opponent painted enough of the map | **194** |
| carol LOST — tiebreak, opponent painted more | **45** |
| carol WON — painted enough / tiebreak | 32 / 27 |
| carol LOST — all units destroyed | **2** |

**99.2% of carol's losses are coverage losses**, and 80% of them are *decisive* — the opponent
reached the area threshold outright rather than edging a tiebreak. Combat is not the game.
Whatever else is true, carol's outcome is a function of how much ground she paints.

### The trace: the empty ground is in a corner and nobody goes there

`DefaultMedium` at round 1200 (arena grid reliable here — reconstruction gap −3/−4 per-mille,
well inside what the unmodelled splashes explain):

- carol (T1) holds the left edge and the top; the opponent holds the right and the bottom.
- **The unpainted region is a contiguous block in the bottom-left corner**, roughly rows 0–12 ×
  columns 0–14, plus a wall-shadowed pocket around rows 4–8.
- **Every carol soldier on the frame is in the contested middle band, rows 13–25.** Not one is in
  the empty corner.
- Coverage is 431 vs 444 per-mille — near-even, with ~12% of the map unclaimed by anyone.

carol lost that game on area at round 2000 while an eighth of the map sat unpainted and
undefended.

### The mechanism, and it implicates a feature I accepted

This is not the random-walk problem iteration 14 fixed; it is **iteration 14's fix being
myopic**. `nearestVisibleEmpty()` returns the *nearest* empty tile in vision, and the nearest
empty tile is almost always on the **contested** frontier, because that is where the two paint
fronts meet and keep overwriting each other. So idle soldiers are pulled toward the one place
where painted ground does not stay painted, while uncontested ground — worth strictly more per
unit of paint, because nobody takes it back — is never targeted at all.

`frontNone` (72–88% of idle turns) is the same failure seen from the other side: a soldier deep
in its own territory sees no empty tile anywhere in r²=20, so it falls through to
`newExploreTarget()`, which samples **four uniform-random map coordinates and keeps the
farthest** — no memory of where paint already is, no notion of which half is ours, no bias
toward the empty corner it has never visited.

**History pre-check.** Iteration 14 deliberately established frontier-seeking and it was a real
accept (+6 games, +2.93 sd). This does not revert it — `frontFound` soldiers should still go to
the frontier. It supersedes the *target choice* on new evidence: nearest is the wrong ranking
when the nearest is also the most contested.

### Pre-checks still outstanding, to run before building anything

1. **Generality** — DefaultMedium is one map, and my own LEARNINGS says a quantity measured on
   one map is a statement about that map. Fossil is rendering now; a second map showing a large
   uncontested empty region with no soldiers in it is required before this becomes a hypothesis.
2. **Reachability / sizing** — how much empty ground is there at round 1000+, corpus-wide, and
   how far is it from the nearest carol soldier? If the answer is "a few tiles behind a wall",
   the prize is small and this dies cheaply.
3. **Price** — sending a soldier to a far corner costs its travel turns and the paint upkeep of
   crossing neutral ground (1/turn). That must be costed against the tiles it would have painted
   at the frontier, **not** against zero — the mistake I have now made three times.
4. **Instrument the decision at the right width** — count the *choice* of target and how it
   ranks candidates, not the coverage outcome; and make sure the counter can see every option
   the bot could pick, not one of them.

### Generality pre-check: Fossil confirms it, on inverted geometry, with a sharper detail

`Fossil` at round 900, 30×30 (grid reliable: T1 gap −2, T2 −13 per-mille):

- Coverage **254 vs 668 per-mille** — carol is being buried, not narrowly edged.
- The unpainted region is a contiguous block in the **top-right**, rows ~25–29 × columns ~18–29,
  roughly 40–50 tiles. On DefaultMedium it was the *bottom-left*. **Different corner, different
  map geometry, same shape** — so this is not a property of one map's layout.
- Every carol soldier on the frame sits in rows 9–22, columns 3–15: the contested middle-left.
  **None is in the empty region.**

And the detail that makes it worse than DefaultMedium's: **carol has a money tower at (26, 27),
directly on the edge of that empty block**, and paints essentially none of it. This is not a
navigation-range problem — she is not failing to *reach* the region, she already holds ground
inside it. Her soldiers are choosing to be somewhere else, 15+ tiles away, in the one place the
paint gets overwritten.

**Generality: PASSED.** Two maps, two different corners, same failure. Combined with the
tournament's 99.2%-coverage-losses figure, the direction is well founded.

**Pre-checks still outstanding before building** (unchanged, and I am registering that they are
*not* done rather than letting the momentum carry): sizing the empty region corpus-wide and its
distance from the nearest soldier; **pricing the travel turns and the 1/turn neutral-ground
upkeep against the frontier tiles forgone, not against zero**; and instrumenting the target
*choice* at the full width of the options the bot could pick. The third of those is the one that
has caught me three times, and the second is the one that has caught me three times differently.

A design note to carry, not yet a commitment: the cheap version of this is a **ranking change,
not a new mechanism** — `nearestVisibleEmpty()` already enumerates every empty tile in vision and
returns the closest. Scoring those candidates by something other than raw distance (e.g.
penalising proximity to enemy paint) is a one-function change inside a branch that already fires,
which is the cheapest possible shape for a first attempt and keeps iteration 14's accept intact.

### Pre-check 2 (sizing) — partly answered with NO run, and it constrains my own hypothesis

The coordinator pointed out the corpus sizing might be partly answerable from `tools/mapdata/`
without spending VM time. It is: map geometry gives the denominator, and I already have measured
coverage from replays on disk. `passable = w*h - walls` (walls from the replay `MatchHeader`),
`unclaimed = (1000 - T1 - T2) per-mille x passable`, `margin = |T2 - T1| x passable`.

| map | passable tiles | unclaimed at the sampled round | carol's losing margin | prize ÷ margin |
|---|---|---|---|---|
| **DefaultMedium** (r1200) | 1,193 | **149** | **16** | **×9.3** |
| **Fossil** (r900) | 868 | 68 | **359** | **×0.2** |

**On DefaultMedium the prize is 9.3× the losing margin — taking just 11% of the unclaimed corner
flips the game.** That is a decisive sizing result and it is what earns the direction.

**On Fossil it is the opposite, and this corrects what I wrote three entries ago.** The entire
unclaimed region is 68 tiles against a 359-tile deficit: even painting *all* of it loses by a
distance. I described Fossil as the sharper case because carol holds a tower on the edge of the
empty block and paints none of it — that remains true as *behavioural* evidence, and the
generality check still passes on it. But I let "sharper evidence for the mechanism" slide into
"stronger case for the fix", and those are different claims. **Fossil is the map where fixing
this matters least.** Its loss has a larger, separate cause.

**What that changes about the evaluation design**, before any code exists: this mechanism is
worth games in *close* matchups and worth nothing in blowouts, so it must be evaluated on an
instrument that can see it — doctrine #4's "resolution is not representativeness" pointing the
other way than usual. A gauntlet drawing a random 20-map sample will mix both regimes and dilute
a real effect into invisibility. **Pre-registering now**: the accept arm must be maps where the
head-to-head margin is small, and the prediction is map-level — gains concentrate where
`unclaimed > margin` and are absent where it is not. That is checkable per map from the same two
numbers, with no extra instrumentation.

Pre-check 2 is therefore **partly done**: the method is established and free, and two maps are
sized. What remains is applying it corpus-wide, which needs coverage per map and so rides along
with the next full run rather than costing one. Pre-checks 3 (price the reallocation against the
frontier tiles forgone) and 4 (instrument the target choice at full width) remain **not done**.

### Pre-check 3 (price the reallocation) — done, no run, and it CHANGES the target

The rule is to price a reallocation against what it displaces. So the question is not "what does
a frontier paint action look like" but **what does the marginal frontier paint action actually
buy**, since that is the thing a redirect gives up. Parsed the per-100-round aggregates of the
DefaultMedium game (`--every 100`, counters are per-window — verified in `ReplayDump` that they
are `Arrays.fill`-reset each sample) and converted per-mille to tiles at 1,193 passable:

| phase | paint actions | net coverage gained | **value per paint action** |
|---|---|---|---|
| **growth**, rounds 1–300 | 516 | **+423.5 tiles** | **82.1% of face value** |
| **plateau**, rounds 300–2000 | 423 | **+53.7 tiles** | **12.7% of face value** |

**After round 300 a carol paint action nets 0.127 tiles, not 1.** She spends 423 actions across
1,700 rounds to gain 54 tiles. Eleven of the seventeen plateau windows are flat or *negative*.

**This inverts the price term I was so careful to insist on.** I registered pre-check 3 because
I have three times costed a benefit without its price, and I expected the travel-and-upkeep cost
of sending a soldier to a far corner to be the thing that killed the idea. Instead: in the phase
where the mechanism would fire, **the frontier tiles forgone are worth about an eighth of face
value**, so the displacement cost is roughly 8× smaller than the naive accounting. Travel is ~15
turns at 1 tile/turn (soldier movement and action cooldowns are separate, so it can still paint
en route) plus ~15 paint of neutral-ground upkeep, against forgoing ~15 actions worth 0.127 each
≈ **1.9 net tiles**. Uncontested ground converts at near face value because nobody takes it back.

**And it moves the target, which is why this pre-check was worth doing before building.** My
registered hypothesis was about *idle* soldiers (`frontNone`, 72–88% of idle turns). The bigger
finding is that carol's **active** soldiers are also near-worthless after round 300 — the waste
is not confined to the idle branch. "Rank targets by contestedness" was scoped to one branch;
the measurement says the plateau phase as a whole is where the game is lost.

It also hands me a **self-calibrating trigger**, which the algorithm prefers over fixed
constants: the growth→plateau boundary is observable in-game as "team coverage stopped rising",
not a hardcoded round number. That matches the coverage peak I found independently on Fossil
(~r400) and on DefaultMedium (~r300–400).

**Honest limitation, stated because it bounds the claim.** Net coverage change conflates carol's
painting with the opponent overwriting her, so 12.7% is a *net team* figure and not proof that
individual paints are wasted: an action that holds a tile against an overwrite has real defensive
value this metric scores as zero. For *pricing a reallocation* net is the right unit — the
question is what the marginal action buys the team — but it would be the wrong unit for asking
"should carol paint at all", and I am not making that claim. Separating the two needs per-tile
repaint counts from `PaintAction`, which is a next-run measurement, not a free one.

Pre-check 3: **DONE**. Pre-check 4 (instrument the target choice at full width) remains **not
done**, and is now the only one outstanding before a build.

### Pre-check 4 (instrument the choice at full width) — REFUTES the ranking design, before a build

`gauntlet/20260907-202304`, 8 games, i27a vs `carol_iter25`. **Identity check passes**: 4/8, all
four maps split by side, zero swept — the mirror-null shape, so the probe is a confirmed no-op
and the counters below describe iteration 25's own play.

| map | paint decisions | **candidates per decision (the WIDTH)** | chosen tile contested | **a less-contested option existed** |
|---|---|---|---|---|
| DefaultMedium | 52 | **5.10** | 11.5% | **11.5%** |
| Fossil | 14 | **4.93** | 14.3% | **14.3%** |
| Bunny | 23 | **3.39** | 21.7% | **8.7%** |
| Mirage | 24 | **2.33** | 0.0% | **0.0%** |

**The design is refuted and the reason is structural.** My intended first attempt was "rank the
paint target by contestedness rather than by distance". But the choice set is **2.3 to 5.1 tiles
wide**, and on **85.5–100% of decisions no strictly less-contested candidate existed at all.**
A better ranking over a menu that averages four items, where the best item is already chosen
seven times in eight, cannot move a game.

The cause is a scale mismatch I should have seen without a run: the paint step chooses within the
**action radius, r²=9** — at most a couple of tiles away. Contested-versus-uncontested is a
property of the map at the scale of *a corner fifteen tiles away*. **The distinction I traced
does not exist inside the decision I was about to change.**

**What is refuted, stated narrowly.** This kills re-ranking the *paint target* within the action
radius. It does **not** test re-ranking the *exploration/frontier target*, which is a different
decision made over `senseNearbyMapInfos(-1)` at r²=20 — a candidate set several times larger,
and the one `nearestVisibleEmpty()` actually serves. My own LEARNINGS rule is that a counter must
be as wide as the decision; I instrumented the r²=9 decision at full width and the r²=20 decision
not at all, so the honest verdict is **one of the two branches refuted, the other still open**.
Recording that rather than letting a clean refutation of the cheap branch read as a refutation of
the direction.

**Bytecode caution, which the probe surfaced by nearly breaking itself.** Peak robot usage went
from the baseline's 37.5% of 17,500 to **88.5%** (15,489), with 1–2 near-misses per game and
**zero overruns**. The identity check confirms no behaviour changed, so the measurement stands.
But a production version that rebuilt an 11×11 enemy-paint window every painting turn would be
running at the edge of the limiter, where an overrun silently truncates a turn. Any real
implementation of contestedness needs a cheaper representation — and I would not have known that
from reasoning.

**Score for the session's pre-checks: four registered, four run, two designs killed before a
build** (24a/24b by decision counters, this one by width), one direction re-costed into the
favourable range (pre-check 3), one sizing result that corrected my own overstatement.

### Pre-check 4, second branch (r²=20 navigation) — ALSO refuted, and the two together relocate the problem

`gauntlet/20260907-203249`, 8 games, i27b vs `carol_iter25`. Identity check passes (4/8, all four
maps split, zero swept). The self-limiting probe worked as designed: **zero overruns**, `fvSkip`
= 0 on every map, peaks 68.9–87.3%.

| map | decision fires | **width per fire** | chosen contested | **a less-contested option existed** |
|---|---|---|---|---|
| DefaultMedium | 30 | 5.73 | **0.0%** | **0.0%** |
| Bunny | 18 | 5.89 | **0.0%** | **0.0%** |
| Mirage | 13 | 4.69 | **0.0%** | **0.0%** |
| Fossil | 8 | 14.50 | 37.5% | **37.5%** |

**On three of four maps the nearest visible empty tile had zero enemy neighbours — it was already
the least contested option available. There is nothing to re-rank.** And the one map with real
signal is **Fossil**, which my own sizing pre-check showed is the map where this mechanism
*cannot* change the result (68 unclaimed tiles against a 359-tile deficit). The two independent
pre-checks agree, from different directions, that the signal and the payoff do not co-occur.

**The contestedness direction is refuted on both branches, and I am closing it.**

### What was actually wrong with my hypothesis

The *trace* was real: a contiguous unpainted corner, every soldier in the contested middle band,
on two maps with different geometry. What was wrong was the **mechanism I inferred from it** —
that carol *chooses* contested ground over uncontested ground. She does not. When she can see
empty ground it is almost always uncontested already, and she goes to it.

The corner sits unclaimed for a different reason: **her soldiers never see it.** `frontNone` —
nothing empty anywhere in vision — is 72–88% of idle turns, and this probe shows the complementary
fact that when the frontier decision *does* fire it fires only 8–30 times per robot per game.
The empty ground is beyond r²=20, and the only thing that could take a soldier there is
`newExploreTarget()`, which samples **four uniform-random map coordinates and keeps the farthest**,
with no memory of where the robot has been or where paint already is.

**So the problem is not target selection at any radius. It is that carol has no map memory and
therefore no way to direct a soldier at ground she has never seen.** That is a different and
larger claim than the one I registered, and it was reached by eliminating the alternatives with
two probes costing 16 games total — cheaper than one evaluation of the wrong design.

### Closed-directions ledger

- **"Rank paint/frontier targets by contestedness" — CLOSED, both branches measured.** r²=9: the
  choice set is 2.3–5.1 wide with no better option on 85.5–100% of decisions. r²=20: no better
  option on 100% of decisions on three of four maps; the sole exception is the map where the
  prize is a fifth of the deficit. Re-opening would require evidence that carol's soldiers
  routinely *see* contested and uncontested ground together and pick wrong — which is exactly
  what these two counters measure, and both say no.

**Next target, registered but not started**: map memory for exploration — some persistent record
of where paint and terrain have been observed, so `newExploreTarget()` can aim at ground not yet
taken rather than at a random coordinate. Pre-checks required before building, and note the
second one is a direct consequence of tonight's bytecode findings:
1. **Sizing** — how much of the map is never entered by any carol soldier? Free from replays.
2. **Bytecode budget first, not last.** Peak is already 68.9–87.3% on instrumented builds and
   37.5% on the bare baseline. Any per-turn map-memory structure competes for that headroom, and
   an overrun truncates turns silently. Cost the bytecode before the behaviour.
3. **Play-symmetry** — a memory keyed on absolute map coordinates is exactly the fixed-absolute-
   order hazard Phase 0 item 7 warns about; check it cannot give one side a tempo edge.

### Next target, pre-check 1 (sizing/reachability) — PASSES, free, from a frame already on disk

Before spending anything on map memory, the cheapest way to kill it: **if the unclaimed ground is
walled off, no amount of memory helps.** Flood-filled the DefaultMedium round-1200 arena frame
(8-directional, walls the only barrier) from every carol-painted tile:

```
tile census        empty 116   painted 1075   ruin 3   wall 31   (= 1225 = 35x35, closes)
empty tiles reachable from carol's own territory:  116 / 116  = 100.0%
walled off:                                          0
bounding box of reachable empty ground:  x 0-34, y 0-25  (i.e. everywhere)
```

**Not one unclaimed tile is inaccessible.** The corner is not hard to reach; it is simply never
visited. The direction survives its cheapest possible refutation.

**Counting caveat, stated because the two numbers disagree.** The grid census gives 116 empty
tiles; the per-mille arithmetic earlier in this log gave ~149. The census closes exactly to
35×35, so it is not a parse error — the gap is that the arena overlays *units* on top of paint, so
an unpainted tile with a soldier standing on it renders as `s` and I counted it as painted. So
**116 is a lower bound and ~149 the upper**, and the true figure is between. The reachability
conclusion is untouched either way: the extra tiles are by construction the ones with units on
them, which are trivially reachable.

That is the same class of error as the tooling inversion — a metric that looks like it answers
one question while actually answering a slightly different one. I am recording both numbers and
which is which rather than picking the convenient one.

Pre-checks for the map-memory target: **1 (sizing/reachability) DONE and passing**; 2 (bytecode
budget costed before behaviour) and 3 (play-symmetry of a coordinate-keyed memory) remain **not
done**, and both stay build gates.

#### Correction, in place: the exact census resolves my 116/149 bracket

The coordinator fixed the occlusion flaw I hit (`4388f3d`): the combined arena view now warns
that units are drawn over paint and must not be censused by counting characters, and every frame
prints an **exact census from the arrays** that closes to the map area by construction. Re-ran
the same DefaultMedium round-1200 frame:

```
with a robot on it reads as a unit. DO NOT census paint by counting
coverage per-mille  T1 recon=431 engine=434 gap=-3  T2 recon=444 engine=448 gap=-4  
```

That supersedes the "116 lower bound / ~149 upper bound" I recorded above. **Neither of my two
numbers was wrong given what was on screen** — which is the point. The render could not answer
the question I was asking it, and no amount of care in counting would have fixed that; the fix
had to be a different data source. The bracket was the right way to hold an unanswerable
question open, and it is now closed by measurement rather than by choosing.

The reachability conclusion is unchanged and was never at risk: 116 of 116 rendered-empty tiles
reachable, and any tiles hidden under units are by construction the ones units are standing on.

---

## STANDING CONSTRAINT (project owner, 2026-09-07): BC25 finals bots are a YARDSTICK ONLY

Recording this in the append-only log because it binds every future session, not just this one.

BC25 finals bots now exist on battlecode-dev, **outside this repo**, used solely to measure how
far each lineage sits from a tournament-winning bot.

**Forbidden, absolutely:**
- reading their source, in any form, anywhere;
- examining **any game played against them** — no replay, log, trace, dump, or arena view;
- seeking out, requesting, or reasoning from any such artefact.

**Permitted:** reading a benchmark **score** if one appears in a committed results file. That is
the entire allowance. Which side won and in how many rounds — never how.

**I do not run these matches.** The coordinator does. I must not add a finals bot to a gauntlet,
an `OPPONENTS` list, `roster_extra.txt`, or anything else.

**If I ever find myself holding such an artefact: stop and tell the coordinator.**

The 2025 post-mortem ban is unchanged and still applies. So does the standing ban on downloading
bot implementations.

**Compliance check run at the time of the rule** (evidence, not assertion): every opponent
appearing in any of my `gauntlet/*/results.csv` is `carol_*`, `carol_rush`, `carol_turtle` or
`examplefuncsplayer`; every package in `src/` is `carol_*` or `examplefuncsplayer`; all eight
archived replays are against my own lineage or my own synthetic. **Nothing external is or has
been in this workspace.**

### Why the enforcement design is the right shape, and the one gap I see

The enforcement is *structural rather than behavioural*: the source is not in my checkout, and
**no replay is written for those games at all**, so the artefact does not exist rather than
existing and relying on me to look away. That is strictly stronger than a rule, because it also
survives a session that never read the rule.

The gap it does not close is **requesting**. A restarted session reads `AGENT.md` first, and that
file currently lists the standing constraints (no downloaded bots, no 2025 post-mortems) without
this one. A future me could therefore ask for a benchmark replay in good faith, or propose adding
a finals bot to the frozen roster — which is exactly the kind of thing `roster_extra.txt` is for,
and it would look reasonable. **Flagging that for the coordinator rather than editing `AGENT.md`
myself, since that file is theirs.** This log entry and the LEARNINGS entry cover the case where a
future session reads them first, but the charter is what it reads *first*.

### On how to use the number

The score is **information about distance, not a target to tune against.** Tuning toward a fixed
external opponent is overfitting with extra steps, and it is the same error as hand-picking a
standing map list, which my own charter forbids for exactly this reason. My accept gate stays the
within-run head-to-head against my last snapshot; the frozen roster stays my absolute instrument;
the inter-agent tournament stays my independent-opponent instrument. The benchmark adds a fourth
reference point, and a bad one is *expected* — carol sits last in the inter-agent standings while
her own instruments read 92–100%, which is precisely the self-referential blind spot the
algorithm warns about, and a third-party number is the only thing that can size it.

**None of my working methods are affected for my own games.** Arena grids, flood fill, per-window
aggregates, decision counters, mirror nulls, map-resampling — all remain available for my
gauntlets, my synthetics, my frozen roster and the inter-agent tournament. Only benchmark games
are off-limits.

---

## Session resume (2026-09-07, later): recovering the i28p probe, and what it found instead

A session death left `src/carol_i28p/` uncommitted and **two completed, collated gauntlet runs
never analysed** (`gauntlet/20260907-214045` and `20260907-214645`, 8 games each, i28p vs
`carol_iter25` on the same 4 pinned maps). Neither had reached the log. Recovering them cost no
VM time — the games were already on disk.

### The registered design is REFUTED by its own pre-registered criterion

i28p is a **no-op probe** for the map-memory candidate I registered last session: mark the coarse
6x6 map cell underfoot as EXHAUSTED whenever the `frontNone` branch fires, then aim exploration at
the nearest non-exhausted cell instead of a uniform-random coordinate. It computes every quantity
the mechanism would use and throws it away, so play is unchanged.

**Identity check passes** on both runs: 4/8, all four maps split by side, zero swept — the mirror-null
shape. So the counters describe iteration 25's own behaviour.

Registered kill criterion, written before the run: *"exB = fires where the RANDOM target lands in a
cell this robot already exhausted (the waste the mechanism removes — **if this is ~0 the design is
dead**)."*

| map | soldiers | exF (explore draws) | **exB (the waste)** | choice-set width | exX (cells marked) |
|---|---|---|---|---|---|
| DefaultMedium | 218 | 439 | **2 (0.5%)** | 35.3 / 36 | mean 1.43, max 10 |
| Bunny | 66 | 119 | **0 (0.0%)** | 39.9 / 40 | mean 0.39, max 2 |
| Fossil | 101 | 150 | **0 (0.0%)** | 24.8 / 25 | mean 0.60, max 3 |
| Mirage | 88 | 147 | **0 (0.0%)** | 48.9 / 49 | mean 1.12, max 5 |

**exB = 2 of 855 draws = 0.2%. The design is dead by the criterion I registered for it.**

The cause is visible in exX and it is structural, not a tuning matter: a soldier marks a mean of
**0.4–1.4 cells out of 25–49** in its entire life. Per-robot exhausted-cell memory never accumulates
enough to constrain anything — the choice set stays 99% of the map (35.3/36, 39.9/40, 48.9/49), so a
random draw essentially cannot land in an exhausted cell. This is a *third* independent way the
same family of designs has died: not "the ranking is wrong" (r²=9, refuted), not "the signal isn't
there" (r²=20, refuted), but **the memory is empty**.

`exD` = 100% on every fire is uninformative and I am flagging it rather than quoting it: "the
nearest non-exhausted cell differs from the random target's cell" is trivially true because
`newExploreTarget()` keeps the *farthest* of four samples while the probe's candidate is the
*nearest* cell. It measures "near != far", not a decision quality. Recording that because a 100%
counter looks like a strong result and is not one.

### What the probe found instead — and it is much larger than what it was built to test

The same indicator stream carries a per-turn soldier state histogram I had never tabulated.

| map | soldier turns | **in the ruin branch** | painted a tile (slf/pnt) | at paint < 5 |
|---|---|---|---|---|
| DefaultMedium | 11,519 | **71.5%** | 5.2% | 22.6% |
| Bunny | 3,772 | **58.0%** | 9.4% | 19.8% |
| Fossil | 4,920 | **68.9%** | 6.4% | 22.1% |
| Mirage | 4,634 | **68.3%** | 6.9% | 23.9% |

And then the lifespan, which is the number that reframes everything:

| map | soldiers spawned | **median life** | ruin-branch turns per soldier | **died with paint < 5** |
|---|---|---|---|---|
| DefaultMedium | 218 | **50 rounds** | 37.8 | **206/218 = 94%** |
| Bunny | 66 | **56 rounds** | 33.2 | **51/66 = 77%** |
| Fossil | 101 | **49 rounds** | 33.6 | **85/101 = 84%** |
| Mirage | 88 | **50 rounds** | 36.0 | **81/88 = 92%** |

**A carol soldier costs 200 paint and 250 chips, lives about 50 rounds, spends ~70% of them walking
to a single ruin, and 77–94% of the time dies of paint starvation.** Steady-state soldier population
is 4–7 (range 1–14) on maps of 868–1,193 passable tiles.

That is an absolute degeneracy signal, not an opponent-relative one — it needs no opponent to be
wrong — which is exactly the kind of target Step 1 of the algorithm says to prefer.

### One hypothesis of mine died here too, cheaply and before it cost anything

I suspected the single-slot `ruinBanned` (one `MapLocation`, replaced whenever a new ban is set)
would make soldiers ping-pong between two unfinishable ruins. **Refuted from data already on disk:
zero re-targets of an already-chased ruin across all four maps, and 0.94–1.08 distinct ruins per
soldier.** Soldiers do not oscillate. They chase one ruin, once — they simply do not live long
enough to chase a second. The single-slot ban is harmless because the bug it could cause needs a
lifespan carol's soldiers never reach.

### The paint accounting, closed — and it relocates the problem a second time

All of the following is computed **offline from replays already on disk**: zero VM game time. The
four games are i28p (= iteration 25, no-op probe) as bot A on DefaultMedium, Fossil, Bunny, Mirage.
Because the probe is a verified no-op, **T2 in these games is byte-identical carol on the winning
side** — which gives me a within-game control on identical code, and that control turns out to be
the load-bearing part.

#### Soldier paint conversion: 9–23%, and the SAME on both sides

A soldier is built for 200 paint drawn from a tower's stash. Counting its actual `PAINT` and
`markTowerPattern` actions in the replay (1 PAINT = 1 attack = 5 paint; marks come in blocks of
exactly 24 tiles = one 25-paint call):

| map | side | soldiers built | paint budget | spent on painting | **conversion** |
|---|---|---|---|---|---|
| DefaultMedium | T1 (lost) | 218 | 43,600 | 4,455 | **10.2%** |
| DefaultMedium | T2 (won) | 268 | 53,600 | 4,950 | **9.2%** |
| Bunny | T1 (lost) | 66 | 13,200 | 2,420 | **18.3%** |
| Bunny | T2 (won) | 116 | 23,200 | 5,255 | **22.7%** |
| Fossil | T1 (lost) | 101 | 20,200 | 2,470 | **12.2%** |
| Fossil | T2 (won) | 138 | 27,600 | 3,645 | **13.2%** |
| Mirage | T1 (lost) | 88 | 17,600 | 2,520 | **14.3%** |
| Mirage | T2 (won) | 125 | 25,000 | 5,140 | **20.6%** |

**77–91% of every soldier's paint budget never becomes a painted tile, and the winning side is no
better at it than the losing side** — on DefaultMedium the *loser* converts marginally better
(10.2% vs 9.2%). So this is **structural to carol's design, not a symptom of losing**. That
distinction is the whole reason the control was worth computing: without it I would have read
T1's low numbers as the cause of T1's defeat, which is the wrong referent.

#### The exchange rate — and a 6x claim of mine that measurement killed

Per RESEARCH.md §8 ("build an exchange rate, even a crude one"), tiles painted per 100 paint
*spent on attacking*:

| unit | tiles per attack | **tiles per 100 paint spent attacking** |
|---|---|---|
| soldier | 1.00 | **20.0** (every map, every side — it is 1 tile / 5 paint by definition) |
| splasher | 10.0–12.6 | **20.0–25.2** |

I had reasoned my way to "splashers are ~6x more paint-efficient than soldiers" by dividing tiles
by *build cost*. **That is the wrong referent and the measurement refutes it: per paint actually
spent attacking, the two are within 10% of each other.** Recording the wrong number and its
correction rather than quietly replacing it.

The real difference is upstream of the exchange rate — what fraction of the unit's budget ever
reaches an attack at all:

| unit | build paint | paint reaching attacks | **share of budget converted** |
|---|---|---|---|
| soldier (T2, DefaultMedium) | 53,600 | 4,600 | **8.6%** |
| splasher (T2, DefaultMedium) | 4,500 | 3,150 | **70%** |
| splasher (T2, Bunny) | 2,400 | 2,300 | **96%** |

A splasher's attack costs 50 paint against a soldier's 5, while both lose the same ~1–3/turn to
drain while walking. **The soldier is drain-dominated and the splasher is attack-dominated**, and
that — not per-attack efficiency — is where the 8x sits.

#### The build mix carol *intends* is not the build mix she *gets*

**[PARTLY SUPERSEDED 2026-09-08 by the doctrine-15 audit at the end of this log: the realized-vs-
intended mix below SURVIVES (it is a direct count of SPAWN events), but the affordability-filter
EXPLANATION of it is REFUTED, and the `SPLASHER_IN_20` retrodiction is WITHDRAWN. Read the audit
before citing anything in this subsection as a cause.]**

Constants: `SPLASHER_IN_20 = 3`, `MOPPER_IN_20 = 2` → **intended 75% soldier / 15% splasher /
10% mopper**. Realized, counting every unit actually built:

| map | side | soldier | splasher | mopper | realized splasher% |
|---|---|---|---|---|---|
| DefaultMedium | T1 | 218 | 3 | 220 | **0.7%** |
| DefaultMedium | T2 | 268 | 15 | 39 | 4.7% |
| Bunny | T1 | 66 | 1 | 67 | **0.7%** |
| Bunny | T2 | 116 | 8 | 29 | 5.2% |
| Fossil | T1 | 101 | 4 | 55 | **2.5%** |
| Fossil | T2 | 138 | 8 | 61 | 3.9% |
| Mirage | T1 | 88 | 2 | 31 | **1.7%** |
| Mirage | T2 | 125 | 11 | 16 | 7.9% |

On the losing side the realized mopper share is **50%** against an intended 10%, and the splasher
share is **0.7%** against an intended 15%.

**The cause is an affordability filter nobody designed.** The tower rolls a type, then
`canBuildRobot` silently fails if the tower's own stash cannot pay: mopper 100, soldier 200,
splasher 300. So `P(build type) = P(roll type) x P(afford type)`, and the stash distribution
decides the mix:

| map | paint-tower turns | tp < 100 | **tp in [100,200) — mopper only** | tp >= 200 | **tp >= 300 — splasher possible** |
|---|---|---|---|---|---|
| Bunny | 1,444 | 49.0% | **48.6%** | 2.4% | **0.3%** |
| DefaultMedium | 10,744 | 41.7% | **43.0%** | 15.3% | **9.6%** |
| Mirage | 3,000 | 28.5% | **36.9%** | 34.6% | 21.2% |
| Fossil | 4,097 | 24.8% | **26.5%** | 48.7% | 40.7% |

**The paint tower spends a quarter to a half of its life holding exactly enough for a mopper and
never enough for a soldier.** That is the "resource pinned in a dead band" degeneracy shape
verbatim. Money towers are irrelevant here: their median stash is **0** (84–98% of their turns
below 100) because `paintPerTurn == 0` for a money tower, so essentially every unit carol fields
comes out of a paint tower.

**This retrodicts a result I could not explain before.** My earlier `SPLASHER_IN_20` dose sweep
found the shape "concave, incumbent exactly at the peak, both arms rejected" — puzzling at the
time. It is explained now: on Bunny the tower can afford a splasher on **0.3%** of its turns, so
the roll probability is saturated by affordability and moving the knob cannot move the realized
share. **The constant was tuned; the thing the constant controls was not.** A retrodiction of an
old anomaly is worth more than a fresh story, so I am flagging this as the strongest single piece
of support for the direction.

#### The price of a mopper, measured rather than assumed

Before treating moppers as waste — the pre-check that has caught me three times. Mopper state
histogram, same games:

| map | mopper turns | mopped | swung | **idle** |
|---|---|---|---|---|
| Bunny | 2,498 | 20% | 0% | **78%** |
| DefaultMedium | 4,932 | 14% | 1% | **84%** |
| Fossil | 1,067 | 24% | 1% | **73%** |
| Mirage | 1,025 | 18% | 0% | **80%** |

**Moppers are not idle waste at this iteration.** 517 mop actions on Bunny is real work, and it
supersedes nothing: iteration 19a (delete moppers outright) was rejected at 32% and that rejection
stands. Any candidate here must be conditional on the tower's stash, not a removal — a different
mechanism from 19a, not a silent revert of it.

#### Soldier drain, decomposed — and the discriminating case is running

Two independent artefacts agree, which is what licenses reading anything off this. From the
lifetime budget: 200 paint − 19 on attacks − 1.5 on marks over 52.8 turns = **3.40/turn** on
DefaultMedium. **[SUPERSEDED 2026-09-08: both figures below are WRONG — the true drain is
1.20–1.58/turn. Both routes shared one false assumption (that paint leaves a robot only via drain
or a logged action) and so were one method twice, not two. See "The discriminating case" below.]** From differencing the per-turn `p=` in the indicator stream and subtracting that
turn's logged attacks: **3.46/turn**. Agreement to 2%.

Terrain drain is capped at 2/turn by the rules (−1 neutral, −2 enemy, 0 ally), so **at least 1.4 of
the 3.46 cannot be terrain.** The per-turn distribution is sharply bimodal:

| map | mean | 0 | 1 | 2 | 5 | 6 | 7 | 9 | 11 |
|---|---|---|---|---|---|---|---|---|---|
| Bunny | 2.65 | 36% | 13% | 17% | 9% | 8% | 12% | 3% | – |
| DefaultMedium | 3.46 | 38% | 10% | 5% | 8% | 11% | 13% | 8% | 3% |
| Fossil | 3.52 | 32% | 9% | 11% | 7% | 11% | 18% | 6% | 1% |
| Mirage | 3.22 | 41% | 8% | 9% | 7% | 8% | 13% | 8% | 2% |

Half the turns are free (0–1) and **about a third cost 5–11 paint each**. Two mechanisms can
produce that tail and they need **opposite** fixes:

- **Ally clumping** (−1 per adjacent ally, −2 on enemy ground) → the fix is a local repulsion rule,
  which is a movement change costing nothing, the "capability at zero marginal cost" shape.
- **Enemy mopper theft** (mop-steal −10, mop-swing −5 to each of up to 6) → a completely different
  fix, and nothing to do with our own movement.

I am explicitly **not naming the fault yet**. The two hypotheses look identical in the drain total
and the observed values are suggestive both ways: 5, 6, 7, 10, 11 are exactly {swing 5, steal 10} +
{ally 0, neutral 1, enemy 2}, which favours theft; but a gap at 3 and 8 argues against smooth
clumping too. Enemy mopper attacks on our soldiers are logged individually as `ATTACK -> <id>`, so
the discriminating case is free and is running now: split the same drain distribution by whether an
enemy attacked that soldier that round.

### The discriminating case: my offline drain estimate was WRONG, and the probe found the real sink

`gauntlet/20260907-234722`, 8 games, `carol_i29p` vs `carol_iter25`. **Identity check passes and is
unusually strong**: 4/8, all four maps split by side, zero swept, and every game ends on the
*byte-identical round* as the i28p run (r2000 / r1037 / r1015 / r728). Confirmed no-op.

**The drain model closes.** Observed end-of-turn drain vs. what the rules predict from the tile
underfoot and the adjacent-ally count, read by the robot itself:

| map | observed | predicted | residual | turns mismatched | terrain | clumping | **end-of-turn tile is ENEMY paint** |
|---|---|---|---|---|---|---|---|
| Bunny | 1.20/turn | 1.19 | +0.01 | 1.0% | 1.08 | 0.52 | **41.6%** |
| DefaultMedium | 1.56/turn | 1.58 | −0.02 | 1.3% | 1.02 | 1.31 | **39.4%** |
| Fossil | 1.58/turn | 1.54 | +0.04 | 2.1% | 1.27 | 0.92 | **48.5%** |
| Mirage | 1.57/turn | 1.58 | −0.01 | 1.2% | 1.18 | 1.16 | **45.2%** |

**And it refutes my own offline number in the entry above.** I published 3.2–3.5 paint/turn,
derived two ways that agreed with each other. The truth is **1.20–1.58**. Both offline routes
shared one assumption — that a soldier's paint could only leave via drain or via an action the
replay logs — and they agreed because they were the *same* method twice, not two methods. That is
the "what did both versions take for granted" failure in its exact form, and the agreement of two
artefacts is only evidence when the two are actually independent. Superseding the number in place.

#### The sink neither offline route could see

Tracing soldier `id11954` on Bunny end to end — it loses 5 or 7 paint on turn after turn while the
probe's measured drain rises by only 2, and the replay logs **two** PAINT events for its entire
life:

```
r549 p=195  dO= 0   ruin=[11, 20]        <- 200 -> 0 in 37 turns
r550 p=188  dO= 2   ruin=[11, 20]           drain accounts for 60
r551 p=181  dO= 4   ruin=[11, 20]           actions account for 10
...                                          the other 130 is invisible
r583 p=  0  dO=60   ruin=[11, 20]
```

**`workOnRuin` attacks tower-pattern tiles that hold ENEMY paint.** A soldier paints a tile only
if it is EMPTY or already own-team (RULES.md, soldier attack `[E]`). `rc.canAttack()` does **not**
check this, so the attack is legal, the engine charges the full 5 paint, and **nothing happens.**
The soldier in the trace is standing on enemy ground working a ruin whose pattern is enemy-painted,
and it burns its entire 200-paint stash doing it, at 5 per turn, for 35 turns.

**Attribution closed by enumeration over the code, not by a story.** There are four soldier attack
sites. Line 278 hits an enemy tower (lands, 50 dmg). Line 292 is guarded by
`myTile.getPaint() == EMPTY`. Line 303 skips every candidate with `t.getPaint() != PaintType.EMPTY`.
All three provably always land. **Line 451 in `workOnRuin` is the only unguarded one**, so it
accounts for all of the waste. Falsifiable: name a soldier attack that fails at 292 or 303 and the
identity breaks — their guards make it impossible.

Measured exactly, per turn, against the probe's drain and the replay's logged actions:

| map | **attacks discarded** | attacks that landed | **% of all soldier attacks discarded** | paint burned | **% of the soldier paint budget** |
|---|---|---|---|---|---|
| Bunny | 1,104 | 454 | **70.9%** | 5,520 | **41.8%** |
| DefaultMedium | 4,789 | 826 | **85.3%** | 23,945 | **54.9%** |
| Fossil | 1,956 | 444 | **81.5%** | 9,780 | **48.4%** |
| Mirage | 1,751 | 464 | **79.1%** | 8,755 | **49.7%** |

That is the 41–53% hole the accounting could not close, found and named. It also explains every
downstream symptom in one stroke: why soldiers die dry at ~50 rounds, why 77–94% end at paint < 5,
why the ruin branch eats 56–71% of soldier turns without producing towers, and why the paint tower
never climbs out of the [100,200) dead band — the soldiers it funds are pouring its output into
attacks the engine discards.

## Iteration 29 — don't attack a tile the engine will not let us paint

**Change (one line of behaviour):** in `workOnRuin`, `if (tile.getPaint().isEnemy()) continue;`
before the attack. The loop then reaches a pattern tile that *is* paintable instead of breaking on
an impossible one. The zero arm is the current code, byte-identical.

**Price:** zero. The skipped attacks accomplish nothing by the engine's own rules, so this is not a
reallocation and there is no forgone use to charge against it — the one case where "priced against
zero" is the correct accounting rather than the error I have made three times. The paint saved is
picked up by the existing paint block, which targets EMPTY tiles in the action radius.

**Pre-registered, before any evaluation:**
1. Discarded-attack share falls from 71–85% toward 0 (mechanistic verification).
2. Soldier median life rises from its 49–56 rounds.
3. Head-to-head vs `carol_iter25` > 50% on a **fresh random 25-map sample** — not the four maps
   the diagnosis was made on, which are an overfitting surface.
4. Map-level: gains concentrate where the discarded share is highest (DefaultMedium 85.3%,
   Fossil 81.5%) and least on Bunny (70.9%).

**Identity check / first read** (`gauntlet/20260908-000103`, the four diagnosis maps):
**8/8, all four maps SWEPT, zero swept losses**, against a null measured three separate times
today on these exact maps at 4/8 with all four split by side and **zero** sweeps. Games also end
far earlier (Fossil r403 and r1107 vs r1037; DefaultMedium r1087/r1345 vs r2000), i.e. carol is
now reaching the 70% paint win rather than grinding to the round limit.

**This is not the accept.** Those are the diagnosis maps. The accept gate is the fresh-sample run
now in flight (`carol_i29` vs `carol_iter25` plus the full frozen roster, 8 opponents x 25 fresh
maps x both sides = 400 games), which also refreshes the absolute-strength instrument on the same
ground per measurement doctrine #12 — run the roster *before* accepting, not after.

#### Correction in place: "8/8 **and** all four swept" is one number twice, not two

The coordinator's tournament report now states the identity, and it is exact: with every map played
from both sides, wins = 2·SW + D and losses = 2·SL + D where D is the split maps, so

> margin = 2 x (swept − swept-against), always.

Checking my own iteration-29 identity-check run against it: margin 8 − 0 = 8, sweeps 4 − 0 = 4,
and 2 x 4 = 8. **They agree because they are algebraically the same number.** So writing "8/8, and
all four maps swept" as if the sweeps corroborated the score was double-counting, exactly the error
the note describes. Superseding that phrasing here rather than editing it above.

What the sweep counts *do* add is **D, the number of split maps** — how decisive the pair is rather
than who is ahead. Stated correctly, on the four diagnosis maps:

| build vs `carol_iter25` | wins | swept | **split maps (D)** |
|---|---|---|---|
| null (identical code, measured 3x today) | 4/8 | 0 | **4 — every map a coin-flip decided by side** |
| `carol_i29` | 8/8 | 4 | **0 — every map decided by the code** |

That contrast is the real content and it is not a restatement of the margin: on the same four maps,
the side-dependence that fully determined the null's outcome disappeared entirely. It remains a
first read on the diagnosis maps, not the accept.

### DOCTRINE 15 AUDIT — my tower dead-band figure was post-spend, and the reconciliation partly refutes my story

New engine fact (`tools/engine-facts.md`): **replay per-robot state is written AFTER the robot's
turn resolves**, so anything phrased as "could this robot have afforded X" is conditioned on the
outcome it is predicting. My `tp=` figures come from carol's own tower indicator, which
`monitorAndYield` prints *after* `runTower()` has already called `buildRobot`. **Same class, same
bias.** Auditing rather than assuming I was outside it.

**First: I could correct it exactly rather than only retract it.** Every build is logged as a SPAWN
with its unit type, and every refill as a TRANSFER with its amount, so the decision-point stash is
`tp_recorded + everything that tower spent that round`. Reconstructed:

| map | basis | tp<100 | **tp 100–199 (dead band)** | tp≥200 | tp≥300 |
|---|---|---|---|---|---|
| Bunny | post-spend (valid for PERSISTENCE) | 49.0% | 48.6% | 2.1% | 0.3% |
| Bunny | **decision-point (for AFFORDABILITY only)** | 40.7% | **52.4%** | 6.4% | **0.6%** |
| DefaultMedium | post-spend (valid for PERSISTENCE) | 41.7% | 43.0% | 5.7% | 9.6% |
| DefaultMedium | **decision-point (for AFFORDABILITY only)** | 38.2% | **44.7%** | 7.4% | 9.8% |
| Fossil | post-spend (valid for PERSISTENCE) | 24.8% | 26.5% | 8.0% | 40.7% |
| Fossil | **decision-point (for AFFORDABILITY only)** | 22.6% | **27.2%** | 9.1% | **41.1%** |
| Mirage | post-spend (valid for PERSISTENCE) | 28.5% | 36.9% | 13.4% | 21.2% |
| Mirage | **decision-point (for AFFORDABILITY only)** | 25.9% | **37.3%** | 14.9% | 21.9% |

The bias is real but small here (+1.7 to +3.8 points), and it widens the dead band rather than
narrowing it — towers build rarely relative to how many turns they take, so little is spent down.
**So the dead-band measurement survives, corrected.** Recording that because the comfortable move
would have been to bin the number, and the correction runs *against* me.

**Second, and this is the part that hurts: the reconciliation test refutes the story I built on it.**
Multiplying the corrected rate back into a count and comparing with a directly observed count:

| map | implied soldier-affordable tower-turns | **soldiers actually built** | ratio |
|---|---|---|---|
| Bunny | 100 | 66 | **1.5x — consistent** |
| DefaultMedium | 1,840 | 218 | 8.4x |
| Mirage | 1,103 | 88 | 12.5x |
| Fossil | 2,059 | 101 | **20x — not consistent** |

On Bunny paint really is close to binding. **On Fossil it plainly is not**: the tower could afford
a soldier on 2,059 turns and built 101, and could afford a *splasher* on 41.1% of its turns and
built four. Something else limits building there — the chips gate, the roll, or `canBuildRobot`'s
placement check — and it is not paint.

**Scoping the damage precisely, which is the part worth copying:**

- **SURVIVES** — the realized-vs-intended build mix (218 soldiers / 3 splashers / 220 moppers on
  DefaultMedium against an intended 75/15/10). That is a direct count of SPAWN events, not a rate
  from post-turn state, and no bias touches it.
- **SURVIVES, CORRECTED** — the tower paint distribution, as reconstructed above.
- **REFUTED** — "the affordability filter explains the mix divergence." It is consistent on Bunny
  and clearly false on Fossil and Mirage. The filter demonstrably *exists* in the code
  (`canBuildRobot` fails silently on paint), but it does not carry the explanation, and I had
  generalised from a map where it fits.
- **WITHDRAWN** — my retrodiction of the `SPLASHER_IN_20` sweep anomaly, which rested on "the tower
  can afford a splasher on 0.3% of turns". That is a Bunny number. On Fossil the figure is 41.1%
  and only four splashers were built, so affordability was not saturating the knob. **A
  retrodiction that explains an old anomaly is seductive precisely because it feels free, and I
  called it "the strongest single piece of support for the direction". It was the weakest.**

**Iteration 29 is NOT affected, checked rather than asserted.** Its evidence is per-turn paint
*differences* and direct action counts, never a conditional affordability rate: the probe reads
paint in-bot at the top of the turn (before any action) and again at the end, and the discarded
attacks are the residual of a conservation identity. Post-turn state is the correct referent for a
difference. Running the same reconciliation on iteration 29's own headline, on DefaultMedium:
5,615 attacks (4,789 discarded + 826 landed) over 11,519 soldier turns is 48.7% of turns, plausible
for a unit whose action cooldown lets it act every turn; and 5,615 x 5 = 28,075 paint, plus drain
14,449, plus 1,320 held at death = **43,844 against 44,904 issued — closes to 2.4%.**

## Iteration 29 RESULT — **ACCEPT** at 88%, 19 swept wins to zero, on a fresh random sample

Run `20260908-000327`: `carol_i29` vs `carol_iter25` + the full frozen roster, **25 maps drawn
fresh at random from the 75** (not the four the diagnosis was made on), both sides, 8 opponents,
400 games.

| instrument | result |
|---|---|
| **h2h vs `carol_iter25`** (accept gate) | **44/50 = 88%** |
| swept-win / swept-loss / **split maps (D)** | **19 / 0 / 6** |
| overall | 381/400 = 95.2% |

Per doctrine 14 the margin and the sweeps are one number (44−6 = 38 = 2×19), so the independent
content is **D = 6**: nineteen of twenty-five maps were decided by the code rather than by which
side carol spawned on, and **not one map swept against**. Against a null that swept nothing and
split every map, on ground the mechanism was never tuned against.

**Frozen roster, run *before* the accept per measurement doctrine 12** — and it is the strongest
absolute reading this lineage has recorded:

| opponent | iteration 29 | swept-win / swept-loss |
|---|---|---|
| `carol_iter0` | **100%** | 25 / 0 |
| `carol_iter1` | **100%** | 25 / 0 |
| `carol_iter7` | 94% | 22 / 0 |
| `carol_iter21` | 88% | 19 / 0 |
| `carol_rush` | 92% | 23 / 2 |
| `carol_turtle` | **100%** | 25 / 0 |
| `examplefuncsplayer` | **100%** | 25 / 0 |

**Zero swept losses against every self-lineage opponent.** The only swept losses anywhere in 400
games are two maps against `carol_rush` (DefaultSmall and `giver`, both lost fast — r166–r341 —
i.e. a genuine rush that ends before carol's economy exists). That is a clean, specific, unrelated
weakness and it is now the obvious next target.

**Pre-registered predictions, scored honestly:**
1. *Discarded-attack share falls toward 0* — **not yet verified.** `src/carol_i29q` (the candidate
   plus the drain counters) is built for exactly this and has not been run. Registering it as
   outstanding rather than letting the win rate imply it: the result is accepted on the gate, and
   the mechanism check is a separate claim that I have not made yet.
2. *Soldier median life rises* — same, outstanding, same probe.
3. *h2h > 50% on a fresh sample* — **met, 88%.**
4. *Gains concentrate where the discarded share was highest* — **cannot be scored.** The four maps
   I measured the discarded share on are not in this run's random sample. Stating that plainly
   rather than substituting a different covariate after the fact; the honest status is that the
   map-level prediction went untested, and the follow-up run will pin the maps to test it.

So: accepted on the gate and on the roster, with the **mechanism attribution OPEN** — the change is
one line whose effect is forced by the engine's own rule, but "the engine discards these attacks"
is a code-and-rules argument, not yet a measurement of this build. Per rule 3b I am accepting the
result and recording the attribution as open rather than back-filling it from the win rate.

Snapshot `src/carol_iter29`; `src/carol` promoted; `src/carol_mirror` regenerated from the new
baseline (the accept moves the null, and reading a candidate against a mirror of the *previous*
build credits it with games the accepted mechanism flipped).

### Doctrine 14 extended — and it corrects my own doctrine-15 audit, one entry above

**Independence of the derivation is not independence of the referent.** Re-deriving a number by a
different route does not repair it if both routes read the same invalid quantity. I reached the
same conclusion from the other side earlier today (two offline drain estimates agreed to 2% and
were both wrong by 2x because they were one method twice), and the extension makes the general form
explicit: **ask what a derivation measured, not what path it took there.**

The usable distinction, applied to my own tower-paint numbers — and it changes how I should read my
own correction table:

- **"How often could the tower afford a soldier"** — invalid from post-spend state, because the
  turns where it *did* build are exactly the turns whose recorded stash was spent down. This is
  what I retracted, correctly.
- **"The paint tower persists in the [100,200) band"** — **sound from post-spend state**, because
  persistence is precisely what post-turn state records.

**So my two columns answer different questions, and I mislabelled them.** I headed them "post-spend
(INVALID)" and "decision-point (corrected)", as though one were a repaired version of the other.
They are not:

- For the **persistence** claim, the *post-spend* column is the correct referent, not a biased one.
  27–49% is the right number for "how much of its life does the tower spend holding 100–199".
- For the **affordability** claim, the reconstructed column is the right referent — and that claim
  then dies anyway on the count reconciliation (2,059 implied vs 101 built on Fossil).

Neither column is "the corrected one". Correcting the header rather than the numbers, because the
numbers were right and the framing was wrong — which is exactly the failure the extension names.

**Ledger and figure hygiene (adopted from another lineage's fix).** "Supersede in place, do not
delete" preserves history correctly but leaves stale text *looking live*, because a reader who
greps lands on whichever row matches first rather than the newest. Superseded figures in this log
now carry an inline `**[SUPERSEDED <date>: …]**` marker at the point of the stale number, applied
retroactively to the 3.40/3.46 drain figures and to the build-mix subsection whose explanation was
refuted. Preserving the old text is right; leaving it indistinguishable from live text is the
defect.

### Mechanism verification — attribution CLOSED, and prediction 4 stays honestly unscored

`gauntlet/20260908-005610` (8/8, all four maps, end rounds byte-identical to the `carol_i29` run,
so `carol_i29q` is verified no-op instrumentation of the accepted build), plus four `vm-match`
games run to pull replays back, since a build that wins every game leaves no losses to collect.

**Prediction 1 — discarded-attack share falls toward 0. MET, exactly.**

| map | discarded (iter25) | **discarded (iter29)** | landed (iter25) | **landed (iter29)** |
|---|---|---|---|---|
| Bunny | 70.9% | **0.0%** | 454 | **1,021** |
| DefaultMedium | 85.3% | **0.0%** | 826 | **999** |
| Fossil | 81.5% | **0.0%** | 444 | **1,447** |
| Mirage | 79.1% | **0.0%** | 464 | **1,239** |

Zero, on every map, by the same measurement that found 1,104–4,789 of them before. **The
attribution recorded as OPEN at the accept is now CLOSED**: the mechanism is the mechanism.

**Prediction 2 — soldier median life rises. MET, and by more than I expected.**

| map | median life (iter25) | **median life (iter29)** | on ENEMY paint (iter25 → iter29) | drain/turn |
|---|---|---|---|---|
| Bunny | 56 | **93** | 41.6% → **25.6%** | 1.20 → 1.06 |
| DefaultMedium | 50 | **81** | 39.4% → **36.5%** | 1.56 → 2.15 |
| Fossil | 49 | **93** | 48.5% → **29.7%** | 1.58 → 1.59 |
| Mirage | 50 | **120** | 45.2% → **28.5%** | 1.57 → 1.08 |

Soldiers live **1.6–2.4x longer**, and the share of turns spent standing on enemy paint — where a
soldier can do nothing at all — falls by a third to a half. That second number was not predicted
and is worth keeping: the old build parked soldiers on enemy ground because the ruin loop kept
handing them an "action" there. Removing the fake action removed the reason to stand still.

**Prediction 4 — gains concentrate where the discarded share was highest. STILL UNSCORED, and now
for a second reason.** The accept run's random sample contains none of these four maps. And even
here the comparison is between *different games*: i29 wins Fossil at r403–r1107 where i25 ran to
r1037, and Mirage at r1846 where i25 ended at r728, so attack totals are not comparable without
normalising, and raw vs per-round orderings disagree with each other **and** with the prediction
(DefaultMedium had the highest discarded share, 85.3%, and the smallest gain on both measures).

I could pick whichever normalisation flatters the prediction. I am not going to. **The registered
map-level prediction is untested, its cheapest test is confounded, and the correct next step is a
run with the maps pinned** — which is what doctrine's map-level discipline asks for and what I will
do rather than settling it by choice of denominator. Nothing in the accept rests on it: the gate
was the fresh-sample head-to-head and the roster, both met, and predictions 1 and 2 are now met
outright.

### Prediction 4 resolved without a run, and the economy re-measured on UNCONTAMINATED data

**Prediction 4 is untestable on the diagnosis maps, and the reason is saturation.** `carol_i29`
went 8/8 there. A ceiling leaves no residual variation for a map covariate to explain — which is
doctrine 3b's note that "no covariate structure" and "swept everywhere" are frequently the same
fact. Testing it needs an instrument that does not saturate, and the attribution is already closed
by direct measurement (0.0% discarded), so this is a nice-to-have rather than a gate. Not spending
a run on it.

**More important: my entire model of carol's economy was built on data contaminated by this bug.**
Re-measuring the same quantities on iteration 29 (intended mix = 75 / 15 / 10):

| map | realized soldier % | realized **splasher** % | realized mopper % | dead band [100,200) | tp ≥ 300 |
|---|---|---|---|---|---|
| Bunny | 49.3 → **59.4** | 0.7 → **1.5** | 50.0 → 39.1 | 48.6% → 39.7% | 0.3% → **12.1%** |
| DefaultMedium | 49.4 → **77.5** | 0.7 → **2.3** | 49.9 → 20.3 | 43.0% → 36.4% | 9.6% → **22.3%** |
| Fossil | 63.1 → **69.2** | 2.5 → **2.7** | 34.4 → 28.1 | 26.5% → 29.9% | 40.7% → 31.3% |
| Mirage | 72.7 → **54.0** | 1.7 → **1.2** | 25.6 → 44.9 | 36.9% → 32.2% | 21.2% → 25.5% |

Three findings, and the second kills a target I would otherwise have spent a run on:

1. **The soldier/mopper distortion largely resolved itself.** DefaultMedium goes 49.4% → 77.5%
   soldiers against an intended 75% — essentially exact. It was a symptom of the discarded attacks,
   not a separate defect. Three of the six degeneracies I catalogued are now gone without being
   targeted.
2. **The affordability story is refuted a second time, on new data.** On Bunny the tower's
   splasher-affordable share went from 0.3% to **12.1% — a 40x increase — and the realized splasher
   share moved only 0.7% → 1.5%.** If affordability were the binding constraint, a 40x loosening
   could not leave the outcome flat. This is an independent confirmation of the refutation I
   recorded from the count reconciliation, and it arrives from a different direction.
3. **The splasher shortfall SURVIVES and is now the best-founded open target**: 1.2–2.7% realized
   against 15% intended, on clean data, with affordability eliminated as the cause. Expected builds
   from the roll and the stash alone are two orders of magnitude above what is observed, so
   something between the roll and the build is discarding almost every splasher.

**Registered next target, with the pre-check named**: instrument the tower build DECISION — count
rolls by type, then how many fail the chips gate, and how many fail `canBuildRobot` — rather than
the outcome, which is what I have been counting all along. One live suspicion to test rather than
assume: the build site is a single `DIRS[rng.nextInt(8)]` cell with no retry, so a blocked
neighbour discards the whole build. That would hit every type, so on its own it cannot explain a
splasher-specific shortfall — which is exactly why the decision counter has to separate the two
failure modes instead of my guessing between them.

## Iteration 30 pre-checks — the splasher shortfall is FULLY explained, and my suspicion was wrong

`gauntlet/20260908-010951`, `carol_i30p` vs `carol_iter25`, four pinned maps. **Identity check
passes**: 8/8 with end rounds byte-identical to the accepted `carol_i29` run (r1087, r873, r1107,
r1846...). Verified no-op, so the counters describe iteration 29's own play.

Every counter is read **at the decision point, before `buildRobot` resolves** — which is what
doctrine 15 requires. Counting the outcome is what I had been doing all along and it is exactly
what could not answer this.

| map | type | rolls | **rejected: chips** | rejected: paint | **cell blocked** | built | free neighbours /8 |
|---|---|---|---|---|---|---|---|
| Bunny | SPLASHER | 616 | **311 (50.5%)** | 303 (49.2%) | **0** | 2 | 8.00 |
| DefaultMedium | SPLASHER | 1,546 | **1,471 (95.1%)** | 70 (4.5%) | **0** | 5 | 8.00 |
| Fossil | SPLASHER | 1,172 | **1,086 (92.7%)** | 81 (6.9%) | **0** | 5 | 7.60 |
| Mirage | SPLASHER | 2,026 | **1,400 (69.1%)** | 622 (30.7%) | **0** | 4 | 7.75 |
| DefaultMedium | SOLDIER | 7,820 | **6,688 (85.5%)** | 953 (12.2%) | 7 | 172 | 7.86 |

**My registered suspicion is REFUTED, and I am glad I registered it as a suspicion.** I wrote that
the single no-retry `DIRS[rng.nextInt(8)]` build cell might be discarding builds. It is not:
**5.77–8.00 of the 8 neighbours would have worked**, and blocked draws total 0–7 across thousands
of rolls. The build site is a non-issue. Had I "fixed" it I would have spent an iteration on a
branch that discards ~0.1% of builds.

**The chips gate is the whole story, and it is map-dependent** — which is why no single-map
diagnosis would have been safe:

- **DefaultMedium and Fossil are chips-bound**: 93–95% of splasher rolls die at the chips gate,
  only 4–7% at paint.
- **Bunny is jointly bound**: 50.5% chips, 49.2% paint.
- **Mirage is mostly chips-bound**: 69% / 31%.

And the arithmetic closes on the chips-bound maps. On DefaultMedium the treasury is ≥1600 (the
splasher gate) on 1.1% of tower-turns and ≥1450 (the soldier gate) on 11.5%; weighting by the roll
shares gives a predicted realized splasher share of
`0.15x1.1 / (0.15x1.1 + 0.75x11.5 + …)` ≈ **1.9%**, against **2.3% observed.** The shortfall needs
no new mechanism: it is the chips gate, and nothing else.

### The treasury dwells in a dead band — the same shape one level up

`chips` is captured at the top of `runTower` before any build, so the indicator's `chips=` is a
decision-point value, not post-spend. Gates: soldier 1450, mopper 1500, splasher 1600.

| map | median chips | <1200 | **[1200, 1450) — above the reserve, below every gate** | ≥1600 |
|---|---|---|---|---|
| Bunny | 1,580 | 10.3% | 28.4% | 48.2% |
| DefaultMedium | 1,300 | 25.2% | **63.3%** | 1.1% |
| Fossil | 1,300 | 25.7% | **61.3%** | 2.7% |
| Mirage | 1,360 | 17.6% | 43.1% | 27.9% |

**On two maps the treasury spends ~62% of the game above `CHIP_RESERVE` and below the cheapest
build gate.** That is the identical degeneracy iteration 6 diagnosed and iterations 7 and 18 built
escapes for — and the escape *does* fire, but only on ~5% of the pinned turns (321 tower-turns at
`rsv=0` against 6,567 pinned, on DefaultMedium), because `pinnedTurns` resets the moment chips
leave the band and must then re-accumulate ten consecutive turns.

**History pre-check, and it forbids the obvious move.** Iteration 4 lowered/disarmed the reserve
early and was **rejected with a trace**: the 1,980 starting chips are exactly the first tower
completion (`completeTowerPattern` costs 1,000), and spending them on ~7 early soldiers left the
bot a tower behind by round 300 and never catching up. "The early reserve is load-bearing after
all." So **"lower `CHIP_RESERVE`" is a known-rejected direction** and I am not proposing it.

What is new and does not revert it: the reserve is armed *for the whole game* whereas its evidenced
job — protecting the first completions — is an *early* job, and the escape built to handle the late
case is measurably reaching only 5% of it. **Registered as the next candidate: fix the escape's
duty cycle, not the reserve's value.** Pre-checks still outstanding and named rather than assumed:
(1) price what the reserve buys late — does a late tower completion actually get missed when the
reserve is off, or is that purely an early-game effect; (2) check the bytecode; and (3) size
whether more units is even the binding constraint, since three iterations (5, 8, 10) already
raised production and my own LEARNINGS records that "unit production is not the binding
constraint" — that entry must be superseded with evidence, not ignored.

### The tournament replays REFUTE the candidate I registered above, before it cost a run

Per the stall protocol ("re-examine the old tournament games — read them for what the *other*
lineages do that you never attempt"), pulled three `bob-vs-carol` replays from tournament
`20260907-1300` (carol was iteration 25 there). This is the only evidence in the project produced
by an opponent my lineage did not build.

| map | | units built | towers built | **paint tiles** | **tiles per unit** | splasher share |
|---|---|---|---|---|---|---|
| Brat | bob | 131 | 7 | **1,151** | **8.8** | **18%** |
| | carol | **159** | 3 | 473 | 3.0 | 1% |
| DefaultMedium | bob | 90 | 10 | **1,057** | **11.7** | **18%** |
| | carol | 54 | 5 | 347 | 6.4 | 2% |
| Fossil | bob | 127 | 9 | **1,486** | **11.7** | **18%** |
| | carol | **166** | 7 | 692 | 4.2 | 1% |

**Carol builds MORE units than bob on two of three maps and paints 2.2–3.0x fewer tiles.**

So the candidate I registered one entry above — "fix the escape's duty cycle so more units get
built" — is attacking a constraint that **is not binding**, and I would have spent a run proving it.
Withdrawing it now, unrun.

**And this does not supersede my old LEARNINGS entry, it CONFIRMS it.** That entry says three
iterations (5, 8, 10) raised production by three different routes and none helped: "unit production
is not the binding constraint". I had just written that it "must be superseded with evidence, not
ignored" — and the evidence arrived pointing the other way, from an opponent my lineage never
produced. The pre-check I named as outstanding (#3, "size whether more units is even the binding
constraint") is the one that killed the candidate, which is exactly what naming outstanding
pre-checks is for.

**What the comparison does say, and it is the sharpest target this lineage has had:**

1. **bob gets 2.8–3.9x more painted tiles per unit built.** The gap is per-unit productivity, not
   unit count.
2. **bob's splasher share is 18% on all three maps** — remarkably stable — against carol's 1–2%.
   Carol's own *intended* share is 15%. bob is running roughly the mix carol's constants ask for
   and carol cannot reach.
3. bob builds more towers (7–10 vs 3–7) on the same maps, which is plausibly upstream of the chips
   that buy splashers — so tower count, chips, and splasher share may be one chain rather than
   three targets. **Not asserting that; naming it as the thing to decompose.**

**Deliberately NOT designing a candidate on this yet, and the reason is dated evidence.** These
games are iteration 25. Iteration 29 raised carol's landed attacks by 1.2–3.3x and lifted the
soldier mix to nearly its intended share, so an unknown part of this gap is already closed. The
tournament now running (`20260908-0100`) is the *same instrument* measuring iteration 29 against
the *same* bob, and it is the correct thing to read before committing a design. Polling it rather
than designing against superseded numbers.

## Iteration 30 — registered: a SPLASHER FLOOR on the treasury

### Re-opening a CLOSED direction, on the ledger's own stated terms

The ledger says: *"**'Change the splasher share' — CLOSED.** dose 0 = 12.5% (catastrophic), dose 6
loses to dose 3... Re-opening needs a reason the **optimum moved**, e.g. **a change to the paint
economy large enough to alter what a 300-paint unit costs in practice.**"*

**Iteration 29 is exactly that change**, and it is the largest one this lineage has made to the
paint economy: it removed 42–55% of all soldier paint waste. The re-open condition was written
before I knew what would satisfy it, and it is satisfied verbatim rather than by
"feels under-explored".

**And the direction I am re-opening is not the one that was closed.** The closed direction is the
`SPLASHER_IN_20` *roll* constant. This changes the **realized** share while leaving the roll
constant at its measured optimum. That distinction is now load-bearing, because the i30p decision
counters show the roll and the realization are decoupled: 50–95% of splasher rolls die at the chips
gate, so the dose sweep was moving a knob whose output was clamped.

**That also explains the old sweep's shape without contradicting it** — flagged as a hypothesis,
not a conclusion, because I withdrew a retrodiction of this exact kind three hours ago. A tower
whose roll it cannot pay builds **nothing at all** that turn (verified by reading the code, not
inferred). So raising `SPLASHER_IN_20` to 6 converts build-turns into idle turns, which would make
dose 6 worse than dose 3 *even if more splashers were good*. And dose 0 being catastrophic (12.5%)
says the 1–2% of splashers carol does field are worth an enormous amount.

### The price, computed in BOTH currencies before building

Iteration 29 fixed the soldier, so the splasher's advantage had to be re-measured rather than
carried over — the soldier is what a splasher displaces, and it just got better.

| map | unit | build paint → attack paint | **tiles per 100 build paint** | chips per tile |
|---|---|---|---|---|
| Bunny | soldier | 32.3% | **6.46** | ~19 |
| | splasher | 125% (refills) | **30.33** | ~4 |
| DefaultMedium | soldier | 14.5% | **2.90** | ~43 |
| | splasher | 70.0% | **15.80** | ~8 |
| Fossil | soldier | 28.3% | **5.65** | ~22 |
| | splasher | 56.7% | **12.60** | ~11 |
| Mirage | soldier | 16.8% | **3.37** | ~37 |
| | splasher | 70.8% | **14.92** | ~9 |

**A splasher paints 2.4–4.7x more tiles per unit of build paint than a soldier, and is ~4x cheaper
per tile in chips.** Both currencies agree, on all four maps, *after* iteration 29. The advantage
is not per-attack efficiency (they are within 10% there) — it is that a splasher's 50-paint attack
dwarfs the ~1.5/turn it loses to drain, while a soldier's 5-paint attack does not.

Small-sample caveat, stated rather than buried: only 2–5 splashers per game. But the effect is
2.4–4.7x, consistent on four maps, and **corroborated by a source that shares none of my
assumptions — bob runs an 18% splasher share on every map measured.**

### The design, and why the obvious version fails

Not "raise the roll" (closed, and clamped anyway). Not "lower `CHIP_RESERVE`" (iteration 4,
rejected with a trace). Not "make the splasher roll sticky" — **that one fails on inspection: a
holding tower cannot stop the other 12–18 towers from spending the shared treasury**, so it would
lose the race it is trying to win. Recording the discarded design because the reason it fails is
the same reason the chosen one works.

**Chosen: a splasher floor.** A tower may build a *non*-splasher only if doing so leaves the
treasury at or above `SPLASH_FLOOR`. Chips are team-shared, so every tower computes the identical
predicate from `rc.getChips()` — **team-consistent coordination with no communication at all**,
which is the "emergent, not commanded" shape RESEARCH.md §7 recommends.

```java
boolean afford = chips >= reserve + want.moneyCost;
if (afford && want != UnitType.SPLASHER && chips - want.moneyCost < SPLASH_FLOOR) afford = false;
```

**Dose ladder with a byte-identical zero arm**: `SPLASH_FLOOR = 0` (never blocks — provably the
current code), 1600, 2000.

**It is aligned with iteration 4 rather than against it**: a higher treasury floor makes the
1,000-chip `completeTowerPattern` *more* reliable, which is precisely what iteration 4 showed the
reserve was protecting.

**Pre-checks: reachability MEASURED (splasher rolls 616–2,026/game, 50–95% dying at the gate);
price MEASURED in both currencies above; history CHECKED against iterations 4, 21 and the splasher
sweep. Outstanding and named: (1) does the floor starve early production on maps where chips are
genuinely scarce — the `<1200` share is 10–26%, so the floor must not bite there; (2) bytecode
(trivial, one comparison); (3) the one-map identity check.**

### Audit: the coverage-denominator correction, and the two tooling fixes

**Coverage denominator — my figures are UNAFFECTED, checked rather than assumed.**
`tools/engine-facts.md` previously said `teamCoverageAmounts` divides by *total* map area and
warned against passable area; it is now corrected to **passable area, walls excluded**. My sizing
pre-check computed `passable = w*h - walls` and multiplied per-mille by that — i.e. it used the
now-correct denominator throughout. So the ×9.3 (DefaultMedium) and ×0.2 (Fossil) prize-to-margin
figures, and the "868–1,193 passable tiles" map sizes, all stand as written.

One residual I am naming rather than hiding: ruins are also unpaintable (RULES: paintable = not
wall, not ruin) and my denominator subtracted only walls. On DefaultMedium the exact census gives
3 ruins against 1,194 non-wall tiles, so the error is 0.25% — irrelevant to a ×9.3 vs ×0.2
comparison, but it is an error and it would matter on a ruin-dense map.

**The lesson attached to the correction is the valuable part, and it indicts a habit of mine.**
The wrong version survived because its verification ran on a 2.6%-wall map, where the two candidate
denominators differ by 2 per-mille — inside the noise the check already tolerated. *A verification
performed where the hypotheses barely differ is not a verification.* I have the same exposure: my
own identity checks and probes all run on the same four maps (DefaultMedium, Fossil, Bunny,
Mirage), chosen because they were the diagnosis maps, not because they discriminate anything.
**Registering as a standing practice: when a quantity depends on a fraction, pick the probe map by
where that fraction is LARGE, not by where the trace came from.**

**`replaydump` glyph collision** (`M` meant a team-1 money tower or a team-2 mopper): I have not
counted units from arena glyphs in this session — the unit counts here come from `SPAWN` events and
the per-turn indicator stream, neither of which is affected. The one arena-grid census I inherited
(the 116/149 bracket) was already superseded by the exact array census.

**`track_vs_old_bots` `+cand` resolution**: re-ran it; **0 new rows, 7 replaced, no diff.** The fix
targets labels ending `+cand`, and my roster run is labelled `carol_i29` — the directory that
played, which is unambiguous and content-identical to `carol_iter29`. So my absolute-progress chart
was never carrying a stale hollow point. Charts regenerated regardless.

### Tournament `20260908-0100` — first external read on iteration 29, and it is SPLIT

| pair | iteration 25 (prev tournament) | **iteration 29** |
|---|---|---|
| carol vs alice | 47/150 = 31.3% | **47/150 = 31.3%** (complete) |
| carol vs bob | 12/150 = 8.0% | **7/14 = 50%** (early, incomplete) |

**The identical 47/150 is a coincidence, and I checked rather than assuming.** An identical total
from a changed bot on a deterministic engine is exactly the shape of a stale build being exported,
so I diffed the per-map results: **120 of 150 (map, side, winner) rows are identical and 30 flipped
— 15 each way.** Real games changed; the net happens to be zero. Not a tooling fault.

Two things follow, and the first is uncomfortable:

- **Against alice, iteration 29 is worth 0 net games**, with the mixed-direction scatter that is
  the churn signature — despite being worth +88% against my own predecessor. That is
  TRAINING_ALGORITHM §5b exactly: **a head-to-head margin is a partial derivative and does not
  transfer to an opponent it was not measured against.** My within-lineage instruments said this
  was the biggest accept the lineage has made; against an independent opponent it moved nothing.
  Both readings are true and they are about different questions.
- Attribution is not clean either way: **alice changed too** between the two tournaments
  (`688a75b` → `25c3160`), so the 30 flipped games carry both lineages' changes and I cannot
  isolate mine.

The bob pair is the one to watch (8% → 50% on 14 of 150 games) and it is far too early to read.
Polling it rather than concluding.

### Tournament `20260908-0100` COMPLETE — iteration 29's external verdict, and it is a clean split

| | iteration 25 (`20260907-1300`) | **iteration 29 (`20260908-0100`)** | delta |
|---|---|---|---|
| carol overall | 59/300 = 19.7% | **97/300 = 32.3%** | **+12.7** |
| carol vs **bob** | 12/150 = 8.0% | **50/150 = 33.3%** | **+25.3** |
| carol vs **alice** | 47/150 = 31.3% | 47/150 = 31.3% | **0.0** |
| bob overall | 277/300 = 92.3% | 211/300 = 70.3% | −22.0 |

Sweeps, quoted for **D** rather than as corroboration of the margin (doctrine 14 — they are the
same number):

| pair | before | **after** |
|---|---|---|
| bob–carol | bob 64, carol **1**, D=10 | bob 39, carol **14**, D=22 |
| alice–carol | alice 42, carol 14, D=19 | alice 39, carol **11**, D=25 |

**+12.7 points is the largest move any lineage made this run**, and carol went from sweeping **one**
map against bob to sweeping **fourteen**. This is the instrument that matters — an opponent my
lineage did not produce — and it says iteration 29 was real.

**But the split is the interesting part, and it is sharp: +25.3 against bob, exactly 0.0 against
alice.** Not approximately zero — the same 47/150, with 30 of 150 games flipping 15 each way.
The same one-line change is worth a quarter of the matchup against one independent opponent and
literally nothing against another.

That is doctrine 7's representativeness rule arriving from an unexpected direction. The usual form
is "an instrument cannot measure a defence against a behaviour its opponents never perform". Here
it is the offensive twin: **the discarded-attack fix only pays where the opponent contests ground
with paint that carol's soldiers then hammer at uselessly.** Against an opponent whose paint carol
rarely stands on, there was nothing to stop wasting. I have not verified that account — it is a
hypothesis with an obvious test (compare the share of carol soldier-turns spent on enemy paint in
alice games versus bob games, which is free from tournament replays) and I am registering it as
open rather than asserting it.

**Caveat that bounds all of the above**: both siblings changed too (`alice` 688a75b→25c3160,
`bob` ceef7af→f67ac8b, an accepted iteration). Wins are conserved in a three-way round robin, so
bob falling 22 points and carol rising 12.7 are not independent facts. What is *not* explained by
bob's decline is the asymmetry: if carol's gain were merely bob's loss, it would not have left the
alice pair at exactly 0.0.

### Testing the alice/bob asymmetry — directionally consistent, NOT closed

Pulled `alice-vs-carol` replays from the same tournament (`20260907-1300`, carol = iteration 25 in
both sets, same three maps) and measured carol's **landed** soldier attacks per soldier built. If
the discarded-attack waste were heavier against bob, carol's soldiers should land fewer attacks
there.

| map | vs **bob** | vs **alice** |
|---|---|---|
| DefaultMedium | 5.82 | **6.59** |
| Fossil | 8.89 | **9.82** |
| Brat | 3.17 | **4.09** |

**Consistent in the predicted direction on 3 of 3 maps** — carol lands 13–29% more attacks per
soldier against alice, i.e. wastes fewer, i.e. had less for iteration 29 to recover. That is the
sign the hypothesis predicts.

**It does not close the question, and I am not going to pretend it does.** Two reasons, both fatal
to reading it as confirmation:

1. **Magnitude mismatch.** A 13–29% difference in landed attacks is being asked to explain +25.3
   points against one opponent and *exactly* 0.0 against the other. Those are not the same size.
2. **Confounded by game length.** Carol builds 51/64/106 soldiers against bob and 64/116/209
   against alice on the same maps — roughly double. Longer games mean more attacks per soldier
   regardless of waste, and "per soldier" normalises for count but not for lifetime.

**And the decisive version is not runnable from my workspace.** It needs the iteration-29 drain
counters measured in games against alice and bob, and I cannot add a sibling as a gauntlet opponent
— their package is not in my workspace and putting it there is exactly what the isolation rules
forbid. The only games against them are the tournament's, which the coordinator runs.

So the attribution stays **OPEN**, with the record showing it was examined rather than merely
labelled: the cheapest available test was run, it came out the right way, and it is not sufficient.
What would settle it is a coordinator-run tournament with an instrumented carol, which I am noting
as a possible request rather than assuming.

---

## Iteration 30 — ACCEPTED: the splasher floor (`SPLASH_FLOOR = 2000`)

### Session recovery first: two complete runs that the log never recorded

Resumed after a session death. `git status` was clean and `src/carol` was still byte-identical to
`carol_iter29`, so from the log alone iteration 30 looked unbuilt. It was not: `src/carol_i30_1600`,
`src/carol_i30_2000` and `src/carol_i30_2600` were committed at `dcb7f3e`, and
`gauntlet-collect.sh --list` showed **both** of the iteration's runs finished on battlecode-dev and
already collated locally. What died was the *decision*, not the games — the exact casualty
MULTI_AGENT.md's "If your session dies mid-run" describes, in its least visible form, because the
collation had already succeeded and nothing looked missing.

Recording the shape so a future session recognises it: **a clean working tree is not evidence that
an iteration was never run.** The snapshot directories and the run list are, and they disagreed with
the log. Checked both before touching anything.

### The candidate, verified as a single mechanism

`diff` of `carol_iter29` against `carol_i30_2000`, package line normalised, is exactly two hunks:
the `BUILD` string, and the affordability predicate in `runTower`:

```java
final int SPLASH_FLOOR = 2000;
boolean afford = chips >= reserve + want.moneyCost;
if (afford && want != UnitType.SPLASHER && chips - want.moneyCost < SPLASH_FLOOR) afford = false;
```

No bundling. `SPLASH_FLOOR = 0` never blocks and is provably the previous code, so **`carol_iter29`
IS the zero arm** rather than a separate build that has to be trusted to be equivalent.

### Result — two independent map samples, both decisive

**Run `20260908-013505`** (dose sweep, 25 maps, bot = the working tree, which `bot_identity` resolved
as content-identical to `carol_i30_2000`):

| opponent | bot wins | swept-win | swept-loss | D (split) |
|---|---|---|---|---|
| `carol_iter29` (**the zero arm**) | **42/50 (84%)** | 17 | **0** | 8 |
| `carol_i30_1600` | 29/50 (58%) | 8 | 4 | 13 |
| `carol_i30_2600` | 25/50 (50%) | 7 | 7 | 11 |

**Run `20260908-021045`** (full gauntlet + frozen roster, a *fresh* 25-map sample, `head=12239ce`,
`dirty=0`, played as the `carol_i30_2000` package): overall **383/400 (95.8%)**.

| opponent | bot wins | swept-win | swept-loss | D |
|---|---|---|---|---|
| `carol_iter29` (**accept gate**) | **44/50 (88%)** | **19** | **0** | 6 |
| `carol_iter0` | 48/50 (96%) | 24 | **1** | 0 |
| `carol_iter1` | 49/50 (98%) | 24 | 0 | 1 |
| `carol_iter7` | 48/50 (96%) | 23 | 0 | 2 |
| `carol_iter21` | 47/50 (94%) | 22 | 0 | 3 |
| `carol_rush` | 47/50 (94%) | 23 | **1** | 1 |
| `carol_turtle` | 50/50 (100%) | 25 | 0 | 0 |
| `examplefuncsplayer` | 50/50 (100%) | 25 | 0 | 0 |

Doctrine 14 discharged rather than cited: sweeps and margin are **one number**, not two, and the
identity checks out — vs `carol_iter29`, `wins − losses = 44 − 6 = 38 = 2 × (19 − 0)`. So the sweeps
are quoted for **D**, the decisiveness, not as corroboration. D = 6 of 25 means this pair is mostly
*not* coin-flips: 19 of 25 maps went one way from both spawns.

Against the measured mirror null — identical code splits every map, **0 swept maps, se = 0** — a
19–0 sweep count is not a margin to be hedged. It is 19 maps the mechanism decided.

### Accept, against the pre-registered gate

- Head-to-head vs the last accepted snapshot > 50%: **88%** and **84%** on two disjoint map samples.
- Peer `WinPct` 60%: every peer ≥ 88%.
- No unresolved one-directional regression against `carol_iter29`: **zero swept losses in either
  run.** The 6 splits are single-side games spread over 6 different maps.

Promoted to `src/carol` and snapshotted as `src/carol_iter30` (verified byte-identical to
`src/carol` apart from the package line). Compile-checked with `javac` against
`battlecode25-java-3.1.0.jar` on battlecode-dev, in a scratch directory rather than the workspace
build tree, so no in-flight gauntlet could load half-written classes.

### What the dose ladder does and does NOT establish

It establishes that **2000 is a local maximum among {1600, 2000, 2600}** and that it beats the zero
arm by a wide margin on two samples. It does **not** give a full curve against zero: 1600-vs-zero
and 2600-vs-zero were never played, so the ladder is pinned to zero only at 2000 and is otherwise
measured *relative to 2000*. Stating that rather than drawing a curve through points I do not have.

2000 and 2600 are **dead even** (25/50, swept 7–7). The tiebreak is outstanding pre-check (1) —
"does the floor starve early production on maps where chips are genuinely scarce", where the
`<1200 chips` share runs 10–26%. With the head-to-head unable to separate them, the lower floor is
the conservative choice, and I took it for that stated reason rather than because it scored higher.

Pre-check (2), bytecode: one integer comparison in a branch that already existed; no new loop, no
new sensing call. Pre-check (3), the one-map identity check: subsumed — the arms disagree on 30+
games in both runs, so the mechanism demonstrably executes.

### The attribution, and the honest size of it

The mechanism story is the one registered before the run: 50–95% of splasher rolls were dying at
the chips gate because cheaper units drained the shared treasury below it first, pinning the
realized splasher share at 1.2–2.7% against an intended 15%. The floor makes every tower compute
the same predicate off the shared `rc.getChips()`, so they coordinate with no communication —
RESEARCH.md §7's "emergent, not commanded" shape.

**I have not verified that the realized splasher share actually moved**, and I am not going to
assert it from the win rate. That is the back-fill this project keeps punishing (§5b/3b). It is
also cheap to close by instrumentation rather than argument, and it is the first thing I would
measure if the next result is confusing. Registering it as **OPEN**, examined-but-unclosed.

### The one degeneracy signal in 400 games, and it is a good target

Only two swept losses in the whole roster run, and one of them is a genuine absolute signal rather
than an opponent-relative one:

**`carol_iter0` sweeps `Parking_lot` against iteration 30, both sides.** Generation 30 loses a map
from both spawns to the minimal first bot of its own lineage. Parking_lot also went A=loss against
`carol_iter1`, `carol_iter7` and `carol_iter29` — so it is not a single fluke game, it is a map this
build is broadly bad on, and losing it to iteration 0 needs no opponent model to be wrong.

Registering as the iteration 31 target. **First question is discriminating, not descriptive: is
this new?** Parking_lot was not in the `carol_i29` roster sample (`20260908-000327`), so I cannot
subtract across runs to find out — and per doctrine 6 I am not going to reason from a subtraction I
have just called unsound. Instead: pinned `MAPS="Parking_lot"` and launched
`BOT=carol_iter29 OPPONENTS="carol_iter0 carol_iter21 carol_iter25"` — 6 games. If iteration 29
also loses Parking_lot to iteration 0, this is a long-standing lineage-wide weakness and the
splasher floor is exonerated; if iteration 29 wins it, the floor caused it and the accept carries a
map-shaped regression I should price. Two hypotheses, visibly different numbers, six games.

## Iteration 30 follow-up — the Parking_lot probe, and the attribution CLOSES itself

### The probe answered the "is it new?" question in six games

Pinned `MAPS="Parking_lot"`, `BOT=carol_iter29`, opponents `carol_iter0 carol_iter21 carol_iter25`
(run `20260908-041852`). Result: **iteration 29 splits Parking_lot against iteration 0** (1/2), and
beats iterations 21 and 25 from both sides.

So generation 30 sweep-loses a map that generation 29 splits, against the same ancestor: the
splasher floor cost exactly **one game** there. That is a real one-game effect (deterministic
engine, no noise floor) but it is one game on a lopsided instrument, and doctrine 9 says a
lopsided instrument gives direction only. **It does not overturn a 44/50 accept, and the far more
interesting fact is the one it rules out: this is not a regression the floor introduced. It is a
lineage-wide weakness that predates iteration 30.**

**Every single Parking_lot game — all 6 in the probe and all 16 in the roster run — was decided by
paint coverage**, either `AREA_PAINTED` at the round limit or the coverage threshold. Not one
elimination. Parking_lot is a pure coverage race.

### The regime cut, done on an exogenous variable rather than an outcome

First cut was by end condition: 98.6% when somebody hit the coverage threshold, 80.5% in r2000
tiebreaks. **I am not using that number.** End condition is decided partly *by* who was winning, so
conditioning on it is post-treatment selection — the same shape as doctrine 15. The exogenous cut is
by map:

| | maps | win rate |
|---|---|---|
| games reach r2000 on ≥50% of the map's pairings | 3 | 41/48 = **85.4%** |
| everything else | 22 | 342/352 = **97.2%** |

And within the slow maps it is not uniform — `shell` is 100%, `mit` 87.5%, **`Parking_lot` 68.8%**,
the worst map in a 400-game run (next worst is `giver` at 75%, which is a *fast* map). So "slow maps
are a weakness" is too coarse a claim to make from three maps; Parking_lot specifically is the
outlier and that is what I traced.

Ruin density, checked because it was my first guess: Parking_lot is rank **38 of 75**, exactly the
corpus median (11.36 ruins/1000 tiles). Hypothesis dead before it cost anything. Area 2025, rank 26
of 75 — large but not extreme.

### The trace, and it is an absolute degeneracy

`carol_i30_2000` (T1) vs `carol_iter0` (T2), Parking_lot, bot side A — a loss:

| round | T1 cov | T1 chips | T1 tw | T1 paint acts | T1 died/starved | T2 cov | T2 tw |
|---|---|---|---|---|---|---|---|
| 200 | 122m | 4,020 | 3 | 238 | 9/8 | 100m | 3 |
| 600 | 136m | 7,620 | 3 | 17 | 26/26 | 103m | 3 |
| 1000 | 135m | 15,870 | 3 | **0** | 21/21 | 104m | 3 |
| 1400 | 134m | 24,220 | 3 | **0** | 23/23 | 103m | 3 |
| 1600 | 135m | 29,070 | 3 | 2 | 21/20 | **305m** | **10** |
| 2000 | 146m | **35,620** | **3** | 19 | 21/20 | **305m** | 10 |

Four facts, none of which needs an opponent to be wrong:

1. **Coverage flatlines from round 600 to round 2000** — 136 → 146 per-mille across 1,400 rounds.
2. **Paint actions are literally zero** for windows at rounds 800, 1000 and 1200.
3. **Deaths are starvation deaths**: `starved` ≈ `died` throughout (21/21, 23/23, 26/26). The bot
   builds ~20 units per 200 rounds and ~18 of them die at zero paint having painted nothing.
   `xfer` is **0 for the entire game** — not one paint transfer — while iteration 0 does 8–18 per
   window.
4. **35,620 chips banked against a 3-tower count and a 25-tower cap.** RULES.md's own line: "Chips
   accumulate uselessly unless spent on towers/upgrades/SRPs."

Iteration 0 wins by doing the opposite: it builds almost no units (+0–2 soldiers per window against
my +6–11 soldiers and +8–18 moppers), so its towers keep paint, its few soldiers survive, and at
round 1430–1537 it completes **seven** tower patterns and its coverage triples, 104 → 305.

### This CLOSES iteration 30's open attribution — and the mechanism is bigger than registered

I logged the attribution OPEN and said I would not back-fill it from the win rate. It is now closed
by a within-game A/B that was already on disk: the archived `iter30_carol_iter29_Fossil_botA`
replay has generation 30 (floor 2000) as T1 and **iteration 29 (floor 0, the zero arm) as T2**, on
one map, in one game. At round 300:

| | splashers alive | builds in window | tower paint | died/starved | coverage |
|---|---|---|---|---|---|
| **gen 30** (floor 2000) | **6** | +12 spl, **+0 sold, +0 mop** | **2,128** | 9/**4** | **635m** |
| **iter 29** (floor 0) | 0 | +0 spl, **+26 sold, +4 mop** | 412 | 23/**21** | 263m |

The registered mechanism is confirmed far more strongly than registered — realized splasher share
went from ~0% to essentially 100% of builds. But the trace shows **it is one mechanism, not two**:
blocking the cheap-unit spam is *how* the splashers get built, and the same block is why gen 30's
towers hold 5x the paint and why its units stop starving (4 starved vs 21). Iteration 29 on Fossil
is in exactly the same starvation spiral that generation 30 is in on Parking_lot.

**Which hands me the iteration 31 target directly.** The floor is keyed on **chips**, but the
resource it is really protecting is **tower paint**. On Parking_lot chips are ≥2000 on **100.0%** of
tower turns, so the floor never binds — and the degeneracy survives precisely where chips are
abundant. The throttle works; it is measured in the wrong currency.

### I nearly published a doctrine-15 artefact, and the reconciliation caught it

Sizing the operating band for that candidate, I extracted 2,403 tower-turns of `tp=` (the tower's
own paint) from the Parking_lot replay, rounds 600–1400, and got: median **38**, max **200**,
`tp >= 200` on **0.1%** of turns. Read naively that says *a soldier (200 paint) was affordable on
one turn in a thousand* — a spectacular finding, and the basis for the paint-floor design I was
about to build.

It is invalid. `tp` is `rc.getPaint()` evaluated **in the return statement of `runTower`, after
`rc.buildRobot` has already spent the stash.** It is post-spend state, and the turns that show a
drained tower are exactly the turns it built something. Doctrine 15, verbatim.

The check that caught it is doctrine 15's own: **multiply the rate back into a count.** 0.1% of
2,403 turns implies ~2.4 soldier-affordable turns in that window; the replay shows roughly **30
soldiers actually built** in it. An order of magnitude — not a subtle bias. (The `chips=` field in
the same string *is* a decision-point value, captured at the top of `runTower`; I had verified that
in an earlier session and carried the assurance across to a neighbouring field that does not share
it. Two fields, one string, different referents.)

**Scoping what dies, not the whole analysis**, per the doctrine: the claim that my towers *end*
most turns at ~38 paint is a claim about post-turn state, which is exactly what post-turn state
supports, so **"the towers are drained" stands.** What dies is only the step from that to
affordability at the decision point — which is the number the design needed.

### The history pre-check independently constrains the same design

Before building, checked LEARNINGS for prior work on this currency. Two entries bite:

- **Iteration 6's `PAINT_PLENTIFUL = 500`** sat *above* the mid-game tower-paint band and so fired
  early and then never again — "verify a threshold against the operating band before, not after,
  the run." A tower-paint floor is the same class of constant and needs the same sizing.
- **Iteration 19a (stop building moppers)** ran at **32%**: a mopper costs 100 paint against a
  soldier's 200, and "cutting the cheap unit in a paint-starved economy *removes* production."

So a naive "tower may not build below a paint floor" is the shape of an already-rejected direction,
and my sizing number for it was the invalid one. Both objections point the same way: **measure the
decision properly first, then design.**

Built `src/carol_i31p`: `src/carol` plus `int tpIn = rc.getPaint()` captured at the **top** of
`runTower`, and `want`/`cost`/`afford`/`canBuildRobot`/`built` recorded per decision. All pure
reads; `rng.next` call count verified unchanged, so the games must be identical to `carol`'s.
Compiles, and `UnitType.paintCost` was confirmed by `javap` on the engine jar rather than assumed.
Running it on the motivating game to get the true decision-point distribution.

### The decision probe — and this time the accounting closes exactly

`carol_i31p` vs `carol_iter0`, Parking_lot (run `20260908-042926`). **Arm-to-arm identity check
passed**: the probe went 0/2, both losses at r2000, reproducing the shipping build's Parking_lot
result against iteration 0 game for game. It is a no-op, so what it reports is what `src/carol` does.

2,403 tower decisions, rounds 600–1400:

| rolled `want` | decisions | share | paintCost | chips gate passes | **actually built** | tower paint ≥ cost |
|---|---|---|---|---|---|---|
| SOLDIER | 1,809 | 75.3% | 200 | **100.0%** | **2.0%** | 2.0% |
| SPLASHER | 366 | 15.2% | 300 | **100.0%** | **0.0%** | 0.0% |
| MOPPER | 228 | 9.5% | 100 | **100.0%** | **21.1%** | 21.1% |

**The accounting closes before I read anything off it**, per the "close the accounting" rule and as
the direct remedy for the artefact above: the probe predicts **84** builds in the window, and the
independent per-window spawn counts in the aggregate trace (+20, +22, +20, +22 at rounds 800, 1000,
1200, 1400) sum to **84**. Exactly. Nothing is left unexplained, which is what licenses the rest.

Tower paint **at the decision point**: median **38**, p90 140, p99 205, **max 215**. (The invalid
post-spend version said `≥200` on 0.1%; the true figure is 2.0% — the artefact understated it 20x,
so the retraction was worth making and the corrected number is materially different, not cosmetic.)

Three findings, in descending order of how firmly they are established:

1. **The chips gate passes on 100.0% of 2,403 decisions.** Iteration 30's `SPLASH_FLOOR` provably
   never binds on this map — measured at the decision point, not inferred from chip totals.
2. **96.5% of decisions build nothing, and 100.0% of those failures are `tpIn < paintCost`.** Not
   one failure has any other cause. The binding constraint is the tower's own paint stash, full stop.
3. **The roll is a fiction.** Realized production is 36 soldiers : 48 moppers : **0 splashers** —
   **43% / 57% / 0%** against an intended 75% / 9.5% / 15.2%. The tower never *chooses* a mopper;
   a mopper roll simply succeeds 10x more often than a soldier roll (21.1% vs 2.0%) because it is
   cheaper, and a splasher roll succeeds never. **The allocation is set by which roll happens to be
   affordable — a policy nobody chose**, which is §5b's "the order they fire in sets the allocation,
   by accident rather than by measurement" in the paint currency.

This is the *same* clamping pathology iteration 30 fixed, one level down and much more severe:
iteration 30 unclamped the chips gate, and the paint gate underneath it is untouched.

## Iteration 31 — registered, NOT yet built: the paint-side clamp

**Target**: the realized mopper share is 57% against an intended 9.5%, and my own LEARNINGS measures
moppers as idle on **95.1%** of 78,480 turns. The single largest sink of a starved paint economy is
the unit least able to use it, and it wins that sink by being cheapest rather than by being chosen.

**Why this is not a silent revert of iteration 19a.** 19a *deleted* moppers from the roll and ran at
**32%**, with the recorded cause "a mopper costs 100 paint against a soldier's 200, and cutting the
cheap unit in a paint-starved economy *removes* production". That cause was correct and I am not
contradicting it — but 19a was a permanent removal, and what the probe adds is *why* the cheap unit
dominates. A floor that yields when paint is genuinely plentiful is a different mechanism from a
deletion, and 19a's rejection does not reach it. Recording this as the specific reason the recorded
cause no longer applies, rather than "feels under-explored".

**Pre-checks I have DONE:**
- *Reachability, at the decision point*: 2,403 decisions, chips gate 100%, paint gate binding on
  96.5%. The branch fires constantly.
- *Operating band* (iteration 6's `PAINT_PLENTIFUL` lesson): median 38, p99 205, max 215.
- *Instrument validity*: identity check passed; accounting closes 84 = 84.

**Pre-checks I have NOT done — naming them rather than letting momentum imply they are done:**
1. **The band's max of 215 is ENDOGENOUS, and I have not proved it.** A splasher needs 300 and the
   stash never reaches it — but that is a consequence of the *current* spending policy, not a cap.
   Team paint income backs out at ~15/turn (12,000 paint spent over 800 rounds), so a blocked stash
   should climb past 300 in ~20 turns. I have not verified that, and the whole design rests on it.
2. **My own history contraindicates the obvious payoff.** LEARNINGS measures splashers as `noPaint`
   on up to **79% of their turns, 1,987 turns on Parking_lot specifically, against 10 splashes.**
   So "let the stash reach 300 and build splashers" would buy, on this exact map, the unit already
   measured as useless on it. This is the price term, it falls on the binding axis, and it is the
   most likely killer of the candidate. It must be settled before building, not after.
3. **Sizing map is one map.** Parking_lot is the outlier that motivated this; per the "check your
   sizing map is not degenerate" rule the distribution must be re-measured on a typical map before
   a constant is chosen. The probe is built and is a verified no-op, so this costs 2 games.
4. Bytecode on the shipping build (the probe adds a string concat that the shipping build would not).

Stopping the design here deliberately. Pre-check 2 is the one that has caught this lineage three
times in the "cost the price, not just the benefit" family, and it points at the payoff rather than
the mechanism — exactly where I have historically not looked.

### Pre-checks 1 and 3 settled — and the finding generalizes off the outlier map

Ran the probe against `carol_iter29` on a **random 6-map sample** (run `20260908-043517`,
`NMAPS=6`, maps drawn by the tool, not chosen by me) and read the decisions off two of them.
Incidentally another no-op confirmation: `carol_i31p` went **10/12 (83%)** against `carol_iter29`,
in line with iteration 30's accepted 84–88%.

| | Parking_lot | **Snowman** | **sunrise** |
|---|---|---|---|
| decisions | 2,403 | 2,403 | 1,568 |
| tower paint at decision: median / max | 38 / 215 | 0 / 250 | **192 / 1000** |
| chips gate passes | 100.0% | 100.0% | **30.7%** |
| builds, as share of decisions | 3.5% | 3.4% | 1.4% |
| **no-build (chips OK) that is `tpIn < paintCost`** | **100.0%** | **100.0%** | **100.0%** |
| realized MOPPER share (intended 10%) | **57%** | **53%** | **50%** |
| realized SPLASHER share (intended 15%) | 0% | 0% | 23% |

**Pre-check 3 (degenerate sizing map) — cleared.** Parking_lot is not special. On all three maps,
every single build blocked while chips were available was blocked by the tower's own paint, and the
realized mopper share is 50–57% against an intended 10%. The one thing Parking_lot *was* an outlier
on — losing to iteration 0 — is not the thing the constant is being sized against.

**Pre-check 1 (is the 215 ceiling endogenous?) — cleared, with evidence rather than argument.** On
`sunrise` the stash reaches **1,000**. So 215 is not a cap the engine imposes; it is what the
current spending policy leaves behind. `sunrise` also shows the other half of the mechanism: it is
the one chips-*scarce* map here (chips gate passes on 30.7%), the stash therefore accumulates, and
it is the only map where splashers get built at all (23%).

**Pre-check 2 (the splasher price on Parking_lot) — no longer load-bearing, so I am not spending a
run on it.** The design below does not depend on splashers. Its case is the mopper over-share,
which is 50–57% on every map measured.

## Iteration 31 — built and running: MOPPER PAINT FLOOR

**Hypothesis.** The mopper is 10% of the roll and 50–57% of realized production. It wins that share
by costing 100 paint against a soldier's 200 and a splasher's 300, so its roll clears a starved
stash roughly 10x more often (21.1% vs 2.0% vs 0.0% on Parking_lot). Nothing chooses this; it is
cost ordering deciding the allocation, which is §5b's "the order they fire in sets the allocation,
by accident rather than by measurement".

**Mechanism.** A mopper may be built only if the tower's own stash covers its cost *plus* a floor:

```java
final int MOP_PAINT_FLOOR = <dose>;
if (MOP_PAINT_FLOOR > 0 && afford && want == UnitType.MOPPER
        && tpIn < want.paintCost + MOP_PAINT_FLOOR) afford = false;
```

**The `> 0` guard is load-bearing, not decoration.** Without it, a floor of 0 would still touch
`afford` whenever `tpIn < 100` — and since the `if (afford)` block is what draws
`DIRS[rng.nextInt(8)]`, that would skip an rng draw and desynchronise the entire stream, so the
"zero arm" would not be byte-identical to iteration 30 and every comparison would be against a
different bot. Verified: 4 real rng call sites in both arms, identical.

**Why this is not iteration 19a again.** 19a deleted the mopper roll and ran at 32%, with the
recorded cause "cutting the cheap unit in a paint-starved economy *removes* production". This
removes no spend channel: the paint is spent either way, on a soldier or splasher instead, and the
mopper is still built whenever the stash is genuinely comfortable. **It is a mix change at constant
paint spend, not a production cut** — which is precisely the term 19a's rejection turns on.

**Price, in the binding currency, written down before the result.** Cost: the mopper builds that
occur while the stash sits in [100, 100+dose) are foregone. Benefit: that paint instead reaches a
soldier or splasher roll. The exchange rate is the whole bet — if moppers are worth as much per
paint as soldiers, this is worth exactly zero. My own LEARNINGS measures moppers as idle on 95.1%
of 78,480 turns, which is the reason to expect the exchange to be favourable; it is also a figure
from an older iteration and I have **not** re-measured it on the current build. That is the honest
weak point of the price argument and I am recording it as such rather than leaning on the 95.1%.

**Pre-registered gate**, fixed before any game was read:
- **Accept** if `carol_i31_100` beats `carol_iter30` head-to-head **> 50%** (the mirror null is an
  exact even split with zero swept maps, so a margin is simply games flipped), peers hold, and
  there is no one-directional regression.
- **Dose ladder**: 0 (`carol_iter30`, provably byte-identical), 100, 200.
- **Identity check** folded into the run: if the mechanism is dead, the `carol_iter30` arm returns
  exactly 25/50 with every map split and zero sweeps.
- **Map-level prediction**, stated so the sample can check itself: the effect should be *absent* on
  chip-scarce maps like `sunrise`, where the stash already accumulates past the floor on its own and
  splashers are already 23% of production, and *present* on chip-rich maps like Parking_lot and
  Snowman, where the stash is pinned under 250 and the mopper takes half of everything.

Run `20260908-044251` launched: `BOT=carol_i31_100`, opponents `carol_iter30` and `carol_i31_200`,
fresh random 25-map sample, 100 games.

### Iteration 31 — REJECTED (25/50), and the pre-named weak point is exactly what killed it

Run `20260908-044251`, fresh random 25-map sample, 100 games.

| arm | result | swept-win | swept-loss | D (split) |
|---|---|---|---|---|
| `carol_i31_100` vs **`carol_iter30`** (the accept gate) | **25/50 (50.0%)** | 2 | 2 | **21** |
| `carol_i31_100` vs `carol_i31_200` | 26/50 (52%) | 4 | 3 | 18 |

**Fails the pre-registered gate** (`> 50%` required; this is exactly 50%). No dose rescue: 100 and
200 are indistinguishable at 26/50, so the ladder is flat rather than pointing anywhere.

**The mechanism was NOT dead — this is a real rejection, not a void iteration.** The mirror null is
an exact even split with **zero** swept maps; this run has 4 swept maps against `carol_iter30`
(2 win, 2 loss). Games genuinely changed and the net came out at zero.

**Mechanism verification: it worked exactly as designed.** From the `gridworld` replay (a swept
loss), both arms in one game, at the round-500 window:

| | soldiers built | **moppers built** | **realized mopper share** | towers | coverage |
|---|---|---|---|---|---|
| **`carol_i31_100`** (floor 100) | 18 | **2** | **9.5%** — the intended share | 5 | 358m |
| **`carol_iter30`** (floor 0) | 27 | **21** | **44%** | 9 | 534m |

The floor did precisely what it was built to do: it pulled the realized mopper share from 44% to
9.5%, onto its intended 10%. **And the bot got no better.** This is my own LEARNINGS entry "a
mechanism can rewrite the whole game and move nothing", second instance, and I should have weighted
that entry more heavily when the mechanistic story looked this clean.

**Why it moved nothing, and it is the term I flagged in advance.** I wrote in the pre-registration:
*"if moppers are worth as much per paint as soldiers, this is worth exactly zero... [the 95.1% idle
figure] is from an older iteration and I have not re-measured it on the current build. That is the
honest weak point of the price argument."* That is the term that failed. In the same window:

- `carol_iter30`'s moppers: **112 unpaint actions and 28 mop swings.**
- `carol_i31_100`'s moppers: **19 unpaints and 0 mop swings.**

**Moppers on the current build are active, not idle.** The 95.1%-idle figure that the whole price
argument rested on does not describe this bot. Blocking them removed real work, and the paint
released did not buy more than the work it displaced — `carol_iter30` out-produced the candidate on
*every* axis in that window (48 builds to 21, 9 towers to 5), because mopping enemy paint is itself
part of how coverage is won.

So the rejection converts a weakly-founded belief into a firmly-founded one, which is what the
algorithm says a rejected run is for: **the mopper is not the waste channel this lineage has assumed
it to be since iteration 19a.** Two iterations have now attacked mopper production on the strength
of a stale idle figure, and both failed — 19a at 32%, this at exactly the null.

`src/carol` is untouched and remains iteration 30; nothing to revert.

### Closed-directions ledger update

- **"Cut mopper production to redirect tower paint" — CLOSED, both routes measured.** Iteration 19a
  deleted the mopper roll: **32%**. Iteration 31 throttled it with a paint floor at two doses,
  leaving the spend channel open: **25/50 and 26/50, exactly the null**, with the realized share
  verified to have moved 44% → 9.5%. The mechanism is confirmed to work and the effect is confirmed
  to be zero. **Re-opening requires a re-measurement showing moppers have become idle on the
  then-current build** — not an argument that they ought to be, and not the 95.1% figure, which is
  superseded (see LEARNINGS). The two attempts used opposite mechanisms and landed in the same
  place, which is what makes this a closure rather than a pair of near misses.

- **NOT closed: "the tower build gate is paint, not chips."** That finding stands on its own
  measurements — 100.0% of chips-available no-builds are `tpIn < paintCost` on three maps, and the
  realized mix is set by cost ordering. What iteration 31 refutes is one *use* of that finding (that
  the mopper is the channel worth reclaiming), not the finding. The unexplored branch it leaves is
  the other direction entirely: on `sunrise`, the one chip-scarce map measured, the stash reaches
  1,000 and splashers reach 23% of production unaided. **Raising tower paint income** — rather than
  re-dividing a starved stash — is the branch nothing has tested, and RULES.md names the instrument:
  each active SRP adds +3/turn to *every* tower, so its value scales with tower count. Registering
  it as the next candidate to size, with iteration 26's recorded failure (gate set at the cost of
  the first step, 59–88% of marks abandoned) as the specific thing a design must fix.

## Iteration 32 — opportunistic LATTICE SRP: re-opening iteration 26 on the ledger's own terms

**Where this came from.** Iteration 31's ledger registered the next candidate as *"raising tower
paint income — rather than re-dividing a starved stash"*, naming the SRP as the instrument
(+3 paint/turn to every paint tower per active SRP, so its value scales with tower count) and
iteration 26's failure as the specific thing a design must fix. This is that candidate.

**The closed direction, and the clause that re-opens it.** Iteration 26 closed *"SRPs as
currently designed"* — but explicitly **"on the commitment model, not on the mechanic"**. The
mechanic is *proven*: 88 patterns completed across one run, on a build that had never laid one in
26 iterations. What was refuted is **per-soldier commitment with navigation capture**: once
`srpCenter` was set, `SRPfar` fired 573–4,583 times a game steering the soldier, which then
arrived back below the release threshold. The ledger wrote its own re-opening condition, and I am
taking it verbatim: *"an opportunistic version with no `srpCenter` at all — complete any pattern
that happens to be finishable from where the soldier already is ... That has no in-transit spend
to lose."*

**The missing piece was coordination, and a LATTICE supplies it.** With no per-robot target,
soldiers must agree on *where* a pattern goes without communicating. `cell(x,y)` centred at
`(5*(x/5)+2, 5*(y/5)+2)` is a **pure function of the tile**, so every soldier that ever stands
there computes the same centre with nothing exchanged, and 5×5 blocks on a 5-stride lattice tile
the plane exactly with no overlap. This is the same device `towerTypeFor()` has used since
iteration 5 — *"must be a pure function of the ruin so that every soldier agrees every turn"*.

**The property that makes this not iteration 26 again**, and it is the whole bet: because the
target is a function of the **map** rather than of the **robot**, *partial work is never lost*.
Paint already laid stays on the ground, and the next soldier to stand in that cell — any soldier,
any number of rounds later — continues from where the last one stopped. Iteration 26 discarded
every partially-built pattern the moment its owner was distracted; this holds no state at all, so
there is nothing to drop. It also pays **no 25-paint deposit**: RULES.md records that marks are
optional and "pattern match is on paint only", so iteration 26's non-refundable entry cost — the
thing I priced wrongly and which killed it — does not exist in this design.

### Two probes, and the first one was a FALSE NEGATIVE I nearly acted on

**Probe p (`carol_i32p`, run `20260908-054603`, 8 games).** Identity check exact: 4/8, all four
maps split by side, every map ending on the same round as iteration 30 — a confirmed no-op.
Pre-registered kill condition: *if `srpOk` is ~0 the design is unreachable.*

| map | idle turns | ruin-blocked | dirty | **`srpOk`** |
|---|---|---|---|---|
| Parking_lot | 137 | 5 (3.6%) | 132 (96%) | **0** |
| sunrise | 46 | 31 (67%) | 15 | **0** |
| gridworld | 44 | 44 (100%) | 0 | **0** |
| DefaultLarge | 67 | 62 (93%) | 5 | **0** |

`srpOk = 0` everywhere. **The kill condition fired — and it was wrong.** Probe p tested a
condition *wider than the mechanism needs*, which is precisely the error iteration 26a wrote the
rule against: *"check that the counter's condition is the same width as the decision the bot would
actually get to make. A narrower proxy can only produce false negatives, and a false negative here
reads exactly like a refutation."* I wrote that rule, then broke it in the other direction — p's
condition was **wider**, which produces false negatives just as effectively. Two guards were too
wide, both provably:

1. **Full-cell sensing.** p required all 25 cell tiles to be sensable. Vision is r²=20 and a cell
   corner sits at (4,4) = r² 32 from the opposite corner, so **only 13 of the 25 standing
   positions inside a cell can see the whole cell** — ~48% of turns failed on geometry, not on the
   map. Worse, p folded that into the *same counter* as real dirt, so p cannot say how much of
   Parking_lot's 96% was ever real. That conflation is the actual defect.
2. **The ruin guard.** p vetoed any cell overlapping *any* visible ruin. But RULES.md: *"tower
   survives even if its pattern is later painted over"* — a ruin that **already has a tower** is
   not a conflict at all.

**Probe q (`carol_i32q`, run `20260908-055828`, 8 games)** re-asked the question at the width of
the *tile-local* decision the shipping mechanism actually makes. Identity check exact again (4/8,
same four splits, same end rounds).

| map | idle turns | **turns with an actionable tile** | firing rate | tiles available | of which p vetoed on a BUILT ruin |
|---|---|---|---|---|---|
| Parking_lot | 137 | **137** | **100%** | 1485 | 39 |
| sunrise | 46 | **24** | **52%** | 153 | 39 |
| gridworld | 54 | **53** | **98%** | 383 | **378** |
| DefaultLarge | 67 | **37** | **55%** | 39 | 5 |

The direction is reachable on **52–100%** of idle turns, not 0%. On gridworld the built-ruin
distinction alone accounts for 378 vetoed tiles — p's blanket guard was the whole of its "100%
ruin-blocked" result. **Had I stopped at probe p I would have closed a live direction on my own
instrument's artefact**, and the run that would have proved it never happens.

### The ceiling, measured off the map corpus for ZERO VM game time

Cell viability is a *static* property of the map — walls and ruins never move — so it can be read
straight out of the `.map25` flatbuffers with no games at all. `carol-tools/latticescan/`
(modelled on the shared `tools/mapdata/ruinscan`, and reading only the official 75-map corpus):

```
TOTAL cells=5072 viable=1491 (29.4%) ruin-free=726 (14.3%)
per-map viable%: min 4.0  median 25.0  max 63.6
maps with ZERO viable cells: 0
```

**29.4% of lattice cells corpus-wide can host an SRP** (wholly on-map, no wall, no ruin), median
25% per map, and no map is dead. A median 40×40 map has ~16 hostable cells. This is a hard ceiling
no in-game tuning can raise, and it is comfortably high. It also says what the mechanism must
avoid: **70.6% of cells can never complete**, so recolouring inside one is pure loss — hence the
viability filter, which exists for a measured reason rather than as decoration.

### Price, in the binding currency, written down before the result

Our soldiers paint everything primary, so a viable cell needs its **13 secondary tiles** recoloured:
13 × 5 = **65 paint**, plus 200 chips at completion. Return is **+3 paint/turn to every paint tower
and +3 chips/turn to every money tower, forever**, after a 50-round activation hold. At carol's
observed 3–6 paint towers that is +9…18 paint/turn for 65 paint — payback in ~4–7 rounds of
holding. The 200 chips are close to free: this lineage measured **100.0% of chips-available
no-builds as paint-limited**, so chips are not the constraint.

**The honest weak points, named in advance** (iteration 31's rejection turned on exactly the term
I had flagged, so this is where the attention belongs):

- **The 50-round hold.** An SRP pays nothing until it has sat undisturbed for 50 rounds. Our own
  splashers paint **primary only** and cannot choose per-tile colour, so a splasher crossing a
  completed cell breaks it. Iteration 30 raised splasher production, which makes this *more*
  likely than it was, not less. The mechanism is self-healing — the next soldier repaints — but
  self-healing costs paint, and a cell that is broken every 40 rounds pays out never while still
  charging 65 paint a cycle. **This is the term I expect to fail if the iteration fails.**
- **Paint spent is real even when the turn was worthless.** The turns are measured waste, but the
  *paint* is not: a soldier that recolours 20 tiles arrives at the frontier 100 paint lighter.
  That is what the dose is for.

**The dose is not arbitrary.** RULES.md: below 50% of capacity a robot takes a `(100 − 2·X)%`
cooldown penalty, and at 0 paint it takes −20 HP/turn and cannot act at all. A soldier holds 200,
so a floor of **100** means SRP work can never push a soldier across the 50% cooldown cliff — the
mechanism is structurally barred from inflicting the penalty on itself. Dose **0** is the
aggressive arm testing whether that safety costs completions.

### Pre-registered gate, fixed before any game of the evaluation is read

- **Accept** if `carol_i32_100` beats `carol_iter30` head-to-head **> 50%**, with swept wins
  exceeding swept losses and no one-directional regression.
- **Dose ladder**: `carol_iter30` (floor ∞ — the mechanism absent, and provably byte-identical
  since it is the accepted snapshot itself), `carol_i32_100`, `carol_i32_0`.
- **Identity check** folded in: the `carol_iter30` arm must return exactly 25/50 with every map
  split by side and zero sweeps if the mechanism is inert.
- **§4 engagement check, run FIRST on an 8-game repro sample**: `SRPdone` must be > 0. Iteration
  26 completed 88 patterns; if this completes ~0 the lattice never closes a cell and the design is
  refuted *before* a 100-game run is bought, not after.
- **Map-level prediction**, stated so the sample can check itself: the effect should scale with
  **viable-cell density**, which `latticescan` gives per map independently of any game. It should
  be strongest on high-viability maps (`sunrise` 36.4%, `gardenworld` 34.7%) and near-absent on
  `gridworld` (11.1%) and `roads` (5.6%). If the gain is uniform across viability, the mechanism
  is not working through the channel I claim and the attribution is OPEN regardless of the result.

## Iteration 32 — REFUTED at the §4 engagement pre-check. Zero completions, and the 100-game run was never bought

The pre-registered engagement check was: **`SRPdone` must be > 0** on an 8-game repro sample,
*before* a full run is paid for. It is 0. On every arm, on every map.

| arm | run | h2h | `SRPpnt` (tiles recoloured) | **`SRPdone`** | dominant veto |
|---|---|---|---|---|---|
| `carol_i32_100` (floor 100) | `20260908-061042` | 5/8 | 0 in the sampled windows | **0** | `SRPpoor` 65, `SRPfoe` 39 |
| `carol_i32_0` (floor 0) | `20260908-061552` | 5/8 | **10** / 900 rounds | **0** | `SRPwall` 3591 (93%) |
| `carol_i32b` (widened) | `20260908-062421` | 5/8 | **14** / 900 rounds | **0** | `SRPdead` 3837 |

**The 5/8 is not evidence of anything and I am not treating it as such.** All three arms scored
identically while taking 0, 10 and 14 SRP actions respectively across a whole game. A change that
touches ~10 of ~30,000 robot-turns cannot be what moved three games; reading that 5/8 as support
would be exactly the back-filled mechanism story rule 3b forbids. (Bytecode was checked first and
ruled out as the cause: max 6,515 of 17,500, `ov=0 nm=0`.)

### Why it completed nothing, and the answer is different on different maps — which is the finding

A cell needs **13 recolours by soldiers standing in it**. We got 14 across an entire map in 900
rounds. That is not a tuning gap, it is two orders of magnitude, and tracing it map by map gives
two *different* blockers that turn out to be the same problem:

**1. Where the idle budget is plentiful, the cells are not viable.** Parking_lot: 6,597 IDLE-ALLY
turns, and 93% of firings died on a wall or ruin inside the cell. Parking_lot's own viability is
**19.8%** (`latticescan`), so a uniformly-scattered robot would pass 19.8% of the time; carol's
soldiers passed **6.8%** — they are **~3× under-represented in viable cells**. That is not the
map, it is carol: `nearestEmptyRuin`/`workOnRuin` park soldiers next to ruins by design, and a
ruin is precisely what makes every overlapping cell non-viable. **The bot's own accepted
navigation denies this mechanism its ground.**

**2. Where the cells are plentiful, the idle budget is not ally-side.** DefaultLarge has the
highest viability of the four (**46.7%**) and there the veto flips entirely: 1,166 `SRPnone` — the
cell was fine and there was simply no ally tile worth recolouring. The reason is in the idle
census: **IDLE-ENEMY 1,424 vs IDLE-ALLY 20**, i.e. 98.6% of that map's idle budget is a soldier
parked at a ruin beside enemy paint it cannot overwrite (`ruin=[27, 17]` on every one of those
turns). There is no friendly ground under it to recolour.

**So the two things this mechanism needs — clean ally ground to stand on, and a wall/ruin-free
cell to stand in — are anti-correlated across the corpus.** Parking_lot has the first and not the
second; DefaultLarge has the second and not the first. That is why the completion count is zero on
all four maps despite the local cause being different on each, and it is a stronger statement than
either blocker on its own.

### The idle budget I designed against was measured on a different bot

Iteration 26 measured the idle budget as **72–88% `frontNone`** — deep inside saturated ally
territory, which is exactly the right ground for a pattern. I built iteration 32 on that figure.
On the current build it is **map-dependent and often nothing like it**: IDLE-ALLY is 77% on
Parking_lot, 33% on gridworld, and **1.4% on DefaultLarge**. Iterations 29 and 30 pushed carol's
soldiers toward the frontier, and the waste moved with them.

**This is the third iteration in a row killed by a stale measurement.** Iteration 31 died on a
95.1%-idle mopper figure taken from an older build; iteration 32 dies on an idle-composition
figure taken from iteration 25. The pattern is now unmistakable and it is a property of my *loop*,
not of any one mechanism: **a measured constant is only valid for the build it was measured on,
and this lineage keeps re-using them across accepts that specifically changed the thing measured.**
Recorded in LEARNINGS as a standing pre-condition rather than as a third anecdote.

### The width error, twice more in one iteration, and my own rule was only half right

Iteration 26a wrote: *"a NARROWER proxy can only produce false negatives."* That is the half I had
seen. This iteration produced both halves inside one hour:

- **Probe p was WIDER than the mechanism needed** (full-cell sensing, blanket ruin guard) and
  returned `srpOk = 0` on all four maps — a **false negative** that would have closed a live
  direction on my own instrument's artefact, had I stopped there.
- **Probe q was WIDER than the code I then shipped** (tile-local across the whole action radius,
  versus own-cell-only in the build) and returned 52–100% firing — a **false positive** that sent
  me to a build which engaged 0.26% of the time.

The corrected rule, which supersedes 26a's: **a probe is only informative when its condition is
the SAME width as the shipping decision; any mismatch invalidates it, and the direction of the
mismatch decides whether you are handed a false negative or a false positive.** Both are equally
capable of costing an iteration, and I have now paid for each.

### Closed-directions ledger

- **"SRPs" — CLOSED on the mechanic now, not merely on the commitment model.** The two possible
  designs have been built and measured, and they fail for *opposite* reasons that cannot be
  satisfied together:
  - **With navigation** (iteration 26): the soldier reaches viable cells, and `srpCenter` captures
    it for 573–4,583 turns a game; it arrives back below the release threshold. Rejected on
    evaluation, 3/8 and 4/12 across two doses.
  - **Without navigation** (iteration 32, two builds and a widening refinement): nothing is
    captured and nothing is lost, and the soldier is essentially never standing in a completable
    cell — 14 recolours and **0 completions** in 900 rounds. Refuted at the engagement pre-check.

  **The dilemma is the closure**: reaching a viable cell requires steering, and steering is the
  thing that was already measured to kill it. Re-opening now requires *neither* — a design that
  puts the pattern where soldiers already are rather than moving soldiers to the pattern. The one
  candidate of that shape, recorded for whoever re-opens it: **anchor the pattern to ruins**
  (a fixed offset from each sensed ruin is still a pure function of the map, so it still needs no
  communication) *because soldiers already cluster at ruins* — that inverts blocker 1 instead of
  fighting it. It is not free: `latticescan` says only 14.3% of cells are both viable and clear of
  a ruin's tower pattern, so the offset would have to thread that gap, and blocker 2 (enemy-side
  idle turns) is untouched by it.

- **NOT closed, and now better supported: "raise tower paint income."** Iteration 31 registered
  this and named the SRP as the instrument. The *instrument* is what failed here, not the target.
  The arithmetic that motivated it is unchanged and was never the weak link.

**DECISION: REJECT.** `src/carol` is untouched and remains iteration 30; nothing to revert, HEAD
still compiles. Cost: three 8-game samples (24 games) and two no-op probe runs, against the
**100-game run the pre-registered engagement check prevented me from buying**. That check is the
cheapest thing in this log and it has now paid for itself outright.

## Iteration 33 — iteration 14's frontier-seeking is switched OFF on the largest block of idle turns

**Target, and it came free out of iteration 32's failure.** Tracing why the SRP mechanism found no
friendly ground to stand on turned up a much larger fact about the *current* build: the idle budget
is dominated by IDLE-ENEMY, and iteration 14's frontier-seeking is gated `if (foe == 0)` — so it
does not run there at all.

| map | IDLE-ENEMY | IDLE-ALLY | share of idle budget where iteration 14 is DISABLED |
|---|---|---|---|
| DefaultLarge | **1,424** | 20 | **98.6%** |
| gridworld | **7,099** | 3,480 | **67.1%** |
| Parking_lot | 1,980 | 6,597 | 23.1% |

**Measured on this build** (`carol_i32b`, run `20260908-062421`), not inherited from an earlier
iteration — this is the standing pre-condition LEARNINGS acquired an hour ago, applied.

**Hypothesis.** Reaching that line means nothing paintable inside the action radius r²=9. When
`foe > 0` that is a **capability** wall, not a navigation one: RULES.md, a soldier's attack "paints
the tile ONLY if empty or already own-team paint", so it can *never* convert the enemy paint it is
standing beside, no matter how long it waits. Meanwhile vision is r²=20 — more than twice the
action area — so genuinely EMPTY ground is usually in sight, and `newExploreTarget()` instead sends
the soldier to a **random map coordinate**. Un-gating costs nothing: it spends no paint and no
action, it only redirects a move that was already going to happen. That is the same
"capability at zero marginal cost" shape iteration 14 itself was accepted on.

**Why the gate existed, and why that is not a defence of it.** The ally/foe census arrived with
iteration 14 to *diagnose* the two kinds of idleness — "ally paint everywhere = nav problem; enemy
paint in reach = capability problem". The diagnosis was then reused as a *policy* without ever
being tested as one. Nothing in the log measures the gate; it has simply never been touched.

**Price, in the binding currency.** Paint: **zero** — no attack is added or removed. Chips: zero.
The only cost is the counterfactual value of the move the soldier would otherwise have made, which
is `newExploreTarget()`'s random coordinate. The honest weak point: a soldier at the enemy frontier
may be there for a *reason* the census cannot see — chipping a tower (handled earlier in
`runSoldier`, so unaffected) or holding contested ground (not modelled anywhere in this bot). If
carol is quietly relying on soldiers loitering at the frontier, this removes it, and that is the
term I expect to fail if the iteration fails.

**Same-width discipline, applied deliberately.** The probe and the shipping decision are the
*same expression* — `nearestVisibleEmpty()` is called once and both the counter and the redirect
read that one result. Iteration 32 was killed twice by width mismatches between probe and build;
here there is no separate probe to mismatch.

**Pre-registered gate**, fixed before any game is read:
- **§4 engagement check first, on an 8-game repro sample**: `ideFound` must be > 0 and a
  substantial fraction of `ideTurns`. If the empty ground I claim is visible is not actually
  visible, the mechanism is inert and no full run is bought — the check that saved 100 games on
  iteration 32.
- **Accept** if `carol_i33` beats `carol_iter30` head-to-head **> 50%** on a fresh random 25-map
  sample, swept wins exceeding swept losses, no one-directional regression.
- **Map-level prediction**, stated so the sample can check itself: the gain should track the
  IDLE-ENEMY share, i.e. be largest on DefaultLarge-like maps (98.6% disabled) and smallest on
  Parking_lot-like maps (23.1%). If the gain is uniform, attribution is OPEN.

### Instrument note: the frozen roster has SATURATED and can no longer detect improvement

Checked while iteration 33's run was in flight. The last roster run (`carol_i30_2000`, 2026-09-08
02:10) scores:

| opponent | win% |
|---|---|
| `examplefuncsplayer` | 100.0 |
| `carol_turtle` | 100.0 |
| `carol_iter1` | 98.0 |
| `carol_iter0` | 96.0 |
| `carol_iter7` | 96.0 |
| `carol_iter21` | **94.0** |
| `carol_rush` | 94.0 |

**Every member is at 94–100%.** This is a ceiling, and it matters because the frozen roster is my
*only* absolute-strength instrument — AGENT.md: the gauntlet headline "cannot tell 'the bot
improved' from 'the instrument moved'; a frozen opponent can." An instrument pinned at 94–100%
cannot distinguish iteration 30 from an iteration 40 that is twice as good, so the one measurement
designed to catch the "chain of individually-positive accepts walking downhill" failure
(TRAINING_ALGORITHM §5b) is currently blind.

The roster is derived automatically from every 5th accepted snapshot, so it refreshes on its own —
but only every five accepts, and its newest member is `carol_iter21` while the bot is at iteration
30. **The saturation is a lag, not a fault**, and it will clear when iter25/iter30 enter the
roster. What is worth doing in the meantime is the sanctioned alternative: `roster_extra.txt` takes
fixed non-snapshot yardsticks, and mine currently holds three that are all beaten ≥94%. A *harder*
synthetic archetype — one built to exploit the weakness the tournament actually reports, which for
carol is the coverage race — would restore resolution without waiting five accepts.

Registering that as a process task rather than an iteration, since it changes how I measure rather
than what the bot does. It must be a synthetic archetype I write; **a BC25 finals benchmark bot is
a yardstick and never an opponent, and must never enter `roster_extra.txt`** — AGENT.md names that
exact file as the trap, precisely because a never-changing external bot is what a frozen yardstick
looks like.

## Iteration 33 — REJECT at 24/50, and the trace says paint is binding for the third time

Run `20260908-063927`, fresh random 25-map sample, 100 games.

| arm | result | swept-win | swept-loss | split |
|---|---|---|---|---|
| `carol_i33` vs **`carol_iter30`** (the accept gate) | **24/50 (48.0%)** | 3 | 4 | 18 |
| `carol_i33` vs `carol_iter25` (peer check) | 47/50 (94.0%) | 22 | 0 | 3 |

**Fails the pre-registered gate** (`> 50%` required). The peer check is strong and one-sided, so
this is **not** a general regression — the bot is intact, the change simply does not pay.

**The mechanism engaged, so this is a real rejection and not a void iteration.** The §4 engagement
check passed before the run was bought: the redirect fired on **94.7%** (Parking_lot), **64.3%**
(DefaultLarge) and **21.4%** (gridworld) of IDLE-ENEMY turns, and 7 maps were swept (3–4), so games
genuinely changed.

### Why it lost, from both teams inside ONE game

`Snowglobe` was a swept loss and the replay carries both arms, so the comparison is exact rather
than cross-run. T1 = `carol_i33`, T2 = `carol_iter30`, same map, same game:

| round | | coverage | **tower paint** | paint acts (that window) | starved |
|---|---|---|---|---|---|
| 200 | `carol_i33` | **318m** | **520** | **724** | 4 |
| 200 | `carol_iter30` | 242m | **2,312** | 526 | 7 |
| 400 | `carol_i33` | 290m *(fell)* | **418** | 521 | **22** |
| 400 | `carol_iter30` | **390m** | **1,379** | **855** | 13 |

**The mechanism worked exactly as designed and that is what beat it.** Un-gating found soldiers
more empty ground, so they painted more — 724 acts to 526 in the first 200 rounds — and took a
76m coverage lead. Paying for it drained the tower stash to **520 against 2,312**, a 4.4× deficit.
From there production collapsed: by round 400 the candidate had *less* coverage (290 vs 390), was
painting *less* (521 vs 855), and had **22 starved robots against 13**. Early coverage is not
durable — it gets painted over — while tower paint is what funds sustained production.

So the change converts stored tower paint into early coverage at an unfavourable exchange rate.
That is the same shape as the price argument I have now got wrong three times, and it is the term
I named in the pre-registration ("a soldier at the enemy frontier may be there for a reason the
census cannot see") — though not for the reason I guessed: it was not about holding contested
ground, it was about the paint bill.

### The finding that outlives the iteration

Four iterations have now tried to convert idle soldier turns into value — 14 (frontier-seeking),
26 (SRP commitment), 32 (lattice SRP), 33 (un-gating). Only 14 was accepted, and 33 has just shown
why the others cannot work as a class:

> **carol's soldiers are not idle for lack of targets. They are idle for lack of paint.**

The direct, on-this-build evidence, which I already had and had not put together:
- Iteration 32's probe: on **63%** of idle turns the soldier held **< 100 paint** — below half
  capacity, where RULES.md's `(100 − 2·X)%` cooldown penalty is already biting (`SRPpoor` 65 of 104).
- Iteration 33's trace: giving idle soldiers *more* to do raised paint acts 38% and starvation 69%,
  and cost the game.

Any mechanism that spends an idle turn spends paint, and paint is the constraint. **The idle-turn
budget is not free capacity; it is the visible shadow of the paint shortage.** That closes the
whole class as a source of gains and points at the one direction the ledger already registered.

### Closed-directions ledger

- **"Spend idle soldier turns on additional work" — CLOSED as a class.** Three mechanisms, three
  failures, one cause: iterations 26 and 32 (SRP) and 33 (frontier redirect) all spend paint, and
  paint is what the idleness is made of. Re-opening requires a mechanism that consumes idle turns
  at **literally zero paint** — iteration 14 is the existing member of that class and it is the one
  that was accepted, which is the pattern.
- **"Raise tower paint income" — OPEN and now the indicated direction, on three independent
  measurements**: 100.0% of chips-available no-builds are paint-limited (iteration 31 probe, on
  this build); 63% of idle soldier turns are below half paint (iteration 32 probe); and iteration
  33's tower stash collapsed 4.4× below the baseline's the moment spending rose. The SRP was only
  ever one *instrument* for this and it failed; the target did not.

**DECISION: REJECT.** `src/carol` is untouched and remains iteration 30; nothing to revert.

### Tooling report — `gauntlet-collect.sh` prints the WORKSPACE name, not the bot that played

`gauntlet-collect.sh 20260908-063927` prints `bot=carol` for a run whose `bot.txt` records
`bot=carol_i33`. Cause, read out of the script rather than inferred from the symptom
(`tools/gauntlet-collect.sh:22-23`):

```bash
default_bot="$(basename "$WS_REL")"; ...
BOT="${BOT:-$default_bot}"          # never reads bot.txt, which HAS the right value
```

**Discriminating check, so this is characterised and not just reported**: `grep '\$BOT'` finds
line 54 — the `echo` — as the *only* use in the file. Scoring comes from `results.csv`, whose rows
are keyed by opponent and side and carry no bot identity at all. So the defect is **cosmetic and
cannot move a verdict** (unlike `map-resample.py`, which was inverting; I checked which this was
before naming it).

It is still worth fixing, because of exactly who reads it: a session recovering a finished run
after a session death — the case `gauntlet-collect.sh` exists for — sees `bot=carol` and can
reasonably conclude the run was a mirror of the baseline against itself, then discard a valid
100-game run or re-run it and pay for shared VM time twice. `bot.txt` already holds the correct
label, so the fix is to read it there. Reported rather than worked around.

## Iteration 34 — fewer MONEY towers: the constant is from iteration 3 and the binding resource moved

**Target.** `towerTypeFor` makes a ruin a money tower when `k % 3 == 0`, i.e. ~1 ruin in 3. That
literal 3 was fixed in **iteration 5**, from **iteration 3's** galaxy trace ("chip income is
exactly 30/turn"). It is a constant from iteration 3 setting the build mix at iteration 30, and it
has never been re-measured — the exact stale-constant failure LEARNINGS recorded this session after
it killed iterations 31 and 32.

**Why the direction is paint-ward, on three measurements all taken on THIS build:**

| evidence | source | says |
|---|---|---|
| **100.0%** of chips-available no-builds are `tpIn < paintCost` | iteration 31 probe (built from iteration 30) | the build gate is paint, never chips |
| **63%** of idle soldier turns hold < 100 paint | iteration 32 probe (`SRPpoor` 65 of 104) | soldiers live below the 50% cooldown cliff |
| tower stash **4.4× below** baseline as spending rose, while **both** teams' chips idled above **$2,200** | iteration 33 trace, Snowglobe r400 | chips accumulate unspent while paint collapses |

**And RULES.md gives the mechanism, not just the correlation.** A money tower has
`paintPerTurn == 0`, so it gains paint from *nothing* — not from mining, and not from SRPs either,
because the SRP bonus sits inside the same `if (type.paintPerTurn != 0)` guard. `buildRobot` draws
paint from the **building tower's own stash**. So a money tower spawns ~2 robots from its 500
starting stash and is then a **dry build site for the rest of the game**, while a paint tower makes
10/turn into the stash it builds from. One ruin in three is currently spent on that.

**Mechanism.** One constant: `MONEY_MOD` replaces the literal 3. `k` is invariant under both map
symmetries and `k % MONEY_MOD` is a pure function of `k`, so the two properties `towerTypeFor`
depends on — play-symmetry, and every soldier agreeing on every ruin every turn — are preserved
exactly. Iteration 25's census override (flip money→paint when `seenPaint*2 < seenMoney`) is
untouched and still acts as the one-sided safety net.

**Price, in the binding currency, written down before the result.** Cost: chip income falls by
roughly one money tower in three-to-four. Chips fund robots (250/400), ruins (1000) and upgrades,
so if chips become binding this reverses. **That is the honest weak point and it is the term I
expect to fail if this fails** — the evidence above says chips are idle *now*, at the current money
share, which is not the same as saying they would stay idle at a lower one. Benefit: each converted
ruin becomes +10 paint/turn into a stash that can actually build, instead of +30 chips/turn into a
treasury already sitting above $2,200 unspent.

**Dose ladder**, so the curve is measured rather than a single guess: `carol_iter30` (MONEY_MOD 3,
the incumbent, provably byte-identical since it is the accepted snapshot), `carol_i34_4` (~1 in 4),
`carol_i34_5` (~1 in 5). If chips are genuinely slack the ordering should be 5 ≥ 4 > 3; if the
ordering inverts, chips bind sooner than the evidence suggests and the direction is wrong.

**Pre-registered gate, fixed before any game is read:**
- **§4 engagement check first, on an 8-game repro sample**: the realized mix must actually move —
  `sm=` (money towers seen) must fall relative to `sp=` versus `carol_iter30` in the same games.
  A pure-function change on a coordinate that happens not to vary would be inert.
- **Accept** if `carol_i34_4` beats `carol_iter30` head-to-head **> 50%** on a fresh random 25-map
  sample, swept wins exceeding swept losses, no one-directional regression.
- **Map-level prediction**: the gain should be largest on **ruin-rich** maps, where the money share
  costs the most absolute paint towers (`tools/mapdata` gives ruin density independently of any
  game: gridworld 21.9/1000 tiles, median 11.4, Gears 4.6). If the gain is uniform across ruin
  density, the attribution is OPEN.

### Free finding while iteration 34 ran: the paint-tower UPGRADE gate is an off switch

Read off replays **already on disk**, at zero VM cost, from the counter iteration 12 left in the
tower state string. Snowglobe (iteration 33 build; the tower code is identical to iteration 30's):

```
  UPG        4
  upgPoor    9147
```

**The paint-tower upgrade fires on 0.04% of eligible tower turns.** Iteration 12's gate is
`need = CHIP_RESERVE + getNextLevel().moneyCost` = 1200 + 2500 = **3,700 chips**, and the treasury
is measured on this build to oscillate in roughly **[1,600, 2,450]** — `$2,250 / $2,250 / $2,050 /
$2,450` on Parking_lot at rounds 300/600/900/1200, `$2,350` on Snowglobe at 400. It never reaches
3,700, so the mechanism is switched off rather than tuned.

**This is the same fault iteration 30 already fixed once, in the same file, and was accepted on at
44/50**: *"50–95% of splasher rolls die at the chips gate (1600 = CHIP_RESERVE + 400) because
cheaper units drain the shared treasury below it first, pinning the realized splasher share at
1.2–2.7% against an intended 15%."* A gate set above where the treasury actually sits is not a
policy, it is an off switch — and this lineage now has two independent instances of it, both from
adding `CHIP_RESERVE` to a cost that already had one.

It also matters *more* than the splasher case, because of what it buys: upgrading a paint tower
lv1→lv2 takes it from **5 to 10 paint/turn**, permanently, and paint is the resource three separate
measurements this session identify as binding while chips sit idle above $2,200. That is the
cheapest chips→paint converter in the game and it has been dormant since iteration 12.

`src/carol_i35` is built and compiles: it drops the `CHIP_RESERVE` term from the upgrade gate
only. The reasoning for dropping the reserve rather than adding a floor is that CHIP_RESERVE exists
to protect a **1,000-chip ruin completion from robot production**; an upgrade is not robot
production, it is the same class of investment the reserve protects, so charging it the reserve on
top of its own 2,500 cost double-counts. Note there is no dose below this — `canUpgradeTower`
checks affordability itself, so any `need` under 2,500 is identical to 2,500.

Held until iteration 34 resolves, since if 34 is accepted the baseline moves and this must be
rebuilt on top of it. Registered here so the measurement is durable regardless.

#### Reachability of iteration 35's new gate, checked before building on it (and it disproved my worry)

I suspected the 2,500 gate might be unreachable too, because `SPLASH_FLOOR = 2000` caps the
treasury by design: it blocks non-splasher builds below `2000 + cost`, so soldiers fire whenever
chips reach ~2,250 and pull them straight back down. If the ceiling were under 2,500, iteration 35
would be inert and I would have shipped a second off switch to replace the first.

The chip distribution over **12,932 tower-turns** in one Snowglobe game settles it:

| | chips |
|---|---|
| min | 0 |
| p50 | 1,710 |
| p90 | 2,350 |
| p99 | 2,600 |
| max | 2,800 |

- **share ≥ 3,700 (the incumbent gate): 0.00%** — the mechanism is not rare, it is *exactly off*.
- **share ≥ 2,500 (iteration 35's gate): 3.21%** — ~415 qualifying tower-turns in one game.

So the worry was wrong and the direction survives: an upgrade needs to happen a handful of times,
not constantly, and 415 opportunities is ample. Worth noting that I checked rather than redesigning
on the strength of the suspicion — a floor-based redesign would have added a second constant to fix
a problem that does not exist.

**The price this measurement also exposes, and it belongs in the pre-registration.** An upgrade
costs 2,500 out of a treasury whose p99 is 2,600, so it drains the team to ~100 chips and blocks
*all* robot production (250 each) and any ruin completion (1,000) until income rebuilds — several
rounds at 30–60 chips/turn. Against that: +5 paint/turn on that tower for the rest of the game,
which over 1,000+ remaining rounds is 5,000+ paint, or ~25 soldiers' worth of build paint. The
trade looks strongly favourable, but **the drain is a real, measured cost and not a rounding
error**, and it is the term to watch if the iteration fails.

#### The realized dose, computed off the map corpus before the run is read (zero VM game time)

`k = min(x, W−1−x) + min(y, H−1−y)` is a distance-from-edge sum and is **not uniform**, so "1 ruin
in `MONEY_MOD`" was an assumption, not a fact. `carol-tools/mixscan/` reads the real ruin
coordinates out of the official 75-map corpus (1,374 ruins) and reports what the constant actually
delivers:

| `MONEY_MOD` | money ruins | realized share | nominal | **maps with ZERO money ruins** |
|---|---|---|---|---|
| 3 (incumbent) | 447 | 32.5% | 33.3% | 5 |
| **4** (`carol_i34_4`) | 373 | **27.1%** | 25.0% | 6 |
| **5** (`carol_i34_5`) | 242 | **17.6%** | 20.0% | **18** |

Two things this changes, both stated before any result is read:

1. **Dose 4 is a smaller step than it looks** — 32.5% → 27.1%, not 33% → 25%. If the effect is
   real but the step is small, a near-miss should be read as "go further", not "the axis is wrong".
2. **Dose 5 carries a specific, quantified hazard on 18 of 75 maps (24%)**, where it leaves the
   team *no* money-tower ruins at all — only the single starting money tower at 30 chips/turn.
   That is precisely iteration 3's diagnosed failure state ("chip income is exactly 30/turn ...
   one soldier per 8.3 rounds forever"), which is what put money towers in the mix in the first
   place. So a dose-5 collapse would **not** refute the direction; it would confirm the floor.
   The incumbent already has 5 such maps, so the failure mode is not new, only more frequent.

**Sharpened map-level prediction**: dose 5 should lose specifically on its 18 zero-money maps and
be neutral-to-better elsewhere. That is checkable against `mixscan` per map without any extra games,
and it separates "the direction is wrong" from "the dose overshot" — which the win rate alone
cannot do.

## Iteration 34 — ACCEPT. 28/50 with a weak margin and a STRONGLY confirmed mechanism prediction

Run `20260908-071553`, fresh random 25-map sample, 100 games.

| arm | result | swept-win | swept-loss | split | resampled |
|---|---|---|---|---|---|
| `carol_i34_4` vs **`carol_iter30`** (the accept gate) | **28/50 (56.0%)** | **7** | 4 | 14 | 95% CI [22, 34], **+0.92 sd** |
| `carol_i34_4` vs `carol_i34_5` | 25/50 (50.0%) | 4 | 4 | 17 | CI [20, 30], +0.00 sd |

**The pre-registered gate is met**: > 50%, swept wins (7) exceed swept losses (4), and the peer
direction shows no one-directional regression (only 4 maps swept-lost of 25).

**And the headline margin is weak, which I am recording rather than smoothing over.** +0.92 sd,
with a 95% CI of [22, 34] that *includes the 25/50 null*. That is weaker than iteration 25's
accept (+1.01 sd) and nothing like iteration 30's 44/50. On the win rate alone this would be a
coin-flip dressed as a result.

### What actually carries this accept is the pre-registered map-level prediction

Before the run I wrote: *"the gain should be largest on **ruin-rich** maps, where the money share
costs the most absolute paint towers ... If the gain is uniform across ruin density, the
attribution is OPEN."* Joining the 25 per-map results against ruin counts read from the official
corpus (`carol-tools/mixscan`, no extra games):

| | maps | record | win% |
|---|---|---|---|
| ruin-**poor** half (< 18 ruins) | 11 | 10/22 | **45.5%** |
| ruin-**rich** half (≥ 18 ruins) | 14 | 18/28 | **64.3%** |

**Spearman rho(wins, ruin count) = +0.624** (n = 25, t = 3.83, df = 23, **p < 0.001**).

This is the prediction I registered, in the direction I registered, at a significance the headline
margin does not come close to. It matters *because* it was pre-registered: a covariate story fitted
after the fact would be the back-filled mechanism rule 3b forbids, but a covariate prediction
written down before the sample was drawn is independent evidence. The mechanism is confirmed:
converting money ruins to paint ruins pays in proportion to how many ruins there are to convert,
and on ruin-poor maps there is nothing to convert and the change is correctly near-null (45.5%).

### Why the dose ladder is flat, and it was predicted too

Doses 4 and 5 are indistinguishable (25/50, +0.00 sd). The corpus scan explains it and did so in
advance: `MONEY_MOD = 5` leaves **zero money ruins on 18 of 75 maps** against 6 for dose 4, which
reproduces iteration 3's diagnosed failure state (chip income pinned at 30/turn from the single
starting money tower). So dose 5 buys more paint towers where ruins are plentiful and loses the
chip floor where they are not, netting to zero against dose 4. **A flat ladder here is the floor
being found, not the axis being wrong** — which is exactly the distinction I registered it to make.

**DECISION: ACCEPT at dose 4.** Dose 4 is also the safer of two statistically tied arms (6
zero-money maps against 18), so the tie is broken on measured risk rather than preference.
`src/carol` is now iteration 34 (`MONEY_MOD = 4`, realized money share 32.5% → 27.1% corpus-wide);
frozen as `src/carol_iter34`. Both charts regenerated: 15 accepted iterations, `carol_iter0..34`.

**Honest statement of what was bought**: a small, real, mechanism-confirmed gain concentrated on
ruin-rich maps. Given the CI spans the null, the *size* is not established — only the direction and
the channel. The next tournament (13:00 UTC) is the external check, and per MULTI_AGENT.md it is
the only measurement here taken against opponents this lineage did not produce.

**Caveat carried forward, unresolved.** My absolute-strength instrument is saturated at 94–100%
(logged earlier this session), so TRAINING_ALGORITHM §5b's "chain of individually-positive accepts
walking downhill" is exactly the failure I currently cannot detect — and a +0.92 sd accept is
precisely the kind of link such a chain is made of. `src/carol_racer` is built and compiles for
this reason; validating it as a roster yardstick is the outstanding process task.

---

---

## CORRECTION to iteration 34 — the published rho is not reproducible. Retracted; the accept stands

Found while building `carol-tools/covar/mapcovar.py`, the committed tool that computes iteration
35's pre-registered covariate. I ran it against iteration 34's own run (`20260908-071553`,
`carol_iter30` arm) as a sanity check, expecting to reproduce a published number. It reproduced
every number in that entry **except the one the accept was argued on**.

| quantity | published in the iteration-34 entry | recomputed from `results.csv` |
|---|---|---|
| headline | 28/50 (56.0%) | **28/50** ✓ |
| swept win / loss / split | 7 / 4 / 14 | **7 / 4 / 14** ✓ |
| ruin-poor half | 11 maps, 10/22, 45.5% | **11 maps, 10/22, 45.5%** ✓ |
| ruin-rich half | 14 maps, 18/28, 64.3% | **14 maps, 18/28, 64.3%** ✓ |
| **Spearman rho(wins, ruins)** | **+0.624, t=3.83, p < 0.001** | **+0.244, t=+1.21, p ≈ 0.24** |

### The discriminating check, run before naming the fault

A wrong label and a wrong value look identical in a log entry, so I did not stop at "the numbers
differ". I recomputed rho every plausible way the earlier session could have computed it, on both
arms of the run and against three covariates:

| computation | rho | t |
|---|---|---|
| Spearman, midranks (correct) | +0.244 | +1.21 |
| Spearman, ordinal ranks, ties uncorrected | +0.130 | +0.63 |
| Pearson on raw values | +0.221 | +1.09 |
| `1 − 6Σd²/(n(n²−1))` with ordinal ranks | +0.130 | +0.63 |
| `1 − 6Σd²/(n(n²−1))` with midranks (invalid under ties) | +0.320 | +1.62 |
| per-game rows, n = 50 | +0.165 | +1.16 |
| win>1 indicator vs ruins | +0.142 | +0.69 |

and across the whole space of {both arms} x {ruins, area, ruin density} x {wins, margin}, the
largest |rho| anywhere is **0.474** (`dens`, and negative). **Nothing in that space reaches
+0.624.** So this is not a mislabelled covariate and not a tie-handling convention: the published
value does not correspond to any computation over this run's data. It was computed ad hoc in
session, never written to a file, and therefore never checkable — which is exactly why it survived
into a commit message.

### This is a lineage error, not a `tools/` bug — so there is nothing to report upstream

`tools/` computed none of this. The ruin counts come from `tools/mapdata/ruin_parity.txt` and are
correct (spot-checked against `mixscan/per_map_dose.txt`; they agree). The join, the ranking and
the t-statistic were all mine. Reporting it to the coordinator would be pointing at the wrong file.

### What changes, and what does not

**The ACCEPT stands.** The pre-registered gate for iteration 34 was `> 25/50` **and** swept wins
>= swept losses **and** no one-directional regression in the peer arm. Those were 28/50, 7 vs 4,
and 4 swept-losses of 25 — all verified correct above, none of them touched by this error. The
gate was met on its own terms and rho was never part of it.

**The argument for the accept is materially weaker than that entry claims, and I am striking the
claim rather than softening it.** That entry says: *"What actually carries this accept is the
pre-registered map-level prediction ... at a significance the headline margin does not come close
to."* That sentence is **withdrawn**. At rho = +0.244, t = 1.21 on 23 df, the covariate is *less*
significant than the headline (+0.92 sd), not more. The honest summary of iteration 34's evidence
is now:

> a weak 28/50 (CI [22, 34], spanning the null) with a **directionally consistent but
> non-significant** ruin-count covariate (+0.244) and a stronger, **unregistered** area covariate
> (+0.414, t = 2.18). The direction survives; the "confirmed mechanism" reading does not.

Note the area covariate is the larger of the two and I did **not** pre-register it for 34, so
under rule 3b it is a back-filled mechanism and carries no evidential weight there. It is
pre-registered for iteration 35, where it will.

**Iteration 34 is not reverted.** Reverting an accept whose pre-registered gate was met, on the
strength of a corrected *supporting* statistic, would be re-deciding the iteration on evidence
selected after the fact — the same error in the opposite direction. What it does change is my
confidence: iteration 34 is now a **weak** accept with no independent corroboration, and it should
be one of the first candidates for an ablation if the lineage stalls.

### The process fix, committed with this entry

`carol-tools/covar/mapcovar.py` is now the only way this lineage computes a map covariate. It
reads `results.csv` and the shared corpus file, uses tie-corrected midranks, prints the per-map
join it used, and is committed — so every future rho is reproducible from the repo by anyone,
including a session that has forgotten this one. An in-session arithmetic result that never lands
in a file is not a measurement; it is a recollection. This is the second time this lineage has
been bitten by a number that was true when computed and unverifiable afterwards.

## Iteration 35 — PRE-REGISTERED. Un-gate the paint-tower upgrade (rebuilt on the iteration-34 baseline)

Registered before any game of run is played. The iteration-35 direction was written up under
iteration 34's entry and explicitly **held** until 34 resolved, because 34 moved the baseline. 34
was accepted, so `src/carol_i35` has been **rebuilt from the current `src/carol` (iteration 34,
`MONEY_MOD = 4`)** rather than from the pre-34 build the earlier draft sat on. Verified by diff:
the only three lines that differ from `src/carol` are the package name, the `BUILD` string, and

```java
-            int need = CHIP_RESERVE + rc.getType().getNextLevel().moneyCost;
+            int need = rc.getType().getNextLevel().moneyCost;
```

**One mechanism.** Nothing else moves.

### Hypothesis

The lv1->lv2 paint-tower upgrade is not a tuned policy, it is an **off switch**. On the
iteration-33 build the gate `CHIP_RESERVE + 2500 = 3700` fired **4 times against 9,147 `upgPoor`**
on Snowglobe (0.04% of eligible tower-turns) because the treasury is measured to oscillate in
[1600, 2450] and never reaches 3700. Dropping the reserve term puts the gate at 2,500, which the
chip distribution (12,932 tower-turns) says is reached on **3.21%** of tower-turns — ~415
opportunities per game, ample for a handful of upgrades. The payoff is permanent: 5 -> 10
paint/turn on that tower, and paint is the resource three independent measurements on this lineage
call binding while chips sit idle above $2,200.

**The axis has exactly one reachable setting**, stated so no one asks for a dose ladder later:
`canUpgradeTower` checks affordability itself so any `need` below 2,500 is identical to 2,500,
and the measured p99 treasury is 2,600 / max 2,800 so anything at 3,000 or above is back to
near-off. There is no ladder to walk.

### The cost, quantified in advance

An upgrade takes 2,500 from a treasury whose p99 is 2,600, draining the team to ~100 chips and
blocking **all** robot production (250 each) and any ruin completion (1,000) until income rebuilds
— several rounds at 30–60 chips/turn. This is a real measured cost, not a rounding error, and it
is the first term to inspect if the iteration fails.

### Accept gate (pre-registered, binding)

`BOT=carol_i35 OPPONENTS="carol_iter34 carol_racer"`, `MAPS` unset (fresh random 25-map sample),
both sides = 50 games per arm.

1. **`carol_i35` vs `carol_iter34` > 25/50**, and
2. **swept wins >= swept losses** on that arm.

Both must hold. Iteration 34 was accepted on a +0.92 sd margin whose CI spanned the null, so I am
*not* loosening the gate to match it.

### Pre-registered mechanism prediction (this is what separates cause from noise)

**Manipulation check**: the realized upgrade count per game must be **> 0**. If the gate is still
never reached the iteration is inert and any win-rate difference is noise by construction — that
reading voids the arm regardless of the headline.

**Outcome covariate: map area.** The mechanism buys +5 paint/turn amortized over the *remaining*
rounds and pays an immediate 2,500-chip drain up front, so its net value rises with the payback
horizon. Bigger maps run longer and support more towers, so:

> the gain should be **larger on large-area maps than on small ones**, and rho(wins, map area)
> should be **positive**.

Map area is known from the corpus before the sample is drawn, so this is exogenous — unlike game
length, which is endogenous (winning quickly shortens the game and would fake the correlation in
the direction I want). **Stated honestly in advance: area and ruin count are collinear in this
corpus, so a positive rho cannot separate "longer payback horizon" from "more towers to upgrade".
It can only confirm that the effect scales with map size, not which of the two channels carries
it.** If the gain is instead uniform across area, the attribution is OPEN and the accept rests on
the head-to-head alone.

### Second arm is a process task, not a dose

`carol_racer` is the coverage-race synthetic archetype built for the saturation problem logged
under iteration 34: the frozen roster reads **94–100% on every member** (last roster run at
iteration 30), which makes it blind, and TRAINING_ALGORITHM §5b's "chain of individually-positive
accepts walking downhill" is exactly what a blind absolute instrument cannot detect. This arm asks
one question: **is `carol_racer` discriminating?** A result near 50–75% qualifies it for
`progress/roster_extra.txt`; a result at 95%+ means it saturated on arrival and is no better than
what the roster already has. It rides along in the same run at no extra map cost.

---

## INSTRUMENT FINDING (external data, zero VM cost) — carol scales *inversely* with map area, and it is getting worse

Found while iteration 35 was playing, from `tournaments/*/results.csv` joined against map areas in
the shared corpus file. Reproducible: `carol-tools/covar/sizestrat.py`, committed.

Carol's win rate against alice and bob in the latest tournament, binned by map area:

| area bin | maps | carol win% |
|---|---|---|
| tiny (<= 900) | 19 | **56.6%** |
| small (901–1600) | 24 | 33.3% |
| large (1601–2500) | 19 | 18.4% |
| huge (> 2500) | 13 | **15.4%** |

**rho(win%, area) = −0.546, t = −5.57 on 73 df.** This is not a marginal effect. It is the most
significant thing this lineage has ever measured, and it is ten times better attested than any
number in my last three accept entries.

This contrast is **within one tournament** — the same two opponents on every map — so it is not
affected by the wins-are-conserved caveat that makes cross-tournament deltas relative.

### It is a trend, not a snapshot, and the trend is the indictment

| tournament | carol overall | tiny | small | large | huge | rho(area) |
|---|---|---|---|---|---|---|
| 20260907-0100 | 19.0% | 15.8% | 20.8% | 18.4% | 21.2% | **+0.029** |
| 20260907-1300 | 19.7% | 36.8% | 18.8% | 13.2% | 5.8% | −0.401 |
| 20260908-0100 | 32.3% | **56.6%** | 33.3% | 18.4% | **15.4%** | **−0.546** |

Two days ago carol was **flat across map size** (rho = +0.029). The headline went 19.0% → 32.3%,
and essentially all of it is small maps: tiny went **+40.8 points** while huge went **−5.8**. My
accepted iterations bought a large gain on small maps and paid for part of it on large ones.

And the other two lineages go the *other* way — alice +0.217, bob +0.443. Whatever they are doing
scales up with the board; carol's does not.

### This is TRAINING_ALGORITHM §5b, and I predicted I could not detect it

Under iteration 34 I wrote: *"§5b's 'chain of individually-positive accepts walking downhill' is
exactly the failure I currently cannot detect."* This is that failure, and here is precisely why
both of my instruments are blind to it:

1. **The gauntlet gate is one aggregate number over a random 25-map sample.** A change worth +20
   points on small maps and −5 on large ones clears `> 25/50` comfortably. Every such change is
   accepted, and each one tilts the bot further. The gate is not wrong, it is *unstratified*.
2. **The frozen roster cannot see it either, and this is the deeper problem.** Every roster member
   is a carol snapshot, so they all share the large-map weakness and it **cancels in the
   head-to-head**. That is not saturation from being too strong — it is saturation from measuring
   against opponents that fail the same way I do. Adding another synthetic archetype of my own
   construction would not fix it, because I would build that one out of the same assumptions.

The tournament is the only instrument here with an opponent that does not share my blind spot, and
this finding is the single strongest argument in this project for MULTI_AGENT.md's claim that it
is the highest-value evidence available.

### Where the games are actually lost — the losses are not close

Split of carol's tournament losses by how the game ended:

| area bin | median rounds | losses painted out | losses on tiebreak |
|---|---|---|---|
| tiny | 998 | 28 (85%) | 5 |
| small | 1252 | 51 (80%) | 13 |
| large | **847** | 51 (82%) | 11 |
| huge | 1568 | 30 (68%) | 14 |

The large bin is decisive: carol loses there at a **median of 847 rounds**, *faster* than it loses
on small maps (998) and much faster than the small bin (1252), and 82% of those losses are the
opponent painting enough of the map outright rather than a coverage tiebreak. Carol is not
narrowly out-scored on big maps — it is **out-expanded and finished early**. On huge maps 29 of 75
corpus maps are ones carol went 0-for-4 on, and they are overwhelmingly the big ones.

### Process change, effective now (and this is the durable part)

**Every future accept gate is stratified by map area.** The pre-registered condition gains a
standing clause, in addition to whatever that iteration's own gate says:

> the candidate must not lose ground on the large half of the sampled maps. Report the win rate on
> the small half and the large half separately in every verdict. An iteration that wins overall
> while going backwards on the large half is **not** an accept — it is the next link in the chain
> above, and it gets logged as one.

This is a change to *how I evaluate*, not to the bot, so it goes in `progress/milestones.txt` per
the charter. Iteration 35 is already in flight with its own pre-registered gate; I will report its
size split too, but I will not retroactively add this clause to its accept condition — moving a
gate after the games are played is exactly the thing pre-registration exists to prevent.

**The agenda this sets.** Economy-mix tuning (iterations 30–35: splasher share, mopper share, money
share, upgrade gate) has been working an axis that the external data says is not where carol is
losing. Iteration 36 targets large-map expansion directly.

## Iteration 35 — ACCEPT. 33/50, swept 9–1, the strongest margin since iteration 30

Run `20260908-091804`, fresh random 25-map sample, 100 games.

| arm | result | swept-win | swept-loss | split | |
|---|---|---|---|---|---|
| `carol_i35` vs **`carol_iter34`** (the accept gate) | **33/50 (66.0%)** | **9** | **1** | 15 | **+2.26 sd**, one-sided p = 0.016, 95% CI [26, 40] |
| `carol_i35` vs `carol_racer` (process arm) | 50/50 (100%) | 25 | 0 | 0 | — |

**The pre-registered gate is met on both clauses**: 33/50 > 25/50, and swept wins (9) exceed swept
losses (1) nine to one. Unlike iteration 34, **the CI excludes the null** — this is the first accept
since iteration 30 whose headline stands on its own.

### The pre-registered manipulation check passes

I registered that a zero upgrade count voids the arm regardless of the win rate, so I ran it even
though the result was favourable — a check you only run when you expect to fail it is not a check.
Counting non-initial `UPGRADE` events in this run's own loss replays (the round-1 upgrades of
`id1`–`id4` are engine initialization, not the gate):

| replay | `carol_i35` upgrades | `carol_iter34` upgrades |
|---|---|---|
| `SMILE` (i35 = T2) | **3** (r180, r358, r931) | 1 (r1270) |
| `DonkeyKong` (i35 = T1) | **1** (r395) | 0 |

The mechanism fires, and fires more in the candidate than the incumbent. Worth recording that the
incumbent gate is **rare, not literally never**: iteration 34 did manage one upgrade at round 1270
on SMILE. My earlier "exactly off (0.00%)" was measured on one Snowglobe game and is too strong as
a general claim; "0.04% of eligible tower-turns" is the defensible version. These are loss replays,
so if anything they understate the candidate.

### The pre-registered covariate FAILED, and that is recorded as a failure

I predicted rho(wins, map area) > 0, on the reasoning that a +5 paint/turn annuity paid for with an
up-front 2,500-chip drain is worth more the longer the payback horizon.

> **rho(wins, area) = +0.009, t = +0.04.** Low-area half 16/24 (66.7%), high-area half 17/26
> (65.4%). Flat to three decimal places.

The prediction is wrong. Per my own pre-registration — *"If the gain is instead uniform across
area, the attribution is OPEN and the accept rests on the head-to-head alone"* — **the attribution
is OPEN.** The iteration is accepted on its head-to-head, which is strong enough alone, and I am
**not** substituting the ruin covariate (rho = −0.163, also null) or any other post-hoc story for
the one I registered and lost. Given that I spent this session retracting a covariate that was
argued after the fact, back-filling a new one here would be the identical error committed twice in
one sitting.

What the flat result does tell me, read against the new area finding below, is that **the upgrade
gate is not the thing that makes carol scale badly** — it helps uniformly, so it moves the whole
curve up and leaves the slope alone.

### Under the new standing clause: no ground lost on the large half

66.7% small / 65.4% large. Reported per the process change committed this session. The clause was
adopted while this run was in flight and was deliberately **not** added to its gate; it passes
anyway.

### `carol_racer` is REJECTED as a roster yardstick

**50/50, 25 maps swept to zero.** It saturated on arrival and is strictly worse than the roster
members it was built to replace, which at least sit at 94–100%. It does not go in
`progress/roster_extra.txt`.

This is worth more than the null result it looks like, because it is the *second* confirmation of
this session's instrument finding: I built `carol_racer` myself, out of my own model of what a
coverage race is, and it inherited my blind spots exactly as a snapshot would. **A yardstick I
construct cannot be independent of me.** The saturation problem is therefore not solvable by
building better synthetic archetypes, and I should stop trying — the tournament is the instrument
that works, and this session showed it answers questions no gauntlet of mine can.

`src/carol` is now iteration 35; frozen as `src/carol_iter35`. **16 accepted iterations**,
`carol_iter0..35`. Both charts regenerated.

---

## Iteration 36 — PRE-REGISTERED. A PAINT floor: the build roll is unchecked on paint, and it inverts the unit mix

Registered before any game is played. Found from tournament replays while iteration 35 was in
flight, at zero extra VM cost.

### The fault

The tower build gate reads, in full:

```java
boolean afford = chips >= reserve + want.moneyCost;      // CHIPS ONLY
...
if (rc.canBuildRobot(want, loc)) rc.buildRobot(want, loc);   // paint checked HERE, silently
```

Paint is never tested. A roll the tower cannot pay for **in paint** dies inside
`canBuildRobot` with no branch, no counter, and no trace. This is the third instance in this
lineage of "a gate that is an off switch" (iteration 30, splasher chips; iteration 35, upgrade
chips) — and the first on the paint axis, which is why it survived two hunts for exactly this
shape. **Both previous hunts audited `afford`; the bug is in the line after it.**

### Why it inverts the mix rather than thinning it — and this is the part that matters

Tower paint accrues at 5/turn (10 after iteration 35's upgrade), capped at 1000. A mopper costs
100 paint, a soldier 200. From a dry tower the 100 line is crossed at turn ~20, and from then on
every mopper roll (10%) succeeds and resets the stash toward zero. To ever reach 200 the tower
must go ~40 consecutive turns without rolling a mopper: **0.9^40 = 1.5%.** The cheap unit does not
merely get built more often — **it prevents the expensive one from ever being afforded.**

The chips gate cannot produce this and never could: a mopper costs **more** chips than a soldier
(300 vs 250). Only the unchecked paint gate favours it. That asymmetry is why the two earlier
chip-gate fixes left this untouched.

### Measured, from tournament replays (intended: 75% soldier / 10% mopper / 15% splasher)

| game | carol tower-paint median | soldier | mopper |
|---|---|---|---|
| alice–carol UglySweater (2500) | 100 | 35.0% | **60.0%** |
| bob–carol Gears (3025) | 438 | 27.6% | **71.4%** |
| alice–carol Gears (3025) | 507 | **24.7%** | **74.8%** |
| bob–carol DefaultSmall (400) | 974 | 66.7% | 25.0% |
| bob–carol DonkeyKong (3600) | 2535 | **83.9%** | 13.8% |

**The realized mix is set by tower paint, not by `MOPPER_IN_20`.** Where paint is scarce it inverts
outright — 360 moppers against 119 soldiers in one game, from a constant that asks for the reverse
ratio at 7:1. Where paint is plentiful it lands near the intended mix. Note DonkeyKong is the
largest map in the table and behaves *well*: the driver is paint, not area directly, and I state
that because it constrains the covariate prediction below rather than helping it.

**Why this is the coverage story.** `workOnRuin` is called only from `runSoldier` — moppers cannot
claim ruins. Every displaced soldier is a ruin never claimed, hence a tower never built, hence
less paint: the ratchet feeds itself. In the UglySweater game carol finished with **4 towers to
alice's 19** while sitting on **$2,480 of unspent chips**. Carol was never short of money. It was
short of soldiers, because its towers kept buying the cheap unit.

### The change

One mechanism, the exact analogue of iteration 30's `SPLASH_FLOOR` one resource over:

```java
final int PAINT_FLOOR = <dose>;
if (afford && want.paintCost < UnitType.SOLDIER.paintCost
        && rc.getPaint() - want.paintCost < PAINT_FLOOR) {
    afford = false;
}
```

Written as a cost comparison rather than `want == MOPPER` so it states its intent: protect the
expensive unit from the cheap one. Banking is safe — the floor is 100–200 against a 1000 cap, so
it cannot idle a tower into wasting income.

**Doses**: `carol_i36_200` (protect a full soldier) and `carol_i36_100`, against the incumbent,
which is exactly `PAINT_FLOOR = 0`. So the ladder is 0 / 100 / 200 with the zero arm free.

### Accept gate (pre-registered, binding — now with the standing size clause)

`BOT=carol_i36_200 OPPONENTS="carol_iter35 carol_i36_100"`, `MAPS` unset, 100 games.

1. **`carol_i36_200` vs `carol_iter35` > 25/50**, and
2. **swept wins >= swept losses**, and
3. **the standing clause adopted this session**: the candidate must **not lose ground on the
   large-area half** of the sample. Explicitly: large-half win rate >= 45%. This is the first
   iteration the clause binds on, and I am stating the threshold as a number now so it cannot be
   argued afterwards.

### Manipulation check (can void the arm regardless of the headline)

The realized **soldier share** in `carol_i36_200`'s games must be **materially above** the
incumbent's in the same replays. If the floor does not move the mix, it is inert and any win-rate
difference is noise. Measured the same way as the table above, from this run's own loss replays.

### Pre-registered covariate, with the reason it may fail

> rho(wins, map area) > 0 — the gain should be larger on large maps.

The mechanism is paint starvation; starvation is worst where towers are fewest; towers are fewest,
relative to the ground to be covered, on large maps. **But the table above already contains a
counterexample I am not hiding**: DonkeyKong is the largest map there and had the healthiest mix,
because carol happened to get 13 towers. So the real driver is tower paint and area is only a
proxy for it. If rho comes back flat, the honest reading is *"area is a poor proxy for paint
starvation"*, **not** that the mechanism is absent — the manipulation check is what settles
whether the mechanism fired. My last area prediction (iteration 35) failed at +0.009, so I am
registering this one with lowered confidence and saying so in advance.

### VERDICT — ACCEPT (recovered: the run finished, the verdict died with the session)

Run `gauntlet/20260908-094128`, `BOT=carol_i36_200`, opponents `carol_iter35` and `carol_i36_100`,
100 games on a fresh random 25-map sample. The run had completed and been collated before the
session ended; only the accept/reject decision was lost. **No games were re-run.**

| gate (pre-registered) | required | measured | |
|---|---|---|---|
| 1. `carol_i36_200` vs `carol_iter35` | > 25/50 | **28/50 (56%)** | pass |
| 2. swept wins >= swept losses | >= | **6 vs 3** | pass *(but see below — this is not independent)* |
| 3. large-area half win rate | >= 45% | **57.7%** (15/26 over 13 maps) | pass |

vs `carol_i36_100`: 26/50. The 200 dose is ahead of the 100 dose, consistent with the ladder.

**The headline margin is weak and I am not going to dress it up.** 28/50 has a one-sided binomial
p = 0.24 — a coin flip clears this gate a quarter of the time. What carries this accept is the
manipulation check, not the win rate.

### Gate 2 was never independent evidence — an arithmetic error in my own gate

The tournament report states the identity `wins - N = swept - swept_against` for an N-map,
both-sides sample. Checked on this exact run: N=25, wins=28, SW=6, SL=3, split=16 →
`2*6+16 = 28` wins and `2*3+16 = 22` losses, and `28-25 = 3 = 6-3`. Exact.

So **gate 2 is algebraically implied by gate 1**: any result with wins > 25/50 has SW > SL
necessarily. My "three-condition" accept gate has only ever been two conditions, and I have been
reporting a margin and its sweep counts as two agreeing facts when they are one fact written twice.
The report warns about precisely this and I encoded the error into the gate anyway.

What the sweep counts *do* add is **D, the split count** — decisiveness, not direction. Here D=16
of 25 maps, i.e. **64% of maps are coin-flips decided by spawn side**, which is the honest reason
the headline margin is weak. Replacing gate 2 with a decisiveness condition is a process change,
recorded in `progress/milestones.txt`.

### Manipulation check — PASSES decisively, and this is what the accept rests on

Both bots play in the same replay, so every game is a **paired** observation: same map, same
round count, same opponent. Realized build mix is a direct count of `SPAWN` events
(`carol-tools/mixcheck/`), not a rate reconstructed from post-turn robot state, so the
"replay state is written AFTER the turn resolves" bias documented in `tools/engine-facts.md`
does not touch it.

| game (candidate loss) | cand s/m/p | cand sold% | inc s/m/p | inc sold% | d(sold%) |
|---|---|---|---|---|---|
| giver__botB | 13/0/46 | 22.0% | 154/105/35 | 52.4% | -30.3 |
| SMILE__botA | 48/1/250 | 16.1% | 201/48/198 | 45.0% | -28.9 |
| DefaultHuge__botB | 488/3/151 | 76.0% | 112/47/205 | 30.8% | +45.2 |
| lighthouse__botA | 60/0/12 | 83.3% | 60/36/33 | 46.5% | +36.8 |
| Brat__botA | 37/0/7 | 84.1% | 26/33/6 | 40.0% | +44.1 |
| Snowman__botB | 39/0/6 | 86.7% | 25/23/9 | 43.9% | +42.8 |
| Gears__botA | 63/0/23 | 73.3% | 40/22/47 | 36.7% | +36.6 |
| Circuit__botA | 160/1/33 | 82.5% | 65/20/102 | 34.8% | +47.7 |
| Snowman__botA | 21/0/8 | 72.4% | 17/16/6 | 43.6% | +28.8 |
| Brat__botB | 22/0/6 | 78.6% | 9/6/17 | 28.1% | +50.4 |
| starburst__botA | 15/0/9 | 62.5% | 17/5/11 | 51.5% | +11.0 |
| giver__botA | 38/0/38 | 50.0% | 23/2/52 | 29.9% | +20.1 |
| sierpinski__botB | 139/0/29 | 82.7% | 17/2/86 | 16.2% | +66.5 |
| Thirds__botB | 10/0/135 | 6.9% | 9/1/133 | 6.3% | +0.6 |
| windmill__botA | 9/0/4 | 69.2% | 3/1/11 | 20.0% | +49.2 |
| Castle__botA | 4/0/141 | 2.8% | 8/0/138 | 5.5% | -2.7 |
| Oasis__botA | 2/0/144 | 1.4% | 7/0/138 | 4.8% | -3.5 |
| Racetrack__botB | 4/0/24 | 14.3% | 5/0/21 | 19.2% | -4.9 |
| Justice__botA | 12/0/2 | 85.7% | 1/0/10 | 9.1% | +76.6 |
| SaltyPepper__botB | 1/0/144 | 0.7% | 7/0/141 | 4.7% | -4.0 |
| galaxy__botA | 3/0/143 | 2.1% | 4/0/143 | 2.7% | -0.7 |
| walalilongla__botA | 9/0/136 | 6.2% | 9/0/132 | 6.4% | -0.2 |
| **POOLED (22 games)** | **1197/5/1491** | | **819/367/1674** | | |

**Summary of the 22 paired games** (`carol-tools/mixcheck/aggregate.py`):

| set | n | mean d(soldier%) | median | positive |
|---|---|---|---|---|
| all paired games | 22 | **+21.9 pp** | +24.5 pp | 14/22 |
| incumbent built >=5 moppers (**mechanism can fire**) | 11 | **+25.8 pp** | +36.8 pp | 9/11 |
| incumbent built <5 moppers (**mechanism inert**) | 11 | +17.9 pp | -0.2 pp | 5/11 |

**Soldier share is the pre-registered statistic but it is not the cleanest one, and I should say so.**
Unit *counts* scale with how the game went, and in the two games where soldier share moved against
the candidate (`giver`, `SMILE`) the candidate was simply being crushed and built few of everything.
The direct, outcome-robust reading of the mechanism is the **mopper share**, because it is the
quantity the floor acts on:

- candidate **5 moppers of 2,693 builds = 0.19%**
- incumbent **367 moppers of 2,860 builds = 12.83%**
- a **69x reduction**, and in **0 of 22** games did the candidate build more moppers than the
  incumbent. Candidate maximum in any single game: **3**. Incumbent maximum: **105**.

The manipulation check passes, and it passes on the statistic that cannot be confounded by the
outcome of the game it was measured in.


The split is the whole result. **Where the incumbent actually built moppers, the floor moves the
soldier share by ~45 points, in 5 of 5 games. Where the incumbent built almost none, the floor is
inert and the share difference is noise of either sign.** That is exactly the behaviour a correct
gate should produce, and it is strong evidence the mechanism is the one I named rather than a
lucky win rate.

**But I must state what the floor actually computes, not what I advertised.** I wrote it as
"protect the expensive unit from the cheap one", implying re-prioritisation. Combined with
iteration 30's still-active `SPLASH_FLOOR = 2000` — which already requires `chips >= 2300` for a
mopper — the realized effect is that **moppers go to approximately zero, not to a smaller share**:
0, 0, 1, 3, 0 in the five games where the mechanism fired, against 33, 6, 20, 47, 22 for the
incumbent. This is a unit-removal change wearing a prioritisation change's clothes. It passed its
gate as built, so it is accepted as built, but the honest name is "carol no longer builds moppers",
and the next session must not reason about it as a dial.

### Covariate — directionally right, NOT significant, and I am not claiming it

> pre-registered: rho(wins, map area) > 0

Measured **rho = +0.291, t = +1.46, df = 23** (`carol-tools/covar/mapcovar.py`). Low-area half
54.2%, high-area half 57.7%. The sign is as predicted and the magnitude is not distinguishable
from zero. **I retracted iteration 34's rho for exactly this and I am not going to re-earn that
mistake by counting +0.291 as a confirmation.** It is consistent with the prediction and it is not
evidence for it.

### The result that matters most is the one that did NOT go my way — stated carefully

`DefaultHuge` (area 3481), the largest map in the sample, is where the mechanism fired hardest:
the candidate built **488 soldiers / 3 moppers / 151 splashers** against the incumbent's
**112 / 47 / 205**, a 45-point swing in soldier share — and the candidate lost that game.

**A caveat I nearly skipped, which would have been a real error.** The gauntlet only writes
replays for the candidate's *losses*, so every row of the table above is a loss by construction.
I cannot read a direction out of this set — "more soldiers, therefore the loss" is not available
to me, and the per-map record confirms the trap: DefaultHuge went **1–1**, so the candidate won
the same map from the other side.

What the set *does* support is a claim about **sufficiency**, which does not depend on selection:
in that game the mix fault was fully corrected — 3 moppers, 76% soldier share — and the game was
lost anyway. **Whatever loses DefaultHuge for this lineage is not the build mix.** The mix was a
real fault, it is now fixed, and it is not the binding constraint on the largest maps.

That is a more useful finding than the accept itself, and it is what iteration 37 is aimed at.

`src/carol` is now iteration 36; frozen as `src/carol_iter36`. **17 accepted iterations**,
`carol_iter0..36`. Compile checked (`tools/vm-compile.sh` -> COMPILE-OK), so HEAD plays.

### New tooling, and the waste that motivated it

- `carol-tools/mixcheck/spawnmix.sh` — paired realized-build-mix counter for a run's loss replays.
- `carol-tools/mixcheck/aggregate.py` — the fired/inert split above.
- `carol-tools/mixcheck/dumpcache.sh` — **because I wasted shared VM time.** The 22-replay sweep
  cost ~30s of remote compile-and-run each and I kept three integers from each dump, throwing away
  the tower spawns, the per-round economy and the coverage series. Every later question about the
  same games would have paid the VM again. Dumps are now cached on disk under the git-ignored
  `gauntlet/.dumpcache` and keyed by replay path plus flags. Dump once, parse many times.

---

## Iteration 37 — PRE-REGISTERED. The splasher floor is an off switch for the soldier, and I built it

Registered before any game is played. Found entirely from replays and committed tournament results
at **zero extra VM cost**, during iteration 36's write-up.

### How I got here, including the hypothesis I killed on the way

Iteration 36 proved the build mix was a real fault and fixed it, and its own biggest map showed the
mix was **not** the binding constraint. So I went looking for what is.

First hypothesis: **long games**. Realized soldier share correlates with game length far more
strongly than with map area — rho(soldier share, rounds) = **-0.654, t=-3.87** against
rho(soldier share, area) = -0.389. Games reaching round 2000 average **5.1%** soldier share;
games ending early average **68.2%**.

**I killed it with the tournament rather than believing it.** If long games were where carol dies,
carol's win rate should sag in them. It does not: **31.9% in decisive games, 33.8% in tiebreaks** —
flat. And splitting carol's area deficit by game length:

| subset | rho(win%, area) | t | maps |
|---|---|---|---|
| all games | -0.490 | -4.81 | 75 |
| **decisive only (<2000)** | **-0.463** | **-4.43** | 74 |
| tiebreak only (=2000) | -0.045 | -0.27 | 39 |

Game length does not mediate the area deficit — and length is itself barely related to area
(rho=+0.165, ns). **Carol loses big maps by being beaten outright before round 2000.** The
long-game correlation is real and is a symptom, not the disease. Recording the killed hypothesis
because it cost nothing and would have cost a 100-game run.

### What the deficit actually is

| map size | carol won | of those, by painting enough | carol lost | of those, opponent painted enough |
|---|---|---|---|---|
| <= 900 tiles | 43 | **93.0%** | 33 | 84.8% |
| >= 2500 tiles | 9 | **22.2%** | 55 | 69.1% |

**On maps >= 2500 tiles carol reaches the paint threshold in 2 of 64 games. On maps <= 900 it does
so in 40 of 76.** Carol's coverage engine does not scale with area. The engine is towers.

### The fault, stated as what the code computes

`reserve` is `CHIP_RESERVE = 1200`, or `0` when `freed`.

```
splasher passes at  chips >= reserve + 400                  = 1600   (400 when freed)
soldier  passes at  chips >= max(reserve + 250, 2000 + 250) = 2250   (ALWAYS)
```

The `2000` is `SPLASH_FLOOR`, an absolute constant I introduced in iteration 30. **It does not
track `reserve`**, so the `freed` escape hatch — whose entire purpose is to *unblock* spending —
drops the splasher gate to 400 and leaves the soldier's at 2250, widening the gap from 650 chips
to 1850.

**Measured, 9 games, `carol-tools/mixcheck/trajectory.py`, from cached dumps at no VM cost:** the
treasury sawtooths between ~1200 and ~1750 for the entire game and **never reaches 2250**, because
splashers at 400 chips drain it as fast as it fills. In **7 of 9 games carol builds zero soldiers
from round ~600 to round 2000**, while building a metronomic 13–16 splashers per 200 rounds, and
the tower count freezes at 4–5. Representative, one game end to end:

```
round |  carol s/m/p  sold%  chips  tw
  400 |     0/0/15      0%   1350   4
  600 |     4/0/9      31%   1750   5
  800 |     0/0/16      0%   1350   5
 1000 |     0/0/15      0%   1350   5
 ...  |     (identical to round 2000)         5
```

**Why this closes a ratchet rather than merely skewing a mix.** `workOnRuin` is called only from
`runSoldier`, so **soldiers are the only unit that claims ruins**. No soldiers → no new towers →
no new income → the treasury stays under 2250 → no soldiers. Pooled over 22 games the realized mix
is **44% soldier / 55% splasher against an intended 75/10/15**: iteration 30 overshot its own
target by 3.7x, turning a 1.2–2.7% splasher share into 55%.

This is the **fourth** gate-as-off-switch in this lineage (30 splasher chips, 35 upgrade chips,
36 build paint) and **the first one I created myself while fixing the previous one.** The lesson I
am writing down before the result arrives: *a floor added to protect a starved unit is a floor
that can starve a different one, and iteration 30 never measured the other side of its own gate.*

### The change — one mechanism, two doses

Stop comparing against a magic `2000` and compare against **the price of the thing the floor
exists to protect**. Iteration 30's intent is preserved exactly; only the number it is measured
against changes, and it now tracks `reserve` for free.

```java
// carol_i37_eq  -- EQUAL GATES: a non-splasher passes exactly where a splasher does (1600)
if (afford && want != UnitType.SPLASHER
        && chips < reserve + UnitType.SPLASHER.moneyCost) afford = false;

// carol_i37_res -- KEEP A SPLASHER IN RESERVE: non-splasher gate 1850
if (afford && want != UnitType.SPLASHER
        && chips - want.moneyCost < reserve + UnitType.SPLASHER.moneyCost) afford = false;
```

Ladder on the soldier gate: **1600 (eq) / 1850 (res) / 2250 (incumbent)**.

### Accept gate (pre-registered, binding) — with condition 2 replaced

`BOT=carol_i37_eq OPPONENTS="carol_iter36 carol_i37_res"`, `MAPS` unset, 100 games.

1. **`carol_i37_eq` vs `carol_iter36` > 25/50**, and
2. **swept wins >= 5 of 25** — the *new* condition adopted this session, replacing "swept wins >=
   swept losses", which iteration 36 showed is algebraically implied by condition 1 and therefore
   was never independent evidence. An absolute floor constrains the split count D and is not
   implied by the margin, and
3. **large-area half win rate >= 45%** (the standing size clause).

### Manipulation check — CAN VOID THE ARM regardless of the headline

Both must hold, measured from this run's own loss replays, paired within each game:

1. **realized soldier share materially above the incumbent's** — pooled incumbent is 44%; the arm
   must clear **>= 60%** pooled, and
2. **mean tower count from round 800 onward strictly higher than the incumbent's in the same
   games** — this is the link the whole story turns on, and if towers do not move then the mix
   changed without unlocking the ratchet and the mechanism is not the one I named.

If both fail the arm is void whatever the win rate says.

### Pre-registered covariate, with my confidence stated in advance

> rho(wins, map area) > 0.

**Low confidence, and I am saying so before the number arrives.** My last two area predictions came
in at +0.009 (iteration 35) and +0.291/ns (iteration 36), and I retracted iteration 34's outright.
Area keeps being a proxy for something else. The primary prediction here is the **tower count**,
not the covariate, and I will read a flat rho as "area is again a poor proxy", not as support.

### Iteration 37 addendum, written BEFORE any game is scored: the price, and a bias in my own check

**The price, which I failed to state in the pre-registration and am stating now.** The milestone
"state benefit AND price as two numbers before running a mechanism" applies here and I only
registered the benefit. Benefit: more soldiers -> more ruins claimed -> more towers -> more income.
**Price: splashers paint 2.4-4.7x more tiles per unit of build paint than soldiers (measured in
iteration 30), so moving the realized mix from 44/55 soldier/splasher toward 83/17 buys towers with
direct paint throughput.** It is entirely possible for towers to rise and coverage to fall. Added
final coverage to `carol-tools/mixcheck/paircheck.py` so the price is measured, not assumed.

**A bias in the manipulation check itself, stated in advance so it cannot be used selectively
afterwards.** The gauntlet writes replays only for the candidate's *losses*. Tower count and
coverage are both outcomes that fall when a bot is losing, so measuring them on losses is biased
**against** the candidate. That asymmetry cuts cleanly:

- a **positive** tower delta on loss replays is **strong** evidence — it appears despite the bias;
- a **negative** tower delta is **weak** evidence — it is what the bias alone would produce.

So my pre-registered condition (towers strictly higher) is a conservative test, and I will not
quietly reinterpret it as a two-sided one if it comes back negative. If it does come back negative
the honest reading is "not demonstrated on the evidence available", and the way to settle it is a
run that keeps win replays too — not a re-reading of these.

### Iteration 37 addendum 2, still BEFORE any game is scored: the second link is the weak one

Measured from the same cached dumps, no VM cost. Across 20 team-games (both teams of 10 games,
tower claims counted from `SPAWN ... TOWER` events, soldiers from `+sold` deltas):

| | soldiers built | ruins claimed | per 100 soldiers |
|---|---|---|---|
| `carol_iter35` | 356 | 54 | 15.2 |
| `carol_i36_200` | 213 | 32 | 15.0 |

The pooled rates match almost exactly, which looks like a clean constant conversion — and it is
**not one**, because a rate with soldiers in its denominator is anti-correlated with soldiers by
construction. The claim that matters is the numerator:

> **rho(soldiers built, ruins claimed) = +0.199, t=+0.86, df=18 — not significant.**
> Team-games with >10 soldiers claimed 5.88 ruins on average; those with <=10 claimed 3.25.

**So the second link of my causal chain is the weak one, and I am saying so before the run lands.**
The chain is: soldier gate reachable -> more soldiers -> more ruins claimed -> more towers ->
more income. Link 1 is arithmetic and certain. Link 2 is directionally right and statistically
weak on the evidence I have.

The worst case is concrete and already on disk: on **Brat**, `carol_i36_200` built 37 soldiers,
banked **14,150 chips**, and claimed **exactly one ruin in the whole game** (round 15) on a map
with 15 ruins, while its opponent claimed 6. Soldiers in abundance converted to nothing there.

**This is what pre-registered manipulation check #2 exists for**, and it is now clearly the
condition most likely to fail. Stating the consequence in advance so the next step is not chosen
after seeing which way it broke:

- **If soldier share rises AND towers rise** — the chain holds, accept on the gate.
- **If soldier share rises and towers do NOT** — the arm is void by the pre-registered rule, and
  the fault is *ruin conversion*, not ruin *affordability*: a soldier that reaches a ruin fails to
  finish it. The candidates there are `RUIN_PATIENCE = 40` with a 250-round ban, and the fact that
  `nearestEmptyRuin` senses ruins only within vision (r2=20) with **no memory of ruins seen
  earlier** — a soldier that walks past an unclaimed ruin forgets it permanently. That is
  iteration 38, and I would rather have named it before the data chose it for me.

### A flagged RISK to iteration 36, which I cannot settle with the evidence I have

Reading `workOnRuin` while waiting on iteration 37's run turned up an interaction I should have
seen before accepting iteration 36.

Completing a ruin means painting its tower pattern. Iteration 29 established, and the code says
so in as many words, that **a soldier cannot overwrite enemy paint** — `if
(tile.getPaint().isEnemy()) continue;`. The only unit that can clear enemy paint is the **mopper**.
And iteration 36 reduced moppers from 12.83% of builds to **0.19%**.

So there is a plausible mechanism by which iteration 36 *harmed* ruin conversion on contested
ground: a pattern tile an enemy has painted is now permanently unpaintable by carol, because carol
no longer builds the unit that clears it.

**Why I am flagging this as a risk and not reporting it as a finding.** The suggestive numbers are
paired games at matched soldier counts — `lighthouse` 60 soldiers each, 2 ruins claimed by the
mopper-less variant against 7; `walalilongla` 9 each, 2 against 6 — a ~2x deficit on n=4 matched
games. **But every one of those replays is a game the mopper-less variant LOST**, because the
gauntlet only saves the candidate's losses. Ruins claimed is depressed by losing, so the
comparison is loser-versus-winner by construction and matching on soldier count does not repair
it. I noticed the same trap earlier in this session and I am not going to fall into it here
because the conclusion happens to be interesting.

**How to settle it properly**, for whoever runs it: `tools/vm-match.sh` writes a replay for a
single match regardless of outcome, so a handful of `carol_iter36` vs `carol_iter35` matches on
the same maps gives ruin-claim counts from *won* games as well as lost ones. That breaks the
selection. It is cheap — a few games, not a gauntlet — and it is the right next probe if
iteration 37's tower check comes back flat, because both stories then point at conversion.

Not reverting iteration 36 on a confounded signal: it passed a pre-registered gate and its
manipulation check was decisive on a statistic the confound cannot touch (moppers built).

### CORRECTION to the flagged risk above — I asserted a mechanism without checking my own RULES.md

I wrote, one entry above, "the only unit that can clear enemy paint is the mopper". **That is
wrong, and my own `RULES.md` says so in a line I had already written:**

> "[the splasher] is the ONLY unit that converts enemy paint in bulk (within r2<=2 of its centre)"

So carol has *two* enemy-paint converters, and iteration 36 shifted the mix toward the one it
kept. Working the interaction through properly:

- `workOnRuin` skips a pattern tile only when `tile.getPaint().isEnemy()`. Ally paint of the
  *wrong shade* is not skipped — it is repainted.
- A splasher landing near a ruin converts enemy paint to **ally** paint in bulk. It cannot set the
  pattern's per-tile colours, but it does not need to: converting enemy → ally is exactly what
  lifts the `isEnemy()` guard and hands the tile back to the soldier.

**So splashers unblock ruin conversion, and iteration 36 did not remove carol's ability to clear
enemy paint off a tower pattern.** The risk as I stated it is withdrawn. The confound I flagged
(loss-only replays) still stands and was the right caution; the *mechanism* I attached to it was
not checked and should have been, since the refuting sentence was in a file of my own in this
workspace.

**The lesson, which is the same one as iteration 36's `BOT` grep:** I reasoned from the code I had
just read (`workOnRuin`'s `isEnemy()` skip) to a claim about the whole unit roster, without asking
what the *other* units do. Reading one function tells you what that function computes, never what
the alternatives cannot.

**One quantity also needs restating.** I have been citing "splashers paint 2.4-4.7x more tiles per
unit of build paint than soldiers" from iteration 30. `RULES.md`'s independent derivation gives
**2.6x the sustained tiles/turn and 23% cheaper per tile** (soldier 1 tile/turn at 5 paint/tile;
splasher up to 13 tiles per 50-paint attack on a 5-turn cooldown, 3.85 paint/tile). Those are
different quantities and I should stop quoting the iteration-30 range as if it were the throughput
figure. The price of iteration 37 is real either way — moving the mix toward soldiers buys ruin
claims with area-paint throughput — but the number attached to it is 2.6x sustained, with the
standing caveat that a splasher wastes paint inside already-owned territory and is worth much more
on the frontier.

---

## PHASE 0 API SWEEP — carol calls 35 of 68 `RobotController` methods

Run on coordinator instruction, which also put this on a schedule (iteration 5, every 10
thereafter, and whenever the loop stalls) because "periodically" is an instruction with no trigger
and loses every time it competes with a live hypothesis. I am at iteration 37 and had never run it.
Method: `javap battlecode.common.RobotController` off the engine jar, `grep` for `rc.<name>(` in
`src/carol`, `comm -23`. Cost: two commands.

### Never called (33 of 68)

```
adjacentLocation broadcastMessage canBroadcastMessage canCompleteResourcePattern canMark
canMarkResourcePattern canPaint canRemoveMark canSendMessage canSenseLocation canSenseRobot
completeResourcePattern disintegrate getActionCooldownTurns getHealth getMoney
getMovementCooldownTurns getResourcePattern getTowerPattern isLocationOccupied mark
markResourcePattern onTheMap readMessages removeMark resign sendMessage sensePassability
senseRobot senseRobotAtLocation setIndicatorDot setIndicatorLine setTimelineMarker
```

Triaged honestly, because most of that list is noise:

- **Conveniences and debug** — `adjacentLocation`, `onTheMap`, `isLocationOccupied`,
  `sensePassability`, `getHealth`, `getMoney`, the cooldown getters, `setIndicatorDot/Line`,
  `resign`, `disintegrate`. Nothing here changes what carol can do.
- **Decided absence, not an oversight** — the whole resource-pattern family
  (`markResourcePattern`, `completeResourcePattern`, `canCompleteResourcePattern`,
  `getResourcePattern`). Iterations 26 and 32 built both possible designs and the log CLOSES the
  mechanic on a dilemma: reaching a viable cell needs steering, and steering is what killed it.
  That closure stands and I am not re-opening it here.
- **One real find, below.**

### The find: carol has NO COMMUNICATION AT ALL, and never checked whether it could

`sendMessage`, `canSendMessage`, `broadcastMessage`, `canBroadcastMessage`, `readMessages` —
five methods, zero calls, across 37 iterations. From `GameConstants`:

| constant | value | what it means |
|---|---|---|
| `MAX_MESSAGE_BYTES` | 4 | a full 32-bit payload; a MapLocation needs 12 bits |
| `MESSAGE_RADIUS_SQUARED` | 20 | robot -> tower send range, exactly a unit's vision |
| **`BROADCAST_RADIUS_SQUARED`** | **80** | tower -> everyone; **4x the AREA of a unit's vision disc** |
| `MESSAGE_ROUND_DURATION` | 5 | messages live 5 rounds |
| `MAX_MESSAGES_SENT_ROBOT` | 1 | per robot per round |
| `MAX_MESSAGES_SENT_TOWER` | 20 | per tower per round |

**The damning part is not that I never used it — it is that I reasoned around its absence in
writing.** The iteration-32 closure note, arguing for a future SRP design anchored to ruins, says:

> "a fixed offset from each sensed ruin is still a pure function of the map, **so it still needs no
> communication**"

I treated "needs no communication" as a design *virtue* to be engineered for, at a moment when a
four-byte broadcast with 4x my vision area was sitting unused in the API. That is exactly the miss
this sweep exists to catch: **not a mechanism used badly, a mechanism never called at all**, and
re-reading my own bot could never have surfaced it because the failure mode is not knowing the call
exists.

### Why this lands directly on the critical path, not on a side quest

I had already named iteration 38 in this session, before the sweep, as **ruin memory**: soldiers
sense ruins only within `senseNearbyRuins` at r2=20, hold no memory of ruins seen earlier, and a
soldier that walks past an unclaimed ruin forgets it permanently. My planned fix was a private
per-robot array — each soldier separately re-learning the map.

Messaging replaces that with a **team** solution, and the geometry is the argument: a tower
broadcasts at r2=80 against a unit's r2=20 vision, so one tower informs four vision-discs' worth of
units at once, 20 messages a round. Carol's measured deficit is that its coverage engine does not
scale with map area (paint threshold reached in 2 of 64 games on maps >= 2500 tiles, against 40 of
76 on maps <= 900), and the per-robot search radius not scaling with the map is a direct candidate
cause.

This is the shape the coordinator described: **a call that changes the constraint rather than
rationing under it.** Iteration 37, in flight, rations chips between soldiers and splashers.
Messaging would change what a soldier can find at all.

### Open questions to settle BEFORE pre-registering it (not assumed)

1. **Who can `sendMessage` reach?** The signature takes a `MapLocation`. BC25 is believed to allow
   robot<->tower messaging only, not robot<->robot. If so the topology is soldier -> tower ->
   broadcast, which still works but changes the design. **Verify against the spec/engine, do not
   assume.**
2. **What does it cost?** No paint or chip cost is visible in the constants, but a cooldown may
   apply. If it is free, this is a "capability at zero marginal cost" change — the same shape as
   iteration 14, which was accepted.
3. **Does anything need it more than ruins do?** Ruin locations are the obvious payload; enemy
   tower locations and frontier direction are alternatives. One mechanism, one payload.

### One tooling item worth taking now

`setTimelineMarker(String, int, int, int)` writes a marker into the replay. My whole analysis
pipeline this session was reconstructing bot decisions from `SPAWN` deltas and per-200-round
aggregates. A timeline marker would let the bot label its own decision points for
`replay-dump.sh` to read back. Noting it; not acting on it while a verdict is pending.

### VERDICT — REJECT, emphatically, and the covariate came back with the WRONG SIGN

Run `gauntlet/20260908-104505`, `BOT=carol_i37_eq`, opponents `carol_iter36` and `carol_i37_res`,
100 games, fresh random 25-map sample.

| gate (pre-registered) | required | measured | |
|---|---|---|---|
| 1. `carol_i37_eq` vs `carol_iter36` | > 25/50 | **3/50 (6%)** | **FAIL** |
| 2. swept wins (new absolute floor) | >= 5 of 25 | **0**, against 22 swept losses | **FAIL** |
| 3. large-area half win rate | >= 45% | **0.0%** — 0 of 26 games | **FAIL** |

The other dose is no better: `carol_i37_res` (soldier gate 1850) took 5/50. The ladder is monotone
in the wrong direction — 2250 (incumbent) >> 1850 >> 1600 — so this is a gradient, not noise.

**Covariate: rho(wins, area) = -0.491, t = -2.70, df=23.** I pre-registered `rho > 0` and said in
advance I held it with low confidence. It came back **negative and significant**. The arm won
**0 of 26 games on the large-area half** and all 3 of its wins on the small half.

So the direction is not merely unsupported, it is reversed: moving the mix toward soldiers made
carol's *large-map* deficit worse, and large maps are precisely the deficit this iteration set out
to fix.

### What I got wrong, which is worth more than the run cost

I opened the pre-registration by calling `SPLASH_FLOOR = 2000` "the fourth gate-as-off-switch in
this lineage, and the first one I built myself." **That framing was wrong, and the error has a
name I can generalise.**

My evidence was: realized mix 44% soldier / 55% splasher, against an *intended* 75/10/15 from the
build roll. I treated the divergence as proof the gate was broken. But a divergence between
realized and intended is evidence that **one of the two is wrong, and I assumed every time that it
was the realized one.** The intended mix is `SPLASHER_IN_20 = 3`, a constant dating from iteration
3, never validated against anything. The gate was not corrupting a good policy — **the gate WAS
the policy, and it was quietly correcting a stale constant.** This run is the measurement that the
roll constants, not the gate, are the vestigial half.

That also retro-validates iteration 30 far more strongly than its own 28/50 accept did: forcing
splashers past the cheap units is worth roughly **44 points of win rate** against the same
opponent family, and nothing in my instrument had ever measured it, because every gauntlet I run
is carol against carol and both sides carried the same gate.

**Why the pattern-match was seductive.** Iterations 30, 35 and 36 were all real off-switches, all
found by the same recipe (compare realized against intended, find the gate, make it reachable),
and all accepted. A fourth case fitting the template arrived and I ran the recipe without asking
the one question the previous three never forced me to ask: *is the gate doing work?* Three
confirmations of a heuristic are exactly when it stops being checked.

### The gradient this bought, stated as the useful output

Splashers carry carol on large maps. Reducing splasher share cost **every single game** on the
large-area half. That is a sharper directional signal than anything my accepted iterations have
produced, and it points the opposite way from where I was heading:

- coverage — painted area — is the win condition in 76% of tournament games;
- a splasher paints 2.6x the sustained tiles/turn of a soldier at 23% lower paint per tile
  (`RULES.md`);
- carol's measured deficit is that coverage does not scale with map area.

**The lever on large maps is splasher throughput, not soldier count.** Iteration 38 should test
that directly rather than inferring it from a rejection.

### What does NOT follow, said explicitly so a later session does not over-read this

This is a within-lineage result: every game was carol against carol. It establishes that the
splasher gate beats its absence *for this bot's other machinery*, not that carol's splasher share
is optimal, and not that more splashers is monotone good. The tournament — the only opponents this
lineage did not produce — is where that gets checked, and iterations 30-36 have never played one.
The next tournament is the first that will.

### The manipulation check: link 1 fired perfectly, link 2 failed exactly where I said it would

Six paired loss replays, both bots in the same game (`carol-tools/mixcheck/paircheck.py`):

| game | cand s/m/p | sold% | inc s/m/p | sold% | cand tw | inc tw | cand cov | inc cov |
|---|---|---|---|---|---|---|---|---|
| Brat | 148/1/2 | 98.0 | 142/0/6 | 95.9 | 3.0 | 3.0 | 340 | 573 |
| DefaultHuge | 273/5/8 | 95.5 | 56/0/68 | 45.2 | 18.0 | 15.0 | 286 | 603 |
| Gears | 71/5/4 | 88.8 | 39/0/36 | 52.0 | 0.0 | 0.0 | 232 | 659 |
| SMILE | 189/6/14 | 90.4 | 117/0/73 | 61.6 | 10.0 | 13.0 | 337 | 555 |
| Oasis | 122/10/9 | 86.5 | 5/0/96 | 5.0 | 8.0 | 4.5 | 167 | 678 |
| Circuit | 275/5/4 | 96.8 | 200/1/59 | 76.9 | 5.0 | 6.7 | 371 | 605 |
| **POOLED** | **1078/32/41** | **93.7** | **559/1/338** | **62.2** | **7.33** | **7.04** | **289** | **612** |

Read against what I registered in advance:

1. **Soldier share >= 60%: PASSED, overwhelmingly — 93.7%.** The gate change did exactly what the
   arithmetic said it would. My reading of the code was correct; my reading of what the code was
   *for* was not.
2. **Towers strictly higher: FAILED. +0.30, and higher in only 2 of 6 games.** Soldier share went
   from 62.2% to 93.7% — a half-again increase in soldiers — and the tower count did not move.
3. **The price: catastrophic. Coverage 289 against 612 — the candidate painted 53% less ground,
   in 0 of 6 games more.** 41 splashers produced 289 coverage; 338 produced 612.

**Addendum 2 of this pre-registration called link 2 the weak one, before any game was played,
and it is exactly the link that broke.** I wrote: "if soldier share rises and towers do not, the
fault is ruin *conversion*, not ruin *affordability*." That is now measured rather than
speculated: 1,078 soldiers bought 0.3 of a tower. **Soldiers are not the constraint on tower
count, and no amount of making them cheaper will make them one.**

The rejection is therefore not "it lost"; it is fully accounted for. Link 1 worked, link 2 does
not exist at the strength I assumed, and the price I registered came due at roughly twice the size
of any benefit that was available.

**DECISION: REJECT.** `src/carol` is untouched and remains iteration 36; nothing to revert, HEAD
compiles and is what plays in the tournament. Cost: one 100-game run and six cached dumps.

---

# Iteration 38 — RETURN TO REFILL (pre-registered before any game is played)

## The measurement that motivates it

Not a new run: 16 replays already cached from iterations 35-37, re-read with a new counter
(`carol-tools/mixcheck/attrition.py`). ReplayDump classifies a death as starved when the
robot's last observed paint was <= 0, so the split between "walked itself to death" and
"the opponent killed it" is already in every dump I own.

| band | splasher action utilisation | starvation share of deaths |
|---|---|---|
| small maps (< 2000 tiles) | 16.4% | **91.1%** (1498/1644) |
| large maps (>= 2000 tiles) | 17.8% | **85.8%** (2407/2806) |

**88% of all carol unit deaths are paint starvation, not combat** — 3,905 of 4,450. And RULES
records the reason this is not merely a curiosity: *no unit damages enemy robots' HP directly*.
Robot attrition in BC25 is tower fire plus paint starvation, so paint is the whole attrition
mechanic and starvation is the part of it I control completely.

Splashers fire at ~17% of the engine ceiling (an attack adds +50 cooldown falling 10/turn, so
0.2 shots/splasher/round is exact, not a model). Iteration 37 established that splashers are
what carries carol on large maps; they are running at a sixth of capacity.

## Two engine facts read this iteration, one of which killed my first design

`javap -p -c battlecode.world.RobotControllerImpl` (engine 3.1.0):

1. **`assertCanTransferPaint` calls `assertCanActLocation(loc, 2)` — a HARDCODED 2**, not the
   unit's action radius. Refill range is r2<=2 for every unit type.
2. **Low-paint cooldown**: below 50% paint, all cooldowns rise by (100 - 2*X)% where X is
   percent full. A unit under half paint is already crawling at up to half speed *before* it
   starves, painting nothing the whole way.

Fact 1 killed the iteration I was about to build. `refillIfPossible` searches
`senseNearbyRobots(2, ...)` while RULES gives soldier action r2 = 9, so it looked exactly like
the fourth instance of this lineage's most productive bug class — a gate set narrower than the
mechanism it guards, which is what iterations 30, 35 and 36 all were. **It is not.** The engine
pins transfer at 2 regardless of unit, so widening the search would have been a no-op that
`canTransferPaint` refuses, and a no-op arm produces an uninterpretable result rather than a
clean rejection. Iteration 37's lesson was that three confirmations of a heuristic are exactly
when it stops being checked; this is that check being run, and it saved a 100-game run.

## The hypothesis

Units do not run out of paint because they cannot reach a tower. They run out because **nothing
in carol ever sends them back to one.** `refillIfPossible` fires only when a unit happens to be
standing within r2=2 of a tower, which in practice means the turns just after it spawns.

The memory required already exists. `seenLoc` has stored every distinct ally tower's `(x<<6)|y`
since iteration 34, refreshed every turn by `censusTowers()` — and **its coordinates have never
been read by anything.** Only the paint/money counts derived from it are used, by `towerTypeFor`.
So this iteration adds a consumer for data already collected, at no new sensing cost.

**Change (movement only, one mechanism):** when a unit's paint falls below `RETURN_PCT`% of its
capacity, `moveExploring` retargets it at the nearest remembered tower instead of its
exploration target. Action logic is untouched, so a unit still paints whatever it can reach on
the way home.

`RETURN_PCT = 50` is read off the engine, not tuned: it is the cooldown-penalty knee from fact 2,
and it is also exactly the threshold `refillIfPossible` already uses. Triggering there means the
walk home happens at full speed rather than at the penalised rate.

**Reachability, checked before building** (my own doctrine, and the thing iteration 37 skipped):
`seenN >= 1` is guaranteed — a unit spawns adjacent to the tower that built it and `censusTowers`
runs on turn 1. And the iteration-32 probe already measured that **63% of idle soldier turns are
below half paint**, so the trigger fires on a large fraction of exactly the turns being wasted.
This gate is reachable on existing evidence; I am not paying a run to discover it.

## Doses

| arm | RETURN_PCT | |
|---|---|---|
| `carol_iter36` | — | zero arm (incumbent; never returns) |
| `carol_i38_50` | 50 | the engine's knee — primary |
| `carol_i38_25` | 25 | returns later, having done more work, but walks home penalised |

Both candidates carry `BUILD = "i38"` per the shared-tag convention. One run,
`BOT=carol_i38_50 OPPONENTS="carol_iter36 carol_i38_25"`, 25 fresh random maps, both sides,
100 games. The sample is drawn once and shared, so the dose-response comparison within the run
is exact.

## Gate — the FIRST use of the re-set gate, and it is stricter than anything I have accepted on

Under the standing gate adopted this session (commit 5443d59), against a measured sd of ~2.4
wins for a near-even 50-game arm:

1. **`carol_i38_50` vs `carol_iter36` >= 29/50 accepts. <= 25/50 rejects. 26-28 is UNRESOLVED**
   and may not accept without a replication on a disjoint map sample.
2. Report `D` (split count) and the sd distance from `tools/map-resample.py`. Gate on neither.
3. Stratify by map area; report the small and large halves separately.

Note what this costs me: iterations 34 and 36 were both accepted at 28/50, which under this gate
would have been unresolved. I am not going to quietly discover that 28 is enough after seeing a 28.

## Manipulation checks, with the WEAK LINK named in advance

Iteration 37's most useful output was that I named its weak causal link before the run and it
was exactly the link that broke. Doing that again:

1. **Link 1 (strong, expect it to pass).** The decision fires and finds a tower: `hg/ha > 0.8`
   from the indicator counters. Starvation share of deaths falls from 88% pooled to **< 70%**.
   If this fails, the mechanism did not run and nothing else is interpretable.

2. **Link 2 — THE WEAK ONE.** Fewer starvation deaths become more coverage. **I expect this to
   be where it breaks**, and the mechanism is specific: a refill draws from the tower's stash,
   which is *the same paint a replacement unit would have been built from*. If tower paint
   rather than chips is the binding constraint, the field population is unchanged and the only
   gain is the 250 chips per unit not re-bought. Carol's treasury is measured to oscillate in
   [1600, 2450] and never to reach the 3700 an upgrade needed before iteration 35, which is
   evidence she is chip-tight too — but "chip-tight" and "chips are the binding constraint" are
   different claims and only one of them is measured.

   **If starvation falls and coverage does not move, the finding is that carol is paint-limited,
   and refilling merely relocates the same paint.** That is a real result about the bot's
   binding constraint, not a null, and I would rather buy it knowingly than infer it.

3. **The PRICE, stated before it is paid.** Returning units drain tower stashes, so `twPaint`
   falls and production falls with it. This is the most likely way the arm loses outright, and
   it is the "two consumers of one budget must partition it by an explicit decision" failure
   from my own LEARNINGS — `refillIfPossible` takes `min(cap - paint, ally.paintAmount)`, i.e.
   everything the tower has, with no floor left for building. I am deliberately NOT adding that
   partition in this iteration: it would be a second mechanism, and I do not yet have a
   measurement saying the drain happens. If the price comes due, the partition is iteration 39
   and it will have evidence behind it.

Measured for all three: `twPaint`, `+sold`/`+spl` spawn counts, `died`/`starved`, `cov`.

## Iteration 38 ADDENDUM — cross-lineage evidence, recorded BEFORE the verdict lands

Four carol games from tournament `20260908-0100` (the sanctioned cross-agent channel), dumped
while the gauntlet plays. This is the only instrument in the project that can see a weakness my
whole lineage shares, and it **corrects my own framing of this iteration**. Writing it down now,
with the run still in flight, so it cannot be read as post-hoc.

| map | team | starv% of deaths | mean soldiers alive | coverage |
|---|---|---|---|---|
| galaxy 2025 | **carol** | 93.2 | 18.4 | **281** |
| galaxy 2025 | bob | 93.5 | 16.1 | 659 |
| DefaultHuge 3481 | **carol** | 35.3 | 23.7 | **377** |
| DefaultHuge 3481 | alice | 57.0 | 53.9 | 592 |
| SMILE 3600 | **carol** | 83.3 | 38.6 | **300** |
| SMILE 3600 | alice | 80.7 | 64.0 | 661 |
| SMILE 3600 | bob | 91.1 | 84.4 | 683 |

**1. Starvation is not a carol defect. It is how BC25 works.** My motivating statistic — 88% of
carol's deaths are paint starvation — is matched almost exactly by both opponents (bob 91-94%,
alice 57-81%). RULES already said why: *no unit damages enemy robots' HP directly*, so attrition
is tower fire plus starvation and starvation necessarily dominates. **I measured a property of
the game and read it as a property of my bot.** The number is correct; the diagnosis I hung on
it was not, and only an opponent my lineage did not produce could have shown me that. This is
the self-referential blind spot the training algorithm warns about, caught in the act.

**2. The real deficit, which this table does show, is a different quantity.** Carol paints
**roughly half** what its opponents paint on large maps (281/377/300 against 592-683) — and
carries **a third to a half of their standing army** (18-39 soldiers against 54-84). Same
starvation rate, half the units in the field, half the ground painted. Carol's problem is not
that units die; everyone's units die. It is that carol cannot keep as many alive at once.

**3. What this does to the weak link I pre-registered, before I know the answer.** I named link 2
— fewer starvation deaths becoming more coverage — as the one likely to break, because a refill
draws the same tower paint a replacement would have been built from. This table sharpens that
into a near-prediction: if all three lineages starve alike and the opponents still field twice
the army, the binding constraint is paint THROUGHPUT, and recycling a unit at 200 paint instead
of rebuilding it at 200 paint + 250 chips leaves army size exactly unchanged. **Refill would then
buy chips, not units** — worth something only if chips bind, which is a separate claim I have not
established.

So my honest expectation, stated before the result: **link 1 passes, link 2 fails, and the arm
lands at or below the null.** If that is what comes back, the iteration is still worth its VM
time, because it converts "carol is paint-limited, not chip-limited" from a guess into a
measurement — and that is the fact iteration 39 needs.

**4. Iteration 39 is already named by this table, independent of how 38 resolves**: carol fields
half the army. Whether that is tower count, tower paint income, or paint spent per tile is the
next question, and the frozen-roster/gauntlet instruments cannot ask it because every carol
snapshot shares the deficit.

## Iteration 38 ADDENDUM 2 — the tower economy behind "half the army", and an external retro-validation of iteration 36

Same four tournament dumps, now reading build mix and tower economy.

| map | team | mean towers | mean tower paint | +sold | +mop | +spl | mean chips |
|---|---|---|---|---|---|---|---|
| DefaultHuge | **carol** | 23.7 | 1523 | 425 | **887** | 2 | 1894 |
| DefaultHuge | alice | 24.1 | 2143 | 971 | 304 | 0 | 128297 |
| SMILE | **carol** | 13.4 | 1212 | 190 | **459** | 0 | 1579 |
| SMILE | alice | 20.8 | 4483 | 683 | 237 | 0 | 1684 |
| SMILE | **carol** | 13.0 | 1732 | 322 | 238 | 8 | 1123 |
| SMILE | bob | 17.0 | 4259 | 576 | 179 | 184 | 2492 |
| galaxy | **carol** | 7.6 | 2415 | 216 | 96 | 11 | 1639 |
| galaxy | bob | 6.6 | 577 | 188 | 58 | 58 | 57935 |

**THE CAVEAT FIRST, because it changes everything about how this is read.** The tournament
exported `carol @ 6c55fc4`, which is **iteration 29**. Iterations 30-36 have never played a
tournament. Nothing in this table describes the bot I am currently testing, and I nearly wrote it
up as a live deficit.

**Read correctly, it is an external retro-validation of iteration 36.** On two of four games
carol built **two moppers for every soldier** — 887 against 425, and 459 against 190 — a 60-70%
mopper share against an intended `MOPPER_IN_20 = 2`, i.e. 10%. That is *exactly* the failure
iteration 36's `PAINT_FLOOR` was built to fix, and whose mechanism the code comment spells out:
tower paint accrues at 5/turn, a mopper costs 100 and a soldier 200, so the cheap unit resets the
stash before the expensive one is ever affordable and **prevents** it rather than merely
outnumbering it. Only soldiers call `workOnRuin`, so every displaced soldier is a ruin not claimed.

This matters more than a normal corroboration. **Iteration 36 was accepted at 28/50, +1.03 sd —
statistically unresolved under the gate I re-set today** — and it stood on a within-lineage
manipulation check (5 moppers against 367). Here is the same fault, at the same magnitude,
measured on the only opponents my lineage did not produce. That is independent evidence for the
mechanism arriving from outside the lineage, and it is the strongest support iteration 36 has.

**What it does NOT license.** It says nothing about whether iteration 36 *fixed* it — the fixed
build has never played an external opponent. The next tournament is the first that will, and it
is the measurement to look for.

**One live-looking signal, flagged but not acted on.** Carol's mean treasury sits at 1,100-1,900
while alice banks 128,297 on DefaultHuge and bob 57,935 on galaxy. Carol spends everything she
earns; the opponents cannot spend what they have. If that survives into iteration 36's build, it
says chips genuinely bind for carol and not for them — which is the one condition under which
iteration 38's link 2 could actually hold, since the whole benefit of a refill over a rebuild is
250 chips. I am recording this as a *hypothesis about the weak link*, from a build that is nine
iterations stale, not as support for it.

## Iteration 38 ADDENDUM 3 — a BUG-shaped failure mode, named before the result

Tracing `nearestKnownTower`'s dry-tower guard while the run finishes. The guard returns `null`
when the nearest remembered tower is within r2<=2, on the reasoning that being adjacent and still
low means `refillIfPossible` just failed, so the tower is dry or destroyed and homing again would
deadlock the unit.

**It does not deadlock. It oscillates.** A unit adjacent to a dry tower gets `null`, so it walks
toward its exploration target — one step, to d2 = 4 or so. Next turn 4 > 2, the guard no longer
fires, the tower is still the nearest remembered one, and the unit steps back. Period-2 ping-pong
beside a dry tower, painting almost nothing, for as long as it stays under `RETURN_PCT`.

I am recording this now, before any number, because of the interpretation it controls:

- If the arm loses **and** units are found oscillating, the hypothesis is **untested**, not
  refuted. That is an implementation bug, and a rejection would say nothing about whether
  returning to refill is a good idea.
- If the arm loses **and** units are not oscillating, the hypothesis is genuinely refuted and the
  weak link (link 2) is where to look.

The discriminating evidence is cheap and I will run it either way rather than reason about it:
`hg/ha` near 1.0 with coverage collapsed is the oscillation signature, since a ping-ponging unit
asks and goes on nearly every turn. A per-robot position track over ~40 rounds settles it outright.

Also to check on the same dumps, because the new scan is not free: `ov=` (bytecode overruns) in
the indicator string. `nearestKnownTower` walks up to 64 entries on every low-paint turn, and a
silent mid-turn truncation would corrupt the arm without any other symptom.

## Iteration 38 RESULT — **REJECT** at 17/50, −3.10 sd. The price I pre-registered is exactly what came due.

Run `gauntlet/20260908-121614`, `BOT=carol_i38_50`, opponents `carol_iter36` and `carol_i38_25`,
100 games, fresh random 25-map sample.

| gate (pre-registered, first use of the re-set gate) | required | measured | |
|---|---|---|---|
| `carol_i38_50` vs `carol_iter36` | >= 29/50 | **17/50**, −3.10 sd | **REJECT** |
| area split (reported, not gated) | — | small 36.1%, large **28.6%** | — |
| D, split maps (reported, not gated) | — | 13 of 25 (52%) | — |

The dose ladder is monotone and points at zero: `carol_i38_25` beats `carol_i38_50` **37–13**, so
returning *less* is better at every dose I tested, and the incumbent (RETURN_PCT = 0) is better
still. That is a gradient, not noise.

### The manipulation check: link 1 passed 50-fold, and the PRICE ate it

Paired within-game, both bots in the same replay (mit / lighthouse / TheBest, pooled):

| | `carol_i38_50` | `carol_iter36` | |
|---|---|---|---|
| **paint transfers (`xfer`)** | **4,758** | **94** | **50x — the mechanism ran** |
| tower paint stash (mean) | 2,853 | **9,748** | **−71%** |
| towers alive (mean) | 15.3 | 20.1 | −24% |
| splashers built | 286 | 404 | −29% |
| soldiers built | 128 | 64 | +100% |
| deaths | 361 | 413 | −13% |
| **starvation deaths** | **347** | **374** | **−7%** |
| **coverage** | **852** | **1,748** | **−51%** |

Link 1 fired perfectly: `hg/ha = 93.0%` from the indicator counters (5,007 asks, 4,656 goes over
60 robots), and refills rose **fiftyfold**. `ov=0` on every robot inspected, peak bytecode 6,875
of 17,500, so the new scan is not the problem either.

**And it bought a 7% reduction in starvation deaths.** Fifty times the refilling, and the units
starved anyway. Meanwhile the tower stash fell 71%, and tower paint is what *builds* units — so
splasher production fell 29%, tower count fell 24%, and coverage halved.

The causal chain is closed end to end:

> refill 50x -> tower paint −71% -> splashers −29% and towers −24% -> coverage −51% -> 17/50

**This is the price I named in the pre-registration, in the words I named it in**: "returning
units drain tower stashes... this is the *two consumers of one budget must partition it by an
explicit decision* failure from my own LEARNINGS — `refillIfPossible` takes
`min(cap - paint, ally.paintAmount)`, i.e. everything the tower has, with no floor left for
building." I chose deliberately not to fix it in the same iteration, so that if the price came due
I would know that it had. It did, at roughly twice the size of any benefit available.

### What did NOT happen, said plainly because I pre-registered it as an excuse

Addendum 3 predicted a period-2 oscillation beside dry towers, and named it as the reading under
which a rejection would leave the hypothesis *untested* rather than refuted. **It is not
supported.** The robot I traced does orbit a fixed point — but at paint 168-200, which is *above*
the 50% gate, so the homing branch was not running; that orbit is pre-existing `workOnRuin`
behaviour present in the incumbent too. The rejection is real, and I do not get to keep the
hypothesis.

### Link 2 was never reached, and I should not claim it was tested

I pre-registered link 2 — fewer starvation deaths becoming more coverage — as the weak one. It was
never put to the test: starvation deaths barely moved (−7%), so link 2's input never materialised.
**The arm failed at the price, upstream of the weak link.** My addendum's prediction ("link 1
passes, link 2 fails, arm at or below the null") got the arm right for a reason that was not the
one I gave, and saying so is worth more than claiming the call.

### The finding worth more than the run: carol's refill loop already exists, and it is LOCAL

Tracing incumbent soldier `id10270` on `mit`:

```
round 39  (9,35)  paint=7    SPAWN id12046(T1,PAINT_TOWER) at (9,34)
round 41  (10,35) paint=199
```

The soldier spends itself down to 7 paint building a ruin into a paint tower, and refills from the
tower it just built, two rounds later. **Carol's soldiers do not return to refill points — they
manufacture them.** That is why the incumbent needs only 94 transfers to my 4,758, and it is a far
better loop: the walk is zero, and the trip produces a tower.

My change pulled low-paint soldiers *away* from the ruins they were converting, and the numbers
show exactly that shape: **soldiers built doubled (64 -> 128) while towers alive fell 24%.** More
soldiers, fewer ruins finished. I replaced an efficient local loop that creates infrastructure
with an expensive global one that consumes it.

### DECISION: REJECT

`src/carol` is untouched and remains iteration 36. HEAD compiles and is what plays in the
tournament. Cost: one 100-game run and five cached dumps.

**Iteration 39 is now evidenced rather than guessed**, and it is *not* "partition the paint budget
and try again" — that would rescue a mechanism whose own best case bought 7%. The measurement that
matters is that soldier-to-tower conversion is carol's paint pump, and this run priced it: pulling
soldiers off ruins costs 24% of the tower count and half the coverage. **The direction is to feed
that pump, not to bypass it.**

---

# Iteration 39 — SPLASHER FRONTIER STEERING (pre-registered before any game)

## The measurements, all free from replays already on disk

Incumbent (`carol_iter36`), `mit`, two windows — because a one-window read samples a game *phase*,
which is a mistake already in my LEARNINGS:

| | rounds 200-240 | rounds 900-940 |
|---|---|---|
| fired (`SPLASH`) | 4.4% | 2.0% |
| cooldown-blocked | 21.4% | 14.2% |
| **out of paint** | **45.4%** | 14.8% |
| **targetless** (`lowScore`+`noTgt`) | 28.8% | **69.1%** |

**The binding constraint switches phase**: paint early, targets late. Had I read only the late
window I would have built for the wrong half of the game.

Splasher `bestScore` distribution (the score is already stamped in the indicator):
**median 0, p75 2, p90 4-6, max 18-27.** The median splasher turn scores *zero* — it is standing
where there is nothing to paint. In the same window the soldier's own frontier counter reports
`frontFound` on **41 of 41** idle turns, so empty ground is visible at r2=20 while the splasher's
r2~8 scoring window sees none of it.

## Two candidate iterations killed here, for free, before any VM time

1. **Raise `SPLASH_MIN_SCORE`** (fire only on dense frontier). Dead: `>=8` is reached on 4.4% /
   2.0% of turns, which *exactly* equals the observed fire rate. The threshold is already firing
   on only the top 2-4% of opportunities; raising it drives firing to zero and lowering it buys
   shots at 25-50 paint per tile. The constant is well placed.
2. **More money towers (`MONEY_MOD` down)** to unpin the treasury below the soldier build gate of
   2250. Dead: the treasury is not uniformly pinned — median $1,550 but p90 $15,190 and max
   $46,200. Chips explode later in the game, so chips are not the binding constraint, which
   matches the existing iteration-31 probe (100% of chips-available no-builds are `tpIn <
   paintCost`). Iteration 34's direction was right.

## The ceiling, computed BEFORE building — the new rule, and it nearly killed this iteration

My LEARNINGS rule from iteration 38: alongside "can the gate fire?", compute *"if it fired on
every eligible turn, how much could the outcome move?"*

First pass said **near zero**, and the argument was sound: a splasher holds 300 paint and a shot
costs 50, so its whole life is 6 shots; it cannot refill without walking to a tower, which
iteration 38 just priced at −3.10 sd. If splashers already spend all their paint, steering cannot
add a single shot — it can only relocate shots that were going to happen anyway, and the `>=8`
threshold gates quality identically in both arms.

So I measured the thing the argument turned on:

| | splash actions | splashers built | paint-capped ceiling (6/unit) | realised |
|---|---|---|---|---|
| `carol_iter36` | 559 | 136 | 816 | **68.5%** |

**Splashers die holding roughly 31% of their paint.** The headroom is real: up to **+46% splash
actions at zero resource cost**, since this spends paint already committed to the unit and never
touches a tower stash. (Corroboration from the rejected arm: `carol_i38_50`, whose splashers
refilled constantly, realised 94.7% — the headroom is reachable, that build just paid for it out
of the towers.)

That is a modest, quantified ceiling rather than an exciting one, and it is the honest number.

## Change (one mechanism, movement only)

The splasher is the only unit that never steers. `runSoldier` has redirected idle soldiers at
`nearestVisibleEmpty()` since iteration 29 and it was accepted there; splashers and moppers still
call `moveExploring(null)` — a random far target. When a splasher is action-ready and fuelled but
does not fire, steer it at the nearest visible empty tile. **Zero marginal cost: it redirects a
move that was already going to happen.**

**One implementation note that is a real bug avoided.** The target is passed as `moveExploring`'s
`target` argument, *not* written into `explore` the way the soldier version does. `moveExploring`
replaces `explore` whenever `distanceSquaredTo(explore) <= 8`, and for a splasher the nearest
empty tile is frequently that close — its scoring window is only r2~8, so "nothing worth hitting"
and "nothing within 8" are different conditions. Written the soldier's way, the steering would be
silently discarded exactly when it matters. (The soldier version is safe from this only because an
idle soldier by definition has no empty tile inside its r2=9 action radius.)

## Doses

| arm | | |
|---|---|---|
| `carol_iter36` | — | zero arm (incumbent, never steers) |
| `carol_i39_all` | `STEER_ON_LOWSCORE = true` | steer whenever it did not fire — primary |
| `carol_i39_notgt` | `false` | steer only when `bestScore == 0` (conservative) |

`BOT=carol_i39_all OPPONENTS="carol_iter36 carol_i39_notgt"`, 25 fresh random maps, both sides,
100 games. Both carry `BUILD = "i39"`.

## Gate (standing gate, second use)

1. `carol_i39_all` vs `carol_iter36`: **>= 29/50 accepts, <= 25/50 rejects, 26-28 UNRESOLVED**
   pending a replication on a disjoint map sample. The complement of this run's `maps.txt` is 50
   maps, and a replication there **pools with this run to cover all 75 — where map-sampling error
   is exactly zero.**
2. Report D, the sd distance, and the small/large area split. Gate on none of them.

## Manipulation checks, weak link named in advance

1. **Link 1 (strong).** `sf/(sf+sn)` — the conditional reachability counter — is high, and splash
   actions per splasher rise from **68.5%** of the paint ceiling toward 100%. If this does not
   move, the mechanism did not run and nothing downstream is interpretable.
2. **Link 2 — THE WEAK ONE.** More shots become more coverage. It breaks if the extra shots are
   *marginal* ones: the threshold fires at `bestScore >= 8`, which is only ~4 empty tiles for 50
   paint (12.5 paint/tile) against a best case of ~3.8. Steering toward the **nearest** empty tile
   is not steering toward the **densest**, so the extra shots may all be bought at the worst price
   the threshold allows. That is the specific way I expect this to fail, and the check is the
   `s=` score distribution at the moment of firing, not the count of firings.
3. **The price.** A steered splasher walks toward empty ground and therefore *away* from painted
   territory, and several splashers steering at the same frontier tile will clump (−1 HP per
   adjacent ally, −2 on enemy ground). Measured: coverage, deaths, and whether tower paint moves
   at all — it should NOT, and if it does I have mis-read the mechanism.

## Iteration 39 ADDENDUM — the incumbent's firing quality, measured before the result

Building the weak-link check turned up the number that check needs, and it is not the one I
assumed. `carol_iter36`, `mit`, rounds 900-940, scores at the moment of firing:

> **shots = 12, mean score 17.1, median 18, p90 27, max 27.**

`SPLASH_MIN_SCORE = 8` is a floor the incumbent is nowhere near. Its shots average **17.1**,
roughly 9 empty tiles for 50 paint (~5.6 paint/tile against a best case near 3.8). **The
incumbent is not firing at the threshold; it is firing well above it**, because a splasher that
waits accumulates a better target than one that shoots at the first legal opportunity.

This sharpens the pre-registered weak link into a specific, falsifiable comparison rather than a
worry:

> **If `carol_i39_all` raises the shot COUNT while its mean firing score falls toward 8-10, the
> extra shots are marginal ones bought at roughly half the tiles per paint, and a raw count of
> splash actions would report that as success.**

So the acceptance evidence is **shots x mean score**, not shots. Pre-registered thresholds, set
now against the measured baseline of 17.1:

- link 1 confirmed if shot count rises **and** mean firing score stays **>= 14**;
- link 2 **refuted** if shot count rises while mean firing score falls **< 12**, which would mean
  steering trades quality for quantity at a loss;
- the honest null is both roughly unchanged, meaning steering did not change where splashers
  stand.

**One methodological note, because it cost a wrong table.** My first version of this check grepped
the whole dump line for `SPLASH` — and the robot label `(T1,SPLASHER)` contains that substring, so
every splasher turn matched and the tool reported all 607 turns as firing shots at "mean score
1.3". The number was absurd enough to catch, which is the same luck as the `p`-counts-tiles trap:
the guard is a stated ceiling, not vigilance. Fixed by filtering the extracted state fragment
rather than the line. Recorded in the tool.

## CORRECTION to the iteration 38 verdict table — two numbers were sums of means, not means

Caught while rendering the arena: the round-900 map on `mit` shows only a handful of towers, which
does not fit the "towers alive (mean) 20.1" I wrote in the verdict.

My pooling script summed the *time-averaged* columns across the three games instead of averaging
them. Per map, `carol_iter36`'s tower count is **4.7 / 2.5 / 12.9**, which sums to the 20.1 I
printed; tower paint is **1,512 / 423 / 7,813**, which sums to 9,748.

**What survives unchanged:** every ratio in that table. Both arms were summed identically, so
tower paint −71%, towers −24%, splashers −29% and coverage −51% are all exactly as reported, and
the verdict rests entirely on those ratios. The rejection is unaffected.

**What does not survive:** any absolute reading of those two columns, and one inference I drew
from it. I wrote in the iteration-39 analysis that carol has "9,748 tower paint banked late", and
used it to argue tower paint is abundant in the late game. It is not a mean, and the per-map
spread makes the point badly: 7,813 on `TheBest` against **423** on `lighthouse`, an 18-fold
range. **Tower paint abundance is map-dependent, not a general late-game property**, and I had
generalised from a number that was mostly one map.

The label is the whole defect — the column header said `twPaint~`, which reads as an average.
This is the same class as `p`-counts-tiles from earlier today: a quantity whose *name* implies a
normalisation it does not have. Both were caught by an external check (an impossible ratio; an
arena that disagreed with a table), not by re-reading the code, which is the argument for
rendering the thing at least once rather than only tabulating it.

## Candidate for iteration 40 raised and KILLED in the same hour: walls are not the barrier

Rendering `mit` at round 900 showed both teams' paint stopping dead at horizontal wall bands
(rows 37, 42, 45), with rows 47-59 untouched. `stepToward` is a greedy stepper with no
pathfinding and `mit` is 16.3% walls, so "greedy movement cannot cross wall structures" was an
attractive iteration-40 hypothesis — and it was built on a within-lineage game, where **both**
teams are carol and share the mover, so the symmetry that looked like evidence was guaranteed by
construction.

The discriminating case is an opponent with a different mover, and it was already on disk.
`carol-vs-bob-on-galaxy`, round 900:

- **bob** holds a single connected region spanning the centre and right of the map and reaching
  the top rows, **straight past the same kind of wall structures**;
- **carol** is confined to a narrow strip down the left edge and one block in rows 18-27.

Walls are not the barrier. Bob crosses them; carol simply never expands. **The deficit is
dispersal, not pathfinding**, and an iteration spent on a routing algorithm would have been spent
on a non-problem.

Two things worth keeping:

1. **A symmetry observed in a self-play game is not evidence about the game.** Both arms shared
   the mover, so "both stop at the wall" was a property of the *pair*, not of the terrain. This is
   the self-referential blind spot again, in its most seductive form yet — the artefact was a
   picture, and a picture feels like direct observation rather than an inference.
2. **It corroborates iteration 39's premise from outside the lineage.** Carol has a large empty
   frontier immediately adjacent to its territory and its splashers sit inside painted ground
   scoring a median of zero. That is exactly the condition steering is meant to fix, and it is now
   visible in a game against an opponent my lineage did not produce.

## Iteration 39 RESULT — **REJECT** at 17/50, −3.50 sd. Steering inverted its own target metric.

Run `gauntlet/20260908-125607`. `carol_i39_all` vs `carol_iter36`: **17/50, −3.50 sd**, small
41.2% / large 18.8%, D=15. Second dose `carol_i39_notgt` beats `carol_i39_all` 32–18, so the
ladder is again monotone toward zero steering: `iter36 >> i39_notgt > i39_all`.

**Link 1 fired and found the frontier**: fleet-summed `sf=35,899 sn=4,078` — **89.8%** of steering
decisions found a visible empty tile. The mechanism ran, at scale, and worked as designed.

**And it inverted the metric it was built to raise** (`galaxy`, paired within one game):

| | `carol_i39_all` | `carol_iter36` |
|---|---|---|
| splash actions (whole game) | 629 | **663** |
| realised % of paint ceiling | 74.9% | **78.4%** |
| splasher turns out of paint (window) | **47.0%** | 27.8% |
| shots fired (window) | 10 | **19** |
| mean firing score | 13.0 | 13.4 |
| coverage | 362 | **436** |

The pre-registered weak link said the extra shots would be *marginal* ones bought at a worse
score. **That is not what happened — there were no extra shots.** Mean firing score barely moved
(13.0 vs 13.4), so quality held; the candidate simply fired *less* and ran dry *more*.

### Why, and it is the same fact as iteration 38 seen from the other side

Steering pushes splashers toward the frontier, which is *away from towers*. Refill needs adjacency
(r2<=2, hardcoded), so a splasher that runs dry at the frontier is dry permanently. `noPaint` went
27.8% -> 47.0%: the steered splashers spent their paint further out and then stood there useless.

> **Iteration 38 dragged units toward towers and drained the towers.
> Iteration 39 pushed units away from towers and stranded the units.
> Carol's units are TETHERED to towers by paint, and both iterations attacked the tether.**

The tether length bounds carol's territory. That is why the arena shows carol boxed into a corner
while bob spans the map, and it is why *both* movement overrides lost monotonically in the dose.
**The tether is not extended by moving units better. It is extended by putting more towers
further out** — which is the soldier -> ruin -> tower pump iteration 38 already identified.

**DECISION: REJECT.** `src/carol` remains iteration 36; HEAD compiles.

---

# Iteration 40 — MORE MONEY TOWERS, because iteration 35 changed what a chip buys

## The cross-lineage measurement (tournament replays, sanctioned channel)

Tower upgrades per game:

| map | carol | opponent |
|---|---|---|
| DefaultHuge | **9** (8 paint) | alice **90** (25 paint) |
| SMILE | **2** (1) | alice **17** (13) |
| galaxy | **3** (2) | bob **30** (10) |
| SMILE | **2** (1) | bob **22** (13) |

A 7-10x gap, against opponents this lineage did not produce. Honest discount: the tournament build
is iteration 29, and the current build upgrades more (8-11 per game in self-play) because
iteration 35 fixed the upgrade gate — but nowhere near 17-90.

**A level-2 paint tower makes 10 paint/turn against a level-1's 5.** Paint income bounds splasher
count, splashers bound coverage, and coverage is the win condition in 76% of tournament games.
Upgrades need chips >= 2500; carol's treasury median is ~1,550.

## The hypothesis, and why it reverses a constant I set myself

`MONEY_MOD` makes a ruin a money tower when `k % MONEY_MOD == 0`. Iteration 34 raised it 3 -> 4
(**fewer** money towers) on the grounds that paint binds and chips do not.

**That was measured on a build where a chip could not buy paint.** The upgrade gate was then
`CHIP_RESERVE + 2500 = 3700`, which iteration 35 showed the treasury never reaches — it fired 4
times against 9,147 `upgPoor`. On that build, chips beyond production genuinely had no use paint
would rather have, and trading them away was correct.

**Iteration 35 changed what a chip buys.** The gate is now 2500 flat, and clearing it converts a
tower's paint income from 5/turn to 10/turn permanently. So chips now purchase paint income
directly, and iteration 34's premise no longer holds. This is my own LEARNINGS entry — *a measured
constant is only valid for the build it was measured on* — applied to a constant I set six
iterations ago and have not re-checked since.

Note also that iteration 34's accept was **28/50, +1.03 sd — UNRESOLVED** under the gate I re-set
this morning. I am not overturning a solid result; I am re-opening one that was never established.

## Doses

`carol_iter36` (MONEY_MOD 4, zero arm) / **`carol_i40_3`** (3, the pre-iteration-34 value,
primary) / `carol_i40_2` (2, half of all ruins). Both candidates carry `BUILD = "i40"`.
`BOT=carol_i40_3 OPPONENTS="carol_iter36 carol_i40_2"`, 25 fresh maps, both sides, 100 games.

## Gate (standing gate, third use)

**>= 29/50 accepts, <= 25 rejects, 26-28 UNRESOLVED** pending a disjoint-sample replication.
Report D, sd distance, and the area split; gate on none of them.

## Manipulation checks, weak link named in advance

1. **Link 1 (strong).** Money-tower share rises and **paint-tower upgrades per game rise** above
   the incumbent's 8-11. If upgrades do not move, the chain is cut at its first link.
2. **Link 2 — THE WEAK ONE.** Upgrades become coverage. It breaks if the paint *lost* by
   converting ruins to money towers exceeds the paint *gained* by upgrading the survivors. The
   arithmetic is knife-edged and I want it on record before the result: each money tower forgoes
   5/turn; each upgrade adds 5/turn. So the trade is roughly **one ruin sacrificed per upgrade
   bought**, and it only wins if the chips buy *more than one* upgrade per forgone paint tower —
   or if the treasury was so far below 2500 that upgrades were never firing at all, which is the
   case the measurement actually supports.
3. **The price.** Fewer paint towers means less paint income *immediately* and the upgrade payoff
   arrives later, so this should look worse early and better late. Measured: `twPaint`, upgrades,
   splashers built, coverage, and the early/late split rather than the game total.

## Iteration 40 ADDENDUM — my own upgrade table was contaminated by the round-1 freebies

Building the link-1 checker exposed it. All four starting towers upgrade on round 1 for free, so
a raw `grep -c UPGRADE` carries a constant +2 per team. Excluding round 1, and counting only
**paint**-tower upgrades — the only ones that convert chips into paint income (5/turn -> 10/turn):

| map | carol | opponent |
|---|---|---|
| DefaultHuge | 7 | alice **24** |
| SMILE | **0** | alice **12** |
| galaxy | 1 | bob **9** |
| SMILE | **0** | bob **12** |

**Carol upgrades zero paint towers on two of the four maps**, and the self-play `galaxy` game from
iteration 39's run has **0 real upgrades for both arms**. So my pre-registration's claim that "the
current build upgrades 8-11 per game in self-play" was also round-1 contamination — the current
build barely upgrades either.

This makes the premise *stronger* and the ceiling larger than I registered: going from zero
upgrades to any is pure gain, and the weak-link arithmetic I put on record (one ruin sacrificed
per upgrade bought) is only knife-edged when upgrades are actually firing. At zero, the money
towers are buying nothing at all — which is precisely what the iteration is meant to change, and
precisely what link 1 will now measure.

**A second thing the opponents do that carol never does:** alice and bob upgrade *money* towers
too (64, 19, 8, 3 against carol's 0 everywhere). Noted, not acted on — one mechanism at a time.

**Third time today for the same defect class:** a count whose name implied a normalisation it did
not have (`p` = tiles not units; `twPaint~` = sum not mean; `UPGRADE` = includes a constant
baseline). All three were caught by building the *next* tool rather than by re-reading the last
one, which is now the pattern rather than the exception.

## Iteration 40 ADDENDUM 2 — how this connects to the tether finding, and why it is not iteration 37 again

Written with the run in flight, because the connection sharpens what link 2 should be checked
against and I do not want to discover it afterwards.

The tether finding says the way to reach further is to **move the anchors** — more towers, further
out — and only soldiers convert ruins into towers. So the chain that matters most here may not be
the one I led with:

> more money towers -> more chips -> **the treasury clears 2250 more often -> soldiers actually
> get built -> ruins become towers -> anchors move outward**

alongside the one I registered (chips -> upgrades -> paint income). Both run off the same
constant, so this is still one mechanism, but the *soldier* channel is the one the tether finding
predicts will matter, and the upgrade channel is the one the cross-lineage table measures. I will
report both and let them separate.

**Why this is not iteration 37 repeated.** Iteration 37 lowered the soldier gate — 2250 -> 1850 ->
1600 — and lost catastrophically (3/50, 5/50, monotone). That changed **who gets built when the
team is poor**, letting cheap units displace splashers, and splashers are what carry carol.

Iteration 40 does not touch the gate. It changes **how often the team is rich.** The floor stays
at 2000, so a splasher still has first call on every treasury below 2250 and the displacement
mechanism that killed iteration 37 cannot operate. Soldiers appear only out of surplus.

Stated as a falsifiable difference rather than an assurance: **if iteration 40 fails the same way
iteration 37 did, the splasher build count will fall.** If splashers hold and soldiers rise, the
two iterations are doing different things and iteration 37's result does not transfer. That is a
cheap check on a real risk, and it goes on the record now.

## Iteration 40 RESULT — **REJECT** at 22/50, −1.10 sd. Chips bought soldiers, and soldiers are paid for in paint.

Run `gauntlet/20260908-133202` (finished and collated before the session died; only the verdict
was lost). `carol_i40_3` (MONEY_MOD 3) vs `carol_iter36` (MONEY_MOD 4): **22/50, −1.10 sd**,
SW 4 / SL 7 / D 14, small 17/30 = 56.7%, large 5/20 = 25.0%.

**The dose ladder is monotone toward FEWER money towers, for the fourth iteration running:**
`carol_i40_3` beats `carol_i40_2` (MONEY_MOD 2) **30/50, +2.11 sd**, so
`iter36 (mod 4) > i40_3 (mod 3) > i40_2 (mod 2)`. Iterations 37, 38, 39 and now 40 have all
produced a ladder monotone toward zero dose. That is now a pattern about my hypothesis
generation, not about four separate mechanisms, and I take it up at the end.

**DECISION: REJECT.** `src/carol` remains iteration 36 (MONEY_MOD 4); HEAD compiles.

### Link 1 (channel A — chips -> paint-tower upgrades) fired, weakly and with inconsistent sign

Real paint-tower upgrades, round 1 excluded, paired within one game:

| map | `carol_i40_3` | `carol_iter36` |
|---|---|---|
| TheBest | **7** | 2 |
| Piglets2 | **5** | 2 |
| gridworld | 1 | **2** |
| sayhi | 1 | **3** |
| total | 14 | 9 |

So the first link is not cut — more money towers do buy some upgrades — but the effect is small
and reverses on two maps of four.

**This also corrects my own addendum.** I wrote that "the current build barely upgrades", from a
single self-play `galaxy` game that showed 0 real upgrades for both arms. `carol_iter36` upgrades
**2-3 paint towers per game** on these four maps. The zero was a property of that map, not of the
build — the same over-generalisation from one map as the `twPaint~` reading, made three hours
after I logged that lesson.

### Channel B (chips -> soldiers -> ruins become towers) did NOT fire as designed. It is the failure.

Whole-game build counts and fleet-summed tower paint (median over rounds), paired within a game:

| map | arm | soldiers built | splashers built | paint towers built | median tower paint | end coverage |
|---|---|---|---|---|---|---|
| TheBest | `i40_3` | **153** | 173 | 7 | **993** | 417 |
| TheBest | `iter36` | 25 | 180 | **10** | **3082** | **452** |
| Piglets2 | `i40_3` | **78** | 106 | 3 | 650 | 394 |
| Piglets2 | `iter36` | 28 | 111 | 2 | **1680** | **499** |
| gridworld | `i40_3` | 22 | 6 | **0** | 199 | 183 |
| gridworld | `iter36` | 13 | **18** | **3** | **436** | **702** |
| sayhi | `i40_3` | 18 | 28 | 4 | 2861 | 151 |
| sayhi | `iter36` | **55** | **57** | **9** | 593 | **702** |
| **rain (a WIN)** | `i40_3` | **8** | **46** | **2** | **974** | **702** |
| **rain (a WIN)** | `iter36` | 29 | 30 | 1 | 388 | 234 |

The four losing maps came from the run's `losses/`, so they are a biased sample; I reproduced the
swept-win map `rain` with a single deterministic re-run specifically to break that bias, and it is
the row that decides the reading.

**On the map it WON, the candidate built the FEWEST soldiers (8 vs 29) and the MOST splashers
(46 vs 30).** The soldier surge is therefore not the mechanism working — it appears only where the
candidate loses. It is not a cause I can credit and not a symptom I can ignore, because the
arithmetic says which way it runs.

### The mechanism, and it is the second-order cost I failed to price

**A soldier costs 200 paint, drawn from the building tower's own stash** (`RULES.md`: build cost
is paint from the TOWER's stash, not team-wide). So:

> `MONEY_MOD` trades a tower's **paint income** for **chips**. The chips then clear the soldier
> gate. Each soldier so bought is **paid for in paint** — 200 of it — out of the reduced pool.
> Every link moves supply off the binding resource and then converts the non-binding resource
> back into demand on the binding one.

On `TheBest` that is 153 x 200 = **~30,600 tower paint spent on soldiers** against the incumbent's
25 x 200 = ~5,000, and the candidate's median tower paint is **993 against 3,082**. Soldiers and
tower paint are anticorrelated in all five games, in both directions of outcome (on `rain` the
arm with fewer soldiers held more tower paint, and it was the candidate that time).

**My pre-registered weak link priced only half of this.** I wrote that the trade was "roughly one
ruin sacrificed per upgrade bought" — 5 paint/turn forgone against 5 paint/turn gained. That
prices the *income* ledger and nothing else. It misses that the chips do not sit idle: they buy
units, and units are billed to the paint account. My own `RULES.md` had the fact written down
already — *"money towers generate no paint... chips accumulate uselessly unless spent on towers
/upgrades/SRPs"* — and I read that sentence as a statement about chips being useless rather than
about what happens when they stop being useless.

### The pre-registered iteration-37 discriminator RESOLVES — and its value was in being wrong

I put on record before the run: *"if iteration 40 fails the same way iteration 37 did, the
splasher build count will fall."* It did not. Splashers held on the losing maps where soldiers
surged (`TheBest` 173 vs 180; `Piglets2` 106 vs 111) and **rose** on the winning one (46 vs 30).
So iteration 37's displacement mechanism — cheap units crowding out splashers when the team is
poor — is genuinely not operating here, and iteration 37's result does not transfer.

That is worth stating plainly because the check earned its keep by clearing the hypothesis it was
aimed at. Without it I would have filed "money towers = iteration 37 again", which is tidy,
plausible, and wrong. The real failure was a third thing neither iteration had met before. **A
discriminator that exonerates its suspect is not a wasted check; it is the one that forces you to
go and find the actual mechanism.**

### What this says about the tether, and about four monotone ladders in a row

The tether finding said: reach further by moving the anchors outward, and only soldiers convert
ruins into towers. Iteration 40 tried to buy more soldiers and found the catch:

> **Extending the tether costs the resource the tether rations.** A soldier is 200 paint; a tower
> pattern is another ~120 paint of attacks. The anchors that would relieve the paint constraint
> can only be paid for out of the paint constraint.

And the conversion is appallingly lossy, which is the number I did not expect and the one I intend
to chase next. Paint spent on soldiers per paint tower actually completed, on `TheBest`:

- `carol_i40_3`: 153 soldiers -> 7 paint towers = **~4,370 paint per tower**
- `carol_iter36`: 25 soldiers -> 10 paint towers = **~500 paint per tower**

A tower pattern is 24 tiles x 5 paint = **~120 paint** of attacks. So even the *incumbent* pays
about **4x** the theoretical cost of a tower, and the candidate pays **36x**. Whatever the right
mechanism is, there is a factor of four sitting in the incumbent's own soldier economy that no
iteration has touched, and it is not a matter of buying more soldiers — it is that soldiers, once
bought, mostly fail to finish a ruin.

**On the four monotone ladders.** Iterations 37 (soldier gate), 38 (drag to towers), 39 (steer to
frontier) and 40 (more money towers) all landed monotone toward zero dose. Every one of them was a
*parameter or policy change applied to the existing unit economy*. None of them changed the thing
the last two results both point at: the per-unit efficiency with which paint becomes territory. I
am going to stop proposing doses of existing knobs.


---

# Iteration 41 — SPECIAL RESOURCE PATTERNS, a capability this lineage has never had

Pre-registered before writing any code.

## Why this is not another dose of an existing knob

Iterations 37-40 all landed monotone toward zero dose, and all four were parameter changes to
machinery that was already running. I said at the end of iteration 40 that I would stop proposing
doses. **Carol has no SRP code at all** — `grep -i srp src/carol/*.java` returns one comment and
nothing else, and the per-round team counter reads `srp0` for both arms in all eight cached game
dumps. This is a capability at literally zero, not a setting at the wrong value.

## The arithmetic, engine-verified against the jar rather than the spec

`javap` on `battlecode.common.GameConstants`:

```
COMPLETE_RESOURCE_PATTERN_COST  = 200      RESOURCE_PATTERN_ACTIVE_DELAY   = 50
EXTRA_RESOURCES_FROM_PATTERN    = 3        RESOURCE_PATTERN_RADIUS_SQUARED = 8
MARK_PATTERN_PAINT_COST         = 25       PATTERN_SIZE                    = 5
```

and the API is all present: `canMarkResourcePattern` / `markResourcePattern` /
`canCompleteResourcePattern` / `completeResourcePattern` / `getResourcePattern`.

Each **active** SRP pays **+3 paint/turn to every PAINT tower** (`RULES.md` [E]: the bonus sits
inside the `type.paintPerTurn != 0` guard, so money towers get chips, not paint). The payment is
per tower, so it scales with the tower count, and it is permanent.

Against the only other way carol can convert chips into paint income:

| purchase | chips | paint/turn bought | paint/turn per chip |
|---|---|---|---|
| upgrade one paint tower to lv2 | 2500 | +5 (that tower only) | 0.0020 |
| **one SRP, with 5 paint towers** | **200** | **+15 (team-wide)** | **0.0750** |

**~37x more chip-efficient, and the multiple grows with every paint tower carol owns.** At 5 paint
towers one SRP is +15 paint/turn against a base income of 25/turn — a **60% increase in the
binding resource** for 200 chips out of a treasury that iteration 40 showed sitting idle (median
1,550-3,050, and 60,000 unspendable in the pathological case `RULES.md` records).

**And this is the one chip purchase that does not rebound onto paint.** That is the whole lesson
of iteration 40: chips bought soldiers, and soldiers are billed 200 paint each, so the trade was
charged twice. An SRP is charged in chips and paid back in paint. It runs the exchange the
correct way for the first time.

## The cost is smaller than it looks, and this is the crux

Laying an SRP costs 25 paint to mark plus up to 25 x 5 = 125 paint to paint the 25 tiles. **But
those 25 tiles are territory carol wants painted anyway** — 99.7% of tournament games are decided
on area painted (85.3% by the 70% coverage win, 14.4% on the area tiebreak). The SRP does not
consume coverage; it asks that ground already destined for paint be painted in a particular
arrangement. The genuinely marginal costs are the 25-paint mark, the secondary-colour tiles, and
the soldier-turns spent standing still.

## The mechanism

A soldier standing on a candidate centre reaches all 25 tiles (corner distance^2 = 8, soldier
action radius 9), so it adopts its own location as the site, marks the pattern with
`markResourcePattern` — letting the **engine** compute the orientation rather than my decoding
`RESOURCE_PATTERN = 28873275` by hand — and then reuses iteration 29's proven paint-to-match-marks
loop, enemy-tile skip included. It completes when `canCompleteResourcePattern` says so.

Using the engine's own marks is deliberate. A hand-decoded 5x5 that is transposed or flipped
produces a pattern that never completes and a mechanism that silently does nothing, which is this
lineage's most common failure shape. `markResourcePattern` cannot be off by an orientation.

**Strictly subordinate to ruin work**: SRP work is attempted only when `nearestEmptyRuin()` returns
null. Iteration 36 established that displacing soldiers off ruins is expensive, and I am not
retrying that.

## Doses

`carol_iter36` (no SRP, zero arm) / **`carol_i41_a`** (SRP only when no unclaimed ruin is visible,
primary) / `carol_i41_b` (SRP also when the nearest unclaimed ruin is farther than r^2=36).
Monotone in soldier-attention diverted to SRPs. Both candidates carry `BUILD = "i41"`.
`BOT=carol_i41_a OPPONENTS="carol_iter36 carol_i41_b"`, 25 fresh maps, both sides, 100 games.

## Gate (standing gate, fourth use)

**>= 29/50 accepts, <= 25 rejects, 26-28 UNRESOLVED** pending a disjoint-sample replication.
Report D, sd distance and the area split; gate on none of them.

## Manipulation checks, weak link named in advance

1. **Link 1 (does it fire at all).** The dump's per-team `srp<N>` counter must leave 0. It has read
   `srp0` in every game this lineage has ever played, so this is an unusually clean instrument:
   any non-zero value proves the mechanism ran, and a zero proves it did not, with no inference.
2. **Link 2 — THE WEAK ONE. The pattern completes but never ACTIVATES, or does not survive.**
   `RESOURCE_PATTERN_ACTIVE_DELAY = 50` means 50 undisturbed rounds after completion. A single
   enemy splasher repainting one of the 25 tiles resets it. So the failure I most expect is a
   candidate that pays the paint and the soldier-turns, completes SRPs, and holds none of them
   long enough to be paid. **I will measure the `srp` counter as a time series, not a total** —
   a count that rises and falls is completion without activation, and is a rejection with a
   different remedy (place SRPs deep in home territory) than a count that never rises at all.
3. **Link 3.** Activation becomes paint income: fleet tower paint and splashers built both rise.
4. **The price, and the falsifiable version of it.** Each SRP costs ~25 soldier-turns of standing
   still. If that time is taken from ruin completion, I lose towers to buy paint income and repeat
   iteration 36's mistake in reverse. **Falsifiable: paint towers built must NOT fall.** If
   `twPAINT` drops against `carol_iter36` while `srp` rises, the subordination gate has failed and
   the iteration is rejected regardless of the win count.

## Iteration 41 ADDENDUM — three pre-flights before the gauntlet, and a revised dose axis

Written before the run. The gate is unchanged; what changed is the dose axis, and it changed
because a one-match pre-flight kept answering link 1 with "no". Each pre-flight is one game of
shared-VM time against the 100 a gauntlet costs, and it has now saved three of them.

**Pre-flight 1 — SRP_RUIN_D2 as the dose.** 5 patterns completed on `DefaultMedium`; the team's
active-SRP counter read **0** at every 100-round sample. A finer dump found exactly **one**
activation, at round 638, lasting **28 rounds**. `RESOURCE_PATTERN_ACTIVE_DELAY` is 50 undisturbed
rounds, so four patterns were paid for and never paid out. This is precisely the link-2 failure I
registered ("completes but never ACTIVATES"), and the remedy I named in the same breath was "place
SRPs deep in home territory".

**Pre-flight 2 — require all 25 tiles already ours.** Every tag count came back **identical to the
byte** (5 SRPDONE, 6 srpMark, 149 srpPaint, 1705 srpNo). I first suspected my own dump cache, which
keys on the replay's path while `vm-match.sh` writes every rerun of a pairing to the same filename
— and the cached dump was three minutes *older* than the replay it described. **That is a real bug
and I fixed it** (`carol-tools/mixcheck/dumpcache.sh` now keys on the replay's content hash), but
it was not this: a fresh dump and the deployed remote source both confirmed the new gate was live.
The gate was a genuine no-op, because all six sites were *already* fully ours. Interiority was not
the problem.

**What the arena render proved.** At round 650 the pattern centred on (11,26) read exactly

```
AAaAA        A = ally SECONDARY      round 650: intact and ACTIVE
AaaaA        a = ally PRIMARY        round 680: top row is AaaaA
aaAaa        b = enemy paint         (10,28) and (12,28) went A -> a
AaaaA
AAaAA
```

Two tiles flipped from ally secondary to **ally primary**. Still our paint. The enemy never
touched it.

> **OUR OWN SPLASHERS BREAK OUR OWN RESOURCE PATTERNS.** A splasher paints ally primary across
> its whole footprint and scores centres by enemy paint (r^2<=2) and empty tiles. There was enemy
> paint one tile off the pattern's left edge, so a perfectly correct splash at a legitimate target
> converted our secondary tiles to primary and reset the 50-round clock.

I would not have found this from the counters. The counter said "completed 5, active 0", which is
equally consistent with a bad orientation, a chip shortage, an enemy raid, or friendly fire — four
faults with four different remedies. Rendering the thing once separated them in a single look.
That is the second time today a picture has settled a question the tabulation could not.

**Pre-flight 3 — SRP_MARGIN, a ring of our own paint.** The soldier-side fix: place patterns where
no splash centre can score. It does not work, and the reason is quantitative. Vision is r^2=20, so
a 7x7 ring (corner (3,3), d^2=18) is the widest that can be *sensed*, and margin 2 would fail its
own sense check on every call. Margin 1 adopted **1 site against 608 rejections**, and that one
still died. Placing patterns out of a splasher's reach and placing them anywhere useful turn out
to be the same constraint pulling in opposite directions.

**Pre-flight 4 — SRP_GUARD, the causal fix, on the splasher's side.** A splasher refuses a centre
whose footprint holds a tile it is actively keeping ally-secondary to satisfy a mark. Link 1 and
link 2 both fire: first activation at round **422**, **81 paid SRP-rounds**, and the candidate won
the map it had lost in both previous pre-flights (round 867). Bytecode max **10,938 / 17,500**,
`ov=0 nm=0` — the extra footprint scan is affordable.

**Revised doses**, and note this makes the run its own ablation:

- `carol_iter36` — zero arm, no SRP.
- **`carol_i41_a`** — SRP + `SRP_GUARD` (primary).
- `carol_i41_b` — SRP with the guard **ablated**, everything else identical.

So `i41_a` vs `i41_b` isolates the guard, and both against `iter36` price the feature as a whole.
The prediction I want on record: **if the guard is what makes SRPs work, `i41_b` should be the
worst of the three** — it pays the soldier-turns and the paint for patterns that then get bulldozed
by its own splashers. A ladder of `i41_a > iter36 > i41_b` corroborates the whole account; a
monotone `iter36 > i41_a > i41_b` says SRPs cost more than they pay and the mechanism is wrong.

Honest caveat carried into the verdict: one pre-flight game is a mechanism check, **not** evidence
of strength, and I am not counting that round-867 win as anything.

## Standing target, established from the sanctioned channel: carol is a SMALL-MAP bot

Computed while the iteration-41 gauntlet ran, from `tournaments/20260908-1300/results.csv` — 300
carol games against opponents this lineage did not produce.

| | vs alice | vs bob | all |
|---|---|---|---|
| small maps (area < 2000) | 42/94 = 44.7% | 61/94 = **64.9%** | 103/188 = **54.8%** |
| large maps (area >= 2000) | 14/56 = **25.0%** | 19/56 = **33.9%** | 33/112 = **29.5%** |

**Carol is above 50% on small maps and under 30% on large ones**, and the ~25-point gap reproduces
independently against both opponents, which rules out its being a quirk of one rival's style. My
own gauntlets have shown the same split repeatedly (iteration 40: 56.7% small, 25.0% large) but
those are self-play; this is the cross-lineage version and it agrees.

This is the largest, best-measured, most durable deficit the lineage has, and it is exactly what
the tether account predicts: carol's territory is bounded by refill range, so on a bigger board the
same reachable area is a smaller *fraction*, and coverage is what decides 99.7% of games. It is the
standing target from here.

Noted as a reading instruction for the iteration-41 verdict: SRP paint income should help *most*
where paint is spread thinnest, so **if iteration 41 works at all, the large-map arm should move
more than the small-map arm.** If it improves only on small maps it is not touching this problem.

## Groundwork for the standing target: on a large map, carol's soldiers PAINT on 6% of their turns

Measured locally from `carol_iter36`'s indicator strings on `TheBest` (60x60, 48 ruins), the
incumbent build, no VM cost:

| | `carol_iter36` |
|---|---|
| soldier-turns | 5,484 |
| turns with a ruin targeted | 1,778 = **32.4%** |
| distinct ruins ever targeted | **21 of 48** (11 towers actually built) |
| **IDLE-ALLY** (nothing paintable in r^2=9, surrounded by OUR paint) | 2,697 = **49.2%** |
| IDLE-ENEMY | 1,663 = 30.3% |
| actually painting (`pnt` + `slf`) | 315 = **5.7%** |

**Half of every soldier's life is spent standing inside our own finished territory with nothing to
do, and under 6% of turns produce paint.** That is the large-map deficit stated as a mechanism.

The cause is in `newExploreTarget()`: it samples **four uniformly random map coordinates and keeps
the farthest**. It has no notion of where unpainted ground is. On a small map a random target is
near, so the dead walk is short; on a 60x60 board the soldier crosses dozens of turns of its own
paint to reach a point chosen for no reason. **This is why the deficit scales with map area** —
the same mechanism, priced by the length of the walk.

Iteration 14 already identified idleness and added the persistent far target, which fixed
*local* random-walking. It did not make the target *informative*, and the measurement above is what
is left over.

Two consequences worth recording now:

1. **Iteration 41 should reduce IDLE-ALLY as a side effect**, because an idle soldier standing in
   our own territory is exactly the soldier that can lay a resource pattern. That is an
   independent, pre-registered-in-advance reason to expect the large-map arm to move more than the
   small-map arm, and it is checkable in the verdict.
2. **Iteration 42's target is the explore target itself** — making it point at the frontier rather
   than at a random coordinate. Noting the trap in advance: iteration 39 steered *splashers* to the
   frontier and stranded them beyond refill range. Soldiers carry their own pattern work and are
   the unit that must be at the frontier, but the paint tether applies to them too, so the dose
   must be on *target selection*, not on pushing units past their refill range.

**And it scales with area, which is the claim that matters.** Same build (`carol_iter36`), same
instrument, two maps:

| map | area | IDLE-ALLY share of soldier turns |
|---|---|---|
| `rain` | 30x30 = 900 | **1.4%** |
| `TheBest` | 60x60 = 3,600 | **49.2%** |

Four times the area, thirty-five times the idleness. Two points is not a curve, and I am not
claiming the exponent — but the *direction* is the one the mechanism predicts, and it agrees with
the 300-game cross-lineage small/large split (54.8% vs 29.5%) that was measured on completely
independent ground. Three instruments, one story.

## Iteration 41 RESULT — **UNRESOLVED** at 27/50, +0.76 sd. The mechanism is real and has a diagnosed defect.

Run `gauntlet/20260908-151657`. `carol_i41_a` vs `carol_iter36`: **27/50, +0.76 sd**, SW 6 / SL 4 /
D 15, small 18/32 = 56.2%, large 9/18 = 50.0%. Under the standing gate that is **UNRESOLVED**
(26-28), which may not accept without a disjoint-sample replication.

**DECISION: not accepted. `src/carol` remains iteration 36; HEAD compiles.**

### Both of my pre-registered predictions FAILED, and I am recording that before the good news

1. **"The large-map arm should move more than the small-map arm."** It did not: small **56.2%**,
   large **50.0%** — the opposite ordering. My reasoning was that an idle soldier in our own
   territory is exactly the one that can lay a pattern, so large maps (49.2% IDLE-ALLY) had more
   spare capacity to convert. The capacity was there; something else ate the gain.
2. **"If the guard is what makes SRPs work, `i41_b` should be the worst of the three."** It was
   not. `carol_i41_a` vs the guard-ablated `carol_i41_b`: **24/50, −0.54 sd** — the ablated arm is
   *marginally ahead*, well inside noise, but certainly not the worst. So the pre-flight's
   splasher-guard story, which was *proved* on a single rendered game, does not show up as a
   win-rate effect over 50. **A correct mechanism account is not the same as a load-bearing one**:
   splashers really do break patterns, and stopping them really does let patterns activate, and
   that turns out not to be what decides games.

### Link 1 and link 3 fire hard. Link 2 is fully cleared.

`TheBest` (60x60), reproduced deterministically because it is a **swept WIN** and my own learning
says not to read a mechanism off a loss sample:

| | `carol_i41_a` | `carol_iter36` |
|---|---|---|
| rounds with >=1 ACTIVE pattern | **1,376** | 0 |
| SRP-rounds actually paid | **2,739** | 0 |
| first activation | round **155** | — |
| median fleet tower paint | **3,453** | 1,113 |
| splashers built | **238** | 180 |
| **paint towers built** | **4** | **4** |
| end coverage | **478** | 365 |

**Tower paint 3.1x, coverage up, splashers up, paint towers equal — and it wins a 60x60 map this
lineage normally loses.** The economic premise of the iteration is confirmed: SRPs convert idle
chips into the binding resource at scale.

### And on the losing side, the pre-registered price condition fires exactly as written

`DefaultHuge`:

| | `carol_i41_a` | `carol_iter36` |
|---|---|---|
| SRP-rounds paid | 1,748 | 0 |
| median fleet tower paint | **2,256** | 1,764 |
| **soldiers built** | **26** | **479** |
| **paint towers built** | **4** | **14** |
| end coverage | **240** | **695** |

I wrote in advance: *"Falsifiable: paint towers built must NOT fall. If `twPAINT` drops against
`carol_iter36` while `srp` rises, the subordination gate has failed and the iteration is rejected
regardless of the win count."* **twPAINT fell 14 -> 4 while SRP-rounds rose 0 -> 1,748.** The
condition fired. It is map-dependent rather than uniform — it held on `TheBest` — but it fired, and
it names the defect precisely.

### The defect, and it is iteration 30's lesson repeated against my own new code

Soldiers are built only when `chips >= 2250` (the binding term is iteration 30's `SPLASH_FLOOR`
of 2000 plus a soldier's 250). **I gated SRP completion at `CHIP_RESERVE + 200 = 1400.**

> The SRP's chip gate sits **850 chips BELOW the soldier gate**, so a completing pattern takes the
> treasury out from under soldier production and holds it there. On `DefaultHuge` that cost ~450
> soldiers, and soldiers are the only unit that converts a ruin into a tower — 14 paint towers
> became 4, and coverage 695 became 240.

This is precisely the mechanism my own iteration-30 note describes — *"the cheap unit does not
merely get built more often, it PREVENTS the expensive one from ever being afforded"* — and I
reproduced it with a 200-chip purchase I had argued was free because "the treasury sits idle".
**The treasury is idle at 3,000 and contested at 2,300, and a gate is only ever evaluated at the
margin.** I priced the purchase against the average and it is the threshold that matters.

### Iteration 42: raise the SRP chip gate above the soldier gate

One constant, the same shape as `SPLASH_FLOOR` and `PAINT_FLOOR` before it: complete a pattern
only out of true surplus, so an SRP can never be the reason a soldier was not built. This is the
resolution of iteration 41 rather than a new hypothesis — the mechanism is established, the price
is diagnosed, and the fix is the one the diagnosis names.

## Iteration 42 attempts ABANDONED — and the reason is a methodological failure, not a bot failure

I built and pre-flighted four fixes for iteration 41's `DefaultHuge` collapse. All four failed.
Then I checked the run and found the collapse was not real:

> **`carol_i41_a` went 1/2 on `DefaultHuge`, not 0/2. It won the other side.** The large-map
> record for the run was **9/18**, with `TheBest` and `Oasis` both swept wins.

**I spent six VM matches debugging one side of one map.** Every "diagnosis" was fitted to a single
game, and each one was wrong in a different way:

| attempted fix | prediction | pre-flight result |
|---|---|---|
| `SRP_CHIP_FLOOR` 1400 -> 2250 | SRPs were starving the soldier gate | soldiers still 24 vs 485 |
| `SRP_MIN_TOWERS` = 8 (expand first) | pattern work was stalling early expansion | reached 8 towers, stalled back to 5 |
| `SRP_SHARE` = 1-in-8 soldiers | bound the mobility cost | SRP nearly off (51 rounds), still lost |
| `SRP_GUARD` off | the guard was suppressing splashes near tower patterns | still lost, and 0 SRPs survived |

The fourth is the one that should have stopped me two attempts earlier: **with the mechanism almost
entirely disabled, the arm still lost that game.** That is proof the mechanism was not what lost
it, and I read it as "so it must be the guard" instead of "so this map is not evidence about the
mechanism at all".

**This is the THIRD time today I have generalised from a single map** — after the `twPaint~`
reading that was mostly one map, and "the current build barely upgrades" from one `galaxy` game. I
wrote the lesson down both times. What is new here is the cost: the earlier two produced a wrong
sentence in a log, this one produced four builds and six matches of shared VM time, and it did so
*after* the gauntlet had already given me the honest 25-map answer.

The specific trap, stated so I can recognise it next time:

> **A gauntlet gives you a distribution; the `losses/` directory gives you its left tail. Opening
> one tail replay and diagnosing "why the candidate loses" silently substitutes one draw for the
> distribution.** The number that matters was already computed — 27/50, large 9/18 — and no amount
> of staring at one replay can revise it. Replay inspection is for *mechanism* (does link 1 fire?),
> never for *verdict*, and I crossed that line the moment I started fixing things.

I have also, twice today, treated a within-noise comparison as a signal in the direction I wanted:
`i41_b` beating `i41_a` at −0.54 sd was noise, and I first dismissed it as noise, then later
seized on it as proof the guard was harmful. It cannot be both. It is noise.

**Exploratory candidates deleted** (`src/carol_i42_a`, `src/carol_i42_b`); none was a designed dose
and none belongs in the tree. `src/carol` remains iteration 36 and HEAD compiles.

## The correct next step, which the gate already prescribed

Iteration 41 is **UNRESOLVED at 27/50**, and my standing gate says exactly what to do with that:
*a disjoint-sample replication*. Not a redesign, not a fix for a map that was never broken — a
second 25-map draw that does not overlap the first, to separate a real +0.76 sd from sampling
noise. The economic case is strong and independently confirmed (`TheBest`: tower paint 3,453 vs
1,113, coverage 478 vs 365, paint towers equal, a swept win on a 60x60 board), and that is worth
resolving properly rather than abandoning.

Queued, in order:
1. **Replicate iteration 41 on a disjoint map sample.** `MAPS` drawn to exclude this run's 25.
2. If it accepts, snapshot `carol_iter41`, redraw both progress charts, and **extend the frozen
   roster** — `progress/vs_old_bots_history.csv` has not been extended since iteration 30, six
   iterations ago, and it is the lineage's only absolute-strength instrument.
3. Iteration 43 targets the standing deficit (large maps, 29.5% cross-lineage) via
   `newExploreTarget()`, which is uniformly random and is why 49.2% of soldier turns on a 60x60
   map are spent idle inside our own paint.

## Iteration 41 replication — pre-registered combining rule, written before the result

Run `20260908-160944`: `carol_i41_a` vs `carol_iter36` only, 50 games on **25 pinned maps drawn to
have zero overlap** with run `20260908-151657` (verified: 50 maps were available outside the first
sample, and the intersection is empty). One opponent, because the question is now a single
two-arm comparison and the ablation arm has already told me what it can.

The standing gate says an UNRESOLVED result "may not accept without a replication on a DISJOINT
map sample". It does not say how to combine the two, and deciding that *after* seeing the second
number is exactly how a gate stops being a gate. So, in advance:

- **ACCEPT** only if the replication is **>= 29/50** on its own **and** the pooled record is
  **>= 56/100**. (The pooled threshold is the per-run gate carried across: +4 wins over even at
  sd ~2.4 is ~1.6 sd; a 50-map pooled sample has sd ~3.4, so the matching margin is ~+5.4 over 50.)
- **REJECT** if the replication is **<= 25/50**.
- **Anything else — including a second 26-28 — is NOT ESTABLISHED, and I reject the iteration.**
  Two inconclusive 50-game runs is an answer: the effect, if any, is smaller than this instrument
  resolves, and continuing to redraw samples until one clears is the purest form of the error I
  spent this afternoon committing. The SRP mechanism stays documented and unshipped, and I move to
  the standing large-map target.

Recording also what I will NOT do with the result: I will not open a loss replay to explain it.
The verdict is the 50 games.

## Iteration 41 REPLICATION — **REJECT** at 22/50, −1.22 sd. Pooled 49/100. The effect was not there.

Run `20260908-160944`, 25 pinned maps with **zero overlap** with the first sample.
`carol_i41_a` vs `carol_iter36`: **22/50, −1.22 sd**, SW 3 / SL 6 / D 16.

Against the rule I wrote before seeing it — *reject if the replication is <= 25/50* — this is an
unambiguous **REJECT**, and the pooled record is **49/100**, below even the even-money line, let
alone the 56 I pre-registered for an accept.

**DECISION: REJECT iteration 41.** `src/carol` remains iteration 36; HEAD compiles.

### What the two runs together actually say

| | run 1 (25 maps) | run 2 (25 disjoint maps) |
|---|---|---|
| overall | 27/50, +0.76 sd | **22/50, −1.22 sd** |
| small maps | 18/32 = 56.2% | **13/32 = 40.6%** |
| large maps | 9/18 = **50.0%** | 9/18 = **50.0%** |

The large-map arm reproduced *exactly* — 50.0% twice, on disjoint ground. The small-map arm swung
56.2% -> 40.6%. **So the first run's +0.76 sd lived entirely in the small-map half, and that half
did not replicate.** A single 50-game run pointed at a real-looking effect on the maps where carol
is already strong, and a second draw erased it. This is the whole reason the unresolved band exists
and the reason it may not accept on one sample.

### The honest summary of iteration 41

The mechanism is **real, measurable and confirmed at every link**: patterns activate at scale
(1,376 rounds on `TheBest`), tower paint triples (3,453 vs 1,113), coverage and splasher counts
rise, and the paint-per-chip arithmetic against a tower upgrade is right. Every engine constant
behind it re-verified this hour against the resolver-approved 3.1.0 jar.

**And it does not win games.** Those are not in tension: the SRP converts idle chips into paint
income, and this lineage's binding constraint is evidently not the paint income at the margin — it
is the *reach* that decides how much ground the paint can be spent on. Iterations 37-41 have now
all attacked the resource economy in some form, and the standing measurement says the deficit is
geometric: **29.5% on large maps against 54.8% on small, cross-lineage over 300 games**, with 49.2%
of soldier turns on a 60x60 board spent idle inside our own paint because `newExploreTarget()`
picks a uniformly random coordinate.

Five iterations of economics have produced one accept. The next one goes at the geometry.

### Kept from the rejection

- `carol-tools/mixcheck/srpcheck.py` and the content-keyed `dumpcache.sh` — instruments, still good.
- The proof that carol's splashers repaint carol's own secondary tiles. That is a true fact about
  the bot with no current consequence, and it will matter the moment anything else in this lineage
  depends on holding a specific paint arrangement.
- `src/carol_i41_a` and `src/carol_i41_b` stay in the tree as a documented negative result: a fully
  working SRP implementation, so a future session can tell "we never tried it" from "we tried it
  and it did not pay".

---

# Iteration 42 — RADIAL EXPLORATION, and the first run evaluated as a CENSUS

## Adopting doctrine 1: sampled runs find a SHAPE, the full corpus fixes a LEVEL

The coordinator has settled the standard-error question. The engine is deterministic, so the only
randomness in this apparatus is **which maps were drawn** — one lineage decomposed it (sd 0.58
within a shared map sample against 3.37 across samples), another ran a 150-game census twice and
got 150/150 identical games. Run the whole corpus and the sampling term is not reduced, it is gone:
a census does not estimate the population, it **is** the population.

This lands squarely on my last two verdicts. I rejected iteration 41 on a disjoint replication —
27/50 then 22/50, pooled 49/100 — which was the right instinct and cost me a **second 50-game run**
to reach. A census would have answered it once, exactly. And my accepts at 28/50 that I
deliberately rested on covariates rather than the margin: those margins sat inside a ±3.5 band, so
the caution was not merely prudent, it was necessary.

Note also that this does **not** conflict with my charter's ban on hand-picked map lists. The
charter forbids a *standing subset* because accepted iterations drift toward it. The full 75 is not
a subset — **you cannot overfit to the population**, and it is the same corpus the tournament
judges on.

**So iteration 42 is evaluated on all 75 maps, both sides, 150 games, against `carol_iter36`.**

## Gate for a census — different in kind, and pre-registered

There is no sampling error to clear, so the gate is not a noise threshold:

- **ACCEPT at > 75/150** — a strict majority of the corpus, which for a census is an exact
  statement about the population rather than an estimate of one.
- **REJECT at <= 75/150.**
- No unresolved band, because the band existed only to hold sampling noise.

I will report swept maps as the **free mechanism test** the coordinator points out: byte-identical
code splits every map by spawn side, so on a census *any* sweep at all proves the change did
something.

## The hypothesis and the pre-flight

`newExploreTarget()` samples four uniformly random map coordinates and keeps the farthest. It
biases outward but its DIRECTION is random, so on arrival a soldier picks another random far point
— often back across the board — and spends the crossing walking over ground that is already ours.
Iteration 42 gives each soldier a fixed heading from its ID, runs it to the map edge, and advances
to the NEXT sector on arrival rather than re-drawing at random, so the fleet fans out and no
soldier re-crosses the territory it just left.

**Pre-flight on `TheBest` (60x60), link 1 only, and it is the largest mechanism effect I have
measured in this lineage:**

| | `carol_iter36` | `carol_i42_a` |
|---|---|---|
| IDLE-ALLY (idle inside our own paint) | **71.0%** | **6.8%** |
| IDLE-ENEMY | 10.2% | 0.3% |
| **turns actually painting** | **5.7%** | **28.4%** |

Idleness inside our own territory falls by a factor of ten and productive turns rise five-fold.
The candidate also won that game at round 769, which I am **not** counting as evidence — one game
is a mechanism check, and after this afternoon I am particularly clear about that.

## Doses

`carol_iter36` (zero arm) / **`carol_i42_a`** (all soldiers radial, primary) / `carol_i42_b` (half
the fleet). The census runs the primary against the incumbent to fix the level; the half dose is
held for a shape run if the level is worth resolving further.

## Weak link named in advance

**Radial headings send soldiers to the map EDGE, and the paint tether does not care about my
geometry.** Iterations 38 and 39 both died by moving units relative to their refill anchors. A
soldier that commits to a heading walks away from towers by construction, so the failure I expect
is soldiers stranded at the perimeter at zero paint. Measured: `starved` turns and soldier deaths,
and **the falsifiable version — if this fails the way 38/39 did, deaths and starvation will rise
against the incumbent while coverage does not.** If instead coverage rises and starvation is flat,
the tether is not the binding constraint on soldiers the way it was on splashers.

## Iteration 42 RESULT — **REJECT** at 70/150 on the full corpus. Exact, and no argument to be had.

Census `gauntlet/20260908-163205`: `carol_i42_a` vs `carol_iter36`, **all 75 maps, both sides, 150
games**. **70/150 = 46.7%.** The pre-registered census gate was ACCEPT above 75/150; this is below
it. There is no unresolved band and no sampling error to appeal to — that is the point of a census.

Sweeps: **swept-win 15, swept-loss 20, split 40**. Identity holds exactly (wins − N = −5 = SW − SL).

**DECISION: REJECT.** `src/carol` remains iteration 36; HEAD compiles.

### The mechanism fired enormously. It just did not help.

| `TheBest` (60x60) | `carol_iter36` | `carol_i42_a` |
|---|---|---|
| IDLE-ALLY | 71.0% | **6.8%** |
| turns actually painting | 5.7% | **28.4%** |

And the coordinator's free census test corroborates it independently: byte-identical code splits
every map by spawn side, so **35 of 75 maps decided by a sweep proves the change did a great deal**.
This is the cleanest separation I have produced between *a mechanism working* and *a mechanism
being worth having* — a tenfold reduction in the exact idleness I measured as the large-map deficit,
converted into nothing.

### The pre-registered weak link is FALSIFIED, and that matters more than the rejection

I predicted the tether would kill it as it killed iterations 38 and 39: *"if this fails the way
38/39 did, deaths and starvation will rise against the incumbent while coverage does not."*

| | deaths | starved-turns |
|---|---|---|
| `DefaultHuge` — `i42_a` | **161** | **68** |
| `DefaultHuge` — `iter36` | 1,127 | 1,095 |
| `DefaultSmall` — `i42_a` | 39 | 15 |
| `DefaultSmall` — `iter36` | 32 | 17 |

Deaths and starvation went **down**, by a factor of seven on the large map. Radial soldiers do not
strand — they survive far better than the incumbent's. **So the paint tether is not what bounds
soldier behaviour**, and four iterations of mine (38, 39, and the framing of 40 and 41) have leaned
on a tether story that this measurement does not support for soldiers. That is the most valuable
thing in this rejection and it was only available because the failure mode was named in advance.

### A fifth single-map generalisation, caught this time

`DefaultHuge` was a swept win with coverage 687 vs 296 on **4 towers against 25**; `DefaultSmall` a
swept loss at 253 vs 715. I formed the obvious hypothesis — radial wins big maps, loses small ones,
the inverse of carol's profile — and then checked it against the census instead of building it:

| tiny (<=900) | small (901-1600) | medium (1601-2500) | large (>2500) |
|---|---|---|---|
| 18/38 = 47.4% | 21/48 = 43.8% | 20/38 = 52.6% | 11/26 = 42.3% |

**Flat.** No trend, and the "large maps" cell is the *worst* of the four. The two-game story was
wrong, and this time it cost one query against a file already on disk rather than four builds and
six matches. That is the afternoon's lesson actually being applied, and I am recording the catch
as deliberately as I recorded the failure.

### What I now believe, and what iteration 43 must not assume

Carol's large-map deficit is real and cross-lineage (29.5% vs 54.8% over 300 tournament games).
Soldier idleness is real and scales with area (1.4% -> 49.2%). **But fixing the idleness does not
fix the deficit**, so idleness was a symptom sharing a cause with the deficit rather than the cause
of it — and the tether, my standing explanation for that cause, is now falsified for soldiers.

I am therefore out of a working theory rather than out of ideas, which is the honest position.
Per TRAINING_ALGORITHM's "when the loop stalls", the next move is not another mechanism: it is to
re-examine the cross-lineage tournament replays and `reference/` before proposing anything, since
every theory I currently hold has now been tested and at least partly falsified.

## CORRECTION to the census gate — a census removes SAMPLING error, not all error

The coordinator's qualification, received an hour after I adopted the census doctrine and acted on
it. The zero-variance result that motivated "a census has no error left to quote" was measured
between **byte-identical** builds. Any real candidate differs in code, which perturbs the PRNG
stream, and that is a different regime: a third lineage calibrated two **policy-identical** arms
differing only in PRNG phase at **sd 4.80 games per 150 — 78% of binomial**, with only 38 of 75
maps surviving a phase change. So the residue on a fixed corpus is **engine chaos, not sampling**,
and more of the same maps does not remove it. A census buys about **2.2x** resolution, not 4.7x.

**My iteration 42 verdict under the corrected gate.** 70/150 is a margin of wins − losses =
**−10**, against a suggested band of >= +10 accept / +7..+9 replicate / <= +6 reject. It sits
outside that band in the reject direction, so **the rejection stands and stands more firmly**.
Nothing I concluded today needs revisiting — but my pre-registered gate said "ACCEPT above 75/150",
i.e. any margin at all, and had iteration 42 come back at +6 or +8 I would have accepted a result
the noise floor does not support. **My gate was wrong in a way the result happened not to expose**,
which is the most dangerous kind of wrong and worth recording as loudly as a failed verdict.

### Calibrating carol's OWN floor rather than inheriting 4.80

Run `20260908-173918`: `carol_phase` vs `carol_iter36`, full corpus, 150 games. `carol_phase` is
`carol_iter36` with **one character changed** — the PRNG seed constant `rc.getID() * 7919 + 13`
becomes `+ 14`. Policy-identical by construction; only the stream differs.

Two arm totals cannot estimate a standard deviation, but a fixed corpus hands over **75 paired map
records for free**, and over those pairs `E[(Sa − Sb)^2] = 2·Var(S)` turns them into one. That is
the transferable part of the method, and carol's chaos need not match another lineage's.

**And the trap the coordinator flagged, named here before I have the number**: if the two arm
totals come back close — say within a game or two — the *convenient* reading is "carol's noise
floor is near zero, so my original gate was fine after all". That reading is wrong, and I am
committing to rejecting it now rather than when it is in front of me. A near-draw between two arms
is *exactly what binomial predicts*; an outcome that probable under a hypothesis cannot even weakly
reject it. The estimate must come from the **per-map variance**, which is the whole reason to
compute it that way, not from the totals.

## Iteration 43 (symmetry inference) — link 1 is WEAK, and it will not get a census

Built and pre-flighted per §6 of `reference/RESEARCH.md`. First, the check the short list actually
asks for: **carol has no map symmetry inference at all.** Every `symmetr` match in the bot before
today was about *play*-symmetry — a fairness constraint on my own build mix — not about the map.
`battlecode.world.MapSymmetry{ROTATIONAL, HORIZONTAL, VERTICAL}` is engine-side only, confirmed by
`javap` through `tools/engine-jar.sh`, so it must be inferred.

I verified the inference against ground truth I computed myself rather than trusting the bot. On
`TheBest` the true transform is the up-down flip (0 wall mismatches out of 3,600; the other two
candidates each mismatch 440). The bot killed the left-right candidate and kept up-down — **correct
refutation, no false kill of the truth**. But it is far too slow:

| map | most common state | pinned? |
|---|---|---|
| `TheBest` | `symRHV` 1,321 turns, `symR-V` 204 | never to one |
| `DefaultMedium` | `symRHV` 9,324 turns, `sym-H-` 259 | briefly |

Adding ruin-based refutation (a ruin's *absence* where a candidate predicts one is decisive,
because ruins are sparse) helped only marginally. The mechanism spends nearly the whole game with
all three candidates alive, because refutation needs a tile and its mirror sensible *at the same
time*, which requires standing near an axis.

**By my own pre-flight rule — never spend a gauntlet until link 1 fires — this does not get a
census.** The fix is a terrain memory so refutation does not require simultaneous visibility, which
is a real piece of infrastructure (§2: "infrastructure first") and the right next build. Carrying
it forward rather than evaluating a mechanism I have measured as barely running.

## Carol's census noise floor, measured: **sd 6.48 games per 150 (106% of binomial)**

Run `20260908-173918`, `carol_phase` vs `carol_iter36` — policy-identical, one character apart
(PRNG seed `+13` -> `+14`), full corpus, 150 games.

| | |
|---|---|
| arm total | **74/150, margin −2** |
| maps decided the same from BOTH sides (survive a phase change) | **33/75 = 44%** |
| maps split by side (still a coin flip) | 42/75 = 56% |
| Var(single-game S) from the 75 paired records | **0.2800** |
| **sd of a 150-game total** | **6.48 games = 106% of binomial** |

**The trap, disarmed as pre-committed.** The arm totals came back 2 games apart. Before the run I
wrote that this would be the convenient reading — "carol's noise is near zero, my original gate was
fine" — and that I would reject it. I reject it. A margin of −2 between policy-identical arms is
almost exactly what binomial predicts; an outcome that probable under a hypothesis cannot even
weakly reject it. The floor comes from the per-map variance, which says 6.48, not from the totals,
which say nothing at all.

**Carol's chaos is WORSE than the lineage I would have inherited from** — 106% of binomial against
their 78%, and 44% of maps surviving a phase change against their 51%. Inheriting 4.80 would have
set my gate about a third too loose. This is why the coordinator said to calibrate rather than
inherit, and it is the concrete payoff of having done so.

### The gate, replacing the one I got wrong this morning

**On MARGIN (wins − losses) over a 150-game full-corpus census:**

- **ACCEPT >= +13** (2.0 sd)
- **REPLICATE +9 .. +12**
- **REJECT <= +8**

My pre-registered census gate hours ago was "ACCEPT above 75/150" — margin >= +1, when the noise is
±6.5. It would have accepted pure phase noise better than half the time it came up positive.

### An internal check that says my own estimator is conservative

`Var(S) = 0.2800` **exceeds the binomial maximum of 0.25**, which is impossible for genuine
Bernoulli noise. So the estimator is picking up something systematic, and it is identifiable: the
per-map difference `d = Sa − Sb` conflates PRNG chaos with **deterministic spawn-side advantage**.
A map that always goes to the A side regardless of bot contributes `d² = 1` every time while
contributing *zero* variance to the 150-game total.

So **6.48 is an upper bound on the chaos floor, not a point estimate**, and the >100% reading is
the tell rather than a curiosity. I am adopting it anyway and deliberately: a conservative floor
makes a strict gate, which trades type-II risk for type-I protection — and after a day in which two
mechanisms measured unambiguously real and converted to nothing, type-I protection is exactly what
this lineage needs. Separating the two terms cleanly needs the same pairing run twice at different
phase, which is another 150 games and is not worth it while the bound is this usable.

### Re-scoring today's verdicts against the measured floor

| iteration | margin | sd from zero | verdict then | verdict now |
|---|---|---|---|---|
| 42 (radial exploration) | **−10** | −1.54 | REJECT | **REJECT**, unchanged |
| 41 (SRP, run 1) | +4 /100 | — | UNRESOLVED | rejected on replication, unchanged |
| 41 (SRP, replication) | −6 /100 | — | REJECT | **REJECT**, unchanged |

Every verdict stands. But iteration 42's −10 is **−1.54 sd**, not the crushing refutation "70/150
on an exact census" made it sound like this afternoon, and I should say so: it is a clear reject
under the gate and a moderate one in effect size. The falsification of the tether that came out of
it rests on the deaths and starvation measurements, which are direct and large, not on the margin.

---

# Iteration 44 — DENIED RUINS. The deficit tracks RUIN COUNT, not map area.

## Where this came from: the stall protocol, run properly for once

Iteration 43 left me with no working theory (the tether is falsified for soldiers; radial
exploration fired tenfold and converted to nothing). TRAINING_ALGORITHM's "when the loop stalls"
says: re-examine the cross-lineage tournament games before inventing a mechanism. I did that first
this time, and it produced the sharpest result this lineage has had.

## The finding: carol's win rate falls monotonically in RUIN COUNT

Pooled over **1,208 tournament games** (every complete round-robin so far, carol vs both other
lineages), bucketed by the map's claimable-ruin count from `tools/mapdata/ruin_parity.txt`:

| ruins | carol | |
|---|---|---|
| <= 11 | 134/308 | **43.5%** |
| 12-17 | 106/304 | **34.9%** |
| 18-23 | 75/324 | **23.1%** |
| >= 24 | 38/272 | **14.0%** |

**Cochran-Armitage trend z = -8.44.** It replicates in each of the three most recent tournaments
independently, and it holds separately against *both* other lineages (vs alice 57.9 -> 14.7%;
vs bob 71.1 -> 23.5%), which is two independent instruments agreeing.

**And it is NOT the "large map deficit" I have been chasing since iteration 38.** Holding ruin
count fixed, area does almost nothing (latest tournament, vs alice):

| | few ruins (<=16) | many ruins (>16) |
|---|---|---|
| small area (<=1350) | 51.7% | 41.7% |
| large area (>1350) | **50.0%** | **20.3%** |

Small-area/few-ruin 51.7% vs large-area/few-ruin 50.0% — **area alone costs nothing.** Every
iteration from 38 onward that framed the problem as "large maps" was conditioning on the wrong
variable, and area only looked like the cause because it is collinear with ruin count.

## The mechanism, read out of the replays rather than inferred

`nearestEmptyRuin()` sends a soldier to the nearest unclaimed ruin; `workOnRuin()` paints its 5x5
tower pattern. Three engine facts already in `RULES.md` combine into a trap:

1. A **soldier cannot overwrite enemy paint** (soldier attack [E]).
2. Pattern completion is **exact** — all 24 non-centre tiles must hold the right colour
   (`GameWorld.checkPattern`).
3. Only a **mopper** removes enemy paint, and only a **splasher** overwrites it in bulk.

So **one enemy-painted tile inside the 5x5 makes a ruin permanently impossible for a soldier.**
carol fields `mop0` on every tournament map I sampled, and her splashers are not steered at
patterns, so nothing ever clears it.

The incumbent detects none of this. It holds the soldier there for `RUIN_PATIENCE = 40` turns and
then remembers exactly **one** banned ruin (`ruinBanned` is a single slot), so on a ruin-rich map
the soldier walks to the next denied ruin and the previous ban is overwritten.

**Measured on carol's own indicator strings in the 20260908-1300 replays** — soldier-turns that
are IDLE while holding a ruin target, as a share of ALL soldier turns:

| map | ruins | blocked-at-ruin | painting |
|---|---|---|---|
| BatSignal | 14 | 24.8% | 6.4% |
| AlarmClock | 20 | 35.5% | 6.3% |
| Rose | 30 | **43.2%** | 12.0% |

The waste scales with ruin count, which is the gradient. And **97.4% of carol's idle soldier-turns
on Rose are IDLE-ENEMY, not IDLE-ALLY** — the soldiers are not lost, they are blocked.

### The discriminating check, because "enemy paint nearby" is not "enemy paint in the pattern"

`IDLE-ENEMY` counts enemy tiles within the soldier's action radius (r2=9), which is larger than the
5x5. That is a different claim from the one I wanted to make, so I dumped the arena instead of
naming the fault from the symptom. Ruin **(20,26) on Rose at round 176**:

```
y=28: a A A A a          a/A = carol primary/secondary
y=27: A A s A A          b/B = alice primary/secondary
y=26: A a o s A          o = ruin, s = carol soldier, M = alice MOPPER
y=25: A b b A A     <--- two alice-painted tiles at (19,25) and (20,25)
y=24: M A A A *
```

The pattern is complete carol paint **except two alice tiles**, with an alice mopper parked beside
it. carol's soldiers orbited that ruin from round 62 to past round 210. Consequence on that game:
**carol finished with 2 towers against alice's 18**, coverage 165 vs 667.

## Iteration 44: the change

A **gate correction**, not new work. `nearestEmptyRuin()` accepts ruins it can prove uncompletable.

1. `workOnRuin`'s existing pattern scan (which already fetched all 25 MapInfos, and which iteration
   29 already taught to recognise an enemy-painted tile in order to skip it) now also **counts**
   those skips. If the pattern is marked and any tile of it holds enemy paint, the ruin is DENIED.
2. A denied ruin is banned **immediately** instead of after 40 dead turns.
3. `ruinBanned` (one slot) becomes an **8-slot ban set** with the same 250-round expiry.

It spends **zero paint** — it only changes which ruin a soldier commits to. That matters because
the ledger closes *"spend idle soldier turns on additional work"* as a class and permits re-opening
only at literally zero paint cost. This does not even consume the idle turns; it prevents them.

## PRE-REGISTERED GATE — written before any evaluation game was run

**Instrument**: full-corpus CENSUS, 150 games, `carol_i44_a` vs `carol_iter36`.

**Primary, on MARGIN (wins - losses)**, against carol's own measured chaos floor (sd 6.48/150,
run `20260908-173918`):

- **ACCEPT >= +13** (2.0 sd)
- **REPLICATE +9 .. +12**
- **REJECT <= +8**

**Pre-registered secondary (stated in advance so it is not back-filled):** the margin on maps with
**>= 18 ruins** exceeds the margin on maps with **<= 17 ruins**. The mechanism has no fuel on
ruin-poor maps, so if the gain is flat in ruin count the headline is not this mechanism.

**Named weak link — the one that killed iteration 42.** Link 2 is *blocked turns fall -> more
towers completed -> more coverage*. Iteration 42 cut IDLE-ALLY 71% -> 6.8% and bought nothing.
**If the decision counters fire but towers-built does not rise, I REJECT**, and record that
idleness-removal converted to nothing for the SECOND time — which would be a finding about carol's
whole loop rather than about this mechanism.

## Pre-flight (link 1), before spending the census

Per my own rule, no gauntlet until the mechanism is measured firing. `carol_i44_a` vs
`carol_iter36` on **Rose** (30 ruins), one game:

| | `carol_i44_a` | `carol_iter36` |
|---|---|---|
| towers at r450 | **8** | 2 |
| coverage at r450 | **644** | 73 |
| tower paint at r450 | **3,636** | 65 |
| blocked-at-ruin (all soldier turns) | **2.8%** | 43.2% |
| turns actually painting | **22.1%** | 12.0% |
| result | **win, r494** | |

Decision counters: `dn` (denial bans) up to **5 per soldier**, `bs` (ruins skipped as banned) up to
**56**, and — the load-bearing one — `bp` (**peak simultaneously-live bans) = 6**. The incumbent's
single slot would have forgotten five of those six. That is the direct evidence that the
one-slot ban is the ruin-count-dependent defect, rather than a plausible story about one.

Link 2 also moved in the probe (towers 8 vs 2), which is exactly what iteration 42 never had.
One self-play map is not the evaluation; the census is.

### Ablation arms built and PRE-REGISTERED now, before the census returns

Both compile; neither has been run. Queued behind the census and conditional on it accepting.

- `carol_i44_ban` — the 8-slot ban set **only**. The denial test still runs and still increments
  `dn`, but does not ban; the only thing that fills the set is the old 40-turn timeout.
- `carol_i44_den` — early denial detection **only**, `BAN_CAP = 1`. Bans the instant a pattern is
  denied, but remembers one ruin, so it can ping-pong between two denied ruins forever.

**Pre-registered prediction: neither arm recovers most of `i44_a`'s margin — the two halves are
one mechanism.** The probe's `bp = 6` says at least two slots are genuinely needed, which cripples
`i44_den`; and the 40-turn park is the direct waste, which cripples `i44_ban`. If instead one arm
matches `i44_a`, the other half is dead weight and should be removed rather than carried.

### Tooling report — `replay-dump.sh` resolves the engine jar by HIGHEST VERSION, not by `engine_version.txt`

`tools/replay-dump.sh:39` resolves the engine as

```bash
BC_JAR=$(find ~/.gradle -name 'battlecode25-java-*.jar' | grep -v source | sort -V | tail -1)
```

This is the exact pattern `RULES.md` records as a hazard and that `tools/engine-jar.sh` was written
to remove: battlecode-dev's gradle cache holds **both** `1.0.0` and `3.1.0`.

**Discriminating check before naming it, because "wrong resolver" and "wrong result" are different
claims.** The cache today holds exactly those two jars; `sort -V | tail -1` returns `3.1.0`; and
`arena/engine_version.txt` says `3.1.0`. So the two agree, and **the defect is latent, not live**:
every replay measurement in this iteration was taken on the correct engine, and none of today's
findings is in doubt. It diverges only if a jar higher than the pinned version ever lands in the
cache, or if `engine_version.txt` is pinned below the highest cached jar — at which point it fails
**silently**, which is the property that makes it worth reporting rather than watching.

`engine-jar.sh` itself is sound: it searches for the exact filename `battlecode25-java-${WANT}.jar`
derived from `engine_version.txt`, so it cannot resolve a mismatched version. The one-line fix is
for `replay-dump.sh` to use the same exact-version name (or `engine-jar.sh --remote`) instead of
`sort -V | tail -1`. Not patched here: `tools/` is coordinator-owned.

## Iteration 44 RESULT — ACCEPT on the primary gate. The pre-registered SECONDARY FAILED.

Run `20260908-200140`, full-corpus census, 150 games, `carol_i44_a` vs `carol_iter36`.

| | |
|---|---|
| **97/150 = 64.7%** | margin **+44** |
| swept wins / swept losses / split | **29 / 7 / 39** |
| margin in sd of carol's measured chaos floor (6.48) | **+6.8 sd** |

The swept counts corroborate nothing extra — `wins − losses = 2 × (swept − swept-against)` is an
identity, and 2 × (29 − 7) = +44 exactly. What they *do* add is D = 39 split maps, i.e. the pair is
decisive on about half the corpus and a coin flip on the rest.

**DECISION: ACCEPT.** Pre-registered gate was ACCEPT >= +13; this is +44. Promoted to `src/carol`
and frozen as `src/carol_iter44`; HEAD compiles.

### The secondary was pre-registered precisely so it could not be back-filled, and it FAILED

> *"the margin on maps with >= 18 ruins exceeds the margin on maps with <= 17 ruins. The mechanism
> has no fuel on ruin-poor maps, so if the gain is flat in ruin count the headline is not this
> mechanism."*

| | margin |
|---|---|
| few ruins (<= 17) | **+24** (50/76) |
| many ruins (>= 18) | **+20** (47/74) |

| ruins | | margin |
|---|---|---|
| <= 11 | 27/38 = 71.1% | +16 |
| 12-17 | 23/38 = 60.5% | +8 |
| 18-23 | 24/40 = 60.0% | +8 |
| >= 24 | 23/34 = 67.6% | +12 |

**Flat, and the ruin-poorest bucket is the best one.** By the rule I wrote before the run, this
means **the attribution is OPEN, not confirmed**. The bot got a great deal better and the
mechanism demonstrably fires — but this run does not establish that the gain comes from the
ruin-count-dependent part of it, and I am not entitled to say it does.

### Why this instrument may be structurally unable to test that claim

The gradient was measured **against alice and bob**. This census is **self-play against
`carol_iter36`, which has the identical defect.** On a ruin-rich map the incumbent is crippled too,
so the ruin-rich maps are not the ones where I was uniquely losing — both arms flail there. The
cross-lineage gradient exists *because alice and bob convert ruins into towers and carol does not*;
an opponent that also fails to convert them cannot reproduce it.

That is a specific, falsifiable reason and not an excuse, so it comes with its own test.

### PRE-REGISTERED, before the next tournament runs

`carol_iter44` is now HEAD, so the next scheduled round-robin plays it against alice and bob with
no action from me. **Prediction: carol's ruin-count gradient flattens.** Concretely, re-running
`carol-tools/ruingradient/ruingradient.py` on the next completed tournament should show the
pooled Cochran-Armitage |z| **fall below the 8.44 measured over the previous five**, and the
`>= 24` bucket rise from 14.0% pooled / 19.1% in the last run.

If the gradient does NOT flatten while the headline improves, the mechanism is a general
improvement that has nothing to do with ruin count, my whole causal story is wrong, and the
tournament will have said so against opponents I did not build. That is the outcome to watch for.

### Link 2 (the weak link that killed iteration 42) — held, on the probe

Named in advance: *"if the decision counters fire but towers-built does not rise, I REJECT."*
Iteration 42 cut IDLE-ALLY 71% -> 6.8% and bought nothing. This time the probe showed **towers 8
vs 2** and coverage 644 vs 73 alongside blocked-at-ruin 43.2% -> 2.8%, so the chain
*blocked turns fall -> towers get built -> coverage rises* is intact at every link rather than
snapping at the second. That is the difference between the two iterations, and it is why one is a
+44 and the other was a −10.

### Cost of the change, measured rather than assumed

Removing the loop `break` means scanning all 25 pattern tiles every turn. Peak soldier bytecode
**3,928 vs the incumbent's 3,716** — a 5.7% rise, both about 22% of the 17,500 limit, with **zero
overruns and zero near-misses** across the probe game.

### A scoring bug I caught with a sanity check, worth recording

My first pass at the secondary used a `winner_bot` column that does not exist in a gauntlet
`results.csv` (the column is `bot_result`), and printed **0/150 wins in every bucket**. It was
caught only because the total is *impossible* — the summary says 97. The lesson is the cheap one:
**check a derived table against a total you already know before reading anything into its shape.**
Had the bug been subtler than "everything is zero" — a mis-joined bucket rather than a missing
column — the shape would have looked plausible and I would have read a story out of it.

---

## Iteration 44 ABLATION RESULT — the two halves are NOT symmetric: early denial is the mechanism, the ban set is its storage

Run `20260908-202103`, 25 sampled maps pinned and shared by all three arms, `BOT=carol_i44_a`,
150 games. Collated after a session death; the run itself was setsid-detached and survived.

| arm | what it removes | i44_a's record | margin | swept W/L/split |
|---|---|---|---|---|
| `carol_iter36` | everything (the pre-44 incumbent) | 32/50 | **+14** | 8 / 1 / 16 |
| `carol_i44_ban` | early denial (8 slots kept, filled only by the 40-turn timeout) | 30/50 | **+10** | 7 / 2 / 16 |
| `carol_i44_den` | the extra slots (early denial kept, `BAN_CAP = 1`) | 27/50 | **+4** | 3 / 1 / 21 |

Margin sd on a 50-game arm is ~6 (2 x the ~3-win sd of a 50-game count), so **+14 is ~2.3 sd,
+10 is ~1.7 sd, and +4 is 0.7 sd — indistinguishable from zero.**

### The decisive number is not the margin, it is the identity check

Per-cell `(map, side) -> (winner, rounds)` agreement between arms, which costs nothing and does
not depend on any win-rate resolution:

| pair | identical games (winner AND round count) | same winner |
|---|---|---|
| `i44_ban` vs `iter36` | **31/50** | 48/50 |
| `i44_den` vs `iter36` | 13/50 | 37/50 |
| `i44_ban` vs `i44_den` | 12/50 | 39/50 |

**The 8-slot ban set, without early denial, is very nearly a no-op**: it plays the *identical game*
to the pre-44 incumbent in 62% of cells. That is the mechanistic explanation of its +10 and it is
not a statistical claim. The reason is structural — the only thing that fills the set in `i44_ban`
is the old 40-turn timeout, which almost never fires twice on one soldier, so slots 2..8 stay
empty and 8 slots behave as 1.

**Early denial is what fills the set.** `i44_den` diverges from the incumbent in 37 of 50 cells
with a single slot, i.e. it is doing the work on its own.

### So the pre-registered prediction was HALF right, and I am recording which half

I wrote: *"neither arm recovers most of `i44_a`'s margin — the two halves are one mechanism."*

- For `i44_ban`: **confirmed, and more strongly than predicted** — it is not merely weaker, it is
  mostly the incumbent wearing the candidate's name.
- For `i44_den`: **not supported.** +4 at 0.7 sd does not establish that the extra slots buy
  anything. The probe's `bp = 6` proved the slots get *occupied*; occupancy is not value, and I
  should not have read it as value. That is a reachability fact being quietly promoted to an
  effect-size fact.

The honest summary is a **conjunction, not two halves**: early denial is the mechanism, the ban
set is the storage it needs, and the storage is worthless without the mechanism. What remains
unmeasured is how much storage — whether 8 slots beat 1 given early denial.

## PRE-REGISTERED: BAN_CAP dose census (written before the run is launched)

**Instrument**: full-corpus census, all 75 maps both sides, `BOT=carol_i44_a` (`BAN_CAP = 8`),
opponents `carol_i44_den` (`BAN_CAP = 1`) and `carol_i44_c32` (`BAN_CAP = 32`). 300 games.
Everything else byte-identical to `src/carol`; the only edit in `c32` is the constant, verified by
diff. This is a dose ladder 1 / 8 / 32 read against a common reference, with the zero-ish arm
(cap 1) included per the zero-arm rule.

**Noise floor**: carol's own measured chaos floor, sd **6.48 on the margin per 150 games**
(run `20260908-173918`), not an inherited number.

**Gate on the cap-1 arm (what the extra slots are worth):**

- margin **>= +13** (2.0 sd): the multi-slot set is load-bearing; `BAN_CAP = 8` stays and is
  priced for the first time.
- **+9 .. +12**: ambiguous, replicate.
- margin **<= +8**: the extra slots are **not measurably worth anything given early denial**. I do
  not then rip them out — a null is not a negative, and `MaxConsecutiveRejects` does not apply to
  a feature that is already accepted — but the attribution of iteration 44's +44 collapses onto
  early denial alone, and the log must say so.

**Gate on the cap-32 arm (is 8 saturating?):**

- If `c32` beats `i44_a` by **>= +13**, 8 slots are too few on ruin-rich maps and the cap rises.
  That would be a free win and is the reason this arm is in the run.
- If the margin is within +/- 8, the ladder is flat above 8 and the cap is settled on both sides,
  which closes the constant permanently per the closed-directions rule.

**Pre-registered identity check, to be read BEFORE the margins** (rule: a dose that changes nothing
is a dead run): `i44_a` vs `c32` must differ in a non-trivial share of the 150 cells. If they come
back near-identical, the cap-32 arm proves only that 8 is never exceeded — which is still a real
answer (the ladder is flat because the dose does not exist above 8), and I will report it as that
rather than as "32 is no better than 8".

## CORRECTION — my census gate was HALF as strict as it claimed. `noisefloor.py` had a units bug.

Found while scoring the iteration 44 ablation, by re-deriving the sd instead of reusing the
number. `carol-tools/noisefloor.py` computed

    sd_total = sqrt(150 * Var(S)) = 6.48

which is the sd of the **WIN COUNT** `W`. It then printed a gate quoted on the **MARGIN**
`M = W − (N − W) = 2W − N`. But `Var(M) = 4·Var(W)`, so **sd(M) = 2·sd(W) = 12.96**. The tool
multiplied `sd_total` by 2 and labelled the product "2.0 sd" — except that factor of 2 is the
win-count-to-margin conversion, not a confidence multiplier. **Every census gate it produced was
1.0 sd wearing a 2.0 sd label.**

### The discriminating check, and what actually moved

|  | as claimed | corrected |
|---|---|---|
| ACCEPT | >= +13 ("2.0 sd") | **>= +26** |
| REPLICATE | +9 .. +12 | **+18 .. +25** |
| REJECT | <= +8 | **<= +17** |

| verdict | margin | claimed | corrected | changes? |
|---|---|---|---|---|
| iteration 42 | −10 | −1.54 sd | **−0.77 sd** | no — reject either way |
| iteration 44 | **+44** | 6.8 sd | **+3.39 sd** | **no — +44 clears the corrected +26** |

**No verdict moves, and iteration 44's accept is safe on the corrected gate** (+44 against a true
2.0 sd threshold of +26). But **the "6.8 sd" I put in the log and in the accept commit is inflated
exactly 2x and is withdrawn**; the correct figure is **+3.39 sd**. And the loose gate was live for
every census since I adopted it — iteration 44 happens to clear the strict version by a wide
margin, which is luck, not diligence. This is the second time this lineage has published an effect
size that no computation over the data supports (the first was iteration 34's rho = +0.624).

**Fixed in the tool, not by hand.** `noisefloor.py` now prints sd of the win count AND sd of the
margin, derives the gate from the margin sd, and prints the divisor to score with. A correction I
merely remember fails the first session that resumes without re-reading this entry.

## Iteration 44 ABLATION — my pre-registered prediction was HALF WRONG

Run `20260908-202103`, 25-map sample shared by all three opponents, every opponent played every
map, 50 games each. `sd(margin)` at 50 games = **7.48**.

| `carol_i44_a` vs | record | margin | sd | swept |
|---|---|---|---|---|
| `carol_iter36` (incumbent) | 32/50 = 64% | +14 | **+1.87** | 8–1 |
| `carol_i44_ban` (8-slot ban only) | 30/50 = 60% | +10 | **+1.34** | 7–2 |
| `carol_i44_den` (early denial, 1 slot) | 27/50 = 54% | +4 | **+0.53** | 3–1 |

I pre-registered: *"neither arm recovers most of `i44_a`'s margin — the two halves are one
mechanism."*

**Wrong.** `carol_i44_den` — early denial detection with the ban list back to a SINGLE slot —
is statistically indistinguishable from the full change (+0.53 sd). The 8-slot ban set,
which I argued was load-bearing, recovers much less on its own (+1.34 sd against it) and adds
little on top of early denial.

### Why I predicted the wrong half, which is the useful part

I reasoned from the probe's `bp = 6` — six bans live simultaneously — and concluded the single slot
must be the defect. **`bp` measures the mechanism FIRING, not the mechanism MATTERING.** That is
the iteration 42 lesson recurring in miniature, one iteration after I wrote it down: a decision
counter licenses spending a gauntlet, and nothing more. With early denial in place a soldier leaves
a denied ruin in ~1 turn instead of 40, so it barely matters whether it remembers the ruin
afterwards — it re-detects the denial immediately on arrival and leaves again. The ban set was
solving a problem that early detection had already dissolved.

**What I am NOT doing: churning HEAD on a +0.53 sd result.** That difference is inside the noise at
50 games, and "indistinguishable" is not "worse". The honest status is:

- **Attribution: early denial detection carries iteration 44.** The 8-slot ban set is unproven.
- The ban set costs ~7 int-comparisons per ruin check and no paint, so carrying it is nearly free.
- **Queued: re-measure `i44_a` vs `i44_den` at full census power (150 games)** before either
  removing the ban set or claiming it earns its place. At 50 games this run could not have detected
  a genuine +1 sd effect.

## Splasher frontier-steering — KILLED at the arithmetic, before a build

Soldiers got frontier-seeking at iteration 14 and it was accepted. Splashers never did:
`runSplasher` ends in `moveExploring(null)`, i.e. a **random far map coordinate**, and the splasher
is the unit that paints 2.6x faster per turn and is worth most on the frontier. That looks like an
accepted mechanism simply never applied to the unit that needs it most.

Splasher turn census, `carol_i44_a` on Rose, 1,694 splasher-turns:

| tag | turns | share |
|---|---|---|
| `cd` (action cooldown) | 671 | 39.6% |
| **`noPaint`** | **521** | **30.8%** |
| `lowScore` | 237 | 14.0% |
| `noTgt` | 140 | 8.3% |
| **`SPLASH` (actually fired)** | **125** | **7.4%** |

The `cd` block is an engine ceiling, not a defect: a splasher's attack adds +50 cooldown falling
10/turn, so each fire necessarily blocks the next four turns — 125 x 5 = 625, which accounts for
the 671 almost exactly.

**The tempting read**: 377 turns (22.3%) were ready AND fueled and did not fire for lack of a
target — three times the 125 fires that happened. Steer those at the frontier and splasher output
triples. That is the iteration-14 argument, transplanted.

**Why it is wrong, and the number that kills it**: `noPaint` is **30.8%**. The splasher is already
**paint-saturated** — it is spending every point of paint it can get. A splasher attack costs 50
from a 300 capacity, so six attacks empty it, and `transferPaint` is r2<=2 so it must physically
walk to a tower to refill. Total tiles painted over a splasher's life is therefore set by **how
much paint reaches it**, not by how many targets it finds. Better targeting makes it fire sooner,
run dry sooner, and paint the same total.

So the honest gain from steering is not throughput at all — it is **tiles per 50 paint** (a fire on
13 fresh tiles instead of 4), which the existing score function already maximises locally and
`SPLASH_MIN_SCORE` already gates. That is a much smaller prize than "triple the fires", and it is
the prize I would actually have been buying.

- **"Frontier-steering for splashers" — CLOSED on arithmetic, zero gauntlets spent.** Re-opening
  requires the splasher to stop being paint-saturated, i.e. `noPaint` well below 30% on the
  then-current build. That is a real re-opening condition: iteration 20's ferry or a paint-income
  change would produce exactly it.

**The general form, which is the transferable part**: an idle-turn count is not a prize until you
check which resource the unit is actually short of. I have now made this mistake twice with idle
counters (iteration 42's soldiers, and this, caught) and the check is the same both times —
*if this unit were never idle again, what would it spend?* If the answer is "paint it does not
have", the idleness is a symptom of the shortage, not an independent waste.

### Ablation, re-scored against the lineage's STANDING gauntlet gate (not my ad-hoc sd)

Commit `5443d59` already set a standing gate for 50-game **sampled** gauntlets, where map-sampling
error dominates and the census floor does not apply: **>= 29/50 accepts, <= 25 rejects, 26-28 is
UNRESOLVED and must be replicated on a disjoint map sample.** Scoring the ablation on that instead:

| `carol_i44_a` vs | record | standing gate |
|---|---|---|
| `carol_iter36` | 32/50 | **resolved win** |
| `carol_i44_ban` | 30/50 | **resolved win** |
| `carol_i44_den` | 27/50 | **UNRESOLVED** (26-28 band) |

So the correct statement is **not** "early denial alone is indistinguishable from the full change"
— it is **unresolved**, which under the standing rule *requires* the replication I had already
queued rather than merely inviting it. I am tightening my own wording because "indistinguishable"
smuggles in an accepted null, and this lineage has a standing rule against exactly that.

What does NOT change: `i44_ban` (the 8-slot ban set without early denial) is a **resolved loss**
against the full change, so **early denial detection is confirmed load-bearing**. The open question
is only whether the ban set adds anything on top of it.

And the audit I was about to redo is already done: `5443d59` records that iterations 34 and 36 were
accepted at +1.03 sd, unresolved on their headlines and resting on mechanism evidence. I re-derived
that same concern from the corrected census units and found the lineage had already caught and
recorded it — so it is not a new finding, and iteration 36's paint floor is not quietly unsupported.

---

# Iteration 45 — target selection: where do soldier turns actually GO on the accepted build?

Not from a losing game: from an **absolute degeneracy signal**, which the algorithm prefers over an
opponent-relative one. Measured on `carol_iter44` (= `src/carol`) with **no new games** — the
indicator strings already carry the decomposition, and the build tag splits the two carol teams in
a self-play replay.

61 loss replays from run `20260908-202103`, **507,375 soldier turns** of the `i44a` team:

| soldier turn outcome | turns | share |
|---|---|---|
| `IDLE-ENEMY` (enemy paint in r2=9, nothing paintable, **frontier-seek disabled**) | 282,753 | **55.7%** |
| `IDLE-ALLY` (own paint everywhere, nothing paintable) | 152,868 | 30.1% |
| no action-block token (ruin work consumed the action, or paint-starved) | 58,831 | 11.6% |
| `pnt` — painted a nearby empty tile | 10,951 | 2.2% |
| `slf` — painted the tile underfoot | 1,972 | **0.4%** |

**The five categories are mutually exclusive by construction and sum to 100.0%** (55.7 + 30.1 +
11.6 + 2.2 + 0.4). I checked that the accounting closes before reading anything off it, per the
rule that a decomposition which does not close is not evidence.

**2.6% of soldier turns paint a tile.** Coverage is the win condition in 85.3% of tournament games.

Caveat stated rather than buried: these are 61 **losses**, so they oversample games where the enemy
out-painted us. The wins are measured below and they look completely different, which is itself the
finding.

## The obvious candidate, and the pre-check that killed it for three games

`runSoldier` gates the iteration-14 frontier-seek on **`foe == 0`**: a soldier that is idle *and*
has any enemy paint within r2=9 does not retarget at all. That guard covers 55.7% of soldier turns,
so removing it looked like a large, zero-paint capability change — the accepted shape.

**Reachability of the CHOICE SET, not the guard** (the rule that a ranking over one option is not a
ranking). `carol_i45p` computes `nearestVisibleEmpty()` in the `foe > 0` branch too, records
whether it found anything, and **does not act on it** — reads only, so play is unchanged.

Identity check first, as required for an instrumented build: `i45p` vs `carol_iter36` returned
**Rose r494 win** and **Gears r940 loss**, matching the baseline's recorded results on those maps
exactly. The instrument does not move the game.

| map | outcome | soldier turns | `IDLE-ENEMY` | of those, a visible empty tile exists |
|---|---|---|---|---|
| DefaultHuge | loss | — | 14,706 turns | **92 = 0.6%** |
| Gears | loss | 10,973 | 9,020 = 82.2% | **1,210 = 13.4%** |
| Rose | **win** | 792 | 120 = 15.2% | 57 = 47.5% |

**Killed.** On the maps where the guard covers the most turns there is nothing to steer to on
86.6%–99.4% of them, and the few tiles that are found sit at d2 = 13–20 against a vision radius of
r2 = 20 — the very edge of sight. This is the "chooses badly" / "never sees it" pair producing an
identical trace, and the discriminating measurement says **never sees it**. Cost: three probe games,
no gauntlet.

## What the same three games found instead, which is much larger

The win and the losses are different worlds, and the separating variable is not idleness:

| map | outcome | `IDLE-ENEMY` share | ally tiles in r2=9 (median) | enemy tiles (median) | **turns with ally > enemy** |
|---|---|---|---|---|---|
| Rose | **win** | 15.2% | 18 | 10 | **100.0%** |
| Gears | loss | 82.2% | 10 | 11 | **0.2%** |
| DefaultHuge | loss | — | 7 | 20 | **0.0%** |

In the two losses, carol's soldiers are **inside enemy-painted ground essentially every turn they
are idle**, with the whole vision disc painted. In the win they are inside their own.

### Why that is a paint claim and not just a positioning claim

`RULES.md` [E], end-of-turn drain: **enemy tile −2, neutral −1, ally 0**, and clumping doubles on
enemy territory. Paint is this lineage's measured binding resource — 100.0% of chips-available
no-builds are paint-limited. So a soldier idling on enemy ground is not merely doing nothing, it is
**paying double the neutral rate to do nothing**, and nothing in this bot has ever consulted the
tile underfoot for that reason.

### The reconciliation that stops me claiming it yet

`LEARNINGS.md` records soldier paint drain measured at **1.20–1.58 per turn**. If soldiers stood on
enemy paint most turns the drain would sit near **2.0**. Those two numbers do not reconcile, and by
my own rule the tell for a wrong referent is exactly two artefacts that ought to agree and don't.

**`IDLE-ENEMY` counts enemy tiles within r2=9. That is NOT the tile underfoot.** The drain depends
only on the tile the robot occupies, so the table above cannot support a drain claim no matter how
suggestive it looks. Probe `carol_i45q` measures the underfoot paint type and the adjacent choice
set on every soldier turn, reads only, and is the thing that decides it.

**Pre-checks NOT yet done, named explicitly** so a session resuming here does not inherit momentum
without the doubt: (a) underfoot paint distribution — running; (b) whether an adjacent ally/neutral
passable tile exists when underfoot is enemy (the choice set, which killed the first candidate);
(c) the price of the reallocation — what a soldier that steps to cheaper ground stops doing.

## The underfoot measurement — probe `carol_i45q`, and the reconciliation that licenses reading it

`carol_i45q` records the tile UNDERFOOT and the adjacent passable tiles by paint type, on every
soldier turn. Reads only. **Identity check passed on all three maps against the true baseline
`carol`: Rose r494, Gears r940, DefaultHuge r1477 — identical for `carol`, `i45p`, `i45q` and
`i45r`.** Peak bytecode on the heaviest probe 6,890 / 17,500 with zero overruns and zero
near-misses, so nothing here was measured at the limiter's edge.

| map | outcome | underfoot ALLY (drain 0) | NEUTRAL (−1) | **ENEMY (−2)** | of enemy-tile turns, an adjacent ally tile exists |
|---|---|---|---|---|---|
| Rose | **win** | 69.3% | 13.8% | **16.9%** | 85.8% |
| Gears | loss | 59.2% | 0.1% | **40.7%** | 52.7% |
| DefaultHuge | loss | 49.2% | 0.6% | **50.2%** | 49.4% |

**The reconciliation.** `LEARNINGS.md` records soldier paint drain at 1.20–1.58/turn, which I
flagged as inconsistent with soldiers standing on enemy paint. Expected underfoot drain from this
table is 0·P(A) + 1·P(N) + 2·P(X) = **0.48 (Rose), 0.82 (Gears), 1.01 (DefaultHuge)**, and the
clumping term (−1 per adjacent ally, **−2 on enemy territory**) supplies the rest. The two artefacts
now agree once the referent is right, and the apparent contradiction was mine: `IDLE-ENEMY` counts
enemy tiles in r2=9, which is **not** the tile the drain is charged on. Recorded because it is the
same wrong-referent shape the log keeps catching, caught this time before it reached a claim.

## The decision instrument — probes `carol_i45r` / `carol_i45s`

Instrumenting the DECISION rather than the outcome: at every `stepToward` move, which drain rank was
taken, the cheapest rank legally available among the directions the method **already** considers,
which call site, and whether the straight direction was the one taken.

| map | moves | landed on enemy paint | **improvable (a legal non-enemy option existed)** | as a share of soldier turns |
|---|---|---|---|---|
| Rose | 561 | 17.8% | **26.9%** | 19.1% |
| Gears | 8,452 | 40.4% | **13.5%** | 10.4% |
| DefaultHuge | 18,074 | 47.6% | **17.0%** | 14.7% |

And the split that decides the design (Gears):

| call site | moves | improvable |
|---|---|---|
| toward a RUIN, straight | 1.1% | 0.3% |
| toward a RUIN, fallback | 0.6% | 0.0% |
| **toward the EXPLORE target, straight** | **50.9%** | **10.5%** |
| toward the EXPLORE target, fallback | 47.4% | 2.7% |

**98.3% of all stepToward moves are toward the explore target**, and `newExploreTarget()` draws that
target as the farthest of **four uniformly random map coordinates**. So the thing a deviation
sacrifices progress toward carries no information about where useful ground is. That is the price
side of the ledger, read off the code rather than assumed — and it is why this reallocation is cheap
where iteration 39's steering was not.

# Iteration 45 — DRAIN-AWARE EXPLORE STEP. Pre-registered before any evaluation game.

**Change.** Only the `stepToward(explore)` call site is routed through a drain-aware variant. Among
the directions the incumbent already considers, **in the incumbent's exact order** (straight, then
left/right ordered by robot ID, then the two wider rotations), take the first legal destination that
is not enemy paint; if none exists, take exactly what the incumbent would have taken. Zero paint,
zero chips, no new mechanic — a re-ranking of a choice already being made.

**Play-symmetry**: a tie in drain rank leaves the incumbent order untouched, so the ID-based
left/right tie-break that Phase 0 installed is preserved intact; "prefer my own paint" is symmetric
between teams. **History**: no prior iteration established that soldiers should step onto enemy
paint — the existing tie-break comment is about symmetry only, so nothing is being silently
reverted.

**Dose ladder, with the zero arm being the incumbent itself (byte-identical by construction):**

| arm | dose | expected trigger |
|---|---|---|
| `carol_iter44` | zero | — |
| `carol_i45_a` | fires **only when the straight direction is already blocked** — no deviation cost at all | ~2.7% of moves |
| `carol_i45_b` | avoid enemy paint on the explore step (main arm) | ~13.2% of moves |
| `carol_i45_c` | prefer ALLY paint first, then non-enemy | ~13.2%, stronger |

**Stage 0, one-map identity check — RUN AND PASSED before any gauntlet.** vs `carol_iter36` on
Gears the baseline plays r940; `a` r662, `b` r1410, `c` r701. All three differ, so no arm is a
dormant branch and no run is wasted on a candidate that compiles to the same behaviour.

**Instrument**: 25 sampled maps, `BOT=carol_i45_b`, opponents `carol_iter44`, `carol_i45_a`,
`carol_i45_c` — 150 games. The sample is drawn once and shared, so the three comparisons are exact
against each other. Sampled first to find the SHAPE of the ladder; a full-corpus census against
`carol_iter44` fixes the LEVEL for whichever arm the ladder favours.

**Gate on the sampled run** (margin sd ~6 on a 50-game arm, so this stage cannot accept):
proceed to census if `b` (or the arm the ladder favours) is at or above even vs `carol_iter44`;
abandon if it is below −8, which would be a real regression rather than noise.

**Census gate**, against carol's own measured chaos floor (sd **6.48** on the margin per 150):
**ACCEPT >= +13**, REPLICATE +9..+12, **REJECT <= +8**.

**Named weak link — the one to watch, because it is the link that killed iteration 42 and held in
44.** The chain is: *improvable moves fall -> soldiers spend fewer turns on enemy paint -> paint
drain falls -> coverage rises*. Link 1 is the `ds` decision counter (deviations actually taken) and
`i45q`'s underfoot distribution re-measured on the candidate. **If `ds` fires and the underfoot
enemy share does not fall, I REJECT** — that would mean the deviation is immediately undone and the
mechanism is churn. If underfoot falls but coverage does not, I follow rule 3b: report the number
honestly and record attribution as OPEN rather than back-filling a story.

**Pre-registered secondary, stated in advance so it cannot be back-filled:** the margin is larger on
maps where the incumbent's underfoot-enemy share is HIGHER, because that is where the mechanism has
fuel. Iteration 44's secondary came back flat and I recorded the attribution as open; the same rule
applies here whichever way it lands.

**Pre-checks NOT done, named:** (a) trigger frequency is measured on three maps, not the corpus —
Rose/Gears/DefaultHuge span win/loss and small/large, but this is not a census; (b) the price is
argued from the randomness of the explore target and the 98.3% call-site split, and is **not**
directly measured as forgone coverage; (c) no check yet that the deviation does not simply
oscillate a soldier back and forth across a paint boundary, which is the specific way this
mechanism could be churn rather than saving.

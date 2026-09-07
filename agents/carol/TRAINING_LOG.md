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

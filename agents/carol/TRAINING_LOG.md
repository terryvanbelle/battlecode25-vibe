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

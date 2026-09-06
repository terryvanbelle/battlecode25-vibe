# Bob — TRAINING_LOG.md (append-only)

Conventions (**superseded 2026-09-06, see below**): dev map set `DEV12` =
DefaultSmall DefaultMedium DefaultLarge DefaultHuge Circuit FourCorners Gears maze
Money Oasis Thirds gridworld (12 maps, x2 sides).
Full evaluation = gauntlet over current peer pool + head-to-head vs last
accepted snapshot.

**METHODOLOGY CHANGE 2026-09-06 (coordinator, effective from run 20260906-202139+1).**
`tools/gauntlet.sh` with `MAPS` unset now draws a FRESH RANDOM sample of 25 maps
from the 75 in `tools/bc25-maps.txt` (50 games/opponent). DEV12 is retired as a
standing list: a fixed hand-picked map set is an overfitting surface, and my
accepted iterations would drift toward those 12 maps. Consequences for reading
this log:

- **Win rates recorded BEFORE this line (iterations 0-3) are on DEV12, 24 games.
  Win rates AFTER it are on a resampled 25-map draw, 50 games. They are not the
  same instrument — never compare the raw percentages across that boundary.**
- Within a run the sample is shared by all opponents, so the head-to-head accept
  gate (a within-run comparison) is unaffected and stays valid.
- When run-to-run comparability is actually needed — regression vs an old
  snapshot, an ablation arm, or re-running a map to trace it — pin the sample
  with `MAPS="$(cat gauntlet/<run-id>/maps.txt)"`.
- Upside for my specific problem: my recurring finding is that near-mirror
  matchups split by side on most maps and that swept-map counts are the sturdier
  signal. 25 maps per run gives roughly double the swept-map evidence per run,
  and the binomial noise floor on 50 games is ~3.5 games (~7pts), so a
  swept-map/win-rate move now has to clear a computable bar. Fixed old-bot roster (per updated algorithm 2026-09-06): every 5th
accepted snapshot (iter1, iter5, iter10, ...), run every ~5 accepted iterations.

---

## Phase 0 (2026-09-06)

**Spec + engine ground truth** → `RULES.md`. Sources: official specs.pdf V3.1.0 +
reflection dump of battlecode25-java-3.1.0.jar + engine source (GitHub). Key facts:

- Win = paint >70% of paintable tiles (or annihilation). Tiebreak: painted area,
  towers, money, paint sum, robots. 2000 rounds.
- Units cannot damage units — only towers take attack damage. Unit-v-unit combat is
  paint attrition (moppers) + tower fire. Soldier/splasher/mopper: 250/150/50 HP.
- Only splashers (r²≤2 of target) and moppers remove enemy paint. Soldiers cannot.
- Paint = per-robot ammo + timer: territory penalties/turn (neutral −1, enemy −2,
  +1/adjacent ally, doubled in enemy territory; moppers pay 2× territory part),
  <50% stash → up to +100% cooldowns, 0 paint → frozen, −20 HP/turn.
- Towers: start 2 (paint L2 + money L2, both 500 paint). Money L2 = 30 chips/turn.
  Max 25. Tower AoE = attack(null), hits ALL enemies in r²9 (defense 16) for 10-30 +
  single-block 20-60. Defense tower r²16 outranges soldier r²9.
- SRP: 200 chips, +3 resources/turn per mining tower per active SRP after 50
  undisturbed rounds — scales multiplicatively with tower count.
- Comms: robot↔tower only, needs ally-paint connectivity, r²20; tower↔tower
  broadcast r²80. 1 msg/turn robots, 20 towers. Markers = shared map blackboard.
- Bytecode: 17500 robots / 20000 towers. Exceptions cost 500. Team wall-clock cap
  20 min/match (auto-resign!).
- Patterns decoded in RULES.md (resource/paint/money/defense 5x5 bitmasks).

**Determinism**: VERIFIED. Same match run 4x: identical outcome (win r187), and
replay files are BYTE-IDENTICAL for identical games → arm-to-arm identity checks can
`cmp` replays directly. Caveat discovered: the FIRST run after a source change once
produced a result consistent with a stale build (example-copy behavior). Rule: never
trust a single first-run result right after syncing new source; gauntlet.sh builds
before running and is safe.

**Bytecode monitoring**: wired into v0 (RobotPlayer): confirmed-overrun counter
(round changed across own turn body) + Clock.getBytecodeNum() vs limit + max,
surfaced in every indicator string. Checked on every evaluation.

**Symmetry audit stance**: v0 tie-breaks use per-robot rng (seeded by id) for
direction iteration starts and wander; tower-type choice keyed on (ruin.x+ruin.y)
parity (map-symmetric). Mirror-match check scheduled once lineage has 2+ iterations.

**Infrastructure**: vm-match.sh + gauntlet.sh (shared tools) work; replays byte-
comparable; match logs pulled to logs/. Replay-to-text parser deferred until traces
need it (match stdout + indicators may suffice; revisit).

---

## Iteration 0 (2026-09-06) — baseline v0 — ACCEPTED (baseline)

Bot: package `bob` v0. Towers: AoE+focused attack, soldier-heavy spawn (S,S,SPL@r>60,
S,M cycle), 1200-chip reserve after r30. Soldiers: nearest-free-ruin capture
(money/paint tower by ruin parity), refill <50 paint, shoot adjacent enemy towers,
paint-under-self, persistent wander. Moppers: adjacent-robot mop, swing if ≥2 in
zone, mop enemy tiles, seek enemy paint. Splashers: cluster-scored splash ≥5 value.
Nav: greedy + slide, avoids enemy paint, stuck-kick.

Snapshot: src/bob_iter0. Evaluation: gauntlet vs examplefuncsplayer on DEV12 (24
games) — results below when complete.

Result: 24/24 (100%) vs examplefuncsplayer on DEV12, all 12 maps swept. 0 exceptions.
Bytecode (mirror DefaultMedium trace): towers ~550, soldiers ~1k, moppers ~1.9k,
splashers ~8.3k max of 17500; ov=0 everywhere. examplefuncsplayer classified
BENCHMARK-beaten (100% x2 would retire it; keep as occasional sanity check only).
Baseline accepted; bob_iter0 is the first h2h gate.

---

## Iteration 1 (2026-09-06) — soldier idle-action painting — ACCEPTED

Target (structural/degeneracy): mirror needed 1757 rounds to reach 70% paint on
DefaultMedium — soldiers idle their action on most turns (only painted own tile when
non-ally, or pattern tiles). Absolute stall signal, no opponent needed.

Hypothesis: using idle actions to paint the nearest EMPTY tile within action r²9
(own tile first; skip marked tiles to not fight patterns) raises team paint rate →
faster 70% and h2h win. Pre-registered: (1) h2h vs bob_iter0 DEV12 >50% (accept
gate), (2) median win-round vs examplefuncsplayer drops vs iteration-0 run.

Change: Soldier.paintSomething() — own tile if non-ally else nearest empty passable
unmarked tile in r²9. PAINT_FLOOR=15 unchanged.

Evaluation (gauntlet 20260906-183531): **16/24 (66.7%) vs bob_iter0**, swept-win
4/12, swept-loss 0, split 8. Losses scattered both sides (5 of 8 at r2000
tiebreak) — no one-directional regression. ACCEPT. Snapshot src/bob_iter1.
Secondary metric (round-speed vs examplefuncsplayer) run follows.

Learning: splits-by-side on 8/12 maps in near-mirror matchups — side asymmetry is
large relative to this feature's edge; swept-map counts are the sturdier signal.

Iter1 secondary metric (gauntlet 20260906-184306 vs examplefuncsplayer, 24/24):
win rounds dropped on most maps (Money 464→209, FourCorners 427→304, DefaultLarge
469→319) — consistent with higher paint rate. WATCH: DefaultHuge/Gears/maze slid
from decisive (r991–1654) to r2000-tiebreak wins — on big/corridor maps idle
painting may thin soldiers' stashes (more refills, slower deep push). CAVEAT: this
run overlapped the iter2 candidate rebuild on the VM (shared build/classes) — late
games may have run iter2 code. RULE (infrastructure): never run two gauntlets from
the same workspace concurrently; results.csv rows after a rebuild are poisoned.

---

## Iteration 2 (2026-09-06) — paint-starved mopper fallback at non-regen towers — REJECTED

Target: traced loss iter1-vs-iter0 Thirds botA (replays/iter01_bobiter0_Thirds_A_LOSS):
A built 1 tower vs B's 15; A coverage DECLINED 195→137 per-mil; 14k chips unspent.
Root mechanism: money towers never regen paint → after 2 soldier spawns their stash
is dead; chips gate nothing, PAINT gates everything.

Attempt 1 (rejected at mechanism stage): any tower spawns mopper when stash <
soldier cost & chips ≥ reserve+800. Backfired: paint towers' 10/turn regen hits 100
→ mopper spawns preempt soldiers 2:1 → paint output collapsed, Thirds-A loss got
WORSE (r755 vs r1199), money pinned at 1850. Learning: trigger-frequency pre-check
failure — "stash < 200" is the steady state at paint towers.

Attempt 2 (current): fallback only at towers with paintPerTurn==0 (their stash IS
dead weight) and chips ≥ 1500. Mechanism check Thirds-A vs iter0: engaged, A ahead
at r300 (214 vs 193 cov), still lost r1715 — B's Thirds-side economy (76k money,
15 towers) dwarfs the fix; class-2 proceed (side asymmetry documented in iter1).

ALSO OBSERVED (both lineages): 26k–76k chips unspent by late game; nobody upgrades
towers or builds SRPs. Spending idle chips (upgrades/SRPs/defense) is likely the
next structural win. → backlog.

Pre-registered: h2h vs bob_iter1 DEV12 >50% gate; no swept-loss regression.

**RESULT (gauntlet 20260906-184918): 12/24 = exactly 50.0% — REJECTED.**
Swept-win 1/12, swept-loss 1, split-by-side 10. The gate was a strict majority
(>50%) and 12/24 is not one; per measurement doctrine #5 a ~50% h2h is a near
miss, not an accept, absent a separate mechanistic argument, and there is none
here — the mechanism engaged (verified) and bought nothing. Compare iter1's
accept: 16/24 with swept-win 4 / swept-loss 0. This is a coin flip by contrast,
and the split-by-side count rose 8 → 10, i.e. the run got *more* side-dominated,
not less. Reverted `src/bob/Tower.java` fully; `bob_iter1` remains the h2h gate.

Functional-area status: **tower spawn composition / paint-starvation — CLOSED
(2 consecutive rejects).** Both attempts assumed converting a dead paint stash
into a unit was the win. Attempt 1 died on trigger frequency, attempt 2 on a
null effect. The next attempt must leave this area (algorithm §1,
MaxConsecutiveRejects). Ledger entry below.

---

## Closed-directions ledger

| direction | killed by |
|---|---|
| Tower spawns a mopper when its paint stash is below soldier cost (any tower) | iter2 attempt 1: "stash < 200" is the *steady state* at paint towers, so the fallback preempted soldiers 2:1; Thirds-A loss got worse (r755 vs r1199) |
| Same, restricted to towers with `paintPerTurn == 0` and chips ≥ 1500 | iter2 attempt 2: h2h vs iter1 exactly 12/24 (50.0%), swept 1–1. Mechanism engaged, effect nil |

---

## Structural trace (2026-09-06) — the real degeneracy

Ran `bob-tools/dump-replay.sh` over the iter2 losses. `gridworld` botA, per 50
rounds (`round, covA, covB, moneyA, moneyB, srpA, srpB, died, turns`):

```
 50, 226,205,    440,  1410, 0,0,0, 24
150, 488,433,   2040,  6100, 0,0,0, 54      <-- coverage PEAK
200, 498,445,  11040, 11890, 0,0,0, 56      <-- robot-count peak
500, 463,486,  63690, 64540, 0,0,0, 48
1000,469,493, 151440,160590, 0,0,0, 48
2000,424,542, 326940,357090, 0,0,0, 48
```

Three absolute degeneracy signals, no opponent needed:

1. **327,000 chips unspent at r2000** (both teams). Chips pass 8k by ~r180 and
   then grow ~175/turn forever. Chips are a dead resource for this bot.
2. **Coverage peaks at round 150 (48.8%) and then DECLINES** to ~42–45%. The
   win condition is 70%. Everything after r150 is a stall; the last tower is
   built at r167 and nothing changes again for 1800 rounds.
3. **0 SRPs, ever**, on either side.

**Engine probe (authoritative, `javap -c` on battlecode25-java-3.1.0.jar) —
three facts that explain the stall:**

- `InternalRobot.<init>` sets `paintAmount = 0`. A newly completed tower spawns
  with **zero paint**. Only the two starting towers get INITIAL_TOWER_PAINT_AMOUNT.
- `MONEY` towers have `paintPerTurn == 0`. Combined with the above: **every money
  tower we build is a permanently sterile spawn point** — it can never accumulate
  the 200 paint a soldier costs, and it produces the one resource we already have
  327k of. `Soldier.towerTypeFor` splits ruins 50/50 by parity, so roughly half
  our captured ruins are dead weight.
- `InternalRobot.processBeginningOfRound`:
  `if (paintPerTurn != 0) addPaint(paintPerTurn + gameWorld.extraResourcesFromPatterns(team))`
  and `extraResourcesFromPatterns = numResourcePatterns * 3`. So **an SRP gives
  +3 PAINT/turn to every paint tower**, not just +3 chips to money towers. With
  P paint towers and N SRPs that is +3·N·P paint/turn for 200 chips each.
- `assertCanUpgradeTower` requires only: target within r²≤2, ally tower,
  `canUpgradeType()`, chips ≥ `getNextLevel().moneyCost`. **No action check, no
  cooldown added** — so a tower can upgrade *itself* (distance 0) on any turn,
  for free, alongside attacking and spawning. `InternalRobot.upgradeTower` keeps
  the paint stash and carries missing-HP across (+500 max HP).

Conclusion: paint income is the single binding constraint on this bot, chips are
free, and the engine offers three untouched paint-income multipliers (upgrade
paint towers, build paint towers instead of money towers, SRPs). That is the
iteration queue for 3/4/5, one at a time.

---

## Iteration 3 (2026-09-06) — idle-chip tower self-upgrade — ACCEPTED

Target: structural track / absolute degeneracy #1 above (327k unspent chips,
coverage plateau from r150). New area — leaves the closed spawn-composition
thread as required.

Hypothesis: converting surplus chips into tower levels raises paint income
(paint tower 5→10→15/turn) and so raises unit production past the r150 plateau,
which raises coverage. Chips are non-binding, so the spend is ~free.

Change (isolated, `src/bob/Tower.java`): a tower self-upgrades when
`chips >= getNextLevel().moneyCost + UPGRADE_RESERVE` (UPGRADE_RESERVE = 4000,
i.e. four tower-builds still in hand). Timeline marker "upgrade" on each.

Pre-checks: **Reachability** — chips exceed 5000+4000 by ~r180 in every traced
game, and 100k+ by r1000. Passes emphatically. **Trigger frequency** — fires
once per tower per level, ~20 times/game, saturating by ~r400; it cannot fire
often enough to crowd anything out. **History** — no prior iteration
established the un-upgraded behavior; it was simply never coded.

Mechanism verification (single match, gridworld, bob vs bob_iter1, side A —
the same map/side that lost in run 184918): **WON r2000 on painted-area
tiebreak, 534 vs 407 per-mil** (baseline: LOSS, 424 vs 542). 20 upgrade markers
for our team. Chips dip early as designed (r400: 8,070 vs baseline 46,140).
Class 1 (won) — proceed.

Pre-registered accept criteria:
1. **h2h vs bob_iter1 on DEV12 > 50%** (i.e. ≥13/24) — accept gate.
2. swept-win > swept-loss (no one-directional regression).
3. Secondary/mechanistic: r2000 coverage in the traced win exceeds baseline.

Note for interpretation: chips still reach 551k by r2000 in the traced game
(money towers at L3 mine 40/turn), so this iteration *does not* fix the dead-chip
problem — it only takes the one cheap sink the engine offers. Degeneracy #1
stays open for iterations 4–5 (paint-tower bias, SRPs).

**RESULT (gauntlet 20260906-202139, DEV12): 21/24 = 87.5% vs bob_iter1 — ACCEPTED.**

| | iter1 accept (vs iter0) | iter2 reject (vs iter1) | **iter3 (vs iter1)** |
|---|---|---|---|
| h2h | 16/24 (66.7%) | 12/24 (50.0%) | **21/24 (87.5%)** |
| swept-win | 4/12 | 1/12 | **9/12** |
| swept-loss | 0 | 1 | **0** |
| split-by-side | 8 | 10 | **3** |

All three pre-registered criteria met. The diff shape is the strongest evidence
here and it is one-directional: Circuit, FourCorners, DefaultHuge, Gears and
DefaultSmall all went from split-by-side to swept wins. **The split-by-side count
collapsed 10 → 3** — games stopped being decided by which spawn we got, which is
exactly what a real capability gain (rather than churn) looks like against the
side-asymmetry finding logged in iteration 1. Win rounds also fell sharply
(DefaultMedium A 1592→510, DefaultLarge A 1854→716, Money 2000→897).

Remaining losses: DefaultLarge B r1879, maze B r2000, Thirds B r2000 — all side B,
all late/tiebreak, none a sweep against us.

Snapshot: `src/bob_iter3` (there is no `bob_iter2`; iteration 2 was rejected).
`bob_iter3` is now the h2h gate. Representative replay archived:
`replays/iter03_bobiter1_gridworld_A_WIN.bc25` (the mechanism-verification game —
the exact map/side that lost in run 184918, won here 534 vs 407 per-mil).

Accepted-iteration count: 3 (iter0, iter1, iter3). Fixed old-bot roster run
(iter1 + iter5 …) is due at the next accept-count multiple of 5 — flagged so it
is not treated as "later".

**Learning (durable).** The winner's-profile line in TRAINING_ALGORITHM.md —
*capability preserved at zero marginal cost: standing defenses, spending idle
resources, removing pure waste* — paid out on the first try here, and it beat two
consecutive clever-mechanism attempts (iteration 2) by 37 points. The generalisable
move was not the idea but the instrument: dumping raw per-round replay counters
(`bob-tools/dump-replay.sh`) and reading them for **absolute degeneracy** rather
than for an opponent-relative deficit. "327k chips unspent" and "coverage peaks at
r150 and then declines" need no opponent to be obviously wrong, and both had been
sitting in every replay since iteration 0. Do the counter dump before theorising.

---

## Iteration 4 (2026-09-06) — paint-tower bias in ruin capture — REJECTED

Target: structural degeneracy #1 again (chips still dead: 551k at r2000 *after*
iteration 3 upgrades), attacked from the other side — stop manufacturing the dead
resource. New sub-target, not a refinement of iteration 3.

Evidence: `Soldier.towerTypeFor` picks money vs paint tower by `(ruin.x+ruin.y)&1`,
so ~half of every ruin we capture becomes a money tower. Engine-verified, a money
tower has `paintPerTurn == 0` and a newly completed tower starts at
`paintAmount == 0`, so **a money tower we build is a permanently sterile spawn
point** — it can never accumulate the 200 paint a soldier costs — and it mines the
resource we already pile 551k of. Meanwhile paint income is the binding constraint
on unit production and therefore on coverage.

Hypothesis: building paint towers instead of money towers after the early
expansion phase raises paint income roughly in proportion to the paint-tower
count, and so raises coverage and the h2h.

Change (isolated, one expression in `Soldier.towerTypeFor`): money tower only
while `roundNum <= MONEY_TOWER_UNTIL` (dose parameter, 100), paint tower after.
Round number is a shared, exactly team-symmetric signal — strictly better on the
symmetry audit than the current absolute-coordinate parity, which is not
preserved under the map's rotation/reflection.

Pre-checks: **Reachability** — towers are built at r18/39/58/85/100/105/129/139/167
in the traced game, so a r100 cut-off splits them ~4 money / ~5 paint; the branch
is taken every game. **Trigger frequency** — fires once per ruin captured, ~9
times/game. **History** — the parity rule was never justified by measurement; it
was an arbitrary iteration-0 default ("mix money and paint towers"), so this
supersedes nothing that evidence established. **Risk to check in the trace** —
with fewer money towers, chips may stop being free (iteration 3's upgrades want
7,500/tower); if chips go to zero the dose is too aggressive and MONEY_TOWER_UNTIL
should rise. That is the dose sweep if this comes back a near miss.

Pre-registered accept criteria (first run under the NEW resampled 25-map default):
1. **h2h vs bob_iter3 > 50%** (≥26/50) — accept gate.
2. swept-win > swept-loss.
3. Mechanistic: team chips at r2000 in a traced game are materially below the
   551k baseline (i.e. the change actually removed money income), AND r2000
   coverage is not lower. If chips collapse toward 0 *and* coverage drops, the
   dose is too aggressive — refine rather than reject.

**Implementation correction made before running** (worth recording, it was nearly
a self-inflicted bug). The first draft keyed the choice on `roundNum <= 100`.
That is unsafe: `workOnRuin` marks the ruin's 5x5 with one type's pattern and then
refuses to re-mark (its probe is "is any tile marked?"), so a ruin whose type
changed between marking and completion can never be completed — a soldier would
sit on it forever. **The tower type must be a pure function of the ruin, never of
time.** Shipped instead as a stable mask on the ruin coordinates,
`((ruin.x + ruin.y) & MONEY_SHARE) == 0`, with MONEY_SHARE as the dose parameter:
1 = one ruin in two is money (iterations 0-3, the zero arm), 3 = one in four
(this arm), larger = fewer still.

Mechanism verification (single match, gridworld, bob vs bob_iter3, side A):
**WON AT ROUND 804 BY MAJORITY_PAINTED — 70.2% coverage.** This is the lineage's
first ever win by the actual win condition; every prior game in every prior run
ended at the r2000 area tiebreak around 45-55%. Per-round trace:

```
round  covA  covB   moneyA   moneyB   turns
  250   532   432     5760     5950      64
  500   564   394     6010    24770      74
  750   698   268     6220   100290      83
  804   702   264     7620   114210      85
```

All three pre-registered mechanistic predictions hit at once: our chips stop
piling up (7.6k vs the baseline's 114k on the same round, i.e. income is now
fully consumed by iteration 3's upgrades instead of dying in the treasury),
coverage rises monotonically with no r150 plateau, and the robot count reaches 85
against the ~48 that every earlier trace showed. Class 1 (won) — proceed to the
full run.

---

## Standing audit items (not yet measured)

- **`Nav.navTo` has a fixed handedness.** Its candidate list is
  `{d, d.rotateLeft(), d.rotateRight(), d.rotateLeft().rotateLeft(), …}` — left is
  always tried before right. This is exactly the fixed absolute-order tie-break
  TRAINING_ALGORITHM.md §7 names as the largest bug class in both prior projects:
  it interacts with map geometry to favour one side. It is a plausible contributor
  to the persistent split-by-side result, and it is untested. Mirror-match (bot vs
  byte-identical copy, both sides, all maps) is the instrument. Note the caution
  recorded there: a consistent arbitrary preference can be supplying real formation
  cohesion, so randomising it can be a net regression — measure, don't assume.
- **Comms are entirely unused.** An API sweep against `src/bob/` (algorithm phase
  0.2) shows `sendMessage`, `broadcastMessage`, `readMessages`, `canSendMessage`
  and `canBroadcastMessage` are never called, along with the whole marker API and,
  until iteration 5, the whole SRP API. Symmetry inference and target
  deconfliction both live here.
- **Our own splashers can break our own SRPs.** `Splasher.run` scores EMPTY tiles
  and splashes an r²≤4 AoE that repaints in primary; a finished SRP's 25 tiles must
  keep their exact primary/secondary colours or the engine resets the pattern to
  neutral and restarts its 50-round activation clock. Watch `srpA` in the replay
  dump: if SRPs are built but the count keeps falling back, this is the cause.



### Iteration 4 trace — THE RESERVE DEAD BAND (the real find of this run)

Run 20260906-203014 (first under the resampled 25-map default) went badly on maps
this lineage had never seen: hovering around 47-50% against bob_iter3, with swept
losses on starburst, Racetrack and Snowglobe. Dumped both swept losses.

`starburst` bot=A (us), per 100 rounds:
```
round covA covB moneyA moneyB
  100  321  414   1250    500
  300  382  602   1350   2350
  500  320  646   1300   1900
  526  280  700    780   2800   <- B wins by MAJORITY_PAINTED
```
`Snowglobe` bot=A (us), per 75 rounds:
```
   75  191  240    750   1360
  225  273  489   1200   1760
  375  302  667   1350   6450
  453  267  700   1290   5040   <- B wins by MAJORITY_PAINTED
```

**Our chips sat pinned between 1200 and 1350 for the entire game, on both maps.**
That number is `Tower.reserve` itself (1200). A soldier costs 250, so spawning
required 1450 chips and simply never happened — for hundreds of consecutive
rounds, on every tower we owned. Coverage decayed (428 → 280, 302 → 267) because
nothing replaced the units that died, while the opponent walked to 70%.

This is the "resource pinned in a dead band" signal TRAINING_ALGORITHM.md §1 names
as preferable to any opponent-relative comparison, and it needed no opponent to be
obviously wrong. Two things about it are worth recording:

1. **The reserve was protecting an expansion that had already finished.** Its
   purpose is to keep 1,000 chips free so a soldier can complete a tower pattern
   the instant it is ready. On a ruin-poor map the last ruin is captured early;
   after that the 1,200 chips protect nothing whatsoever while blocking all unit
   production. A fixed constant converted a modest income shortfall into
   *permanently zero* output.
2. **This bug is in bob_iter3 as well** — it is not something iteration 4
   introduced. Iteration 4's paint-tower bias lowered chip income enough to push
   many more maps into the band, which is how it became visible. It had been
   invisible for four iterations because every map tested until today was
   ruin-rich enough that chips ran away to six figures.

Refinement (iteration 4b), self-calibrating per the algorithm's stated preference
over fixed constants: hold the expansion reserve only while the team's tower count
is still growing. `rc.getNumberTowers()` is team-global and engine-verified to
return our own team's count, so every tower agrees without needing comms; if the
count has not moved for `EXPANSION_IDLE` = 200 rounds, there is nothing to reserve
for and the reserve drops to 0. A tower being destroyed also re-arms it, which is
right — a destroyed tower frees its ruin for rebuilding.

Next run is designed to separate the two effects on ONE shared map sample:
`bob` (paint bias 1-in-4 + reserve fix) against `bob_i4a` (the paint bias alone,
frozen byte-identical to what ran here — so this is an exact isolation of the
reserve fix in the regime where it is actually reachable), `bob_iter3` (the accept
gate, neither change), and the frozen roster `bob_iter0` + `bob_iter1` for the
absolute-strength chart. Reachability note for honesty: the reserve fix is nearly
dead code under iter3's own economy, where chips run to 551k and the band is never
occupied — it is reachable *because of* the paint bias, so the two are a genuine
interaction and any accept here is for the pair, not for either alone.


### Iteration 4 RESULT — REJECTED

**Run 20260906-203014: 22/50 = 44.0% vs bob_iter3. swept-win 6/25, swept-loss 9,
split-by-side 10.** Both pre-registered criteria failed: the h2h is below 50%, and
swept-loss exceeds swept-win. The deficit is 6 points below the gate against a
~7pt binomial noise floor on 50 games, but the swept-map asymmetry (9 maps lost
from BOTH sides against 6 won from both) is the sturdier signal and it is
one-directional. REJECT. Paint bias reverted; `src/bob_i4a` deleted.

**What the rejection bought** (a rejection that converts a weakly-founded belief
into a firmly-founded one has paid for its run):

The premise was verified and the conclusion was still wrong, which is worth
stating precisely. Money towers really are permanently sterile spawn points — that
is engine fact, not inference. What the hypothesis missed is that **iteration 3
turned chips INTO paint income**: an upgrade buys +5 paint/turn for 2,500 chips.
Once that conversion exists, money towers are no longer producing a dead resource,
they are producing the feedstock for paint income, and starving the treasury
starves the upgrades. Rough arithmetic on the traced games: iter3 runs ~5 paint
towers upgraded to L3 for 5 x 15 = 75 paint/turn; the 1-in-4 arm runs ~8 paint
towers that it can never afford to upgrade, for 8 x 5 = 40 paint/turn. **More paint
towers, less paint.**

This is the algorithm's own warning about supersession, inverted: I did not
contradict a previous iteration's evidence, I failed to notice that a previous
iteration had *changed the economics the new hypothesis depended on*. Iteration 3
was two hours old. Ledger entry added.

Note the gridworld result stands and is not contradicted: the 1-in-4 arm won there
at r804 by MAJORITY_PAINTED. gridworld is ruin-rich, so it could afford both more
paint towers and their upgrades. The arm is bad on ruin-poor maps, which the
resampled 25-map draw contains far more of than DEV12 did — an early vindication
of the coordinator's map-resampling change, since DEV12 would have hidden this.

Closed-directions ledger, new entry:

| direction | killed by |
|---|---|
| Bias ruin capture toward paint towers (1 in 4 money instead of 1 in 2) | iter4: 22/50 (44%) vs bob_iter3, swept-loss 9 > swept-win 6. Chips buy paint income back through iteration 3's upgrades, so starving money starves upgrades and nets less paint. Re-open only with evidence that changes that arithmetic — e.g. if a cheaper paint-income source (SRPs) makes upgrades non-critical |

---

## Iteration 5 (2026-09-06) — self-calibrating expansion reserve — running

Target: the reserve dead band traced above. Carried forward from iteration 4 as an
independent change, with the rejected paint bias stripped out, so the accept test
is a single isolated change against bob_iter3.

Hypothesis: `Tower.reserve` is a fixed 1,200 chips held back for tower completion.
When income is modest the treasury pins at that value and unit production stops
entirely and permanently — traced on two maps for hundreds of consecutive rounds.
Holding the reserve only while the team is actually still expanding removes a pure
waste with no capability cost.

Change (isolated, `src/bob/Tower.java`): track `rc.getNumberTowers()` (team-scoped,
engine-verified); if it has not changed for `EXPANSION_IDLE` = 200 rounds, set the
reserve to 0. A destroyed tower re-arms it, which is correct — it frees a ruin.

Reachability caveat, stated up front for honesty: under bob_iter3's own economy
chips run to 551k and the band is rarely occupied, so this change may be close to
a no-op on ruin-rich maps. It was clearly reachable under iteration 4's economy.
The resampled map draw contains many ruin-poor maps, which is where it should
bite. If it comes back a clean no-op rather than a regression, that is a
"mechanistically correct but upstream state never produces the situation" result
and it should be kept in mind for when a later iteration changes the economy again
— not discarded.

Evaluation run 20260906-2136ish, 15 maps x 2 sides, four opponents on one shared
sample: `bob_iter3` (accept gate), plus the frozen roster `bob_iter0`, `bob_iter1`
and `examplefuncsplayer` for the absolute-strength chart.

Pre-registered accept criteria:
1. **h2h vs bob_iter3 > 50%** (≥16/30) — accept gate.
2. swept-win ≥ swept-loss.
3. Mechanistic: on a ruin-poor map from the sample, team chips no longer sit
   pinned at 1200-1350 for the whole game.

---

## Iteration 6 (2026-09-06) — Special Resource Patterns — prepared, gated on iteration 5

Target: the third and largest untouched paint-income multiplier found in the
iteration-3 engine probe. Whole game mechanic, never used by this bot (confirmed
by the API sweep: `getResourcePattern`, `canMarkResourcePattern`,
`markResourcePattern`, `canCompleteResourcePattern`, `completeResourcePattern`
are all uncalled), and `srpA`/`srpB` are 0 in every replay ever dumped, on both
sides.

Engine ground truth (`InternalRobot.processBeginningOfRound`):
```
if (type.paintPerTurn != 0) addPaint(type.paintPerTurn + gameWorld.extraResourcesFromPatterns(team));
if (type.moneyPerTurn != 0) teamInfo.addMoney(team, type.moneyPerTurn + gameWorld.extraResourcesFromPatterns(team));
```
with `extraResourcesFromPatterns(team) = 3 * numResourcePatterns(team)`. So an SRP
is **+3 paint/turn on every allied PAINT tower**, not merely +3 chips on money
towers — the spec's phrase "mining towers" hides that. With P paint towers and N
SRPs the paint income is P·(base + 3N).

Chip efficiency vs the accepted iteration 3 mechanism: an SRP costs 200 chips for
+3 paint/turn × P towers; a tower upgrade costs 2500 chips for +5 paint/turn × 1
tower. At P ≈ 8 the SRP is ~30× better per chip, which is why `SRP_MIN_CHIPS` is
set at 500 — below iteration 3's upgrade threshold, so SRPs win the race for chips.
This matters now in a way it would not have before iteration 4: chips stopped being
free (7.6k at r804 vs 114k for iter3), so the two mechanisms genuinely compete.

Implementation (in `Soldier`, isolated; already written and compile-verified on
the VM in an isolated directory that does not touch the workspace build):
an idle soldier — one with no ruin to capture — marks a resource pattern on its
own square, paints the 25 tiles to match the marks it just wrote, and completes it.
Standing on the centre puts all 25 tiles inside the soldier's own r²≤9 action
radius, so it never has to move while building.
`canMarkResourcePattern` is left to enforce the geometry (centre ≥2 from every
edge, all 25 tiles paintable) rather than re-deriving it. `srpSiteSafe` adds the
three checks the engine does not: no enemy paint (a soldier cannot overwrite it,
so the site could never be completed), no overlap with a finished SRP, and no tile
already marked (which is what prevents two adjacent soldiers from marking
contradictory overlapping patterns and deadlocking each other).

Pre-checks: **Reachability** — soldiers go idle as soon as the nearby ruins are
all captured, which the traces show happens by ~r170; chips exceed 500 from ~r150.
**Trigger frequency** — bounded by idle soldiers and by the no-marked-tile rule.
**Generality** — this is a whole-mechanic gap, not a fix aimed at one game.
**Known interaction to watch** — our own splashers repaint in primary over an r²≤4
AoE and would reset any SRP they clip (the engine re-checks pattern integrity every
round and restarts the 50-round activation clock on any mismatch). Instrument: the
`srpA` column of the replay dump. SRPs built but repeatedly falling back to 0
active means the splasher is eating them, and the fix is a splasher exclusion, not
abandoning the mechanic.

Pre-registered accept criteria:
1. **h2h vs the newest accepted snapshot > 50%** — accept gate.
2. swept-win > swept-loss.
3. Mechanistic (checked first, on one match): `srpA` reaches ≥3 and stays there,
   and the win round drops versus the same map/side baseline.


---

## Backlog / next structural targets (evidence, not speculation)

**The endgame is zero-sum and only two unit types can move the line.** In every
long game the whole map ends up painted by somebody: gridworld iter3-vs-iter1
finished 424 + 542 = 966 per-mil, and the iteration-4 gridworld win finished
702 + 264 = 966. There is no neutral ground left to claim after roughly round 200.
Engine fact: **soldiers cannot overwrite enemy paint at all.** Only splashers (and
only within r²≤2 of the splash centre) and moppers can. So once the map is
saturated, three fifths of our production — the soldiers — can no longer affect
the score at all, and the entire remaining contest runs through the 1 splasher +
1 mopper we build per 5 units (`Tower.spawned % 5`).

That ratio has never been measured; it is an iteration-0 default. It is a clean
dose parameter with an obvious zero arm, and the trigger is universal rather than
situational. Candidate for iteration 7, after SRPs — and note it interacts with
SRPs in the right direction, since more paint income makes the more expensive
splashers (300 paint, 400 chips) affordable.

Watch the confound flagged in TRAINING_ALGORITHM.md's deep regularities before
spending a run on it: "metrics that improve without converting to wins" and
"survival bought with inactivity". The metric to pre-register is enemy-paint
per-mil removed per round, normalised per round, NOT raw tiles mopped.

**Second-order, cheap, unmeasured**: `markResourcePattern` has a public overload
taking a rotation (0-3) and a reflect flag, so a resource pattern can be laid in 8
orientations. Verified in the engine but not needed yet — it would matter only if
site rejection due to contradicting neighbours becomes common in iteration 6.


---

## ROOT CAUSE FOUND (2026-09-06) — the tower mix degenerates to all-one-type per map

Found by extending `bob-tools/BobDump.java` to read the replay's per-turn action
union (the engine declares `Turn.actions` as a union of flatbuffer *structs*, and
the generated accessor only offers the Table form, so `Cursor` exposes the
protected buffer position and the struct is re-assigned onto it). The dumper now
reports, per team: cumulative spawns by unit type, total robot paint, enemy-paint
removals per interval, and peak bytecode. RobotType indices verified by running
the enum, not assumed: NONE=0, PAINT_TOWER=1, MONEY_TOWER=2, DEFENSE_TOWER=3,
SOLDIER=4, SPLASHER=5, MOPPER=6.

Tower types actually built (paint / money), across every replay on disk:

| map | our side | their side |
|---|---|---|
| gridworld | **0 paint / 9 money** | **0 paint / 8 money** |
| starburst | **4 paint / 0 money** | **3 paint / 0 money** |
| Snowglobe | **4 paint / 0 money** | 2 paint / 1 money |
| Thirds | **1 paint / 0 money** | 5 paint / 3 money |

`Soldier.towerTypeFor` has been `((ruin.x + ruin.y) & 1) == 0 ? MONEY : PAINT`
since iteration 0, commented "mix money and paint towers". **It does not mix.**
Ruin centres are constrained to be ≥5 apart and maps lay them out on regular
lattices, so on any given map they overwhelmingly share one parity of `x+y` and
every ruin resolves to the same tower type. The rule is a per-map coin flip that
usually lands on 100% of one type, and it lands on a *different* type on different
maps.

This is precisely the bug class TRAINING_ALGORITHM.md §7 puts first — "any fixed
absolute-order decision ... interacts with map geometry" — and I walked past it
in the iteration 4 comment while congratulating myself on noticing the *time*
dependence hazard in the same function.

**It is the common root cause of both degeneracies this session chased.**

- Iteration 3's story (327k → 551k unspent chips, paint starving unit production)
  is the *all-money* degeneracy. On gridworld our entire paint income for 2000
  rounds was the single starting paint tower. The upgrade mechanism was accepted
  at 87.5% because it was the only way to get paint out of a lineage that was
  building zero paint towers on that map.
- Iteration 4's story (chips pinned at 1200-1350 in the reserve dead band) is the
  *all-paint* degeneracy on starburst and Snowglobe, where we built 4 paint towers
  and zero money towers and had no chip income beyond the one starting tower.

It also explains iteration 4's confusing result honestly. Changing the mask from
`&1` to `&3` did not shift a 50/50 mix to 25/75; it re-rolled *which* maps
degenerate *which way*. That shuffles outcomes rather than fixing anything, which
is exactly the scattered mixed-direction pattern the run produced. **The ledger
entry for iteration 4 is therefore downgraded**: the arithmetic argument I wrote
there (chips buy paint income through upgrades, so starving money starves
upgrades) is plausible but was never actually the condition tested, because no arm
ever ran a mixed economy. Re-opening the paint-bias question is legitimate once
the mix is real — the recorded cause genuinely no longer applies.

### Iteration 7 (next, ahead of SRPs): lattice-independent tower mix

Fix must keep the type a pure function of the ruin (the marking deadlock from
iteration 4 still applies) while breaking the correlation with the ruin lattice.
An integer hash with avalanche does both:

```java
int h = ruin.x * 0x27D4EB2D + ruin.y * 0x165667B1;
h ^= h >>> 15; h *= 0x2545F491; h ^= h >>> 13;
return (h & 1) == 0 ? MONEY : PAINT;
```

Stable per ruin, no time dependence, ~10 bytecodes, and the parity of a
well-avalanched hash is uncorrelated with any lattice. It yields a binomial rather
than a guaranteed mix (on a 4-ruin map a 4-0 split still has probability 1/8,
versus near-certainty today), which is a large improvement and a small residual.

The guaranteed-balance version needs an adaptive rule (pick the type our team has
fewer of), and that needs the deadlock hazard removed first, by deriving a ruin's
type from its existing marks rather than recomputing it: fetch
`rc.getTowerPattern()` for both types at runtime, find the first cell where they
disagree, and read the mark there. Noted as the enabler, not attempted yet.

Pre-registered for iteration 7: h2h vs the then-current snapshot > 50%; and the
mechanistic check that makes this worth doing at all — **paint-tower and
money-tower counts must both be non-zero on the great majority of maps in the
sample**, read straight out of the new dumper columns.

### Instrument note

Peak bytecode measured from the replay is **9148 / 17500 (52%)** for our team,
higher than the ~8.3k the in-bot monitor reported at iteration 0. Still safe, but
half the budget is gone and the SRP work in iteration 6 adds two 25-tile scans.
Worth re-checking on every evaluation, as the algorithm requires.


### Iteration 7 pre-check: the hash validated offline against ruin lattices

Simulated both rules over regular and staggered ruin lattices at spacings 5-8
(Java 32-bit semantics emulated), before spending any VM time:

```
lattice                       old money%  new money%
grid sp=5 off=2                      50%         56%
grid sp=6 off=2                     100%         56%
grid sp=6 off=3                     100%         44%
grid sp=6 off=5                     100%         61%
grid sp=7 off=3                      50%         44%
grid sp=8 off=2                     100%         42%
grid sp=8 off=3                     100%         42%
staggered sp=5                       50%         56%

worst deviation from a 50/50 mix:  old rule 50 pts   new hash 11 pts
4-ruin maps that come out ALL ONE TYPE: old 33%   new 15%
```

This pins the mechanism exactly rather than leaving it as a story: the old rule
returns **100% one type on every EVEN ruin spacing** and 50% on odd spacings,
because `(x + y) & 1` is invariant along a lattice whose steps are even. The
observed splits are exactly this — gridworld and the other all-one-type maps have
even ruin spacing. The hash holds every lattice tested within 11 points of an even
mix, and cuts the small-map degenerate case from 33% to 15%.

Worth recording as method, not just result: this was a free pre-check. Nothing
about it needed the engine, the VM or a game — the hypothesis was about a pure
integer function and could be tested as one in a few seconds. Reachability and
effect-size questions of that shape should always be answered offline first.


---

## Ledger correction (2026-09-06) — iteration 4 RE-OPENED

TRAINING_ALGORITHM.md permits re-opening a closed direction only with a specific
reason the recorded cause no longer applies. That test is met here, so the entry
is re-opened rather than quietly ignored.

Closed as: *"Bias ruin capture toward paint towers (1 in 4 money instead of 1 in
2) — chips buy paint income back through iteration 3's upgrades, so starving
money starves upgrades and nets less paint."*

Why the recorded cause does not apply: **the condition named in it was never
tested.** "1 in 4 money instead of 1 in 2" describes an experiment that did not
happen. `towerTypeFor` produced ~100% of a single type per map under both masks
(measured: gridworld 0 paint/9 money, starburst 4/0, Snowglobe 4/0, Thirds 1/0),
so the `&1`→`&3` change did not move a mix from 50/50 to 25/75 — it re-rolled
*which* maps degenerate *which way*. No arm on either side of that comparison ever
ran a mixed economy, so the arithmetic argument I wrote in the ledger, however
plausible, was not what the run measured. A rejection has to be attributed to the
condition actually evaluated.

Status: **re-openable, but not queued yet.** The honest position is that the
paint/money ratio is an *unmeasured* parameter, not a rejected one. It becomes
measurable only after iteration 7 makes the mix real, and it should be measured
then as a proper dose sweep with a zero arm (the hash's natural ~50/50 being the
zero arm), not as another single point.

---

## Ablation queued (2026-09-06) — is iteration 3 worth what it scored?

Acting on my own caveat rather than leaving it as a hedge in a report.

**The worry, stated precisely.** Iteration 3 (idle-chip tower self-upgrade) was
accepted at 21/24 = 87.5% against `bob_iter1`. Upgrading a paint tower is +5
paint/turn per level. But on an all-money map — gridworld, where that h2h ran —
the team owns exactly ONE paint tower all game (the starting one), so upgrading it
is close to the only lever on paint income that exists, and the mechanism gets
credit for rescuing a situation that the `towerTypeFor` defect created. On a map
with a genuine mix, expansion into more paint towers may dominate, and the upgrade
may be worth far less than 87.5% suggested. The instrument and the disease shared
a cause.

This is the shape TRAINING_ALGORITHM.md's ablation section describes: headline
accepts worth ~0 once measured directly, while incidental failure-mode preventers
carry the real value.

**Design** (run once iteration 7 has landed, so the ablation is measured on a bot
with a real tower mix — ablating it now would just re-measure the defect):
- `src/bob_noupg` = the then-current accepted bot with `UPGRADE_RESERVE` set
  beyond any reachable treasury, so `canUpgradeTower` is never called. Everything
  else byte-identical. This is a true zero arm, not a re-implementation.
- One gauntlet, current bot vs `bob_noupg`, on a resampled draw.
- Pre-registered readouts: h2h; and from the dumper, `ptow`/`mtow` counts to
  confirm the mix is genuinely mixed on most maps (otherwise the ablation is
  invalid for the same reason the original accept was suspect), plus team paint
  totals.
- **Pre-committed interpretation, so this cannot be rationalised after the fact:**
  if the current bot beats `bob_noupg` by less than ~60/40, iteration 3's standing
  value is materially lower than its accept implied and I will say so in this log
  and on the chart, keeping the feature only if it is at least neutral. An accept
  that was right for the wrong reason still needs the correction recorded.


---

## Synthetic archetype added (2026-09-06) — `src/bob_denier`, the paint-denial pole

The opponent pool has been 100% self-lineage since iteration 0 (plus
examplefuncsplayer). TRAINING_ALGORITHM.md calls synthetic archetypes core
infrastructure — "build the simple poles early; they exist to answer 'does our bot
handle an opponent that does X' for X our own lineage never does" — and I had
none. Fixed.

Pole chosen from evidence rather than taste. The measured fact that makes it the
right one: long games end with the map fully painted (966 of 1000 per-mil claimed
by someone), and **soldiers cannot overwrite enemy paint at all** — only splashers
(within r²≤2 of the splash centre) and moppers can. Every bot in my lineage spawns
a fixed 3 soldiers : 1 splasher : 1 mopper, so my whole evolutionary history has
never produced an opponent that attacks my territory. `bob_denier` inverts the
ratio: 60 rounds of soldiers to capture ruins, then splashers and moppers only.

It is a POLE, not a peer, and the log should never read a win rate against it as a
strength claim. The staleness trap is recorded in `src/bob_denier/README`: it is
forked from bob_iter3 and drifts further from the live bot with every accept, so
it must be re-forked when it stops being a challenge, with the re-fork recorded
here so no win rate is compared across it.

Not added to `progress/roster_extra.txt` yet, and deliberately so: the roster is
the *absolute-strength* instrument and requires opponents that never change, but
this one is scheduled to be re-forked. It joins the peer pool, not the roster.

Compile-verified in isolation (`~/bob-tools/dencheck`), so it cannot break the
tournament build when committed.


---

## Backlog find (2026-09-06) — our splashers and moppers do almost nothing

Free analysis on a replay already on disk, using the new `unpaint` column
(Unpaint + Splash + Mop actions per interval). gridworld, our side, per 200 rounds:

```
round  splashers  moppers  denial actions/round   per denial unit
 400       4         5            0.12                0.014
 800      10        11            0.06                0.003
1400      19        20            0.17                0.004
2000      27        28            0.20                0.004
```

A mopper's action cooldown is 30 and a splasher's is 50, so their ceilings are
0.33 and 0.20 actions per round *each*. Measured throughput is ~0.004 per unit per
round — **on the order of 1% of capacity**. (Those unit counts are cumulative
spawns rather than live population, so the true per-unit rate is somewhat higher;
even assuming only a fifth are alive it is under 5% of capacity.) We are spending
2 of every 5 units built on the only two unit types that can remove enemy paint,
and they are essentially idle.

That matters more than the spawn *ratio* I had queued as iteration 7 — tuning the
ratio of units that do nothing would have been a textbook case of the algorithm's
"metrics that improve without converting to wins". **The ratio question is
demoted; utilisation comes first.**

Candidate mechanism, and it is specific and checkable: `Nav.navTo` tries a first
pass that refuses to step onto enemy paint, and only falls back to "take anything"
if no other move exists. That is correct for a soldier — standing on enemy
territory costs 2 paint/turn — but splashers and moppers are *paid* to be in enemy
territory, and enemy paint is exactly the terrain they must enter. A splasher
navigating toward a large enemy region will slide along its border rather than
penetrate it, and `Splasher.run` only fires when a cluster scores ≥5, which on a
saturated map requires enemy tiles within r²≤2 — i.e. requires having gone *in*.
The navigation policy and the firing condition are fighting each other.

Second candidate, additive rather than alternative: the splasher's 50-paint
attack cost against a starved paint economy. `Splasher.run` requires
`paint >= 60`, and a unit that cannot refill sits at the floor.

Pre-registered instrument for whichever iteration takes this on: denial actions
per living denial unit per round, from the dumper — normalised per round and per
unit, because raw counts scale with game length and with army size and would read
as "better" for reasons unrelated to the change. Note also the caution from
measurement doctrine #4: this must NOT be evaluated only in mirror matches, where
both sides paint at the same rate; `bob_denier` exists partly to pose this threat.

Queue order revised on this evidence:
1. iteration 7 — lattice-independent tower mix (root cause, already validated)
2. iteration 8 — denial-unit utilisation (this)
3. iteration 9 — SRPs (written and compile-verified, still the largest paint lever)
4. then the iteration 3 ablation and the re-opened paint/money ratio sweep


---

## Iteration 5 RESULT (2026-09-06) — self-calibrating expansion reserve — REJECTED (no-op)

Session note: the driver session running this evaluation was killed by an SSH
hangup at ~21:07 UTC. The **run itself finished on battlecode-dev** (only the
poll loop died) and was recovered with `tools/gauntlet-collect.sh` into
`gauntlet/20260906-204201/` — 120 games, GAUNTLET-COMPLETE. Not re-run.

### Result against the pre-registered criteria

| pre-registered | required | measured | verdict |
|---|---|---|---|
| 1. h2h vs `bob_iter3` | > 50% (≥16/30) | **15/30 = 50.0%** | FAIL |
| 2. swept-win ≥ swept-loss | — | 0 vs 0 (all 15 maps split by side) | vacuous |
| 3. chips no longer pinned at 1200-1350 | — | see below | not the reason |

Roster, same shared 15-map sample: `bob_iter0` 26/30 (87%), `bob_iter1` 24/30
(80%), `examplefuncsplayer` 30/30. Recorded in `progress/vs_old_bots_history.csv`
labelled as `bob_iter3`, which is the build that actually played — see the
identity check below.

### The arm-to-arm identity check settles it (measurement doctrine #3)

Not "50%, marginal, re-run it" — determinism means a re-run is worthless, so I
checked *identity* instead. Per-map round counts, candidate vs `bob_iter3`:

```
map          A-side rounds   B-side rounds   winner side
AlarmClock       1188            1188             B
Bunny            1120            1120             A
Castle           2000            2000             B
...              (13 of 15 maps identical to the round)
UnderTheSea       798             817             A   <- differs
rain             1861            1939             B   <- differs
```

On **13 of 15 maps the two arms are byte-identical**: the same map produces the
same round count and the same winning *side* no matter which team my candidate
plays. That is not a close match, it is the same bot playing itself. The 15/30 is
therefore pure side advantage, not a 50/50 skill split, and the two maps that do
differ (UnderTheSea, rain) changed round count without changing the winner.

So the change **executed on 2 of 15 maps and altered 0 outcomes**. This is exactly
the reachability caveat pre-registered in the iteration 5 entry before the run:
under `bob_iter3`'s economy chips run to hundreds of thousands and the 1200-1350
dead band is essentially never occupied. The band was real and traced — under
*iteration 4's* economy, which was rejected.

### Decision and disposition

**REJECTED** — fails the accept gate, and honestly it is not even a near miss to
refine, because there is nothing to refine: no dose of `EXPANSION_IDLE` can matter
in games that never enter the band. Tuning it would be searching a parameter that
feeds a check that never runs — the exact failure mode measurement doctrine #2
warns about.

`src/bob/Tower.java` reverted to the accepted build. The diff is **shelved, not
discarded**, at `bob-tools/shelved/iter5-expansion-reserve.patch`, because the
mechanism is correct and only its upstream state is missing.

**Pre-registered re-open condition, so this is a test and not a hunch:** re-apply
it when an accepted iteration lowers chip income enough that the treasury visibly
occupies 1200-1350 for a sustained stretch — read `moneyA`/`moneyB` from the
dumper, not from intuition. Iteration 7 is a candidate trigger: it converts maps
that were 100% money towers into a ~50/50 mix, which roughly halves chip income on
exactly those maps. If iteration 7 is accepted, re-check the band before anything
else, and re-run this patch as its own iteration — never bundled with 7, since a
bundled result is uninterpretable.

### What this cost and what it bought

One gauntlet. It converted "the reserve dead band is a live bug in the current
bot" from a belief into a measured falsehood: it is a live bug in an *economy* the
current bot does not have. That distinction is worth the run, and it is the reason
the patch is shelved with a trigger rather than deleted or silently carried.

**Method note for LEARNINGS.md:** when an h2h lands near exactly 50%, count
byte-identical games *before* reaching for "marginal, needs a wider sample". A
perfect side-split across every map is the signature of a no-op, and it is free to
detect from `results.csv` alone.

---

## Iteration 7 (2026-09-06) — lattice-independent tower mix — RUNNING

Target: the root cause recorded above — `towerTypeFor` used `((x + y) & 1)`, and
parity is invariant along any lattice with an even step, so on every even ruin
spacing the map came out 100% one tower type. Measured degeneracies: gridworld
0 paint / 9 money, starburst 4/0, Snowglobe 4/0, Thirds 1/0.

Change (isolated, `src/bob/Soldier.java`, ~10 bytecodes, nothing else touched):
replace the parity with the low bit of an avalanche hash of the ruin's
coordinates. Still a pure function of the ruin, which the marking protocol
requires — a type that varies with time deadlocks `workOnRuin`'s "already marked?"
probe (iteration 4's finding, preserved).

Validated offline before spending any VM time (full table in the pre-check entry
above): worst deviation from an even mix across grid and staggered lattices at
spacings 5-8 falls from **50 points to 11**, and 4-ruin maps that come out all one
type fall from **33% to 15%**.

Evaluation run: `NMAPS=20`, 5 opponents on one shared sample, 200 games —
`bob_iter3` (accept gate), the frozen roster `bob_iter0` / `bob_iter1` /
`examplefuncsplayer`, and `bob_denier`, the paint-denial pole, which is in a
gauntlet for the first time.

Pre-registered accept criteria:
1. **h2h vs `bob_iter3` > 50%** (≥21/40) — accept gate.
2. **Mechanistic gate, and this one is the point of the iteration:** from the
   dumper, `ptowA` and `mtowA` must BOTH be non-zero on the great majority of
   maps sampled. If the mix is still degenerate the hash did not do its job and
   the win rate is irrelevant either way.
3. No one-directional regression concentrated on a single map or side.

Pre-registered *interpretation* of a 50%-ish result, written before the numbers
arrive: if the identity check shows a large fraction of byte-identical games, that
means the sampled maps had mostly odd ruin spacing and the instrument could not
see the change — a sample problem, not a verdict, to be answered by resampling
onto maps with even spacing rather than by refining the hash.


---

## Structural trace (2026-09-06) — WE STARVE OUR OWN ARMY: 78% of our deaths are paint zero

Done with the VM busy on iteration 7, on replays already sitting on disk. Cost: no
games. It refuted the hypothesis I had queued as iteration 8 *and* replaced it with
a much larger one, which is the whole argument for tracing before building.

### New instrument: `bob-tools/BobMop.java` + `mop-trace.sh`

The existing dumper reports engine team totals; it cannot say where our units were
or what they could see. `BobMop` reconstructs the **per-tile paint owner** round by
round from the replay's Paint/Unpaint/Splash actions, reads `Turn.x/y` for every
robot, and reads the map header's size, `symmetry()` and ruin list. Per sampled
round it prints, for our moppers and splashers: how many have an enemy tile inside
action range (r²≤2) and inside vision (r²≤20), the median distance to the nearest
enemy tile, live population by type, and average/minimum stash. Then it does death
forensics: every one of our units that dies is bucketed by the paint it held on its
last recorded turn.

Two engine details it had to get right, both found by `javap`: deaths are reported
as `DieAction` inside a turn, **not** in `Round.diedIds` (which is empty all game),
and `DieAction` carries a `dieType` that distinguishes an EXCEPTION death.

### Finding 1 — the queued iteration 8 hypothesis is dead

I had queued "denial units can't reach enemy paint because `Nav.navTo` refuses to
step on it". Measured on Castle (2000 rounds, our side A), per 200 rounds:

```
round  liveMop  mopInAct(r2<=2)  mopInVis  medDistToEnemyPaint
 400      2            1             2            3
 800      2            1             1           16
1200      3            0             0           11
1400      4            1             2            8
1600      3            1             2            3
1800      1            1             1            1
```

Roughly **half our live moppers are already standing within action range of enemy
paint**, and nearly all of them can see some. They are in contact. Navigation is
not the binding constraint, and I would have spent an iteration proving that the
expensive way.

### Finding 2 — my own "1% of action capacity" number was wrong, and I made the error

The backlog entry above divided denial actions by **cumulative spawn counts**. I
even flagged the caveat and then guessed the live fraction at "a fifth". The truth
from `Turn` records: by round 2000 on Castle we had spawned 52 moppers and had
**2 alive**. Recomputed against live population, denial throughput is ~0.1 actions
per live unit per round against a ~0.27 mixed ceiling — about **37% of capacity**,
not 1%. The lesson is not subtle and belongs in LEARNINGS.md: *a rate is a claim
about a denominator; if the denominator is a guess, so is the finding.* Never
publish a per-unit rate over a count the engine does not actually mean as
population.

### Finding 3 — the real degeneracy, and it is enormous

Cumulative spawns by round 2000 on Castle: 183 soldiers, 54 splashers, 52 moppers.
Live population at any moment: **6-13 soldiers, 1-4 splashers, 1-4 moppers.** We
build roughly 290 units across a game and hold a standing army of about 15.

Death forensics say why. Every one of our dead units, bucketed by the paint it held
on its final turn:

```
game (map, opponent, side)        SOLDIER deaths / starved(<=10)   SPLASHER      MOPPER
Castle       vs bob_iter3  A          177 / 147  (83%)             54 / 21      52 / 41
lighthouse   vs bob_iter0  A           58 /  54  (93%)             17 / 15      18 / 15
UnderTheSea  vs bob_iter1  B           81 /  63  (78%)             20 / 13      22 / 17
Thirds       vs bob_iter0  A           52 /  51  (98%)             16 /  7      16 / 12
------------------------------------------------------------------------------------
totals                                 368 / 315 (86%)            107 / 56     108 / 85
```

**456 of 583 unit deaths (78%) happen at ≤10 paint.** Zero exception deaths, on all
four games, which at least rules out silent crashes. Combat kills are the minority
everywhere; on Thirds our soldiers were killed by an enemy exactly **zero** times
out of 52 deaths.

This satisfies the generality pre-check on its own: three maps, three different
opponents, both sides, sizes 27x27 to 51x51. It is not a Castle artifact.

Priced in paint, Castle alone: 147 soldiers x 200 + 21 splashers x 300 + 41 moppers
x 100 = **~39,800 paint** spent on units that then died with an empty stash. Paint
is the resource the win condition is denominated in.

### Finding 4 — the mechanism, and it is a two-line hole

`Soldier.run` step 0 is `if (rc.getPaint() < REFILL_BELOW && tryRefill()) return;`
and `tryRefill` scans `senseNearbyRobots(-1, us)` for a tower with ≥100 paint.
Vision is r²=20, about 4.5 tiles. **If no tower is in vision, `tryRefill` returns
false and the soldier carries on wandering** — it has no idea where any tower is,
so a unit that runs low away from home simply keeps walking until it hits zero,
takes `NO_PAINT_DAMAGE` 20 HP/turn, and dies. The refill has no memory.

`Mopper.run` and `Splasher.run` have **no refill logic at all**. Not a weak one —
none. Neither type ever calls `tryRefill`.

That is a capability we already paid for and then discarded, which is exactly the
recurring winner's profile TRAINING_ALGORITHM.md names: *capability preserved at
zero marginal cost*. Mopping in particular costs **0 paint** (engine table), so a
mopper that stays alive on ally paint is free denial forever.

### Closed direction (recorded now, with its measurement)

- **"Denial units are idle because `Nav.navTo` avoids enemy paint."** CLOSED by the
  contact measurement above: ~half of live moppers are already inside action range
  of enemy paint. Re-open only if a future trace shows contact collapsing.

### Queue revised on this evidence

1. iteration 7 — lattice-independent tower mix (running)
2. **iteration 8 — refill memory: units remember an allied tower and walk to it
   when low, and moppers/splashers gain refill at all** (this; by far the largest
   measured waste in the bot)
3. iteration 9 — SRPs (written and compile-verified)
4. then the iteration 3 ablation and the re-opened paint/money ratio sweep


---

## Iteration 8 (2026-09-06) — remembered-tower refill — WRITTEN, queued behind 7

Written and compile-verified while iteration 7 occupies the evaluator; held in
`bob-tools/shelved/iter8-candidate/` so it survives a session death.

**Target** (from the starvation trace above, not from a single losing game — the
algorithm prefers absolute degeneracy signals over opponent-relative ones, and
"78% of our units die with an empty stash" needs no opponent to be wrong).

**Hypothesis.** Units die of paint starvation because the refill path can only see
towers inside vision (r²=20). A unit that runs low anywhere else has no idea where
a tower is, keeps executing its normal routine, and starves. Every robot spawns
within `BUILD_ROBOT_RADIUS_SQUARED=4` of the tower that built it, so the location
of a tower is already in its very first sense call and we discard it. Remembering
it, and walking back when low, should convert a large share of those deaths into
living units at no resource cost.

**Change** (one mechanism, one new file `src/bob/Refill.java`, called by all three
unit types): remember the nearest allied PAINT tower ever seen (`paintPerTurn > 0`
— money towers are engine-verified sterile), plus any tower as a fallback for the
two starting towers. When below threshold: withdraw from a tower in range, else
navigate to the remembered one, else wait adjacent for it to regenerate rather than
sliding around it. `Soldier.tryRefill` is superseded and deleted, so this replaces
a path rather than adding a second one.

Thresholds, each derived from the engine table rather than picked:
- SOLDIER 50 of 200 — **unchanged from the existing constant**, deliberately, so
  the measured effect is the *memory*, not a retuned threshold.
- MOPPER 35 of 100 — moppers pay `MOPPER_PAINT_PENALTY_MULTIPLIER=2`, so 4/turn on
  enemy paint: 35 is roughly nine turns of walking home from enemy ground.
- SPLASHER 110 of 300 — an attack costs 50 and `Splasher.run`'s own gate is
  `paint >= 60`, so below 110 a splasher has at most one shot left in it.

**Bytecode, stated as a risk up front:** peak is already 9148/17500 (52%) and the
limiter truncates a turn silently with no exception. So the sense call is gated: a
unit that already knows a tower and is above `2 x threshold` does no extra sensing
at all. It scans only on its first turn (at the tower that built it) or when
approaching the threshold.

**Pre-registered accept criteria:**
1. **h2h vs the then-current accepted snapshot > 50%** — accept gate.
2. **Mechanistic, from `BobMop` death forensics on a sampled game: the starved
   fraction (deaths at ≤10 paint) must fall well below the measured 78% baseline,
   and live standing-army population must rise.** If starvation does not fall, the
   mechanism did not engage and the win rate is not evidence about this idea.
3. **Peak bytecode from the dumper's `maxbc` must stay under ~14000** (80%).
4. No one-directional regression concentrated on one map or side.

**Pre-registered failure shape, written before the run:** the algorithm's own
ledger warns that *survival bought with inactivity* is a recurring trap — "halving
the death rate cost 18 peer games; units die doing the thing that wins". This
change makes units walk home instead of painting, so it can absolutely buy
longevity with lost tempo. That is why criterion 1 is a win rate and criterion 2 is
only a mechanism check: a big drop in starvation with a losing h2h is a REJECT, and
it would be a well-earned one that closes the direction properly.

**Confound to keep separate:** iteration 7, if accepted, creates paint towers on
maps that previously had none, which would make refill more valuable. That is why 7
is being measured first and alone.


---

## Iteration 7 mid-run analysis (2026-09-06) — the whole map pool, measured, and a direction closed by arithmetic

Done while the evaluation ran, on the map files themselves. New tool
`bob-tools/BobRuins.java`: every `.map25` is a flatbuffer whose root is a `GameMap`
carrying the ruin list, so "what tower mix does `towerTypeFor` produce on this map"
is a question about the maps and needs **no games at all**. Answered exactly for
all 75.

### The offline pre-check I ran before the iteration was measuring the wrong population

I validated the hash against *simulated* ruin lattices and concluded the old parity
rule "returns 100% one type on every EVEN ruin spacing". Against the real maps:

```
deviation from a 50/50 mix     old rule   new hash   fair coin (expected)
  > 10 points                        24         33                   30.4
  > 20 points                        13          6                    8.6
  > 30 points                         7          0                    2.1
  > 40 points                         4          0                    0.3
mean deviation                      9.3        9.9                   10.1
```

The old rule degenerates completely on **4 maps of 75** — CastleDefense, Filter,
Snowman, gridworld — not on a broad class. And its *mean* behaviour is slightly
BETTER than the hash's, because parity on a spatially structured ruin set is
anti-correlated in a way that lands near 50/50 on most maps while failing totally
on a few. My lattice model predicted the failures but badly overstated how many
maps they covered.

### Direction CLOSED by arithmetic: no pure function can beat this hash

The fair-coin column above is computed exactly, per map, from that map's own ruin
count. The hash's 9.9 mean deviation *is* the fair-coin floor of 10.1 — it is
behaving as a fair coin, which is all any function of a single ruin's coordinates
can be. A ruin's type being a pure function means each ruin decides independently,
so the split is binomial and the median map's 17 ruins give a standard deviation of
50/sqrt(17) = 12 points no matter what mask, multiplier or mixing constant is used.

- **CLOSED: "search for a better hash / a different mask / more avalanche steps."**
  Killed by the table above, not by a run. There is nothing left on the table:
  9.9 against a floor of 10.1.
- **The only way past the floor is an adaptive rule**, which requires removing the
  marking deadlock first (derive a ruin's type from its existing marks by diffing
  `rc.getTowerPattern()` for the two types and reading the mark at a disagreeing
  cell). That enabler is already recorded above and is now the *only* live
  descendant of this thread.

Interesting for its own sake: the hash beats the fair coin in the tails (0 maps
over 30 points where a coin expects 2.1). That is luck, not design, and I am not
going to claim it as a property.

### What the change is actually worth, stated honestly

It converts 4 maps from "100% one tower type" to a mix and pulls 7 maps back from
over 30 points of skew, at the cost of moving typical behaviour from a
lucky-structured 9.3 to a fair-coin 9.9. That trade is good on convexity, not on
the mean: a 100%-money map has **no paint income at all** beyond the single
starting paint tower, which the iteration 3 work showed is crippling, whereas a
60/40 map is unremarkable. Harm is convex in skew; the mean is the wrong summary.

### And the sample cannot see it

The run's 20-map sample contains **none of the 4 degenerate maps**. That is exactly
the interpretation I pre-registered before the numbers existed: "a sample problem,
not a verdict." The h2h from this run therefore measures *no regression on ground
where the change is a lateral move* — a real and necessary thing to measure, but
not the value of the fix.

Accordingly, and pre-registered now, before the affected-subset run: the affected
subset is defined **by the mechanism, not by outcome** — the maps where the two
rules disagree most, computable before any game. The accept case requires BOTH
halves: (a) the broad random sample shows no regression, and (b) the affected
subset shows a real gain. Reporting only (b) would be cherry-picking, so both go
in the log whichever way they land.


---

## Cross-agent evidence (2026-09-06) — an independent lineage starves 6x less than I do

From the sanctioned channel only: tournament `20260906-1755` replays on
battlecode-dev. `BobMop` reads observable match behaviour — robot positions, paint
actions, deaths and the stash held at death — which is exactly what MULTI_AGENT.md
permits ("replays show what an opponent *does*, observable in any real match").
No code, notes or logs of another agent were read.

`bob-vs-carol-on-DefaultMedium`, both sides of the same game, our-unit deaths
bucketed by paint held on the final turn:

```
                 SOLDIER deaths / starved      MOPPER deaths / starved
  bob   (side A)        4 /   4                    157 / 157
  carol (side B)        2 /   2                     25 /  25
```

Two things fall out, and they point in the same direction.

**1. Starvation is confirmed by an instrument my own lineage did not produce.**
100% of both bots' unit deaths were at ≤10 paint — zero combat kills on either
side of a full-length game. This is the self-referential blind spot working as
TRAINING_ALGORITHM.md hoped: the finding survives contact with a lineage that
shares none of my code.

**2. It is a differentiator, not a law of the game.** I lost **157 moppers** where
the independent bot lost 25 on the identical map. Six times the attrition. That is
15,700 paint plus 47,100 chips of mopper production converted into nothing on one
map. Whatever the other lineage does differently, my mopper loss rate is not forced
by the engine — which is precisely what I could not have learned from my own
snapshots, since every one of them shares the defect.

This raises iteration 8's expected value considerably and it is now unambiguously
the right next target. It also sharpens the mopper threshold: on this evidence the
mopper is the worst-affected type by a wide margin, so `Refill.seek(35)` for
moppers is the load-bearing part of that change, not an afterthought.

Note for the ledger: the standings from that tournament (every pair splitting every
map by side, 4/8 each) carry almost no information — 2 maps, 8 games. The *replays*
carried a great deal. Standings and replays are very different instruments and the
run being uninformative on one does not make it uninformative on the other.

### Iteration 7 affected-subset run — PRE-REGISTERED before it is launched

Subset defined by the mechanism, from `bob-tools/ruins-mix.csv`, before any game on
these maps is played. A map qualifies if the two rules' deviation from a 50/50 mix
differs by **≥17 points in either direction** — so the subset deliberately contains
the maps the hash makes WORSE as well as the ones it fixes. That is what stops it
being a cherry-pick, and it turns the run into a two-sided dose-response test
rather than a search for good news.

```
helped (9): Snowman CastleDefense gridworld Filter yearofthesnake
            lighthouse windmill DefaultMedium boxofchocolates
hurt   (6): Paintball Castle Rose SandyBeach sierpinski sunrise
```

15 maps x 2 sides vs `bob_iter3` = 30 games.

Pre-registered readouts:
1. **Win rate on the 9 helped maps vs the 6 hurt maps.** The prediction the
   mechanism makes is a *split*: above 50% on helped, at or below 50% on hurt. A
   uniform result in either direction across both groups is evidence the tower mix
   is not what is driving the games at all, and would make the whole iteration a
   wash regardless of the headline.
2. The 4 formerly all-one-type maps (CastleDefense, Filter, Snowman, gridworld)
   read out separately — that is where the convexity argument lives.
3. Combined with the broad 20-map run as the no-regression half. **Both halves are
   reported whichever way they land.**

Decision rule, fixed now: accept only if the broad run shows no regression AND the
helped group beats the hurt group. If the helped group does not beat the hurt
group, the mechanism is not converting into wins, and iteration 7 is a REJECT that
closes the tower-mix thread for good — which, given the arithmetic above showing no
pure function can do better, would be a genuinely useful thing to have established.


---

## Iteration 8 evaluation plan, finalised while 7 ran (2026-09-06)

**Bytecode baseline pinned**, so criterion 3 has something to compare against.
Measured peak `maxbc` from existing replays, both teams: Castle 9388 / 9640,
UnderTheSea 9928 / 9931 — i.e. **54-57% of the 17500 limit**. The 14000 (80%)
ceiling pre-registered for iteration 8 leaves real margin, and the gated sense call
means a healthy unit adds nothing at all.

**Exact-comparison plan for the mechanistic gate.** The gauntlet's map sample is
redrawn each run, so the candidate may never play the map I have baseline forensics
for. Rather than hope, after the gauntlet I will run a single `vm-match.sh` with
`TEAM_A=bob TEAM_B=bob_iter3` on **Castle**, pull the replay, and run `BobMop` on
side A — the identical map, side and opponent as the baseline below. That makes the
starvation comparison exact rather than across-sample:

```
baseline (bob_iter3, Castle, side A):  SOLDIER 177 deaths / 147 starved (83%)
                                       SPLASHER 54 / 21      MOPPER 52 / 41 (79%)
```

**Pre-registered failure shape and its refinement, written now so the response is
not invented after the fact.** `Refill.seek` sits at the top of `Soldier.run`,
ahead of ruin capture. The old code had the same threshold but `tryRefill` returned
false when no tower was visible, so a low soldier simply carried on working; the
new code walks it home. Soldiers will therefore abandon ruin work far more often —
which is precisely TRAINING_ALGORITHM.md's "survival bought with inactivity" trap
("units die doing the thing that wins").

So if the result is **starvation down but h2h below 50%**, that is the diagnosed
shape, not a mystery, and the single pre-registered refinement is: do not interrupt
a soldier that is actively completing a ruin pattern unless it is critically low
(below `PAINT_FLOOR`), i.e. move the refill check below the ruin-capture step for
soldiers that already hold a `workRuin`. One refinement, then a decision either
way — no open-ended search.

If instead **starvation does not fall**, the mechanism did not engage, the win rate
says nothing about this idea, and the answer is a trace, not a refinement.


---

## Iteration 7 play-symmetry audit (2026-09-06) — the hash DOUBLES the side asymmetry

TRAINING_ALGORITHM.md Phase 0 item 7 requires auditing new tie-break/default
decisions as they are written, and I had not applied it to the hash. Doing so now
found a real cost I had not anticipated.

New tool `bob-tools/BobSym.java`. Maps are guaranteed symmetric and each team
captures the ruins in its own half, so the two teams' ruins are mirror images. If
`towerTypeFor` gives a mirrored ruin pair *different* types, the two teams get
different tower mixes on a symmetric map — an unearned economic asymmetry that has
nothing to do with either bot's play. The symmetry is inferred per map (whichever of
rotation / horizontal / vertical maps the ruin set onto itself), not trusted.

```
                                        old parity rule    new hash
maps with a mismatched mirrored pair      30 (40%)          73 (97%)
mean money%-gap between the two halves    11.0 pts          24.0 pts
```

The parity rule is *partly* symmetry-preserving by accident: under rotation,
`(x+y)` and `(W-1-x + H-1-y)` have the same parity exactly when `W+H` is even, so
on those maps every mirrored pair agrees. The hash has no such structure and
disagrees on about half of all pairs, by design.

### The obvious fix, tested offline, and REJECTED offline

Hash the **folded** coordinates `min(x, W-1-x), min(y, H-1-y)`. That quantity is
invariant under rotation *and* both reflections simultaneously, so mirrored ruins
hash identically and the team gap is 0 by construction, with no need to infer which
symmetry holds. Elegant. Measured over all 75 maps, it is also worse:

```
rule           all-one-type maps   mean mix deviation   team gap
old parity          4 (5%)                9.3            11.0
new hash            0 (0%)                9.9            24.0
folded hash         6 (8%)               16.0             0.0
```

Folding halves the number of independent draws — each mirrored pair now contributes
two ruins of the same type — so the whole-map mix variance doubles (sd x sqrt(2),
and 10.1 x 1.41 = 14.3, which is what the 16.0 is). It buys perfect side symmetry by
making the *catastrophic* case more common than the rule I am trying to replace: 6
all-one-type maps against the old rule's 4.

**CLOSED: "make the tower-type hash symmetry-invariant by folding coordinates."**
Killed by the table above. Cost: about three minutes and no games. This is the
second time in this iteration that a question which looked like it needed a
gauntlet turned out to be a question about the map files.

### Where that leaves iteration 7

No rule dominates. The hash's case rests entirely on the catastrophe dimension — it
is the only one of the three that never produces a 100%-one-type map — and it pays
for that with double the side asymmetry and a hair more typical skew. That is a
genuine trade, not a free win, and it is consistent with the broad run's 21/40:
structure improved in one place and worsened in another, netting out near zero.

The pre-registered affected-subset run is now the tiebreaker, and its decision rule
was fixed before any of this was known. I am not going to relax it because I have
since found an extra argument on either side.


---

## Structural trace (2026-09-06) — the supply side: our towers are chronically paint-poor

Found while blocked on a saturated VM, from a replay already on disk. `BobMop` now
also reports our paint towers' count and stash.

`Tower.run` step 3 gates spawning on **chips only** — `if (chips >= want.moneyCost
+ reserve)`. It never looks at the tower's own paint. The engine stops an
unaffordable build (`canBuildRobot` checks paint), so the tower simply spends down
to the floor and stays there. Castle, our side, paint towers only:

```
round   livePaintTowers   avg stash   min stash
 250          1              100        100
 500          2               90         75
 750          2              122         40
1000          2              142         75
1500          3               93         45
1750          3               48          0
2000          3              110         50
```

A soldier costs **200 paint** to spawn and a mopper 100. Our paint towers average
about 100 and touch zero. They are converting every drop of regen into new units
the moment they can afford one, which is precisely why the units that already exist
have nothing to refill from — the two findings are the demand and supply sides of a
single leak.

**This is a live risk to iteration 8, and I want it on record before that run, not
after.** `Refill.seek` requires a tower with ≥100 paint before withdrawing; on this
evidence that condition will often be false. The candidate handles it (a unit that
has arrived waits adjacent for regen rather than wandering off), but waiting is
inactivity, which is the failure mode the algorithm warns about. So iteration 8 may
well come back as a *partial* success — starvation down, tempo flat — and if it
does, the reason is already identified and is not a mystery to be re-traced.

### Queued (NOT bundled into iteration 8)

**Tower paint reserve**: do not spawn unless the tower would retain a float for
refills, e.g. `rc.getPaint() >= want.paintCost + FLOAT`. Note the shape: iteration 5
*removed* a fixed reserve because it protected an expansion that had already
finished, so it was blocking production to protect nothing. This *adds* one, and
the distinction is that it protects a demand which is continuous rather than a
one-off event — refills happen all game. The iteration 5 lesson is not "reserves are
bad", it is "a reserve must protect a demand that still exists", and this one does.
It also must be measured on paint towers specifically: a money tower has
`paintPerTurn == 0`, so once its initial stash is gone it can never refill anyone
and reserving its paint would be pointless.

Order stays: iteration 8 (demand side) alone first, then this (supply side) alone,
so each is interpretable. If they interact, the interaction is measurable as the
difference between their individual and combined effects — which is only possible
if they are run separately first.


---

## Paint accounting (2026-09-06) — 59% of the paint we hand our units evaporates as drain

Engine probe first, because the whole picture turns on two numbers I had never
actually looked up:

```
LEVEL_ONE_PAINT_TOWER   paintPerTurn=5    LEVEL_TWO=10   LEVEL_THREE=15   cap 1000
SOLDIER paintCost=200   SPLASHER paintCost=300   MOPPER paintCost=100
every money tower and defense tower: paintPerTurn = 0
```

**A level-one paint tower makes 5 paint per turn. A soldier costs 200 paint — forty
turns of a tower's entire output.** With the 2-3 paint towers the Castle trace shows,
team paint income is on the order of 20-30/turn, and that is the budget for
everything.

### Where it goes (Castle, our side, whole game)

```
paid out as spawns                      58,000 paint
soldier paint actions   2,686 x 5   =   13,430
splash actions            207 x 50  =   10,350
                                      ---------
total that ever reached the map         23,780
```

Units were handed **58,000** paint at spawn and put **23,780** of it onto the map.
78% of them died holding ≤10, so the missing **~34,220 — 59% of everything the
economy produced — went to passive drain**: the −1/turn on neutral, −2 on enemy
(moppers double), and +1 per adjacent allied robot. Not to painting. Not to combat.
To standing in the wrong place while walking around.

(The tower-income counter in the tool is a lower bound — it assumes every paint
tower is level one, and the starting one is level two — so I derive the drain from
the spawn/spend gap instead, which needs no such assumption. Refills that did fire
would only make the drain estimate larger.)

### Correction to my own earlier claim

The starvation entry above priced Castle's losses as "~39,800 paint spent on units
that then died with an empty stash", implying the paint died with them. That is
wrong and I am correcting it rather than leaving it to stand. A starved unit **had
already spent** its stash; the question is on what. This accounting answers it: a
bit over 40% on painting, and nearly 60% on drain. The waste is not the death, it
is the wandering that precedes it. Same root cause, but the mechanism is now exact
instead of rhetorical, and the earlier phrasing overstated the case.

### What this changes

1. **Iteration 8's rationale survives and sharpens.** A unit that walks home and
   refills converts tower paint into more painting instead of more bodies. But the
   lever is not "stop units dying" — it is "stop units paying rent on tiles they are
   not painting".
2. **A new risk for iteration 8, from the adjacency term.** The penalty includes
   +1 per adjacent allied robot, doubled in enemy territory. Units queueing around a
   tower to refill will be adjacent to each other and to the tower's other
   customers, so a refill queue is itself a drain source. If iteration 8 comes back
   flat, this is the second thing to check after the tower-stash question.
3. **A new candidate lever, unqueued and cheaper than either:** reduce drain
   directly. `Nav.navTo` already prefers not to step on *enemy* paint; it is
   indifferent to *neutral*, which costs 1/turn. Preferring ally paint when moving —
   free, no new sensing, a comparison the loop already has in hand — attacks 59% of
   the budget rather than the margin. Recorded here as evidence, not yet a
   hypothesis; it needs its own reachability check (how often is an ally-paint step
   available and not taken?), which is answerable from a replay for no games.

### Where the drain actually comes from — measured, and it is mostly units crowding

Standing census over all 38,616 of our unit-turns on Castle (allied adjacency only;
the first pass counted both teams and overstated it, corrected here):

```
on ally paint    24,664  (63%)   penalty  0
on neutral       10,342  (26%)   penalty -1
on enemy paint    3,610   (9%)   penalty -2
allied neighbours 19,006 total = 0.49 per unit-turn, +1 paint each
off ally paint WITH an ally tile one step away: 12,405 (32% of all unit-turns)
```

Per unit-turn that is 0.44 from territory and 0.49 from adjacency, ~0.93 total,
which over 38,616 unit-turns is ~36,000 — closing neatly against the ~34,220 derived
independently from the spawn/spend gap. Two independent routes to the same number,
so I believe it.

**Our units spend about 19,000 paint standing next to each other. They put 23,780
onto the map.** Crowding costs 80% of what painting costs, and nobody chose it.

Two levers fall out, both with the dose already measured:

1. **Anti-crowding (the larger, ~19,000 paint).** Nothing in the bot considers
   allied adjacency when moving. `Nav` scores candidate steps by direction only.
   Counting allied neighbours at the destination and preferring fewer is a handful
   of bytecodes on data the unit has already sensed.
   *Caveat recorded up front, from TRAINING_ALGORITHM.md's symmetry section: "a
   consistent arbitrary preference can be supplying real formation cohesion that
   pure randomization destroys." Spreading units out may cost ruin-capture tempo or
   splasher massing. This needs the same reachability and trigger-frequency
   pre-checks as anything else, not a straight line from a big number to a change.*

2. **Prefer ally paint when stepping (~17,000 paint, cheaper to reason about).**
   `Nav.navTo`'s first pass refuses *enemy* paint but treats neutral and ally alike,
   and **32% of our unit-turns are spent off ally paint with an ally tile one step
   away** — a free step that was available and not taken. That 32% is the
   reachability check already answered: the branch is live on a third of all turns.

Both are the "capability preserved at zero marginal cost" shape: no new sensing, no
resource spent, pure waste removed. They go in the queue *behind* iteration 8, which
is already built and pre-registered — but ahead of the tower paint reserve, because
their doses are measured and the reserve's is not.

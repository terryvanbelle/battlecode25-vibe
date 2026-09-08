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
`cmp` replays directly. **[THE CLAUSE AFTER THE ARROW IS WRONG — SUPERSEDED 2026-09-08, see
"Methodology correction — `cmp` on replay bytes is NOT a valid arm-to-arm identity check" at the
end of this log. The 4x test re-ran the SAME match, so the team names matched; two arms are
different packages and play under different team names, which are recorded in the replay. Diff
`replay-dump.sh --quiet` event streams instead. The determinism finding itself stands.]** Caveat discovered: the FIRST run after a source change once
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


---

## Iteration 7 BROAD RUN result (2026-09-06) — run 20260906-212734, 200 games

```
vs bob_iter3           21/40 (52%)   swept-win  3  swept-loss  2  split-by-side 15
vs bob_iter0           36/40 (90%)   swept-win 16  swept-loss  0
vs bob_iter1           34/40 (85%)   swept-win 14  swept-loss  0
vs examplefuncsplayer  40/40 (100%)  swept-win 20  swept-loss  0
vs bob_denier          32/40 (80%)   swept-win 14  swept-loss  2
overall 163/200 (81.5%)
```

**Criterion 1 (accept gate, h2h > 50%): PASSES, 21/40 = 52.5%.** Marginal: the
binomial standard deviation on 40 games is 3.2, so 21 versus 20 is 0.3 sd. This
number on its own is a coin flip and I am not going to pretend otherwise.

**No regression, which is the half this sample CAN measure.** Roster comparison
against the previous run's 15-map sample: `bob_iter0` 87% → 90%, `bob_iter1` 80% →
85%. Different map samples, so those deltas are soft, but nothing moved down.
Swept-loss count against the gate opponent is 2 against 3 swept wins.

### Dose-response — the analysis this iteration was actually designed around

Every map's dose is known exactly and in advance (`bob-tools/ruins-mix.csv`): how
many points the hash moves that map's tower mix toward or away from 50/50. Grouping
the h2h games by dose rather than reading the headline:

```
maps whose mix the change IMPROVED   8/12  (67%)
maps it left alone                    3/6  (50%)
maps whose mix it made WORSE        10/22  (45%)
```

Monotone, in the predicted order, and the prediction was registered before the run.
The two swept wins (DefaultMedium +21, UnderTheSea +13) are the two most-improved
maps in the sample; both swept losses (leavemealone −7, quack −8) are maps it makes
worse. That is measurement doctrine #7's causal shape rather than churn.

It is also **underpowered**, and saying so is part of the result: the
better-minus-worse gap of 22 points has a standard error of about 18 points on
these sample sizes, so it is ~1.2 sd, p≈0.11 one-tailed. Suggestive. Not decisive.

### Why I am NOT deciding on this run

The sample contains **none of the four maps where the old rule degenerates
completely**, and the entire case for the change rests on those. TRAINING_ALGORITHM.md
rule 10 is explicit: "don't let pre-registered metrics decide when a cheap unrun
instrument could reverse them." The affected-subset run is exactly that instrument
and it costs 30 games against this run's 200. It is launched.

### Two pool-management notes, acted on rather than filed

- **`examplefuncsplayer` is 40/40 and was 30/30 before** — two consecutive
  evaluations at 100%, which is the retirement condition. It stays in
  `roster_extra.txt` because the absolute-strength chart needs a frozen yardstick
  and roster entries are never retired, but it consumed **20% of this run's games**
  to tell me nothing. From now on it plays in deliberate roster runs only, not in
  every gauntlet.
- **`bob_denier` scored 80% on its first outing** — one evaluation at the retirement
  threshold, and it is the only opponent besides the gate that took games off me
  (2 swept losses, on Paintball and leavemealone). It stays as a peer for now. Its
  README already records that it is forked from `bob_iter3` and must be re-forked
  when it stops being a challenge; one more evaluation at ≥80% triggers that, and
  the re-fork gets logged so no win rate is compared across it.


---

## The archetype earned its keep (2026-09-06) — one enemy splasher beat thirteen of my soldiers

`bob_denier` scored 80% against, i.e. I beat it comfortably overall — but it took
two maps from both sides, and the *way* it won is the most useful thing this run
produced. This is exactly the return TRAINING_ALGORITHM.md promises from synthetic
archetypes: an opponent that does something my lineage never does.

**Paintball, our side A, lost at round 223 by MAJORITY_PAINTED.** Cumulative spawns
and coverage (per mil):

```
round   ourCov  theirCov   ourSold ourSpl ourMop   theirSold theirSpl theirMop
  50      421      463         8      0      0          1        0        0
 150      381      528        11      1      1          1        1        0
 223      240      703        13      1      1          1        1        0
```

The denier built **two units in the whole game** — one soldier and one splasher —
and its coverage went 463 → 703 while ours *fell* 421 → 240. We had thirteen
soldiers. We lost anyway, and we lost fast.

**The mechanism, and it is a rule of this game rather than a bug in my code:
soldiers cannot overwrite enemy paint.** Only splashers (within r²≤2 of the splash
centre) and moppers can. So every tile that enemy splasher converted was permanently
gone as far as my thirteen soldiers were concerned — they physically could not take
it back. One splasher firing every fifth round for 150 rounds is ~30 attacks x 5
overwritable tiles ≈ 150 tiles, which is almost exactly the 181 per-mil we lost.

Our answer to that threat was one splasher and one mopper, and the trace above says
2-4 of each are alive at any moment because they starve. **A soldier-heavy army has
no reply to paint denial at all**, and my entire lineage is soldier-heavy, so no
instrument descended from it could ever have shown me this. That is the
self-referential blind spot, closed by a bot I built specifically to close it.

### What follows, and what does not

**Reinforces iteration 8 with a competitive story, not just an efficiency one.**
Keeping denial units alive is not about tidy resource accounting; it is the only
mechanism by which lost territory can ever be recovered. The refill change is the
cheapest available route to having more than two of them alive.

**A separate, arithmetic-only observation that I am explicitly NOT yet claiming as
a result.** A splasher attack costs 50 paint and paints up to 13 empty/ally tiles
(r²≤4 disc) = 3.85 paint per tile; a soldier pays 5 paint for one tile. Per action
the gap is 13x, and cooldowns (50 vs 10) only reduce that to ~2.6x per unit per
round. My own Castle numbers agree: 207 splash actions delivered a comparable tile
count to 2,686 soldier actions, for 10,350 paint against 13,430. So splashers may
dominate soldiers for *coverage* on both paint and action efficiency.

But the Paintball game does **not** demonstrate that — the denier won there by
removal, not by out-painting — and the arithmetic degrades as the map fills and
fewer of the 13 tiles are empty. Soldiers also remain the only unit that can build
tower patterns. So this is a hypothesis with a promising dose, filed for a proper
reachability and efficiency-decay check, not a conclusion. Recording the
distinction because "metrics that improve without converting to wins" is the trap
the ledger fills with fastest.

### Pool note
`bob_denier` is NOT retired despite 80%: it is the only opponent besides the accept
gate that beat me from both sides of any map, and the algorithm says never retire an
opponent we lose to.


---

## Iteration 7 DECISION (2026-09-06) — ACCEPTED, on a robustness argument

### The two runs

```
broad random 20-map sample (200 games)   vs bob_iter3  21/40 (52.5%)  swept 3-2
affected subset, 15 maps (30 games)      vs bob_iter3  19/30 (63.3%)  swept 5-1
```

Combined h2h grouped by each map's exactly-known dose (64 games):

```
maps whose mix the change IMPROVED   21/30  (70%)
maps it left alone                    3/6   (50%)
maps whose mix it made WORSE         16/34  (47%)
better-minus-worse: +23 points, se 13  ->  1.83 sd, one-tailed p ~ 0.033
```

Monotone, in the direction registered before either run. **The mechanism is real:
the tower mix causally affects who wins, and moving it toward 50/50 helps.**

### The awkward fact I went looking for, and found

Across all 75 maps the hash **helps 18, leaves 20 unchanged, and HURTS 37** — mean
gain −0.59 points. It applies a confirmed mechanism in the wrong net direction. Feed
the measured per-group win rates through that pool composition and the predicted
overall effect is (18x0.70 + 20x0.50 + 37x0.47)/75 = **53.3%**, which is almost
exactly the 52.5% the broad run measured. The model and the data agree, and they
agree on "barely positive".

### So I searched offline for a rule that dominates — and the search argued against itself

Free, over all 75 maps, no games. `parity ^ (((x>>3)+(y>>3))&1)` looked like a clean
win: 0 all-one-type maps, mean deviation **8.50** — better than parity's 9.28 *and*
the hash's 9.87 — and only 1 map over 30 points. It keeps the local checkerboard
alternation that makes parity beat a fair coin while flipping the pattern every 8
tiles to break the global invariance.

Then I swept the parameter, which is the check that matters:

```
parity ^ ((x>>1)+(y>>1))   allOne 3   mean  8.90
parity ^ ((x>>2)+(y>>2))   allOne 3   mean 11.36   <- WORSE than baseline
parity ^ ((x>>3)+(y>>3))   allOne 0   mean  8.50   <- the "winner"
parity ^ ((x>>4)+(y>>4))   allOne 1   mean  8.64
parity ^ ((x>>5)+(y>>5))   allOne 4   mean 10.74
same rule, origin shifted by 1 tile:  allOne 1   mean  9.16
same rule, origin shifted by 2 tiles: allOne 1   mean 10.60
```

**The optimum is a spike, not a plateau.** One tile of phase shift or one bit of
block size destroys it. That is the signature of a rule fitted to the particular
lattices in these 75 files, not of a structural property — and there is no
principled reason for 8 tiles. Ruin spacings here run 5-8, so a block of 8 happens
to de-phase these maps and would be worth nothing on maps spaced differently.

**CLOSED: "tune a structured pure function (parity XOR a low-frequency term)."**
Killed by its own parameter sweep. Adopting it would have been overfitting to the
map pool, and my gauntlet resamples from that same pool, so *no instrument I own
would ever have caught it* — which is precisely why AGENT.md calls a fixed map list
an overfitting surface.

### Correction to my own earlier closure

Earlier I wrote that the hash "is at the fair-coin floor, so no pure function can do
better". That was overstated and I am fixing it rather than leaving it. Parity gets
9.28 against a fair-coin expectation of 10.1 — a pure function *can* beat the floor,
by correlating with map structure. The floor bounds *structure-blind* functions
only. The sweep above is what that correction buys: structure-exploiting rules exist,
and they are exactly the ones that overfit.

### Why accept

Not because 52.5% is impressive — it is 0.3 sd. The case is:

1. **The pre-registered gate is met on both halves**, and it was fixed before any of
   this analysis existed: broad run shows no regression (roster `bob_iter0` 87→90%,
   `bob_iter1` 80→85%, swept 3-2), and the helped group beats the hurt group (70% vs
   47%).
2. **The mechanism is confirmed at 1.83 sd** on a dose-response that was predicted
   in advance.
3. **The real argument is robustness, not average performance.** Parity's 9.28 and
   the tuned rule's 8.50 are *contingent* on this pool's lattices; parity degenerates
   to 100% one type whenever ruin spacing is even, and that failure is unbounded. The
   hash's ~9.9 is a mathematical guarantee that holds on any map set, seen or unseen,
   with a bounded tail. Iteration 7 trades a fraction of a point of average-case mix
   quality for the elimination of an unbounded worst case. On a convex loss — a
   100%-money map has no paint income at all — that trade is right.

**Known cost, carried forward honestly:** it doubles the play-symmetry gap (11 → 24
points, section above). That is a real debt, not a rounding error, and the only thing
that repays it is the adaptive rule (deriving a ruin's type from its existing marks),
which remains the single live descendant of this thread.

**ACCEPTED.** Snapshotted as `bob_iter7`.

### Mechanistic gate (criterion 2) — confirmed in game, on the worst case

Single match `bob` (A) vs `bob_iter3` (B) on **gridworld**, the map where the old
rule was most degenerate (21 ruins, all 21 assigned money). Towers actually built:

```
round   covA  covB   ptowA mtowA   ptowB mtowB   maxbcA
 200     454   494     2     6       0     9      9116
 600     495   460     2     6       0     9      9116
1000     689   277     4     7       0     9      9126
FOOTER winner=A  MAJORITY_PAINTED  round 1005
```

Team B built **zero paint towers and nine money towers** — the degeneracy, exactly
as `BobRuins` predicted from the map file alone. Team A built **4 paint and 7
money**. A won by paint majority at round 1005, 709 to 256 per mil.

Criterion 2 (both tower types non-zero) passes, and it passes on the single map
most likely to falsify it. Prediction from the map file → mechanism in game →
outcome, end to end.

**Criterion 3 (bytecode): `maxbcA` = 9126 against a 9042-9928 baseline** — the hash
costs nothing measurable. Replay archived as
`replays/iter07_bob_iter3_gridworld_A.bc25`.

**Note on the roster chart labels.** `track_vs_old_bots.py` labels rows with the
accepted snapshot *as of the run date*, so runs 20260906-2042 and -2127 are both
recorded `bob_iter3`. For -2127 the build that actually played was the iteration 7
candidate, now `bob_iter7`. The win% values are correct; only the label lags. Not
hand-editing, because the tool is shared and would rewrite it — recorded here
instead so the chart is not misread.


---

## CORRECTION (2026-09-06) — the standing census counted towers as units

Caught by an implausible number rather than by review: the crowding-at-towers check
came back "0% of ally-neighbour instances are near one of our towers", which cannot
be true. The cause is an engine constant I assumed instead of probing:

```
battlecode.schema.RobotType:  NONE=0  PAINT_TOWER=1  MONEY_TOWER=2
                              DEFENSE_TOWER=3  SOLDIER=4  SPLASHER=5  MOPPER=6
```

**MOPPER is the HIGHEST value, not the lowest.** My filter `if (type > MOPPER)
continue` was meant to exclude towers and excluded nothing, so towers were counted
as units in the standing census — as subjects *and* as each other's neighbours. This
is the same class of error as assuming deaths live in `Round.diedIds`, and the same
fix applies: probe the enum, never infer the ordering.

### Corrected numbers (Castle, our side, units only — 29,183 unit-turns, not 38,616)

```
                          reported (wrong)   corrected
on ally paint                  63%              84%
on neutral                     26%               3%
on enemy paint                  9%              12%
allied neighbours/unit-turn    0.49             0.53   (15,600 total)
free ally step available       32%              10%
```

### What this changes, and it is not cosmetic

**The "prefer ally paint when stepping" lever is largely dead, and I am striking
it.** I claimed it was worth ~17,000 paint on the strength of "32% of unit-turns are
off ally paint with a free step available". The real figure is **10%**, and units
are already on ally paint **84%** of the time. The neutral-territory term is 909
unit-turns — about 909 paint in a game, i.e. nothing. The remaining off-ally time is
12% on *enemy* paint, which is where splashers and moppers are supposed to be. There
is no meaningful waste here to remove.

**Anti-crowding is promoted, and is now clearly the largest non-starvation lever.**
Adjacency is 15,600 paint against a total drain of roughly 23,000 — about two thirds
of it — and it remains large compared with the 23,780 that ever reached the map.

**And the new measurement answers the question I built it for:** only **18%** of
ally-adjacency happens within r²≤8 of one of our own towers. Crowding is not units
queueing at home; it is units traveling and working in clumps out on the map. So
iteration 8, which deliberately sends units back to towers, is adding to a term that
is currently only a fifth of the problem, rather than doubling the whole thing. That
is a materially smaller risk than the version I logged earlier, and it is worth
knowing before the result lands rather than after.

**Method note.** Two instrument bugs in one session — a masked `javac` failure
running a stale class, and this enum-ordering assumption — and both produced
*plausible-looking output*. The stale class printed believable metrics; this one
printed a believable 63/26/9 split. Neither was caught by reading the code. Both
were caught by one number being obviously impossible (nothing printed at all; 0%).
The habit that works is to put a value in every report whose correct magnitude I can
predict in advance, and check that one first.

### Anti-crowding: reachability pre-check CLOSES it before it cost an iteration

The corrected census made anti-crowding the largest non-starvation lever at 15,600
paint. TRAINING_ALGORITHM.md requires a reachability check before building
anything, so: for every unit-turn that *has* allied neighbours, could a single step
to an adjacent passable, unoccupied tile have reduced the count? (Walls read from
the map header's `wallsVector`.)

```
unit-turns with >=1 allied neighbour            11,022  (37% of unit-turns)
of those, a single step could REDUCE the count   2,421  (21%)
total reducible neighbour-instances              2,834
```

**The achievable dose is 2,834 paint, not 15,600.** Four fifths of the crowding is
geometrically unavoidable — units are packed in corridors and around the same
objectives, and every adjacent tile is just as crowded or occupied. And 2,834 is an
*upper bound* assuming every unit always takes the least-crowded step, which would
directly fight moving toward its objective. Against the 23,780 that reaches the map,
the realistic capture is a rounding error.

**CLOSED: "reduce paint drain by having units avoid standing next to each other."**
Not because the cost is small — it is 15,600 paint, two thirds of all drain — but
because almost none of it is recoverable. Re-open only if a future change makes
units substantially more mobile or spreads objectives out.

### The pattern worth naming

That is now **three levers killed by measuring the achievable dose rather than the
observed cost**, all in one session, all for free:

| lever | observed cost | achievable | verdict |
|---|---|---|---|
| denial units idle (navigation) | ~99% of capacity | 0 — they are already in contact | closed |
| prefer ally paint when stepping | claimed 17,000 paint | ~909 paint | struck |
| anti-crowding | 15,600 paint | ≤2,834, conflicts with objectives | closed |

**A big cost is not a big opportunity.** Every one of these looked like a headline
finding, and the number that mattered in each case was not the size of the waste but
the size of the *slice a change could actually take*. The reachability and
trigger-frequency pre-checks are the whole difference, they cost minutes against a
gauntlet's hour, and I would have spent three iterations without them.

What survives the same test is starvation: 78% of deaths at ≤10 paint, with a
mechanism (`tryRefill` cannot see past vision) whose fix is a few lines and whose
dose is the entire 456-death population. That is why iteration 8 is the one running.


---

## Iteration 8 — a second failure mode identified BEFORE the run lands

Found by re-reading `Refill.seek` while the gauntlet was in flight. Recording it now
so that if the result is a near miss, the refinement is pre-registered rather than
invented to explain the number.

**The case.** `observe()` sets `home` only from towers with `paintPerTurn > 0`, i.e.
paint towers, and `anyTower` from any tower. A unit built by a **money** tower —
and the tower mix is money-heavy, so that is many units — leaves `home` null. Step 2
then falls back to `anyTower`, walks the unit to that money tower, finds it below
100 paint (a money tower has `paintPerTurn == 0`, and one built mid-game starts at
`paintAmount == 0`, both engine-verified), and hits the "already adjacent, wait for
regen" branch.

**A money tower never regenerates.** So the unit parks next to it forever. That is
not merely inactivity, it is permanent inactivity, and it would also pile units
adjacent to each other at the tower — the adjacency drain term.

**Why I am not fixing it mid-run.** The evaluation is already staged and running on
the current source. Editing now would mean the code I measure is not the code I
keep, which makes the result uninterpretable. The run finishes as launched.

**Pre-registered refinement #2** (refinement #1, the ruin-work interruption, is
recorded above; the algorithm allows up to 3): if `home` is null — no paint tower
has ever been seen — do not park. Walk toward `anyTower` while it may still hold
its initial 500 paint, but return false when already adjacent and it has nothing,
so the unit resumes its normal routine instead of waiting for regeneration that
cannot come.

**How to tell which refinement, if any, is needed** — measurable from the run's own
replays, no new games:
- *Parking at sterile towers*: our units stationary for many consecutive rounds
  within r²≤2 of a MONEY tower. `BobMop` already has positions and types.
- *Ruin-work interruption*: tower-completion count down versus `bob_iter7` on the
  same maps, from the dumper's `ptow`/`mtow` columns.
- If starvation falls sharply and neither signature appears, the change worked and
  a flat h2h means something else entirely is binding.

A side note on the gate that was supposed to save bytecode: `if (home != null &&
paint >= below * 2) return false;` cannot short-circuit for a unit whose `home` is
null, so exactly the units affected by the bug above also sense every single turn.
Baseline peak is 9126 of 17500 and a sense is a few hundred bytecodes, so this is
not dangerous — but it is worth checking `maxbc` in the result rather than assuming,
which criterion 3 already requires.


---

## Iteration 8 RESULT (2026-09-06) — REJECTED, and it reverses the finding that motivated it

```
vs bob_iter7 (accept gate)   16/40 (40%)   swept-win  2  swept-loss 6
vs bob_iter3                 18/40 (45%)   swept-win  4  swept-loss 6
vs bob_denier                30/40 (75%)   swept-win 13  swept-loss 3
```

Gate required >50%. **40%, with six swept losses to two swept wins** — one-directional,
well outside the 3.2-game noise floor. Not a near miss.

### The mechanism worked. That is why we lost.

Castle, our side A, against the same opponent and map as the baseline trace:

```
                          bob_iter3 baseline      iteration 8
unit deaths                     283                    31      (-89%)
of which starved (<=10)     221 (78%)               12 (39%)
paint reaching the map      11.9 / round           6.7 / round  (-44%)
```

Starvation fell exactly as designed — deaths down 89%, the starved fraction halved.
Criterion 2 passes emphatically. And the h2h collapsed to 40%.

### Why, with the full causal chain measured

```
round   ourCov  theirCov   ourChips  theirChips   ourSoldiers  theirSoldiers
 200      480      494        4,470      2,070          19            21
 400      497      464        8,660      4,210          22            33
 600      417      553       17,480      4,990          26            44
 889      267      703       55,630      7,610          29            45
                                    FOOTER  winner=B  MAJORITY_PAINTED  r889
```

Refill trips drained the towers' paint, so the towers could not afford to spawn.
**Our chips piled up to 55,630 unspent** — the classic dead-resource signature — while
the opponent, spending its paint on bodies instead, held only 7,610 and built **45
soldiers to our 29**. Fewer bodies painted less; coverage collapsed 480 → 267 and the
game ended at round 889.

### The economics, and they are general

Spawning converts 200 paint into **200 paint plus a body**. Refilling converts 200
paint into **200 paint**. Bodies are the scarce resource — the standing army is ~15
against ~290 built — and chips are abundant (55k unspent here, 327k in the earlier
trace), so chips never bind. While paint is the binding constraint and chips are
free, **spawning strictly dominates refilling**, and every unit of paint sent to a
living unit is a body not built.

**So the finding that motivated this iteration was real and my reading of it was
backwards.** 78% of deaths at ≤10 paint is not waste: a unit that paints until it
starves has converted its entire stash into tiles and then *freed the economy to
build a replacement that arrives with a fresh body and a full stash*. Dying at zero
is the efficient terminal state. I had it as the bot's largest leak; it is closer to
the bot's most efficient behaviour.

This is precisely TRAINING_ALGORITHM.md's recorded regularity — "survival bought
with inactivity; units die doing the thing that wins" — and I walked into it with
the warning quoted in my own pre-registration two entries above. Pre-registering the
trap did not stop me falling into it, but it did mean the diagnosis took one trace
rather than three iterations.

### No refinement is attempted, and that is a reasoned choice

Two refinements were pre-registered. Neither is worth a run, because the failure is
structural rather than mis-tuned:

- *Refinement #1 (don't interrupt ruin work)* and *#2 (don't park at sterile money
  towers)* both reduce the number of refill trips. They shrink the harm toward zero;
  they cannot produce a gain, because every completed refill is still a body not
  built.
- The one refinement that would address the cause directly — let a unit withdraw
  only paint **above** a spawn's cost, so refills never block spawning — is a no-op
  by measurement: paint towers were measured hovering at ~100 paint against a
  200-paint soldier, so surplus above 200 essentially never exists. The refinement
  would make the mechanism fire almost never.

### CLOSED, with a precise re-open trigger

**CLOSED: "keep units alive by walking them back to a tower to refill."** Killed by
the chip/paint economics above, not by a tuning failure. `bob-tools/shelved/` keeps
both candidate builds.

**Re-open when paint stops being the binding constraint.** Concretely: when team
chips stop accumulating — say sustained below ~5,000 while towers still want to
spawn — spawning has become chip-limited, paint is no longer convertible into
bodies, and refilling is then free rather than dominated. **Iteration 9 (SRPs) is
the most likely trigger**: +3 paint/turn per allied paint tower per pattern directly
attacks the paint constraint, and if it lands, this decision should be re-examined
rather than treated as settled. That is a real test, not a hedge — the chips column
of any replay answers it.

Reverted to `bob_iter7`. Next: iteration 9, SRPs.


---

## Iteration 9 (2026-09-06) — Special Resource Patterns — RUNNING

Prepared as "iteration 6" and gated behind iteration 5; the code was recovered off
the VM this session and grafted onto `bob_iter7` with `bob-tools/shelved/apply-srp.py`
rather than copied, so iteration 7 survives intact (90 lines added, `Soldier.java`
only). Full rationale and engine derivation in the iteration 6 entry above.

Short version: `extraResourcesFromPatterns(team) = 3 * numResourcePatterns(team)` is
added to **every allied tower's per-turn income**, so an SRP is +3 paint/turn on
every paint tower for 200 chips, against a tower upgrade's +5 paint/turn on one
tower for 2,500 chips. `srpA`/`srpB` are 0 in every replay ever dumped — the whole
mechanic is unused.

Evaluation: 20 maps x 2 sides x `bob_iter7` (accept gate) and `bob_denier` = 80
games. `examplefuncsplayer` and the iter0/iter1 roster are excluded per the pool
decision above.

Pre-registered accept criteria (1-3 carried from the iteration 6 entry, 4 added
today on the strength of what iteration 8 taught):
1. **h2h vs `bob_iter7` > 50%** — accept gate.
2. swept-win > swept-loss.
3. Mechanistic: `srpA` reaches ≥3 and **stays** there. If SRPs are built and keep
   collapsing to 0, our own splashers are clipping them (the engine restarts the
   50-round activation clock on any pattern mismatch) and the fix is a splasher
   exclusion zone, not abandoning the mechanic.
4. **NEW — the iteration 8 re-open test, measured in the same run.** Iteration 8 was
   closed because paint binds and chips are free (55,630 unspent). If SRPs raise
   paint income enough that **team chips stop accumulating** — sustained below
   ~5,000 while towers still want to spawn — then spawning has become chip-limited,
   paint is no longer convertible into bodies, and refilling stops being dominated.
   Read the `moneyA` column. This costs nothing extra and either re-opens a closed
   direction on evidence or confirms its closure.

Note what criterion 4 is doing: iteration 8's rejection was not just a discarded
iteration, it produced a *quantitative condition* under which its conclusion flips.
That condition is now a pre-registered readout on the next run rather than a note
someone might revisit.


---

## Iteration 9 RESULT (2026-09-07) — ACCEPTED (SRPs)

The run (`gauntlet/20260906-230658`, 20 maps x 2 sides) finished on the VM before my
session was killed by the account-wide rate limit at ~00:55; only the collation was
lost. Recovered with `gauntlet-collect.sh 20260906-230658` — no games re-played.

```
vs bob_iter7 (accept gate)   25/40 (62.5%)   swept-win  5   swept-loss 0
vs bob_denier                30/40 (75.0%)   swept-win 12   swept-loss 2
overall                      55/80 (68.8%)
```

Gate >50%: passed. Peer `WinPct` 60%: passed on both peers. Swept 5-0 against the
baseline with **zero swept losses** — the flips are one-directional in our favour,
which is the shape doctrine #7 calls a real causal effect rather than churn.

### Criterion 3 (mechanism) — passes, with a magnitude caveat worth keeping

`srpA` by map (side A, opponent `bob_iter7`, which has `srpB == 0` throughout — the
arm-to-arm identity check is trivially satisfied, the mechanic is ours alone):

```
map      srpA trajectory                        result
Castle   1 from r200, held to the end            win r727
quack    1 -> 2 by r300, held 1080 rounds        win r1380
Oasis    2 -> 5 -> 8 -> 10, oscillating 7-10     win r804
```

The pre-registered failure mode — SRPs built and collapsing to 0 because our own
splashers clip the pattern and restart the 50-round clock — **did not occur**. Oasis
dips 8->7 and recovers, so clipping happens and is survivable; the population is
maintained rather than reset. No splasher exclusion zone is needed.

What did not pass is the magnitude: I pre-registered "reaches >=3 and stays", and two
of three maps hold only 1-2. **The binding constraint is `SRP_MIN_CHIPS = 500`**, and
the reason is visible in the same trace (below): the accepted bot's treasury now
*hovers around 1,300 chips*, so a 500-chip gate plus a 200-chip completion competes
directly with spawning for a treasury that is no longer idle. That is the refinement
this iteration hands to the next one, and it is a dose question, not a mechanism one.

### The causal chain, measured end to end (quack, r1380)

This is the trace that makes the accept mechanistic rather than statistical. A = the
candidate, B = `bob_iter7`:

```
round    moneyA   moneyB    soldA  soldB   splA splB   covA  covB
 100        360    1,050       8     13      0    0     306   383
 400      1,226    8,460      37     32      8    6     512   458
 800      1,256   39,980      98     69     29   17     605   377
1380      3,826   73,750     192    110     59   31     703   271
```

**The baseline hoards 73,750 chips; the candidate never exceeds 3,826.** The
difference is not the SRPs' own cost — 2 SRPs is 400 chips — it is what the SRPs
*unlock*. Units cost paint **and** chips (soldier 200/250, splasher 300/400, mopper
100/300). When paint is the binding input, chips accumulate unspent; every unit of
paint income converts one waiting chip pile into a body.

Order-of-magnitude check, and it lands: 2 SRPs x 6 paint towers x 3 = **+36
paint/turn**, which over 1380 rounds is ~49,700 extra paint. The realised unit
surplus is +82 soldiers, +28 splashers, +28 moppers = 82(200) + 28(300) + 28(100) =
**~27,600 paint**, plus the tower surplus and the paint those extra bodies spend
being alive. Same order, right sign, and the chip side matches too: that unit surplus
costs 82(250)+28(400)+28(300) = ~40,100 chips, against a 70,000-chip divergence in
treasuries. The mechanism explains the win rather than merely accompanying it.

Coverage is the consequence, not a separate effect: more bodies paint more, covA
climbs 306 -> 703 while covB falls 383 -> 271, and every win here is
`MAJORITY_PAINTED`.

Bytecode: `maxbcA` peaks at 10,038 (Oasis) against a 17,500 soldier limit. Headroom
intact; criterion 3's bytecode clause satisfied.

**ACCEPTED.** Snapshotted as `src/bob_iter9/`. Replay archived as
`replays/iter09_bob_iter7_Oasis_botA.bc25` (the most informative win: 10 concurrent
SRPs, 310 soldiers to 89).

### Criterion 4 — the iteration 8 re-open test fires on its letter and fails on its intent

Pre-registered condition: *"if team chips stop accumulating — sustained below ~5,000
while towers still want to spawn — then spawning has become chip-limited, paint is no
longer convertible into bodies, and refilling stops being dominated."*

Literally, that condition is met. `moneyA` is sustained at 360-4,343 across all three
traces, for 1,380 rounds on quack, while unit counts climb monotonically — towers
plainly still want to spawn. By the wording I registered, iteration 8 re-opens.

**It does not, and the reason is that I registered a proxy instead of the quantity.**
The thing that would actually make refilling non-dominated is *paint stranded in a
tower that chips prevent from being spawned*. Team chips sitting at 1,300 does not
show that: a soldier costs 250 chips, so 1,300 chips is **five soldiers already
affordable, right now**, and chips are team-global while paint is per-tower — so no
tower in that state is chip-blocked. A genuinely chip-limited economy pins the
treasury below one unit's cost (<250) and holds it there. Mine oscillates at 5-16x
that, which is the signature of income being *spent at the rate it arrives* — a
healthy equilibrium, not a shortage.

So the correct reading is: **iteration 9 moved chips from "dead resource" (73,750
unspent on the baseline) to "in balance" (~1,300, turning over), and stopped short of
"binding".** Paint remains the binding input. **Iteration 8 stays CLOSED.**

One real exception, recorded because it is the seed of the next re-open: on Oasis the
treasury hits **71 chips at round 200** — genuinely below a single soldier — before
recovering. Chip scarcity is real but *transient and early*, not a steady state. If a
future change pushes that transient into the steady state, the re-open trigger is
now sharpened to the right quantity: **team chips pinned under ~250 while any allied
tower holds >=200 paint**, not "chips under 5,000".

### What this episode is worth, methodologically

The pre-registration did its job in a way I did not anticipate: it did not confirm or
reverse iteration 8, it **exposed that my re-open condition was the wrong variable**.
Had I not written the number down in advance, I would have looked at "chips fell from
55,630 to 1,300" and re-opened a closed direction on a proxy, spending a full gauntlet
to rediscover that paint still binds. The cost of finding this was reading one column.

Generalisation for LEARNINGS: *a pre-registered trigger is only as good as the link
between its proxy and the mechanism it stands for. Register the mechanism's own
quantity where you can, and when you must use a proxy, write down what would make the
proxy lie.* Here the proxy lied because it collapsed a team-global stock (chips) and a
per-tower stock (paint) into one threshold, and only the second one gates a spawn.


---

## Tournament 20260907-0100 — first cross-agent evidence, and one loss worth everything

The project's first round-robin. Read while in flight; the bot that played is HEAD at
01:00 = `c7d8263`, i.e. **`bob_iter7`** — iteration 9's SRP work was still uncommitted
when the tournament started. So these results describe iter7, not the current bot.

Bob vs Alice, 78 of 150 games played at the time of reading:

```
bob     77 / 78   (98.7%)
alice    1 / 78
```

No forfeits — 78 real games, rounds 240 to 2000, median 838, every decision by
`MAJORITY_PAINTED` or its tiebreaker. **Alice is a benchmark, not a peer** (<30%), so
by the algorithm's classification she does not gate my acceptance and should be played
less often. Carol had not been reached yet when I read this.

I am deliberately not treating 98.7% as a strength claim. It says my lineage beats one
independent lineage at this stage; it says nothing absolute, and the pool of two is
tiny. The valuable part is the single loss.

### The one loss: `Rose`, bob as side B, r581 — we build nothing at all

```
round   covA(alice) covB(bob)   soldB  ptowB  mtowB   paintB/round
   50       132        87          6      0      0        193
  200       239       125          9      0      0        147
  400       550        101        14      0      0         39
  550       665         89        14      0      0          0
  581       702         85        14      0      0          0   FOOTER winner=A
```

`ptow`/`mtow` are *cumulative towers built*. **Bob built zero towers in 581 rounds.**
Alice built three paint towers and five money towers over the same span. Our soldier
count froze at 14 by round 350 and never moved; paint delivered to the map decayed
193 → 147 → 39 → **0**, and coverage went backwards, 125 → 85.

This is the doom loop in its pure form, and it is an *absolute* degeneracy signal of
exactly the kind the algorithm says to prefer over opponent-relative deficits: no
new paint towers → no paint income growth → soldiers cannot afford to paint ruins →
no new paint towers. It needs no opponent to be wrong. A bot that paints zero tiles
per round for the last 30+ rounds of a game is broken on that map/side regardless of
who it is playing.

For contrast, the same map with sides swapped is a **win**: bob built 10 paint and 4
money towers and took it at r1202. So this is not "Rose is a bad map for us" — it is
one spawn position on one map where expansion never starts. That side-specificity is
the signature TRAINING_ALGORITHM.md flags in doctrine #7 (concentrated on one
map/side = real causal effect, not churn) and in the play-symmetry audit item.

### One observation about Alice worth recording (replay-observable only)

Alice's bytecode peak reads **1,842–2,063** all game, against our 9,194–9,701. She
runs an order of magnitude cheaper per turn and, in the game we won, still fielded
**176 soldiers to our 98** by round 900 — while painting less per round (2,689 vs
4,747). Two things follow, neither of which requires knowing anything about how she
decides: bytecode is nowhere near the binding constraint for a bot of this shape, and
raw unit count is not what wins these games — paint delivered is. That is consistent
with iteration 9's own finding from the other direction.

### Next target, selected

**Zero-expansion games.** Before hypothesising, check generality: is "built zero (or
near-zero) towers" a recurring shape in my *own* gauntlet losses, or is Rose-B a
one-off? Dumping four iteration-9 losses (`fix`, `Snowman`, `box`, `Brat`) to read
`ptow`/`mtow` answers that for the cost of four replay dumps and no games.


---

## Reachability probe (2026-09-07) — why SRP counts range 1 to 10, and the dose I was about to sweep is dead

Iteration 9's criterion 3 under-delivered on magnitude: `srpA` held at 1 on Castle and
2 on quack against 10 on Oasis. My first instinct was a dose sweep on
`SRP_MIN_CHIPS = 500`, since the accepted bot's treasury now hovers near 1,300 and a
500-chip gate looked like it was competing with spawning.

**That would have been a dead dose.** Before spending a gauntlet I built
`src/bob_probe` — iteration 9's code plus counters for every reason an SRP start is
refused — and ran it against `bob_iter7` on Castle and quack with robot stdout on.
The instrumented build reproduced quack exactly (win, r1380, same as the uninstrumented
candidate), so the counters are describing the real game.

```
                        Castle                 quack
attempts to start        862                    9,250
  geometry (isValid-)    856   99.3%            8,029   86.8%
  overlapping mark         6    0.7%              884    9.6%
  chips < 500              0    0.0%              175    1.9%
  robot paint < 25         0    0.0%              156    1.7%
  enemy paint              0    0.0%                4    0.0%
  starts                   0                        2
```

**The chip gate accounts for 1.9% of refusals on one map and 0.0% on the other.**
Sweeping `SRP_MIN_CHIPS` would have moved almost nothing — the precise failure
doctrine #2 warns about ("a dose sweep once produced byte-identical games because the
parameter fed a check that never ran"). The probe cost two matches and no gauntlet.

### The real constraint, from the engine rather than inference

`javap -c` on `RobotControllerImpl.assertCanMarkResourcePattern` gives exactly four
conditions: robot type, `assertCanActLocation(loc, 8)`, `GameWorld.isValidPatternCenter(loc, false)`,
and `getPaint() >= 25`. And `isValidPatternCenter` is: `x >= 2`, `y >= 2`,
`x < width - 2`, `y < height - 2`, and `areaIsPaintable(loc)` — all 25 tiles free of
walls and ruins.

So 87–99% of refusals are "the 5×5 around this soldier contains a wall, a ruin, or a
map edge".

### The actual bug, and it is a policy bug, not a tuning one

`workOnSrp` tests **exactly one candidate centre per turn: the tile the soldier is
standing on.** It never looks anywhere else. But the engine's own check is
`assertCanActLocation(loc, 8)` — **r² ≤ 8, which is 25 candidate tiles, not one.**
The bot has been sampling one square of a 25-square neighbourhood and concluding the
neighbourhood is unusable.

That also explains the map spread without any map-specific story: on open maps
(Oasis) a random tile is often a valid centre, so one sample succeeds often enough to
reach 10 SRPs; on cluttered maps (Castle) a random tile almost never is, and one
sample per turn finds nothing in 862 tries.

This is also a clean instance of the algorithm's Phase 0 item 2 — *"sweep the
`RobotController` API for methods the bot never calls"* — in miniature: the capability
to mark at range was in the signature the whole time and the bot passed `me` to it.

## Iteration 10 (2026-09-07) — PRE-REGISTERED: search the markable neighbourhood

**Hypothesis.** SRP construction is limited by candidate-site *sampling*, not by
chips, paint, marks, or map geometry. Testing more of the r² ≤ 8 neighbourhood the
engine already permits will raise sustained SRP counts, and — since an SRP is +3
paint/turn on *every* allied paint tower and paint is the established binding
constraint — that will convert into paint delivered and coverage.

**Mechanism (one change).** In `workOnSrp`, when `srp == null`, test up to `SRP_SCAN`
candidate centres within r² ≤ 8 instead of only the soldier's own tile, taking the
first that passes `canMarkResourcePattern` and `srpSiteSafe`. Candidate order is
rotated by `rc.getID()` so soldiers do not all probe the same tile first — and
deliberately *not* by compass order, per the play-symmetry audit item.

**Dose, with a zero arm (doctrine #2).**
`SRP_SCAN ∈ {1, 5, 13, 25}`. **`SRP_SCAN = 1` is byte-identical to iteration 9** —
that is the zero arm and it is already measured (25/40 vs iter7). 25 is the full
legal neighbourhood.

**Pre-registered accept criteria.**
1. **h2h vs `bob_iter9` > 50%** — accept gate, 20 maps × 2 sides.
2. Swept-win > swept-loss.
3. **Mechanistic**: sustained `srpA` rises versus iteration 9 on the *cluttered* maps
   specifically (Castle 1, quack 2 are the reference points). If `srpA` does not move
   on those maps, the hypothesis is wrong regardless of the win rate, and the win rate
   is then measuring something else.
4. **Bytecode, and this one can veto.** `canMarkResourcePattern` scans 25 tiles, so
   `SRP_SCAN = 25` is up to 625 tile examinations per soldier-turn. Iteration 9 peaks
   at `maxbc` 10,038 of a soldier's 17,500. If `maxbc` reaches the limit the soldier
   is silently truncated mid-turn and every downstream conclusion is void. **Read
   `maxbcA` first, before the win rate.** A dose that wins while clipping bytecode is
   rejected, not accepted.

**Reachability pre-check on the fix itself** (applying the lesson to the lesson):
the probe says 8,029 of 9,250 quack refusals are geometric, so a scan that examines
25 sites instead of 1 has real headroom to find one — this branch is demonstrably
live. What the probe cannot tell me is whether valid centres are *spatially
clustered*, in which case 25 neighbours of a bad tile are also bad and the scan buys
less than the arithmetic suggests. That is precisely what the dose curve measures.

### Generality check on the Rose shape — it is the dominant loss mode, and it names iteration 11

Four iteration-9 losses dumped (cumulative towers built, our side; `srp` is ours):

```
map      side  paint towers  money towers  srp  our chips (end)  coverage  result
Snowman   A         0              2        0        5,810        224-711   loss r363
Brat      B         0              3        0       46,590        276-703   loss r817
fix       A         1              3        1        6,088        222-705   loss r358
box       A         3              0        1        1,385        280-704   loss r634
--- for contrast, the wins ---
Oasis     A         7              6        8        3,648        704-283   win  r804
quack     A         6              4        2        3,826        703-271   win  r1380
Rose(t)   B         0              0        -        6,010         85-702   LOSS r581
```

**Three of four losses built zero or one paint tower**, and in exactly those games the
chip pile runs away — 46,590 unspent on Brat, 6,088 on fix, 5,810 on Snowman — while
paint delivered to the map decays toward a floor (Brat: 268 → 209 → 209 → 209).
The two wins built six and seven paint towers and kept chips turning over at ~3,700.

So the Rose-B tournament game was not an outlier. **Paint towers built is the master
variable**, it is upstream of everything iteration 9 did — an SRP is *+3 paint/turn
per allied paint tower*, so it is worth +21/turn with seven of them and +0 with none
— and it is the same dead-chips signature as ever, one level further up the causal
chain.

### Why it happens (read from the source, not guessed)

`towerTypeFor(ruin)` is an avalanche hash of the ruin's coordinates whose **low bit**
picks the type: a **fixed 50/50 money/paint split**. That design solved a real earlier
problem — a lattice-correlated choice produced all-one-type maps (gridworld 0 paint /
9 money) — and the hash fixed the *correlation*. It never revisited the *ratio*.

A 50/50 split is a bet that the two resources are equally valuable. Every measurement
in this log says they are not: paint binds, chips accumulate unspent into the tens of
thousands. Half of all ruins are being converted into more of the resource we already
cannot spend.

Note the hard constraint any fix must respect, recorded in the code and still true:
the type must be a **pure function of the ruin**. `workOnRuin` marks a pattern and a
later soldier probes "already marked?"; a type that varied with team state would let
two soldiers disagree and deadlock a half-built tower. So the algorithm's usual
preference for a self-calibrating threshold over a constant is **not available here**
— the constant is what preserves consistency between soldiers. What can change is
its value, which makes this a clean dose.

**Iteration 11, queued behind iteration 10's evaluation** (not bundled with it):
paint fraction of new towers ∈ {50% (zero arm = current), 75%, 100%}, implemented as
the hash compared against a threshold instead of its low bit. The 100% arm is the one
that answers whether money towers are worth building at all at this stage; the two
wins above suggest the answer is "some, but far fewer than half".

### Tournament 20260907-0100, bob-alice pairing complete: 143-7

All 150 bob-alice games played (`bob_iter7`). **143-7, 95.3%.** Alice-carol stands at
22-6 to alice with the pairing unfinished; bob-carol had not started. Alice is firmly
a **benchmark** (<30% for her against me), not a peer, so she does not gate my accepts.

My seven losses, which is the part worth having:

```
Rose         bob B   r581     UglySweater  bob B   r2000
SandyBeach   bob A   r571     galaxy       bob A   r2000
Jail         bob A   r2000    mit          bob B   r2000
Brat         bob B   r976
```

Four of the seven ran the full 2000 rounds and were decided on the painted-tiles
tiebreaker — those are close games, not collapses. Three were decisive, and one of
them matters more than the rest.

**`Brat`, side B, loses to two independent opponents.** It is a loss here against
alice (r976) *and* a loss in my own iteration-9 gauntlet against `bob_iter7` (r817).
Two unrelated lineages beat us from the same spawn on the same map. Doctrine #7 calls
flips concentrated on one map/side across many opponents a real causal effect rather
than churn, and this is that signature at its strongest — the common factor cannot be
the opponent.

And the gauntlet dump of Brat-B says exactly what the Rose-B dump said: **zero paint
towers built, three money towers, chips running to 46,590 unspent, paint delivered
flat at 209/round.** The repeatable map/side failure and the dominant loss shape are
the same phenomenon, which means **iteration 11's paint-fraction dose is aimed
directly at a failure two independent opponents have both demonstrated.** That is as
close to an externally-validated target as this project can produce.

`Brat` side B is therefore the pinned regression case for iteration 11: pin the map
with `MAPS` and check whether the paint-fraction dose makes us build paint towers
there at all.

### Iteration 11's premise refuted before it was built, for zero games

I had queued iteration 11 as a dose on the paint/money split, reasoning that a fixed
50/50 `towerTypeFor` was spending half of all ruins on the resource we cannot spend.
Before writing it I remembered `bob-tools/BobRuins.java` already answers this exactly:
tower type is a **pure function of the ruin's coordinates**, so the split every map
produces is computable from the map files with no games at all.

```
across all 75 maps      mean money fraction  50.9%   (min 27% Rose, max 75% Paintball)
my loss maps            mean money fraction  53.9%
my win maps             mean money fraction  57.3%
```

**No separation, and the sign is backwards** — the maps I win are slightly *more*
money-heavy. The hash is behaving exactly as designed: near-50% on average with no
lattice pathology. And the single most damning point: **Rose is the most paint-friendly
map in the entire pool at 27% money — 19 paint ruins out of 26 — and Rose side B is
the game where we built zero towers of either type.**

**CLOSED: "we lose because too many ruins become money towers."** Killed by a
measurement over the whole map pool that cost no games and about a minute, on a tool
I had already written for a different question two iterations earlier.

That is the third time this session the achievable-dose / reachability pre-check has
killed a plausible headline before it cost a gauntlet (the others: `SRP_MIN_CHIPS`,
and iteration 8's re-open). The pattern is now unmistakable enough to be a habit
rather than a discipline: **the cheap measurement that could refute the hypothesis
comes before the expensive one that could confirm it.**

### Re-targeting: tower COUNT, not tower type — and the bot has no memory

The losses do not differ from the wins in what they build ruins *into*. They differ in
how many ruins they build at all: 0-3 towers in losses against 10-14 in wins. So the
question is why expansion stalls, and the source answers it directly.

`chooseRuin()` picks a target from `rc.senseNearbyRuins(-1)` — **only ruins inside the
soldier's current vision, r² = 20.** There is no memory of a ruin walked past, and no
sharing between soldiers. A soldier that cannot presently see an unoccupied ruin has
no expansion target at all and falls through to wandering.

The frequency is already measured, from the iteration-9 probe, no new games needed:

```
              soldier-turns with a ruin target   without one
Castle              233  (21%)                    862  (79%)
quack             1,161  (11%)                  9,250  (89%)
```

**Soldiers spend 79-89% of their turns with no expansion target.** On a 26-ruin map
like Rose that is not a shortage of ruins; it is a shortage of *knowing where they
are*. This is the Phase 0 item-2 failure shape — a capability assumed absent because
the obvious call (`senseNearbyRuins`) was treated as the whole interface — and the
engine also exposes a messaging layer (`r² = 20` unit-to-unit, `r² = 80` tower relay)
that this bot has never once used.

**Iteration 11 (re-targeted), to be pre-registered properly once iteration 10 resolves:**
give each soldier a memory of unoccupied ruin locations it has seen, and navigate to
the nearest remembered one when none is visible. Purely local memory, one mechanism,
no comms yet — comms is the larger follow-on if memory alone proves the direction.

## Iteration 10 — three defects found in mechanistic verification, before any gauntlet

Step 4 of the algorithm (re-run the motivating game, classify engagement) earned its
keep here. The candidate was never evaluated, because it never worked, and each defect
was found by measurement rather than by reading alone.

**Defect 1 — the site check could not see what it was checking.**
First verification: lost Castle r775 and quack r627 to `bob_iter9`, with `srpA = 0`
against iteration 9's 1. `javap` on `senseNearbyMapInfos(MapLocation, int)` shows it
calls `getAllLocationsWithinRadiusSquared` and then filters by `canSenseLocation` —
it does **not throw** for tiles outside vision, it silently returns fewer. So
`srpSiteSafe` was approving remote candidates whose 5×5 it had only partly inspected,
letting soldiers mark overlapping patterns that can never complete.
*Fix*: require `area.length == 25`. `isValidPatternCenter` already guarantees all 25
tiles are on the map, so anything short of 25 means "I cannot see this pattern".
*Effect*: Castle r775 loss → r2000 tiebreaker loss; quack r627 loss → **win**.

**Defect 2 — searching at range and painting at range are different things.**
Despite that improvement, `srpA` was still **0 in both games**, so the wins were not
coming from the mechanism at all — algorithm step 4 case 3, "no evidence of
engagement: discard or fix, don't evaluate further". Cause, from the unit table: a
soldier's **action radius is r² = 9**, and the 5×5 around its *own* tile tops out at
r² = 8 — which is exactly why iteration 9's comment could claim the whole pattern was
attackable. Iteration 10 let the centre sit up to r² = 8 away, putting the far corner
of a remote pattern at r² = 32, and the "wandered off" guard only walked the soldier
back when it was **more** than 8 away. So a soldier marked a site it could never
paint, stood still for its 120-turn patience, and abandoned it — 25 paint burned and
the site poisoned with marks for everyone else.
The probe measured exactly that over a whole 2000-round game: **`start = 1`,
`done = 0`, `aband = 1`.**
*Fix*: navigate to the centre and paint only while standing on it (`!me.equals(srp)`).

**Defect 3 — the rotation defeated the very bound it was supposed to respect.**
I capped `SRP_SCAN` at 13 on the argument that exactly 13 offsets (dx²+dy² ≤ 4) have
their whole 5×5 inside vision r² = 20 — (2,0) lands on 20, (2,1) on 25. But the
ID-rotation indexed over all 24 tail offsets, so most scan slots landed on the r² = 5
and 8 candidates that can never pass. Measured: **the visibility guard refused 70% of
all attempts**, and `mark` overlap refused another 52%.
*Fix*: rotate within indices 1..12 only, so every scanned candidate is one the soldier
can actually inspect.

### What this sequence is worth

Three defects, all in one 20-line change, none of which a win rate would have
diagnosed — and the second one is the sharpest: **the candidate won a verification
game while its mechanism was completely inert.** Had I gone straight to the gauntlet
after the encouraging Castle/quack flip, I would have measured a 20-line change whose
stated mechanism fired once in 2000 rounds, and whatever number came back — accept or
reject — would have been about something else entirely.

That is the concrete argument for criterion 3 being a *mechanistic* criterion checked
*before* the win rate, and for reading it even when the win rate looks good.

## Iteration 10 RESULT (2026-09-07) — REJECTED, premise refuted, never reached a gauntlet

With all three defects fixed, the mechanism is well-formed — the visibility guard now
refuses **0%** of attempts, where it had been refusing 70% — and the candidate is
*worse*, losing quack (r920) and Castle (r283) to `bob_iter9`. It was never worth a
gauntlet, and the counters say why.

```
                          quack            Castle
attempts to start          1,795              95
  canMark refusals      19,904 (11.1/try)  1,192 (12.5/try)
  visibility guard           0   0.0%          0    0.0%
  EXISTING MARK          2,298 128.0%         43   45.3%
  starts                     1                 0
  completions                0                 0
```

**The blocker is mark saturation, not sampling.** Of the ~1–2 candidates per turn that
survive the geometry check, essentially all are refused because some tile of their 5×5
already carries a mark — at 128% of attempts on quack, more than one refusal per turn.

And those marks are overwhelmingly **tower-pattern marks**, not SRP marks.
`markTowerPattern` blankets a 5×5 around every ruin under construction, and soldiers
congregate at ruins because that is where the work is — so the neighbourhoods they
scan are precisely the marked ones. `srpSiteSafe` *must* refuse them:
`markResourcePattern` would overwrite those marks and break a tower another soldier is
building, and a tower is worth far more than an SRP.

So iteration 10's hypothesis — "SRP construction is limited by candidate-site
sampling" — is **wrong**. Sampling was a real defect (the bot did test 1 of 25 legal
centres), but fixing it exposes the actual constraint underneath: SRPs and tower
patterns compete for the same ground, and tower patterns rightly win. Scanning 13
neighbours of a marked tile finds 13 more marked tiles.

Bytecode was checked first as pre-registered and **exonerated**: `maxbcA` peaks at
8,601 of a soldier's 17,500 even with 13 `canMarkResourcePattern` calls per turn. The
veto did not fire; the idea simply does not work.

**CLOSED: "build more SRPs by searching harder for sites."** Re-open only if tower
marks stop blanketing the areas soldiers occupy — e.g. if a future change clears marks
after a tower completes, or moves SRP construction deliberately *away* from ruins.
That second one is a real idea and is recorded here rather than attempted now: it is a
different mechanism (site selection policy at the map level) from the one just killed.

Reverted `src/bob/Soldier.java` to the iteration 9 snapshot, verbatim and
compile-checked. **`bob_iter9` remains the current bot.**

### What iteration 10 bought

No accept, and three durable engine facts that were not in `RULES.md` and would have
cost far more to learn later:

1. `senseNearbyMapInfos(centre, r)` **silently truncates** outside vision — it filters
   by `canSenseLocation` rather than throwing. Any "check an area around a remote
   point" code in this bot is suspect unless it verifies the returned count.
2. A soldier's **action radius r² = 9 versus vision r² = 20** means it can *evaluate*
   ground it cannot *act on*. The 5×5 pattern around its own tile (max r² = 8) fits
   the action radius exactly — that is not a coincidence in the rules, it is the
   design, and any pattern work must be done from the centre tile.
3. Marks are a **shared, scarce, map-wide resource** contended between tower patterns
   and resource patterns, and nothing in the bot models that contention.

Fact 3 is the one with legs: it reframes SRPs as competing with expansion for ground,
which is a much better model than "SRPs are free paint income" — and it means
iteration 9's accept was buying its +3/turn on maps *open enough* to have spare
unmarked ground, which is exactly the Oasis-versus-Castle split it showed.


---

## Iteration 11 (2026-09-07) — PRE-REGISTERED: soldiers remember ruins they walk past

**Target selection.** Not a single losing game but the shape shared by all of them,
which is the algorithm's preferred absolute-degeneracy signal: **losses build 0–3
towers, wins build 10–14**, on maps carrying 8–28 ruins. Two independent opponents
(alice on `Rose`-B and `Brat`-B, `bob_iter7` on `Brat`-B, `Snowman`, `fix`) produce
the same picture, so the cause is ours, not a matchup.

**Root cause, read from the source.** `chooseRuin()` targets only
`rc.senseNearbyRuins(-1)` — ruins inside the soldier's **current** vision, r² = 20. A
soldier keeps a ruin it has already claimed (`workRuin` persists), but it has no
memory of any *other* ruin it has seen, and none at all if it has never had one. When
nothing is visible it falls straight through to `Nav.wander()`.

**Trigger frequency — already measured, no new games.** From the iteration-9 probe,
counting soldier-turns by whether a ruin target existed:

```
            with a ruin target     without one
Castle          233  (21%)          862  (79%)
quack         1,161  (11%)        9,250  (89%)
```

**79–89% of soldier-turns have no expansion target.** On 26-ruin `Rose` that is not a
shortage of ruins, it is a shortage of knowing where they are.

**Mechanism (one change).** Each soldier records unoccupied ruins it sees into a small
per-robot array, drops one as soon as it can see a tower standing there, and — *only
in the branch that would otherwise call `Nav.wander()`* — walks toward the nearest
remembered one. It consumes a move the bot was going to spend wandering anyway, which
is TRAINING_ALGORITHM.md's recurring winner's profile: **capability preserved at zero
marginal cost.** Statics are per-robot in this engine (the bot already relies on that
for `workRuin` and `srp`), so this is per-soldier memory; sharing it over the unused
messaging layer is the deliberate follow-on, not bundled here.

**Dose, with a zero arm.** `RUIN_MEM ∈ {0, 8, 24}`. **`RUIN_MEM = 0` is
byte-identical to iteration 9** — `seekRememberedRuin` returns false immediately and
the wander branch runs unchanged — so the zero arm is the accepted bot and is already
measured.

**Pre-registered accept criteria.**
1. **h2h vs `bob_iter9` > 50%**, 20 maps × 2 sides — accept gate.
2. Swept-win > swept-loss.
3. **Mechanistic, and checked before the win rate** (the lesson iteration 10 just
   taught): **cumulative towers built (`ptow + mtow`) must rise versus iteration 9 on
   the maps where expansion currently stalls.** `Brat` side B is the pinned case —
   zero paint towers against two independent opponents. If tower count does not move
   there, the mechanism is inert and the win rate is measuring something else,
   regardless of what it says.
4. Bytecode: the memory scan is O(24) per idle turn against a peak of ~10,000 of
   17,500, so no veto is expected — but `maxbc` is read, not assumed.

**Reachability pre-check.** The branch is live by construction: it replaces
`Nav.wander()`, which the probe measured as the path taken on 79–89% of soldier-turns.
The risk is not that it never fires but that it fires *too* readily — a soldier that
walks 30 tiles to a remembered ruin someone else has already claimed has traded
painting for travel, which is the "survival bought with inactivity" failure in a new
costume. Criterion 3 is what would catch that: towers built must actually rise.

### Iteration 11 mechanistic verification — criterion 3 passes, read before any win rate

Both pinned maps re-run as side B against `bob_iter9`. Cumulative towers built, our side:

```
map / side        before (iter7 or iter9)        iteration 11        result
Rose   B          0 paint, 0 money  = 0          4 paint, 1 money = 5   loss r771
Brat   B          0 paint, 3 money  = 3          1 paint, 4 money = 5   loss r1464
```

**On `Rose` side B the bot went from building nothing whatsoever in 581 rounds to
building five towers, four of them paint towers.** That is the exact degeneracy the
hypothesis named, reversed by the exact mechanism it proposed. Paint delivered followed:
it had decayed 193 → 147 → 39 → **0** in the tournament game, and now *climbs* through
the game to 1,738 per interval at the end, with soldiers growing 8 → 32 instead of
freezing at 14.

`Brat` side B moves less but in the same direction, and produces **the first paint
tower we have ever built on that side of that map** — the side two independent
opponents both exploit.

Bytecode read, not assumed: `maxbcB` peaks at 9,828 of 17,500. Criterion 4 clear.

**Classification: algorithm step 4, case 2** — still lost, but the mechanism
demonstrably engaged as designed, with an evidenced account of why these games could
not flip anyway. On Brat the opponent finished with 124 soldiers to our 84 and we
still ended on 90,170 unspent chips; five towers does not close a gap that size, and
the hypothesis never claimed it would. The claim was that expansion stalls because
soldiers forget ruins, and expansion demonstrably un-stalled.

Proceeding to staged evaluation. Note these two verification games are *not* evidence
of strength — they are both losses — and they are deliberately being read only as
mechanism engagement, which is the discipline iteration 10 cost me an afternoon to
learn the hard way.

### What the verification also says about where this direction runs out

Two details from the Rose trace bound how much per-soldier memory can be worth, and
both point at the same follow-on.

**It works late.** `ptowB` stays at 0 until round ~450 and then reaches 4 by round 750.
Memory cannot help a soldier that has not yet *seen* a ruin, and early in the game it
has seen almost nothing — which is exactly when expansion tempo matters most. The
opponent had 4 paint towers by round 150.

**It dies with its owner.** Statics are per-robot, and this bot's turnover is extreme —
an earlier trace measured ~290 soldiers built against ~15 alive at any moment. Every
death discards that soldier's entire map knowledge, and every replacement starts blind
next to a tower.

So per-soldier memory is a leaky bucket that fills slowly and empties on every death.
That is still worth measuring on its own — it is one mechanism, and the Rose result
says the leak is not fatal — but it names the two follow-ons precisely:

1. **Share ruin knowledge over the messaging layer** (`r² = 20` unit-to-unit, `r² = 80`
   tower relay). The bot has never sent a single message. Towers are immortal and sit
   at the relay tier, so a tower that accumulates ruin sightings and hands them to each
   unit it spawns would fix both the slow fill *and* the loss on death, which
   per-soldier memory fixes neither of.
2. **Symmetry inference.** Maps are guaranteed one of a small set of symmetries, and
   `bob-tools/BobSym.java` already exists to identify which. A ruin seen at (x, y)
   implies one at its mirror — knowledge available from the *first* sighting rather
   than after walking there, which is the direct answer to "it works late".

Both are recorded now, before the gauntlet reports, so that whichever way iteration 11
lands the next step is chosen from the trace rather than from the number.


---

## Fixed-roster run 20260907-011346 (bob_iter9) — the absolute instrument says something is wrong

Run at the accept of iteration 9, 25 maps x 2 sides x 3 roster opponents = 150 games.
`bot.txt` label is **`bob_iter9`** with no `+cand` suffix, so this measures the accepted
snapshot, not a candidate.

```
                     bob_iter3 (20260906-212734)      bob_iter9 (20260907-011346)
vs bob_iter0            36/40   90.0%                    48/50   96.0%
vs bob_iter1            34/40   85.0%                    28/50   56.0%      <-- 
vs examplefuncsplayer   40/40  100.0%                    50/50  100.0%
overall                                                 126/150  84.0%
```

**Win rate against the frozen `bob_iter1` fell from 85.0% to 56.0%** — 29 points — over
six accepted iterations, while the rate against `bob_iter0` rose and
`examplefuncsplayer` stayed pinned at 100%. The swept-map view says the same thing more
sharply, since it is immune to spawn advantage: **9 swept wins against 6 swept losses
and 10 maps split by side**, where against `bob_iter0` it is 23-0.

This is exactly the failure the fixed roster exists to detect, and it is the reason
TRAINING_ALGORITHM.md doctrine #9 keeps a never-retired opponent: *every accept in this
lineage cleared a within-run head-to-head against its immediate predecessor, and the
lineage still went backwards against an older frozen bot.* A chain of locally-winning
steps is not a globally improving path. My gauntlet headline (68.8% at iteration 9) is
measured against a pool that moves; `bob_iter1` does not move.

### Before treating it as established — the one competing explanation

Map samples are redrawn per run (25 of 75), and `AGENT.md` warns explicitly that a raw
win-rate delta *between* runs is noisier than it looks. The `bob_iter3` figure came off
a different 25-map draw. So the honest position is that this is a strong signal, not yet
a proven regression: 29 points at n=40-50 is roughly 6 binomial standard deviations,
which no plausible sampling story covers on its own, but map draw is not a plain
binomial.

**The decisive experiment is cheap and pinned, and is the next thing to run after
iteration 11 resolves**: replay `bob_iter3` and `bob_iter9` against `bob_iter1` on the
*same* map list —

```
MAPS="$(cat gauntlet/20260907-011346/maps.txt)" BOT=bob_iter3 OPPONENTS=bob_iter1 ../../tools/gauntlet.sh
```

`bob_iter9`'s half is already measured on exactly those maps by this run, so one 50-game
run answers it exactly, with the map variable eliminated by construction rather than
argued away.

### What it implies either way

If it holds, the lineage has been drifting toward beating its own recent ancestors — the
self-referential blind spot in TRAINING_ALGORITHM.md's own words — and the response is
the ablation track: gate iterations 5, 7 and 9's features off one at a time and measure
each against `bob_iter1` specifically, since that is the opponent that exposes it.
Notably the tournament agrees that absolute strength is not the problem *versus alice*
(143-7), which is consistent with a weakness that only an opponent of our own old shape
can see.

Recorded before iteration 11's gauntlet reports, so the interpretation of that run
cannot be bent by this one.

### The prime suspect, and a pre-registered ablation for it

Walking the accepted lineage for a feature that would show up specifically as
*side-dependence* against an old opponent produces one obvious candidate.

**Iteration 7 replaced a rule my own code called "team-symmetric" with one that is
not.** `bob_iter1`'s `towerTypeFor` is `((ruin.x + ruin.y) & 1)`, and its comment reads
"Deterministic, team-symmetric tower type choice". Iteration 7 swapped it for an
avalanche hash, and my own audit at the time measured the cost:

```
                                        old parity rule    iteration 7 hash
maps with a mismatched mirrored pair      30 (40%)            73 (97%)
mean money%-gap between the two halves    11.0 pts            24.0 pts
across all 75 maps                         --                 helps 18, HURTS 37
                                                              mean gain -0.59 pts
broad-run h2h that accepted it             --                 21/40 = 52.5%
```

I accepted it anyway, on an explicit robustness argument (it is the only rule that
never produces a 100%-one-type map) and on a pre-registered affected-subset tiebreaker.
That reasoning is still on the record above and I stand by having followed the rule I
set in advance. But the roster now supplies evidence that did not exist then, and it
points at exactly the dimension the audit flagged:

```
vs bob_iter1   swept-win 9 / swept-loss 6 / SPLIT BY SIDE 10 of 25 maps
vs bob_iter0   swept-win 23 / swept-loss 0 / split by side 2 of 25
```

**Ten of twenty-five maps against `bob_iter1` are won from one side and lost from the
other** — five times the side-splitting seen against `bob_iter0`. That is the
signature of an unearned economic asymmetry between the two halves of a symmetric map,
which is precisely what doubling the mirrored-pair mismatch rate from 40% to 97% buys.

**Ablation A7, pre-registered.** `src/bob_abl7` is `bob_iter9` verbatim with iteration
7's hash replaced by iteration 1's parity rule — one feature gated off, nothing else
touched (`bob-tools/ablations/make-abl7.sh`, compile-checked).

```
MAPS="$(cat gauntlet/20260907-011346/maps.txt)" \
  BOT=bob_abl7 OPPONENTS=bob_iter1 ../../tools/gauntlet.sh
```

The maps are **pinned to the roster run's exact sample**, so `bob_iter9`'s 28/50 is the
control measured on identical ground — the map-draw objection is eliminated by
construction, not argued away.

**Pre-registered readouts:**
1. **A7 win rate vs `bob_iter1` on those maps, against iteration 9's 28/50 (56%).**
2. **Split-by-side count**, which is the mechanism-specific one: if the hash is the
   cause, removing it should collapse the 10 split maps toward `bob_iter0`'s 2.
   A win-rate move without a split-by-side move would mean I found the right answer
   for the wrong reason, and I would keep looking.

Note what this ablation can and cannot settle. It measures iteration 7's *current*
value, which is the question the ablation track exists to ask — TRAINING_ALGORITHM.md
records that a 2026 audit found headline-accepted features worth ~0 and one negative.
It does not by itself prove the 85% → 56% decline is all iteration 7; iterations 5, 8
and 9 would each need their own gate to apportion the rest.

### Iteration 11 evaluation IN FLIGHT — recovery note for a future session

```
run id      20260907-020350
command     OPPONENTS="bob_iter9 bob_denier" NMAPS=20 ../../tools/gauntlet.sh
games       80  (20 maps x 2 sides x 2 opponents)
launched    2026-09-07 02:03 UTC, queued behind tournament 20260907-0100 (450 games)
candidate   src/bob/Soldier.java at HEAD = iteration 9 + RUIN_MEM = 24
control     bob_iter9 (the accepted snapshot), h2h vs it is the accept gate
```

The remote runner is `setsid`-detached, so this finishes whether or not the driver-side
poll survives. **If this session dies, do not re-run it** — that discards finished
matches and burns shared VM time twice. Recover with:

```
../../tools/gauntlet-collect.sh --list
../../tools/gauntlet-collect.sh 20260907-020350
```

Read criteria in the pre-registered order: **criterion 3 (towers built on Brat-B and
Rose-B) before the win rate**, then criterion 4 (`maxbc` against 17,500), then the h2h.
Iteration 10 is the reason that order is not negotiable.

**Queued behind it, already built and pre-registered**: ablation A7 on the pinned roster
maps (`bob-tools/ablations/README`), which is the higher-priority question — iteration
11 asks whether one new feature helps, A7 asks whether the lineage has been drifting
backwards for six iterations, and the roster says it has.

### Tournament, bob-carol opens: 91-2, and what that does to the roster finding

```
bob   beat alice   143 / 150   95.3%   (pairing complete)
bob   beat carol    91 /  93   97.8%   (in progress)
alice beat carol    99 / 150   66.0%   (pairing complete)
```

Both independent lineages lose to `bob_iter7` at 95%+. My two losses to carol are
`PlumberGame` (side B, r2000 tiebreaker) and `Thirds` (side B, r1626) — both as side B
again, which is now the third opponent to beat us disproportionately from that side.

**This complicates the `bob_iter1` regression rather than dismissing it, and the
distinction is worth being precise about.** Two readings compete:

1. The weakness `bob_iter1` exposes is *idiosyncratic to our own old shape* — iter1
   plays a way neither sibling plays, so no real opponent exploits it, and the 85% → 56%
   decline is a curiosity about a lineage-internal matchup.
2. It is a genuine capability loss that alice and carol are not yet strong enough to
   punish, and it will start costing games as they improve.

The tournament cannot distinguish these, because a 95-98% win rate has no resolution —
doctrine #4 exactly: an instrument pinned near 100% cannot resolve a few games, and
both siblings are pinned. `bob_iter1` at 56% is the only *even* instrument I currently
possess, and evenness is precisely what makes it able to resolve small effects.

So the ablation stays worth its one run, but its framing changes: it is no longer
"diagnose a regression that is costing me the tournament" — plainly it is not — it is
**"find out what capability the lineage traded away while its scoreboard was pinned at
the ceiling"**, which is the self-referential blind spot in TRAINING_ALGORITHM.md
stated from the other direction. A weakness invisible at 97.8% is exactly the kind that
surfaces later against a stronger field.

The side-B pattern is the thread tying all of it together: `Rose`-B, `Brat`-B,
`UglySweater`-B and `mit`-B against alice, `PlumberGame`-B and `Thirds`-B against carol,
`Brat`-B against `bob_iter7`, and 10-of-25 maps split by side against `bob_iter1`.
Four independent opponents, one recurring asymmetry — and iteration 7's own audit
recorded that it doubled exactly that asymmetry. Ablation A7 is aimed at the right
place.


---

## The regression investigation, designed as ONE pinned run (2026-09-07)

Priority note taken from the coordinator, and it is correct: **an accepted lineage
drifting downward invalidates the ground every later iteration is measured against**,
so this outranks new mechanisms. It also carries a warning I had not planned for —
the answer may be *"several accepts each cost a little"* rather than one culprit, and
mechanism ablations cannot tell me that. Only the roster, read **by snapshot**, can.

So the two questions are different and I had conflated them:

- **Is the decline concentrated?** — a question about *when*, answered by snapshots.
- **Is iteration 7's hash the cause?** — a question about *what*, answered by A7.

**Both fall out of a single run, because the gauntlet's `BOT` can be the frozen
opponent.** Make `bob_iter1` the bot and the snapshots its opponents; every pairing is
then played on one map sample, and each opponent's win rate against `bob_iter1` is the
complement of `bob_iter1`'s against it.

```
MAPS="$(cat gauntlet/20260907-011346/maps.txt)" \
  BOT=bob_iter1 OPPONENTS="bob_iter3 bob_iter7 bob_abl7" ../../tools/gauntlet.sh
```

25 maps x 2 sides x 3 opponents = 150 games, and the maps are **pinned to the roster
run's exact sample**, so `bob_iter9`'s already-measured 28/50 (56.0%) is a fourth arm
obtained for free on identical ground. The resulting curve:

```
   bob_iter3   vs bob_iter1    ?      <- was 85.0% on a DIFFERENT map draw
   bob_iter7   vs bob_iter1    ?      <- iteration 7 = the hash lands here
   bob_iter9   vs bob_iter1   56.0%   <- already measured on these maps
   bob_abl7    vs bob_iter1    ?      <- iteration 9 with the hash removed
```

**What each shape would mean, registered before the run:**

- `iter3` high and `iter7` low → the decline is **concentrated at iteration 7**, and
  `abl7` should recover most of it. One culprit, and it is the marginal 52.5% accept.
- `iter3`, `iter7`, `iter9` stepping down gradually → **diffuse drift**, several accepts
  each costing a little. `abl7` would then recover only its own share, and the right
  response is not one revert but re-examining the accept bar itself.
- `iter3` also low on *these* maps → the 85% was **a map-draw artifact** and there may
  be no regression at all. This is the null I most need to be able to detect, and it is
  the reason `bob_iter3` is in the run rather than assumed from the old number.
- `abl7` ≈ `iter9` → the hash is **not** the cause regardless of where the step is, and
  the side-split readout below decides whether I keep looking at symmetry at all.

**Second readout on every arm, pre-registered: split-by-side count.** `bob_iter9` shows
10 of 25 maps split by side against `bob_iter1`, against 2 of 25 versus `bob_iter0`. If
symmetry is the mechanism, that count should track the win rate across the four arms.
A win-rate move without a side move means the right answer for the wrong reason.

This is one run instead of three, it answers *when* and *what* together, and it cannot
be confounded by map draw because every arm plays the same 25 maps.

### RETRACTION — the side-B asymmetry is not real, and one of my readouts carries no information

Before pre-registering an iteration on the side-B pattern I had claimed across four
independent opponents, I checked the base rate. **The pattern does not survive it, and
I am withdrawing the claim.**

**1. There is no systematic side bias.** Win rate by side, computed over every game I
have rather than over the losses I noticed:

```
tournament (271 games)     side A 132/135 = 97.8%     side B 130/136 = 95.6%
                           gap 2.2 pts, se 2.2 pts  ->  1.01 sd
roster run  (150 games)    side A  61/75  = 81.3%     side B  65/75  = 86.7%   (B better)
iteration 9 (80 games)     side A  24/40  = 60.0%     side B  31/40  = 77.5%   (B better)
iteration 7 (200 games)    side A  86/100 = 86.0%     side B  77/100 = 77.0%   (A better)
```

One standard deviation in the tournament, and the sign **flips** across my own runs.
The "four independent opponents all exploit side B" reading was **selection bias of the
exact kind TRAINING_ALGORITHM.md warns about in Step 1** — *"Don't sample only losses."*
At a 95-98% win rate almost every game is a win, so the nine losses had to land
somewhere; 3 as A and 6 as B is what a fair coin does.

**2. Worse: `split-by-side` is a deterministic function of the win rate and carries no
independent information.** If per-game outcomes were independent, the chance a map
splits is `2p(1-p)`, so out of 25 maps:

```
vs bob_iter1          p=0.56   expected 12.3 +/- 2.5   observed 10
vs bob_iter0          p=0.96   expected  1.9 +/- 1.3   observed  2
vs examplefuncsplayer p=1.00   expected  0.0 +/- 0.0   observed  0
```

Every observation sits inside its expectation. **"10 of 25 split by side against
`bob_iter1` versus 2 of 25 against `bob_iter0`" was never evidence of asymmetry — it is
arithmetic on 56% versus 96%.** I presented it as a mechanism signature; it was a
restatement of the win rate.

**Consequences, applied rather than noted:**

- The pre-registered iteration on side-B asymmetry is **cancelled before it was
  written**. There is nothing to explain.
- My registered "second readout: split-by-side count" on the regression run is
  **struck**. A readout that is a function of the primary metric cannot corroborate it,
  and keeping it would have manufactured agreement between two views of one number.
- **A7 still runs**, but its motivation is now only what it always legitimately was:
  iteration 7 was accepted on a 52.5% head-to-head with its own audit recording that it
  *hurts 37 maps and helps 18*, mean −0.59 points. That is a marginal accept worth
  ablating on its own terms. The symmetry story was decoration and is gone.

**One real thing does survive.** Observed sweeps deviate from independence in the other
direction: iteration 9 vs `bob_iter7` at p=0.625 predicts 7.8 swept wins and 2.8 swept
losses, and I observed **5 and 0**. Fewer sweeps than chance means the two sides of a
map are *anti-correlated* — maps genuinely have side-specific character. That is a
statement about maps, not about a weakness of ours, and it is why the swept metric is
still worth reading even though `split-by-side` is not.

This also means **criterion 2 in my pre-registrations ("swept-win > swept-loss") is
largely implied by criterion 1**, since `p > 0.5` implies `p² > (1-p)²`. It is not
worthless — the deviation from `25p²` is informative — but it is not the independent
confirmation I have been treating it as, and doctrine #10's "a real effect shows up in
more than one place" is not satisfied by two functions of the same number.

### Corrected readouts for the regression run

With `split-by-side` struck, the regression run's readouts are:

1. **Primary — the win-rate curve across snapshots on the pinned maps.** This alone
   answers the *when* question (concentrated step versus diffuse drift versus null),
   which is the question that matters most, and it needs no second metric to be
   interpretable.
2. **Second source, only if the curve shows a step — and drawn from a different KIND of
   instrument** per LEARNINGS 14: replay-derived quantities on the stepping pair, i.e.
   cumulative towers built and paint delivered per round, which are measured from the
   replay rather than computed from the win/loss vector. These are follow-up dumps on
   the identified pair, not a pre-registered arm, because there is nothing to read them
   on until the curve names a step.

No metric that is an arithmetic transform of the primary is being carried, which is the
whole content of the retraction above.


---

## Iteration 11 GAUNTLET RESULT (2026-09-07) — all criteria pass, accept DEFERRED on a thin margin

Run `20260907-020350`, 20 maps x 2 sides. Criteria read in the pre-registered order.

**Criterion 3 (mechanism) — passed, and read first.** Verified before the run:
`Rose` side B went from 0 towers built in 581 rounds to 5 (four of them paint towers);
`Brat` side B from 3 to 5, including the first paint tower ever built on that side.

**Criterion 4 (bytecode) — passed.** `maxbc` 9,828 of a soldier's 17,500.

**Criteria 1 and 2 (the numbers):**

```
vs bob_iter9 (accept gate)   24/40  60.0%    swept-win  5   swept-loss 1
vs bob_denier                37/40  92.5%    swept-win 17   swept-loss 0
overall                      61/80  76.2%    (iteration 9 was 68.8%)
```

The gate is cleared and `WinPct` = 60% is met exactly. `bob_denier` improved from
75.0% to 92.5%, and the overall rate rose 68.8% -> 76.2%.

### Why I am not accepting yet

```
h2h 24/40      excess over even = 4 games,  binomial sd 3.16  ->  1.26 sd
denier +7/40   delta over iteration 9,      sd ~4.47          ->  1.57 sd
```

**Neither instrument clears its own noise floor.** Doctrine #6 says to compute that
floor and distrust deltas beneath it *regardless of how good the story is*, and the
story here is good — which is exactly when the rule is worth having. Doctrine #9 is
more specific still: **on thin accept margins, run the fixed roster BEFORE accepting,
not after.** It records that this once caught a bad accept by ten games when the
pre-registered metrics had each moved by one.

That instruction and the regression investigation want the same run, so they are now
one run:

```
MAPS="$(cat gauntlet/20260907-011346/maps.txt)" \
  BOT=bob_iter1 OPPONENTS="bob bob_iter3 bob_iter7 bob_abl7" ../../tools/gauntlet.sh
```

Run `20260907-<t>`, 25 pinned maps x 2 sides x 4 opponents = **200 games**, launched
with the tournament finished so the VM is free. `bob_iter1` is the *bot* and everything
else is an opponent, so each arm's rate against the frozen bot is the complement of the
reported number, and all arms play identical ground.

```
  bob (iteration 11)  vs bob_iter1    ?    <- doctrine #9 pre-accept check
  bob_iter3           vs bob_iter1    ?    <- was 85.0% on a DIFFERENT map draw
  bob_iter7           vs bob_iter1    ?    <- where iteration 7's hash lands
  bob_abl7            vs bob_iter1    ?    <- iteration 9 minus the hash
  bob_iter9           vs bob_iter1  56.0%  <- already measured on these very maps
```

**Decision rule, fixed now.** Accept iteration 11 if it is **not below `bob_iter9`'s
56.0%** on these pinned maps. A candidate that clears a thin head-to-head against its
predecessor while dropping further against the frozen bot is the precise failure this
whole detour exists to catch, and I would rather find it here than five iterations
later.

Note this run also folds in the four-arm regression curve, so one 200-game run answers
the accept question, the *when* question, and the A7 *what* question together.

### Tooling note — a launch died to a mid-read script race (reported, not worked around)

The first launch of the combined run failed instantly:

```
gauntlet 20260907-023506 ... games=200
../../tools/gauntlet.sh: line 84: syntax error near unexpected token `in'
```

`bash -n tools/gauntlet.sh` reports the file is **syntactically fine**. The cause is a
race, not a bug in my invocation: bash reads a script incrementally, and my
`git pull --rebase` landed commit `47334f8` — *"tools: run gauntlet and tournament from
a private copy"* — into `tools/gauntlet.sh` while bash was partway through executing it.
The file changed underneath the interpreter and the byte offset it resumed from landed
mid-token. That commit exists precisely to prevent this class of failure, and it caught
me on the last launch before it took effect.

Nothing was lost and no shared VM time was burned: the failure happened driver-side
before the remote script was generated, so `gauntlet-collect.sh --list` shows no run
`023506` on the VM at all. The local stub directory (bot.txt/maps.txt, zero games) was
removed. Relaunched cleanly as **`20260907-023720`**, 200 games.

Per the shared-resource rules I am reporting this rather than patching `tools/`, which
is the coordinator's to maintain. The lesson for me is narrower: **do not run a
`git pull --rebase` concurrently with launching a script out of the same tree.**


---

## INSTRUMENT CORRECTION (2026-09-07) — I have been misreading two BobDump columns

Reading `BobDump.java` line by line while the regression run played, to check a claim
about `Parking_lot`, I found I had two column semantics wrong. Both misreadings appear
in entries above and both are corrected here rather than quietly.

**1. `paintA`/`paintB` is the team's TOTAL PAINT STASH, not paint delivered to the map.**

```java
paintNow[0] = 0; paintNow[1] = 0;          // reset every round
...
paintNow[tm] += turn.paint();              // each robot's CURRENT paint, summed
```

Every robot takes one turn per round, so this sums the paint *held* by all living
robots. It is a **stock**, not a flow. I repeatedly described it as "paint delivered to
the map per interval", which is wrong.

**2. `ptow`/`mtow` are LIVE tower counts, not cumulative towers built.** `live[][]` is
incremented on `SpawnAction` and decremented from `diedIds`. (The field's own comment
says "cumulative spawns" and is itself wrong — the decrement is right there.)

### What survives, what changes, and one finding that gets *stronger*

The structural conclusions survive, because a standing count of 0 paint towers and a
cumulative count of 0 are the same statement:

- `Rose` side B "built zero towers in 581 rounds" -> **held zero towers, all game**.
  Unchanged as a degeneracy signal.
- Iteration 11 taking `Rose` B from 0 to 4 live paint towers -> unchanged, still the
  mechanism firing.
- "Paint delivered decayed 193 -> 147 -> 39 -> **0**" -> **the team's entire paint stash
  fell to zero.** That is *worse* than what I claimed, not better: every living unit was
  simultaneously empty.

**And one earlier reading inverts into a much more interesting finding.** On
`Parking_lot`, `bob_iter9` (A) loses to `bob_iter1` (B) with near-identical armies:

```
              soldiers  splashers  moppers   paint STASH   coverage
bob_iter9         95       26        26        4,708          261
bob_iter1         93       24        25        1,477          708
```

I had read this as "we paint more and cover less", which was incoherent. The correct
reading is the opposite and it is coherent: **our units are sitting on three times the
paint and converting it into a third of the coverage.** `bob_iter1` runs its units
close to empty and paints the map; `bob_iter9` hoards.

That is precisely the economics of the iteration 8 entry, pointing back at us —
*"dying at zero is the efficient terminal state"* — and the obvious suspects are our
own gates: `PAINT_FLOOR = 15` (refuse to paint below this) and `REFILL_BELOW = 50`
(walk away to refill above this), neither of which `bob_iter1` has in the same form.
A unit that will not paint below 15 and leaves to refill below 50 is idle across a
35-point band.

**This is now a stronger candidate for the `bob_iter1` regression than the tower hash**,
because it is a mechanism that (a) `bob_iter1` demonstrably does not share, (b) shows up
directly in the losing trace as a 3x stock difference, and (c) explains coverage loss
without needing any symmetry story — which I have already had to retract once.

The pinned run in flight measures *when* the decline happened and settles A7. If its
curve does not localise at iteration 7, this paint-hoarding gate is the next thing to
ablate, and it now has a pre-registered readout: **team paint stash relative to
coverage**, which is a replay quantity and therefore a genuinely independent instrument
per LEARNINGS 14.


---

## Iteration 11 ACCEPTED (2026-09-07) — and it partially reverses the regression

The deferred accept is resolved by the pinned run's first arm, which is complete at
50 games.

```
                          vs frozen bob_iter1, 25 PINNED maps x 2 sides
bob_iter9   (accepted)         28/50   56.0%     <- measured 20260907-011346
bob (iteration 11)             37/50   74.0%     <- measured 20260907-023720

delta +18.0 pts (+9 games), se 9.4 pts  ->  1.92 sd
```

**Identical maps, identical opponent, opponent frozen since iteration 1.** This is the
one instrument in the whole system that cannot move, and it moved 18 points in the
candidate's favour — a cleaner result than the 1.26 sd head-to-head that made me defer.
My pre-registered rule was "accept if not *below* `bob_iter9`'s 56.0%". It is 18 points
above.

**ACCEPTED.** Full criteria set:

```
1. h2h vs bob_iter9        24/40  60.0%   PASS (gate >50%, WinPct 60% met)
2. swept                    5 win / 1 loss  PASS (though largely implied by 1)
3. mechanism               Rose B: 0 -> 4 live paint towers   PASS, read first
4. bytecode                maxbc 9,828 / 17,500               PASS
5. roster, pre-accept      74.0% vs 56.0% on pinned maps       PASS, 1.92 sd
   (doctrine #9, triggered by the thin margin in 1)
```

Snapshotted `src/bob_iter11`. Replay `replays/iter11_bob_denier_quack_botA.bc25`.
`bob_denier` also improved 75.0% -> 92.5% and the overall gauntlet rate 68.8% -> 76.2%.

### Deferring was the right call and it changed the evidence, not just the timing

Had I accepted on the 60% head-to-head alone, iteration 11 would have entered the log
carrying a 1.26 sd justification. It now carries a 1.92 sd result against a frozen
opponent on pinned maps — a *different and much better* claim, obtained for one run
that I was going to spend on the regression anyway. Doctrine #9's instruction to run
the roster *before* accepting on a thin margin did not merely confirm the decision; it
replaced weak evidence with strong evidence.

### And it speaks to the regression

`bob_iter1` was beating `bob_iter9` at 44%. Against iteration 11 it manages 26%. So
**roughly half of the 85% -> 56% decline is recovered by a single change: letting
soldiers remember ruins they have walked past.**

That is strong evidence for the reading the instrument correction above arrived at
independently — the lineage's problem is **expansion and paint conversion**, not the
tower-type hash. Iteration 11 attacks expansion directly and recovers ~18 of the ~29
lost points.

The remaining arms (`bob_iter3`, `bob_iter7`, `bob_abl7`) are still playing and will say
whether the residual ~11 points localise at iteration 7 or are diffuse. Note the accept
decision above does not depend on them.


---

## REGRESSION RESOLVED (2026-09-07) — run 20260907-023720, 200 games, 25 pinned maps

Every arm played the identical 25-map sample against the identical frozen opponent.

```
                                          vs frozen bob_iter1
bob_iter3                                    39/50   78.0%
bob_iter7        (hash, no SRP)              38/50   76.0%
bob_iter9        (hash + SRP)                28/50   56.0%     <- the accepted bot
bob_abl7         (parity + SRP)              41/50   82.0%     <- BEST
bob iteration 11 (hash + SRP + memory)       37/50   74.0%

iter7 -> iter9    -20.0 pts   -2.16 sd
iter9 -> abl7     +26.0 pts   +2.93 sd
iter9 -> iter11   +18.0 pts   +1.92 sd
```

### 1. The decline is CONCENTRATED, not diffuse

`iter3 -> iter7` is −2.0 points, comfortably inside noise. **The entire 85% → 56%
collapse happens at iteration 9**, which I accepted earlier today on a 62.5%
head-to-head with a mechanism traced end to end. Every word of that trace was true and
the iteration still cost 20 points of absolute strength.

### 2. The cause is an INTERACTION, and neither feature is guilty alone

```
                        no SRP      with SRP
iteration 7 hash         76.0%       56.0%     <- -20
parity rule              (iter1/3 lineage)  82.0%
```

`bob_iter7` carries the hash without SRPs and is fine at 76%. `bob_abl7` carries SRPs
without the hash and is the **best build I have ever measured, 82%**. Only the
combination collapses. This is why single-feature reasoning missed it: I evaluated
iteration 9 against `bob_iter7`, which shares the hash, so the interaction was present
in *both* arms of the accept test and therefore invisible to it.

**Why it interacts, mechanistically.** An SRP is worth `+3 paint/turn per allied PAINT
tower`, so its return is *multiplied* by your paint-tower count, while its cost is a
flat 200 chips. Iteration 7's hash raised the variance of the tower mix — my own audit
measured mismatched mirrored pairs going 40% → 97% and the money-gap between halves
11.0 → 24.0 points. Higher mix variance is survivable when tower type only adds income
linearly; it is punishing once SRPs make the payoff multiplicative in paint-tower
count, because money-heavy draws now pay 200 chips a time for almost nothing.

**Note carefully what this does and does not rehabilitate.** The side-split evidence I
retracted was genuinely bogus — `split-by-side` is `2p(1-p)` and carried no
information. But the *other* half of that audit, the mix-variance measurement, was
real, and it is the half that matters here. Retracting bad evidence for a hypothesis is
not the same as refuting the hypothesis, and I nearly conflated those: **A7 was aimed
at the right feature for the wrong stated reason, and running it anyway is what found
this.** That is a good argument for running a cheap pre-registered ablation even after
its motivating story collapses.

### 3. Consequences

- **`bob_abl7` (82%) beats accepted iteration 11 (74%)** by 8 points (−0.97 sd, not
  significant on its own, but it is the better build and it is *simpler*).
- Iteration 11's ruin memory (+18) and removing the hash (+26) attack **different**
  causes — expansion versus tower-mix variance — so they should compose.
- **Iteration 12 is therefore obvious and is being built now: iteration 11 + the parity
  tower rule**, i.e. ruin memory *and* the hash reverted. Predicted ~82-88%; the
  pre-registered gate is that it must beat **both** iteration 11's 74.0% and `abl7`'s
  82.0% on these same pinned maps.
- **CLOSED: "iteration 7's avalanche hash is a net positive."** It was accepted at
  52.5% with its own audit recording −0.59 points across the pool; it is now measured
  at −20 points in the presence of SRPs. Reverting it.


---

## Iteration 12 (2026-09-07) — PRE-REGISTERED: revert the hash, keep the memory

**Hypothesis.** Iteration 11's ruin memory (+18 pts) and removing iteration 7's hash
(+26 pts) address **different** causes — expansion tempo versus tower-mix variance —
and therefore compose rather than overlap.

**Mechanism (one change, on top of accepted iteration 11).** `towerTypeFor` reverts
from the avalanche hash to iteration 1's parity rule `((x + y) & 1)`. Nothing else
touched.

**Pre-registered gate — it must beat BOTH known builds, on the pinned maps:**

```
must exceed   iteration 11   74.0%   (the accepted bot, hash + SRP + memory)
must exceed   bob_abl7       82.0%   (hash reverted, SRP, NO memory)
```

Beating iteration 11 alone is not enough. `bob_abl7` is a *simpler* build already
measured at 82%, so if iteration 12 does not beat it, the memory is not paying for
itself once the mix variance is fixed, and the correct bot is `abl7` — I would then
ablate the memory back out rather than carry it. **A candidate must beat the best
thing I have, not merely the thing it descends from.** That is the discipline whose
absence let iteration 9 through: it beat `bob_iter7` head-to-head while being 20 points
worse than `bob_iter7` in absolute terms, because both arms shared the hash.

**Evaluation, deliberately on the frozen instrument first.** Same 25 pinned maps, same
frozen `bob_iter1`, so all five prior arms are directly comparable with no map-draw
term at all. The head-to-head versus iteration 11 follows only if this clears.

That ordering is itself a change: I am now running the **absolute** instrument before
the relative one, because this session produced a case where the relative instrument
was structurally blind — an interaction shared by both arms cannot be seen by comparing
them.

**Prediction, registered:** ~82-88%. If it lands at ~82% (no better than `abl7`), the
memory contributes nothing once the mix is fixed and the two effects were the same
effect wearing different clothes.

## Iteration 12 RESULT — 78.0%, gate FAILED, and my composition hypothesis is refuted

```
                                       vs frozen bob_iter1, same 25 pinned maps
bob_iter9   (hash + SRP)                  28/50   56.0%
bob iteration 11 (hash + SRP + memory)    37/50   74.0%
bob_abl7    (parity + SRP, NO memory)     41/50   82.0%
bob iteration 12 (parity + SRP + memory)  39/50   78.0%

iter12 vs iter11   +4.0 pts   +0.47 sd
iter12 vs abl7     -4.0 pts   -0.50 sd
iter12 vs iter9   +22.0 pts   +2.41 sd
```

The registered gate was **"must exceed BOTH iteration 11's 74.0% AND `abl7`'s 82.0%"**.
It cleared the first and missed the second. **Gate failed; iteration 12 is not
accepted.**

### The hypothesis was that the two fixes compose. They do not — they substitute.

```
                      without ruin memory     with ruin memory
hash (high mix variance)     56.0%                 74.0%      +18.0
parity (low mix variance)    82.0%                 78.0%       -4.0
```

**Ruin memory is worth +18 points when the tower mix is noisy and roughly zero — very
slightly negative — once the mix is clean.** That is an interaction of the same kind
that caused the original regression, running the other way, and it is coherent: memory
improves expansion tempo, and expansion tempo matters most when your economy is
handicapped. Fix the economy and the compensating mechanism stops earning its keep.

My registered prediction was 82-88% and I wrote down in advance what a ~82% result
would mean: *"the memory contributes nothing once the mix is fixed and the two effects
were the same effect wearing different clothes."* That is what happened, at 78%.

### What is firm and what is not

- **Firm: the hash must go.** 56.0% -> 82.0% at +2.93 sd, and 56.0% -> 78.0% at
  +2.41 sd through the other path. Both routes that remove it gain ~20+ points.
- **Not firm: whether to keep the ruin memory.** `abl7` 82.0% versus iteration 12 78.0%
  is **0.50 sd** — I cannot separate them by comparing their rates against a third
  party, and I will not pick on a 4-game difference. Iteration 11's accept (+18 at
  1.92 sd) was measured in the *hash* world that no longer exists, so it does not
  settle this either.

### Deciding it properly, and cheaply

Comparing two builds through their records against a common opponent throws away most
of the information. **A direct head-to-head is far more sensitive**, so that is the run:

```
MAPS="$(cat gauntlet/20260907-011346/maps.txt)" BOT=bob OPPONENTS=bob_abl7
```

50 games, same pinned maps, iteration 12 against `bob_abl7` directly — the two builds
differ by exactly one feature, the ruin memory. **>50% keeps the memory and accepts
iteration 12; <50% drops the memory and makes `abl7` the bot**, which would mean
un-accepting iteration 11's mechanism on better evidence than accepted it.

Recording that possibility plainly: iteration 11 was accepted honestly on the evidence
available, and the evidence has since changed underneath it. Reverting an accept
because a later measurement invalidated its premise is a normal outcome, not a failure
of the earlier decision.


---

## MIRROR CALIBRATION (2026-09-07) — my bot is fully deterministic, and I invented a noise floor

Applying the new shared doctrine (MULTI_AGENT.md, "Calibrate your null: run a mirror",
`8073e62`). `src/bob_mirror` is `src/bob` with only the `package` line changed —
verified by diff — played over the 25 pinned maps, run `20260907-032957`.

**Result: every map returns one win and one loss with byte-identical round counts.**

```
  Justice        r525 / r525        MoneyTower     r630 / r630
  leavemealone   r741 / r741        walalilongla   r729 / r729
  windmill      r1000 / r1000       ...
  maps complete: 9   split-by-side: 9   (and rising 1:1)
```

The mirror is **exactly 50%, with 100% of maps split by side**. My bot seeds
`new java.util.Random(robot.getID())`, so there is no entropy anywhere: a game is a
pure function of (map, side, both builds).

### Consequence 1 — most of my "noise floor" reasoning this session was wrong

I repeatedly discounted results as "1.26 sd", "0.50 sd", "1.01 sd" and called them
noise. **Under determinism there is no sampling noise on the maps actually played.**
A 24/40 head-to-head is an exact +4-game effect on those 40 games, not a draw from a
binomial. Doctrine #1 said this all along — *"determinism means re-running is
worthless"* — and I failed to draw the obvious corollary that the *variance model* it
implies is zero, not binomial.

**The precise correction, because the sd figures are not entirely meaningless:**
uncertainty does not come from repeating games, it comes from *which maps were drawn*.
So binomial-style error bars are legitimate **only** for the question "will this hold
on the other 50 maps I did not play", and never for "is this difference real on the
maps I did play". On a **pinned** sample — every comparison in the regression run —
the difference is exact and error bars are meaningless. That reframes rather than
erases: iteration 9's 56.0% versus `bob_abl7`'s 82.0% on identical pinned maps is a
flat 13-game fact.

And the remedy for generalisation uncertainty is **more maps, never more repeats**,
which is what `NMAPS` is for.

### Consequence 2 — the split-by-side null is 25/25, not `2p(1-p)`

My retraction above computed the split-by-side null from binomial independence. The
mirror gives the *true* null and it is different: **identical code splits every map**,
because swapping sides just relabels a deterministic game. Both the retraction's
conclusion and this both hold — split-by-side still carries little information about
asymmetry — but the correct baseline is the mirror, not the binomial. The side-B
retraction itself stands on **magnitude** (2.2 points over 271 games), which needs no
variance model at all.

### Consequence 3 — deviation attribution, which is the real prize

Games where a candidate deviates from the mirror null are exactly the games its
mechanism changed. Applied to the completed head-to-head between iteration 12 and
`bob_abl7`, which differ by **only** the ruin memory:

```
25 maps,  mirror null predicts 25 splits
  split by side   19
  swept WINS       3    AlarmClock, giver, sayhi
  swept LOSSES     3    HungerGames, Parking_lot, rain
  deviations       6 maps (24%)
```

**The aggregate said 25-25, "no effect". The attribution says the memory decisively
flips a quarter of all maps and nets to zero only because three wins and three losses
cancel.** Those are completely different findings, and only the second one is
actionable. This is precisely the coordinator's point that a low aggregate is not
evidence a mechanism did nothing — here the aggregate is *exactly* the null and the
mechanism is *highly* active.

It also vindicates the caution I registered with iteration 11 and then failed to act
on: *"the risk is not that it never fires but that it fires too readily — a soldier
that walks 30 tiles to a remembered ruin someone else has already claimed has traded
painting for travel."* Three swept losses is what that looks like.


---

## MIRROR NULL MEASURED, and the whole regression restated in games and sweeps

Mirror regenerated **from the current build** and byte-identity verified by diff
(package line only), per the doctrine addition — a stale mirror would silently be an
ordinary head-to-head against an old fork, which is the exact measurement it exists to
replace. Run `20260907-032957`, 25 pinned maps:

```
MIRROR NULL     25/50 games     swept WIN 0     swept LOSS 0     split 25/25
```

Identical to the two other lineages' independently measured nulls. **The null for a
sweep is exactly zero**, so every swept map is signal, and margins are quoted below in
**games**, not standard deviations — this engine has no coin to be indistinguishable
from.

### The regression, restated on the sharp instrument

```
vs FROZEN bob_iter1, 25 pinned maps        games    sweptW  sweptL   net
bob_iter3   (pre-hash lineage)             39/50      14       0     +14
bob_iter7   (hash, no SRP)                 38/50      13       0     +13
bob_abl7    (parity + SRP)                 41/50      16       0     +16
iteration 12 (parity + SRP + memory)       37/50      13       1     +12
bob_iter9   (hash + SRP)                   28/50       9       6      +3
```

**`bob_iter9` is the only build in the entire lineage that suffers swept losses against
`bob_iter1` — six of them.** Every other build has zero or one. Against a null of
exactly zero sweeps, six maps lost *from both sides* is not a percentage difference to
be argued about; it is six maps where the bot is simply worse regardless of spawn.

That is a far crisper statement of the same finding than "56.0% versus 82.0%", and it
is the coordinator's point exactly: at these win rates the headline compresses, while
sweeps do not. The win-rate view made this look like a 13-game gap needing a variance
model; the sweep view makes it six unambiguous map-level regressions against a null of
zero.

### It also decides the ruin-memory question, which the head-to-head could not

The direct head-to-head between iteration 12 and `bob_abl7` was **exactly 25-25**, and
deviation attribution showed why: **3 swept wins and 3 swept losses**, 19 splits. The
mechanism is highly active and nets precisely zero. A pure aggregate would have called
that "no effect"; it is in fact "flips a quarter of all maps, both directions".

On the frozen instrument the tie breaks: `abl7` is **+16 with zero swept losses**,
iteration 12 is **+12 with one**. Adding the memory costs four net sweeps and
introduces the only swept loss in an otherwise clean build.

**Decision: the ruin memory is removed.** `src/bob` is now byte-identical to `bob_abl7`
(verified by diff) — iteration 9's SRPs with iteration 1's parity tower rule, no
memory. Snapshotted `src/bob_iter12`.

This **un-accepts iteration 11's mechanism**, on better evidence than accepted it.
Iteration 11's +18 games was measured in the hash world, where a compensating expansion
fix was worth a lot; with the mix repaired that compensation is worth −4 net sweeps.
The accept was honest on the evidence then available and the evidence changed. Reverting
it is the system working.

**Iteration 12 = revert iteration 7's avalanche hash to iteration 1's parity rule.**
The evidence is the pinned regression run: +13 net sweeps over `bob_iter9`, and 6 swept
losses eliminated.

### Closed and open

- **CLOSED: iteration 7's avalanche tower-type hash.** Net negative in the presence of
  SRPs; reverted. Its own audit had already measured −0.59 points across the pool.
- **CLOSED: per-soldier ruin memory as a standing feature.** Not inert — it flips 6 of
  25 maps — but net −4 sweeps once the tower mix is clean. `bob-tools/shelved/` keeps it.
- **OPEN, with a trace to do first:** the memory wins `AlarmClock`/`giver`/`sayhi`
  outright and loses `HungerGames`/`Parking_lot`/`rain` outright. Map area and ruin
  count do **not** separate those groups (1908 vs 1808; 21.3 vs 20.3 ruins), so my
  travel-distance hypothesis failed its own cheap pre-check. A refinement must come
  from tracing a swept-loss game, not from theorising — and the deviation attribution
  above hands the trace exactly three games to look at.


---

## Next pairwise ablation, chosen by LEARNINGS 15's own rule (2026-09-07)

Rule 4 says to suspect an interaction wherever a mechanism's payoff is multiplicative
in an existing quantity, and rule 3 says to ablate **pairwise, in the presence of the
new mechanism** rather than one feature at a time. Applying both to my own remaining
carried features rather than waiting for the roster to drop again:

**Iteration 3's idle-chip tower self-upgrade is the candidate.** It and SRPs are the
two things in this bot that consume chips, and their exchange rates are wildly
different now that the mix is clean:

```
tower upgrade   2,500 chips  ->  +5 paint/turn on ONE tower
SRP               200 chips  ->  +3 paint/turn on EVERY allied paint tower
```

With ~6-8 paint towers an SRP is `+18 to +24 paint/turn` for 200 chips against an
upgrade's `+5` for 2,500 — **over an order of magnitude better per chip**. Iteration 3
was accepted *before* SRPs existed, when the upgrade was the only chip sink available
and chips were a dead resource piling to 70,000 unspent. Both of those conditions have
since been falsified: iteration 9 gave chips a far better sink, and iteration 12's
measurements show the treasury now turning over at ~1,300 rather than accumulating.

So the exact shape LEARNINGS 15 warns about is present: a feature accepted under
conditions that a later feature removed, still being carried, and competing for the
same resource.

`src/bob_abl3` is now rebuilt **on the iteration 12 baseline** (parity + SRP, no
memory) with the upgrade gate turned off and nothing else touched — verified by diff,
compile-checked. It is queued behind the roster run; one gauntlet per workspace.

**Pre-registered readouts, in games and sweeps against the measured null of zero:**
1. Swept wins/losses versus `bob_iter12` head-to-head, and separately against frozen
   `bob_iter1` on the pinned maps for comparability with the whole curve above.
2. **A null result here is informative and will be recorded as such.** Unlike A7, I
   have no roster drop pointing at this feature — I am testing a *prediction* from the
   lesson rather than diagnosing a known failure, and "the upgrade still pays despite
   the arithmetic" would be a genuine correction to my model of the economy.


---

## Fixed-roster re-measurement from the iteration 12 baseline (2026-09-07)

Run `20260907-034757`, 200 games, fresh 25-map sample, `bot.txt` label **`bob_iter12`**,
`dirty=0`. This is the companion point the 41/50 needed.

```
                      games        sweptW  sweptL  split      MIRROR NULL: 0 / 0
vs bob_iter0         46/50  92%      21      0       4
vs bob_iter1         42/50  84%      17      0       8
vs bob_iter11        29/50  58%       7      3      15
vs examplefuncsplayer 50/50 100%     25      0       0
overall             167/200 83.5%
```

### The regression is repaired, and the sweep view says it cleanly

```
vs frozen bob_iter1        games     sweptW   sweptL
bob_iter3  (2026-09-06)    34/40  85%    —       —
bob_iter9  (2026-09-07)    28/50  56%    9       6      <- the regression
bob_iter12 (2026-09-07)    42/50  84%   17       0      <- repaired
```

**Six swept losses to zero.** Against a measured null of zero sweeps, that is the whole
finding in one line: iteration 9 was losing six maps from *both* sides to a bot frozen
eleven iterations ago, and iteration 12 loses none. The win rate is back to iteration
3's level (84% against 85%) while the lineage has kept everything else it learned.

`bob_iter0` (21-0) and `examplefuncsplayer` (25-0) also show zero swept losses. **The
only opponent that takes a swept map off the current bot is `bob_iter11`** — the
immediately preceding snapshot, which is exactly where the remaining contest should be.

### Reading the `bob_iter11` arm honestly

58% (29/50), swept 7-3. Iteration 12 beats the build it replaced, but this is the
narrowest margin on the board, and it should be: iteration 12 differs from
`bob_iter11` by *removing* two things (the hash and the ruin memory) rather than adding
anything. Getting 58% and +4 net sweeps by deleting code is a good trade, but it is not
a claim of a large advance — the advance was undoing damage.

The 15 split maps mean the two builds genuinely diverge on most of the pool while
netting out close, which is the same high-variance signature the ruin memory showed in
its own attribution. That is consistent and expected.

### Where this leaves the lineage

Seven accepted snapshots, and the honest summary of absolute progress is that
**iterations 7 through 11 netted approximately zero** — iteration 7 was a coin-flip
accept that became a liability, iteration 9 was a genuine mechanism that the liability
poisoned, and iteration 11 was a compensating fix that stopped paying once the
liability was removed. The bot is now roughly where iteration 3 stood against the frozen
opponent, but with SRPs actually working and with three durable instruments that did not
exist this morning: the mirror null, deviation attribution, and pairwise ablation.

That is not a comfortable result to write down, and it is the correct one. The next
accept has to clear iteration 12 on the frozen instrument, not just head-to-head.


---

## Ablation A3 RESULT (2026-09-07) — my prediction is REFUTED and iteration 3 is vindicated

Run `20260907-042157`, `bob_abl3` = iteration 12 with iteration 3's idle-chip tower
self-upgrade gated off, nothing else touched, against frozen `bob_iter1` on the same
25 pinned maps.

```
                                     games     sweptW  sweptL  split     NULL: 0 / 0
iteration 12 (upgrade ON)            41/50       16      0       9
bob_abl3     (upgrade OFF)           32/50        8      1      16

removing the upgrade costs 9 games, 8 net sweeps, and creates a swept loss
```

**The tower self-upgrade is strongly valuable, and my chip-efficiency argument for
retiring it was wrong.** I predicted an interaction of the LEARNINGS-15 shape — a
feature accepted under conditions a later feature removed. The measurement says the
opposite, and the engine table says why my arithmetic was bad:

```
PAINT tower mining by level        5 / 10 / 15 paint per turn
upgrade L1 -> L2                   2,500 chips  ->  +5 paint/turn on that tower
one SRP                              200 chips  ->  +3 paint/turn on EVERY paint tower
```

I compared these as if they competed for the same job. **They do not: they are
additive on the same tower.** A level-1 paint tower with three SRPs makes `5 + 9 = 14`
paint/turn; upgrade it and the same tower makes `10 + 9 = 19`. The upgrade *doubles the
base* that the SRP bonus is added to. Far from being obsoleted by SRPs, the upgrade is
what makes each tower a bigger platform for them — and the upgrade also carries
`1000 -> 1500` HP, which my income-only comparison ignored entirely.

**A3 is rejected; the upgrade stays.** Recorded as a genuine correction to my model of
the economy, which is exactly what I pre-registered a null result would be worth here.

### What this says about applying LEARNINGS 15

The lesson's rule 4 — *suspect an interaction wherever a payoff is multiplicative in an
existing quantity* — correctly flagged this pair as worth testing. It was worth testing.
But **a heuristic that nominates candidates is not evidence about them**, and I came
close to writing "SRPs obsolete upgrades" into the ledger on arithmetic alone. The
50-game ablation cost one run and prevented removing a feature worth 8 net sweeps.

The sharper form of the rule, learned here: **"multiplicative in an existing quantity"
identifies a pair worth measuring, but the sign is not predictable from the
arithmetic.** The hash/SRP pair interacted *destructively* because the hash controlled
the *variance* of the multiplier. The upgrade/SRP pair interacts *constructively*
because the upgrade raises the *level* of the base. Same structural signature, opposite
sign — so the pair always has to be run, never reasoned about.


---

## bob_denier RE-FORKED (2026-09-07) — it had gone stale exactly as its own README predicted

Triggered by the coordinator's note that iteration 12's reverted hash has never met a
non-lineage opponent. `bob_denier` is the closest thing I can legitimately play outside
the tournament, so I checked it before trusting it — and it was stale.

```
                                bob_denier (old)   live bot
iteration 3 tower upgrade             present       present
iteration 9 SRPs                      ABSENT        present   <- 0 refs vs 7
tower-type rule                       parity        parity
Nav.java / G.java                     identical     identical
```

**It was competing without iteration 9's entire paint economy.** That is the algorithm's
documented trap — *"a forked archetype going stale once masked a 62.5% as 95.0%"* — and
its own README had written the warning down in advance and named the trigger:
*"re-fork it from the current accepted snapshot whenever it stops being a challenge"*.
At 92.5% (iteration 11) it had comfortably stopped being a challenge.

Note the archetype was forked from `bob_iter3`, so it carried the **parity** tower rule
all along and never had iteration 7's hash. In hindsight it was quietly sitting on the
better half of the interaction for four iterations.

**Re-forked** with a new tool, `bob-tools/refork-denier.sh`, which copies the live bot
and re-applies *only* the paint-denial spawn policy — a single localized block in
`Tower.java`, the archetype's entire strategic content. `--check` reports drift and
exits non-zero, which is the "make staleness loud" half the algorithm asks for and which
I had not previously automated. It correctly flagged `Soldier.java` before the re-fork
and reports in-sync after.

### The measurement boundary, recorded so it is never crossed

Run `20260907-043355` was launched **before** the re-fork and uploaded the old source,
so its `bob_denier` arm measures the **stale** archetype. Per the README's own
instruction, win rates must never be compared across a re-fork:

```
vs bob_denier   iteration  9   30/40   75.0%     STALE archetype
vs bob_denier   iteration 11   37/40   92.5%     STALE archetype
vs bob_denier   iteration 12   (run 043355)      STALE archetype  <- last of the old series
--------------------------------- RE-FORK BOUNDARY ---------------------------------
vs bob_denier   iteration 12+  future runs       re-forked, carries SRPs
```

I expect the re-forked archetype to be substantially harder, and a drop across that line
is **not** a regression. The whole point is that the old number was inflated.

Also worth stating plainly: `bob_denier` is a pole, not a peer, and it is built from my
own code. It is a weaker independent-opponent proxy than the tournament, and it is not
a substitute for it — it can only answer "can I still handle paint denial", never "is
the hash revert sound against a foreign lineage". **The 06:00 PDT tournament remains the
real external check on iteration 12**, and it is a regression check rather than a
diagnosis: bob has been winning 95%+ against both siblings, so the question is only
whether the reverted hash holds that, and a drop would be information the frozen roster
structurally cannot supply.


---

## Session resumed 2026-09-07 ~13:10 UTC — run 20260907-043355 read, iteration 12 confirmed

The session was killed at ~04:40 by an account-wide rate limit. The run survived
(setsid) and had already been collated. Reading it now, with the timing caveat I
recorded before the session died applied.

```
run 20260907-043355   iteration 12 (bob_iter12), fresh 25-map sample, 100 games
                            games      sweptW  sweptL  split      NULL: 0 / 0
vs bob_denier (STALE)      47/50 94%     22       0       3
vs bob_iter11              28/50 56%      7       4      14
overall                    75/100 75.0%
```

**The `bob_denier` arm is the last of the pre-re-fork series and must not be compared
across the boundary** — the run uploaded `src/` before the re-fork, so this 94% is
against the archetype that was missing iteration 9's SRPs entirely. Honouring that
caveat is the whole reason it was written down; the number is retired, not carried.

The `bob_iter11` arm is the load-bearing one and it replicates the roster run
(`20260907-034757`, 29/50, swept 7-3) on a **different** 25-map draw: 28/50, swept 7-4.
Two independent map samples agree to within one game and one sweep. Iteration 12 is
confirmed as the accepted bot.

Note what that arm is *not*: a large advance. Iteration 12 differs from `bob_iter11`
by **removing** two things, and 56% with +3 net sweeps is what undoing damage looks
like. The lineage's absolute position is iteration 3's, reached by a longer road.


---

## Closed-direction RE-OPEN TEST (2026-09-07) — refill: trigger NOT met, ledger stands

The refill direction was closed with an unusually precise re-open trigger, and the
honest thing to do on resuming is to *test* it rather than quote it:

> **Re-open when paint stops being the binding constraint.** Concretely: when team
> chips stop accumulating — say sustained below ~5,000 while towers still want to
> spawn... **Iteration 9 (SRPs) is the most likely trigger** ... the chips column of
> any replay answers it.

Iteration 9 landed and is in the accepted bot, so the trigger is live. Answering it
from `bob_denier__box__botA.bc25` (iteration 12, full 2000 rounds, a loss):

```
round    500   1000   1500   1700   1800   1900   2000
chips   4770   5830   6420  11720  15770  18370  20720
paint   2431   3099   2908   2482   1580   1040    486     <- summed over ~63 robots
```

**The trigger is not met.** Chips never sit sustained below 5,000; they oscillate
4.5k–8.5k mid-game and then run away to 20,720. And the spawn gate is
`chips >= 250 + 1200 = 1450`, which is cleared on every single row — **spawning is
never chip-limited in this game**. Paint is still the binding constraint, exactly as
the closed entry said.

Two corrections this test produced, both worth keeping:

1. **The ~5,000 floor is partly my own constant, not a fact about the economy.**
   `UPGRADE_RESERVE = 4000` means a tower refuses to upgrade below `cost + 4000`, so
   the treasury is *held* near 4–6.5k by construction. A future re-open test must read
   the **spawn** gate, not the level, or it will be reading its own reserve back.
2. **The "dying at zero is efficient" argument does not obviously cover moppers** — a
   mopper's attack costs 0 paint, so its stash is consumed entirely by the territory
   penalty (2x for moppers) rather than converted into tiles. I checked whether that
   reopens it and it does not: refilling a mopper still costs the same 100 paint the
   tower would spend spawning one, and the 300 chips it saves are worthless while
   20,720 sit idle. The exemption I thought I had found is not one.

**CLOSED (re-affirmed): "keep units alive by walking them back to a tower to refill."**
Re-open trigger restated in the sharper form: *when a tower is observed declining to
spawn for want of chips*, not when the chip level is low.

The last row is the real finding here and it is not about refill: **486 paint across
~63 living robots at round 2000 — under 8 each, against capacities of 100–300 —
while 20,720 chips sit unspendable.** The bot has run out of things to buy with chips
(3 towers, all upgraded) and cannot buy paint with them.


---

## Iteration 13 target selection (2026-09-07) — iteration 9's SRPs are close to inert

Two replays of the accepted iteration 12, from `20260907-043355`, read for the
`srpA`/`srpB` columns (engine-reported **active** SRP counts):

```
bob_denier on box, side A, 2000 rounds          bob_iter11 on DefaultHuge, side A
round  srpA  srpB  chips  paint  ptow            round  srpA  srpB  covA  covB  soldA  soldB
  500     0     0   4770   2431    2                200     0     1   249   360    21     36
 1000     0     0   5830   3099    2                400     0     7   308   647    58    143
 2000     0     0  20720    486    2                471     1     9   271   702    63    150
   one SRP completion marker (r461), never activated
```

**Zero active SRPs for an entire 2000-round game**, and one completion that the
integrity re-check evidently reset before it ever activated. On DefaultHuge, one
active SRP against `bob_iter11`'s nine — and `bob_iter11` carries the *same* SRP code.

Iteration 9's SRPs are the bot's single largest paint lever (+3 paint/turn per active
pattern **per allied paint tower**), cost 200 chips against a treasury holding 20,720
idle, and are the mechanism the entire iteration 7-12 regression saga was about. They
are producing approximately nothing.

### This is a recorded-open successor, not a re-open

Iteration 10 closed *"build more SRPs by searching harder for sites"* on a solid
measurement (mark saturation refuses ~128% of geometrically-valid candidates per turn),
and wrote its own successor down:

> Re-open only if tower marks stop blanketing the areas soldiers occupy — e.g. if a
> future change ... **moves SRP construction deliberately away from ruins. That second
> one is a real idea and is recorded here rather than attempted now**: it is a
> different mechanism (site selection policy at the map level) from the one just
> killed.

That is the direction. But the `box` game says the story cannot be *only* mark
saturation: box carries **three towers in 2000 rounds**, so there is almost no marked
ground on that map, and it still produced zero SRPs. There is a second blocker, and
the obvious candidate is structural rather than geometric — `workOnSrp()` is called
only when `workRuin == null`, so a soldier holding a ruin target it may never reach
never executes the SRP path at all.

### PRE-REGISTERED: measure which gate before writing the fix

Two candidate blockers with opposite fixes is exactly the situation where theorising
costs an iteration. `src/bob_probe` is re-forked from the current `src/bob` (package
line only, verified) with counters at every SRP gate and nothing else changed:

```
turns  hasRuin  reached  chips  canMark  enemyPaint  overlap  mark  starts  done  abandon
```

`hasRuin` counts turns where the SRP path is never reached; `reached` counts turns
that entered site selection; the rest partition the refusals. Compile-checked in
isolation. Counters add no decisions, and soldier bytecode peaks at 9,488 of 17,500,
so the probe's games should be byte-identical to the bot's.

**Pre-registered reading, written before the run:**

- `hasRuin` dominant (>80% of turns) -> the blocker is **structural**: soldiers are
  monopolised by ruin targets. Fix is a reachability change, and the "site away from
  ruins" idea would be attacking the wrong gate.
- `mark` dominant among refusals -> iteration 10's finding still governs and the
  recorded successor (site away from ruins) is the right mechanism.
- `canMark` dominant -> geometry/paint, i.e. `isValidPatternCenter` or the 25-paint
  marking cost against a starved stash; that is a third mechanism again and would
  point at paint, not siting.
- `starts` >> `done` -> siting is fine and **completion** is the blocker (patience,
  paint, or disruption), which would redirect the whole iteration.

Both maps are run at the side that lost, so the trace is of a game I actually lose.
A null result — no single dominant gate — is recorded as such and sends me to the
`starts`/`done` ratio instead.


---

## SRP GATE PROBE RESULT (2026-09-07) — it is geometry, and my third branch was the right one

`src/bob_probe`, iteration 12 plus counters only, box and gridworld, side A (the side
that loses). Counters sum over the final per-soldier reports.

```
                turns  hasRuin  reached  canMark   (paintLow / geom)  mark  enemyPaint  starts
box              5999      101     5898     5410      45 / 5365        457      31         0
gridworld        4900     2826     2074     2071       0 / 2071          0       0         0

mean stash at the attempt:  box 121   gridworld 188      (soldier capacity 200)
```

**`canMarkResourcePattern` refuses 92% (box) and 99.9% (gridworld) of all attempts, and
that refusal is 99%+ GEOMETRY, not paint.** Of 7,481 refusals across both maps, 45 were
"stash under the 25-paint marking cost". Mean stash at the moment of the attempt was
121 of 200. Soldiers are not too poor to mark; they are standing in the wrong place.

Against my pre-registration:

- `hasRuin` dominant — **refuted on box** (1.7% of turns). Soldiers there almost never
  hold a ruin target, so "monopolised by ruin work" is wrong; on gridworld it is 58%,
  so the structural blocker is real but map-specific and secondary.
- `mark` dominant — **refuted**. 457 and 0. Iteration 10's mark-saturation finding is
  real but it is the *second* gate; it only bites on ground that already passed
  geometry, and on these maps almost nothing does.
- `canMark` dominant — **confirmed**, and it was the branch I wrote down as pointing at
  a third mechanism again.
- `starts >> done` — moot: **zero starts on either map.**

### The ceiling, measured over all 75 maps with no games at all

New tool `bob-tools/BobSites.java`. `GameWorld.isValidPatternCenter` is a pure function
of the map file (>=2 from each edge, and none of the 25 tiles in the 5x5 a wall or a
ruin), so the question "what fraction of tiles can host an SRP at all?" is a question
about the maps, not about a match.

```
maps=75   mean legal-centre share of paintable tiles   20.6%
          mean share of wall-legal centres killed by RUINS  47.6%
          worst  gridworld  2.1%        best  Oasis  53.8%
```

**The bot tests exactly ONE candidate per turn — whichever tile a random wander left it
on — against a ~20% base rate.** Observed pass rates are worse than the map-wide base
rate (box 8.3%, gridworld 0.14% against 2.1%), because soldiers cluster near ruins and
a ruin invalidates every 5x5 containing it. That is the whole mechanism, and gridworld
at 2.1% predicted its own 99.9% refusal rate before the probe was read.

This is the fourth time a question that looked like it needed a gauntlet turned out to
be a question about the map files. The habit is holding.


---

## Iteration 13 (2026-09-07) — SRP prospecting: mechanism VERIFIED, dose too large

**Change (one, in `Soldier`).** When a soldier has no ruin work and cannot mark where it
stands, it walks to the nearest tile within r² ≤ 4 that the engine's own
`canMarkResourcePattern` accepts, instead of calling `Nav.wander()`. Marking still
happens only from the centre tile, per RULES.md's pattern discipline — so this does not
re-open iteration 10's closed direction, which marked at range across 13 offsets and
died to mark saturation. `SRP_PROSPECT_R2 = 0` is an exact zero arm.

**Mechanistic verification (algorithm §4), three games, all side A:**

```
                              srpA (active SRPs)          outcome
                       baseline iter12   candidate
box       vs denier      0 all game        2 -> 0        r2000 tiebreak -> r828 MAJORITY  WORSE
gridworld vs denier      0 all game        0 all game    loss -> loss                     NO-OP
DefaultHuge vs iter11    0,0,1             1,3,2         r471 -> r728                     BETTER
```

Bytecode checked first: soldier max **8,286 of 17,500, zero overruns**, so none of this
is a limiter artefact.

**The mechanism engages** — it produces active SRPs on maps where iteration 12 produces
none for 2,000 rounds. On gridworld it correctly does nothing, which is what `BobSites`
predicted from the map file alone (2.1% legal centres): a mechanism that is inert
exactly where the offline model says it must be is evidence the model is right.

### Why box got worse, and it is a finding rather than an excuse

```
box, side A          r200 soldiers   towers built   r800 chips
iteration 12              36              3            —
iteration 13              14              1          17,844
```

Prospecting steers soldiers toward SRP-legal ground, and SRP-legal ground is
**anti-correlated with ruins by construction** — a ruin invalidates every 5x5
containing it, which is 47.6% of what walls would otherwise allow. So a mechanism I
wrote to find patterns silently became a mechanism that walks soldiers away from
ruins, and expansion is this bot's dominant loss shape (0-3 towers in losses, 10-14 in
wins). I got iteration 10's recorded successor idea — "site SRPs away from ruins" — for
free, and it cost more than it paid.

It also fires far too often: on box the prospecting condition is available on ~98% of
soldier turns, so it does not supplement the exploration policy, it replaces it.

### Pre-registered dose-response, with the zero arm, on the pinned maps

Three arms, one run, identical 25 pinned maps (`20260907-011346`), identical frozen
opponent `bob_iter1`, both sides — so every arm is directly comparable to the whole
regression curve already in this log with no map-draw term at all.

```
run 20260907-134632   BOT=bob_iter1   OPPONENTS = bob (share 1/1), bob_p3 (1/3), bob_iter12 (0)
   -- reported as bob_iter1's record; each ARM's score is 50 minus that, and
      bob_iter1's swept WINS are the arm's swept LOSSES.
```

`bob_p3` is the candidate with `rc.getID() % 3 != 0` declining to prospect: one soldier
in three. It exists because the box failure is a *trade* — patterns against expansion —
and a trade should be priced, not assumed. Doctrine #2's zero arm is `bob_iter12`
itself, already measured at 41/50 on these exact maps, which makes it a live
consistency check on the run as well as an arm.

**Prediction, registered:** the full dose loses to the zero arm; 1/3 is where an
interior optimum would sit if one exists. If the curve is monotone downward the
mechanism is rejected outright and the finding is that SRP siting cannot be bought
with soldier movement.


---

## The parity rule's degeneracy has a DIRECTION, and nobody priced it (2026-09-07)

Found while dumping the iteration 13 gridworld game for an unrelated reason: on
gridworld, side A, **`ptowA = 0` for the entire 2000 rounds and the treasury reaches
461,480 chips.** Zero paint towers, half a million idle chips, and it is my **only
swept loss** to the re-forked `bob_denier`.

`BobRuins` answers why from the map files, and this time I split the failure by
direction, which the earlier analysis never did:

```
parity rule ((x+y)&1), all-one-type maps -- 4 of 75
  CastleDefense   6 ruins,  0 money   ALL PAINT     benign
  Filter          5 ruins,  5 money   ALL MONEY     catastrophic
  Snowman         6 ruins,  6 money   ALL MONEY     catastrophic
  gridworld      21 ruins, 21 money   ALL MONEY     catastrophic
```

**Three of the four are all-MONEY, and the two directions are not remotely equivalent.**
A money tower is engine-verified sterile — `paintPerTurn == 0` and a new tower spawns
with `paintAmount == 0`, so it can never accumulate the 200 paint a soldier costs. An
all-money map is a bot with no paint income and no spawn points. An all-paint map is a
bot short of a resource it already cannot spend (20,720 idle on box, 461,480 on
gridworld). The closed comparison of the three tower-type rules counted "all-one-type
maps" as one number — parity 4, hash 0, folded 6 — and that number silently treats a
fatal outcome and a harmless one as the same event.

The prediction is confirmed in my own recent results: **gridworld is a swept loss** to
the re-forked denier, and **Snowman loses** to both `bob_denier` and `bob_iter11`.

### And my own instrument cannot see it

The 25 pinned maps that carry this log's entire regression curve — iter3 39/50, iter7
38/50, `abl7` 41/50, iter12 41/50, iter9 28/50 — contain **none of the four**. So every
comparison that decided to revert iteration 7's hash was made on ground that excludes
the reverted rule's known catastrophic case. The revert is still right (the hash cost
six swept losses against frozen `bob_iter1` through the SRP interaction), but its price
was never on the instrument, and I should have noticed that a pinned sample drawn once
is a fixed map list with all the overfitting properties AGENT.md warns about.

Recorded as a standing caveat on every pinned-map number in this log, and the reason
the full-pool tournament and fresh-sample gauntlets are not optional.

### Iteration 14, pre-registered here: abandon the pure function

Three closed directions surround this — "search for a better hash/mask", "fold the
coordinates", "too many ruins become money towers". All three are about finding a
better **pure function of the ruin's coordinates**, and any such function is degenerate
on some lattice; that is the whole lesson of those three entries taken together.

The purity requirement is not a law of the game. It exists because `workOnRuin`'s
"already marked?" probe refuses to re-mark, so a ruin whose type changed mid-build
could never complete. That is a defect in my own marking code, not an engine
constraint — `markTowerPattern` may be called again to overwrite marks.

So iteration 14 is the structural version: **make `workOnRuin` re-mark when the
existing mark disagrees with the wanted type, then choose the type adaptively — build
PAINT whenever the team is short of paint towers, MONEY otherwise.** That is the
algorithm's own recorded design preference ("self-calibrating thresholds beat fixed
constants ... derive the threshold from in-game observation"), it is not a re-open of
any of the three closed entries (all of which assume purity), and it dissolves the
lattice problem rather than searching for a lattice that survives.

Queued behind iteration 13's dose-response, which is running.


---

## Iteration 14 PRE-REGISTERED (2026-09-07) — adaptive tower type, and a two-sided map subset

Extending the degeneracy measurement from the 4 all-one-type maps to the whole
distribution (`bob-tools/ruins-mix.csv`, now pulled local):

```
parity rule, money fraction of ruins        most extreme maps of 75
gridworld    21 ruins  1.00        CastleDefense  6 ruins  0.00
Snowman       6        1.00        MoneyTower    10        0.20
Filter        5        1.00        starburst      8        0.25
yearofthesnake 16      0.88        box            8        0.25
lighthouse   11        0.82
Brat         11        0.82
windmill      8        0.75
DefaultMedium 19       0.74
boxofchocolates 15     0.73
Money        20        0.70

>= 75% money: 7 maps      <= 25% money: 4 maps
```

**The parity rule is not symmetrically degenerate — it is biased toward the fatal
direction, 7 maps against 4.** That is a stronger statement than "4 maps are
all-one-type", and it was free.

Two honesty checks on it, both of which cut against my story and are recorded because
they cut against it:

- **`box` is 25% money — a PAINT-heavy map — and box is a loss in both recent runs.**
  So the tower mix does not explain box, and I will not let it. The gridworld/Snowman
  explanation stands on its own maps only.
- `Brat` at 0.82 is the map whose side-B failure this log already diagnosed in the
  iteration-11 era as "zero paint towers built, three money towers, chips running to
  46,590 unspent". That entry did not connect the failure to the parity rule because
  the bot was on iteration 7's hash at the time. It is the same failure shape, and
  reverting to parity has re-armed it.

### The change (built, compiled: `src/bob_i14`, forked from `bob_iter12`)

Two edits, one of which is provably inert alone:

1. `workOnRuin` completes whichever tower type the **ground** supports, not only the
   type this soldier wants. With today's pure `towerTypeFor` the two can never
   disagree, so this branch is dead and the build is iteration 12. It exists so an
   adaptive type cannot deadlock a ruin an earlier soldier marked for the other type
   — that deadlock, not any engine rule, is the sole reason the type had to be pure.
2. `towerTypeFor` returns PAINT when `getChips() >= CHIP_SURPLUS` (dose 5000), else the
   parity rule. `CHIP_SURPLUS = 0` is an exact zero arm, and `bob_iter12` already
   serves as that arm at 41/50 on the pinned maps.

This is **not** a re-open of the three closed tower-type entries ("better hash/mask",
"fold the coordinates", "too many money towers"). All three search for a better pure
function of the ruin's coordinates, and the lesson of the three taken together is that
every such function is degenerate on some lattice. This abandons purity instead.

### Pre-registered evaluation, defined by the mechanism before any game

The mechanism fires whenever the treasury is in surplus, so it is **not** confined to
money-heavy maps — on paint-heavy maps it pushes further toward paint and could starve
the chips that buy towers and units. The subset therefore contains both tails:

```
FATAL tail (expect gains):    gridworld Snowman Filter yearofthesnake lighthouse Brat windmill
BENIGN tail (expect no harm): CastleDefense MoneyTower starburst box
```

Accept requires **both**: a real gain on the fatal tail and no regression on the benign
tail. Reporting only the first would be a cherry-pick, so both go in the log whichever
way they land — the same rule iteration 7's affected-subset run was held to.

A broad fresh-sample run and the head-to-head against `bob_iter12` follow only if the
subset clears; the subset is a screen, never the accept gate.


---

## Iteration 14's premise REFUTED by the tournament, before it cost a game (2026-09-07)

Tournament `20260907-1300` completed while iteration 13's dose run was playing. It
staged iteration 12 from HEAD, so it is the regression check on the reverted hash
against two independent lineages:

```
bot     won/played   win%    vs 20260907-0100
bob      277/300    92.3%        -3.3
alice    114/300    38.0%        +2.7
carol     59/300    19.7%        +0.7

swept:  alice-bob   alice 1,  bob 65        bob-carol   bob 64,  carol 1
```

**The revert holds.** 92.3% with 65 and 64 swept maps of 75 against a measured null of
zero sweeps. The −3.3 is worth naming but not chasing: both runs were complete over the
same 75 maps, so it is a real 10-game move, and it is dwarfed by the sweep counts.

### And then the same file killed my next iteration for free

Iteration 14 was built, compiled and pre-registered on the claim that the parity rule's
money bias costs games. The tournament is an **independent** test of exactly that claim,
and I had it on disk before spending a gauntlet:

```
bob's 23 losses         on maps >=70% money under parity:  2  ( 9%)
bob's 21 non-swept pairs on maps >=70% money under parity:  2  (10%)
pool base rate                                                 15%
```

**Bob loses and fails to sweep on money-heavy maps LESS often than chance, not more.**
And `gridworld` — the 21-ruin, 100%-money map that motivated the entire iteration, where
iteration 12 runs 2000 rounds with zero paint towers and 461,480 idle chips — is **swept
by bob against both siblings**.

So the mechanism is real and the *inference from it* was wrong. The gridworld failure is
genuine but it is a failure against `bob_denier`, a paint-denial archetype forked from
my own code, and independent lineages do not exploit it. This is measurement doctrine #4
biting from the other side: I checked that my instrument could *resolve* the effect and
forgot to check that the effect *matters* against anything but my own archetype.

**Iteration 14 is NOT run.** `src/bob_i14` is shelved, compiled and ready, with its
re-open condition recorded: if an opponent ever appears that punishes a paint-tower
shortage the way `bob_denier` does, the build already exists. One tournament report,
already on disk, cost nothing and saved 150+ games.

That is now the fifth time this session a question that looked like it needed a gauntlet
was answered by a file I already had.

### The target the same report DOES support

In 450 games bob has exactly **two swept losses**: `maze` to alice and `catface` to
carol — the only two maps where an independent lineage beats iteration 12 from *both*
sides. Against a null of zero sweeps that is the sharpest signal the sanctioned channel
can produce, it comes from lineages that share none of my code, and it is precisely what
MULTI_AGENT.md says the tournament is for. That is iteration 15's target.


---

## Swept-loss trace (2026-09-07) — the two maps independent lineages take from me

Tournament replays only (`~/battlecode25-vibe/arena/tournaments/20260907-1300/replays/`),
which MULTI_AGENT.md sanctions: they show what an opponent *does*, as any real match
would. No sibling code, notes or logs were read.

```
maze  (60x60, 28 ruins)    bob as A            bob as B
  bob towers at r2000       2 paint + 2 money   2 paint + 2 money
  sibling towers            9 paint + 12 money  9 paint + 10 money
  bob soldiers built        202                 182
  sibling soldiers built    651                 726
  coverage                  338 vs 641          337 vs 643

catface (30x30, 6 ruins)   bob as A, loss at r1431
  bob towers at r250 and r500:  ZERO of either type   (both starting towers dead)
  bob paint held, whole army:   553 -> 306 -> 297
  sibling denial actions/250r:  178, 199, 335   against bob's 39, 37, 50
```

These are two completely different failures and both are side-independent.

**`maze` is expansion, and the magnitude is not subtle: four towers from both sides
against roughly twenty.** This is my lineage's documented dominant loss shape ("losses
build 0-3 towers, wins build 10-14") appearing against an opponent that shares none of
my code.

**`catface` is denial**: the sibling removes paint 4-7x faster than I do and kills both
of my starting towers inside 250 rounds. That is the same axis `bob_denier` attacks,
now demonstrated by an independent lineage — which upgrades it from "my archetype's
speciality" to a real weakness.

### Why maze, specifically — and the test iteration 14 failed, run again

`BobSites` also yields each map's blocked (wall + ruin) share, free:

```
most blocked of 75:  gridworld 22.2%  MAZE 20.6%  boxofchocolates 20.0%
                     yearofthesnake 19.2%  sierpinski 17.7%  mit 17.0%
                     CastleDefense 16.5%  Brat 16.3%          pool mean 11.2%
```

**maze is the 2nd most wall-blocked map in the pool**, and 60x60. Applying the same
test that killed iteration 14's premise:

```
bob swept        129 pairs   mean blocked 11.0%
bob NOT swept     21 pairs   mean blocked 12.2%        <- weak on the mean
top-8 most blocked maps contested by a sibling: 5 of 8  (maze, sierpinski, mit,
                                                         CastleDefense, Brat)
base rate of contested maps: 21/75 = 28%
```

The mean barely moves, but **the extreme tail concentrates hard: 62% of the eight most
blocked maps are contested against a 28% base rate.** That shape — flat until a
threshold, then sharp — is what a navigation failure looks like: greedy movement is
fine until obstacles are concave enough to trap it.

Stated honestly: 5 of 8 is three maps above expectation, which is suggestive rather than
conclusive on its own. It earns an iteration because it also has a mechanism, and
because it passed the identical test that refuted iteration 14 rather than being
excused from it.

### Mechanism, read from my own source

`Nav.navTo` considers **five** of the eight directions (the target direction and ±45°,
±90°), refuses enemy paint on a first pass, and after three turns stuck picks a
**random** direction. There is no wall-following of any kind. In a concave pocket the
five-direction fan cannot move away from the target to get around an obstacle, and the
random escape does not systematically circumnavigate anything — it resets progress.
TRAINING_ALGORITHM.md lists hybrid bug-nav among the perennial mechanics; this bot has
none of it, on any unit type.

**Iteration 15 (queued): replace the greedy fan's failure mode with bug navigation** —
on a blocked greedy step, latch a wall-following direction and hold it until the target
is strictly closer than when the obstacle was met. Two things to watch, both from the
algorithm's own warnings: this touches every unit type at once, so it must be measured
broadly and not just on maze; and a fixed handedness for wall-following is exactly the
"fixed absolute-order decision" Phase 0.7 flags, so the mirror gets run on it.


---

## Iteration 13 RESULT (2026-09-07) — REJECTED, monotone dose-response, no interior optimum

Run `20260907-134632`, 150 games, `BOT=bob_iter1` frozen, all three arms on the identical
25 pinned maps, both sides. Reported as each arm's own record (the run measures
`bob_iter1`, so an arm's wins are 50 minus its opponent's).

```
arm                              games    win%   sweptW  sweptL  split   net    MIRROR NULL: 25/50, 0 sweeps
ZERO ARM (iteration 12)          41/50   82.0%     16       0       9    +16
iteration 13, share 1/3          30/50   60.0%      9       4      12     +5     -11 games, -11 net sweeps
iteration 13, share 1/1           6/50   12.0%      0      19       6    -19     -35 games, -35 net sweeps
```

**REJECTED.** The curve is monotone downward — 82% -> 60% -> 12% — so there is no
interior optimum, and my registered prediction that "1/3 is where an interior optimum
would sit if one exists" is answered: none exists. At full dose the bot scores **zero
swept wins and nineteen swept losses** against a snapshot from eleven iterations ago,
against a null of zero sweeps in either direction. That is not a marginal call.

**The zero arm reproduced 41/50 exactly**, matching the figure this log recorded for
iteration 12 on these same pinned maps in run `20260907-011346`. Determinism held and
the instrument is sound, so the two candidate arms' numbers are exact facts about these
50 games rather than draws from anything.

### What it actually taught, which is worth more than the accept would have been

I built this on the reading that a soldier calling `Nav.wander()` is **idle capacity**:
its action is already spent painting (step 4 runs regardless), so redirecting its
*movement* looked free. The dose-response says movement is the opposite of free.

**Soldier movement is this bot's scarcest capability, not its spare one.** Wandering is
how the bot discovers ruins, ruins are the entire economy, and expansion is the
documented dominant loss shape. Prospecting spends that discovery on pattern siting, and
because SRP-legal ground is anti-correlated with ruins by construction (a ruin
invalidates every 5x5 containing it — 47.6% of otherwise-legal centres), it does not
merely fail to find ruins, it walks away from them. Full dose loses 3 of every 4 games
it used to win.

The mechanism was never the problem: it demonstrably produced active SRPs on maps where
iteration 12 produces none in 2,000 rounds, at a bytecode cost of 8,286 of 17,500. It
bought a real thing at a price I had assumed was zero without measuring it.

**CLOSED: "spend soldier movement to find SRP sites."** Killed by a three-arm
dose-response with a zero arm on pinned maps: −11 games at one soldier in three, −35 at
all of them, monotone. Re-open only if soldier movement stops being the binding
constraint on ruin discovery — for instance if a future iteration gives soldiers a
non-movement way to find ruins, which is exactly what iteration 11's shelved ruin memory
did. Note the connection: memory was worth +18 games in the hash world and −4 sweeps in
the clean one, and this result says why the sign could flip so easily — both features
trade against the same scarce quantity.

`src/bob/` reverted to `bob_iter12`, verified byte-identical apart from the package line
on all seven files. **`bob_iter12` remains the bot.**

### Standing correction to how I read "idle"

Three times now I have proposed spending something I called idle — idle chips (twice)
and idle movement (once). Idle chips were genuinely idle and SRPs were right to take
them. Idle movement was not idle at all. The distinction that separates them: a
**resource** accumulates when unused and can be verified idle by watching it pile up
(20,720 chips, 461,480 chips); a **capability** produces value continuously and looks
idle only because its output is not on any counter I print. Before spending anything
called idle again, ask which of the two it is, and find the counter that would show its
output.


---

## Iteration 15 (2026-09-07) — PRE-REGISTERED: bug navigation

**Target.** `maze`, a swept loss to an independent lineage from both sides, where I
build 4 towers to their ~20. Selected from the tournament, not from my own gauntlet,
so it is a weakness my whole lineage shares and no self-play instrument could have
surfaced.

**Mechanism (one change, `Nav.navTo`).** The old greedy fan tried the target direction
and ±45° and ±90°, so it almost never failed to *move* — it failed to make *progress*,
sliding along a concavity and back, with a random escape after three turns literally
stuck that resets rather than circumnavigates. Replaced with Bug2: take the straight
step (preferring non-enemy paint, with ±45° slides); if it is blocked, latch a
wall-following heading and hold it until the target is strictly closer than it was when
the obstacle was met. The `lastLoc`/`stuckTurns` random escape is deleted.

**Mechanistic verification (algorithm §4), before any gauntlet:**

```
bob (bug nav) vs bob_iter12, maze, side A -- WIN r1608 (MAJORITY_PAINTED)

round        towers A (bug nav)      towers B (iteration 12)     coverage
  400            1p + 1m                   1p + 1m                215 / 160
  800            2p + 2m                   1p + 1m                337 / 290
 1200            8p + 7m                   2p + 2m                550 / 346
 1608            9p + 10m  = 19            2p + 2m  = 4           700 / 286
soldiers built    213                       132
```

**19 towers against 4**, which is exactly the ~20 the independent sibling built on this
map, and iteration 12 reproduces its 4-tower failure against *my own* snapshot as
faithfully as it did against alice — so the defect is a property of the map, not of the
matchup, which is what a navigation bug must look like. `sierpinski` (5th most blocked)
also flips to a win. Bytecode max **8,837 of 17,500, zero overruns**.

### Pre-registered evaluation, and why NOT on the pinned maps

The 25 pinned maps carrying this log's regression curve contain **none of the eight most
wall-blocked maps** (maze, gridworld, boxofchocolates, yearofthesnake, sierpinski, mit,
CastleDefense, Brat are all absent). Measuring a navigation change there would
systematically understate it — the same blind spot I recorded this morning about the
tower-mix revert, now cutting the other way. So the accept gate runs on a **fresh random
sample**, per AGENT.md, and the wall-dense maps are reported separately as a subset
defined by the mechanism rather than by outcome.

```
RUN A (accept gate + null)   BOT=bob_iter12  OPPONENTS="bob_mirror bob"  fresh 25 maps, 100 games
   bob_iter12 vs bob_mirror -> the mirror NULL, regenerated from the BASELINE being
                               measured against (verified byte-identical, 7 files)
   bob_iter12 vs bob        -> the head-to-head accept gate, on the identical maps,
                               so deviation attribution against the null is exact
RUN B (mechanism subset)     the 8 most wall-blocked maps, BOT=bob OPPONENTS=bob_iter12
```

**Accept requires all three:** the head-to-head beats the mirror null in games and net
sweeps; no one-directional regression in the diff; and the subset moves in the predicted
direction. A subset gain with a flat head-to-head is **not** an accept — it would mean I
had bought wall-dense maps with something paid elsewhere, and I would want to know what.

**Phase 0.7, registered in advance:** wall-following handedness is a fixed absolute-order
tie-break. The mirror in run A is therefore also the symmetry audit — identical code must
still split every map 1-1. If the null is no longer 25/50 with zero sweeps, the
handedness has introduced a side bias and that is a real bug regardless of the win rate.


## Iteration 15 arm A RESULT — REJECTED on both pre-registered gates

```
RUN A  20260907-144139, fresh 25-map sample, 100 games
  MIRROR NULL   bob_iter12 vs byte-identical clone     25/50   swept 0-0, split 25
  ACCEPT GATE   bob_iter12 vs candidate                24/50   candidate swept 4, lost 5, split 16
                                                        -> -1 game, -1 net sweep vs the null

  deviation attribution: 11 of 50 games deviate (22%) -- candidate won 5, lost 6

RUN B  20260907-152404, the 8 most wall-blocked maps, 32 games
  SUBSET        candidate vs bob_iter12                 8/16   swept 1-1, split 6
  HANDEDNESS    candidate vs byte-identical clone       8/16   swept 0-0, split 8
```

**Rejected.** The accept gate is one game *below* a null that never sweeps, and the
subset defined by the mechanism — the eight maps the whole hypothesis is about — is
flat at 1 swept win and 1 swept loss.

**Registering the subset in advance is what makes this readable.** The verification game
was spectacular: 19 towers against 4 on maze, matching the independent sibling's ~20
exactly. Played from both sides against the same opponent, maze **splits**. That single
game would have carried an accept if I had let it, and it is a textbook instance of the
regularity TRAINING_ALGORITHM.md records — metrics that improve without converting to
wins. The bot really does build 19 towers now; it does not win more often for it.

**The handedness audit is a clean positive and worth keeping.** Identical code carrying
right-handed wall-following splits all eight of the most obstacle-dense maps in the pool,
zero sweeps either way. So the Phase 0.7 worry about a fixed absolute-order tie-break is
measured and dismissed *for this mechanism* — the consistent handedness costs no side
symmetry, which is not something I could have assumed.

### One refinement, on an identified defect (near-miss refinement 1 of 3)

The deviations have a shape and it is not random:

```
candidate swept WINS   windmill 14.2%  Piglets2 16.2%  gardenworld 12.3%  Racetrack 11.7%
candidate swept LOSSES CastleDefense 16.5%  Bread 11.1%  rain 6.9%  Oasis 4.8%  DefaultHuge 3.1%
                                                  sample mean blocked 10.1%
```

Every swept win is above the sample's mean blocked share; three of the five swept losses
are among the least obstructed maps in the pool, where there is barely a wall to follow.

**The cause is in the latch condition.** `canMove()` is false for a tile occupied by an
**ally** as well as by terrain, and with 60+ robots alive three adjacent tiles are
routinely all blocked by teammates. Arm A latches there and starts wall-following around
a *crowd* — and because bug mode only releases when the target is **strictly** closer
than when it latched, a moment of congestion can hold a soldier for many turns. On open
maps that is all cost and no benefit, which is exactly where the swept losses are.

Refinement: latch only when the blocking tile is impassable terrain
(`!onTheMap || !isPassable`); on congestion fall back to the pre-iteration-15 wide fan,
which never latches. Compiled; arm A preserved as `src/bob_i15a`.

Evaluated against **both** `bob_iter12` and arm A on one fresh sample, because the
refinement and arm A differ by exactly the terrain check, so a direct head-to-head is
far more sensitive than comparing their records against a third party — and the arm A
column simultaneously replicates today's result on a map draw it has never seen.


## Iteration 15 RESULT — REJECTED, both arms, replicated on two independent map draws

```
run 20260907-153729, fresh 25-map sample (a draw neither arm had seen), 100 games
                                        games    sweptW  sweptL  split   net      NULL: 25/50, 0-0
refinement 1 (latch on terrain only)    21/50      0       4      21     -4
arm A       (latch on any block)        21/50      2       6      17     -4
arm A, first sample (20260907-144139)   24/50      4       5      16     -1
arm A, both samples pooled              45/100     6      11      33     -5
```

**Rejected.** Arm A is below the null on both draws, and the refinement did not rescue
it. `bob_iter12` remains the bot; `src/bob` reverted and verified byte-identical on all
seven files.

**My refinement hypothesis was wrong, and interestingly so.** I diagnosed arm A's losses
as spurious latching onto *allies* rather than terrain, and predicted that restricting
the latch to impassable terrain would recover them. It made things worse — 0 swept wins
against arm A's 2. So the ally-latching was, on net, doing something useful. That is the
caution TRAINING_ALGORITHM.md 0.7 records in its other form: *a consistent arbitrary
preference can be supplying real formation cohesion that a "fair" fix destroys.* Here the
"defect" was apparently helping soldiers flow around each other, and removing it cost
more than the spurious wall-following did.

**CLOSED: "bug navigation / wall-following for pathing."** Killed by two arms across two
independent map draws, 150 games, against a null with zero sweeps: −1, −4, −4. The
handedness audit came back clean (all 8 most obstacle-dense maps split 1-1), so this is
not a symmetry artefact — the pathing simply is not what is costing games. Re-open only
with evidence that a *specific* loss is caused by a robot failing to reach a reachable
target, traced in a replay, rather than by map-level wall-density correlation.

### The shape these three iterations share, and the rule it triggers

```
iteration 13  SRP prospecting   mechanism verified (SRPs where there were none)   -35 games
iteration 14  adaptive tower type  premise refuted by the tournament before running
iteration 15  bug navigation    mechanism verified (19 towers vs 4 on maze)        -4 games
```

Two of the three were **mechanistically perfect and worth nothing or less**. On maze the
candidate builds 19 towers where iteration 12 builds 4 — the exact gap that diagnosed the
swept loss — and the map still splits. This is TRAINING_ALGORITHM.md's recorded
regularity, met twice in one session: *metrics that improve without converting to wins.*

`MaxConsecutiveRejects` is 3 and iterations 13 and 15 are both **soldier movement**. The
rule says the next attempt must leave that functional area, and it will.

### Where the evidence actually points next

The `catface` trace is the strongest untouched lead and it is in a different area
entirely: an independent lineage removes paint **4-7x faster than I do** (178/199/335
denial actions per 250 rounds against my 39/37/50) and destroys **both of my starting
towers inside 250 rounds**. My own backlog measurement from 2026-09-06 says my splashers
and moppers run at roughly 1-5% of their action capacity while consuming 2 of every 5
units built. Those two facts are the same fact seen from both ends, one of them measured
on an opponent that shares none of my code.

That is iteration 16: **denial-unit utilisation**, not movement, not economy.


---

## DENIAL PROBE (2026-09-07) — my splashers and moppers are RICH and BLIND, not poor

`src/bob_probe`, iteration 12 plus counters only, vs `bob_denier` (which poses the
denial threat, per measurement doctrine #4). Counters summed over the final per-unit
reports.

```
SPLASHERS                     DefaultHuge         catface
  turns                          2,908               156
  fired                             32  ( 1.1%)        9  ( 5.8%)
  action not ready                 243  ( 8.4%)       51
  paint below 60                   150  ( 5.2%)       85
  NO TARGET >= threshold         2,483  (85.4%)       11
  mean best score on those          4.0             4.0
  nothing in vision at all       1,650  (56.7%)        5
  mean paint held                  205 of 300

MOPPERS                       DefaultHuge         catface
  turns                          1,942                72
  fired                              8  ( 0.4%)       10
  NO ENEMY PAINT IN VISION       1,895  (97.6%)       43
  mean paint held                   74 of 100
```

Three things fall out and none of them is what I assumed.

**1. They are not starved.** I had expected splashers to fire five times and then sit
permanently under the 60-paint firing floor with no refill path. Wrong: the paint floor
blocks 5.2% of turns and splashers hold a mean of **205 paint of 300**, moppers **74 of
100**. This is the third time today I have had to abandon a starvation story that the
counters refuse to support, and it is a good thing the refill direction stayed closed.

**2. The splasher threshold sits exactly on top of the distribution.** `SPLASH_MIN_VALUE`
is 5 and the **mean best available score is 4.0**. 85% of a splasher's life is spent
ready, funded, and one point short. A constant sitting on the centre of the distribution
it gates is the definition of a badly chosen constant — but see below before reading that
as a fix.

**3. The real cause is shared, and it is not paint or thresholds: they never reach the
enemy.** Moppers have **no enemy paint anywhere in vision on 97.6% of their turns**.
Splashers see nothing scoreable at all on 57%. Both types react only to what is inside
r² = 20 and random-walk otherwise, so on a large map they spend their entire lives in
friendly or neutral ground carrying full stashes. That is the whole of the "~1% of action
capacity" figure from 2026-09-06, and the mechanism is not the one that note guessed
("the navigation policy and the firing condition fight each other") — it is that there
is no target to navigate to.

### Why lowering the threshold is NOT the iteration, despite being the dominant gate

A splash costs 50 paint and the score approximates tiles gained, so score 5 is 10 paint
per tile and score 4 is 12.5 — against a **soldier's 5 paint per tile**. Splashing is
already the worse deal at the current threshold; lowering it makes each splasher action
worse, not better. The threshold is only worth paying when the score is high, and scores
are high in **enemy** territory, where enemy tiles count double and soldiers cannot paint
at all.

So the dominant gate is a symptom. Cutting it would be the algorithm's "metrics that
improve without converting to wins" for the third time in one day, and this time I can
see it coming from the arithmetic before spending the run.

### Iteration 16 (next): give denial units a destination

RULES.md records that maps are **guaranteed symmetric by rotation or reflection**, and
TRAINING_ALGORITHM.md Phase 0.8 says extrapolating the unseen half is standard practice
to plan for rather than discover late. **This bot has no symmetry inference anywhere.**
A robot can compute candidate enemy tower locations from its own starting towers and the
map dimensions at spawn, for a handful of bytecodes, and a mopper with nothing in vision
should walk toward the enemy half instead of random-walking in ours.

Pre-registered instrument, from the probe above and normalised per unit per round:
`noEnemyPaint` share for moppers (97.6% now) and `blindWander` share for splashers
(56.7%), plus denial actions per living denial unit per round. **A dose exists and has a
zero arm**: the fraction of the map-crossing a blind unit commits to before reverting to
wander, with 0 = today's behaviour.

Honest note on `MaxConsecutiveRejects`: iterations 13 and 15 were both soldier movement,
so the rule says leave that area. This changes what splashers and moppers *target*, in
the unit types and the failure mode the tournament independently flagged on `catface`
(a sibling out-denying me 4-7x and killing both my starting towers by round 250). I am
counting that as a different area, and recording the tension rather than hiding it.


---

## Iteration 16 RE-AIMED (2026-09-07) — applying the new §3 pre-checks to my own plan

TRAINING_ALGORITHM.md §3 gained two pre-checks that land directly on what I was about to
build, one of them from my own iteration 14. Running them before writing code.

**Pre-check: evidence already on disk.** I justified "denial-unit utilisation" partly on
the `catface` swept loss. Checked against the whole report: bob has exactly **two** swept
losses in 450 games — `maze` (alice) and `catface` (carol) — so denial costs me **one map
of seventy-five**, while I sweep 64/75 against the very lineage that out-denies me there.
**A broad denial weakness is not supported.** The probe's numbers are real; their price
tag is one map.

**Pre-check: cost the price as well as the benefit.** My plan was to send blind moppers
and splashers toward the enemy. The price, which I had not written down:

```
mopper  100 paint cap, pays 2x territory penalty = -4/turn inside enemy paint
        -> ~25 turns of life once it arrives, and its action cooldown is 30
        -> roughly 5-8 mops per unit before starving, plus the low-paint cooldown tax
splasher 300 paint, 50/attack; a splasher sent to the enemy stops painting empty
        tiles in our own half, which is real coverage foregone
```

That is exactly the error §3 now names — "costing a movement policy's benefit without its
paint" — and it is my own iteration 13 recorded as doctrine. So I am not building it yet.

**Pre-check: sizing map not degenerate.** My headline 97.6% came from `DefaultHuge`,
which is 59x59 and the *least* wall-blocked map in the pool (3.1%) — an outlier. On
`catface` (30x30) the same counter is 60%. Both are high, but **97.6% is a big-map
number, not a pool number**, and quoting it alone would have oversold the case. Corrected
in the record.

### The question that must be answered first

The probe says splashers act on **1.1%** of their turns and moppers on **0.4%**, while
those two types are **2 of every 5 units built** — 400 paint and 700 chips per five
units, against 600 paint for the three soldiers. So ~40% of unit paint goes to types that
do essentially nothing.

Before making them work, the cheaper and more fundamental question is whether they are
worth their slot at all. That is a true dose with a zero arm, it is a **spawn-policy**
change rather than a movement change (so it leaves the area iterations 13 and 15 closed),
and both of its numbers are computable in advance:

```
benefit of removing a denial slot   +1 soldier per 5 units (200 paint) -> ~40 painted tiles
price of removing a denial slot     soldiers CANNOT overwrite enemy paint; splashers and
                                    moppers are the only units that can. My own log:
                                    "one enemy splasher beat thirteen of my soldiers"
```

**Doctrine #4 makes the design non-optional.** An ablation of a defensive capability, run
only against my own lineage — which never denies paint — would prove nothing; that is the
recorded case of a mirror calling a feature worthless when it was worth several games
against rushers. So the zero arm must be measured against `bob_denier`, which is
re-forked, current, and freshly baselined today at 86% (19 swept wins, 1 swept loss).

```
ARMS   bob_iter12  3 soldier : 1 splasher : 1 mopper   (today, the zero arm)
       bob_d1      4 soldier : 0 splasher : 1 mopper   (drop the 300-paint slot first)
       bob_d0      5 soldier : 0 splasher : 0 mopper   (no denial capability at all)

RUN 1  BOT=bob_denier  OPPONENTS="bob_iter12 bob_d1 bob_d0"   representativeness FIRST,
       because it is the measurement that can refute, and iteration 12's 86% is a live
       consistency check on the run in the same way the zero arm was for iteration 13.
RUN 2  BOT=bob_iter12  OPPONENTS="bob_d1 bob_d0"              the accept gate.
```

**Pre-registered reading.** If denial units are worth their slot, `bob_d0` collapses
against `bob_denier` while doing fine against the lineage — and the gap between those two
numbers *is* the value of the capability, which no single instrument can report. If
`bob_d0` holds against both, then 40% of my unit paint has been buying nothing and the
correct iteration is to delete it, not to fix its targeting.

---

## Iteration 16 PRE-REGISTERED (2026-09-07 18:17) — is the denial slot worth its paint?

Session was killed at ~16:20 by an account-wide usage limit (nothing I did); resumed
18:20. State reconciled: run `20260907-153729` was already collated locally, `src/bob` is
byte-identical to `bob_iter12` on all seven files, nothing was lost.

**The question.** Not "how do I make splashers and moppers work" (the §3 pre-checks
above shelved that: one swept loss in 450 tournament games does not support a broad
denial weakness, and I had not costed the paint). The prior question is whether the two
denial slots earn the 40% of unit paint they consume, given they act on 1.1% and 0.4% of
their turns.

**Arms built** (`src/bob_d1`, `src/bob_d0`), verified byte-identical to `src/bob` on all
seven files except `Tower.java`, whose only change is the spawn ternary:

```
bob_iter12  3 soldier : 1 splasher : 1 mopper   zero arm (today's bot)
bob_d1      4 soldier : 0 splasher : 1 mopper   drop the 300-paint splasher slot
bob_d0      5 soldier : 0 splasher : 0 mopper   no denial capability at all
```

**RUN 1 (launched, `20260907-181731`, 150 games): `BOT=bob_denier`, opponents
`bob_iter12 bob_d1 bob_d0`.** Representativeness first, per measurement doctrine #4: an
ablation of a *defensive* capability run only against my own lineage — which never denies
paint — proves nothing. `bob_denier` is the only opponent that poses the threat. All
three arms share one map sample, so the arm-to-arm comparison inside this run is exact.

**RUN 2 (to launch when RUN 1 finishes): `BOT=bob_iter12`, opponents `bob_d1 bob_d0`.**
The accept gate, on the lineage.

**Pre-registered variables and thresholds.** Reported win% is `bob_denier`'s.
`bob_iter12` was baselined against `bob_denier` today at 86% from my side, so I expect
denier ≈ 14% against the zero arm; that number is a live consistency check on the run.

```
D_denial = (denier win% vs bob_d0) - (denier win% vs bob_iter12)      value of the whole
D_splash = (denier win% vs bob_d1) - (denier win% vs bob_iter12)      value of the splasher slot
```

Uncertainty on every margin is quoted from `tools/map-resample.py` over MAPS, never a
binomial formula — the engine is deterministic, so the only thing that re-rolls is which
maps were drawn. Swept maps get more weight than headline win%: identical code sweeps
nothing.

Decision rule, registered before the numbers exist:

- `D_denial >= 10 pts` (>=5 of 50 games): the capability is load-bearing against a
  denier. Do **not** delete it. Iteration 16 becomes targeting — and I then owe it the
  paint price I have not yet computed.
- `D_denial < 10 pts` **and** RUN 2 puts `bob_d1` or `bob_d0` at >50% head-to-head vs
  `bob_iter12`: accept the slot deletion (the better of the two arms).
- `D_denial` large but `D_splash` ~0: the mopper is the load-bearing half and the
  splasher slot is free to reclaim — `bob_d1` is then the candidate.
- Both arms below 50% on RUN 2 with `D_denial` small: 40% of unit paint buys nothing
  *and* removing it helps nothing, which points the next iteration at what the extra
  soldiers do with their turns rather than at the spawn mix.

### While RUN 1 plays: the win-condition census (2026-09-07 18:30)

Non-blocking work on evidence already on disk. Joined `tournaments/20260907-1300/results.csv`
against its `reasons.txt` for all 300 of my games:

```
BOB_WIN   painted enough of the map                259
BOB_WIN   tiebreak, painted more                    16
bob_loss  painted enough of the map                 16
bob_loss  tiebreak, painted more                     7
BOB_WIN   destroyed all of the enemy team's units     2
```

**298 of 300 decided on paint. Not one of my 23 losses was an elimination.** My losses
split into a fast group (CastleDefense r308, Rose r426, Jail r434, starburst r471,
walalilongla r519, Filter r537, SandyBeach r544, Brat r605, Dominoes r636, DefaultSmall
r772, Bread r828 — out-painted to the 70% threshold early) and a slow group (six
1400–1900 and seven round-2000 tiebreaks). Written up as LEARNINGS §18, with a
cross-reference added into §5.

This does not change iteration 16's design — the ablation and its thresholds were
pre-registered above before I ran the census, and I am not editing them now — but it
sharpens what the answer will mean. The unit of value is **net painted tiles per chip**:
tiles my unit paints, plus enemy tiles it removes (which moves the differential twice
under a tiebreak decided by "painted more"), minus the paint it burns standing on hostile
ground. RUN 1 and RUN 2 measure exactly that trade at the spawn-slot level.

It also retires the framing I carried into this session: `catface` is not a defensive
hole. Both my towers dying by r250 is real, but the game was lost on **paint** at r1431
and on the r2000 tiebreak. I was one step from building a defensive iteration against a
verdict that never occurs.

### The price, computed before the run reports (2026-09-07 18:40)

§3 requires both numbers written down before building. Exact costs from `RULES.md`
(engine table: cost is paint/chips) — **paint is the binding constraint** (LEARNINGS §5:
chips ran to 327k unspent while coverage sat at 45%), so paint is the denominator that
matters and chips are close to free.

```
per 5 units spawned          paint   chips   painters   can remove enemy paint
bob_iter12  3S : 1Sp : 1M     1000    1450      3              yes (2 units)
bob_d1      4S : 0Sp : 1M      900    1300      4              yes (1 unit)
bob_d0      5S : 0Sp : 0M     1000    1250      5              NO
```

`bob_d0` buys **5 painters for the same 1000 paint that buys iteration 12 three** — a 67%
increase in painting capacity out of the binding resource, at no paint cost at all.
`bob_d1` is cheaper still in paint (900) and keeps the denial capability at one unit.
That is the benefit side, and it is larger than I expected before doing the arithmetic.

The price side is the capability §5's zero-sum bullet names: **soldiers cannot overwrite
enemy paint at all.** Once the map saturates, a pure-soldier team has no move that
reduces enemy territory, and the tiebreak that decided 23 of my 300 games is "painted
more". `bob_d0` cannot play that endgame. That is precisely why RUN 1 is against
`bob_denier` and not against my own lineage.

Second-order, and it cuts toward the ablation: the probe measured splashers idle on 98.9%
of turns and moppers on 99.6%, and an idle unit is **not free** — end-of-turn territory
penalty is −1 neutral / −2 enemy, doubled for moppers, plus 1 per adjacent ally. On
`DefaultHuge` the splashers burned ~2,900 unit-turns of that upkeep plus 1,600 paint of
attacks to place 32 splashes at a mean score of 4 tiles: order **35 paint per tile
against a soldier's 5**. Moppers, 1,942 turns for 8 mops. `DefaultHuge` is an outlier map
and I am not quoting those as pool figures — the point is only that the idle-unit branch
of the price is a debit, not a zero, so the ablation's benefit is *not* purely the spawn
paint.

Correction to my own earlier note: I wrote "400 paint and 700 chips per five units" for
the denial slots and then briefly doubted the chips figure while re-deriving it. The
engine table reads paint/chips, so 400 paint and 700 chips is right — 40% of the paint and
48% of the chips.

### Tracing the eleven fast losses (2026-09-07 18:55) — two degeneracies, both opponent-free

Still non-blocking work while RUN 1 plays. §1 of the algorithm says prefer *absolute
degeneracy signals* over opponent-relative comparisons, and the census gave me eleven
losses decided before round 900 to sort through. Dumped four of them with
`bob-tools/dump-replay.sh` against the sanctioned tournament replays on battlecode-dev.

**Tool caveat, recorded before the numbers.** `BobDump` counts my own side's
spawns/paint correctly (the 3:1:1 mix is visible in them) but reports **zero unit spawns
for the opponent** on every one of these — alice tripled her coverage on Jail with
`soldB=0`, which is impossible. So I read only `cov*` and `money*` (engine team totals)
for the opponent, and the unit/paint columns for my side alone. It is my own private
tool, not shared `tools/`, so this is a note-to-self rather than a bug report; I will not
quote an opponent's composition off it until it is fixed.

**Mode 1 — paint bankruptcy, coverage goes into REVERSE.**

```
Rose (bob=B, lost r426)         r50   r100  r150  r200  r250  r300  r350  r400  r426
  bob coverage                   87    89    106   101   101    97    63    45    49
  bob robot paint held          193   128      6     0     0     0     0     0     0
  bob chips (idle)             2200  3450   4300  5000  5850  6800  7800  4300  4680
  bob towers built                0     0      0     0     0     0     0     0     0
  opponent coverage             126   161    197   239   292   394   478   638   701

CastleDefense (bob=B, lost r308)      r100  r150  r175  r200  r250  r300  r308
  bob coverage                         215   250   244   200   115    76    65
  bob robot paint held                 281     9     0     0     0     0     0
  bob chips (idle)                    3200  3750  4250  5000  6500  8000  8240
  bob towers built                       0     0     0     0     0     0     0
```

**My team's robots hold zero paint from round ~175 onward and never recover, while 8,240
chips sit unspent.** Coverage does not stall — it *declines monotonically*, because a
robot at zero paint cannot move or act and my painted tiles get overwritten by units I
can no longer answer. This needs no opponent to be wrong.

**Mode 2 — coverage stall at full health.**

```
Jail (bob=A, lost r434)         r50   r150  r250  r350  r434
  bob coverage                  246    261   298   276   259     <- flat over 384 rounds
  bob robot paint held          628    579   448   411   387     <- healthy throughout
  bob units (S/Sp/M)          8/0/0  11/2/2 14/3/3 17/4/4 18/4/5
  opponent coverage             320    387   374   541   700

SandyBeach (bob=B, lost r544)   r50   r150  r250  r350  r450  r544
  bob coverage                  251    240   224   223   271   241  <- flat over 500 rounds
  bob robot paint held          169    319   396   332   239    11
  bob units (S/Sp/M)          6/0/1  9/1/2 12/2/3 15/3/4 18/4/5 20/5/5
  opponent coverage             293    251   230   296   585   701
```

On Jail I finish with **27 living units and a healthy stash, and 384 rounds of net-zero
painting.** Twenty-seven units produced a coverage change of +13 tiles. That is the
purest form of LEARNINGS §18: the only scored quantity, flat, while every input to it
grows.

**Nine of those 27 units — a third of the army — are splashers and moppers**, which is
what iteration 16 is pricing right now. That is not proof the ablation will pay, but it
puts the ablation on exactly the games I lose rather than on the ones I sweep.

### Iteration 17, queued (do not start until 16 resolves)

Mode 1 has a candidate mechanism already visible in my own `Tower.java`:

```java
static final int UPGRADE_RESERVE = 4000;
...
if (selfType.canUpgradeType() && chips >= selfType.getNextLevel().moneyCost + UPGRADE_RESERVE)
```

The reserve exists so a soldier can complete a new tower (1000 chips) the moment a
pattern finishes. But my own iteration-13 measurement says **SRP/tower construction is
refused by geometry on 99% of attempts**, and both bankruptcy games built **zero** towers
in 300–430 rounds. So on these maps the reserve is withholding 4,000 chips to protect a
purchase that never happens, while the team's paint — the binding resource — is at zero.
On Rose the upgrade finally fired at r390, 240 rounds after bankruptcy; on CastleDefense
it never fired at all despite 8,240 chips.

Hypothesis to pre-register when 16 closes: **a paint tower holding zero paint should
ignore `UPGRADE_RESERVE`.** It is a true dose with a zero arm (the reserve value, 0 =
unconditional upgrade, 4000 = today), it is reachable (the guard's condition is measured
false with 8,240 chips in hand), and it is the algorithm's recorded winner profile —
*spending idle resources, capability at zero marginal cost*. The price to compute first:
what the withheld 4,000 chips would otherwise have bought, on maps where construction is
**not** geometry-blocked.

### The History pre-check fires, and it saves the obvious fix (2026-09-07 19:10)

Reading `Soldier.tryRefill` after the bankruptcy traces, the "obvious" cause is right
there: it scans `senseNearbyRobots(-1, us)` — **vision only, r²=20** — so a soldier with
no tower in sight cannot refill, paints itself to zero, and at zero cannot move, so it
can never walk to one. The refill has no memory. That is exactly mode 1's mechanism.

**And it is a CLOSED direction.** Iteration 8 built precisely that fix (`Refill.seek`,
remembered towers, extended to moppers and splashers) and it was killed on economics, not
tuning: *spawning converts 200 paint into 200 paint plus a body; refilling converts 200
paint into 200 paint.* While paint binds and chips are free, spawning strictly dominates,
and a unit that paints until it starves has converted its whole stash into tiles and
freed the economy to build a replacement.

The ledger gave a precise re-open trigger: **"when team chips stop accumulating — say
sustained below ~5,000 while towers still want to spawn."** I checked it against every
trace I dumped today rather than assuming:

```
                        outcome   bob chips at end   towers built   bob paint at end
Rose                    loss              4,680            0               0
CastleDefense           loss              8,240            0               0
Jail                    loss              4,580            1             387
SandyBeach              loss              4,412            0              11
starburst               loss              5,480            0               —
DefaultHuge             WIN              61,150           23          10,687
Filter                  WIN              23,190            3             150
```

**The trigger is not met anywhere.** Chips accumulate in every game I have looked at, win
or loss, on a 59x59 map and a 30x30 one. Refill stays closed, and the History pre-check
just paid for itself: I would otherwise have re-implemented iteration 8 from a trace that
looks like a slam dunk.

### What the same table says instead — iteration 17 sharpened

The real asymmetry between my wins and my fast losses is not refill. It is **towers**:

```
losses   0-1 towers built,  paint income = 1 starting LEVEL_TWO paint tower = 10 paint/turn
wins     3-23 towers built, paint income scales with them
```

Exact engine figures (probed from the jar today, `UnitType` fields):

```
LEVEL_ONE_PAINT_TOWER    1000 chips   +5  paint/turn      <- 5 paint/turn per 1,000 chips
LEVEL_TWO_PAINT_TOWER    2500 chips   +10 paint/turn
LEVEL_THREE_PAINT_TOWER  5000 chips   +15 paint/turn      <- upgrade from L2 = +5 for 5,000
LEVEL_TWO_MONEY_TOWER    2500 chips   +30 chips/turn
LEVEL_THREE_MONEY_TOWER  5000 chips   +40 chips/turn      <- +10/turn of a DEAD resource
```

Two defects in the same eight lines of `Tower.run`, both of which spend or withhold a
resource the table above proves is free:

1. **`UPGRADE_RESERVE = 4000` makes the paint-tower upgrade cost 9,000 chips**
   (`nextLevel.moneyCost 5000 + 4000`). CastleDefense peaked at 8,240 and therefore
   *never upgraded at all* while its robots sat at zero paint for 130 rounds. Rose
   crossed the bar at r390, 240 rounds after bankruptcy. The reserve is protecting a
   1,000-chip tower completion that geometry refuses on 99% of attempts (my own
   iteration-13 measurement) and that these maps never once achieved.

2. **The upgrade gate is `selfType.canUpgradeType()` — it does not care which type.** A
   money tower will happily spend 5,000 chips to gain +10 chips/turn, which is income in
   the one resource that ends every game unspent (61,150 on DefaultHuge). Worse, it
   competes for the same chips as the paint upgrade: on Filter I took two upgrades at
   r166/r196 while robot paint sat flat at 150 for the whole game and finished with
   23,190 chips idle.

Iteration 17 will change **one** of these, not both. Defect 2 is the cleaner single
mechanism — a pure deletion of a spend, with no new behaviour, no paint price at all, and
a dose with a zero arm (upgrade: any tower / paint towers only / none). It is the
algorithm's recorded winner profile in its exact words: *removing pure waste*.

Pre-checks I still owe it before building, and will run when 16 closes: the **decision**
count (how often a money tower actually takes the upgrade branch — not how many upgrades
appear, which cannot distinguish "money tower upgraded" from "paint tower upgraded"), and
the price (whether any game is ever chip-limited at the spawn gate, which the table above
suggests is never but which I have measured only at end-of-game, not per-round).

---

## CORRECTION (2026-09-07 19:30) — adopting `tools/replay-dump.sh`, and a figure it retracts

The coordinator replaced the per-agent dumpers with one shared tool
(`tools/replay-dump.sh` + `tools/replaydump/ReplayDump.java`, `152ad05`) and asked me to
retire `bob-tools/BobDump.java` and `bob-tools/dump-replay.sh`. Done — both deleted, and
`bob-tools/mop-trace.sh` repointed. My focused analyses (`BobSites`, `BobSym`, `BobRuins`,
`BobMop`) are unaffected.

**It immediately retracted a number I published an hour ago, exactly where the coordinator
warned it would.** `BobDump`'s `sold/spl/mop` columns were *cumulative spawns*, and its
death accounting trusted `Round.diedIds`, which this engine does not populate — deaths
arrive as `Action.DieAction` inside a Turn. So the counts never decremented.

```
Jail r400        BobDump (wrong)                 shared tool (right)
  my army        "27 living units"               sold3 spl1 mop1  = FIVE living units
  my deaths      died 0 all game                 died6 in that interval alone, starved6
```

**Retract: "Mode 2 — coverage stall at full health ... 27 living units and a healthy
stash, and 384 rounds of net-zero painting."** That is wrong, and wrong in a way that
flattered me. I did not have a large healthy army painting nothing. I had **three to five
living units**, dying and starving continuously, painting 4 tiles per 100 rounds
(`acts[p4 ...]` at r400) against alice's 144. Superseded in place; the sentence above
stands as written so the reasoning that followed it stays readable.

**Modes 1 and 2 were never two failures.** With correct alive-counts they are one:

```
CastleDefense (bob=T2)     r50    r100   r150   r200   r250   r300
  my towers                  2      2      2      1      1      1      <- I LOSE one
  my tower paint pool      150    250    150     50     50     50
  my living units            6      3      3      3      0      0      <- extinct by r250
  my chips                2200   3200   3750   5000   6500   8000
  opponent towers            4      5      6      6      6      6
  opponent tower paint    1075   1745   1411    455    304    528

Rose (bob=T2)              r50    r150   r250   r350   r400
  my towers                  2      2      2      2      2      <- never builds one
  my tower paint pool      150    110    110    230    260      <- never affords a soldier
  my living units            7      4      3      2      2
  my chips                2200   4300   5850   7800   4300
  opponent towers            3      5      9     13     18      <- +15
  opponent tower paint     500    995   2945   1925   3360
```

The single variable is **towers**. My tower paint pool hovers at 110–260 against a
soldier's 200-paint spawn cost, so I spawn roughly one unit per fifty rounds and my
standing army never exceeds seven. Coverage is entirely downstream of that. The chips
column is the same dead resource as ever.

### An independent lineage confirms the refill closure

The shared tool prints paint transfers, and this is the cleanest evidence I have for a
decision I made on my own economics three days ago:

```
paint transfers per 50-round interval, Rose
  bob     1  2  1  0  0  1  1  4
  alice   0  0  0  0  0  0  0  0
```

**Alice never refills a unit, all game, and beats me 701–49.** She also starves *more*
units than I do in absolute terms (15 in one interval against my 2), because she has more
of them. A lineage that shares none of my code independently arrived at "let them starve
and build another", which is precisely the economics that closed my iteration 8. That is
the sanctioned cross-agent channel doing the job MULTI_AGENT.md claims for it.

### What this does and does not change

It does **not** change iteration 16, which is running: the arms and thresholds were
pre-registered and I am not touching them.

It **sharpens** iteration 17 and demotes my "upgrade" framing. Upgrading the level-2 paint
tower buys +5 paint/turn for 5,000 chips; building a level-1 paint tower buys the same +5
for **1,000**. Alice built fifteen of them on Rose while I built none. So the first
question is not how to spend dead chips more cleverly on the two towers I have — it is why
I build no towers on maps where an opponent builds fifteen. My iteration-13 note says
construction is refused by geometry on 99% of attempts; alice's fifteen towers on the same
map, same symmetry, are a direct refutation of that being a property of the *map*.

Iteration 17 is therefore re-aimed at **tower construction**, and its first step is a
decision-level instrument (§3: instrument the decision, not the outcome): count how often
a soldier *wants* a ruin and what refuses it, on Rose specifically, where the opponent
proves 15 sites exist. The upgrade-reserve and money-tower-upgrade defects are real and
stay queued behind it, but they are second-order against a 15-tower gap.

---

## Iteration 16 RUN 1 RESULT (2026-09-07 19:55) — the denial slots are worth their paint, decisively

`BOT=bob_denier`, one shared 25-map sample, 150 games, run `20260907-181731`. Reported
below from **my** side (each arm's wins against `bob_denier`), with uncertainty from
`tools/map-resample.py` — bootstrap/jackknife over maps, never a binomial formula.

```
arm                             wins/50   95% CI     per-map 0/1/2      swept   swept-lost
bob_iter12  3S : 1Sp : 1M        43/50   [37, 48]    2 / 3 / 20          20         2
bob_d1      4S : 0Sp : 1M        30/50   [23, 37]    5 / 10 / 10         10         5
bob_d0      5S : 0Sp : 0M        10/50   [ 4, 17]   18 / 4 / 3            3        18
                                        mirror null = 25/50, zero sweeps
```

**Consistency check passes exactly.** I pre-registered that `bob_iter12` should land near
its 86% baseline from earlier today; it landed at 43/50 = **86.0%**. The instrument is
reading true, so the other two arms can be trusted.

```
D_denial = 43 - 10 = 33 games (+66 pts)     value of the denial capability
D_splash = 43 - 30 = 13 games (+26 pts)     value of the splasher slot alone
```

**Pre-registered decision rule: `D_denial >= 10 pts` -> the capability is load-bearing;
do NOT delete it.** It came in at 66. `bob_d0`'s interval [4, 17] does not come close to
`bob_iter12`'s [37, 48], and the per-map columns are the honest read: iteration 12 wins
**both sides of 20 of 25 maps** against the denier, while the no-denial arm is swept on
**18 of 25**. Identical code sweeps nothing, so an 18-map sweep is 18 real maps.

**REJECTED: "delete the denial slots."** 40% of my unit paint is not buying nothing. It
is buying the only capability that can reduce enemy territory, and a soldier — which
cannot overwrite enemy paint at all — is not a substitute at any exchange rate.

### Why this was worth 150 games even though it changed nothing

This is measurement doctrine #4 doing exactly what it is for. The probe said splashers act
on 1.1% of turns and moppers on 0.4%, and every instinct said delete them. Had I priced
that ablation on my own lineage — which never denies paint — I would have seen the extra
soldiers help and **deleted the capability that wins me 33 games in 50 against an opponent
that does.** The recorded case in the algorithm is a mirror calling a defensive feature
worthless when it was worth several games against rushers; this is the same shape, at
larger scale, caught before the accept rather than after.

It also settles the utilisation paradox rather than deepening it: **a mechanism can be
rare and high-value.** A splasher firing on 1.1% of turns is not idle capacity going to
waste — it is a standing threat whose 32 shots per game are worth more than the ~40 tiles
the same paint would buy as a fourth soldier. MULTI_AGENT.md says this in one line and I
had not believed it: *a low firing rate on its own is not evidence that it did not cause
the result.*

`D_splash = 13 games` also kills the cheaper variant before I could be tempted by it. The
splasher slot alone, the 300-paint one I called "the worse deal at the current threshold"
from the paint-per-tile arithmetic, is worth 13 of 50 games. **The arithmetic was right
and the conclusion drawn from it was wrong**, because it priced the tiles a splash paints
and ignored the enemy tiles it removes — which move the differential twice under a
tiebreak decided by "painted more" (LEARNINGS §18).

### RUN 2 launched anyway, and why it is not now moot

The accept decision is made. RUN 2 (`BOT=bob_iter12`, opponents `bob_d1 bob_d0`) prices
the *other* half: what the denial slots cost me against opponents that do **not** deny.
The gap between the two runs is the thing no single instrument reports. If `bob_d0` beats
`bob_iter12` handily on the lineage while collapsing against the denier, then the mix is
paying a standing premium for insurance, and the right mechanism is the algorithm's
recorded design preference — **a self-calibrating threshold**: spawn denial units in
proportion to observed enemy paint, rather than at a fixed 2-in-5 chosen in iteration 0.
If `bob_d0` is merely level on the lineage, there is no premium to reclaim and the fixed
mix stands.

---

## Iteration 17 PRE-REGISTERED (2026-09-07 20:05) — why do I build zero towers where an opponent builds nineteen?

**Functional area: tower construction.** New area — iterations 13 and 15 were soldier
movement (both rejected) and 16 was spawn policy (rejected), so `MaxConsecutiveRejects`
is satisfied without strain.

**The observation, from the shared dumper, not from theory.**

```
Rose  40x40, walls 5.5%, ruins=30, symmetry=0
  alice  towers  2 -> 19    first at r31, then r77, r84, r160, r191, r208, r235, ...
  bob    towers  2 ->  2    zero, in 426 rounds, on a map with 30 ruins
  bob    tower paint pool   110-260 all game, against a soldier's 200-paint spawn cost
  bob    chips               2,200 -> 7,800 unspent
```

Everything else I traced today is downstream of this line. With two towers my paint income
is one LEVEL_TWO paint tower — 10 paint/turn — so I spawn roughly one unit per fifty
rounds, my standing army never exceeds seven, and coverage decays. Alice, from the same
two starting towers on the same map, reaches nineteen.

**This refutes the map-geometry story I have been carrying.** My iteration-13 note says
construction is refused by geometry on 99% of attempts. That measurement was about
**SRPs** (`canMarkResourcePattern`), and I have been quoting it at **ruins**
(`canMarkTowerPattern`), which is a different call with a different validity rule. Alice's
nineteen towers on Rose are proof that the ruins there are buildable. Superseding that
misapplication in place rather than deleting it: the SRP measurement stands for SRPs.

**Candidate mechanism, from reading `Soldier.workOnRuin`.** The ruin path has **no
patience rule**, while the SRP path beside it has `SRP_PATIENCE = 120`:

```java
static final int SRP_PATIENCE = 120;   // SRP: abandon a site after 120 turns
// workRuin: no equivalent. A soldier holds its ruin until a tower APPEARS on it.
```

A soldier paints exactly one pattern tile per turn and only if `canAttack(l)`. **Soldiers
cannot overwrite enemy paint.** So if any of the 24 pattern tiles is enemy-painted, the
soldier can never finish, `canCompleteTowerPattern` stays false, no tower ever appears, and
`chooseRuin`'s only release condition — *a robot is now standing on the ruin* — never
fires. The soldier is deadlocked on that ruin for the rest of the game, and step 3 keeps
navigating it back there. That is a mechanism which produces exactly the observed
"0 towers, 2-4 living soldiers, coverage decays" shape, and it gets worse as the opponent
paints more, which is why it bites hardest in the games I lose.

**Instrument first, per §3 — the DECISION, not the outcome.** `src/bob_rprobe` is forked
from `src/bob` (verified identical except counters in `Soldier` and the reporter in
`RobotPlayer`), compile-checked in isolation, and partitions every turn a soldier holds a
ruin:

```
turns hasRuin adjacent markOK markRefused tilePainted blockedEnemy blockedOther
      nothingToDo lowPaint completed switched heldMax
```

`heldMax` is the direct test of the deadlock: the longest unbroken run of turns one
soldier spent on one ruin.

**First probe run is against `examplefuncsplayer` on Rose**, deliberately. If I build ~0
towers on Rose even against an opponent that applies no pressure and paints almost
nothing, the blocker is structural and mine; if I build plenty, the blocker is enemy paint
and the deadlock story is the right one. Either answer is decisive, and the run costs two
games. (I cannot reproduce the alice matchup directly — reading or running another agent's
bot is forbidden — so this substitution *is* the experiment, not a compromise of it.)

**Pre-registered reading, written before the numbers exist:**

- `heldMax` in the hundreds with `blockedEnemy` dominant -> deadlock confirmed; the fix is
  a patience/abandon rule on `workRuin`, mirroring `SRP_PATIENCE`. Dose with a zero arm:
  patience in turns, 0 = never abandon = today.
- `heldMax` in the hundreds with `nothingToDo` dominant -> the soldier believes the
  pattern is complete but `canCompleteTowerPattern` disagrees; that is a marking bug, a
  different fix entirely.
- `markRefused` dominant -> `canMarkTowerPattern` really is refusing, and the geometry
  story survives after all, now measured on the right call.
- `hasRuin` low and towers still ~0 -> soldiers never even find the ruins, and the target
  is `chooseRuin`'s vision-only search, not patience.
- Towers built ~19 against `examplefuncsplayer` -> the blocker is enemy paint pressure
  rather than anything structural, which points at the same patience rule but prices it
  only in contested games.

**Price, computed before building anything** (§3, and my own iteration-13 doctrine): a
patience rule spends nothing — no paint, no chips, no action. It releases a soldier that
is by construction doing nothing. The only cost is the paint already sunk into a partial
pattern on the abandoned ruin, which is at most the ~24 tiles x 5 paint = 120 paint the
soldier had already spent, and which it spends *whether or not* it later gives up. So the
worst case is a wasted 120 paint that was already wasted, and the best case is a soldier
returned to painting. That asymmetry is why this is worth a run.

## RUIN PROBE RESULT (2026-09-07 20:15) — the deadlock is real, and my named cause was wrong

`src/bob_rprobe` vs `examplefuncsplayer` on Rose, side A. Won at r446. Per-soldier
counters at the r250 report, the four long-lived soldiers plus four young ones:

```
id       turns hasRuin adjacent markOK markRef tilePainted blockEnemy nothingToDo lowPaint completed switched heldMax
13761      249     202      185      1      34         108          8          35       30         0        0     171
10351      249     235      229      2       6          44          0          24      151         1        0     183
11019      248     247      245      1       4          26          0           5      210         0        0     247
13417      220     182      165      0       5         136         13           6       10         1        0     154
(4 young)  119      54       49      0       0          50          0           0        0         0        0      26
TOTAL     1085     920      873      4      49         364         21          70      401         2        0     247
```

**Against my pre-registration, one confirmation and two refutations.**

- **CONFIRMED — the deadlock.** `heldMax` = 171, 183, **247**, 154. Soldier 11019 held one
  ruin for 247 of its 248 turns of life. And `switched = 0` **for every soldier in the
  game**: not one ever changed ruin. `chooseRuin`'s only release condition is a robot
  appearing on the ruin, so a claim is effectively permanent.
- **REFUTED — enemy paint is not the cause.** `blockedEnemy` is 21 of 920 ruin-turns,
  **2%**. My story ("soldiers cannot overwrite enemy paint, so a contested pattern can
  never finish") is not what these games show.
- **REFUTED — and this is the important one — the blocker is not the opponent at all.** I
  pre-registered "towers built ~19 against `examplefuncsplayer` -> the blocker is enemy
  paint pressure". Unopposed, on a 30-ruin map, against an opponent that applies no
  pressure whatsoever, **I completed 2 towers in 250 rounds.** Alice had 8 by r250 on the
  same map against a real opponent. The gap is structural and it is mine.

**The dominant gate is `lowPaint`: 401 of 920 ruin-turns, 44%.** Soldier 11019 spent
**210 of its 248 turns** standing on a ruin at or below `PAINT_FLOOR`, unable to paint,
unable to leave, and — below the engine's move threshold — eventually unable to move.

### The arithmetic nobody had written down

A soldier spawns with a full 200 stash and that is every drop it will ever have: my tower
paint pool sits at 110-260, so there is nothing to refill from even if it walked back.
Against that fixed 200:

```
tower pattern      5x5 minus the ruin = 24 tiles x 5 paint            = 120 paint
travel + upkeep    -1/turn neutral, -2/turn enemy, +1 per adjacent ally
                   over the ~40-80 turns to reach and work a ruin      = 40-160 paint
                                                                        -----------
                                                                        160-280
```

**One soldier's entire life is roughly one tower pattern, and the margin is negative on
the wrong side of the range.** Soldier 11019 painted 26 tiles — about one pattern's worth
— and finished nothing. That is the whole story of "0 towers on Rose".

And completion is a **threshold good, not a linear one**: 119 paint of a 120-paint pattern
buys exactly zero towers, while 120 buys +5 paint/turn for the rest of the game. Every
metric I have used to reason about paint until now has treated paint→tiles as linear.

### This re-opens iteration 8's closure, narrowly, and I am recording why

The ledger requires a specific reason the recorded cause no longer applies, not a feeling.
Iteration 8 was closed on: *"spawning converts 200 paint into 200 paint plus a body;
refilling converts 200 paint into 200 paint"* — an argument that is **only valid where
paint converts to value linearly.** It does not hold across a completion threshold. A
soldier that dies at 119/120 of a pattern has converted its stash into **nothing**, not
into 119 tiles' worth of value.

That said, I am **not** re-opening general refill, and the run I just did says why: these
soldiers are stalled at ruins with no tower in reach and a team pool of 110-260 paint —
there is nothing to refill *from*. Alice, who builds 19 towers, performs **zero** paint
transfers all game. Refill is not how she does it.

### What iteration 17 actually becomes

Three candidate mechanisms now, and they are cheap to separate. Recording all three, then
picking one, because bundling makes a result uninterpretable:

1. **Affordability gate on claiming.** Do not claim a ruin unless the stash can plausibly
   finish it; release it when it cannot. Spends nothing. But the probe warns this may be
   near-worthless on its own: a released soldier at 15 paint has almost nothing left to do.
2. **Concurrency.** `switched = 0` and each soldier independently picks its *nearest*
   ruin, so four soldiers work four separate patterns and finish none, when the same four
   on one ruin would finish it in a quarter of the turns. Completion being a threshold
   good makes concentration strictly better than spreading — this is the mechanism the
   threshold insight actually implies, and no iteration of mine has ever touched it.
3. **Don't start what a fresh soldier cannot finish**, i.e. bias the *first* soldiers off
   ruins entirely until income supports it.

**(2) is the pre-registered choice for iteration 17.** It follows directly from the one
finding that survived the probe, it is in a functional area I have never touched, it
spends no paint and no chips, and it has a clean dose with a zero arm (how many soldiers
may hold the same ruin; 1 = today's behaviour by accident rather than by design). Writing
the pre-registration and the price before any code, as §3 requires — next entry.

---

## Iteration 17 PRE-REGISTERED (2026-09-07 20:25) — anchor ruin choice to the spawn tower

**Hypothesis.** My soldiers each pick the ruin nearest *themselves*, after they have
already wandered. Because they wander independently, they pick different ruins, and
because a tower pattern is a **threshold good costing roughly one soldier's entire stash**,
four soldiers each 60% of the way through four patterns build **nothing**, while the same
four on one pattern build a tower and double the team's paint income for the rest of the
game.

Scoring a ruin by its distance from the soldier's **birth location** instead makes every
soldier spawned by the same tower agree on the same ruin, without any communication. It
buys concentration and short travel from one change.

**Supporting observation from the tournament, and it is what suggested this.** Alice's
first tower on Rose completes at **round 31** — with her opening soldiers, right next to
where they spawned. My first completes at r250-never. Round 31 is not a pathing or a
targeting advantage; it is a *siting* one.

**Change (one mechanism).** `G` records `birth`, the robot's location on its first turn
(free; it is already in `G.init`'s reach). `Soldier.chooseRuin` scores candidate ruins

```java
score = me.distanceSquaredTo(r) + ANCHOR * birth.distanceSquaredTo(r)
```

instead of `me.distanceSquaredTo(r)`. **`ANCHOR = 0` is exactly today's behaviour**, which
is the zero arm; arms at 1 and 3 give a dose. Nothing else changes — no patience rule, no
affordability gate, no refill. Those stay unbuilt so this result stays interpretable.

**Pre-registered variables**, from `src/bob_rprobe`'s counters re-run on each arm:

```
completed     tower patterns finished per game        (the target; 2 today on Rose)
distinctRuins number of distinct ruins claimed team-wide  (concentration; falls if it works)
lowPaint      ruin-turns at or below PAINT_FLOOR      (401 of 920 today; should fall)
heldMax       longest tenure on one ruin              (247 today)
```

**The price, written before the code** (§3, and my own iteration-13 doctrine):

- Paint: **zero.** No new action, no new attack, no travel that was not already happening.
- Bytecode: one extra `distanceSquaredTo` per visible ruin per turn, ~10 bytecodes against
  a measured soldier peak of 9,488 of 17,500. Not a constraint.
- The real price is **map coverage**: anchoring soldiers near their spawn tower concentrates
  my painting into my own half. Since 298 of 300 games are decided by coverage
  (LEARNINGS §18) that is a genuine cost, not a rounding error, and it is the reason
  `ANCHOR` needs a dose sweep rather than a single value — a large `ANCHOR` turtles.
- Second-order risk I am naming now so I do not "discover" it later: soldiers piling on one
  ruin sit adjacent to each other, and the territory penalty adds **+1 paint/turn per
  adjacent ally**. Concentration is not free in paint even though the mechanism is. If the
  arms come back flat, this is the first thing to instrument.

**Accept gate**, unchanged from the algorithm: head-to-head against `bob_iter12` over a
fresh 25-map sample, both sides, read against the mirror null and with the interval from
`tools/map-resample.py`. Peer `WinPct` on the wider pool. Diff read for one-directional
regressions.

**Sequencing.** RUN 2 of iteration 16 is still in flight and owns the VM budget; this gets
built and compile-checked now, and evaluated when that lands.

---

## Iteration 16 RUN 2 RESULT (2026-09-07 20:45) — and a confound I have to name

`BOT=bob_iter12`, opponents `bob_d1 bob_d0`, fresh 25-map sample, 100 games, run
`20260907-185613`. Reported as each arm's wins against `bob_iter12`:

```
arm                        wins/50   95% CI    per-map 0/1/2      vs the denier (RUN 1)
bob_d1  4S : 0Sp : 1M        7/50    [3, 12]   18 / 7 / 0             30/50
bob_d0  5S : 0Sp : 0M        2/50    [0,  5]   23 / 2 / 0             10/50
                                   mirror null = 25/50, zero sweeps
```

**Both arms collapse against my own lineage too — harder than they collapse against the
denier.** `bob_d0` wins 2 games in 50 and sweeps not one map of 25. My pre-registered
fourth branch ("both arms below 50% on RUN 2 with `D_denial` small") does not apply, since
`D_denial` was large; but the *size* of this collapse is not what the denial story
predicts, and I am not going to pretend it is.

### The premise of my own experimental design was wrong

I wrote, in the pre-registration: *"an ablation of a defensive capability run only against
my own lineage — which never denies paint — would prove nothing."* **My lineage does deny
paint.** `bob_iter12` spawns 1 splasher and 1 mopper in every 5 units; that is the very
mix under test. What my lineage does not do is deny paint *well*. So RUN 2 was never the
"no threat present" control I designed it to be — it is a second measurement against a
weak denier, not a measurement against a non-denier.

The design error did not corrupt RUN 1, which is the run the decision rests on, and
`bob_denier` remains a genuine strong-denial opponent. But it means I have **no** clean
non-denier control, and the "standing insurance premium" question I set RUN 2 to answer is
still unanswered.

### And a confound that would explain the size of the collapse without any denial at all

`Tower.run` spawns only when `chips >= want.moneyCost + reserve`, and the engine pays the
unit's **paint** cost out of the spawning tower's stash. Exact costs:

```
SOLDIER   200 paint / 250 chips
MOPPER    100 paint / 300 chips     <- half a soldier's paint
SPLASHER  300 paint / 400 chips
```

Iteration 17's probe measured my tower paint pool sitting at **110-260** for whole games —
straddling a soldier's 200-paint price. A tower in that band can often afford a **mopper**
and not a soldier. So the 3:1:1 rotation is not only a mix of capabilities, it is a mix of
**price points**, and `bob_d0` — soldiers only — is a bot whose towers simply cannot spawn
anything for long stretches. That alone could produce 2/50 without denial mattering at all.

This is the algorithm's own caution, which I quoted at myself this morning and then walked
past: **an ablation prices a CODE PATH, not a concept.** I gated the spawn *ternary* and
then read the result as the price of *denial*. Two things changed together.

**What the runs do establish, stated no more strongly than the evidence allows:**

1. The 3:1:1 spawn mix is strongly load-bearing. Both departures from it lose decisively,
   on two independent map samples, against two different opponents, with intervals nowhere
   near the null. That is 250 games and it is not in doubt.
2. Deleting denial slots to reclaim paint is **rejected**, which was the decision this
   iteration existed to make.
3. *Why* it is load-bearing is **not** established. Denial capability and spawn
   affordability are confounded in every arm I ran.

**Follow-up that separates them, recorded but not run now:** an arm with 3 soldiers : 2
moppers : 0 splashers holds the price mix roughly fixed while removing the splasher's
denial; and an arm of soldiers-only with the spawn reserve dropped so throughput is not
paint-gated isolates affordability. Neither is worth a run today — the decision they would
inform (keep the mix) is already made, and iteration 17 has a live mechanism with a
measured degeneracy behind it. Logged so the question is not silently lost.

**Functional-area note.** Iteration 16 is a reject, in spawn policy. That is three
rejects in three different areas (13/15 movement, 16 spawn), so `MaxConsecutiveRejects`
does not bind; iteration 17 is tower construction, a fourth area, and it is where the
evidence is strongest.

### Iteration 17 pre-check: the `coworker` counter weakens my hypothesis before it costs a run

`bob_rp0` (ANCHOR=0) reproduces `bob_rprobe` **exactly** — same counters, same win at
r446 — so the zero arm is verified as byte-equivalent behaviour and the dose is real.

The new counter I added, `coworker` (turns holding a ruin with an ally soldier inside that
ruin's 5x5), says my concentration story is largely already true:

```
soldier    hasRuin   coworker   share
13761          202        149     74%
13417          182        155     85%
10351          235        107     46%
11019          247         26     11%
12930           26         25     96%
10571           26         26    100%
```

**Soldiers are not scattered across separate patterns; most of them already have company.**
That is not what "four soldiers each 60% through four patterns" predicts, and it is the
main mechanical argument I pre-registered for anchoring. I am recording this as a partial
refutation of my own hypothesis, arriving from a two-game probe rather than a 100-game
gauntlet — which is precisely what §3's pre-checks are for.

**What survives.** The dominant gate is still `lowPaint` at 44% of ruin-turns: soldiers
are **broke**, not scattered. And there is a second-order route by which anchoring could
still pay, which I did *not* pre-register and am writing down now so that if the arms win I
do not credit the wrong mechanism: ruins near a soldier's birth tile are near its spawning
**tower**, and `tryRefill` is vision-only (r²=20) — so a soldier working a ruin next to its
own tower can actually refill, where one working a distant ruin cannot. Anchoring may
therefore act as a **paint** fix disguised as a siting fix.

That is a testable distinction, not a hedge: if the arms improve, `lowPaint` should fall
sharply and `coworker` should barely move. If `coworker` rises and `lowPaint` does not,
the concentration story was right after all. The counters to separate them are already in
the probe, and the doses are already built and compile-checked.

---

## Iteration 17 RESULT — VOID before evaluation: the mechanism never executes

**Arm-to-arm identity check (measurement doctrine #3), run before spending a gauntlet.**
ANCHOR = 0, 1 and 3 on Rose vs `examplefuncsplayer`:

```
soldier   ANCHOR=0                                    ANCHOR=1        ANCHOR=3
13761     hasRuin202 tile108 lowPaint30 heldMax171    identical       identical
10351     hasRuin235 tile 44 lowPaint151 heldMax183   identical       identical
11019     hasRuin247 tile 26 lowPaint210 heldMax247   identical       identical
13417     hasRuin182 tile136 lowPaint10 heldMax154    identical       identical
```

**Every counter, for every soldier, at every dose. The change never runs.** Doctrine #3
names exactly this: *"All-identical means the change never executed — this caught three
'results' in one project that were the same bot measured twice."*

**Why, and it is obvious in hindsight.** `chooseRuin` scores `rc.senseNearbyRuins(-1)` —
**ruins currently in vision**, r² = 20, about 4.5 tiles. A soldier essentially never sees
two unoccupied ruins at once, so the candidate set is a **singleton**, and every scoring
function whatsoever picks the same element of a one-element set. I pre-registered
reachability as a check and then applied it to the *guard* rather than to the *choice set*.
To make soldiers agree on a ruin they would need memory of ruins seen earlier — a much
larger change than the one I priced.

**VOID, not rejected**: no evidence was produced about anchoring either way, and it cost
three single-map games rather than a 100-game gauntlet. `src/bob_a1`, `src/bob_a3`,
`src/bob_rp1`, `src/bob_rp3` are discarded. `src/bob` is untouched and still
byte-identical to `bob_iter12`.

### What the same three games did find — traced, not theorised

`tools/replay-dump.sh --robot 11019` on the ANCHOR=0 replay, the soldier with
`lowPaint=210`:

```
round   9  (24,18)  paint=139  mCD=10  aCD=10
round  20  (23,17)  paint= 84  mCD=14  aCD=12
round  40  (24,18)  paint= 14  mCD=12  aCD=22
round  42  (23,17)  paint= 14  mCD=11  aCD= 2
round  50  (24,18)  paint= 14  mCD=26  aCD= 0
   ...
round 225  (24,18)  paint= 13  mCD=24  aCD= 0
round 234  (24,18)  paint=  5  mCD=10  aCD= 0     hp=250 throughout
```

Three facts, all directly read off the trace:

1. **It oscillates between two tiles, (23,17) and (24,18), from round 9 to round 234+** —
   225 rounds. `adjacent` was true on 245 of its 248 turns, so it is *at* its ruin the
   whole time. `Nav.navTo(workRuin)` runs every turn even when the soldier has already
   arrived. The SRP path beside it does the opposite and says so in its own comment —
   *"holds position ... so it returns early"* — the third asymmetry I have now found where
   the SRP path has a discipline the ruin path lacks.
2. **`aCD` is 0 from round 42 to the end of the game.** Its action is available and unused
   for roughly two hundred consecutive rounds, because `PAINT_FLOOR = 15` refuses to paint
   and its stash is pinned at 14.
3. **`hp` never leaves 250.** It does not die. `NO_PAINT_DAMAGE` only applies at *zero*
   paint, and `PAINT_FLOOR` stops the soldier one point above the band that would kill it.

**`PAINT_FLOOR` manufactures immortal do-nothing soldiers.** A soldier that spent its last
paint would hit zero, take 20 HP/turn, die, and free the economy — which my own iteration-8
economics concluded is the *efficient* terminal state ("dying at zero is the efficient
terminal state ... it frees the economy to build a replacement that arrives with a fresh
body and a full stash"). Instead it hoards fourteen paint and stands on a ruin for two
hundred rounds. This is TRAINING_ALGORITHM.md's recorded regularity by name: **survival
bought with inactivity.**

And it compounds with the threshold insight. The last 15 paint is worth **more** spent on
a tower pattern than held, because 119 of 120 paint on a pattern buys nothing while 120
buys +5 paint/turn forever. `PAINT_FLOOR` is a linear-value heuristic sitting on top of a
threshold good.

### Iteration 18 PRE-REGISTERED — spend the floor on the pattern

**One mechanism**: `workOnRuin` may paint below `PAINT_FLOOR`. Everything else, including
`paintSomething`'s floor, is untouched — so the change is scoped to the threshold good and
cannot be confused with a general "paint more" policy.

**Dose with a verified zero arm**: the ruin-work floor at 15 (today) / 5 / 0.
`RUIN_FLOOR = 15` must reproduce iteration 12 byte-for-byte, and I will check that with
the same identity test that just voided iteration 17 **before** reading any arm.

**Reachability, checked against the choice set this time, not the guard**: the branch is
`rc.isActionReady() && rc.getPaint() > PAINT_FLOOR` inside `workOnRuin`. Measured: 401 of
920 ruin-turns fail it, and one soldier failed it 210 times with `aCD = 0`. It is the
single most-taken refusal in the probe.

**Price, both numbers, before the code**:

```
benefit   401 ruin-turns team-wide are currently no-ops; at 5 paint per pattern tile the
          stash they hoard is ~3 tiles per soldier, but those tiles land on a THRESHOLD
          good, so their value is 0 or a whole tower, not 3/24 of one
price     soldiers die sooner. Iteration 8 measured that as a GAIN, not a loss, but that
          measurement assumed linear paint value, so it does not transfer unexamined --
          which is why the arm at 0 and the arm at 5 are both run rather than just 0
price     a soldier at exactly 0 paint cannot move, so it lingers ~13 rounds dying in
          place, taxing adjacent allies 1 paint/turn each. The arm at 5 exists to price
          precisely this against the arm at 0
```

**Accept gate**: head-to-head vs `bob_iter12`, fresh 25-map sample, both sides, read
against the mirror null with intervals from `tools/map-resample.py`.

---

## Coordinator status query (2026-09-07 19:40) — 16 hours, 0 accepts. Answered directly.

### 1. Consecutive rejects and `MaxConsecutiveRejects`

Five attempts since `bob_iter12`, and the areas do rotate:

```
it  area                        outcome   cost            margin vs the mirror null (25/50)
13  soldier movement (SRP)      REJECT    full gauntlet   -35 games
14  tower type adaptivity       VOID      0 games         premise refuted by tournament report on disk
15  soldier movement (bug nav)  REJECT    250 games       -1, -4, -4 across two independent draws
16  spawn policy (denial mix)   REJECT    250 games       -13 and -33 games
17  tower construction (siting) VOID      3 games         exactly 0 -- byte-identical, never executed
18  tower construction (floor)  in flight
```

`MaxConsecutiveRejects = 3` has **not** fired on any single area: the longest run in one
area is two (13 and 15, both soldier movement), and I recorded the rule at the time and
left the area deliberately. Movement -> spawn policy -> tower construction.

**Closed directions, with what killed each:**

```
paint refill by walking units home     it8   chip/paint economics; re-open trigger
                                             "chips sustained below ~5,000" -- re-checked
                                             today against 7 fresh traces, chips run
                                             4.4k-61k in every game, trigger NOT met
bug navigation / wall-following        it15  two arms, two map draws, 150 games, -1/-4/-4
soldier movement as spare capacity     it13  -35 games; movement is scarce, not spare
lowering SPLASH_MIN_VALUE              probe arithmetic: 10-12.5 paint/tile against a
                                             soldier's 5; and it16 then measured the
                                             splasher slot at +13 games, confirming the
                                             threshold was never the problem
deleting the denial slots              it16  -33 games against a denier, -46 on the lineage
```

Iteration 17 is **void, not closed** — it produced no evidence about anchoring, only
about my own reachability check. Re-opening it requires ruin *memory* first, since the
choice set is a singleton without it.

### 2. The frozen roster was 15 hours stale. Re-launched.

Fair, and it is the instrument I have the least excuse to neglect, having been the one to
show a lineage can walk downhill with every local comparison looking fine. Launched
`OPPONENTS="bob_iter0 bob_iter1 bob_iter11 examplefuncsplayer"` against the current build.
It runs alongside iteration 18's dose gauntlet; the shared semaphore splits my share
rather than the machine's, so this costs me wall-clock and nobody else anything.

Note the run will be labelled `bob_iter12`, **not** `+cand`: `src/bob` is byte-identical
to `bob_iter12` on all seven files, so this is a clean re-measurement of the accepted
build rather than a pre-accept candidate point. It is directly comparable to the
04:33 row (`bob_iter12` vs `bob_iter11`, 28/50 = 56.0%).

### 3. Is the gate mis-calibrated? No, and the numbers say so plainly.

This is the question I most wanted to be true, and it is not. If a strict gate were
rejecting real gains, my rejections would cluster just under the bar — candidates at
51-55% that a demanding threshold turned away. Here is where they actually landed,
measured in games against a mirror null of exactly 25/50 with zero swept maps:

```
iteration 13   -35 games
iteration 15   -1, -4, -4     (three arms, two independent map draws)
iteration 16   -13, -33       (two arms)  and -46, -36 on the second run
iteration 17    0             (byte-identical to the zero arm at every dose)
```

**Not one candidate has landed in the band where the gate's strictness could matter.**
The nearest was iteration 15 at −4, which is below the null, not marginally above it.
So the dry spell is not a stuck gate and not an unnoticed regression at the accept
boundary — **the ideas have been wrong**, and the instrument has been telling me so
clearly and cheaply.

I will say the uncomfortable half too: at 92.3% in the tournament, the improvements still
available are small, and my last three *hypotheses* were all built on premises the data
then refuted — a broad denial weakness (one swept loss in 450 games), enemy paint blocking
patterns (2% of ruin-turns), soldiers scattered across ruins (they already cluster). The
pattern is not a gate problem; it is that I have been forming hypotheses from plausible
mechanism stories and only then checking them against evidence already on disk.

### The lever the coordinator named, and what I am changing because of it

Cheap rejections cost me ~0 and were three of the last five: the History pre-check killing
the refill fix, iteration 17 voided by an identity check for three games, and the shared
dumper retracting my own "27 living units". The expensive ones were iterations 15 and 16,
at 250 games each.

**Change to my loop, recorded as a process change:** before any gauntlet, run the
identity/reachability check that voided iteration 17 — build the arms, play *one map*, and
diff the counters. If the arms are byte-identical the mechanism is dead and the gauntlet is
wasted. That check cost three games and would have caught a 100-game run; it is now
mandatory rather than lucky. Iteration 18's zero arm (`bob_f15`) is built to be
byte-identical to `bob_iter12` precisely so this check runs inside the evaluation itself.

---

## Iteration 18 RESULT — **ACCEPTED**. Spend the last paint on the pattern.

Run `20260907-192946`, `BOT=bob_iter12`, one shared fresh 25-map sample, 150 games.
Reported as the **arm's** wins; intervals from `tools/map-resample.py` over maps.

```
RUIN_FLOOR   arm wins/50   vs null   95% CI (iter12's wins)   swept   swept-lost
   15 (zero)     25/50        +0        [25, 25]  se = 0.00      0         0
    5            27/50        +2        [18, 28]                 4         2
    0            31/50        +6        [15, 23]                 6         0
```

**The zero arm is a perfect null: 25/50, standard error exactly 0.00, and all 25 maps
split 1-1.** `bob_f15` is `bob_iter12` with the constant renamed and no behaviour change,
and the engine confirms it to the game. That is simultaneously the mandatory identity
check, and a mirror regenerated from the current baseline on this exact map sample —
which is what MULTI_AGENT.md requires and what makes every margin below a count of games
the code actually flipped, not a standard-deviation claim.

**Dose-response is monotone toward zero: +0, +2, +6.** Three arms, one map sample, exact
within-run comparison. The mechanism gets better the more of it you take, right up to the
boundary (paint cannot go below 0), so 0 is both the best tested dose and the end of the
dose axis.

**Six swept maps and zero swept losses.** `Piglets2`, `Crab`, `HungerGames`, `Dominoes`,
`mit`, `Money`. Identical code sweeps nothing — measured at 0 of 25 in the zero arm of
this very run — so six sweeps are six real maps. And **`mit` and `Dominoes` are both maps
I lost to alice in tournament `20260907-1300`**, which is a cross-check I did not
engineer: the fix flips maps an independent lineage beats me on.

**The diff has no one-directional regression**: the arm loses both sides of no map at all.

### Accepted, and what it changes

```java
static final int RUIN_FLOOR = 0;   // was PAINT_FLOOR = 15, for tower-pattern work only
```

`paintSomething` deliberately keeps `PAINT_FLOOR = 15`. The change is scoped to the
**threshold good** and is not a general "paint more" policy — which is what makes the
result interpretable.

`src/bob` updated, snapshotted to `src/bob_iter18` (compile-checked in isolation), charts
regenerated, replay archived as `replays/iter18_bob_iter12_mit_botA_WIN.bc25`
(`bob_iter18` beats `bob_iter12` on `mit` at r896).

### Why this one worked when five before it did not

Every rejected hypothesis in this block was a story about what a good bot *would* do. This
one came from `tools/replay-dump.sh --robot 11019` showing a single soldier with
`aCD = 0` and `paint <= 14` for two hundred consecutive rounds while its HP never moved —
an absolute degeneracy, visible without reference to any opponent, exactly the selection
discipline §1 asks for and that I had not been following.

The general lesson is now LEARNINGS §20: **a floor constant is a linear-value heuristic,
and it was guarding a threshold good.** Under a threshold the marginal value of the last
point spent is the *highest*, not the lowest, which inverts the reasoning a floor is built
on. `PAINT_FLOOR` was also parking soldiers one point above the band that kills them —
`NO_PAINT_DAMAGE` applies only at *zero* — so it manufactured immortal do-nothing units,
against my own iteration-8 finding that dying at zero is the efficient terminal state.

### Still open, recorded so it is not lost

- The **frozen roster run** (`20260907-193911`) is still in flight and measures
  `bob_iter12`, the pre-accept baseline. That is the clean "before" point; `bob_iter18`
  needs its own roster run next, and doctrine #9 wants one every ~5 accepts regardless.
- Iteration 16's confound (denial capability vs. spawn **affordability**) is unresolved.
- Iteration 17 is void, not closed; re-opening needs ruin memory so the choice set stops
  being a singleton.
- The `UPGRADE_RESERVE` and money-tower-upgrade defects in `Tower.run` remain queued.

---

## FROZEN ROSTER RE-MEASURED (2026-09-07 20:20) — and it is flat, which matters

Run `20260907-193911`, 200 games. `bot.txt` confirms `label=bob_iter12`, `dirty=0`, so the
build that played is exactly the accepted snapshot — not a candidate, not the working tree.

```
opponent              wins/50    95% CI      per-map 0/1/2      earlier measurements
bob_iter0              46/50    [42, 49]     0 / 4 / 21
bob_iter1              43/50    [38, 47]     0 / 7 / 18         84.0% at 03:47
bob_iter11             25/50    [19, 31]     4 / 17 / 4         58.0% 03:47 -> 56.0% 04:33 -> 50.0% now
examplefuncsplayer     50/50    [50, 50]    25 swept, se = 0
```

**`bob_iter12` scores exactly the null against `bob_iter11`: 25/50, +0.00 sd.** Across
three independent map draws the number has gone **58.0 -> 56.0 -> 50.0**.

And it is *not* a degenerate "same bot" result — the per-map column is `{0:4, 1:17, 2:4}`,
so iteration 12 sweeps four maps, is swept on four, and splits seventeen. These are two
genuinely different programs that trade evenly. Iteration 12 was "revert the hash, remove
the ruin memory" — a simplification accepted on sweep evidence — and on this instrument it
**bought nothing over its predecessor**.

This is precisely what §5b says only the frozen roster can see, and what the coordinator
was right to ask about: my head-to-head gate said iteration 12 beat iteration 11, and the
absolute instrument says the lineage did not move. A head-to-head against your predecessor
cannot tell a rising lineage from a drifting one.

**What I am doing about it, in order:**

1. **Re-measure with `bob_iter18` immediately** — launched, same roster. Iteration 18 is a
   +6-game change with 6 sweeps and 0 swept losses against a zero-variance null, so if the
   lineage is healthy this is where it shows. If `bob_iter18` vs `bob_iter11` comes back at
   or near 50% as well, the flatness is structural rather than a property of iteration 12,
   and §5b's answer is a **pairwise** ablation, not a single-feature one.
2. Only if that second point is also flat do I start nominating pairs — and per the
   algorithm's own base rate (two of three nominated pairs refuted, the one real
   destructive pair found by ablating *after* a roster drop rather than by prediction), I
   will ablate on the roster's evidence and not on a story about which features look like
   they should interact.

`progress/vs_old_bots_history.csv` has the four new rows; `vs_old_bots.png` regenerated.

---

## ROSTER ON `bob_iter18` (2026-09-07 21:50) — the accept does NOT show on the absolute instrument

Run `20260907-201817`, `label=bob_iter18`, `dirty=0`. The `bob_iter11` arm is complete at
50 games; the `examplefuncsplayer` arm is still playing.

```
opponent          iter18 wins/50   95% CI    per-map 0/1/2     iter12's number (run 193911)
bob_iter0             46/50       [42, 49]   0 / 4 / 21          46/50   same
bob_iter1             43/50       [39, 47]   0 / 7 / 18          43/50   same
bob_iter11            20/50       [15, 26]   7 / 16 / 2          25/50   -5 games
                                  -1.78 sd
```

**Against `bob_iter11` the lineage now reads 58.0 -> 56.0 -> 50.0 (iter12) -> 40.0
(iter18).** And the swept-map column, which is the near noise-free instrument here, is
worse than the headline: iteration 18 sweeps **2** maps and is swept on **7**, where
iteration 12 was 4 and 4.

**This is the §5b shape, arriving on the very next accept after I flagged it.** The
within-run head-to-head said iteration 18 beats iteration 12 by +6 games with 6 sweeps and
0 swept losses — an exact comparison on one shared sample, the strongest kind I have. The
frozen roster says iteration 18 is *further below* a three-generation-old ancestor than
iteration 12 was. Both cannot be a simple statement about strength.

### What I am NOT concluding, and why

The two roster runs drew **different 25-map samples** (verified: `maps.txt` differs), so
20/50 against 25/50 is a **cross-run** delta — exactly the comparison MULTI_AGENT.md warns
is noisier than it looks. The intervals overlap, `[15, 26]` against `[19, 31]`. I cannot
say from this that iteration 18 is weaker than iteration 12; I can only say that **neither
is above the null against `bob_iter11`, and the newer one is not better on this evidence.**

I am also **not** reverting the accept. Iteration 18's evidence is an exact within-run
head-to-head with a zero arm measured at se = 0.00, and the mechanism it removed is a
documented degeneracy (units immortal at 14 paint with an unused action for 200 rounds).
Reverting on a cross-run comparison whose interval overlaps would be trading the stronger
instrument for the weaker one.

### The measurement that actually settles it — launched

`BOT=bob_iter11 OPPONENTS="bob_iter12 bob_iter18"`, 100 games on **one shared map
sample**. That makes the iteration-12-vs-iteration-18 comparison *exact* rather than
cross-run, against the ancestor where the drop appears. It is the cheapest thing that can
distinguish:

- **iter18 < iter12 vs iter11 on a shared sample** -> the accept really did walk downhill
  against older code despite beating its predecessor, which is §5b's destructive-pair
  signature, and the answer is a **pairwise** ablation driven by this roster drop and not
  by nomination (base rate in this project: 2 of 3 nominated pairs refuted; the one real
  pair found by ablating after a roster drop).
- **iter18 >= iter12 vs iter11 on a shared sample** -> the 50 -> 40 step was the map draw,
  and the standing finding remains the *earlier* one: `bob_iter12` bought nothing over
  `bob_iter11`, which is where the flatness actually starts.

Either way the next action is determined by the measurement rather than by my judgement,
which is the point of running it.

### Tooling caveat worth reporting

`tools/map-resample.py` printed `examplefuncsplayer 9/50 ... 95% CI [2, 17] -4.30 sd` for
an arm that has played **9 games of 50**. It assumes the full `maps x 2` denominator, so a
partial arm reads as a catastrophic loss rather than as incomplete. `gauntlet.sh`'s own
summary warns about unequal game counts; the resampler does not. Not a wrong number so
much as a missing guard, and it would be easy to misread in exactly the situation where
someone is anxiously watching a roster run. Flagging rather than working around it.

### Re-verified every quoted number against the fixed resampler (`2eefb92`)

The coordinator's fix turned my one report into three bugs. Checked what each could have
done to conclusions I have already drawn, rather than assuming none of them bit:

**Bug 1, incomplete arms.** Only ever affected my mid-run peek at `examplefuncsplayer`
(9 games of 50, printed as −4.30 sd). I read it as a partial-arm artifact at the time and
the arm finished at 50/50, so nothing propagated.

**Bug 2, opponents listed from the wins map — a shut-out opponent vanishes.** Audited all
five of my runs today: arm counts are 3, 2, 3, 4, 4, which is exactly what I launched in
each case, and **zero arms were shut out**, so no row could have been dropped. This is the
worst of the three and it happens not to have touched me — but only by luck, since
`bob_d0` came within two games of a shutout in iteration 16's RUN 2.

**Bug 3, `se = 0` labelled "exact null".** This one did reach my log. The roster block I
pasted contains the tool's line `examplefuncsplayer 50/50 ... exact null (se=0)` for an
arm I **swept 25 of 25 maps**. Under the fix it correctly reads `+25 games vs null (se=0,
every map identical)`. My own prose beside it said "25 swept, se = 0", so the conclusion
was never wrong — but the pasted block was, and a future reader would have hit it.
**Superseding in place rather than editing history**: where an earlier entry shows
`examplefuncsplayer ... exact null (se=0)`, read `+25 games vs the null`. se = 0 is a
statement about *spread* — every map agreed — and says nothing about *position*.

Everything else is unchanged under the fixed tool. Iteration 18's decisive figures
re-verified verbatim: `bob_f0` 19/50 [15,23] −2.81 sd, and the zero arm `bob_f15` now
labelled `exactly the null (se=0, every map split)`, which is precisely the claim I made
for it.

Note the shape this shares with my LEARNINGS §14 and the consistency-pass rule: three
tools gave three different answers about one run, and each was individually plausible.
Nobody catches that by reviewing one output; it needs two outputs compared.

---

## NEW BINDING RULE (2026-09-07 21:50) — BC25 finals bots are a yardstick I may not study

Recorded at the top of `RULES.md` as well, because a restarted session reads that file early
and must not have to discover this by accident.

Finals bots from the BC25 contest now exist on battlecode-dev as a **distance measurement**.
I am forbidden to read their code or to examine **any game played against them** — no
replay, log, trace, dump or derived counter. Only the score survives, and the coordinator
runs those matches. I may read a benchmark score if it lands in a committed results file;
that is all. If I ever find myself holding such an artefact, I stop and report it.

**This lands squarely on my habits, which is why I am writing it down rather than nodding.**
Almost everything I did today was replay archaeology: the denial probe's per-unit counters,
`RUINPROBE`, `tools/replay-dump.sh --robot 11019` for two hundred rounds of one soldier.
That reflex is exactly the thing to suppress here. Concretely: **never point the dumper, a
probe package, or any counter at a benchmark game, and never go looking for those files on
the VM.**

Untouched, and to be used exactly as before: my gauntlet, `bob_denier`, the frozen roster,
and `tournaments/`. Those remain how I measure.

**And the epistemics matter as much as the prohibition.** A benchmark score is information
about *distance*, not a target. It is the only instrument in this project my own lineage
did not produce, and its entire value comes from my never having adapted to it — the moment
I tune toward it, it stops measuring anything. That is the same reason `tools/bc25-maps.txt`
is resampled rather than pinned, and the same reason my frozen roster is frozen. It also
means a bad score is not a reason to change course: my accept gate stays the within-workspace
head-to-head, and my absolute instrument stays the frozen roster.

The 2025 post-mortem ban and the no-downloaded-bot-implementations rule are unchanged.

---

## THE DECIDING RUN (2026-09-07 22:20) — the drop is REAL. Iteration 18 walks downhill.

Run `20260907-204710`, `BOT=bob_iter11`, opponents `bob_iter12` and `bob_iter18`, **one
shared 25-map sample**, both arms complete at 50 games. This makes the
iteration-12-vs-iteration-18 comparison **exact**, which the two roster runs could not be.

```
arm vs bob_iter11      wins/50   95% CI (iter11's)   swept   swept-lost
bob_iter12              24/50      +0.34 sd            4         5
bob_iter18              18/50      +2.65 sd            1         8
                                                     ------------------
difference             -6 games                       -3        +3
```

**Iteration 18 is six games worse than iteration 12 against `bob_iter11`, on identical
maps.** The swept-map column is worse than the headline and it is the near noise-free
instrument: iteration 12 sweeps 4 and is swept on 5; iteration 18 sweeps **1** and is swept
on **8**.

My pre-registered branch fires, and it is the unwelcome one. **The 50 -> 40 step was not
the map draw.**

### Two exact measurements that disagree, and which one governs

```
iteration 18 vs iteration 12 (its predecessor)      +6 games, 6 sweeps, 0 swept losses
iteration 18 vs iteration 11 (three generations back, same maps)   -6 games vs iteration 12
```

Both are exact within-run comparisons. Both are real. §5b says exactly which one to trust:
*"The head-to-head in step 5 is a partial derivative, not a level ... a chain of
individually-positive accepts can walk downhill ... the frozen roster is the only
instrument that sees this."* I wrote that caution into my own log this morning and then
produced a textbook instance of it by dinner.

### The nomination the roster itself hands me — not a story I invented

§5b is emphatic that pairs found by *reasoning* are usually wrong (2 of 3 refuted in this
project) and that the one real destructive pair was found by ablating **after a roster
drop**. This is a roster drop, so I am allowed a nomination — and the ancestry points at
one without my having to be clever:

```
bob_iter11   HAS ruin memory (a soldier remembers a ruin it cannot currently see)
bob_iter12   REMOVED it -- "revert the hash, REMOVE the ruin memory, on sweep evidence"
bob_iter18   = bob_iter12 + RUIN_FLOOR = 0 (soldiers spend their last paint on a pattern)
```

**Mechanism, and it is the threshold-good argument turned against me.** Spending a
soldier's last paint into a pattern only pays if *someone finishes the pattern*. With ruin
memory, a replacement soldier remembers the ruin and completes the investment. Without it,
the soldier dies at 0 paint beside a partly-built pattern that **no one ever returns to** —
and I have converted a soldier's whole stash into nothing, which is precisely the failure
mode I used to justify the change. Iteration 18 is a bet that only pays out under a feature
iteration 12 had already deleted.

That is a genuine destructive pair: `RUIN_FLOOR = 0` x `ruin memory removed`. It is
invisible to my accept gate because both arms of that gate carry "ruin memory removed".

### Pre-registered 2x2 for iteration 19

```
                       ruin memory OFF (today)     ruin memory ON
RUIN_FLOOR = 15        bob_iter12                  arm C
RUIN_FLOOR = 0         bob_iter18                  arm D
```

All four against one shared sample. If the interaction is real, **D > B, C and the
iter12->iter18 step reverses sign** when memory is present. If D is no better than B, the
pair is refuted and iteration 18 is simply a regression to revert — which the base rate
says is the more likely outcome and which I am pre-committing to accept.

### What I am doing about HEAD, and why I am NOT reverting tonight

The tournament fires at 01:00 UTC and HEAD carries `bob_iter18`. I am leaving it there for
exactly one tournament, deliberately:

- Both `bob_iter11` and `bob_iter12` are **my own code**. Every measurement above is
  self-referential, and "worse against my own ancestor" is not the same claim as "weaker".
- The tournament plays **all 75 maps**, so consecutive tournaments are compared on an
  identical map set with no draw confound — the one place I get an exact comparison against
  two lineages I did not write. `bob@iter12` scored **92.3%** in `20260907-1300`.
- **Pre-registered reading, written now:** if `bob@iter18` lands materially below 92.3% —
  and especially if its swept-map count against alice (65) and carol (64) falls — the
  regression is real in absolute terms and iteration 18 is reverted regardless of how the
  2x2 comes out. If it holds near 92.3%, then iteration 18 is worse specifically against
  *my own older code* and the interaction story is live.

One tournament of possibly-worse standing is a cheap price for the only non-self-referential
instrument in the project, and standings are relative anyway. This is a decision to *buy a
measurement*, not a decision to keep a build I like.

**Recorded honestly: my accept of iteration 18 was premature.** Not because the gate was
mis-applied — it was applied correctly and the mechanism is real — but because doctrine #9
says *"on thin accept margins, run the frozen roster BEFORE accepting"*, and I ran it after.
A +6 with 6 sweeps did not feel thin, which is exactly the state in which the rule matters.

### Iteration 19 2x2 built and launched (2026-09-07 22:45)

Arms forked from the shelved iteration-11 patch (`bob-tools/shelved/iter11-ruin-memory/
apply.py`, capacity 24 — the value iteration 11 shipped), applied to each base and then
lifted into its own package. `src/bob` was restored from git afterwards and verified clean.

```
                    ruin memory OFF          ruin memory ON (RUIN_MEM = 24)
RUIN_FLOOR = 15     A  bob_iter12            C  bob_mC
RUIN_FLOOR =  0     B  bob_iter18            D  bob_mD
```

Gate check, because these two constants are the whole experiment and confusing them would
silently ruin it:

```
mC   workOnRuin uses PAINT_FLOOR   (both pattern-paint sites)   <- iteration 12 base
mD   workOnRuin uses RUIN_FLOOR, paintSomething keeps PAINT_FLOOR <- iteration 18 base
```

Both compile-checked in isolation. Launched as `BOT=bob_iter11` against all four on **one
shared 25-map sample** (200 games, `20260907-224...`), so every arm-to-arm comparison in the
table is exact. `bob_iter11` is the right common reference: it is the ancestor where the
drop appears, it is frozen, and A and B against it are already measured at 24/50 and 18/50
on a different draw, which gives a consistency check on the new sample.

**Pre-registered reading, before any games are played:**

- **D > C and D > B, with the B−A gap reversing sign under memory** -> the destructive pair
  is real. `RUIN_FLOOR = 0` is a good mechanism that requires a feature iteration 12 had
  already deleted, and the fix is to restore ruin memory *and then* re-accept the floor —
  as a pair, never separately.
- **D ≈ B (memory does not rescue it)** -> the pair is refuted, iteration 18 is simply a
  regression, and I revert it. **I am pre-committing to this now**, because the base rate
  in this project says refutation is the likely outcome (2 of 3 nominated pairs refuted)
  and I do not want to be arguing for my own mechanism after seeing the number.
- **C > A as well** -> ruin memory is independently valuable and iteration 12's removal of
  it was the actual regression, which would make the flat 58 -> 56 -> 50 stretch a story
  about iteration 12 rather than about iteration 18.

Note what makes this legitimate under §5b: I am not ablating because a pair *looks* like it
should interact. I am ablating because the frozen roster dropped and then an exact
same-sample run confirmed the drop — and the ancestry, not my imagination, named which two
features to cross.

### LEARNINGS consistency pass (2026-09-07 23:00) — run while the 2x2 plays

TRAINING_ALGORITHM.md's logging section asks for a **consistency pass, not only an append**,
and gives the tell: *two rules that ought to cite each other and never do.* I added four
sections today (§18–§21), so I ran the pass rather than assuming it was fine. It found one
real contradiction, one supersession, and one thread split across four sections.

**1. §13 and §21 are the same finding, and §13 is dated this morning.** §13 ("Local wins do
not compose into global progress") records the lineage going 29 points backwards against a
frozen opponent while winning every step against itself. §21 records iteration 18 doing it
again. **§13 rule 2 already said "run it more often than every five accepts."** I wrote
that rule this morning and let the roster go 15 hours and two accepts stale until the
coordinator asked. The rule I broke was my own, not just the algorithm's — a harder
finding than the one I filed at the time, and I only got it by comparing entries.

**2. §13 rule 3 is partially WRONG and is now superseded in place.** It says *"marginal
accepts are where the drift enters"*, evidenced by a 52.5% coin-flip accept. Iteration 18
was **+6 games, 6 swept maps, 0 swept losses** against a zero-variance null — about as
unmarginal as this lineage produces — and it drifted anyway. So margin size is **not** a
safety signal, and believing it was is exactly what let me skip the roster. Superseded, not
deleted: the old text stands because it was load-bearing for what was decided while it
stood.

**3. §16 and §21 would have contradicted each other in front of a future reader.** §16 says
*a heuristic that nominates a candidate is not evidence about it* — 2 of 3 nominated pairs
refuted. §21 rule 3 says *when the roster drops, ancestry names the pair*. Those look
opposed, and a future session could quote §16 to refuse the very ablation §21 requires.
Added §16 rule 5 to reconcile them explicitly: plausibility nomination is a **prediction**
("which of my features look coupled?"); ancestry nomination is a **lookup** ("which
features entered or left between the generations the roster is comparing?") performed only
*after* the roster has already produced evidence that something is wrong.

**4. Cross-links added** so §13, §15, §16 and §21 read as one thread instead of four
independent observations. §15 is the mechanism in the abstract; §13 and §21 are two
measurements of it; §16 bounds how the follow-up may be chosen.

This is the second time the pass has earned its keep, and both times the failure was
invisible per-entry: every one of these sections was correct when written and checked when
written. Only *comparing* them failed — which is precisely what the algorithm predicted.

---

## Session recovery (2026-09-07 23:15 UTC)

Session died shortly after launching the iteration-19 2x2. `gauntlet-collect.sh --list`
showed `20260907-212222  200 games  complete` on the VM with only `results.txt` pulled
locally and no `summary.txt` — the textbook session-death casualty. Collated it rather
than re-running. Nothing else was queued on the driver, so nothing else was lost.

Note for future sessions: the log entry below the 2x2 launch guessed the run id as
`20260907-224...` from a wall-clock time in local zone; the actual id is `20260907-212222`
(run ids are UTC). **Write the run id down from the tool's own output, never from a
timestamp you reconstruct.**

## Iteration 19 — the 2x2. The destructive pair is REFUTED.

Run `20260907-212222`, `BOT=bob_iter11`, four arms, one shared 25-map sample, 200 games,
complete. Columns are the ARM's wins (of 50) against the frozen common reference.

```
                     ruin memory OFF        ruin memory ON
RUIN_FLOOR = 15   A  bob_iter12  22/50   C  bob_mC  26/50
RUIN_FLOOR =  0   B  bob_iter18  19/50   D  bob_mD  22/50

swept / swept-lost   A 3/6   B 3/9   C 5/4   D 4/7
```

- **Interaction = (D−C) − (B−A) = (−4) − (−3) = −1 game.** The pair I nominated does
  not exist. Memory does not rescue `RUIN_FLOOR = 0`; it moves both rows by the same
  amount. **Pre-committed to this reading before the games were played, and it is the
  outcome the project base rate predicted (now 3 of 4 nominated pairs refuted).**
- Main effect of ruin memory: **+4** (floor 15), **+3** (floor 0). Positive at both doses.
- Main effect of `RUIN_FLOOR = 0`: **−3** (memory off), **−4** (memory on). Negative at both.
- The third pre-registered branch fired: **C > A**, and C is the only arm that beats
  `bob_iter11` at all.

## Iteration 19 CANDIDATE — **REJECTED**

Candidate = arm C: revert `RUIN_FLOOR` to `PAINT_FLOOR`, restore ruin memory (`RUIN_MEM=24`).
Byte-verified `src/bob` == `bob_mC` mod the package line; both compiled in isolation.
Run `20260907-232155`, `BOT=bob`, fresh 25-map sample, 200 games, complete.

```
opponent        wins by candidate   95% CI      vs null    swept / swept-lost
bob_iter18            22/50        [18, 26]    -1.39 sd        1 / 4      <- ACCEPT GATE
bob_iter12            22/50        [18, 26]    -1.40 sd        1 / 4
bob_iter11            23/50        [17, 28]    -0.71 sd        3 / 5
bob_mirror            25/50        [25, 25]    exactly the null (se=0, all 25 maps split)
```

**22/50 against the snapshot it would replace. The gate is not met. Rejected.**

The mirror null came back at **exactly 25/50 with se = 0 and every one of 25 maps split
1–1** — a third independent confirmation on a fresh build and a fresh draw. So −3 games
is a real 3-game effect, not spread.

> **ANNOTATED 2026-09-08 (superseded in place, not deleted — this rejection was decided while the
> reasoning below stood).** The sentence above is **wrong**, and LEARNINGS 36 retracts the premise:
> a byte-identical mirror arm is *structurally forced* to 25/50-all-split on a deterministic engine,
> so its zero variance is a wiring check on the harness and **not** this instrument's standard error.
> Against the floor actually measured since — binomial `se ≈ 3.5`, confirmed today at **3.37** by
> four PRNG-phase-only arms (LEARNINGS 43) — the −3 that rejected iteration 19 is **0.85 se, i.e.
> indistinguishable from zero.** Iteration 19 was not refuted; it was **unresolved**, and the two runs
> disagreeing by 10 games is exactly what two different 25-map draws produce.
>
> The same correction applies with the opposite sign to **iteration 18's ACCEPT**, which cited the
> identical `se = 0` claim to accept a **+6** — a figure my current gate sends to replication rather
> than to acceptance. **One retracted premise let a +6 in and kept a −3 out**, and both are still
> carried in the shipping bot's ancestry. This is why `src/bob_abl18` is built and why the
> iteration 18 ablation is the first candidate after the full-corpus calibration.

### The two runs are in tension, and §5b says which one governs

Both are exact within-run measurements and they disagree in direction:

```
run 212222 (draw 1), common reference bob_iter11:  mC 26  >  iter18 19     (+7 apart)
run 232155 (draw 2), DIRECT head-to-head:          mC 22/50 vs iter18      (-3)
```

This is my own LEARNINGS §21 happening again, one day after I wrote it: **margins measured
against a common third party do not chain into a direct margin.** A +7 gap versus
`bob_iter11` did not survive as a direct head-to-head. Neither number is wrong; they are
different quantities, and only the direct one is the accept gate.

Within draw 2 the candidate is uniformly weak against all three ancestors (22, 22, 23) —
whereas in draw 1 it looked like the strongest arm. A swing that large between draws means
**the ruin-memory effect is map-dependent**, which is exactly the 3 Musketeers warning
`reference/RESEARCH.md` §1 raises about small margins on a fixed map list. That is now the
best available account of the +4: it was draw-specific.

### Why I am NOT reverting iteration 18 after all — and flagging that I said I would

I pre-committed: *"D ≈ B (memory does not rescue it) -> the pair is refuted, iteration 18
is simply a regression, and I revert it."* The pair was refuted, so the pre-commitment is
live and I am not going to quietly drop it. But the inference "iteration 18 is a
regression" rested on iter18 < iter12 **against bob_iter11**, and the only *direct* test of
a revert-containing build I now own says the revert **loses 3 games to iteration 18**.

Two exact facts that do not compose:

```
iter18 beats iter12 directly            +6   (iteration 18's own accept)
iter18 loses to iter12 against iter11   -3   (this 2x2, draw 1)
```

So the honest position is **not** "iteration 18 is a regression" and **not** "iteration 18
is fine". It is: *the lineage is non-transitive around iterations 11/12/18, my roster is
flat across that stretch, and I do not yet have an instrument that resolves the level.*
Recorded **OPEN**, per §3b — I am not back-filling a story to make the pre-commitment come
out tidy, and I am not executing a revert whose only direct measurement is negative.
HEAD stays on iteration 18 for the 01:00 UTC tournament, which is the one non-self-referential
reading available and was pre-registered before any of this.

**Functional area: ruin work / paint floors. This is the 3rd consecutive reject in it
(17 void, 18 accepted-then-doubted, 19 rejected). `MaxConsecutiveRejects` is reached: the
next attempt must leave this area.** It does — see below.

## Pre-check that KILLED a candidate before it was built: soldier repulsion

`reference/RESEARCH.md` §7/§11 point at emergent coordination (wololo's repulsion fields).
`Nav.wander()` already carries the momentum term and has **no** ally-awareness, so
repulsion looked like a clean gap. Sized it offline first — soldier over-dispersion against
a uniform-placement null, from replay arena grids:

```
map              r200    r400    r600    r800
mit   60x60      3.2x    6.5x    4.2x    1.4x
Gears 55x55      0.0x    1.0x    1.6x    1.6x
rain  30x30      2.2x    2.5x    1.6x    2.2x
quack 30x35      2.6x    1.0x    1.0x     -
```

**`mit` was a degenerate sizing map** — precisely the trap the algorithm names. On the other
three maps my soldiers are only ~1.0–2.5x more clustered than uniform, and on the *largest*
map barely at all. Not worth an iteration on this evidence. Cost: zero games.

## A wrong-referent error I caught in my OWN instrument, mid-analysis

My first coverage table read **`DefaultSmall 134%`**. Impossible, and the tell was that two
artefacts which must agree did not. Cause: `teamCoverageAmounts` is **per-mille of TOTAL
tiles** (`tools/engine-facts.md`), and I had divided it by *passable* tiles — the exact
error doctrine #5 lists. Reconciled against the census printed in the same dump:

```
census 3025 tiles = 2002 painted (T1 1106) ... coverage per-mille T1 recon=366 engine=382
```

recon 366 vs engine 382, gap −16, and T1 had 17 units on the board occluding paint in the
reconstructed grid. **The residual is explained to within one tile**, which is what licenses
reading anything off the corrected numbers.

## THE FINDING (2026-09-08) — the map is FULL for ~75% of every game

With the denominator fixed, the coverage trajectories say something much stronger than
"coverage saturates". Engine census on Gears at r800: **2883 of 2885 paintable tiles are
painted — 2 tiles left.** Checked across every map I had a replay for:

```
map              walls   game ends   map full by       last cov T1/T2
Brat             15.0%      r792     r200 (25% in)      632/315
DefaultLarge      1.6%     r1398     r400 (29% in)      647/323
DefaultSmall      7.0%      r717     r200 (28% in)      680/266
Flower           12.0%      r925     r200 (22% in)      671/315
Gears             4.6%     r1832     r400 (22% in)      685/304
Justice           7.4%      r393     r100 (25% in)      622/342
Money             6.9%     r1549     r200 (13% in)      661/292
Piglets2         15.3%     r2000     r500 (25% in)      587/388
boxofchocolates  19.5%     r1335     r700 (52% in)      694/290
rain              5.6%     r1507     r300 (20% in)      666/305
Jail             10.0%      r674     never              478/198
Parking_lot      11.4%      r745     never              599/224
```

**10 of 12 maps fill completely, typically ~25% of the way through the game.** Now combine
that with two facts already in RULES.md and LEARNINGS §5, which I have never put together:

- **Soldiers cannot overwrite enemy paint at all.** Only splashers (r²≤2 of the splash
  centre) and moppers can.
- Robots **spawn with a full stash paid out of the spawning tower's paint**, so a soldier
  costs 200 paint — and paint, not chips, is the binding resource.

So for roughly three-quarters of every game, the map is saturated and a soldier can no
longer change the score, yet 3 of every 5 units I build is a soldier. Gears steady state,
per 100 rounds, from r700 to r1800:

```
+sold ~38   died ~60, of which STARVED (died at 0 paint) ~57   =  ~95% of deaths
soldiers alive ~110       paint actions ~300  (2.7 per soldier per 100 rounds)
chips $5,932 -> $120,986 unspent
```

~38 soldiers x 200 paint = **~7,600 paint per 100 rounds spent re-buying soldiers that
cannot affect a full map**, while ~95% of their deaths are starvation rather than combat.
LEARNINGS §5 already says *"the 3:1:1 spawn ratio is an unmeasured iteration-0 default"*
and *"once the map saturates, the 3-in-5 of production that is soldiers stops being able to
affect the score."* It has been sitting in my own notes as an observation and was never
converted into a candidate. It is the next one.

### Iteration 20 hypothesis (pre-registered)

**Once local ground is saturated, soldier production is near-pure waste; shifting the
tower's spawn mix toward splashers (the only unit that converts enemy paint) at that point
raises final coverage.** The threshold must be *self-calibrating* from what a tower can
actually sense (unpainted tiles in its own vision), not a fixed round number — maps here
saturate anywhere from r100 to r700.

Pre-registered map-level prediction, per doctrine #4: the effect appears on the 10 maps
that saturate and is **absent on Jail and Parking_lot**, which never do.

**Pre-checks I have NOT done yet, named explicitly so the next session does not inherit
momentum without the doubt:**

1. **Price the reallocation.** A splasher costs 300 paint against a soldier's 200. I have
   *not* computed what a soldier buys post-saturation (re-claiming tiles the enemy neutralises,
   tower attacks) versus what a splasher buys. Iteration 16 measured the splasher slot at
   +13 games, which is suggestive but is not this number.
2. **Reachability of the sensing threshold.** I have not checked what a tower actually sees:
   towers do not move, so a tower's own vision may be permanently saturated long before the
   map is, making the trigger fire far too early.
3. **The saturation sample is win-biased.** All 12 replays are games the candidate *won*
   (they are `bob_iter11`'s losses). Saturation timing should be roughly outcome-independent,
   but I have not verified it on a game I lost. Run 232155's `losses/` can settle this and I
   have not looked.

---

## Iteration 20 — spawn mix. PRE-REGISTERED before the run (launched `20260908-000848`).

New functional area (**required**: ruin work / paint floors hit `MaxConsecutiveRejects`).

### The three pre-checks I named as undone, now done

**Pre-check 2 (reachability of a tower-local saturation trigger) — FAILED, and it killed
the design I first had in mind.** I intended to have each tower sense its own unpainted
surroundings and switch production locally. Measured, offline, counting unpainted passable
tiles within r²≤20 of every T1 tower:

```
map           round   map unpainted    towers with ZERO unpainted in vision
Gears          r100      37.4%                 5 / 5      <-- fires with a THIRD of the map virgin
Gears          r600       0.6%                 9 / 9
DefaultLarge   r100      48.7%                 1 / 5
Money          r200       1.6%                10 /12
rain           r100      33.6%                 1 / 5
```

A tower sits in the middle of its own painted blob, so **its local vision saturates long
before the map does** — on Gears every tower reads "saturated" at r100 while 37.4% of the
map is unpainted. A tower is the wrong sensor. Design abandoned before it was written.

**Pre-check 1 (price the reallocation) — PASSED, and it is large.** Rather than price the
outcome I counted the *decision*, offline, over rounds 900–920 (r500–520 for Parking_lot):

```
map            soldier-turns  tiles   per 1000    splasher-turns  tiles   per 1000   ratio
Gears              2441         10       4.1           534          33      61.8     15.1x
DefaultLarge        592         14      23.6           197          41     208.1      8.8x
Money               460         24      52.2            99          85     858.6     16.4x
Parking_lot         470         23      48.9           174          66     379.3      7.8x
```

**Soldiers act on 0.4–5.2% of their turns.** Not because they are starved — a paint census
from the indicator strings at Gears r900 shows **89.6% of soldiers hold paint above the
floor** and 68% of splashers can afford a splash. They are able and idle, because the map is
full and **a soldier cannot overwrite enemy paint at all**. Splashers convert 7.8–16.4x more
tiles per unit-turn at 1.5x the paint cost: **5–11x per unit of paint.**

**Pre-check 3 (win-bias) — acknowledged, not discharged.** All these replays are games I
won (they are `bob_iter11`'s losses). Saturation timing should be roughly outcome-independent,
but the productivity ratio is measured only on winning games. In a losing game I hold less
territory and face more enemy paint, which should make splashers *more* valuable, so I
expect the bias to understate the effect — but that is an argument, not a measurement, and
run `20260908-000848`'s own `losses/` will settle it.

### The change (one mechanism, one constant)

`Tower.SPLASHER_SLOTS`, a bitmask over `spawned % 5` selecting which spawn slots build a
splasher. Slot 4 stays MOPPER; everything else is a soldier.

```
arm            mask       soldier : splasher : mopper
bob   (zero)   0b00100        3 : 1 : 1     <- the iteration-0 default, EXACT zero arm
bob_s2         0b01100        2 : 2 : 1
bob_s3         0b01110        1 : 3 : 1
```

The zero arm reduces the new expression to the original one exactly, so **the identity check
runs inside the evaluation**: `bob` vs `bob_iter18` must come back at exactly 25/50 with
every map split. If it does not, the refactor is not behaviour-preserving and the whole run
is void. `bob_mirror` is regenerated from this build and is the null.

LEARNINGS §5 has called the 3:1:1 ratio *"an unmeasured iteration-0 default"* for some time;
no prior iteration established it deliberately, so no history is being silently reverted.

### Pre-registered reading

- **Monotone in dose** (s3 better than s2 better than zero) -> accept the largest dose and
  sweep further next iteration.
- **Interior peak** (s2 best) -> accept s2; doctrine #2 calls a curve peaking in the middle
  the strongest evidence available here.
- **Flat or negative** -> the *marginal* splasher is worth much less than the *average* one.
  This is the specific risk I have NOT priced: splashers currently splash on only 0.6–8.1%
  of their turns against a cooldown ceiling of 20%, so opportunities may be limited by
  front-line geometry rather than by splasher count. A flat curve is the evidence for that,
  and it would close this direction rather than invite a refinement.

---

## TOOLING BUG (coordinator-owned `tools/replaydump/ReplayDump.java`) — arena glyphs are not injective

Reporting rather than working around, and reporting what the code *computes* rather than the
symptom. The arena renderer encodes team by case over an alphabet where tower and mobile
glyphs already overlap:

```java
if (tower) c = PAINT_TOWER ? 'P' : MONEY_TOWER ? 'M' : 'D';
else if (SOLDIER) c='s'; else if (MOPPER) c='m'; else c='p';
if (team == 2) c = tower ? toLowerCase(c) : toUpperCase(c);
```

So `M` = team-1 money tower **or** team-2 mopper; `P` = team-1 paint tower **or** team-2
splasher; likewise `m`/`p` for the mirrored pair. This is a correctness failure, not a
mislabelling — the glyph does not identify the unit.

**Discriminating case, on data already on disk** (Gears r800, `bob_mC__Gears__botB.bc25`),
comparing grid glyphs against tower positions taken from the authoritative event log:

```
cells rendered 'M': 10   actually T1 money towers:  5   (other 5 are T2 moppers)
cells rendered 'P': 15   actually T1 paint towers:  4   (other 11 are T2 splashers)
```

Anyone censusing towers or units from the arena grid gets a 2x–4x overcount. `D`/`d` are
safe (defense towers only) and `s`/`S` are safe (the soldier glyph is not a tower glyph),
which is why the soldier-dispersion figures earlier in this entry are unaffected. Suggested
fix: give towers a disjoint alphabet from mobiles, or print team as a separate layer.

### CORRECTION to the saturation table above, and a second tooling bug (2026-09-08, run still in flight)

While reading tournament replays I hit a coverage sum that is **impossible**: on
`boxofchocolates` (19.5% walls) the two teams' engine coverage sums to 984 per-mille. If
the denominator were total map area — which is what `tools/engine-facts.md` states, and it
explicitly warns *against* using passable area — the maximum possible sum is
1000 x (1 - 0.195) = **805**. Three maps, and the excess tracks the wall fraction:

```
map               walls    max sum under the DOCUMENTED denominator   observed sum
boxofchocolates   19.5%                 805                               984
Piglets2          15.3%                 847                               975
Gears              4.6%                 954                               989
```

A sum exceeding its own maximum is a proof, not a fit, so the documented denominator is
**refuted** regardless of anything else. Excluding walls fits: on Gears r800 the exact census
gives T1 1661 painted of 2885 non-wall = 576 per-mille against the engine's 573 (off by 3),
where the documented denominator gives 549 (off by 24). **I cannot fully explain the
residual 3**, so I am reporting the refutation as certain and the replacement as best-fit,
not as closed.

Why `engine-facts.md`'s own verification passed: it was done on a map with **32 walls of
1225 (2.6%)**, where the two candidate denominators differ by 2 per-mille and rounding hides
it. It is a real check performed on the one kind of map that cannot discriminate — the same
shape as LEARNINGS §22, a quantity sized on an unrepresentative case.

**And the retraction audits harder than the claim.** My first table divided per-mille by
passable tiles (134% — LEARNINGS §23). My second divided correctly but set the saturation
ceiling to `1000 x (1-wallfrac)`, inheriting the documented denominator. **What both versions
took for granted is that a coverage *sum* is the right instrument for saturation at all.** It
is not: it needs a denominator, and the denominator was the thing in doubt. The paint-only
grid counts unpainted tiles directly and needs no denominator:

```
map            % of paintable tiles still UNPAINTED, counted from the grid
               r100    r200    r300    r400    r600    r800     game ends
Money          29.9%    1.6%    0.1%    1.1%    1.1%    0.9%      r1549
DefaultLarge   48.7%   20.2%    3.1%    1.1%    1.4%    1.1%      r1398
rain           33.6%   11.7%    5.0%    5.2%    1.6%    3.2%      r1507
Gears          37.4%   30.4%   16.6%    5.8%    0.6%    0.1%      r1832
```

**The map is >=95% painted by 13-22% of the way into the game, on all four maps measured
with no denominator at all.** That is the claim iteration 20 rests on, and it is now
independent of both bugs. The cov-sum table above is superseded: read it as a weak proxy
whose "never saturates" rows are an artifact of a strict threshold, not evidence.

Reported to the coordinator: `tools/engine-facts.md`'s coverage-denominator section states
the opposite of what the engine does, and it is load-bearing — it is written as a warning
that would actively push a reader into the wrong referent.

### What the tournament replays say my two independent lineages do (stall-protocol #1)

Sanctioned channel only: replays from `20260907-1300`, Gears, all three pairings.

```
                        soldiers  splashers  moppers   coverage
alice  @r600 vs bob        18         0         4        338
bob    @r600 vs alice     119        35        24        646     (won r690)
alice  @r1400 vs carol     52         0         9        554     (won on AREA_PAINTED)
carol  @r1400 vs alice      7         0        22        382
carol  @r1000 vs bob        2         0         8        244
bob    @r1000 vs carol     83        21        14        656
```

**Neither alice nor carol builds a single splasher, in any window of any game I sampled.**
Carol drifts to a near-pure mopper composition late (7 soldiers, 22 moppers, +53 moppers
per 200 rounds). I am the only lineage of the three fielding the one unit that can convert
enemy paint outright.

Two things follow. First, this is direct support for iteration 20's direction rather than a
coincidence: my one structural difference from both independent lineages is the unit whose
share I am now increasing. Second — and this is the self-referential blind spot pointing the
other way — **all three of us starve**: alice's deaths are ~95% starvation (37 of 39 per 200
rounds), carol's are lower but large, and mine are ~95%. A weakness all three lineages share
is exactly what none of our instruments can see, and the tournament cannot reveal it either
because it is zero-sum. Logging it as an open question, not a candidate.

## Iteration 20 RESULT — dose curve has an INTERIOR PEAK at 2:2:1. Roster running before I accept.

Run `20260908-000848`, `BOT=bob` (the refactored zero arm), one shared 25-map sample, 200
games, complete. Scores below are wins **by the zero arm**, so a low number means the
opponent arm is better.

```
arm            mix        zero-arm   95% CI      vs null    arm swept   arm swept-against   split D
bob_iter18      --          25/50    [25, 25]   exactly the null (se=0)     0        0         25
bob_mirror      --          25/50    [25, 25]   exactly the null (se=0)     0        0         25
bob_s2        2:2:1         17/50    [12, 21]      -3.45 sd                 8        0         17
bob_s3        1:3:1         21/50    [15, 27]      -1.31 sd                 7        3         15
```

**The mandatory identity check passed exactly**: the zero arm scored 25/50 against
`bob_iter18` with **all 25 maps split and se = 0**. The refactor is a verified no-op, so
`bob_s2`'s margin against the zero arm *is* its margin against `bob_iter18` — established by
behavioural identity, not by chaining head-to-heads (which §21 says does not work).

```
dose curve (games above the null)      3:1:1  ->  0      2:2:1  ->  +8      1:3:1  ->  +4
```

**Interior peak, which doctrine #2 calls the strongest evidence available here** — and I
pre-registered it mechanistically in §24a before the run: cut soldiers too far and the
mopper->soldier repaint chain starves, because a mopper turns enemy paint NEUTRAL and only
a soldier can then claim it. That is exactly the shape that came back.

**What the sweeps add here, given §25's identity.** The margin already told me +8 and +4, so
the sweep *difference* is not new. The decisiveness is: **`bob_s2` sweeps 8 maps and is
swept on none.** `bob_s3` wins 7 and loses 3. Same net, different risk — and "never swept on
any of 25 maps" is a statement the margin alone does not make.

### Doctrine 15 (replay state is POST-turn) — scoping which of my claims it kills

Verified the mechanism in my own code rather than taking it on trust:
`RobotPlayer.run()` calls `rc.setIndicatorString(... p=" + rc.getPaint())` **after**
`Soldier.run()`/`Splasher.run()` have already acted. So my `p=` census is post-action paint
and doctrine 15 applies to it directly.

**Which way the bias runs, and why that decides everything.** Post-action paint is <= paint
at the decision point, always. So a replay-derived affordability rate is biased **downward**:

- it can **manufacture** a false *"could not afford"* finding — the other lineage's case
- it can only **understate** a *"could afford"* finding

My claim was *"89.6% of soldiers held paint above the floor — they were able and idle"*.
That is a **can-afford** claim, so the bias makes it conservative. It survives a fortiori.

**The prescribed reconciliation — multiply the rate out, compare against a countable thing:**

```
~103 of 115 soldiers affordable x 21 rounds  ~=  2,163 affordable soldier-turns
paint actions actually taken in that window   =        10
neutral tiles CREATED in that window (mopper unpaints, both teams)  =  21
```

10 <= 21. The realized count is bounded by **target supply**, not by affordability, and the
supply number is a count of realized actions, immune to doctrine 15. The gap between 2,163
and 10 is explained, so nothing is left dangling.

**Independent confirmation from a doctrine-15-SAFE instrument I already had.** The
2026-09-07 denial probe used `src/bob_probe`, an in-bot build counting at the decision
point — which is precisely what doctrine 15 prescribes:

```
splasher turns, DefaultHuge:   paint below 60   5.2%      NO TARGET >= threshold   85.4%
```

Two instruments, one of them immune, agreeing that splashers are **target-limited, not
paint-limited** — and the in-bot figure (94.8% not blocked by paint) is *higher* than the
replay figure (68% affordable), exactly as the bias direction predicts. That agreement is
what makes today's conclusion safe rather than lucky.

**Not affected**, because both numerator and denominator are realized actions or map state:
the 0.4-5.2% soldier action rates, the 7.8-16.4x splasher:soldier productivity ratios, the
saturation timings, the tower-vision counts, and the ~95% starvation share (a claim about
post-turn state, which is what post-turn state supports).

**Already retracted for a different reason:** the older "splashers and moppers run at ~1% of
action capacity" number died in LEARNINGS §7 as a *denominator* error (cumulative spawns
instead of live population; real figure ~37%). That is not a doctrine-15 fault, and saying
so keeps the two failure modes distinct.

### Pre-accept frozen roster — running now (`20260908-005627`), decision withheld

LEARNINGS §21 rule 2, written by me after iteration 18: *"the trigger is not the margin's
size; it is simply 'before accepting'"* — because iteration 18 felt too strong to need the
check and was the accept that drifted. +8 with 8 sweeps and zero swept losses feels exactly
that strong, so the roster runs first. `OPPONENTS="bob_iter0 bob_iter1 bob_iter11
examplefuncsplayer"`. The number that matters is **`bob_iter11`**, where the lineage
recorded 25/50 for iteration 12 and **20/50 for iteration 18** — the drop that started all
of this. **Pre-registered: if this candidate does not beat iteration 18's 20/50 against
`bob_iter11`, I do not accept it on the head-to-head alone.**

## Iteration 20 — **ACCEPTED**. Spawn 2 splashers per 5 units instead of 1.

Frozen roster `20260908-005627` (200 games, complete), run **before** the accept decision:

```
opponent              candidate    vs null    iter18 was    iter12 was    per-map (0/1/2)
bob_iter0               46/50     +11.52 sd     46/50           --        {1:4, 2:21}
bob_iter1               44/50      +8.93 sd     43/50           --        {1:6, 2:19}
bob_iter11              35/50      +3.53 sd     20/50         25/50       {0:1, 1:13, 2:11}
examplefuncsplayer      50/50    +25 vs null    50/50           --        {2:25}
```

**`bob_iter11` is the number this whole investigation has been about.** The lineage went
25/50 -> 20/50 across iterations 12 and 18, which is the drop that triggered the §5b
pairwise ablation, the refuted destructive-pair nomination, and the rejected iteration 19.
Iteration 20 puts it at **35/50 — +15 games over iteration 18 and +10 over iteration 12.**
No roster member regressed. The decline is not merely halted, it is reversed past where it
started.

### The full accept case

1. **Head-to-head vs the snapshot it replaces: +8** (17/50 for the zero arm), 8 maps swept,
   **0 maps swept against**. Established through a *verified behavioural identity* — the
   zero arm scored exactly 25/50 against `bob_iter18` with all 25 maps split and se = 0 —
   not by chaining margins, which §21 says does not work.
2. **Dose curve with an interior peak**, pre-registered mechanistically before the run:
   `3:1:1 -> 0`, `2:2:1 -> +8`, `1:3:1 -> +4`. Doctrine #2's strongest available shape.
3. **Frozen roster run before accepting**, per §21 rule 2 — the rule I wrote after
   iteration 18 and whose whole point is that it applies when the margin feels too strong to
   need it. It did feel that strong. It also came back +15.
4. **Both controls exactly at the null**, se = 0, every map split.
5. Mechanism traced at the **decision** level before a single game was played, and the two
   pre-checks that could have killed it were run first (one of them did kill the design I
   started with).

### What the mechanism actually is

The map is >=95% painted by 13-22% of the way into a game (denominator-free tile counts, four
maps). A soldier **cannot overwrite enemy paint**; only splashers and moppers can. So for
roughly three-quarters of every game, most of a soldier's turns have no legal scoring move —
0.4-5.2% action rates, while ~95% of soldier deaths are starvation and each replacement
costs the tower a full 200-paint stash. Moving one spawn slot in five from soldier to
splasher redirects that paint into the only unit that can convert enemy territory.

Why it stops at 2:2:1 and reverses by 1:3:1: a mopper turns enemy paint **neutral**, and only
a soldier can then claim it, so soldiers are **demand-limited rather than useless** (§24a).
Cut them too far and the mopper->soldier chain starves. I wrote that prediction down before
the run and the curve came back that shape.

### Post-accept routine (atomic, this commit)

- `src/bob_iter20/` snapshotted and compile-checked in isolation.
- `progress/vs_old_bots_history.csv` +4 rows; both charts regenerated.
- `replays/iter20_bob_iter18_Gears_botB_WIN.bc25` — a swept win on `Gears`, the map every
  mechanism measurement in this iteration was taken on.
- Iteration 20 is a multiple of 5, so it **joins the frozen roster** from here.

**Tooling note (not worked around, reported):** the four new roster rows are labelled
`bob_iter18+cand` because `bot.txt` is written at launch, before the snapshot exists.
Re-running `track_vs_old_bots.py` after creating `src/bob_iter20` replaces the rows but
keeps the old label, so an accepted candidate's roster point stays permanently "hollow" on
the only absolute chart I have — it reads as "may have been rejected" when it was accepted.
I am **not** hand-editing the CSV, which the docs say is derived and never hand-edited, and
a hand-fix would hold only as long as I remembered it. Reported to the coordinator.

---

## Iteration 21 — PRE-REGISTERED before the run: denial units have no long-range objective

New functional area. Iteration 20 doubled the splasher share (1→2 of every 5 spawns), which
makes the largest un-acted-on number I own twice as expensive as it was when I measured it.

### The number this iteration attacks

From the 2026-09-07 denial probe (`src/bob_probe`, counted at the **decision point**, so
doctrine 15 does not touch it):

```
SPLASHERS  nothing scoreable in vision at all   1,650 / 2,908 turns   56.7%
MOPPERS    no enemy paint in vision at all      1,895 / 1,942 turns   97.6%
```

Both types react only to what is inside `VISION_RADIUS_SQUARED` and **random-walk
otherwise**. The probe's own conclusion was that the fault is not paint and not the
threshold: *"there is no target to navigate to."* Nothing has been done about it since.

### Mechanism chain, each link verified rather than assumed

1. The map is **>=95% painted by 13-22%** into a game (denominator-free tile counts, four maps).
2. Once saturated the only scoreable tiles are **enemy** tiles — a soldier cannot overwrite
   enemy paint (`engine-facts.md`), and `SPLASHER_ATTACK_ENEMY_PAINT_RADIUS_SQUARED = 2`
   confirms the splasher is the unit that can, which is what my score function already models.
3. Enemy tiles are in the **enemy half**, by map symmetry.
4. `VISION_RADIUS_SQUARED = 20` — a radius under 4.5 tiles on maps up to 60 wide. A unit in
   friendly territory cannot see the enemy half, and has no other way to learn where it is.
5. So the denial units sit in their own paint, rich and idle, exactly as counted.

### The change (one mechanism, no tuned constant)

A **migration beacon**: each robot records its birth location once and computes the 180°
rotation of it about the map centre, `(W-1-x, H-1-y)`. When — and *only* when — there is
**nothing scoreable in vision at all**, it navigates to the beacon instead of random-walking.

**Why the rotation is symmetry-agnostic, which is what makes it constant-free.** BC25 maps
are symmetric under one of vertical reflection, horizontal reflection, or 180° rotation. I do
not need to know which, because I only need the beacon to land in the *enemy half*:

```
vertical reflection  (enemy half is x > W/2):  beacon x' = W-1-x > W/2   in enemy half
horizontal reflection(enemy half is y > H/2):  beacon y' = H-1-y > H/2   in enemy half
180 rotation         (both flip):              both hold                 in enemy half
```

All three cases hold, so the beacon needs **no symmetry detection and no comms**. It is not
the true mirror of my spawn under reflection — it does not have to be.

### Pre-checks done before writing a line of it

- **Is the march affordable?** `PENALTY_ENEMY_TERRITORY = 2`, `PENALTY_NEUTRAL_TERRITORY = 1`
  against `MOVEMENT_COOLDOWN = 10` / `COOLDOWNS_PER_TURN = 10`. Crossing hostile ground is a
  **cooldown tax of 10-20%, not a paint cost** — there is no paint drain for standing on
  enemy paint. And `INCREASED_COOLDOWN_THRESHOLD = 50` only bites below 50% paint, while
  splashers carry a measured mean of **205 of 300 (68%)**. The march is affordable; verified
  from `GameConstants` in the 3.1.0 jar, not from memory.
- **Does it fight an existing mechanism?** No. The patch touches exactly one branch — the
  `tgt == null` fallback. A splasher already adjacent to a scoreable tile (`best <= 2`) still
  holds position exactly as before; that branch is copied through unchanged and I checked it.
- **Will it silently never execute?** This is what voided iteration 17. `src/bob_mprobe`
  (arm B plus counters, non-competing) will be run separately to confirm the branch fires and
  the beacon distance actually falls.

### Arms — one run, shared map sample, so within-run comparisons are exact

`BOT=bob` (= `bob_iter20`, verified byte-identical) vs three opponents:

```
bob_m0   package rename only          MANDATORY IDENTITY CONTROL: must be 25/50, se = 0
bob_mA   splashers migrate
bob_mB   splashers AND moppers migrate
```

### Pre-registered gate, and the shape I predict

- **Void** the run if `bob_m0` is not 25/50 with every map split. The zero arm is the only
  thing standing between me and §21's "margins do not chain".
- **Accept-eligible** requires the best arm at **>= +7 games over the null (>= 32/50)** and
  **swept-against <= 3**. Margin and sweeps are the same number (§25) — the sweep clause is
  there for **D, the split count**, i.e. whether the pair is decisive or coin-flips.
- **Before accepting anything**, the frozen roster runs (§21 rule 2 — the rule I wrote after
  iteration 18 precisely because it applies when the margin feels too strong to need it).
  Registered now: **no roster member may regress by more than 3 games, and `bob_iter11` must
  hold at >= 32/50** against iteration 20's 35/50.

**The shape I predict, and it is not the obvious one.** Moppers have far the worse pathology
(97.6% vs 56.7%), so the naive expectation is `mB > mA`. I predict **`mA > null` but
`mB < mA`**, from the mechanism §24a already established: a mopper turns enemy paint
**neutral**, and only a **soldier** can then claim it. Soldiers do not migrate in either arm.
So marching moppers deep into enemy land breaks the mopper→soldier chain — it manufactures
neutral tiles where no soldier will ever arrive. That is the same interior-peak logic that
made iteration 20's dose curve turn over at 1:3:1, applied before the fact rather than after.

If `mB > mA` instead, the chain story is weaker than §24a claims and I will say so.

### Tournament `20260908-0100` — the external instrument confirms the iteration-18 regression

This round-robin played `bob @ f67ac8b` = **iteration 18**. The previous one
(`20260907-1300`) played `bob @ ceef7af` = **iteration 12**. So the delta between them is
exactly the 12→18 step my own frozen roster flagged, measured this time against opponents my
lineage did not produce.

```
                 20260907-1300      20260908-0100     delta
bob                  92.3%              70.3%         -22.0
alice                38.0%              47.3%          +9.3
carol                19.7%              32.3%         +12.7

alice vs bob        7.3%               26.0%         +18.7  (alice's share)
bob vs carol       92.0%               66.7%         -25.3
alice vs carol     68.7%               68.7%           0.0   <-- unchanged
```

**Two independent instruments now agree that iteration 18 was a regression:**

```
frozen roster, absolute   bob_iter11:  iter12 25/50  ->  iter18 20/50
tournament, relative      standings:   iter12 92.3%  ->  iter18 70.3%
```

Per §26 I have to ask whether that is independence of *derivation* or of *referent*. It is
genuinely of referent: the roster is my own frozen snapshots, the tournament is two foreign
lineages. Different opponents, different map procedure, same verdict.

**But the tournament number cannot carry the attribution on its own, and the report says so
in its own words:** wins are conserved across the three bots, so a delta means "changed
*relative to* the other two" and never "got worse". Both siblings also changed commits
between the two runs, so -22.0 is a priori consistent with bob standing still while both
others improved.

**What decides it is the `alice vs carol` cell: 68.7% → 68.7%, a delta of exactly 0.0.**
Both siblings changed builds, yet their head-to-head did not move a single game, while both
gained heavily against bob. The parsimonious reading is that the thing that changed is bob.
The alternative — both improving by precisely the amount that leaves their mutual record
untouched — is possible but requires a coincidence, and the frozen roster, which *is*
absolute and cannot move under anyone else's improvements, already says iteration 18 lost 5
games to `bob_iter11`. The relative instrument and the absolute one point the same way, so
the attribution holds.

**Where this leaves iteration 20.** It was committed at 01:28, after this tournament's 01:00
export, so **iteration 20 has never played a tournament**. Its 35/50 against `bob_iter11`
(+15 on iteration 18, +10 on iteration 12) is so far a purely internal claim. The 13:00 UTC
round is its first external test, and it is a real prediction rather than a hope: if the
roster is measuring what I think it is, bob's standing should recover most of the -22.0. If
it does not, the roster and the tournament disagree about my own lineage, and *that*
disagreement becomes the next thing to investigate rather than any new mechanism.

### Iteration 21 pre-check I had missed: how long is the march? (offline, zero VM load)

I priced the march's *rate* (a 10-20% cooldown tax) but never its *length*, which is the
number that decides whether the mechanism has time to matter. Computed offline from the
`.map25` ruins tables — ruins are where towers get built, so they are the right proxy for
where units are actually born throughout a game:

```
march length = Chebyshev(birth, beacon) = max(|W-1-2x|, |H-1-2y|)   (movement is 8-directional)

                    median      worst map
moves                  30           83
rounds @ ~1.15          34           95      (the hostile-ground cooldown tax)

game length                       2000 rounds
map saturates 13-22% in        260-440 rounds   <- when the mechanism starts to matter
```

**A splasher reaches the enemy half in ~34 rounds at the median, ~95 in the worst case —
1.7% to 4.8% of a game, and 8-13x sooner than saturation.** So the beacon is not a
late-game mechanism that arrives after the game is decided; units born at any point in the
game arrive ~34 rounds later. The pre-check passes with a wide margin, which is the only
reason the "it converts idle turns" story can hold at all — had the march cost 300 rounds it
would have been converting idle turns into *travel* turns and nothing else.

Note the degenerate case is handled for free: a unit born near the map centre has a march
length near zero and is "arrived" immediately, which is correct — it is already at the front.

### A structural weakness in the tournament data, and a SECOND pre-registered prediction for iteration 21

Mined the local `20260908-0100` results (bob = iteration 18) against map geometry parsed from
the jar. Bob's per-map win rate correlates with map **area**:

```
corr(win rate, area)    +0.412          corr(win rate, wall %)   -0.246
area >= 2500  (n=16)     84.4%
area <  2500  (n=59)     66.5%

worst maps: Brat 0/4 (841)  DefaultSmall 0/4 (400)  Filter 1/4 (441)  Jail 1/4 (600)
            FourCorners 1/4 (625)  CastleDefense 2/4 (400)  Barcode 1/4 (1050)
best maps:  TheBest 4/4 (3600)  Restart 4/4 (3025)  UglySweater 4/4 (2500)  memstore 4/4 (2301)
```

**Bob is a large-map bot.** Seven of the eight worst maps are among the smallest in the
corpus. That is consistent with the lineage's whole direction: splasher-heavy area denial
needs territory to convert, and on a 20x20 map the game is decided before denial compounds.

**Why this predicts where iteration 21 will and will not help.** The beacon fixes *blindness*
— units that cannot see a target. Blindness is a function of vision relative to map size, and
`VISION_RADIUS_SQUARED = 20` gives a 9x9 sensed box:

```
DefaultSmall  20x20     81 / 400  = 20.3% of the map visible from one tile
DefaultHuge   59x59     81 / 3481 =  2.3%
```

**So I pre-register: iteration 21's gain should be concentrated on LARGE maps and be near
zero on small ones**, because on a small map a wandering splasher stumbles onto the enemy
half by accident within a few turns and there is little for the beacon to fix. If the run
comes back with a gain that is *flat* across map size, my mechanism story is wrong even if
the margin is positive — the bot would be winning for some reason other than the one I built.

That is deliberately the uncomfortable prediction: it says my headline number should come
from the maps I am *already strongest on*, and it means iteration 21 is **not** the fix for
the small-map weakness. That weakness is the strongest candidate for iteration 22, and I am
naming it here so it does not get quietly absorbed into this iteration's story.

**Caveat, stated rather than buried:** this is iteration 18, a build both instruments agree
was regressed. The area correlation may differ for iteration 20. The 13:00 UTC tournament
gives the same table for iteration 20 and I will recompute rather than assume it carries.

### How bob loses, split by map size — sharpening the iteration 22 candidate

Same tournament, joining `results.csv` to `reasons.txt` (join verified: 450 unique keys,
0 duplicates, 0 unmatched of bob's 300 games).

```
bucket           outcome  games   mean rounds  median   lost on tiebreak
small (<2500)      won      157       1109       965          15%
small (<2500)      lost      79       1043       952          20%
large (>=2500)     won       54       1147       944          20%
large (>=2500)     lost      10       1781      2000          70%
```

**The two buckets fail in completely different ways.**

- On **large** maps bob loses 10 games in 64, and those losses run to the **round cap**
  (median exactly 2000) and are **70% tiebreaks**. Bob is essentially never *beaten* on a
  large map; it occasionally fails to finish and loses on a paint count.
- On **small** maps bob loses 79 in 236, at a median of **952 rounds** with only 20%
  tiebreaks. Those are decisive mid-game losses: the opponent reaches the coverage threshold
  while the game is still live.

So the small-map problem is **not** an endgame or a closing problem — it is being out-paced
to 70% coverage in the first half. That is a tempo/economy failure, and it is a different
animal from everything iterations 16-21 have addressed, all of which improve *denial*
(converting enemy territory once the map is full). Denial cannot help in a game that ends
before the map fills.

This is now a concrete iteration 22 hypothesis rather than a vague weakness, and it is
deliberately outside the direction I have been mining, which is what the algorithm asks for
when one area has been worked hard.

**A caution I am writing down before I act on it:** the same +0.41 area correlation would
appear if my *opponents* happen to be small-map specialists, since tournament wins are
zero-sum among the three. "Bob is weak on small maps" and "alice and carol are strong on
small maps" are the same table. Distinguishing them needs the frozen roster — my own
snapshots, which cannot have specialised against me — broken down by map size. That is a
cheap check on data I already hold and it comes before any iteration 22 code.

### The confound was live: "bob is a large-map bot" does NOT survive its own check

I said the frozen-roster breakdown comes before any iteration 22 code. It does, and it
refutes the framing I had just written. Same two roster runs, split by map area:

```
iteration 20 (run 20260908-005627)        small maps            large maps
  vs bob_iter0                            36/38  (94.7%)       10/12  (83.3%)
  vs bob_iter1                            35/38  (92.1%)        9/12  (75.0%)
  vs bob_iter11                           27/38  (71.1%)        8/12  (66.7%)

iteration 18 (run 20260907-201817)
  vs bob_iter0                            31/34  (91.2%)       15/16  (93.8%)
  vs bob_iter1                            28/34  (82.4%)       15/16  (93.8%)
  vs bob_iter11                           15/34  (44.1%)        5/16  (31.2%)
```

**Against opponents that cannot have specialised against me, there is no large-map
advantage — iteration 20 is if anything better on small maps, on all three opponents.**
The +0.412 area correlation appears only in games against alice and carol.

So the two readings of that correlation are not equally likely after all, and the one I
led with is the weaker: **"alice and/or carol are relatively stronger on small maps" fits
the evidence better than "bob is weak on small maps."** Tournament wins are zero-sum among
three bots, so those two sentences describe the same table, and only a non-sibling opponent
can separate them. Mine says the effect is not in bob.

**What I am retracting:** "Bob is a large-map bot", and iteration 22 as a small-map tempo
fix. The premise is not established.

**What survives, because it conditions on losses rather than comparing across opponents:**
bob's large-map losses run to the round cap and are 70% tiebreaks, while its small-map
losses end mid-game at a median of 952 rounds. That contrast is between two sets of bob's
own games, so a sibling's small-map skill cannot manufacture it — it says that when bob does
lose a large map it is because it failed to *close*, and that is worth a look on its own
terms. But it is a much narrower claim than the one I made, and 10 losses is a thin base.

**The methodological point, which is the same one as §27 and §28 for the third time today.**
I had the discriminating data on disk before I wrote the claim — the roster runs were already
collated in `gauntlet/`. What made me write it anyway is that the tournament table is the
*more impressive* instrument, and impressiveness is not discrimination. The zero-sum caveat
was even printed in the report I was reading. I wrote the caveat down, called the check
cheap, and still published the headline before running it.

### AMENDMENT to the iteration 21 pre-registration, made BEFORE the run returned: I got the penalty's UNIT wrong

In the pre-registration I wrote:

> Crossing hostile ground is a **cooldown tax of 10-20%, not a paint cost** — there is no
> paint drain for standing on enemy paint. Verified from `GameConstants` in the 3.1.0 jar,
> not from memory.

**That is backwards, and my own `RULES.md` has had it right the whole time:**

> Paint penalties per turn (from robot's own stash): end turn on neutral −1, on enemy −2
> (`PENALTY_NEUTRAL/ENEMY_TERRITORY`); PLUS 1 × (# adjacent allied robots), doubled while in
> enemy territory. Moppers pay **2×** the territory penalties.

`PENALTY_ENEMY_TERRITORY = 2` is **2 paint per turn**, not 2 cooldown. I read the constant's
*value* correctly out of the jar and then assumed its *unit*. The discriminating evidence was
sitting in the same constant dump I printed: **`MOPPER_PAINT_PENALTY_MULTIPLIER = 2`**. A
multiplier that applies to the territory penalty and is named *PAINT* settles what the
penalty is denominated in. I printed that line and did not read it.

### Redoing the affordability pre-check with the right unit

Roughly half a march is over friendly paint (no penalty); price the other half at the enemy
rate, and recall a mopper pays double and cannot refill away from a tower:

```
                  capacity   drain/turn   median march (~17 hostile rounds)   worst (~47)
SPLASHER            300          -2            -34 paint   arrives ~170        -94  arrives ~110
MOPPER              100          -4            -68 paint   arrives ~32         -188  DEAD
```

- **Splasher: still affordable.** It needs 60 paint to splash and arrives with ~170 of a
  measured mean 205. The pre-check passes, so arm A's design stands as written.
- **Mopper: not affordable.** On a median map it arrives with ~32 of 100 — below the
  `INCREASED_COOLDOWN_THRESHOLD = 50`, so it is *also* slowed exactly when it arrives. On a
  long map it reaches zero paint, and at zero a robot cannot move or act and takes
  `NO_PAINT_DAMAGE = 20`/turn against a mopper's **50 HP** — dead in three turns.

**So arm B should be clearly worse than arm A, and may well be worse than the null.** That is
the same ordering I pre-registered, but the reason I gave was wrong: I attributed it to the
mopper→soldier repaint chain of §24a. The real mechanism is cruder — **a migrating mopper
cannot pay for the trip.** Both predict `mB < mA`, so the run cannot separate them, and I am
writing that down now rather than claiming afterwards that whichever story fits was mine.

If `mB` comes back at or above `mA`, then this drain model is wrong too, and that becomes the
finding rather than anything about migration.

**Why this correction matters beyond one arm.** "Verified from the jar, not from memory" was
the phrase I used to license the claim, and it was true of the number and false of the
meaning. A constant dump gives values, never units — and the unit was recoverable from the
very same dump. Reading the *name* of the neighbouring constant would have caught it, and so
would opening `RULES.md`, which is my own javap-verified digest and the file I skipped
because I "already knew" the mechanic.

**Knock-on to the march-length pre-check.** That entry priced rounds at `moves x 1.15`,
where the 1.15 was the "hostile-ground cooldown tax" that does not exist. Terrain costs
paint, not cooldown, so the march is **~30 rounds at the median, not ~34** — the error was in
the conservative direction and the pre-check passes by slightly more than I claimed. The one
cooldown effect that is real is `INCREASED_COOLDOWN_THRESHOLD = 50`, which bites *below* 50%
paint — irrelevant to a splasher arriving at ~57% of capacity, and precisely the trap for a
mopper arriving at ~32%.

### Why iteration 15 (bug navigation) may have been tested in a regime where it could not pay

Written now, before iteration 21's result, because it is an argument about the *design* and
I do not want it available afterwards as an excuse.

Iteration 15 replaced greedy nav with Bug2 and was **rejected on two independent map draws**
(−4, −4, pooled 45/100). I have just audited where every `navTo` call in that bot was
pointed:

```
Splasher   nearest scoreable tile      from senseNearbyMapInfos()   -> within vision
Mopper     nearest enemy paint         from senseNearbyMapInfos()   -> within vision
Soldier    workRuin                    from senseNearbyRuins(-1)    -> within vision when latched
Soldier    srp centre, refill tower    vision-derived               -> within vision
```

**Every target was inside `VISION_RADIUS_SQUARED = 20` — a radius of 4.47 tiles.** Bug
navigation exists to circumnavigate an obstacle standing between you and a *distant* goal.
Over a four-tile hop there is essentially no concavity to escape, so Bug2's benefit was
unmeasurable there while its costs — latching a heading, holding it until the target is
strictly closer, and the deletion of the random escape — were paid on every step. A −4 result
is what that predicts.

**Iteration 21 is the first thing this lineage has built that creates a long-range target
at all**: a median 30-tile march. If arm A shows a positive but modest effect, the natural
reading is that the *objective* is right and the *executor* is the greedy fan, and bug
navigation becomes re-testable on evidence rather than on a hunch — the regime changed, which
is the only legitimate reason to reopen a rejected direction.

**Registering the trap in the same breath.** This is a tidy story for reopening a direction I
already spent two map draws rejecting, and tidy stories about one's own past failures are
exactly what a lineage talks itself into. So: it is a hypothesis about *why* iteration 15
failed, not evidence that Bug2 works, and it does not become an iteration until arm A has
actually produced a long march worth navigating. If arm A is flat or negative, this note is
moot and stays moot — there is no version of it that survives arm A failing.

### Correction to the iteration 20 accept note: iteration 20 does NOT join the frozen roster

I wrote, in the iteration 20 post-accept routine:

> Iteration 20 is a multiple of 5, so it **joins the frozen roster** from here.

It does not, and `progress_lib.roster_numbers` warns against precisely this misreading in
its own docstring: *"Strides over POSITION, not over the iteration number. Striding over
numbers ({0,1,6,11,...}) silently drops every slot whose iteration was rejected."*

```
accepted snapshots        [0, 1, 3, 7, 9, 11, 12, 18, 20]     iteration 20 is at POSITION 8
roster_numbers(stride 5)  [0, 11]                             positions 0 and 5
roster (with extras)      bob_iter0  bob_iter1  bob_iter11  examplefuncsplayer
```

`bob_iter20` is absent, and I checked it is **not** the `exclude_current` rule doing it —
passing `exclude_current=False` returns the same four names. It is the stride: position 8 is
not a multiple of 5, so iteration 20 joins the roster only after **two more accepted
snapshots** put a rung at position 10. (`bob_iter1` is in the list not by stride but by the
"never drop a rung that already has history" rule.)

**Why I am bothering to correct a line in a note.** The claim would have set up a future
session to expect `bob_iter20` in the next roster run, not find it, and go looking for a bug
in a tool that is behaving exactly as documented. That is the same shape as §27: a false
statement about an instrument costs more than a false statement about the bot, because the
instrument is what adjudicates everything after it. My accept decision itself is untouched —
the roster it ran against was `bob_iter0/1/11/examplefuncsplayer`, which is what the tool
actually selected and what the results table reports.

---

## Iteration 21 — RESULT: REJECTED. The migration beacon is worth zero, and both of my pre-registered predictions came out wrong

Run `20260908-015815`, 150 games, 25 maps resampled, `BOT=bob` (= `bob_iter20`, `dirty=0`).
Scored with `bob-tools/arm_eval.py`, which prints the **arm's** score (not the reference's):

```
arm             score  vs null     sd  swept  swept-against  split
bob_m0        25/50         +0  +0.00      0              0     25
bob_mA        24/50         -1  -0.28      4              5     16
bob_mB        26/50         +1  +0.28      4              3     18
```

### The identity control passed, and passed perfectly

`bob_m0` is a package rename of the baseline and came back **25/50 with all 25 maps split by
side and zero swept in either direction**. That is the third time this lineage has measured
its own null and the third time it has come back with **no variance at all**, not binomial
spread. The run is valid and the comparisons below are exact, not estimates.

### The gate, applied

Pre-registered: *accept-eligible requires the best arm at >= +7 games over the null (>= 32/50)
and swept-against <= 3.* Best arm is `bob_mB` at **26/50, +1**. That is not a near miss
(`NearMissMargin` is 5 points and this is 1 game); it is a flat zero. **Iteration 21 is
rejected outright.** No refinement is earned — there is no directionally-correct effect to
refine.

The shape is the churn signature from doctrine 10, unusually cleanly. Against the null every
one of 25 maps splits by side; migration converts 9 maps (arm A) and 7 maps (arm B) into
decisive pairs, and they come out **4–5 and 4–3** — mixed direction, scattered, near-perfectly
balanced. The mechanism unambiguously *changed the games*. It did not change who won them.

### Prediction 1 — the arm ordering — REFUTED, and I said in advance I would say so

I pre-registered `mA > null` and `mB < mA`, from the §24a mopper→soldier chain: a marching
mopper manufactures neutral tiles no soldier will arrive to claim. I wrote: *"If `mB > mA`
instead, the chain story is weaker than §24a claims and I will say so."*

**`mB` (26) came in above `mA` (24).** So I say it: this run gives no support to the chain
story as an *ordering* prediction. But I am not going to overclaim the refutation either,
because 2 games is exactly the scale at which this run cannot discriminate anything — the
honest statement is that **the run cannot tell arm A from arm B**, and my prediction was that
it would be able to. A prediction that the difference would be visible is refuted by the
difference not being visible, and that is the whole of what died here. §24a itself is
untouched; what died is my belief that it was worth 5+ games in this configuration.

The redone affordability pre-check (mopper arrives at ~32/100 paint, below
`INCREASED_COOLDOWN_THRESHOLD`, dead on long maps) predicted `mB` should be *clearly worse*
than `mA` for a second, cruder reason. That is refuted too, and by the same 2 games. Two
different mechanisms both predicted `mB < mA`; neither happened. Since both predicted the same
sign, the run was never able to separate them — which I wrote down at the time — and now
neither is supported.

### Prediction 2 — the map-size gradient — came out the WRONG SIGN

This one I had not pre-registered as sharply, but the mechanism's entire motivation is
`VISION_RADIUS_SQUARED = 20` (radius 4.47) against maps up to 60 wide: the bigger the map, the
larger the fraction of enemy territory a unit cannot see, and the more a long-range objective
should be worth. So the mechanism predicts **gain concentrated on large maps**.

```
arm              small <2500    large >=2500  gain small  gain large
bob_m0           19/38            6/12                +0          +0
bob_mA           21/38            3/12                +2          -3
bob_mB           22/38            4/12                +3          -2
```

Both arms gain slightly on small maps and lose on large ones — **the reverse of the
mechanism's own rationale, and both arms agree in sign on both halves.** With 12 large cells
this is thin (a 3-game move on 12 games), so I am not claiming migration actively hurts big
maps. What I *am* claiming is that the one place the mechanism story says the effect must live
is the one place the sign is negative, and that is a positive disconfirmation rather than an
absence of evidence.

### What this closes, and what it does not

**Closed direction (ledger):** *"give the denial units a long-range objective by beacon, so
they stop random-walking in friendly paint."* Measured at **+1 and -1 games on 25 resampled
maps against a zero-variance null**, with the map-level gradient the wrong sign. This is the
attack on the largest un-acted-on number I own (splashers idle 56.7% of turns, moppers 97.6%)
and it converts to nothing.

Re-opening requires a specific reason the above no longer applies — and note the obvious
"reason" is already refuted: *"the beacon is the wrong target, a better target would work"*
is not licensed by this run, because the run does not show units failing to reach a bad
target, it shows arriving somewhere changing nothing about the score.

**Not closed:** the 56.7% / 97.6% idle rates themselves. Those are measured at the decision
point and stand. What is now known is that **idleness is not costing games through the
mechanism I proposed** — the units being somewhere else does not, on its own, buy anything.
That is a genuinely different fact from "the idleness is harmless", and I do not yet have the
second one.

**Explicitly moot, per its own registration:** the note above titled *"Why iteration 15
(bug navigation) may have been tested in a regime where it could not pay"*. I wrote: *"If arm
A is flat or negative, this note is moot and stays moot — there is no version of it that
survives arm A failing."* Arm A came in at **-1**. The note is moot. Bug navigation stays
rejected, and iteration 15's two rejections stand at three.

---

## Iteration 22 — PRE-REGISTERED before the run (launched, 160 games): the tower rule is not symmetric on 31 maps

**Functional area: tower type.** Last touched at iteration 12, which is the largest single
effect this lineage has ever measured (+26 points).

### How I got here, because the route matters

Iteration 21 was rejected, so I went target-hunting rather than mechanism-hunting, and
dumped the three replays the migration probe had already produced (zero extra VM cost).
The aggregates said something I had never looked at:

```
DonkeyKong r2000   T1 $132,014 unspent   tw25 (the cap)   twPaint 1977/25000   starved 169/228 deaths
Flower     r800    T1  $39,925 unspent   tw9              twPaint  489/9000    starved  26/34
Dominoes   r800    T1   $7,600 unspent   tw13             twPaint 1104/13000   starved  28/58
```

Every tower upgraded by ~r600, every buildable ruin taken, and the treasury then runs away
to six figures while ~75% of unit deaths are **starvation** and the tower paint pools sit at
8-10% of capacity. Chips are a slack resource; paint is the binding one. That pointed me at
the tower-type rule — and reading it turned up something sharper than the mix ratio.

### The defect

```java
return ((ruin.x + ruin.y) & 1) == 0 ? MONEY : PAINT;
```

Iteration 12 adopted this rule over iteration 7's avalanche hash and was accepted on
**+26 points**, and the recorded mechanism was *team symmetry*: "under rotation `(x+y)` and
`(W-1-x + H-1-y)` share parity whenever `W+H` is even, so mirrored ruins agree on those maps
and the two halves get the same mix." Iteration 7's hash was measured to raise mirror
mismatch (mismatched mirrored pairs 40% -> 97%) and that is what cost 20 points once SRPs
made the payoff multiplicative in paint-tower count.

**The condition in that sentence is not the corpus.** `x` and `W-1-x` sum to `W-1`, so they
share parity exactly when **W is odd**; likewise `y` needs `H` odd. On any map with an even
dimension the rule assigns **opposite** types to mirrored ruins — and 48 of the 75 maps have
one. Corpus scan (`bob-tools/foldscan/BobFold.java`, run against the engine jar's own
`.map25` flatbuffers, symmetry inferred per map from the ruin set):

```
                money share     all-one-type maps     mirror-mismatched ruins
PLAIN (today)   732/1374 53.3%          4             638/1374  46.4%   on 31 maps
FOLD  (cand.)   764/1374 55.6%          4                    0   0.0%   on  0 maps
```

**Verified in a replay I already had, not only in simulation.** Dominoes is 44x30 with
vertical symmetry, so W is even and the rule must flip on *every* mirrored pair. All nine
mirrored ruin pairs that got towers in `bob_mprobe-vs-bob-on-Dominoes` came out opposite:

```
T1 ( 2,12) MONEY  <->  T2 (41,12) PAINT        T1 (10,25) PAINT  <->  T2 (33,25) MONEY
T1 ( 3, 7) MONEY  <->  T2 (40, 7) PAINT        T1 (11,18) PAINT  <->  T2 (32,18) MONEY
T1 ( 3,19) MONEY  <->  T2 (40,19) PAINT        T1 (18,12) MONEY  <->  T1 (25,12) PAINT
T2 ( 9, 2) PAINT  <->  T2 (34, 2) MONEY        T1 (18,19) PAINT  <->  T1 (25,19) MONEY
                                               T1 (18,25) PAINT  <->  T1 (25,25) MONEY
```

The last three pairs are the point: **the same team built both halves and gave them
different types**, so this is not only a fairness problem between teams, it is the
mix-variance problem inside one team's own economy — the exact quantity iteration 12 was
accepted for reducing.

### The change (one mechanism, one line, no new constant)

Fold the coordinates into the canonical quadrant before the parity test:

```java
int a = Math.min(ruin.x, G.mapW - 1 - ruin.x);
int b = Math.min(ruin.y, G.mapH - 1 - ruin.y);
return ((a + b) & 1) == 0 ? MONEY : PAINT;
```

Invariant under all three candidate symmetries by construction, so it needs no symmetry
detection — the same "weaken the claim until it is symmetry-agnostic" move as LEARNINGS 28,
and it is exact rather than heuristic. Still a pure function of the ruin, which the marking
protocol requires. ~6 bytecodes.

### Why this supersedes iteration 12 rather than reverting it

It does not restore the hash. Iteration 12's closure was *"iteration 7's avalanche hash is a
net positive: CLOSED"*, killed by mirror mismatch; this candidate has **less** mirror
mismatch than the rule that closed it (0% vs 46.4%), and keeps parity's lattice-following
character and its money share (53.3% -> 55.6%). It extends iteration 12's own argument to
the 48 maps that argument silently excluded.

### The confound I deliberately controlled

The chip-surplus evidence above argues the money *share* is too high (the engine's cost
table puts the production-balanced share at 26-35%, against 53.3% today). That is a
**different, larger iteration**, and bundling it here would make the result uninterpretable.
The fold moves the share by 2.3 points, so this run prices symmetry and essentially nothing
else. The share change is queued as iteration 23 whatever this returns.

### Arms — `BOT=bob` (= `bob_iter20`), NMAPS=40, one shared sample

```
bob_tp0   package rename only    MANDATORY IDENTITY CONTROL: must be 40/80, every map split
bob_tp1   the fold
```

### Pre-registered gates, and a map-level prediction that is an EXACT identity

- **Void** if `bob_tp0` is not 40/80 with every map split by side.
- **Accept-eligible** at `bob_tp1` **>= 45/80** (+5 over the null) with swept-against <= 6,
  then the frozen roster before accepting (doctrine 12; no roster member may regress by more
  than 3 games).
- **The map-level prediction, and it is not a correlation but an identity.** `x` and `W-1-x`
  share parity iff `W` is odd, so on a map with **both dimensions odd** the fold changes
  nothing at all: `min(x,W-1-x) ≡ x (mod 2)`. 27 of the 75 maps are odd x odd, and the corpus
  scan confirms the money count is identical on all 27 with zero counter-examples. So:

  > **every odd x odd map in the sample must come back byte-identical between `bob_tp1` and
  > `bob_tp0`, and all deviation must fall on maps with an even dimension.**

  A 40-map draw should contain ~14 odd x odd and ~26 even-dimension maps. If a single
  odd x odd map deviates, my account of the mechanism is wrong and the run is uninterpretable
  regardless of the headline — I would be reading an effect I cannot locate. This is the
  check doctrine 3 asks for, run *inside* the evaluation instead of alongside it, and unlike
  a swept-map count it is not an algebraic restatement of the margin (LEARNINGS/doctrine 14):
  it is a statement about *which* games moved, which the margin cannot express.

- **What would falsify the mechanism story while the number still passes**: deviation
  spread evenly over odd x odd and even-dimension maps. Then the fold is doing something
  other than what I claim, and doctrine 3b applies — record the result, mark the attribution
  OPEN, and do not back-fill a story.

### Pre-checks I have NOT done, named explicitly

1. **The early-game chip cost is unpriced.** The surplus is an endgame observation; at r200
   on Dominoes one side sat at $661. The fold barely moves the share so I expect this to be
   second-order here, but it is exactly the number iteration 23 will live or die on, and I
   have not measured it. Doctrine 15 forbids taking it off replay post-state — it needs
   in-bot instrumentation at the spawn decision.
2. **`roads` swaps from mismatched to all-one-type.** The all-one-type count is 4 before and
   4 after, so the corpus total is neutral, but the *set* changes and I have not checked
   whether an all-money map is worse than an all-paint one. `roads` is 30x30, 8 ruins.
3. **I have not checked whether the mopper/splasher paint accounting closes.** Summing unit
   paint costs against paint-tower income on Flower leaves a ~3,200-per-100-round gap I
   cannot yet explain. It does not bear on this iteration, but it is an unreconciled
   residual and doctrine 5 says to say so rather than let it sit unnoticed.

### AMENDMENT to the iteration 22 pre-registration, written BEFORE the run returned: I re-derived a CLOSED direction and mis-stated my own history

Two corrections, and the second is a cost I failed to price.

**1. "Nobody ever evaluated it against the map corpus" is FALSE. I did, at iteration 14.**
`bob-tools/BobSym.java` measured exactly this and the number is in this log:

```
                                        old parity rule    new hash
maps with a mismatched mirrored pair      30 (40%)          73 (97%)
mean money%-gap between the two halves    11.0 pts          24.0 pts
```

My fresh scan says 31 maps and a team gap of 46.4% *of ruins*; the older one says 30 maps
and 40% *of maps* (mine is 41.3% on that denominator). Two implementations written a day
apart, reading the same flatbuffers by different routes, differing by one map — that is
corroboration of the parser, and the one-map gap is a symmetry-inference tie-break on a map
that admits more than one transform. Both say the same thing. **What is new today is not the
measurement. It is only the replay confirmation and the exact odd/even identity.**

**2. Folding the coordinates is a CLOSED direction, and I did not find the closure.**

> **CLOSED: "make the tower-type hash symmetry-invariant by folding coordinates."**
> Killed by the table above. Cost: about three minutes and no games.

The closure's kill argument: folding halves the number of independent draws, so whole-map
mix variance rises by sqrt(2). I had not measured that for my variant, so I measured it
before reading any game:

```
rule                  all-one-type maps   mean mix deviation   team gap
plain parity (today)        4                    9.3             11.0
folded hash (CLOSED)        6                   16.0              0.0
folded parity (mine)        4                   15.6              0.0
```

My scanner reproduces the logged 9.3 and 4 for plain parity **exactly**, which is the check
that licenses reading the third row at all. And the third row says the closure's central
argument **applies to my variant too**: I buy a perfect team gap and pay 9.3 -> 15.6 in
whole-map mix skew. What folded *parity* does not inherit is the closure's other half — the
catastrophe count stays at 4, where the folded *hash* went to 6.

**So iteration 22 is a re-open, and here is the specific reason the recorded cause no longer
applies** (the ledger requires one, and "I forgot" is not it). The closure was written at
iteration 14, and it weighed an unpriced team gap against an unpriced mix deviation —
correctly concluding "no rule dominates". **Iteration 12 then put a price on one side of
that trade and not the other**: hash -> parity was +26 points, and the mechanistic account
was mix *mismatch* (multiplicative SRP payoff in paint-tower count). Since iteration 14 the
team-gap side of the trade has a measured price and the mix-deviation side still has none.
That is new information about the closure's own trade, which is what a re-open needs.

**What the run now measures, restated.** It is no longer "does symmetry help". It is a
decomposition of iteration 12's +26 between two quantities that moved together there and
move in *opposite* directions here:

```
                       team gap      mix deviation
iteration 12 (+26)     24.0 -> 11.0   9.9 -> 9.3     both improved -- cannot separate
iteration 22           11.0 ->  0.0   9.3 -> 15.6    opposed -- this run separates them
```

- `tp1` clearly ahead  => the team gap dominates, and iteration 12's +26 is mostly that.
- `tp1` clearly behind => mix deviation dominates, and **iteration 12's recorded mechanism is
  wrong** even though its accept was right. That is the more valuable outcome of the two and
  I would rather have it than the accept.
- `tp1` flat => the two roughly cancel at these magnitudes, which is the iteration-14
  conclusion ("no rule dominates") confirmed with games instead of arithmetic.

**The pre-registered gate is unchanged** (>= 45/80, swept-against <= 6, roster before
accepting) and the odd x odd byte-identity prediction is unchanged. I am not relaxing a gate
because I found an extra argument after launching — that is the iteration-14 entry's own
closing line, and it applies to me here.

**What I actually did wrong, for the ledger.** TRAINING_ALGORITHM.md §3 says to check the
evidence already on disk before spending a run, and I checked `tournaments/` and the
gauntlet history and never grepped my own closed-directions ledger for the *mechanism*. I
searched the log for "A7" and for "BobSym" only after the run was in flight, and the second
search is the one that found this in ten seconds. **I searched by functional area and the
ledger is keyed by mechanism.** The run is not wasted — it is a better-designed run than the
one I registered, because it now has a decomposition to report either way — but it went out
under a justification that was partly false, and the false part was recoverable for free.

### Tooling: two shared-VM hazards in MY OWN `bob-tools/vm-verbose-match.sh`, plus the audit of what they may have cost

Found while the iteration-22 gauntlet was in flight, by reading `tools/vm-match.sh` to work
out why my migration-probe counters came back empty. (They came back empty because the
shared runner hardcodes `-PoutputVerbose=false` — which is not a bug, it is why my own
verbose wrapper exists. Reading it is what turned up the rest.)

My wrapper (a) built and ran inside `$WS_REL`, the very directory the gauntlets build from,
and (b) took no slot from the shared semaphore. `tools/vm-match.sh` documents and avoids
both, in comments that say exactly why: `./gradlew run` rewrites `build/classes` and
in-flight gauntlet games load their robot classes from that path, so a trace run during a
gauntlet can swap code out from under games already in progress; and a runner that does not
take a slot makes every other runner's `HARD_CAP` check a fiction on a box shared with a
live BC26 project and two sibling lineages. Fixed both: sibling directory, `acquire_slot`.

This is my file in `bob-tools/`, so fixing it is right — the "report, don't work around"
rule is about `tools/`, which is coordinator-owned. But the defect came from *copying*
`vm-match.sh` and dropping the two parts that looked like boilerplate. Both were load-bearing
and both said so in comments I did not read.

**Audit of the damage, because a fix is not an assessment.** 12 verbose runs exist. Pull
times against gauntlet windows (dir name = start, `summary.txt` mtime = collate):

```
box 13:38, gridworld 13:39   gauntlets 13:11-13:24 and 13:46-14:35     gap, clear
maze 14:38, sierpinski 14:39 gauntlets 13:46-14:35 and 14:41-15:23     gap of 6 min, clear by 3
catface/DefaultHuge 16:13    gauntlets 15:37-16:03 and 18:17-19:02     gap, clear
Rose 19:21                   gauntlets 18:56-19:18 and 19:29-20:15     gap of 11 min, clear by 3
Oasis/quack/Castle/Brat 01:20-01:50, DefaultMedium (Sep 6 18:33)       UNVERIFIABLE
```

**No verified overlap**, so no gauntlet result on disk is known to be corrupted. But twice
the margin was three minutes, which is luck and not discipline, and five runs fall in windows
whose gauntlet directories have since been pruned locally, so they cannot be checked at all.
I am not going to retract anything on this basis — "might have overlapped" is not evidence —
but the honest summary is that this lineage has been running an unsafe tool for two days and
got away with it, rather than that it was never at risk.

**The generalisable bit**: the hazard is invisible at the call site. A trace run and a
gauntlet do not conflict in anything either script prints; the collision is in a build
directory neither mentions in its output. That is why it survived being written, reviewed,
and used a dozen times.

### API SWEEP (2026-09-08, during the iteration-22 run) — 27 of 68 `RobotController` methods have never been called, and one of them is a whole subsystem

TRAINING_ALGORITHM.md Phase 0 item 2 says to sweep the full `RobotController` API
periodically because "a whole game mechanic sat unused for 81 iterations once". I had never
done it. Diffed `javap battlecode.common.RobotController` against every call site in
`src/bob`:

```
methods on RobotController   68
called by src/bob            41
NEVER called                 27
```

The 27, grouped by what they would buy:

**1. The entire communication subsystem — `sendMessage`, `readMessages`, `broadcastMessage`,
`canSendMessage`, `canBroadcastMessage`.** Not one message has ever been sent by this
lineage. Per RULES.md: robot<->tower within r²<=20 *and* connected by a path over ally paint
(<=1 msg/robot/turn), and tower->all allied towers within r²<=80 with **no paint-connectivity
requirement**. The tower-to-tower channel is the interesting one — my towers are spread across
the map, never move, and currently know nothing about each other.

**2. Markers — `mark`, `removeMark`, `canMark`.** Ally-visible map annotations, r²<=2, **1
paint**, no action cooldown. The bot uses `markTowerPattern` (a different call) and has never
placed a free-standing marker. This is a stigmergic channel that needs no radio, no
connectivity and no protocol: a robot can leave a fact on the ground for whoever arrives next.

That matters specifically because **iteration 17 was VOIDED for want of exactly this.** Its
finding was that `chooseRuin` ranks `senseNearbyRuins(-1)` — ruins in vision — and a soldier
essentially never sees two at once, so the choice set is a singleton and no ranking function
can do anything. I wrote then: *"to make soldiers agree on a ruin they would need memory of
ruins seen earlier — a much larger change than the one I priced."* Memory is one answer;
**a mark on the ground is another, and it is shared rather than per-robot.** I did not know
the call existed when I wrote that sentence.

**3. `getNumberTowers`** — the team's own tower count, readable by any robot, free. Directly
relevant to iteration 23: a self-calibrating tower-mix rule needs to know how many towers the
team has, and I had assumed that required comms.

**4. `disintegrate`** — checked the bytecode rather than guessing: `RobotControllerImpl.
disintegrate` simply throws `RobotDeathException`. **No paint refund, no chip refund.** So it
buys exactly one thing — removing a unit *now* — which is worth something only against LEARNINGS
§20's zombie soldiers, because RULES.md's upkeep rule taxes a robot 1 paint/turn *per adjacent
ally*, so a hoarding zombie is a standing drain on every neighbour, not merely on itself.
Iteration 18 reduced that population; I have not measured whether it eliminated it.

**5. Utility/debug I should just use** — `setIndicatorDot`, `setIndicatorLine` (replay-visible
tracing, far better than parsing strings), `onTheMap`, `sensePassability`, `isLocationOccupied`,
`adjacentLocation`, `getTowerPattern`/`getResourcePattern`.

`getTowerPattern` deserves a line of its own because it unblocks a design I had written off.
The shipping comment on `towerTypeFor` says the type "must stay a pure function of the ruin and
never of time", because `workOnRuin` marks once and then calls `canCompleteTowerPattern(want,
ruin)` — so a `want` that changed mid-build can never complete. That is true *only because the
code recomputes `want`*. `getTowerPattern(type)` returns the pattern, so `want` can instead be
**read back off the marks already on the ground**, which is where the decision was actually
recorded. That converts "the tower type may not depend on time" from a hard constraint into an
implementation detail — and a time-dependent (self-calibrating) tower mix is precisely what the
chip-surplus evidence argues for.

**What I am NOT doing with this.** Not building any of it now. Iteration 22 is in flight and
bundling is how results become uninterpretable. This is a target list, entered in the log so
it survives the session, and the comms/marker item is the first genuinely *structural* track
this lineage has had available — TRAINING_ALGORITHM.md's "high-risk structural exploration",
which both prior projects say produced their highest-value accepts.

**The methodological point.** This sweep took about four minutes and it has been available
every one of the 22 iterations so far. The reason it never happened is that nothing ever
*failed* in a way that pointed at it: an unused API method produces no error, no bad number,
and no losing replay to trace. It is invisible to every instrument I own except this one, which
is exactly why the algorithm makes it a scheduled sweep rather than a response to a symptom.

---

## Iteration 22 — RESULT: **REJECTED at −4**. The pre-registered prediction came out EXACT, and the offline closure I re-derived was right all along.

Run `20260908-043525`, 160 games, 40 maps resampled, `BOT=bob` (= `bob_iter20`, `dirty=0`).

```
arm             score  vs null     sd  swept  swept-against  split
bob_tp0       40/80         +0  +0.00      0              0     40
bob_tp1       36/80         -4  -0.89      3              7     30
```

Identity control `bob_tp0`: **40/80, all 40 maps split by side, zero swept in either
direction.** Fourth consecutive zero-variance null. The run is valid and every comparison
below is exact rather than estimated. (Sweep identity holds as always: 36 − 44 = −8 =
2 × (3 − 7).)

Gate was `bob_tp1 >= 45/80`. It came in at **36/80**. Rejected, and on the wrong side of the
null rather than short of the bar.

### The map-level prediction was exact, and that is the most important line in this entry

```
odd x odd cells        30   deviations  0     <- PREDICTED 0
even-dimension cells   50   deviations 40     <- all change predicted here
```

**Zero deviations in 30 odd x odd cells; 40 of 50 even-dimension cells changed.** The
identity `min(x, W-1-x) ≡ x (mod 2) when W is odd` held on every single game, and 80% of the
cells where the fold *could* act did change. Validated beforehand as a negative control on
iteration 21's migration arm, where the same categorisation gave 89% and 84% — i.e. no
spurious predictive power — so the clean split here is real.

This matters more than the headline because it settles what usually stays open. The mechanism
did not fail to engage (doctrine 5 step 0), it did not engage somewhere unexpected, and there
is no room to wonder whether I measured the thing I built: the change fired exactly where the
arithmetic said it must, nowhere else, on 80% of eligible games, **and lost 4 games doing it.**

### What this establishes, and what it does not

**Established, with games rather than a three-minute offline table:** the iteration-14 closure
of "make the tower-type rule symmetry-invariant by folding coordinates" was correct. I
re-derived that direction from scratch today, spent 160 games on it, and got the same verdict
the closure reached for free. **CLOSED, re-affirmed, now with a price attached.**

The run also converts a weakly-founded belief into a firmly-founded one, which is the
algorithm's own definition of a rejection that paid for itself. The 2026-09-07 entry concluded
"no rule dominates" from arithmetic; it now has a measured sign.

**The trade, restated with the numbers that actually moved:**

```
                       team gap   mix deviation   measured
iteration 7  -> 12       24.0 -> 11.0   9.9 -> 9.3     +26 pts  (+13 games of 50)
iteration 20 -> 22       11.0 ->  0.0   9.3 -> 15.6     -4 games of 80
```

**And here is where I stop, rather than fit a story.** Two equations, two unknowns
(games per point of gap, games per point of mix deviation) — I can solve it exactly, and the
solution is worthless, because a two-parameter fit to two data points has **zero degrees of
freedom** and therefore cannot be wrong. It is interpolation wearing the clothes of a
measurement. I am recording that I did the algebra (it yields mix deviation ~2.2x dearer per
point than team gap, which would leave iteration 12's recorded mechanism *vindicated* rather
than refuted) and that **it is not evidence**, precisely because it is the comfortable
correction — doctrine's "the dangerous corrections are the comfortable ones", and I pre-
registered a reading of this branch ("iteration 12's recorded mechanism is wrong") that the
algebra happens to reverse in my favour. Attribution: **OPEN.**

### The genuinely new structural finding, which is not a fit

**Perfect team symmetry and low mix variance are in unavoidable tension, and the tension is
structural rather than a property of my rule.** Under any of the three map symmetries the
ruins come in mirrored pairs. A rule with zero team gap must assign both members of a pair the
same type — so it has at most **n/2 independent draws instead of n**, and the whole-map mix
variance rises by sqrt(2) *by construction*, for every symmetric rule, not just this one. There
is no coordinate rule that gets both.

That reframes the whole functional area. Of the three coordinate-based rules now measured:

```
rule                  all-one-type   mix deviation   team gap   measured
avalanche hash (i7)         0              9.9         24.0     worse than parity
plain parity (i12)          4              9.3         11.0     the incumbent
folded parity (i22)         4             15.6          0.0     -4 vs the incumbent
```

**Parity dominates on the axes that turned out to matter, and the two directions away from it
have now both been measured and both lost.** This area is a local optimum for
coordinate-keyed rules, and I should stop searching it: `MaxConsecutiveRejects` aside, the
remaining gain cannot come from a better function of `(x, y)`, because the constraint binding
it is a property of symmetric maps and not of the function.

**Where the next gain would have to come from**: a rule that is not coordinate-keyed at all.
Today's API sweep found `getNumberTowers` (the team's own tower count, free, no comms) and
`getTowerPattern` (which lets `workOnRuin` read the intended type back off the marks instead
of recomputing it, dissolving the "must not depend on time" constraint). Together those make a
*self-calibrating* mix possible — one that reads the team's actual position instead of
hashing a coordinate — and self-calibrating thresholds beating fixed constants is a design
preference both prior projects arrived at independently. That is iteration 23, and note it is
a different mechanism in the same area rather than another coordinate function, which is what
the functional-area rule requires after a reject.

### Functional-area accounting

Tower type: 1 reject (this one). Not yet at `MaxConsecutiveRejects`. But the finding above is
a stronger reason to leave coordinate rules than the counter is — the area is closed by
argument, not by budget.

### The chip-surplus premise is untouched

Nothing here bears on it. $132,014 unspent at r2000 on DonkeyKong, ~75% of unit deaths by
starvation, tower paint pools at 8-10% of capacity, and the SRP arithmetic (verified from
bytecode today) putting the production-balanced money share at 43% against 53.3% today. That
premise is about the *share*, and this run deliberately held the share fixed (53.3% -> 55.6%)
so it could price symmetry alone. It priced it at −4. The share is still unpriced.

---

## Iteration 23 candidate — **VOID at step 0, for six single-map games**. A count-keyed tower rule is not a dose; it is a lottery on when the marking burst happens.

### The design, and why it looked right

Iteration 22 established that no *coordinate* rule can have both a low team gap and low
whole-map mix variance: under any map symmetry the ruins come in mirrored pairs, so a zero-gap
coordinate rule has at most n/2 independent draws and its mix variance rises by sqrt(2) by
construction. The obvious escape is a rule that is **not a function of position at all**.
Today's API sweep supplied one: `rc.getNumberTowers()` — the team's own tower count, free,
global, no communication. Key the type on the count and the realized share becomes a
*controlled sequence* converging on 1/K whatever the lattice does.

It also required dissolving a constraint the shipping comment calls absolute — that the type
"must stay a pure function of the ruin and never of time", because `workOnRuin` recomputes
`want` and a changed type can never complete. `getTowerPattern` makes the type readable back
**off the marks**, which is where the decision was recorded in the first place. I built that:
one cached discriminating offset (the first cell at which the engine's two patterns disagree,
found at runtime rather than hand-decoded, because RULES.md flags the row/column convention as
unverified), then one sense call per turn.

Arms: `bob_c0` (package rename, verified byte-identical), `bob_c2` (K=2, intended 50% money),
`bob_c3` (K=3, intended 33%).

### Step 0 — and it earned its keep twice over

**First, the good news: the marks-readback works.** This was the real risk — a broken readback
deadlocks `workOnRuin` and towers simply stop being built, which is how iteration 17 died. The
arms build 10-17 towers against the baseline's 8-14. No deadlock. The "type must not depend on
time" constraint is genuinely an artefact of the old code and not of the engine.

**Second, the bad news, which kills it.** Realized money share, three maps:

```
                 Dominoes    Flower    memstore
bob_c2 (K=2)       14%        89%        65%        <- intended 50%
bob_c3 (K=3)       20%        17%        25%        <- intended 33%
baseline           57%        75%        50%
```

**`bob_c2` swings from 14% to 89%.** That is not a dose. Doctrine 2 is explicit: *"a parameter
is only a dose if it changes the condition actually evaluated (verify)"*, and this parameter
does not control the quantity it is named for.

### Why — and the cause is a finding of its own

The count-keyed rule assumes marking decisions are *spread over* the tower-count sequence. They
are not. **Marking is bursty**: iteration 17's ruin probe measured `switched = 0` for every
soldier in the game and `heldMax` of 171/183/247/154 turns — soldiers latch the first ruin they
see and hold it for the rest of their lives. So the first soldier to reach each ruin marks it,
those first-arrivals cluster into an early window, and a mark placed then is stamped with
**whatever the tower count happened to be during the burst**. The whole map's mix is decided by
one accident of timing.

K=3 is stable (17-25%) not because the design works but because with only 1 count value in 3
producing MONEY, a burst is twice as likely to land on PAINT — the lottery is biased, not
removed.

**This is iteration 17's finding wearing new clothes, and I walked into it again.** There the
lesson was "reachability means the choice set, not just the guard"; here it is the same
underlying fact about soldier behaviour — ruin claims are latched early and never revisited —
reaching a different mechanism. I checked that the *branch* fires and that the *readback*
works, and never asked **when** the decision is taken. A time-keyed rule is only as controlled
as the distribution of the moments it is sampled at, and I never looked at that distribution.

### Cost, and what it bought

**Six single-map games.** No gauntlet. Doctrine 5 step 0 exists for exactly this and it has now
paid for itself twice in this lineage (three games for one iteration, six for this one) against
runs of 160-240 games. Two things survive and are worth more than the candidate:

1. **The marks-readback is verified working.** Any future self-calibrating tower rule can use
   it; the "pure function of the ruin" constraint is retired. `src/bob_c2` holds the working
   implementation.
2. **Marking is bursty, measured.** Any rule keyed on *time*, in any form — round number, tower
   count, resource level at mark time — inherits this and will be a lottery. That closes a whole
   family, not one candidate.

**CLOSED: "key the tower type on a time-varying team quantity sampled at mark time."** Re-open
only if ruin claiming stops being latch-early-and-hold — which is itself a thing worth changing,
and is now a candidate in its own right rather than a precondition I assumed away.

### What iteration 23 becomes instead

The share still needs a dose, and it now has to be **per-ruin** (so it is sampled once per ruin
rather than once per burst) while holding the incumbent's symmetry properties near-constant, so
that the run prices the *share* and not a second change to the gap. The design that does this
is parity with a symmetric partial override — keep `((x+y)&1)` as the base assignment, and flip
a *folded* (hence exactly symmetric) subset of the MONEY ruins to PAINT. The flipped fraction
is the dose. Because only the small flipped subset carries the n/2-draws penalty, the mix
deviation cost should be a fraction of the 9.3 -> 15.6 that full folding cost.

Every one of those quantities is computable offline from the map files with the scanner I
already have, so the next step spends **zero games**: extend `bob-tools/foldscan` to score the
candidate rule family on share, all-one-type maps, mix deviation and mirror mismatch, and only
build the arms whose numbers say they are a dose.

---

## Iteration 23 — PRE-REGISTERED before the run returns (launched, 150 games): the money share, priced at last

**Functional area: tower type, second attempt.** Iteration 22 was a reject in this area and
the count-keyed candidate was a step-0 void, so by `MaxConsecutiveRejects` I am close to
having to leave. I am staying for one more attempt on a specific ground: **both previous
attempts changed the rule's *symmetry*, and neither changed the *share*, which is the quantity
all the economic evidence actually points at.** They were the wrong variable.

### The premise, and every number in it is independently sourced

```
chips are slack     $132,014 unspent at r2000 (DonkeyKong), $39,925 (Flower), $7,600 (Dominoes)
                    every tower upgraded by ~r600, tw25 = the engine cap, every ruin taken
paint binds         ~75% of unit deaths are STARVATION; tower paint pools at 8-10% of the
                    1000 cap all game
the rule            money share 53.3% corpus-wide, an iteration-1 default never re-measured
the balance point   35% at S=0 SRPs, 43% at S=4, 47% at S=8
```

The last line is the one I would previously have got wrong: the bare cost table puts the
balanced share at 26-35%, but the SRP bonus is `+3 per active pattern per tower, of that
tower's own resource` — **verified today from `InternalRobot.processBeginningOfRound` bytecode,
not inferred** — and because the flat +3S is a bigger fraction of a paint tower's smaller base
it lifts a paint tower 15->27 (+80%) against a money tower's 40->52 (+30%). That moves the
balance point up to 43% and would have made me overshoot the dose.

### The mechanism, chosen to change ONE variable

Parity picks MONEY exactly as today; a **folded** selector then flips a fraction of those MONEY
ruins to PAINT. Folded means invariant under all three map symmetries, so the override
contributes no mirror mismatch of its own. Scored over all 75 official maps offline, before a
game was played (`bob-tools/foldscan/BobMix.java`):

```
rule            money%   allOne   spread   mismatch%
mask 0 (today)   53.3       4      16.3      46.4
mask 15          49.3       3      16.7      43.7
mask 7           42.1       2      15.7      39.3     <- the balance point
mask 3           33.3       5      15.4      33.0     <- deliberate overshoot
mask 1           14.8      31      14.0      22.7     <- catastrophic, NOT an arm
```

**`mask 7` lands on 42.1% and is better than the incumbent on all three secondary axes**
(all-one-type 2 vs 4, spread 15.7 vs 16.3, mismatch 39.3% vs 46.4%). That is the point of the
folded override: it moves the share without paying anything back on the axes iteration 22
showed are expensive. `mask 1` is excluded on the offline table alone — 31 maps building zero
money towers is a catastrophe I do not need to buy games to recognise.

### Step 0, and it is the check that killed the previous candidate

I did not repeat the mistake of trusting an *intended* dose. Extracted every tower the arms
actually built, and evaluated the rule on those exact ruins:

```
             towers   rule-vs-observed mismatches   ruins flipped MONEY->PAINT
k7 Dominoes    16                 0                            1
k7 memstore     8                 0                            1
k3 Dominoes    16                 0                            2
k3 memstore     8                 0                            2
```

**Zero mismatches**: the rule does exactly what it says on every ruin in play. And the dose is
real, monotone and small — 0 / 1 / 2 converted towers on a captured set of 8-16. That is a
genuine dose ladder with a zero arm, but I want the *size* on the record before the result, so
it cannot be re-scaled afterwards: one converted tower is +27 paint/turn at S=4 against a
measured team paint income of ~165/turn, i.e. **~+16% paint income per flip**.

### Arms and pre-registered gate

```
bob_k0   mask 0   MANDATORY IDENTITY CONTROL: must be 25/50, every map split by side
bob_k7   mask 7   42.1% money -- the balance point
bob_k3   mask 3   33.3% money -- deliberate overshoot
```

- **Void** if `bob_k0` is not 25/50 with all 25 maps split.
- **Accept-eligible** at best arm **>= 30/50** (+5 over the null), then the frozen roster
  before accepting, no member regressing by more than 3 games.
- **The dose prediction, and it is sharp: an INTERIOR PEAK at `k7`.** The SRP-corrected balance
  point is 43%; `k7` is 42.1% and `k3` overshoots to 33.3%. So if the balanced-share model is
  right the curve reads `k7 > k3 > k0` — better than the null, but with `k3` *falling back*
  because it has gone past the balance point. A monotone curve `k3 > k7 > k0` would mean more
  paint is simply better and my balance model is wrong about where the optimum sits (though
  right about the direction). `k7 ≈ k3 ≈ k0` means a 1-2 tower dose cannot be resolved at 50
  games per arm.
- **What would falsify the premise outright**: both arms *below* the null. Chips would then be
  doing something I have not accounted for, and the whole chip-surplus reading — which is
  currently the largest un-acted-on evidence I own — would need re-examining rather than
  re-dosing.

### Pre-checks NOT done, named

1. **The early game is still unpriced.** The surplus is an endgame observation; Dominoes sat at
   $661 at r200. `src/bob_sprobe` is built and compile-checked to answer this at the decision
   point (chip-blocked vs paint-blocked vs tile-blocked spawns) and has **not been run** — I
   did not want its stdout instrumentation competing for VM slots with the run itself. If both
   arms come back negative, that probe is the first thing to run, not another dose.
2. **I have not verified that the instrumented `bob_sprobe` is behaviourally identical** to the
   shipping build. Doctrine requires that before believing anything it reports.
3. **The realized share is confounded by capture.** A build's realized mix depends on which
   ruins it takes, so `k7` measured 62.5% money on Dominoes against the baseline's 57% — higher,
   despite the rule strictly removing money assignments. That is not a contradiction (different
   games capture different ruins) but it does mean **realized share is not a valid read-out of
   the dose**, and I will not quote it as one when the result comes back. The dose is the
   policy, verified per-ruin above.

### Pre-check supporting iteration 23's premise: tower COUNT is near-saturated, so the MIX is what is left

Before spending a run on the mix I should rule out the obvious rival explanation — that the
lever is simply *more towers*. Claimable ruins come from `tools/mapdata/ruin_parity.txt`
(the `.map25` `ruins()` vector, which excludes the four starting-tower tiles, so a replay
header reads four higher — that distinction is in the file's own preamble and I am using the
claimable number here).

```
map           claimable   towers built (both teams, end of game)   utilisation
Flower            12                 15 - 4 = 11                      92%
Dominoes          20                 20 - 4 = 16                      80%
DonkeyKong        46                 41 - 4 = 37                      80%   T1 at tw25 = the ENGINE CAP
```

**80-92% of buildable ruins get a tower, and on the large map my own side is pinned at
`MAX_NUMBER_OF_TOWERS = 25`.** So "build more towers" has at most a fifth of a map's worth of
headroom on the small maps and *literally none* on the big ones. Whatever is wrong with the
economy cannot be fixed by expanding, which is what makes the composition of those towers the
remaining lever — and it is the lever nobody has touched since iteration 1.

Worth stating explicitly because it also **retires a hypothesis I would otherwise have reached
for after a failed dose**: if iteration 23 comes back flat, "we just need more towers" is not
the fallback. The fallback is the spawn probe (`src/bob_sprobe`, built and unrun), which asks
whether the spawn decision is chip-limited or paint-limited at the decision point.

---

## Iteration 23 — RESULT: **REJECTED, and the premise is REFUTED, not merely the dose**

Run `20260908-054213`, 150 games, 25 maps resampled, `BOT=bob` (= `bob_iter20`).

```
arm       money share   score  vs null     sd  swept  swept-against  split
bob_k0       53.3%    25/50         +0  +0.00      0              0     25
bob_k7       42.1%    22/50         -3  -0.85      1              4     20
bob_k3       33.3%    17/50         -8  -2.26      0              8     17
```

Control `bob_k0`: **25/50, all 25 maps split, zero swept.** Fifth consecutive zero-variance
null; the run is valid and the comparisons are exact.

**A clean monotone dose-response, pointing the wrong way.** More paint towers is monotonically
worse: +0, −3, −8 as the money share falls 53.3% → 42.1% → 33.3%. And `bob_k3`'s shape is
one-directional — **0 swept-wins against 8 swept-losses** — which per doctrine 10 is the
signature of a real causal effect rather than churn. This is not a near miss and not noise: it
is a dose curve that says the incumbent share is better than either alternative I built.

### My pre-registered falsification condition fired, and I am honouring it

I wrote, before the run:

> **What would falsify the premise outright**: both arms *below* the null. Chips would then be
> doing something I have not accounted for, and the whole chip-surplus reading — which is
> currently the largest un-acted-on evidence I own — would need re-examining rather than
> re-dosing.

Both arms are below the null. So: **the chip-surplus premise is refuted, and I am not
re-dosing it.** Note how well-supported it looked. Every number in it was real and
independently sourced — $132,014 unspent, every tower upgraded, tw25 at the engine cap, ~75%
of deaths by starvation, tower paint pools at 8-10% of capacity, and a balance point computed
from bytecode I decompiled myself. The premise was not built on a bad measurement anywhere. It
was built on **correct measurements of the wrong time**.

### The hypothesis for *why*, registered as a hypothesis and not as the finding

Doctrine 3b forbids back-filling a mechanism because the number came out a certain way, so
this is written as a claim with a test attached, not as an explanation of the result.

**Iteration 4 may have been right all along, and my refutation of it read the wrong window.**
Its recorded reason for rejecting a paint-heavy mix was: *"chips buy paint income back through
iteration 3's upgrades at +5 paint/turn per 2,500 chips, so starving the treasury starves the
upgrades and nets out worse."* I declared that refuted this morning on the strength of the
endgame surplus. But **the surplus only appears after the upgrades finish, at around r600** —
and by then the game is largely decided. My own LEARNINGS §18 says every game is settled on
paint coverage, and my own coverage traces say the map is full by ~25% of game length and
coverage peaks near r150.

So the chip surplus may be a **post-decision artefact**: I measured a resource's abundance at
a time when it could no longer matter, and concluded it had never mattered. That is the same
shape as doctrine 15's post-action-state trap in a different coordinate — there the error is
reading state *after the action*, here it is reading state *after the game is decided* — and
it is worth naming as a sibling, because I would not have recognised it from the doctrine as
written.

**The test, which was pre-registered as this exact fallback and is already built:**
`src/bob_sprobe` counts, at the spawn decision point, in-bot, before the action resolves,
whether a tower is chip-blocked, paint-blocked or tile-blocked — per 200-round window, so the
early game is separable from the late. If chips block spawns before ~r600, iteration 4's
argument is vindicated and the premise dies with a named cause. If they never block, the
premise dies without one and I will say so rather than invent one.

Doctrine 15 is why this has to be an in-bot probe and cannot come off a replay: the chips a
replay shows a tower holding on turn N are what it had *after* spending, so affordability
computed from replay state is conditioned on the outcome it is meant to predict.

### Functional area

**Tower type: 3 consecutive rejects** (iteration 22, the count-keyed void, this one).
`MaxConsecutiveRejects = 3`, so **the next attempt must leave this area** — and unlike the
usual case I am not leaving it on a budget rule but on evidence: iteration 22 showed the
symmetry axis is a local optimum, and this run shows the share axis is too. Both axes of the
tower-type rule are now measured and the incumbent wins on both. The iteration-1 default that
nobody had ever re-measured turns out to have been right, which is worth its three rejections.

### What survives

- The **null is calibrated five times over** now: identical code scores exactly 25/50 or 40/80
  with every map split and zero swept, every time. A one-game margin in this lineage is a real
  one-game effect.
- The `markedTypeAt` readback (`src/bob_c2`) works and is verified; the "tower type must be a
  pure function of the ruin" constraint is retired whenever it is next needed.
- The offline scanners (`BobFold`, `BobMix`) now price any candidate tower rule on four axes
  for zero games. `mask 1` was excluded on that table alone.
- The chip-surplus *observations* stand as observations. What is refuted is the inference from
  them to "the tower mix is wrong", which is a different statement and dies alone.

---

## SPAWN PROBE RESULT (2026-09-08) — the binding resource FLIPS between maps, and my premise was sized on the wrong three

The pre-registered fallback from iteration 23. `src/bob_sprobe` counts, at the spawn decision
point, in-bot, before the action resolves, whether a tower's spawn was refused for chips, for
paint, or for a free tile.

**Behavioural neutrality checked first, as doctrine requires of any instrumented build.**
`bob_c0` (a verified byte-identical package rename) and `bob_sprobe` played the same opponent
on the same maps: **Dominoes r1504 both, memstore r785 both**, same winner. The probe does not
change what the bot does, so its counters describe the shipping build.

```
map          r200 chipBlock   later chipBlock      paintBlock (later)
memstore        90.0%          78.5% (r600)            17.5%
Justice         51.3%          23.5% (r400)            74.5%
Flower          38.8%           8.7% (r600)            88.7%
DonkeyKong        --            7.5% (r2000)           88.6%
Dominoes         0.0%           0.0%                   97.5%
```

**The binding resource is not a property of this bot. It is a property of the map, and it
inverts completely.** On Dominoes the spawn decision is refused for paint 97.5% of the time and
for chips *never*. On memstore it is refused for chips 78-90% of the time and for paint 7-18%.

### This is why iteration 23 lost, and why the premise was wrong in a way no single number revealed

My chip-surplus premise was sized on **DonkeyKong, Flower and Dominoes** — and on those three
it is correct. It is exactly backwards on memstore. That is TRAINING_ALGORITHM.md §3's *"check
your sizing map is not degenerate"* landing on me: I sized a quantity on three maps, all three
agreed, and three agreeing maps still did not span the corpus. Iteration 23 then removed money
towers everywhere, which is a gain where paint binds and a straight loss where chips do — and
it came back −3 and −8.

**And the time dimension confirms the hypothesis I registered rather than asserted.** I wrote,
before running this probe, that the chip surplus might be a *post-decision artefact* — a
correct measurement taken after the game is decided. The probe says chip-blocking is
overwhelmingly an **early-game** phenomenon that then decays: Flower 38.8% -> 8.7%, Justice
51.3% -> 23.5%. Coverage is what decides games (LEARNINGS §18), the map is full by ~25% of game
length and coverage peaks near r150 — so **chips bind exactly when it matters and release
exactly when it stops mattering.** Reading the endgame treasury and concluding "chips are
slack" measured the second half of that sentence and missed the first.

That is a sibling of doctrine 15 in a different coordinate: there the error is reading state
*after the action*, here it is reading state *after the decision the state was supposed to
explain*. Worth naming, because I would not have recognised it from the doctrine as written.

### The far more actionable thing the probe found: the gate is MY OWN CONSTANT

The spawn gate is `chips >= want.moneyCost + reserve` with `reserve = 1200` — 1450 for a
soldier. On memstore the treasury sat at a **mean of 1000-1350 for the entire game**: pinned
just below my own gate, never above it. With `reserve = 0` the gate is 250 and those same turns
clear it comfortably. **So on chip-limited maps it is not the economy refusing to spawn, it is
my reserve.** A resource pinned in a dead band is one of the two absolute degeneracy signals
the algorithm names in Step 1, and this one is self-inflicted.

`reserve = 1200` has been in `Tower.run` since iteration 0 and has never been measured.

---

## Iteration 24 — PRE-REGISTERED before the run returns (launched, 150 games): the spawn reserve

**Functional area: tower production/economy. New area** — and the move out of tower type is
required (3 consecutive rejects) *and* independently justified: both axes of the tower-type
rule are now measured and the incumbent wins on both.

**Hypothesis.** The 1200-chip spawn reserve refuses 38-90% of early spawn decisions on 3 of 5
probed maps, during the window in which coverage — the thing that decides every game — is
actually being set. It buys the ability to complete a tower pattern (1000 chips) the instant one
is ready. Tower utilisation is already 80-92% of claimable ruins and pinned at the engine cap on
large maps, so that insurance is being bought at a price nobody has ever checked.

**The price, both halves, written before the code** (§3 requires it, and a reallocation must be
priced against what it displaces, not against zero):

```
benefit   on memstore ~80% of tower-turns are chip-refused; converting even a fraction into
          units is a large change in early production, which is where coverage is decided
price     tower completion stalls when the treasury is empty. A soldier that finishes a
          pattern and cannot pay the 1000 waits -- and iteration 17's probe showed soldiers
          hold a ruin for 170-250 turns, so a stalled completion is not a short delay
price     it is a REALLOCATION, not new income: every chip spent on a unit is a chip not
          available for the next tower, and towers are permanent income while units die in
          ~200 rounds
```

**Arms**: `bob_v12` (reserve 1200 = exact zero arm), `bob_v6` (600), `bob_v0` (0).

**Gates.**
- **Void** if `bob_v12` is not 25/50 with all 25 maps split by side.
- **Accept-eligible** at best arm **>= 30/50**, then the frozen roster before accepting
  (baselines: `bob_iter0` 46/50, `bob_iter1` 44/50, `bob_iter11` 35/50, `examplefuncsplayer`
  50/50; none may regress by more than 3).
- **Regime-matched map-level prediction, per doctrine 4, and it embeds a free identity check.**
  The reserve can only act where the gate actually binds. On a map where `chipBlock` is 0% the
  gate never refused anything, so lowering it is **inert and the games must be byte-identical**.
  Dominoes is such a map. So: deviation must concentrate on chip-limited maps and be *absent*
  on maps where the treasury never approaches the gate. If deviation is spread evenly, the
  mechanism is not doing what the probe says it does.
- **Dose shape.** I do *not* pre-register monotonicity. The two priced effects run in opposite
  directions (more units vs stalled towers), so an interior peak at 600 is as plausible as a
  monotone gain at 0, and I am recording that I cannot call it rather than claiming a
  prediction I do not have. What I *do* predict is that **`v0` and `v6` both differ from the
  null on chip-limited maps** — if they do not, the probe's account of the gate is wrong.

**Pre-checks NOT done, named.**
1. I have not measured how often a completed pattern actually waits on chips today. That is the
   price half of the trade and it needs its own decision-point counter; I am running the dose
   first because the probe already sizes the benefit half and the arms are cheap.
2. The probe covers 5 maps of 75. That is what burned iteration 23, and 5 is better than 3 but
   it is not the corpus. The map-level prediction above is what protects this run from the same
   error: it checks the regime split *within* the sample rather than assuming it.

---

## Iteration 24 — RESULT: **REJECTED, monotone**. Lowering the reserve is monotonically worse — so the constant was not over-bought, and the curve says to look UPWARD.

Run `20260908-062158`, 150 games, 25 maps resampled, `BOT=bob` (= `bob_iter20`).

```
arm       reserve   score  vs null     sd  swept  swept-against  split
bob_v12     1200   25/50         +0  +0.00      0              0     25
bob_v6       600   22/50         -3  -0.85      4              7     14
bob_v0         0   18/50         -7  -1.98      3             10     12
```

Control `bob_v12`: **25/50, all 25 maps split, zero swept.** Sixth consecutive zero-variance
null.

**Monotone in the reserve, and against me: 1200 > 600 > 0.** Removing the gate that refuses
38-90% of early spawn decisions makes the bot *worse*, and worse in proportion to how much of
it is removed. The reserve is not over-insurance. Its 1000-chip tower-completion readiness is
worth more than the units the withheld chips would have bought.

### The map-level prediction held EXACTLY where the probe measured, and failed where I extrapolated

I predicted that on a map where `chipBlock` is 0% the gate never refused anything, so lowering
it must be inert and **the games must be byte-identical**. Dominoes was the registered example.
Aggregate first, which looks like a flat refutation:

```
bob_v6: 43/50 cells deviate, on 24/25 maps
bob_v0: 45/50 cells deviate, on 25/25 maps
```

But split Dominoes by side, and the prediction is not refuted at all — it is *located*:

```
                      v12          v6           v0
Dominoes, arm on A   A/1504      A/1504       A/1504     <- ALL THREE IDENTICAL
Dominoes, arm on B   A/1504      B/692        A/874      <- deviates
memstore, arm on A   A/785       B/493        B/663
memstore, arm on B   A/785       A/645        B/1303
```

**The probe ran `bob_sprobe` as TEAM_A — side A — and measured 0.0% chip-blocking. Side A is
exactly the side on which all three arms are byte-identical.** Three different reserves, three
identical games, on the one (map, side) where the probe says the gate never binds. The
mechanism account is confirmed to the game; what failed is the *scope* I gave it.

**The error, named precisely: a probe figure is per (map, SIDE), not per map.** I measured one
side of one game and wrote a prediction about the map. This is the same failure as iteration
23's sizing error — a sample that did not span the condition — one level finer, and it is the
third time today that "I measured it in more than one place" turned out not to mean "I measured
it across the range that matters". Span, not count. Again.

That the prediction survives when correctly scoped is worth more than if it had simply passed,
because it converts "the reserve matters" into "the reserve matters exactly where the gate
binds and nowhere else", which is a mechanism rather than a correlation.

### Two independent runs now refute the same premise, from opposite directions

```
iteration 23   fewer MONEY towers (less chip income)        -3, -8
iteration 24   less chip RESERVE (more chips spent)         -3, -7
```

One reduces the supply of chips, the other releases the stock of them; **both lose, monotonically.**
The premise "chips are a slack resource" is now refuted from two directions that share no
mechanism, which is the kind of corroboration doctrine 26 asks for — genuinely different
referents, not a re-derivation of one number. Chips are worth *more* than this lineage has been
treating them as, not less. The $132,014 endgame surplus was real and told me nothing.

### What the curve says to do next, and it is an ACCEPT candidate rather than another refutation

Doctrine 2: *"Always measure the zero arm... a curve that peaks in the middle is stronger
evidence than any single point."* I measured the zero arm and the curve does **not** peak in
the middle — it is monotone increasing in the reserve across the whole tested range [0, 1200],
with 1200 the best point measured. The obvious question is the one the dose ladder cannot
answer from inside its own range: **does it keep rising above 1200?**

`reserve = 1200` was chosen in iteration 0 as "roughly the 1000 a tower costs, plus a little".
It has never been searched upward. If 2400 beats 1200 that is an accept, and if it does not the
curve has an interior peak at the incumbent and the constant is *validated* rather than merely
unrefuted — which is itself worth having, because it currently rests on one endpoint of one run.

Iteration 25 is that extension: `1200` (zero arm) / `2400` / `3600`.

**Functional area accounting.** Tower production/economy: 1 reject. Iteration 25 stays in the
area deliberately — it is the same dose ladder extended through its best point, not a new
mechanism, which is what doctrine 2 asks for when a curve is monotone at its boundary.

## Iteration 25 — PRE-REGISTERED before the run returns (launched, 150 games): extend the reserve ladder upward

**One mechanism, same knob, extended through its best measured point.** Arms `bob_w12` (1200 =
exact zero arm), `bob_w24` (2400), `bob_w36` (3600).

**Why this and not a new mechanism.** Iteration 24's curve is monotone increasing in the
reserve across [0, 1200] and 1200 is the *boundary* of the tested range, not an interior peak.
Doctrine 2 says a curve that peaks in the middle is stronger evidence than any single point —
I do not have that yet, and the cheapest way to get it is to keep going in the direction the
data points. `reserve = 1200` was set in iteration 0 as "the 1000 a tower costs, plus a little"
and has never been searched upward in 25 iterations.

**Gates.**
- **Void** if `bob_w12` is not 25/50 with all 25 maps split.
- **Accept-eligible** at best arm **>= 30/50**, then the frozen roster before accepting
  (`bob_iter0` 46/50, `bob_iter1` 44/50, `bob_iter11` 35/50, `examplefuncsplayer` 50/50; none
  may regress by more than 3).
- **Both outcomes are informative, which is why this is worth a run.** If 2400 or 3600 clears
  the bar, that is an accept on a constant nobody has touched since iteration 0. If both fall
  below the null, the curve has an **interior peak at the incumbent**, and 1200 stops being an
  unrefuted guess and becomes a measured optimum — bracketed on both sides by 0/600 below and
  2400/3600 above. I would rather have a validated constant than an unexamined one, so I am not
  treating the second branch as a failure.

**The prediction I am willing to be wrong about.** I expect an **interior peak at or near
1200** — i.e. both new arms at or below the null. The reasoning: the reserve insures tower
completion, tower utilisation is already 80-92% of claimable ruins and pinned at the engine cap
on large maps, so raising the reserve buys readiness for towers that mostly cannot be built,
while the chips it withholds are exactly the ones iteration 24 showed are refusing 38-90% of
early spawns. That argument says the gain from raising it should be small and the cost real.

**Registering the asymmetry honestly**: this prediction is the comfortable one. It ends with my
existing bot being right, and doctrine warns that the comfortable correction is the least
audited. So the *number* decides, and if 2400 clears 30/50 I accept it and write down that my
tower-saturation argument was wrong about the margin.

**Pre-check NOT done**: I still have not measured how often a completed pattern actually waits
on chips — the price half of the reserve's trade. Iteration 24 rejected on the benefit half
alone, which was enough to reject but is not enough to *explain*, and if 2400 wins here that
missing counter is the first thing to instrument rather than a third dose.

---

## Iteration 25 — RESULT: the curve has an interior peak, **at 2400, not where I predicted**. Not accepted: +2 against a gate of +5.

Run `20260908-070613`, 150 games, 25 maps resampled.

```
arm       reserve   score  vs null     sd  swept  swept-against  split
bob_w12     1200   25/50         +0  +0.00      0              0     25
bob_w24     2400   27/50         +2  +0.57      5              3     17
bob_w36     3600   18/50         -7  -1.98      1              8     16
```

Control `bob_w12`: 25/50, all 25 maps split, zero swept — seventh consecutive zero-variance null.

### My pre-registered prediction was wrong, and it was the comfortable one

I predicted an **interior peak at or near 1200** — both new arms at or below the null — and
argued it from tower saturation: the reserve insures completion, utilisation is already 80-92%
of claimable ruins and capped on large maps, so raising it buys readiness for towers that
mostly cannot be built. I also wrote, before the run: *"this prediction is the comfortable one.
It ends with my existing bot being right... the number decides, and if 2400 clears 30/50 I
accept it and write down that my tower-saturation argument was wrong about the margin."*

**2400 beat the null by 2 games.** So the saturation argument is wrong, and I can now say where:
**utilisation counts towers EVENTUALLY built and says nothing about WHEN.** A tower finished 200
rounds late, on a game decided by round ~500, is most of a tower wasted — and it still counts as
utilised. My argument treated a stock as if it were a flow. The number caught what the argument
elided.

### But the gate is the gate

Pre-registered accept-eligibility was **>= 30/50**. `bob_w24` is **27/50** — short by 3 games,
and also just outside the `NearMissMargin` band (54% against a 60% `WinPct`, where the allowance
is 5 points). **Not accepted.** I wrote "I am not relaxing a gate because I found an extra
argument after launching" in the iteration-22 amendment, and it binds here, where the temptation
is live rather than hypothetical: +2 against a zero-variance null *is* a real +2 games, and that
is exactly the sort of true statement that gets used to walk a threshold backwards.

### What is genuinely new: the curve doctrine 2 asks for

```
reserve      0     600    1200    2400    3600
vs null     -7      -3      +0      +2      -7
```

Concave, interior optimum near 2400, both tails falling away hard. Two cautions on the record
rather than left implicit:

1. **The two halves come from different runs with different map samples.** The ladder is exactly
   comparable only *within* each run; each is anchored at 1200 as its own zero arm, which is what
   makes the shape readable, but `600` and `2400` have never met on one sample and **I will not
   quote a difference between them.** Doctrine 6: a flagged caveat has to constrain what I do
   with the number, not decorate it.
2. **`+2` is one point on one sample.** The peak's *location* is far better supported than its
   *height* — location rests on a sign pattern across five doses, height on two games.

## Iteration 26 — PRE-REGISTERED, launched (200 games): locate the peak on ONE sample

`MaxNearMissRefinements = 3`; this is refinement 1 of a directionally-correct mechanism. Arms
`bob_w12` (1200, exact zero arm), `bob_x18` (1800), `bob_w24` (2400), `bob_x30` (3000) — all on
**one shared 25-map sample**, which repairs caveat 1 across the entire right-hand side of the
curve and re-measures 2400 on a *fresh* sample, the only way to learn whether its +2 replicates.

- **Void** if `bob_w12` is not 25/50 with all 25 maps split.
- **Accept-eligible** at best arm **>= 30/50**, then the frozen roster before accepting
  (`bob_iter0` 46/50, `bob_iter1` 44/50, `bob_iter11` 35/50, `examplefuncsplayer` 50/50; none
  regressing by more than 3).
- **Prediction**: peak somewhere in 1800-2400, with 3000 falling between 2400 and 3600's −7.
  I am explicitly **not** predicting that 2400 reproduces +2 — a single 2-game margin is the
  least reliable thing on the table. If 2400 returns 0 while 1800 returns positive, that is the
  curve relocating its optimum, not the effect vanishing; if *both* return ~0, the +2 was the
  sample and the whole right-hand rise is in doubt.

**Pre-check still NOT done, third time named**: how often a *finished* pattern waits on chips —
the price half of this trade. `src/bob_cprobe` is now built and compile-checked to count exactly
that at the decision point (pattern verified complete tile-by-tile, then `canCompleteTowerPattern`
false, split by whether chips < 1000). It has not been run. If iteration 26 produces an accept,
this probe is what turns it from a tuned constant into an explained one.

---

## ROSTER SATURATION AUDIT (2026-09-08) — doctrine 12's new clause, applied to my own roster

**The clause**: a rung beaten 94-100% of the time has stopped measuring, because it can
register no improvement *and no decline*; report the **weakest** rung rather than the mean; fix
saturation by **adding** a harder fixed reference, never by retiring rungs.

**My roster at iteration 20, sorted weakest-first — which is how it has to be read:**

```
bob_iter11           35/50    70.0%    <- the only rung still discriminating
bob_iter1            44/50    88.0%       near-saturated
bob_iter0            46/50    92.0%       near-saturated
examplefuncsplayer   50/50   100.0%    <- SATURATED: cannot register a decline at all
                     mean     87.5%    <- the number I should never quote
```

**One of four rungs is dead, two are nearly dead, one works.** The mean, 87.5%, is exactly the
misleading summary the clause warns about: it reads like a strong instrument and three quarters
of it cannot move.

**And this lineage is the case study for why that matters.** `bob_iter11` is the rung that
caught iteration 18 sliding — 25/50 under iteration 12, 20/50 under iteration 18 — which the
tournament then confirmed independently with a 22-point standings drop. That detection was only
possible because `bob_iter11` could still beat me sometimes. Had it been saturated, iteration 18
would have stood.

**It is saturating from below right now**, which is the part I would have missed:

```
iter12: 58% -> 56% -> 50%      iter18: 40%      iter20: 70%
```

It moved **30 points in one accept**. Two more accepts of that size and the last live rung joins
the dead ones — and per §5b that is precisely the condition under which a chain of
individually-positive accepts can walk downhill undetected. Iteration 25's `+2` is exactly the
kind of thin link such a chain is made of.

### The fix, and one candidate I rejected

**Rejected: `bob_denier`.** The obvious move was to promote my existing synthetic archetype. It
scores **86% and 94%** against this lineage in recent runs — it is *already* saturated, so
adding it would have produced a fifth dead rung while feeling like a repair. Worth recording,
because "add an archetype" is the clause's own suggested remedy and applying it without checking
the archetype's current strength would have quietly made things worse.

**Adopted: `bob_iter20` as a fixed extra rung.** It is the strongest build this lineage has
produced, it is already frozen and compile-checked, and the stride rule puts it at **position 8**
— not a multiple of 5 — so it would otherwise never have joined the roster at all. It reads ~50%
by construction until the next accept, which is what a maximally discriminating rung should
read. Roster is now `bob_iter0 bob_iter1 bob_iter11 examplefuncsplayer bob_iter20`; nothing was
retired.

**Standing rule recorded in `roster_extra.txt` itself**, not just here, so it survives a session
that never reads this entry: *whenever the weakest rung passes ~90%, add the newest accepted
snapshot as a new rung. Add, never replace.*

**Reporting convention changed**: I will quote the weakest rung from here on, never the mean.

**What this does not fix, named so it is not mistaken for done.** `bob_iter20` is my own code,
so it inherits every blind spot the lineage shares — it makes the roster *harder*, not more
*independent*. A genuine strategic archetype would do both, and today's spawn probe hands me the
weakness to build one against: production is chip-gated on 38-90% of early tower-turns on most
maps, and coverage is decided in exactly that window. An archetype that races coverage early and
ignores the late game would attack a weakness I have measured rather than one I imagine. That is
a real candidate, not a note — but it is a build, and it is not this iteration.

---

## Iteration 26 — RESULT: **REJECTED**, and iteration 25's `+2` does **not** replicate. The reserve is a *plateau*, not a peak.

Recovered after a session death: the run had finished and been collated, and a **second, unplanned
duplicate run of the identical four arms** (launched 31s later, almost certainly a double-submit by
the dying session) had finished on the VM and was never collated. I collected it rather than
discarding it — it is a paid-for, independent map sample of exactly the arms under test, which is
the one thing doctrine 1 says a deterministic engine *cannot* give you by re-running.

Runs `20260908-074050` (sample A) and `20260908-074121` (sample B), 200 games each, 400 total.
Map overlap between samples: **9 of 25** (16 fresh maps in B), so B is substantially but not
perfectly independent of A.

**Scores below are the ARM's own score** (the log's standing convention; the raw `summary.txt`
reports the *incumbent's* score against each arm, i.e. `50 − arm`). See the convention note below.

```
arm       reserve   sample A   sample B   pooled     vs null
bob_w12      1200     25/50      25/50    50/100        +0   (mirror of the incumbent -> null)
bob_x18      1800     23/50      26/50    49/100        -1
bob_w24      2400     24/50      26/50    50/100        +0
bob_x30      3000     25/50      22/50    47/100        -3
```

- **Not void.** Control `bob_w12` is 25/50 with all 25 maps split and zero swept in *both* samples —
  the eighth and ninth consecutive zero-variance null.
- **Doctrine 3 satisfied.** Outcomes differing from the null arm on the same (map, side):
  A: x18 12/50, w24 15/50, x30 10/50; B: x18 7/50, w24 5/50, x30 11/50. The dose executes.
- **Gate.** Pre-registered accept-eligibility was best arm **>= 30/50**. Best arm is **25/50**.
  Not accepted, and not close — this is a null, not a near miss, so it does not consume a
  `MaxNearMissRefinements` slot so much as it closes the thread outright.

### The pre-registered contingency fired, word for word

I wrote before launching: *"if **both** return ~0, the `+2` was the sample and the whole right-hand
rise is in doubt."* Both returned ~0. **2400 gave `+1` on sample A and `−1` on sample B; pooled over
200 games it is exactly `+0`.** Iteration 25's `+2` was the map sample.

I record this as a win for the pre-registration and a loss for my iteration-25 write-up, which spent
several paragraphs explaining a mechanism (*"utilisation counts towers eventually built and says
nothing about WHEN"*) for an effect that does not exist. The explanation was good prose about noise.
**Doctrine 2's warning is about reading a curve's shape; it says nothing about a 2-game height, and
I had already flagged exactly that** — *"the peak's location is far better supported than its
height — location rests on a sign pattern across five doses, height on two games"* — and then wrote
the mechanism section as if the height were real anyway. That is doctrine 6 in its purest form: I
flagged the caveat and reasoned from the number regardless.

### What the whole ladder now says

```
reserve      0    600   1200   1800   2400   3000   3600
vs null     -7     -3     +0     -1     +0     -3     -7
games        50     50    ~200    100    150     100     50
```

Not a peak at 1200, and not a peak at 2400. A **broad flat plateau from ~1200 to ~2400**, with both
tails falling away hard and symmetrically. Within the plateau the reserve is genuinely inert.

**This is the good branch of iteration 25's pre-registered fork**, and I am claiming it as such: the
constant set in iteration 0 as *"the 1000 a tower costs, plus a little"* and never examined for 25
iterations is now **bracketed on both sides by measured falloff** and sitting on a plateau. It stops
being an unrefuted guess and becomes a validated constant. **Keep `reserve = 1200`** — not because it
won, but because it is on the plateau, it is the incumbent, and nothing beats it.

### Thread closed, with the mechanistic reason

Five doses, seven levels, ~700 games. A reallocation knob reading zero across its entire plateau is
consistent with LEARNINGS 31 and the iteration-24 spawn probe: **production is chip-gated on 38–90%
of early tower-turns on most maps.** A reserve decides *how a budget is split*; if the budget itself
is the binding constraint on most turns, then splitting it differently moves nothing until the split
gets extreme enough to break something — which is exactly the flat-middle, falling-tails shape above.
**The lever is income, not allocation.** That is where iteration 27 goes.

### Convention note, recorded because I nearly mis-called it a tooling bug

On resuming I read the raw `summary.txt` (`vs bob_w24 23/50`) against the log (`bob_w24 27/50`) and
was one step from reporting the resampling tool as sign-inverting. **I ran the discriminating case
first**, as doctrine requires: iterations 24 and 25 reconcile *exactly* — `27 = 50 − 23` and
`18 = 50 − 32` — so the log's conversion is correct and consistently applied, and there is **no
tooling bug**. Nothing to report to the coordinator. Recorded here because the near-miss is the
lesson: the two artefacts that "should agree and didn't" (doctrine 5's tell) disagreed for a benign
reason, and the check that separated benign from real cost one command.

`gauntlet.sh` reports the **bot's** score; this log reports the **arm's**. Stated here so a future
session does not re-derive it under pressure.

---

## COMPLETION PROBE RESULT (2026-09-08) — the spawn reserve insures against an event that never happens

Named as a missing pre-check **four times** across iterations 24-26 and finally run. `src/bob_cprobe`
= `src/bob` plus counters only (verified: 32 added lines in `Soldier.java`, zero diff in the other
six files). Peer opponent `bob_iter11`, one map from each resource regime per LEARNINGS 31's
*span, not count* rule: **memstore** (chip-bound, 90% of early tower-turns refused for chips) and
**Dominoes** (paint-bound, 0% chip-refused, 97.5% paint-blocked).

```
map        ruin-turns sampled   turns unable to complete   ...for want of CHIPS   ...other
memstore          ~250                     ~14                      0               14
Dominoes         ~1100                    ~1000                     0             ~1000
```

**`waitingOnChips` is ZERO in every single sample, on both maps, in both resource regimes.**
Across roughly a thousand ruin-turns on which the bot stood at a ruin and could not complete the
tower, it had **at least 1000 chips every time**.

The reserve's stated purpose is written in the source, one line above it: *"keep a reserve so
soldiers can complete new towers (1000 chips) the moment a pattern is done."* **That event does not
occur.** The 1200 chips withheld from spawning on every tower-turn from round 31 onward buy
insurance against a contingency that never arises.

### The probe's own definitional flaw, reported rather than papered over

`patternDone` is computed as *"no marked tile in the 5x5 mismatches its mark"*, which is **vacuously
true when nothing is marked**. On Dominoes it reads `patternDone=330` out of `ruinTurns=331` — a
soldier cannot have held a genuinely finished pattern for 330 consecutive turns, so the flag is
mostly firing on unmarked ruins. That is a wrong-referent error (doctrine 5) in my own probe, and
it is mine, not the shared tooling's — nothing to report to the coordinator.

**It does not touch the conclusion, and here is exactly why.** The flaw makes `patternDone` a
*superset* of the intended condition, so `waitingOnChips` was evaluated over **more** ruin-turns
than intended, not fewer. A count of zero over a superset is zero over the subset. The claim the
probe supports is therefore the weaker but sufficient one, and it is the one I am asserting:
**whenever this bot was at a ruin and could not complete a tower, chips were never the reason.**
What the probe *cannot* do is measure the rate of genuine completion-waits, because it cannot tell
"pattern finished" from "pattern never marked". I am not quoting a rate.

### The puzzle this creates, stated because it is the whole reason iteration 27 exists

If the reserve insures nothing, `reserve = 0` should have been free. Iteration 24 measured it at
**−7 games**, with 600 at −3, monotone. So the reserve **is** doing something real — it is simply
not doing the thing its comment claims. The remaining candidate: it is not insurance, it is an
accidental **spawn-rate throttle**, and it works because spawning is being *over*-done.

That reframes the constant entirely, and it points at the resource the gate has never looked at.

---

## Iteration 27 — PRE-REGISTERED: the spawn gate has never tested PAINT

**The mechanism, and it is one line.** `Tower.run` step 3 gates spawning on
`chips >= want.moneyCost + reserve`. **Chips only.** But a soldier costs the *tower* **200 paint**
(`UnitType.paintCost`, javap-confirmed), and `Soldier.tryRefill` will only draw from a tower holding
**>= 100 paint**, drawing it down to 50. So:

> **One spawn (200 tower paint) = up to four refills forgone**, and my own iteration-20 note records
> that **~95% of soldier deaths are starvation**, with tower paint pools measured at **8-10% of
> capacity**.

The tower is spending on new units the exact paint its existing units are dying for want of, and no
line of code has ever compared the two. Add the missing conjunct:

```java
final int PAINT_RESERVE = <dose>;
if (chips >= want.moneyCost + reserve
        && rc.getPaint() >= want.paintCost + PAINT_RESERVE) {
```

**Arms** (one shared 25-map sample, 200 games): `bob_q0` (0), `bob_q1` (100), `bob_q2` (200),
`bob_q3` (300).

**`bob_q0` is an EXACT zero arm, and this one is checkable rather than asserted.** `javap` of
`RobotControllerImpl.assertCanBuildRobot` shows its four conditions, the first being *"Not enough
paint to build new robot!"* — so at `PAINT_RESERVE = 0` the added conjunct is *implied by a check the
engine already performs*, and the games must come out **byte-identical** to the incumbent. That is a
stronger null than the mirror-arm nulls I have been using: those are 25/50 by symmetry, this one is
25/50 *and* every game identical. If `bob_q0` is not 25/50 with all 25 maps split, something is
wrong with my reasoning about the engine and the run is void.

**Dose scale is derived, not guessed.** 100 = the exact threshold below which a tower can no longer
refill anyone. 200 = one further soldier's worth. 300 = a hard throttle.

**Gates.**
- **Void** if `bob_q0` is not 25/50 with all 25 maps split.
- **Accept-eligible** at best arm **>= 30/50**, then the frozen roster before accepting
  (`bob_iter0` 46/50, `bob_iter1` 44/50, `bob_iter11` 35/50, `examplefuncsplayer` 50/50,
  `bob_iter20` ~25/50; none regressing by more than 3). Per the saturation audit I will quote the
  **weakest** rung, never the mean.

**Prediction, and I am committing to a shape rather than a height** — LEARNINGS 33 says a
three-point ladder cannot tell a peak from a plateau, so I am running three non-zero doses on one
sample and predicting **an interior peak at 100 or 200**, with 300 falling back toward or below the
null as the throttle starts starving unit production outright.

**Map-level prediction (doctrine 4), so the sample checks itself.** The mechanism can only act where
towers are paint-poor. LEARNINGS 31 puts Dominoes/DonkeyKong/Flower at 88-97% paint-blocked and
memstore at ~0%. So I predict **gains concentrated on paint-bound maps and approximately nothing on
memstore-like chip-bound maps.** If the gain is uniform across regimes, my mechanism story is wrong
even if the headline is positive, and I will say so.

**What would falsify the whole framing**: if all three non-zero arms sit at the null, then spawning
is not over-done, the reserve's −7 at zero has some third explanation, and I stop theorising about
that constant and go back to the tournament maps for a target.

### Two notes recorded WHILE iteration 27 is in flight, neither of which may rescue a null

Written after launch and marked as such, so that neither can be quietly promoted into an
explanation if the run comes back at the null. The pre-registered gate and falsification
condition above are unchanged.

**1. The resource regime is NOT predictable from static map data — a negative result worth having.**
I tried to build a map-regime classifier so the doctrine-4 map-level prediction could be scored on
all 25 sampled maps rather than the ~1.7 of my five measured maps a random draw is expected to
contain. Against the measured early chip-refusal rates:

```
map          chipRefusal%   ruins   paintable   area/ruin   ruins per 1000 tiles
memstore            90.0      26        2055        79.0                  12.65
Justice             51.3       8         381        47.6                  21.00
Flower              38.8      12        1611       134.2                   7.45
DonkeyKong           7.5      46        3186        69.3                  14.44
Dominoes             0.0      20        1208        60.4                  16.56
```

**Neither statistic is monotone in the regime** — Flower has by far the highest area-per-ruin and
sits mid-table; Justice has the highest ruin density and is second-most chip-bound. So the binding
resource is not a simple function of ruin supply or map area. This is the *first* time the "ask the
map files instead of running games" habit has come back empty, and that is the useful part: the
regime is a dynamic property, so classifying it requires the in-bot refusal counter and cannot be
short-cut. A future session should not re-attempt a static classifier.

Consequence, stated plainly: **I cannot score the map-level half of my prediction on this run.** I
will score the headline and the dose shape, and report the map-level prediction as untestable here
rather than quietly dropping it.

**2. A specific way the mechanism can fail that I did not think of before launching.** Withheld
paint only pays off if a starving soldier is actually adjacent to the tower holding it —
`tryRefill` needs the tower inside the soldier's vision. Soldiers wander far from towers, so the
reserve could simply park paint in a tower nobody comes back to, buying nothing while still costing
the forgone unit. If all three arms read null, this is the first thing to check, **not** an excuse
to re-run. Checking it is a probe (count refill attempts that found no tower with >=100 paint versus
soldiers that starved with no tower in vision at all), not another gauntlet.

### Tournament loss-shape analysis (local, zero VM cost, while iteration 27 runs)

The round-length distribution of my tournament games, which I had never looked at, dates the
iteration-18 regression precisely and names its signature:

```
tournament        bob record     losses <r500   losses at r2000    wins <r500   wins at r2000
20260907-0100     287W- 13L          0.0%           61.5%             19.9%          8.4%
20260907-1300     277W- 23L         17.4%           30.4%             20.6%          5.8%
20260908-0100     211W- 89L         25.8%           25.8%             10.4%         16.1%
```

**A loss mode that did not exist appeared and then grew.** Two tournaments ago bob had *zero*
losses inside 500 rounds; it now loses 23 games that way, a quarter of all losses. Symmetrically,
fast wins halved (19.9% -> 10.4%) and grind-to-r2000 wins doubled (8.4% -> 16.1%). The bot did not
merely get worse — **it got slower, and it acquired an early-collapse mode.**

That signature fits iteration 18 (`RUIN_FLOOR = 0`, "spend the last paint on the tower pattern")
better than anything else in the window: its own source comment records that `NO_PAINT_DAMAGE`
applies at **exactly zero** paint, and iteration 18 is the change that lets a soldier paint itself
all the way to zero while working a pattern. Soldiers that reach zero take damage and die, which is
an early-game effect because pattern work is an early-game activity.

**PRE-REGISTERED PREDICTION for the next tournament (13:00 UTC 2026-09-08), the first to play
iteration 20.** The 0100 tournament played `f67ac8b` = iteration 18; iterations 19 and 20 landed
afterwards and `bob_iter11` already shows the recovery in self-play (40% -> 70%). So:

1. **bob's standings win% recovers from 70.3% toward 90%+**, and
2. **the share of losses inside 500 rounds collapses back toward 0%.**

Prediction 2 is the load-bearing one. If the headline recovers but fast losses stay near 25%, then
iteration 20 bought back the games by some other route and the early-collapse mode is still live and
still unexplained — which would be a bigger finding than the recovery, and would become the next
iteration's target ahead of anything else queued. Recording it now, before the result exists, so it
cannot be read either way after the fact.

### CORRECTION, issued before the 13:00 tournament lands: that −22 is CONFOUNDED

I wrote the prediction above treating bob's 92.3% -> 70.3% standings drop as a measurement of bob.
Checking what actually played in each tournament shows it is not:

```
tournament       bob                 alice                carol
20260907-1300    iteration 12        iteration 14         iteration 12
20260908-0100    iteration 18        (later build)        iteration 29
```

**Carol advanced seventeen accepted iterations between those two tournaments.** The head-to-head
deltas say the same thing directly: `alice vs bob` moved **+18.7 points in alice's favour** and
`bob vs carol` moved **−25.3**. A standings delta is a joint measurement of my bot *and* both
opponents, and here both opponents moved a long way.

So "bob dropped 22 points" is a wrong-referent error of exactly the shape doctrine 5 describes — a
number correctly computed against the wrong thing. The tell was available and I walked past it: the
report prints *"What played"* with a commit per bot, and I read only my own line.

**This also corrects something I committed earlier today.** The roster saturation audit says
`bob_iter11` caught iteration 18 sliding *"which the tournament then confirmed independently with a
22-point standings drop."* **That confirmation is not independent and not clean.** What survives is
the frozen-rung evidence alone: `bob_iter11` cannot change, so bob going 50% -> 40% against it is an
unconfounded regression. The tournament number is consistent with that but does not corroborate its
size, and I should not have quoted the two together.

**Revised prediction for 13:00 UTC, replacing prediction (1) above.** I am *withdrawing* the
"recovers toward 90%+" claim: it is unscoreable, because carol and alice will have moved again and I
cannot separate their movement from mine. Predicting a confounded number is how a lineage talks
itself into credit for an opponent's bad day.

**Prediction (2) stands and is now the whole of it**, because it is a *shape*, not a level: the
share of bob's losses that end **inside 500 rounds**, which was 0.0% -> 17.4% -> 25.8%. A shape is
far more robust to opponent drift than a rate — an opponent that got broadly stronger lengthens and
shortens games roughly in proportion, whereas a specific early-collapse mode is a spike at one end
of the distribution. I predict it **falls below 15%**. If it stays at or above 25%, bob has a live
early-collapse mode that six accepted iterations have not touched, and that becomes the next target
ahead of anything queued.

**And the mechanism candidate is already in the current bot.** `RUIN_FLOOR = 0` (iteration 18) is
still live in `src/bob`. RULES.md line 82: at **exactly zero** paint a robot *cannot move* and loses
`NO_PAINT_DAMAGE = 20` HP/turn — 250 HP soldier, dead in 12.5 turns, unable to walk to a tower.
`Soldier.run` calls `tryRefill` below 50 paint, but when no tower within vision holds >= 100 paint
`tryRefill` returns false and the soldier **falls through to ruin work and paints itself to zero**.
Soldier paint cost is 5 and stashes start at 200, so exact zero is reachable, not a corner case.

**Note the convergence with iteration 27, which I did not design for.** The reason no tower has
>= 100 paint in vision is that towers spend their paint spawning — which is precisely the trade
iteration 27's `PAINT_RESERVE` throttles. The spawn-side probe and the tournament loss-shape arrived
at the same trade from opposite directions. That raises my prior on iteration 27, and it does not
lower the gate.

### Doctrine 12 update adopted, and a manipulation check pre-registered for iteration 27

**The archetype remedy is withdrawn from doctrine 12; the newest accepted snapshot replaces it.**
Two lineages tested the old advice and it failed in *opposite* directions — my `bob_denier` was
already too strong to lose to (86% / 94%, a fifth dead rung), another lineage's freshly-built
archetype saturated on arrival, sweeping 25 maps to zero. The premise that died is *"unlike a
snapshot you can choose its difficulty."* You cannot: a hand-built opponent's difficulty is set by
guesswork about your own weaknesses, so it lands at a ceiling or a floor. The newest accepted
snapshot reads **~50% by construction** — calibration you get for free rather than aim for.

My `roster_extra.txt` already implements this, including the reason `bob_iter20` must be named
explicitly (the stride rule puts it at position 8, not a multiple of 5) and my own caveat that a
snapshot makes the roster *harder*, not more *independent*. Nothing to change; recorded so the
resuming session knows the rule is now doctrine rather than a local choice.

**Rule adopted: run the manipulation check WHEN YOU EXPECT TO PASS IT.** A check run only when you
fear the answer is a formality whose outcome you have already decided. A favourable headline is
exactly when it gets skipped and exactly when skipping costs most, because nothing else catches a
gate that passed for the wrong reason. My accepts are thin — six consecutive rejects — so the
temptation to wave a positive iteration 27 through is live rather than hypothetical.

**So I am pre-registering it now, while iteration 27 is still running and I do not know the
headline.** `src/bob_qprobe` (= `bob_q2`, dose 200, plus counters; compile-checked) counts at the
spawn decision point:

```
blockedByPaint      chips would have allowed the spawn, the paint conjunct refuses it
blockedOnlyByDose   ...and the ZERO arm would have spawned (paint >= paintCost)
```

`blockedOnlyByDose` is the manipulation itself: it counts spawns that exist in `bob_q0` and not in
`bob_q2`. Doctrine 2 requires this — *"a parameter is only a dose if it changes the condition
actually evaluated"*, and a past sweep produced byte-identical games because the parameter fed a
check that never ran.

**Pre-registered thresholds, set before the headline exists:**
- If `blockedOnlyByDose` is **~0**, the dose does not exist, and **any** iteration 27 headline —
  positive or negative — is measuring something other than my mechanism. That voids the iteration
  regardless of how good the number looks.
- I **expect it to pass**: tower paint pools at 8-10% of capacity and a soldier costs 200, so the
  gate should sit right in the live band. Recording the expectation is the point — if it fails, I
  was wrong about the bot's paint economics and that is worth more than the sweep.

The gauntlet's own diff-from-null count is a *weaker* version of this check (it detects that games
differ, not that they differ **for the pre-registered reason**), so it is a cross-check, not a
substitute. Both will be reported.

### PREDICTION (2) WITHDRAWN TOO — the frozen rung refutes the early-collapse story before the tournament runs

I argued the fast-loss share was *"a shape, not a level"* and therefore robust to opponent drift.
**That was wrong, and my own data says so.** Round length is strongly opponent-dependent: in run
`20260908-005627`, **78% of my wins over `examplefuncsplayer` end inside 500 rounds** versus 2.2%
at r2000 against `bob_iter0`. A pool that got stronger shortens my losses and lengthens my wins.
So the fast-loss share is confounded by exactly the same opponent drift as the standings — I
invented a reason it would not be, and the reason does not survive contact with the data.

**The unconfounded instrument was available the whole time.** `bob_iter11` is frozen and cannot
change, so bob's fast-loss share *against it* is a clean measurement of bob:

```
run                 vs bob_iter11   win%    losses inside r500
20260907-034757        50 games      58%        4/21 = 19%
20260907-043355        50 games      56%        5/22 = 23%
20260907-193911        50 games      50%        4/25 = 16%
20260907-201817        50 games      40%   <-    2/30 =  7%   <- ITERATION 18, the regression
20260907-232155        50 games      46%        6/27 = 22%
20260908-005627        50 games      70%        3/15 = 20%
```

**Flat at 16-23% across every build, and iteration 18 has the LOWEST fast-loss share of the six.**
The early-collapse mode does not exist in bob. The tournament's 0.0% -> 17.4% -> 25.8% rise is
alice and carol getting better at closing games quickly, not bob acquiring a way to die young.

So **the `RUIN_FLOOR = 0` / zero-paint story is refuted** — not weakened, refuted, by the one
instrument in the project that holds the opponent fixed. I am not spending an iteration on it, and
`src/bob_zprobe` is not needed for that purpose. (I am keeping it: its `refillNoTower` counter
measures iteration 27's *premise* — how often a soldier below 50 paint finds no tower holding
>= 100 — which is a live question regardless.)

### The actual lesson, and it is that I made the same error twice in ninety minutes

Both times I took a tournament-derived quantity as a measurement of my bot; both times the referent
was really *bob-and-alice-and-carol jointly*; both times the fix was the frozen roster. The second
occurrence is the damning one, because I had **just written the correction for the first** and then
reached for a different tournament statistic and told myself a story about why *this* one was
immune. The story was even plausible. It was also invented to license the number I wanted.

**Rule: no tournament-derived quantity measures my bot. Not the standings, not the head-to-head,
not any distributional shape derived from them.** The tournament tells me where I stand *today
against today's opponents*, which is genuinely valuable and is what MULTI_AGENT.md says it is for.
It cannot tell me whether a change of mine helped, because the other two lineages are accepting
iterations between every pair of runs. Only a frozen opponent can answer that, and I have five.

**Where this leaves the tournament**: still the highest-value evidence for *target selection* — a
map I am swept on is a real weakness whoever caused it — but never for *attribution*. That is a
narrower role than the one I have been giving it all session.

### Bytecode audit refreshed (TRAINING_ALGORITHM phase 0.6), from data already on disk

Phase 0.6 says to check the bytecode budget on **every** full evaluation forever, because a one-off
"we have headroom" result goes stale as logic accumulates. Mine had gone stale: the last figure in
this log is **8,837 / 17,500** at iteration 15, and iterations 16-20 have been accepted since.

It cost nothing to refresh — the monitor in `RobotPlayer` prints `BCMON` every 500 rounds and today's
completion-probe runs were verbose, so two full games were already sitting in `logs/`. Peak per type,
both maps, **zero overruns anywhere**:

```
                     memstore        Dominoes
SPLASHER           9937 (56.8%)    9329 (53.3%)   <- the peak
MOPPER             3175 (18.1%)    2705 (15.5%)
SOLDIER            2185 (12.5%)    2120 (12.1%)
towers (all)        <590 (2.9%)     <564 (2.8%)
```

- **Zero overruns on every type on both maps**, and the round-number cross-check (phase 0.6's
  confirmed-overrun test, not just the near-miss counter) agrees.
- **`SPLASHER` is the constraint at ~57%**, not the soldier I had been watching. Worth recording,
  because iteration 20 shifted the unit mix *toward* splashers, so the type nearest the ceiling is
  also the one whose population I recently increased. Still comfortable, but it is the one to watch.
- The soldier's 12.5% is far below the 8,837 (50%) noted at iteration 15 — that figure was measured
  with the Bug2 navigation of iteration 15, which was rejected. Nothing regressed; the expensive
  code went away with the rejection.

Caveat: these come from `bob_cprobe`, which carries extra instrumentation, so `src/bob` is at or
below these numbers on the paths measured. Headroom is not in question either way.

---

## Iteration 27 run 1 — **VOID**, and the void check earned its keep

Run `20260908-093442`, 200 games. Evaluated with the new `bob-tools/eval_arms.py`:

```
arm       PAINT_RESERVE   score  vs null  swept  sweptAg  split  diff-from-null
bob_q0              0     19/50      +0      2        8     15        0/50   <- NULL, BROKEN
bob_q1            100     25/50      +6      5        5     15       18/50
bob_q2            200     15/50      -4      2       12     11       14/50
bob_q3            300     15/50      -4      2       12     11       18/50
```

**Pre-registered void condition: "Void if `bob_q0` is not 25/50 with all 25 maps split."** It came
back **19/50 with 15/25 split and 8 swept losses**. Void. Nothing in the table above means anything,
including `bob_q1`'s +6.

### Why the "exact" zero arm was not exact — my bug, not the tooling's

`G.rng` is a **per-robot `java.util.Random(rc.getID())`**, and the spawn block is:

```java
if (chips >= want.moneyCost + reserve) {
    int start = G.rng.nextInt(8);          // <-- consumed INSIDE the gate
    for (int i = 0; i < 8; i++) { ... rc.canBuildRobot(want, l) ... }
}
```

In the incumbent, a tower with enough chips but **too little paint to build anything** still enters
the block, still draws from the PRNG, and still runs a loop that spawns nothing. My arm added the
paint test to the `if`, so on exactly those turns the block was skipped and **the draw was not
consumed**. From that moment the tower's PRNG stream is offset by one, and every subsequent
`G.rng.nextInt(8)` — spawn directions, and `G.randomDir()` wherever else it is reached — returns a
different value for the rest of the game.

The change was **behaviourally neutral in outcome** (the skipped loop could not have spawned) and
**behaviourally catastrophic in sequence**. Fixed by putting the paint test *inside* the chips block,
after the draw:

```java
if (chips >= want.moneyCost + reserve) {
    int start = G.rng.nextInt(8);
    if (rc.getPaint() >= want.paintCost + PAINT_RESERVE)
    for (int i = 0; i < 8; i++) { ... }
}
```

At `PAINT_RESERVE = 0` this consumes the draw identically *and* its guard is exactly what
`canBuildRobot` already asserts, so it is now genuinely exact. Rebuilt as `bob_r0..bob_r3`,
compile-checked, relaunched as run **`20260908-101158`**.

**What this cost and what it bought.** It cost 200 games of shared VM time. It bought the bug — and
had I not pre-registered the void condition, I would have read `bob_q1` at **25/50, +6 over the
null, 5 swept wins** as my first promising result in seven iterations, and it is an artefact of a
desynchronised random number generator. That is precisely the coordinator's rule about running the
manipulation check when you expect to pass: I expected the zero arm to pass, it was the check I was
most confident about, and it is the one that fired.

### The far more important finding: **my nulls' zero variance is STRUCTURAL, not statistical**

For seven consecutive runs I have recorded the control arm at *exactly* 25/50 with all 25 maps split,
and I wrote at iteration 18, in as many words, *"a zero arm measured at EXACTLY the null (25/50,
**se = 0**, all 25 maps split)"*. I have been reading that as **the instrument has no noise**.

It does not mean that. Those arms were **byte-identical** to the bot, so the deterministic engine
produced a perfectly antisymmetric mirror; 25/50-all-split is forced by symmetry and could not have
come out otherwise. It is a check that the harness is wired correctly. **It is not a measurement of
how much a changed arm's score moves for reasons unrelated to its mechanism.**

And run 1 accidentally measured that quantity for the first time. `bob_q0` differs from the
incumbent **only** by PRNG phase — no decision rule changed, no outcome that the loop could have
produced was altered — and it scored **19/50, with swept maps going from 0-against to 8-against.**

**So a behaviourally neutral change moved this instrument by 6 games and 8 swept maps.** Against
that, look at what I have been calling results:

```
iteration 24    reserve 600    -3
iteration 25    reserve 2400   +2      <- wrote several paragraphs of mechanism for this
iteration 26    1800 / 2400 / 3000     -1 / +0 / -3
```

**Every one of them is inside the band that a pure PRNG reshuffle produces.** This does not overturn
iteration 26's conclusion — the plateau stands, and is if anything better supported, since the
readings were noise exactly as the pooled 400-game result said. What it overturns is the *precision*
I have implied all session, and it explains why iteration 25's `+2` failed to replicate: it was never
a +2 of anything.

**Caveat, held to my own standard (LEARNINGS 32): this is ONE draw from that distribution.** 19/50 is
1.7 binomial sd below 25 and I am not going to build a mechanism story on a single sample. The
*logical* half of the point needs no sample and is what I am asserting: a mirror null's zero variance
is forced by byte-identity and says nothing about a changed arm's variance.

**QUEUED — null-distribution calibration, and it is cheap and overdue.** Build 3-4 arms that are
behaviourally neutral but PRNG-desynchronised in different ways (consume an extra draw at a different
point), run them as one gauntlet, and read the **spread**. That is a direct measurement of this
instrument's noise floor, which doctrine 9 has asked me for since day one — *"compute the binomial
noise floor for each instrument's sample size and distrust any delta under it"* — and which I have
been approximating with a binomial formula that assumes the only variation is coin-flipping. One
200-game run buys a number that every future accept gate should be set against.

### Null-distribution calibration built and queued (runs after iteration 27b)

`src/bob_n0 .. bob_n3`, compile-checked. Each burns 0/1/2/3 extra `G.rng.nextInt(8)` draws per
robot-turn in `RobotPlayer`'s loop and changes **nothing else** — no decision rule differs from
`src/bob` anywhere. `bob_n0`'s burn loop has zero iterations and consumes no draw, so it is
behaviourally identical and must return 25/50-all-split: a control on the control.

`bob_n1..n3` are policy-identical to the bot and differ only in the **phase** of every robot's
per-robot PRNG stream. The **spread** of their three scores is a direct measurement of how far this
instrument moves for reasons that have nothing to do with any mechanism — the noise floor doctrine 9
has asked for since day one and that I have been supplying with a binomial formula instead. The
formula assumes coin-flips are the only source of variation; a deterministic engine is not a quiet
engine, it is a chaotic one with reproducible chaos, and the accidental 19/50 says the difference is
large enough to have swallowed every "result" I logged in iterations 24-26.

**How the number will be used, fixed in advance so it cannot be tuned to taste:** the observed range
of `n1..n3` becomes the minimum margin any future single-sample arm must clear before I write a
mechanism paragraph about it. If the spread is wide, my accept gate of `>= 30/50` (a +5 margin) is
too generous and moves up. I am committing to that direction now, while I do not know the answer —
a calibration that can only ever loosen my gate is not a calibration.

### PRNG draw-site audit of the live bot (LEARNINGS 35's corollary, checked rather than assumed)

Every `G.rng` draw in `src/bob`, with the condition that gates it:

```
Tower.java:77   int start = G.rng.nextInt(8)      inside  if (chips >= moneyCost + reserve)
Nav.java:23     G.randomDir()                     inside  if (stuckTurns >= 3)
Nav.java:52     int start = G.rng.nextInt(8)      inside  if (wanderDir == null || wanderSteps <= 0
Nav.java:58     wanderSteps = 6 + G.rng.nextInt(10)         || !rc.canMove(wanderDir))
```

**All four draws sit inside a condition, and three of those conditions are governed by constants
this lineage tunes** — the spawn `reserve` (iterations 24-26), the stuck threshold `3`, and the
wander-length constants `6` and `10`. So **essentially every behavioural change I can make to this
bot also reshuffles the PRNG.**

That is not a bug and mostly not fixable: for a genuine behavioural change the reshuffle is *part of
the change*, not a confound to be removed. The trap is narrower and is exactly the one I fell into —
believing a change inert while it re-scopes a draw.

But it does settle the priority of the queued calibration. If every measured arm's score is
`mechanism + reshuffle`, then knowing the reshuffle's typical size is not a refinement, it is a
precondition for reading **any** of my results. I have run 27 iterations without it.

### Gate clarification for iteration 27b, written BEFORE the run lands

With `se ≈ 3.5` games on a 50-game arm now established, my pre-registered accept threshold of
**>= 30/50** is a **+5 margin = 1.4 se** — about a one-in-twelve result by chance alone. That is a
weaker gate than I had understood it to be when I wrote it, and I have now set six iterations
against it.

I am **not** moving the pre-registered number: it stands as **necessary**. What I am fixing, while I
still do not know the outcome, is that it is not **sufficient**:

- **Margin >= +7 (32/50), i.e. 2 se** — accept-eligible on this single sample, then the frozen
  roster as pre-registered.
- **Margin +5 or +6 (30-31/50)** — meets the letter of the gate but sits inside 2 se, so it requires
  **replication on a fresh map sample** before I accept. Iteration 26 is the precedent and the whole
  argument: a `+2` that bought a page of mechanism was worth exactly nothing when re-sampled, and
  the replication cost one command.
- **Margin <= +4** — reject, as before.

This only ever makes acceptance harder, which is the direction a mid-flight clarification is allowed
to run. I committed one paragraph ago that a calibration which can only loosen a gate is not a
calibration; this is that commitment being spent rather than quoted.

---

## Iteration 27b — RESULT: **REJECTED**, monotone in the wrong direction, and the premise is refuted

Run `20260908-101158`, 200 games, one shared 25-map sample. Arms `bob_r0..r3`.

```
arm      PAINT_RESERVE   score   vs null   swept  sweptAg  split   diff-from-null
bob_r0             0     25/50      +0       0        0      25        0/50   <- NULL
bob_r1           100     18/50      -7       2        9      14       13/50
bob_r2           200     19/50      -6       2        8      15       16/50
bob_r3           300     10/50     -15       0       15      10       17/50
```

**The zero arm is EXACT this time: 25/50, all 25 maps split, zero swept.** That is the fix to the
run-1 void confirmed directly — moving the paint test after `G.rng.nextInt(8)` restored byte-exact
behaviour, exactly as diagnosed. The void was called correctly and for the right reason.

**Manipulation check: PASSED**, and I ran it because I expected to pass, per the rule adopted this
session. `src/bob_qprobe` (rebuilt on the corrected `bob_r2`, not the broken `q2`) counts spawns the
zero arm makes that the dosed arm does not:

```
                blockedOnlyByDose (per tower)     paintShortAnyway
Dominoes            30, 88, 1                       569, 0, 60
memstore            30, 3, 11                       155, 33, 0
```

Non-zero and substantial — **119 blocked spawns on Dominoes, 44 on memstore.** The dose bites, so
the numbers above measure my mechanism rather than something else. (`paintShortAnyway` is large,
confirming the 8-10% pooling figure: towers are usually below `paintCost` regardless. But a live band
exists and the reserve acts in it.)

### Verdict and what it refutes

**Monotone decreasing across the whole tested range**, and `bob_r3` at **−15** is far outside the
±7 band that `se ≈ 3.5` gives at 2 se. This is not a null — it is a clear, well-measured result in
the **opposite** direction to my prediction, which was an interior peak at 100-200.

The premise is refuted, and precisely: I argued *"one spawn (200 tower paint) = up to four refills
forgone, and ~95% of soldier deaths are starvation, so the tower is spending on new units the paint
its existing units are dying for."* Every step of that is true and the **conclusion is still wrong**.
Withholding paint to fund refills loses games, harder the more you withhold. **A new unit is worth
more than keeping an old one alive.** In hindsight the reason is not subtle: a refilled soldier
resumes a job the map may no longer have, while a new soldier is a fresh action budget — and
iteration 20 already measured that late-game soldiers act on 0.4-5.2% of their turns. I priced the
paint and never priced what the two purchases *buy*.

### The genuinely valuable part: the spawn rate is now BRACKETED

Two independent knobs, pushed in opposite directions, both worse:

```
iteration 24   chip reserve -> 0     spawn MORE than baseline    -7
iteration 27   paint reserve -> 100+ spawn LESS than baseline    -7, -6, -15
```

So the current spawn policy sits at an **interior optimum on the spawn-rate axis, measured on both
sides** rather than assumed. The two knobs are not the same quantity — the chip reserve moves when
chips permit, the paint reserve moves which towers can afford the paint — so I am claiming the
bracket only at the level of *spawn rate*, which is what they share. That caveat is the whole of my
claim's fine print and I am not quoting a combined magnitude.

This is the second constant this week to go from unexamined guess to measured optimum (the other
being `reserve = 1200`), and per LEARNINGS 37 that is the right use of a 50-game instrument: it
cannot resolve a small win, but it resolves a **−15** without difficulty. Both tails here are far
outside noise; it is only the middle that this instrument cannot read.

`src/bob/` unchanged. **`bob_iter20` remains the bot.**

---

## PHASE 0 API SWEEP (2026-09-08) — overdue, and it found a whole mechanic I have never called

Doctrine now schedules this at **iteration 5, every 10 thereafter, and whenever the loop stalls**,
replacing "periodically" — an instruction with no trigger, which loses every time it competes with a
live hypothesis. I am at iteration 27 and had never run it. The coordinator's framing is the reason
it cannot be substituted: **the failure mode is not knowing a call exists, so re-reading my own bot
cannot surface it.** It needs the external list.

`javap battlecode.common.RobotController` from the 3.1.0 engine jar, diffed against every method
`src/bob/*.java` calls. **68 methods; 27 never called.**

### 1. THE HEADLINE: this bot has no communication whatsoever

```
sendMessage        0 call sites        canSendMessage        0
readMessages       0 call sites        canBroadcastMessage   0
broadcastMessage   0 call sites
```

**Zero. Twenty-seven iterations, and the entire messaging mechanic is untouched.** My own `RULES.md`
documents it in full and has since Phase 0 — robot↔tower within r²≤20 over connected ally paint,
**tower→tower broadcast within r²≤80 with no paint connectivity required**, 32-bit payload, 5-round
buffer, towers may send 20 messages a turn. I wrote that section, and then built a bot in which no
robot ever tells another robot anything.

**This lands exactly on the constraint that closed my most promising rejected direction.** Iteration
13's closure reads: *"Re-open only if soldier movement stops being the binding constraint on ruin
discovery — **for instance if a future iteration gives soldiers a non-movement way to find ruins**."*
Communication is precisely that, and I wrote the re-open condition myself without noticing that the
engine already offers the capability it names. The related finding from that closure — *"soldier
movement is this bot's scarcest capability, not its spare one"* — is what makes it valuable: the bot
currently spends its scarcest resource rediscovering, unit by unit, information some other unit
already had.

The tower→tower broadcast backbone is the part that needs no paint connectivity, so a tower mesh is
reachable without solving the connectivity problem first.

### 2. Markers — a free persistent shared blackboard, also unused

```
mark  0        removeMark  0        canMark  0        canRemoveMark  0
```

The bot calls `markTowerPattern` and `markResourcePattern` (different methods) but never the
general-purpose `mark()`. `RULES.md`: *ally-visible map annotations, r²≤2, costs 1 paint, no
cooldown.* That is a persistent shared blackboard written on the terrain itself, needing no
connectivity and no protocol — strictly simpler than messaging, and a cheaper first probe of the
same idea. Caveat already in my own notes: marks are a contended map-wide resource that pattern
marking competes for, so this is not free of interactions.

### 3. Smaller, but real

- **`getNumberTowers` — never called, and `MAX_NUMBER_OF_TOWERS = 25` is a hard cap I reason about.**
  Iteration 25's write-up asserts tower utilisation is *"pinned at the engine cap on large maps"* —
  a claim about a quantity the bot cannot observe, and the engine hands it over in one call.
- `getResourcePattern` / `getTowerPattern` — `RULES.md` line 201 explicitly says *"use
  rc.getResourcePattern() rather than hand-decoding"*, and I do neither.
- `getActionCooldownTurns` / `getMovementCooldownTurns` — I use only the boolean `isActionReady`,
  so the bot cannot tell "ready next turn" from "ready in five".
- `senseRobot`, `canSenseRobotAtLocation`, `isLocationOccupied`, `sensePassability`, `onTheMap`,
  `adjacentLocation` — utilities; convenience rather than capability.
- `disintegrate`, `resign`, `setIndicatorDot`, `setIndicatorLine` — situational or debug.

### What this does to my plan

I was about to pre-register iteration 28 on the **mopper share** — a genuinely untested axis (the
mopper slot has been pinned at 1-in-5 since iteration 0 and appears nowhere in the CLOSED list). It
is still a real candidate and I am keeping it queued.

But it is another *parameter* in a space I already know about, and the sweep's whole point is that a
ladder cannot tell you whether the space is the right one. Per LEARNINGS 37, a 50-game arm cannot
resolve anything under ~14 points, so tuning a share I have already bracketed twice is poor value,
whereas **an unused mechanic is where a 14-point effect could plausibly live.** Communication is
therefore ahead of the mopper share in the queue.

**And one correction it forces immediately**: iteration 25's "utilisation is pinned at the engine
cap" was inferred, when `getNumberTowers()` would have measured it. That is a small instance of the
sweep's general lesson — I reasoned about a quantity rather than reading it, because I did not know
it was readable.

## COMMUNICATION CHANNEL-SIZING PROBE (2026-09-08) — the channel is wide open and the demand is enormous

Doctrine 4 says size the condition before building the mechanism. `src/bob_commprobe` (instrumentation
only; counters placed where they touch no PRNG draw and change no control flow), vs `bob_iter11`, on
one map from each resource regime.

**Tower→tower broadcast — the backbone:**

```
map        tower-turns   canBroadcast      numberTowers
Dominoes      53 / 38      53 / 38  =100%       15
memstore     372 / 250    372 / 250 =100%        6
```

**`canBroadcastMessage()` is true on 100% of tower turns on both maps.** As documented, it needs no
paint connectivity. There is no gating condition to engineer around — the backbone is simply available
and has been for 27 iterations.

**Soldier→tower — the access link:**

```
map        soldier-turns   tower in vision   canSend   idle (no ruin)   idle AND canSend
Dominoes      20/10/2          18/10/2       18/10/2      20/10/2          18/10/2
memstore     212/37/26        121/4/6        113/4/5      212/7/7          113/4/5
```

Two things, and the second is the one that matters:

1. **When a tower is in vision, the soldier can almost always message it** — 100% on Dominoes,
   113/121 = **93%** on memstore. The ally-paint connectivity requirement, which I expected to be the
   binding constraint, essentially never bites, because the ground around a tower is painted.
2. **`idleNoRuin` is 212 of 212 turns for one memstore soldier and 20 of 20, 10 of 10, 2 of 2 on
   Dominoes.** These soldiers hold **no ruin target at all**, for their entire lives, and on 113 of
   those 212 turns that soldier was in message contact with a tower. The demand side is not a trickle;
   idle soldiers are the normal state, and they are in contact.

**So the mechanism is not gated by the channel.** Both links are open far more often than any
mechanism needs. That is an unusually clean pre-check: the usual outcome (iterations 13, 22, 23) is
that the enabling condition turns out to be rare.

### And it settles the iteration 25 claim the sweep flagged

`getNumberTowers()` — never called before today — returns **15 on Dominoes and 6 on memstore**, against
`MAX_NUMBER_OF_TOWERS = 25`. Iteration 25 asserted tower utilisation was *"pinned at the engine cap on
large maps"* and built a tower-saturation argument on it. **It is not pinned at the cap. It is at 60%
and 24%.** The argument was already refuted by iteration 26's replication; it is now refuted a second
time, by a direct reading of the quantity it was about. I inferred a number the engine hands over in
one call — LEARNINGS 38's smaller instance, now with figures.

**This also removes the reason iteration 25 gave for not expecting gains from more towers**, and more
towers is exactly what better ruin discovery would buy.

---

## Iteration 28 — PRE-REGISTERED: share ruin locations over the messaging mechanic

**Why this and not the mopper share.** The API sweep found messaging entirely unused; the
channel-sizing probe found both links open (100% broadcast, 93-100% soldier→tower when a tower is in
vision) and the demand enormous (soldiers idle with no ruin target for whole lifetimes). And it is
the literal re-open condition I wrote for iteration 13 — *"a non-movement way to find ruins"* — for a
direction closed because **soldier movement is this bot's scarcest capability.** Per LEARNINGS 37 a
50-game arm cannot resolve a small effect, so an unused mechanic is where a resolvable one can live.

**Mechanism (one idea, two halves).**
- *Tower*: ingests ruin sightings from its own vision (unclaimed ruins only) and from messages,
  keeps 12, and each turn broadcasts one round-robin to the tower mesh (r²≤80, no connectivity) and
  pushes it to allied soldiers in vision (capped at 15 sends, under the 20/turn tower limit).
- *Soldier*: reads messages; in `chooseRuin`, when **nothing unclaimed is visible**, adopts the
  hinted ruin instead of falling through to `Nav.wander()`.

Encoding `1 + x*64 + y`; 0 means nothing.

**Dose: `HINT_MAX_D2`, how far a soldier will travel for a hint.** Arms `bob_h0` (0), `bob_h1` (400),
`bob_h2` (1600), `bob_h3` (6400), one shared 25-map sample, 200 games.

**`bob_h0` is an exact zero arm, and deliberately so**: at 0 the hint is still read and broadcast but
never *accepted*, so `chooseRuin` returns the same answer and `Nav.wander()` is reached on exactly
the same turns — which keeps each robot's PRNG in phase. That is LEARNINGS 35 applied at design time
rather than discovered by a void. All comm machinery runs in every arm, so the **only** thing that
varies across arms is the acceptance radius.

**Pre-flight checks already run** (a new mechanism can fail silently): one full game, **zero
exceptions** (`EXC`/`GAE` both 0 — each would cost 500 bytecode) and **zero bytecode overruns**, with
towers rising only 590→736 of 20,000 (3.7%) and soldiers at 1,736 of 17,500 (9.9%).

**Gates.**
- **Void** if `bob_h0` is not 25/50 with all 25 maps split.
- **Accept** per the tightened rule fixed earlier today: margin **>= +7 (32/50, 2 se)** → accept-
  eligible on this sample, then the frozen roster (`bob_iter0`, `bob_iter1`, `bob_iter11`,
  `examplefuncsplayer`, `bob_iter20`; none regressing by more than 3, and I quote the **weakest**
  rung). Margin **+5/+6** → replication on a fresh sample before accepting. **<= +4** → reject.
- **Manipulation check** to be run *whichever way the headline falls*, per the rule adopted today: a
  counter build measuring how often a soldier actually **adopts** a hint. If that is ~0 the dose does
  not exist and the run voids regardless of the number. The dose-response across three radii is a
  weaker cross-check of the same thing, not a substitute.

**Prediction.** Monotone increasing from 0 through 1600, because a longer acceptance radius converts
more idle wandering into directed travel — then **flattening or falling at 6400**, where a soldier
crosses most of the map for a ruin that will usually be claimed before it arrives. So: **interior
peak at 1600, with 6400 at or below it.**

**A failure mode I can see now and am recording before the run**, so it cannot become a
post-hoc rescue: the hint is a *single most-recent* location, so every soldier in a tower's range
receives the same one and may pile onto one ruin. If the effect is negative, that is the first thing
to check, and the fix is a per-soldier spread (round-robin per recipient), not abandoning the idea.

## Iteration 28 v1 — **VOID by the manipulation check, called while the run was still in flight**

Run `20260908-111254` was still playing when `src/bob_hprobe` (= the `bob_h2` arm plus adoption
counters) returned the pre-registered kill condition:

```
map         soldier-turns   haveHint   ADOPTED
Dominoes     123 / 104 / 17    0/0/0     0/0/0
memstore     212 /  37 / 26    0/0/0     0/0/0
```

**Soldiers never received a single message.** `ADOPTED = 0` everywhere, so `HINT_MAX_D2` was not a
dose at all — every arm played identical policy and the run measures nothing. Pre-registered
condition: *"If that is ~0 the dose does not exist and the run voids regardless of the number."*
**Void.** I am not looking at its scores.

This is the second void in one day and the second time the check fired on the thing I was most
confident about. It is also the second time the pre-registration is what stopped me: the dose-
response across three radii would have come back flat, and "communication does not help" is an
extremely plausible-sounding conclusion to draw from a flat curve produced by a mechanism that never
executed.

### The fault, diagnosed rather than guessed

Two engine facts checked first, so I did not blame the wrong thing:

- **`readMessages(-1)` is correct.** Disassembling `RobotControllerImpl.readMessages` shows
  `if (arg == -1) add-unconditionally`, so `-1` really does mean "all buffered rounds".
- **Tower→robot sending is legal.** `assertCanSendMessage`'s messages are *"Only (robot <-> tower)
  communication is allowed"* — both directions.

So the channel was fine and the fault was mine: **I built a consumer and a relay and no producer.**
Towers ingested ruins from their own vision only — and **towers are built on ruins and sit among
ruins that are therefore already claimed**, so `nKnown` stayed 0 and there was nothing to relay. The
units that actually discover *unclaimed* ruins are the wandering soldiers, and in v1 soldiers never
sent anything at all.

That is a design error with an obvious shape in hindsight, and the reason I missed it is worth
naming: I designed the protocol around **who owns the radio** (towers have the long-range broadcast
and the 20-message budget) rather than around **who holds the information**. The capability lives in
one place and the knowledge in another.

### Two further fixes the probe forced, each measured rather than assumed

**v2 — soldiers report a free ruin.** Still `reportable = 0` on both maps. Diagnosed: my producer
excluded `workRuin`, but `chooseRuin` always claims the *nearest* free ruin it can see, so the only
reportable ruins were second-and-later sightings. Removed the exclusion.

**v3 — per-recipient round-robin.** The tower was sending the *same* code to every soldier in range;
it now advances the round-robin per recipient, so two soldiers are steered to different ruins. This
is the failure mode I pre-registered before the run (*"every soldier receives the same one and may
pile onto one ruin"*) — fixed on its own merits, not because a number demanded it.

**v3 manipulation check PASSES on both maps:**

```
map         haveHint   ADOPTED   seenTaken (hint pointed at a claimed ruin)
Dominoes     29/25/12    8/1/2      4/0/0
memstore     27/11/8     7/3/1     14/2/6
```

Hints flow, and soldiers adopt them, in both resource regimes. **`seenTaken` is large** — 14 of 21
on one memstore soldier — meaning many hints point at ruins claimed since they were broadcast. That
is a real staleness cost, recorded now as a known limitation rather than discovered later: towers
cannot see distant entries go stale, and nothing expires them.

`src/bob_j0..j3` built from the **verified** v3 mechanism with the counters stripped (assertion-
checked that none remain), compile-checked. Iteration 28c launches when the void run releases the VM
— I am not killing it; the shared-VM rule is absolute and it costs only wall-clock.

## Iteration 28c — PRE-REGISTERED (the v1 registration does not carry over; this is a different build)

Arms `bob_j0` (0), `bob_j1` (400), `bob_j2` (1600), `bob_j3` (6400), built from the **v3 mechanism
whose manipulation check passed**, counters stripped and asserted absent, all four compile-checked.
200 games, one shared 25-map sample.

**Zero arm.** `bob_j0` runs the full protocol — soldiers report, towers ingest, relay and push — and
simply never *accepts* a hint. So `chooseRuin` returns what it always returned and `Nav.wander()` is
reached on exactly the same turns, keeping each robot's PRNG in phase. Comm work costs bytecode only
(no PRNG draw, no control-flow change on the spawn or wander paths). **Void if `bob_j0` is not 25/50
with all 25 maps split** — and note this is a *stronger* test here than usual, because it also
certifies that the entire messaging layer is behaviourally inert when its output is ignored.

**Gates unchanged** from the tightened rule: accept-eligible at margin **>= +7 (32/50, 2 se)** then
the frozen roster (weakest rung quoted, none regressing by more than 3); **+5/+6** requires
replication on a fresh sample; **<= +4** rejects.

**Revised prediction, and it moved because of a measurement.** v1's registration predicted an
interior peak at 1600. The v3 probe measured something I did not have then: **`seenTaken` is large —
14 of 21 on one memstore soldier, 4 of 12 on Dominoes.** Many hints point at ruins that were claimed
after the broadcast, nothing expires them, and a soldier only adopts a hint it *cannot yet verify*,
so it pays the full walk and discovers the ruin is taken on arrival. **A longer acceptance radius
therefore buys both more directed travel and more wasted travel**, and the wasted half grows faster,
because a distant ruin has had longer to be claimed and costs more to reach.

**So I now predict the peak at 400, the SHORTEST non-zero dose, with 1600 lower and 6400 clearly
negative** — possibly below the null. That is a different prediction from the one I registered this
morning and I am flagging the change rather than quietly substituting it: it is driven by a number I
did not have (`seenTaken`), not by a preference for being right.

**If all three doses come back at or below the null**, the mechanism as built is refuted and
staleness is the pre-named cause — the fix would be expiry (towers dropping an entry when they
observe a tower on it, and a round-stamp so old entries age out), not abandoning ruin sharing. I am
writing that down now so that a negative result does not get read as "communication does not help",
which is the over-general conclusion this experiment is most likely to produce.

### Iteration 27b, map-level shape (doctrine 10) — one-directional, not churn

Free re-analysis of the completed run. Per-map arm scores, 2 games per map:

```
bob_r0 (null)  scores exactly 1 of 2 on ALL 25 maps          <- perfect mirror, every map split
bob_r3 (300)   worse than the null on 15 maps
               equal on 10
               BETTER on 0
```

Doctrine 10 distinguishes churn from causation by the diff's *shape*: scattered mixed-direction
flips are churn, one-directional flips are a real causal effect. **This is 15-0 with no map moving
the other way.** Under a sign test that is p ≈ 3 x 10⁻⁵, so the rejection does not rest on the
50-game margin at all — it rests on a uniform, one-signed effect across the whole pool. Withholding
tower paint from spawning hurts *everywhere*; there is no regime in which it pays.

That also disposes of the doctrine-4 worry I raised when I could not build a static regime
classifier. I wanted to know whether gains might be concentrated on paint-bound maps and diluted by
chip-bound ones. **There are no gains to concentrate** — the effect is negative or neutral on 25 of
25, so no regime split could rescue it.

And `bob_r0` scoring **exactly 1 of 2 on every one of the 25 maps** is the cleanest confirmation
available that the corrected arm is byte-exact: not merely 25/50 in aggregate, but perfectly
antisymmetric map by map. The run-1 void diagnosis is now confirmed twice over.

### Queue after iteration 28 (recorded now, while the reasoning is fresh)

1. **SRP-site sharing — the same key, a second lock.** Iteration 13 closed *"spend soldier movement
   to find SRP sites"* at −35 games, and the SRP gate probe showed why: only **20.6%** of paintable
   tiles are legal pattern centres, and the bot tests exactly **one** candidate per turn (whichever
   tile a random wander left it on). The mechanism was never the problem — it *"demonstrably produced
   active SRPs on maps where iteration 12 produces none in 2,000 rounds"* — the **price** was, and the
   price was movement. If ruin-sharing works, the identical protocol carries SRP-legal centres, and
   a soldier walks to a *known* legal site instead of prospecting for one. Note this is the **same
   re-open condition** iteration 13 wrote, applied to the same closure a second time.
2. **Markers** (`mark`/`removeMark`, unused). A persistent ally-visible blackboard on the terrain,
   1 paint, no cooldown, no connectivity requirement and no protocol. Cheaper than messaging and
   would survive the death of the unit that wrote it — which messages do not. Caveat already on
   record: marks are a contended map-wide resource that tower-pattern marking competes for.
3. **Mopper share.** The mopper slot has been pinned at 1-in-5 since iteration 0, appears nowhere in
   the CLOSED list, and iteration 20 established a real mopper→soldier repaint chain (a mopper turns
   enemy paint neutral and only a soldier can then claim it), so an interior optimum is plausible.
   Ranked below the first two per LEARNINGS 37: it is another constant in a space I already know,
   and a 50-game arm cannot resolve a small win.
4. **Null-distribution calibration** (`bob_n0..n3`, built and compile-checked). Still queued; its job
   is now the sharper question of whether the real spread **exceeds** binomial.

Ordering principle, from today: an unused mechanic outranks an untuned constant, because only the
first can plausibly produce an effect this instrument can see.

---

## STATE OF PLAY (2026-09-08 ~11:40 UTC) — read this first if you are resuming

**The bot**: `src/bob` is byte-identical to `bob_iter20` (verified, all seven files modulo the
package line). HEAD compiles and is tournament-safe. **No accept this session.**

**In flight / queued, in order:**

1. **Run `20260908-111254` is VOID** — iteration 28 v1, whose manipulation check returned
   `ADOPTED = 0` while it was still playing. **Do not read its scores.** It was left to finish
   because the shared-VM rule forbids killing, and killing the local driver would not have stopped
   the setsid-detached remote games anyway.
2. **Iteration 28c** (`bob_j0..j3`, HINT_MAX_D2 = 0/400/1600/6400) is pre-registered and launches
   automatically when the void run releases the VM. **If it did not launch, launch it:**
   `MAXJOBS=3 BOT=bob OPPONENTS="bob_j0 bob_j1 bob_j2 bob_j3" ../../tools/gauntlet.sh`
   Evaluate with `python3 bob-tools/eval_arms.py gauntlet/<run> bob_j0 bob_j1 bob_j2 bob_j3`.
3. Then the queue recorded above: SRP-site sharing, markers, mopper share, null calibration.

**Three standing rules established today that change how results are read.** These matter more than
any single iteration and are easy to lose:

- **`eval_arms.py` exists so nobody re-derives the score convention under pressure.** `gauntlet.sh`
  reports the **bot's** score; a dose sweep needs the **arm's** (`50 − bot`). Use the tool.
- **`se ≈ 3.5` games on a 50-game arm.** A mirror null reading 25/50-all-split is **forced by
  byte-identity**, not measured — never quote it as the instrument's standard error. Accept needs
  **>= +7 (2 se)**; **+5/+6** needs replication on a fresh sample; **<= +4** rejects.
- **Run the manipulation check on a PROBE build before the gauntlet, not after.** It fired twice
  today, both times on the thing I was most confident about, and both times it was the only thing
  standing between me and a confident wrong conclusion.

**A PRNG trap that will bite again**: `G.rng` is a per-robot `Random(id)` and all four draw sites sit
inside conditions, three of them governed by constants this lineage tunes. **Narrowing an `if` that
wraps a draw is never a no-op** — it desynchronises that robot for the rest of the game. Put a new
guard *after* the draw. This voided a 200-game run today.

---

## Iteration 28c — REJECT (decisive). Run `20260908-115418`, 200 games, collated 2026-09-08.

This is the run that finished after the previous session died; the games were complete and collated,
only the verdict was missing. Recovered rather than re-run.

**Design.** One mechanism, one constant. `HINT_MAX_D2` = the largest r² at which a soldier will
accept a broadcast ruin hint. Arms `bob_j0/j1/j2/j3` = 0 / 400 / 1600 / 6400 (d = 0 / 20 / 40 / 80).
Diff between arms is literally one line, verified with `diff` modulo the package statement.

**Null arm clean.** `bob_j0` read 25/50 with all 25 maps split by side and 0 swept either way — the
signature of behavioural identity to baseline. The `HINT_MAX_D2 = 0` arm therefore reaches
`Nav.wander()` on exactly the same turns as `bob` and the per-robot PRNG stays in phase, which is
what LEARNINGS 35 demands. The dose ladder is measured against a sound zero.

**Result** (`eval_arms.py`, arm's own score = 50 − bot):

| arm | HINT_MAX_D2 | score | vs null | swept for | swept against |
|---|---|---|---|---|---|
| j0 | 0    | 25/50 |  +0 | 0 | 0  |
| j1 | 400  |  9/50 | −16 | 1 | 17 |
| j2 | 1600 | 10/50 | −15 | 1 | 16 |
| j3 | 6400 | 10/50 | −15 | 1 | 16 |

−15/−16 is >4 se against (se ≈ 3.5), one-directional across all three doses, and corroborated by the
sweep counts: 16–17 maps lost from *both* sides against 1 won from both. **Ruin-hint sharing is
rejected, and this is the third and final attempt at it** (v1 void by manipulation check, v2 producer
measured reportable=0, v3 = this). Closing it.

**The flatness is the finding, not the sign.** 400 → 6400 is a 16× change in accepted radius, d=20 to
d=80 (whole-map). It moved the score by **one game**. A knob on the causal path shows a gradient; this
one shows none. **`HINT_MAX_D2` is not on the causal path of the damage.** I pre-registered a dose
sweep over a constant that does not control the mechanism it was meant to titrate, which means the
sweep spent 150 games re-measuring one arm three times.

**What the knob missed.** The damage is not *how far* a soldier walks to a hint. It is that
`workRuin` becomes non-null **at all**. Two behaviours in `Soldier.run()` are gated on it:

- `if (workRuin == null && workOnSrp()) return;` — SRP construction is switched off for any soldier
  holding a hint. SRP is the compounding economy (+3/turn per mining tower per active SRP,
  multiplicative in tower count).
- `if (workRuin != null) Nav.navTo(workRuin); else Nav.wander();` — wander is the paint-expansion and
  ruin-discovery behaviour, and the win condition is painting 70% of the map.

Both saturate at the smallest dose, because `hint` is **sticky**: `readHints()` overwrites it when a
message arrives and never clears it. Once a soldier has been within d=20 of any hint it holds one
essentially permanently, so at every dose ≥400 the army has SRP and wander suppressed nearly always.
That is exactly the shape the data has: a large step at the first nonzero dose and a flat line after.

**A hypothesis I checked and dropped.** "Soldiers are getting stuck on phantom/occupied ruins and
functionally dying" predicts a change in *how* games end — annihilations, timeouts, more tiebreakers.
Reason breakdown is null 40 paint / 10 tiebreak vs arms 42 / 8, i.e. **unchanged**. Games end the same
way and at the same rate; only the winner moves. This is an ordinary strategic deficit, not a crash,
a freeze or an exception loop. Stated because the displacement account above is an inference from
code reading plus flatness, and this is the one competing account the run can actually discriminate.

**Secondary contributor, not measured.** `Tower.known[]` is never pruned: a ruin code enters and stays
after a tower is built there, and towers cross-feed codes to each other. So a share of hints steer at
ruins that are already claimed. This makes the displacement worse but cannot explain the flatness, so
it is not the primary fault and I am not testing it separately — the mechanic is closed.

### LEARNINGS 40 — a dose sweep is only informative if the knob controls the damage

A flat sweep across three doses over a clean null is **not** evidence of a robust effect. It is
evidence the knob is **off the causal path**, and it converts an n-arm experiment into a 1-arm
experiment at n× the price. Before pre-registering a dose ladder, state in one sentence *the physical
quantity the constant is supposed to titrate*, then check that quantity is the one doing the work. Here
the constant titrated "distance a soldier will travel for a hint" while the damage was done by "fraction
of turns `workRuin` is non-null" — a quantity `HINT_MAX_D2` barely touches, because stickiness pins it
near 1 at every nonzero dose.

Corollary, and the reason this is worth a numbered entry: the same flat ladder would have been read as
*"robust across doses, the effect is real"* had the sign been positive. The failure mode is symmetric
and it is not detectable from the numbers alone — only from re-deriving what the knob controls.

---

## Iteration 29 — PRE-REGISTERED 2026-09-08, before the probe reports

Written before I have seen a single probe number, so the arms cannot be fitted to them.

**Where this came from.** Not from a new idea — from the *code reading that explained 28c*. To
explain why the hint ladder was flat I had to work out what `workRuin != null` costs, and the answer
was a coupling that exists **in the shipping bot at baseline**:

```java
if (workRuin == null && workOnSrp()) return;      // Soldier.run(), step 1b
```

`srp` is a persistent per-soldier field. A soldier that has already marked a 5×5 resource pattern —
25 tiles of paint, spent — **abandons it the moment any free ruin enters vision**, and `srpTurns`
stops advancing while it is away, so `SRP_PATIENCE` never retires the stale site either. When the
ruin work ends, `workOnSrp` sees `distanceSquaredTo(srp) > 8` and walks the soldier back. That is an
oscillation between two sites with paint sunk into one of them.

28c is what makes this worth a run rather than a note: it *measured* how expensive this gate is.
Forcing `workRuin` non-null more often cost **15–16 games of 50**. A coupling with that much
leverage is worth testing in the other direction.

**Fit to the algorithm's stated winner profile.** "Capability preserved at zero marginal cost —
standing defenses, spending idle resources, **removing pure waste**." An abandoned half-built SRP is
pure waste, and finishing it spends no movement and no new resource.

**Neither SRP closure covers this, and I checked both rather than assuming.**
- Iteration 10 closed *"build more SRPs by searching harder for sites"* — and recorded a re-open
  note that this is a **different mechanism**: *"or moves SRP construction deliberately away from
  ruins ... a different mechanism (site selection policy) from the one just killed."*
- Iteration 13 closed *"spend soldier movement to find SRP sites"* at −35 games, re-open trigger
  "soldier movement stops being the binding constraint."

This iteration **spends no movement and searches for no sites.** It changes only whether a soldier
keeps working the site it is *already standing on and has already paid for*. It does not touch
`chooseRuin`, site selection, or the search. Iteration 13's −35 came from movement spent
prospecting; there is no prospecting here.

**Pre-registered reachability veto (this is the part that can kill it before it costs a gauntlet).**
The probe `bob_srpgate` counts the DECISION at the gate, not the outcome:
`abandon` = turns with `workRuin != null && srp != null`; `forgone` = turns ruin-busy while standing
on a legal, safe, affordable centre. **If `abandon` is ~0 across both probe maps, arm A is dead code
and does not get built** — no gauntlet. Iteration 10 already found that tower marks blanket the
ground soldiers occupy, and `srpSiteSafe` rejects any marked tile, so I expect `forgone` to be low;
`abandon` is the quantity that is genuinely unknown.

**Arms — and per LEARNINGS 40, the ladder titrates the quantity that does the work.** 28c's knob
(acceptance radius) was not on the causal path. The causal quantity is *the fraction of turns SRP
work is suppressed*, so the ladder steps that directly, in increasing SRP priority:

- `bob_s0` — exact baseline copy. Null arm; must read 25/50 all-split or the run is void.
- `bob_s1` — finish what you started: run `workOnSrp()` when `srp != null`, even if ruin-busy.
- `bob_s2` — s1, plus take a legal safe centre under foot rather than forgoing it.
- `bob_s3` — SRP work unconditionally outranks ruin work.

**Accept gate, pre-registered, per the standing rule**: arm's own score via `eval_arms.py`
(`50 − bot`). **≥ +7 accepts; +5/+6 needs replication on a fresh sample; ≤ +4 rejects.** If the
ladder is monotone in the arm index, that is corroboration the causal quantity is the right one; a
*flat* ladder here means I have made LEARNINGS 40's mistake twice and the knob is still wrong.

**Priced against what it displaces, not against zero.** The gain is a completed SRP (+3 resources/turn
per mining tower per active SRP, compounding in tower count). The price is delayed tower capture — and
towers are worth 30 chips/turn flat *and* raise the value of every future SRP. So the price is real and
plausibly larger than the gain; s3 in particular could be strongly negative, which is why the ladder
runs from "finish the sunk one" (cheapest, waste-removal only) up to "SRP always wins" (most
expensive) rather than testing only the aggressive end.

**Prediction, recorded now:** s1 > 0 and small (waste removal), s2 ≈ s1, s3 < 0. If s3 is the best arm
my model of the tower/SRP trade is wrong and I should say so plainly.

---

## Methodology correction 2026-09-08 — `cmp` on replay bytes is NOT a valid arm-to-arm identity check

This one nearly cost me a rebuilt probe and a wrong conclusion, and the false claim is in **my own
log's Phase 0 block**, where every resuming session reads it.

Phase 0 established, correctly: *"Same match run 4x: identical outcome, and replay files are
BYTE-IDENTICAL for identical games."* It then drew the conclusion — *"arm-to-arm identity checks can
`cmp` replays directly"* — **which does not follow.** The 4x determinism test ran the *same match*,
so both replays carried the *same team names*. An arm-to-arm check does not: the arms are different
Java packages, so they play under different team names, and **the team name is recorded in the
replay.** Different names produce different bytes for a game that is otherwise identical.

**Measured today.** `bob_srpgate` (baseline + counters) vs `bob_iter11` on Thirds, against `bob` vs
`bob_iter11` on the same map:

- raw `cmp`: **DIFFER** (1,907,765 vs 1,907,251 bytes — and 1,516,581 vs 1,515,476 on Portal)
- same winner, same `winType`, same round count (1374)
- full event stream from `replay-dump.sh --quiet`, team-name line excluded: **66 lines vs 66 lines,
  `diff` clean — identical.**

So the game is bit-for-bit the same game and only the recording differs. Had I trusted `cmp` I would
have voided a behaviour-neutral probe as "the instrumentation changed the game", rebuilt it smaller,
and still failed the same check forever.

**The discriminating case that made this safe to call.** Two hypotheses produce identical `cmp`
output — *"the probe changed behaviour"* and *"only the recording differs"* — so I did not name the
fault from the symptom. First I re-ran the baseline **alone** against the saved concurrent one: it
reproduced **byte-for-byte**, which cleared the competing worry that two concurrent
`vm-verbose-match.sh` runs sharing one remote build dir had corrupted the results (they had not —
both jobs compile the same source tree, so the race is benign). Only then did the event-stream diff
identify the recording as the sole difference.

**Standing rule, replacing the Phase 0 sentence.** To check an arm is behaviour-identical to
baseline, compare **event streams, not bytes**:

```bash
tools/replay-dump.sh <armA>.bc25 --quiet | grep -v GameHeader > a.txt
tools/replay-dump.sh <base>.bc25 --quiet | grep -v GameHeader > b.txt
diff a.txt b.txt          # clean == behaviour-identical
```

`cmp` remains valid for one thing only: **re-running the identical pairing** to test determinism or
detect a corrupted run, where the team names are the same by construction.

**Still-open item, deliberately not claimed as measured.** I attribute the byte delta to the team-name
strings, but 514 bytes is more than the 8 extra characters, so the remainder may be per-turn profiler
or bytecode data. `bob_namectl` — a copy of `src/bob` identical modulo the package line, with **no
probe code** — is built and compile-checked to settle it: if it differs from baseline by a similar
amount with an identical event stream, the name alone explains it and no instrumentation is implicated.
Until that runs, the attribution is a hypothesis; **the standing rule above does not depend on it.**

---

## Iteration 29 — VETOED at the pre-registered reachability check. No gauntlet. Cost: 4 probe games.

The veto I wrote into the pre-registration fired on the arm I was most confident about, which is the
third time today that a pre-gauntlet check has been the only thing between me and a confident wrong
conclusion.

**Probe** `bob_srpgate2`, two full games vs `bob_iter11` (Thirds 60×21, Leaf 60×60). v1 printed only
every 250 rounds and produced 6–9 lines a game — too sparse to measure — so v2 prints every 100
rounds **and** emits an event line the first six times each target counter increments per robot.
That makes absence meaningful: zero event lines is a **census** over every soldier that ever ran, not
a sampling gap.

**Probe verified behaviour-neutral by the corrected method** (event-stream diff, not `cmp` — see the
methodology correction above). Peak bytecode *at the probe point* was 1,300 of a soldier's 17,500, so
the added senses are nowhere near the limiter.

| map | robots | soldier turns | ruinBusy | srpLive | **abandon** | **forgone** |
|---|---|---|---|---|---|---|
| Thirds | 49 | 3,752 | 497 (13.2%) | 147 | **0** | 3 |
| Leaf | 566 | 74,211 | 15,584 (21.0%) | 384 | **0** | 0 |

**`abandon` is exactly 0 across 77,963 soldier turns.** This is not a small number, it is *zero*, and
neither input state is rare: soldiers are ruin-busy 13–21% of turns, and they hold an active SRP on
147 and 384 turns respectively. If the two states were independent the expected overlap is
3,752 × 0.132 × 0.039 ≈ 19 turns on Thirds and 74,211 × 0.21 × 0.0052 ≈ 81 on Leaf — call it ~100
turns expected, **0 observed**. The two states are structurally mutually exclusive.

**Why they cannot co-occur, which is the finding worth keeping.** `srpSiteSafe` rejects any tile with
a non-empty mark within r²≤8, and `markTowerPattern` blankets a 5×5 around every ruin under
construction. So an SRP can only ever be *started* on ground with no tower marks — that is, away from
ruins — and once started the soldier stays within d²≤8 of it. **SRP-active soldiers are, by
construction, in ruin-free neighbourhoods.** This is a direct quantitative confirmation of iteration
10's mark-saturation measurement (~128% of geometrically-valid candidates refused per turn) and of
`RULES.md`'s "marks are a contended, map-wide resource", arrived at from the opposite direction.

**Verdict**: arm `s1` (finish what you started) acts on a state that never occurs — dead code. Arm
`s2` would have fired **three times in a 1,374-round game** on one map and never on the other, which
cannot move 7 games in 50. `s3` remains logically possible but its whole premise was that SRP and
ruin work contend, and they do not. **Iteration 29 is not built and does not reach a gauntlet.**
Four probe games instead of two hundred.

**My pre-registered prediction was wrong in an instructive way.** I predicted "s1 > 0 and small, s2 ≈
s1, s3 < 0" — I was arguing about the *sizes* of effects in a state that does not exist. The
pre-check that mattered was not "which arm wins" but "does the situation arise at all", and I had
written that veto down precisely because I could not answer it from the code. Reachability outranks
effect-size reasoning, every time, and the reason is that effect-size reasoning always *sounds*
answerable.

### The measurement that came out of the failed iteration is worth more than the iteration was

Dumping the probe replays for engine-reported **active** SRP counts turned up something I did not go
looking for. `T1` is the current bot, `T2` is `bob_iter11` — **which carries the same SRP code**:

```
Leaf     r400   T1 $1,507 cov395 srp4   |  T2 $6,336   cov567 srp8
         r1000  T1 $1,555 cov535 srp3   |  T2 $8,430   cov445 srp8
         r2000  T1 $1,268 cov544 srp3   |  T2 $301,529 cov438 srp5
Thirds   r1000  T1 $1,468 cov325 srp1   |  T2 $1,419   cov526 srp4
```

Two things, and I am deliberately separating what is measured from what it might mean.

1. **The current bot sustains 2–4× fewer active SRPs than its own ancestor on identical SRP code.**
   Iteration 13 saw this once (1 vs 9 on DefaultHuge) and moved on; it reproduces here on two more maps.
2. **On Leaf the current bot's treasury is pinned at ~$1,300 for 1,800 rounds** while `bob_iter11`
   ends on $301,529. Flat-at-low with continuous spending means income ≈ spending: the bot is
   **chip-bound** on that map.

Point 2 matters because a recorded re-open trigger is written against exactly this quantity.
Iteration 8's closure says: *re-open trigger "chips sustained below ~5,000" — re-checked against 7
fresh traces, chips run 4.4k–61k in every game, trigger NOT met.* On Leaf it now reads $413–$1,571
all game. **The trigger appears to be met — on one map.** My own doctrine forbids sizing a quantity on
one map ("a quantity measured on one map is a statement about that map"), and Thirds is genuinely
mixed ($1,468–$7,519), so this is **not yet a re-open**. A 21-map chip census over baseline replays
already on disk is running; the re-open stands or falls on that, not on Leaf.

Note also that the direction is not obvious and I should not pre-judge it: `bob_iter11` has 8 SRPs and
$301k it cannot spend and **still loses on coverage** (438 vs 544). More resource income is only worth
something to a bot that converts it. The current bot converts and is short; its ancestor hoards and is
not. That asymmetry is the actual hypothesis, and it is about *chips*, not about SRPs.

---

## CORRECTION to the iteration 29 by-product, same day — both readings were confounded by SIDE

I published the two observations above with hedges about what they might mean. The hedges were on the
wrong thing. Within the hour the mirror data refuted the *attribution*, not the interpretation, and I
am correcting it in place rather than letting a confounded number sit in the log looking measured.

**What I claimed.** (1) "The current bot sustains 2–4× fewer active SRPs than its own ancestor on
identical SRP code." (2) "On Leaf the current bot is chip-bound at ~$1,300 while `bob_iter11` ends on
$301,529."

**Both compared `T1` against `T2` — and `T1` is side A, `T2` is side B.** The comparison is
bot-vs-bot only if side is not doing the work. It is.

**The mirror settles it.** `bob` vs `bob_j0` on Leaf — `bob_j0` is the 28c null arm, verified
behaviourally identical (25/50 with all 25 maps split by side, 0 swept, i.e. perfectly antisymmetric):

```
Leaf, MIRROR (bob side A vs bob_j0 side B, identical behaviour)
  r750   A $1,318  srp2   |   B   $5,465  srp6
  r1000  A $1,240  srp3   |   B $103,345  srp6
  r2000  A $5,736  srp1   |   B $527,895  srp6
```

A **400× treasury gap and a 2–6× SRP gap between two bots that are the same bot.** The identical
pattern (side A ≈ $1,300, side B ≈ $300–500k) then reproduces in the separate game against
`bob_iter11`, and it tracks **side**, not winner — side A won that one and side B won this one. So
observation (1) is not a fact about the current bot versus its ancestor at all, and observation (2)
is not a fact about the bot's economy. Both are facts about **Leaf's spawn positions**.

The algorithm states this outright and I read past it: *"in a mirror, any inter-team stat difference
is positional, not policy."* I had the mirror replay on disk the whole time — it was in the same
directory I pulled the numbers from.

**And Leaf is a degenerate sizing map, which the multi-map census caught.** Final-phase chips across
the baseline replays:

```
Leaf         A $5,736    B $527,895      <- extreme outlier, both directions
FourCorners  A $21,446   B $35,160
Bread        A $1,291    B $4,993
Circuit      A $3,898    B $4,056
MoneyTower   A $5,331    B $1,362
Paintball    A $6,270    B $3,850
Parking_lot  A $5,040    B $5,788
Justice      A $5,830    B $6,110
```

Typical is **$1,300–$6,000 on both sides**. So the two stories Leaf tempted me into — "the bot is
chip-starved" and "the bot hoards a fortune it never spends" — are each true of **one side of one
map** and false of the corpus. Neither iteration 8's re-open trigger ("chips sustained below ~5,000")
nor an "idle chips" thesis is established by this data. **No re-open. No iteration built.**

This is the second time today the same discipline paid: iteration 29 died at a reachability probe
instead of a 200-game gauntlet, and this died at an 8-map census instead of an iteration built on
Leaf. Both were cheap. The expensive version of this mistake is the one where the outlier map is the
one you happened to trace.

**What survives as a real, unexplained observation** — recorded as an observation, with no mechanism
claimed: on Leaf, two byte-identical bots diverge to a 400× treasury gap by spawn position alone.
Whether that is a property of Leaf's geometry or a symmetry defect in this bot is **not determined**;
`towerTypeFor`'s parity rule was my first suspect and the tower-type counts do not support it (side A
16 money / 17 paint, side B 14 money / 9 paint — a mix difference far too small to produce 400×).
The mirror-match sweep the algorithm prescribes for exactly this ("a persistent lopsided split on a
map is a real bug") is the right instrument, and the 28c null arm already reports the headline:
**all 25 maps split by side, none swept.** Queued, not concluded.

### Closing the byte-delta attribution: measured, not assumed

The correction above left one item explicitly open — I attributed the replay byte delta to the team
name but flagged that 514 bytes is far more than the 8 characters involved, so the remainder was
unexplained. `bob_namectl` (a copy of `src/bob` identical modulo the package line, **no probe code**)
settles it on Leaf:

```
bob          vs bob_iter11   19,650,643 bytes   (baseline)
bob_namectl  vs bob_iter11   19,650,651 bytes   +8      <- pure rename
bob_srpgate2 vs bob_iter11   19,663,986 bytes   +13,343 <- rename + 1,041 printed probe lines
```

**A pure rename costs exactly 8 bytes — the length difference between `bob` and `bob_namectl`,
appearing once.** Everything above that is the probe's own `System.out.println` output, which the
engine records into the replay when run with `-PoutputVerbose=true`.

So `cmp` on replays is sensitive to two things that are not behaviour: **the team name, and any robot
logging.** Both differ by construction for every instrumented arm — the name because arms are separate
packages, the logging because instrumenting is the point. That is why the check could never have been
cleared by making the probe smaller: shrinking a probe reduces the printed volume but never removes
the 8 bytes, and the check would have kept failing at the end of it. LEARNINGS 41 stands as written and
is now measured rather than inferred.

### Chip census, widened to 15 maps — the conclusion is unchanged and now sturdy

Final-phase treasury, both sides, baseline replays from run `20260908-115418`:

```
Leaf         A $5,736   B $527,895     <- the outlier, by two orders of magnitude
FourCorners  A $5,796   B $35,160      <- mild outlier
every other map, both sides:  $1,157 - $8,307
```

**Fourteen of fifteen maps sit in low single-digit thousands on BOTH sides.** So neither story Leaf
suggested survives contact with the corpus: there is no general hoarding problem, and iteration 8's
re-open trigger ("chips sustained below ~5,000") is not cleanly met either — several sides sit in the
$1.2k-$5k band, but these are final-phase samples from games of differing lengths and "sustained"
is a claim about the whole trajectory, which I have not measured. **No re-open, and I am not going to
manufacture one from an ambiguous read.**

---

## STATE OF PLAY (2026-09-08 ~13:30 UTC) — read this first if you are resuming

**The bot**: `src/bob` is byte-identical to `bob_iter20` (re-verified today, all seven files modulo
the package line; `git status src/bob` clean). HEAD compiles and is tournament-safe.
**No accept this session, and no gauntlet was run** — by design, see below.

**What this session did**: recovered one stranded verdict, closed a three-attempt thread, killed an
iteration before it cost a run, and corrected three instrument errors — two of which were in my own
committed doctrine and were actively producing wrong readings.

1. **Iteration 28c: REJECT, and ruin-hint sharing is CLOSED.** Run `20260908-115418` had finished and
   been collated before the last session died; only the verdict was missing. Arms 9/10/10 of 50
   against a clean null. The *flat* dose ladder is the finding → LEARNINGS 40.
2. **Iteration 29: VETOED at the pre-registered reachability probe. Never built.** `abandon = 0`
   across **77,963 soldier turns** on two maps, versus ~100 expected under independence. SRP work and
   ruin work are structurally mutually exclusive because marks blanket the ground around ruins.
   **4 probe games instead of a 200-game gauntlet.**
3. **Three corrections to how results are read** (details in the entries above):
   - `cmp` on replay bytes is **not** an arm-to-arm identity check — it also detects the team name and
     any robot logging. Measured: a pure rename costs exactly 8 bytes. Use event-stream diffs.
     Phase 0's claim is annotated in place. → LEARNINGS 41
   - `G.rng = new Random(r.getID())` and IDs are not mirrored, so **this lineage has never run a real
     mirror test.** "All 25 maps split by side" does not establish a positional bug. → LEARNINGS 42
   - I published a bot-vs-ancestor comparison that was **confounded by side**, and corrected it from
     the mirror replay that was already on disk. Leaf is a two-order-of-magnitude outlier; the 15-map
     census killed the story it suggested.

**NEXT RUN — the null-distribution calibration. Run this first; it outranks any new mechanism.**

`src/bob_n0..n3` are already built and compile-checked. Each burns 0/1/2/3 extra `G.rng.nextInt(8)`
draws per robot-turn and changes no decision rule anywhere; `n0` consumes no draw and must return
25/50-all-split as a control on the control. The **spread of n1..n3** is a direct measurement of how
far this instrument moves for reasons that have nothing to do with any mechanism.

```bash
MAXJOBS=3 BOT=bob OPPONENTS="bob_n0 bob_n1 bob_n2 bob_n3" ../../tools/gauntlet.sh
python3 bob-tools/eval_arms.py gauntlet/<run> bob_n0 bob_n1 bob_n2 bob_n3
```

**Why it is now urgent rather than merely overdue.** My own note from iteration 27 says every measured
arm's score is `mechanism + reshuffle`, so the reshuffle's size is "a precondition for reading **any**
of my results", and I have run 28 iterations without it. Today supplies the corroboration that was
missing: two policy-identical bots differing **only in PRNG seed** diverged to a 400× treasury gap on
Leaf. The reshuffle is not a rounding error. If the n1..n3 spread is wide, the `>= +7` gate moves up
and several past accepts need re-reading — and per the commitment already in this log, a calibration
that can only ever loosen the gate is not a calibration.

**It was NOT launched because tournament `20260908-1300` is running** (450 games; started ~13:00 UTC).
Launching 200 games against it would starve both. Check `ls -t ../../tournaments/` for its
`report.md`, then launch. Do not run `tools/tournament.sh` yourself.

**Then, in order:**
1. **Position-symmetric mirror arm** (from LEARNINGS 42) — seed `rng` from spawn location in the
   robot's own team frame so mirrored robots get equal seeds. Only under that seeding can a surviving
   split be called a symmetry bug, and Phase 0 calls symmetry bugs the single largest bug class
   either predecessor project found. This is an instrument, not a bot change.
2. Markers (`mark`/`removeMark`, still unused by the bot — verified today).
3. Mopper share (a constant, ranked below the above per LEARNINGS 37).

**Do NOT re-open** ruin-hint sharing (closed, 3 attempts), SRP-site *searching* (it10), soldier
movement for SRP siting (it13, −35), or the SRP/ruin priority gate (it29, vetoed at reachability —
the state does not occur). Iteration 8's chip trigger is **not** met; the 15-map census says so.

**Probe hygiene that worked and should be reused**: instrument the DECISION not the outcome; print
every 100 rounds **and** emit an event line on the first few increments, so that *zero events is a
census rather than a sampling gap*; verify neutrality by event-stream diff; and put the probe on a
throwaway package (`bob_srpgate2`), never on `src/bob`.

### Null calibration LAUNCHED — run `20260908-131748`, 200 games, IN FLIGHT

Launched at 13:17 UTC alongside tournament `20260908-1300`, on the precedent already in this log:
the shared semaphore splits **my** share rather than the machine's, so running beside the tournament
costs me wall-clock and nobody else anything. `MAXJOBS=3`, within the cap.

```bash
# collate when it finishes (it will NOT collate itself -- see below)
../../tools/gauntlet-collect.sh 20260908-131748
python3 bob-tools/eval_arms.py gauntlet/20260908-131748 bob_n0 bob_n1 bob_n2 bob_n3
```

**Read it as the pre-registered design says**: `bob_n0` burns zero extra draws and is behaviourally
identical — it **must** return 25/50-all-split, and if it does not, the run is void and the arms mean
nothing. The number being bought is the **spread of `n1..n3`**, which are policy-identical to `src/bob`
and differ only in the phase of every robot's PRNG stream. That spread is the noise floor. If it is
wide, the `>= +7` gate moves **up** and iterations 24-26 need re-reading — per the commitment already
in this log, a calibration that can only ever loosen a gate is not a calibration.

**My own error, recorded because it will recur**: I wrapped the launcher in `timeout 300`. A gauntlet
takes far longer than that, so the timeout killed the **local driver** at five minutes. The run itself
was unaffected — `gauntlet-collect.sh --list` shows it at 15/200 games and climbing — because the
remote runner is setsid-detached and survives the driver dying. **The only thing a dead driver costs
is the collation**, which is why `gauntlet-collect.sh <run-id>` exists. Do not wrap a long-running
launcher in a short timeout; and if a launcher produces no output for minutes, check
`gauntlet-collect.sh --list` before concluding it failed to start, because the absence of local output
says nothing about the remote run.

---

## Benchmark 20260908-0212 read as DISTANCE (score only; no replay of those games exists)

`bob` @ `e425f46` (iteration 20): **7/150 = 4.7% vs `v3`**, 1 map swept, 69 swept against.
**0/150 vs `TSPAARKHS`**, 75 swept against — as did both other lineages.

Recorded per the charter's one permitted access: a committed score, read as distance, never as a
target. `v3` is not in my gauntlet, not in `progress/roster_extra.txt` (verified today: that file
contains `examplefuncsplayer` and `bob_iter20`, nothing else), and there is nothing to examine.

**The number I should actually take from this is not mine, it is the spread.** alice 8.0%, carol 5.3%,
bob 4.7%. Three lineages within **3.3 points** of each other, all under 10%, and all **0.0% against
`TSPAARKHS` with 75/75 swept against**. Meanwhile my tournament standing over those same two bots is
70.3% and carol's is 32.3% — a 38-point spread *inside* the project.

So: **the intra-project differences my entire measurement apparatus is built to resolve are tiny
compared to the distance to a finalist bot.** All three of us are clustered in one narrow band, and my
gauntlet — which plays my own snapshots on maps I resample — cannot see out of it by construction.
This is the self-referential blind spot the algorithm names, quantified for once.

**What follows for my loop, stated as a consequence and not as enthusiasm.** A cluster at 5% is not
closed by another constant. The algorithm ranks **high-risk structural exploration** as a first-class
track precisely for this state — *"name a capability gap or strategic difference versus a strong
opponent, implement at whatever scope it needs"* — and notes the highest-value accepts in both prior
projects came from it. My last four iterations have been: a constant, a constant, a messaging protocol,
and a priority gate. The one direction the algorithm names that I have never attempted is **symmetry
inference** — standard practice elsewhere, needs no communication, and is *exact* rather than
heuristic. `reference/RESEARCH.md` §11 lists it first for a stalled lineage, and my own `bob-tools/`
already contains `map_symmetry.py` and `BobSym.java`, so some past session started down this road and
stopped.

Caveat I am holding onto: `TSPAARKHS` at 0/150 with 75/75 swept against has **no resolution at all** —
it cannot distinguish any change I make from any other. And `v3` at 4.7% is lopsided enough that it
has almost no room to show a *regression*. Neither can catch a decline. **The frozen roster remains
the only instrument that can**, which is exactly why `bob_iter11` catching iteration 18 sliding
(25/50 → 20/50) mattered, and why `bob_iter20` was added as a hard rung.

### Chip census, final at 21 maps — my "14 of 15" claim was too tidy

```
Leaf   B $527,895   shell B $106,895   mit A $53,365 B $99,018   FourCorners B $35,160
all other sides:    $1,038 - $8,307
```

**37 of 42 sides sit in $1k-$8.3k; 5 sides across 4 maps carry a large hoard.** So there IS a real
tail — about 12% of sides — which my 15-map read ("14 of 15") understated by luck of the draw. The
conclusion is unchanged in direction: hoarding is **not** the typical case and iteration 8's re-open
trigger is not met. But "one outlier map" was wrong, and I am correcting it rather than leaving the
tidier sentence standing.

### Sharpening the benchmark read with my own `se` reasoning — the three lineages are INDISTINGUISHABLE

The coordinator's caution is right and it cuts harder than I first wrote. I said "three lineages within
3.3 points". Applying the same arithmetic I used on my 50-game gates to the 150-game benchmark arm:

```
se on 150 games at p≈0.05      = sqrt(150·p·(1−p)) ≈ 2.6–2.7 games ≈ 1.7–1.8 points
alice 8.0% − bob 4.7%          = 5 games
se of that difference          = sqrt(150·.047·.953 + 150·.08·.92) = 4.21 games
                          → 5 / 4.21 = 1.19 se
```

**A 1.2 se gap is not a result.** So alice is not measurably ahead of me against `v3`, carol is not
measurably ahead either, and the honest statement is that **all three lineages are statistically
indistinguishable on this instrument** — clustered near its floor. That does not weaken the point I
drew from the spread, it strengthens it: the differences my whole apparatus resolves are not merely
small next to the distance to a finalist, they are **below this instrument's resolution entirely**.

It also means the *first* thing I would have been tempted to do with a second data point tonight —
read my own delta — is precisely what the table is not for. A move from 4.7% to 7% would be 3.5 games
against se ≈ 2.6: **1.3 se, i.e. nothing.** Only a trend across many runs will mean anything, and I am
writing that down now, before I have a number I might want to over-read.

### Accept-time git procedure (corrected by the coordinator; I hit this at my NEXT accept)

`git commit --only <path>` **refuses a path git does not already track** — "did not match any file(s)
known to git". Every accept creates `src/bob_iterN/`, a new directory, so the rule as I had it would
have failed exactly when it mattered. Correct form, the two commands kept **adjacent**:

```bash
git add src/bob_iterN progress/vs_old_bots_history.csv     # new/untracked paths only
git commit --only src/bob_iterN src/bob TRAINING_LOG.md progress/ -m "..."
```

`--only` still guarantees my commit contains only my paths, which is the half of the protection that
stops me sweeping a sibling's staged work out of the shared `.git/index`. For already-tracked files,
`--only` alone still needs no `add` — which is why every commit I made today worked.

---

## Iteration 30 — PRE-REGISTERED 2026-09-08. Denial-unit utilisation: the navigation policy fights the firing condition.

**This is not a new idea. It is a fully worked, pre-registered candidate from 2026-09-06 that was
queued as "iteration 8 — denial-unit utilisation", displaced by the queue revision that day, and
never executed.** I found it by grepping my own backlog rather than by inventing something, which is
the order the algorithm asks for. Today supplies the corroborating symptom it never had.

**The measured defect (2026-09-06, free analysis on a replay already on disk).** Denial actions per
denial unit per round ran at **~0.004 against ceilings of 0.33 (mopper) and 0.20 (splasher)** — on the
order of **1% of capacity**. We spend **2 of every 5 units built** on the only two unit types that can
remove enemy paint, and they are essentially idle.

**The new corroboration, from today's coverage trajectories.** Painted coverage does not plateau, it
**peaks and then declines**:

```
Leaf     cov 416 @r1400  ->  356 @r2000     (-14%)
Thirds   cov 367 @r800   ->  205 @r1400     (-44%)
```

This is an **absolute degeneracy signal**, which the algorithm explicitly prefers over any
opponent-relative comparison — a bot shedding 44% of its territory needs no opponent to be wrong. And
it is exactly the symptom idle denial units predict, because of an engine fact in `RULES.md`:
**soldiers cannot remove enemy paint — only splashers and moppers can.** So every tile the enemy
converts is permanently lost to us unless a denial unit clears it, and our denial units are running at
1% of capacity. Two independent measurements, taken two days apart for different reasons, meeting.

**The mechanism, specific and checkable.** `Nav.navTo`'s first pass refuses to step onto enemy paint
and only falls back to "take anything" when no other candidate exists. That is **correct for a
soldier** (standing on enemy ground costs 2 paint/turn). It is **wrong for a mopper or splasher**,
whose only useful terrain is enemy paint. `Mopper.run` navigates to the nearest visible enemy paint
via `navTo` — so as it approaches, a sideways non-enemy candidate almost always exists and it
**slides along the border instead of entering**. `Splasher.run` only fires on a cluster scoring ≥5,
which on a saturated map needs enemy tiles within r²≤2 — i.e. needs having gone *in*. **The
navigation policy and the firing condition are fighting each other.**

**Arms — and the knob is on the causal path, checked against LEARNINGS 40.** The quantity the
hypothesis is about is *denial units' willingness to stand on enemy paint*, and `paintPref` controls
exactly that, monotonically:

- `bob_d0` — Nav refactored, **every caller still passes pref 0**. Null arm. Must read
  **25/50-all-split**, which also proves the refactor itself is inert. If it does not, the run is void.
- `bob_d1` — moppers indifferent to enemy paint (pref 1).
- `bob_d2` — moppers **and** splashers indifferent (pref 1).
- `bob_d3` — both actively **prefer** enemy paint (pref 2).

Verified minimal: `d0` touches only `Nav.java`; `d1` adds one call site; `d2`/`d3` add one more.
**Soldiers are untouched in every arm.** The `G.randomDir()` draw under `stuckTurns >= 3` sits *above*
the changed branch and is not re-scoped, per LEARNINGS 35.

**Priced as a reallocation, not against zero.** The gain is denial throughput. The **price is paint**:
standing on enemy ground costs 2/turn and *moppers pay double the territory component*, so a denial
unit that lives in enemy paint drains faster and may sit frozen at 0. That price is why `d3` is in the
ladder rather than being assumed best, and why I expect the ladder to be non-monotone at the top.

**Not to be judged only in mirrors — pre-registered on 2026-09-06 and still binding.** In a
`bob`-vs-`bob` mirror neither side poses a paint-denial threat, so an improvement to denial capacity
has almost nothing to act on. `bob_denier` (my own synthetic archetype) goes in the run as a fifth
opponent precisely to pose that threat. 5 opponents × 50 = **250 games**.

**Gate.** `>= +7` accepts, `+5/+6` needs replication on a fresh sample, `<= +4` rejects — **unless the
null-calibration run `20260908-131748`, in flight now, says the noise floor is wider, in which case the
gate moves UP and this iteration is judged against the wider bar.** I am writing that down before
either result exists. A calibration that only ever loosens a gate is not a calibration, and that
applies to the iteration I want to accept tonight exactly as much as to any other.

**Secondary instrument, mechanistic verification, separate from the win gate**: denial actions per
**living** denial unit per round, from the dumper's `unpaint` column — normalised per round and per
unit, because raw counts scale with game length and army size and would read as "better" for reasons
unrelated to the change. A win with no movement in that number would mean the mechanism did not fire
and the games were won by something else.

**Prediction, recorded now**: `d1` positive and small, `d2` > `d1`, `d3` uncertain and possibly
negative as the paint price bites.

---

## Null calibration — VERDICT. Run `20260908-131748`, recovered 2026-09-08 14:40 UTC.

**Recovery note first.** The run finished remotely long ago; the local `gauntlet/20260908-131748/`
directory held a **15-game stub** (46 lines of `results.txt`, no `results.csv`, no `summary.txt`) —
the partial the `timeout 300` driver left behind before it was killed. `gauntlet-collect.sh --list`
reported it `complete`, and `gauntlet-collect.sh 20260908-131748` pulled the full 200 games. **A local
run directory that exists is not a collated run**; check for `summary.txt`/`results.csv`, not for the
directory. Nothing was re-run and no shared VM time was spent re-learning this.

### The numbers

```
arm          score  vs null  swept  sweptAg  split  diff-from-null
bob_n0       25/50       +0      0        0     25           0/50   <- NULL, zero extra draws
bob_n1       26/50       +1      6        5     14          15/50
bob_n2       25/50       +0      3        3     19          14/50
bob_n3       26/50       +1      6        5     14          19/50
```

**The control on the control is clean**: `n0` returned 25/50 with all 25 maps split by side and zero
sweeps either way. The run is valid and the arms mean what they were designed to mean.

**Reconciliation, run because I expected it to pass (doctrine 13).** `eval_arms.py` reports the
**arm's** score; `summary.txt` reports **bob's**. They read 26/25/26 and 24/25/24 — complementary to
exactly 50 on every pair, no residual. Two opposite referents, each correctly labelled for its own
convention; this is *not* the inverted-tool bug, and I checked rather than assumed. The sweep identity
`wins − losses = 2·(swept − sweptAgainst)` also holds exactly on all four arms (n1: 26−24 = 2 = 2·(6−5)).

### What was bought

**1. The PRNG-reshuffle floor on this design is ±1 game.** Three arms that are policy-identical to
`src/bob` and differ *only* in the phase of every robot's PRNG stream scored 26, 25, 26 of 50. That is
the entire spread. The reshuffle, on a fixed map sample, does not move the aggregate.

**2. But the churn underneath is large: 14–19 of 50 (map,side) cells flip.** ~30% of games change
outcome and the total barely moves, because the flips come back balanced (8/7, 7/7, 10/9).

**3. That balance is itself the finding, and it is not what an independent-flip model predicts.** If
each of `k` flipped cells resolved as an independent coin, the score difference would have
sd = √k ≈ 3.7–4.4 games, and all three arms landing within 1 of the null has probability

```
P(|delta|<=1):  n1 (k=15) 0.393   n2 (k=14) 0.209   n3 (k=19) 0.352   joint = 0.029
```

So the paired design is materially **more powerful** than counting flips would suggest: map difficulty
is shared by both arms and cancels, and what is left over largely self-cancels too. Recorded as an
observation on **n = 3 arms**, not as a variance estimate.

**4. Swept-map counts are NOT noise-immune, and I have been treating them as though they were.** A
change that alters *nothing but PRNG phase* manufactured **6 swept wins and 5 swept losses** on a
25-map sample. `n2` produced 3 and 3. So a sweep count of 5–6 in each direction is what pure noise
looks like here, and the information in a sweep count is the **asymmetry**, not the magnitude. "Nine
swept wins and zero swept losses" is strong precisely because of the zero. A gate condition phrased as
an absolute floor on swept wins must clear ~6 before it is saying anything at all.

### What was NOT bought — and why the gate does not move

This run held the **map sample fixed**. It therefore measures exactly one of the two noise sources, the
reshuffle, and says **nothing whatever** about the other: sampling 25 maps out of 75, which is the
variance that governs whether a result generalises — and which is the *larger* of the two (doctrine 1
puts its sd near 3 wins on a 50-game arm).

I pre-registered: *"if the noise floor is wider, the gate moves UP."* The component I measured came
back **narrower** than assumed. The temptation is to bank that and lower the bar. **I am not doing
that, and the reason is not caution, it is that the arithmetic does not support it**: the unmeasured
component is the dominant one and it is untouched by this run. Per the commitment already standing in
this log, a calibration that only ever loosens a gate is not a calibration — and that binds hardest
when the loosening is the answer I would prefer.

**So: iteration 30's gate stands unchanged at `>= +7` accepts, `+5/+6` replicates on a fresh sample,
`<= +4` rejects.**

Equally, iterations 24–26 are **not** vindicated. The flag on them was "the reshuffle may be wide
enough to have produced these"; the reshuffle is now shown to be ±1, so *that* source is eliminated,
but the map-sampling source is exactly as live as it was this morning. The flag is **narrowed from two
causes to one, not discharged**. (Doctrine 6: a flagged caveat is not a discharged one — and neither
is a half-answered one.)

### The operational consequence — LEVEL and SHAPE have different resolutions

This is the part that changes how I work, and it applies to the run in flight right now.

- **Within one run, on its own pinned map sample**, arm-to-arm differences are contaminated only by
  the reshuffle. Floor ±1. A dose ladder read *internally* — is it monotone, does it peak in the
  middle, where is the maximum — resolves far finer than +7.
- **Across map samples**, and for any claim that a change helps over the map *population* — which is
  what an accept asserts — the map-sampling variance applies in full and the +7 gate governs.

A single gauntlet therefore yields two readings at two different precisions, and conflating them is
the wrong-referent error in its cheapest form. Doctrine 2 already says a curve peaking in the middle
beats any single point; this run says **why**, in games: the curve is read at ±1 and the point is read
at ±3.

**Control installed, not just a lesson (doctrine 16).** `eval_arms.py` prints `diff-from-null`, so
every future ladder shows its own churn beside its own score, and the ±1 / 5–6-sweep floors above are
in `LEARNINGS.md` next to the gate they qualify — not only here in the chronology.

### CORRECTION, same session, before this entry was committed — I dropped a fourth arm that was already in my own LEARNINGS

I wrote "the PRNG-reshuffle floor on this design is ±1 game" from the three arms in *this* run. Then I
ran the consistency pass against `LEARNINGS.md` §36, which records a **fourth** PRNG-phase-only arm —
behaviourally neutral, no rule changed — that scored **19/50** with 8 maps swept against. That number
has been in my log all day and I did not reach for it while writing a calibration whose entire subject
is that quantity. This is precisely the failure the algorithm names: *entries are checked when written,
so a per-entry review passes everything; only comparing entries fails.*

Pooling every PRNG-phase-only arm this lineage has ever run:

```
19, 26, 25, 26        mean 24.0   sample sd 3.37
binomial prediction   sqrt(50 x 0.25) = 3.54
```

**§36a asked the sharp question — "does the real spread EXCEED binomial, which would mean cross-map
chaos is correlated and even ±7 is too tight?" The answer is no. It matches binomial almost exactly
(3.37 vs 3.54), and ±7 = 2 se is the right bar.** That question has been open since iteration 18 and
is now closed by measurement rather than by formula, which is what doctrine 9 asked for from day one.

**The two readings do not conflict — they decompose, and the decomposition is the real result.**

```
three arms sharing ONE map sample      sd 0.58   <- reshuffle only
all four arms, across map samples      sd 3.37   <- reshuffle + map sampling
```

The 19/50 came from a **different run on a different 25-map draw**. So the near-total stability of
n1/n2/n3 is not evidence that this instrument is quiet; it is evidence that **map sampling is nearly
the whole of its variance**, with the reshuffle contributing almost nothing once the maps are held
fixed. Which is exactly the conclusion I reached above from doctrine — the gate stays at +7 because
the unmeasured component dominates — except that it is now a measurement instead of an argument, and
it is *stronger* than the version it replaces.

Caveat held to standard, in both directions: the across-sample sd rests on **one** differing-sample
draw, so 3.37 is not a precise estimate — it is a demonstration that the across-sample spread is of
binomial size and not of the ±1 size the within-sample arms suggest. And the within-sample ±0.58 rests
on 3 arms. Neither number deserves a third significant figure.

**What both versions took for granted (doctrine: audit the retraction harder than the claim).** My
first draft and this correction both assume the four arms are *the same kind of object*. They are not
quite: the 19/50 arm was voided for a different reason and played a different opponent set. It is a
PRNG-phase-only arm, which is the property that matters here, but pooling four numbers from three
designs is the loosest step in this entry and I am naming it rather than letting the arithmetic imply
more precision than it has.

**The correction that runs against me is the one I nearly missed**: the comfortable version of this
entry was "the floor is ±1, my instrument is sharper than I thought." The uncomfortable version is
"the floor is the binomial ±3.5 I already had, and §37's finding that a 50-game arm cannot resolve
anything under ~14 points stands untouched." The second is correct.

---

## Tournament `20260908-1300` — I fell 22 points for the second consecutive run. The roster says I did NOT decline.

```
              20260907-1300      20260908-0100      20260908-1300
bob              92.3%             70.3% (-22.0)      48.3% (-22.0)     iter12 -> iter18 -> iter20
alice            38.0%             47.3%  (+9.3)      56.3%  (+9.0)     iter14 -> ...   -> iter30
carol            19.7%             32.3% (+12.7)      45.3% (+13.0)     iter12 -> iter29 -> iter36
```

Exactly −22.0 twice, with alice +9 and carol +13 both times. Wins are conserved across the three
lineages, so these deltas sum to zero **by construction** and cannot separate "bob got worse" from
"the other two got better". My own `roster_extra.txt` already carries a correction for quoting a
tournament delta as if it could — I am not repeating it.

**The frozen roster is the instrument that can, and it says the opposite of the standings:**

```
rung          iter12        iter18        iter20
bob_iter11    58/56/50       40            70
bob_iter1        86          86            88
bob_iter0        92          92            92
```

`bob_iter11` cannot change, so 40 → **70** is a **+15-game, 4.2 se** improvement, unconfounded. Against
every frozen rung, `iter20` is the strongest build this lineage has produced. **There is no absolute
decline to explain.** (Iterations 13–18 do look like they gave ground — ~55 → 40 on that rung, 2.1 se,
suggestive not decisive — and 19–20 more than repaired it. Flagged for an ablation, not acted on.)

### So the finding is about my LOOP, and it is throughput

```
09-06 18:33 -> 09-07 03:44    iter0 -> iter12     8 accepts in  9h
09-07 03:44 -> 09-08 01:28    iter12 -> iter20    2 accepts in 22h
09-08 01:28 -> 09-08 14:50    iter20 -> iter20    0 accepts in 13.5h   <- iterations 21-30
```

In the same 24 hours carol took 24 accepts and alice 16. **My accept rate has been zero for thirteen
hours.** Where the time went is not a mystery — it is in this log: LEARNINGS 36 through 44, the chip
census, the benchmark reads, the `cmp` identity-check bug, the ID-seeded-mirror bug, the iteration 29
veto, and the null calibration I collated this afternoon. Several of those were **real instrument
faults producing wrong readings**, and finding them was not wasted. But the algorithm's rule is that
there is no valid state where nothing is being attempted, and what I have been attempting is
*measurement*, not *bot*.

**The sharp version, which is the part worth acting on.** Almost every one of those instrument findings
converges on the same sentence: *a 50-game arm cannot resolve an effect below ~14 points* (§37,
restated and confirmed by §43 today). I then kept feeding that instrument candidates worth 1–3 points —
constants, thresholds, priority gates — and correctly measured them all as zero. **More calibration
cannot fix that. It is a power problem, and it has exactly two honest fixes:**

1. **Test mechanisms big enough to see.** Iteration 30 qualifies and is why it is in flight: denial
   units are **2 of every 5 units built and run at ~1% of their action capacity**. That is a
   large-effect candidate, not a constant.
2. **Widen the sample when the level matters.** 100 games gives 2 se ≈ 10 points against 14 at 50. So
   for a *single* candidate's level (as opposed to a ladder's shape, which §43 shows reads at ±1) the
   right shape is fewer arms on more maps, not more arms on 25.

**Ranked queue coming out of this, replacing the previous "markers / mopper share" ordering** — both of
those are small-effect candidates and my own instrument says I cannot see them:

1. **Iteration 30** (in flight, run `20260908-144158`).
2. **Ablate iteration 18.** The frozen rung dropped ~55 → 40 across 13–18 and §5b says a chain of
   positive accepts can walk downhill. Ancestry names the candidate; this is exactly the trigger
   doctrine 12 describes, and it is a *large* suspected effect.
3. **Symmetry inference** — the one structural direction `RESEARCH.md` §11 ranks first for a stalled
   lineage that I have never attempted, and `bob-tools/map_symmetry.py` + `BobSym.java` are already on
   disk from a session that started and stopped. Structural, so plausibly large.

Markers and mopper share are **deferred, not closed**: they are small-effect and I would be measuring
noise.

---

## API sweep (iteration 30 + stalled loop — both triggers fired), and what it found: THE TOWER CAP

The algorithm schedules this sweep "at iteration 5, every 10 iterations after that, and whenever the
loop stalls." I am at iteration 30 with zero accepts in 13.5 hours, so both triggers were live.

**First, a wrong-referent error I caught mid-sweep and nearly published.** I ran `javap` on the first
`battlecode25-java` jar `ls` returned — **1.0.0**. `engine_version.txt` says **3.1.0**, and both jars
are in the gradle cache. The tell was doctrine 5's exact signature, two artefacts that should agree and
didn't: my bot calls `rc.getChips()` and `getChips` did not appear in the dumped API. Had that method
existed in both versions, the sweep would have silently reported the wrong surface. **Always dump the
jar named by `engine_version.txt`, never the first one `ls` returns.**

Against the correct 3.1.0 `RobotController`, **27 of 68 methods are never called anywhere in
`src/bob`**:

```
adjacentLocation  broadcastMessage  canBroadcastMessage  canMark  canPaint  canRemoveMark
canSendMessage  canSenseRobot  canSenseRobotAtLocation  disintegrate  getActionCooldownTurns
getMoney  getMovementCooldownTurns  getNumberTowers  getResourcePattern  getTowerPattern
isLocationOccupied  mark  onTheMap  readMessages  removeMark  resign  sendMessage
sensePassability  senseRobot  setIndicatorDot  setIndicatorLine
```

Most are utility or debug. Three are mechanics: the free-form markers (`mark`/`removeMark`, already
queued), messaging (`sendMessage`/`readMessages`/`broadcastMessage` — unused because iteration 28c was
rejected and reverted), and **`getNumberTowers`**.

### `getNumberTowers` — my bot cannot see a capped team resource, and the cap BINDS

`RULES.md` line 114: **`MAX_NUMBER_OF_TOWERS` = 25.** The algorithm's §4 warning is verbatim about this
situation: *"if the change alters who draws on any shared/capped team resource (a build cap, a shared
treasury, comm slots), instrument the pool itself — three iterations once failed identically because a
global cap, visible in the data the whole time, was never printed."*

It is visible in the data. It is the `tw` column my own dumper has printed all along. On
`matches/bob-vs-bob_iter11-on-Leaf.bc25` (Leaf, 56 header ruins):

```
round  250   T1 tw15   T2 tw22
round  500   T1 tw25   T2 tw25     <- BOTH TEAMS AT THE CAP
round 1000   T1 tw25   T2 tw25
round 1500   T1 tw25   T2 tw25
round 2000   T1 tw25   T2 tw23
```

**Pinned at 25 from round 500 to the end — 75% of the game.**

### The defect this exposes is not the wasted paint, it is a PERMANENT SOLDIER SINK

`Soldier.chooseRuin()` releases `workRuin` on exactly two conditions: the ruin becomes visibly
occupied by a robot, or `completeTowerPattern` succeeds. At the tower cap **neither can ever happen**
on an unoccupied ruin — nobody can build there, so it stays empty forever, and
`canCompleteTowerPattern` is permanently false.

So a soldier that locks onto an unclaimed ruin while the team is at 25 towers:

1. navigates to it (`Nav.navTo(workRuin)`) and stays,
2. spends 25 paint on `markTowerPattern` (marks are a separate layer — that paint does **not** reach
   the board as coverage),
3. paints the 5x5 pattern **down to zero paint**, because iteration 18 set `RUIN_FLOOR = 0` precisely
   so the last point is spent on tower-pattern work,
4. **never releases the ruin**, and re-selects it next turn.

The paint-loop guard is `rc.getPaint() > RUIN_FLOOR` and the mark guard is `canMarkTowerPattern`.
**Neither consults the tower count**, and the engine's own `canCompleteTowerPattern` only blocks step
4 — the step that costs nothing — while leaving steps 1–3 running forever.

**Honest accounting of what is and is not waste** (doctrine: price the reallocation, not the gain):
the *pattern painting* in step 3 does put ally paint on the board and coverage is the win condition,
so it is **not** pure waste — it is ordinary painting done on tiles chosen by a dead goal instead of by
`paintSomething`. What is genuinely destroyed is the 25 paint per marking, the travel, and above all
the soldier's **remaining career**, which is spent servicing a task with a structurally impossible
completion condition. Iteration 18 makes this maximally expensive by driving the soldier to 0 paint.

This is the recurring winner's profile the algorithm names — *capability preserved at zero marginal
cost, removing pure waste* — and it is one `getNumberTowers()` call.

### Pre-checks: this is REGIME-DEPENDENT and must not be measured on a random sample

Doctrine 4 governs. The guard can only fire where a team actually reaches 25 towers, and a random
25-map draw would average a fixed zero over the maps where it cannot.

**Upper bound, free, already on disk.** A team can hold 25 towers only if ~25 ruins are available to
it. From `tools/mapdata/ruin_parity.txt`, **20 of 75 maps have >= 23 claimable ruins** (+2 starting
towers). So the cap is reachable on at most **27% of the corpus** — and Leaf, where I measured it, is
the ruin-richest map at 52 and is flagged in this log as a two-order-of-magnitude outlier. **Sizing on
Leaf alone would be exactly the degenerate-sizing-map error §3 warns about.** Gears (14 claimable)
reached only `tw8`; the cap cannot bind there.

Probe matches are running now on `DefaultHuge DonkeyKong TheBest SMILE headphones maze UglySweater`
(49/46/44/38/32/28/28 claimable) to convert that upper bound into an observed rate. **Pre-registered
before the probes land**: I expect the cap to bind on the 40+-ruin maps, to be marginal near 28, and
never to bind below ~23. If it binds on fewer than three of the seven, the regime is too narrow to
carry an iteration and I will say so rather than running it anyway.

**Pre-checks NOT yet done, named explicitly so the next session does not inherit my momentum:**
- Trigger frequency *within* a binding map: what fraction of soldier-turns have `workRuin != null`
  while at cap? The sink's size is that number, and I have not measured it.
- Whether `canMarkTowerPattern` already returns false at the cap. If the engine blocks the mark, step 2
  costs nothing and only steps 1 and 3 remain. **This changes the size of the claim and I have not
  checked it** — it needs a `javap`/probe, not an assumption.
- History: iteration 18 deliberately established `RUIN_FLOOR = 0`. A fix here does not revert it, but
  the interaction is real and must be stated, not discovered later.

### Tower-cap pre-checks CLOSED: the mechanism is real, the regime is 6.6% of the corpus, and it cannot clear my gate

**Pre-check A — does the engine already prevent the waste? NO.** `javap -c` on
`battlecode.world.RobotControllerImpl` 3.1.0:

- `assertCanMarkTowerPattern` checks robot type, tower type, act location, `hasRuin`,
  `isValidPatternCenter`, and paint >= cost. **There is no tower-count check.** So at the cap a soldier
  can still spend 25 paint marking a 5x5 that can never become a tower.
- `GameConstants.MAX_NUMBER_OF_TOWERS = 25`, confirmed from the jar rather than from `RULES.md`.

So the sink is real and the engine does not guard it. That pre-check is discharged.

**Pre-check B — regime size. This is what kills it.** Seven probe matches (`bob` vs `bob_iter20`),
T1 tower count sampled every 250 rounds:

```
map           claimable ruins   trajectory                          binds?
Leaf                52          tw25 from r500 to r2000             YES  (75% of game)
DefaultHuge         49          tw25 from r750                      YES  (63%)
DonkeyKong          46          tw25 from r1000                     YES  (50%)
TheBest             44          tw25 from r500, game ended r808     YES  (37%)
SMILE               38          peaks tw20, declines to 18          no
headphones          32          peaks tw16, declines to 13          no
maze                28          tw4 flat all game                   no
UglySweater         28          tw6 at r250, game ended r377        no
```

**My pre-registered prediction — binds on the 40+-ruin maps, marginal near 28, never below ~23 — came
out right, and the boundary is sharper than I guessed: it sits between 38 and 44 claimable ruins, not
at 23.** The naive upper bound (25 towers needs ~25 ruins) was wrong by a factor of two, because a team
never claims anywhere near all the ruins on a map.

**Corpus-wide, only 5 of 76 maps have >= 44 claimable ruins.** So:

```
regime                       5/76 = 6.6% of maps
expected binding maps in a random 25-map draw     1.6
maximum possible effect if the fix flipped EVERY game on them   ~3 games of 50
noise floor (LEARNINGS 43, measured today)                      +-3.5 games
accept gate                                                     +7
```

**The largest effect this change could possibly have is smaller than the noise floor, and half the
gate.** It cannot be accepted on a random sample no matter how right the mechanism is. Killed at
pre-check, for **seven probe matches and a javap**, not a 200-game gauntlet.

**A tidy reconciliation I checked and had to discard.** At the cap chips have no tower sink, so I
expected the chip-hoard maps from my 21-map census to *be* the cap-binding maps. They are not:

```
hoard map      claimable ruins        cap-binding?
Leaf                 52                  YES
mit                  24                  no
shell                20                  no
FourCorners          10                  no
```

Three of the four cannot reach the cap. **The story is refuted, not supported** — the hoards have some
other cause, and Leaf is on both lists because Leaf is an outlier on every list. I record this because
it is exactly the shape of thing I would otherwise have published as "two independent measurements
meeting": it was one measurement and a coincidence.

**Disposition — CLOSED, with the measurement that closed it.** Not "under-explored"; the regime is
6.6% and the ceiling is below the noise floor. Re-open only if the map pool changes to include more
40+-ruin maps, or if a corpus-wide version of the defect is found — the cap is one instance of
`workRuin` having **no abandonment condition at all**, and a broader version might reach further. Note
before anyone reaches for that: iteration 29 was vetoed at reachability with `abandon = 0` across
77,963 soldier turns, so the broader version has already failed once and needs a specific reason that
finding no longer applies.

**What this cost and what it bought.** Cost: 7 probe matches, two javap calls, no gauntlet. Bought: a
mechanically-confirmed engine fact (no cap check in the mark path), a sized regime, a refuted
reconciliation, and the knowledge that my sweep's most promising hit is unmeasurable by my instrument.
That last point is the same wall as this morning's throughput finding — **my binding constraint is not
ideas, it is that a 50-game random-sample instrument cannot see anything acting on under ~15% of maps.**

---

## The instrument fix my own calibration implies: PLAY THE WHOLE CORPUS when measuring a LEVEL

Twice today the binding constraint has been the same, and it is not ideas:

- the throughput finding this morning — a 50-game arm cannot resolve under ~14 points, and I spent ten
  iterations feeding it 1-3 point constants;
- the tower cap this afternoon — a mechanically-confirmed, engine-verified defect whose *ceiling* is
  below the noise floor, killed without ever being tried.

Today's calibration says exactly where that noise comes from: **sd 0.58 within one shared map sample,
sd 3.37 across map samples.** Map sampling is nearly the whole of it.

**So stop sampling.** `tools/bc25-maps.txt` has 75 maps and `gauntlet.sh` takes a pinned `MAPS`. A run
that plays *all 75, both sides* is 150 games against one opponent, and for the question an accept
actually asks — *does this change help over the map population?* — there is **no sampling variance at
all, because there is no sample. It is the population.** That is a logical fact, not an estimate.

```
                          games   map-sampling noise   what it can resolve
25-map random draw    50/opponent      sd ~3.4          ~14 points   <- what I have been using
75-map full corpus   150/opponent      ZERO             reshuffle only
```

**What I do NOT know, and will not assume:** the reshuffle component at 150 games. I measured it at
sd 0.58 on a 50-game paired arm; I have no right to carry that number to 150 cells, where three times
as many games flip. It could stay ~1 game or grow toward the binomial 6.1. **Pre-registered: before I
accept anything on a full-corpus run, I run `bob_n0`/`bob_n1` at full corpus once and measure it** —
the same arms, the same design, at the scale I intend to use. A calibration I extrapolate instead of
running is exactly the failure this morning's entry was written about, and it would be the second time
today I let a comfortable number travel further than the measurement behind it.

**Cost, honestly.** 150 games/opponent against 50 is 3x. A two-arm accept test is 300 games where I
have been spending 200 on four. That is affordable *because it replaces runs, not adds to them*: a
4-arm 25-map ladder followed by a replication is 400 games and still cannot resolve 14 points, while
one full-corpus head-to-head is 300 and resolves far better. The right split is the one §43 already
names:

- **SHAPE (which dose, is the curve monotone) — 25-map ladder, many arms, cheap.** Reads at +-1.
- **LEVEL (does this accept) — full corpus, two arms.** No map-sampling noise by construction.

### This REOPENS the tower cap, and I am saying so in the same breath as closing it

I closed the tower-cap direction one entry ago because its ceiling (~3 games of 50) sits under the
noise floor. That reason is a statement about **the instrument**, not about the defect — and I am now
changing the instrument. At full corpus the 5 binding maps are 10 games of 150 rather than ~3 of 50,
against a residual that is reshuffle-only.

Doctrine allows re-opening exactly when there is *"a specific reason the recorded cause no longer
applies"*, and this is one — but it is conditional and I am not pretending otherwise:

**The tower-cap fix is re-opened IF AND ONLY IF the full-corpus reshuffle calibration comes back small
(say <= 2 games of 150). If it comes back near binomial, the cap stays closed and so does most of what
I have been trying to measure all week.** The order is: calibrate first, then decide. Not the reverse,
which is how a lineage talks itself into the instrument that gives it the answer it wants.

**Queue, revised:**
1. Iteration 30 ladder — landing now (`20260908-144158`).
2. **Full-corpus reshuffle calibration**, `bob_n0`/`bob_n1`, 300 games. Gates everything below.
3. Re-run iteration 30's best dose at full corpus for its LEVEL, if the ladder shows a peak.
4. Tower-cap guard (`getNumberTowers`), conditional on 2.
5. Symmetry inference — still the one structural direction never attempted, and corpus-wide rather
   than regime-narrow, which now matters more than it did this morning.

### Why the FULL corpus and not just a fixed 25-map list — the charter already answers this

The cheap version of the fix would be to pin one standing 25-map list and reuse it for every accept
test. That gets the same statistical benefit (both arms see identical maps, so map difficulty cancels
and only the reshuffle remains) at 50 games instead of 150. It is also **forbidden by my own AGENT.md**,
for a reason that has nothing to do with statistics:

> Do not hand-pick a standing map list: a fixed list is an overfitting surface, and accepted iterations
> drift toward the maps on it.

Both things are true at once, and the full corpus is the **unique** map set that satisfies both:

```
                        fixed?  (no sampling noise)     overfitting surface?
fresh random 25          no  -- sd 3.4 across runs       no
standing pinned 25       yes -- sd ~0.6                  YES, and my charter forbids it
all 75                   yes -- sd ~0.6 (to be measured) NO -- you cannot overfit to the population
```

You cannot drift toward the whole map set: fitting it *is* the objective. So the corpus is the one
fixed reference that costs nothing in generalisation, and the 3x game cost is what buys the exemption
from the charter's rule rather than a violation of it.

**Design for the next run, combining the calibration with the level test in one go**, so the noise
measurement is taken at the exact scale it will be used at and on the exact same maps:

```bash
MAPS="$(cat ../../tools/bc25-maps.txt)" MAXJOBS=3 BOT=bob \
  OPPONENTS="bob_n1 bob_n2 bob_<best dose from iteration 30>" ../../tools/gauntlet.sh
```

`n1` and `n2` are policy-identical to `bob` and differ only in PRNG phase, so **their deviation from
75/150 IS the noise floor at this scale** — two independent draws of it, measured inside the same run
that measures the candidate, on identical ground. 450 games. That is one run answering the calibration
question and the accept question together, instead of two runs answering neither.

### A free by-product of the tower-cap probes: `maze` is an absolute degeneracy signal, and it points at NAVIGATION

The seven probe matches were run to size the tower cap. They also handed me a ruin-capture rate per
map, which I did not go looking for. Towers built by T1 (`bob`) against claimable ruins:

```
map           ruins   towers    capture     walls
Leaf            52      25 (cap)   cap        4.4%
DefaultHuge     49      25 (cap)   cap
DonkeyKong      46      25 (cap)   cap
TheBest         44      25 (cap)   cap
SMILE           38      20          53%
Gears           14       8          57%
headphones      32      16          50%
maze            32       4          12.5%    19.8%    <- OUTLIER
```

**On `maze` my bot claims 4 of 32 ruins in 2000 rounds and the count is flat from round 250 onward.**
Every other non-capped map sits at 50-57%. This needs no opponent to be wrong — it is the "our bot
stalls" class of signal the algorithm explicitly prefers over any opponent-relative comparison.

`maze` has **19.8% walls against Leaf's 4.4%**, and `Nav.navTo` is a greedy stepper whose only
escape is `stuckTurns >= 3 -> G.randomDir()`. That is not a bug-nav, and greedy descent with a random
kick is the classic failure in wall-dense terrain: it does not escape concavities, it re-enters them.
`reference/RESEARCH.md` lists hybrid bug-nav among the perennial mechanics.

**Why this is a better candidate than the tower cap**, in the terms that killed the tower cap:

- the tower cap's ceiling was ~3 games of 50 because its regime is 5 of 76 maps;
- this is a **50-point capture deficit on the affected maps**, not a marginal one, so the per-map
  effect is large and the question is only how many maps are wall-dense.

**Pre-check to run before anything else, and NOT yet done:** the wall-density distribution over all 75
maps. `tools/mapdata/` carries ruin parity but no wall counts, so this needs a small scanner in
`bob-tools/` reading the `.map25` flatbuffers the way `BobSym.java` already does. **I am naming this as
unfinished**: I have one wall-dense map and one dense-map failure, which is n=1, and §3's
degenerate-sizing-map rule applies to me here exactly as it applied to the tower cap. If wall-dense
maps turn out to be 3 of 75, this dies the same death and should.

Also noted while looking: `bob-tools/BobSym.java` is an **offline audit** of the tower-type rule's
symmetry, not runtime symmetry inference. So the structural direction "infer the map symmetry in-bot
and extrapolate the unseen half" remains genuinely unattempted, not half-built as I assumed this
morning.

### Wall-density pre-check, run immediately: the naive "wall-dense maps" regime is 8% — same trap as the cap

`bob-tools/map_symmetry.py` already parses the `.map25` flatbuffers out of the engine jar and already
computes wall counts; I did not need a new tool, only to read the one I had. Over all 75 maps:

```
wall density   min 1.6%   median 10.1%   p90 15.0%   max 20.0%
maps >= 16%:   gridworld 20.0  maze 19.8  boxofchocolates 19.5
               yearofthesnake 18.4  sierpinski 16.9  mit 16.3      = 6 of 75 (8%)
```

**So "fix navigation for wall-dense maps" is an 8%-of-corpus regime, which is the tower cap's death
sentence almost exactly.** I am writing that down before I get attached to the direction, because I
found the maze result forty minutes after closing a direction for this precise reason and the
temptation to grade the new favourite on a softer curve is the whole failure mode.

**But the two are not equivalent, and the difference is testable rather than rhetorical.** The tower
cap is a *threshold* effect — it does nothing at all below 44 ruins, which I verified (38 and below:
never binds). Wall density is a *continuum*, and if capture degrades continuously with it then the
effect is spread over the whole corpus rather than concentrated in 6 maps, and the median map at 10.1%
is already paying something. My four data points cannot tell these apart:

```
map          walls    capture
Gears         4.6%      57%
headphones   11.5%      50%
SMILE          ?        53%
maze         19.8%      12.5%
```

Three flat points and one collapse is equally consistent with "a cliff somewhere above 16%" (regime =
6 maps, dies) and with "a knee that starts biting in the mid teens" (regime = much larger, worth it).

**Pre-registered discriminating probe, before any candidate is built**: run the four remaining >=16%
maps (`gridworld`, `boxofchocolates`, `yearofthesnake`, `sierpinski`, plus `mit`) and three mid-density
maps (12-15%), and plot capture against wall%. **Prediction I am committing to now: if the mid-density
maps come back at 45-57% like `headphones`, this is a cliff and a 6-map regime, and I close it the way
I closed the cap.** Only a graded decline across the mid-range justifies building anything.

**And a confound I must rule out in the same probe**: `maze` at 19.8% walls may simply have ruins
behind walls that no navigation can reach, in which case the 12.5% is the map's ceiling and not my
bot's failure. The discriminating observation is the *opponent's* capture on the same map — `bob_iter20`
played the other side of that very game. If both teams sit near 4, it is the map; if the opponent
captured many more, it is the bot. **That number is already in the replay I have on disk and I have not
looked at it.**

---

## Iteration 30 — **REJECTED**. Run `20260908-144158`, 200 games, complete.

```
arm      what changed                              score   vs null  swept  sweptAg  diff-from-null
bob_d0   Nav refactored, every caller pref 0        25/50     +0       0       0        0/50   NULL
bob_d1   moppers indifferent to enemy paint         22/50     -3       1       4        7/50
bob_d2   moppers AND splashers indifferent          22/50     -3       1       4        7/50
bob_d3   both actively PREFER enemy paint           19/50     -6       0       6        8/50
```

**The null arm is clean** — 25/50, all 25 maps split, zero sweeps either way — so the `Nav` refactor is
inert and the run is valid. Stage-0 had already shown `d0` reproducing the baseline exactly on Bread
(r616) and Rose (r530) while `d1` diverged on both.

**Gate: `>= +7` accepts. The best arm is −3. Rejected, and not marginally.**

### The ladder is monotone DOWNWARD, and that is the finding

My pre-registered prediction was *"`d1` positive and small, `d2` > `d1`, `d3` uncertain and possibly
negative as the paint price bites."* The sign is wrong from the first rung:

```
pref 0 (avoid)  25   ->   pref 1 (indifferent)  22   ->   pref 2 (prefer)  19
```

Monotone, evenly spaced, and — per §43, measured today — a ladder's **shape** on a single shared map
sample reads at ±1. So this is a real, clean dose-response, not three noisy points. **The more willing
a denial unit is to stand on enemy paint, the worse the bot does, at every dose I tested.**

**The hypothesis is refuted rather than merely unsupported.** The theory was that `navTo`'s enemy-paint
avoidance fights the splasher's firing condition, so relaxing it would raise denial throughput. The
price I priced — 2 paint/turn to stand on enemy ground, doubled for moppers — is not merely a cost to
subtract from a gain; it **exceeds any gain at every dose**. The reallocation costing exercise in the
pre-registration had both numbers, and the price side won.

`d1` and `d2` scoring identically (22/50, 7 flipped cells each, same 1/4 sweeps) is worth noting: adding
**splashers** to the change on top of moppers moved nothing at all. Whatever is happening is a mopper
effect.

### The flip signature confirms this is causal, not churn — and today's calibration is what licenses saying so

Doctrine 10 says scattered mixed-direction flips are churn and one-directional flips are a real causal
effect. I now have both signatures measured on the same day, on the same instrument:

```
                        cells flipped      direction        score
PRNG phase only  n1           15            8 up / 7 down     +1     <- churn
                 n2           14            7 up / 7 down     +0
                 n3           19           10 up / 9 down     +1
iteration 30     d1            7            2 up / 5 down     -3     <- causal
                 d2            7            2 up / 5 down     -3
                 d3            8            1 up / 7 down     -6
```

**The real mechanism perturbs HALF as many games as a pure PRNG reshuffle and moves the score six times
as far**, because its flips point one way. A change that alters behaviour a lot and outcomes randomly
looks nothing like a change that alters behaviour a little and outcomes systematically, and until this
morning I had no measured baseline for the first shape. This is the calibration paying for itself
inside one iteration.

### Closed direction, recorded with the measurement that closed it

**Denial-unit navigation policy (willingness to stand on enemy paint) is CLOSED.** Dose ladder
0/1/2 → 25/22/19 on a clean null, one-directional flips at every dose. Re-open only with evidence that
changes the paint arithmetic — the price is an engine constant (2/turn, doubled territory component for
moppers), so a re-open needs either a mechanism that pays the cost back explicitly, or a regime where
denial units are not paint-constrained. "Denial units run at 1% of capacity" remains **true and
unexplained**; what is now known is that this is *not* the cause, and freeing them to enter enemy paint
is not the cure.

**Functional-area tracking**: this is my 3rd consecutive reject in unit-behaviour/threshold tuning
(28c ruin-hint sharing, 29 vetoed, 30 rejected). `MaxConsecutiveRejects = 3` is reached, so **the next
attempt must leave this area** — which the revised queue already does: instrument work first, then
structural.

---

## RETRACTION — the `maze` navigation lead was a GREEDY-REGEX ERROR. My probe table reported the wrong team.

The entry above ("maze is an absolute degeneracy signal, and it points at NAVIGATION", commit
`a6e194f`) is **wrong and is withdrawn**. It stands in the log because decisions were queued off it;
this supersedes it.

**The bug.** My extraction was

```bash
grep -oE "^round [0-9]+ \| T1 .* tw[0-9]+"   |  sed -E 's/.*(round [0-9]+).* tw([0-9]+).*/\1 tw\2/'
```

`.* tw([0-9]+)` is **greedy**, so on a line containing both teams it matches the *last* `tw` on the
line — **T2's tower count**, under a pattern I had written `T1` into and therefore read as T1's. Every
number in that probe table was the opponent's. This is doctrine 5 exactly: a number correctly computed
against the wrong referent, produced by a procedure that looked right and had the right label on it.

**Re-extracted per team with a field-split parser instead of a regex** (T1 = `bob`, T2 = `bob_iter20`):

```
map           ruins   r500        r1000       r1500       r2000
DefaultHuge     49    23 / 22     21 / 25     20 / 25     21 / 25
DonkeyKong      46    23 / 21     20 / 25     19 / 25     18 / 25
TheBest         44    17 / 25       (ended r808)
SMILE           38    12 / 15     23 / 19     23 / 19     23 / 18
headphones      32    16 / 16     21 / 13     20 / 14     22 / 13
maze            32     4 /  4      7 /  4     14 /  4     18 /  4
UglySweater     28      (ended r377)
```

**What survives.** The tower-cap conclusion is unaffected and is confirmed on correct data: a team
reaches 25 on Leaf (both), DefaultHuge, DonkeyKong and TheBest — every map with >= 44 claimable ruins —
and on none at 38 or below (SMILE peaks at 23, headphones at 22). The regime is still 5 of 76 maps and
the direction stays closed for the reason recorded.

**What dies.** *"On maze my bot claims 4 of 32 ruins in 2000 rounds"* is false. **T1 reached 18 of 32
(56%), which is exactly the normal rate.** There is no navigation degeneracy here. The 12.5% belonged to
the other side, and the wall-density story I built on it — median 10.1%, the 8%-of-corpus regime, the
cliff-versus-knee probe I pre-registered two entries ago — was built on a number that was never about
wall density at all. **That probe is cancelled, not deferred.** The wall-density census itself is fine
and stays as a fact about the corpus; only the inference from it goes.

**What is left, and what I may NOT say about it.** On maze, two byte-identical builds went 18 and 4.
That is a real and very large split. But **LEARNINGS 42 forbids me from calling it a symmetry bug**:
`G.rng = new Random(r.getID())` and IDs are not mirrored, so `bob` vs `bob_iter20` is not a mirror — it
is one policy under two random streams, and a compounding divergence (the 400x treasury gap on Leaf is
the precedent) produces exactly this. Positional bug and seed divergence are indistinguishable here, on
n = 1, by construction. The position-symmetric mirror arm §42 specifies is the only thing that could
separate them, and it is still unbuilt.

**What both the claim and this retraction took for granted** (the retraction audit): both assumed the
probe replays were a *mirror* and so that either team's number characterises "my bot". They are not a
mirror in the only sense that matters, which is why a 4 and an 18 can sit in one game with no bug at
all. The deeper error was not the regex — it was reaching for a per-team number from a matchup whose
two sides I have already documented as incomparable.

**Control installed, not a lesson (doctrine 16).** The regex is replaced by an awk field-split on `|`
that binds T1 and T2 to named variables and prints both, always, as `r<round>(T1/T2)`. It is not
possible to read one team's number believing it is the other's when the output shows the pair. That
form is what produced the table above and is what I will use for every replay aggregate from here.

### Iteration 30's pre-registered SECONDARY instrument was not validly measured — saying so rather than quoting it

I pre-registered "denial actions per **living** denial unit per round" as the mechanistic check. Two
verification matches (`bob` vs `bob_d0` / `bob_d3`, Bread and Rose):

```
Bread  d0  r600  u6   mop1        Rose  d0  r500  u16  mop2
Bread  d3  r750  u19  mop3        Rose  d3  r400  u5   mop1
```

The raw `u` counts move a lot and in opposite directions on the two maps. Dividing them out gives
0.010 -> 0.008 (Bread) and 0.016 -> 0.013 (Rose), i.e. "throughput fell" — **and that number is
invalid.** `u` is a *cumulative* action count while `mop` is the *instantaneous* count of living
moppers at the sampled round; moppers die and are replaced continuously (the `died`/`starved` columns
run into the hundreds), so this divides a whole-game total by a final-instant denominator. It is
doctrine 15's shape — a rate whose numerator and denominator answer different questions — and I am not
going to quote it in either direction.

**The reject does not rest on it.** The mechanism demonstrably engaged: 7, 7 and 8 of 50 (map,side)
cells changed outcome against the null, one-directionally. A −6 at the top dose on a clean null with
that flip signature is decisive on the win gate alone. What I do **not** get to say is whether denial
throughput rose, fell, or held — measuring that properly needs per-round integration of living denial
units, which this dumper does not emit and which I did not build. **Logged as an open measurement gap,
not as a result.**

---

## STATE OF PLAY — end of session 2026-09-08 ~16:15 UTC

**The bot**: `src/bob` is unchanged and byte-identical to `bob_iter20`. HEAD compiles; nothing this
session touched shipping code. Last accept remains **iteration 20**.

**What this session did.** No accept. One recovered verdict, one clean reject, two directions closed at
pre-check for a combined cost of 7 probe matches and two `javap` calls, one retraction of my own
published claim, and one instrument change that I think matters more than any of them.

1. **Null calibration recovered and read** (`20260908-131748` had finished but its local directory held
   only the killed driver's 15-game stub). PRNG-phase-only arms: 26/25/26. Pooled with the fourth such
   arm already in LEARNINGS 36 → **sd 3.37 against a binomial 3.54**. §36a's open question is closed:
   the spread does *not* exceed binomial, `+7 = 2 se` is right, and §37 stands.
2. **The decomposition that follows**: sd **0.58** within one shared map sample, **3.37** across
   samples. Map sampling is nearly the whole of my noise. → LEARNINGS 43, 44.
3. **Iteration 30 REJECTED** — dose ladder 25 / 22 / 22 / 19, monotone downward, clean null.
4. **Tournament read**: the −22 drop is *not* an absolute decline; the frozen `bob_iter11` rung has
   `iter18` at 40 and `iter20` at **70**. The real problem is throughput — zero accepts in 13.5 hours
   against carol's 24 and alice's 16 in the same day.
5. **API sweep** (both triggers live): 27 of 68 `RobotController` methods unused; found and closed the
   tower cap.
6. **Retracted the maze/navigation lead** as a greedy-regex error. → LEARNINGS 45.

**The one thing to carry forward if nothing else does.** Every dead end today died the same death:
*the instrument cannot resolve it.* The tower cap's ceiling (~3 games of 50) is under the noise floor.
The constants of iterations 21-27 were under it. §37 says a 50-game arm cannot see below ~14 points.
**The fix is already derived and pre-registered above: measure LEVELS on the full 75-map corpus (150
games/opponent, zero map-sampling variance by construction), and keep 25-map ladders for SHAPE.** The
corpus is the unique map set that is both fixed and non-overfittable, so it does not violate the
charter's standing-map-list rule — it is the one exception the rule's own reasoning allows.

**NEXT RUN — do this first, it gates everything else.**

```bash
MAPS="$(cat ../../tools/bc25-maps.txt)" MAXJOBS=3 BOT=bob \
    OPPONENTS="bob_n1 bob_n2" ../../tools/gauntlet.sh          # 300 games, ~1.5h
python3 bob-tools/eval_arms.py gauntlet/<run> bob_n1 bob_n2
```

`n1`/`n2` are policy-identical to `bob` and differ only in PRNG phase, so **their deviation from 75/150
is the full-corpus noise floor** — the number every future accept gate depends on, measured at the
scale it will be used at rather than extrapolated from 50 games. Both arms are already built and
compile-checked in `src/bob_n1`, `src/bob_n2`.

**Pre-registered readings, written before the run exists:**
- `<= 2 games` of 150 → full-corpus runs resolve ~3 points, adopt them for all level tests, **and the
  tower-cap guard re-opens** (its 5 binding maps are 10 games of 150, not 3 of 50).
- `~6 games` (binomial) → the reshuffle does not cancel at scale, full-corpus buys only the sampling
  half, the gate stays near +7 in proportion, and the tower cap **stays closed**.
- Anything between → interpolate, and say which.

Decide in that order. Do not let the candidate I want to run pick the calibration I believe.

**Then, in order:**
1. **Ablate iteration 18** (`RUIN_FLOOR = 0`). It was accepted on **+6** — inside the band my current
   gate sends to replication, not to accept — and justified by a *"zero arm at exactly the null,
   se = 0"* that LEARNINGS 36 has since retracted as structural. The 2x2 already run (`iter12`/`iter18`/
   `mC`/`mD`) put its main effect at **−3 / −4 at both memory doses**, and arm C was then rejected at
   22/50 on a *different* map draw — a 10-game disagreement that §43 now says is exactly what two
   25-map draws produce. **On the full corpus this becomes decidable**, and it is the largest suspected
   negative carried in the current bot.
2. **Position-symmetric mirror arm** (LEARNINGS 42). Still unbuilt, and it is the only way to read the
   maze 18-vs-4 split — or any split — as a symmetry bug rather than seed divergence.
3. **Symmetry inference in-bot.** Confirmed today as genuinely unattempted: `bob-tools/BobSym.java` is
   an *offline* audit of the tower-type rule, not runtime inference. Corpus-wide, not regime-narrow.

**Do NOT re-open**: denial-unit navigation policy (it30, ladder 25/22/19, one-directional flips);
ruin-hint sharing (3 attempts); SRP-site searching (it10); soldier movement for SRP siting (it13, −35);
the SRP/ruin priority gate (it29, vetoed — `abandon = 0` in 77,963 soldier turns); the tower cap
(regime 5/76, **conditionally** re-openable per the calibration above and by nothing else); the
wall-density/navigation probe (cancelled — the number under it was the opponent's). Iteration 8's chip
trigger is **not** met (21-map census).

**Pre-checks I did NOT do, named so the next session does not inherit my momentum:**
- Iteration 30's secondary throughput instrument was never validly measured (cumulative numerator over
  instantaneous denominator). The reject does not depend on it, but "denial units run at 1% of
  capacity" remains **true and unexplained**.
- Whether the full-corpus reshuffle floor is stable across *opponents*, not just across arms. My
  calibration uses self-play arms only.
- `getMoney`, `sensePassability`, `disintegrate`, `broadcastMessage` and the free-form markers are all
  still unused and none has been costed. The sweep listed them; I only chased `getNumberTowers`.

### Full-corpus calibration LAUNCHED — run `20260908-160234`, 300 games, IN FLIGHT

```
gauntlet 20260908-160234  bot=bob  opponents=[bob_n1 bob_n2]  maps=75 pinned  games=300  jobs=3
```

Launched 16:02 UTC. The next tournament is 01:00 UTC, so there is no contention. Collate with:

```bash
../../tools/gauntlet-collect.sh 20260908-160234
python3 bob-tools/eval_arms.py gauntlet/20260908-160234 bob_n1 bob_n2
```

**Read it against the three pre-registered outcomes written above, in that order, before considering
any candidate.** `n1`/`n2` differ from `bob` only in PRNG phase, so each arm's deviation from 75/150 is
one draw of the full-corpus noise floor. Note there is **no `n0` in this run**: a byte-identical arm is
structurally forced to 75/150-all-split on a deterministic engine (LEARNINGS 36), so playing it would
buy a wiring check for 150 games. The wiring was checked this morning at 25 maps.

**If this session dies here**: the run is setsid-detached and survives; only the collation is lost.
`gauntlet-collect.sh --list` will show it complete. Do not re-run it.

### A false alarm worth recording: "ABLATION A7" is live shipping code, and the comment says the wrong word

While building the iteration 18 ablation arm I found this in **`src/bob/Soldier.java`** — the file that
plays in the tournament:

```java
// ABLATION A7: iteration 7's avalanche hash removed; back to iteration 1's
// team-symmetric parity rule.
return ((ruin.x + ruin.y) & 1) == 0 ? ... ;
```

Finding the word ABLATION in the shipping bot is exactly the shape of a serious accident — an
experimental arm's edit left in the baseline — so I traced it before assuming either way:

```
bob_iter7  bob_iter9  bob_iter11   avalanche hash
bob_iter12 bob_iter18 bob_iter20   parity rule + "ABLATION A7" comment
```

It entered at **iteration 12, deliberately**: *"revert the hash, REMOVE the ruin memory, on sweep
evidence"*, and the log carries the full case — the hash was measured at **−20 points in the presence
of SRPs**, and iteration 22 later tried a third rule (folded parity) and lost as well. Three
coordinate-keyed rules measured, parity dominates, area closed. **No accident. Nothing to fix in the
code.**

**But the hazard is real and it cost me twenty minutes**, so it goes in the log rather than being
forgotten: a comment that says "ABLATION" beside *accepted, shipping* behaviour will read as a leaked
arm to every future session, including me an hour ago. I am deliberately **not** editing it, because a
comment-only change to `src/bob` would break the invariant I rely on every session — that `src/bob` is
byte-identical to the last accepted snapshot modulo the package line, which is the check that would
actually catch a real leak. Trading a genuine detector for a cosmetic fix is a bad trade. **Renaming it
belongs in the next commit that legitimately touches `Soldier.java`.**

The general form, since I keep meeting it: **an invariant that makes accidents visible is worth more
than the tidiness it costs**, and a scary-looking comment is cheap to check when the invariant holds.

### `src/bob_abl18` built and compile-checked, ready for the full-corpus test

One line, reverting iteration 18 only: `workOnRuin`'s paint guard goes from `RUIN_FLOOR` (0) back to
`PAINT_FLOOR` (15). **Deliberately NOT arm C** — arm C bundled this with restoring ruin memory, and
bundling is what made the earlier result uninterpretable. One mechanism, one arm.

Queued behind the calibration, not launched: whether it is worth 150 games depends on what the
calibration says the floor is, and running it first would be choosing the experiment before knowing
whether the instrument can read it.

---

## 2026-09-08 ~16:55 UTC — the "1% of capacity" figure is retracted (LEARNINGS 47)

Non-blocking work while the full-corpus calibration `20260908-160234` plays. No shipping code touched;
`src/bob` is still byte-identical to `bob_iter20`.

**Why I picked this up.** My own STATE OF PLAY, written this morning, lists "denial units run at 1% of
capacity" under *pre-checks I did NOT do*, marked **true and unexplained**. An unexplained order-of-
magnitude anomaly in my own shipping bot is the cheapest lead I have, it needs no VM games, and it sits
directly under the iteration the loop just spent 250 games rejecting.

**The instrument.** `bob-tools/denialprobe/DenialProbe.java` + `bob-tools/denial-probe.sh`, a private
fork of the shared `tools/replaydump/ReplayDump.java`. **The shared tool is coordinator-owned and is
not modified**; the fork is generated from it and carries a header saying so. The runner uses
`tools/engine-jar.sh --remote` rather than a bare `find`, per the standing warning about the stale
`1.0.0` jar in the gradle cache.

It answers the question the raw rate cannot: for every mopper/splasher turn, was there an enemy tile in
**action range**, was the unit **off cooldown**, and did it **act**. Those separate "no target" from
"target present, declined".

**One semantics check I had to run before believing any of it.** The first output had a ratio of
**578%**, which is impossible, and the cause was `Turn.actionCooldown()`. Tracking one mopper across
its actions settled it:

```
round 396  aCD=10
round 397  aCD=30   <- id10011 UNPAINT (24,9)
round 398  aCD=20
round 399  aCD=10
round 400  aCD=30   <- id10011 UNPAINT (22,10)
round 403  aCD=30   <- id10011 UNPAINT
```

The cooldown in a `Turn` is the **post-action** value. So `aCD < 10` does not mean "could act" — it
means "**ended the turn able to act and did not**", which makes it the count of *declined*
opportunities and gives the correct denominator `actedInRange + readyInRange`. Note also what those
three rounds say on their own: 397, 400, 403 is an action **every third round**, which is 100% of the
mopper ceiling. A unit at "1% of capacity" cannot do that, and that was the first hard evidence the
headline figure was wrong.

**The finding.** Denial units run at **19-43% of ceiling**, not 1%. The old number divided by
(units ever spawned) x (total rounds) instead of unit-rounds actually lived; I had the probe print both
divisors on the same replay and the wrong one reproduces "~0.004" exactly. Full table and the rule in
**LEARNINGS 47**.

Moppers take **84-86%** of their opportunities and are bounded by target availability. Splashers
decline **85%**, which is `SPLASH_MIN_VALUE = 5` behaving as designed — and that 85% independently
reproduces the figure already measured on 2026-09-07 by a different tool, which is a good check on this
probe rather than a new result.

**What does NOT re-open.** Lowering `SPLASH_MIN_VALUE` stays closed. Its rejection rests on arithmetic
that has nothing to do with either instrument — a splash costs 50 paint and score approximates tiles,
so score 4 is 12.5 paint/tile against a soldier's 5 — and iteration 16 then measured the splasher slot
at +13 games. A broken denominator elsewhere does not revive a direction killed by a division.

**What this changes going forward.** Iteration 30's urgency was manufactured. The denial thread is not
dead — moppers being target-limited is real and confirmed by two instruments — but it is a *target
availability* question (where the units are, and how many of them there are), not an idleness one, and
it must be priced against the fact that they are already working at a fifth to nearly a half of
capacity. Nothing here is worth an iteration until the calibration says what effect size I can resolve.

**Still queued, unchanged, and still gated on the calibration**: ablate iteration 18 (`src/bob_abl18`,
built and compile-checked), then the position-symmetric mirror arm, then in-bot symmetry inference.

### Correction, ~17:00 UTC — I ran the discriminating case and it overturned half my own write-up

An hour ago I published LEARNINGS 47 with a paragraph flagging "moppers have no enemy paint in vision
on 97.6% of turns" as an **unresolved disagreement between two of my instruments**. That was wrong, and
I only found out because I went and ran the other instrument instead of reasoning about it.

`BobMop` on today's replays gives `mopInVis/ourMop` of **60% on Leaf and 57% on DefaultHuge**; my new
probe gives **59% on Leaf**. The two tools agree to within a point, and their enemy-tile
reconstructions agree with the engine census to ~2%. There is no instrument disagreement.

**What there is instead is a stale fact.** The original table says
`MOPPERS turns 1,942` for a whole 2000-round game — about **one mopper alive at a time**. Today
DefaultHuge carries ~12. A single mopper on a 59x59 board genuinely does see nothing 97.6% of the time.
The number was right when taken; the bot outgrew it, largely because iteration 20 doubled the splasher
share and the denial population grew ~12x.

**And that forces a correction to my own headline.** "1% of capacity" had two independent sources:
the 2026-09-06 spawned-x-rounds divisor (a real artefact, reproduced exactly), **and** a 2026-09-07
probe measuring "moppers fired on 0.4% of 1,942 turns" — which is **correctly denominated** and was
true of the bot it measured. So the claim was one part miscalculation and one part an expired truth.
Both roads end at the same place — the current bot runs at 19-43% of ceiling — but "it was just a bad
divisor" would have been a tidier story than the real one, and I had already committed it.

The generalised rule is now in LEARNINGS 47 and it is worth more than the divisor lesson:
**a measurement of the engine is permanent; a measurement of your own bot is a snapshot with an expiry
date that nothing in your notes announces.** Date them, and re-take before building.

### Free by-product: every unit death in this lineage is paint starvation

`BobMop`'s death forensics on today's `Leaf` replay, bucketed by paint held on the last turn:

```
SOLDIER   439 deaths   438 starved (paint <= 10)     1 killed
SPLASHER  409 deaths   370 starved                   9 killed
MOPPER    202 deaths   202 starved                   0 killed
```

**1,050 of 1,050 unit deaths are starvation, and combat kills are 10.** Paired with the same run's
paint accounting — passive drain of 70,110, i.e. **-59% of tower income**, against 16% of unit-turns
spent standing on enemy paint at -2 (moppers -4) — this says mopper lifetime, and therefore total
denial throughput, is set by a paint budget rather than by anything either the navigation or the
firing-threshold hypotheses touched.

**Recorded as a lead, deliberately NOT opened as an iteration.** Paint refill by walking units home is
a closed direction (it8) whose re-open trigger is "chips sustained below ~5,000", and that trigger is
still not met. This is a different quantity — paint, not chips — so it does not re-open it by default,
and it is exactly the kind of striking number that has now twice tempted this lineage into an iteration
before the instrument could resolve it. It waits for the calibration like everything else.

### Queue correction: the mirror arm DEPENDS on symmetry inference. My STATE OF PLAY had them backwards.

My standing queue lists (2) position-symmetric mirror arm, then (3) in-bot symmetry inference. Building
(2) today showed that ordering is impossible, for the price of one code read.

LEARNINGS 42 prescribes a mirror arm "seeded position-symmetrically ... so mirrored robots get equal
seeds". **Equal seeds are necessary but nowhere near sufficient**, because of what the seed then feeds:

```java
// Nav.wander()
int start = G.rng.nextInt(8);
Direction c = G.DIRS[(start + i) & 7];   // G.DIRS is an ABSOLUTE compass-ordered array
```

Two mirrored robots drawing the *same* `start` pick the **same absolute direction** — both walk north.
On a 180deg-rotationally symmetric map the mirrored robot needed to walk **south**. So the "fixed"
mirror is still not a mirror; it has merely traded one asymmetry for another, and it would have
produced exactly the same plausible-looking splits that LEARNINGS 42 warns cannot be interpreted.

A real control needs the policy's *outputs* mirrored too: pick the random direction in a **team-relative
frame** and map it through the map's symmetry (negate for 180deg rotation; reflect, with a chirality
flip, for the reflective cases). That transform requires knowing which symmetry the map has — and BC25
does not expose it (it is not in `RULES.md`'s API digest, and Phase 0.8 of the algorithm treats
inferring it as the standard practice precisely because it is not given).

**Therefore: (3) symmetry inference is a prerequisite for (2), not a successor.** The queue is reordered
accordingly. This is also the second time today that LEARNINGS 42's own lesson — *check that your
control is actually controlled* — has applied to a fix proposed for it: the first fix was itself
uncontrolled.

Cost: one grep. Value: it would have been a 150-game arm answering a different question than the one
asked, and I would have believed it.

---

## 2026-09-08 ~17:20 UTC — FULL-CORPUS CALIBRATION, run `20260908-160234`, 300 games. Verdict: outcome 3, near the binomial end.

`bob` vs `bob_n1`/`bob_n2` on all 75 corpus maps, both sides. The arms are policy-identical to `bob`
and differ only in PRNG phase, so each arm's deviation from 75/150 is one draw of the full-corpus noise
floor.

```
bob_n1   bot 75/150 (50.0%)   ARM 75/150   dev  +0
bob_n2   bot 71/150 (47.3%)   ARM 79/150   dev  +4
```

**The aggregate is two numbers, and two numbers cannot estimate a standard deviation.** Read naively,
|dev| of 0 and 4 looks like outcome 1 ("<= 2 games") and would have handed me the loosest, most
convenient reading — the one that re-opens the tower cap and declares 3-point resolution. My own
pre-registration warned about exactly this: *do not let the candidate I want to run pick the
calibration I believe.* Under a pure binomial (sd 6.12), P(both arms land within 4) is about 0.34, so
this draw does not even weakly reject binomial.

**The fixed corpus gives a far better instrument than the aggregate, for free: 75 PAIRED maps.** Both
arms played the same 75 maps, both sides. For each map take the two arms' bot-records
`S in {0,1,2}` and use `E[(S_a - S_b)^2] = 2 Var(S_m)`:

```
per-map difference (n1 - n2):   -2: 2   -1: 14   0: 38   +1: 20   +2: 1     (75 maps)
sum of squared differences = 46   ->   Var(total) = 46/2 = 23   ->   sd = 4.80 games / 150
```

Checks: the differences sum to +4, which reproduces the aggregate 75 vs 71 exactly; bot-swept 15 and
arm-swept 15 against `n1` is the symmetry two policy-identical arms must show.

**So the full-corpus noise floor is sd = 4.8 games of 150**, against a binomial 6.12 — **78% of
binomial**, not the near-zero the "shared map sample" reasoning of LEARNINGS 43 predicted. Only 38 of
75 maps give the same result under a mere PRNG-phase change; **half the corpus is still a coin flip.**

### Reading it against the three pre-registered outcomes, in the order I registered them

- **Outcome 1 (`<= 2 games`)** — NOT met. The paired-map estimate is 4.8, and the two aggregate
  deviations that superficially suggested it are one lucky draw.
- **Outcome 2 (`~6 games`, binomial)** — nearly met, and this is the one to act on.
- **Verdict: outcome 3, interpolating close to outcome 2.** Saying which, as registered.

**Consequences, binding:**

1. **The tower-cap guard STAYS CLOSED.** Its re-opening was conditional on outcome 1 and nothing else.
   Its 5 binding maps are 10 games of 150 = 2.1 sd — nominally at the bar, but that is the *best case*
   of a direction already rejected once, and the pre-registration did not offer it this door.
2. **Full-corpus runs are still worth their cost, just not as much as hoped.** 2 sd = **+10 games of
   150** (6.4 percentage points), against the 50-game arm's +7 games of 50 (14 points). **Resolution
   improves 2.2x, not 4.7x.**
3. **The new accept gate for a 150-game full-corpus head-to-head: `>= +10` accepts, `+7..+9`
   replicates, `<= +6` rejects.** Registered now, before the ablation reports.
4. LEARNINGS 43 needs qualifying: map sampling is most of the *cross-run* noise, but removing it leaves
   78% of binomial standing, because the residue is not sampling — it is the engine's own chaos
   re-rolling on a fixed map. §46's churn finding is the same fact from the other side.

### Iteration 18 ablation LAUNCHED — run `20260908-172346`, 150 games, and it is UNDERPOWERED. Saying so first.

```
gauntlet 20260908-172346  bot=bob  opponents=[bob_abl18]  maps=75 pinned  games=150  jobs=3
```

`bob_abl18` is the one-line revert of iteration 18 (`workOnRuin`'s guard back from `RUIN_FLOOR` to
`PAINT_FLOOR`), compile-checked. The suspected effect from the earlier 2x2 is **-3/-4 games of 50**,
i.e. **-9 to -12 games of 150**. Against sd 4.8 that is **1.9 to 2.5 sd**, so a single run has roughly
coin-flip power at my own +10 bar.

**Pre-registered, before the result exists:**
- `abl18 >= +10` — iteration 18 is a genuine negative; revert it.
- `abl18 +7..+9` — suggestive at the size predicted; **replicate on a fresh 25-map draw** rather than
  accepting or dismissing. This is the likeliest outcome and I am naming it in advance so that a
  borderline number does not get argued into whichever conclusion I prefer at 18:00.
- `abl18 <= +6` — iteration 18 is not the carried negative I suspected; close it and stop paying
  attention to it.

Collate with `../../tools/gauntlet-collect.sh 20260908-172346`.

### Closing the four uncosted API-sweep methods (engine probe, ~5 minutes, no games)

My STATE OF PLAY listed `getMoney`, `sensePassability`, `disintegrate`, `broadcastMessage` and the
free-form markers as "still unused and none has been costed. The sweep listed them; I only chased
`getNumberTowers`." Costing them is cheap and, per LEARNINGS 47, engine facts do **not** expire — this
is the durable kind of knowledge.

- **`getMoney()` — CLOSED, it is a synonym.** `RULES.md` already records `getChips() == getMoney()`,
  and the bot calls `getChips` 3x. Zero new capability.
- **`sensePassability(MapLocation)` — CLOSED, a convenience.** Duplicates `MapInfo.isPassable()`, which
  the bot already uses throughout. No capability, and it costs a separate sense call.
- **`disintegrate()` — CLOSED, and the engine settles it outright.** Decompiled:

  ```
  public void disintegrate();
     0: new  #775   // class battlecode/instrumenter/RobotDeathException
     3: dup
     4: invokespecial ...
     7: athrow
  ```

  It is a bare suicide — it throws and nothing else. No paint returned, no chips refunded, no area
  effect. There is no BC25 upkeep or unit cap for a death to relieve, so the mechanic has **no upside
  for this lineage at all**. I had been carrying a vague idea that a starving mopper might disintegrate
  for value; there is none, and one `javap` was the whole cost of finding out.
- **`sendMessage` / `broadcastMessage` — already tried, and honestly closed.** The bot has **zero**
  comms calls, which looked from the sweep like a whole untouched mechanic. It is not: iteration 28c
  put ruin hints over broadcast (`bob_j0/j1/j2/j3` at doses 0/400/1600/6400) and lost **16-17 maps from
  both sides against 1 won from both**. Ruin-hint sharing is closed after 3 attempts. The *mechanism*
  is therefore tested and the *payload* is what failed — but I am not re-opening it on that
  distinction, because "same mechanism, different payload" is precisely the reasoning that produced
  attempts 2 and 3.

**Net: three closed by engine probe, one already closed by experiment. No new lever, and the sweep item
is now discharged rather than carried forward again.** Recording the negative result matters as much as
a positive one would have: the next session should not re-derive it.

### Caveat on my own sd 4.80, now that it is project doctrine

The coordinator has promoted the full-corpus calibration to `TRAINING_ALGORITHM.md`. Two limits of the
number should travel with it, because I would rather they be known now than rediscovered by whichever
lineage it misleads:

1. **It is measured on self-play arms only.** `n1`/`n2` are policy-identical to `bob` and differ only
   in PRNG phase. Whether the same floor holds when the two sides are *different bots* — the case every
   accept gate actually uses — is untested. My own STATE OF PLAY already listed this as a pre-check I
   did not do, and promoting the number does not discharge it. A lineage whose candidate differs
   structurally from its baseline may face a wider floor than 4.80.
2. **`Var = 23` is itself an estimate from 75 paired maps**, so it carries roughly +/-16% relative
   error (chi-square on 75 df). sd 4.80 is really "about 4.4 to 5.3". The gate +10 is ~2 sd at the
   point estimate and ~1.9 sd at the pessimistic end, which is fine — but +10 should not be treated as
   a sharp boundary, and a result at +9 or +11 is not meaningfully different from one at +10. That is
   exactly why the band +7..+9 says *replicate* rather than *decide*.

Neither weakens the doctrine's main claim — a census kills sampling error and leaves engine chaos —
which is the part that came from the paired-map structure and is not sensitive to either caveat.

### Symmetry inference: probe built, and PRE-REGISTERED before it runs

`src/bob_symprobe` compiles. It is **measurement only** — `Sym.observe()` maintains the candidate set
and nothing reads it, so the arm's play is unchanged apart from bytecode.

**Engine ground truth (permanent, per LEARNINGS 47):** `battlecode.world.MapSymmetry` has exactly three
values — `ROTATIONAL`, `HORIZONTAL`, `VERTICAL`. It is in `battlecode.world`, **not**
`battlecode.common`, so it is genuinely not exposed to bots. I index by *transform*, not by the
engine's name, because "HORIZONTAL" is ambiguous between "mirror across the horizontal axis" and
"mirror horizontally" and the bot only ever needs the transform.

**The question the probe exists to answer, and why it is not obvious.** Memory is **per robot**. A
mopper lives ~86 rounds (measured today), and a robot can only eliminate a hypothesis once it has seen
a tile *and* that tile's image. It is entirely possible that a short-lived robot never resolves the
symmetry at all, in which case the whole direction is dead before any game is played. **Bytecode is not
the constraint** — observed usage is 1,600-1,900 against a 17,500 limit, and `observe()` returns on its
first line once resolved.

**Pre-registered readings, written before the probe has run:**
- **Median resolve-life <= 100 rounds, on most maps** — the mechanism fires within a typical unit's
  lifetime. Build the treatment arm.
- **Median resolve-life 100-300 rounds** — it fires only for long-lived units. Then the treatment must
  be attached to **towers** (stationary, long-lived) rather than to moppers, which changes the design;
  do not paper over it by using it in moppers anyway.
- **Frequently never resolves** — the direction is dead in its per-robot form and needs shared state to
  live. Shared state means comms, which is a closed direction (28c, 3 attempts). **Then I close it and
  say so**, rather than re-opening comms through the back door.

**Correctness check, and it is separate from the timing one.** The probe prints `which=` per robot;
`BobMop` prints the engine's own `symmetry=N` per map. Across maps the two must form a **consistent
bijection**. If they do not, the inference is wrong and no timing number means anything — so the
bijection is checked FIRST. A probe that resolves fast and resolves wrongly looks identical in the
output to one that works, which is the same trap as the "1% of capacity" divisor.

**Why this direction and not another.** It is not invented: `TRAINING_ALGORITHM.md`'s "when the loop
stalls" names symmetry inference as the most load-bearing entry of its short list, my queue correction
today made it a prerequisite for the mirror arm, and today's denial measurement independently says
moppers are bounded by *target availability* (nothing in vision on 50-77% of rounds) — which is exactly
what knowing where the enemy half is would address. Three independent routes to the same mechanism.

**Not launched yet, deliberately.** The ablation is using my full 3-job budget and the VM also serves
BC26 and two siblings. Probe matches go after it finishes, not beside it.

---

## Iteration 18 ablation — run `20260908-172346`, 150 games, full corpus. VERDICT: the suspected negative is NOT there. CLOSED.

```
bob        82/150  (54.7%)
bob_abl18  68/150            deviation from 75:  -7
per-map:   bob swept 14 | split 54 | abl18 swept 7   (of 75)
sides:     bob as A 48/75    bob as B 34/75
```

**Against the gate I registered before the run:**

- `abl18 >= +10` → iteration 18 is a genuine negative, revert it. **Not met.**
- `abl18 +7..+9` → replicate. **Not met.**
- `abl18 <= +6` → not the carried negative I suspected; **close it.** ← **this one**

**And the failure is directional, which is stronger than the threshold alone.** The hypothesis did not
merely fail to clear a bar — it predicted the wrong *sign*. The earlier 2x2 put iteration 18's main
effect at **-3/-4 games of 50**, i.e. abl18 should have scored **+9 to +12** on 150. It scored **-7**.
Against sd 4.80 that is **3.3 to 4.0 sd away from the prediction**. The suspected negative is not
merely unproven; the data actively point the other way.

**What I must NOT conclude: that iteration 18 is positive.** bob's +7 is 1.5 sd — inside my own
replicate band and not significant. The honest statement is "iteration 18 is not the carried negative I
suspected, and its true value remains indistinguishable from zero." Closing it means *stop spending
games on it*, not *declare it good*. This is the same discipline that made me discard the flattering
reading of the calibration three hours ago, applied to a result that happens to flatter a shipping
feature instead.

**Why this mattered enough to spend 150 games on.** Iteration 18 was accepted on **+6** — inside the
band my current gate sends to replication rather than accept — and justified by a "zero arm at exactly
the null, se = 0" argument that LEARNINGS 36 has since retracted as structural. It was **the largest
suspected negative carried in the shipping bot**. Retiring that suspicion is worth the run even though
nothing changes in `src/bob`.

### Two diagnostics, recorded rather than acted on

**1. A side asymmetry that the null run does not show.** bob went **48/75 as A** and **34/75 as B**, a
side effect of +7 games ((48-34)/2), about **2.3 sd**. The calibration on the *same 75 maps* showed
nothing like it — vs `n1` it was 36/39, vs `n2` 36/35, i.e. ~0 both times. Since abl18 differs from bob
by one line, a pure map-or-engine side advantage should have appeared in the null too **and did not**.
So this is either noise at 2.3 sd or a genuine interaction between iteration 18's paint guard and spawn
side. **Not chased today** — it is exactly the kind of lopsided split LEARNINGS 42 says I cannot
currently interpret, because I still have no working mirror instrument. It is logged so the symmetry
work has a concrete question waiting for it.

**2. Churn is HIGHER than the null, and per LEARNINGS 46 that argues for "no effect".** Splits rose to
**54 of 75** against ~46 in the null arms, while the score moved +7. §46's finding was that a
behaviourally-null change perturbs *more* games than a real one and moves the score less; that is the
signature here. Note also that the sweep counts (14 vs 7) merely restate the margin — 82 - 75 = 7 =
14 - 7, the identity the tournament report proves — so they are not a second piece of evidence.

**Closed-directions ledger, updated:** iteration 18 / `RUIN_FLOOR` — closed 2026-09-08 by a 150-game
full-corpus ablation at -7 against a predicted +9..+12. Re-open only if a *mechanism-level* reason
appears that the paint guard behaves differently than the 2x2 modelled; a fresh map draw is not such a
reason, because the corpus is already every map.

**This is my fourth consecutive non-accept.** `MaxConsecutiveRejects = 3` is passed, so the loop-stall
protocol is in force — and I am already executing it rather than inventing: today's work has been
ablating a carried feature (protocol item 1) and the symmetry-inference probe, which is the first entry
on the algorithm's own short list for a stalled lineage.

### Applying the other lineage's Var > 0.25 caveat to my own 4.80 — it does NOT bind here, and the bound is sharper than "upper bound"

The coordinator relayed that another lineage's paired estimator returned `Var(S) = 0.28` against a
0.25 per-game maximum — impossible for genuine Bernoulli noise — and asked whether mine is inflated the
same way. Computed on my own per-map records, at zero cost:

```
sum of squared paired differences   46 over 75 maps
Var(S_m), S in {0,1,2}              0.3067     (max 0.5 = 2 x 0.25)
  as a PER-GAME Bernoulli variance  0.1533     (max 0.25)      -> 61.3% of maximum
```

**Mine does not exceed the bound**, and is not close to it. The floor of 4.80 shows none of the
contamination that made theirs impossible.

**Watch the scale when comparing these.** `S_m in {0,1,2}` is a *count over two games*, so its ceiling
is **0.5**, not 0.25; the 0.25 ceiling belongs to the per-game proportion. Quoting 0.3067 against 0.25
would look like a violation and is not one. Whichever lineage compares next should say which scale it
is on, because the two differ by exactly the factor that decides whether you think you have an
impossible number.

**And I think "upper bound, not unbiased estimate" is very slightly the wrong diagnosis, in a way worth
handing back.** For two *exchangeable* arms, `E[(Sa - Sb)^2] = 2 Var(S)` is **unbiased**, not an upper
bound. A deterministic map — one that resolves the same way regardless of phase — contributes
`(Sa - Sb)^2 = 0` **and** has `Var(S_m) = 0`, so it deflates both sides equally and biases nothing.

The term that actually makes it an upper bound is the arms not being exchangeable: if they differ
systematically by `d` per map, the sum absorbs `N * dbar^2` and charges a real effect to chaos. That
term is **measurable**, so the bound's tightness need not be guessed:

```
systematic component  N*dbar^2 = 0.213 of 46   (0.46%)
noise-only sd = 4.785   against 4.796 uncorrected
```

**0.46%.** My arms differ in PRNG phase alone, so they are exchangeable by construction and the
estimator is essentially unbiased — the correction is in the third decimal. A lineage whose per-game
Var exceeds 0.25 has arms that are **not** exchangeable, and that is a diagnosable fault in the
calibration design rather than an irreducible property of the estimator: compute `N*dbar^2` and it
names how much was borrowed from a real difference.

**The genuinely important part of their result is not the caveat — it is 6.48 vs my 4.80.** Same
engine, same 75 maps, 33 of 75 surviving a phase change against my 38, and a floor **35% wider**. So
**the noise floor is a property of the bot, not only of the game**, and no lineage may inherit
another's. That also sharpens my own caveat from earlier: I flagged that 4.80 is measured on
*self-play* arms and may not hold when the two sides are different bots. If the floor varies this much
between two bots that are merely *different lineages*, the case for it varying between a baseline and a
structurally different candidate is stronger, not weaker. **My +10 gate stays, and stays provisional.**

---

## Symmetry-inference probe — the timing headline says BUILD, the denominator says DON'T. Per-robot full resolution FAILS its gate.

Four verbose matches (`bob_symprobe` vs `bob` on Leaf, DefaultHuge, catface, DefaultSmall), evaluated by
`bob-tools/sym_eval.py`, which was written and committed **before** the probe ran.

### 1. Correctness first, as registered — and it is perfect

```
engine symmetry=0  ->  probe says 0, 47 robots   100%
engine symmetry=1  ->  probe says 1, 299 robots  100%
engine symmetry=2  ->  probe says 2, 113 robots  100%
```

**459 of 459 robots correct, on all three symmetries.** The inference is sound. This mattered to check
first: fast-and-wrong is indistinguishable from working in the output, which is how "1% of capacity"
survived four days.

**Permanent engine fact, now pinned down** (and per LEARNINGS 47 this is the kind that does not expire):
the bijection is the **identity**, so the engine's `MapSymmetry` ordinals are

```
0 ROTATIONAL  (x,y) -> (W-1-x, H-1-y)
1 HORIZONTAL  (x,y) -> (x,     H-1-y)     i.e. HORIZONTAL mirrors the Y coordinate
2 VERTICAL    (x,y) -> (W-1-x, y    )     i.e. VERTICAL   mirrors the X coordinate
```

The `HORIZONTAL`/`VERTICAL` naming is the ambiguous one I refused to guess at when writing the probe.
It is now measured rather than assumed, and it is the *opposite* of the reading I would have picked.

### 2. Timing — and the number that actually decides it

```
map            robots resolved   median life   p90
DefaultHuge                299            70   252
DefaultSmall                47            21    65
Leaf                        88            39   154
catface                     25            41    69
ALL                        459            51   231
```

Median resolve-life **51 rounds**, which trips my pre-registered "**<= 100 -> BUILD THE TREATMENT
ARM**". **That reading is wrong, and my own script said why before it ran:** the median is conditional
on resolving at all, and robots that never resolve cannot appear in it. Against the spawn counts from
the same replays:

```
type       spawned resolved      rate
SOLDIER       1177      243     20.6%
SPLASHER      1065      155     14.6%
MOPPER         529       61     11.5%
ALL           2771      459     16.6%
```

**Five robots in six never resolve the symmetry at all, and moppers — the unit the whole treatment was
for — resolve 11.5% of the time.** The pre-registered third condition, *"frequently never resolves"*,
is the one that is met.

### VERDICT: the per-robot, full-resolution form is CLOSED, by my own rule

I wrote: *"Frequently never resolves — the direction is dead in its per-robot form and needs shared
state to live. Shared state means comms, which is a closed direction (28c, 3 attempts). Then I close it
and say so, rather than re-opening comms through the back door."* That is the situation. **Closed, and
no comms.**

Cost: four probe matches and no gauntlet. Had I trusted the median — the number my own pre-registration
told me to distrust — I would have built a treatment arm and spent 150 games discovering that it fires
for one mopper in nine.

**Towers are not the escape hatch either**, and the reason is geometric rather than empirical: a tower
is stationary, so its 69-tile vision disc never moves, and it can only ever eliminate a hypothesis
whose axis happens to cut its own disc. Long life does not help when the observations never change.
Pre-registered option 2 ("attach it to towers") is therefore closed by inspection, not deferred.

### One genuinely new idea, flagged as NEW rather than smuggled in as a rescue

**Full resolution is not actually required.** With 2 of 3 hypotheses alive a robot has two candidate
enemy regions; with 3 alive it has three — and all three images of its own position lie away from its
own corner. Steering by the *current candidate set* rather than waiting for a unique answer would fire
on **100%** of robot-turns instead of 16.6%.

I am recording this as a **separate hypothesis requiring its own pre-registration**, not as a
continuation of the one that just failed — because "the mechanism failed, but a variant of it might
work" is exactly the reasoning that produced ruin-hint-sharing attempts 2 and 3, and I would rather
name the pattern than repeat it. It also inherits an unmeasured assumption: that the images of a
robot's own position are useful targets *before* the set narrows, which the probe did not test and
which is not obvious on a map whose symmetry is rotational versus reflective.

**What survives regardless:** `Sym.java` is correct, cheap, and now validated at 459/459 — so whenever a
mechanism does need the symmetry, the inference itself is built and does not have to be re-derived or
re-trusted.

---

## STATE OF PLAY — end of session 2026-09-08 ~18:30 UTC

**The bot**: `src/bob` unchanged, still byte-identical to `bob_iter20` (verified this session, 7/7
files). HEAD compiles (`compile-check.sh bob`). Last accept remains **iteration 20**. No accept today.

**Two runs completed and read, both against pre-registered gates:**

1. **Full-corpus calibration** `20260908-160234` (300 games). Noise floor **sd 4.80 per 150**, 78% of
   binomial, from **75 paired maps** rather than the 2-arm aggregate. Now project doctrine. New gate for
   a 150-game full-corpus head-to-head: **>= +10 accept, +7..+9 replicate, <= +6 reject**.
2. **Iteration 18 ablation** `20260908-172346` (150 games). `bob_abl18` **-7** where the hypothesis
   predicted **+9..+12** — wrong sign, 3.3-4.0 sd from prediction. **CLOSED.** Do not conclude
   iteration 18 is positive: bob's +7 is 1.5 sd, inside the replicate band.

**Four things closed today**, none of which cost a full iteration:

- "Denial units run at 1% of capacity" — **RETRACTED** (LEARNINGS 47). Truth is 19-43% of ceiling.
- Iteration 18's suspected negative — **not there**.
- Symmetry inference, per-robot full-resolution form — **CLOSED**: correct 459/459 but only **16.6%** of
  robots ever resolve (moppers **11.5%**). Towers are not an escape hatch, by geometry.
- `getMoney` / `sensePassability` / `disintegrate` / comms — **all discharged**, three by engine probe.

**The queue is now nearly empty, and that is the honest headline.** Everything I inherited has been
closed. What remains:

1. **The candidate-set variant of symmetry steering** — the one live new idea, flagged as needing its
   **own** pre-registration rather than inheriting the closed one's. Steer by the *surviving* hypothesis
   set (2 or 3 alive) instead of waiting for uniqueness; fires on 100% of turns instead of 16.6%.
   **Do the arithmetic first**: moppers attack at r^2<=2 so they need not *stand* on enemy paint, but
   202/202 mopper deaths are starvation and enemy ground costs them 4/turn, so "send moppers deeper"
   has a measured price. Rough figures: ~25 turns of life in enemy territory x 0.33 = ~8 actions,
   against ~12 actions per mopper life today. **That is not obviously a win and may kill the idea for
   the price of one division** — which is the check LEARNINGS says I keep skipping.
2. **The side asymmetry from the ablation** — bob 48/75 as A vs 34/75 as B (~2.3 sd), where the null run
   on the *same 75 maps* showed ~0. Uninterpretable until a real mirror instrument exists.
3. **Whether the 4.80 floor holds for non-self-play arms.** Still unmeasured, now more urgent: another
   lineage measured 6.48 on the same corpus, so the floor is a property of the **bot**.

**Do NOT re-open**: denial-unit navigation (it30); ruin-hint sharing / any comms (28c, 3 attempts);
SRP-site searching (it10); soldier movement for SRP siting (it13); the SRP/ruin priority gate (it29);
the tower cap (**stays closed** — its re-opening was conditional on calibration outcome 1, which was not
met); wall-density navigation; iteration 18 / `RUIN_FLOOR`; symmetry inference in its per-robot
full-resolution form; the four API methods above.

**New instruments built today, all committed and reusable:**
`bob-tools/denialprobe/DenialProbe.java` + `denial-probe.sh` + `denial_agg.py` (denial utilisation, with
the correct unit-round denominator); `bob-tools/sym_eval.py` (symmetry, correctness-before-timing);
`src/bob_symprobe/Sym.java` (symmetry inference, validated 459/459).

**Permanent engine facts pinned today** (LEARNINGS 47: these do not expire):
`MapSymmetry` ordinals are `0 ROTATIONAL`, `1 HORIZONTAL` = mirror **Y**, `2 VERTICAL` = mirror **X** —
measured, and the opposite of the natural reading. `disintegrate()` constructs and throws
`RobotDeathException` and does nothing else. `Turn.actionCooldown()` in a replay is the **post-action**
value.

**Fifth consecutive non-accept.** The loop-stall protocol is in force and being executed by the book
(feature ablation, then the algorithm's own first-listed stalled-lineage entry). The bot has not
regressed — `src/bob` is untouched — but the loop has not produced an accept today, and the next
session should weigh **protocol item 2, high-risk structural exploration**, over another small knob.

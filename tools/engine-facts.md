# Verified engine behaviour (shared neutral ground)

Facts about the BC25 engine, each verified against the engine jar itself and
each stating how to re-verify it. The engine and the spec are shared ground
under MULTI_AGENT.md rule 4, so anything here is available to every lineage.

Add a fact only with the check that established it. A claim about the engine
that cannot be re-derived is a belief, not a fact.

---

## A soldier attack on enemy paint costs 5 paint and does nothing

`InternalRobot.soldierAttack` deducts the attack cost **before** it examines the
target tile:

```
offset  58   invokevirtual  addPaint:(I)V        <-- cost deducted here
offset 178   invokevirtual  GameWorld.getPaint   <-- target first examined here
```

120 bytecodes separate them, and `canAttack` does not protect against it. So a
soldier ordered to attack a tile already holding **enemy** paint pays
`SOLDIER.attackCost` (5) and accomplishes nothing — the paint is gone whether or
not the action could ever have succeeded.

**Why this bites.** A guard written on a *proxy* for the engine's condition —
"the tile is not mine" — is not the same predicate as the engine's "the tile is
EMPTY", and the two diverge exactly as a map saturates. On a map that reaches
977 per-mille painted, almost every tile that is "not mine" is enemy-held rather
than empty, so a proxy guard sends soldiers to burn paint on no-ops all game.
One lineage measured starvation deaths falling roughly fourfold when it switched
from the proxy to the engine's own predicate.

**Re-verify:**

```bash
JAR=$(find ~/.gradle -name 'battlecode25-java-*.jar' | grep -v source | head -1)
unzip -o -q "$JAR" battlecode/world/InternalRobot.class -d /tmp/iv
javap -c -p /tmp/iv/battlecode/world/InternalRobot.class \
  | awk '/soldierAttack/,/^$/' | grep -nE 'addPaint|getPaint'
```

**The general form, which is the transferable part:** guard on the engine's own
predicate, not on a proxy you believe implies it. Where the engine exposes the
test (`getPaint(loc) == EMPTY`), use it; a paraphrase agrees with it only in the
states you happened to have in mind.

---

## Coverage per-mille is over PASSABLE tiles, walls excluded

`Round.teamCoverageAmounts` divides by the passable area — total tiles **minus
walls**. Using total area as the denominator deflates every figure derived from
it, by exactly the wall fraction.

**This entry previously said the opposite.** It was corrected on 2026-09-08 after
a lineage refuted it. The correction matters more than the fact, so the reasoning
is kept in full below.

**Verify by contradiction, not by fit.** On `Gears` (140 walls of 3025 tiles):

```
census  3025 tiles = 2872 painted (T1 1320, T2 1552) + 13 unpainted + 140 wall
coverage per-mille  T1 engine=454   T2 engine=535        sum = 989
```

Total area caps the two teams' sum at 2885/3025 = **954** per-mille, because only
passable tiles can hold paint. **989 > 954 is impossible**, so the walls are not
in the denominator. No estimate of the painted count is needed for this argument,
which is why it is decisive where a fit is not.

Confirming with the reconstruction, which is an independent count:

```
denominator = total    (3025):  T1 recon 436 vs engine 454   gap -18
denominator = passable (2885):  T1 recon 458 vs engine 454   gap  +4
```

The passable denominator leaves a residual of a few per-mille in the direction
unmodelled splashes predict (the reconstruction over-counts paint it cannot
attribute). The total denominator leaves a large residual in the opposite
direction, which nothing explains.

**Why the wrong version survived, which is the transferable part.** Its
verification was run on a map with 32 walls in 1225 tiles — 2.6%. There the two
candidate denominators differ by **2 per-mille**, well inside the gap unmodelled
splashes already produce, so the check could not separate the hypotheses it was
meant to decide between. **A verification performed where the hypotheses barely
differ is not a verification.** When a quantity depends on a fraction, test it
where that fraction is large.

`tools/replaydump` used the same wrong denominator and has been fixed; its
mismatch alarm was also set at 40 per-mille, wide enough to pass an 18-22
per-mille systematic error in silence, and is now 15.

---

## Replay per-robot state is written AFTER the robot's turn resolves

The paint and money a replay reports for a robot on round N are its values
*after* that round's actions, not the values it decided on. So any quantity read
from replay state is post-spend.

**Re-verify:** take a game in which a unit type is built often, compute from
replay state the fraction of turns on which that unit was affordable, multiply
that fraction by the number of robot-turns to get implied opportunities, and
compare against the number of that unit actually built in the same game. If the
state were pre-decision the two would be the same order of magnitude. Measured on
one game: an implied ~24 opportunities against **572 soldiers actually built**.

**Consequence:** replay state answers "what was true after the turn", which is
enough for questions about accumulation, pooling and drought. It cannot answer
"what could this robot have done", because the turns where it *did* act are
exactly the turns whose recorded resources were spent down — the estimate is
conditioned on the outcome it is predicting. To measure a decision, instrument
the decision in-bot, at the decision point.

---

## Resolve the engine jar with `tools/engine-jar.sh`, never with a bare `find`

battlecode-dev's gradle cache holds **two** engine jars —
`battlecode25-java-1.0.0.jar` and `battlecode25-java-3.1.0.jar` — so a probe
that locates the engine with `find ... -name 'battlecode25*.jar' | head -1` can
decompile the **wrong engine** and derive confident, false facts about the game.

This is not hypothetical: a lineage decompiled 1.0.0 while every
`engine_version.txt` in the repo says 3.1.0, and caught it only because a method
it expected (`getChips`) was missing outright. A subtler difference between
versions — a changed constant, a reordered branch — would have passed silently
into this file, which all three lineages trust.

**Use:**

```
tools/engine-javap.sh          battlecode.common.RobotController   # -p by default
tools/engine-javap.sh -c -p    battlecode.world.GameWorld          # flags pass through
tools/engine-jar.sh --remote                # just the path, as resolved on the VM
```

`engine-javap.sh` is the form to reach for. Resolving a path is not running a
command, and the older documented incantation
`javap -p -c -cp "$(tools/engine-jar.sh)" <class>` **cannot work on the driver at
all**: there is no local jar and no local JDK there, and the `--remote` path is
only meaningful on the VM, where `javap` is not on `PATH` in a non-interactive
ssh (it lives in `~/jdk21`). A lineage paid two failed calls to discover that and
reported it instead of keeping the workaround. The wrapper resolves the pinned
jar, exports the JDK on to `PATH`, and runs javap wherever both actually exist.

It reads the wanted version from `arena/engine_version.txt` and **refuses to
print a path whose version does not match**, so a missing or wrong jar becomes an
error rather than a wrong fact. Verified end to end: the resolved 3.1.0 jar
contains `getChips` and `getNumberTowers`, which 1.0.0 does not.

**Add an engine fact only if you obtained it through this resolver.** A fact
derived from an unpinned jar cannot be trusted, and cannot be distinguished later
from one that can.

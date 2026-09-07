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

## Coverage per-mille is over TOTAL tiles, not passable tiles

`Round.teamCoverageAmounts` divides by the full map area — **walls included, and
counted as unpainted**. Using passable area as the denominator inflates every
figure derived from it, by exactly the wall fraction.

**Verify** on any replay, with `tools/replay-dump.sh <replay> --map-at R`, which
prints both an exact census and the engine's own per-mille:

```
census  1225 tiles = 174 painted (T1 83, T2 91) + 1019 unpainted + 32 wall
coverage per-mille  T1 recon=68 engine=68
```

83 / 1225 = 67.8 → 68, matching. 83 / 1193 (passable) = 69.6 → 70, not matching.

**Why it matters:** one lineage combined this denominator mismatch with using
*reconstructed* rather than engine coverage and produced an unpainted-tile
estimate ~25% too high — a number that was plausible, defensible, and computed
correctly from the wrong referent.

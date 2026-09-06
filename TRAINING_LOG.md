
## Iteration 10 pre-registration — tower paint reserve (`src/carol_pr`, written and compile-verified)

Ready to launch the moment the VM frees. Numbered 10 because iteration 9 (SRPs, `src/carol_i8`)
is already registered ahead of it — but **see the ordering note at the end: this now outranks
it**, and I would rather record the reordering with its reason than quietly renumber.

**Change** (one clause in `refillIfPossible`):
```java
int avail = Math.max(0, ally.paintAmount - TOWER_PAINT_RESERVE);
int want  = Math.min(cap - rc.getPaint(), avail);
```
Refuelling an existing soldier can never consume the tower's ability to create a new one.

**Base**: whatever iteration 8 leaves behind. The change is in `refillIfPossible`, disjoint from
iteration 8's `towerTypeFor` clause and iteration 7's `runTower` clause, so it applies to either.

**Pre-registered gate**:
- **PRIMARY**: h2h vs the accepted snapshot > 50% accept, 45-50% near miss, < 45% reject. This
  instrument *can* see the change — unlike iteration 7, the mechanism fires in ordinary play on
  every map, so there is no representativeness problem.
- **MECHANISM** (must move, or the result is uninterpretable): rounds in the first 100 with **no
  tower able to afford a 200-paint soldier** must fall from its measured baseline of **median 28
  of 100** (9 of 27 games above 50). Measured with the same query already written, so the
  before-figure is on the record rather than reconstructed afterwards.
- **COUNTER-METRIC, named in advance because this is the obvious way it backfires**: soldiers
  denied a refill will run dry and die (0 paint = -20 HP/turn and frozen). If the mechanism
  metric improves while the h2h drops, that is the trade, and the algorithm's own warning
  applies — *survival bought with inactivity*, in reverse: production bought with unit deaths.
  I will check soldier lifetime, not just the paint metric, before reading a drop as noise.
- **DOSE**: `TOWER_PAINT_RESERVE` = 0 / 100 / 200 / 1000, where **0 is the byte-identical zero
  arm** and **1000 is the full ablation of `refillIfPossible`** (never examined in 8 iterations).
  Starting at 200. A concave curve with an interior peak would be much stronger evidence than
  any single arm, and both ends are meaningful policies rather than arbitrary extremes.
- **REGRESSION**: 0 exceptions; frozen-treasury and paint-drought gates must not worsen.
- **ARM-TO-ARM**: some games must be identical (maps where tower paint never drops below 200
  cannot be affected); *all*-identical voids the run.

**Ordering note.** This should run before SRPs. SRPs add +3 paint/turn per paint tower per SRP —
real, but they cost 200 chips *and* ~125 paint to lay, and the measurement above says carol
frequently has **no paint at all** in the window where it would matter most. A paint multiplier
applied to a stash that is empty a quarter to a half of the opening is the weaker of the two
bets, and fixing the leak first also makes the SRP iteration cleaner to interpret. Recording the
reason rather than the preference.

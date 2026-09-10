# Alice — UNCONFIRMED changes standing in HEAD

Machine-read by `tools/unconfirmed.sh`, which `tools/ac.sh` runs whenever
`src/alice/` is committed. **Do not reformat the checkbox lines.**

## Why this file exists

A screen ACCEPT followed by a census FAIL leaves a change in `src/alice` that is
positive on its own evidence and **not established**. The keep rule I registered
after K3's census — *keep if the census point estimate is >= 0 and no falsifier
fired* — is **keep-biased**: it says keep for nearly every unconfirmed positive
result, which is most of them. Applied twenty times it builds a HEAD that is an
accumulation of individually-unconfirmed changes, none harmful on its own evidence,
**with no point at which the accumulation is ever tested.** This lineage has already
measured a fifteen-iteration plateau; that rule is a mechanism for manufacturing one
and hiding it.

So the keep rule gets a RATCHET. No single keep decision has to carry the weight:

> **After every 3 UNCONFIRMED changes standing in HEAD, the accumulation must be
> measured against the last CONFIRMED snapshot — 75 maps / 150 games at the +12
> bar — before any further change may be promoted.**

**Why 3.** An unconfirmed change is, by construction, one that failed a +12 census;
K3's came in at +5. Three such changes accumulate to roughly +15 if they are
additive, which is **above the +12 bar** — so 3 is the smallest count at which the
accumulation is detectable by the instrument I already have. It is not a round
number chosen for tidiness.

**On a PASS:** all pending entries become confirmed-in-aggregate and the counter
resets. **On a FAIL:** the accumulation is not paying, and the entries are reverted
newest-first until it does. That is the point at which a hidden plateau surfaces.

## Pending

- [ ] K3 — refill reserve 200 -> 50 (`src/alice/RobotPlayer.java`, tryRefill).
      Screen ACCEPT net +4/50. Census FAIL net +5/150 against +12. Manipulation
      check passed (refills/unit 0.231 -> 0.265); falsifier did not fire (units
      0.92x, per-unit paint actions 1.16x).
      **CAVEAT, recorded because the keep rests on "no evidence of harm":** the
      census carried **no null arm**, so its ability to detect harm at this effect
      size was never measured on that draw. The screen's null read +0, which
      corroborates and does not replace it. This does not change the decision; it
      is part of it.

## Confirmed in aggregate

- [x] baseline: `alice_iter43` — the last snapshot measured by the roster.

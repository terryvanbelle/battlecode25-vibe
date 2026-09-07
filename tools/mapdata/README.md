# Map corpus facts (shared neutral ground)

Properties of the **official BC25 map corpus**, read straight from the engine
jar's `.map25` flatbuffers by `ruinscan/RuinScan.java`. Nothing here comes from
any agent's workspace, so it is shared ground under MULTI_AGENT.md rule 4
alongside the spec and the engine source.

## `ruin_parity.txt` — ruin coordinate parity, per map

Contributed by an agent after it cost that lineage a false finding, and
promoted here because the trap is live for anyone.

**The trap.** Any policy keyed on `(x+y)&1` — a common way to split ruins into
two classes without coordination — is **single-branch on four of the 75 maps**:

| map | ruins | even | odd |
|---|---|---|---|
| `gridworld` | 21 | 21 | **0** |
| `Filter` | 5 | 5 | **0** |
| `Snowman` | 6 | 6 | **0** |
| `CastleDefense` | 6 | **0** | 6 |

Corpus-wide the split is near even (732 even / 642 odd), so a trace on a
*typical* map shows both branches live and nothing looks wrong.

**Why it matters.** On one of those four maps a parity-keyed policy silently
executes one branch for the whole game. A census then shows the other branch
never firing, which reads exactly like a bug in the policy — and "fixing" it by
forcing the live branch appears to double the outcome, because the comparison is
against a build that was never doing anything different there. That is a real
sequence: it produced a confident "latent bug, half of all ruins wasted" report
that had to be retracted, after the same doubling reproduced with byte-identical
code on both sides.

**How to use it.** Before concluding a branch is dead from a single-map trace,
check that map here. And when picking a map to trace a two-branch mechanism on,
avoid these four unless the single-branch case is what you are testing.

```bash
# regenerate (needs the engine's map directory)
cd tools/mapdata/ruinscan && javac RuinScan.java && java RuinScan <dir-of-.map25>
```

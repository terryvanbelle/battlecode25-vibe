# RESEARCH.md — cross-year findings from Battlecode post-mortems

Synthesised from the published post-mortems of strong teams across **2019, 2020,
2021, 2023 and 2024**, rebuilt for this project from its two predecessors'
research documents.

## Provenance, and what is deliberately missing

**Nothing here derives from a 2025 post-mortem.** That exclusion is a standing
project rule, and 2025 is the contest year this project is playing — reading how
the actual finalists solved *this* game would replace the search with a lookup,
which is the one thing three independent lineages exist to avoid.

Both predecessor documents were built partly on 2025 sources, so neither could be
copied across. They were filtered mechanically before anyone read them: every
paragraph mentioning the 2025 year, or any 2025 team by name, was dropped
*before* the surviving text was read, so the exclusion holds for the coordinator
who assembled this file as well as for you. What remains is the 2019–2024
material, reorganised and re-pointed at this project.

That filtering is why some sections are thinner than they look like they should
be. Where a perennial pattern lost its best-documented example to the filter, the
pattern is still stated — it recurs across enough other years to stand — but you
are seeing the second-best illustration of it.

**If you ever find 2025 post-mortem content in this file or anywhere in
`reference/`, stop reading and tell the coordinator.**

## How to use this

Most of what follows is about **process** — how strong teams decided a change was
real — because that is what transfers between years with completely different
rules. The game-mechanics sections (§4–§8) transfer only where BC25 happens to
share the mechanic; read them as a catalogue of *classes of idea*, not as
instructions.

Each section ends with **→ for us**, tying the finding to this project's actual
constraints. Those are the parts to argue with. A finding you can show does not
apply here is worth as much as one you adopt.

This document exists mainly for the moment your loop stalls. See
`TRAINING_ALGORITHM.md`, "When the loop stalls" — re-examine the old tournament
games first, then come here.

---

## 1. Evaluation and measurement — the strongest regularity across every year

This recurs in more years than any other finding, and it is the one most relevant
to how this project works.

**A handful of games is not a measurement.** don't @ me (2023): *"Just three
matches might not be enough to highlight the strength and expose the weaknesses
of one's robot."* Their practice was full-set scrimmages against live opponents
**paired with** all-map runs against older versions of their own bot — two
instruments, not one.

**Not scrimming is how you miss a meta shift.** Oak's Last Disciple (2019) names
this as their single biggest mistake: *"we barely scrimmed after seeding (games
took too long and we were really lazy about it), and we didn't see the meta shift
that was happening right in front of our eyes."* The failure was not a bad
measurement; it was declining to measure while the ground moved.

**Ladder rank is not the objective.** don't @ me: *"Code > Elo … Generalizing
solutions in your code rather than coding for specific cases that appear on the
ladder often helped us find wins in tournaments where opponents might have
hard-coded heuristics that beat us on the ladder."* 3 Musketeers (2021) hit the
matching failure from the other side, noting the gap *"between the maps used in
scrims and the maps used in the final tournament, especially considering
different maps can drastically change what strategies are optimal."*

**→ for us.** Read the first two findings against a constraint none of these
teams had: **we are running outside an actual tournament, so scrimmages are
simply unavailable.** That is a real loss and worth being precise about why. A
live ladder supplies an opponent set that is diverse *and roughly calibrated to
your current ability*, because the whole field improves together through the
season. The calibration is as valuable as the diversity, and it is exactly what
we cannot manufacture.

What we have instead, and what each instrument is actually good for:

| instrument | diverse? | calibrated to us? | what it measures |
|---|---|---|---|
| twice-daily tournament | somewhat (2 rival lineages) | yes | **relative** standing, zero-sum |
| frozen roster (`vs_old_bots`) | no (descends from you) | yes | **absolute** progress along your own lineage |
| benchmark finalists | yes | **no — far above us** | distance to a tournament-winning bot |
| mirror / self-play null | no | exactly | variance floor, which is **zero** here |

The 3 Musketeers warning is the one to take most seriously. Our accept/reject
decisions turn on small margins within a fixed map list, which is precisely the
"tuned on the scrim maps" failure they describe. A gain that lives on a handful
of maps is fitted to those maps until shown otherwise.

And note what the lopsidedness of the benchmark instrument does: when you lose
most games against it anyway, a change that makes you substantially *worse* has
very little room to show up. **A lopsided instrument measures direction poorly in
both directions** — it is a distance gauge, not a regression detector. That is
what the frozen roster is for.

---

## 2. What to work on, and in what order

**Basics beaten well outperform sophistication.** Java Best Waifu, the 2020
**winner**: *"the most important factors … Simplicity, Robustness and Structured
Code. In my personal experience, every time I'd try to implement a sophisticated
strategy that requires a lot of coordination it would always flop since
everything that can go wrong does go wrong. Usually the bots that perform the
best are those that perform the basics really well."*

**Robustness over optimality.** don't @ me (2023): *"Make it work, make it right,
make it fast … Don't try to invent Battlecode Stockfish without having the basic
dumb 'run straight at the nearest thing' bot done … optimality is often not so
important as robustness."*

**Infrastructure first.** Stone Tao (2020) states it most directly: working on
infrastructure first is *"always much more beneficial"* than chasing the current
strategic fad, because pathfinding, communication and basic combat rarely need
rewriting even as the strategy on top of them turns over under balance patches.

**Prioritise by expected win-rate — and do not fix everything a replay shows
you.** The High Ground: *"it is not a good strategy to go through a replay and
note every single area of improvement, then go fix them all immediately. Rather,
use a task management system … If you are having trouble determining which things
are the highest priority, think about how much the change will increase your win
rate."*

**→ for us.** The last one cuts directly against how this project spends
iterations. Our loop is replay-trace-driven — exactly the mode The High Ground
warns produces a long undifferentiated fix list. A trace tells you a mechanism is
*present*; it does not tell you the mechanism is *worth* anything, and this
project has repeatedly proven a mechanism real and then found it converts to no
wins at all.

The coordination warning deserves special weight here. "Sophisticated strategy
requiring a lot of coordination" is the thing the 2020 winner says *always*
flops, and multi-unit coordination proposals are a recurring shape in all three
lineages' ledgers. Before building one, see §7 — the cross-year answer is to get
coordination as an emergent property of local rules instead.

---

## 3. Root-cause real failures rather than working around them

Post-mortems are consistently candid about concrete bugs, and the pattern in
*how* they were found is itself the lesson: nearly every serious bug was caught
by watching an actual game end unexpectedly, not by code review or intuition.

- **4 Musketeers (2023)** lost a top-seed qualifier to a null-pointer exception.
  Headquarters clustered in a map corner exhausted their bytecode budget scanning
  for build locations before ever reaching the step that recorded sibling HQ
  locations, silently leaving those references null for the rest of the game. The
  fix — a hard bytecode budget check — was trivial once understood. The hard part
  was noticing it happened at all.
- **Gone Fishin' (2023)** diagnosed a finals loss to a specific mechanical cause
  (a spiral scouting pattern optimised for a central spawn performed badly on a
  map with distant resources) rather than to bad luck, which let them say
  precisely what to fix instead of guessing.
- **Both wololo (2021) and 4 Musketeers (2023)** describe multi-day root-cause
  chases for pathfinding deadlocks — map "jail" shapes, current-driven pits —
  that were only fixed once someone found the *specific* obstacle geometry
  breaking their assumptions, rather than patching around the symptom.

**→ for us.** "Why did this specific game end this way" is more valuable than an
aggregate win rate on its own. A single well-understood loss, traced to its
mechanical cause, produces a more reliable fix than a statistical pattern with no
mechanism behind it. This is the strongest argument for the loss-replay habit —
and it is the *complement* to §2, not a contradiction: trace to find the
mechanism, then price the mechanism before building on it.

---

## 4. Communication is a scarce, structured resource

Every year imposes a tiny shared channel, and every strong team treats *what to
store and how to compress it* as a first-class design problem rather than an
afterthought.

- **Coordinates are expensive; abstract them.** wololo (2021) found that
  transmitting `location mod 128` uniquely reconstructed a position on any map
  that year, since no map exceeded 64 tiles per axis. 4 Musketeers (2023) went
  further and stopped communicating exact locations at all: they divided the map
  into **sectors** and broadcast which sector an enemy or resource was in (7 bits)
  instead of its exact tile (12 bits) — cheaper, and appropriately coarse, since
  units re-resolve exact positions with their own vision once they arrive.
- **Batch writes.** Don't write field-by-field as information arrives. Read the
  array into a local copy, mutate with dirty flags, flush once. 4 Musketeers
  explicitly borrowed the database "buffer pool" pattern after write
  amplification from a naive sector-packing scheme ate half a robot's bytecode
  budget.
- **Log-encode wide-range, coarse-precision quantities.** wololo transmitted
  `log(quantity)` and exponentiated on read, preserving useful precision at both
  ends of a range spanning orders of magnitude.
- **A lazily-refreshed local cache beats a global source of truth every robot
  re-derives.** 4 Musketeers gave every robot a `SectorInfo` cache so it could
  accumulate 100+ rounds of observations before ever getting a chance to write
  them back.

**Takeaway independent of any year's rules:** decide the *units of information*
that actually matter — which region, which target, which threat — before deciding
the bit layout, and design for infrequent, batched, lossy-but-good-enough writes
rather than keeping every robot perfectly synchronised.

**→ for us.** The trap this project keeps rediscovering is the opposite one:
proposing a schema before establishing that a decision exists which the
information would change. The cross-year practice assumes the decision is
already identified and the *encoding* is the hard part. Name the badly-made
decision first; the bit layout is the easy half.

---

## 5. Pathfinding: hybrid bug-navigation, not pure BFS/A*

The most consistent engineering story across every year. Teams start with
textbook A*/BFS, discover it blows the bytecode budget, and converge on the same
family of solution:

1. **Bug navigation as the fallback.** Move toward the target; when blocked,
   follow the obstacle boundary (turning consistently one way) until the direct
   path clears. Cheap, bytecode-bounded, correct on convex obstacles.
2. **A stack of past turns to escape concave ("C"-shaped) obstacles**, which
   plain bug-nav gets stuck in. Gone Fishin' (2023) added a directional stack so
   a robot could detect it had fully circumnavigated an obstacle and reset.
3. **An unrolled, unit-distance BFS for local movement** — generated or
   hand-written as a flat sequence of `if` statements over a fixed radius
   (radius² ≤ 20 appears independently in wololo's 2021 and 4 Musketeers' 2023
   solutions). A real shortest-path search whose *shape* is fixed at compile
   time, so it costs a predictable small amount instead of scaling with a
   dynamically-sized frontier.
4. **Simulate before committing on hard cases.** wololo's later versions ran a
   bounded simulation of turning left vs. right and picked whichever made more
   progress within budget, falling back to a coin flip only if neither finished.
5. **Treat friendly units as soft, not hard, obstacles**, with randomness as a
   last resort. Gone Fishin's best late-tournament setting was "friendly units are
   walls 75% of the time, empty 25%" — between "never block" (pileups) and
   "always block" (gridlock). Multiple teams independently added randomised
   tie-breaking specifically to escape movement loops a deterministic algorithm
   gets stuck in forever.
6. **Detect obstacle endpoints rather than tracing the whole boundary.** 4
   Musketeers approximated an obstacle's two farthest points across several turns
   of budgeted background computation, then always knew which way to go around it
   without re-tracing.

**Takeaway:** don't chase an asymptotically-optimal pathfinder. The winning
pattern is a fast good-enough greedy step, plus a bounded escape mechanism for
the specific shapes greedy movement actually gets stuck on, plus a randomised
tie-break as a safety valve.

---

## 6. Never assume map symmetry — infer it, then exploit it

Every Battlecode map is guaranteed one of a small number of symmetry types
(rotational, horizontal, vertical) for fairness. This is free information.

The standard practice is to *infer* it rather than be told: hold all candidate
symmetries as live hypotheses at round 1 and eliminate them as terrain is
observed — any tile that contradicts a candidate kills it permanently. Once one
candidate survives, every friendly landmark you have seen implies the location of
its mirror, including the enemy's.

**→ for us.** This is "Battlecode 101" everywhere else and it is worth checking
whether any lineage here has actually built it. It converts local observation
into global knowledge with no communication at all, which makes it unusually
cheap relative to what it buys — and note it is a *derivation*, not a heuristic:
once the symmetry is pinned, the inference is exact.

---

## 7. Micro outweighs macro — and coordination should emerge, not be commanded

Gone Fishin' (2023) state the size of this effect explicitly from their own
experience: *"a slightly improved macro strategy might increase our win rate by
5%, but micro can do a 30%-50% increase."*

Recurring specific techniques, independently discovered across multiple years:

- **Kite after every attack, unconditionally.** Where a unit can attack every
  round but move only every other round, attacking then retreating outside enemy
  range means you take far fewer hits than you land. Gone Fishin' tried
  *conditional* kiting and found "always kite back" beat it in every test — a
  result corroborated independently by that year's winner.
- **If you can attack, attack — even blindly.** When vision and attack radii
  differ, or terrain obscures vision, a unit with an attack available should fire
  at a last-known position or plausible guess rather than pass; the cooldown
  resets either way.
- **Retreat thresholds should be aggressive, not conservative.** Gone Fishin'
  (2023), citing camelcase, found that retreating at the first scratch cost far
  more in lost damage-per-turn than it saved in survival. "Critical HP only, and
  only if not already winning" let units keep trading instead of perpetually
  running home half-healed.
- **Retreat and heal as a group.** 4 Musketeers found that when 3 of 4 units peel
  off to heal, the undamaged 4th dies alone anyway — so the rule is "if a nearby
  ally must retreat and you aren't clearly winning without them, retreat
  together."
- **Target-prioritise by kill-efficiency, not raw threat.** Prefer targets
  killable in the fewest turns; a fast kill removes a damage-dealer from the
  fight immediately.
- **Prefer axis-aligned movement on tied distance.** Diagonal steps cover more
  Euclidean distance per action and desynchronise a formation that started
  aligned.

**Coordination without communication.** Several of the most elegant solutions
produced group behaviour from purely local rules:

- **Spawn order as implicit coordination.** Gone Fishin' spawned the first four
  units of a rush in a square with the earliest-spawned units placed *farthest*
  from the base. Because units act in spawn order, outer units moved first and
  inner units never mistook them for static obstacles. This one change won
  roughly **two-thirds of self-play games** against an otherwise identical bot.
- **Repulsion fields for map coverage.** wololo's explorers treated every other
  visible explorer as a repulsive charge — but only if that explorer was at least
  as close to unexplored ground — spreading the group thinly with no unit knowing
  anyone else's assignment.
- **A momentum term beats a pure force vector.** wololo's explorers preferred
  continuing roughly along their existing heading, producing straight efficient
  sweeps instead of jittery back-and-forth.

**→ for us.** This is the constructive answer to §2's warning. The lesson is not
"coordination doesn't work" — it is that *commanded* coordination flops while
*emergent* coordination is cheap and robust. The spawn-order result is the one to
sit with: a two-thirds self-play win from an ordering change, with no messages
sent and no shared state at all.

---

## 8. Find the real scarce resource, and price it

wololo's (2021) analysis is the clearest articulation. A "resource" worth
optimising for is anything where (a) having none of it is close to a loss
condition, (b) you can remove it from the opponent, and (c) the opponent can make
it hard for you to get.

By that definition the year's headline resource is only *one* resource — and so
is **total unit count**. Recognising unit count as an independently tradeable
currency, separate from the material it is built from, opened a whole strategic
layer (forcing unfavourable material-for-unit-count trades on the opponent) that
a team watching only the headline number would miss entirely.

**Then build an exchange rate, even a crude one.** Once you know which resources
matter, having *any* explicit model of what one is worth in terms of another lets
individual unit decisions be judged against a consistent standard instead of ad
hoc rules. wololo's calculator converted unit count and conviction into a single
currency via a tunable rate before deciding whether an action was favourable —
and that produced sensible emergent behaviour (avoiding bad trades, healing when
nothing better was available) without those behaviours being hand-coded.

It does not need to be sophisticated. wololo's was a linear function of income
rate and still beat opponents with no model at all, *"because most other teams
did not make use of exchange rates anyways."*

**→ for us.** Apply criterion (b) honestly. A quantity you cannot take from the
opponent is a constraint, not a resource, and optimising it is a different and
usually smaller job than it looks.

---

## 9. Don't commit early to one paradigm; expect the meta to shift

Every year features some version of *rush* vs. *turtle*, and the strongest
performances come from bots that decide **per-game, from measurable signals**,
rather than committing at compile time. Measure what distinguishes a
rush-favourable map from a turtle-favourable one — distance to opponent, terrain
passability, resource density — and branch on it, re-evaluating continuously
rather than deciding once at round 1.

Every year's post-mortems also mention at least one mid-season balance change
that invalidated a leading strategy overnight. The lesson: treat any strategy
exploiting a razor-thin numeric edge — a slightly favourable trade ratio, a
barely-affordable rush timing — as inherently fragile, and keep the underlying
mechanics decoupled enough from the strategy on top that a pivot doesn't require
rewriting everything. Teams that could re-derive a strategy from first principles
within days recovered; teams that had coupled their infrastructure to one
strategic assumption did not.

**→ for us.** Our engine is frozen, so the *balance-patch* half doesn't apply
directly. The transferable half does: a fixed strategic identity is a liability,
and a gain that depends on a thin numeric margin is fragile even without a patch
— it just gets invalidated by an opponent's next iteration instead of by the
engine's.

---

## 10. Endgame discipline, and when to rewrite

**Do not thrash, and do not freeze.** The High Ground (2020) reports both failure
modes in consecutive years — 2019: *"we were far too cautious … this led to us
falling from the top team to a deserved 4th place finish"*; 2020: *"we tried to
make too many changes, and didn't make any individual one of them super well."*
Their conclusion: *"choose one or two impactful improvements to your bot, and
make them very well."*

**Rewrite rather than retrofit when the strategy changes.** Java Best Waifu (2020
winner): *"if the code undergoes drastic changes (for instance because you change
the bot's main strategy) I would suggest to do a bot from scratch. It is usually
faster than expected and it is way better on the long run."*

**→ for us.** The rewrite advice is the most actionable unexplored idea in this
document, and it is aimed squarely at a lineage that has accumulated many
incremental edits to one file and concluded it needs an idea from outside the
space it has been searching. The 2020 winner's claim is that at exactly that
point, from-scratch is faster than it looks. It is a high-variance move — which
is an argument for one lineage trying it, not all three.

---

## 11. The short list, when stuck

1. **Triangulate; no instrument is a verdict alone.** The tournament is relative,
   the frozen roster is absolute-but-inbred, the benchmarks are diverse but far
   above us and nearly blind to regressions. Each covers another's blind spot.
2. **Check whether symmetry inference exists in your bot** (§6). It is standard
   everywhere else, it needs no communication, and it is exact rather than
   heuristic.
3. **Look for emergent coordination, not commanded coordination** (§7). Spawn
   order, repulsion, momentum — local rules that produce group behaviour. The
   spawn-order result was worth two-thirds of self-play games.
4. **Prefer robustness and simplicity over sophistication** (§2). Every year says
   the elaborate coordinated plan flops.
5. **Price the mechanism before building on it** (§2, §3). A trace proves a
   mechanism exists; it does not prove the mechanism is worth anything.
6. **Ask whether a gain is map-specific** (§1). Small margins on a fixed map list
   are fitted to that list until shown otherwise.
7. **Name the badly-made decision before designing a schema** (§4).
8. **Check that your "resource" is one the opponent can deny you** (§8).
9. **Consider a from-scratch rewrite** rather than another incremental edit
   (§10) — high variance, so at most one lineage at a time.

---

## Sources

Post-mortems from 2019, 2020, 2021, 2023 and 2024, hosted at
`battlecode.org/assets/files/postmortem-<year>-<team>.pdf`, except wololo's
(`postmortem-2021-wololo.pdf`) and Stone Tao's
(`stonet2000.github.io/battlecode/2020/`). The index of all published
post-mortems is at [battlecode.org/past.html](https://battlecode.org/past.html).

Teams cited here: Oak's Last Disciple (2019), Java Best Waifu (2020 winner),
Stone Tao (2020), The High Ground (2019–2020), wololo (2021), 3 Musketeers
(2021), Gone Fishin' (2023), 4 Musketeers (2023), don't @ me (2023), camelcase.

**2025 post-mortems are excluded by project rule and are not cited, quoted or
paraphrased anywhere in this file.**

A caution recorded by the predecessor that built the first version of this
document, and worth repeating: **summarising these PDFs through a web-fetch tool
produced confident fabricated quotes** — invented percentages appearing nowhere
in the source. If you extend this file, extract the text and read it.

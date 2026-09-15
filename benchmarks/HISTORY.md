# Benchmark history

**Records only.** A row appears here when a lineage beat its own previous best
against that benchmark over a COMPLETE run — every map, both sides,
150 games. Runs that did not improve on the record are not listed, and
neither are the small map-subset probes used to read indicator strings: a 1/12
and a 56/150 are not the same measurement.

Nothing is lost by the filtering. This file is regenerated from the
`scores.csv` in each run directory, so any run can be recovered in full by
reading its own directory under `benchmarks/`.

Scores only — no replay of a benchmark game is ever written by `benchmark.sh`.

**These are a yardstick, not a target.** A benchmark bot must never become a
gauntlet or roster opponent, and `TSPAARKHS` is never a selection instrument.
Read the win% in one direction only: while it sits near the floor the
instrument has little room to show a *regression*, so it measures distance to a
tournament-winning bot and nothing else. Absolute progress is what each
lineage's frozen roster reports.

## Records vs `TSPAARKHS`

| run | build | won | played | win% | previous record | gain |
|---|---|---|---|---|---|---|
| 20260908-0212 | `alice` | 0 | 150 | **0.0%** | — | first |
| 20260908-0212 | `bob` | 0 | 150 | **0.0%** | — | first |
| 20260908-0212 | `carol` | 0 | 150 | **0.0%** | — | first |
| 20260910-0149 | `alice` | 2 | 150 | **1.3%** | 0.0% | +1.3 |
| 20260910-2317 | `darla` | 1 | 150 | **0.7%** | — | first |

Current record: **alice 1.3%** (run 20260910-0149), **bob 0.0%** (run 20260908-0212), **carol 0.0%** (run 20260908-0212), **darla 0.7%** (run 20260910-2317).

## Records vs `v3`

| run | build | won | played | win% | previous record | gain |
|---|---|---|---|---|---|---|
| 20260908-0212 | `alice` | 12 | 150 | **8.0%** | — | first |
| 20260908-0212 | `bob` | 7 | 150 | **4.7%** | — | first |
| 20260908-0212 | `carol` | 8 | 150 | **5.3%** | — | first |
| 20260909-0133 | `alice` | 19 | 150 | **12.7%** | 8.0% | +4.7 |
| 20260909-0133 | `carol` | 31 | 150 | **20.7%** | 5.3% | +15.3 |
| 20260910-0149 | `alice` | 26 | 150 | **17.3%** | 12.7% | +4.7 |
| 20260910-0149 | `carol` | 37 | 150 | **24.7%** | 20.7% | +4.0 |
| 20260910-2317 | `darla` | 51 | 150 | **34.0%** | — | first |
| 20260911-1112 | `darla` | 63 | 150 | **42.0%** | 34.0% | +8.0 |
| 20260913-0058 | `darla` | 65 | 150 | **43.3%** | 42.0% | +1.3 |
| 20260914-0717 | `darla` | 69 | 150 | **46.0%** | 43.3% | +2.7 |
| 20260915-1427 | `darla` | 72 | 150 | **48.0%** | 46.0% | +2.0 |

Current record: **alice 17.3%** (run 20260910-0149), **bob 4.7%** (run 20260908-0212), **carol 24.7%** (run 20260910-0149), **darla 48.0%** (run 20260915-1427).

## Per-run detail — record-setting runs only

### 20260908-0212

| agent | benchmark | won | played | win% | swept | swept against | played build |
|---|---|---|---|---|---|---|---|
| alice | TSPAARKHS | 0 | 150 | 0.0% | 0 | 75 | `25c3160` |
| alice | v3 | 12 | 150 | 8.0% | 1 | 64 | `25c3160` |
| bob | TSPAARKHS | 0 | 150 | 0.0% | 0 | 75 | `e425f46` |
| bob | v3 | 7 | 150 | 4.7% | 1 | 69 | `e425f46` |
| carol | TSPAARKHS | 0 | 150 | 0.0% | 0 | 75 | `6c55fc4` |
| carol | v3 | 8 | 150 | 5.3% | 1 | 68 | `6c55fc4` |

### 20260909-0133

| agent | benchmark | won | played | win% | swept | swept against | played build |
|---|---|---|---|---|---|---|---|
| alice | TSPAARKHS | 0 | 150 | 0.0% | 0 | 75 | `920dafd` |
| alice | v3 | 19 | 150 | 12.7% | 4 | 60 | `920dafd` |
| bob | TSPAARKHS | 0 | 150 | 0.0% | 0 | 75 | `e425f46` |
| bob | v3 | 7 | 150 | 4.7% | 1 | 69 | `e425f46` |
| carol | TSPAARKHS | 0 | 150 | 0.0% | 0 | 75 | `5be82ca` |
| carol | v3 | 31 | 150 | 20.7% | 8 | 52 | `5be82ca` |

### 20260910-0149

| agent | benchmark | won | played | win% | swept | swept against | played build |
|---|---|---|---|---|---|---|---|
| alice | TSPAARKHS | 2 | 150 | 1.3% | 0 | 73 | `55c8037` |
| alice | v3 | 26 | 150 | 17.3% | 8 | 57 | `55c8037` |
| bob | TSPAARKHS | 0 | 150 | 0.0% | 0 | 75 | `b85c7cf` |
| bob | v3 | 7 | 150 | 4.7% | 1 | 69 | `b85c7cf` |
| carol | TSPAARKHS | 0 | 150 | 0.0% | 0 | 75 | `3610230` |
| carol | v3 | 37 | 150 | 24.7% | 10 | 48 | `3610230` |

### 20260910-2317

| agent | benchmark | won | played | win% | swept | swept against | played build |
|---|---|---|---|---|---|---|---|
| darla | TSPAARKHS | 1 | 150 | 0.7% | 0 | 74 | `4335c3c` |
| darla | v3 | 51 | 150 | 34.0% | 16 | 40 | `4335c3c` |

### 20260911-1112

| agent | benchmark | won | played | win% | swept | swept against | played build |
|---|---|---|---|---|---|---|---|
| darla | TSPAARKHS | 0 | 150 | 0.0% | 0 | 75 | `8dc8f37` |
| darla | v3 | 63 | 150 | 42.0% | 23 | 35 | `8dc8f37` |

### 20260913-0058

| agent | benchmark | won | played | win% | swept | swept against | played build |
|---|---|---|---|---|---|---|---|
| darla | v3 | 65 | 150 | 43.3% | 19 | 29 | `bedb743` |

### 20260914-0717

| agent | benchmark | won | played | win% | swept | swept against | played build |
|---|---|---|---|---|---|---|---|
| darla | v3 | 69 | 150 | 46.0% | 24 | 30 | `6a8b72a` |

### 20260915-1427

| agent | benchmark | won | played | win% | swept | swept against | played build |
|---|---|---|---|---|---|---|---|
| darla | v3 | 72 | 150 | 48.0% | 25 | 28 | `b32cad5` |

---

104 run directories on disk. 64 complete scored result(s), of which 35 were unshipped candidates; 58 map-subset probe(s) excluded as too small to compare; 17 record(s) shown.


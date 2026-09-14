#!/usr/bin/env python3
"""Regenerate benchmarks/HISTORY.md from every benchmark run on disk.

REGENERATED, never appended. Appending would duplicate rows whenever a run is
re-collated by benchmark-collect.sh, and would leave a stale row if a run were
ever re-scored. Rebuilding from the scores.csv files makes the history a
function of the data -- idempotent by construction, and correct after a
recovery -- which is the same reason cron-benchmark.sh keys on the artifact
rather than on a run-id pattern.

Called from benchmark-collate.sh, so BOTH the live path and the recovery path
update the history.
"""
import csv, collections, pathlib, re, sys

REPO = pathlib.Path(__file__).resolve().parent.parent
BENCH = REPO / "benchmarks"


def load(run_dir):
    """-> {(agent, benchmark): dict}, plus the commit each agent played."""
    f = run_dir / "scores.csv"
    if not f.is_file():
        return None, {}
    per = collections.defaultdict(lambda: {"won": 0, "played": 0, "maps": collections.defaultdict(list)})
    try:
        for r in csv.DictReader(f.open()):
            k = (r["agent"], r["benchmark"])
            per[k]["played"] += 1
            if r["agent_result"] == "win":
                per[k]["won"] += 1
            per[k]["maps"][r["map"]].append(r["agent_result"])
    except (OSError, csv.Error, KeyError):
        return None, {}

    out = {}
    for k, v in per.items():
        sw = sum(1 for res in v["maps"].values() if len(res) == 2 and all(x == "win" for x in res))
        sl = sum(1 for res in v["maps"].values() if len(res) == 2 and all(x == "loss" for x in res))
        out[k] = {"won": v["won"], "played": v["played"], "swept": sw, "against": sl}

    commits = {}
    bots = run_dir / "bots.txt"
    if bots.is_file():
        for line in bots.read_text().splitlines():
            parts = line.split()
            if len(parts) >= 2:
                commits[parts[0]] = parts[1]
    return out, commits


def lineage(agent):
    """darla, darla102, darla117 -> "darla". Arms are the lineage, not new agents."""
    m = re.match(r"[a-z]+", agent)
    return m.group(0) if m else agent


def full_size():
    """Games in a COMPLETE benchmark: every map, both sides.

    Derived from the map list rather than hardcoded, so it stays correct if the
    pool changes. Runs smaller than this are probes -- 12-game map subsets used
    to read indicator strings -- and must never set or beat a record: a 1/12 and
    a 56/150 are not the same measurement and putting them in one column is what
    made this file unreadable.
    """
    f = REPO / "tools" / "bc25-maps.txt"
    n = sum(1 for line in f.read_text().splitlines() if line.strip()) if f.is_file() else 75
    return 2 * n


def main():
    runs = sorted(d for d in BENCH.iterdir()
                  if d.is_dir() and re.fullmatch(r"\d{8}-\d{4,6}", d.name)) if BENCH.is_dir() else []
    data = [(d.name, *load(d)) for d in runs]
    data = [(n, s, c) for n, s, c in data if s]
    if not data:
        print("!! no benchmark runs with scores.csv found", file=sys.stderr)
        return 1

    FULL = full_size()
    benchmarks = sorted({b for _, s, _ in data for (_, b) in s})

    # One pass per benchmark, chronological, keeping only runs that beat the
    # lineage's own previous best.
    records = {}          # benchmark -> [(run, agent, v, pct, prev)]
    keep_runs = set()
    n_full = n_probe = n_arm = 0
    for b in benchmarks:
        best = {}
        rows = []
        for name, sc, _ in data:
            for (a, bm), v in sorted(sc.items()):
                if bm != b or not v["played"]:
                    continue
                if v["played"] < FULL:
                    n_probe += 1
                    continue
                n_full += 1
                # SHIPPED BUILDS ONLY. `darla109` scored 46.7% on a full run and was
                # then CLOSED -- one game over the incumbent, inside noise. Listing a
                # rejected candidate as the lineage record would say Darla improved
                # when Darla did not change at all. Every accepted iteration is
                # re-benchmarked under the plain lineage name (see the benchmark-on-
                # accept rule), so nothing real is missed by this.
                if a != lineage(a):
                    n_arm += 1
                    continue
                pct = 100.0 * v["won"] / v["played"]
                lin = lineage(a)
                if lin in best and pct <= best[lin] + 1e-9:
                    continue
                rows.append((name, a, v, pct, best.get(lin)))
                best[lin] = pct
                keep_runs.add(name)
        records[b] = rows

    L = ["# Benchmark history",
         "",
         "**Records only.** A row appears here when a lineage beat its own previous best",
         "against that benchmark over a COMPLETE run — every map, both sides,",
         f"{FULL} games. Runs that did not improve on the record are not listed, and",
         "neither are the small map-subset probes used to read indicator strings: a 1/12",
         "and a 56/150 are not the same measurement.",
         "",
         "Nothing is lost by the filtering. This file is regenerated from the",
         "`scores.csv` in each run directory, so any run can be recovered in full by",
         "reading its own directory under `benchmarks/`.",
         "",
         "Scores only — no replay of a benchmark game is ever written by `benchmark.sh`.",
         "",
         "**These are a yardstick, not a target.** A benchmark bot must never become a",
         "gauntlet or roster opponent, and `TSPAARKHS` is never a selection instrument.",
         "Read the win% in one direction only: while it sits near the floor the",
         "instrument has little room to show a *regression*, so it measures distance to a",
         "tournament-winning bot and nothing else. Absolute progress is what each",
         "lineage's frozen roster reports.",
         ""]

    for b in benchmarks:
        L += [f"## Records vs `{b}`", ""]
        rows = records[b]
        if not rows:
            L += ["No complete run has been scored against this benchmark yet.", ""]
            continue
        L += ["| run | build | won | played | win% | previous record | gain |",
              "|---|---|---|---|---|---|---|"]
        for name, a, v, pct, prev in rows:
            p = "—" if prev is None else f"{prev:.1f}%"
            g = "first" if prev is None else f"+{pct - prev:.1f}"
            L.append(f"| {name} | `{a}` | {v['won']} | {v['played']} | **{pct:.1f}%** | {p} | {g} |")
        L.append("")
        cur = {}
        for name, a, v, pct, prev in rows:
            cur[a] = (pct, name)
        L += ["Current record: " + ", ".join(
            f"**{a} {pct:.1f}%** (run {run})" for a, (pct, run) in sorted(cur.items())) + ".", ""]

    L += ["## Per-run detail — record-setting runs only", ""]
    for name, sc, commits in data:
        if name not in keep_runs:
            continue
        L += [f"### {name}", "",
              "| agent | benchmark | won | played | win% | swept | swept against | played build |",
              "|---|---|---|---|---|---|---|---|"]
        for (a, bmk), v in sorted(sc.items()):
            pct = 100.0 * v["won"] / v["played"] if v["played"] else 0.0
            L.append(f"| {a} | {bmk} | {v['won']} | {v['played']} | {pct:.1f}% | "
                     f"{v['swept']} | {v['against']} | `{commits.get(a, '?')}` |")
        L.append("")

    L += ["---", "",
          f"{len(data)} run directories on disk. {n_full} complete scored result(s), "
          f"of which {n_arm} were unshipped candidates; {n_probe} map-subset probe(s) "
          f"excluded as too small to compare; "
          f"{sum(len(r) for r in records.values())} record(s) shown.", ""]

    (BENCH / "HISTORY.md").write_text("\n".join(L) + "\n")
    print(f"wrote {BENCH / 'HISTORY.md'} ({len(data)} run(s), "
          f"{sum(len(r) for r in records.values())} record(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())

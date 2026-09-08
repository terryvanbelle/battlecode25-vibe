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


def main():
    runs = sorted(d for d in BENCH.iterdir()
                  if d.is_dir() and re.fullmatch(r"\d{8}-\d{4,6}", d.name)) if BENCH.is_dir() else []
    data = [(d.name, *load(d)) for d in runs]
    data = [(n, s, c) for n, s, c in data if s]
    if not data:
        print("!! no benchmark runs with scores.csv found", file=sys.stderr)
        return 1

    pairs = sorted({k for _, s, _ in data for k in s})
    L = ["# Benchmark history",
         "",
         "Every finalist-bot benchmark run, oldest first. Scores only — no replay of",
         "these games was ever written, so there is nothing here but the numbers.",
         "",
         "**These are a yardstick, not a target.** A benchmark bot must never become a",
         "gauntlet or roster opponent. And read the win% in one direction only: while it",
         "sits near the floor the instrument has little room to show a *regression*, so it",
         "measures distance to a tournament-winning bot and nothing else. Absolute",
         "progress is what each lineage's frozen roster reports.",
         "",
         "## Win rate over time",
         "",
         "| run | " + " | ".join(f"{a} vs {b}" for a, b in pairs) + " |",
         "|---" * (len(pairs) + 1) + "|"]

    prev = {}
    for name, sc, _ in data:
        cells = []
        for k in pairs:
            v = sc.get(k)
            if not v or not v["played"]:
                cells.append("—")
                continue
            pct = 100.0 * v["won"] / v["played"]
            d = ""
            if k in prev:
                delta = pct - prev[k]
                d = f" ({delta:+.1f})" if abs(delta) >= 0.05 else " (=)"
            cells.append(f"{v['won']}/{v['played']} {pct:.1f}%{d}")
            prev[k] = pct
        L.append(f"| {name} | " + " | ".join(cells) + " |")

    L += ["", "## Per-run detail", ""]
    for name, sc, commits in data:
        L.append(f"### {name}")
        L.append("")
        L.append("| agent | benchmark | won | played | win% | swept | swept against | played build |")
        L.append("|---|---|---|---|---|---|---|---|")
        for (a, b) in pairs:
            v = sc.get((a, b))
            if not v:
                continue
            pct = 100.0 * v["won"] / v["played"] if v["played"] else 0.0
            L.append(f"| {a} | {b} | {v['won']} | {v['played']} | {pct:.1f}% | "
                     f"{v['swept']} | {v['against']} | `{commits.get(a, '?')}` |")
        L.append("")

    (BENCH / "HISTORY.md").write_text("\n".join(L) + "\n")
    print(f"wrote {BENCH / 'HISTORY.md'} ({len(data)} run(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())

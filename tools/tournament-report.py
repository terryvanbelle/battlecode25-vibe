#!/usr/bin/env python3
"""Write a human-readable report for a finished tournament, and update the
running league table across every tournament so far.

`summary.txt` already answers "what happened in this run". This answers the
question a person actually asks -- "how did it go?" -- which is a question about
CHANGE: who moved, against whom, and whether the move is big enough to mean
anything. Run by tools/cron-tournament.sh before it commits the results, so it
happens on every tournament whether or not anyone is watching.

    tools/tournament-report.py <run-id>     # default: newest in tournaments/

Writes tournaments/<run-id>/report.md and rewrites tournaments/HISTORY.md.

READ THE CAVEAT IT PRINTS. A full run plays all 75 maps, but a truncated one
plays a random subset, so a delta between a complete run and a truncated one is
measured on different ground and is noisier than it looks. The report says so
rather than letting a reader treat every number as comparable.
"""
import csv
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TDIR = REPO / "tournaments"
RUN_ID = re.compile(r"^\d{8}-\d{4}$")


def runs():
    return sorted(p for p in TDIR.iterdir()
                  if p.is_dir() and RUN_ID.match(p.name) and (p / "results.csv").is_file())


def load(run):
    """-> (wins {bot: n}, played {bot: n}, h2h {(x,y): x's wins}, sweeps, rows)"""
    rows = list(csv.DictReader((run / "results.csv").open()))
    rows = [r for r in rows if r.get("winner_bot") and r["winner_bot"] != "unknown"]
    wins, played = defaultdict(int), defaultdict(int)
    h2h = defaultdict(int)
    bymap = defaultdict(list)
    for r in rows:
        a, b, w = r["team_a"], r["team_b"], r["winner_bot"]
        wins[w] += 1
        played[a] += 1
        played[b] += 1
        h2h[(w, b if w == a else a)] += 1
        bymap[(tuple(sorted((a, b))), r["map"])].append(w)
    sweeps = defaultdict(int)
    for (pair, _), ws in bymap.items():
        if len(ws) == 2 and ws[0] == ws[1]:
            sweeps[(ws[0], pair[1] if ws[0] == pair[0] else pair[0])] += 1
    return wins, played, h2h, sweeps, rows


def pct(w, t):
    return 100.0 * w / t if t else 0.0


def flags(run):
    """Forfeits and truncation, read back from the run's own summary."""
    s = (run / "summary.txt")
    if not s.is_file():
        return [], False
    text = s.read_text()
    forfeits = [l.strip(" !").strip() for l in text.splitlines() if "FORFEIT" in l]
    return forfeits, "!! INCOMPLETE" in text


def played_commits(run):
    f = run / "bots.txt"
    if not f.is_file():
        return {}
    out = {}
    for line in f.read_text().splitlines():
        parts = line.split(None, 2)
        if len(parts) >= 2:
            out[parts[0]] = (parts[1], parts[2] if len(parts) > 2 else "")
    return out


def arrow(d):
    if d is None:
        return "     —"
    return f"  {d:+5.1f}" if abs(d) >= 0.05 else "   0.0"


def main():
    all_runs = runs()
    if not all_runs:
        sys.exit("!! no tournaments with results.csv yet")
    want = sys.argv[1] if len(sys.argv) > 1 else all_runs[-1].name
    cur = next((r for r in all_runs if r.name == want), None)
    if cur is None:
        sys.exit(f"!! no tournament {want}")
    prev = None
    for r in all_runs:
        if r.name == cur.name:
            break
        prev = r

    wins, played, h2h, sweeps, rows = load(cur)
    bots = sorted(played)
    forfeits, incomplete = flags(cur)
    commits = played_commits(cur)

    pw, pp, ph, _, _ = load(prev) if prev else ({}, {}, {}, {}, [])
    prev_incomplete = flags(prev)[1] if prev else False
    comparable = prev is not None and not incomplete and not prev_incomplete

    L = []
    L.append(f"# Tournament {cur.name} (UTC)\n")
    if forfeits:
        for f in forfeits:
            L.append(f"> **FORFEIT** — {f}\n")
    if incomplete:
        L.append("> **INCOMPLETE** — this run was truncated. Maps are played in random\n"
                 "> order, so the games below are an unbiased random subset, not the\n"
                 "> alphabetically-first slice. Totals are not comparable to a full run.\n")
    prev_rows = len(load(prev)[4]) if prev else 0
    L.append(f"{len(rows)} decided games"
             + (f", against {prev_rows} in `{prev.name}`" if prev else "")
             + ".\n")

    L.append("\n## Standings\n")
    L.append("| bot | won | played | win% | vs last |")
    L.append("|---|---|---|---|---|")
    for b in sorted(bots, key=lambda b: -pct(wins[b], played[b])):
        d = (pct(wins[b], played[b]) - pct(pw.get(b, 0), pp.get(b, 0))) if comparable and pp.get(b) else None
        L.append(f"| {b} | {wins[b]} | {played[b]} | {pct(wins[b], played[b]):.1f}% |{arrow(d)} |")

    L.append("\n## Head to head\n")
    L.append("| matchup | record | win% | vs last |")
    L.append("|---|---|---|---|")
    for x in bots:
        for y in bots:
            if x >= y:
                continue
            t = h2h[(x, y)] + h2h[(y, x)]
            if not t:
                continue
            pt = ph.get((x, y), 0) + ph.get((y, x), 0)
            d = (pct(h2h[(x, y)], t) - pct(ph.get((x, y), 0), pt)) if comparable and pt else None
            L.append(f"| {x} vs {y} | {h2h[(x, y)]}–{h2h[(y, x)]} | {pct(h2h[(x,y)], t):.1f}% |{arrow(d)} |")

    L.append("\n## Swept maps\n")
    L.append("Won from *both* sides, so immune to spawn advantage — the honest read on a pair.\n")
    for x in bots:
        for y in bots:
            if x >= y:
                continue
            if h2h[(x, y)] + h2h[(y, x)]:
                L.append(f"- **{x}–{y}**: {x} swept {sweeps[(x,y)]}, {y} swept {sweeps[(y,x)]}")

    if commits:
        L.append("\n## What played\n")
        L.append("Each bot is exported from HEAD at tournament time, never the working tree.\n")
        for b in bots:
            sha, subj = commits.get(b, ("?", ""))
            L.append(f"- `{b}` @ `{sha}` {subj}")

    L.append("\n## Reading this\n")
    if not prev:
        L.append("First tournament — no deltas yet. From the next one on, the *vs last*\n"
                 "columns are the interesting part.")
    elif not comparable:
        why = "this run" if incomplete else "the previous run"
        L.append(f"Deltas are suppressed because {why} was truncated: a full run plays every\n"
                 "map and a truncated one a random subset, so the two are measured on\n"
                 "different ground and a delta between them would be noise dressed as signal.")
    else:
        L.append(f"Deltas compare against `{prev.name}`. Both runs were complete, so both\n"
                 "played the full map list and the two are measured on the same ground.\n"
                 "Treat a few points as noise; a pair moving together with its swept-map\n"
                 "count is the signal worth chasing.")

    (cur / "report.md").write_text("\n".join(L) + "\n")

    # -- running league table across every tournament --
    H = ["# Tournament history\n",
         "Every round-robin so far, newest last. Win% is over all games that bot",
         "played in that run. `!` marks a truncated run, whose maps are a random",
         "subset — compare those with care.\n",
         "| run | " + " | ".join(sorted({b for r in all_runs for b in load(r)[1]})) + " | games |",
         "|---" * (len(sorted({b for r in all_runs for b in load(r)[1]})) + 2) + "|"]
    allbots = sorted({b for r in all_runs for b in load(r)[1]})
    for r in all_runs:
        w, p, _, _, rr = load(r)
        mark = "!" if flags(r)[1] else ""
        cells = [f"{pct(w[b], p[b]):.1f}%" if p.get(b) else "—" for b in allbots]
        H.append(f"| {r.name}{mark} | " + " | ".join(cells) + f" | {len(rr)} |")
    (TDIR / "HISTORY.md").write_text("\n".join(H) + "\n")

    print(f"wrote {cur / 'report.md'} and {TDIR / 'HISTORY.md'}")


if __name__ == "__main__":
    main()

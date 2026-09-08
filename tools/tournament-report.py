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
    """-> (wins, played, h2h, sweeps, rows, maps-played)"""
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
    # Split maps (each side won once) and partial maps (only one game decided).
    # Splits are the ONLY thing the sweep counts add over the head-to-head
    # margin, since margin = 2*(swept - swept against) identically; partials are
    # the sole way that identity can fail, so they are counted to be reported
    # rather than silently breaking the arithmetic.
    splits, partial = defaultdict(int), defaultdict(int)
    for (pair, _), ws in bymap.items():
        if len(ws) == 2 and ws[0] == ws[1]:
            sweeps[(ws[0], pair[1] if ws[0] == pair[0] else pair[0])] += 1
        elif len(ws) == 2:
            splits[pair] += 1
        else:
            partial[pair] += 1
    return wins, played, h2h, sweeps, rows, {r['map'] for r in rows}, splits, partial


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


def activity(prev, cur):
    """Agent commits per hour between two tournaments — a proxy for how much
    work the delta actually covers.

    A delta is only as meaningful as the working time behind it, and in this
    project the agents are killed regularly by things outside their control
    (usage limits, dropped sessions). Between the first two tournaments they
    committed for about 3.5 hours of a 12-hour gap. Reporting the gap without
    that is how a delta gets read as "a day of work barely moved anything".
    """
    if prev is None:
        return None
    import subprocess
    from datetime import datetime, timezone

    def stamp(run):
        d = datetime.strptime(run.name, "%Y%m%d-%H%M").replace(tzinfo=timezone.utc)
        return d.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        out = subprocess.run(
            ["git", "log", f"--since={stamp(prev)}", f"--until={stamp(cur)}",
             "--format=%aI", "--", "agents/"],
            cwd=REPO, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    lines = [l for l in out.stdout.splitlines() if l.strip()]
    hours = {l[11:13] for l in lines}
    span = (datetime.strptime(cur.name, "%Y%m%d-%H%M")
            - datetime.strptime(prev.name, "%Y%m%d-%H%M")).total_seconds() / 3600
    return len(lines), len(hours), round(span)


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

    wins, played, h2h, sweeps, rows, cur_maps, splits, partial = load(cur)
    bots = sorted(played)
    forfeits, incomplete = flags(cur)
    commits = played_commits(cur)

    pw, pp, ph, _, _, prev_maps, _, _ = (load(prev) if prev else
        ({}, {}, {}, {}, [], set(), {}, {}))
    prev_incomplete = flags(prev)[1] if prev else False
    # Deltas require the same ground, and "not truncated" does not establish
    # that: a run played with an explicit short MAPS= list is complete and still
    # not comparable. The first report compared a 450-game run against a 2-map
    # smoke test and called both complete. So compare the map sets themselves.
    same_maps = bool(prev_maps) and cur_maps == prev_maps
    comparable = (prev is not None and not incomplete and not prev_incomplete
                  and same_maps)

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
    L.append("Won from *both* sides, so a sweep is immune to spawn advantage.\n")
    L.append("\n**These do not corroborate the head-to-head margin — they restate it.** "
             "Every map is played twice, so wins = 2·SW + D and losses = 2·SL + D, "
             "where D is the split maps; the D cancels and\n")
    L.append("\n> margin = 2 × (swept − swept against)\n")
    L.append("\nexactly, always. Verified on every pair of every run. So citing a "
             "margin *and* its sweep counts as two agreeing pieces of evidence is "
             "citing one number twice. What the sweep counts add that the margin "
             "cannot is **D, the number of split maps** — how decisive the pair is, "
             "not who is ahead. A 60–40 pair with few splits is a different animal "
             "from a 60–40 pair that is mostly coin-flips, and only the sweep counts "
             "tell them apart.\n")
    for x in bots:
        for y in bots:
            if x >= y:
                continue
            if h2h[(x, y)] + h2h[(y, x)]:
                pair = tuple(sorted((x, y)))
                extra = f", {splits[pair]} split"
                if partial[pair]:
                    extra += (f", {partial[pair]} partial (only one game decided "
                              f"— the margin identity does not hold for these)")
                L.append(f"- **{x}–{y}**: {x} swept {sweeps[(x,y)]}, "
                         f"{y} swept {sweeps[(y,x)]}{extra}")

    if commits:
        L.append("\n## What played\n")
        L.append("Each bot is exported from HEAD at tournament time, never the working tree.\n")
        for b in bots:
            sha, subj = commits.get(b, ("?", ""))
            L.append(f"- `{b}` @ `{sha}` {subj}")

    # How games actually end. Worth printing rather than leaving each lineage to
    # derive it: one derived it by hand and reported "none by elimination" when
    # two of 450 were, which is the kind of small overstatement a table prevents.
    reasons = cur / "reasons.txt"
    if reasons.is_file():
        counts = {}
        for line in reasons.read_text().splitlines():
            parts = line.split(None, 3)
            if len(parts) == 4:
                counts[parts[3]] = counts.get(parts[3], 0) + 1
        if counts:
            L.append("\n## How games ended\n")
            L.append("| outcome | games | share |")
            L.append("|---|---|---|")
            tot = sum(counts.values())
            for why, n in sorted(counts.items(), key=lambda kv: -kv[1]):
                L.append(f"| {why} | {n} | {100.0*n/tot:.1f}% |")

    L.append("\n## What this cannot tell you\n")
    L.append(
        "**These standings are relative, not absolute.** Every game has a winner\n"
        "among the three, so wins are conserved — the three win counts always sum\n"
        f"to {len(rows)}. If all three lineages improve by the same amount, every\n"
        "number above stays exactly where it is. A delta therefore means *changed\n"
        "relative to the other two*, and can never mean *got better* or *got worse*\n"
        "on its own. Absolute strength is what each agent's frozen roster measures\n"
        "(`progress/vs_old_bots.png`), because a frozen opponent cannot improve\n"
        "alongside you. Read the two together: a lineage can gain real absolute\n"
        "strength and move nowhere here, which is the normal case when all three\n"
        "are working.\n")
    act = activity(prev, cur)
    if act:
        n, hrs, span = act
        L.append(
            f"**And weigh the delta by the work behind it.** Between `{prev.name}` and\n"
            f"this run — a {span}-hour gap — the agents committed {n} times across {hrs} distinct\n"
            "hours. Commits are only a proxy, but a small delta over a mostly idle\n"
            "interval says little about the lineages and a lot about their uptime;\n"
            "sessions here are killed regularly by usage limits and dropped\n"
            "connections, which is not the agents' doing.\n")

    L.append("\n## Reading this\n")
    if not prev:
        L.append("First tournament — no deltas yet. From the next one on, the *vs last*\n"
                 "columns are the interesting part.")
    elif not comparable:
        if incomplete or prev_incomplete:
            why = "this run" if incomplete else f"`{prev.name}`"
            L.append(f"Deltas are suppressed because {why} was truncated, so the two runs\n"
                     "played different maps and a delta between them would be noise dressed\n"
                     "as signal.")
        else:
            L.append(f"Deltas are suppressed because `{prev.name}` played a different map set\n"
                     f"({len(prev_maps)} maps vs {len(cur_maps)} here). Both runs finished, but\n"
                     "finishing is not the same as covering the same ground — comparing win\n"
                     "rates across different maps measures the maps, not the bots.")
    else:
        L.append(f"Deltas compare against `{prev.name}`. Both runs were complete, so both\n"
                 "played the full map list and the two are measured on the same ground.\n"
                 "Treat a few points as noise; a pair moving together with its swept-map\n"
                 "count is the signal worth chasing.")

    (cur / "report.md").write_text("\n".join(L) + "\n")

    # -- running league table across every tournament --
    H = ["# Tournament history\n",
         "Every round-robin so far, newest last. Win% is over all games that bot",
         "played in that run. `!` marks a truncated run. The `maps` column matters:",
         "two runs are only comparable when they played the same map set.\n",
         "| run | " + " | ".join(sorted({b for r in all_runs for b in load(r)[1]})) + " | games | maps |",
         "|---" * (len(sorted({b for r in all_runs for b in load(r)[1]})) + 3) + "|"]
    allbots = sorted({b for r in all_runs for b in load(r)[1]})
    for r in all_runs:
        w, p, _, _, rr, _, _, _ = load(r)
        mark = "!" if flags(r)[1] else ""
        cells = [f"{pct(w[b], p[b]):.1f}%" if p.get(b) else "—" for b in allbots]
        nmaps = len({row["map"] for row in rr})
        H.append(f"| {r.name}{mark} | " + " | ".join(cells) + f" | {len(rr)} | {nmaps} |")
    (TDIR / "HISTORY.md").write_text("\n".join(H) + "\n")

    print(f"wrote {cur / 'report.md'} and {TDIR / 'HISTORY.md'}")


if __name__ == "__main__":
    main()

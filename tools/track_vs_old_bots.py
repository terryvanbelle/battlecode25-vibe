#!/usr/bin/env python3
"""
Record win% against a fixed roster of old snapshots, from completed gauntlet runs.

WHY THIS EXISTS, separately from the gauntlet's own summary: the gauntlet pool
moves. Opponents get retired, new snapshots replace old ones, and the map sample
is redrawn every run, so "83% this run" is measured against a different
instrument each time. This file keeps a deliberately frozen set of reference
points -- iteration 0, then every 5th accepted snapshot -- so a rising line is
absolute progress rather than a moving-target artifact.

Ported from battlecode26-vibe/battlecode22-vibe. Two changes here:
 - the roster is derived (progress_lib.roster_opponents), never hardcoded;
 - rows are keyed by (run date, opponent) rather than by current snapshot, so
   backfilling old runs works and re-processing a run replaces its rows instead
   of drawing two points on one date.

Usage (from your workspace):
    cd agents/alice

    # what should I play to extend the chart?
    ../../tools/.venv/bin/python3 ../../tools/track_vs_old_bots.py --roster

    # run it (leave MAPS unset: fresh random 25-map sample)
    OPPONENTS="$(../../tools/.venv/bin/python3 ../../tools/track_vs_old_bots.py --roster)" \
        ../../tools/gauntlet.sh

    # record it, then redraw
    ../../tools/.venv/bin/python3 ../../tools/track_vs_old_bots.py gauntlet/<run-id>
    ../../tools/.venv/bin/python3 ../../tools/plot_vs_old_bots.py

    # one-off: seed history from every gauntlet run already on disk
    ../../tools/.venv/bin/python3 ../../tools/track_vs_old_bots.py --all

Data: <workspace>/progress/vs_old_bots_history.csv, which IS committed --
gauntlet/ is git-ignored, so this file is the only durable record.
"""
import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

import progress_lib as pl

FIELDS = ["date", "current_snapshot", "opponent", "wins", "total", "win_pct", "source"]

# What produced a row, which changes how it may be read:
#   roster-run  a gauntlet run deliberately played against the roster. The bot
#               measured is the accepted lineage, so the point is a clean
#               absolute-strength reading.
#   backfill    harvested by --all from a run that happened for some other
#               reason -- usually a pre-accept head-to-head, so the bot measured
#               was a CANDIDATE that may well have been rejected. Useful for
#               bootstrapping a chart with history, but a dip in these points can
#               mean "that candidate was bad" rather than "the bot regressed".
SOURCES = ("roster-run", "backfill")

# `current_snapshot` names the build that PLAYED, and comes from the run's own
# bot.txt (written by gauntlet.sh at launch). A name ending `+cand` is a
# candidate ahead of every snapshot -- the usual case for a roster run, since
# roster runs are normally played before the accept decision. Do not read
# `carol_iter7+cand` as iteration 7; it means "something after iter7, not yet
# accepted". Runs older than bot.txt fall back to a date-based reconstruction,
# which names the previous accepted iteration and is why two of carol's rows
# had to be relabelled by hand.


def _snapshot_opponents(results_csv, agent):
    """Every <agent>_iterN opponent that actually appears in a run."""
    pat = re.compile(rf"^{re.escape(agent)}_iter\d+$")
    with open(results_csv) as f:
        return {r["opponent"] for r in csv.DictReader(f)
                if r.get("opponent") and pat.match(r["opponent"])}


def tally_run(results_csv, roster):
    """{opponent: [wins, total]} for roster opponents in one run."""
    tally = defaultdict(lambda: [0, 0])
    with open(results_csv) as f:
        for row in csv.DictReader(f):
            opp = row.get("opponent")
            if opp not in roster:
                continue
            tally[opp][1] += 1
            if row.get("bot_result") == "win":
                tally[opp][0] += 1
    return tally


def load_history(path):
    if not path.is_file():
        return []
    with open(path) as f:
        return list(csv.DictReader(f))


def write_history(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(rows, key=lambda r: (r["date"], r["opponent"]))
    for r in rows:
        r.setdefault("source", "roster-run")   # histories written before the column existed
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def bot_label(rundir):
    """What the run itself recorded about the build that played, if anything.

    gauntlet.sh writes bot.txt at launch, when which-build-is-this is still a
    fact rather than a reconstruction. Prefer it: `snapshot_as_of` can only
    guess from snapshot dates, and a roster run normally measures a CANDIDATE
    that is ahead of every snapshot, so its guess names the previous accepted
    iteration and silently changes once the candidate is snapshotted. Returns
    "" for runs launched before bot.txt existed, which keep the old behaviour.
    """
    f = rundir / "bot.txt"
    if not f.is_file():
        return ""
    fields = dict(
        line.split("=", 1) for line in f.read_text().splitlines() if "=" in line
    )
    return fields.get("label", "").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rundir", nargs="?", help="gauntlet/<run-id> (or its results.csv)")
    ap.add_argument("--all", action="store_true",
                    help="backfill from every gauntlet run in this workspace")
    ap.add_argument("--roster", action="store_true",
                    help="print the roster opponent list and exit")
    ap.add_argument("--stride", type=int, default=5,
                    help="roster spacing: iter0, then every Nth (default 5)")
    ap.add_argument("--workspace", help="agent workspace (default: detect from cwd)")
    args = ap.parse_args()

    repo_root, ws_dir, agent = pl.find_workspace(args.workspace)
    roster = pl.roster_opponents(ws_dir, agent, stride=args.stride)

    if args.roster:
        print(" ".join(roster))
        return
    if not roster:
        raise SystemExit(f"!! no roster yet for {agent}: need at least one "
                         f"{agent}_iterN snapshot older than the current one")
    if not args.rundir and not args.all:
        raise SystemExit("!! pass a gauntlet run dir, or --all to backfill")

    runs = []
    if args.all:
        runs = sorted(p for p in (ws_dir / "gauntlet").glob("*/results.csv")) \
            if (ws_dir / "gauntlet").is_dir() else []
    else:
        p = Path(args.rundir)
        if not p.is_absolute():
            p = ws_dir / p
        runs = [p if p.name == "results.csv" else p / "results.csv"]

    history = load_history(ws_dir / "progress" / "vs_old_bots_history.csv")
    added = replaced = 0
    for results_csv in runs:
        if not results_csv.is_file():
            print(f"  skip {results_csv} (no results.csv)")
            continue
        rundir = results_csv.parent
        when = pl.run_timestamp(rundir)
        if when is None:
            print(f"  skip {rundir.name} (run-id has no timestamp)")
            continue
        tally = tally_run(results_csv, set(roster))

        # A run can contain an old snapshot that the CURRENT stride does not
        # select, and silently dropping it is a trap: bootstrapping a new rung
        # means playing it deliberately, and the rung only becomes permanent
        # once it is in this CSV. So say so, with the command that records it,
        # instead of skipping without comment.
        skipped = sorted(_snapshot_opponents(results_csv, agent) - set(roster))
        if skipped:
            print(f"  !! {rundir.name} also played {', '.join(skipped)}, which the")
            print(f"  !! current --stride {args.stride} roster does not select, so they are NOT")
            print("  !! recorded. To keep them as permanent rungs, re-run this with a")
            print("  !! stride that selects them, e.g.:")
            print(f"  !!   track_vs_old_bots.py --stride 3 {rundir}")
            print("  !! Once recorded they stay in the roster at any stride.")

        if not tally:
            print(f"  skip {rundir.name} (no roster opponents in it)")
            continue
        snap = bot_label(rundir) or pl.snapshot_as_of(repo_root, ws_dir, agent, when)
        ts = when.isoformat()
        for opp, (wins, total) in sorted(tally.items()):
            row = {"date": ts, "current_snapshot": snap, "opponent": opp,
                   "wins": str(wins), "total": str(total),
                   "win_pct": f"{100 * wins / total:.1f}" if total else "0.0",
                   "source": "backfill" if args.all else "roster-run"}
            prior = [r for r in history if r["date"] == ts and r["opponent"] == opp]
            for r in prior:
                history.remove(r)
            history.append(row)
            if prior:
                replaced += 1
            else:
                added += 1
            print(f"  {rundir.name}  vs {opp:<20} {wins}/{total} "
                  f"({row['win_pct']}%)  as {snap}  [{row['source']}]")

    write_history(ws_dir / "progress" / "vs_old_bots_history.csv", history)
    print(f"roster: {' '.join(roster)}")
    print(f"wrote {ws_dir / 'progress' / 'vs_old_bots_history.csv'} "
          f"({added} new rows, {replaced} replaced, {len(history)} total)")


if __name__ == "__main__":
    main()

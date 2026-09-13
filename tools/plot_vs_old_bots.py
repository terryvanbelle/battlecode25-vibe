#!/usr/bin/env python3
"""
Plot one agent's win% against its fixed roster of old snapshots, over time.

Read it as an absolute-strength curve. Each line is a frozen opponent, so the
line rising means this bot got stronger, full stop -- unlike the gauntlet's
headline win%, which is measured against whatever the pool currently holds on
whatever maps were sampled that run. A line that flattens near 100% has stopped
resolving and its opponent is spent as an instrument; a line sagging back toward
50% is a regression against ground the bot used to hold.

Ported from battlecode26-vibe (originally battlecode22-vibe).

Usage (from your workspace):
    cd agents/alice
    ../../tools/.venv/bin/python3 ../../tools/plot_vs_old_bots.py

Output: <workspace>/progress/vs_old_bots.png
Input:  <workspace>/progress/vs_old_bots_history.csv (see track_vs_old_bots.py)
"""
import argparse
import csv
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import progress_lib as pl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", help="agent workspace (default: detect from cwd)")
    ap.add_argument("-o", "--output")
    args = ap.parse_args()

    repo_root, ws_dir, agent = pl.find_workspace(args.workspace)
    history_csv = ws_dir / "progress" / "vs_old_bots_history.csv"
    if not history_csv.is_file():
        print(f"{history_csv} doesn't exist yet -- run track_vs_old_bots.py first")
        return
    with open(history_csv) as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print(f"{history_csv} has no data rows yet")
        return

    matplotlib = pl.use_matplotlib()
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    by_opp = defaultdict(list)
    for r in rows:
        by_opp[r["opponent"]].append(
            (datetime.fromisoformat(r["date"]), float(r["win_pct"]),
             int(r["wins"]), int(r["total"]), r.get("source", "roster-run")))
    for k in by_opp:
        by_opp[k].sort(key=lambda t: t[0])

    def sort_key(name):
        m = re.search(r"_iter(\d+)$", name)
        return (0, int(m.group(1))) if m else (1, 0)  # snapshots first, then extras

    order = sorted(by_opp, key=sort_key)
    fig, ax = plt.subplots(figsize=(13, 7))
    cmap = plt.get_cmap("viridis_r")
    colors = [cmap(i / max(1, len(order) - 1)) for i in range(len(order))]

    any_backfill = False
    for color, opp in zip(colors, order):
        pts = by_opp[opp]
        n_games = pts[-1][3]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], linestyle="-",
                linewidth=1.6, color=color, label=f"vs {opp}  (n={n_games})")
        # Solid marker = a run played deliberately against the roster, so the bot
        # measured was the accepted lineage. Hollow marker = backfilled from a
        # run held for another reason, usually a pre-accept head-to-head, where
        # the bot measured was a candidate that may have been REJECTED. A dip in
        # a hollow point says that candidate was bad, not that the bot regressed.
        solid = [p for p in pts if p[4] != "backfill"]
        hollow = [p for p in pts if p[4] == "backfill"]
        any_backfill = any_backfill or bool(hollow)
        if solid:
            ax.scatter([p[0] for p in solid], [p[1] for p in solid], s=42,
                       color=color, zorder=3)
        if hollow:
            ax.scatter([p[0] for p in hollow], [p[1] for p in hollow], s=42,
                       facecolors="white", edgecolors=color, linewidths=1.5, zorder=3)
        # A single measurement is a dot with no trend; say so rather than
        # letting a lone point read as a flat line.
        if len(pts) == 1:
            ax.annotate("single measurement", pts[0][:2], textcoords="offset points",
                        xytext=(6, 6), fontsize=7, color=color)

    # ---- the roster average -------------------------------------------------
    # One number per run for "how is the bot doing overall", which the per-opponent
    # lines cannot show: they cross, and which one is on top changes with the
    # opponent rather than with the bot. Only dates where EVERY tracked opponent
    # was measured are averaged -- a date missing an opponent would move this line
    # by changing the composition rather than the strength, which is exactly the
    # artifact the whole chart exists to avoid.
    by_date = defaultdict(list)
    for opp, pts in by_opp.items():
        for dt, pct, wins, total, source in pts:
            by_date[dt].append((opp, pct, wins, total, source))
    full = {dt: v for dt, v in by_date.items() if len(v) == len(order)}
    skipped = len(by_date) - len(full)
    if len(full) >= 2:
        avg_dates = sorted(full)
        # Games-weighted, so the line stays correct if a run ever measures
        # different numbers of games per opponent. With equal totals -- the
        # normal case -- this is identical to the mean of the three win rates.
        avg_pcts = [100.0 * sum(x[2] for x in full[dt]) / max(1, sum(x[3] for x in full[dt]))
                    for dt in avg_dates]
        ax.plot(avg_dates, avg_pcts, linestyle="--", linewidth=2.8, color="black",
                alpha=0.85, zorder=4,
                label=f"AVERAGE of all {len(order)}  (n={sum(x[3] for x in full[avg_dates[-1]])})")
        solid_avg = [(d, p) for d, p in zip(avg_dates, avg_pcts)
                     if all(x[4] != "backfill" for x in full[d])]
        hollow_avg = [(d, p) for d, p in zip(avg_dates, avg_pcts)
                      if any(x[4] == "backfill" for x in full[d])]
        if solid_avg:
            ax.scatter([d for d, _ in solid_avg], [p for _, p in solid_avg],
                       s=30, color="black", zorder=5)
        if hollow_avg:
            ax.scatter([d for d, _ in hollow_avg], [p for _, p in hollow_avg],
                       s=30, facecolors="white", edgecolors="black",
                       linewidths=1.4, zorder=5)
        if skipped:
            print(f"  average line: {len(full)} complete runs plotted, "
                  f"{skipped} skipped for missing an opponent")

    ax.axhline(50, color="gray", linestyle=":", linewidth=1, alpha=0.7)
    ax.annotate("even", (0.002, 50), xycoords=("axes fraction", "data"),
                fontsize=7.5, color="gray", va="bottom")
    ax.set_title(
        f"Win % vs. a fixed roster of old snapshots — {agent} (Battlecode 2025)\n"
        "absolute-strength yardstick: frozen opponents, so a rising line is real progress\n"
        "dashed black = average across the whole roster",
        fontsize=12)
    ax.set_xlabel(f"Date of gauntlet run ({pl.pacific_label()})")
    ax.set_ylabel("Win % against that frozen opponent")
    ax.set_ylim(-5, 105)
    ax.grid(True, alpha=0.3)
    # Ticks are placed AND labelled in Pacific, so a label reads as the
    # wall-clock time the run happened at rather than a UTC instant.
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(tz=pl.PACIFIC))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M", tz=pl.PACIFIC))
    fig.autofmt_xdate(rotation=30)
    handles, labels = ax.get_legend_handles_labels()
    if any_backfill:
        from matplotlib.lines import Line2D
        handles += [
            Line2D([], [], marker="o", color="gray", linestyle="none",
                   markersize=7, label="run played against the roster"),
            Line2D([], [], marker="o", color="gray", linestyle="none",
                   markerfacecolor="white", markersize=7,
                   label="backfilled: candidate under test,\nmay have been rejected"),
        ]
    ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1.01, 0.5),
              fontsize=8)
    fig.tight_layout()

    out_path = Path(args.output) if args.output else ws_dir / "progress" / "vs_old_bots.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    print(f"wrote {out_path} ({len(rows)} rows, {len(by_opp)} tracked opponents)")


if __name__ == "__main__":
    main()

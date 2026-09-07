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

    ax.axhline(50, color="gray", linestyle=":", linewidth=1, alpha=0.7)
    ax.annotate("even", (0.002, 50), xycoords=("axes fraction", "data"),
                fontsize=7.5, color="gray", va="bottom")
    ax.set_title(
        f"Win % vs. a fixed roster of old snapshots — {agent} (Battlecode 2025)\n"
        "absolute-strength yardstick: frozen opponents, so a rising line is real progress",
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

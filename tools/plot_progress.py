#!/usr/bin/env python3
"""
Plot one agent's cumulative accepted iterations over time.

Every accepted iteration is frozen as src/<agent>_iterN/, so counting those
directories by the date they first appeared is a reliable proxy for accepted
iterations -- no parsing of ACCEPTED/REJECTED prose out of TRAINING_LOG.md,
which drifts. Ported from battlecode26-vibe (originally battlecode22-vibe);
see MULTI_AGENT.md for why each agent charts only its own workspace.

The slope is the thing to read, not the height: a flat stretch means the loop
is spending its time on rejected candidates, which is information about the
loop rather than about the bot.

Usage (from your workspace):
    cd agents/alice
    ../../tools/.venv/bin/python3 ../../tools/plot_progress.py

Output: <workspace>/progress/cumulative_iterations.png

Milestones: put process/policy changes -- changes to HOW evaluation is done,
not individual accepts -- in <workspace>/progress/milestones.txt, one per line
as `<commit>|<label>`. Add the line in the same commit as the change itself;
deferring it is how the BC22 and BC26 charts ended up with unlabelled slope
changes nobody could explain later.
"""
import argparse
from pathlib import Path

import progress_lib as pl


def load_milestones(ws_dir):
    f = ws_dir / "progress" / "milestones.txt"
    if not f.is_file():
        return []
    out = []
    for line in f.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "|" not in line:
            continue
        commit, label = line.split("|", 1)
        out.append((commit.strip(), label.strip()))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", help="agent workspace (default: detect from cwd)")
    ap.add_argument("-o", "--output")
    args = ap.parse_args()

    repo_root, ws_dir, agent = pl.find_workspace(args.workspace)
    rows = pl.snapshot_dates(repo_root, ws_dir, agent)
    if not rows:
        print(f"no {agent}_iterN snapshots under {ws_dir}/src -- nothing to plot yet")
        return

    matplotlib = pl.use_matplotlib()
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    dates = [r[2] for r in rows]
    cum = list(range(1, len(rows) + 1))

    fig, ax = plt.subplots(figsize=(13, 7))
    ax.step(dates, cum, where="post", color="#2563eb", linewidth=2)
    ax.scatter(dates, cum, color="#2563eb", s=22, zorder=3)

    # An accepted-but-uncommitted snapshot is dated by mtime, not by git; ring it
    # so nobody reads a provisional point as a committed one.
    prov = [(d, c) for (n, name, d, committed), c in zip(rows, cum) if not committed]
    if prov:
        ax.scatter([p[0] for p in prov], [p[1] for p in prov], s=110,
                   facecolors="none", edgecolors="#dc2626", linewidths=1.4,
                   zorder=4, label="not yet committed (dated by mtime)")
        ax.legend(loc="upper left", fontsize=8)

    ax.set_title(f"Cumulative Accepted Iterations Over Time — {agent} "
                 f"(Battlecode 2025)", fontsize=13)
    ax.set_xlabel("Date (UTC)")
    ax.set_ylabel(f"Cumulative accepted iterations ({rows[0][1]}..{rows[-1][1]})")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, len(rows) + 1)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    fig.autofmt_xdate(rotation=30)

    for (n, name, d, _committed), c in zip(rows, cum):
        ax.annotate(name.replace(f"{agent}_", ""), (d, c), textcoords="offset points",
                    xytext=(5, -13), fontsize=8, color="gray")

    colors = ["#dc2626", "#16a34a", "#9333ea", "#ea580c", "#0891b2"]
    for i, (commit, label) in enumerate(load_milestones(ws_dir)):
        d = pl.commit_date(repo_root, commit)
        if d is None:
            print(f"  (milestone commit {commit} not found; skipped)")
            continue
        color = colors[i % len(colors)]
        ax.axvline(d, color=color, linestyle="--", linewidth=1.2, alpha=0.8, zorder=1)
        ax.annotate(label, (d, 0), xycoords=("data", "axes fraction"),
                    textcoords="offset points", xytext=(4, 8 + 30 * (i % 4)),
                    rotation=90, va="bottom", ha="left", fontsize=7.5, color=color)

    fig.tight_layout()
    out_path = Path(args.output) if args.output else ws_dir / "progress" / "cumulative_iterations.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    print(f"wrote {out_path} ({len(rows)} accepted iterations, "
          f"{rows[0][1]}..{rows[-1][1]})")


if __name__ == "__main__":
    main()

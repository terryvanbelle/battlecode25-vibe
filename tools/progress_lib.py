#!/usr/bin/env python3
"""
Shared helpers for the per-agent progress charts (tools/plot_progress.py,
tools/track_vs_old_bots.py, tools/plot_vs_old_bots.py).

Ported from battlecode26-vibe's tools/plot_progress.py + track/plot_vs_old_bots.py,
which were themselves ported from battlecode22-vibe. Two things changed in the
port, both forced by this project's shape:

1. **Multi-agent.** BC26 had one bot at src/g_iterN; here each of alice, bob and
   carol has its own workspace, so every tool auto-detects the workspace it is
   run from and reads only that agent's data. Nothing here ever reads a sibling
   agent's directory -- see MULTI_AGENT.md's isolation rules.
2. **UTC, not Pacific.** Everything else in this project (the 06:00/18:00
   tournament cron, gauntlet run-ids) is UTC, and both VMs run UTC.
"""
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

UTC = timezone.utc


def find_workspace(start=None):
    """(repo_root, ws_dir, agent) for the agent workspace containing `start`.

    An agent workspace is a directory under agents/ holding a build.gradle.
    Run the tools from inside one (cd agents/alice && ../../tools/...).
    """
    repo_root = Path(__file__).resolve().parent.parent
    d = Path(start).resolve() if start else Path.cwd().resolve()
    while True:
        if (d / "build.gradle").is_file() and d.parent.name == "agents":
            return repo_root, d, d.name
        if d == d.parent or d == repo_root:
            break
        d = d.parent
    raise SystemExit(
        "!! run this from inside an agent workspace (e.g. cd agents/alice), "
        "or pass --workspace agents/<name>"
    )


def snapshot_numbers(ws_dir, agent):
    """Accepted-iteration snapshot numbers present in this workspace's src/.

    Each accepted iteration is frozen as src/<agent>_iterN/, so counting these
    is a reliable proxy for 'cumulative accepted iterations' without parsing
    ACCEPTED/REJECTED prose out of TRAINING_LOG.md.
    """
    src = ws_dir / "src"
    if not src.is_dir():
        return []
    pat = re.compile(rf"{re.escape(agent)}_iter(\d+)$")
    nums = [int(m.group(1)) for p in src.iterdir() if p.is_dir()
            for m in [pat.match(p.name)] if m]
    return sorted(nums)


def snapshot_name(agent, n):
    return f"{agent}_iter{n}"


def first_commit_date(repo_root, rel_path):
    """When `rel_path` first appeared in git, as UTC. None if never committed."""
    out = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%aI", "--", str(rel_path)],
        cwd=repo_root, capture_output=True, text=True,
    ).stdout.strip()
    if not out:
        return None
    return datetime.fromisoformat(out.splitlines()[-1]).astimezone(UTC)


def commit_date(repo_root, commit):
    out = subprocess.run(
        ["git", "log", "-1", "--format=%aI", commit],
        cwd=repo_root, capture_output=True, text=True,
    ).stdout.strip()
    return datetime.fromisoformat(out).astimezone(UTC) if out else None


def snapshot_dates(repo_root, ws_dir, agent):
    """[(n, name, date, committed)] for every snapshot, oldest first.

    A snapshot that exists on disk but is not committed yet still counts as an
    accepted iteration -- it is dated by directory mtime and flagged, so a chart
    drawn mid-session shows the accept that just happened instead of silently
    dropping it.
    """
    rows = []
    for n in snapshot_numbers(ws_dir, agent):
        name = snapshot_name(agent, n)
        rel = ws_dir.relative_to(repo_root) / "src" / name
        d = first_commit_date(repo_root, rel)
        committed = d is not None
        if d is None:
            d = datetime.fromtimestamp((ws_dir / "src" / name).stat().st_mtime, UTC)
        rows.append((n, name, d, committed))
    rows.sort(key=lambda r: (r[2], r[0]))
    return rows


def roster_numbers(newest, stride=5):
    """Fixed reference points: iteration 0, then every `stride`-th from 1.

    Derived, never hardcoded. BC26's port hardcoded its roster as a usage
    example, then wasn't revisited when a second reference snapshot existed, so
    the chart tracked a single opponent long after it should have had three.
    Deriving it means the roster grows on its own as the project does.

    iter0 is always included: it is the origin, and win% against it is the
    closest thing this project has to an absolute-strength yardstick. Never
    remove an entry -- the value of each line is its long-run trend.
    """
    if newest is None or newest < 0:
        return []
    nums = {0} | set(range(1, newest + 1, stride))
    return sorted(n for n in nums if n <= newest)


def roster_opponents(ws_dir, agent, stride=5, exclude_current=True):
    """Roster opponent names: the snapshot roster, plus any fixed extras.

    progress/roster_extra.txt (one name per line, '#' comments) lets an agent
    add a non-snapshot fixed yardstick -- a synthetic archetype or a pinned
    benchmark. Those are valid reference points for exactly the same reason old
    snapshots are: they never change, so a rising line against them is absolute
    progress rather than a moving-target artifact.
    """
    present = set(snapshot_numbers(ws_dir, agent))
    newest = max(present) if present else None
    names = [snapshot_name(agent, n) for n in roster_numbers(newest, stride)
             if n in present]
    if exclude_current and newest is not None:
        cur = snapshot_name(agent, newest)
        names = [n for n in names if n != cur]

    extra_file = ws_dir / "progress" / "roster_extra.txt"
    if extra_file.is_file():
        for line in extra_file.read_text().splitlines():
            line = line.split("#", 1)[0].strip()
            if line and line not in names:
                names.append(line)
    return names


def run_timestamp(rundir):
    """UTC datetime encoded in a gauntlet run-id like 20260906-185051."""
    m = re.search(r"(\d{8})-(\d{6})", Path(rundir).name)
    if not m:
        return None
    return datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S").replace(tzinfo=UTC)


def snapshot_as_of(repo_root, ws_dir, agent, when):
    """Newest snapshot that already existed at time `when` (for backfill).

    Labelling every backfilled row with today's newest snapshot would be wrong;
    this reconstructs what the bot was at the time of the run.
    """
    rows = [r for r in snapshot_dates(repo_root, ws_dir, agent) if r[2] <= when]
    if rows:
        return max(rows, key=lambda r: r[0])[1]
    nums = snapshot_numbers(ws_dir, agent)
    return snapshot_name(agent, max(nums)) if nums else "unknown"


def use_matplotlib():
    try:
        import matplotlib
    except ModuleNotFoundError:
        raise SystemExit(
            "!! matplotlib missing -- run these with the shared venv:\n"
            "   ../../tools/.venv/bin/python3 ../../tools/<script>.py"
        )
    matplotlib.use("Agg")
    return matplotlib

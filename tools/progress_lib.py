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
2. **Stored in UTC, displayed in Pacific.** Run-ids, both VM clocks and every
   timestamp on disk are UTC, and stay that way -- converting stored data would
   make run-ids disagree with the rows they name. Only the CHART AXES are
   converted, via `PACIFIC` below, because the person reading a chart wants the
   wall-clock time they were working at. The tournament schedule is likewise
   Pacific (06:00/18:00 America/Los_Angeles).
"""
import csv
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    PACIFIC = ZoneInfo("America/Los_Angeles")
except Exception:                      # no tzdata: fall back to fixed PDT
    PACIFIC = timezone(timedelta(hours=-7), "PDT")

UTC = timezone.utc


def pacific_label(dt=None):
    """Axis label suffix naming the zone as it stands at `dt` -- PDT or PST."""
    when = dt or datetime.now(UTC)
    name = when.astimezone(PACIFIC).tzname() or "Pacific"
    return name


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


def commit_touches(repo_root, commit, rel_path):
    """True if `commit` actually changed anything under `rel_path`.

    `commit_date` resolves a hash REPO-WIDE, which is the right behaviour for a
    hash you trust and the wrong one for a hash a human typed. A milestone hash
    that is wrong but happens to exist -- a sibling lineage's commit, a
    coordinator commit, a transposed character that still parses -- resolves to a
    real date and plots a confident vertical line at the wrong moment. Nothing
    looks broken, which is what makes it worth a check.

    Scoping the lookup to the workspace turns a silent wrong answer into a loud
    one, which is the only trade that matters here.
    """
    out = subprocess.run(
        ["git", "show", "--name-only", "--format=", commit, "--", str(rel_path)],
        cwd=repo_root, capture_output=True, text=True,
    )
    return out.returncode == 0 and bool(out.stdout.strip())


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


def roster_numbers(present):
    """Fixed reference points: the origin, then the build that was current at
    each iteration whose number ends in 1 or 6 (1, 6, 11, 16, 21, ...).

    Set by the user 2026-09-09, replacing "every 5th accepted snapshot by
    position". Derived either way, never hardcoded: BC26's port hardcoded its
    roster as a usage example and then wasn't revisited when a second reference
    snapshot existed, so the chart tracked one opponent long after it should
    have had three.

    A milestone iteration is usually REJECTED, and a rejected iteration never
    becomes a snapshot -- alice has 18 accepted snapshots and exactly one whose
    number ends in 1 or 6. So a milestone resolves to the last accepted snapshot
    at or before it: the bot as it stood at that iteration, which is the thing
    the chart is asking about. Milestones can collide (alice's 31 and 36 both
    resolve to iter30); the set absorbs that.

    This is why the roster is not simply {n : n % 5 == 1}. That reading gives
    alice a single rung and carol four from lineages of the same length, so an
    agent that rejects more candidates would get a permanently worse
    absolute-strength chart -- exactly backwards.

    The first snapshot is always included: it is the origin, and win% against it
    is the closest thing this project has to an absolute-strength yardstick.
    """
    nums = sorted(present)
    if not nums:
        return []
    keep = {nums[0]}
    for m in range(1, nums[-1] + 1, 5):        # 1, 6, 11, 16, ...
        at_or_before = [n for n in nums if n <= m]
        if at_or_before:
            keep.add(max(at_or_before))
    return sorted(keep)


# BC25 finals benchmark bots. These are a yardstick measured by the coordinator,
# never an opponent a lineage may train against, so the roster refuses them even
# if a workspace lists one in roster_extra.txt. The rule is in every AGENT.md;
# this is the guard that does not depend on anyone having read it.
BENCHMARK_BOTS = {"spaark", "tspaarkhs", "quals_current_submission", "v3",
                  "quals", "frontreset", "micro", "jottesen_test", "v1", "v2"}


def is_benchmark(name):
    return name.strip().lower() in BENCHMARK_BOTS


def _history_opponents(ws_dir):
    """Opponent names already recorded in this workspace's roster history."""
    f = ws_dir / "progress" / "vs_old_bots_history.csv"
    if not f.is_file():
        return set()
    try:
        with f.open() as fh:
            return {r["opponent"] for r in csv.DictReader(fh) if r.get("opponent")}
    except (OSError, csv.Error):
        return set()


def roster_opponents(ws_dir, agent, exclude_current=True, extra_numbers=()):
    """Roster opponent names: the snapshot roster, plus any fixed extras.

    progress/roster_extra.txt (one name per line, '#' comments) lets an agent
    add a non-snapshot fixed yardstick -- a synthetic archetype or a pinned
    benchmark. Those are valid reference points for exactly the same reason old
    snapshots are: they never change, so a rising line against them is absolute
    progress rather than a moving-target artifact.
    """
    present = set(snapshot_numbers(ws_dir, agent))
    newest = max(present) if present else None
    keep = set(roster_numbers(present)) | {n for n in extra_numbers if n in present}
    # Never drop a rung that already has history. "Never remove an entry -- the
    # value of each line is its long-run trend" is a promise about the chart, so
    # a snapshot that has ever been measured stays measured even if the current
    # rule would not pick it. This is what makes changing the rule safe: the
    # 2026-09-09 switch from positions to numbers selects fewer snapshots for
    # some lineages, and not one existing line was dropped by it.
    keep |= {n for n in present
             if snapshot_name(agent, n) in _history_opponents(ws_dir)}
    names = [snapshot_name(agent, n) for n in sorted(keep)]
    if exclude_current and newest is not None:
        cur = snapshot_name(agent, newest)
        names = [n for n in names if n != cur]

    extra_file = ws_dir / "progress" / "roster_extra.txt"
    if extra_file.is_file():
        for line in extra_file.read_text().splitlines():
            line = line.split("#", 1)[0].strip()
            if is_benchmark(line):
                print(f"!! refusing benchmark bot {line!r} as a roster opponent -- "
                      f"finals bots are a yardstick, never something to train against")
                continue
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

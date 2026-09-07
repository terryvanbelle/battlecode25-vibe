#!/usr/bin/env python3
"""Identify which build a workspace's bot currently IS, at the moment it plays.

`src/<agent>` is a moving target: it is whatever the agent is working on, which
is normally a candidate ahead of every committed snapshot. Reconstructing that
later from snapshot dates cannot work -- the answer changes retroactively the
moment the candidate is accepted and snapshotted, so the same run gets a
different label depending on when the tool is run. That mislabelled two of
carol's roster rows and had to be corrected by hand both times.

So record it at the only moment the information exists: run launch. A run's bot
is identified by CONTENT, by comparing src/<agent> against every
src/<agent>_iterN, normalising the package declaration -- which is exactly the
"identical apart from the package line" check the agents already do by hand when
they snapshot.

    tools/bot_identity.py [--workspace DIR]

prints KEY=VALUE lines (shell-sourceable, stdlib only, no venv needed):

    bot=carol             the package that plays
    snapshot=carol_iter7  the snapshot this build IS, empty if it matches none
    base=carol_iter5      newest snapshot that exists (context for a candidate)
    label=carol_iter7     what to call this build: `base+cand` when snapshot is
                          empty, so a candidate is never labelled as an accepted
                          iteration
    head=3f89699          repo HEAD when the run launched
    dirty=1               src/<agent> had uncommitted edits at launch
"""
import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

PACKAGE = re.compile(rb"^\s*package\s+[A-Za-z0-9_.]+\s*;", re.M)


def find_workspace(start=None):
    d = Path(start or Path.cwd()).resolve()
    for cand in [d, *d.parents]:
        if (cand / "build.gradle").is_file():
            return cand
    sys.exit("!! run this from inside a workspace (agents/<name> or arena)")


def digest(src_dir):
    """Content hash of a bot package, blind to its package declaration."""
    h = hashlib.sha256()
    files = sorted(src_dir.rglob("*.java"), key=lambda p: p.relative_to(src_dir).as_posix())
    if not files:
        return None
    for f in files:
        h.update(f.relative_to(src_dir).as_posix().encode())
        h.update(b"\0")
        h.update(PACKAGE.sub(b"", f.read_bytes()))
        h.update(b"\0")
    return h.hexdigest()


def git(repo, *args):
    try:
        out = subprocess.run(["git", "-C", str(repo), *args],
                             capture_output=True, text=True, timeout=30)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace")
    ap.add_argument("--bot", help="package that actually plays (default: the "
                                  "workspace's own bot). A run launched with "
                                  "BOT=<something else> plays that package, and "
                                  "labelling it with src/<agent> would name a "
                                  "build that never took the field.")
    args = ap.parse_args()

    ws = find_workspace(args.workspace)
    agent = ws.name
    src = ws / "src"
    bot = args.bot or agent
    mine = src / bot
    if not mine.is_dir():
        sys.exit(f"!! no {mine}")

    want = digest(mine)
    snaps = {}
    for d in src.iterdir():
        m = re.fullmatch(rf"{re.escape(agent)}_iter(\d+)", d.name) if d.is_dir() else None
        if m:
            snaps[int(m.group(1))] = d.name

    match = ""
    if bot in snaps.values():      # playing a snapshot directly: it is itself
        match = bot
    for n in sorted(snaps, reverse=True):          # newest match wins
        if match:
            break
        if want is not None and digest(src / snaps[n]) == want:
            match = snaps[n]
            break
    base = snaps[max(snaps)] if snaps else ""
    # An explicitly named non-snapshot package (BOT=carol_i12b) IS its own
    # identity -- the package name says exactly which build played, which is
    # more informative than "something after iter11". Only the workspace's own
    # moving src/<agent> needs the +cand form.
    if match:
        label = match
    elif bot != agent:
        label = bot
    elif base:
        label = f"{base}+cand"
    else:
        label = "pre-iter0"

    repo = Path(git(ws, "rev-parse", "--show-toplevel") or ws)
    rel = mine.relative_to(repo) if repo in mine.parents else mine
    dirty = "1" if git(repo, "status", "--porcelain", "--", str(rel)) else "0"

    for k, v in (("bot", bot), ("snapshot", match), ("base", base),
                 ("label", label), ("head", git(repo, "rev-parse", "--short", "HEAD")),
                 ("dirty", dirty)):
        print(f"{k}={v}")


if __name__ == "__main__":
    main()

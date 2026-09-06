#!/usr/bin/env python3
"""Measure carol's frozen-treasury degeneracy in one or more .bc25 replays.

The bug (see TRAINING_LOG, iteration 7): CHIP_RESERVE=1200 blocks every build below
1200+250, so once team income stops the treasury can freeze between the reserve and the
build gate and unit production ends permanently. Measured as the longest run of consecutive
rounds in which the team's chip total is EXACTLY unchanged while it still has towers.

Usage:
    tools/frozen-treasury.py <replay.bc25> [...]        # one line per replay
    tools/frozen-treasury.py --gate 50 <replay.bc25>... # exit 1 if any run >= 50

Team separation: replays where both teams run a carol build emit identical indicator
formats, so the two teams are split by following each round's two `chips=` values by
continuity. Builds carrying different BUILD tags (`[i7] ...`) are split by tag instead,
which is exact -- prefer that where available.
"""
import argparse, collections, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
STRINGS = os.path.join(HERE, "replay-strings.py")
ROW = re.compile(r'(?:\[(\w+)\] )?.*T r=(\d+) chips=(\d+) tw=(\d+)')


def rows(path):
    out = subprocess.run([sys.executable, STRINGS, path], capture_output=True, text=True).stdout
    for line in out.splitlines():
        m = ROW.search(line)
        if m:
            yield m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))


def split_teams(path):
    """Return {label: [(round, chips, towers)]}.

    Split by BUILD tag, which is exact: from iteration 7 on, carol stamps `[iN]` into every
    indicator, while frozen snapshots carry their own tag or none, so tagged-vs-untagged
    separates the two teams cleanly.

    Within one team, several towers report in the same round and their `chips=` readings
    differ whenever one of them builds mid-round -- so per (team, round) we collapse to the
    minimum. Not doing this was a real bug: the tool read one team's two towers as two teams
    and reported 0 frozen rounds for the three games the degeneracy was first measured in.
    """
    groups = collections.defaultdict(lambda: collections.defaultdict(list))
    for tag, r, c, tw in rows(path):
        groups[tag][r].append((c, tw))
    out = {}
    for tag, byr in groups.items():
        label = tag or "untagged"
        out[label] = [(r, min(v)[0], max(v)[1]) for r, v in sorted(byr.items())]
    return out


def longest_frozen(series):
    best = run = 0
    last = None
    at = None
    for r, c, tw in series:
        if last is not None and c == last and tw > 0:
            run += 1
            if run > best:
                best, at = run, (r, c, tw)
        else:
            run = 0
        last = c
    return best, at


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", type=int, default=None,
                    help="exit 1 if any team's frozen run reaches this many rounds")
    ap.add_argument("replays", nargs="+")
    a = ap.parse_args()
    worst = 0
    for p in a.replays:
        parts = []
        for label, series in split_teams(p).items():
            n, at = longest_frozen(series)
            worst = max(worst, n)
            parts.append(f"{label}={n}" + (f"@r{at[0]}/{at[1]}chips/{at[2]}tw" if n >= 20 else ""))
        print(f"{os.path.basename(p)[:48]:50s} " + "  ".join(parts))
    if a.gate is not None:
        print(f"\nworst frozen run = {worst}; gate = {a.gate} -> "
              + ("FAIL" if worst >= a.gate else "PASS"))
        return 1 if worst >= a.gate else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())

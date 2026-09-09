#!/usr/bin/env python3
"""Parse tournament-census.sh output into per-game rows and cut summaries.

    tools/census-parse.py <label> <census.tsv> [...]

Each input row is:  map <TAB> aliceSide <TAB> OK|SHORT <TAB> footer <TAB> summary

`aliceSide` is T1 or T2 as resolved from the replay's GameHeader, so ALICE's
columns are picked by team identity and never by filename order.

A SHORT game is one that ENDED before the census round. It is counted in the
win rate (it is a real result) but excluded from the round-300 means, and the
excluded count is always reported -- silently dropping the fast games would bias
the very quantity this census is about.
"""
import re
import sys

FIELDS = ("cov", "sold", "spl", "mop", "tw", "twPaint", "died", "xfer", "starved")


def parse_team(chunk):
    """Pull the per-team fields out of one '| T1 $x covNm ... |' segment."""
    out = {}
    m = re.search(r"\$(-?\d+)", chunk)
    out["money"] = int(m.group(1)) if m else None
    for f in FIELDS:
        m = re.search(r"\b" + f + r"(-?\d+)", chunk)
        out[f] = int(m.group(1)) if m else None
    m = re.search(r"acts\[p(\d+) u(\d+) a(\d+) s(\d+) m(\d+)\]", chunk)
    if m:
        for i, k in enumerate(("p", "u", "a", "s", "m")):
            out["act_" + k] = int(m.group(i + 1))
    return out


def parse_rows(path):
    rows = []
    for line in open(path):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 5:
            continue
        mp, side, status, footer, summary = parts[0], parts[1], parts[2], parts[3], parts[4]
        fm = re.search(r"winner=team(\d)\s+winType=(\S+)\s+rounds=(\d+)", footer)
        if not fm:
            continue
        winner_team, wintype, rounds = "T" + fm.group(1), fm.group(2), int(fm.group(3))
        seg = summary.split("|")
        if len(seg) < 3:
            continue
        t1, t2 = parse_team(seg[1]), parse_team(seg[2])
        a, c = (t1, t2) if side == "T1" else (t2, t1)
        rows.append(dict(map=mp, side=side, status=status, rounds=rounds,
                         wintype=wintype, alice_won=(winner_team == side), a=a, c=c))
    return rows


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else float("nan")


def sd(xs):
    xs = [x for x in xs if x is not None]
    if len(xs) < 2:
        return float("nan")
    m = sum(xs) / len(xs)
    return (sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5


def report(label, rows, opp="opponent"):
    n = len(rows)
    wins = sum(1 for r in rows if r["alice_won"])
    ok = [r for r in rows if r["status"] == "OK"]
    short = [r for r in rows if r["status"] == "SHORT"]
    short_alice = sum(1 for r in short if r["alice_won"])
    print(f"\n===== {label}  n={n} games =====")
    print(f"alice wins           : {wins}/{n} = {100*wins/n:.1f}%")
    print(f"ended BEFORE r300    : {len(short)}/{n} = {100*len(short)/n:.1f}%"
          f"   (alice won {short_alice} of those)")
    print(f"median game length   : {sorted(r['rounds'] for r in rows)[n//2]}")
    wt = {}
    for r in rows:
        wt[r["wintype"]] = wt.get(r["wintype"], 0) + 1
    print(f"win types            : {wt}")
    if not ok:
        print("no games reached r300 -- no r300 means")
        return
    print(f"\n-- at round 300, over the {len(ok)} games that reached it --")
    print(f"{'quantity':<22}{'alice':>9}{opp:>9}{'diff':>9}{'sd(diff)':>10}")
    for f in ("tw", "cov", "sold", "spl", "mop", "money", "twPaint",
              "died", "starved", "xfer", "act_p", "act_u", "act_a", "act_s"):
        av = [r["a"].get(f) for r in ok]
        cv = [r["c"].get(f) for r in ok]
        dv = [x - y for x, y in zip(av, cv) if x is not None and y is not None]
        print(f"{f:<22}{mean(av):>9.1f}{mean(cv):>9.1f}{mean(dv):>+9.2f}{sd(dv):>10.2f}")
    tw_ahead = [r for r in ok if r["a"]["tw"] > r["c"]["tw"]]
    tw_behind = [r for r in ok if r["a"]["tw"] < r["c"]["tw"]]
    tw_level = [r for r in ok if r["a"]["tw"] == r["c"]["tw"]]
    print("\n-- does the r300 tower lead predict the win, cross-lineage? --")
    for nm, g in (("alice ahead", tw_ahead), ("level", tw_level), ("alice behind", tw_behind)):
        if g:
            w = sum(1 for r in g if r["alice_won"])
            print(f"  {nm:<14} {len(g):>3} games   alice won {w:>3} ({100*w/len(g):.0f}%)")
    cov_ahead = [r for r in ok if r["a"]["cov"] > r["c"]["cov"]]
    cov_behind = [r for r in ok if r["a"]["cov"] < r["c"]["cov"]]
    print("\n-- and does the r300 COVERAGE lead predict it? --")
    for nm, g in (("alice ahead", cov_ahead), ("alice behind", cov_behind)):
        if g:
            w = sum(1 for r in g if r["alice_won"])
            print(f"  {nm:<14} {len(g):>3} games   alice won {w:>3} ({100*w/len(g):.0f}%)")


if __name__ == "__main__":
    args = sys.argv[1:]
    for i in range(0, len(args), 2):
        lab = args[i]
        # opponent name is taken from the label, never hardcoded: printing
        # 'carol' over bob's column would mislabel a control as the treatment.
        opp = "bob" if "BOB" in lab.upper() else ("carol" if "CAROL" in lab.upper() else "opp")
        report(lab, parse_rows(args[i + 1]), opp)

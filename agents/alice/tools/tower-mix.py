#!/usr/bin/env python3
"""Reconstruct ALICE's paint/money tower mix at a round, from census EV rows.

    tools/tower-mix.py <round> <label> <mix.tsv> [<label> <mix.tsv> ...]

Input is `tournament-census.sh ... 'TOWER'` output, which carries per-game
summary rows AND the raw tower event lines:

    initial id4(T2,MONEY_TOWER) at (9,17)
    round 38 id13054(T1,SOLDIER) SPAWN id11718(T1,MONEY_TOWER) at (2,7)
    round 91 DIED id11718(T1,MONEY_TOWER)

Tower SPAWNs and round-level DIEDs are printed unconditionally by ReplayDump, so
a game's tower population is exactly reconstructible without an action window.

THE CONTROL: the reconstructed total is checked against `tw` on the same game's
round-R summary line, which comes from the engine's own alive-count. A
reconstruction that disagrees is REPORTED, never averaged -- if the two ever
diverge the event stream is missing a death path and every mix number would be
silently wrong in the same direction.
"""
import re
import sys
from collections import defaultdict

SPAWN = re.compile(r"^round (\d+) id\d+\([^)]*\) SPAWN id(\d+)\(T(\d),(\w+)\)")
INIT = re.compile(r"^initial id(\d+)\(T(\d),(\w+)\)")
DIED = re.compile(r"^round (\d+) DIED id(\d+)\(T(\d),(\w+)\)")
SUMM = re.compile(r"\btw(\d+)\b")
FOOT = re.compile(r"winner=team(\d)\s+winType=\S+\s+rounds=(\d+)")
TOWERS = ("PAINT_TOWER", "MONEY_TOWER", "DEFENSE_TOWER")


def load(path, upto):
    games = defaultdict(lambda: {"ev": [], "tw": None, "won": None, "rounds": None})
    for line in open(path):
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 4:
            continue
        key = (parts[0], parts[1])
        g = games[key]
        if parts[2] == "EV":
            g["ev"].append(parts[3])
        else:
            fm = FOOT.search(parts[3])
            if fm:
                g["won"] = ("T" + fm.group(1)) == parts[1]
                g["rounds"] = int(fm.group(2))
            if parts[2] == "OK":
                m = SUMM.search(parts[4].split("|")[1 if parts[1] == "T1" else 2])
                if m:
                    g["tw"] = int(m.group(1))
    out = []
    for (mp, side), g in games.items():
        alive = {}
        for ev in g["ev"]:
            m = INIT.match(ev)
            if m and m.group(3) in TOWERS:
                alive[m.group(1)] = ("T" + m.group(2), m.group(3))
                continue
            m = SPAWN.match(ev)
            if m and m.group(4) in TOWERS and int(m.group(1)) <= upto:
                alive[m.group(2)] = ("T" + m.group(3), m.group(4))
                continue
            m = DIED.match(ev)
            if m and m.group(4) in TOWERS and int(m.group(1)) <= upto:
                alive.pop(m.group(2), None)
        mine = [t for (tm, t) in alive.values() if tm == side]
        out.append(dict(map=mp, side=side, won=g["won"], rounds=g["rounds"],
                        tw_reported=g["tw"],
                        paint=mine.count("PAINT_TOWER"),
                        money=mine.count("MONEY_TOWER"),
                        defense=mine.count("DEFENSE_TOWER"),
                        total=len(mine)))
    return out


def report(label, rows, upto):
    ok = [r for r in rows if r["tw_reported"] is not None]
    bad = [r for r in ok if r["total"] != r["tw_reported"]]
    print(f"\n===== {label}  ({len(rows)} games, {len(ok)} reached r{upto}) =====")
    if bad:
        print(f"!! RECONSTRUCTION DISAGREES with engine tw on {len(bad)}/{len(ok)} games "
              f"-- mix numbers below are NOT trustworthy")
        for r in bad[:5]:
            print(f"   {r['map']:<18}{r['side']}  rebuilt={r['total']} engine tw={r['tw_reported']}")
    else:
        print(f"reconstruction CHECKS against engine tw on all {len(ok)} games")
    if not ok:
        return
    p = sum(r["paint"] for r in ok) / len(ok)
    m = sum(r["money"] for r in ok) / len(ok)
    d = sum(r["defense"] for r in ok) / len(ok)
    print(f"alice towers at r{upto}: paint {p:.2f}   money {m:.2f}   defense {d:.2f}"
          f"   total {p+m+d:.2f}")
    if p + m > 0:
        print(f"PAINT SHARE of alice's paint+money towers: {100*p/(p+m):.1f}%")
    wins = [r for r in ok if r["won"]]
    losses = [r for r in ok if not r["won"]]
    for nm, g in (("won", wins), ("lost", losses)):
        if g:
            pp = sum(r["paint"] for r in g) / len(g)
            mm = sum(r["money"] for r in g) / len(g)
            sh = 100 * pp / (pp + mm) if pp + mm else float("nan")
            print(f"  games alice {nm:<5} ({len(g):>2}): paint {pp:.2f}  money {mm:.2f}"
                  f"  paint share {sh:.1f}%")


if __name__ == "__main__":
    upto = int(sys.argv[1])
    args = sys.argv[2:]
    for i in range(0, len(args), 2):
        report(args[i], load(args[i + 1], upto), upto)

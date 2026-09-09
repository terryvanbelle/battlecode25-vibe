#!/usr/bin/env python3
"""How did the games END? Split a paired gauntlet run by WHO won, then compare
win reasons and winning round.

    tools/end-shape.py gauntlet/<run-id> [opponent]

Written for iteration 45's pre-registered mechanism falsifier. The claim there is
that the arm reaches the 70%-coverage instant win SOONER; a margin built instead
out of round-limit tiebreakers is not that mechanism, however large it is. A
headline win count cannot tell those apart -- this can.

ORIENTATION (stated because getting it backwards inverts the whole reading, and
tools in this workspace have disagreed by construction before): results.txt is
  RESULT <opponent> <map> <bot_side> <winning_side> <rounds>
so the BOT named in bot.txt won iff field 4 == field 5. Rows are labelled with
the actual bot/opponent NAMES, never "us"/"them".
"""
import os, sys, statistics, collections

run = sys.argv[1]
want = sys.argv[2] if len(sys.argv) > 2 else None

bot = "?"
bf = os.path.join(run, "bot.txt")
if os.path.exists(bf):
    for l in open(bf):
        if l.startswith("bot="):
            bot = l.strip().split("=", 1)[1]

# reasons keyed by (opponent, map, bot_side)
reason = {}
rf = os.path.join(run, "reasons.txt")
if os.path.exists(rf):
    for l in open(rf):
        f = l.split()
        if len(f) >= 4:
            reason[(f[0], f[1], f[2])] = " ".join(f[3:])

rounds = collections.defaultdict(list)
reasons = collections.defaultdict(collections.Counter)
for l in open(os.path.join(run, "results.txt")):
    f = l.split()
    if f[:1] != ["RESULT"] or len(f) < 6:
        continue
    opp, mp, side, win, rnd = f[1], f[2], f[3], f[4], int(f[5])
    if want and opp != want:
        continue
    who = bot if side == win else opp
    rounds[who].append(rnd)
    reasons[who][reason.get((opp, mp, side), "?")] += 1

print(f"{run}  bot={bot}\n")
for who in sorted(rounds, key=lambda k: (k != bot, k)):
    rs = rounds[who]
    print(f"{who}: {len(rs)} wins   median round {statistics.median(rs):.0f}   "
          f"mean {statistics.mean(rs):.0f}   min {min(rs)}  max {max(rs)}")
    for txt, n in reasons[who].most_common():
        short = txt.replace("The winning team ", "").rstrip(".")
        print(f"    {n:4d}  ({100*n/len(rs):5.1f}%)  {short}")
    print()

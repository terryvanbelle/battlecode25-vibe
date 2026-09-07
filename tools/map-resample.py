#!/usr/bin/env python3
"""Uncertainty for a gauntlet result, by resampling MAPS -- not binomially.

The engine and both builds are deterministic, so every (map, side) cell is a
fixed function of the two programs. Nothing is random per game. The only thing
that varies between one estimate and another is WHICH MAPS WERE DRAWN, so the
map is the unit of resampling and the binomial sd is the wrong model. In
practice binomial has overstated the spread here by ~2x, because deterministic
per-map outcomes are concentrated rather than coin-flip-like.

  tools/map-resample.py gauntlet/<run-id> [opponent ...]

Reports, PER OPPONENT AND FROM THE WORKSPACE BOT'S OWN PERSPECTIVE, that bot's
score, a bootstrap and jackknife se over maps, a 95% interval, and the distance
from the mirror null.

WHOSE SCORE THIS IS. Earlier this script assumed the workspace bot was the
BASELINE and every opponent a candidate, and counted the opponent's wins. That
is only one of the two conventions in use here: run as
BOT=<baseline> OPPONENTS=<candidates> it was right, and run the other way round
-- BOT=<candidate> OPPONENTS=<baseline> -- every number silently inverted, while
still reading plausibly. It now always reports the wins of the bot the run was
launched as, names that bot in the header, and leaves you to say which side was
the candidate.
"""
import csv, sys, collections, random, statistics, os

def load(run):
    """{opponent: {map: wins BY THE WORKSPACE BOT}}, the map list, and per-opponent
    games actually played.

    The played count matters: an opponent still mid-run has played a PREFIX of the
    map list, not a sample of it, and scoring it against the full maps*2
    denominator prints a catastrophic-looking number for a run that is merely
    incomplete (an arm at 9/50 and -4.30 sd finished at 50/50). collate.sh warns
    about unequal counts and track_vs_old_bots.py refuses to record them; this
    script used to do neither."""
    per = collections.defaultdict(lambda: collections.defaultdict(int))
    played = collections.Counter()
    maps = set()
    for r in csv.DictReader(open(os.path.join(run, "results.csv"))):
        maps.add(r["map"])
        played[r["opponent"]] += 1
        if r["bot_result"] == "win":
            per[r["opponent"]][r["map"]] += 1
    return per, sorted(maps), played


def bot_label(run):
    """Which build actually played, from the run's bot.txt (gauntlet.sh writes it)."""
    f = os.path.join(run, "bot.txt")
    if not os.path.isfile(f):
        return "the run's bot"
    for line in open(f):
        if line.startswith("label="):
            return line.split("=", 1)[1].strip()
    return "the run's bot"

def stats(wins, maps, iters=20000, seed=7):
    n = len(maps)
    score = lambda s: sum(wins[m] for m in s) * n / len(s)
    pt = score(maps)
    random.seed(seed)
    boot = sorted(score([random.choice(maps) for _ in range(n)]) for _ in range(iters))
    bse = statistics.pstdev(boot)
    jack = [score([x for x in maps if x != m]) for m in maps]
    jb = statistics.mean(jack)
    jse = ((n - 1) / n * sum((j - jb) ** 2 for j in jack)) ** 0.5
    return pt, bse, jse, boot[int(.025 * len(boot))], boot[int(.975 * len(boot))]

if __name__ == "__main__":
    run = sys.argv[1]
    per, maps, played = load(run)
    # List opponents from what was PLAYED, not from what was won: `per` only gains
    # a key when the bot wins a game, so an opponent that shut the bot out would
    # silently vanish from the report -- the worst possible one to omit.
    want = sys.argv[2:] or sorted(played)
    null = len(maps)          # the mirror null: every map splits 1-1
    who = bot_label(run)
    full = 2 * len(maps)
    print(f"{run}  maps={len(maps)}  mirror null = {null}/{full}")
    print(f"scores below are WINS BY {who} (the bot this run was launched as)\n")
    for opp in want:
        if played[opp] < full:
            print(f"{opp:18s} INCOMPLETE: {played[opp]} of {full} games played."
                  f" Maps run in a fixed order, so this is a PREFIX, not a sample --")
            print(f"{'':18s} no score printed. Re-run when the arm finishes.")
            continue
        pt, bse, jse, lo, hi = stats(per[opp], maps)
        # se=0 means every map gave the same result, which is a statement about
        # spread, NOT about where the score sits. Labelling a 0/6 shutout "exact
        # null" would be exactly backwards, so separate the two cases.
        if bse:
            sd = f"{(pt-null)/bse:+.2f} sd"
        elif pt == null:
            sd = "exactly the null (se=0, every map split)"
        else:
            sd = f"{pt-null:+.0f} games vs null (se=0, every map identical)"
        dist = dict(sorted(collections.Counter(per[opp][m] for m in maps).items()))
        print(f"{opp:18s} {pt:.0f}/{2*len(maps)}  boot_se={bse:.2f} jack_se={jse:.2f}"
              f"  95% CI [{lo:.0f}, {hi:.0f}]  {sd}")
        print(f"{'':18s} per-map wins by {who} (0/1/2): {dist}")

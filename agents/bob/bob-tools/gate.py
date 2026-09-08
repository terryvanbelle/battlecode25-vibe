#!/usr/bin/env python3
"""Read a gauntlet run and apply my accept gate, with the UNIT IN EVERY NAME.

    bob-tools/gate.py gauntlet/<run-id>

Why this file exists
--------------------
My gate is "+10 accept / +7..+9 replicate / +6 reject" and my calibrated noise
floor is "sd 4.80 per 150".  Neither number carries its unit, and there are two
units in play that differ by exactly a factor of 2:

    wins_above_half = W - N/2         <- the unit I actually use, everywhere
    win_minus_loss  = W - L = 2*(W - N/2)

Because W + L = N, win_minus_loss is exactly 2 x wins_above_half, so quoting a
threshold in one unit against an sd measured in the other silently halves or
doubles the strictness of the gate.  Another lineage shipped that exact bug: its
tool multiplied by 2 for the unit conversion and then labelled the product
"2.0 sd", so every gate it produced was 1.0 sd wearing a 2.0 sd label -- a
one-tail false-accept rate near 16% where it believed it had 2%.

SETTLED FOR THIS LINEAGE, from published numbers rather than memory:
  - iteration 32 census, W=67 of N=150.  I published -8.
    wins_above_half = -8.  win_minus_loss = -16.  So my unit is WINS ABOVE HALF.
  - iteration 31 ladder, published +0/+2/-7/-3; the W-L reading would have been
    +0/+4/-14/-6.  Same answer.
  - SD_WINS = 4.80 is the sd of the WIN COUNT: my calibration compared it to a
    binomial 6.12 = sqrt(150 * 0.25), which is a win-count sd.

  => +10 wins_above_half / 4.80 = 2.08 sd.  Sound as intended.
     (Had it meant W-L it would be 10/9.60 = 1.04 sd, half as strict.)

The durable fix is that the names below carry their units, so the next session
cannot make this mistake by being less careful than I was.  Do not add a
function that returns a bare "margin".
"""
import csv, sys, collections

SD_WINS_PER_150 = 4.80        # sd of the WIN COUNT over 150 games. NOT of W-L.
GATE_ACCEPT_WINS_ABOVE_HALF = 10
GATE_REPLICATE_LOW_WINS_ABOVE_HALF = 7

def sd_wins(n_games):
    """sd of the win COUNT, scaled from the 150-game calibration."""
    return SD_WINS_PER_150 * (n_games / 150.0) ** 0.5

def verdict(wins_above_half, n_games):
    if n_games < 150:
        return "NO VERDICT (sub-census: a 50-game arm cannot resolve below ~14 wins_above_half)"
    if wins_above_half >= GATE_ACCEPT_WINS_ABOVE_HALF:      return "ACCEPT"
    if wins_above_half >= GATE_REPLICATE_LOW_WINS_ABOVE_HALF: return "REPLICATE"
    return "REJECT"

def main(run):
    rows = list(csv.DictReader(open(f"{run}/results.csv")))
    per = collections.defaultdict(lambda: [0, 0])   # opponent -> [wins, games]
    for r in rows:
        p = per[r["opponent"]]
        p[1] += 1
        p[0] += (r["bot_result"] == "win")
    print(f"{run}  ({len(rows)} games, bot = the BOT column of bot.txt)\n")
    # BOTH perspectives, always, explicitly named. A ladder writeup reports the
    # ARM's margin (is the candidate better?) while results.csv is written from the
    # BOT's perspective, so the two differ by a sign. Printing only one is how a
    # correct number gets published upside down -- and this lineage has already
    # published an arm ladder as +0/+2/-7/-3 whose bot-side reading is +0/-2/+7/+3.
    print(f"  {'opponent':14} {'wins/games':>12} {'bot_wins_above_half':>20} "
          f"{'arm_wins_above_half':>20} {'sd_wins':>8} {'z(bot)':>7}  verdict(bot)")
    for opp in sorted(per):
        w, n = per[opp]
        bot_wah = w - n / 2.0
        arm_wah = -bot_wah          # zero-sum: the arm's wins above half
        s = sd_wins(n)
        print(f"  {opp:14} {w:>5}/{n:<6} {bot_wah:>+20.1f} {arm_wah:>+20.1f} "
              f"{s:>8.2f} {bot_wah/s:>+7.2f}  {verdict(bot_wah, n)}")
    if len(per) > 1:
        print("\n  (multi-arm run: this is a SHAPE ladder. Per my doctrine it accepts nothing;")
        print("   promote a peak to a 150-game census and judge it there.)")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1].rstrip("/"))

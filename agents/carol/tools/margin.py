#!/usr/bin/env python3
"""Signed gauntlet margins that CANNOT be computed against the wrong referent.

Why this exists: `results.csv` carries `bot_result`, which is the perspective of the run's
own BOT -- and a gauntlet is launched either way round (BOT=baseline with the candidate as
an opponent, or BOT=candidate with the baseline as an opponent). Reading `bot_result` without
resolving which, silently inverts every signed number downstream.

This lineage has now produced that inversion twice. Both were caught because the magnitude was
absurd (-11.24 sd once), NOT because the code was re-read. A third will land in a plausible
range and become a verdict. So the guard belongs in the tool, not in the discipline:

  * the candidate must be named EXPLICITLY -- there is no default;
  * it is checked against the run's own bot.txt and its opponent set;
  * if the named candidate is neither the BOT nor an opponent, it refuses rather than guessing.

    tools/margin.py gauntlet/<run-id> --candidate carol_i69_2 [--opponent bobf]
"""
import csv, sys, os, argparse

def load(rundir):
    bot = None
    p = os.path.join(rundir, 'bot.txt')
    if os.path.exists(p):
        for line in open(p):
            if line.startswith('bot='):
                bot = line.strip().split('=', 1)[1]
    rows = list(csv.DictReader(open(os.path.join(rundir, 'results.csv'))))
    return bot, rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rundir')
    ap.add_argument('--candidate', required=True,
                    help='REQUIRED. No default: naming the referent is the whole point.')
    ap.add_argument('--opponent', default=None)
    a = ap.parse_args()
    bot, rows = load(a.rundir)
    if bot is None:
        sys.exit('REFUSING: %s has no bot.txt, so the referent cannot be resolved.' % a.rundir)
    opps = sorted({r['opponent'] for r in rows})
    if a.candidate == bot:
        cand_is_bot = True
    elif a.candidate in opps:
        cand_is_bot = False
    else:
        sys.exit('REFUSING: candidate %r is neither the run BOT (%r) nor an opponent (%s).'
                 % (a.candidate, bot, ', '.join(opps)))
    sel = [r for r in rows if a.opponent is None or r['opponent'] == a.opponent]
    if not sel:
        sys.exit('REFUSING: no games against opponent %r.' % a.opponent)
    # bot_result is the BOT's result. Candidate wins are those rows iff the candidate IS the bot.
    wins = sum(1 for r in sel if (r['bot_result'] == 'win') == cand_is_bot)
    n = len(sel)
    print('run          %s' % a.rundir)
    print('run BOT      %s' % bot)
    print('candidate    %s   (%s)' % (a.candidate, 'IS the run BOT' if cand_is_bot else 'is an OPPONENT'))
    # Name the unit, per METHODS: "margin" spans two quantities that differ by a factor of two,
    # and this project has published a 6.8 sd that was 3.39. Print both, labelled.
    print('candidate    %d/%d = %.1f%%' % (wins, n, 100.0 * wins / n))
    print('  wins_minus_losses %+d      wins_above_half %+d' % (2 * wins - n, wins - n // 2))
    print('  NOTE: a DELTA against another run is neither of these -- it is this run\'s wins')
    print('        minus that run\'s wins, and both must be computed through this tool.')

if __name__ == '__main__':
    main()

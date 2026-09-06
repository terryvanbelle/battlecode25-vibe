#!/usr/bin/env bash
# Interim tally of a running gauntlet from the raw results.txt.
# RESULT <opponent> <map> <bot_side> <winner_side> <rounds>
# NOTE: when the gauntlet's BOT is the ZERO ARM of a dose sweep, a LOSS for BOT
# is a WIN for the dose -- both columns are printed so neither can be misread.
awk '$1=="RESULT" {
        n[$2]++; if ($4==$5) w[$2]++
     }
     END {
        for (o in n) printf "  BOT %2d/%-2d (%5.1f%%) vs %-14s   =>  %s scores %2d/%-2d (%5.1f%%)\n",
            w[o], n[o], 100*w[o]/n[o], o, o, n[o]-w[o], n[o], 100*(n[o]-w[o])/n[o]
     }' "$1"

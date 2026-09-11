#!/usr/bin/env bash
# Direct head-to-head of a candidate against the shipped baseline, all 75 maps.
#
# WHY, and why it is more sensitive than the screens: a 3-opponent gauntlet asks
# "how does each build do against carol/bob/alice", and the difference between
# two nearly-identical builds is then a difference of differences -- which is why
# the instrument's floor is ~5 points there. Playing the candidate DIRECTLY
# against the baseline measures the marginal change once instead of twice, on
# every map in the pool rather than a 12-map sample.
#
# This is legitimate self-play, not doctrine-17 self-play blindness: the question
# is not "is this bot good" but "does this ONE change help", and the two builds
# differ by exactly that change.
#
# Usage: tools/head-to-head.sh <candidate-package>
set -uo pipefail
ARM="${1:?usage: head-to-head.sh <package> [reference]}"
# The reference is EXPLICIT. It defaulted to "darla", which was correct until
# iteration 1 was accepted and src/darla became the new build -- at which point
# an attribution run would silently have measured a candidate against the very
# change it was meant to attribute. src/darla_iter0 is the frozen pre-acceptance
# baseline and is the right reference for anything comparing against it.
REF="${2:-darla_iter0}"
cd /home/terryvanbelle/projects/vibe/2025/agents/darla
while [ "$(grep -cvE '^\s*(#|$)' progress/pending-arms.txt 2>/dev/null || true)" -gt 0 ] \
   || pgrep -f '\.reexec-gauntlet\.sh' > /dev/null; do sleep 60; done
echo "$(date -uIs) H2H START $ARM vs $REF -- all 75 maps, both sides"
MAPS="$(tr '\n' ' ' < ../../tools/bc25-maps.txt)" BOT="$ARM" OPPONENTS="$REF" MAXJOBS=2 \
  ../../tools/gauntlet.sh || { echo "$(date -uIs) H2H ERROR $ARM"; exit 1; }
run=$(ls -1t gauntlet | head -1)
echo "$(date -uIs) H2H COMPLETE $ARM $run -- $(grep -E '^overall' gauntlet/$run/summary.txt)"

#!/usr/bin/env bash
# ITERATION 47 census: whole-game counters per team per replay, on battlecode-dev.
#
#   bob-tools/refill-census.sh <run-id> [stride]
#
# USE STRIDE 1. I wrote this script asserting that a stride is free, TESTED the
# assertion, and it is FALSE -- recording both, because the wrong version is the
# plausible one.
#
# The reasoning that looked right: ReplayDump RESETS its action/death/xfer/
# starved counters immediately after printing each team line (ReplayDump.java,
# `Arrays.fill(...)` right below `println(sb)`), so a printed line carries
# everything accumulated SINCE THE PREVIOUS PRINTED LINE, and summing the printed
# lines should give exact whole-game totals at any stride.
#
# What it misses: rounds AFTER the final printed line are never flushed, so each
# game silently loses up to (stride - 1) rounds off its end. Measured on the same
# two replays (iteration 45's run 20260909-162244, bob_m0 vs BunnyGame):
#
#     stride |  xfer  starv   died   paint   dCov
#          1 |  14.5  26.00  33.50  1027.0  433.0     <- ground truth
#         10 |  14.5  25.50  32.50  1023.5  431.0     <- -0.3% to -3%
#         50 |  14.5  24.00  31.00  1017.5  430.0     <- -0.9% to -8%
#
# Every counter except xfer decays monotonically with stride, and the loss is a
# function of each game's end-round mod stride -- so it is NOT a constant offset
# that cancels between arms, it varies with how long each arm's games run. For an
# iteration whose whole claim is that games get LONGER, a stride-dependent bias in
# death and action counts is exactly the wrong error to carry.
#
# So: stride 1, which prints every round and loses nothing. The stride argument is
# kept for cheap smoke tests only. Soldier-rounds are sum(sold) * stride, exact at
# stride 1.
#
# Reuses tools/replaydump/ReplayDump.java verbatim -- not a fork.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
source "$REPO/tools/lib.sh"
RUN="$1"; STRIDE="${2:-10}"; FILT="${3:-}"
WANT_VER="$(cat "$REPO/arena/engine_version.txt")"
RDIR="\$HOME/battlecode25-vibe/agents/bob/gauntlet/$RUN"
ensure_vm
W="bobrefill-$$"
gssh "mkdir -p ~/$W" >/dev/null
trap 'gssh "rm -rf ~/'"$W"'" >/dev/null 2>&1 || true' EXIT
gscp "$REPO/tools/replaydump/ReplayDump.java" "$USER_NAME@$IP:$W/" >/dev/null
gssh "
  export PATH=\$HOME/jdk21/bin:\$PATH
  BC_JAR=\$(find ~/.gradle -name 'battlecode25-java-$WANT_VER.jar' | grep -v source | head -1)
  [ -n \"\$BC_JAR\" ] || { echo '!! no pinned engine jar' >&2; exit 1; }
  cd ~/$W
  javac -d . -classpath \"\$BC_JAR\" ReplayDump.java 2>&1 | head -3
  for f in $RDIR/*$FILT*.bc25; do
    b=\$(basename \"\$f\")
    # ISOLATION: drop every IND line at the source (RULES.md, 2026-09-09) -- a
    # gauntlet replay is all mine, but the filter is unconditional by policy so
    # this script can never become the one that leaks a tournament replay.
    java -classpath \".:\$BC_JAR\" com.google.flatbuffers.ReplayDump \"\$f\" --every $STRIDE 2>/dev/null |
      grep -v ' IND ' |
      awk -v F=\"\$b\" '
        /^=== GameHeader/ { if (match(\$0,/team1=[^ ]+/)) t1=substr(\$0,RSTART+6,RLENGTH-6);
                            if (match(\$0,/team2=[^ ]+/)) t2=substr(\$0,RSTART+6,RLENGTH-6);
                            printf \"HDR\t%s\t%s\t%s\n\", F, t1, t2 }
        /^round .* \\| T1 / { printf \"ROW\t%s\t%s\n\", F, \$0 }
        /^=== MatchFooter/ { printf \"FTR\t%s\t%s\n\", F, \$0 }'
  done
"

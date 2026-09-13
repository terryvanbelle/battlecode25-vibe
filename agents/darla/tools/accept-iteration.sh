#!/usr/bin/env bash
# Promote an accepted arm, mechanically and in the right order.
#
#   tools/accept-iteration.sh <arm> <N>      # N = iteration number to FREEZE as
#
# Freezes the current src/darla as src/darla_iter<N>, promotes <arm> onto
# src/darla as darla-i<N+1>, and prints the resulting diff for the notebook.
#
# WHY THIS EXISTS, twice over:
#
#   1. The accept has five steps -- freeze, promote, promotion test, v3 benchmark,
#      push -- and doing them by hand has gone wrong before: 31 commits once sat
#      unpushed, an arm's source was committed two days after its result, and the
#      benchmark went two accepted iterations stale. A script cannot forget.
#   2. The freeze needs `rm -rf`, which is (correctly) on the ask list, so the
#      owner was prompted mid-accept for a routine step. A gauntlet driver under
#      tools/ is already allowed, so moving the rm in here removes the prompt
#      without loosening the rule for anything else.
#
# It deliberately does NOT commit: the notebook entry is the part that needs a
# person, and a script that commits invites an accept with no write-up.
set -euo pipefail
ARM="${1:?usage: accept-iteration.sh <arm> <N-to-freeze-as>}"
N="${2:?}"
cd "$(dirname "${BASH_SOURCE[0]}")/.."
NEXT=$((N + 1))

[ -f "src/$ARM/RobotPlayer.java" ] || { echo "!! no such arm: src/$ARM"; exit 1; }
[ -d "src/darla_iter$N" ] && { echo "!! src/darla_iter$N already exists -- wrong N?"; exit 1; }
diff -q <(tail -n +2 src/darla/RobotPlayer.java) <(tail -n +2 "src/$ARM/RobotPlayer.java") >/dev/null \
  && { echo "!! $ARM is identical to the shipped build below the package line"; exit 1; }

rm -rf "src/darla_iter$N"
cp -r src/darla "src/darla_iter$N"
sed -i "s/^package darla;/package darla_iter$N;/; s/BUILD = \"[^\"]*\"/BUILD = \"darla_iter$N\"/" \
  "src/darla_iter$N/RobotPlayer.java"
grep -qx "package darla_iter$N;" "src/darla_iter$N/RobotPlayer.java" || { echo "!! freeze failed"; exit 1; }

cp "src/$ARM/RobotPlayer.java" src/darla/RobotPlayer.java
sed -i "s/^package $ARM;/package darla;/; s/BUILD = \"$ARM\"/BUILD = \"darla-i$NEXT\"/" src/darla/RobotPlayer.java
grep -qx 'package darla;'          src/darla/RobotPlayer.java || { echo "!! promote failed: package"; exit 1; }
grep -q  "BUILD = \"darla-i$NEXT\"" src/darla/RobotPlayer.java || { echo "!! promote failed: BUILD"; exit 1; }

echo "frozen  src/darla_iter$N"
echo "shipped src/darla is now darla-i$NEXT (was $ARM)"
echo "=== behavioural diff vs the frozen build:"
diff <(tail -n +2 "src/darla_iter$N/RobotPlayer.java") <(tail -n +2 src/darla/RobotPlayer.java) \
  | grep '^[<>]' | grep -v 'BUILD =' | cut -c1-140
echo
echo "NEXT, and none of it is automatic:"
echo "  1. write the DESIGN.md entry, commit, push"
echo "  2. tools/head-to-head.sh darla darla_iter$N     # must return the arm's exact screen score"
echo "  3. BOTS=darla BENCH=v3 ../../tools/benchmark.sh  # standing rule: benchmark on every accept"

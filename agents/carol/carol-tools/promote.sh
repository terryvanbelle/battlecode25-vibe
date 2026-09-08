#!/usr/bin/env bash
# Promote an accepted candidate tree to src/carol and freeze it as src/carol_iterN.
#
# Two things this gets right that a manual copy has got wrong before:
#   * the package line must match the DIRECTORY, in both the live tree and the snapshot;
#   * the snapshot must be frozen from the SAME text that becomes src/carol, so the frozen
#     opponent in the roster is byte-identical in behaviour to what was measured.
#
#   promote.sh <candidate-pkg> <N>      e.g. promote.sh carol_i39_all 39
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
CAND="$1"; N="$2"; SNAP="carol_iter$N"
[ -f "src/$CAND/RobotPlayer.java" ] || { echo "no such candidate: src/$CAND" >&2; exit 1; }
[ -e "src/$SNAP" ] && { echo "snapshot src/$SNAP already exists -- refusing to overwrite" >&2; exit 1; }
mkdir -p "src/$SNAP"
sed "s/^package $CAND;/package $SNAP;/" "src/$CAND/RobotPlayer.java" > "src/$SNAP/RobotPlayer.java"
sed "s/^package $CAND;/package carol;/"  "src/$CAND/RobotPlayer.java" > "src/carol/RobotPlayer.java"
grep -h '^package' "src/$SNAP/RobotPlayer.java" "src/carol/RobotPlayer.java"
echo "promoted $CAND -> src/carol and frozen as src/$SNAP"
echo "NOW: ./tools/vm-compile.sh   (HEAD must compile -- it is what plays in the tournament)"

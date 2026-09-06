#!/usr/bin/env bash
# Freeze the current src/bob as src/bob_iterN (package bob_iterN) and compile-check it
# in isolation. TRAINING_ALGORITHM.md's post-accept routine is atomic and "every one
# of these lapsed for 10+ iterations at some point when treated as later" -- so it is
# a script, not a habit.
#
# Usage: bob-tools/snapshot.sh <N>
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
N="${1:?usage: snapshot.sh <N>}"
DST="src/bob_iter$N"
[ -e "$DST" ] && { echo "refusing to overwrite existing $DST" >&2; exit 1; }
cp -r src/bob "$DST"
# Package rename. The bot uses no fully-qualified self-references (checked), so the
# package line is the only thing that has to move; the guard below fails loudly if
# that ever stops being true.
sed -i "s/^package bob;/package bob_iter$N;/" "$DST"/*.java
if grep -rn '\bbob\.' "$DST"/*.java; then
  echo "!! fully-qualified 'bob.' reference found above -- fix before trusting this snapshot" >&2
  exit 1
fi
bob-tools/compile-check.sh "bob_iter$N"
echo "snapshot ready: $DST"

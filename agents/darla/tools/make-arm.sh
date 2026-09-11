#!/usr/bin/env bash
# Create an arm from the baseline and PROVE it differs exactly as intended.
#
#   tools/make-arm.sh <name> '<sed expr>' '<expected substring in the changed line>'
#
# WHY: darla14 was queued as a byte-identical copy of the baseline. Its sed
# silently matched nothing, so the file kept `package darla;`, the classes landed
# in package `darla`, the engine could not load `darla14.RobotPlayer`, and all 72
# games were forfeited -- 0/72, which briefly looked like a catastrophic result
# rather than a build that never ran. A `javac ... && echo COMPILE_OK` does NOT
# catch this: it happily compiles the baseline under a new directory name.
#
# So this script refuses to leave a broken arm on disk:
#   1. the package line must actually name the arm;
#   2. the diff against the baseline must be NON-EMPTY;
#   3. the intended change must be present.
# Any failure removes the directory, so a broken arm can never reach the queue.
#
# The BUILD rewrite matches ANY current value, not the literal "darla1". It was
# pinned to "darla1" and would have silently stopped rewriting the moment the
# baseline was promoted to "darla-i1" -- the check on line 30 would then have
# caught it, but as a confusing failure rather than a no-op, and every arm built
# on the accepted baseline would have refused to build.
set -euo pipefail
NAME="${1:?usage: make-arm.sh <name> <sed-expr> <expected>}"
SED="${2:?}"; EXPECT="${3:?}"
cd "$(dirname "${BASH_SOURCE[0]}")/.."          # agents/darla
SRC=src/darla/RobotPlayer.java
DST="src/$NAME/RobotPlayer.java"

rm -rf "src/$NAME"; cp -r src/darla "src/$NAME"
sed -i "s/^package darla;/package $NAME;/; s/BUILD = \"[^\"]*\"/BUILD = \"$NAME\"/; $SED" "$DST"

fail () { echo "!! $NAME: $1"; rm -rf "src/$NAME"; exit 1; }
grep -qx "package $NAME;" "$DST"        || fail "package line was not rewritten"
grep -q "BUILD = \"$NAME\""  "$DST"     || fail "BUILD constant was not rewritten"
grep -q "$EXPECT"            "$DST"     || fail "intended change absent: expected '$EXPECT'"
n=$(diff <(tail -n +2 "$SRC") <(tail -n +2 "$DST") | grep -c '^[<>]' || true)
[ "$n" -ge 2 ] || fail "diff against baseline is empty below the package line"

echo "$NAME: OK -- $((n/2)) changed line(s) beyond package/BUILD"
grep -n "$EXPECT" "$DST" | head -2

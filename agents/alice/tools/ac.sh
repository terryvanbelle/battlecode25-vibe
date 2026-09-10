#!/usr/bin/env bash
# Commit alice's paths from ANY working directory.
#
#   tools/ac.sh -m "message" agents/alice/<path> [more...]
#   tools/ac.sh -m "message" TRAINING_LOG.md            # also accepts bare names
#
# WHY THIS EXISTS (doctrine 19 -- install the check where the mistake happens):
# tools/agent-commit.sh takes repo-relative paths, and I habitually `cd` into
# agents/alice to do the work. `git add agents/alice/foo` then resolves to
# agents/alice/agents/alice/foo and dies with "pathspec did not match any files".
# That cost me three failed commits in one session, each time after a long
# heredoc had already run -- so the failure lands *after* the irreplaceable part,
# which is the worst place for it. Remembering to cd back is not a fix; this is.
#
# It cds to the repo root itself and normalises every path argument to
# agents/alice/..., so the same command works from the repo root, from
# agents/alice, or from anywhere else.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

args=()
for a in "$@"; do
  case "$a" in
    -m|--*|-*)            args+=("$a") ;;                       # flags pass through
    agents/alice/*)       args+=("$a") ;;                       # already correct
    */*|*.md|*.sh|*.py|*.java|*.txt)
      # a workspace-relative path: prefix it, but only if that file exists
      if [ -e "agents/alice/$a" ]; then args+=("agents/alice/$a"); else args+=("$a"); fi ;;
    *)                    args+=("$a") ;;                       # message text etc.
  esac
done

# ---------------------------------------------------------------- POINTER GATE
# Added after the SECOND time in one session that a piped exit status let a broken
# LEARNINGS pointer into the repo:
#
#     bash tools/check-pointers.sh 2>&1 | tail -2 && tools/ac.sh ...
#
# A pipeline's exit status is its LAST command's, so that reads `tail`'s status,
# which is always 0. The check printed FAIL and the commit ran anyway. The same
# family had already bitten me as `diff | head && echo IDENTICAL`, and it was
# ALREADY in LEARNINGS by name. Knowing a trap by name did not stop me walking
# into it, because the guard lived in a document and not in the command.
#
# So it lives here now. This is the same argument this session made for putting a
# gate's branch order into code rather than into my intentions.
#
# Note the invocation: `bash "$CHECK"` with NO pipe, so the gate reads the tool's
# own status. Never `... | tail`.
CHECK="$ROOT/agents/alice/tools/check-pointers.sh"
if [ "${AC_SKIP_POINTERS:-0}" = "1" ]; then
  echo "ac.sh: pointer check SKIPPED (AC_SKIP_POINTERS=1)" >&2
elif [ -f "$CHECK" ]; then
  OUT="$(mktemp)"
  # AC_SELFTEST=1 forces the failure branch, so this guard is provably reachable.
  # A check that has never failed may be a check that CANNOT fail -- the defect
  # roster-stale.sh was given a SELFTEST for, for exactly this reason.
  if [ "${AC_SELFTEST:-0}" = "1" ]; then
    echo "ac.sh SELFTEST: forcing the pointer gate to fail" > "$OUT"; ok=1
  elif bash "$CHECK" > "$OUT" 2>&1; then
    ok=0
  else
    ok=1
  fi
  if [ "$ok" != "0" ]; then
    echo "!! ac.sh REFUSING TO COMMIT -- LEARNINGS.md has dead pointer(s):" >&2
    cat "$OUT" >&2; rm -f "$OUT"
    echo "!! A dead pointer orphans a lesson from its evidence. Fix it, or set" >&2
    echo "!! AC_SKIP_POINTERS=1 if the TRAINING_LOG entry it names is not written yet." >&2
    exit 3
  fi
  rm -f "$OUT"
fi

exec "$ROOT/tools/agent-commit.sh" alice "${args[@]}"

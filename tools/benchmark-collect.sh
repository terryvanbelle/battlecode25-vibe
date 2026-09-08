#!/usr/bin/env bash
# Collate a benchmark run that finished on battlecode-dev but whose driver-side
# poll loop did not survive to collate it.
#
#   tools/benchmark-collect.sh                 # newest remote run
#   tools/benchmark-collect.sh 20260908-0130   # a specific run
#   tools/benchmark-collect.sh --list          # what is on the VM, and whether it finished
#
# WHY THIS EXISTS. The gauntlets have had gauntlet-collect.sh since the first
# session death; the benchmark did not, and it is the most expensive thing this
# project runs -- 900 games. Its remote runner is setsid-detached exactly like a
# gauntlet's, so a driver-side death (a pause, an OOM kill, a dropped SSH) never
# stops the games; it only loses the collation. Without this tool, a run that
# died at game 850 left the results sitting on the VM with no way to pick them
# up, and the only option was to pay for all 900 again.
#
# COORDINATOR ONLY, and it inherits the benchmark's hard rules by construction:
# it transfers a text results file and nothing else. No replay was ever written
# by the run (benchmark.sh omits -Dbc.server.save-file), so there is none here to
# fetch, examine or discard.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib.sh"
source "$HERE/benchmark-collate.sh"

ensure_vm
RDIR="bc25-benchmarks"

if [ "${1:-}" = --list ]; then
  listing=$(mktemp)
  # Results files are ~/bc25-benchmarks/<run-id>.txt; the runner script is
  # ~/benchmark-<run-id>.sh and is removed only on a successful collation, so
  # its presence is a second hint that a run was never collected.
  gssh "for f in \$(ls -t ~/$RDIR/*.txt 2>/dev/null); do
          r=\$(basename \$f .txt)
          printf '%-16s %4s games  %-10s %s\n' \"\$r\" \
            \"\$(grep -c '^RESULT ' \$f 2>/dev/null || echo 0)\" \
            \"\$(grep -q BENCHMARK-COMPLETE \$f 2>/dev/null && echo complete || echo INCOMPLETE)\" \
            \"\$(pgrep -f benchmark-\$r.sh >/dev/null && echo '(RUNNING NOW)' || echo '')\"
        done" > "$listing" 2>/dev/null || true
  # An empty listing is the normal state before the first run. Say so: a tool
  # that prints nothing is indistinguishable from a tool that is broken.
  if [ -s "$listing" ]; then cat "$listing"
  else echo "(no benchmark runs on $VM -- ~/$RDIR holds no <run-id>.txt)"; fi
  rm -f "$listing"
  exit 0
fi

RUN_ID="${1:-$(gssh "ls -t ~/$RDIR/*.txt 2>/dev/null | head -1 | xargs -r basename | sed 's/\.txt\$//'")}"
[ -n "$RUN_ID" ] || { echo "!! no benchmark runs under ~/$RDIR on $VM" >&2; exit 1; }

# Refuse to collate a run that is still playing. Its results file grows under
# us, so the scores would be a snapshot mislabelled as a finished measurement --
# and the live poll loop is about to write the real one.
if gssh "pgrep -f 'benchmark-$RUN_ID.sh' >/dev/null && echo RUNNING" | grep -q RUNNING; then
  echo "!! run $RUN_ID is STILL RUNNING on $VM." >&2
  echo "   Let it finish -- its own poll loop will collate it. Collating now" >&2
  echo "   would freeze a partial result and label it final." >&2
  exit 1
fi

OUT="$REPO_ROOT/benchmarks/$RUN_ID"
mkdir -p "$OUT"
RAW="$OUT/raw.txt"

gscp "$USER_NAME@$IP:$RDIR/$RUN_ID.txt" "$RAW" >/dev/null \
  || { echo "!! no results file for run $RUN_ID on $VM" >&2; exit 1; }

grep -q '^BUILD-FAILED' "$RAW" && {
  echo "!! run $RUN_ID failed to build on the VM -- no games were played" >&2
  rm -rf "$OUT"; exit 1; }
grep -q '^RESULT ' "$RAW" || {
  echo "!! run $RUN_ID has no RESULT lines -- nothing to collate" >&2
  rm -rf "$OUT"; exit 1; }

echo "collecting benchmark $RUN_ID ($(grep -c '^RESULT ' "$RAW") games)"
collate_benchmark
rm -f "$RAW"

# Only now is it safe to clear the VM: the results are on disk here.
gssh "rm -f ~/$RDIR/$RUN_ID.txt ~/benchmark-$RUN_ID.sh" >/dev/null 2>&1 || true

cat "$OUT/summary.md"
echo
echo "wrote $OUT/"

#!/usr/bin/env bash
# Run the finalist-bot benchmark after the EVENING tournament, and commit scores.
#
# Chained from bc25-tournament.service via OnSuccess=, rather than from its own
# timer, because the benchmark and the tournament must never overlap: both run
# hundreds of games through the same five-slot semaphore on battlecode-dev, and a
# timer set to "18:00 plus however long a tournament takes" is a guess that goes
# wrong the first time the VM is busy.
#
# It previously ran as a shell loop inside the coordinator's session, polling
# `systemctl is-active`. That was killed by the OOM killer on a 2G driver, taking
# the benchmark with it and leaving no trace in any log. Anything that must
# survive the session belongs in systemd.
#
# EVENING ONLY. The user asked for the benchmark after the 18:00 Pacific
# tournament, not the 06:00 one. The tournament timer fires at both, so the guard
# lives here.
set -uo pipefail
cd /home/terryvanbelle/projects/vibe/2025

# The guard keys on the hour the TOURNAMENT FINISHED, which is the only clock
# available at OnSuccess time. The morning run starts at 06:00 Pacific and has
# never taken more than an hour, so 06:00-11:59 is its window with hours to
# spare. Everything else is the evening run -- INCLUDING the small hours, since
# an evening tournament that runs long finishes after midnight Pacific and would
# read as "0" under a naive `hour < 12` test, skipping the run the user actually
# asked for.
HOUR=$(TZ=America/Los_Angeles date +%-H)
if [ "$HOUR" -ge 6 ] && [ "$HOUR" -lt 12 ]; then
    echo "$(date -u +%FT%TZ) benchmark: morning tournament (${HOUR}h Pacific) -- not the evening run, skipping"
    exit 0
fi
echo "$(date -u +%FT%TZ) benchmark: evening run (${HOUR}h Pacific) -- starting"

BENCH="TSPAARKHS v3" tools/benchmark.sh || { echo "!! benchmark failed"; exit 1; }

# Newest run directory that actually holds results. Deliberately NOT a run-id
# regex: the first version required [0-9]{8}-[0-9]{6} while benchmark.sh stamps
# %Y%m%d-%H%M -- four digits, not six. It matched nothing, so the very first
# real benchmark played all 900 games, wrote them, and then this wrapper
# declared "no benchmark run directory produced" and exited 1. The measurement
# survived only because the games were already on disk.
# Keying on the artifact rather than on the name cannot drift apart from the
# producer the way a duplicated format string does.
RUN=$(ls -1t benchmarks 2>/dev/null | head -1)
[ -n "$RUN" ] && [ -f "benchmarks/$RUN/scores.csv" ] || {
    echo "!! no benchmark run directory with scores.csv under benchmarks/"; exit 1; }

# scores.csv and summary.md only. No replay was ever written -- benchmark.sh
# omits -Dbc.server.save-file precisely so there is nothing to discard here.
# HISTORY.md too: benchmark-collate.sh regenerates it, but it lives beside the
# run directories rather than inside one, so committing only "benchmarks/$RUN"
# left every history update sitting uncommitted in a shared working tree. The
# cross-run view was the point of the file, and it would have been the one part
# that never reached the repo.
git add "benchmarks/$RUN" benchmarks/HISTORY.md
git commit -m "benchmark $RUN scores" || exit 0

for i in 1 2 3; do
  git push origin main && { echo "   pushed"; exit 0; }
  git fetch --quiet origin || true
  git merge --ff-only origin/main 2>/dev/null || {
    echo "!! branch diverged from origin; scores committed locally but NOT pushed"; exit 0; }
done

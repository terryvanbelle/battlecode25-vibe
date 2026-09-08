#!/usr/bin/env bash
# One-shot verdict pipeline for a gauntlet run: headline, pre-registered gates, covariate,
# and the paired manipulation check. Usage: verdict.sh <run-id> <candidate> <incumbent>
set -euo pipefail
WS=/home/terryvanbelle/projects/vibe/2025/agents/carol
RUN=$1; CAND=$2; INC=$3
cd "$WS"
echo "================ SUMMARY"
cat "gauntlet/$RUN/summary.txt"
echo
echo "================ COVARIATE + LARGE-HALF (gate 3)"
../../tools/.venv/bin/python3 carol-tools/covar/mapcovar.py "gauntlet/$RUN" "$INC"
echo
echo "================ MANIPULATION CHECK (paired, loss replays)"
../../tools/.venv/bin/python3 carol-tools/mixcheck/paircheck.py "$CAND" gauntlet/$RUN/losses/${INC}__*.bc25

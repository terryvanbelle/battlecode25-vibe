#!/usr/bin/env bash
# Cron entry point: pull latest agent commits, run the round-robin tournament,
# commit+push the results. Installed at 06:00 and 18:00 UTC on claude-driver.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"
echo "=== cron tournament $(date -u +%FT%TZ) ==="

git pull --rebase --autostash origin main || echo "!! git pull failed; running on local HEAD"
tools/tournament.sh || { echo "!! tournament failed"; exit 1; }

RUN=$(ls -1 tournaments | tail -1)
git add "tournaments/$RUN"
git commit -m "tournament $RUN results" || exit 0
for i in 1 2 3; do
  git push origin main && break
  git pull --rebase --autostash origin main
done

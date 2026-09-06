#!/usr/bin/env bash
# Cron entry point: sync the repo, run the round-robin tournament, commit+push
# the results. Installed at 06:00 and 18:00 UTC on claude-driver.
#
# NEVER use `git pull --rebase --autostash` here. All three agents work in THIS
# checkout, and at cron time they are usually mid-iteration with uncommitted
# edits; autostash would momentarily remove their working-tree changes (poisoning
# any build or upload running in that window) and a stash-pop conflict would
# leave their tree wedged. So: fetch + fast-forward only, which never rewrites a
# dirty working tree. The tournament itself reads bots from HEAD via `git
# archive`, so an unsynced or dirty tree cannot poison the games either.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"
echo "=== cron tournament $(date -u +%FT%TZ) ==="

git fetch --quiet origin || echo "!! git fetch failed; running on local HEAD"
git merge --ff-only origin/main 2>/dev/null || echo "   (no fast-forward available; running on local HEAD)"

tools/tournament.sh || { echo "!! tournament failed"; exit 1; }

RUN=$(ls -1 tournaments | tail -1)
git add "tournaments/$RUN"
git commit -m "tournament $RUN results" || exit 0

for i in 1 2 3; do
  git push origin main && { echo "   pushed"; exit 0; }
  # Rejected => someone pushed from elsewhere. Fast-forward is impossible with a
  # local commit, and rebasing would fail on the agents' dirty tree, so leave the
  # commit local rather than touching their work; the next run pushes it.
  git fetch --quiet origin || true
  git merge --ff-only origin/main 2>/dev/null || {
    echo "!! branch diverged from origin; results committed locally but NOT pushed"; exit 0; }
done

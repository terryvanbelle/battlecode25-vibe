#!/usr/bin/env bash
# Commit paths under agents/carol/ without ever writing the SHARED .git/index.
#
# Why this exists. `git commit --only <paths>` is the project rule, and it works -- but only
# for paths git already tracks. A NEW file cannot be named to --only ("did not match any
# files known to git"), and the obvious fix, `git add`, publishes into an index all three
# agents share; a sibling's commit in that window takes your files with it. That has
# happened once already, for 1,716 lines.
#
# Instead: build a PRIVATE index seeded from HEAD, add there, and commit from it. The commit
# tree is then HEAD + exactly my paths, so no sibling's working-tree changes can be swept in,
# and .git/index is never opened for writing.
#
# The one wrinkle, which cost a scare the first time: after the commit, HEAD has moved but
# the shared index still holds the OLD blobs for those paths, so `git status` shows them
# STAGED IN REVERSE -- a sibling committing from the index would revert this commit. So the
# last step re-syncs the shared index for those paths only, with `git reset -q HEAD -- <paths>`.
# Path-scoped, so a sibling's genuinely staged work is untouched.
#
#   carol-tools/commit.sh -m "message" <path> [path...]     (paths relative to repo root)
set -euo pipefail
REPO=/home/terryvanbelle/projects/vibe/2025
[ "${1:-}" = "-m" ] || { echo "usage: $0 -m <message> <path>..." >&2; exit 1; }
MSG="$2"; shift 2
for p in "$@"; do case "$p" in agents/carol/*) ;; *) echo "refusing path outside agents/carol/: $p" >&2; exit 1;; esac; done
IDX="$(mktemp -t carol-idx.XXXXXX)"; trap 'rm -f "$IDX"' EXIT
cd "$REPO"
GIT_INDEX_FILE="$IDX" git read-tree HEAD
GIT_INDEX_FILE="$IDX" git add -- "$@"
GIT_INDEX_FILE="$IDX" git commit -q -m "$MSG"
git reset -q HEAD -- "$@"
git log --oneline -1

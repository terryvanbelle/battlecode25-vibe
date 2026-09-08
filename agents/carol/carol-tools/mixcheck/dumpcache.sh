#!/usr/bin/env bash
# Cache a full replay dump on disk, keyed by replay path + flags.
#
# Why: a remote replay-dump costs ~30s of shared-VM time and my first sweep threw
# away 95% of each dump to keep three counters. Every later question about the same
# game then pays the VM again. Dump once, keep the text, parse it as many times as
# the analysis needs.
#
#   dumpcache.sh <replay.bc25> [flags...]   -> prints path to the cached dump
set -euo pipefail
REPO=/home/terryvanbelle/projects/vibe/2025
CACHE="${DUMPCACHE:-$REPO/agents/carol/gauntlet/.dumpcache}"
mkdir -p "$CACHE"
R="$1"; shift
# Key on the replay's CONTENT, not its path. vm-match.sh writes every rerun of the same
# pairing+map to the SAME filename, so a path-keyed cache silently served a stale dump for a
# freshly rebuilt bot -- the cached file was three minutes OLDER than the replay it claimed to
# describe, and the two runs produced byte-identical numbers for two different builds. That is
# a wrong-verdict bug, not a slow one.
KEY=$(printf '%s|%s' "$(sha1sum < "$R" | cut -d' ' -f1)" "$*" | sha1sum | cut -c1-16)
OUT="$CACHE/$KEY.txt"
if [ ! -s "$OUT" ]; then
    "$REPO/tools/replay-dump.sh" "$R" "$@" > "$OUT.tmp" 2>/dev/null && mv "$OUT.tmp" "$OUT"
fi
echo "$OUT"

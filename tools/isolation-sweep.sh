#!/usr/bin/env bash
# Close the sibling-transcript leak in the coordinator's scratchpad.
#
# THE LEAK. All three agents run as subagents of the one coordinator session,
# so they share that session's task directory:
#
#   /tmp/claude-*/<project>/<session-uuid>/tasks/
#
# It holds two unrelated things:
#   b*.output  regular files -- output of an agent's own background BASH jobs.
#              Small, legitimate, and the only reason an agent goes there.
#   a*.output  SYMLINKS to full subagent JSONL transcripts -- one per agent
#              session, siblings included.
#
# The path is keyed to the session UUID, so nothing about it looks shared, and
# an agent globbing the directory for its own job output sweeps up its
# siblings' entire reasoning. Alice hit exactly this: a wildcard grep for
# MatchHeader pulled a fragment of another lineage's replay dump into her
# context, revealing that lineage fields a splasher -- a direction she has open
# and unpriced. She stopped and disclosed it rather than using it.
#
# MULTI_AGENT.md's isolation rule is absolute ("not code, not snapshots, not
# logs"), and these are logs. Isolation is what makes the tournament a
# measurement instead of three bots converging on each other, so the rule
# needs a mechanism and not just a paragraph.
#
# WHAT THIS REMOVES. Only the a*.output symlinks, and only the symlink -- never
# the transcript it points at, which stays in ~/.claude and is the coordinator's
# own record. Removing them costs nothing: an agent never spawns subagents, and
# the coordinator reads agent results from completion notifications, not from
# these files (the Agent tool explicitly warns against reading them).
#
# It is a sweep and not a one-shot because the harness recreates the symlink
# every time an agent is launched, and agents are relaunched constantly.
set -uo pipefail

SCRATCH_GLOB="/tmp/claude-*/-home-terryvanbelle-projects-vibe-2025/*/tasks"
removed=0

for tdir in $SCRATCH_GLOB; do
    [ -d "$tdir" ] || continue
    for f in "$tdir"/a*.output; do
        # -L: symlinks only. A regular a*.output would be somebody's real job
        # output and is none of this script's business.
        [ -L "$f" ] || continue
        rm -f "$f" && removed=$(( removed + 1 ))
    done
done

[ "$removed" -gt 0 ] && echo "$(date -u +%FT%TZ) isolation-sweep: removed $removed sibling transcript symlink(s)"
exit 0

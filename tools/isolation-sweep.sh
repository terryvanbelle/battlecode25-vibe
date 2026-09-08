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

# --- the scratchpad ROOT is the second, worse channel -------------------------
# tasks/ leaks transcripts; the scratchpad root leaks REPLAYS. A .bc25 is a
# complete game record, so one opened by the wrong lineage exposes the other's
# composition and build order in full -- and the filenames advertise ownership
# (t_alice-vs-bob-on-Gears.bc25, carol_rush__Leaf__botA.bc25). 100 of them were
# sitting in one shared directory when this was found, by the lineage that
# globbed the root looking for its own dumps and got nine of somebody else's.
#
# Unlike the transcript symlinks these are agents' working files, so they are
# QUARANTINED, not deleted: moved out of the shared tree into a coordinator-only
# directory. Nothing is destroyed, the leak is closed, and the engine is
# deterministic so a lineage that wants one back can re-dump it.
#
# Two hours of grace, so a dump being actively analysed is never pulled from
# under the analysis. Agents are told to work under <scratchpad>/<name>/, which
# this never touches -- following the rule makes you immune to the sweep.
QUARANTINE="$HOME/.bc25-scratchpad-quarantine"
quarantined=0
for sp in /tmp/claude-*/-home-terryvanbelle-projects-vibe-2025/*/scratchpad; do
    [ -d "$sp" ] || continue
    mkdir -p "$QUARANTINE"
    while IFS= read -r f; do
        [ -n "$f" ] || continue
        mv -f "$f" "$QUARANTINE/" 2>/dev/null && quarantined=$(( quarantined + 1 ))
    done < <(find "$sp" -maxdepth 1 -type f -name '*.bc25' -mmin +120 2>/dev/null)
done

[ "$removed" -gt 0 ] && echo "$(date -u +%FT%TZ) isolation-sweep: removed $removed sibling transcript symlink(s)"
[ "$quarantined" -gt 0 ] && echo "$(date -u +%FT%TZ) isolation-sweep: quarantined $quarantined root-level replay blob(s) from the shared scratchpad"
exit 0

#!/usr/bin/env bash
# Reclaim disk on the DRIVER by deleting old gauntlet replay blobs.
#
# The companion to tools/vm-prune.sh, which does the same job on
# battlecode-dev. The driver filled up because every collated gauntlet run
# copies its .bc25 replays back here, and nothing ever removed them: 1458
# replays across three workspaces, 3.2G, against a 30G root shared with a live
# BC26 project.
#
# What it deletes: ONLY *.bc25 files, ONLY under agents/*/gauntlet/<run>/, and
# only in runs outside the newest KEEP_RUNS for that agent.
#
# What it never touches: results.txt, results.csv, maps.txt, bot.txt, losses/
# and every other text artifact. Those are the EVIDENCE -- an agent's verdicts,
# its map lists, its per-game outcomes. They are a few kB per run and they are
# what the training loop actually reasons over, so they are kept for every run
# ever made, forever. A replay is a re-derivable detail; a result is not.
#
# It also never touches anything outside $REPO/agents, so the BC26 project and
# everything else on this box are structurally out of reach.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Newest N gauntlet runs per agent keep their replays. Four, not six: the
# retained set IS the steady state, since all the growth happens inside the
# protected window, and three busy agents at six runs each settle around 2.5G on
# a 30G root already carrying an 18G sibling project. Four keeps a couple of
# days of traceable runs and cuts the floor by a third. Results are kept forever
# either way, so this only ever costs re-runnable detail.
KEEP_RUNS="${KEEP_RUNS:-4}"
MIN_AGE_MIN="${MIN_AGE_MIN:-60}" # never touch a file written in the last hour

DRY=0
[[ "${1:-}" == "--dry-run" || "${1:-}" == "-n" ]] && DRY=1

# Refuse to run anywhere that isn't the repo we expect. A prune script that
# guesses its root is one bad symlink away from deleting the wrong tree.
[[ -d "$REPO/agents" && -f "$REPO/MULTI_AGENT.md" ]] || {
    echo "!! $REPO does not look like the bc25 repo -- refusing to prune" >&2
    exit 1
}

total=0
for ws in "$REPO"/agents/*/; do
    agent="$(basename "$ws")"
    gdir="$ws/gauntlet"
    [[ -d "$gdir" ]] || continue

    # Newest KEEP_RUNS by run-id. Run-ids are YYYYMMDD-HHMMSS, so a reverse
    # lexical sort IS a reverse chronological sort -- no mtime involved, which
    # matters because collation rewrites mtimes long after a run really ran.
    mapfile -t keep < <(ls -1 "$gdir" 2>/dev/null | sort -r | head -n "$KEEP_RUNS")

    for run in "$gdir"/*/; do
        rid="$(basename "$run")"
        skip=0
        for k in "${keep[@]}"; do [[ "$rid" == "$k" ]] && skip=1; done
        (( skip )) && continue

        # -mmin guards a run that is somehow still being written despite being
        # outside the newest N (a resumed collation, a clock skew).
        bytes=$(find "$run" -type f -name '*.bc25' -mmin "+$MIN_AGE_MIN" \
                     -printf '%s\n' 2>/dev/null | awk '{s+=$1} END{print s+0}')
        (( bytes )) || continue
        n=$(find "$run" -type f -name '*.bc25' -mmin "+$MIN_AGE_MIN" 2>/dev/null | wc -l)

        printf '%s %s/%s: %d replays, %s\n' \
               "$( ((DRY)) && echo would-prune || echo prune )" \
               "$agent" "$rid" "$n" "$(numfmt --to=iec "$bytes")"
        if (( ! DRY )); then
            find "$run" -type f -name '*.bc25' -mmin "+$MIN_AGE_MIN" -delete
            # Leave a tombstone. losses/ holds the replays an agent saved to
            # study its own defeats, so finding it empty with no explanation
            # reads as a broken run or a collation bug -- and an agent told to
            # "re-examine the old games" would burn a session chasing it.
            cat > "$run/PRUNED.txt" <<TOMB
Replays pruned $(date -u +%Y-%m-%dT%H:%M:%SZ) by tools/driver-prune.sh
to reclaim disk on the driver ($n files, $(numfmt --to=iec "$bytes")).

The RESULTS ARE INTACT: results.csv, results.txt, maps.txt, bot.txt and
reasons.txt are untouched, so every verdict this run supports still stands.
Only the .bc25 replay blobs are gone, including those under losses/.

To watch these games again, re-run the matchup -- the engine is deterministic,
so the same bots on the same map reproduce the same game exactly.
TOMB
        fi
        total=$(( total + bytes ))
    done
done

printf '%s total: %s\n' "$( ((DRY)) && echo would-reclaim || echo reclaimed )" \
       "$(numfmt --to=iec "$total")"

#!/usr/bin/env bash
# Keep battlecode-dev's disk from filling with old replays.
#
# WHY THIS IS NOT LEFT TO THE AGENTS
# ----------------------------------
# AGENT.md tells each agent to prune its own gauntlet output, and on
# 2026-09-07 the VM still reached 20G/20G with ZERO free -- which broke a replay
# upload and would have broken tournament staging for all three lineages a few
# hours later. An instruction that everyone is supposed to follow, that fails
# silently and hurts everyone else when one lineage forgets, belongs in
# infrastructure instead. The agent that noticed had 3.2G of its own; the
# largest holder at the time had 2.7G across 34 runs.
#
# WHAT IT WILL NOT DELETE
#   * anything outside ~/battlecode25-vibe (the BC26 project is not ours)
#   * any run modified within GRACE_H hours -- an in-flight run is never touched
#   * the newest KEEP runs of each workspace, in-flight or not
#   * tournament runs beyond the newest KEEP_T: their replays are the sanctioned
#     cross-agent evidence channel, so they are kept longer than gauntlets
#
# DRY_RUN=1 prints what it would remove and removes nothing.
set -uo pipefail

VM=battlecode-dev
ZONE=us-west1-b
PROJECT=tvanbelle-vibecode
KEEP="${KEEP:-6}"          # newest gauntlet runs kept per workspace
KEEP_T="${KEEP_T:-4}"      # newest tournaments kept (replays = shared evidence)
GRACE_H="${GRACE_H:-6}"    # never touch anything this recently modified
LOW_GB="${LOW_GB:-4}"      # below this much free, prune harder
DRY_RUN="${DRY_RUN:-0}"

IP=$(gcloud compute instances describe "$VM" --zone="$ZONE" --project="$PROJECT" \
       --format='value(networkInterfaces[0].accessConfigs[0].natIP)' 2>/dev/null)
[ -n "$IP" ] || { echo "!! cannot resolve $VM"; exit 1; }

ssh -i "$HOME/.ssh/google_compute_engine" -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null -o ConnectTimeout=20 -o LogLevel=ERROR \
    "$(whoami)@$IP" "KEEP=$KEEP KEEP_T=$KEEP_T GRACE_H=$GRACE_H LOW_GB=$LOW_GB DRY_RUN=$DRY_RUN bash -s" <<'REMOTE'
set -uo pipefail
R=$HOME/battlecode25-vibe
free_gb () { df -BG --output=avail / | tail -1 | tr -dc '0-9'; }
before=$(free_gb)
echo "$(date -u +%FT%TZ) prune: ${before}G free before (keep=$KEEP tourn=$KEEP_T grace=${GRACE_H}h)"

# Under real pressure, keep less -- but never fewer than 3.
if [ "$before" -lt "$LOW_GB" ]; then
  KEEP=3; KEEP_T=2
  echo "  !! under ${LOW_GB}G free -- pruning harder (keep=$KEEP tourn=$KEEP_T)"
fi

prune_dir () {   # <parent-of-run-dirs> <how-many-to-keep> <label>
  local parent="$1" keep="$2" label="$3" n=0
  [ -d "$parent" ] || return 0
  # Newest first; skip the first `keep`, then skip anything still warm.
  for d in $(ls -1dt "$parent"/*/ 2>/dev/null); do
    n=$((n+1))
    [ "$n" -le "$keep" ] && continue
    if [ -n "$(find "$d" -maxdepth 1 -newermt "-${GRACE_H} hours" -print -quit 2>/dev/null)" ]; then
      echo "  keep  $label/$(basename $d)  (modified within ${GRACE_H}h)"
      continue
    fi
    local sz; sz=$(du -sh "$d" 2>/dev/null | cut -f1)
    if [ "$DRY_RUN" = 1 ]; then
      echo "  WOULD remove $label/$(basename $d)  ($sz)"
    else
      rm -rf "$d" && echo "  removed $label/$(basename $d)  ($sz)"
    fi
  done
}

for a in alice bob carol; do prune_dir "$R/agents/$a/gauntlet" "$KEEP" "$a"; done
prune_dir "$R/arena/tournaments" "$KEEP_T" "tournaments"

after=$(free_gb)
echo "$(date -u +%FT%TZ) prune: ${after}G free after (+$((after-before))G)"
REMOTE

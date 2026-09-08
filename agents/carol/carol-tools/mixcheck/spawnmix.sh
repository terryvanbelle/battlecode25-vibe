#!/usr/bin/env bash
# Paired realized-build-mix counter for a gauntlet run's loss replays.
#
# Both bots of a head-to-head appear in the SAME replay, so this compares the
# candidate's realized soldier/mopper/splasher build mix against the incumbent's
# on the same map, in the same game -- a paired comparison, immune to map-sample
# differences. It is a direct count of SPAWN events (ReplayDump's +sold/+mop/+spl
# per-interval deltas, summed), not a rate reconstructed from post-turn state,
# so the AFTER-turn recording bias documented in engine-facts.md does not touch it.
#
#   spawnmix.sh <replay.bc25>   -> "<team1name> s m p | <team2name> s m p | twPaint1 twPaint2"
set -euo pipefail
REPO=/home/terryvanbelle/projects/vibe/2025
R="$1"
"$REPO/tools/replay-dump.sh" "$R" --every 200 2>/dev/null | awk '
/^=== GameHeader/ { for(i=1;i<=NF;i++){ if($i ~ /^team1=/){sub(/^team1=/,"",$i); n1=$i} if($i ~ /^team2=/){sub(/^team2=/,"",$i); n2=$i} } }
/\| T[12] /  {
  # split the aggregate line on "| " and parse each team block
  n=split($0, parts, /\| /)
  for(k=2;k<=n;k++){
    m=split(parts[k], f, /[ ]+/)
    tid=substr(f[1],2)+0
    for(j=1;j<=m;j++){
      if(f[j] ~ /^\+sold/){ v=f[j]; sub(/^\+sold/,"",v); S[tid]+=v }
      if(f[j] ~ /^\+mop/){  v=f[j]; sub(/^\+mop/,"",v);  M[tid]+=v }
      if(f[j] ~ /^\+spl/){  v=f[j]; sub(/^\+spl/,"",v);  P[tid]+=v }
      if(f[j] ~ /^twPaint/){ v=f[j]; sub(/^twPaint/,"",v); TP[tid]=v; TPn[tid]++ ; TPs[tid]+=v }
    }
  }
}
END { printf "%s %d %d %d %s %d %d %d %d %d\n", n1, S[1], M[1], P[1], n2, S[2], M[2], P[2], (TPn[1]?TPs[1]/TPn[1]:0), (TPn[2]?TPs[2]/TPn[2]:0) }'

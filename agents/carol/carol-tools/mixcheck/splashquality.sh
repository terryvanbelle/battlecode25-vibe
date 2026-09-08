#!/usr/bin/env bash
# Iteration 39's weak-link check: are the EXTRA splasher shots bought at a worse price?
#
# Counting shots is not enough. A shot fires at bestScore >= SPLASH_MIN_SCORE = 8, which is
# roughly 4 empty tiles for 50 paint (12.5 paint/tile) against a best case near 3.8. Steering
# toward the NEAREST empty tile is not steering toward the DENSEST, so a candidate can raise
# the shot count purely by buying more shots at the worst price the threshold allows -- which
# would look like success in every aggregate counter.
#
# So this reports the s= score distribution AT THE MOMENT OF FIRING, per team, plus the
# turn-state split and the sf/sn conditional reachability counter.
#
#   splashquality.sh <replay.bc25> <from> <to>
set -uo pipefail   # NOT -e: a team with no splashers, or a build without sf=/sn=, makes a
                  # grep exit 1 and that is a normal empty result, not a failure.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
D=$("$HERE/dumpcache.sh" "$1" --quiet --from "$2" --to "$3")
head -1 "$D"
for T in T1 T2; do
  echo "--- $T ---"
  grep 'IND' "$D" | grep "($T,SPLASHER)" | grep -o '| P[^"]*' | awk '
    {n++; if(/SPLASH/)s++; else if(/noPaint/)p++; else if(/ cd/)c++; else if(/lowScore/)l++; else if(/noTgt/)t++}
    END{if(n) printf "  turns=%d  fired=%.1f%%  cd=%.1f%%  noPaint=%.1f%%  targetless=%.1f%%\n",
        n,100*s/n,100*c/n,100*p/n,100*(l+t)/n}'
  # NOTE: filter the extracted state fragment, never the whole line -- the robot label
  # "(T1,SPLASHER)" contains the substring "SPLASH", so grepping the line matches every turn
  # and silently reports the whole population as if it had fired. Cost one wrong table.
  grep 'IND' "$D" | grep "($T,SPLASHER)" | grep -o '| P[^"]*' | grep ' SPLASH ' | grep -o 's=[0-9]*' | cut -d= -f2 | sort -n | awk '
    {v[n++]=$1; sum+=$1}
    END{if(n) printf "  FIRING shots=%d  mean score=%.1f  median=%d  p90=%d  max=%d\n",
        n,sum/n,v[int(n/2)],v[int(.9*n)],v[n-1]; else print "  FIRING shots=0"}'
  grep 'IND' "$D" | grep "($T,SPLASHER)" | grep -o 'sf=[0-9]* sn=[0-9]*' | tail -1 | awk -F'[= ]' '
    {if($2+$4>0) printf "  steer reachability: sf=%d sn=%d found=%.1f%%\n",$2,$4,100*$2/($2+$4)}'
done

#!/usr/bin/env bash
# Score one of carol's gauntlet runs against the standing checklist.
#
#   tools/eval-run.sh <run-id> [gate-opponent]
#
# Prints, in order: completeness, per-opponent win rate with the binomial noise floor,
# swept-map shape, side split (symmetry audit), exception count, the bytecode check, and the
# frozen-treasury gate. Everything the algorithm says to check every evaluation, so that none
# of it quietly stops being checked -- which is exactly how the dead band survived four
# iterations after being diagnosed.
set -uo pipefail
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$WS/../../tools/.venv/bin/python3"
RUN="${1:?usage: eval-run.sh <run-id> [gate-opponent]}"
GATE_OPP="${2:-}"
D="$WS/gauntlet/$RUN"
[ -d "$D" ] || { echo "no such run: $D" >&2; exit 1; }

echo "=== run $RUN ==="
if grep -q GAUNTLET-COMPLETE "$D/results.txt" 2>/dev/null; then echo "status: COMPLETE"
else echo "status: !! INCOMPLETE -- do not score a prefix (see LEARNINGS)"; fi

echo
echo "--- win rates (+-1sd binomial noise floor at p=0.5) ---"
awk '$1=="RESULT"{n[$2]++; if($5==$4) w[$2]++}
     END{for(o in n){sd=sqrt(n[o]*0.25);
       printf "  %-22s %3d/%-3d = %5.1f%%   1sd = %.1f games (%.1f pts)\n",
              o, w[o], n[o], 100*w[o]/n[o], sd, 100*sd/n[o]}}' "$D/results.txt" | sort

echo
echo "--- swept maps (immune to spawn advantage) ---"
awk '$1=="RESULT"{k=$2" "$3; r=($5==$4?1:0); s[k]+=r; c[k]++}
     END{for(k in c) if(c[k]==2){split(k,a," ");
       t=(s[k]==2?"swept-win":(s[k]==0?"swept-LOSS":"split"));
       n[a[1]" "t]++}
     for(x in n){split(x,b," "); printf "  %-22s %-10s %d\n", b[1], b[2], n[x]}}' "$D/results.txt" | sort

echo
echo "--- side split (play-symmetry audit) ---"
awk '$1=="RESULT"{k=$2" "$4; c[k]++; if($5==$4) w[k]++}
     END{for(k in c) printf "  %-26s %2d/%-2d\n", k, w[k], c[k]}' "$D/results.txt" | sort

echo
echo "--- exceptions (must be 0) ---"
awk '$1=="EXC"{t+=$5} END{printf "  total thrown: %d\n", t+0}' "$D/results.txt"

echo
echo "--- bytecode check (must be 0 overruns / 0 near-misses) ---"
LOSS=$(ls "$D"/losses/*.bc25 2>/dev/null | head -1)
if [ -n "$LOSS" ]; then
  "$PY" "$WS/tools/replay-strings.py" "$LOSS" 2>/dev/null \
    | grep -o 'bc=[0-9]*/[0-9]* max=[0-9]* ov=[0-9]* nm=[0-9]*' \
    | "$PY" -c "
import sys,re
mx={};ov=nm=0
for l in sys.stdin:
    m=re.search(r'bc=(\d+)/(\d+) max=(\d+) ov=(\d+) nm=(\d+)',l)
    if m:
        u,lim,mm,o,n=(int(x) for x in m.groups())
        mx[lim]=max(mx.get(lim,0),mm); ov=max(ov,o); nm=max(nm,n)
for lim,v in sorted(mx.items()):
    print(f'  {\"robot\" if lim==17500 else \"tower\"}: peak {v}/{lim} = {100*v/lim:.1f}%')
print(f'  overruns={ov}  near-misses={nm}')"
else echo "  (no loss replays)"; fi

echo
echo "--- frozen-treasury gate (iteration 7 mechanism) ---"
if ls "$D"/losses/*.bc25 >/dev/null 2>&1; then
  "$PY" "$WS/tools/frozen-treasury.py" --gate 50 "$D"/losses/*.bc25 | tail -4
else echo "  (no loss replays -- nothing to check)"; fi

echo
echo "--- paint-drought gate (no-paint-tower absorbing state, RULES.md hard loss) ---"
if ls "$D"/losses/*.bc25 >/dev/null 2>&1; then
  "$PY" "$WS/tools/paint-drought.py" --gate 200 "$D"/losses/*.bc25 | tail -3
else echo "  (no loss replays -- nothing to check)"; fi

if [ -n "$GATE_OPP" ]; then
  echo
  echo "--- ACCEPT GATE vs $GATE_OPP ---"
  awk -v o="$GATE_OPP" '$1=="RESULT" && $2==o{n++; if($5==$4) w++}
       END{if(n==0){print "  no games"; exit}
           p=100*w/n; printf "  %d/%d = %.1f%%  -> %s\n", w,n,p,
             (p>50?"ACCEPT (>50%)":(p>=45?"NEAR MISS (45-50%)":"REJECT (<45%)"))}' "$D/results.txt"
fi

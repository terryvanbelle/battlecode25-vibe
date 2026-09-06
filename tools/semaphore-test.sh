#!/usr/bin/env bash
# Reproduces the HARD_CAP check-then-take race that the acquire_slot gate in
# gauntlet.sh / tournament.sh exists to close, using the same lock structure
# with fake games. GATED=0 is the old logic, GATED=1 the current one.
#
#   GATED=0 tools/semaphore-test.sh   -> peak 8 vs HARD_CAP 7  (BREACHED)
#   GATED=1 tools/semaphore-test.sh   -> peak 7                (ok)
#
# Run this after touching acquire_slot. Note what it does NOT show: it found no
# starvation in the old logic under several timings, so the "incumbents crowd
# out a newly launched run" theory is unsupported -- a fresh run making no
# progress is more likely just a saturated machine.
GATED=${GATED:-1}
D=$(mktemp -d); GLOBAL_CAP=5; HARD_CAP=7; EXTERNAL=3
LOG=$D/log; : > "$LOG"; : > "$D/running"
# stands in for `pgrep -fc battlecode.server.Main`: BC25 games + BC26's
count () { echo $(( $(wc -l < "$D/running") + EXTERNAL )); }
acquire_slot () {
  if [ "$GATED" = 1 ]; then exec {GFD}>"$D/gate"; flock $GFD; fi
  while [ "$(count)" -ge "$HARD_CAP" ]; do sleep 0.05; done
  while true; do
    for i in $(seq 1 $GLOBAL_CAP); do
      exec {SFD}>"$D/slot.$i"
      if flock -n $SFD; then [ "$GATED" = 1 ] && exec {GFD}>&-; return 0; fi
      exec {SFD}>&-
    done
    sleep 0.05
  done
}
play () {
  acquire_slot
  exec {L}>"$D/lk"; flock $L; echo x >> "$D/running"; echo IN >> "$LOG"; exec {L}>&-
  sleep 0.5
  exec {L}>"$D/lk"; flock $L; sed -i '$d' "$D/running"; echo OUT >> "$LOG"; exec {L}>&-
}
for w in 1 2 3; do ( for g in $(seq 1 12); do
    ( play ) & while [ "$(jobs -rp|wc -l)" -ge 3 ]; do wait -n; done
  done; wait ) & done
wait
awk -v e=$EXTERNAL -v h=$HARD_CAP '/^IN/{c++; if(c>m)m=c} /^OUT/{c--}
  END{printf "peak BC25 %d + external %d = %d  (HARD_CAP %d) -> %s\n",
      m, e, m+e, h, (m+e>h) ? "BREACHED" : "ok"}' "$LOG"
rm -rf "$D"

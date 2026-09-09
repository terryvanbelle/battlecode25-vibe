#!/usr/bin/env bash
# Early-game PAINT-FLOW census over a directory of replays ON battlecode-dev.
#
# WHY (iteration 41): LEARNING 69 established that bob's r30 coverage
# differential is -65 per-mille on small maps while bob fields 4x carol's
# soldiers. That is a statement about the OUTCOME (coverage). This tool reads
# the INPUT side -- how many paint actions each team actually took, how many
# units starved, how much tower paint was left -- so "bob paints too slowly"
# can be separated from "bob paints plenty and it does not become coverage".
#
# Emits raw `round N | T1 ... | T2 ...` lines (N <= LIMIT) prefixed with the
# replay basename; parse with early_paint_agg.py. Deliberately dumb: all
# interpretation happens locally where it can be re-run without the VM.
#
# Reuses tools/replaydump/ReplayDump.java verbatim (NOT a fork).
#
#   bob-tools/early-paint-census.sh <remote-replay-dir> <name-filter> [limit-round] [stride]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
source "$REPO/tools/lib.sh"
RDIR="$1"; FILT="${2:-bob}"; LIMIT="${3:-30}"; STRIDE="${4:-10}"
WANT_VER="$(cat "$REPO/arena/engine_version.txt")"
ensure_vm
RUN="bobpaint-$$"
gssh "mkdir -p ~/$RUN" >/dev/null
trap 'gssh "rm -rf ~/'"$RUN"'" >/dev/null 2>&1 || true' EXIT
gscp "$REPO/tools/replaydump/ReplayDump.java" "$USER_NAME@$IP:$RUN/" >/dev/null
gssh "
  export PATH=\$HOME/jdk21/bin:\$PATH
  BC_JAR=\$(find ~/.gradle -name 'battlecode25-java-$WANT_VER.jar' | grep -v source | head -1)
  [ -n \"\$BC_JAR\" ] || { echo '!! no pinned engine jar' >&2; exit 1; }
  cd ~/$RUN
  javac -d . -classpath \"\$BC_JAR\" ReplayDump.java 2>&1 | head -3
  n=0
  for f in $RDIR/*$FILT*.bc25; do
    [ -e \"\$f\" ] || continue
    n=\$((n+1))
    b=\$(basename \"\$f\")
    java -classpath \".:\$BC_JAR\" com.google.flatbuffers.ReplayDump \"\$f\" --every $STRIDE 2>/dev/null |
      awk -v F=\"\$b\" -v L=$LIMIT '
        /^=== GameHeader/ { print F \"\\tHDR\\t\" \$0 }
        /^round / { split(\$2,a,\" \"); if (\$2+0 <= L) print F \"\\tRND\\t\" \$0 }
        /^=== MatchFooter/ { print F \"\\tFTR\\t\" \$0 }'
  done
  if [ \"\$n\" -eq 0 ]; then echo '!! MATCHED ZERO REPLAYS -- filter or dir wrong' >&2; exit 3; fi
  echo \"# censused \$n replays\" >&2
"

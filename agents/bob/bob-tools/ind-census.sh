#!/usr/bin/env bash
# Batch INDICATOR-STRING dump over a directory of replays ON battlecode-dev.
#
# WHY: tools/replay-dump.sh copies and compiles ReplayDump per replay (~40s each),
# which is right for one game and far too slow for two dozen. This compiles once
# on the VM and loops there.
#
# ReplayDump prints IndicatorStringAction ONLY inside --from/--to, and its default
# window admits nothing -- a consumer that forgets the window reads a silent zero
# (LEARNING 70). So the window is a REQUIRED argument here, not a default, and the
# script fails loudly if it matched no replays or parsed no IND lines.
#
#   bob-tools/ind-census.sh <remote-replay-dir> <name-filter> <from> <to>
#
# Emits: <replay-basename> TAB <the raw IND line>
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
source "$REPO/tools/lib.sh"

[ "$#" -eq 4 ] || { echo "usage: $0 <remote-replay-dir> <name-filter> <from> <to>" >&2; exit 1; }
RDIR="$1"; FILT="$2"; FROM="$3"; TO="$4"
WANT_VER="$(cat "$REPO/arena/engine_version.txt")"
ensure_vm
RUN="bobind-$$"
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
  : > out.tsv
  for f in $RDIR/*$FILT*.bc25; do
    [ -e \"\$f\" ] || continue
    n=\$((n+1)); b=\$(basename \"\$f\")
    java -classpath \".:\$BC_JAR\" com.google.flatbuffers.ReplayDump \"\$f\" \
          --quiet --from $FROM --to $TO 2>/dev/null |
        awk -v F=\"\$b\" '/ IND \"/ { print F \"\\t\" \$0 }' >> out.tsv
  done
  lines=\$(wc -l < out.tsv)
  cat out.tsv
  if [ \"\$n\" -eq 0 ]; then echo '!! MATCHED ZERO REPLAYS -- filter or dir wrong' >&2; exit 3; fi
  if [ \"\$lines\" -eq 0 ]; then echo \"!! \$n replays but ZERO IND lines parsed -- window $FROM-$TO may be empty, or the bot writes no indicator string\" >&2; exit 4; fi
  echo \"# censused \$n replays, \$lines IND lines\" >&2
"

#!/usr/bin/env bash
# ITERATION 46. Classify every PAINT action as NEW / FLIP / REDUNDANT.
#
# ISOLATION (see RULES.md, 2026-09-09): the detailed action log prints IND lines
# for BOTH teams, and another lineage's indicator string is private debug output,
# not "what the opponent does". This script DROPS every IND line at the source --
# before anything local ever sees it -- so no filtering decision is left to a
# future reader. Nothing downstream can read what was never transmitted.
#
#   redundancy-census.sh <abs-remote-replay-dir> <name-filter> [limit-round]
#
# NOTE the ABSOLUTE path: the remote shell cds into its own temp dir first, so a
# relative replay dir silently matches nothing (that trap cost this session two runs).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
source "$REPO/tools/lib.sh"
RDIR="$1"; FILT="${2:-bob}"; LIMIT="${3:-200}"
WANT_VER="$(cat "$REPO/arena/engine_version.txt")"
ensure_vm
RUN="bobredund-$$"
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
    n=\$((n+1)); b=\$(basename \"\$f\")
    java -classpath \".:\$BC_JAR\" com.google.flatbuffers.ReplayDump \"\$f\" --from 1 --to $LIMIT --quiet 2>/dev/null |
      grep -v ' IND ' |
      awk -v F=\"\$b\" '
        /^=== GameHeader/ { print F \"\\tHDR\\t\" \$0; next }
        / PAINT | UNPAINT | SPLASH / { print F \"\\tACT\\t\" \$0 }'
  done
  if [ \"\$n\" -eq 0 ]; then echo '!! MATCHED ZERO REPLAYS' >&2; exit 3; fi
  echo \"# censused \$n replays\" >&2
"

#!/usr/bin/env bash
# Bob's denial-utilisation probe. Runs bob-tools/denialprobe/DenialProbe.java
# (a private fork of the shared tools/replaydump/ReplayDump.java -- the shared
# tool is coordinator-owned and is NOT modified) on battlecode-dev.
#
#   bob-tools/denial-probe.sh <replay.bc25> [replay.bc25 ...]
#
# Compiles once and runs every replay, printing one report per file prefixed
# with "## <name>", so a batch can be aggregated by bob-tools/denial_agg.py.
#
# Uses tools/engine-jar.sh --remote for the jar rather than a bare `find`: the
# gradle cache holds a stale battlecode25-java-1.0.0.jar beside the real 3.1.0.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
source "$ROOT/tools/lib.sh"

[ "$#" -ge 1 ] || { echo "usage: $0 <replay.bc25> [more.bc25 ...]" >&2; exit 1; }
ensure_vm
JAR="$("$ROOT/tools/engine-jar.sh" --remote)"
RUN_DIR="bob-denialprobe/run-$$-$(date +%s%N)"
gssh "mkdir -p ~/$RUN_DIR/reps" >/dev/null
trap 'gssh "rm -rf ~/$RUN_DIR" >/dev/null 2>&1 || true' EXIT
gscp "$HERE/denialprobe/DenialProbe.java" "$USER_NAME@$IP:$RUN_DIR/" >/dev/null

i=0; names=""
for f in "$@"; do
  [ -f "$f" ] || { echo "no such file: $f" >&2; continue; }
  gscp "$f" "$USER_NAME@$IP:$RUN_DIR/reps/$i.bc25" >/dev/null
  names="$names $i:$(basename "$f")"
  i=$((i+1))
done

gssh "
  export JAVA_HOME=\$HOME/jdk21 PATH=\$HOME/jdk21/bin:\$PATH
  cd ~/$RUN_DIR
  javac -nowarn -d . -classpath '$JAR' DenialProbe.java 2>&1 | grep -v '^Note:' || true
  for n in \$(seq 0 $((i-1))); do
    echo \"## \$n\"
    java -classpath \".:$JAR\" com.google.flatbuffers.DenialProbe reps/\$n.bc25 --quiet \
      | sed -n '/=== DENIAL UTILISATION/,/^  READ/p; /=== MatchFooter/p'
  done
"
echo "# names:$names"

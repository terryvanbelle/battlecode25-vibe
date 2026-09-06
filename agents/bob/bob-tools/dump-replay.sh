#!/usr/bin/env bash
# Dump per-round metrics from a local .bc25 replay (runs BobDump on the VM).
# Usage: bob-tools/dump-replay.sh <local-replay.bc25> [sampleEvery]
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../../../tools/lib.sh"
REPLAY="$1"; EVERY="${2:-50}"
ensure_vm
JAR='$HOME/.gradle/caches/modules-2/files-2.1/org.battlecode/battlecode25-java/3.1.0/ed91f61dfa7c5d4afd9760ad4ef31ec8357e0167/battlecode25-java-3.1.0.jar'
# compile once (cached by .class timestamp)
gssh "mkdir -p ~/bob-tools" >/dev/null
gscp "$(dirname "${BASH_SOURCE[0]}")/BobDump.java" "$USER_NAME@$IP:bob-tools/" >/dev/null
gscp "$REPLAY" "$USER_NAME@$IP:bob-tools/_dump_input.bc25" >/dev/null
gssh "export JAVA_HOME=\$HOME/jdk21 PATH=\$HOME/jdk21/bin:\$PATH
  cd ~/bob-tools
  if [ BobDump.java -nt BobDump.class ]; then javac -cp $JAR BobDump.java; fi
  java -cp .:$JAR BobDump _dump_input.bc25 $EVERY"

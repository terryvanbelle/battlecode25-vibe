#!/usr/bin/env bash
# Usage: bob-tools/mop-trace.sh <local-replay.bc25> <A|B> [sampleEvery]
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../../../tools/lib.sh"
REPLAY="$1"; SIDE="$2"; EVERY="${3:-100}"
ensure_vm
JAR='$HOME/.gradle/caches/modules-2/files-2.1/org.battlecode/battlecode25-java/3.1.0/ed91f61dfa7c5d4afd9760ad4ef31ec8357e0167/battlecode25-java-3.1.0.jar'
gssh "mkdir -p ~/bob-tools" >/dev/null
gscp -q "$(dirname "${BASH_SOURCE[0]}")/BobMop.java" "$USER_NAME@$IP:bob-tools/" >/dev/null
gscp -q "$REPLAY" "$USER_NAME@$IP:bob-tools/_mop_input.bc25" >/dev/null
gssh "export JAVA_HOME=\$HOME/jdk21 PATH=\$HOME/jdk21/bin:\$PATH
  cd ~/bob-tools && javac -cp $JAR BobMop.java 2>&1 | head -20
  java -cp .:$JAR BobMop _mop_input.bc25 $SIDE $EVERY"

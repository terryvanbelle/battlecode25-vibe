#!/usr/bin/env bash
# Fast remote compile check for carol's src (no match, no gradle).
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../../../tools/lib.sh"
find_workspace
ensure_vm
gssh "mkdir -p ~/$REMOTE_REPO/$WS_REL/src" >/dev/null
gscp -r "$WS_DIR/src/." "$USER_NAME@$IP:$REMOTE_REPO/$WS_REL/src/" >/dev/null
JAR='$(find ~/.gradle -path "*battlecode25-java/3.1.0*" -name "*.jar" | grep -v sources | grep -v javadoc | head -1)'
gssh "cd ~/$REMOTE_REPO/$WS_REL && rm -rf /tmp/carol-cc && mkdir -p /tmp/carol-cc && ~/jdk21/bin/javac -cp $JAR -d /tmp/carol-cc \$(find src -name '*.java') && echo COMPILE-OK"

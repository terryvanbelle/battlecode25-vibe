#!/usr/bin/env bash
# Compile one of my bot packages IN ISOLATION on battlecode-dev, so a syntax
# error can never reach the tournament build. Usage: compile-check.sh <pkg>
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../../../tools/lib.sh"
PKG="${1:-bob}"
ensure_vm
JAR='$HOME/.gradle/caches/modules-2/files-2.1/org.battlecode/battlecode25-java/3.1.0/ed91f61dfa7c5d4afd9760ad4ef31ec8357e0167/battlecode25-java-3.1.0.jar'
D="bob-tools/compilecheck/$PKG"
gssh "rm -rf ~/$D && mkdir -p ~/$D" >/dev/null
gscp -q -r "$(dirname "${BASH_SOURCE[0]}")/../src/$PKG" "$USER_NAME@$IP:$D/" >/dev/null
gssh "export JAVA_HOME=\$HOME/jdk21 PATH=\$HOME/jdk21/bin:\$PATH
  cd ~/$D && javac -d out -cp $JAR \$(find $PKG -name '*.java')" \
  && echo "COMPILE OK: $PKG"

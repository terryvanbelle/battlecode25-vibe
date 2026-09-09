#!/usr/bin/env bash
# Generate iteration 37 arms from src/bob by substituting FRONTIER_MODE.
# Generator, not hand-copies: iteration 33 was voided by a hand-edit that also
# perturbed RNG ordering, so the arms differ in ONE constant by construction.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
for m in 0 1 2; do
  d=src/bob_t$m
  rm -rf "$d"; cp -r src/bob "$d"
  sed -i "s/^package bob;/package bob_t$m;/" "$d"/*.java
  sed -i "s/static final int FRONTIER_MODE = 0;/static final int FRONTIER_MODE = $m;/" "$d/Soldier.java"
  grep -q "FRONTIER_MODE = $m;" "$d/Soldier.java" || { echo "!! dose not applied for $m" >&2; exit 1; }
done
echo "arms built: bob_t0 (zero) bob_t1 (always) bob_t2 (only when fed)"

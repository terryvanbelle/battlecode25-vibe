#!/usr/bin/env bash
# Ablation A3: bob_iter9 with iteration 3's idle-chip tower self-upgrade REMOVED.
# Everything else is iteration 9 verbatim. Builds src/bob_abl3 (package bob_abl3).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
rm -rf src/bob_abl3
cp -r src/bob_iter9 src/bob_abl3
sed -i 's/^package bob_iter9;/package bob_abl3;/' src/bob_abl3/*.java
python3 - <<'PY'
import pathlib
p = pathlib.Path('src/bob_abl3/Tower.java')
s = p.read_text()
old = """        if (selfType.canUpgradeType()
                && chips >= selfType.getNextLevel().moneyCost + UPGRADE_RESERVE) {"""
new = """        // ABLATION A3: iteration 3's idle-chip self-upgrade gated off. The condition
        // is kept intact and simply never entered, so the surrounding control flow is
        // byte-for-byte the accepted iteration 9 apart from this one gate.
        if (false && selfType.canUpgradeType()
                && chips >= selfType.getNextLevel().moneyCost + UPGRADE_RESERVE) {"""
assert old in s, "iteration 3 upgrade gate not found"
p.write_text(s.replace(old, new))
print("A3: tower self-upgrade gated off")
PY
bob-tools/compile-check.sh bob_abl3

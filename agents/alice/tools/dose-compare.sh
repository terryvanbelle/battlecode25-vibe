#!/usr/bin/env bash
# Exact within-run comparison of two dose arms from one gauntlet.
# Both arms played the SAME map sample, so restricting to (map,side) cells that
# both arms actually played makes the comparison exact rather than sample-noisy.
# BOT is the zero arm, so "BOT lost" == "the dose won".
R="$1"; A="$2"; B="$3"
awk -v A="$A" -v B="$B" '
  $1=="RESULT" {
    key=$3"|"$4
    if ($2==A) { a[key] = ($4!=$5) ? 1 : 0 }
    if ($2==B) { b[key] = ($4!=$5) ? 1 : 0 }
  }
  END {
    for (k in a) if (k in b) {
      n++; aw += a[k]; bw += b[k]
      if (a[k] != b[k]) { split(k, p, "|"); d = d sprintf("    %-14s side %s : %s\n", p[1], p[2], (a[k] ? A" won, "B" lost" : B" won, "A" lost")) }
    }
    printf "  shared (map,side) cells played by BOTH arms: %d\n", n
    printf "  %-12s %2d/%d (%.1f%%)\n", A, aw, n, 100*aw/n
    printf "  %-12s %2d/%d (%.1f%%)\n", B, bw, n, 100*bw/n
    printf "  cells where the two arms disagree:\n%s", d
  }' "$R/results.txt"

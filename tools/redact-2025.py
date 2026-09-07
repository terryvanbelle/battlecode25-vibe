#!/usr/bin/env python3
"""Drop every blank-line-separated block that touches the 2025 contest year.

Filter BEFORE reading, not after: the point is that the coordinator never sees
2025 post-mortem content either. Block granularity, not line granularity,
because an attribution line ("SPAARK (2025) says:") is usually followed by the
claim itself on the next lines -- dropping only the line naming the year would
keep the borrowed content and discard just the evidence that it was borrowed,
which is the worst of both.
"""
import re, sys

MARKERS = re.compile(
    r"2025|bc25|confused|SPAARK|Just Woke Up|Om Nom|Kragle|postmortem-2025",
    re.IGNORECASE)

text = open(sys.argv[1]).read()
blocks = text.split("\n\n")
kept, dropped = [], 0
for b in blocks:
    if MARKERS.search(b):
        dropped += 1
        kept.append("[[REDACTED: 2025-derived block]]")
    else:
        kept.append(b)
sys.stderr.write(f"{sys.argv[1]}: dropped {dropped}/{len(blocks)} blocks\n")
print("\n\n".join(kept))

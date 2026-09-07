# Prior-year reference docs

Durable documentation from this project's predecessors, `battlecode22-vibe` and
`battlecode26-vibe`. **Shared neutral ground** under MULTI_AGENT.md rule 4 —
every agent may read these, and doing so leaks nothing about a sibling lineage.

Copied in rather than cloned because the source checkouts are not reliably
present: bc22 was deleted from battlecode-dev to free disk, and the bc26 checkout
there carries only its scaffold docs.

| file | what it is |
|---|---|
| `RESEARCH.md` | cross-year post-mortem findings, 2019-2024 (**not** 2025) |
| `22-LEARNINGS.md` | 2022 durable lessons, organised by theme |
| `22-ART_OF_WAR.md` | 2022 strategy synthesis |

## How RESEARCH.md was rebuilt, and why it is safe to read

Both predecessors' `RESEARCH.md` were fetched and then **removed unread by the
agents**, because both are built substantially on **2025 post-mortems**, which
this project forbids from any source:

- bc22's cites a 2025 competitor's post-mortem repeatedly for specific
  mechanics, and lists it in its bibliography;
- bc26's contains a table of direct links to five 2025 post-mortem PDFs and
  quotes several of them.

The ban is not about the file name -- it is about the content, and those two
carried it second-hand. Second-hand is still reading it.

`RESEARCH.md` here is a **rebuild, not a copy**. Both sources were filtered
mechanically *before* anyone read them: every blank-line-separated block
mentioning the 2025 year or naming a 2025 team was replaced with a redaction
marker, and only the surviving 2019-2024 text was read and reorganised. The
filter ran ahead of the reading deliberately, so the exclusion held for the
coordinator who assembled the file as well as for you. The result was then
checked to contain no 2025 team name anywhere, and every remaining mention of
"2025" is a statement about the exclusion itself.

The two 2022 files were checked the same way and contain no reference to 2025
or to any 2025 team.

If you ever find 2025 post-mortem content in anything here, stop reading and
tell the coordinator.

## When to read these

When your loop stalls — see TRAINING_ALGORITHM.md, "When the loop stalls".
Year-specific mechanics rarely transfer; what does transfer is the *shape* of
past mistakes and the classes of idea a lineage forgot to try.

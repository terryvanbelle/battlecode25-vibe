# Permissions

`settings.json` here is project-scoped and committed, so the intent is versioned
alongside the work it governs. The owner's rule, 2026-09-13:

> do legitimate work without stopping to ask; ask if you're doing something unusual

## The three lists

**`deny` — empty.** `WebFetch` and `WebSearch` started here and were moved to
`ask` on the owner's instruction the same day: *"There are occasions when I'll
want you to do this."* A hard deny would have made those occasions impossible
without editing config first, which is the wrong trade for a tool that is
occasionally the right answer.

What the deny had been buying is worth stating, because moving it to `ask` moves
the burden rather than removing it: this lineage must never read 2025-contest
post-mortems or the source of the benchmark bots, and a web search is the one
thing that could surface either **by accident** — a search for Battlecode
pathfinding does not know which year's write-up it is returning. Under `ask` that
rule is enforced by judgment and by the owner seeing the query in the prompt,
not by construction. So: web access here is opt-in per use, the query should be
narrow enough that the owner can see what it would return, and a result that
turns out to be 2025 material gets closed unread and reported.

**`ask` — the unusual.** Three groups: reaching the network another way (`curl`,
`wget`, `nc`, `scp`), installing software (`pip`, `npm`, `apt`), and anything
hard to undo (`sudo`, `rm -rf`, `kill`/`pkill`, `git push --force`,
`git reset --hard`, deleting or stopping the VM). `kill`/`pkill` earned its place:
a `pkill -f` pattern once matched the shell that was running it.

**On `rm -rf` specifically.** It stays in `ask`, with no narrowing exception. The
one routine step that needed it -- freezing `src/darla` as `src/darla_iter<N>`
during an accept -- now happens inside `tools/accept-iteration.sh`, which a
`Bash(tools/*)` allow already covers. Owner's call, 2026-09-13, and the right one:
an allow rule would have applied to every future command matching the pattern,
while the script removes the need for one and refuses to overwrite an existing
snapshot into the bargain. Prefer moving a dangerous step inside a checked script
over widening a permission to admit it.

**`kill` is allowed; `pkill` is not.** Owner's call, 2026-09-13, after approving a
kill of two duplicate run drivers. The split is deliberate: `kill <pid>` acts on
one process whose identity I verified immediately beforehand, while `pkill -f`
takes a *pattern* whose matches cannot be seen in advance — and it has already
misfired once today, matching the very shell that invoked it and killing the
command mid-write. Same intent, different blast radius.

Note this rule governs only local driver processes. Killing anything on
`battlecode-dev` would go through `gcloud compute ssh`, which is a separate
standing prohibition and not something a `Bash(kill *)` rule can authorise.

**`allow` — the work.** `git`, `gcloud compute ssh` and the read-only `gcloud`
queries, this repo's own scripts, and the ordinary text-processing commands that
make up a replay census. Generous on purpose: a prompt on `awk` teaches nobody
anything and trains the owner to approve without reading.

## What this does and does not guarantee

It is a **guardrail, not a boundary.** Bash rules match the *command text*, not
network syscalls. Almost all VM access here runs through `tools/gauntlet.sh`,
which calls `gcloud` and `ssh` internally — those never surface as a `Bash(ssh *)`
match, and by the same token a script could open any socket without any rule
seeing it. This stops casual and accidental access. It does not contain a
determined path.

The enforcing version is OS-level egress filtering on the driver (allow only
`github.com:443`, the GCE API endpoints, and `battlecode-dev`), which holds
regardless of what a script does. Not applied: it can break the nightly runs if
an endpoint is missed, so it wants staging rather than a one-line commit.

## Scope notes

- `ask` rules do nothing in a session already running in **bypass-permissions
  mode**; they apply to sessions started in default mode.
- These are *project* settings. `~/.claude/settings.json` covers every project;
  lift rules there if they should apply beyond this repo.
- To review or edit interactively, run `/permissions` in Claude Code.

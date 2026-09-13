# Permissions

`settings.json` here is project-scoped and committed, so the intent is versioned
alongside the work it governs. The owner's rule, 2026-09-13:

> do legitimate work without stopping to ask; ask if you're doing something unusual

## The three lists

**`deny` — `WebFetch`, `WebSearch`.** Tool-level denials, so they are airtight in
a way no Bash rule is. They also enforce a standing project rule *by
construction*: this lineage must never read 2025-contest post-mortems or the
source of the benchmark bots, and a web search is the one thing that could put
either in front of me by accident. Nothing in this project's normal work needs
the web — the only outbound traffic is `git` to GitHub and `gcloud`/`ssh` to
`battlecode-dev`.

**`ask` — the unusual.** Three groups: reaching the network another way (`curl`,
`wget`, `nc`, `scp`), installing software (`pip`, `npm`, `apt`), and anything
hard to undo (`sudo`, `rm -rf`, `kill`/`pkill`, `git push --force`,
`git reset --hard`, deleting or stopping the VM). `kill`/`pkill` earned its place:
a `pkill -f` pattern once matched the shell that was running it.

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

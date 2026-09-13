# Restarting the Claude Code session

From a fresh terminal window on your laptop to a working session again. Every
Linux and tmux command is spelled out.

The usual reason to do this is to **leave bypass-permissions mode**, which can
only be set at launch (see §6). Reattaching to a session that is still alive is
§2 and takes one command.

| | |
|---|---|
| **Driver** (runs Claude) | `claude-driver`, e2-small, zone `us-west1-b`, project `tvanbelle-vibecode` |
| **Compute VM** (runs games) | `battlecode-dev`, e2-standard-8, same zone and project |
| **tmux session** | `bc25`, one window named `claude` |
| **Launcher** | `~/bc25` on the driver |
| **Checkout** | `/home/terryvanbelle/projects/vibe/2025` |

---

## 1. From your laptop: get onto the driver

```bash
gcloud compute ssh claude-driver --zone us-west1-b --project tvanbelle-vibecode
```

If `gcloud` asks you to pick a project or complains about credentials:

```bash
gcloud auth login
gcloud config set project tvanbelle-vibecode
```

Plain SSH also works if you already have the key, but look the address up rather
than keeping it written down — it is ephemeral and changes when the instance is
recreated:

```bash
gcloud compute instances describe claude-driver \
  --zone us-west1-b --project tvanbelle-vibecode \
  --format='value(networkInterfaces[0].accessConfigs[0].natIP)'
```

`gcloud compute ssh` is preferred anyway: it manages the key for you and survives
an address change.

To confirm you are on the right machine:

```bash
hostname          # expect: claude-driver
```

---

## 2. If the session is still alive, just reattach

```bash
tmux ls
```

```
bc25: 1 windows (created Sun Sep  6 21:19:11 2026)
```

If `bc25` is listed, nothing is broken — reattach and you are done:

```bash
~/bc25            # attaches if the session exists, creates it if it does not
```

or equivalently `tmux attach -t bc25`.

**Detach again without killing anything:** `Ctrl+b` then `d`.

---

## 3. Before restarting: see what is running

A restart is safe for the games and destructive for the loop. Check both.

```bash
# Evaluation drivers -- these are setsid-detached and SURVIVE a restart
pgrep -fa 'head-to-head.sh|paired-roster.sh|widen|replicate.sh' | grep -v 'bash -c'

# Games actually playing on the VM right now
pgrep -fc '\.reexec-gauntlet\.sh'

# One-line summary of what the VM is doing
/home/terryvanbelle/projects/vibe/2025/agents/darla/tools/status-line.sh

# Scheduled maintenance -- independent of the session, also survives
systemctl list-timers --all | grep bc25
```

**Survives a restart:** every `setsid`-detached run driver, the gauntlets they
launched on `battlecode-dev`, and the systemd timers.

**Does not survive:** the Darla heartbeat loop, and any background task or
monitor armed inside the session. §7 re-arms it.

There is no need to wait for a run to finish. A 450-game gauntlet keeps playing
with no session attached; the result lands in `agents/darla/gauntlet/<run>/` and
is read whenever someone asks.

---

## 4. Leave the session cleanly

Reattach first if you are not already inside (`~/bc25`), then, at the Claude
prompt:

```
/exit
```

`Ctrl+d` does the same thing. **`Ctrl+c` twice** also works if the UI is wedged.

Because `~/bc25` starts tmux with `claude` as the session's command, the tmux
session ends when Claude exits — you do not need to kill tmux separately. Confirm:

```bash
tmux ls           # expect: "no server running on /tmp/tmux-1000/default"
```

If a session somehow lingers:

```bash
tmux kill-session -t bc25
```

---

## 5. Choose the permission mode

`~/bc25` currently hardcodes bypass mode:

```bash
exec tmux new -s "$SESSION" "claude --dangerously-skip-permissions"
```

`claude --permission-mode <mode>` accepts `acceptEdits`, `auto`,
`bypassPermissions`, `manual`, `dontAsk`, and `plan`.

| mode | prompts? | `deny` rules | use when |
|---|---|---|---|
| `--dangerously-skip-permissions` | never | **still enforced** | unattended overnight work |
| *(default, no flag)* | yes, on anything not in `allow` | enforced | you are watching the session |
| `--permission-mode dontAsk` | *believed* not to | enforced | unverified — test before relying on it |

**The overnight caveat.** In default mode a command matching no `allow` rule
blocks until you answer it. Left alone overnight that is indistinguishable from
the session being idle. The `allow` list in `.claude/settings.json` covers the
routine work, but compound commands (`cd X && Y`) may not match a single prefix
rule. If nobody will be at the keyboard, prefer bypass and rely on `deny`.

**`deny` works in every mode, live, with no restart** — verified 2026-09-13 by
adding `WebFetch`/`WebSearch` to `deny` mid-session and watching them disappear
while bypass mode was active. So for anything you want hard-stopped right now,
edit `.claude/settings.json` instead of restarting.

---

## 6. Relaunch

Edit the launcher once so the flag is not baked in:

```bash
nano ~/bc25       # or: vi ~/bc25
```

Make the last line take arguments:

```bash
exec tmux new -s "$SESSION" "claude $*"
```

Then launch in whichever mode you want:

```bash
~/bc25                              # default mode: prompts on anything not allowed
~/bc25 --continue                   # default mode, RESUMES the previous conversation
~/bc25 --dangerously-skip-permissions --continue    # bypass, resuming
```

`--continue` picks up the most recent conversation with its context. Without it
you get a cold session that knows only what is in the repo — which is a lot
(`agents/darla/DESIGN.md` is the lab notebook) but not the working state of an
in-flight experiment.

One-liner if you would rather not edit the launcher:

```bash
cd /home/terryvanbelle/projects/vibe/2025 && tmux new -s bc25 "claude --continue"
```

---

## 7. Re-arm the Darla heartbeat

This is the step people forget. Without it the session sits idle between your
messages and nothing queues new work. At the Claude prompt:

```
/loop 10m Darla heartbeat. Keep this SHORT — the owner wants visible proof that work is progressing, not a report.

1. Run `/home/terryvanbelle/projects/vibe/2025/agents/darla/tools/status-line.sh` and `touch ~/.bc25-coordinator-heartbeat`.
2. If it says RUNNING: reply with just that one status line. Nothing else. Do not re-analyse, do not re-report finished results, do not repeat conclusions already in DESIGN.md.
3. If it says IDLE: that is a failure — queue work immediately. Build arms with tools/make-arm.sh, compile on the VM, launch with `tools/head-to-head.sh <arm> darla`. Keep at least 3 queued. Then reply with the new status line.
4. If any run directory has a summary.txt whose result is not yet written up in DESIGN.md, read it, write it up, and commit — then give the status line.
```

Adjust `10m` to the cadence you want. Check what is already scheduled with
`/cron` before adding a second copy — two heartbeats on the same project waste
tokens and interleave confusingly.

---

## 8. Verify

```bash
# inside the session
/status                     # model, permission mode, working directory

# from a shell (Claude can run these for you)
hostname                                                  # claude-driver
tmux ls                                                   # bc25: 1 windows
cd /home/terryvanbelle/projects/vibe/2025 && git log --oneline -1
git log --oneline origin/main..HEAD                       # must be EMPTY: unpushed work is invisible work
agents/darla/tools/status-line.sh                         # RUNNING / WAITING / IDLE
```

A healthy result is `RUNNING` or `WAITING`, a clean push state, and a heartbeat
arriving within the interval you set.

---

## 9. tmux cheat sheet

| | |
|---|---|
| list sessions | `tmux ls` |
| attach | `tmux attach -t bc25` (or `~/bc25`) |
| detach, leaving everything running | `Ctrl+b` then `d` |
| scroll back | `Ctrl+b` then `[`, arrows/PgUp, `q` to exit |
| kill the session | `tmux kill-session -t bc25` |
| kill every session | `tmux kill-server` |

The whole point of tmux here is that an SSH drop **detaches** rather than kills:
the session keeps working and you reattach with `~/bc25`. This was added after an
SSH hangup killed running agents twice.

---

## 10. Troubleshooting

**`tmux ls` says no server, but work is still running.** Normal and fine. The run
drivers are `setsid`-detached and outlive the session entirely. Start a new
session and ask for `status-line.sh`.

**Claude starts in the wrong directory.** `~/bc25` does `cd` before launching; a
manual `tmux new` does not. Always `cd /home/terryvanbelle/projects/vibe/2025`
first.

**Permission prompts appear where they did not before.** Expected in default
mode. Either answer them, add the pattern to `allow` in `.claude/settings.json`
(see `.claude/README.md`), or relaunch in bypass mode.

**The VM looks asleep.** `tools/lib.sh` has `ensure_vm`, which starts
`battlecode-dev` on demand, so the next gauntlet wakes it. To check by hand:

```bash
gcloud compute instances list --project tvanbelle-vibecode
```

**Disk pressure on the driver.** `df -h /` — the `bc25-driver-prune` timer
handles this, but an 18G BC26 archive under `/Users/terryvanbelle/projects/vibe_bc26`
is the usual culprit.

**To wipe and rebuild rather than restart** — that is a different document:
`WIPE-RUNBOOK.md`.

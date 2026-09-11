# Wipe runbook — battlecode-dev and claude-driver

**This document does not run anything.** It is a reference for deliberately
destroying the two machines this project uses, written while nothing is on fire
so that the decisions are made calmly rather than at speed.

Nothing here should be run without the project owner explicitly authorising the
specific level below. The standing shared-VM rules (never kill processes, never
stop the VM) remain in force for all ordinary work; this document is the named
exception, not a loophole.

| | |
|---|---|
| **VM** | `battlecode-dev`, zone `us-west1-b`, project `tvanbelle-vibecode` |
| **Driver** | `claude-driver` (the machine this repo is checked out on) |
| **Git remote** | `https://github.com/terryvanbelle/battlecode25-vibe.git` |

---

## 0. STOP — read this before anything else

Four things are **not** recoverable from git or from the other machine. If any
of them matter, save them first; every level below destroys at least one.

| what | where | size | why it is gone forever |
|---|---|---|---|
| **BC26 archive** | driver `/Users/terryvanbelle/projects/vibe_bc26` | **18G** | another project's recorded results; not in this repo, not on the VM |
| **BC26 archive** | VM `~/battlecode26-vibe` | **2.3G** | same, second copy — not necessarily the same contents |
| **BC25 finalist bots** | VM `~/bc25-benchmarks` | 125M | deliberately never committed (the isolation firewall). Re-downloading needs the original source, which is not scripted |
| **Coordinator memory** | driver `~/.claude/projects/-home-terryvanbelle-projects-vibe-2025/memory/` | small | not in the repo |

Also uncommitted at the time of writing, and lost with the driver's repo:

- `.methods-queue/pending.md` (modified)
- `agents/alice/TRAINING_LOG.md` (modified)
- `agents/alice/src/alice_forward/` (untracked)
- every `.bc25` replay under `agents/*/gauntlet/*/losses/` (gitignored by design)

**Everything else is safe**: all committed work is pushed (`git log origin/main..HEAD`
was empty when this was written — re-check before wiping).

### Pre-flight

```bash
cd /home/terryvanbelle/projects/vibe/2025

# 1. Is anything unpushed or uncommitted?
git status --short
git log --oneline origin/main..HEAD

# 2. Push whatever should survive.
git add -A && git commit -m "pre-wipe snapshot" && git push origin main

# 3. Back up the four irrecoverable items (adjust the destination).
tar czf ~/bc26-driver-archive.tgz  /Users/terryvanbelle/projects/vibe_bc26
tar czf ~/coordinator-memory.tgz   ~/.claude/projects/-home-terryvanbelle-projects-vibe-2025/memory
gcloud compute ssh battlecode-dev --zone us-west1-b --project tvanbelle-vibecode \
  --command 'tar czf - ~/bc25-benchmarks ~/battlecode26-vibe' > ~/vm-irrecoverable.tgz

# 4. Confirm the backups are non-empty before continuing.
ls -lh ~/bc26-driver-archive.tgz ~/coordinator-memory.tgz ~/vm-irrecoverable.tgz
```

---

## 1. Quiesce first — always, at every level

Stop the things that will otherwise keep writing while you delete.

```bash
# Driver-side daemons (this project's own; safe to kill)
pkill -f 'tools/arm-runner.sh'
pkill -f 'tools/idle-filler.sh'
pkill -f 'tools/disk-guard.sh'
pkill -f 'tools/head-to-head.sh'
pkill -f 'tools/replicate.sh'

# Scheduled work
sudo systemctl stop    bc25-tournament.timer bc25-benchmark.service \
                       bc25-vm-prune.timer bc25-driver-prune.timer
sudo systemctl disable bc25-tournament.timer \
                       bc25-vm-prune.timer bc25-driver-prune.timer

# Confirm nothing is still playing games on the VM
gcloud compute ssh battlecode-dev --zone us-west1-b --project tvanbelle-vibecode \
  --command 'pgrep -fc battlecode.server.Main'      # expect 0
```

---

## 2. Level 1 — wipe this project's data, keep both machines

The usual case: reclaim space or start the experiment clean, without rebuilding
anything. **Leaves BC26 and the benchmark bots intact.**

```bash
# --- VM ---
gcloud compute ssh battlecode-dev --zone us-west1-b --project tvanbelle-vibecode \
  --command 'rm -rf ~/battlecode25-vibe ~/darla-compile ~/out ~/bob-tools ~/.bc25-slots'

# --- driver ---
cd /home/terryvanbelle/projects/vibe/2025
rm -rf agents/*/gauntlet agents/*/matches agents/*/logs benchmarks/2026* tournaments/2026*
rm -f  /tmp/darla-*.log /tmp/bc25-*.lock ~/.bc25-coordinator-heartbeat
```

Recovery: the next gauntlet recreates the VM workspace automatically. Committed
results are still in git; only the local run artefacts are gone.

---

## 3. Level 2 — wipe both machines' home directories

Everything this project ever wrote outside git, on both machines, **including the
benchmark bots and the BC26 archives.** Do not run without the backups in §0.

```bash
# --- VM: everything under the home directory ---
gcloud compute ssh battlecode-dev --zone us-west1-b --project tvanbelle-vibecode \
  --command 'rm -rf ~/battlecode25-vibe ~/battlecode26-vibe ~/bc25-benchmarks \
                    ~/darla-compile ~/out ~/bob-tools ~/.bc25-slots \
                    ~/jdk21 ~/jdk21.tar.gz ~/.gradle'

# --- driver: the checkout, the archives, the memory, the units ---
rm -rf /home/terryvanbelle/projects/vibe/2025
rm -rf /Users/terryvanbelle/projects/vibe_bc26
rm -rf ~/.claude/projects/-home-terryvanbelle-projects-vibe-2025
sudo rm -f /etc/systemd/system/bc25-*.{service,timer}
sudo systemctl daemon-reload
```

Recovery: `git clone https://github.com/terryvanbelle/battlecode25-vibe.git`
restores all committed work. The VM re-bootstraps on the next run **except** the
JDK and the benchmark bots, which must be restored from `~/vm-irrecoverable.tgz`
or re-downloaded.

---

## 4. Level 3 — destroy the VM instance itself

The only option that also releases the disk and the IP. Irreversible; there is no
undelete in GCE.

```bash
# Confirm you are about to delete the right thing
gcloud compute instances describe battlecode-dev \
  --zone us-west1-b --project tvanbelle-vibecode \
  --format='value(name,status,creationTimestamp)'

# Optional: keep a disk image first (cheap insurance, minutes to create)
gcloud compute images create battlecode-dev-final \
  --source-disk battlecode-dev --source-disk-zone us-west1-b \
  --project tvanbelle-vibecode

# Delete the instance and its boot disk
gcloud compute instances delete battlecode-dev \
  --zone us-west1-b --project tvanbelle-vibecode --delete-disks=all --quiet
```

A gentler alternative that stops billing for CPU but keeps everything on disk:

```bash
gcloud compute instances stop battlecode-dev \
  --zone us-west1-b --project tvanbelle-vibecode
```

**Note:** `tools/lib.sh` calls `ensure_vm`, which starts the VM on demand. After a
stop, the next gauntlet will start it again. After a delete, every tool that
touches the VM fails until a new instance of the same name exists.

---

## 5. Verification

```bash
# VM gone or empty?
gcloud compute instances list --project tvanbelle-vibecode | grep battlecode-dev
gcloud compute ssh battlecode-dev --zone us-west1-b --project tvanbelle-vibecode \
  --command 'du -x -sh ~/* 2>/dev/null | sort -rh | head'

# Driver clean?
ls /home/terryvanbelle/projects/vibe/2025 2>&1
systemctl list-timers --all | grep bc25
pgrep -fa 'arm-runner|idle-filler|disk-guard|head-to-head'
df -h /
```

---

## 6. Rebuilding afterwards

1. `git clone https://github.com/terryvanbelle/battlecode25-vibe.git` on the driver.
2. Recreate `battlecode-dev` in `us-west1-b` (e2-standard-8 is what it was: 8 vCPU,
   31G RAM, 20G disk — **the 20G disk is what filled on 2026-09-11; 50G would be
   a better choice**).
3. Restore `~/jdk21` and `~/bc25-benchmarks` on the VM from the backup tarball.
4. Re-install the systemd units from `tools/systemd/` (see its README).
5. The first gauntlet run recreates `~/battlecode25-vibe` by rsync automatically.

## 7. What is deliberately *not* here

- No command that touches the GitHub remote. Deleting published history is a
  separate decision with a separate authorisation, and nothing in this document
  should make it look routine.
- No "wipe everything" one-liner. Each level is written out so that running it
  requires reading it.

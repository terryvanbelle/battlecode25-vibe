# Wipe runbook — the two VMs

**This document does not run anything.** It is a reference for deliberately
destroying the two machines this project uses. Nothing here touches GitHub: the
remote is the backup, and everything committed and pushed survives every command
below.

Standing policy from the owner: **anything not checked in is expendable.** So
there is no backup ceremony here — just the commands, in escalating order.

| | |
|---|---|
| **VM** | `battlecode-dev`, zone `us-west1-b`, project `tvanbelle-vibecode` |
| **Driver** | `claude-driver` (holds the git checkout) |
| **Remote** | `github.com/terryvanbelle/battlecode25-vibe` — untouched by all of this |

Before anything: **push.** That is the whole safety net.

```bash
cd /home/terryvanbelle/projects/vibe/2025
git status --short                       # anything you actually want?
git add -A && git commit -m "pre-wipe" && git push origin main
git log --oneline origin/main..HEAD      # must be empty
```

Two things are not in the repo and will not come back. Both are fine to lose per
the policy above, listed so the loss is a decision and not a surprise:
**`~/bc25-benchmarks` on the VM** (the BC25 finalist bots, 125M — deliberately
never committed, and re-downloading is not scripted) and the **BC26 archives**
(`~/battlecode26-vibe` on the VM, 2.3G; `/Users/terryvanbelle/projects/vibe_bc26`
on the driver, 18G).

---

## 1. Quiesce — do this first at every level

```bash
# This project's own daemons on the driver
pkill -f 'tools/arm-runner.sh|tools/idle-filler.sh|tools/disk-guard.sh'
pkill -f 'tools/head-to-head.sh|tools/replicate.sh'

# Scheduled work
sudo systemctl stop    bc25-tournament.timer bc25-vm-prune.timer bc25-driver-prune.timer
sudo systemctl disable bc25-tournament.timer bc25-vm-prune.timer bc25-driver-prune.timer

# Nothing still playing on the VM?
gcloud compute ssh battlecode-dev --zone us-west1-b --project tvanbelle-vibecode \
  --command 'pgrep -fc battlecode.server.Main'     # expect 0
```

---

## 2. battlecode-dev — wipe the disk, keep the instance

```bash
# Just this project's working data (leaves the JDK, the benchmark bots, BC26)
gcloud compute ssh battlecode-dev --zone us-west1-b --project tvanbelle-vibecode \
  --command 'rm -rf ~/battlecode25-vibe ~/darla-compile ~/out ~/bob-tools ~/.bc25-slots'

# Everything this project and its neighbours ever wrote
gcloud compute ssh battlecode-dev --zone us-west1-b --project tvanbelle-vibecode \
  --command 'rm -rf ~/battlecode25-vibe ~/battlecode26-vibe ~/bc25-benchmarks \
                    ~/darla-compile ~/out ~/bob-tools ~/.bc25-slots \
                    ~/jdk21 ~/jdk21.tar.gz ~/.gradle'
```

The workspace rebuilds itself by rsync on the next gauntlet. The JDK and the
benchmark bots do not — restore or re-download them before expecting either
`tools/engine-javap.sh` or `tools/benchmark.sh` to work again.

---

## 3. battlecode-dev — destroy the instance

Irreversible. There is no undelete in GCE.

```bash
# Confirm the target
gcloud compute instances describe battlecode-dev \
  --zone us-west1-b --project tvanbelle-vibecode \
  --format='value(name,status,creationTimestamp)'

# Delete instance and boot disk
gcloud compute instances delete battlecode-dev \
  --zone us-west1-b --project tvanbelle-vibecode --delete-disks=all --quiet
```

Cheaper, reversible alternative — stops CPU billing, keeps the disk:

```bash
gcloud compute instances stop battlecode-dev \
  --zone us-west1-b --project tvanbelle-vibecode
```

**After a `stop`, `ensure_vm` in `tools/lib.sh` restarts the VM on demand**, so
the next gauntlet quietly brings it back. After a `delete`, every tool that
touches the VM fails until an instance of the same name exists again.

---

## 4. claude-driver — wipe

```bash
# The checkout (everything committed is on GitHub; the rest is expendable)
rm -rf /home/terryvanbelle/projects/vibe/2025

# The BC26 archive, 18G, the thing that actually fills this disk
rm -rf /Users/terryvanbelle/projects/vibe_bc26

# Scheduler units and scratch
sudo rm -f /etc/systemd/system/bc25-*.service /etc/systemd/system/bc25-*.timer
sudo systemctl daemon-reload
rm -f /tmp/darla-*.log /tmp/bc25-*.lock ~/.bc25-coordinator-heartbeat
```

The driver is where the git checkout lives, so wiping it loses nothing that was
pushed. If the driver itself is a GCE instance in the same project, §3's commands
apply to it with the name changed — check first:

```bash
gcloud compute instances list --project tvanbelle-vibecode
```

---

## 5. Verify

```bash
gcloud compute instances list --project tvanbelle-vibecode
gcloud compute ssh battlecode-dev --zone us-west1-b --project tvanbelle-vibecode \
  --command 'du -x -sh ~/* 2>/dev/null | sort -rh | head'
ls /home/terryvanbelle/projects/vibe/2025 2>&1
systemctl list-timers --all | grep bc25
df -h /
```

---

## 6. Rebuild

1. `git clone https://github.com/terryvanbelle/battlecode25-vibe.git` on the driver.
2. Recreate `battlecode-dev` in `us-west1-b`. It was e2-standard-8 — 8 vCPU, 31G
   RAM, **20G disk**. The 20G is what filled on 2026-09-11 and killed three arms
   mid-run; **50G is the right size** if it is ever rebuilt.
3. Put back `~/jdk21` and `~/bc25-benchmarks` on the VM.
4. Reinstall the systemd units from `tools/systemd/` (see its README).
5. The first gauntlet recreates `~/battlecode25-vibe` automatically.

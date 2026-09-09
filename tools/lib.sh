#!/usr/bin/env bash
# Shared helpers for running Battlecode 2025 workloads on the battlecode-dev VM.
# Source this from other tools; not executable on its own.

VM=battlecode-dev
ZONE=us-west1-b
PROJECT=tvanbelle-vibecode
REMOTE_REPO=battlecode25-vibe          # ~/battlecode25-vibe on the VM
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Plain ssh/scp with the gcloud-managed key -- `gcloud compute ssh` re-pushes
# keys to instance metadata on every call and stalls under load (BC26 lesson).
SSHO=(-i "$HOME/.ssh/google_compute_engine" -o StrictHostKeyChecking=no
      -o UserKnownHostsFile=/dev/null -o ConnectTimeout=20 -o ServerAliveInterval=20
      -o ServerAliveCountMax=3 -o LogLevel=ERROR)
USER_NAME="${BC_SSH_USER:-$(whoami)}"

vm_ip () { gcloud compute instances describe "$VM" --zone="$ZONE" --project="$PROJECT" \
             --format='value(networkInterfaces[0].accessConfigs[0].natIP)' 2>/dev/null; }
gssh () { ssh "${SSHO[@]}" "$USER_NAME@$IP" "$1"; }
gscp () { scp "${SSHO[@]}" "$@"; }
wait_ssh () { for _ in $(seq 1 40); do gssh true 2>/dev/null && return 0; sleep 8; done; return 1; }

# The IP, cached across invocations. EVERY tool in this directory calls
# ensure_vm before doing anything, and the old version paid two `gcloud compute
# instances describe` calls each time: measured at 32.5s of wall time per
# invocation, against a 3s ssh round trip and (for example) a 0.25s replay dump.
# That overhead was the real cost behind "71s to dump one game", not the work.
#
# The fast path trusts the cached IP only as far as a single ssh probe: if the
# probe answers, the VM is up and the IP is right, which is the whole of what
# ensure_vm has to establish. Anything else -- no cache, a stale IP after a
# restart, a stopped VM -- falls through to the original slow path, which is
# unchanged and still authoritative. A wrong cached IP therefore costs one failed
# probe, never a wrong answer.
VM_IP_CACHE="${TMPDIR:-/tmp}/.bc25-vm-ip-$VM"

ensure_vm () {
  # Fast path: a cached IP that still answers.
  if [ -s "$VM_IP_CACHE" ]; then
    IP="$(cat "$VM_IP_CACHE")"
    if ssh "${SSHO[@]}" -o ConnectTimeout=8 "$USER_NAME@$IP" true 2>/dev/null; then
      return 0
    fi
  fi
  local state
  state=$(gcloud compute instances describe "$VM" --zone="$ZONE" --project="$PROJECT" --format='value(status)' 2>/dev/null || true)
  [ "$state" = RUNNING ] || { echo "  starting VM ..."; gcloud compute instances start "$VM" --zone="$ZONE" --project="$PROJECT" >/dev/null; }
  IP="$(vm_ip)"
  [ -n "$IP" ] || { echo "!! no external IP" >&2; return 1; }
  wait_ssh || { echo "!! cannot reach $USER_NAME@$IP" >&2; return 1; }
  printf '%s\n' "$IP" > "$VM_IP_CACHE" 2>/dev/null || true
  return 0
}

# Workspace = nearest ancestor of $PWD (within the repo) containing build.gradle.
# Its path relative to the repo root doubles as the remote workspace dir.
find_workspace () {
  local d="$PWD"
  while [ "$d" != "/" ]; do
    if [ -f "$d/build.gradle" ] && [[ "$d" == "$REPO_ROOT"/* ]]; then
      WS_DIR="$d"; WS_REL="${d#"$REPO_ROOT"/}"; return 0
    fi
    d="$(dirname "$d")"
  done
  echo "!! run this from inside a workspace (agents/<name> or arena)" >&2
  return 1
}

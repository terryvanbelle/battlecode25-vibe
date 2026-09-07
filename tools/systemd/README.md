# Tournament schedule (claude-driver)

The round-robin tournament runs at **06:00 and 18:00 America/Los_Angeles**,
driven by these two units rather than by cron.

Why not cron: Debian's cron (3.0pl1) has no `CRON_TZ`, so a crontab entry can
only name a fixed *UTC* hour. Pinning 13:00/01:00 UTC is correct only while
Pacific is on PDT and silently slips an hour every DST changeover. systemd
resolves the zone on each firing, so the wall-clock time stays put.

Install / update after editing these files:

```bash
sudo cp tools/systemd/bc25-tournament.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now bc25-tournament.timer
systemctl list-timers bc25-tournament.timer   # when does it next fire
```

Log: `~/bc25-tournament.log` (appended by the service; `journalctl -u
bc25-tournament.service` has the unit's own view). A run in progress is
`systemctl is-active bc25-tournament.service`. To play a tournament right now,
`sudo systemctl start bc25-tournament.service` — but check first that the
agents are not mid-gauntlet, since it competes for the same VM slots.


# Agent watchdog (claude-driver)

`bc25-agent-watchdog.timer` runs `tools/agent-watchdog.sh` every 10 minutes.

Why it exists: the coordinator session restarts dead agents itself, on a
self-scheduled loop — which is enough for every failure except the one that
matters most. An account usage limit pauses the coordinator too; its scheduled
wake-up fires into a 429, the turn dies before it can re-arm, and the loop meant
to recover from the limit is killed by it. systemd needs no API quota, so it
keeps retrying through the outage and lands as soon as the window clears.

It is **not** a second coordinator. Two coordinators would each spawn three
agents into one working tree, the exact race MULTI_AGENT.md's git rules forbid.
It types a message into the coordinator's existing tmux session instead:

| situation | what happens |
|---|---|
| coordinator paused by a usage limit | keystrokes queue; processed when the window clears |
| coordinator alive and healthy | heartbeat is fresh, no nudge sent |
| tmux session gone entirely | recreated (as `~/bc25` does), then nudged |

Liveness is a heartbeat file, `~/.bc25-coordinator-heartbeat`, touched by the
coordinator each loop tick. A heartbeat rather than "any recent agent commits?"
because an agent can legitimately spend half an hour tracing a replay without
committing, and a false positive costs duplicate agents.

```bash
DRY_RUN=1 tools/agent-watchdog.sh     # decide and print, send nothing
STALE_MIN=30 COOLDOWN_MIN=15          # thresholds (defaults)
systemctl list-timers 'bc25-*'        # when both timers next fire
tail ~/bc25-watchdog.log              # what it decided, every 10 minutes
```

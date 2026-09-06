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

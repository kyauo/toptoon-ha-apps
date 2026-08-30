# KY Home Assistant Apps

Home Assistant App repository containing **Toptoon Attendance**.

## Repository structure

```text
toptoon-ha-apps/
├── repository.yaml
├── README.md
└── toptoon_attendance/
    ├── config.yaml
    ├── Dockerfile
    ├── run.sh
    ├── bot.py
    ├── README.md
    └── DOCS.md
```

> Never commit real `PHPSESSID` or `rm_session` values. They are stored only in the Home Assistant App data directory.

## Current version

Contains **Toptoon Attendance v0.4.2**. This version adds timestamped logs, readable UI times, automatic preservation of server-refreshed Toptoon session cookies, clearer first-setup wording, and an X close button in the Ingress UI.


### 21:00 safety reminder
If today's attendance has not been confirmed by `manual_reminder_time` (default 21:00), the App sends one mobile reminder so you can check Toptoon manually before the day ends.

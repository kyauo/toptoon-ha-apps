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

## GitHub setup

1. Create a new GitHub repository, for example `toptoon-ha-apps`.
2. Keep the repository private while testing.
3. Upload the contents of this folder to the repository root.
4. After confirming the repository works with Home Assistant, make it public if you
   want Home Assistant to install it directly as a third-party App repository.

> Do not put `PHPSESSID` or `rm_session` values in GitHub.
> They are entered only in the Home Assistant App configuration UI.

## Add the repository to Home Assistant

In Home Assistant:

1. Open **Settings → Apps → App store**.
2. Open the repository management menu.
3. Add the GitHub repository URL.
4. Refresh the App store if necessary.
5. Install **Toptoon Attendance**.

## First test

In the App configuration:

- enter the current `PHPSESSID`
- enter the current `rm_session`
- leave `timezone` as `Asia/Seoul`
- set `run_on_start: true`

Start the App. If today's attendance has already been completed, the log should say:

```text
Attendance was already completed today.
```

After the test succeeds, set `run_on_start: false` and restart the App.

## Session expiry

If Toptoon returns `errorType: login`, the App records `login_expired` and can
create a Home Assistant persistent notification asking you to refresh the two
cookie values.


## Current version

Contains **Toptoon Attendance v0.4.0** with a Home Assistant Ingress web UI for manual session renewal.

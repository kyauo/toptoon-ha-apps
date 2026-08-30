# Toptoon Attendance 0.4.1

## Automatic flow

- Daily attendance: configured by `run_time` (default 00:30 Asia/Seoul).
- Retry 1: default +5 minutes.
- Retry 2: default +15 minutes from the first attempt.
- After all attempts fail: Home Assistant persistent notification.
- Morning unresolved-failure recheck: default 09:05.
- If still unresolved: mobile notification through the configured notify entity.
- Every log line includes the configured local date/time and timezone abbreviation.

## Session lifecycle

The Ingress form is primarily for first setup and recovery after a fully expired login. After a valid session has been stored, the App uses it for scheduled attendance. If Toptoon sends a refreshed `PHPSESSID` or `rm_session` cookie in a response, the App automatically saves the refreshed value to `/data/session.json`. Values are never written to logs or rendered back into the web UI.

## Web UI

Open **OPEN WEB UI** from the Home Assistant App page. The page shows readable local timestamps, current attendance state, and an X close button at the top-right.

## Security

The web UI is exposed only through Home Assistant Ingress. Home Assistant authenticates the user before proxying the request to the App. The App rejects web requests whose source is not the Ingress proxy address.

Do not commit session values or `/data/session.json` to GitHub.

- 21:00 manual reminder: if no successful or already-confirmed attendance exists for the current day, send a mobile reminder to check Toptoon manually.

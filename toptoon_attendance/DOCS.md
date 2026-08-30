# Toptoon Attendance 0.4.0

## Automatic flow

- Daily attendance: configured by `run_time` (default 00:30 Asia/Seoul).
- Retry 1: default +5 minutes.
- Retry 2: default +15 minutes from the first attempt.
- After all attempts fail: Home Assistant persistent notification.
- Morning unresolved-failure recheck: default 09:05.
- If still unresolved: mobile notification through the configured notify entity.

## Renewing an expired login session

This version no longer uses a bookmarklet, webhook, or STDIN to transfer browser cookies.

Open the App's **OPEN WEB UI** button through Home Assistant Ingress. Enter the two Toptoon session values manually:

- `PHPSESSID`
- `rm_session`

Press **저장하고 즉시 출석 확인**. The App writes the new values to `/data/session.json` and immediately performs an attendance request.

The session values are not printed to logs or rendered back into the page.

## Security

The web UI is exposed only through Home Assistant Ingress. Home Assistant authenticates the user before proxying the request to the App. The App also rejects web requests whose source is not the Ingress proxy address.

Do not commit session values or `/data/session.json` to GitHub.

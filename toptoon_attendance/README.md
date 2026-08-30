# Toptoon Attendance 0.4.0

Home Assistant App for scheduled Toptoon attendance.

## v0.4.0

- Keeps the existing daily attendance schedule and retry logic.
- Keeps the 09:05 unresolved-failure recheck and mobile notification.
- Removes the browser bookmarklet, webhook, and App STDIN session-transfer flow.
- Adds a Home Assistant **Ingress web UI** for manually renewing `PHPSESSID` and `rm_session`.
- Saving new session values immediately performs an attendance check.
- Stores renewed session values only in `/data/session.json`.
- App Configuration cookie values remain as a fallback.
- Uses the current multi-platform Home Assistant base image: `ghcr.io/home-assistant/base:latest`.

## Session renewal

When Home Assistant reports that the Toptoon login session has expired:

1. Log in to Toptoon normally in a browser.
2. Copy the current `PHPSESSID` and `rm_session` values from the browser's cookie management UI.
3. In Home Assistant open **Settings → Apps → Toptoon Attendance → OPEN WEB UI**.
4. Paste both values.
5. Press **저장하고 즉시 출석 확인**.

The page will report whether the session works and whether attendance succeeded or was already completed.

Never put real cookie values in GitHub.

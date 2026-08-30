# Toptoon Attendance 0.4.3

Home Assistant App for scheduled Toptoon attendance.

## v0.4.3

- Adds KST/local-time timestamps to every App log line.
- Displays saved/test times in the Ingress UI as readable local time instead of raw ISO strings.
- Clarifies that session entry is an initial setup / expired-login recovery step, not a daily task.
- Automatically preserves refreshed `PHPSESSID` / `rm_session` values returned by Toptoon. Cookie values are never printed to logs.
- Adds an **X close button** to both the input and result screens. It returns to the Home Assistant root view.
- Keeps the v0.4.0 automatic schedule, retries, failure notifications, and immediate session validation.

## Normal operation

1. Enter `PHPSESSID` and `rm_session` once and press **저장하고 즉시 출석 확인**.
2. Home Assistant performs the scheduled attendance automatically.
3. If Toptoon rotates either session cookie in an HTTP response, the App updates `/data/session.json` automatically.
4. Re-enter the two values only if Toptoon reports that the login is fully expired.

Never put real cookie values in GitHub.


### 21:00 safety reminder
If today's attendance has not been confirmed by `manual_reminder_time` (default 21:00), the App sends one mobile reminder so you can check Toptoon manually before the day ends.

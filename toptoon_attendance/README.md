# Toptoon Attendance 0.3.0

- 00:30 daily attendance
- retries at +5 min and +15 min
- 09:05 unresolved-failure recheck
- browser bookmarklet session sync via Home Assistant webhook and App STDIN
- current browser session stored in `/data/session.json`
- App Configuration cookie values remain as fallback
- corrected `notify.send_message` REST payload

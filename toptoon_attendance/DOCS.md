# Toptoon Attendance

## Configuration

### `phpsessid`
Current Toptoon `PHPSESSID` cookie value.

### `rm_session`
Current Toptoon `rm_session` cookie value.

### `run_time`
Daily run time in 24-hour `HH:MM` format.

### `timezone`
IANA timezone name. Default: `Asia/Seoul`.

### `run_on_start`
If enabled, run one attendance request immediately when the App starts.
Useful for testing. Normally leave disabled.

### `notify_on_login_expiry`
Create a Home Assistant persistent notification if Toptoon reports that
the login session is no longer valid.

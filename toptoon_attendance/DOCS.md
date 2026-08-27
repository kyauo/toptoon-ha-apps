# Toptoon Attendance v0.2.0

## Daily flow

Default schedule:

- 00:15: attendance attempt
- 00:20: first retry if needed
- 00:30: second retry if needed
- after the second retry fails: create a Home Assistant persistent notification
- 09:05: re-check the unresolved failure
- if still unresolved at 09:05: send a mobile push notification

Successful attendance and "already attended" remain silent.

## Configuration

### `phpsessid`
Current Toptoon `PHPSESSID` cookie value.

### `rm_session`
Current Toptoon `rm_session` cookie value.

### `run_time`
Daily attendance time. Default: `00:15`.

### `retry_1_minutes`
Minutes after the first failed attempt for retry 1. Default: `5`.

### `retry_2_minutes`
Minutes after the original attempt for retry 2. Default: `15`.

### `mobile_alert_time`
Morning re-check and phone notification time. Default: `09:05`.

### `mobile_notify_entity`
Home Assistant notify entity for the phone. Default: `notify.ky17`.

Verify the exact entity ID in:
Settings -> Devices & services -> Entities -> KY17 -> entity details.

### `run_on_start`
Runs a single test request immediately when the App starts. It does not run the full retry workflow.

### `notify_on_failure`
Controls Home Assistant persistent failure notifications.

## Session expiry

If Toptoon returns `errorType: login`, the App retries on schedule. If it remains
unresolved after the retries, Home Assistant receives a persistent notification.
At the morning alert time the App checks again and sends the phone push only if
the issue is still unresolved.

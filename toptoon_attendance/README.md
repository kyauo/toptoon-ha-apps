# Toptoon Attendance for Home Assistant

Home Assistant App for automatic Toptoon attendance.

## v0.2.0

The App now separates night-time failure handling from morning phone alerts:

```text
00:15  attendance
00:20  retry 1
00:30  retry 2
        |
        +-- still failing -> HA persistent notification

09:05  re-check
        |
        +-- recovered -> no phone push
        +-- still failing -> KY17 phone push
```

By default the mobile notification entity is `notify.ky17`. Confirm the exact
entity ID in Home Assistant before relying on the phone alert.

Credentials are entered only in the Home Assistant App configuration UI.
Do not commit cookie values to GitHub.

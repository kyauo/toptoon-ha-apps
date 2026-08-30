# Toptoon Attendance 0.3.0

Browser sync requires a Home Assistant webhook automation.
The automation forwards `PHPSESSID` and `rm_session` to the App with
`hassio.addon_stdin`.

Do not put cookie values, webhook IDs, or session.json in a public repository.

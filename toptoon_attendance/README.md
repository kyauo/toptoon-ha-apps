# Toptoon Attendance Bot v0.5.0

Persistent-Chromium based Toptoon attendance automation for Home Assistant.

## v0.5.0
- Replaces manual PHPSESSID/rm_session management with a persistent Chromium profile.
- Login only through the Ingress VNC browser when Toptoon login expires.
- Daily attendance is executed inside the real logged-in browser context.
- Fast Ingress control/status UI with login check and manual attendance test.
- Existing retry, 09:05 failure alert, 21:00 manual reminder and mobile notifications retained.
- Includes KY red-circle icon and logo assets.

After upgrading, open the Web UI, choose **로그인 브라우저 열기**, sign in to Toptoon once, then close the browser. The profile remains under `/data/chromium-profile`.

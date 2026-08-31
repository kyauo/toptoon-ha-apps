# Changelog

## 0.5.5
- Added VNC-independent Facebook login assistant in the Ingress control UI.
- Selenium navigates to Toptoon, clicks Facebook login, fills credentials, and submits the form directly.
- Credentials are transient request data only; values are neither logged nor written to files.
- VNC remains available only for CAPTCHA, 2FA, device verification, or unexpected UI.
- Added timing logs for Toptoon navigation, Facebook handoff, and login submission to separate browser/network latency from VNC latency.
- Preserved persistent Chromium profile, schedules, retries, notifications, readiness checks, and KY branding.

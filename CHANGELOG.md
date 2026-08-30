# Changelog

## 0.4.1

- Added configured-local-time timestamp to every log line.
- Converted Ingress status timestamps from raw ISO strings to readable local time.
- Added automatic persistence of Toptoon-refreshed `PHPSESSID` and `rm_session` cookies.
- Added clearer initial-setup / expired-login recovery wording.
- Added an X close button to the Ingress input and result screens.
- Kept cookie values out of logs and rendered HTML.

## 0.4.0

- Added Home Assistant Ingress web UI for manual Toptoon session renewal.
- Added immediate attendance validation after saving a renewed session.
- Removed bookmarklet/webhook/STDIN session sync dependency.
- Updated failure messages to direct the user to the App web UI.
- Kept the existing daily schedule, retry, persistent notification, and morning mobile alert behavior.
- Fixed Dockerfile base image to `ghcr.io/home-assistant/base:latest`.

# Changelog

## 0.4.0

- Added Home Assistant Ingress web UI for manual Toptoon session renewal.
- Added immediate attendance validation after saving a renewed session.
- Removed bookmarklet/webhook/STDIN session sync dependency.
- Updated failure messages to direct the user to the App web UI.
- Kept the existing daily schedule, retry, persistent notification, and morning mobile alert behavior.
- Fixed Dockerfile base image to `ghcr.io/home-assistant/base:latest`.

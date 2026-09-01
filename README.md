# KY Home Assistant Apps — Toptoon Attendance Bot v0.5.14

v0.5.14는 Facebook MFA 경로를 기본 로그인에서 제외하고, Toptoon ID/비밀번호를 `/login/login_proc`에 직접 제출한 뒤 성공 쿠키를 persistent Chromium 세션에 저장하는 버전입니다. 인증 확인은 기존처럼 direct attendance AJAX 응답으로 판정합니다.

# Toptoon Attendance Bot v0.5.10

Persistent Chromium 세션으로 Toptoon 출석을 자동 처리합니다.

## v0.5.10
- `Facebook 로그인 화면 준비`에서 느린 `driver.get()`을 제거하고, 비차단 페이지 전환과 짧은 bounded wait를 사용합니다.
- 로그인 여부는 DOM/쿠키 추정이 아니라 Toptoon attendance AJAX 응답으로 판정합니다.
- 로그인 준비는 정상 경로에서 약 45초 이내에 끝나도록 제한합니다.
- Ingress 클라이언트가 먼저 끊겨도 `BrokenPipeError` traceback을 남기지 않습니다.
- 버전 표기를 config, DOCS, README, CHANGELOG에서 0.5.10로 통일했습니다.

## 로그인 갱신
평상시에는 빠른 Facebook 로그인 도우미를 사용합니다. Facebook 추가 인증/보안 확인이 필요한 경우에만 로그인 브라우저(VNC)를 사용하세요.

# Toptoon Attendance Bot v0.5.11

Persistent Chromium 세션으로 Toptoon 출석을 자동 처리합니다.

## v0.5.11
- Facebook 로그인 제출을 여러 Selenium DOM 호출 대신 단일 CDP 호출로 처리합니다.
- 제출 요청이 승인되면 UI에 즉시 반환하고, Toptoon 로그인 확인은 direct HTTP probe로 백그라운드에서 수행합니다.
- Facebook renderer의 URL/DOM 폴링을 제거해 로그인 제출 후 수분간 멈추는 현상을 피합니다.
- 출석 확인은 Chromium 쿠키를 CDP로 가져와 direct HTTP POST로 처리합니다.
- 버전 표기를 config, DOCS, README, CHANGELOG에서 0.5.11로 통일했습니다.

## 로그인 갱신
`Facebook 로그인 화면 준비` 후 ID와 비밀번호를 입력하고 제출합니다. 제출 직후 상태는 `확인 중`이 될 수 있으며, Toptoon 서버 인증이 확인되면 `로그인 유지됨`으로 갱신됩니다. Facebook 추가 인증 또는 보안 확인이 필요한 경우에만 VNC를 사용하세요.

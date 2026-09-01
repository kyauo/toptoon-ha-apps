# Toptoon Attendance Bot v0.5.12

Persistent Chromium 세션으로 Toptoon 출석을 자동 처리합니다.

## v0.5.12
- Facebook 로그인 제출 중복 요청을 서버 측 lock으로 차단합니다.
- 단일 CDP 제출 스크립트가 접근 가능한 frame의 로그인 입력칸까지 확인하고, 버튼이 없으면 form submit을 시도합니다.
- `rm_session` 같은 legacy cookie 존재만으로 로그인 성공을 추정하지 않습니다.
- 출석 확인은 Chromium 쿠키를 CDP로 가져와 direct HTTP POST로 처리합니다.
- 버전 표기를 config, DOCS, README, CHANGELOG에서 0.5.12로 통일했습니다.

## 로그인 갱신
`Facebook 로그인 화면 준비` 후 ID와 비밀번호를 입력하고 제출합니다. 제출 직후 상태는 `확인 중`이 될 수 있으며, Toptoon 서버 인증이 확인되면 `로그인 유지됨`으로 갱신됩니다. Facebook 추가 인증 또는 보안 확인이 필요한 경우에만 VNC를 사용하세요.

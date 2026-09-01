# Toptoon Attendance Bot v0.5.20

Persistent Chromium 세션으로 Toptoon 출석을 자동 처리합니다.

## v0.5.20
- 로그인 상태 확인 버튼이 Chromium/Selenium에 붙지 않고 저장된 최근 상태를 즉시 보여줍니다.
- 실제 Toptoon 서버 인증 확인은 출석 테스트로 확인하도록 UI 문구를 정리했습니다.
- Toptoon이 redirect HTML을 반환하고 출석 probe도 로그인 필요를 반환하면 `login_required` 상태를 저장합니다.
- Selenium `set_timeout` deprecation warning이 앱 로그를 어지럽히지 않도록 숨겼습니다.
- 버전 표기를 config, DOCS, README, CHANGELOG에서 0.5.20으로 통일했습니다.

## v0.5.19
- 시작 시 Supervisor API를 통해 저장된 legacy `phpsessid`, `rm_session` 옵션을 제거합니다.
- 두 legacy key는 migration 검증을 위해 schema에만 남기고 기본 options에는 더 이상 넣지 않습니다.
- cleanup 결과를 앱 로그에 남깁니다.
- 버전 표기를 config, DOCS, README, CHANGELOG에서 0.5.19로 통일했습니다.

## v0.5.18
- Toptoon ID 로그인 응답이 HTTP 200 `text/html`이어도 곧바로 실패하지 않고 direct attendance probe로 실제 로그인 여부를 확인합니다.
- JSON 성공 응답과 HTML 성공 응답 모두 같은 Chromium cookie persistence 경로를 사용합니다.
- HTML 응답 뒤에도 출석 probe가 로그인 필요를 반환하면 더 명확한 실패 메시지를 표시합니다.
- 버전 표기를 config, DOCS, README, CHANGELOG에서 0.5.18로 통일했습니다.

## v0.5.17
- Toptoon ID 로그인 응답이 HTTP 200이지만 JSON으로 바로 파싱되지 않는 경우 JSON 객체 복구 파싱을 시도합니다.
- JSON 파싱이 끝내 실패하면 content-type과 짧은 응답 앞부분을 로그에 남겨 다음 원인 분석이 가능하게 했습니다.
- 버전 표기를 config, DOCS, README, CHANGELOG에서 0.5.17로 통일했습니다.

## v0.5.16
- 과거 저장된 `phpsessid`, `rm_session` 옵션을 Supervisor validation 호환용으로만 다시 허용합니다.
- 해당 값들은 로그인이나 인증 판정에 사용하지 않습니다.
- 버전 표기를 config, DOCS, README, CHANGELOG에서 0.5.16으로 통일했습니다.

## v0.5.15
- 로그인 준비 단계가 Chromium을 건드리지 않고 즉시 반환합니다.
- Toptoon ID/비밀번호 로그인 성공 여부를 requests 세션의 direct attendance probe로 먼저 확인합니다.
- Chromium 세션 저장은 짧은 timeout으로만 시도해 느린 renderer가 로그인 결과를 가리지 않게 했습니다.
- 버전 표기를 config, DOCS, README, CHANGELOG에서 0.5.15로 통일했습니다.

## v0.5.14
- Facebook quick login 대신 Toptoon ID/비밀번호 직접 로그인을 사용합니다.
- `/login/login_proc`에 browser AJAX와 같은 형태로 `user_id`, `user_pw`, `ci_token`, 자동 로그인 옵션을 전송합니다.
- 로그인 성공 쿠키를 persistent Chromium profile에 반영한 뒤 direct attendance AJAX probe로 인증을 확인합니다.
- CAPTCHA 또는 계정 확인이 필요한 경우에는 로그인 브라우저에서 수동으로 처리합니다.
- 버전 표기를 config, DOCS, README, CHANGELOG에서 0.5.14로 통일했습니다.

## v0.5.13
- Facebook 로그인 준비 이동을 Chromium debug HTTP endpoint로 먼저 처리합니다.
- 자동 Facebook 제출이 renderer 대기에서 막히면 약 18초 안에 수동 로그인 브라우저 안내로 전환합니다.
- 자동 제출 실패 상태를 일반 요청 실패가 아니라 `manual_needed`로 기록합니다.
- 버전 표기를 config, DOCS, README, CHANGELOG에서 0.5.13으로 통일했습니다.

## v0.5.12
- Facebook 로그인 제출 중복 요청을 서버 측 lock으로 차단합니다.
- 단일 CDP 제출 스크립트가 접근 가능한 frame의 로그인 입력칸까지 확인하고, 버튼이 없으면 form submit을 시도합니다.
- `rm_session` 같은 legacy cookie 존재만으로 로그인 성공을 추정하지 않습니다.
- 출석 확인은 Chromium 쿠키를 CDP로 가져와 direct HTTP POST로 처리합니다.
- 버전 표기를 config, DOCS, README, CHANGELOG에서 0.5.12로 통일했습니다.

## 로그인 갱신
Toptoon ID와 비밀번호를 입력하고 제출합니다. 준비 버튼은 브라우저를 열지 않고 직접 로그인 준비 상태만 갱신합니다. Toptoon 서버 인증이 확인되면 `로그인 유지됨`으로 갱신됩니다. CAPTCHA 또는 추가 계정 확인이 필요한 경우에만 로그인 브라우저를 사용하세요.

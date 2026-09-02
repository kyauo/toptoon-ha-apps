# Toptoon Attendance Bot v0.5.29

Persistent Chromium 세션으로 Toptoon 출석을 자동 처리합니다.

## v0.5.29
- 다음 앱 재시작 때 persistent Chromium 프로필/캐시를 삭제하도록 예약하는 UI 버튼을 추가했습니다.
- 초기화 플래그가 있으면 시작 시 `/data/chromium-profile`을 삭제한 뒤 Chromium을 새로 띄웁니다.
- 초기화/시작 후 첫 Chromium 페이지를 `/event/attendance`로 바꿔 출석 페이지 기준으로 다시 테스트할 수 있게 했습니다.
- 로그인 화면 준비는 더 가벼운 Toptoon ID 로그인 URL과 `/robots.txt` redirect를 유지합니다.
- 버전 표기를 config, DOCS, README, CHANGELOG에서 0.5.29로 통일했습니다.

## v0.5.28
- Toptoon 홈(`/`)도 무거워서, 로그인 성공 후 redirect를 `/robots.txt`로 바꿨습니다.
- 가벼운 로그인 확인은 legacy cookie 이름을 믿지 않고, 로그인 URL을 요청했을 때 로그인 폼이 다시 나오는지로 판단합니다.
- v0.5.27의 브라우저 레벨 DevTools websocket 쿠키 읽기는 유지합니다.
- 버전 표기를 config, DOCS, README, CHANGELOG에서 0.5.28로 통일했습니다.

## v0.5.27
- Chromium 탭이 `Aw Snap` 상태로 죽어도 브라우저 프로세스의 DevTools websocket에서 쿠키를 읽도록 했습니다.
- 출석 테스트와 브라우저 쿠키 로그인 확인은 쿠키 복사 시 Selenium 탭 attach를 피합니다.
- 직접 DevTools websocket 접근을 위해 `websocket-client`를 앱 이미지에 추가했습니다.
- 버전 표기를 config, DOCS, README, CHANGELOG에서 0.5.27로 통일했습니다.

## v0.5.26
- 로그인 성공 직후 무거운 `/event/attendance` 페이지로 이동하지 않도록 브라우저 로그인 redirect를 `/`로 바꿨습니다.
- Chromium 화면이 느리거나 크래시되어도 CDP로 쿠키만 읽고 Toptoon 홈 HTML을 가볍게 요청해 로그인 여부를 확인하는 기능을 추가했습니다.
- 출석 요청 없이 브라우저 쿠키 로그인 상태를 확인하는 UI 버튼을 추가했습니다.
- 버전 표기를 config, DOCS, README, CHANGELOG에서 0.5.26으로 통일했습니다.

## v0.5.25
- Chromium/noVNC에서 까만 화면이 나올 수 있어 Xvfb를 640x480x8에서 640x480x16으로 되돌렸습니다.
- Chromium 창 위치를 0,0으로 고정해 VNC 화면 안에서 시작하도록 했습니다.
- 이미지 차단과 낮은 noVNC 품질은 유지해 세팅 브라우저 부담을 계속 낮췄습니다.
- 버전 표기를 config, DOCS, README, CHANGELOG에서 0.5.25로 통일했습니다.

## v0.5.24
- 가상 브라우저 화면을 1024x720x16에서 640x480x8로 낮춰 CPU와 VNC 렌더링 부담을 줄였습니다.
- Chromium 시작 페이지를 `about:blank` 대신 Toptoon ID 로그인 페이지로 바꿨습니다.
- 세팅 브라우저에서 이미지 로딩과 추가 백그라운드 기능을 끄도록 Chromium 옵션을 가볍게 조정했습니다.
- noVNC 품질을 낮추고 압축을 높여 원격 브라우저 표시 부담을 줄였습니다.
- 로그인 UI에 이미지가 의도적으로 꺼져 있음을 안내하도록 문구를 정리했습니다.
- 버전 표기를 config, DOCS, README, CHANGELOG에서 0.5.24로 통일했습니다.

## v0.5.23
- xdotool이 보이는 Chromium 창을 찾거나 활성화하지 못해도 remote debugging endpoint와 CDP navigation으로 Toptoon 로그인 페이지를 여는 fallback을 추가했습니다.
- Chromium 창 class 탐색 범위를 `chromium-browser`와 non-visible window까지 넓혔습니다.
- 세팅 중에는 하드코딩 좌표 자동 입력 대신 로그인 브라우저를 보면서 직접 로그인하는 흐름으로 바꿨습니다.
- 로그인 카드에서 VNC 브라우저 콘솔을 바로 열 수 있게 했습니다.
- 버전 표기를 config, DOCS, README, CHANGELOG에서 0.5.23으로 통일했습니다.

## v0.5.22
- Toptoon ID 로그인 제출을 HTTP 직접 요청 방식에서 실제 Chromium 브라우저 자동 입력 방식으로 바꿨습니다.
- 로그인 화면 준비 버튼이 Chromium에 실제 Toptoon ID 로그인 페이지를 엽니다.
- 로그인 제출 버튼은 가상 브라우저의 입력칸에 ID와 비밀번호를 붙여넣고 Enter를 보내며, 이후 백그라운드에서 Toptoon 인증 상태를 확인합니다.
- UI 문구를 브라우저 자동 입력 방식에 맞게 정리했습니다.
- `phpsessid`, `rm_session`은 Supervisor 검증 호환용 schema에만 남아 있고, 저장된 값은 시작 시 cleanup으로 제거합니다.
- 버전 표기를 config, DOCS, README, CHANGELOG에서 0.5.22로 통일했습니다.

## v0.5.21
- 저장된 로그인 상태가 이미 `login_required` 또는 `login_failed`이면 수동 출석 테스트가 Chromium 쿠키 확인을 건너뛰고 즉시 멈춥니다.
- Toptoon ID 로그인에서 redirect HTML이 반환되면 같은 세션으로 `/`를 따라가 `user_idx`와 Toptoon cookie 이름을 로그에 남깁니다.
- 자동 스케줄 출석은 기존 persistent Chromium 세션 회복 가능성을 위해 전체 브라우저 쿠키 경로를 유지합니다.
- 버전 표기를 config, DOCS, README, CHANGELOG에서 0.5.21로 통일했습니다.

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
준비 버튼은 Chromium에 실제 Toptoon ID 로그인 화면을 엽니다. 그 다음 로그인 브라우저를 열어 화면을 보면서 직접 ID와 비밀번호를 입력하고 로그인합니다. Toptoon 서버 인증이 확인되면 `로그인 유지됨`으로 갱신됩니다. CAPTCHA 또는 추가 계정 확인이 떠도 같은 브라우저 안에서 처리하면 됩니다.

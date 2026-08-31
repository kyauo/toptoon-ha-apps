# Toptoon Attendance Bot v0.5.6

- 출석 테스트와 자동 출석을 persistent Chromium 세션 하나로 통일했습니다.
- Selenium page load strategy를 `eager`로 바꾸고, 전체 페이지 로딩을 무한정 기다리지 않도록 bounded timeout + `window.stop()` 처리를 추가했습니다.
- 출석 POST는 현재 Toptoon 문서 안에서 `fetch(..., credentials: 'include')`로 실행합니다.
- 페이지에 `ci_token`이 있으면 실제 값을 사용하고, 없으면 기존 `null` 동작을 유지합니다.
- AJAX 응답의 `login_required`를 권위 있는 로그인 판정으로 취급해 UI 로그인 상태도 함께 갱신합니다.
- 수동 출석 실패 시 `오늘 출석`이 더 이상 `확인 안 함`에 머물지 않고 실패 원인을 표시합니다.
- 출석 단계별 timing 로그를 추가했습니다.

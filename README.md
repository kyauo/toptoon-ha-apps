# Toptoon Attendance Bot v0.5.6 bundle

`toptoon_attendance` 폴더 전체를 기존 GitHub 저장소의 같은 폴더에 덮어쓴 뒤 Home Assistant App Store에서 업데이트하세요.

이번 버전의 핵심은 로그인 확인과 실제 출석 요청이 서로 다른 인증 상태를 보지 않도록 persistent Chromium 세션 하나로 통일한 것입니다. 또한 Toptoon 페이지 전체 리소스 로딩을 오래 기다리지 않도록 조정했습니다.

업데이트 후에는 OPEN WEB UI에서 먼저 `지금 로그인 상태 확인`, 이어서 `지금 출석 테스트`를 한 번씩 실행하고 로그의 `Attendance:` 줄과 최종 결과를 확인하세요.

# Toptoon Attendance Bot v0.5.4

GitHub 저장소의 `toptoon_attendance` 폴더를 이 번들 내용으로 교체한 뒤 Home Assistant App을 새로고침하고 0.5.4로 업데이트합니다.

로그인 갱신 때는 **로그인 브라우저 열기**를 사용합니다. 아래 원격 Chromium에서 입력할 칸을 먼저 한 번 클릭한 뒤, 상단 입력창에 Mac 클립보드로 ID 또는 비밀번호를 붙여넣고 **선택 칸에 전송**을 누릅니다.


## v0.5.5
빠른 Facebook 로그인 도우미를 추가했습니다. 일반 로그인은 VNC 화면을 조작하지 않고 Selenium DOM 조작으로 진행하며, ID/비밀번호는 저장하거나 로그에 남기지 않습니다. Facebook 추가 인증/보안 확인이 나타날 때만 VNC를 사용합니다. 페이지 이동 단계별 소요 시간을 앱 로그에 기록합니다.

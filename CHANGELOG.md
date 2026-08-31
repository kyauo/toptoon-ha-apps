# Toptoon Attendance Bot v0.5.4

- 로그인 콘솔에 ID/비밀번호용 임시 텍스트 브리지를 추가했습니다.
- 입력 내용은 파일이나 앱 로그에 저장하지 않고 X11 클립보드에 잠시 넣은 뒤 현재 Chromium 입력칸에 Ctrl+V를 전송합니다.
- `xclip`, `xdotool`을 추가했습니다.
- x11vnc의 과도한 CPU 점유를 줄이기 위해 X DAMAGE를 다시 사용하고 `-wait 20 -defer 20 -nap`으로 조정했습니다.
- 로컬 HA 접속에서 CPU보다 대역폭을 더 쓰도록 noVNC compression을 1로 낮췄습니다.
- persistent Chromium profile, Ingress WebSocket 경로 수정, readiness 점검, 기존 스케줄/재시도/알림은 유지합니다.

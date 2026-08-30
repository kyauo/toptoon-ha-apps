import html
import json
import os
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs
from zoneinfo import ZoneInfo

import requests

OPTIONS_PATH = Path("/data/options.json")
STATUS_PATH = Path("/data/status.json")
SESSION_PATH = Path("/data/session.json")
TOPTOON_URL = "https://toptoon.com/event/attendance"
PERSISTENT_NOTIFICATION_ID = "toptoon_attendance_failure"
WEB_PORT = 8099
INGRESS_PROXY_IP = "172.30.32.2"

HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://toptoon.com",
    "Referer": "https://toptoon.com/event/attendance",
    "User-Agent": "Mozilla/5.0 Toptoon-HA/0.4.0",
}
DATA = {"ci_token": "null"}
OK_STATES = {"success", "already_done"}
ATTENDANCE_LOCK = threading.Lock()


def log(level, message):
    print(f"[{level}] {message}", flush=True)


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def load_options():
    return load_json(OPTIONS_PATH, {})


def load_status():
    return load_json(STATUS_PATH, {})


def save_status(**updates):
    status = load_status()
    status.update(updates)
    save_json(STATUS_PATH, status)


def now_local(options=None):
    options = options or load_options()
    tz = ZoneInfo(options.get("timezone", "Asia/Seoul"))
    return datetime.now(tz)


def current_cookies(options=None):
    options = options or load_options()
    session = load_json(SESSION_PATH, {})
    return {
        "PHPSESSID": session.get("phpsessid") or options.get("phpsessid", ""),
        "rm_session": session.get("rm_session") or options.get("rm_session", ""),
    }


def ha_service(domain, service, payload):
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        log("WARNING", "SUPERVISOR_TOKEN is missing.")
        return False
    url = f"http://supervisor/core/api/services/{domain}/{service}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:
        log("WARNING", f"Home Assistant service call failed: {e}")
        return False


def persistent_failure(message):
    if ha_service("persistent_notification", "create", {
        "notification_id": PERSISTENT_NOTIFICATION_ID,
        "title": "Toptoon 출석 실패",
        "message": message,
    }):
        log("INFO", "Persistent failure notification created.")


def dismiss_persistent_failure():
    ha_service("persistent_notification", "dismiss", {
        "notification_id": PERSISTENT_NOTIFICATION_ID
    })


def mobile_push(entity_id, title, message):
    payload = {"entity_id": entity_id, "message": message, "title": title}
    if ha_service("notify", "send_message", payload):
        log("INFO", f"Mobile notification sent to {entity_id}.")


def check_attendance(options=None):
    options = options or load_options()
    cookies = current_cookies(options)
    if not cookies["PHPSESSID"] or not cookies["rm_session"]:
        return "missing_session", "PHPSESSID 또는 rm_session이 없습니다."

    try:
        with ATTENDANCE_LOCK:
            r = requests.post(
                TOPTOON_URL,
                headers=HEADERS,
                cookies=cookies,
                data=DATA,
                timeout=20,
            )
        log("INFO", f"Toptoon HTTP {r.status_code}")
        r.raise_for_status()
    except requests.RequestException as e:
        return "network_error", str(e)

    try:
        body = r.json()
    except ValueError:
        return "invalid_response", f"JSON이 아닌 응답: {r.text[:300]}"

    if body.get("result") is True:
        return "success", body.get("message") or "출석 완료"

    message = str(body.get("message") or "")
    if "이미 출석" in message:
        return "already_done", message
    if body.get("errorType") == "login":
        return "login_expired", message or "로그인이 만료되었습니다."
    return "failed", message or json.dumps(body, ensure_ascii=False)[:300]


def store_session(phpsessid, rm_session, source="manual_ingress"):
    phpsessid = str(phpsessid or "").strip()
    rm_session = str(rm_session or "").strip()
    if len(phpsessid) < 5 or len(rm_session) < 5:
        return False, "두 세션 값을 모두 입력해 주세요."

    updated_at = now_local().isoformat(timespec="seconds")
    save_json(SESSION_PATH, {
        "phpsessid": phpsessid,
        "rm_session": rm_session,
        "updated_at": updated_at,
        "source": source,
    })
    save_status(session_updated_at=updated_at)
    log("INFO", f"Session updated manually at {updated_at}.")
    return True, updated_at


def test_after_session_update():
    state, message = check_attendance(load_options())
    checked_at = now_local().isoformat(timespec="seconds")
    updates = {
        "last_result": state,
        "last_message": message,
        "session_tested_at": checked_at,
    }
    if state in OK_STATES:
        updates.update({
            "last_run_date": now_local().date().isoformat(),
            "unresolved": False,
            "failure_date": None,
            "mobile_notified": False,
        })
        dismiss_persistent_failure()
    save_status(**updates)
    return state, message


def failure_instruction():
    return (
        "Home Assistant에서 Toptoon Attendance 앱의 웹 UI를 열고 "
        "새 PHPSESSID와 rm_session 값을 저장해 주세요. 저장 즉시 출석 상태를 다시 확인합니다."
    )


def run_with_retries(options, now):
    r1 = int(options.get("retry_1_minutes", 5))
    r2 = int(options.get("retry_2_minutes", 15))
    delays = [0, r1 * 60, max(0, (r2 - r1) * 60)]
    last_state, last_message = None, ""

    for attempt, delay in enumerate(delays):
        if delay:
            log("WARNING", f"Attempt failed ({last_state}); retry {attempt} in {delay // 60} minutes.")
            time.sleep(delay)

        options = load_options()
        check_time = now_local(options)
        log("INFO", f"Checking attendance at {check_time.isoformat(timespec='seconds')}")
        last_state, last_message = check_attendance(options)

        if last_state in OK_STATES:
            log("INFO", f"Attendance OK: {last_state} / {last_message}")
            dismiss_persistent_failure()
            save_status(
                last_run_date=check_time.date().isoformat(),
                last_result=last_state,
                last_message=last_message,
                unresolved=False,
                failure_date=None,
                mobile_notified=False,
            )
            return

    log("ERROR", f"Attendance failed after retries: {last_state}")
    if options.get("notify_on_failure", True):
        persistent_failure(
            "자동 출석과 재시도가 모두 실패했습니다.\n"
            f"상태: {last_state}\n내용: {last_message}\n\n{failure_instruction()}"
        )
    save_status(
        last_run_date=now.date().isoformat(),
        last_result=last_state,
        last_message=last_message,
        unresolved=True,
        failure_date=now.date().isoformat(),
        mobile_notified=False,
    )


def morning_recheck_and_notify(options, now):
    status = load_status()
    today = now.date().isoformat()
    if not status.get("unresolved") or status.get("failure_date") != today:
        return
    if status.get("mobile_notified"):
        return

    log("INFO", "Morning check: rechecking unresolved attendance failure.")
    state, message = check_attendance(options)
    if state in OK_STATES:
        log("INFO", f"Morning recheck recovered: {state}")
        dismiss_persistent_failure()
        save_status(
            last_result=state,
            last_message=message,
            unresolved=False,
            failure_date=None,
            mobile_notified=False,
        )
        return

    persistent_failure(
        "09:05 재확인에서도 Toptoon 출석이 실패했습니다.\n"
        f"상태: {state}\n내용: {message}\n\n{failure_instruction()}"
    )
    mobile_push(
        options.get("mobile_notify_entity", "notify.ky17"),
        "Toptoon 출석 실패",
        "09:05 재확인에서도 출석하지 못했습니다. HA의 Toptoon Attendance 웹 UI에서 세션을 갱신해 주세요.",
    )
    save_status(last_result=state, last_message=message, mobile_notified=True)


def within_minute(now, hhmm):
    hour, minute = [int(x) for x in hhmm.split(":")]
    return now.hour == hour and now.minute == minute


def result_label(state):
    return {
        "success": "출석 성공",
        "already_done": "이미 출석 완료",
        "login_expired": "로그인 만료",
        "missing_session": "세션 없음",
        "network_error": "네트워크 오류",
        "invalid_response": "응답 오류",
        "failed": "실패",
    }.get(state, state or "기록 없음")


def page_html(flash=None, flash_kind="info"):
    status = load_status()
    session = load_json(SESSION_PATH, {})
    updated_at = session.get("updated_at") or "아직 저장된 세션 없음"
    last_result = result_label(status.get("last_result"))
    last_message = status.get("last_message") or "아직 실행 기록 없음"
    tested_at = status.get("session_tested_at") or "-"
    flash_block = ""
    if flash:
        flash_block = f'<div class="flash {html.escape(flash_kind)}">{html.escape(flash)}</div>'

    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Toptoon Attendance</title>
<style>
:root {{ color-scheme: light dark; font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
body {{ margin:0; padding:24px; background:var(--primary-background-color,#fafafa); color:var(--primary-text-color,#222); }}
main {{ max-width:680px; margin:0 auto; }}
.card {{ background:var(--card-background-color,#fff); border-radius:14px; padding:20px; margin-bottom:16px; box-shadow:0 2px 10px rgba(0,0,0,.08); }}
h1 {{ font-size:24px; margin:0 0 8px; }}
h2 {{ font-size:18px; margin:0 0 12px; }}
p {{ line-height:1.55; }}
label {{ display:block; font-weight:600; margin:14px 0 6px; }}
input {{ box-sizing:border-box; width:100%; padding:12px; border:1px solid #8888; border-radius:9px; font:inherit; }}
button {{ width:100%; margin-top:18px; padding:13px; border:0; border-radius:9px; font:inherit; font-weight:700; cursor:pointer; background:#03a9f4; color:white; }}
.meta {{ display:grid; grid-template-columns:150px 1fr; gap:8px 12px; font-size:14px; }}
.meta strong {{ font-weight:650; }}
.flash {{ padding:13px; border-radius:9px; margin-bottom:16px; font-weight:600; }}
.flash.ok {{ background:#2e7d3230; }}
.flash.error {{ background:#c6282830; }}
.flash.info {{ background:#1565c030; }}
.note {{ font-size:13px; opacity:.78; }}
@media (max-width:520px) {{ body {{ padding:12px; }} .meta {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body><main>
<div class="card">
<h1>Toptoon Attendance</h1>
<p>자동 출석은 기존 일정대로 동작합니다. 로그인 세션이 만료됐을 때만 아래 두 값을 새로 저장하면 됩니다.</p>
</div>
{flash_block}
<div class="card">
<h2>현재 상태</h2>
<div class="meta">
<strong>세션 갱신 시각</strong><span>{html.escape(str(updated_at))}</span>
<strong>최근 결과</strong><span>{html.escape(str(last_result))}</span>
<strong>최근 메시지</strong><span>{html.escape(str(last_message))}</span>
<strong>수동 갱신 테스트</strong><span>{html.escape(str(tested_at))}</span>
</div>
</div>
<div class="card">
<h2>세션 갱신</h2>
<form method="post" action="">
<label for="phpsessid">PHPSESSID</label>
<input id="phpsessid" name="phpsessid" type="password" autocomplete="off" required>
<label for="rm_session">rm_session</label>
<input id="rm_session" name="rm_session" type="password" autocomplete="off" required>
<button type="submit">저장하고 즉시 출석 확인</button>
</form>
<p class="note">값은 Home Assistant App의 /data/session.json에만 저장되며 화면과 로그에는 표시하지 않습니다.</p>
</div>
<div class="card">
<h2>갱신 방법</h2>
<p>Toptoon에 정상 로그인한 뒤 브라우저의 쿠키 관리 화면에서 PHPSESSID와 rm_session 값을 복사해 위 칸에 붙여 넣으세요. 저장하면 이 App이 즉시 출석 요청을 보내 새 세션이 유효한지 확인합니다.</p>
</div>
</main></body></html>"""


class IngressHandler(BaseHTTPRequestHandler):
    server_version = "ToptoonAttendance/0.4.0"

    def log_message(self, fmt, *args):
        log("WEB", fmt % args)

    def ingress_only(self):
        # Home Assistant Ingress proxy is the intended and only entry point.
        # When the runtime reports another source IP, reject direct access.
        client_ip = self.client_address[0]
        if client_ip != INGRESS_PROXY_IP:
            log("WARNING", f"Rejected non-Ingress web request from {client_ip}.")
            self.send_response(403)
            self.end_headers()
            return False
        return True

    def send_page(self, content, status=200):
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.ingress_only():
            return
        self.send_page(page_html())

    def do_POST(self):
        if not self.ingress_only():
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0 or length > 16384:
            self.send_page(page_html("잘못된 요청입니다.", "error"), 400)
            return
        raw = self.rfile.read(length).decode("utf-8", "replace")
        form = parse_qs(raw, keep_blank_values=True)
        phpsessid = (form.get("phpsessid") or [""])[0]
        rm_session = (form.get("rm_session") or [""])[0]

        ok, detail = store_session(phpsessid, rm_session)
        if not ok:
            self.send_page(page_html(detail, "error"), 400)
            return

        state, message = test_after_session_update()
        if state in OK_STATES:
            flash = f"세션 저장 완료. 즉시 확인 결과: {result_label(state)} — {message}"
            kind = "ok"
        else:
            flash = f"세션은 저장했지만 즉시 확인에 실패했습니다: {result_label(state)} — {message}"
            kind = "error"
        self.send_page(page_html(flash, kind))


def start_web_server():
    server = ThreadingHTTPServer(("0.0.0.0", WEB_PORT), IngressHandler)
    thread = threading.Thread(target=server.serve_forever, name="ingress-web", daemon=True)
    thread.start()
    log("INFO", f"Ingress session-renewal UI listening on port {WEB_PORT}.")
    return server


def main():
    options = load_options()
    start_web_server()
    log(
        "INFO",
        f"Daily attendance: {options.get('run_time','00:30')} "
        f"({options.get('timezone','Asia/Seoul')}); "
        f"retries +{options.get('retry_1_minutes',5)}m/+{options.get('retry_2_minutes',15)}m; "
        f"mobile alert check: {options.get('mobile_alert_time','09:05')}"
    )
    log("INFO", "Manual session renewal is available through Home Assistant Ingress.")

    if options.get("run_on_start", False):
        run_with_retries(options, now_local(options))

    while True:
        options = load_options()
        now = now_local(options)
        today = now.date().isoformat()
        status = load_status()

        if within_minute(now, options.get("run_time", "00:30")):
            if status.get("last_run_date") != today:
                run_with_retries(options, now)

        status = load_status()
        if within_minute(now, options.get("mobile_alert_time", "09:05")):
            if status.get("morning_check_date") != today:
                morning_recheck_and_notify(options, now)
                save_status(morning_check_date=today)

        time.sleep(1)


if __name__ == "__main__":
    main()

import json
import os
import select
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

OPTIONS_PATH = Path("/data/options.json")
STATUS_PATH = Path("/data/status.json")
SESSION_PATH = Path("/data/session.json")
TOPTOON_URL = "https://toptoon.com/event/attendance"
PERSISTENT_NOTIFICATION_ID = "toptoon_attendance_failure"

HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://toptoon.com",
    "Referer": "https://toptoon.com/event/attendance",
    "User-Agent": "Mozilla/5.0 Toptoon-HA/0.3.0",
}
DATA = {"ci_token": "null"}
OK_STATES = {"success", "already_done"}


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


def current_cookies(options):
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
    if ha_service("persistent_notification", "dismiss", {
        "notification_id": PERSISTENT_NOTIFICATION_ID
    }):
        log("INFO", "Persistent failure notification dismissed.")


def mobile_push(entity_id, title, message):
    # REST service-call body is service data, not the automation target/data wrapper.
    payload = {"entity_id": entity_id, "message": message, "title": title}
    if ha_service("notify", "send_message", payload):
        log("INFO", f"Mobile notification sent to {entity_id}.")


def notify_session_updated(updated_at):
    ha_service("persistent_notification", "create", {
        "notification_id": "toptoon_session_updated",
        "title": "Toptoon 세션 갱신",
        "message": f"브라우저에서 새 로그인 세션을 받았습니다.\n갱신 시각: {updated_at}",
    })


def update_session(payload):
    phpsessid = str(payload.get("phpsessid") or "").strip()
    rm_session = str(payload.get("rm_session") or "").strip()
    if len(phpsessid) < 5 or len(rm_session) < 5:
        log("WARNING", "Session sync rejected: cookie value missing or too short.")
        return

    options = load_options()
    tz = ZoneInfo(options.get("timezone", "Asia/Seoul"))
    updated_at = datetime.now(tz).isoformat(timespec="seconds")
    save_json(SESSION_PATH, {
        "phpsessid": phpsessid,
        "rm_session": rm_session,
        "updated_at": updated_at,
        "source": "browser_bookmarklet",
    })
    save_status(session_updated_at=updated_at)
    log("INFO", f"Browser session updated at {updated_at}.")
    notify_session_updated(updated_at)


def poll_stdin():
    try:
        ready, _, _ = select.select([sys.stdin], [], [], 0)
    except Exception:
        return
    if not ready:
        return
    line = sys.stdin.readline()
    if not line:
        return
    try:
        payload = json.loads(line.strip())
    except Exception:
        log("WARNING", "Ignoring invalid stdin input.")
        return

    if payload.get("action") == "update_session":
        update_session(payload)
    else:
        log("WARNING", f"Unknown stdin action: {payload.get('action')}")


def check_attendance(options):
    cookies = current_cookies(options)
    if not cookies["PHPSESSID"] or not cookies["rm_session"]:
        return "missing_session", "PHPSESSID 또는 rm_session이 없습니다."

    try:
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


def sleep_with_stdin(seconds):
    end = time.time() + seconds
    while time.time() < end:
        poll_stdin()
        time.sleep(1)


def run_with_retries(options, now):
    r1 = int(options.get("retry_1_minutes", 5))
    r2 = int(options.get("retry_2_minutes", 15))
    delays = [0, r1 * 60, max(0, (r2 - r1) * 60)]
    last_state, last_message = None, ""

    for attempt, delay in enumerate(delays):
        if delay:
            log("WARNING", f"Attempt failed ({last_state}); retry {attempt} in {delay // 60} minutes.")
            sleep_with_stdin(delay)

        options = load_options()
        tz = ZoneInfo(options.get("timezone", "Asia/Seoul"))
        check_time = datetime.now(tz)
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
            f"상태: {last_state}\n내용: {last_message}\n"
            "탑툰에 다시 로그인한 뒤 '탑툰 세션전송' 북마크를 실행해 주세요."
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
        f"상태: {state}\n내용: {message}\n"
        "탑툰에 로그인한 뒤 '탑툰 세션전송' 북마크를 실행해 주세요."
    )
    mobile_push(
        options.get("mobile_notify_entity", "notify.ky17"),
        "Toptoon 출석 실패",
        "09:05 재확인에서도 출석하지 못했습니다. 탑툰에 로그인한 뒤 '탑툰 세션전송' 북마크를 실행해 주세요.",
    )
    save_status(last_result=state, last_message=message, mobile_notified=True)


def within_minute(now, hhmm):
    hour, minute = [int(x) for x in hhmm.split(":")]
    return now.hour == hour and now.minute == minute


def main():
    options = load_options()
    log(
        "INFO",
        f"Daily attendance: {options.get('run_time','00:30')} "
        f"({options.get('timezone','Asia/Seoul')}); "
        f"retries +{options.get('retry_1_minutes',5)}m/+{options.get('retry_2_minutes',15)}m; "
        f"mobile alert check: {options.get('mobile_alert_time','09:05')}"
    )
    log("INFO", "Browser session sync via app STDIN is enabled.")

    if options.get("run_on_start", False):
        tz = ZoneInfo(options.get("timezone", "Asia/Seoul"))
        run_with_retries(options, datetime.now(tz))

    while True:
        poll_stdin()
        options = load_options()
        tz = ZoneInfo(options.get("timezone", "Asia/Seoul"))
        now = datetime.now(tz)
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

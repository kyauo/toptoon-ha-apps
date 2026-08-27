\
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

OPTIONS_PATH = Path("/data/options.json")
STATUS_PATH = Path("/data/status.json")
TOPTOON_URL = "https://toptoon.com/event/attendance"
PERSISTENT_NOTIFICATION_ID = "toptoon_attendance_failure"

HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://toptoon.com",
    "Referer": "https://toptoon.com/event/attendance",
}
DATA = {"ci_token": "null"}

OK_STATES = {"success", "already_done"}


def log(level: str, message: str) -> None:
    print(f"[{level}] {message}", flush=True)


def load_options() -> dict:
    return json.loads(OPTIONS_PATH.read_text(encoding="utf-8"))


def load_status() -> dict:
    if not STATUS_PATH.exists():
        return {}
    try:
        return json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_status(payload: dict) -> None:
    STATUS_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def ha_service(domain: str, service: str, payload: dict) -> bool:
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        log("WARNING", "SUPERVISOR_TOKEN unavailable; HA notification skipped.")
        return False

    url = f"http://supervisor/core/api/services/{domain}/{service}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        r.raise_for_status()
        return True
    except requests.RequestException as exc:
        log("WARNING", f"Home Assistant service call failed: {exc}")
        return False


def persistent_failure(message: str) -> None:
    ok = ha_service(
        "persistent_notification",
        "create",
        {
            "notification_id": PERSISTENT_NOTIFICATION_ID,
            "title": "탑툰 출석체크 실패",
            "message": message,
        },
    )
    if ok:
        log("INFO", "Persistent failure notification created.")


def dismiss_persistent_failure() -> None:
    ha_service(
        "persistent_notification",
        "dismiss",
        {"notification_id": PERSISTENT_NOTIFICATION_ID},
    )


def mobile_push(entity_id: str, title: str, message: str) -> None:
    ok = ha_service(
        "notify",
        "send_message",
        {
            "target": {"entity_id": entity_id},
            "data": {
                "title": title,
                "message": message,
            },
        },
    )
    if ok:
        log("INFO", f"Mobile notification sent to {entity_id}.")


def check_attendance(options: dict) -> dict:
    now = datetime.now(ZoneInfo(options["timezone"]))
    cookies = {
        "PHPSESSID": options["phpsessid"],
        "rm_session": options["rm_session"],
    }

    log("INFO", f"Checking attendance at {now.isoformat(timespec='seconds')}")

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
    except requests.RequestException as exc:
        return {
            "time": now.isoformat(),
            "state": "network_error",
            "detail": str(exc),
        }

    try:
        result = r.json()
    except ValueError:
        return {
            "time": now.isoformat(),
            "state": "unexpected_response",
            "http_status": r.status_code,
            "detail": r.text[:300].replace("\n", " "),
        }

    message = str(result.get("message", ""))

    if result.get("result") is True:
        return {"time": now.isoformat(), "state": "success", "response": result}

    if "이미 출석" in message:
        return {"time": now.isoformat(), "state": "already_done", "response": result}

    if result.get("errorType") == "login":
        return {"time": now.isoformat(), "state": "login_expired", "response": result}

    return {"time": now.isoformat(), "state": "other_error", "response": result}


def describe_failure(result: dict) -> str:
    state = result.get("state")
    if state == "login_expired":
        return (
            "탑툰 로그인 세션이 만료되었습니다. 브라우저에서 다시 로그인한 뒤 "
            "App 설정의 PHPSESSID와 rm_session 값을 갱신해주세요."
        )
    if state == "network_error":
        return f"탑툰 접속 중 네트워크 오류가 발생했습니다: {result.get('detail', '')}"
    if state == "unexpected_response":
        return "탑툰이 예상하지 못한 응답을 반환했습니다. 사이트 변경 또는 일시 장애를 확인해주세요."
    return f"탑툰 출석체크가 완료되지 않았습니다. 상태: {state}"


def hm_today(now: datetime, hm: str) -> datetime:
    hour, minute = map(int, hm.split(":"))
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)


def next_daily(now: datetime, hm: str) -> datetime:
    target = hm_today(now, hm)
    if target <= now:
        target += timedelta(days=1)
    return target


def validate(options: dict) -> None:
    for key in (
        "phpsessid",
        "rm_session",
        "run_time",
        "timezone",
        "mobile_alert_time",
        "mobile_notify_entity",
    ):
        if not options.get(key):
            raise ValueError(f"Required option is missing: {key}")
    ZoneInfo(options["timezone"])
    r1 = int(options["retry_1_minutes"])
    r2 = int(options["retry_2_minutes"])
    if r2 <= r1:
        raise ValueError("retry_2_minutes must be greater than retry_1_minutes")


def run_with_retries(options: dict) -> dict:
    first = check_attendance(options)
    save_status(first)
    if first["state"] in OK_STATES:
        log("INFO", f"Attendance state: {first['state']}")
        dismiss_persistent_failure()
        return first

    delays = [
        int(options["retry_1_minutes"]),
        int(options["retry_2_minutes"]) - int(options["retry_1_minutes"]),
    ]

    result = first
    for idx, delay_minutes in enumerate(delays, start=1):
        log("WARNING", f"Attempt failed ({result['state']}); retry {idx} in {delay_minutes} minutes.")
        time.sleep(delay_minutes * 60)
        options = load_options()
        validate(options)
        result = check_attendance(options)
        save_status(result)
        if result["state"] in OK_STATES:
            log("INFO", f"Retry succeeded: {result['state']}")
            dismiss_persistent_failure()
            return result

    log("ERROR", f"Attendance failed after retries: {result['state']}")
    if options.get("notify_on_failure", True):
        persistent_failure(describe_failure(result))

    final = dict(result)
    final["unresolved"] = True
    final["failure_date"] = datetime.now(ZoneInfo(options["timezone"])).date().isoformat()
    save_status(final)
    return final


def morning_recheck_and_notify(options: dict) -> None:
    tz = ZoneInfo(options["timezone"])
    now = datetime.now(tz)
    status = load_status()

    if not status.get("unresolved"):
        log("INFO", "Morning check: no unresolved failure.")
        return

    if status.get("failure_date") != now.date().isoformat():
        log("INFO", "Morning check: unresolved failure is not from today.")
        return

    log("INFO", "Morning check: rechecking unresolved attendance failure.")
    result = check_attendance(options)
    save_status(result)

    if result["state"] in OK_STATES:
        log("INFO", "Morning recheck succeeded; no mobile notification needed.")
        dismiss_persistent_failure()
        return

    message = describe_failure(result)
    persistent_failure(message)
    mobile_push(
        options["mobile_notify_entity"],
        "탑툰 출석체크 확인 필요",
        message,
    )

    result["unresolved"] = True
    result["failure_date"] = now.date().isoformat()
    result["mobile_notified"] = True
    save_status(result)


def main() -> None:
    try:
        options = load_options()
        validate(options)
    except Exception as exc:
        log("ERROR", f"Invalid configuration: {exc}")
        sys.exit(1)

    tz = ZoneInfo(options["timezone"])
    log(
        "INFO",
        f"Daily attendance: {options['run_time']} ({options['timezone']}); "
        f"retries +{options['retry_1_minutes']}m/+{options['retry_2_minutes']}m; "
        f"mobile alert check: {options['mobile_alert_time']}"
    )

    if options.get("run_on_start", False):
        result = check_attendance(options)
        save_status(result)
        log("INFO", f"Startup test result: {result['state']}")

    last_daily_date = None
    last_morning_date = None

    while True:
        options = load_options()
        try:
            validate(options)
        except Exception as exc:
            log("ERROR", f"Invalid configuration: {exc}")
            time.sleep(60)
            continue

        tz = ZoneInfo(options["timezone"])
        now = datetime.now(tz)
        today = now.date().isoformat()

        daily_target = hm_today(now, options["run_time"])
        morning_target = hm_today(now, options["mobile_alert_time"])

        # A 60-second execution window makes the scheduler tolerant of loop timing.
        if (
            0 <= (now - daily_target).total_seconds() < 60
            and last_daily_date != today
        ):
            last_daily_date = today
            run_with_retries(options)

        if (
            0 <= (now - morning_target).total_seconds() < 60
            and last_morning_date != today
        ):
            last_morning_date = today
            morning_recheck_and_notify(options)

        time.sleep(15)


if __name__ == "__main__":
    main()

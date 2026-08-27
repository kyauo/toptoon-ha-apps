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

HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://toptoon.com",
    "Referer": "https://toptoon.com/event/attendance",
}

DATA = {"ci_token": "null"}


def log(level: str, message: str) -> None:
    print(f"[{level}] {message}", flush=True)


def load_options() -> dict:
    try:
        return json.loads(OPTIONS_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        log("ERROR", f"Could not read {OPTIONS_PATH}: {exc}")
        raise


def save_status(payload: dict) -> None:
    try:
        STATUS_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as exc:
        log("WARNING", f"Could not write status file: {exc}")


def persistent_notification(title: str, message: str) -> None:
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        log("WARNING", "SUPERVISOR_TOKEN is unavailable; notification skipped.")
        return

    url = "http://supervisor/core/api/services/persistent_notification/create"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {"title": title, "message": message}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        log("INFO", "Home Assistant persistent notification created.")
    except requests.RequestException as exc:
        log("WARNING", f"Could not create Home Assistant notification: {exc}")


def check_attendance(options: dict) -> str:
    cookies = {
        "PHPSESSID": options["phpsessid"],
        "rm_session": options["rm_session"],
    }

    now = datetime.now(ZoneInfo(options["timezone"]))
    log("INFO", f"Checking attendance at {now.isoformat(timespec='seconds')}")

    try:
        response = requests.post(
            TOPTOON_URL,
            headers=HEADERS,
            cookies=cookies,
            data=DATA,
            timeout=20,
        )
        log("INFO", f"Toptoon HTTP {response.status_code}")
        response.raise_for_status()
    except requests.RequestException as exc:
        log("ERROR", f"Network/HTTP error: {exc}")
        save_status(
            {
                "time": now.isoformat(),
                "state": "network_error",
                "detail": str(exc),
            }
        )
        return "network_error"

    try:
        result = response.json()
    except ValueError:
        snippet = response.text[:300].replace("\n", " ")
        log("ERROR", f"Toptoon returned non-JSON data: {snippet}")
        save_status(
            {
                "time": now.isoformat(),
                "state": "unexpected_response",
                "http_status": response.status_code,
            }
        )
        return "unexpected_response"

    message = str(result.get("message", ""))

    if result.get("result") is True:
        log("INFO", f"Attendance succeeded. Response: {result}")
        save_status(
            {
                "time": now.isoformat(),
                "state": "success",
                "response": result,
            }
        )
        return "success"

    if "이미 출석" in message:
        log("INFO", "Attendance was already completed today.")
        save_status(
            {
                "time": now.isoformat(),
                "state": "already_done",
                "response": result,
            }
        )
        return "already_done"

    if result.get("errorType") == "login":
        log("ERROR", "Toptoon login session has expired.")
        save_status(
            {
                "time": now.isoformat(),
                "state": "login_expired",
                "response": result,
            }
        )
        if options.get("notify_on_login_expiry", True):
            persistent_notification(
                "탑툰 출석체크",
                "로그인 세션이 만료되었습니다. Toptoon에 다시 로그인한 뒤 "
                "PHPSESSID와 rm_session 값을 App 설정에서 갱신해주세요.",
            )
        return "login_expired"

    log("WARNING", f"Unhandled Toptoon response: {result}")
    save_status(
        {
            "time": now.isoformat(),
            "state": "other_error",
            "response": result,
        }
    )
    return "other_error"


def next_run(now: datetime, run_time: str) -> datetime:
    hour, minute = map(int, run_time.split(":"))
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target


def validate_options(options: dict) -> None:
    for key in ("phpsessid", "rm_session", "run_time", "timezone"):
        if not options.get(key):
            raise ValueError(f"Required option is missing: {key}")

    ZoneInfo(options["timezone"])


def main() -> None:
    options = load_options()

    try:
        validate_options(options)
    except Exception as exc:
        log("ERROR", f"Invalid configuration: {exc}")
        sys.exit(1)

    tz = ZoneInfo(options["timezone"])
    log(
        "INFO",
        f"Schedule: every day at {options['run_time']} "
        f"({options['timezone']})",
    )

    if options.get("run_on_start", False):
        check_attendance(options)

    while True:
        now = datetime.now(tz)
        target = next_run(now, options["run_time"])
        wait_seconds = max(1, int((target - now).total_seconds()))

        log(
            "INFO",
            f"Next run: {target.isoformat(timespec='minutes')} "
            f"({wait_seconds // 60} minutes from now)",
        )

        # Wake periodically so an app restart/config update doesn't leave
        # a very long uninterruptible sleep.
        while wait_seconds > 0:
            sleep_for = min(wait_seconds, 300)
            time.sleep(sleep_for)
            wait_seconds -= sleep_for

        # Reload options at each scheduled run so changed credentials or
        # scheduling options take effect after an app restart/update.
        options = load_options()
        try:
            validate_options(options)
        except Exception as exc:
            log("ERROR", f"Invalid configuration: {exc}")
            time.sleep(60)
            continue

        tz = ZoneInfo(options["timezone"])
        check_attendance(options)


if __name__ == "__main__":
    main()

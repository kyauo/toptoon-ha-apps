# Toptoon Attendance for Home Assistant

A small Home Assistant App that performs the same attendance POST request
confirmed from a logged-in Toptoon browser session.

## What it does

- Runs once per day at the configured time.
- Sends `POST https://toptoon.com/event/attendance`.
- Uses only the two session cookies confirmed to be required:
  - `PHPSESSID`
  - `rm_session`
- Treats "already attended" as a normal result.
- Detects `errorType: login` as session expiry.
- Can create a Home Assistant persistent notification when the login session expires.
- Stores the last result in `/data/status.json`.

## Security

Do not commit real cookie values into Git.
Enter them only in the Home Assistant App configuration UI.
The schema marks both values as `password`.

## Local installation on Home Assistant OS

1. Install or use an App that gives access to the local `/addons` directory,
   such as Samba or SSH.
2. Copy the entire `toptoon_attendance` folder into:

   `/addons/toptoon_attendance`

3. In Home Assistant, open the App store and refresh/check for updates.
4. Find `Toptoon Attendance` under Local Apps and install it.
5. Open its Configuration tab and enter:
   - `phpsessid`
   - `rm_session`
   - desired `run_time`
   - `timezone` (default `Asia/Seoul`)
6. For the first test, temporarily set `run_on_start: true`.
7. Start the App and inspect its Log.
8. Once the test succeeds, set `run_on_start: false` and restart the App.

## Expected test result

If today's attendance is already complete, the log should contain:

`Attendance was already completed today.`

If the session has expired, the log should contain:

`Toptoon login session has expired.`

and, if enabled, Home Assistant will receive a persistent notification.

## Updating expired cookies

When Toptoon asks you to log in again:

1. Log in normally in your browser.
2. Open Developer Tools -> Application -> Cookies -> `https://toptoon.com`.
3. Copy the current values for `PHPSESSID` and `rm_session`.
4. Replace the two values in this App's Configuration.
5. Restart the App.

No Facebook password is stored in this App.

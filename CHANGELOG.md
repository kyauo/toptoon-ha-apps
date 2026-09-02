# Toptoon Attendance Bot v0.5.37

## v0.5.37
- Added a `로그인 페이지 열기` button inside the VNC login console so users can open the Toptoon login page after the lightweight parked browser loads.
- Updated login console instructions to clarify that the top text field is a secure paste helper for the selected field inside the remote Chromium page.
- Added Chromium `--test-type` to suppress the unsupported `--no-sandbox` warning banner while keeping `--no-sandbox` for root container startup.
- Synchronized visible version strings to 0.5.37.

## v0.5.36
- Changed Chromium startup from the heavy Toptoon attendance page to a tiny local data URL so VNC refresh/reconnect is much faster.
- Updated browser reset messaging to say the next restart begins from the lightweight waiting page.
- Toptoon pages are now opened only on demand through login preparation or direct manual navigation.
- Synchronized visible version strings to 0.5.36.

## v0.5.35
- Restored Chromium `--no-sandbox` because the Home Assistant container runs Chromium as root and Chromium refuses to start without it.
- Restored `--no-zygote` together with `--no-sandbox`; Chromium only allows disabling zygote when sandboxing is disabled.
- Fixes Chromium failing to open the remote debugging port with `Running as root without --no-sandbox is not supported`.
- Synchronized visible version strings to 0.5.35.

## v0.5.34
- Removed Chromium `--no-zygote` because it cannot be used while sandboxing is enabled.
- Fixes Chromium failing to open the remote debugging port with `Zygote cannot be disabled if sandbox is enabled`.
- Kept the v0.5.33 V8 heap increase to 192MB.
- Synchronized visible version strings to 0.5.34.

## v0.5.33
- Increased Chromium V8 old-space limit from 64MB to 192MB so Toptoon page JavaScript has more room before renderer crashes.
- Kept the 640x480x16 display and single renderer process while testing whether the previous JS heap limit was too tight.
- Synchronized visible version strings to 0.5.33.

## v0.5.32
- Removed the unsupported Chromium `--no-sandbox` flag from the app startup command.
- Kept the v0.5.31 low-memory Chromium flags unchanged.
- Synchronized visible version strings to 0.5.32.

## v0.5.31
- Added lower-memory Chromium flags for `Aw Snap! Error code: 9` renderer crashes.
- Reduced renderer process limit from 2 to 1 and disabled zygote, breakpad, crash reporting, site isolation, isolated origins, and out-of-process audio service.
- Added a small V8 old-space limit for the setup browser.
- Kept the 640x480x16 display instead of increasing resolution, because more pixels would raise memory pressure.
- Synchronized visible version strings to 0.5.31.

## v0.5.30
- Normalize Chromium profile preferences before startup so `exit_type` is `Normal` and `exited_cleanly` is true.
- Added Chromium flags to suppress session crash restore prompts and error dialogs.
- Kept the profile reset flag workflow from v0.5.29 for clearing corrupted browser state on the next app restart.
- Synchronized visible version strings to 0.5.30.

## v0.5.29
- Added a UI action to schedule a persistent Chromium profile/cache reset on the next app restart.
- When the reset flag is present, startup removes `/data/chromium-profile` before launching Chromium.
- Changed the initial Chromium startup page to `/event/attendance` after reset/startup so testing can begin from the attendance page.
- Kept login preparation on the lighter Toptoon ID login URL with `/robots.txt` redirect.
- Synchronized visible version strings to 0.5.29.

## v0.5.28
- Changed the browser login redirect from `/` to `/robots.txt` because the Toptoon home page is heavier than the login setup browser can reliably render.
- The lightweight login check now probes the login URL and treats a returned login form as login-required instead of trusting legacy cookie names.
- Kept browser-level DevTools websocket cookie reading from v0.5.27 for crashed-tab recovery.
- Synchronized visible version strings to 0.5.28.

## v0.5.27
- Added browser-level Chromium DevTools websocket cookie reading so a crashed renderer tab does not block login checks or attendance tests.
- Attendance tests and browser-cookie login checks now avoid Selenium tab attachment when copying cookies from persistent Chromium.
- Added `websocket-client` to the app image for direct DevTools websocket access.
- Synchronized visible version strings to 0.5.27.

## v0.5.26
- Changed the browser login redirect from `/event/attendance` to `/` so a successful login does not immediately load the heavy attendance page.
- Added a browser-cookie login check action that reads Chromium cookies through CDP and verifies login with a lightweight Toptoon home HTML request.
- Added a UI button for checking browser-cookie login state without rendering the heavy attendance page or submitting attendance.
- Synchronized visible version strings to 0.5.26.

## v0.5.25
- Changed the lightweight Xvfb display from 640x480x8 to 640x480x16 because 8-bit color can render as a black screen in Chromium/noVNC.
- Pinned the Chromium window position to 0,0 so the browser starts inside the visible VNC canvas.
- Kept image loading disabled and noVNC quality low for the lighter setup browser.
- Synchronized visible version strings to 0.5.25.

## v0.5.24
- Reduced the virtual browser from 1024x720x16 to 640x480x8 to lower CPU and VNC rendering load.
- Start Chromium on the Toptoon ID login page instead of `about:blank`.
- Disabled image loading and more background Chromium features for the setup browser.
- Lowered noVNC quality and increased compression for lighter remote browser viewing.
- Updated UI copy to explain that images are intentionally disabled during login setup.
- Synchronized visible version strings to 0.5.24.

## v0.5.23
- Added Chromium login-page preparation fallback through the remote debugging endpoint and CDP navigation when xdotool cannot find or activate the visible Chromium window.
- Broadened Chromium xdotool window matching to include `chromium-browser` class names and non-visible search fallback.
- Switched the setup flow to manual visible-browser login instead of hardcoded coordinate credential typing.
- The login card now opens the VNC browser console directly so account prompts, CAPTCHA, and field placement can be handled visibly.
- Synchronized visible version strings to 0.5.23.

## v0.5.22
- Changed Toptoon ID login submission from direct HTTP POST to real Chromium browser input using the virtual display, clipboard, and keyboard events.
- The login preparation button now opens the actual Toptoon ID login page in Chromium.
- Background verification still checks Toptoon authentication after the browser submits the form.
- Updated UI copy to distinguish browser-input login from the earlier direct-request login path.
- Kept legacy `phpsessid` and `rm_session` schema compatibility while startup cleanup removes stored values from Supervisor options.
- Synchronized visible version strings to 0.5.22.

## v0.5.21
- Manual attendance test now skips the slow browser-cookie path immediately when the saved login state is already `login_required` or `login_failed`.
- Added redirect-HTML diagnostics for Toptoon ID login, following `/` with the same session and logging `user_idx` plus Toptoon cookie names.
- Kept scheduled attendance checks on the full browser-cookie path so existing persistent sessions can still recover automatically.
- Synchronized visible version strings to 0.5.21.

## v0.5.20
- Changed the login status button to a fast saved-state check so it no longer attaches to slow Chromium/Selenium.
- Clarified in the UI that actual server authentication should be checked with the attendance test.
- Records `login_required` when Toptoon returns redirect HTML and the follow-up attendance probe still reports login required.
- Suppressed Selenium `set_timeout` deprecation noise while keeping short command timeouts.
- Synchronized visible version strings to 0.5.20.

## v0.5.19
- Added startup migration that removes stored legacy `phpsessid` and `rm_session` options from Supervisor's saved app configuration through the Supervisor options API.
- Kept the legacy keys in schema only, without default option values, so old saved configs validate during migration but new defaults no longer recreate them.
- Logs whether legacy option cleanup removed values, found nothing to remove, or could not reach the Supervisor API.
- Synchronized visible version strings to 0.5.19.

## v0.5.18
- Treat HTTP 200 `text/html` login responses as potentially successful and verify them with the direct attendance probe before failing.
- Share Chromium cookie persistence through one helper for JSON-success and HTML-success login flows.
- Return clearer messages when Toptoon returns an HTML response but the follow-up auth probe still reports login required.
- Synchronized visible version strings to 0.5.18.

## v0.5.17
- Added resilient login response parsing that can recover a JSON object embedded in an otherwise non-JSON Toptoon response.
- Logs the content type and a short sanitized response snippet when Toptoon returns HTTP 200 with a body that still cannot be parsed as JSON.
- Synchronized visible version strings to 0.5.17.

## v0.5.16
- Reintroduced legacy `phpsessid` and `rm_session` config keys as ignored compatibility options so Supervisor can validate old saved app options without warnings.
- The app still does not use cookie option values for login or authentication.
- Synchronized visible version strings to 0.5.16.

## v0.5.15
- Changed login preparation to return immediately without touching Chromium; Toptoon ID login no longer needs a browser page preparation step.
- Verifies successful ID/password login with a direct requests-session attendance probe before trying to persist cookies to Chromium.
- Keeps Chromium cookie persistence on a short timeout so a slow renderer cannot hide the direct login result.
- Synchronized visible version strings to 0.5.15.

## v0.5.14
- Replaced Facebook quick login with direct Toptoon ID/password login via `/login/login_proc`.
- Matches Toptoon's browser login POST shape, including `ci_token` from `ci_cookie`, auto-login, AJAX headers, and transient credentials.
- Persists successful login cookies into the persistent Chromium profile through CDP, then verifies authentication with the direct attendance AJAX probe.
- Keeps the login browser as the fallback for CAPTCHA, account challenge, or other manual confirmation.
- Synchronized visible version strings to 0.5.14.

## v0.5.13
- Open the Facebook login target through Chromium's debugging HTTP endpoint before falling back to CDP navigation, avoiding renderer wait during login preparation.
- Cap Selenium command waits so failed automatic Facebook submit returns in about 18 seconds instead of hanging for two minutes.
- When automatic submit times out, update status to `manual_needed` and direct the user to the login browser instead of leaving a generic request failure.
- Synchronized visible version strings to 0.5.13.

## v0.5.12
- Added a server-side duplicate-submit guard for quick Facebook login.
- Broadened the single CDP submit script to search visible login fields across accessible frames and submit the owning form when no button is found.
- Removed the legacy `rm_session` cookie shortcut from login probing; Toptoon auth is confirmed only by the direct attendance AJAX response.
- Synchronized visible version strings to 0.5.12.

## v0.5.11
- Facebook credential submission now uses one CDP `Runtime.evaluate` call instead of repeated Selenium element commands.
- The submit endpoint returns immediately after the click command is accepted.
- Toptoon authentication is verified in a background thread using the fast direct HTTP probe.
- Removed renderer-dependent post-submit polling that could hang for minutes.
- Synchronized visible version strings to 0.5.11.

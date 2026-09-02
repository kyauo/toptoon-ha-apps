import html, json, os, subprocess, threading, time, warnings
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote
from zoneinfo import ZoneInfo
import requests
import websocket
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

OPTIONS_PATH=Path('/data/options.json'); STATUS_PATH=Path('/data/status.json')
PAGE_URL='https://toptoon.com/event/attendance'; LOGIN_URL='https://toptoon.com/alert/auth/login?redirect=/robots.txt'; WEB_PORT=8098
PERSISTENT_NOTIFICATION_ID='toptoon_attendance_failure'; OK_STATES={'success','already_done'}
BROWSER_LOCK=threading.Lock()
LOGIN_SUBMIT_LOCK=threading.Lock()
LEGACY_OPTION_KEYS={'phpsessid','rm_session'}

def load_json(p,d):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception:return d

def parse_response_json(r):
    try:return r.json()
    except Exception:
        text=(r.text or '').strip()
        start=text.find('{'); end=text.rfind('}')
        if start>=0 and end>start:
            try:return json.loads(text[start:end+1])
            except Exception:pass
        ctype=r.headers.get('content-type','')
        snippet=' '.join(text[:220].split())
        return None,ctype,snippet

def save_json(p,d):
    t=p.with_suffix(p.suffix+'.tmp'); t.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8'); t.replace(p)
def load_options(): return load_json(OPTIONS_PATH,{})
def save_status(**u): s=load_json(STATUS_PATH,{}); s.update(u); save_json(STATUS_PATH,s)
def now_local(o=None):
    o=o or load_options(); return datetime.now(ZoneInfo(o.get('timezone','Asia/Seoul')))
def log(level,msg):
    try: stamp=now_local().strftime('%Y-%m-%d %H:%M:%S %Z')
    except Exception: stamp=datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')
    print(f'[{stamp}] [{level}] {msg}',flush=True)
def fmt_time(v):
    if not v:return '-'
    try:return datetime.fromisoformat(v).astimezone(ZoneInfo(load_options().get('timezone','Asia/Seoul'))).strftime('%Y-%m-%d %H:%M:%S %Z')
    except Exception:return str(v)
def ha_service(domain,service,payload):
    token=os.environ.get('SUPERVISOR_TOKEN')
    if not token:return False
    try:
        r=requests.post(f'http://supervisor/core/api/services/{domain}/{service}',headers={'Authorization':f'Bearer {token}','Content-Type':'application/json'},json=payload,timeout=10); r.raise_for_status(); return True
    except Exception as e: log('WARNING',f'Home Assistant service call failed: {e}'); return False
def mobile_push(entity,title,message):
    if ha_service('notify','send_message',{'entity_id':entity,'title':title,'message':message}): log('INFO',f'Mobile notification sent to {entity}: {title}')
def persistent_failure(msg):
    if ha_service('persistent_notification','create',{'notification_id':PERSISTENT_NOTIFICATION_ID,'title':'Toptoon 출석 실패','message':msg}): log('INFO','Persistent failure notification created.')
def dismiss_failure(): ha_service('persistent_notification','dismiss',{'notification_id':PERSISTENT_NOTIFICATION_ID})

def supervisor_api(method,path,payload=None):
    token=os.environ.get('SUPERVISOR_TOKEN')
    if not token:return None
    try:
        r=requests.request(method,f'http://supervisor{path}',headers={'Authorization':f'Bearer {token}','Content-Type':'application/json'},json=payload,timeout=10)
        if r.status_code>=400:
            log('WARNING',f'Supervisor API {method} {path} failed: HTTP {r.status_code} {r.text[:160]}')
            return None
        try:return r.json()
        except Exception:return {}
    except Exception as e:
        log('WARNING',f'Supervisor API {method} {path} failed: {type(e).__name__}: {str(e)[:160]}')
        return None

def cleanup_legacy_options():
    """Remove old manual-cookie options from Supervisor's stored app config."""
    for base in ('/addons/self','/apps/self'):
        info=supervisor_api('GET',f'{base}/info')
        if not isinstance(info,dict):continue
        data=info.get('data') if isinstance(info.get('data'),dict) else info
        opts=data.get('options') if isinstance(data,dict) else None
        if not isinstance(opts,dict):continue
        found=sorted(k for k in LEGACY_OPTION_KEYS if k in opts)
        if not found:
            log('INFO','Legacy option cleanup: no phpsessid/rm_session values are stored.')
            return
        cleaned={k:v for k,v in opts.items() if k not in LEGACY_OPTION_KEYS}
        res=supervisor_api('POST',f'{base}/options',{'options':cleaned})
        if isinstance(res,dict):
            log('INFO',f"Legacy option cleanup: removed stored options {', '.join(found)} via {base}/options.")
            save_status(legacy_options_cleaned_at=now_local().isoformat(timespec='seconds'))
            return
    log('WARNING','Legacy option cleanup: could not read or update Supervisor app options.')

def browser_driver():
    opts=Options(); opts.page_load_strategy='none'; opts.add_experimental_option('debuggerAddress','127.0.0.1:9222'); opts.binary_location='/usr/bin/chromium-browser'
    d=webdriver.Chrome(service=Service('/usr/bin/chromedriver'),options=opts)
    set_driver_timeout(d,18)
    return d

def set_driver_timeout(d,seconds):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',DeprecationWarning)
            d.command_executor.set_timeout(seconds)
    except Exception:
        pass

def x_env():
    env=os.environ.copy(); env['DISPLAY']=':99'
    return env

def x_run(args,input_bytes=None,timeout=5):
    try:
        cp=subprocess.run(args,input=input_bytes,env=x_env(),timeout=timeout,check=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        msg=((cp.stderr or cp.stdout or b'').decode('utf-8','ignore') or '').strip()
        return cp.returncode==0,msg[:220]
    except Exception as e:
        return False,f'{type(e).__name__}: {str(e)[:180]}'

def x_key(key,timeout=4):
    return x_run(['xdotool','key','--clearmodifiers',key],timeout=timeout)

def x_click(x,y,timeout=4):
    return x_run(['xdotool','mousemove',str(x),str(y),'click','1'],timeout=timeout)

def x_clip(text):
    return x_run(['xclip','-selection','clipboard','-i'],input_bytes=text.encode('utf-8'),timeout=4)

def activate_chromium():
    for args in (
        ['xdotool','search','--onlyvisible','--class','chromium','windowactivate','--sync'],
        ['xdotool','search','--onlyvisible','--class','chromium-browser','windowactivate','--sync'],
        ['xdotool','search','--class','chromium','windowactivate','--sync'],
        ['xdotool','search','--class','chromium-browser','windowactivate','--sync'],
        ['xdotool','search','--onlyvisible','--name','Chromium','windowactivate','--sync'],
    ):
        ok,msg=x_run(args,timeout=5)
        if ok:return True,''
    return False,msg or 'Chromium 창을 찾지 못했습니다.'

def open_login_page_via_debug_port():
    encoded=quote(LOGIN_URL,safe='')
    for method,path in (
        ('PUT',f'/json/new?{encoded}'),
        ('GET',f'/json/new?{encoded}'),
        ('PUT',f'/json/new?url={encoded}'),
        ('GET',f'/json/new?url={encoded}'),
    ):
        try:
            r=requests.request(method,f'http://127.0.0.1:9222{path}',timeout=3)
            if r.status_code < 400:
                log('INFO',f'Login assist: Chromium debug endpoint opened Toptoon login page with {method} {path[:18]}...')
                return True,'Toptoon 로그인 페이지를 Chromium 브라우저에 열었습니다.'
        except Exception:
            pass
    try:
        d=browser_driver()
        d.execute_cdp_cmd('Page.navigate',{'url':LOGIN_URL})
        log('INFO','Login assist: Chromium CDP Page.navigate opened Toptoon login page.')
        return True,'Toptoon 로그인 페이지를 Chromium 브라우저에 열었습니다.'
    except Exception as e:
        return False,f'{type(e).__name__}: {str(e)[:180]}'

def paste_text_to_chromium_field(text):
    ok,msg=x_clip(text)
    if not ok:return False,msg or '가상 브라우저 클립보드에 텍스트를 전달하지 못했습니다.'
    time.sleep(0.12)
    ok,msg=x_key('ctrl+v')
    if not ok:return False,msg or '가상 브라우저에 붙여넣기 키를 전달하지 못했습니다.'
    return True,''

def open_toptoon_login_page():
    active,msg=activate_chromium()
    if active:
        ok,msg=x_clip(LOGIN_URL)
        if not ok:return False,msg or '로그인 URL을 가상 브라우저 클립보드에 전달하지 못했습니다.'
        for key in ('ctrl+l','ctrl+v','Return'):
            ok,msg=x_key(key)
            if not ok:return False,msg or f'{key} 키 전달에 실패했습니다.'
            time.sleep(0.12)
        clear_x_clipboard_later(2)
        log('INFO','Login assist: Chromium was navigated to the Toptoon ID login page through X input.')
        return True,'Toptoon 로그인 페이지를 Chromium 브라우저에 열었습니다.'
    log('WARNING',f'Login assist: xdotool could not activate Chromium, falling back to debug navigation: {msg}')
    return open_login_page_via_debug_port()
def page_text(d):
    try:return d.find_element(By.TAG_NAME,'body').text
    except Exception:return ''
def login_probe(d):
    """Conservative DOM probe. Final auth truth comes from the direct attendance AJAX probe."""
    try:
        u=d.current_url.lower()
        if 'facebook.com' in u or 'login' in u or 'member/login' in u:
            return 'login_required'
        # Visible login controls are stronger evidence than body text.
        login_nodes=d.find_elements(By.XPATH,"//*[self::a or self::button or @role='button'][contains(normalize-space(.),'로그인') or contains(translate(normalize-space(.),'FACEBOOK','facebook'),'facebook') or contains(normalize-space(.),'페이스북')]")
        if any(e.is_displayed() for e in login_nodes):
            return 'login_required'
        logout_nodes=d.find_elements(By.XPATH,"//*[self::a or self::button][contains(normalize-space(.),'로그아웃') or contains(translate(@href,'LOGOUT','logout'),'logout')]")
        if any(e.is_displayed() for e in logout_nodes):
            return 'logged_in'
    except Exception:
        pass
    return 'unknown'

def _ua():
    return 'Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36'

def is_login_required(d):
    return login_probe(d)=='login_required'

def inspect_page():
    st=load_json(STATUS_PATH,{})
    state=st.get('login_state') or 'unknown'
    msg=st.get('login_message') or '저장된 로그인 상태가 없습니다. 로그인 제출 또는 출석 테스트로 확인해 주세요.'
    if state=='logged_in':
        msg='저장된 상태는 로그인 유지입니다. 실제 확인은 출석 테스트가 가장 정확합니다.'
    elif state in ('login_required','login_failed'):
        msg=msg or '저장된 상태는 로그인 필요입니다.'
    elif state=='login_ready':
        msg='Toptoon ID 로그인 화면이 Chromium 브라우저에 준비되어 있습니다.'
    save_status(status_checked_at=now_local().isoformat(timespec='seconds'))
    log('INFO',f'Fast status check from saved state: {state} / {msg}')
    return state,msg

def check_attendance(skip_when_login_required=False):
    if skip_when_login_required:
        st=load_json(STATUS_PATH,{})
        if st.get('login_state') in ('login_required','login_failed'):
            msg=st.get('login_message') or 'Toptoon 로그인이 필요합니다.'
            log('INFO',f'Attendance: skipped browser check because saved login state is {st.get("login_state")}.')
            return 'login_required',msg
    with BROWSER_LOCK:
        t0=time.monotonic()
        try:
            sess,cookies=_requests_from_browser()
            log('INFO',f'Attendance: copied {len(cookies)} Toptoon cookies from persistent Chromium via browser-level CDP.')
            r=sess.post('https://toptoon.com/event/attendance',data={'ci_token':'null'},headers={'Accept':'application/json, text/javascript, */*; q=0.01','Content-Type':'application/x-www-form-urlencoded; charset=UTF-8','X-Requested-With':'XMLHttpRequest','Origin':'https://toptoon.com','Referer':PAGE_URL},timeout=(5,12))
            log('INFO',f'Attendance: direct AJAX returned HTTP {r.status_code} after {time.monotonic()-t0:.1f}s.')
            try:body=r.json()
            except Exception:return 'invalid_response',f'HTTP {r.status_code}: {r.text[:300]}'
            msg=str(body.get('message') or '') if isinstance(body,dict) else ''
            if isinstance(body,dict) and body.get('result') is True:
                save_status(login_state='logged_in',login_message='Toptoon 서버에서 Chromium 쿠키 로그인이 확인되었습니다.',status_checked_at=now_local().isoformat(timespec='seconds')); return 'success',msg or '출석 완료'
            if '이미 출석' in msg:
                save_status(login_state='logged_in',login_message='Toptoon 서버에서 Chromium 쿠키 로그인이 확인되었습니다.',status_checked_at=now_local().isoformat(timespec='seconds')); return 'already_done',msg
            if isinstance(body,dict) and body.get('errorType')=='login':
                save_status(login_state='login_required',login_message=msg or 'Toptoon 로그인이 필요합니다.',status_checked_at=now_local().isoformat(timespec='seconds')); return 'login_required',msg or '로그인이 만료되었습니다.'
            return 'failed',msg or json.dumps(body,ensure_ascii=False)[:300]
        except requests.Timeout:return 'network_error','Toptoon 출석 HTTP 요청이 12초 안에 끝나지 않았습니다.'
        except Exception as e:return 'browser_error',str(e)[:400]

def record_result(state,msg,manual=False):
    n=now_local(); u={'last_run_at':n.isoformat(timespec='seconds'),'last_result':state,'last_message':msg}
    if manual:u['manual_run_at']=n.isoformat(timespec='seconds')
    if state in OK_STATES:
        u.update(last_run_date=n.date().isoformat(),unresolved=False,failure_date=None,mobile_notified=False,today_status='출석 완료' if state=='success' else '이미 출석 완료')
    elif state=='login_required':
        u.update(today_status='실패: 로그인 필요')
    elif state=='browser_error':
        u.update(today_status='실패: 브라우저 오류')
    elif state=='network_error':
        u.update(today_status='실패: 네트워크 오류')
    else:
        u.update(today_status='실패: '+(msg[:60] if msg else state))
    save_status(**u)
def success_notification(o,state):
    if o.get('notify_on_success',True): mobile_push(o.get('mobile_notify_entity','notify.ky17'),'Toptoon 출석 완료','오늘 Toptoon 출석이 정상 확인되었습니다.' if state=='success' else '오늘 Toptoon은 이미 출석 완료 상태입니다.')
def failure_instruction(): return 'Home Assistant에서 Toptoon Attendance Bot을 열어 로그인 상태를 확인해 주세요. 로그인이 풀린 경우에만 로그인 브라우저를 열어 Toptoon에 다시 로그인하면 됩니다.'
def manual_attendance():
    log('INFO','Manual attendance test requested from Ingress UI.'); s,m=check_attendance(skip_when_login_required=True); record_result(s,m,True)
    if s in OK_STATES:dismiss_failure(); log('INFO',f'Manual attendance OK: {s} / {m}')
    else:log('WARNING',f'Manual attendance failed: {s} / {m}')
    return s,m
def run_with_retries(o):
    r1=int(o.get('retry_1_minutes',5)); r2=int(o.get('retry_2_minutes',15)); delays=[0,r1*60,max(0,(r2-r1)*60)]; s=None;m=''
    for i,delay in enumerate(delays):
        if delay:log('WARNING',f'Attempt failed ({s}); retry {i} in {delay//60} minutes.'); time.sleep(delay)
        log('INFO','Checking Toptoon daily attendance.'); s,m=check_attendance(); record_result(s,m)
        if s in OK_STATES: log('INFO',f'Toptoon attendance OK: {s} / {m}'); dismiss_failure(); success_notification(o,s); return True
        log('WARNING',f'Toptoon attendance failed: {s} / {m}')
    save_status(unresolved=True,failure_date=now_local(o).date().isoformat(),mobile_notified=False)
    if o.get('notify_on_failure',True):persistent_failure(f'{s}: {m}\n\n{failure_instruction()}')
    return False
def manual_reminder(o,n):
    if not o.get('notify_manual_reminder',True):return
    today=n.date().isoformat(); st=load_json(STATUS_PATH,{})
    if st.get('manual_reminder_date')==today:return
    if st.get('last_run_date')==today and st.get('last_result') in OK_STATES:save_status(manual_reminder_date=today); log('INFO',"21:00 manual reminder skipped: today's Toptoon attendance is confirmed."); return
    mobile_push(o.get('mobile_notify_entity','notify.ky17'),'Toptoon 출석 확인 필요',f"21:00까지 오늘 Toptoon 출석 성공이 확인되지 않았습니다. 직접 출석을 확인해 주세요.\n마지막 상태: {st.get('last_result','기록 없음')} / {st.get('last_message','오늘 성공 기록이 없습니다.')}")
    save_status(manual_reminder_date=today); log('WARNING','21:00 manual attendance reminder sent.')

def render_ui(message='',kind=''):
    st=load_json(STATUS_PATH,{}); o=load_options(); ls=st.get('login_state'); badge=('good','로그인 유지됨') if ls=='logged_in' else (('bad','로그인 필요') if ls=='login_required' else ('neutral','아직 확인 안 함'))
    alert=f'<div class="{("okmsg" if kind=="ok" else "warnmsg")}">{html.escape(message)}</div>' if message else ''
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Toptoon Attendance Bot</title><style>
:root{{color-scheme:light dark;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}body{{margin:0;background:#f4f5f7;color:#202124}}.wrap{{max-width:720px;margin:0 auto;padding:20px;position:relative}}.card{{background:white;border-radius:16px;padding:20px;box-shadow:0 2px 10px #0001;margin-bottom:16px}}h1{{font-size:24px;margin:0 36px 6px 0}}p{{line-height:1.55}}.close{{position:absolute;right:25px;top:22px;border:0;background:transparent;font-size:28px;cursor:pointer;color:#666}}.badge{{display:inline-block;padding:6px 10px;border-radius:999px;font-weight:700;font-size:13px}}.good{{background:#e8f5e9;color:#1b5e20}}.bad{{background:#ffebee;color:#b71c1c}}.neutral{{background:#eceff1;color:#455a64}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px}}.item{{border:1px solid #e5e7eb;border-radius:12px;padding:13px}}.label{{color:#6b7280;font-size:12px}}.value{{font-size:17px;font-weight:700;margin-top:4px}}.actions{{display:grid;gap:10px}}button,.btn{{width:100%;box-sizing:border-box;border:0;border-radius:11px;padding:13px;font-size:15px;font-weight:700;cursor:pointer;text-align:center;text-decoration:none;display:block}}button:disabled{{opacity:.65;cursor:wait}}.primary{{background:#e53935;color:white}}.secondary{{background:#e8eaed;color:#202124}}.danger{{background:#fff3e0;color:#bf360c}}.busy{{display:none;margin-top:12px;border-radius:10px;padding:12px;background:#e3f2fd;color:#0d47a1;font-weight:700}}.note{{color:#5f6368;font-size:13px}}.okmsg,.warnmsg{{border-radius:10px;padding:12px;margin:12px 0}}.okmsg{{background:#e8f5e9}}.warnmsg{{background:#fff3e0}}@media(prefers-color-scheme:dark){{body{{background:#111827;color:#f3f4f6}}.card{{background:#1f2937}}.item{{border-color:#374151}}.secondary{{background:#374151;color:#f3f4f6}}.note,.label{{color:#9ca3af}}.close{{color:#d1d5db}}}}</style></head><body><div class="wrap">
<button class="close" onclick="try{{window.parent.location.href='/'}}catch(e){{history.back()}}">×</button><div class="card"><h1>Toptoon Attendance Bot</h1><p>평소에는 이 화면에서 상태만 확인하면 됩니다. <b>로그인 브라우저는 Toptoon 로그인이 풀렸을 때만</b> 열어 주세요. 브라우저 프로필은 앱 재시작 후에도 유지됩니다.</p>{alert}<span class="badge {badge[0]}">{badge[1]}</span><div class="grid"><div class="item"><div class="label">오늘 출석</div><div class="value">{html.escape(str(st.get('today_status','아직 확인 안 함')))}</div></div><div class="item"><div class="label">마지막 상태 확인</div><div class="value" style="font-size:13px">{html.escape(fmt_time(st.get('status_checked_at')))}</div></div></div></div>
<div class="card"><b>Toptoon 브라우저 로그인 세팅</b><p class="note">저해상도 Chromium에 Toptoon 로그인 화면을 열고, 로그인 브라우저에서 보면서 직접 로그인합니다. 이미지는 꺼 둬서 화면은 단순하게 보일 수 있습니다.</p><div class="actions"><button class="secondary" id="prepBtn" onclick="loginPrepare(this)">Toptoon 로그인 화면 준비</button><a class="btn primary" href="login-console">로그인 브라우저에서 직접 로그인</a></div><div id="loginMsg" class="note" style="margin-top:10px"></div></div>
<div class="card"><div class="actions"><button id="checkBtn" class="primary" onclick="runAction('check',this)">저장된 로그인 상태 확인</button><button class="secondary" onclick="runAction('probe',this)">브라우저 쿠키 로그인 확인</button><button id="attBtn" class="danger" onclick="if(confirm('오늘 미출석이면 실제 출석 요청을 실행합니다. 계속할까요?'))runAction('attendance',this)">지금 출석 테스트</button><a id="vncBtn" class="btn secondary" href="login-console">로그인 브라우저 열기</a></div><div id="busy" class="busy">처리 중... 잠시 기다려 주세요.</div><p class="note">로그인 직후 브라우저 화면이 무거워도 쿠키 확인은 렌더링 없이 수행합니다. 실제 출석은 출석 테스트가 가장 정확합니다.</p></div>
<div class="card"><b>자동 실행</b><p class="note">매일 {o.get('run_time','00:30')} ({o.get('timezone','Asia/Seoul')}) · 재시도 +{o.get('retry_1_minutes',5)}분 / +{o.get('retry_2_minutes',15)}분 · 실패 확인 {o.get('mobile_alert_time','09:05')} · 수동 확인 알림 {o.get('manual_reminder_time','21:00')}</p><div class="label">마지막 출석 실행</div><div>{html.escape(fmt_time(st.get('last_run_at')))}</div><div class="label" style="margin-top:10px">마지막 결과</div><div><b>{html.escape(str(st.get('last_result','아직 없음')))}</b> {html.escape(str(st.get('last_message','')))}</div></div></div>
	<script>let loginSubmitInFlight=false;async function postLogin(doit,extra={{}}){{let q=new URLSearchParams();q.set('do',doit);for(const [k,v] of Object.entries(extra))q.set(k,v);let r=await fetch('action',{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded'}},body:q,cache:'no-store'}});return await r.json()}}async function loginPrepare(b){{let m=document.getElementById('loginMsg');b.disabled=true;m.textContent='Toptoon 로그인 화면 준비 중...';let ctl=new AbortController();let tm=setTimeout(()=>ctl.abort(),35000);try{{let q=new URLSearchParams();q.set('do','login_prepare');let r=await fetch('action',{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded'}},body:q,cache:'no-store',signal:ctl.signal}});let j=await r.json();m.textContent=j.message||j.state;if(j.state==='logged_in')setTimeout(()=>location.reload(),700)}}catch(e){{m.textContent=e.name==='AbortError'?'35초 안에 준비가 끝나지 않았습니다. 로그인 브라우저를 열어 수동으로 진행해 주세요.':'로그인 화면 준비 요청 실패'}}finally{{clearTimeout(tm);b.disabled=false}}}}async function loginSubmit(b){{let m=document.getElementById('loginMsg'),u=document.getElementById('fbid'),p=document.getElementById('fbpw');if(loginSubmitInFlight){{m.textContent='이미 로그인 제출을 처리 중입니다.';return}}if(!u.value||!p.value){{m.textContent='ID와 비밀번호를 모두 입력해 주세요.';return}}loginSubmitInFlight=true;b.disabled=true;m.textContent='Toptoon 로그인 제출 중...';try{{let j=await postLogin('login_submit',{{user:u.value,password:p.value}});p.value='';m.textContent=j.message||j.state;if(j.state==='logged_in'||j.state==='verifying')setTimeout(()=>location.reload(),2500)}}catch(e){{p.value='';m.textContent='로그인 제출 요청 실패'}}finally{{loginSubmitInFlight=false;b.disabled=false}}}}async function runAction(a,b){{let c=document.getElementById('checkBtn'),d=document.getElementById('attBtn'),v=document.getElementById('vncBtn'),x=document.getElementById('busy');c.disabled=d.disabled=true;v.style.pointerEvents='none';v.style.opacity='.6';x.style.display='block';b.textContent=a==='attendance'?'출석 처리 중...':'상태 확인 중...';let done=false;let w=setTimeout(()=>{{if(!done)location.reload()}},125000);let ctl=new AbortController();let t=setTimeout(()=>ctl.abort(),120000);try{{let q=new URLSearchParams();q.set('do',a);q.set('ajax','1');let r=await fetch('action',{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded','X-Requested-With':'fetch'}},body:q,signal:ctl.signal,cache:'no-store'}});let j=await r.json();done=true;clearTimeout(w);clearTimeout(t);x.textContent=(j.message||j.state||'완료');setTimeout(()=>location.reload(),900)}}catch(e){{done=true;clearTimeout(w);clearTimeout(t);x.textContent='요청이 시간 초과되었거나 연결이 끊겼습니다.';setTimeout(()=>location.reload(),1200)}}}}</script></body></html>'''


def _switch_latest_window(d):
    try:
        if len(d.window_handles)>1: d.switch_to.window(d.window_handles[-1])
    except Exception: pass

def _browser_cookies_via_cdp(d):
    data=d.execute_cdp_cmd('Network.getAllCookies', {})
    cookies=data.get('cookies',[]) if isinstance(data,dict) else []
    return [c for c in cookies if 'toptoon.com' in str(c.get('domain','')).lower()]

def _browser_cookies_via_debug_port():
    try:
        r=requests.get('http://127.0.0.1:9222/json/version',timeout=3)
        ws_url=(r.json() or {}).get('webSocketDebuggerUrl')
        if not ws_url:return None
        ws=websocket.create_connection(ws_url,timeout=5)
        try:
            for i,method in enumerate(('Network.getAllCookies','Storage.getCookies'),start=1):
                ws.send(json.dumps({'id':i,'method':method}))
                deadline=time.monotonic()+5
                while time.monotonic()<deadline:
                    msg=json.loads(ws.recv())
                    if msg.get('id')!=i:continue
                    if 'error' in msg:break
                    result=msg.get('result') or {}
                    cookies=result.get('cookies',[]) if isinstance(result,dict) else []
                    return [c for c in cookies if 'toptoon.com' in str(c.get('domain','')).lower()]
        finally:
            try:ws.close()
            except Exception:pass
    except Exception as e:
        log('WARNING',f'Chromium browser-level cookie read failed: {type(e).__name__}: {str(e)[:160]}')
    return None

def _requests_from_browser(d=None):
    sess=requests.Session()
    sess.headers.update({'User-Agent':_ua(),'Accept-Language':'ko-KR,ko;q=0.9,en;q=0.8'})
    cookies=_browser_cookies_via_debug_port()
    if cookies is None and d is not None:
        cookies=_browser_cookies_via_cdp(d)
    cookies=cookies or []
    for c in cookies:
        try:sess.cookies.set(c['name'],c.get('value',''),domain=c.get('domain') or '.toptoon.com',path=c.get('path') or '/')
        except Exception:pass
    return sess,cookies

def _copy_requests_cookies_to_browser(d,sess):
    copied=0
    for c in sess.cookies:
        if not c.domain or 'toptoon.com' not in c.domain.lower():continue
        payload={'name':c.name,'value':c.value,'domain':c.domain,'path':c.path or '/','secure':bool(c.secure)}
        try:
            d.execute_cdp_cmd('Network.setCookie',payload)
            copied+=1
        except Exception as e:
            log('WARNING',f'Login assist: failed to persist cookie {c.name}: {type(e).__name__}')
    return copied

def _toptoon_auth_probe_http(d=None):
    sess,cookies=_requests_from_browser(d); t=time.monotonic()
    r=sess.post('https://toptoon.com/event/attendance',data={'ci_token':'null'},headers={'Accept':'application/json, text/javascript, */*; q=0.01','Content-Type':'application/x-www-form-urlencoded; charset=UTF-8','X-Requested-With':'XMLHttpRequest','Origin':'https://toptoon.com','Referer':PAGE_URL},timeout=(5,12))
    log('INFO',f'Login assist: direct Toptoon auth probe returned HTTP {r.status_code} after {time.monotonic()-t:.1f}s using {len(cookies)} Toptoon cookies.')
    try:body=r.json()
    except Exception:return 'probe_error',f'HTTP {r.status_code}: {r.text[:180]}'
    msg=str(body.get('message') or '') if isinstance(body,dict) else ''
    if isinstance(body,dict) and (body.get('result') is True or '이미 출석' in msg):return 'logged_in',msg or 'Toptoon 세션에서 로그인이 확인되었습니다.'
    if isinstance(body,dict) and body.get('errorType')=='login':return 'login_required',msg or '로그인이 필요합니다.'
    return 'unknown',msg

def browser_cookie_login_check():
    with BROWSER_LOCK:
        try:
            sess,cookies=_requests_from_browser()
        except Exception as e:
            msg=f'Chromium 쿠키를 읽지 못했습니다: {type(e).__name__}: {str(e)[:160]}'
            save_status(login_state='browser_error',login_message=msg,status_checked_at=now_local().isoformat(timespec='seconds'))
            log('WARNING',f'Login assist: {msg}')
            return 'browser_error',msg
    try:
        t=time.monotonic()
        r=sess.get(LOGIN_URL,headers={'Accept':'text/html,text/plain,*/*','Referer':'https://toptoon.com/'},timeout=(5,12))
        text=r.text or ''
        login_form=('name="userId"' in text or "name='userId'" in text or 'signUserPassword' in text)
        names=','.join(sorted(c.get('name','') for c in cookies if c.get('name')))
        log('INFO',f'Login assist: browser-cookie lightweight login-page probe HTTP {r.status_code} after {time.monotonic()-t:.1f}s using {len(cookies)} cookies [{names}], final_url={r.url[:120]!r}.')
        if not login_form and '/alert/auth/login' not in r.url:
            save_status(login_state='logged_in',login_message='Chromium 쿠키에서 Toptoon 로그인을 확인했습니다.',status_checked_at=now_local().isoformat(timespec='seconds'))
            return 'logged_in','Chromium 쿠키에서 Toptoon 로그인을 확인했습니다. 이제 출석 테스트를 실행해도 됩니다.'
        msg='Chromium 쿠키에서는 아직 Toptoon 로그인이 확인되지 않았습니다.'
        save_status(login_state='login_required',login_message=msg,status_checked_at=now_local().isoformat(timespec='seconds'))
        return 'login_required',msg
    except requests.Timeout:
        return 'network_error','Toptoon 로그인 확인 HTTP 요청이 12초 안에 끝나지 않았습니다.'
    except Exception as e:
        msg=f'로그인 확인 실패: {type(e).__name__}: {str(e)[:180]}'
        save_status(login_state='browser_error',login_message=msg,status_checked_at=now_local().isoformat(timespec='seconds'))
        log('WARNING',f'Login assist: {msg}')
        return 'browser_error',msg

def _toptoon_auth_probe_session(sess):
    t=time.monotonic()
    r=sess.post('https://toptoon.com/event/attendance',data={'ci_token':'null'},headers={'Accept':'application/json, text/javascript, */*; q=0.01','Content-Type':'application/x-www-form-urlencoded; charset=UTF-8','X-Requested-With':'XMLHttpRequest','Origin':'https://toptoon.com','Referer':PAGE_URL},timeout=(5,12))
    log('INFO',f'Login assist: direct Toptoon auth probe with login session returned HTTP {r.status_code} after {time.monotonic()-t:.1f}s.')
    try:body=r.json()
    except Exception:return 'probe_error',f'HTTP {r.status_code}: {r.text[:180]}'
    msg=str(body.get('message') or '') if isinstance(body,dict) else ''
    if isinstance(body,dict) and (body.get('result') is True or '이미 출석' in msg):return 'logged_in',msg or 'Toptoon 세션에서 로그인이 확인되었습니다.'
    if isinstance(body,dict) and body.get('errorType')=='login':return 'login_required',msg or '로그인이 필요합니다.'
    return 'unknown',msg

def _diagnose_login_html(sess,snippet):
    if 'top.location.replace' not in snippet:return
    try:
        r=sess.get('https://toptoon.com/',headers={'Accept':'text/html,application/xhtml+xml','Referer':LOGIN_URL},timeout=(5,12))
        import re
        m=re.search(r'user_idx\s*=\s*[\'"]?([0-9]+)',r.text or '')
        user_idx=m.group(1) if m else 'unknown'
        names=','.join(sorted(c.name for c in sess.cookies if c.domain and 'toptoon.com' in c.domain.lower()))
        log('INFO',f'Login assist: redirect follow-up page HTTP {r.status_code}, user_idx={user_idx}, cookies=[{names}].')
    except Exception as e:
        log('WARNING',f'Login assist: redirect follow-up diagnosis failed: {type(e).__name__}: {str(e)[:160]}')

def _persist_verified_login_session(sess):
    copied=0
    try:
        with BROWSER_LOCK:
            d=browser_driver()
            set_driver_timeout(d,8)
            copied=_copy_requests_cookies_to_browser(d,sess)
    except Exception as e:
        log('WARNING',f'Login assist: login succeeded but Chromium cookie persistence failed: {type(e).__name__}: {str(e)[:180]}')
        save_status(login_state='verification_needed',login_message='Toptoon ID 로그인은 성공했지만 Chromium 세션 저장이 실패했습니다. 앱을 재시작하거나 로그인 브라우저 수동 로그인이 필요할 수 있습니다.',status_checked_at=now_local().isoformat(timespec='seconds'))
        return 'verification_needed','Toptoon ID 로그인은 성공했지만 Chromium 세션 저장이 실패했습니다.'
    save_status(login_state='logged_in',login_message='Toptoon ID 로그인 및 Chromium 세션 저장이 확인되었습니다.',status_checked_at=now_local().isoformat(timespec='seconds'))
    log('INFO',f'Login assist: Toptoon ID login persisted {copied} cookies after direct auth probe confirmed login.')
    return 'logged_in','Toptoon ID 로그인 성공. Chromium 세션에 저장했습니다.'

def prepare_login():
    with BROWSER_LOCK:
        ok,msg=open_toptoon_login_page()
    if not ok:
        save_status(login_state='manual_needed',login_message=f'Toptoon 로그인 페이지 열기 실패: {msg}',status_checked_at=now_local().isoformat(timespec='seconds'))
        log('WARNING',f'Login assist: failed to prepare Chromium login page: {msg}')
        return 'manual_needed','로그인 브라우저를 자동으로 준비하지 못했습니다. 로그인 브라우저를 열어 수동으로 진행해 주세요.'
    save_status(login_state='login_ready',login_message='Chromium 브라우저에 Toptoon ID 로그인 화면을 열었습니다.',status_checked_at=now_local().isoformat(timespec='seconds'))
    return 'login_ready','Toptoon ID 로그인 화면을 열었습니다. ID와 비밀번호를 입력한 뒤 로그인 제출을 누르세요.'

def _verify_login_after_submit():
    """Verify Toptoon login without touching the slow login renderer."""
    delays=(4,6,8,10)
    for delay in delays:
        time.sleep(delay)
        try:
            with BROWSER_LOCK:
                state,msg=_toptoon_auth_probe_http()
            log('INFO',f'Login assist: post-submit Toptoon auth probe -> {state}.')
            if state=='logged_in':
                save_status(login_state='logged_in',login_message='Toptoon 서버에서 로그인 성공을 확인했습니다.',status_checked_at=now_local().isoformat(timespec='seconds'))
                return
        except Exception as e:
            log('WARNING',f'Login assist: background auth probe failed: {type(e).__name__}: {str(e)[:160]}')
    save_status(login_state='verification_needed',login_message='로그인 제출 후 Toptoon 인증이 아직 확인되지 않았습니다. 추가 인증 화면이 있는지 확인해 주세요.',status_checked_at=now_local().isoformat(timespec='seconds'))
    log('WARNING','Login assist: Toptoon login was not confirmed after background verification window.')

def submit_toptoon_login(user,password):
    if not LOGIN_SUBMIT_LOCK.acquire(blocking=False):
        return 'already_submitting','이미 로그인 준비를 처리 중입니다. 잠시 뒤 다시 시도해 주세요.'
    try:
        with BROWSER_LOCK:
            ok,msg=open_toptoon_login_page()
            if not ok:
                save_status(login_state='manual_needed',login_message=f'브라우저 로그인 제출 준비 실패: {msg}',status_checked_at=now_local().isoformat(timespec='seconds'))
                log('WARNING',f'Login assist: browser-input submit could not open login page: {msg}')
                return 'manual_needed','로그인 브라우저를 자동으로 제어하지 못했습니다. 로그인 브라우저에서 수동으로 로그인해 주세요.'
        save_status(login_state='login_ready',login_message='Chromium에 Toptoon 로그인 화면을 열었습니다. 로그인 브라우저에서 직접 로그인해 주세요.',status_checked_at=now_local().isoformat(timespec='seconds'))
        log('INFO','Login assist: manual browser login page prepared; automatic credential typing is disabled in this setup build.')
        return 'login_ready','로그인 브라우저에서 보면서 직접 로그인해 주세요. 로그인 후 저장된 로그인 상태 확인 또는 출석 테스트를 눌러 주세요.'
    finally:
        LOGIN_SUBMIT_LOCK.release()

def clear_x_clipboard_later(delay=8):
    def _clear():
        time.sleep(delay)
        try:
            env=os.environ.copy(); env['DISPLAY']=':99'
            subprocess.run(['xclip','-selection','clipboard','-i'], input=b'', env=env, timeout=3, check=False)
        except Exception:
            pass
    threading.Thread(target=_clear, daemon=True).start()

def paste_into_browser(text):
    if not text:
        return False, '붙여넣을 텍스트가 없습니다.'
    if len(text) > 4096:
        return False, '텍스트가 너무 깁니다.'
    env=os.environ.copy(); env['DISPLAY']=':99'
    try:
        cp=subprocess.run(['xclip','-selection','clipboard','-i'], input=text.encode('utf-8'), env=env, timeout=4, check=False)
        if cp.returncode != 0:
            return False, '가상 브라우저 클립보드에 텍스트를 전달하지 못했습니다.'
        time.sleep(0.12)
        kp=subprocess.run(['xdotool','key','--clearmodifiers','ctrl+v'], env=env, timeout=4, check=False)
        if kp.returncode != 0:
            return False, '가상 브라우저에 붙여넣기 키를 전달하지 못했습니다.'
        clear_x_clipboard_later()
        log('INFO','Transient text paste sent to the focused Chromium field (content not logged or stored).')
        return True, '현재 선택된 입력칸에 붙여넣기를 보냈습니다.'
    except Exception as e:
        log('WARNING', f'Transient paste failed: {type(e).__name__}: {e}')
        return False, '붙여넣기 전달에 실패했습니다.'

def render_login_console():
    return """<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Toptoon Login Console</title><style>
:root{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color-scheme:light dark}*{box-sizing:border-box}body{margin:0;background:#111827;color:#f3f4f6}.bar{position:sticky;top:0;z-index:10;background:#111827;padding:10px;border-bottom:1px solid #374151}.row{display:flex;gap:8px;align-items:center}.row input{flex:1;min-width:0;padding:11px 12px;border-radius:9px;border:1px solid #4b5563;background:#fff;color:#111;font-size:16px}.row button,.back{border:0;border-radius:9px;padding:11px 13px;font-weight:700;text-decoration:none;cursor:pointer}.paste{background:#e53935;color:#fff}.back{background:#374151;color:#fff;white-space:nowrap}.hint{font-size:12px;color:#cbd5e1;margin-top:7px;line-height:1.45}.msg{font-size:12px;margin-top:6px;min-height:18px}.frame{width:100%;height:calc(100vh - 105px);border:0;background:#000}@media(max-width:560px){.row{flex-wrap:wrap}.row input{flex-basis:100%}.frame{height:calc(100vh - 150px)}}
</style></head><body><div class="bar"><div class="row"><a class="back" href="./">← 돌아가기</a><input id="clip" type="text" autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="ID 또는 비밀번호를 여기에 붙여넣기"><button class="paste" id="pasteBtn">선택 칸에 전송</button></div><div class="hint">아래 원격 브라우저에서 먼저 입력칸을 한 번 클릭한 뒤, 위 칸에 Mac에서 ⌘V로 붙여넣고 ‘선택 칸에 전송’을 누르세요. 내용은 파일에 저장하거나 로그에 남기지 않으며, 가상 클립보드도 잠시 뒤 지웁니다. 성능을 위해 이미지와 고품질 VNC 전송은 꺼져 있습니다.</div><div class="msg" id="msg"></div></div><iframe class="frame" src="vnc/vnc.html?autoconnect=1&amp;resize=scale&amp;quality=1&amp;compression=9&amp;path=websockify"></iframe><script>
const b=document.getElementById('pasteBtn'),i=document.getElementById('clip'),m=document.getElementById('msg');async function send(){let v=i.value;if(!v){m.textContent='전송할 텍스트를 먼저 넣어 주세요.';return}b.disabled=true;m.textContent='전송 중...';try{let q=new URLSearchParams();q.set('do','paste');q.set('text',v);let r=await fetch('action',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:q,cache:'no-store'});let j=await r.json();m.textContent=j.message||'';if(j.ok)i.value=''}catch(e){m.textContent='전송 실패'}finally{b.disabled=false}}b.onclick=send;i.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();send()}});
</script></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*a):return
    def sendx(self,obj,json_mode=False,status=200):
        data=(json.dumps(obj,ensure_ascii=False) if json_mode else obj).encode()
        try:
            self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8' if json_mode else 'text/html; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            log('INFO','Ingress client disconnected before the response was delivered; backend work already finished.')
    def do_GET(self):
        path=self.path.split('?',1)[0]
        if path in ('/',''): return self.sendx(render_ui())
        if path in ('/login-console','/login-console/'): return self.sendx(render_login_console())
        return self.sendx(render_ui('알 수 없는 경로입니다.','warn'))
    def do_POST(self):
        if self.path.split('?',1)[0]!='/action':return self.sendx({'ok':False,'message':'bad request'},True,404)
        p=parse_qs(self.rfile.read(int(self.headers.get('Content-Length','0') or 0)).decode()); a=p.get('do',[''])[0]
        if a=='login_prepare':s,m=prepare_login(); ok=s in ('login_ready','logged_in')
        elif a=='login_submit':s,m=submit_toptoon_login(p.get('user',[''])[0],p.get('password',[''])[0]); ok=s in ('verifying','logged_in')
        elif a=='check':s,m=inspect_page(); ok=s=='logged_in'
        elif a=='probe':s,m=browser_cookie_login_check(); ok=s=='logged_in'
        elif a=='attendance':s,m=manual_attendance(); ok=s in OK_STATES
        elif a=='paste':
            ok,m=paste_into_browser(p.get('text',[''])[0]); return self.sendx({'ok':ok,'message':m},True,200 if ok else 400)
        else:return self.sendx({'ok':False,'message':'unsupported'},True,400)
        self.sendx({'ok':ok,'state':s,'message':m},True)
def start_ui():
    srv=ThreadingHTTPServer(('127.0.0.1',WEB_PORT),Handler); threading.Thread(target=srv.serve_forever,daemon=True).start(); log('INFO','Ingress control UI listening behind nginx on port 8099.')
def at_time(n,t):return n.strftime('%H:%M')==t

def main():
    o=load_options(); log('INFO','Starting Toptoon Attendance Bot...'); cleanup_legacy_options(); log('INFO','Persistent Chromium profile: /data/chromium-profile'); log('INFO','Ingress opens the control/status UI. VNC is reserved for login renewal.'); log('INFO',f"Daily attendance: {o.get('run_time','00:30')} ({o.get('timezone','Asia/Seoul')}); retries +{o.get('retry_1_minutes',5)}m/+{o.get('retry_2_minutes',15)}m; mobile alert check: {o.get('mobile_alert_time','09:05')}; manual reminder: {o.get('manual_reminder_time','21:00')}"); start_ui()
    if o.get('run_on_start',False):run_with_retries(o)
    last=None
    while True:
        o=load_options(); n=now_local(o); key=n.strftime('%Y-%m-%d %H:%M'); today=n.date().isoformat()
        if key!=last:
            last=key; st=load_json(STATUS_PATH,{})
            if at_time(n,o.get('run_time','00:30')) and st.get('last_run_date')!=today:run_with_retries(o)
            st=load_json(STATUS_PATH,{})
            if at_time(n,o.get('mobile_alert_time','09:05')) and st.get('unresolved') and st.get('failure_date')==today and not st.get('mobile_notified'):
                log('INFO','Morning unresolved-failure recheck.'); s,m=check_attendance(); record_result(s,m)
                if s in OK_STATES:dismiss_failure(); success_notification(o,s)
                else:mobile_push(o.get('mobile_notify_entity','notify.ky17'),'Toptoon 출석 실패',f'{s}: {m}\n{failure_instruction()}'); save_status(mobile_notified=True)
            st=load_json(STATUS_PATH,{})
            if at_time(n,o.get('manual_reminder_time','21:00')) and st.get('manual_reminder_date')!=today:manual_reminder(o,n)
        time.sleep(5)
if __name__=='__main__':main()

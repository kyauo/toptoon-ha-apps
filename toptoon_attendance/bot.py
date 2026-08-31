import html, json, os, threading, time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs
from zoneinfo import ZoneInfo
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

OPTIONS_PATH=Path('/data/options.json'); STATUS_PATH=Path('/data/status.json')
PAGE_URL='https://toptoon.com/event/attendance'; WEB_PORT=8098
PERSISTENT_NOTIFICATION_ID='toptoon_attendance_failure'; OK_STATES={'success','already_done'}
BROWSER_LOCK=threading.Lock()

def load_json(p,d):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception:return d

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

def browser_driver():
    opts=Options(); opts.add_experimental_option('debuggerAddress','127.0.0.1:9222'); opts.binary_location='/usr/bin/chromium-browser'
    return webdriver.Chrome(service=Service('/usr/bin/chromedriver'),options=opts)
def page_text(d):
    try:return d.find_element(By.TAG_NAME,'body').text
    except Exception:return ''
def is_login_required(d):
    u=d.current_url.lower(); body=page_text(d).lower()
    return ('login' in u or 'member/login' in u or '로그인' in body and ('facebook' in body or '페이스북' in body))

def inspect_page():
    with BROWSER_LOCK:
        try:
            d=browser_driver(); d.get(PAGE_URL); WebDriverWait(d,25).until(lambda x:x.execute_script("return document.readyState") in ('interactive','complete')); time.sleep(3)
            if is_login_required(d): state,msg='login_required','Toptoon 로그인이 필요합니다. 로그인 브라우저를 열어 로그인해 주세요.'
            else: state,msg='logged_in','Toptoon 로그인 세션이 유지되고 있습니다.'
            save_status(login_state=state,login_message=msg,status_checked_at=now_local().isoformat(timespec='seconds'))
            log('INFO',f'Status check: {state} / {msg}'); return state,msg
        except Exception as e:
            msg=str(e)[:400]; save_status(login_state='browser_error',login_message=msg,status_checked_at=now_local().isoformat(timespec='seconds')); log('WARNING',f'Status check failed: {msg}'); return 'browser_error',msg

def check_attendance():
    with BROWSER_LOCK:
        try:
            d=browser_driver(); d.get(PAGE_URL); WebDriverWait(d,25).until(lambda x:x.execute_script("return document.readyState") in ('interactive','complete')); time.sleep(3)
            if is_login_required(d): return 'login_required','Toptoon 로그인이 필요합니다. 로그인 브라우저를 열어 로그인해 주세요.'
            # Run the site's attendance POST inside the real logged-in browser context.
            result=d.execute_async_script("""
const done=arguments[arguments.length-1];
fetch('/event/attendance',{method:'POST',credentials:'include',headers:{'Accept':'application/json, text/javascript, */*; q=0.01','Content-Type':'application/x-www-form-urlencoded; charset=UTF-8','X-Requested-With':'XMLHttpRequest'},body:'ci_token=null'})
.then(async r=>{let t=await r.text(); let j=null; try{j=JSON.parse(t)}catch(e){} done({ok:r.ok,status:r.status,json:j,text:t.slice(0,400)});})
.catch(e=>done({error:String(e)}));
""")
            if result.get('error'): return 'network_error',result['error']
            body=result.get('json')
            if not isinstance(body,dict): return 'invalid_response',f"HTTP {result.get('status')}: {result.get('text','')}"
            msg=str(body.get('message') or '')
            if body.get('result') is True:return 'success',msg or '출석 완료'
            if '이미 출석' in msg:return 'already_done',msg
            if body.get('errorType')=='login':return 'login_required',msg or '로그인이 만료되었습니다.'
            return 'failed',msg or json.dumps(body,ensure_ascii=False)[:300]
        except Exception as e:return 'browser_error',str(e)[:400]

def record_result(state,msg,manual=False):
    n=now_local(); u={'last_run_at':n.isoformat(timespec='seconds'),'last_result':state,'last_message':msg}
    if manual:u['manual_run_at']=n.isoformat(timespec='seconds')
    if state in OK_STATES:u.update(last_run_date=n.date().isoformat(),unresolved=False,failure_date=None,mobile_notified=False,today_status='출석 완료')
    save_status(**u)
def success_notification(o,state):
    if o.get('notify_on_success',True): mobile_push(o.get('mobile_notify_entity','notify.ky17'),'Toptoon 출석 완료','오늘 Toptoon 출석이 정상 확인되었습니다.' if state=='success' else '오늘 Toptoon은 이미 출석 완료 상태입니다.')
def failure_instruction(): return 'Home Assistant에서 Toptoon Attendance Bot을 열어 로그인 상태를 확인해 주세요. 로그인이 풀린 경우에만 로그인 브라우저를 열어 Toptoon에 다시 로그인하면 됩니다.'
def manual_attendance():
    log('INFO','Manual attendance test requested from Ingress UI.'); s,m=check_attendance(); record_result(s,m,True)
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
<div class="card"><div class="actions"><button id="checkBtn" class="primary" onclick="runAction('check',this)">지금 로그인 상태 확인</button><button id="attBtn" class="danger" onclick="if(confirm('오늘 미출석이면 실제 출석 요청을 실행합니다. 계속할까요?'))runAction('attendance',this)">지금 출석 테스트</button><a id="vncBtn" class="btn secondary" href="vnc/vnc.html?autoconnect=1&amp;resize=scale&amp;path=websockify">로그인 브라우저 열기</a></div><div id="busy" class="busy">처리 중... 잠시 기다려 주세요.</div><p class="note">로그인을 마치면 브라우저를 그냥 닫아도 됩니다. 로그인 상태는 /data/chromium-profile에 보존됩니다.</p></div>
<div class="card"><b>자동 실행</b><p class="note">매일 {o.get('run_time','00:30')} ({o.get('timezone','Asia/Seoul')}) · 재시도 +{o.get('retry_1_minutes',5)}분 / +{o.get('retry_2_minutes',15)}분 · 실패 확인 {o.get('mobile_alert_time','09:05')} · 수동 확인 알림 {o.get('manual_reminder_time','21:00')}</p><div class="label">마지막 출석 실행</div><div>{html.escape(fmt_time(st.get('last_run_at')))}</div><div class="label" style="margin-top:10px">마지막 결과</div><div><b>{html.escape(str(st.get('last_result','아직 없음')))}</b> {html.escape(str(st.get('last_message','')))}</div></div></div>
<script>async function runAction(a,b){{let c=document.getElementById('checkBtn'),d=document.getElementById('attBtn'),v=document.getElementById('vncBtn'),x=document.getElementById('busy');c.disabled=d.disabled=true;v.style.pointerEvents='none';v.style.opacity='.6';x.style.display='block';b.textContent=a==='attendance'?'출석 처리 중...':'상태 확인 중...';let done=false;let w=setTimeout(()=>{{if(!done)location.reload()}},60000);let ctl=new AbortController();let t=setTimeout(()=>ctl.abort(),55000);try{{let q=new URLSearchParams();q.set('do',a);q.set('ajax','1');let r=await fetch('action',{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded','X-Requested-With':'fetch'}},body:q,signal:ctl.signal,cache:'no-store'}});await r.json();done=true;clearTimeout(w);clearTimeout(t);setTimeout(()=>location.reload(),350)}}catch(e){{done=true;clearTimeout(w);clearTimeout(t);setTimeout(()=>location.reload(),700)}}}}</script></body></html>'''

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*a):return
    def sendx(self,obj,json_mode=False,status=200):
        data=(json.dumps(obj,ensure_ascii=False) if json_mode else obj).encode(); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8' if json_mode else 'text/html; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_GET(self):self.sendx(render_ui() if self.path.split('?',1)[0] in ('/','') else render_ui('알 수 없는 경로입니다.','warn'))
    def do_POST(self):
        if self.path.split('?',1)[0]!='/action':return self.sendx({'ok':False,'message':'bad request'},True,404)
        p=parse_qs(self.rfile.read(int(self.headers.get('Content-Length','0') or 0)).decode()); a=p.get('do',[''])[0]
        if a=='check':s,m=inspect_page(); ok=s=='logged_in'
        elif a=='attendance':s,m=manual_attendance(); ok=s in OK_STATES
        else:return self.sendx({'ok':False,'message':'unsupported'},True,400)
        self.sendx({'ok':ok,'state':s,'message':m},True)
def start_ui():
    srv=ThreadingHTTPServer(('127.0.0.1',WEB_PORT),Handler); threading.Thread(target=srv.serve_forever,daemon=True).start(); log('INFO','Ingress control UI listening behind nginx on port 8099.')
def at_time(n,t):return n.strftime('%H:%M')==t

def main():
    o=load_options(); log('INFO','Starting Toptoon Attendance Bot...'); log('INFO','Persistent Chromium profile: /data/chromium-profile'); log('INFO','Ingress opens the control/status UI. VNC is reserved for login renewal.'); log('INFO',f"Daily attendance: {o.get('run_time','00:30')} ({o.get('timezone','Asia/Seoul')}); retries +{o.get('retry_1_minutes',5)}m/+{o.get('retry_2_minutes',15)}m; mobile alert check: {o.get('mobile_alert_time','09:05')}; manual reminder: {o.get('manual_reminder_time','21:00')}"); start_ui()
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

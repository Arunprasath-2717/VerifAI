"""Isolated Chromium regression suite for the built VerifAI application.

Starts Vite Preview on a temporary loopback port and intercepts ALL API calls
inside the browser before application JavaScript executes. No actual database,
Firebase account, LLM credential, or backend service is required.

Run from anywhere: python3 frontend/tests/browser_regression.py
Requires: npm ci, npm run build, Chromium and matching ChromeDriver.
"""

import base64
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_http(url, timeout=20):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return
        except Exception:
            pass
        time.sleep(0.15)
    raise RuntimeError(f"Local test server did not start: {url}")


browser = (shutil.which(os.getenv("VERIFAI_CHROME_BIN", "chromium"))
           or shutil.which("google-chrome") or shutil.which("chrome")
           or shutil.which("chromium-browser"))
driver = shutil.which(os.getenv("VERIFAI_CHROMEDRIVER_BIN", "chromedriver"))
if not browser or not driver:
    raise SystemExit("Chromium/Google Chrome and matching ChromeDriver are required.")

PORT = free_port()
PREVIEW_PORT = free_port()
BASE = f"http://127.0.0.1:{PREVIEW_PORT}"
DRIVER = f"http://127.0.0.1:{PORT}"
preview = None
proc = None
sid = None
test_failure = False
profile_dir = tempfile.TemporaryDirectory(prefix="verifai-browser-test-")


def call(path, data=None, method=None):
    request = urllib.request.Request(
        DRIVER + path,
        data=None if data is None else json.dumps(data).encode(),
        method=method or ("POST" if data is not None else "GET"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"WebDriver HTTP {exc.code}: {detail[:950]}") from exc
    if isinstance(payload.get("value"), dict) and payload["value"].get("error"):
        raise RuntimeError(payload["value"])
    return payload


def js(script):
    return call(f"/session/{sid}/execute/sync", {"script": script, "args": []})["value"]


def wait(expr, seconds=9):
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        try:
            if js(f"return Boolean({expr});"):
                return True
        except Exception:
            pass
        time.sleep(.17)
    return False


def nav(path, query):
    call(f"/session/{sid}/url", {"url": BASE + path})
    return wait(query, 13)


def assert_ok(label, expression):
    truth = bool(js(f"return ({expression});"))
    print(("PASS " if truth else "FAIL ") + label, flush=True)
    if not truth:
        raise AssertionError(label)


JS = r"""
(() => {
  window.__phase4Errors = [];
  window.addEventListener('error', event => {
    window.__phase4Errors.push({
      message: String(event.message || ''),
      filename: String(event.filename || ''),
      stack: String(event.error?.stack || '').slice(0, 1200)
    });
  });
  window.addEventListener('unhandledrejection', event => {
    window.__phase4Errors.push({
      rejection: String(event.reason?.message || event.reason || ''),
      stack: String(event.reason?.stack || '').slice(0, 1200)
    });
  });
  try {
    if (sessionStorage.getItem('__verifaiTestGuest') === 'yes') {
      localStorage.removeItem('verifai_token');
      localStorage.removeItem('verifai_authenticated');
    } else {
      localStorage.setItem('verifai_token','phase4-isolated-test-no-real-token');
      localStorage.setItem('verifai_authenticated','true');
    }
  } catch {}
  window.__phase4Calls=[];
  const originalFetch=window.fetch.bind(window);
  const uuid='11111111-1111-4111-8111-111111111111';
  const iso='2026-10-22T08:00:00Z';
  const responds=(value,status=200)=>new Response(JSON.stringify(value),{
    status,headers: {'content-type':'application/json','X-Request-ID':'phase4-browser-fixture'}
  });
  window.fetch=async (request,options={})=>{
    const url=typeof request==='string'?request:request.url;
    if(!url.includes('/api/v1/')) return originalFetch(request,options);
    const resource=new URL(url,location.href);
    const path=resource.pathname;
    const method=options.method||'GET';
    const body=options.body?String(options.body):null;
    window.__phase4Calls.push({method,path,query:resource.search,body});
    if(path.endsWith('/auth/username-availability')&&method==='GET'){
      const username=(resource.searchParams.get('username')||'').toLowerCase();
      return responds({username,available:username!=='reserved_name'});
    }
    if(path.endsWith('/auth/register')&&method==='POST'){
      const data=JSON.parse(body);
      window.__phase4CreatedAccount=data;
      return responds({id:uuid,username:data.username,email:data.email,role:'USER',is_active:true,created_at:iso},201);
    }
    if(path.endsWith('/auth/login')&&method==='POST'){
      const data=JSON.parse(body);
      window.__phase4PasswordLogin=data;
      return responds({access_token:'isolated-browser-credential',token_type:'bearer',expires_in:3600,role:'USER',user_id:uuid});
    }
    if(path.endsWith('/auth/me')){
      if(sessionStorage.getItem('__verifaiTestGuest')==='yes'){
        return responds({error:{message:'Authentication required'}},401);
      }
      return responds({
        id:uuid, username:'Test Account', email:'browser.test@example.invalid',
        role:'USER',is_active:true,created_at:iso
      });
    }
    if(path.endsWith('/history/verifications'))return responds({total:0,items:[]});
    if(path.endsWith('/knowledge/documents'))return responds({total_documents:0,documents:[]});
    if(path.endsWith('/providers/chat-models/probe')&&method==='POST'){
      const model=JSON.parse(body);
      const working=!window.__phase4ProbeFail;
      return responds({provider:model.provider,model:model.model_name,
        working,status:working?'WORKING':'UNAVAILABLE',
        message:working?'Completion test succeeded.':'Isolated test: model quota reached.',
        latency_ms:93});
    }
    if(path.endsWith('/providers/chat-models'))return responds({
      providers:[
        {providerId:'prov-groq',name:'Groq',
         status:window.__phase4GroqVerified?'Connected':window.__phase4GroqRejected?'Unavailable':window.__phase4SavedKey?'Saved':'Not Connected',
         keyMasked:window.__phase4SavedKey?'gsk_•••test':null,modelsCount:window.__phase4GroqVerified?1:0},
        {providerId:'prov-openrouter',name:'OpenRouter',status:'Connected',
         keyMasked:'sk-o•••test',modelsCount:3},
        {providerId:'prov-custom-nvidia-6187',name:'Nvidia',status:'Connected',
         keyMasked:'nvap•••test',modelsCount:1}
      ],
      models:[
        {id:'meta-llama/llama-3.3-8b-instruct:free',name:'Llama Free',
         provider:'openrouter',providerId:'prov-openrouter',
         contextWindow:64000,isFree:true,description:'OpenRouter free route'},
        {id:'demo-architecture-a:free',name:'Architecture A',
          provider:'openrouter',providerId:'prov-openrouter',
          contextWindow:64000,isFree:true,description:'Second free text model'},
        {id:'demo-architecture-b:free',name:'Architecture B',
          provider:'openrouter',providerId:'prov-openrouter',
          contextWindow:64000,isFree:true,description:'Third free text model'},
        {id:'nvidia/nemotron-mini-test',name:'NVIDIA Demo',
          provider:'prov-custom-nvidia-6187',providerId:'prov-custom-nvidia-6187',
          contextWindow:32000,isFree:false,
          description:'Synthetic NVIDIA model, browser-only fixture'},
        ...(window.__phase4GroqVerified?[{
          id:'llama-3.3-70b-versatile',name:'Llama 3.3 70B',
          provider:'groq',providerId:'prov-groq',
          contextWindow:128000,isFree:false,description:'Groq hosted model'
        }]:[])
      ]
    });
    if(path.endsWith('/providers/prov-groq/key')&&method==='POST'){
      window.__phase4SavedKey=true;
      return responds({id:'prov-groq',name:'Groq Cloud',status:'Saved',
        category:'cloud',keyMasked:'gsk_•••test',models:[]});
    }
    if(path.endsWith('/providers/prov-groq/test')&&method==='POST'){
      if(window.__phase4RejectGroq){
        window.__phase4GroqVerified=false;
        window.__phase4GroqRejected=true;
        return responds({id:'prov-groq',success:false,status:'INVALID_KEY',
          message:'The provider rejected this API key.',latency_ms:40});
      }
      window.__phase4GroqVerified=true;
      window.__phase4GroqRejected=false;
      return responds({id:'prov-groq',success:true,status:'VALID',
        message:'Credential accepted by the provider.',latency_ms:40});
    }
    if(path.endsWith('/providers')&&window.__phase4ProvidersFail){
      return responds({error:{message:'Isolated provider sidebar status failure'}},503);
    }
    if(path.endsWith('/providers'))return responds(['groq','openrouter'].map(name=>({
      id:'prov-'+name,name,category:'cloud',
      status:name==='openrouter'||window.__phase4GroqVerified?'Connected':'Not Connected',
      keyMasked:name==='openrouter'?'***-test':window.__phase4GroqVerified?'gsk_•••test':null
    })));
    if(path.endsWith('/chat/conversations')&&method==='GET')return responds({total:0,items:[]});
    if(path.endsWith('/chat/conversations')&&method==='POST'&&window.__phase4FailCreate) {
      return responds({error:{message:'Isolated test: session creation unavailable'}},503);
    }
    if(path.endsWith('/chat/conversations')&&method==='POST')return responds({
      id:uuid,title:'New Multi-Model Session',updated_at:iso,created_at:iso,message_count:0,owner_id:'test-account'
    });
    if(path.endsWith('/chat/conversations/'+uuid)&&method==='GET'){
      const saved=sessionStorage.getItem('__phase4SavedRun');
      const posted=saved?JSON.parse(saved):null;
      const messages=posted?[{
        id:uuid,conversation_id:uuid,owner_id:'test-account',role:'USER',
        sequence_number:1,created_at:iso,content:posted.prompt,
        synthesis:sessionStorage.getItem('__phase4Summary')?{
          text:'Combined browser-only architecture response',
          method:'LLM_SYNTHESIS',status:'UNVERIFIED',
          source_models:posted.models.map(m=>m.provider+'/'+m.model_name)
        }:null,
        llm_runs:posted.models.map(m=>({
          id:uuid,conversation_id:uuid,message_id:uuid,owner_id:'test-account',
          provider:m.provider,model_name:m.model_name,status:'COMPLETED',
          response:'Browser-only response for '+m.model_name,latency_ms:125,
          prompt:posted.prompt,started_at:iso
        }))
      }]:[];
      return responds({
        id:uuid,owner_id:'test-account',title:'New Multi-Model Session',
        created_at:iso,updated_at:iso,messages
      });
    }
    if(path.endsWith('/chat/conversations/'+uuid)&&method==='DELETE'){
      sessionStorage.removeItem('__phase4SavedRun');
      sessionStorage.removeItem('__phase4Summary');
      return responds({deleted:true,conversation_id:uuid});
    }
    if(path.endsWith('/chat/conversations/'+uuid+'/messages')&&method==='POST'){
      const posted=JSON.parse(body);
      sessionStorage.setItem('__phase4SavedRun',JSON.stringify(posted));
      sessionStorage.removeItem('__phase4Summary');
      return responds({conversation_id:uuid,prompt:posted.prompt,user_message_id:uuid,
        cross_model_disagreement:false,
        synthesis:null,
        runs:posted.models.map(m=>({
          provider:m.provider,model_name:m.model_name,status:'COMPLETED',
          response:'Browser-only response for '+m.model_name,latency_ms:125,
          id:uuid,conversation_id:uuid,owner_id:uuid,prompt:posted.prompt,started_at:iso
        }))
      });
    }
    if(path.endsWith('/chat/conversations/'+uuid+'/messages/'+uuid+'/summarize')&&method==='POST'){
      const posted=JSON.parse(sessionStorage.getItem('__phase4SavedRun')||'{}');
      sessionStorage.setItem('__phase4Summary','yes');
      return responds({
        text:'Combined browser-only architecture response',
        method:'LLM_SYNTHESIS',status:'UNVERIFIED',
        source_models:(posted.models||[]).map(m=>m.provider+'/'+m.model_name)
      });
    }
    // Direct result URL with no related evidence, judges or audit events.
    if(path.endsWith('/verification/22222222-2222-4222-8222-222222222222')&&method==='GET'){
      return responds({
        verification_id:'22222222-2222-4222-8222-222222222222',
        owner_id:'test-account',status:'COMPLETED',created_at:iso,
        input_text:'An isolated verification with no detail records',
        content_type:'FACTUAL',total_claims:1,supported_claims:0,
        contradicted_claims:0,unknown_claims:1,non_factual_claims:0,
        is_calibrated:false,
        claims:[{id:'empty-claim',claim_index:0,claim_text:'Unknown claim',
          content_type:'FACTUAL',verdict:'UNKNOWN',confidence:null,
          is_verifiable:true,is_calibrated:false,evidence:[],judges:[]}],
        audit_trail:[]
      });
    }
    if(path.endsWith('/verification')&&method==='POST') {
      if(window.__phase4FailVerify) {
        return responds({error:{message:'Isolated test: verification unavailable'}},503);
      }
      const posted=JSON.parse(body);
      await new Promise(resolve=>setTimeout(resolve,350));
      // Isolated test-only response with 5 claims, 15 evidence items,
      // 5 recorded judge evaluations and 3 audit entries.
      const claims=Array.from({length:5},(_,i)=>({
        id:'claim-'+i,claim_index:i,
        claim_text:i===0?'Browser-only synthetic assertion':'Isolated claim '+(i+1),
        content_type:'FACTUAL',verdict:i<2?'SUPPORTED':i===2?'CONTRADICTED':'UNKNOWN',
        is_verifiable:true,is_calibrated:false,confidence:null,
        evidence:Array.from({length:3},(_,j)=>({
          id:'source-'+i+'-'+j,source_url:'https://example.org/reference/'+i+'/'+j,
          source_title:'Regression source '+(i+1)+'.'+(j+1),
          snippet:'Test evidence excerpt '+(i+1)+'.'+(j+1),
          publisher:'Regression publisher',publication_date:'2026-10-01',
          retriever_name:'isolated-test',evidence_source:'EXTERNAL',
          relevance_score:0.91,authority_score:0.83
        })),
        judges:[{
          id:'judge-'+i,judge_name:'Test Judge '+(i+1),
          judgment:i<2?'SUPPORTED':i===2?'CONTRADICTED':'UNKNOWN',
          confidence:0.73,rationale:'Test judgment rationale '+(i+1),
          evidence_references:['source-'+i+'-0']
        }]
      }));
      const audit_trail=Array.from({length:3},(_,i)=>({
        id:'audit-'+i,stage:'Test stage '+(i+1),
        event_type:'ISOLATED_TEST',status:'COMPLETED',
        message:'Test audit recorded event '+(i+1),timestamp:iso
      }));
      return responds({verification_id:uuid,owner_id:'test-account',status:'COMPLETED',
        input_text:posted.text,query:posted.text,content_type:'FACTUAL',
        total_claims:5,supported_claims:2,contradicted_claims:1,unknown_claims:2,
        non_factual_claims:0,is_calibrated:false,created_at:iso,
        claims,audit_trail
      });
    }
    if(path.endsWith('/models/public-benchmarks'))return responds(window.__phase4PublicBenchmarkSnapshot);
    if(path.endsWith('/models/leaderboard'))return responds([]);
    if(path.endsWith('/dashboard/stats'))return responds({verifications_count:0,claims_count:0,
      conversations_count:0,evidence_sources_count:0,weekly_chart_data:[],monthly_chart_data:[],
      recent_verifications:[],stat_cards:[],leaderboard_preview:[]});
    if(path.endsWith('/reports/analytics')) {
      if (sessionStorage.getItem('__phase4ReportsWithData')==='yes') {
        const range=resource.searchParams.get('timeframe')||'30D';
        const count=range==='7D'?7:range==='90D'?30:range==='1Y'?27:30;
        const chart_data=Array.from({length:count},(_,index)=>{
          const offset=(count-index-1)*(range==='1Y'?14:range==='90D'?3:1);
          const date=new Date(Date.UTC(2026,9,24-offset)).toISOString().slice(0,10);
          return {date,day:date.slice(5),claims:index===count-3?38:index===count-2?35:index===count-1?4:index%9===0?1:0,
                  evidence:index%7===0?2:0,verifications:index===count-3?8:index===count-2?6:0};
        });
        return responds({
          timeframe:range,total_verifications:66,total_claims:120,average_trust_score:0,
          supported_rate:57.6,unknown_rate:34.8,contradicted_rate:6.1,chart_data,
          model_usage:[
            {model:'openai/gpt-oss-120b',usage:13},
            {model:'qwen/qwen3.8-27b',usage:9},
            {model:'anthropic/claude-sonnet-5.5-2026-10-21',usage:5},
            {model:'google/gemini-4-argon',usage:4}
          ],
          evidence_sources:[
            {domain:'en.wikipedia.org',count:16},
            {domain:'youtube.com',count:7},
            {domain:'www.businessinsider.com',count:6},
            {domain:'long-academic-journal.publisher.example.org',count:5},
            {domain:'medium.com',count:3},
          ],
        });
      }
      return responds({
        timeframe:'30D',total_verifications:0,total_claims:0,average_trust_score:0,
        supported_rate:0,unknown_rate:0,contradicted_rate:0,chart_data:[],
        model_usage:[],evidence_sources:[]
      });
    }
    return responds({error:{message:'Unexpected request in isolated browser test: '+path}},503);
  };
})();
"""

try:
    if not (ROOT / "dist/index.html").is_file():
        raise RuntimeError("Production build missing. Run 'npm run build' first.")
    preview = subprocess.Popen(
        [str(ROOT / "node_modules/.bin/vite"), "preview",
         "--host", "127.0.0.1", "--port", str(PREVIEW_PORT), "--strictPort"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    wait_http(BASE + "/")
    proc = subprocess.Popen(
        [driver, f"--port={PORT}", "--allowed-ips=127.0.0.1"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    wait_http(DRIVER + "/status")

    options = {"binary": browser,
               "args": ["--headless=new", "--no-sandbox", "--disable-gpu",
                        "--disable-dev-shm-usage", "--disable-extensions",
                        "--disable-background-networking", "--no-first-run",
                        "--window-size=1440,960",
                        f"--user-data-dir={profile_dir.name}"]}
    session = call("/session", {
        "capabilities": {"alwaysMatch": {
            "browserName": "chrome", "pageLoadStrategy": "none",
            "goog:chromeOptions": options,
        }}
    })
    sid = session.get("sessionId") or session["value"].get("sessionId")
    public_fixture = json.loads(
        (ROOT.parent / "backend/app/data/public_model_leaderboard.json").read_text(encoding="utf-8")
    )
    injected_script = (
        "window.__phase4PublicBenchmarkSnapshot="
        + json.dumps(public_fixture, ensure_ascii=True, separators=(",", ":"))
        + ";\n" + JS
    )
    call(f"/session/{sid}/goog/cdp/execute",
         {"cmd": "Page.addScriptToEvaluateOnNewDocument",
          "params": {"source": injected_script}})

    print("Phase 4: production-build browser regression with isolated API fixtures", flush=True)
    # First visit always opens the public landing, even with a valid session.
    root_loaded = nav("/", "document.querySelector('.verifai-landing h1')!==null")
    if not root_loaded:
        print("LANDING DEBUG", js("""return ({
            url: location.href,
            state: document.readyState,
            headingCount: document.querySelectorAll('h1').length,
            body: document.body.innerText.slice(0, 450),
            markup: document.querySelector('#root')?.innerHTML.slice(0, 450),
            scripts: [...document.querySelectorAll('script[src]')].map(x=>x.src),
            errors: window.__phase4Errors,
            resources: performance.getEntriesByType('resource').slice(0, 28)
              .map(x=>({url:x.name.split('/').pop(),status:x.responseStatus,duration:x.duration}))
        });"""), flush=True)
    assert root_loaded, "Root did not render landing"
    assert_ok("authenticated launch starts on landing, not dashboard",
              "location.pathname==='/' && document.querySelector('.verifai-landing h1')!==null")
    assert wait("document.querySelector('.vc-nav-login')?.getAttribute('href')==='/dashboard'",13), "Authenticated landing account link did not initialize"
    print("PASS landing account navigation leads to dashboard when signed in",flush=True)
    print("PASS landing shown before authenticated dashboard",flush=True)
    assert_ok("legacy full-screen loading interface is absent",
              "!document.body.innerText.includes('VERIFAI INTELLIGENCE CORE') && "
              "!document.body.innerText.includes('Establishing cryptographic handshake')")
    assert nav("/loading", "document.body.innerText.includes('404_DIAGNOSTIC')"), (
        "Removed /loading route still displays its previous loading interface"
    )
    assert_ok("removed diagnostic loading route is not reachable",
              "document.body.innerText.includes('404_DIAGNOSTIC') && "
              "!document.body.innerText.includes('VERIFAI INTELLIGENCE CORE')")
    print("PASS full-screen loader removed from app and former /loading URL",flush=True)

    # A returning authenticated user entering /login is taken to their dashboard.
    assert nav("/login", "location.pathname==='/dashboard'"), "Authenticated login did not forward to dashboard"
    assert wait("document.querySelector('aside[aria-label]')!==null"), "dashboard navigation did not hydrate"
    print('PASS dashboard navigation is rendered', flush=True)
    assert_ok("sidebar labels have readable 15px type",
              "parseFloat(getComputedStyle(document.querySelector('aside nav button span.whitespace-nowrap')).fontSize)>=15")
    js("""const sidebar=document.querySelector('aside[aria-label="Main Navigation"]');
          sidebar.dispatchEvent(new MouseEvent('mouseover',{bubbles:true}));return true;""")
    assert wait("document.querySelector('aside[aria-label]')?.offsetWidth>=255"), "Expanded sidebar width too narrow"
    print("PASS dashboard sidebar text and expanded width",flush=True)

    # Sidebar width has ONE owner; the dock, toolbar and hero must occupy
    # separate columns without colliding during either direction of motion.
    def workspace_geometry():
        return js('''const bounds=s=>{const e=document.querySelector(s);if(!e)return null;
          const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,right:r.right};};
          return {aside:bounds('aside[aria-label="Main Navigation"]'),
            column:bounds('.verifai-sidebar-column'),
            toolbar:bounds('.verifai-topbar-frame'),
            main:bounds('main'), hero:bounds('.mocha-dashboard-hero'),
            viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth};''')

    def aligned(g):
        return (abs(g['toolbar']['x']-g['hero']['x']) < 2 and
                abs(g['toolbar']['right']-g['hero']['right']) < 2 and
                g['aside']['right']+10 <= g['toolbar']['x'] and
                abs(g['aside']['width']-(g['column']['width']-12)) < 2 and
                g['scrollWidth'] <= g['viewport'] + 2)

    geometry_open = workspace_geometry()
    assert aligned(geometry_open), f'Expanded layout overlaps/misaligns: {geometry_open}'
    js('''document.querySelector('aside[aria-label="Main Navigation"]')
      .dispatchEvent(new MouseEvent('mouseout',{bubbles:true,relatedTarget:document.body}));return true;''')
    assert wait("document.querySelector('aside[aria-label]')?.getBoundingClientRect().width <= 66",4), 'Dock failed to contract'
    geometry_closed = workspace_geometry()
    assert aligned(geometry_closed), f'Collapsed layout overlaps/misaligns: {geometry_closed}'
    js('''document.querySelector('aside[aria-label="Main Navigation"]')
      .dispatchEvent(new MouseEvent('mouseover',{bubbles:true}));return true;''')
    time.sleep(.14)
    geometry_in_motion = workspace_geometry()
    assert 65 < geometry_in_motion['aside']['width'] < 260, f'No smooth interim width: {geometry_in_motion}'
    assert aligned(geometry_in_motion), f'Layout separated during motion: {geometry_in_motion}'
    assert wait("document.querySelector('aside[aria-label]')?.getBoundingClientRect().width >= 258",4), 'Dock failed to expand'
    print('PASS aligned desktop container and seamless bidirectional sidebar transition',flush=True)

    # At the narrowest desktop breakpoint there must still be room for toolbar.
    call(f"/session/{sid}/window/rect", {"width":1024, "height":900})
    assert wait("innerWidth === 1024",3), 'Could not test narrow desktop width'
    assert wait("document.querySelector('.verifai-sidebar-column')?.getBoundingClientRect().width>=270",4), 'Desktop sidebar not expanded at 1024px'
    assert aligned(workspace_geometry()), f'1024px desktop alignment failed: {workspace_geometry()}'
    call(f"/session/{sid}/window/rect", {"width":1440, "height":960})
    assert wait("innerWidth>=1400",3), 'Could not restore desktop viewport'
    assert aligned(workspace_geometry()), f'Restored desktop alignment failed: {workspace_geometry()}'
    print('PASS desktop sidebar, header and page alignment at 1024px and 1440px',flush=True)
    js("window.scrollTo(0, 760);return true;")
    assert wait("window.scrollY>500",3), 'Could not scroll dashboard for sticky-header test'
    chrome_scroll = js("""return {scroll:window.scrollY,header:document.querySelector('.verifai-workspace-header').getBoundingClientRect().top,
       dock:document.querySelector('aside[aria-label]').getBoundingClientRect().top,
       rootOverflow:getComputedStyle(document.querySelector('div.min-h-screen')).overflowX};""")
    print('STICKY_CHROME_SCROLL',chrome_scroll,flush=True)
    assert 4 <= chrome_scroll['header'] <= 13, f'Sticky toolbar did not stay visible: {chrome_scroll}'
    assert 4 <= chrome_scroll['dock'] <= 13, f'Sticky sidebar did not stay visible: {chrome_scroll}'
    print('PASS sticky sidebar and header remain aligned while scrolling',flush=True)
    js("window.scrollTo(0,0);return true;")
    assert wait("window.scrollY<2",3), 'Failed to reset dashboard scroll'

    # Mobile gets a contained toolbar and independent slide-over navigation.
    call(f"/session/{sid}/window/rect", {"width":390, "height":844})
    assert wait("innerWidth===390",3), 'Could not render mobile dashboard'
    mobile = js("""const h=document.querySelector('.verifai-topbar-frame').getBoundingClientRect();
      const v=document.querySelector('.mocha-dashboard-hero').getBoundingClientRect();
      return {headerLeft:h.left,headerRight:h.right,heroLeft:v.left,heroRight:v.right,
        overflow:document.documentElement.scrollWidth-innerWidth,
        dock:getComputedStyle(document.querySelector('.verifai-sidebar-column')).display};""")
    assert (abs(mobile['headerLeft']-mobile['heroLeft'])<2 and
            abs(mobile['headerRight']-mobile['heroRight'])<2 and
            mobile['overflow']<=2 and mobile['dock']=='none'), f'Mobile toolbar/container alignment failed: {mobile}'
    js("document.querySelector('[aria-label=\"Open Navigation Menu\"]').click();return true;")
    assert wait("document.querySelector('aside[data-mobile=true]')!==null",4), 'Mobile sidebar drawer did not open'
    assert_ok('mobile drawer stays within viewport',
              "document.querySelector('aside[data-mobile=true]').getBoundingClientRect().width<=innerWidth")
    js("document.querySelector('[aria-label=\"Close Navigation Menu\"]').click();return true;")
    assert wait("document.querySelector('aside[data-mobile=true]')===null",4), 'Mobile drawer did not close'
    call(f"/session/{sid}/window/rect", {"width":1440, "height":960})
    assert wait("innerWidth>=1400",3), 'Unable to restore full desktop layout'
    print('PASS 390px mobile container alignment and navigation drawer',flush=True)




    if os.getenv("VERIFAI_CAPTURE_REDESIGN") == "1":
        screenshots=ROOT.parent / ".impeccable/review"
        screenshots.mkdir(parents=True,exist_ok=True)
        def save_capture(name):
            raw=call(f"/session/{sid}/screenshot")["value"]
            (screenshots/name).write_bytes(base64.b64decode(raw))
            print("VISUAL_CAPTURE",screenshots/name,flush=True)
        save_capture("dashboard-desktop.png")
        call(f"/session/{sid}/window/rect",{"width":390,"height":844})
        assert wait("innerWidth===390",3),'Dashboard mobile capture viewport failed'
        save_capture("dashboard-mobile.png")
        call(f"/session/{sid}/window/rect",{"width":1440,"height":960})
        assert wait("innerWidth>=1400",3),'Dashboard desktop restore failed'
    # Black-on-white/mint light UI checked against the rendered production DOM.
    if os.getenv("VERIFAI_CAPTURE_THEME") == "1":
        Path("/tmp/verifai-light-redesign.png").write_bytes(
            base64.b64decode(call(f"/session/{sid}/screenshot")["value"]))
        print("SAVED /tmp/verifai-light-redesign.png",flush=True)
        call(f"/session/{sid}/window/rect", {"width":390,"height":844})
        assert wait("innerWidth<=390",3), "Mobile viewport was not applied"
        print("MOBILE_DASHBOARD_SIZE",js("return ({innerWidth,docWidth:document.documentElement.scrollWidth,heroWidth:document.querySelector('.mocha-dashboard-hero')?.getBoundingClientRect().width,scrollHeight:document.documentElement.scrollHeight});"),flush=True)
        Path("/tmp/verifai-light-redesign-mobile.png").write_bytes(
            base64.b64decode(call(f"/session/{sid}/screenshot")["value"]))
        print("SAVED /tmp/verifai-light-redesign-mobile.png",flush=True)
        call(f"/session/{sid}/window/rect", {"width":1440,"height":960})
        assert wait("innerWidth>=1200",3), "Desktop viewport was not restored"
    assert_ok("dashboard canvas uses pale green #D8F3DC",
              "getComputedStyle(document.querySelector('div.min-h-screen')).backgroundColor==='rgb(216, 243, 220)'")
    assert_ok("hero is a contained, light mint digital globe image",
              "getComputedStyle(document.querySelector('.mocha-dashboard-hero')).backgroundImage.includes('hero_card_light_network_globe') && getComputedStyle(document.querySelector('.mocha-dashboard-hero')).borderTopLeftRadius==='17px'")
    assert_ok("hero primary action uses mint with BLACK text",
              "getComputedStyle(document.querySelector('.mocha-hero-primary')).backgroundColor==='rgb(116, 198, 157)' && getComputedStyle(document.querySelector('.mocha-hero-primary')).color==='rgb(0, 0, 0)'")
    assert_ok("dark dashboard information architecture is mirrored in the light theme",
              "document.querySelectorAll('.mocha-dashboard .lt-kpi-card').length===4 && document.querySelector('.mocha-trust-panel')!==null && document.querySelector('.mocha-empty-state')!==null")
    assert_ok("dashboard KPIs use black typography",
              "getComputedStyle(document.querySelector('.lt-kpi-card h4')).color==='rgb(0, 0, 0)'")
    assert_ok("light dashboard preserves leaderboard and quick action controls",
              "document.querySelector('.mocha-dashboard')?.textContent.includes('Quick Actions & Evaluation Engines') && document.querySelector('.mocha-dashboard')?.textContent.includes('Full Benchmark Matrix') && document.querySelector('.mocha-dashboard')?.textContent.includes('NOT MEASURED')")
    assert_ok("sidebar is white with black menu labels",
              "getComputedStyle(document.querySelector('aside[aria-label]')).backgroundColor==='rgb(255, 255, 255)' && getComputedStyle(document.querySelector('aside nav button span.whitespace-nowrap')).color==='rgb(0, 0, 0)'")
    assert_ok("empty VerifAI-measured leaderboard honestly indicates pending evaluations",
              "document.querySelector('.mocha-dashboard')?.textContent.includes('Your benchmark story starts with real evaluations') && document.querySelectorAll('.mocha-empty-state').length>=1")
    black_text_violations = js("""return [...document.querySelectorAll('.verifai-olive-shell *')]
      .filter(e => !e.closest('svg') && ['SCRIPT','STYLE','NOSCRIPT'].indexOf(e.tagName)<0 &&
        [...e.childNodes].some(n => n.nodeType===3 && n.textContent.trim()) &&
        e.getBoundingClientRect().width>0 && e.getBoundingClientRect().height>0 &&
        getComputedStyle(e).visibility!=='hidden' &&
        getComputedStyle(e).color!=='rgb(0, 0, 0)' &&
        !e.closest('.mocha-dashboard-hero h1') &&
        !e.closest('.mocha-trust-panel .border-t'))
      .slice(0,20).map(e => ({tag:e.tagName,text:e.textContent.trim().slice(0,32),color:getComputedStyle(e).color}));""")
    print("LIGHT BLACK TEXT AUDIT",black_text_violations,flush=True)
    assert_ok("primary dashboard headings retain black readable ink",
              "getComputedStyle(document.querySelector('.mocha-dashboard h3')).color==='rgb(0, 0, 0)' && getComputedStyle(document.querySelector('.mocha-hero-primary')).color==='rgb(0, 0, 0)'")
    print('PASS white / olive / pale green dashboard with black typography',flush=True)

    # New styling applies to light mode only; dark remains independent.
    js("document.querySelector('button[aria-label=\"Switch to Dark Theme\"]').click();return true;")
    assert wait("document.documentElement.classList.contains('dark') && document.querySelector('.mocha-dashboard')===null && document.querySelector('.verifai-olive-shell')===null"), 'Olive light styling leaked into dark mode'
    assert wait("getComputedStyle(document.querySelector('div.min-h-screen')).backgroundColor==='rgb(24, 26, 32)'", 4), "Dark canvas did not return to original charcoal #181A20"
    assert_ok("dark hero uses the uploaded neon network globe artwork",
              "getComputedStyle(document.querySelector('.mocha-dashboard-hero')).backgroundImage.includes('hero_card_dark_network_globe')")
    if os.getenv("VERIFAI_CAPTURE_DARK_HERO") == "1":
        Path("/tmp/verifai-dark-hero-updated.png").write_bytes(
            base64.b64decode(call(f"/session/{sid}/screenshot")["value"]))
        print("SAVED /tmp/verifai-dark-hero-updated.png", flush=True)

    js("document.querySelector('button[aria-label=\"Switch to Light Theme\"]').click();return true;")
    assert wait("!document.documentElement.classList.contains('dark') && document.querySelector('.mocha-dashboard')!==null && document.querySelector('.verifai-olive-shell')!==null"), 'Unable to restore black-text light dashboard'
    print('PASS original dark theme remains separate from olive light theme',flush=True)

    assert nav("/reports/models", "document.body.innerText.includes('AI Model Leaderboard')"), 'Public leaderboard route missing'
    assert wait("document.body.innerText.includes('LiveBench 2.0') && document.querySelectorAll('table tbody tr').length>=20", 7), 'Source benchmark scores did not render'
    assert_ok('public leaderboard data is attributed and dated',
              "document.body.textContent.includes('Independent benchmark data') && document.querySelector('a[href^=\"https://livebench.ai/\"]')!==null")
    assert_ok('latest published model appears with measured score',
              "document.body.innerText.includes(window.__phase4PublicBenchmarkSnapshot.models[0].name) && document.body.innerText.includes(window.__phase4PublicBenchmarkSnapshot.models[0].overall_score.toFixed(1))")
    js("document.querySelector('button[aria-label^=\"View benchmark details for\"]').click();return true;")
    assert wait("document.querySelector('[role=dialog]')?.textContent.includes('Official overall score')", 4), 'Benchmark detail modal failed'
    assert_ok('public detail modal lists seven source metrics',
              "document.querySelector('[role=dialog]')?.textContent.includes('Agentic tasks') && document.querySelector('[role=dialog]')?.textContent.includes('Research')")
    js("document.querySelector('button[aria-label=\"Close model details\"]').click();return true;")
    assert wait("document.querySelector('[role=dialog]')===null",4), 'Leaderboard details did not close'
    js("document.querySelector('[role=tab][aria-selected=false]').click();return true;")
    assert wait("document.body.innerText.includes('No internally measured model rankings yet')",4), 'Empty first-party data was misrepresented'
    assert_ok('private VerifAI leaderboard remains distinct from public scores',
              "document.querySelector('[role=tab][aria-selected=true]')?.textContent.includes('VerifAI evaluations')")
    js("document.querySelector('[role=tab][aria-selected=false]').click();return true;")
    call(f"/session/{sid}/window/rect", {"width":390,"height":844})
    assert wait("innerWidth===390",3), 'Could not resize model leaderboard'
    assert_ok('mobile benchmark layout has no document-level horizontal overflow',
              "document.documentElement.scrollWidth<=innerWidth+2 && document.querySelectorAll('button[aria-label^=\"Details for\"]').length>=20")
    call(f"/session/{sid}/window/rect", {"width":1440,"height":960})
    assert wait("innerWidth>=1400",3), 'Could not reset benchmark viewport'
    print('PASS sourced LiveBench public leaderboard, modal, separate VerifAI tab and mobile layout',flush=True)

    assert nav("/chat", "document.body.innerText.includes('AI Chat Workspace')"), "Chat did not load"
    assert_ok("chat workspace renders after route-splitting",
              "document.body.innerText.includes('AI Chat Workspace')")
    assert_ok("chat uses same-origin API",
              "window.__phase4Calls.some(r=>r.path.endsWith('/auth/me'))")

    js("""const btn=[...document.querySelectorAll('button')].find(b=>b.textContent.includes('New Multi-Model Session'));btn.click();return true;""")
    if not wait("location.pathname.includes('11111111')"):
        raise AssertionError("new session did not navigate to backend UUID")
    assert_ok("new chat route uses backend UUID",
              "location.pathname==='/chat/11111111-1111-4111-8111-111111111111'")
    assert_ok("created conversation through POST",
              "window.__phase4Calls.some(x=>x.path.endsWith('/chat/conversations')&&x.method==='POST')")
    assert_ok("no fabricated conv- timestamp IDs in URL",
              "!location.pathname.includes('conv-')")

    assert_ok('catalogue candidates are not automatically trusted or selected',
              "document.querySelector('[data-testid=selected-models-workspace]')?.textContent.includes('0 of 3 ready')")
    js("window.__phase4ProbeFail=true;return true;")
    js("""const b=document.querySelector('button[aria-label^="Test and select Llama Free"]');
          if(!b)throw new Error('Missing live model probe action');b.click();return true;""")
    assert wait("document.body.innerText.includes('Isolated test: model quota reached.')"), 'Failed model probe marked as working'
    assert_ok('unavailable model is not selected',
              "document.querySelector('[data-testid=selected-models-workspace]')?.textContent.includes('0 of 3 ready')")
    js("window.__phase4ProbeFail=false;return true;")
    js("""const b=document.querySelector('button[aria-label^="Test and select Llama Free"]');
          if(!b)throw new Error('Missing model retest action');b.click();return true;""")
    assert wait("document.querySelector('[data-testid=selected-models-workspace]')?.textContent.includes('1 of 3 ready')"), 'Working model was not selected'
    assert_ok('linked NVIDIA custom provider appears in the chat BYOK sidebar',
              "document.body.innerText.includes('Nvidia') && document.body.innerText.includes('Manage custom connection')")
    for label in ('Architecture A','NVIDIA Demo'):
        js("const b=document.querySelector('button[aria-label^=\"Test and select '+%r+'\"]');if(!b)throw new Error('Missing additional model');b.click();return true;" % label)
        assert wait("window.__phase4Calls.filter(x=>x.path.endsWith('/providers/chat-models/probe')).length>="+str(3 if label=='Architecture A' else 4)), 'Additional probe not performed'
    assert wait("document.querySelector('[data-testid=selected-models-workspace]')?.textContent.includes('3 of 3 ready')"), 'Selected model panel did not show all three lanes'
    assert_ok('synthesis studio and editor options are removed',
              "document.querySelector('[data-testid=synthesis-model-workspace]')===null && !document.querySelector('#synthesis-model') && !document.querySelector('#synthesis-focus') && !document.querySelector('#synthesis-rounds')")
    print('PASS real-probe workflow, failed test rejection and three separate model lanes',flush=True)
    if os.environ.get('VERIFAI_CHAT_VISUAL') == '1':
        time.sleep(0.8)
        (Path('/tmp')/'verifai-chat-selected-workspace.png').write_bytes(
            base64.b64decode(call(f"/session/{sid}/screenshot")["value"])
        )


    js("""const el=document.querySelector('textarea[placeholder^="Ask anything"]');
          const setter=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set;
          setter.call(el,'How are electric vehicles evaluated?');
          el.dispatchEvent(new Event('input',{bubbles:true}));
          return true;""")
    if not wait("document.querySelector('textarea[placeholder^=\"Ask anything\"]')?.value.length>0"):
        raise AssertionError("chat prompt input failed")
    js("""document.querySelector('textarea[placeholder^="Ask anything"]').closest('form').requestSubmit();return true;""")
    if not wait("window.__phase4Calls.some(x=>x.path.endsWith('/messages')&&x.method==='POST')"):
        print('CHAT_SEND_DEBUG',js("""return ({
          url:location.href,errors:window.__phase4Errors,
          selected:document.querySelector('[data-testid=selected-models-workspace]')?.innerText,
          prompt:document.querySelector('textarea[placeholder^="Ask anything"]')?.value,
          sendDisabled:document.querySelector('textarea[placeholder^="Ask anything"]')?.closest('form')?.querySelector('button[type=submit]')?.disabled,
          errorsShown:[...document.querySelectorAll('[role=alert]')].map(e=>e.textContent),
          calls:window.__phase4Calls.slice(-13).map(x=>({path:x.path,method:x.method}))
        })"""),flush=True)
        raise AssertionError("chat POST was not sent")
    assert_ok('three tested models receive the same prompt including saved NVIDIA custom BYOK',
              "(()=>{const p=JSON.parse(window.__phase4Calls.find(x=>x.path.endsWith('/messages')&&x.method==='POST').body);return p.models.length===3 && p.verify===true && p.models.some(m=>m.provider==='prov-custom-nvidia-6187'&&m.model_name==='nvidia/nemotron-mini-test')})()")
    assert_ok('chat submission no longer requests automatic synthesis or review cycles',
              "(()=>{const p=JSON.parse(window.__phase4Calls.find(x=>x.path.endsWith('/messages')&&x.method==='POST').body);return !('synthesizer' in p) && !('refinement_rounds' in p) && !('synthesis_focus' in p)})()")
    assert_ok("exact free OpenRouter model ID is sent",
              """JSON.parse(window.__phase4Calls.find(x=>x.path.endsWith('/messages')&&x.method==='POST').body)
                  .models.some(m=>m.provider==='openrouter'&&m.model_name==='meta-llama/llama-3.3-8b-instruct:free')""")
    if not wait("document.body.innerText.includes('Browser-only response for')"):
        raise AssertionError("model response did not render")
    assert_ok('summary does not appear before user clicks',
              "document.querySelector('[data-testid=combined-summary]')===null")
    assert wait("!!document.querySelector('[data-testid=summarize-response]')"), 'Summarize button missing'
    js("document.querySelector('[data-testid=summarize-response]').click();return true;")
    assert wait("document.querySelector('[data-testid=combined-summary]')?.textContent.includes('Combined browser-only architecture response')"), 'On-demand summary missing'
    assert_ok('one summary API call, without re-sending original prompt',
              "window.__phase4Calls.filter(x=>x.path.endsWith('/summarize')&&x.method==='POST').length===1")
    assert_ok('summary explicitly declines to present model consensus as verified evidence',
              "document.querySelector('[data-testid=combined-summary]')?.textContent.includes('not independently verified')")
    print('PASS three-model prompting and on-demand summarization',flush=True)
    if os.environ.get('VERIFAI_CHAT_VISUAL') == '1':
        time.sleep(0.8)
        (Path('/tmp')/'verifai-chat-synthesis.png').write_bytes(
            base64.b64decode(call(f"/session/{sid}/screenshot")["value"])
        )

    assert_ok("server model response visible",
              "document.body.innerText.includes('Browser-only response for meta-llama/llama-3.3-8b-instruct:free')")

    # Reload the route in a fresh document. Test-only persistent API data
    # must reconstruct the user prompt and model reply from a saved USER run.
    assert nav('/chat/11111111-1111-4111-8111-111111111111',
               "document.body.innerText.includes('AI Chat Workspace')"), 'Reloaded chat route missing'
    assert wait("document.body.innerText.includes('How are electric vehicles evaluated?')"), 'Saved user message missing'
    assert wait("document.body.innerText.includes('Browser-only response for meta-llama/llama-3.3-8b-instruct:free')"), 'Saved model reply missing after reload'
    assert wait("document.body.innerText.includes('Combined browser-only architecture response')"), 'Saved synthesis not restored after reload'
    assert_ok("chat reload reconstructs actual saved user plus assistant run",
              "window.__phase4Calls.some(r=>r.path.includes('/chat/conversations/11111111')&&r.method==='GET')")
    print("PASS persisted model responses restored after browser reload",flush=True)

    # BYOK: save an ephemeral fake Groq key in the mocked backend, then test.
    js("""const btn=[...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='Add API key');
          if (!btn) throw new Error('Groq key form not found');btn.click();return true;""")
    assert wait("document.getElementById('key-prov-groq')!==null"), 'Groq key input missing'
    js("""const field=document.getElementById('key-prov-groq');
          const setValue=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
          setValue.call(field,'gsk-isolated-browser-test-key');
          field.dispatchEvent(new Event('input',{bubbles:true}));return true;""")
    assert wait("document.getElementById('key-prov-groq')?.value.length>0"),'Could not enter Groq key'
    js("""document.getElementById('key-prov-groq').closest('form').requestSubmit();return true;""")
    assert wait("window.__phase4GroqVerified===true"), 'Provider verification not triggered'
    assert wait("document.body.innerText.includes('Llama 3.3 70B')"), 'Connected Groq model not discovered'
    assert_ok("Groq key saved and tested, model list refreshed",
              "window.__phase4Calls.some(x=>x.path.endsWith('/providers/prov-groq/key')&&x.method==='POST') && window.__phase4Calls.some(x=>x.path.endsWith('/providers/prov-groq/test')&&x.method==='POST')")
    print("PASS BYOK save, live check and model discovery UI",flush=True)

    # An unrelated provider-settings status error must not erase already
    # discovered model choices or prevent actual chat.
    js("window.__phase4ProvidersFail=true;return true;")
    js("""document.querySelector('button[aria-label="Refresh connected model list"]').click();return true;""")
    assert wait("window.__phase4Calls.some(r=>r.path.endsWith('/providers')&&r.method==='GET')"), 'Provider status refresh not attempted'
    assert wait("document.body.innerText.includes('Llama Free') && document.body.innerText.includes('Llama 3.3 70B')"), 'Working model catalog erased on unrelated refresh failure'
    js("window.__phase4ProvidersFail=false;return true;")
    print("PASS model catalog survives unrelated provider-settings refresh failure",flush=True)

    # Provider rejects previously stored key: never leave it looking connected.
    js("window.__phase4RejectGroq=true;return true;")
    js("""const section=[...document.querySelectorAll('section')].find(s=>s.textContent.includes('Groq hosted model')===false&&s.querySelector('h3')?.textContent==='Groq');
          const test=section&&[...section.querySelectorAll('button')].find(b=>b.textContent.trim()==='Test');
          if(!test)throw new Error('Saved Groq Test button not found');
          test.click();return true;""")
    assert wait("window.__phase4GroqRejected===true"), 'Credential rejection not simulated'
    assert wait("document.body.innerText.includes('The provider rejected this API key')"), 'Provider failure not displayed'
    assert wait("!document.body.innerText.includes('Llama 3.3 70B')"), 'Revoked Groq model remains selectable'
    assert_ok("revoked credentials cannot present stale connected models",
              "document.body.innerText.includes('Needs attention')")
    print('PASS rejected BYOK key disconnects unavailable model',flush=True)

    # A failed new-session POST must not cause fabricated navigation or success.
    js("window.__phase4FailCreate=true;return true;")
    js("const btn=[...document.querySelectorAll('button')].find(b=>b.textContent.includes('New Multi-Model Session'));btn.click();return true;")
    assert wait("document.querySelector('[role=alert]')?.innerText.includes('Isolated test: session creation unavailable')"), "create-session failure was hidden"
    assert_ok("new-session failure leaves existing route intact",
              "location.pathname==='/chat/11111111-1111-4111-8111-111111111111'")
    js("window.__phase4FailCreate=false;return true;")
    print("PASS failed chat creation retains existing session and shows the server error",flush=True)

    # Delete requires confirmation, backend acknowledgement and UI removal.
    js("""window.confirm=()=>true;
          const btn=[...document.querySelectorAll('button')]
             .find(b=>b.getAttribute('aria-label')?.startsWith('Delete conversation '));
          if (!btn) throw new Error('Delete action missing');
          btn.click();return true;""")
    assert wait("window.__phase4Calls.some(r=>r.path.endsWith('/chat/conversations/11111111-1111-4111-8111-111111111111')&&r.method==='DELETE')"), 'Delete was not sent'
    assert wait("location.pathname==='/chat'"), 'Chat did not return to /chat after successful delete'
    assert_ok("deleted conversation removed after backend confirmation",
              "![...document.querySelectorAll('a')].some(a=>a.getAttribute('href')?.includes('11111111'))")
    print("PASS confirmed chat deletion updates UI and navigation",flush=True)
    # The selector must use successful real probes, never catalog-only guesses.
    js("""const b=document.querySelector('button[aria-label="Find working models"]');
          if(!b)throw new Error('Missing working-model selector');b.click();return true;""")
    assert wait("document.body.innerText.includes('selected after real inference checks')",8), 'Best-model selection did not complete'
    assert_ok('working-model picker leaves at least one validated lane',
              "document.querySelector('[data-testid=selected-models-workspace]')?.textContent.includes('of 3 ready') && !document.querySelector('[data-testid=selected-models-workspace]')?.textContent.includes('0 of 3 ready')")
    print('PASS working-model recommendation and validated lanes',flush=True)


    assert nav("/verify", "document.body.innerText.includes('Paste & Verify')"), "verify route did not render"
    js("""const btn=[...document.querySelectorAll('button')].find(b=>b.textContent.includes('Advanced Verification Options'));btn.click();return true;""")
    assert_ok("real backend max-claims control", "Boolean(document.querySelector('#verify-max-claims'))")
    assert_ok("strict consensus checkbox", "Boolean(document.querySelector('input[type=checkbox]'))")

    js("""const btn=[...document.querySelectorAll('button')].find(b=>b.textContent.includes('Verify Answer'));btn.click();return true;""")
    if not wait("window.__phase4Calls.some(x=>x.path.endsWith('/verification')&&x.method==='POST')"):
        raise AssertionError("verify POST was not sent")
    assert_ok("verification parameters match backend schema",
              """(()=>{const x=JSON.parse(window.__phase4Calls.find(x=>x.path.endsWith('/verification')).body);
              return x.options.max_claims===20&&x.options.strict_consensus===true&&!('strictness' in x.options)})()""")
    if not wait("location.pathname.startsWith('/verification/')"):
        raise AssertionError("verify result navigation failed")
    def select_result_tab(tab_name):
        # A concurrent result-detail hydration may reset the active tab once;
        # target a stable mounted tab and retry click after that hydration.
        for attempt in range(3):
            if wait(f"document.querySelector('#verification-tab-{tab_name}')!==null", 2):
                js(f"document.getElementById('verification-tab-{tab_name}').click();return true;")
            if wait(f"document.getElementById('verification-tab-{tab_name}')?.getAttribute('aria-selected')==='true'", 3):
                return
        raise AssertionError(f"Tab did not become active: {tab_name}")

    # Each tab displays only its own content, not all sections at once.
    assert wait("document.querySelector('#verification-tab-overview')?.getAttribute('aria-selected')==='true'", 8), "Overview tab was not selected after result hydration"
    print("PASS Overview tab selected by default", flush=True)
    assert_ok("Overview contains original answer and summary",
              "document.querySelector('[role=tabpanel]')?.textContent.includes('Original Answer Audited') && document.querySelector('[role=tabpanel]')?.textContent.includes('Verification Summary')")
    assert_ok("Overview is not showing the claims breakdown",
              "!document.querySelector('[role=tabpanel]')?.textContent.includes('Claims Breakdown')")
    assert_ok("Tab labels use verification counts",
              "document.querySelector('#verification-tab-claims')?.innerText.includes('Claims (5)') && document.querySelector('#verification-tab-evidence')?.innerText.includes('Evidence (15)')")

    select_result_tab('claims')
    assert_ok("Claims tab shows all five actual claims",
              "document.querySelector('[role=tabpanel]')?.textContent.includes('Isolated claim 5') && document.querySelector('[role=tabpanel]')?.textContent.includes('Browser-only synthetic assertion')")
    assert_ok("Claims tab hides overview",
              "!document.querySelector('[role=tabpanel]')?.textContent.includes('Original Answer Audited')")
    js("""const claim=[...document.querySelectorAll('p')].find(p=>p.textContent.includes('Browser-only synthetic assertion'));
       const row=claim?.closest('div.cursor-pointer'); if(row)row.click();return true;""")
    assert_ok("Missing claim-level confidence is disclosed",
              "document.querySelector('[role=tabpanel]')?.textContent.includes('Confidence unavailable')")
    assert_ok("Claim expands to show its own evidence",
              "document.querySelector('[role=tabpanel]')?.textContent.includes('Test evidence excerpt 1.1')")
    js("""document.querySelector('[role=tabpanel] [role=button][aria-expanded=true]').dispatchEvent(
          new KeyboardEvent('keydown',{key:'Enter',bubbles:true}));return true;""")
    assert_ok("Enter key collapses an expanded claim",
              "document.querySelector('[role=tabpanel] [role=button][aria-expanded=true]')===null")
    print("PASS claims panel uses actual claim records and keyboard interaction",flush=True)

    select_result_tab('evidence')
    assert_ok("Evidence tab contains all fifteen independent source entries",
              "document.querySelectorAll('[role=tabpanel] article').length===15")
    assert_ok("Evidence tab shows original evidence provenance",
              "document.querySelector('[role=tabpanel]')?.textContent.includes('Test evidence excerpt 5.3') && document.querySelector('[role=tabpanel] a')?.href.includes('example.org')")
    assert_ok("Evidence tab excludes claim breakdown and audit events",
              "!document.querySelector('[role=tabpanel]')?.textContent.includes('Claims Breakdown') && !document.querySelector('[role=tabpanel]')?.textContent.includes('Test audit recorded event')")
    print("PASS evidence panel lists every retrieved source",flush=True)

    select_result_tab('judgments')
    assert_ok("Judgments tab contains five real judge evaluations",
              "document.querySelectorAll('[role=tabpanel] article').length===5")
    assert_ok("Judgments tab renders backend judge names and rationales",
              "document.querySelector('[role=tabpanel]')?.textContent.includes('Test Judge 5') && document.querySelector('[role=tabpanel]')?.textContent.includes('Test judgment rationale 5')")
    assert_ok("Judgments tab hides individual evidence excerpts",
              "!document.querySelector('[role=tabpanel]')?.textContent.includes('Test evidence excerpt 5.3')")
    print("PASS judge evaluations mapped without fabricated results",flush=True)

    select_result_tab('audit')
    assert_ok("Audit tab renders all three backend lifecycle events",
              "document.querySelectorAll('[role=tabpanel] ol > li').length===3")
    assert_ok("Audit tab includes actual stage and message",
              "document.querySelector('[role=tabpanel]')?.textContent.includes('Test stage 3') && document.querySelector('[role=tabpanel]')?.textContent.includes('Test audit recorded event 3')")
    assert_ok("Audit tab does not present signed ledger claims",
              "document.querySelector('[role=tabpanel]')?.textContent.includes('not cryptographically signed')")
    print("PASS audit events shown without invented attestations",flush=True)

    # Keyboard navigation supports moving between tabs and updates panel.
    js("""document.getElementById('verification-tab-audit').dispatchEvent(
          new KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}));return true;""")
    assert_ok("ArrowRight keyboard moves Audit to Overview",
              "document.getElementById('verification-tab-overview')?.getAttribute('aria-selected')==='true'")
    print("PASS accessible keyboard tab navigation",flush=True)

    # Direct links without nested details must show honest empty states,
    # not invented sources, judges, or audit evidence.
    assert nav('/verification/22222222-2222-4222-8222-222222222222',
               "document.querySelector('#verification-tab-overview')!==null"), 'Empty-detail record not loaded'
    select_result_tab('evidence')
    assert_ok("Empty evidence shows explicit no-evidence state",
              "document.querySelector('[role=tabpanel]')?.textContent.includes('No retrieved evidence was returned')")
    select_result_tab('judgments')
    assert_ok("Empty judgments show explicit unavailable state",
              "document.querySelector('[role=tabpanel]')?.textContent.includes('No individual model judgments were returned')")
    select_result_tab('audit')
    assert_ok("Empty audit shows explicit no-event state",
              "document.querySelector('[role=tabpanel]')?.textContent.includes('No backend audit events are available')")
    print("PASS direct-link and empty-state verification tabs",flush=True)

    # The UI must also preserve input and surface failed verification requests.
    assert nav("/verify", "document.body.innerText.includes('Paste & Verify')"), "verify retry route missing"
    js("window.__phase4FailVerify=true;return true;")
    js("const btn=[...document.querySelectorAll('button')].find(b=>b.textContent.includes('Verify Answer'));btn.click();return true;")
    assert wait("document.querySelector('[role=alert]')?.innerText.includes('Isolated test: verification unavailable')"), "verification API error was hidden"
    assert_ok("failed verification stays on input screen", "location.pathname==='/verify'")
    print("PASS failed verification is visible without fabricated success", flush=True)

    # Reporting periods must reach the correct API parameter (1Y != 30D).
    js("sessionStorage.setItem('__phase4ReportsWithData','yes');return true;")
    assert nav('/reports', "document.body.innerText.includes('Reports & Insights')"), 'Reports page failed to load'
    assert wait("document.querySelector('.rpt-activity-chart') && document.querySelectorAll('.rpt-rank-item').length>=8",8), 'Analytics live chart and long model names did not render'
    assert_ok('reports header excludes the marked redundant leaderboard button',
              "![...document.querySelectorAll('.rpt-head button')].some(b=>b.textContent.includes('Leaderboard'))")
    assert_ok('activity axis uses six or fewer legible dates',
              "document.querySelectorAll('.rpt-activity-chart .recharts-xAxis .recharts-cartesian-axis-tick').length<=6")
    assert_ok('model usage rows preserve complete long names and count',
              "document.querySelector('.rpt-rank-panel')?.textContent.includes('anthropic/claude-sonnet-5.5-2026-10-21') && document.querySelectorAll('.rpt-rank-panel')[0].querySelectorAll('.rpt-rank-item').length===4")
    assert_ok('evidence sources use full labels not crammed X axis ticks',
              "[...document.querySelectorAll('.rpt-rank-panel')][1]?.textContent.includes('www.businessinsider.com') && document.querySelectorAll('.rpt-bottom-grid .recharts-xAxis').length===0")
    assert_ok('outcome ring reflects actual response percentages',
              "getComputedStyle(document.querySelector('.rpt-donut')).backgroundImage.includes('conic-gradient') && document.querySelector('.rpt-outcomes')?.textContent.includes('57.6%')")
    assert_ok('report metrics are source derived',
              "document.querySelector('.rpt-metrics')?.textContent.includes('120') && document.querySelector('.rpt-metrics')?.textContent.includes('66')")
    if os.getenv("VERIFAI_CAPTURE_REDESIGN") == "1":
        call(f"/session/{sid}/window/rect",{"width":1695,"height":900})
        assert wait("innerWidth>=1600",3),'Reports wide capture viewport failed'
        save_capture("reports-desktop.png")
        js("window.scrollTo(0, 680);return true;")
        save_capture("reports-details-desktop.png")
        js("window.scrollTo(0, 0);return true;")
        call(f"/session/{sid}/window/rect",{"width":390,"height":844})
        assert wait("innerWidth===390",3),'Reports mobile capture viewport failed'
        assert_ok('reports mobile has no page overflow',
                  "document.documentElement.scrollWidth<=innerWidth+2")
        save_capture("reports-mobile.png")
        js("window.scrollTo(0, 900);return true;")
        save_capture("reports-details-mobile.png")
        js("window.scrollTo(0, 0);return true;")
        call(f"/session/{sid}/window/rect",{"width":1440,"height":960})
        assert wait("innerWidth>=1400",3),'Reports desktop restore failed'
    js("""const button=[...document.querySelectorAll('.rpt-period button')].find(b=>b.textContent.trim()==='1 year');
          if(!button)throw new Error('Missing 1 year filter');button.click();return true;""")
    assert wait("window.__phase4Calls.some(r=>r.path.endsWith('/reports/analytics')&&r.query==='?timeframe=1Y')"), '1Y report did not fetch 1Y data'
    print('PASS analytics labeled dates, complete names, accurate ring, responsiveness and 1-year timeframe', flush=True)

    # Title-only knowledge entries must not be treated as indexed evidence.
    assert nav('/knowledge-base', "document.body.innerText.includes('Knowledge Base')"), 'Knowledge base did not load'
    assert_ok('Upload Document uses mint primary surface and black text, never burgundy',
              "(()=>{const b=[...document.querySelectorAll('button')].find(b=>b.textContent.includes('Upload Document')); const g=b?.closest('.border-glow-card'); return !!g && getComputedStyle(g).backgroundColor==='rgb(116, 198, 157)' && getComputedStyle(b).color==='rgb(0, 0, 0)' && g.style.getPropertyValue('--glow-color').includes('152deg')})()")
    print('PASS shared glow button uses forest/mint light-theme palette',flush=True)
    js("""const btn=[...document.querySelectorAll('button')].find(b=>b.textContent.includes('Upload Document'));
          if(!btn)throw new Error('No upload button');btn.click();return true;""")
    if not wait("document.querySelector('input[type=file]') != null"):
        raise AssertionError('Upload modal did not open')
    # Fill the required document title so HTML's native validation lets the
    # application handle the missing-file condition.
    js("""const input=document.querySelector('input[placeholder^="e.g. Clinical Trial"]');
          if (!input) throw new Error('Missing document title input');
          const setter=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
          setter.call(input,'Phase 4 empty-file validation');
          input.dispatchEvent(new Event('input',{bubbles:true}));
          return true;""")
    assert wait("document.querySelector('input[placeholder^=\"e.g. Clinical Trial\"]')?.value.length>0"), 'Cannot enter document title'
    js("""document.querySelector('input[type=file]').closest('form').requestSubmit();return true;""")
    assert wait("document.body.innerText.includes('Choose a file to upload')"), 'Title-only upload accepted'
    assert_ok('empty file upload does not produce fake indexed document',
              "!window.__phase4Calls.some(r=>r.path.endsWith('/knowledge/upload')&&r.method==='POST')")
    print('PASS empty knowledge upload prevented with visible error',flush=True)

    call(f'/session/{sid}/goog/cdp/execute',{'cmd':'Emulation.setDeviceMetricsOverride',
         'params':{'width':390,'height':844,'deviceScaleFactor':1,'mobile':True}})
    time.sleep(.4)
    assert_ok('narrow layout has no horizontal document overflow',
              'document.documentElement.scrollWidth<=innerWidth+2')
    print("PASS mobile 390px layout",flush=True)

    # Exercise the public landing/auth routes without injecting a real token.
    js("sessionStorage.setItem('__verifaiTestGuest','yes');return true;")
    assert nav('/login', "document.querySelector('#auth-password')!==null"), 'Login screen failed'
    assert_ok('reference-styled auth exposes username/email, password and Google',
              "document.querySelector('#auth-email[type=text]')!==null && "
              "document.querySelector('input[type=password]')!==null && "
              "document.querySelector('.auth-studio__google')!==null && "
              "document.querySelector('.auth-studio__photo')?.getAttribute('src')?.includes('auth-illustration')")
    assert_ok('generated illustration loads locally and mobile page does not scroll',
              "document.querySelector('.auth-studio__photo')?.naturalWidth>0 && "
              "document.documentElement.scrollHeight<=innerHeight+2 && "
              "document.documentElement.scrollWidth<=innerWidth+2")
    assert_ok('login artwork is above the live form on mobile',
              "document.querySelector('.auth-studio__visual').getBoundingClientRect().bottom<="
              "document.querySelector('.auth-studio__heading').getBoundingClientRect().top")
    assert_ok('account creation has a large accessible action',
              "document.querySelector('.auth-studio__account-action')?.textContent.includes('Create your free account') && "
              "document.querySelector('.auth-studio__account-action').getBoundingClientRect().height>=36")
    js("document.querySelector('.auth-studio__account-action').click();return true;")
    assert wait("location.pathname==='/signup'"), 'Prominent create account control did not navigate to signup'
    assert_ok('back link is visible on signup',
              "document.querySelector('.auth-studio__back-link')?.textContent.includes('Back to website') && "
              "document.querySelector('.auth-studio__back-link').getAttribute('href')==='/'")
    js("document.querySelector('.auth-studio__back-link').click();return true;")
    assert wait("location.pathname==='/'"), 'Back to website did not return to landing'
    print('PASS prominent account creation and landing-page return navigation',flush=True)
    assert nav('/signup', "document.querySelector('#auth-username')!==null"), 'Signup screen failed'
    assert_ok('signup collects username, email, password and consent',
              "document.querySelectorAll('.auth-studio__form input').length>=4 && "
              "document.querySelector('input[name=accept-policy]')!==null")
    assert_ok('signup form and Google action fit mobile viewport',
              "document.documentElement.scrollHeight<=innerHeight+2 && "
              "document.querySelector('.auth-studio__google').getBoundingClientRect().bottom<=innerHeight && "
              "document.querySelector('.auth-studio__heading').getBoundingClientRect().top>="
              "document.querySelector('.auth-studio__visual').getBoundingClientRect().bottom")
    js("document.querySelector('.auth-studio__submit').click();return true;")
    assert wait("document.querySelector('[role=alert]')?.textContent.includes('valid email')"), 'Email validation missing'
    js("const set=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;const e=document.getElementById('auth-username');set.call(e,'Reserved_Name');e.dispatchEvent(new Event('input',{bubbles:true}));return true;")
    assert wait("document.getElementById('auth-username-help')?.textContent.includes('already taken')"), 'Taken username missing'
    js("const set=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;const e=document.getElementById('auth-username');set.call(e,'Unique_Case');e.dispatchEvent(new Event('input',{bubbles:true}));return true;")
    assert wait("document.getElementById('auth-username-help')?.textContent.includes('is available')"), 'Available username missing'
    assert_ok('username is normalized for DB lookup',
              "window.__phase4Calls.some(x=>x.path.endsWith('/auth/username-availability')&&x.query.includes('unique_case'))")
    assert_ok('signup branding sits above the heading without overlap',
              "document.querySelector('.auth-studio__brand-block').getBoundingClientRect().bottom<="
              "document.querySelector('.auth-studio__heading').getBoundingClientRect().top && "
              "document.querySelector('.auth-studio__back-link').getAttribute('href')==='/'")
    assert_ok('signup has one Terms/Privacy entry point, not duplicate footer links',
              "document.querySelectorAll('.auth-studio__consent button').length===2 && "
              "!document.querySelector('.auth-studio__footer button')?.textContent.includes('Terms') && "
              "!document.querySelector('.auth-studio__footer button')?.textContent.includes('Privacy')")

    js("document.querySelector('.auth-studio__consent button').click();return true;")
    assert wait("document.querySelector('[role=dialog] #policy-modal-title')?.textContent.includes('Terms')"), 'Terms reader did not open'
    assert_ok('Terms reader has artwork and real policy sections',
              "document.querySelector('.legal-studio__illustration-panel img')?.getAttribute('src')==='/auth/verifai-trust-art.webp' && "
              "document.querySelectorAll('.legal-studio__article').length>=3 && "
              "document.querySelector('.legal-studio__draft-note')!==null")
    js("document.querySelector('[role=tab][aria-selected=false]').click();return true;")
    assert wait("document.querySelector('[role=dialog] #policy-modal-title')?.textContent.includes('Privacy')"), 'Privacy tab did not activate'
    assert_ok('Privacy tab renders the original privacy policy sections',
              "document.querySelectorAll('.legal-studio__article').length>=3 && "
              "document.querySelector('[role=tab][aria-selected=true]')?.textContent.includes('Privacy')")
    js("document.querySelector('.legal-studio__confirm').click();return true;")
    assert wait("!document.querySelector('[role=dialog]') && document.querySelector('input[name=accept-policy]')?.checked"), 'Policy consent not applied'
    print('PASS policy dialog, artwork, tabs, original sections and consent',flush=True)

    assert nav('/terms', "document.querySelector('.legal-studio__page-section')!==null"), 'Standalone Terms page failed'
    assert_ok('full Terms page includes image and review notice',
              "document.querySelector('.legal-studio__page-hero-art img')?.getAttribute('src')==='/auth/verifai-trust-art.webp' && "
              "document.querySelector('.legal-studio__draft-note')!==null")
    assert nav('/privacy', "document.querySelector('.legal-studio__page-section')!==null"), 'Standalone Privacy page failed'
    assert_ok('full Privacy page has version metadata and all policy sections',
              "document.querySelector('.legal-studio__page-hero-metadata')?.textContent.includes('Version') && "
              "document.querySelectorAll('.legal-studio__page-section').length>=3")
    print('PASS editorial full-page Terms and Privacy documents',flush=True)

    print('PASS editorial login/signup fields and email validation',flush=True)
    assert nav('/', "document.querySelector('.verifai-landing h1')!=null"), 'Marketing landing page failed'
    assert_ok('guest landing contains a real login action',
              "document.querySelector('.vc-nav-login')?.getAttribute('href')==='/login'")
    assert_ok('guest launch goes to login',
              "[...document.querySelectorAll('a.vc-action-light')].some(a=>a.getAttribute('href')==='/login')")
    print('PASS public landing routes to login',flush=True)

    # The route guard must preserve the original path for post-Google-login
    # return navigation rather than always sending users to /dashboard.
    assert nav('/chat', "location.pathname==='/login'"), 'Guest chat route did not redirect to login'
    assert_ok('guest redirect preserves requested chat location',
              "history.state?.usr?.from==='/chat'")
    print('PASS unauthenticated chat deep link records post-login destination',flush=True)

    # Isolated signup with fake endpoints; no real user is registered.
    assert nav('/signup', "document.querySelector('#auth-username')!==null"), 'Signup page unavailable'
    js("const set=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;for(const [id,v] of [['auth-username','Unique_Case'],['auth-email','browser-auth@example.invalid'],['auth-password','ValidPassword2026!']]){const el=document.getElementById(id);set.call(el,v);el.dispatchEvent(new Event('input',{bubbles:true}));}document.querySelector('input[name=accept-policy]').click();return true;")
    assert wait("document.getElementById('auth-username-help')?.textContent.includes('is available')"), 'Signup username validation unresolved'
    js("document.querySelector('.auth-studio__submit').click();return true;")
    assert wait("window.__phase4CreatedAccount?.username==='unique_case'"), 'Normalized registration not submitted'
    assert wait("window.__phase4PasswordLogin?.email_or_username==='browser-auth@example.invalid'"), 'Backend login not requested'
    assert wait("location.pathname==='/dashboard'"), 'Signup did not redirect to dashboard'
    print('PASS local signup, normalized username, login, and dashboard redirect',flush=True)

    print("ALL PHASE 4 BROWSER INTEGRATION CHECKS PASSED", flush=True)
except Exception as error:
    test_failure = True
    print("BROWSER TEST FAILED:", repr(error)[:1800], file=sys.stderr, flush=True)
finally:
    if sid:
        try:
            call(f"/session/{sid}", method="DELETE")
        except Exception:
            pass
    for owned in (proc, preview):
        if owned:
            owned.terminate()
            try:
                owned.wait(timeout=3)
            except subprocess.TimeoutExpired:
                owned.kill()
                owned.wait()
    profile_dir.cleanup()

if test_failure:
    sys.exit(1)

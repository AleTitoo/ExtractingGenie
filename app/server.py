"""Local-only browser interface; no remote services."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import base64, ctypes, json, os, re, secrets, sys, tempfile, threading, time, webbrowser
import subprocess
from urllib.parse import parse_qs, urlparse
from core import import_report, load_library, export_csv, upgrade_library
from lab_export import export_lab_csv
from excel_export import export_xlsx
from evidence import render_png
from update import check_for_update, download_verified_update, schedule_install
from version import APP_VERSION
ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
ASSET_ROOT = ROOT / 'assets' if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1] / 'assets'
if getattr(sys, 'frozen', False):
    default_data = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'Platinum-189'
else:
    default_data = Path(__file__).resolve().parent
OFFLINE_EDITION = (ROOT / 'offline-edition.json').exists()
if OFFLINE_EDITION:
    default_data = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'Platinum-189 Offline'
DATA_ROOT = Path(os.environ.get('GENIE_DATA_DIR', default_data))
LIBRARY = DATA_ROOT / 'library'
LIBRARY.mkdir(parents=True, exist_ok=True)
LIBRARY_UPGRADE_ERRORS = upgrade_library(LIBRARY)
TOKEN = secrets.token_urlsafe(32)
LOCK = threading.Lock()
UPDATE_LOCK = threading.Lock()
UPDATE_STATE = {'stage':'idle','percent':0,'version':'','message':'','installer':None}

def update_state(**changes):
    with UPDATE_LOCK:
        UPDATE_STATE.update(changes)
        return {key:value for key,value in UPDATE_STATE.items() if key != 'installer'}

def public_update_state():
    result = DATA_ROOT / 'update-install-result.json'
    if result.exists():
        try:
            outcome = json.loads(result.read_text(encoding='utf-8-sig'))
            if outcome.get('error'): update_state(stage='error', message=outcome['error'])
            result.unlink(missing_ok=True)
        except (OSError, ValueError): pass
    with UPDATE_LOCK:
        return {key:value for key,value in UPDATE_STATE.items() if key != 'installer'}

def download_update(info):
    try:
        update_state(stage='downloading', percent=0, version=info['latest_version'], message='Downloading update…', installer=None)
        def progress(value): update_state(percent=round(value * 100, 1))
        installer = download_verified_update(info, DATA_ROOT/'updates', progress=progress)
        update_state(stage='ready', percent=100, message='Update downloaded and verified.', installer=str(installer))
    except Exception as exc:
        update_state(stage='error', message=str(exc), installer=None)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def send(self, data, kind='application/json', status=200):
        if isinstance(data,(dict,list)): data=json.dumps(data)
        if isinstance(data,str): data=data.encode('utf-8')
        self.send_response(status)
        for k,v in [('Content-Type',kind),('Content-Length',str(len(data))),('Cache-Control','no-store'),('X-Content-Type-Options','nosniff'),('X-Frame-Options','DENY')]: self.send_header(k,v)
        self.end_headers()
        self.wfile.write(data)
    def valid_host(self):
        return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'
    def do_GET(self):
        if not self.valid_host(): return self.send({'error':'Invalid host'},status=403)
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        request_token = query.get('token', [''])[0]
        if parsed.path == '/': return self.send((ROOT/'interface.html').read_text(encoding='utf-8').replace('__TOKEN__',TOKEN).replace('__OFFLINE__',str(OFFLINE_EDITION).lower()),'text/html; charset=utf-8')
        if parsed.path == '/assets/platinum-189.png':
            return self.send((ASSET_ROOT/'platinum-189.png').read_bytes(),'image/png')
        if parsed.path == '/assets/platinum-189-animated.js':
            return self.send((ASSET_ROOT/'platinum-189-animated.js').read_bytes(),'application/javascript; charset=utf-8')
        match=re.fullmatch(r'/pdf/([a-f0-9]{64})',parsed.path)
        if match and secrets.compare_digest(request_token,TOKEN):
            path=LIBRARY/(match[1]+'.pdf')
            if path.exists(): return self.send(path.read_bytes(),'application/pdf')
        match=re.fullmatch(r'/evidence/([a-f0-9]{64})/(summary|line)/(\d+)\.png',parsed.path)
        if match and secrets.compare_digest(request_token,TOKEN):
            digest, kind, index = match.groups()
            record=LIBRARY/(digest+'.json')
            pdf=LIBRARY/(digest+'.pdf')
            if record.exists() and pdf.exists():
                report=json.loads(record.read_text(encoding='utf-8'))
                values=report['rows'] if kind=='summary' else report.get('line_rows',[])
                if int(index)<len(values):
                    row=values[int(index)]
                    return self.send(render_png(pdf,row['page'],row.get('bbox')),'image/png')
        self.send({'error':'Not found'},status=404)
    def do_POST(self):
        if not self.valid_host() or not secrets.compare_digest(self.headers.get('X-Library-Token',''),TOKEN): return self.send({'error':'Invalid token'},status=403)
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=70*1024*1024: return self.send({'error':'Request too large'},status=413)
            data=json.loads(self.rfile.read(size))
            with LOCK:
                if self.path=='/api/list': return self.send(load_library(LIBRARY))
                if self.path=='/api/info': return self.send({'version':APP_VERSION,'offline':OFFLINE_EDITION,'library_upgrade_errors':LIBRARY_UPGRADE_ERRORS})
                if OFFLINE_EDITION and self.path.startswith('/api/update/'):
                    return self.send({'error':'Offline / Lab Edition: install updates manually.'},status=403)
                if self.path=='/api/update/check':
                    info=check_for_update()
                    if info['available'] and public_update_state()['stage'] in ('idle','error'):
                        update_state(stage='available',version=info['latest_version'],message=f"Version {info['latest_version']} is available.")
                    return self.send({**info,'update':public_update_state()})
                if self.path=='/api/update/status': return self.send(public_update_state())
                if self.path=='/api/update/download':
                    state=public_update_state()
                    if state['stage'] not in ('downloading','ready'):
                        info=check_for_update()
                        if not info['available']: raise ValueError('No update is available.')
                        threading.Thread(target=download_update,args=(info,),daemon=True).start()
                    return self.send(public_update_state())
                if self.path=='/api/update/install':
                    with UPDATE_LOCK: installer=UPDATE_STATE.get('installer')
                    if not installer: raise ValueError('Download and verify the update first.')
                    schedule_install(installer)
                    update_state(stage='installing',message='Preparing to restart and install...')
                    return self.send(public_update_state())
                if self.path=='/api/import':
                    name=str(data['name']).replace('\\','/').split('/')[-1]
                    if not name.lower().endswith('.pdf'): raise ValueError('Select a PDF report.')
                    raw=base64.b64decode(data['data'],validate=True)
                    with tempfile.TemporaryDirectory() as temp:
                        path=Path(temp)/name
                        path.write_bytes(raw)
                        report,new=import_report(path,LIBRARY)
                    return self.send({'report':report,'added':new})
                if self.path in ('/api/export','/api/export-lab','/api/export-excel'):
                    reports=[r for r in load_library(LIBRARY) if r['sha256'] in set(data['ids'])]
                    if not reports: raise ValueError('Select at least one report.')
                    with tempfile.TemporaryDirectory() as temp:
                        if self.path=='/api/export-excel':
                            target=Path(temp)/'results.xlsx'
                            export_xlsx(reports,target,str(data['threshold']),bool(data['all']),str(data.get('uncertainty_threshold','10')))
                            return self.send(target.read_bytes(),'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                        target=Path(temp)/'results.csv'
                        if self.path=='/api/export-lab':
                            export_lab_csv(reports,target,str(data['threshold']),bool(data['all']),str(data.get('uncertainty_threshold','10')))
                        else:
                            export_csv(reports,target,LIBRARY,str(data['threshold']),bool(data['all']),str(data.get('uncertainty_threshold','10')))
                        return self.send(target.read_bytes(),'text/csv; charset=utf-8')
                return self.send({'error':'Not found'},status=404)
        except Exception as exc: self.send({'error':str(exc)},status=400)

def make_server(): return ThreadingHTTPServer(('127.0.0.1',0),Handler)

def edge_path():
    candidates = [
        Path(os.environ.get('PROGRAMFILES(X86)', '')) / 'Microsoft/Edge/Application/msedge.exe',
        Path(os.environ.get('PROGRAMFILES', '')) / 'Microsoft/Edge/Application/msedge.exe',
        Path(os.environ.get('LOCALAPPDATA', '')) / 'Microsoft/Edge/Application/msedge.exe',
    ]
    return next((path for path in candidates if path.is_file()), None)

def run_desktop(server, url):
    if os.name == 'nt':
        try: ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('AleTitoo.Platinum189')
        except Exception: pass
    edge = edge_path()
    if not edge:
        webbrowser.open(url)
        server.serve_forever()
        return
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    profile = DATA_ROOT / 'browser-profile'
    profile.mkdir(parents=True, exist_ok=True)
    process = subprocess.Popen([
        str(edge), f'--app={url}', f'--user-data-dir={profile}',
        '--no-first-run', '--disable-background-mode'
    ])
    process.wait()
    server.shutdown()
    thread.join(timeout=5)

if __name__=='__main__':
    server=make_server()
    url=f'http://127.0.0.1:{server.server_port}'
    port_file = os.environ.get('GENIE_PORT_FILE')
    if port_file:
        Path(port_file).write_text(url, encoding='utf-8')
    if sys.stdout:
        print(url, flush=True)
    if os.environ.get('GENIE_EMBEDDED') != '1':
        if sys.stdout:
            print('Platinum-189\nKeep this window open. Close it or press Ctrl+C to stop.', flush=True)
    try:
        if os.environ.get('GENIE_EMBEDDED') == '1':
            server.serve_forever()
        else:
            run_desktop(server, url)
    except KeyboardInterrupt: pass
    finally: server.server_close()

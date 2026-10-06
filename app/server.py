"""Local-only browser interface; no remote services."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import base64, json, os, re, secrets, sys, tempfile, threading, time, webbrowser
import subprocess
from urllib.parse import parse_qs, urlparse
from core import import_report, load_library, export_csv, upgrade_library
from lab_export import export_lab_csv
from evidence import render_png
from update import check_for_update, download_verified_update, schedule_install
from version import APP_VERSION
ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
if getattr(sys, 'frozen', False):
    default_data = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'GENIE Report Studio'
else:
    default_data = Path(__file__).resolve().parent
DATA_ROOT = Path(os.environ.get('GENIE_DATA_DIR', default_data))
LIBRARY = DATA_ROOT / 'library'
LIBRARY.mkdir(parents=True, exist_ok=True)
LIBRARY_UPGRADE_ERRORS = upgrade_library(LIBRARY)
TOKEN = secrets.token_urlsafe(32)
LOCK = threading.Lock()

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
        if parsed.path == '/': return self.send((ROOT/'interface.html').read_text(encoding='utf-8').replace('__TOKEN__',TOKEN),'text/html; charset=utf-8')
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
                if self.path=='/api/info': return self.send({'version':APP_VERSION,'library_upgrade_errors':LIBRARY_UPGRADE_ERRORS})
                if self.path=='/api/update/check': return self.send(check_for_update())
                if self.path=='/api/update/install':
                    info=check_for_update()
                    installer=download_verified_update(info,DATA_ROOT/'updates')
                    schedule_install(installer)
                    threading.Thread(target=lambda:(time.sleep(1.5),os._exit(0)),daemon=True).start()
                    return self.send({'status':'Installing verified update…'})
                if self.path=='/api/import':
                    name=str(data['name']).replace('\\','/').split('/')[-1]
                    if not name.lower().endswith('.pdf'): raise ValueError('Select a PDF report.')
                    raw=base64.b64decode(data['data'],validate=True)
                    with tempfile.TemporaryDirectory() as temp:
                        path=Path(temp)/name
                        path.write_bytes(raw)
                        report,new=import_report(path,LIBRARY)
                    return self.send({'report':report,'added':new})
                if self.path in ('/api/export','/api/export-lab'):
                    reports=[r for r in load_library(LIBRARY) if r['sha256'] in set(data['ids'])]
                    if not reports: raise ValueError('Select at least one report.')
                    with tempfile.TemporaryDirectory() as temp:
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
            print('GENIE Report Studio\nKeep this window open. Close it or press Ctrl+C to stop.', flush=True)
    try:
        if os.environ.get('GENIE_EMBEDDED') == '1':
            server.serve_forever()
        else:
            run_desktop(server, url)
    except KeyboardInterrupt: pass
    finally: server.server_close()

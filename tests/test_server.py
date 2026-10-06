import unittest, threading, json, urllib.request, urllib.error, tempfile
from pathlib import Path
import server

class ServerTests(unittest.TestCase):
    def test_library_export_and_auth(self):
        service=server.make_server()
        thread=threading.Thread(target=service.serve_forever,daemon=True)
        thread.start()
        url=f'http://127.0.0.1:{service.server_port}'
        try:
            with urllib.request.urlopen(url) as response:
                self.assertIn(b'GENIE Report Library',response.read())
            def request(path,data,token=server.TOKEN):
                return urllib.request.urlopen(urllib.request.Request(url+path,
                    data=json.dumps(data).encode(),headers={'X-Library-Token':token,'Content-Type':'application/json'}))
            with request('/api/list',{}) as response:
                reports=json.load(response)
            if reports:
                with request('/api/export',{'ids':[r['sha256'] for r in reports],'threshold':'0.7','all':False}) as response:
                    self.assertIn(b'Weighted mean activity',response.read())
                with request('/api/export-lab',{'ids':[r['sha256'] for r in reports],'threshold':'0.7','all':False}) as response:
                    self.assertIn(b'Foil no.',response.read())
            with self.assertRaises(urllib.error.HTTPError) as context:
                request('/api/list',{},'wrong')
            self.assertEqual(context.exception.code,403)
        finally:
            service.shutdown()
            service.server_close()

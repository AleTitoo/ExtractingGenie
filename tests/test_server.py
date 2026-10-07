import unittest, threading, json, urllib.request, urllib.error, tempfile
from pathlib import Path
import server
from unittest.mock import patch

class ServerTests(unittest.TestCase):
    def test_library_export_and_auth(self):
        service=server.make_server()
        thread=threading.Thread(target=service.serve_forever,daemon=True)
        thread.start()
        url=f'http://127.0.0.1:{service.server_port}'
        try:
            with urllib.request.urlopen(url) as response:
                self.assertIn(b'Platinum-189',response.read())
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

    def test_update_install_waits_for_native_handoff_without_exiting_backend(self):
        service=server.make_server()
        threading.Thread(target=service.serve_forever,daemon=True).start()
        url=f'http://127.0.0.1:{service.server_port}'
        previous=server.UPDATE_STATE.copy()
        def request(path):
            return urllib.request.urlopen(urllib.request.Request(url+path,data=b'{}',
                headers={'X-Library-Token':server.TOKEN,'Content-Type':'application/json'}),timeout=5)
        try:
            server.update_state(stage='ready',installer='verified.exe')
            with patch.object(server,'schedule_install') as handoff:
                with request('/api/update/install') as response:
                    self.assertEqual(json.load(response)['stage'],'installing')
                handoff.assert_called_once_with('verified.exe')
            # The native shell owns shutdown; the report service still responds.
            with request('/api/info') as response:
                self.assertIn('version',json.load(response))
            with patch.object(server,'schedule_install',side_effect=ValueError('checksum changed')):
                with self.assertRaises(urllib.error.HTTPError) as failure:
                    request('/api/update/install')
                self.assertEqual(failure.exception.code,400)
        finally:
            server.UPDATE_STATE.clear()
            server.UPDATE_STATE.update(previous)
            service.shutdown()
            service.server_close()

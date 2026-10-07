import json, threading, unittest, urllib.request, urllib.error
from unittest.mock import patch
import server

class OfflineTests(unittest.TestCase):
    def test_offline_endpoints_never_check_download_or_install(self):
        service = server.make_server()
        threading.Thread(target=service.serve_forever, daemon=True).start()
        origin = f'http://127.0.0.1:{service.server_port}'
        try:
            with patch.object(server, 'OFFLINE_EDITION', True), patch.object(server, 'check_for_update') as check, patch.object(server, 'download_verified_update') as download, patch.object(server, 'schedule_install') as install:
                for route in ['check', 'download', 'install', 'status']:
                    request = urllib.request.Request(origin + '/api/update/' + route, data=b'{}', headers={'X-Library-Token': server.TOKEN})
                    with self.assertRaises(urllib.error.HTTPError) as error:
                        urllib.request.urlopen(request)
                    self.assertEqual(error.exception.code, 403)
                check.assert_not_called(); download.assert_not_called(); install.assert_not_called()
                with urllib.request.urlopen(origin) as response:
                    self.assertIn(b'const offline=true;', response.read())
                request = urllib.request.Request(origin + '/api/info', data=b'{}', headers={'X-Library-Token': server.TOKEN})
                with urllib.request.urlopen(request) as response:
                    self.assertTrue(json.load(response)['offline'])
        finally:
            service.shutdown(); service.server_close()

    def test_lab_installer_has_no_legacy_or_standard_targets(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        script = (root / 'installer-offline.nsi').read_text()
        self.assertNotIn('GENIE', script)
        self.assertIn('InstallDir "$LOCALAPPDATA\\Programs\\Platinum-189 Offline"', script)
        self.assertNotIn('migrateLibrary', script)
        self.assertIn('dist-offline\\win-unpacked', script)

import io
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import update

class Response(io.BytesIO):
    headers = {}
    def __enter__(self): return self
    def __exit__(self,*args): self.close()

class UpdateTests(unittest.TestCase):
    def test_native_update_hands_off_only_verified_installer(self):
        import hashlib
        with tempfile.TemporaryDirectory() as temp:
            installer = Path(temp) / 'updates' / 'Platinum-189-Setup-9.0.0.exe'
            installer.parent.mkdir()
            installer.write_bytes(b'installer')
            checksum = hashlib.sha256(b'installer').hexdigest()
            Path(str(installer) + '.sha256').write_text(checksum)
            with patch.object(update.sys, 'frozen', True, create=True), patch.object(update.os, 'name', 'nt'), patch.dict(update.os.environ, {'GENIE_DATA_DIR':temp,'GENIE_DESKTOP_PID':'1234'}), patch.object(update.subprocess, 'Popen') as launch:
                update.schedule_install(installer)
                launch.assert_not_called()
                request = json.loads((Path(temp) / 'update-install-request.json').read_text())
                self.assertEqual(request['desktop_pid'], 1234)
                self.assertEqual(request['sha256'], checksum)
                self.assertFalse((Path(temp) / 'update-install-request.tmp').exists())
                installer.write_bytes(b'tampered')
                with self.assertRaisesRegex(ValueError, 'changed after download'):
                    update.schedule_install(installer)

    def test_version_tuple(self):
        self.assertEqual(update.version_tuple('v1.2.3'),(1,2,3))
        with self.assertRaises(ValueError): update.version_tuple('latest')

    def test_check_requires_installer_and_checksum(self):
        release={'tag_name':'v9.0.0','html_url':'https://example/release','assets':[
            {'name':'Platinum-189-Setup-9.0.0.exe','browser_download_url':'https://example/app'},
            {'name':'Platinum-189-Setup-9.0.0.exe.sha256','browser_download_url':'https://example/hash'}]}
        info=update.check_for_update(lambda request,timeout=0:Response(json.dumps(release).encode()))
        self.assertTrue(info['available'])
        release['assets'].pop()
        info=update.check_for_update(lambda request,timeout=0:Response(json.dumps(release).encode()))
        self.assertFalse(info['available'])

    def test_check_uses_asset_matching_release_version(self):
        release={'tag_name':'v9.0.0','assets':[
            {'name':'Platinum-189-Setup-8.0.0.exe','browser_download_url':'https://example/wrong'},
            {'name':'Platinum-189-Setup-9.0.0.exe','browser_download_url':'https://example/right'},
            {'name':'Platinum-189-Setup-9.0.0.exe.sha256','browser_download_url':'https://example/hash'}]}
        info=update.check_for_update(lambda request,timeout=0:Response(json.dumps(release).encode()))
        self.assertEqual(info['installer_url'],'https://example/right')

    def test_verified_download_reports_completion(self):
        payload=b'installer'
        import hashlib
        checksum=hashlib.sha256(payload).hexdigest().encode()
        info={'available':True,'installer_name':'setup.exe','installer_url':'https://example/app','checksum_url':'https://example/hash'}
        progress=[]
        def opener(request,timeout=0): return Response(checksum if request.full_url.endswith('hash') else payload)
        with tempfile.TemporaryDirectory() as temp:
            update.download_verified_update(info,temp,opener,progress.append)
        self.assertEqual(progress[-1],1.0)

    def test_verified_download_rejects_bad_hash(self):
        info={'available':True,'installer_name':'setup.exe','installer_url':'https://example/app','checksum_url':'https://example/hash'}
        def opener(request,timeout=0):
            return Response(b'bad-hash' if request.full_url.endswith('hash') else b'installer')
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError): update.download_verified_update(info,temp,opener)
            self.assertFalse((Path(temp)/'setup.exe').exists())

if __name__=='__main__': unittest.main()

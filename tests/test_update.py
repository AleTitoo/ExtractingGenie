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
    def test_native_update_waits_for_shell_and_relaunches_visible_executable(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(update.sys, 'frozen', True, create=True), patch.object(update.os, 'name', 'nt'), patch.object(update.tempfile, 'gettempdir', return_value=temp), patch.dict(update.os.environ, {'GENIE_DESKTOP_EXE':'C:/GENIE/Platinum-189.exe','GENIE_DESKTOP_PID':'1234'}), patch.object(update.subprocess, 'Popen') as launch:
                update.schedule_install('C:/updates/setup.exe')
                arguments = launch.call_args.args[0]
                self.assertEqual(arguments[arguments.index('-DesktopProcessId') + 1], '1234')
                self.assertEqual(arguments[arguments.index('-App') + 1], 'C:\\GENIE\\Platinum-189.exe')
                script = (Path(temp) / 'platinum-189-update.ps1').read_text(encoding='utf-8')
                self.assertLess(script.index('Wait-Process -Id $DesktopProcessId'), script.index('$result = Start-Process'))
                self.assertIn('if ($result.ExitCode -eq 0)', script)

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

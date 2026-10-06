import io
import json
import tempfile
import unittest
from pathlib import Path

import update

class Response(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self,*args): self.close()

class UpdateTests(unittest.TestCase):
    def test_version_tuple(self):
        self.assertEqual(update.version_tuple('v1.2.3'),(1,2,3))
        with self.assertRaises(ValueError): update.version_tuple('latest')

    def test_check_requires_installer_and_checksum(self):
        release={'tag_name':'v9.0.0','html_url':'https://example/release','assets':[
            {'name':'GENIE-Report-Studio-Setup-9.0.0.exe','browser_download_url':'https://example/app'},
            {'name':'GENIE-Report-Studio-Setup-9.0.0.exe.sha256','browser_download_url':'https://example/hash'}]}
        info=update.check_for_update(lambda request,timeout=0:Response(json.dumps(release).encode()))
        self.assertTrue(info['available'])
        release['assets'].pop()
        info=update.check_for_update(lambda request,timeout=0:Response(json.dumps(release).encode()))
        self.assertFalse(info['available'])

    def test_verified_download_rejects_bad_hash(self):
        info={'available':True,'installer_name':'setup.exe','installer_url':'https://example/app','checksum_url':'https://example/hash'}
        def opener(request,timeout=0):
            return Response(b'bad-hash' if request.full_url.endswith('hash') else b'installer')
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError): update.download_verified_update(info,temp,opener)
            self.assertFalse((Path(temp)/'setup.exe').exists())

if __name__=='__main__': unittest.main()

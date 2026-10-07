from pathlib import Path
import re
import json
import unittest

from version import APP_VERSION


class VersionTests(unittest.TestCase):
    def test_release_version_is_synchronized(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(APP_VERSION, (root / 'version.txt').read_text(encoding='utf-8').strip())
        site = (root / 'site' / 'index.html').read_text(encoding='utf-8')
        self.assertRegex(site, rf'Version {re.escape(APP_VERSION)} ·')
        package = json.loads((root / 'package.json').read_text(encoding='utf-8'))
        self.assertEqual(package['version'], APP_VERSION)


if __name__ == '__main__': unittest.main()

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import legacy_launcher

class LauncherTests(unittest.TestCase):
    def test_sharing_violation_is_retried(self):
        error = PermissionError('File is in use')
        error.winerror = 32
        waits = []
        with patch.object(legacy_launcher.subprocess, 'Popen', side_effect=[error, error, 'started']) as spawn:
            self.assertEqual(legacy_launcher.launch('Platinum-189.exe', waits.append), 'started')
            self.assertEqual(spawn.call_count, 3)
        self.assertEqual(waits, [0.5, 0.5])

    def test_installer_marker_delays_launch_until_all_files_are_ready(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'Platinum-189.exe'
            marker = target.parent / '.installing'
            marker.write_text('busy')
            def finish_install(_): marker.unlink()
            with patch.object(legacy_launcher.subprocess, 'Popen', return_value='started') as spawn:
                self.assertEqual(legacy_launcher.launch(target, finish_install), 'started')
                spawn.assert_called_once()

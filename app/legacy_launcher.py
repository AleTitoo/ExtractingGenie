"""Compatibility bridge for existing updater relaunch paths and Windows pins."""
from pathlib import Path
import os
import subprocess
import time

def launch(target, wait=time.sleep, attempts=120):
    target = Path(target)
    environment = {key: value for key, value in os.environ.items() if not key.startswith('GENIE_')}
    for attempt in range(attempts):
        if not (target.parent / '.installing').exists():
            try:
                return subprocess.Popen([str(target)], close_fds=True, env=environment)
            except OSError as exc:
                if getattr(exc, 'winerror', None) not in (2, 5, 32, 33): raise
        wait(0.5)
    raise RuntimeError('The installation is still in progress.')

if __name__ == '__main__':
    target = Path(os.environ['LOCALAPPDATA']) / 'Programs' / 'Platinum-189' / 'Platinum-189.exe'
    try:
        launch(target)
    except Exception:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, 'Platinum-189 could not open while its files were being updated. Wait a moment, then open Platinum-189 from Start.', 'Platinum-189', 0x10)

"""Compatibility bridge for existing updater relaunch paths and Windows pins."""
from pathlib import Path
import os
import subprocess

target = Path(os.environ['LOCALAPPDATA']) / 'Programs' / 'Platinum-189' / 'Platinum-189.exe'
environment = {key: value for key, value in os.environ.items() if not key.startswith('GENIE_')}
subprocess.Popen([str(target)], close_fds=True, env=environment)

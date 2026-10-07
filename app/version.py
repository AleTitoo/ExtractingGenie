from pathlib import Path
import sys

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
APP_VERSION = (ROOT / 'version.txt').read_text(encoding='utf-8').strip()
GITHUB_REPOSITORY = 'AleTitoo/ExtractingGenie'
INSTALLER_NAME = f'Platinum-189-Setup-{APP_VERSION}.exe'

"""GitHub release updater with SHA-256 integrity verification."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request

from version import APP_VERSION, GITHUB_REPOSITORY

API = f'https://api.github.com/repos/{GITHUB_REPOSITORY}/releases/latest'
USER_AGENT = 'Platinum-189-Updater'

def version_tuple(value):
    match = re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)', str(value).strip())
    if not match:
        raise ValueError(f'Unsupported release version: {value}')
    return tuple(map(int, match.groups()))

def _request(url):
    return urllib.request.Request(url, headers={'User-Agent': USER_AGENT,
                                                'Accept': 'application/vnd.github+json'})

def check_for_update(opener=urllib.request.urlopen):
    with opener(_request(API), timeout=12) as response:
        release = json.load(response)
    tag = release.get('tag_name', '')
    assets = {asset.get('name'): asset for asset in release.get('assets', [])}
    latest = tag.lstrip('v')
    expected_name = f'Platinum-189-Setup-{latest}.exe'
    installer = assets.get(expected_name)
    checksum = assets.get((installer or {}).get('name', '') + '.sha256')
    return {
        'current_version': APP_VERSION,
        'latest_version': tag.lstrip('v'),
        'available': bool(installer and checksum and version_tuple(tag) > version_tuple(APP_VERSION)),
        'release_url': release.get('html_url', ''),
        'installer_name': (installer or {}).get('name', ''),
        'installer_url': (installer or {}).get('browser_download_url', ''),
        'checksum_url': (checksum or {}).get('browser_download_url', ''),
    }

def _download(url, target, opener=urllib.request.urlopen, progress=None, start=0.0, end=1.0):
    with opener(_request(url), timeout=120) as response, open(target, 'wb') as stream:
        total = int(response.headers.get('Content-Length', '0')) if getattr(response, 'headers', None) else 0
        received = 0
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            stream.write(block)
            received += len(block)
            if progress and total:
                progress(start + (end - start) * min(received / total, 1.0))
    if progress:
        progress(end)

def download_verified_update(info, update_dir, opener=urllib.request.urlopen, progress=None):
    if not info.get('available'):
        raise ValueError('No verified update is available.')
    update_dir = Path(update_dir)
    update_dir.mkdir(parents=True, exist_ok=True)
    installer = update_dir / info['installer_name']
    checksum_file = update_dir / (info['installer_name'] + '.sha256')
    _download(info['installer_url'], installer, opener, progress, 0.0, 0.96)
    _download(info['checksum_url'], checksum_file, opener, progress, 0.96, 0.99)
    expected = checksum_file.read_text(encoding='utf-8').strip().split()[0].lower()
    actual = hashlib.sha256(installer.read_bytes()).hexdigest()
    if not re.fullmatch(r'[a-f0-9]{64}', expected) or actual != expected:
        installer.unlink(missing_ok=True)
        checksum_file.unlink(missing_ok=True)
        raise ValueError('Downloaded installer failed SHA-256 verification.')
    if progress:
        progress(1.0)
    return installer

def schedule_install(installer, app_path=None):
    """Ask the native shell to install; never spawn from the private report service."""
    if os.name != 'nt' or not getattr(sys, 'frozen', False):
        raise RuntimeError('Automatic installation is available only in the installed Windows app.')
    desktop_pid = int(os.environ.get('GENIE_DESKTOP_PID', '0'))
    if desktop_pid <= 0:
        raise RuntimeError('Open Platinum-189 from its desktop shortcut to install an update.')
    root = Path(os.environ['GENIE_DATA_DIR']).resolve()
    installer = Path(installer).resolve()
    if installer.parent != root / 'updates' or not re.fullmatch(r'Platinum-189-Setup-\d+\.\d+\.\d+\.exe', installer.name):
        raise ValueError('Invalid update installer path.')
    checksum = Path(str(installer) + '.sha256').read_text(encoding='utf-8').strip().split()[0].lower()
    actual = hashlib.sha256(installer.read_bytes()).hexdigest()
    if not re.fullmatch(r'[a-f0-9]{64}', checksum) or actual != checksum:
        raise ValueError('Installer changed after download. Download the update again.')
    (root / 'update-install-result.json').unlink(missing_ok=True)
    request = root / 'update-install-request.json'
    temporary = request.with_suffix('.tmp')
    temporary.write_text(json.dumps({'installer': str(installer), 'sha256': checksum,
                                    'desktop_pid': desktop_pid}), encoding='utf-8')
    temporary.replace(request)

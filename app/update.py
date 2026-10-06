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

from version import APP_VERSION, GITHUB_REPOSITORY, INSTALLER_NAME

API = f'https://api.github.com/repos/{GITHUB_REPOSITORY}/releases/latest'
USER_AGENT = 'GENIE-Report-Studio-Updater'

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
    installer = next((asset for name, asset in assets.items()
                      if name and name.startswith('GENIE-Report-Studio-Setup-') and name.endswith('.exe')), None)
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

def _download(url, target, opener=urllib.request.urlopen):
    with opener(_request(url), timeout=120) as response, open(target, 'wb') as stream:
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            stream.write(block)

def download_verified_update(info, update_dir, opener=urllib.request.urlopen):
    if not info.get('available'):
        raise ValueError('No verified update is available.')
    update_dir = Path(update_dir)
    update_dir.mkdir(parents=True, exist_ok=True)
    installer = update_dir / info['installer_name']
    checksum_file = update_dir / (info['installer_name'] + '.sha256')
    _download(info['installer_url'], installer, opener)
    _download(info['checksum_url'], checksum_file, opener)
    expected = checksum_file.read_text(encoding='utf-8').strip().split()[0].lower()
    actual = hashlib.sha256(installer.read_bytes()).hexdigest()
    if not re.fullmatch(r'[a-f0-9]{64}', expected) or actual != expected:
        installer.unlink(missing_ok=True)
        raise ValueError('Downloaded installer failed SHA-256 verification.')
    return installer

def schedule_install(installer):
    if os.name != 'nt' or not getattr(sys, 'frozen', False):
        raise RuntimeError('Automatic installation is available only in the installed Windows app.')
    script = Path(tempfile.gettempdir()) / 'genie-report-studio-update.ps1'
    script.write_text(
        'param([int]$ProcessId,[string]$Installer)\n'
        'Wait-Process -Id $ProcessId -ErrorAction SilentlyContinue\n'
        'Start-Process -FilePath $Installer -ArgumentList \'/S\'\n',
        encoding='utf-8')
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0) | getattr(subprocess, 'DETACHED_PROCESS', 0)
    subprocess.Popen(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                      '-File', str(script), '-ProcessId', str(os.getpid()),
                      '-Installer', str(installer)], creationflags=flags,
                     close_fds=True)

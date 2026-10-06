from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = collect_submodules('pdfminer') + collect_submodules('pdfplumber')
datas = collect_data_files('pdfminer') + [('app/interface.html', '.')]

a = Analysis(
    ['app/server.py'],
    pathex=['app'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GENIE-Report-Studio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = collect_submodules('pdfminer') + collect_submodules('pdfplumber')
datas = collect_data_files('pdfminer') + [
    ('app/interface.html', '.'),
    ('version.txt', '.'),
    ('build/offline-edition.json', '.'),
    ('assets/platinum-189.png', 'assets'),
    ('assets/platinum-189-animated.js', 'assets'),
]

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
    name='Platinum-189',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='assets/platinum-189.ico',
)

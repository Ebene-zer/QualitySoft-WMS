# -*- mode: python ; coding: utf-8 -*-

import sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hiddenimports = []

# Optional: include any dynamic submodules PyInstaller might miss
hiddenimports += collect_submodules('matplotlib')
hiddenimports += collect_submodules('pandas')


a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[('assets' + '/*', 'assets')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='tradia',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='assets/tradia.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='tradia'
)


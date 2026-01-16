# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('eagle_traders.db', '.'), ('fonts', 'fonts'), ('style.qss', '.'), ('invoice.html', '.'), ('header.png', '.'), ('C:\\Users\\Cyber Menta CEO\\AppData\\Local\\Python\\pythoncore-3.14-64\\Lib\\site-packages\\barcode\\fonts', 'barcode/fonts')],
    hiddenimports=['barcode'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

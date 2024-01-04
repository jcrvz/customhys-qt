# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['customhys-qt.py'],
    pathex=[],
    binaries=[],
    datas=[('data/*', 'data'), ('data/icons/*', 'data/icons')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='customhys-qt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['data/chm_logo.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='customhys-qt',
)
app = BUNDLE(
    coll,
    name='customhys-qt.app',
    icon='data/chm_logo.ico',
    bundle_identifier=None,
)

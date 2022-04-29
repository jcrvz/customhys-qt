# -*- mode: python -*-

block_cipher = None


a = Analysis(['customhys-qt.py'],
             pathex=['/Users/jcrvz/Library/Mobile Documents/com~apple~CloudDocs/Codes/customhys-qt'],
             binaries=[],
             datas=[('customhys', '.'), ('customhys-qt.ui','.'), ('data', 'data')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='cUIstomhys',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          icon='assets/chm_logo.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='cUIstomhys')

# -*- mode: python -*-

block_cipher = None


a = Analysis(['customhys-qt.py'],
             pathex=[],
             binaries=[],
             datas=[('customhys-qt.ui','.'), ('data', 'data')],
             hiddenimports=['PyQt6', 'PyQt6-Qt6', 'PyQt6-sip', 'numpy', 'matplotlib', 'customhys==1.0.1.dev1'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure,
          a.zipped_data,
          cipher=block_cipher)

#if sys.platform == 'darwin':
exe = EXE(pyz,
          a.binaries,
          a.datas,
          name='cUIstomhys',
          debug=True,
          strip=False,
          upx=False,
          console=True,
          onefile=True,
          windowed=True,
          runtime_tmpdir=None,
          icon="data/chm_logo.icns")

#if sys.platform == 'darwin':
app = BUNDLE(exe,
             name="cUIstomhys.app",
             info_plist={
                'NSHighResolutionCapable': 'True'
             },
             icon="data/chm_logo.icns")


#if sys.platform == 'win32' or sys.platform == 'win64' or sys.platform == 'linux':
#    exe = EXE(pyz,
#              a.scripts,
#              a.binaries,
#              a.zipfiles,
#              a.datas,
#              name='cUIstomhys',
#              debug=False,
#              strip=False,
#              upx=True,
#              console=False,
#              runtime_tmpdir=None,
#              icon='data/chm_logo.ico')


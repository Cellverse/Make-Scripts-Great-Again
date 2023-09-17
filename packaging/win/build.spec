# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

image_overrides = Tree('images', prefix='images')

a = Analysis(['main.py'],  # replace me with your path
             pathex=['.'],
             binaries=[],
             datas=[],
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
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          image_overrides,
          name='AutoCryoSPARC',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          icon=os.path.join('images', 'program_icon.ico'),
          options={'python_flags': ['u']})  # Added the unbuffered mode flag here

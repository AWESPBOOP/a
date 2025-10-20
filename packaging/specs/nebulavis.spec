# PyInstaller spec for NebulaVis

block_cipher = None

a = Analysis(
    ['-m', 'nebulavis.main'],
    pathex=[],
    binaries=[],
    datas=[('src/nebulavis/resources', 'nebulavis/resources')],
    hiddenimports=['sounddevice', 'moderngl', 'glfw', 'dearpygui.dearpygui'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='NebulaVis',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

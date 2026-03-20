# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Collect all data/binaries for ultralytics, moviepy, and their dependencies
ultralytics_datas, ultralytics_binaries, ultralytics_hiddenimports = collect_all('ultralytics')
moviepy_datas, moviepy_binaries, moviepy_hiddenimports = collect_all('moviepy')
imageio_datas, imageio_binaries, imageio_hiddenimports = collect_all('imageio')
imageio_ffmpeg_datas, imageio_ffmpeg_binaries, imageio_ffmpeg_hiddenimports = collect_all('imageio_ffmpeg')

# Collect submodules that PyInstaller might miss
hidden_imports = collect_submodules('ultralytics') + collect_submodules('moviepy')
hidden_imports += [
    'torch',
    'torchvision',
    'requests',
    'PIL',
    'PIL._tkinter_finder',
    'cv2',
    'numpy',
    'yaml',
    'tqdm',
    'psutil',
    'py_cpuinfo',
    'charset_normalizer',
    'certifi',
    'urllib3',
    'idna',
]

a = Analysis(
    ['gui_app.py'],
    pathex=['.'],
    binaries=ultralytics_binaries + moviepy_binaries + imageio_binaries + imageio_ffmpeg_binaries,
    datas=[
        ('run_mosaic.py', '.'),
        ('models', 'models'),
    ] + ultralytics_datas + moviepy_datas + imageio_datas + imageio_ffmpeg_datas,
    hiddenimports=hidden_imports + ultralytics_hiddenimports + moviepy_hiddenimports + imageio_hiddenimports + imageio_ffmpeg_hiddenimports,
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
    [],
    exclude_binaries=True,
    name='MosaicApp',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MosaicApp',
)

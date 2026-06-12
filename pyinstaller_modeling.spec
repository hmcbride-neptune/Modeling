# PyInstaller spec for Modeling app
# This spec uses PyInstaller helpers to collect PyQt5 data and binaries
# so Qt plugins (platforms, styles, etc.) are bundled correctly.
# Run with: pyinstaller pyinstaller_modeling.spec

from PyInstaller.utils.hooks import collect_all
import os

block_cipher = None

# collect PyQt5 package data, binaries and hidden imports
datas, binaries, hiddenimports = collect_all('PyQt5')

# Filter out any collected entries whose source path does not exist. Some PyQt
# installations can return plugin paths like '/plugins' which aren't valid on
# the build machine; skip those to avoid build-time exceptions.
def _src_exists(entry):
    # entry may be a tuple (src, dest) or a plain path
    try:
        src = entry[0] if isinstance(entry, (list, tuple)) else entry
    except Exception:
        src = entry
    return os.path.exists(src)

filtered_datas = [d for d in datas if _src_exists(d)]
filtered_binaries = [b for b in binaries if _src_exists(b)]

# Application analysis

a = Analysis(
    ['run.py'],
    pathex=['.'],
    binaries=filtered_binaries,
    datas=filtered_datas,
    hiddenimports=hiddenimports,
    hookspath=['pyinstaller_hooks'],
    runtime_hooks=[],
    # Exclude Qt WebEngine modules if your app doesn't use them. Some PyQt5
    # installations report webengine-related translation directories that don't
    # exist on the build machine which causes PyInstaller to fail. Excluding
    # these modules prevents their hooks from running.
    excludes=[
        'PyQt5.QtWebEngine',
        'PyQt5.QtWebEngineCore',
        'PyQt5.QtWebEngineWidgets',
        'PyQt5.QtWebEngineWidgets',
        'PyQt5.QtWebChannel',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Modeling',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='Modeling',
)

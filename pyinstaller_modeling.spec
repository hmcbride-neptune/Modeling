# PyInstaller spec for Modeling app
# Run with: pyinstaller pyinstaller_modeling.spec
#
# Qt collection is done explicitly here rather than via PyInstaller's Qt hooks.
# The PyQt5 wheel in this venv reports an empty QLibraryInfo prefix (plugin dir
# resolves to '/plugins'), which makes PyInstaller's automatic Qt hooks either
# raise or silently collect nothing. The wrapper hooks in pyinstaller_hooks/
# neutralise those hooks, and the plugin/binary collection below replaces them.

import os

import PyQt5

block_cipher = None

QT5_DIR = os.path.join(os.path.dirname(PyQt5.__file__), 'Qt5')

# Qt plugins the app actually needs. 'platforms' is mandatory (qwindows.dll);
# the rest cover widget styling, icons and image loading.
QT_PLUGIN_DIRS = [
    'platforms',
    'platformthemes',
    'styles',
    'imageformats',
    'iconengines',
]

binaries = []
for plugin_dir in QT_PLUGIN_DIRS:
    src_dir = os.path.join(QT5_DIR, 'plugins', plugin_dir)
    if not os.path.isdir(src_dir):
        continue
    dest_dir = os.path.join('PyQt5', 'Qt5', 'plugins', plugin_dir)
    for name in os.listdir(src_dir):
        if name.lower().endswith('.dll'):
            binaries.append((os.path.join(src_dir, name), dest_dir))

# Core Qt libraries plus the OpenGL/ANGLE fallbacks QtGui loads at runtime.
QT_BIN_LIBS = [
    'Qt5Core.dll',
    'Qt5Gui.dll',
    'Qt5Widgets.dll',
    'libEGL.dll',
    'libGLESv2.dll',
    'opengl32sw.dll',
    'd3dcompiler_47.dll',
]
for name in QT_BIN_LIBS:
    src = os.path.join(QT5_DIR, 'bin', name)
    if os.path.isfile(src):
        binaries.append((src, '.'))

a = Analysis(
    ['run.py'],
    pathex=['.'],
    binaries=binaries,
    datas=[],
    hiddenimports=['PyQt5.sip'],
    hookspath=['pyinstaller_hooks'],
    runtime_hooks=[],
    # Only QtCore/QtGui/QtWidgets are used. Excluding the rest keeps their
    # hooks from running - several of them fail against this PyQt5 install.
    excludes=[
        'PyQt5.QtBluetooth',
        'PyQt5.QtDBus',
        'PyQt5.QtDesigner',
        'PyQt5.QtHelp',
        'PyQt5.QtLocation',
        'PyQt5.QtMultimedia',
        'PyQt5.QtMultimediaWidgets',
        'PyQt5.QtNfc',
        'PyQt5.QtOpenGL',
        'PyQt5.QtPositioning',
        'PyQt5.QtQml',
        'PyQt5.QtQuick',
        'PyQt5.QtQuick3D',
        'PyQt5.QtQuickWidgets',
        'PyQt5.QtRemoteObjects',
        'PyQt5.QtSensors',
        'PyQt5.QtSerialPort',
        'PyQt5.QtSql',
        'PyQt5.QtTest',
        'PyQt5.QtTextToSpeech',
        'PyQt5.QtWebChannel',
        'PyQt5.QtWebEngine',
        'PyQt5.QtWebEngineCore',
        'PyQt5.QtWebEngineWidgets',
        'PyQt5.QtWebSockets',
        'PyQt5.QtXmlPatterns',
        'PyQt5.QAxContainer',
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

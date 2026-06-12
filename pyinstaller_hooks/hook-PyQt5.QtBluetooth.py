# Safe wrapper hook for PyQt5.QtBluetooth
try:
    from PyInstaller.utils.hooks.qt import add_qt5_dependencies
    hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
except Exception:
    hiddenimports, binaries, datas = [], [], []

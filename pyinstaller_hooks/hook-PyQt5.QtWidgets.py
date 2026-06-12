# Safe wrapper hook for PyQt5.QtWidgets
# Some PyQt5 installations report plugin directories that don't exist
# (e.g. '/plugins'). The standard hook can raise an exception in that
# case. This wrapper attempts to call the real helper and falls back to
# empty lists if collection fails.
try:
    # Use the helper provided by PyInstaller for Qt5
    from PyInstaller.utils.hooks.qt import add_qt5_dependencies
    hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
except Exception:
    hiddenimports, binaries, datas = [], [], []

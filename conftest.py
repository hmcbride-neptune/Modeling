import os
import sys

# Set Qt platform plugin path before any Qt imports
script_dir = os.path.dirname(os.path.abspath(__file__))
plugins_path = os.path.join(script_dir, 'venv', 'Lib', 'site-packages', 'PyQt5', 'Qt5', 'plugins')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugins_path

import pytest
from PyQt5.QtWidgets import QApplication


def pytest_configure(config):
    """Configure pytest with QApplication."""
    if QApplication.instance() is None:
        app = QApplication([])

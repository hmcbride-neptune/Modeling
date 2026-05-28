#!/usr/bin/env python
import sys
import os

# Set up Qt plugin path before importing PyQt5
script_dir = os.path.dirname(os.path.abspath(__file__))
plugins_path = os.path.join(script_dir, 'venv', 'Lib', 'site-packages', 'PyQt5', 'Qt5', 'plugins')

os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugins_path

# Import the main function and classes
sys.path.insert(0, script_dir)

# Import after setting the plugin path
from PyQt5.QtWidgets import QApplication
import main as main_module

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = main_module.MainWindow()
    main_window.show()
    sys.exit(app.exec_())

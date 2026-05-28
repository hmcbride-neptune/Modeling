#  This file will be the main entry point for the application. It will be responsible for starting the application and initializing any necessary components.
# It will create the main window and set up the user interface. It will also handle any necessary events and interactions with the user.
# I need a gui with a button to import project files. They should be 'Collectors.csv', 'CollectorUsagePrem.csv', 'DataAll.csv', 'DataByColl.csv', 'Prem.csv', 'RSSIDecline.csv'
# When the user clicks the button, it should open a file dialog to allow them to select the files.
# The user should be able to edit the files in the application and save any changes back to the original files. Particularly the 'Collectors.csv', the user shuould add the 'EDXName' column to it. 
# There should be an area in the application that displays the unique collectors from the 'Collectors.csv' file. The user should select only the collectors they want to include in the analysis. The selected collectors should be used to filter the data in the other files and update the displayed information accordingly.
# Collector Column Names: 'Collectors.csv' -> 'collector name'; 'CollectorUsagePrem.csv' -> 'collector'; 'DataByColl.csv' -> 'device_description'; 'Prem.csv' -> 'collowner'

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QListWidget, QMessageBox
import pandas as pd
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Collector Data Analysis")
        self.setGeometry(100, 100, 800, 600)

        self.collectors_file = None
        self.collector_usage_prem_file = None
        self.data_all_file = None
        self.data_by_coll_file = None
        self.prem_file = None
        self.rssi_decline_file = None

        self.collectors_data = None
        self.selected_collectors = []

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.import_button = QPushButton("Import Project Files")
        self.import_button.clicked.connect(self.import_files)
        layout.addWidget(self.import_button)

        self.collector_list_widget = QListWidget()
        layout.addWidget(self.collector_list_widget)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def import_files(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        files, _ = QFileDialog.getOpenFileNames(self, "Select Project Files", "",
                                                "CSV Files (*.csv);;All Files (*)", options=options)
        
        if files:
            try:
                for file in files:
                    if 'Collectors.csv' in file:
                        self.collectors_file = file
                        self.collectors_data = pd.read_csv(file)
                    elif 'CollectorUsagePrem.csv' in file:
                        self.collector_usage_prem_file = file
                    elif 'DataAll.csv' in file:
                        self.data_all_file = file
                    elif 'DataByColl.csv' in file:
                        self.data_by_coll_file = file
                    elif 'Prem.csv' in file:
                        self.prem_file = file
                    elif 'RSSIDecline.csv' in file:
                        self.rssi_decline_file = file
                
                if self.collectors_data is not None:
                    unique_collectors = self.collectors_data['collector name'].unique()
                    self.collector_list_widget.addItems(unique_collectors)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while importing files: {e}")
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

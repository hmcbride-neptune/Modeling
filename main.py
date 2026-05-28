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
        self.collector_list_widget.setSelectionMode(self.collector_list_widget.MultiSelection)
        layout.addWidget(self.collector_list_widget)

        self.filter_button = QPushButton("Filter Collectors")
        self.filter_button.clicked.connect(self.filter_collectors)
        layout.addWidget(self.filter_button)

        self.remove_button = QPushButton("Remove All Files")
        self.remove_button.clicked.connect(self.remove_all_files)
        layout.addWidget(self.remove_button)

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
                    self.collector_list_widget.clear()
                    self.collector_list_widget.addItems([str(c) for c in unique_collectors])
                    QMessageBox.information(self, "Success", f"Files imported successfully. Found {len(unique_collectors)} collectors.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while importing files: {e}")

    def filter_collectors(self):
        selected_items = self.collector_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select at least one collector to filter.")
            return
        
        try:
            self.selected_collectors = [item.text() for item in selected_items]
            
            # Filter each loaded file by selected collectors
            if self.collectors_data is not None:
                self.collectors_data = self.collectors_data[self.collectors_data['collector name'].isin(self.selected_collectors)]
            
            if self.collector_usage_prem_file is not None:
                data = pd.read_csv(self.collector_usage_prem_file)
                data = data[data['collector'].isin(self.selected_collectors)]
                data.to_csv(self.collector_usage_prem_file, index=False)
            
            if self.data_all_file is not None:
                data = pd.read_csv(self.data_all_file)
                data = data[data['device_description'].isin(self.selected_collectors)]
                data.to_csv(self.data_all_file, index=False)
            
            if self.data_by_coll_file is not None:
                data = pd.read_csv(self.data_by_coll_file)
                data = data[data['device_description'].isin(self.selected_collectors)]
                data.to_csv(self.data_by_coll_file, index=False)
            
            if self.prem_file is not None:
                data = pd.read_csv(self.prem_file)
                data = data[data['collowner'].isin(self.selected_collectors)]
                data.to_csv(self.prem_file, index=False)
            
            if self.rssi_decline_file is not None:
                data = pd.read_csv(self.rssi_decline_file)
                # Assuming a column exists for filtering; adjust if needed
                if 'collector' in data.columns:
                    data = data[data['collector'].isin(self.selected_collectors)]
                    data.to_csv(self.rssi_decline_file, index=False)
            
            QMessageBox.information(self, "Success", f"Filtered {len(self.selected_collectors)} collector(s) across all files.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while filtering collectors: {e}")

    def remove_all_files(self):
        reply = QMessageBox.question(self, "Confirm", "Are you sure you want to remove all files from memory?",
                                      QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.collectors_file = None
            self.collector_usage_prem_file = None
            self.data_all_file = None
            self.data_by_coll_file = None
            self.prem_file = None
            self.rssi_decline_file = None
            
            self.collectors_data = None
            self.selected_collectors = []
            
            self.collector_list_widget.clear()
            QMessageBox.information(self, "Success", "All files have been removed from memory.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

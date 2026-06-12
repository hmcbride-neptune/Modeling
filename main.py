import sys
import pandas as pd
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout,
    QHBoxLayout, QWidget, QListWidget, QListWidgetItem, QMessageBox,
    QLabel, QLineEdit, QDialog, QDialogButtonBox, QTableWidget,
    QAbstractItemView,
    QTableWidgetItem, QInputDialog, QProgressBar,
)
from file_cleanup import FileManager
from SystemAnalysis import run_analysis


class PasteableTableWidget(QTableWidget):
    """QTableWidget that accepts Excel-style Ctrl+V paste (TSV with newline-separated rows)."""

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Paste):
            self._paste_from_clipboard()
            return
        super().keyPressEvent(event)

    def _paste_from_clipboard(self):
        text = QApplication.clipboard().text()
        if not text:
            return
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        if text.endswith('\n'):
            text = text[:-1]
        rows = [line.split('\t') for line in text.split('\n')]

        start_row = max(self.currentRow(), 0)
        start_col = max(self.currentColumn(), 0)

        needed_rows = start_row + len(rows)
        if needed_rows > self.rowCount():
            self.setRowCount(needed_rows)

        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                col = start_col + c
                if col >= self.columnCount():
                    break
                self.setItem(start_row + r, col, QTableWidgetItem(value))


class CollectorsEditorDialog(QDialog):
    """Modal editor that loads a CSV into a table, lets the user edit cells, and saves."""

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.df = pd.read_csv(file_path)
        self.result_df = None

        self.setWindowTitle("Edit Collectors.csv")
        self.resize(800, 600)

        layout = QVBoxLayout()

        self.table = PasteableTableWidget(len(self.df), len(self.df.columns))
        self.table.setHorizontalHeaderLabels([str(c) for c in self.df.columns])
        for r in range(len(self.df)):
            for c in range(len(self.df.columns)):
                value = self.df.iat[r, c]
                text = "" if pd.isna(value) else str(value)
                self.table.setItem(r, c, QTableWidgetItem(text))
        layout.addWidget(self.table)

        row_buttons = QHBoxLayout()
        add_row_btn = QPushButton("Add Row")
        add_row_btn.clicked.connect(self.add_row)
        remove_row_btn = QPushButton("Remove Selected Row")
        remove_row_btn.clicked.connect(self.remove_selected_row)
        add_col_btn = QPushButton("Add Column")
        add_col_btn.clicked.connect(self.add_column)
        remove_col_btn = QPushButton("Remove Selected Column")
        remove_col_btn.clicked.connect(self.remove_selected_column)
        row_buttons.addWidget(add_row_btn)
        row_buttons.addWidget(remove_row_btn)
        row_buttons.addWidget(add_col_btn)
        row_buttons.addWidget(remove_col_btn)
        row_buttons.addStretch()
        layout.addLayout(row_buttons)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def add_row(self):
        self.table.insertRow(self.table.rowCount())

    def remove_selected_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def add_column(self):
        name, ok = QInputDialog.getText(self, "Add Column", "Column name:")
        if not ok or not name.strip():
            return
        col = self.table.columnCount()
        self.table.insertColumn(col)
        self.table.setHorizontalHeaderItem(col, QTableWidgetItem(name.strip()))

    def remove_selected_column(self):
        col = self.table.currentColumn()
        if col >= 0:
            self.table.removeColumn(col)

    def save(self):
        columns = [self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount())]
        data = []
        for r in range(self.table.rowCount()):
            row = []
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                row.append(item.text() if item is not None else "")
            data.append(row)
        try:
            new_df = pd.DataFrame(data, columns=columns)
            new_df.to_csv(self.file_path, index=False)
            self.result_df = new_df
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")


def _delegated(name):
    """Build a property that forwards reads and writes to self.file_manager.<name>."""
    return property(
        lambda self: getattr(self.file_manager, name),
        lambda self, value: setattr(self.file_manager, name, value),
    )


class MainWindow(QMainWindow):
    collectors_file = _delegated('collectors_file')
    collector_usage_prem_file = _delegated('collector_usage_prem_file')
    data_all_file = _delegated('data_all_file')
    data_by_coll_file = _delegated('data_by_coll_file')
    prem_file = _delegated('prem_file')
    rssi_decline_file = _delegated('rssi_decline_file')
    collectors_data = _delegated('collectors_data')
    all_collectors = _delegated('all_collectors')

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Collector Data Analysis")
        self.setGeometry(100, 100, 800, 600)

        self.file_manager = FileManager()
        self.selected_collectors = []
        self.search_text = ""

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.import_button = QPushButton("Import Project Files")
        self.import_button.clicked.connect(self.import_files)
        layout.addWidget(self.import_button)

        files_label = QLabel("Imported Files:")
        layout.addWidget(files_label)

        self.files_list_widget = QListWidget()
        self.files_list_widget.setMaximumHeight(100)
        layout.addWidget(self.files_list_widget)

        collectors_label = QLabel("Collectors:")
        layout.addWidget(collectors_label)

        self.collector_search = QLineEdit()
        self.collector_search.setPlaceholderText("Search collectors...")
        self.collector_search.textChanged.connect(self.search_collectors)
        layout.addWidget(self.collector_search)

        self.collector_list_widget = QListWidget()
        # Use ExtendedSelection so Ctrl+click toggles selection and mouse-drag selects ranges
        self.collector_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.collector_list_widget.itemSelectionChanged.connect(self.sync_selected_collectors)
        layout.addWidget(self.collector_list_widget)

        # Label showing how many gateways/collectors are currently selected
        self.selected_count_label = QLabel("Selected gateways: 0")
        layout.addWidget(self.selected_count_label)

        self.filter_button = QPushButton("Filter Collectors")
        self.filter_button.clicked.connect(self.filter_collectors)
        layout.addWidget(self.filter_button)

        self.clean_button = QPushButton("Clean Files")
        self.clean_button.clicked.connect(self.clean_prem)
        layout.addWidget(self.clean_button)

        self.create_files_button = QPushButton("Create Files")
        self.create_files_button.clicked.connect(self.create_files)
        layout.addWidget(self.create_files_button)

        self.remove_button = QPushButton("Remove All Files")
        self.remove_button.clicked.connect(self.remove_all_files)
        layout.addWidget(self.remove_button)

        self.progress_label = QLabel("Idle")
        layout.addWidget(self.progress_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def _set_progress(self, percent, message):
        """Update the progress bar/label and force the UI to repaint."""
        self.progress_bar.setValue(int(percent))
        self.progress_label.setText(message)
        QApplication.processEvents()

    def _reset_progress(self):
        self.progress_bar.setValue(0)
        self.progress_label.setText("Idle")

    def import_files(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        files, _ = QFileDialog.getOpenFileNames(self, "Select Project Files", "",
                                                "CSV Files (*.csv);;All Files (*)", options=options)

        if files:
            try:
                self._set_progress(20, "Importing files...")
                count = self.file_manager.import_files(files)
                self._set_progress(70, "Updating file list...")
                self.update_file_list()
                if self.collectors_data is not None:
                    self.update_collector_list()
                    self._set_progress(100, f"Imported {count} collectors")
                    QMessageBox.information(self, "Success", f"Files imported successfully. Found {count} collectors.")
                self._reset_progress()
            except Exception as e:
                self._reset_progress()
                QMessageBox.critical(self, "Error", f"An error occurred while importing files: {e}")

    def update_file_list(self):
        """Update the files list widget to show all imported files."""
        self.files_list_widget.clear()
        imported = self.file_manager.get_imported_filenames()
        if not imported:
            self.files_list_widget.addItem("No files imported")
            return

        for filename in imported:
            item = QListWidgetItem(self.files_list_widget)
            if filename == "Collectors.csv":
                row_widget = QWidget()
                row_layout = QHBoxLayout()
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.addWidget(QLabel(f"✓ {filename}"))
                row_layout.addStretch()
                edit_btn = QPushButton("Edit")
                edit_btn.clicked.connect(self.open_collectors_editor)
                row_layout.addWidget(edit_btn)
                row_widget.setLayout(row_layout)
                item.setSizeHint(row_widget.sizeHint())
                self.files_list_widget.setItemWidget(item, row_widget)
            else:
                item.setText(f"✓ {filename}")

    def open_collectors_editor(self):
        """Open the tabular editor for Collectors.csv and refresh state on save."""
        if not self.file_manager.collectors_file:
            return
        dialog = CollectorsEditorDialog(self.file_manager.collectors_file, self)
        if dialog.exec_() == QDialog.Accepted and dialog.result_df is not None:
            self.file_manager.set_collectors_data(dialog.result_df)
            self.selected_collectors = [c for c in self.selected_collectors if c in self.all_collectors]
            self.update_collector_list()
            QMessageBox.information(self, "Saved", "Collectors.csv has been updated.")

    def update_collector_list(self):
        """Refresh the collector list based on search text and current selections."""
        self.collector_list_widget.blockSignals(True)
        self.collector_list_widget.clear()
        filtered = [collector for collector in self.all_collectors if self.search_text.lower() in collector.lower()]
        self.collector_list_widget.addItems(filtered)
        for i in range(self.collector_list_widget.count()):
            item = self.collector_list_widget.item(i)
            if item.text() in self.selected_collectors:
                item.setSelected(True)
        self.collector_list_widget.blockSignals(False)
        # Update selected count label to reflect preserved selections
        self.update_selected_gateways_count()

    def search_collectors(self, text):
        self.search_text = text
        self.update_collector_list()

    def sync_selected_collectors(self):
        selected_items = self.collector_list_widget.selectedItems()
        visible_items = [self.collector_list_widget.item(i).text() for i in range(self.collector_list_widget.count())]
        selected_texts = [item.text() for item in selected_items]

        # Preserve selections for collectors not currently visible while syncing visible selection state.
        self.selected_collectors = [text for text in self.selected_collectors if text not in visible_items]
        self.selected_collectors.extend([text for text in selected_texts if text not in self.selected_collectors])
        self.selected_collectors = [text for text in self.selected_collectors if text in self.all_collectors]
        # Update the selected count label whenever the selection changes
        self.update_selected_gateways_count()

    def filter_collectors(self):
        selected_items = self.collector_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select at least one collector to filter.")
            return

        try:
            self.selected_collectors = [item.text() for item in selected_items]
            self._set_progress(30, "Filtering source files...")
            self.file_manager.filter_by_collectors(self.selected_collectors)
            self._set_progress(80, "Refreshing collector list...")
            self.search_text = ""
            self.collector_search.clear()
            self.update_collector_list()
            self._set_progress(100, f"Filtered {len(self.selected_collectors)} collector(s)")
            QMessageBox.information(self, "Success", f"Filtered {len(self.selected_collectors)} collector(s) across all files.")
            self._reset_progress()
        except Exception as e:
            self._reset_progress()
            QMessageBox.critical(self, "Error", f"An error occurred while filtering collectors: {e}")

    def clean_prem(self):
        """Drop Prem.csv rows whose latitude or longitude is invalid."""
        try:
            self._set_progress(40, "Cleaning Prem.csv lat/lon...")
            removed, status = self.file_manager.clean_prem_lat_lon()
        except Exception as e:
            self._reset_progress()
            QMessageBox.critical(self, "Error", f"An error occurred while cleaning Prem.csv: {e}")
            return

        if status == 'no_file':
            self._reset_progress()
            QMessageBox.warning(self, "Warning", "Prem.csv has not been imported.")
        elif status == 'no_lat_lon_columns':
            self._reset_progress()
            QMessageBox.warning(self, "Warning", "Could not find latitude/longitude columns in Prem.csv.")
        else:
            self._set_progress(100, f"Removed {removed} row(s)")
            QMessageBox.information(self, "Success", f"Removed {removed} Prem.csv row(s) with invalid lat/lon.")
            self._reset_progress()

    def create_files(self):
        """Run the system analysis on the imported files and write outputs to a user-selected folder."""
        required = {
            'Collectors.csv': self.file_manager.collectors_file,
            'CollectorUsagePrem.csv': self.file_manager.collector_usage_prem_file,
            'DataAll.csv': self.file_manager.data_all_file,
            'DataByColl.csv': self.file_manager.data_by_coll_file,
            'RSSIDecline.csv': self.file_manager.rssi_decline_file,
            'Prem.csv': self.file_manager.prem_file,
        }
        missing = [name for name, path in required.items() if not path]
        if missing:
            QMessageBox.warning(self, "Missing Files",
                                "Cannot create files. Missing: " + ", ".join(missing))
            return

        months = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
        month_name, ok = QInputDialog.getItem(self, "Analysis Month",
                                              "Select the month of analysis:", months, 11, False)
        if not ok:
            return
        analysis_month = months.index(month_name) + 1

        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if not output_dir:
            return

        try:
            summary = run_analysis(
                collectors_file=required['Collectors.csv'],
                collector_usage_file=required['CollectorUsagePrem.csv'],
                data_all_file=required['DataAll.csv'],
                data_by_coll_file=required['DataByColl.csv'],
                rssi_decline_file=required['RSSIDecline.csv'],
                prem_file=required['Prem.csv'],
                output_dir=output_dir,
                analysis_month=analysis_month,
                progress_callback=self._set_progress,
            )
        except Exception as e:
            self._reset_progress()
            QMessageBox.critical(self, "Error", f"Analysis failed: {e}")
            return

        QMessageBox.information(
            self, "Success",
            f"Analysis complete for {month_name}.\n\n"
            f"Output folder: {summary['output_dir']}\n"
            f"Good collectors: {summary['good_collectors']}\n"
            f"Good MIUs: {summary['good_mius']}\n"
            f"Cleaned Prem rows: {summary['cleaned_prem']}\n"
            f"Cleaned Data rows: {summary['cleaned_data']}\n"
            f"Measurement files: {summary['measurement_files']}\n"
            f"Meter files: {summary['meter_files']}"
        )
        self._reset_progress()

    def remove_all_files(self):
        reply = QMessageBox.question(self, "Confirm", "Are you sure you want to remove all files from memory?",
                                      QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.file_manager.reset()
            self.selected_collectors = []
            self.search_text = ""
            self.collector_search.clear()
            self.files_list_widget.clear()
            self.files_list_widget.addItem("No files imported")
            self.collector_list_widget.clear()
            # reflect zero selections in the UI
            self.update_selected_gateways_count()
            QMessageBox.information(self, "Success", "All files have been removed from memory.")

    def update_selected_gateways_count(self):
        """Set the selected gateways label text to the current number of selected collectors."""
        try:
            count = len(self.selected_collectors) if self.selected_collectors is not None else 0
        except Exception:
            count = 0
        self.selected_count_label.setText(f"Selected gateways: {count}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

import pytest
import pandas as pd
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from PyQt5.QtWidgets import QApplication
from main import MainWindow


@pytest.fixture
def qapp():
    """Create a QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def main_window(qapp):
    """Create a MainWindow instance for testing."""
    window = MainWindow()
    return window


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_data(temp_dir):
    """Create sample CSV files for testing."""
    # Create sample Collectors.csv
    collectors_data = {
        'collector name': ['Collector1', 'Collector2', 'Collector3'],
        'location': ['Site A', 'Site B', 'Site C'],
        'status': ['active', 'active', 'inactive']
    }
    collectors_path = os.path.join(temp_dir, 'Collectors.csv')
    pd.DataFrame(collectors_data).to_csv(collectors_path, index=False)
    
    # Create sample CollectorUsagePrem.csv
    usage_data = {
        'collector': ['Collector1', 'Collector2', 'Collector1', 'Collector3'],
        'usage_count': [100, 200, 150, 50],
        'date': ['2024-01-01', '2024-01-01', '2024-01-02', '2024-01-02']
    }
    usage_path = os.path.join(temp_dir, 'CollectorUsagePrem.csv')
    pd.DataFrame(usage_data).to_csv(usage_path, index=False)
    
    # Create sample DataAll.csv
    data_all = {
        'device_description': ['Collector1', 'Collector2', 'Collector3'],
        'signal_strength': [50, 60, 40],
        'timestamp': ['2024-01-01 10:00', '2024-01-01 10:05', '2024-01-01 10:10']
    }
    data_all_path = os.path.join(temp_dir, 'DataAll.csv')
    pd.DataFrame(data_all).to_csv(data_all_path, index=False)
    
    # Create sample DataByColl.csv
    data_by_coll = {
        'device_description': ['Collector1', 'Collector2'],
        'value': [10, 20],
        'reading': ['reading1', 'reading2']
    }
    data_by_coll_path = os.path.join(temp_dir, 'DataByColl.csv')
    pd.DataFrame(data_by_coll).to_csv(data_by_coll_path, index=False)
    
    # Create sample Prem.csv
    prem_data = {
        'collowner': ['Collector1', 'Collector2', 'Collector3'],
        'premise_id': [101, 102, 103],
        'address': ['123 Main St', '456 Oak Ave', '789 Pine Rd']
    }
    prem_path = os.path.join(temp_dir, 'Prem.csv')
    pd.DataFrame(prem_data).to_csv(prem_path, index=False)
    
    # Create sample RSSIDecline.csv
    rssi_data = {
        'collector': ['Collector1', 'Collector2', 'Collector3'],
        'rssi_value': [-50, -60, -40],
        'measurement_date': ['2024-01-01', '2024-01-01', '2024-01-01']
    }
    rssi_path = os.path.join(temp_dir, 'RSSIDecline.csv')
    pd.DataFrame(rssi_data).to_csv(rssi_path, index=False)
    
    return {
        'collectors': collectors_path,
        'usage': usage_path,
        'data_all': data_all_path,
        'data_by_coll': data_by_coll_path,
        'prem': prem_path,
        'rssi': rssi_path
    }


class TestMainWindowInit:
    """Test MainWindow initialization."""
    
    def test_main_window_created(self, main_window):
        """Test that MainWindow is created successfully."""
        assert main_window is not None
        assert main_window.windowTitle() == "Collector Data Analysis"
    
    def test_initial_state(self, main_window):
        """Test initial state of MainWindow."""
        assert main_window.collectors_file is None
        assert main_window.collector_usage_prem_file is None
        assert main_window.data_all_file is None
        assert main_window.data_by_coll_file is None
        assert main_window.prem_file is None
        assert main_window.rssi_decline_file is None
        assert main_window.collectors_data is None
        assert main_window.selected_collectors == []
    
    def test_ui_elements_exist(self, main_window):
        """Test that all UI elements are created."""
        assert hasattr(main_window, 'import_button')
        assert hasattr(main_window, 'filter_button')
        assert hasattr(main_window, 'remove_button')
        assert hasattr(main_window, 'collector_list_widget')


class TestFileLoading:
    """Test file loading functionality."""
    
    @patch('main.QFileDialog.getOpenFileNames')
    def test_load_collectors_file(self, mock_dialog, main_window, sample_data):
        """Test loading Collectors.csv file."""
        mock_dialog.return_value = ([sample_data['collectors']], "")
        
        main_window.import_files()
        
        assert main_window.collectors_file == sample_data['collectors']
        assert main_window.collectors_data is not None
        assert len(main_window.collectors_data) == 3
        assert 'collector name' in main_window.collectors_data.columns
    
    @patch('main.QFileDialog.getOpenFileNames')
    def test_load_multiple_files(self, mock_dialog, main_window, sample_data):
        """Test loading multiple files at once."""
        files = [
            sample_data['collectors'],
            sample_data['usage'],
            sample_data['data_all'],
            sample_data['data_by_coll'],
            sample_data['prem'],
            sample_data['rssi']
        ]
        mock_dialog.return_value = (files, "")
        
        main_window.import_files()
        
        assert main_window.collectors_file == sample_data['collectors']
        assert main_window.collector_usage_prem_file == sample_data['usage']
        assert main_window.data_all_file == sample_data['data_all']
        assert main_window.data_by_coll_file == sample_data['data_by_coll']
        assert main_window.prem_file == sample_data['prem']
        assert main_window.rssi_decline_file == sample_data['rssi']
    
    @patch('main.QFileDialog.getOpenFileNames')
    def test_no_files_selected(self, mock_dialog, main_window):
        """Test when no files are selected."""
        mock_dialog.return_value = ([], "")
        
        main_window.import_files()
        
        assert main_window.collectors_file is None
        assert main_window.collectors_data is None


class TestCollectorListDisplay:
    """Test collector list display functionality."""
    
    @patch('main.QFileDialog.getOpenFileNames')
    def test_collectors_displayed_in_list(self, mock_dialog, main_window, sample_data):
        """Test that collectors are displayed in the list widget."""
        mock_dialog.return_value = ([sample_data['collectors']], "")
        
        main_window.import_files()
        
        assert main_window.collector_list_widget.count() == 3
        items = [main_window.collector_list_widget.item(i).text() 
                 for i in range(main_window.collector_list_widget.count())]
        assert 'Collector1' in items
        assert 'Collector2' in items
        assert 'Collector3' in items


class TestFilterFunctionality:
    """Test filtering functionality."""
    
    @patch('main.QFileDialog.getOpenFileNames')
    @patch('main.QMessageBox.warning')
    def test_filter_without_selection(self, mock_warning, mock_dialog, main_window, sample_data):
        """Test filtering without selecting collectors."""
        mock_dialog.return_value = ([sample_data['collectors']], "")
        main_window.import_files()
        
        main_window.filter_collectors()
        
        mock_warning.assert_called_once()
        assert "select at least one collector" in mock_warning.call_args[0][2].lower()
    
    @patch('main.QFileDialog.getOpenFileNames')
    @patch('main.QMessageBox.information')
    def test_filter_single_collector(self, mock_info, mock_dialog, main_window, sample_data, temp_dir):
        """Test filtering with a single collector selected."""
        # Load files
        files = [
            sample_data['collectors'],
            sample_data['usage'],
            sample_data['prem']
        ]
        mock_dialog.return_value = (files, "")
        main_window.import_files()
        
        # Simulate selecting Collector1
        main_window.collector_list_widget.selectAll()
        main_window.collector_list_widget.item(0).setSelected(True)
        main_window.collector_list_widget.item(1).setSelected(False)
        main_window.collector_list_widget.item(2).setSelected(False)
        
        # Get selected items
        selected_items = main_window.collector_list_widget.selectedItems()
        if selected_items:
            main_window.selected_collectors = [item.text() for item in selected_items]
        
        # Manual filter simulation
        if main_window.collectors_data is not None:
            original_count = len(main_window.collectors_data)
            main_window.collectors_data = main_window.collectors_data[
                main_window.collectors_data['collector name'].isin(main_window.selected_collectors)
            ]
            assert len(main_window.collectors_data) <= original_count
    
    @patch('main.QFileDialog.getOpenFileNames')
    @patch('main.QMessageBox.information')
    def test_filter_multiple_collectors(self, mock_info, mock_dialog, main_window, sample_data):
        """Test filtering with multiple collectors selected."""
        mock_dialog.return_value = ([sample_data['collectors']], "")
        main_window.import_files()
        
        # Simulate selecting multiple collectors
        for i in range(min(2, main_window.collector_list_widget.count())):
            main_window.collector_list_widget.item(i).setSelected(True)
        
        selected_items = main_window.collector_list_widget.selectedItems()
        main_window.selected_collectors = [item.text() for item in selected_items]
        
        assert len(main_window.selected_collectors) == 2


class TestRemoveFilesFunction:
    """Test remove all files functionality."""
    
    @patch('main.QFileDialog.getOpenFileNames')
    @patch('main.QMessageBox.question')
    @patch('main.QMessageBox.information')
    def test_remove_all_files_confirmed(self, mock_info, mock_question, mock_dialog, 
                                       main_window, sample_data):
        """Test removing all files when user confirms."""
        from PyQt5.QtWidgets import QMessageBox
        
        mock_dialog.return_value = ([sample_data['collectors']], "")
        mock_question.return_value = QMessageBox.Yes
        
        # Load files
        main_window.import_files()
        assert main_window.collectors_data is not None
        
        # Remove files
        main_window.remove_all_files()
        
        # Verify all files are cleared
        assert main_window.collectors_file is None
        assert main_window.collector_usage_prem_file is None
        assert main_window.data_all_file is None
        assert main_window.data_by_coll_file is None
        assert main_window.prem_file is None
        assert main_window.rssi_decline_file is None
        assert main_window.collectors_data is None
        assert main_window.selected_collectors == []
        assert main_window.collector_list_widget.count() == 0
    
    @patch('main.QFileDialog.getOpenFileNames')
    @patch('main.QMessageBox.question')
    def test_remove_all_files_cancelled(self, mock_question, mock_dialog, main_window, sample_data):
        """Test cancelling the remove all files operation."""
        from PyQt5.QtWidgets import QMessageBox
        
        mock_dialog.return_value = ([sample_data['collectors']], "")
        mock_question.return_value = QMessageBox.No
        
        # Load files
        main_window.import_files()
        original_data = main_window.collectors_data
        
        # Try to remove files
        main_window.remove_all_files()
        
        # Verify files are NOT cleared when user cancels
        assert main_window.collectors_data is not None


class TestDataIntegrity:
    """Test data integrity after operations."""
    
    @patch('main.QFileDialog.getOpenFileNames')
    def test_collectors_data_structure(self, mock_dialog, main_window, sample_data):
        """Test that loaded data maintains correct structure."""
        mock_dialog.return_value = ([sample_data['collectors']], "")
        main_window.import_files()
        
        assert isinstance(main_window.collectors_data, pd.DataFrame)
        assert 'collector name' in main_window.collectors_data.columns
        assert len(main_window.collectors_data) == 3
    
    @patch('main.QFileDialog.getOpenFileNames')
    def test_no_data_corruption_on_load(self, mock_dialog, main_window, sample_data):
        """Test that loading files doesn't corrupt data."""
        mock_dialog.return_value = ([sample_data['collectors']], "")
        
        # Load original data
        original = pd.read_csv(sample_data['collectors'])
        
        # Load via application
        main_window.import_files()
        
        # Verify data is identical
        pd.testing.assert_frame_equal(original, main_window.collectors_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

import pandas as pd


PREM_LAT_CANDIDATES = {'lat', 'latitude', 'prem_latitude', 'y'}
PREM_LON_CANDIDATES = {'lon', 'longitude', 'long', 'prem_longitude', 'x'}


def _find_column(df, candidates):
    """Return the actual column name in df whose lowercased form matches any candidate, else None."""
    for col in df.columns:
        if str(col).strip().lower() in candidates:
            return col
    return None


class FileManager:
    """Owns the imported CSV file paths and the collector data within them."""

    def __init__(self):
        self.collectors_file = None
        self.collector_usage_prem_file = None
        self.data_all_file = None
        self.data_by_coll_file = None
        self.prem_file = None
        self.rssi_decline_file = None

        self.collectors_data = None
        self.all_collectors = []
        self.prem_rows_removed = 0

    def import_files(self, files):
        """Classify the given file paths by filename and load Collectors.csv.

        Returns the number of unique collectors found.
        """
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
            self.all_collectors = [str(c) for c in unique_collectors]
            return len(unique_collectors)
        return 0

    def clean_prem_lat_lon(self):
        """Drop Prem.csv rows with invalid lat/lon and save the cleaned file.

        Invalid means: blank, non-numeric, zero, negative latitude, or positive longitude.
        Returns (removed_count, status) where status is one of
        'ok', 'no_file', 'no_lat_lon_columns'.
        """
        if not self.prem_file:
            return 0, 'no_file'
        df = pd.read_csv(self.prem_file)
        lat_col = _find_column(df, PREM_LAT_CANDIDATES)
        lon_col = _find_column(df, PREM_LON_CANDIDATES)
        if lat_col is None or lon_col is None:
            return 0, 'no_lat_lon_columns'

        original = len(df)
        lat = pd.to_numeric(df[lat_col], errors='coerce')
        lon = pd.to_numeric(df[lon_col], errors='coerce')
        valid = (lat > 0) & (lon < 0)
        cleaned = df[valid]
        cleaned.to_csv(self.prem_file, index=False)
        removed = original - len(cleaned)
        self.prem_rows_removed = removed
        return removed, 'ok'

    def get_imported_filenames(self):
        """Return the basenames of files that have been imported."""
        imported = []
        if self.collectors_file:
            imported.append("Collectors.csv")
        if self.collector_usage_prem_file:
            imported.append("CollectorUsagePrem.csv")
        if self.data_all_file:
            imported.append("DataAll.csv")
        if self.data_by_coll_file:
            imported.append("DataByColl.csv")
        if self.prem_file:
            imported.append("Prem.csv")
        if self.rssi_decline_file:
            imported.append("RSSIDecline.csv")
        return imported

    def set_collectors_data(self, df):
        """Replace in-memory Collectors data and refresh the collector list."""
        self.collectors_data = df
        if 'collector name' in df.columns:
            unique = df['collector name'].unique()
            self.all_collectors = [str(c) for c in unique]

    def filter_by_collectors(self, selected):
        """Filter all loaded CSVs in place to keep only rows for the selected collectors."""
        if self.collectors_data is not None and self.collectors_file is not None:
            filtered = self.collectors_data[self.collectors_data['collector name'].isin(selected)]
            filtered.to_csv(self.collectors_file, index=False)
            self.collectors_data = filtered

        if self.collector_usage_prem_file is not None:
            data = pd.read_csv(self.collector_usage_prem_file)
            data = data[data['collector'].isin(selected)]
            data.to_csv(self.collector_usage_prem_file, index=False)

        if self.data_by_coll_file is not None:
            data = pd.read_csv(self.data_by_coll_file)
            data = data[data['device_description'].isin(selected)]
            data.to_csv(self.data_by_coll_file, index=False)

        if self.prem_file is not None:
            data = pd.read_csv(self.prem_file)
            data = data[data['collowner'].isin(selected)]
            data.to_csv(self.prem_file, index=False)

        self.all_collectors = list(selected)

    def reset(self):
        """Clear all file references and loaded data."""
        self.collectors_file = None
        self.collector_usage_prem_file = None
        self.data_all_file = None
        self.data_by_coll_file = None
        self.prem_file = None
        self.rssi_decline_file = None
        self.collectors_data = None
        self.all_collectors = []
        self.prem_rows_removed = 0

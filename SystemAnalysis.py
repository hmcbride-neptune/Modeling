# I need a python file to help me locate bad mius and bad collectors in our system.
# Collectors - Collector Data: collector name, lat, long, daysactive, EDXName
# CollectorUsagePrem - Collector Usage: collector, miucount, miucountall, avgrssi, avgnoise, system type
# DataAll - MIU Data: miu id, first read, last read, drr, avg rssi, # of readings, hrr, system type, lastrcvd
# DataByColl - MIU data from collectors: miu id, device_description, first read, last read, daysrcvd, avg rssi, # of readings, avgdailyreading, system type
# RSSIDecline - RSSI Changes: reading_miu_id, systype, first_last_30_diff, rssi_change
# Prem - MIU Data: meter_miu_id, prem_latitude, prem_longitude, drr, hrr, firstread, collowner

# Criteria

# Collectors: 	Must have latitude, longitude, EDXName
# 				daysactive must be full month (31)

# CollectorUsagePrem: system type must be L900
# 					avgnoise must be low

# DataAll:		miu id must be in prem
# 				first read must be in month of analysis
# 				system type must be L900

# DataByColl: 	system type must be L900
# 				miu_id must be in prem
# 				avg rssi must be between -50 dBm and -120 dBm(Remove from all files)

# RSSIDecline: 	Remove MIU with RSSI change > +- 10 dB (Remove from all files)
# 				reading_miu_id must be in prem

# Prem: 			firstread can not be in month of analysis


# From this data the mius need filtered for bad mius.
# From this data the collectors need analyzed and pointed out if bad performance

# Outputs needed: Collectors to use for Propagation modeling (Good_Collectors.csv)
# 				MIU list for modeling (Good_MIUs.csv) (If MIU belongs to bad collector remove from list)

import os
import re
import pandas as pd


def run_analysis(
    collectors_file,
    collector_usage_file,
    data_all_file,
    data_by_coll_file,
    rssi_decline_file,
    prem_file,
    output_dir,
    analysis_month,
    progress_callback=None,
):
    """Run the full system analysis and write all output files into output_dir.

    analysis_month: integer 1-12 identifying the month of analysis. Used to
    exclude MIUs whose firstread falls in that month (they are too new to
    judge).

    progress_callback: optional callable taking (percent: int, message: str).
    Invoked at major checkpoints so a GUI can update a progress bar.

    Returns a dict summarizing what was written.
    """
    if not 1 <= analysis_month <= 12:
        raise ValueError(f'analysis_month must be 1-12, got {analysis_month}')

    def report(percent, message):
        if progress_callback is not None:
            progress_callback(percent, message)

    report(0, 'Starting analysis...')
    os.makedirs(output_dir, exist_ok=True)

    report(5, 'Loading source files...')
    collectors = pd.read_csv(collectors_file)
    data_all = pd.read_csv(data_all_file)
    data_by_coll = pd.read_csv(data_by_coll_file)
    prem = pd.read_csv(prem_file)
    _ = collector_usage_file, rssi_decline_file  # accepted in signature for future use
    # Drop Prem rows whose firstread is in the analysis month
    prem = prem[~pd.to_datetime(prem['firstread']).dt.month.eq(analysis_month)]
    report(20, 'Filtering collectors and MIUs...')

    good_collectors = collectors[
        (collectors['lat'].notnull()) &
        (collectors['long'].notnull()) &
        (collectors['daysactive'] == 31)
    ]
    good_data_all = data_all[
        (data_all['miu id'].isin(prem['meter_miu_id'])) &
        (data_all['system type'] == 'L900')
    ]
    good_data_by_coll = data_by_coll[
        (data_by_coll['system type'] == 'L900') &
        (data_by_coll['miu id'].isin(prem['meter_miu_id'])) &
        (data_by_coll['avg rssi'].between(-120, -50))
    ]

    # Collectors serving fewer than 500 MIUs in good_data_by_coll are bad
    miu_counts_per_collector = good_data_by_coll.groupby('device_description')['miu id'].nunique()
    low_miu_collectors = set(miu_counts_per_collector[miu_counts_per_collector < 500].index)
    unseen_collectors = set(collectors['collector name']) - set(miu_counts_per_collector.index)
    bad_collectors = (
        (set(collectors['collector name']) - set(good_collectors['collector name']))
        | low_miu_collectors
        | unseen_collectors
    )
    good_collectors = good_collectors[~good_collectors['collector name'].isin(bad_collectors)]
    good_collector_names = set(good_collectors['collector name'])

    bad_mius = set(data_all['miu id']) - set(good_data_all['miu id'])
    mius_with_good_collector = set(
        good_data_by_coll[good_data_by_coll['device_description'].isin(good_collector_names)]['miu id']
    )
    good_mius = good_data_all[good_data_all['miu id'].isin(mius_with_good_collector)]['miu id']

    report(40, 'Writing Good_Collectors.csv and Good_MIUs.csv...')
    good_collectors.to_csv(os.path.join(output_dir, 'Good_Collectors.csv'), index=False)
    good_mius.to_csv(os.path.join(output_dir, 'Good_MIUs.csv'), index=False)

    report(55, 'Building cleaned Prem and DataByColl...')
    cleaned_prem = prem[~prem['meter_miu_id'].isin(bad_mius)].copy()
    cleaned_data_by_coll = data_by_coll[~data_by_coll['miu id'].isin(bad_mius)]
    # 0-indexed objectid to match the PQ tool's numbering convention
    if not any(col.lower() == 'objectid' for col in cleaned_prem.columns):
        cleaned_prem.insert(0, 'objectid', range(len(cleaned_prem)))
    cleaned_prem.to_csv(os.path.join(output_dir, 'Cleaned_Prem.csv'), index=False)
    cleaned_data_by_coll.to_csv(os.path.join(output_dir, 'Cleaned_DataByColl.csv'), index=False)

    cleaned_data = pd.merge(
        cleaned_data_by_coll,
        cleaned_prem[['meter_miu_id', 'objectid', 'prem_latitude', 'prem_longitude', 'drr', 'hrr', 'collowner']],
        left_on='miu id',
        right_on='meter_miu_id',
        how='inner',
    )
    cleaned_data = cleaned_data[cleaned_data['device_description'].isin(good_collector_names)].copy()
    objectid_col = cleaned_data.pop('objectid')
    cleaned_data.insert(0, 'objectid', objectid_col)
    report(70, 'Writing Cleaned_Data.csv...')
    cleaned_data.to_csv(os.path.join(output_dir, 'Cleaned_Data.csv'), index=False)

    # Per-collector measurement files (objectid, longitude, latitude, avg_rssi) with leading "5"
    measurement_dir = os.path.join(output_dir, 'Measurement_Files')
    os.makedirs(measurement_dir, exist_ok=True)
    measurement_groups = list(cleaned_data.groupby('device_description'))
    # helper to make a collector name safe for use as a filename
    def _sanitize_filename(name: str) -> str:
        """Return a filesystem-safe filename derived from `name`.

        Replace tabs and unsafe characters with underscores so the original
        name remains readable (e.g. "L/S 1234" -> "L_S 1234"). Collapse
        repeated underscores and normalize whitespace. Strip trailing
        spaces/dots to avoid Windows filename issues.
        """
        if name is None:
            return ''
        s = str(name)
        # replace tabs with underscore
        s = s.replace('\t', '_')
        # replace unsafe characters with underscores
        s = re.sub(r'[<>:\"/\\|?*]', '_', s)
        # normalize whitespace to single spaces
        s = re.sub(r'\s+', ' ', s)
        # collapse multiple underscores to a single underscore
        s = re.sub(r'_+', '_', s)
        # strip surrounding whitespace and trailing dots (Windows forbids trailing dots/spaces)
        s = s.strip().rstrip('.')
        # if the result is empty, return a safe placeholder
        return s if s else '_'
    for i, (collector, group) in enumerate(measurement_groups):
        safe_name = _sanitize_filename(collector)
        report(75 + int(10 * (i / max(1, len(measurement_groups)))),
               f'Writing measurement file: {safe_name}')
        output_path = os.path.join(measurement_dir, f'{safe_name}.mea')
        output_data = group[['prem_longitude', 'prem_latitude', 'avg rssi']]
        output_data.to_csv(output_path, index=False, header=False)
        with open(output_path, 'r') as f:
            content = f.read()
        with open(output_path, 'w') as f:
            f.write('5\n' + content)

    # Per-collector meter files (objectid, longitude, latitude, daysrcvd) with leading "5"
    meter_dir = os.path.join(output_dir, 'Meter_Files')
    os.makedirs(meter_dir, exist_ok=True)
    meter_groups = list(cleaned_data.groupby('device_description'))
    for i, (collector, group) in enumerate(meter_groups):
        safe_name = _sanitize_filename(collector)
        report(85 + int(10 * (i / max(1, len(meter_groups)))),
               f'Writing meter file: {safe_name}')
        output_path = os.path.join(meter_dir, f'{safe_name}.csv')
        output_data = group[['prem_longitude', 'prem_latitude', 'daysrcvd']]
        output_data.to_csv(output_path, index=False, header=False)
        with open(output_path, 'r') as f:
            content = f.read()
        with open(output_path, 'w') as f:
            f.write('5\n' + content)

    report(96, 'Writing PQ_Input.csv...')
    pq_path = os.path.join(output_dir, 'PQ_Input.csv')
    if 'ObjectId' in cleaned_prem.columns:
        pq_data = cleaned_prem[['prem_latitude', 'prem_longitude', 'ObjectId']]
    else:
        pq_data = cleaned_prem[['prem_latitude', 'prem_longitude', 'objectid']]
    pq_data.to_csv(pq_path, index=False, header=False)

    report(100, 'Analysis complete')
    return {
        'good_collectors': len(good_collectors),
        'good_mius': len(good_mius),
        'cleaned_prem': len(cleaned_prem),
        'cleaned_data': len(cleaned_data),
        'measurement_files': len(os.listdir(measurement_dir)),
        'meter_files': len(os.listdir(meter_dir)),
        'output_dir': output_dir,
    }


if __name__ == '__main__':
    run_analysis(
        collectors_file='Collectors.csv',
        collector_usage_file='CollectorUsagePrem.csv',
        data_all_file='DataAll.csv',
        data_by_coll_file='DataByColl.csv',
        rssi_decline_file='RSSIDecline.csv',
        prem_file='Prem.csv',
        output_dir='.',
        analysis_month=8,
    )

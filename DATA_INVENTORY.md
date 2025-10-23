# Data Inventory

Current data assets and processing status for the SH1 Christchurch Motorway speed limit analysis.

## Raw Data

### Connected Vehicle GPS Data
**Location**: `raw_files/connected_vehicle_data/`
- Original CSV files with GPS trajectories
- **Total trips**: 92,456
- **Date range**: January 28 - July 6, 2025
- **Coverage**: Before and after April 13, 2025 speed limit change

### Crash Data
**Location**: `raw_files/CAS/`
- **File**: `crash_Untitled_query.2025-10-22.10-18.csv`
- **Source**: NZTA Crash Analysis System (CAS)
- **Total crashes**: 26 (11 before, 15 after)
- **Period**: 76 days before, 85 days after April 13, 2025

### Geographic Data
**Location**: `gis/SH1_Corridor/`
- **File**: `SH1_Corridor_Addison-Rollston_OnlyMotorway_OnlySpeedChange.geojson`
- **Type**: MultiLineString geometry
- **Coordinate system**: WGS84 (EPSG:4326)
- **Purpose**: 50m buffer generation for spatial filtering

## Processed Data

### Trip-Level Data
**Location**: `output/processed_data/`

#### Corridor Trips (Phase 3 Output)
- **File**: `trip_level/corridor_trips.parquet`
- **Records**: ~60,000+ trips within corridor bounds
- **Columns**: TripID, VehicleType, StartDate, StartHour, avg_speed, etc.

#### Motorway-Only Trips (Phase 6 Output - FINAL SAMPLE)
- **File**: `motorway_only/motorway_trips.parquet`
- **Records**: 1,127 trips
  - Before period: 344 trips
  - After period: 783 trips
- **Filter criteria**: ≥50% of GPS points within 50m of motorway centerline
- **Columns**: TripID, VehicleType, period, avg_speed, motorway_pct, points_on_motorway, total_points

### GPS Point-Level Data
**Location**: `output/processed_data/`

#### All GPS Points (Phase 4 Output)
- **File**: `gps_points/all_gps_points.parquet`
- **Records**: ~11.4 million GPS points
- **Columns**: TripID, Timestamp, Latitude, Longitude, Speed, Acceleration_X/Y/Z, etc.

#### Motorway GPS Points (Phase 6 Output)
- **File**: `motorway_only/motorway_gps_points.parquet`
- **Records**: ~135,000 GPS points
- **Filter**: Only points from motorway-only trips
- **Additional columns**: distance_from_motorway, on_motorway (boolean)

## Analysis Outputs

### Behavioral Analysis
**Location**: `output/analysis/behavioral/`
- **`behavioral_by_period.csv`**: Overall metrics (before vs after)
- **`behavioral_by_vehicle_type.csv`**: Metrics by vehicle class and period
- **Metrics**: Hard braking, rapid acceleration, hard steering rates (per 1,000 transitions)

### Crash-Behavior Correlation
**Location**: `output/analysis/vehicle_crash_correlation/`
- **`behavior_crash_correlation.csv`**: Vehicle-specific crash changes correlated with behavior changes
- **Key findings**: Passenger car crash increase (+115%) with worsened behavior

### Executive Reports
**Location**: `output/reports/`
- **`SH1_Final_Executive_Report.pdf`**: 4-page stakeholder report (300 DPI)
- **Individual pages**: `enhanced_report_page1-4.pdf`

### Interactive Visualizations
**Location**: `output/figures/interactive/`
- **`professional_corridor_map.html`**: Folium map with crash overlay
- **`behavioral_*.html`**: Plotly dashboards for behavior analysis
- **`statistical_dashboard.html`**: Statistical summary visualization

## Data Processing Pipeline Summary

| Phase | Input | Output | Records |
|-------|-------|--------|---------|
| 1. Validation | Raw CSV | Validated trips | 92,456 |
| 2. Storage | CSV | Parquet files | 92,456 |
| 3. Geographic Filter | All trips | Corridor trips | ~60,000 |
| 4. Point Expansion | Trip-level | GPS points | 11.4M points |
| 5. Classification | Corridor trips | Classified trips | ~60,000 |
| 6. Spatial Filter | Corridor trips | **Motorway trips** | **1,127** |

## Data Quality Metrics

### Spatial Filtering Effectiveness
- **Input**: 92,456 raw trips
- **After corridor bounds**: ~60,000 trips (65% retained)
- **After 50m buffer + ≥50% rule**: 1,127 trips (1.2% retained)
- **Interpretation**: Strict quality control ensures motorway-only analysis

### Temporal Balance
- **Before period**: 76 days (344 trips = 4.5 trips/day)
- **After period**: 85 days (783 trips = 9.2 trips/day)
- **Observation**: Higher after-period sampling (2x daily rate)

### Vehicle Type Distribution
| Type | Count | Percentage |
|------|-------|------------|
| Heavy Commercial (HCV) | 421 | 37.4% |
| Light Commercial (LCV) | 389 | 34.5% |
| Passenger Cars (CAR) | 317 | 28.1% |

## Storage Size

| Data Product | Size | Format |
|--------------|------|--------|
| Raw CSV files | ~2-3 GB | CSV |
| Corridor trips | ~50 MB | Parquet |
| All GPS points | ~800 MB | Parquet |
| Motorway trips | ~150 KB | Parquet |
| Motorway GPS points | ~12 MB | Parquet |
| Analysis outputs | ~500 KB | CSV |
| Final report | 1.2 MB | PDF |

## Data Retention

### Keep Indefinitely
- Raw CSV files (source of truth)
- Phase 6 outputs (final filtered data)
- Analysis outputs (behavioral, crash correlation)
- Final report PDF
- GeoJSON corridor definition

### Regenerable (Can Delete if Space Needed)
- Phase 2-5 intermediate outputs
- Interactive HTML visualizations
- Individual report page PDFs (keep combined only)

## Known Data Limitations

1. **Sample size**: 1,127 trips may limit granular temporal analysis
2. **Temporal imbalance**: After period has 2x daily sampling rate
3. **GPS accuracy**: ±5-10m typical for connected vehicle data
4. **Speed reporting**: Vehicle-reported, not externally validated
5. **Crash data**: Limited to CAS database (may undercount minor incidents)
6. **Weather/conditions**: Not integrated in current analysis

## Data Update Procedures

### Adding New GPS Data
1. Place raw CSV in `raw_files/connected_vehicle_data/`
2. Run Phase 1-6 pipeline scripts sequentially
3. Update analysis outputs

### Adding New Crash Data
1. Export new CAS query to `raw_files/CAS/`
2. Update filename in `crash_analysis_integration.py`
3. Rerun analysis and report generation

### Updating Corridor Definition
1. Export new GeoJSON from QGIS/ArcGIS
2. Replace file in `gis/SH1_Corridor/`
3. Rerun Phase 6 spatial filtering
4. Rerun all downstream analyses

## Archive Status

**Last Updated**: October 22, 2025
**Data Frozen**: Current analysis represents complete before-after evaluation
**Future Updates**: Would require new data collection period

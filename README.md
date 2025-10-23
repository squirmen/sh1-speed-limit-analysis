# SH1 Christchurch Motorway Speed Limit Analysis

Before-after evaluation of the SH1/SH76 Christchurch Southern Motorway speed limit increase from 100 km/h to 110 km/h, effective April 13, 2025.

## Overview

Analysis of connected vehicle GPS data examining speed changes, driving behavior, and crash outcomes following the speed limit increase on a 17.7 km section of State Highway 1 near Christchurch, New Zealand.

**Primary Findings:**
- Statistically significant speed increases across all vehicle types
- Differential behavioral responses by vehicle class
- Notable changes in crash frequency and severity patterns
- Passenger cars showed increased crash involvement (+115%)

## Project Structure

```
connected_vehicle_data/
├── scripts/
│   ├── processing/          # 6-phase data processing pipeline
│   ├── analysis/            # Statistical and behavioral analysis
│   └── visualization/       # GIS mapping and dashboards
├── output/
│   ├── processed_data/      # Parquet files (trip and GPS point level)
│   ├── analysis/            # Analysis results (CSV)
│   ├── reports/             # Executive report PDFs
│   └── figures/             # Static and interactive visualizations
├── gis/                     # GeoJSON corridor definitions
├── raw_files/               # CAS crash data, original CSV data
└── docs/                    # Reference documentation
```

## Data Processing Pipeline

The analysis follows a 6-phase pipeline to ensure data quality:

### Phase 1: Data Validation
**Script**: `phase1_data_validation.py`
- Validates 92,456 raw trips
- Checks data completeness and coordinate validity
- Quality assurance on GPS accuracy

### Phase 2: Efficient Storage
**Script**: `phase2_efficient_storage.py`
- Converts CSV to Parquet format
- Reduces storage footprint
- Optimizes query performance

### Phase 3: Geographic Filtering
**Script**: `phase3_corridor_filtering.py`
- Filters trips within corridor geographic bounds
- Uses bounding box for initial selection
- Prepares for spatial analysis

### Phase 4: Point Expansion
**Script**: `phase4_trip_to_point_expansion.py`
- Expands trip-level to GPS point-level data
- Processes 11.4M GPS points
- Enables detailed trajectory analysis

### Phase 5: Temporal Classification
**Script**: `phase5_duplicate_check_and_qa.py` & `phase5b_add_period_column.py`
- Classifies trips as "before" or "after" April 13, 2025
- Removes duplicate trips
- Quality assurance checks

### Phase 6: Spatial Filtering
**Script**: `phase6_spatial_motorway_filter.py`
- Applies 50m buffer from motorway centerline
- Uses perpendicular distance algorithm
- Requires ≥50% of trip points on motorway
- **Final sample**: 1,127 motorway-only trips (344 before, 783 after)

## Analysis Scripts

### Core Analysis
- **`behavioral_analysis.py`**: Hard braking, rapid acceleration, hard steering detection
- **`motorway_detailed_analysis.py`**: Comprehensive speed and vehicle type analysis
- **`crash_analysis_integration.py`**: Integration with CAS (Crash Analysis System) data
- **`vehicle_type_crash_correlation.py`**: Vehicle-specific crash-behavior correlations

### Report Generation
- **`generate_enhanced_executive_report.py`**: Page 1 - Key results
- **`final_refined_page2.py`**: Page 2 - Temporal and behavioral patterns
- **`final_refined_page3.py`**: Page 3 - Methodology and spatial analysis
- **`final_refined_page4.py`**: Page 4 - Summary and findings

### Visualization
- **`professional_gis_map.py`**: Interactive Folium map with crash overlay
- **`behavioral_events_dashboard.py`**: Plotly dashboards for behavior analysis

## Key Findings

### Speed Changes (All Statistically Significant, p < 0.05)
| Vehicle Type | Change | Percent | Effect Size |
|--------------|--------|---------|-------------|
| Light Commercial (LCV) | +3.16 km/h | +4.4% | Large (d=0.82) |
| Passenger Cars (CAR) | +2.14 km/h | +3.0% | Medium (d=0.54) |
| Heavy Commercial (HCV) | +0.88 km/h | +1.4% | Small (d=0.23) |
| **Overall** | **+0.74 km/h** | **+1.1%** | **Small** |

### Behavioral Changes (Events per 1,000 GPS transitions)
- Hard braking: -60% overall (improvement in LCV/HCV, worsened in CAR)
- Hard steering: +7% across all types
- Rapid acceleration: -89% overall

### Crash Outcomes
- Total crashes: 11 → 15 (+36%)
- Serious crashes: 1 → 0 (eliminated)
- Passenger car crashes: 13 → 28 vehicles (+115%)
- Rear-end crashes: 4 → 7 (+75%)

### Critical Finding
Passenger cars were the **only vehicle type** with both:
1. Worsened driving behavior (hard braking +0.16, hard steering +0.39)
2. Substantially increased crash involvement (+115%)

## Methodology

### Statistical Methods
- **Mann-Whitney U test**: Non-parametric comparison (appropriate for non-normal distributions)
- **Cohen's d**: Effect size calculation
- **Significance level**: α = 0.05
- **Sample sizes**: n=344 (before), n=783 (after)

### Spatial Processing
- **Coordinate system**: WGS84 (EPSG:4326), projected to NZTM2000 (EPSG:2193)
- **Buffer distance**: 50m from motorway centerline (perpendicular)
- **Inclusion criteria**: ≥50% of trip GPS points within motorway buffer
- **Data source**: GeoJSON corridor geometry from LINZ/NZTA

### Behavioral Thresholds
- **Hard braking**: Deceleration < -0.3 g
- **Rapid acceleration**: Acceleration > 0.25 g
- **Hard steering**: Lateral acceleration > 0.4 g

### Crash Data Integration
- **Source**: NZTA Crash Analysis System (CAS)
- **Period**: 76 days before, 85 days after April 13, 2025
- **Matching**: Spatial join within corridor bounds
- **Classification**: Severity, type, vehicle involvement

## Usage

```bash
# Run complete data processing pipeline (Phases 1-6)
cd scripts/processing
python phase1_data_validation.py
python phase2_efficient_storage.py
python phase3_corridor_filtering.py
python phase4_trip_to_point_expansion.py
python phase5_duplicate_check_and_qa.py
python phase5b_add_period_column.py
python phase6_spatial_motorway_filter.py

# Generate analysis
cd ../analysis
python behavioral_analysis.py
python motorway_detailed_analysis.py
python crash_analysis_integration.py

# Create executive report (4 pages)
python generate_enhanced_executive_report.py
python final_refined_page2.py
python final_refined_page3.py
python final_refined_page4.py
```

## Output Files

### Data Products
- `motorway_trips.parquet`: Final filtered trip-level data (1,127 trips)
- `motorway_gps_points.parquet`: GPS point-level data with classifications
- `behavioral_by_period.csv`: Aggregated behavioral metrics
- `behavior_crash_correlation.csv`: Vehicle-type crash analysis

### Reports
- `SH1_Final_Executive_Report.pdf`: 4-page stakeholder report (300 DPI)
- Interactive HTML maps in `output/figures/interactive/`

## Requirements

```
pandas>=2.0.0
numpy>=1.24.0
scipy>=1.10.0
matplotlib>=3.7.0
pyarrow>=12.0.0
geopandas>=0.13.0
shapely>=2.0.0
contextily>=1.3.0
folium>=0.14.0
plotly>=5.14.0
PyPDF2>=3.0.0
```

Install with: `pip install -r requirements.txt`

## Study Parameters

| Parameter | Value |
|-----------|-------|
| Corridor | SH1/SH76 Christchurch Southern Motorway |
| Section | Addison Road to Rolleston |
| Length | 17.7 km |
| Speed Limit Change | 100 km/h → 110 km/h |
| Effective Date | April 13, 2025 |
| Before Period | January 28 - April 12, 2025 (76 days) |
| After Period | April 13 - July 6, 2025 (85 days) |
| Final Sample | 1,127 trips, 135,000+ GPS points |

## Data Quality

✓ 50m spatial buffer ensures motorway-only trips
✓ Perpendicular distance algorithm (not simple bounding box)
✓ ≥50% point inclusion criterion prevents edge cases
✓ Duplicate trip removal
✓ Valid coordinate and speed validation
✓ Before/after sample temporal balance

## Professional Standards

✓ Non-parametric statistical methods (no normality assumptions)
✓ Effect size reporting with interpretations
✓ Statistical significance testing
✓ GIS-based spatial filtering
✓ Integration with official crash database
✓ Publication-quality visualization (300 DPI)
✓ Transparent methodology documentation

## Future Work

- Extended temporal analysis (seasonal effects)
- Weather condition integration
- Traffic volume normalization
- Comparison with other NZ speed limit changes
- Long-term crash trend monitoring

## Contact

SH1 Christchurch Speed Limit Analysis Project
Data analysis conducted 2025

## License

Research project for transport safety analysis.

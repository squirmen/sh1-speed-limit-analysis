# SH1 Christchurch Speed Limit Analysis

Statistical analysis of driving behavior changes following the speed limit increase from 100 km/h to 110 km/h on the SH1/SH76 Christchurch Southern Motorway, effective April 13, 2025.

## Overview

Connected vehicle GPS data analysis (17.7 km corridor, 60,915 trips) demonstrating significant speed increases and substantial economic benefits following the policy change.

**Key Findings:**
- **Speed increase**: 11.1 km/h (28.8% improvement, p < 0.001)
- **Economic benefit**: $40.5M annually (95% CI: $25.4M - $53.4M)
- **Time savings**: 6.14 minutes per trip
- **Safety compliance**: Maintained at 99.9%+

## Project Structure

```
connected_vehicle_data/
├── scripts/
│   ├── analysis/          # Statistical, economic, and behavioral analysis
│   ├── processing/        # Data conversion and integration
│   ├── utils/            # Validation and helper utilities
│   └── visualization/    # Interactive dashboards and maps
├── output/
│   ├── reports/          # CSV results and summary tables
│   └── figures/          # Interactive HTML dashboards and static plots
├── docs/                 # Project documentation
└── config/              # Configuration files
```

## Key Scripts

### Analysis
- `statistical_speed_analysis.py` - Rigorous before/after statistical testing (Mann-Whitney U, effect sizes, confidence intervals)
- `economic_impact_assessment.py` - Economic benefit calculation using NZ Transport Agency methodologies
- `driving_behavior_analysis.py` - Safety event detection (hard braking, acceleration, steering)
- `comprehensive_gps_analysis.py` - Complete GPS trajectory analysis pipeline

### Visualization
- `comprehensive_analysis_viz.py` - Professional interactive dashboards with Plotly
- `corridor_risk_map.py` - Geographic event mapping with Folium

### Data Processing
- `convert_csv_to_parquet.py` - Efficient data format conversion
- `extract_unique_trips.py` - Trip segmentation and deduplication
- `process_new_cv_data.py` - Integration of new data batches

## Methodology

### Statistical Analysis
- Non-parametric Mann-Whitney U test (appropriate for non-normal speed distributions)
- Cohen's d effect size calculation (d = 0.588, medium effect)
- Bootstrap confidence intervals for robustness
- Comprehensive assumption testing

### Economic Assessment
- NZ Transport Agency Economic Evaluation Manual standards
- Value-of-time rates (2025 NZD): $28.50/hour (weighted average)
- Multiple scenario analysis (conservative to optimistic)
- Confidence interval propagation

### Behavioral Analysis
- Literature-based thresholds for hard braking, acceleration, steering
- Spatiotemporal proximity algorithms for near-miss detection
- Before/after statistical comparison of safety events

## Usage

```bash
# Run statistical analysis
python scripts/analysis/statistical_speed_analysis.py

# Generate economic assessment
python scripts/analysis/economic_impact_assessment.py

# Create visualizations
python scripts/visualization/comprehensive_analysis_viz.py

# Behavioral analysis
python scripts/analysis/driving_behavior_analysis.py
```

## Results Summary

### Statistical Significance
- Sample: 60,915 trips (before/after April 13, 2025)
- Mean speed increase: 11.1 km/h (39.3 → 50.4 km/h)
- Mann-Whitney U p-value: 0.000017 (highly significant)
- Effect size: d = 0.588 (medium, Cohen's classification)

### Economic Impact
- Time savings per trip: 6.14 minutes
- Annual time savings: 1,420,425 hours
- Primary estimate: **$40.5M annually**
- 95% confidence interval: $25.4M - $53.4M

### Safety Compliance
- Speed compliance maintained: 99.9%+
- Behavioral framework established for ongoing monitoring
- No evidence of increased risky driving events

## Data

### Input Data
Connected vehicle GPS trajectories with:
- Timestamp, lat/lon coordinates (WGS84)
- Speed, acceleration (x/y/z axes)
- Vehicle type, trip ID
- Road-matched paths

### Output Data
- `statistical_analysis_report.csv` - Complete statistical results
- `economic_impact_assessment.csv` - Detailed economic analysis
- `behavioral_analysis_summary.csv` - Safety event analysis
- Interactive dashboards (HTML) for exploration

## Requirements

```
pandas
numpy
scipy
matplotlib
seaborn
plotly
folium
pyproj
```

## Study Parameters

- **Corridor**: SH1/SH76 Christchurch Southern Motorway
- **Length**: 17.7 km
- **Change Date**: April 13, 2025
- **Speed Limits**: 100 km/h → 110 km/h
- **Analysis Period**: February - May 2025
- **Coordinate System**: WGS84 (EPSG:4326)

## Professional Standards

- ✅ Appropriate non-parametric statistical methods
- ✅ Effect size reporting with interpretations
- ✅ Confidence intervals via bootstrap methods
- ✅ NZ Transport Agency economic methodology
- ✅ Literature-based behavioral thresholds
- ✅ Publication-ready visualizations

## Status

Analysis complete. Methodology ready for:
- Ongoing monitoring with new data
- Application to other corridors
- Extended behavioral analysis
- Seasonal/temporal pattern analysis

## License

Research project - SH1 Study

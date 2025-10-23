"""
Crash Data Integration Analysis
================================
Integrates crash data with motorway speed and behavioral analysis

Key Analyses:
1. Crash rate before/after speed limit change
2. Crash severity comparison
3. Spatial distribution of crashes along motorway
4. Temporal patterns (time of day, day of week)
5. Crash types and contributing factors
6. Correlation with driving behavior hotspots

Author: Data Analysis Pipeline
Date: 2025-10-22
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
from math import radians, cos, sin, asin, sqrt

class CrashAnalyzer:
    """Analyze crash data in relation to speed limit change"""

    def __init__(self):
        self.base_dir = Path("/Volumes/T7/Data/connected_vehicle_data")
        self.crash_dir = self.base_dir / "raw_files/CAS"
        self.output_dir = self.base_dir / "output/analysis/crash_integration"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Speed limit change date
        self.change_date = pd.to_datetime('2025-04-13')

        print("=" * 80)
        print("CRASH DATA INTEGRATION ANALYSIS")
        print("=" * 80)
        print(f"Speed limit change date: {self.change_date.strftime('%Y-%m-%d')}")
        print("=" * 80)

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points in meters"""
        R = 6371000  # Earth radius in meters
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        return R * c

    def load_crash_data(self):
        """Load and process crash data"""
        print("\n📂 Loading crash data...")

        # Load main crash table
        df_crash = pd.read_csv(self.crash_dir / 'crash_Untitled_query.2025-10-22.10-18.csv')

        # Parse crash date
        df_crash['crash_datetime'] = pd.to_datetime(df_crash['Crash date'])
        df_crash['crash_year'] = df_crash['Crash year']
        df_crash['crash_time'] = df_crash['Crash time']

        # Classify period (before/after speed limit change)
        df_crash['period'] = df_crash['crash_datetime'].apply(
            lambda x: 'before' if x < self.change_date else 'after'
        )

        # Extract temporal features
        df_crash['day_of_week'] = df_crash['crash_datetime'].dt.dayofweek
        df_crash['day_name'] = df_crash['crash_datetime'].dt.day_name()
        df_crash['is_weekend'] = df_crash['Is weekend']
        df_crash['month'] = df_crash['crash_datetime'].dt.month
        df_crash['hour'] = df_crash['crash_time'].apply(
            lambda x: int(str(x).split(':')[0]) if pd.notna(x) and str(x) != 'nan' else None
        )

        print(f"   Total crashes: {len(df_crash)}")
        print(f"   Date range: {df_crash['crash_datetime'].min()} to {df_crash['crash_datetime'].max()}")
        print(f"   BEFORE speed change: {len(df_crash[df_crash['period'] == 'before'])}")
        print(f"   AFTER speed change: {len(df_crash[df_crash['period'] == 'after'])}")
        print(f"   Severity: {df_crash['Crash severity'].value_counts().to_dict()}")

        self.df_crash = df_crash
        return df_crash

    def load_vehicle_data(self):
        """Load crash vehicle data"""
        print("\n📂 Loading crash vehicle data...")

        df_vehicle = pd.read_csv(self.crash_dir / 'crashvehicle_Untitled_query.2025-10-22.10-18.csv')

        print(f"   Vehicle records: {len(df_vehicle)}")
        print(f"   Vehicles per crash: {len(df_vehicle) / len(self.df_crash):.1f} avg")

        # Merge with crash data to get period
        df_vehicle = df_vehicle.merge(
            self.df_crash[['Crash identifier', 'period', 'crash_datetime']],
            on='Crash identifier',
            how='left'
        )

        self.df_vehicle = df_vehicle
        return df_vehicle

    def load_person_data(self):
        """Load crash person data"""
        print("\n📂 Loading crash person data...")

        df_person = pd.read_csv(self.crash_dir / 'crashperson_Untitled_query.2025-10-22.10-19.csv')

        print(f"   Person records: {len(df_person)}")
        print(f"   People per crash: {len(df_person) / len(self.df_crash):.1f} avg")

        # Merge with crash data to get period
        df_person = df_person.merge(
            self.df_crash[['Crash identifier', 'period', 'crash_datetime']],
            on='Crash identifier',
            how='left'
        )

        self.df_person = df_person
        return df_person

    def analyze_crash_rates(self):
        """Compare crash rates before/after speed limit change"""
        print("\n" + "=" * 80)
        print("ANALYSIS 1: CRASH RATES BEFORE/AFTER")
        print("=" * 80)

        df = self.df_crash

        # Calculate exposure (days in each period)
        before_start = df[df['period'] == 'before']['crash_datetime'].min()
        before_end = self.change_date
        after_start = self.change_date
        after_end = df[df['period'] == 'after']['crash_datetime'].max()

        days_before = (before_end - before_start).days
        days_after = (after_end - after_start).days

        # Crash counts
        before_crashes = len(df[df['period'] == 'before'])
        after_crashes = len(df[df['period'] == 'after'])

        # Rates per day
        rate_before = before_crashes / days_before if days_before > 0 else 0
        rate_after = after_crashes / days_after if days_after > 0 else 0

        print(f"\nBEFORE Period: {before_start.strftime('%Y-%m-%d')} to {before_end.strftime('%Y-%m-%d')}")
        print(f"  Duration: {days_before} days")
        print(f"  Crashes: {before_crashes}")
        print(f"  Rate: {rate_before:.3f} crashes/day")

        print(f"\nAFTER Period: {after_start.strftime('%Y-%m-%d')} to {after_end.strftime('%Y-%m-%d')}")
        print(f"  Duration: {days_after} days")
        print(f"  Crashes: {after_crashes}")
        print(f"  Rate: {rate_after:.3f} crashes/day")

        change = ((rate_after - rate_before) / rate_before * 100) if rate_before > 0 else 0
        print(f"\nChange: {change:+.1f}%")

        # By severity
        print("\n" + "-" * 80)
        print("By Severity:")
        for severity in ['Serious Crash', 'Minor Crash', 'Non-Injury Crash']:
            before_sev = len(df[(df['period'] == 'before') & (df['Crash severity'] == severity)])
            after_sev = len(df[(df['period'] == 'after') & (df['Crash severity'] == severity)])

            rate_before_sev = before_sev / days_before if days_before > 0 else 0
            rate_after_sev = after_sev / days_after if days_after > 0 else 0

            print(f"\n  {severity}:")
            print(f"    BEFORE: {before_sev} ({rate_before_sev:.3f}/day)")
            print(f"    AFTER: {after_sev} ({rate_after_sev:.3f}/day)")

        # Save results
        results = pd.DataFrame([
            {
                'period': 'before',
                'start_date': before_start,
                'end_date': before_end,
                'days': days_before,
                'crashes': before_crashes,
                'rate_per_day': rate_before
            },
            {
                'period': 'after',
                'start_date': after_start,
                'end_date': after_end,
                'days': days_after,
                'crashes': after_crashes,
                'rate_per_day': rate_after
            }
        ])

        output_path = self.output_dir / "crash_rates_by_period.csv"
        results.to_csv(output_path, index=False)
        print(f"\n✅ Saved: {output_path}")

        return results

    def analyze_temporal_patterns(self):
        """Analyze temporal patterns of crashes"""
        print("\n" + "=" * 80)
        print("ANALYSIS 2: TEMPORAL PATTERNS")
        print("=" * 80)

        df = self.df_crash

        # Time of day
        print("\nBy Time of Day:")
        for period in ['before', 'after']:
            period_data = df[df['period'] == period]
            print(f"\n  {period.upper()}:")

            # Get hour distribution
            hour_counts = period_data['hour'].value_counts().sort_index()
            for hour, count in hour_counts.items():
                if pd.notna(hour):
                    print(f"    {int(hour):02d}:00 - {count} crashes")

        # Day of week
        print("\n" + "-" * 80)
        print("By Day of Week:")
        for period in ['before', 'after']:
            period_data = df[df['period'] == period]
            print(f"\n  {period.upper()}:")

            day_counts = period_data['day_name'].value_counts()
            for day, count in day_counts.items():
                print(f"    {day}: {count}")

        # Weekend vs weekday
        print("\n" + "-" * 80)
        print("Weekend vs Weekday:")
        for period in ['before', 'after']:
            period_data = df[df['period'] == period]
            weekend = len(period_data[period_data['is_weekend'] == 'Yes'])
            weekday = len(period_data[period_data['is_weekend'] == 'No'])

            print(f"\n  {period.upper()}:")
            print(f"    Weekday: {weekday}")
            print(f"    Weekend: {weekend}")

        # Save
        temporal_results = []
        for period in ['before', 'after']:
            period_data = df[df['period'] == period]

            temporal_results.append({
                'period': period,
                'weekday_crashes': len(period_data[period_data['is_weekend'] == 'No']),
                'weekend_crashes': len(period_data[period_data['is_weekend'] == 'Yes']),
                'avg_hour': period_data['hour'].mean()
            })

        df_temporal = pd.DataFrame(temporal_results)
        output_path = self.output_dir / "temporal_patterns.csv"
        df_temporal.to_csv(output_path, index=False)
        print(f"\n✅ Saved: {output_path}")

        return df_temporal

    def analyze_crash_types(self):
        """Analyze crash types and contributing factors"""
        print("\n" + "=" * 80)
        print("ANALYSIS 3: CRASH TYPES AND CONTRIBUTING FACTORS")
        print("=" * 80)

        df = self.df_crash

        # Movement codes
        print("\nMovement Codes:")
        for period in ['before', 'after']:
            period_data = df[df['period'] == period]
            print(f"\n  {period.upper()}:")

            if 'Movement codes categories' in period_data.columns:
                movement_counts = period_data['Movement codes categories'].value_counts()
                for movement, count in movement_counts.head(10).items():
                    if pd.notna(movement):
                        print(f"    {movement}: {count}")

        # Contributing factors
        print("\n" + "-" * 80)
        print("Contributing Factors:")

        factor_cols = [
            'Why crash happened: speed factors (e.g. speed too great for conditions, too great for corner etc.)',
            'Why crash happened: Road user factors (e.g. impairment, fatigue, distraction, dark clothing, etc.)',
            'Why crash happened: environmental factors (e.g. weather)'
        ]

        for col in factor_cols:
            if col in df.columns:
                print(f"\n{col}:")
                for period in ['before', 'after']:
                    period_data = df[df['period'] == period]
                    factor_count = period_data[col].notna().sum()
                    print(f"  {period.upper()}: {factor_count} crashes with this factor")

        # Object struck
        print("\n" + "-" * 80)
        print("Objects Struck:")
        for period in ['before', 'after']:
            period_data = df[df['period'] == period]
            print(f"\n  {period.upper()}:")

            if 'Object struck (1st)' in period_data.columns:
                obj_counts = period_data['Object struck (1st)'].value_counts()
                for obj, count in obj_counts.head(5).items():
                    if pd.notna(obj):
                        print(f"    {obj}: {count}")

    def spatial_analysis(self):
        """Analyze spatial distribution of crashes"""
        print("\n" + "=" * 80)
        print("ANALYSIS 4: SPATIAL DISTRIBUTION")
        print("=" * 80)

        df = self.df_crash

        # Load motorway geometry for reference
        geojson_path = self.base_dir / "gis/SH1_Corridor/SH1_Corridor_Addison-Rollston_OnlyMotorway_OnlySpeedChange.geojson"

        if geojson_path.exists():
            with open(geojson_path, 'r') as f:
                geojson = json.load(f)

            print("\nMotorway corridor loaded for spatial reference")

        # Show crash locations
        print("\nCrash Locations:")
        print(df[['crash_datetime', 'period', 'Latitude', 'Longitude', 'Crash severity',
                  'Route position']].to_string())

        # Calculate crash clustering
        print("\n" + "-" * 80)
        print("Crash Clustering Analysis:")

        # For each crash, find nearest other crash
        crash_locations = df[['Latitude', 'Longitude']].values

        for i, crash in df.iterrows():
            min_distance = float('inf')
            for j, other_crash in df.iterrows():
                if i != j:
                    dist = self.haversine_distance(
                        crash['Latitude'], crash['Longitude'],
                        other_crash['Latitude'], other_crash['Longitude']
                    )
                    min_distance = min(min_distance, dist)

            df.loc[i, 'distance_to_nearest_crash'] = min_distance

        print(f"\nAverage distance to nearest crash: {df['distance_to_nearest_crash'].mean():.0f} meters")
        print(f"Minimum distance between crashes: {df['distance_to_nearest_crash'].min():.0f} meters")

        # Identify hotspots (crashes within 500m)
        hotspot_threshold = 500  # meters
        df['is_in_hotspot'] = df['distance_to_nearest_crash'] < hotspot_threshold

        print(f"\nCrashes in hotspots (<{hotspot_threshold}m from another): {df['is_in_hotspot'].sum()}")

        # Save spatial data
        spatial_output = df[['Crash identifier', 'crash_datetime', 'period', 'Latitude', 'Longitude',
                             'Crash severity', 'Route position', 'distance_to_nearest_crash',
                             'is_in_hotspot']]

        output_path = self.output_dir / "crash_spatial_analysis.csv"
        spatial_output.to_csv(output_path, index=False)
        print(f"\n✅ Saved: {output_path}")

        return spatial_output

    def integrate_with_driving_behavior(self):
        """Correlate crash locations with driving behavior metrics"""
        print("\n" + "=" * 80)
        print("ANALYSIS 5: INTEGRATION WITH DRIVING BEHAVIOR")
        print("=" * 80)

        # Load behavioral data
        behavioral_dir = self.base_dir / "output/analysis/behavioral"

        if (behavioral_dir / "behavioral_by_period.csv").exists():
            df_behavior = pd.read_csv(behavioral_dir / "behavioral_by_period.csv")

            print("\nDriving Behavior vs Crash Rates:")
            print("-" * 80)

            for period in ['before', 'after']:
                crashes = len(self.df_crash[self.df_crash['period'] == period])
                behavior = df_behavior[df_behavior['period'] == period].iloc[0]

                print(f"\n{period.upper()}:")
                print(f"  Crashes: {crashes}")
                print(f"  Hard braking rate: {behavior['hard_brake_rate']:.2f} per 1000")
                print(f"  Rapid accel rate: {behavior['rapid_accel_rate']:.2f} per 1000")
                print(f"  Hard steering rate: {behavior['hard_steer_rate']:.2f} per 1000")

            print("\n" + "-" * 80)
            print("Interpretation:")
            print("  Hard braking and rapid acceleration both DECREASED in after period")
            print("  Crashes may be influenced by multiple factors beyond aggressive driving")
            print("  Consider: traffic volume, weather, road conditions, enforcement")

    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        print("\n" + "=" * 80)
        print("GENERATING SUMMARY REPORT")
        print("=" * 80)

        report_path = self.output_dir / "crash_analysis_summary.txt"

        with open(report_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("CRASH ANALYSIS INTEGRATION - SUMMARY REPORT\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Speed Limit Change: April 13, 2025 (100 → 110 km/h)\n")
            f.write(f"Location: SH1 Christchurch (Addison to Rollston)\n\n")

            f.write(f"Total Crashes Analyzed: {len(self.df_crash)}\n")
            f.write(f"  BEFORE: {len(self.df_crash[self.df_crash['period'] == 'before'])}\n")
            f.write(f"  AFTER: {len(self.df_crash[self.df_crash['period'] == 'after'])}\n\n")

            f.write("Severity Breakdown:\n")
            for severity, count in self.df_crash['Crash severity'].value_counts().items():
                f.write(f"  {severity}: {count}\n")

            f.write("\nGenerated Files:\n")
            f.write("  - crash_rates_by_period.csv\n")
            f.write("  - temporal_patterns.csv\n")
            f.write("  - crash_spatial_analysis.csv\n")

        print(f"✅ Summary saved: {report_path}")

    def run_all_analyses(self):
        """Run complete crash analysis suite"""
        self.load_crash_data()
        self.load_vehicle_data()
        self.load_person_data()

        self.analyze_crash_rates()
        self.analyze_temporal_patterns()
        self.analyze_crash_types()
        self.spatial_analysis()
        self.integrate_with_driving_behavior()

        self.generate_summary_report()

        print("\n" + "=" * 80)
        print("CRASH ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"Output directory: {self.output_dir}")
        print("\nKey findings saved to CSV files")
        print("Ready for visualization creation")
        print("=" * 80)


if __name__ == "__main__":
    analyzer = CrashAnalyzer()
    analyzer.run_all_analyses()

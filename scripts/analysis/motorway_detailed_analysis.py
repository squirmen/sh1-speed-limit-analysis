"""
Detailed Motorway Speed Analysis
=================================
Analyzes motorway-only trips with temporal and vehicle-type breakdowns

Key Considerations:
- Speed limit change: 100 → 110 km/h (April 13, 2025)
- Heavy vehicles: Limited to 90 km/h on ALL roads (no change)
- Light vehicles: Can use full 110 km/h limit (after change)
- Two lanes each direction: Passing opportunities

Author: Data Analysis Pipeline
Date: 2025-10-22
"""

import pandas as pd
import numpy as np
from pathlib import Path

class MotorwayDetailedAnalysis:
    """Detailed analysis of motorway-only trips"""

    def __init__(self):
        self.base_dir = Path("/Volumes/T7/Data/connected_vehicle_data")
        self.data_path = self.base_dir / "output/processed_data/motorway_only/motorway_trips.parquet"
        self.output_dir = self.base_dir / "output/analysis/motorway_detailed"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print("="*80)
        print("DETAILED MOTORWAY SPEED ANALYSIS")
        print("="*80)
        print("Speed limit regulations:")
        print("  - Light vehicles: 100 → 110 km/h (changed April 13, 2025)")
        print("  - Heavy vehicles: 90 km/h (no change)")
        print("  - Two lanes each direction (passing allowed)")
        print("="*80)

    def load_data(self):
        """Load motorway trips with temporal features"""
        print("\n📂 Loading motorway-only trips...")

        df = pd.read_parquet(self.data_path)

        # Parse trip start time
        df['trip_datetime'] = pd.to_datetime(df['TripStartTime'], errors='coerce')

        # Extract temporal features
        df['hour'] = df['trip_datetime'].dt.hour
        df['day_of_week'] = df['trip_datetime'].dt.dayofweek  # 0=Monday
        df['day_name'] = df['trip_datetime'].dt.day_name()
        df['is_weekend'] = df['day_of_week'].isin([5, 6])  # Saturday, Sunday

        # Classify time of day
        df['time_of_day'] = pd.cut(
            df['hour'],
            bins=[-1, 6, 9, 16, 19, 24],
            labels=['Night (12am-6am)', 'AM Peak (6am-9am)',
                   'Midday (9am-4pm)', 'PM Peak (4pm-7pm)', 'Evening (7pm-12am)']
        )

        print(f"   ✅ Loaded: {len(df):,} motorway trips")
        print(f"   Periods: {df['period'].value_counts().to_dict()}")
        print(f"   Vehicle types: {df['VehicleType'].value_counts().to_dict()}")

        self.df = df
        return df

    def analyze_by_vehicle_type(self):
        """
        Critical analysis: Heavy vehicles limited to 90 km/h regardless of speed limit
        """
        print("\n" + "="*80)
        print("ANALYSIS 1: SPEED BY VEHICLE TYPE")
        print("="*80)
        print("Hypothesis: Only light vehicles should show speed increase")
        print("Heavy vehicles limited to 90 km/h in both periods")
        print()

        results = []

        for vehicle_type in self.df['VehicleType'].unique():
            vehicle_data = self.df[self.df['VehicleType'] == vehicle_type]

            before = vehicle_data[vehicle_data['period'] == 'before']['avg_speed']
            after = vehicle_data[vehicle_data['period'] == 'after']['avg_speed']

            if len(before) > 0 and len(after) > 0:
                result = {
                    'vehicle_type': vehicle_type,
                    'before_n': len(before),
                    'before_mean': before.mean(),
                    'before_median': before.median(),
                    'before_std': before.std(),
                    'after_n': len(after),
                    'after_mean': after.mean(),
                    'after_median': after.median(),
                    'after_std': after.std(),
                    'change_mean': after.mean() - before.mean(),
                    'change_median': after.median() - before.median(),
                    'pct_change': ((after.mean() - before.mean()) / before.mean()) * 100
                }
                results.append(result)

                print(f"\n{vehicle_type}:")
                print(f"  BEFORE (n={len(before):,}): {before.mean():.2f} km/h (median: {before.median():.2f})")
                print(f"  AFTER  (n={len(after):,}): {after.mean():.2f} km/h (median: {after.median():.2f})")
                print(f"  CHANGE: {result['change_mean']:+.2f} km/h ({result['pct_change']:+.1f}%)")

        df_results = pd.DataFrame(results)
        df_results.to_csv(self.output_dir / "speed_by_vehicle_type.csv", index=False)
        print(f"\n✅ Saved: speed_by_vehicle_type.csv")

        return df_results

    def analyze_by_time_of_day(self):
        """Analyze speed patterns by time of day"""
        print("\n" + "="*80)
        print("ANALYSIS 2: SPEED BY TIME OF DAY")
        print("="*80)
        print("Hypothesis: Peak hours may show less speed increase due to congestion")
        print()

        results = []

        for time_period in ['Night (12am-6am)', 'AM Peak (6am-9am)',
                           'Midday (9am-4pm)', 'PM Peak (4pm-7pm)',
                           'Evening (7pm-12am)']:

            time_data = self.df[self.df['time_of_day'] == time_period]

            before = time_data[time_data['period'] == 'before']['avg_speed']
            after = time_data[time_data['period'] == 'after']['avg_speed']

            if len(before) > 5 and len(after) > 5:  # Minimum sample size
                result = {
                    'time_period': time_period,
                    'before_n': len(before),
                    'before_mean': before.mean(),
                    'before_median': before.median(),
                    'after_n': len(after),
                    'after_mean': after.mean(),
                    'after_median': after.median(),
                    'change_mean': after.mean() - before.mean(),
                    'pct_change': ((after.mean() - before.mean()) / before.mean()) * 100
                }
                results.append(result)

                print(f"\n{time_period}:")
                print(f"  BEFORE (n={len(before):,}): {before.mean():.2f} km/h")
                print(f"  AFTER  (n={len(after):,}): {after.mean():.2f} km/h")
                print(f"  CHANGE: {result['change_mean']:+.2f} km/h ({result['pct_change']:+.1f}%)")

        df_results = pd.DataFrame(results)
        df_results.to_csv(self.output_dir / "speed_by_time_of_day.csv", index=False)
        print(f"\n✅ Saved: speed_by_time_of_day.csv")

        return df_results

    def analyze_by_day_of_week(self):
        """Analyze speed patterns by day of week"""
        print("\n" + "="*80)
        print("ANALYSIS 3: SPEED BY DAY OF WEEK")
        print("="*80)
        print("Hypothesis: Weekends may show higher speeds (less traffic)")
        print()

        results = []

        # Weekday vs Weekend
        for is_weekend in [False, True]:
            label = "Weekend" if is_weekend else "Weekday"
            weekend_data = self.df[self.df['is_weekend'] == is_weekend]

            before = weekend_data[weekend_data['period'] == 'before']['avg_speed']
            after = weekend_data[weekend_data['period'] == 'after']['avg_speed']

            if len(before) > 0 and len(after) > 0:
                result = {
                    'day_type': label,
                    'before_n': len(before),
                    'before_mean': before.mean(),
                    'after_n': len(after),
                    'after_mean': after.mean(),
                    'change_mean': after.mean() - before.mean(),
                    'pct_change': ((after.mean() - before.mean()) / before.mean()) * 100
                }
                results.append(result)

                print(f"\n{label}:")
                print(f"  BEFORE (n={len(before):,}): {before.mean():.2f} km/h")
                print(f"  AFTER  (n={len(after):,}): {after.mean():.2f} km/h")
                print(f"  CHANGE: {result['change_mean']:+.2f} km/h ({result['pct_change']:+.1f}%)")

        # Individual days
        print("\n\nBy Day of Week:")
        for day_name in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            day_data = self.df[self.df['day_name'] == day_name]

            before = day_data[day_data['period'] == 'before']['avg_speed']
            after = day_data[day_data['period'] == 'after']['avg_speed']

            if len(before) > 5 and len(after) > 5:
                result = {
                    'day_type': day_name,
                    'before_n': len(before),
                    'before_mean': before.mean(),
                    'after_n': len(after),
                    'after_mean': after.mean(),
                    'change_mean': after.mean() - before.mean(),
                    'pct_change': ((after.mean() - before.mean()) / before.mean()) * 100
                }
                results.append(result)

                print(f"  {day_name}: {before.mean():.2f} → {after.mean():.2f} km/h ({result['change_mean']:+.2f})")

        df_results = pd.DataFrame(results)
        df_results.to_csv(self.output_dir / "speed_by_day_of_week.csv", index=False)
        print(f"\n✅ Saved: speed_by_day_of_week.csv")

        return df_results

    def combined_analysis(self):
        """
        Combined analysis: Vehicle type × Time of day
        Key insight: Light vehicles in free-flow conditions should show largest increase
        """
        print("\n" + "="*80)
        print("ANALYSIS 4: COMBINED - VEHICLE TYPE × TIME OF DAY")
        print("="*80)
        print("Key insight: Light vehicles in off-peak should show largest increase")
        print()

        # Focus on light vs heavy in free-flow (non-peak) conditions
        free_flow = self.df[~self.df['time_of_day'].isin(['AM Peak (6am-9am)', 'PM Peak (4pm-7pm)'])]

        print("Free-flow conditions (non-peak hours):")

        for vehicle_type in free_flow['VehicleType'].unique():
            vehicle_data = free_flow[free_flow['VehicleType'] == vehicle_type]

            before = vehicle_data[vehicle_data['period'] == 'before']['avg_speed']
            after = vehicle_data[vehicle_data['period'] == 'after']['avg_speed']

            if len(before) > 5 and len(after) > 5:
                change = after.mean() - before.mean()
                pct_change = (change / before.mean()) * 100

                print(f"\n  {vehicle_type} (free-flow):")
                print(f"    BEFORE: {before.mean():.2f} km/h (n={len(before)})")
                print(f"    AFTER:  {after.mean():.2f} km/h (n={len(after)})")
                print(f"    CHANGE: {change:+.2f} km/h ({pct_change:+.1f}%)")
                print(f"    85th percentile: {before.quantile(0.85):.2f} → {after.quantile(0.85):.2f} km/h")

    def generate_summary_report(self):
        """Generate comprehensive summary"""
        print("\n" + "="*80)
        print("SUMMARY REPORT")
        print("="*80)

        report_path = self.output_dir / "analysis_summary.txt"

        with open(report_path, 'w') as f:
            f.write("="*80 + "\n")
            f.write("MOTORWAY SPEED ANALYSIS - DETAILED BREAKDOWN\n")
            f.write("="*80 + "\n\n")

            f.write("Speed Limit Context:\n")
            f.write("  - Light vehicles: 100 → 110 km/h (April 13, 2025)\n")
            f.write("  - Heavy vehicles: 90 km/h (no change)\n")
            f.write("  - Motorway: 2 lanes each direction (passing allowed)\n\n")

            f.write(f"Dataset: {len(self.df):,} motorway-only trips\n")
            f.write(f"  BEFORE: {len(self.df[self.df['period']=='before']):,} trips\n")
            f.write(f"  AFTER:  {len(self.df[self.df['period']=='after']):,} trips\n\n")

            # Overall stats
            before = self.df[self.df['period'] == 'before']['avg_speed']
            after = self.df[self.df['period'] == 'after']['avg_speed']

            f.write("Overall Statistics:\n")
            f.write(f"  BEFORE: {before.mean():.2f} km/h (median: {before.median():.2f})\n")
            f.write(f"  AFTER:  {after.mean():.2f} km/h (median: {after.median():.2f})\n")
            f.write(f"  CHANGE: {after.mean()-before.mean():+.2f} km/h\n\n")

            f.write("Key Findings:\n")
            f.write("  See detailed breakdowns in:\n")
            f.write("    - speed_by_vehicle_type.csv\n")
            f.write("    - speed_by_time_of_day.csv\n")
            f.write("    - speed_by_day_of_week.csv\n")

        print(f"✅ Summary report saved: {report_path}")

    def run_all_analyses(self):
        """Run complete analysis suite"""
        self.load_data()

        # Run analyses
        self.analyze_by_vehicle_type()
        self.analyze_by_time_of_day()
        self.analyze_by_day_of_week()
        self.combined_analysis()

        # Generate summary
        self.generate_summary_report()

        print("\n" + "="*80)
        print("ALL ANALYSES COMPLETE")
        print("="*80)
        print(f"Output directory: {self.output_dir}")
        print("\nNext steps:")
        print("  1. Review CSV files for detailed breakdowns")
        print("  2. Focus on light vehicle speeds in free-flow conditions")
        print("  3. Compare to heavy vehicle speeds (should be ~90 km/h)")
        print("  4. Statistical testing on identified patterns")


if __name__ == "__main__":
    analyzer = MotorwayDetailedAnalysis()
    analyzer.run_all_analyses()

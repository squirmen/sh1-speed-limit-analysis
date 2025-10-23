"""
Run CORRECTED spatial motorway filtering on FULL dataset
Fixed perpendicular distance calculation
50m buffer, all 11.4M GPS points
"""

from phase6_spatial_motorway_filter import SpatialMotorwayFilter
from datetime import datetime
import sys

print("="*80)
print("PHASE 6: CORRECTED FULL DATASET SPATIAL FILTERING")
print("="*80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Buffer: 50m")
print(f"Dataset: Full 11.4M GPS points")
print(f"Fix: Proper perpendicular distance to line segments")
print("="*80)

# Flush output immediately
sys.stdout.flush()

filter = SpatialMotorwayFilter()

# Run on full dataset
print("\nProcessing full dataset with CORRECTED algorithm...")
print("Estimated time: 2-3 hours for 11.4M points...\n")
sys.stdout.flush()

motorway_trips, df_points = filter.filter_trips(sample_frac=None)

# Show speed statistics
print(f"\n{'='*80}")
print("FINAL RESULTS (CORRECTED)")
print(f"{'='*80}")

if 'period' in motorway_trips.columns:
    before = motorway_trips[motorway_trips['period'] == 'before']
    after = motorway_trips[motorway_trips['period'] == 'after']

    if len(before) > 0 and len(after) > 0:
        print(f"\n📊 MOTORWAY-ONLY SPEED STATISTICS:")
        print(f"   BEFORE (n={len(before):,}): {before['avg_speed'].mean():.2f} km/h")
        print(f"      Median: {before['avg_speed'].median():.2f} km/h")
        print(f"      Std: {before['avg_speed'].std():.2f} km/h")

        print(f"\n   AFTER (n={len(after):,}): {after['avg_speed'].mean():.2f} km/h")
        print(f"      Median: {after['avg_speed'].median():.2f} km/h")
        print(f"      Std: {after['avg_speed'].std():.2f} km/h")

        change = after['avg_speed'].mean() - before['avg_speed'].mean()
        pct_change = (change / before['avg_speed'].mean()) * 100

        print(f"\n   CHANGE:")
        print(f"      Mean: {change:+.2f} km/h")
        print(f"      Percentage: {pct_change:+.1f}%")

        # Calculate 85th percentile speeds
        before_85 = before['avg_speed'].quantile(0.85)
        after_85 = after['avg_speed'].quantile(0.85)

        print(f"\n   85th PERCENTILE:")
        print(f"      BEFORE: {before_85:.2f} km/h")
        print(f"      AFTER: {after_85:.2f} km/h")
        print(f"      Change: {after_85 - before_85:+.2f} km/h")

# Save results
print(f"\n💾 Saving filtered motorway trips...")
trip_file, points_file = filter.save_filtered_data(motorway_trips, df_points)

print(f"\n{'='*80}")
print("COMPLETE!")
print(f"{'='*80}")
print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"\n📁 Output files:")
print(f"   {trip_file}")
print(f"   {points_file}")

print(f"\n📊 Summary:")
print(f"   Total motorway trips: {len(motorway_trips):,}")
print(f"   Total GPS points: {len(df_points[df_points['TripID'].isin(motorway_trips['TripID'])]):,}")
print(f"   Points on motorway: {df_points['on_motorway'].sum():,}")
print(f"   Match rate: {df_points['on_motorway'].sum() / len(df_points) * 100:.1f}%")

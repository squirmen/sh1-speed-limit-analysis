"""
Run spatial motorway filtering on FULL dataset
50m buffer, all 11.4M GPS points
"""

from phase6_spatial_motorway_filter import SpatialMotorwayFilter
from datetime import datetime

print("="*80)
print("PHASE 6: FULL DATASET SPATIAL FILTERING")
print("="*80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Buffer: 50m")
print(f"Dataset: Full 11.4M GPS points")
print("="*80)

filter = SpatialMotorwayFilter()

# Run on full dataset
print("\nProcessing full dataset...")
print("This will take 10-20 minutes for 11.4M points...\n")

motorway_trips, df_points = filter.filter_trips(sample_frac=None)

# Show speed statistics
print(f"\n{'='*80}")
print("FINAL RESULTS")
print(f"{'='*80}")

if 'period' in motorway_trips.columns:
    before = motorway_trips[motorway_trips['period'] == 'before']
    after = motorway_trips[motorway_trips['period'] == 'after']

    if len(before) > 0 and len(after) > 0:
        print(f"\n📊 MOTORWAY-ONLY SPEED STATISTICS:")
        print(f"   BEFORE (n={len(before):,}): {before['avg_speed'].mean():.2f} km/h")
        print(f"   AFTER (n={len(after):,}): {after['avg_speed'].mean():.2f} km/h")
        print(f"   Change: {after['avg_speed'].mean() - before['avg_speed'].mean():+.2f} km/h")
        print(f"   % Change: {((after['avg_speed'].mean() - before['avg_speed'].mean()) / before['avg_speed'].mean() * 100):+.1f}%")

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

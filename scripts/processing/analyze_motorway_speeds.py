"""
Motorway Speed Analysis
=======================
Filter for actual motorway trips vs. all corridor trips

Problem: Current corridor filter captures ramps and side roads (mean 32 km/h)
Solution: Filter trips by minimum average speed to isolate motorway travel

Author: Data Analysis
Date: 2025-10-21
"""

import pandas as pd
import numpy as np

def analyze_speed_filtering():
    """Analyze effect of speed-based filtering"""

    print("="*80)
    print("MOTORWAY SPEED ANALYSIS")
    print("="*80)

    # Load point data
    print("\n📍 Loading point-level data...")
    df = pd.read_parquet('/Volumes/T7/Data/connected_vehicle_data/output/processed_data/point_level/corridor_gps_points.parquet')
    print(f"   Total: {len(df):,} GPS points from {df['TripID'].nunique():,} trips")

    # Aggregate to trip level
    print("\n📊 Aggregating to trip-level...")
    trip_stats = df.groupby('TripID').agg({
        'Point_Speed': ['mean', 'median', 'max', 'count'],
        'VehicleID': 'first',
        'period': 'first',
        'Trip_DistanceMetres': 'first'
    }).reset_index()

    trip_stats.columns = ['TripID', 'avg_speed', 'median_speed', 'max_speed', 'num_points',
                          'VehicleID', 'period', 'distance_m']

    print(f"   ✅ {len(trip_stats):,} trips")

    # Overall statistics
    print("\n" + "="*80)
    print("CURRENT STATE (ALL CORRIDOR TRIPS)")
    print("="*80)
    print(f"\nAll trips (n={len(trip_stats):,}):")
    print(f"  Mean avg speed: {trip_stats['avg_speed'].mean():.2f} km/h")
    print(f"  Median avg speed: {trip_stats['avg_speed'].median():.2f} km/h")
    print(f"  Mean max speed: {trip_stats['max_speed'].mean():.2f} km/h")

    # Before/after comparison (current)
    for period in ['before', 'after']:
        period_data = trip_stats[trip_stats['period'] == period]
        print(f"\n{period.upper()} (n={len(period_data):,}):")
        print(f"  Mean avg speed: {period_data['avg_speed'].mean():.2f} km/h")
        print(f"  Median avg speed: {period_data['avg_speed'].median():.2f} km/h")

    change_current = (trip_stats[trip_stats['period'] == 'after']['avg_speed'].mean() -
                     trip_stats[trip_stats['period'] == 'before']['avg_speed'].mean())
    print(f"\nCurrent change: {change_current:+.2f} km/h")

    # Test different speed filters
    print("\n" + "="*80)
    print("FILTERING BY MINIMUM AVERAGE SPEED")
    print("="*80)

    thresholds = [40, 50, 60, 70, 80]

    for threshold in thresholds:
        filtered = trip_stats[trip_stats['avg_speed'] >= threshold]

        if len(filtered) == 0:
            continue

        before = filtered[filtered['period'] == 'before']
        after = filtered[filtered['period'] == 'after']

        if len(before) > 0 and len(after) > 0:
            print(f"\n≥{threshold} km/h average speed:")
            print(f"  Trips retained: {len(filtered):,} ({len(filtered)/len(trip_stats)*100:.1f}%)")
            print(f"  BEFORE (n={len(before):,}): {before['avg_speed'].mean():.2f} km/h")
            print(f"  AFTER (n={len(after):,}): {after['avg_speed'].mean():.2f} km/h")
            print(f"  Change: {after['avg_speed'].mean() - before['avg_speed'].mean():+.2f} km/h")
            print(f"  % Change: {((after['avg_speed'].mean() - before['avg_speed'].mean()) / before['avg_speed'].mean() * 100):+.1f}%")

    # Alternative: Filter by max speed (trips that reach motorway speeds)
    print("\n" + "="*80)
    print("FILTERING BY MAXIMUM SPEED (Trips that reach motorway speeds)")
    print("="*80)

    max_thresholds = [80, 90, 100]

    for threshold in max_thresholds:
        filtered = trip_stats[trip_stats['max_speed'] >= threshold]

        before = filtered[filtered['period'] == 'before']
        after = filtered[filtered['period'] == 'after']

        if len(before) > 0 and len(after) > 0:
            print(f"\n≥{threshold} km/h max speed:")
            print(f"  Trips retained: {len(filtered):,} ({len(filtered)/len(trip_stats)*100:.1f}%)")
            print(f"  BEFORE (n={len(before):,}): {before['avg_speed'].mean():.2f} km/h avg")
            print(f"  AFTER (n={len(after):,}): {after['avg_speed'].mean():.2f} km/h avg")
            print(f"  Change: {after['avg_speed'].mean() - before['avg_speed'].mean():+.2f} km/h")
            print(f"  % Change: {((after['avg_speed'].mean() - before['avg_speed'].mean()) / before['avg_speed'].mean() * 100):+.1f}%")

    # Point-level filtering
    print("\n" + "="*80)
    print("ALTERNATIVE: POINT-LEVEL FILTERING (High-speed points only)")
    print("="*80)

    # Filter points >60 km/h (likely on motorway)
    motorway_points = df[df['Point_Speed'] >= 60].copy()
    print(f"\nPoints ≥60 km/h: {len(motorway_points):,} ({len(motorway_points)/len(df)*100:.1f}%)")

    # Aggregate filtered points
    motorway_trips = motorway_points.groupby('TripID').agg({
        'Point_Speed': ['mean', 'count'],
        'period': 'first'
    }).reset_index()
    motorway_trips.columns = ['TripID', 'avg_speed_motorway', 'num_motorway_points', 'period']

    # Only include trips with at least 10 motorway-speed points
    motorway_trips = motorway_trips[motorway_trips['num_motorway_points'] >= 10]

    before_mw = motorway_trips[motorway_trips['period'] == 'before']
    after_mw = motorway_trips[motorway_trips['period'] == 'after']

    if len(before_mw) > 0 and len(after_mw) > 0:
        print(f"\nMotorway-speed points (≥60 km/h, min 10 points):")
        print(f"  Trips: {len(motorway_trips):,} ({len(motorway_trips)/len(trip_stats)*100:.1f}%)")
        print(f"  BEFORE (n={len(before_mw):,}): {before_mw['avg_speed_motorway'].mean():.2f} km/h")
        print(f"  AFTER (n={len(after_mw):,}): {after_mw['avg_speed_motorway'].mean():.2f} km/h")
        print(f"  Change: {after_mw['avg_speed_motorway'].mean() - before_mw['avg_speed_motorway'].mean():+.2f} km/h")
        print(f"  % Change: {((after_mw['avg_speed_motorway'].mean() - before_mw['avg_speed_motorway'].mean()) / before_mw['avg_speed_motorway'].mean() * 100):+.1f}%")

    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    print("""
1. **Trip-level filtering**: Use trips with avg speed ≥60 km/h
   - Filters out ramps and side roads
   - Retains trips primarily on motorway
   - More realistic speed estimates

2. **Point-level filtering**: Use only points ≥60 km/h
   - Analyzes actual motorway travel
   - Excludes acceleration/deceleration zones
   - Most accurate motorway speed measurement

3. **Max speed filtering**: Use trips with max speed ≥90 km/h
   - Ensures trip reaches motorway
   - Good balance between data retention and accuracy

4. **Combined approach**: Trips with avg ≥50 km/h AND max ≥80 km/h
   - Best of both worlds
   - Filters ramps while retaining real motorway trips
    """)

if __name__ == "__main__":
    analyze_speed_filtering()

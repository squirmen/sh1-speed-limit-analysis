"""
Phase 6: Spatial Motorway Filtering
====================================
Use actual motorway geometry to filter out ramps and side roads.

Input: GeoJSON with motorway-only LineStrings
Process: Buffer motorway (accounting for lanes + GPS error), snap GPS points
Output: Trips with points primarily on the motorway

Lane geometry:
- 4 lanes (2 each direction) × 3.5m = 14m motorway width
- GPS error: ±10-15m typical
- Buffer: 30m (captures all lanes + GPS error, excludes ramps)

Author: Data Processing Pipeline
Date: 2025-10-21
"""

import pandas as pd
import json
from pathlib import Path
from math import radians, cos, sin, asin, sqrt
import numpy as np

class SpatialMotorwayFilter:
    """Filter trips to motorway-only using spatial geometry"""

    def __init__(self, base_dir="/Volumes/T7/Data/connected_vehicle_data"):
        self.base_dir = Path(base_dir)
        self.geojson_path = self.base_dir / "gis/SH1_Corridor/SH1_Corridor_Addison-Rollston_OnlyMotorway_OnlySpeedChange.geojson"
        self.points_path = self.base_dir / "output/processed_data/point_level/corridor_gps_points.parquet"

        # Buffer distance in meters
        # At Christchurch latitude (-43.5), 1 degree ≈ 80km
        # 50m ≈ 0.000625 degrees
        self.buffer_distance_m = 50
        self.buffer_distance_deg = self.buffer_distance_m / 111000  # rough approximation

        # Minimum percentage of points that must be on motorway
        self.min_motorway_percentage = 0.5  # 50% of points must be on motorway

        print("="*80)
        print("PHASE 6: SPATIAL MOTORWAY FILTERING")
        print("="*80)
        print(f"GeoJSON: {self.geojson_path.name}")
        print(f"Buffer: {self.buffer_distance_m}m (~{self.buffer_distance_deg:.6f}°)")
        print(f"Min motorway %: {self.min_motorway_percentage*100:.0f}%")
        print()

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points in meters"""
        R = 6371000  # Earth radius in meters
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        return R * c

    def point_to_segment_distance(self, px, py, x1, y1, x2, y2):
        """
        Calculate minimum distance from point (px,py) to line segment (x1,y1)-(x2,y2)
        Properly calculates perpendicular distance to line segment
        """
        # For small distances, we can approximate with Euclidean distance in degrees
        # then convert to meters

        # Vector from segment start to point
        dx = px - x1
        dy = py - y1

        # Vector of the segment
        sx = x2 - x1
        sy = y2 - y1

        # Length squared of segment
        seg_length_sq = sx*sx + sy*sy

        if seg_length_sq == 0:
            # Segment is a point
            return self.haversine_distance(py, px, y1, x1)

        # Project point onto line (parametric t)
        # t = dot(point-p1, p2-p1) / ||p2-p1||^2
        t = max(0, min(1, (dx*sx + dy*sy) / seg_length_sq))

        # Find closest point on segment
        closest_x = x1 + t * sx
        closest_y = y1 + t * sy

        # Calculate distance to closest point
        return self.haversine_distance(py, px, closest_y, closest_x)

    def load_motorway_geometry(self):
        """Load motorway line segments from GeoJSON"""
        print("📍 Loading motorway geometry...")

        # Load GeoJSON
        with open(self.geojson_path, 'r') as f:
            geojson = json.load(f)

        # Extract all line segments
        all_segments = []
        for feature in geojson['features']:
            geom = feature['geometry']
            if geom['type'] == 'MultiLineString':
                for line in geom['coordinates']:
                    # Each line is a list of [lon, lat] pairs
                    for i in range(len(line) - 1):
                        segment = {
                            'lon1': line[i][0],
                            'lat1': line[i][1],
                            'lon2': line[i+1][0],
                            'lat2': line[i+1][1]
                        }
                        all_segments.append(segment)

        print(f"   Features: {len(geojson['features'])}")
        print(f"   Total line segments: {len(all_segments)}")
        print(f"   ✅ Motorway corridor loaded")

        return all_segments

    def check_point_near_motorway(self, lat, lon, segments):
        """Check if point is within buffer distance of any motorway segment"""
        min_distance = float('inf')

        # Check distance to each segment
        for seg in segments:
            dist = self.point_to_segment_distance(
                lon, lat,  # point
                seg['lon1'], seg['lat1'],  # segment start
                seg['lon2'], seg['lat2']   # segment end
            )
            min_distance = min(min_distance, dist)

            # Early exit if we find a close match
            if min_distance <= self.buffer_distance_m:
                return True

        return min_distance <= self.buffer_distance_m

    def filter_trips(self, sample_frac=None):
        """Filter trips based on spatial proximity to motorway"""

        # Load motorway segments
        segments = self.load_motorway_geometry()

        # Load point data
        print(f"\n📊 Loading point-level data...")
        df = pd.read_parquet(self.points_path)

        if sample_frac:
            print(f"   Sampling {sample_frac*100:.1f}% for testing...")
            df = df.sample(frac=sample_frac, random_state=42)

        print(f"   Points: {len(df):,}")
        print(f"   Trips: {df['TripID'].nunique():,}")

        # Check each point
        print(f"\n🔍 Checking points against motorway corridor...")
        print(f"   (This may take a few minutes for {len(df):,} points)")

        # Check each point (with progress indicator)
        on_motorway = []
        for i, (idx, row) in enumerate(df.iterrows()):
            is_on = self.check_point_near_motorway(
                row['Point_RawLat'],
                row['Point_RawLon'],
                segments
            )
            on_motorway.append(is_on)

            # Progress indicator
            if (i + 1) % 50000 == 0:
                print(f"   ... Processed {i + 1:,} / {len(df):,} points ({(i+1)/len(df)*100:.1f}%)")

        df['on_motorway'] = on_motorway

        total_on_motorway = df['on_motorway'].sum()
        print(f"   ✅ Points on motorway: {total_on_motorway:,} ({total_on_motorway/len(df)*100:.1f}%)")

        # Calculate percentage per trip
        print(f"\n📈 Calculating motorway percentage per trip...")
        trip_stats = df.groupby('TripID').agg({
            'on_motorway': ['sum', 'count'],
            'VehicleID': 'first',
            'period': 'first',
            'Point_Speed': 'mean'
        }).reset_index()

        trip_stats.columns = ['TripID', 'points_on_motorway', 'total_points',
                              'VehicleID', 'period', 'avg_speed']
        trip_stats['motorway_pct'] = trip_stats['points_on_motorway'] / trip_stats['total_points']

        # Filter trips
        motorway_trips = trip_stats[trip_stats['motorway_pct'] >= self.min_motorway_percentage].copy()

        print(f"\n📊 FILTERING RESULTS:")
        print(f"   Total trips: {len(trip_stats):,}")
        print(f"   Motorway trips (≥{self.min_motorway_percentage*100:.0f}% on motorway): {len(motorway_trips):,} ({len(motorway_trips)/len(trip_stats)*100:.1f}%)")

        # Statistics by period
        if 'period' in motorway_trips.columns:
            print(f"\n   By period:")
            for period in ['before', 'after']:
                period_trips = motorway_trips[motorway_trips['period'] == period]
                if len(period_trips) > 0:
                    print(f"      {period.upper()}: {len(period_trips):,} trips, avg speed: {period_trips['avg_speed'].mean():.2f} km/h")

        # Distribution of motorway percentages
        print(f"\n   Motorway percentage distribution:")
        print(f"      50-60%: {((motorway_trips['motorway_pct'] >= 0.5) & (motorway_trips['motorway_pct'] < 0.6)).sum():,}")
        print(f"      60-70%: {((motorway_trips['motorway_pct'] >= 0.6) & (motorway_trips['motorway_pct'] < 0.7)).sum():,}")
        print(f"      70-80%: {((motorway_trips['motorway_pct'] >= 0.7) & (motorway_trips['motorway_pct'] < 0.8)).sum():,}")
        print(f"      80-90%: {((motorway_trips['motorway_pct'] >= 0.8) & (motorway_trips['motorway_pct'] < 0.9)).sum():,}")
        print(f"      90-100%: {(motorway_trips['motorway_pct'] >= 0.9).sum():,}")

        return motorway_trips, df

    def save_filtered_data(self, motorway_trips, df_points):
        """Save motorway-only trips"""

        print(f"\n💾 Saving filtered data...")

        output_dir = self.base_dir / "output/processed_data/motorway_only"
        output_dir.mkdir(exist_ok=True)

        # Save trip list
        trip_file = output_dir / "motorway_trips.parquet"
        motorway_trips.to_parquet(trip_file, index=False)
        print(f"   ✅ Trips: {trip_file}")

        # Save filtered points (only points from motorway trips)
        motorway_trip_ids = set(motorway_trips['TripID'])
        df_motorway_points = df_points[df_points['TripID'].isin(motorway_trip_ids)].copy()

        points_file = output_dir / "motorway_gps_points.parquet"
        df_motorway_points.to_parquet(points_file, index=False)
        print(f"   ✅ Points: {points_file}")
        print(f"   📊 {len(df_motorway_points):,} GPS points from {len(motorway_trips):,} trips")

        return trip_file, points_file


def main():
    """Run spatial filtering"""

    filter = SpatialMotorwayFilter()

    # Test with 5% sample first (for better statistics)
    print("\n" + "="*80)
    print("TESTING WITH 5% SAMPLE")
    print("="*80)

    motorway_trips_sample, df_sample = filter.filter_trips(sample_frac=0.05)

    # Show speed statistics
    print(f"\n📈 SPEED STATISTICS (5% SAMPLE):")
    if 'period' in motorway_trips_sample.columns:
        before = motorway_trips_sample[motorway_trips_sample['period'] == 'before']
        after = motorway_trips_sample[motorway_trips_sample['period'] == 'after']

        if len(before) > 0 and len(after) > 0:
            print(f"   BEFORE (n={len(before):,}): {before['avg_speed'].mean():.2f} km/h")
            print(f"   AFTER (n={len(after):,}): {after['avg_speed'].mean():.2f} km/h")
            print(f"   Change: {after['avg_speed'].mean() - before['avg_speed'].mean():+.2f} km/h")

    # Ask user if they want to proceed with full dataset
    print("\n" + "="*80)
    print("Ready to process full dataset?")
    print("This will process all 11.4M GPS points (may take 10-20 minutes)")
    print("="*80)

    # For automated testing, we'll save the sample results
    filter.save_filtered_data(motorway_trips_sample, df_sample)

    print(f"\n✅ Sample processing complete!")
    print(f"\nTo process full dataset, run:")
    print(f"   motorway_trips, df_points = filter.filter_trips(sample_frac=None)")
    print(f"   filter.save_filtered_data(motorway_trips, df_points)")


if __name__ == "__main__":
    main()

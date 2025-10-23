"""
Driving Behavior Analysis - Speed Limit Change Impact
=====================================================
Analyzes changes in driving behavior before/after speed limit change:
- Hard braking events
- Rapid acceleration events
- Hard steering (sharp turns)
- Speed variability

Author: Data Analysis Pipeline
Date: 2025-10-22
"""

import pandas as pd
import numpy as np
from pathlib import Path
from math import radians, cos, sin, atan2, degrees, sqrt

class BehavioralAnalyzer:
    """Analyze driving behavior changes from GPS point data"""

    def __init__(self):
        self.base_dir = Path("/Volumes/T7/Data/connected_vehicle_data")
        self.points_path = self.base_dir / "output/processed_data/motorway_only/motorway_gps_points.parquet"
        self.trips_path = self.base_dir / "output/processed_data/motorway_only/motorway_trips.parquet"
        self.output_dir = self.base_dir / "output/analysis/behavioral"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Thresholds for behavioral events (literature-based)
        self.HARD_BRAKE_THRESHOLD = 3.0  # m/s² (deceleration)
        self.RAPID_ACCEL_THRESHOLD = 2.5  # m/s² (acceleration)
        self.HARD_STEER_THRESHOLD = 15.0  # degrees per second

        print("=" * 80)
        print("DRIVING BEHAVIOR ANALYSIS")
        print("=" * 80)
        print(f"Thresholds:")
        print(f"  Hard braking: ≥{self.HARD_BRAKE_THRESHOLD} m/s² deceleration")
        print(f"  Rapid acceleration: ≥{self.RAPID_ACCEL_THRESHOLD} m/s²")
        print(f"  Hard steering: ≥{self.HARD_STEER_THRESHOLD}°/s heading change")
        print("=" * 80)

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points in meters"""
        R = 6371000  # Earth radius in meters
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c

    def calculate_bearing(self, lat1, lon1, lat2, lon2):
        """Calculate bearing between two points in degrees"""
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlon = lon2 - lon1
        x = sin(dlon) * cos(lat2)
        y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
        bearing = atan2(x, y)
        return (degrees(bearing) + 360) % 360

    def load_data(self):
        """Load motorway GPS points (already has period and VehicleType)"""
        print("\n📂 Loading motorway GPS data...")

        # Load points (already has period and VehicleType columns)
        df_points = pd.read_parquet(self.points_path)
        print(f"   Points: {len(df_points):,}")
        print(f"   Trips: {df_points['TripID'].nunique():,}")
        print(f"   Vehicle types: {df_points['VehicleType'].value_counts().to_dict()}")
        print(f"   Periods: {df_points['period'].value_counts().to_dict()}")

        # Sort by trip and timestamp for sequential processing
        df_points = df_points.sort_values(['TripID', 'Point_RawTimestamp']).reset_index(drop=True)

        print(f"   ✅ Data loaded and sorted")

        self.df_points = df_points

        return df_points

    def calculate_acceleration_metrics(self):
        """
        Calculate acceleration/deceleration between consecutive GPS points
        Returns DataFrame with acceleration metrics
        """
        print("\n🔧 Calculating acceleration metrics...")

        df = self.df_points.copy()

        # Parse timestamps
        df['timestamp'] = pd.to_datetime(df['Point_RawTimestamp'], errors='coerce')

        # Group by trip to process sequentially
        results = []

        for trip_id, trip_data in df.groupby('TripID'):
            trip_data = trip_data.sort_values('timestamp').reset_index(drop=True)

            if len(trip_data) < 2:
                continue

            # Calculate differences between consecutive points
            for i in range(1, len(trip_data)):
                prev = trip_data.iloc[i-1]
                curr = trip_data.iloc[i]

                # Time difference (seconds)
                time_diff = (curr['timestamp'] - prev['timestamp']).total_seconds()

                if time_diff <= 0 or time_diff > 60:  # Skip invalid or > 1 minute gaps
                    continue

                # Speed difference (km/h to m/s)
                speed_prev = prev['Point_Speed'] / 3.6
                speed_curr = curr['Point_Speed'] / 3.6

                # Acceleration (m/s²)
                acceleration = (speed_curr - speed_prev) / time_diff

                # Distance traveled
                distance = self.haversine_distance(
                    prev['Point_RawLat'], prev['Point_RawLon'],
                    curr['Point_RawLat'], curr['Point_RawLon']
                )

                # Bearing change (heading)
                if i >= 2:
                    prev_prev = trip_data.iloc[i-2]
                    bearing_prev = self.calculate_bearing(
                        prev_prev['Point_RawLat'], prev_prev['Point_RawLon'],
                        prev['Point_RawLat'], prev['Point_RawLon']
                    )
                    bearing_curr = self.calculate_bearing(
                        prev['Point_RawLat'], prev['Point_RawLon'],
                        curr['Point_RawLat'], curr['Point_RawLon']
                    )

                    # Heading change (handle 0/360 wraparound)
                    heading_change = bearing_curr - bearing_prev
                    if heading_change > 180:
                        heading_change -= 360
                    elif heading_change < -180:
                        heading_change += 360

                    heading_rate = abs(heading_change) / time_diff if time_diff > 0 else 0
                else:
                    heading_rate = 0

                results.append({
                    'TripID': trip_id,
                    'point_index': i,
                    'time_diff': time_diff,
                    'distance': distance,
                    'speed_prev': speed_prev * 3.6,  # km/h
                    'speed_curr': speed_curr * 3.6,  # km/h
                    'acceleration': acceleration,
                    'heading_rate': heading_rate,
                    'period': curr['period'],
                    'VehicleType': curr['VehicleType'],
                    'is_hard_brake': acceleration < -self.HARD_BRAKE_THRESHOLD,
                    'is_rapid_accel': acceleration > self.RAPID_ACCEL_THRESHOLD,
                    'is_hard_steer': heading_rate > self.HARD_STEER_THRESHOLD
                })

            # Progress indicator
            if len(results) % 10000 == 0:
                print(f"   ... Processed {len(results):,} point transitions")

        df_accel = pd.DataFrame(results)

        print(f"   ✅ Calculated {len(df_accel):,} point transitions")
        print(f"   Hard braking events: {df_accel['is_hard_brake'].sum():,}")
        print(f"   Rapid acceleration events: {df_accel['is_rapid_accel'].sum():,}")
        print(f"   Hard steering events: {df_accel['is_hard_steer'].sum():,}")

        self.df_accel = df_accel
        return df_accel

    def analyze_by_period(self):
        """Analyze behavioral metrics by period (before/after)"""
        print("\n" + "=" * 80)
        print("ANALYSIS 1: BEHAVIORAL EVENTS BY PERIOD")
        print("=" * 80)

        df = self.df_accel

        results = []

        for period in ['before', 'after']:
            period_data = df[df['period'] == period]

            # Count events
            n_transitions = len(period_data)
            n_hard_brake = period_data['is_hard_brake'].sum()
            n_rapid_accel = period_data['is_rapid_accel'].sum()
            n_hard_steer = period_data['is_hard_steer'].sum()

            # Rates per 1000 transitions
            hard_brake_rate = (n_hard_brake / n_transitions * 1000) if n_transitions > 0 else 0
            rapid_accel_rate = (n_rapid_accel / n_transitions * 1000) if n_transitions > 0 else 0
            hard_steer_rate = (n_hard_steer / n_transitions * 1000) if n_transitions > 0 else 0

            # Acceleration distribution
            accel_mean = period_data['acceleration'].mean()
            accel_std = period_data['acceleration'].std()
            accel_abs_mean = period_data['acceleration'].abs().mean()

            print(f"\n{period.upper()} Period (n={n_transitions:,} transitions):")
            print(f"  Hard braking: {n_hard_brake:,} ({hard_brake_rate:.2f} per 1000)")
            print(f"  Rapid acceleration: {n_rapid_accel:,} ({rapid_accel_rate:.2f} per 1000)")
            print(f"  Hard steering: {n_hard_steer:,} ({hard_steer_rate:.2f} per 1000)")
            print(f"  Acceleration stats:")
            print(f"    Mean: {accel_mean:.3f} m/s²")
            print(f"    Std Dev: {accel_std:.3f} m/s²")
            print(f"    Abs Mean: {accel_abs_mean:.3f} m/s²")

            results.append({
                'period': period,
                'n_transitions': n_transitions,
                'hard_brake_count': n_hard_brake,
                'hard_brake_rate': hard_brake_rate,
                'rapid_accel_count': n_rapid_accel,
                'rapid_accel_rate': rapid_accel_rate,
                'hard_steer_count': n_hard_steer,
                'hard_steer_rate': hard_steer_rate,
                'accel_mean': accel_mean,
                'accel_std': accel_std,
                'accel_abs_mean': accel_abs_mean
            })

        df_results = pd.DataFrame(results)

        # Calculate changes
        if len(df_results) == 2:
            before = df_results[df_results['period'] == 'before'].iloc[0]
            after = df_results[df_results['period'] == 'after'].iloc[0]

            print(f"\n{'=' * 80}")
            print("CHANGES (AFTER - BEFORE):")
            print(f"{'=' * 80}")
            print(f"  Hard braking rate: {after['hard_brake_rate'] - before['hard_brake_rate']:+.2f} per 1000")
            print(f"  Rapid acceleration rate: {after['rapid_accel_rate'] - before['rapid_accel_rate']:+.2f} per 1000")
            print(f"  Hard steering rate: {after['hard_steer_rate'] - before['hard_steer_rate']:+.2f} per 1000")
            print(f"  Acceleration variability: {after['accel_abs_mean'] - before['accel_abs_mean']:+.3f} m/s²")

        # Save
        output_path = self.output_dir / "behavioral_by_period.csv"
        df_results.to_csv(output_path, index=False)
        print(f"\n✅ Saved: {output_path}")

        return df_results

    def analyze_by_vehicle_type(self):
        """Analyze behavioral metrics by vehicle type"""
        print("\n" + "=" * 80)
        print("ANALYSIS 2: BEHAVIORAL EVENTS BY VEHICLE TYPE")
        print("=" * 80)

        df = self.df_accel

        results = []

        for vehicle_type in ['LCV', 'CAR', 'HCV']:
            vehicle_data = df[df['VehicleType'] == vehicle_type]

            for period in ['before', 'after']:
                period_data = vehicle_data[vehicle_data['period'] == period]

                if len(period_data) == 0:
                    continue

                n_transitions = len(period_data)
                n_hard_brake = period_data['is_hard_brake'].sum()
                n_rapid_accel = period_data['is_rapid_accel'].sum()
                n_hard_steer = period_data['is_hard_steer'].sum()

                hard_brake_rate = (n_hard_brake / n_transitions * 1000)
                rapid_accel_rate = (n_rapid_accel / n_transitions * 1000)
                hard_steer_rate = (n_hard_steer / n_transitions * 1000)

                results.append({
                    'vehicle_type': vehicle_type,
                    'period': period,
                    'n_transitions': n_transitions,
                    'hard_brake_rate': hard_brake_rate,
                    'rapid_accel_rate': rapid_accel_rate,
                    'hard_steer_rate': hard_steer_rate,
                    'accel_mean': period_data['acceleration'].mean(),
                    'accel_std': period_data['acceleration'].std()
                })

        df_results = pd.DataFrame(results)

        # Print summary
        for vehicle_type in ['LCV', 'CAR', 'HCV']:
            veh_data = df_results[df_results['vehicle_type'] == vehicle_type]

            if len(veh_data) < 2:
                continue

            print(f"\n{vehicle_type}:")

            before = veh_data[veh_data['period'] == 'before'].iloc[0]
            after = veh_data[veh_data['period'] == 'after'].iloc[0]

            print(f"  Hard braking: {before['hard_brake_rate']:.2f} → {after['hard_brake_rate']:.2f} per 1000 " +
                  f"({after['hard_brake_rate'] - before['hard_brake_rate']:+.2f})")
            print(f"  Rapid accel: {before['rapid_accel_rate']:.2f} → {after['rapid_accel_rate']:.2f} per 1000 " +
                  f"({after['rapid_accel_rate'] - before['rapid_accel_rate']:+.2f})")
            print(f"  Hard steering: {before['hard_steer_rate']:.2f} → {after['hard_steer_rate']:.2f} per 1000 " +
                  f"({after['hard_steer_rate'] - before['hard_steer_rate']:+.2f})")

        # Save
        output_path = self.output_dir / "behavioral_by_vehicle_type.csv"
        df_results.to_csv(output_path, index=False)
        print(f"\n✅ Saved: {output_path}")

        return df_results

    def analyze_speed_variability(self):
        """Analyze speed variability within trips"""
        print("\n" + "=" * 80)
        print("ANALYSIS 3: SPEED VARIABILITY")
        print("=" * 80)

        # Calculate per-trip variability
        trip_stats = self.df_accel.groupby('TripID').agg({
            'speed_curr': ['mean', 'std', 'min', 'max'],
            'acceleration': lambda x: x.abs().mean(),  # Mean absolute acceleration
            'period': 'first',
            'VehicleType': 'first'
        }).reset_index()

        trip_stats.columns = ['TripID', 'speed_mean', 'speed_std', 'speed_min',
                               'speed_max', 'accel_abs_mean', 'period', 'VehicleType']

        trip_stats['speed_range'] = trip_stats['speed_max'] - trip_stats['speed_min']
        trip_stats['speed_cv'] = trip_stats['speed_std'] / trip_stats['speed_mean']  # Coefficient of variation

        results = []

        for period in ['before', 'after']:
            period_data = trip_stats[trip_stats['period'] == period]

            print(f"\n{period.upper()} Period (n={len(period_data):,} trips):")
            print(f"  Speed std dev: {period_data['speed_std'].mean():.2f} km/h (mean)")
            print(f"  Speed range: {period_data['speed_range'].mean():.2f} km/h (mean)")
            print(f"  Coefficient of variation: {period_data['speed_cv'].mean():.3f}")
            print(f"  Mean absolute acceleration: {period_data['accel_abs_mean'].mean():.3f} m/s²")

            results.append({
                'period': period,
                'n_trips': len(period_data),
                'speed_std_mean': period_data['speed_std'].mean(),
                'speed_range_mean': period_data['speed_range'].mean(),
                'speed_cv_mean': period_data['speed_cv'].mean(),
                'accel_abs_mean': period_data['accel_abs_mean'].mean()
            })

        df_results = pd.DataFrame(results)

        # Calculate changes
        if len(df_results) == 2:
            before = df_results[df_results['period'] == 'before'].iloc[0]
            after = df_results[df_results['period'] == 'after'].iloc[0]

            print(f"\n{'=' * 80}")
            print("CHANGES (AFTER - BEFORE):")
            print(f"{'=' * 80}")
            print(f"  Speed std dev: {after['speed_std_mean'] - before['speed_std_mean']:+.2f} km/h")
            print(f"  Speed range: {after['speed_range_mean'] - before['speed_range_mean']:+.2f} km/h")
            print(f"  Speed CV: {after['speed_cv_mean'] - before['speed_cv_mean']:+.3f}")
            print(f"  Mean abs accel: {after['accel_abs_mean'] - before['accel_abs_mean']:+.3f} m/s²")

        # Save
        output_path = self.output_dir / "speed_variability.csv"
        df_results.to_csv(output_path, index=False)
        print(f"\n✅ Saved: {output_path}")

        return df_results

    def run_all_analyses(self):
        """Run complete behavioral analysis"""
        self.load_data()
        self.calculate_acceleration_metrics()

        self.analyze_by_period()
        self.analyze_by_vehicle_type()
        self.analyze_speed_variability()

        print("\n" + "=" * 80)
        print("BEHAVIORAL ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"Output directory: {self.output_dir}")
        print("\nGenerated files:")
        print("  1. behavioral_by_period.csv")
        print("  2. behavioral_by_vehicle_type.csv")
        print("  3. speed_variability.csv")
        print("=" * 80)


if __name__ == "__main__":
    analyzer = BehavioralAnalyzer()
    analyzer.run_all_analyses()

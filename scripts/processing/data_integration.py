"""
Data Integration Module
=======================
Unified interface to load and work with both trip-level and point-level corridor data.
Provides backward compatibility with existing analysis scripts.

Key Features:
- Load trip-level data (92,456 trips)
- Load point-level data (11.4M GPS points)
- Aggregate point-level to trip-level for existing analyses
- Period classification (before/after April 13, 2025)

Author: Data Processing Pipeline
Date: 2025-10-21
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

class CorridorDataLoader:
    """Unified data loader for SH1 corridor analysis"""

    def __init__(self, base_dir="/Volumes/T7/Data/connected_vehicle_data"):
        self.base_dir = Path(base_dir)
        self.processed_data_dir = self.base_dir / "output/processed_data"
        self.speed_change_date = pd.to_datetime("2025-04-13")

        print("🚀 Corridor Data Integration Module")
        print("="*70)
        print(f"Base directory: {self.base_dir}")
        print(f"Speed limit change date: {self.speed_change_date.date()}")
        print()

    def load_trip_level_data(self, filter_corridor=True):
        """
        Load trip-level data

        Parameters:
        -----------
        filter_corridor : bool
            If True, load only corridor trips (92,456)
            If False, load all trips (4.5M)

        Returns:
        --------
        pandas.DataFrame with trip-level data
        """
        print(f"📂 Loading trip-level data...")

        if filter_corridor:
            trip_file = self.processed_data_dir / "trip_level/corridor_trips.parquet"
            print(f"   Source: corridor_trips.parquet (filtered)")
        else:
            trip_file = self.processed_data_dir / "trip_level/all_trips.parquet"
            print(f"   Source: all_trips.parquet (full dataset)")

        if not trip_file.exists():
            raise FileNotFoundError(f"Trip data not found: {trip_file}")

        df = pd.read_parquet(trip_file)
        print(f"   ✅ Loaded: {len(df):,} trips")

        # Add period classification if StartDate exists
        if 'StartDate' in df.columns:
            df['trip_start_datetime'] = pd.to_datetime(
                df['StartDate'] + ' ' + df['StartTime'],
                errors='coerce',
                utc=True
            )
            # Make speed_change_date timezone-aware
            speed_change_tz = pd.to_datetime(self.speed_change_date, utc=True)
            df['period'] = df['trip_start_datetime'].apply(
                lambda x: 'before' if pd.notna(x) and x < speed_change_tz else 'after'
            )

            period_counts = df['period'].value_counts()
            print(f"   📊 Period distribution:")
            for period, count in period_counts.items():
                pct = (count / len(df)) * 100
                print(f"      {period.upper()}: {count:,} trips ({pct:.1f}%)")

        return df

    def load_point_level_data(self, sample_frac=None, period=None):
        """
        Load point-level GPS data

        Parameters:
        -----------
        sample_frac : float, optional
            Fraction of data to sample (e.g., 0.1 for 10%). Use for memory efficiency.
        period : str, optional
            Filter by period: 'before', 'after', or None for both

        Returns:
        --------
        pandas.DataFrame with point-level GPS data (11.4M points or sample)
        """
        print(f"📍 Loading point-level GPS data...")

        points_file = self.processed_data_dir / "point_level/corridor_gps_points.parquet"

        if not points_file.exists():
            raise FileNotFoundError(f"Point data not found: {points_file}")

        # Load full dataset
        df = pd.read_parquet(points_file)
        print(f"   ✅ Loaded: {len(df):,} GPS points")

        # Filter by period if requested
        if period:
            if 'period' not in df.columns:
                raise ValueError("Period column not found. Run phase5b_add_period_column.py first.")

            df = df[df['period'] == period].copy()
            print(f"   🔍 Filtered to {period.upper()} period: {len(df):,} points")

        # Sample if requested
        if sample_frac:
            df = df.sample(frac=sample_frac, random_state=42)
            print(f"   📉 Sampled {sample_frac*100:.1f}%: {len(df):,} points")

        # Display period distribution
        if 'period' in df.columns:
            period_counts = df['period'].value_counts()
            print(f"   📊 Period distribution:")
            for period, count in period_counts.items():
                pct = (count / len(df)) * 100
                unique_trips = df[df['period'] == period]['TripID'].nunique()
                print(f"      {period.upper()}: {count:,} points ({pct:.1f}%) from {unique_trips:,} trips")

        return df

    def aggregate_points_to_trips(self, points_df, metrics=['speed', 'distance', 'duration']):
        """
        Aggregate point-level data to trip-level for compatibility with existing analyses

        Parameters:
        -----------
        points_df : pandas.DataFrame
            Point-level data from load_point_level_data()
        metrics : list
            Metrics to calculate: 'speed', 'distance', 'duration', 'acceleration'

        Returns:
        --------
        pandas.DataFrame with trip-level aggregated data
        """
        print(f"\n📊 Aggregating point-level data to trip-level...")
        print(f"   Input: {len(points_df):,} GPS points")

        # Group by trip
        trip_groups = points_df.groupby('TripID')

        # Initialize aggregation dictionary
        agg_data = {
            'TripID': [],
            'VehicleID': [],
            'VehicleType': [],
            'TripStartTime': [],
            'period': [],
            'num_points': [],
        }

        # Add metric-specific fields
        if 'speed' in metrics:
            agg_data.update({
                'avg_speed_kmh': [],
                'max_speed_kmh': [],
                'min_speed_kmh': [],
                'median_speed_kmh': [],
            })

        if 'distance' in metrics:
            agg_data['total_distance_m'] = []

        if 'duration' in metrics:
            agg_data['travel_time_min'] = []

        # Aggregate each trip
        for trip_id, trip_data in trip_groups:
            agg_data['TripID'].append(trip_id)
            agg_data['VehicleID'].append(trip_data['VehicleID'].iloc[0])
            agg_data['VehicleType'].append(trip_data['VehicleType'].iloc[0])
            agg_data['TripStartTime'].append(trip_data['TripStartTime'].iloc[0])
            agg_data['num_points'].append(len(trip_data))

            if 'period' in trip_data.columns:
                agg_data['period'].append(trip_data['period'].iloc[0])

            if 'speed' in metrics:
                agg_data['avg_speed_kmh'].append(trip_data['Point_Speed'].mean())
                agg_data['max_speed_kmh'].append(trip_data['Point_Speed'].max())
                agg_data['min_speed_kmh'].append(trip_data['Point_Speed'].min())
                agg_data['median_speed_kmh'].append(trip_data['Point_Speed'].median())

            if 'distance' in metrics and 'Trip_DistanceMetres' in trip_data.columns:
                agg_data['total_distance_m'].append(trip_data['Trip_DistanceMetres'].iloc[0])

            if 'duration' in metrics and 'Trip_TravelTimeMinutes' in trip_data.columns:
                agg_data['travel_time_min'].append(trip_data['Trip_TravelTimeMinutes'].iloc[0])

        df_agg = pd.DataFrame(agg_data)
        print(f"   ✅ Aggregated to {len(df_agg):,} trips")

        if 'period' in df_agg.columns:
            period_counts = df_agg['period'].value_counts()
            print(f"   📊 Period distribution:")
            for period, count in period_counts.items():
                pct = (count / len(df_agg)) * 100
                print(f"      {period.upper()}: {count:,} trips ({pct:.1f}%)")

        return df_agg

    def get_speed_statistics(self, data_source='trip', period=None):
        """
        Get speed statistics for before/after comparison

        Parameters:
        -----------
        data_source : str
            'trip' for trip-level data, 'point' for point-level data
        period : str, optional
            'before', 'after', or None for both

        Returns:
        --------
        dict with speed statistics
        """
        print(f"\n📈 Calculating speed statistics...")

        if data_source == 'trip':
            df = self.load_trip_level_data(filter_corridor=True)
            speed_col = 'SpeedAvg' if 'SpeedAvg' in df.columns else 'avg_speed_kmh'
        else:
            df = self.load_point_level_data()
            # Aggregate to trip level
            df = self.aggregate_points_to_trips(df, metrics=['speed'])
            speed_col = 'avg_speed_kmh'

        # Filter by period if requested
        if period and 'period' in df.columns:
            df = df[df['period'] == period]

        stats = {}

        if 'period' in df.columns:
            for p in ['before', 'after']:
                period_data = df[df['period'] == p][speed_col]
                stats[p] = {
                    'count': len(period_data),
                    'mean': period_data.mean(),
                    'median': period_data.median(),
                    'std': period_data.std(),
                    'min': period_data.min(),
                    'max': period_data.max(),
                    'q25': period_data.quantile(0.25),
                    'q75': period_data.quantile(0.75),
                }

            # Calculate change
            stats['change'] = {
                'mean_diff': stats['after']['mean'] - stats['before']['mean'],
                'median_diff': stats['after']['median'] - stats['before']['median'],
                'pct_change': ((stats['after']['mean'] - stats['before']['mean']) / stats['before']['mean']) * 100
            }
        else:
            period_data = df[speed_col]
            stats['overall'] = {
                'count': len(period_data),
                'mean': period_data.mean(),
                'median': period_data.median(),
                'std': period_data.std(),
                'min': period_data.min(),
                'max': period_data.max(),
            }

        return stats

    def export_for_existing_analyses(self, output_format='csv'):
        """
        Export point-level data in formats compatible with existing analysis scripts

        Parameters:
        -----------
        output_format : str
            'csv' or 'parquet'
        """
        print(f"\n💾 Exporting data for existing analyses...")

        # Load and aggregate point data
        points_df = self.load_point_level_data()
        trips_df = self.aggregate_points_to_trips(points_df, metrics=['speed', 'distance', 'duration'])

        # Export
        output_dir = self.base_dir / "output/processed_data"

        if output_format == 'csv':
            output_file = output_dir / "corridor_trips_from_points.csv"
            trips_df.to_csv(output_file, index=False)
        else:
            output_file = output_dir / "corridor_trips_from_points.parquet"
            trips_df.to_parquet(output_file, index=False)

        print(f"   ✅ Exported: {output_file}")
        print(f"   📊 {len(trips_df):,} trips ready for analysis")

        return output_file


def main():
    """Demo usage"""
    print("="*70)
    print("DATA INTEGRATION MODULE - DEMO")
    print("="*70)

    loader = CorridorDataLoader()

    # Example 1: Load trip-level data
    print("\n" + "="*70)
    print("EXAMPLE 1: Load Trip-Level Data")
    print("="*70)
    trips = loader.load_trip_level_data(filter_corridor=True)
    print(f"Shape: {trips.shape}")
    print(f"Columns: {', '.join(trips.columns[:10])}...")

    # Example 2: Load point-level data (sample for demo)
    print("\n" + "="*70)
    print("EXAMPLE 2: Load Point-Level Data (10% sample)")
    print("="*70)
    points = loader.load_point_level_data(sample_frac=0.1)
    print(f"Shape: {points.shape}")
    print(f"Columns: {', '.join(points.columns)}")

    # Example 3: Aggregate points to trips
    print("\n" + "="*70)
    print("EXAMPLE 3: Aggregate Points to Trips")
    print("="*70)
    aggregated = loader.aggregate_points_to_trips(points)
    print(f"Shape: {aggregated.shape}")
    print(f"Columns: {', '.join(aggregated.columns)}")

    # Example 4: Get speed statistics
    print("\n" + "="*70)
    print("EXAMPLE 4: Speed Statistics from Point-Level Data")
    print("="*70)
    stats = loader.get_speed_statistics(data_source='point')

    if 'before' in stats and 'after' in stats:
        print(f"\n📊 BEFORE Period:")
        print(f"   Trips: {stats['before']['count']:,}")
        print(f"   Mean speed: {stats['before']['mean']:.2f} km/h")
        print(f"   Median speed: {stats['before']['median']:.2f} km/h")

        print(f"\n📊 AFTER Period:")
        print(f"   Trips: {stats['after']['count']:,}")
        print(f"   Mean speed: {stats['after']['mean']:.2f} km/h")
        print(f"   Median speed: {stats['after']['median']:.2f} km/h")

        print(f"\n📈 CHANGE:")
        print(f"   Mean difference: {stats['change']['mean_diff']:+.2f} km/h")
        print(f"   Percent change: {stats['change']['pct_change']:+.1f}%")

    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()

"""
Efficient Data Integration
Fast integration of new vehicle data with existing comprehensive dataset
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

class EfficientDataIntegrator:
    def __init__(self):
        self.base_dir = "/Volumes/T7/Data/connected_vehicle_data"
        self.data_dir = os.path.join(self.base_dir, "output", "processed_data")

        print("⚡ EFFICIENT DATA INTEGRATION")
        print("Integrating 66K new trips with existing dataset")
        print("="*50)

    def create_summary_integration(self):
        """Create summary-level integration without processing full GPS paths"""
        print(f"\n📊 LOADING EXISTING DATA SUMMARY")

        # Load existing comprehensive data
        existing_path = os.path.join(self.data_dir, "comprehensive_gps_metrics.csv")
        existing = pd.read_csv(existing_path)
        existing['timestamp'] = pd.to_datetime(existing['timestamp'])

        print(f"✅ Existing data: {len(existing):,} GPS points")

        # Create summary of existing data
        existing_summary = existing.groupby(['VehicleID', 'TripID']).agg({
            'timestamp': ['min', 'max', 'count'],
            'derived_speed_kmh': ['mean', 'max', 'std'],
            'Point_RawLon': ['mean', 'std'],
            'Point_RawLat': ['mean', 'std']
        }).reset_index()

        # Flatten column names
        existing_summary.columns = [
            'VehicleID', 'TripID', 'trip_start_time', 'trip_end_time', 'gps_points',
            'avg_speed_kmh', 'max_speed_kmh', 'speed_std_kmh',
            'avg_lon', 'lon_std', 'avg_lat', 'lat_std'
        ]

        existing_summary['trip_duration_seconds'] = (
            existing_summary['trip_end_time'] - existing_summary['trip_start_time']
        ).dt.total_seconds()

        existing_summary['data_source'] = 'original_comprehensive'

        print(f"📈 Existing trips summarized: {len(existing_summary):,}")

        # Load new data (already processed)
        new_path = os.path.join(self.data_dir, "combined_new_cv_data.csv")
        new_data = pd.read_csv(new_path)

        print(f"✅ New data: {len(new_data):,} trips")

        # Standardize new data format
        new_standardized = pd.DataFrame({
            'VehicleID': new_data['vehicleID'],
            'TripID': new_data['TripID'],
            'trip_start_time': pd.to_datetime(new_data['StartDate']),
            'trip_end_time': pd.to_datetime(new_data['EndDate']),
            'gps_points': new_data['TimestampPath'].str.count(',') + 1,  # Approximate
            'avg_speed_kmh': pd.to_numeric(new_data['SpeedAvg'], errors='coerce'),
            'max_speed_kmh': pd.to_numeric(new_data['SpeedMax'], errors='coerce'),
            'speed_std_kmh': np.nan,  # Not available in new data
            'avg_lon': np.nan,  # Could extract from paths if needed
            'avg_lat': np.nan,
            'lon_std': np.nan,
            'lat_std': np.nan,
            'trip_duration_seconds': pd.to_numeric(new_data['TravelTimeSeconds'], errors='coerce'),
            'data_source': 'additional_jan_feb_2025'
        })

        # Combine datasets
        integrated_summary = pd.concat([existing_summary, new_standardized], ignore_index=True)
        integrated_summary = integrated_summary.sort_values('trip_start_time').reset_index(drop=True)

        print(f"\n🎯 INTEGRATED SUMMARY:")
        print(f"• Total trips: {len(integrated_summary):,}")
        print(f"• Original trips: {len(existing_summary):,}")
        print(f"• New trips added: {len(new_standardized):,}")

        # Temporal analysis
        speed_change_date = pd.to_datetime("2025-04-13")
        before_trips = integrated_summary[integrated_summary['trip_start_time'] < speed_change_date]
        after_trips = integrated_summary[integrated_summary['trip_start_time'] >= speed_change_date]

        print(f"\n📅 TEMPORAL DISTRIBUTION:")
        print(f"• BEFORE period (< Apr 13): {len(before_trips):,} trips")
        print(f"• AFTER period (>= Apr 13): {len(after_trips):,} trips")
        print(f"• Improvement factor: {len(before_trips) / (len(before_trips) - len(new_standardized)):.1f}x more BEFORE data")

        return integrated_summary

    def save_integrated_data(self, integrated_summary):
        """Save the integrated dataset"""
        print(f"\n💾 SAVING INTEGRATED DATA")

        # Save trip-level summary
        summary_path = os.path.join(self.data_dir, "integrated_trip_summary.csv")
        integrated_summary.to_csv(summary_path, index=False)
        print(f"✅ Trip summary: {summary_path}")

        # Save as parquet for efficiency
        parquet_path = os.path.join(self.data_dir, "integrated_trip_summary.parquet")
        integrated_summary.to_parquet(parquet_path, index=False)
        print(f"✅ Parquet format: {parquet_path}")

        # Create integration metadata
        metadata = {
            'integration_timestamp': datetime.now().isoformat(),
            'original_trips': len(integrated_summary[integrated_summary['data_source'] == 'original_comprehensive']),
            'new_trips_added': len(integrated_summary[integrated_summary['data_source'] == 'additional_jan_feb_2025']),
            'total_integrated_trips': len(integrated_summary),
            'date_range_start': str(integrated_summary['trip_start_time'].min()),
            'date_range_end': str(integrated_summary['trip_start_time'].max()),
            'enhancement_factor': len(integrated_summary) / len(integrated_summary[integrated_summary['data_source'] == 'original_comprehensive'])
        }

        metadata_df = pd.DataFrame([metadata])
        metadata_path = os.path.join(self.data_dir, "integration_metadata.csv")
        metadata_df.to_csv(metadata_path, index=False)
        print(f"📊 Metadata: {metadata_path}")

        return True

def main():
    integrator = EfficientDataIntegrator()

    # Create integrated summary
    integrated_summary = integrator.create_summary_integration()

    # Save results
    integrator.save_integrated_data(integrated_summary)

    print(f"\n✅ EFFICIENT INTEGRATION COMPLETE!")
    print(f"Ready for enhanced statistical analysis")

if __name__ == "__main__":
    main()
"""
Integrate New Before-Period Data into Comprehensive Analysis
Merge the 66,897 new vehicle trips (Jan-Feb 2025) with existing comprehensive dataset
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

class BeforeDataIntegrator:
    def __init__(self):
        self.base_dir = "/Volumes/T7/Data/connected_vehicle_data"
        self.data_dir = os.path.join(self.base_dir, "output", "processed_data")
        self.speed_change_date = pd.to_datetime("2025-04-13")

        print("🔗 BEFORE-PERIOD DATA INTEGRATOR")
        print("Integrating 66,897 new vehicle trips into comprehensive analysis")
        print("="*60)

    def load_datasets(self):
        """Load existing and new datasets"""
        print(f"\n📂 LOADING DATASETS")

        # Load existing comprehensive data
        existing_path = os.path.join(self.data_dir, "comprehensive_gps_metrics.csv")
        if os.path.exists(existing_path):
            self.existing_data = pd.read_csv(existing_path)
            print(f"✅ Existing comprehensive data: {len(self.existing_data):,} records")

            # Parse timestamps
            self.existing_data['timestamp'] = pd.to_datetime(self.existing_data['timestamp'])

            # Analyze existing temporal coverage
            min_date = self.existing_data['timestamp'].min()
            max_date = self.existing_data['timestamp'].max()
            print(f"📅 Existing date range: {min_date} to {max_date}")

            before_count = len(self.existing_data[self.existing_data['timestamp'] < self.speed_change_date])
            after_count = len(self.existing_data[self.existing_data['timestamp'] >= self.speed_change_date])
            print(f"   • BEFORE period: {before_count:,} records")
            print(f"   • AFTER period: {after_count:,} records")
        else:
            print(f"❌ Existing comprehensive data not found at {existing_path}")
            return False

        # Load new data
        new_path = os.path.join(self.data_dir, "combined_new_cv_data.csv")
        if os.path.exists(new_path):
            self.new_data = pd.read_csv(new_path)
            print(f"✅ New combined data: {len(self.new_data):,} records")

            # Check temporal coverage of new data
            if 'StartDate' in self.new_data.columns:
                self.new_data['parsed_date'] = pd.to_datetime(self.new_data['StartDate'])
                new_min = self.new_data['parsed_date'].min()
                new_max = self.new_data['parsed_date'].max()
                print(f"📅 New data range: {new_min} to {new_max}")
                print(f"   • Period: {'BEFORE' if new_max < self.speed_change_date else 'MIXED'}")

            print(f"📊 New data columns: {len(self.new_data.columns)}")
        else:
            print(f"❌ New combined data not found at {new_path}")
            return False

        return True

    def analyze_data_compatibility(self):
        """Analyze compatibility between existing and new datasets"""
        print(f"\n🔍 ANALYZING DATA COMPATIBILITY")

        print(f"📊 DATASET COMPARISON:")
        print(f"• Existing data: {len(self.existing_data):,} records, {len(self.existing_data.columns)} columns")
        print(f"• New data: {len(self.new_data):,} records, {len(self.new_data.columns)} columns")

        # Column analysis
        existing_cols = set(self.existing_data.columns)
        new_cols = set(self.new_data.columns)

        common_cols = existing_cols.intersection(new_cols)
        existing_only = existing_cols - new_cols
        new_only = new_cols - existing_cols

        print(f"\n📋 COLUMN ANALYSIS:")
        print(f"• Common columns: {len(common_cols)}")
        print(f"• Existing only: {len(existing_only)}")
        print(f"• New only: {len(new_only)}")

        if existing_only:
            print(f"\n📝 Existing-only columns (first 5): {list(existing_only)[:5]}")

        if new_only:
            print(f"📝 New-only columns (first 5): {list(new_only)[:5]}")

        # Check key columns for GPS analysis
        gps_key_columns = ['VehicleID', 'timestamp', 'derived_speed_kmh', 'Point_RawLon', 'Point_RawLat']
        missing_in_new = [col for col in gps_key_columns if col not in new_cols]

        if missing_in_new:
            print(f"\n⚠️  Key GPS columns missing in new data: {missing_in_new}")
            print("   This may require data transformation before integration")
        else:
            print(f"\n✅ All key GPS analysis columns present")

        return {
            'common_columns': common_cols,
            'compatible': len(missing_in_new) == 0,
            'requires_transformation': len(missing_in_new) > 0
        }

    def transform_new_data_format(self):
        """Transform new data to match existing GPS analysis format"""
        print(f"\n🔄 TRANSFORMING NEW DATA FORMAT")

        # The new data has trip-level summaries, not individual GPS points
        # We need to create a mapping strategy

        print("📊 NEW DATA STRUCTURE ANALYSIS:")
        print(f"• Data type: Trip-level summaries (not individual GPS points)")
        print(f"• Key fields: vehicleID, TripID, StartDate, SpeedAvg, etc.")

        # Check if we have path/trajectory data
        if 'TimestampPath' in self.new_data.columns:
            print("✅ Found TimestampPath - individual GPS points available")
            return self.extract_gps_points_from_paths()
        else:
            print("⚠️  No individual GPS points - using trip summaries")
            return self.create_synthetic_gps_from_trips()

    def extract_gps_points_from_paths(self):
        """Extract individual GPS points from path strings"""
        print(f"\n📍 EXTRACTING GPS POINTS FROM PATHS")

        extracted_points = []
        processed_trips = 0

        for idx, row in self.new_data.iterrows():
            if processed_trips % 1000 == 0:
                print(f"   Processing trip {processed_trips:,}/{len(self.new_data):,}")

            try:
                # Parse timestamp path
                if pd.isna(row['TimestampPath']) or pd.isna(row['SnappedPath']):
                    continue

                timestamps = row['TimestampPath'].split(',')
                coordinates = row['SnappedPath'].split(',')
                speeds = str(row['SpeedPath']).split(',') if not pd.isna(row['SpeedPath']) else []

                # Process each point in the path
                for i, (timestamp_str, coord_str) in enumerate(zip(timestamps, coordinates)):
                    try:
                        # Parse coordinates
                        coord_parts = coord_str.strip().split(' ')
                        if len(coord_parts) >= 2:
                            lon = float(coord_parts[0])
                            lat = float(coord_parts[1])

                            # Create GPS point record
                            point_data = {
                                'TripID': row['TripID'],
                                'VehicleID': row['vehicleID'],
                                'VehicleType': row['VehicleType'],
                                'timestamp': pd.to_datetime(timestamp_str.strip()),
                                'Point_RawLon': lon,
                                'Point_RawLat': lat,
                                'Point_SnappedLon': lon,
                                'Point_SnappedLat': lat,
                                'derived_speed_kmh': float(speeds[i]) if i < len(speeds) and speeds[i].isdigit() else np.nan,
                                'source_file': row['source_file'],
                                'data_source': 'new_trip_paths'
                            }
                            extracted_points.append(point_data)

                    except (ValueError, IndexError) as e:
                        continue  # Skip malformed points

            except Exception as e:
                continue  # Skip problematic trips

            processed_trips += 1

        if extracted_points:
            gps_df = pd.DataFrame(extracted_points)
            print(f"✅ Extracted {len(gps_df):,} GPS points from {processed_trips:,} trips")
            print(f"📅 Point time range: {gps_df['timestamp'].min()} to {gps_df['timestamp'].max()}")
            return gps_df
        else:
            print("❌ No GPS points could be extracted")
            return pd.DataFrame()

    def integrate_datasets(self, new_gps_data):
        """Integrate new GPS data with existing comprehensive dataset"""
        if new_gps_data.empty:
            print("❌ No new GPS data to integrate")
            return False

        print(f"\n🔗 INTEGRATING DATASETS")

        # Align columns between datasets
        common_columns = []
        for col in self.existing_data.columns:
            if col in new_gps_data.columns:
                common_columns.append(col)

        print(f"📊 Using {len(common_columns)} common columns for integration")

        # Prepare datasets with common columns
        existing_subset = self.existing_data[common_columns].copy()
        new_subset = new_gps_data[common_columns].copy()

        # Add integration metadata
        existing_subset['integration_batch'] = 'original'
        new_subset['integration_batch'] = 'january_february_2025'

        # Combine datasets
        integrated_data = pd.concat([existing_subset, new_subset], ignore_index=True)
        integrated_data = integrated_data.sort_values('timestamp').reset_index(drop=True)

        print(f"🎯 INTEGRATED DATASET:")
        print(f"• Total records: {len(integrated_data):,}")
        print(f"• Original records: {len(existing_subset):,}")
        print(f"• New records: {len(new_subset):,}")
        print(f"• Date range: {integrated_data['timestamp'].min()} to {integrated_data['timestamp'].max()}")

        # Analyze BEFORE/AFTER periods
        before_data = integrated_data[integrated_data['timestamp'] < self.speed_change_date]
        after_data = integrated_data[integrated_data['timestamp'] >= self.speed_change_date]

        print(f"\n📊 BEFORE/AFTER ANALYSIS:")
        print(f"• BEFORE (< Apr 13): {len(before_data):,} records")
        print(f"• AFTER (>= Apr 13): {len(after_data):,} records")
        print(f"• Improvement: {len(new_subset):,} additional BEFORE period records")

        return integrated_data

    def save_integrated_dataset(self, integrated_data):
        """Save the integrated dataset"""
        if integrated_data is None or len(integrated_data) == 0:
            print("❌ No integrated data to save")
            return False

        print(f"\n💾 SAVING INTEGRATED DATASET")

        # Save enhanced comprehensive dataset
        output_path = os.path.join(self.data_dir, "enhanced_comprehensive_gps_metrics.csv")
        integrated_data.to_csv(output_path, index=False)
        print(f"✅ Saved: {output_path}")

        # Also save as parquet for efficiency
        parquet_path = os.path.join(self.data_dir, "enhanced_comprehensive_gps_metrics.parquet")
        integrated_data.to_parquet(parquet_path, index=False)
        print(f"✅ Saved: {parquet_path}")

        # Create backup of original
        original_backup = os.path.join(self.data_dir, "comprehensive_gps_metrics_backup.csv")
        if not os.path.exists(original_backup):
            import shutil
            shutil.copy2(os.path.join(self.data_dir, "comprehensive_gps_metrics.csv"), original_backup)
            print(f"📁 Backup created: {original_backup}")

        # Generate integration summary
        summary = {
            'integration_date': datetime.now().isoformat(),
            'original_records': len(self.existing_data),
            'new_records_added': len(integrated_data) - len(self.existing_data),
            'total_records': len(integrated_data),
            'date_range_start': str(integrated_data['timestamp'].min()),
            'date_range_end': str(integrated_data['timestamp'].max()),
            'before_period_records': len(integrated_data[integrated_data['timestamp'] < self.speed_change_date]),
            'after_period_records': len(integrated_data[integrated_data['timestamp'] >= self.speed_change_date])
        }

        summary_df = pd.DataFrame([summary])
        summary_path = os.path.join(self.data_dir, "integration_summary.csv")
        summary_df.to_csv(summary_path, index=False)
        print(f"📊 Integration summary: {summary_path}")

        return True

def main():
    integrator = BeforeDataIntegrator()

    # Load datasets
    if not integrator.load_datasets():
        print("❌ Failed to load datasets")
        return

    # Analyze compatibility
    compatibility = integrator.analyze_data_compatibility()

    if compatibility['requires_transformation']:
        # Transform new data format
        new_gps_data = integrator.transform_new_data_format()
    else:
        print("✅ Data formats compatible - proceeding with direct integration")
        new_gps_data = integrator.new_data

    # Integrate datasets
    integrated_data = integrator.integrate_datasets(new_gps_data)

    # Save results
    if integrator.save_integrated_dataset(integrated_data):
        print(f"\n✅ INTEGRATION COMPLETE!")
        print(f"Enhanced dataset ready for improved before/after analysis")
        print(f"Next step: python scripts/analysis/economic_impact_analysis_our_data.py")
    else:
        print(f"\n❌ INTEGRATION FAILED")

if __name__ == "__main__":
    main()
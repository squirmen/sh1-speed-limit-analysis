"""
Comprehensive Data Validation and Deduplication Analysis
Determine if new files contain duplicates or actual new post-May 12 data
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
import hashlib

class DataValidator:
    def __init__(self):
        self.base_dir = "/Volumes/T7/Data/connected_vehicle_data"
        self.data_dir = os.path.join(self.base_dir, "output", "processed_data")

        print("🔍 COMPREHENSIVE DATA VALIDATION")
        print("Checking for duplicates vs new data (expected: May 12 - July 31, 2025)")
        print("="*60)

    def load_and_analyze_existing_data(self):
        """Load existing comprehensive data and analyze coverage"""
        print(f"\n📊 ANALYZING EXISTING DATA COVERAGE")

        existing_path = os.path.join(self.data_dir, "comprehensive_gps_metrics.csv")
        if not os.path.exists(existing_path):
            print(f"❌ Existing data not found: {existing_path}")
            return None

        df = pd.read_csv(existing_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        print(f"✅ Existing data: {len(df):,} records")
        print(f"📅 Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

        # Check coverage by month
        df['month'] = df['timestamp'].dt.to_period('M')
        monthly_counts = df['month'].value_counts().sort_index()

        print(f"\n📈 MONTHLY COVERAGE:")
        for month, count in monthly_counts.items():
            print(f"  {month}: {count:,} records")

        # Check if we have post-May 12 data
        post_may12 = df[df['timestamp'] >= pd.to_datetime('2025-05-12')]
        print(f"\n🎯 POST-MAY 12 COVERAGE: {len(post_may12):,} records")
        if len(post_may12) > 0:
            print(f"   Range: {post_may12['timestamp'].min()} to {post_may12['timestamp'].max()}")

        return df

    def deep_analyze_new_files(self):
        """Deep analysis of the new files to check actual temporal coverage"""
        print(f"\n🔍 DEEP ANALYSIS OF NEW FILES")

        new_files = [
            "support.NZ_report_withOD-3bce8a274bbe280dd0b32026-000000000000.csv",
            "support.NZ_report_withOD-3bce8a274bbe280dd0b32026-000000000001.csv",
            "support.NZ_report_withOD-3bce8a274bbe280dd0b32026-000000000002.csv"
        ]

        all_dates = []
        all_trip_ids = []

        for file_name in new_files:
            file_path = os.path.join(self.data_dir, file_name)
            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_name}")
                continue

            print(f"\n📁 ANALYZING: {file_name}")

            # Sample the file more thoroughly
            chunk_size = 1000
            date_samples = []
            trip_id_samples = []

            try:
                for chunk in pd.read_csv(file_path, chunksize=chunk_size, nrows=10000):
                    # Extract dates from multiple possible columns
                    for date_col in ['StartDate', 'EndDate']:
                        if date_col in chunk.columns:
                            dates = pd.to_datetime(chunk[date_col], errors='coerce')
                            valid_dates = dates.dropna()
                            date_samples.extend(valid_dates.tolist())

                    # Extract trip IDs for duplication checking
                    if 'TripID' in chunk.columns:
                        trip_id_samples.extend(chunk['TripID'].dropna().tolist())

                if date_samples:
                    min_date = min(date_samples)
                    max_date = max(date_samples)
                    print(f"   📅 Date range: {min_date} to {max_date}")
                    print(f"   📊 Date samples: {len(date_samples):,}")
                    all_dates.extend(date_samples)
                else:
                    print(f"   ❌ No valid dates found")

                if trip_id_samples:
                    print(f"   🆔 Unique trip IDs: {len(set(trip_id_samples)):,}")
                    all_trip_ids.extend(trip_id_samples)

            except Exception as e:
                print(f"   ❌ Error reading file: {e}")

        # Overall analysis of new files
        if all_dates:
            print(f"\n🎯 OVERALL NEW FILES ANALYSIS:")
            print(f"   📅 Combined date range: {min(all_dates)} to {max(all_dates)}")
            print(f"   📊 Total date records: {len(all_dates):,}")

            # Check if we have the expected May 12 - July 31 range
            expected_start = pd.to_datetime('2025-05-12')
            expected_end = pd.to_datetime('2025-07-31')

            post_may12_dates = [d for d in all_dates if d >= expected_start]
            in_expected_range = [d for d in all_dates if expected_start <= d <= expected_end]

            print(f"   🔍 POST-MAY 12: {len(post_may12_dates):,} records")
            print(f"   🎯 EXPECTED RANGE (May 12-July 31): {len(in_expected_range):,} records")

            if len(in_expected_range) == 0:
                print(f"   ⚠️  WARNING: NO DATA IN EXPECTED RANGE!")
                print(f"   📋 This appears to be DUPLICATE data, not new post-May 12 data")
            else:
                print(f"   ✅ Found data in expected range!")

        if all_trip_ids:
            print(f"   🆔 Total unique trip IDs: {len(set(all_trip_ids)):,}")

        return {
            'all_dates': all_dates,
            'all_trip_ids': all_trip_ids,
            'has_expected_range': len(in_expected_range) > 0 if all_dates else False
        }

    def check_for_duplicates(self, existing_data, new_file_analysis):
        """Check if new data contains duplicates of existing data"""
        print(f"\n🔄 CHECKING FOR DUPLICATES")

        if not new_file_analysis['has_expected_range']:
            print(f"⚠️  New files don't contain expected date range (May 12-July 31 2025)")
            print(f"   This suggests the files contain DUPLICATE data, not new data")
            return True  # Likely duplicates

        # Load combined new data for more detailed comparison
        combined_path = os.path.join(self.data_dir, "combined_new_cv_data.csv")
        if not os.path.exists(combined_path):
            print(f"❌ Combined new data not found")
            return None

        new_data = pd.read_csv(combined_path, nrows=5000)  # Sample for performance

        print(f"📊 DUPLICATION ANALYSIS:")
        print(f"   Existing data records: {len(existing_data):,}")
        print(f"   New data sample: {len(new_data):,}")

        # Check trip ID overlaps if available
        if 'TripID' in existing_data.columns and 'TripID' in new_data.columns:
            existing_trips = set(existing_data['TripID'].dropna())
            new_trips = set(new_data['TripID'].dropna())

            overlap = existing_trips.intersection(new_trips)
            print(f"   🆔 Trip ID overlap: {len(overlap):,} trips")

            if len(overlap) > len(new_trips) * 0.5:  # More than 50% overlap
                print(f"   ⚠️  HIGH OVERLAP - Likely DUPLICATE data")
                return True
            else:
                print(f"   ✅ Low overlap - Likely NEW data")
                return False
        else:
            print(f"   ⚠️  Cannot check Trip ID overlap - different schemas")

        return None

    def test_malformed_data_handling(self):
        """Test robustness of malformed data handling"""
        print(f"\n🛠️  TESTING MALFORMED DATA HANDLING")

        test_cases = [
            "Normal,Data,Row,With,Five,Columns",
            "Row,With,Too,Many,Columns,Extra1,Extra2,Extra3,Extra4,Extra5",
            "Row,With,Too,Few",
            "Row,With,\"Embedded,Comma\",In,Quotes",
            "Row,With,\"Unclosed,Quote,Problem",
            "",  # Empty line
            "Row,With,Special,Characters,🚗,ñ,é",
        ]

        print("📋 Testing various malformed scenarios:")

        # Create test file
        test_file = os.path.join(self.data_dir, "malformed_test.csv")
        with open(test_file, 'w') as f:
            f.write("Col1,Col2,Col3,Col4,Col5\n")  # Header
            for case in test_cases:
                f.write(case + "\n")

        # Test pandas loading with various strategies
        strategies = [
            ("Default", {}),
            ("Skip bad lines", {"on_bad_lines": "skip"}),
            ("Warn bad lines", {"on_bad_lines": "warn"}),
            ("Engine python", {"engine": "python"}),
        ]

        for strategy_name, kwargs in strategies:
            try:
                df = pd.read_csv(test_file, **kwargs)
                print(f"   ✅ {strategy_name}: {len(df)} rows loaded")
            except Exception as e:
                print(f"   ❌ {strategy_name}: {str(e)[:50]}...")

        # Clean up test file
        os.remove(test_file)

        print(f"🔧 RECOMMENDED APPROACH: Use 'on_bad_lines=skip' for robustness")

    def generate_validation_report(self, existing_data, new_analysis, is_duplicate):
        """Generate comprehensive validation report"""
        print(f"\n📋 VALIDATION REPORT")
        print("="*50)

        report = {
            'validation_date': datetime.now().isoformat(),
            'existing_data_records': len(existing_data) if existing_data is not None else 0,
            'existing_date_range': f"{existing_data['timestamp'].min()} to {existing_data['timestamp'].max()}" if existing_data is not None else "N/A",
            'new_files_analyzed': 3,
            'new_data_appears_duplicate': is_duplicate,
            'expected_range_coverage': new_analysis['has_expected_range'],
            'recommendation': ""
        }

        if is_duplicate:
            report['recommendation'] = "REQUEST NEW DATA: Files appear to contain duplicate Jan-Feb 2025 data, not the expected May 12 - July 31 2025 data"
        else:
            report['recommendation'] = "PROCEED WITH INTEGRATION: Files contain new data in expected range"

        print(f"🎯 KEY FINDINGS:")
        print(f"   • Expected data range: May 12 - July 31, 2025")
        print(f"   • Actual data range: {min(new_analysis['all_dates'])} to {max(new_analysis['all_dates'])}" if new_analysis['all_dates'] else "No dates found")
        print(f"   • Contains expected range: {'YES' if new_analysis['has_expected_range'] else 'NO'}")
        print(f"   • Appears to be duplicates: {'YES' if is_duplicate else 'NO'}")

        print(f"\n💡 RECOMMENDATION:")
        print(f"   {report['recommendation']}")

        # Save report
        report_df = pd.DataFrame([report])
        report_path = os.path.join(self.data_dir, "data_validation_report.csv")
        report_df.to_csv(report_path, index=False)
        print(f"\n💾 Report saved: {report_path}")

        return report

def main():
    validator = DataValidator()

    # Load and analyze existing data
    existing_data = validator.load_and_analyze_existing_data()

    # Deep analyze new files
    new_analysis = validator.deep_analyze_new_files()

    # Check for duplicates
    is_duplicate = validator.check_for_duplicates(existing_data, new_analysis)

    # Test malformed data handling
    validator.test_malformed_data_handling()

    # Generate report
    validator.generate_validation_report(existing_data, new_analysis, is_duplicate)

if __name__ == "__main__":
    main()
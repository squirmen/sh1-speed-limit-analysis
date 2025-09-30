"""
Process New Connected Vehicle Data with Malformed Line Handling
Handle the three new post-speed-change data files and integrate with existing analysis
"""

import pandas as pd
import numpy as np
import os
import glob
import csv
import io
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class NewCVDataProcessor:
    def __init__(self):
        # Updated paths for T7 drive organization
        self.base_dir = "/Volumes/T7/Data/connected_vehicle_data"
        self.output_dir = os.path.join(self.base_dir, "output", "processed_data")
        self.speed_change_date = pd.to_datetime("2025-04-13")

        # Target files (now in base directory)
        self.new_files = [
            "support.NZ_report_withOD-3bce8a274bbe280dd0b32026-000000000000.csv",
            "support.NZ_report_withOD-3bce8a274bbe280dd0b32026-000000000001.csv",
            "support.NZ_report_withOD-3bce8a274bbe280dd0b32026-000000000002.csv"
        ]

        print("🔄 NEW CONNECTED VEHICLE DATA PROCESSOR")
        print("Processing post-speed-change data with malformed line handling")
        print(f"Base directory: {self.base_dir}")
        print("="*60)

    def inspect_file_structure(self, file_path, sample_lines=100):
        """Inspect file structure and identify malformed lines"""
        print(f"\n🔍 INSPECTING: {os.path.basename(file_path)}")

        file_size = os.path.getsize(file_path)
        print(f"📁 File size: {file_size:,} bytes ({file_size/(1024*1024):.1f} MB)")

        issues = {
            'malformed_lines': [],
            'inconsistent_columns': [],
            'total_lines_sampled': 0,
            'valid_lines': 0,
            'header': None,
            'expected_columns': 0
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Read header
                header_line = f.readline().strip()
                issues['header'] = header_line
                issues['expected_columns'] = len(header_line.split(','))

                print(f"📊 Expected columns: {issues['expected_columns']}")
                print(f"📋 Header preview: {header_line[:100]}...")

                # Sample lines for analysis
                line_count = 0
                for i, line in enumerate(f):
                    if i >= sample_lines:
                        break

                    line = line.strip()
                    if not line:
                        continue

                    actual_cols = len(line.split(','))
                    issues['total_lines_sampled'] += 1

                    if actual_cols != issues['expected_columns']:
                        issues['malformed_lines'].append({
                            'line_num': i + 2,  # +2 because we already read header
                            'expected_cols': issues['expected_columns'],
                            'actual_cols': actual_cols,
                            'line_preview': line[:100] + "..." if len(line) > 100 else line
                        })
                    else:
                        issues['valid_lines'] += 1

        except Exception as e:
            print(f"❌ Error inspecting file: {e}")
            return issues

        # Report findings
        print(f"\n📈 INSPECTION RESULTS:")
        print(f"• Lines sampled: {issues['total_lines_sampled']:,}")
        print(f"• Valid lines: {issues['valid_lines']:,}")
        print(f"• Malformed lines: {len(issues['malformed_lines']):,}")

        if issues['malformed_lines']:
            print(f"\n⚠️  MALFORMED LINE EXAMPLES (first 3):")
            for issue in issues['malformed_lines'][:3]:
                print(f"  Line {issue['line_num']}: {issue['actual_cols']} cols (expected {issue['expected_cols']})")
                print(f"    Preview: {issue['line_preview']}")

        return issues

    def load_with_error_handling(self, file_path, max_errors=1000):
        """Load CSV with robust error handling for malformed lines"""
        print(f"\n🔄 LOADING: {os.path.basename(file_path)}")

        try:
            # Method 1: Try pandas with error handling
            df = pd.read_csv(file_path,
                           on_bad_lines='skip',
                           low_memory=False,
                           dtype=str)  # Load as strings first

            print(f"✅ Loaded {len(df):,} rows, {len(df.columns)} columns")

            # Basic data type inference for key columns
            timestamp_cols = [col for col in df.columns if any(x in col.lower() for x in ['time', 'date', 'timestamp'])]
            if timestamp_cols:
                print(f"🕒 Found timestamp columns: {timestamp_cols[:3]}")

            numeric_cols = [col for col in df.columns if any(x in col.lower() for x in ['lat', 'lng', 'lon', 'speed', 'alt'])]
            if numeric_cols:
                print(f"🔢 Found numeric columns: {numeric_cols[:5]}")

            return df

        except Exception as e:
            print(f"❌ Failed to load {file_path}: {e}")
            return pd.DataFrame()

    def process_all_new_files(self):
        """Process all three new data files"""
        print(f"\n🔄 PROCESSING ALL NEW FILES")

        all_dataframes = []
        total_records = 0

        for file_name in self.new_files:
            # Check multiple possible locations
            possible_paths = [
                os.path.join(self.base_dir, file_name),
                os.path.join(self.output_dir, file_name),
                os.path.join(self.base_dir, "raw_files", file_name)
            ]

            file_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    file_path = path
                    break

            if file_path is None:
                print(f"❌ File not found: {file_name}")
                print(f"   Searched in: {[os.path.dirname(p) for p in possible_paths]}")
                continue

            print(f"\n" + "="*50)
            print(f"PROCESSING: {file_name}")

            # Inspect structure
            issues = self.inspect_file_structure(file_path)

            # Load data
            df = self.load_with_error_handling(file_path)

            if not df.empty:
                # Add metadata
                df['source_file'] = file_name
                df['processing_timestamp'] = datetime.now().isoformat()

                all_dataframes.append(df)
                total_records += len(df)
                print(f"✅ Added {len(df):,} records from {file_name}")
            else:
                print(f"❌ No data loaded from {file_name}")

        if all_dataframes:
            # Combine all data
            print(f"\n🔗 COMBINING DATA FROM {len(all_dataframes)} FILES")
            combined_df = pd.concat(all_dataframes, ignore_index=True, sort=False)

            print(f"🎯 COMBINED DATASET:")
            print(f"• Total records: {len(combined_df):,}")
            print(f"• Total columns: {len(combined_df.columns)}")
            print(f"• Memory usage: {combined_df.memory_usage(deep=True).sum()/(1024*1024):.1f} MB")

            # Save combined dataset
            output_path = os.path.join(self.output_dir, "combined_new_cv_data.csv")
            combined_df.to_csv(output_path, index=False)
            print(f"💾 Saved to: {output_path}")

            # Also save as parquet for efficiency
            parquet_path = os.path.join(self.output_dir, "combined_new_cv_data.parquet")
            combined_df.to_parquet(parquet_path, index=False)
            print(f"💾 Saved parquet: {parquet_path}")

            return combined_df
        else:
            print("❌ No data processed from any files")
            return None

    def analyze_temporal_coverage(self, df):
        """Analyze temporal coverage of the new data"""
        if df is None or df.empty:
            return None

        print(f"\n📅 ANALYZING TEMPORAL COVERAGE")

        # Find timestamp columns
        timestamp_cols = [col for col in df.columns if any(x in col.lower() for x in ['time', 'date', 'timestamp'])]

        if not timestamp_cols:
            print("⚠️  No timestamp columns found")
            print("Available columns:")
            for i, col in enumerate(df.columns[:20]):
                print(f"  {i+1:2d}. {col}")
            return None

        timestamp_col = timestamp_cols[0]
        print(f"🕒 Using timestamp column: {timestamp_col}")

        try:
            # Convert timestamps
            df['parsed_timestamp'] = pd.to_datetime(df[timestamp_col], errors='coerce', utc=True)
            valid_data = df.dropna(subset=['parsed_timestamp'])

            if len(valid_data) == 0:
                print("❌ No valid timestamps found")
                return None

            # Analyze coverage
            min_date = valid_data['parsed_timestamp'].min()
            max_date = valid_data['parsed_timestamp'].max()

            print(f"📊 TEMPORAL ANALYSIS:")
            print(f"• Date range: {min_date} to {max_date}")
            print(f"• Valid timestamps: {len(valid_data):,} / {len(df):,} ({len(valid_data)/len(df)*100:.1f}%)")

            # Check post-speed-change data
            # Convert speed_change_date to UTC for comparison
            speed_change_utc = pd.to_datetime(self.speed_change_date).tz_localize('UTC')
            post_change = valid_data[valid_data['parsed_timestamp'] >= speed_change_utc]

            print(f"\n🎯 POST-SPEED-CHANGE ANALYSIS:")
            print(f"• Records after April 13, 2025: {len(post_change):,}")

            if len(post_change) > 0:
                post_min = post_change['parsed_timestamp'].min()
                post_max = post_change['parsed_timestamp'].max()
                print(f"• Post-change period: {post_min} to {post_max}")

                # Days of coverage
                days_coverage = (post_max - post_min).days + 1
                print(f"• Days of post-change coverage: {days_coverage}")

                return {
                    'total_records': len(df),
                    'valid_timestamps': len(valid_data),
                    'post_change_records': len(post_change),
                    'date_range': (min_date, max_date),
                    'post_change_range': (post_min, post_max),
                    'days_coverage': days_coverage
                }
            else:
                print("❌ No post-speed-change data found!")
                return None

        except Exception as e:
            print(f"❌ Error analyzing timestamps: {e}")
            return None

    def create_integration_plan(self, analysis_summary):
        """Create plan for integrating with existing analysis"""
        if analysis_summary is None:
            return

        print(f"\n📋 INTEGRATION PLAN")
        print("="*50)

        print(f"📊 NEW DATA SUMMARY:")
        print(f"• Total new records: {analysis_summary['total_records']:,}")
        print(f"• Post-change records: {analysis_summary['post_change_records']:,}")
        print(f"• Additional coverage days: {analysis_summary['days_coverage']}")

        print(f"\n🔄 INTEGRATION STEPS:")
        print("1. ✅ New data processed and saved")
        print("2. 🔄 Run GPS analysis pipeline on new data")
        print("3. 🔄 Update comprehensive_gps_metrics.csv")
        print("4. 🔄 Update comprehensive_gps_events.csv")
        print("5. 🔄 Re-run economic impact analysis")
        print("6. 🔄 Update spatial risk analysis")
        print("7. 🔄 Generate updated reports")

        # Check existing files
        existing_files = {
            'comprehensive_gps_metrics.csv': 'GPS metrics dataset',
            'comprehensive_gps_events.csv': 'Detected driving events',
            'our_economic_impact_report.csv': 'Economic analysis results'
        }

        print(f"\n📁 EXISTING FILES TO UPDATE:")
        for filename, description in existing_files.items():
            filepath = os.path.join(self.output_dir, filename)
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                print(f"• ✅ {filename} ({size:,} bytes) - {description}")
            else:
                print(f"• ❌ {filename} - {description} (MISSING)")

def main():
    processor = NewCVDataProcessor()

    # Process all new files
    combined_data = processor.process_all_new_files()

    if combined_data is not None:
        # Analyze temporal coverage
        analysis = processor.analyze_temporal_coverage(combined_data)

        # Create integration plan
        processor.create_integration_plan(analysis)

        print(f"\n✅ NEW DATA PROCESSING COMPLETE!")
        print(f"Next step: Run GPS analysis pipeline on the new data")
        print(f"Command: python scripts/analysis/comprehensive_gps_analysis.py")

    else:
        print(f"\n❌ PROCESSING FAILED")
        print("Please check file locations and try again")

if __name__ == "__main__":
    main()
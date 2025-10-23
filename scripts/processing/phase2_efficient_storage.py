#!/usr/bin/env python3
"""
Phase 2: Efficient Storage Strategy
====================================
Convert CSV files to optimized Parquet format using DuckDB

Standards: Production-grade, memory-efficient, complete audit trail
Technology: DuckDB (in-process SQL) + Parquet (columnar storage)
"""

import duckdb
import pandas as pd
import os
from datetime import datetime
from glob import glob
import json

class EfficientStorageProcessor:
    def __init__(self, data_dir, output_dir):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.audit_log = []

        # Create output directories
        os.makedirs(os.path.join(output_dir, "trip_level"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "quality_assurance"), exist_ok=True)

        print("="*80)
        print("PHASE 2: EFFICIENT STORAGE STRATEGY")
        print("="*80)
        print(f"Input directory:  {data_dir}")
        print(f"Output directory: {output_dir}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    def log_event(self, event_type, message, details=None):
        """Add event to audit trail"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'message': message,
            'details': details or {}
        }
        self.audit_log.append(event)
        print(f"[{event_type}] {message}")

    def get_csv_files(self):
        """Get list of all CSV files"""
        csv_files = sorted(glob(os.path.join(self.data_dir, "*.csv")))
        self.log_event("INFO", f"Found {len(csv_files)} CSV files")
        return csv_files

    def create_all_trips_parquet(self, csv_files):
        """
        Step 2.1: Load all CSV files into single Parquet file using DuckDB

        Benefits:
        - DuckDB handles memory efficiently (streams data)
        - Parquet provides 5-10x compression
        - Preserves data types
        - Fast columnar operations
        """
        print("\n" + "="*80)
        print("STEP 2.1: CONVERTING ALL CSVs TO PARQUET")
        print("="*80 + "\n")

        output_file = os.path.join(self.output_dir, "trip_level", "all_trips.parquet")

        # Connect to DuckDB (in-memory)
        conn = duckdb.connect()

        self.log_event("START", "Beginning CSV to Parquet conversion")
        start_time = datetime.now()

        try:
            # Create a view that reads all CSV files
            # DuckDB can read multiple CSV files efficiently
            print("Creating unified view of all CSV files...")

            # Read all CSVs into DuckDB (streaming, memory-efficient)
            conn.execute("""
                CREATE TABLE all_trips AS
                SELECT * FROM read_csv_auto(?,
                    union_by_name=true,
                    ignore_errors=false,
                    header=true
                )
            """, [f"{self.data_dir}/*.csv"])

            # Get row count
            row_count = conn.execute("SELECT COUNT(*) FROM all_trips").fetchone()[0]
            self.log_event("INFO", f"Loaded {row_count:,} trips from CSV files")

            # Get column info
            columns = conn.execute("DESCRIBE all_trips").fetchall()
            col_names = [col[0] for col in columns]
            self.log_event("INFO", f"Schema has {len(col_names)} columns: {', '.join(col_names[:5])}...")

            # Export to Parquet (highly compressed)
            print(f"\nWriting to Parquet: {output_file}")
            conn.execute(f"""
                COPY all_trips TO '{output_file}'
                (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000)
            """)

            # Get file size
            file_size_mb = os.path.getsize(output_file) / (1024**2)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self.log_event("SUCCESS", "Parquet conversion complete", {
                'output_file': output_file,
                'row_count': row_count,
                'file_size_mb': round(file_size_mb, 2),
                'duration_seconds': round(duration, 1),
                'compression': 'ZSTD'
            })

            print(f"\n✅ Conversion complete!")
            print(f"   Rows: {row_count:,}")
            print(f"   Size: {file_size_mb:.1f} MB")
            print(f"   Time: {duration:.1f} seconds")

            conn.close()
            return output_file, row_count

        except Exception as e:
            self.log_event("ERROR", f"Conversion failed: {str(e)}")
            conn.close()
            raise

    def validate_parquet_integrity(self, parquet_file, expected_rows):
        """
        Step 2.2: Validate Parquet file integrity
        """
        print("\n" + "="*80)
        print("STEP 2.2: VALIDATING PARQUET INTEGRITY")
        print("="*80 + "\n")

        conn = duckdb.connect()

        try:
            # Check row count
            actual_rows = conn.execute(f"SELECT COUNT(*) FROM '{parquet_file}'").fetchone()[0]

            if actual_rows == expected_rows:
                self.log_event("PASS", f"Row count matches: {actual_rows:,} rows")
            else:
                self.log_event("FAIL", f"Row count mismatch: expected {expected_rows:,}, got {actual_rows:,}")
                raise ValueError("Data integrity check failed: row count mismatch")

            # Check for nulls in critical columns
            null_check = conn.execute(f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN TripID IS NULL THEN 1 ELSE 0 END) as null_tripid,
                    SUM(CASE WHEN VehicleID IS NULL THEN 1 ELSE 0 END) as null_vehicleid,
                    SUM(CASE WHEN StartDate IS NULL THEN 1 ELSE 0 END) as null_startdate,
                    SUM(CASE WHEN RawPath IS NULL THEN 1 ELSE 0 END) as null_rawpath
                FROM '{parquet_file}'
            """).fetchone()

            print(f"Null value checks:")
            print(f"  TripID nulls:    {null_check[1]:,}")
            print(f"  VehicleID nulls: {null_check[2]:,}")
            print(f"  StartDate nulls: {null_check[3]:,}")
            print(f"  RawPath nulls:   {null_check[4]:,}")

            # Check schema
            schema = conn.execute(f"DESCRIBE SELECT * FROM '{parquet_file}'").fetchall()
            col_count = len(schema)
            self.log_event("INFO", f"Schema validated: {col_count} columns")

            print(f"\n✅ Integrity validation passed")

            conn.close()
            return True

        except Exception as e:
            self.log_event("ERROR", f"Validation failed: {str(e)}")
            conn.close()
            raise

    def create_initial_statistics(self, parquet_file):
        """
        Step 2.3: Generate statistical summary of all data
        """
        print("\n" + "="*80)
        print("STEP 2.3: GENERATING STATISTICAL SUMMARY")
        print("="*80 + "\n")

        conn = duckdb.connect()

        try:
            # Basic statistics
            stats = conn.execute(f"""
                SELECT
                    COUNT(*) as total_trips,
                    COUNT(DISTINCT VehicleID) as unique_vehicles,
                    COUNT(DISTINCT TripID) as unique_trips,
                    AVG(TravelTimeMinutes) as avg_travel_time,
                    AVG(TravelDistanceMetres) as avg_distance
                FROM '{parquet_file}'
            """).fetchone()

            print(f"Dataset Statistics:")
            print(f"  Total trips:       {stats[0]:,}")
            print(f"  Unique vehicles:   {stats[1]:,}")
            print(f"  Unique trip IDs:   {stats[2]:,}")
            print(f"  Avg travel time:   {stats[3]:.2f} minutes")
            print(f"  Avg distance:      {stats[4]:.1f} meters")

            # Save statistics
            stats_file = os.path.join(self.output_dir, "quality_assurance", "phase2_statistics.json")
            stats_dict = {
                'total_trips': int(stats[0]),
                'unique_vehicles': int(stats[1]),
                'unique_trip_ids': int(stats[2]),
                'avg_travel_time_minutes': float(stats[3]) if stats[3] else None,
                'avg_distance_meters': float(stats[4]) if stats[4] else None,
                'timestamp': datetime.now().isoformat()
            }

            with open(stats_file, 'w') as f:
                json.dump(stats_dict, f, indent=2)

            self.log_event("INFO", f"Statistics saved to {stats_file}")

            print(f"\n✅ Statistics generated and saved")

            conn.close()
            return stats_dict

        except Exception as e:
            self.log_event("ERROR", f"Statistics generation failed: {str(e)}")
            conn.close()
            raise

    def save_audit_trail(self):
        """Save complete audit trail"""
        audit_file = os.path.join(self.output_dir, "quality_assurance", "phase2_audit_trail.json")

        with open(audit_file, 'w') as f:
            json.dump({
                'phase': 'Phase 2: Efficient Storage',
                'timestamp': datetime.now().isoformat(),
                'events': self.audit_log
            }, f, indent=2)

        print(f"\n✅ Audit trail saved: {audit_file}")

    def run_phase2(self):
        """Execute complete Phase 2 pipeline"""
        start_time = datetime.now()

        try:
            # Step 1: Get all CSV files
            csv_files = self.get_csv_files()

            if len(csv_files) != 1500:
                raise ValueError(f"Expected 1,500 CSV files, found {len(csv_files)}")

            # Step 2.1: Convert to Parquet
            parquet_file, row_count = self.create_all_trips_parquet(csv_files)

            # Step 2.2: Validate integrity
            self.validate_parquet_integrity(parquet_file, row_count)

            # Step 2.3: Generate statistics
            stats = self.create_initial_statistics(parquet_file)

            # Save audit trail
            self.save_audit_trail()

            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()

            print("\n" + "="*80)
            print("PHASE 2 COMPLETE")
            print("="*80)
            print(f"Total processing time: {total_duration:.1f} seconds")
            print(f"Output: {parquet_file}")
            print(f"Trips processed: {row_count:,}")
            print(f"\n✅ Ready for Phase 3: Corridor Filtering")

            return True

        except Exception as e:
            self.log_event("CRITICAL", f"Phase 2 failed: {str(e)}")
            self.save_audit_trail()
            print(f"\n❌ Phase 2 failed: {str(e)}")
            return False


def main():
    """Execute Phase 2"""
    data_dir = "/Volumes/T7/Data/connected_vehicle_data/raw_files/additional_data"
    output_dir = "/Volumes/T7/Data/connected_vehicle_data/output/processed_data"

    processor = EfficientStorageProcessor(data_dir, output_dir)
    success = processor.run_phase2()

    if success:
        print("\n🎯 PROCEED TO PHASE 3: Corridor Definition & Filtering")
        return 0
    else:
        print("\n⛔ Phase 2 failed - review logs")
        return 1


if __name__ == "__main__":
    exit(main())

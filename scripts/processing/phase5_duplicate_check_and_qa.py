"""
Phase 5: Duplicate Check and QA Validation
=============================================
Checks for TripID duplicates between datasets and performs comprehensive QA validation
on the newly created point-level data.

Author: Data Processing Pipeline
Date: 2025-10-21
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

def print_header(title):
    """Print formatted section header"""
    print(f"\n{'='*80}")
    print(f"{title:^80}")
    print(f"{'='*80}\n")

def check_tripid_duplicates(base_dir):
    """Check for TripID duplicates across all datasets"""
    print_header("PHASE 5: DUPLICATE CHECK & QA VALIDATION")

    # Define file paths
    all_trips_path = base_dir / "output/processed_data/trip_level/all_trips.parquet"
    corridor_trips_path = base_dir / "output/processed_data/trip_level/corridor_trips.parquet"
    corridor_points_path = base_dir / "output/processed_data/point_level/corridor_gps_points.parquet"
    integrated_path = base_dir / "output/processed_data/integrated_trip_summary.parquet"

    print("📂 Loading datasets...")
    print(f"  - all_trips.parquet")
    print(f"  - corridor_trips.parquet")
    print(f"  - corridor_gps_points.parquet")
    print(f"  - integrated_trip_summary.parquet (if exists)")

    # Load TripIDs from each dataset (only TripID column for memory efficiency)
    results = {}

    # All trips
    if all_trips_path.exists():
        df_all = pd.read_parquet(all_trips_path, columns=['TripID'])
        results['all_trips'] = set(df_all['TripID'].unique())
        print(f"\n✅ all_trips.parquet: {len(results['all_trips']):,} unique TripIDs")
        all_trips_count = len(df_all)
        all_trips_unique = len(results['all_trips'])
        if all_trips_count != all_trips_unique:
            print(f"   ⚠️  WARNING: {all_trips_count - all_trips_unique:,} duplicate TripIDs within all_trips")
        del df_all  # Free memory

    # Corridor trips
    if corridor_trips_path.exists():
        df_corridor = pd.read_parquet(corridor_trips_path, columns=['TripID'])
        results['corridor_trips'] = set(df_corridor['TripID'].unique())
        print(f"✅ corridor_trips.parquet: {len(results['corridor_trips']):,} unique TripIDs")
        corridor_count = len(df_corridor)
        corridor_unique = len(results['corridor_trips'])
        if corridor_count != corridor_unique:
            print(f"   ⚠️  WARNING: {corridor_count - corridor_unique:,} duplicate TripIDs within corridor_trips")
        del df_corridor  # Free memory

    # Point-level data - only load TripID for duplicate check
    if corridor_points_path.exists():
        print(f"✅ Loading TripIDs from corridor_gps_points.parquet...")
        df_points_tripid = pd.read_parquet(corridor_points_path, columns=['TripID'])
        results['corridor_points'] = set(df_points_tripid['TripID'].unique())
        total_points = len(df_points_tripid)
        print(f"   📍 Total GPS points: {total_points:,}")
        print(f"   🔑 Unique TripIDs: {len(results['corridor_points']):,}")
        del df_points_tripid  # Free memory before loading full data

    # Integrated summary (if exists)
    if integrated_path.exists():
        df_integrated = pd.read_parquet(integrated_path, columns=['TripID'])
        results['integrated'] = set(df_integrated['TripID'].unique())
        print(f"✅ integrated_trip_summary.parquet: {len(results['integrated']):,} unique TripIDs")
        del df_integrated  # Free memory

    # Check for overlaps
    print_header("DUPLICATE CHECK RESULTS")

    duplicates_found = False

    # Check if corridor_trips is subset of all_trips
    if 'all_trips' in results and 'corridor_trips' in results:
        not_in_all = results['corridor_trips'] - results['all_trips']
        if not_in_all:
            print(f"⚠️  WARNING: {len(not_in_all):,} TripIDs in corridor_trips NOT found in all_trips")
            print(f"   Sample: {list(not_in_all)[:5]}")
            duplicates_found = True
        else:
            print(f"✅ All corridor_trips TripIDs exist in all_trips (expected)")

    # Check if corridor_points TripIDs match corridor_trips
    if 'corridor_trips' in results and 'corridor_points' in results:
        not_in_trips = results['corridor_points'] - results['corridor_trips']
        not_in_points = results['corridor_trips'] - results['corridor_points']

        if not_in_trips:
            print(f"⚠️  WARNING: {len(not_in_trips):,} TripIDs in points NOT in corridor_trips")
            print(f"   Sample: {list(not_in_trips)[:5]}")
            duplicates_found = True

        if not_in_points:
            print(f"⚠️  WARNING: {len(not_in_points):,} TripIDs in corridor_trips NOT expanded to points")
            print(f"   Sample: {list(not_in_points)[:5]}")
            duplicates_found = True

        if not not_in_trips and not not_in_points:
            print(f"✅ corridor_points and corridor_trips TripIDs match perfectly")

    # Check integrated summary alignment
    if 'integrated' in results and 'corridor_points' in results:
        overlap = results['integrated'] & results['corridor_points']
        if overlap:
            print(f"⚠️  POTENTIAL ISSUE: {len(overlap):,} TripIDs exist in BOTH integrated_summary and corridor_points")
            print(f"   This could indicate duplicate analysis if both are used together")
            print(f"   Sample overlapping TripIDs: {list(overlap)[:5]}")
            duplicates_found = True
        else:
            print(f"✅ No overlap between integrated_summary and corridor_points (good)")

    if not duplicates_found:
        print("\n🎉 No duplicate issues found!")

    # Return results and path (not the dataframe to save memory)
    return results, corridor_points_path if corridor_points_path.exists() else None

def comprehensive_qa_validation(points_path, base_dir):
    """Run comprehensive QA checks on point-level data"""
    print_header("COMPREHENSIVE QA VALIDATION")

    qa_results = {
        'total_checks': 0,
        'passed': 0,
        'warnings': 0,
        'failures': 0,
        'details': []
    }

    def add_check(name, passed, message, level='info'):
        qa_results['total_checks'] += 1
        if level == 'pass':
            qa_results['passed'] += 1
            status = "✅"
        elif level == 'warning':
            qa_results['warnings'] += 1
            status = "⚠️ "
        else:
            qa_results['failures'] += 1
            status = "❌"

        qa_results['details'].append({
            'name': name,
            'passed': passed,
            'message': message,
            'level': level
        })
        print(f"{status} {name}: {message}")

    print("Running QA checks on corridor_gps_points.parquet...\n")
    print("📊 Loading data in chunks for memory efficiency...\n")

    # Load the full dataset (we need it for QA checks)
    df_points = pd.read_parquet(points_path)
    total_rows = len(df_points)

    # Check 1: Row count
    add_check(
        "Total Rows",
        total_rows > 0,
        f"{total_rows:,} GPS points",
        'pass' if total_rows > 10_000_000 else 'warning'
    )

    # Check 2: Required columns
    required_cols = ['TripID', 'Point_RawTimestamp', 'Point_RawLat', 'Point_RawLon', 'Point_Speed', 'Trip_DistanceMetres']
    missing_cols = [col for col in required_cols if col not in df_points.columns]
    add_check(
        "Required Columns",
        len(missing_cols) == 0,
        f"All required columns present" if not missing_cols else f"Missing: {missing_cols}",
        'pass' if not missing_cols else 'failure'
    )

    # Log available columns for reference
    print(f"\n   Available columns: {', '.join(df_points.columns)}")

    # Check 3: Null values
    print("\n📊 Null Value Analysis:")
    for col in df_points.columns:
        null_count = df_points[col].isnull().sum()
        null_pct = (null_count / total_rows) * 100
        if null_count > 0:
            add_check(
                f"  Nulls in {col}",
                null_pct < 1,
                f"{null_count:,} nulls ({null_pct:.2f}%)",
                'warning' if null_pct < 5 else 'failure'
            )

    # Check 4: Coordinate validity
    invalid_lat = ((df_points['Point_RawLat'] < -90) | (df_points['Point_RawLat'] > 90)).sum()
    invalid_lon = ((df_points['Point_RawLon'] < -180) | (df_points['Point_RawLon'] > 180)).sum()
    add_check(
        "Latitude Range",
        invalid_lat == 0,
        f"All valid" if invalid_lat == 0 else f"{invalid_lat:,} invalid coordinates",
        'pass' if invalid_lat == 0 else 'failure'
    )
    add_check(
        "Longitude Range",
        invalid_lon == 0,
        f"All valid" if invalid_lon == 0 else f"{invalid_lon:,} invalid coordinates",
        'pass' if invalid_lon == 0 else 'failure'
    )

    # Check 5: Speed validity
    invalid_speed = (df_points['Point_Speed'] < 0).sum()
    max_speed = df_points['Point_Speed'].max()
    add_check(
        "Speed Range",
        invalid_speed == 0 and max_speed < 200,
        f"Valid (max: {max_speed:.1f} km/h)" if invalid_speed == 0 else f"{invalid_speed:,} negative speeds",
        'pass' if invalid_speed == 0 and max_speed < 200 else 'warning'
    )

    # Check 6: Period distribution (if period column exists)
    if 'period' in df_points.columns:
        print("\n📅 Period Distribution:")
        period_counts = df_points['period'].value_counts()
        for period in ['before', 'after']:
            if period in period_counts:
                count = period_counts[period]
                pct = (count / total_rows) * 100
                add_check(
                    f"  {period.capitalize()} Period",
                    count > 100_000,
                    f"{count:,} points ({pct:.1f}%)",
                    'pass' if count > 1_000_000 else 'warning'
                )
    else:
        add_check(
            "Period Column",
            False,
            "Period column not found - will need to be added for before/after analysis",
            'warning'
        )

    # Check 7: TripID distribution
    unique_trips = df_points['TripID'].nunique()
    avg_points_per_trip = total_rows / unique_trips if unique_trips > 0 else 0
    add_check(
        "Unique Trips",
        unique_trips > 50_000,
        f"{unique_trips:,} trips (avg {avg_points_per_trip:.1f} points/trip)",
        'pass' if unique_trips > 50_000 else 'warning'
    )

    # Check 8: Time consistency
    print("\n⏰ Temporal Consistency:")
    # Sample for performance
    sample_size = min(100000, len(df_points))
    df_points_sample = df_points.sample(sample_size)
    df_points_sample = df_points_sample.copy()
    df_points_sample['time_parsed'] = pd.to_datetime(df_points_sample['Point_RawTimestamp'], errors='coerce')
    time_sorted = df_points_sample.groupby('TripID')['Point_Sequence'].apply(lambda x: x.is_monotonic_increasing).all()
    add_check(
        "Time Ordering (by sequence)",
        time_sorted,
        f"Point sequences monotonically increasing within trips (sample of {sample_size:,})" if time_sorted else "Some trips have non-monotonic sequences",
        'pass' if time_sorted else 'warning'
    )

    # Check 9: Geographic consistency (NZ bounds)
    nz_lat_min, nz_lat_max = -47, -34
    nz_lon_min, nz_lon_max = 166, 179
    in_nz = ((df_points['Point_RawLat'] >= nz_lat_min) & (df_points['Point_RawLat'] <= nz_lat_max) &
             (df_points['Point_RawLon'] >= nz_lon_min) & (df_points['Point_RawLon'] <= nz_lon_max)).sum()
    in_nz_pct = (in_nz / total_rows) * 100
    add_check(
        "NZ Geographic Bounds",
        in_nz_pct > 95,
        f"{in_nz:,} points in NZ bounds ({in_nz_pct:.1f}%)",
        'pass' if in_nz_pct > 99 else 'warning'
    )

    # Check 10: Distance consistency (trip-level)
    if 'Trip_DistanceMetres' in df_points.columns:
        zero_distance_trips = (df_points['Trip_DistanceMetres'] == 0).sum()
        zero_distance_pct = (zero_distance_trips / total_rows) * 100
        add_check(
            "Trip Distance Values",
            zero_distance_pct < 10,
            f"{zero_distance_trips:,} points with zero-distance trips ({zero_distance_pct:.1f}%)",
            'pass' if zero_distance_pct < 5 else 'warning'
        )

    # Summary
    print_header("QA VALIDATION SUMMARY")
    print(f"Total Checks: {qa_results['total_checks']}")
    print(f"✅ Passed: {qa_results['passed']}")
    print(f"⚠️  Warnings: {qa_results['warnings']}")
    print(f"❌ Failures: {qa_results['failures']}")

    score = (qa_results['passed'] / qa_results['total_checks']) * 100
    print(f"\n📊 QA Score: {score:.1f}%")

    if qa_results['failures'] == 0:
        print("\n🎉 All critical checks passed!")
    else:
        print(f"\n⚠️  {qa_results['failures']} critical issue(s) need attention")

    return qa_results

def generate_qa_report(qa_results, base_dir):
    """Generate a detailed QA report file"""
    report_path = base_dir / "output/quality_assurance/phase5_qa_report.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w') as f:
        f.write("="*80 + "\n")
        f.write("PHASE 5: QA VALIDATION REPORT\n")
        f.write("="*80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write(f"Total Checks: {qa_results['total_checks']}\n")
        f.write(f"Passed: {qa_results['passed']}\n")
        f.write(f"Warnings: {qa_results['warnings']}\n")
        f.write(f"Failures: {qa_results['failures']}\n\n")

        score = (qa_results['passed'] / qa_results['total_checks']) * 100
        f.write(f"QA Score: {score:.1f}%\n\n")

        f.write("-"*80 + "\n")
        f.write("DETAILED RESULTS\n")
        f.write("-"*80 + "\n\n")

        for detail in qa_results['details']:
            status_icon = "✅" if detail['level'] == 'pass' else ("⚠️ " if detail['level'] == 'warning' else "❌")
            f.write(f"{status_icon} {detail['name']}\n")
            f.write(f"   {detail['message']}\n\n")

    print(f"\n📄 QA Report saved to: {report_path}")
    return report_path

def main():
    """Main execution function"""
    base_dir = Path("/Volumes/T7/Data/connected_vehicle_data")

    print(f"Starting Phase 5: Duplicate Check & QA Validation")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Step 1: Check for duplicates
    duplicate_results, points_path = check_tripid_duplicates(base_dir)

    # Step 2: Run comprehensive QA
    if points_path is not None:
        qa_results = comprehensive_qa_validation(points_path, base_dir)

        # Step 3: Generate report
        report_path = generate_qa_report(qa_results, base_dir)

        print_header("PHASE 5 COMPLETE")
        print("✅ Duplicate check complete")
        print("✅ QA validation complete")
        print(f"✅ Report generated: {report_path}")
        print("\nReady to proceed with integration!")
    else:
        print("\n❌ Error: Could not find corridor_gps_points.parquet")
        sys.exit(1)

if __name__ == "__main__":
    main()

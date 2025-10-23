"""
Phase 5B: Add Period Column
============================
Add 'period' column (before/after) to point-level data based on speed limit change date.

Speed limit change: April 13, 2025
- before: trips starting before 2025-04-13
- after: trips starting on or after 2025-04-13

Author: Data Processing Pipeline
Date: 2025-10-21
"""

import pandas as pd
from datetime import datetime
from pathlib import Path

def add_period_column():
    """Add period column to corridor_gps_points.parquet"""

    print("="*80)
    print("PHASE 5B: ADDING PERIOD COLUMN TO POINT-LEVEL DATA")
    print("="*80)

    # Configuration
    base_dir = Path("/Volumes/T7/Data/connected_vehicle_data")
    input_file = base_dir / "output/processed_data/point_level/corridor_gps_points.parquet"
    output_file = base_dir / "output/processed_data/point_level/corridor_gps_points_with_period.parquet"
    backup_file = base_dir / "output/processed_data/point_level/corridor_gps_points_backup.parquet"

    # Speed limit change date
    change_date = pd.to_datetime('2025-04-13')

    print(f"\n📅 Speed Limit Change Date: {change_date.date()}")
    print(f"📂 Input:  {input_file}")
    print(f"📂 Output: {output_file}")
    print(f"📂 Backup: {backup_file}")

    # Load data
    print("\n📊 Loading point-level data...")
    df = pd.read_parquet(input_file)
    print(f"   Loaded: {len(df):,} GPS points")

    # Create backup
    print(f"\n💾 Creating backup...")
    df.to_parquet(backup_file, index=False)
    print(f"   ✅ Backup saved: {backup_file}")

    # Parse TripStartTime and determine period
    print(f"\n🔍 Parsing TripStartTime and determining period...")
    df['TripStartTime_parsed'] = pd.to_datetime(df['TripStartTime'], errors='coerce', utc=True)

    # Make change_date timezone-aware (UTC)
    change_date_tz = pd.to_datetime('2025-04-13', utc=True)

    # Classify period
    df['period'] = df['TripStartTime_parsed'].apply(
        lambda x: 'before' if pd.notna(x) and x < change_date_tz else 'after'
    )

    # Handle any parsing errors
    parsing_errors = df['TripStartTime_parsed'].isna().sum()
    if parsing_errors > 0:
        print(f"   ⚠️  Warning: {parsing_errors:,} trips had unparseable timestamps (defaulted to 'after')")

    # Drop the temporary parsed column
    df = df.drop(columns=['TripStartTime_parsed'])

    # Summary statistics
    print(f"\n📈 Period Distribution:")
    period_counts = df['period'].value_counts()
    total_points = len(df)

    for period in ['before', 'after']:
        if period in period_counts:
            count = period_counts[period]
            pct = (count / total_points) * 100
            unique_trips = df[df['period'] == period]['TripID'].nunique()
            print(f"   {period.upper()}: {count:,} points ({pct:.1f}%) from {unique_trips:,} trips")

    # Save updated data
    print(f"\n💾 Saving updated data...")
    df.to_parquet(output_file, index=False)
    print(f"   ✅ Saved: {output_file}")

    # Verify
    print(f"\n✅ Verification:")
    df_verify = pd.read_parquet(output_file)
    print(f"   Total points: {len(df_verify):,}")
    print(f"   Columns: {', '.join(df_verify.columns)}")
    print(f"   Period column present: {'period' in df_verify.columns}")

    # Replace original file
    print(f"\n🔄 Replacing original file...")
    import shutil
    shutil.move(str(output_file), str(input_file))
    print(f"   ✅ Original file updated: {input_file}")

    print("\n" + "="*80)
    print("PHASE 5B COMPLETE!")
    print("="*80)
    print(f"✅ Period column added successfully")
    print(f"✅ Backup available at: {backup_file}")
    print(f"✅ Original file updated with period information")
    print("\nReady for analysis integration!")

if __name__ == "__main__":
    add_period_column()

#!/usr/bin/env python3
"""
Analyze temporal and spatial coverage of sample data
"""

import pandas as pd
import re

# Read sample files
file_path1 = "/Volumes/T7/Data/connected_vehicle_data/raw_files/test_samples/support.NZ_report_withOD-90fb5e1c1dce2c282d53abd3-000000000000.csv"
file_path2 = "/Volumes/T7/Data/connected_vehicle_data/raw_files/test_samples/support.NZ_report_withOD-90fb5e1c1dce2c282d53abd3-000000000001.csv"
file_path3 = "/Volumes/T7/Data/connected_vehicle_data/raw_files/test_samples/support.NZ_report_withOD-90fb5e1c1dce2c282d53abd3-000000000002.csv"

print("="*80)
print("DATA STRUCTURE ANALYSIS")
print("="*80 + "\n")

# Read first file fully
df1 = pd.read_csv(file_path1)
df2 = pd.read_csv(file_path2)
df3 = pd.read_csv(file_path3)

# Combine
df_all = pd.concat([df1, df2, df3], ignore_index=True)

print(f"Total trips across 3 sample files: {len(df_all):,}")
print(f"Unique vehicles: {df_all['VehicleID'].nunique():,}")
print(f"Unique trips: {df_all['TripID'].nunique():,}\n")

# Parse first point location from RawPath to get coordinates
def extract_first_lat_lon(raw_path):
    """Extract first lat/lon from RawPath string"""
    if pd.isna(raw_path):
        return None, None
    try:
        # Format is "lon lat,lon lat,..."
        first_point = raw_path.split(',')[0].strip()
        parts = first_point.split()
        if len(parts) == 2:
            lon, lat = float(parts[0]), float(parts[1])
            return lat, lon
    except:
        pass
    return None, None

# Extract coordinates from a sample
sample_coords = []
for _, row in df_all.head(100).iterrows():
    lat, lon = extract_first_lat_lon(row['RawPath'])
    if lat is not None:
        sample_coords.append((lat, lon))

if sample_coords:
    lats = [c[0] for c in sample_coords]
    lons = [c[1] for c in sample_coords]
    print("="*80)
    print("SPATIAL COVERAGE (from 100 trip samples)")
    print("="*80)
    print(f"Latitude range:  {min(lats):.6f} to {max(lats):.6f}")
    print(f"Longitude range: {min(lons):.6f} to {max(lons):.6f}")

    # Christchurch coordinates for reference
    # SH1/SH76 Southern Motorway is roughly:
    # Lat: -43.48 to -43.58
    # Lon: 172.55 to 172.65
    print(f"\nChristchurch SH1/SH76 reference:")
    print(f"  Latitude:  -43.58 to -43.48")
    print(f"  Longitude: 172.55 to 172.65")

    # Check if data overlaps with SH1/SH76
    in_lat_range = any(-43.58 <= lat <= -43.48 for lat in lats)
    in_lon_range = any(172.55 <= lon <= 172.65 for lon in lons)

    if in_lat_range and in_lon_range:
        print(f"\n✅ Data includes Christchurch SH1/SH76 area")
    else:
        print(f"\n⚠️  Data may not fully cover SH1/SH76 area")

    # Count how many are in the corridor
    in_corridor = sum(1 for lat, lon in sample_coords
                      if -43.58 <= lat <= -43.48 and 172.55 <= lon <= 172.65)
    print(f"   {in_corridor}/{len(sample_coords)} sample trips start in SH1/SH76 area")

print("\n" + "="*80)
print("TEMPORAL COVERAGE")
print("="*80)

# Parse start dates more carefully
df_all['start_dt'] = pd.to_datetime(df_all['StartDate'] + ' ' + df_all['StartTime'],
                                     errors='coerce', format='mixed', utc=True)

# Drop any that failed to parse
df_all = df_all.dropna(subset=['start_dt'])

print(f"\nSuccessfully parsed {len(df_all):,} trip timestamps")
print(f"Date range: {df_all['start_dt'].min().strftime('%Y-%m-%d')} to {df_all['start_dt'].max().strftime('%Y-%m-%d')}")

# Count by month
df_all['month'] = df_all['start_dt'].dt.to_period('M')
monthly_counts = df_all.groupby('month').size().sort_index()

print(f"\nTrips by month:")
for month, count in monthly_counts.items():
    print(f"  {month}: {count:,} trips")

# Speed limit change analysis
speed_change_date = pd.to_datetime('2025-04-13', utc=True)
before = df_all[df_all['start_dt'] < speed_change_date]
after = df_all[df_all['start_dt'] >= speed_change_date]

print(f"\n" + "="*80)
print("SPEED LIMIT CHANGE PERIOD ANALYSIS")
print("="*80)
print(f"Speed limit change date: April 13, 2025")
print(f"\nBEFORE period (< Apr 13):")
print(f"  Trips: {len(before):,}")
if len(before) > 0:
    print(f"  Date range: {before['start_dt'].min().strftime('%Y-%m-%d')} to {before['start_dt'].max().strftime('%Y-%m-%d')}")

print(f"\nAFTER period (>= Apr 13):")
print(f"  Trips: {len(after):,}")
if len(after) > 0:
    print(f"  Date range: {after['start_dt'].min().strftime('%Y-%m-%d')} to {after['start_dt'].max().strftime('%Y-%m-%d')}")

print(f"\n" + "="*80)
print("SPEED AND TRAVEL TIME STATISTICS")
print("="*80)

print(f"\nSpeed metrics:")
print(f"  Average speed: {df_all['SpeedAvg'].mean():.1f} km/h (mean across trips)")
print(f"  85th percentile speed: {df_all['Speed85P'].mean():.1f} km/h (mean across trips)")
print(f"  Max speed observed: {df_all['SpeedMax'].max():.1f} km/h")

print(f"\nTravel time metrics:")
print(f"  Average travel time: {df_all['TravelTimeMinutes'].mean():.1f} minutes")
print(f"  Median travel time: {df_all['TravelTimeMinutes'].median():.1f} minutes")

print(f"\nDistance metrics:")
print(f"  Average distance: {df_all['TravelDistanceMetres'].mean():.0f} meters")
print(f"  Median distance: {df_all['TravelDistanceMetres'].median():.0f} meters")

print("\n" + "="*80)
print("DATA FORMAT SUMMARY")
print("="*80)

# Check path lengths
first_trip = df_all.iloc[0]
timestamps = first_trip['TimestampPath'].split(',')
raw_points = first_trip['RawPath'].split(',')
speeds = first_trip['SpeedPath'].split(',')

print(f"\nFirst trip path details:")
print(f"  Number of timestamps: {len(timestamps)}")
print(f"  Number of GPS points: {len(raw_points)}")
print(f"  Number of speed readings: {len(speeds)}")
print(f"  Path data is synchronized: {len(timestamps) == len(raw_points) == len(speeds)}")

print("\n" + "="*80)

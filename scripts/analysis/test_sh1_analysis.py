"""
Quick test of SH1 Speed Analysis with minimal data
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

# Test with just the first few files
data_dir = "/Users/timwelch/Dropbox/Files/Research/Compass_Data/SH1_Study/Data/connected_vehicle_data"
parquet_dir = os.path.join(data_dir, "parquet_files")
speed_change_date = pd.to_datetime("2025-04-13")

print("🔍 Testing SH1 Analysis with minimal data...")

results = []

# Process just the first 3 parquet files
parquet_files = [f for f in sorted(os.listdir(parquet_dir)) 
                if f.endswith(".parquet") and f != "unique_trips_clean.parquet"][:3]

print(f"📂 Testing with files: {parquet_files}")

for filename in parquet_files:
    file_path = os.path.join(parquet_dir, filename)
    print(f"Processing {filename}...")
    
    try:
        df = pd.read_parquet(file_path, columns=[
            "TripID", "Point_RawTimestamp", "Point_Speed", 
            "point_acc_x", "Point_acc_y"
        ])
        
        print(f"  📊 Loaded {len(df)} rows, {len(df['TripID'].unique())} unique trips")
        
        # Process timestamps
        df["timestamp"] = pd.to_datetime(df["Point_RawTimestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"])
        df["period"] = df["timestamp"].apply(lambda x: "before" if x < speed_change_date else "after")
        
        print(f"  📅 Period breakdown: {df['period'].value_counts().to_dict()}")
        
        # Process first 10 trips only
        for trip_id in list(df["TripID"].unique())[:10]:
            trip_data = df[df["TripID"] == trip_id].copy()
            
            if len(trip_data) < 3:  
                continue
                
            trip_data = trip_data.sort_values("timestamp")
            
            # Basic metrics
            period = trip_data["period"].iloc[0]
            avg_speed = trip_data["Point_Speed"].mean()
            max_speed = trip_data["Point_Speed"].max()
            start_time = trip_data["timestamp"].iloc[0]
            
            results.append({
                "TripID": trip_id,
                "period": period,
                "trip_start": start_time,
                "avg_speed_kmh": avg_speed,
                "max_speed_kmh": max_speed,
                "data_points": len(trip_data)
            })
        
        print(f"  ✅ Processed {len([r for r in results if r['TripID'] in df['TripID'].unique()])} trips from this file")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")

# Analyze results
print(f"\n📊 ANALYSIS RESULTS")
print(f"Total trips processed: {len(results)}")

if results:
    df_results = pd.DataFrame(results)
    
    print("\nPeriod breakdown:")
    print(df_results['period'].value_counts())
    
    print("\nAverage speeds by period:")
    speed_by_period = df_results.groupby('period')['avg_speed_kmh'].agg(['mean', 'count'])
    print(speed_by_period.round(1))
    
    print(f"\nFirst few results:")
    print(df_results.head())
    
    # Save mini results
    output_path = os.path.join(parquet_dir, "test_results.csv")
    df_results.to_csv(output_path, index=False)
    print(f"\n💾 Test results saved to: {output_path}")

else:
    print("❌ No trips processed successfully")
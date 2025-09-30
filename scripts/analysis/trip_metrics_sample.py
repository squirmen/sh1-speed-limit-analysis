import os
import pandas as pd
import numpy as np
from datetime import datetime

# Path setup
parquet_dir = "/Users/timwelch/Dropbox/Files/Research/Compass_Data/SH1_Study/Data/connected_vehicle_data/parquet_files"
trip_summary_path = os.path.join(parquet_dir, "unique_trips_clean.parquet")

# Speed limit change date
SPEED_CHANGE_DATE = pd.to_datetime("2025-04-13")

# Load trip summary and pick a manageable sample
summary = pd.read_parquet(trip_summary_path)
sample_trips = summary.head(1000)["TripID"].tolist()

# Prepare results
results = []

print(f"Processing {len(sample_trips)} sample trips...")

# Loop through all Parquet files to collect trips
for filename in sorted(os.listdir(parquet_dir)):
    if not filename.endswith(".parquet"):
        continue
    if filename == "unique_trips_clean.parquet":
        continue  # Skip the summary file!

    file_path = os.path.join(parquet_dir, filename)
    print(f"Scanning {filename}...")

    df = pd.read_parquet(file_path, columns=[
        "TripID", "Point_RawTimestamp", "Point_Speed", "point_acc_x", "Point_acc_y", "Point_acc_z"
    ])
    
    # Filter for sample trips only
    df = df[df["TripID"].isin(sample_trips)]
    
    if len(df) == 0:
        continue
        
    # Process timestamp
    df["timestamp"] = pd.to_datetime(df["Point_RawTimestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    
    # Add before/after period
    df["period"] = df["timestamp"].apply(lambda x: "before" if x < SPEED_CHANGE_DATE else "after")
    
    # Process each trip in this file
    for trip_id in df["TripID"].unique():
        trip_data = df[df["TripID"] == trip_id].copy()
        
        if len(trip_data) < 5:  # Skip trips with too few points
            continue
            
        # Sort by timestamp
        trip_data = trip_data.sort_values("timestamp")
        
        # Calculate trip metrics
        duration = (trip_data["timestamp"].max() - trip_data["timestamp"].min()).total_seconds() / 60  # minutes
        avg_speed = trip_data["Point_Speed"].mean()
        max_speed = trip_data["Point_Speed"].max()
        speed_std = trip_data["Point_Speed"].std()
        
        # Speed adherence (assuming 110 km/h limit after change, estimate before)
        speed_limit = 100 if trip_data["period"].iloc[0] == "before" else 110
        speed_violations = (trip_data["Point_Speed"] > speed_limit).sum()
        speed_adherence = 1 - (speed_violations / len(trip_data))
        
        # Erratic driving indicators
        if len(trip_data) > 1:
            # Speed variability
            speed_changes = np.abs(trip_data["Point_Speed"].diff())
            rapid_speed_changes = (speed_changes > 10).sum()  # Changes > 10 km/h
            
            # Acceleration metrics (if available)
            acc_x_mean = trip_data["point_acc_x"].mean() if not trip_data["point_acc_x"].isna().all() else np.nan
            acc_y_mean = trip_data["Point_acc_y"].mean() if not trip_data["Point_acc_y"].isna().all() else np.nan
            
            # Hard acceleration/braking events
            hard_accel = (trip_data["point_acc_x"] > 2.0).sum() if not trip_data["point_acc_x"].isna().all() else 0
            hard_brake = (trip_data["point_acc_x"] < -2.0).sum() if not trip_data["point_acc_x"].isna().all() else 0
        else:
            rapid_speed_changes = 0
            acc_x_mean = acc_y_mean = np.nan
            hard_accel = hard_brake = 0
        
        # Time of day analysis
        hour = trip_data["timestamp"].iloc[0].hour
        if 6 <= hour < 9:
            time_period = "morning_peak"
        elif 16 <= hour < 19:
            time_period = "evening_peak"
        elif 9 <= hour < 16:
            time_period = "midday"
        else:
            time_period = "off_peak"
        
        # Store results
        results.append({
            "TripID": trip_id,
            "period": trip_data["period"].iloc[0],
            "trip_start": trip_data["timestamp"].min(),
            "trip_duration_min": duration,
            "avg_speed_kmh": avg_speed,
            "max_speed_kmh": max_speed,
            "speed_std": speed_std,
            "speed_limit": speed_limit,
            "speed_adherence_rate": speed_adherence,
            "speed_violations": speed_violations,
            "rapid_speed_changes": rapid_speed_changes,
            "acc_x_mean": acc_x_mean,
            "acc_y_mean": acc_y_mean,
            "hard_accel_events": hard_accel,
            "hard_brake_events": hard_brake,
            "time_period": time_period,
            "hour": hour,
            "data_points": len(trip_data)
        })

# Save results
results_df = pd.DataFrame(results)
output_path = os.path.join(parquet_dir, "trip_metrics_sample.csv")
results_df.to_csv(output_path, index=False)

print(f"\n✅ Sample trip metrics written to: {output_path}")
print(f"✅ Processed {len(results)} trips")
print(f"✅ Before period: {len(results_df[results_df['period']=='before'])} trips")
print(f"✅ After period: {len(results_df[results_df['period']=='after'])} trips")

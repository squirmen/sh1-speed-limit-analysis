import os
import pandas as pd

# Path to Parquet directory
parquet_dir = "/Users/timwelch/Dropbox/Files/Research/Compass_Data/SH1_Study/Data/connected_vehicle_data/parquet_files"
output_file = os.path.join(parquet_dir, "unique_trips_clean.parquet")

# Collect all rows: just TripID + Timestamp
all_chunks = []

for filename in sorted(os.listdir(parquet_dir)):
    if filename.endswith(".parquet"):
        full_path = os.path.join(parquet_dir, filename)
        print(f"Reading {filename}...")
        try:
            df = pd.read_parquet(full_path, columns=["TripID", "Point_RawTimestamp"])
            df["Timestamp"] = pd.to_datetime(df["Point_RawTimestamp"], errors="coerce")
            all_chunks.append(df[["TripID", "Timestamp"]])
        except Exception as e:
            print(f"Error reading {filename}: {e}")

# Combine into one DataFrame
combined_df = pd.concat(all_chunks, ignore_index=True)

# Group by TripID and reduce to one row per trip
print("Grouping trips...")
trip_summary = combined_df.groupby("TripID").agg(
    TripStartTime=("Timestamp", "min"),
    TripEndTime=("Timestamp", "max")
).reset_index()

# Save as compressed Parquet (MUCH smaller than CSV)
trip_summary.to_parquet(output_file, index=False)
print(f"\n✅ Saved {len(trip_summary)} unique trips to: {output_file}")

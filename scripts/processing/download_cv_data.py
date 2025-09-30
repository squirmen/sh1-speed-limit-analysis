import os
import pandas as pd

# Directory of your Parquet files
parquet_dir = "/Users/timwelch/Dropbox/Files/Research/Compass_Data/SH1_Study/Data/connected_vehicle_data/parquet_files"
output_path = os.path.join(parquet_dir, "unique_trips.csv")

all_points = []

# Loop through each Parquet file
for filename in sorted(os.listdir(parquet_dir)):
    if filename.endswith(".parquet"):
        filepath = os.path.join(parquet_dir, filename)
        print(f"Reading {filename}...")
        try:
            df = pd.read_parquet(filepath, columns=["TripID", "Point_RawTimestamp"])
            df["Timestamp"] = pd.to_datetime(df["Point_RawTimestamp"], errors="coerce")
            all_points.append(df[["TripID", "Timestamp"]])
        except Exception as e:
            print(f"Error in {filename}: {e}")

# Combine all trip points into one DataFrame
combined = pd.concat(all_points, ignore_index=True)

# Now aggregate full start/end times across all files
summary = combined.groupby("TripID").agg(
    TripStartTime=("Timestamp", "min"),
    TripEndTime=("Timestamp", "max")
).reset_index()

summary.to_csv(output_path, index=False)
print(f"\n✅ Combined trip summary written to: {output_path}")
print(f"✅ Unique trips: {len(summary)}")

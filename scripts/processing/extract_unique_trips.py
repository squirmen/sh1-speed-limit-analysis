import os
import pandas as pd

# Paths
parquet_dir = "/Users/timwelch/Dropbox/Files/Research/Compass_Data/SH1_Study/Data/connected_vehicle_data/parquet_files"
output_path = os.path.join(parquet_dir, "unique_trips.csv")

# Init list to collect summary
trip_summaries = []

# Loop through Parquet files
for filename in sorted(os.listdir(parquet_dir)):
    if filename.endswith(".parquet"):
        filepath = os.path.join(parquet_dir, filename)
        print(f"Processing {filename}...")

        try:
            # Read only what's needed
            df = pd.read_parquet(filepath, columns=["TripID", "Point_RawTimestamp"])

            # Convert timestamp from string to datetime
            df["Timestamp"] = pd.to_datetime(df["Point_RawTimestamp"], errors="coerce")

            # Aggregate first and last timestamp for each trip
            summary = df.groupby("TripID").agg(
                TripStartTime=("Timestamp", "min"),
                TripEndTime=("Timestamp", "max")
            ).reset_index()

            summary["source_file"] = filename
            trip_summaries.append(summary)

        except Exception as e:
            print(f"Error reading {filename}: {e}")

# Combine and save
all_trips = pd.concat(trip_summaries, ignore_index=True)
all_trips.to_csv(output_path, index=False)
print(f"\n✅ Unique trip summary saved to {output_path}")

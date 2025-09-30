import pandas as pd

# Adjust to any small .parquet file you've already converted
filepath = "/Users/timwelch/Dropbox/Files/Research/Compass_Data/SH1_Study/Data/connected_vehicle_data/parquet_files/support.nz_gettingdistance-fafb97a7d07df2990ff2ffa0-000000000000.parquet"

df = pd.read_parquet(filepath)

# Preview raw timestamp
print("RAW TIMESTAMP SAMPLE:")
print(df["Point_RawTimestamp"].head())

# Try parsing timestamp
try:
    df["Timestamp"] = pd.to_datetime(df["Point_RawTimestamp"], errors="coerce")
except Exception:
    df["Timestamp"] = pd.to_datetime(df["Point_RawTimestamp"], unit='ms', errors="coerce")

print("\nPARSED TIMESTAMP SAMPLE:")
print(df["Timestamp"].describe())

# Now group and check trip summary
summary = df.groupby("TripID").agg(
    TripStartTime=("Timestamp", "min"),
    TripEndTime=("Timestamp", "max")
).reset_index()

print("\nTRIP SUMMARY SAMPLE:")
print(summary.head())
print(f"\nUnique trips found: {len(summary)}")
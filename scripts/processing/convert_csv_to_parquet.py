import os
import pandas as pd

# Paths
input_dir = "/Users/timwelch/Dropbox/Files/Research/Compass_Data/SH1_Study/Data/connected_vehicle_data"
output_dir = os.path.join(input_dir, "parquet_files")
os.makedirs(output_dir, exist_ok=True)

# Loop over files 000–999
for i in range(1000):
    file_suffix = str(i).zfill(12)
    csv_file = f"support.nz_gettingdistance-fafb97a7d07df2990ff2ffa0-{file_suffix}.csv"
    csv_path = os.path.join(input_dir, csv_file)

    if os.path.exists(csv_path):
        print(f"Processing {csv_file}...")
        try:
            df = pd.read_csv(csv_path)
            parquet_file = csv_file.replace(".csv", ".parquet")
            parquet_path = os.path.join(output_dir, parquet_file)
            df.to_parquet(parquet_path, index=False)
        except Exception as e:
            print(f"Failed to process {csv_file}: {e}")
    else:
        print(f"Skipped missing file {csv_file}")
#!/usr/bin/env python3
"""
Download Additional Connected Vehicle Data
Downloads 2500 CSV files from signed URLs to T7 drive
"""

import os
import requests
import re
import time
from datetime import datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class CVDataDownloader:
    def __init__(self):
        self.base_dir = "/Volumes/T7/Data/connected_vehicle_data"
        self.raw_data_dir = os.path.join(self.base_dir, "raw_files", "additional_data")
        self.urls_file = os.path.join(self.base_dir, "raw_files", "additonal_raw", "NZ_report_withOD-signed_urls.txt")

        # Create output directory
        os.makedirs(self.raw_data_dir, exist_ok=True)

        # Progress tracking
        self.download_count = 0
        self.total_files = 0
        self.failed_downloads = []
        self.lock = threading.Lock()

        print("🚛 ADDITIONAL CONNECTED VEHICLE DATA DOWNLOADER")
        print(f"📁 Output directory: {self.raw_data_dir}")
        print("=" * 60)

    def parse_urls_file(self):
        """Parse the signed URLs file and extract download URLs"""
        urls = []

        print("📄 Parsing URLs file...")

        with open(self.urls_file, 'r') as f:
            content = f.read()

        # Extract total count
        total_match = re.search(r'Total Number of CSV Files: (\d+)', content)
        if total_match:
            self.total_files = int(total_match.group(1))
            print(f"📊 Total files to download: {self.total_files}")

        # Extract URLs - look for lines starting with https://storage.googleapis.com
        url_pattern = r'https://storage\.googleapis\.com/[^\s]+'
        urls = re.findall(url_pattern, content)

        print(f"✅ Found {len(urls)} valid URLs")
        return urls

    def extract_filename_from_url(self, url):
        """Extract filename from the signed URL"""
        # Look for the CSV filename in the URL path
        match = re.search(r'/([^/?]+\.csv)', url)
        if match:
            return match.group(1)

        # Fallback: generate filename from URL hash
        url_hash = str(hash(url))[-8:]
        return f"cv_data_{url_hash}.csv"

    def download_single_file(self, url, retries=3):
        """Download a single CSV file with retry logic"""
        filename = self.extract_filename_from_url(url)
        file_path = os.path.join(self.raw_data_dir, filename)

        # Skip if file already exists
        if os.path.exists(file_path):
            with self.lock:
                self.download_count += 1
            return {"success": True, "filename": filename, "status": "skipped"}

        for attempt in range(retries):
            try:
                # Download with progress tracking
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()

                # Write file
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                # Update progress
                with self.lock:
                    self.download_count += 1
                    if self.download_count % 50 == 0:
                        print(f"📥 Downloaded: {self.download_count}/{self.total_files} files")

                return {"success": True, "filename": filename, "status": "downloaded"}

            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(1)  # Wait before retry
                    continue
                else:
                    with self.lock:
                        self.failed_downloads.append({"url": url, "filename": filename, "error": str(e)})
                    return {"success": False, "filename": filename, "error": str(e)}

    def download_all_files(self, max_workers=10):
        """Download all CSV files using parallel workers"""
        urls = self.parse_urls_file()

        if not urls:
            print("❌ No URLs found to download")
            return False

        print(f"🔄 Starting download with {max_workers} workers...")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        start_time = time.time()

        # Use ThreadPoolExecutor for parallel downloads
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all download tasks
            future_to_url = {executor.submit(self.download_single_file, url): url for url in urls}

            # Process completed downloads
            for future in as_completed(future_to_url):
                result = future.result()
                # Progress is tracked in download_single_file

        end_time = time.time()
        duration = end_time - start_time

        # Print summary
        print("\n" + "=" * 60)
        print("📊 DOWNLOAD SUMMARY")
        print("=" * 60)
        print(f"✅ Successfully downloaded: {self.download_count - len(self.failed_downloads)} files")
        print(f"⏭️  Skipped (already existed): Files counted as successful")
        print(f"❌ Failed downloads: {len(self.failed_downloads)} files")
        print(f"⏱️  Total time: {duration/60:.1f} minutes")
        print(f"📁 Output directory: {self.raw_data_dir}")

        # Report failed downloads
        if self.failed_downloads:
            print("\n❌ FAILED DOWNLOADS:")
            for failed in self.failed_downloads[:10]:  # Show first 10
                print(f"   {failed['filename']}: {failed['error']}")
            if len(self.failed_downloads) > 10:
                print(f"   ... and {len(self.failed_downloads) - 10} more")

        return len(self.failed_downloads) == 0

    def verify_downloads(self):
        """Verify downloaded files and get basic statistics"""
        print("\n🔍 VERIFYING DOWNLOADS...")

        csv_files = [f for f in os.listdir(self.raw_data_dir) if f.endswith('.csv')]
        print(f"📄 Found {len(csv_files)} CSV files")

        if not csv_files:
            print("❌ No CSV files found!")
            return

        # Sample a few files to check structure
        print("🔍 Checking file structure...")
        sample_files = csv_files[:3]

        for filename in sample_files:
            file_path = os.path.join(self.raw_data_dir, filename)
            try:
                # Read just the header and first few rows
                df_sample = pd.read_csv(file_path, nrows=5)
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB

                print(f"   ✅ {filename}: {len(df_sample.columns)} columns, {file_size:.1f} MB")
                if filename == sample_files[0]:  # Show columns for first file
                    print(f"      Columns: {list(df_sample.columns)}")

            except Exception as e:
                print(f"   ❌ {filename}: Error reading - {e}")

        # Calculate total storage used
        total_size = sum(os.path.getsize(os.path.join(self.raw_data_dir, f))
                        for f in csv_files) / (1024 * 1024 * 1024)  # GB

        print(f"💾 Total storage used: {total_size:.2f} GB")

def main():
    """Main function to download additional CV data"""

    downloader = CVDataDownloader()

    # Download all files
    success = downloader.download_all_files(max_workers=8)  # Conservative worker count

    # Verify downloads
    downloader.verify_downloads()

    if success:
        print("\n🎯 DOWNLOAD COMPLETE - ALL FILES SUCCESSFUL")
    else:
        print("\n⚠️  DOWNLOAD COMPLETE - SOME FAILURES OCCURRED")
        print("Consider re-running to retry failed downloads")

    print("=" * 60)
    return success

if __name__ == "__main__":
    main()
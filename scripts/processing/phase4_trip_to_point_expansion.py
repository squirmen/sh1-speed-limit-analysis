#!/usr/bin/env python3
"""
Phase 4: Trip-to-Point Expansion
==================================
Expand 92,456 corridor trips to point-level format

Memory-efficient: Process in chunks
Expected output: ~1-2M GPS points
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
import sys

class TripToPointExpander:
    def __init__(self, input_file, output_dir, chunk_size=10000):
        self.input_file = input_file
        self.output_dir = output_dir
        self.chunk_size = chunk_size
        self.audit_log = []

        os.makedirs(os.path.join(output_dir, "point_level"), exist_ok=True)

        print("="*80)
        print("PHASE 4: TRIP-TO-POINT EXPANSION")
        print("="*80)
        print(f"Input:  {input_file}")
        print(f"Output: {output_dir}")
        print(f"Chunk size: {chunk_size:,} trips")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        sys.stdout.flush()

    def log_event(self, event_type, message, details=None):
        """Log event"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'message': message,
            'details': details or {}
        }
        self.audit_log.append(event)
        print(f"[{event_type}] {message}")
        sys.stdout.flush()

    def parse_path(self, path_str):
        """Parse comma-separated path string to list"""
        if pd.isna(path_str):
            return []
        try:
            return [item.strip() for item in str(path_str).split(',')]
        except:
            return []

    def expand_trip(self, trip_row):
        """Expand single trip to point-level records"""
        try:
            # Parse paths
            timestamps = self.parse_path(trip_row.get('TimestampPath', ''))
            raw_path = self.parse_path(trip_row.get('RawPath', ''))
            speeds = self.parse_path(trip_row.get('SpeedPath', ''))

            # Validate synchronization
            if not (timestamps and raw_path and speeds):
                return []

            n_timestamps = len(timestamps)
            n_coords = len(raw_path)
            n_speeds = len(speeds)

            if not (n_timestamps == n_coords == n_speeds):
                return []

            # Create point records
            points = []
            for i in range(n_timestamps):
                try:
                    # Parse coordinate
                    coord_parts = raw_path[i].strip().split()
                    if len(coord_parts) != 2:
                        continue

                    lon, lat = float(coord_parts[0]), float(coord_parts[1])
                    speed = float(speeds[i])

                    # Create point record matching existing schema
                    point = {
                        'TripID': trip_row.get('TripID', ''),
                        'VehicleID': trip_row.get('VehicleID', ''),
                        'VehicleType': trip_row.get('VehicleType', ''),
                        'TripStartTime': f"{trip_row.get('StartDate', '')} {trip_row.get('StartTime', '')}",
                        'Point_RawLon': lon,
                        'Point_RawLat': lat,
                        'Point_RawTimestamp': timestamps[i],
                        'Point_Speed': speed,
                        'Point_Sequence': i,
                        'Trip_TotalPoints': n_timestamps,
                        'Trip_TravelTimeMinutes': trip_row.get('TravelTimeMinutes', None),
                        'Trip_DistanceMetres': trip_row.get('TravelDistanceMetres', None)
                    }
                    points.append(point)
                except:
                    continue

            return points

        except Exception as e:
            return []

    def process_chunk(self, chunk_df, chunk_num):
        """Process a chunk of trips"""
        print(f"\n--- Chunk {chunk_num}: {len(chunk_df):,} trips ---")
        sys.stdout.flush()

        all_points = []
        successful_trips = 0
        total_points = 0

        for idx, row in chunk_df.iterrows():
            points = self.expand_trip(row)
            if points:
                all_points.extend(points)
                successful_trips += 1
                total_points += len(points)

            if (idx + 1) % 1000 == 0:
                print(f"  Processed {idx+1:,} trips, {total_points:,} points so far...")
                sys.stdout.flush()

        print(f"  Chunk complete: {successful_trips:,} trips expanded to {total_points:,} points")
        sys.stdout.flush()

        # Convert to DataFrame
        if all_points:
            points_df = pd.DataFrame(all_points)
            return points_df
        else:
            return pd.DataFrame()

    def expand_all_trips(self):
        """Expand all corridor trips to point-level"""
        print("\n" + "="*80)
        print("EXPANDING TRIPS TO POINTS")
        print("="*80 + "\n")
        sys.stdout.flush()

        # Load corridor trips
        print(f"Loading corridor trips from {self.input_file}...")
        sys.stdout.flush()

        df_trips = pd.read_parquet(self.input_file)
        total_trips = len(df_trips)

        print(f"Total corridor trips: {total_trips:,}")
        print(f"Processing in chunks of {self.chunk_size:,}...\n")
        sys.stdout.flush()

        # Process in chunks
        chunk_files = []
        total_points = 0
        num_chunks = (total_trips + self.chunk_size - 1) // self.chunk_size

        for chunk_num in range(num_chunks):
            start_idx = chunk_num * self.chunk_size
            end_idx = min(start_idx + self.chunk_size, total_trips)

            print(f"\n{'='*80}")
            print(f"CHUNK {chunk_num + 1}/{num_chunks}")
            print(f"{'='*80}")
            sys.stdout.flush()

            chunk_df = df_trips.iloc[start_idx:end_idx]
            points_df = self.process_chunk(chunk_df, chunk_num + 1)

            if len(points_df) > 0:
                # Save chunk
                chunk_file = os.path.join(
                    self.output_dir,
                    "point_level",
                    f"points_chunk_{chunk_num+1:04d}.parquet"
                )
                points_df.to_parquet(chunk_file, engine='pyarrow', compression='snappy', index=False)
                chunk_files.append(chunk_file)

                file_size_mb = os.path.getsize(chunk_file) / (1024**2)
                print(f"  Saved: {len(points_df):,} points ({file_size_mb:.1f} MB)")
                total_points += len(points_df)
            else:
                print(f"  No valid points in this chunk")

            print(f"  Running total: {total_points:,} points")
            sys.stdout.flush()

        self.log_event("SUCCESS", f"Expanded {total_trips:,} trips to {total_points:,} points", {
            'input_trips': total_trips,
            'output_points': total_points,
            'chunk_files': len(chunk_files)
        })

        return chunk_files, total_points

    def combine_chunks(self, chunk_files):
        """Combine point chunks into single file"""
        print("\n" + "="*80)
        print("COMBINING POINT CHUNKS")
        print("="*80 + "\n")
        sys.stdout.flush()

        if not chunk_files:
            print("No point files to combine!")
            return None, 0

        print(f"Combining {len(chunk_files)} chunk files...")
        sys.stdout.flush()

        # Load and concatenate all chunks
        dfs = []
        for i, chunk_file in enumerate(chunk_files):
            df = pd.read_parquet(chunk_file)
            dfs.append(df)
            if (i + 1) % 3 == 0:
                print(f"  Loaded {i+1}/{len(chunk_files)} chunks...")
                sys.stdout.flush()

        combined_df = pd.concat(dfs, ignore_index=True)

        output_file = os.path.join(self.output_dir, "point_level", "corridor_gps_points.parquet")
        combined_df.to_parquet(output_file, engine='pyarrow', compression='snappy', index=False)

        file_size_mb = os.path.getsize(output_file) / (1024**2)
        print(f"\n✅ Combined file: {output_file}")
        print(f"   Points: {len(combined_df):,}")
        print(f"   Size: {file_size_mb:.1f} MB")
        sys.stdout.flush()

        # Clean up chunks
        print("\nCleaning up chunk files...")
        for chunk_file in chunk_files:
            os.remove(chunk_file)
        print(f"✅ Removed {len(chunk_files)} chunk files")
        sys.stdout.flush()

        return output_file, len(combined_df)

    def generate_statistics(self, output_file, total_points):
        """Generate statistics"""
        print("\n" + "="*80)
        print("STATISTICS")
        print("="*80 + "\n")
        sys.stdout.flush()

        df = pd.read_parquet(output_file)

        stats = {
            'total_points': int(total_points),
            'unique_trips': int(df['TripID'].nunique()),
            'unique_vehicles': int(df['VehicleID'].nunique()),
            'avg_points_per_trip': float(total_points / df['TripID'].nunique()),
            'timestamp': datetime.now().isoformat()
        }

        # Temporal split
        df['timestamp_dt'] = pd.to_datetime(df['Point_RawTimestamp'], errors='coerce', utc=True)
        speed_change_date = pd.Timestamp('2025-04-13', tz='UTC')

        before = (df['timestamp_dt'] < speed_change_date).sum()
        after = (df['timestamp_dt'] >= speed_change_date).sum()

        stats['before_period_points'] = int(before)
        stats['after_period_points'] = int(after)

        # Save stats
        stats_file = os.path.join(self.output_dir, "quality_assurance", "phase4_statistics.json")
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)

        print(f"Total GPS points:    {stats['total_points']:,}")
        print(f"Unique trips:        {stats['unique_trips']:,}")
        print(f"Unique vehicles:     {stats['unique_vehicles']:,}")
        print(f"Avg points/trip:     {stats['avg_points_per_trip']:.1f}")
        print(f"  Before period:     {stats['before_period_points']:,} points")
        print(f"  After period:      {stats['after_period_points']:,} points")
        print(f"\n✅ Statistics: {stats_file}")
        sys.stdout.flush()

        return stats

    def save_audit_trail(self):
        """Save audit trail"""
        audit_file = os.path.join(self.output_dir, "quality_assurance", "phase4_audit_trail.json")
        with open(audit_file, 'w') as f:
            json.dump({
                'phase': 'Phase 4: Trip-to-Point Expansion',
                'timestamp': datetime.now().isoformat(),
                'events': self.audit_log
            }, f, indent=2)
        print(f"✅ Audit trail: {audit_file}")
        sys.stdout.flush()

    def run_phase4(self):
        """Execute Phase 4"""
        start_time = datetime.now()

        try:
            # Expand trips to points
            chunk_files, total_points = self.expand_all_trips()

            # Combine chunks
            output_file, point_count = self.combine_chunks(chunk_files)

            # Generate statistics
            stats = self.generate_statistics(output_file, point_count)

            # Save audit trail
            self.save_audit_trail()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            print("\n" + "="*80)
            print("PHASE 4 COMPLETE")
            print("="*80)
            print(f"Time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
            print(f"Output: {output_file}")
            print(f"GPS points: {point_count:,}")
            print(f"\n✅ Ready for Analysis Integration")
            sys.stdout.flush()

            return True

        except Exception as e:
            self.log_event("CRITICAL", f"Phase 4 failed: {str(e)}")
            self.save_audit_trail()
            print(f"\n❌ Phase 4 failed: {str(e)}")
            sys.stdout.flush()
            import traceback
            traceback.print_exc()
            return False


def main():
    """Execute Phase 4"""
    input_file = "/Volumes/T7/Data/connected_vehicle_data/output/processed_data/trip_level/corridor_trips.parquet"
    output_dir = "/Volumes/T7/Data/connected_vehicle_data/output/processed_data"

    expander = TripToPointExpander(input_file, output_dir, chunk_size=10000)
    success = expander.run_phase4()

    if success:
        print("\n🎯 DATA READY FOR ANALYSIS")
        return 0
    else:
        print("\n⛔ Phase 4 failed")
        return 1


if __name__ == "__main__":
    exit(main())

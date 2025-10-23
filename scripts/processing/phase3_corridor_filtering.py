#!/usr/bin/env python3
"""
Phase 3: Corridor Definition & Filtering
=========================================
Filter trips to SH1/SH76 Christchurch corridor using 3-tier approach

Approach:
- Tier 1: Bounding box (fast elimination)
- Tier 2: Centerline distance (precision)
- Tier 3: Route validation (quality)
"""

import duckdb
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
import sys
from math import radians, cos, sin, asin, sqrt

class CorridorFilter:
    def __init__(self, input_file, output_dir):
        self.input_file = input_file
        self.output_dir = output_dir
        self.audit_log = []

        # SH1/SH76 Christchurch corridor boundaries
        self.CORRIDOR_BOUNDS = {
            'lat_min': -43.58,
            'lat_max': -43.48,
            'lon_min': 172.55,
            'lon_max': 172.65
        }

        # Corridor centerline (south to north)
        self.CENTERLINE = [
            (-43.5776, 172.5892),
            (-43.5654, 172.5912),
            (-43.5532, 172.5935),
            (-43.5410, 172.5958),
            (-43.5288, 172.5982),
            (-43.5166, 172.6005),
            (-43.5044, 172.6028),
            (-43.4922, 172.6052)
        ]

        self.MAX_DISTANCE_M = 500  # meters from centerline
        self.MIN_CORRIDOR_LENGTH_M = 2000  # minimum 2km on corridor

        print("="*80)
        print("PHASE 3: CORRIDOR FILTERING")
        print("="*80)
        print(f"Input:  {input_file}")
        print(f"Output: {output_dir}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        sys.stdout.flush()

    def log_event(self, event_type, message, details=None):
        """Log event with immediate output"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'message': message,
            'details': details or {}
        }
        self.audit_log.append(event)
        print(f"[{event_type}] {message}")
        sys.stdout.flush()

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance in meters between two points"""
        R = 6371000  # Earth radius in meters

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))

        return R * c

    def distance_to_centerline(self, lat, lon):
        """Calculate minimum distance from point to corridor centerline"""
        min_dist = float('inf')

        for i in range(len(self.CENTERLINE) - 1):
            # For each segment, find minimum distance
            seg_start = self.CENTERLINE[i]
            seg_end = self.CENTERLINE[i + 1]

            # Distance to segment start
            d1 = self.haversine_distance(lat, lon, seg_start[0], seg_start[1])
            # Distance to segment end
            d2 = self.haversine_distance(lat, lon, seg_end[0], seg_end[1])

            min_dist = min(min_dist, d1, d2)

        return min_dist

    def parse_first_coord(self, raw_path):
        """Extract first coordinate from RawPath"""
        if pd.isna(raw_path):
            return None, None
        try:
            first_point = str(raw_path).split(',')[0].strip()
            parts = first_point.split()
            if len(parts) == 2:
                lon, lat = float(parts[0]), float(parts[1])
                return lat, lon
        except:
            pass
        return None, None

    def parse_last_coord(self, raw_path):
        """Extract last coordinate from RawPath"""
        if pd.isna(raw_path):
            return None, None
        try:
            points = str(raw_path).split(',')
            last_point = points[-1].strip()
            parts = last_point.split()
            if len(parts) == 2:
                lon, lat = float(parts[0]), float(parts[1])
                return lat, lon
        except:
            pass
        return None, None

    def tier1_bounding_box_filter(self):
        """Tier 1: Fast bounding box filtering using DuckDB"""
        print("\n" + "="*80)
        print("TIER 1: BOUNDING BOX FILTERING")
        print("="*80 + "\n")
        sys.stdout.flush()

        conn = duckdb.connect()

        try:
            # Load data
            print(f"Loading data from {self.input_file}...")
            sys.stdout.flush()

            total_trips = conn.execute(f"""
                SELECT COUNT(*) FROM '{self.input_file}'
            """).fetchone()[0]

            print(f"Total trips to filter: {total_trips:,}")
            sys.stdout.flush()

            # Export to pandas for coordinate parsing (DuckDB can't easily parse the path strings)
            print("\nLoading trip data (this may take a few minutes)...")
            sys.stdout.flush()

            df = conn.execute(f"""
                SELECT * FROM '{self.input_file}'
            """).df()

            print(f"Loaded {len(df):,} trips into memory")
            sys.stdout.flush()

            # Parse first coordinate from each trip
            print("\nParsing trip coordinates...")
            sys.stdout.flush()

            coords = df['RawPath'].apply(self.parse_first_coord)
            df['first_lat'] = coords.apply(lambda x: x[0])
            df['first_lon'] = coords.apply(lambda x: x[1])

            # Filter by bounding box
            mask = (
                (df['first_lat'] >= self.CORRIDOR_BOUNDS['lat_min']) &
                (df['first_lat'] <= self.CORRIDOR_BOUNDS['lat_max']) &
                (df['first_lon'] >= self.CORRIDOR_BOUNDS['lon_min']) &
                (df['first_lon'] <= self.CORRIDOR_BOUNDS['lon_max']) &
                df['first_lat'].notna() &
                df['first_lon'].notna()
            )

            tier1_trips = df[mask].copy()

            eliminated = len(df) - len(tier1_trips)
            pct = 100 * len(tier1_trips) / len(df)

            print(f"\n✅ Tier 1 complete:")
            print(f"   Passed: {len(tier1_trips):,} trips ({pct:.1f}%)")
            print(f"   Eliminated: {eliminated:,} trips")
            sys.stdout.flush()

            self.log_event("SUCCESS", f"Tier 1: {len(tier1_trips):,} trips in bounding box", {
                'total_input': total_trips,
                'passed': len(tier1_trips),
                'eliminated': eliminated
            })

            conn.close()
            return tier1_trips

        except Exception as e:
            conn.close()
            raise

    def tier2_centerline_filter(self, df):
        """Tier 2: Filter by distance from centerline"""
        print("\n" + "="*80)
        print("TIER 2: CENTERLINE DISTANCE FILTERING")
        print("="*80 + "\n")
        sys.stdout.flush()

        print(f"Calculating distances for {len(df):,} trips...")
        print("(This is computationally intensive, may take several minutes)")
        sys.stdout.flush()

        # Calculate distance to centerline for each trip
        distances = []
        for idx, row in df.iterrows():
            if pd.notna(row['first_lat']) and pd.notna(row['first_lon']):
                dist = self.distance_to_centerline(row['first_lat'], row['first_lon'])
                distances.append(dist)
            else:
                distances.append(float('inf'))

            if (idx + 1) % 50000 == 0:
                print(f"  Processed {idx+1:,} / {len(df):,} trips...")
                sys.stdout.flush()

        df['centerline_dist_m'] = distances

        # Filter by distance
        tier2_trips = df[df['centerline_dist_m'] <= self.MAX_DISTANCE_M].copy()

        eliminated = len(df) - len(tier2_trips)
        pct = 100 * len(tier2_trips) / len(df)

        print(f"\n✅ Tier 2 complete:")
        print(f"   Passed: {len(tier2_trips):,} trips ({pct:.1f}%)")
        print(f"   Eliminated: {eliminated:,} trips (>{self.MAX_DISTANCE_M}m from centerline)")
        sys.stdout.flush()

        self.log_event("SUCCESS", f"Tier 2: {len(tier2_trips):,} trips within {self.MAX_DISTANCE_M}m", {
            'input': len(df),
            'passed': len(tier2_trips),
            'eliminated': eliminated
        })

        return tier2_trips

    def tier3_route_validation(self, df):
        """Tier 3: Validate route characteristics"""
        print("\n" + "="*80)
        print("TIER 3: ROUTE VALIDATION")
        print("="*80 + "\n")
        sys.stdout.flush()

        print(f"Validating routes for {len(df):,} trips...")
        sys.stdout.flush()

        # Parse last coordinate
        coords = df['RawPath'].apply(self.parse_last_coord)
        df['last_lat'] = coords.apply(lambda x: x[0])
        df['last_lon'] = coords.apply(lambda x: x[1])

        # Check that trip travels along corridor (not just crossing)
        # Simple check: both start and end should be in bounding box
        mask = (
            (df['last_lat'] >= self.CORRIDOR_BOUNDS['lat_min']) &
            (df['last_lat'] <= self.CORRIDOR_BOUNDS['lat_max']) &
            (df['last_lon'] >= self.CORRIDOR_BOUNDS['lon_min']) &
            (df['last_lon'] <= self.CORRIDOR_BOUNDS['lon_max']) &
            df['last_lat'].notna() &
            df['last_lon'].notna()
        )

        # Also check minimum travel distance
        if 'TravelDistanceMetres' in df.columns:
            mask = mask & (df['TravelDistanceMetres'] >= self.MIN_CORRIDOR_LENGTH_M)

        tier3_trips = df[mask].copy()

        eliminated = len(df) - len(tier3_trips)
        pct = 100 * len(tier3_trips) / len(df)

        print(f"\n✅ Tier 3 complete:")
        print(f"   Passed: {len(tier3_trips):,} trips ({pct:.1f}%)")
        print(f"   Eliminated: {eliminated:,} trips (crossing only or too short)")
        sys.stdout.flush()

        self.log_event("SUCCESS", f"Tier 3: {len(tier3_trips):,} quality corridor trips", {
            'input': len(df),
            'passed': len(tier3_trips),
            'eliminated': eliminated
        })

        return tier3_trips

    def save_corridor_trips(self, df):
        """Save filtered corridor trips to Parquet"""
        print("\n" + "="*80)
        print("SAVING CORRIDOR TRIPS")
        print("="*80 + "\n")
        sys.stdout.flush()

        # Drop temporary columns
        cols_to_drop = ['first_lat', 'first_lon', 'last_lat', 'last_lon', 'centerline_dist_m']
        df_clean = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

        output_file = os.path.join(self.output_dir, "trip_level", "corridor_trips.parquet")

        print(f"Writing {len(df_clean):,} trips to Parquet...")
        sys.stdout.flush()

        df_clean.to_parquet(
            output_file,
            engine='pyarrow',
            compression='snappy',
            index=False
        )

        file_size_mb = os.path.getsize(output_file) / (1024**2)

        print(f"✅ Saved: {output_file}")
        print(f"   Size: {file_size_mb:.1f} MB")
        sys.stdout.flush()

        self.log_event("SUCCESS", "Corridor trips saved", {
            'output_file': output_file,
            'trip_count': len(df_clean),
            'file_size_mb': round(file_size_mb, 1)
        })

        return output_file

    def generate_statistics(self, df_all, df_corridor):
        """Generate filtering statistics"""
        print("\n" + "="*80)
        print("FILTERING STATISTICS")
        print("="*80 + "\n")
        sys.stdout.flush()

        stats = {
            'total_input_trips': len(df_all),
            'corridor_trips': len(df_corridor),
            'filter_rate': len(df_corridor) / len(df_all),
            'unique_vehicles': int(df_corridor['VehicleID'].nunique()) if 'VehicleID' in df_corridor.columns else None,
            'timestamp': datetime.now().isoformat()
        }

        # Temporal split if we have dates
        if 'StartDate' in df_corridor.columns:
            # Parse dates
            df_corridor['start_dt'] = pd.to_datetime(
                df_corridor['StartDate'].astype(str) + ' ' + df_corridor['StartTime'].astype(str),
                errors='coerce',
                utc=True
            )

            speed_change_date = pd.Timestamp('2025-04-13', tz='UTC')

            before = (df_corridor['start_dt'] < speed_change_date).sum()
            after = (df_corridor['start_dt'] >= speed_change_date).sum()

            stats['before_period_trips'] = int(before)
            stats['after_period_trips'] = int(after)

        # Save stats
        stats_file = os.path.join(self.output_dir, "quality_assurance", "phase3_statistics.json")
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)

        print(f"Input trips:     {stats['total_input_trips']:,}")
        print(f"Corridor trips:  {stats['corridor_trips']:,} ({100*stats['filter_rate']:.1f}%)")
        if 'before_period_trips' in stats:
            print(f"  Before (< Apr 13): {stats['before_period_trips']:,}")
            print(f"  After (>= Apr 13): {stats['after_period_trips']:,}")
        if stats['unique_vehicles']:
            print(f"Unique vehicles: {stats['unique_vehicles']:,}")

        print(f"\n✅ Statistics: {stats_file}")
        sys.stdout.flush()

        return stats

    def save_audit_trail(self):
        """Save audit trail"""
        audit_file = os.path.join(self.output_dir, "quality_assurance", "phase3_audit_trail.json")
        with open(audit_file, 'w') as f:
            json.dump({
                'phase': 'Phase 3: Corridor Filtering',
                'timestamp': datetime.now().isoformat(),
                'events': self.audit_log
            }, f, indent=2)
        print(f"✅ Audit trail: {audit_file}")
        sys.stdout.flush()

    def run_phase3(self):
        """Execute Phase 3 pipeline"""
        start_time = datetime.now()

        try:
            # Tier 1: Bounding box
            tier1_df = self.tier1_bounding_box_filter()

            # Tier 2: Centerline distance
            tier2_df = self.tier2_centerline_filter(tier1_df)

            # Tier 3: Route validation
            corridor_df = self.tier3_route_validation(tier2_df)

            # Save results
            output_file = self.save_corridor_trips(corridor_df)

            # Generate statistics
            # Load original count
            conn = duckdb.connect()
            total = conn.execute(f"SELECT COUNT(*) FROM '{self.input_file}'").fetchone()[0]
            conn.close()

            stats = self.generate_statistics(
                pd.DataFrame({'dummy': range(total)}),  # Dummy df with correct length
                corridor_df
            )

            # Save audit trail
            self.save_audit_trail()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            print("\n" + "="*80)
            print("PHASE 3 COMPLETE")
            print("="*80)
            print(f"Time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
            print(f"Output: {output_file}")
            print(f"Corridor trips: {len(corridor_df):,}")
            print(f"\n✅ Ready for Phase 4: Trip-to-Point Expansion")
            sys.stdout.flush()

            return True

        except Exception as e:
            self.log_event("CRITICAL", f"Phase 3 failed: {str(e)}")
            self.save_audit_trail()
            print(f"\n❌ Phase 3 failed: {str(e)}")
            sys.stdout.flush()
            return False


def main():
    """Execute Phase 3"""
    input_file = "/Volumes/T7/Data/connected_vehicle_data/output/processed_data/trip_level/all_trips.parquet"
    output_dir = "/Volumes/T7/Data/connected_vehicle_data/output/processed_data"

    filter = CorridorFilter(input_file, output_dir)
    success = filter.run_phase3()

    if success:
        print("\n🎯 PROCEED TO PHASE 4")
        return 0
    else:
        print("\n⛔ Phase 3 failed")
        return 1


if __name__ == "__main__":
    exit(main())

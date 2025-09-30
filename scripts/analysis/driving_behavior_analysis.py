"""
Driving Behavior Analysis: Hard Braking, Hard Steering & Near-Miss Events
Professional analysis of safety-related driving behaviors before/after speed limit change
SH1/SH76 Christchurch Southern Motorway
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from scipy.spatial.distance import pdist, squareform
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class DrivingBehaviorAnalysis:
    def __init__(self):
        self.base_dir = "/Volumes/T7/Data/connected_vehicle_data"
        self.data_dir = os.path.join(self.base_dir, "output", "processed_data")
        self.output_dir = os.path.join(self.base_dir, "output", "reports")

        # Behavior detection thresholds (based on transportation safety literature)
        self.thresholds = {
            'hard_braking_decel': -3.0,      # m/s² (longitudinal deceleration)
            'hard_acceleration': 2.5,        # m/s² (longitudinal acceleration)
            'hard_steering_lateral': 2.0,    # m/s² (lateral acceleration)
            'near_miss_distance': 30.0,      # meters (minimum safe distance)
            'near_miss_time_window': 10.0,   # seconds (temporal proximity)
            'speed_differential_kmh': 20.0   # km/h (relative speed threshold)
        }

        # Study parameters
        self.speed_change_date = pd.to_datetime("2025-04-13")
        self.corridor_bounds = {
            'lat_min': -43.65, 'lat_max': -43.45,  # Approximate SH1/SH76 bounds
            'lon_min': 172.35, 'lon_max': 172.65
        }

        os.makedirs(self.output_dir, exist_ok=True)

        print("🚗 DRIVING BEHAVIOR ANALYSIS")
        print("Hard Braking, Hard Steering & Near-Miss Event Detection")
        print("Before/After Analysis of Safety-Related Behaviors")
        print("="*60)

    def load_gps_data(self):
        """Load GPS data for behavior analysis"""
        print(f"\n📂 LOADING GPS DATA FOR BEHAVIOR ANALYSIS")

        # Load comprehensive GPS metrics
        gps_path = os.path.join(self.data_dir, "comprehensive_gps_metrics.csv")
        if not os.path.exists(gps_path):
            print(f"❌ GPS data not found: {gps_path}")
            return None

        # Load in chunks to handle large dataset efficiently
        chunk_size = 10000
        chunks = []
        total_rows = 0

        print("📊 Loading GPS data in chunks...")

        try:
            for chunk in pd.read_csv(gps_path, chunksize=chunk_size):
                # Filter for corridor area and valid data
                chunk = chunk[
                    (chunk['Point_RawLat'].between(self.corridor_bounds['lat_min'],
                                                  self.corridor_bounds['lat_max'])) &
                    (chunk['Point_RawLon'].between(self.corridor_bounds['lon_min'],
                                                  self.corridor_bounds['lon_max'])) &
                    (chunk['derived_speed_kmh'].notna()) &
                    (chunk['derived_speed_kmh'] > 10) &
                    (chunk['derived_speed_kmh'] < 150)
                ]

                if len(chunk) > 0:
                    chunks.append(chunk)
                    total_rows += len(chunk)

                if total_rows > 50000:  # Limit for performance
                    break

            if chunks:
                self.gps_data = pd.concat(chunks, ignore_index=True)
                self.gps_data['timestamp'] = pd.to_datetime(self.gps_data['timestamp'], format='mixed', errors='coerce')

                # Remove invalid timestamps
                self.gps_data = self.gps_data.dropna(subset=['timestamp'])

                print(f"✅ GPS data loaded: {len(self.gps_data):,} valid points")
                print(f"📅 Date range: {self.gps_data['timestamp'].min()} to {self.gps_data['timestamp'].max()}")

                # Period classification
                self.gps_data['period'] = self.gps_data['timestamp'].apply(
                    lambda x: 'before' if x < self.speed_change_date else 'after'
                )

                period_counts = self.gps_data['period'].value_counts()
                print(f"📊 Period distribution:")
                for period, count in period_counts.items():
                    print(f"   • {period.upper()}: {count:,} points")

                return True
            else:
                print("❌ No valid GPS data found in corridor area")
                return False

        except Exception as e:
            print(f"❌ Error loading GPS data: {e}")
            return False

    def detect_hard_events(self):
        """Detect hard braking, acceleration, and steering events"""
        print(f"\n🎯 DETECTING HARD DRIVING EVENTS")

        if not hasattr(self, 'gps_data') or self.gps_data.empty:
            print("❌ No GPS data available for analysis")
            return None

        events = []

        # Group by vehicle and trip for sequential analysis
        grouped = self.gps_data.groupby(['VehicleID', 'TripID'])
        total_trips = len(grouped)
        processed = 0

        print(f"🔄 Processing {total_trips:,} vehicle trips...")

        for (vehicle_id, trip_id), trip_data in grouped:
            processed += 1
            if processed % 500 == 0:
                print(f"   Processed {processed:,}/{total_trips:,} trips")

            # Sort by timestamp
            trip_data = trip_data.sort_values('timestamp').reset_index(drop=True)

            if len(trip_data) < 3:  # Need minimum points for acceleration calculation
                continue

            # Calculate acceleration from speed data (approximate)
            trip_data['time_diff'] = trip_data['timestamp'].diff().dt.total_seconds()
            trip_data['speed_diff_ms'] = trip_data['derived_speed_kmh'].diff() / 3.6  # Convert km/h to m/s

            # Longitudinal acceleration (m/s²)
            trip_data['longitudinal_accel'] = np.where(
                trip_data['time_diff'] > 0,
                trip_data['speed_diff_ms'] / trip_data['time_diff'],
                0
            )

            # Use existing lateral acceleration if available, otherwise approximate
            if 'lateral_accel_ms2' in trip_data.columns:
                trip_data['lateral_accel'] = trip_data['lateral_accel_ms2'].abs()
            else:
                # Approximate lateral acceleration from direction changes
                if 'bearing_deg' in trip_data.columns:
                    bearing_diff = trip_data['bearing_deg'].diff().abs()
                    bearing_diff = np.where(bearing_diff > 180, 360 - bearing_diff, bearing_diff)
                    trip_data['lateral_accel'] = np.where(
                        trip_data['time_diff'] > 0,
                        (bearing_diff * np.pi / 180) * trip_data['derived_speed_kmh'] / 3.6 / trip_data['time_diff'],
                        0
                    )
                else:
                    trip_data['lateral_accel'] = 0

            # Detect events
            for idx, row in trip_data.iterrows():
                event_list = []

                # Hard braking
                if row['longitudinal_accel'] <= self.thresholds['hard_braking_decel']:
                    event_list.append('hard_braking')

                # Hard acceleration
                if row['longitudinal_accel'] >= self.thresholds['hard_acceleration']:
                    event_list.append('hard_acceleration')

                # Hard steering
                if row['lateral_accel'] >= self.thresholds['hard_steering_lateral']:
                    event_list.append('hard_steering')

                # Record events
                for event_type in event_list:
                    events.append({
                        'vehicle_id': vehicle_id,
                        'trip_id': trip_id,
                        'timestamp': row['timestamp'],
                        'period': row['period'],
                        'event_type': event_type,
                        'latitude': row['Point_RawLat'],
                        'longitude': row['Point_RawLon'],
                        'speed_kmh': row['derived_speed_kmh'],
                        'longitudinal_accel': row['longitudinal_accel'],
                        'lateral_accel': row['lateral_accel'],
                        'severity': abs(row['longitudinal_accel']) if 'braking' in event_type or 'acceleration' in event_type else row['lateral_accel']
                    })

        self.hard_events = pd.DataFrame(events) if events else pd.DataFrame()

        if not self.hard_events.empty:
            print(f"✅ Hard events detected: {len(self.hard_events):,}")

            # Event type breakdown
            event_summary = self.hard_events.groupby(['period', 'event_type']).size().unstack(fill_value=0)
            print(f"\n📊 EVENT TYPE SUMMARY:")
            print(event_summary)

        else:
            print("⚠️  No hard events detected with current thresholds")

        return self.hard_events

    def detect_near_miss_events(self):
        """Detect near-miss events using spatiotemporal proximity analysis"""
        print(f"\n⚠️  DETECTING NEAR-MISS EVENTS")

        if not hasattr(self, 'gps_data') or self.gps_data.empty:
            print("❌ No GPS data available for near-miss analysis")
            return None

        near_misses = []

        # Process data in time windows to detect proximity events
        print("🔄 Analyzing spatiotemporal proximity...")

        # Sort by timestamp for temporal analysis
        sorted_data = self.gps_data.sort_values('timestamp').reset_index(drop=True)

        # Process in time windows
        window_size = timedelta(seconds=self.thresholds['near_miss_time_window'])
        current_time = sorted_data['timestamp'].min()
        end_time = sorted_data['timestamp'].max()
        window_count = 0

        while current_time < end_time:
            window_count += 1
            if window_count % 1000 == 0:
                progress = (current_time - sorted_data['timestamp'].min()) / (end_time - sorted_data['timestamp'].min()) * 100
                print(f"   Progress: {progress:.1f}%")

            window_end = current_time + window_size

            # Get vehicles in current time window
            window_data = sorted_data[
                (sorted_data['timestamp'] >= current_time) &
                (sorted_data['timestamp'] < window_end)
            ]

            if len(window_data) > 1:
                # Calculate distances between all pairs of vehicles in this window
                vehicles = window_data[['Point_RawLat', 'Point_RawLon', 'VehicleID', 'derived_speed_kmh', 'timestamp', 'period']].values

                for i in range(len(vehicles)):
                    for j in range(i+1, len(vehicles)):
                        # Skip same vehicle
                        if vehicles[i][2] == vehicles[j][2]:  # Same VehicleID
                            continue

                        # Calculate distance using Haversine approximation
                        lat1, lon1 = vehicles[i][0], vehicles[i][1]
                        lat2, lon2 = vehicles[j][0], vehicles[j][1]

                        # Simple distance calculation (approximate for small distances)
                        lat_diff = np.radians(lat2 - lat1)
                        lon_diff = np.radians(lon2 - lon1)
                        distance_km = np.sqrt(lat_diff**2 + (lon_diff * np.cos(np.radians((lat1 + lat2)/2)))**2) * 6371
                        distance_m = distance_km * 1000

                        # Check if within near-miss distance threshold
                        if distance_m <= self.thresholds['near_miss_distance']:
                            # Calculate speed differential
                            speed_diff = abs(vehicles[i][3] - vehicles[j][3])  # km/h difference

                            # Time difference
                            time_diff = abs((vehicles[i][5] - vehicles[j][5]).total_seconds()) if hasattr(vehicles[i][5], 'total_seconds') else 0

                            # Determine period (use earlier timestamp's period)
                            period = vehicles[i][6] if vehicles[i][5] <= vehicles[j][5] else vehicles[j][6]

                            near_misses.append({
                                'timestamp': min(vehicles[i][5], vehicles[j][5]),
                                'period': period,
                                'vehicle1_id': vehicles[i][2],
                                'vehicle2_id': vehicles[j][2],
                                'distance_m': distance_m,
                                'speed_differential_kmh': speed_diff,
                                'time_difference_s': time_diff,
                                'vehicle1_speed': vehicles[i][3],
                                'vehicle2_speed': vehicles[j][3],
                                'latitude': (lat1 + lat2) / 2,
                                'longitude': (lon1 + lon2) / 2,
                                'severity_score': (self.thresholds['near_miss_distance'] - distance_m) / self.thresholds['near_miss_distance']
                            })

            current_time += window_size / 2  # Overlap windows by 50%

            # Limit processing for performance
            if window_count > 5000:
                print("   Limiting analysis due to computational constraints")
                break

        self.near_miss_events = pd.DataFrame(near_misses) if near_misses else pd.DataFrame()

        if not self.near_miss_events.empty:
            print(f"✅ Near-miss events detected: {len(self.near_miss_events):,}")

            # Period breakdown
            period_summary = self.near_miss_events['period'].value_counts()
            print(f"📊 NEAR-MISS EVENTS BY PERIOD:")
            for period, count in period_summary.items():
                print(f"   • {period.upper()}: {count:,} events")
        else:
            print("⚠️  No near-miss events detected")

        return self.near_miss_events

    def analyze_behavioral_changes(self):
        """Statistical analysis of behavioral changes"""
        print(f"\n📊 ANALYZING BEHAVIORAL CHANGES")

        results = {
            'analysis_date': datetime.now().isoformat(),
            'behavioral_changes': {}
        }

        # Analyze hard events
        if hasattr(self, 'hard_events') and not self.hard_events.empty:
            print("\n🎯 HARD EVENTS ANALYSIS:")

            for event_type in self.hard_events['event_type'].unique():
                event_data = self.hard_events[self.hard_events['event_type'] == event_type]

                before_events = event_data[event_data['period'] == 'before']
                after_events = event_data[event_data['period'] == 'after']

                # Calculate rates (events per trip or time period)
                before_count = len(before_events)
                after_count = len(after_events)

                # Get total GPS points for rate calculation
                before_points = len(self.gps_data[self.gps_data['period'] == 'before'])
                after_points = len(self.gps_data[self.gps_data['period'] == 'after'])

                before_rate = (before_count / before_points * 1000) if before_points > 0 else 0  # Events per 1000 GPS points
                after_rate = (after_count / after_points * 1000) if after_points > 0 else 0

                rate_change = ((after_rate - before_rate) / before_rate * 100) if before_rate > 0 else float('inf')

                print(f"\n   {event_type.upper().replace('_', ' ')}:")
                print(f"   • Before: {before_count:,} events ({before_rate:.2f} per 1000 points)")
                print(f"   • After: {after_count:,} events ({after_rate:.2f} per 1000 points)")
                print(f"   • Rate change: {rate_change:+.1f}%")

                # Statistical significance test (if sufficient data)
                if before_count >= 5 and after_count >= 5:
                    # Chi-square test for count data
                    contingency = [[before_count, before_points - before_count],
                                 [after_count, after_points - after_count]]
                    chi2, p_value = stats.chi2_contingency(contingency)[0:2]
                    significant = p_value < 0.05

                    print(f"   • Statistical test: {'✅ Significant' if significant else '❌ Not significant'} (p={p_value:.4f})")
                else:
                    print(f"   • Statistical test: Insufficient data")
                    significant = False
                    p_value = None

                results['behavioral_changes'][event_type] = {
                    'before_count': before_count,
                    'after_count': after_count,
                    'before_rate': before_rate,
                    'after_rate': after_rate,
                    'rate_change_percent': rate_change,
                    'statistically_significant': significant,
                    'p_value': p_value
                }

        # Analyze near-miss events
        if hasattr(self, 'near_miss_events') and not self.near_miss_events.empty:
            print(f"\n⚠️  NEAR-MISS EVENTS ANALYSIS:")

            before_near_misses = self.near_miss_events[self.near_miss_events['period'] == 'before']
            after_near_misses = self.near_miss_events[self.near_miss_events['period'] == 'after']

            before_count = len(before_near_misses)
            after_count = len(after_near_misses)

            # Calculate rates
            before_points = len(self.gps_data[self.gps_data['period'] == 'before'])
            after_points = len(self.gps_data[self.gps_data['period'] == 'after'])

            before_rate = (before_count / before_points * 10000) if before_points > 0 else 0  # Per 10,000 points
            after_rate = (after_count / after_points * 10000) if after_points > 0 else 0

            rate_change = ((after_rate - before_rate) / before_rate * 100) if before_rate > 0 else float('inf')

            print(f"   • Before: {before_count:,} near-misses ({before_rate:.2f} per 10,000 points)")
            print(f"   • After: {after_count:,} near-misses ({after_rate:.2f} per 10,000 points)")
            print(f"   • Rate change: {rate_change:+.1f}%")

            # Severity analysis
            if before_count > 0 and after_count > 0:
                before_severity = before_near_misses['severity_score'].mean()
                after_severity = after_near_misses['severity_score'].mean()
                severity_change = ((after_severity - before_severity) / before_severity * 100)

                print(f"   • Average severity change: {severity_change:+.1f}%")

            results['behavioral_changes']['near_misses'] = {
                'before_count': before_count,
                'after_count': after_count,
                'before_rate': before_rate,
                'after_rate': after_rate,
                'rate_change_percent': rate_change
            }

        self.behavior_results = results
        return results

    def save_behavioral_analysis_results(self):
        """Save behavioral analysis results"""
        print(f"\n💾 SAVING BEHAVIORAL ANALYSIS RESULTS")

        # Save hard events
        if hasattr(self, 'hard_events') and not self.hard_events.empty:
            hard_events_path = os.path.join(self.output_dir, "hard_driving_events.csv")
            self.hard_events.to_csv(hard_events_path, index=False)
            print(f"✅ Hard events: {hard_events_path}")

        # Save near-miss events
        if hasattr(self, 'near_miss_events') and not self.near_miss_events.empty:
            near_miss_path = os.path.join(self.output_dir, "near_miss_events.csv")
            self.near_miss_events.to_csv(near_miss_path, index=False)
            print(f"✅ Near-miss events: {near_miss_path}")

        # Save behavioral analysis summary
        if hasattr(self, 'behavior_results'):
            results_df = pd.DataFrame([self.behavior_results])
            results_path = os.path.join(self.output_dir, "behavioral_analysis_summary.csv")
            results_df.to_csv(results_path, index=False)
            print(f"✅ Behavioral summary: {results_path}")

        return True

def main():
    analyzer = DrivingBehaviorAnalysis()

    # Load GPS data
    if not analyzer.load_gps_data():
        print("❌ Cannot proceed without GPS data")
        return

    # Detect hard driving events
    analyzer.detect_hard_events()

    # Detect near-miss events (computationally intensive)
    analyzer.detect_near_miss_events()

    # Analyze behavioral changes
    analyzer.analyze_behavioral_changes()

    # Save results
    analyzer.save_behavioral_analysis_results()

    print(f"\n✅ BEHAVIORAL ANALYSIS COMPLETE")
    print("Hard braking, steering, and near-miss event analysis finished")

if __name__ == "__main__":
    main()
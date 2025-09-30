"""
GPS-Derived Behavioral Analysis
Calculate accelerations, G-forces, and detect driving events from raw GPS coordinates
"""

import pandas as pd
import numpy as np
from datetime import datetime
import math

class GPSDerivedAnalysis:
    def __init__(self):
        print("🛰️ GPS-DERIVED BEHAVIORAL ANALYSIS")
        print("Calculating accelerations, G-forces, and events from coordinate data")
        print("="*60)
        
    def load_gps_data(self, parquet_file):
        """Load and prepare GPS data from parquet file"""
        print(f"\n📡 Loading GPS data from {parquet_file}")
        
        df = pd.read_parquet(f"parquet_files/{parquet_file}")
        df['timestamp'] = pd.to_datetime(df['Point_RawTimestamp'], format='mixed')
        
        # Sort by vehicle and time for proper sequence analysis
        df = df.sort_values(['VehicleID', 'timestamp']).reset_index(drop=True)
        
        print(f"✅ Loaded {len(df):,} GPS points from {df['VehicleID'].nunique():,} vehicles")
        return df
        
    def calculate_haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two GPS points in meters"""
        R = 6371000  # Earth's radius in meters
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def calculate_bearing(self, lat1, lon1, lat2, lon2):
        """Calculate bearing (heading) between two GPS points in degrees"""
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        dlon = lon2 - lon1
        
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        bearing = math.atan2(y, x)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360  # Normalize to 0-360
        
        return bearing
    
    def derive_motion_metrics(self, df):
        """Calculate derived speed, acceleration, and heading from GPS"""
        print(f"\n🧮 CALCULATING DERIVED MOTION METRICS")
        
        results = []
        
        # Group by vehicle to calculate derivatives properly
        processed_count = 0
        for vehicle_id in df['VehicleID'].unique():
            vehicle_data = df[df['VehicleID'] == vehicle_id].copy()
            
            # Only process vehicles with substantial GPS tracks
            if len(vehicle_data) < 5:
                continue
                
            processed_count += 1
            if processed_count > 500:  # Process more vehicles but still manageable
                break
                
            # Calculate distances and time differences
            lats = vehicle_data['Point_RawLat'].values
            lons = vehicle_data['Point_RawLon'].values
            times = vehicle_data['timestamp'].values
            
            # Initialize arrays
            distances = np.zeros(len(vehicle_data))
            time_diffs = np.zeros(len(vehicle_data))
            derived_speeds = np.zeros(len(vehicle_data))
            bearings = np.zeros(len(vehicle_data))
            accelerations = np.zeros(len(vehicle_data))
            lateral_accelerations = np.zeros(len(vehicle_data))
            
            # Calculate point-to-point metrics
            for i in range(1, len(vehicle_data)):
                # Distance traveled
                dist = self.calculate_haversine_distance(
                    lats[i-1], lons[i-1], lats[i], lons[i]
                )
                distances[i] = dist
                
                # Time difference in seconds
                time_diff = (times[i] - times[i-1]) / np.timedelta64(1, 's')
                time_diffs[i] = time_diff
                
                # Derived speed (m/s then convert to km/h) - filter unrealistic values
                if time_diff > 0 and time_diff < 300:  # Ignore gaps >5 minutes
                    speed_ms = dist / time_diff
                    # Filter unrealistic speeds (>200 km/h likely GPS error)
                    if speed_ms * 3.6 < 200:
                        derived_speeds[i] = speed_ms * 3.6  # Convert to km/h
                
                # Bearing (heading)
                bearing = self.calculate_bearing(
                    lats[i-1], lons[i-1], lats[i], lons[i]
                )
                bearings[i] = bearing
                
            # Calculate accelerations from speed changes
            for i in range(2, len(vehicle_data)):
                if time_diffs[i] > 0:
                    # Longitudinal acceleration (speed change)
                    speed_change = (derived_speeds[i] - derived_speeds[i-1]) / 3.6  # m/s
                    accelerations[i] = speed_change / time_diffs[i]  # m/s²
                    
                    # Lateral acceleration (heading change)
                    bearing_change = bearings[i] - bearings[i-1]
                    # Handle wraparound (359° to 1°)
                    if bearing_change > 180:
                        bearing_change -= 360
                    elif bearing_change < -180:
                        bearing_change += 360
                    
                    if time_diffs[i] > 0:
                        angular_velocity = math.radians(bearing_change) / time_diffs[i]
                        # v²/r approximation for lateral acceleration
                        if derived_speeds[i] > 0:
                            lateral_accelerations[i] = (derived_speeds[i] / 3.6) * angular_velocity
            
            # Add calculated metrics to vehicle data
            vehicle_data = vehicle_data.copy()
            vehicle_data['derived_speed_kmh'] = derived_speeds
            vehicle_data['longitudinal_accel_ms2'] = accelerations
            vehicle_data['lateral_accel_ms2'] = lateral_accelerations
            vehicle_data['distance_m'] = distances
            vehicle_data['time_diff_s'] = time_diffs
            vehicle_data['bearing_deg'] = bearings
            
            # Calculate total G-force
            vehicle_data['derived_total_gforce'] = np.sqrt(
                accelerations**2 + lateral_accelerations**2
            ) / 9.81  # Convert m/s² to G-forces
            
            results.append(vehicle_data)
            
            if len(results) % 10 == 0:
                print(f"  Processed {len(results)} vehicles...")
        
        # Combine all results
        combined_df = pd.concat(results, ignore_index=True)
        
        print(f"✅ Calculated motion metrics for {len(results)} vehicles")
        print(f"   Records with derived data: {len(combined_df):,}")
        
        return combined_df
    
    def detect_driving_events(self, df):
        """Detect driving events from derived metrics"""
        print(f"\n🚨 DETECTING DRIVING EVENTS FROM DERIVED METRICS")
        
        # Define more realistic thresholds for GPS-derived data
        HARSH_BRAKING_THRESHOLD = -1.5  # m/s² (negative acceleration) - reduced for GPS noise
        HARSH_ACCELERATION_THRESHOLD = 1.5  # m/s² - reduced for GPS noise  
        HARSH_STEERING_THRESHOLD = 1.0  # m/s² lateral - reduced for GPS noise
        HIGH_GFORCE_THRESHOLD = 0.15  # G-forces - reduced for GPS-derived data
        SPEED_VIOLATION_THRESHOLD = 110  # km/h
        
        events = []
        
        # Harsh braking events
        harsh_braking = df[df['longitudinal_accel_ms2'] < HARSH_BRAKING_THRESHOLD].copy()
        for _, event in harsh_braking.iterrows():
            events.append({
                'event_type': 'harsh_braking',
                'vehicle_id': event['VehicleID'],
                'timestamp': event['timestamp'],
                'latitude': event['Point_RawLat'],
                'longitude': event['Point_RawLon'],
                'derived_speed': event['derived_speed_kmh'],
                'longitudinal_accel': event['longitudinal_accel_ms2'],
                'lateral_accel': event['lateral_accel_ms2'],
                'total_gforce': event['derived_total_gforce'],
                'severity': abs(event['longitudinal_accel_ms2'])
            })
        
        # Harsh acceleration events  
        harsh_accel = df[df['longitudinal_accel_ms2'] > HARSH_ACCELERATION_THRESHOLD].copy()
        for _, event in harsh_accel.iterrows():
            events.append({
                'event_type': 'harsh_acceleration',
                'vehicle_id': event['VehicleID'],
                'timestamp': event['timestamp'],
                'latitude': event['Point_RawLat'],
                'longitude': event['Point_RawLon'],
                'derived_speed': event['derived_speed_kmh'],
                'longitudinal_accel': event['longitudinal_accel_ms2'],
                'lateral_accel': event['lateral_accel_ms2'],
                'total_gforce': event['derived_total_gforce'],
                'severity': event['longitudinal_accel_ms2']
            })
        
        # Harsh steering events
        harsh_steering = df[abs(df['lateral_accel_ms2']) > HARSH_STEERING_THRESHOLD].copy()
        for _, event in harsh_steering.iterrows():
            events.append({
                'event_type': 'harsh_steering',
                'vehicle_id': event['VehicleID'],
                'timestamp': event['timestamp'],
                'latitude': event['Point_RawLat'],
                'longitude': event['Point_RawLon'],
                'derived_speed': event['derived_speed_kmh'],
                'longitudinal_accel': event['longitudinal_accel_ms2'],
                'lateral_accel': event['lateral_accel_ms2'],
                'total_gforce': event['derived_total_gforce'],
                'severity': abs(event['lateral_accel_ms2'])
            })
        
        # High G-force events
        high_gforce = df[df['derived_total_gforce'] > HIGH_GFORCE_THRESHOLD].copy()
        for _, event in high_gforce.iterrows():
            events.append({
                'event_type': 'high_gforce',
                'vehicle_id': event['VehicleID'],
                'timestamp': event['timestamp'],
                'latitude': event['Point_RawLat'],
                'longitude': event['Point_RawLon'],
                'derived_speed': event['derived_speed_kmh'],
                'longitudinal_accel': event['longitudinal_accel_ms2'],
                'lateral_accel': event['lateral_accel_ms2'],
                'total_gforce': event['derived_total_gforce'],
                'severity': event['derived_total_gforce']
            })
        
        # Speed violations
        speed_violations = df[df['derived_speed_kmh'] > SPEED_VIOLATION_THRESHOLD].copy()
        for _, event in speed_violations.iterrows():
            events.append({
                'event_type': 'speed_violation',
                'vehicle_id': event['VehicleID'],
                'timestamp': event['timestamp'],
                'latitude': event['Point_RawLat'],
                'longitude': event['Point_RawLon'],
                'derived_speed': event['derived_speed_kmh'],
                'longitudinal_accel': event['longitudinal_accel_ms2'],
                'lateral_accel': event['lateral_accel_ms2'],
                'total_gforce': event['derived_total_gforce'],
                'severity': event['derived_speed_kmh'] - SPEED_VIOLATION_THRESHOLD
            })
        
        events_df = pd.DataFrame(events)
        
        if len(events_df) > 0:
            print(f"🚨 DETECTED EVENTS SUMMARY:")
            event_counts = events_df['event_type'].value_counts()
            for event_type, count in event_counts.items():
                print(f"• {event_type}: {count:,} events")
            
            print(f"\nTop 5 most severe events by type:")
            for event_type in event_counts.index:
                top_events = events_df[events_df['event_type'] == event_type].nlargest(5, 'severity')
                print(f"\n{event_type.upper()}:")
                for _, event in top_events.iterrows():
                    print(f"  {event['timestamp']}: {event['severity']:.2f} severity at {event['derived_speed']:.1f} km/h")
        
        return events_df
    
    def compare_with_compass_data(self, our_events, compass_file):
        """Compare our detected events with Compass IOT's results"""
        print(f"\n🔍 COMPARING WITH COMPASS IOT RESULTS")
        
        compass_df = pd.read_csv(compass_file)
        compass_df['timestamp'] = pd.to_datetime(compass_df['local_Timestamp'])
        
        print(f"Our events: {len(our_events):,}")
        print(f"Compass events: {len(compass_df):,}")
        
        # Compare by overlapping vehicles
        our_vehicles = set(our_events['vehicle_id'].unique()) if len(our_events) > 0 else set()
        compass_vehicles = set(compass_df['VehicleID'].unique())
        
        overlap_vehicles = our_vehicles.intersection(compass_vehicles)
        print(f"Overlapping vehicles: {len(overlap_vehicles):,}")
        
        if len(overlap_vehicles) > 0:
            print(f"Vehicle overlap: {len(overlap_vehicles)/min(len(our_vehicles), len(compass_vehicles))*100:.1f}%")

def main():
    analyzer = GPSDerivedAnalysis()
    
    # Process first parquet file as test
    test_file = "support.nz_gettingdistance-fafb97a7d07df2990ff2ffa0-000000000000.parquet"
    
    # Load and analyze
    gps_data = analyzer.load_gps_data(test_file)
    derived_data = analyzer.derive_motion_metrics(gps_data)
    
    # Detect events
    our_events = analyzer.detect_driving_events(derived_data)
    
    # Compare with Compass data
    compass_file = "support.nz_christchurch_nearmisses-ed71ff0e713ef10baadc4371-000000000000.csv"
    analyzer.compare_with_compass_data(our_events, compass_file)
    
    # Save our results
    if len(our_events) > 0:
        our_events.to_csv('gps_derived_events.csv', index=False)
        print(f"\n💾 Saved our events to: gps_derived_events.csv")
    
    # Save derived metrics sample
    derived_data.to_csv('gps_derived_metrics_sample.csv', index=False)
    print(f"💾 Saved derived metrics to: gps_derived_metrics_sample.csv")

if __name__ == "__main__":
    main()
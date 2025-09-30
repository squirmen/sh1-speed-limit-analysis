"""
Replicate Compass IOT Near-Miss Detection
Use same raw GPS data to replicate their 265 near-miss events
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
from gps_derived_behaviors import GPSDerivedAnalysis

class CompassReplicationAnalysis:
    def __init__(self):
        print("🔄 REPLICATING COMPASS IOT NEAR-MISS DETECTION")
        print("Using same raw GPS data to match their methodology")
        print("="*60)
        
    def load_compass_events(self):
        """Load Compass IOT events for comparison"""
        self.compass_events = pd.read_csv(
            '/Users/timwelch/Dropbox/Files/Research/Compass_Data/SH1_Study/Data/connected_vehicle_data/support.nz_christchurch_nearmisses-ed71ff0e713ef10baadc4371-000000000000.csv'
        )
        self.compass_events['timestamp'] = pd.to_datetime(self.compass_events['local_Timestamp'])
        
        print(f"📊 Compass IOT Events:")
        print(f"• Total events: {len(self.compass_events):,}")
        print(f"• Unique vehicles: {self.compass_events['VehicleID'].nunique():,}")
        print(f"• Date range: {self.compass_events['timestamp'].min()} to {self.compass_events['timestamp'].max()}")
        
        # Event types
        print(f"• Event types: {self.compass_events['nm_Classification'].value_counts().to_dict()}")
        
        # G-force statistics
        print(f"• G-force range: {self.compass_events['TotalGForce'].min():.3f} to {self.compass_events['TotalGForce'].max():.3f}")
        print(f"• G-force mean: {self.compass_events['TotalGForce'].mean():.3f}")
        
        return True
        
    def analyze_compass_thresholds(self):
        """Reverse engineer Compass IOT thresholds"""
        print(f"\n🔍 REVERSE ENGINEERING COMPASS THRESHOLDS")
        
        # Analyze their G-force distribution
        gforce_stats = self.compass_events['TotalGForce'].describe()
        print(f"G-Force Distribution:")
        for percentile in [25, 50, 75, 90, 95, 99]:
            value = self.compass_events['TotalGForce'].quantile(percentile/100)
            print(f"  {percentile}th percentile: {value:.3f}g")
            
        # Analyze by event type
        print(f"\nBy Event Type:")
        for event_type in self.compass_events['nm_Classification'].unique():
            type_data = self.compass_events[self.compass_events['nm_Classification'] == event_type]
            print(f"  {event_type}:")
            print(f"    Count: {len(type_data)}")
            print(f"    G-force: {type_data['TotalGForce'].min():.3f} - {type_data['TotalGForce'].max():.3f} (mean: {type_data['TotalGForce'].mean():.3f})")
            print(f"    Speed: {type_data['speed'].min():.1f} - {type_data['speed'].max():.1f} km/h (mean: {type_data['speed'].mean():.1f})")
            
        # Inferred thresholds
        min_gforce = self.compass_events['TotalGForce'].min()
        print(f"\n🎯 INFERRED THRESHOLDS:")
        print(f"• Minimum G-force threshold: ~{min_gforce:.3f}g")
        print(f"• This suggests they use hardware sensors (precise measurements)")
        print(f"• Our GPS-derived method needs calibration to match")
        
        return {
            'min_gforce': min_gforce,
            'mean_gforce': self.compass_events['TotalGForce'].mean(),
            'steering_min': self.compass_events[self.compass_events['nm_Classification']=='Steering']['TotalGForce'].min(),
            'braking_min': self.compass_events[self.compass_events['nm_Classification']=='Braking']['TotalGForce'].min()
        }
        
    def find_overlapping_vehicles(self):
        """Find vehicles that appear in both datasets"""
        print(f"\n🔍 FINDING OVERLAPPING VEHICLES")
        
        # Load our GPS data to get vehicle IDs
        parquet_files = glob.glob('/Users/timwelch/Dropbox/Files/Research/Compass_Data/SH1_Study/Data/connected_vehicle_data/parquet_files/*.parquet')
        
        our_vehicle_ids = set()
        sample_files = parquet_files[:10]  # Sample first 10 files
        
        for i, file in enumerate(sample_files):
            try:
                df = pd.read_parquet(file)
                our_vehicle_ids.update(df['VehicleID'].unique())
                print(f"  Processed file {i+1}/{len(sample_files)}: {len(df['VehicleID'].unique())} vehicles")
            except Exception as e:
                print(f"  Error reading {file}: {e}")
                
        compass_vehicle_ids = set(self.compass_events['VehicleID'].unique())
        
        overlapping_vehicles = our_vehicle_ids.intersection(compass_vehicle_ids)
        
        print(f"\nVehicle Overlap Analysis:")
        print(f"• Our GPS data: {len(our_vehicle_ids):,} unique vehicles")
        print(f"• Compass events: {len(compass_vehicle_ids):,} unique vehicles") 
        print(f"• Overlapping vehicles: {len(overlapping_vehicles):,}")
        
        if len(overlapping_vehicles) > 0:
            overlap_pct = len(overlapping_vehicles) / len(compass_vehicle_ids) * 100
            print(f"• Overlap percentage: {overlap_pct:.1f}%")
            
            # Sample overlapping vehicles for detailed analysis
            sample_vehicles = list(overlapping_vehicles)[:5]
            print(f"• Sample overlapping vehicles: {sample_vehicles}")
            
            return overlapping_vehicles
        else:
            print("❌ No overlapping vehicles found - different vehicle fleets or ID formats")
            return set()
            
    def attempt_threshold_calibration(self, compass_thresholds):
        """Attempt to calibrate our thresholds to match Compass results"""
        print(f"\n⚙️ CALIBRATING THRESHOLDS TO MATCH COMPASS")
        
        # Load our comprehensive events
        our_events = pd.read_csv('/Users/timwelch/Dropbox/Files/Research/Compass_Data/SH1_Study/Data/connected_vehicle_data/comprehensive_gps_events.csv')
        our_events['timestamp'] = pd.to_datetime(our_events['timestamp'])
        
        print(f"Starting with {len(our_events):,} our events")
        
        # Try progressively stricter thresholds to match Compass count
        target_count = len(self.compass_events)  # 265 events
        
        threshold_tests = [
            {'name': 'Current', 'gforce_min': 0.15, 'severity_min': 0},
            {'name': 'Conservative', 'gforce_min': 0.25, 'severity_min': 2.0},
            {'name': 'Strict', 'gforce_min': 0.35, 'severity_min': 4.0},
            {'name': 'Very Strict', 'gforce_min': 0.45, 'severity_min': 6.0},
            {'name': 'Extreme', 'gforce_min': compass_thresholds['min_gforce'], 'severity_min': 8.0}
        ]
        
        print(f"Testing thresholds to match {target_count} events:")
        
        best_match = None
        best_diff = float('inf')
        
        for test in threshold_tests:
            # Filter events by criteria
            filtered = our_events[
                ((our_events['event_type'] == 'high_gforce') & (our_events['severity'] >= test['gforce_min'])) |
                ((our_events['event_type'] == 'harsh_steering') & (our_events['severity'] >= test['severity_min'])) |
                ((our_events['event_type'] == 'harsh_braking') & (our_events['severity'] >= test['severity_min'])) |
                ((our_events['event_type'] == 'speed_violation') & (our_events['derived_speed'] > 120))
            ]
            
            count = len(filtered)
            diff = abs(count - target_count)
            
            print(f"  {test['name']:<12}: {count:4d} events (diff: {diff:+4d})")
            
            if diff < best_diff:
                best_diff = diff
                best_match = test
                best_filtered = filtered.copy()
        
        print(f"\n🎯 BEST MATCH: {best_match['name']} threshold")
        print(f"   Our calibrated: {len(best_filtered)} events")
        print(f"   Compass target: {target_count} events")
        print(f"   Difference: {best_diff} events ({best_diff/target_count*100:.1f}%)")
        
        # Save calibrated events
        best_filtered.to_csv('/Users/timwelch/PyCharmMiscProject/calibrated_near_miss_events.csv', index=False)
        
        return best_filtered, best_match
        
    def compare_calibrated_results(self, calibrated_events):
        """Compare our calibrated results with Compass"""
        print(f"\n📊 CALIBRATED RESULTS COMPARISON")
        print("="*50)
        
        print(f"Event Counts:")
        print(f"• Our calibrated: {len(calibrated_events):,}")
        print(f"• Compass original: {len(self.compass_events):,}")
        print(f"• Ratio: {len(calibrated_events)/len(self.compass_events):.2f}:1")
        
        # Temporal comparison
        speed_change_date = pd.to_datetime("2025-04-13")
        
        our_before = calibrated_events[calibrated_events['timestamp'] < speed_change_date]
        our_after = calibrated_events[calibrated_events['timestamp'] >= speed_change_date]
        
        compass_before = self.compass_events[self.compass_events['timestamp'] < speed_change_date]
        compass_after = self.compass_events[self.compass_events['timestamp'] >= speed_change_date]
        
        print(f"\nBefore/After Comparison:")
        print(f"                    Before    After    Change")
        print(f"Our calibrated:     {len(our_before):6d}   {len(our_after):6d}   {(len(our_after)-len(our_before))/max(len(our_before),1)*100:+6.1f}%")
        print(f"Compass original:   {len(compass_before):6d}   {len(compass_after):6d}   {(len(compass_after)-len(compass_before))/max(len(compass_before),1)*100:+6.1f}%")
        
        # Event type comparison
        print(f"\nEvent Type Comparison:")
        our_types = calibrated_events['event_type'].value_counts()
        compass_types = self.compass_events['nm_Classification'].value_counts()
        
        print(f"Our calibrated event types:")
        for event_type, count in our_types.items():
            print(f"  {event_type}: {count}")
            
        print(f"Compass event types:")
        for event_type, count in compass_types.items():
            print(f"  {event_type}: {count}")
            
        return {
            'our_total': len(calibrated_events),
            'compass_total': len(self.compass_events),
            'our_before': len(our_before),
            'our_after': len(our_after),
            'compass_before': len(compass_before),
            'compass_after': len(compass_after)
        }

def main():
    analyzer = CompassReplicationAnalysis()
    
    # Load Compass events
    if analyzer.load_compass_events():
        # Analyze their thresholds
        compass_thresholds = analyzer.analyze_compass_thresholds()
        
        # Find overlapping vehicles
        overlapping_vehicles = analyzer.find_overlapping_vehicles()
        
        # Calibrate our thresholds
        calibrated_events, best_threshold = analyzer.attempt_threshold_calibration(compass_thresholds)
        
        # Compare results
        comparison = analyzer.compare_calibrated_results(calibrated_events)
        
        print(f"\n✅ COMPASS REPLICATION ANALYSIS COMPLETE")
        print(f"Successfully calibrated our method to detect {comparison['our_total']} near-miss events")
        print(f"vs Compass's {comparison['compass_total']} events ({comparison['our_total']/comparison['compass_total']:.2f}:1 ratio)")

if __name__ == "__main__":
    main()
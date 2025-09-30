"""
Comprehensive GPS-Derived Analysis Pipeline
Process multiple parquet files and create complete behavioral analysis
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from gps_derived_behaviors import GPSDerivedAnalysis

class ComprehensiveAnalysis:
    def __init__(self):
        self.speed_change_date = pd.to_datetime("2025-04-13")
        
        print("🚀 COMPREHENSIVE GPS-DERIVED ANALYSIS PIPELINE")
        print("Processing multiple parquet files for complete behavioral analysis")
        print("="*60)
        
    def process_multiple_parquet_files(self, num_files=10):
        """Process multiple parquet files to get comprehensive dataset"""
        print(f"\n📂 PROCESSING MULTIPLE PARQUET FILES")
        print(f"Target: {num_files} files for comprehensive analysis")
        
        parquet_files = glob.glob("parquet_files/*.parquet")[:num_files]
        print(f"Found {len(parquet_files)} parquet files")
        
        all_events = []
        all_metrics = []
        processed_files = 0
        
        analyzer = GPSDerivedAnalysis()
        
        for i, parquet_file in enumerate(parquet_files):
            try:
                print(f"\n🔄 Processing file {i+1}/{len(parquet_files)}: {os.path.basename(parquet_file)}")
                
                # Load GPS data
                gps_data = analyzer.load_gps_data(os.path.basename(parquet_file))
                
                # Calculate derived metrics (limit vehicles per file to manage memory)
                derived_data = analyzer.derive_motion_metrics(gps_data)
                
                if len(derived_data) > 0:
                    # Detect events
                    events = analyzer.detect_driving_events(derived_data)
                    
                    if len(events) > 0:
                        events['source_file'] = os.path.basename(parquet_file)
                        all_events.append(events)
                    
                    # Store sample of metrics
                    derived_sample = derived_data.sample(n=min(1000, len(derived_data)))
                    derived_sample['source_file'] = os.path.basename(parquet_file)
                    all_metrics.append(derived_sample)
                    
                processed_files += 1
                
                print(f"   ✅ Events detected: {len(events) if len(events) > 0 else 0}")
                
            except Exception as e:
                print(f"   ❌ Error processing {parquet_file}: {str(e)}")
                continue
        
        # Combine all results
        if all_events:
            combined_events = pd.concat(all_events, ignore_index=True)
            combined_events.to_csv('comprehensive_gps_events.csv', index=False)
            print(f"\n💾 Saved {len(combined_events):,} total events to comprehensive_gps_events.csv")
        else:
            combined_events = pd.DataFrame()
        
        if all_metrics:
            combined_metrics = pd.concat(all_metrics, ignore_index=True)
            combined_metrics.to_csv('comprehensive_gps_metrics.csv', index=False)
            print(f"💾 Saved {len(combined_metrics):,} metric records to comprehensive_gps_metrics.csv")
        else:
            combined_metrics = pd.DataFrame()
            
        return combined_events, combined_metrics
        
    def cross_validate_with_compass(self, our_events):
        """Cross-validate our events with Compass IOT data"""
        print(f"\n🔍 CROSS-VALIDATION WITH COMPASS IOT")
        print("="*50)
        
        # Load Compass data
        compass_df = pd.read_csv("support.nz_christchurch_nearmisses-ed71ff0e713ef10baadc4371-000000000000.csv")
        compass_df['timestamp'] = pd.to_datetime(compass_df['local_Timestamp'])
        
        print(f"📊 Dataset Comparison:")
        print(f"• Our events: {len(our_events):,}")
        print(f"• Compass events: {len(compass_df):,}")
        print(f"• Our unique vehicles: {our_events['vehicle_id'].nunique():,}")
        print(f"• Compass unique vehicles: {compass_df['VehicleID'].nunique():,}")
        
        # Check vehicle overlap
        our_vehicles = set(our_events['vehicle_id'].unique())
        compass_vehicles = set(compass_df['VehicleID'].unique())
        overlapping_vehicles = our_vehicles.intersection(compass_vehicles)
        
        print(f"\n🔄 Vehicle Overlap Analysis:")
        print(f"• Overlapping vehicles: {len(overlapping_vehicles):,}")
        if len(our_vehicles) > 0 and len(compass_vehicles) > 0:
            overlap_pct = len(overlapping_vehicles) / min(len(our_vehicles), len(compass_vehicles)) * 100
            print(f"• Overlap percentage: {overlap_pct:.1f}%")
        
        # Temporal analysis
        our_events['timestamp'] = pd.to_datetime(our_events['timestamp'])
        
        print(f"\n📅 Temporal Coverage:")
        print(f"• Our events: {our_events['timestamp'].min()} to {our_events['timestamp'].max()}")
        print(f"• Compass events: {compass_df['timestamp'].min()} to {compass_df['timestamp'].max()}")
        
        # Before/after analysis
        our_before = our_events[our_events['timestamp'] < self.speed_change_date]
        our_after = our_events[our_events['timestamp'] >= self.speed_change_date]
        compass_before = compass_df[compass_df['timestamp'] < self.speed_change_date]
        compass_after = compass_df[compass_df['timestamp'] >= self.speed_change_date]
        
        print(f"\n📊 Before/After Speed Limit Change (April 13, 2025):")
        print(f"• Our events - Before: {len(our_before):,}, After: {len(our_after):,}")
        print(f"• Compass events - Before: {len(compass_before):,}, After: {len(compass_after):,}")
        
        if len(overlapping_vehicles) > 0:
            print(f"\n🎯 Event Rate Analysis for Overlapping Vehicles:")
            
            # Calculate event rates for overlapping vehicles
            for vehicle_id in list(overlapping_vehicles)[:5]:  # Sample first 5
                our_vehicle_events = our_events[our_events['vehicle_id'] == vehicle_id]
                compass_vehicle_events = compass_df[compass_df['VehicleID'] == vehicle_id]
                
                print(f"• Vehicle {vehicle_id[:8]}...: Our={len(our_vehicle_events)} events, Compass={len(compass_vehicle_events)} events")
        
        return overlapping_vehicles
        
    def analyze_event_patterns(self, events_df):
        """Analyze patterns in detected events"""
        print(f"\n📈 EVENT PATTERN ANALYSIS")
        print("="*50)
        
        if len(events_df) == 0:
            print("❌ No events to analyze")
            return
            
        # Event type distribution
        print(f"Event Type Distribution:")
        event_counts = events_df['event_type'].value_counts()
        for event_type, count in event_counts.items():
            pct = count / len(events_df) * 100
            print(f"• {event_type}: {count:,} events ({pct:.1f}%)")
        
        # Severity analysis
        print(f"\nSeverity Analysis:")
        severity_stats = events_df.groupby('event_type')['severity'].agg(['count', 'mean', 'std', 'max'])
        print(severity_stats.round(3))
        
        # Temporal patterns
        events_df['timestamp'] = pd.to_datetime(events_df['timestamp'])
        events_df['hour'] = events_df['timestamp'].dt.hour
        events_df['day_of_week'] = events_df['timestamp'].dt.day_name()
        events_df['month'] = events_df['timestamp'].dt.month
        
        print(f"\nTemporal Patterns:")
        print(f"• Peak hour: {events_df['hour'].mode().iloc[0]}:00 ({events_df[events_df['hour'] == events_df['hour'].mode().iloc[0]].shape[0]} events)")
        print(f"• Most active day: {events_df['day_of_week'].mode().iloc[0]} ({events_df[events_df['day_of_week'] == events_df['day_of_week'].mode().iloc[0]].shape[0]} events)")
        
        # Speed correlation
        if 'derived_speed' in events_df.columns:
            speed_corr = events_df['derived_speed'].corr(events_df['severity'])
            print(f"• Speed-severity correlation: {speed_corr:.3f}")
            
        # Before/after analysis
        before_events = events_df[events_df['timestamp'] < self.speed_change_date]
        after_events = events_df[events_df['timestamp'] >= self.speed_change_date]
        
        print(f"\nBefore/After Speed Limit Change:")
        print(f"• Before April 13: {len(before_events):,} events")
        print(f"• After April 13: {len(after_events):,} events")
        
        if len(before_events) > 0 and len(after_events) > 0:
            # Calculate rates per day
            before_days = (self.speed_change_date - before_events['timestamp'].min()).days
            after_days = (after_events['timestamp'].max() - self.speed_change_date).days
            
            before_rate = len(before_events) / max(before_days, 1)
            after_rate = len(after_events) / max(after_days, 1)
            rate_change = (after_rate - before_rate) / before_rate * 100 if before_rate > 0 else 0
            
            print(f"• Event rate change: {rate_change:+.1f}% ({before_rate:.2f} → {after_rate:.2f} events/day)")
        
        return event_counts, severity_stats
        
    def generate_comprehensive_report(self, events_df, metrics_df, overlapping_vehicles):
        """Generate comprehensive analysis report"""
        print(f"\n📋 COMPREHENSIVE ANALYSIS REPORT")
        print("="*60)
        
        report = {
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_events_detected': len(events_df),
            'total_vehicles_processed': events_df['vehicle_id'].nunique() if len(events_df) > 0 else 0,
            'total_gps_records_processed': len(metrics_df),
            'parquet_files_processed': metrics_df['source_file'].nunique() if len(metrics_df) > 0 else 0,
            'compass_overlap_vehicles': len(overlapping_vehicles),
            'detection_success_rate': len(events_df) / len(metrics_df) * 100 if len(metrics_df) > 0 else 0
        }
        
        print(f"🎯 KEY METRICS:")
        for key, value in report.items():
            if isinstance(value, float):
                print(f"• {key.replace('_', ' ').title()}: {value:.2f}")
            else:
                print(f"• {key.replace('_', ' ').title()}: {value:,}")
        
        # Save report
        report_df = pd.DataFrame([report])
        report_df.to_csv('comprehensive_analysis_report.csv', index=False)
        
        print(f"\n💾 Analysis complete! Files saved:")
        print(f"• comprehensive_gps_events.csv - {len(events_df):,} detected events")
        print(f"• comprehensive_gps_metrics.csv - {len(metrics_df):,} processed GPS records")
        print(f"• comprehensive_analysis_report.csv - Summary report")
        
        return report

def main():
    analyzer = ComprehensiveAnalysis()
    
    # Process multiple parquet files
    events_df, metrics_df = analyzer.process_multiple_parquet_files(num_files=20)
    
    if len(events_df) > 0:
        # Cross-validate with Compass data
        overlapping_vehicles = analyzer.cross_validate_with_compass(events_df)
        
        # Analyze patterns
        event_counts, severity_stats = analyzer.analyze_event_patterns(events_df)
        
        # Generate comprehensive report
        report = analyzer.generate_comprehensive_report(events_df, metrics_df, overlapping_vehicles)
    else:
        print("❌ No events detected across processed files")

if __name__ == "__main__":
    main()
"""
SH1 Safety Analysis - Near Miss Events Before/After Speed Change
Analyzes safety impacts using the preprocessed near-miss data from Compass IOT
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from scipy import stats

class SH1SafetyAnalysis:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.speed_change_date = pd.to_datetime("2025-04-13")
        
        print("🛡️ SH1 Safety Impact Analysis")
        print(f"📅 Speed change date: {self.speed_change_date.strftime('%Y-%m-%d')}")
        
    def load_near_miss_data(self):
        """Load the near-miss data"""
        # Find near-miss files
        near_miss_files = []
        for filename in os.listdir(self.data_dir):
            if 'nearmisses' in filename and filename.endswith('.csv'):
                near_miss_files.append(filename)
        
        if not near_miss_files:
            print("❌ No near-miss files found")
            return False
            
        print(f"📂 Found near-miss files: {near_miss_files}")
        
        # Load all near-miss data
        all_data = []
        for filename in near_miss_files:
            filepath = os.path.join(self.data_dir, filename)
            try:
                df = pd.read_csv(filepath)
                df['source_file'] = filename
                all_data.append(df)
                print(f"  📊 Loaded {len(df)} events from {filename}")
            except Exception as e:
                print(f"  ❌ Error loading {filename}: {e}")
        
        if not all_data:
            print("❌ No near-miss data loaded successfully")
            return False
            
        self.near_miss_data = pd.concat(all_data, ignore_index=True)
        print(f"✅ Total near-miss events loaded: {len(self.near_miss_data)}")
        
        # Process timestamps and periods
        self.near_miss_data['timestamp'] = pd.to_datetime(self.near_miss_data['local_Timestamp'])
        self.near_miss_data['period'] = self.near_miss_data['timestamp'].apply(
            lambda x: 'before' if x < self.speed_change_date else 'after'
        )
        
        return True
    
    def analyze_near_misses(self):
        """Analyze near-miss events before/after speed change"""
        print(f"\n🚨 NEAR-MISS ANALYSIS")
        
        # Basic statistics
        before_events = self.near_miss_data[self.near_miss_data['period'] == 'before']
        after_events = self.near_miss_data[self.near_miss_data['period'] == 'after']
        
        print(f"Before period: {len(before_events):,} events")
        print(f"After period:  {len(after_events):,} events")
        
        if len(before_events) == 0 or len(after_events) == 0:
            print("❌ Insufficient data for before/after comparison")
            return
        
        # Analyze by event type
        self._analyze_by_event_type(before_events, after_events)
        
        # Analyze by time of day
        self._analyze_by_time_of_day()
        
        # Analyze severity metrics
        self._analyze_severity(before_events, after_events)
        
        # Spatial analysis
        self._spatial_analysis()
    
    def _analyze_by_event_type(self, before_events, after_events):
        """Analyze near-miss events by type (steering vs braking)"""
        print(f"\n📊 ANALYSIS BY EVENT TYPE")
        
        # Event type breakdown
        before_types = before_events['nm_Classification'].value_counts()
        after_types = after_events['nm_Classification'].value_counts()
        
        print("Before period event types:")
        for event_type, count in before_types.items():
            print(f"  {event_type}: {count:,} events")
        
        print("After period event types:")
        for event_type, count in after_types.items():
            print(f"  {event_type}: {count:,} events")
        
        # Calculate rates (events per day)
        before_days = (before_events['timestamp'].max() - before_events['timestamp'].min()).days
        after_days = (after_events['timestamp'].max() - after_events['timestamp'].min()).days
        
        if before_days > 0 and after_days > 0:
            print(f"\nDaily event rates:")
            print(f"Before period: {len(before_events)/before_days:.2f} events/day")
            print(f"After period:  {len(after_events)/after_days:.2f} events/day")
            
            rate_change = (len(after_events)/after_days) - (len(before_events)/before_days)
            print(f"Change: {rate_change:+.2f} events/day ({rate_change/(len(before_events)/before_days)*100:+.1f}%)")
    
    def _analyze_by_time_of_day(self):
        """Analyze near-miss patterns by time of day"""
        print(f"\n⏰ TIME-OF-DAY PATTERNS")
        
        # Add hour and time period classifications
        self.near_miss_data['hour'] = self.near_miss_data['timestamp'].dt.hour
        
        def classify_time_period(hour):
            if 6 <= hour < 9:
                return "morning_peak"
            elif 16 <= hour < 19:
                return "evening_peak"
            elif 9 <= hour < 16:
                return "midday"
            else:
                return "off_peak"
        
        self.near_miss_data['time_period'] = self.near_miss_data['hour'].apply(classify_time_period)
        
        # Analyze by time period
        time_analysis = self.near_miss_data.groupby(['period', 'time_period']).size().unstack(fill_value=0)
        print("\nEvents by time period:")
        print(time_analysis)
        
        # Calculate percentage change
        if 'before' in time_analysis.index and 'after' in time_analysis.index:
            pct_change = ((time_analysis.loc['after'] - time_analysis.loc['before']) / 
                         time_analysis.loc['before'] * 100)
            print(f"\nPercentage change by time period:")
            for period, change in pct_change.items():
                print(f"  {period}: {change:+.1f}%")
    
    def _analyze_severity(self, before_events, after_events):
        """Analyze severity metrics"""
        print(f"\n⚡ SEVERITY ANALYSIS")
        
        # G-force analysis
        if 'TotalGForce' in self.near_miss_data.columns:
            before_gforce = before_events['TotalGForce'].mean()
            after_gforce = after_events['TotalGForce'].mean()
            
            print(f"Average G-Force:")
            print(f"  Before: {before_gforce:.3f}g")
            print(f"  After:  {after_gforce:.3f}g")
            print(f"  Change: {after_gforce - before_gforce:+.3f}g")
        
        # Speed analysis during events
        if 'speed' in self.near_miss_data.columns:
            before_speed = before_events['speed'].mean()
            after_speed = after_events['speed'].mean()
            
            print(f"\nAverage speed during events:")
            print(f"  Before: {before_speed:.1f} km/h")
            print(f"  After:  {after_speed:.1f} km/h")
            print(f"  Change: {after_speed - before_speed:+.1f} km/h")
        
        # High-speed events analysis
        if 'HighestSpeed' in self.near_miss_data.columns:
            before_high_speed = before_events['HighestSpeed'].mean()
            after_high_speed = after_events['HighestSpeed'].mean()
            
            print(f"\nHighest speed during events:")
            print(f"  Before: {before_high_speed:.1f} km/h")
            print(f"  After:  {after_high_speed:.1f} km/h")
            print(f"  Change: {after_high_speed - before_high_speed:+.1f} km/h")
    
    def _spatial_analysis(self):
        """Analyze spatial patterns of near-miss events"""
        print(f"\n🗺️ SPATIAL ANALYSIS")
        
        # Road class analysis
        if 'osm_roadclass' in self.near_miss_data.columns:
            road_analysis = self.near_miss_data.groupby(['period', 'osm_roadclass']).size().unstack(fill_value=0)
            print("Events by road class:")
            print(road_analysis)
    
    def statistical_significance(self):
        """Test statistical significance of changes"""
        print(f"\n📈 STATISTICAL SIGNIFICANCE")
        
        before_events = self.near_miss_data[self.near_miss_data['period'] == 'before']
        after_events = self.near_miss_data[self.near_miss_data['period'] == 'after']
        
        # Test for difference in event rates
        before_days = (before_events['timestamp'].max() - before_events['timestamp'].min()).days
        after_days = (after_events['timestamp'].max() - after_events['timestamp'].min()).days
        
        if before_days > 0 and after_days > 0:
            before_rate = len(before_events) / before_days
            after_rate = len(after_events) / after_days
            
            # Chi-square test for rate difference
            observed = [len(before_events), len(after_events)]
            expected_total = sum(observed)
            expected = [expected_total * before_days / (before_days + after_days),
                       expected_total * after_days / (before_days + after_days)]
            
            chi2, p_value = stats.chisquare(observed, expected)
            significance = "significant" if p_value < 0.05 else "not significant"
            
            print(f"Event rate change test:")
            print(f"  Chi-square: {chi2:.3f}")
            print(f"  p-value: {p_value:.3f}")
            print(f"  Result: {significance} at α=0.05")
    
    def generate_summary_report(self):
        """Generate summary report"""
        print(f"\n📋 SAFETY IMPACT SUMMARY")
        print("=" * 50)
        
        before_events = self.near_miss_data[self.near_miss_data['period'] == 'before']
        after_events = self.near_miss_data[self.near_miss_data['period'] == 'after']
        
        # Calculate key metrics
        before_days = (before_events['timestamp'].max() - before_events['timestamp'].min()).days
        after_days = (after_events['timestamp'].max() - after_events['timestamp'].min()).days
        
        before_rate = len(before_events) / before_days if before_days > 0 else 0
        after_rate = len(after_events) / after_days if after_days > 0 else 0
        rate_change = ((after_rate - before_rate) / before_rate * 100) if before_rate > 0 else 0
        
        print(f"📊 Key Findings:")
        print(f"• Total events analyzed: {len(self.near_miss_data):,}")
        print(f"• Before period events: {len(before_events):,} ({before_rate:.2f}/day)")
        print(f"• After period events: {len(after_events):,} ({after_rate:.2f}/day)")
        print(f"• Rate change: {rate_change:+.1f}%")
        
        if rate_change < -10:
            print("✅ POSITIVE SAFETY IMPACT: Significant reduction in near-miss events")
        elif rate_change > 10:
            print("⚠️ NEGATIVE SAFETY IMPACT: Increase in near-miss events")
        else:
            print("➡️ NEUTRAL IMPACT: Minimal change in near-miss events")
    
    def save_results(self, filename="safety_analysis_results.csv"):
        """Save analysis results"""
        if hasattr(self, 'near_miss_data'):
            output_path = os.path.join(self.data_dir, filename)
            
            # Create summary dataset
            summary_stats = self.near_miss_data.groupby(['period', 'nm_Classification']).agg({
                'TotalGForce': ['mean', 'std', 'count'],
                'speed': ['mean', 'std'],
                'HighestSpeed': ['mean', 'std']
            }).round(3)
            
            summary_stats.to_csv(output_path.replace('.csv', '_summary.csv'))
            self.near_miss_data.to_csv(output_path, index=False)
            print(f"\n💾 Safety analysis saved to: {output_path}")

def main():
    # Initialize analysis
    data_dir = "/Users/timwelch/Dropbox/Files/Research/Compass_Data/SH1_Study/Data/connected_vehicle_data"
    analyzer = SH1SafetyAnalysis(data_dir)
    
    # Load and analyze near-miss data
    if analyzer.load_near_miss_data():
        analyzer.analyze_near_misses()
        analyzer.statistical_significance()
        analyzer.generate_summary_report()
        analyzer.save_results()
    else:
        print("❌ Could not load near-miss data")

if __name__ == "__main__":
    main()
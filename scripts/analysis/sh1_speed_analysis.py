"""
SH1 Speed Limit Analysis - Before/After Study
Analyzes the impact of speed limit change to 110km/h on April 13, 2025

This script provides:
1. Before/after speed behavior analysis
2. Time-of-day patterns
3. Safety impact assessment  
4. Economic time savings calculation
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class SH1SpeedAnalysis:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.parquet_dir = os.path.join(data_dir, "parquet_files")
        self.speed_change_date = pd.to_datetime("2025-04-13")
        self.results = []
        
        # Assumed corridor length (km) - you may need to adjust this
        self.corridor_length_km = 50  
        
        print("🚗 SH1 Speed Limit Impact Analysis")
        print(f"📅 Speed change date: {self.speed_change_date.strftime('%Y-%m-%d')}")
        print(f"📁 Data directory: {data_dir}")
        
    def load_trip_summary(self):
        """Load the unique trips summary"""
        summary_path = os.path.join(self.parquet_dir, "unique_trips_clean.parquet")
        if os.path.exists(summary_path):
            self.trip_summary = pd.read_parquet(summary_path)
            print(f"📋 Loaded {len(self.trip_summary):,} unique trips")
        else:
            print("❌ Trip summary not found. Please run rebuild_unique_trips.py first.")
            return False
        return True
    
    def process_all_trips(self, max_trips=None, max_files=None):
        """Process all trips for comprehensive analysis"""
        print(f"🔄 Processing trips from data files...")
        
        processed_files = 0
        trips_processed = 0
        
        # Loop through all Parquet files
        parquet_files = [f for f in sorted(os.listdir(self.parquet_dir)) 
                        if f.endswith(".parquet") and f != "unique_trips_clean.parquet"]
        
        if max_files:
            parquet_files = parquet_files[:max_files]
            
        print(f"📂 Found {len(parquet_files)} data files to process")
        
        for filename in parquet_files:
            file_path = os.path.join(self.parquet_dir, filename)
            
            try:
                df = pd.read_parquet(file_path, columns=[
                    "TripID", "Point_RawTimestamp", "Point_Speed", 
                    "point_acc_x", "Point_acc_y", "Point_acc_z",
                    "Point_RawLat", "Point_RawLon"
                ])
                
                if len(df) == 0:
                    continue
                    
                before_count = len(self.results)
                self._process_file_trips(df)
                trips_from_file = len(self.results) - before_count
                trips_processed += trips_from_file
                
                processed_files += 1
                
                if processed_files % 10 == 0:
                    print(f"   📂 Processed {processed_files} files, {len(self.results)} trips so far")
                
                # Stop if we've reached the max trips limit
                if max_trips and len(self.results) >= max_trips:
                    print(f"✅ Reached maximum trip limit of {max_trips}")
                    break
                    
            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")
                continue
        
        print(f"✅ Completed processing {len(self.results)} trips from {processed_files} files")
        
    def _process_file_trips(self, df):
        """Process trips within a single file"""
        df["timestamp"] = pd.to_datetime(df["Point_RawTimestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"])
        df["period"] = df["timestamp"].apply(lambda x: "before" if x < self.speed_change_date else "after")
        
        for trip_id in df["TripID"].unique():
            trip_data = df[df["TripID"] == trip_id].copy()
            
            if len(trip_data) < 10:  # Require at least 10 points for reliable analysis
                continue
                
            trip_data = trip_data.sort_values("timestamp")
            metrics = self._calculate_trip_metrics(trip_data)
            if metrics:
                self.results.append(metrics)
    
    def _calculate_trip_metrics(self, trip_data):
        """Calculate comprehensive metrics for a single trip"""
        try:
            period = trip_data["period"].iloc[0]
            
            # Basic trip info
            duration_min = (trip_data["timestamp"].max() - trip_data["timestamp"].min()).total_seconds() / 60
            
            # Speed metrics
            speeds = trip_data["Point_Speed"].dropna()
            if len(speeds) < 5:
                return None
                
            avg_speed = speeds.mean()
            max_speed = speeds.max()
            speed_std = speeds.std()
            speed_85th = speeds.quantile(0.85)
            
            # Speed limits (assume 100 km/h before, 110 km/h after)
            speed_limit = 100 if period == "before" else 110
            
            # Speed adherence
            violations = (speeds > speed_limit).sum()
            adherence_rate = 1 - (violations / len(speeds))
            
            # Extreme speeding (>20 km/h over limit)
            extreme_violations = (speeds > speed_limit + 20).sum()
            extreme_rate = extreme_violations / len(speeds)
            
            # Speed variability
            if len(speeds) > 1:
                speed_changes = np.abs(speeds.diff().dropna())
                rapid_changes = (speed_changes > 15).sum()  # Changes > 15 km/h
                avg_speed_change = speed_changes.mean()
            else:
                rapid_changes = 0
                avg_speed_change = 0
            
            # Acceleration analysis
            acc_x = trip_data["point_acc_x"].dropna()
            if len(acc_x) > 0:
                hard_accel = (acc_x > 2.5).sum()
                hard_brake = (acc_x < -2.5).sum()
                acc_variability = acc_x.std()
            else:
                hard_accel = hard_brake = 0
                acc_variability = np.nan
            
            # Time analysis
            start_time = trip_data["timestamp"].iloc[0]
            hour = start_time.hour
            day_of_week = start_time.dayofweek  # 0=Monday
            
            # Peak hour classification
            if 6 <= hour < 9:
                time_period = "morning_peak"
            elif 16 <= hour < 19:
                time_period = "evening_peak"
            elif 9 <= hour < 16:
                time_period = "midday"
            else:
                time_period = "off_peak"
            
            # Weekend vs weekday
            is_weekend = day_of_week >= 5
            
            return {
                "TripID": trip_data["TripID"].iloc[0],
                "period": period,
                "trip_start": start_time,
                "trip_duration_min": duration_min,
                "avg_speed_kmh": avg_speed,
                "max_speed_kmh": max_speed,
                "speed_85th_kmh": speed_85th,
                "speed_std": speed_std,
                "speed_limit": speed_limit,
                "speed_adherence_rate": adherence_rate,
                "speed_violations": violations,
                "extreme_violations": extreme_violations,
                "extreme_violation_rate": extreme_rate,
                "rapid_speed_changes": rapid_changes,
                "avg_speed_change": avg_speed_change,
                "hard_accel_events": hard_accel,
                "hard_brake_events": hard_brake,
                "acc_variability": acc_variability,
                "time_period": time_period,
                "hour": hour,
                "day_of_week": day_of_week,
                "is_weekend": is_weekend,
                "data_points": len(trip_data)
            }
            
        except Exception as e:
            print(f"Error calculating metrics for trip: {e}")
            return None
    
    def analyze_results(self):
        """Perform comprehensive before/after analysis"""
        if not self.results:
            print("❌ No results to analyze. Run process_all_trips() first.")
            return
        
        self.df = pd.DataFrame(self.results)
        print(f"📊 Analyzing {len(self.df)} trips...")
        
        # Basic statistics
        before_trips = self.df[self.df["period"] == "before"]
        after_trips = self.df[self.df["period"] == "after"]
        
        print(f"\n📈 BASIC STATISTICS")
        print(f"Before period: {len(before_trips):,} trips")
        print(f"After period:  {len(after_trips):,} trips")
        
        if len(before_trips) == 0 or len(after_trips) == 0:
            print("⚠️  Insufficient data for before/after comparison")
            return
        
        # Speed analysis
        self._analyze_speeds()
        
        # Safety analysis
        self._analyze_safety()
        
        # Time-of-day analysis
        self._analyze_time_patterns()
        
        # Statistical significance
        self._statistical_tests()
        
        # Time savings calculation
        self._calculate_time_savings()
    
    def _analyze_speeds(self):
        """Analyze speed changes"""
        print(f"\n🚄 SPEED ANALYSIS")
        
        before = self.df[self.df["period"] == "before"]
        after = self.df[self.df["period"] == "after"]
        
        # Average speeds
        before_avg = before["avg_speed_kmh"].mean()
        after_avg = after["avg_speed_kmh"].mean()
        speed_increase = after_avg - before_avg
        
        print(f"Average Speed:")
        print(f"  Before: {before_avg:.1f} km/h")
        print(f"  After:  {after_avg:.1f} km/h")
        print(f"  Change: {speed_increase:+.1f} km/h ({speed_increase/before_avg*100:+.1f}%)")
        
        # 85th percentile speeds
        before_85th = before["speed_85th_kmh"].mean()
        after_85th = after["speed_85th_kmh"].mean()
        
        print(f"\n85th Percentile Speed:")
        print(f"  Before: {before_85th:.1f} km/h")
        print(f"  After:  {after_85th:.1f} km/h")
        print(f"  Change: {after_85th - before_85th:+.1f} km/h")
        
        # Speed adherence
        before_adherence = before["speed_adherence_rate"].mean() * 100
        after_adherence = after["speed_adherence_rate"].mean() * 100
        
        print(f"\nSpeed Adherence:")
        print(f"  Before: {before_adherence:.1f}%")
        print(f"  After:  {after_adherence:.1f}%")
        print(f"  Change: {after_adherence - before_adherence:+.1f} percentage points")
    
    def _analyze_safety(self):
        """Analyze safety-related metrics"""
        print(f"\n🛡️  SAFETY ANALYSIS")
        
        before = self.df[self.df["period"] == "before"]
        after = self.df[self.df["period"] == "after"]
        
        # Extreme speeding
        before_extreme = before["extreme_violation_rate"].mean() * 100
        after_extreme = after["extreme_violation_rate"].mean() * 100
        
        print(f"Extreme Speeding (>20 km/h over limit):")
        print(f"  Before: {before_extreme:.1f}% of trip time")
        print(f"  After:  {after_extreme:.1f}% of trip time")
        print(f"  Change: {after_extreme - before_extreme:+.1f} percentage points")
        
        # Hard acceleration/braking events
        before_hard_accel = before["hard_accel_events"].mean()
        after_hard_accel = after["hard_accel_events"].mean()
        
        before_hard_brake = before["hard_brake_events"].mean()
        after_hard_brake = after["hard_brake_events"].mean()
        
        print(f"\nErratic Driving Events per Trip:")
        print(f"  Hard Acceleration - Before: {before_hard_accel:.2f}, After: {after_hard_accel:.2f}")
        print(f"  Hard Braking - Before: {before_hard_brake:.2f}, After: {after_hard_brake:.2f}")
    
    def _analyze_time_patterns(self):
        """Analyze time-of-day patterns"""
        print(f"\n⏰ TIME-OF-DAY ANALYSIS")
        
        # Speed by time period
        speed_by_time = self.df.groupby(['period', 'time_period'])['avg_speed_kmh'].mean().unstack()
        print("\nAverage Speed by Time Period (km/h):")
        print(speed_by_time.round(1))
        
        # Weekend vs weekday
        weekend_analysis = self.df.groupby(['period', 'is_weekend'])['avg_speed_kmh'].mean().unstack()
        print("\nAverage Speed: Weekend vs Weekday (km/h):")
        weekend_analysis.columns = ['Weekday', 'Weekend']
        print(weekend_analysis.round(1))
    
    def _statistical_tests(self):
        """Perform statistical significance tests"""
        print(f"\n📊 STATISTICAL SIGNIFICANCE")
        
        before = self.df[self.df["period"] == "before"]
        after = self.df[self.df["period"] == "after"]
        
        # T-test for speed difference
        t_stat, p_value = stats.ttest_ind(before["avg_speed_kmh"], after["avg_speed_kmh"])
        significance = "significant" if p_value < 0.05 else "not significant"
        
        print(f"Speed Change T-Test:")
        print(f"  t-statistic: {t_stat:.3f}")
        print(f"  p-value: {p_value:.3f}")
        print(f"  Result: {significance} at α=0.05")
    
    def _calculate_time_savings(self):
        """Calculate time savings for 38k daily trips"""
        print(f"\n💰 ECONOMIC IMPACT - TIME SAVINGS")
        
        before = self.df[self.df["period"] == "before"]
        after = self.df[self.df["period"] == "after"]
        
        if len(before) == 0 or len(after) == 0:
            print("❌ Insufficient data for time savings calculation")
            return
        
        # Average speeds
        before_speed = before["avg_speed_kmh"].mean()
        after_speed = after["avg_speed_kmh"].mean()
        
        # Travel time calculation (assuming corridor length)
        before_travel_time = (self.corridor_length_km / before_speed) * 60  # minutes
        after_travel_time = (self.corridor_length_km / after_speed) * 60   # minutes
        
        time_savings_per_trip = before_travel_time - after_travel_time  # minutes
        
        # Daily calculations for 38,000 trips
        daily_trips = 38000
        daily_time_savings_hours = (time_savings_per_trip * daily_trips) / 60
        
        # Annual calculations
        annual_time_savings_hours = daily_time_savings_hours * 365
        
        # Economic value (assume $25/hour value of time)
        hourly_value = 25  # USD per hour
        daily_economic_value = daily_time_savings_hours * hourly_value
        annual_economic_value = annual_time_savings_hours * hourly_value
        
        print(f"Corridor Length: {self.corridor_length_km} km (assumed)")
        print(f"Average Travel Time:")
        print(f"  Before: {before_travel_time:.1f} minutes")
        print(f"  After:  {after_travel_time:.1f} minutes")
        print(f"  Savings: {time_savings_per_trip:.1f} minutes per trip")
        
        print(f"\nDaily Impact (38,000 trips):")
        print(f"  Time Savings: {daily_time_savings_hours:,.0f} hours")
        print(f"  Economic Value: ${daily_economic_value:,.0f}")
        
        print(f"\nAnnual Impact:")
        print(f"  Time Savings: {annual_time_savings_hours:,.0f} hours")
        print(f"  Economic Value: ${annual_economic_value:,.0f}")
    
    def save_results(self, filename="sh1_analysis_results.csv"):
        """Save detailed results to CSV"""
        if hasattr(self, 'df'):
            output_path = os.path.join(self.parquet_dir, filename)
            self.df.to_csv(output_path, index=False)
            print(f"\n💾 Results saved to: {output_path}")
        else:
            print("❌ No results to save")

def main():
    # Initialize analysis
    data_dir = "/Users/timwelch/Dropbox/Files/Research/Compass_Data/SH1_Study/Data/connected_vehicle_data"
    analyzer = SH1SpeedAnalysis(data_dir)
    
    # Process trips (start with smaller sample for testing)
    analyzer.process_all_trips(max_trips=1000, max_files=50)  # Process first 50 files, up to 1000 trips
    
    # Analyze results
    analyzer.analyze_results()
    
    # Save results
    analyzer.save_results()

if __name__ == "__main__":
    main()
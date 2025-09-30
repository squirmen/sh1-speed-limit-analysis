c"""
Economic Impact Analysis Using Our GPS-Derived Data
Calculate time savings and economic benefits from speed limit change based on our analysis
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

class OurEconomicImpactAnalysis:
    def __init__(self):
        self.speed_change_date = pd.to_datetime("2025-04-13")
        self.base_dir = "/Volumes/T7/Data/connected_vehicle_data"
        self.data_dir = os.path.join(self.base_dir, "output", "processed_data")
        self.output_dir = os.path.join(self.base_dir, "output", "reports")
        
        print("💰 ECONOMIC IMPACT ANALYSIS - OUR GPS DATA")
        print("Calculating economic benefits using our GPS-derived behavioral analysis")
        print("="*60)
        
    def load_our_gps_metrics(self):
        """Load our GPS-derived metrics"""
        print(f"\n📊 LOADING OUR GPS METRICS")
        
        metrics_path = os.path.join(self.data_dir, 'comprehensive_gps_metrics.csv')
        self.metrics = pd.read_csv(metrics_path)
        self.metrics['timestamp'] = pd.to_datetime(self.metrics['timestamp'])
        
        # Add period classification
        self.metrics['period'] = self.metrics['timestamp'].apply(
            lambda x: 'before' if x < self.speed_change_date else 'after'
        )
        
        # Filter out unrealistic speeds and focus on valid data
        valid_speeds = (self.metrics['derived_speed_kmh'] > 10) & (self.metrics['derived_speed_kmh'] < 150)
        self.metrics = self.metrics[valid_speeds].copy()
        
        print(f"✅ Loaded {len(self.metrics):,} GPS records with valid speeds")
        print(f"📅 Date range: {self.metrics['timestamp'].min()} to {self.metrics['timestamp'].max()}")
        print(f"🚗 Vehicles: {self.metrics['VehicleID'].nunique():,}")
        
        # Period breakdown
        before_records = len(self.metrics[self.metrics['period'] == 'before'])
        after_records = len(self.metrics[self.metrics['period'] == 'after'])
        
        print(f"\nPeriod breakdown:")
        print(f"• Before April 13: {before_records:,} records")
        print(f"• After April 13: {after_records:,} records")
        
        return True
        
    def analyze_speed_changes(self):
        """Analyze speed changes from our GPS data"""
        print(f"\n📈 ANALYZING SPEED CHANGES FROM OUR DATA")
        
        before_speeds = self.metrics[self.metrics['period'] == 'before']['derived_speed_kmh']
        after_speeds = self.metrics[self.metrics['period'] == 'after']['derived_speed_kmh']
        
        before_stats = {
            'mean': before_speeds.mean(),
            'median': before_speeds.median(),
            'std': before_speeds.std(),
            'count': len(before_speeds)
        }
        
        after_stats = {
            'mean': after_speeds.mean(),
            'median': after_speeds.median(),
            'std': after_speeds.std(),
            'count': len(after_speeds)
        }
        
        print(f"Speed Analysis:")
        print(f"• Before period: {before_stats['mean']:.1f} km/h mean ({before_stats['count']:,} records)")
        print(f"• After period: {after_stats['mean']:.1f} km/h mean ({after_stats['count']:,} records)")
        
        speed_increase = after_stats['mean'] - before_stats['mean']
        speed_increase_pct = (speed_increase / before_stats['mean']) * 100
        
        print(f"• Speed change: {speed_increase:+.1f} km/h ({speed_increase_pct:+.1f}%)")
        
        # Speed compliance analysis
        before_over_100 = (before_speeds > 100).sum()
        after_over_110 = (after_speeds > 110).sum()
        
        before_compliance = (1 - before_over_100 / len(before_speeds)) * 100
        after_compliance = (1 - after_over_110 / len(after_speeds)) * 100
        
        print(f"\nCompliance Analysis:")
        print(f"• Before (>100 km/h violations): {before_over_100:,} ({100-before_compliance:.1f}%)")
        print(f"• After (>110 km/h violations): {after_over_110:,} ({100-after_compliance:.1f}%)")
        
        return {
            'before_speed': before_stats['mean'],
            'after_speed': after_stats['mean'],
            'speed_increase': speed_increase,
            'speed_increase_pct': speed_increase_pct,
            'before_compliance': before_compliance,
            'after_compliance': after_compliance
        }
        
    def calculate_time_savings(self, speed_analysis):
        """Calculate time savings based on our speed analysis"""
        print(f"\n⏱️ CALCULATING TIME SAVINGS")
        
        # SH1 corridor parameters
        corridor_length_km = 70  # Approximate SH1 length through study area
        daily_trips = 38000      # From original study
        
        before_speed = speed_analysis['before_speed']
        after_speed = speed_analysis['after_speed']
        
        # Calculate travel times (in hours)
        before_time = corridor_length_km / before_speed
        after_time = corridor_length_km / after_speed
        
        # Time savings per trip (in minutes)
        time_savings_per_trip = (before_time - after_time) * 60
        
        print(f"Travel Time Analysis:")
        print(f"• Corridor length: {corridor_length_km} km")
        print(f"• Before speed: {before_speed:.1f} km/h")
        print(f"• After speed: {after_speed:.1f} km/h")
        print(f"• Before travel time: {before_time*60:.1f} minutes")
        print(f"• After travel time: {after_time*60:.1f} minutes")
        print(f"• Time savings per trip: {time_savings_per_trip:.2f} minutes")
        
        # Daily and annual savings
        daily_time_savings_hours = (time_savings_per_trip / 60) * daily_trips
        annual_time_savings_hours = daily_time_savings_hours * 365
        
        print(f"\nAggregate Time Savings:")
        print(f"• Daily savings: {daily_time_savings_hours:.0f} hours")
        print(f"• Annual savings: {annual_time_savings_hours:,.0f} hours")
        
        return {
            'time_savings_per_trip_min': time_savings_per_trip,
            'daily_time_savings_hours': daily_time_savings_hours,
            'annual_time_savings_hours': annual_time_savings_hours,
            'before_travel_time_min': before_time * 60,
            'after_travel_time_min': after_time * 60
        }
        
    def calculate_economic_value(self, time_savings):
        """Calculate economic value of time savings"""
        print(f"\n💰 CALCULATING ECONOMIC VALUE")
        
        # Value of travel time savings (NZ Transport Agency values)
        hourly_values = {
            'light_vehicles': 32.50,  # NZD per hour (business travel)
            'heavy_vehicles': 45.00,  # NZD per hour (freight)
            'average_mixed': 35.00    # NZD per hour (mixed traffic)
        }
        
        annual_hours_saved = time_savings['annual_time_savings_hours']
        
        scenarios = {}
        
        for scenario, value_per_hour in hourly_values.items():
            annual_value = annual_hours_saved * value_per_hour
            scenarios[scenario] = {
                'hourly_value': value_per_hour,
                'annual_benefit': annual_value,
                'per_trip_value': (time_savings['time_savings_per_trip_min'] / 60) * value_per_hour
            }
            
            print(f"\n{scenario.replace('_', ' ').title()} Scenario:")
            print(f"• Value per hour: ${value_per_hour:.2f} NZD")
            print(f"• Value per trip: ${scenarios[scenario]['per_trip_value']:.3f} NZD")
            print(f"• Annual benefit: ${annual_value:,.0f} NZD")
            print(f"• Daily benefit: ${annual_value/365:,.0f} NZD")
        
        return scenarios
        
    def analyze_safety_benefits(self):
        """Analyze safety improvements based on our detected events"""
        print(f"\n🛡️ ANALYZING SAFETY BENEFITS FROM OUR EVENT DETECTION")
        
        # Load our detected events
        events_path = os.path.join(self.data_dir, 'comprehensive_gps_events.csv')
        events = pd.read_csv(events_path)
        events['timestamp'] = pd.to_datetime(events['timestamp'])
        
        before_events = events[events['timestamp'] < self.speed_change_date]
        after_events = events[events['timestamp'] >= self.speed_change_date]
        
        # Calculate event rates
        before_days = (self.speed_change_date - before_events['timestamp'].min()).days
        after_days = (after_events['timestamp'].max() - self.speed_change_date).days
        
        before_rate = len(before_events) / max(before_days, 1)
        after_rate = len(after_events) / max(after_days, 1)
        
        rate_change = (after_rate - before_rate) / before_rate * 100 if before_rate > 0 else 0
        
        print(f"Safety Event Analysis:")
        print(f"• Before period: {len(before_events):,} events over {before_days} days ({before_rate:.2f} events/day)")
        print(f"• After period: {len(after_events):,} events over {after_days} days ({after_rate:.2f} events/day)")
        print(f"• Event rate change: {rate_change:+.1f}%")
        
        # Severity analysis
        before_severity = before_events['severity'].mean()
        after_severity = after_events['severity'].mean()
        severity_change = (after_severity - before_severity) / before_severity * 100 if before_severity > 0 else 0
        
        print(f"• Average severity change: {severity_change:+.1f}%")
        
        # Estimate safety value (rough approximation)
        if rate_change < 0:  # Events decreased
            events_prevented_daily = abs(rate_change / 100 * before_rate)
            events_prevented_annual = events_prevented_daily * 365
            
            # Conservative estimate: each prevented event saves $1000 in potential costs
            safety_value_annual = events_prevented_annual * 1000
            
            print(f"\\nEstimated Safety Benefits:")
            print(f"• Events prevented daily: {events_prevented_daily:.2f}")
            print(f"• Events prevented annually: {events_prevented_annual:.0f}")
            print(f"• Estimated annual safety value: ${safety_value_annual:,.0f} NZD")
            
            return safety_value_annual
        else:
            print(f"\\n⚠️ Events increased - no direct safety benefit calculated")
            return 0
            
    def generate_comprehensive_economic_report(self, speed_analysis, time_savings, economic_scenarios, safety_value):
        """Generate comprehensive economic impact report"""
        print(f"\n📋 COMPREHENSIVE ECONOMIC IMPACT REPORT")
        print("="*60)
        
        report = {
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_source': 'GPS-derived analysis',
            'total_gps_records': len(self.metrics),
            'vehicles_analyzed': self.metrics['VehicleID'].nunique(),
            'before_speed_kmh': speed_analysis['before_speed'],
            'after_speed_kmh': speed_analysis['after_speed'],
            'speed_increase_kmh': speed_analysis['speed_increase'],
            'speed_increase_pct': speed_analysis['speed_increase_pct'],
            'time_savings_per_trip_min': time_savings['time_savings_per_trip_min'],
            'annual_time_savings_hours': time_savings['annual_time_savings_hours'],
            'conservative_annual_benefit_nzd': economic_scenarios['light_vehicles']['annual_benefit'],
            'moderate_annual_benefit_nzd': economic_scenarios['average_mixed']['annual_benefit'],
            'optimistic_annual_benefit_nzd': economic_scenarios['heavy_vehicles']['annual_benefit'],
            'estimated_safety_benefit_nzd': safety_value
        }
        
        print(f"🎯 KEY ECONOMIC FINDINGS:")
        print(f"• Speed increase: {report['speed_increase_kmh']:+.1f} km/h ({report['speed_increase_pct']:+.1f}%)")
        print(f"• Time savings per trip: {report['time_savings_per_trip_min']:.2f} minutes")
        print(f"• Annual time savings: {report['annual_time_savings_hours']:,.0f} hours")
        
        print(f"\\n💰 ECONOMIC BENEFIT SCENARIOS:")
        print(f"• Conservative (Light Vehicles): ${report['conservative_annual_benefit_nzd']:,.0f} NZD")
        print(f"• Moderate (Mixed Traffic): ${report['moderate_annual_benefit_nzd']:,.0f} NZD") 
        print(f"• Optimistic (Heavy Vehicles): ${report['optimistic_annual_benefit_nzd']:,.0f} NZD")
        
        if safety_value > 0:
            total_benefits = {
                'conservative_total': report['conservative_annual_benefit_nzd'] + safety_value,
                'moderate_total': report['moderate_annual_benefit_nzd'] + safety_value,
                'optimistic_total': report['optimistic_annual_benefit_nzd'] + safety_value
            }
            
            print(f"\\n🛡️ TOTAL BENEFITS (Including Safety):")
            print(f"• Conservative Total: ${total_benefits['conservative_total']:,.0f} NZD")
            print(f"• Moderate Total: ${total_benefits['moderate_total']:,.0f} NZD")
            print(f"• Optimistic Total: ${total_benefits['optimistic_total']:,.0f} NZD")
        
        # Save detailed report
        report_df = pd.DataFrame([report])
        report_path = os.path.join(self.output_dir, 'our_economic_impact_report.csv')
        os.makedirs(self.output_dir, exist_ok=True)
        report_df.to_csv(report_path, index=False)
        
        print(f"\\n💾 Economic analysis saved to: our_economic_impact_report.csv")
        
        return report

def main():
    analyzer = OurEconomicImpactAnalysis()
    
    # Load our GPS metrics
    if analyzer.load_our_gps_metrics():
        # Analyze speed changes
        speed_analysis = analyzer.analyze_speed_changes()
        
        # Calculate time savings  
        time_savings = analyzer.calculate_time_savings(speed_analysis)
        
        # Calculate economic value
        economic_scenarios = analyzer.calculate_economic_value(time_savings)
        
        # Analyze safety benefits
        safety_value = analyzer.analyze_safety_benefits()
        
        # Generate comprehensive report
        report = analyzer.generate_comprehensive_economic_report(
            speed_analysis, time_savings, economic_scenarios, safety_value
        )
        
        print(f"\\n✅ ECONOMIC IMPACT ANALYSIS COMPLETE")
        print(f"Annual economic benefit: ${report['moderate_annual_benefit_nzd']:,.0f} NZD")
        print(f"Based on analysis of {len(analyzer.metrics):,} GPS records from {analyzer.metrics['VehicleID'].nunique():,} vehicles")

if __name__ == "__main__":
    main()
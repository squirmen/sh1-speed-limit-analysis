"""
SH1 Time Savings Analysis - Economic Impact Assessment
Calculates time savings and economic benefits from speed limit increase to 110km/h
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

class SH1TimeSavingsAnalysis:
    def __init__(self, corridor_length_km=50, daily_trips=38000):
        """
        Initialize time savings analysis
        
        Args:
            corridor_length_km: Length of SH1 corridor (default 50km)
            daily_trips: Number of daily trips (default 38,000)
        """
        self.corridor_length_km = corridor_length_km
        self.daily_trips = daily_trips
        self.hourly_value_time = 25  # USD per hour - adjust based on local standards
        
        print("💰 SH1 Time Savings & Economic Impact Analysis")
        print(f"🛣️ Corridor length: {corridor_length_km} km")
        print(f"🚗 Daily trips: {daily_trips:,}")
        print(f"💵 Value of time: ${self.hourly_value_time}/hour")
    
    def load_processed_data(self, data_dir):
        """Load processed trip data and safety results"""
        # Try to load the test results we generated
        test_results_path = os.path.join(data_dir, "parquet_files", "test_results.csv")
        safety_results_path = os.path.join(data_dir, "safety_analysis_results.csv")
        
        # Load speed data
        if os.path.exists(test_results_path):
            self.speed_data = pd.read_csv(test_results_path)
            print(f"📊 Loaded speed data: {len(self.speed_data)} trips")
        else:
            print("⚠️ No processed speed data found - using estimates")
            self.speed_data = None
        
        # Load safety data
        if os.path.exists(safety_results_path):
            self.safety_data = pd.read_csv(safety_results_path)
            print(f"🛡️ Loaded safety data: {len(self.safety_data)} events")
        else:
            print("⚠️ No safety data found")
            self.safety_data = None
    
    def calculate_baseline_scenarios(self):
        """Calculate time savings under different scenarios"""
        print(f"\n⏱️ TIME SAVINGS SCENARIOS")
        
        scenarios = [
            {"name": "Conservative", "before_speed": 85, "after_speed": 95, "description": "Modest speed increase"},
            {"name": "Moderate", "before_speed": 80, "after_speed": 100, "description": "Typical highway speeds"},
            {"name": "Optimistic", "before_speed": 75, "after_speed": 105, "description": "Maximum realistic improvement"},
        ]
        
        if self.speed_data is not None and len(self.speed_data) > 0:
            # Use actual data if available
            before_trips = self.speed_data[self.speed_data['period'] == 'before']
            after_trips = self.speed_data[self.speed_data['period'] == 'after']
            
            if len(before_trips) > 0 and len(after_trips) > 0:
                actual_before = before_trips['avg_speed_kmh'].mean()
                actual_after = after_trips['avg_speed_kmh'].mean()
                scenarios.insert(0, {
                    "name": "Actual Data", 
                    "before_speed": actual_before, 
                    "after_speed": actual_after,
                    "description": "Based on processed trip data"
                })
        
        results = []
        
        for scenario in scenarios:
            result = self._calculate_scenario(scenario)
            results.append(result)
            
            print(f"\n📈 {scenario['name']} Scenario - {scenario['description']}")
            print(f"   Before: {scenario['before_speed']:.1f} km/h")
            print(f"   After:  {scenario['after_speed']:.1f} km/h")
            print(f"   Time saving per trip: {result['time_savings_min']:.2f} minutes")
            print(f"   Daily time savings: {result['daily_hours']:.0f} hours")
            print(f"   Daily economic value: ${result['daily_value']:,.0f}")
            print(f"   Annual economic value: ${result['annual_value']:,.0f}")
        
        return results
    
    def _calculate_scenario(self, scenario):
        """Calculate savings for a single scenario"""
        before_speed = scenario['before_speed']
        after_speed = scenario['after_speed']
        
        # Calculate travel times in minutes
        before_time_min = (self.corridor_length_km / before_speed) * 60
        after_time_min = (self.corridor_length_km / after_speed) * 60
        
        # Time savings per trip
        time_savings_min = before_time_min - after_time_min
        
        # Daily and annual calculations
        daily_time_savings_hours = (time_savings_min * self.daily_trips) / 60
        annual_time_savings_hours = daily_time_savings_hours * 365
        
        # Economic values
        daily_economic_value = daily_time_savings_hours * self.hourly_value_time
        annual_economic_value = annual_time_savings_hours * self.hourly_value_time
        
        return {
            'scenario': scenario['name'],
            'before_speed_kmh': before_speed,
            'after_speed_kmh': after_speed,
            'speed_increase_kmh': after_speed - before_speed,
            'time_savings_min': time_savings_min,
            'daily_hours': daily_time_savings_hours,
            'annual_hours': annual_time_savings_hours,
            'daily_value': daily_economic_value,
            'annual_value': annual_economic_value
        }
    
    def peak_hour_analysis(self):
        """Analyze time savings by peak vs off-peak periods"""
        print(f"\n⏰ PEAK HOUR IMPACT ANALYSIS")
        
        # Typical traffic distribution
        peak_periods = {
            'morning_peak': {'hours': 3, 'trips_pct': 25, 'congestion_factor': 0.7},  # Lower speeds due to congestion
            'evening_peak': {'hours': 3, 'trips_pct': 30, 'congestion_factor': 0.7},
            'midday': {'hours': 7, 'trips_pct': 30, 'congestion_factor': 0.9},
            'off_peak': {'hours': 11, 'trips_pct': 15, 'congestion_factor': 1.0}
        }
        
        base_before_speed = 80  # km/h
        base_after_speed = 100  # km/h
        
        total_daily_value = 0
        
        print("Time period analysis:")
        for period, data in peak_periods.items():
            # Adjust speeds for congestion
            before_speed = base_before_speed * data['congestion_factor']
            after_speed = base_after_speed * data['congestion_factor']
            
            trips_in_period = self.daily_trips * (data['trips_pct'] / 100)
            
            # Calculate time savings
            before_time = (self.corridor_length_km / before_speed) * 60
            after_time = (self.corridor_length_km / after_speed) * 60
            time_savings_min = before_time - after_time
            
            # Economic value
            period_hours_saved = (time_savings_min * trips_in_period) / 60
            period_value = period_hours_saved * self.hourly_value_time
            total_daily_value += period_value
            
            print(f"  {period}:")
            print(f"    Trips: {trips_in_period:,.0f} ({data['trips_pct']}%)")
            print(f"    Speed: {before_speed:.1f} → {after_speed:.1f} km/h")
            print(f"    Time savings: {time_savings_min:.2f} min/trip")
            print(f"    Daily value: ${period_value:,.0f}")
        
        annual_value = total_daily_value * 365
        print(f"\nTotal daily value: ${total_daily_value:,.0f}")
        print(f"Total annual value: ${annual_value:,.0f}")
        
        return {'daily_value': total_daily_value, 'annual_value': annual_value}
    
    def sensitivity_analysis(self):
        """Perform sensitivity analysis on key parameters"""
        print(f"\n🔬 SENSITIVITY ANALYSIS")
        
        base_params = {
            'before_speed': 80,
            'after_speed': 100,
            'daily_trips': self.daily_trips,
            'corridor_length': self.corridor_length_km,
            'value_of_time': self.hourly_value_time
        }
        
        # Test parameter variations
        variations = {
            'Speed increase (+/-10 km/h)': [
                {'after_speed': 90}, {'after_speed': 110}
            ],
            'Daily trips (+/-20%)': [
                {'daily_trips': int(self.daily_trips * 0.8)}, 
                {'daily_trips': int(self.daily_trips * 1.2)}
            ],
            'Value of time (+/-50%)': [
                {'value_of_time': self.hourly_value_time * 0.5}, 
                {'value_of_time': self.hourly_value_time * 1.5}
            ]
        }
        
        base_result = self._calculate_scenario_with_params(base_params)
        base_annual = base_result['annual_value']
        
        print(f"Base case annual value: ${base_annual:,.0f}")
        print()
        
        for variation_name, param_sets in variations.items():
            print(f"{variation_name}:")
            for i, params in enumerate(param_sets):
                test_params = base_params.copy()
                test_params.update(params)
                
                result = self._calculate_scenario_with_params(test_params)
                difference = result['annual_value'] - base_annual
                pct_change = (difference / base_annual) * 100
                
                param_desc = ', '.join([f"{k}={v}" for k, v in params.items()])
                print(f"  {param_desc}: ${result['annual_value']:,.0f} ({pct_change:+.1f}%)")
    
    def _calculate_scenario_with_params(self, params):
        """Calculate scenario with custom parameters"""
        # Travel times
        before_time_min = (params['corridor_length'] / params['before_speed']) * 60
        after_time_min = (params['corridor_length'] / params['after_speed']) * 60
        
        # Savings
        time_savings_min = before_time_min - after_time_min
        daily_hours = (time_savings_min * params['daily_trips']) / 60
        annual_hours = daily_hours * 365
        
        return {
            'time_savings_min': time_savings_min,
            'daily_hours': daily_hours,
            'annual_hours': annual_hours,
            'daily_value': daily_hours * params['value_of_time'],
            'annual_value': annual_hours * params['value_of_time']
        }
    
    def generate_executive_summary(self, results):
        """Generate executive summary of findings"""
        print(f"\n📊 EXECUTIVE SUMMARY - ECONOMIC IMPACT")
        print("=" * 60)
        
        # Use moderate scenario as primary estimate
        moderate_scenario = next((r for r in results if r['scenario'] == 'Moderate'), results[1])
        
        print(f"🎯 PRIMARY ESTIMATE (Moderate Scenario):")
        print(f"   Speed increase: {moderate_scenario['speed_increase_kmh']:.0f} km/h")
        print(f"   Time savings per trip: {moderate_scenario['time_savings_min']:.1f} minutes")
        print(f"   Daily economic benefit: ${moderate_scenario['daily_value']:,.0f}")
        print(f"   Annual economic benefit: ${moderate_scenario['annual_value']:,.0f}")
        
        print(f"\n📈 RANGE OF ESTIMATES:")
        min_annual = min([r['annual_value'] for r in results])
        max_annual = max([r['annual_value'] for r in results])
        print(f"   Conservative to Optimistic: ${min_annual:,.0f} - ${max_annual:,.0f} annually")
        
        # Cost-benefit context
        print(f"\n💡 POLICY IMPLICATIONS:")
        print(f"   • Estimated annual time savings: ${moderate_scenario['annual_value']:,.0f}")
        print(f"   • Daily benefit per trip: ${moderate_scenario['daily_value']/self.daily_trips:.2f}")
        print(f"   • Break-even implementation cost: ~${moderate_scenario['annual_value']*3:,.0f} (3-year payback)")
        
        if hasattr(self, 'safety_data') and self.safety_data is not None:
            print(f"   • Safety considerations: Monitor near-miss trends (limited post-change data)")
        
        return moderate_scenario
    
    def save_results(self, results, filename="time_savings_analysis.csv"):
        """Save analysis results"""
        df_results = pd.DataFrame(results)
        output_path = filename
        df_results.to_csv(output_path, index=False)
        print(f"\n💾 Time savings analysis saved to: {output_path}")

def main():
    # Initialize analysis - adjust parameters as needed
    analyzer = SH1TimeSavingsAnalysis(
        corridor_length_km=50,  # Adjust based on actual corridor length
        daily_trips=38000
    )
    
    # Load processed data
    data_dir = "/Users/timwelch/Dropbox/Files/Research/Compass_Data/SH1_Study/Data/connected_vehicle_data"
    analyzer.load_processed_data(data_dir)
    
    # Run analysis
    results = analyzer.calculate_baseline_scenarios()
    peak_analysis = analyzer.peak_hour_analysis()
    analyzer.sensitivity_analysis()
    summary = analyzer.generate_executive_summary(results)
    
    # Save results
    analyzer.save_results(results)

if __name__ == "__main__":
    main()
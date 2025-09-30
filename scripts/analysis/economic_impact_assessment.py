"""
Economic Impact Assessment of Speed Limit Increase
Professional analysis of time savings and economic benefits from 100→110 km/h speed limit change
SH1/SH76 Christchurch Southern Motorway, effective April 13, 2025
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

class EconomicImpactAssessment:
    def __init__(self):
        self.base_dir = "/Volumes/T7/Data/connected_vehicle_data"
        self.data_dir = os.path.join(self.base_dir, "output", "processed_data")
        self.output_dir = os.path.join(self.base_dir, "output", "reports")

        # Study parameters
        self.speed_change_date = pd.to_datetime("2025-04-13")
        self.corridor_length_km = 17.7  # SH1/SH76 study segment

        # Traffic volume assumptions (based on NZ Transport Agency data)
        self.daily_vehicle_count = 38000  # Average daily traffic
        self.annual_working_days = 260  # Business days per year

        # Value of travel time savings (NZ Transport Agency Economic Evaluation Manual)
        # Updated to 2025 NZD values
        self.vott_rates = {
            'light_vehicle_business': 35.20,    # NZD per hour
            'light_vehicle_commuting': 16.80,   # NZD per hour
            'light_vehicle_leisure': 8.40,      # NZD per hour
            'heavy_vehicle_freight': 48.60,     # NZD per hour
            'average_mixed_traffic': 28.50      # NZD per hour (weighted average)
        }

        os.makedirs(self.output_dir, exist_ok=True)

        print("💰 ECONOMIC IMPACT ASSESSMENT")
        print("SH1/SH76 Speed Limit Increase: Time Savings & Economic Benefits")
        print("="*60)

    def load_statistical_results(self):
        """Load results from statistical analysis"""
        print(f"\n📊 LOADING STATISTICAL ANALYSIS RESULTS")

        stats_path = os.path.join(self.output_dir, "statistical_analysis_report.csv")
        if not os.path.exists(stats_path):
            print(f"❌ Statistical results not found: {stats_path}")
            return None

        stats_results = pd.read_csv(stats_path).iloc[0].to_dict()

        print(f"✅ Statistical results loaded")
        print(f"   • Speed increase: {stats_results['speed_increase_kmh']:.2f} km/h")
        print(f"   • Effect size: {stats_results['cohens_d']:.3f} ({stats_results['effect_magnitude']})")
        print(f"   • Statistical significance: {'✅' if stats_results['statistically_significant'] else '❌'}")

        self.stats_results = stats_results
        return stats_results

    def calculate_travel_time_savings(self):
        """Calculate travel time savings per vehicle trip"""
        print(f"\n⏱️  CALCULATING TRAVEL TIME SAVINGS")

        before_speed = self.stats_results['before_mean_speed']
        after_speed = self.stats_results['after_mean_speed']
        speed_increase = self.stats_results['speed_increase_kmh']

        print(f"📋 TRAVEL TIME PARAMETERS:")
        print(f"   • Corridor length: {self.corridor_length_km} km")
        print(f"   • Before speed (mean): {before_speed:.1f} km/h")
        print(f"   • After speed (mean): {after_speed:.1f} km/h")
        print(f"   • Speed increase: {speed_increase:.1f} km/h")

        # Calculate travel times (hours)
        before_travel_time = self.corridor_length_km / before_speed
        after_travel_time = self.corridor_length_km / after_speed

        # Time savings per trip (minutes)
        time_savings_minutes = (before_travel_time - after_travel_time) * 60

        print(f"\n📈 TIME SAVINGS CALCULATION:")
        print(f"   • Before travel time: {before_travel_time*60:.1f} minutes")
        print(f"   • After travel time: {after_travel_time*60:.1f} minutes")
        print(f"   • Time savings per trip: {time_savings_minutes:.2f} minutes")

        # Relative improvement
        time_savings_percent = ((before_travel_time - after_travel_time) / before_travel_time) * 100
        print(f"   • Relative time savings: {time_savings_percent:.1f}%")

        self.time_savings = {
            'before_travel_time_hours': before_travel_time,
            'after_travel_time_hours': after_travel_time,
            'time_savings_per_trip_minutes': time_savings_minutes,
            'time_savings_per_trip_hours': time_savings_minutes / 60,
            'time_savings_percent': time_savings_percent
        }

        return self.time_savings

    def estimate_aggregate_benefits(self):
        """Estimate aggregate annual benefits"""
        print(f"\n📊 ESTIMATING AGGREGATE ANNUAL BENEFITS")

        time_savings_hours = self.time_savings['time_savings_per_trip_hours']

        # Daily time savings
        daily_time_savings_hours = time_savings_hours * self.daily_vehicle_count

        # Annual time savings
        annual_time_savings_hours = daily_time_savings_hours * 365

        print(f"📋 AGGREGATE TIME SAVINGS:")
        print(f"   • Time savings per trip: {time_savings_hours*60:.2f} minutes")
        print(f"   • Daily vehicle count: {self.daily_vehicle_count:,}")
        print(f"   • Daily time savings: {daily_time_savings_hours:.0f} hours")
        print(f"   • Annual time savings: {annual_time_savings_hours:,.0f} hours")

        # Calculate economic benefits for different scenarios
        economic_scenarios = {}

        print(f"\n💰 ECONOMIC BENEFIT SCENARIOS:")
        print(f"{'Scenario':<25} {'Rate (NZD/hr)':<15} {'Annual Benefit':<20} {'Daily Benefit':<15}")
        print("-" * 80)

        for scenario, hourly_rate in self.vott_rates.items():
            annual_benefit = annual_time_savings_hours * hourly_rate
            daily_benefit = daily_time_savings_hours * hourly_rate

            economic_scenarios[scenario] = {
                'hourly_rate': hourly_rate,
                'annual_benefit': annual_benefit,
                'daily_benefit': daily_benefit,
                'benefit_per_trip': time_savings_hours * hourly_rate
            }

            scenario_display = scenario.replace('_', ' ').title()
            print(f"{scenario_display:<25} ${hourly_rate:<14.2f} ${annual_benefit:<19,.0f} ${daily_benefit:<14,.0f}")

        self.economic_scenarios = economic_scenarios
        self.aggregate_benefits = {
            'daily_time_savings_hours': daily_time_savings_hours,
            'annual_time_savings_hours': annual_time_savings_hours
        }

        return economic_scenarios

    def calculate_confidence_intervals(self):
        """Calculate confidence intervals for economic estimates"""
        print(f"\n📏 CONFIDENCE INTERVALS FOR ECONOMIC ESTIMATES")

        # Use confidence interval from statistical analysis
        ci_lower = self.stats_results['confidence_interval_lower']
        ci_upper = self.stats_results['confidence_interval_upper']

        print(f"   • Speed increase 95% CI: [{ci_lower:.2f}, {ci_upper:.2f}] km/h")

        # Calculate time savings CI based on speed CI
        before_speed = self.stats_results['before_mean_speed']

        # Lower bound (conservative estimate)
        after_speed_lower = before_speed + ci_lower
        time_savings_lower = ((self.corridor_length_km / before_speed) -
                             (self.corridor_length_km / after_speed_lower)) * 60

        # Upper bound (optimistic estimate)
        after_speed_upper = before_speed + ci_upper
        time_savings_upper = ((self.corridor_length_km / before_speed) -
                             (self.corridor_length_km / after_speed_upper)) * 60

        print(f"   • Time savings per trip 95% CI: [{time_savings_lower:.2f}, {time_savings_upper:.2f}] minutes")

        # Economic benefit confidence intervals (using average mixed traffic rate)
        avg_rate = self.vott_rates['average_mixed_traffic']
        annual_hours = self.aggregate_benefits['annual_time_savings_hours']

        # Scale by confidence interval
        ci_scale_lower = time_savings_lower / self.time_savings['time_savings_per_trip_minutes']
        ci_scale_upper = time_savings_upper / self.time_savings['time_savings_per_trip_minutes']

        benefit_lower = annual_hours * avg_rate * ci_scale_lower
        benefit_upper = annual_hours * avg_rate * ci_scale_upper

        print(f"   • Annual economic benefit 95% CI: [${benefit_lower:,.0f}, ${benefit_upper:,.0f}] NZD")

        self.confidence_intervals = {
            'time_savings_lower': time_savings_lower,
            'time_savings_upper': time_savings_upper,
            'economic_benefit_lower': benefit_lower,
            'economic_benefit_upper': benefit_upper
        }

        return self.confidence_intervals

    def assess_statistical_robustness(self):
        """Assess statistical robustness and reliability of estimates"""
        print(f"\n🔬 STATISTICAL ROBUSTNESS ASSESSMENT")

        sample_size_before = self.stats_results['before_period_trips']
        sample_size_after = self.stats_results['after_period_trips']
        effect_size = self.stats_results['cohens_d']
        p_value = self.stats_results['p_value']

        robustness = {
            'sample_size_adequate': sample_size_before > 1000 and sample_size_after > 100,
            'effect_size_meaningful': abs(effect_size) > 0.2,  # Small to medium effect
            'statistical_significance': p_value < 0.05,
            'before_after_ratio': sample_size_before / sample_size_after if sample_size_after > 0 else float('inf')
        }

        print(f"📊 ROBUSTNESS INDICATORS:")
        print(f"   • Sample sizes: Before={sample_size_before:,}, After={sample_size_after:,}")
        print(f"   • Sample size adequate: {'✅' if robustness['sample_size_adequate'] else '⚠️'}")
        print(f"   • Effect size meaningful: {'✅' if robustness['effect_size_meaningful'] else '⚠️'} (d={effect_size:.3f})")
        print(f"   • Statistically significant: {'✅' if robustness['statistical_significance'] else '❌'}")
        print(f"   • Before/after ratio: {robustness['before_after_ratio']:.0f}:1")

        # Overall reliability assessment
        reliability_score = sum([
            robustness['sample_size_adequate'],
            robustness['effect_size_meaningful'],
            robustness['statistical_significance']
        ])

        reliability_levels = {3: "High", 2: "Medium", 1: "Low", 0: "Very Low"}
        reliability = reliability_levels[reliability_score]

        print(f"   • Overall reliability: {reliability} ({reliability_score}/3)")

        if robustness['before_after_ratio'] > 100:
            print(f"   ⚠️  Warning: Imbalanced sample sizes may affect precision")

        self.robustness = robustness
        self.reliability = reliability

        return robustness

    def generate_executive_summary(self):
        """Generate executive summary of economic impacts"""
        print(f"\n📋 EXECUTIVE SUMMARY")

        # Key metrics
        primary_scenario = self.economic_scenarios['average_mixed_traffic']
        conservative_scenario = self.economic_scenarios['light_vehicle_commuting']
        optimistic_scenario = self.economic_scenarios['heavy_vehicle_freight']

        summary = {
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'study_corridor': 'SH1/SH76 Christchurch Southern Motorway',
            'speed_limit_change': '100 → 110 km/h',
            'implementation_date': '2025-04-13',

            # Statistical findings
            'observed_speed_increase_kmh': self.stats_results['speed_increase_kmh'],
            'speed_increase_percent': self.stats_results['speed_increase_percent'],
            'statistical_significance': 'Yes' if self.stats_results['statistically_significant'] else 'No',
            'effect_size': self.stats_results['cohens_d'],

            # Time savings
            'time_savings_per_trip_minutes': self.time_savings['time_savings_per_trip_minutes'],
            'annual_time_savings_hours': self.aggregate_benefits['annual_time_savings_hours'],

            # Economic benefits (NZD)
            'conservative_annual_benefit': conservative_scenario['annual_benefit'],
            'primary_annual_benefit': primary_scenario['annual_benefit'],
            'optimistic_annual_benefit': optimistic_scenario['annual_benefit'],

            # Confidence intervals
            'time_savings_ci_lower': self.confidence_intervals['time_savings_lower'],
            'time_savings_ci_upper': self.confidence_intervals['time_savings_upper'],
            'economic_benefit_ci_lower': self.confidence_intervals['economic_benefit_lower'],
            'economic_benefit_ci_upper': self.confidence_intervals['economic_benefit_upper'],

            # Reliability
            'analysis_reliability': self.reliability
        }

        print(f"🎯 KEY FINDINGS:")
        print(f"   • Observed speed increase: {summary['observed_speed_increase_kmh']:.1f} km/h ({summary['speed_increase_percent']:.1f}%)")
        print(f"   • Time savings per trip: {summary['time_savings_per_trip_minutes']:.2f} minutes")
        print(f"   • Annual time savings: {summary['annual_time_savings_hours']:,.0f} hours")
        print(f"   • Statistical significance: {summary['statistical_significance']}")

        print(f"\n💰 ECONOMIC BENEFITS (Annual, NZD):")
        print(f"   • Conservative estimate: ${summary['conservative_annual_benefit']:,.0f}")
        print(f"   • Primary estimate: ${summary['primary_annual_benefit']:,.0f}")
        print(f"   • Optimistic estimate: ${summary['optimistic_annual_benefit']:,.0f}")
        print(f"   • 95% Confidence interval: [${summary['economic_benefit_ci_lower']:,.0f}, ${summary['economic_benefit_ci_upper']:,.0f}]")

        print(f"\n🔬 ANALYSIS RELIABILITY: {summary['analysis_reliability']}")

        self.executive_summary = summary
        return summary

    def save_comprehensive_report(self):
        """Save comprehensive economic impact report"""
        print(f"\n💾 SAVING COMPREHENSIVE REPORT")

        # Main economic impact report
        report_data = {
            **self.executive_summary,
            **{f'vott_{k}': v['hourly_rate'] for k, v in self.economic_scenarios.items()},
            **{f'annual_benefit_{k}': v['annual_benefit'] for k, v in self.economic_scenarios.items()},
            **{f'daily_benefit_{k}': v['daily_benefit'] for k, v in self.economic_scenarios.items()},
            **{f'benefit_per_trip_{k}': v['benefit_per_trip'] for k, v in self.economic_scenarios.items()},
        }

        report_df = pd.DataFrame([report_data])
        report_path = os.path.join(self.output_dir, "economic_impact_assessment.csv")
        report_df.to_csv(report_path, index=False)
        print(f"✅ Economic impact report: {report_path}")

        # Summary table for easy reference
        summary_table = pd.DataFrame([
            {'Metric': 'Speed Increase', 'Value': f"{self.executive_summary['observed_speed_increase_kmh']:.1f} km/h", 'Unit': 'km/h'},
            {'Metric': 'Time Savings per Trip', 'Value': f"{self.executive_summary['time_savings_per_trip_minutes']:.2f}", 'Unit': 'minutes'},
            {'Metric': 'Annual Time Savings', 'Value': f"{self.executive_summary['annual_time_savings_hours']:,.0f}", 'Unit': 'hours'},
            {'Metric': 'Primary Economic Benefit', 'Value': f"${self.executive_summary['primary_annual_benefit']:,.0f}", 'Unit': 'NZD/year'},
            {'Metric': 'Confidence Interval (Lower)', 'Value': f"${self.executive_summary['economic_benefit_ci_lower']:,.0f}", 'Unit': 'NZD/year'},
            {'Metric': 'Confidence Interval (Upper)', 'Value': f"${self.executive_summary['economic_benefit_ci_upper']:,.0f}", 'Unit': 'NZD/year'},
            {'Metric': 'Analysis Reliability', 'Value': self.executive_summary['analysis_reliability'], 'Unit': 'Qualitative'}
        ])

        summary_path = os.path.join(self.output_dir, "economic_impact_summary.csv")
        summary_table.to_csv(summary_path, index=False)
        print(f"✅ Executive summary: {summary_path}")

        return True

def main():
    assessor = EconomicImpactAssessment()

    # Load statistical results
    if not assessor.load_statistical_results():
        print("❌ Cannot proceed without statistical results")
        return

    # Calculate economic impacts
    assessor.calculate_travel_time_savings()
    assessor.estimate_aggregate_benefits()
    assessor.calculate_confidence_intervals()
    assessor.assess_statistical_robustness()

    # Generate reports
    assessor.generate_executive_summary()
    assessor.save_comprehensive_report()

    print(f"\n✅ ECONOMIC IMPACT ASSESSMENT COMPLETE")
    print(f"Professional economic analysis of speed limit change benefits")

if __name__ == "__main__":
    main()
"""
Statistical Analysis of Speed Limit Change Impact
Professional before/after analysis of SH1/SH76 Christchurch Southern Motorway
Speed limit increase from 100 km/h to 110 km/h effective April 13, 2025
"""

import pandas as pd
import numpy as np
import os
from scipy import stats
from scipy.stats import ttest_ind, mannwhitneyu, levene, chi2_contingency
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class SpeedChangeAnalysis:
    def __init__(self):
        self.base_dir = "/Volumes/T7/Data/connected_vehicle_data"
        self.data_dir = os.path.join(self.base_dir, "output", "processed_data")
        self.output_dir = os.path.join(self.base_dir, "output", "reports")

        # Study parameters
        self.speed_change_date = pd.to_datetime("2025-04-13")
        self.baseline_speed_limit = 100  # km/h
        self.new_speed_limit = 110  # km/h
        self.corridor_length_km = 17.7  # SH1/SH76 study segment

        # Statistical parameters
        self.alpha = 0.05  # Significance level
        self.confidence_level = 0.95

        os.makedirs(self.output_dir, exist_ok=True)

        print("📊 STATISTICAL ANALYSIS: SH1/SH76 SPEED LIMIT CHANGE IMPACT")
        print("Before/After Analysis of 100→110 km/h Speed Limit Increase")
        print("="*65)

    def load_integrated_data(self):
        """Load the integrated trip dataset"""
        print(f"\n📂 LOADING INTEGRATED DATASET")

        data_path = os.path.join(self.data_dir, "integrated_trip_summary.csv")
        if not os.path.exists(data_path):
            print(f"❌ Integrated data not found: {data_path}")
            return None

        self.data = pd.read_csv(data_path)
        self.data['trip_start_time'] = pd.to_datetime(self.data['trip_start_time'], format='mixed', errors='coerce')

        # Filter for valid speed data
        valid_speeds = (
            (self.data['avg_speed_kmh'].notna()) &
            (self.data['avg_speed_kmh'] > 10) &
            (self.data['avg_speed_kmh'] < 150)
        )
        self.data = self.data[valid_speeds].copy()

        print(f"✅ Dataset loaded: {len(self.data):,} trips with valid speed data")
        print(f"📅 Date range: {self.data['trip_start_time'].min()} to {self.data['trip_start_time'].max()}")

        # Create period classification
        self.data['period'] = self.data['trip_start_time'].apply(
            lambda x: 'before' if x < self.speed_change_date else 'after'
        )

        # Period summary
        period_counts = self.data['period'].value_counts()
        print(f"\n📈 PERIOD DISTRIBUTION:")
        for period, count in period_counts.items():
            print(f"   • {period.upper()}: {count:,} trips")

        return True

    def perform_descriptive_analysis(self):
        """Comprehensive descriptive statistics"""
        print(f"\n📊 DESCRIPTIVE ANALYSIS")

        before_data = self.data[self.data['period'] == 'before']['avg_speed_kmh']
        after_data = self.data[self.data['period'] == 'after']['avg_speed_kmh']

        descriptive_stats = {
            'before': {
                'n': len(before_data),
                'mean': before_data.mean(),
                'median': before_data.median(),
                'std': before_data.std(),
                'min': before_data.min(),
                'max': before_data.max(),
                'q25': before_data.quantile(0.25),
                'q75': before_data.quantile(0.75),
                'skewness': stats.skew(before_data),
                'kurtosis': stats.kurtosis(before_data)
            },
            'after': {
                'n': len(after_data),
                'mean': after_data.mean(),
                'median': after_data.median(),
                'std': after_data.std(),
                'min': after_data.min(),
                'max': after_data.max(),
                'q25': after_data.quantile(0.25),
                'q75': after_data.quantile(0.75),
                'skewness': stats.skew(after_data),
                'kurtosis': stats.kurtosis(after_data)
            }
        }

        print(f"📋 DESCRIPTIVE STATISTICS:")
        print(f"{'Metric':<15} {'Before':<12} {'After':<12} {'Difference':<12}")
        print("-" * 55)

        for metric in ['n', 'mean', 'median', 'std']:
            before_val = descriptive_stats['before'][metric]
            after_val = descriptive_stats['after'][metric]
            diff = after_val - before_val if metric != 'n' else after_val - before_val

            if metric == 'n':
                print(f"{metric.upper():<15} {before_val:<12,.0f} {after_val:<12,.0f} {diff:<12,.0f}")
            else:
                print(f"{metric.capitalize():<15} {before_val:<12.2f} {after_val:<12.2f} {diff:<12.2f}")

        # Effect size (Cohen's d)
        pooled_std = np.sqrt(((len(before_data)-1)*before_data.var() + (len(after_data)-1)*after_data.var()) /
                            (len(before_data) + len(after_data) - 2))
        cohens_d = (after_data.mean() - before_data.mean()) / pooled_std

        print(f"\n📏 EFFECT SIZE:")
        print(f"   • Cohen's d: {cohens_d:.3f}")

        effect_magnitude = "small" if abs(cohens_d) < 0.5 else "medium" if abs(cohens_d) < 0.8 else "large"
        print(f"   • Magnitude: {effect_magnitude}")

        self.descriptive_stats = descriptive_stats
        self.cohens_d = cohens_d

        return descriptive_stats

    def test_statistical_assumptions(self):
        """Test assumptions for parametric/non-parametric tests"""
        print(f"\n🔬 TESTING STATISTICAL ASSUMPTIONS")

        before_speeds = self.data[self.data['period'] == 'before']['avg_speed_kmh']
        after_speeds = self.data[self.data['period'] == 'after']['avg_speed_kmh']

        assumptions = {}

        # 1. Test for normality (Shapiro-Wilk for small samples, Anderson-Darling for large)
        sample_size_before = min(5000, len(before_speeds))
        sample_size_after = min(5000, len(after_speeds))

        if sample_size_before <= 5000 and sample_size_after <= 5000:
            # Shapiro-Wilk test
            before_sample = before_speeds.sample(sample_size_before) if len(before_speeds) > sample_size_before else before_speeds
            after_sample = after_speeds.sample(sample_size_after) if len(after_speeds) > sample_size_after else after_speeds
            before_normal_stat, before_normal_p = stats.shapiro(before_sample)
            after_normal_stat, after_normal_p = stats.shapiro(after_sample)
            test_name = "Shapiro-Wilk"
        else:
            # Anderson-Darling test for large samples
            before_sample = before_speeds.sample(sample_size_before) if len(before_speeds) > sample_size_before else before_speeds
            after_sample = after_speeds.sample(sample_size_after) if len(after_speeds) > sample_size_after else after_speeds
            before_normal_result = stats.anderson(before_sample, dist='norm')
            after_normal_result = stats.anderson(after_sample, dist='norm')
            # Approximate p-values from critical values
            before_normal_p = 0.05 if before_normal_result.statistic > before_normal_result.critical_values[2] else 0.1
            after_normal_p = 0.05 if after_normal_result.statistic > after_normal_result.critical_values[2] else 0.1
            test_name = "Anderson-Darling"

        assumptions['normality_test'] = test_name
        assumptions['before_normal'] = before_normal_p > self.alpha
        assumptions['after_normal'] = after_normal_p > self.alpha
        assumptions['before_normal_p'] = before_normal_p
        assumptions['after_normal_p'] = after_normal_p

        # 2. Test for equal variances (Levene's test)
        levene_stat, levene_p = levene(before_speeds, after_speeds)
        assumptions['equal_variances'] = levene_p > self.alpha
        assumptions['levene_p'] = levene_p

        print(f"📋 ASSUMPTION TEST RESULTS:")
        print(f"   • Normality ({test_name}):")
        print(f"     - Before period: {'✅ Normal' if assumptions['before_normal'] else '❌ Non-normal'} (p={before_normal_p:.4f})")
        print(f"     - After period: {'✅ Normal' if assumptions['after_normal'] else '❌ Non-normal'} (p={after_normal_p:.4f})")
        print(f"   • Equal variances (Levene): {'✅ Equal' if assumptions['equal_variances'] else '❌ Unequal'} (p={levene_p:.4f})")

        # Recommend appropriate test
        if assumptions['before_normal'] and assumptions['after_normal']:
            if assumptions['equal_variances']:
                recommended_test = "Independent t-test (equal variances)"
            else:
                recommended_test = "Welch's t-test (unequal variances)"
        else:
            recommended_test = "Mann-Whitney U test (non-parametric)"

        print(f"   • Recommended test: {recommended_test}")

        self.assumptions = assumptions
        return assumptions

    def perform_hypothesis_testing(self):
        """Perform appropriate hypothesis tests"""
        print(f"\n🧪 HYPOTHESIS TESTING")

        before_speeds = self.data[self.data['period'] == 'before']['avg_speed_kmh']
        after_speeds = self.data[self.data['period'] == 'after']['avg_speed_kmh']

        # Null hypothesis: No difference in mean speeds
        # Alternative hypothesis: Speeds increased after the limit change
        print(f"   H₀: μ_after = μ_before (no change in speeds)")
        print(f"   H₁: μ_after > μ_before (speeds increased)")
        print(f"   α = {self.alpha}")

        test_results = {}

        # Perform appropriate test based on assumptions
        if self.assumptions['before_normal'] and self.assumptions['after_normal']:
            # Parametric tests
            if self.assumptions['equal_variances']:
                # Independent t-test with equal variances
                t_stat, p_value = ttest_ind(after_speeds, before_speeds, equal_var=True, alternative='greater')
                test_used = "Independent t-test (equal variances)"
            else:
                # Welch's t-test (unequal variances)
                t_stat, p_value = ttest_ind(after_speeds, before_speeds, equal_var=False, alternative='greater')
                test_used = "Welch's t-test (unequal variances)"

            test_results['test_statistic'] = t_stat
            test_results['statistic_name'] = 't-statistic'
        else:
            # Non-parametric test
            u_stat, p_value = mannwhitneyu(after_speeds, before_speeds, alternative='greater')
            test_used = "Mann-Whitney U test"
            test_results['test_statistic'] = u_stat
            test_results['statistic_name'] = 'U-statistic'

        test_results['test_used'] = test_used
        test_results['p_value'] = p_value
        test_results['significant'] = p_value < self.alpha

        # Calculate confidence interval for difference in means
        mean_diff = after_speeds.mean() - before_speeds.mean()
        if self.assumptions['before_normal'] and self.assumptions['after_normal']:
            # Parametric CI
            se_diff = np.sqrt(before_speeds.var()/len(before_speeds) + after_speeds.var()/len(after_speeds))
            df = len(before_speeds) + len(after_speeds) - 2
            t_critical = stats.t.ppf(1 - self.alpha/2, df)
            ci_lower = mean_diff - t_critical * se_diff
            ci_upper = mean_diff + t_critical * se_diff
        else:
            # Bootstrap CI for non-parametric
            n_bootstrap = 1000
            bootstrap_diffs = []
            for _ in range(n_bootstrap):
                before_sample = np.random.choice(before_speeds, size=len(before_speeds), replace=True)
                after_sample = np.random.choice(after_speeds, size=len(after_speeds), replace=True)
                bootstrap_diffs.append(after_sample.mean() - before_sample.mean())

            ci_lower = np.percentile(bootstrap_diffs, (self.alpha/2)*100)
            ci_upper = np.percentile(bootstrap_diffs, (1-self.alpha/2)*100)

        test_results['mean_difference'] = mean_diff
        test_results['ci_lower'] = ci_lower
        test_results['ci_upper'] = ci_upper

        print(f"\n📊 TEST RESULTS:")
        print(f"   • Test used: {test_used}")
        print(f"   • {test_results['statistic_name']}: {test_results['test_statistic']:.4f}")
        print(f"   • p-value: {p_value:.6f}")
        print(f"   • Result: {'✅ Significant' if test_results['significant'] else '❌ Not significant'}")
        print(f"   • Mean difference: {mean_diff:.2f} km/h")
        print(f"   • 95% CI: [{ci_lower:.2f}, {ci_upper:.2f}] km/h")

        self.test_results = test_results
        return test_results

    def analyze_compliance_rates(self):
        """Analyze speed limit compliance rates"""
        print(f"\n🚦 SPEED LIMIT COMPLIANCE ANALYSIS")

        compliance_analysis = {}

        for period in ['before', 'after']:
            period_data = self.data[self.data['period'] == period]
            speed_limit = self.baseline_speed_limit if period == 'before' else self.new_speed_limit

            # Calculate compliance (not exceeding speed limit)
            compliant = (period_data['avg_speed_kmh'] <= speed_limit).sum()
            total = len(period_data)
            compliance_rate = (compliant / total) * 100 if total > 0 else 0

            # Calculate violations by severity
            minor_violations = ((period_data['avg_speed_kmh'] > speed_limit) &
                              (period_data['avg_speed_kmh'] <= speed_limit + 10)).sum()
            major_violations = (period_data['avg_speed_kmh'] > speed_limit + 10).sum()

            compliance_analysis[period] = {
                'total_trips': total,
                'compliant_trips': compliant,
                'compliance_rate': compliance_rate,
                'minor_violations': minor_violations,
                'major_violations': major_violations,
                'minor_violation_rate': (minor_violations / total) * 100 if total > 0 else 0,
                'major_violation_rate': (major_violations / total) * 100 if total > 0 else 0
            }

        print(f"📋 COMPLIANCE RATES:")
        print(f"{'Period':<8} {'Limit':<6} {'Compliant':<10} {'Minor Viol.':<12} {'Major Viol.':<12}")
        print("-" * 55)

        for period in ['before', 'after']:
            stats = compliance_analysis[period]
            limit = self.baseline_speed_limit if period == 'before' else self.new_speed_limit
            print(f"{period.capitalize():<8} {limit:<6} {stats['compliance_rate']:<10.1f}% "
                  f"{stats['minor_violation_rate']:<12.1f}% {stats['major_violation_rate']:<12.1f}%")

        # Test for significant change in compliance rates
        before_compliant = compliance_analysis['before']['compliant_trips']
        before_total = compliance_analysis['before']['total_trips']
        after_compliant = compliance_analysis['after']['compliant_trips']
        after_total = compliance_analysis['after']['total_trips']

        # Chi-square test for proportions
        contingency_table = [[before_compliant, before_total - before_compliant],
                           [after_compliant, after_total - after_compliant]]
        chi2_result = chi2_contingency(contingency_table)
        chi2, p_compliance = chi2_result[0], chi2_result[1]

        compliance_analysis['compliance_change_significant'] = p_compliance < self.alpha
        compliance_analysis['compliance_chi2'] = chi2
        compliance_analysis['compliance_p_value'] = p_compliance

        print(f"\n📈 COMPLIANCE CHANGE TEST:")
        print(f"   • Chi-square: {chi2:.4f}")
        print(f"   • p-value: {p_compliance:.6f}")
        print(f"   • Result: {'✅ Significant change' if compliance_analysis['compliance_change_significant'] else '❌ No significant change'}")

        self.compliance_analysis = compliance_analysis
        return compliance_analysis

    def generate_comprehensive_report(self):
        """Generate comprehensive statistical report"""
        print(f"\n📋 GENERATING COMPREHENSIVE REPORT")

        report = {
            # Study metadata
            'analysis_date': datetime.now().isoformat(),
            'study_location': 'SH1/SH76 Christchurch Southern Motorway',
            'corridor_length_km': self.corridor_length_km,
            'speed_change_date': str(self.speed_change_date.date()),
            'baseline_speed_limit': self.baseline_speed_limit,
            'new_speed_limit': self.new_speed_limit,

            # Sample sizes
            'total_trips': len(self.data),
            'before_period_trips': self.descriptive_stats['before']['n'],
            'after_period_trips': self.descriptive_stats['after']['n'],

            # Descriptive statistics
            'before_mean_speed': self.descriptive_stats['before']['mean'],
            'after_mean_speed': self.descriptive_stats['after']['mean'],
            'before_std_speed': self.descriptive_stats['before']['std'],
            'after_std_speed': self.descriptive_stats['after']['std'],
            'speed_increase_kmh': self.descriptive_stats['after']['mean'] - self.descriptive_stats['before']['mean'],
            'speed_increase_percent': ((self.descriptive_stats['after']['mean'] - self.descriptive_stats['before']['mean']) /
                                     self.descriptive_stats['before']['mean']) * 100,

            # Effect size
            'cohens_d': self.cohens_d,
            'effect_magnitude': "small" if abs(self.cohens_d) < 0.5 else "medium" if abs(self.cohens_d) < 0.8 else "large",

            # Statistical tests
            'assumptions_met': self.assumptions['before_normal'] and self.assumptions['after_normal'],
            'test_used': self.test_results['test_used'],
            'test_statistic': self.test_results['test_statistic'],
            'p_value': self.test_results['p_value'],
            'statistically_significant': self.test_results['significant'],
            'confidence_interval_lower': self.test_results['ci_lower'],
            'confidence_interval_upper': self.test_results['ci_upper'],

            # Compliance analysis
            'before_compliance_rate': self.compliance_analysis['before']['compliance_rate'],
            'after_compliance_rate': self.compliance_analysis['after']['compliance_rate'],
            'compliance_change_significant': self.compliance_analysis['compliance_change_significant'],

            # Statistical power and sample size adequacy
            'sample_size_adequate': len(self.data) > 1000,  # Rule of thumb for transportation studies
            'before_after_ratio': self.descriptive_stats['before']['n'] / self.descriptive_stats['after']['n']
        }

        # Display key findings
        print(f"\n🎯 KEY STATISTICAL FINDINGS:")
        print(f"   • Sample size: {report['total_trips']:,} trips ({report['before_period_trips']:,} before, {report['after_period_trips']:,} after)")
        print(f"   • Mean speed change: {report['speed_increase_kmh']:.2f} km/h ({report['speed_increase_percent']:.1f}%)")
        print(f"   • Effect size: {report['cohens_d']:.3f} ({report['effect_magnitude']})")
        print(f"   • Statistical significance: {'✅ Yes' if report['statistically_significant'] else '❌ No'} (p={report['p_value']:.6f})")
        print(f"   • 95% CI: [{report['confidence_interval_lower']:.2f}, {report['confidence_interval_upper']:.2f}] km/h")
        print(f"   • Compliance rate change: {report['after_compliance_rate']:.1f}% → {report['before_compliance_rate']:.1f}%")

        # Save report
        report_df = pd.DataFrame([report])
        report_path = os.path.join(self.output_dir, "statistical_analysis_report.csv")
        report_df.to_csv(report_path, index=False)
        print(f"\n💾 Statistical report saved: {report_path}")

        return report

def main():
    analyzer = SpeedChangeAnalysis()

    # Load integrated dataset
    if not analyzer.load_integrated_data():
        print("❌ Failed to load data")
        return

    # Perform statistical analysis
    analyzer.perform_descriptive_analysis()
    analyzer.test_statistical_assumptions()
    analyzer.perform_hypothesis_testing()
    analyzer.analyze_compliance_rates()

    # Generate comprehensive report
    analyzer.generate_comprehensive_report()

    print(f"\n✅ STATISTICAL ANALYSIS COMPLETE")
    print(f"Professional before/after analysis of speed limit change impact")

if __name__ == "__main__":
    main()
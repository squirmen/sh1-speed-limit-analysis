"""
Comprehensive Analysis Visualization Suite
High-quality visualizations for statistical, economic, and behavioral analysis
SH1/SH76 Speed Limit Change Impact Study
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import folium
from folium import plugins
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set professional styling
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class AnalysisVisualizationSuite:
    def __init__(self):
        self.base_dir = "/Volumes/T7/Data/connected_vehicle_data"
        self.data_dir = os.path.join(self.base_dir, "output", "processed_data")
        self.reports_dir = os.path.join(self.base_dir, "output", "reports")
        self.figures_dir = os.path.join(self.base_dir, "output", "figures")

        # Create figures directory
        os.makedirs(self.figures_dir, exist_ok=True)
        os.makedirs(os.path.join(self.figures_dir, "static"), exist_ok=True)
        os.makedirs(os.path.join(self.figures_dir, "interactive"), exist_ok=True)

        # Professional color scheme
        self.colors = {
            'before': '#2E86AB',      # Professional blue
            'after': '#A23B72',       # Professional magenta
            'primary': '#F18F01',     # Professional orange
            'secondary': '#C73E1D',   # Professional red
            'success': '#92B4A7',     # Professional green
            'neutral': '#6C757D'      # Professional gray
        }

        print("📊 COMPREHENSIVE VISUALIZATION SUITE")
        print("High-Quality Visualizations for Speed Limit Analysis")
        print("="*55)

    def load_analysis_results(self):
        """Load all analysis results"""
        print(f"\n📂 LOADING ANALYSIS RESULTS")

        results = {}

        # Statistical analysis results
        stats_path = os.path.join(self.reports_dir, "statistical_analysis_report.csv")
        if os.path.exists(stats_path):
            results['statistical'] = pd.read_csv(stats_path).iloc[0].to_dict()
            print("✅ Statistical analysis results loaded")
        else:
            print("⚠️  Statistical results not found")

        # Economic impact results
        economic_path = os.path.join(self.reports_dir, "economic_impact_assessment.csv")
        if os.path.exists(economic_path):
            results['economic'] = pd.read_csv(economic_path).iloc[0].to_dict()
            print("✅ Economic impact results loaded")
        else:
            print("⚠️  Economic results not found")

        # Trip summary data
        trips_path = os.path.join(self.data_dir, "integrated_trip_summary.csv")
        if os.path.exists(trips_path):
            results['trips'] = pd.read_csv(trips_path)
            results['trips']['trip_start_time'] = pd.to_datetime(results['trips']['trip_start_time'], format='mixed', errors='coerce')
            results['trips']['period'] = results['trips']['trip_start_time'].apply(
                lambda x: 'Before' if pd.notna(x) and x < pd.to_datetime("2025-04-13") else 'After'
            )
            print(f"✅ Trip data loaded: {len(results['trips']):,} trips")
        else:
            print("⚠️  Trip data not found")

        # Behavioral analysis results (if available)
        behavior_events_path = os.path.join(self.reports_dir, "hard_driving_events.csv")
        if os.path.exists(behavior_events_path):
            results['hard_events'] = pd.read_csv(behavior_events_path)
            print("✅ Behavioral events loaded")

        near_miss_path = os.path.join(self.reports_dir, "near_miss_events.csv")
        if os.path.exists(near_miss_path):
            results['near_miss'] = pd.read_csv(near_miss_path)
            print("✅ Near-miss events loaded")

        self.results = results
        return results

    def create_statistical_dashboard(self):
        """Create comprehensive statistical analysis dashboard"""
        print(f"\n📊 CREATING STATISTICAL ANALYSIS DASHBOARD")

        if 'statistical' not in self.results or 'trips' not in self.results:
            print("❌ Missing required data for statistical dashboard")
            return

        stats = self.results['statistical']
        trips = self.results['trips']

        # Create subplot figure
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Speed Distribution Before/After',
                'Statistical Test Results',
                'Sample Size Comparison',
                'Effect Size & Confidence Interval',
                'Time Series: Speed Trend',
                'Compliance Analysis'
            ),
            specs=[
                [{"type": "scatter"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "scatter"}],
                [{"type": "scatter"}, {"type": "bar"}]
            ],
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )

        # 1. Speed Distribution
        before_speeds = trips[trips['period'] == 'Before']['avg_speed_kmh'].dropna()
        after_speeds = trips[trips['period'] == 'After']['avg_speed_kmh'].dropna()

        fig.add_trace(go.Histogram(
            x=before_speeds,
            name='Before',
            opacity=0.7,
            marker_color=self.colors['before'],
            nbinsx=30
        ), row=1, col=1)

        fig.add_trace(go.Histogram(
            x=after_speeds,
            name='After',
            opacity=0.7,
            marker_color=self.colors['after'],
            nbinsx=30
        ), row=1, col=1)

        # 2. Statistical Test Results
        fig.add_trace(go.Bar(
            x=['Before Mean', 'After Mean', 'Difference'],
            y=[stats['before_mean_speed'], stats['after_mean_speed'], stats['speed_increase_kmh']],
            marker_color=[self.colors['before'], self.colors['after'], self.colors['primary']],
            name='Speed Statistics'
        ), row=1, col=2)

        # 3. Sample Size Comparison
        fig.add_trace(go.Bar(
            x=['Before Period', 'After Period'],
            y=[stats['before_period_trips'], stats['after_period_trips']],
            marker_color=[self.colors['before'], self.colors['after']],
            name='Sample Sizes'
        ), row=2, col=1)

        # 4. Effect Size & Confidence Interval
        fig.add_trace(go.Scatter(
            x=['Effect Size'],
            y=[stats['cohens_d']],
            mode='markers',
            marker=dict(size=20, color=self.colors['primary']),
            name="Cohen's d"
        ), row=2, col=2)

        # Add CI error bars
        ci_lower = stats['confidence_interval_lower']
        ci_upper = stats['confidence_interval_upper']
        ci_center = (ci_lower + ci_upper) / 2

        fig.add_trace(go.Scatter(
            x=['Speed Increase'],
            y=[ci_center],
            error_y=dict(
                type='data',
                symmetric=False,
                arrayminus=[ci_center - ci_lower],
                array=[ci_upper - ci_center]
            ),
            mode='markers',
            marker=dict(size=15, color=self.colors['secondary']),
            name='95% CI'
        ), row=2, col=2)

        # 5. Time Series (if sufficient data)
        if len(trips) > 100:
            # Create monthly aggregation
            trips['month'] = trips['trip_start_time'].dt.to_period('M')
            monthly_speeds = trips.groupby(['month', 'period'])['avg_speed_kmh'].mean().unstack(fill_value=np.nan)

            if 'Before' in monthly_speeds.columns:
                fig.add_trace(go.Scatter(
                    x=monthly_speeds.index.astype(str),
                    y=monthly_speeds['Before'],
                    mode='lines+markers',
                    name='Before Trend',
                    line=dict(color=self.colors['before'])
                ), row=3, col=1)

            if 'After' in monthly_speeds.columns:
                fig.add_trace(go.Scatter(
                    x=monthly_speeds.index.astype(str),
                    y=monthly_speeds['After'],
                    mode='lines+markers',
                    name='After Trend',
                    line=dict(color=self.colors['after'])
                ), row=3, col=1)

        # 6. Compliance Analysis
        before_compliant = (before_speeds <= 100).sum()
        before_total = len(before_speeds)
        after_compliant = (after_speeds <= 110).sum()
        after_total = len(after_speeds)

        compliance_data = pd.DataFrame({
            'Period': ['Before (≤100 km/h)', 'After (≤110 km/h)'],
            'Compliant': [before_compliant/before_total*100, after_compliant/after_total*100],
            'Non-Compliant': [(before_total-before_compliant)/before_total*100,
                             (after_total-after_compliant)/after_total*100]
        })

        fig.add_trace(go.Bar(
            x=compliance_data['Period'],
            y=compliance_data['Compliant'],
            name='Compliant',
            marker_color=self.colors['success']
        ), row=3, col=2)

        fig.add_trace(go.Bar(
            x=compliance_data['Period'],
            y=compliance_data['Non-Compliant'],
            name='Non-Compliant',
            marker_color=self.colors['secondary']
        ), row=3, col=2)

        # Update layout
        fig.update_layout(
            title=dict(
                text='SH1/SH76 Speed Limit Analysis: Statistical Dashboard',
                font=dict(size=20, color='#2C3E50'),
                x=0.5
            ),
            showlegend=True,
            height=1200,
            font=dict(family="Arial", size=12),
            template="plotly_white"
        )

        # Save interactive version
        interactive_path = os.path.join(self.figures_dir, "interactive", "statistical_dashboard.html")
        fig.write_html(interactive_path)
        print(f"✅ Statistical dashboard: {interactive_path}")

        # Save static version
        static_path = os.path.join(self.figures_dir, "static", "statistical_dashboard.png")
        fig.write_image(static_path, width=1400, height=1200, scale=2)
        print(f"✅ Static dashboard: {static_path}")

    def create_economic_impact_visualization(self):
        """Create economic impact visualization"""
        print(f"\n💰 CREATING ECONOMIC IMPACT VISUALIZATION")

        if 'economic' not in self.results:
            print("❌ Missing economic data")
            return

        econ = self.results['economic']

        # Create economic impact visualization
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Annual Economic Benefits by Scenario',
                'Time Savings Breakdown',
                'Confidence Intervals',
                'Daily vs Annual Impact'
            ),
            specs=[
                [{"type": "bar"}, {"type": "pie"}],
                [{"type": "scatter"}, {"type": "bar"}]
            ]
        )

        # 1. Annual Benefits by Scenario
        scenarios = ['Conservative', 'Primary', 'Optimistic']
        benefits = [
            econ['conservative_annual_benefit'],
            econ['primary_annual_benefit'],
            econ['optimistic_annual_benefit']
        ]

        fig.add_trace(go.Bar(
            x=scenarios,
            y=benefits,
            marker_color=[self.colors['before'], self.colors['primary'], self.colors['after']],
            name='Annual Benefits'
        ), row=1, col=1)

        # 2. Time Savings Breakdown
        time_savings = econ['time_savings_per_trip_minutes']
        # Estimate original travel time from statistical data
        if 'statistical' in self.results:
            original_time = 17.7 / self.results['statistical']['before_mean_speed'] * 60  # minutes
        else:
            original_time = time_savings * 5  # Rough estimate

        fig.add_trace(go.Pie(
            labels=['Time Savings', 'Remaining Travel Time'],
            values=[time_savings, max(0, original_time - time_savings)],
            marker_colors=[self.colors['primary'], self.colors['neutral']],
            name='Time Breakdown'
        ), row=1, col=2)

        # 3. Confidence Intervals
        ci_data = pd.DataFrame({
            'Metric': ['Economic Benefit', 'Time Savings'],
            'Lower': [econ['economic_benefit_ci_lower'], econ['time_savings_ci_lower']],
            'Upper': [econ['economic_benefit_ci_upper'], econ['time_savings_ci_upper']],
            'Point': [econ['primary_annual_benefit'], econ['time_savings_per_trip_minutes']]
        })

        for i, row in ci_data.iterrows():
            fig.add_trace(go.Scatter(
                x=[row['Metric']],
                y=[row['Point']],
                error_y=dict(
                    type='data',
                    symmetric=False,
                    arrayminus=[row['Point'] - row['Lower']],
                    array=[row['Upper'] - row['Point']]
                ),
                mode='markers',
                marker=dict(size=12, color=self.colors['primary']),
                name=f'{row["Metric"]} CI',
                showlegend=False
            ), row=2, col=1)

        # 4. Daily vs Annual Impact
        daily_benefit = econ['primary_annual_benefit'] / 365
        fig.add_trace(go.Bar(
            x=['Daily Benefit', 'Annual Benefit'],
            y=[daily_benefit, econ['primary_annual_benefit']],
            marker_color=[self.colors['secondary'], self.colors['primary']],
            name='Impact Scale'
        ), row=2, col=2)

        # Update layout
        fig.update_layout(
            title=dict(
                text=f'Economic Impact: ${econ["primary_annual_benefit"]/1e6:.1f}M Annual Benefit',
                font=dict(size=20, color='#2C3E50'),
                x=0.5
            ),
            height=1000,
            font=dict(family="Arial", size=12),
            template="plotly_white"
        )

        # Save
        interactive_path = os.path.join(self.figures_dir, "interactive", "economic_impact.html")
        fig.write_html(interactive_path)
        print(f"✅ Economic visualization: {interactive_path}")

    def create_behavioral_analysis_viz(self):
        """Create behavioral analysis visualizations"""
        print(f"\n🚗 CREATING BEHAVIORAL ANALYSIS VISUALIZATIONS")

        if 'hard_events' not in self.results:
            print("⚠️  No behavioral event data available")
            return

        events = self.results['hard_events']

        # Create behavioral analysis dashboard
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Hard Events by Type and Period',
                'Event Severity Distribution',
                'Temporal Pattern of Events',
                'Geographic Distribution of Events'
            ),
            specs=[
                [{"type": "bar"}, {"type": "box"}],
                [{"type": "scatter"}, {"type": "scatter"}]
            ]
        )

        # 1. Events by Type and Period
        event_summary = events.groupby(['event_type', 'period']).size().unstack(fill_value=0)

        for period in event_summary.columns:
            fig.add_trace(go.Bar(
                x=event_summary.index,
                y=event_summary[period],
                name=f'{period.title()} Period',
                marker_color=self.colors['before'] if period == 'before' else self.colors['after']
            ), row=1, col=1)

        # 2. Event Severity Distribution
        for period in events['period'].unique():
            period_data = events[events['period'] == period]
            fig.add_trace(go.Box(
                y=period_data['severity'],
                name=f'{period.title()} Severity',
                marker_color=self.colors['before'] if period == 'before' else self.colors['after']
            ), row=1, col=2)

        # 3. Temporal Pattern
        events['timestamp'] = pd.to_datetime(events['timestamp'])
        events['hour'] = events['timestamp'].dt.hour
        hourly_counts = events.groupby(['hour', 'period']).size().unstack(fill_value=0)

        for period in hourly_counts.columns:
            fig.add_trace(go.Scatter(
                x=hourly_counts.index,
                y=hourly_counts[period],
                mode='lines+markers',
                name=f'{period.title()} Hourly',
                line=dict(color=self.colors['before'] if period == 'before' else self.colors['after'])
            ), row=2, col=1)

        # 4. Geographic Distribution
        fig.add_trace(go.Scatter(
            x=events['longitude'],
            y=events['latitude'],
            mode='markers',
            marker=dict(
                color=[self.colors['before'] if p == 'before' else self.colors['after']
                      for p in events['period']],
                size=events['severity']*3,
                opacity=0.6
            ),
            name='Event Locations'
        ), row=2, col=2)

        # Update layout
        fig.update_layout(
            title=dict(
                text='Driving Behavior Analysis: Safety Events Before/After',
                font=dict(size=18, color='#2C3E50'),
                x=0.5
            ),
            height=1000,
            font=dict(family="Arial", size=12),
            template="plotly_white"
        )

        # Save
        interactive_path = os.path.join(self.figures_dir, "interactive", "behavioral_analysis.html")
        fig.write_html(interactive_path)
        print(f"✅ Behavioral visualization: {interactive_path}")

    def create_corridor_risk_map(self):
        """Create interactive corridor risk map"""
        print(f"\n🗺️  CREATING INTERACTIVE CORRIDOR RISK MAP")

        # Create base map centered on Christchurch
        center_lat = -43.532
        center_lon = 172.636

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=11,
            tiles='OpenStreetMap'
        )

        # Add SH1/SH76 corridor highlight
        corridor_coords = [
            [-43.45, 172.50],
            [-43.50, 172.55],
            [-43.55, 172.60],
            [-43.60, 172.65]
        ]

        folium.PolyLine(
            corridor_coords,
            color='blue',
            weight=5,
            opacity=0.8,
            popup='SH1/SH76 Study Corridor'
        ).add_to(m)

        # Add behavioral events if available
        if 'hard_events' in self.results:
            events = self.results['hard_events']

            # Create event clusters
            marker_cluster = plugins.MarkerCluster().add_to(m)

            for idx, event in events.iterrows():
                if pd.notna(event['latitude']) and pd.notna(event['longitude']):
                    color = 'red' if event['period'] == 'before' else 'blue'

                    folium.CircleMarker(
                        [event['latitude'], event['longitude']],
                        radius=event['severity'] * 2,
                        popup=f"{event['event_type'].title()}<br>"
                              f"Period: {event['period'].title()}<br>"
                              f"Severity: {event['severity']:.2f}<br>"
                              f"Speed: {event['speed_kmh']:.1f} km/h",
                        color=color,
                        fillColor=color,
                        fillOpacity=0.6
                    ).add_to(marker_cluster)

        # Add legend
        legend_html = '''
        <div style="position: fixed;
                    bottom: 50px; left: 50px; width: 150px; height: 90px;
                    background-color: white; border:2px solid grey; z-index:9999;
                    font-size:14px; padding: 10px">
        <p><b>Legend</b></p>
        <p><i class="fa fa-circle" style="color:red"></i> Before Period</p>
        <p><i class="fa fa-circle" style="color:blue"></i> After Period</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))

        # Save map
        map_path = os.path.join(self.figures_dir, "interactive", "corridor_risk_map.html")
        m.save(map_path)
        print(f"✅ Interactive map: {map_path}")

    def create_executive_summary_viz(self):
        """Create executive summary visualization"""
        print(f"\n📋 CREATING EXECUTIVE SUMMARY VISUALIZATION")

        if 'statistical' not in self.results or 'economic' not in self.results:
            print("❌ Missing required data for executive summary")
            return

        stats = self.results['statistical']
        econ = self.results['economic']

        # Create executive summary figure
        fig = make_subplots(
            rows=1, cols=4,
            subplot_titles=(
                'Speed Increase',
                'Time Savings',
                'Economic Benefit',
                'Statistical Confidence'
            ),
            specs=[[{"type": "indicator"}, {"type": "indicator"},
                   {"type": "indicator"}, {"type": "indicator"}]]
        )

        # 1. Speed Increase Indicator
        fig.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=stats['speed_increase_kmh'],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Speed Increase (km/h)"},
            delta={'reference': 0},
            gauge={
                'axis': {'range': [None, 20]},
                'bar': {'color': self.colors['primary']},
                'steps': [
                    {'range': [0, 5], 'color': "lightgray"},
                    {'range': [5, 15], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 10
                }
            }
        ), row=1, col=1)

        # 2. Time Savings Indicator
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=econ['time_savings_per_trip_minutes'],
            title={'text': "Time Savings<br>(minutes per trip)"},
            number={'font': {'size': 40}},
            delta={'reference': 0, 'valueformat': '.2f'}
        ), row=1, col=2)

        # 3. Economic Benefit Indicator
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=econ['primary_annual_benefit']/1e6,
            title={'text': "Annual Benefit<br>(Million NZD)"},
            number={'font': {'size': 40}, 'prefix': "$", 'suffix': "M"},
            delta={'reference': 0}
        ), row=1, col=3)

        # 4. Statistical Confidence
        confidence_score = 95 if stats['statistically_significant'] else 50
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=confidence_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Statistical<br>Confidence (%)"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': self.colors['success']},
                'steps': [
                    {'range': [0, 90], 'color': "lightgray"},
                    {'range': [90, 100], 'color': self.colors['success']}
                ]
            }
        ), row=1, col=4)

        fig.update_layout(
            title=dict(
                text='SH1/SH76 Speed Limit Analysis: Executive Summary',
                font=dict(size=24, color='#2C3E50'),
                x=0.5
            ),
            height=600,
            font=dict(family="Arial", size=14)
        )

        # Save
        executive_path = os.path.join(self.figures_dir, "interactive", "executive_summary.html")
        fig.write_html(executive_path)
        print(f"✅ Executive summary: {executive_path}")

        static_path = os.path.join(self.figures_dir, "static", "executive_summary.png")
        fig.write_image(static_path, width=1400, height=600, scale=2)
        print(f"✅ Static summary: {static_path}")

def main():
    viz_suite = AnalysisVisualizationSuite()

    # Load all results
    viz_suite.load_analysis_results()

    # Create visualizations
    viz_suite.create_statistical_dashboard()
    viz_suite.create_economic_impact_visualization()
    viz_suite.create_behavioral_analysis_viz()
    viz_suite.create_corridor_risk_map()
    viz_suite.create_executive_summary_viz()

    print(f"\n✅ COMPREHENSIVE VISUALIZATION SUITE COMPLETE")
    print(f"High-quality interactive and static visualizations created")
    print(f"📁 Output location: {viz_suite.figures_dir}")

if __name__ == "__main__":
    main()
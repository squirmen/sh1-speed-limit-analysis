"""
Comprehensive Behavioral Events Analysis Dashboard
Creates detailed visualizations of driving behavior patterns
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
from datetime import datetime

class BehavioralEventsDashboard:
    def __init__(self):
        self.base_dir = "/Volumes/T7/Data/connected_vehicle_data"
        self.reports_dir = os.path.join(self.base_dir, "output", "reports")
        self.figures_dir = os.path.join(self.base_dir, "output", "figures")

        print("📊 CREATING BEHAVIORAL EVENTS ANALYSIS DASHBOARD")
        print("=" * 55)

        # Define color palette
        self.colors = {
            'before': '#2E86AB',
            'after': '#A23B72',
            'harsh_braking': '#E63946',
            'harsh_steering': '#F77F00',
            'harsh_acceleration': '#FCBF49',
            'high_gforce': '#6A994E',
            'near_miss': '#FF6B35'
        }

    def load_behavioral_events(self):
        """Load and process behavioral events data"""

        events_path = os.path.join(self.reports_dir, "hard_driving_events.csv")

        if not os.path.exists(events_path):
            print("⚠️  No behavioral events data found")
            return None

        print(f"📂 Loading behavioral events: {events_path}")

        events = pd.read_csv(events_path)

        # Add period classification
        events['timestamp'] = pd.to_datetime(events['timestamp'])
        cutoff_date = pd.to_datetime('2025-04-13')
        events['period'] = events['timestamp'].apply(
            lambda x: 'before' if x < cutoff_date else 'after'
        )

        print(f"✅ Loaded {len(events)} behavioral events")
        print(f"Event types: {events['event_type'].value_counts().to_dict()}")
        print(f"Period distribution: {events['period'].value_counts().to_dict()}")

        return events

    def create_behavioral_overview(self, events):
        """Create overview of behavioral events"""

        # Event counts by type and period
        event_summary = events.groupby(['event_type', 'period']).size().unstack(fill_value=0)

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'Event Counts by Type and Period',
                'Event Severity Distribution',
                'Events by Hour of Day',
                'Speed Distribution During Events'
            ],
            specs=[[{"type": "bar"}, {"type": "histogram"}],
                   [{"type": "bar"}, {"type": "histogram"}]]
        )

        # 1. Event counts by type
        for period in ['before', 'after']:
            if period in event_summary.columns:
                fig.add_trace(
                    go.Bar(
                        name=f'{period.title()} Speed Change',
                        x=event_summary.index,
                        y=event_summary[period],
                        marker_color=self.colors[period],
                        showlegend=True
                    ), row=1, col=1
                )

        # 2. Severity distribution
        fig.add_trace(
            go.Histogram(
                x=events['severity'],
                name='Severity',
                marker_color='rgba(46, 134, 171, 0.7)',
                nbinsx=20,
                showlegend=False
            ), row=1, col=2
        )

        # 3. Events by hour
        events['hour'] = events['timestamp'].dt.hour
        hourly_counts = events.groupby('hour').size()

        fig.add_trace(
            go.Bar(
                x=hourly_counts.index,
                y=hourly_counts.values,
                name='Events by Hour',
                marker_color='rgba(247, 127, 0, 0.7)',
                showlegend=False
            ), row=2, col=1
        )

        # 4. Speed distribution
        fig.add_trace(
            go.Histogram(
                x=events['derived_speed'],
                name='Speed (km/h)',
                marker_color='rgba(106, 153, 78, 0.7)',
                nbinsx=25,
                showlegend=False
            ), row=2, col=2
        )

        fig.update_layout(
            title="SH1/SH76 Behavioral Events Analysis Overview",
            height=800,
            showlegend=True,
            template="plotly_white"
        )

        # Update axes labels
        fig.update_xaxes(title_text="Event Type", row=1, col=1)
        fig.update_yaxes(title_text="Event Count", row=1, col=1)
        fig.update_xaxes(title_text="Severity Score", row=1, col=2)
        fig.update_yaxes(title_text="Frequency", row=1, col=2)
        fig.update_xaxes(title_text="Hour of Day", row=2, col=1)
        fig.update_yaxes(title_text="Event Count", row=2, col=1)
        fig.update_xaxes(title_text="Speed (km/h)", row=2, col=2)
        fig.update_yaxes(title_text="Frequency", row=2, col=2)

        return fig

    def create_temporal_analysis(self, events):
        """Create temporal analysis of events"""

        # Daily event counts
        events['date'] = events['timestamp'].dt.date
        daily_counts = events.groupby(['date', 'period']).size().unstack(fill_value=0)

        fig = go.Figure()

        # Add before/after traces
        for period in ['before', 'after']:
            if period in daily_counts.columns:
                fig.add_trace(
                    go.Scatter(
                        x=daily_counts.index,
                        y=daily_counts[period],
                        mode='lines+markers',
                        name=f'{period.title()} Speed Change',
                        line=dict(color=self.colors[period], width=2),
                        marker=dict(size=4)
                    )
                )

        # Add vertical line for speed change
        cutoff_date = datetime(2025, 4, 13).date()
        fig.add_shape(
            type="line",
            x0=cutoff_date, x1=cutoff_date,
            y0=0, y1=1,
            yref="paper",
            line=dict(color="red", width=2, dash="dash")
        )
        fig.add_annotation(
            x=cutoff_date,
            y=0.9,
            yref="paper",
            text="Speed Limit Change<br>Apr 13, 2025",
            showarrow=False,
            bgcolor="white",
            bordercolor="red"
        )

        fig.update_layout(
            title="Daily Behavioral Events Over Time",
            xaxis_title="Date",
            yaxis_title="Daily Event Count",
            template="plotly_white",
            height=500
        )

        return fig

    def create_acceleration_analysis(self, events):
        """Create detailed acceleration analysis"""

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=['Longitudinal vs Lateral Acceleration', 'G-Force Distribution by Event Type']
        )

        # 1. Acceleration scatter plot
        for event_type in events['event_type'].unique():
            event_data = events[events['event_type'] == event_type]

            fig.add_trace(
                go.Scatter(
                    x=event_data['longitudinal_accel'],
                    y=event_data['lateral_accel'],
                    mode='markers',
                    name=event_type.replace('_', ' ').title(),
                    marker=dict(
                        color=self.colors.get(event_type, '#666666'),
                        size=6,
                        opacity=0.7
                    )
                ), row=1, col=1
            )

        # 2. G-force by event type
        fig.add_trace(
            go.Box(
                x=events['event_type'],
                y=events['total_gforce'],
                name='G-Force Distribution',
                marker_color='rgba(46, 134, 171, 0.7)',
                showlegend=False
            ), row=1, col=2
        )

        fig.update_layout(
            title="Acceleration and G-Force Analysis",
            height=500,
            template="plotly_white"
        )

        fig.update_xaxes(title_text="Longitudinal Accel (m/s²)", row=1, col=1)
        fig.update_yaxes(title_text="Lateral Accel (m/s²)", row=1, col=1)
        fig.update_xaxes(title_text="Event Type", row=1, col=2)
        fig.update_yaxes(title_text="Total G-Force", row=1, col=2)

        return fig

    def create_before_after_comparison(self, events):
        """Create before/after statistical comparison"""

        # Calculate statistics by period
        stats_by_period = events.groupby(['period', 'event_type']).agg({
            'severity': ['count', 'mean', 'std'],
            'derived_speed': 'mean',
            'total_gforce': 'mean'
        }).round(3)

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'Event Rates: Before vs After',
                'Average Severity: Before vs After',
                'Average Speed During Events',
                'Average G-Force During Events'
            ]
        )

        # Prepare data for comparison
        event_types = events['event_type'].unique()
        before_data = events[events['period'] == 'before']
        after_data = events[events['period'] == 'after']

        # 1. Event counts
        before_counts = before_data.groupby('event_type').size()
        after_counts = after_data.groupby('event_type').size()

        fig.add_trace(
            go.Bar(
                name='Before',
                x=event_types,
                y=[before_counts.get(et, 0) for et in event_types],
                marker_color=self.colors['before']
            ), row=1, col=1
        )

        fig.add_trace(
            go.Bar(
                name='After',
                x=event_types,
                y=[after_counts.get(et, 0) for et in event_types],
                marker_color=self.colors['after']
            ), row=1, col=1
        )

        # 2. Average severity
        before_severity = before_data.groupby('event_type')['severity'].mean()
        after_severity = after_data.groupby('event_type')['severity'].mean()

        fig.add_trace(
            go.Bar(
                name='Before (Severity)',
                x=event_types,
                y=[before_severity.get(et, 0) for et in event_types],
                marker_color=self.colors['before'],
                showlegend=False
            ), row=1, col=2
        )

        fig.add_trace(
            go.Bar(
                name='After (Severity)',
                x=event_types,
                y=[after_severity.get(et, 0) for et in event_types],
                marker_color=self.colors['after'],
                showlegend=False
            ), row=1, col=2
        )

        # 3. Average speed
        before_speed = before_data.groupby('event_type')['derived_speed'].mean()
        after_speed = after_data.groupby('event_type')['derived_speed'].mean()

        fig.add_trace(
            go.Bar(
                name='Before (Speed)',
                x=event_types,
                y=[before_speed.get(et, 0) for et in event_types],
                marker_color=self.colors['before'],
                showlegend=False
            ), row=2, col=1
        )

        fig.add_trace(
            go.Bar(
                name='After (Speed)',
                x=event_types,
                y=[after_speed.get(et, 0) for et in event_types],
                marker_color=self.colors['after'],
                showlegend=False
            ), row=2, col=1
        )

        # 4. Average G-force
        before_gforce = before_data.groupby('event_type')['total_gforce'].mean()
        after_gforce = after_data.groupby('event_type')['total_gforce'].mean()

        fig.add_trace(
            go.Bar(
                name='Before (G-Force)',
                x=event_types,
                y=[before_gforce.get(et, 0) for et in event_types],
                marker_color=self.colors['before'],
                showlegend=False
            ), row=2, col=2
        )

        fig.add_trace(
            go.Bar(
                name='After (G-Force)',
                x=event_types,
                y=[after_gforce.get(et, 0) for et in event_types],
                marker_color=self.colors['after'],
                showlegend=False
            ), row=2, col=2
        )

        fig.update_layout(
            title="Before vs After Speed Change: Behavioral Event Comparison",
            height=800,
            template="plotly_white"
        )

        return fig

    def save_dashboard(self):
        """Create and save the complete behavioral dashboard"""

        events = self.load_behavioral_events()

        if events is None or events.empty:
            print("❌ No behavioral events data available")
            return None

        # Create individual visualizations
        overview_fig = self.create_behavioral_overview(events)
        temporal_fig = self.create_temporal_analysis(events)
        acceleration_fig = self.create_acceleration_analysis(events)
        comparison_fig = self.create_before_after_comparison(events)

        # Save individual figures
        output_dir = os.path.join(self.figures_dir, "interactive")
        os.makedirs(output_dir, exist_ok=True)

        overview_path = os.path.join(output_dir, "behavioral_overview.html")
        temporal_path = os.path.join(output_dir, "behavioral_temporal.html")
        acceleration_path = os.path.join(output_dir, "behavioral_acceleration.html")
        comparison_path = os.path.join(output_dir, "behavioral_comparison.html")

        overview_fig.write_html(overview_path)
        temporal_fig.write_html(temporal_path)
        acceleration_fig.write_html(acceleration_path)
        comparison_fig.write_html(comparison_path)

        print(f"✅ Behavioral overview saved: {overview_path}")
        print(f"✅ Temporal analysis saved: {temporal_path}")
        print(f"✅ Acceleration analysis saved: {acceleration_path}")
        print(f"✅ Before/after comparison saved: {comparison_path}")

        # Generate summary statistics
        self.generate_behavioral_summary(events)

        return {
            'overview': overview_path,
            'temporal': temporal_path,
            'acceleration': acceleration_path,
            'comparison': comparison_path
        }

    def generate_behavioral_summary(self, events):
        """Generate summary statistics for behavioral events"""

        # Overall statistics
        total_events = len(events)
        before_events = len(events[events['period'] == 'before'])
        after_events = len(events[events['period'] == 'after'])

        # Event type breakdown
        event_type_summary = events.groupby(['event_type', 'period']).agg({
            'severity': ['count', 'mean', 'std'],
            'derived_speed': 'mean',
            'total_gforce': 'mean'
        }).round(3)

        summary_data = {
            'analysis_date': datetime.now().isoformat(),
            'total_events': total_events,
            'before_events': before_events,
            'after_events': after_events,
            'event_types': events['event_type'].value_counts().to_dict(),
            'avg_severity_before': events[events['period'] == 'before']['severity'].mean(),
            'avg_severity_after': events[events['period'] == 'after']['severity'].mean(),
            'avg_speed_during_events_before': events[events['period'] == 'before']['derived_speed'].mean(),
            'avg_speed_during_events_after': events[events['period'] == 'after']['derived_speed'].mean()
        }

        # Save detailed summary
        summary_path = os.path.join(self.reports_dir, "behavioral_events_summary.csv")

        summary_df = pd.DataFrame([summary_data])
        summary_df.to_csv(summary_path, index=False)

        print(f"✅ Behavioral summary saved: {summary_path}")
        print(f"📊 Total Events: {total_events}")
        print(f"📊 Before: {before_events}, After: {after_events}")

def main():
    dashboard = BehavioralEventsDashboard()
    dashboard.save_dashboard()

    print("\n✅ BEHAVIORAL EVENTS DASHBOARD COMPLETE")
    print("Comprehensive analysis of driving behavior patterns created")

if __name__ == "__main__":
    main()
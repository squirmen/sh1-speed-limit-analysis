"""
Behavioral Analysis Visualizations
==================================
Creates publication-quality visualizations of driving behavior changes

Author: Data Analysis Pipeline
Date: 2025-10-22
"""

import pandas as pd
import numpy as np
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class BehavioralVisualizer:
    """Create publication-quality visualizations of behavioral analysis"""

    def __init__(self):
        self.base_dir = Path("/Volumes/T7/Data/connected_vehicle_data")
        self.data_dir = self.base_dir / "output/analysis/behavioral"
        self.output_dir = self.base_dir / "output/figures/behavioral_analysis"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Professional color scheme
        self.colors = {
            'before': '#2E86AB',
            'after': '#A23B72',
            'decrease': '#06A77D',
            'increase': '#D84545'
        }

        print("=" * 80)
        print("BEHAVIORAL ANALYSIS - VISUALIZATION")
        print("=" * 80)

    def create_event_rates_comparison(self):
        """
        Figure 1: Event rates by period with change indicators
        """
        print("\n[1/4] Creating event rates comparison...")

        # Load data
        df = pd.read_csv(self.data_dir / "behavioral_by_period.csv")

        # Prepare data
        events = ['Hard Braking', 'Rapid Acceleration', 'Hard Steering']
        rate_cols = ['hard_brake_rate', 'rapid_accel_rate', 'hard_steer_rate']

        before = df[df['period'] == 'before'].iloc[0]
        after = df[df['period'] == 'after'].iloc[0]

        # Create figure with subplots
        fig = make_subplots(
            rows=1, cols=3,
            subplot_titles=events,
            horizontal_spacing=0.15
        )

        for idx, (event, rate_col) in enumerate(zip(events, rate_cols), 1):
            before_rate = before[rate_col]
            after_rate = after[rate_col]
            change = after_rate - before_rate
            color = self.colors['decrease'] if change < 0 else self.colors['increase']

            # Before bar
            fig.add_trace(
                go.Bar(
                    x=['Before'],
                    y=[before_rate],
                    name='Before' if idx == 1 else None,
                    marker_color=self.colors['before'],
                    showlegend=(idx == 1),
                    legendgroup='before',
                    text=f"{before_rate:.2f}",
                    textposition='outside',
                    hovertemplate=(
                        '<b>Before</b><br>' +
                        f'Rate: {before_rate:.2f} per 1000<br>' +
                        '<extra></extra>'
                    )
                ),
                row=1, col=idx
            )

            # After bar
            fig.add_trace(
                go.Bar(
                    x=['After'],
                    y=[after_rate],
                    name='After' if idx == 1 else None,
                    marker_color=self.colors['after'],
                    showlegend=(idx == 1),
                    legendgroup='after',
                    text=f"{after_rate:.2f}",
                    textposition='outside',
                    hovertemplate=(
                        '<b>After</b><br>' +
                        f'Rate: {after_rate:.2f} per 1000<br>' +
                        '<extra></extra>'
                    )
                ),
                row=1, col=idx
            )

            # Add change annotation
            fig.add_annotation(
                text=f"Change: {change:+.2f}<br>({'↓' if change < 0 else '↑'})",
                xref=f"x{idx}", yref=f"y{idx}",
                x=0.5, y=max(before_rate, after_rate) * 1.2,
                showarrow=False,
                font=dict(size=11, color=color),
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor=color,
                borderwidth=2
            )

        # Update layout
        fig.update_layout(
            title={
                'text': 'Driving Behavior Event Rates<br><sub>Per 1,000 GPS Point Transitions</sub>',
                'x': 0.5,
                'xanchor': 'center'
            },
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            font=dict(size=12),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        # Update axes
        for i in range(1, 4):
            fig.update_yaxes(
                title_text="Events per 1000" if i == 1 else "",
                gridcolor='lightgray',
                row=1, col=i
            )
            fig.update_xaxes(
                showticklabels=True,
                row=1, col=i
            )

        # Save
        output_path = self.output_dir / "event_rates_comparison.html"
        fig.write_html(output_path)
        print(f"   ✅ Saved: {output_path}")

        return fig

    def create_vehicle_type_comparison(self):
        """
        Figure 2: Behavioral changes by vehicle type
        """
        print("\n[2/4] Creating vehicle type comparison...")

        # Load data
        df = pd.read_csv(self.data_dir / "behavioral_by_vehicle_type.csv")

        # Calculate changes
        results = []
        for vehicle_type in ['LCV', 'CAR', 'HCV']:
            veh_data = df[df['vehicle_type'] == vehicle_type]

            if len(veh_data) < 2:
                continue

            before = veh_data[veh_data['period'] == 'before'].iloc[0]
            after = veh_data[veh_data['period'] == 'after'].iloc[0]

            results.append({
                'vehicle_type': vehicle_type,
                'hard_brake_change': after['hard_brake_rate'] - before['hard_brake_rate'],
                'rapid_accel_change': after['rapid_accel_rate'] - before['rapid_accel_rate'],
                'hard_steer_change': after['hard_steer_rate'] - before['hard_steer_rate']
            })

        df_changes = pd.DataFrame(results)

        # Create figure
        fig = go.Figure()

        # Hard braking
        fig.add_trace(go.Bar(
            name='Hard Braking',
            x=df_changes['vehicle_type'],
            y=df_changes['hard_brake_change'],
            marker_color='#E63946',
            text=[f"{x:+.2f}" for x in df_changes['hard_brake_change']],
            textposition='outside'
        ))

        # Rapid acceleration
        fig.add_trace(go.Bar(
            name='Rapid Acceleration',
            x=df_changes['vehicle_type'],
            y=df_changes['rapid_accel_change'],
            marker_color='#F77F00',
            text=[f"{x:+.2f}" for x in df_changes['rapid_accel_change']],
            textposition='outside'
        ))

        # Hard steering
        fig.add_trace(go.Bar(
            name='Hard Steering',
            x=df_changes['vehicle_type'],
            y=df_changes['hard_steer_change'],
            marker_color='#06A77D',
            text=[f"{x:+.2f}" for x in df_changes['hard_steer_change']],
            textposition='outside'
        ))

        # Update layout
        fig.update_layout(
            title={
                'text': 'Behavioral Change by Vehicle Type<br><sub>Change in Event Rate (After - Before)</sub>',
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title="Vehicle Type",
            yaxis_title="Change in Event Rate (per 1000)",
            barmode='group',
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            font=dict(size=12),
            plot_bgcolor='white',
            paper_bgcolor='white',
            yaxis=dict(
                gridcolor='lightgray',
                zeroline=True,
                zerolinecolor='black',
                zerolinewidth=2
            )
        )

        # Save
        output_path = self.output_dir / "vehicle_type_comparison.html"
        fig.write_html(output_path)
        print(f"   ✅ Saved: {output_path}")

        return fig

    def create_acceleration_distribution(self):
        """
        Figure 3: Acceleration distribution comparison
        Load from raw acceleration data
        """
        print("\n[3/4] Creating acceleration distribution...")

        # Load period comparison data
        df = pd.read_csv(self.data_dir / "behavioral_by_period.csv")

        # Create figure showing acceleration stats
        fig = go.Figure()

        periods = ['before', 'after']
        colors = [self.colors['before'], self.colors['after']]

        for period, color in zip(periods, colors):
            row = df[df['period'] == period].iloc[0]

            # Create box plot using stats
            fig.add_trace(go.Box(
                name=period.capitalize(),
                marker_color=color,
                boxmean='sd',
                # Use stats to approximate distribution
                y=[row['accel_mean']],  # Will create single point
                text=f"Mean: {row['accel_mean']:.3f} m/s²<br>Std: {row['accel_std']:.3f} m/s²",
                hoverinfo='text'
            ))

        # Create bar chart instead (clearer)
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=['Mean Acceleration', 'Acceleration Std Dev', 'Mean Abs Acceleration'],
            y=[df[df['period'] == 'before']['accel_mean'].iloc[0],
               df[df['period'] == 'before']['accel_std'].iloc[0],
               df[df['period'] == 'before']['accel_abs_mean'].iloc[0]],
            name='Before',
            marker_color=self.colors['before'],
            text=[f"{x:.3f}" for x in [
                df[df['period'] == 'before']['accel_mean'].iloc[0],
                df[df['period'] == 'before']['accel_std'].iloc[0],
                df[df['period'] == 'before']['accel_abs_mean'].iloc[0]
            ]],
            textposition='outside'
        ))

        fig.add_trace(go.Bar(
            x=['Mean Acceleration', 'Acceleration Std Dev', 'Mean Abs Acceleration'],
            y=[df[df['period'] == 'after']['accel_mean'].iloc[0],
               df[df['period'] == 'after']['accel_std'].iloc[0],
               df[df['period'] == 'after']['accel_abs_mean'].iloc[0]],
            name='After',
            marker_color=self.colors['after'],
            text=[f"{x:.3f}" for x in [
                df[df['period'] == 'after']['accel_mean'].iloc[0],
                df[df['period'] == 'after']['accel_std'].iloc[0],
                df[df['period'] == 'after']['accel_abs_mean'].iloc[0]
            ]],
            textposition='outside'
        ))

        # Update layout
        fig.update_layout(
            title={
                'text': 'Acceleration Pattern Comparison<br><sub>Mean and Variability of Acceleration</sub>',
                'x': 0.5,
                'xanchor': 'center'
            },
            yaxis_title="Acceleration (m/s²)",
            barmode='group',
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            font=dict(size=12),
            plot_bgcolor='white',
            paper_bgcolor='white',
            yaxis=dict(
                gridcolor='lightgray'
            )
        )

        # Save
        output_path = self.output_dir / "acceleration_distribution.html"
        fig.write_html(output_path)
        print(f"   ✅ Saved: {output_path}")

        return fig

    def create_variability_summary(self):
        """
        Figure 4: Speed variability summary
        """
        print("\n[4/4] Creating speed variability summary...")

        # Load data
        df = pd.read_csv(self.data_dir / "speed_variability.csv")

        before = df[df['period'] == 'before'].iloc[0]
        after = df[df['period'] == 'after'].iloc[0]

        # Create figure with 2x2 subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['Speed Standard Deviation',
                           'Speed Range',
                           'Coefficient of Variation',
                           'Mean Absolute Acceleration'],
            vertical_spacing=0.15,
            horizontal_spacing=0.15
        )

        metrics = [
            ('speed_std_mean', 'km/h', 1, 1),
            ('speed_range_mean', 'km/h', 1, 2),
            ('speed_cv_mean', '', 2, 1),
            ('accel_abs_mean', 'm/s²', 2, 2)
        ]

        for metric, unit, row, col in metrics:
            before_val = before[metric]
            after_val = after[metric]
            change = after_val - before_val
            change_pct = (change / before_val * 100) if before_val != 0 else 0

            fig.add_trace(
                go.Bar(
                    x=['Before', 'After'],
                    y=[before_val, after_val],
                    marker_color=[self.colors['before'], self.colors['after']],
                    text=[f"{before_val:.3f}", f"{after_val:.3f}"],
                    textposition='outside',
                    showlegend=False,
                    hovertemplate=(
                        '<b>%{x}</b><br>' +
                        f'Value: %{{y:.3f}} {unit}<br>' +
                        '<extra></extra>'
                    )
                ),
                row=row, col=col
            )

            # Add change annotation
            color = self.colors['decrease'] if change < 0 else self.colors['increase']
            fig.add_annotation(
                text=f"{change:+.3f} {unit}<br>({change_pct:+.1f}%)",
                xref=f"x{(row-1)*2 + col}", yref=f"y{(row-1)*2 + col}",
                x=0.5, y=max(before_val, after_val) * 1.15,
                showarrow=False,
                font=dict(size=10, color=color),
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor=color,
                borderwidth=1
            )

        # Update layout
        fig.update_layout(
            title={
                'text': 'Speed Variability Comparison<br><sub>Trip-Level Metrics</sub>',
                'x': 0.5,
                'xanchor': 'center'
            },
            height=700,
            font=dict(size=11),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        # Update axes
        for i in range(1, 5):
            fig.update_yaxes(gridcolor='lightgray', row=(i-1)//2+1, col=(i-1)%2+1)

        # Save
        output_path = self.output_dir / "variability_summary.html"
        fig.write_html(output_path)
        print(f"   ✅ Saved: {output_path}")

        return fig

    def generate_all_figures(self):
        """Generate all visualization figures"""
        print("\nGenerating behavioral visualizations...")
        print("-" * 80)

        self.create_event_rates_comparison()
        self.create_vehicle_type_comparison()
        self.create_acceleration_distribution()
        self.create_variability_summary()

        print("\n" + "=" * 80)
        print("BEHAVIORAL VISUALIZATION COMPLETE")
        print("=" * 80)
        print(f"Output directory: {self.output_dir}")
        print("\nGenerated figures:")
        print("  1. event_rates_comparison.html - Event rates before/after")
        print("  2. vehicle_type_comparison.html - Changes by vehicle type")
        print("  3. acceleration_distribution.html - Acceleration patterns")
        print("  4. variability_summary.html - Speed variability metrics")
        print("\nAll figures are interactive (hover for details, zoom, pan)")
        print("=" * 80)


if __name__ == "__main__":
    visualizer = BehavioralVisualizer()
    visualizer.generate_all_figures()

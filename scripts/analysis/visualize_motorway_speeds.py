"""
Motorway Speed Analysis - Publication Quality Visualizations
=============================================================
Creates clear, methodologically robust visualizations of speed limit change impact

Author: Data Analysis Pipeline
Date: 2025-10-22
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

# Import plotly for interactive, publication-quality graphics
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

class MotorwaySpeedVisualizer:
    """Create publication-quality visualizations of motorway speed analysis"""

    def __init__(self):
        self.base_dir = Path("/Volumes/T7/Data/connected_vehicle_data")
        self.data_path = self.base_dir / "output/processed_data/motorway_only/motorway_trips.parquet"
        self.output_dir = self.base_dir / "output/figures/motorway_analysis"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Professional color scheme (neutral, colorblind-friendly)
        self.colors = {
            'before': '#2E86AB',  # Blue
            'after': '#A23B72',   # Magenta
            'light': '#F18F01',   # Orange
            'heavy': '#6A4C93'    # Purple
        }

        print("=" * 80)
        print("MOTORWAY SPEED ANALYSIS - VISUALIZATION")
        print("=" * 80)

    def load_data(self):
        """Load motorway trips data"""
        print("\nLoading motorway trips data...")

        df = pd.read_parquet(self.data_path)

        # Load original trip data to get VehicleType
        trips_path = self.base_dir / "output/processed_data/trip_level/corridor_trips.parquet"
        df_trips = pd.read_parquet(trips_path, columns=['TripID', 'VehicleType'])

        # Merge to get vehicle types
        df = df.merge(df_trips, on='TripID', how='left')

        print(f"   Total trips: {len(df):,}")
        print(f"   BEFORE: {len(df[df['period']=='before']):,}")
        print(f"   AFTER: {len(df[df['period']=='after']):,}")
        print(f"   Vehicle types: {df['VehicleType'].value_counts().to_dict()}")

        self.df = df
        return df

    def create_speed_distribution_by_vehicle(self):
        """
        Figure 1: Speed distributions by vehicle type (before vs after)
        Box plots showing median, quartiles, and sample sizes
        """
        print("\n[1/4] Creating speed distribution by vehicle type...")

        # Prepare data
        vehicle_order = ['LCV', 'CAR', 'HCV']  # Light to heavy
        vehicle_labels = {
            'LCV': 'Light Commercial',
            'CAR': 'Passenger',
            'HCV': 'Heavy Commercial'
        }

        fig = make_subplots(
            rows=1, cols=3,
            subplot_titles=['Light Commercial', 'Passenger', 'Heavy Commercial'],
            horizontal_spacing=0.12
        )

        for idx, vehicle_type in enumerate(vehicle_order, 1):
            vehicle_data = self.df[self.df['VehicleType'] == vehicle_type]

            for period, color in [('before', self.colors['before']), ('after', self.colors['after'])]:
                period_data = vehicle_data[vehicle_data['period'] == period]['avg_speed']

                fig.add_trace(
                    go.Box(
                        y=period_data,
                        name=period.capitalize(),
                        marker_color=color,
                        boxmean='sd',  # Show mean and standard deviation
                        showlegend=(idx == 1),  # Only show legend once
                        legendgroup=period,
                        hovertemplate=(
                            f'<b>{period.capitalize()}</b><br>' +
                            'Speed: %{y:.1f} km/h<br>' +
                            f'n={len(period_data)}<br>' +
                            '<extra></extra>'
                        )
                    ),
                    row=1, col=idx
                )

            # Add sample size annotations
            before_n = len(vehicle_data[vehicle_data['period'] == 'before'])
            after_n = len(vehicle_data[vehicle_data['period'] == 'after'])

            fig.add_annotation(
                text=f"n={before_n}, {after_n}",
                xref=f"x{idx}", yref=f"y{idx}",
                x=0.5, y=1.02,
                xanchor='center', yanchor='bottom',
                showarrow=False,
                font=dict(size=10, color='gray')
            )

        # Update layout
        fig.update_layout(
            title={
                'text': 'Motorway Speed Distributions by Vehicle Type<br><sub>Before and After Speed Limit Change (April 13, 2025)</sub>',
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
                title_text="Average Speed (km/h)" if i == 1 else "",
                gridcolor='lightgray',
                range=[40, 100],
                row=1, col=i
            )
            fig.update_xaxes(
                showticklabels=False,
                row=1, col=i
            )

        # Save
        output_path = self.output_dir / "speed_by_vehicle_type.html"
        fig.write_html(output_path)
        print(f"   ✅ Saved: {output_path}")

        return fig

    def create_speed_change_summary(self):
        """
        Figure 2: Summary of speed changes with confidence intervals
        Shows mean change and 85th percentile for each vehicle type
        """
        print("\n[2/4] Creating speed change summary...")

        # Calculate statistics
        results = []
        vehicle_order = ['LCV', 'CAR', 'HCV']

        for vehicle_type in vehicle_order:
            vehicle_data = self.df[self.df['VehicleType'] == vehicle_type]

            before = vehicle_data[vehicle_data['period'] == 'before']['avg_speed']
            after = vehicle_data[vehicle_data['period'] == 'after']['avg_speed']

            if len(before) > 0 and len(after) > 0:
                # Mean change
                mean_before = before.mean()
                mean_after = after.mean()
                mean_change = mean_after - mean_before

                # Standard errors
                se_before = before.std() / np.sqrt(len(before))
                se_after = after.std() / np.sqrt(len(after))
                se_change = np.sqrt(se_before**2 + se_after**2)

                # 85th percentile change
                p85_before = before.quantile(0.85)
                p85_after = after.quantile(0.85)
                p85_change = p85_after - p85_before

                results.append({
                    'vehicle_type': vehicle_type,
                    'mean_change': mean_change,
                    'se_change': se_change,
                    'p85_change': p85_change,
                    'n_before': len(before),
                    'n_after': len(after)
                })

        df_results = pd.DataFrame(results)

        # Create figure
        fig = go.Figure()

        # Mean change with error bars
        fig.add_trace(go.Bar(
            x=df_results['vehicle_type'],
            y=df_results['mean_change'],
            error_y=dict(
                type='data',
                array=df_results['se_change'] * 1.96,  # 95% CI
                visible=True
            ),
            marker_color=self.colors['light'],
            name='Mean Change',
            text=[f"+{x:.2f} km/h" for x in df_results['mean_change']],
            textposition='outside',
            hovertemplate=(
                '<b>%{x}</b><br>' +
                'Mean change: +%{y:.2f} km/h<br>' +
                '95% CI: ±%{error_y.array:.2f} km/h<br>' +
                '<extra></extra>'
            )
        ))

        # 85th percentile change
        fig.add_trace(go.Scatter(
            x=df_results['vehicle_type'],
            y=df_results['p85_change'],
            mode='markers',
            marker=dict(
                size=12,
                color=self.colors['heavy'],
                symbol='diamond',
                line=dict(width=2, color='white')
            ),
            name='85th Percentile Change',
            hovertemplate=(
                '<b>%{x}</b><br>' +
                '85th percentile change: +%{y:.2f} km/h<br>' +
                '<extra></extra>'
            )
        ))

        # Update layout
        fig.update_layout(
            title={
                'text': 'Speed Change by Vehicle Type<br><sub>Mean and 85th Percentile (Free-Flow Conditions)</sub>',
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title="Vehicle Type",
            yaxis_title="Speed Change (km/h)",
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
                range=[0, max(df_results['mean_change']) + 2]
            )
        )

        # Add sample size annotation
        annotations_text = "<br>".join([
            f"{row['vehicle_type']}: n={row['n_before']}, {row['n_after']}"
            for _, row in df_results.iterrows()
        ])

        fig.add_annotation(
            text=annotations_text,
            xref="paper", yref="paper",
            x=1.02, y=0.5,
            xanchor='left', yanchor='middle',
            showarrow=False,
            font=dict(size=10, color='gray'),
            align='left'
        )

        # Save
        output_path = self.output_dir / "speed_change_summary.html"
        fig.write_html(output_path)
        print(f"   ✅ Saved: {output_path}")

        return fig

    def create_overall_comparison(self):
        """
        Figure 3: Overall before/after comparison
        Shows all data combined with vehicle mix annotation
        """
        print("\n[3/4] Creating overall comparison...")

        fig = go.Figure()

        # Before distribution
        before_data = self.df[self.df['period'] == 'before']['avg_speed']
        fig.add_trace(go.Violin(
            y=before_data,
            name='Before',
            box_visible=True,
            meanline_visible=True,
            fillcolor=self.colors['before'],
            opacity=0.6,
            x0='Before',
            hovertemplate=(
                '<b>Before</b><br>' +
                'Speed: %{y:.1f} km/h<br>' +
                f'n={len(before_data)}<br>' +
                '<extra></extra>'
            )
        ))

        # After distribution
        after_data = self.df[self.df['period'] == 'after']['avg_speed']
        fig.add_trace(go.Violin(
            y=after_data,
            name='After',
            box_visible=True,
            meanline_visible=True,
            fillcolor=self.colors['after'],
            opacity=0.6,
            x0='After',
            hovertemplate=(
                '<b>After</b><br>' +
                'Speed: %{y:.1f} km/h<br>' +
                f'n={len(after_data)}<br>' +
                '<extra></extra>'
            )
        ))

        # Calculate statistics
        mean_before = before_data.mean()
        mean_after = after_data.mean()
        change = mean_after - mean_before
        pct_change = (change / mean_before) * 100

        # Vehicle mix
        vehicle_mix = self.df.groupby('VehicleType').size()
        vehicle_pct = (vehicle_mix / len(self.df) * 100).to_dict()

        # Update layout
        fig.update_layout(
            title={
                'text': 'Overall Motorway Speed Distribution<br><sub>All Vehicle Types Combined</sub>',
                'x': 0.5,
                'xanchor': 'center'
            },
            yaxis_title="Average Speed (km/h)",
            height=600,
            showlegend=False,
            font=dict(size=12),
            plot_bgcolor='white',
            paper_bgcolor='white',
            yaxis=dict(
                gridcolor='lightgray',
                range=[40, 100]
            )
        )

        # Add statistics annotations
        stats_text = (
            f"<b>Summary Statistics</b><br>"
            f"BEFORE: {mean_before:.2f} km/h (n={len(before_data)})<br>"
            f"AFTER: {mean_after:.2f} km/h (n={len(after_data)})<br>"
            f"CHANGE: +{change:.2f} km/h (+{pct_change:.1f}%)<br>"
            f"<br><b>Vehicle Mix</b><br>"
        )

        for vtype, pct in sorted(vehicle_pct.items()):
            stats_text += f"{vtype}: {pct:.1f}%<br>"

        fig.add_annotation(
            text=stats_text,
            xref="paper", yref="paper",
            x=1.02, y=0.5,
            xanchor='left', yanchor='middle',
            showarrow=False,
            font=dict(size=11),
            align='left',
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='gray',
            borderwidth=1
        )

        # Save
        output_path = self.output_dir / "overall_comparison.html"
        fig.write_html(output_path)
        print(f"   ✅ Saved: {output_path}")

        return fig

    def create_methodology_summary(self):
        """
        Figure 4: Methodology and data summary
        Visual summary of the spatial filtering process
        """
        print("\n[4/4] Creating methodology summary...")

        # Load processing statistics
        stats = {
            'total_trips': len(self.df),
            'before_trips': len(self.df[self.df['period'] == 'before']),
            'after_trips': len(self.df[self.df['period'] == 'after']),
            'vehicle_types': self.df['VehicleType'].value_counts().to_dict()
        }

        # Create figure with text summary
        fig = go.Figure()

        # Add invisible scatter to set up axes
        fig.add_trace(go.Scatter(
            x=[0, 10],
            y=[0, 10],
            mode='markers',
            marker=dict(size=0.1, color='white'),
            showlegend=False,
            hoverinfo='skip'
        ))

        # Add methodology text
        methodology_text = (
            "<b>METHODOLOGY SUMMARY</b><br>"
            "<br>"
            "<b>Data Source:</b><br>"
            "• Connected vehicle GPS data (11.4M points)<br>"
            "• SH1 Christchurch corridor (Addison to Rollston)<br>"
            "• January - May 2025<br>"
            "<br>"
            "<b>Spatial Filtering:</b><br>"
            "• 50m buffer from motorway centerline<br>"
            "• Perpendicular distance calculation to line segments<br>"
            "• Trips with ≥50% of points on motorway<br>"
            f"• Resulted in {stats['total_trips']:,} motorway-only trips<br>"
            "<br>"
            "<b>Speed Limit Change:</b><br>"
            "• Date: April 13, 2025<br>"
            "• Light vehicles: 100 → 110 km/h<br>"
            "• Heavy vehicles: 90 km/h (no change)<br>"
            "<br>"
            "<b>Sample Composition:</b><br>"
            f"• BEFORE period: {stats['before_trips']:,} trips<br>"
            f"• AFTER period: {stats['after_trips']:,} trips<br>"
        )

        for vtype, count in sorted(stats['vehicle_types'].items()):
            pct = count / stats['total_trips'] * 100
            methodology_text += f"• {vtype}: {count:,} ({pct:.1f}%)<br>"

        fig.add_annotation(
            text=methodology_text,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=13, family='monospace'),
            align='left',
            bgcolor='rgba(240,240,240,0.9)',
            bordercolor='gray',
            borderwidth=2,
            borderpad=20
        )

        # Update layout
        fig.update_layout(
            title={
                'text': 'Study Methodology and Data Summary',
                'x': 0.5,
                'xanchor': 'center'
            },
            height=700,
            showlegend=False,
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        # Save
        output_path = self.output_dir / "methodology_summary.html"
        fig.write_html(output_path)
        print(f"   ✅ Saved: {output_path}")

        return fig

    def generate_all_figures(self):
        """Generate all visualization figures"""
        self.load_data()

        print("\nGenerating publication-quality visualizations...")
        print("-" * 80)

        self.create_speed_distribution_by_vehicle()
        self.create_speed_change_summary()
        self.create_overall_comparison()
        self.create_methodology_summary()

        print("\n" + "=" * 80)
        print("VISUALIZATION COMPLETE")
        print("=" * 80)
        print(f"Output directory: {self.output_dir}")
        print("\nGenerated figures:")
        print("  1. speed_by_vehicle_type.html - Box plots by vehicle type")
        print("  2. speed_change_summary.html - Speed change summary with CIs")
        print("  3. overall_comparison.html - Overall before/after comparison")
        print("  4. methodology_summary.html - Study methodology summary")
        print("\nAll figures are interactive (hover for details, zoom, pan)")
        print("=" * 80)


if __name__ == "__main__":
    visualizer = MotorwaySpeedVisualizer()
    visualizer.generate_all_figures()

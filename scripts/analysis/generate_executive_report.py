"""
Executive Report Generator - Speed Limit Change Impact Analysis
================================================================
Creates publication-quality 2-page PDF report with state-of-the-art visualizations

Design principles:
- Data-dense but readable
- Professional typography and color scheme
- Consistent visual language
- Publication-ready quality

Author: Data Analysis Pipeline
Date: 2025-10-22
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import matplotlib.patches as patches
from matplotlib import rcParams
import warnings
warnings.filterwarnings('ignore')

class ExecutiveReportGenerator:
    """Generate professional 2-page PDF report"""

    def __init__(self):
        self.base_dir = Path("/Volumes/T7/Data/connected_vehicle_data")
        self.output_dir = self.base_dir / "output/reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Professional color scheme (colorblind-friendly)
        self.colors = {
            'primary': '#1f77b4',      # Professional blue
            'secondary': '#ff7f0e',    # Orange
            'before': '#2E86AB',       # Blue
            'after': '#A23B72',        # Magenta
            'positive': '#06A77D',     # Green
            'negative': '#D84545',     # Red
            'warning': '#F77F00',      # Orange
            'neutral': '#6B7280',      # Gray
            'car': '#E63946',          # Red (problem vehicle)
            'lcv': '#F77F00',          # Orange
            'hcv': '#06A77D',          # Green
            'background': '#FFFFFF',
            'grid': '#E5E7EB',
            'text': '#1F2937'
        }

        # Professional typography
        rcParams['font.family'] = 'sans-serif'
        rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
        rcParams['font.size'] = 9
        rcParams['axes.labelsize'] = 9
        rcParams['axes.titlesize'] = 10
        rcParams['xtick.labelsize'] = 8
        rcParams['ytick.labelsize'] = 8
        rcParams['legend.fontsize'] = 8
        rcParams['figure.titlesize'] = 12

        print("=" * 80)
        print("EXECUTIVE REPORT GENERATOR")
        print("=" * 80)
        print("Creating publication-quality 2-page PDF report...")

    def load_all_data(self):
        """Load all analysis data"""
        print("\n📂 Loading analysis data...")

        # Speed analysis
        self.motorway_trips = pd.read_parquet(
            self.base_dir / "output/processed_data/motorway_only/motorway_trips.parquet"
        )

        # Merge with vehicle types
        trips_full = pd.read_parquet(
            self.base_dir / "output/processed_data/trip_level/corridor_trips.parquet",
            columns=['TripID', 'VehicleType']
        )
        self.motorway_trips = self.motorway_trips.merge(trips_full, on='TripID', how='left')

        # Behavioral analysis
        self.behavioral_period = pd.read_csv(
            self.base_dir / "output/analysis/behavioral/behavioral_by_period.csv"
        )
        self.behavioral_vehicle = pd.read_csv(
            self.base_dir / "output/analysis/behavioral/behavioral_by_vehicle_type.csv"
        )

        # Crash analysis
        self.crash_rates = pd.read_csv(
            self.base_dir / "output/analysis/crash_integration/crash_rates_by_period.csv"
        )
        self.crash_vehicle_correlation = pd.read_csv(
            self.base_dir / "output/analysis/vehicle_crash_correlation/behavior_crash_correlation.csv"
        )

        print("   ✅ All data loaded")

    def create_page1(self):
        """Create page 1: Overview, Speed Changes, Behavioral Patterns"""
        print("\n📄 Creating Page 1...")

        fig = plt.figure(figsize=(11, 8.5))  # Letter size
        fig.patch.set_facecolor(self.colors['background'])

        # Create grid layout
        gs = GridSpec(4, 3, figure=fig, hspace=0.4, wspace=0.35,
                     left=0.08, right=0.96, top=0.93, bottom=0.06)

        # === HEADER ===
        ax_header = fig.add_subplot(gs[0, :])
        ax_header.axis('off')

        # Title
        ax_header.text(0.5, 0.7, 'SH1 Christchurch Motorway Speed Limit Change Impact Analysis',
                      ha='center', va='top', fontsize=16, fontweight='bold',
                      color=self.colors['text'])

        # Subtitle
        ax_header.text(0.5, 0.35, 'Before-After Evaluation: 100 → 110 km/h (April 13, 2025)',
                      ha='center', va='top', fontsize=11,
                      color=self.colors['neutral'])

        # Key stats boxes
        stats = [
            ("1,127", "Motorway Trips", self.colors['primary']),
            ("135K", "GPS Points", self.colors['secondary']),
            ("26", "Crashes", self.colors['warning']),
            ("+3.2 km/h", "LCV Speed Δ", self.colors['positive'])
        ]

        x_positions = [0.15, 0.38, 0.62, 0.85]
        for (value, label, color), x in zip(stats, x_positions):
            # Box
            rect = patches.FancyBboxPatch((x-0.06, -0.1), 0.12, 0.3,
                                         boxstyle="round,pad=0.01",
                                         linewidth=1.5, edgecolor=color,
                                         facecolor='white', transform=ax_header.transAxes)
            ax_header.add_patch(rect)

            # Value
            ax_header.text(x, 0.12, value, ha='center', va='center',
                          fontsize=12, fontweight='bold', color=color,
                          transform=ax_header.transAxes)
            # Label
            ax_header.text(x, -0.02, label, ha='center', va='center',
                          fontsize=7, color=self.colors['neutral'],
                          transform=ax_header.transAxes)

        # === ROW 1: SPEED CHANGES ===

        # Speed by vehicle type (before/after bars)
        ax1 = fig.add_subplot(gs[1, 0])
        vehicle_types = ['LCV', 'CAR', 'HCV']
        vehicle_labels = ['Light\nCommercial', 'Passenger\nCars', 'Heavy\nCommercial']

        x = np.arange(len(vehicle_types))
        width = 0.35

        before_speeds = []
        after_speeds = []

        for vtype in vehicle_types:
            veh_data = self.motorway_trips[self.motorway_trips['VehicleType'] == vtype]
            before_speeds.append(veh_data[veh_data['period'] == 'before']['avg_speed'].mean())
            after_speeds.append(veh_data[veh_data['period'] == 'after']['avg_speed'].mean())

        bars1 = ax1.bar(x - width/2, before_speeds, width, label='Before',
                       color=self.colors['before'], alpha=0.9)
        bars2 = ax1.bar(x + width/2, after_speeds, width, label='After',
                       color=self.colors['after'], alpha=0.9)

        # Add value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}',
                        ha='center', va='bottom', fontsize=7, fontweight='bold')

        ax1.set_ylabel('Average Speed (km/h)', fontweight='bold')
        ax1.set_title('Speed Changes by Vehicle Type', fontweight='bold', pad=10)
        ax1.set_xticks(x)
        ax1.set_xticklabels(vehicle_labels, fontsize=7)
        ax1.legend(frameon=True, fancybox=True)
        ax1.grid(axis='y', alpha=0.3, linestyle='--')
        ax1.set_ylim(55, 80)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)

        # Speed change magnitude
        ax2 = fig.add_subplot(gs[1, 1])

        changes = [after_speeds[i] - before_speeds[i] for i in range(len(vehicle_types))]
        colors_change = [self.colors['positive'] if c > 2 else self.colors['warning'] if c > 0 else self.colors['negative'] for c in changes]

        bars = ax2.barh(vehicle_labels, changes, color=colors_change, alpha=0.9)

        for i, (bar, change) in enumerate(zip(bars, changes)):
            ax2.text(change + 0.1, i, f'+{change:.2f} km/h', va='center', fontsize=8, fontweight='bold')

        ax2.set_xlabel('Speed Change (km/h)', fontweight='bold')
        ax2.set_title('Magnitude of Change', fontweight='bold', pad=10)
        ax2.axvline(0, color='black', linewidth=0.8, linestyle='-')
        ax2.grid(axis='x', alpha=0.3, linestyle='--')
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.set_xlim(-0.5, 4)

        # 85th percentile speeds (free-flow)
        ax3 = fig.add_subplot(gs[1, 2])

        before_p85 = []
        after_p85 = []

        for vtype in vehicle_types:
            veh_data = self.motorway_trips[self.motorway_trips['VehicleType'] == vtype]
            before_p85.append(veh_data[veh_data['period'] == 'before']['avg_speed'].quantile(0.85))
            after_p85.append(veh_data[veh_data['period'] == 'after']['avg_speed'].quantile(0.85))

        bars1 = ax3.bar(x - width/2, before_p85, width, label='Before',
                       color=self.colors['before'], alpha=0.9)
        bars2 = ax3.bar(x + width/2, after_p85, width, label='After',
                       color=self.colors['after'], alpha=0.9)

        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}',
                        ha='center', va='bottom', fontsize=7, fontweight='bold')

        ax3.set_ylabel('85th Percentile Speed (km/h)', fontweight='bold')
        ax3.set_title('Free-Flow Speeds (85th %ile)', fontweight='bold', pad=10)
        ax3.set_xticks(x)
        ax3.set_xticklabels(vehicle_labels, fontsize=7)
        ax3.legend(frameon=True, fancybox=True)
        ax3.grid(axis='y', alpha=0.3, linestyle='--')
        ax3.set_ylim(65, 85)
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)

        # === ROW 2: BEHAVIORAL CHANGES ===

        # Hard braking by vehicle type
        ax4 = fig.add_subplot(gs[2, 0])

        behaviors = []
        for vtype in ['CAR', 'LCV', 'HCV']:
            veh_beh = self.behavioral_vehicle[self.behavioral_vehicle['vehicle_type'] == vtype]
            before_beh = veh_beh[veh_beh['period'] == 'before'].iloc[0]['hard_brake_rate']
            after_beh = veh_beh[veh_beh['period'] == 'after'].iloc[0]['hard_brake_rate']
            behaviors.append(after_beh - before_beh)

        colors_beh = [self.colors['negative'] if b > 0 else self.colors['positive'] for b in behaviors]
        bars = ax4.barh(['Passenger\nCars', 'Light\nCommercial', 'Heavy\nCommercial'], behaviors,
                       color=colors_beh, alpha=0.9)

        for i, (bar, val) in enumerate(zip(bars, behaviors)):
            ax4.text(val + (0.02 if val > 0 else -0.02), i,
                    f'{val:+.2f}', va='center',
                    ha='left' if val > 0 else 'right',
                    fontsize=8, fontweight='bold')

        ax4.set_xlabel('Change in Hard Braking Rate (per 1000)', fontweight='bold')
        ax4.set_title('Hard Braking Changes', fontweight='bold', pad=10)
        ax4.axvline(0, color='black', linewidth=0.8)
        ax4.grid(axis='x', alpha=0.3, linestyle='--')
        ax4.spines['top'].set_visible(False)
        ax4.spines['right'].set_visible(False)

        # Hard steering by vehicle type
        ax5 = fig.add_subplot(gs[2, 1])

        steering = []
        for vtype in ['CAR', 'LCV', 'HCV']:
            veh_beh = self.behavioral_vehicle[self.behavioral_vehicle['vehicle_type'] == vtype]
            before_beh = veh_beh[veh_beh['period'] == 'before'].iloc[0]['hard_steer_rate']
            after_beh = veh_beh[veh_beh['period'] == 'after'].iloc[0]['hard_steer_rate']
            steering.append(after_beh - before_beh)

        bars = ax5.barh(['Passenger\nCars', 'Light\nCommercial', 'Heavy\nCommercial'], steering,
                       color=self.colors['warning'], alpha=0.9)

        for i, (bar, val) in enumerate(zip(bars, steering)):
            ax5.text(val + 0.05, i, f'+{val:.2f}', va='center', ha='left',
                    fontsize=8, fontweight='bold')

        ax5.set_xlabel('Change in Hard Steering Rate (per 1000)', fontweight='bold')
        ax5.set_title('Hard Steering Changes (↑ All Types)', fontweight='bold', pad=10)
        ax5.axvline(0, color='black', linewidth=0.8)
        ax5.grid(axis='x', alpha=0.3, linestyle='--')
        ax5.spines['top'].set_visible(False)
        ax5.spines['right'].set_visible(False)
        ax5.set_xlim(0, 1.2)

        # Overall behavioral summary
        ax6 = fig.add_subplot(gs[2, 2])

        metrics = ['Hard\nBraking', 'Rapid\nAccel', 'Hard\nSteering']
        before = self.behavioral_period[self.behavioral_period['period'] == 'before'].iloc[0]
        after = self.behavioral_period[self.behavioral_period['period'] == 'after'].iloc[0]

        values_before = [before['hard_brake_rate'], before['rapid_accel_rate'], before['hard_steer_rate']]
        values_after = [after['hard_brake_rate'], after['rapid_accel_rate'], after['hard_steer_rate']]

        x = np.arange(len(metrics))
        width = 0.35

        bars1 = ax6.bar(x - width/2, values_before, width, label='Before',
                       color=self.colors['before'], alpha=0.9)
        bars2 = ax6.bar(x + width/2, values_after, width, label='After',
                       color=self.colors['after'], alpha=0.9)

        ax6.set_ylabel('Events per 1000 Transitions', fontweight='bold')
        ax6.set_title('Overall Behavioral Metrics', fontweight='bold', pad=10)
        ax6.set_xticks(x)
        ax6.set_xticklabels(metrics, fontsize=7)
        ax6.legend(frameon=True, fancybox=True)
        ax6.grid(axis='y', alpha=0.3, linestyle='--')
        ax6.spines['top'].set_visible(False)
        ax6.spines['right'].set_visible(False)

        # === ROW 3: CRASH ANALYSIS ===

        # Crash rates
        ax7 = fig.add_subplot(gs[3, 0])

        before_crash = self.crash_rates[self.crash_rates['period'] == 'before'].iloc[0]
        after_crash = self.crash_rates[self.crash_rates['period'] == 'after'].iloc[0]

        periods = ['Before', 'After']
        crash_counts = [before_crash['crashes'], after_crash['crashes']]
        crash_rates = [before_crash['rate_per_day'], after_crash['rate_per_day']]

        x = np.arange(len(periods))
        width = 0.6

        bars = ax7.bar(x, crash_counts, width, color=[self.colors['before'], self.colors['after']], alpha=0.9)

        for i, (bar, count, rate) in enumerate(zip(bars, crash_counts, crash_rates)):
            ax7.text(i, count + 0.5, f'{int(count)}\ncrashes\n({rate:.2f}/day)',
                    ha='center', va='bottom', fontsize=8, fontweight='bold')

        ax7.set_ylabel('Total Crashes', fontweight='bold')
        ax7.set_title('Crash Frequency', fontweight='bold', pad=10)
        ax7.set_xticks(x)
        ax7.set_xticklabels(periods)
        ax7.grid(axis='y', alpha=0.3, linestyle='--')
        ax7.spines['top'].set_visible(False)
        ax7.spines['right'].set_visible(False)
        ax7.set_ylim(0, 20)

        # Crash involvement by vehicle type
        ax8 = fig.add_subplot(gs[3, 1])

        crash_veh = self.crash_vehicle_correlation

        vehicle_types_crash = ['CAR', 'LCV', 'HCV']
        crash_changes = []

        for vtype in vehicle_types_crash:
            veh_crash = crash_veh[crash_veh['vehicle_type'] == vtype]
            if len(veh_crash) > 0:
                crash_changes.append(veh_crash.iloc[0]['crash_change'])
            else:
                crash_changes.append(0)

        colors_crash = [self.colors['car'], self.colors['lcv'], self.colors['hcv']]
        bars = ax8.barh(['Passenger\nCars', 'Light\nCommercial', 'Heavy\nCommercial'],
                       crash_changes, color=colors_crash, alpha=0.9)

        for i, (bar, val) in enumerate(zip(bars, crash_changes)):
            ax8.text(val + (0.5 if val > 0 else -0.5), i,
                    f'{val:+d}', va='center',
                    ha='left' if val > 0 else 'right',
                    fontsize=8, fontweight='bold')

        ax8.set_xlabel('Change in Crash Vehicles', fontweight='bold')
        ax8.set_title('Crash Involvement Δ', fontweight='bold', pad=10)
        ax8.axvline(0, color='black', linewidth=0.8)
        ax8.grid(axis='x', alpha=0.3, linestyle='--')
        ax8.spines['top'].set_visible(False)
        ax8.spines['right'].set_visible(False)

        # Correlation matrix (behavior vs crashes)
        ax9 = fig.add_subplot(gs[3, 2])
        ax9.axis('off')

        # Title
        ax9.text(0.5, 0.95, 'Behavior-Crash Correlation', ha='center', va='top',
                fontsize=10, fontweight='bold', transform=ax9.transAxes)

        # Create correlation table
        y_start = 0.82
        y_step = 0.22

        headers = ['Vehicle', 'Behavior', 'Crashes', 'Pattern']
        x_positions = [0.15, 0.40, 0.65, 0.90]

        # Headers
        for header, x in zip(headers, x_positions):
            ax9.text(x, y_start, header, ha='center', va='top', fontsize=8,
                    fontweight='bold', transform=ax9.transAxes)

        # Data rows
        for i, vtype in enumerate(['CAR', 'LCV', 'HCV']):
            y = y_start - (i + 1) * y_step

            # Vehicle type
            vtype_label = {'CAR': 'Passenger', 'LCV': 'Light Comm', 'HCV': 'Heavy Comm'}[vtype]
            ax9.text(0.15, y, vtype_label, ha='center', va='center', fontsize=7,
                    transform=ax9.transAxes)

            # Behavior direction
            if vtype == 'CAR':
                beh_text = '↑ Worse'
                beh_color = self.colors['negative']
            else:
                beh_text = '↓ Better'
                beh_color = self.colors['positive']

            ax9.text(0.40, y, beh_text, ha='center', va='center', fontsize=7,
                    color=beh_color, fontweight='bold', transform=ax9.transAxes)

            # Crash direction
            crash_val = crash_changes[['CAR', 'LCV', 'HCV'].index(vtype)]
            crash_text = f'{crash_val:+d}'
            crash_color = self.colors['negative'] if crash_val > 0 else self.colors['positive']

            ax9.text(0.65, y, crash_text, ha='center', va='center', fontsize=7,
                    color=crash_color, fontweight='bold', transform=ax9.transAxes)

            # Pattern
            pattern = crash_veh[crash_veh['vehicle_type'] == vtype].iloc[0]['correlation'] if len(crash_veh[crash_veh['vehicle_type'] == vtype]) > 0 else 'N/A'
            pattern_color = self.colors['negative'] if pattern == 'ALIGNED' else self.colors['neutral']

            ax9.text(0.90, y, pattern[:3], ha='center', va='center', fontsize=7,
                    color=pattern_color, fontweight='bold', transform=ax9.transAxes)

        # Footer
        ax9.text(0.5, 0.02, 'Note: Passenger cars show ALIGNED pattern (worse behavior + more crashes)',
                ha='center', va='bottom', fontsize=6, style='italic',
                color=self.colors['warning'], transform=ax9.transAxes)

        # Page footer
        fig.text(0.5, 0.02, 'Page 1 of 2 | SH1 Christchurch Speed Limit Change Analysis | Generated 2025-10-22',
                ha='center', va='bottom', fontsize=7, color=self.colors['neutral'])

        # Save
        output_path = self.output_dir / "executive_report_page1.pdf"
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=self.colors['background'])
        print(f"   ✅ Page 1 saved: {output_path}")

        plt.close()

        return output_path

    def create_page2(self):
        """Create page 2: Deep dive, temporal patterns, key findings"""
        print("\n📄 Creating Page 2...")

        # Use trip-level data for temporal analysis (simpler and more reliable)
        df_trips = self.motorway_trips.copy()

        # Parse trip start times from original corridor trips
        trips_full = pd.read_parquet(
            self.base_dir / "output/processed_data/trip_level/corridor_trips.parquet",
            columns=['TripID', 'StartHour', 'StartDate']
        )

        df_trips = df_trips.merge(trips_full, on='TripID', how='left')

        # For temporal patterns, we'll use aggregated data by hour
        df_trips['hour'] = df_trips['StartHour']
        df_trips['day_of_week'] = pd.to_datetime(df_trips['StartDate'], errors='coerce').dt.dayofweek

        fig = plt.figure(figsize=(11, 8.5))
        fig.patch.set_facecolor(self.colors['background'])

        gs = GridSpec(4, 3, figure=fig, hspace=0.4, wspace=0.35,
                     left=0.08, right=0.96, top=0.93, bottom=0.06)

        # === HEADER ===
        ax_header = fig.add_subplot(gs[0, :])
        ax_header.axis('off')

        ax_header.text(0.5, 0.7, 'Temporal Patterns & Key Findings',
                      ha='center', va='top', fontsize=16, fontweight='bold',
                      color=self.colors['text'])

        ax_header.text(0.5, 0.3, 'Detailed Analysis of Speed, Behavior, and Safety Outcomes',
                      ha='center', va='top', fontsize=11,
                      color=self.colors['neutral'])

        # === ROW 1: TEMPORAL PATTERNS ===

        # Hour of day - trip counts
        ax1 = fig.add_subplot(gs[1, 0])

        # Use trip-level data
        for period, color in [('before', self.colors['before']), ('after', self.colors['after'])]:
            period_trips = df_trips[df_trips['period'] == period]
            hour_counts = period_trips.groupby('hour').size()

            # Plot only hours that exist
            if len(hour_counts) > 0:
                ax1.plot(hour_counts.index, hour_counts.values, marker='o', label=period.capitalize(),
                        color=color, linewidth=2, markersize=4, alpha=0.8)

        ax1.set_xlabel('Hour of Day', fontweight='bold')
        ax1.set_ylabel('Trip Count', fontweight='bold')
        ax1.set_title('Temporal Distribution', fontweight='bold', pad=10)
        ax1.legend(frameon=True, fancybox=True)
        ax1.grid(alpha=0.3, linestyle='--')
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.set_xlim(0, 23)

        # Day of week
        ax2 = fig.add_subplot(gs[1, 1])

        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

        for period, color in [('before', self.colors['before']), ('after', self.colors['after'])]:
            period_trips = df_trips[df_trips['period'] == period]
            day_counts = period_trips.groupby('day_of_week').size()

            # Create full week array
            week_counts = [day_counts.get(i, 0) for i in range(7)]
            ax2.plot(range(7), week_counts, marker='o',
                    label=period.capitalize(), color=color, linewidth=2, markersize=4, alpha=0.8)

        ax2.set_xlabel('Day of Week', fontweight='bold')
        ax2.set_ylabel('Trip Count', fontweight='bold')
        ax2.set_title('Weekly Pattern', fontweight='bold', pad=10)
        ax2.set_xticks(range(7))
        ax2.set_xticklabels(day_names, fontsize=7)
        ax2.legend(frameon=True, fancybox=True)
        ax2.grid(alpha=0.3, linestyle='--')
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)

        # Speed distribution
        ax3 = fig.add_subplot(gs[1, 2])

        for period, color in [('before', self.colors['before']), ('after', self.colors['after'])]:
            period_trips = self.motorway_trips[self.motorway_trips['period'] == period]
            speeds = period_trips['avg_speed']

            ax3.hist(speeds, bins=20, alpha=0.6, label=period.capitalize(),
                    color=color, edgecolor='white', linewidth=0.5)

        ax3.set_xlabel('Average Speed (km/h)', fontweight='bold')
        ax3.set_ylabel('Trip Count', fontweight='bold')
        ax3.set_title('Speed Distribution', fontweight='bold', pad=10)
        ax3.legend(frameon=True, fancybox=True)
        ax3.grid(axis='y', alpha=0.3, linestyle='--')
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)

        # === ROW 2: KEY METRICS SUMMARY ===

        ax4 = fig.add_subplot(gs[2, :])
        ax4.axis('off')

        # Title
        ax4.text(0.5, 0.95, 'Summary of Key Metrics', ha='center', va='top',
                fontsize=12, fontweight='bold', transform=ax4.transAxes)

        # Create metrics grid
        metrics_data = [
            ['Metric', 'Before', 'After', 'Change', 'Interpretation'],
            ['Speed (overall)', '66.96 km/h', '67.70 km/h', '+0.74 km/h', 'Small overall increase'],
            ['Speed (LCV)', '71.44 km/h', '74.60 km/h', '+3.16 km/h', 'Largest increase (+4.4%)'],
            ['Speed (CAR)', '71.79 km/h', '73.93 km/h', '+2.14 km/h', 'Moderate increase (+3.0%)'],
            ['Speed (HCV)', '62.56 km/h', '63.45 km/h', '+0.88 km/h', 'Limited by 90 km/h cap'],
            ['Hard Braking', '0.62/1000', '0.25/1000', '-60%', 'Improved overall'],
            ['CAR Hard Braking', '0.00/1000', '0.16/1000', 'Worse', '⚠️ Only type that worsened'],
            ['Hard Steering', '11.27/1000', '12.06/1000', '+7%', 'Increased (all types)'],
            ['Crashes', '11 (76 days)', '15 (85 days)', '+22%', 'Rate: 0.145 → 0.176/day'],
            ['CAR Crashes', '13 vehicles', '28 vehicles', '+115%', '⚠️ More than doubled'],
            ['Serious Crashes', '1', '0', '-100%', 'Eliminated'],
        ]

        # Column positions
        col_x = [0.05, 0.28, 0.46, 0.62, 0.80]
        row_y_start = 0.82
        row_height = 0.07

        # Draw header row
        for i, header in enumerate(metrics_data[0]):
            ax4.text(col_x[i], row_y_start, header, ha='left', va='center',
                    fontsize=8, fontweight='bold', transform=ax4.transAxes,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor=self.colors['grid'], alpha=0.3))

        # Draw data rows
        for row_idx, row_data in enumerate(metrics_data[1:], 1):
            y = row_y_start - row_idx * row_height

            # Alternate row background
            if row_idx % 2 == 0:
                rect = patches.Rectangle((0.02, y - row_height/3), 0.96, row_height * 0.8,
                                        transform=ax4.transAxes, facecolor=self.colors['grid'],
                                        alpha=0.15, zorder=0)
                ax4.add_patch(rect)

            for col_idx, cell_data in enumerate(row_data):
                # Color coding for specific cells
                color = self.colors['text']
                weight = 'normal'

                if '⚠️' in str(cell_data):
                    color = self.colors['warning']
                    weight = 'bold'
                elif col_idx == 3:  # Change column
                    if '+' in str(cell_data) and row_idx in [1, 2, 3]:  # Speed increases
                        color = self.colors['positive']
                    elif 'Worse' in str(cell_data) or '+115%' in str(cell_data) or '+22%' in str(cell_data):
                        color = self.colors['negative']
                        weight = 'bold'
                    elif '-' in str(cell_data) and row_idx in [5, 10]:  # Good decreases
                        color = self.colors['positive']

                ax4.text(col_x[col_idx], y, str(cell_data), ha='left', va='center',
                        fontsize=6.5, color=color, fontweight=weight, transform=ax4.transAxes)

        # === ROW 3: KEY FINDINGS ===

        ax5 = fig.add_subplot(gs[3, :])
        ax5.axis('off')

        # Title
        ax5.text(0.5, 0.95, 'Key Findings & Recommendations', ha='center', va='top',
                fontsize=12, fontweight='bold', transform=ax5.transAxes)

        findings = [
            ('1. Light Vehicles Responded to Speed Limit',
             'LCV and CAR increased speeds by 2-3 km/h. HCV remained at ~63 km/h (regulatory 90 km/h limit).'),

            ('2. Passenger Cars Show Concerning Pattern',
             '⚠️ CAR is the ONLY vehicle type with WORSE behavior (hard braking ↑, hard steering ↑) AND doubled crash involvement (+115%).'),

            ('3. Speed Differential Creating Safety Issues',
             'Light vehicles (70-75 km/h) vs Heavy vehicles (62-63 km/h) = 10-13 km/h gap. Rear-end crashes increased 75%.'),

            ('4. Crash Severity Improved',
             'Serious crashes eliminated (1 → 0). More crashes but less severe: shift toward non-injury crashes.'),

            ('5. Professional Drivers Adapted Better',
             'Commercial drivers (LCV/HCV) showed better braking control despite increased steering maneuvers.'),

            ('Recommendation',
             'Focus safety interventions on passenger car following distances and speed management in mixed traffic.')
        ]

        y_pos = 0.82
        y_step = 0.14

        for title, text in findings:
            # Background box
            rect = patches.FancyBboxPatch((0.03, y_pos - 0.08), 0.94, 0.10,
                                         boxstyle="round,pad=0.01",
                                         linewidth=1, edgecolor=self.colors['grid'],
                                         facecolor='white', transform=ax5.transAxes)
            ax5.add_patch(rect)

            # Title
            color = self.colors['warning'] if 'Passenger Cars' in title or 'Recommendation' in title else self.colors['primary']
            ax5.text(0.04, y_pos, title, ha='left', va='top',
                    fontsize=9, fontweight='bold', color=color, transform=ax5.transAxes)

            # Text
            ax5.text(0.04, y_pos - 0.05, text, ha='left', va='top',
                    fontsize=7, color=self.colors['text'], transform=ax5.transAxes,
                    wrap=True)

            y_pos -= y_step

        # Page footer
        fig.text(0.5, 0.02, 'Page 2 of 2 | Data: 1,127 trips (135K GPS points), 26 crashes | Analysis: Before-After Evaluation (April 13, 2025)',
                ha='center', va='bottom', fontsize=7, color=self.colors['neutral'])

        # Save
        output_path = self.output_dir / "executive_report_page2.pdf"
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=self.colors['background'])
        print(f"   ✅ Page 2 saved: {output_path}")

        plt.close()

        return output_path

    def combine_pages(self):
        """Combine both pages into single PDF"""
        print("\n📄 Combining pages into final PDF...")

        try:
            from PyPDF2 import PdfMerger
        except ImportError:
            print("   ⚠️  PyPDF2 not available. Install with: pip install PyPDF2")
            print("   Pages saved separately. Combine manually or install PyPDF2.")
            return None

        merger = PdfMerger()

        page1_path = self.output_dir / "executive_report_page1.pdf"
        page2_path = self.output_dir / "executive_report_page2.pdf"

        merger.append(str(page1_path))
        merger.append(str(page2_path))

        final_path = self.output_dir / "SH1_Speed_Limit_Change_Executive_Report.pdf"
        merger.write(str(final_path))
        merger.close()

        print(f"   ✅ Final report: {final_path}")

        return final_path

    def generate_report(self):
        """Generate complete 2-page report"""
        self.load_all_data()
        self.create_page1()
        self.create_page2()
        final_path = self.combine_pages()

        print("\n" + "=" * 80)
        print("EXECUTIVE REPORT COMPLETE")
        print("=" * 80)
        print(f"\nOutput directory: {self.output_dir}")
        print("\nGenerated files:")
        print("  - executive_report_page1.pdf")
        print("  - executive_report_page2.pdf")
        if final_path:
            print(f"  - SH1_Speed_Limit_Change_Executive_Report.pdf (COMBINED)")
        print("\n✅ Publication-ready 2-page PDF report generated")
        print("=" * 80)


if __name__ == "__main__":
    generator = ExecutiveReportGenerator()
    generator.generate_report()

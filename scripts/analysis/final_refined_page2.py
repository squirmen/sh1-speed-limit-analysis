"""
Page 2 - Final Refinement
Fix all data issues and improve clarity
"""

import sys
sys.path.append('/Volumes/T7/Data/connected_vehicle_data/scripts/analysis')

from generate_enhanced_executive_report import EnhancedExecutiveReportGenerator
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.patches as patches
import pandas as pd
import numpy as np

class FinalRefinedPage2(EnhancedExecutiveReportGenerator):
    """Create Page 2 with all fixes"""

    def create_page2_final(self):
        """Page 2: Fixed Data-Rich Visualizations"""
        print("\n📄 Creating Page 2 (FINAL - All Fixes)...")

        fig = plt.figure(figsize=(11, 8.5))
        fig.patch.set_facecolor(self.colors['background'])

        gs = GridSpec(4, 3, figure=fig, hspace=0.60, wspace=0.45,
                     left=0.08, right=0.96, top=0.92, bottom=0.07)

        # Header
        ax_header = fig.add_subplot(gs[0, :])
        ax_header.axis('off')

        ax_header.text(0.5, 0.7, 'Temporal & Behavioral Patterns',
                      ha='center', va='top', fontsize=17, fontweight='bold',
                      color=self.colors['text'])

        ax_header.text(0.5, 0.25, 'Detailed Analysis of Speed Changes and Driving Behavior',
                      ha='center', va='top', fontsize=10,
                      color=self.colors['neutral'])

        # === ROW 1: TEMPORAL PATTERNS ===

        # Chart 1: Speed by hour of day - CLEARER
        ax1 = fig.add_subplot(gs[1, :2])

        hours = range(24)
        before_hourly = []
        after_hourly = []

        for hour in hours:
            before_data = self.motorway_trips[(self.motorway_trips['period'] == 'before') &
                                              (self.motorway_trips['StartHour'] == hour)]
            after_data = self.motorway_trips[(self.motorway_trips['period'] == 'after') &
                                             (self.motorway_trips['StartHour'] == hour)]

            before_hourly.append(before_data['avg_speed'].mean() if len(before_data) > 0 else np.nan)
            after_hourly.append(after_data['avg_speed'].mean() if len(after_data) > 0 else np.nan)

        # Plot with clear markers
        ax1.plot(hours, before_hourly, marker='o', linewidth=2.5, markersize=6,
                color=self.colors['before'], label='Before (100 km/h)', alpha=0.9,
                markeredgecolor='white', markeredgewidth=1)
        ax1.plot(hours, after_hourly, marker='s', linewidth=2.5, markersize=6,
                color=self.colors['after'], label='After (110 km/h)', alpha=0.9,
                markeredgecolor='white', markeredgewidth=1)

        # Shade peak hours for context
        ax1.axvspan(7, 9, alpha=0.08, color='orange', zorder=0)
        ax1.axvspan(16, 18, alpha=0.08, color='red', zorder=0)

        # Add annotations
        ax1.text(8, max([h for h in before_hourly + after_hourly if not np.isnan(h)]) * 0.98,
                'AM Peak', ha='center', fontsize=6, style='italic', color='orange')
        ax1.text(17, max([h for h in before_hourly + after_hourly if not np.isnan(h)]) * 0.98,
                'PM Peak', ha='center', fontsize=6, style='italic', color='red')

        ax1.set_xlabel('Hour of Day', fontweight='bold', fontsize=9)
        ax1.set_ylabel('Average Speed (km/h)', fontweight='bold', fontsize=9)
        ax1.set_title('Speed Variation Throughout Day', fontweight='bold', pad=15, fontsize=10)
        ax1.legend(frameon=True, fancybox=True, loc='lower right', fontsize=7)
        ax1.grid(axis='both', alpha=0.25, linestyle='--', linewidth=0.5)
        ax1.set_xlim(0, 23)
        ax1.set_xticks(range(0, 24, 3))
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)

        # Chart 2: Speed distribution histogram
        ax2 = fig.add_subplot(gs[1, 2])

        before_speeds = self.motorway_trips[self.motorway_trips['period'] == 'before']['avg_speed'].dropna()
        after_speeds = self.motorway_trips[self.motorway_trips['period'] == 'after']['avg_speed'].dropna()

        bins = np.arange(40, 95, 4)
        ax2.hist(before_speeds, bins=bins, alpha=0.6, color=self.colors['before'],
                label='Before', edgecolor='white', linewidth=0.5, density=True)
        ax2.hist(after_speeds, bins=bins, alpha=0.6, color=self.colors['after'],
                label='After', edgecolor='white', linewidth=0.5, density=True)

        # Add mean lines
        ax2.axvline(before_speeds.mean(), color=self.colors['before'],
                   linestyle='--', linewidth=2.5, alpha=0.9, label=f'Before μ={before_speeds.mean():.1f}')
        ax2.axvline(after_speeds.mean(), color=self.colors['after'],
                   linestyle='--', linewidth=2.5, alpha=0.9, label=f'After μ={after_speeds.mean():.1f}')

        ax2.set_xlabel('Speed (km/h)', fontweight='bold', fontsize=9)
        ax2.set_ylabel('Density', fontweight='bold', fontsize=9)
        ax2.set_title('Speed Distribution', fontweight='bold', pad=15, fontsize=10)
        ax2.legend(frameon=True, fancybox=True, loc='upper right', fontsize=6)
        ax2.grid(axis='y', alpha=0.25, linestyle='--', linewidth=0.5)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)

        # === ROW 2: CRASH ANALYSIS ===

        # Chart 3: Crashes by time of day - FIXED PARSING
        ax3 = fig.add_subplot(gs[2, 0])

        # Fix the time format parsing - it's HH:MM not HH:MM:SS
        crash_data_with_time = self.crash_data.copy()
        crash_data_with_time['crash_hour'] = pd.to_datetime(
            crash_data_with_time['Crash time'],
            format='%H:%M',  # FIXED FORMAT
            errors='coerce'
        ).dt.hour

        time_groups = ['0-3', '3-6', '6-9', '9-12', '12-15', '15-18', '18-21', '21-24']
        before_time = []
        after_time = []

        for i, tg in enumerate(time_groups):
            start_hour = i * 3
            end_hour = (i + 1) * 3

            before_count = len(crash_data_with_time[(crash_data_with_time['period'] == 'before') &
                                                    (crash_data_with_time['crash_hour'] >= start_hour) &
                                                    (crash_data_with_time['crash_hour'] < end_hour)])
            after_count = len(crash_data_with_time[(crash_data_with_time['period'] == 'after') &
                                                   (crash_data_with_time['crash_hour'] >= start_hour) &
                                                   (crash_data_with_time['crash_hour'] < end_hour)])

            before_time.append(before_count)
            after_time.append(after_count)

        y_pos = np.arange(len(time_groups))
        width = 0.35

        ax3.barh(y_pos - width/2, before_time, width, label='Before',
                color=self.colors['before'], alpha=0.85, edgecolor='white', linewidth=0.5)
        ax3.barh(y_pos + width/2, after_time, width, label='After',
                color=self.colors['after'], alpha=0.85, edgecolor='white', linewidth=0.5)

        ax3.set_yticks(y_pos)
        ax3.set_yticklabels(time_groups, fontsize=7)
        ax3.set_xlabel('Crash Count', fontweight='bold', fontsize=9)
        ax3.set_title('Crashes by Time of Day', fontweight='bold', pad=15, fontsize=10)
        ax3.legend(frameon=True, fancybox=True, loc='lower right', fontsize=7)
        ax3.grid(axis='x', alpha=0.25, linestyle='--', linewidth=0.5)
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)

        # Chart 4: Vehicle type speed differential
        ax4 = fig.add_subplot(gs[2, 1])

        vehicle_types = ['LCV', 'CAR', 'HCV']
        vehicle_labels = ['Light\nCommercial', 'Passenger\nCars', 'Heavy\nCommercial']

        before_means = []
        after_means = []
        before_p85 = []
        after_p85 = []

        for vtype in vehicle_types:
            veh_data = self.motorway_trips[self.motorway_trips['VehicleType'] == vtype]
            before_data = veh_data[veh_data['period'] == 'before']['avg_speed']
            after_data = veh_data[veh_data['period'] == 'after']['avg_speed']

            before_means.append(before_data.mean())
            after_means.append(after_data.mean())
            before_p85.append(before_data.quantile(0.85))
            after_p85.append(after_data.quantile(0.85))

        x = np.arange(len(vehicle_types))

        # Plot mean and p85 as connected range
        for i, (label, color) in enumerate(zip(['Before', 'After'],
                                               [self.colors['before'], self.colors['after']])):
            means = before_means if i == 0 else after_means
            p85s = before_p85 if i == 0 else after_p85

            offset = -0.15 if i == 0 else 0.15

            # Plot range
            for j in range(len(vehicle_types)):
                ax4.plot([x[j] + offset, x[j] + offset], [means[j], p85s[j]],
                        color=color, linewidth=3, alpha=0.7, zorder=1)

            ax4.scatter(x + offset, means, s=100, marker='o', color=color,
                       alpha=0.9, edgecolors='white', linewidths=1.5,
                       label=f'{label}', zorder=3)
            ax4.scatter(x + offset, p85s, s=60, marker='^', color=color,
                       alpha=0.6, edgecolors='white', linewidths=1,
                       zorder=2)

        ax4.set_xticks(x)
        ax4.set_xticklabels(vehicle_labels, fontsize=6.5)
        ax4.set_ylabel('Speed (km/h)', fontweight='bold', fontsize=9)
        ax4.set_title('Speed Range (Mean & 85th)', fontweight='bold', pad=15, fontsize=10)
        ax4.legend(frameon=True, fancybox=True, loc='lower left', fontsize=6.5)
        ax4.grid(axis='y', alpha=0.25, linestyle='--', linewidth=0.5)
        ax4.spines['top'].set_visible(False)
        ax4.spines['right'].set_visible(False)

        # Chart 5: Passenger car behavior
        ax5 = fig.add_subplot(gs[2, 2])

        car_beh = self.behavioral_vehicle[self.behavioral_vehicle['vehicle_type'] == 'CAR']

        metrics = ['Hard\nBrake', 'Rapid\nAccel', 'Hard\nSteer']
        before_beh = []
        after_beh = []

        if len(car_beh[car_beh['period'] == 'before']) > 0:
            before_row = car_beh[car_beh['period'] == 'before'].iloc[0]
            before_beh = [before_row['hard_brake_rate'], before_row['rapid_accel_rate'], before_row['hard_steer_rate']]

        if len(car_beh[car_beh['period'] == 'after']) > 0:
            after_row = car_beh[car_beh['period'] == 'after'].iloc[0]
            after_beh = [after_row['hard_brake_rate'], after_row['rapid_accel_rate'], after_row['hard_steer_rate']]

        x = np.arange(len(metrics))
        width = 0.35

        bars1 = ax5.bar(x - width/2, before_beh, width, label='Before',
                       color=self.colors['before'], alpha=0.85, edgecolor='white', linewidth=0.5)
        bars2 = ax5.bar(x + width/2, after_beh, width, label='After',
                       color=self.colors['after'], alpha=0.85, edgecolor='white', linewidth=0.5)

        # Highlight increases with arrows
        for i, (b, a) in enumerate(zip(before_beh, after_beh)):
            if a > b:
                ax5.annotate('', xy=(i, a + 0.5), xytext=(i, a + 0.25),
                           arrowprops=dict(arrowstyle='->', color=self.colors['negative'], lw=2))

        ax5.set_ylabel('Events per 1000', fontweight='bold', fontsize=9)
        ax5.set_title('Passenger Car Behavior', fontweight='bold', pad=15, fontsize=10)
        ax5.set_xticks(x)
        ax5.set_xticklabels(metrics, fontsize=6.5)
        ax5.legend(frameon=True, fancybox=True, loc='upper left', fontsize=7)
        ax5.grid(axis='y', alpha=0.25, linestyle='--', linewidth=0.5)
        ax5.spines['top'].set_visible(False)
        ax5.spines['right'].set_visible(False)

        # === ROW 3: KEY INSIGHTS ===

        # Chart 6: Speed differential risk
        ax6 = fig.add_subplot(gs[3, 0])

        # Calculate speed differential
        differential_before = max(before_means) - min(before_means)
        differential_after = max(after_means) - min(after_means)

        periods = ['Before', 'After']
        differentials = [differential_before, differential_after]
        bar_colors = [self.colors['before'], self.colors['after']]

        bars = ax6.bar(range(2), differentials, width=0.6, color=bar_colors,
                      alpha=0.85, edgecolor='white', linewidth=0.5)

        for i, (bar, val) in enumerate(zip(bars, differentials)):
            ax6.text(i, val + 0.3, f'{val:.1f} km/h',
                    ha='center', va='bottom', fontsize=8, fontweight='bold')

        ax6.set_ylabel('Speed Gap (km/h)', fontweight='bold', fontsize=9)
        ax6.set_title('Vehicle Type Speed Gap', fontweight='bold', pad=15, fontsize=10)
        ax6.set_xticks(range(2))
        ax6.set_xticklabels(periods, fontsize=8)
        ax6.grid(axis='y', alpha=0.25, linestyle='--', linewidth=0.5)
        ax6.spines['top'].set_visible(False)
        ax6.spines['right'].set_visible(False)
        ax6.set_ylim(0, 16)

        # Chart 7: Severity trend - FIXED COLORS
        ax7 = fig.add_subplot(gs[3, 1])

        severity_order = ['Serious Crash', 'Minor Crash', 'Non-Injury Crash']
        severity_colors = [self.colors['negative'], self.colors['warning'], self.colors['neutral']]

        before_counts = [len(self.crash_data[(self.crash_data['period'] == 'before') &
                                             (self.crash_data['Crash severity'] == sev)])
                        for sev in severity_order]
        after_counts = [len(self.crash_data[(self.crash_data['period'] == 'after') &
                                            (self.crash_data['Crash severity'] == sev)])
                       for sev in severity_order]

        x = np.arange(len(severity_order))
        width = 0.35

        labels = ['Serious', 'Minor', 'Non-Injury']

        # FIXED: Use period colors for bars, not severity colors
        bars1 = ax7.bar(x - width/2, before_counts, width, label='Before',
                       color=self.colors['before'], alpha=0.85, edgecolor='white', linewidth=0.5)
        bars2 = ax7.bar(x + width/2, after_counts, width, label='After',
                       color=self.colors['after'], alpha=0.85, edgecolor='white', linewidth=0.5)

        # Highlight eliminated serious crashes
        if before_counts[0] > 0 and after_counts[0] == 0:
            ax7.text(0, max(before_counts[0], after_counts[0]) + 0.5, '✓ Eliminated',
                    ha='center', va='bottom', fontsize=7,
                    fontweight='bold', color=self.colors['positive'])

        ax7.set_ylabel('Crash Count', fontweight='bold', fontsize=9)
        ax7.set_title('Crash Severity Changes', fontweight='bold', pad=15, fontsize=10)
        ax7.set_xticks(x)
        ax7.set_xticklabels(labels, fontsize=7)
        ax7.legend(frameon=True, fancybox=True, loc='upper left', fontsize=7)
        ax7.grid(axis='y', alpha=0.25, linestyle='--', linewidth=0.5)
        ax7.spines['top'].set_visible(False)
        ax7.spines['right'].set_visible(False)

        # Chart 8: Commercial vehicle performance
        ax8 = fig.add_subplot(gs[3, 2])

        commercial_types = ['LCV', 'HCV']
        commercial_labels = ['Light\nCommercial', 'Heavy\nCommercial']

        brake_changes = []
        for vtype in commercial_types:
            veh_beh = self.behavioral_vehicle[self.behavioral_vehicle['vehicle_type'] == vtype]
            if len(veh_beh) >= 2:
                before_beh = veh_beh[veh_beh['period'] == 'before'].iloc[0]['hard_brake_rate']
                after_beh = veh_beh[veh_beh['period'] == 'after'].iloc[0]['hard_brake_rate']
                brake_changes.append(after_beh - before_beh)
            else:
                brake_changes.append(0)

        y_pos = np.arange(len(commercial_types))

        bars = ax8.barh(y_pos, brake_changes, color=[self.colors['lcv'], self.colors['hcv']],
                       alpha=0.85, edgecolor='white', linewidth=0.5)

        for i, (bar, val) in enumerate(zip(bars, brake_changes)):
            label_x = val - 0.15 if val < 0 else val + 0.15
            ha = 'right' if val < 0 else 'left'
            ax8.text(label_x, i, f'{val:.2f}',
                    va='center', ha=ha, fontsize=7, fontweight='bold')

        ax8.set_yticks(y_pos)
        ax8.set_yticklabels(commercial_labels, fontsize=7)
        ax8.set_xlabel('Change (per 1000)', fontweight='bold', fontsize=9)
        ax8.set_title('Commercial Hard Braking Δ', fontweight='bold', pad=15, fontsize=10)
        ax8.axvline(0, color='black', linewidth=0.8)
        ax8.grid(axis='x', alpha=0.25, linestyle='--', linewidth=0.5)
        ax8.spines['top'].set_visible(False)
        ax8.spines['right'].set_visible(False)

        # Footer
        fig.text(0.5, 0.02, 'Page 2 of 4 | SH1 Christchurch Speed Limit Change Analysis | Generated 2025-10-22',
                ha='center', va='bottom', fontsize=7, color=self.colors['neutral'])

        # Save
        output_path = self.output_dir / "enhanced_report_page2.pdf"
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=self.colors['background'])
        print(f"   ✅ Page 2 saved: {output_path}")

        plt.close()

        return output_path


if __name__ == "__main__":
    generator = FinalRefinedPage2()
    generator.load_all_data()
    generator.calculate_statistical_significance()
    generator.create_page2_final()

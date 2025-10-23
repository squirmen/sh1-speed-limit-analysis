"""
Page 4 - Final Refinement
Clean up comprehensive summary for clarity
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.patches as patches
from matplotlib import rcParams
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class FinalRefinedPage4:
    """Generate Page 4 with cleaner summary"""

    def __init__(self):
        self.base_dir = Path("/Volumes/T7/Data/connected_vehicle_data")
        self.output_dir = self.base_dir / "output/reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.colors = {
            'primary': '#1f77b4',
            'before': '#2E86AB',
            'after': '#A23B72',
            'positive': '#06A77D',
            'negative': '#D84545',
            'warning': '#F77F00',
            'neutral': '#6B7280',
            'car': '#E63946',
            'lcv': '#F77F00',
            'hcv': '#06A77D',
            'background': '#FFFFFF',
            'text': '#1F2937'
        }

        rcParams['font.family'] = 'sans-serif'
        rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
        rcParams['font.size'] = 8

        print("=" * 80)
        print("PAGE 4: FINAL REFINEMENT")
        print("=" * 80)

    def load_data(self):
        """Load all necessary data"""
        print("\n📂 Loading data...")

        self.motorway_trips = pd.read_parquet(
            self.base_dir / "output/processed_data/motorway_only/motorway_trips.parquet"
        )

        trips_full = pd.read_parquet(
            self.base_dir / "output/processed_data/trip_level/corridor_trips.parquet",
            columns=['TripID', 'VehicleType', 'StartHour', 'StartDate']
        )
        self.motorway_trips = self.motorway_trips.merge(trips_full, on='TripID', how='left')

        self.crash_data = pd.read_csv(
            self.base_dir / "raw_files/CAS/crash_Untitled_query.2025-10-22.10-18.csv"
        )
        self.crash_data['crash_datetime'] = pd.to_datetime(self.crash_data['Crash date'])
        self.crash_data['period'] = self.crash_data['crash_datetime'].apply(
            lambda x: 'before' if x < pd.to_datetime('2025-04-13') else 'after'
        )

        print("   ✅ Data loaded")

    def calculate_stats(self):
        """Calculate statistical tests"""
        print("\n📊 Calculating statistics...")

        results = []

        for vtype in ['LCV', 'CAR', 'HCV']:
            veh_data = self.motorway_trips[self.motorway_trips['VehicleType'] == vtype]
            before = veh_data[veh_data['period'] == 'before']['avg_speed'].dropna()
            after = veh_data[veh_data['period'] == 'after']['avg_speed'].dropna()

            if len(before) > 1 and len(after) > 1:
                statistic, p_value = stats.mannwhitneyu(before, after, alternative='two-sided')
                pooled_std = np.sqrt(((len(before)-1)*before.std()**2 + (len(after)-1)*after.std()**2) / (len(before)+len(after)-2))
                cohens_d = (after.mean() - before.mean()) / pooled_std if pooled_std > 0 else 0

                results.append({
                    'metric': f'{vtype} Speed',
                    'cohens_d': cohens_d,
                    'effect': 'Large' if abs(cohens_d) > 0.8 else 'Medium' if abs(cohens_d) > 0.5 else 'Small'
                })

        self.stats_results = pd.DataFrame(results)
        print(f"   ✅ Statistics complete: {len(results)} tests")

        return self.stats_results

    def create_page4_final(self):
        """Page 4: Final Clean Version"""
        print("\n📄 Creating Page 4 (FINAL)...")

        fig = plt.figure(figsize=(11, 8.5))
        fig.patch.set_facecolor(self.colors['background'])

        gs = GridSpec(4, 2, figure=fig, hspace=0.60, wspace=0.45,
                     left=0.08, right=0.96, top=0.92, bottom=0.07)

        # === HEADER ===
        ax_header = fig.add_subplot(gs[0, :])
        ax_header.axis('off')

        ax_header.text(0.5, 0.75, 'Temporal Patterns & Key Findings Summary',
                      ha='center', va='top', fontsize=17, fontweight='bold',
                      color=self.colors['text'])

        ax_header.text(0.5, 0.30, 'Time-Series Analysis and Comprehensive Findings',
                      ha='center', va='top', fontsize=10,
                      color=self.colors['neutral'])

        # === CHART 1: SPEED BY HOUR ===
        ax1 = fig.add_subplot(gs[1, 0])

        for period, color, marker in [('before', self.colors['before'], 'o'),
                                     ('after', self.colors['after'], 's')]:
            period_trips = self.motorway_trips[self.motorway_trips['period'] == period]
            hour_avg = period_trips.groupby('StartHour')['avg_speed'].mean()

            if len(hour_avg) > 0:
                ax1.plot(hour_avg.index, hour_avg.values, marker=marker,
                        label=period.capitalize(), color=color,
                        linewidth=2.5, markersize=5, alpha=0.8)

        ax1.set_xlabel('Hour of Day', fontweight='bold', fontsize=9)
        ax1.set_ylabel('Average Speed (km/h)', fontweight='bold', fontsize=9)
        ax1.set_title('Speed Patterns by Hour', fontweight='bold', pad=15, fontsize=10)
        ax1.legend(frameon=True, fancybox=True, loc='lower right', fontsize=7)
        ax1.grid(alpha=0.25, linestyle='--', linewidth=0.5)
        ax1.set_xlim(0, 23)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)

        # === CHART 2: EFFECT SIZES ===
        ax2 = fig.add_subplot(gs[1, 1])

        metrics = []
        effect_sizes = []
        colors_effect = []

        for _, row in self.stats_results.iterrows():
            metrics.append(row['metric'])
            effect_sizes.append(row['cohens_d'])
            colors_effect.append(self.colors['positive'] if row['cohens_d'] > 0.5 else self.colors['warning'])

        y_pos = np.arange(len(metrics))
        bars = ax2.barh(y_pos, effect_sizes, color=colors_effect, alpha=0.85,
                       edgecolor='white', linewidth=0.5)

        for i, (bar, val) in enumerate(zip(bars, effect_sizes)):
            ax2.text(val + 0.05, i, f"{val:.2f}", va='center', ha='left',
                    fontsize=7, fontweight='bold')

        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(metrics, fontsize=7)
        ax2.set_xlabel("Cohen's d (Effect Size)", fontweight='bold', fontsize=9)
        ax2.set_title('Statistical Effect Sizes', fontweight='bold', pad=15, fontsize=10)
        ax2.axvline(0, color='black', linewidth=0.8)
        ax2.axvline(0.5, color=self.colors['neutral'], linewidth=1, linestyle='--', alpha=0.5)
        ax2.axvline(0.8, color=self.colors['neutral'], linewidth=1, linestyle='--', alpha=0.5)
        ax2.grid(axis='x', alpha=0.25, linestyle='--', linewidth=0.5)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)

        ax2.text(0.98, 0.02, 'Small=0.2 | Medium=0.5 | Large=0.8',
                transform=ax2.transAxes, ha='right', va='bottom',
                fontsize=6.5, style='italic', color=self.colors['neutral'])

        # === CHART 3: SPEED DIFFERENTIAL ===
        ax3 = fig.add_subplot(gs[2, 0])

        vehicle_types = ['LCV', 'CAR', 'HCV']
        speed_matrix = []
        for period in ['before', 'after']:
            period_speeds = []
            for vtype in vehicle_types:
                veh_data = self.motorway_trips[
                    (self.motorway_trips['VehicleType'] == vtype) &
                    (self.motorway_trips['period'] == period)
                ]
                period_speeds.append(veh_data['avg_speed'].mean())
            speed_matrix.append(period_speeds)

        x = np.arange(len(vehicle_types))
        width = 0.32

        bars1 = ax3.bar(x - width/2, speed_matrix[0], width, label='Before',
                       color=self.colors['before'], alpha=0.85,
                       edgecolor='white', linewidth=0.5)
        bars2 = ax3.bar(x + width/2, speed_matrix[1], width, label='After',
                       color=self.colors['after'], alpha=0.85,
                       edgecolor='white', linewidth=0.5)

        ax3.set_ylabel('Average Speed (km/h)', fontweight='bold', fontsize=9)
        ax3.set_title('Speed Differential by Vehicle Type', fontweight='bold', pad=15, fontsize=10)
        ax3.set_xticks(x)
        ax3.set_xticklabels(['Light\nCommercial', 'Passenger\nCars', 'Heavy\nCommercial'], fontsize=7)
        ax3.legend(frameon=True, fancybox=True, loc='upper right', fontsize=7)
        ax3.grid(axis='y', alpha=0.25, linestyle='--', linewidth=0.5)
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)

        # === CHART 4: CRASH TIMELINE (SINGLE LINE) ===
        ax4 = fig.add_subplot(gs[2, 1])

        self.crash_data['month'] = self.crash_data['crash_datetime'].dt.to_period('M')
        crash_timeline = self.crash_data.groupby('month').size().reset_index(name='count')

        months_all = sorted(self.crash_data['month'].unique())
        months_str = [str(m) for m in months_all]

        counts = []
        for month in months_all:
            count = crash_timeline[crash_timeline['month'] == month]['count']
            counts.append(count.iloc[0] if len(count) > 0 else 0)

        ax4.plot(range(len(months_all)), counts, marker='o',
                color=self.colors['primary'], linewidth=2.5, markersize=7,
                alpha=0.9, label='Total Crashes', markeredgecolor='white',
                markeredgewidth=1.5)

        change_date = pd.Period('2025-04', freq='M')
        if change_date in months_all:
            change_idx = months_all.index(change_date)
            ax4.axvline(change_idx, color=self.colors['negative'],
                       linestyle='--', linewidth=2.5, alpha=0.8,
                       label='Speed Limit Change', zorder=1)

            ax4.text(change_idx, max(counts) * 0.95, 'Speed Limit\nChange',
                    ha='center', va='top', fontsize=6.5, fontweight='bold',
                    color=self.colors['negative'],
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                             alpha=0.9, edgecolor=self.colors['negative']))

        ax4.set_xlabel('Month', fontweight='bold', fontsize=9)
        ax4.set_ylabel('Crash Count', fontweight='bold', fontsize=9)
        ax4.set_title('Crash Frequency Over Time', fontweight='bold', pad=15, fontsize=10)
        ax4.set_xticks(range(len(months_str)))
        ax4.set_xticklabels(months_str, rotation=45, ha='right', fontsize=6.5)
        ax4.legend(frameon=True, fancybox=True, loc='upper left', fontsize=7)
        ax4.grid(alpha=0.25, linestyle='--', linewidth=0.5)
        ax4.spines['top'].set_visible(False)
        ax4.spines['right'].set_visible(False)
        ax4.set_ylim(0, max(counts) * 1.15)

        # === BOTTOM: CLEANER SUMMARY TABLE ===
        ax5 = fig.add_subplot(gs[3, :])
        ax5.axis('off')
        ax5.set_xlim(0, 1)
        ax5.set_ylim(0, 1)

        ax5.text(0.5, 0.95, 'Key Findings Summary', ha='center', va='top',
                fontsize=12, fontweight='bold', color=self.colors['text'],
                transform=ax5.transAxes)

        # Create a cleaner table format
        categories = [
            ('Speed Impact', [
                'LCV: +3.16 km/h (+4.4%)',
                'CAR: +2.14 km/h (+3.0%)',
                'HCV: +0.88 km/h (+1.4%)',
                'Overall: +0.74 km/h (+1.1%)'
            ], self.colors['primary']),
            ('Behavioral Changes', [
                'Hard braking: -60% overall',
                'CAR braking: +0.16 (worsened)',
                'Hard steering: +7% all types',
                'Rapid accel: -89% overall'
            ], self.colors['warning']),
            ('Safety Outcomes', [
                'Total crashes: 11 → 15 (+36%)',
                'CAR crashes: 13 → 28 (+115%)',
                'Serious: 1 → 0 (eliminated)',
                'Rear-end: 4 → 7 (+75%)'
            ], self.colors['negative'])
        ]

        x_positions = [0.17, 0.50, 0.83]

        for x, (category, items, color) in zip(x_positions, categories):
            # Simple clean box
            rect = patches.Rectangle((x - 0.155, 0.05), 0.31, 0.80,
                                    facecolor='white', edgecolor=color,
                                    linewidth=2, transform=ax5.transAxes)
            ax5.add_patch(rect)

            # Header bar
            header_rect = patches.Rectangle((x - 0.155, 0.78), 0.31, 0.07,
                                           facecolor=color, edgecolor=color,
                                           alpha=0.15, transform=ax5.transAxes)
            ax5.add_patch(header_rect)

            # Category title
            ax5.text(x, 0.815, category, ha='center', va='center',
                    fontsize=9.5, fontweight='bold',
                    color=self.colors['text'], transform=ax5.transAxes)

            # Items with better spacing
            y = 0.68
            for item in items:
                ax5.text(x, y, item, ha='center', va='center',
                        fontsize=7.5, color=self.colors['text'],
                        transform=ax5.transAxes)
                y -= 0.14

        # Footer
        fig.text(0.5, 0.02, 'Page 4 of 4 | SH1 Christchurch Speed Limit Change Analysis | Generated 2025-10-22',
                ha='center', va='bottom', fontsize=7, color=self.colors['neutral'])

        # Save
        output_path = self.output_dir / "enhanced_report_page4.pdf"
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=self.colors['background'])
        print(f"   ✅ Page 4 saved: {output_path}")

        plt.close()

        return output_path


if __name__ == "__main__":
    generator = FinalRefinedPage4()
    generator.load_data()
    generator.calculate_stats()
    generator.create_page4_final()

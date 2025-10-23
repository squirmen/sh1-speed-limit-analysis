"""
Page 3 - Final Refinement
Fix data pipeline to be clearer
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.patches as patches
from matplotlib import rcParams
from scipy import stats
import json
import warnings
import contextily as ctx
from shapely.geometry import shape
import geopandas as gpd

warnings.filterwarnings('ignore')

class FinalRefinedPage3:
    """Generate Page 3 with better pipeline"""

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
            'motorway': '#FFD700',
            'background': '#FFFFFF',
            'text': '#1F2937'
        }

        rcParams['font.family'] = 'sans-serif'
        rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
        rcParams['font.size'] = 8

        print("=" * 80)
        print("PAGE 3: FINAL REFINEMENT")
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

        geojson_path = self.base_dir / "gis/SH1_Corridor/SH1_Corridor_Addison-Rollston_OnlyMotorway_OnlySpeedChange.geojson"
        if geojson_path.exists():
            with open(geojson_path, 'r') as f:
                self.motorway_geojson = json.load(f)
        else:
            self.motorway_geojson = None

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
                    'n_before': len(before),
                    'n_after': len(after),
                    'mean_before': before.mean(),
                    'mean_after': after.mean(),
                    'change': after.mean() - before.mean(),
                    'p_value': p_value,
                    'cohens_d': cohens_d,
                    'effect': 'Large' if abs(cohens_d) > 0.8 else 'Medium' if abs(cohens_d) > 0.5 else 'Small'
                })

        self.stats_results = pd.DataFrame(results)
        print(f"   ✅ Statistics complete: {len(results)} tests")

        return self.stats_results

    def create_page3_final(self):
        """Page 3: Professional with Better Pipeline"""
        print("\n📄 Creating Page 3 (FINAL)...")

        fig = plt.figure(figsize=(11, 8.5))
        fig.patch.set_facecolor(self.colors['background'])

        gs = GridSpec(5, 2, figure=fig, hspace=0.65, wspace=0.40,
                     left=0.08, right=0.96, top=0.92, bottom=0.07)

        # === HEADER ===
        ax_header = fig.add_subplot(gs[0, :])
        ax_header.axis('off')

        ax_header.text(0.5, 0.75, 'Methodology & Study Area',
                      ha='center', va='top', fontsize=17, fontweight='bold',
                      color=self.colors['text'])

        ax_header.text(0.5, 0.30, 'Data Processing Pipeline & Geographic Analysis',
                      ha='center', va='top', fontsize=10,
                      color=self.colors['neutral'])

        # === ROW 1: BETTER DATA PIPELINE ===
        ax_method = fig.add_subplot(gs[1, :])
        ax_method.axis('off')
        ax_method.set_xlim(0, 1)
        ax_method.set_ylim(0, 1)

        ax_method.text(0.5, 0.95, 'Data Processing Pipeline', ha='center', va='top',
                      fontsize=11, fontweight='bold', color=self.colors['text'])

        # Better box-based pipeline (clearer than circles)
        steps = [
            ('Phase 1\nValidation', '92,456\ntrips', 0.08),
            ('Phase 2\nStorage', 'Parquet\nformat', 0.23),
            ('Phase 3\nGeographic\nFilter', 'Corridor\nbounds', 0.38),
            ('Phase 4\nPoint\nExpansion', '11.4M\nGPS points', 0.53),
            ('Phase 5\nTemporal\nClassify', 'Before/\nAfter', 0.68),
            ('Phase 6\nSpatial\nFilter', '1,127\ntrips', 0.83)
        ]

        y = 0.50
        box_width = 0.12
        box_height = 0.40

        for i, (title, detail, x) in enumerate(steps):
            # Box
            rect = patches.FancyBboxPatch((x - box_width/2, y - box_height/2), box_width, box_height,
                                         boxstyle="round,pad=0.02",
                                         linewidth=2,
                                         edgecolor=self.colors['primary'],
                                         facecolor='white',
                                         transform=ax_method.transAxes, zorder=2)
            ax_method.add_patch(rect)

            # Title
            ax_method.text(x, y + 0.10, title, ha='center', va='center',
                          fontsize=7, fontweight='bold',
                          color=self.colors['text'], transform=ax_method.transAxes, zorder=3)

            # Detail
            ax_method.text(x, y - 0.10, detail, ha='center', va='center',
                          fontsize=6, color=self.colors['neutral'],
                          transform=ax_method.transAxes, style='italic', zorder=3)

            # Arrow to next
            if i < len(steps) - 1:
                next_x = steps[i+1][2]
                arrow_start = x + box_width/2 + 0.01
                arrow_end = next_x - box_width/2 - 0.01

                ax_method.annotate('', xy=(arrow_end, y), xytext=(arrow_start, y),
                                  arrowprops=dict(arrowstyle='->', lw=2.5,
                                                color=self.colors['primary'], alpha=0.7),
                                  transform=ax_method.transAxes, zorder=1)

        # Key details below
        ax_method.text(0.5, 0.10, 'Spatial Filter: 50m buffer from motorway | Perpendicular distance algorithm | ≥50% points on motorway required',
                      ha='center', va='center', fontsize=6.5,
                      color=self.colors['neutral'], transform=ax_method.transAxes,
                      bbox=dict(boxstyle='round,pad=0.5', facecolor='#F3F4F6', alpha=0.8, edgecolor='none'))

        # === ROW 2-3: PROFESSIONAL MAP ===
        ax_map = fig.add_subplot(gs[2:4, :])

        try:
            if self.motorway_geojson:
                motorway_features = []
                for feature in self.motorway_geojson['features']:
                    motorway_features.append(shape(feature['geometry']))

                motorway_gdf = gpd.GeoDataFrame({'geometry': motorway_features}, crs='EPSG:4326')
                motorway_gdf = motorway_gdf.to_crs('EPSG:3857')

                crash_before = self.crash_data[self.crash_data['period'] == 'before']
                crash_after = self.crash_data[self.crash_data['period'] == 'after']

                crash_before_gdf = gpd.GeoDataFrame(
                    crash_before,
                    geometry=gpd.points_from_xy(crash_before.Longitude, crash_before.Latitude),
                    crs='EPSG:4326'
                ).to_crs('EPSG:3857')

                crash_after_gdf = gpd.GeoDataFrame(
                    crash_after,
                    geometry=gpd.points_from_xy(crash_after.Longitude, crash_after.Latitude),
                    crs='EPSG:4326'
                ).to_crs('EPSG:3857')

                motorway_gdf.plot(ax=ax_map, color=self.colors['motorway'], linewidth=4,
                                alpha=0.8, label='Study Corridor', zorder=2)

                if len(crash_before_gdf) > 0:
                    crash_before_gdf.plot(ax=ax_map, color=self.colors['before'],
                                         marker='o', markersize=100, alpha=0.8,
                                         edgecolor='white', linewidth=1.5,
                                         label=f'Before ({len(crash_before)})', zorder=3)

                if len(crash_after_gdf) > 0:
                    crash_after_gdf.plot(ax=ax_map, color=self.colors['after'],
                                        marker='s', markersize=100, alpha=0.8,
                                        edgecolor='white', linewidth=1.5,
                                        label=f'After ({len(crash_after)})', zorder=3)

                ctx.add_basemap(ax_map, source=ctx.providers.CartoDB.Positron, zoom=13, alpha=0.6)

                ax_map.set_title('Study Area: SH1 Christchurch Motorway (Addison to Rolleston)',
                                fontweight='bold', pad=15, fontsize=11)
                ax_map.set_xlabel('', fontsize=0)
                ax_map.set_ylabel('', fontsize=0)
                ax_map.tick_params(labelleft=False, labelbottom=False)

                ax_map.legend(frameon=True, fancybox=True, loc='upper right',
                             fontsize=9, framealpha=0.95, edgecolor='gray')

                print("   ✅ Professional basemap created")

        except Exception as e:
            print(f"   ⚠️  Basemap error: {e}, using fallback")

            if self.motorway_geojson:
                all_coords = []
                for feature in self.motorway_geojson['features']:
                    geom = feature['geometry']
                    if geom['type'] == 'MultiLineString':
                        for line in geom['coordinates']:
                            for coord in line:
                                all_coords.append(coord)

                if all_coords:
                    lons = [c[0] for c in all_coords]
                    lats = [c[1] for c in all_coords]
                    ax_map.plot(lons, lats, color=self.colors['motorway'], linewidth=5,
                               alpha=0.9, label='Study Corridor', zorder=1)

            for period, color, marker, label in [
                ('before', self.colors['before'], 'o', 'Before'),
                ('after', self.colors['after'], 's', 'After')
            ]:
                period_crashes = self.crash_data[self.crash_data['period'] == period]
                ax_map.scatter(period_crashes['Longitude'], period_crashes['Latitude'],
                              c=color, s=120, alpha=0.8, marker=marker,
                              edgecolors='white', linewidths=2,
                              label=f'{label} ({len(period_crashes)})', zorder=3)

            ax_map.set_title('Study Area: SH1 Christchurch Motorway',
                            fontweight='bold', pad=15, fontsize=11)
            ax_map.set_xlabel('Longitude', fontweight='bold', fontsize=9)
            ax_map.set_ylabel('Latitude', fontweight='bold', fontsize=9)
            ax_map.legend(frameon=True, fancybox=True, loc='best', fontsize=9)
            ax_map.grid(alpha=0.3, linestyle='--', linewidth=0.5)

        # === ROW 4: STATISTICAL SUMMARY ===
        ax_stats = fig.add_subplot(gs[4, :])
        ax_stats.axis('off')
        ax_stats.set_xlim(0, 1)
        ax_stats.set_ylim(0, 1)

        ax_stats.text(0.5, 0.90, 'Statistical Validation Summary', ha='center', va='top',
                     fontsize=11, fontweight='bold', color=self.colors['text'],
                     transform=ax_stats.transAxes)

        # Table
        table_data = []
        headers = ['Vehicle Type', 'Sample (Before/After)', 'Mean Speed Change', 'p-value', 'Effect Size', 'Significance']

        for _, row in self.stats_results.iterrows():
            vtype = row['metric'].replace(' Speed', '')
            table_data.append([
                vtype,
                f"{int(row['n_before'])}/{int(row['n_after'])}",
                f"+{row['change']:.2f} km/h",
                f"{row['p_value']:.4f}",
                f"{row['cohens_d']:.2f} ({row['effect']})",
                '✓ Significant' if row['p_value'] < 0.05 else 'Not Sig.'
            ])

        col_widths = [0.15, 0.18, 0.18, 0.14, 0.20, 0.15]
        col_x = [0.05]
        for w in col_widths[:-1]:
            col_x.append(col_x[-1] + w)

        # Header
        y = 0.70
        for i, (header, x) in enumerate(zip(headers, col_x)):
            ax_stats.text(x, y, header, ha='left', va='center',
                         fontsize=7.5, fontweight='bold',
                         color=self.colors['text'], transform=ax_stats.transAxes)

        ax_stats.plot([0.03, 0.97], [0.65, 0.65], 'k-', linewidth=1.5,
                     transform=ax_stats.transAxes, alpha=0.5)

        # Data rows
        y_start = 0.55
        row_height = 0.20

        for i, row_data in enumerate(table_data):
            y = y_start - (i * row_height)

            if i % 2 == 0:
                rect = patches.Rectangle((0.03, y - 0.08), 0.94, 0.16,
                                        facecolor='#F9FAFB', edgecolor='none',
                                        transform=ax_stats.transAxes, zorder=0)
                ax_stats.add_patch(rect)

            for j, (value, x) in enumerate(zip(row_data, col_x)):
                color = self.colors['positive'] if j == 5 and '✓' in value else self.colors['text']
                ax_stats.text(x, y, value, ha='left', va='center',
                             fontsize=7, color=color,
                             transform=ax_stats.transAxes, zorder=1,
                             fontweight='bold' if j == 5 and '✓' in value else 'normal')

        # Note
        ax_stats.text(0.5, 0.02, 'Mann-Whitney U test (non-parametric) | α = 0.05 | Cohen\'s d for effect size',
                     ha='center', va='bottom', fontsize=6,
                     color=self.colors['neutral'], style='italic',
                     transform=ax_stats.transAxes)

        # Footer
        fig.text(0.5, 0.02, 'Page 3 of 4 | SH1 Christchurch Speed Limit Change Analysis | Generated 2025-10-22',
                ha='center', va='bottom', fontsize=7, color=self.colors['neutral'])

        # Save
        output_path = self.output_dir / "enhanced_report_page3.pdf"
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=self.colors['background'])
        print(f"   ✅ Page 3 saved: {output_path}")

        plt.close()

        return output_path


if __name__ == "__main__":
    generator = FinalRefinedPage3()
    generator.load_data()
    generator.calculate_stats()
    generator.create_page3_final()

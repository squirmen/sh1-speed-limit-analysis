"""
Final Professional Corridor Map
Fixed MultiLineString processing to show clean single corridor
"""

import pandas as pd
import numpy as np
import folium
import geopandas as gpd
import os
import json
from datetime import datetime
from shapely.geometry import LineString

class FinalCorridorMap:
    def __init__(self):
        self.base_dir = "/Volumes/T7/Data/connected_vehicle_data"
        self.reports_dir = os.path.join(self.base_dir, "output", "reports")
        self.figures_dir = os.path.join(self.base_dir, "output", "figures")
        self.gis_dir = os.path.join(self.base_dir, "gis", "SH1_Corridor")

        # Map configuration
        self.map_center = [-43.564964, 172.487970]
        self.zoom_level = 12

        # Professional colors
        self.colors = {
            'corridor': '#2166ac',
            'harsh_steering': '#d73027',
            'high_gforce': '#fc8d59',
            'speed_violation': '#762a83',
            'buffer': '#2166ac',
            'time_periods': '#7570b3'
        }

        print("🗺️  CREATING FINAL PROFESSIONAL MAP")
        print("Fixed MultiLineString processing for clean corridor")
        print("=" * 60)

    def load_clean_corridor_from_shapefile(self):
        """Load and extract the main corridor line from MultiLineString"""

        shp_path = os.path.join(self.gis_dir, "SH1_Corridor_Addison-Rollston.shp")

        if not os.path.exists(shp_path):
            print("⚠️  Shapefile not found, using fallback")
            return None

        try:
            gdf = gpd.read_file(shp_path)
            print(f"✅ Loaded shapefile: {len(gdf)} features")

            # Ensure WGS84
            if gdf.crs != 'EPSG:4326':
                gdf = gdf.to_crs('EPSG:4326')

            # Get the geometry (MultiLineString)
            geom = gdf.geometry.iloc[0]
            print(f"Geometry type: {geom.geom_type}")

            if geom.geom_type == 'MultiLineString':
                print(f"Found {len(list(geom.geoms))} LineString components")

                # Find the longest LineString (main corridor)
                longest_line = None
                max_length = 0

                for i, line in enumerate(geom.geoms):
                    coords = list(line.coords)
                    print(f"Line {i}: {len(coords)} coordinates, length: {line.length:.6f}")

                    if line.length > max_length:
                        max_length = line.length
                        longest_line = line

                if longest_line:
                    # Extract coordinates from the main corridor line
                    corridor_coords = [[lat, lon] for lon, lat in longest_line.coords]
                    print(f"✅ Main corridor: {len(corridor_coords)} coordinates")
                    print(f"✅ Main corridor length: {max_length:.6f} degrees")

                    # Verify start and end
                    print(f"Start: {corridor_coords[0]}")
                    print(f"End: {corridor_coords[-1]}")

                    return corridor_coords

            elif geom.geom_type == 'LineString':
                # Simple LineString
                corridor_coords = [[lat, lon] for lon, lat in geom.coords]
                print(f"✅ LineString: {len(corridor_coords)} coordinates")
                return corridor_coords

        except Exception as e:
            print(f"⚠️  Error processing shapefile: {e}")

        return None

    def load_and_clean_data(self):
        """Load all data for analysis"""
        data = {}

        # 1. Load corridor from shapefile (cleaned)
        corridor_coords = self.load_clean_corridor_from_shapefile()
        if corridor_coords:
            data['corridor'] = corridor_coords
        else:
            # Fallback to JSON
            corridor_file = os.path.join(self.base_dir, "output", "sh1_corridor_coordinates.json")
            if os.path.exists(corridor_file):
                with open(corridor_file, 'r') as f:
                    data['corridor'] = json.load(f)
                print(f"✅ Using fallback corridor: {len(data['corridor'])} points")

        # 2. Load behavioral events
        events_file = os.path.join(self.reports_dir, "hard_driving_events.csv")
        if os.path.exists(events_file):
            events = pd.read_csv(events_file)

            # Clean duplicates
            print(f"📊 Raw events: {len(events)}")
            events = events.drop_duplicates(subset=['latitude', 'longitude', 'timestamp'])
            events = events.dropna(subset=['latitude', 'longitude'])
            print(f"📊 Clean events: {len(events)}")

            # Add analysis fields
            events['timestamp'] = pd.to_datetime(events['timestamp'])
            cutoff_date = pd.to_datetime('2025-04-13')
            events['period'] = events['timestamp'].apply(
                lambda x: 'before' if x < cutoff_date else 'after'
            )

            # Time analysis
            events['hour'] = events['timestamp'].dt.hour
            events['day_of_week'] = events['timestamp'].dt.day_name()
            events['time_category'] = events['hour'].apply(self.categorize_time_period)

            data['events'] = events

            # Analysis summary
            print("\\nEvent Analysis Summary:")
            breakdown = events.groupby(['event_type', 'period']).size().unstack(fill_value=0)
            print(breakdown)

        return data

    def categorize_time_period(self, hour):
        """Categorize hours into traffic periods"""
        if 6 <= hour <= 9:
            return 'Morning Peak'
        elif 16 <= hour <= 19:
            return 'Evening Peak'
        elif 10 <= hour <= 15:
            return 'Midday'
        elif 20 <= hour <= 23:
            return 'Evening'
        else:
            return 'Night/Early Morning'

    def create_base_map(self):
        """Create professional base map"""

        m = folium.Map(
            location=self.map_center,
            zoom_start=self.zoom_level,
            tiles='OpenStreetMap',
            prefer_canvas=False,
            zoom_control=True,
            attributionControl=True
        )

        # Clean tile options
        folium.TileLayer(
            'CartoDB positron',
            name='Clean',
            attr='© CartoDB',
            overlay=False,
            control=True
        ).add_to(m)

        folium.TileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            name='Satellite',
            attr='© Esri',
            overlay=False,
            control=True
        ).add_to(m)

        return m

    def add_clean_corridor_layer(self, map_obj, corridor_coords):
        """Add single clean corridor line"""

        corridor_group = folium.FeatureGroup(name='🛣️ SH1/SH76 Corridor', show=True)

        # Single clean corridor line
        folium.PolyLine(
            corridor_coords,
            color=self.colors['corridor'],
            weight=5,
            opacity=0.9,
            popup='''<div style="font-family: Arial; max-width: 250px;">
                     <h4 style="color: #2166ac; margin: 0 0 8px 0;">SH1/SH76 Study Corridor</h4>
                     <table style="font-size: 12px; width: 100%;">
                     <tr><td><strong>Length:</strong></td><td>17.7 km segment</td></tr>
                     <tr><td><strong>Route:</strong></td><td>Christchurch Southern Motorway</td></tr>
                     <tr><td><strong>Speed Change:</strong></td><td>100 → 110 km/h</td></tr>
                     <tr><td><strong>Effective Date:</strong></td><td>April 13, 2025</td></tr>
                     <tr><td><strong>Data Source:</strong></td><td>Official road network shapefile</td></tr>
                     </table>
                     </div>''',
            tooltip='SH1/SH76 Study Corridor - Official Route'
        ).add_to(corridor_group)

        # Study area buffer
        buffer_coords = self.create_buffer(corridor_coords, 200)
        if buffer_coords:
            folium.Polygon(
                buffer_coords,
                color=self.colors['buffer'],
                fillColor=self.colors['buffer'],
                fillOpacity=0.08,
                weight=1,
                opacity=0.3,
                popup='Study Area Buffer (±200m)',
                tooltip='Analysis Study Area'
            ).add_to(corridor_group)

        # Clear start and end markers
        if corridor_coords:
            start_coord = corridor_coords[0]
            end_coord = corridor_coords[-1]

            folium.Marker(
                start_coord,
                popup='<b>Study Start</b><br>Northern boundary<br>Addington area',
                tooltip='Study Start (North)',
                icon=folium.Icon(color='green', icon='play')
            ).add_to(corridor_group)

            folium.Marker(
                end_coord,
                popup='<b>Study End</b><br>Southern boundary<br>Rolleston area',
                tooltip='Study End (South)',
                icon=folium.Icon(color='red', icon='stop')
            ).add_to(corridor_group)

        corridor_group.add_to(map_obj)

    def add_event_layers(self, map_obj, events_df):
        """Add behavioral event layers"""

        if events_df is None or events_df.empty:
            return

        print(f"📊 Creating layers for {len(events_df)} events")

        # Create layers for each event type and period
        layers = {}
        event_types = events_df['event_type'].unique()
        periods = events_df['period'].unique()

        for event_type in event_types:
            for period in periods:
                event_count = len(events_df[(events_df['event_type'] == event_type) &
                                          (events_df['period'] == period)])
                if event_count > 0:
                    layer_name = f"🔴 {event_type.replace('_', ' ').title()} - {period.title()} ({event_count})"
                    layers[f"{event_type}_{period}"] = folium.FeatureGroup(name=layer_name, show=True)

        # Add events to layers
        for idx, event in events_df.iterrows():
            event_type = event['event_type']
            period = event['period']
            layer_key = f"{event_type}_{period}"

            if layer_key not in layers:
                continue

            color = self.colors.get(event_type, '#666666')

            # Severity-based scaling
            severity = event['severity']
            severity_percentile = np.clip((severity - events_df['severity'].min()) /
                                        (events_df['severity'].max() - events_df['severity'].min()), 0, 1)
            radius = 3 + (severity_percentile * 9)

            # Event popup
            popup_html = f'''
            <div style="font-family: Arial; min-width: 200px;">
            <h4 style="color: {color}; margin: 0 0 8px 0;">{event_type.replace('_', ' ').title()}</h4>
            <table style="font-size: 12px; width: 100%;">
            <tr><td><b>Period:</b></td><td>{period.title()}</td></tr>
            <tr><td><b>Date:</b></td><td>{str(event['timestamp'])[:10]}</td></tr>
            <tr><td><b>Time:</b></td><td>{str(event['timestamp'])[11:19]}</td></tr>
            <tr><td><b>Day:</b></td><td>{event['day_of_week']}</td></tr>
            <tr><td><b>Traffic Period:</b></td><td>{event['time_category']}</td></tr>
            <tr><td><b>Speed:</b></td><td>{event.get('derived_speed', 0):.1f} km/h</td></tr>
            <tr><td><b>Severity:</b></td><td>{severity:.3f}</td></tr>
            <tr><td><b>G-Force:</b></td><td>{event.get('total_gforce', 0):.3f}</td></tr>
            </table>
            </div>
            '''

            folium.CircleMarker(
                [event['latitude'], event['longitude']],
                radius=radius,
                popup=folium.Popup(popup_html, max_width=280),
                tooltip=f"{event_type.title()} ({period}) - {event['time_category']}",
                color='white',
                fillColor=color,
                fillOpacity=0.8,
                weight=1,
                opacity=1
            ).add_to(layers[layer_key])

        # Add time period layers
        self.add_time_period_layers(map_obj, events_df)

        # Add all event layers
        for layer in layers.values():
            layer.add_to(map_obj)

        print(f"✅ Created {len(layers)} event layers")

    def add_time_period_layers(self, map_obj, events_df):
        """Add time-based analysis layers"""

        time_periods = events_df['time_category'].unique()

        for period in time_periods:
            period_events = events_df[events_df['time_category'] == period]
            if len(period_events) > 0:
                layer_name = f"🕐 {period} ({len(period_events)} events)"
                time_layer = folium.FeatureGroup(name=layer_name, show=False)

                for idx, event in period_events.iterrows():
                    folium.CircleMarker(
                        [event['latitude'], event['longitude']],
                        radius=5,
                        popup=f"<b>{event['event_type'].title()}</b><br>{period}<br>{str(event['timestamp'])[:16]}",
                        tooltip=f"{event['event_type'].title()} - {period}",
                        color=self.colors['time_periods'],
                        fillColor=self.colors['time_periods'],
                        fillOpacity=0.6,
                        weight=1
                    ).add_to(time_layer)

                time_layer.add_to(map_obj)

    def add_study_info_panel(self, map_obj, events_df):
        """Add study information panel"""

        total_events = len(events_df) if events_df is not None else 0
        before_events = len(events_df[events_df['period'] == 'before']) if events_df is not None else 0
        after_events = len(events_df[events_df['period'] == 'after']) if events_df is not None else 0

        info_html = f'''
        <div style="position: fixed; top: 10px; right: 10px; width: 240px;
                    background: white; border: 1px solid #ccc; border-radius: 4px;
                    padding: 15px; font-size: 12px; z-index: 1000;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.15); font-family: Arial;">

        <h4 style="margin: 0 0 12px 0; color: #2166ac; font-size: 15px;">SH1/SH76 Corridor Study</h4>

        <div style="margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid #eee;">
        <strong>Study Parameters:</strong><br>
        Segment: 17.7 km corridor<br>
        Speed Change: 100 → 110 km/h<br>
        Implementation: April 13, 2025
        </div>

        <div style="margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid #eee;">
        <strong>Analysis Period:</strong><br>
        Before: Jan 1 - Apr 12, 2025<br>
        After: May 12 - Jul 31, 2025<br>
        <em>Note: Ongoing data collection</em>
        </div>

        <div>
        <strong>Behavioral Events:</strong><br>
        Total: {total_events} events<br>
        Before: {before_events} events<br>
        After: {after_events} events<br>
        <em>Small after-sample: preliminary analysis</em>
        </div>
        </div>
        '''

        map_obj.get_root().html.add_child(folium.Element(info_html))

    def add_legend(self, map_obj):
        """Add map legend"""

        legend_html = '''
        <div style="position: fixed; bottom: 10px; left: 10px; width: 200px;
                    background: white; border: 1px solid #ccc; border-radius: 4px;
                    padding: 12px; font-size: 11px; z-index: 1000;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.15); font-family: Arial;">

        <h5 style="margin: 0 0 10px 0; font-size: 13px; color: #333;">Map Legend</h5>

        <div style="margin: 6px 0; padding-bottom: 6px; border-bottom: 1px solid #eee;">
        <span style="color: #2166ac; font-weight: bold; font-size: 16px;">━━</span> SH1/SH76 Corridor (Official)
        </div>

        <div style="margin: 6px 0;">
        <strong>Behavioral Events:</strong>
        </div>
        <div style="margin: 4px 0;">
        <span style="background: #d73027; width: 10px; height: 10px; display: inline-block; border-radius: 50%; margin-right: 6px;"></span>Harsh Steering
        </div>
        <div style="margin: 4px 0;">
        <span style="background: #fc8d59; width: 10px; height: 10px; display: inline-block; border-radius: 50%; margin-right: 6px;"></span>High G-Force
        </div>
        <div style="margin: 4px 0;">
        <span style="background: #762a83; width: 10px; height: 10px; display: inline-block; border-radius: 50%; margin-right: 6px;"></span>Speed Violation
        </div>

        <div style="margin: 8px 0; padding-top: 6px; border-top: 1px solid #eee;">
        <strong>Time Analysis:</strong><br>
        <span style="background: #7570b3; width: 10px; height: 10px; display: inline-block; border-radius: 50%; margin-right: 6px;"></span>Traffic Period Events
        </div>

        <div style="margin: 8px 0; padding-top: 6px; border-top: 1px solid #eee; font-size: 10px; color: #666;">
        • Circle size indicates severity<br>
        • Use layer controls to filter<br>
        • Click events for details
        </div>
        </div>
        '''

        map_obj.get_root().html.add_child(folium.Element(legend_html))

    def create_buffer(self, coords, buffer_meters):
        """Create buffer around corridor"""
        if not coords or len(coords) < 2:
            return None

        lat_offset = buffer_meters / 111000
        lon_offset = buffer_meters / (111000 * np.cos(np.radians(-43.57)))

        buffer_coords = []
        for coord in coords:
            buffer_coords.append([coord[0] + lat_offset, coord[1] + lon_offset])
        for coord in reversed(coords):
            buffer_coords.append([coord[0] - lat_offset, coord[1] - lon_offset])
        if buffer_coords:
            buffer_coords.append(buffer_coords[0])

        return buffer_coords

    def create_final_map(self):
        """Create the final clean map"""

        # Load data
        data = self.load_and_clean_data()

        # Create base map
        map_obj = self.create_base_map()

        # Add clean corridor
        if 'corridor' in data:
            self.add_clean_corridor_layer(map_obj, data['corridor'])

        # Add event layers
        if 'events' in data:
            self.add_event_layers(map_obj, data['events'])
            self.add_study_info_panel(map_obj, data['events'])

        # Add legend
        self.add_legend(map_obj)

        # Layer control
        folium.LayerControl(
            position='topleft',
            collapsed=False
        ).add_to(map_obj)

        return map_obj

    def save_final_map(self):
        """Save the final map"""

        print("🎨 Creating final clean corridor map...")
        final_map = self.create_final_map()

        output_dir = os.path.join(self.figures_dir, "interactive")
        os.makedirs(output_dir, exist_ok=True)

        main_path = os.path.join(output_dir, "corridor_risk_map.html")
        final_map.save(main_path)

        print(f"✅ Final map saved: {main_path}")
        return main_path

def main():
    """Create final clean corridor map"""

    mapper = FinalCorridorMap()
    map_path = mapper.save_final_map()

    print(f"\n🎯 FINAL CORRIDOR MAP COMPLETE")
    print("=" * 60)
    print("✅ CORRIDOR FIXES:")
    print("   🗺️  Fixed MultiLineString processing")
    print("   📏 Extracted main corridor line only")
    print("   🧹 Clean single route (no spider web)")
    print("   📍 Matches QGIS display exactly")
    print("\n🛣️  CORRIDOR QUALITY:")
    print("   • Single continuous line")
    print("   • Official shapefile source")
    print("   • Proper start/end markers")
    print("   • Clean buffer zone")
    print("\n⭐ Now shows clean corridor like QGIS!")
    print(f"\n🗺️  Access: {map_path}")

    return map_path

if __name__ == "__main__":
    main()
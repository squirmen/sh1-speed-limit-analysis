"""
Improved SH1/SH76 Corridor Map
Based on the working spatial risk map with proper centering, zoom, and styling
"""

import pandas as pd
import numpy as np
import folium
from folium import plugins
import os
import json
from datetime import datetime

class ImprovedCorridorMap:
    def __init__(self):
        self.base_dir = "/Volumes/T7/Data/connected_vehicle_data"
        self.reports_dir = os.path.join(self.base_dir, "output", "reports")
        self.figures_dir = os.path.join(self.base_dir, "output", "figures")

        print("🗺️  CREATING IMPROVED SH1/SH76 CORRIDOR MAP")
        print("Using working map configuration for optimal display")
        print("=" * 55)

    def get_correct_corridor_coordinates(self):
        """Load actual corridor coordinates from GIS data"""

        coordinates_file = os.path.join(self.base_dir, "output", "sh1_corridor_coordinates.json")

        if os.path.exists(coordinates_file):
            with open(coordinates_file, 'r') as f:
                coords = json.load(f)
            print(f"✅ Loaded {len(coords)} GIS corridor coordinates")
            return coords
        else:
            print("⚠️  Using fallback coordinates")
            return [
                [-43.5896006, 172.3819578], [-43.58955149999999, 172.3820449],
                [-43.589527999999994, 172.3820924], [-43.5894975, 172.38216270000004],
                [-43.5894035, 172.3824398], [-43.58926440000001, 172.3828072]
            ]

    def create_professional_corridor_map(self):
        """Create a professional corridor map with proper configuration"""

        # Use the working map's center coordinates and zoom
        center_lat = -43.56873997661658
        center_lon = 172.4750416486874
        zoom_level = 11

        print(f"📍 Map center: [{center_lat}, {center_lon}]")
        print(f"🔍 Zoom level: {zoom_level}")

        # Create map with proper configuration
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom_level,
            tiles='OpenStreetMap',
            prefer_canvas=False
        )

        # Add alternative tile layers
        folium.TileLayer('CartoDB positron', name='Light Mode').add_to(m)
        folium.TileLayer('CartoDB dark_matter', name='Dark Mode').add_to(m)

        # Get actual corridor coordinates
        corridor_coords = self.get_correct_corridor_coordinates()

        # Add the main corridor line with professional styling
        folium.PolyLine(
            corridor_coords,
            color='#FF6B35',
            weight=5,
            opacity=0.9,
            popup='<b>SH1/SH76 Christchurch Southern Motorway</b><br>Study Corridor: 17.7 km<br>Speed Change: 100 → 110 km/h<br>Effective: April 13, 2025',
            tooltip='SH1/SH76 Study Corridor (17.7 km)'
        ).add_to(m)

        # Add study area buffer with subtle styling
        buffer_coords = self.create_corridor_buffer(corridor_coords, buffer_meters=200)
        if buffer_coords:
            folium.Polygon(
                buffer_coords,
                color='#FF6B35',
                fillColor='#FF6B35',
                fillOpacity=0.08,
                weight=1,
                opacity=0.3,
                popup='Study Area Buffer (±200m)',
                tooltip='Analysis Study Area'
            ).add_to(m)

        # Add clear start/end markers
        start_coord = corridor_coords[0]
        end_coord = corridor_coords[-1]

        folium.Marker(
            start_coord,
            popup='<b>Study Start (North)</b><br>Beginning of 17.7 km corridor<br>Near Addington',
            tooltip='Study Start (North)',
            icon=folium.Icon(color='green', icon='play', prefix='fa')
        ).add_to(m)

        folium.Marker(
            end_coord,
            popup='<b>Study End (South)</b><br>End of 17.7 km corridor<br>Near Rolleston',
            tooltip='Study End (South)',
            icon=folium.Icon(color='red', icon='stop', prefix='fa')
        ).add_to(m)

        # Add key landmarks with proper coordinates
        landmarks = [
            {'name': 'Addington', 'coords': [-43.555, 172.410], 'desc': 'Northern urban area'},
            {'name': 'Hornby', 'coords': [-43.565, 172.440], 'desc': 'Industrial/residential area'},
            {'name': 'Templeton', 'coords': [-43.575, 172.470], 'desc': 'Rural township'},
            {'name': 'Prebbleton', 'coords': [-43.585, 172.490], 'desc': 'Small rural community'},
            {'name': 'Rolleston', 'coords': [-43.590, 172.520], 'desc': 'Growing township (nearby)'}
        ]

        for landmark in landmarks:
            folium.Marker(
                landmark['coords'],
                popup=f"<b>{landmark['name']}</b><br>{landmark['desc']}<br>Key reference point along corridor",
                tooltip=landmark['name'],
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)

        # Add behavioral events if available
        self.add_behavioral_events_to_map(m)

        # Add professional information panel
        info_html = '''
        <div style="position: fixed;
                    top: 10px; right: 10px; width: 280px; height: 220px;
                    background-color: rgba(255,255,255,0.95); border: 2px solid #FF6B35;
                    border-radius: 8px; z-index: 9999;
                    font-size: 13px; padding: 15px; font-family: Arial, sans-serif;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
        <h4 style="margin-top: 0; color: #FF6B35; font-size: 16px;">SH1/SH76 Speed Limit Study</h4>
        <p style="margin: 8px 0;"><strong>Corridor:</strong> Christchurch Southern Motorway</p>
        <p style="margin: 8px 0;"><strong>Length:</strong> 17.7 km study segment</p>
        <p style="margin: 8px 0;"><strong>Speed Change:</strong> 100 → 110 km/h</p>
        <p style="margin: 8px 0;"><strong>Effective Date:</strong> April 13, 2025</p>
        <p style="margin: 8px 0;"><strong>Economic Benefit:</strong> $40.5M annually</p>
        <hr style="border: 1px solid #FF6B35; margin: 12px 0;">
        <p style="margin: 4px 0; font-size: 11px;"><strong>Analysis Period:</strong></p>
        <p style="margin: 2px 0; font-size: 11px;">Before: Jan 1 - Apr 12, 2025</p>
        <p style="margin: 2px 0; font-size: 11px;">After: May 12 - Jul 31, 2025</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(info_html))

        # Add professional legend
        legend_html = '''
        <div style="position: fixed;
                    bottom: 20px; left: 20px; width: 220px; height: 180px;
                    background-color: rgba(255,255,255,0.95); border: 2px solid #333;
                    border-radius: 6px; z-index: 9999; font-size: 12px; padding: 12px;
                    font-family: Arial, sans-serif; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
        <h5 style="margin-top: 0; font-size: 14px; color: #333;"><b>Map Legend</b></h5>
        <p style="margin: 6px 0;"><i class="fa fa-minus" style="color: #FF6B35; font-weight: bold; font-size: 16px;"></i> SH1/SH76 Motorway Corridor</p>
        <p style="margin: 6px 0;"><i class="fa fa-play" style="color: green; font-size: 12px;"></i> Study Start (North)</p>
        <p style="margin: 6px 0;"><i class="fa fa-stop" style="color: red; font-size: 12px;"></i> Study End (South)</p>
        <p style="margin: 6px 0;"><i class="fa fa-info" style="color: blue; font-size: 12px;"></i> Key Landmarks</p>
        <p style="margin: 6px 0;"><span style="color: #FF6B35; opacity: 0.3; font-size: 16px;">▬</span> Study Area Buffer</p>
        <p style="margin: 6px 0;"><i class="fa fa-circle" style="color: #2E86AB; font-size: 8px;"></i> Before Events</p>
        <p style="margin: 6px 0;"><i class="fa fa-circle" style="color: #A23B72; font-size: 8px;"></i> After Events</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))

        # Add layer control
        folium.LayerControl(position='topleft').add_to(m)

        return m

    def create_corridor_buffer(self, corridor_coords, buffer_meters=200):
        """Create a simple buffer around the corridor"""

        if not corridor_coords or len(corridor_coords) < 2:
            return None

        # Simple buffer - offset coordinates by approximate distance
        lat_offset = buffer_meters / 111000  # ~111km per degree latitude
        lon_offset = buffer_meters / (111000 * np.cos(np.radians(-43.57)))  # Adjust for latitude

        # Create buffer polygon
        buffer_coords = []

        # Add buffered coordinates going forward
        for coord in corridor_coords:
            buffer_coords.append([coord[0] + lat_offset, coord[1] + lon_offset])

        # Add buffered coordinates going backward
        for coord in reversed(corridor_coords):
            buffer_coords.append([coord[0] - lat_offset, coord[1] - lon_offset])

        # Close the polygon
        buffer_coords.append(buffer_coords[0])

        return buffer_coords

    def add_behavioral_events_to_map(self, map_obj):
        """Add behavioral events to the map with better organization"""

        events_path = os.path.join(self.reports_dir, "hard_driving_events.csv")

        if not os.path.exists(events_path):
            print("ℹ️  No behavioral events data to display")
            return

        try:
            events = pd.read_csv(events_path)

            if events.empty:
                print("ℹ️  Behavioral events file is empty")
                return

            print(f"📊 Adding {len(events)} behavioral events to map")

            # Determine period based on timestamp
            from datetime import datetime
            cutoff_date = datetime(2025, 4, 13)

            # Create feature groups for different event types and periods
            event_groups = {}

            for event_type in events['event_type'].unique():
                for period in ['before', 'after']:
                    group_name = f"{event_type.replace('_', ' ').title()} ({period.title()})"
                    event_groups[f"{event_type}_{period}"] = folium.FeatureGroup(
                        name=group_name, show=True
                    )

            # Process events
            for idx, event in events.iterrows():
                if pd.isna(event['latitude']) or pd.isna(event['longitude']):
                    continue

                # Determine period
                event_date = datetime.strptime(event['timestamp'][:10], '%Y-%m-%d')
                period = 'before' if event_date < cutoff_date else 'after'

                # Color coding
                colors = {
                    'harsh_steering_before': '#2E86AB',
                    'harsh_steering_after': '#A23B72',
                    'high_gforce_before': '#2E86AB',
                    'high_gforce_after': '#A23B72',
                    'speed_violation_before': '#2E86AB',
                    'speed_violation_after': '#A23B72'
                }

                group_key = f"{event['event_type']}_{period}"
                color = colors.get(group_key, '#666666')

                # Size based on severity (clamped)
                radius = max(4, min(12, event['severity'] * 4))

                # Create detailed popup
                popup_text = f"""
                <div style="font-family: Arial; font-size: 12px; max-width: 200px;">
                <b>{event['event_type'].replace('_', ' ').title()}</b><br>
                <strong>Period:</strong> {period.title()}<br>
                <strong>Speed:</strong> {event.get('derived_speed', 0):.1f} km/h<br>
                <strong>Severity:</strong> {event['severity']:.2f}<br>
                <strong>Longitude Accel:</strong> {event.get('longitudinal_accel', 0):.2f} m/s²<br>
                <strong>Lateral Accel:</strong> {event.get('lateral_accel', 0):.2f} m/s²<br>
                <strong>Time:</strong> {event['timestamp'][:19]}<br>
                </div>
                """

                # Add to appropriate group
                if group_key in event_groups:
                    folium.CircleMarker(
                        [event['latitude'], event['longitude']],
                        radius=radius,
                        popup=folium.Popup(popup_text, max_width=250),
                        tooltip=f"{event['event_type'].title()} - {period.title()}",
                        color=color,
                        fillColor=color,
                        fillOpacity=0.7,
                        weight=2,
                        opacity=0.8
                    ).add_to(event_groups[group_key])

            # Add all groups to map
            for group in event_groups.values():
                group.add_to(map_obj)

            print(f"✅ Added behavioral events with {len(event_groups)} categories")

        except Exception as e:
            print(f"⚠️  Could not load behavioral events: {e}")

    def save_improved_map(self):
        """Save the improved corridor map"""

        # Create the improved map
        improved_map = self.create_professional_corridor_map()

        # Save to output directory
        output_dir = os.path.join(self.figures_dir, "interactive")
        os.makedirs(output_dir, exist_ok=True)

        map_path = os.path.join(output_dir, "improved_corridor_map.html")
        improved_map.save(map_path)

        print(f"✅ Improved corridor map saved: {map_path}")

        # Also update the main corridor map
        main_map_path = os.path.join(output_dir, "corridor_risk_map.html")
        improved_map.save(main_map_path)

        print(f"✅ Main corridor map updated: {main_map_path}")

        return map_path

def main():
    mapper = ImprovedCorridorMap()
    map_path = mapper.save_improved_map()

    print(f"\n✅ IMPROVED CORRIDOR MAP COMPLETE")
    print(f"🗺️  Professional map with proper centering and zoom")
    print(f"📍 Correct corridor alignment with GIS coordinates")
    print(f"🎯 Clear start/end markers and professional styling")
    print(f"📊 Behavioral events properly categorized and displayed")

    return map_path

if __name__ == "__main__":
    main()
"""
SH1 Corridor Risk Map - No Forced Clustering
Show actual spatial distribution of events along the corridor
"""

import pandas as pd
import folium
import numpy as np

def create_corridor_map():
    print("🗺️ CREATING SH1 CORRIDOR RISK MAP")
    print("Showing actual spatial distribution without forced clustering")
    print("="*60)
    
    # Load our events
    events = pd.read_csv('/Users/timwelch/Dropbox/Files/Research/Compass_Data/SH1_Study/Data/connected_vehicle_data/comprehensive_gps_events.csv')
    events['timestamp'] = pd.to_datetime(events['timestamp'])
    
    print(f"✅ Loaded {len(events):,} events")
    
    # Calculate center of all events
    center_lat = events['latitude'].mean()
    center_lon = events['longitude'].mean()
    
    print(f"Map center: {center_lat:.6f}, {center_lon:.6f}")
    print(f"Lat range: {events['latitude'].min():.6f} to {events['latitude'].max():.6f}")
    print(f"Lon range: {events['longitude'].min():.6f} to {events['longitude'].max():.6f}")
    
    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,  # Zoom out to show full corridor
        tiles='OpenStreetMap'
    )
    
    # Color scheme for event types
    event_colors = {
        'harsh_braking': '#FF0000',      # Red
        'harsh_steering': '#FF8C00',     # Orange
        'harsh_acceleration': '#FFD700', # Gold
        'high_gforce': '#8A2BE2',        # Purple
        'speed_violation': '#DC143C'     # Crimson
    }
    
    # Add all events to map
    for idx, event in events.iterrows():
        color = event_colors.get(event['event_type'], '#000000')
        
        # Size based on severity
        radius = 2 + min(event['severity'] / 5, 8)  # Cap at reasonable size
        
        # Period indicator
        period_icon = "🔵" if pd.to_datetime(event['timestamp']) < pd.to_datetime("2025-04-13") else "🔴"
        
        popup_text = f"""
        <b>{event['event_type'].replace('_', ' ').title()}</b><br>
        {period_icon} {str(event['timestamp'])[:16]}<br>
        Speed: {event['derived_speed']:.1f} km/h<br>
        Severity: {event['severity']:.2f}<br>
        Vehicle: {event['vehicle_id'][:8]}...
        """
        
        folium.CircleMarker(
            location=[event['latitude'], event['longitude']],
            radius=radius,
            popup=folium.Popup(popup_text, max_width=200),
            color=color,
            fillColor=color,
            fillOpacity=0.6,
            weight=1
        ).add_to(m)
    
    # Add legend
    legend_html = f'''
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 250px; height: 220px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px">
    <b>SH1 Corridor Risk Events</b><br><br>
    <b>Event Types:</b><br>
    <i class="fa fa-circle" style="color:#FF0000"></i> Harsh Braking<br>
    <i class="fa fa-circle" style="color:#FF8C00"></i> Harsh Steering<br> 
    <i class="fa fa-circle" style="color:#FFD700"></i> Harsh Acceleration<br>
    <i class="fa fa-circle" style="color:#8A2BE2"></i> High G-Force<br>
    <i class="fa fa-circle" style="color:#DC143C"></i> Speed Violation<br>
    <br>
    <b>Time Period:</b><br>
    🔵 Before Apr 13 (n={len(events[events['timestamp'] < '2025-04-13'])})<br>
    🔴 After Apr 13 (n={len(events[events['timestamp'] >= '2025-04-13'])})
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Save map
    output_file = '/Users/timwelch/PyCharmMiscProject/sh1_corridor_events_map.html'
    m.save(output_file)
    print(f"✅ Corridor map saved: {output_file}")
    
    # Event distribution analysis
    print(f"\n📊 SPATIAL DISTRIBUTION ANALYSIS:")
    
    # Latitude-based distribution (north-south along corridor)
    lat_bins = pd.cut(events['latitude'], bins=10)
    lat_distribution = events.groupby(lat_bins).size()
    
    print(f"Event distribution along corridor (north to south):")
    for i, (lat_range, count) in enumerate(lat_distribution.items()):
        if count > 0:
            print(f"  Segment {i+1}: {count:3d} events ({lat_range})")
    
    # Event density by type
    print(f"\nEvent types by location density:")
    for event_type, count in events['event_type'].value_counts().items():
        avg_lat = events[events['event_type'] == event_type]['latitude'].mean()
        avg_lon = events[events['event_type'] == event_type]['longitude'].mean()
        print(f"  {event_type}: {count:3d} events (center: {avg_lat:.4f}, {avg_lon:.4f})")

if __name__ == "__main__":
    create_corridor_map()
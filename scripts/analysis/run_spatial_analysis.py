"""
Simple runner for spatial risk analysis with fixed string formatting
"""

import os
import pandas as pd
import numpy as np
import folium
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN

def run_spatial_analysis():
    print("🗺️ SH1 SPATIAL RISK ANALYSIS")
    print("Creating comprehensive location-based risk assessment")
    print("="*60)
    
    # Load data
    data_dir = "/Users/timwelch/Dropbox/Files/Research/Compass_Data/SH1_Study/Data/connected_vehicle_data"
    near_miss_file = "support.nz_christchurch_nearmisses-ed71ff0e713ef10baadc4371-000000000000.csv"
    
    df = pd.read_csv(f"{data_dir}/{near_miss_file}")
    df['timestamp'] = pd.to_datetime(df['local_Timestamp'])
    
    # Extract coordinates
    df['longitude'] = df['Point'].str.extract(r'POINT\(([^\s]+)').astype(float)
    df['latitude'] = df['Point'].str.extract(r'POINT\([^\s]+ ([^\)]+)\)').astype(float)
    
    print(f"📊 Data loaded: {len(df)} events")
    print(f"📅 Date range: {df['timestamp'].min().date()} to {df['timestamp'].max().date()}")
    
    # Calculate risk metrics
    print(f"\n🧮 CALCULATING BEHAVIORAL METRICS")
    
    # Speed metrics
    speed_ratio = df['speed'] / df['speed'].mean()
    speed_differential = df['HighestSpeed'] - df['speed']
    
    # Severity metrics  
    gforce_severity = df['TotalGForce']
    total_acceleration = np.sqrt(df['XAcc']**2 + df['YAcc']**2)
    
    # Event weights
    event_weights = {'Steering': 1.0, 'Braking': 1.5}
    event_type_weight = df['nm_Classification'].map(event_weights)
    
    # Vehicle weights
    vehicle_weights = {'CAR': 1.2, 'VAN': 1.0, 'TRUCK': 0.8, 'BUS': 0.9}
    vehicle_risk_weight = df['vehicletype'].map(vehicle_weights)
    
    # Infrastructure complexity
    road_complexity = {
        'motorway': 0.6, 'trunk': 0.8, 'primary': 1.0, 
        'secondary': 1.3, 'tertiary': 1.5, 'service_other': 1.4
    }
    infrastructure_complexity = df['osm_roadclass'].map(road_complexity).fillna(1.0)
    
    # Lane risk
    lane_risk = {1: 1.5, 2: 1.0, 3: 0.8, 4: 0.6}
    lane_risk_score = df['LaneCount'].map(lane_risk).fillna(1.0)
    
    # Temporal weighting
    current_date = pd.to_datetime('2025-08-27')
    days_from_current = (current_date - df['timestamp']).dt.days
    half_life_days = 365
    temporal_weights = 0.5 ** (days_from_current / half_life_days)
    
    print(f"Temporal weights: {temporal_weights.min():.3f} to {temporal_weights.max():.3f}")
    
    # Create risk index
    print(f"\n📈 CALCULATING COMPOSITE RISK INDEX")
    
    # Combine metrics
    metrics_df = pd.DataFrame({
        'speed_ratio': speed_ratio,
        'speed_differential': speed_differential,
        'gforce_severity': gforce_severity,
        'total_acceleration': total_acceleration,
        'event_type_weight': event_type_weight,
        'vehicle_risk_weight': vehicle_risk_weight,
        'infrastructure_complexity': infrastructure_complexity,
        'lane_risk': lane_risk_score
    })
    
    # Normalize and weight
    scaler = StandardScaler()
    normalized_metrics = pd.DataFrame(
        scaler.fit_transform(metrics_df),
        columns=metrics_df.columns,
        index=metrics_df.index
    )
    
    # Component weights
    component_weights = {
        'speed_ratio': 0.15,
        'speed_differential': 0.10,
        'gforce_severity': 0.25,
        'total_acceleration': 0.20,
        'event_type_weight': 0.10,
        'vehicle_risk_weight': 0.05,
        'infrastructure_complexity': 0.10,
        'lane_risk': 0.05
    }
    
    # Calculate weighted risk index
    risk_index = pd.Series(0.0, index=df.index)
    for component, weight in component_weights.items():
        risk_index += normalized_metrics[component] * weight
    
    # Apply temporal weighting
    risk_index *= temporal_weights
    
    # Normalize to 0-100 scale
    risk_index = (risk_index - risk_index.min()) / (risk_index.max() - risk_index.min()) * 100
    df['risk_index'] = risk_index
    
    print(f"Risk index: {risk_index.min():.1f} to {risk_index.max():.1f}, mean: {risk_index.mean():.1f}")
    
    # Spatial clustering
    print(f"\n🎯 IDENTIFYING HIGH-RISK SPATIAL CLUSTERS")
    
    coords = df[['latitude', 'longitude']].values
    eps_degrees = 0.5 / 111.0  # 0.5km radius
    clustering = DBSCAN(eps=eps_degrees, min_samples=3).fit(coords)
    df['cluster'] = clustering.labels_
    
    # Cluster stats
    cluster_stats = []
    for cluster_id in set(clustering.labels_):
        if cluster_id == -1:
            continue
        cluster_events = df[df['cluster'] == cluster_id]
        stats = {
            'cluster_id': cluster_id,
            'event_count': len(cluster_events),
            'mean_risk_index': cluster_events['risk_index'].mean(),
            'center_lat': cluster_events['latitude'].mean(),
            'center_lon': cluster_events['longitude'].mean(),
            'dominant_road_class': cluster_events['osm_roadclass'].mode().iloc[0],
            'dominant_vehicle_type': cluster_events['vehicletype'].mode().iloc[0]
        }
        cluster_stats.append(stats)
    
    cluster_df = pd.DataFrame(cluster_stats).sort_values('mean_risk_index', ascending=False)
    
    print(f"Identified {len(cluster_df)} high-risk clusters")
    print(f"Events in clusters: {len(df[df['cluster'] != -1])}")
    
    # Create map
    print(f"\n🗺️ CREATING RISK HOTSPOT MAP")
    
    center_lat = df['latitude'].mean()
    center_lon = df['longitude'].mean()
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
    
    # Add events
    for idx, event in df.iterrows():
        risk_score = event['risk_index']
        
        if risk_score >= 80:
            color = 'red'
            risk_level = 'Extreme'
        elif risk_score >= 60:
            color = 'orange'
            risk_level = 'High'
        elif risk_score >= 40:
            color = 'yellow'
            risk_level = 'Moderate'
        else:
            color = 'green'
            risk_level = 'Low'
        
        popup_text = f"""
        <b>Risk Index: {risk_score:.1f} ({risk_level})</b><br>
        Date: {event['timestamp'].strftime('%Y-%m-%d %H:%M')}<br>
        Event: {event['nm_Classification']}<br>
        Vehicle: {event['vehicletype']}<br>
        Speed: {event['speed']:.0f} km/h<br>
        G-Force: {event['TotalGForce']:.3f}g<br>
        Road: {event['osm_roadclass']}
        """
        
        folium.CircleMarker(
            location=[event['latitude'], event['longitude']],
            radius=3 + (risk_score / 25),
            popup=popup_text,
            color=color,
            fillColor=color,
            fillOpacity=0.6,
            weight=2
        ).add_to(m)
    
    # Add cluster markers
    for _, cluster in cluster_df.head(5).iterrows():
        folium.Marker(
            location=[cluster['center_lat'], cluster['center_lon']],
            popup=f"Cluster #{cluster['cluster_id']}: {cluster['mean_risk_index']:.1f} risk",
            icon=folium.Icon(color='red', icon='warning-sign')
        ).add_to(m)
    
    # Save map
    m.save('sh1_risk_hotspots.html')
    print(f"Interactive map saved: sh1_risk_hotspots.html")
    
    # Generate insights
    print(f"\n📊 SPATIAL RISK ANALYSIS INSIGHTS")
    print("="*60)
    
    # Risk distribution
    risk_levels = pd.cut(df['risk_index'], bins=[0, 25, 50, 75, 100], 
                        labels=['Low', 'Moderate', 'High', 'Extreme'])
    risk_distribution = risk_levels.value_counts()
    
    print(f"Risk Level Distribution:")
    for level, count in risk_distribution.items():
        pct = count / len(df) * 100
        print(f"• {level}: {count} events ({pct:.1f}%)")
    
    # Top clusters
    print(f"\nTop 5 Risk Hotspots:")
    for i, (_, cluster) in enumerate(cluster_df.head(5).iterrows(), 1):
        print(f"{i}. Cluster #{cluster['cluster_id']}: {cluster['mean_risk_index']:.1f} risk index")
        print(f"   {cluster['event_count']} events on {cluster['dominant_road_class']}")
    
    # Infrastructure risk
    print(f"\nRisk by Infrastructure Type:")
    infra_risk = df.groupby('osm_roadclass')['risk_index'].agg(['mean', 'count']).sort_values('mean', ascending=False)
    for road_type, stats in infra_risk.iterrows():
        print(f"• {road_type}: {stats['mean']:.1f} avg risk ({stats['count']} events)")
    
    print(f"\n✅ SPATIAL RISK ANALYSIS COMPLETE")
    return df, cluster_df

if __name__ == "__main__":
    df, clusters = run_spatial_analysis()
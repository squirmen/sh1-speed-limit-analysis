"""
SH1 Spatial Risk Analysis - Comprehensive Risk Index
Creates location-based risk index using multi-dimensional behavioral metrics
Identifies infrastructure-behavior causality patterns
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import folium
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import warnings
warnings.filterwarnings('ignore')

class SpatialRiskAnalysis:
    def __init__(self):
        self.current_date = pd.to_datetime('2025-08-27')  # For temporal weighting
        
        print("🗺️ SH1 SPATIAL RISK ANALYSIS")
        print("Creating comprehensive location-based risk assessment")
        print("="*60)
        
    def load_and_prepare_data(self, data_dir):
        """Load near-miss data and prepare for spatial analysis"""
        near_miss_file = "support.nz_christchurch_nearmisses-ed71ff0e713ef10baadc4371-000000000000.csv"
        
        self.df = pd.read_csv(f"{data_dir}/{near_miss_file}")
        self.df['timestamp'] = pd.to_datetime(self.df['local_Timestamp'])
        
        # Extract coordinates from Point column (POINT(lon lat))
        self.df['longitude'] = self.df['Point'].str.extract(r'POINT\(([^\s]+)').astype(float)
        self.df['latitude'] = self.df['Point'].str.extract(r'POINT\([^\s]+ ([^\)]+)\)').astype(float)
        
        print(f"📊 Data loaded: {len(self.df)} events")
        print(f"📅 Date range: {self.df['timestamp'].min().date()} to {self.df['timestamp'].max().date()}")
        print(f"🌐 Coordinate range: {self.df['longitude'].min():.6f} to {self.df['longitude'].max():.6f} (lon)")
        print(f"🌐 Coordinate range: {self.df['latitude'].min():.6f} to {self.df['latitude'].max():.6f} (lat)")
        
        return True
    
    def calculate_behavioral_metrics(self):
        """Calculate comprehensive behavioral metrics for each event"""
        print(f"\n🧮 CALCULATING BEHAVIORAL METRICS")
        print("-"*40)
        
        metrics = {}
        
        # 1. Speed-related metrics
        metrics['speed_ratio'] = self.df['speed'] / self.df['speed'].mean()
        metrics['speed_differential'] = self.df['HighestSpeed'] - self.df['speed']
        
        # 2. Severity metrics
        metrics['gforce_severity'] = self.df['TotalGForce']
        metrics['total_acceleration'] = np.sqrt(self.df['XAcc']**2 + self.df['YAcc']**2)
        
        # 3. Event type weights
        event_weights = {'Steering': 1.0, 'Braking': 1.5}  # Braking events more severe
        metrics['event_type_weight'] = self.df['nm_Classification'].map(event_weights)
        
        # 4. Vehicle type risk weights
        vehicle_weights = {
            'CAR': 1.2,      # Higher risk per event (based on our analysis)
            'VAN': 1.0,      # Baseline
            'TRUCK': 0.8,    # Lower risk per event but more events
            'BUS': 0.9       # Moderate risk
        }
        metrics['vehicle_risk_weight'] = self.df['vehicletype'].map(vehicle_weights)
        
        # 5. Infrastructure complexity
        road_complexity = {
            'motorway': 0.6,     # Lowest complexity
            'trunk': 0.8,        # Moderate
            'primary': 1.0,      # Baseline
            'secondary': 1.3,    # Higher complexity
            'tertiary': 1.5,     # Highest complexity
            'service_other': 1.4
        }
        metrics['infrastructure_complexity'] = self.df['osm_roadclass'].map(road_complexity).fillna(1.0)
        
        # 6. Lane count risk (fewer lanes = higher risk)
        lane_risk = {1: 1.5, 2: 1.0, 3: 0.8, 4: 0.6}
        metrics['lane_risk'] = self.df['LaneCount'].map(lane_risk).fillna(1.0)
        
        # Convert to DataFrame
        self.metrics_df = pd.DataFrame(metrics, index=self.df.index)
        
        print(f"Calculated {len(metrics)} behavioral metrics:")
        for metric in metrics.keys():
            print(f"• {metric}")
            
        return self.metrics_df
    
    def apply_temporal_weighting(self):
        """Apply temporal decay to older events"""
        print(f"\n⏰ APPLYING TEMPORAL WEIGHTING")
        print("-"*40)
        
        # Calculate days from current date
        days_from_current = (self.current_date - self.df['timestamp']).dt.days
        
        # Exponential decay: more recent events weighted higher
        # Half-life of 365 days (events lose 50% weight after 1 year)
        half_life_days = 365
        decay_factor = 0.5 ** (days_from_current / half_life_days)
        
        self.temporal_weights = decay_factor
        
        print(f"Temporal weighting statistics:")
        print(f"• Weight range: {self.temporal_weights.min():.3f} to {self.temporal_weights.max():.3f}")
        print(f"• Mean weight: {self.temporal_weights.mean():.3f}")
        
        # Show weight by year
        self.df['year'] = self.df['timestamp'].dt.year
        yearly_weights = self.df.groupby('year').apply(lambda x: self.temporal_weights[x.index].mean())
        print(f"\nAverage weights by year:")
        for year, weight in yearly_weights.items():
            print(f"• {year}: {weight:.3f}")
            
        return self.temporal_weights
    
    def calculate_composite_risk_index(self):
        """Calculate composite risk index combining all metrics"""
        print(f"\n📈 CALCULATING COMPOSITE RISK INDEX")
        print("-"*40)
        
        # Define weights for each component (sum to 1.0)
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
        
        print(f"Risk index components and weights:")
        for component, weight in component_weights.items():
            print(f"• {component}: {weight:.0%}")
        
        # Normalize each metric to 0-1 scale
        scaler = StandardScaler()
        normalized_metrics = pd.DataFrame(
            scaler.fit_transform(self.metrics_df),
            columns=self.metrics_df.columns,
            index=self.metrics_df.index
        )
        
        # Calculate weighted risk index
        risk_index = pd.Series(0.0, index=self.df.index)
        
        for component, weight in component_weights.items():
            if component in normalized_metrics.columns:
                risk_index += normalized_metrics[component] * weight
        
        # Apply temporal weighting
        risk_index *= self.temporal_weights
        
        # Normalize to 0-100 scale
        risk_index = (risk_index - risk_index.min()) / (risk_index.max() - risk_index.min()) * 100
        
        self.df['risk_index'] = risk_index
        
        print(f"\nRisk index statistics:")
        print(f"• Range: {risk_index.min():.1f} to {risk_index.max():.1f}")
        print(f"• Mean: {risk_index.mean():.1f}")
        print(f"• Std Dev: {risk_index.std():.1f}")
        
        return risk_index
    
    def identify_spatial_clusters(self, cluster_radius_km=0.5):
        """Identify spatial clusters of high-risk events"""
        print(f"\n🎯 IDENTIFYING HIGH-RISK SPATIAL CLUSTERS")
        print("-"*40)
        
        # Prepare coordinate data
        coords = self.df[['latitude', 'longitude']].values
        
        # Convert radius to approximate degrees (rough approximation)
        eps_degrees = cluster_radius_km / 111.0  # 111 km per degree
        
        # DBSCAN clustering
        clustering = DBSCAN(eps=eps_degrees, min_samples=3).fit(coords)
        self.df['cluster'] = clustering.labels_
        
        # Calculate cluster statistics
        cluster_stats = []
        for cluster_id in set(clustering.labels_):
            if cluster_id == -1:  # Noise points
                continue
                
            cluster_events = self.df[self.df['cluster'] == cluster_id]
            
            stats = {
                'cluster_id': cluster_id,
                'event_count': len(cluster_events),
                'mean_risk_index': cluster_events['risk_index'].mean(),
                'max_risk_index': cluster_events['risk_index'].max(),
                'center_lat': cluster_events['latitude'].mean(),
                'center_lon': cluster_events['longitude'].mean(),
                'dominant_road_class': cluster_events['osm_roadclass'].mode().iloc[0],
                'dominant_vehicle_type': cluster_events['vehicletype'].mode().iloc[0],
                'avg_speed': cluster_events['speed'].mean(),
                'avg_gforce': cluster_events['TotalGForce'].mean()
            }
            cluster_stats.append(stats)
        
        self.cluster_stats = pd.DataFrame(cluster_stats).sort_values('mean_risk_index', ascending=False)
        
        print(f\"Identified {len(self.cluster_stats)} high-risk clusters\")
        print(f\"Events in clusters: {len(self.df[self.df['cluster'] != -1])}\")
        print(f\"Isolated events: {len(self.df[self.df['cluster'] == -1])}\")
        
        return self.cluster_stats
    
    def create_risk_hotspot_map(self, output_file='sh1_risk_hotspots.html'):
        \"\"\"Create interactive map showing risk hotspots\"\"\"
        print(f\"\n🗺️ CREATING RISK HOTSPOT MAP\")
        print(\"-\"*40)
        
        # Center map on data
        center_lat = self.df['latitude'].mean()
        center_lon = self.df['longitude'].mean()
        
        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles='OpenStreetMap'
        )
        
        # Add individual events with risk-based coloring
        for idx, event in self.df.iterrows():
            risk_score = event['risk_index']
            
            # Color based on risk level
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
            
            # Create popup with detailed information
            popup_text = f\"\"\"
            <b>Risk Index: {risk_score:.1f} ({risk_level})</b><br>
            Date: {event['timestamp'].strftime('%Y-%m-%d %H:%M')}<br>
            Event: {event['nm_Classification']}<br>
            Vehicle: {event['vehicletype']}<br>
            Speed: {event['speed']:.0f} km/h<br>
            G-Force: {event['TotalGForce']:.3f}g<br>
            Road: {event['osm_roadclass']}<br>
            Lanes: {event['LaneCount']}
            \"\"\"
            
            folium.CircleMarker(
                location=[event['latitude'], event['longitude']],
                radius=5 + (risk_score / 20),  # Size based on risk
                popup=popup_text,
                color=color,
                fillColor=color,
                fillOpacity=0.6,
                weight=2
            ).add_to(m)
        
        # Add cluster markers
        if hasattr(self, 'cluster_stats'):
            for _, cluster in self.cluster_stats.head(10).iterrows():  # Top 10 clusters
                popup_text = f\"\"\"
                <b>Risk Cluster #{cluster['cluster_id']}</b><br>
                Events: {cluster['event_count']}<br>
                Mean Risk: {cluster['mean_risk_index']:.1f}<br>
                Max Risk: {cluster['max_risk_index']:.1f}<br>
                Road Type: {cluster['dominant_road_class']}<br>
                Vehicle Type: {cluster['dominant_vehicle_type']}<br>
                Avg Speed: {cluster['avg_speed']:.1f} km/h<br>
                Avg G-Force: {cluster['avg_gforce']:.3f}g
                \"\"\"
                
                folium.Marker(
                    location=[cluster['center_lat'], cluster['center_lon']],
                    popup=popup_text,
                    icon=folium.Icon(color='red', icon='warning-sign')
                ).add_to(m)
        
        # Add legend
        legend_html = '''
        <div style=\"position: fixed; 
                    top: 10px; right: 10px; width: 200px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px\">
        <b>Risk Level Legend</b><br>
        <i class=\"fa fa-circle\" style=\"color:red\"></i> Extreme (80-100)<br>
        <i class=\"fa fa-circle\" style=\"color:orange\"></i> High (60-80)<br>
        <i class=\"fa fa-circle\" style=\"color:yellow\"></i> Moderate (40-60)<br>
        <i class=\"fa fa-circle\" style=\"color:green\"></i> Low (0-40)
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Save map
        m.save(output_file)
        print(f\"Interactive map saved: {output_file}\")
        
        return m
    
    def generate_insights_report(self):
        \"\"\"Generate comprehensive insights report\"\"\"
        print(f\"\n📊 SPATIAL RISK ANALYSIS INSIGHTS\")
        print(\"=\"*60)
        
        # Overall risk distribution
        risk_levels = pd.cut(self.df['risk_index'], 
                           bins=[0, 25, 50, 75, 100], 
                           labels=['Low', 'Moderate', 'High', 'Extreme'])
        risk_distribution = risk_levels.value_counts()
        
        print(f\"Risk Level Distribution:\")
        for level, count in risk_distribution.items():
            pct = count / len(self.df) * 100
            print(f\"• {level}: {count} events ({pct:.1f}%)\")
        
        # Top risk hotspots
        if hasattr(self, 'cluster_stats') and len(self.cluster_stats) > 0:
            print(f\"\nTop 5 Risk Hotspots:\")
            for i, (_, cluster) in enumerate(self.cluster_stats.head(5).iterrows(), 1):
                print(f\"{i}. Cluster #{cluster['cluster_id']}: {cluster['mean_risk_index']:.1f} risk index\")
                print(f\"   {cluster['event_count']} events on {cluster['dominant_road_class']} (mainly {cluster['dominant_vehicle_type']})\")\")
        
        # Infrastructure-risk relationships
        print(f\"\nRisk by Infrastructure Type:\")
        infra_risk = self.df.groupby('osm_roadclass')['risk_index'].agg(['mean', 'count'])
        infra_risk = infra_risk.sort_values('mean', ascending=False)
        
        for road_type, stats in infra_risk.iterrows():
            print(f\"• {road_type}: {stats['mean']:.1f} avg risk ({stats['count']} events)\")
        
        # Vehicle type risk patterns
        print(f\"\nRisk by Vehicle Type:\")
        vehicle_risk = self.df.groupby('vehicletype')['risk_index'].agg(['mean', 'count'])
        vehicle_risk = vehicle_risk.sort_values('mean', ascending=False)
        
        for vehicle_type, stats in vehicle_risk.iterrows():
            print(f\"• {vehicle_type}: {stats['mean']:.1f} avg risk ({stats['count']} events)\")
        
        # Temporal risk trends
        print(f\"\nRisk Trends by Year:\")
        yearly_risk = self.df.groupby('year')['risk_index'].agg(['mean', 'count'])
        
        for year, stats in yearly_risk.iterrows():
            print(f\"• {year}: {stats['mean']:.1f} avg risk ({stats['count']} events)\")

def main():
    analyzer = SpatialRiskAnalysis()
    
    # Load data
    data_dir = \"/Users/timwelch/Dropbox/Files/Research/Compass_Data/SH1_Study/Data/connected_vehicle_data\"
    
    if analyzer.load_and_prepare_data(data_dir):
        # Calculate comprehensive risk metrics
        analyzer.calculate_behavioral_metrics()
        analyzer.apply_temporal_weighting()
        analyzer.calculate_composite_risk_index()
        
        # Spatial analysis
        analyzer.identify_spatial_clusters()
        
        # Generate outputs
        analyzer.create_risk_hotspot_map()
        analyzer.generate_insights_report()
        
        print(f\"\n✅ SPATIAL RISK ANALYSIS COMPLETE\")
        print(f\"📊 Risk index calculated for {len(analyzer.df)} events\")
        print(f\"🗺️ Interactive map created: sh1_risk_hotspots.html\")
        print(f\"🎯 Risk hotspots identified and analyzed\")

if __name__ == \"__main__\":
    main()
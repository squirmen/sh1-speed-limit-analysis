"""
Spatial Risk Analysis Using Our GPS-Derived Events
Create comprehensive location-based risk assessment from our detected events
"""

import pandas as pd
import numpy as np
import folium
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class OurSpatialRiskAnalysis:
    def __init__(self):
        self.speed_change_date = pd.to_datetime("2025-04-13")
        
        print("🗺️ SPATIAL RISK ANALYSIS - OUR GPS-DERIVED EVENTS")
        print("Creating location-based risk assessment from our behavioral detection")
        print("="*60)
        
    def load_our_events(self):
        """Load our GPS-derived events"""
        print(f"\n📊 LOADING OUR DETECTED EVENTS")
        
        self.events = pd.read_csv('comprehensive_gps_events.csv')
        self.events['timestamp'] = pd.to_datetime(self.events['timestamp'])
        
        # Add period classification
        self.events['period'] = self.events['timestamp'].apply(
            lambda x: 'before' if x < self.speed_change_date else 'after'
        )
        
        print(f"✅ Loaded {len(self.events):,} events")
        print(f"📅 Date range: {self.events['timestamp'].min()} to {self.events['timestamp'].max()}")
        print(f"🚗 Vehicles: {self.events['vehicle_id'].nunique():,}")
        
        # Event type summary
        print(f"\nEvent types:")
        for event_type, count in self.events['event_type'].value_counts().items():
            print(f"• {event_type}: {count:,} events")
            
        return True
        
    def calculate_comprehensive_risk_index(self):
        """Calculate risk index for our events"""
        print(f"\n📈 CALCULATING COMPREHENSIVE RISK INDEX")
        
        # Create risk components
        risk_components = pd.DataFrame(index=self.events.index)
        
        # 1. Severity score (normalized)
        risk_components['severity_score'] = self.events['severity'] / self.events['severity'].max()
        
        # 2. Speed factor  
        risk_components['speed_factor'] = np.minimum(self.events['derived_speed'] / 100, 2.0)  # Cap at 200%
        
        # 3. Event type weights
        event_type_weights = {
            'harsh_braking': 2.0,      # Highest risk - emergency situation
            'harsh_steering': 1.8,     # High risk - collision avoidance  
            'harsh_acceleration': 1.2,  # Moderate risk - aggressive driving
            'high_gforce': 1.6,       # High risk - loss of control potential
            'speed_violation': 1.4     # Moderate-high risk - regulatory violation
        }
        risk_components['event_type_weight'] = self.events['event_type'].map(event_type_weights)
        
        # 4. Temporal weighting (more recent = higher weight)
        current_date = pd.to_datetime('2025-08-27')
        days_from_current = (current_date - self.events['timestamp']).dt.days
        half_life_days = 180  # 6 months half-life
        risk_components['temporal_weight'] = 0.5 ** (days_from_current / half_life_days)
        
        # 5. Frequency factor (multiple events at same location)
        location_counts = self.events.groupby(['latitude', 'longitude']).size()
        location_freq = self.events.apply(
            lambda row: location_counts.get((row['latitude'], row['longitude']), 1), axis=1
        )
        risk_components['frequency_factor'] = np.log1p(location_freq)  # Log scale for frequency
        
        # Normalize all components to 0-1 scale
        scaler = StandardScaler()
        normalized_components = pd.DataFrame(
            scaler.fit_transform(risk_components),
            columns=risk_components.columns,
            index=risk_components.index
        )
        
        # Component weights (sum to 1.0)
        component_weights = {
            'severity_score': 0.35,      # Primary factor
            'speed_factor': 0.20,        # Speed context
            'event_type_weight': 0.25,   # Event severity
            'temporal_weight': 0.10,     # Recency
            'frequency_factor': 0.10     # Location frequency
        }
        
        # Calculate weighted risk index
        risk_index = pd.Series(0.0, index=self.events.index)
        for component, weight in component_weights.items():
            risk_index += normalized_components[component] * weight
        
        # Normalize to 0-100 scale
        risk_index = (risk_index - risk_index.min()) / (risk_index.max() - risk_index.min()) * 100
        
        self.events['risk_index'] = risk_index
        
        print(f"Risk index statistics:")
        print(f"• Range: {risk_index.min():.1f} to {risk_index.max():.1f}")
        print(f"• Mean: {risk_index.mean():.1f}")
        print(f"• Std Dev: {risk_index.std():.1f}")
        
        return risk_index
        
    def identify_spatial_clusters(self, cluster_radius_km=1.0):
        """Identify spatial clusters of high-risk events"""
        print(f"\n🎯 IDENTIFYING SPATIAL CLUSTERS")
        print(f"Using cluster radius: {cluster_radius_km} km")
        
        # Prepare coordinate data
        coords = self.events[['latitude', 'longitude']].values
        
        # Convert radius to approximate degrees
        eps_degrees = cluster_radius_km / 111.0  # 111 km per degree
        
        # DBSCAN clustering
        clustering = DBSCAN(eps=eps_degrees, min_samples=5).fit(coords)  # Min 5 events for cluster
        self.events['cluster'] = clustering.labels_
        
        # Calculate cluster statistics
        cluster_stats = []
        for cluster_id in set(clustering.labels_):
            if cluster_id == -1:  # Noise points
                continue
                
            cluster_events = self.events[self.events['cluster'] == cluster_id]
            
            stats = {
                'cluster_id': cluster_id,
                'event_count': len(cluster_events),
                'mean_risk_index': cluster_events['risk_index'].mean(),
                'max_risk_index': cluster_events['risk_index'].max(),
                'center_lat': cluster_events['latitude'].mean(),
                'center_lon': cluster_events['longitude'].mean(),
                'dominant_event_type': cluster_events['event_type'].mode().iloc[0],
                'avg_speed': cluster_events['derived_speed'].mean(),
                'max_severity': cluster_events['severity'].max(),
                'before_count': len(cluster_events[cluster_events['period'] == 'before']),
                'after_count': len(cluster_events[cluster_events['period'] == 'after'])
            }
            cluster_stats.append(stats)
        
        self.cluster_stats = pd.DataFrame(cluster_stats).sort_values('mean_risk_index', ascending=False)
        
        print(f"Identified {len(self.cluster_stats)} high-risk clusters")
        print(f"Events in clusters: {len(self.events[self.events['cluster'] != -1])}")
        print(f"Isolated events: {len(self.events[self.events['cluster'] == -1])}")
        
        return self.cluster_stats
        
    def create_interactive_risk_map(self, output_file='our_spatial_risk_map.html'):
        """Create interactive map showing our risk hotspots"""
        print(f"\n🗺️ CREATING INTERACTIVE RISK MAP")
        
        # Center map on data
        center_lat = self.events['latitude'].mean()
        center_lon = self.events['longitude'].mean()
        
        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=11,
            tiles='OpenStreetMap'
        )
        
        # Color mapping for event types
        event_colors = {
            'harsh_braking': 'red',
            'harsh_steering': 'orange', 
            'harsh_acceleration': 'yellow',
            'high_gforce': 'purple',
            'speed_violation': 'darkred'
        }
        
        # Add individual events
        for idx, event in self.events.iterrows():
            risk_score = event['risk_index']
            event_color = event_colors.get(event['event_type'], 'blue')
            
            # Size based on risk index
            radius = 3 + (risk_score / 20)
            
            # Popup with detailed information
            popup_text = f"""
            <b>Risk Index: {risk_score:.1f}</b><br>
            Event Type: {event['event_type']}<br>
            Timestamp: {event['timestamp'].strftime('%Y-%m-%d %H:%M')}<br>
            Speed: {event['derived_speed']:.1f} km/h<br>
            Severity: {event['severity']:.2f}<br>
            Period: {event['period']}<br>
            Vehicle: {event['vehicle_id'][:12]}...
            """
            
            folium.CircleMarker(
                location=[event['latitude'], event['longitude']],
                radius=radius,
                popup=popup_text,
                color=event_color,
                fillColor=event_color,
                fillOpacity=0.6,
                weight=2
            ).add_to(m)
        
        # Add cluster markers for top clusters
        if hasattr(self, 'cluster_stats'):
            for _, cluster in self.cluster_stats.head(10).iterrows():
                # Determine risk level color
                if cluster['mean_risk_index'] >= 80:
                    icon_color = 'red'
                elif cluster['mean_risk_index'] >= 60:
                    icon_color = 'orange'
                elif cluster['mean_risk_index'] >= 40:
                    icon_color = 'yellow'
                else:
                    icon_color = 'green'
                
                popup_text = f"""
                <b>Risk Cluster #{cluster['cluster_id']}</b><br>
                Events: {cluster['event_count']}<br>
                Mean Risk: {cluster['mean_risk_index']:.1f}<br>
                Max Risk: {cluster['max_risk_index']:.1f}<br>
                Dominant Type: {cluster['dominant_event_type']}<br>
                Avg Speed: {cluster['avg_speed']:.1f} km/h<br>
                Max Severity: {cluster['max_severity']:.2f}<br>
                Before/After: {cluster['before_count']}/{cluster['after_count']}
                """
                
                folium.Marker(
                    location=[cluster['center_lat'], cluster['center_lon']],
                    popup=popup_text,
                    icon=folium.Icon(color=icon_color, icon='warning-sign')
                ).add_to(m)
        
        # Add legend
        legend_html = f'''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 250px; height: 200px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <b>Our GPS-Derived Risk Events</b><br>
        <i class="fa fa-circle" style="color:red"></i> Harsh Braking<br>
        <i class="fa fa-circle" style="color:orange"></i> Harsh Steering<br> 
        <i class="fa fa-circle" style="color:yellow"></i> Harsh Acceleration<br>
        <i class="fa fa-circle" style="color:purple"></i> High G-Force<br>
        <i class="fa fa-circle" style="color:darkred"></i> Speed Violation<br>
        <br>
        <b>Cluster Risk Levels:</b><br>
        <i class="fa fa-map-marker" style="color:red"></i> Extreme (80-100)<br>
        <i class="fa fa-map-marker" style="color:orange"></i> High (60-80)<br>
        <i class="fa fa-map-marker" style="color:yellow"></i> Moderate (40-60)<br>
        <i class="fa fa-map-marker" style="color:green"></i> Low (0-40)
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Save map
        m.save(output_file)
        print(f"Interactive map saved: {output_file}")
        
        return m
        
    def generate_insights_report(self):
        """Generate comprehensive insights from our spatial analysis"""
        print(f"\n📊 OUR SPATIAL RISK ANALYSIS INSIGHTS")
        print("="*60)
        
        # Risk level distribution
        risk_levels = pd.cut(self.events['risk_index'], 
                           bins=[0, 25, 50, 75, 100], 
                           labels=['Low', 'Moderate', 'High', 'Extreme'])
        risk_distribution = risk_levels.value_counts()
        
        print(f"Risk Level Distribution:")
        for level, count in risk_distribution.items():
            pct = count / len(self.events) * 100
            print(f"• {level}: {count:,} events ({pct:.1f}%)")
        
        # Top risk hotspots
        if hasattr(self, 'cluster_stats') and len(self.cluster_stats) > 0:
            print(f"\nTop 5 Risk Hotspots:")
            for i, (_, cluster) in enumerate(self.cluster_stats.head(5).iterrows(), 1):
                print(f"{i}. Cluster #{cluster['cluster_id']}: {cluster['mean_risk_index']:.1f} risk index")
                print(f"   {cluster['event_count']} events, mainly {cluster['dominant_event_type']}")
                print(f"   Before/After: {cluster['before_count']}/{cluster['after_count']} events")
        
        # Event type risk analysis
        print(f"\nRisk by Event Type:")
        event_risk = self.events.groupby('event_type')['risk_index'].agg(['mean', 'count', 'max'])
        event_risk = event_risk.sort_values('mean', ascending=False)
        
        for event_type, stats in event_risk.iterrows():
            print(f"• {event_type}: {stats['mean']:.1f} avg risk (max: {stats['max']:.1f}, n={stats['count']})")
        
        # Before/After analysis
        print(f"\nBefore/After Speed Limit Change Analysis:")
        before_events = self.events[self.events['period'] == 'before']
        after_events = self.events[self.events['period'] == 'after']
        
        print(f"• Before period: {len(before_events):,} events (avg risk: {before_events['risk_index'].mean():.1f})")
        print(f"• After period: {len(after_events):,} events (avg risk: {after_events['risk_index'].mean():.1f})")
        
        if len(before_events) > 0 and len(after_events) > 0:
            # Calculate temporal rates
            before_days = (self.speed_change_date - before_events['timestamp'].min()).days
            after_days = (after_events['timestamp'].max() - self.speed_change_date).days
            
            before_rate = len(before_events) / max(before_days, 1)
            after_rate = len(after_events) / max(after_days, 1)
            
            if before_rate > 0:
                rate_change = (after_rate - before_rate) / before_rate * 100
                print(f"• Event rate change: {rate_change:+.1f}% ({before_rate:.2f} → {after_rate:.2f} events/day)")
        
        # Save comprehensive results
        self.events.to_csv('our_spatial_risk_events.csv', index=False)
        if hasattr(self, 'cluster_stats'):
            self.cluster_stats.to_csv('our_spatial_clusters.csv', index=False)
            
        print(f"\n💾 Results saved:")
        print(f"• our_spatial_risk_events.csv - {len(self.events):,} events with risk scores")
        print(f"• our_spatial_clusters.csv - {len(self.cluster_stats)} risk hotspots")
        print(f"• our_spatial_risk_map.html - Interactive map")

def main():
    analyzer = OurSpatialRiskAnalysis()
    
    # Load our detected events
    if analyzer.load_our_events():
        # Calculate comprehensive risk index
        analyzer.calculate_comprehensive_risk_index()
        
        # Identify spatial clusters
        analyzer.identify_spatial_clusters()
        
        # Create interactive map
        analyzer.create_interactive_risk_map()
        
        # Generate insights
        analyzer.generate_insights_report()
        
        print(f"\n✅ OUR SPATIAL RISK ANALYSIS COMPLETE")
        print(f"We've successfully analyzed {len(analyzer.events):,} GPS-derived events")
        print(f"and identified {len(analyzer.cluster_stats)} high-risk spatial clusters")

if __name__ == "__main__":
    main()
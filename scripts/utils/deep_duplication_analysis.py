"""
Deep Duplication Analysis - Trip and Vehicle Level
Check if new data contains actually different trips/vehicles vs complete duplicates
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
import hashlib

class DeepDuplicationAnalyzer:
    def __init__(self):
        self.base_dir = "/Volumes/T7/Data/connected_vehicle_data"
        self.data_dir = os.path.join(self.base_dir, "output", "processed_data")

        print("🔍 DEEP DUPLICATION ANALYSIS")
        print("Checking trip-level and vehicle-level uniqueness")
        print("="*60)

    def load_existing_trip_data(self):
        """Extract trip and vehicle info from existing comprehensive data"""
        print(f"\n📊 ANALYZING EXISTING TRIP DATA")

        existing_path = os.path.join(self.data_dir, "comprehensive_gps_metrics.csv")
        if not os.path.exists(existing_path):
            print(f"❌ Existing data not found")
            return None

        # Load sample for performance, but get trip identifiers
        existing = pd.read_csv(existing_path)
        existing['timestamp'] = pd.to_datetime(existing['timestamp'])

        print(f"✅ Existing data loaded: {len(existing):,} GPS points")

        # Extract unique trips and vehicles from existing data
        existing_analysis = {
            'unique_vehicles': set(),
            'unique_trips': set(),
            'date_range': (existing['timestamp'].min(), existing['timestamp'].max()),
            'total_points': len(existing)
        }

        if 'VehicleID' in existing.columns:
            existing_analysis['unique_vehicles'] = set(existing['VehicleID'].dropna().unique())

        if 'TripID' in existing.columns:
            existing_analysis['unique_trips'] = set(existing['TripID'].dropna().unique())

        print(f"📈 EXISTING DATA SUMMARY:")
        print(f"   • GPS points: {existing_analysis['total_points']:,}")
        print(f"   • Unique vehicles: {len(existing_analysis['unique_vehicles']):,}")
        print(f"   • Unique trips: {len(existing_analysis['unique_trips']):,}")
        print(f"   • Date range: {existing_analysis['date_range'][0]} to {existing_analysis['date_range'][1]}")

        # Focus on Jan-Feb 2025 period (same as new data)
        jan_feb_existing = existing[
            (existing['timestamp'] >= pd.to_datetime('2025-01-01')) &
            (existing['timestamp'] <= pd.to_datetime('2025-02-28'))
        ]

        if len(jan_feb_existing) > 0:
            jan_feb_vehicles = set(jan_feb_existing['VehicleID'].dropna().unique()) if 'VehicleID' in jan_feb_existing.columns else set()
            jan_feb_trips = set(jan_feb_existing['TripID'].dropna().unique()) if 'TripID' in jan_feb_existing.columns else set()

            print(f"\n🎯 EXISTING JAN-FEB 2025 DATA:")
            print(f"   • GPS points: {len(jan_feb_existing):,}")
            print(f"   • Unique vehicles: {len(jan_feb_vehicles):,}")
            print(f"   • Unique trips: {len(jan_feb_trips):,}")

            existing_analysis['jan_feb_vehicles'] = jan_feb_vehicles
            existing_analysis['jan_feb_trips'] = jan_feb_trips
            existing_analysis['jan_feb_points'] = len(jan_feb_existing)
        else:
            print(f"⚠️  No existing Jan-Feb 2025 data found")
            existing_analysis['jan_feb_vehicles'] = set()
            existing_analysis['jan_feb_trips'] = set()
            existing_analysis['jan_feb_points'] = 0

        return existing_analysis

    def analyze_new_data_details(self):
        """Detailed analysis of new data trip and vehicle patterns"""
        print(f"\n🔍 ANALYZING NEW DATA DETAILS")

        # Load the combined new data
        new_path = os.path.join(self.data_dir, "combined_new_cv_data.csv")
        if not os.path.exists(new_path):
            print(f"❌ Combined new data not found")
            return None

        new_data = pd.read_csv(new_path)
        print(f"✅ New data loaded: {len(new_data):,} trip records")

        new_analysis = {
            'total_trips': len(new_data),
            'unique_vehicles': set(),
            'unique_trips': set(),
            'trip_characteristics': {}
        }

        # Analyze vehicle IDs
        if 'vehicleID' in new_data.columns:
            new_analysis['unique_vehicles'] = set(new_data['vehicleID'].dropna().unique())
            print(f"🚗 Unique vehicles in new data: {len(new_analysis['unique_vehicles']):,}")
        elif 'VehicleID' in new_data.columns:
            new_analysis['unique_vehicles'] = set(new_data['VehicleID'].dropna().unique())
            print(f"🚗 Unique vehicles in new data: {len(new_analysis['unique_vehicles']):,}")

        # Analyze trip IDs
        if 'TripID' in new_data.columns:
            new_analysis['unique_trips'] = set(new_data['TripID'].dropna().unique())
            print(f"🛣️  Unique trips in new data: {len(new_analysis['unique_trips']):,}")

        # Analyze trip characteristics
        numeric_cols = ['SpeedAvg', 'SpeedMax', 'SpeedMin', 'TravelTimeSeconds', 'TravelDistanceMiles']
        for col in numeric_cols:
            if col in new_data.columns:
                new_data[col] = pd.to_numeric(new_data[col], errors='coerce')
                new_analysis['trip_characteristics'][col] = {
                    'mean': new_data[col].mean(),
                    'median': new_data[col].median(),
                    'std': new_data[col].std(),
                    'count': new_data[col].count()
                }

        print(f"\n📊 NEW DATA TRIP CHARACTERISTICS:")
        for col, stats in new_analysis['trip_characteristics'].items():
            if stats['count'] > 0:
                print(f"   • {col}: mean={stats['mean']:.1f}, median={stats['median']:.1f} ({stats['count']:,} records)")

        # Analyze vehicle types
        if 'VehicleType' in new_data.columns:
            vehicle_types = new_data['VehicleType'].value_counts()
            print(f"\n🚙 VEHICLE TYPES:")
            for vtype, count in vehicle_types.head(5).items():
                print(f"   • {vtype}: {count:,} trips ({count/len(new_data)*100:.1f}%)")

        # Geographic analysis if coordinates available
        coord_cols = ['StartPoint', 'EndPoint']
        for col in coord_cols:
            if col in new_data.columns:
                unique_points = new_data[col].nunique()
                print(f"   • Unique {col}: {unique_points:,}")

        return new_analysis

    def compare_vehicle_overlap(self, existing_analysis, new_analysis):
        """Compare vehicle IDs between existing and new data"""
        print(f"\n🔄 COMPARING VEHICLE OVERLAP")

        if not existing_analysis['jan_feb_vehicles'] and not new_analysis['unique_vehicles']:
            print("⚠️  Cannot compare - no vehicle IDs found in datasets")
            return None

        existing_vehicles = existing_analysis['jan_feb_vehicles']
        new_vehicles = new_analysis['unique_vehicles']

        if not existing_vehicles:
            print(f"✅ No existing Jan-Feb vehicles to compare - new data adds {len(new_vehicles):,} vehicles")
            return {
                'overlap_count': 0,
                'overlap_percentage': 0,
                'new_vehicles': len(new_vehicles),
                'is_redundant': False
            }

        overlap = existing_vehicles.intersection(new_vehicles)
        new_only = new_vehicles - existing_vehicles
        existing_only = existing_vehicles - new_vehicles

        overlap_pct = (len(overlap) / len(new_vehicles) * 100) if len(new_vehicles) > 0 else 0

        print(f"📊 VEHICLE COMPARISON RESULTS:")
        print(f"   • Existing vehicles (Jan-Feb): {len(existing_vehicles):,}")
        print(f"   • New data vehicles: {len(new_vehicles):,}")
        print(f"   • Overlapping vehicles: {len(overlap):,} ({overlap_pct:.1f}%)")
        print(f"   • New unique vehicles: {len(new_only):,}")
        print(f"   • Existing-only vehicles: {len(existing_only):,}")

        # Sample some vehicle IDs for inspection
        if len(overlap) > 0:
            sample_overlap = list(overlap)[:5]
            print(f"   • Sample overlapping IDs: {sample_overlap}")

        if len(new_only) > 0:
            sample_new = list(new_only)[:5]
            print(f"   • Sample new vehicle IDs: {sample_new}")

        return {
            'existing_vehicles': len(existing_vehicles),
            'new_vehicles': len(new_vehicles),
            'overlap_count': len(overlap),
            'overlap_percentage': overlap_pct,
            'new_unique_vehicles': len(new_only),
            'is_redundant': overlap_pct > 90  # Consider redundant if >90% overlap
        }

    def compare_trip_overlap(self, existing_analysis, new_analysis):
        """Compare trip IDs and patterns between datasets"""
        print(f"\n🛣️  COMPARING TRIP OVERLAP")

        existing_trips = existing_analysis['jan_feb_trips']
        new_trips = new_analysis['unique_trips']

        if not existing_trips and not new_trips:
            print("⚠️  Cannot compare - no trip IDs found in datasets")
            return None

        if not existing_trips:
            print(f"✅ No existing Jan-Feb trips to compare - new data adds {len(new_trips):,} trips")
            return {
                'overlap_count': 0,
                'overlap_percentage': 0,
                'new_trips': len(new_trips),
                'is_redundant': False
            }

        overlap = existing_trips.intersection(new_trips)
        new_only = new_trips - existing_trips
        existing_only = existing_trips - new_trips

        overlap_pct = (len(overlap) / len(new_trips) * 100) if len(new_trips) > 0 else 0

        print(f"📊 TRIP COMPARISON RESULTS:")
        print(f"   • Existing trips (Jan-Feb): {len(existing_trips):,}")
        print(f"   • New data trips: {len(new_trips):,}")
        print(f"   • Overlapping trips: {len(overlap):,} ({overlap_pct:.1f}%)")
        print(f"   • New unique trips: {len(new_only):,}")
        print(f"   • Existing-only trips: {len(existing_only):,}")

        return {
            'existing_trips': len(existing_trips),
            'new_trips': len(new_trips),
            'overlap_count': len(overlap),
            'overlap_percentage': overlap_pct,
            'new_unique_trips': len(new_only),
            'is_redundant': overlap_pct > 90
        }

    def generate_final_assessment(self, vehicle_comparison, trip_comparison, existing_analysis, new_analysis):
        """Generate final assessment of data value"""
        print(f"\n📋 FINAL ASSESSMENT")
        print("="*50)

        assessment = {
            'analysis_date': datetime.now().isoformat(),
            'data_appears_redundant': False,
            'data_value_score': 0,  # 0-100 scale
            'recommendation': '',
            'key_findings': []
        }

        # Determine redundancy
        vehicle_redundant = vehicle_comparison and vehicle_comparison['is_redundant']
        trip_redundant = trip_comparison and trip_comparison['is_redundant']

        if vehicle_redundant and trip_redundant:
            assessment['data_appears_redundant'] = True
            assessment['data_value_score'] = 10
            assessment['recommendation'] = "REJECT - Data appears to be complete duplicates"
        elif vehicle_redundant or trip_redundant:
            assessment['data_appears_redundant'] = True
            assessment['data_value_score'] = 30
            assessment['recommendation'] = "CAUTION - High overlap, limited additional value"
        else:
            assessment['data_appears_redundant'] = False
            if vehicle_comparison and trip_comparison:
                new_vehicles_pct = (vehicle_comparison['new_unique_vehicles'] / vehicle_comparison['new_vehicles'] * 100) if vehicle_comparison['new_vehicles'] > 0 else 0
                new_trips_pct = (trip_comparison['new_unique_trips'] / trip_comparison['new_trips'] * 100) if trip_comparison['new_trips'] > 0 else 0
                assessment['data_value_score'] = (new_vehicles_pct + new_trips_pct) / 2
            else:
                assessment['data_value_score'] = 75  # Assume good if can't compare

            if assessment['data_value_score'] > 70:
                assessment['recommendation'] = "INTEGRATE - Significant new data value"
            elif assessment['data_value_score'] > 40:
                assessment['recommendation'] = "CONSIDER - Moderate additional value"
            else:
                assessment['recommendation'] = "QUESTION - Limited additional value"

        # Key findings
        if vehicle_comparison:
            assessment['key_findings'].append(f"Vehicle overlap: {vehicle_comparison['overlap_percentage']:.1f}%")
            assessment['key_findings'].append(f"New unique vehicles: {vehicle_comparison['new_unique_vehicles']:,}")

        if trip_comparison:
            assessment['key_findings'].append(f"Trip overlap: {trip_comparison['overlap_percentage']:.1f}%")
            assessment['key_findings'].append(f"New unique trips: {trip_comparison['new_unique_trips']:,}")

        # Display results
        print(f"🎯 KEY FINDINGS:")
        for finding in assessment['key_findings']:
            print(f"   • {finding}")

        print(f"\n📊 DATA VALUE SCORE: {assessment['data_value_score']:.0f}/100")
        print(f"💡 RECOMMENDATION: {assessment['recommendation']}")

        if not assessment['data_appears_redundant']:
            print(f"\n✅ ADDITIONAL VALUE IDENTIFIED:")
            if vehicle_comparison:
                print(f"   • {vehicle_comparison['new_unique_vehicles']:,} new vehicles")
            if trip_comparison:
                print(f"   • {trip_comparison['new_unique_trips']:,} new trips")
            print(f"   • This could strengthen your Jan-Feb 2025 baseline analysis")

        # Save assessment
        assessment_df = pd.DataFrame([assessment])
        assessment_path = os.path.join(self.data_dir, "deep_duplication_assessment.csv")
        assessment_df.to_csv(assessment_path, index=False)
        print(f"\n💾 Assessment saved: {assessment_path}")

        return assessment

def main():
    analyzer = DeepDuplicationAnalyzer()

    # Load and analyze existing data
    existing_analysis = analyzer.load_existing_trip_data()
    if existing_analysis is None:
        print("❌ Cannot proceed without existing data")
        return

    # Analyze new data details
    new_analysis = analyzer.analyze_new_data_details()
    if new_analysis is None:
        print("❌ Cannot proceed without new data")
        return

    # Compare vehicles and trips
    vehicle_comparison = analyzer.compare_vehicle_overlap(existing_analysis, new_analysis)
    trip_comparison = analyzer.compare_trip_overlap(existing_analysis, new_analysis)

    # Generate final assessment
    assessment = analyzer.generate_final_assessment(
        vehicle_comparison, trip_comparison, existing_analysis, new_analysis
    )

    print(f"\n{'='*60}")
    print(f"DEEP DUPLICATION ANALYSIS COMPLETE")

if __name__ == "__main__":
    main()
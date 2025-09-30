"""
Extract actual SH1 corridor coordinates from GIS shapefiles
"""

import geopandas as gpd
import json
import os

def extract_corridor_coordinates():
    """Extract coordinates from the SH1 corridor GIS data"""

    base_dir = "/Volumes/T7/Data/connected_vehicle_data"
    gis_dir = os.path.join(base_dir, "gis", "SH1_Corridor")

    # Try to read the main corridor shapefile
    corridor_shp = os.path.join(gis_dir, "SH1_Corridor_Addison-Rollston.shp")

    if os.path.exists(corridor_shp):
        print(f"Reading SH1 corridor shapefile: {corridor_shp}")

        # Read the shapefile
        gdf = gpd.read_file(corridor_shp)

        print(f"Shapefile info:")
        print(f"  CRS: {gdf.crs}")
        print(f"  Number of features: {len(gdf)}")
        print(f"  Columns: {list(gdf.columns)}")
        print(f"  Geometry types: {gdf.geometry.type.value_counts()}")

        # Convert to WGS84 (EPSG:4326) for web mapping
        if gdf.crs != 'EPSG:4326':
            print(f"Converting from {gdf.crs} to EPSG:4326")
            gdf = gdf.to_crs('EPSG:4326')

        # Extract coordinates from the geometry
        coordinates = []
        for idx, row in gdf.iterrows():
            geom = row.geometry
            if geom.geom_type == 'LineString':
                coords = [[lat, lon] for lon, lat in geom.coords]
                coordinates.extend(coords)
            elif geom.geom_type == 'MultiLineString':
                for line in geom.geoms:
                    coords = [[lat, lon] for lon, lat in line.coords]
                    coordinates.extend(coords)

        print(f"Extracted {len(coordinates)} coordinate points")
        print(f"First 5 coordinates: {coordinates[:5]}")
        print(f"Last 5 coordinates: {coordinates[-5:]}")

        return coordinates

    else:
        print(f"Shapefile not found: {corridor_shp}")
        return None

if __name__ == "__main__":
    coords = extract_corridor_coordinates()

    if coords:
        # Save coordinates to JSON for use in mapping
        output_file = "/Volumes/T7/Data/connected_vehicle_data/output/sh1_corridor_coordinates.json"
        with open(output_file, 'w') as f:
            json.dump(coords, f, indent=2)
        print(f"✅ Coordinates saved to: {output_file}")
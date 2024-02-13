import json
import pandas as pd
import folium
from folium.plugins import HeatMap

def create_heat_map(json_file_path, csv_file_path, pollutant_metric='NOx_g_km'):
    # Load JSON data with road segment coordinates
    with open(json_file_path, 'r') as json_file:
        road_segments_data = json.load(json_file)

    # Create a mapping from BOSCH_network.id to coordinates
    road_id_to_coords = {}
    for feature in road_segments_data['features']:
        road_id = feature['properties']['id']
        coordinates = feature['geometry']['coordinates']
        road_id_to_coords[road_id] = coordinates

    # Load CSV data with emissions
    csv_data = pd.read_csv(csv_file_path)

    # Convert 'NOx_g_km' to numeric, set errors='coerce' to handle non-numeric values
    csv_data['NOx_g_km'] = pd.to_numeric(csv_data['NOx_g_km'], errors='coerce')
    csv_data['CO_g_km'] = pd.to_numeric(csv_data['CO_g_km'], errors='coerce')
    csv_data['CO2_g_km'] = pd.to_numeric(csv_data['CO2_g_km'], errors='coerce')
    csv_data['EC_MJ_km'] = pd.to_numeric(csv_data['EC_MJ_km'], errors='coerce')
    csv_data['PM10_g_km'] = pd.to_numeric(csv_data['PM10_g_km'], errors='coerce')
    csv_data['PM2.5_g_km'] = pd.to_numeric(csv_data['PM2.5_g_km'], errors='coerce')

    # Prepare data for the heatmap
    heatmap_data = []
    print(pollutant_metric)
    for _, row in csv_data.iterrows():
        road_id = row['BOSCH_network.id']
        
        # Skip rows where 'NOx_g_km' is NaN
        if pd.isnull(row[pollutant_metric]):
            continue  # Or assign a default value if preferred
        else:
            value = row[pollutant_metric]

        # If the road segment is in the JSON data, add its coordinates to the heatmap data
        if road_id in road_id_to_coords:
            for coord_pair in road_id_to_coords[road_id]:
                lat, lon = coord_pair[1], coord_pair[0]  # Ensure the order is (latitude, longitude)
                heatmap_data.append([lat, lon, value])

    # Create a Folium map centered on Thessaloniki
    m = folium.Map(location=[40.6401, 22.9444], zoom_start=12)

    # Add heatmap layer
    HeatMap(
        heatmap_data,
        min_opacity=0.5,
        max_zoom=17,
        radius=20,  # Adjust if necessary
        blur=15    # Adjust if necessary
    ).add_to(m)

    html_string = m._repr_html_()

    return html_string
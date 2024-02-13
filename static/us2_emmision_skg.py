import json
import pandas as pd
import folium
from folium.plugins import HeatMap

def create_heat_map(json_file_path, csv_file_path, pollutant_metric='SumOfNOxGKm', start_hour=None, end_hour=None):
    # Load JSON data with road segment coordinates
    with open(json_file_path, 'r') as json_file:
        road_segments_data = json.load(json_file)

    road_id_to_coords = {feature['properties']['id']: feature['geometry']['coordinates']
                         for feature in road_segments_data['features']}

    # Load CSV data with emissions
    csv_data = pd.read_csv(csv_file_path)

    # Convert specified emissions metrics to numeric, handling non-numeric values
    pollutant_columns = ['SumOfNOxGKm', 'SumOfCOGKm', 'SumOfCO2GKm', 'SumOfECMJKm', 'SumOfPM10GKm',
                         'SumOfPM25GKm', 'SumOfVOCGKm', 'SumOfNOxGVkm', 'SumOfCOGVkm', 'SumOfCO2GVkm',
                         'SumOfECMJVkm', 'SumOfPM10GVkm', 'SumOfPM25GVkm', 'SumOfVOCGVkm']
    for col in pollutant_columns:
        csv_data[col] = pd.to_numeric(csv_data[col], errors='coerce')

    # Filter the data by the specified hour range if provided
    if start_hour is not None and end_hour is not None:
        csv_data = csv_data[(csv_data['Hour'] >= start_hour) & (csv_data['Hour'] <= end_hour)]
    # Note: No need for an else part here as we want to include all data if no specific hours are provided

    # Prepare data for the heatmap
    heatmap_data = []
    for _, row in csv_data.iterrows():
        road_id = row['BoschNetworkId']
        if pd.isnull(row[pollutant_metric]):
            continue
        value = row[pollutant_metric]
        if road_id in road_id_to_coords:
            for coord_pair in road_id_to_coords[road_id]:
                lat, lon = coord_pair[1], coord_pair[0]
                heatmap_data.append([lat, lon, value])

    # Create and configure the Folium map
    m = folium.Map(location=[40.6401, 22.9444], zoom_start=12)
    HeatMap(heatmap_data, min_opacity=0.5, max_zoom=17, radius=20, blur=15).add_to(m)
    
    return m._repr_html_()

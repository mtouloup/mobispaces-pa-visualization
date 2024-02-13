import json
import pandas as pd
import folium
import os

def create_traffic_map(json_file_path, csv_file_path):
    # Load JSON data with road segment coordinates
    with open(json_file_path, 'r') as json_file:
        road_segments_data = json.load(json_file)

    # Create a mapping from BOSCH_network.id to coordinates
    road_id_to_coords = {}
    for feature in road_segments_data['features']:
        road_id = feature['properties']['id']
        coordinates = feature['geometry']['coordinates']
        road_id_to_coords[road_id] = coordinates

    # Load CSV data with emissions and traffic data
    csv_data = pd.read_csv(csv_file_path)

    # Prepare data for the traffic lines
    traffic_lines_data = []

    # Define a function to determine the color based on traffic intensity
    def get_traffic_color(value, max_value):
        if value < max_value / 3:
            return 'green'
        elif value < 2 * max_value / 3:
            return 'purple'
        else:
            return 'red'

    # Maximum value for traffic to normalize the color representation
    max_traffic_value = csv_data['Nm_ofVeh'].max()

    for _, row in csv_data.iterrows():
        road_id = row['BOSCH_network.id']
        traffic_value = row['Nm_ofVeh']  # Traffic intensity
        if road_id in road_id_to_coords:
            coordinates = road_id_to_coords[road_id]
            lat_lon_pairs = [(coord[1], coord[0]) for coord in coordinates]  # Convert to (lat, lon)

            # Add traffic lines with color based on intensity
            color = get_traffic_color(traffic_value, max_traffic_value)
            traffic_lines_data.append({'coords': lat_lon_pairs, 'color': color, 'weight': 5})  # Adjust weight as needed

    # Create a Folium map centered on Thessaloniki
    m = folium.Map(location=[40.6401, 22.9444], zoom_start=12)

    # Add traffic lines to the map
    for line_data in traffic_lines_data:
        folium.PolyLine(
            line_data['coords'],
            color=line_data['color'],
            weight=line_data['weight'],
            opacity=0.8
        ).add_to(m)

    html_string = m._repr_html_()

    return html_string
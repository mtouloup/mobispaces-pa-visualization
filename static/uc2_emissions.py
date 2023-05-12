import os
import folium
from folium.plugins import HeatMap
import json

def calculate_center_coordinates(data):

    total_features = 0
    center_latitude = 0
    center_longitude = 0

    # Iterate over each object in the JSON array
    for obj in data:
        features = obj['features']

        # Calculate the center coordinates using the features
        for feature in features:
            geometry = feature['geometry']
            coordinates = geometry['coordinates']

            # Find the average latitude and longitude
            avg_latitude = sum(coord[1] for coord in coordinates) / len(coordinates)
            avg_longitude = sum(coord[0] for coord in coordinates) / len(coordinates)

            center_latitude += avg_latitude
            center_longitude += avg_longitude
            total_features += 1

    # Calculate the average center coordinates
    if total_features > 0:
        center_latitude /= total_features
        center_longitude /= total_features
    else:
        print("No features found.")

    return center_latitude, center_longitude


def create_markers(data, map_obj):
    for obj in data:
        features = obj['features']

        # Iterate over the features and create markers
        for feature in features:
            geometry = feature['geometry']
            coordinates = geometry['coordinates']
            segment = feature['properties']['segment']['segmentNo']
            avg_speed = feature['properties']['traffic']['speedAvg']

            # Find the center coordinate for each feature
            avg_latitude = sum(coord[1] for coord in coordinates) / len(coordinates)
            avg_longitude = sum(coord[0] for coord in coordinates) / len(coordinates)

            popup_text = f'Segment: {segment}<br>Average Speed: {avg_speed:.2f}'
            folium.Marker(location=[avg_latitude, avg_longitude], popup=popup_text).add_to(map_obj)


def create_traffic_speed_map(data):

    # Get the center of the map
    center_latitude, center_longitude = calculate_center_coordinates(data)
    map_center = [center_latitude, center_longitude]

    # Create a map with markers indicating the average speed for each segment
    m = folium.Map(location=map_center, zoom_start=14)
    create_markers(data, m)

    # Create the 'maps' directory if it doesn't exist
    if not os.path.exists('maps'):
        os.makedirs('maps')

    # Save the map as an HTML file
    html_string = m._repr_html_()

    return html_string

def create_heatmap(data):
    
    """
    data_dir = os.path.abspath(os.path.join(os.getcwd(), '.', 'data'))
    data_file = os.path.join(data_dir, 'response_1683810677274.json')
    with open(data_file) as file:
        data = json.load(file)
    """
    # Get the center of the map
    map_center = [0, 0]  # Initialize center coordinates
    num_features = 0

    # Iterate over the data to calculate the center coordinates
    for obj in data:
        features = obj['features']

        # Calculate the center coordinates using the features
        for feature in features:
            geometry = feature['geometry']
            coordinates = geometry['coordinates']

            # Find the average latitude and longitude
            avg_latitude = sum(coord[1] for coord in coordinates) / len(coordinates)
            avg_longitude = sum(coord[0] for coord in coordinates) / len(coordinates)

            map_center[0] += avg_latitude
            map_center[1] += avg_longitude
            num_features += 1

    # Calculate the average center coordinates
    if num_features > 0:
        map_center[0] /= num_features
        map_center[1] /= num_features
    else:
        print("No features found.")

    # Create a map
    m = folium.Map(location=map_center, zoom_start=14)

    # Extract the heatmap data
    heatmap_data = []
    for obj in data:
        features = obj['features']

        for feature in features:
            geometry = feature['geometry']
            coordinates = geometry['coordinates']
            intensity = feature['properties']['traffic']['speedAvg']

            for coord in coordinates:
                heatmap_data.append([coord[1], coord[0], intensity])

    # Create the HeatMap layer
    heat_layer = HeatMap(heatmap_data)

    # Add the HeatMap layer to the map
    heat_layer.add_to(m)

    # Add the custom legend
    gradient = ['#00ff00', '#ffff00', '#ff0000']  # Customize the gradient colors
    labels = ['Low', 'Medium', 'High']  # Customize the legend labels

    legend_html = '''
        <div style="position: fixed;
                    bottom: 50px; left: 50px; width: 120px; height: 80px;
                    border:2px solid grey; z-index:9999; font-size:14px;
                    background-color: rgba(255, 255, 255, 0.9);
                    ">
            <span style="text-align: center; display: block;
                         background-color: rgba(0, 0, 0, 0.7);
                         color: white; padding: 4px;">
                <strong>Legend</strong>
            </span>
            <table style="width:100%; margin-top: 8px; color: black;">
                <tr>
                    <td style="width:33%; background-color:{0}; text-align: center;">{1}</td>
                    <td style="width:33%; background-color:{2}; text-align: center;">{3}</td>
                    <td style="width:33%; background-color:{4}; text-align: center;">{5}</td>
                </tr>
            </table>
        </div>
    '''.format(gradient[0], labels[0], gradient[1], labels[1], gradient[2], labels[2])

    m.get_root().html.add_child(folium.Element(legend_html))

    # Save the map as an HTML file
    html_string = m._repr_html_()

    return html_string


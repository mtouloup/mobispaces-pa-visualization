import pandas as pd
import folium
from folium.plugins import MarkerCluster

def calculate_center(df):
    """
    Calculate the center of the map based on the mean latitude and mean longitude
    in the given dataframe.

    Args:
        df (pandas.DataFrame): A dataframe with columns 'lat' and 'lon'

    Returns:
        (float, float): A tuple containing the mean latitude and mean longitude
    """
    # Calculate the mean latitude and longitude values
    mean_lat = df['lat'].mean()
    mean_lon = df['lon'].mean()

    # Return a tuple containing the mean latitude and longitude
    return mean_lat, mean_lon

def create_map_with_markers(dataset_url, zoom_start, marker_limit):

    df = pd.read_csv(dataset_url, nrows=int(marker_limit))
    df = df.dropna(subset=['lon', 'lat'])

    # Create a map centered on the mean latitude and longitude
    center_lat = df['lat'].mean()
    center_lon = df['lon'].mean()
    my_map = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start)

    # Add markers for each data point
    for _, row in df.iterrows():
        folium.Marker([row['lat'], row['lon']], tooltip=row['shipid']).add_to(my_map)

    # Save the map as an HTML file
    # my_map.save('map.html')

    html_string = my_map._repr_html_()

    return html_string


def create_map_with_trip(dataset_url, zoom_start, marker_limit):

    df = pd.read_csv(dataset_url, nrows=int(marker_limit))
    df = df.dropna(subset=['lon', 'lat'])

    # Create a map object
    m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=zoom_start)

    # Create a marker cluster object
    marker_cluster = MarkerCluster().add_to(m)

    # Add markers to the marker cluster object
    for index, row in df.iterrows():
        popup_text = "Ship ID: {}<br>Timestamp: {}".format(row['shipid'], row['t'])
        folium.Marker(location=[row['lat'], row['lon']], popup=popup_text).add_to(marker_cluster)

    # Create a polyline to show the vessel's trip
    trip_coords = df[['lat', 'lon']].values.tolist()
    folium.PolyLine(locations=trip_coords, color='blue').add_to(m)

    html_string = m._repr_html_()
    # Save the map to an HTML file
    # m.save('map2.html')

    return html_string
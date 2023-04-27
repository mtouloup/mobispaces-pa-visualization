import pandas as pd
import folium
from folium.plugins import MarkerCluster
from io import StringIO

def read_csv_nrows(dataset_url, n):
    """
    Reads the first n rows of a CSV file using Pandas.

    Args:
        file_path (str): The path to the CSV file.
        n (int): The number of rows to read.

    Returns:
        A pandas DataFrame containing the first n rows of the CSV file.
    """
    df = pd.read_csv(dataset_url, nrows=int(n))
    return df

def read_dataset(dataset_url):
    """
    Reads the first n rows of a CSV file using Pandas.

    Args:
        file_path (str): The path to the CSV file.
        n (int): The number of rows to read.

    Returns:
        A pandas DataFrame containing the first n rows of the CSV file.
    """
    df = pd.read_csv(dataset_url)
    return df


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

def get_aggregated_data(dataset_url):
    # Load the dataset
    df = pd.read_csv(dataset_url)
    df = df.dropna(subset=['lon', 'lat'])

    # Convert the BaseDateTime column to a datetime object
    df['t'] = pd.to_datetime(df['t'])
    
    # Group the data by vessel ID and get the latest timestamp for each vessel
    latest_df = df.groupby('shipid')['t'].max().reset_index()
    
    # Merge the latest timestamp with the original dataframe to get the latest data for each vessel
    latest_data = pd.merge(latest_df, df, on=['shipid', 't'])
    
    # Convert the BaseDateTime values to strings
    latest_data['t'] = latest_data['t'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # Select the columns to include in the output
    output_columns = ['t','shipid','lon','lat','heading','course','speed','status','shiptype','draught','destination']
    
    # Select the latest data for each vessel and return as a list of dictionaries
    latest_agg_data = latest_data[output_columns].to_dict('records')
    
    # Return the latest aggregated data
    return latest_agg_data

def get_aggregated_trajectory_data(dataset_url):
    # Load the dataset
    df = pd.read_csv(dataset_url)
    #df = df.dropna(subset=['lon', 'lat'])

    # Group the data by shipid and calculate the average speed, course, and draft for each vessel
    agg_df = df.groupby('shipid').agg({'speed': 'mean', 'course': 'mean', 'draught': 'mean'})
    
    # Convert the average course values to degrees (0-360)
    agg_df['course'] = agg_df['course'].apply(lambda x: x % 360)
    
    # Convert the average speed and draft values to two decimal places
    agg_df['speed'] = agg_df['speed'].round(2)
    agg_df['draught'] = agg_df['draught'].round(2)
    
    # Convert the aggregated data to a list of dictionaries
    agg_data = []
    for index, row in agg_df.iterrows():
        agg_data.append({
            'shipid': index,
            'avg_speed': row['speed'],
            'avg_course': row['course'],
            'avg_draft': row['draught']
        })
        
    # Return the aggregated data
    return agg_data

def create_map_with_markers_and_popups(aggr_data, traj_aggr_data):
    #  convert aggr_data to a pandas DataFrame
    df = pd.DataFrame(aggr_data).dropna(subset=['lon', 'lat'])
    df_traj = pd.DataFrame(traj_aggr_data)
    # Create a map object
    m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=10, scrollWheelZoom=False)
    # Create a marker cluster object
    marker_cluster = MarkerCluster().add_to(m)
    # Add markers to the marker cluster
    for index, row in df_traj.iterrows():
        for index2, row2 in df.iterrows():
            if row2['shipid'] == row['shipid']:
                popup_text = '<table>'
                popup_text += '<tr><td><b>Ship ID:</b></td><td>{}</td></tr>'.format(row['shipid'])
                popup_text += '<tr><td><b>Ship Type:</b></td><td>{}</td></tr>'.format(row2['shiptype'])
                popup_text += '<tr><td><b>Destination:</b></td><td>{}</td></tr>'.format(row2['destination'])
                popup_text += '<tr><td><b>Average Speed:</b></td><td>{:.2f} knots</td></tr>'.format(row['avg_speed'])
                popup_text += '<tr><td><b>Average Course:</b></td><td>{:.2f} degrees</td></tr>'.format(row['avg_course'])
                popup_text += '<tr><td colspan="2"><b>Latest Positions:</b></td></tr>'
                popup_text += '<tr><td>Time:</td><td>{}</td></tr>'.format(row2['t'])
                popup_text += '<tr><td>Latitude:</td><td>{:.4f} deg</td></tr>'.format(row2['lat'])
                popup_text += '<tr><td>Longitude:</td><td>{:.4f} deg</td></tr>'.format(row2['lon'])
                popup_text += '<tr><td colspan="2"><a href="../../pages/dashboard/usecase3_vessel_history.html?data-shipid='+row['shipid']+'" target="_blank">View details</a></td></tr>'
                popup_text += '</table>'
                folium.Marker(location=[row2['lat'], row2['lon']], popup=popup_text).add_to(marker_cluster)

    html_string = m._repr_html_()
    # Save the map to an HTML file
    #m.save('map.html')

    return html_string
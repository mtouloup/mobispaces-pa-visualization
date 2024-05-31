import numpy as np
import pandas as pd
import folium
from folium.plugins import MarkerCluster, AntPath
from haversine import haversine
from static.ais_ship_types import ship_types


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
    # Replace the shiptype number with the corresponding ship type name from the shipTypes mapping object
    latest_data['shiptype'] = latest_data['shiptype'].apply(lambda x: ship_types[x] if x in ship_types else 'Unknown')
    # Select the latest data for each vessel and return as a list of dictionaries
    latest_agg_data = latest_data[output_columns].to_dict('records')
    # Return the latest aggregated data

    return latest_agg_data


def get_aggregated_vessel_data(dataset_url, shipid):
    # Load the dataset
    df = pd.read_csv(dataset_url)
    df = df.dropna(subset=['lon', 'lat'])

    # Convert the BaseDateTime column to a datetime object and then to a string
    df['t'] = pd.to_datetime(df['t']).astype(str)
    # Filter the data for the given shipid
    vessel_data = df[df['shipid'] == shipid]
    # Check if the vessel is moving on the latest data
    moving = False
    latest_data = vessel_data.iloc[-1]
    if latest_data['speed'] > 0:
        moving = True
    # Calculate average, min, and max speed
    avg_speed = vessel_data['speed'].mean()
    min_speed = vessel_data['speed'].min()
    max_speed = vessel_data['speed'].max()
    # Calculate average, min, and max draught
    avg_draught = vessel_data['draught'].mean()
    min_draught = vessel_data['draught'].min()
    max_draught = vessel_data['draught'].max()
    # Calculate travelled distance based on starting and ending coordinates. The result is returned in kilometers.
    start_lat = vessel_data.iloc[0]['lat']
    start_lon = vessel_data.iloc[0]['lon']
    end_lat = latest_data['lat']
    end_lon = latest_data['lon']
    distance = haversine((start_lat, start_lon), (end_lat, end_lon))
    # Select the columns to include in the output
    output_columns = ['t','shipid','lon','lat','heading','course','speed','status','shiptype','draught','destination']
    # Select the latest data for the vessel and return as a list of dictionaries
    latest_data = vessel_data.sort_values('t').tail(1)
    latest_data['moving'] = moving
    latest_data['avg_speed'] = avg_speed
    latest_data['min_speed'] = min_speed
    latest_data['max_speed'] = max_speed
    latest_data['avg_draught'] = avg_draught
    latest_data['min_draught'] = min_draught
    latest_data['max_draught'] = max_draught
    latest_data['distance'] = distance
    # Replace the shiptype number with the corresponding ship type name from the shipTypes mapping object
    latest_data['shiptype'] = latest_data['shiptype'].apply(lambda x: ship_types[x] if x in ship_types else 'Unknown')

    # Convert NaN values to a string
    latest_data = latest_data.fillna(0)

    return latest_data[output_columns + ['moving', 'avg_speed', 'min_speed', 'max_speed', 'avg_draught', 'min_draught', 'max_draught', 'distance']].to_dict('records')

def get_all_vessel_data(dataset_url, shipid):
    # Load the dataset
    df = pd.read_csv(dataset_url)
    df = df.dropna(subset=['lon', 'lat'])

    # Convert the BaseDateTime column to a datetime object and then to a string
    df['t'] = pd.to_datetime(df['t']).astype(str)
    # Filter the data for the given shipid
    vessel_data = df[df['shipid'] == shipid]

    # Replace the shiptype number with the corresponding ship type name from the shipTypes mapping object
    vessel_data['shiptype'] = vessel_data['shiptype'].apply(lambda x: ship_types[x] if x in ship_types else 'Unknown')

    # Convert NaN values to a string
    vessel_data = vessel_data.fillna(0)

    return vessel_data.to_dict('records')


def get_aggregated_statistic_data(dataset_url):
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

def create_map_with_markers_and_popups(aggr_data, traj_aggr_data, token_status):
    print("Token Status = " + token_status)
    #  convert aggr_data to a pandas DataFrame
    df = pd.DataFrame(aggr_data).dropna(subset=['lon', 'lat'])
    df_traj = pd.DataFrame(traj_aggr_data)
    # Create a map object
    m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=15, scrollWheelZoom=False)
    # Create a marker cluster object
    marker_cluster = MarkerCluster().add_to(m)
    
    if token_status == "valid":
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
    elif token_status == "invalid":
        # Add a marker with encrypted data message for invalid or missing token
        for index, row in df.iterrows():
            encrypted_popup_text = '<h1>User Role is not able to decrypt data</h1>'
            folium.Marker(location=[row['lat'], row['lon']], popup=encrypted_popup_text).add_to(marker_cluster)         

    html_string = m._repr_html_()
    # Save the map to an HTML file
    #m.save('map.html')

    return html_string



###### Create Trajectory for a specific vessel ########
#######################################################

def create_vessel_trajectory(dataset_url, shipid):
    df = pd.read_csv(dataset_url)
    df = df[df['shipid'] == str(shipid)]
    df = df.dropna(subset=['lon', 'lat'])

    if df.empty:
        return "No data available for this ship ID."

    m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=7, scrollWheelZoom=False)
    marker_cluster = MarkerCluster().add_to(m)

    for index, row in df.iterrows():
        popup_text = "Ship ID: {}<br>Timestamp: {}".format(row['shipid'], row['t'])
        folium.Marker(location=[row['lat'], row['lon']], popup=popup_text).add_to(marker_cluster)

    # Create a PolyLine object and add it to the map
    trip_coords = df[['lat', 'lon']].values.tolist()
    earliest_timestamp = df['t'].min()
    latest_timestamp = df['t'].max()
    antpath = AntPath(
        locations=trip_coords,
        dash_array=[10, 20],
        delay=800,
        weight=5,
        color='#FF0000',
        pulse_color='#FFFFFF',
        reverse=False,
        # Set the heading of the first arrow based on the direction from the first to the last point
        heading=np.arctan2(trip_coords[-1][1]-trip_coords[0][1], trip_coords[-1][0]-trip_coords[0][0]) * 180/np.pi,
        # Set the heading of the last arrow based on the direction from the second to the last point
        heading_toward_end=np.arctan2(trip_coords[-1][1]-trip_coords[-2][1], trip_coords[-1][0]-trip_coords[-2][0]) * 180/np.pi
    )
    antpath.add_to(m)

    html_string = m._repr_html_()
    return html_string
import pandas as pd
import folium
import os
from sklearn.neighbors import BallTree
import numpy as np

# Define file paths
data_dir = os.path.abspath(os.path.join(os.getcwd(), '.', 'data', 'iroute', 'service execution'))

bus_file = "2024-02-09_report.csv"
bus_file_path = os.path.join(data_dir, 'req4', bus_file)

# Load the bus data as a DataFrame
bus_data = pd.read_csv(bus_file_path)

stops_file = 'stops.csv'
stops_file_path = os.path.join(data_dir, 'yyyymmdd_bus', stops_file)

# Load the stops data as a DataFrame
stops_data = pd.read_csv(stops_file_path)

# Filter for buses E801 - E830
bus_data = bus_data[bus_data['Veicolo'].astype(str).str.startswith('E80') & bus_data['Veicolo'].astype(str).isin([f'E80{i}' for i in range(1, 31)])]

# Normalize battery values (keep only first two digits if greater than 100)
bus_data['Valore'] = bus_data['Valore'].apply(lambda x: int(str(int(x))[:2]) if x > 100 else x)

# Prepare data for BallTree (convert lat/lon to radians)
bus_coords = np.radians(bus_data[['Latitudine', 'Longitudine']].values)
stop_coords = np.radians(stops_data[['stop_lat', 'stop_lon']].values)

# Build BallTree for fast nearest neighbor search
tree = BallTree(stop_coords, metric='haversine')

# Query the nearest stop for each bus point (returns distances in radians and the index of nearest stop)
distances, indices = tree.query(bus_coords, k=1)

# Convert distances from radians to meters
distances_in_meters = distances.flatten() * 6371000  # Earth's radius in meters
indices = indices.flatten()

# Set a threshold for proximity to bus stops (e.g., within 100 meters)
bus_data['closest_stop_id'] = np.where(distances_in_meters <= 100, indices, np.nan)

# Remove rows where no stop is found
bus_data = bus_data.dropna(subset=['closest_stop_id'])

# Map stop indices to stop details
bus_data['closest_stop_id'] = bus_data['closest_stop_id'].astype(int)
bus_data = bus_data.merge(stops_data[['stop_id', 'stop_name', 'stop_lat', 'stop_lon']], left_on='closest_stop_id', right_index=True)

# Sort by DataOra to process stops in order
bus_data = bus_data.sort_values('DataOra')

# Initialize map
map_genova = folium.Map(location=[44.414568, 8.926358], zoom_start=13)

# Group by bus to calculate the battery consumption between consecutive stops
for bus_id, group in bus_data.groupby('Veicolo'):
    group = group.drop_duplicates(subset=['closest_stop_id'], keep='first').reset_index(drop=True)

    # For each stop, calculate the battery consumption rate from the previous stop
    for i in range(1, len(group)):
        current_stop = group.iloc[i]
        previous_stop = group.iloc[i - 1]

        # Calculate the battery consumption
        battery_consumption = abs(previous_stop['Valore'] - current_stop['Valore'])
        
        # We are only interested in positive battery consumption
        if battery_consumption >= 0 and battery_consumption <= 100:  # Valid consumption between 0 and 100%
            popup_text = f"Bus {bus_id} | Stop: {current_stop['stop_name']} | Battery consumption: {battery_consumption}% from previous stop"
        else:
            popup_text = f"Bus {bus_id} | Stop: {current_stop['stop_name']} | Battery consumption: Invalid data"

        # Add a marker for the current stop
        folium.Marker([current_stop['stop_lat'], current_stop['stop_lon']],
                      popup=popup_text).add_to(map_genova)

# Save the map to a file
map_genova.save('bus_stops_with_battery_consumption.html')

import os
import logging
from flask import jsonify, send_file, g
from flask_restx import Namespace, Resource
import static.authenticate as auth
import pandas as pd
import numpy as np  
import matplotlib.pyplot as plt
import io
import seaborn as sns
import folium
import random
from sklearn.neighbors import BallTree

# Set up logging
logging.basicConfig(level=logging.DEBUG)  # Log all messages, including debug

# Helper function to convert hh:mm:ss or negative time to seconds
def parse_time_to_seconds(time_str):
    """ Convert time in hh:mm:ss format to total seconds, handling negative values """
    try:
        if time_str and isinstance(time_str, str):
            is_negative = time_str.startswith('-')
            time_str = time_str.lstrip('-')  # Remove negative sign for processing
            parts = time_str.split(':')
            if len(parts) == 3:
                h, m, s = map(int, parts)
            elif len(parts) == 2:
                h, m, s = 0, *map(int, parts)  # If the format is mm:ss
            elif len(parts) == 1:
                h, m, s = 0, 0, int(parts[0])  # If the format is ss
            else:
                raise ValueError(f"Unexpected time format: {time_str}")
            total_seconds = h * 3600 + m * 60 + s
            return -total_seconds if is_negative else total_seconds
        return 0
    except ValueError as e:
        logging.error(f"Error parsing time '{time_str}': {e}")
        return None


def init_uc1():
    uc1_ns = Namespace('UC1', description='iRoute related operations')

    # Base directory for data files
    try:
        data_dir = os.path.abspath(os.path.join(os.getcwd(), '.', 'data', 'iroute', 'service execution'))
    except Exception as e:
        logging.error(f"Error setting up data directory: {e}")
        raise

    # Outside the function, define a global set to keep track of missing files
    missing_files = set()

    def parse_canbus_file(bus_id, date):
        canbus_dir = os.path.join(data_dir, 'yyyymmdd_Exxx')
        battery_data = {}
        try:
            # Correctly format the date to match the filename structure
            formatted_date = date[:4] + '-' + date[4:6] + '-' + date[6:]  # Convert 'YYYYMMDD' to 'YYYY-MM-DD'
            filename = f"{formatted_date}_E{bus_id[2:]}.csv"
            file_path = os.path.join(canbus_dir, filename)
            
            # Check if the file is already marked as missing
            if filename in missing_files:
                return None
                     
            if not os.path.exists(file_path):
                logging.error(f"CanBus file {file_path} does not exist")
                missing_files.add(filename)  # Mark the file as missing
                return None

            # Attempt to read the CSV file, handling potential issues with encoding or delimiter
            try:
                df = pd.read_csv(file_path, skiprows=1)  # Skip the first line containing "sep=,"
            except Exception as e:
                logging.error(f"Error reading CSV file {file_path}: {e}")
                missing_files.add(filename)  # Mark the file as missing if reading fails
                return None

            # Check for columns
            if 'Date' not in df.columns or 'Signal' not in df.columns or 'Value' not in df.columns:
                logging.error(f"Required columns not found in {file_path}. Columns found: {df.columns.tolist()}")
                missing_files.add(filename)  # Mark the file as missing if columns are not found
                return None

            df['Date'] = pd.to_datetime(df['Date'], format='%Y/%m/%d %H:%M:%S', errors='coerce')  # Convert 'Date' to datetime
            df = df[df['Signal'] == 'tractionBatterySocSOLEL']
            df = df.dropna(subset=['Date'])  # Drop rows where 'Date' could not be parsed
            df = df.sort_values(by='Date')

            if df.empty:
                logging.error(f"No battery data found in file {file_path}")
                return None

            entry_battery = df['Value'].iloc[-1]  # Last recorded battery level
            exit_battery = df['Value'].iloc[0]  # First recorded battery level
            
            battery_data = {
                'depot_entry_battery': entry_battery,
                'depot_exit_battery': exit_battery
            }

        except Exception as e:
            logging.error(f"Error parsing CanBus file for bus ID {bus_id}: {e}")
        return battery_data


    def parse_bus_file(file_path):
        bus_data = []
        valid_bus_ids = {f"0E{str(i).zfill(3)}" for i in range(801, 831)}  # Set of valid bus IDs 0E801 - 0E830

        try:
            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        values = line.split(',')
                        if len(values) < 27:
                            continue
                    
                        bus_id = values[0]
                        if bus_id not in valid_bus_ids:
                            continue

                        block_id = values[4] or ''  # Handle missing block_id
                        depot_entry_time = values[13] or ''  # Handle missing depot_entry_time
                        depot_exit_time = values[14] or ''  # Handle missing depot_exit_time
                        
                        try:
                            odometer_start = float(values[12]) if values[12] else 0.0
                            odometer_end = float(values[13]) if values[13] else odometer_start
                        except ValueError:
                            odometer_start = 0.0
                            odometer_end = 0.0

                        distance_traveled = odometer_end - odometer_start

                        bus_info = {
                            "bus_id": bus_id,
                            "block_id": block_id,
                            "depot_entry_time": depot_entry_time,
                            "depot_exit_time": depot_exit_time,
                            "distance_traveled_km": distance_traveled
                        }
                        bus_data.append(bus_info)

                    except Exception as e:
                        logging.error(f"Error processing line '{line.strip()}': {e}")
                        continue

        except Exception as e:
            logging.error(f"Error parsing bus file {file_path}: {e}")
        return bus_data
    
    @uc1_ns.route('/battery_dashboard')
    class BatteryDashboard(Resource):
        @auth.require_token
        def get(self, token_status="valid"):
            token_status = getattr(g, 'token_status', 'none')

            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403
            
            try:
                all_buses_data = []
                filename = "20231015_bus.csv"
                date = filename.split('_')[0]
                file_path = os.path.join(data_dir, 'yyyymmdd_bus', filename)

                bus_data = parse_bus_file(file_path)

                for bus in bus_data:
                    battery_data = parse_canbus_file(bus['bus_id'], date)
                    if battery_data:
                        bus.update(battery_data)
                        all_buses_data.append(bus)

                if not all_buses_data:
                    return jsonify({"error": "No data available for battery dashboard"}), 404

                # Convert data to JSON serializable types
                for bus in all_buses_data:
                    for key, value in bus.items():
                        if isinstance(value, pd._libs.tslibs.timestamps.Timestamp):
                            bus[key] = value.isoformat()
                        elif isinstance(value, (np.int64, np.int32)):
                            bus[key] = int(value)

                #return jsonify(all_buses_data)

                    # Convert the JSON data to a DataFrame
                # Convert the JSON data to a DataFrame
                df = pd.DataFrame(all_buses_data)
                
                # Remove duplicates based on bus_id (if that's the case)
                df = df.drop_duplicates(subset='bus_id')

                # Extract relevant columns for the heatmap (battery-related data)
                battery_data = df[['bus_id', 'depot_entry_battery', 'depot_exit_battery']]
                
                # Set bus_id as the index
                battery_data.set_index('bus_id', inplace=True)
                
                # Adjust the size of the heatmap
                plt.figure(figsize=(10, 6))
                
                # Create the heatmap using seaborn
                sns.heatmap(battery_data, annot=True, cmap="YlGnBu", cbar=True, linewidths=0.5)

                # Rotate the x-axis labels for clarity
                plt.xticks(rotation=45, ha='right')
                
                # Add better labels
                plt.title('Battery Levels: Depot Entry vs Exit')
                plt.xlabel('Battery Levels')
                plt.ylabel('Bus ID')
                
                # Save the plot to a bytes buffer instead of displaying it
                img = io.BytesIO()
                plt.tight_layout()  # Ensure everything fits well
                plt.savefig(img, format='png')
                img.seek(0)
                
                # Return the image as a response
                return send_file(img, mimetype='image/png')
            except Exception as e:
                logging.error(f"Unhandled exception in generating battery dashboard: {e}")
                return jsonify({"error": str(e)}), 500

    @uc1_ns.route('/average_delays/graph')
    class AverageDelaysGraph(Resource):
        @auth.require_token
        def get(self, token_status="valid"):
            token_status = getattr(g, 'token_status', 'none')

            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403
            
            try:
                # Calculate average delays and punctuality for buses 0E801-0E830
                average_delays, punctuality_percentages = self.calculate_average_delays_for_selected_buses()

                if not average_delays or not punctuality_percentages:
                    return jsonify({"error": "No delay or punctuality data available"}), 404

                # Plot the delays and punctuality percentages
                fig = self.plot_average_delays_graph(average_delays, punctuality_percentages)

                # Save the figure to a BytesIO object
                from io import BytesIO
                img = BytesIO()
                fig.savefig(img, format='png')
                img.seek(0)

                # Return the image as a response
                from flask import send_file
                return send_file(img, mimetype='image/png')

            except Exception as e:
                logging.error(f"Unhandled exception in generating average delays graph: {e}")
                return jsonify({"error": str(e)}), 500

        def calculate_average_delays_for_selected_buses(self):
            delays = {}
            counts = {}
            punctual_counts = {}  # New dictionary to store punctual counts (within -300s and +300s)

            valid_bus_ids = {f"0E{str(i).zfill(3)}" for i in range(801, 831)}  # Set of valid bus IDs 0E801 - 0E830

            try:
                # Iterate over all CSV files in the directory
                for filename in os.listdir(os.path.join(data_dir, 'yyyymmdd_bus')):
                    if filename.endswith('_bus.csv'):
                        file_path = os.path.join(data_dir, 'yyyymmdd_bus', filename)

                        with open(file_path, 'r') as f:
                            for line in f:
                                try:
                                    values = line.split(',')
                                    if len(values) < 27:  # Ensuring there are enough columns
                                        continue
                                    
                                    bus_id = values[0]
                                    if bus_id not in valid_bus_ids:
                                        continue

                                    bus_line = values[10]  # 11th value after the 10th comma
                                    delay_str = values[25]  # 26th value after the 26th comma
                                    delay_seconds = parse_time_to_seconds(delay_str)

                                    if delay_seconds is None:
                                        continue  # Skip processing if time parsing failed

                                    # Initialize data for new bus lines
                                    if bus_line not in delays:
                                        delays[bus_line] = 0
                                        counts[bus_line] = 0
                                        punctual_counts[bus_line] = 0  # Initialize punctuality counter for each bus line

                                    delays[bus_line] += delay_seconds
                                    counts[bus_line] += 1

                                    # Count punctual events (delay between -300 and +300 seconds)
                                    if -300 <= delay_seconds <= 300:
                                        punctual_counts[bus_line] += 1

                                except Exception as e:
                                    logging.error(f"Error processing line '{line.strip()}': {e}")
                                    continue

                # Calculate average delays and convert to minutes, also calculate punctuality percentage
                average_delays = {
                    bus_line: (delays[bus_line] / counts[bus_line]) / 60  # Convert to minutes
                    for bus_line in delays
                }
                punctuality_percentages = {
                    bus_line: (punctual_counts[bus_line] / counts[bus_line]) * 100  # Calculate percentage of punctual events
                    for bus_line in punctual_counts
                }

                return average_delays, punctuality_percentages

            except Exception as e:
                logging.error(f"Error calculating average delays from datasets: {e}")
                return None, None

        def plot_average_delays_graph(self, average_delays, punctuality_percentages):
            bus_lines = list(average_delays.keys())
            delays = [delay for delay in average_delays.values()]
            punctualities = [punctuality_percentages[bus_line] for bus_line in bus_lines]  # Get punctuality percentages

            # Create a figure with two subplots (bar charts for delays and punctuality)
            fig, ax1 = plt.subplots(figsize=(10, 6))

            # Plot average delays
            sns.barplot(x=bus_lines, y=delays, palette="viridis", ax=ax1)
            ax1.set_xlabel('Bus Line')
            ax1.set_ylabel('Average Delay (minutes)', color='b')
            ax1.tick_params(axis='y', labelcolor='b')
            plt.xticks(rotation=45)

            # Create another y-axis for punctuality percentages
            ax2 = ax1.twinx()
            sns.lineplot(x=bus_lines, y=punctualities, marker='o', color='r', ax=ax2)
            ax2.set_ylabel('Punctuality (%)', color='r')
            ax2.tick_params(axis='y', labelcolor='r')

            plt.title('Average Delay per Bus Line with Punctuality Percentage (0E801 - 0E830)')
            plt.tight_layout()

            return fig

    @uc1_ns.route('/bus_trajectories_map')
    class BusTrajectoriesMap(Resource):
        @auth.require_token
        def get(self, token_status="valid"):
            token_status = getattr(g, 'token_status', 'none')
            
            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403
            
            try:
                # Define the file paths (update with correct paths)
                data_dir = os.path.abspath(os.path.join(os.getcwd(), '.', 'data', 'iroute', 'service execution'))
                bus_file = "20231015_bus.csv"
                bus_file_path = os.path.join(data_dir, 'yyyymmdd_bus', bus_file)

                percorsi_file = "Percorsi_bus.xlsx"
                percorsi_file_path = os.path.join(data_dir, 'yyyymmdd_bus', percorsi_file)

                stops_file = 'stops.csv'
                stops_file_path = os.path.join(data_dir, 'yyyymmdd_bus', stops_file)

                # Load the bus data (20231015_bus.csv) without headers
                bus_df = pd.read_csv(bus_file_path, header=None)

                # Load the percorsi bus data (Percorsi_bus.xlsx for Path IDs for lines 003 and 008)
                percorsi_df = pd.read_excel(percorsi_file_path)

                # Load the stops data (stops.csv for stop coordinates)
                stops_df = pd.read_csv(stops_file_path)

                # Filter the Percorsi Bus file for lines '003' and '008' using the 'LINEA' column
                line_003_008_ids = percorsi_df[percorsi_df['LINEA'].isin(['003', '008'])]['ID_PERCORSO'].tolist()

                # Filter the bus data using Path ID from column 11 (index 10)
                filtered_bus_data = bus_df[bus_df[10].isin(line_003_008_ids)]

                # Merge filtered bus data with stops_df using Stop ID (column 8 of bus_df matches 'stop_code' in stops_df)
                merged_data = pd.merge(filtered_bus_data, stops_df, left_on=8, right_on='stop_code', how='left')

                # Group data by Block ID (column 4, index 3) and Path ID (column 11, index 10) to define trips
                trip_groups = merged_data.groupby([3, 10])

                # Initialize a map centered around Genova
                map_genova = folium.Map(location=[44.414568, 8.926358], zoom_start=13)

                # Generate random colors for different trips
                def generate_random_color():
                    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

                # Function to calculate average delay (assumed in column 26, index 25 in seconds)
                def calculate_average_delay(trip_data):
                    delay_seconds = trip_data[25].dropna()  # Drop NaN values
                    if len(delay_seconds) > 0:
                        average_delay = delay_seconds.mean() / 60  # Convert to minutes
                        return round(average_delay, 2)
                    else:
                        return None

                # Loop over each trip group
                for (block_id, path_id), trip_data in trip_groups:
                    # Store coordinates for polyline
                    trip_coords = []

                    # Calculate average delay for the trip
                    average_delay = calculate_average_delay(trip_data)

                    # Get the stops for this trip and plot them on the map
                    for idx, stop in trip_data.iterrows():
                        stop_lat = stop['stop_lat']
                        stop_lon = stop['stop_lon']

                        # Check if lat/lon are valid (not NaN)
                        if pd.notna(stop_lat) and pd.notna(stop_lon):
                            trip_coords.append([stop_lat, stop_lon])  # Append the stop coordinates to the list

                            # Add a marker for each stop
                            folium.Marker(
                                location=[stop_lat, stop_lon],
                                popup=f"Block ID: {block_id}, Path ID: {path_id}, Stop Name: {stop['stop_name']}",
                                icon=folium.Icon(color="blue")
                            ).add_to(map_genova)

                    # Plot polyline for this trip (if we have at least 2 coordinates)
                    if len(trip_coords) > 1:
                        polyline = folium.PolyLine(
                            trip_coords,
                            color=generate_random_color(),
                            weight=5,
                            opacity=0.7,
                            tooltip=f"Block ID: {block_id}, Path ID: {path_id}, Avg Delay: {average_delay} mins" if average_delay else f"Block ID: {block_id}, Path ID: {path_id}"
                        )
                        polyline.add_to(map_genova)

                # Save the map to a bytes buffer instead of displaying it
                output_html_path = os.path.join(os.getcwd(), 'genova_bus_map_trajectories_with_delay.html')
                map_genova.save(output_html_path)

                # Return the generated HTML map as a downloadable file
                return send_file(output_html_path, as_attachment=True, mimetype='text/html')

            except Exception as e:
                logging.error(f"Error generating bus trajectories map: {e}")
                return jsonify({"error": str(e)}), 500


    @uc1_ns.route('/bus_stops_with_battery_consumption/<string:bus_id>')
    class BusStopsWithBatteryConsumption(Resource):
        @auth.require_token
        def get(self, bus_id, token_status="valid"):
            token_status = getattr(g, 'token_status', 'none')
            token_status = "valid"
            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403

            # Define valid bus IDs
            valid_bus_ids = [f'E80{i}' for i in range(1, 31)]

            # Check if bus_id is within the valid range
            if bus_id not in valid_bus_ids:
                return {"error": f"Bus ID '{bus_id}' is not in the valid range (E801-E830)"}, 400

            try:
                # Define file paths
                data_dir = os.path.abspath(os.path.join(os.getcwd(), '.', 'data', 'iroute', 'service execution'))

                bus_file = "2024-02-09_report.csv"
                bus_file_path = os.path.join(data_dir, 'req4', bus_file)

                stops_file = 'stops.csv'
                stops_file_path = os.path.join(data_dir, 'yyyymmdd_bus', stops_file)

                # Load the bus data and stops data as DataFrames
                bus_data = pd.read_csv(bus_file_path)
                stops_data = pd.read_csv(stops_file_path)

                # Filter for the specified bus only
                bus_data = bus_data[bus_data['Veicolo'] == bus_id]

                # Check if bus_id exists in the data
                if bus_data.empty:
                    return {"error": f"Bus ID '{bus_id}' not found in the data."}, 404

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

                # Initialize the map
                map_genova = folium.Map(location=[44.414568, 8.926358], zoom_start=13)

                # Group by each stop and accumulate all battery levels and timestamps
                stops_grouped = bus_data.groupby(['stop_id', 'stop_name', 'stop_lat', 'stop_lon'])

                for (stop_id, stop_name, stop_lat, stop_lon), group in stops_grouped:
                    # Prepare a popup text showing all battery levels recorded at this stop
                    popup_text = f"<strong>Stop: {stop_name}</strong><br><br>"

                    for _, row in group.iterrows():
                        time = row['DataOra']  # Assuming 'DataOra' is the timestamp column
                        battery_level = row['Valore']
                        popup_text += f"Bus {bus_id} | Battery level: {battery_level}% | Time: {time}<br>"

                    # Add a marker for the stop with all recorded battery values
                    folium.Marker(
                        [stop_lat, stop_lon],
                        popup=folium.Popup(popup_text, max_width=300)
                    ).add_to(map_genova)

                # Save the map to a file
                output_html_path = os.path.join(os.getcwd(), 'bus_stops_with_battery_consumption.html')
                map_genova.save(output_html_path)

                # Return the generated HTML map as a downloadable file
                return send_file(output_html_path, as_attachment=True, mimetype='text/html')

            except Exception as e:
                logging.error(f"Unhandled exception in generating bus stops with battery consumption: {e}")
                return jsonify({"error": str(e)}), 500




    return uc1_ns


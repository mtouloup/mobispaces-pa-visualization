import os
import logging
from flask import jsonify, send_file
from flask_restx import Namespace, Resource
import static.authenticate as auth
import pandas as pd
import numpy as np  
import matplotlib.pyplot as plt
import io
import seaborn as sns

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
        def get(self):
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
        def get(self):
            try:
                # Calculate average delays for buses 0E801-0E830
                average_delays = self.calculate_average_delays_for_selected_buses()

                if not average_delays:
                    return jsonify({"error": "No delay data available"}), 404

                # Plot the delays
                fig = self.plot_average_delays_graph(average_delays)

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

                                    if bus_line not in delays:
                                        delays[bus_line] = 0
                                        counts[bus_line] = 0
                                    
                                    delays[bus_line] += delay_seconds
                                    counts[bus_line] += 1
                                except Exception as e:
                                    logging.error(f"Error processing line '{line.strip()}': {e}")
                                    continue

                # Calculate average delays and convert to minutes
                average_delays = {
                    bus_line: (delays[bus_line] / counts[bus_line]) / 60
                    for bus_line in delays
                }
                return average_delays
            
            except Exception as e:
                logging.error(f"Error calculating average delays from datasets: {e}")
                return None

        def plot_average_delays_graph(self, average_delays):
            import matplotlib.pyplot as plt
            import seaborn as sns

            bus_lines = list(average_delays.keys())
            delays = [delay for delay in average_delays.values()]

            plt.figure(figsize=(10, 6))
            sns.barplot(x=bus_lines, y=delays, palette="viridis")
            plt.xlabel('Bus Line')
            plt.ylabel('Average Delay (minutes)')
            plt.title('Average Delay per Bus Line (0E801 - 0E830)')
            plt.xticks(rotation=45)
            plt.tight_layout()

            return plt.gcf()


    return uc1_ns

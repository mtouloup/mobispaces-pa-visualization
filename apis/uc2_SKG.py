from flask import Response, g, request
from flask_restx import Namespace, Resource, reqparse
import static.authenticate as auth
import static.us2_emmision_skg as heat_map_gen
import static.us2_traffic_skg as traffic_map_gen
import os
from werkzeug.utils import secure_filename
import pandas as pd


def init_uc2_skg():
    uc2_ns_skg = Namespace('UC2_SKG', description='UC2 related operations for the city of Thessaloniki')

    ALLOWED_FORMATS_MAP = {'div', 'html'}

    # Helper function to wrap map div in HTML
    def render_html_template(map_content):
        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Map View</title>
            <!-- Add any required CSS or JS for your map library here -->
        </head>
        <body>
            {content}
        </body>
        </html>
        """
        return html_template.format(content=map_content)
             
    @uc2_ns_skg.route('/SKG/heat_map', methods=['GET', 'POST'])
    @uc2_ns_skg.route('/SKG/heat_map/export/<export_format>', methods=['GET', 'POST'])
    class get_uc2_SKG_heat_map(Resource):
        @auth.require_token
        def get(self, export_format='div'):
            parser = reqparse.RequestParser()
            pollutant_choices = ['SumOfNOxGKm', 'SumOfPM10GKm', 'SumOfPM25GKm', 'SumOfCOGKm', 'SumOfCO2GKm','SumOfECMJKm', 'SumOfVOCGKm']
            parser.add_argument('pollutant_metric', type=str, default='SumOfNOxGKm', choices=pollutant_choices)
            parser.add_argument('start_hour', type=int, help="Start hour for filtering data", required=False)
            parser.add_argument('end_hour', type=int, help="End hour for filtering data", required=False)
            
            args = parser.parse_args()
            start_hour = args.get('start_hour')
            end_hour = args.get('end_hour')

            # Range checks
            if (start_hour is not None and not (0 <= start_hour <= 23)) or (end_hour is not None and not (0 <= end_hour <= 23)):
                return {"error": "Hours must be between 0 and 23 inclusive."}, 400

            # Logical consistency check
            if start_hour is not None and end_hour is not None and start_hour > end_hour:
                return {"error": "Start hour must be less than or equal to end hour."}, 400

            pollutant_metric = args['pollutant_metric']

            token_status = getattr(g, 'token_status', 'none')
            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403
                            
            if export_format not in ALLOWED_FORMATS_MAP:
                return {"error": "Invalid format. Allowed values are: 'div', 'html'."}, 400

            # Define the data directory and file paths
            data_dir = os.path.abspath(os.path.join(os.getcwd(), '.', 'data'))
            # Use the uploaded file if exists, otherwise default
            csv_file_path = os.path.join(data_dir, request.args.get('uploaded_file', 'demo_roadtrafficemissions_uc_v2.csv'))
            json_file_data = os.path.join(data_dir, 'uc2_map_v2.json')

            # Create the map with traffic data, passing the selected pollutant metric
            heat_map = heat_map_gen.create_heat_map(json_file_data, csv_file_path, pollutant_metric, start_hour, end_hour)

            if export_format == 'html':
                return Response(
                    render_html_template(heat_map),
                    mimetype="text/html",
                    headers={"Content-disposition": "attachment; filename=map.html"}
                )
            else:
                return heat_map, 200

        def post(self, export_format='div'):
            if 'file' not in request.files:
                return {"error": "No file part in the request"}, 400
            file = request.files['file']
            if file.filename == '':
                return {"error": "No selected file"}, 400

            filename = secure_filename(file.filename)
            if filename.split('.')[-1].lower() != 'csv':
                return {"error": "Invalid file type. Only CSV files are allowed."}, 400

            data_dir = os.path.abspath(os.path.join(os.getcwd(), '.', 'data'))
            filepath = os.path.join(data_dir, filename)
            file.save(filepath)

            # Validate CSV schema
            expected_columns = set(["LinkId", "BoschNetworkId", "BoschNetworkLength", "Month", "Day", "Hour", 
                                    "NmOfVeh", "AvgSpeedH", "SumOfNOxG", "SumOfCOG", "SumOfCO2G", "SumOfECMJ", 
                                    "SumOfPM10G", "SumOfPM25G", "SumOfVOCG", "SumOfNOxGKm", "SumOfCOGKm", 
                                    "SumOfCO2GKm", "SumOfECMJKm", "SumOfPM10GKm", "SumOfPM25GKm", "SumOfVOCGKm", 
                                    "SumOfNOxGVkm", "SumOfCOGVkm", "SumOfCO2GVkm", "SumOfECMJVkm", "SumOfPM10GVkm", 
                                    "SumOfPM25GVkm", "SumOfVOCGVkm"])
            try:
                df = pd.read_csv(filepath)
                if set(df.columns) != expected_columns:
                    os.remove(filepath)  # Remove the file if it doesn't match the schema
                    return {"error": "Uploaded file does not match the required schema"}, 400
            except Exception as e:
                return {"error": str(e)}, 400

            # After successful upload and validation, generate and return the heat map
            # Extract these from form data or use defaults if not provided
            pollutant_metric = request.form.get('pollutant_metric', 'SumOfNOxGKm')
            start_hour = request.form.get('start_hour', None)
            end_hour = request.form.get('end_hour', None)
            start_hour = int(start_hour) if start_hour is not None else None
            end_hour = int(end_hour) if end_hour is not None else None

            # Re-use the heat map generation logic
            return self.generate_heat_map(export_format, pollutant_metric, start_hour, end_hour, filepath)

        def generate_heat_map(self, export_format, pollutant_metric, start_hour, end_hour, csv_file_path):
            json_file_path = os.path.abspath(os.path.join(os.getcwd(), '.', 'data', 'uc2_map_v2.json'))
            heat_map = heat_map_gen.create_heat_map(json_file_path, csv_file_path, pollutant_metric, start_hour, end_hour)
            
            if export_format == 'html':
                return Response(
                    render_html_template(heat_map),
                    mimetype="text/html",
                    headers={"Content-disposition": "attachment; filename=map.html"}
                )
            else:
                return heat_map, 200
            

    @uc2_ns_skg.route('/SKG/traffic', methods=['GET'], defaults={'export_format': 'div'})
    @uc2_ns_skg.route('/SKG/traffic/export/<export_format>', methods=['GET'])
    class get_uc2_SKG_traffic_map(Resource):   
        @auth.require_token
        def get(self,export_format='div', token_status="valid"):
            token_status = getattr(g, 'token_status', 'none')

            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403
                        
            if export_format not in ALLOWED_FORMATS_MAP:
                return {"error": "Invalid format. Allowed values are: 'div', 'html'."}, 400

           # Define the data directory and file paths
            data_dir = os.path.abspath(os.path.join(os.getcwd(), '.', 'data'))
            json_file_data = os.path.join(data_dir, 'uc2_map_v2.json')
            csv_file_data = os.path.join(data_dir, 'demo_roadtrafficemissions_uc_v2.csv')

            # Create the map with traffic data
            traffic_map = traffic_map_gen.create_traffic_map(json_file_data, csv_file_data)

            if export_format == 'html':
                    return Response(
                        render_html_template(traffic_map),
                        mimetype="text/html",
                        headers={"Content-disposition": "attachment; filename=map.html"}
                    )
            else:
                return traffic_map,200
            

    return uc2_ns_skg


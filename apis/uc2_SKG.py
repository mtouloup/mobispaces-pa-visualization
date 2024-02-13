from flask import Response, g
from flask_restx import Namespace, Resource, reqparse
import static.authenticate as auth
import static.us2_emmision_skg as heat_map_gen
import static.us2_traffic_skg as traffic_map_gen
import os

def init_uc2_skg():
    uc2_ns_skg = Namespace('UC2_SKG', description='UC2 related operationsfor the city of Thessaloniki')

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
             
    @uc2_ns_skg.route('/SKG/heat_map', methods=['GET'])
    @uc2_ns_skg.route('/SKG/heat_map/export/<export_format>', methods=['GET'])
    class get_uc2_SKG_heat_map(Resource):
        @auth.require_token
        def get(self, export_format='div'):
            parser = reqparse.RequestParser()
            parser.add_argument('pollutant_metric', type=str, default='NOx_g_km', choices=['NOx_g_km', 'CO_g_km', 'CO2_g_km', 'EC_MJ_km', 'PM10_g_km', 'PM2.5_g_km'])
            args = parser.parse_args()
            pollutant_metric = args['pollutant_metric']

            token_status = getattr(g, 'token_status', 'none')
            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403
                        
            if export_format not in ALLOWED_FORMATS_MAP:
                return {"error": "Invalid format. Allowed values are: 'div', 'html'."}, 400

            # Define the data directory and file paths
            data_dir = os.path.abspath(os.path.join(os.getcwd(), '.', 'data'))
            json_file_data = os.path.join(data_dir, 'uc2_map.json')
            csv_file_data = os.path.join(data_dir, 'demo_roadtrafficemissions_uc2.csv')

            # Create the map with traffic data, passing the selected pollutant metric
            heat_map = heat_map_gen.create_heat_map(json_file_data, csv_file_data, pollutant_metric)

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
            json_file_data = os.path.join(data_dir, 'uc2_map.json')
            csv_file_data = os.path.join(data_dir, 'demo_roadtrafficemissions_uc2.csv')

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


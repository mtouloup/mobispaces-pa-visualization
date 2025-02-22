from flask_restx import Namespace, Resource
import static.load_trajectories as lt
import static.authenticate as auth
from flask import jsonify, Response, g
import os
import io
import pandas as pd

def init_uc3():
    uc3_ns = Namespace('UC3', description='UC3 related operations')

    ALLOWED_FORMATS_MAP = {'div', 'html'}
    ALLOWED_FORMATS_DATA = {'json', 'csv', 'xlsx'}

    # Define the local file path to the dataset
    data_dir = os.path.abspath(os.path.join(os.getcwd(), '.', 'data'))
    decrypted_dataset_path = os.path.join(data_dir, 'ais.csv')
    mini_encrypted_dataset_path = os.path.join(data_dir, 'ais_mini_encrypted.csv')

    ais_dataset_path_2025 = os.path.join(data_dir, 'ais_data_2025', 'ais_data.csv')  # New AIS data
    rf_dataset_path_2025 = os.path.join(data_dir, 'ais_data_2025', 'doa_data.csv')   # RF data

    # Helper function for data export format
    def data_to_export_format(data, export_format):
        if export_format == "csv":
            df = pd.json_normalize(data)  
            df.columns = df.columns.str.replace('payload.', '')  
            return Response(
                df.to_csv(index=False),
                mimetype="text/csv",
                headers={"Content-disposition": "attachment; filename=data.csv"}
            )
        elif export_format == "xlsx":
            df = pd.json_normalize(data)  
            df.columns = df.columns.str.replace('payload.', '')  
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Sheet1', index=False)
                writer.close()
            output.seek(0)
            return Response(
                output,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-disposition": "attachment; filename=data.xlsx"}
            )
        else:
            return jsonify(data)    
    
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
    

    @uc3_ns.route('/trip_map/<zoom>/<markers>', defaults={'export_format': 'div'})
    @uc3_ns.route('/trip_map/<zoom>/<markers>/export/<export_format>')
    class map_trip(Resource):
        @auth.require_token
        def get(self, zoom, markers, export_format='div', token_status="valid"):
            token_status = getattr(g, 'token_status', 'none')

            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403
                        
            user_role = getattr(g, 'user_role', 'none')

            if export_format not in ALLOWED_FORMATS_MAP:
                return {"error": "Invalid format. Allowed values are: 'div', 'html'."}, 400
            html_map = lt.create_map_with_trip(
                dataset_url=decrypted_dataset_path, 
                zoom_start=zoom, 
                marker_limit=markers
            )
            if export_format == 'html':
                return Response(
                    render_html_template(html_map),
                    mimetype="text/html",
                    headers={"Content-disposition": "attachment; filename=map.html"}
                )
            else:
                return html_map

    @uc3_ns.route('/map/<zoom>/<markers>', defaults={'export_format': 'div'})
    @uc3_ns.route('/map/<zoom>/<markers>/export/<export_format>')
    class marker_map(Resource):
        @auth.require_token
        def get(self, zoom, markers, export_format='div', token_status="valid"):
            token_status = getattr(g, 'token_status', 'none')

            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403
                        
            user_role = getattr(g, 'user_role', 'none')
            if export_format not in ALLOWED_FORMATS_MAP:
                return {"error": "Invalid format. Allowed values are: 'div', 'html'."}, 400            
            html_map = lt.create_map_with_markers(
                dataset_url=decrypted_dataset_path, 
                zoom_start=zoom, 
                marker_limit=markers
            )
            if export_format == 'html':
                return Response(
                    render_html_template(html_map),
                    mimetype="text/html",
                    headers={"Content-disposition": "attachment; filename=map.html"}
                )
            else:
                return html_map

    @uc3_ns.route('/data/<number_of_rows>')
    class get_Data(Resource):
        @auth.require_token
        def get(self, number_of_rows, token_status="valid"):
            token_status = getattr(g, 'token_status', 'none')

            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403
                        
            user_role = getattr(g, 'user_role', 'none')
            data = lt.read_csv_nrows(
                dataset_url=decrypted_dataset_path, 
                n=number_of_rows
            )
            response = data.to_json(orient='records')
            return jsonify(response)


    # ### API for getting aggregated data for all vessels ###
    ###########################################################
    @uc3_ns.route('/data/aggregated')
    class get_aggr_data(Resource):
        @auth.require_token
        def get(self, token_status="valid"):
            token_status = getattr(g, 'token_status', 'none')

            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403
            
            user_role = getattr(g, 'user_role', 'none')
            return lt.get_aggregated_data(dataset_url=decrypted_dataset_path)
        
    # ### API for getting aggregated data for specific vessels based on shipid ###
    ##############################################################################
    @uc3_ns.route('/data/aggregated/<shipid>')
    class get_aggr_vessel_data(Resource):
        @auth.require_token
        def get(self, shipid, token_status="valid"):
            token_status = getattr(g, 'token_status', 'none')

            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403
            
            user_role = getattr(g, 'user_role', 'none')
            return lt.get_aggregated_vessel_data(dataset_url=decrypted_dataset_path, shipid=shipid)

    # ### API for getting aggregated statistic data for all vessels ###
    ###########################################################
    @uc3_ns.route('/statistic_data/aggregated')
    class get_traj_aggr_data(Resource):
        @auth.require_token
        def get(self, token_status="valid"):
            token_status = getattr(g, 'token_status', 'none')

            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403
            
            user_role = getattr(g, 'user_role', 'none')
            return lt.get_aggregated_statistic_data(dataset_url=decrypted_dataset_path)


    # ### API for creating a  aggregated statistic data for all vessels over map ###
    ###########################################################
    @uc3_ns.route('/aggr_map', defaults={'export_format': 'div'})
    @uc3_ns.route('/aggr_map/export/<export_format>')
    class aggr_marker_map(Resource):
        @auth.require_token
        def get(self, export_format='div', token_status="valid"):
            token_status = getattr(g, 'token_status', 'none')

            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403
            
            user_role = getattr(g, 'user_role', 'none')
            print(user_role)
            if user_role == "data-owner":
                token_status = "valid"
                dataset_path = decrypted_dataset_path
            elif user_role == "pilot-user":
                token_status = "invalid"
                dataset_path = mini_encrypted_dataset_path
            else:
                return "Something went wrong with the authentication token"
            if export_format not in ALLOWED_FORMATS_MAP:
                return {"error": "Invalid format. Allowed values are: 'div', 'html'."}, 400
            # Get aggregated data and trajectory data
            aggr_data = lt.get_aggregated_data(dataset_url=dataset_path)
            traj_aggr_data = lt.get_aggregated_statistic_data(dataset_url=dataset_path)
        
            # Create map with markers and pop-ups
            html_map = lt.create_map_with_markers_and_popups(
                aggr_data=aggr_data,
                traj_aggr_data=traj_aggr_data,
                token_status = token_status
            )
            if export_format == 'html':
                return Response(
                    render_html_template(html_map),
                    mimetype="text/html",
                    headers={"Content-disposition": "attachment; filename=map.html"}
                )
            else:
                return html_map
             
    # ### API for creating trajectory for a specific vessel ###
    ###########################################################
    @uc3_ns.route('/trajectory_map/<shipid>', defaults={'export_format': 'div'})
    @uc3_ns.route('/trajectory_map/<shipid>/export/<export_format>')
    class trajectory_map_trip(Resource):
        @auth.require_token
        def get(self, shipid, export_format='div', token_status="valid"):
            token_status = getattr(g, 'token_status', 'none')

            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403
            
            user_role = getattr(g, 'user_role', 'none')
            if export_format not in ALLOWED_FORMATS_MAP:
                return {"error": "Invalid format. Allowed values are: 'div', 'html'."}, 400
            html_map = lt.create_vessel_trajectory(
                dataset_url=decrypted_dataset_path, 
                shipid=shipid 
            )
            if export_format == 'html':
                return Response(
                    render_html_template(html_map),
                    mimetype="text/html",
                    headers={"Content-disposition": "attachment; filename=map.html"}
                )
            else:
                return html_map  
        
    @uc3_ns.route('/data/<number_of_rows>/export/<export_format>')
    class get_Data_With_Export(Resource):
        @auth.require_token
        def get(self, number_of_rows, export_format="json", token_status="valid"):
            token_status = getattr(g, 'token_status', 'none')

            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403
            
            user_role = getattr(g, 'user_role', 'none')
            if export_format not in ALLOWED_FORMATS_DATA:
                return {"error": "Invalid format. Allowed values are: 'json', 'csv', 'xlsx'."}, 400    
            data = lt.read_csv_nrows(
                dataset_url=decrypted_dataset_path, 
                n=number_of_rows
            )
            response_data = data.to_dict(orient='records', doc=False)
            return data_to_export_format(response_data, export_format)

    @uc3_ns.route('/data/aggregated/export/<export_format>')
    class get_aggr_data_with_export(Resource):
        @auth.require_token
        def get(self, export_format="json", token_status="valid"):
            token_status = getattr(g, 'token_status', 'none')

            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403
            
            user_role = getattr(g, 'user_role', 'none')
            if export_format not in ALLOWED_FORMATS_DATA:
                return {"error": "Invalid format. Allowed values are: 'json', 'csv', 'xlsx'."}, 400    
            data = lt.get_aggregated_data(dataset_url=decrypted_dataset_path)
            return data_to_export_format(data, export_format)

    @uc3_ns.route('/data/aggregated/<shipid>/export/<export_format>')
    class get_aggr_vessel_data_with_export(Resource):
        @auth.require_token
        def get(self, shipid, export_format="json", token_status="valid"):
            token_status = getattr(g, 'token_status', 'none')

            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403
            
            user_role = getattr(g, 'user_role', 'none')
            if export_format not in ALLOWED_FORMATS_DATA:
                return {"error": "Invalid format. Allowed values are: 'json', 'csv', 'xlsx'."}, 400    
            data = lt.get_aggregated_vessel_data(dataset_url=decrypted_dataset_path, shipid=shipid)
            return data_to_export_format(data, export_format)
        
    @uc3_ns.route('/vessel/data/<shipid>')
    class get_ship_data(Resource):
        @auth.require_token
        def get(self, shipid, export_format="json", token_status="valid"):
            token_status = getattr(g, 'token_status', 'none')

            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403
            
            user_role = getattr(g, 'user_role', 'none')
            if export_format not in ALLOWED_FORMATS_DATA:
                return {"error": "Invalid format. Allowed values are: 'json', 'csv', 'xlsx'."}, 400  
            print("Hello!!!")  
            data = lt.get_all_vessel_data(dataset_url=decrypted_dataset_path, shipid=shipid)
            return data_to_export_format(data, export_format)
            #return True
        
    @uc3_ns.route('/statistic_data/aggregated/export/<export_format>')
    class get_traj_aggr_data_with_export(Resource):
        @auth.require_token
        def get(self, export_format="json", token_status="valid"):
            token_status = getattr(g, 'token_status', 'none')

            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403
            
            user_role = getattr(g, 'user_role', 'none')
            if export_format not in ALLOWED_FORMATS_DATA:
                return {"error": "Invalid format. Allowed values are: 'json', 'csv', 'xlsx'."}, 400        
            data = lt.get_aggregated_statistic_data(dataset_url=decrypted_dataset_path)
            return data_to_export_format(data, export_format)
    
    
    
    def load_rf_data():
        """Loads RF dataset and extracts necessary columns."""
        rf_data = pd.read_csv(rf_dataset_path_2025, usecols=['t', 'lon', 'lat'])
        return rf_data.to_dict(orient='records')

    @uc3_ns.route('/map/ais_rf')
    class ais_rf_map(Resource):
        @auth.require_token
        def get(self, token_status="valid"):
            token_status = getattr(g, 'token_status', 'none')

            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403  
            
            html_map = lt.create_map_with_ais_rf(
                ais_dataset_url=ais_dataset_path_2025,
                rf_data=load_rf_data(),
                zoom_start=12
            )
            
            return Response(
                html_map,
                mimetype="text/html",
                headers={"Content-disposition": "attachment; filename=ais_rf_map.html"}
            ) 
        
                       
    return uc3_ns
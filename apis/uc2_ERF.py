from flask import jsonify, request, Response, g
from flask_restx import Namespace, Resource
import base64
import requests
import io
import json
import static.authenticate as auth
import static.uc2_emissions as emmisions
import pandas as pd

def init_uc2_erfut():
    init_uc2_erfut = Namespace('UC2_ERF', description='UC2 related operations for the city of Erfut')

    ALLOWED_FORMATS_MAP = {'div', 'html'}
    ALLOWED_FORMATS_DATA = {'json', 'csv', 'xlsx'}

    def build_params(bbox, time_from, time_until, data_points):
        params = {}
        if bbox:
            params['bbox'] = bbox
        if time_from:
            params['since'] = time_from
        if time_until:
            params['until'] = time_until
        if data_points:
            params['limit'] = data_points
        
        return params

    def send_api_request(url, headers, params):
        response = requests.get(url, headers=headers, params=params)
        return response

    def calculate_iterations(data_points):
        return int(int(data_points) / 100 - 1)    
    
    def data_to_export_format(data, format):
        if format == "csv":
            df = pd.json_normalize(data)  # Flatten the JSON data
            df.columns = df.columns.str.replace('payload.', '')  # Remove 'payload.' prefix from column names
            return Response(
                df.to_csv(index=False),
                mimetype="text/csv",
                headers={"Content-disposition": "attachment; filename=data.csv"}
            )
        elif format == "xlsx":
            df = pd.json_normalize(data)  # Flatten the JSON data
            df.columns = df.columns.str.replace('payload.', '')  # Remove 'payload.' prefix from column names
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
    
    
    @init_uc2_erfut.route('/sensor_data/<sensor_id>')
    class get_uc2_sensor_data(Resource):
        @auth.require_token
        def get(self, sensor_id, token_status="valid"):
            user_role = getattr(g, 'user_role', 'none')
            token_status = getattr(g, 'token_status', 'none')

            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403
        
            url = "https://bosch-iot-insights.com/r/pyf4020/currentaqi/" + sensor_id
            username = "pyf4020-mobispaces-api"
            password = "Um-6VztCxpgjowyQ"

            # Encode username and password as base64
            auth = base64.b64encode((username + ":" + password).encode()).decode()

            headers = {
                "Authorization": "Basic " + auth,
                "Content-Type": "application/json"
            }

            response = requests.get(url, headers=headers)

            # Check if the response was successful and return JSON response
            if response.ok:
                json_data = response.json()
                return jsonify(json_data)
            else:
                response.raise_for_status()
                return jsonify(response)
            
    # @init_uc2_erfut.route('/Erfut/traffic', methods=['GET'], defaults={'export_format': 'div'})
    # @init_uc2_erfut.route('/Erfut/traffic/export/<export_format>', methods=['GET'])
    # class get_uc2_emmision_data(Resource):
    #     @auth.require_token
    #     def get(self, export_format='div', token_status="valid"):
    #         token_status = getattr(g, 'token_status', 'none')

    #         if token_status != "valid":
    #             return {"error": "Authentication Issue | Check User Credentials"}, 403
            
    #         if export_format not in ALLOWED_FORMATS_MAP:
    #             return {"error": "Invalid format. Allowed values are: 'div', 'html'."}, 400
    #         url = "https://api.bosch-air-quality-solutions.com/estm/emissions"
    #         headers = {
    #             "Content-Type": "application/json",
    #             "api-key": "280cc19b5fb04b839845002fee3233d7" 
    #         }

    #         bbox = request.args.get('bbox')  # Retrieve the value of the 'bbox' parameter from the request
    #         time_from = request.args.get('time_from')  # Retrieve the value of the 'time_from' parameter from the request
    #         time_until = request.args.get('time_until')  # Retrieve the value of the 'time_until' parameter from the request
    #         data_points = request.args.get('data_points')  # Retrieve the value of the 'data_points' parameter from the request

    #         if data_points is None:
    #             data_points = 100

    #         params = build_params(bbox, time_from, time_until, data_points)
    #         response = send_api_request(url, headers, params)

    #         if response.ok:
    #             emissions_data = []
    #             json_data = response.json()
    #             emissions_data.append(json_data)

    #             next_token = json_data.get("next")
    #             n = 1
    #             while n <= calculate_iterations(data_points):
    #                 if next_token:
    #                     params["next"] = next_token
    #                     response = send_api_request(url, headers, params)
    #                     if response.ok:
    #                         try:
    #                             results = response.json()
    #                             emissions_data.append(results)
    #                             next_token = results.get("next")
    #                             n += 1
    #                         except json.JSONDecodeError:
    #                             print("Invalid JSON response, continuing to next iteration...")
    #                             continue
    #                     else:
    #                         response.raise_for_status()
    #                         return jsonify(error=str(response))
    #                 else:
    #                     break
    #             map_html = emmisions.create_traffic_speed_map(emissions_data)
    #             if export_format == 'html':
    #                     return Response(
    #                         render_html_template(map_html),
    #                         mimetype="text/html",
    #                         headers={"Content-disposition": "attachment; filename=map.html"}
    #                     )
    #             else:
    #                 return map_html,200
    #         else:
    #             response.raise_for_status()
    #             return jsonify(error=str(response))

    @init_uc2_erfut.route('/Erfut/heat_map', methods=['GET'], defaults={'export_format': 'div'})
    @init_uc2_erfut.route('/Erfut/heat_map/export/<export_format>', methods=['GET'])
    class get_uc2_heat_map(Resource):   
        @auth.require_token
        def get(self,export_format='div', token_status="valid"):
            token_status = getattr(g, 'token_status', 'none')

            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403
                        
            if export_format not in ALLOWED_FORMATS_MAP:
                return {"error": "Invalid format. Allowed values are: 'div', 'html'."}, 400
            url = "https://api.bosch-air-quality-solutions.com/estm/emissions"
            headers = {
                "Content-Type": "application/json",
                "api-key": "280cc19b5fb04b839845002fee3233d7"  
            }

            bbox = request.args.get('bbox')  # Retrieve the value of the 'bbox' parameter from the request
            time_from = request.args.get('time_from')  # Retrieve the value of the 'time_from' parameter from the request
            time_until = request.args.get('time_until')  # Retrieve the value of the 'time_until' parameter from the request
            data_points = request.args.get('data_points')  # Retrieve the value of the 'data_points' parameter from the request

            if data_points is None:
                data_points = 100

            params = build_params(bbox, time_from, time_until, data_points)

            response = send_api_request(url, headers, params)

            if response.ok:
                emissions_data = []
                json_data = response.json()
                emissions_data.append(json_data)

                next_token = json_data.get("next")
                n = 1
                while n <= calculate_iterations(data_points):
                    if next_token:
                        params["next"] = next_token
                        response = send_api_request(url, headers, params)
                        if response.ok:
                            try:
                                results = response.json()
                                emissions_data.append(results)
                                next_token = results.get("next")
                                n += 1
                            except json.JSONDecodeError:
                                print("Invalid JSON response, continuing to next iteration...")
                                continue
                        else:
                            response.raise_for_status()
                            return jsonify(error=str(response))
                    else:
                        break
                map_html = emmisions.create_heatmap(emissions_data)
                if export_format == 'html':
                        return Response(
                            render_html_template(map_html),
                            mimetype="text/html",
                            headers={"Content-disposition": "attachment; filename=map.html"}
                        )
                else:
                    return map_html,200
            else:
                print(response.status_code)
                response.raise_for_status()
                return jsonify(error=str(response))
            
    @init_uc2_erfut.route('/sensor_data/<sensor_id>/export/<export_format>') 
    class get_uc2_sensor_data_with_export(Resource):
        @auth.require_token
        def get(self, sensor_id, export_format="json", token_status="valid"):
            token_status = getattr(g, 'token_status', 'none')

            if token_status != "valid":
                return {"error": "Authentication Issue | Check User Credentials"}, 403
                          
            if export_format not in ALLOWED_FORMATS_DATA:
                return {"error": "Invalid format. Allowed values are: 'json', 'csv', 'xlsx'."}, 400  
            url = "https://bosch-iot-insights.com/r/pyf4020/currentaqi/" + sensor_id
            username = "pyf4020-mobispaces-api"
            password = "Um-6VztCxpgjowyQ"

            auth_str = base64.b64encode((username + ":" + password).encode()).decode()

            headers = {
                "Authorization": "Basic " + auth_str,
                "Content-Type": "application/json"
            }

            response = requests.get(url, headers=headers)

            if response.ok:
                json_data = response.json()
                return data_to_export_format(json_data, export_format)
            else:
                response.raise_for_status()
                return jsonify(response)
    return init_uc2_erfut


from flask import jsonify, request
from flask_restx import Namespace, Resource
import base64
import requests
import json
import time
import static.authenticate as auth
import static.uc2_emissions as emmisions

def init_uc2():
    uc2_ns = Namespace('UC2', description='UC2 related operations')

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
    

    @uc2_ns.route('/sensor_data/<sensor_id>')
    class get_uc2_sensor_data(Resource):
        @auth.require_token
        def get(self, sensor_id):
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
            
    @uc2_ns.route('/traffic', methods=['GET'])
    class get_uc2_emmision_data(Resource):
        @auth.require_token
        def get(self):
            url = "https://api.bosch-air-quality-solutions.com/estm/emissions"
            headers = {
                "Content-Type": "application/json",
                "api-key": "280cc19b5fb04b839845002fee3233d7"  # Replace this with your actual API key
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
                map_html = emmisions.create_traffic_speed_map(emissions_data)
                return map_html, 200
            else:
                response.raise_for_status()
                return jsonify(error=str(response))


        
    @uc2_ns.route('/heat_map', methods=['GET'])
    class get_uc2_heat_map(Resource):   
        @auth.require_token 
        def get(self):
            url = "https://api.bosch-air-quality-solutions.com/estm/emissions"
            headers = {
                "Content-Type": "application/json",
                "api-key": "280cc19b5fb04b839845002fee3233d7"  # Replace this with your actual API key
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
                return map_html, 200
            else:
                response.raise_for_status()
                return jsonify(error=str(response))

    return uc2_ns


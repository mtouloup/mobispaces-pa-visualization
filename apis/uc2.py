from flask_restx import Namespace, Resource
import base64
import requests
import static.authenticate as auth
from flask import jsonify

def init_uc2():
    uc2_ns = Namespace('UC2', description='UC2 related operations')

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
    return uc2_ns
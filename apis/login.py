from flask_restx import Namespace, Resource
import base64
import requests
import static.authenticate as auth
from flask import jsonify

def init_login():
    login_ns = Namespace('login', description='Log In related operations')

    @login_ns.route('/<user_name>/<password>')
    class login(Resource):
        def get(self, user_name, password):
            url = 'https://mobispaces-keycloak.euprojects.net/auth/realms/Mobispaces/protocol/openid-connect/token'
            data = {
                'client_id': 'trino-coordinator',
                'client_secret': 'xnO71hz52xD60aJ02TAaJ2K4ATpk2DWv',
                'username': user_name,
                'password': password,
                'grant_type': 'password'
            }
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            response = requests.post(url, data=data, headers=headers)
            if response.ok:
                response_data = response.json()
                access_token = response_data.get('access_token')
                return access_token
            else:
                print('Error:', response.status_code)
                return None
    return login_ns
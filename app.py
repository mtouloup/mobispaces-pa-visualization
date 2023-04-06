from flask import Flask, Blueprint, jsonify
from flask_cors import CORS
from flask_oidc import OpenIDConnect
from flask_restx import Api, Resource

import static.load_trajectories as lt

app = Flask(__name__)
app.config.update({
    'SECRET_KEY': 'EpsqJxbG4wg6M4OP4zzh67SEDIlZ3qrm',
    'TESTING': True,
    'DEBUG': True,
    'OIDC_CLIENT_SECRETS': '/usr/src/app/app/auth.json',
    'OIDC_ID_TOKEN_COOKIE_SECURE': True,
    'OIDC_REQUIRE_VERIFIED_EMAIL': False,
    'OIDC_USER_INFO_ENABLED': True,
    'OIDC_OPENID_REALM': 'myrealm',
    'OIDC_SCOPES': ['openid', 'email', 'profile'],
    'OIDC_INTROSPECTION_AUTH_METHOD': 'client_secret',
    'OIDC_COOKIE_SECURE': False
})

oidc = OpenIDConnect(app)
CORS(app)

# Create the blueprint for your API
api_blueprint = Blueprint('api', __name__)
api = Api(api_blueprint, version="0.1",
          title='MobiSpaces Privacy Aware Visualization',
          description="")

@api.route('/authentication/test')
class test_auth(Resource):
    @oidc.require_login
    def get(self):
        return 'Authentication from Ubitech Works!'
    
@api.route('/UC3/trip_map/<zoom>/<markers>')
class map_trip(Resource):
    @oidc.require_login
    def get(self, zoom, markers):
        html_map = lt.create_map_with_trip(dataset_url="https://dl.dropboxusercontent.com/s/8iqq3seeav02c0f/ais.csv", zoom_start=zoom, marker_limit=markers)
        return html_map
    
@api.route('/UC3/map/<zoom>/<markers>')
class marker_map(Resource):
    @oidc.require_login
    def get(self, zoom, markers):
        html_map = lt.create_map_with_markers(dataset_url="https://dl.dropboxusercontent.com/s/8iqq3seeav02c0f/ais.csv", zoom_start=zoom, marker_limit=markers)
        return html_map

@api.route('/UC3/data/<number_of_rows>')
class get_Data(Resource):
    @oidc.require_login
    def get(self, number_of_rows):
        data = lt.read_csv_nrows(dataset_url="https://dl.dropboxusercontent.com/s/8iqq3seeav02c0f/ais.csv", n=number_of_rows)
        response = data.to_json(orient='records')
        return jsonify(response)
       
"""

@api.route('/UC4')
class movpandasex1(Resource):
    @oidc.require_login
    def get(self):
        html_map = lt.create_map_with_markers('figures/')
        return html_map

@api.route('/register/<email>/<password>')
class register(Resource):
    @oidc.require_login
    def post(self, email=None, password=None):
        db_methods.register_user(email=email, password=password)
        response = {'status': 'success'}
        return Response(
            json.dumps(response),
            mimetype='application/json',
            status=200
            )


@api.route('/login/<email>/<password>')
class login(Resource):
    @oidc.require_login
    def get(self, email=None, password=None):
        
        if (db_methods.get_user(email=email, password=password) == 1):
            response = {'status': 'success'}
        else:
            response = {'status': 'fail'}
            
        return Response(
            json.dumps(response),
            mimetype='application/json',
            status=200
        )
"""
# Register the blueprints with your app
app.register_blueprint(api_blueprint)

# Configure Swagger UI
api_doc_blueprint = Blueprint('api_doc', __name__)
api_doc = Api(api_doc_blueprint, doc='/docs')
api_doc.add_namespace(api)
app.register_blueprint(api_doc_blueprint, url_prefix='/doc')

# main driver function
if __name__ == '__main__': 
    # run() method of Flask class runs the application
    # on the local development server.
    app.run(host='0.0.0.0', debug=True, port=80)
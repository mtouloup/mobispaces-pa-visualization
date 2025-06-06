from flask import Flask, Blueprint
from flask_cors import CORS
from flask_restx import Api, apidoc
from apis.uc2_ERF import init_uc2_erfut
from apis.uc2_SKG import init_uc2_skg
from apis.uc3 import init_uc3
from apis.login import init_login
from apis.uc1 import init_uc1
from flask import send_file
from static.ship_predictions import generate_prediction_map
import os

apidoc.apidoc.url_prefix = '/pava'
app = Flask(__name__, static_folder='static', static_url_path='/pava/static')

CORS(app)

@app.route('/pava')
def serve_swagger_ui():
    return app.send_static_file('swaggerui/index.html')


@app.route('/pava/ship_prediction_map', methods=['GET'])
def ship_prediction_map():
    # Point to the location of your dataset
    data_dir = os.path.abspath(os.path.join(os.getcwd(), '.', 'data'))
    csv_path = os.path.join(data_dir, 'FLP_test_result.zip')
    map_path = generate_prediction_map(csv_path)
    return send_file(map_path, mimetype='text/html')

# Create the blueprint for your API without the prefix
api_blueprint = Blueprint('api', __name__)
api = Api(api_blueprint, version="0.1",
          title='MobiSpaces Privacy Aware Visualization',
          description="")

# Register the blueprint with your app using the url_prefix
app.register_blueprint(api_blueprint, url_prefix='/pava')

# Configure Swagger UI
api_doc_blueprint = Blueprint('api_doc', __name__, url_prefix='/pava/doc')
api_doc = Api(api_doc_blueprint, doc='/docs')
api_doc.add_namespace(api)
app.register_blueprint(api_doc_blueprint)

# Initialize and register the UC2, UC3, and login namespaces
uc2_ns_erfut = init_uc2_erfut()
uc2_ns_skg = init_uc2_skg()
login_ns = init_login()
uc3_ns = init_uc3()
uc1_ns = init_uc1()

api.add_namespace(uc2_ns_erfut)
api.add_namespace(uc3_ns)
api.add_namespace(login_ns)
api.add_namespace(uc2_ns_skg)
api.add_namespace(uc1_ns)
# Main driver function
if __name__ == '__main__':
    # Run() method of Flask class runs the application on the local development server.
    app.run(host='0.0.0.0', debug=True, port=80)
import os
from flask import Flask, Blueprint
from flask_cors import CORS
from flask_restx import Api
from apis.uc2 import init_uc2
from apis.uc3 import init_uc3

app = Flask(__name__)
CORS(app)

# Create the blueprint for your API
api_blueprint = Blueprint('api', __name__)
api = Api(api_blueprint, version="0.1",
          title='MobiSpaces Privacy Aware Visualization',
          description="")

# Register the blueprints with your app
app.register_blueprint(api_blueprint)

# Configure Swagger UI
api_doc_blueprint = Blueprint('api_doc', __name__)
api_doc = Api(api_doc_blueprint, doc='/docs')
api_doc.add_namespace(api)
app.register_blueprint(api_doc_blueprint, url_prefix='/doc')

# Initialize and register the UC2 and UC3 namespaces
uc2_ns = init_uc2()
uc3_ns = init_uc3()
api.add_namespace(uc2_ns)
api.add_namespace(uc3_ns)

# Main driver function
if __name__ == '__main__':
    # Run() method of Flask class runs the application
    # on the local development server.
    app.run(host='0.0.0.0', debug=True, port=80)
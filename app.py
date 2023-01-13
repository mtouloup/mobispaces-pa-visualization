# Importing flask module in the project is mandatory
from flask import Blueprint,Flask
from flask_restplus import Api, Resource

import static.moving_pandas_examples as mve

# Flask constructor takes the name of
# current module (__name__) as argument.
app = Flask(__name__)

blueprint = Blueprint('api', __name__)
api = Api(blueprint, version="0.1",
          title='MobiSpaces Privacy Aware Visualization',
          description="XXX")

app.register_blueprint(blueprint)
 
@api.route('/home/', methods=["GET"])
class home(Resource):
    def get(self):
        return 'Hello World'

@api.route('/mov-pandas/ex1', methods=["GET"])
class movpandasex1(Resource):
    def get(self):
        return mve.load_trajectory()



# main driver function
if __name__ == '__main__': 
    # run() method of Flask class runs the application
    # on the local development server.
    app.run(host='0.0.0.0', debug=True, port=80)
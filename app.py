from flask import Blueprint,Flask,Response
from flask_restplus import Api, Resource
import json


import static.moving_pandas_examples as mve
import database.db_methods as db_methods

app = Flask(__name__)

blueprint = Blueprint('api', __name__)
api = Api(blueprint, version="0.1",
          title='MobiSpaces Privacy Aware Visualization',
          description="")

app.register_blueprint(blueprint)
 
@api.route('/home/', methods=["GET"])
class home(Resource):
    def get(self):
        return 'Hello World'

@api.route('/mov-pandas/ex1', methods=["GET"])
class movpandasex1(Resource):
    def get(self):
        return mve.load_trajectory()

@api.route('/register/<email>/<password>', methods=["POST"])
class register(Resource):
    def post(self, email=None, password=None):
        db_methods.register_user(email=email, password=password)
        response = {'status': 'success'}
        return Response(
            json.dumps(response),
            mimetype='application/json',
            status=200
            )


@api.route('/login/<email>/<password>', methods=["GET"])
class login(Resource):
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


# main driver function
if __name__ == '__main__': 
    # run() method of Flask class runs the application
    # on the local development server.
    app.run(host='0.0.0.0', debug=True, port=80)
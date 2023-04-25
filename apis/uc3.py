from flask_restx import Namespace, Resource
from flask_oidc import OpenIDConnect
import static.load_trajectories as lt
from flask import jsonify

def init_uc3(oidc: OpenIDConnect):
    uc3_ns = Namespace('UC3', description='UC3 related operations')

    @uc3_ns.route('/trip_map/<zoom>/<markers>')
    class map_trip(Resource):
        @oidc.require_login
        def get(self, zoom, markers):
            html_map = lt.create_map_with_trip(
                dataset_url="https://dl.dropboxusercontent.com/s/8iqq3seeav02c0f/ais.csv", 
                zoom_start=zoom, 
                marker_limit=markers
            )
            return html_map

    @uc3_ns.route('/map/<zoom>/<markers>')
    class marker_map(Resource):
        @oidc.require_login
        def get(self, zoom, markers):
            html_map = lt.create_map_with_markers(
                dataset_url="https://dl.dropboxusercontent.com/s/8iqq3seeav02c0f/ais.csv", 
                zoom_start=zoom, 
                marker_limit=markers
            )
            return html_map

    @uc3_ns.route('/data/<number_of_rows>')
    class get_Data(Resource):
        @oidc.require_login
        def get(self, number_of_rows):
            data = lt.read_csv_nrows(
                dataset_url="https://dl.dropboxusercontent.com/s/8iqq3seeav02c0f/ais.csv", 
                n=number_of_rows
            )
            response = data.to_json(orient='records')
            return jsonify(response)

    @uc3_ns.route('/data/aggregated')
    class get_aggr_data(Resource):
        @oidc.require_login
        def get(self):
            return lt.get_aggregated_data(dataset_url="https://dl.dropboxusercontent.com/s/8iqq3seeav02c0f/ais.csv")

    @uc3_ns.route('/trajectory_data/aggregated')
    class get_traj_aggr_data(Resource):
        @oidc.require_login
        def get(self):
            return lt.get_aggregated_trajectory_data(dataset_url="https://dl.dropboxusercontent.com/s/8iqq3seeav02c0f/ais.csv")

    return uc3_ns
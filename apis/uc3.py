from flask_restx import Namespace, Resource
import static.load_trajectories as lt
import static.authenticate as auth
from flask import jsonify

def init_uc3():
    uc3_ns = Namespace('UC3', description='UC3 related operations')

    @uc3_ns.route('/trip_map/<zoom>/<markers>')
    class map_trip(Resource):
        @auth.require_token
        def get(self, zoom, markers):
            html_map = lt.create_map_with_trip(
                dataset_url="https://dl.dropboxusercontent.com/s/8iqq3seeav02c0f/ais.csv", 
                zoom_start=zoom, 
                marker_limit=markers
            )
            return html_map

    @uc3_ns.route('/map/<zoom>/<markers>')
    class marker_map(Resource):
        @auth.require_token
        def get(self, zoom, markers):
            html_map = lt.create_map_with_markers(
                dataset_url="https://dl.dropboxusercontent.com/s/8iqq3seeav02c0f/ais.csv", 
                zoom_start=zoom, 
                marker_limit=markers
            )
            return html_map

    @uc3_ns.route('/data/<number_of_rows>')
    class get_Data(Resource):
        @auth.require_token
        def get(self, number_of_rows):
            data = lt.read_csv_nrows(
                dataset_url="https://dl.dropboxusercontent.com/s/8iqq3seeav02c0f/ais.csv", 
                n=number_of_rows
            )
            response = data.to_json(orient='records')
            return jsonify(response)


    # ### API for getting aggregated data for all vessels ###
    ###########################################################
    @uc3_ns.route('/data/aggregated')
    class get_aggr_data(Resource):
        @auth.require_token
        def get(self):
            return lt.get_aggregated_data(dataset_url="https://dl.dropboxusercontent.com/s/8iqq3seeav02c0f/ais.csv")
        
    # ### API for getting aggregated data for specific vessels based on shipid ###
    ##############################################################################
    @uc3_ns.route('/data/aggregated/<shipid>')
    class get_aggr_vessel_data(Resource):
        @auth.require_token
        def get(self, shipid):
            return lt.get_aggregated_vessel_data(dataset_url="https://dl.dropboxusercontent.com/s/8iqq3seeav02c0f/ais.csv", shipid=shipid)

    # ### API for getting aggregated statistic data for all vessels ###
    ###########################################################
    @uc3_ns.route('/statistic_data/aggregated')
    class get_traj_aggr_data(Resource):
        @auth.require_token
        def get(self):
            return lt.get_aggregated_statistic_data(dataset_url="https://dl.dropboxusercontent.com/s/8iqq3seeav02c0f/ais.csv")


    # ### API for creating a  aggregated statistic data for all vessels ###
    ###########################################################
    @uc3_ns.route('/aggr_map')
    class aggr_marker_map(Resource):
        @auth.require_token
        def get(self):
            # Get aggregated data and trajectory data
            aggr_data = lt.get_aggregated_data(dataset_url="https://dl.dropboxusercontent.com/s/8iqq3seeav02c0f/ais.csv")
            traj_aggr_data = lt.get_aggregated_statistic_data(dataset_url="https://dl.dropboxusercontent.com/s/8iqq3seeav02c0f/ais.csv")
        
            # Create map with markers and pop-ups
            html_map = lt.create_map_with_markers_and_popups(
                aggr_data=aggr_data,
                traj_aggr_data=traj_aggr_data,
            )
            return html_map
             
    # ### API for creating trajectory for a specific vessel ###
    ###########################################################
    @uc3_ns.route('/trajectory_map/<shipid>')
    class map_trip(Resource):
        @auth.require_token
        def get(self, shipid):
            html_map = lt.create_vessel_trajectory(
                dataset_url="https://dl.dropboxusercontent.com/s/8iqq3seeav02c0f/ais.csv", 
                shipid=shipid 
            )
            return html_map  
    return uc3_ns
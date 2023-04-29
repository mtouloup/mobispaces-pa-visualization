from flask_restx import Namespace, Resource
import static.load_trajectories as lt
import static.authenticate as auth
from flask import jsonify
import os

def init_uc3():
    uc3_ns = Namespace('UC3', description='UC3 related operations')
    # Define the local file path to the dataset
    data_dir = os.path.abspath(os.path.join(os.getcwd(), '.', 'data'))
    dataset_path = os.path.join(data_dir, 'ais.csv')
    print(dataset_path)

    @uc3_ns.route('/trip_map/<zoom>/<markers>')
    class map_trip(Resource):
        @auth.require_token
        def get(self, zoom, markers):
            html_map = lt.create_map_with_trip(
                dataset_url=dataset_path, 
                zoom_start=zoom, 
                marker_limit=markers
            )
            return html_map

    @uc3_ns.route('/map/<zoom>/<markers>')
    class marker_map(Resource):
        @auth.require_token
        def get(self, zoom, markers):
            html_map = lt.create_map_with_markers(
                dataset_url=dataset_path, 
                zoom_start=zoom, 
                marker_limit=markers
            )
            return html_map

    @uc3_ns.route('/data/<number_of_rows>')
    class get_Data(Resource):
        @auth.require_token
        def get(self, number_of_rows):
            data = lt.read_csv_nrows(
                dataset_url=dataset_path, 
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
            return lt.get_aggregated_data(dataset_url=dataset_path)
        
    # ### API for getting aggregated data for specific vessels based on shipid ###
    ##############################################################################
    @uc3_ns.route('/data/aggregated/<shipid>')
    class get_aggr_vessel_data(Resource):
        @auth.require_token
        def get(self, shipid):
            return lt.get_aggregated_vessel_data(dataset_url=dataset_path, shipid=shipid)

    # ### API for getting aggregated statistic data for all vessels ###
    ###########################################################
    @uc3_ns.route('/statistic_data/aggregated')
    class get_traj_aggr_data(Resource):
        @auth.require_token
        def get(self):
            return lt.get_aggregated_statistic_data(dataset_url=dataset_path)


    # ### API for creating a  aggregated statistic data for all vessels ###
    ###########################################################
    @uc3_ns.route('/aggr_map')
    class aggr_marker_map(Resource):
        @auth.require_token
        def get(self):
            # Get aggregated data and trajectory data
            aggr_data = lt.get_aggregated_data(dataset_url=dataset_path)
            traj_aggr_data = lt.get_aggregated_statistic_data(dataset_url=dataset_path)
        
            # Create map with markers and pop-ups
            html_map = lt.create_map_with_markers_and_popups(
                aggr_data=aggr_data,
                traj_aggr_data=traj_aggr_data,
            )
            return html_map
             
    # ### API for creating trajectory for a specific vessel ###
    ###########################################################
    @uc3_ns.route('/trajectory_map/<shipid>')
    class trajectory_map_trip(Resource):
        @auth.require_token
        def get(self, shipid):
            html_map = lt.create_vessel_trajectory(
                dataset_url=dataset_path, 
                shipid=shipid 
            )
            return html_map  
           
    return uc3_ns
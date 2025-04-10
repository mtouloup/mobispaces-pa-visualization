# ship_predictions.py

import pandas as pd
import folium

def generate_prediction_map(csv_path):
    use_cols = [
        'timestamp', 'oid', 'lat', 'lon', 'lh',
        'predicted_lat', 'predicted_lon'
    ]
    df = pd.read_csv(csv_path, usecols=use_cols, parse_dates=['timestamp'])
    df = df.drop_duplicates(subset=['timestamp', 'oid', 'lat', 'lon', 'lh'])

    agg_result = (
        df.groupby(['timestamp', 'oid'])
        .agg(
            lat=('lat', 'first'),
            lon=('lon', 'first'),
            predictions=('lh', list),
            pred_lats=('predicted_lat', list),
            pred_lons=('predicted_lon', list)
        )
        .reset_index()
    )

    # Pick first timestamp to visualize
    timestamp_to_plot = agg_result['timestamp'].iloc[0]
    subset = agg_result[agg_result['timestamp'] == timestamp_to_plot]

    map_center = [subset['lat'].mean(), subset['lon'].mean()]
    m = folium.Map(location=map_center, zoom_start=12)

    for _, row in subset.iterrows():
        actual_pos = (row['lat'], row['lon'])
        predicted_positions = list(zip(row['pred_lats'], row['pred_lons'], row['predictions']))

        # Actual position marker
        folium.Marker(
            location=actual_pos,
            popup=folium.Popup(
                f"""
                <b>Ship ID:</b> {row['oid']}<br>
                <b>Timestamp:</b> {row['timestamp']}<br>
                <b>This is the actual position of the ship at this time.</b>
                """, max_width=300
            ),
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)

        # Predicted points
        for pred_lat, pred_lon, lh_val in predicted_positions:
            folium.CircleMarker(
                location=(pred_lat, pred_lon),
                radius=3,
                color='red',
                fill=True,
                fill_opacity=0.8,
                popup=folium.Popup(
                    f"""
                    <b>Prediction Horizon:</b> {lh_val} seconds<br>
                    <b>This is the predicted position of the ship {lh_val // 60} minutes after the actual timestamp.</b>
                    """, max_width=300
                )
            ).add_to(m)

        folium.PolyLine(
            locations=[actual_pos] + [(lat, lon) for lat, lon, _ in predicted_positions],
            color='blue', weight=2
        ).add_to(m)

    map_file_path = 'static/ship_predictions_map.html'
    m.save(map_file_path)
    return map_file_path

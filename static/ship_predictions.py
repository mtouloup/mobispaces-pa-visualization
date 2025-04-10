import pandas as pd
import folium

def generate_prediction_map(csv_path):
    use_cols = [
        'timestamp', 'oid', 'lat', 'lon', 'lh',
        'predicted_lat', 'predicted_lon', 'bearing'
    ]
    df = pd.read_csv(csv_path, usecols=use_cols, parse_dates=['timestamp'])
    df = df.drop_duplicates(subset=['timestamp', 'oid', 'lat', 'lon', 'lh'])

    # Group by timestamp and ship
    agg_result = (
        df.groupby(['timestamp', 'oid'])
        .agg(
            lat=('lat', 'first'),
            lon=('lon', 'first'),
            bearing=('bearing', 'first'),
            predictions=('lh', list),
            pred_lats=('predicted_lat', list),
            pred_lons=('predicted_lon', list)
        )
        .reset_index()
    )

    # Select first timestamp with more than one ship
    timestamp_counts = agg_result['timestamp'].value_counts()
    timestamp_to_plot = timestamp_counts[timestamp_counts > 1].index[0]
    subset = agg_result[agg_result['timestamp'] == timestamp_to_plot]

    # Initialize folium map
    map_center = [subset['lat'].mean(), subset['lon'].mean()]
    m = folium.Map(location=map_center, zoom_start=7)

    for _, row in subset.iterrows():
        actual_pos = (row['lat'], row['lon'])
        predicted_positions = list(zip(row['pred_lats'], row['pred_lons'], row['predictions']))
        bearing = row['bearing'] if not pd.isna(row['bearing']) else 0

        # Add rotated triangle to indicate actual position + direction
        folium.RegularPolygonMarker(
            location=actual_pos,
            number_of_sides=3,
            radius=10,
            rotation=bearing,
            color='blue',
            fill_color='blue',
            fill_opacity=0.9,
            popup=folium.Popup(
                f"""
                <b>Ship ID:</b> {row['oid']}<br>
                <b>Timestamp:</b> {row['timestamp']}<br>
                <b>Bearing:</b> {int(bearing)}°<br>
                <b>This is the actual position of the ship at this time.</b>
                """,
                max_width=300
            )
        ).add_to(m)

        # Add predicted positions (red dots)
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
                    """,
                    max_width=300
                )
            ).add_to(m)

        # Connect actual point to predictions
        path_coords = [actual_pos] + [(lat, lon) for lat, lon, _ in predicted_positions]
        folium.PolyLine(locations=path_coords, color='blue', weight=2).add_to(m)

    # Save and return path
    map_file_path = 'static/ship_predictions_map.html'
    m.save(map_file_path)
    return map_file_path

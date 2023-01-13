import pandas as pd
from geopandas import gpd
import movingpandas as mpd
import matplotlib.pyplot as plt

def load_trajectory():
    gdf = gpd.read_file('./data/geolife_small.gpkg')
    gdf.plot(figsize=(9,5))

    plt.savefig('figures/gdf.jpg')
        
    return("Figure Saved!")



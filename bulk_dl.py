import fiona
import collections
import matplotlib.pyplot as plt
import pyproj
import rasterio
import rasterio.mask
from rasterio.plot import show
from rasterio import features
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
from datetime import date, timedelta
import geopandas
import os
from shapely import geometry
import numpy as np
import utilities
import pandas as pd
import shutil
import glob
pd.set_option('display.max_columns', None)
import time

# 18-21 Jul 2019
start_date = date(2017, 8, 15)
end_date = date(2017, 8, 20)

path = "/home/primity/terras/bulk/"
dest = "/home/primity/terras/bulk_crops/"

freguesias_shapes=fiona.open("gadm36_PRT_shp/gadm36_PRT_3.shp")
concelhos_shapes = fiona.open("gadm36_PRT_shp/gadm36_PRT_2.shp")


for shp in freguesias_shapes:
    #print(shp['properties']['NAME_3'])
    if shp['properties']['NAME_3']=='Cardigos' :
        cardigos_shp = shp

for shp in concelhos_shapes:
    if shp['properties']['NAME_2'] =='Mação':
        macao_shp = shp


os.makedirs(dest, exist_ok=True)
footprint = geojson_to_wkt(read_geojson('quadrado-macao.geojson'))
for current_date in utilities.daterange(start_date, end_date -  timedelta(1)):
    time.sleep(5)
    print(current_date)
    os.makedirs(path, exist_ok=True)
    #get products list from this day
    api = SentinelAPI('fernandeslouro', 'copernicospw', 'https://scihub.copernicus.eu/dhus')
    products = api.query(footprint,
                         date=(current_date, current_date + timedelta(1)),
                         platformname='Sentinel-2',
                         cloudcoverpercentage=(0, 30))
    products_df = api.to_dataframe(products)
    
    if products:
        print(f"{current_date} - {len(products)} available products")
        # download them all
        for p in list(products_df.index):
            time.sleep(10)
            utilities.download_no_fail(p, 'fernandeslouro', 'copernicospw', 'https://scihub.copernicus.eu/dhus')
            print(p)
        # unzip them all
        for f in os.listdir(path):
            bashCmd = f"!unzip {os.path.join(path, f)}"
            process = subprocess.Popen(bashCmd, stdout=subprocess.PIPE)
            output, error = process.communicate()
        # copy jp2 to dest
        utilities.subfolders_copy(path, dest)
        
        # save cropped jp2 with same name 
        for i in os.listdir(dest):
            with rasterio.open(os.path.join(image_dir, i)) as src:
                out_macao, out_transform = rasterio.mask.mask(src, utilities.transform_shapefile(macao_shp), crop=True, nodata=10, all_touched=True)
                out_cardigos, out_transform = rasterio.mask.mask(src, utilities.transform_shapefile(cardigos_shp), crop=True, nodata=10, all_touched=True)
                out_meta = src.meta.copy()
                
            with rasterio.open(os.path.join(image_dir, f"mac_{i}"), 'w', **profile) as dst:
                dst.write(out_macao.astype(rasterio.uint8), 1)           
                
            with rasterio.open(os.path.join(image_dir, f"card_{i}"), 'w', **profile) as dst:
                dst.write(out_cardigos.astype(rasterio.uint8), 1)
                
        
        shutil.rmtree(path) 
    

import pyproj
from shapely import geometry
import datetime
import glob
import os
import geopandas as gpd
import numpy as np
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
import shutil
import zipfile


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)
    
def transform_shapefile(shp):
    transformer = pyproj.Transformer.from_crs("epsg:4326", "epsg:32629")
    p1 = pyproj.Proj('epsg:4326', preserve_units=False)
    p2 = pyproj.Proj('epsg:32629', preserve_units=False)
    shp_t={
        'type':shp['type'],
        'id':shp['id'],
        'properties':shp['properties'],
        'geometry':{'type':shp['geometry']['type'],
                    'coordinates':[pt for pt in pyproj.itransform(p1,p2,shp['geometry']['coordinates'][0], always_xy=True)]}
        #'geometry':{'type':macao_shp['geometry']['type'], 'coordinates':[[transformer.transform(point[0], point[1]) for point in macao_shp['geometry']['coordinates'][0]]]}
    }
    to_mask_input = [geometry.Polygon([[p[0], p[1]] for p in shp_t['geometry']['coordinates']])]
    return to_mask_input

def download_most_recent_product(products_dataframe, polygon_to_overlap, path, username='fernandeslouro', pw='copernicospw', server='https://scihub.copernicus.eu/dhus', unzip=True):
    products_dataframe['footprint'] = gpd.GeoSeries.from_wkt(products_dataframe['footprint'])
    products_dataframe = gpd.GeoDataFrame(products_dataframe, geometry='footprint')
    products_dataframe['intersection_area'] = products_dataframe.apply(lambda row: 
                                                         polygon_to_overlap.intersection(row.footprint).area/polygon_to_overlap.area, axis=1)
    print(f"{len(products_dataframe)} available products")
    # download them all
    to_download = products_dataframe[products_dataframe.intersection_area == max(products_dataframe.intersection_area)]
    to_download = to_download.sort_values('generationdate', ascending=False)
    to_download = single_row_dataframe_to_dict(to_download)
    download_no_fail(to_download['uuid'], path, username, pw, server)
    if unzip:
        with zipfile.ZipFile(os.path.join(path, to_download['title']+'.zip'), 'r') as zip_ref:
            zip_ref.extractall(path)
        os.remove(os.path.join(path, to_download['title']+'.zip'))
    return to_download


def download_no_fail(product, path, username, password, server):
    api = SentinelAPI(username, password, server)
    print(f'Trying to download {product}')
    try:
        output = api.download(product, directory_path=path)
    except:
        download_no_fail(product)
    return output

def subfolders_copy(src, dest):
    for file_path in glob.glob(os.path.join(src, '**', '*.jp2'), recursive=True):
        if 'TCI_10m' in file_path:
            new_path = os.path.join(dest, os.path.basename(file_path))
            shutil.copy(file_path, new_path)
        
def outer_square_points(list_of_tuples):
    lat, long = [point[0] for point in list_of_tuples], [point[1] for point in list_of_tuples]
    points_list = [(min(lat), min(long)),
                    (min(lat), max(long)),
                    (max(lat), max(long)),
                    (max(lat), min(long))]
    return geometry.Polygon(points_list)

def polygon_outer_square(poly):
    points_list = [(poly.bounds[0], poly.bounds[3]),
              (poly.bounds[0], poly.bounds[1]),
              (poly.bounds[2], poly.bounds[1]),
              (poly.bounds[2], poly.bounds[3])]
    return geometry.Polygon(points_list)

def append_transparency_band(rgb_array):
    mask = np.full((rgb_array.shape[1], rgb_array.shape[2]), True, dtype=bool)
    for band in range(rgb_array.shape[0]):
        mask *= rgb_array[band]==0
    mask = 255 * mask
    mask = mask.reshape((1, mask.shape[0], mask.shape[1]))
    mask = 255-mask
    return np.append(rgb_array, mask, axis=0)

def single_row_dataframe_to_dict(sr_df): 
    return list(sr_df.to_dict('index').values())[0]

def listdir_nohidden(path):
    return glob.glob(os.path.join(path, '*'))
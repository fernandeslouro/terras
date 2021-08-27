import os
import argparse
import shutil
import numpy as np
import geopandas as gpd
import rasterio
import rasterio.mask
from sentinelsat import SentinelAPI
from datetime import date, timedelta
import utilities

#!python download_latest --intermediate_folder path --dest dest --cutoff_name Mação --county True --days_back 7 --username fernandeslouro --password copernicospw --server https://scihub.copernicus.eu/dhus

parser=argparse.ArgumentParser()
parser.add_argument('--intermediate_folder', action='store', type=str, help='Intermediate folder to be created')
parser.add_argument('--dest', action='store', type=str, help='Destination path to drop the cripped images')
parser.add_argument('--cutoff_name', action='store', type=str, help='Name of the parish or county to be cut off, e.g. "Mação", "Cardigos"')
parser.add_argument('--county', action='store', type=str, help='Boolean value representing whether cutoff_name is a county. If not "True", it is assumed that cutoff_name is the name of a parish')
parser.add_argument('--days_back', action='store', help='Number of days to check back on')
parser.add_argument('--username', action='store', type=str, help='Sentinel username')
parser.add_argument('--password', action='store', type=str, help='Sentinel Password')
parser.add_argument('--server', action='store', type=str, help='Sentinel server, e.g. https://scihub.copernicus.eu/dhus')
parser.add_argument('--delete_intermediate_files', action='store_true', help='Run with this option to delete intermediate files (all data downloaded from Copernicus)')
args=parser.parse_args()

cutoff_shp, cutoff_shp_ptcrs, outer_square = utilities.get_zone_info(args.cutoff_name, county=args.county)

intermediate_existed = os.path.isdir(args.intermediate_folder)
os.makedirs(args.intermediate_folder, exist_ok=True)
os.makedirs(args.dest, exist_ok=True)

#get products list from this day
api = SentinelAPI(args.username, args.password, args.server)
products = api.query(outer_square,
                     date=(date.today() - timedelta(int(args.days_back)), date.today()),
                     platformname='Sentinel-2',
                     cloudcoverpercentage=(0, 30))
products_df = api.to_dataframe(products)

if products_df.empty:
    print('No images found')
else:    
    downloaded_product = utilities.download_most_recent_product(products_df, polygon_to_overlap=cutoff_shp, download_path=args.intermediate_folder)
    
# copy jp2 to args.dest
utilities.subfolders_copy(os.path.join(args.intermediate_folder, downloaded_product['title'] + '.SAFE'), args.dest)

# save cropped jp2 with same name 
for i in [img for img in utilities.listdir_nohidden(args.dest) if img.endswith('.jp2')]:
    for namepart in i.split('/')[-1].split('_'):
        if namepart.startswith('202'):
            imgname = f'{namepart[:4]}-{namepart[4:6]}-{namepart[6:8]}_{namepart[9:11]}:{namepart[11:13]}'
            break
    #with rasterio.open(os.path.join(args.dest, i)) as src:
    print(args.dest, i)
    with rasterio.open(i) as src:
        out_image, out_transform = rasterio.mask.mask(src, [cutoff_shp_ptcrs], crop=True, nodata=0, all_touched=True)
        out_meta = src.meta.copy() 
    
    out_image = utilities.append_transparency_band(out_image)
            
    with rasterio.open(os.path.join(args.dest, imgname)+'.png','w',
                       driver='PNG',
                       height=out_image.shape[1],
                       width=out_image.shape[2],
                       dtype=rasterio.uint8,
                       count=out_image.shape[0],
                       compress='lzw') as dst:
        dst.write(np.array(out_image, dtype='uint8'))
    
for f in utilities.listdir_nohidden(args.dest):
    if '.jp2' in f and not f.startswith('.'):
        #os.remove(os.path.join(args.dest, f))
        os.remove(f)

if args.delete_intermediate_files:
    if intermediate_existed:
        shutil.rmtree(os.path.join(args.intermediate_folder, f'{downloaded_product["title"]}.SAFE')) 
    else:
        shutil.rmtree(args.intermediate_folder)

#maria e linda bebe mmoooooooooo!!!!!!       
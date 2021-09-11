import errno
import pyproj
from git import Repo
from pathlib import Path
from shapely import geometry
import pandas as pd
import datetime
import glob
import os
import geopandas as gpd
import numpy as np
from sentinelsat import SentinelAPI
import shutil
import zipfile
import shutil
import numpy as np
import geopandas as gpd
import rasterio
import rasterio.mask
from sentinelsat import SentinelAPI
from datetime import date, timedelta
from mdutils.mdutils import MdUtils

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)


def transform_shapefile(shp):
    p1 = pyproj.Proj('epsg:4326', preserve_units=False)
    p2 = pyproj.Proj('epsg:32629', preserve_units=False)
    shp_t={
        'type':shp['type'],
        'id':shp['id'],
        'properties':shp['properties'],
        'geometry':{'type':shp['geometry']['type'],
                    'coordinates':[pt for pt in pyproj.itransform(p1,p2,shp['geometry']['coordinates'][0], always_xy=True)]}}
    to_mask_input = [geometry.Polygon([[p[0], p[1]] for p in shp_t['geometry']['coordinates']])]
    return to_mask_input

def download_most_recent_product(products_dataframe, polygon_to_overlap, download_path, username='fernandeslouro', pw='copernicospw', server='https://scihub.copernicus.eu/dhus', unzip=True):
    products_dataframe['footprint'] = gpd.GeoSeries.from_wkt(products_dataframe['footprint'])
    products_dataframe = gpd.GeoDataFrame(products_dataframe, geometry='footprint')
    products_dataframe['intersection_area'] = products_dataframe.apply(lambda row: 
                                                         polygon_to_overlap.intersection(row.footprint).area/polygon_to_overlap.area, axis=1)
    print(f"{len(products_dataframe)} available products")
    # download them all
    to_download = products_dataframe[products_dataframe.intersection_area == max(products_dataframe.intersection_area)]
    to_download = to_download.sort_values('generationdate', ascending=False)
    to_download = single_row_dataframe_to_dict(to_download)
    download_no_fail(to_download['uuid'], download_path, username, pw, server)
    if unzip:
        with zipfile.ZipFile(os.path.join(download_path, to_download['title']+'.zip'), 'r') as zip_ref:
            zip_ref.extractall(download_path)
        os.remove(os.path.join(download_path, to_download['title']+'.zip'))
    return to_download


def download_no_fail(product, path, username, password, server):
    api = SentinelAPI(username, password, server)
    print(f'Trying to download {product}')
    try:
        output = api.download(product, directory_path=path)
    except:
        download_no_fail(product, path, username, password, server)
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


def get_zone_info(cutoff_name, county=True):
    if county == 'True':
        level=2
    else:
        level = 3
    
    all_shapes = gpd.read_file(f"shapefiles/gadm36_PRT_{level}.shp")
    cutoff_shp = all_shapes[all_shapes[f'NAME_{level}']==cutoff_name].iloc[0].geometry
    all_shapes_ptcrs = all_shapes.to_crs(epsg=32629)
    cutoff_shp_ptcrs = all_shapes_ptcrs[all_shapes_ptcrs[f'NAME_{level}']==cutoff_name].iloc[0].geometry

    outer_square = polygon_outer_square(cutoff_shp)

    return cutoff_shp, cutoff_shp_ptcrs, outer_square


def get_product(username, password, server, outer_square, days_back):
    api = SentinelAPI(username, password, server)
    products = api.query(outer_square,
                     date=(date.today() - timedelta(days_back), date.today()),
                     platformname='Sentinel-2',
                     cloudcoverpercentage=(0, 30))

    return api.to_dataframe(products)


def download_latest(intermediate_folder, dest, cutoff_name, county, days_back, username, password, server, delete_intermediate_files):
    cutoff_shp, cutoff_shp_ptcrs, outer_square = get_zone_info(cutoff_name, county=county)

    intermediate_existed = os.path.isdir(intermediate_folder)
    os.makedirs(intermediate_folder, exist_ok=True)
    os.makedirs(dest, exist_ok=True)

    products_df = pd.DataFrame()

    days_back = int(days_back)

    while products_df.empty:
        products_df = get_product(username, password, server, outer_square, days_back)
        days_back += 1

    downloaded_product = download_most_recent_product(products_df, polygon_to_overlap=cutoff_shp, download_path=intermediate_folder)
    
    # copy jp2 to dest
    subfolders_copy(os.path.join(intermediate_folder, downloaded_product['title'] + '.SAFE'), dest)

    # save cropped jp2 with same name 
    for i in [img for img in listdir_nohidden(dest) if img.endswith('.jp2')]:
        for namepart in i.split('/')[-1].split('_'):
            if namepart.startswith('202'):
                imgname = f'{namepart[:4]}-{namepart[4:6]}-{namepart[6:8]}_{namepart[9:11]}:{namepart[11:13]}'
                break
        #with rasterio.open(os.path.join(dest, i)) as src:
        print(dest, i)
        with rasterio.open(i) as src:
            out_image, _ = rasterio.mask.mask(src, [cutoff_shp_ptcrs], crop=True, nodata=0, all_touched=True)
    
        out_image = append_transparency_band(out_image)
            
        with rasterio.open(os.path.join(dest, imgname)+'.png','w',
                       driver='PNG',
                       height=out_image.shape[1],
                       width=out_image.shape[2],
                       dtype=rasterio.uint8,
                       count=out_image.shape[0],
                       compress='lzw') as dst:
            dst.write(np.array(out_image, dtype='uint8'))
    
    for f in listdir_nohidden(dest):
        if '.jp2' in f and not f.startswith('.'):
            #os.remove(os.path.join(dest, f))
            os.remove(f)

    if delete_intermediate_files:
        if intermediate_existed:
            shutil.rmtree(os.path.join(intermediate_folder, f'{downloaded_product["title"]}.SAFE')) 
        else:
            shutil.rmtree(intermediate_folder)
    
    return str(os.path.join(dest, imgname)+'.png')

def delete_initial_lines_file(filepath, lines_nr):
    with open(filepath, 'r') as fin:
        data = fin.read().splitlines(True)
    with open(filepath, 'w') as fout:
        fout.writelines(data[3:])

def create_markdown_file(new_image_path, output_path):

    # crate new markdown file referencing the image, inside correct directory
    img_date = os.path.basename(new_image_path).split("_")[0]
    
    mdFile = MdUtils(file_name=output_path)
    mdFile.write("---")
    mdFile.new_line("layout: page")
    mdFile.new_line("---")

    mdFile.new_paragraph(f"This is a satellite picture of Mação, my home region, taken on {img_date}."
        "It is the latest available image from ESA's Sentinel 2 satellites. It's kept updated using "
        "some [scripts](https://github.com/fernandeslouro/terras) I made to have something on my "
        "website to mark the passage of time. It all runs on a rented server I also use to self-host "
        "some services.")
    mdFile.new_paragraph("In the summer months, the picture will appear very brown. Most of the area was burned in recent wildfires, and it shows when the grass dies. In winter, it turns greener, but there's not a lot of forest now. The population is also shrinking at an alarming pace.")
    mdFile.new_paragraph("I grew up here, and I have love for this land. You should visit if you have the chance.")

    image_text = f"Mação viewed from the sky at {img_date}"
    mdFile.new_line(mdFile.new_inline_image(text=image_text, path=os.path.join("/assets/images", os.path.basename(new_image_path))))

    mdFile.create_md_file()

    # 3 empty lines are being created for some misterious reason, and they break the formatting
    delete_initial_lines_file(output_path, 3)

def git_push(list_to_commit, repo_path, commit_message):
    try:
        repo = Repo(repo_path)
        print(1)
        repo.git.add(list_to_commit)
        print(2)
        repo.index.commit(commit_message)
        print(3)
        origin = repo.remote(name='origin')
        print(4)
        origin.push()
    except:
        print('Some error occured while pushing the code') 


def refresh_markdown(new_image_path, blog_dir):
    # delete old markdon file
    silentremove(os.path.join(blog_dir, "_pages", "hometown.md"))
    blog_image_path = os.path.join(blog_dir, "assets/images", Path(new_image_path).name)

    shutil.copyfile(new_image_path, blog_image_path)

    new_markdown_path = os.path.join(blog_dir, "_pages", "hometown.md")

    # delete old image
    #for f in os.listdir(os.path.join(blog_dir, "_pages")):
        #if f.endswith(".png") and f != new_image_path:
            #os.remove(os.path.join(blog_dir, "_pages", "hometown.md"))

    create_markdown_file(new_image_path, new_markdown_path)

    inside_blog_image_path = os.path.join("assets/images", Path(new_image_path).name)
    files_to_commit = ["_pages/hometown.md", inside_blog_image_path]
    print(files_to_commit)
    # commit and push to blog
    git_push(files_to_commit, os.path.join(blog_dir),
        f'Updating with image from {new_image_path.split("-")[0]}')

def silentremove(filename):
    try:
        os.remove(filename)
    except OSError as e: # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise # re-raise exception if a different error occurred

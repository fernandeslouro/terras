# %% 
from utilities import download_latest, refresh_markdown
import argparse
import os
# %%
if __name__ == "__main__":

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

    parser.add_argument('--blog_dir', action='store', type=str, help='Path of the git repository to be updated')
    args=parser.parse_args()

    # download new image
    new_image_path = download_latest(intermediate_folder=args.intermediate_folder, 
                    dest=args.dest,
                    cutoff_name=args.cutoff_name,
                    county=args.county, 
                    days_back=args.days_back, 
                    username=args.username,
                    password = args.password,
                    server= args.server,
                    delete_intermediate_files=args.delete_intermediate_files)


    refresh_markdown(new_image_path, args.blog_dir)
# %% 
from types import MethodDescriptorType
from utilities import download_latest, git_push
import argparse
import os
from mdutils.mdutils import MdUtils
from mdutils import Html
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

    # delete old markdon file
    os.remove(os.path.join(args.blog_dir, "_pages", "hometown.md"))

    # delete old image
    for f in os.listdir(os.path.join(args.blog_dir, "_pages")):
        if f.endswith(".png") and f != new_image_path:
            os.remove(os.path.join(args.blog_dir, "_pages", "hometown.md"))

  # %% 
    new_image_path = "/home/j/projects/terras/2021-08-22_11:21.png"
    print(os.path.basename(new_image_path))
    # %%
    # crate new markdown file referencing the image, inside correct directory
    mdFile = MdUtils(file_name='hometown', title='Mação')
    img_date = os.path.basename(new_image_path).split("_")[0]

    mdFile.new_paragraph(f"This is a satellite picture of Mação, my home region, on {img_date}. It is the latest available image from ESA's Sentinel 2 satellites. It's kept updated using some [scripts](https://github.com/fernandeslouro/terras) I made to have something on my website to mark the passage of time.")

    mdFile.new_paragraph("In the summer months, the picture will appear very brown. Most of the area was burned in recent wildfires, and it shows when the grass dies. In winter, it turns greener, but there's not a lot of forest now. The population is also shrinking at an alarming pace.")

    mdFile.new_paragraph("I grew up here, and I have love for this land. You should visit if you have the chance.")

    mdFile.new_paragraph(" ")
    mdFile.new_paragraph(" ")

    image_text = f"Mação viewed from the sky at {img_date}"
    mdFile.new_line(mdFile.new_inline_image(text=image_text, path=new_image_path))

    mdFile.create_md_file()
# %%
    # commit and push to blog
    git_push(os.path.join(args.blog_dir, ".git"),
        f'Updating with image from {new_image_path.split("-")[0]}')

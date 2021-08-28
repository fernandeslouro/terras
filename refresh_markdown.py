from utilities import refresh_markdown
import argparse

if __name__ == "__main__":

    parser=argparse.ArgumentParser()
    parser.add_argument('--new_image_path', action='store', type=str, help='Path of the image to be used in the refreshed markdown file')
    parser.add_argument('--blog_dir', action='store', type=str, help='Path of the git repository to be updated')
    args=parser.parse_args()

    refresh_markdown(args.new_image_path, args.blog_dir)
# terras

This repo includes some utilities I made for downloading Sentinel satellite data I find interesting.

download_latest.py is a script to download freshest available image from a Portuguese parish or municipality of your choice. Example usage to download the latest image from the last 7 days, for the Mação municipality:

```shell
python download_latest.py --intermediate_folder <folder_for_intermediate_files> 
    --dest <destination_folder> --cutoff_name Mação --county True --days_back 7
    --username <copernicus_username> --password <copernicus_password>
    --server https://scihub.copernicus.eu/dhus --delete_intermediate_files
```

You should get something that looks like this:

![Mação](macao_example.png)
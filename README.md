# reddit-place-2022
Scripts for reading/viewing the Reddit /r/place 2022 Event data.

# Viewer
This repo contains a viewer for looking at a form of the full pixel update data (~160M pixel updates) rendered in realtime, with some initial capabilities to seek. 

The data for the entire image has been partitioned into data for many 32x32 tiles and packed into a binary format. The full details of the encoding are available at the link in the "Data" section. This was done to reduce the original 11GiB CSV zip data down to a 1.1GB zip. The format is also much easier to batch process and better for fast viewing when zoomed in (not implemented here, yet).

To download the data and start the viewer, do the following:
```bash
wget "https://archive.org/download/reddit_place_2022_tile_data/place_2022_tiles.zip"
unzip place_2022_tiles.zip
pip3 install tqdm pygame
python3 scripts/viewer.py
```

### Data
Download the dataset at https://archive.org/details/reddit_place_2022_tile_data
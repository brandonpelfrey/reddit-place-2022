import os
import sys
import pygame
import numpy as np
import bisect
from struct import unpack
from tqdm import tqdm
import datetime

# Directory, relative to where the script is run, containing tile data
DIR = 'packed_tiles'

# Window resolution
WIDTH = 1000
HEIGHT = 1000

# Number of real world seconds to advance for each frame drawn to the screen
REAL_SECONDS_PER_FRAME = 60

# Set to True if you want to see a visualization of changes superimposed on top of the image
DRAW_HEATMAP = False

# Colors used across the lifetime of the event.
COLORS = [(0, 0, 0), (0, 204, 192), (148, 179, 255), (106, 92, 255), (0, 158, 170), (228, 171, 255), (0, 0, 0), (0, 117, 111), (0, 163, 104), (0, 204, 120), (36, 80, 164), (54, 144, 234), (73, 58, 193), (81, 82, 82), (81, 233, 244), (109, 0, 26), (109, 72, 47), (126, 237, 86), (129, 30, 159), (137, 141, 144), (156, 105, 38), (180, 74, 192), (190, 0, 57), (212, 215, 217), (222, 16, 127), (255, 56, 129), (255, 69, 0), (255, 153, 170), (255, 168, 0), (255, 180, 112), (255, 214, 53), (255, 248, 184), (255, 255, 255)]

# One 32x32 tile.
class Tile:
  # Create a tile given the path to the binary file
  def __init__(self, file_path):
    with open(file_path, 'rb') as tile_file:
      # Read tile size (x,y) and tile location within the grid 
      self.res_x, self.res_y = unpack('II', tile_file.read(4+4))
      self.tile_x, self.tile_y = unpack('II', tile_file.read(4+4))
      # Number of pixel updates in this data
      self.n = unpack('I', tile_file.read(4))[0]
      # Packed pixel updates
      self.data = np.fromfile(tile_file, dtype=np.uint16, count=self.n)
      # User IDs for each pixel update
      self.users = np.fromfile(tile_file, dtype=np.uint32, count=self.n)
      # Timestamps for each pixel update
      self.timestamps = np.fromfile(tile_file, dtype=np.uint32, count=self.n)
    # Tile maintains internal state of the index of the next update to show
    # 0 is first update, 1 is second, ..., self.n-1 is last pixel update in this tile
    self.i = 0

  # Move timeline to target timestamp, this uses the fact that the timestamps are ascending
  def seek(self, target_ts):
    self.i = bisect.bisect_left(self.timestamps, target_ts)
  
  # Yield pixel updates (x, y, color index) from the current index until the target timestamp
  def get_until_ts(self, target_ts):
    while self.i < self.n and self.timestamps[self.i] < target_ts:
      x = (self.data[self.i] >> 0) & 0b11111
      y = (self.data[self.i] >> 5) & 0b11111
      c = (self.data[self.i] >> 10) & 0b111111
      yield (self.res_x * self.tile_x + x, self.res_y * self.tile_y + y, c)
      self.i += 1

######################################

# VIEWER CODE
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), 0, 32)

# Load all tiles in DIR
tiles = []
filenames = sorted(os.listdir(DIR))
for file_name in tqdm(filenames, desc='Loading updates'):
  tiles.append(Tile(f"{DIR}/{file_name}"))

# As a slight optimization, this script is currently viewing just the top left quadrant.
# Discard tiles which aren't in this area since they won't contribute to the animation
tiles = list(filter(lambda tile: tile.tile_x<32 and tile.tile_y<32, tiles))

# Count total updates drawn so far
n_updates = 0

# Image data begins ~47k seconds into April 1st UTC
current_ts = 47 * 1000 * 1000

# Image showing all pixel updates so far
image_data = np.zeros((WIDTH, HEIGHT, 3), np.int32)

# "Heatmap"
delta_image = np.zeros((WIDTH, HEIGHT, 3), np.int32)

# Initially, fill the screen with white
image_data[:] = (255, 255, 255)

# Advance to timestamp 'next_ts', update image_data, (and delta_image "heatmap" if passed in)
def update(tiles, next_ts, image_data, delta_image=None):
  frame_updates = 0
  for tile in tiles:
      for (x,y,c) in tile.get_until_ts(next_ts):
        frame_updates += 1
        if x<WIDTH and y<HEIGHT:
          image_data[x,y] = COLORS[c]
          if delta_image:
            delta_image[x,y] = (255,0,0)
  return frame_updates

# Forever...
while 1:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()
    
    # Walk forward in time, tell all the tiles to update the image up until that time
    current_ts += 60 * 1000

    if DRAW_HEATMAP:
      # In this mode, every pixel update additionally sets a red pixel in a second 'delta image' 
      frame_updates = update(tiles, current_ts, image_data, delta_image)
      # Make the delta image fade to black slowly
      delta_image[:] -= (10,10,10)
      # Clamp the delta image ...
      delta_image = np.clip(delta_image, (0,0,0), (255,255,255))
      # ... and superimpose on top of the original image
      present_image = np.clip((image_data >> 1) + delta_image, (0,0,0), (255,255,255))
    else:
      # Same as above, but no delta image stuff
      frame_updates = update(tiles, current_ts, image_data)
      present_image = image_data

    n_updates += frame_updates

    # Draw to the screen
    pygame.surfarray.blit_array(screen, present_image)
    pygame.display.flip()

    # Update title with some statistics
    current_dt = datetime.datetime(2022,4,1) + datetime.timedelta(milliseconds=current_ts)
    pygame.display.set_caption(f"Current timestamp={current_dt} updates={frame_updates:,} ({n_updates:,} Total)")
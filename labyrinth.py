from PIL import Image
import json
import random
import queue


class Tile:
    def __init__(self):
        self.empty = True
        self.queued = False
        self.north = False
        self.east = False
        self.south = False
        self.west = False
        self.tunnel = False

    def open(self, dir_x, dir_y):
        '''Opens a connection in the given direction regardless of wether it is
        open already. Possible inputs: (1,0), (0,1), (-1,0), (0,-1)'''
        if dir_x == 0:
            if dir_y == 1:
                self.south = True
            else:
                self.north = True
        else:
            if dir_x == 1:
                self.east = True
            else:
                self.west = True

    def is_open(self, dir_x, dir_y):
        '''Returns True if the tile has an open connection in the given direction.
        Otherwise returns False. Possible inputs: (1,0), (0,1), (-1,0), (0,-1)'''
        if dir_x == 0:
            if dir_y == 1:
                return self.south
            else:
                return self.north
        else:
            if dir_x == 1:
                return self.east
            else:
                return self.west

# The following functions are not part of the Tile class
def in_bounds(x: int, y: int) -> bool:
    '''Returns True if the given coordinates are within the labyrinth's bounds.
    Otherwise returns False'''
    if x < 0 or y < 0 or x >= config['WIDTH'] or y >= config['HEIGHT']:
        return False
    else:
        return True


def process_tile(coordinates: tuple, queue: queue):
    '''The given coordinate is processed. Makes connections to neighbouring tiles with
    open connections and possibly creates open connections to empty neighbouring tiles
    in which case those empty tiles are put to the processing queue.'''
    x, y = coordinates
    
    # A processed tile is neither empty nor queued anymore
    lab[x][y].empty = False
    lab[x][y].queued = False

    connection_made = False
    # Look at all four neigbouring tiles in random order
    for i in range(len(sequence)):
        neigh_x = x + sequence[i][0]
        neigh_y = y + sequence[i][1]

        # Can only have connection to tile in bounds
        if not in_bounds(neigh_x, neigh_y):
            continue
        # Can only have connection to unqueued tile (this prevents loops in the labyrinth)
        if lab[neigh_x][neigh_y].queued:
            continue

        # Decide randomly if a connection to an empty neighbouring tile is made
        if lab[neigh_x][neigh_y].empty:
            if random.random() <= config["CON_PROB"] or queue.qsize() <= config["LOOSE_ENDS"]:
                lab[x][y].open(sequence[i][0], sequence[i][1])
                queue.put((neigh_x, neigh_y))
                lab[neigh_x][neigh_y].queued = True
                connection_made = True
        # Only make a connection to a processed neighbouring tile if that tile also has an open connection to this one
        else:
            if lab[neigh_x][neigh_y].is_open(-sequence[i][0], -sequence[i][1]):
                lab[x][y].open(sequence[i][0], sequence[i][1])
                # Don't que neighbour tho because it was already processed

                # Try to create a tunnel in the opposite direction of the connected neighbour
                # A tunnel can only be created if no random connection was made beforehand
                if connection_made:
                    continue
                # A tunnel can only be made if there are no other tunnels in any orthogonal direction
                tunnel_found = False
                for j in range(config["WIDTH"]):
                    if lab[j][y].tunnel:
                        tunnel_found = True
                        break
                for j in range(config["HEIGHT"]):
                    if lab[x][j].tunnel:
                        tunnel_found = True
                        break
                if tunnel_found:
                    continue
                    
                # Loop through a line of tiles
                search_length = 0
                skipped_tiles = random.randint(config["MIN_TUN_DIS"], config["MAX_TUN_DIS"])
                search_location = (x + skipped_tiles * -sequence[i][0], y + skipped_tiles * -sequence[i][1])
                to_be_tunnel = None
                while True:
                    # Pay attention to the maximum tunnel distance
                    if search_length >= config["MAX_TUN_DIS"]:
                        break
                    # Move to next tile
                    search_location = (search_location[0] + -sequence[i][0], search_location[1] + -sequence[i][1])
                    search_length += 1
                    # Stop searching if the bounds of the labyrinth are reached
                    if not in_bounds(search_location[0], search_location[1]):
                        break
                    current_tile = lab[search_location[0]][search_location[1]]
                    # Is the current tile empty?
                    if current_tile.empty and not current_tile.queued:
                        if to_be_tunnel == None:
                            # This tile is empty but no position for the tunnel was yet determined
                            to_be_tunnel = current_tile
                        else:
                            # This tile is empty and a tunnel position was already determined, so the current tile has to be queued
                            queue.put((search_location[0], search_location[1]))
                            current_tile.queued = True
                            # Additionally the tunnel has to be created
                            to_be_tunnel.empty = False
                            to_be_tunnel.tunnel = True
                            to_be_tunnel.open(-sequence[i][0], -sequence[i][1])
                            lab[x][y].tunnel = True
                            break
                    else:
                        to_be_tunnel = None
                # After creating a tunnel, no other connections can be made (so break the loop)
                if lab[x][y].tunnel: break
    # Shuffle direction sequence
    random.shuffle(sequence)


############################## PROGRAM START #######################################################            
# Load json config
with open('config.json', 'r') as f:
    config = json.load(f)

# All possible Tiles: North, East, South, West
tile_names = ["NESW", "NES", "NEW", "NSW", "ESW", "NS", "EW", "NE", "ES", "SW", "NW", "N", "E", "S", "W", "TN", "TE", "TS", "TW", "BLACK", "ENTRY"]

# Load all the tile images
tile_images = []
for name in tile_names:
    tile_images.append(Image.open("LabTiles/" + name + ".png"))

# The tile size is determined by the loaded images
TILE_SIZE = tile_images[0].size[0]

# The sequence saves the possible neighbouring directions of a tile
sequence = [(1,0), (0,1), (-1,0), (0,-1)]

# Tile checks are put in a queue. That way they will be processed 'first in first out'.
# Queue or LifoQueue
tile_queue = queue.LifoQueue()

# Create a 2d list to store the tiles of the labyrinth
lab = []
for y in range(config['HEIGHT']):
    lab.append([])
    for x in range(config['WIDTH']):
        lab[y].append(Tile())

# Step 1: Process Labyrinth
tile_queue.put(config['START'])
while not tile_queue.empty():
    process_tile(tile_queue.get(), tile_queue)

# Step 2: Fill tiles that are still empty
# For that, every tile makes one connection to a neigbouring tile that is not empty
empty_exists = True
while empty_exists:
    empty_exists = False
    for x in range(config["WIDTH"]):
        for y in range(config["HEIGHT"]):
            random.shuffle(sequence)
            current_tile = lab[x][y]
            # Only process empty tiles
            if not current_tile.empty:
                continue
            # Search a neighbouring tile that is not empty
            found = False
            for i in range(len(sequence)):
                neigh_x = x + sequence[i][0]
                neigh_y = y + sequence[i][1]
                if not in_bounds(neigh_x, neigh_y):
                    continue
                neigbour = lab[neigh_x][neigh_y]
                if not neigbour.empty and not neigbour.tunnel:
                    current_tile.open(sequence[i][0], sequence[i][1])
                    current_tile.empty = False
                    neigbour.open(-sequence[i][0], -sequence[i][1])
                    found = True
                    break
            if not found:
                empty_exists = True

# Step 3: Generate image out of the 2d list
img = Image.new(mode = "RGB",
                size = [config['WIDTH'] * TILE_SIZE, config['HEIGHT'] * TILE_SIZE], 
                color = (255, 255, 255))
for x in range(config["WIDTH"]):
    for y in range(config["HEIGHT"]):
        name = ""
        if lab[x][y].tunnel: name += 'T'
        if lab[x][y].north: name += 'N'
        if lab[x][y].east: name += 'E'
        if lab[x][y].south: name += 'S'
        if lab[x][y].west: name += 'W'
        if name == "": name = "BLACK"
        img.paste(tile_images[tile_names.index(name)], (x * TILE_SIZE, y * TILE_SIZE))

# Add start end destination points
entry_img = tile_images[tile_names.index("ENTRY")]
img.paste(entry_img, [i * TILE_SIZE for i in config["START"]], mask=entry_img)
img.paste(entry_img, [i * TILE_SIZE for i in config["DEST"]], mask=entry_img)

# Save image as PNG
img.save("Labyrinth.png", "PNG")
# Pygame sprite Example
import pygame
import random
import os
import json
import logging
import sys
import argparse
import config
import utils 
import ctypes

# If we're on Windows do this thing to deal with display scaling issues...
try:
    ctypes.windll.user32.SetProcessDPIAware()
except:
    pass

"""
We have config.tiles and extend it to include non-special tiles as well.  These have their filename as the index into config.tiles.
Within this program scene_data["tile"] entries are either 
- None if the tile is blank
- a dict containing: 
    "tile" a reference to a config.tiles entry otherwise
    "rotate" either 0 or 180 indicating if the tile should be rotated
"""

#logging.basicConfig(filename='platform.log', filemode='w', level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
module = sys.modules['__main__'].__file__
log = logging.getLogger(module)

parser = argparse.ArgumentParser(description='Platformgame scene designer')
parser.add_argument('scene_file', 
                     help='scene file to create or update')
args = parser.parse_args()
print("Scene file = {}".format(args.scene_file))

# Load the tile options so that we know how many there are going to be!
utils.load_default_tiles()
number_of_tile_options = len(config.tiles)

TILE_OPTIONS_X_OFFSET = (config.SCREEN_WIDTH_TILES+1)*config.TILE_SIZE_PX
TILE_OPTIONS_Y_OFFSET = 0
TILE_OPTIONS_PER_ROW = 18
TILE_OPTIONS_PADDING = 20
TILE_OPTIONS_SIZE = int(config.TILE_SIZE_PX*0.9) 
TEXT_SIZE = 50

# Get the screen resolution and consider scaling everything?
pygame.init()
pygame.mixer.init()
displayInfo = pygame.display.Info()

width = TILE_OPTIONS_X_OFFSET + TILE_OPTIONS_PER_ROW*(TILE_OPTIONS_SIZE+TILE_OPTIONS_PADDING)
height = max(config.SCREEN_HEIGHT_TILES*config.TILE_SIZE_PX, (int(number_of_tile_options/TILE_OPTIONS_PER_ROW)+1)*(TILE_OPTIONS_SIZE+TILE_OPTIONS_PADDING)+TEXT_SIZE)

print ("default width, height {}, {}.  Screen width, height {},{}".format(width, height, displayInfo.current_w, displayInfo.current_h))

scale_factor = min(displayInfo.current_w / width, displayInfo.current_h / height)
print("Scale by {}".format(scale_factor))
config.TILE_SIZE_PX = int(config.TILE_SIZE_PX * scale_factor)
TILE_OPTIONS_SIZE = int(TILE_OPTIONS_SIZE*scale_factor)
TILE_OPTIONS_PADDING = int(TILE_OPTIONS_PADDING*scale_factor)
TILE_OPTIONS_X_OFFSET = (config.SCREEN_WIDTH_TILES+1)*config.TILE_SIZE_PX


screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
print("Window width = {}, height = {}".format(screen.get_rect().width, screen.get_rect().height))

pygame.display.set_caption("Scene designer")
clock = pygame.time.Clock()

blank_tile = pygame.Surface((config.TILE_SIZE_PX, config.TILE_SIZE_PX))

player = None
tile_options = pygame.sprite.Group()
current_option = None

idx = 0
for tile_id, tile_data in config.tiles.items():
    tile = pygame.sprite.Sprite()
    
    tile_data.image = utils.load_tile_image(tile_data, (config.TILE_SIZE_PX, config.TILE_SIZE_PX))
    tile.unselected_image = utils.load_tile_image(tile_data, (TILE_OPTIONS_SIZE, TILE_OPTIONS_SIZE))
    tile.tile_data = tile_data
    selected_image = utils.load_tile_image(tile_data, (TILE_OPTIONS_SIZE, TILE_OPTIONS_SIZE))
    pygame.draw.rect(selected_image, (255, 0, 0), (0,0,config.TILE_SIZE_PX,config.TILE_SIZE_PX), 2)
    tile.selected_image = selected_image
    tile.image = tile.unselected_image
    tile.tile_id = tile_id
    tile.rect = tile.image.get_rect()
    tile.rect.top = TILE_OPTIONS_Y_OFFSET + int(idx / TILE_OPTIONS_PER_ROW) * (TILE_OPTIONS_SIZE + TILE_OPTIONS_PADDING)
    tile.rect.left = TILE_OPTIONS_X_OFFSET + (idx % TILE_OPTIONS_PER_ROW) * (TILE_OPTIONS_SIZE + TILE_OPTIONS_PADDING)
    tile_options.add(tile)
    idx += 1

scene_data = {}
scene_file_path = os.path.join(config.scene_folder, args.scene_file)
if os.path.isfile(scene_file_path):
    with open(scene_file_path) as scene_file:
        scene_data = json.load(scene_file)
    player_start = scene_data["player_start"]
    scene_data["tiles"][player_start[1]][player_start[0]] = {"id": "PLAYER"}    
else:   
    scene_data = {}
    scene_data["tiles"] = [ [ {"id": "BLANK"} for x in range( config.SCREEN_WIDTH_TILES ) ] for y in range( config.SCREEN_HEIGHT_TILES ) ]
    scene_data["player_start"] = [0,0]
    scene_data["lock_time"] = 8000
    
class Point(pygame.sprite.Sprite):
    def __init__(self, pos):
        super(pygame.sprite.Sprite, self).__init__()
        self.rect = pygame.Rect(pos[0], pos[1], 1, 1)

# sprite is the sprite that represents the tile on the scene
# 
# It has tile.x = the x co-ordinate.  tile.y = the y co-ordinate
# This function updates the tile.image to be the image for the tile with ID tile_id
# It also updates tile.id and the relevant entry in scene_data to be the new tile_id 
def update_screen_tile(sprite, tile_id=None, rotate=0):
    if tile_id == "BLANK":
        sprite.image = blank_tile.copy()
        scene_data["tiles"][sprite.y][sprite.x] = {"id": "BLANK"}
    else:
        sprite.image = pygame.transform.rotate(config.tiles[tile_id].image.copy(), rotate)
        scene_data["tiles"][sprite.y][sprite.x] = {"filename": config.tiles[tile_id].filename, "path": config.tiles[tile_id].path, "rotate": rotate}
        if not "." in tile_id:
            scene_data["tiles"][sprite.y][sprite.x]["id"] = tile_id
            
    sprite.rect = sprite.image.get_rect()
    sprite.rect.left = sprite.x*config.TILE_SIZE_PX        
    sprite.rect.top = sprite.y*config.TILE_SIZE_PX        
    sprite.tile_id = tile_id

scene_tiles = pygame.sprite.Group()
for x in range(config.SCREEN_WIDTH_TILES):
    for y in range(config.SCREEN_HEIGHT_TILES):
        tile = pygame.sprite.Sprite()
        tile.x = x
        tile.y = y
        rotate = 0
        if "rotate" in scene_data["tiles"][y][x]:
            rotate = scene_data["tiles"][y][x]["rotate"]    
        if "id" in scene_data["tiles"][y][x]:
            update_screen_tile(tile, scene_data["tiles"][y][x]["id"], rotate=rotate)
        else:
            update_screen_tile(tile, scene_data["tiles"][y][x]["filename"], rotate=rotate)
        scene_tiles.add(tile)

pygame.font.init()
myfont = pygame.font.SysFont('Comic Sans MS', 30)
textsurface = myfont.render('Done', False, (255, 255, 255))
done_tile = pygame.sprite.Sprite()
done_tile.image = textsurface
done_tile.rect = done_tile.image.get_rect()
done_tile.rect.top = screen.get_rect().height - 50
print("Window width = {}, height = {}".format(screen.get_rect().width, screen.get_rect().height))
print("done tile top = {}".format(done_tile.rect.top))
done_tile.rect.left = TILE_OPTIONS_X_OFFSET
done_group = pygame.sprite.Group()
done_group.add(done_tile)

# Game loop
running = True
while running:
    # keep loop running at the right speed
    clock.tick(config.FPS)
    # Process input (events)
    for event in pygame.event.get():
        # check for closing window
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False
                continue

    if pygame.mouse.get_focused():
        buttons = pygame.mouse.get_pressed()
        if buttons != (0,0,0):
            point = Point(pygame.mouse.get_pos())
            option_selected = pygame.sprite.spritecollideany(point, tile_options, False)
            if option_selected:
                log.debug("Option selected")
                if current_option:
                    current_option.image = current_option.unselected_image
                current_option = option_selected
                option_selected.image = option_selected.selected_image
                    
            scene_tile_selected = pygame.sprite.spritecollideany(point, scene_tiles, False)
            keys_pressed=pygame.key.get_pressed()  #checking pressed keys
            log.debug("Mouse click.  scene_tile_selected = {}.  Buttons {}.  Key c = {}.  Key shift = {}".format(scene_tile_selected, buttons, keys_pressed[pygame.K_c], keys_pressed[pygame.K_LSHIFT]))
            if scene_tile_selected and buttons[0] and keys_pressed[pygame.K_c] and scene_tile_selected.tile_id != "BLANK":
                log.info("selected tile ID = {}".format(scene_tile_selected.tile_id))
                option_selected = next(option for option in tile_options if option.tile_id == scene_tile_selected.tile_id)
                if current_option:
                    current_option.image = current_option.unselected_image
                current_option = option_selected
                option_selected.image = option_selected.selected_image

            elif scene_tile_selected and buttons[0] and current_option != None:
                update_screen_tile(scene_tile_selected, current_option.tile_id, rotate=180 if keys_pressed[pygame.K_LSHIFT] else 0)
            elif scene_tile_selected and buttons[2] == 1:
                update_screen_tile(scene_tile_selected, "BLANK")
            
            if done_tile.rect.colliderect(pygame.Rect(pygame.mouse.get_pos(), (1,1))):                
                for x in range(config.SCREEN_WIDTH_TILES):
                    for y in range(config.SCREEN_HEIGHT_TILES):
                        if scene_data["tiles"][y][x].get("id", None) == "PLAYER":
                            scene_data["tiles"][y][x]["id"] = "BLANK"                            
                            scene_data["player_start"] = [x, y]

                with open(scene_file_path, "w") as scene_file:
                    json.dump(scene_data, scene_file, indent=4)
                exit()
    
    # Update
    tile_options.update()

    # Draw / render
    screen.fill((0, 0, 0))
    tile_options.draw(screen)
    scene_tiles.draw(screen)
    done_group.draw(screen)
    for x in range(config.SCREEN_WIDTH_TILES):
        pygame.draw.line(screen, (100,100,100), [x*config.TILE_SIZE_PX, 0], [x*config.TILE_SIZE_PX,config.SCREEN_HEIGHT_TILES*config.TILE_SIZE_PX], 1)
    for y in range(config.SCREEN_HEIGHT_TILES):
        pygame.draw.line(screen, (100,100,100), [0, y*config.TILE_SIZE_PX], [config.SCREEN_WIDTH_TILES*config.TILE_SIZE_PX,y*config.TILE_SIZE_PX], 1)
   
    # *after* drawing everything, flip the display
    pygame.display.flip()

pygame.quit()
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
import tkinter as tk
from tkinter import simpledialog

#logging.basicConfig(filename='platform.log', filemode='w', level=logging.DEBUG)
logging.basicConfig(level=logging.INFO, format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
module = sys.modules['__main__'].__file__
log = logging.getLogger(module)

parser = argparse.ArgumentParser(description='Platformgame scene designer')
parser.add_argument('scene_file', 
                     help='scene file to create or update')
args = parser.parse_args()
print("Scene file = {}".format(args.scene_file))

TILE_OPTIONS_X_OFFSET = (config.SCREEN_WIDTH_TILES+2)*config.TILE_SIZE_PX
TILE_OPTIONS_Y_OFFSET = 20
TILE_OPTIONS_PER_ROW = 22
TILE_OPTIONS_SIZE = config.TILE_SIZE_PX + 20

#config.SCREEN_WIDTH_PX = TILE_OPTIONS_X_OFFSET + TILE_OPTIONS_PER_ROW*TILE_OPTIONS_SIZE
#config.SCREEN_HEIGHT_PX = config.SCREEN_HEIGHT_TILES*config.TILE_SIZE_PX

scene_data = {}
scene_file_path = os.path.join(config.scene_folder, args.scene_file)
if os.path.isfile(scene_file_path):
    with open(scene_file_path) as scene_file:
        scene_data = json.load(scene_file)
    player_start = scene_data["player_start"]
    scene_data["tiles"][player_start[1]][player_start[0]] = "PLAYER"
else:   
    scene_data = {}
    scene_data["tiles"] = [ [ "BLANK" for x in range( config.SCREEN_WIDTH_TILES ) ] for y in range( config.SCREEN_HEIGHT_TILES ) ]
    scene_data["player_start"] = [0,0]
    scene_data["lock_time"] = 8000
    
# initialize pygame and create window
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0,50)
pygame.init()
pygame.mixer.init()
config.SCREEN_WIDTH_PX = pygame.display.Info().current_w
config.SCREEN_HEIGHT_PX = pygame.display.Info().current_h - 100

screen = pygame.display.set_mode((config.SCREEN_WIDTH_PX, config.SCREEN_HEIGHT_PX))
pygame.display.set_caption("Scene designer")
clock = pygame.time.Clock()


blank_tile = pygame.Surface((config.TILE_SIZE_PX, config.TILE_SIZE_PX))

player = None
tile_options = pygame.sprite.Group()
current_option = None

utils.load_default_tiles()
idx = 0
for tile_id, tile_data in config.tiles.items():
    tile = pygame.sprite.Sprite()
    
    tile.unselected_image = utils.load_tile_image(tile_data)
    selected_image = utils.load_tile_image(tile_data)
    pygame.draw.rect(selected_image, (255, 0, 0), (0,0,config.TILE_SIZE_PX,config.TILE_SIZE_PX), 2)
    tile.selected_image = selected_image
    tile.image = tile.unselected_image
    tile.tile_id = tile_id
    tile.rect = tile.image.get_rect()
    tile.rect.top = TILE_OPTIONS_Y_OFFSET + int(idx / TILE_OPTIONS_PER_ROW) * TILE_OPTIONS_SIZE
    tile.rect.left = TILE_OPTIONS_X_OFFSET + (idx % TILE_OPTIONS_PER_ROW) * TILE_OPTIONS_SIZE
    tile_options.add(tile)
    idx += 1

class Point(pygame.sprite.Sprite):
    def __init__(self, pos):
        super(pygame.sprite.Sprite, self).__init__()
        self.rect = pygame.Rect(pos[0], pos[1], 1, 1)

# Tile is a sprite representing a tile on the scene.
# It has tile.x = the x co-ordinate.  tile.y = the y co-ordinate
# This function updates the tile.image to be the image for the tile with ID tile_id
# It also updates tile.id and the relevant entry in scene_data to be the new tile_id 
def update_screen_tile(tile, tile_id):
    if tile_id == "BLANK":
        tile.image = blank_tile.copy()
    else:
        for tile_option in tile_options:
            if tile_option.tile_id == tile_id:
                tile.image = tile_option.unselected_image.copy()   

    tile.rect = tile.image.get_rect()
    tile.rect.left = tile.x*config.TILE_SIZE_PX        
    tile.rect.top = tile.y*config.TILE_SIZE_PX        
    tile.tile_id = tile_id
    scene_data["tiles"][tile.y][tile.x] = tile_id

scene_tiles = pygame.sprite.Group()
for x in range(config.SCREEN_WIDTH_TILES):
    for y in range(config.SCREEN_HEIGHT_TILES):
        tile = pygame.sprite.Sprite()
        tile.x = x
        tile.y = y
        update_screen_tile(tile, scene_data["tiles"][y][x])
        scene_tiles.add(tile)

pygame.font.init()
myfont = pygame.font.SysFont('Comic Sans MS', 30)
textsurface = myfont.render('Done', False, (255, 255, 255))
done_tile = pygame.sprite.Sprite()
done_tile.image = textsurface
done_tile.rect = done_tile.image.get_rect()
done_tile.rect.top = screen.get_rect().height - 50
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

    if pygame.mouse.get_focused():
        buttons = pygame.mouse.get_pressed()
        if buttons != (0,0,0):
            point = Point(pygame.mouse.get_pos())
            option_selected = pygame.sprite.spritecollideany(point, tile_options, False)
            if option_selected:
                if current_option:
                    current_option.image = current_option.unselected_image
                current_option = option_selected
                option_selected.image = option_selected.selected_image
                    
            scene_tile_selected = pygame.sprite.spritecollideany(point, scene_tiles, False)
            if scene_tile_selected and buttons[0] and current_option != None:
                update_screen_tile(scene_tile_selected, current_option.tile_id)
            elif scene_tile_selected and buttons[2] == 1:
                update_screen_tile(scene_tile_selected, "BLANK")
            
            if done_tile.rect.colliderect(pygame.Rect(pygame.mouse.get_pos(), (1,1))):                
                for x in range(config.SCREEN_WIDTH_TILES):
                    for y in range(config.SCREEN_HEIGHT_TILES):
                        if scene_data["tiles"][y][x] == "PLAYER":
                            scene_data["tiles"][y][x] = "BLANK"                            
                            scene_data["player_start"] = [x, y]

                with open(scene_file_path, "w") as scene_file:
                    json.dump(scene_data, scene_file, indent=4)
                exit()

                
                """
                    print("Open dialog")
                    app_window = tk.Tk()
                    #Tk().wm_withdraw() #to hide the main window
                    answer = simpledialog.askinteger("Input", "What is your age?",
                                        parent=app_window,
                                        minvalue=0, maxvalue=100)
                    app_window.destroy()
                    print("Answer is {}".format(answer))
                """
            

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
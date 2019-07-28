# Pygame sprite Example
import pygame
import random
import os
import json
import logging
import sys
import argparse
import config

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
TILE_OPTIONS_PER_ROW = 3
TILE_OPTIONS_SIZE = config.TILE_SIZE_PX + 20

config.SCREEN_WIDTH_PX = TILE_OPTIONS_X_OFFSET + TILE_OPTIONS_PER_ROW*TILE_OPTIONS_SIZE
config.SCREEN_HEIGHT_PX = config.SCREEN_HEIGHT_TILES*config.TILE_SIZE_PX

scene_data = {}
scene_file_path = os.path.join(config.scene_folder, args.scene_file)
if os.path.isfile(scene_file_path):
    with open(scene_file_path) as scene_file:
        scene_data = json.load(scene_file)
else:   
    scene_data = {}
    scene_data["tiles"] = [ [ "BLANK" for x in range( config.SCREEN_WIDTH_TILES ) ] for y in range( config.SCREEN_HEIGHT_TILES ) ]
    scene_data["player_start"] = [0,0]
    
# initialize pygame and create window
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((config.SCREEN_WIDTH_PX, config.SCREEN_HEIGHT_PX))
pygame.display.set_caption("My Game")
clock = pygame.time.Clock()

blank_tile = pygame.Surface((config.TILE_SIZE_PX, config.TILE_SIZE_PX))

player = None
tile_options = pygame.sprite.Group()
current_option = None

idx = 0
for tile_id, tile_data in config.tiles.items():
    print("Load tile {}".format(tile_id))
    tile = pygame.sprite.Sprite()
    tile.unselected_image = pygame.image.load(os.path.join(config.tile_folder, tile_data.filename)).convert_alpha()
    selected_image = pygame.image.load(os.path.join(config.tile_folder, tile_data.filename))
    pygame.draw.rect(selected_image, (255, 0, 0), (0,0,config.TILE_SIZE_PX,config.TILE_SIZE_PX), 2)
    tile.selected_image = selected_image
    tile.image = tile.unselected_image
    tile.tile_id = tile_id
    tile.rect = tile.image.get_rect()
    tile.rect.top = TILE_OPTIONS_Y_OFFSET + int(idx / TILE_OPTIONS_PER_ROW) * TILE_OPTIONS_SIZE
    tile.rect.left = TILE_OPTIONS_X_OFFSET + (idx % TILE_OPTIONS_PER_ROW) * TILE_OPTIONS_SIZE
    print("Placed tile at {}, {}, {}, {}".format(tile.rect.left, tile.rect.top, tile.rect.right, tile.rect.bottom))
    tile_options.add(tile)
    idx += 1

class Point(pygame.sprite.Sprite):
    def __init__(self, pos):
        super(pygame.sprite.Sprite, self).__init__()
        self.rect = pygame.Rect(pos[0], pos[1], 1, 1)

def update_screen_tile(tile, tile_id):
    if tile_id == "BLANK":
        print("Blank tile")
        tile.image = blank_tile.copy()
    else:
        print("not blank: {}".format(tile_id))
        for tile_option in tile_options:
            if tile_option.tile_id == tile_id:
                tile.image = tile_option.unselected_image.copy()   
    tile.rect = tile.image.get_rect()
    tile.rect.left = tile.x*config.TILE_SIZE_PX        
    tile.rect.top = tile.y*config.TILE_SIZE_PX        
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
done_tile.rect = tile.image.get_rect()
done_tile.rect.top = config.SCREEN_HEIGHT_PX - 100
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
        if event.type == pygame.MOUSEBUTTONDOWN:
            print("{}".format(event.button))
            point = Point(event.pos)
            option_selected = pygame.sprite.spritecollideany(Point(event.pos), tile_options, False)
            if option_selected:
                print("Hit option: {}".format(option_selected.tile_id))
                if current_option:
                    current_option.image = current_option.unselected_image
                current_option = option_selected
                option_selected.image = option_selected.selected_image
                 
            scene_tile_selected = pygame.sprite.spritecollideany(Point(event.pos), scene_tiles, False)
            if scene_tile_selected and event.button == 1 and current_option != None:
                update_screen_tile(scene_tile_selected, current_option.tile_id)
            elif scene_tile_selected and event.button == 3:
                update_screen_tile(scene_tile_selected, "BLANK")
            
            if pygame.sprite.spritecollide(Point(event.pos), done_group, False):
                with open(scene_file_path, "w") as scene_file:
                    json.dump(scene_data, scene_file)
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
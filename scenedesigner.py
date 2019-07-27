# Pygame sprite Example
import pygame
import random
import os
import json
import logging
import sys
import argparse

#logging.basicConfig(filename='platform.log', filemode='w', level=logging.DEBUG)
logging.basicConfig(level=logging.INFO, format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
module = sys.modules['__main__'].__file__
log = logging.getLogger(module)

parser = argparse.ArgumentParser(description='Platformgame scene designer')
parser.add_argument('scene_file', 
                     help='scene file to create or update')
args = parser.parse_args()
print("Scene file = {}".format(args.scene_file))

WIDTH = 10
HEIGHT = 10
TILE_SIZE = 70

TILE_OPTIONS_X_OFFSET = (WIDTH+2)*TILE_SIZE
TILE_OPTIONS_Y_OFFSET = 20
TILE_OPTIONS_PER_ROW = 3
TILE_OPTIONS_SIZE = TILE_SIZE + 20

SCREEN_WIDTH = TILE_OPTIONS_X_OFFSET + TILE_OPTIONS_PER_ROW*TILE_OPTIONS_SIZE
SCREEN_HEIGHT = HEIGHT*TILE_SIZE

FPS = 30

game_folder = os.path.dirname(__file__)
img_folder = os.path.join(game_folder, "images")
scene_folder = os.path.join(game_folder, "scenes")
tile_folder = os.path.join(img_folder, "Tiles")

scene_data = {}
scene_file_path = os.path.join(scene_folder, args.scene_file)
if os.path.isfile(scene_file_path):
    with open(scene_file_path) as scene_file:
        scene_data = json.load(scene_file)
else:   
    scene_data = {}
    scene_data["tiles"] = [ [ "BLANK" for x in range( WIDTH ) ] for y in range( HEIGHT ) ]
    scene_data["player_start"] = [0,0]
    
# initialize pygame and create window
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("My Game")
clock = pygame.time.Clock()

blank_tile = pygame.Surface((TILE_SIZE, TILE_SIZE))

player = None
tile_options = pygame.sprite.Group()
current_option = None

with open("platformdata.json") as data_file:
    data = json.load(data_file)
    for idx, tile_data in enumerate(data["tiles"]):
        print("Load tile {}".format(tile_data["id"]))
        tile = pygame.sprite.Sprite()
        tile.unselected_image = pygame.image.load(os.path.join(tile_folder, tile_data["filename"])).convert_alpha()
        selected_image = pygame.image.load(os.path.join(tile_folder, tile_data["filename"]))
        pygame.draw.rect(selected_image, (255, 0, 0), (0,0,TILE_SIZE,TILE_SIZE), 2)
        tile.selected_image = selected_image
        tile.image = tile.unselected_image
        tile.tile_id = tile_data["id"]
        tile.rect = tile.image.get_rect()
        tile.rect.top = TILE_OPTIONS_Y_OFFSET + int(idx / TILE_OPTIONS_PER_ROW) * TILE_OPTIONS_SIZE
        tile.rect.left = TILE_OPTIONS_X_OFFSET + (idx % TILE_OPTIONS_PER_ROW) * TILE_OPTIONS_SIZE
        print("Placed tile at {}, {}, {}, {}".format(tile.rect.left, tile.rect.top, tile.rect.right, tile.rect.bottom))
        tile_options.add(tile)

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
    tile.rect.left = tile.x*TILE_SIZE        
    tile.rect.top = tile.y*TILE_SIZE        
    scene_data["tiles"][tile.y][tile.x] = tile_id

scene_tiles = pygame.sprite.Group()
for x in range(WIDTH):
    for y in range(HEIGHT):
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
done_tile.rect.top = SCREEN_HEIGHT - 100
done_tile.rect.left = TILE_OPTIONS_X_OFFSET
done_group = pygame.sprite.Group()
done_group.add(done_tile)

# Game loop
running = True
while running:
    # keep loop running at the right speed
    clock.tick(FPS)
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
    for x in range(WIDTH):
        pygame.draw.line(screen, (100,100,100), [x*TILE_SIZE, 0], [x*TILE_SIZE,HEIGHT*TILE_SIZE], 1)
    for y in range(HEIGHT):
        pygame.draw.line(screen, (100,100,100), [0, y*TILE_SIZE], [WIDTH*TILE_SIZE,y*TILE_SIZE], 1)
   
    # *after* drawing everything, flip the display
    pygame.display.flip()

pygame.quit()
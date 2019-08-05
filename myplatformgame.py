# Pygame sprite Example
import config
import pygame
import random
import os
import json
import logging
import sys
from character import Player
from scene import Scene
import utils
import argparse
import time

#logging.basicConfig(filename='platform.log', filemode='w', level=logging.DEBUG)
logging.basicConfig(level=logging.ERROR, format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
module = sys.modules['__main__'].__file__
log = logging.getLogger(module)

parser = argparse.ArgumentParser(description='Platformgame')
parser.add_argument('initial_scene',
                    nargs='?', 
                    default=0,
                    type=int, 
                    help='scene to start on')
args = parser.parse_args()
print("Start on scene {}".format(args.initial_scene))

# Initialize pygame and create window
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((config.SCREEN_WIDTH_PX, config.SCREEN_HEIGHT_PX), flags=pygame.DOUBLEBUF)
pygame.display.set_caption("My Game")
clock = pygame.time.Clock()

# Load the tile data.  This doesn't feel like the right place, but hey...
for tile_id, tile in config.tiles.items():
    tile.image = utils.load_tile_image(tile)

# Load the scenes
scenes = []
current_scene = args.initial_scene
with os.scandir(config.scene_folder) as it:
    for entry in it:
        if entry.name.endswith(".json") and entry.is_file():
            scenes.append(Scene(entry.path, screen))

def next_scene(new_scene):
    global current_scene
    print ("Moving to scene {}".format(new_scene))
    if new_scene >= len(scenes):
        # Game over
        exit()
    player.start_scene(scenes[new_scene])
    scenes[current_scene].add_player(None)
    scenes[new_scene].add_player(player)
    current_scene = new_scene

# Create the player
player = Player()
player_group = pygame.sprite.Group()
player_group.add(player)
player.start_scene(scenes[current_scene])
scenes[current_scene].add_player(player)

# Game loop
running = True
while running:
    # Keep loop running at the right speed
    clock.tick(config.FPS)
    
    # Check whether we have any exit events and deal with them first
    if pygame.event.get(eventtype=config.REACHED_EXIT_EVENT_ID):
        pygame.time.wait(1000)
        next_scene(current_scene+1)

    # Check whether we have any dead events and deal with them first
    if pygame.event.get(eventtype=config.PLAYER_DEAD):
        pygame.time.wait(1000)
        utils.screen_spin(screen, angle=1440, time=2000, steps=180, shrink=True)
        next_scene(current_scene)

    for event in pygame.event.get():
        # check for closing window
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_n:
                next_scene(current_scene+1)
                continue
            scenes[current_scene].key_down(event)
        elif event.type == config.LOCK_TIMER_EVENT_ID:
            scenes[current_scene].timer_pop()

    # Update
    player_group.update()
    scenes[current_scene].update()

    # Draw / render
    screen.fill((0, 0, 0))
    scenes[current_scene].draw(screen)
    player_group.draw(screen)

    # *after* drawing everything, flip the display
    pygame.display.flip()

pygame.quit()

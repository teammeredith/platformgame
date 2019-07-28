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

#logging.basicConfig(filename='platform.log', filemode='w', level=logging.DEBUG)
logging.basicConfig(level=logging.ERROR, format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
module = sys.modules['__main__'].__file__
log = logging.getLogger(module)

# Initialize pygame and create window
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((config.SCREEN_WIDTH_PX, config.SCREEN_HEIGHT_PX))
pygame.display.set_caption("My Game")
clock = pygame.time.Clock()

# Load the tile data.  This doesn't feel like the right place, but hey...
for tile_id, tile in config.tiles.items():
    tile.image = pygame.image.load(os.path.join(config.tile_folder, tile.filename)).convert_alpha()

# Load the scenes
scenes = []
current_scene = 0
with os.scandir(config.scene_folder) as it:
    for entry in it:
        if entry.name.endswith(".json") and entry.is_file():
            scenes.append(Scene(entry.path))

def next_scene():
    global current_scene
    current_scene += 1
    print ("Moving to scene {}".format(current_scene))
    if current_scene >= len(scenes):
        # Game over
        exit()
    player.start_scene(scenes[current_scene])

# Create the player
player = Player()
player_group = pygame.sprite.Group()
player_group.add(player)
player.start_scene(scenes[current_scene])

# Game loop
running = True
while running:
    # Keep loop running at the right speed
    clock.tick(config.FPS)
    
    # Check whether we have any exit events and deal with them first
    if pygame.event.get(eventtype=config.REACHED_EXIT_EVENT_ID):
        next_scene()

    for event in pygame.event.get():
        # check for closing window
        if event.type == pygame.QUIT:
            running = False
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
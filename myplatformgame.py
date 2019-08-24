""" To do list 
- Think we're loading images here and in scenes.  Shouldn't do that.  Just load them in scenes?
- Make it so that button timers start again if you press the button whilst down
- Can embed yourself in a block by hitting an upsidedown spring
- Can't push a block when standing on a down button
- TNT block
- Add scenery -- moving clouds?  (Tried -- didn't work well)
- (Done) Make torches flicker
- (Done) Stop jumping whilst falling
- Commonize the code to move player and movable blocks...
- (Done) Make it possible to set initial player position
- (Done) Work out why the box can't fall through a 1x1 hole
- Fix the issue when a block gets moved on to a lock
- Add Red buttons that toggle things to flip flop
- (Done) Think about a mechanism to enable the case where you have to drop multiple blocks into a pile.  One block can push another?
-   Trial mechanism where you can only see part of the total scene?  
"""

# Pygame sprite Example
import config
import pygame
import random
import os
import json
import logging
from logging.handlers import RotatingFileHandler
import sys
from character import Player
from scene import Scene
import utils
import argparse
import time
import frame_timer

#logging.basicConfig(filename='platform.log', filemode='w', level=logging.DEBUG)
# logging.basicConfig(level=logging.ERROR, format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
log = logging.getLogger()
log.setLevel(logging.INFO)
handler = RotatingFileHandler("platform.log", maxBytes=200000, backupCount=10)
handler.doRollover()
formatter = logging.Formatter('%(asctime)s - %(filename)10.10s:%(lineno)4.4s - %(funcName)10.10s() - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)

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
    tile.image = utils.load_image(tile.path, tile.filename, tile.rotate)
    tile.animate_images = []
    for image_file in tile.animate_image_files:
        tile.animate_images.append(utils.load_image(tile.path, image_file, tile.rotate))
config.tiles["PLAIN"] = config.Tile("")
config.tiles["PLAIN"].animate_images = []

#background_image = utils.load_image(["backgrounds"], "background3-720.png", size=(config.SCREEN_WIDTH_PX, config.SCREEN_HEIGHT_PX))
spotlight_mask = utils.load_image([], "spotlight_mask.png", size=(config.SPOTLIGHT_RADIUS*2, config.SPOTLIGHT_RADIUS*2))
mask = pygame.Surface((config.SCREEN_WIDTH_PX, config.SCREEN_HEIGHT_PX), flags=pygame.SRCALPHA)

# Load the scenes
scenes = []
current_scene = args.initial_scene
with os.scandir(config.scene_folder) as it:
    for entry in it:
        if entry.name.endswith(".json") and entry.is_file():
            scenes.append(Scene(entry.path, screen))

def next_scene(new_scene):
    global current_scene
    frame_timer.frame_timer_del_all()
    print ("Moving to scene {}".format(new_scene))
    if new_scene >= len(scenes):
        # Game over
        exit()
    player.start_scene(scenes[new_scene])
    scenes[current_scene].add_player(None)
    scenes[new_scene].reset()
    scenes[new_scene].add_player(player)
    current_scene = new_scene

# Create the player
player = Player()
player_group = pygame.sprite.Group()
player_group.add(player)

# Associate the player and the first scene
player.start_scene(scenes[current_scene])
scenes[current_scene].add_player(player)

# Game loop
running = True
while running:
    log.debug("Main game loop")
    # Keep loop running at the right speed
    clock.tick(config.FPS)
    
    # Check whether we have any exit events and deal with them first
    if pygame.event.get(eventtype=config.REACHED_EXIT_EVENT_ID):
        pygame.time.wait(1000)
        next_scene(current_scene+1)

    # Check whether we have any dead events and deal with them first
    if pygame.event.get(eventtype=config.PLAYER_DEAD):
        log.info("Player dead event received")
        pygame.time.wait(1000)
        utils.screen_spin(screen, angle=1440, time=1000, steps=135, shrink=True)
        next_scene(current_scene)

    for event in pygame.event.get():
        # check for closing window
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_n:
                next_scene(current_scene+1)
                continue
            if event.key == pygame.K_ESCAPE:
                utils.screen_spin(screen, angle=1440, time=1000, steps=135, shrink=True)
                next_scene(current_scene)
                break
            if event.key == pygame.K_q:
                exit()
            scenes[current_scene].key_down(event)
        elif event.type == config.ROTATE_BOARD_EVENT_ID:
            scenes[current_scene].rotate()

    frame_timer.frame_timer_tick()

    # Update
    log.info("Update")
    player_group.update()
    scenes[current_scene].update()

    # Draw / render
    #screen.blit(background_image, (0,0))
    screen.fill((0,0,0))
    log.info("Draw")
    scenes[current_scene].draw(screen)
    player_group.draw(screen)

    if scenes[current_scene].dark:
        # Mask everything, except a circle around the player
        # Have the spotlight trail the player by a bit
        mask.fill((0,0,0,255))
        mask.blit(spotlight_mask, (player.rect.centerx - config.SPOTLIGHT_RADIUS, player.rect.centery - config.SPOTLIGHT_RADIUS), special_flags=pygame.BLEND_RGBA_MIN)
        screen.blit(mask, (0,0))

    # *after* drawing everything, flip the display
    pygame.display.flip()

pygame.quit()

# Pygame sprite Example
from globals import *
import pygame
import random
import os
import json
import logging
import sys
from character import *

#logging.basicConfig(filename='platform.log', filemode='w', level=logging.DEBUG)
logging.basicConfig(level=logging.ERROR, format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
module = sys.modules['__main__'].__file__
log = logging.getLogger(module)

game_folder = os.path.dirname(__file__)
img_folder = os.path.join(game_folder, "images")
scene_folder = os.path.join(game_folder, "scenes")
tile_folder = os.path.join(img_folder, "Tiles")

# initialize pygame and create window
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("My Game")
clock = pygame.time.Clock()

class Tile():
    def __init__(self, tile_data):
        self.image = pygame.image.load(os.path.join(tile_folder, tile_data["filename"])).convert_alpha()
        self.id = tile_data["id"]

with open("platformdata.json") as data_file:
    game_data = json.load(data_file)
    for tile_data in game_data["tiles"]:
        tiles[tile_data["id"]] = Tile(tile_data)


class Player(Character):
    # sprite for the Player
    def __init__(self):
        player_data = game_data["characters"]["PLAYER"]
        standing_image = pygame.transform.smoothscale(
                            pygame.image.load(
                                os.path.join(img_folder, 
                                             player_data["image_path"],
                                             player_data["standing_image"])).convert_alpha(), 
                            (70,70))
        walk_left_images = []
        walk_right_images = []
        for frame_image in player_data["walk_images"]:
            image = pygame.transform.smoothscale(
                        pygame.image.load(
                            os.path.join(img_folder, 
                                        player_data["image_path"],
                                        frame_image)).convert_alpha(), 
                        (70,70))
            walk_right_images.append(image)
            walk_left_images.append(pygame.transform.flip(image, True, False))

        Character.__init__(self, standing_image, walk_left_images, walk_right_images)
        self.max_step_height = 15
        self.slip_distance = 15
        self.move_speed = 10
        self.jump_speed = 25
        self.is_player = True
        self.tile_id = ""

    def check_for_key_press(self):    
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_RIGHT]:
            self.x_speed = self.move_speed
            self.walking = True
        elif pressed[pygame.K_LEFT]:
            self.x_speed = -self.move_speed
            self.walking = True
        else:
            self.x_speed = 0
            self.walking = False

        if pressed[pygame.K_SPACE] and not self.falling:
            self.falling = True
            self.y_speed = -self.jump_speed

    def collided(self, tile):
        if tile.tile_id == "EXIT":
            # We reached the exit
            next_scene()
            return
        log.debug("Collided with {}".format(tile.tile_id))

    def die(self):
        self.reset(scenes[current_scene].player_start)
"""
class Spider(Character):
    # sprite for the Player
    def __init__(self):
        standing_image = pygame.transform.smoothscale(pygame.image.load(os.path.join(img_folder, "Enemies\spider.png")).convert_alpha(), (30,30))
        walk_left_images = [pygame.transform.smoothscale(pygame.image.load(os.path.join(img_folder, "Enemies\spider_walk1.png")).convert_alpha(), (30,30)),
                            pygame.transform.smoothscale(pygame.image.load(os.path.join(img_folder, "Enemies\spider_walk2.png")).convert_alpha(), (30,30))]
        walk_right_images = walk_left_images

        Character.__init__(self, standing_image, walk_left_images, walk_right_images)
        self.max_step_height = 1
        self.slip_distance = 15
        self.move_speed = 10
        self.jump_speed = 25

    def reset(self, pos):
        Character.reset(self, pos)
        self.x_speed = 3

    def on_hit_x(self):
        self.x_speed = -self.x_speed
        print("Hit overridden on hit")
"""

class Scene():
    def __init__(self, scene_file_path):
        with open(scene_file_path, "r") as scene_file:
            self.scene_data = json.load(scene_file)
            self.player_start = (self.scene_data["player_start"][0], self.scene_data["player_start"][1]) 
            self.open_locks = []

            # Create the platform sprites
            self.platform_sprites = pygame.sprite.Group()
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    tile_id = self.scene_data["tiles"][y][x]                    
                    """if tile_id == "SPIDER":
                        spider = Spider()
                        spider.tile_id = "SPIDER"
                        spider.reset((x, y))
                        self.platform_sprites.add(spider)
                    elif """
                    if tile_id != "BLANK":
                        tile = pygame.sprite.Sprite()
                        tile.image = tiles[tile_id].image
                        tile.tile_id = tile_id
                        tile.rect = tile.image.get_rect()
                        tile.rect.top = TILE_SIZE*y
                        tile.rect.left = TILE_SIZE*x
                        self.platform_sprites.add(tile)
    
    def test_collision(self, sprite):
        for test_sprite in self.platform_sprites:
            if sprite != test_sprite and pygame.sprite.collide_rect(sprite, test_sprite) and pygame.sprite.collide_mask(sprite, test_sprite):
                return test_sprite
        if sprite != player and pygame.sprite.collide_mask(player, sprite):
            return player

        return None

    def update(self):
        self.platform_sprites.update()

    def animate_spring(self, tile):
        if tile.tile_id == "SPRING_UP":
            tile.image = tiles["SPRING_DN"].image
            tile.tile_id = "SPRING_DN"
        else:
            tile.image = tiles["SPRING_UP"].image
            tile.tile_id = "SPRING_UP"

    def hit_button(self, tile):
        if tile.tile_id == "BUTTON_YELLOW":
            tile.image = tiles["BUTTON_YELLOW_DN"].image
            tile.tile_id = "BUTTON_YELLOW_DN"
        for sprite in self.platform_sprites:
            if sprite.tile_id == "LOCK_YELLOW":
                sprite.remove(self.platform_sprites)
                self.open_locks.append(sprite)
                pygame.time.set_timer(LOCK_TIMER_EVENT_ID, 4000)

    def draw(self, screen):
        self.platform_sprites.draw(screen)

    def timer_pop(self):
        log.info("Timer pop")
        for sprite in self.open_locks:
            self.platform_sprites.add(sprite)
            if pygame.sprite.collide_mask(sprite, player):
                player.die()

        for tile in self.platform_sprites:
            if tile.tile_id == "BUTTON_YELLOW_DN":
                tile.image = tiles["BUTTON_YELLOW"].image
                tile.tile_id = "BUTTON_YELLOW"
                if pygame.sprite.collide_mask(tile, player):
                    self.hit_button(tile)


with os.scandir(scene_folder) as it:
    for entry in it:
        if entry.name.endswith(".json") and entry.is_file():
            scenes.append(Scene(entry.path))

def next_scene():
    global current_scene
    global player

    current_scene += 1
    if current_scene >= len(scenes):
        # Game over
        exit()
    player.reset(scenes[current_scene].player_start)

player = Player()
player_group = pygame.sprite.Group()
player_group.add(player)
player.reset(scenes[current_scene].player_start)

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
        if event.type == LOCK_TIMER_EVENT_ID:
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
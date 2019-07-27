# Pygame sprite Example
import pygame
import random
import os
import json
import logging
import sys

#logging.basicConfig(filename='platform.log', filemode='w', level=logging.DEBUG)
logging.basicConfig(level=logging.ERROR, format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
module = sys.modules['__main__'].__file__
log = logging.getLogger(module)

WIDTH = 10
HEIGHT = 10
TILE_SIZE = 70
SCREEN_WIDTH = WIDTH*TILE_SIZE
SCREEN_HEIGHT = HEIGHT*TILE_SIZE

FPS = 30

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

tiles = {}
with open("platformdata.json") as data_file:
    data = json.load(data_file)
    for tile_data in data["tiles"]:
        print("tile_data = {}".format(tile_data))
        tiles[tile_data["id"]] = Tile(tile_data)

current_scene = 0
scenes = []

class Character(pygame.sprite.Sprite):
    # sprite for the Player
    def __init__(self, standing_image, walk_left_images, walk_right_images):
        pygame.sprite.Sprite.__init__(self)
        self.walk_right_images = walk_right_images
        self.walk_left_images = walk_left_images
        self.standing_image = standing_image
        self.image = self.standing_image
        self.mask = pygame.mask.from_surface(standing_image)
        self.rect = self.image.get_rect()
        self.reset((0,0))
        self.is_player = False

    def reset(self, pos):
        self.walking = False
        self.rect.left = pos[0]*TILE_SIZE
        self.rect.top = pos[1]*TILE_SIZE
        self.y_speed = 0
        self.x_speed = 0
        self.falling = True
        self.walk_index = 0
    
    def animate(self):
        # Change the character's image if we need to
        if self.x_speed != 0:
            self.walk_index = (self.walk_index+1)%len(self.walk_right_images)
            if self.x_speed > 0:
                self.image = self.walk_right_images[self.walk_index]
            else:
                self.image = self.walk_left_images[self.walk_index]
        else:
            self.walk_index = 0
            self.image = self.standing_image

    def collide_with_any_tile(self):
        # Check whether the player has collided with any tile.  If they have, return the Tile.  
        # Otherwise return None
        return scenes[current_scene].test_collision(self)

    def check_for_key_press(self):    
        pass

    def on_hit_x(self):
        self.x_speed = 0

    def update(self):
        # Called every frame
        self.check_for_key_press()

        #log.debug("pos = {}, {}".format(self.rect.left, self.rect.top))
        #log.debug("speed = {}, {}".format(self.x_speed, self.y_speed))

        old_center = self.rect.center

        if self.x_speed != 0:
            move_dir = (1 if self.x_speed > 0 else -1)
            step_height_remaining = self.max_step_height
            # Try and move in the x direction
            for i in range(abs(self.x_speed)):
                log.debug("Current pos = {}, {}".format(self.rect.left, self.rect.top))
                self.rect.left += move_dir
                if self.rect.right > SCREEN_WIDTH:
                    self.rect.right = SCREEN_WIDTH
                    self.on_hit_x()
                elif self.rect.left < 0:
                    self.rect.left = 0                    
                    self.on_hit_x()

                collided = self.collide_with_any_tile()
                if collided:
                    if collided.tile_id == "EXIT" and self.is_player:
                        # We reached the exit
                        next_scene()
                        return
                    log.debug("Collided with {}".format(collided.tile_id))
                    # Is this something that we can go over?
                    if self.y_speed == 0:
                        over = False
                        old_top = self.rect.top
                        for step in range(step_height_remaining):
                            log.debug("Step up")
                            self.rect.top -= 1
                            if not self.collide_with_any_tile():
                                log.info("Made it over")
                                over = True
                                break
                        if over:
                            step_height_remaining -= (step+1)
                            continue
                        self.rect.top = old_top
                    # We've moved as far as we can
                    self.rect.left -= move_dir
                    self.on_hit_x()
                    break
                    # if we went over something?  self.y_speed = -1

        # Apply gravity.  We start slow 'cos that makes it more efficient when we're just standing on something...
        if self.y_speed == 0:
            self.y_speed = 1
        else:
            self.y_speed += 2

        move_dir = (1 if self.y_speed > 0 else -1)
        slip_remaining = self.slip_distance
        for i in range(abs(self.y_speed)):
            self.rect.bottom += move_dir
            collided = self.collide_with_any_tile()
            if collided:
                if collided.tile_id == "EXIT" and self.is_player:
                    next_scene()
                    return
                elif self.y_speed > 5 and collided.tile_id == "SPRING_UP":
                    log.info("Hit SPRING_UP.  y_speed = {}".format(self.y_speed))
                    scenes[current_scene].animate_spring(collided)
                    self.y_speed = min(self.y_speed, 10)
                    break
                elif collided.tile_id == "SPRING_DN":
                    log.info("Hit SPRING_DOWN")
                    scenes[current_scene].animate_spring(collided)
                    self.rect.top -= 30
                    self.y_speed = -40
                    break
                elif move_dir == 1 and self.x_speed == 0:
                    orig_left = self.rect.left
                    # Check if we can slip off whatever we've hit
                    slipped = False
                    for slip in range(slip_remaining):
                        for try_pos in (orig_left - slip, orig_left + slip):                        
                            self.rect.left = try_pos
                            if not self.collide_with_any_tile():
                                log.info("Slipped off")
                                slipped = True
                                break
                        if slipped:
                            slip_remaining -= (slip+1)
                            break
                    if slipped:
                        continue 
                    else:
                        self.rect.left = orig_left       
                if move_dir == 1:
                    self.falling = False
                self.y_speed = 0
                self.rect.bottom -= move_dir                

        """
        elif self.y_speed < 0:
            # We're going up.  Check if we've hit our head.
            for tile in platform_sprites:
                if pygame.sprite.collide_rect(self, tile) and pygame.sprite.collide_mask(self, tile):
                    print("Hit head")
                    self.rect.bottom = old_bottom
                    self.y_speed = 0
        """

            
        if old_center != self.rect.center:
            log.info("New pos = {}, {}".format(self.rect.left, self.rect.top))
            log.info("Current speed = {}, {}".format(self.x_speed, self.y_speed))

        self.animate()

class Player(Character):
    # sprite for the Player
    def __init__(self):
        standing_image = pygame.transform.smoothscale(pygame.image.load(os.path.join(img_folder, "Player\p3_front.png")).convert_alpha(), (70,70))
        walk_left_images = []
        walk_right_images = []
        for i in range(11):
            image = pygame.transform.smoothscale(pygame.image.load(os.path.join(img_folder, "Player\p3_walk\PNG\p3_walk{0:02d}.png".format(i+1))).convert_alpha(), (70,70))
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


class Scene():
    def __init__(self, scene_file_path):
        with open(scene_file_path, "r") as scene_file:
            self.scene_data = json.load(scene_file)
            self.player_start = (self.scene_data["player_start"][0], self.scene_data["player_start"][1]) 

            # Create the platform sprites
            self.platform_sprites = pygame.sprite.Group()
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    tile_id = self.scene_data["tiles"][y][x]
                    if tile_id == "SPIDER":
                        spider = Spider()
                        spider.tile_id = "SPIDER"
                        spider.reset((x, y))
                        self.platform_sprites.add(spider)
                    elif tile_id != "BLANK":
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

    def draw(self, screen):
        self.platform_sprites.draw(screen)

with os.scandir(scene_folder) as it:
    for entry in it:
        if entry.name.endswith(".json") and entry.is_file():
            scenes.append(Scene(entry.path))

current_scene = 0

def next_scene():
    global current_scene
    global player

    current_scene += 1
    if current_scene >= len(scenes):
        # Game over
        exit()
    player.reset(scenes[current_scene].player_start)

#ToDo: refactor scene into scene class including e.g. player start location

player = Player()
player_group = pygame.sprite.Group()
player_group.add(player)

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
import config
import pygame
import logging
import sys
import os
import utils
from enum import Enum
from movable import Movable, MovableRC

log = logging.getLogger()


class Character(Movable):
    # sprite for the Player
    def __init__(self, standing_image, walk_left_images, walk_right_images):
        Movable.__init__(self, standing_image)
        self.walk_right_images = walk_right_images
        self.walk_left_images = walk_left_images
        self.standing_image = standing_image
        self.is_player = False
        self.dead = False

    def start_scene(self, scene, initial_left, initial_top): 
        Movable.start_scene(self, scene, initial_left, initial_top)
        self.walking = False
        self.walk_index = 0
        self.dead = False
    
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

    def check_for_key_press(self):    
        pass

    def update(self):

        if self.dead:
            return

        # Called every frame
        self.check_for_key_press()

        rc = Movable.update(self)
        if rc == MovableRC.FELL_OFF_SCREEN:
            self.die()
        elif not rc == MovableRC.STOP:
            self.animate()


class Player(Character):
    # sprite for the Player
    def __init__(self):
        player_data = config.characters["PLAYER"]
        standing_image = utils.load_image(player_data.image_path, player_data.standing_image)
        walk_left_images = []
        walk_right_images = []
        for frame_image in player_data.walk_images:
            image = utils.load_image(player_data.image_path, frame_image)
            walk_right_images.append(image)
            walk_left_images.append(pygame.transform.flip(image, True, False))

        Character.__init__(self, standing_image, walk_left_images, walk_right_images)
        self.is_player = True
        self.tile_id = ""
        self.reorient_on_rotation = False

        self.dead_image = utils.load_image(player_data.image_path, player_data.dead_image)

    def check_for_key_press(self):
        if self.rotating:
            return    
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
            log.info("Jump")
            self.falling = True
            self.y_speed = -self.jump_speed

    # See comment on parent class
    def act_on_collision(self, tile):
        log.debug("Collided with {}".format(tile.tile_id))
        self.rotating = False
        if tile.kill:
            self.die()
            return MovableRC.STOP
        if tile.tile_id == "EXIT":
            print("Posting exit event")
            self.scene = None
            pygame.event.post(pygame.event.Event(config.REACHED_EXIT_EVENT_ID))
            return MovableRC.STOP
        if tile.tile_id == "SPIN":
            self.y_speed = 0
            self.last_collided = None # Make sure we don't hit spin again after it's been deleted
            self.scene.spin_activated(tile)
            return MovableRC.STOP
        if self.y_speed > config.SPRING_ACTIVE_SPEED and tile.spring and tile.state == 0 and tile.rotation_enabled:
            log.info("Hit SPRING_UP.  y_speed = {}".format(self.y_speed))
            self.scene.animate_spring(tile)
            self.y_speed = min(self.y_speed, 10)
            self.falling = True 
            return MovableRC.STOP
        elif self.y_speed > config.SPRING_ACTIVE_SPEED and tile.spring and tile.state == 1 and tile.rotation_enabled:
            log.info("Hit SPRING_DOWN")
            self.scene.animate_spring(tile)
            # ToDo.  This is a nasty hack to avoid the tile springing back and overlapping the sprite.
            self.rect.top -= int(config.TILE_SIZE_PX)/2
            self.y_speed = -1 * config.SPRING_JUMP_SPEED
            return MovableRC.STOP
        elif self.y_speed > config.SPRING_ACTIVE_SPEED and tile.button:
            log.info("Hit button.  y_speed = {}".format(self.y_speed))
            self.scene.hit_button(tile)
            self.y_speed = min(self.y_speed, 10)
            return MovableRC.CONTINUE
        return MovableRC.CONTINUE

    def die(self):
        self.dead = True
        self.image = self.dead_image
        pygame.event.post(pygame.event.Event(config.PLAYER_DEAD))

    def start_scene(self, scene):
        Character.start_scene(self, scene, scene.player_start[0] * config.TILE_SIZE_PX, scene.player_start[1] * config.TILE_SIZE_PX)

"""
class Spider(Character):
    # sprite for the Player
    def __init__(self):
        standing_image = pygame.transform.smoothscale(pygame.image.load(os.path.join(config.img_folder, "Enemies\spider.png")).convert_alpha(), (30,30))
        walk_left_images = [pygame.transform.smoothscale(pygame.image.load(os.path.join(config.img_folder, "Enemies\spider_walk1.png")).convert_alpha(), (30,30)),
                            pygame.transform.smoothscale(pygame.image.load(os.path.join(config.img_folder, "Enemies\spider_walk2.png")).convert_alpha(), (30,30))]
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

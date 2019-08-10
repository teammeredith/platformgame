import config
import pygame
import logging
import sys
import os
import utils
from enum import Enum

#logging.basicConfig(filename='platform.log', filemode='w', level=logging.DEBUG)
logging.basicConfig(level=logging.ERROR, format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
module = sys.modules['__main__'].__file__
log = logging.getLogger(module)

class CollideRC(Enum):
    CONTINUE = 1
    STOP = 2 

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
        self.scene = None
        self.is_player = False
        self.rotating = True
        self.dead = False
        self.max_step_height = config.MAX_STEP_HEIGHT
        self.slip_distance = config.SLIP_DISTANCE
        self.move_speed = config.MOVE_SPEED
        self.jump_speed = config.JUMP_SPEED
        self.last_collided = None

    def start_scene(self, scene): 
        self.scene = scene
        self.scene.reset()
        self.walking = False
        self.rect.left = scene.player_start[0] * config.TILE_SIZE_PX
        self.rect.top = scene.player_start[1] * config.TILE_SIZE_PX
        self.y_speed = 0
        self.x_speed = 0
        self.falling = True
        self.walk_index = 0
        self.dead = False
        self.last_collided = None
    
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

    def collide_with_any_tile(self, sprite=None):
        # Check whether the player has collided with any tile.  If they have, return the Tile.  
        # Otherwise return None
        if self.scene:
            return self.scene.test_collision(self)
        return False

    def check_for_key_press(self):    
        pass

    # Override this function to e.g. make a character that walks back and forth bouncing when it hits an object
    def on_stopped_x(self):
        self.x_speed = 0

    # Called every time the character makes contact with a tile -- even if e.g. they are going to slip off it / walk over it
    # Override to check for e.g. contact with spikes or the exit.
    # Returns one of CollideRC
    # - CONTINUE: We will continue as normal, including stopping, stepping over or slipping off the thing we've hit as appropriate
    # - STOP:     The player will be halted in their tracks.  We will undo the move that caused the collision, but won't do any more 
    #             motion processing for this frame.  act_on_collision can and should update any player attributes that need to be 
    #             updated as a result of the collision, such as self.rotating, self.falling, or self.y_speed.  
    def act_on_collision(self, tile):
        self.rotating = False
        return CollideRC.CONTINUE

    def board_rotate(self):
        self.rect.right, self.rect.bottom = config.SCREEN_WIDTH_PX - self.rect.left, config.SCREEN_HEIGHT_PX - self.rect.top 
        self.x_speed = 0
        self.rotating = True

    def change_x(self, increment):
        self.rect.left += increment
        if self.rect.right > config.SCREEN_WIDTH_PX:
            self.rect.right = config.SCREEN_WIDTH_PX
            return False
        elif self.rect.left < 0:
            self.rect.left = 0                    
            return False
        return True

    def update(self):

        if not self.scene or self.dead:
            return

        # Called every frame
        self.check_for_key_press()

        #log.debug("pos = {}, {}".format(self.rect.left, self.rect.top))
        #log.debug("speed = {}, {}".format(self.x_speed, self.y_speed))

        old_center = self.rect.center

        # Logic here is:
        # - Try to move in the x-direction.  If we hit something, can we go over it?
        # - Apply gravity
        # - Try to move in the y-direction.  If we hit something, should we slip off it?
        # - Animate the character image
        if self.x_speed != 0:
            move_dir = (1 if self.x_speed > 0 else -1)
            step_height_remaining = self.max_step_height
            
            # Try and move in the x direction
            for i in range(abs(self.x_speed)):
                log.debug("Current pos = {}, {}".format(self.rect.left, self.rect.top))

                # Update our x-position enforcing screen bounds
                if not self.change_x(move_dir):
                    # We hit the edge of the screen
                    self.on_stopped_x()
                    break

                collided = self.collide_with_any_tile()
                if not collided:
                    # We're good.  Try to move again.
                    continue

                if self.act_on_collision(collided) == CollideRC.STOP:
                    # Immediate stop.  Undo the move and return.  Don't try and move any further.
                    log.debug("act_on_collision -> stop")
                    self.rect.left -= move_dir
                    return 
                log.debug("try to move tile {}".format(collided.tile_id))

                if self.scene.try_to_move_tile(collided, move_dir):
                    log.info("Collided with {}".format(collided.tile_id))
                    # We moved the thing we hit, but it's possible we were colliding with multiple objects.  So undo this move, 
                    # but keep trying to move further.   This will also have the effect of slowing us down which is nice.
                    self.rect.left -= move_dir
                    continue

                # Is this something that we can go over?
                if True: #self.y_speed == 0:
                    over = False
                    old_top = self.rect.top
                    for step in range(step_height_remaining):
                        log.debug("Step up")
                        self.rect.top -= 1
                        collided_on_push = self.collide_with_any_tile() 
                        if not collided_on_push:
                            log.info("Made it over")
                            over = True
                            break
                        elif collided_on_push != collided:
                            log.debug("Now colliding with {}".format(collided_on_push.tile_id))

                            # We're now colliding with something different.  Maybe we can push that?
                            # ToDo: really ought to iterate through everything that we are colliding with and try to push it 
                            if self.scene.try_to_move_tile(collided_on_push, move_dir):
                                log.debug("Moved tile")
                                # Has that solved the issue?
                                if not self.collide_with_any_tile():
                                    log.info("Made it over")
                                    over = True
                                    break

                    if over:
                        step_height_remaining -= (step+1)
                        continue
                    self.rect.top = old_top

                # If we get here we must have hit something that we couldn't move or go over.  Undo the move and stop trying to 
                # change our x position.
                self.rect.left -= move_dir
                self.on_stopped_x()
                break

        # Apply gravity.  
        self.y_speed = min(config.TERMINAL_VELOCITY, self.y_speed + config.GRAVITY_EFFECT)

        # Try to move in the y-direction.
        move_dir = (1 if self.y_speed > 0 else -1)
        slip_remaining = self.slip_distance
        for i in range(abs(self.y_speed)):
            self.rect.bottom += move_dir

            # Check if we fall off the bottom or top of the screen
            if self.rect.top > config.SCREEN_HEIGHT_PX:
                self.die()
                return
            elif self.rect.top < 0:
                self.rect.top = 0                    
                self.y_speed = 0
                break

            collided = self.collide_with_any_tile()
            if collided:
                if self.act_on_collision(collided) == CollideRC.STOP:
                    # Don't try and move any further.
                    self.rect.bottom -= move_dir
                    return 
                elif self.x_speed == 0:
                    # See if we should slip past whatever we've hit
                    slip_distance = utils.try_to_slip_sprite(self, slip_remaining, self.collide_with_any_tile)
                    if slip_distance:
                        # We successfully slipped off
                        slip_remaining -= slip_distance
                        continue 
                
                #  We've hit something and not slipped past it
                if move_dir == 1:
                    self.falling = False
                    
                self.y_speed = 0
                self.rect.bottom -= move_dir
                break                
            else:
                # We didn't hit anything...
                self.falling = True

        if old_center != self.rect.center:
            log.info("New pos = {}, {}".format(self.rect.left, self.rect.top))
            log.info("Current speed = {}, {}".format(self.x_speed, self.y_speed))

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
            return CollideRC.STOP
        if tile.tile_id == "EXIT":
            print("Posting exit event")
            self.scene = None
            pygame.event.post(pygame.event.Event(config.REACHED_EXIT_EVENT_ID))
            return CollideRC.STOP
        if tile.tile_id == "SPIN":
            self.y_speed = 0
            self.scene.spin_activated(tile)
            return CollideRC.STOP
        if self.y_speed > config.SPRING_ACTIVE_SPEED and tile.spring and tile.state == 0 and tile.rotation_enabled:
            log.info("Hit SPRING_UP.  y_speed = {}".format(self.y_speed))
            self.scene.animate_spring(tile)
            self.y_speed = min(self.y_speed, 10)
            self.falling = True 
            return CollideRC.STOP
        elif self.y_speed > config.SPRING_ACTIVE_SPEED and tile.spring and tile.state == 1 and tile.rotation_enabled:
            log.info("Hit SPRING_DOWN")
            self.scene.animate_spring(tile)
            # ToDo.  This is a nasty hack to avoid the tile springing back and overlapping the sprite.
            self.rect.top -= int(config.TILE_SIZE_PX)/2
            self.y_speed = -1 * config.SPRING_JUMP_SPEED
            return CollideRC.STOP
        elif self.y_speed > config.SPRING_ACTIVE_SPEED and tile.button:
            log.info("Hit button.  y_speed = {}".format(self.y_speed))
            self.scene.hit_button(tile)
            self.y_speed = min(self.y_speed, 10)
            return CollideRC.CONTINUE
        return CollideRC.CONTINUE

    def die(self):
        self.dead = True
        self.image = self.dead_image
        pygame.event.post(pygame.event.Event(config.PLAYER_DEAD))

    def start_scene(self, scene):
        Character.start_scene(self, scene)

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

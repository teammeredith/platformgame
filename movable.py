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

class MovableRC(Enum):
    CONTINUE = 1
    STOP = 2 
    FELL_OFF_SCREEN = 3
    HIT_EDGE_OF_SCREEN = 4

class Movable(pygame.sprite.Sprite):
    def __init__(self, image):
        pygame.sprite.Sprite.__init__(self)
        self.image = image
        self.mask = pygame.mask.from_surface(self.image)
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
        self.gravity_effect = config.GRAVITY_EFFECT

    def start_scene(self, scene, initial_left, initial_top): 
        self.scene = scene
        self.rect.left = initial_left
        self.rect.top = initial_top
        self.y_speed = 0
        self.x_speed = 0
        self.falling = True
        self.last_collided = None
    
    def collide_with_any_tile(self, sprite=None):
        # Check whether we have collided with any tile.  If we have, return the Tile.  
        # Otherwise return None
        if self.scene:
            return self.scene.test_collision(self)
        return False

    # Override this function to e.g. make a character that walks back and forth bouncing when it hits an object
    def on_stopped_x(self):
        self.x_speed = 0

    # Called every time the character makes contact with a tile -- even if e.g. they are going to slip off it / walk over it
    # Override to check for e.g. contact with spikes or the exit.
    # Returns one of MovableRC
    # - CONTINUE: We will continue as normal, including stopping, stepping over or slipping off the thing we've hit as appropriate
    # - STOP:     The player will be halted in their tracks.  We will undo the move that caused the collision, but won't do any more 
    #             motion processing for this frame.  act_on_collision can and should update any player attributes that need to be 
    #             updated as a result of the collision, such as self.rotating, self.falling, or self.y_speed.  
    def act_on_collision(self, tile):
        self.rotating = False
        return MovableRC.CONTINUE

    def board_rotate(self):
        self.rect.right, self.rect.bottom = config.SCREEN_WIDTH_PX - self.rect.left, config.SCREEN_HEIGHT_PX - self.rect.top 
        self.x_speed = 0
        self.rotating = True

    def try_to_move(self, x_speed = 0, y_speed = 0):
        initial_center = self.rect.center
        if x_speed:
            self.rect.left += x_speed
            if self.rect.left < 0:
                self.rect.left = 0
                return MovableRC.HIT_EDGE_OF_SCREEN, None
            if self.rect.right > config.SCREEN_WIDTH_PX:
                self.rect.right = config.SCREEN_WIDTH_PX
                return MovableRC.HIT_EDGE_OF_SCREEN, None
        else:
            self.rect.top += y_speed
            
        collided = self.collide_with_any_tile() 
        if collided:
            #  Hit something.  Check whether we can move whatever we've hit too.
            if isinstance(collided, Movable) and collided.try_to_move(x_speed = x_speed, y_speed = y_speed) == MovableRC.CONTINUE:
                # The thing we hit moved.  Check whether we're not collision free.
                collided = collide_with_any_tile()
                if not collided:
                    return MovableRC.CONTINUE, None

            self.rect.center = initial_center
            return MovableRC.STOP, collided
        return MovableRC.CONTINUE, None

    def update(self):

        if not self.scene:
            return None

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

                # Try to update our X position.  This will try to push anything that we hit.
                rc, collided = self.try_to_move(x_speed = move_dir)
                if rc == MovableRC.HIT_EDGE_OF_SCREEN:
                    # We hit the edge of the screen
                    self.on_stopped_x()
                    break

                if rc == MovableRC.CONTINUE:
                    # We're good.  Try to move again.
                    continue

                if self.act_on_collision(collided) == MovableRC.STOP:
                    # Immediate stop.  Undo the move and return.  Don't try and move any further.
                    log.debug("act_on_collision -> stop")
                    return MovableRC.STOP

                # Is this something that we can go over?
                if True: #self.y_speed == 0:
                    over = False
                    old_top = self.rect.top
                    for step in range(step_height_remaining):
                        log.debug("Step up")
                        self.rect.top -= 1
                        collided_on_step = self.collide_with_any_tile() 
                        if not collided_on_step:
                            log.info("Made it over")
                            over = True
                            break
                        elif collided_on_step != collided:
                            log.debug("Now colliding with {}".format(collided_on_step.tile_id))

                            # We're now colliding with something different.  Maybe we can push that?
                            # ToDo: really ought to iterate through everything that we are colliding with and try to push it 
                            if isinstance(collided_on_push, Movable) and collided_on_push.try_to_move(x_speed = move_dir):
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
        self.y_speed = min(config.TERMINAL_VELOCITY, self.y_speed + self.gravity_effect)

        # Try to move in the y-direction.
        move_dir = (1 if self.y_speed > 0 else -1)
        slip_remaining = self.slip_distance
        for i in range(abs(self.y_speed)):
            self.rect.bottom += move_dir

            # Check if we fall off the screen
            if self.rect.top > config.SCREEN_HEIGHT_PX:
                return MovableRC.FELL_OFF_SCREEN
            
            """elif self.rect.top < 0:
                self.rect.top = 0                    
                self.y_speed = 0
                break"""

            collided = self.collide_with_any_tile()
            if collided:
                if self.act_on_collision(collided) == MovableRC.STOP:
                    # Don't try and move any further.
                    self.rect.bottom -= move_dir
                    return MovableRC.STOP
                elif self.scene.try_to_move_tile(collided, y_speed = move_dir):
                    self.rect.bottom -= move_dir
                    continue
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

        return None

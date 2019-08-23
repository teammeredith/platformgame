import config
import pygame
import logging
import sys
import os
import utils
from enum import Enum

#logging.basicConfig(filename='platform.log', filemode='w', level=logging.DEBUG)
#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
log = logging.getLogger()

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
        self.step_height_remaining = 0
        self.slip_remaining = 0

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

    # Tries to move us either +/- 1 in the x_direction or +/- 1 in the y_direction.
    # Returns one of:
    # - STOP.  We've hit something. Will have called act_on_collision and will have undone the move.  The caller shouldn't
    #          try to move this sprite again this frame.
    # - HIT_EDGE_OF_SCREEN.  Will have undone the move.
    # - FELL_OFF_SCREEN.  We fell off the bottom of the screen.
    # - CONTINUE.  We've moved successfully (or pushed something that will allow us to move successfully if called again)
    def try_to_move(self, x_speed = 0, y_speed = 0, already_moved=None):
        log.debug("Try to move {} {}. x_s = {} y_s = {} pos = {}".format(self.tile_id, self, x_speed, y_speed, self.rect.center))

        # We call ourselves recursively, recording the list of objects that have been moved as a result.      
        if not already_moved:
            already_moved = []
            top_level_move = True
        else:
            top_level_move = False

        if self in already_moved:
            # Avoid perpetual motion where we push something that pushes us which we push etc.  That's bad.
            return MovableRC.STOP

        already_moved.append(self)

        initial_center = self.rect.center

        # Update our position based on the direction we're trying to move
        if x_speed:
            self.rect.left += x_speed
            if self.rect.left < 0:
                self.rect.left = 0
                self.on_stopped_x()
                return MovableRC.HIT_EDGE_OF_SCREEN
            if self.rect.right > config.SCREEN_WIDTH_PX:
                self.rect.right = config.SCREEN_WIDTH_PX
                self.on_stopped_x()
                return MovableRC.HIT_EDGE_OF_SCREEN
        else:
            self.rect.top += y_speed
            if self.rect.top > config.SCREEN_HEIGHT_PX:
                return MovableRC.FELL_OFF_SCREEN
        
        # Did we collide with anything?
        collided = self.collide_with_any_tile() 
        if not collided:
            if self.y_speed:
                self.falling = True
            return MovableRC.CONTINUE

        # We've hit something.  
        # - Call act_on_collision.  This determines whether we should continue trying to move, or whether we should stop.
        log.debug("{} hit {} {}".format(self.tile_id, collided.tile_id, collided))
        pre_action_center = self.rect.center
        if self.act_on_collision(collided) == MovableRC.STOP:
            # Immediate stop.  Return.  Don't try and move any further.
            log.debug("act_on_collision -> stop")
            if pre_action_center == self.rect.center:
                # Act on action didn't move us -- undo the move 
                self.rect.center = initial_center
            return MovableRC.STOP

        #  Hit something.  Check whether we can move whatever we've hit too.
        while collided:
            if isinstance(collided, Movable) and collided.try_to_move(x_speed = x_speed, y_speed = y_speed, already_moved = already_moved) == MovableRC.CONTINUE:
                log.debug("{} moved {}".format(self.tile_id, collided.tile_id))
                # The thing we hit moved.  Check whether we're now collision free.
                collided = self.collide_with_any_tile()
            else:
                log.debug("{} couldn't move {}".format(self.tile_id, collided.tile_id))
                # We hit something that we couldn't move.
                break

        if not collided:
            # We are now collision free.  If we're the one actually initiating the move then undo it anyway in order to slow us down when we're pushing things.
            if top_level_move: 
                self.rect.center = initial_center
            return MovableRC.CONTINUE

        # We've hit something that we can't move.  If we're trying to go sideways, see if we can step over it.
        if x_speed:
            over = False
            for step in range(self.step_height_remaining):
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
                    if isinstance(collided_on_step, Movable) and collided_on_step.try_to_move(x_speed = x_speed, already_moved = already_moved) == MovableRC.CONTINUE:
                        log.debug("Moved tile")
                        # Has that solved the issue?
                        if not self.collide_with_any_tile():
                            log.info("Made it over")
                            over = True
                            break

            if over:
                self.step_height_remaining -= (step+1)
                return MovableRC.CONTINUE
            
            # We've hit something that we can't move and we can't go over.  We're out of options.
            self.rect.center = initial_center
            return MovableRC.STOP

        if y_speed:
            if getattr(self, "x_speed", 0) == 0:
                # See if we should slip past whatever we've hit
                slip_distance = utils.try_to_slip_sprite(self, self.slip_remaining, self.collide_with_any_tile)
                if slip_distance:
                    log.debug("{} {} slipped {}".format(self.tile_id, self, slip_distance))
                    # We successfully slipped off
                    self.slip_remaining -= slip_distance
                    return MovableRC.CONTINUE 

            # We've hit something and not slipped past it                
            self.rect.center = initial_center
            if self.y_speed > 0:
                self.falling = False
            self.y_speed = 0
            return MovableRC.STOP

    def update(self):

        if not self.scene:
            return None

        old_center = self.rect.center

        if self.x_speed != 0:
            move_dir = (1 if self.x_speed > 0 else -1)
            self.step_height_remaining = self.max_step_height
            
            # Try and move in the x direction
            for i in range(abs(self.x_speed)):
                log.debug("Current pos = {}, {}".format(self.rect.left, self.rect.top))

                # Try to update our X position.  
                rc = self.try_to_move(x_speed = move_dir)
                if rc == MovableRC.CONTINUE:
                    # We're good.  Try to move again.
                    continue

                # We couldn't move any further
                self.on_stopped_x()
                break

        # Apply gravity.  
        self.y_speed = min(config.TERMINAL_VELOCITY, self.y_speed + self.gravity_effect)

        # Try to move in the y-direction.
        move_dir = (1 if self.y_speed > 0 else -1)
        self.slip_remaining = self.slip_distance
        for i in range(abs(self.y_speed)):
            log.debug("{} {} Move Y.  Bottom = {}".format(self.tile_id, self, self.rect.bottom))

            rc = self.try_to_move(y_speed = move_dir)
            if rc == MovableRC.CONTINUE:
                # We're good.  Try to move again.
                self.falling = True
                continue
            elif rc == MovableRC.FELL_OFF_SCREEN:
                return rc # Let the caller deal with it

            break

        if old_center != self.rect.center:
            log.info("{} New pos = {}, {}".format(self.tile_id, self.rect.left, self.rect.top))
            log.info("{} Current speed = {}, {}".format(self.tile_id, self.x_speed, self.y_speed))
        
        # Add this in if we want to be able to push stuff UP slopes / over objects etc.
        # self.step_height_remaining = self.max_step_height

        return None

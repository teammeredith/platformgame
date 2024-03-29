
# - Define lift class that inherits from Movable?  So that it handles hitting things and trying to move them?
# - Move try_to_push to be part of Movable
# - Never move anything without checking for collisions!  

import pygame
import config
import os
import json
import logging
import sys
import itertools
import utils
import frame_timer
import movable
from config import TileAttr
from movable import Movable

log = logging.getLogger()

class Lift(movable.Movable):
    # sprite for the Player
    def __init__(self, image):
        movable.Movable.__init__(self, image)
        self.slip_distance = 0
        self.move_speed = 0
        self.jump_speed = 0
        self.gravity_effect = 0
        self.can_be_pushed = False

    def start_scene(self, scene, initial_left, initial_top): 
        movable.Movable.start_scene(self, scene, initial_left, initial_top)
    
    def off_bottom_of_screen(self):
        return movable.MovableRC.CONTINUE

    def being_pushed(self, x_speed, y_speed):
        if y_speed > 0:
            self.y_speed = -config.LIFT_SPEED
        return movable.MovableRC.STOP

    def update(self):
        movable.Movable.update(self)
        self.y_speed = 0

    def off_top_of_screen(self):
        # We're off the top of the screen.  Start again at the bottom, but far enough off the bottom 
        # that we're not about to move it on top of something that's just falling off the screen... 
        return movable.MovableRC.STOP

class Scene():
    def __init__(self, scene_file_path, screen):
        with open(scene_file_path, "r") as scene_file:
            self.scene_data = json.load(scene_file)
            if "dark" in self.scene_data:
                self.dark = self.scene_data["dark"]
            else:
                self.dark = False
            self.reset()
            self.screen = screen
            self.frame_counter = 0
        self.player = None
    
    def reset(self):
        self.player_start = (self.scene_data["player_start"][0], self.scene_data["player_start"][1]) 
        self.open_locks = []
        self.exited = False

        # Create the platform sprites
        self.platform_sprites = pygame.sprite.Group()
        for y in range(config.SCREEN_HEIGHT_TILES):
            for x in range(config.SCREEN_WIDTH_TILES):
                tile_data = self.scene_data["tiles"][y][x]
                tile_id = tile_data.get("id", "PLAIN")                    
                """if tile_id == "SPIDER":
                    spider = Spider()
                    spider.tile_id = "SPIDER"
                    spider.reset((x, y))
                    self.platform_sprites.add(spider)
                elif """

                if tile_id != "BLANK":
                    image = utils.load_image(tile_data["path"], tile_data["filename"], tile_data.get("rotate", 0))
                    if config.tiles[tile_id].attrs & TileAttr.MOVABLE:
                        tile = movable.Movable(image)
                        tile.start_scene(self, x * config.TILE_SIZE_PX, y * config.TILE_SIZE_PX)
                    elif config.tiles[tile_id].attrs & TileAttr.LIFT:
                        tile = Lift(image)
                        tile.start_scene(self, x * config.TILE_SIZE_PX, y * config.TILE_SIZE_PX)
                    else:
                        tile = pygame.sprite.Sprite()
                        tile.image = image
                        tile.mask = pygame.mask.from_surface(tile.image)
                        tile.rect = tile.image.get_rect()
                        tile.rect.top = config.TILE_SIZE_PX*y
                        tile.rect.left = config.TILE_SIZE_PX*x                
                    tile.images = []
                    tile.tile_id = tile_id

                    tile.attrs = config.tiles[tile_id].attrs

                    tile.rotation_enabled = (config.tiles[tile_id].attrs & TileAttr.DISABLE_ON_ROTATE) and (tile_data.get("rotate", 0) == 0)
                    
                    tile.frames_per_transition = config.tiles[tile_id].frames_per_transition
                    tile.last_collided = None
                    if config.tiles[tile_id].animate_image_files:
                        tile.images = [tile.image.copy()]
                        for image_file in config.tiles[tile_id].animate_image_files:
                            tile.images.append(utils.load_image(tile_data["path"], image_file, tile_data.get("rotate", 0)))
                            tile.state = 0
                    self.platform_sprites.add(tile)

    """
    Rotate the board clockwise
    """
    def rotate(self):
        
        # Rotate the sprites
        utils.screen_spin(self.screen, steps=10, angle=180, time=150)
        for tile in itertools.chain(self.platform_sprites, self.open_locks):
            if isinstance(tile, movable.Movable):
                tile.board_rotate()
            else:
                tile.image = pygame.transform.rotate(tile.image, -180)
                tile.mask = pygame.mask.from_surface(tile.image)
                for i in range(len(tile.images)):
                    tile.images[i] = pygame.transform.rotate(tile.images[i], -180)
                tile.rect.right, tile.rect.bottom = config.SCREEN_WIDTH_PX - tile.rect.left, config.SCREEN_HEIGHT_PX - tile.rect.top 
            tile.rotation_enabled = not tile.rotation_enabled

        self.player.board_rotate()

    def exit_scene(self):
        self.exited = True

    def test_collision(self, sprite):
        # Perf optimization.  In general the thing we're goiong to hit is the last thing we hit.  Test against that first.
        if sprite.last_collided and not getattr(sprite.last_collided, "inactive", False) and pygame.sprite.collide_mask(sprite, sprite.last_collided):
            return sprite.last_collided
        for test_sprite in itertools.chain(self.platform_sprites, [self.player]):
            if sprite != test_sprite and pygame.sprite.collide_rect(sprite, test_sprite) and pygame.sprite.collide_mask(sprite, test_sprite):
                sprite.last_collided = test_sprite
                return test_sprite
        return None

    def collided_movable_tiles(self, sprite):
        collided = []
        for test_sprite in itertools.chain(itertools.filterfalse(lambda x: not isinstance(x, Movable), self.platform_sprites), [self.player]):
            if sprite != test_sprite and isinstance(test_sprite, Movable) and pygame.sprite.collide_rect(sprite, test_sprite) and pygame.sprite.collide_mask(sprite, test_sprite):
                collided.append(test_sprite)
        return collided

    def key_down(self, event):
        return    
        if event.key == pygame.K_r:
            self.rotate()

    def animate_tiles(self):
        # Check whether any tiles should be animated
        for sprite in itertools.filterfalse(lambda x: not x.frames_per_transition, self.platform_sprites):        
            if not self.frame_counter % sprite.frames_per_transition:
                sprite.state = (sprite.state+1) % len(sprite.images)
                sprite.image = sprite.images[sprite.state]
                sprite.mask = pygame.mask.from_surface(sprite.image)

    def update(self):
        self.frame_counter = (self.frame_counter+1) % config.FPS
        sprites_to_delete = []
        for sprite in self.platform_sprites:
            rc = sprite.update()
            if rc == movable.MovableRC.FELL_OFF_SCREEN:
                sprites_to_delete.append(sprite)
        for sprite in sprites_to_delete:
            log.info("Delete sprite {}".format(sprite.tile_id))
            self.platform_sprites.remove(sprite)
            del sprite
        self.animate_tiles()

    def add_player(self, player):
        self.player = player

    def spin_activated(self, spin_tile):
        # Can only use each spin once.  Remove the tile now.
        self.platform_sprites.remove(spin_tile)
        pygame.event.post(pygame.event.Event(config.ROTATE_BOARD_EVENT_ID))

    def animate_spring(self, tile):
        tile.state = (tile.state+1)%2
        tile.image = tile.images[tile.state]
        tile.mask = pygame.mask.from_surface(tile.image)

    def hit_button(self, tile):
        if tile.attrs & TileAttr.BUTTON:
            if tile.tile_id == "BUTTON_YELLOW":
                # If the button is up, then change it to down
                if tile.state == 0:
                    tile.image = tile.images[1]
                    tile.mask = pygame.mask.from_surface(tile.image)
                    tile.state = 1
                frame_timer.FrameTimer(int(self.scene_data["lock_time"]*config.FPS/1000), self.timer_pop, frame_timer.FRAME_TIMER_ID_YELLOW_BUTTON, unique=True)
                for sprite in self.platform_sprites:
                    if sprite.tile_id == "LOCK_YELLOW":
                        sprite.remove(self.platform_sprites)
                        sprite.inactive = True
                        self.open_locks.append(sprite)
            else:
                # Toggle the button state
                tile.state = (tile.state+1)%2
                tile.image = tile.images[tile.state]
                tile.mask = pygame.mask.from_surface(tile.image)


    def remove_tile(self, tile):
        tile.remove(self.platform_sprites)
        tile.inactive = True

    def draw(self, screen):
        self.platform_sprites.draw(screen)

    def timer_pop(self, id=None):
        log.info("Timer pop")
        print("timer pop {}".format(id))
        for sprite in self.open_locks:
            log.info("Redraw lock")
            self.platform_sprites.add(sprite)
            sprite.inactive = False
            if pygame.sprite.collide_mask(sprite, self.player):
                self.player.die()
        self.open_locks = []

        for tile in self.platform_sprites:
            if tile.attrs & TileAttr.BUTTON:
                if tile.state == 1:
                    tile.image = tile.images[0]
                    tile.mask = pygame.mask.from_surface(tile.image)
                    tile.state = 0
                if pygame.sprite.collide_mask(tile, self.player):
                    self.hit_button(tile)

    def add_torch_lights(self, mask, spotlight_mask):
        for sprite in filter(lambda x: x.attrs & TileAttr.LIGHT, self.platform_sprites):
            mask.blit(spotlight_mask, (sprite.rect.centerx - config.SPOTLIGHT_RADIUS, sprite.rect.centery - config.SPOTLIGHT_RADIUS), special_flags=pygame.BLEND_RGBA_MIN)
        
        
                    
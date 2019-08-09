import pygame
import config
import os
import json
import logging
import sys
import itertools
import utils

#logging.basicConfig(filename='platform.log', filemode='w', level=logging.DEBUG)
logging.basicConfig(level=logging.ERROR, format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
module = sys.modules['__main__'].__file__
log = logging.getLogger(module)

class Scene():
    def __init__(self, scene_file_path, screen):
        with open(scene_file_path, "r") as scene_file:
            self.scene_data = json.load(scene_file)
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
                tile_id = self.scene_data["tiles"][y][x]                    
                """if tile_id == "SPIDER":
                    spider = Spider()
                    spider.tile_id = "SPIDER"
                    spider.reset((x, y))
                    self.platform_sprites.add(spider)
                elif """
                if tile_id != "BLANK":
                    tile = pygame.sprite.Sprite()
                    tile.image = config.tiles[tile_id].image
                    tile.images = []
                    tile.tile_id = tile_id
                    tile.rect = tile.image.get_rect()
                    tile.rect.top = config.TILE_SIZE_PX*y
                    tile.rect.left = config.TILE_SIZE_PX*x
                    tile.movable = config.tiles[tile_id].movable
                    tile.kill = config.tiles[tile_id].kill
                    tile.spring = config.tiles[tile_id].spring
                    tile.rotation_enabled = config.tiles[tile_id].rotation_enabled
                    tile.button = config.tiles[tile_id].button
                    tile.frames_per_transition = config.tiles[tile_id].frames_per_transition
                    if config.tiles[tile_id].animate_images:
                        tile.images = [tile.image] + config.tiles[tile_id].animate_images
                        tile.state = 0
                    if tile.movable:
                        tile.y_speed = 0
                    self.platform_sprites.add(tile)

    """
    Rotate the board clockwise
    """
    def rotate(self):
        
        # Rotate the sprites
        utils.screen_spin(self.screen, steps=10, angle=180, time=150)
        for tile in itertools.chain(self.platform_sprites, self.open_locks):
            tile.image = pygame.transform.rotate(tile.image, -180)
            tile.rotation_enabled = not tile.rotation_enabled
            for i in range(len(tile.images)):
                tile.images[i] = pygame.transform.rotate(tile.images[i], -180)
            tile.rect.right, tile.rect.bottom = config.SCREEN_WIDTH_PX - tile.rect.left, config.SCREEN_HEIGHT_PX - tile.rect.top 

        self.player.board_rotate()

    def exit_scene(self):
        self.exited = True

    def test_collision(self, sprite):
        for test_sprite in itertools.chain(self.platform_sprites, [self.player]):
            if sprite != test_sprite and pygame.sprite.collide_rect(sprite, test_sprite) and pygame.sprite.collide_mask(sprite, test_sprite):
                return test_sprite

        return None

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

    # Called to see if any movable tiles should be *autonomously* moving.  This doesn't get involved when
    # tiles are being pushed.  That's covered by try_to_move_tile.  So at the moment this function 
    # just has to worry about whether non-fixed tiles should be falling.
    def update_movable_tiles(self):
        sprites_to_delete = []

        for sprite in itertools.filterfalse(lambda x: not x.movable, self.platform_sprites):        
            # Apply gravity.  
            sprite.y_speed = min(config.TERMINAL_VELOCITY, sprite.y_speed + config.GRAVITY_EFFECT)

            move_dir = (1 if sprite.y_speed > 0 else -1)
            slip_remaining = config.SLIP_DISTANCE             
            for i in range(abs(sprite.y_speed)):
                sprite.rect.bottom += move_dir

                if sprite.rect.top > config.SCREEN_HEIGHT_PX:
                    # This sprite just fell off the bottom of the screen
                    sprites_to_delete.append(sprite) 
                    break

                if self.test_collision(sprite):                    
                    if move_dir == 1:
                        # Check if we can slip off whatever we've hit
                        slip_distance = utils.try_to_slip_sprite(sprite, slip_remaining, self.test_collision)
                        if slip_distance:
                            # We successfully slipped off
                            slip_remaining -= slip_distance
                            continue
                    # We've hit something and not slipped past it 
                    sprite.rect.bottom -= move_dir
                    sprite.y_speed = 0
                    break      

        self.platform_sprites.remove(sprites_to_delete)

    def update(self):
        self.frame_counter = (self.frame_counter+1) % config.FPS
        self.platform_sprites.update()
        self.animate_tiles()
        self.update_movable_tiles()

    def add_player(self, player):
        self.player = player

    def spin_activated(self, spin_tile):
        # Can only use each spin once.  Remove the tile now.
        self.platform_sprites.remove(spin_tile)
        pygame.event.post(pygame.event.Event(config.ROTATE_BOARD_EVENT_ID))

    def animate_spring(self, tile):
        tile.state = (tile.state+1)%2
        tile.image = tile.images[tile.state]

    def hit_button(self, tile):
        if tile.button == "YELLOW":
            # If the button is up, then change it to down
            if tile.state == 0:
                tile.image = tile.images[1]
                tile.state = 1
                pygame.time.set_timer(config.LOCK_TIMER_EVENT_ID, self.scene_data["lock_time"])
            for sprite in self.platform_sprites:
                if sprite.tile_id == "LOCK_YELLOW":
                    sprite.remove(self.platform_sprites)
                    self.open_locks.append(sprite)

    def try_to_move_tile(self, tile, direction):
        if tile.tile_id != "BOX":
            return False
        # It's a box.  Can we move it?
        tile.rect.left += direction
        if tile.rect.left < 0:
            tile.rect.left = 0
            return False
        if tile.rect.right > config.SCREEN_WIDTH_PX:
            tile.rect.right = config.SCREEN_WIDTH_PX
            return False
        collided = self.test_collision(tile) 
        if collided:
            #  Hit something.  Check whether we can move whatever we've hit too.
            if self.try_to_move_tile(collided, direction):
                # The thing we hit moved.  Check whether we're not collision free.
                if not self.test_collision(tile):
                    return True

            tile.rect.left -= direction
            return False
        return True


    def draw(self, screen):
        self.platform_sprites.draw(screen)

    def timer_pop(self):
        log.info("Timer pop")
        for sprite in self.open_locks:
            self.platform_sprites.add(sprite)
            if pygame.sprite.collide_mask(sprite, self.player):
                self.player.die()
        self.open_locks = []

        for tile in self.platform_sprites:
            if tile.button == "YELLOW":
                if tile.state == 1:
                    tile.image = tile.images[0]
                    tile.state = 0
                if pygame.sprite.collide_mask(tile, self.player):
                    self.hit_button(tile)
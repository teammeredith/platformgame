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
        utils.screen_spin(self.screen, steps=10, angle=90, time=150)
        for tile in itertools.chain(self.platform_sprites, self.open_locks):
            tile.image = pygame.transform.rotate(tile.image, -90)
            for i in range(len(tile.images)):
                tile.images[i] = pygame.transform.rotate(tile.images[i], -90)
            tile.rect.left, tile.rect.top = config.SCREEN_WIDTH_PX - config.TILE_SIZE_PX - tile.rect.top, tile.rect.left 

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
            self.rotate()

    def animate_tiles(self):
        # Check whether any tiles should be animated
        for sprite in itertools.filterfalse(lambda x: not x.frames_per_transition, self.platform_sprites):        
            if not self.frame_counter % sprite.frames_per_transition:
                sprite.state = (sprite.state+1) % len(sprite.images)
                sprite.image = sprite.images[sprite.state]

    def update_movable_tiles(self):
        # Check whether any movable tiles should be falling

        for sprite in itertools.filterfalse(lambda x: not x.movable, self.platform_sprites):        
            # Check whether it should be moving sideways?
            """
            if sprite.target_left:
                self.try_to_move_tile(sprite, 1 if sprite.target_left > sprite.rect.left else -1)
            """

            # Apply gravity.  We start slow 'cos that makes it more efficient when we're just standing on something...
            if sprite.y_speed == 0:
                sprite.y_speed = 1
            else:
                sprite.y_speed += config.GRAVITY_EFFECT
                sprite.y_speed = min(config.TERMINAL_VELOCITY, sprite.y_speed)

            move_dir = (1 if sprite.y_speed > 0 else -1)
            slip_remaining = config.SLIP_DISTANCE             
            for i in range(abs(sprite.y_speed)):
                sprite.rect.bottom += move_dir

                if sprite.rect.bottom > config.SCREEN_HEIGHT_PX: 
                    sprite.rect.bottom -= move_dir
                    sprite.y_speed = 0
                    break        
                if self.test_collision(sprite):                    
                    if move_dir == 1:
                        orig_left = sprite.rect.left
                        # Check if we can slip off whatever we've hit
                        slipped = False
                        for slip in range(slip_remaining):
                            for try_pos in (max(0, orig_left - slip), min(config.SCREEN_WIDTH_PX - config.TILE_SIZE_PX, orig_left + slip)):                        
                                sprite.rect.left = try_pos
                                if not self.test_collision(sprite):
                                    log.info("Slipped off")
                                    slipped = True
                                    break
                            if slipped:
                                slip_remaining -= (slip+1)
                                break
                        if slipped:
                            continue 
                        else:
                            sprite.rect.left = orig_left       
                            sprite.rect.bottom -= move_dir
                            sprite.y_speed = 0
                            break        

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

        """
        # Managed to move it.  Encourage the box to continue moving to the next aligned space
        if tile.target_left:
            # We already had a target.  Have we reached it?
            if tile.target_left == tile.rect.left:
                tile.target_left = None
          
        elif direction == 1:
            tile.target_left = (int(tile.rect.left / config.TILE_SIZE_PX) + 1) * config.TILE_SIZE_PX
        else:
            tile.target_left = int(tile.rect.left-1 / config.TILE_SIZE_PX) * config.TILE_SIZE_PX
        """
        
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
import pygame
import config
import os
import json
import logging
import sys

#logging.basicConfig(filename='platform.log', filemode='w', level=logging.DEBUG)
logging.basicConfig(level=logging.ERROR, format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
module = sys.modules['__main__'].__file__
log = logging.getLogger(module)

class Scene():
    def __init__(self, scene_file_path):
        with open(scene_file_path, "r") as scene_file:
            self.scene_data = json.load(scene_file)
            self.player_start = (self.scene_data["player_start"][0], self.scene_data["player_start"][1]) 
            self.open_locks = []
            self.player = None
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
                        tile.tile_id = tile_id
                        tile.rect = tile.image.get_rect()
                        tile.rect.top = config.TILE_SIZE_PX*y
                        tile.rect.left = config.TILE_SIZE_PX*x
                        self.platform_sprites.add(tile)

    def exit_scene(self):
        self.exited = True

    def test_collision(self, sprite):
        for test_sprite in self.platform_sprites:
            if sprite != test_sprite and pygame.sprite.collide_rect(sprite, test_sprite) and pygame.sprite.collide_mask(sprite, test_sprite):
                return test_sprite

        return None

    def update(self):
        self.platform_sprites.update()

    def add_player(self, player):
        self.player = player

    def animate_spring(self, tile):
        if tile.tile_id == "SPRING_UP":
            tile.image = config.tiles["SPRING_DN"].image
            tile.tile_id = "SPRING_DN"
        else:
            tile.image = config.tiles["SPRING_UP"].image
            tile.tile_id = "SPRING_UP"

    def hit_button(self, tile):
        if tile.tile_id == "BUTTON_YELLOW":
            tile.image = config.tiles["BUTTON_YELLOW_DN"].image
            tile.tile_id = "BUTTON_YELLOW_DN"
        for sprite in self.platform_sprites:
            if sprite.tile_id == "LOCK_YELLOW":
                sprite.remove(self.platform_sprites)
                self.open_locks.append(sprite)
                pygame.time.set_timer(config.LOCK_TIMER_EVENT_ID, 3500)

    def draw(self, screen):
        self.platform_sprites.draw(screen)

    def timer_pop(self):
        log.info("Timer pop")
        for sprite in self.open_locks:
            self.platform_sprites.add(sprite)
            if pygame.sprite.collide_mask(sprite, self.player):
                self.player.die()

        for tile in self.platform_sprites:
            if tile.tile_id == "BUTTON_YELLOW_DN":
                tile.image = config.tiles["BUTTON_YELLOW"].image
                tile.tile_id = "BUTTON_YELLOW"
                if pygame.sprite.collide_mask(tile, self.player):
                    self.hit_button(tile)


import pygame
import config
import os

def load_tile_image(tile_data):
    return pygame.transform.rotate(
                pygame.transform.smoothscale(
                    pygame.image.load(
                        os.path.join(config.img_folder, *tile_data.path, tile_data.filename)
                    ).convert_alpha(), 
                    (config.TILE_SIZE_PX, config.TILE_SIZE_PX)
                ),
                tile_data.rotate)

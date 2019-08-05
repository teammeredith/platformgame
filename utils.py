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

def screen_spin(screen, angle=90, time=1000, steps=45, shrink=False):
    screen_image = pygame.display.get_surface().copy()
    scale_factor = 0.95 if shrink else 1
    scale =  1 
    for i in range(steps):
        pygame.time.wait(int(time/steps))
        screen.fill((0, 0, 0))
        scale = scale*scale_factor
        new_image = pygame.transform.rotozoom(screen_image, int(angle/steps)*i, scale)
        width = new_image.get_width()
        height = new_image.get_height()
        x_offset = int((config.SCREEN_WIDTH_PX - width)/2)
        y_offset = int((config.SCREEN_HEIGHT_PX - height)/2)
        if width < config.SCREEN_WIDTH_PX:
            screen.blit(new_image, pygame.Rect(x_offset, y_offset, width, height))
        else:
            screen.blit(new_image, pygame.Rect(0, 0, config.SCREEN_WIDTH_PX, config.SCREEN_HEIGHT_PX), pygame.Rect(-1*x_offset, -1*y_offset, config.SCREEN_WIDTH_PX, config.SCREEN_HEIGHT_PX))            
        pygame.display.flip()
            

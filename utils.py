import pygame
import config
import os

def load_image(path, filename, rotation=0, size=(config.TILE_SIZE_PX, config.TILE_SIZE_PX)):
    return pygame.transform.rotate(
                pygame.transform.smoothscale(
                    pygame.image.load(
                        os.path.join(config.img_folder, *path, filename)
                    ).convert_alpha(), 
                    size
                ),
                rotation)

def load_tile_image(tile_data, size=(config.TILE_SIZE_PX, config.TILE_SIZE_PX)):
    return load_image(tile_data.path, tile_data.filename, tile_data.rotate, size)

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
        pygame.event.pump()
            
def try_to_slip_sprite(sprite, slip_remaining, collision_fn):
    orig_left = sprite.rect.left
    for slip in range(1, slip_remaining+1):
        for try_pos in (max(0, orig_left - slip), min(config.SCREEN_WIDTH_PX - sprite.rect.width, orig_left + slip)):                        
            sprite.rect.left = try_pos
            if not collision_fn(sprite=sprite):
                # We've successfully slipped
                return slip
    # Undo our attempted slip
    sprite.rect.left = orig_left       
    return 0


def load_default_tiles():
    # Add more tiles without any special properties
    used_files = [tile.filename for tile in config.tiles.values()]
    print("Used files = {}".format(used_files))    
    with os.scandir(os.path.join(config.img_folder, "Tiles")) as it:
        for tile_file in it:
            print("Consider loading {}".format(tile_file.name))
            if tile_file.is_file() and not tile_file.name in used_files: 
                filename, file_extension = os.path.splitext(tile_file)
                if file_extension == ".png":
                    config.tiles[tile_file.name] = config.Tile(tile_file.name)

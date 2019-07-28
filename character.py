import config
import pygame
import logging
import sys
import os

#logging.basicConfig(filename='platform.log', filemode='w', level=logging.DEBUG)
logging.basicConfig(level=logging.ERROR, format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
module = sys.modules['__main__'].__file__
log = logging.getLogger(module)

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

    def start_scene(self, scene):
        self.scene = scene
        self.walking = False
        self.rect.left = scene.player_start[0] * config.TILE_SIZE_PX
        self.rect.top = scene.player_start[1] * config.TILE_SIZE_PX
        self.y_speed = 0
        self.x_speed = 0
        self.falling = True
        self.walk_index = 0
    
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

    def collide_with_any_tile(self):
        # Check whether the player has collided with any tile.  If they have, return the Tile.  
        # Otherwise return None
        return self.scene.test_collision(self)

    def check_for_key_press(self):    
        pass

    def on_hit_x(self):
        self.x_speed = 0

    def collided(self, tile):
        pass

    def update(self):
        # Called every frame
        self.check_for_key_press()

        #log.debug("pos = {}, {}".format(self.rect.left, self.rect.top))
        #log.debug("speed = {}, {}".format(self.x_speed, self.y_speed))

        old_center = self.rect.center

        if self.x_speed != 0:
            move_dir = (1 if self.x_speed > 0 else -1)
            step_height_remaining = self.max_step_height
            # Try and move in the x direction
            for i in range(abs(self.x_speed)):
                log.debug("Current pos = {}, {}".format(self.rect.left, self.rect.top))
                self.rect.left += move_dir
                if self.rect.right > config.SCREEN_WIDTH_PX:
                    self.rect.right = config.SCREEN_WIDTH_PX
                    self.on_hit_x()
                elif self.rect.left < 0:
                    self.rect.left = 0                    
                    self.on_hit_x()

                collided = self.collide_with_any_tile()
                if collided:
                    self.collided(collided)
                    # Is this something that we can go over?
                    if self.y_speed == 0:
                        over = False
                        old_top = self.rect.top
                        for step in range(step_height_remaining):
                            log.debug("Step up")
                            self.rect.top -= 1
                            if not self.collide_with_any_tile():
                                log.info("Made it over")
                                over = True
                                break
                        if over:
                            step_height_remaining -= (step+1)
                            continue
                        self.rect.top = old_top
                    # We've moved as far as we can
                    self.rect.left -= move_dir
                    self.on_hit_x()
                    break
                    # if we went over something?  self.y_speed = -1

        # Apply gravity.  We start slow 'cos that makes it more efficient when we're just standing on something...
        if self.y_speed == 0:
            self.y_speed = 1
        else:
            self.y_speed += 2

        move_dir = (1 if self.y_speed > 0 else -1)
        slip_remaining = self.slip_distance
        for i in range(abs(self.y_speed)):
            self.rect.bottom += move_dir
            collided = self.collide_with_any_tile()
            if collided:
                self.collided(collided)
                if self.y_speed > 5 and collided.tile_id == "SPRING_UP":
                    log.info("Hit SPRING_UP.  y_speed = {}".format(self.y_speed))
                    self.scene.animate_spring(collided)
                    self.y_speed = min(self.y_speed, 10)
                    break
                elif collided.tile_id == "SPRING_DN":
                    log.info("Hit SPRING_DOWN")
                    self.scene.animate_spring(collided)
                    self.rect.top -= 30
                    self.y_speed = -40
                    break
                elif self.y_speed > 5 and collided.tile_id == "BUTTON_YELLOW":
                    log.info("Hit BUTTON_YELLOW.  y_speed = {}".format(self.y_speed))
                    self.scene.hit_button(collided)
                    self.y_speed = min(self.y_speed, 10)
                    break
                elif move_dir == 1 and self.x_speed == 0:
                    orig_left = self.rect.left
                    # Check if we can slip off whatever we've hit
                    slipped = False
                    for slip in range(slip_remaining):
                        for try_pos in (orig_left - slip, orig_left + slip):                        
                            self.rect.left = try_pos
                            if not self.collide_with_any_tile():
                                log.info("Slipped off")
                                slipped = True
                                break
                        if slipped:
                            slip_remaining -= (slip+1)
                            break
                    if slipped:
                        continue 
                    else:
                        self.rect.left = orig_left       
                if move_dir == 1:
                    self.falling = False
                self.y_speed = 0
                self.rect.bottom -= move_dir                

        """
        elif self.y_speed < 0:
            # We're going up.  Check if we've hit our head.
            for tile in platform_sprites:
                if pygame.sprite.collide_rect(self, tile) and pygame.sprite.collide_mask(self, tile):
                    print("Hit head")
                    self.rect.bottom = old_bottom
                    self.y_speed = 0
        """

            
        if old_center != self.rect.center:
            log.info("New pos = {}, {}".format(self.rect.left, self.rect.top))
            log.info("Current speed = {}, {}".format(self.x_speed, self.y_speed))

        self.animate()


class Player(Character):
    # sprite for the Player
    def __init__(self):
        player_data = config.characters["PLAYER"]
        standing_image = pygame.transform.smoothscale(
                            pygame.image.load(
                                os.path.join(config.img_folder, 
                                             player_data.image_path,
                                             player_data.standing_image)).convert_alpha(), 
                            (70,70))
        walk_left_images = []
        walk_right_images = []
        for frame_image in player_data.walk_images:
            image = pygame.transform.smoothscale(
                        pygame.image.load(
                            os.path.join(config.img_folder, 
                                        player_data.image_path,
                                        frame_image)).convert_alpha(), 
                        (70,70))
            walk_right_images.append(image)
            walk_left_images.append(pygame.transform.flip(image, True, False))

        Character.__init__(self, standing_image, walk_left_images, walk_right_images)
        self.max_step_height = 15
        self.slip_distance = 15
        self.move_speed = 10
        self.jump_speed = 25
        self.is_player = True
        self.tile_id = ""

    def check_for_key_press(self):    
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
            self.falling = True
            self.y_speed = -self.jump_speed

    def collided(self, tile):
        log.debug("Collided with {}".format(tile.tile_id))
        if tile.tile_id == "EXIT":
            print("Posting exit event")
            pygame.event.post(pygame.event.Event(config.REACHED_EXIT_EVENT_ID))
            
    def die(self):
        self.reset(self.scene.player_start)
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

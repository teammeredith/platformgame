import pygame
import os

SCREEN_WIDTH_TILES = 15
SCREEN_HEIGHT_TILES = 15
TILE_SIZE_PX = 45
SCREEN_WIDTH_PX = SCREEN_WIDTH_TILES*TILE_SIZE_PX
SCREEN_HEIGHT_PX = SCREEN_HEIGHT_TILES*TILE_SIZE_PX

# Character constants
MAX_STEP_HEIGHT = 8
SLIP_DISTANCE = 10
MOVE_SPEED = 6
JUMP_SPEED = 14
SPRING_JUMP_SPEED = 23
SPRING_ACTIVE_SPEED = 2
GRAVITY_EFFECT = 1
TERMINAL_VELOCITY = 40

FPS = 30

LOCK_TIMER_EVENT_ID = pygame.USEREVENT + 1
REACHED_EXIT_EVENT_ID = pygame.USEREVENT + 2

game_data = {}

game_folder = os.path.dirname(__file__)
img_folder = os.path.join(game_folder, "images")
scene_folder = os.path.join(game_folder, "scenes")
tile_folder = os.path.join(img_folder, "Tiles")

class Tile():
    def __init__(self, filename):
        self.filename = filename

tiles = {
    "P_GRASS_L": Tile("grassCliffLeft.png"),
    "P_GRASS_C": Tile("grassMid.png"),
    "P_GRASS_R": Tile("grassCliffRight.png"),
    "CASTLE_CLIFF_LT": Tile("castleCliffLeftAlt.png"),
    "CASTLE_CLIFF": Tile("castleMid.png"),
    "CASTLE_CLIFF_RT": Tile("castleCliffRightAlt.png"),
    "FENCE": Tile("ladder_top.png"),
    "BRICK": Tile("brickWall.png"),
    "EXIT": Tile("signExit.png"),
    "DIRT_SL_R": Tile("grassHillRight.png"),
    "DIRT_SL_L": Tile("grassHillLeft.png"),
    "BUSH": Tile("bush.png"),
    "SPRING_UP": Tile("springboardUp.png"),
    "SPRING_DN":  Tile("springboardDown.png"),
    "BUTTON_YELLOW": Tile("buttonYellow.png"),
    "BUTTON_YELLOW_DN": Tile("buttonYellow_pressed.png"),
    "LOCK_YELLOW": Tile("lock_yellow.png")
}             

class CharacterData():
    def __init__(self, image_path, standing_image, walk_images):
        self.image_path = image_path
        self.standing_image = standing_image
        self.walk_images = walk_images

characters = {
    "PLAYER": CharacterData("Player", "p3_front.png", ["p3_walk01.png",
                                                       "p3_walk02.png",
                                                       "p3_walk03.png",
                                                       "p3_walk04.png",
                                                       "p3_walk05.png",
                                                       "p3_walk06.png",
                                                       "p3_walk07.png",
                                                       "p3_walk08.png",
                                                       "p3_walk09.png",
                                                       "p3_walk10.png",
                                                       "p3_walk11.png"])
}

 

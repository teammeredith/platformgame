import pygame
import os
from enum import Flag, auto

SCREEN_WIDTH_TILES = 25
SCREEN_HEIGHT_TILES = 25
TILE_SIZE_PX = 30
SCREEN_WIDTH_PX = SCREEN_WIDTH_TILES*TILE_SIZE_PX
SCREEN_HEIGHT_PX = SCREEN_HEIGHT_TILES*TILE_SIZE_PX
SPOTLIGHT_RADIUS = 130

# Character constants
MAX_STEP_HEIGHT = 6
SLIP_DISTANCE = 9
MOVE_SPEED = 5
JUMP_SPEED = 12
SPRING_JUMP_SPEED = 18
SPRING_ACTIVE_SPEED = 4
GRAVITY_EFFECT = 1
TERMINAL_VELOCITY = 30
LIFT_SPEED = 3

FPS = 30

LOCK_TIMER_EVENT_ID = pygame.USEREVENT + 1
REACHED_EXIT_EVENT_ID = pygame.USEREVENT + 2
PLAYER_DEAD = pygame.USEREVENT + 3
ROTATE_BOARD_EVENT_ID = pygame.USEREVENT + 4

game_data = {}

game_folder = os.path.dirname(__file__)
img_folder = os.path.join(game_folder, "images")
scene_folder = os.path.join(game_folder, "scenes")

class TileAttr(Flag):
    NONE = 0
    MOVABLE = auto()
    KILL = auto()
    LIFT = auto()
    SPRING = auto()    
    BUTTON = auto()
    BREAKABLE = auto()
    HEAVY = auto()

class Tile():
    def __init__(self, 
                 filename, 
                 path=["Tiles"], 
                 animate_image_files=[],
                 frames_per_transition=0,
                 rotate=0, 
                 rotation_enabled=True,
                 kill=False,
                 attrs=TileAttr.NONE):
        self.filename = filename
        self.path = path
        self.rotate = rotate
        self.attrs = attrs
        self.animate_image_files = animate_image_files
        self.frames_per_transition = frames_per_transition
        self.rotation_enabled = rotation_enabled

tiles = {
    "EXIT": Tile("signExit.png"),
    "SPRING": Tile("springboardUp.png", animate_image_files=["springboardDown.png"], attrs=TileAttr.SPRING, rotation_enabled=True),
    "SPRING_ROTATED": Tile("springboardUp.png", animate_image_files=["springboardDown.png"], attrs=TileAttr.SPRING, rotate=180, rotation_enabled=False),
    "SPRING_DN_ROTATED":  Tile("springboardDown.png", rotate=180),
    "BUTTON_YELLOW": Tile("buttonYellow.png", animate_image_files=["buttonYellow_pressed.png"], attrs=TileAttr.BUTTON),
    "BUTTON_YELLOW_ROTATED": Tile("buttonYellow.png", animate_image_files=["buttonYellow_pressed.png"], attrs=TileAttr.BUTTON, rotate=180),
    "LOCK_YELLOW": Tile("lock_yellow.png"),
    "BOX": Tile("box.png", attrs=TileAttr.MOVABLE|TileAttr.HEAVY),
    "SPIN": Tile("fireball.png", path=["Items"]),
    "SPIKES": Tile("spikes.png", path=["Items"], attrs=TileAttr.KILL),
    "SPIKES_DN": Tile("spikes.png", path=["Items"], attrs=TileAttr.KILL, rotate=180),
    "TORCH": Tile("tochLit.png", animate_image_files=["tochLit2.png"], frames_per_transition=6),
    "LIFT": Tile("bridge.png", attrs=TileAttr.LIFT),
    "BRIDGE": Tile("bridgeLogs.png", attrs=TileAttr.BREAKABLE),
    "PLAYER": Tile("p3_front.png", path=["Player"]) # This is just here for the scene designer
}        

class CharacterData():
    def __init__(self, image_path, standing_image, walk_images, dead_image):
        self.image_path = image_path
        self.standing_image = standing_image
        self.walk_images = walk_images
        self.dead_image = dead_image

characters = {
    "PLAYER": CharacterData(["Player"], 
                            "p3_front.png", 
                            ["p3_walk01.png",
                             "p3_walk02.png",
                             "p3_walk03.png",
                             "p3_walk04.png",
                             "p3_walk05.png",
                             "p3_walk06.png",
                             "p3_walk07.png",
                             "p3_walk08.png",
                             "p3_walk09.png",
                             "p3_walk10.png",
                             "p3_walk11.png"],
                             "p3_hurt.png")
}

 

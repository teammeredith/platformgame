import pygame

WIDTH = 10
HEIGHT = 10
TILE_SIZE = 70
SCREEN_WIDTH = WIDTH*TILE_SIZE
SCREEN_HEIGHT = HEIGHT*TILE_SIZE

FPS = 30

LOCK_TIMER_EVENT_ID = pygame.USEREVENT + 1

game_data = {}
tiles = {}
current_scene = 0
scenes = []

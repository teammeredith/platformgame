# Pygame sprite Example
import config
import pygame
import random
import os
import json
import logging
import sys
from character import Player
from scene import Scene
import utils
import argparse
import time

# Initialize pygame and create window
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((config.SCREEN_WIDTH_PX, config.SCREEN_HEIGHT_PX), flags=pygame.DOUBLEBUF)
pygame.display.set_caption("My Game")
clock = pygame.time.Clock()

spotlight_mask = utils.load_image([], "spotlight_mask.png", size=(config.SPOTLIGHT_RADIUS*2, config.SPOTLIGHT_RADIUS*2))
mask = pygame.Surface((config.SCREEN_WIDTH_PX, config.SCREEN_HEIGHT_PX), flags=pygame.SRCALPHA)
mask.fill((0,0,0,255))
mask.blit(spotlight_mask, (200,200), special_flags=pygame.BLEND_RGBA_MIN)

screen.fill((128, 0, 0))
screen.blit(mask, (0,0))

pygame.display.flip()
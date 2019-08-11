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



mask = pygame.Surface((260,260), flags=pygame.SRCALPHA)
mask.fill((0,0,0,255))
for i in range(0,50):
    pygame.draw.circle(mask, (0,0,0,245-i*2), (130,130), 130-i)
for i in range(0,10):
    pygame.draw.circle(mask, (0,0,0,145-i*15), (130,130), 80-i)
pygame.draw.circle(mask, (0,0,0,0), (130,130), 70)

pygame.image.save(mask, "mask.png")
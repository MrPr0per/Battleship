import pygame

pygame.init()

FIELD_WIDTH = 10
FIELD_HEIGHT = 12

ABC = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

DEFAULT_SHIPS_COUNT = {
    # # 4: 1,
    # # 3: 1,
    # # 2: 1,
    # 1: 2,

    4: 1,
    3: 2,
    2: 3,
    1: 4,
}

# GUI
SC_W, SC_H = 1280, 720
FPS = 120

DEFAULT_FONT_NAME = 'Lucida Console'
DEFAULT_FONT_SIZE = 24
DEFAULT_FONT = pygame.font.SysFont(DEFAULT_FONT_NAME, DEFAULT_FONT_SIZE)

DEFAULT_BUTTON_MARGIN = 24
DEFAULT_BUTTON_SIZE = 32

WHITE = (255, 255, 255)
GREEN = (90, 180, 90)
RED = (200, 100, 100)
DARK_RED = (100, 50, 50)
BRIGHT_RED = (240, 110, 100)
GREY = (160, 160, 160)

TEXT_MATGIN_LEFT_RIGHT = 10
TEXT_MATGIN_TOP_BOT = 10

#
# AI_HIT_COOLDOWN = 0.03
# MOVE_COOLDOWN = 0.03
AI_HIT_COOLDOWN = 0.4
MOVE_COOLDOWN = 1

HIDE_AI_FIELD = True

QUICKSAVE_PATH = 'quicksave.save'
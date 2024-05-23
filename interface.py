import random

import numpy as np

from settings import *
import pygame
from main import Player, MyFildCells, OpponentCells

# нужно сделать окна:
# 1.
#   - выбор левого, правого игрока из (чел, тупой аи, умный аи)
# 2.
#   - Параметризация поля (размеры, типы и количество кораблей)
#   - расстановка кораблей
#   - Угловые корабли
# 3.
#   - выбор времени для каждого игрока (в т.ч. бесконечное)
#   Игра на время (в режиме hot seat)
#
#
# + предустановленные параметры, чтобы прокликать "далее"


class Screen:
    pass

class ChoosePlayersScreen(Screen):
    pass

class SetShipsScreen(Screen):
    pass

class ChooseTimeScreen(Screen):
    pass

class ScreensController:
    def __init__(self):
        self.screens = []
        self.active_creen_index = 0

def main():
    windows = []


if __name__ == '__main__':
    main()
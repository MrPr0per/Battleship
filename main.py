import datetime
import random
import time

import numpy as np
from numpy import array as arr
from enum import Enum, auto
from settings import *


class Dir(Enum):
    v = auto()
    h = auto()


class MyFildCells(Enum):
    empty = 0
    intact_ship = 1
    destroyed_ship = 2


class Ship:
    def __init__(self, dir_, size, x, y):
        self.dir = dir_
        self.size = size
        self.x = x
        self.y = y

    def get_rect(self):
        """возвращает (x0, y0, x1, y1) - верхнюю левую и нижнюю правую точки корабля"""
        if self.dir == Dir.h:
            return self.x, self.y, self.x + self.size - 1, self.y
        if self.dir == Dir.v:
            return self.x, self.y, self.x, self.y + self.size - 1
        raise ValueError('у корабля задано неизвестное напрвление (?)')

    def __str__(self):
        return f'({self.x}, {self.y}) x{self.size}: {self.dir.name}'

    def __repr__(self):
        return str(self)


class Player:
    def __init__(self):
        self.my_ships = np.full((FIELD_WIDTH, FIELD_HEIGHT), False)  # True - в этой клетке есть корабль, False - нет
        self.my_shoots = np.full((FIELD_WIDTH, FIELD_HEIGHT), False)  # True - игрок стрелял в эту клетку, False - нет
        self.possible_crds_for_ships = self.get_possible_crds_for_ships()
        self.opponent = None
        # ссылка на объект Player соперника
        # сразу инициализировать нельзя, тк для создания опонента нужно передать ему ссылку на этого игрока,
        # а мы его еще не создали - возникает циклическая зависимость

    def set_random_ships(self):
        for ship_size, count in SHIPS_COUNT.items():
            for _ in range(count):
                ship = self.get_random_possible_ship(ship_size)
                self.update_possible_crds_for_ships(self.possible_crds_for_ships, ship)
                self.set_ship(ship)

    def get_random_possible_ship(self, ship_size):
        # если корабль одно направления установить будет невозмножно - попробуем установить корабль другого направления
        dirs = [Dir.v, Dir.h]
        random.shuffle(dirs)
        for dir_ in dirs:
            try:
                x0, y0 = random.choice(tuple(self.possible_crds_for_ships[dir_][ship_size]))
                ship = Ship(dir_, ship_size, x0, y0)
                return ship
            except IndexError:
                continue
        raise Exception(f'для корабля такого размера нет места:'
                        f'{Debug.show_possible_crds_for_ships(self.possible_crds_for_ships, ship_sizes=(ship_size,))}')

    def set_ship(self, ship):
        x0, y0, x1, y1 = ship.get_rect()
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.my_ships[x, y] = True

    @staticmethod
    def get_possible_crds_for_ships():
        # possible_crds_for_ships[direction][size] = {(0,0), (0,1) ... (7,9)}
        # - все возмножные точки, в которых будет верхний левый угол соотвествующего корабля
        ships_sises = SHIPS_COUNT.keys()
        possible_crds_for_ships = {Dir.v: {}, Dir.h: {}}
        for s in ships_sises:
            possible_crds_for_ships[Dir.v][s] = set()
            possible_crds_for_ships[Dir.h][s] = set()

        for x in range(FIELD_WIDTH):
            for y in range(FIELD_HEIGHT):
                for s in ships_sises:
                    if x + s <= FIELD_WIDTH:
                        possible_crds_for_ships[Dir.h][s].add((x, y))
                    if y + s <= FIELD_HEIGHT:
                        possible_crds_for_ships[Dir.v][s].add((x, y))
        return possible_crds_for_ships

    @staticmethod
    def update_possible_crds_for_ships(possible_crds_for_ships, ship):
        """
        принимает координаты, направление и размер поставленного на поле корабля
        и чистит из possible_crds_for_ships лишние координаты
        """

        # нужно удилить все координаты из области [x0-s, x1+1] x [y0-1, y1+1] для горизонтальных кораблей размера s
        #                                    и из [x0-1, x1+1] x [y0-s, y1+1] для веритикльных размера s
        # x0y0 - верхняя левая точка нового корабля
        # x1y1 - нижняя правая точка нового корабля

        x0, y0, x1, y1 = ship.get_rect()

        for s in SHIPS_COUNT.keys():
            for x in range(x0 - s, x1 + 1 + 1):
                for y in range(y0 - 1, y1 + 1 + 1):
                    # if x0 <= x <= x1 and y0 <= y <= y1: continue
                    try:
                        possible_crds_for_ships[Dir.h][s].remove((x, y))
                    except KeyError:
                        pass
            for x in range(x0 - 1, x1 + 1 + 1):
                for y in range(y0 - s, y1 + 1 + 1):
                    # if x0 <= x <= x1 and y0 <= y <= y1: continue
                    try:
                        possible_crds_for_ships[Dir.v][s].remove((x, y))
                    except KeyError:
                        pass


class Debug:
    @staticmethod
    def show_possible_crds_for_ships(possible_crds_for_ships, ship_sizes=None, directions=None):
        if ship_sizes is None: ship_sizes = SHIPS_COUNT.keys()
        if directions is None: directions = Dir.v, Dir.h

        output = ''
        for s in ship_sizes:
            for d in directions:
                # print(f'{d.name}:')
                output += f'{d.name}:\n'
                for y in range(FIELD_HEIGHT):
                    for x in range(FIELD_WIDTH):
                        if (x, y) in possible_crds_for_ships[d][s]:
                            # print(f'{s} ', end='')
                            output += f'{s} '
                        else:
                            # print('. ', end='')
                            output += '. '
                    # print()
                    output += '\n'
                # print()
                output += '\n'

        return output

    @staticmethod
    def show_field(field):
        out = ''

        for y in range(FIELD_HEIGHT):
            for x in range(FIELD_WIDTH):
                if field[x, y]:
                    out += '▄▀'
                else:
                    out += '. '
            out += '\n'
        out += '\n'

        return out


class Tests:
    @staticmethod
    def test_set_ship():
        global FIELD_WIDTH, FIELD_HEIGHT
        old_w, old_h = FIELD_WIDTH, FIELD_HEIGHT
        FIELD_WIDTH, FIELD_HEIGHT = 4, 4

        pl = Player()
        pl.set_ship(Ship(Dir.v, 4, 0, 0))

        print(Debug.show_field(pl.my_ships))

        FIELD_WIDTH, FIELD_HEIGHT = old_w, old_h


# class Game:
#     @staticmethod
#     def run(cls):

def main():
    # r = Player.get_possible_crds_for_ships()
    # Player.update_possible_crds_for_ships(r, Ship(Dir.h, 2, 5, 5))
    # Debug.show_possible_crds_for_ships(r)

    # Tests.test_set_ship()

    pl1 = Player()
    pl1.set_random_ships()

    print(Debug.show_field(pl1.my_ships))


if __name__ == '__main__':
    main()

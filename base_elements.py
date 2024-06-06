from enum import Enum, auto

import numpy as np


class Dir(Enum):  # direction
    v = auto()  # vertical
    h = auto()  # horisontal


# class FieldOwner(Enum):  # в морском бое у каждого игрока есть 2 поля: свое поле и поле противника
#     Me = auto()
#     Opponent = auto()
#
#     def get_default(self):
#         if self == FieldOwner.Me:
#             return MyCell.empty
#         elif self == FieldOwner.Opponent:
#             return OpponentCell.empty
#         else:
#             raise NotImplemented()


class MyCell(Enum):
    empty = 0
    intact_ship = 1
    missed_shot = 2
    destroyed_ship = 3


class OpponentCell(Enum):
    unknown = 0
    empty = 1
    ship = 2


class ShootStatus(Enum):
    miss = auto()  # мимо
    hit = auto()  # попал в корабль, но не уничтожил его
    kill = auto()  # уничтожил корабль, но не последний
    total_annihilation = auto()  # уничтожил последний корабль

    def is_success(self):
        if self == self.miss: return False
        if self in (ShootStatus.hit, ShootStatus.kill, ShootStatus.total_annihilation): return True
        raise NotImplemented()


class ShipRect:
    def __init__(self, dir_: Dir, size, x, y):
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

    @staticmethod
    def get_ships_count(ships: list['ShipRect']):
        count = {}
        for ship in ships:
            size = ship.size
            if size not in count: count[size] = 0
            count[size] += 1
        return count

    def __str__(self):
        return f'({self.x}, {self.y}) x{self.size}: {self.dir.name}'

    def __repr__(self):
        return str(self)


# class Field:
#     def __init__(self, w, h):
#         self.w, self.h = w, h
#         self.ships

class MyField:
    def __init__(self, w, h):
        self.cells = np.full((w, h), MyCell.empty)

    def validate(self, ship: ShipRect) -> bool:
        """проверяет, что корабль может находиться на поле"""
        x0, y0, x1, y1 = ship.get_rect()
        w, h = self.cells.shape
        if x0 < 0 or y0 < 0 or x1 >= w or y1 >= h: return False

        for x in range(x0 - 1, x1 + 2):
            for y in range(y0 - 1, y0 + 2):
                # noinspection PyTypeChecker
                if not self.can_ship_be_nearby(self.cells[x, y]):  # пучарм тут определяет тип неправильно
                    return False

        return True

    @classmethod
    def can_ship_be_nearby(cls, cell: MyCell) -> bool:
        if cell in (MyCell.empty, MyCell.missed_shot): return True
        if cell in (MyCell.intact_ship, MyCell.destroyed_ship): return False
        raise NotImplemented()


class OpponentField:
    def __init__(self, w, h):
        self.cells = np.full((w, h), OpponentCell.unknown)
